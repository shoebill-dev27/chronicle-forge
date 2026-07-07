"""P17 Legacy Legibility (Fingerprint Read-Model) — read-only projection.

A pure lens over a finished world that makes its **Fingerprint** legible: the
player's enduring marks, each attributed to the *specific life* that made it,
arranged so the player recognizes them ("あ、これ昔の自分だ"). It computes no new
history and invents no score: every field is read straight off an existing
``Heritage`` row / ``World.memories`` / ``World.theme``. See
docs/design_p17_legacy_legibility.md and docs/fingerprint_design.md.

``LegacyView`` is the single source of truth: ``legacy_json`` serializes it and
``legacy_markdown`` renders it. The Markdown renderer reads **only the view**,
never the world.

Boundaries (hard): read-only (never mutates the world), id-free (no seed / node /
life / npc id, no ``source_seed`` crosses the boundary — heritage by proper name,
founders by their ordinal only), deterministic (total orders, no dict/set
iteration leaks), and it invents **no** score — significance is the engine's own
``reach`` / ``derived_events`` / ``longevity`` read verbatim, never re-ranked. It
touches no engine / Recipe / World / persistence state and moves no existing
golden (it ships its own).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from ..enums import MemoryType
from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import heritage_rows, place

# The complete public surface: the view contract types, the two builder entries,
# and the one renderer. Everything else is a ``_``-prefixed internal.
__all__ = [
    "SCHEMA_VERSION",
    "RECOGNITION_MIN_EVENTS",
    "RECOGNITION_MIN_REACH",
    "AxisWeight",
    "LegacyMark",
    "ReputationNote",
    "RecognitionCue",
    "LegacyView",
    "legacy_model",
    "legacy_json",
    "legacy_markdown",
]

# Read-model contract version — deliberately decoupled from ENGINE_VERSION.
SCHEMA_VERSION = "1"

# Recognition thresholds (§4). Local to this read-model like ``opportunity.py``'s
# constants — no ``config.py`` change. A mark self-signals when it is *living*, or
# consequential (many descendant events), or far-reaching (broad reach).
RECOGNITION_MIN_EVENTS = 8
RECOGNITION_MIN_REACH = 8

# Domain values (``seed.domain.value``, as carried by ``heritage_rows``) mapped to
# their theme axis — the same living-status rule the Heritage Explorer uses.
_DOMAIN_VALUE_TO_AXIS = {d.value: axis for d, axis in SEED_DOMAIN_TO_THEME.items()}

# Humanised ``MemoryType`` — the world's remembered sentiment, id-free.
_SENTIMENT: Dict[MemoryType, str] = {
    MemoryType.SAVED: "remembered with gratitude",
    MemoryType.RESCUED: "remembered with relief",
    MemoryType.EDUCATED: "remembered as a teacher",
    MemoryType.BETRAYED: "remembered with resentment",
    MemoryType.BEREAVED: "remembered in grief",
    MemoryType.HUMILIATED: "remembered with shame",
}

# Recognition hint vocabulary (§6.3) — evocative, never spelling out authorship.
_HINT_LIVING = "still shapes the world today"
_HINT_CONSEQUENTIAL = "far more came of it than anyone alive could see"
_HINT_FAR_REACHING = "its echoes outlived the one who began it"

_LIVING_PHRASE = "still shaping the world"

_FOUNDER_RE = re.compile(r"Life (\d+)")


class _View(BaseModel):
    """Base for every legacy record: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class AxisWeight(_View):
    """One axis of the Fingerprint's Shape — how much the world was shaped there."""

    axis: str  # ThemeAxis.value
    weight: int  # count of enduring marks on this axis (a read, not a score)
    living: bool  # axis == world.theme.dominant


class LegacyMark(_View):
    """One enduring mark, attributed to the life that founded it (id-free)."""

    name: str  # heritage proper name
    kind: str  # HeritageType.value
    founder_life: int  # founding life's 1-based ordinal
    reach: int  # engine's breadth measure (verbatim)
    derived_events: int  # descendant events in the causal DAG (verbatim)
    longevity: int  # years the legacy propagated (verbatim)
    living: bool  # its domain still runs in the world's dominant theme


class ReputationNote(_View):
    """How the world remembers the player — a humanised, id-free memory count."""

    sentiment: str  # humanised MemoryType
    count: int  # number of such memories


class RecognitionCue(_View):
    """A rare mark that self-signals "that was me" — the Recognition Moment."""

    mark_name: str  # references a LegacyMark by name
    founder_life: int  # founding life's ordinal
    living: bool
    hint: str  # evocative line chosen by the satisfied self-signal


class LegacyView(_View):
    """The immutable, id-free Fingerprint snapshot — the single source of truth."""

    schema_version: str
    place: str  # founding village name (id-free) | world id
    span: int  # world.current_year
    shape: List[AxisWeight]  # the Shape dimension
    marks: List[LegacyMark]  # Weight / Persistence / Hand
    reputation: List[ReputationNote]  # Reputation
    recognitions: List[RecognitionCue]  # the rare self-signalling subset


# --- builder internals --------------------------------------------------


def _founder_ordinal(origin_life: str) -> Optional[int]:
    """The founder life's 1-based ordinal parsed from ``origin_life`` ("Life N"),
    or ``None`` when no founder resolves (world-force seeds never attribute)."""
    match = _FOUNDER_RE.match(origin_life)
    return int(match.group(1)) if match else None


