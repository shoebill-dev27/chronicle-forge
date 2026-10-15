"""What a person knows: first-hand, discrete, and theirs alone.

What this pins. A person who was present for an event knows it, in the year it
happened, once however many times they see it reported. Nothing else
establishes knowledge: not being somebody's parent, not twenty years spent
beside them, not standing in the same village as an event the world cannot
place. The dead keep what they knew, and the next life starts knowing none of
it, because knowledge belongs to the person and the player is not a person.

And what it refuses: there is no confidence, intensity or valence anywhere in
the record, the event's own words are never copied into it, and the old
affect-bearing ``Memory`` system is left exactly as it was.
"""

from __future__ import annotations

import io

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge import knowledge as kn
from chronicle_forge import relationship as rel
from chronicle_forge.enums import (
    EventScale,
    KnowledgeSource,
    RoutineKind,
    SeedDomain,
)
from chronicle_forge.knowledge import KnowledgeRefused
from chronicle_forge.life import begin_life, end_life
from chronicle_forge.macro import advance_year
from chronicle_forge.models import CausalNode, PersonKnowledge
from chronicle_forge.play import view
from chronicle_forge.play.routine_session import run_routine_world
from chronicle_forge.worldgen import generate_world


def _world(seed=4):
    world = generate_world(seed)
    return world, begin_life(world)


def _neighbours(world, actor):
    return [
        p
        for p in pop.adults(world)
        if p.id != actor.id and p.lifecycle.location_id == actor.lifecycle.location_id
    ]


def _event_here(world, person, *, title="somebody rises to power", actors=None):
    """A real node in the graph, placed where this person is by naming them."""
    node = CausalNode(
        id=f"node-test-{len(world.causal_nodes):04d}",
        scale=EventScale.SMALL,
        domain=SeedDomain.GOVERNANCE,
        year=world.current_year,
        title=title,
        actors=actors if actors is not None else [person.id],
    )
    world.causal_nodes.append(node)
    return node


def _run(seed, commands, life_cap=1):
    it = iter(commands)
    out = io.StringIO()
    world = run_routine_world(
        seed, reader=lambda: next(it, None), writer=out.write, life_cap=life_cap
    )
    return world, out.getvalue()


def _played_life(seed=4, life_cap=1):
    """A whole life of one routine, which is a life with observations in it."""
    return _run(seed, ["work at"] + ["continue 10"] * 7, life_cap=life_cap)


# --- being there is what makes you know -------------------------------------


def test_a_life_that_saw_things_knows_them():
    world, text = _played_life()
    me = world.lives[0].person_id

    known = kn.knowledge_of(world, me)
    assert known, "a sixty-four year life saw nothing"
    assert all(k.source is KnowledgeSource.OBSERVED for k in known)
    assert len(known) == text.count("  Year ")


def test_knowing_is_a_reference_and_never_a_copy():
    world, _ = _played_life()
    me = world.lives[0].person_id
    ids = {n.id for n in world.causal_nodes}

    for row in kn.knowledge_of(world, me):
        assert row.event_id in ids
        assert set(row.model_dump()) == {
            "person_id",
            "event_id",
            "learned_year",
            "source",
        }


def test_the_record_holds_no_reading_of_any_kind():
    fields = set(PersonKnowledge.model_fields)
    assert not fields & {
        "confidence",
        "certainty",
        "intensity",
        "importance",
        "valence",
        "familiarity",
        "strength",
        "decay_rate",
    }


def test_seeing_the_same_thing_twice_is_one_piece_of_knowledge():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    advance_year(world)
    node = _event_here(world, me)

    first = kn.learn(world, me.id, node.id)
    again = kn.learn(world, me.id, node.id)

    assert first is not None and again is None
    assert len(kn.knowledge_of(world, me.id)) == 1


def test_the_year_you_first_knew_does_not_move():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    advance_year(world)
    node = _event_here(world, me)
    kn.learn(world, me.id, node.id)
    first_year = kn.knowledge_of(world, me.id)[0].learned_year

    for _ in range(12):
        advance_year(world)
    kn.learn(world, me.id, node.id)

    assert kn.knowledge_of(world, me.id)[0].learned_year == first_year


def test_somebody_who_was_there_knew_it_the_year_it_happened():
    """Not the year the session got around to reporting it."""
    world, _ = _played_life()
    me = world.lives[0].person_id
    by_id = {n.id: n for n in world.causal_nodes}

    for row in kn.knowledge_of(world, me):
        assert row.learned_year == by_id[row.event_id].year


