"""Asking: the player may hear what somebody here knows, and how they came to
know it.

What this pins. A told row keeps the place it was told in, because people move
and that place cannot be read back afterwards. ``ask`` lists who is here;
``ask <n>`` reports that person's own knowledge — the event, and either that
they saw it or the year, the teller, the teller's age then and the place of the
telling. Asking takes no time, changes nothing, and teaches nobody anything,
the asker included.

The point of it is the next life: a successor who goes to where somebody their
predecessor told still lives can ask them, and read enough — a name, an age, a
year, a place — to recognise who told them. The engine never says who that was.
"""

from __future__ import annotations

import io

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge import knowledge as kn
from chronicle_forge.enums import (
    EventScale,
    KnowledgeSource,
    RoutineEndReason,
    SeedDomain,
)
from chronicle_forge.knowledge import KnowledgeRefused
from chronicle_forge.life import begin_life
from chronicle_forge.macro import advance_year
from chronicle_forge.models import CausalNode
from chronicle_forge.play import routine_session as rs
from chronicle_forge.play import view
from chronicle_forge.routine import RoutineRefused
from chronicle_forge.worldgen import generate_world

HOLLOWFEN, GREYWIND, THORNREACH = 1, 2, 3  # ``move`` numbers, in world order

# Seed 4, as measured (see test_knowledge_transmission): Vewen sees Sellin rise
# in year 14, tells Vegar of it in Hollowfen in year 20 and dies in year 64.
# The successor, Dunric, begins in Greywind Moor in year 74.
TELL_THEN_DIE = [
    "work at",
    "continue 10",
    "continue 10",
    "associate with 9",
    "tell",
    "tell 1",
    "tell",
] + ["continue 10"] * 5
GO_AND_ASK = ["move", f"move {HOLLOWFEN}", "ask", "ask 4"]
VEGAR = 4  # Vegar's number in Hollowfen in year 75

# What would announce the connection instead of leaving it to the player.
ATTRIBUTION = (
    "previous life",
    "past life",
    "former life",
    "your life",
    "you told",
    "told you",
    "was you",
    "were you",
    "yourself",
    "reincarnat",
    "soul",
    "prove",
)
# What would expose the engine's answer rather than a person's knowledge.
ENGINE_WORDS = ("cause", "because", "seed", "edge", "why", "led to", "npc-", "loc-")
ENUM_WORDS = ("observed", "told", "provenance", "knowledge", "source")


def _world(seed=4):
    world = generate_world(seed)
    return world, begin_life(world)


def _run(seed, commands, life_cap=2):
    it = iter(commands)
    out = io.StringIO()
    world = rs.run_routine_world(
        seed, reader=lambda: next(it, None), writer=out.write, life_cap=life_cap
    )
    return world, out.getvalue()


def _place(world, name):
    return next(loc for loc in world.locations if loc.name == name)


def _neighbours(world, person):
    return [
        p
        for p in pop.adults(world)
        if p.id != person.id and p.lifecycle.location_id == person.lifecycle.location_id
    ]


def _event(world, actor, title="somebody rises to power"):
    node = CausalNode(
        id=f"node-test-{len(world.causal_nodes)}",
        scale=EventScale.SMALL,
        domain=SeedDomain.GOVERNANCE,
        year=world.current_year,
        title=title,
        actors=[actor.id],
    )
    world.causal_nodes.append(node)
    return node


def _told(world):
    return next(k for k in world.knowledge if k.source is KnowledgeSource.TOLD)


# --- where a telling happened --------------------------------------------------


def test_a_telling_keeps_the_place_it_happened_and_a_seeing_has_none():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    b = _neighbours(world, me)[0]
    node = _event(world, me)
    seen = kn.learn(world, me.id, node.id)
    told = kn.tell(world, me.id, b.id, node.id)

    assert seen.told_at_location_id is None
    assert told.told_at_location_id == me.lifecycle.location_id


def test_the_place_of_a_telling_is_not_where_anybody_lives_now():
    """Vewen tells Vegar in Hollowfen and leaves for Thornreach the same year.
    Nothing but the row still says Hollowfen: Vewen lives elsewhere, and the
    span beside Vegar was closed in the year of the telling, so it covers no
    year at all."""
    world, _ = _run(4, TELL_THEN_DIE[:6] + [f"move {THORNREACH}"], life_cap=1)
    vewen = pop.person_by_id(world, world.lives[0].person_id)
    told = _told(world)
    beside = next(r for r in rt.routines_of(world, vewen.id) if r.target_person_id)

    assert told.told_at_location_id == _place(world, "Hollowfen").id
    assert vewen.lifecycle.location_id == _place(world, "Thornreach").id
    assert (beside.start_year, beside.end_year, beside.end_reason) == (
        20,
        20,
        RoutineEndReason.RELOCATED,
    )
    assert view.recollections(world, told.person_id)[0].told_in == "Hollowfen"


