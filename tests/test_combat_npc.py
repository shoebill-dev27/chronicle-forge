"""Rule-based combat and minimal NPC stepping (sections 6.3 / AI policy)."""

from __future__ import annotations

from chronicle_forge import (
    begin_life,
    generate_world,
    player_fight,
    resolve_combat,
    step_npc,
)
from chronicle_forge.enums import DeathCause
from chronicle_forge.rng import DeterministicRNG


def test_resolve_combat_strength_dominates():
    rng = DeterministicRNG(1)
    assert resolve_combat(1000, 1, rng) == "attacker"
    assert resolve_combat(1, 1000, rng) == "defender"


def test_player_fight_win_bumps_military():
    world = generate_world(seed=6)
    life = begin_life(world)
    before = life.evaluation.military
    won = player_fight(world, life, enemy_power=1, rng=DeterministicRNG(1))
    assert won is True
    assert life.evaluation.military > before


def test_player_fight_loss_ends_life_by_combat():
    world = generate_world(seed=6)
    life = begin_life(world)
    won = player_fight(world, life, enemy_power=10_000, rng=DeterministicRNG(1))
    assert won is False
    assert life.death_cause == DeathCause.COMBAT
    assert world.player.current_life_id is None


def test_step_npc_returns_intent():
    world = generate_world(seed=6)
    npc = world.npcs[0]
    intent = step_npc(world, npc)
    assert intent in {
        "seek_power",
        "seek_wealth",
        "spread_faith",
        "seek_valor",
        "keep_peace",
    }
    assert npc.goals == [intent]


def test_step_dead_npc_returns_none():
    world = generate_world(seed=6)
    npc = world.npcs[0]
    npc.alive = False
    assert step_npc(world, npc) is None
