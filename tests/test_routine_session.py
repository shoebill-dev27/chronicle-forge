"""The played life: the first loop in which the new core is something a person
can actually do.

What this pins: the player starts as a real sixteen-year-old the world already
holds; they can see where they are and who is there; choosing a way of living
costs no time and living it costs exactly the years they ask for; the world
interrupts them truthfully; and when they die the next life is somebody else
who inherits none of it.

It also pins the separation: this loop never touches the old juncture funnel,
and the old funnel still runs the auto-player.
"""

from __future__ import annotations

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge.enums import RoutineEndReason, RoutineKind
from chronicle_forge.life import begin_life
from chronicle_forge.play import routine_session as rs
from chronicle_forge.play import view
from chronicle_forge.play.human import null_writer, scripted_reader
from chronicle_forge.routine import RoutineRefused
from chronicle_forge.worldgen import generate_world


def _started(seed=4, max_year=200):
    """A world with a life under way, ready for commands."""
    world = generate_world(seed, max_year=max_year)
    life = begin_life(world)
    return world, life


def _run(seed, commands, max_year=200):
    """Drive a whole session from a fixed script."""
    out: list[str] = []
    world = rs.run_routine_world(
        seed,
        reader=scripted_reader(commands),
        writer=out.append,
        max_year=max_year,
    )
    return world, "".join(out)


# --- who am I, and who is here ------------------------------------------------


def test_the_player_begins_as_a_real_sixteen_year_old():
    world, life = _started()
    me = view.self_view(world)
    person = pop.person_by_id(world, life.person_id)
    assert me.person_id == person.id
    assert me.name == person.name
    assert me.age == config.ADULT_AGE
    assert me.year == 0
    assert me.routine is None


def test_the_player_is_told_where_they_are():
    world, _life = _started()
    me = view.self_view(world)
    known = {loc.name for loc in world.locations}
    assert me.location_name in known
    assert rs.render_status(world).count(me.location_name) >= 1


def test_the_people_here_are_the_grown_ones_in_the_same_place():
    world, life = _started()
    me = pop.person_by_id(world, life.person_id)
    here = view.nearby(world)
    assert here
    for p in here:
        person = pop.person_by_id(world, p.person_id)
        assert person.id != me.id
        assert person.alive
        assert person.lifecycle.location_id == me.lifecycle.location_id
        assert pop.age_of(world, person) >= config.ADULT_AGE
    assert [p.person_id for p in here] == sorted(p.person_id for p in here)


def test_the_status_screen_names_people_rather_than_ids():
    world, _life = _started()
    text = rs.render_status(world)
    for p in view.nearby(world):
        assert p.name in text
    assert "npc-" not in text


# --- choosing a way of living -------------------------------------------------


def test_beginning_a_way_of_living_costs_no_time():
    world, _life = _started()
    rs.handle(world, "work at")
    assert world.current_year == 0
    assert rt.active_routine(world).kind is RoutineKind.WORK_AT


@pytest.mark.parametrize(
    "command,kind",
    [
        ("work at", RoutineKind.WORK_AT),
        ("work with 1", RoutineKind.WORK_WITH),
        ("associate with 1", RoutineKind.ASSOCIATE_WITH),
    ],
)
def test_each_way_of_living_can_be_begun(command, kind):
    world, _life = _started()
    rs.handle(world, command)
    routine = rt.active_routine(world)
    assert routine.kind is kind
    if kind is not RoutineKind.WORK_AT:
        assert routine.target_person_id == view.nearby(world)[0].person_id


def test_status_and_history_move_no_time():
    world, _life = _started()
    rs.handle(world, "work at")
    rs.handle(world, "continue 3")
    year = world.current_year
    rs.handle(world, "status")
    rs.handle(world, "history")
    rs.handle(world, "help")
    assert world.current_year == year


# --- living it ----------------------------------------------------------------


def test_seven_years_of_one_life_is_one_seven_year_span():
    world, _life = _started()
    rs.handle(world, "work at")
    rs.handle(world, "continue 7")
    spans = view.history(world, view.current_person(world).id)
    assert len(spans) == 1
    assert spans[0].years == 7
    assert world.current_year == 7