def test_telling_happens_in_one_place():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    elsewhere = next(
        p
        for p in pop.adults(world)
        if p.lifecycle.location_id != me.lifecycle.location_id
    )
    node = _event(world, me)
    kn.learn(world, me.id, node.id)

    with pytest.raises(KnowledgeRefused):
        kn.tell(world, me.id, elsewhere.id, node.id)
    assert not kn.knows(world, elsewhere.id, node.id)


def test_the_first_place_of_hearing_is_kept():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    b, c = _neighbours(world, me)[:2]
    node = _event(world, me)
    kn.learn(world, me.id, node.id)
    kn.tell(world, me.id, b.id, node.id)
    first = next(k for k in world.knowledge if k.person_id == b.id)
    kn.learn(world, c.id, node.id)
    advance_year(world)

    assert kn.tell(world, c.id, b.id, node.id) is None
    assert next(k for k in world.knowledge if k.person_id == b.id) == first


def test_the_tellers_age_is_read_from_the_teller():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    b = _neighbours(world, me)[0]
    node = _event(world, me)
    kn.learn(world, me.id, node.id)
    for _ in range(7):
        advance_year(world)
    kn.tell(world, me.id, b.id, node.id)
    for _ in range(5):
        advance_year(world)

    (heard,) = view.recollections(world, b.id)
    assert heard.learned_year == 7
    assert heard.teller_age == 7 - me.lifecycle.birth_year  # then, not now
    assert heard.teller_age != pop.age_of(world, me)


# --- asking -------------------------------------------------------------------


def test_ask_lists_who_is_here_as_status_numbers_them():
    world, _ = _world()
    listing = rs.handle(world, "ask")
    people = view.nearby(world)

    assert listing.splitlines()[0] == "People you could ask:"
    assert listing.splitlines()[1:] == [
        f"  [{i}] {p.name}, {p.age}" for i, p in enumerate(people, 1)
    ]
    status = rs.render_status(world)
    assert all(line in status for line in listing.splitlines()[1:])


def test_asking_hears_only_what_that_person_knows():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    people = view.nearby(world)
    b, c = (pop.person_by_id(world, p.person_id) for p in people[:2])
    told = _event(world, me, "Sellin rises to power")
    mine = _event(world, me, "Kalin rises to power")
    _event(world, me, "Ashmar rises to power")  # happened; nobody knows it
    for node in (told, mine):
        kn.learn(world, me.id, node.id)
    kn.tell(world, me.id, b.id, told.id)

    heard_b = rs.handle(world, "ask 1")
    heard_c = rs.handle(world, "ask 2")

    assert "Sellin rises to power" in heard_b
    assert "Kalin" not in heard_b and "Ashmar" not in heard_b
    assert heard_c == f"{c.name} knows of nothing that has happened.\n"


def test_somebody_who_saw_it_says_so_and_names_nobody():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    b = pop.person_by_id(world, view.nearby(world)[0].person_id)
    node = _event(world, b, "Dunric rises to power")
    kn.learn(world, b.id, node.id)

    assert rs.handle(world, "ask 1") == (
        f"{b.name} remembers:\n"
        f"  Year {node.year}. Dunric rises to power.\n"
        "    Saw it happen.\n"
    )
    assert me.name not in rs.handle(world, "ask 1").split("\n", 1)[1]


def test_asking_takes_no_time_and_changes_nothing():
    world, _ = _run(4, TELL_THEN_DIE + ["move", f"move {HOLLOWFEN}"])
    dunric = pop.current_person_id(world)
    before = world.model_dump()

    for line in ("ask", f"ask {VEGAR}", "ask 1", "ask 16"):
        rs.handle(world, line)

    assert world.model_dump() == before
    assert kn.knowledge_of(world, dunric) == []  # the asker learns nothing


def test_asking_nobody_is_refused_at_no_cost():
    world, _ = _world()
    before = world.model_dump()
    for line in ("ask 0", "ask 999", "ask vegar", "ask -1"):
        with pytest.raises(RoutineRefused):
            rs.handle(world, line)
    assert world.model_dump() == before


def test_only_the_living_here_can_be_asked():
    world, _ = _run(4, TELL_THEN_DIE + ["move", f"move {HOLLOWFEN}"])
    here = {p.person_id for p in view.nearby(world)}
    me = view.current_person(world)
    assert all(
        pop.person_by_id(world, p).alive
        and pop.person_by_id(world, p).lifecycle.location_id == me.lifecycle.location_id
        for p in here
    )
    vewen = world.lives[0].person_id
    assert vewen not in here  # the dead keep their knowledge, but are not asked
    assert kn.knowledge_of(world, vewen) != []


