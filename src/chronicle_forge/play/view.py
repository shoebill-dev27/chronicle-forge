"""What the player can see of the world they are living in.

A read model over the new core — :mod:`population`, :mod:`routine`,
:mod:`relationship` — and nothing else. It holds no state, draws no RNG, reads
no clock of its own and never writes to the world: every field is a fact those
modules already own, shaped for a surface to print.

Two rules it keeps:

* **Names, not ids.** A person is shown by name. Ids travel in these records
  because a command has to be able to name a target unambiguously, but they are
  not what the player reads.
* **Facts, not readings.** A tie reports the years two people shared and who is
  whose parent. It never reports that they were close, trusted each other, or
  that any of it mattered — the engine does not know those things.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .. import population as pop
from .. import relationship as rel
from .. import routine as rt
from ..enums import RoutineEndReason, RoutineKind
from ..models import NPC, CausalNode, Routine, World


@dataclass(frozen=True)
class PersonView:
    """Somebody the player can see, and name in a command."""

    person_id: str
    name: str
    age: int


@dataclass(frozen=True)
class RoutineView:
    """One span of a life, as it reads from outside."""

    kind: RoutineKind
    location_name: str
    target_name: Optional[str]
    start_year: int
    end_year: Optional[int]
    years: int
    end_reason: Optional[RoutineEndReason]

    @property
    def active(self) -> bool:
        return self.end_year is None


@dataclass(frozen=True)
class TieView:
    """What the world can say about the player and one other person."""

    name: str
    shared_years: int
    kinds: Tuple[RoutineKind, ...]
    parent_or_child: Optional[str]  # "parent" / "child", from the player's side
    alive: bool


@dataclass(frozen=True)
class EventView:
    """Something that happened in the world, as this person could have seen it."""

    year: int
    text: str


@dataclass(frozen=True)
class SelfView:
    """The person the player currently is."""

    person_id: str
    name: str
    age: int
    year: int
    location_name: str
    parents: Tuple[str, ...]
    routine: Optional[RoutineView]


# --- helpers ---------------------------------------------------------------


def _location_name(world: World, location_id: str) -> str:
    loc = next((l for l in world.locations if l.id == location_id), None)
    return loc.name if loc is not None else location_id


def _name(world: World, person_id: Optional[str]) -> Optional[str]:
    if person_id is None:
        return None
    person = pop.person_by_id(world, person_id)
    return person.name if person is not None else None


def _person_view(world: World, person: NPC) -> PersonView:
    return PersonView(
        person_id=person.id, name=person.name, age=pop.age_of(world, person)
    )


def _routine_view(world: World, routine: Routine) -> RoutineView:
    return RoutineView(
        kind=routine.kind,
        location_name=_location_name(world, routine.location_id),
        target_name=_name(world, routine.target_person_id),
        start_year=routine.start_year,
        end_year=routine.end_year,
        years=rt.routine_years(world, routine),
        end_reason=routine.end_reason,
    )


# --- the views -------------------------------------------------------------


def current_person(world: World) -> Optional[NPC]:
    return pop.person_by_id(world, pop.current_person_id(world) or "")


def self_view(world: World) -> Optional[SelfView]:
    """Who the player is right now, or ``None`` between lives."""
    person = current_person(world)
    if person is None:
        return None
    routine = rt.active_routine(world, person.id)
    return SelfView(
        person_id=person.id,
        name=person.name,
        age=pop.age_of(world, person),
        year=world.current_year,
        location_name=_location_name(world, person.lifecycle.location_id),
        parents=tuple(
            n for n in (_name(world, p) for p in person.lineage.parent_ids) if n
        ),
        routine=_routine_view(world, routine) if routine is not None else None,
    )


def nearby(world: World) -> List[PersonView]:
    """The grown people in the same place as the player, by id so the list a
    command indexes into is the same list every time."""
    person = current_person(world)
    if person is None:
        return []
    here = [
        p
        for p in pop.adults(world)
        if p.id != person.id and p.lifecycle.location_id == person.lifecycle.location_id
    ]
    return [_person_view(world, p) for p in sorted(here, key=lambda p: p.id)]


def history(world: World, person_id: str) -> List[RoutineView]:
    """Every way this person has lived, in the order they lived it."""
    return [_routine_view(world, r) for r in rt.routines_of(world, person_id)]


def ties(world: World, person_id: str) -> List[TieView]:
    """Everyone this person has anything with — only where the world has
    evidence, and only the evidence itself."""
    out: List[TieView] = []
    for tie in rel.relationships_of(world, person_id):
        name = _name(world, tie.person_b_id)
        if name is None:
            continue
        out.append(
            TieView(
                name=name,
                shared_years=tie.shared_years,
                kinds=tie.routine_kinds,
                parent_or_child=(
                    tie.genealogical_role.value
                    if tie.genealogical_role is not None
                    else None
                ),
                alive=tie.b_alive,
            )
        )
    return out


def _event_place(world: World, node: CausalNode) -> Optional[str]:
    """Where this event happened, if the world actually knows.

    Two kinds of answer would count, and only the second is currently ever
    available: an event may carry its own ``location_id``, which no emitter in
    the engine sets today, or it may name a tracked person, who is somewhere.
    Nothing else is guessed. An event whose only actors are factions or
    wildcards has no location anywhere in the world state, so it has none here
    either, and is shown to nobody rather than to everybody.
    """
    if node.location_id is not None:
        return node.location_id
    for actor_id in node.actors:
        person = pop.person_by_id(world, actor_id)
        if person is not None:
            return person.lifecycle.location_id
    return None


def observed_events(
    world: World, person_id: str, nodes: List[CausalNode]
) -> List[EventView]:
    """The ones of ``nodes`` this person was in a position to see.

    The test is the only one the world can support: it happened where they
    were. It is deliberately not a feed of everything — a war between two
    factions is real and is not shown, because the world does not record
    where a war was.
    """
    person = pop.person_by_id(world, person_id)
    if person is None:
        return []
    here = person.lifecycle.location_id
    return [
        EventView(year=node.year, text=node.title)
        for node in nodes
        if _event_place(world, node) == here and node.title
    ]
