"""Chronicle Forge: a history-creation RPG / reincarnation roguelite.

See docs/design.md for the design-locked specification (v0.3). This package is
the rules-only core; AI integration (the 5 bounded call sites) and the
presentation layer are added in later roadmap phases.
"""

from __future__ import annotations

from .activity import perform_activity
from .causal import CausalCycleError, CausalGraph
from .combat import player_fight, resolve_combat
from .discovery import explore_dungeon
from .generation import fire_seeds, generate_events
from .heritage import compute_heritage_score, promote_heritage
from .life import begin_life, end_life, lifespan_reached
from .memory import form_memory
from .npc import step_npc
from .pipeline import advance_history
from .powers import foresight, imprint, manifest_amplify
from .theme import compute_theme
from .timeskip import compute_skip_years
from .worldgen import generate_world

__version__ = "0.3.0"

__all__ = [
    # world / causal core (P0/P1)
    "generate_world",
    "compute_skip_years",
    "CausalGraph",
    "CausalCycleError",
    "fire_seeds",
    "generate_events",
    "compute_theme",
    "promote_heritage",
    "compute_heritage_score",
    "advance_history",
    # micro loop (P2)
    "begin_life",
    "end_life",
    "lifespan_reached",
    "perform_activity",
    "explore_dungeon",
    "form_memory",
    "imprint",
    "foresight",
    "manifest_amplify",
    "step_npc",
    "player_fight",
    "resolve_combat",
    "__version__",
]
