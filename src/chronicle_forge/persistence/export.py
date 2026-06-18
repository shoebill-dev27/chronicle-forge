"""P9-2 Transcript Export — durable, readable run artifacts.

An export *stores* the transcript body and *embeds the Recipe* as a reference,
with metadata (seed, engine_version, and sha256 of the recipe, transcript, and
world). The stored transcript is a **non-authoritative cache**: the Recipe is the
only canon, and the artifact carries everything needed to regenerate the
transcript (`replay_transcript(embedded_recipe)`) and re-validate it against
``transcript_hash``. Three formats — txt (human), md (share/replay), json
(machine) — all byte-deterministic for a given recipe.

Read-only over P9-3: this module only consumes ``replay_transcript``; it changes
nothing in P6/P7/P8/P9-1/P9-3.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Optional, Tuple, Union

from pydantic import BaseModel

from .replay import replay_transcript
from .schema import Recipe

ExportFormat = Literal["txt", "md", "json"]
PathLike = Union[str, Path]

_EXT_FORMAT = {".txt": "txt", ".md": "md", ".json": "json"}


class ExportMetadata(BaseModel):
    """Provenance for an export artifact. All hashes are full sha256 hex."""

    seed: int
    engine_version: str
    recipe_hash: str
    transcript_hash: str
    world_hash: str


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _recipe_canonical(recipe: Recipe) -> str:
    """The canonical recipe form used for hashing — sorted, compact, so the hash
    is independent of on-disk indentation."""
    return json.dumps(recipe.model_dump(), sort_keys=True, separators=(",", ":"))


def _build_metadata(recipe: Recipe, world, transcript: str) -> ExportMetadata:
    return ExportMetadata(
        seed=recipe.seed,
        engine_version=recipe.engine_version,
        recipe_hash=_sha(_recipe_canonical(recipe)),
        transcript_hash=_sha(transcript),
        world_hash=_sha(world.model_dump_json()),
    )


def _render_txt(recipe: Recipe, meta: ExportMetadata, transcript: str) -> str:
    header = "\n".join(
        [
            f"seed: {meta.seed}",
            f"engine_version: {meta.engine_version}",
            f"recipe_hash: {meta.recipe_hash}",
            f"transcript_hash: {meta.transcript_hash}",
            f"world_hash: {meta.world_hash}",
        ]
    )
    return f"{header}\n\n{transcript}"


def _render_md(recipe: Recipe, meta: ExportMetadata, transcript: str) -> str:
    recipe_block = json.dumps(recipe.model_dump(), sort_keys=True, indent=2)
    return (
        "# Chronicle Forge — Transcript Export\n\n"
        f"- **seed:** {meta.seed}\n"
        f"- **engine_version:** {meta.engine_version}\n"
        f"- **recipe_hash:** `{meta.recipe_hash}`\n"
        f"- **transcript_hash:** `{meta.transcript_hash}`\n"
        f"- **world_hash:** `{meta.world_hash}`\n\n"
        "## Recipe (replayable)\n\n"
        f"```json\n{recipe_block}\n```\n\n"
        "---\n\n"
        f"{transcript}"
    )


def _render_json(recipe: Recipe, meta: ExportMetadata, transcript: str) -> str:
    payload = {
        "metadata": meta.model_dump(),
        "recipe": recipe.model_dump(),
        "transcript": transcript,
    }
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


_RENDERERS = {"txt": _render_txt, "md": _render_md, "json": _render_json}


def export_transcript(
    recipe: Recipe, *, fmt: ExportFormat = "md"
) -> Tuple[str, ExportMetadata]:
    """Regenerate the run and render an export artifact. Returns
    ``(artifact, metadata)``; byte-deterministic for a given recipe + format."""
    world, transcript = replay_transcript(recipe)
    meta = _build_metadata(recipe, world, transcript)
    return _RENDERERS[fmt](recipe, meta, transcript), meta


def write_export(
    recipe: Recipe, path: PathLike, *, fmt: Optional[ExportFormat] = None
) -> ExportMetadata:
    """Write an export artifact, inferring the format from the path extension
    (``.txt`` / ``.md`` / ``.json``) when ``fmt`` is not given."""
    path = Path(path)
    fmt = fmt or _EXT_FORMAT.get(path.suffix.lower())
    if fmt is None:
        raise ValueError(
            f"cannot infer export format from extension {path.suffix!r} "
            "(expected .txt, .md, or .json)"
        )
    artifact, meta = export_transcript(recipe, fmt=fmt)
    path.write_text(artifact, encoding="utf-8")
    return meta
