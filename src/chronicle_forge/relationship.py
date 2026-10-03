"""Relationships: what two people actually have between them, read off history.

This is **not** a friendship score. The engine does not decide that seven years
beside someone made them a friend, or that a parent was loved. It answers the
questions history can actually answer:

* is there anything between these two at all, and on what evidence
* how many years did they directly share, and in which routines
* when did that start, when did it last run, is it still running
* is one of them the other's parent or child

Everything here is **derived**, never stored. The truth already exists —
:class:`~.models.Routine` spans in ``world.routines`` and ``Lineage.parent_ids``
on the people themselves — and a stored tie would be a second copy that can
disagree with it. The same rule age and routine duration follow
(docs/design_time_domain.md §2, docs/design_routine.md §3). Nothing in this
module writes to the world, so a routine ending, a person dying or a life
handing over never destroys a relationship: the evidence outlives all three.

The old ``models.Relation`` (``affinity``/``trust``/``fear``, keyed by the
*soul* id) is a different thing entirely — mutable affect from the old activity
path — and is deliberately left alone. See docs/design_relationship.md §1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from .enums import RoutineKind
from .models import Routine, World
from .population import person_by_id

# The routine kinds whose years count as time two people shared.
#
# Deliberately spelled out here rather than taken from ``routine.PERSON_KINDS``.
# That set means "aimed at a person"; this one means "was time spent
# together", and they are not the same question. A future person-facing kind —
# betraying somebody, a single favour — would join ``PERSON_KINDS`` and must
# *not* thereby start adding years to how long two people lived side by side.
# Whether a new kind is shared time is a decision made here, on purpose.
SHARED_TIME_ROUTINE_KINDS = (RoutineKind.WORK_WITH, RoutineKind.ASSOCIATE_WITH)


class RelationshipEvidence(str, Enum):
    """Why the world says these two have anything to do with each other.

    Every tie names its grounds. New grounds (helping, teaching, opposing) are
    added here and given a collector below; nothing else has to change.
    """

    SHARED_ROUTINE = "shared_routine"
    GENEALOGY = "genealogy"


class GenealogicalRole(str, Enum):
    """What B is to A. Directional: querying the other way round inverts it."""

    PARENT = "parent"
    CHILD = "child"


_INVERSE = {
    GenealogicalRole.PARENT: GenealogicalRole.CHILD,
    GenealogicalRole.CHILD: GenealogicalRole.PARENT,
}


@dataclass(frozen=True)
class Relationship:
    """One pair, and everything the world can say about them.

    Years are half-open, exactly as routines are: a span that ran from year 12
    to year 19 contributed seven shared years, and ``last_shared_year_exclusive``
    is 19 — the first year they were *not* together. The field is named for the
    convention so it cannot be misread as "the last year they were together".
    """

    person_a_id: str
    person_b_id: str
    evidence: Tuple[RelationshipEvidence, ...]
    shared_years: int
    shared_spans: Tuple[Routine, ...]
    routine_kinds: Tuple[RoutineKind, ...]
    first_shared_year: Optional[int]
    last_shared_year_exclusive: Optional[int]
    sharing_now: bool
    # What B is to A, when one is directly the other's parent. Descendants
    # further back are ancestry, not a relationship (``population.ancestors``).
    genealogical_role: Optional[GenealogicalRole]
    a_alive: bool
    b_alive: bool


# --- shared time -----------------------------------------------------------


def _span_bounds(world: World, routine: Routine) -> Tuple[int, int]:
    """A routine as the half-open year interval it actually covers.

    A span still being lived is measured against the clock, so starting one and
    asking the same year contributes nothing: pressing the button is not a year
    spent together.
    """
    end = routine.end_year if routine.end_year is not None else world.current_year
    return routine.start_year, max(routine.start_year, end)


def shared_years(world: World, spans: Sequence[Routine]) -> int:
    """Total years covered by these spans, counting overlap once.

    Separate stretches add up and the gap between them does not count. Two
    stretches that overlap — which one player cannot currently produce, but the
    rule must not assume that — contribute their union, not their sum.
    """
    intervals = sorted(_span_bounds(world, span) for span in spans)
    total = 0
    current_start: Optional[int] = None
    current_end = 0
    for start, end in intervals:
        if current_start is None or start > current_end:
            if current_start is not None:
                total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_start is not None:
        total += current_end - current_start
    return total


def _shared_spans(world: World, a_id: str, b_id: str) -> List[Routine]:
    """Every routine that put these two together, whoever began it.

    Direct shared history is a fact about the pair, so it reads the same from
    either side. Only :data:`SHARED_TIME_ROUTINE_KINDS` counts: ``WORK_AT`` is
    not here, because being in the same village is not a relationship, and a
    future person-facing kind is not here either until somebody decides it is
    time spent together.
    """
    pair = {a_id, b_id}
    return [
        r
        for r in world.routines
        if r.kind in SHARED_TIME_ROUTINE_KINDS
        and r.target_person_id is not None
        and {r.actor_person_id, r.target_person_id} == pair
    ]


def _genealogical_role(
    world: World, a_id: str, b_id: str
) -> Optional[GenealogicalRole]:
    a = person_by_id(world, a_id)
    b = person_by_id(world, b_id)
    if a is None or b is None:
        return None
    if b_id in a.lineage.parent_ids:
        return GenealogicalRole.PARENT
    if a_id in b.lineage.parent_ids:
        return GenealogicalRole.CHILD
    return None


# --- the query surface -----------------------------------------------------


def relationship_between(
    world: World, person_a_id: str, person_b_id: str
) -> Optional[Relationship]:
    """What these two have between them, or ``None`` if the world says nothing.

    Nobody has a relationship with themselves, and two people the history never
    put together do not get an empty record — silence is the honest answer.
    """
    if person_a_id == person_b_id:
        return None
    a = person_by_id(world, person_a_id)
    b = person_by_id(world, person_b_id)
    if a is None or b is None:
        return None

    spans = _shared_spans(world, person_a_id, person_b_id)
    role = _genealogical_role(world, person_a_id, person_b_id)
    if not spans and role is None:
        return None

    evidence: List[RelationshipEvidence] = []
    if spans:
        evidence.append(RelationshipEvidence.SHARED_ROUTINE)
    if role is not None:
        evidence.append(RelationshipEvidence.GENEALOGY)

    bounds = [_span_bounds(world, span) for span in spans]
    return Relationship(
        person_a_id=person_a_id,
        person_b_id=person_b_id,
        evidence=tuple(evidence),
        # Genealogy alone buys no shared years: being someone's child is not
        # the same as having spent time with them, and the world does not know
        # that they did.
        shared_years=shared_years(world, spans),
        shared_spans=tuple(sorted(spans, key=lambda r: (r.start_year, r.id))),
        routine_kinds=tuple(sorted({r.kind for r in spans}, key=lambda k: k.value)),
        first_shared_year=min((s for s, _ in bounds), default=None),
        last_shared_year_exclusive=max((e for _, e in bounds), default=None),
        sharing_now=any(span.active for span in spans),
        genealogical_role=role,
        a_alive=a.alive,
        b_alive=b.alive,
    )


def relationships_of(world: World, person_id: str) -> List[Relationship]:
    """Everyone this person has anything with, by the other person's id.

    Only people the evidence actually names: a world of two hundred strangers
    is not two hundred relationships. The dead are included — they are who this
    person's history is made of.
    """
    person = person_by_id(world, person_id)
    if person is None:
        return []

    others = set(person.lineage.parent_ids)
    for other in world.npcs:
        if person_id in other.lineage.parent_ids:
            others.add(other.id)
    for routine in world.routines:
        if (
            routine.kind not in SHARED_TIME_ROUTINE_KINDS
            or routine.target_person_id is None
        ):
            continue
        pair = {routine.actor_person_id, routine.target_person_id}
        if person_id in pair:
            others |= pair - {person_id}

    ties = [relationship_between(world, person_id, other) for other in sorted(others)]
    return [tie for tie in ties if tie is not None]
