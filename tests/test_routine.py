"""Routines: a life is made of spans of years, not of single decisions.

What this pins: every tracked person is somewhere the world knows; a way of
living is one record covering many years; its length is read off the
chronology rather than counted; and it ends, for a named reason, the moment
the world stops supporting it — never later.
"""

from __future__ import annotations

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.enums import DeathCause, RoutineEndReason, RoutineKind
from chronicle_forge.life import TURNS_PER_YEAR, advance_time, begin_life, end_life
from chronicle_forge.macro import advance_to_next_life, advance_year
from chronicle_forge.routine import RoutineRefused
from chronicle_forge.worldgen import generate_world

SEEDS = (1, 7, 42, 99, 123)


@pytest.fixture(scope="module")
def worlds():
    return {seed: simulate_world(seed, mode="opportunity") for seed in SEEDS}


def _neighbour(world, actor, *, adult=True):
    """Somebody else who is in the same place as ``actor``."""
    for person in pop.living(world):
        if person.id == actor.id:
            continue
        if person.lifecycle.location_id != actor.lifecycle.location_id:
            continue
        if adult and pop.age_of(world, person) < config.ADULT_AGE:
            continue
        if not adult and pop.age_of(world, person) >= config.ADULT_AGE:
            continue
        return person
    return None


def _doomed_neighbour(world, actor, years):
    """A neighbour whose chronology puts them at the lifespan cap in ``years``."""
    target = _neighbour(world, actor)
    target.lifecycle.birth_year = world.current_year - (config.LIFESPAN_CAP - years)
    return target


# --- spatial grounding ------------------------------------------------------


def test_every_living_person_is_somewhere_the_world_knows(worlds):
    for seed, world in worlds.items():
        known = {loc.id for loc in world.locations}
        for person in pop.living(world):
            assert person.lifecycle.location_id in known, f"seed {seed}: {person.id}"


def test_the_dead_keep_the_place_they_died_in(worlds):
    for seed, world in worlds.items():
        known = {loc.id for loc in world.locations}
        dead = [p for p in world.npcs if not p.alive]
        assert dead, f"seed {seed}"
        for person in dead:
            assert person.lifecycle.location_id in known, f"seed {seed}: {person.id}"


def test_a_newborn_begins_where_their_parent_is():
    world = generate_world(seed=4)
    begin_life(world)
    advance_year(world)
    child = world.npcs[-1]
    parent = pop.person_by_id(world, child.lineage.parent_ids[0])
    assert child.lifecycle.location_id == parent.lifecycle.location_id


def test_every_birth_over_the_horizon_happened_where_its_parent_was(worlds):
    for seed, world in worlds.items():
        for child in world.npcs:
            if not child.lineage.parent_ids:
                continue
            parent = pop.person_by_id(world, child.lineage.parent_ids[0])
            assert child.lifecycle.location_id == parent.lifecycle.location_id, seed


def test_the_successor_keeps_the_place_they_already_lived_in():
    world = generate_world(seed=4)
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    heir = pop.aged(world, config.ADULT_AGE - config.REINCARNATION_GAP_YEARS)
    before = {p.id: p.lifecycle.location_id for p in heir}
    _skip, nxt = advance_to_next_life(world)
    person = pop.person_by_id(world, nxt.person_id)
    # Taking somebody up does not move them: they are where they always were.
    assert person.lifecycle.location_id == before[person.id]


def test_the_same_seed_puts_the_same_people_in_the_same_places():
    a = generate_world(seed=7)
    b = generate_world(seed=7)
    assert [(p.id, p.lifecycle.location_id) for p in a.npcs] == [
        (p.id, p.lifecycle.location_id) for p in b.npcs
    ]


def test_the_world_is_not_settled_in_one_place_only():
    world = generate_world(seed=4)
    places = {p.lifecycle.location_id for p in world.npcs}
    assert len(places) > 1
    dungeon = next(loc for loc in world.locations if loc.type.value == "dungeon")
    assert dungeon.id not in places  # a place to go, not a place to be from


def test_a_person_the_world_has_no_place_for_cannot_begin_a_routine():
    world = generate_world(seed=4)
    life = begin_life(world)
    pop.person_by_id(world, life.person_id).lifecycle.location_id = "loc-nowhere"
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, RoutineKind.WORK_AT)


