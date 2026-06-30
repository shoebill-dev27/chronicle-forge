"""P14 Timeline Observatory (chronological Read-Model) — read-only time-axis projection.

A pure lens over a finished world's causal history that answers the orthogonal
question the significance-first lenses do not: **when did things happen?** It lays
every ``CausalNode`` the engine already recorded out on a single time axis, ordered
by year. Where P12 ``NarrativeView`` selects the top causal *threads* by
significance, P14 surfaces the **full event record** chronologically. It computes no
new history, invents no score, and infers no era: every entry is read straight off
an existing ``CausalNode`` / ``CausalGraph`` / ``World``.

``TimelineView`` is the single source of truth: ``timeline_json`` serializes it and
``timeline_markdown`` renders it. The Markdown renderer reads **only the view**,
never the world.

Boundaries (hard): read-only (never mutates the world), id-free (no seed / node /
life / npc id, no ``source_seed`` crosses the boundary — ``node.title`` embeds seed
ids so the curated ``labels.event_phrase`` is used instead; ``id`` / ``actors`` /
``caused_by`` never surface and ``location_id`` is humanised to a location *name*;
only ordinals, ``.value`` enums and curated label phrases surface), deterministic
(a total year order, no dict/set iteration leaks). It invents **no** score —
``domain`` / ``scale`` are the engine's own markers and ``player_driven`` is the
existing graph signal. It touches no engine / Recipe / World / persistence state and
moves no existing golden.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from ..causal import CausalGraph
from ..enums import EventScale
from ..models import CausalNode, World
from ._data import place
from .labels import event_phrase

# The complete public surface: the view contract types, the two builder entries,
# and the one renderer. Everything else in this module is a ``_``-prefixed internal.
__all__ = [
    "SCHEMA_VERSION",
    "TimelineEntryView",
    "TimelineView",
    "timeline_model",
    "timeline_json",
    "timeline_markdown",
]

# Read-model contract version — deliberately decoupled from ENGINE_VERSION.
SCHEMA_VERSION = "1"

# Engine significance order; the within-year tiebreak surfaces LARGE events first.
_SCALE_RANK = {EventScale.LARGE: 0, EventScale.MEDIUM: 1, EventScale.SMALL: 2}


class _View(BaseModel):
    """Base for every timeline record: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class TimelineEntryView(_View):
    """One event on the time axis — the per-event, id-free record."""

    ordinal: int  # 1-based chronological position — id-free
    year: int  # CausalNode.year
    title: str  # event_phrase(node) — id-free (never node.title)
    domain: str  # SeedDomain.value
    scale: str  # EventScale.value
    location: Optional[str]  # location NAME via world.locations | None — id-free
    player_driven: bool  # a player seed is among the event's causes (graph)


class TimelineView(_View):
    """The immutable, id-free chronological snapshot — the single source of truth."""

    schema_version: str
    place: str  # founding village name (id-free) | world id (_data.place)
    span: int  # world.current_year
    start_year: Optional[int]  # earliest event year | None (no events)
    end_year: Optional[int]  # latest event year | None (no events)
    event_count: int  # len(entries)
    entries: List[TimelineEntryView]


# --- builder: read the World, produce the structured records (internal) -------


def _sort_key(node: CausalNode):
    # Total order: chronological first, then a stable, meaningful within-year
    # tiebreak (significance, domain), and finally the (internal) node id so equal
    # (year, scale, domain) events are stable — the id is used only here and never
    # reaches the view (exactly P12's ``culmination_id`` pattern).
    return (node.year, _SCALE_RANK.get(node.scale, 99), node.domain.value, node.id)


# --- public API: builder (World -> TimelineView -> JSON) ----------------------


def timeline_model(world: World) -> TimelineView:
    """Project a finished world into the immutable, id-free ``TimelineView``.

    Read-only: it reads the causal nodes + graph + locations and composes them; it
    never mutates the world and is not a canonical/persistence source. ``entries``
    is every ``CausalNode`` in total chronological order."""
    graph = CausalGraph.from_world(world)
    loc_name: Dict[str, str] = {loc.id: loc.name for loc in world.locations}

    ordered = sorted(world.causal_nodes, key=_sort_key)
    entries = [
        TimelineEntryView(
            ordinal=i + 1,
            year=node.year,
            title=event_phrase(node),
            domain=node.domain.value,
            scale=node.scale.value,
            location=loc_name.get(node.location_id) if node.location_id else None,
            player_driven=bool(graph.player_seeds_in_ancestry(node.id)),
        )
        for i, node in enumerate(ordered)
    ]
    return TimelineView(
        schema_version=SCHEMA_VERSION,
        place=place(world),
        span=world.current_year,
        start_year=entries[0].year if entries else None,
        end_year=entries[-1].year if entries else None,
        event_count=len(entries),
        entries=entries,
    )


def timeline_json(world: World) -> str:
    """The canonical JSON encoding of the timeline read-model — the client contract
    and the basis of the frozen seed42 hash."""
    return timeline_model(world).model_dump_json()


# --- public API: renderer (TimelineView -> Markdown; never reads the World) ---


def timeline_markdown(view: TimelineView) -> str:
    """Render a ``TimelineView`` as Markdown. A **pure renderer**: it reads only the
    view (never the world) and returns deterministic, id-free prose grouped by year."""
    lines = ["# Timeline", ""]
    lines.append(f"> {view.place} — {view.span} years, {view.event_count} events.")
    lines.append("")

    if not view.entries:
        lines.append("No events recorded.")
        return "\n".join(lines).rstrip() + "\n"

    current_year: Optional[int] = None
    for e in view.entries:
        if e.year != current_year:
            current_year = e.year
            lines.append(f"## Year {e.year}")
        where = f" @ {e.location}" if e.location else ""
        driven = ", player-driven" if e.player_driven else ""
        lines.append(f"- {e.title}{where} ({e.domain}, {e.scale}{driven})")

    return "\n".join(lines).rstrip() + "\n"