def test_how_the_years_were_typed_changes_nothing_about_what_is_known():
    chunked, _ = _run(4, ["work at"] + ["continue 10"] * 7)
    yearly, _ = _run(4, ["work at"] + ["continue 1"] * 64)

    assert kn.knowledge_of(chunked, chunked.lives[0].person_id) == kn.knowledge_of(
        yearly, yearly.lives[0].person_id
    )


def test_knowledge_is_ordered_by_when_it_was_learned():
    world, _ = _played_life()
    years = [k.learned_year for k in kn.knowledge_of(world, world.lives[0].person_id)]
    assert years == sorted(years)


def test_the_same_seed_and_commands_are_known_the_same_way():
    a, _ = _run(17, ["work at", "continue 10", "work with 1", "continue 10"])
    b, _ = _run(17, ["work at", "continue 10", "work with 1", "continue 10"])
    assert a.knowledge == b.knowledge


# --- and nothing else does --------------------------------------------------


def test_what_the_world_cannot_place_stays_unknown():
    """A faction war is real, is not observable, and so is not known."""
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    war = _event_here(
        world,
        me,
        title="war between two factions",
        actors=["faction-0001", "faction-0002"],
    )

    assert view.observed_events(world, me.id, [war]) == []
    assert not kn.knows(world, me.id, war.id)


def test_a_played_world_produces_only_events_the_world_can_place():
    """A measured property of the current engine, not a guarantee: everything
    a routine-first run generates is a tracked person rising to power, and a
    person is somewhere. Faction wars need rival power the quiet years never
    build, and wildcards need activity seeds a played life never plants — so
    the filter withholds nothing here, and is exercised on an event the world
    genuinely cannot place."""
    world, _ = _played_life()
    assert world.causal_nodes
    assert all(view._event_place(world, n) is not None for n in world.causal_nodes)

    me = pop.person_by_id(world, world.lives[0].person_id)
    war = _event_here(
        world, me, title="war between two factions", actors=["faction-0001"]
    )
    assert view.observed_events(world, me.id, [war]) == []
    assert not kn.knows(world, me.id, war.id)


def test_standing_in_the_same_village_is_not_knowing():
    """Co-location makes an event *observable*; only observation records it."""
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    neighbour = _neighbours(world, me)[0]
    advance_year(world)
    node = _event_here(world, neighbour)

    assert view.observed_events(world, me.id, [node])  # they could have seen it
    assert not kn.knows(world, me.id, node.id)  # nobody said they did
    assert kn.knowledge_of(world, neighbour.id) == []


def test_twenty_years_beside_somebody_transmits_nothing():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    other = _neighbours(world, me)[0]
    rt.begin_routine(world, RoutineKind.WORK_WITH, other.id)
    for _ in range(20):
        advance_year(world)
    node = _event_here(world, me)
    kn.learn(world, me.id, node.id)

    tie = rel.relationship_between(world, me.id, other.id)
    assert tie is not None and tie.shared_years == 20
    assert kn.knows(world, me.id, node.id)
    assert not kn.knows(world, other.id, node.id)
    assert kn.knowledge_of(world, other.id) == []


def test_being_somebodys_parent_transmits_nothing():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    parent_id = next(
        p.lineage.parent_ids[0] for p in pop.living(world) if p.lineage.parent_ids
    )
    child = next(p for p in pop.living(world) if parent_id in p.lineage.parent_ids)
    advance_year(world)
    node = _event_here(world, me)
    kn.learn(world, me.id, node.id)

    # and the other direction, from a parent who knows something
    kn.learn(world, parent_id, node.id)

    assert kn.knows(world, parent_id, node.id)
    assert not kn.knows(world, child.id, node.id)
    assert kn.knowledge_of(world, child.id) == []


def test_the_world_refuses_knowledge_of_what_did_not_happen():
    world, life = _world()
    advance_year(world)
    node = _event_here(world, pop.person_by_id(world, life.person_id))

    with pytest.raises(KnowledgeRefused):
        kn.learn(world, "npc-9999", node.id)
    with pytest.raises(KnowledgeRefused):
        kn.learn(world, life.person_id, "node-9999")
    assert world.knowledge == []


def test_a_stranger_simply_knows_nothing():
    world, _ = _world()
    assert kn.knowledge_of(world, "npc-9999") == []
    assert not kn.knows(world, "npc-9999", "node-0000")


# --- death and the next life ------------------------------------------------


def test_the_dead_keep_what_they_knew():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    advance_year(world)
    node = _event_here(world, me)
    kn.learn(world, me.id, node.id)
    end_life(world, life, None)
    for _ in range(25):
        advance_year(world)

    assert not me.alive
    assert kn.knows(world, me.id, node.id)
    assert [k.event_id for k in kn.knowledge_of(world, me.id)] == [node.id]
    assert [n.title for n in kn.known_events(world, me.id)] == [node.title]


