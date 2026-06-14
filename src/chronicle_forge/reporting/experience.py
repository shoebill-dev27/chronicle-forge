"""P7-1 Dead Summary — the human experience at the end of a life.

Read-only. This is a *presentation* layer (P7): it changes no game state and
adds no new aggregation that the reporting data layer does not already provide.
It reuses ``_data.py`` (per-life accessors) and ``labels.py`` (deterministic
human phrases), and the shared causal graph, to translate a finished life into
second-person prose.

The goal is not "what you did" but "what outlived you": every line reads as
cause -> consequence (Count -> Event -> Consequence), never a bare statistic.
"""

from __future__ import annotations

from typing import Optional

from ..causal import CausalGraph
from ..enums import HeritageType, MemoryType, Talent
from ..models import Life, World
from ._data import heritage_rows, place, seeds_of_life, triggered_node
from .labels import event_phrase, seed_label

# How the player's strongest memory of a person reads in second person.
_MEMORY_VERB = {
    MemoryType.SAVED: "saved",
    MemoryType.RESCUED: "rescued",
    MemoryType.EDUCATED: "taught",
    MemoryType.BETRAYED: "betrayed",
    MemoryType.BEREAVED: "grieved with",
    MemoryType.HUMILIATED: "humbled",
}


def _age_at_death(life: Life) -> int:
    """The player's age when this life ended (a human lifespan reads more
    naturally than the active-span). Falls back to the current age for a life
    that has not formally ended yet. Causal span is a separate future field."""
    return life.age_at_death if life.age_at_death is not None else life.age


def _npc_name(world: World, npc_id: str) -> Optional[str]:
    return next((n.name for n in world.npcs if n.id == npc_id), None)


def _strongest_bond(world: World, life: Life):
    """The player's most intense memory of a person formed during this life.
    Returns (verb, npc_name, distinct_people) or None."""
    end = life.death_year if life.death_year is not None else world.current_year
    npc_ids = {n.id for n in world.npcs}
    mine = [
        m
        for m in world.memories
        if m.actor_id == world.player.id
        and m.subject_id in npc_ids
        and life.birth_year <= m.timestamp <= end
    ]
    if not mine:
        return None
    mine.sort(key=lambda m: (-m.intensity, m.id))
    top = mine[0]
    name = _npc_name(world, top.subject_id) or "a stranger"
    verb = _MEMORY_VERB.get(top.type, "touched the life of")
    people = len({m.subject_id for m in mine})
    return verb, name, people


def _longest_thread(world: World, life: Life):
    """This life's fired seed whose founding event has the most downstream
    events. Returns (seed, event, downstream_count) or None."""
    graph = CausalGraph.from_world(world)
    best = None
    for seed in seeds_of_life(world, life.id):
        if not seed.fired:
            continue
        event = triggered_node(world, seed.id)
        if event is None:
            continue
        downstream = len(graph.descendants(event.id))
        key = (downstream, seed.id)
        if best is None or key > best[0]:
            best = (key, seed, event, downstream)
    if best is None:
        return None
    _, seed, event, downstream = best
    return seed, event, downstream


def _top_legacy(world: World, life: Life):
    """The highest-scoring Heritage promoted from this life's seeds, as a
    reporting row (name/longevity/origin_action). Returns the row or None."""
    seed_ids = {s.id for s in seeds_of_life(world, life.id)}
    mine = [r for r in heritage_rows(world) if r["source_seed"] in seed_ids]
    return mine[0] if mine else None  # heritage_rows is already score-sorted


def _title(world: World, life: Life) -> str:
    if life.summary and life.summary.title:
        return life.summary.title
    talent = life.talent.value if life.talent else "soul"
    return f"The {talent.capitalize()} of {place(world)}"


