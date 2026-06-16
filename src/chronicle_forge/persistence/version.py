"""The engine version a recipe is recorded under.

A Recipe is canonical: it reconstructs a run by re-executing the deterministic
engine. That is only sound while the engine behaves as it did when the recipe
was recorded, so every recipe carries ``ENGINE_VERSION`` and ``load_recipe``
refuses any recipe whose version differs (no silent, divergent fallback).

Bump this whenever a change to worldgen, P6 selection, the execution funnel, the
RNG derivation, or the play loop would alter the world produced from a given
seed + inputs. The current baseline is the P8 MVP determinism point
(tag ``v0.1.0-p8-mvp``, seed42 world ``e62d8f2c…``).
"""

from __future__ import annotations

ENGINE_VERSION = "0.1.0-p8-mvp"
