"""End-to-end P1 causal core: a player seed fires, becomes an event, and remains
traceable back to the player (the core fun, section 1 / 9.4)."""

from __future__ import annotations

from chronicle_forge import advance_history, generate_world
from chronicle_forge.causal import CausalGraph
from chronicle_forge.enums import EventScale, SeedDomain
from chronicle_forge.models import CausalSeed


def _seed_world():
    world = generate_world(seed=11)
    npc_id = world.npcs[0].id
    # A player investment that matures in 5 years and targets an NPC.
    world.seeds.append(
        CausalSeed(
            id="seed-invest",
            domain=SeedDomain.ECONOMY,
            magnitude=80,
            target_id=npc_id,
            maturation_time=5,
            planted_year=0,
            planted_by_life_id="life-0001",
        )
    )
    return world, npc_id


def test_seed_does_not_fire_before_maturation():
    world, _ = _seed_world()
    world.current_year = 3  # before planted_year + maturation_time (5)
    result = advance_history(world)
    assert result["fired_seeds"] == []
    assert result["new_nodes"] == []


def test_seed_fires_creates_event_and_is_traceable():
    world, _ = _seed_world()
    world.current_year = 5  # matured
    result = advance_history(world)

    assert len(result["fired_seeds"]) == 1
    assert len(result["new_nodes"]) == 1
    node = result["new_nodes"][0]
    assert node.scale == EventScale.LARGE  # magnitude 80
    assert node.domain == SeedDomain.ECONOMY

    # Trace from the event back to a root and confirm the player seed is a cause.
    graph = CausalGraph.from_world(world)
    paths = graph.trace_to_roots(node.id)
    assert any("seed-invest" in path for path in paths)
    player_seeds = graph.player_seeds_in_ancestry(node.id)
    assert [s.id for s in player_seeds] == ["seed-invest"]


def test_pipeline_updates_theme_and_marks_seed_fired():
    world, _ = _seed_world()
    world.current_year = 5
    result = advance_history(world)

    assert world.seeds[0].fired is True
    assert len(world.theme.history) == 1
    assert result["theme"].dominant is not None


def test_multi_cause_event_links_prior_same_domain_node():
    world, _ = _seed_world()
    # A second economy seed maturing the same year produces a second node that
    # should pick up the first as an AMPLIFY co-cause.
    world.seeds.append(
        CausalSeed(
            id="seed-trade",
            domain=SeedDomain.ECONOMY,
            magnitude=50,
            maturation_time=5,
            planted_year=0,
        )
    )
    world.current_year = 5
    result = advance_history(world)

    assert len(result["new_nodes"]) == 2
    second = result["new_nodes"][1]
    # second node has TRIGGER from its seed plus an AMPLIFY co-cause edge.
    kinds = {e.kind.value for e in second.caused_by}
    assert "trigger" in kinds
    assert "amplify" in kinds
