"""build.py: generate the seed=42 demo asset bundle into docs/examples/<seed>/.

Read-only on game state: runs simulate_world(seed) and writes Markdown/DOT/CSV
derived from it. No AI. PNG is rendered only if the Graphviz `dot` binary is
available.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..autoplay import simulate_world
from ..models import World
from .causal_dot import causal_dot
from .chronicle_md import chronicle_report_md
from .heritage_table import heritage_csv, heritage_table_md
from .story_md import one_causal_chain_md, stories_md, why_ending_chain_md
from .summary_md import summarize_world
from .timeline_md import timeline_md


def _folder_readme(world: World, has_png: bool) -> str:
    lines = [
        f"# Example World — Seed {world.seed}",
        "",
        "> The player's actions continued affecting history long after death.",
        "",
        "| Lives | Events | Heritage | Ending |",
        "|---|---|---|---|",
        f"| {len(world.lives)} | {len(world.causal_nodes)} | "
        f"{len(world.heritage)} | {world.ending_class} |",
        "",
    ]
    why = why_ending_chain_md(world)
    if why:
        lines += [why, ""]
    chain = one_causal_chain_md(world)
    if chain:
        lines += [chain, ""]
    if has_png:
        lines += [
            "![Causal lineage from player seeds to the ending](causal.png)",
            "",
        ]
    lines += [
        "## How to read this (~5 minutes)",
        "",
        "Read in this order:",
        "",
        "**1. [summary.md](summary.md) — _~1 min, read first._**  ",
        "What this world is and what happened, for a first-time reader.",
        "",
        "**2. [story.md](story.md) — _~2–3 min, the heart of it._**  ",
        "Each life traced Life → Seeds → Events → Heritage → Ending. "
        "Look for how one early life's single seed grows into the world's ending.",
        "",
        "**3. [chronicle.md](chronicle.md) — _~1–2 min._**  ",
        'The full factual report. Jump to **"Why this Ending"** to see the '
        "`Ending ← Event ← Seed ← Life` chain spelled out.",
        "",
        "**Then, by interest (optional):**",
        "",
        "- [causal.dot](causal.dot) — _~1 min_ — the same lineages as a graph "
        "(`dot -Tpng causal.dot -o causal.png`). Look for gold ★ player seeds "
        "flowing down to the green `ENDING` node.",
        "- [heritage.md](heritage.md) / [heritage.csv](heritage.csv) — _~1 min_ — "
        "the legacy ranking: which seed, from which life, mattered most.",
        "- [timeline.md](timeline.md) — _~1 min_ — the year-by-year arc of the world.",
        "",
        f"_Everything here is generated from `simulate_world({world.seed})` — fully "
        "reproducible, rules-only, no AI._",
    ]
    return "\n".join(lines) + "\n"


def _maybe_render_png(dot_path: Path) -> bool:
    if shutil.which("dot") is None:
        return False
    png_path = dot_path.with_suffix(".png")
    try:
        subprocess.run(
            ["dot", "-Tpng", str(dot_path), "-o", str(png_path)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        return True
    except Exception:
        return False


def build_seed_assets(
    seed: int = 42, out_dir: str = "docs/examples", png: bool = True
) -> list[str]:
    """Generate the demo bundle for ``seed`` under ``out_dir/seed<seed>/``.

    Returns the list of written file paths.
    """
    world = simulate_world(seed)
    target = Path(out_dir) / f"seed{seed}"
    target.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "story.md": stories_md(world),
        "chronicle.md": chronicle_report_md(world),
        "causal.dot": causal_dot(world),
        "heritage.md": heritage_table_md(world),
        "heritage.csv": heritage_csv(world),
        "timeline.md": timeline_md(world),
        "summary.md": summarize_world(world) + "\n",
    }

    written = []
    for name, content in artifacts.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    has_png = False
    if png:
        has_png = _maybe_render_png(target / "causal.dot")
        if has_png:
            written.append(str(target / "causal.png"))

    readme = target / "README.md"
    readme.write_text(_folder_readme(world, has_png), encoding="utf-8")
    written.append(str(readme))

    return written
