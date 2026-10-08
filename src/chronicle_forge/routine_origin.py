"""Lived routines, read as historical origins — the causal *input* side only.

This module implements an origin representation and **no effect translation**.
A routine that has been lived is a first-class historical origin here, and a
causal input that differs between differently-lived lives. What such an origin
*does to the world* is an open design question, deliberately unresolved.

A :class:`~.models.Routine` is already everything an origin has to be. It is
stable, deterministic, and it carries its actor, its kind, the place, the
person and the chronology; its duration is read off that chronology rather than
counted. So this module stores nothing and writes nothing — like
:mod:`relationship`, which reads the same spans socially, it is a projection.

**An origin is not an event.** "Ashlin and Morgar spent ten years together" is
a true thing about history and a legitimate causal source. It is *not* a thing
that happened to the world because of them, and this module will not dress it
up as one. Nothing here plants a ``CausalSeed``, generates a ``CausalNode`` or
an edge, promotes heritage, or moves a theme axis. There is no domain, no
magnitude, no weight and no scale anywhere in it.

That is not an omission, it is the state of the engine. The existing causal
machinery takes exactly one kind of input — a ``CausalSeed``, which is a
one-shot trigger for a single *act*, carrying a ``SeedDomain`` and a
``magnitude``. Routing a continuing way of living through it would require
deciding that years convert into magnitude at some rate, and that working
beside somebody belongs to one of eight domains written for single acts.
Neither follows from anything the world knows. Until an owner decides what a
routine *does*, the honest shape is this one: the origin exists, it is
queryable, two lives lived differently are different here — and the translator
to a world effect is absent on purpose. ``docs/design_routine_origin.md`` §6
lists the seams one would have to go through, and §7 the decisions it needs.

The one completed year is the only rule this module does enforce: choosing how
to live is not yet living that way, so a routine with no whole year behind it
is not an origin at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .enums import RoutineKind
from .models import Routine, World
from .routine import routine_years


@dataclass(frozen=True)
class RoutineOrigin:
    """One way of living, as a cause the world could be read back from.

    Every field is a fact the :class:`~.models.Routine` already owns, and
    ``duration_years`` is derived from ``[start_year, end_year)`` on the way
    through — never stored, so it cannot drift from the chronology. A span
    still being lived is measured against the clock; a closed one stops moving
    because its ``end_year`` has.

    There is deliberately no strength, weight, scale or magnitude here. Years
    are kept as years.
    """

    routine_id: str
    actor_person_id: str
    kind: RoutineKind
    location_id: str
    target_person_id: Optional[str]  # set for the person-facing kinds
    start_year: int
    end_year: Optional[int]  # None while it is still being lived
    duration_years: int

    @property
    def open(self) -> bool:
        return self.end_year is None


def origin_of(world: World, routine: Routine) -> Optional[RoutineOrigin]:
    """This span as a causal origin, or ``None`` if it has not yet been lived
    for one whole year. Starting is not an act."""
    years = routine_years(world, routine)
    if years < 1:
        return None
    return RoutineOrigin(
        routine_id=routine.id,
        actor_person_id=routine.actor_person_id,
        kind=routine.kind,
        location_id=routine.location_id,
        target_person_id=routine.target_person_id,
        start_year=routine.start_year,
        end_year=routine.end_year,
        duration_years=years,
    )


def routine_origins(
    world: World, actor_person_id: Optional[str] = None
) -> List[RoutineOrigin]:
    """Every way of living that has lasted a year, in the order it was lived,
    optionally only one person's.

    The dead are included and so are closed spans: they are what a history is
    made of, and nothing about them changes once they stop.
    """
    return [
        origin
        for routine in world.routines
        if actor_person_id is None or routine.actor_person_id == actor_person_id
        for origin in (origin_of(world, routine),)
        if origin is not None
    ]
