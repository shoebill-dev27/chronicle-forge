"""P12 Emergent Narrative Observatory — read-only narrative projection.

A pure lens over a finished world's causal history. It surfaces the *emergent
narrative* the engine already produced:

- **threads** — the top causal stories, each running from an origin (a player
  life, or "world forces") to a **culmination** (a ``LARGE`` event or a promoted
  ``HeritageNode``'s founding event), with the chain's span and length;
- **turning points** — the pivotal ``LARGE`` events history turned on.

``NarrativeView`` is the single source of truth: ``narrative_json`` serializes it
and ``narrative_markdown`` renders it. The Markdown renderer reads **only the view**,
never the world.

Boundaries (hard): read-only (never mutates the world), id-free (no seed / node /
life / npc / player id, no ``source_seed`` crosses the boundary — only ordinals and
the curated label phrases from ``labels.py`` surface), deterministic (every order is
a total order; no dict/set iteration leaks). It invents **no** score — significance
is read from the engine's own markers (``EventScale.LARGE``, ``HeritageNode``). It
touches no engine/Recipe/World state and moves no existing golden.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict

from ..causal import CausalGraph
from ..enums import EventScale
from ..models import CausalNode, World
from ._data import life_label, place, triggered_node
from .labels import event_phrase, heritage_name

# The complete public surface: the view contract types, the two builder entries,
# and the one renderer. Everything else in this module is a ``_``-prefixed internal.
__all__ = [
    "SCHEMA_VERSION",
    "DEFAULT_MAX_THREADS",
    "NarrativeView",
    "ThreadView",
    "TurningPointView",
    "narrative_model",
    "narrative_json",
    "narrative_markdown",
]

# Read-model contract version — deliberately decoupled from ENGINE_VERSION.
SCHEMA_VERSION = "1"

# MVP legibility cap; a render concern (which threads to show), never new truth.
DEFAULT_MAX_THREADS = 7

# Engine significance order; LARGE culminations lead the narrative.
_SCALE_RANK = {EventScale.LARGE: 0, EventScale.MEDIUM: 1, EventScale.SMALL: 2}


class _View(BaseModel):
    """Base for every narrative record: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ThreadView(_View):
    """One emergent story: origin -> consequences -> culmination."""

    ordinal: int  # 1-based, by canonical significance order
    title: str  # culmination phrase (heritage name or event phrase) — id-free
    origin: str  # "Life N (title)" | "world forces"
    domain: str  # SeedDomain.value of the culmination
    start_year: int  # earliest event year in the chain
    end_year: int  # culmination year
    length: int  # number of causal events in the chain
    culmination_scale: str  # EventScale.value
    player_driven: bool  # a player seed is among the culmination's causes


class TurningPointView(_View):
    """A pivotal LARGE event the narrative turned on."""

    year: int
    title: str  # event phrase — id-free
    domain: str  # SeedDomain.value
    player_driven: bool
    converging_threads: int  # selected threads whose chain passes through it


class NarrativeView(_View):
    """The immutable, id-free narrative snapshot — the single source of truth."""

    schema_version: str
    place: str
    span: int  # world.current_year
    ending_class: Optional[str]
    threads: List[ThreadView]
    turning_points: List[TurningPointView]


# --- builders: read the World, produce the structured records (internal) -----