# --- starting a routine -----------------------------------------------------


def test_choosing_how_to_live_is_not_itself_a_year():
    world = generate_world(seed=4)
    begin_life(world)
    year = world.current_year
    rt.begin_routine(world, RoutineKind.WORK_AT)
    assert world.current_year == year


def test_a_routine_is_recorded_where_its_actor_is():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    assert routine.actor_person_id == actor.id
    assert routine.location_id == actor.lifecycle.location_id
    assert routine.start_year == world.current_year
    assert routine.active and routine.end_year is None and routine.end_reason is None


def test_nobody_lives_two_ways_at_once():
    world = generate_world(seed=4)
    begin_life(world)
    rt.begin_routine(world, RoutineKind.WORK_AT)
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, RoutineKind.WORK_AT)


def test_a_routine_needs_a_life_to_belong_to():
    world = generate_world(seed=4)
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, RoutineKind.WORK_AT)


def test_a_place_routine_refuses_a_person_and_a_person_routine_refuses_nobody():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    other = _neighbour(world, actor)
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, RoutineKind.WORK_AT, target_person_id=other.id)
    with pytest.raises(RoutineRefused):
        rt.begin_routine(world, RoutineKind.WORK_WITH)


@pytest.mark.parametrize("kind", [RoutineKind.WORK_WITH, RoutineKind.ASSOCIATE_WITH])
def test_the_person_you_spend_years_beside_has_to_be_someone_you_could_have(kind):
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    neighbour = _neighbour(world, actor)
    assert neighbour is not None

    with pytest.raises(RoutineRefused):  # yourself
        rt.begin_routine(world, kind, target_person_id=actor.id)
    with pytest.raises(RoutineRefused):  # nobody
        rt.begin_routine(world, kind, target_person_id="npc-9999")

    child = _neighbour(world, actor, adult=False)
    assert child is not None
    with pytest.raises(RoutineRefused):  # a child
        rt.begin_routine(world, kind, target_person_id=child.id)

    elsewhere = next(
        p
        for p in pop.adults(world)
        if p.lifecycle.location_id != actor.lifecycle.location_id
    )
    with pytest.raises(RoutineRefused):  # not here
        rt.begin_routine(world, kind, target_person_id=elsewhere.id)

    neighbour.alive = False
    with pytest.raises(RoutineRefused):  # dead
        rt.begin_routine(world, kind, target_person_id=neighbour.id)


# --- how long it lasted -----------------------------------------------------


def test_a_span_from_twelve_to_nineteen_is_seven_years():
    """The year it began counts; the year it ended does not."""
    world = generate_world(seed=4)
    begin_life(world)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    routine.start_year = 12
    routine.end_year = 19
    assert rt.routine_years(world, routine) == 7


def test_a_routine_still_being_lived_is_measured_against_the_clock():
    world = generate_world(seed=4)
    begin_life(world)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    for expected in range(1, 4):
        advance_year(world)
        assert rt.routine_years(world, routine) == expected


# --- A: eight years of one life, as one record ------------------------------


def test_eight_years_of_working_somewhere_is_one_routine_not_eight_decisions():
    world = generate_world(seed=4)
    life = begin_life(world)
    start = world.current_year
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    result = rt.continue_routine(world, 8)

    assert result["years_run"] == 8
    assert world.current_year == start + 8
    assert len(world.routines) == 1  # one span, not one per year
    assert rt.routine_years(world, routine) == 8
    assert routine.active and routine.end_reason is None
    assert life.age == config.ADULT_AGE + 8


def test_a_routine_can_outlast_ten_years_without_being_chosen_again():
    world = generate_world(seed=4)
    begin_life(world)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 7)
    rt.continue_routine(world, 5)
    assert len(world.routines) == 1
    assert rt.routine_years(world, routine) == 12


# --- B: the person you worked beside dies -----------------------------------


def test_a_shared_routine_stops_the_year_the_other_person_dies():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    target = _doomed_neighbour(world, actor, years=4)
    start = world.current_year

    routine = rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=target.id)
    result = rt.continue_routine(world, 10)  # asked for ten, the world gave four

    assert not target.alive and target.lifecycle.death_year == start + 4
    assert routine.end_year == start + 4
    assert routine.end_reason is RoutineEndReason.TARGET_DIED
    assert rt.routine_years(world, routine) == 4
    assert result["years_run"] == 4
    assert world.current_year == start + 4  # no year was spent on a dead man


