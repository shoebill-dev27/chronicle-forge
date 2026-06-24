"""P9-3 Replay — re-execute a Recipe into the world and regenerate its story.

Replay reuses the unchanged P8 engine: ``run_human_world`` over a scripted reader
of the recipe's inputs, with a caller-supplied writer, so the transcript is
*regenerated* (never stored). The two replay-time gates (engine version, then
max_year) are shared with P9-1 load via ``_ensure_replayable``; a schema-invalid
recipe file surfaces as :class:`InvalidRecipe`. Every failure refuses — no
fallback, no approximate world.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Callable, Tuple, Union

from pydantic import ValidationError

from ..models import World
from ..play.human import scripted_reader
from ..play.session import run_human_world
from .load import _ensure_replayable
from .save import read_recipe
from .schema import Recipe

PathLike = Union[str, Path]
Writer = Callable[[str], None]


class InvalidRecipe(Exception):
    """A recipe file that fails the pinned schema (bad ``mode``, non-string
    ``inputs``, inputs under ``mode=auto``, or extra/missing keys). Replay
    refuses to run it rather than guessing."""


def replay(recipe: Recipe, *, writer: Writer) -> World:
    """Reconstruct the world a recipe describes, emitting its regenerated
    transcript to ``writer``. Gates engine version and max_year first; refuses
    on mismatch (no fallback)."""
    _ensure_replayable(recipe)
    return run_human_world(
        recipe.seed,
        reader=scripted_reader(recipe.inputs),
        writer=writer,
        social_memory=recipe.social_memory,
    )


def replay_transcript(recipe: Recipe) -> Tuple[World, str]:
    """Replay into a buffer and return ``(world, transcript)``. The transcript
    is regenerated and byte-deterministic for a given recipe."""
    buffer = StringIO()
    world = replay(recipe, writer=buffer.write)
    return world, buffer.getvalue()


def replay_file(path: PathLike, *, writer: Writer) -> World:
    """Read a recipe from disk and replay it. A schema-invalid file raises
    :class:`InvalidRecipe` (the closed 'invalid mode' / 'invalid inputs'
    failures); the version/max_year gates raise as in :func:`replay`."""
    try:
        recipe = read_recipe(path)
    except ValidationError as exc:
        raise InvalidRecipe(str(exc)) from exc
    return replay(recipe, writer=writer)
