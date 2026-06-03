"""Life lifecycle: reincarnation, death, LifeSummary, inheritance (section 4)."""

from __future__ import annotations

from chronicle_forge import (
    advance_history,
    begin_life,
    end_life,
    generate_world,
    lifespan_reached,
    perform_activity,
)
from chronicle_forge.enums import ActivityCategory, DeathCause, Talent


def test_begin_life_sets_current_life():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.MERCHANT)
    assert world.player.current_life_id == life.id
    assert life in world.lives
    assert life.age == 16
    assert life.birth_year == world.current_year


def test_end_life_builds_summary_and_clears_current_life():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.SCHOLAR)
    perform_activity(world, life, ActivityCategory.RESEARCH)
    perform_activity(world, life, ActivityCategory.RESEARCH)

    summary = end_life(world, life, DeathCause.LIFESPAN)
    assert life.death_cause == DeathCause.LIFESPAN
    assert life.age_at_death == life.age
    assert summary.life_id == life.id
    assert summary.title == "The Scholar of Hollowfen"
    assert len(summary.seeds_created) == 2
    assert summary.dominant_axis is not None
    assert world.player.current_life_id is None


def test_bequest_carries_title_to_inheritance():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.MERCHANT)
    perform_activity(world, life, ActivityCategory.COMMERCE)
    summary = end_life(world, life)
    assert summary.title in world.player.inherited.titles


def test_summary_captures_fired_events_as_notable():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.SCHOLAR)
    seed = perform_activity(world, life, ActivityCategory.RESEARCH, maturation_time=0)

    advance_history(world)  # the matured seed fires into an event node
    summary = end_life(world, life)
    assert seed.id in summary.seeds_created
    assert len(summary.notable_events) >= 1


def test_lifespan_reached_flag():
    world = generate_world(seed=4)
    life = begin_life(world, birth_age=80)
    assert lifespan_reached(life) is True