# --- the clock keeps the record true, whoever moves it ----------------------


def test_a_shared_routine_closes_when_the_years_pass_without_being_asked():
    """Nobody called ``continue_routine``: the years were advanced directly.
    The routine must still be closed, at the exact year, by the clock."""
    world = generate_world(seed=4, max_year=40)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    target = _doomed_neighbour(world, actor, years=4)
    start = world.current_year

    routine = rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=target.id)
    for _ in range(8):
        advance_year(world)

    assert routine.end_year == start + 4
    assert routine.end_reason is RoutineEndReason.TARGET_DIED
    assert rt.routine_years(world, routine) == 4
    assert world.current_year == start + 8  # the world kept going; the span did not


def test_a_shared_routine_closes_when_the_years_pass_as_turns():
    """The in-life turn path reaches the same clock, so it keeps the same
    promise."""
    world = generate_world(seed=4, max_year=40)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    target = _doomed_neighbour(world, actor, years=3)
    start = world.current_year

    routine = rt.begin_routine(
        world, RoutineKind.ASSOCIATE_WITH, target_person_id=target.id
    )
    advance_time(world, life, turns=TURNS_PER_YEAR * 5)

    assert routine.end_year == start + 3
    assert routine.end_reason is RoutineEndReason.TARGET_DIED


def test_an_actor_who_dies_by_any_path_keeps_no_open_routine():
    """The actor's row says dead; no command was issued. One year of world
    time is enough for the record to agree."""
    world = generate_world(seed=4, max_year=40)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 3)

    actor.alive = False  # however it happened, the world now says so
    died_at = world.current_year + 1
    advance_year(world)

    assert routine.end_year == died_at
    assert routine.end_reason is RoutineEndReason.ACTOR_DIED


def test_no_open_routine_ever_names_somebody_dead():
    world = generate_world(seed=4, max_year=60)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    _doomed_neighbour(world, actor, years=6)
    rt.begin_routine(
        world, RoutineKind.WORK_WITH, target_person_id=_neighbour(world, actor).id
    )
    for _ in range(20):
        if world.current_year >= world.max_year:
            break
        advance_year(world)
        for routine in world.routines:
            if not routine.active:
                continue
            assert pop.person_by_id(world, routine.actor_person_id).alive
            if routine.target_person_id is not None:
                assert pop.person_by_id(world, routine.target_person_id).alive


# --- a death in the last year outranks the end of the world -----------------


def test_a_targets_death_in_the_final_year_outranks_the_horizon():
    world = generate_world(seed=4, max_year=5)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    target = _doomed_neighbour(world, actor, years=5)  # dies in the horizon year

    routine = rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=target.id)
    rt.continue_routine(world, 10)

    assert world.current_year == 5
    assert routine.end_year == 5
    assert routine.end_reason is RoutineEndReason.TARGET_DIED  # not WORLD_ENDED
    assert life.alive


def test_an_actors_death_in_the_final_year_outranks_the_horizon():
    world = generate_world(seed=4, max_year=5)
    life = begin_life(world)
    person = pop.person_by_id(world, life.person_id)
    # Rig the chronology so the lifespan cap falls exactly on the horizon year.
    life.birth_year = world.max_year - config.LIFESPAN_CAP
    person.lifecycle.birth_year = life.birth_year

    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 10)

    assert world.current_year == 5
    assert not life.alive and life.death_cause is DeathCause.LIFESPAN
    assert routine.end_year == 5
    assert routine.end_reason is RoutineEndReason.ACTOR_DIED  # not WORLD_ENDED


# --- C: changing how you live -----------------------------------------------


