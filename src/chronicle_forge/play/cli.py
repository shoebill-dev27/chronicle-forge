"""Argument parsing for ``python -m chronicle_forge.play``.

Pure mapping from argv to a typed request. It owns no game logic and writes
nothing of its own beyond argparse's usage/error messages. The four switches
mirror the session's only degrees of freedom: which seed to grow, and where the
player's input comes from (live stdin, EOF-equivalent auto, or a replay script).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class PlayArgs:
    """A parsed, immutable invocation request."""

    seed: int
    auto: bool
    script_path: Optional[str]
    debug: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m chronicle_forge.play",
        description="Play a reincarnating Chronicle Forge world (P8).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="world seed; fixes worldgen and every life's RNG stream",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="run unattended: entrust every juncture to the world (EOF-equivalent)",
    )
    parser.add_argument(
        "--script",
        dest="script_path",
        default=None,
        metavar="FILE",
        help="replay file: one chosen number per line, fed to the script chooser",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="emit a structured trace on stderr (stdout stays a clean transcript)",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> PlayArgs:
    ns = build_parser().parse_args(argv)
    return PlayArgs(
        seed=ns.seed,
        auto=ns.auto,
        script_path=ns.script_path,
        debug=ns.debug,
    )