def test_the_years_can_be_taken_a_few_at_a_time():
    world, _life = _started()
    rs.handle(world, "work at")
    rs.handle(world, "continue 4")
    rs.handle(world, "continue 6")
    spans = view.history(world, view.current_person(world).id)
    assert len(spans) == 1 and spans[0].years == 10


def test_changing_how_you_live_closes_the_old_span_in_the_same_year():
    world, _life = _started()
    rs.handle(world, "work at")
    rs.handle(world, "continue 5")
    rs.handle(world, "work with 1")
    assert world.current_year == 5
    spans = view.history(world, view.current_person(world).id)
    assert [s.years for s in spans] == [5, 0]
    assert spans[0].end_reason is RoutineEndReason.PLAYER_CHANGED
    assert sum(1 for s in spans if s.active) == 1


def test_the_player_is_told_when_the_other_person_dies():
    world, life = _started()
    me = pop.person_by_id(world, life.person_id)
    target = pop.person_by_id(world, view.nearby(world)[0].person_id)
    target.lifecycle.birth_year = world.current_year - (config.LIFESPAN_CAP - 3)

    rs.handle(world, "work with 1")
    text = rs.handle(world, "continue 10")

    assert "3 years pass" in text
    assert "They died" in text
    assert "3 years in all" in text
    assert world.current_year == 3
    assert rt.active_routine(world, me.id) is None


# --- what the player may not do ------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "work with 99",  # nobody is listed there
        "work with x",  # not a number
        "continue 0",
        "continue -3",
        "continue 11",  # over the session bound
        "continue years",
        "wander off",  # not a command at all
    ],
)
def test_impossible_commands_are_refused_and_cost_nothing(command):
    world, _life = _started()
    rs.handle(world, "work at")
    rs.handle(world, "continue 2")
    year, spans = world.current_year, len(world.routines)
    with pytest.raises(RoutineRefused):
        rs.handle(world, command)
    assert world.current_year == year and len(world.routines) == spans


def test_continuing_with_no_way_of_living_is_refused():
    world, _life = _started()
    with pytest.raises(RoutineRefused):
        rs.handle(world, "continue 3")
    assert world.current_year == 0


def test_a_child_or_an_absent_person_is_not_on_the_list():
    world, life = _started()
    me = pop.person_by_id(world, life.person_id)
    listed = {p.person_id for p in view.nearby(world)}
    for person in pop.living(world):
        if person.id in listed or person.id == me.id:
            continue
        assert (
            pop.age_of(world, person) < config.ADULT_AGE
            or person.lifecycle.location_id != me.lifecycle.location_id
        )


# --- a whole run ----------------------------------------------------------------


def test_the_player_leaving_does_not_advance_the_world():
    world, _text = _run(4, ["work at", "continue 6"])
    assert world.current_year == 6  # not a year more than was asked for
    assert len(world.lives) == 1


def test_a_life_with_no_command_moves_no_year():
    world, _text = _run(4, [])
    assert world.current_year == 0


def test_death_hands_the_player_to_a_different_person_who_inherits_nothing():
    # Live out a whole life: the cap is 80, so 64 years from sixteen.
    commands = ["work at"] + ["continue 10"] * 7
    world, text = _run(4, commands + ["status"])

    first, second = world.lives[0], world.lives[1]
    assert not first.alive and first.age_at_death == config.LIFESPAN_CAP
    assert second.person_id != first.person_id
    assert second.playable_start_year == first.death_year + 10
    assert "died in year" in text and "10 years pass in the world" in text

    assert rt.active_routine(world, second.person_id) is None
    assert rt.routines_of(world, second.person_id) == []
    # The predecessor's years are still the world's.
    assert rt.routines_of(world, first.person_id)
    assert rt.routines_of(world, first.person_id)[0].end_reason is (
        RoutineEndReason.ACTOR_DIED
    )


def test_the_horizon_ends_the_run_without_killing_the_living():
    world, text = _run(4, ["work at"] + ["continue 10"] * 3, max_year=20)
    life = world.lives[-1]
    assert world.current_year == 20
    assert life.alive
    assert pop.person_by_id(world, life.person_id).alive
    routine = rt.routines_of(world, life.person_id)[0]
    assert routine.end_reason is RoutineEndReason.WORLD_ENDED
    assert "reaches its end" in text


