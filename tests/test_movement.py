"""Moving: the player may leave where they live for another place a person may
live.

What this pins. ``move`` lists the places a person may live — never the
dungeon, and never who lives there — and ``move <n>`` relocates the current
person there. Going ends the way they lived (``RELOCATED``, kept in the place
it was lived), costs exactly one ``advance_year``, and that year is seen from
where they arrive. Everything else follows from the new place being true:
who is here, who can be lived beside, who can be told, what can be seen.
Nobody else moves, and moving teaches nothing by itself.

The point of it is the next life: a successor who starts elsewhere can now go
to where somebody their predecessor told still lives, and find that same
person there — without thereby knowing what they were told.
"""

from __future__ import annotations

import io

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge import knowledge as kn
from chronicle_forge import relationship as rel
from chronicle_forge import spatial
from chronicle_forge.enums import KnowledgeSource, LocationType, RoutineEndReason
from chronicle_forge.life import begin_life
from chronicle_forge.play import routine_session as rs
from chronicle_forge.play import view
from chronicle_forge.routine import RoutineRefused
from chronicle_forge.spatial import RelocationRefused
from chronicle_forge.worldgen import generate_world

HOLLOWFEN, GREYWIND, THORNREACH = 1, 2, 3  # ``move`` numbers, in world order

# Seed 4, as measured (see test_knowledge_transmission): Vewen tells Vegar of
# Sellin's rise in year 20 and dies in year 64; Vegar, younger, lives on in
# Hollowfen. The successor, Dunric, begins in Greywind Moor in year 74.
TELL_THEN_DIE = [
    "work at",
    "continue 10",
    "continue 10",
    "associate with 9",
    "tell",
    "tell 1",
    "tell",
] + ["continue 10"] * 5


def _world(seed=4, max_year=config.WORLD_MAX_YEARS):
    world = generate_world(seed, max_year=max_year)
    return world, begin_life(world)


def _me(world):
    return view.current_person(world)


def _place(world, name):
    return next(loc for loc in world.locations if loc.name == name)


def _run(seed, commands, life_cap=2):
    it = iter(commands)
    out = io.StringIO()
    world = rs.run_routine_world(
        seed, reader=lambda: next(it, None), writer=out.write, life_cap=life_cap
    )
    return world, out.getvalue()


def _to_year(world, year):
    while world.current_year < year:
        rs.handle(world, "continue 1")


# --- where a person may live ------------------------------------------------


def test_a_person_may_live_anywhere_but_the_dungeon():
    world, _ = _world()
    homes = spatial.residential_locations(world)
    assert [loc.name for loc in homes] == ["Hollowfen", "Greywind Moor", "Thornreach"]
    assert all(loc.type is not LocationType.DUNGEON for loc in homes)
    assert any(loc.type is LocationType.DUNGEON for loc in world.locations)


def test_worldgen_houses_people_only_where_a_person_may_live():
    """One rule for both: nobody is born, or moves, where nobody may live."""
    world, _ = _world()
    homes = {loc.id for loc in spatial.residential_locations(world)}
    assert {p.lifecycle.location_id for p in world.npcs} == homes


def test_the_places_are_numbered_the_same_wherever_you_stand():
    world, _ = _world()
    listing = rs.handle(world, "move")
    assert listing == (
        "Places you could live:\n"
        "  [1] Hollowfen (you live here)\n"
        "  [2] Greywind Moor\n"
        "  [3] Thornreach\n"
    )
    rs.handle(world, f"move {GREYWIND}")
    assert [p.name for p in view.places(world)] == [
        "Hollowfen",
        "Greywind Moor",
        "Thornreach",
    ]
    assert [p.here for p in view.places(world)] == [False, True, False]


def test_the_list_says_nothing_of_who_lives_there():
    world, _ = _world()
    listing = rs.handle(world, "move")
    assert all(p.name not in listing for p in world.npcs)
    assert "npc-" not in listing and "loc-" not in listing


# --- the domain act ---------------------------------------------------------


