"""P11 Structured World Read-Model (L1) — the data boundary for a non-text client.

A read-only projection of a finished world into one typed, id-free, JSON-
serializable aggregate (``WorldView``). It *aggregates* several already-player-safe
read-only sources — overview/theme (``_data``), lineage (``world.lives``), heritage
(``heritage_rows``), social memory (``social_memory_bonds``), and the new ``places``
(the 3D map anchor) — and is shaped for a future low-poly 3D / web client to
deserialize.

It is **not** a canonical source and must never become a persistence format: the
save is the Recipe (P9). Every view model is immutable (``frozen``); nothing here
mutates the world, takes an engine flag, or leaks an internal id (``player_id`` /
``npc_id`` / ``faction_id`` / ``source_seed`` are dropped at the boundary — the P8
lesson, enforced as a negative contract). Deterministic. Nothing here touches the
world, P6/P7/P8/P9-*, the frozen P10 Observatory / Social Memory views, or the
seed42 golden.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from ..enums import LocationType
from ..models import World
from ._data import (
    dominant_axis,
    heritage_rows,
    life_index,
    life_world_impact,
    place,
)
from .social_memory import social_memory_bonds

# The read-model's own schema contract version — bumped only when a record shape
# changes. Deliberately independent of ENGINE_VERSION (a world-determinism stamp);
# the two must never be coupled.
SCHEMA_VERSION = "1"


class _View(BaseModel):
    """Base for every read-model record: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Overview(_View):
    place: str
    seed: int  # recipe identity (an int, not an internal entity id)
    current_year: int
    max_year: int
    life_count: int
    ending_class: Optional[str]
    dominant_axis: Optional[str]  # ThemeAxis.value


class ThemeView(_View):
    dominant: Optional[str]  # ThemeAxis.value
    axes: dict[str, int]  # ThemeAxis.value -> score, key-sorted


class LifeView(_View):
    ordinal: int  # 1-based "Life N"
    title: str
    birth_year: int
    death_year: Optional[int]
    dominant_axis: Optional[str]
    world_impact: int


class HeritageView(_View):
    name: str
    type: str
    domain: str
    score: int
    longevity: int
    reach: int
    derived_events: int
    origin_life: str  # "Life N" | "—"
    origin_action: str
    # source_seed is deliberately absent — dropped at the id-free boundary.


class BondView(_View):
    npc_name: str
    npc_tier: str
    life_ordinal: int
    affinity: int
    sentiment: str
    reason: str


class PlaceView(_View):
    """The primary 3D anchor. MVP carries only id-free scalars; the structured
    home means the 3D map section can grow without breaking the text surface.

    Future extension (3D anchor): coordinates / biome / importance / landmark.
    """

    name: str
    location_type: str  # LocationType.value
    theme_affinity: Optional[str]  # ThemeAxis.value | None
    is_origin: bool  # the founding village (3D spawn anchor)


class FactionView(_View):
    name: str
    kind: str  # FactionType.value
    power: int
    # relations deferred — dict keyed by faction_id needs an id->name humaniser.


class WorldView(_View):
    """The structured, id-free snapshot a non-text client deserializes."""

    schema_version: str
    overview: Overview
    theme: ThemeView
    lives: List[LifeView]
    heritage: List[HeritageView]
    bonds: List[BondView]
    places: List[PlaceView]
    factions: List[FactionView]


def _overview(world: World) -> Overview:
    dom = dominant_axis(world)
    return Overview(
        place=place(world),
        seed=world.seed,
        current_year=world.current_year,
        max_year=world.max_year,
        life_count=len(world.lives),
        ending_class=world.ending_class,
        dominant_axis=dom.value if dom else None,
    )


def _theme(world: World) -> ThemeView:
    dom = world.theme.dominant
    axes = {axis.value: score for axis, score in world.theme.axes.items()}
    return ThemeView(
        dominant=dom.value if dom else None,
        axes=dict(sorted(axes.items())),
    )


def _lives(world: World) -> List[LifeView]:
    idx = life_index(world)
    out: List[LifeView] = []
    for life in world.lives:
        summary = life.summary
        dom = summary.dominant_axis if summary else None
        out.append(
            LifeView(
                ordinal=idx[life.id],
                title=summary.title if summary else "",
                birth_year=life.birth_year,
                death_year=life.death_year,
                dominant_axis=dom.value if dom else None,
                world_impact=life_world_impact(world, life.id),
            )
        )
    return out


def _heritage(world: World) -> List[HeritageView]:
    # heritage_rows is already sorted (by -score, source_seed); we preserve its
    # order but drop the internal source_seed at the boundary.
    return [
        HeritageView(
            name=row["name"],
            type=row["type"],
            domain=row["domain"],
            score=row["score"],
            longevity=row["longevity"],
            reach=row["reach"],
            derived_events=row["derived_events"],
            origin_life=row["origin_life"],
            origin_action=row["origin_action"],
        )
        for row in heritage_rows(world)
    ]


def _bonds(world: World) -> List[BondView]:
    return [
        BondView(
            npc_name=b.npc_name,
            npc_tier=b.npc_tier,
            life_ordinal=b.life_ordinal,
            affinity=b.affinity,
            sentiment=b.sentiment,
            reason=b.reason,
        )
        for b in social_memory_bonds(world)
    ]


def _places(world: World) -> List[PlaceView]:
    origin = next(
        (loc for loc in world.locations if loc.type == LocationType.VILLAGE), None
    )
    origin_id = origin.id if origin else None
    views = [
        PlaceView(
            name=loc.name,
            location_type=loc.type.value,
            theme_affinity=loc.theme_affinity.value if loc.theme_affinity else None,
            is_origin=loc.id == origin_id,
        )
        for loc in world.locations
    ]
    views.sort(key=lambda p: (p.location_type, p.name))
    return views


def _factions(world: World) -> List[FactionView]:
    views = [
        FactionView(name=f.name, kind=f.type.value, power=f.power)
        for f in world.factions
    ]
    views.sort(key=lambda f: (-f.power, f.name))
    return views


def world_model(world: World) -> WorldView:
    """Aggregate a finished world into the immutable, id-free ``WorldView``.

    Read-only: it reads several player-safe projections and composes them; it
    never mutates the world and is not a canonical/persistence source."""
    return WorldView(
        schema_version=SCHEMA_VERSION,
        overview=_overview(world),
        theme=_theme(world),
        lives=_lives(world),
        heritage=_heritage(world),
        bonds=_bonds(world),
        places=_places(world),
        factions=_factions(world),
    )


def world_model_json(world: World) -> str:
    """The canonical JSON encoding of the read-model — the client contract and the
    basis of the frozen seed42 hash."""
    return world_model(world).model_dump_json()
