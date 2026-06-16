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

# How the enduring-legacy line closes. Chosen deterministically from the
# legacy's own seed id, so the same life always reads the same way while
# different lives do not all end on the identical phrase.
_LEGACY_CLOSERS = (
    "still bore their mark.",
    "still carried their name.",
    "still remembered their work.",
    "still echoed their choices.",
)


def _legacy_closer(key: str) -> str:
    """Deterministic, hash-seed-independent pick over ``_LEGACY_CLOSERS``."""
    return _LEGACY_CLOSERS[sum(ord(c) for c in key) % len(_LEGACY_CLOSERS)]


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
        legacy_seed = legacy["source_seed"]
        her_type = next(
            (h.type for h in world.heritage if h.seed_id == legacy_seed),
            None,
        )
        work = _WORK_NOUN.get(her_type, "work")
        # When the enduring legacy grew from a thread other than the defining
        # act above, bridge the two so the history reads as one life rather
        # than a jump between unrelated deeds.
        if thread is not None and thread[0].id != legacy_seed:
            lines.append("Though their path wandered elsewhere, one legacy endured.")
        lines.append(f"Their {work} spread beyond their own lifetime.")
        longevity = legacy["longevity"]
        when = "Generations later" if longevity >= 20 else f"{longevity} years later"
        closer = _legacy_closer(legacy_seed)
        lines.append(f'{when}, "{legacy["name"]}" {closer}')
    elif bond is not None:
        lines.append("Little of what they touched outlasted the age,")
        lines.append("yet the world marked their passing and moved on.")
    else:
        lines.append("They left no lasting mark, and the age closed over them.")

    return "\n".join(lines)


# --- P7-3 Historical Timeline -------------------------------------------
#
# Player-facing Markdown (a *reading*, not a developer table): one life placed
# on a single world-year axis across three layers — the life's own acts, the
# ripples those acts sent through the world, and the legacy that outlived them.
# Third person, deterministic, read-only, reusing the same accessors as
# P7-1/P7-2.
#
# A subtlety the raw data forces (see P7-3 review): a seed is *planted* during
# the life but its consequence *fires* years later, often after death. So the
# axis is world-years throughout (the only axis the three layers share — the
# player's personal age would not align), and the layers are split by causality:
#   - Their life          : the player's ACTS, by planted year, within lifespan.
#   - The world around them: the resulting EVENTS (ripples), by event year.
#   - What outlived them   : the enduring LEGACIES, which run past death on purpose.
# Each layer is de-duplicated by phrase/name and capped, so the reading stays a
# reading rather than an event log.

_LAYER_CAP = 3  # most-consequential entries shown per layer


def _cap(text: str) -> str:
    """Capitalize the first letter of a verb-phrase for a sentence opening."""
    return text[:1].upper() + text[1:] if text else text


def _seed_records(world: World, life: Life):
    """For each fired seed of this life: (planted_year, act_phrase, event_year,
    ripple_phrase, downstream). The shared basis for the act and ripple layers."""
    graph = CausalGraph.from_world(world)
    records = []
    for seed in seeds_of_life(world, life.id):
        if not seed.fired:
            continue
        event = triggered_node(world, seed.id)
        if event is None:
            continue
        records.append(
            (
                seed.planted_year,
                seed_label(world, seed.id),
                event.year,
                event_phrase(event),
                len(graph.descendants(event.id)),
            )
        )
    return records


def _top_by_phrase(items, year_idx: int, phrase_idx: int, weight_idx: int):
    """De-duplicate ``items`` by their phrase (keeping the heaviest), take the
    top ``_LAYER_CAP`` by weight, and return them sorted by year. Deterministic."""
    best: dict = {}
    for it in items:
        phrase = it[phrase_idx]
        if phrase not in best or it[weight_idx] > best[phrase][weight_idx]:
            best[phrase] = it
    chosen = sorted(best.values(), key=lambda it: (-it[weight_idx], it[year_idx]))
    chosen = chosen[:_LAYER_CAP]
    return sorted(chosen, key=lambda it: it[year_idx])


def _life_legacies(world: World, life: Life) -> list:
    """Heritage rows promoted from this life's seeds, de-duplicated by name and
    capped, score-sorted (heritage_rows is already score-ordered)."""
    seed_ids = {s.id for s in seeds_of_life(world, life.id)}
    rows, seen = [], set()
    for r in heritage_rows(world):
        if r["source_seed"] in seed_ids and r["name"] not in seen:
            seen.add(r["name"])
            rows.append(r)
        if len(rows) >= _LAYER_CAP:
            break
    return rows


