"""Tunable constants. These are design-locked defaults (see docs/design.md).

World lifespan is the only value expected to differ between dev/CI (40 years,
fast iteration) and production (200 years); the logic is identical.

Many values below were re-tuned in the P3.5 balance pass (see docs/playtest_p5.md
and docs/playtest_p35.md) to fix theme freeze, heritage inflation, the wildcard
monopoly, and the fixed 2-life cycle.
"""

from __future__ import annotations

# --- World lifespan (section 3) ---
DEV_WORLD_MAX_YEARS = 40
PROD_WORLD_MAX_YEARS = 200

# --- Player lifespan (section / "player") ---
LIFESPAN_CAP = 80  # maximum age a life can reach

# --- Post-death time skip (section 5) ---
# skip = clamp(base(age) + seed_maturation_bonus, MIN_SKIP, MAX_SKIP)
# Tightened so several lives fit a world (was 4..22, forcing exactly 2 lives).
MIN_SKIP = 2
MAX_SKIP = 8
MAX_BASE = 7  # base skip for a death at age 0 (younger death -> longer)
MIN_BASE = 2  # base skip for a death at LIFESPAN_CAP (old age -> shorter)
SEED_BONUS_CAP = 5  # cap on the maturation bonus contribution

# --- Natural lifespan distribution (P3.5) ---
# Active world-years a life lasts before natural death (auto-player / default).
NATURAL_SPAN_MIN = 2
NATURAL_SPAN_MAX = 7
COMBAT_DEATH_PROB_PER_YEAR = 0.06  # small chance a life ends in combat

# --- Heritage promotion gate (P3.5; was: promote everything) ---
HERITAGE_MIN_REACH = 4  # transitive descendant events required
HERITAGE_MIN_LONGEVITY = 10  # years propagated required
HERITAGE_MIN_SCORE = 120  # composite score threshold
HERITAGE_MAX_PER_WORLD = 8  # only the most significant legacies are remembered

# --- World Theme dynamics (P3.5) ---
THEME_EVENT_WINDOW = 8  # years of recent events that move the theme
THEME_BASE_AXIS = 20

# --- WildCard ignition gate (P3.5; was: theme-only, 0.5 prob, 1 wildcard) ---
WILDCARD_IGNITION_PROB = 0.25
WILDCARD_PLAYER_SEED_REQ = 2  # fired player seeds in the axis domain required

# --- Faction conflict (P3.5) ---
FACTION_WAR_POWER = 62
FACTION_WAR_PROB = 0.2
FACTION_MEAN_REVERSION = 50  # power drifts toward this

# --- MVP world shape (section 3) ---
MVP_NPC_COUNT = 10
MVP_IMPORTANT_NPC_COUNT = 2  # Tier-S among the named NPCs (2-3 allowed)
MVP_WILDCARD_COUNT = 5  # one per archetype (P3.5: was 1; registry already N-ready)
