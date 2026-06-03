"""Activity execution (section 4.4)."""

from __future__ import annotations

from chronicle_forge import begin_life, generate_world, perform_activity
from chronicle_forge.enums import ActivationMode, ActivityCategory, SeedDomain, Talent


def test_activity_plants_seed_of_profile_domain():
    world = generate_world(seed=11)
    life = begin_life(world)
    seed = perform_activity(world, life, ActivityCategory.COMMERCE)
    assert seed.domain == SeedDomain.ECONOMY
    assert seed.planted_by_life_id == life.id
    assert seed.activation_mode == ActivationMode.GUARANTEED
    assert seed.base_probability == 1.0


def test_talent_match_boosts_magnitude_and_evaluation():
    world = generate_world(seed=11)
    matched = begin_life(world, talent=Talent.MERCHANT)
    s_match = perform_activity(world, matched, ActivityCategory.COMMERCE)

    other = begin_life(world, talent=Talent.WARRIOR)
    s_plain = perform_activity(world, other, ActivityCategory.COMMERCE)

    assert s_match.magnitude > s_plain.magnitude
    assert matched.evaluation.economy > other.evaluation.economy


def test_secondary_lens_accrues_for_education():
    world = generate_world(seed=11)
    life = begin_life(world)
    perform_activity(world, life, ActivityCategory.EDUCATION)
    assert life.evaluation.mentoring > 0  # primary
    assert life.evaluation.heritage > 0  # secondary


def test_targeted_activity_forms_memory():
    world = generate_world(seed=11)
    life = begin_life(world)
    npc = world.npcs[0]
    perform_activity(world, life, ActivityCategory.EDUCATION, target_id=npc.id)
    assert len(world.memories) == 1
    assert world.memories[0].subject_id == npc.id
    assert npc.id in [m.subject_id for m in world.memories]
    assert npc.relations[life.player_id].affinity > 0


def test_activity_logs_and_ages():
    world = generate_world(seed=11)
    life = begin_life(world)
    for _ in range(4):  # TURNS_PER_YEAR
        perform_activity(world, life, ActivityCategory.RESEARCH)
    assert len(life.activity_log) == 4
    assert life.age == 17  # started at 16, one year elapsed
    assert world.current_year == 1
