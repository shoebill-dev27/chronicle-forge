"""Shared read-only accessors for the reporting/demo-asset generators.

Everything here only reads a finished World; nothing mutates game state.
"""

from __future__ import annotations

from typing import Optional

from ..causal import CausalGraph
from ..enums import CausalEdgeKind, EventScale, LocationType
from ..models import CausalNode, CausalSeed, HeritageNode, Life, World
from ..theme import SEED_DOMAIN_TO_THEME

SCALE_ORDER = {EventScale.LARGE: 0, EventScale.MEDIUM: 1, EventScale.SMALL: 2}


def place(world: World) -> str:
    village = next(
        (loc for loc in world.locations if loc.type == LocationType.VILLAGE), None
    )
    return village.name if village else world.id


def life_index(world: World) -> dict:
    """Map life id -> 1-based ordinal."""
    return {life.id: i + 1 for i, life in enumerate(world.lives)}


def life_by_id(world: World, life_id: Optional[str]) -> Optional[Life]:
    return next((life for life in world.lives if life.id == life_id), None)


def life_label(world: World, life_id: Optional[str]) -> str:
    if life_id is None:
        return "world forces"
    idx = life_index(world).get(life_id)
    life = life_by_id(world, life_id)
    title = life.summary.title if life and life.summary else (life_id or "?")
    return f"Life {idx} ({title})" if idx else (title or life_id)


def seeds_of_life(world: World, life_id: str) -> list[CausalSeed]:
    return [s for s in world.seeds if s.planted_by_life_id == life_id]


def triggered_node(world: World, seed_id: str) -> Optional[CausalNode]:
    """The event a seed TRIGGERed, if any."""
    for node in world.causal_nodes:
        for edge in node.caused_by:
            if edge.from_id == seed_id and edge.kind == CausalEdgeKind.TRIGGER:
                return node
    return None


def seed_by_id(world: World, seed_id: str) -> Optional[CausalSeed]:
    return next((s for s in world.seeds if s.id == seed_id), None)


def events_caused_by(world: World, seed_ids: set) -> list[CausalNode]:
    return [
        n for n in world.causal_nodes if any(e.from_id in seed_ids for e in n.caused_by)
    ]


def life_world_impact(world: World, life_id: str) -> int:
    owned = {s.id for s in world.seeds if s.planted_by_life_id == life_id}
    return len(events_caused_by(world, owned))


def activity_counts(life: Life) -> str:
    counts: dict[str, int] = {}
    for rec in life.activity_log:
        counts[rec.category] = counts.get(rec.category, 0) + 1
    return ", ".join(f"{k}×{v}" for k, v in counts.items()) or "—"


def heritage_rows(world: World, top: Optional[int] = None) -> list[dict]:
    """Sorted heritage rows with derived-event counts and origin life."""
    from .labels import heritage_name, seed_label

    graph = CausalGraph.from_world(world)
    idx = life_index(world)
    rows = []
    for h in world.heritage:
        founding = triggered_node(world, h.seed_id)
        derived = len(graph.descendants(founding.id)) if founding else 0
        seed = seed_by_id(world, h.seed_id)
        origin_life = seed.planted_by_life_id if seed else None
        rows.append(
            {
                "name": heritage_name(h),
                "score": h.heritage_score,
                "longevity": h.longevity,
                "reach": h.reach,
                "source_seed": h.seed_id,
                "type": h.type.value,
                "domain": seed.domain.value if seed else "—",
                "derived_events": derived,
                "origin_life": (
                    f"Life {idx.get(origin_life, '?')}" if origin_life else "—"
                ),
                "origin_action": seed_label(world, h.seed_id),
            }
        )
    rows.sort(key=lambda r: (-r["score"], r["source_seed"]))
    return rows[:top] if top else rows


def dominant_axis(world: World):
    return world.theme.dominant
