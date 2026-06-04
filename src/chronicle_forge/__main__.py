"""CLI entry point for the developer observability report.

Usage:
    python -m chronicle_forge [SEED]

Runs a full deterministic world for SEED (default 42) and prints the report:
world summary, player lives, personal history, theme trajectory, major events,
wildcard history, heritage Top 10, and the NPC codex. Read-only; no AI.
"""

from __future__ import annotations

import sys

from .autoplay import simulate_report


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    seed = int(argv[0]) if argv else 42
    print(simulate_report(seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