def test_relocating_changes_where_the_person_lives_and_nothing_else():
    world, life = _world()
    me = _me(world)
    before = {p.id: p.lifecycle.location_id for p in world.npcs if p.id != me.id}
    dump = world.model_dump(exclude={"npcs"})

    spatial.relocate(world, me.id, _place(world, "Thornreach").id)

    assert me.lifecycle.location_id == _place(world, "Thornreach").id
    assert {
        p.id: p.lifecycle.location_id for p in world.npcs if p.id != me.id
    } == before
    assert world.model_dump(exclude={"npcs"}) == dump  # no year, no knowledge


@pytest.mark.parametrize(
    "where", ["here", "nowhere", "dungeon"], ids=["same", "missing", "dungeon"]
)
def test_the_world_refuses_a_move_that_would_not_be_true(where):
    world, _ = _world()
    me = _me(world)
    target = {
        "here": me.lifecycle.location_id,
        "nowhere": "loc-9999",
        "dungeon": next(
            l.id for l in world.locations if l.type is LocationType.DUNGEON
        ),
    }[where]
    before = world.model_dump()
    with pytest.raises(RelocationRefused):
        spatial.relocate(world, me.id, target)
    assert world.model_dump() == before


def test_the_dead_and_the_unknown_do_not_move():
    world, _ = _world()
    rs.handle(world, "work at")
    while all(p.alive for p in world.npcs):
        rs.handle(world, "continue 1")
    dead = next(p for p in world.npcs if not p.alive)
    with pytest.raises(RelocationRefused):
        spatial.relocate(world, dead.id, _place(world, "Thornreach").id)
    with pytest.raises(RelocationRefused):
        spatial.relocate(world, "npc-9999", _place(world, "Thornreach").id)


# --- the command --------------------------------------------------------------


def test_moving_takes_exactly_one_year():
    world, life = _world()
    me = _me(world)
    text = rs.handle(world, f"move {THORNREACH}")
    assert world.current_year == 1
    assert pop.age_of(world, me) == config.ADULT_AGE + 1
    assert text.startswith(
        "You leave Hollowfen and settle in Thornreach.\n1 year passes.\n"
    )
    assert view.self_view(world).location_name == "Thornreach"


@pytest.mark.parametrize("line", ["move 1", "move 0", "move 4", "move north"])
def test_a_move_that_cannot_happen_costs_nothing(line):
    world, _ = _world()
    rs.handle(world, "work at")
    before = world.model_dump()
    with pytest.raises(RoutineRefused):
        rs.handle(world, line)
    assert world.model_dump() == before


def test_one_year_reads_as_one_year():
    world, _ = _world()
    rs.handle(world, "work at")
    assert rs.handle(world, "continue 1").startswith("1 year passes.")
    assert rs.handle(world, "continue 2").startswith("2 years pass.")


# --- the way you lived there ----------------------------------------------------


def test_leaving_ends_the_way_you_lived_and_keeps_where_you_lived_it():
    world, life = _world()
    me = _me(world)
    rs.handle(world, "work with 1")
    target = rt.active_routine(world).target_person_id
    rs.handle(world, "continue 9")
    shared = rel.relationship_between(world, me.id, target).shared_years

    text = rs.handle(world, f"move {GREYWIND}")

    routine = rt.routines_of(world, me.id)[-1]
    assert routine.end_reason is RoutineEndReason.RELOCATED
    assert (routine.start_year, routine.end_year) == (0, 9)
    assert routine.location_id == _place(world, "Hollowfen").id
    assert rt.active_routine(world) is None
    assert "You left that life behind with the place." in text
    # the years beside them stay; the year spent leaving was not one of them
    assert rel.relationship_between(world, me.id, target).shared_years == shared == 9


def test_after_arriving_you_choose_how_to_live_again():
    world, _ = _world()
    rs.handle(world, "work at")
    rs.handle(world, f"move {GREYWIND}")
    assert "You have not settled into anything yet." in rs.render_status(world)
    rs.handle(world, "work at")
    assert rt.active_routine(world).location_id == _place(world, "Greywind Moor").id


