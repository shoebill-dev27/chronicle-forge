"""Tracked persons: they are born, grow up, die, and leave descendants.

This module owns one of the world's two levels of population truth:

* **Tracked persons** — ``world.npcs``, one :class:`NPC` row each, with a name,
  a stable id, a birth year, a death year and ancestry. The body the player is
  living in is one of them (``Life.person_id`` names it). The list is a
  *historical* registry, not a cast list: a dead person keeps their row with
  ``alive=False`` and a ``death_year``, so history can still name them a
  century later.
* **The aggregate populace** — ``world.population``, humanity as a number with
  no identity. Nothing here reads or writes it, and it is never the count of
  tracked persons.

Age is never counted. It is ``world.current_year - lifecycle.birth_year``,
written once a year by :func:`step_population` — the same rule the playable
life uses (docs/design_time_domain.md §2).

The birth rule is deliberately a scaffold, not a fertility model:
``TRACKED_BIRTHS_PER_YEAR`` people enter the registry each year, each to one
living adult, so the world still holds named people in year 200 and always
offers a sixteen-year-old for the player to become. This is not the world's
birth rate — it is how fast history acquires people it can name. Marriage,
households and real demography are later work; a parent here is a genealogical
fact and says nothing about romance.
"""

from __future__ import annotations

from typing import List, Optional

from . import config
from .causal import CausalGraph
from .enums import EventScale, NPCTier, SeedDomain
from .ids import next_id
from .models import NPC, Lifecycle, Lineage, World
from .rng import DeterministicRNG

BIRTH_SALT = 11

PROMOTION_PROBABILITY = 0.1  # an ambitious adult may rise to leader (P3.5)


class NoSuccessor(Exception):
    """The world holds nobody of the age the player must be born into. The
    birth scaffold is meant to make this impossible; it is an invariant
    violation, never something to paper over by inventing a person."""


# --- reading the registry ------------------------------------------------


def age_of(world: World, person: NPC) -> int:
    """The person's age this year — the only formula for a person's age.

    Pure: reading the registry never writes to it. A record with no birth year
    (a fixture from before chronology) is taken at its stored age.
    """
    birth = person.lifecycle.birth_year
    if birth is None:
        return person.lifecycle.age
    return world.current_year - birth


def living(world: World) -> List[NPC]:
    return [p for p in world.npcs if p.alive]


def adults(world: World) -> List[NPC]:
    """The living people old enough to act. Children exist in history and in
    their family, but they are not actors (and not opportunities)."""
    return [p for p in living(world) if age_of(world, p) >= config.ADULT_AGE]


def aged(world: World, age: int) -> List[NPC]:
    return [p for p in living(world) if age_of(world, p) == age]


def person_by_id(world: World, person_id: str) -> Optional[NPC]:
    """The tracked person with this id, or ``None`` if the world has no such
    row — which, for a ``Life.person_id``, means a corrupt registry."""
    return next((p for p in world.npcs if p.id == person_id), None)


def ancestors(world: World, person: NPC) -> List[NPC]:
    """The person's line back to its founder, nearest parent first."""
    out: List[NPC] = []
    seen = {person.id}
    current = person
    while current.lineage.parent_ids:
        parent = person_by_id(world, current.lineage.parent_ids[0])
        if parent is None or parent.id in seen:
            break
        out.append(parent)
        seen.add(parent.id)
        current = parent
    return out


def descendants(world: World, person: NPC) -> List[NPC]:
    """Everyone descended from this person, in registry order."""
    out: List[NPC] = []
    frontier = {person.id}
    for candidate in world.npcs:  # ids are allocated in birth order
        if candidate.lineage.parent_ids and candidate.lineage.parent_ids[0] in frontier:
            out.append(candidate)
            frontier.add(candidate.id)
    return out


# --- the yearly step -------------------------------------------------------


def _current_person_id(world: World) -> Optional[str]:
    """The body the player is in right now, or ``None`` between lives — a real
    world state, not a nullable ``Life.person_id`` (that field is required)."""
    life = next(
        (lf for lf in world.lives if lf.id == world.player.current_life_id), None
    )
    return life.person_id if life is not None else None


