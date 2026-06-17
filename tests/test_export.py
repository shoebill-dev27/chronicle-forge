"""P9-2 Transcript Export contract — test-first (RED until persistence/export.py
exists).

Export writes a durable, readable artifact (txt / md / json) that stores the
transcript body and embeds the Recipe as a reference, plus metadata (seed,
engine_version, recipe/transcript/world hashes). The stored transcript is a
non-authoritative cache: it must re-validate against regeneration from the
embedded recipe. Nothing here changes P6/P7/P8/P9-1/P9-3 or the seed42 golden.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from chronicle_forge import config
from chronicle_forge.persistence import (
    ENGINE_VERSION,
    ExportMetadata,
    Recipe,
    build_recipe,
    export_transcript,
    replay_transcript,
    write_export,
)

MAX_YEAR = config.DEV_WORLD_MAX_YEARS


def _seed42_recipe():
    return build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# --- metadata -----------------------------------------------------------


def test_export_metadata_fields():
    _, meta = export_transcript(_seed42_recipe(), fmt="md")
    assert isinstance(meta, ExportMetadata)
    assert meta.seed == 42
    assert meta.engine_version == ENGINE_VERSION
    assert meta.world_hash.startswith("e62d8f2c")  # golden world
    assert meta.transcript_hash.startswith("98bea862")  # golden transcript
    assert len(meta.recipe_hash) == 64  # full sha256 hex


# --- formats ------------------------------------------------------------


def test_export_txt_contains_transcript_and_reference():
    artifact, meta = export_transcript(_seed42_recipe(), fmt="txt")
    _, transcript = replay_transcript(_seed42_recipe())
    assert transcript in artifact
    assert meta.recipe_hash in artifact  # recipe referenced by hash


def test_export_md_has_metadata_and_transcript():
    artifact, meta = export_transcript(_seed42_recipe(), fmt="md")
    _, transcript = replay_transcript(_seed42_recipe())
    assert artifact.lstrip().startswith("#")  # markdown header
    assert meta.world_hash in artifact
    assert transcript in artifact


def test_export_json_embeds_recipe_and_transcript():
    artifact, _ = export_transcript(_seed42_recipe(), fmt="json")
    obj = json.loads(artifact)
    assert set(obj.keys()) == {"metadata", "recipe", "transcript"}
    # the embedded recipe re-validates to an equal Recipe (artifact is replayable)
    assert Recipe.model_validate(obj["recipe"]) == _seed42_recipe()
    _, transcript = replay_transcript(_seed42_recipe())
    assert obj["transcript"] == transcript
    assert obj["metadata"]["transcript_hash"] == _sha(transcript)


# --- determinism --------------------------------------------------------


def test_export_is_deterministic():
    for fmt in ("txt", "md", "json"):
        a, _ = export_transcript(_seed42_recipe(), fmt=fmt)
        b, _ = export_transcript(_seed42_recipe(), fmt=fmt)
        assert a == b, fmt


# --- stored transcript is a re-validatable cache ------------------------


def test_export_transcript_hash_matches_regeneration():
    artifact, meta = export_transcript(_seed42_recipe(), fmt="json")
    obj = json.loads(artifact)
    # authority = the recipe: regenerate from the embedded recipe and confirm the
    # stored cache agrees with regeneration and the recorded hash.
    embedded = Recipe.model_validate(obj["recipe"])
    _, regenerated = replay_transcript(embedded)
    assert _sha(regenerated) == meta.transcript_hash
    assert obj["transcript"] == regenerated


# --- file writing -------------------------------------------------------


def test_write_export_infers_format(tmp_path):
    recipe = _seed42_recipe()
    for ext, fmt in ((".txt", "txt"), (".md", "md"), (".json", "json")):
        p = tmp_path / f"out{ext}"
        meta = write_export(recipe, p)
        assert isinstance(meta, ExportMetadata)
        artifact, _ = export_transcript(recipe, fmt=fmt)
        assert p.read_text(encoding="utf-8") == artifact


def test_write_export_rejects_unknown_extension(tmp_path):
    with pytest.raises(ValueError):
        write_export(_seed42_recipe(), tmp_path / "out.bin")
