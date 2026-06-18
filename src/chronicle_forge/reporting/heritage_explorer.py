"""P9-5 Heritage Explorer — a browsable catalogue of what endured.

A read-only projection of a finished world into player-facing Markdown. Where
P9-4 Lineage answers *who left it* (the chain of selves), this answers *what
remained*: every heritage by significance, with a selectable sort and grouping,
and a "still shaping the world" mark for legacies whose domain still runs in the
world's final dominant theme.

It reuses the deterministic ``heritage_rows`` projection (already sorted by
``-score, source_seed``), never mutates the world, and never leaks an internal id
(the P8 / P9-4 lesson) — heritage by proper name, founders by their ordinal.

"still shaping the world" (locked definition): a heritage is living when
``SEED_DOMAIN_TO_THEME[seed.domain] == world.theme.dominant``. longevity measures
*historical* persistence; this measures *present* influence — the two are
independent concepts.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional

from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import heritage_rows

# Domain values (``seed.domain.value``, as carried by ``heritage_rows``) mapped to
# their theme axis, so living-status is decided without re-touching the enum.
_DOMAIN_VALUE_TO_AXIS = {d.value: axis for d, axis in SEED_DOMAIN_TO_THEME.items()}

_LIVING_PHRASE = "still shaping the world"

_NO_ORDINAL = 10**9


def _founder_ordinal(row: dict) -> int:
    """The founder life's 1-based ordinal parsed from ``origin_life`` ("Life N").
    Heritage with no resolvable founder sorts last (deterministic)."""
    match = re.match(r"Life (\d+)", row["origin_life"])
    return int(match.group(1)) if match else _NO_ORDINAL


_SORTS: dict[str, Callable[[dict], tuple]] = {
    "score": lambda r: (-r["score"], r["source_seed"]),
    "longevity": lambda r: (-r["longevity"], r["source_seed"]),
    "reach": lambda r: (-r["reach"], r["source_seed"]),
    "origin": lambda r: (_founder_ordinal(r), r["source_seed"]),
}

_GROUPS = (None, "type", "founder")


# --- living status ------------------------------------------------------


def _is_living(world: World, row: dict) -> bool:
    dominant = world.theme.dominant
    if dominant is None:
        return False
    axis = _DOMAIN_VALUE_TO_AXIS.get(row["domain"])
    return axis is not None and axis == dominant


# --- grouping -----------------------------------------------------------


def _grouped(rows: List[dict], group_by: Optional[str]) -> List[tuple]:
    """Return ``[(header_or_None, rows), ...]`` in deterministic group order.
    Rows inside each group keep the order they arrive in (already sorted)."""
    if group_by is None:
        return [(None, rows)]

    buckets: dict[str, List[dict]] = {}
    for row in rows:
        key = row["type"] if group_by == "type" else row["origin_life"]
        buckets.setdefault(key, []).append(row)

    if group_by == "type":
        # Highest-scoring type first; ties on the type name.
        order = sorted(buckets, key=lambda k: (-max(r["score"] for r in buckets[k]), k))
    else:  # founder: earliest founder ordinal first.
        order = sorted(buckets, key=lambda k: (_founder_ordinal(buckets[k][0]), k))

    return [(key, buckets[key]) for key in order]


# --- renderer -----------------------------------------------------------


def _entry(world: World, row: dict) -> List[str]:
    suffix = f" · {_LIVING_PHRASE}" if _is_living(world, row) else ""
    return [
        f"- **{row['name']}** — {row['type']}, founded by "
        f"{row['origin_life']}{suffix}.",
        f"  Reached {row['derived_events']} events over {row['longevity']} years.",
    ]


def heritage_explorer(
    world: World, *, sort: str = "score", group_by: Optional[str] = None
) -> str:
    """What endured, as player-facing Markdown. Read-only and deterministic.

    ``sort`` is one of ``score`` (default), ``longevity``, ``reach``, ``origin``
    (all ties break on the source seed). ``group_by`` is ``None`` (default, a flat
    list), ``type`` or ``founder``. An unknown ``sort`` or ``group_by`` raises
    ``ValueError``.
    """
    if sort not in _SORTS:
        raise ValueError(f"unknown sort {sort!r}; expected one of {tuple(_SORTS)}")
    if group_by not in _GROUPS:
        raise ValueError(f"unknown group_by {group_by!r}; expected one of {_GROUPS}")

    rows = sorted(heritage_rows(world), key=_SORTS[sort])

    lines = [
        "# What endured",
        "",
        f"> {len(rows)} legacies outlived the lives that made them.",
        "",
    ]

    if not rows:
        lines.append("Nothing endured; the world closed over every life.")
        return "\n".join(lines).rstrip() + "\n"

    for header, group_rows in _grouped(rows, group_by):
        if header is not None:
            lines.append(f"### {header}")
        for row in group_rows:
            lines.extend(_entry(world, row))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
