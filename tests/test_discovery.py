"""Dungeon discovery -> causal seed (section B)."""

from __future__ import annotations

from chronicle_forge import begin_life, explore_dungeon, generate_world
from chronicle_forge.enums import DiscoveryType, LocationType, SeedDomain, ThemeAxis


def _dungeon(world):
    return next(l for l in world.locations if l.type == LocationType.DUNGEON)


def test_discovery_creates_linked_seed():
    world = generate_world(seed=11)
    life = begin_life(world)
    dungeon = _dungeon(world)
    disc, seed = explore_dungeon(world, life, dungeon.id, DiscoveryType.TECH)

    assert disc.seed_id == seed.id
    assert seed in world.seeds
    assert disc in world.discoveries
    assert seed.domain == SeedDomain.TECHNOLOGY
    assert disc.theme_affinity == ThemeAxis.INNOVATION
    assert seed.planted_by_life_id == life.id


def test_seal_discovery_maps_to_warfare():
    world = generate_world(seed=11)
    life = begin_life(world)
    dungeon = _dungeon(world)
    disc, seed = explore_dungeon(world, life, dungeon.id, DiscoveryType.SEAL)
    assert seed.domain == SeedDomain.MILITARY
    assert disc.theme_affinity == ThemeAxis.WARFARE