def _shape(world: World, rows: List[dict]) -> List[AxisWeight]:
    dominant = world.theme.dominant
    counts: Counter = Counter()
    for row in rows:
        axis = _DOMAIN_VALUE_TO_AXIS.get(row["domain"])
        if axis is not None:
            counts[axis] += 1
    weights = [
        AxisWeight(axis=axis.value, weight=n, living=axis == dominant)
        for axis, n in counts.items()
    ]
    weights.sort(key=lambda a: (-a.weight, a.axis))
    return weights


def _marks(world: World, rows: List[dict]) -> List[LegacyMark]:
    dominant = world.theme.dominant
    marks: List[LegacyMark] = []
    for row in rows:
        founder = _founder_ordinal(row["origin_life"])
        if founder is None:  # unattributable marks are not legible as "mine"
            continue
        axis = _DOMAIN_VALUE_TO_AXIS.get(row["domain"])
        marks.append(
            LegacyMark(
                name=row["name"],
                kind=row["type"],
                founder_life=founder,
                reach=row["reach"],
                derived_events=row["derived_events"],
                longevity=row["longevity"],
                living=axis is not None and axis == dominant,
            )
        )
    # Lead with living marks, then by consequence/reach; a stable id-free tiebreak.
    marks.sort(key=lambda m: (not m.living, -m.derived_events, -m.reach, m.name))
    return marks


def _reputation(world: World) -> List[ReputationNote]:
    counts: Counter = Counter(m.type for m in world.memories)
    notes = [
        ReputationNote(sentiment=_SENTIMENT.get(mtype, mtype.value), count=n)
        for mtype, n in counts.items()
    ]
    notes.sort(key=lambda note: (-note.count, note.sentiment))
    return notes


def _recognition_hint(mark: LegacyMark) -> Optional[str]:
    if mark.living:
        return _HINT_LIVING
    if mark.derived_events >= RECOGNITION_MIN_EVENTS:
        return _HINT_CONSEQUENTIAL
    if mark.reach >= RECOGNITION_MIN_REACH:
        return _HINT_FAR_REACHING
    return None


def _recognitions(marks: List[LegacyMark]) -> List[RecognitionCue]:
    cues: List[RecognitionCue] = []
    for mark in marks:  # marks are already attributable and sorted
        hint = _recognition_hint(mark)
        if hint is None:
            continue
        cues.append(
            RecognitionCue(
                mark_name=mark.name,
                founder_life=mark.founder_life,
                living=mark.living,
                hint=hint,
            )
        )
    return cues


# --- public API: builder (World -> LegacyView -> JSON) ------------------


def legacy_model(world: World) -> LegacyView:
    """Project a finished world into the immutable, id-free ``LegacyView``.

    Read-only: it reads the heritage rows, memories and theme and composes them;
    it never mutates the world and is not a canonical/persistence source."""
    rows = heritage_rows(world)
    marks = _marks(world, rows)
    return LegacyView(
        schema_version=SCHEMA_VERSION,
        place=place(world),
        span=world.current_year,
        shape=_shape(world, rows),
        marks=marks,
        reputation=_reputation(world),
        recognitions=_recognitions(marks),
    )


def legacy_json(world: World) -> str:
    """The canonical JSON encoding of the legacy read-model — the client contract
    and the basis of the frozen seed42 hash."""
    return legacy_model(world).model_dump_json()


# --- public API: renderer (LegacyView -> Markdown; never reads the World) -----


def _ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', ... — attribution by position, not identity."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def legacy_markdown(view: LegacyView) -> str:
    """Render a ``LegacyView`` as Markdown. A **pure renderer**: it reads only the
    view (never the world) and returns deterministic, id-free prose. It surfaces
    breadcrumbs (founder ordinal, living marks, evocative hints) so the player
    *notices* — it never declares authorship."""
    lines = ["# Legacy", ""]
    lines.append(f"> {view.place} — {view.span} years. What endured, and whose hand.")
    lines.append("")

    if not view.marks:
        lines.append("Nothing endured; the world closed over every life.")
        return "\n".join(lines).rstrip() + "\n"

    lines.append("## Shape")
    for a in view.shape:
        mark_word = "mark" if a.weight == 1 else "marks"
        living = f" · {_LIVING_PHRASE}" if a.living else ""
        lines.append(f"- {a.axis} — {a.weight} {mark_word}{living}")
    lines.append("")

    lines.append("## Marks")
    for m in view.marks:
        living = f" · {_LIVING_PHRASE}" if m.living else ""
        lines.append(
            f"- **{m.name}** — {m.kind}, begun by the {_ordinal(m.founder_life)} "
            f"to live here{living}."
        )
        lines.append(f"  Reached {m.derived_events} events over {m.longevity} years.")
    lines.append("")

    if view.reputation:
        lines.append("## Reputation")
        for note in view.reputation:
            lines.append(f"- {note.sentiment} (×{note.count})")
        lines.append("")

    if view.recognitions:
        lines.append("## Recognitions")
        for cue in view.recognitions:
            lines.append(
                f"- **{cue.mark_name}** — begun by the {_ordinal(cue.founder_life)} "
                f"to live here. {cue.hint}."
            )

    return "\n".join(lines).rstrip() + "\n"
