"""Routines: the years a person spent living one way.

The unit of a life here is not an act but a *span*. "Supported Karic once" is
not what a life is made of; "worked beside Karic in Hollowfen from sixteen to
twenty-three" is. One :class:`~.models.Routine` row holds that whole stretch,
and it stays in ``world.routines`` after it ends and after its actor dies,
because a later life reading history needs to see what an earlier one actually
did with its years.

Two rules keep the record honest:

* **Duration is derived, never stored.** ``end_year - start_year`` (or
  ``world.current_year - start_year`` while it runs), so no counter can drift
  away from the chronology. A routine that began in year 12 and ended in year
  19 lasted **seven** years: the start year counts, the end year does not.
* **The clock is still ``advance_year``.** :func:`continue_routine` may be
  asked for ten years, but it takes them one ``advance_year`` at a time and
  re-checks every year whether the routine is still true. If the person you
  worked beside died in the fourth year, the record says four years, not ten.

What proximity *does* to the people in it — friendship, knowledge, rivalry,
inheritance — is not modelled here, and neither is a routine's causal effect
on the world. This module only makes the span itself true.
"""

from __future__ import annotations

from typing import List, Optional

from . import config
from .enums import RoutineEndReason, RoutineKind
from .ids import next_id
from .models import NPC, Routine, World
from .population import age_of, current_person_id, person_by_id

# The kinds that are aimed at another person rather than at a place.
PERSON_KINDS = (RoutineKind.WORK_WITH, RoutineKind.ASSOCIATE_WITH)


class RoutineRefused(Exception):
    """The world will not record this routine, because it would not be true —
    no such person, they are dead, a child, elsewhere, or the actor is already
    living another way. Refused rather than adjusted: a routine the world
    cannot support is not a smaller routine, it is a fiction.
    """


# --- reading -----------------------------------------------------------


def active_routine(world: World, person_id: Optional[str] = None) -> Optional[Routine]:
    """The routine this person is living right now — the player's, by default."""
    actor_id = person_id if person_id is not None else current_person_id(world)
    if actor_id is None:
        return None
    return next(
        (r for r in world.routines if r.actor_person_id == actor_id and r.active),
        None,
    )


def routines_of(world: World, person_id: str) -> List[Routine]:
    """Everything this person ever did with their years, in the order they
    did it — including the routines that ended long before they died."""
    return [r for r in world.routines if r.actor_person_id == person_id]


def routine_years(world: World, routine: Routine) -> int:
    """How many years this routine has run.

    ``start_year=12, end_year=19`` is seven years: the year it began counts,
    the year it ended does not. A routine still running is measured against
    the clock, so it is never stale.
    """
    end = routine.end_year if routine.end_year is not None else world.current_year
    return end - routine.start_year


# --- starting ----------------------------------------------------------


def _actor(world: World) -> NPC:
    actor_id = current_person_id(world)
    if actor_id is None:
        raise RoutineRefused("nobody is being played: no life is current")
    actor = person_by_id(world, actor_id)
    if actor is None:
        raise RoutineRefused(f"{actor_id} is not in the registry")
    return actor


def _check_target(world: World, actor: NPC, target_person_id: Optional[str]) -> NPC:
    """A person you spend years beside has to be someone you could actually
    have spent them beside: real, alive, grown, not yourself, and here."""
    if target_person_id is None:
        raise RoutineRefused("this routine is lived with somebody; name them")
    target = person_by_id(world, target_person_id)
    if target is None:
        raise RoutineRefused(f"{target_person_id} is not in the registry")
    if target.id == actor.id:
        raise RoutineRefused("nobody spends their years beside themselves")
    if not target.alive:
        raise RoutineRefused(f"{target.id} is dead")
    if age_of(world, target) < config.ADULT_AGE:
        raise RoutineRefused(f"{target.id} is a child")
    if target.lifecycle.location_id != actor.lifecycle.location_id:
        raise RoutineRefused(
            f"{target.id} is not where {actor.id} is — there is no travel yet"
        )
    return target


