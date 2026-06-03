"""Rules-only history generation (section 9.2 / 9.3): seed firing and event
node/edge creation. No AI is involved; the rules engine owns the truth, and
edges are attached structurally so the resulting graph is traceable.
"""

from __future__ import annotations

from typing import Optional

from .causal import CausalGraph
from .enums import ActivationMode, CausalEdgeKind, EventScale
from .models import CausalNode, CausalSeed, World


def fire_seeds(world: World) -> list[CausalSeed]:
    """Fire every matured GUARANTEED seed at the world's current year.

    Deterministic: a seed is mature when ``current_year >= planted_year +
    maturation_time``. PROBABILISTIC seeds are deferred to P3 (probability is
    driven by world state there). Fired seeds are marked and returned in a
    stable order.
    """
    matured = [
        s
        for s in world.seeds
        if not s.fired
        and s.activation_mode == ActivationMode.GUARANTEED
        and world.current_year >= s.planted_year + s.maturation_time
    ]
    matured.sort(key=lambda s: (s.planted_year, s.id))
    for seed in matured:
        seed.fired = True
    return matured


def _scale_for(magnitude: int) -> EventScale:
    if magnitude >= 70:
        return EventScale.LARGE
    if magnitude >= 40:
        return EventScale.MEDIUM
    return EventScale.SMALL


def _next_node_id(world: World) -> str:
    return f"node-{len(world.causal_nodes):04d}"


def generate_events(
    world: World,
    fired_seeds: list[CausalSeed],
    graph: Optional[CausalGraph] = None,
) -> list[CausalNode]:
    """Create one event node per fired seed and attach causal edges.

    Each fired seed TRIGGERs a new node. Any pre-existing node sharing the
    seed's domain or target is linked as an AMPLIFY co-cause, producing
    multi-cause events. Because co-causes are always older nodes, no cycle can
    form (and ``add_edge`` enforces this regardless).
    """
    graph = graph or CausalGraph.from_world(world)
    new_nodes: list[CausalNode] = []

    for seed in fired_seeds:
        node = CausalNode(
            id=_next_node_id(world),
            scale=_scale_for(seed.magnitude),
            domain=seed.domain,
            year=world.current_year,
            title=f"{seed.domain.value} event ({seed.id})",
            actors=[seed.target_id] if seed.target_id else [],
        )
        graph.add_node(node)
        graph.add_edge(
            seed.id, node.id, weight=seed.magnitude, kind=CausalEdgeKind.TRIGGER
        )

        for prior in list(world.causal_nodes):
            if prior.id == node.id:
                continue
            shares_target = bool(seed.target_id) and seed.target_id in prior.actors
            if prior.domain == seed.domain or shares_target:
                graph.add_edge(
                    prior.id,
                    node.id,
                    weight=max(1, seed.magnitude // 2),
                    kind=CausalEdgeKind.AMPLIFY,
                )
        new_nodes.append(node)

    return new_nodes