def life_timeline(world: World, life: Life) -> str:
    """Render a finished life as a player-facing Markdown timeline. Read-only.

    Three layers share one world-year axis: the life's acts, the ripples they
    sent through the world, and the legacy that outlived them (which may extend
    past the death year — the life ends, the history does not)."""
    role = _ROLE.get(life.talent, "wanderer")
    dom = world.theme.dominant
    era = f", in an age of {dom.value}" if dom is not None else ""
    birth = life.birth_year
    death = life.death_year if life.death_year is not None else world.current_year
    age = _age_at_death(life)

    out = [f"# A {role} of {place(world)}", ""]
    span = "a single season" if age == 0 else f"{age} years"
    out.append(
        f"> A {role} who lived {span}{era}."
        if dom is not None
        else f"> A {role} who lived {span}."
    )
    out.append("")

    records = _seed_records(world, life)

    # --- Their life: born -> the player's acts (planted) -> died ---
    acts = _top_by_phrase(records, year_idx=0, phrase_idx=1, weight_idx=4)
    out.append("## Their life")
    personal = [(birth, 0, f"Born into {place(world)}{era}.")]
    for planted_year, act, _ev_year, _ripple, _down in acts:
        personal.append((planted_year, 1, f"They {act}."))
    personal.append(
        (
            death,
            2,
            (
                "They died young, a single season lived."
                if age == 0
                else "They died, their work passing out of their hands."
            ),
        )
    )
    personal.sort(key=lambda r: (r[0], r[1]))
    for year, _, text in personal:
        out.append(f"- **Year {year}** — {text}")

    # --- The world around them: the ripples those acts sent outward ---
    ripples = _top_by_phrase(records, year_idx=2, phrase_idx=3, weight_idx=4)
    if ripples:
        out.append("")
        out.append("## The world around them")
        for _planted, _act, ev_year, ripple, _down in ripples:
            out.append(f"- **Year {ev_year}** — {_cap(ripple)}.")

    # --- What outlived them: the legacy, allowed to run past the death year ---
    out.append("")
    out.append("## What outlived them")
    legacies = _life_legacies(world, life)
    if legacies:
        rows = []
        for r in legacies:
            founding = triggered_node(world, r["source_seed"])
            base = founding.year if founding is not None else death
            endured_year = base + max(r["longevity"], 0)
            rows.append((endured_year, r))
        rows.sort(key=lambda x: (x[0], x[1]["name"]))
        for endured_year, r in rows:
            past = endured_year - death
            if past > 0:
                tail = f', {past} {"year" if past == 1 else "years"} past their death'
            else:
                tail = ", already taking root before they were gone"
            out.append(
                f'- **Year {endured_year}** — "{r["name"]}" still endured{tail}.'
            )
    else:
        out.append(
            "- Nothing they built outlasted the age — yet the world "
            "marked their passing."
        )

    return "\n".join(out)


# --- P7-4 Legacy View ---------------------------------------------------
#
# The catalogue of "What outlived you?" — Chronicle Forge's core question.
# Where P7-1 summarizes and P7-3 lays out a time axis, P7-4 is the inventory of
# the marks a single life left on the world, in the order Count -> Consequence
# -> Continuity: the works that endured, the people and discoveries that carried
# them, and the theme that went on shaping the world after death. Second person,
# read-only, deterministic. heritage_rows is the primary source.

# What a promoted heritage *was*, as a human noun (not a type code). THOUGHT is
# refined by its seed domain so a faith doctrine reads as a religious tradition.
_HERITAGE_NOUN = {
    HeritageType.SCHOOL: "A school of learning",
    HeritageType.THOUGHT: "A tradition of thought",
    HeritageType.TECHNOLOGY: "A craft",
    HeritageType.INSTITUTION: "An institution of rule",
    HeritageType.HEIR: "A bloodline",
    HeritageType.MONUMENT: "A monument",
}

# How a person you touched carries you forward, by the memory that bound them.
_PEOPLE_LINE = {
    MemoryType.EDUCATED: "{name} carried your teachings into the next age.",
    MemoryType.SAVED: "{name} lived because of you, and never forgot it.",
    MemoryType.RESCUED: "{name} owed you their life, and said so to others.",
    MemoryType.BETRAYED: "{name} never forgot how you wronged them.",
    MemoryType.BEREAVED: "{name} grieved at your side, and remembered you.",
    MemoryType.HUMILIATED: "{name} carried the mark of your defiance.",
}

