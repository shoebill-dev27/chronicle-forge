"""History generation pipeline orchestration (P1 integration).

Runs one rules-only generation step over the world in the design order:
fire seeds -> generate events (nodes + edges) -> compute theme -> promote
heritage. AI narration (P4) layers on top of this without changing state.
"""

from __future__ import annotations

from .causal import CausalGraph
from .generation import fire_seeds, generate_events
from .heritage import promote_heritage
from .models import World
from .theme import compute_theme


def advance_history(world: World) -> dict:
    """Advance generated history for the world's current year. Returns a summary
    of what fired/was created this step."""
    graph = CausalGraph.from_world(world)
    fired = fire_seeds(world)
    nodes = generate_events(world, fired, graph)
    theme = compute_theme(world)
    heritage = promote_heritage(world, graph)
    return {
        "fired_seeds": fired,
        "new_nodes": nodes,
        "theme": theme,
        "heritage": heritage,
    }