# --- names ----------------------------------------------------------------------


def _greywind_in_year_4():
    """Seed 4, Greywind Moor in year 4 holds two Lynveths, 52 and 16."""
    world, _ = _world()
    rs.handle(world, "work at")
    rs.handle(world, "continue 3")
    rs.handle(world, f"move {GREYWIND}")
    here = view.nearby(world)
    lynveths = [i for i, p in enumerate(here, 1) if p.name == "Lynveth"]
    return world, here, lynveths


def test_two_people_with_one_name_are_asked_apart():
    world, here, (first, second) = _greywind_in_year_4()
    me = view.current_person(world)
    node = _event(world, me, "Sellin rises to power")
    kn.learn(world, me.id, node.id)
    kn.tell(world, me.id, here[first - 1].person_id, node.id)

    assert "Sellin rises to power" in rs.handle(world, f"ask {first}")
    assert rs.handle(world, f"ask {second}") == (
        "Lynveth knows of nothing that has happened.\n"
    )


def test_a_teller_is_never_confused_with_a_namesake():
    """The elder Lynveth tells; the hearer reports the elder's age then, and
    the younger Lynveth standing in the same place lends nothing."""
    world, here, (first, second) = _greywind_in_year_4()
    elder, younger = (
        pop.person_by_id(world, here[i - 1].person_id) for i in (first, second)
    )
    hearer = next(
        pop.person_by_id(world, p.person_id) for p in here if p.name != "Lynveth"
    )
    node = _event(world, elder, "Sellin rises to power")
    kn.learn(world, elder.id, node.id)
    kn.tell(world, elder.id, hearer.id, node.id)

    (heard,) = view.recollections(world, hearer.id)
    assert _told(world).learned_from_person_id == elder.id
    assert heard.teller_age == pop.age_of(world, elder) == 52
    assert heard.teller_age != pop.age_of(world, younger)
    assert heard.told_in == "Greywind Moor"


# --- the next life ------------------------------------------------------------


def test_a_successor_hears_of_their_predecessor_without_being_told_who():
    world, text = _run(4, TELL_THEN_DIE + GO_AND_ASK)
    vewen = pop.person_by_id(world, world.lives[0].person_id)
    dunric = world.lives[1].person_id
    told = _told(world)
    answer = text[text.index("Vegar remembers:") :].split("\n\n>")[0] + "\n"

    # every piece of evidence is life A's own, at the telling
    assert told.learned_from_person_id == vewen.id and not vewen.alive
    assert told.learned_year == 20
    assert told.told_at_location_id == _place(world, "Hollowfen").id
    assert answer == (
        "Vegar remembers:\n"
        "  Year 14. Sellin rises to power.\n"
        f"    Heard of it in year 20 from {vewen.name}, then "
        f"{20 - vewen.lifecycle.birth_year}, in Hollowfen.\n"
    )
    assert vewen.name == "Vewen" and 20 - vewen.lifecycle.birth_year == 36
    # the namesake now living in Hollowfen could not have been 36 in year 20
    namesake = next(
        p for p in view.nearby(world) if p.name == "Vewen" and p.person_id != vewen.id
    )
    assert pop.person_by_id(world, namesake.person_id).lifecycle.birth_year > -16
    # and nothing says who Vewen was, or why Sellin rose
    lowered = answer.lower()
    assert not any(w in lowered for w in ATTRIBUTION + ENGINE_WORDS + ENUM_WORDS)
    assert kn.knowledge_of(world, dunric) == []


# --- replay -------------------------------------------------------------------


def test_a_recipe_replays_the_asking_exactly():
    from chronicle_forge.persistence import build_recipe, replay_transcript

    commands = TELL_THEN_DIE + GO_AND_ASK + ["ask 16", "work at", "continue 2"]
    lived, lived_text = _run(4, commands, life_cap=60)
    recipe = build_recipe(
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=commands,
        loop="routine",
    )
    replayed, replayed_text = replay_transcript(recipe)

    assert replayed_text == lived_text
    assert replayed.model_dump() == lived.model_dump()
    assert _told(replayed).told_at_location_id == _place(replayed, "Hollowfen").id


def test_a_recipe_from_before_asking_is_refused_not_reread():
    from chronicle_forge.persistence import (
        ENGINE_VERSION,
        EngineVersionMismatch,
        Recipe,
        replay_transcript,
    )

    old = Recipe(
        engine_version="0.7.0-movement",
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=TELL_THEN_DIE + GO_AND_ASK,
        loop="routine",
    )
    assert ENGINE_VERSION == "0.8.0-knowledge-discovery"
    with pytest.raises(EngineVersionMismatch):
        replay_transcript(old)


def test_the_help_page_names_asking():
    assert "  ask                     " in rs.HELP
    assert "  ask <n>                 " in rs.HELP
