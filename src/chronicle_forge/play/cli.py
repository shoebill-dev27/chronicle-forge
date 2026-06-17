"""Argument parsing for ``python -m chronicle_forge.play``.

Pure mapping from argv to a typed request. It owns no game logic and writes
nothing of its own beyond argparse's usage/error messages. A run either grows a
seed (``--seed``, optionally recorded with ``--save``) or replays a saved recipe
(``--replay``); the two are mutually exclusive, since a replay carries its own
seed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class PlayArgs:
    """A parsed, immutable invocation request."""

    seed: Optional[int]
    auto: bool
    script_path: Optional[str]
    debug: bool
    save_path: Optional[str]
    replay_path: Optional[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m chronicle_forge.play",
        description="Play or replay a reincarnating Chronicle Forge world.",
    )
    # Exactly one source: grow a new seed, or replay a saved recipe.
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--seed",
        type=int,
        default=None,
        help="world seed; fixes worldgen and every life's RNG stream",
    )
    source.add_argument(
        "--replay",
        dest="replay_path",
        default=None,
        metavar="FILE",
        help="replay a saved recipe, regenerating its transcript (excludes --seed)",
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
        "--save",
        dest="save_path",
        default=None,
        metavar="FILE",
        help="after the play, write the run as a replayable recipe to FILE",
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
        save_path=ns.save_path,
        replay_path=ns.replay_path,
    )
