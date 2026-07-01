"""P16 MVP Cohesion — the ``chronicle-forge`` console command.

A **thin wrapper** over the P15 Application Layer (:mod:`chronicle_forge.app`) — the
only integration boundary. This module owns argv parsing and rendering only: it holds
no game logic, draws no RNG, reads no clock, and never touches the engine, persistence,
or reporting directly (every side effect goes through ``app``). Following the existing
``play/__main__`` contract, **stdout is a clean transcript/chronicle** while all human
status ("saved …", hints, errors) goes to stderr.

    chronicle-forge play  --seed N (--auto | --script FILE) [--social-memory] [--save FILE] [--export FILE]
    chronicle-forge play  --replay FILE [--export FILE]
    chronicle-forge explore RECIPE [--format md|json]
    chronicle-forge share   RECIPE [--export FILE]
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__, app


def _read_lines(path: str) -> List[str]:
    """Read a script file into one chosen-line-per-entry list (plain text I/O, not
    persistence)."""
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chronicle-forge",
        description="Play, explore, and share a reincarnating Chronicle Forge world.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    play = sub.add_parser("play", help="generate or replay a world (deterministic)")
    source = play.add_mutually_exclusive_group(required=True)
    source.add_argument("--seed", type=int, help="world seed to grow")
    source.add_argument(
        "--replay", metavar="RECIPE", help="reprint a saved recipe's transcript"
    )
    play.add_argument(
        "--auto", action="store_true", help="witness a full unattended run"
    )
    play.add_argument(
        "--script", metavar="FILE", help="drive choices from a file (one per line)"
    )
    play.add_argument(
        "--social-memory",
        dest="social_memory",
        action="store_true",
        help="enable cross-life memory decay/bias (auto/script only)",
    )
    play.add_argument("--save", metavar="FILE", help="write the canonical recipe")
    play.add_argument("--export", metavar="FILE", help="write a transcript artifact")

    explore = sub.add_parser("explore", help="browse a saved world's chronicle")
    explore.add_argument("recipe", metavar="RECIPE")
    explore.add_argument("--format", choices=["md", "json"], default="md")

    share = sub.add_parser("share", help="emit a reproducible artifact for a recipe")
    share.add_argument("recipe", metavar="RECIPE")
    share.add_argument("--export", metavar="FILE", help="write a transcript artifact")

    return parser


def _cmd_play(args: argparse.Namespace) -> int:
    if args.replay is not None:
        result = app.share_file(args.replay, export_path=args.export)
        sys.stdout.write(result.transcript)
        if args.export is not None:
            sys.stderr.write(f"wrote transcript to {args.export}\n")
        return 0

    if not args.auto and args.script is None:
        sys.stderr.write(
            "interactive play is not available in this command yet; "
            "use `python -m chronicle_forge.play --seed N`\n"
        )
        return 2

    script_lines = _read_lines(args.script) if args.script else None
    outcome = app.play(
        app.PlayRequest(
            seed=args.seed,
            auto=args.auto,
            script_lines=script_lines,
            social_memory=args.social_memory,
        )
    )
    sys.stdout.write(outcome.transcript)
    if args.save is not None:
        app.save_recipe_file(outcome.recipe, args.save)
        sys.stderr.write(f"saved recipe to {args.save}\n")
    if args.export is not None:
        app.share(app.ShareRequest(recipe=outcome.recipe, export_path=args.export))
        sys.stderr.write(f"wrote transcript to {args.export}\n")
    return 0


def _cmd_explore(args: argparse.Namespace) -> int:
    view = app.explore_file(args.recipe)
    if args.format == "json":
        sys.stdout.write(view.model_dump_json() + "\n")
    else:
        sys.stdout.write(app.chronicle_markdown(view))
    return 0


def _cmd_share(args: argparse.Namespace) -> int:
    result = app.share_file(args.recipe, export_path=args.export)
    sys.stdout.write(result.reproducible_command + "\n")
    if args.export is not None:
        sys.stderr.write(f"wrote transcript to {args.export}\n")
    return 0


_COMMANDS = {"play": _cmd_play, "explore": _cmd_explore, "share": _cmd_share}


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("--version", "-V"):
        sys.stdout.write(f"chronicle-forge {__version__}\n")
        return 0

    args = build_parser().parse_args(argv)  # usage errors -> SystemExit(2)
    try:
        return _COMMANDS[args.command](args)
    except SystemExit:
        raise
    except Exception as exc:  # runtime refusal: invalid/mismatched recipe, missing file
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
