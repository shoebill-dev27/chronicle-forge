"""P3 macro loop: cross-reincarnation causal continuity and reproducibility.

The success condition for P3 is that a reincarnator leaves a mark on the future:
a life's seed must fire during the post-death skip and shape the world the next
life is born into, and the whole run must be reproducible from the world seed.
"""

from __future__ import annotations

from chronicle_forge import (
    advance_to_next_life,
    advance_year,
    begin_life,
    compute_skip_years,
    end_life,
    explore_dungeon,
    fire_probabilistic_seeds,
    generate_world,
    perform_activity,
    time_skip,
)
from chronicle_forge.enums import (
    ActivationMode,
    ActivityCategory,
    DiscoveryType,
    SeedDomain,
    Talent,
    WildCardStatus,
)
from chronicle_forge.macro import derive_rng
from chronicle_forge.models import CausalSeed


def _scenario(seed: int):
    """A fixed, deterministic playthrough: one life acts, dies, the world skips,
    and a second life is reincarnated."""
    world = generate_world(seed=seed)
    life1 = begin_life(world, talent=Talent.SCHOLAR)
    npc = world.npcs[0]
    perform_activity(
        world, life1, ActivityCategory.EDUCATION, target_id=npc.id, maturation_time=3
    )
    explore_dungeon(world, life1, world.locations[1].id, DiscoveryType.TECH)
    world.seeds.append(
        CausalSeed(
            id="seed-prob",
            domain=SeedDomain.ECONOMY,
            magnitude=60,
            maturation_time=2,
            planted_year=world.current_year,
            planted_by_life_id=life1.id,
            activation_mode=ActivationMode.PROBABILISTIC,
            base_probability=0.7,
        )
    )
    end_life(world, life1)
    advance_to_next_life(world, life1, talent=Talent.MERCHANT)
    return world


def test_same_seed_reproduces_world_history():
    a = _scenario(42)
    b = _scenario(42)
    assert a.model_dump_json() == b.model_dump_json()


def test_different_seed_diverges():
    a = _scenario(42)
    c = _scenario(43)
    assert a.model_dump_json() != c.model_dump_json()


def test_life_seed_affects_next_life_world():
    world = generate_world(seed=21)
    life1 = begin_life(world, talent=Talent.MENTOR)
    npc = world.npcs[0]
    seed = perform_activity(
        world, life1, ActivityCategory.EDUCATION, target_id=npc.id, maturation_time=4
    )
    end_life(world, life1)

    def caused_by_seed():
        return [
            n
            for n in world.causal_nodes
            if any(e.from_id == seed.id for e in n.caused_by)
        ]

    assert caused_by_seed() == []  # not yet fired at death

    skip, life2 = advance_to_next_life(world, life1, talent=Talent.WARRIOR)

    # The life-1 seed fired during the skip and now shapes life-2's world.
    descendants = caused_by_seed()
    assert descendants, "the previous life's seed left no mark on the world"
    assert seed.fired is True
    assert life2 is not None
    assert life2.birth_year > life1.death_year
    # life 2 is born into a world that already contains life 1's consequence.
    assert descendants[0] in world.causal_nodes


def test_probabilistic_firing_is_deterministic():
    # Same seed + year -> same RNG -> same firing decision.
    def run():
        world = generate_world(seed=5)
        world.seeds.append(
            CausalSeed(
                id="s",
                domain=SeedDomain.ECONOMY,
                magnitude=50,
                maturation_time=0,
                planted_year=0,
                planted_by_life_id="life-x",
                activation_mode=ActivationMode.PROBABILISTIC,
                base_probability=0.5,
            )
        )
        rng = derive_rng(world, world.current_year)
        return [s.id for s in fire_probabilistic_seeds(world, rng)]

    assert run() == run()


def test_time_skip_length_matches_formula_and_respects_cap():
    world = generate_world(seed=8)  # max_year = 40 (dev)
    life = begin_life(world)
    life.age_at_death = 30
    life.death_year = world.current_year
    skip = time_skip(world, life)
    assert skip["skip_years"] == compute_skip_years(30, 0)
    assert world.current_year <= world.max_year


def test_time_skip_never_exceeds_max_year():
    world = generate_world(seed=8)
    world.current_year = world.max_year - 2
    life = begin_life(world)
    life.age_at_death = 20  # would skip far, but cap applies
    skip = time_skip(world, life)
    assert world.current_year == world.max_year
    assert skip["world_ended"] is True


def test_wildcard_self_progresses_when_theme_favors_it():
    world = generate_world(seed=7)
    # Several fired technology seeds push INNOVATION above the ignition threshold.
    for i in range(6):
        world.seeds.append(
            CausalSeed(
                id=f"tech-{i}",
                domain=SeedDomain.TECHNOLOGY,
                magnitude=50,
                fired=True,
                planted_by_life_id="life-x",
            )
        )
    for _ in range(25):
        world.current_year += 1
        advance_year(world)

    wc = world.wildcards.wildcards[0]
    assert wc.status in (WildCardStatus.IGNITED, WildCardStatus.RESOLVED)
    wc_events = [n for n in world.causal_nodes if wc.id in n.actors]
    assert wc_events, "an ignited wildcard should emit history"
