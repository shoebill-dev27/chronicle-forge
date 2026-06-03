"""MVP world-shape invariants (section 3)."""

from __future__ import annotations

from chronicle_forge import generate_world
from chronicle_forge.config import (
    DEV_WORLD_MAX_YEARS,
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


def test_npc_count_and_tiers():
    w = generate_world(seed=99)
    assert len(w.npcs) == MVP_NPC_COUNT
    s_tier = [n for n in w.npcs if n.tier == NPCTier.S]
    a_tier = [n for n in w.npcs if n.tier == NPCTier.A]
    assert len(s_tier) == MVP_IMPORTANT_NPC_COUNT
    assert len(a_tier) == MVP_NPC_COUNT - MVP_IMPORTANT_NPC_COUNT


def test_single_wildcard_designed_for_n():
    w = generate_world(seed=99)
    assert len(w.wildcards.wildcards) == MVP_WILDCARD_COUNT
    # Registry holds a list, so adding more later needs no schema change.
    assert isinstance(w.wildcards.wildcards, list)


def test_lineage_fields_reserved_but_unused():
    w = generate_world(seed=99)
    for npc in w.npcs:
        assert npc.lineage.lineage_id is None
        assert npc.lineage.parent_ids == []
        assert npc.lineage.generation == 0


def test_defaults_and_population():
    w = generate_world(seed=99)
    assert w.max_year == DEV_WORLD_MAX_YEARS
    assert w.population > 0
    assert w.player.powers.manifest_charges == 1
    assert w.theme.dominant is not None


def test_every_npc_belongs_to_an_existing_faction():
    w = generate_world(seed=99)
    faction_ids = {f.id for f in w.factions}
    for npc in w.npcs:
        assert npc.lifecycle.faction_id in faction_ids
