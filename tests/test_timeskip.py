"""Post-death time-skip behavior (section 5)."""

from __future__ import annotations

from chronicle_forge import compute_skip_years
from chronicle_forge.config import MAX_SKIP, MIN_SKIP


def test_younger_death_skips_longer_than_old_age():
    assert compute_skip_years(20, 0) > compute_skip_years(70, 0)


def test_result_is_always_clamped():
    for age in range(0, 81, 5):
        for bonus in (0, 5, 100):
            skip = compute_skip_years(age, bonus)
            assert MIN_SKIP <= skip <= MAX_SKIP


def test_pending_seeds_extend_the_skip():
    without = compute_skip_years(40, 0)
    with_seeds = compute_skip_years(40, 10)
    assert with_seeds >= without


def test_seed_bonus_is_capped():
    # Huge pending maturation cannot push skip past the clamp.
    assert compute_skip_years(40, 10_000) <= MAX_SKIP