def test_the_next_life_begins_knowing_none_of_it():
    world, _ = _played_life(life_cap=2)
    first, second = world.lives[0].person_id, world.lives[1].person_id

    assert kn.knowledge_of(world, first)
    assert kn.knowledge_of(world, second) == []
    assert all(k.person_id == first for k in world.knowledge)


def test_a_successor_who_lives_learns_only_their_own_years():
    world, _ = _run(4, (["work at"] + ["continue 10"] * 7) * 2, life_cap=2)
    first, second = world.lives[0].person_id, world.lives[1].person_id
    theirs = {k.event_id for k in kn.knowledge_of(world, second)}
    predecessors = {k.event_id for k in kn.knowledge_of(world, first)}

    assert theirs and predecessors
    assert theirs.isdisjoint(predecessors)
    for row in kn.knowledge_of(world, second):
        assert row.learned_year > world.lives[0].death_year


def test_a_second_person_who_sees_it_gets_their_own_row():
    """Knowing is per person, not per event: the registry holds one row each,
    and the first one knowing it is not the second one knowing it."""
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    other = _neighbours(world, me)[0]
    advance_year(world)
    node = _event_here(world, me)

    kn.learn(world, me.id, node.id)
    assert not kn.knows(world, other.id, node.id)

    for _ in range(4):
        advance_year(world)
    kn.learn(world, other.id, node.id)

    mine, theirs = kn.knowledge_of(world, me.id), kn.knowledge_of(world, other.id)
    assert [k.event_id for k in mine] == [k.event_id for k in theirs] == [node.id]
    assert mine[0].learned_year == theirs[0].learned_year == node.year
    assert sorted(kn.who_knows(world, node.id)) == sorted([me.id, other.id])


def test_who_knows_an_event_is_answerable_from_the_world():
    world, _ = _played_life(life_cap=2)
    me = world.lives[0].person_id
    event_id = kn.knowledge_of(world, me)[0].event_id

    assert kn.who_knows(world, event_id) == [me]


# --- the page -------------------------------------------------------------


def test_no_event_identifier_reaches_the_player():
    _, text = _played_life(life_cap=2)
    assert "node-" not in text
    assert "observed" not in text


# --- replay ---------------------------------------------------------------


def test_a_recipe_replays_into_the_same_knowledge():
    from chronicle_forge.persistence import build_recipe, replay_transcript

    commands = ["work at", "continue 10", "work with 1", "continue 10", "continue 10"]
    lived, lived_text = _run(4, commands, life_cap=2)
    recipe = build_recipe(
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=commands,
        loop="routine",
    )
    replayed, replayed_text = replay_transcript(recipe)

    assert replayed_text == lived_text
    assert replayed.knowledge == lived.knowledge
    assert replayed.knowledge


def test_a_saved_recipe_round_trips_what_was_known(tmp_path):
    from chronicle_forge.persistence import (
        build_recipe,
        read_recipe,
        replay_transcript,
        save_recipe,
    )

    commands = ["work at", "continue 10", "continue 10", "continue 10"]
    lived, _ = _run(4, commands, life_cap=2)
    path = tmp_path / "r.json"
    save_recipe(
        build_recipe(
            seed=4,
            max_year=config.WORLD_MAX_YEARS,
            mode="human",
            inputs=commands,
            loop="routine",
        ),
        path,
    )

    reloaded, _ = replay_transcript(read_recipe(path))
    assert reloaded.knowledge == lived.knowledge


def test_the_dead_are_still_answerable_after_a_replay():
    from chronicle_forge.persistence import build_recipe, replay_transcript

    commands = ["work at"] + ["continue 10"] * 14
    recipe = build_recipe(
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=commands,
        loop="routine",
    )
    world, _ = replay_transcript(recipe)
    dead = world.lives[0]

    assert dead.death_year is not None
    assert kn.knowledge_of(world, dead.person_id)


# --- the old affect system is untouched -------------------------------------


def test_the_old_memory_system_is_left_exactly_as_it_was():
    from chronicle_forge.autoplay import simulate_world

    world = simulate_world(4, mode="opportunity")
    assert world.memories, "the legacy funnel still forms affect-bearing memories"
    assert world.knowledge == []
    assert any(m.valence or m.intensity for m in world.memories)


def test_a_played_life_forms_no_old_memories_and_no_relations():
    world, _ = _played_life()
    assert world.knowledge
    assert world.memories == []
    assert all(not p.relations for p in world.npcs)