class _Thread:
    """A raw thread carrying its chain node-set (used for ordering + convergence;
    the node ids never reach the view)."""

    __slots__ = (
        "title",
        "origin",
        "domain",
        "start_year",
        "end_year",
        "length",
        "scale",
        "player_driven",
        "chain",
        "culmination_id",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def sort_key(self):
        # Total order: significance, then longer chains, earlier start, title,
        # and finally the (internal) culmination id so equal-scale ties are stable.
        return (
            _SCALE_RANK.get(self.scale, 99),
            -self.length,
            self.start_year,
            self.title,
            self.culmination_id,
        )


def _culmination_thread(
    node: CausalNode,
    world: World,
    graph: CausalGraph,
    nodes_by_id: Dict[str, CausalNode],
    founding: Dict[str, object],
) -> _Thread:
    ancestors = graph.ancestors(node.id)
    chain: Set[str] = {node.id} | {a for a in ancestors if a in nodes_by_id}
    years = [nodes_by_id[i].year for i in chain]
    start_year = min(years) if years else node.year

    player_seeds = graph.player_seeds_in_ancestry(node.id)
    if player_seeds:
        seed = min(player_seeds, key=lambda s: (s.planted_year, s.id))
        origin = life_label(world, seed.planted_by_life_id)
    else:
        origin = "world forces"

    title = (
        heritage_name(founding[node.id]) if node.id in founding else event_phrase(node)
    )
    return _Thread(
        title=title,
        origin=origin,
        domain=node.domain.value,
        start_year=start_year,
        end_year=node.year,
        length=len(chain),
        scale=node.scale,
        player_driven=bool(player_seeds),
        chain=chain,
        culmination_id=node.id,
    )


def _raw_threads(world: World, graph: CausalGraph) -> List[_Thread]:
    nodes_by_id = {n.id: n for n in world.causal_nodes}
    # Heritage founding nodes (the event a heritage's seed TRIGGERed), keyed by id.
    founding: Dict[str, object] = {}
    for h in world.heritage:  # list order
        fn = triggered_node(world, h.seed_id)
        if fn is not None:
            founding.setdefault(fn.id, h)

    threads: List[_Thread] = []
    for node in world.causal_nodes:  # list order -> deterministic gather
        if node.scale == EventScale.LARGE or node.id in founding:
            threads.append(
                _culmination_thread(node, world, graph, nodes_by_id, founding)
            )
    threads.sort(key=_Thread.sort_key)
    return threads


def _turning_points(
    world: World, graph: CausalGraph, selected: List[_Thread]
) -> List[TurningPointView]:
    out: List[TurningPointView] = []
    for node in world.causal_nodes:  # list order
        if node.scale != EventScale.LARGE:
            continue
        converging = sum(1 for t in selected if node.id in t.chain)
        out.append(
            TurningPointView(
                year=node.year,
                title=event_phrase(node),
                domain=node.domain.value,
                player_driven=bool(graph.player_seeds_in_ancestry(node.id)),
                converging_threads=converging,
            )
        )
    out.sort(key=lambda tp: (tp.year, tp.title))
    return out


# --- public API: builder (World -> NarrativeView -> JSON) ----------------


def narrative_model(
    world: World, max_threads: int = DEFAULT_MAX_THREADS
) -> NarrativeView:
    """Project a finished world into the immutable, id-free ``NarrativeView``.

    Read-only: it reads the causal DAG + heritage + lineage and composes them; it
    never mutates the world and is not a canonical/persistence source. ``threads``
    is the canonically-ordered top ``max_threads`` culminations."""
    graph = CausalGraph.from_world(world)
    selected = _raw_threads(world, graph)[:max_threads]
    threads = [
        ThreadView(
            ordinal=i + 1,
            title=t.title,
            origin=t.origin,
            domain=t.domain,
            start_year=t.start_year,
            end_year=t.end_year,
            length=t.length,
            culmination_scale=t.scale.value,
            player_driven=t.player_driven,
        )
        for i, t in enumerate(selected)
    ]
    return NarrativeView(
        schema_version=SCHEMA_VERSION,
        place=place(world),
        span=world.current_year,
        ending_class=world.ending_class,
        threads=threads,
        turning_points=_turning_points(world, graph, selected),
    )


def narrative_json(world: World, max_threads: int = DEFAULT_MAX_THREADS) -> str:
    """The canonical JSON encoding of the narrative read-model — the client
    contract and the basis of the frozen seed42 hash."""
    return narrative_model(world, max_threads).model_dump_json()


# --- public API: renderer (NarrativeView -> Markdown; never reads the World) --


def narrative_markdown(view: NarrativeView) -> str:
    """Render a ``NarrativeView`` as Markdown. A **pure renderer**: it reads only
    the view (never the world) and returns deterministic, id-free prose."""
    lines = ["# Narrative", ""]
    tail = f", closing as the {view.ending_class}" if view.ending_class else ""
    lines.append(f"> {view.place} — {view.span} years{tail}.")
    lines.append("")

    lines.append("## Threads")
    lines.append("")
    if view.threads:
        for t in view.threads:
            driven = ", player-driven" if t.player_driven else ""
            lines.append(
                f"{t.ordinal}. **{t.title}** — {t.origin}, {t.domain}, "
                f"years {t.start_year}–{t.end_year} "
                f"({t.length} events, {t.culmination_scale}{driven})"
            )
    else:
        lines.append("No emergent threads.")
    lines.append("")

    lines.append("## Turning Points")
    lines.append("")
    if view.turning_points:
        for tp in view.turning_points:
            driven = ", player-driven" if tp.player_driven else ""
            conv = (
                f", {tp.converging_threads} converging threads"
                if tp.converging_threads
                else ""
            )
            lines.append(f"- Year {tp.year}: {tp.title} ({tp.domain}{driven}{conv})")
    else:
        lines.append("No turning points.")

    return "\n".join(lines).rstrip() + "\n"
