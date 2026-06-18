"""Entrypoint for ``python -m chronicle_forge.play``.

The CLI only *starts or replays a world*: it parses arguments, reads an optional
replay script, forwards to the adapter (play) or the persistence replay (replay),
and lets the writer emit the transcript to stdout. It holds no game logic, draws
no RNG, and reads no clock — determinism lives in the seed/recipe alone.
``--debug`` adds a structured trace on stderr; stdout remains a clean transcript
regardless.
"""

from __future__ import annotations

import json
import sys
from typing import Optional, Sequence

from ..persistence import read_recipe, replay_file, save_recipe, write_export
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
    if args.replay_path is not None:
        return _run_replay(args)
    return _run_play(args)


def _run_replay(args: PlayArgs) -> int:
    """Replay a saved recipe, regenerating its transcript to stdout. ``--export``
    additionally writes a transcript artifact (stdout is unchanged)."""
    if args.debug:
        _log(sys.stderr, event="replay", recipe=args.replay_path)
    replay_file(args.replay_path, writer=sys.stdout.write)
    if args.export_path is not None:
        write_export(read_recipe(args.replay_path), args.export_path)
    return 0


def _run_play(args: PlayArgs) -> int:
    """Grow a seed. Identical to the prior play path; ``--save``/``--export``
    additionally write the recorded recipe / a transcript artifact (the stdout
    transcript is unchanged)."""
    script_lines = _read_script(args.script_path) if args.script_path else None
    mode = _mode(args)

    if args.debug:
        _log(sys.stderr, event="start", mode=mode, seed=args.seed)

    if args.save_path is not None or args.export_path is not None:
        world, recipe = adapter.play_and_record(
            seed=args.seed,
            auto=args.auto,
            script_lines=script_lines,
            mode=mode,
            writer=sys.stdout.write,
        )
        if args.save_path is not None:
            save_recipe(recipe, args.save_path)
        if args.export_path is not None:
            write_export(recipe, args.export_path)
    else:
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
