"""Heritage promotion and scoring (section D).

Heritage measures how long causality keeps propagating after the player's act.
Two dimensions are tracked separately:

- reach (breadth): the number of transitive descendant events in the causal DAG.
- longevity (depth): years the legacy has propagated since its founding event.

Composite score:

    heritage_score = round(weight * longevity * (1 + reach))

The ``(1 + reach)`` term lets a young legacy with no descendants still accrue
value from longevity, while reach amplifies it. ``weight`` favors culture- and
mentoring-oriented legacies, per the design principle that long-range causal
impact outranks combat power (section 1 / 8).
"""

from __future__ import annotations

from typing import Optional

from . import config
from .causal import CausalGraph
from .enums import CausalEdgeKind, HeritageType, SeedDomain
from .models import CausalNode, HeritageNode, World

DOMAIN_TO_HERITAGE_TYPE: dict[SeedDomain, HeritageType] = {
    SeedDomain.HERITAGE: HeritageType.SCHOOL,
    SeedDomain.MONUMENT: HeritageType.MONUMENT,
    SeedDomain.TECHNOLOGY: HeritageType.TECHNOLOGY,
    SeedDomain.GOVERNANCE: HeritageType.INSTITUTION,
    SeedDomain.FAITH: HeritageType.THOUGHT,
}

# Culture/mentoring-oriented legacies are weighted higher (section 1 / 8).
HERITAGE_TYPE_WEIGHT: dict[HeritageType, int] = {
    HeritageType.SCHOOL: 2,
    HeritageType.THOUGHT: 2,
    HeritageType.INSTITUTION: 2,
    HeritageType.HEIR: 2,
    HeritageType.TECHNOLOGY: 1,
    HeritageType.MONUMENT: 1,
}


def compute_heritage_score(longevity: int, reach: int, weight: int = 1) -> int:
    """Composite heritage score from separated reach and longevity."""
    return round(weight * max(0, longevity) * (1 + max(0, reach)))


def qualifies_as_heritage(reach: int, longevity: int, score: int) -> bool:
    """Composite promotion gate (P3.5): only significant legacies promote, so
    "heritage" stays rare and meaningful (was: every fired seed promoted)."""
    return (
        reach >= config.HERITAGE_MIN_REACH
        and longevity >= config.HERITAGE_MIN_LONGEVITY
        and score >= config.HERITAGE_MIN_SCORE
    )


def _triggered_node(world: World, seed_id: str) -> Optional[CausalNode]:
    """The event a seed TRIGGERed, if any."""
    for node in world.causal_nodes:
        for edge in node.caused_by:
            if edge.from_id == seed_id and edge.kind == CausalEdgeKind.TRIGGER:
                return node
    return None


def promote_heritage(
    world: World, graph: Optional[CausalGraph] = None
) -> list[HeritageNode]:
    """Promote eligible fired seeds to HeritageNodes and (re)compute their scores.

    Re-running in later years updates longevity/reach/score in place, modeling a
    legacy that keeps growing (section 5 delayed-reward design).
    """
    graph = graph or CausalGraph.from_world(world)
    existing = {h.seed_id: h for h in world.heritage}
    promoted: list[HeritageNode] = []

    for seed in world.seeds:
        if not seed.fired or seed.domain not in DOMAIN_TO_HERITAGE_TYPE:
            continue
        node = _triggered_node(world, seed.id)
        if node is None:
            continue

        htype = DOMAIN_TO_HERITAGE_TYPE[seed.domain]
        reach = len(graph.descendants(node.id))
        longevity = max(0, world.current_year - node.year)
        score = compute_heritage_score(longevity, reach, HERITAGE_TYPE_WEIGHT[htype])

        if seed.id in existing:
            h = existing[seed.id]
            h.reach, h.longevity, h.heritage_score = reach, longevity, score
        elif not qualifies_as_heritage(reach, longevity, score):
            continue  # not (yet) significant enough to be a legacy
        else:
            h = HeritageNode(
                id=f"her:{seed.id}",  # stable id (survives capping below)
                seed_id=seed.id,
                type=htype,
                reach=reach,
                longevity=longevity,
                heritage_score=score,
            )
            world.heritage.append(h)
            existing[seed.id] = h
        promoted.append(h)

    # Only the most significant legacies are remembered as heritage (P3.5 cap).
    if len(world.heritage) > config.HERITAGE_MAX_PER_WORLD:
        world.heritage.sort(key=lambda h: (-h.heritage_score, h.seed_id))
        del world.heritage[config.HERITAGE_MAX_PER_WORLD :]

    return [h for h in promoted if h in world.heritage]
