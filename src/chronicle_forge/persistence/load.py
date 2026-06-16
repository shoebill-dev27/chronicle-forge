"""Recipe loading and replay.

``replay_recipe`` is the in-memory reconstruction primitive: it gates the recipe
(engine version, then max_year) and, if accepted, re-executes the **unchanged**
P8 engine — ``run_human_world`` driven by a scripted reader over the recipe's
inputs and a silent writer — to reproduce the world byte-for-byte. ``load_recipe``
is the file entrypoint: read, then replay.

Both gates refuse rather than fall back: a recipe from another engine version, or
one whose ``max_year`` the current engine cannot honor (``run_human_world`` does
not expose it), raises instead of silently producing a divergent world.
Determinism is preferred over convenience.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .. import config
from ..models import World
from ..play.human import null_writer, scripted_reader
from ..play.session import run_human_world
from .save import read_recipe
from .schema import EngineVersionMismatch, Recipe, UnsupportedRecipe
from .version import ENGINE_VERSION

PathLike = Union[str, Path]


def replay_recipe(recipe: Recipe) -> World:
    """Reconstruct the world a recipe describes by re-running the engine. Gates
    engine version and max_year first; refuses on mismatch (no fallback)."""
    if recipe.engine_version != ENGINE_VERSION:
        raise EngineVersionMismatch(
            f"recipe engine {recipe.engine_version!r} != current "
            f"{ENGINE_VERSION!r}; replay refused"
        )
    if recipe.max_year != config.DEV_WORLD_MAX_YEARS:
        raise UnsupportedRecipe(
            f"max_year {recipe.max_year} is unsupported "
            f"(engine default {config.DEV_WORLD_MAX_YEARS}); "
            "run_human_world does not expose max_year"
        )
    return run_human_world(
        recipe.seed,
        reader=scripted_reader(recipe.inputs),
        writer=null_writer,
    )


def load_recipe(path: PathLike) -> World:
    """Read a recipe from disk and reconstruct its world (read → replay)."""
    return replay_recipe(read_recipe(path))
