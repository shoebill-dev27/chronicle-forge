"""MVP world-shape invariants (section 3)."""

from __future__ import annotations

from chronicle_forge import generate_world
from chronicle_forge.config import (
    ADULT_AGE,
    WORLD_MAX_YEARS,
    MVP_IMPORTANT_NPC_COUNT,
    MVP_NPC_COUNT,
    MVP_WILDCARD_COUNT,
)
from chronicle_forge.enums import FactionType, LocationType, NPCTier


def test_exactly_one_village_and_one_dungeon():
    w = generate_world(seed=99)
    villages = [l for l in w.locations if l.type == LocationType.VILLAGE]
    dungeons = [l for l in w.locations if l.type == LocationType.DUNGEON]
    assert len(villages) == 1
    assert len(dungeons) == 1


def test_four_distinct_faction_types():
    w = generate_world(seed=99)
    assert len(w.factions) == 4
    assert {f.type for f in w.factions} == {
        FactionType.LORD,
        FactionType.MERCHANT,
        FactionType.RELIGIOUS,
        FactionType.ADVENTURER,
    }


def _founders(world):
    """The adults the world begins with — the people with no parents."""
    return [n for n in world.npcs if not n.lineage.parent_ids]


def test_npc_count_and_tiers():
    w = generate_world(seed=99)
    founders = _founders(w)
    assert len(founders) == MVP_NPC_COUNT
    s_tier = [n for n in w.npcs if n.tier == NPCTier.S]
    assert len(s_tier) == MVP_IMPORTANT_NPC_COUNT
    assert all(n.tier == NPCTier.A for n in w.npcs if n not in s_tier)


def test_the_world_begins_with_children_as_well_as_adults():
    """A village with no young has no sixteen-year-old for the player to be
    until the birth scaffold has run that many years."""
    w = generate_world(seed=99)
    ages = sorted(n.lifecycle.age for n in w.npcs)
    assert ages[:ADULT_AGE] == list(range(ADULT_AGE))  # one child of each age
    assert len(w.npcs) == MVP_NPC_COUNT + ADULT_AGE
    assert min(n.lifecycle.age for n in _founders(w)) == ADULT_AGE


def test_single_wildcard_designed_for_n():
    w = generate_world(seed=99)
    assert len(w.wildcards.wildcards) == MVP_WILDCARD_COUNT
    # Registry holds a list, so adding more later needs no schema change.
    assert isinstance(w.wildcards.wildcards, list)


def test_the_founding_generation_has_no_ancestry_and_the_children_do():
    w = generate_world(seed=99)
    founder_ids = {n.id for n in _founders(w)}
    for npc in _founders(w):
        assert npc.lineage.lineage_id is None
        assert npc.lineage.generation == 0
    children = [n for n in w.npcs if n.lineage.parent_ids]
    assert len(children) == ADULT_AGE
    for child in children:
        assert child.lineage.parent_ids[0] in founder_ids
        assert child.lineage.lineage_id == child.lineage.parent_ids[0]
        assert child.lineage.generation == 1


def test_defaults_and_population():
    w = generate_world(seed=99)
    assert w.max_year == WORLD_MAX_YEARS
    # The aggregate populace is a crowd number; the tracked persons are a
    # separate level of truth and neither is derived from the other.
    assert w.population > 0
    assert w.player.powers.manifest_charges == 1
    assert w.theme.dominant is not None


def test_every_npc_belongs_to_an_existing_faction():
    w = generate_world(seed=99)
    faction_ids = {f.id for f in w.factions}
    for npc in w.npcs:
        assert npc.lifecycle.faction_id in faction_ids
