"""Choosers for P8 — the human input boundary and a deterministic script chooser.

A chooser is the only thing that differs between the auto-player and a human
(see ``execution.play_turn``): it maps the offered options to a chosen index. The
choosers here are a pure I/O boundary — they read input and write prompts, but
never mutate the world, the options, the gate, or the render state, and they draw
no RNG of their own.

"Let this season pass" is not "do nothing": it *entrusts the turn to the world*.
Selecting ``[0]`` — or sending empty input / EOF — invokes ``on_let_pass``, which
the session wires to the auto-chooser, so the world acts exactly as it would on a
turn the player was never asked about.
"""

from __future__ import annotations

from typing import Callable, Optional

from . import render

# I/O contracts: a reader yields the next line (or None at EOF); a writer emits.
Reader = Callable[[], Optional[str]]
Writer = Callable[[str], None]
# Invoked when the player entrusts the turn to the world ([0] / empty / EOF).
LetPass = Callable[[list], int]

LET_IT_PASS = 0  # the display number for "entrust it to the world"
PROMPT = "▸ "  # "▸ "
INVALID = "Choose one of the listed numbers.\n"


def _has_fallback(options) -> bool:
    return any(o.opportunity is None for o in options)


def null_writer(_text: str) -> None:
    """A writer that discards output (used by the script chooser)."""


def scripted_reader(inputs) -> Reader:
    """A reader that yields each item of ``inputs`` once, then None forever (EOF).
    Deterministic: it consumes the fixed sequence in order."""
    queue = [str(x) for x in inputs]
    pos = {"i": 0}

    def reader() -> Optional[str]:
        i = pos["i"]
        if i >= len(queue):
            return None
        pos["i"] = i + 1
        return queue[i]

    return reader


def make_human_chooser(reader: Reader, writer: Writer, on_let_pass: LetPass):
    """Build a chooser driven by ``reader``/``writer``.

    Returns the real index into ``options`` for a valid pick (display 1..3),
    re-prompting on non-numeric or out-of-range input. ``[0]``, empty input, and
    EOF all entrust the turn to the world via ``on_let_pass(options)``. Pure: no
    world/option mutation, no RNG."""

    def chooser(options: list) -> int:
        while True:
            writer(PROMPT)
            raw = reader()
            writer("\n")  # terminate the prompt line (the input is not echoed here)
            if raw is None:  # EOF -> entrust to the world
                return on_let_pass(options)
            text = raw.strip()
            if text == "":  # empty -> entrust to the world
                return on_let_pass(options)
            try:
                number = int(text)
            except ValueError:  # non-numeric -> re-prompt
                writer(INVALID)
                continue
            if number == LET_IT_PASS and _has_fallback(options):
                return on_let_pass(options)
            index = render.option_index_for_choice(options, number)
            if index is None:  # out of range -> re-prompt
                writer(INVALID)
                continue
            return index

    return chooser


def _fallback_pass(options: list) -> int:
    """A deterministic 'entrust to the world' for contexts without an
    auto-chooser (e.g. tests): take the free-action fallback if present, else the
    first option. Draws no RNG."""
    for i, o in enumerate(options):
        if o.opportunity is None:
            return i
    return 0


def make_script_chooser(inputs, on_let_pass: Optional[LetPass] = None):
    """A deterministic chooser that consumes a fixed sequence of display numbers.

    Reuses the exact resolution of the human chooser (so invalid entries are
    consumed and re-prompted just the same), with a silent writer and a scripted
    reader. When the script is exhausted (EOF), the turn is entrusted to the
    world. ``on_let_pass`` defaults to a deterministic, RNG-free handler."""
    reader = scripted_reader(inputs)
    return make_human_chooser(reader, null_writer, on_let_pass or _fallback_pass)
