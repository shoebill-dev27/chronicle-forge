"""Tests for P8 juncture gate (play/gate.py)."""

from __future__ import annotations

from types import SimpleNamespace

from chronicle_forge.opportunity import Opportunity, OpportunityKind, Signals
from chronicle_forge.play.gate import (
    REASON_CRISIS,
    REASON_FLOOR,
    REASON_HISTORY,
    REASON_NOVELTY,
    JunctureGate,
)


def _opp(kind, target, tension):
    return Opportunity(kind, target, f"name:{target}", tension, Signals())


def _world(*heritage_ids):
    return SimpleNamespace(heritage=[SimpleNamespace(id=h) for h in heritage_ids])


def test_high_tension_asks_with_crisis_reason():
    gate = JunctureGate()
    d = gate.decide(_world(), [_opp(OpportunityKind.NPC, "n1", 0.90)], 0, 0)
    assert d.ask and d.reason == REASON_CRISIS


def test_quiet_turn_does_not_ask():
    gate = JunctureGate()
    # below T_ASK, a kind/target already seen, no legacy, no heritage.
    w = _world()
    gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.50)], 0, 0)  # first sight = novel
    d = gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.50)], 1, 0)
    assert not d.ask


def test_legacy_top_slot_triggers_history():
    gate = JunctureGate()
    d = gate.decide(_world(), [_opp(OpportunityKind.LEGACY, "h1", 0.40)], 0, 0)
    assert d.ask and d.reason == REASON_HISTORY


def test_birth_is_baseline_not_novelty():
    # The first turn establishes a baseline; nothing present at birth is "new".
    gate = JunctureGate()
    d = gate.decide(_world(), [_opp(OpportunityKind.FACTION, "f1", 0.50)], 0, 0)
    assert not d.ask


def test_target_appearing_after_birth_is_novelty():
    gate = JunctureGate()
    w = _world()
    gate.decide(w, [_opp(OpportunityKind.FACTION, "f1", 0.50)], 0, 0)  # baseline
    d = gate.decide(w, [_opp(OpportunityKind.FACTION, "f2", 0.50)], 1, 0)  # new target
    assert d.ask and d.reason == REASON_NOVELTY


def test_cooldown_suppresses_non_crisis_but_crisis_pierces():
    gate = JunctureGate()
    w = _world()
    assert gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.90)], 0, 0).ask  # high
    # within cooldown, a high (non-crisis) tension is suppressed
    d1 = gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.88)], 1, 0)
    assert not d1.ask
    # a crisis-level spike pierces the cooldown
    d2 = gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.95)], 2, 0)
    assert d2.ask and d2.reason == REASON_CRISIS


def test_per_year_budget_caps_asks():
    gate = JunctureGate(cooldown_turns=0, asks_per_year=2)
    w = _world()
    asks = 0
    for t in range(6):
        if gate.decide(w, [_opp(OpportunityKind.NPC, f"n{t}", 0.95)], t, year=0).ask:
            asks += 1
    assert asks == 2  # capped to the per-year budget


def test_floor_forces_one_ask_per_life():
    gate = JunctureGate()
    w = _world()
    # a wholly quiet life: low tension, repeated target, no legacy/heritage
    gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.40)], 0, 0)  # novelty consumed
    d = gate.decide(
        w, [_opp(OpportunityKind.NPC, "n1", 0.40)], 1, 0, is_final_turn=True
    )
    assert d.ask and d.reason == REASON_FLOOR


def test_floor_not_triggered_if_already_asked():
    gate = JunctureGate()
    w = _world()
    assert gate.decide(w, [_opp(OpportunityKind.NPC, "n1", 0.95)], 0, 0).ask
    d = gate.decide(
        w, [_opp(OpportunityKind.NPC, "n1", 0.40)], 5, 1, is_final_turn=True
    )
    assert not d.ask


def test_new_heritage_is_novelty():
    gate = JunctureGate()
    seen = [_opp(OpportunityKind.NPC, "n1", 0.40)]
    gate.decide(_world(), seen, 0, 0)  # consume novelty of n1
    gate.decide(_world(), seen, 1, 0)  # quiet
    d = gate.decide(_world("h-new"), seen, 2, 0)  # a heritage just appeared
    assert d.ask and d.reason == REASON_NOVELTY


def test_deterministic_no_rng():
    seq = [
        (_world(), [_opp(OpportunityKind.NPC, "n1", 0.50)], 0, 0, False),
        (_world(), [_opp(OpportunityKind.LEGACY, "h1", 0.40)], 1, 0, False),
        (_world(), [_opp(OpportunityKind.NPC, "n1", 0.95)], 2, 0, False),
    ]

    def run():
        g = JunctureGate()
        return [g.decide(*args).reason for args in seq]

    assert run() == run()