def test_somebody_dying_in_the_year_you_left_does_not_rewrite_why_it_ended():
    world, _ = _world()
    rs.handle(world, "work at")
    oldest = max(view.nearby(world), key=lambda p: p.age)
    _to_year(world, config.LIFESPAN_CAP - 1 - oldest.age)
    index = [p.person_id for p in view.nearby(world)].index(oldest.person_id) + 1
    rs.handle(world, f"work with {index}")
    routine = rt.active_routine(world)

    rs.handle(world, f"move {GREYWIND}")

    assert not pop.person_by_id(world, oldest.person_id).alive
    assert routine.end_reason is RoutineEndReason.RELOCATED
    assert routine.end_year == world.current_year - 1


# --- death and the horizon ------------------------------------------------------


def test_a_person_can_die_in_the_year_they_move():
    world, life = _world()
    rs.handle(world, "work at")
    _to_year(world, config.LIFESPAN_CAP - config.ADULT_AGE - 1)

    text = rs.handle(world, f"move {THORNREACH}")

    assert not life.alive
    assert life.death_year == world.current_year
    assert text.rstrip().endswith("You died.")
    assert rt.routines_of(world, life.person_id)[-1].end_reason is (
        RoutineEndReason.RELOCATED
    )


def test_the_horizon_can_fall_in_the_year_you_move():
    world, life = _world(max_year=5)
    rs.handle(world, "work at")
    rs.handle(world, "continue 4")

    text = rs.handle(world, f"move {THORNREACH}")

    assert world.current_year == world.max_year
    assert life.alive  # nobody dies of the horizon
    assert text.rstrip().endswith("The chronicle reaches its end here.")
    assert rt.routines_of(world, life.person_id)[-1].end_reason is (
        RoutineEndReason.RELOCATED
    )
    with pytest.raises(RoutineRefused):
        rs.handle(world, f"move {GREYWIND}")


# --- who is here, and what can be seen -----------------------------------------


def test_who_is_here_is_who_lives_where_you_now_live():
    world, _ = _world()
    before = {p.person_id for p in view.nearby(world)}
    rs.handle(world, f"move {GREYWIND}")
    after = {p.person_id for p in view.nearby(world)}
    me = _me(world)

    assert before and after and before.isdisjoint(after)
    for pid in after:
        assert pop.person_by_id(world, pid).lifecycle.location_id == (
            me.lifecycle.location_id
        )
    # and they are the only people a routine, and so a telling, can be with
    rs.handle(world, "work with 1")
    assert rt.active_routine(world).target_person_id == view.nearby(world)[0].person_id


def test_you_cannot_take_up_with_somebody_you_left_behind():
    world, _ = _world()
    left = view.nearby(world)[0].person_id
    rs.handle(world, f"move {GREYWIND}")
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, rt.RoutineKind.WORK_WITH, left)


def test_the_year_of_the_move_is_seen_from_where_you_arrive():
    """Seed 17, year 54: one person rises in Hollowfen and one in Greywind Moor.
    Leaving Hollowfen in year 53, the player sees only the second."""
    world, life = _world(seed=17)
    rs.handle(world, "work at")
    _to_year(world, 53)
    known_before = list(world.knowledge)

    text = rs.handle(world, f"move {GREYWIND}")

    year54 = [n for n in world.causal_nodes if n.year == 54]
    places = {n.id: view._event_place(world, n) for n in year54}
    here, there = _place(world, "Greywind Moor").id, _place(world, "Hollowfen").id
    assert sorted(places.values()) == sorted([here, there])
    learned = world.knowledge[len(known_before) :]
    assert [k.event_id for k in learned] == [i for i, p in places.items() if p == here]
    assert all(k.source is KnowledgeSource.OBSERVED for k in learned)
    assert not any(
        kn.knows(world, life.person_id, i) for i, p in places.items() if p == there
    )
    assert (
        f"  Year 54. {next(n for n in year54 if places[n.id] == here).title}." in text
    )


