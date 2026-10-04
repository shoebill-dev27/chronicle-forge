"""The Recipe — a reproduction record for a run.

A Recipe holds what re-executes a run: the engine version it was recorded
under, the ``seed``, the ``max_year``, the play ``mode``, and the exact ordered
``inputs`` the chooser's reader yielded. Because the engine is byte-deterministic
from ``seed`` + ``inputs``, this small record reproduces the world exactly under
the same engine version — which makes it the right tool for debugging, goldens
and bug reports. It is no longer the product's save: that role belongs to a
versioned world snapshot (not yet built), so play can resume without replaying
every input from year zero. Nothing here touches ``models.py``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Mode = Literal["auto", "human", "script"]
# Which player loop consumed the inputs. They are different languages — the
# juncture loop reads option numbers, the routine loop reads commands — so a
# recipe has to say which one wrote it or replay would feed one to the other.
Loop = Literal["juncture", "routine"]


class EngineVersionMismatch(Exception):
    """A recipe was recorded under a different engine version; because the
    snapshot-free recipe can only be reconstructed by re-running the current
    engine, replay is refused rather than silently producing a divergent world."""


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
    # P11-B Social Memory L2 flag. Additive and defaulted, so every recipe
    # written before L2 (no field) loads as ``False`` and replays byte-identically
    # under ``extra="forbid"``; ENGINE_VERSION is intentionally not bumped.
    social_memory: bool = False
    # Additive and defaulted, like ``social_memory`` above: every recipe written
    # before the routine loop existed loads as ``"juncture"`` under
    # ``extra="forbid"`` and replays exactly as it always did.
    loop: Loop = "juncture"

    @model_validator(mode="after")
    def _auto_implies_no_inputs(self) -> "Recipe":
        if self.mode == "auto" and self.inputs:
            raise ValueError("mode 'auto' must have empty inputs")
        return self
