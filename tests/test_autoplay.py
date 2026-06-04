"""Integration smoke (P5): one command runs a world to completion and reports.

Completion condition: a human can read seed=42's full history and judge the game.
"""

from __future__ import annotations

from chronicle_forge import simulate_report, simulate_world


def test_simulate_world_is_deterministic():
    a = simulate_world(42)
    b = simulate_world(42)
    assert a.model_dump_json() == b.model_dump_json()


def test_simulate_world_runs_to_completion():
    world = simulate_world(42)
    assert world.current_year == world.max_year
    assert len(world.lives) >= 1
    assert world.ending_class is not None


def test_simulate_world_produces_observable_history():
    world = simulate_world(42)
    # The reincarnator left a mark: events and heritage exist.
    assert len(world.causal_nodes) > 0
    assert len(world.heritage) > 0
    # Theme evolved over time.
    assert len(world.theme.history) >= world.max_year - 1


def test_report_contains_all_required_sections():
    report = simulate_report(42)
    for section in [
        "WORLD SUMMARY",
        "PLAYER LIVES",
        "THEME TRAJECTORY",
        "WILDCARD HISTORY",
        "HERITAGE RANKING",
        "NPC CODEX",
    ]:
        assert section in report


def test_different_seed_yields_different_report():
    assert simulate_report(42) != simulate_report(7)
