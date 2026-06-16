"""The Recipe — the canonical, replayable save for a run.

A Recipe holds only what determines a run: the engine version it was recorded
under, the ``seed``, the ``max_year``, the play ``mode``, and the exact ordered
``inputs`` the chooser's reader yielded. Because the engine is byte-deterministic
from ``seed`` + ``inputs`` (the P8 seed42 golden identity), this small record
reconstructs the world exactly — the recipe *is* the save. Nothing here touches
``models.py``; the Recipe is an isolated persistence schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Mode = Literal["auto", "human", "script"]


class EngineVersionMismatch(Exception):
    """A recipe was recorded under a different engine version; because the
    snapshot-free recipe can only be reconstructed by re-running the current
    engine, replay is refused rather than silently producing a divergent world."""


class UnsupportedRecipe(Exception):
    """A recipe the current engine cannot faithfully reconstruct — e.g. a
    non-default ``max_year``, which ``run_human_world`` does not expose. Refused
    rather than reconstructed at the wrong horizon (determinism over convenience)."""


class Recipe(BaseModel):
    """A replayable run description. ``inputs`` is one reader line per entry, in
    order (exactly what a ``--script`` file contains); when exhausted, remaining
    gate asks are entrusted to the world, so ``mode == "auto"`` ⇔ ``inputs == []``
    ⇔ a full opportunity-mode run."""

    model_config = ConfigDict(extra="forbid")  # the on-disk schema is pinned

    engine_version: str
    seed: int
    max_year: int
    mode: Mode
    inputs: list[str] = []

    @model_validator(mode="after")
    def _auto_implies_no_inputs(self) -> "Recipe":
        if self.mode == "auto" and self.inputs:
            raise ValueError("mode 'auto' must have empty inputs")
        return self
