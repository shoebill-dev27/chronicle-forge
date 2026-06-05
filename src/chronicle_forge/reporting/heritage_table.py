"""heritage.md + heritage.csv: top-N heritage ranking.

Columns: rank, score, longevity, reach, source_seed, domain, derived_events,
origin_life.
"""

from __future__ import annotations

import csv
import io

from ..models import World
from ._data import heritage_rows

_COLUMNS = [
    "rank",
    "name",
    "score",
    "longevity",
    "reach",
    "source_seed",
    "domain",
    "derived_events",
    "origin_life",
    "origin_action",
]


def heritage_table_md(world: World, top: int = 10) -> str:
    rows = heritage_rows(world, top=top)
    lines = [
        f"# Heritage Ranking — Seed {world.seed} (Top {top})",
        "",
        "| Rank | Name | Type | Score | Longevity | Reach | Source seed | Derived events | Origin |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| — | — | — | — | — | — | — | — | — |")
    for i, r in enumerate(rows, 1):
        origin = f"{r['origin_life']} → {r['origin_action']}"
        lines.append(
            f"| {i} | **{r['name']}** | {r['type']} | {r['score']} | {r['longevity']} "
            f"| {r['reach']} | `{r['source_seed']}` | {r['derived_events']} | {origin} |"
        )
    return "\n".join(lines) + "\n"


def heritage_csv(world: World, top: int = 10) -> str:
    rows = heritage_rows(world, top=top)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_COLUMNS)
    for i, r in enumerate(rows, 1):
        writer.writerow(
            [
                i,
                r["name"],
                r["score"],
                r["longevity"],
                r["reach"],
                r["source_seed"],
                r["domain"],
                r["derived_events"],
                r["origin_life"],
                r["origin_action"],
            ]
        )
    return buf.getvalue()
