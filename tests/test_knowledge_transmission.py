"""Telling: the first act by which one person changes what another knows.

What this pins. A person who knows an event can tell a living person about it,
and from then on the recipient knows it — told, and by whom, in the year they
were told. Telling is the act; years side by side still transmit nothing. The
first way somebody came to know a fact is the one kept: telling them again,
or telling them what they saw, changes nothing. What is told survives the
teller's death, and the next life starts knowing none of it.

In the played life the recipient is never chosen: it is whoever the current
routine is with. ``tell`` lists, ``tell <n>`` tells, and neither moves the
clock, the routine or the tie.

And what it refuses: a fact the teller does not know, a person who is not
there, and every effect beyond the one row — no seed, no heritage, no theme,
no memory, no relation.
"""

from __future__ import annotations

import io

import pytest
from pydantic import ValidationError

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge import knowledge as kn
from chronicle_forge import relationship as rel
from chronicle_forge.enums import EventScale, KnowledgeSource, RoutineKind, SeedDomain
from chronicle_forge.knowledge import KnowledgeRefused
from chronicle_forge.life import begin_life
from chronicle_forge.macro import advance_year
from chronicle_forge.models import CausalNode, PersonKnowledge
from chronicle_forge.play import routine_session as rs
from chronicle_forge.play import view
from chronicle_forge.routine import RoutineRefused
from chronicle_forge.worldgen import generate_world

# Seed 4, as measured: Vewen works until Sellin rises to power in year 14, then
# keeps company with Vegar — [9] on the year-20 list, the youngest there, so
# Vegar outlives her — tells Vegar, and lives on until she dies in year 64.
TELL_THEN_DIE = [
    "work at",
    "continue 10",
    "continue 10",
    "associate with 9",
    "tell",
    "tell 1",
    "tell",
] + ["continue 10"] * 5


def _world(seed=4):
    world = generate_world(seed)
    return world, begin_life(world)


def _neighbours(world, actor):
    return [
        p
        for p in pop.adults(world)
        if p.id != actor.id and p.lifecycle.location_id == actor.lifecycle.location_id
    ]


def _event_here(world, person, *, title="somebody rises to power"):
    node = CausalNode(
        id=f"node-test-{len(world.causal_nodes):04d}",
        scale=EventScale.SMALL,
        domain=SeedDomain.GOVERNANCE,
        year=world.current_year,
        title=title,
        actors=[person.id],
    )
    world.causal_nodes.append(node)
    return node


def _seen(seed=4):
    """A world where the player saw one thing, with two neighbours who did not."""
    world, life = _world(seed)
    me = pop.person_by_id(world, life.person_id)
    b, c = _neighbours(world, me)[:2]
    advance_year(world)
    node = _event_here(world, me)
    kn.learn(world, me.id, node.id)
    return world, me, b, c, node


def _run(seed, commands, life_cap=1):
    it = iter(commands)
    out = io.StringIO()
    world = rs.run_routine_world(
        seed, reader=lambda: next(it, None), writer=out.write, life_cap=life_cap
    )
    return world, out.getvalue()


def _row(world, person_id, event_id):
    return next(
        k
        for k in world.knowledge
        if k.person_id == person_id and k.event_id == event_id
    )


# --- the record ---------------------------------------------------------------


def test_there_are_exactly_two_ways_to_know():
    assert set(KnowledgeSource) == {KnowledgeSource.OBSERVED, KnowledgeSource.TOLD}


def test_the_record_gained_only_the_teller():
    assert set(PersonKnowledge.model_fields) == {
        "person_id",
        "event_id",
        "learned_year",
        "source",
        "learned_from_person_id",
    }


def test_a_teller_is_recorded_exactly_when_told():
    PersonKnowledge(person_id="a", event_id="e", learned_year=1)
    PersonKnowledge(
        person_id="b",
        event_id="e",
        learned_year=1,
        source=KnowledgeSource.TOLD,
        learned_from_person_id="a",
    )
    with pytest.raises(ValidationError):
        PersonKnowledge(
            person_id="b", event_id="e", learned_year=1, source=KnowledgeSource.TOLD
        )
    with pytest.raises(ValidationError):
        PersonKnowledge(
            person_id="b", event_id="e", learned_year=1, learned_from_person_id="a"
        )
    with pytest.raises(ValidationError):
        PersonKnowledge(
            person_id="a",
            event_id="e",
            learned_year=1,
            source=KnowledgeSource.TOLD,
            learned_from_person_id="a",
        )


