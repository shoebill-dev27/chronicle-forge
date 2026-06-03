"""Dungeon discovery -> causal seed (section B).

Clearing a dungeon mines a Discovery, which becomes a causal seed that can
parent world events during the post-death skip. This is how exploration leaves a
mark on history rather than just granting power.
"""

from __future__ import annotations

from .enums import DiscoveryType, SeedDomain, ThemeAxis
from .ids import next_id
from .life import advance_time
from .models import CausalSeed, Discovery, Life, World

DISCOVERY_SEED_DOMAIN: dict[DiscoveryType, SeedDomain] = {
    DiscoveryType.TECH: SeedDomain.TECHNOLOGY,
    DiscoveryType.RELIC: SeedDomain.FAITH,
    DiscoveryType.SEAL: SeedDomain.MILITARY,
    DiscoveryType.LORE: SeedDomain.GOVERNANCE,
}

DISCOVERY_THEME: dict[DiscoveryType, ThemeAxis] = {
    DiscoveryType.TECH: ThemeAxis.INNOVATION,
    DiscoveryType.RELIC: ThemeAxis.FAITH,
    DiscoveryType.SEAL: ThemeAxis.WARFARE,
    DiscoveryType.LORE: ThemeAxis.GOVERNANCE,
}

DISCOVERY_MAGNITUDE = 70
DISCOVERY_MATURATION = 8
EXPLORATION_TURN_COST = 2


def explore_dungeon(
    world: World, life: Life, location_id: str, discovery_type: DiscoveryType
) -> tuple[Discovery, CausalSeed]:
    """Make a discovery in a dungeon, planting a high-magnitude causal seed."""
    domain = DISCOVERY_SEED_DOMAIN[discovery_type]
    seed = CausalSeed(
        id=next_id("seed", world.seeds),
        domain=domain,
        magnitude=DISCOVERY_MAGNITUDE,
        maturation_time=DISCOVERY_MATURATION,
        planted_year=world.current_year,
        planted_by_life_id=life.id,
    )
    world.seeds.append(seed)

    discovery = Discovery(
        id=next_id("disc", world.discoveries),
        type=discovery_type,
        location_id=location_id,
        theme_affinity=DISCOVERY_THEME[discovery_type],
        seed_id=seed.id,
    )
    world.discoveries.append(discovery)

    life.evaluation.academia += 10
    advance_time(world, life, EXPLORATION_TURN_COST)
    return discovery, seed
