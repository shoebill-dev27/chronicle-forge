"""timeline.md: year-by-year flow of the world.

Per year: dominant theme, top-3 axes, wild card activity, and how many events
were recorded. Lets a reader see the world's arc at a glance.
"""

from __future__ import annotations

from ..models import World


def timeline_md(world: World) -> str:
    # Events per year.
    events_by_year: dict[int, int] = {}
    for n in world.causal_nodes:
        events_by_year[n.year] = events_by_year.get(n.year, 0) + 1

    # Wild card notes per year (ignition / stages), from wildcard-actor events.
    wc_notes: dict[int, list] = {}
    wc_ids = {wc.id: wc.name for wc in world.wildcards.wildcards}
    for n in world.causal_nodes:
        for actor in n.actors:
            if actor in wc_ids:
                wc_notes.setdefault(n.year, []).append(n.title)

    lines = [
        f"# World Timeline — Seed {world.seed}",
        "",
        "| Year | Dominant | Top axes | Events | Wild cards |",
        "|---|---|---|---|---|",
    ]
    for snap in world.theme.history:
        top = sorted(snap.axes.items(), key=lambda kv: -kv[1])[:3]
        top_str = ", ".join(f"{a.value} {v}" for a, v in top)
        dom = snap.dominant.value if snap.dominant else "—"
        ev = events_by_year.get(snap.year, 0)
        wc = "; ".join(wc_notes.get(snap.year, [])) or "—"
        lines.append(f"| {snap.year} | {dom} | {top_str} | {ev} | {wc} |")
    return "\n".join(lines) + "\n"
