"""CLI: generate the demo asset bundle.

    python -m chronicle_forge.reporting [SEED] [--out DIR] [--no-png]

Writes docs/examples/seed<SEED>/ by default. Read-only on game state; no AI.
"""

from __future__ import annotations

import argparse

from .build import build_seed_assets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chronicle_forge.reporting")
    parser.add_argument("seed", nargs="?", type=int, default=42)
    parser.add_argument("--out", default="docs/examples")
    parser.add_argument("--no-png", action="store_true", help="skip PNG rendering")
    args = parser.parse_args(argv)

    written = build_seed_assets(args.seed, out_dir=args.out, png=not args.no_png)
    print(f"Generated {len(written)} files for seed {args.seed}:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
