"""A lived routine is a historical origin — and nothing is invented about what
it did.

What this pins, in two halves. First: a routine that has been lived for a whole
year is one causal origin, keeping its actor, kind, place, person and
chronology, with its duration derived from that chronology and never counted;
two lives lived differently are different here, and the same life typed
differently is not. Second, and just as load-bearing: **no effect is
fabricated from it**. No seed is planted, no event is generated, no heritage is
promoted, no theme moves, and switching routines sixty-four times buys nothing
the world would not otherwise have had.

The observation channel is held to the same line: the player is shown what
happened where they were, and is never told why.
"""

from __future__ import annotations

import io
import re

import pytest

from chronicle_forge import config, population as pop, routine as rt
from chronicle_forge import routine_origin as ro
from chronicle_forge.enums import (
    EventScale,
    RoutineEndReason,
    RoutineKind,
    SeedDomain,
)
from chronicle_forge.life import begin_life, end_life
from chronicle_forge.macro import advance_year
from chronicle_forge.models import CausalNode
from chronicle_forge.play import view
from chronicle_forge.play.routine_session import handle, run_routine_world
from chronicle_forge.worldgen import generate_world


def _world(seed=4):
    world = generate_world(seed)
    return world, begin_life(world)


def _neighbours(world, actor):
    """The grown people where this person is — the only ones a routine may
    ever name."""
    return [
        p
        for p in pop.adults(world)
        if p.id != actor.id and p.lifecycle.location_id == actor.lifecycle.location_id
    ]


def _run(seed, commands, life_cap=1):
    """Play the human loop exactly as a person at a keyboard would."""
    it = iter(commands)
    out = io.StringIO()
    world = run_routine_world(
        seed, reader=lambda: next(it, None), writer=out.write, life_cap=life_cap
    )
    return world, out.getvalue()


# --- an origin has to be lived into existence -------------------------------


def test_choosing_a_way_of_living_is_not_yet_a_cause():
    world, _ = _world()
    rt.begin_routine(world, RoutineKind.WORK_AT)
    assert ro.routine_origins(world) == []


def test_one_completed_year_makes_one_origin():
    world, _ = _world()
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    advance_year(world)

    origins = ro.routine_origins(world)
    assert [o.routine_id for o in origins] == [routine.id]
    assert origins[0].duration_years == 1


def test_twenty_years_is_one_origin_and_not_twenty():
    world, _ = _world()
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(20):
        advance_year(world)

    origins = ro.routine_origins(world)
    assert [o.routine_id for o in origins] == [routine.id]
    assert origins[0].duration_years == 20


def test_duration_is_read_off_the_chronology_and_not_counted():
    """Rewriting the span rewrites the duration, because nothing stores it."""
    world, _ = _world()
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(4):
        advance_year(world)
    assert ro.routine_origins(world)[0].duration_years == 4

    routine.start_year -= 10
    assert ro.routine_origins(world)[0].duration_years == 14


def test_an_open_origin_grows_with_the_clock():
    world, _ = _world()
    rt.begin_routine(world, RoutineKind.WORK_AT)
    seen = []
    for _ in range(12):
        advance_year(world)
        origin = ro.routine_origins(world)[0]
        seen.append(origin.duration_years)
        assert origin.open

    assert seen == list(range(1, 13))


def test_a_closed_origin_stops_because_its_span_did():
    world, _ = _world()
    routine = rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(6):
        advance_year(world)
    rt.end_routine(world, routine, RoutineEndReason.PLAYER_CHANGED)
    closed = ro.routine_origins(world)[0]

    for _ in range(9):
        advance_year(world)

    after = ro.routine_origins(world)[0]
    assert after == closed
    assert after.duration_years == 6
    assert not after.open


def test_a_dead_persons_origins_are_still_there_to_be_asked_about():
    world, life = _world()
    rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(5):
        advance_year(world)
    end_life(world, life, None)
    for _ in range(20):
        advance_year(world)

    origins = ro.routine_origins(world, life.person_id)
    assert len(origins) == 1
    assert origins[0].duration_years == 5
    assert origins[0].end_year is not None


# --- what an origin carries -------------------------------------------------


def test_the_actor_kind_place_person_and_chronology_all_survive():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    other = _neighbours(world, me)[0]
    routine = rt.begin_routine(world, RoutineKind.WORK_WITH, other.id)
    for _ in range(3):
        advance_year(world)

    origin = ro.routine_origins(world)[0]
    assert origin.routine_id == routine.id
    assert origin.actor_person_id == me.id
    assert origin.kind is RoutineKind.WORK_WITH
    assert origin.location_id == me.lifecycle.location_id
    assert origin.target_person_id == other.id
    assert (origin.start_year, origin.end_year) == (routine.start_year, None)
    assert origin.duration_years == 3


