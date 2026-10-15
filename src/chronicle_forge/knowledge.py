"""What a person knows: discrete, person-owned, and only ever first-hand.

One kind of truth lives here — *this tracked person knows that this thing
happened*. Nothing more. There is no confidence, no certainty, no intensity,
no importance, no valence and no count of how much anybody knows. The engine
cannot measure those, and a number it cannot measure is a fiction with a
decimal point.

Three rules shape it.

* **Knowledge belongs to the person, not the player.** Player continuity is
  not knowledge continuity: what Ashlin learned, Ashlin knows. The successor
  is a different person and starts knowing nothing, however many lives the
  soul has had.
* **It is a reference, never a copy.** A row names a ``CausalNode`` by id. The
  event's own title, year, place and actors stay in ``world.causal_nodes``,
  where they are already true.
* **Only being there establishes it.** A person knows an event because the
  observation rule (``play.view.observed_events``) found them where it
  happened. Being somebody's parent does not transmit knowledge. Spending
  twenty years beside them does not either. Telling, teaching and overhearing
  are a later unit, and this module is written so that adding them means
  adding a :class:`~.enums.KnowledgeSource` member — not a second notion of
  what knowing is.

What is stored is the registry; what is derived is nothing. Unlike
:mod:`relationship` and :mod:`routine_origin`, this *cannot* be a projection:
who was present for what is not recoverable after the fact from a world that
records no attendance. So it is written once, when it happens, and kept.
"""

from __future__ import annotations

from typing import List, Optional

from .enums import KnowledgeSource
from .models import CausalNode, PersonKnowledge, World
from .population import person_by_id


class KnowledgeRefused(Exception):
    """The world will not record this, because it would not be true — no such
    person, or no such event. Refused rather than invented: knowledge of a
    thing that did not happen is the one thing this registry must never hold.
    """


# --- reading ---------------------------------------------------------------


def knows(world: World, person_id: str, event_id: str) -> bool:
    """Whether this person knows this event happened."""
    return any(
        k.person_id == person_id and k.event_id == event_id for k in world.knowledge
    )


def knowledge_of(world: World, person_id: str) -> List[PersonKnowledge]:
    """Everything this person came to know, in the order they came to know it.

    Works for the dead, which is the point: what somebody knew in their life
    is history, and history does not stop being true when they stop. An
    unknown person simply knows nothing, the same way
    ``relationship.relationships_of`` says nothing about a stranger.
    """
    return [k for k in world.knowledge if k.person_id == person_id]


def known_events(world: World, person_id: str) -> List[CausalNode]:
    """The events themselves, read back through the references."""
    known = {k.event_id for k in knowledge_of(world, person_id)}
    return [node for node in world.causal_nodes if node.id in known]


def who_knows(world: World, event_id: str) -> List[str]:
    """Every person who knows this event, by id, in the order they learned."""
    return [k.person_id for k in world.knowledge if k.event_id == event_id]


# --- writing ---------------------------------------------------------------


def learn(
    world: World,
    person_id: str,
    event_id: str,
    source: KnowledgeSource = KnowledgeSource.OBSERVED,
) -> Optional[PersonKnowledge]:
    """Record that this person now knows this event, if they did not already.

    Returns the new row, or ``None`` when they already knew — learning the
    same thing twice is not two pieces of knowledge, and the year they first
    knew is not overwritten by the second time they saw it.
    """
    if person_by_id(world, person_id) is None:
        raise KnowledgeRefused(f"{person_id} is not in the registry")
    event = next((n for n in world.causal_nodes if n.id == event_id), None)
    if event is None:
        raise KnowledgeRefused(f"{event_id} is not something that happened")
    if knows(world, person_id, event_id):
        return None
    row = PersonKnowledge(
        person_id=person_id,
        event_id=event_id,
        # Somebody who was there knew it the year it happened, whatever year
        # the session got around to telling them about it — so a ten-year
        # ``continue`` and ten one-year ones record the same years. A later
        # source (being told) would be the year of the telling instead.
        learned_year=(
            event.year if source is KnowledgeSource.OBSERVED else world.current_year
        ),
        source=source,
    )
    world.knowledge.append(row)
    return row
