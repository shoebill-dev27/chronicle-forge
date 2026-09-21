"""Tunable constants. These are design-locked defaults (see docs/design.md).

Time domain (owner decisions, 2026-09): one simulation tick is one world year;
the world horizon is 200 years; a playable life begins at 16 and ends by 80
at the latest; death and the next life are exactly ten world years apart.

Many values below were re-tuned in the P3.5 balance pass (see docs/playtest_p5.md
and docs/playtest_p35.md) to fix theme freeze, heritage inflation, the wildcard
monopoly, and the fixed 2-life cycle.
"""

from __future__ import annotations

# --- World clock ---
WORLD_MAX_YEARS = 200  # the horizon: the run ends here, mid-life or not

# --- Player lifespan ---
LIFESPAN_CAP = 80  # natural maximum age; reaching it is death by LIFESPAN.
# Death before the cap only comes from a registered hazard (see mortality.py);
# there is no default one.
REINCARNATION_GAP_YEARS = 10  # death -> next playable life, world-only years

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