@pytest.mark.parametrize(
    "kind", [RoutineKind.WORK_AT, RoutineKind.WORK_WITH, RoutineKind.ASSOCIATE_WITH]
)
def test_each_kind_is_read_back_as_itself(kind):
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    target = None if kind is RoutineKind.WORK_AT else _neighbours(world, me)[0].id
    rt.begin_routine(world, kind, target)
    advance_year(world)

    origin = ro.routine_origins(world)[0]
    assert origin.kind is kind
    assert (origin.target_person_id is None) == (kind is RoutineKind.WORK_AT)


def test_an_origin_carries_no_strength_of_any_kind():
    """Years are kept as years. Nothing here is a weight."""
    fields = set(ro.RoutineOrigin.__dataclass_fields__)
    assert not fields & {
        "magnitude",
        "weight",
        "strength",
        "scale",
        "domain",
        "seed_id",
        "exposure",
    }


def test_changing_how_you_live_leaves_the_old_cause_standing():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    other = _neighbours(world, me)[0]
    rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(3):
        advance_year(world)
    rt.change_routine(world, RoutineKind.ASSOCIATE_WITH, other.id)
    for _ in range(4):
        advance_year(world)

    assert [(o.kind, o.duration_years) for o in ro.routine_origins(world)] == [
        (RoutineKind.WORK_AT, 3),
        (RoutineKind.ASSOCIATE_WITH, 4),
    ]


def test_the_same_life_typed_differently_is_the_same_life():
    """How the player chunks ``continue`` is not something history records."""
    chunked, _ = _run(17, ["work at"] + ["continue 10"] * 7)
    yearly, _ = _run(17, ["work at"] + ["continue 1"] * 64)

    assert ro.routine_origins(chunked) == ro.routine_origins(yearly)


def test_the_same_seed_and_commands_give_the_same_origins():
    a, _ = _run(17, ["work at", "continue 10", "work with 1", "continue 10"])
    b, _ = _run(17, ["work at", "continue 10", "work with 1", "continue 10"])

    assert ro.routine_origins(a) == ro.routine_origins(b)


def test_two_lives_of_the_same_length_are_not_the_same_history():
    steady, _ = _run(17, ["work at"] + ["continue 10"] * 2)
    beside, _ = _run(17, ["work with 1"] + ["continue 10"] * 2)
    company, _ = _run(17, ["associate with 2"] + ["continue 10"] * 2)

    assert steady.current_year == beside.current_year == company.current_year == 20
    shapes = {
        repr(
            [
                (o.kind, o.target_person_id, o.duration_years)
                for o in ro.routine_origins(w)
            ]
        )
        for w in (steady, beside, company)
    }
    assert len(shapes) == 3


# --- nothing is fabricated from it ------------------------------------------


_LIVES = (
    ("one long span", ["work at"] + ["continue 10"] * 7),
    (
        "seven spans",
        [
            "work at",
            "continue 5",
            "work with 1",
            "continue 5",
            "associate with 2",
            "continue 10",
            "work at",
            "continue 10",
            "work with 1",
            "continue 10",
            "associate with 1",
            "continue 10",
            "work at",
            "continue 10",
            "continue 10",
        ],
    ),
    (
        "a change every single year",
        sum(
            (
                [["work at", "work with 1", "associate with 1"][i % 3], "continue 1"]
                for i in range(64)
            ),
            [],
        ),
    ),
)


@pytest.mark.parametrize("name,commands", _LIVES, ids=[n for n, _ in _LIVES])
def test_living_a_life_plants_no_seed_at_all(name, commands):
    world, _ = _run(17, commands)
    assert world.routines
    assert world.seeds == []


@pytest.mark.parametrize("name,commands", _LIVES, ids=[n for n, _ in _LIVES])
def test_living_a_life_promotes_no_heritage(name, commands):
    world, _ = _run(17, commands)
    assert world.heritage == []


def test_no_routine_ever_becomes_a_school():
    for _, commands in _LIVES:
        world, _ = _run(17, commands)
        assert not [h for h in world.heritage]


def test_an_origin_never_appears_in_the_graph_as_an_event():
    """What a person did is not a thing that happened to the world."""
    world, _ = _run(17, _LIVES[1][1])
    routine_ids = {r.id for r in world.routines}
    for node in world.causal_nodes:
        assert node.title
        assert not any(rid in node.title for rid in routine_ids)
        assert node.location_id is None  # no emitter places an event yet


