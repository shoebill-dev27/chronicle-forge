"""P9-1 Save/Load contract — test-first (RED until persistence/ is implemented).

These tests pin the locked Recipe schema, the fixed on-disk JSON, the mandatory
engine_version gate, the honest max_year gate, and reconstruction determinism —
including the PERMANENT seed42 EOF replay regression guard. They reconstruct
worlds by reusing the unchanged P8 engine (run_human_world); nothing here edits
P6/P7/P8, models.py, or the seed42 golden assets.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from chronicle_forge import config
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.play.human import null_writer, scripted_reader
from chronicle_forge.play.session import run_human_world
from chronicle_forge.persistence import (
    ENGINE_VERSION,
    EngineVersionMismatch,
    Recipe,
    UnsupportedRecipe,
    build_recipe,
    load_recipe,
    read_recipe,
    replay_recipe,
    save_recipe,
)

MAX_YEAR = config.DEV_WORLD_MAX_YEARS  # 40
# first 16 hex of simulate_world(42, "opportunity").model_dump_json() — the P8
# golden world. Reconstructing the seed42 EOF recipe must reproduce it forever.
GOLDEN_SEED42_SHA = "e62d8f2cd24d2c72"


def _world_sha(world) -> str:
    return hashlib.sha256(world.model_dump_json().encode()).hexdigest()[:16]


def _live(seed, inputs):
    return run_human_world(seed, reader=scripted_reader(inputs), writer=null_writer)


# --- locked Recipe schema -----------------------------------------------


def test_recipe_locked_fields():
    r = Recipe(engine_version="x", seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    assert set(r.model_dump().keys()) == {
        "engine_version",
        "seed",
        "max_year",
        "mode",
        "inputs",
        "social_memory",
    }


def test_recipe_rejects_unknown_mode():
    with pytest.raises(Exception):
        Recipe(engine_version="x", seed=1, max_year=MAX_YEAR, mode="god", inputs=[])


def test_auto_mode_requires_empty_inputs():
    with pytest.raises(Exception):
        Recipe(engine_version="x", seed=1, max_year=MAX_YEAR, mode="auto", inputs=["1"])


def test_inputs_are_strings():
    r = build_recipe(seed=1, max_year=MAX_YEAR, mode="script", inputs=["1", "0", "2"])
    assert r.inputs == ["1", "0", "2"]
    assert all(isinstance(x, str) for x in r.inputs)


def test_build_recipe_stamps_current_engine_version():
    r = build_recipe(seed=7, max_year=MAX_YEAR, mode="auto", inputs=[])
    assert r.engine_version == ENGINE_VERSION


# --- fixed on-disk JSON schema ------------------------------------------


def test_save_read_roundtrip(tmp_path):
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    p = tmp_path / "run.json"
    save_recipe(r, p)
    assert read_recipe(p) == r


def test_saved_json_schema_is_fixed_and_deterministic(tmp_path):
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="script", inputs=["1", "0"])
    p1, p2 = tmp_path / "a.json", tmp_path / "b.json"
    save_recipe(r, p1)
    save_recipe(r, p2)
    b1, b2 = p1.read_bytes(), p2.read_bytes()
    assert b1 == b2  # deterministic bytes (sorted keys, fixed indent)
    obj = json.loads(b1)
    assert set(obj.keys()) == {
        "engine_version",
        "seed",
        "max_year",
        "mode",
        "inputs",
        "social_memory",
    }


# --- mandatory engine_version gate --------------------------------------


def test_load_rejects_engine_version_mismatch(tmp_path):
    r = Recipe(
        engine_version="0.0.0-bogus",
        seed=42,
        max_year=MAX_YEAR,
        mode="auto",
        inputs=[],
    )
    p = tmp_path / "old.json"
    save_recipe(r, p)
    with pytest.raises(EngineVersionMismatch):
        load_recipe(p)


def test_load_accepts_matching_engine_version(tmp_path):
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    p = tmp_path / "ok.json"
    save_recipe(r, p)
    world = load_recipe(p)
    assert world.seed == 42


# --- honest max_year gate ------------------------------------------------


def test_load_rejects_unsupported_max_year(tmp_path):
    r = build_recipe(seed=42, max_year=MAX_YEAR + 1, mode="auto", inputs=[])
    p = tmp_path / "future.json"
    save_recipe(r, p)
    with pytest.raises(UnsupportedRecipe):
        load_recipe(p)


# --- reconstruction determinism -----------------------------------------


def test_load_reconstructs_deterministically(tmp_path):
    r = build_recipe(seed=123, max_year=MAX_YEAR, mode="script", inputs=["1"] * 50)
    p = tmp_path / "r.json"
    save_recipe(r, p)
    w1, w2 = load_recipe(p), load_recipe(p)
    assert w1.model_dump_json() == w2.model_dump_json()


def test_acting_recipe_matches_live_run(tmp_path):
    inputs = ["1"] * 50
    r = build_recipe(seed=123, max_year=MAX_YEAR, mode="script", inputs=inputs)
    p = tmp_path / "r.json"
    save_recipe(r, p)
    reconstructed = load_recipe(p)
    live = _live(123, inputs)
    assert reconstructed.model_dump_json() == live.model_dump_json()


def test_replay_recipe_matches_load_recipe(tmp_path):
    # replay_recipe(recipe) is the in-memory reconstruction primitive;
    # load_recipe(path) == replay_recipe(read_recipe(path)).
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    p = tmp_path / "x.json"
    save_recipe(r, p)
    assert replay_recipe(r).model_dump_json() == load_recipe(p).model_dump_json()


def test_seed42_eof_replay_equals_golden(tmp_path):
    """PERMANENT REGRESSION: the seed42 EOF recipe must forever reconstruct the
    P8 golden world (sha e62d8f2c…)."""
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    p = tmp_path / "seed42.json"
    save_recipe(r, p)
    reconstructed = load_recipe(p)
    golden = simulate_world(42, mode="opportunity")
    assert reconstructed.model_dump_json() == golden.model_dump_json()
    assert _world_sha(reconstructed) == GOLDEN_SEED42_SHA
