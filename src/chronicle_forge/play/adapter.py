"""Adapter for the P8 CLI — turn a parsed request into one session call.

This is the wiring between the CLI surface and :func:`run_human_world`. It
selects the input source and forwards; it holds no game logic, draws no RNG,
and reads no clock. Determinism lives entirely in the seed and the session
beneath it, so the CLI can never introduce an output diff of its own.
"""

from __future__ import annotations

import sys
from typing import Callable, Optional, Sequence

from .. import config
from ..persistence import build_recipe, recording_reader
from .human import scripted_reader
from .session import run_human_world

Reader = Callable[[], Optional[str]]
Writer = Callable[[str], None]


def _eof_reader() -> Optional[str]:
    """A player who is never there: every juncture is entrusted to the world.
    This is the ``--auto`` path, byte-identical to opportunity-mode autoplay."""
    return None


def _stdin_reader() -> Optional[str]:
    """Live stdin, EOF -> None. Used only when ``--save`` must record human
    input (the normal play path leaves stdin to the session)."""
    try:
        return input()
    except EOFError:
        return None


def build_reader(
    *, auto: bool, script_lines: Optional[Sequence[str]]
) -> Optional[Reader]:
    """Choose the input source. ``--script`` wins (deterministic replay), then
    ``--auto`` (EOF-equivalent), else ``None`` to let the session read live
    stdin. Pure selection: no world state, no RNG."""
    if script_lines is not None:
        return scripted_reader(script_lines)
    if auto:
        return _eof_reader
    return None


def run(
    *,
    seed: int,
    auto: bool = False,
    script_lines: Optional[Sequence[str]] = None,
    writer: Optional[Writer] = None,
    life_cap: int = 60,
):
    """Forward to :func:`run_human_world` with the chosen reader. The seed is
    the single source of determinism; this wrapper adds none of its own."""
    writer = writer or (lambda text: sys.stdout.write(text))
    reader = build_reader(auto=auto, script_lines=script_lines)
    return run_human_world(seed, reader=reader, writer=writer, life_cap=life_cap)


def play_and_record(
    *,
    seed: int,
    auto: bool = False,
    script_lines: Optional[Sequence[str]] = None,
    mode: str,
    writer: Optional[Writer] = None,
    life_cap: int = 60,
):
    """Play exactly as :func:`run`, but wrap the reader so the consumed input is
    captured and returned as a replayable Recipe. The transcript is unchanged
    (the recording reader is transparent); ``--save``'s only effect is the
    returned recipe. Returns ``(world, recipe)``."""
    writer = writer or (lambda text: sys.stdout.write(text))
    base = build_reader(auto=auto, script_lines=script_lines)
    if base is None:  # human path: make stdin explicit so it can be recorded
        base = _stdin_reader
    reader, captured = recording_reader(base)
    world = run_human_world(seed, reader=reader, writer=writer, life_cap=life_cap)
    recipe = build_recipe(
        seed=seed,
        max_year=config.DEV_WORLD_MAX_YEARS,
        mode=mode,
        inputs=captured,
    )
    return world, recipe
