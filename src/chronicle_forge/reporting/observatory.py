"""P10 Observatory — one read-only surface that composes what already exists.

The Observatory is the lens for "explore the world I made". It computes no new
history: it gathers the player-safe projections (lineage P9-4, heritage P9-5) plus
thin id-free overview/theme renders into one navigable Markdown document.

Internally it first builds a structured, ordered, id-free list of ``Section``s
(``_build_sections``); ``observatory()`` is a thin renderer over that. The
structured form is the seam a future low-poly 3D client reads (section key +
id-free fields), so it never has to parse the prose.

Read-only: it never mutates the world and never reuses the dev-facing, id-leaky
``views.py``. P6/P7/P8/P9-* and the seed42 golden are inviolable.
"""

from __future__ import annotations

from typing import Callable, List, NamedTuple, Optional

from ..models import World
from ._data import place
from .heritage_explorer import heritage_explorer
from .lineage import lineage_view


class Section(NamedTuple):
    """One observable aspect of a finished world. ``body`` is rendered Markdown;
    ``key``/``title`` are the stable, id-free handles a 3D client subscribes to."""

    key: str
    title: str
    body: str


# --- section bodies (each: World -> id-free Markdown) -------------------


def _overview_body(world: World) -> str:
    dom = world.theme.dominant
    age = f"an age of {dom.value}" if dom is not None else "an unsettled age"
    lines = [
        f"> {place(world)} endured {world.current_year} years "
        f"across {len(world.lives)} lives.",
        "",
    ]
    if world.ending_class:
        lines.append(f"The age closed as the {world.ending_class} — {age}.")
    else:
        lines.append(f"The age closed in {age}.")
    return "\n".join(lines)


def _theme_body(world: World) -> str:
    dom = world.theme.dominant
    if dom is None or not world.theme.axes:
        return "The world never settled on a defining current."
    standings = sorted(world.theme.axes.items(), key=lambda kv: (-kv[1], kv[0].value))
    lines = [f"The world settled into an age of {dom.value}.", ""]
    for axis, value in standings:
        lines.append(f"- {axis.value}: {value}")
    return "\n".join(lines)


def _embed(body: str) -> str:
    """Embed a reused view's body under an Observatory section, dropping the
    view's own top-level ``# `` title (the Observatory supplies the heading)."""
    lines = body.split("\n")
    while lines and lines[0].strip() == "":
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines.pop(0)
        while lines and lines[0].strip() == "":
            lines.pop(0)
    return "\n".join(lines).strip("\n")


def _lineage_body(world: World) -> str:
    return _embed(lineage_view(world))


def _heritage_body(world: World) -> str:
    return _embed(heritage_explorer(world))


# --- section registry ---------------------------------------------------

_REGISTRY: "dict[str, tuple[str, Callable[[World], str]]]" = {
    "overview": ("Overview", _overview_body),
    "lineage": ("Lineage", _lineage_body),
    "heritage": ("Heritage", _heritage_body),
    "theme": ("Theme", _theme_body),
}

_MVP_SECTIONS = ("overview", "lineage", "heritage", "theme")


def _build_sections(
    world: World, sections: Optional[List[str]] = None
) -> List[Section]:
    """The structured, ordered, id-free section list (the 3D-client seam).

    ``sections`` selects *which* sections appear; the output **order is always the
    canonical MVP order** (``overview`` -> ``lineage`` -> ``heritage`` -> ``theme``)
    regardless of the input order, so the surface is stable for any caller.
    ``sections=None`` selects the full MVP set. An unknown key or an empty list
    raises ``ValueError``.
    """
    keys = list(_MVP_SECTIONS) if sections is None else list(sections)
    if not keys:
        raise ValueError("sections must select at least one section")
    unknown = [k for k in keys if k not in _REGISTRY]
    if unknown:
        raise ValueError(
            f"unknown section(s) {unknown}; expected one of {tuple(_REGISTRY)}"
        )
    selected = set(keys)
    out: List[Section] = []
    for key in _REGISTRY:  # canonical order, input order ignored
        if key in selected:
            title, render = _REGISTRY[key]
            out.append(Section(key=key, title=title, body=render(world)))
    return out


# --- public renderer ----------------------------------------------------


def observatory(world: World, *, sections: Optional[List[str]] = None) -> str:
    """One read-only Markdown surface over a finished world. Deterministic and
    id-free. ``sections=None`` renders the full MVP set (``overview``, ``lineage``,
    ``heritage``, ``theme``); an explicit list selects *which* sections appear, but
    the output is always in that canonical order regardless of the input order.
    Unknown or empty selections raise ``ValueError``."""
    lines = ["# Observatory", ""]
    for section in _build_sections(world, sections):
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
