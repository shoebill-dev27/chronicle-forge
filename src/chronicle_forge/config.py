"""Tunable constants. These are design-locked defaults (see docs/design.md).

World lifespan is the only value expected to differ between dev/CI (40 years,
fast iteration) and production (200 years); the logic is identical.
"""

from __future__ import annotations

# --- World lifespan (section 3) ---
DEV_WORLD_MAX_YEARS = 40
PROD_WORLD_MAX_YEARS = 200

# --- Player lifespan (section / "player") ---
LIFESPAN_CAP = 80  # maximum age a life can reach

# --- Post-death time skip (section 5) ---
# skip = clamp(base(age) + seed_maturation_bonus, MIN_SKIP, MAX_SKIP)
MIN_SKIP = 4
MAX_SKIP = 22
MAX_BASE = 18  # base skip for a death at age 0 (younger death -> longer)
MIN_BASE = 4  # base skip for a death at LIFESPAN_CAP (old age -> shorter)
SEED_BONUS_CAP = 12  # cap on the maturation bonus contribution

# --- MVP world shape (section 3) ---
MVP_NPC_COUNT = 10
MVP_IMPORTANT_NPC_COUNT = 2  # Tier-S among the named NPCs (2-3 allowed)
MVP_WILDCARD_COUNT = 1
