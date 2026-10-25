"""Where people live, and the one way a person changes it.

A place to live is any location that is not a dungeon: the dungeon is a place
to go, not a place to be from. That rule is :func:`is_residential`, and it is
the only copy of it — worldgen hands out homes with it and relocation chooses
destinations with it, so the two can never disagree about where a person may
be.

:func:`relocate` changes the truth of where somebody lives and nothing else
that is not made false by it. A routine is lived *somewhere*, so the mover's
open routine ends here (``RELOCATED``); its row keeps the place it was lived
in. No knowledge is learned or passed on, no tie is touched, no year passes —
time is the caller's to spend, through ``advance_year``. There is no map, no
distance and no road: relocation is leaving one life's place for another.
"""

from __future__ import annotations

from typing import List, Optional

from .enums import LocationType, RoutineEndReason
from .models import Location, World
from .population import person_by_id


class RelocationRefused(Exception):
    """The world will not record this move, because it would not be true — no
    such person or place, a dead person, a place nobody lives, or the place
    they already are."""


def is_residential(location: Location) -> bool:
    """Whether a person may live here."""
    return location.type is not LocationType.DUNGEON


def residential_locations(world: World) -> List[Location]:
    """Every place a person may live, in the world's own (fixed) order."""
    return [loc for loc in world.locations if is_residential(loc)]


def location_by_id(world: World, location_id: str) -> Optional[Location]:
    return next((loc for loc in world.locations if loc.id == location_id), None)


def relocate(world: World, person_id: str, destination_id: str) -> Location:
    """Move a living person to live somewhere else. Returns the destination.

    Everything is checked before anything changes, so a refused move leaves
    the world exactly as it was.
    """
    from .routine import active_routine, end_routine  # routine imports population

    person = person_by_id(world, person_id)
    if person is None or not person.alive:
        raise RelocationRefused(f"{person_id} is not a living person")
    destination = location_by_id(world, destination_id)
    if destination is None:
        raise RelocationRefused(f"{destination_id} is not a place in this world")
    if not is_residential(destination):
        raise RelocationRefused(f"nobody lives in {destination.name}")
    if destination.id == person.lifecycle.location_id:
        raise RelocationRefused(f"{person_id} already lives in {destination.name}")

    routine = active_routine(world, person.id)
    if routine is not None:
        end_routine(world, routine, RoutineEndReason.RELOCATED)
    person.lifecycle.location_id = destination.id
    return destination
