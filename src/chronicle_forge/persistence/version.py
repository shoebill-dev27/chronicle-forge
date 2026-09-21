"""The engine version a recipe is recorded under.

A Recipe reproduces a run by re-executing the deterministic engine. That is
only sound while the engine behaves as it did when the recipe was recorded, so
every recipe carries ``ENGINE_VERSION`` and ``load_recipe`` refuses any recipe
whose version differs (no silent, divergent fallback).

Bump this whenever a change to worldgen, P6 selection, the execution funnel, the
RNG derivation, the clock, or the play loop would alter the world produced from
a given seed + inputs.

History:
- ``0.1.0-p8-mvp`` — the P8 MVP determinism point (tag ``v0.1.0-p8-mvp``,
  seed42 world ``e62d8f2c…``, 40-year worlds, 2–7-year lives).
- ``0.2.0-time-domain`` — one tick = one world year through ``advance_year``
  (the world now simulates during a life, not only in the gap); a life is
  taken up at 16 (``birth_year`` is the actual birth, 16 years earlier) and
  reaches 80 unless a registered hazard ends it (none by default); a fixed
  10-year gap between lives; a 200-year horizon that ends the run mid-life.
"""

from __future__ import annotations

ENGINE_VERSION = "0.2.0-time-domain"
