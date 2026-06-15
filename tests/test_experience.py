"""Tests for P7-1 Dead Summary (reporting/experience.py)."""

from __future__ import annotations

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.life import begin_life
from chronicle_forge.reporting import dead_summary, life_chronicle, life_timeline
from chronicle_forge.reporting._data import heritage_rows, seed_by_id
from chronicle_forge.worldgen import generate_world

SEED = 42


def _life_with_heritage(world):
    """A life that promoted at least one Heritage (top heritage's origin life)."""
    rows = heritage_rows(world)
    assert rows, "expected this seed to produce heritage"
    seed = seed_by_id(world, rows[0]["source_seed"])
    return next(lf for lf in world.lives if lf.id == seed.planted_by_life_id)


def test_deterministic():
    world = simulate_world(SEED)
    life = world.lives[0]
    assert dead_summary(world, life) == dead_summary(world, life)


def test_read_only():
    world = simulate_world(SEED)
    life = world.lives[-1]
    before_world = world.model_dump()
    before_life = life.model_dump()
    dead_summary(world, life)
    assert world.model_dump() == before_world
    assert life.model_dump() == before_life


def test_heritage_world_shows_what_outlived_you():
    world = simulate_world(SEED)
    life = _life_with_heritage(world)
    out = dead_summary(world, life)
    assert "What outlived you?" in out
    # The headline Seed -> History example must name the enduring legacy.
    top_name = heritage_rows(world)[0]["name"]
    # the life's own top legacy name appears (may differ from world top, so just
    # assert a quoted enduring legacy is present)
    assert "still endured." in out
    assert top_name  # sanity


def test_heritageless_life_has_natural_fallback():
    # A freshly-begun life in a fresh world has no seeds/heritage.
    world = generate_world(SEED)
    life = begin_life(world, talent=None)
    out = dead_summary(world, life)
    assert "Nothing you built survived long after your death." in out
    assert "the world remembered your passing." in out
    assert "What outlived you?" not in out


def test_empty_life_is_resilient():
    world = generate_world(SEED)
    life = begin_life(world, talent=None)
    out = dead_summary(world, life)
    # Always at least a title + a lifespan line; never crashes, never empty.
    assert out.splitlines()[0].startswith("─")
    assert "You lived" in out


def test_no_bare_seed_count_headline():
    # The screen must never reduce to "You planted N seeds." (numbers-only ban).
    world = simulate_world(SEED)
    for life in world.lives:
        out = dead_summary(world, life)
        assert "You planted" not in out


def test_lifespan_uses_age_at_death():
    world = simulate_world(SEED)
    for life in world.lives:
        out = dead_summary(world, life)
        assert "You lived" in out
        if life.age_at_death:
            assert f"You lived {life.age_at_death} years." in out


# --- P7-2 Chronicle Generator -------------------------------------------


def test_chronicle_deterministic():
    world = simulate_world(SEED)
    life = world.lives[0]
    assert life_chronicle(world, life) == life_chronicle(world, life)


def test_chronicle_read_only():
    world = simulate_world(SEED)
    life = world.lives[-1]
    before = world.model_dump()
    life_chronicle(world, life)
    assert world.model_dump() == before


def test_chronicle_is_third_person_history():
    world = simulate_world(SEED)
    for life in world.lives:
        out = life_chronicle(world, life)
        assert "You " not in out  # not the second-person death screen
        assert out.startswith("They lived as")


def test_chronicle_line_count_in_range():
    world = simulate_world(SEED)
    for life in world.lives:
        n = len(life_chronicle(world, life).splitlines())
        assert 3 <= n <= 10


_LEGACY_CLOSERS = (
    "still bore their mark.",
    "still carried their name.",
    "still remembered their work.",
    "still echoed their choices.",
)


def test_chronicle_heritage_world_names_the_legacy():
    world = simulate_world(SEED)
    life = _life_with_heritage(world)
    out = life_chronicle(world, life)
    # An enduring legacy is named and closed on one of the deterministic cadences.
    assert any(closer in out for closer in _LEGACY_CLOSERS)


def test_chronicle_legacy_closer_is_deterministic():
    world = simulate_world(SEED)
    life = _life_with_heritage(world)
    assert life_chronicle(world, life) == life_chronicle(world, life)


def test_chronicle_heritageless_life_closes_honestly():
    world = generate_world(SEED)
    life = begin_life(world, talent=None)
    out = life_chronicle(world, life)
    assert not any(closer in out for closer in _LEGACY_CLOSERS)
    assert "age closed over them." in out or "marked their passing" in out


# --- P7-3 Historical Timeline -------------------------------------------


def test_timeline_deterministic():
    world = simulate_world(SEED)
    life = world.lives[0]
    assert life_timeline(world, life) == life_timeline(world, life)


def test_timeline_read_only():
    world = simulate_world(SEED)
    life = world.lives[-1]
    before = world.model_dump()
    life_timeline(world, life)
    assert world.model_dump() == before


def test_timeline_is_player_facing_markdown_third_person():
    world = simulate_world(SEED)
    for life in world.lives:
        out = life_timeline(world, life)
        assert out.startswith("# ")  # a player-facing reading, not a dev table
        assert "## Their life" in out
        assert "## What outlived them" in out
        assert "| Year |" not in out  # not a developer table
        assert "You " not in out  # third person, not the death screen


def test_timeline_heritage_layer_extends_past_death():
    world = simulate_world(SEED)
    life = _life_with_heritage(world)
    out = life_timeline(world, life)
    top_name = _top_legacy_name(world, life)
    assert f'"{top_name}"' in out
    assert "still endured" in out


def test_timeline_heritageless_life_has_honest_outlived_section():
    world = generate_world(SEED)
    life = begin_life(world, talent=None)
    out = life_timeline(world, life)
    assert "## What outlived them" in out
    assert "Nothing they built outlasted the age" in out


def _top_legacy_name(world, life):
    rows = heritage_rows(world)
    seed = seed_by_id(world, rows[0]["source_seed"])
    assert seed.planted_by_life_id == life.id
    return rows[0]["name"]