def _grow_and_die(world: World, player_person_id: Optional[str]) -> None:
    """Refresh every living person's age, and end the lives that reached the
    cap. The body the player is living in is left to the mortality seam, which
    owns that death and writes it back here through ``life.end_life``."""
    for person in world.npcs:
        if not person.alive:
            continue
        person.lifecycle.age = age_of(world, person)
        person.lifecycle.life_stage = (
            "adult" if person.lifecycle.age >= config.ADULT_AGE else "child"
        )
        if person.id == player_person_id:
            continue
        if person.lifecycle.age >= config.LIFESPAN_CAP:
            person.alive = False
            person.lifecycle.death_year = world.current_year


def _promote(world: World, graph: CausalGraph, rng: DeterministicRNG) -> None:
    """An ambitious adult may rise to leader, which is world history (P3.5)."""
    from .macro import _emit_event  # macro owns event emission

    for person in adults(world):
        if (
            person.personality.ambitious > 70
            and person.lifecycle.occupation != "leader"
            and rng.random() < PROMOTION_PROBABILITY
        ):
            person.lifecycle.occupation = "leader"
            _emit_event(
                world,
                graph,
                SeedDomain.GOVERNANCE,
                f"{person.name} rises to power",
                [person.id],
                scale=EventScale.SMALL,
            )


def _make_name(rng: DeterministicRNG) -> str:
    from .worldgen import make_name

    return make_name(rng)


def _make_personality(rng: DeterministicRNG):
    from .worldgen import make_personality

    return make_personality(rng)


def give_birth(world: World, parent: NPC, rng: DeterministicRNG) -> NPC:
    """Record one birth: a new person, aged 0, with ``parent`` as ancestry."""
    child = NPC(
        id=next_id("npc", world.npcs),
        name=_make_name(rng),
        tier=NPCTier.A,
        personality=_make_personality(rng),
        lifecycle=Lifecycle(
            age=0,
            life_stage="child",
            occupation="child",
            faction_id=parent.lifecycle.faction_id,
            birth_year=world.current_year,
        ),
        lineage=Lineage(
            # A founder's own id names the line; everyone below inherits it.
            lineage_id=parent.lineage.lineage_id or parent.id,
            parent_ids=[parent.id],
            generation=parent.lineage.generation + 1,
        ),
    )
    world.npcs.append(child)
    return child


def _births(world: World, rng: DeterministicRNG, player_person_id: Optional[str]):
    """The scaffold: ``TRACKED_BIRTHS_PER_YEAR`` people into the registry.

    The player is never made a parent automatically — children of the player
    are family gameplay, not demography. Their body is not a candidate, and
    neither is anyone who is exactly ``ADULT_AGE``: that cohort is who the
    player may be taken up as this very year, and a child fathered hours before
    the hand-over would be the player's child all the same.
    """
    candidates = [
        p
        for p in adults(world)
        if p.id != player_person_id and age_of(world, p) > config.ADULT_AGE
    ]
    if not candidates:
        return
    for _ in range(config.TRACKED_BIRTHS_PER_YEAR):
        give_birth(world, rng.choice(candidates), rng)


def step_population(world: World, graph: CausalGraph, rng: DeterministicRNG) -> None:
    """One year of tracked people, in one order: everyone ages, the old die,
    the living may rise, and children are born. Called only by
    ``macro.advance_year``. ``world.population`` is untouched — the aggregate
    populace is a separate level of truth this scaffold does not model."""
    player_person_id = _current_person_id(world)
    _grow_and_die(world, player_person_id)
    _promote(world, graph, rng)
    _births(world, derive_birth_rng(world), player_person_id)


def derive_birth_rng(world: World) -> DeterministicRNG:
    from .macro import derive_rng

    return derive_rng(world, world.current_year, salt=BIRTH_SALT)


# --- becoming someone ------------------------------------------------------


def successor(world: World) -> NPC:
    """The person the player takes up next: someone who is exactly
    ``ADULT_AGE`` this year and has never been the player before.

    Raises :class:`NoSuccessor` rather than inventing a body — a world with
    nobody of that age is a broken world, and hiding it would make the player's
    history a fiction.
    """
    taken = {lf.person_id for lf in world.lives}
    candidates = [p for p in aged(world, config.ADULT_AGE) if p.id not in taken]
    if not candidates:
        raise NoSuccessor(
            f"year {world.current_year}: nobody is {config.ADULT_AGE} "
            "for the player to become"
        )
    return candidates[0]  # registry order: the earliest-born of that year
