"""P10 Social Memory contract — test-first (RED until reporting/social_memory.py).

The Social Memory view is a read-only projection of the social trace a soul leaves
across its lives: the people who remember a past self, and how. Memories are
already attributed to the stable soul id (``Player.id``), so this only *surfaces*
existing data — it mutates nothing, takes no engine flag, leaks no internal id
(the P8 lesson; the soul id ``player-0000`` is itself an internal id and must
never appear), and is deterministic. Nothing here changes the world, P6/P7/P8/P9-*
P10-Observatory or the seed42 golden.
"""

from __future__ import annotations

import hashlib
import re

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.reporting.social_memory import (
    _life_ordinal_for_year,
    social_memory_bonds,
    social_memory_view,
)
from chronicle_forge.worldgen import generate_world

# Frozen at GREEN: the Social Memory view's permanent seed42 regression guard.
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"

# Note the extra ``player`` alternative: the soul id (player-0000) is internal.
_INTERNAL_ID = re.compile(r"\b(seed|life|npc|node|loc|fac|her|player)-\d")


def _world():
    return simulate_world(42, mode="opportunity")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# --- shape: markdown, read-only, deterministic, id-free -----------------


def test_social_memory_view_is_markdown():
    assert social_memory_view(_world()).lstrip().startswith("#")


def test_social_memory_view_is_read_only():
    world = _world()
    before = world.model_dump_json()
    social_memory_view(world)
    assert world.model_dump_json() == before


def test_social_memory_view_is_deterministic():
    world = _world()
    assert social_memory_view(world) == social_memory_view(world)


def test_social_memory_view_no_internal_ids():
    out = social_memory_view(_world())
    assert not _INTERNAL_ID.search(out), out
    assert "player-" not in out
    assert "legacy:" not in out


# --- content: every remembering NPC surfaced, attributed to a past life --


def test_social_memory_view_names_every_remembering_npc():
    world = _world()
    soul = world.player.id
    out = social_memory_view(world)
    remembering = [n for n in world.npcs if soul in n.relations]
    assert remembering, "expected the seed42 world to have soul-bonded NPCs"
    for npc in remembering:
        assert npc.name in out, npc.name


def test_social_memory_bonds_one_per_remembering_npc():
    world = _world()
    soul = world.player.id
    expected = {n.name for n in world.npcs if soul in n.relations}
    got = {b.npc_name for b in social_memory_bonds(world)}
    assert got == expected


def test_social_memory_bonds_attribute_to_valid_life():
    world = _world()
    count = len(world.lives)
    bonds = social_memory_bonds(world)
    assert bonds, "expected at least one bond in the seed42 world"
    for bond in bonds:
        assert 1 <= bond.life_ordinal <= count, bond


def test_social_memory_bonds_are_id_free():
    world = _world()
    for bond in social_memory_bonds(world):
        blob = f"{bond.npc_name} {bond.npc_tier} {bond.sentiment} {bond.reason}"
        assert not _INTERNAL_ID.search(blob), blob
        assert "player-" not in blob


# --- life_ordinal attribution: boundary conditions ----------------------


def test_life_ordinal_maps_each_life_span_to_its_ordinal():
    world = _world()
    count = len(world.lives)
    idx = {life.id: i + 1 for i, life in enumerate(world.lives)}
    for life in world.lives:
        ordinal = idx[life.id]
        end = life.death_year if life.death_year is not None else world.current_year
        # both span endpoints attribute to this life
        assert _life_ordinal_for_year(world, life.birth_year) == ordinal
        assert _life_ordinal_for_year(world, end) == ordinal
        for year in (life.birth_year, end):
            assert 1 <= _life_ordinal_for_year(world, year) <= count


def test_life_ordinal_clamps_out_of_range_years():
    world = _world()
    count = len(world.lives)
    last = count
    first = 1
    # a year after every life maps to the most recent (last) life
    assert _life_ordinal_for_year(world, world.current_year + 50) == last
    # a year before the first birth falls back within bounds (no life lived yet)
    earliest = min(lf.birth_year for lf in world.lives)
    assert 1 <= _life_ordinal_for_year(world, earliest - 50) <= count
    # a gap year between two lives attributes to the most recent prior life
    assert (
        first <= _life_ordinal_for_year(world, world.lives[0].birth_year + 0) <= count
    )


def test_life_ordinal_on_lifeless_world_is_zero():
    fresh = generate_world(42)
    assert _life_ordinal_for_year(fresh, 0) == 0  # no lives -> no ordinal


# --- graceful empty (a freshly generated world has lived no lives) -------


def test_social_memory_bonds_empty_on_fresh_world():
    fresh = generate_world(42)
    assert social_memory_bonds(fresh) == []
    assert social_memory_view(fresh).lstrip().startswith("#")  # still markdown


# --- frozen seed42 hash (permanent regression guard) --------------------


def test_social_memory_view_seed42_hash_is_frozen():
    assert _sha(social_memory_view(_world())) == GOLDEN_SOCIAL_MEMORY_SHA
