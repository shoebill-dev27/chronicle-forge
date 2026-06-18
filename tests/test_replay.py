"""P9-3 Replay contract — test-first (RED until persistence/replay.py + record.py
and the additive --replay/--save CLI wiring exist).

Replay re-executes a Recipe into the world AND regenerates its transcript,
byte-for-byte. The transcript is regenerated, never persisted. Failures are a
closed set (engine_version / max_year / invalid mode / invalid inputs) and refuse
rather than diverge. Nothing here changes P6/P7/P8 behavior or the seed42 golden.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from chronicle_forge import config
from chronicle_forge.play.__main__ import main
from chronicle_forge.play.human import null_writer, scripted_reader
from chronicle_forge.play.session import run_human_world
from chronicle_forge.persistence import (
    ENGINE_VERSION,
    EngineVersionMismatch,
    InvalidRecipe,
    Recipe,
    UnsupportedRecipe,
    build_recipe,
    read_recipe,
    replay,
    replay_file,
    replay_transcript,
    save_recipe,
)

MAX_YEAR = config.DEV_WORLD_MAX_YEARS
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"  # simulate_world(42, "opportunity")
GOLDEN_TRANSCRIPT_SHA = "98bea8622c686d8e"  # `play --seed 42 --auto` stdout


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _world_sha(world) -> str:
    return _sha(world.model_dump_json())


def _live_transcript(seed, inputs):
    buf: list[str] = []
    world = run_human_world(seed, reader=scripted_reader(inputs), writer=buf.append)
    return world, "".join(buf)


# --- transcript regeneration (canonical, deterministic) -----------------


def test_replay_transcript_is_deterministic():
    r = build_recipe(seed=123, max_year=MAX_YEAR, mode="script", inputs=["1"] * 50)
    w1, t1 = replay_transcript(r)
    w2, t2 = replay_transcript(r)
    assert w1.model_dump_json() == w2.model_dump_json()
    assert t1 == t2


def test_replay_transcript_matches_live_run():
    inputs = ["1"] * 50
    r = build_recipe(seed=123, max_year=MAX_YEAR, mode="script", inputs=inputs)
    world, transcript = replay_transcript(r)
    live_world, live_transcript = _live_transcript(123, inputs)
    assert world.model_dump_json() == live_world.model_dump_json()
    assert transcript == live_transcript


def test_seed42_eof_replay_transcript_matches_golden():
    """PERMANENT: the seed42 EOF recipe regenerates the golden world AND the
    golden transcript."""
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    world, transcript = replay_transcript(r)
    assert _world_sha(world) == GOLDEN_WORLD_SHA
    assert _sha(transcript) == GOLDEN_TRANSCRIPT_SHA


# --- closed failure taxonomy (refuse, never diverge) --------------------


def test_replay_refuses_engine_version_mismatch():
    r = Recipe(
        engine_version="0.0.0-bogus",
        seed=42,
        max_year=MAX_YEAR,
        mode="auto",
        inputs=[],
    )
    with pytest.raises(EngineVersionMismatch):
        replay(r, writer=null_writer)


def test_replay_refuses_unsupported_max_year():
    r = build_recipe(seed=42, max_year=MAX_YEAR + 1, mode="auto", inputs=[])
    with pytest.raises(UnsupportedRecipe):
        replay(r, writer=null_writer)


def test_replay_file_rejects_invalid_mode(tmp_path):
    p = tmp_path / "bad_mode.json"
    p.write_text(
        json.dumps(
            {
                "engine_version": ENGINE_VERSION,
                "seed": 1,
                "max_year": MAX_YEAR,
                "mode": "god",
                "inputs": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(InvalidRecipe):
        replay_file(p, writer=null_writer)


def test_replay_file_rejects_invalid_inputs(tmp_path):
    p = tmp_path / "bad_inputs.json"
    p.write_text(
        json.dumps(
            {
                "engine_version": ENGINE_VERSION,
                "seed": 1,
                "max_year": MAX_YEAR,
                "mode": "script",
                "inputs": [1, 2],  # ints, not strings
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(InvalidRecipe):
        replay_file(p, writer=null_writer)


# --- CLI: --replay / --save ---------------------------------------------


def test_cli_replay_emits_transcript(tmp_path, capsys):
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    p = tmp_path / "r.json"
    save_recipe(r, p)
    main(["--replay", str(p)])
    out = capsys.readouterr().out
    _, transcript = replay_transcript(r)
    assert out == transcript


def test_cli_save_writes_loadable_recipe(tmp_path, capsys):
    p = tmp_path / "r.json"
    main(["--seed", "42", "--auto", "--save", str(p)])
    capsys.readouterr()  # drain the play transcript
    rec = read_recipe(p)
    assert rec.seed == 42 and rec.mode == "auto" and rec.inputs == []
    world, _ = replay_transcript(rec)
    assert _world_sha(world) == GOLDEN_WORLD_SHA


def test_cli_save_then_replay_roundtrip(tmp_path, capsys):
    script = tmp_path / "s.txt"
    script.write_text("1\n1\n1\n", encoding="utf-8")
    recipe_path = tmp_path / "r.json"
    main(["--seed", "123", "--script", str(script), "--save", str(recipe_path)])
    original = capsys.readouterr().out
    main(["--replay", str(recipe_path)])
    replayed = capsys.readouterr().out
    assert replayed == original


def test_cli_replay_and_seed_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main(["--replay", "x.json", "--seed", "1"])
