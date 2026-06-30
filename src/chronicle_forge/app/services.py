"""P15 Vertical Slice — Application Services (the one-way path, composition only).

These functions own the ``play → save → explore → share`` use case by composing the
existing layers — P8 play, P9 persistence, and the P10–P14 reporting lenses — and
nothing else. They add **no truth**: ``explore`` replays a saved recipe to the very
world the lens goldens are pinned to and composes the lenses; ``share`` re-emits the
byte-deterministic transcript. There is no shared ``World`` to mutate (each call
replays a fresh one), so read-only and determinism are structural.

This module writes no CLI: it is the seam the CLI (a later phase) will call. It draws
no RNG and reads no clock — determinism lives in the seed/recipe alone.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

from ..config import DEV_WORLD_MAX_YEARS
from ..models import World
from ..persistence import (
    Recipe,
    build_recipe,
    read_recipe,
    recording_reader,
    replay_transcript,
    write_export,
)
from ..play.adapter import build_reader, play_and_record
from ..play.session import run_human_world
from ..reporting._data import place
from ..reporting.character import character_markdown, character_model
from ..reporting.heritage_explorer import heritage_explorer
from ..reporting.narrative import narrative_markdown, narrative_model
from ..reporting.timeline import timeline_markdown, timeline_model
from ..reporting.world_model import world_model
from .contracts import (
    SCHEMA_VERSION,
    ChronicleView,
    PlayOutcome,
    PlayRequest,
    ShareRequest,
    ShareResult,
)

PathLike = Union[str, Path]


# --- play (reuse P8) ----------------------------------------------------


def _recipe_mode(request: PlayRequest) -> str:
    """The recipe's input-source mode: script wins, then auto (EOF), else human."""
    if request.script_lines is not None:
        return "script"
    return "auto" if request.auto else "human"


def _grow(request: PlayRequest, writer) -> Tuple[World, Recipe]:
    """Grow a world and capture its replayable recipe. The common path delegates to
    ``play.adapter.play_and_record``; ``social_memory`` (which the adapter does not
    forward) composes the same existing primitives with the flag set."""
    mode = _recipe_mode(request)
    if not request.social_memory:
        return play_and_record(
            seed=request.seed,
            auto=request.auto,
            script_lines=request.script_lines,
            mode=mode,
            writer=writer,
        )
    base = build_reader(auto=request.auto, script_lines=request.script_lines)
    if base is None:
        raise ValueError("social_memory play requires auto or script input")
    reader, captured = recording_reader(base)
    world = run_human_world(
        request.seed, reader=reader, writer=writer, social_memory=True
    )
    recipe = build_recipe(
        seed=request.seed,
        max_year=DEV_WORLD_MAX_YEARS,
        mode=mode,
        inputs=captured,
        social_memory=True,
    )
    return world, recipe


def play(request: PlayRequest) -> PlayOutcome:
    """Grow (or auto/script-drive) a world and capture its canonical Recipe, the
    regenerated transcript, and id-free outcome facts. The ``World`` stays internal."""
    buffer: list[str] = []
    world, recipe = _grow(request, buffer.append)
    return PlayOutcome(
        recipe=recipe,
        transcript="".join(buffer),
        ending_class=world.ending_class,
        life_count=len(world.lives),
        span=world.current_year,
    )


# --- explore (the new seam: recipe -> world -> P10–P14 lenses) ----------


def _compose(world: World) -> ChronicleView:
    """Compose the P10–P14 lenses over a reconstructed world. No new truth: each
    sub-view is the existing frozen lens builder's output."""
    return ChronicleView(
        schema_version=SCHEMA_VERSION,
        place=place(world),
        span=world.current_year,
        ending_class=world.ending_class,
        world=world_model(world),
        timeline=timeline_model(world),
        narrative=narrative_model(world),
        characters=character_model(world),
        heritage_markdown=heritage_explorer(world),
    )


def explore(recipe: Recipe) -> ChronicleView:
    """Reconstruct the world a recipe describes (P9 version-gated replay) and compose
    the P10–P14 lenses into one id-free ``ChronicleView``. Read-only and deterministic;
    the recipe is not mutated."""
    world, _transcript = replay_transcript(recipe)
    return _compose(world)


def explore_file(path: PathLike) -> ChronicleView:
    """``read_recipe(path)`` then :func:`explore`. A schema-invalid file surfaces as
    the persistence layer's error (no guessing)."""
    return explore(read_recipe(path))


def chronicle_json(recipe: Recipe) -> str:
    """Canonical JSON of the ``ChronicleView`` — the client contract and the basis of
    the frozen seed42 chronicle hash."""
    return explore(recipe).model_dump_json()


def chronicle_markdown(view: ChronicleView) -> str:
    """Render a ``ChronicleView`` as Markdown. A **pure renderer**: it reads only the
    view (never the world/recipe) and returns deterministic, id-free prose."""
    tail = f", {view.ending_class}" if view.ending_class else ""
    lines = [f"# Chronicle — {view.place}", "", f"> {view.span} years{tail}.", ""]
    lines.append(timeline_markdown(view.timeline))
    lines.append("")
    lines.append(narrative_markdown(view.narrative))
    lines.append("")
    lines.append(character_markdown(view.characters))
    lines.append("")
    lines.append(view.heritage_markdown.rstrip())
    return "\n".join(lines).rstrip() + "\n"


# --- share (reuse P9) ---------------------------------------------------


def share(request: ShareRequest) -> ShareResult:
    """Emit the byte-deterministic transcript and the command that reproduces the run.
    The recipe **is** the shareable save; ``export_path`` additionally writes an
    artifact (format inferred from the extension)."""
    _world, transcript = replay_transcript(request.recipe)
    if request.export_path is not None:
        write_export(request.recipe, request.export_path)
    return ShareResult(
        recipe=request.recipe,
        transcript=transcript,
        export_path=request.export_path,
        reproducible_command="chronicle-forge play --replay <recipe>",
    )
