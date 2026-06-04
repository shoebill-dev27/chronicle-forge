"""Heritage promotion and the reach/longevity scoring formula (section D)."""

from __future__ import annotations

from chronicle_forge import compute_heritage_score, generate_world, promote_heritage
from chronicle_forge.causal import CausalGraph
from chronicle_forge.enums import CausalEdgeKind, EventScale, HeritageType, SeedDomain
from chronicle_forge.generation import fire_seeds, generate_events
from chronicle_forge.heritage import qualifies_as_heritage
from chronicle_forge.models import CausalNode, CausalSeed


def _school_with_descendants(world, n_descendants):
    """Plant a school seed, fire it, and attach n descendant events."""
    world.current_year = 0
    world.seeds.append(
        CausalSeed(id="seed-school", domain=SeedDomain.HERITAGE, magnitude=80)
    )
    fired = fire_seeds(world)
    founding = generate_events(world, fired)[0]
    graph = CausalGraph.from_world(world)
    for i in range(n_descendants):
        child = CausalNode(
            id=f"node-c{i}", scale=EventScale.SMALL, domain=SeedDomain.HERITAGE, year=2
        )
        graph.add_node(child)
        graph.add_edge(founding.id, child.id, kind=CausalEdgeKind.ENABLE)
    return graph


def test_score_formula_separates_reach_and_longevity():
    # weight * longevity * (1 + reach)
    assert compute_heritage_score(longevity=10, reach=0, weight=1) == 10
    assert compute_heritage_score(longevity=10, reach=2, weight=2) == 60
    assert compute_heritage_score(longevity=0, reach=5, weight=2) == 0


def test_promotion_gate_rejects_insignificant_legacy():
    # reach below the gate (default 4) must not promote.
    assert qualifies_as_heritage(reach=0, longevity=15, score=999) is False
    assert qualifies_as_heritage(reach=4, longevity=2, score=999) is False
    assert qualifies_as_heritage(reach=4, longevity=12, score=150) is True


def test_heritage_promoted_when_gate_met():
    world = generate_world(seed=3)
    graph = _school_with_descendants(world, n_descendants=4)
    world.current_year = 15  # longevity 15, reach 4 -> qualifies
    promoted = promote_heritage(world, graph)

    assert len(promoted) == 1
    h = promoted[0]
    assert h.type == HeritageType.SCHOOL
    assert h.longevity == 15
    assert h.reach == 4
    assert h.heritage_score == compute_heritage_score(15, 4, weight=2)


def test_low_reach_seed_is_not_promoted():
    world = generate_world(seed=3)
    graph = _school_with_descendants(world, n_descendants=1)  # reach 1 < gate
    world.current_year = 15
    assert promote_heritage(world, graph) == []
    assert world.heritage == []
