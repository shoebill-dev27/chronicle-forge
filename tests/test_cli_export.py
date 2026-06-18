"""P9-2 CLI --export wiring (additive on the play CLI).

--export writes a transcript artifact (format by extension) alongside a normal
play (--seed) or a replay (--replay); the existing stdout transcript is
unchanged. The recorded/loaded recipe is what gets exported.
"""

from __future__ import annotations

import hashlib

import pytest

from chronicle_forge import config
from chronicle_forge.play.__main__ import main
from chronicle_forge.persistence import (
    build_recipe,
    export_transcript,
    read_recipe,
    save_recipe,
)

MAX_YEAR = config.DEV_WORLD_MAX_YEARS
GOLDEN_TRANSCRIPT_SHA = "98bea8622c686d8e"


def _seed42_recipe():
    return build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def test_cli_export_from_replay(tmp_path, capsys):
    rp = tmp_path / "r.json"
    save_recipe(_seed42_recipe(), rp)
    out = tmp_path / "story.md"
    main(["--replay", str(rp), "--export", str(out)])
    stdout = capsys.readouterr().out
    assert _sha(stdout) == GOLDEN_TRANSCRIPT_SHA  # stdout transcript unchanged
    artifact, _ = export_transcript(_seed42_recipe(), fmt="md")
    assert out.read_text(encoding="utf-8") == artifact


def test_cli_export_from_seed(tmp_path, capsys):
    out = tmp_path / "story.json"
    main(["--seed", "42", "--auto", "--export", str(out)])
    stdout = capsys.readouterr().out
    assert _sha(stdout) == GOLDEN_TRANSCRIPT_SHA  # stdout unchanged
    artifact, _ = export_transcript(_seed42_recipe(), fmt="json")
    assert out.read_text(encoding="utf-8") == artifact


def test_cli_export_infers_format_by_extension(tmp_path, capsys):
    for ext, fmt in ((".txt", "txt"), (".md", "md"), (".json", "json")):
        out = tmp_path / f"story{ext}"
        main(["--seed", "42", "--auto", "--export", str(out)])
        capsys.readouterr()
        artifact, _ = export_transcript(_seed42_recipe(), fmt=fmt)
        assert out.read_text(encoding="utf-8") == artifact, ext


def test_cli_export_and_save_coexist(tmp_path, capsys):
    recipe_path = tmp_path / "r.json"
    out = tmp_path / "story.md"
    main(
        [
            "--seed",
            "42",
            "--auto",
            "--save",
            str(recipe_path),
            "--export",
            str(out),
        ]
    )
    capsys.readouterr()
    assert read_recipe(recipe_path).seed == 42
    artifact, _ = export_transcript(_seed42_recipe(), fmt="md")
    assert out.read_text(encoding="utf-8") == artifact
