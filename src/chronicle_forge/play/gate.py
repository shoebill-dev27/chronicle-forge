"""The juncture gate — when does history's call warrant asking the player?

Turn by turn, the gate decides whether to interrupt the continuously-advancing
world and hand the choice to the player. It lives strictly *outside* P6: it
reads each opportunity's already-computed tension and signals, and never
re-scores. It holds no queue of pending asks — every turn yields at most one
ask (the most pressing), which is how "History remembers selectively" reaches
the input layer: concurrent critical moments collapse to the single highest one
rather than stacking into a backlog.

All state here is volatile per-life and read-only on the world; the gate draws
no RNG, so a human run with no asks is byte-identical to opportunity mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..opportunity import Opportunity, OpportunityKind

# Thresholds and budgets — P8 layer only; never P6 tension weights. Initial
# values grounded in the observed bimodal top-tension distribution (baseline
# ~0.42-0.67, spike ~0.88-0.94); the valley sits near 0.85.
T_ASK = 0.85  # high-tension juncture
T_HISTORY = 0.70  # a Legacy/History opportunity worth surfacing
T_CRISIS = 0.92  # may interrupt the cooldown
COOLDOWN_TURNS = 4  # one year of quiet after an ask
ASKS_PER_LIFE = 6
ASKS_PER_YEAR = 2

# Trigger reasons (map to display headers in play/render.py).
REASON_CRISIS = "crisis"  # high tension
REASON_NOVELTY = "novelty"
REASON_HISTORY = "history"
REASON_FLOOR = "floor"  # forced so every life has at least one ask


@dataclass
class GateDecision:
    """Whether to ask the player this turn, and why (None reason ⇒ no ask)."""

    ask: bool
    reason: Optional[str] = None


@dataclass
class JunctureGate:
    """Per-life, read-only juncture detector. One instance per life."""

    t_ask: float = T_ASK
    t_history: float = T_HISTORY
    t_crisis: float = T_CRISIS
    cooldown_turns: int = COOLDOWN_TURNS
    asks_per_life: int = ASKS_PER_LIFE
    asks_per_year: int = ASKS_PER_YEAR

    last_ask_turn: Optional[int] = None
    asks_this_life: int = 0
    _year_asks: dict = field(default_factory=dict)
    _seen_kinds: set = field(default_factory=set)
    _seen_targets: set = field(default_factory=set)
    _known_heritage: set = field(default_factory=set)
    _initialized: bool = False  # first turn is a baseline, not a novelty

    def decide(
        self,
        world,
        opps: list[Opportunity],
        turn_index: int,
        year: int,
        is_final_turn: bool = False,
    ) -> GateDecision:
        """Decide for one turn. ``opps`` is P6's untouched, tension-sorted offer.
        ``is_final_turn`` lets the floor guarantee one ask per life."""
        if not opps:
            # A barren turn still ends a life eventually; honour the floor.
            if is_final_turn and self.asks_this_life == 0:
                return self._commit(turn_index, year, REASON_FLOOR)
            return GateDecision(False)

        top = opps[0]
        crisis = top.tension >= self.t_crisis
        high = top.tension >= self.t_ask
        history = self._is_history(opps)
        novelty = self._is_novel(world, opps)

        # Reason priority: crisis/high tension, then history, then novelty.
        if crisis or high:
            reason = REASON_CRISIS
        elif history:
            reason = REASON_HISTORY
        elif novelty:
            reason = REASON_NOVELTY
        else:
            reason = None

        budget_ok = (
            self.asks_this_life < self.asks_per_life
            and self._year_asks.get(year, 0) < self.asks_per_year
        )
        in_cooldown = (
            self.last_ask_turn is not None
            and turn_index - self.last_ask_turn < self.cooldown_turns
        )

        ask = (
            reason is not None
            and budget_ok
            and (crisis or not in_cooldown)  # only a crisis pierces the cooldown
        )

        # Floor: never let a life pass without a single juncture.
        if not ask and is_final_turn and self.asks_this_life == 0:
            ask, reason = True, REASON_FLOOR

        self._absorb(world, opps)
        if ask:
            return self._commit(turn_index, year, reason)
        return GateDecision(False)

    # --- triggers -------------------------------------------------------

    def _is_history(self, opps: list[Opportunity]) -> bool:
        """A Legacy opportunity in the top slot, or a strong one anywhere. Mere
        presence (Legacy is offered on ~half of all turns) does not trigger."""
        if opps[0].kind is OpportunityKind.LEGACY:
            return True
        return any(
            o.kind is OpportunityKind.LEGACY and o.tension >= self.t_history
            for o in opps
        )

    def _is_novel(self, world, opps: list[Opportunity]) -> bool:
        """Something that *stirred during this life*: a kind or target that
        appeared after birth, or a heritage promoted since. The first turn is a
        baseline (everything present at birth is not "new"), so novelty never
        fires at birth — it marks genuine emergence, not first inspection."""
        if not self._initialized:
            return False
        for o in opps:
            if o.kind not in self._seen_kinds or o.target_id not in self._seen_targets:
                return True
        return bool({h.id for h in world.heritage} - self._known_heritage)

    # --- state ----------------------------------------------------------

    def _absorb(self, world, opps: list[Opportunity]) -> None:
        for o in opps:
            self._seen_kinds.add(o.kind)
            self._seen_targets.add(o.target_id)
        for h in world.heritage:
            self._known_heritage.add(h.id)
        self._initialized = True

    def _commit(self, turn_index: int, year: int, reason: str) -> GateDecision:
        self.last_ask_turn = turn_index
        self.asks_this_life += 1
        self._year_asks[year] = self._year_asks.get(year, 0) + 1
        return GateDecision(True, reason)
