"""Recipe construction and writing.

``build_recipe`` stamps the current ``ENGINE_VERSION`` onto a run description;
``save_recipe`` writes it as fixed-schema JSON (sorted keys, fixed indent) so two
saves of the same recipe are byte-identical and diffs stay clean; ``read_recipe``
parses it back under the pinned schema (unknown keys / wrong types are rejected).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Union

from .schema import Mode, Recipe
from .version import ENGINE_VERSION

PathLike = Union[str, Path]


def build_recipe(
    *, seed: int, max_year: int, mode: Mode, inputs: Sequence[str]
) -> Recipe:
    """A Recipe stamped with the current engine version."""
    return Recipe(
        engine_version=ENGINE_VERSION,
        seed=seed,
        max_year=max_year,
        mode=mode,
        inputs=list(inputs),
    )


def save_recipe(recipe: Recipe, path: PathLike) -> None:
    """Write ``recipe`` as deterministic, fixed-schema JSON."""
    text = json.dumps(recipe.model_dump(), sort_keys=True, indent=2) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def read_recipe(path: PathLike) -> Recipe:
    """Parse a Recipe from disk under the pinned schema (no version gate here —
    that is ``load_recipe``'s job)."""
    return Recipe.model_validate_json(Path(path).read_text(encoding="utf-8"))