def test_switching_every_year_buys_no_extra_consequence():
    """Sixty-four spans are sixty-four origins, because sixty-four happened.
    They are not sixty-four effects."""
    settled, _ = _run(17, _LIVES[0][1])
    restless, _ = _run(17, _LIVES[2][1])

    assert len(ro.routine_origins(settled)) == 1
    assert len(ro.routine_origins(restless)) == 64
    assert settled.current_year == restless.current_year
    assert (len(settled.seeds), len(settled.heritage)) == (0, 0)
    assert (len(restless.seeds), len(restless.heritage)) == (0, 0)
    assert len(restless.causal_nodes) == len(settled.causal_nodes)


def test_how_you_live_moves_no_theme_axis():
    settled, _ = _run(17, _LIVES[0][1])
    restless, _ = _run(17, _LIVES[2][1])

    assert settled.theme.axes == restless.theme.axes


def test_the_causal_layer_writes_nothing():
    world, _ = _world()
    rt.begin_routine(world, RoutineKind.WORK_AT)
    for _ in range(5):
        advance_year(world)
    before = world.model_dump_json()

    ro.routine_origins(world)
    ro.origin_of(world, world.routines[0])

    assert world.model_dump_json() == before


# --- what the player is shown -----------------------------------------------


def test_the_years_are_not_silent():
    _, text = _run(4, ["work at"] + ["continue 10"] * 7)
    assert re.search(r"^  Year \d+\. .+\.$", text, re.M)


def test_a_war_nobody_can_place_is_reported_to_nobody():
    """Faction and wildcard events name no person and carry no location, so
    the world cannot say who saw them — and does not guess."""
    world, life = _world()
    node = CausalNode(
        id="node-test",
        scale=EventScale.LARGE,
        domain=SeedDomain.MILITARY,
        year=world.current_year,
        title="war between two factions",
        actors=["faction-0001", "faction-0002"],
    )
    assert view.observed_events(world, life.person_id, [node]) == []


def test_what_happened_somewhere_else_stays_there():
    world, life = _world()
    me = pop.person_by_id(world, life.person_id)
    stranger = next(
        p
        for p in pop.living(world)
        if p.lifecycle.location_id != me.lifecycle.location_id
    )
    node = CausalNode(
        id="node-test",
        scale=EventScale.SMALL,
        domain=SeedDomain.GOVERNANCE,
        year=world.current_year,
        title=f"{stranger.name} rises to power",
        actors=[stranger.id],
    )
    assert view.observed_events(world, life.person_id, [node]) == []

    near = node.model_copy(update={"actors": [_neighbours(world, me)[0].id]})
    assert [e.text for e in view.observed_events(world, life.person_id, [near])] == [
        node.title
    ]


_ATTRIBUTION = re.compile(
    r"because|caused|cause of|thanks to|as a result|led to|due to|your (earlier|past|"
    r"previous|doing)|you made this|owing to",
    re.I,
)


def test_the_player_is_never_told_they_caused_anything():
    for seed, commands in (
        (4, ["work at"] + ["continue 10"] * 7),
        (17, _LIVES[1][1]),
        (1, ["work with 1"] + ["continue 10"] * 7),
    ):
        _, text = _run(seed, commands, life_cap=2)
        assert not _ATTRIBUTION.search(text), text


def test_no_identifier_reaches_the_page():
    _, text = _run(
        17, ["work at", "continue 10", "work with 1", "continue 10"], life_cap=2
    )
    assert not re.search(r"\b(npc|node|seed|origin|routine|loc|life)-\d", text)


def test_looking_is_still_free():
    world, _ = _run(4, ["work at", "continue 3"])
    before = (world.current_year, len(world.causal_nodes), len(world.seeds))

    handle(world, "status")
    handle(world, "history")

    assert (world.current_year, len(world.causal_nodes), len(world.seeds)) == before


# --- the old path is untouched ----------------------------------------------


def test_the_old_funnel_still_plants_its_own_seeds():
    from chronicle_forge.autoplay import simulate_world

    world = simulate_world(4, mode="opportunity")
    assert world.routines == []
    assert world.seeds and all(s.id.startswith("seed-") for s in world.seeds)
    assert world.heritage  # the legacy path still earns heritage


def test_a_played_life_never_touches_the_activity_funnel(monkeypatch):
    import chronicle_forge.activity as activity

    def forbidden(*_a, **_k):
        raise AssertionError("the played loop reached perform_activity")

    monkeypatch.setattr(activity, "perform_activity", forbidden)
    world, _ = _run(4, ["work at", "continue 10", "continue 10"])
    assert world.routines and not any(lf.activity_log for lf in world.lives)
