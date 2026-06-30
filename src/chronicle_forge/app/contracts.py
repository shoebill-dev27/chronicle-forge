"""P15 Vertical Slice — Application Layer contracts (immutable, id-free DTOs).

These records are the boundary of the ``play → save → explore → share`` use case.
They are frozen and closed (``extra="forbid"``); the ``ChronicleView`` and
``PlayOutcome`` are id-free at the boundary (every fact is read off the engine the way
P10–P14 already read it — only ordinals, ``.value`` enums and curated label phrases,
never raw ids). The Application Layer composes existing parts and invents no truth, so
the embedded ``WorldView`` / ``TimelineView`` / ``NarrativeView`` /
``CharacterObservatoryView`` are exactly the frozen P11/P14/P12/P13 lens records.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from ..persistence import Recipe
from ..reporting.character import CharacterObservatoryView
from ..reporting.narrative import NarrativeView
from ..reporting.timeline import TimelineView
from ..reporting.world_model import WorldView

# Application read-model contract version — decoupled from ENGINE_VERSION.
SCHEMA_VERSION = "1"


class _Frozen(BaseModel):
    """Base for every Application DTO: immutable and closed."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class PlayRequest(_Frozen):
    """A request to grow (or auto/script-drive) a world."""

    seed: int
    auto: bool = False  # EOF-equivalent full run; auto ⇔ inputs == []
    script_lines: Optional[List[str]] = None  # scripted chooser (excludes auto)
    social_memory: bool = False  # P11-B L2 cross-life decay/bias (auto/script only)


class PlayOutcome(_Frozen):
    """The id-free result of a grown/driven world. Holds no live ``World`` ref."""

    recipe: Recipe  # the canonical save (seed + max_year + mode + inputs)
    transcript: str  # regenerated, byte-deterministic (== replay)
    ending_class: Optional[str]  # world.ending_class — id-free
    life_count: int
    span: int  # world.current_year


class ChronicleView(_Frozen):
    """The explore product — the P10–P14 lenses composed, id-free, read-only."""

    schema_version: str
    place: str  # _data.place(world) — id-free
    span: int  # world.current_year
    ending_class: Optional[str]
    world: WorldView  # P11
    timeline: TimelineView  # P14
    narrative: NarrativeView  # P12
    characters: CharacterObservatoryView  # P13
    heritage_markdown: str  # heritage_explorer(world) — id-free renderer


class ShareRequest(_Frozen):
    """A request to emit a shareable, reproducible artifact for a recipe."""

    recipe: Recipe
    export_path: Optional[str] = None


class ShareResult(_Frozen):
    """The shared artifact + the command that reproduces the run from the recipe."""

    recipe: Recipe
    transcript: str  # == PlayOutcome.transcript for the same recipe
    export_path: Optional[str]
    reproducible_command: str  # contains "--replay"