def test_a_row_written_before_telling_existed_still_loads():
    row = PersonKnowledge.model_validate(
        {"person_id": "a", "event_id": "e", "learned_year": 3, "source": "observed"}
    )
    assert row.learned_from_person_id is None


# --- the domain act -------------------------------------------------------------


def test_who_saw_it_has_no_teller():
    world, me, _, _, node = _seen()
    row = _row(world, me.id, node.id)
    assert row.source is KnowledgeSource.OBSERVED
    assert row.learned_from_person_id is None


def test_being_told_is_knowing_and_from_whom():
    world, me, b, _, node = _seen()
    for _ in range(5):
        advance_year(world)

    row = kn.tell(world, me.id, b.id, node.id)

    assert kn.knows(world, b.id, node.id)
    assert row == _row(world, b.id, node.id)
    assert row.source is KnowledgeSource.TOLD
    assert row.learned_from_person_id == me.id
    assert row.learned_year == world.current_year != node.year


def test_telling_someone_twice_is_one_piece_of_knowledge():
    world, me, b, _, node = _seen()
    first = kn.tell(world, me.id, b.id, node.id)
    advance_year(world)
    again = kn.tell(world, me.id, b.id, node.id)

    assert first is not None and again is None
    assert kn.knowledge_of(world, b.id) == [first]


def test_the_first_teller_is_kept():
    world, me, b, c, node = _seen()
    kn.tell(world, me.id, b.id, node.id)
    kn.tell(world, me.id, c.id, node.id)
    before = _row(world, c.id, node.id)
    advance_year(world)

    assert kn.tell(world, b.id, c.id, node.id) is None
    assert _row(world, c.id, node.id) == before
    assert before.learned_from_person_id == me.id


def test_telling_somebody_what_they_saw_changes_nothing():
    world, me, b, _, node = _seen()
    kn.learn(world, b.id, node.id)
    before = _row(world, b.id, node.id)
    advance_year(world)

    assert kn.tell(world, me.id, b.id, node.id) is None
    assert _row(world, b.id, node.id) == before
    assert before.source is KnowledgeSource.OBSERVED


def test_seeing_what_you_were_told_changes_nothing():
    world, me, b, _, node = _seen()
    told = kn.tell(world, me.id, b.id, node.id)
    assert kn.learn(world, b.id, node.id) is None
    assert _row(world, b.id, node.id) == told


def test_you_cannot_tell_what_you_do_not_know():
    world, me, b, c, node = _seen()
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, b.id, c.id, node.id)
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, b.id, "node-9999")
    assert kn.knowledge_of(world, b.id) == kn.knowledge_of(world, c.id) == []


def test_only_the_living_tell_and_are_told():
    world, me, b, c, node = _seen()
    kn.tell(world, me.id, c.id, node.id)
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, "npc-9999", node.id)
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, "npc-9999", b.id, node.id)

    b.alive = False
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, b.id, node.id)
    c_row = _row(world, c.id, node.id)
    me.alive = False
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, c.id, node.id)
    assert _row(world, c.id, node.id) == c_row


def test_nobody_tells_themselves():
    world, me, _, _, node = _seen()
    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, me.id, node.id)


