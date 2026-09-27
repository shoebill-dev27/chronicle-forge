"""Population continuity: people are born, grow up, die, and leave descendants.

What this pins: the world holds a human society for its whole 200 years; every
person has a real birth year and real ancestry; the dead stay in history; and
the player always becomes somebody the world already contains.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle_forge import config, population as pop
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.enums import DeathCause
from chronicle_forge.life import begin_life, end_life
from chronicle_forge.macro import advance_to_next_life, advance_year
from chronicle_forge.models import Life
from chronicle_forge.population import NoSuccessor
from chronicle_forge.worldgen import generate_world

SEEDS = (1, 7, 42, 99, 123)
# The founding adults, the children already alive under them, and one birth a
# year for the whole horizon — the registry cannot grow past this.
INITIAL_PEOPLE = config.MVP_NPC_COUNT + config.ADULT_AGE
POPULATION_BOUND = (
    INITIAL_PEOPLE + config.TRACKED_BIRTHS_PER_YEAR * config.WORLD_MAX_YEARS
)


@pytest.fixture(scope="module")
def worlds():
    return {seed: simulate_world(seed, mode="opportunity") for seed in SEEDS}


def _founders(world):
    return [p for p in world.npcs if not p.lineage.parent_ids]


def _born_during_run(world):
    return [p for p in world.npcs if (p.lifecycle.birth_year or 0) > 0]


# --- birth ------------------------------------------------------------------


def test_a_birth_creates_a_person_with_a_real_birth_year():
    world = generate_world(seed=4)
    begin_life(world)
    before = len(world.npcs)
    advance_year(world)
    assert len(world.npcs) == before + config.TRACKED_BIRTHS_PER_YEAR
    child = world.npcs[-1]
    assert child.lifecycle.birth_year == world.current_year
    assert child.lifecycle.age == 0
    assert child.alive


def test_a_child_ages_with_the_world_and_becomes_an_adult_at_sixteen():
    world = generate_world(seed=4)
    begin_life(world)
    advance_year(world)
    child = world.npcs[-1]
    for _ in range(16):
        advance_year(world)
        assert child.lifecycle.age == world.current_year - child.lifecycle.birth_year
        assert child.lifecycle.life_stage == (
            "adult" if child.lifecycle.age >= 16 else "child"
        )
    assert child.lifecycle.age == 16
    assert child in pop.adults(world)


def test_a_child_is_not_an_actor_but_is_in_history():
    world = generate_world(seed=4)
    begin_life(world)
    advance_year(world)
    child = world.npcs[-1]
    assert child in pop.living(world)
    assert child not in pop.adults(world)


def test_every_birth_has_a_parent_who_was_alive_and_adult(worlds):
    for seed, world in worlds.items():
        by_id = {p.id: p for p in world.npcs}
        for child in _born_during_run(world):
            assert child.lineage.parent_ids, f"seed {seed}: {child.id} has no parent"
            parent = by_id[child.lineage.parent_ids[0]]
            born = child.lifecycle.birth_year
            assert parent.lifecycle.birth_year <= born - config.ADULT_AGE
            died = parent.lifecycle.death_year
            assert died is None or died >= born, f"seed {seed}: dead parent"


def test_the_player_is_never_made_a_parent(worlds):
    for seed, world in worlds.items():
        played = {lf.person_id for lf in world.lives}
        for child in _born_during_run(world):
            assert child.lineage.parent_ids[0] not in played, f"seed {seed}"


def test_the_current_player_person_is_excluded_from_parent_selection():
    world = generate_world(seed=4)
    life = begin_life(world)
    # Only the player's own person is an adult: nobody else may parent a child.
    for person in world.npcs:
        if person.id != life.person_id:
            person.alive = False
    before = len(world.npcs)
    advance_year(world)
    assert len(world.npcs) == before  # no birth rather than a player's child


# --- genealogy ---------------------------------------------------------------


def test_ancestry_reaches_a_founder_without_a_cycle(worlds):
    for seed, world in worlds.items():
        founders = {p.id for p in _founders(world)}
        for person in world.npcs:
            line = pop.ancestors(world, person)
            ids = [p.id for p in line]
            assert len(ids) == len(set(ids)), f"seed {seed}: cycle at {person.id}"
            assert person.id not in ids, f"seed {seed}: {person.id} is its own ancestor"
            if line:
                assert line[-1].id in founders
                assert person.lineage.generation == len(line)


def test_a_lineage_reaches_three_generations(worlds):
    for seed, world in worlds.items():
        assert max(p.lineage.generation for p in world.npcs) >= 3, f"seed {seed}"


def test_descendants_are_traversable_from_a_founder(worlds):
    for seed, world in worlds.items():
        traced = [len(pop.descendants(world, founder)) for founder in _founders(world)]
        assert sum(traced) >= len(_born_during_run(world)), f"seed {seed}"


def test_a_person_alive_at_the_horizon_descends_from_the_first_world(worlds):
    for seed, world in worlds.items():
        first_world = {p.id for p in world.npcs if (p.lifecycle.birth_year or 0) <= 0}
        descended = [
            p
            for p in pop.living(world)
            if any(a.id in first_world for a in pop.ancestors(world, p))
        ]
        assert descended, f"seed {seed}: nobody at year 200 comes from the first world"


# --- death is kept ------------------------------------------------------------


def test_the_dead_stay_in_the_registry(worlds):
    for seed, world in worlds.items():
        dead = [p for p in world.npcs if not p.alive]
        assert dead, f"seed {seed}: nobody has died in 200 years"
        for person in dead:
            assert person.lifecycle.death_year is not None
            assert person.lifecycle.death_year >= (person.lifecycle.birth_year or 0)
            assert pop.person_by_id(world, person.id) is person


def test_nobody_outlives_the_cap(worlds):
    for seed, world in worlds.items():
        for person in world.npcs:
            if person.lifecycle.death_year is not None:
                age = person.lifecycle.death_year - (person.lifecycle.birth_year or 0)
                assert (
                    age <= config.LIFESPAN_CAP
                ), f"seed {seed}: {person.id} aged {age}"


# --- the player is a person ----------------------------------------------------


def test_a_life_is_lived_as_a_real_world_person(worlds):
    for seed, world in worlds.items():
        for life in world.lives:
            person = pop.person_by_id(world, life.person_id)
            assert person is not None, f"seed {seed}: {life.id} has no body"
            assert person.lifecycle.birth_year == life.birth_year
            assert life.playable_start_year - life.birth_year == config.ADULT_AGE


def test_the_players_death_is_the_persons_death(worlds):
    for seed, world in worlds.items():
        for life in world.lives:
            person = pop.person_by_id(world, life.person_id)
            if life.alive:
                assert person.alive, f"seed {seed}: the living player's body died"
            else:
                assert not person.alive
                assert person.lifecycle.death_year == life.death_year


def test_no_person_is_taken_up_twice(worlds):
    for seed, world in worlds.items():
        ids = [lf.person_id for lf in world.lives]
        assert len(ids) == len(set(ids)), f"seed {seed}"


def test_the_successor_was_already_born_when_the_player_died(worlds):
    for seed, world in worlds.items():
        for earlier, later in zip(world.lives, world.lives[1:]):
            assert later.birth_year < earlier.death_year, f"seed {seed}"
            assert later.playable_start_year == earlier.death_year + 10


def test_the_successor_is_exactly_sixteen():
    world = generate_world(seed=4)
    life = begin_life(world)
    end_life(world, life, DeathCause.COMBAT)
    _skip, nxt = advance_to_next_life(world)
    person = pop.person_by_id(world, nxt.person_id)
    assert person.lifecycle.age == config.ADULT_AGE
    assert person.lifecycle.birth_year == world.current_year - config.ADULT_AGE


def test_a_world_with_nobody_of_age_refuses_rather_than_inventing_one():
    world = generate_world(seed=4)
    world.current_year = 50  # no births have run, so nobody here is sixteen
    with pytest.raises(NoSuccessor):
        begin_life(world)


# --- the society survives --------------------------------------------------------


def test_the_world_still_holds_people_at_the_horizon(worlds):
    for seed, world in worlds.items():
        assert pop.living(world), f"seed {seed}: the world emptied"
        assert pop.adults(world), f"seed {seed}: no adult remains"


def test_the_population_stays_within_its_bound(worlds):
    for seed, world in worlds.items():
        assert len(world.npcs) <= POPULATION_BOUND, f"seed {seed}"
        # The scaffold is one birth a year, so the registry grows by the years.
        assert len(world.npcs) == INITIAL_PEOPLE + config.WORLD_MAX_YEARS
        # Nobody passes the cap, so the living are at most one cap of cohorts.
        assert len(pop.living(world)) <= config.LIFESPAN_CAP + INITIAL_PEOPLE


def test_the_founding_generation_dies_out(worlds):
    for seed, world in worlds.items():
        assert all(not p.alive for p in _founders(world)), f"seed {seed}"


def test_births_span_the_timeline(worlds):
    for seed, world in worlds.items():
        years = {p.lifecycle.birth_year for p in _born_during_run(world)}
        assert years == set(range(1, config.WORLD_MAX_YEARS + 1)), f"seed {seed}"


# --- two levels of population truth -----------------------------------------------


def test_the_aggregate_populace_is_not_the_tracked_registry(worlds):
    """``World.population`` is humanity as a number; ``world.npcs`` are the
    people history can name. Nothing derives one from the other, so two
    centuries of births and deaths must leave the aggregate exactly as
    worldgen drew it."""
    for seed, world in worlds.items():
        assert world.population == generate_world(seed=seed).population, seed
        assert world.population != len(pop.living(world)), f"seed {seed}"


def test_a_life_cannot_be_recorded_without_a_tracked_person():
    """The player is always somebody the world holds — there is no valid
    state in which a life names no body, so the field is required."""
    with pytest.raises(ValidationError):
        Life(
            id="life-0000",
            player_id="player-0000",
            birth_year=-16,
            playable_start_year=0,
        )


def test_ending_a_life_whose_person_vanished_raises():
    world = generate_world(seed=4)
    life = begin_life(world)
    world.npcs = [p for p in world.npcs if p.id != life.person_id]
    with pytest.raises(RuntimeError):
        end_life(world, life, DeathCause.COMBAT)


# --- determinism ------------------------------------------------------------------


def test_the_same_seed_writes_the_same_people():
    a = simulate_world(7, mode="opportunity")
    b = simulate_world(7, mode="opportunity")
    assert [
        (
            p.id,
            p.name,
            p.lifecycle.birth_year,
            p.lifecycle.death_year,
            p.lineage.parent_ids,
        )
        for p in a.npcs
    ] == [
        (
            p.id,
            p.name,
            p.lifecycle.birth_year,
            p.lifecycle.death_year,
            p.lineage.parent_ids,
        )
        for p in b.npcs
    ]


def test_different_seeds_write_different_families():
    a = simulate_world(7, mode="opportunity")
    b = simulate_world(99, mode="opportunity")
    assert [p.lineage.parent_ids for p in a.npcs] != [
        p.lineage.parent_ids for p in b.npcs
    ]
