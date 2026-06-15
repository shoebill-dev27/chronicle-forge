"""Tests for P8 rendering (play/render.py)."""

from __future__ import annotations

import re
from types import SimpleNamespace

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.execution import ExecutionOption
from chronicle_forge.opportunity import Opportunity, OpportunityKind, Signals
from chronicle_forge.play import render
from chronicle_forge.play.gate import REASON_CRISIS, REASON_HISTORY
from chronicle_forge.reporting._data import heritage_rows

_WHY_PHRASES = {p for _, p in render._WHY}


def _opt(kind, target, tension, label, sig=None):
    opp = Opportunity(kind, target, f"name:{target}", tension, sig or Signals())
    return ExecutionOption(opp, "perform_activity", label)


def _fallback():
    return ExecutionOption(None, "perform_activity", "Live quietly")


def _world(year=10, dom="faith", heritage=()):
    theme = SimpleNamespace(dominant=SimpleNamespace(value=dom))
    return SimpleNamespace(current_year=year, theme=theme, heritage=list(heritage))


def _life(age=14, talent="warrior"):
    return SimpleNamespace(age=age, talent=SimpleNamespace(value=talent))


# --- why_now: words, never numbers -------------------------------------


def test_why_now_is_a_word_phrase():
    sig = Signals(delta=0.9, sigma=0.1, omega=0.2, rho=0.0)
    assert render.why_now(sig) == "tension rising"
    assert render.why_now(sig) in _WHY_PHRASES


def test_why_now_deterministic_tiebreak():
    # all equal -> deterministic Δ>Σ>Ω>Ρ order picks delta
    sig = Signals(delta=0.5, sigma=0.5, omega=0.5, rho=0.5)
    assert render.why_now(sig) == "tension rising"


def test_turn_screen_exposes_no_internal_numbers():
    sig = Signals(delta=0.83, sigma=0.12, omega=0.44, rho=0.05)
    options = [_opt(OpportunityKind.NPC, "n1", 0.91, "Mentor Maren", sig), _fallback()]
    screen = render.turn_screen(_world(), _life(), options, REASON_CRISIS)
    # Option markers ([1]/[0]) are fine; what must never leak is a P6 internal
    # number — a tension/signal float like 0.91 or 0.83.
    assert not re.search(r"\d\.\d", screen), screen
    for leak in ("0.91", "0.83", "0.12", "0.44", "0.05"):
        assert leak not in screen
    assert "(tension rising)" in screen


# --- option layout & choice mapping ------------------------------------


def test_turn_screen_shows_top3_and_let_it_pass():
    options = [
        _opt(OpportunityKind.WILDCARD, "w1", 0.95, "Stand against Korr"),
        _opt(OpportunityKind.FACTION, "f1", 0.80, "Spread the faith"),
        _opt(OpportunityKind.NPC, "n1", 0.70, "Mentor Maren"),
        _opt(OpportunityKind.LOCATION, "l1", 0.60, "Develop Vow Hollow"),
        _fallback(),
    ]
    screen = render.turn_screen(_world(), _life(), options, REASON_CRISIS)
    assert "[1]" in screen and "[2]" in screen and "[3]" in screen
    assert "[4]" not in screen  # trimmed to top 3
    assert "[0] Let this season pass." in screen
    # highest tension is listed first
    assert screen.index("Stand against Korr") < screen.index("Spread the faith")


def test_choice_mapping_resolves_to_real_option_index():
    options = [
        _opt(OpportunityKind.NPC, "n1", 0.70, "Mentor Maren"),
        _opt(OpportunityKind.WILDCARD, "w1", 0.95, "Stand against Korr"),
        _fallback(),
    ]
    # display [1] is the highest tension (the wildcard at options index 1)
    assert render.option_index_for_choice(options, 1) == 1
    assert render.option_index_for_choice(options, 0) == 2  # fallback
    assert render.option_index_for_choice(options, 9) is None


def test_no_actionable_options_renders_only_let_it_pass():
    screen = render.turn_screen(_world(), _life(), [_fallback()], REASON_CRISIS)
    assert "[0] Let this season pass." in screen
    assert "[1]" not in screen


# --- former-self recognition: first time only, read-only ---------------


def _legacy_option(world):
    row = heritage_rows(world)[0]
    heritage_id = next(h.id for h in world.heritage if h.seed_id == row["source_seed"])
    return _opt(OpportunityKind.LEGACY, heritage_id, 0.9, f'Tend {row["name"]}')


def test_recognition_is_first_time_only_and_pure():
    world = simulate_world(42, mode="opportunity")
    opt = _legacy_option(world)
    options = [opt, _fallback()]
    seen = set()

    rid = render.recognizable_heritage(world, options, seen)
    assert rid is not None
    # pure: the helper did not mutate the caller's set
    assert seen == set()

    screen1 = render.turn_screen(world, _life(), options, REASON_HISTORY, rid)
    assert "the work of" in screen1  # recognition shown the first time

    # caller (not render) records it; a re-encounter is no longer recognized
    seen.add(rid)
    assert render.recognizable_heritage(world, options, seen) is None
    screen2 = render.turn_screen(world, _life(), options, REASON_HISTORY, None)
    assert "the work of" not in screen2  # discovery, not notification


def test_turn_screen_is_read_only_on_world():
    world = simulate_world(42, mode="opportunity")
    before = world.model_dump()
    opt = _legacy_option(world)
    render.turn_screen(
        world, _life(), [opt, _fallback()], REASON_HISTORY, opt.target_id
    )
    assert world.model_dump() == before


def test_turn_screen_deterministic():
    options = [
        _opt(OpportunityKind.WILDCARD, "w1", 0.95, "Stand against Korr"),
        _opt(OpportunityKind.NPC, "n1", 0.70, "Mentor Maren"),
        _fallback(),
    ]
    a = render.turn_screen(_world(), _life(), options, REASON_CRISIS)
    b = render.turn_screen(_world(), _life(), options, REASON_CRISIS)
    assert a == b


# --- yearly digest order stability -------------------------------------


def test_year_digest_marks_promotion_and_is_stable():
    quiet = render.year_digest(_world(), 14, "you tend the Dawn Covenant", False)
    promo = render.year_digest(_world(), 15, "a school takes hold", True)
    assert quiet.startswith("  Year 14")
    assert promo.startswith("  ✧ Year 15")
    # deterministic
    assert promo == render.year_digest(_world(), 15, "a school takes hold", True)


def test_year_digest_sequence_preserves_input_order():
    rows = [(14, "a", False), (15, "b", True), (16, "c", False)]
    lines = [render.year_digest(_world(), y, p, pr) for y, p, pr in rows]
    years = [int(re.search(r"Year (\d+)", ln).group(1)) for ln in lines]
    assert years == [14, 15, 16]
