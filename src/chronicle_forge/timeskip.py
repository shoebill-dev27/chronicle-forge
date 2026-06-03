"""Post-death time-skip computation (section 5).

Adopted method: age-based base + seed maturation bonus.

    skip = clamp(base(age) + seed_bonus, MIN_SKIP, MAX_SKIP)

Younger death yields a larger base (the world runs longer without the player);
old age yields a shorter base. The seed bonus ties skip length to how many
not-yet-matured causal seeds the player left, so planting much and dying young
makes the world move more to show the results.
"""

from __future__ import annotations

from . import config


def base_skip(age_at_death: int) -> float:
    """Linearly interpolate base skip from MAX_BASE (age 0) to MIN_BASE (cap)."""
    age = max(0, min(age_at_death, config.LIFESPAN_CAP))
    span = config.MAX_BASE - config.MIN_BASE
    return config.MAX_BASE - (age / config.LIFESPAN_CAP) * span


def compute_skip_years(age_at_death: int, pending_maturation_total: int) -> int:
    """Return the number of world years to skip after a death.

    ``pending_maturation_total`` is the summed maturation time of the player's
    seeds that have not yet fired. Its contribution is capped by SEED_BONUS_CAP.
    """
    bonus = min(max(0, pending_maturation_total), config.SEED_BONUS_CAP)
    raw = base_skip(age_at_death) + bonus
    clamped = max(config.MIN_SKIP, min(raw, config.MAX_SKIP))
    return int(round(clamped))
