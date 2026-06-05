"""CLI: generate demo assets.

    python -m chronicle_forge.reporting [SEED] [--out DIR] [--no-png]
    python -m chronicle_forge.reporting gallery [--out FILE]

Default writes docs/examples/seed<SEED>/. The `gallery` target writes the
multi-world showcase (docs/examples/gallery.md). Read-only on game state; no AI.
"""

from __future__ import annotations

import argparse

from .build import build_gallery, build_seed_assets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chronicle_forge.reporting")
    parser.add_argument(
        "target", nargs="?", default="42", help="a seed number, or 'gallery'"
    )
    parser.add_argument("--out", default=None)
    parser.add_argument("--no-png", action="store_true", help="skip PNG rendering")
    args = parser.parse_args(argv)

    if args.target == "gallery":
        out = args.out or "docs/examples/gallery.md"
        path = build_gallery(out=out)
        print(f"Generated gallery: {path}")
        return 0

    out = args.out or "docs/examples"
    written = build_seed_assets(int(args.target), out_dir=out, png=not args.no_png)
    print(f"Generated {len(written)} files for seed {args.target}:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
