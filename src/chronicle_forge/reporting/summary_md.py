"""summary.md (generated LAST): a 200-500 char factual digest of the world.

This is a summary *of the other assets*, not a primary source. Facts only, no
AI. Built to be reusable as a README/X blurb.
"""

from __future__ import annotations

from ..models import World
from ._data import heritage_rows, place

_MIN, _MAX = 200, 500


def summarize_world(world: World) -> str:
    rows = heritage_rows(world, top=1)
    top = rows[0] if rows else None

    resolved = [wc for wc in world.wildcards.wildcards if wc.status.value == "resolved"]
    wc_clause = (
        f", and {resolved[0].name} the {resolved[0].archetype.value} rose and ran "
        f"their course"
        if resolved
        else ""
    )
    legacy_clause = (
        f" Its greatest legacy, a {top['type']} (seed {top['source_seed']}), set "
        f"{top['derived_events']} later events in motion."
        if top
        else ""
    )

    text = (
        f"Seed {world.seed}: over {world.current_year} years and {len(world.lives)} "
        f"reincarnations in {place(world)}, one soul's deeds rippled into "
        f"{len(world.causal_nodes)} recorded events and {len(world.heritage)} lasting "
        f"legacies, and the world settled into the {world.ending_class}{wc_clause}."
        f"{legacy_clause} Every outcome can be traced back through event and seed to "
        f"the life that began it — the player's actions continued affecting history "
        f"long after death."
    )

    # Keep within the target band: drop the optional clauses if too long.
    if len(text) > _MAX:
        text = (
            f"Seed {world.seed}: over {world.current_year} years and "
            f"{len(world.lives)} reincarnations, one soul's deeds rippled into "
            f"{len(world.causal_nodes)} events and {len(world.heritage)} lasting "
            f"legacies, ending in the {world.ending_class}. Every outcome traces back "
            f"through event and seed to the life that began it — the player's actions "
            f"continued affecting history long after death."
        )
    return text
