"""Rule-based combat (section / AI policy: no AI in ordinary combat).

A deterministic-with-seeded-jitter resolution. The player's combat power derives
from their military evaluation, so combat feeds the same evaluation loop as every
other activity. Losing a fight can end the life (DeathCause.COMBAT).
"""

from __future__ import annotations

from .enums import DeathCause
from .life import end_life
from .models import Life, World
from .rng import DeterministicRNG

COMBAT_BASE_POWER = 10
COMBAT_WIN_MILITARY_BONUS = 5


def player_combat_power(life: Life) -> int:
    return COMBAT_BASE_POWER + life.evaluation.military


def resolve_combat(
    attacker_power: int, defender_power: int, rng: DeterministicRNG
) -> str:
    """Return "attacker" or "defender" as the winner."""
    roll = rng.random()
    attacker_score = attacker_power * (0.5 + roll)
    defender_score = defender_power * (1.5 - roll)
    return "attacker" if attacker_score >= defender_score else "defender"


def player_fight(
    world: World, life: Life, enemy_power: int, rng: DeterministicRNG
) -> bool:
    """Resolve a fight for the player. Returns True on win; a loss ends the life."""
    winner = resolve_combat(player_combat_power(life), enemy_power, rng)
    if winner == "defender":
        end_life(world, life, DeathCause.COMBAT)
        return False
    life.evaluation.military += COMBAT_WIN_MILITARY_BONUS
    return True
