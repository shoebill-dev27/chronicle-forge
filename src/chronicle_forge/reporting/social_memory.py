"""P10 Social Memory (L1) — the people who remember a soul across its lives.

A read-only projection of the social trace a soul leaves behind. Memories are
already attributed to the stable soul id (``Player.id``), so this only *surfaces*
existing data: for each NPC that holds a relation toward the soul, it reports how
they remember a past self and which life it traces to.

It mutates nothing, takes no engine flag, and never leaks an internal id — the
soul id (``player-0000``) and npc ids are internal; people are shown by name and
past selves by their "Life N" ordinal (the P8 lesson). Deterministic. Nothing
here touches the world, P6/P7/P8/P9-*, P10 Observatory, or the seed42 golden.
"""

from __future__ import annotations

from typing import List, NamedTuple, Optional

from ..enums import MemoryType
from ..models import Memory, World
from ._data import life_index


class SocialBond(NamedTuple):
    """One remembered bond, id-free. ``life_ordinal`` is the past self the memory
    traces to ("Life N"); the fields are the seam a future 3D client reads."""

    npc_name: str
    npc_tier: str
    life_ordinal: int
    affinity: int
    sentiment: str
    reason: str


_REASON = {
    MemoryType.SAVED: "you once saved their life",
    MemoryType.RESCUED: "you came to their rescue",
    MemoryType.EDUCATED: "you taught them what you knew",
    MemoryType.BEREAVED: "you stood with them in grief",
    MemoryType.BETRAYED: "you betrayed them",
    MemoryType.HUMILIATED: "you humiliated them",
}


def _sentiment(affinity: int, fear: int) -> str:
    if fear > 0 and fear >= affinity:
        return "warily"
    if affinity > 0:
        return "fondly"
    if affinity < 0:
        return "bitterly"
    return "distantly"


def _life_ordinal_for_year(world: World, year: int) -> int:
    """The 1-based ordinal of the life that was alive in ``year`` (the soul's
    self at the time the memory formed). Falls back to the most recent prior life
    so attribution is always a valid ordinal."""
    idx = life_index(world)
    for life in world.lives:
        end = life.death_year if life.death_year is not None else world.current_year
        if life.birth_year <= year <= end:
            return idx[life.id]
    prior = [lf for lf in world.lives if lf.birth_year <= year]
    if prior:
        return idx[max(prior, key=lambda lf: lf.birth_year).id]
    return 1 if world.lives else 0


def _strongest_memory(world: World, npc_id: str, soul: str) -> Optional[Memory]:
    held = [m for m in world.memories if m.subject_id == npc_id and m.actor_id == soul]
    if not held:
        return None
    return max(held, key=lambda m: (m.intensity, m.timestamp))


def social_memory_bonds(world: World) -> List[SocialBond]:
    """Every NPC that remembers the soul, as id-free ``SocialBond``s, sorted
    deterministically by warmth (``-affinity``) then name. Read-only."""
    soul = world.player.id
    bonds: List[SocialBond] = []
    for npc in world.npcs:
        relation = npc.relations.get(soul)
        if relation is None:
            continue
        memory = _strongest_memory(world, npc.id, soul)
        if memory is not None:
            ordinal = _life_ordinal_for_year(world, memory.timestamp)
            reason = _REASON.get(memory.type, "your paths crossed")
        else:
            ordinal = len(world.lives)
            reason = "your paths crossed"
        bonds.append(
            SocialBond(
                npc_name=npc.name,
                npc_tier=npc.tier.value,
                life_ordinal=ordinal,
                affinity=relation.affinity,
                sentiment=_sentiment(relation.affinity, relation.fear),
                reason=reason,
            )
        )
    bonds.sort(key=lambda b: (-b.affinity, b.npc_name))
    return bonds


def social_memory_view(world: World) -> str:
    """The people who remember you, as player-facing Markdown. Read-only and
    deterministic; never leaks an internal id (people by name, past selves by
    "Life N")."""
    bonds = social_memory_bonds(world)
    lines = ["# Who remembers you", ""]
    if not bonds:
        lines.append("> No one remembers you yet — your story has not begun.")
        return "\n".join(lines).rstrip() + "\n"

    lines.append(
        f"> Across {len(world.lives)} lives, {len(bonds)} "
        f"{'soul' if len(bonds) == 1 else 'souls'} still carry the memory of you."
    )
    lines.append("")
    for bond in bonds:
        lines.append(
            f"- **{bond.npc_name}** remembers you {bond.sentiment} — "
            f"{bond.reason}, from when you were Life {bond.life_ordinal}."
        )
    return "\n".join(lines).rstrip() + "\n"
