"""Heritage promotion and the reach/longevity scoring formula (section D)."""

from __future__ import annotations

from chronicle_forge import compute_heritage_score, generate_world, promote_heritage
from chronicle_forge.causal import CausalGraph
from chronicle_forge.enums import CausalEdgeKind, EventScale, HeritageType, SeedDomain
from chronicle_forge.generation import fire_seeds, generate_events
from chronicle_forge.models import CausalNode, CausalSeed


def test_score_formula_separates_reach_and_longevity():
    # weight * longevity * (1 + reach)
    assert compute_heritage_score(longevity=10, reach=0, weight=1) == 10
    assert compute_heritage_score(longevity=10, reach=2, weight=2) == 60
    assert compute_heritage_score(longevity=0, reach=5, weight=2) == 0


def test_heritage_promoted_from_fired_school_seed():
    world = generate_world(seed=3)
    world.current_year = 0
    world.seeds.append(
        CausalSeed(id="seed-school", domain=SeedDomain.HERITAGE, magnitude=80)
    )
    fired = fire_seeds(world)
    generate_events(world, fired)

    world.current_year = 15  # the school has propagated for 15 years
    promoted = promote_heritage(world)

    assert len(promoted) == 1
    h = promoted[0]
    assert h.type == HeritageType.SCHOOL
    assert h.longevity == 15
    assert h.reach == 0
    assert h.heritage_score == compute_heritage_score(15, 0, weight=2)


def test_reach_increases_score():
    world = generate_world(seed=3)
    world.current_year = 0
    world.seeds.append(
        CausalSeed(id="seed-school", domain=SeedDomain.HERITAGE, magnitude=80)
    )
    fired = fire_seeds(world)
    nodes = generate_events(world, fired)
    founding = nodes[0]

    # Attach a downstream descendant event to the founding node.
    graph = CausalGraph.from_world(world)
    child = CausalNode(
        id="node-child", scale=EventScale.SMALL, domain=SeedDomain.HERITAGE, year=5
    )
    graph.add_node(child)
    graph.add_edge(founding.id, child.id, kind=CausalEdgeKind.ENABLE)

    world.current_year = 15
    h = promote_heritage(world, graph)[0]
    assert h.reach == 1
    assert h.heritage_score == compute_heritage_score(15, 1, weight=2)
