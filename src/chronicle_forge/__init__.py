"""Chronicle Forge: a history-creation RPG / reincarnation roguelite.

See docs/design.md for the design-locked specification. The deterministic engine,
the AI narration call sites (opt-in, deterministic fallback), persistence, the
interactive play loop, and the P10–P14 read-model lenses are all in place; the P15
Application Layer (:mod:`chronicle_forge.app`) composes them into the
play → save → explore → share path that the ``chronicle-forge`` CLI wraps.
"""

from __future__ import annotations

from .activity import perform_activity
from .causal import CausalCycleError, CausalGraph
from .combat import player_fight, resolve_combat
from .discovery import explore_dungeon
from .generation import fire_seeds, generate_events
from .heritage import compute_heritage_score, promote_heritage
from .life import begin_life, end_life, lifespan_reached
from .macro import (
    WorldHorizonReached,
    advance_to_next_life,
    advance_year,
    derive_rng,
    fire_probabilistic_seeds,
    step_factions,
    step_wildcards,
    time_skip,
)
from .memory import form_memory
from .population import adults, give_birth, step_population, successor
from .routine import (
    active_routine,
    begin_routine,
    change_routine,
    continue_routine,
    end_routine,
    routine_years,
    routines_of,
)
from .npc import step_npc
from .pipeline import advance_history
from .powers import foresight, imprint, manifest_amplify
from .theme import compute_theme
from .ai import (
    EndingNarrator,
    HistoryBookGenerator,
    generate_history_book,
    get_ai_client,
    narrate_ending,
)
from .autoplay import simulate_report, simulate_world
from .ending import classify_ending
from .views import (
    full_report,
    render_causal_trace,
    render_heritage_ranking,
    render_npc_codex,
    render_personal_history,
    render_world_summary,
)
from .worldgen import generate_world

__version__ = "0.4.1"

__all__ = [
    # world / causal core (P0/P1)
    "generate_world",
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
    "step_population",
    "adults",
    "give_birth",
    "successor",
    "active_routine",
    "begin_routine",
    "change_routine",
    "continue_routine",
    "end_routine",
    "routine_years",
    "routines_of",
    "player_fight",
    "resolve_combat",
    # macro loop (P3)
    "time_skip",
    "advance_year",
    "WorldHorizonReached",
    "advance_to_next_life",
    "fire_probabilistic_seeds",
    "step_wildcards",
    "step_factions",
    "derive_rng",
    # observability (P5)
    "simulate_world",
    "simulate_report",
    "classify_ending",
    "full_report",
    "render_world_summary",
    "render_personal_history",
    "render_causal_trace",
    "render_heritage_ranking",
    "render_npc_codex",
    # AI integration (P4)
    "get_ai_client",
    "generate_history_book",
    "narrate_ending",
    "HistoryBookGenerator",
    "EndingNarrator",
    "__version__",
]