def begin_routine(
    world: World,
    kind: RoutineKind,
    target_person_id: Optional[str] = None,
) -> Routine:
    """Start living a way. This does **not** move the world: choosing how to
    spend your years is not itself a year (see :func:`continue_routine`).
    """
    actor = _actor(world)
    if active_routine(world, actor.id) is not None:
        raise RoutineRefused(
            f"{actor.id} is already living a routine; change it rather than "
            "starting a second one"
        )
    location_id = actor.lifecycle.location_id
    if not any(loc.id == location_id for loc in world.locations):
        raise RoutineRefused(
            f"{actor.id} is in {location_id}, which this world has not"
        )

    if kind in PERSON_KINDS:
        target = _check_target(world, actor, target_person_id)
        target_id: Optional[str] = target.id
    else:
        if target_person_id is not None:
            raise RoutineRefused(f"{kind.value} is aimed at a place, not a person")
        target_id = None

    routine = Routine(
        id=next_id("routine", world.routines),
        actor_person_id=actor.id,
        kind=kind,
        location_id=location_id,
        target_person_id=target_id,
        start_year=world.current_year,
    )
    world.routines.append(routine)
    return routine


# --- ending ------------------------------------------------------------


def end_routine(world: World, routine: Routine, reason: RoutineEndReason) -> Routine:
    """Close a span in the current world year. A routine ends once."""
    if not routine.active:
        raise RuntimeError(f"{routine.id} already ended in year {routine.end_year}")
    routine.end_year = world.current_year
    routine.end_reason = reason
    return routine


def change_routine(
    world: World,
    kind: RoutineKind,
    target_person_id: Optional[str] = None,
) -> Routine:
    """Stop living one way and start another, in the same world year — so the
    two spans meet without a gap and without ever overlapping."""
    current = active_routine(world)
    if current is None:
        return begin_routine(world, kind, target_person_id)
    end_routine(world, current, RoutineEndReason.PLAYER_CHANGED)
    try:
        return begin_routine(world, kind, target_person_id)
    except RoutineRefused:
        # The new way was not possible; the old one is still over. Say so
        # rather than silently resuming a life the player chose to leave.
        raise


def close_on_death(world: World, person_id: str) -> None:
    """A person's own routine ends with them. Called by ``life.end_life`` so
    one death is written everywhere at once; the row itself stays."""
    routine = active_routine(world, person_id)
    if routine is not None:
        end_routine(world, routine, RoutineEndReason.ACTOR_DIED)


def close_at_horizon(world: World) -> None:
    """The world stops, so every way of living stops with it — but nobody
    dies of the horizon (docs/design_time_domain.md §5)."""
    for routine in world.routines:
        if routine.active:
            end_routine(world, routine, RoutineEndReason.WORLD_ENDED)


# --- living it out -----------------------------------------------------


def _broken(world: World, routine: Routine) -> Optional[RoutineEndReason]:
    """Whether the world as it now stands has made this routine untrue, and
    why. The only place closure conditions are decided."""
    actor = person_by_id(world, routine.actor_person_id)
    if actor is None or not actor.alive:
        return RoutineEndReason.ACTOR_DIED
    if routine.target_person_id is not None:
        target = person_by_id(world, routine.target_person_id)
        if target is None or not target.alive:
            return RoutineEndReason.TARGET_DIED
    return None


def step_routines(world: World) -> None:
    """Bring every open routine back into agreement with the world.

    Called by ``macro.advance_year`` once the year has fully happened, so a
    routine is never left claiming a year the world stopped supporting —
    whoever advanced the clock, and whether or not anybody was running
    :func:`continue_routine`. A routine is world truth, not a side effect of
    the command that happened to move time.

    Only open spans are looked at; a closed one is history and is never
    rewritten.
    """
    for routine in world.routines:
        if not routine.active:
            continue
        reason = _broken(world, routine)
        if reason is not None:
            end_routine(world, routine, reason)


def continue_routine(world: World, years: int) -> dict:
    """Live the current routine for up to ``years`` more years.

    ``years`` is a maximum, not a promise. The world moves one
    ``advance_year`` at a time — never a jump — and that call is what decides
    whether the routine is still true (:func:`step_routines`). This function
    only stops asking for more years once the span has closed; it holds no
    closure rules of its own.
    """
    routine = active_routine(world)
    if routine is None:
        raise RoutineRefused("no routine is being lived")
    from .macro import advance_year  # macro reaches back into this module

    years_run = 0
    for _ in range(max(0, years)):
        if world.current_year >= world.max_year:
            break  # the horizon already closed it
        advance_year(world)
        years_run += 1
        if not routine.active:
            break  # that year ended it: death, or the world's own end

    return {
        "years_run": years_run,
        "routine": routine,
        "years": routine_years(world, routine),
        "ended": not routine.active,
        "end_reason": routine.end_reason,
    }
