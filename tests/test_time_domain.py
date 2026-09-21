"""Time domain: the world clock, a life's chronology, mortality, and the gap.

Owner decisions pinned here: one simulation tick is one world year and
``advance_year`` is its only seam; a life is taken up at 16 and, with no hazard
in play, reaches 80; death before 80 comes only through the mortality seam; a
life's ``birth_year`` is its actual birth (the first life was born in year
-16); the gap between a death and the next life is exactly ten world years,
seed-independent; the world horizon is year 200 and the run ends there even
mid-life.
"""

from __future__ import annotations

import pytest

from chronicle_forge import config, mortality
from chronicle_forge.activity import perform_activity
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.enums import ActivityCategory, DeathCause
from chronicle_forge.life import START_AGE, begin_life, end_life
from chronicle_forge.macro import (
    WorldHorizonReached,
    advance_to_next_life,
    advance_year,
    time_skip,
)
from chronicle_forge.play.human import null_writer, scripted_reader
from chronicle_forge.play.session import run_human_world
from chronicle_forge.worldgen import generate_world


def _run_until_dead(world, life):
    while life.alive and world.current_year < world.max_year:
        advance_year(world)


def _dies_at(age):
    def hazard(world, life, rng):
        return DeathCause.COMBAT if life.age >= age else None

    return hazard


# --- chronology ------------------------------------------------------------


def test_the_first_life_is_taken_up_at_sixteen_in_year_zero():
    world = generate_world(seed=4)
    life = begin_life(world)
    assert world.current_year == 0
    assert life.age == START_AGE == 16
    assert life.playable_start_year == 0
    assert life.birth_year == -16  # born before the world's record begins
    assert life.alive


def test_a_life_taken_up_in_year_fifty_was_born_in_thirty_four():
    world = generate_world(seed=4)
    world.current_year = 50
    life = begin_life(world)
    assert life.playable_start_year == 50
    assert life.birth_year == 34
    assert life.age == 16


def test_age_is_exactly_world_year_minus_birth_year():
    world = generate_world(seed=4)
    start = world.current_year
    life = begin_life(world)
    for n in range(1, 25):
        advance_year(world)
        assert world.current_year == start + n
        assert life.age == world.current_year - life.birth_year == START_AGE + n


def test_no_default_hazard_is_registered():
    assert mortality.HAZARDS == []
    assert not hasattr(config, "COMBAT_DEATH_PROB_PER_YEAR")


def test_healthy_life_reaches_eighty():
    world = generate_world(seed=4)
    life = begin_life(world)
    _run_until_dead(world, life)
    assert not life.alive
    assert life.age_at_death == config.LIFESPAN_CAP == 80
    assert life.death_cause == DeathCause.LIFESPAN
    assert life.death_year == life.birth_year + 80
    assert life.death_year == life.playable_start_year + 64


def test_every_death_in_a_default_run_is_lifespan_at_eighty():
    for seed in (1, 7, 42):
        for lf in simulate_world(seed, mode="opportunity").lives:
            if not lf.alive:
                assert (lf.death_cause, lf.age_at_death) == (DeathCause.LIFESPAN, 80)


# --- mortality seam -----------------------------------------------------------


def test_explicit_hazard_can_end_a_life_early(monkeypatch):
    monkeypatch.setattr(mortality, "HAZARDS", [_dies_at(30)])
    world = generate_world(seed=4)
    life = begin_life(world)
    _run_until_dead(world, life)
    assert life.age_at_death == 30
    assert life.death_cause == DeathCause.COMBAT
    assert life.death_year == life.birth_year + 30


def test_hazard_death_is_deterministic_for_identical_inputs(monkeypatch):
    calls = []

    def coin(world, life, rng):
        calls.append(rng.random())  # the seam's own stream, same every run
        return DeathCause.COMBAT if calls[-1] < 0.05 else None

    monkeypatch.setattr(mortality, "HAZARDS", [coin])

    def run():
        world = generate_world(seed=4)
        life = begin_life(world)
        _run_until_dead(world, life)
        return world.model_dump_json(), list(calls)

    a, draws_a = run()
    calls.clear()
    b, draws_b = run()
    assert a == b and draws_a == draws_b


