"""Reproducibility is a hard requirement (R3): same seed -> identical world."""

from __future__ import annotations

from chronicle_forge import generate_world


def test_same_seed_produces_identical_world():
    a = generate_world(seed=42)
    b = generate_world(seed=42)
    assert a.model_dump_json() == b.model_dump_json()


def test_different_seeds_diverge():
    a = generate_world(seed=42)
    b = generate_world(seed=43)
    assert a.model_dump_json() != b.model_dump_json()


def test_world_id_and_seed_are_recorded():
    w = generate_world(seed=7)
    assert w.seed == 7
    assert w.id == "world-7"


def test_ids_are_stable_sequential():
    w = generate_world(seed=1)
    # Locations are emitted first, in order.
    assert [loc.id for loc in w.locations][:2] == ["loc-0000", "loc-0001"]
    assert w.factions[0].id == "fac-0000"
    assert w.npcs[0].id == "npc-0000"
