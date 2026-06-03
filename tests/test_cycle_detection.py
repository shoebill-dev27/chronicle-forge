"""The causal graph must remain a DAG (section 9): edge insertion rejects
cycles and self-loops."""

from __future__ import annotations

import pytest

from chronicle_forge import CausalCycleError, CausalGraph, generate_world
from chronicle_forge.enums import EventScale, SeedDomain
from chronicle_forge.models import CausalNode, CausalSeed


def _world_with_seed():
    world = generate_world(seed=1)
    seed = CausalSeed(id="seed-x", domain=SeedDomain.GOVERNANCE, magnitude=60)
    world.seeds.append(seed)  # add before building the graph so it is registered
    return world, seed


def _node(node_id: str) -> CausalNode:
    return CausalNode(
        id=node_id, scale=EventScale.MEDIUM, domain=SeedDomain.GOVERNANCE, year=1
    )


def test_linear_chain_is_allowed():
    world, seed = _world_with_seed()
    g = CausalGraph.from_world(world)
    a, b = _node("node-A"), _node("node-B")
    g.add_node(a)
    g.add_node(b)
    g.add_edge(seed.id, a.id)
    g.add_edge(a.id, b.id)
    assert g.is_acyclic()


def test_back_edge_raises_cycle():
    world, seed = _world_with_seed()
    g = CausalGraph.from_world(world)
    a, b = _node("node-A"), _node("node-B")
    g.add_node(a)
    g.add_node(b)
    g.add_edge(seed.id, a.id)
    g.add_edge(a.id, b.id)
    with pytest.raises(CausalCycleError):
        g.add_edge(b.id, a.id)  # would close the loop A -> B -> A


def test_self_loop_raises_cycle():
    world, _ = _world_with_seed()
    g = CausalGraph.from_world(world)
    a = _node("node-A")
    g.add_node(a)
    with pytest.raises(CausalCycleError):
        g.add_edge(a.id, a.id)


def test_unknown_endpoints_rejected():
    world, _ = _world_with_seed()
    g = CausalGraph.from_world(world)
    a = _node("node-A")
    g.add_node(a)
    with pytest.raises(ValueError):
        g.add_edge("nonexistent", a.id)
    with pytest.raises(ValueError):
        g.add_edge(a.id, "nonexistent")  # effect must be an existing node