def test_a_chain_of_telling_is_one_fact_and_three_knowers():
    world, a, b, c, node = _seen()
    nodes_before = [n.model_copy() for n in world.causal_nodes]
    kn.tell(world, a.id, b.id, node.id)
    advance_year(world)
    kn.tell(world, b.id, c.id, node.id)

    assert kn.who_knows(world, node.id) == [a.id, b.id, c.id]
    rows = [_row(world, p, node.id) for p in (a.id, b.id, c.id)]
    assert [(r.source, r.learned_from_person_id) for r in rows] == [
        (KnowledgeSource.OBSERVED, None),
        (KnowledgeSource.TOLD, a.id),
        (KnowledgeSource.TOLD, b.id),
    ]
    # followed back through the rows, the path ends with whoever was there
    path, at = [c.id], _row(world, c.id, node.id)
    while at.learned_from_person_id is not None:
        path.append(at.learned_from_person_id)
        at = _row(world, at.learned_from_person_id, node.id)
    assert path == [c.id, b.id, a.id]
    # one event, referenced and never copied, and no new event made of it
    assert world.causal_nodes[: len(nodes_before)] == nodes_before
    assert len(world.causal_nodes) == len(nodes_before)
    assert all(node.title not in str(r.model_dump()) for r in rows)


def test_telling_changes_nothing_but_the_one_row():
    world, me, b, _, node = _seen()
    rt.begin_routine(world, RoutineKind.WORK_WITH, b.id)
    advance_year(world)
    before = world.model_dump(exclude={"knowledge"})
    rows_before = list(world.knowledge)

    kn.tell(world, me.id, b.id, node.id)

    assert world.model_dump(exclude={"knowledge"}) == before
    assert world.knowledge[: len(rows_before)] == rows_before
    assert len(world.knowledge) == len(rows_before) + 1


def test_years_together_still_transmit_nothing_untold():
    world, me, b, _, node = _seen()
    rt.begin_routine(world, RoutineKind.WORK_WITH, b.id)
    for _ in range(20):
        advance_year(world)
    assert rel.relationship_between(world, me.id, b.id).shared_years == 20
    assert not kn.knows(world, b.id, node.id)


# --- in the played life -------------------------------------------------------


def _played_until_seen():
    """Seed 4 played to year 20: Vewen has seen Sellin rise, in year 14."""
    world, life = _world()
    rs.handle(world, "work at")
    rs.handle(world, "continue 10")
    rs.handle(world, "continue 10")
    assert kn.knowledge_of(world, life.person_id)
    return world, life


@pytest.mark.parametrize("command", ["work with 1", "associate with 1"])
def test_you_can_tell_whoever_you_live_beside(command):
    world, life = _played_until_seen()
    rs.handle(world, command)
    target = rt.active_routine(world).target_person_id

    listing = rs.handle(world, "tell")
    told = rs.handle(world, "tell 1")

    assert listing.startswith(f"Things you can tell {view._name(world, target)}:")
    assert "[1] Year 14." in listing
    assert told.startswith(f"You tell {view._name(world, target)}:")
    assert _row(world, target, kn.knowledge_of(world, life.person_id)[0].event_id)


def test_working_alone_there_is_nobody_to_tell():
    world, _ = _played_until_seen()
    assert rt.active_routine(world).kind is RoutineKind.WORK_AT
    for line in ("tell", "tell 1"):
        with pytest.raises(RoutineRefused, match="nobody to tell"):
            rs.handle(world, line)


def test_an_unsettled_life_has_nobody_to_tell():
    world, _ = _world()
    with pytest.raises(RoutineRefused, match="nobody to tell"):
        rs.handle(world, "tell")


def test_knowing_nothing_there_is_nothing_to_tell():
    world, _ = _world()
    rs.handle(world, "work with 1")
    before = world.model_dump()
    assert "nothing to tell" in rs.handle(world, "tell")
    with pytest.raises(RoutineRefused):
        rs.handle(world, "tell 1")
    assert world.model_dump() == before


def test_only_what_they_do_not_know_is_offered():
    world, life = _played_until_seen()
    rs.handle(world, "work with 1")
    rs.handle(world, "tell 1")

    assert "already knows everything you know" in rs.handle(world, "tell")
    with pytest.raises(RoutineRefused):
        rs.handle(world, "tell 1")
    target = rt.active_routine(world).target_person_id
    assert len(kn.knowledge_of(world, target)) == 1


def test_only_your_own_knowledge_is_offered():
    world, life = _played_until_seen()
    rs.handle(world, "work with 1")
    target = rt.active_routine(world).target_person_id
    mine = {k.event_id for k in kn.knowledge_of(world, life.person_id)}
    offered = view.tellable(world, life.person_id, target)

    assert {f.event_id for f in offered} == mine
    assert len(world.causal_nodes) > len(mine)  # the engine knows more


