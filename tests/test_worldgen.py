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


# --- the founding generation could have had the children it has -------------

SWEEP = range(300)  # a seed sweep: the invariant must not be a property of 99


def _parent_age_at_birth(child, parent) -> int:
    """How old the parent was in the year the child was born — chronology, not
    how old either of them happens to be now."""
    return child.lifecycle.birth_year - parent.lifecycle.birth_year


def test_every_initial_child_has_a_parent_who_could_have_had_them():
    for seed in SWEEP:
        w = generate_world(seed=seed)
        by_id = {n.id: n for n in w.npcs}
        for child in [n for n in w.npcs if n.lineage.parent_ids]:
            parent = by_id.get(child.lineage.parent_ids[0])
            assert parent is not None, f"seed {seed}: {child.id} has no parent row"
            gap = _parent_age_at_birth(child, parent)
            assert (
                gap > ADULT_AGE
            ), f"seed {seed}: {parent.name} was {gap} when {child.name} was born"


def test_no_parent_was_born_after_their_own_child():
    for seed in SWEEP:
        w = generate_world(seed=seed)
        by_id = {n.id: n for n in w.npcs}
        for child in [n for n in w.npcs if n.lineage.parent_ids]:
            parent = by_id[child.lineage.parent_ids[0]]
            assert parent.lifecycle.birth_year < child.lifecycle.birth_year


def test_the_first_playable_person_is_given_no_children():
    """The sixteen-year-old the player may be taken up as in year 0 cannot be
    anyone's parent — they were not born when any of these children were. It
    falls out of the chronology, not out of a special case for the player."""
    for seed in SWEEP:
        w = generate_world(seed=seed)
        youngest_adult = min(_founders(w), key=lambda n: (n.lifecycle.age, n.id))
        assert youngest_adult.lifecycle.age == ADULT_AGE
        assert not [
            n for n in w.npcs if youngest_adult.id in n.lineage.parent_ids
        ], f"seed {seed}: the age-{ADULT_AGE} founder was handed a child"


def test_the_founding_generation_always_contains_someone_old_enough():
    """The eldest child is ADULT_AGE - 1, so the world needs a founder who was
    over ADULT_AGE that many years ago, or there would be no valid parent and
    nothing honest to fall back on."""
    for seed in SWEEP:
        w = generate_world(seed=seed)
        eldest_child_birth = -(ADULT_AGE - 1)
        assert any(
            eldest_child_birth - n.lifecycle.birth_year > ADULT_AGE
            for n in _founders(w)
        ), f"seed {seed}"


def test_initial_genealogy_is_deterministic():
    a, b = generate_world(seed=7), generate_world(seed=7)
    assert [(n.id, n.lineage.parent_ids) for n in a.npcs] == [
        (n.id, n.lineage.parent_ids) for n in b.npcs
    ]


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
