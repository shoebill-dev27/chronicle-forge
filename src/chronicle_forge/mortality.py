"""The mortality seam: why and when a life ends before or at the natural cap.

``check_mortality`` is evaluated exactly once per world year, for the current
life, by :func:`macro.advance_year`. It answers with a ``DeathCause`` or
``None``; the caller records the death. Reaching ``LIFESPAN_CAP`` is always
death. Anything earlier must come from a hazard in ``HAZARDS`` — a
deterministic callable given an RNG derived from ``(world.seed, year,
HAZARD_SALT)``, a stream separate from the world's own so adding a hazard
never reshuffles world events.

There is no default hazard: without a world or action context that puts a life
at risk, a life reaches 80. Early death is what such a context will supply.
"""

from __future__ import annotations

from typing import Callable, Optional

from .enums import DeathCause
from .life import lifespan_reached
from .models import Life, World
from .rng import DeterministicRNG

HAZARD_SALT = 7

Hazard = Callable[[World, Life, DeterministicRNG], Optional[DeathCause]]

HAZARDS: list[Hazard] = []


def check_mortality(
    world: World, life: Life, rng: DeterministicRNG
) -> Optional[DeathCause]:
    """The cause ``life`` dies of this year, or ``None`` if it lives on."""
    if lifespan_reached(life):
        return DeathCause.LIFESPAN
    for hazard in HAZARDS:
        cause = hazard(world, life, rng)
        if cause is not None:
            return cause
    return None