def test_hazard_rng_is_separate_from_the_world_stream(monkeypatch):
    def run():
        world = generate_world(seed=4)
        begin_life(world)
        for _ in range(20):
            advance_year(world)
        return [n.id for n in world.causal_nodes], world.theme.history

    plain = run()
    monkeypatch.setattr(mortality, "HAZARDS", [lambda w, l, rng: rng.random() and None])
    assert run() == plain


def test_death_truth_is_fixed_once():
    world = generate_world(seed=4)
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    with pytest.raises(RuntimeError):
        end_life(world, life, DeathCause.LIFESPAN)


# --- reincarnation gap ---------------------------------------------------------


def test_next_life_is_taken_up_exactly_ten_years_after_death():
    world = generate_world(seed=4)
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    death = life.death_year
    skip, nxt = advance_to_next_life(world)
    assert skip["years_run"] == config.REINCARNATION_GAP_YEARS == 10
    assert world.current_year == death + 10
    assert nxt is not None
    assert nxt.playable_start_year == death + 10
    assert nxt.birth_year == death + 10 - START_AGE  # the body predates the gap


def test_gap_does_not_depend_on_planted_seeds():
    world = generate_world(seed=4)
    life = begin_life(world)
    for _ in range(12):  # many unfired seeds with long maturation
        perform_activity(world, life, ActivityCategory.RESEARCH, maturation_time=30)
    end_life(world, life, DeathCause.COMBAT)
    death = world.current_year
    time_skip(world)
    assert world.current_year == death + 10


def test_every_reincarnation_in_a_full_run_is_ten_years_apart():
    for seed in (1, 42):
        lives = simulate_world(seed, mode="opportunity").lives
        for a, b in zip(lives, lives[1:]):
            assert b.playable_start_year == a.death_year + 10
            assert b.birth_year == b.playable_start_year - START_AGE


def test_world_keeps_simulating_during_the_gap():
    world = generate_world(seed=4)
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    before = len(world.theme.history)
    time_skip(world)
    assert len(world.theme.history) == before + 10


# --- the horizon ------------------------------------------------------------


def test_death_near_horizon_runs_only_the_available_gap():
    world = generate_world(seed=4)
    world.current_year = 195
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    skip, nxt = advance_to_next_life(world)
    assert skip["years_run"] == 5
    assert world.current_year == 200
    assert skip["world_ended"] is True
    assert nxt is None


def test_world_stops_exactly_at_two_hundred():
    world = simulate_world(42, mode="opportunity")
    assert world.max_year == config.WORLD_MAX_YEARS == 200
    assert world.current_year == 200
    with pytest.raises(WorldHorizonReached):
        advance_year(world)


def test_run_ends_at_horizon_with_the_life_still_alive():
    world = generate_world(seed=4)
    world.current_year = 197
    life = begin_life(world)
    for _ in range(3):
        advance_year(world)
    assert world.current_year == 200
    assert life.alive
    with pytest.raises(WorldHorizonReached):
        advance_year(world)


def test_default_run_is_three_lives_with_the_third_unfinished():
    """0-64, gap to 74, 74-138, gap to 148, 148-200: the horizon comes at 68."""
    world = run_human_world(4, reader=scripted_reader([]), writer=null_writer)
    spans = [(lf.playable_start_year, lf.death_year) for lf in world.lives]
    assert spans == [(0, 64), (74, 138), (148, None)]
    assert world.lives[-1].alive and world.lives[-1].age == 68


# --- determinism ---------------------------------------------------------------


def test_same_seed_same_time_and_death_results():
    a = run_human_world(42, reader=scripted_reader([]), writer=null_writer)
    b = run_human_world(42, reader=scripted_reader([]), writer=null_writer)
    assert a.model_dump_json() == b.model_dump_json()
    assert [
        (lf.birth_year, lf.playable_start_year, lf.death_year, lf.age_at_death)
        for lf in a.lives
    ] == [
        (lf.birth_year, lf.playable_start_year, lf.death_year, lf.age_at_death)
        for lf in b.lives
    ]