def test_what_happens_where_you_used_to_live_is_no_longer_seen():
    world, life = _world()
    rs.handle(world, f"move {THORNREACH}")
    rs.handle(world, "work at")
    for _ in range(6):
        rs.handle(world, "continue 10")
    thornreach = _place(world, "Thornreach").id
    nodes = {n.id: n for n in world.causal_nodes}
    mine = kn.knowledge_of(world, life.person_id)
    assert mine
    assert all(view._event_place(world, nodes[k.event_id]) == thornreach for k in mine)


def test_moving_teaches_nothing_by_itself():
    world, life = _world()
    seen_from = len(world.causal_nodes)
    rs.handle(world, f"move {THORNREACH}")
    expected = view.observed_events(
        world, life.person_id, world.causal_nodes[seen_from:]
    )
    assert [k.event_id for k in world.knowledge] == [e.event_id for e in expected]
    assert world.memories == [] and all(not p.relations for p in world.npcs)


def test_two_people_with_one_name_are_still_two_people():
    """Seed 4, Greywind Moor in year 4 holds two Lynveths."""
    world, _ = _world()
    rs.handle(world, "work at")
    rs.handle(world, "continue 3")
    rs.handle(world, f"move {GREYWIND}")

    here = view.nearby(world)
    lynveths = [p for p in here if p.name == "Lynveth"]
    assert len(lynveths) == 2 and lynveths[0].person_id != lynveths[1].person_id
    status = rs.render_status(world)
    assert status.count("Lynveth") == 2
    assert "npc-" not in status


# --- the next life ------------------------------------------------------------


def test_a_successor_can_go_to_where_the_one_who_was_told_still_lives():
    world, text = _run(4, TELL_THEN_DIE + ["move", f"move {HOLLOWFEN}", "status"])
    vewen, dunric = world.lives[0].person_id, world.lives[1].person_id
    told = next(k for k in world.knowledge if k.source is KnowledgeSource.TOLD)
    vegar = pop.person_by_id(world, told.person_id)

    # the successor began somewhere else
    assert "Year 74. You are Dunric, 16, in Greywind Moor." in text
    assert vegar.lifecycle.location_id == _place(world, "Hollowfen").id
    # and went to where Vegar lives, and found the same person there
    assert view.self_view(world).location_name == "Hollowfen"
    assert vegar.alive
    assert vegar.id in [p.person_id for p in view.nearby(world)]
    assert f"{vegar.name}, {pop.age_of(world, vegar)}" in text.split("Year 75.")[-1]
    # what Vegar was told is still Vegar's, from the dead Vewen — and only Vegar's
    assert (told.learned_from_person_id, told.learned_year) == (vewen, 20)
    assert not pop.person_by_id(world, vewen).alive
    assert kn.knowledge_of(world, dunric) == []
    assert not kn.knows(world, dunric, told.event_id)


# --- replay -----------------------------------------------------------------


def test_a_recipe_replays_the_move_exactly():
    from chronicle_forge.persistence import build_recipe, replay_transcript

    commands = TELL_THEN_DIE + ["move", f"move {HOLLOWFEN}", "work at", "continue 5"]
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
    dunric = pop.person_by_id(replayed, replayed.lives[1].person_id)
    assert dunric.lifecycle.location_id == _place(replayed, "Hollowfen").id
    assert rt.routines_of(replayed, dunric.id)[0].location_id == (
        _place(replayed, "Hollowfen").id
    )


def test_a_recipe_from_before_moving_is_refused_not_reread():
    from chronicle_forge.persistence import EngineVersionMismatch, Recipe, replay

    old = Recipe(
        engine_version="0.6.0-knowledge-transmission",
        seed=4,
        max_year=config.WORLD_MAX_YEARS,
        mode="human",
        inputs=["move", "move 2"],
        loop="routine",
    )
    with pytest.raises(EngineVersionMismatch):
        replay(old, writer=lambda _: None)


def test_the_help_page_names_moving():
    assert "  move                    " in rs.HELP
    assert "  move <n>                " in rs.HELP
