"""Recipe loading and replay — reproduction, not the save.

``replay_recipe`` re-executes the engine — ``run_human_world`` at the recipe's
``max_year``, driven by a scripted reader over the recipe's inputs and a silent
writer — to reproduce the world byte-for-byte. ``load_recipe`` is the file
entrypoint: read, then replay.

The one gate refuses rather than falls back: a recipe from another engine
version raises instead of silently producing a divergent world. The recipe's
``max_year`` is simply honored; it no longer defines the engine's time model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from ..models import World
from ..play.human import null_writer, scripted_reader
from ..play.session import run_human_world
from .save import read_recipe
from .schema import EngineVersionMismatch, Recipe
from .version import ENGINE_VERSION

PathLike = Union[str, Path]


def _ensure_replayable(recipe: Recipe) -> None:
    """The replay-time gate, shared by world reconstruction (load) and
    transcript replay (P9-3). Refuses rather than falls back: a recipe from
    another engine version raises instead of silently producing a divergent
    world."""
    if recipe.engine_version != ENGINE_VERSION:
        raise EngineVersionMismatch(
            f"recipe engine {recipe.engine_version!r} != current "
            f"{ENGINE_VERSION!r}; replay refused"
        )


def replay_recipe(recipe: Recipe) -> World:
    """Reconstruct the world a recipe describes by re-running the engine. Gates
    the engine version first; refuses on mismatch (no fallback)."""
    _ensure_replayable(recipe)
    return run_human_world(
        recipe.seed,
        reader=scripted_reader(recipe.inputs),
        writer=null_writer,
        social_memory=recipe.social_memory,
        max_year=recipe.max_year,
    )


def load_recipe(path: PathLike) -> World:
    """Read a recipe from disk and reconstruct its world (read → replay)."""
    return replay_recipe(read_recipe(path))