def test_the_history_screen_reports_years_and_never_a_feeling():
    world, _life = _started()
    rs.handle(world, "work with 1")
    rs.handle(world, "continue 9")
    text = rs.handle(world, "history")
    assert "9 years" in text
    assert view.nearby(world)[0].name in text
    for word in ("friend", "trust", "affection", "bond", "close", "loyal"):
        assert word not in text.lower()


def test_the_same_commands_write_the_same_world():
    commands = ["work at", "continue 5", "work with 1", "continue 4", "history"]
    a, ta = _run(4, commands)
    b, tb = _run(4, commands)
    assert a.model_dump_json() == b.model_dump_json()
    assert ta == tb


# --- the old loop is not in here -------------------------------------------------


def test_the_played_life_never_reaches_the_old_funnel(monkeypatch):
    """No opportunity is scored, no option is expanded, no gate is asked and no
    activity is performed. The old loop is still there; this one does not use
    it."""
    import chronicle_forge.activity as activity
    import chronicle_forge.execution as execution
    import chronicle_forge.opportunity as opportunity

    def forbidden(*_a, **_k):  # pragma: no cover - the test fails if it runs
        raise AssertionError("the played life reached the old juncture funnel")

    for module, name in [
        (opportunity, "select_opportunities"),
        (execution, "expand_options"),
        (execution, "execute_option"),
        (activity, "perform_activity"),
    ]:
        monkeypatch.setattr(module, name, forbidden)

    world, _text = _run(4, ["work at", "continue 10", "work with 1", "continue 10"])
    assert world.current_year == 20
    assert not world.lives[0].activity_log  # nothing went through the old funnel


def test_the_auto_player_still_runs_the_old_loop():
    from chronicle_forge.autoplay import simulate_world

    world = simulate_world(4, mode="opportunity", max_year=40)
    assert world.lives[0].activity_log  # the legacy funnel is untouched
    assert not world.routines  # and it starts no routines


def test_a_played_run_emits_no_option_or_juncture_record():
    world, text = _run(4, ["work at", "continue 8"])
    assert not world.lives[0].activity_log
    assert "[1]" in text  # the only numbers are the people standing here
    assert "Let this season pass" not in text


# --- the recipe knows which loop wrote it ------------------------------------------


def test_a_person_at_a_keyboard_gets_the_played_life(monkeypatch):
    """``chronicle-forge play --seed N`` with nobody passing ``--auto`` is the
    new loop, and the recipe it saves says so."""
    from chronicle_forge.play.adapter import play_and_record

    lines = iter(["work at", "continue 5"])

    def fake_input(*_a):
        try:
            return next(lines)
        except StopIteration:  # a real terminal raises this when it closes
            raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)

    world, recipe = play_and_record(
        seed=4, mode="human", writer=null_writer, life_cap=60
    )
    assert recipe.loop == "routine"
    assert recipe.inputs == ["work at", "continue 5"]
    assert world.routines and world.current_year == 5
    assert not world.lives[0].activity_log


def test_an_unattended_run_stays_on_the_old_loop():
    from chronicle_forge.play.adapter import play_and_record

    world, recipe = play_and_record(
        seed=4, auto=True, mode="auto", writer=null_writer, life_cap=60
    )
    assert recipe.loop == "juncture"
    assert world.lives[0].activity_log and not world.routines


def test_a_played_recipe_replays_to_the_same_world(monkeypatch):
    from chronicle_forge.persistence import build_recipe, replay_transcript

    commands = ["work at", "continue 6", "associate with 1", "continue 3"]
    original, transcript = _run(4, commands)
    recipe = build_recipe(
        seed=4,
        max_year=original.max_year,
        mode="human",
        inputs=commands,
        loop="routine",
    )
    replayed, replayed_transcript = replay_transcript(recipe)
    assert replayed.model_dump_json() == original.model_dump_json()
    assert replayed_transcript == transcript


def test_a_recipe_written_before_the_routine_loop_still_means_the_old_one():
    from chronicle_forge.persistence import Recipe

    r = Recipe(engine_version="x", seed=1, max_year=40, mode="human", inputs=["1"])
    assert r.loop == "juncture"
