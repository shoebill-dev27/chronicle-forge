"""P9-1 Persistent History — Save/Load.

A run is persisted as a :class:`Recipe` (seed + max_year + mode + ordered
inputs) and reconstructed by re-executing the deterministic engine. The recipe
is canonical; ``engine_version`` gates replay so a recipe is never reconstructed
under an engine that would diverge. Isolated from ``models.py`` and P6/P7/P8,
which it only reuses, never modifies.
"""

from __future__ import annotations

from .load import load_recipe, replay_recipe
from .record import recording_reader
from .replay import InvalidRecipe, replay, replay_file, replay_transcript
from .save import build_recipe, read_recipe, save_recipe
from .schema import EngineVersionMismatch, Recipe, UnsupportedRecipe
from .version import ENGINE_VERSION

__all__ = [
    "ENGINE_VERSION",
    "Recipe",
    "EngineVersionMismatch",
    "UnsupportedRecipe",
    "InvalidRecipe",
    "build_recipe",
    "save_recipe",
    "read_recipe",
    "load_recipe",
    "replay_recipe",
    "replay",
    "replay_transcript",
    "replay_file",
    "recording_reader",
]