# One continuity line per discovery flavour (Count -> Consequence).
_DISCOVERY_LINE = {
    "tech": "Techniques you uncovered passed into common use.",
    "relic": "Relics you brought to light outlived you.",
    "seal": "What you unsealed could never be closed again.",
    "lore": "Knowledge you recovered shaped what others believed.",
}
_DISCOVERY_FALLBACK = "Your journeys opened paths that others followed."

# How an inherited world-theme reads as it goes on after a death.
_THEME_NOUN = {
    "faith": "Faith",
    "warfare": "War",
    "innovation": "Innovation",
    "commerce": "Commerce",
    "governance": "The rule of law",
    "culture": "Culture",
}


def _heritage_sentence(row: dict) -> str:
    """Prose for one heritage row: what it was, how long it lasted, how far it
    reached — numbers folded into a sentence, never a bare list."""
    her_type = next((t for t in HeritageType if t.value == row["type"]), None)
    noun = _HERITAGE_NOUN.get(her_type, "A legacy")
    if her_type is HeritageType.THOUGHT and row.get("domain") == "faith":
        noun = "A religious tradition"
    longevity = row["longevity"]
    span = (
        "that took root within a lifetime"
        if longevity <= 0
        else f"that endured for {longevity} {'year' if longevity == 1 else 'years'}"
    )
    reach = row["reach"] or row["derived_events"]
    touch = (
        ""
        if reach <= 0
        else f" and touched {reach} later {'event' if reach == 1 else 'events'}"
    )
    return f"{noun} {span}{touch}."


def _legacy_people(world: World, life: Life) -> list:
    """Up to three people this life marked most, strongest bond first, each as
    (memory_type, npc_name). Deterministic."""
    end = life.death_year if life.death_year is not None else world.current_year
    names = {n.id: n.name for n in world.npcs}
    mine = [
        m
        for m in world.memories
        if m.actor_id == world.player.id
        and m.subject_id in names
        and life.birth_year <= m.timestamp <= end
    ]
    mine.sort(key=lambda m: (-m.intensity, m.id))
    seen, out = set(), []
    for m in mine:
        if m.subject_id in seen:
            continue
        seen.add(m.subject_id)
        out.append((m.type, names[m.subject_id]))
        if len(out) >= 3:
            break
    return out


def _legacy_discoveries(world: World, life: Life) -> list:
    """Discovery types that grew from this life's seeds, earliest-id first."""
    seed_ids = {s.id for s in seeds_of_life(world, life.id)}
    discs = [d for d in world.discoveries if d.seed_id in seed_ids]
    discs.sort(key=lambda d: d.id)
    return discs


def legacy_view(world: World, life: Life) -> str:
    """Render the "What outlived you?" inventory for one life. Read-only.

    A trace, not an achievements screen: heritages that endured, the people and
    discoveries that carried them, and the theme that shaped the world after
    death — Count -> Consequence -> Continuity, in second person."""
    out = ["# What outlived you?", ""]

    legacies = _life_legacies(world, life)
    people = _legacy_people(world, life)
    discoveries = _legacy_discoveries(world, life)
    dom = world.theme.dominant

    if not legacies and not people and not discoveries:
        out.append(
            "Little of what you touched outlasted the age. Yet the world "
            "marked your passing, and went on."
        )
        return "\n".join(out)

    # 1. Heritage — the works that endured (Count).
    if legacies:
        out.append("## What you built")
        for row in legacies:
            out.append(f'**"{row["name"]}"**')
            out.append(_heritage_sentence(row))
            out.append("")
        if out[-1] == "":
            out.pop()

    # 2. People — who carried it forward (Consequence).
    if people:
        out.append("")
        out.append("## Who carried it")
        for mem_type, name in people:
            line = _PEOPLE_LINE.get(mem_type, "{name} remembered you.")
            out.append(f"- {line.format(name=name)}")

    # 3. Discoveries — the paths you opened (Consequence).
    if discoveries:
        out.append("")
        out.append("## What you opened")
        types = []
        for d in discoveries:
            if d.type.value not in types:
                types.append(d.type.value)
        if len(types) == 1:
            out.append(f"- {_DISCOVERY_LINE.get(types[0], _DISCOVERY_FALLBACK)}")
        else:
            out.append(f"- {_DISCOVERY_FALLBACK}")

    # 4. Themes — the world's continuity after you (Continuity).
    if dom is not None:
        out.append("")
        out.append("## What the world became")
        noun = _THEME_NOUN.get(dom.value, dom.value.capitalize())
        out.append(f"- {noun} continued to shape the world after your death.")

    return "\n".join(out)
