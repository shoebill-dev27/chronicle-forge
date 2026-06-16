"""Entrypoint for ``python -m chronicle_forge.play``.

The CLI only *starts a world*: it parses arguments, reads an optional replay
script, forwards to the adapter, and lets the session write the transcript to
stdout. It holds no game logic, draws no RNG, and reads no clock — determinism
lives in the seed alone. ``--debug`` adds a structured trace on stderr; stdout
remains a clean transcript regardless.
"""

from __future__ import annotations

import json
import sys
from typing import Optional, Sequence

from . import adapter
from .cli import PlayArgs, parse_args


def _read_script(path: str) -> list[str]:
    """Read a replay file into one chosen-number-per-line list (no trailing
    newline handling needed: ``splitlines`` drops them)."""
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def _mode(args: PlayArgs) -> str:
    if args.script_path is not None:
        return "script"
    return "auto" if args.auto else "human"


def _log(stream, **fields) -> None:
    """Emit one structured (JSON) log line. Deterministic: sorted keys, no
    timestamp, so a ``--debug`` trace is itself reproducible."""
    stream.write(json.dumps(fields, sort_keys=True) + "\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    script_lines = _read_script(args.script_path) if args.script_path else None
    mode = _mode(args)

    if args.debug:
        _log(sys.stderr, event="start", mode=mode, seed=args.seed)

    world = adapter.run(
        seed=args.seed,
        auto=args.auto,
        script_lines=script_lines,
        writer=sys.stdout.write,
    )

    if args.debug:
        _log(
            sys.stderr,
            event="end",
            ending=str(getattr(world, "ending_class", None)),
            lives=len(world.lives),
            mode=mode,
            seed=args.seed,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
