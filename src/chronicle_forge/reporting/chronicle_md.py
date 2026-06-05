"""chronicle.md: facts-only world report (no prose narrative).

Sections: Overview, Lives, Major Events, Heritage, Wild Cards, Why this Ending.
Why-this-Ending explains the chain Ending <- Event <- Seed <- Life.
"""

from __future__ import annotations

from .. import config
from ..causal import CausalGraph
from ..enums import EventScale
from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import (
    SCALE_ORDER,
    activity_counts,
    heritage_rows,
    life_index,
    life_label,
    life_world_impact,
    place,
)


def _overview(world: World) -> str:
    alive = sum(1 for n in world.npcs if n.alive)
    return "\n".join(
        [
            "## World Overview",
            "",
            f"- **World:** {place(world)} (seed {world.seed})",
            f"- **Span:** {world.current_year} years (of {world.max_year})",
            f"- **Ending:** {world.ending_class}",
            f"- **Dominant theme:** {world.theme.dominant.value if world.theme.dominant else '—'}",
            f"- **Lives:** {len(world.lives)} | **Events:** {len(world.causal_nodes)} "
            f"| **Heritage:** {len(world.heritage)} | **NPCs alive:** {alive}/{len(world.npcs)}",
        ]
    )


def _lives(world: World) -> str:
    lines = [
        "## The Reincarnator's Lives",
        "",
        "| # | Title | Talent | Lived | Activities | World impact |",
        "|---|---|---|---|---|---|",
    ]
    idx = life_index(world)
    for life in world.lives:
        s = life.summary
        acts = activity_counts(life)
        lines.append(
            f"| {idx[life.id]} | {s.title if s else life.id} "
            f"| {life.talent.value if life.talent else '—'} "
            f"| y{life.birth_year}–y{life.death_year} ({life.death_cause.value if life.death_cause else '—'}) "
            f"| {acts} | {life_world_impact(world, life.id)} events |"
        )
    return "\n".join(lines)


def _major_events(world: World) -> str:
    lines = ["## How the World Turned (major events)", ""]
    major = [
        n
        for n in world.causal_nodes
        if n.scale in (EventScale.LARGE, EventScale.MEDIUM)
    ]
    major.sort(key=lambda n: (n.year, SCALE_ORDER[n.scale], n.id))
    for n in major:
        tag = "**" if n.scale == EventScale.LARGE else ""
        lines.append(f"- y{n.year:>2} [{n.scale.value}] {tag}{n.title}{tag}")
    return "\n".join(lines)


def _heritage(world: World) -> str:
    lines = ["## Legacies (heritage)", ""]
    rows = heritage_rows(world, top=5)
    if not rows:
        lines.append("_No enduring heritage formed._")
        return "\n".join(lines)
    for i, r in enumerate(rows, 1):
        lines.append(
            f"{i}. **\"{r['name']}\"** ({r['type']}, `{r['source_seed']}`, "
            f"{r['origin_life']}) — score {r['score']}, {r['longevity']}y, "
            f"reach {r['reach']}, {r['derived_events']} downstream events"
        )
    return "\n".join(lines)


def _wildcards(world: World) -> str:
    lines = ["## Wild Cards", ""]
    any_active = False
    for wc in world.wildcards.wildcards:
        if wc.status.value == "dormant":
            continue
        any_active = True
        lines.append(f"- **{wc.name}** the {wc.archetype.value} — {wc.status.value}")
        events = sorted(
            (n for n in world.causal_nodes if wc.id in n.actors),
            key=lambda n: n.year,
        )
        for n in events:
            lines.append(f"    - y{n.year} {n.title}")
    if not any_active:
        lines.append("_No wild card rose to prominence._")
    return "\n".join(lines)


def why_this_ending_md(world: World) -> str:
    graph = CausalGraph.from_world(world)
    dom = world.theme.dominant
    ec = world.ending_class
    lines = [
        "## Why this Ending",
        "",
        f"The world ended as the **{ec}**, set by a final dominant theme of "
        f"*{dom.value if dom else '—'}*. That tilt traces back through events to "
        f"the lives that caused it:",
        "",
    ]
    window = config.THEME_EVENT_WINDOW
    candidates = [
        n
        for n in world.causal_nodes
        if dom is not None
        and SEED_DOMAIN_TO_THEME[n.domain] == dom
        and 0 <= world.current_year - n.year < window
    ]
    candidates.sort(key=lambda n: (SCALE_ORDER[n.scale], -n.year, n.id))
    if not candidates:
        lines.append(
            "- (the final theme rests on accumulated structure, not a single recent event)"
        )
        return "\n".join(lines)
    for n in candidates[:3]:
        players = graph.player_seeds_in_ancestry(n.id)
        if players:
            s = players[0]
            lines.append(
                f"- **{ec}** ⇐ y{n.year} *{n.title}* ⇐ `{s.id}` ({s.domain.value}) "
                f"⇐ {life_label(world, s.planted_by_life_id)}"
            )
        else:
            lines.append(f"- **{ec}** ⇐ y{n.year} *{n.title}* ⇐ (world forces)")
    return "\n".join(lines)


def chronicle_report_md(world: World) -> str:
    return (
        "\n\n".join(
            [
                f"# Chronicle of {place(world)} — {world.ending_class} (Seed {world.seed})",
                _overview(world),
                _lives(world),
                _major_events(world),
                _heritage(world),
                _wildcards(world),
                why_this_ending_md(world),
            ]
        )
        + "\n"
    )