def dead_summary(world: World, life: Life) -> str:
    """Render the second-person death screen for one finished life. Read-only."""
    years = _age_at_death(life)
    lines = [f"─ {_title(world, life)} ─"]
    lines.append(
        "You lived a single season." if years == 0 else f"You lived {years} years."
    )
    lines.append("")

    # 3. The person who mattered most.
    bond = _strongest_bond(world, life)
    if bond is not None:
        verb, name, people = bond
        line = f"You {verb} {name}."
        if people > 1:
            line += f" In all, your choices fell across {people} lives."
        lines.append(line)

    # 2/4. What took root (framed as consequence, not a seed count).
    seeds = seeds_of_life(world, life.id)
    fired = [s for s in seeds if s.fired]
    heritage_count = len(_legacy_seed_ids(world, life))
    if heritage_count == 1:
        lines.append("One of the ideas you planted took root and outlived you.")
    elif heritage_count > 1:
        lines.append(
            f"{_cap_number(heritage_count)} of the ideas you planted took root "
            "and outlived you."
        )
    elif fired:
        n = len(fired)
        what = "seed" if n == 1 else "seeds"
        lines.append(
            f"{_cap_number(n)} of the {what} you planted stirred the world before you went."
        )

    # 5/6. The longest causal thread and the enduring legacy. When the thread's
    # seed IS the top legacy's seed, the two are merged into one line so the
    # action phrase is never repeated.
    thread = _longest_thread(world, life)
    legacy = _top_legacy(world, life)
    legacy_seed = legacy["source_seed"] if legacy else None
    merged = thread is not None and legacy is not None and thread[0].id == legacy_seed

    if thread is not None and not merged:
        seed, event, downstream = thread
        tail = (
            "and nothing came after — yet"
            if downstream == 0
            else f"and {downstream} {'event' if downstream == 1 else 'events'} followed from it"
        )
        lines.append(
            f"You set out to {seed_label(world, seed.id)}; {event_phrase(event)}, {tail}."
        )

    lines.append("")
    if legacy is not None:
        longevity = legacy["longevity"]
        when = "within a lifetime" if longevity <= 0 else f"{longevity} years on"
        ripple = ""
        if merged and thread[2]:
            downstream = thread[2]
            ripple = (
                f" It set {downstream} "
                f"{'event' if downstream == 1 else 'events'} in motion, and"
            )
        lines.append("What outlived you?")
        lines.append(
            f"  You chose to {legacy['origin_action']}.{ripple} {when} "
            f"\"{legacy['name']}\" still endured."
        )
    else:
        lines.append(
            "Nothing you built survived long after your death. "
            "Yet the world remembered your passing."
        )

    return "\n".join(lines)


def _legacy_seed_ids(world: World, life: Life) -> set:
    seed_ids = {s.id for s in seeds_of_life(world, life.id)}
    return {h.seed_id for h in world.heritage if h.seed_id in seed_ids}


_NUMBER_WORDS = {
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
}


def _cap_number(n: int) -> str:
    return _NUMBER_WORDS.get(n, str(n))


# --- P7-2 Chronicle Generator -------------------------------------------
#
# Not a summary of the death screen: a *historical* retelling (third person,
# template-based, no LLM) that translates a life's causality into history in the
# order Count -> Event -> Consequence -> Legacy. Reuses the same per-life
# accessors as the Dead Summary; adds no new aggregation.

_ROLE = {
    Talent.SCHOLAR: "scholar",
    Talent.WARRIOR: "warrior",
    Talent.MERCHANT: "merchant",
    Talent.STATESMAN: "statesman",
    Talent.MENTOR: "teacher",
    Talent.EXPLORER: "wanderer",
    Talent.PRIEST: "priest",
    Talent.BUILDER: "builder",
}

# The noun for "what they left", by the heritage type that endured.
_WORK_NOUN = {
    HeritageType.SCHOOL: "teachings",
    HeritageType.THOUGHT: "teachings",
    HeritageType.HEIR: "line",
    HeritageType.TECHNOLOGY: "craft",
    HeritageType.INSTITUTION: "order",
    HeritageType.MONUMENT: "work",
}


def life_chronicle(world: World, life: Life) -> str:
    """Render a finished life as a short third-person history (3-10 lines).

    Read-only and deterministic. Translates causality into history rather than
    narrating statistics: a defining act, what it set in motion, and the legacy
    that outlived the life (or an honest closing when none did)."""
    role = _ROLE.get(life.talent, "wanderer")
    dom = world.theme.dominant
    era = f", in an age of {dom.value}" if dom is not None else ""
    lines = [f"They lived as a {role} of {place(world)}{era}."]

    thread = _longest_thread(world, life)
    bond = _strongest_bond(world, life)
    legacy = _top_legacy(world, life)

    # The defining act -> the event it set in motion (Event).
    if thread is not None:
        seed, event, downstream = thread
        lines.append(
            f"They chose to {seed_label(world, seed.id)}, and {event_phrase(event)}."
        )
        if downstream >= 3:  # Consequence (softly, not a raw count)
            lines.append(
                "What began with them rippled on through the years that followed."
            )
    elif bond is not None:
        verb, name, _ = bond
        lines.append(f"They {verb} {name}, and were not forgotten for it.")

    # Legacy (Count -> Event -> Consequence -> Legacy closes here).
    if legacy is not None:
        her_type = next(
            (h.type for h in world.heritage if h.seed_id == legacy["source_seed"]),
            None,
        )
        work = _WORK_NOUN.get(her_type, "work")
        lines.append(f"Their {work} spread beyond their own lifetime.")
        longevity = legacy["longevity"]
        when = "Generations later" if longevity >= 20 else f"{longevity} years later"
        lines.append(f"{when}, \"{legacy['name']}\" still bore their mark.")
    elif bond is not None:
        lines.append("Little of what they touched outlasted the age,")
        lines.append("yet the world marked their passing and moved on.")
    else:
        lines.append("They left no lasting mark, and the age closed over them.")

    return "\n".join(lines)
