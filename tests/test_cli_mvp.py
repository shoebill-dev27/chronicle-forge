"""P16 MVP Cohesion — installable CLI behaviour contract — RED.

``chronicle-forge {play, explore, share}`` is a **thin wrapper** over the P15
Application Layer (``chronicle_forge.app``) — the only integration boundary. The CLI
parses argv, calls ``app``, renders, and returns an exit code; it holds no game logic,
draws no RNG, and (per the existing ``play/__main__`` contract) keeps **stdout a clean
transcript/chronicle** while human status goes to stderr.

Everything here is pinned by behaviour (exit code + stdout/stderr + artifacts), so the
contract holds regardless of the GREEN internals (e.g. ``app.share_file`` vs a
read_recipe adapter). ``chronicle_forge.cli`` is imported **inside each test body** so a
missing module fails the P16 tests alone (clean ``ModuleNotFoundError`` RED) without
perturbing collection of the existing 426-test suite. Recipe fixtures use the existing
``persistence.build_recipe`` (no app/cli import at module top).
"""

from __future__ import annotations

import hashlib
import re

import pytest

from chronicle_forge import config
from chronicle_forge.persistence import build_recipe, save_recipe

MAX_YEAR = config.DEV_WORLD_MAX_YEARS
GOLDEN_TRANSCRIPT_SHA = "98bea8622c686d8e"  # `play --seed 42 --auto` stdout
GOLDEN_CHRONICLE_SHA = "aa4c67a416178e92"  # explore --format json (seed42)
_ID_RE = re.compile(r"[a-z]+-\d{4}")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _seed42_recipe_file(tmp_path):
    """A saved seed42 auto recipe — built via existing persistence, no app/cli."""
    path = tmp_path / "seed42.recipe"
    save_recipe(build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[]), path)
    return path


# --- surface ------------------------------------------------------------


def test_cli_exposes_main():
    import chronicle_forge.cli as cli

    assert callable(cli.main)


def test_cli_version_prints_package_version(capsys):
    import chronicle_forge.cli as cli
    from chronicle_forge import __version__

    rc = cli.main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert __version__ in out


# --- play ---------------------------------------------------------------


def test_play_auto_save_writes_replayable_recipe(tmp_path):
    import chronicle_forge.cli as cli
    from chronicle_forge.persistence import read_recipe, replay_transcript

    recipe_path = tmp_path / "run.recipe"
    rc = cli.main(["play", "--seed", "42", "--auto", "--save", str(recipe_path)])
    assert rc == 0
    assert recipe_path.exists()
    _world, transcript = replay_transcript(read_recipe(recipe_path))
    assert _sha(transcript) == GOLDEN_TRANSCRIPT_SHA


def test_play_auto_stdout_is_clean_transcript(capsys):
    import chronicle_forge.cli as cli

    rc = cli.main(["play", "--seed", "42", "--auto"])
    out = capsys.readouterr().out
    assert rc == 0
    assert _sha(out) == GOLDEN_TRANSCRIPT_SHA


def test_play_replay_reproduces_transcript(tmp_path, capsys):
    import chronicle_forge.cli as cli

    recipe_path = _seed42_recipe_file(tmp_path)
    rc = cli.main(["play", "--replay", str(recipe_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert _sha(out) == GOLDEN_TRANSCRIPT_SHA


def test_play_without_auto_or_script_is_refused(tmp_path):
    """Interactive (live-stdin) play is deferred in P16: a bare invocation refuses
    rather than blocking on stdin (SystemExit from argparse, or a non-zero return)."""
    import chronicle_forge.cli as cli

    try:
        rc = cli.main(["play", "--seed", "42"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        assert rc != 0


# --- explore ------------------------------------------------------------


def test_explore_json_is_chronicle_json(tmp_path, capsys):
    import chronicle_forge.cli as cli

    recipe_path = _seed42_recipe_file(tmp_path)
    rc = cli.main(["explore", str(recipe_path), "--format", "json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert _sha(out.strip()) == GOLDEN_CHRONICLE_SHA


def test_explore_markdown_is_titled_and_id_free(tmp_path, capsys):
    import chronicle_forge.cli as cli

    recipe_path = _seed42_recipe_file(tmp_path)
    rc = cli.main(["explore", str(recipe_path), "--format", "md"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.startswith("# ")
    assert _ID_RE.search(out) is None


# --- share --------------------------------------------------------------


def test_share_writes_artifact_and_prints_replay_command(tmp_path, capsys):
    import chronicle_forge.cli as cli

    recipe_path = _seed42_recipe_file(tmp_path)
    export = tmp_path / "run.md"
    rc = cli.main(["share", str(recipe_path), "--export", str(export)])
    out = capsys.readouterr().out
    assert rc == 0
    assert export.exists()
    assert "--replay" in out


# --- exit-code contract -------------------------------------------------


def test_unknown_command_is_a_usage_error():
    import chronicle_forge.cli as cli

    with pytest.raises(SystemExit) as exc:
        cli.main(["frobnicate"])
    assert exc.value.code != 0
