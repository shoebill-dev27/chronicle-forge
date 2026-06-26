"""P13 Character Observatory (Biography Read-Model) — read-only biography projection.

A pure lens over a finished world that surfaces, per life, the **structured
biography** the engine already computed: the 8 evaluation lenses, the activity
profile, talent, the death, and the legacies that life founded. It is to P7
``experience.py`` (locked prose) what P11-A ``WorldView`` is to the P10 Observatory:
the same facts, structured-first, id-free, hashable.

``CharacterObservatoryView`` is the single source of truth: ``character_json``
serializes it and ``character_markdown`` renders it. The Markdown renderer reads
**only the view**, never the world.

Boundaries (hard): read-only (never mutates the world), id-free (no seed / node /
life / npc id, no ``source_seed`` crosses the boundary — the raw-id ``LifeSummary``
lists ``seeds_created`` / ``heritage_created`` / ``notable_events`` are counted or
humanised, never emitted verbatim; only ordinals, ``.value`` enums and curated
``labels.py`` phrases surface), deterministic (lives in lineage order, activity
key-sorted, legacies sorted; no dict/set iteration leaks). It invents **no** score —
every number is read straight off the ``Life`` record. It touches no engine / Recipe
/ World / persistence state and moves no existing golden.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from ..models import HeritageNode, Life, World
from ._data import life_index, life_world_impact, place, seeds_of_life
from .labels import heritage_name

# The complete public surface: the view contract types, the builder entries, and
# the one renderer. Everything else in this module is a ``_``-prefixed internal.
__all__ = [
    "SCHEMA_VERSION",
    "LensScores",
    "BiographyView",
    "CharacterObservatoryView",
    "character_model",
    "character_json",
    "character_markdown",
]

# Read-model contract version — deliberately decoupled from ENGINE_VERSION.
SCHEMA_VERSION = "1"

# The engine's 8 evaluation lenses (section 8), in their canonical field order.
_LENSES = (
    "military",
    "politics",
    "economy",
    "academia",
    "culture",
    "faith",
    "mentoring",
    "heritage",
)


class _View(BaseModel):
    """Base for every read-model record: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class LensScores(_View):
    """The engine's 8 evaluation lenses for one life (no invented composite)."""

    military: int
    politics: int
    economy: int
    academia: int
    culture: int
    faith: int
    mentoring: int
    heritage: int


class BiographyView(_View):
    """One character's biography — the rich, id-free per-life record."""

    ordinal: int  # 1-based "Life N" (lineage order) — id-free
    title: str  # LifeSummary.title (curated) — id-free
    is_current: bool  # life.id == player.current_life_id (id compared, never shown)
    birth_year: int
    death_year: Optional[int]
    age_at_death: Optional[int]
    death_cause: Optional[str]  # DeathCause.value | None
    talent: Optional[str]  # Talent.value | None
    dominant_axis: Optional[str]  # ThemeAxis.value | None
    evaluation: LensScores
    activity: Dict[str, int]  # ActivityCategory.value -> count, key-sorted
    seeds_planted: int  # count of this life's seeds — never the ids
    world_impact: int  # events this life caused (life_world_impact)
    legacies: List[str]  # founded heritage NAMES (heritage_name), sorted


class CharacterObservatoryView(_View):
    """The immutable, id-free biography snapshot — the single source of truth."""

    schema_version: str
    place: str
    span: int  # world.current_year
    life_count: int
    characters: List[BiographyView]


# --- builder: read the World, produce the structured records (internal) ------


def _activity(life: Life) -> Dict[str, int]:
    """Category -> count, key-sorted so the dict is deterministic (categories are
    already ``ActivityCategory`` value strings on the record)."""
    counts = Counter(rec.category for rec in life.activity_log)
    return {cat: counts[cat] for cat in sorted(counts)}