def test_telling_takes_no_time_and_touches_no_tie():
    world, life = _played_until_seen()
    rs.handle(world, "work with 1")
    rs.handle(world, "continue 3")
    routine = rt.active_routine(world)
    target = routine.target_person_id
    year, span = world.current_year, routine.model_copy()
    shared = rel.relationship_between(world, life.person_id, target).shared_years

    rs.handle(world, "tell")
    rs.handle(world, "tell 1")

    assert world.current_year == year
    assert rt.active_routine(world) == span
    assert rt.routine_years(world, span) == 3
    assert rel.relationship_between(world, life.person_id, target).shared_years == (
        shared
    )


def test_what_the_player_reads_names_no_id():
    _, text = _run(4, TELL_THEN_DIE, life_cap=2)
    assert "You tell Vegar: year 14, Sellin rises to power." in text
    assert "node-" not in text and "npc-" not in text
    assert "told" not in text and "observed" not in text


def test_the_dead_teller_is_still_who_told_them():
    world, text = _run(4, TELL_THEN_DIE, life_cap=2)
    vewen, successor = world.lives[0].person_id, world.lives[1].person_id
    vegar = next(p for p in world.npcs if p.name == "Vegar")
    sellin = next(n for n in world.causal_nodes if n.title == "Sellin rises to power")

    assert world.lives[0].death_year == 64
    assert not pop.person_by_id(world, vewen).alive and vegar.alive
    told = _row(world, vegar.id, sellin.id)
    assert (told.source, told.learned_from_person_id, told.learned_year) == (
        KnowledgeSource.TOLD,
        vewen,
        20,
    )
    seen = _row(world, vewen, sellin.id)
    assert (seen.source, seen.learned_year) == (KnowledgeSource.OBSERVED, 14)
    # the next life is somebody else, and knows none of it
    assert kn.knowledge_of(world, successor) == []
    assert kn.who_knows(world, sellin.id) == [vewen, vegar.id]


def test_a_recipe_replays_the_telling_exactly():
    from chronicle_forge.persistence import build_recipe, replay_transcript

    lived, lived_text = _run(4, TELL_THEN_DIE, life_cap=60)
    recipe = build_recipe(
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=TELL_THEN_DIE,
        loop="routine",
    )
    replayed, replayed_text = replay_transcript(recipe)

    assert replayed_text == lived_text
    assert replayed.knowledge == lived.knowledge
    assert any(k.source is KnowledgeSource.TOLD for k in replayed.knowledge)


def test_a_played_telling_plants_nothing_and_forms_nothing():
    world, _ = _run(4, TELL_THEN_DIE, life_cap=2)
    without, _ = _run(4, [c for c in TELL_THEN_DIE if not c.startswith("tell")], 2)

    assert world.model_dump(exclude={"knowledge"}) == without.model_dump(
        exclude={"knowledge"}
    )
    assert [k for k in world.knowledge if k.source is KnowledgeSource.OBSERVED] == (
        without.knowledge
    )
    assert world.memories == [] and all(not p.relations for p in world.npcs)


# --- the version boundary -----------------------------------------------------


def test_a_recipe_from_before_telling_is_refused_not_reread():
    """Under 0.5.0, ``tell 1`` was an unknown command and changed nothing; here
    it changes what Vegar knows. Same text, different meaning — so a recipe
    from then is refused rather than silently replayed into another world."""
    from chronicle_forge.persistence import (
        ENGINE_VERSION,
        EngineVersionMismatch,
        Recipe,
        replay_transcript,
    )

    old = Recipe(
        engine_version="0.5.0-playable-routine",
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=TELL_THEN_DIE,
        loop="routine",
    )
    assert ENGINE_VERSION != old.engine_version
    with pytest.raises(EngineVersionMismatch):
        replay_transcript(old)


def test_the_help_page_names_telling():
    _, text = _run(4, [])
    assert text.startswith(rs.HELP)
    assert "  tell                    " in rs.HELP
    assert "  tell <n>                " in rs.HELP
