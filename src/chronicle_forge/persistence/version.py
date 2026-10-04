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
- ``0.3.0-population-continuity`` — the world keeps a population across the
  horizon. ``World.npcs`` became a historical registry of individually tracked
  persons (birth year, death year, parents, generation) that nothing deletes;
  worldgen seeds a child cohort as well as founders; one tracked person is born
  every year; everyone dies at the lifespan cap; and a playable life is now
  taken up as a person the world already holds, who is sixteen that year
  (``Life.person_id``). Same seed, different world: world identity changed.
- ``0.4.0-routine`` — a life is made of spans, not single acts. Tracked persons
  gained ``Lifecycle.location_id`` (assigned by index in ``worldgen``, inherited
  by every newborn from its parent) and the world gained ``World.routines``, a
  registry of the year-spans people lived — kept after they end and after their
  actor dies. Worldgen output changed, so world identity changed again; no
  rendered lens did.
- ``0.5.0-playable-routine`` — the human game loop became the routine loop.
  ``chronicle-forge play`` with a person at the keyboard now runs
  ``play.routine_session``: you are a real sixteen-year-old, you choose how to
  spend your years, and time moves only when you say so (``--auto`` and
  ``--script`` stay on the juncture loop). A recipe records which input
  language wrote it (``loop``), since routine commands and option numbers
  cannot be replayed through each other. And the founding generation is now
  chronologically possible: a child's parent was over ``ADULT_AGE`` *in the
  year that child was born*, so a sixteen-year-old founder is no longer handed
  a ten-year-old. That last one changes worldgen output, and with it world
  identity.
"""

from __future__ import annotations

ENGINE_VERSION = "0.5.0-playable-routine"