def test_changing_routine_closes_the_old_one_in_the_same_year():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    first = _neighbour(world, actor)
    second = next(
        p
        for p in pop.adults(world)
        if p.lifecycle.location_id == actor.lifecycle.location_id
        and p.id not in (actor.id, first.id)
    )

    old = rt.begin_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=first.id)
    rt.continue_routine(world, 5)
    changed_at = world.current_year
    new = rt.change_routine(
        world, RoutineKind.ASSOCIATE_WITH, target_person_id=second.id
    )

    assert old.end_year == changed_at
    assert old.end_reason is RoutineEndReason.PLAYER_CHANGED
    assert new.start_year == changed_at
    assert rt.routine_years(world, old) == 5
    assert [r for r in world.routines if r.active] == [new]
    assert world.current_year == changed_at  # changing your life is not a year


def test_the_years_of_a_changed_life_do_not_overlap():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 3)
    rt.change_routine(
        world, RoutineKind.WORK_WITH, target_person_id=_neighbour(world, actor).id
    )
    rt.continue_routine(world, 3)

    spans = rt.routines_of(world, actor.id)
    assert len(spans) == 2
    for earlier, later in zip(spans, spans[1:]):
        assert earlier.end_year == later.start_year
        assert earlier.end_year is not None


# --- D: the actor dies -------------------------------------------------------


def test_a_routine_ends_with_the_person_living_it_and_stays_in_history():
    world = generate_world(seed=4)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 6)
    died_at = world.current_year

    end_life(world, life, DeathCause.COMBAT)

    assert routine.end_year == died_at
    assert routine.end_reason is RoutineEndReason.ACTOR_DIED
    assert rt.routine_years(world, routine) == 6
    assert rt.active_routine(world, actor.id) is None
    assert routine in world.routines  # the dead keep what they did


def test_the_next_life_begins_with_no_routine_of_its_own():
    world = generate_world(seed=4)
    life = begin_life(world)
    rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 6)
    end_life(world, life, DeathCause.COMBAT)

    _skip, nxt = advance_to_next_life(world)
    assert rt.active_routine(world) is None
    assert rt.routines_of(world, nxt.person_id) == []
    assert len(world.routines) == 1  # the predecessor's span is still readable


def test_a_dead_actors_routine_does_not_grow_during_the_gap():
    world = generate_world(seed=4)
    life = begin_life(world)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 6)
    end_life(world, life, DeathCause.COMBAT)
    advance_to_next_life(world)
    assert rt.routine_years(world, routine) == 6


# --- E: the world reaches its horizon ---------------------------------------


def test_the_horizon_closes_a_routine_without_killing_anyone():
    world = generate_world(seed=4, max_year=5)
    life = begin_life(world)
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    result = rt.continue_routine(world, 10)

    assert world.current_year == 5
    assert result["years_run"] == 5
    assert routine.end_year == 5
    assert routine.end_reason is RoutineEndReason.WORLD_ENDED
    assert rt.routine_years(world, routine) == 5
    assert life.alive  # the run ends; the person does not
    assert pop.person_by_id(world, life.person_id).alive


def test_continuing_past_the_horizon_adds_no_years():
    world = generate_world(seed=4, max_year=3)
    begin_life(world)
    rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 10)
    with pytest.raises(RoutineRefused):  # nothing is being lived any more
        rt.continue_routine(world, 1)
    assert world.current_year == 3


# --- determinism -------------------------------------------------------------


def _scripted_history(seed):
    world = generate_world(seed=seed)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 4)
    rt.change_routine(
        world, RoutineKind.WORK_WITH, target_person_id=_neighbour(world, actor).id
    )
    rt.continue_routine(world, 6)
    return [
        (
            r.id,
            r.actor_person_id,
            r.kind,
            r.location_id,
            r.target_person_id,
            r.start_year,
            r.end_year,
            r.end_reason,
        )
        for r in world.routines
    ]


def test_the_same_seed_and_the_same_choices_write_the_same_history():
    assert _scripted_history(4) == _scripted_history(4)


def test_the_spans_are_structural_but_the_people_are_not():
    """Two seeds given the same commands produce the same *shape* of history —
    the same years, the same places by index — because home assignment and the
    birth schedule are structural, not drawn. What differs is who lived it."""
    assert _scripted_history(4) == _scripted_history(11)
    assert _lived_by(4) != _lived_by(11)


def _lived_by(seed):
    world = generate_world(seed=seed)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    neighbour = _neighbour(world, actor)
    return [
        (actor.name, actor.lifecycle.faction_id),
        (neighbour.name, neighbour.lifecycle.faction_id),
    ]
