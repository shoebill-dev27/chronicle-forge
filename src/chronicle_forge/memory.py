"""Memory formation (section 7.1).

Memories are structured records (not natural language). Forming one updates the
subject NPC's relation toward the actor, which later feeds the NPC utility
function (section 6.3).
"""

from __future__ import annotations

from typing import Optional

from .enums import MemoryType
from .ids import next_id
from .models import Memory, Relation, World


def _clamp_signed(value: int) -> int:
    return max(-100, min(100, value))


def form_memory(
    world: World,
    subject_id: str,
    actor_id: str,
    mtype: MemoryType,
    valence: int,
    intensity: int,
    decay_rate: float = 0.05,
    event_ref: Optional[str] = None,
) -> Memory:
    """Create a memory and update the subject NPC's relation toward the actor."""
    memory = Memory(
        id=next_id("mem", world.memories),
        subject_id=subject_id,
        actor_id=actor_id,
        type=mtype,
        valence=_clamp_signed(valence),
        intensity=max(0, min(100, intensity)),
        decay_rate=decay_rate,
        event_ref=event_ref,
        timestamp=world.current_year,
    )
    world.memories.append(memory)

    subject = next((n for n in world.npcs if n.id == subject_id), None)
    if subject is not None:
        relation = subject.relations.get(actor_id, Relation())
        relation.affinity = _clamp_signed(relation.affinity + valence // 2)
        relation.trust = _clamp_signed(relation.trust + valence // 4)
        if valence < 0:
            relation.fear = _clamp_signed(relation.fear - valence // 4)
        subject.relations[actor_id] = relation

    return memory
