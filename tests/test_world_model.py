"""P11 Structured World Read-Model contract — test-first (RED until
reporting/world_model.py).

The read-model is the *data boundary*: a pure ``World -> WorldView`` projection
plus its canonical JSON encoding, shaped for a non-text client (low-poly 3D / web)
to deserialize. It unifies the P10 seams (``Section``, ``SocialBond``) and
introduces ``places`` — the primary 3D anchor the Observatory deferred. It mutates
nothing, takes no engine flag, leaks no internal id (the P8 lesson; ``source_seed``
present in ``heritage_rows`` is dropped at the boundary), and is deterministic.
Nothing here changes the world, P6/P7/P8/P9-*, or the frozen P10 Observatory /
Social Memory views, or the seed42 golden.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.enums import LocationType
from chronicle_forge.reporting._data import heritage_rows
from chronicle_forge.reporting.social_memory import social_memory_bonds
from chronicle_forge.reporting.world_model import (
    WorldView,
    world_model,
    world_model_json,
)
from chronicle_forge.worldgen import generate_world

# Frozen at GREEN: the read-model's permanent seed42 regression guard.
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"

# The soul id (player-0000) is itself internal — note the extra ``player`` alt.
_INTERNAL_ID = re.compile(r"\b(seed|life|npc|node|loc|fac|her|player)-\d")


def _world():
    return simulate_world(42, mode="opportunity")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# --- shape: typed, serializable, read-only, deterministic ---------------


def test_world_model_returns_worldview():
    assert isinstance(world_model(_world()), WorldView)


def test_world_model_json_is_valid_json():
    parsed = json.loads(world_model_json(_world()))
    assert isinstance(parsed, dict)
    assert "places" in parsed and "schema_version" in parsed


def test_world_model_json_is_read_only():
    world = _world()
    before = world.model_dump_json()
    world_model_json(world)
    assert world.model_dump_json() == before


def test_world_model_json_is_deterministic():
    world = _world()
    assert world_model_json(world) == world_model_json(world)


# --- id-free boundary (the P8 lesson, structurally enforced) ------------


def test_world_model_no_internal_ids():
    out = world_model_json(_world())
    assert not _INTERNAL_ID.search(out), out
    assert "player-" not in out
    assert "legacy:" not in out


def test_world_model_heritage_has_no_source_seed():
    world = _world()
    out = world_model_json(world)
    assert "source_seed" not in out
    for h in world_model(world).heritage:
        assert not hasattr(h, "source_seed")


# --- content: faithful, id-free projection of the finished world --------


def test_world_model_overview_scope():
    world = _world()
    ov = world_model(world).overview
    assert ov.current_year == world.current_year
    assert ov.life_count == len(world.lives)
    assert ov.place  # a humanised place name, not an id
    assert not _INTERNAL_ID.search(ov.place)


def test_world_model_lives_one_per_life_ordered():
    world = _world()
    lives = world_model(world).lives
    assert len(lives) == len(world.lives)
    assert [lv.ordinal for lv in lives] == list(range(1, len(world.lives) + 1))


def test_world_model_heritage_matches_rows():
    world = _world()
    rows = heritage_rows(world)
    got = world_model(world).heritage
    assert len(got) == len(rows)
    assert {h.name for h in got} == {r["name"] for r in rows}


def test_world_model_bonds_match_social_memory():
    world = _world()
    bonds = social_memory_bonds(world)
    got = world_model(world).bonds
    assert [
        (b.npc_name, b.npc_tier, b.life_ordinal, b.affinity, b.sentiment, b.reason)
        for b in got
    ] == [
        (b.npc_name, b.npc_tier, b.life_ordinal, b.affinity, b.sentiment, b.reason)
        for b in bonds
    ]


# --- places: the new primary 3D anchor ----------------------------------


def test_world_model_places_cover_locations():
    world = _world()
    places = world_model(world).places
    assert len(places) == len(world.locations)
    names = {p.name for p in places}
    assert names == {loc.name for loc in world.locations}
    kinds = {t.value for t in LocationType}
    for p in places:
        assert p.location_type in kinds, p.location_type
    assert sum(1 for p in places if p.is_origin) == 1  # one founding village


def test_world_model_factions_are_id_free_scalars():
    world = _world()
    factions = world_model(world).factions
    assert len(factions) == len(world.factions)
    for f in factions:
        assert not hasattr(f, "relations")
        assert isinstance(f.power, int)
        assert not _INTERNAL_ID.search(f.name)


# --- client-deserialization contract ------------------------------------


def test_world_model_round_trips():
    world = _world()
    blob = world_model_json(world)
    assert WorldView.model_validate_json(blob) == world_model(world)


def test_world_model_json_round_trip_is_stable():
    # world_model_json -> model_validate_json -> model_dump_json reproduces bytes.
    world = _world()
    blob = world_model_json(world)
    restored = WorldView.model_validate_json(blob)
    assert restored.model_dump_json() == blob


def test_world_model_views_are_immutable():
    view = world_model(_world())
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        view.schema_version = "tampered"
    with pytest.raises(pydantic.ValidationError):
        view.places[0].name = "tampered"


# --- graceful empty (a freshly generated world has lived no lives) ------


def test_world_model_on_fresh_world():
    fresh = generate_world(42)
    view = world_model(fresh)
    assert view.lives == []
    assert view.bonds == []
    assert view.places  # the map exists before any life is lived


# --- frozen seed42 hash (permanent regression guard) --------------------


def test_world_model_seed42_hash_is_frozen():
    assert _sha(world_model_json(_world())) == GOLDEN_WORLD_MODEL_SHA