def _legacies(life: Life, heritage_by_id: Dict[str, HeritageNode]) -> List[str]:
    """The heritage a life founded, as sorted id-free proper names. ``summary``
    holds heritage *ids*; they are humanised through ``heritage_name`` and the ids
    themselves never surface."""
    summary = life.summary
    if summary is None:
        return []
    names = [
        heritage_name(heritage_by_id[hid])
        for hid in summary.heritage_created
        if hid in heritage_by_id
    ]
    return sorted(names)


def _biography(
    world: World,
    life: Life,
    ordinal: int,
    current_life_id: Optional[str],
    heritage_by_id: Dict[str, HeritageNode],
) -> BiographyView:
    summary = life.summary
    dom = summary.dominant_axis if summary else None
    ev = life.evaluation
    return BiographyView(
        ordinal=ordinal,
        title=summary.title if summary else "",
        is_current=life.id == current_life_id,
        birth_year=life.birth_year,
        death_year=life.death_year,
        age_at_death=life.age_at_death,
        death_cause=life.death_cause.value if life.death_cause else None,
        talent=life.talent.value if life.talent else None,
        dominant_axis=dom.value if dom else None,
        evaluation=LensScores(**{lens: getattr(ev, lens) for lens in _LENSES}),
        activity=_activity(life),
        seeds_planted=len(seeds_of_life(world, life.id)),
        world_impact=life_world_impact(world, life.id),
        legacies=_legacies(life, heritage_by_id),
    )


# --- public API: builder (World -> CharacterObservatoryView -> JSON) ----------


def character_model(world: World) -> CharacterObservatoryView:
    """Project a finished world into the immutable, id-free biography snapshot.

    Read-only: it reads each ``Life`` + heritage + lineage and composes them; it
    never mutates the world and is not a canonical/persistence source. Characters
    follow ``world.lives`` (lineage) order."""
    idx = life_index(world)
    current = world.player.current_life_id
    heritage_by_id = {h.id: h for h in world.heritage}
    characters = [
        _biography(world, life, idx[life.id], current, heritage_by_id)
        for life in world.lives
    ]
    return CharacterObservatoryView(
        schema_version=SCHEMA_VERSION,
        place=place(world),
        span=world.current_year,
        life_count=len(world.lives),
        characters=characters,
    )


def character_json(world: World) -> str:
    """The canonical JSON encoding of the biography read-model — the client
    contract and the basis of the frozen seed42 hash."""
    return character_model(world).model_dump_json()


# --- public API: renderer (view -> Markdown; never reads the World) -----------


def character_markdown(view: CharacterObservatoryView) -> str:
    """Render a ``CharacterObservatoryView`` as Markdown. A **pure renderer**: it
    reads only the view (never the world) and returns deterministic, id-free prose."""
    lines = ["# Characters", ""]
    lines.append(f"> {view.place} — {view.span} years, {view.life_count} lives.")
    lines.append("")

    if not view.characters:
        lines.append("No lives recorded.")
        return "\n".join(lines).rstrip() + "\n"

    for bio in view.characters:
        current = " (current)" if bio.is_current else ""
        lines.append(f"## Life {bio.ordinal}: {bio.title or '—'}{current}")
        if bio.death_year is not None:
            aged = f" (aged {bio.age_at_death})" if bio.age_at_death is not None else ""
            cause = f", {bio.death_cause}" if bio.death_cause else ""
            lines.append(f"- Born {bio.birth_year}, died {bio.death_year}{aged}{cause}")
        else:
            lines.append(f"- Born {bio.birth_year}, still living")
        lines.append(
            f"- Talent: {bio.talent or '—'}, dominant: {bio.dominant_axis or '—'}"
        )
        lines.append(
            f"- Impact: {bio.world_impact} events from {bio.seeds_planted} seeds"
        )
        ev = bio.evaluation
        lenses = ", ".join(f"{lens} {getattr(ev, lens)}" for lens in _LENSES)
        lines.append(f"- Lenses: {lenses}")
        if bio.activity:
            activity = ", ".join(f"{cat} {n}" for cat, n in bio.activity.items())
            lines.append(f"- Activity: {activity}")
        if bio.legacies:
            lines.append(f"- Legacies: {', '.join(bio.legacies)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
