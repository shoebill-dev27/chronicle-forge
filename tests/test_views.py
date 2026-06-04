"""Read-only observability views (P5). Views must render from existing data
without mutating state."""

from __future__ import annotations

from chronicle_forge import (
    begin_life,
    end_life,
    generate_world,
    perform_activity,
    render_causal_trace,
    render_heritage_ranking,
    render_npc_codex,
    render_personal_history,
)
from chronicle_forge.enums import ActivityCategory, Talent
from chronicle_forge.pipeline import advance_history
from chronicle_forge.views import render_world_summary


def _world_with_a_fired_seed():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.SCHOLAR)
    seed = perform_activity(world, life, ActivityCategory.RESEARCH, maturation_time=0)
    advance_history(world)  # fire the seed into an event
    return world, life, seed


def test_personal_history_does_not_mutate_world():
    world, _, _ = _world_with_a_fired_seed()
    before = world.model_dump_json()
    render_personal_history(world)
    assert world.model_dump_json() == before


def test_personal_history_contains_life_and_evaluation():
    world, life, _ = _world_with_a_fired_seed()
    end_life(world, life)
    text = render_personal_history(world)
    assert life.id in text
    assert "evaluation:" in text
    assert "Inheritance" in text


def test_causal_trace_highlights_player_seed():
    world, _, seed = _world_with_a_fired_seed()
    node = world.causal_nodes[0]
    text = render_causal_trace(world, node.id)
    assert node.id in text
    assert seed.id in text
    assert "★" in text  # player-driven seed marker


def test_causal_trace_unknown_node():
    world, _, _ = _world_with_a_fired_seed()
    text = render_causal_trace(world, "node-does-not-exist")
    assert "not found" in text


def test_heritage_ranking_renders_columns():
    world = generate_world(seed=4)
    life = begin_life(world, talent=Talent.MENTOR)
    perform_activity(world, life, ActivityCategory.EDUCATION, maturation_time=0)
    world.current_year = 10
    advance_history(world)  # fire + promote heritage
    text = render_heritage_ranking(world)
    assert "HERITAGE RANKING" in text
    assert "score=" in text and "reach=" in text and "longevity=" in text


def test_npc_codex_shows_birth_year():
    world = generate_world(seed=4)
    text = render_npc_codex(world)
    assert "NPC CODEX" in text
    assert "born y" in text


def test_world_summary_basic_fields():
    world = generate_world(seed=4)
    text = render_world_summary(world)
    assert "seed=4" in text
    assert "theme dominant" in text
