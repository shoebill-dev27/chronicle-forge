"""The Python side of the Living Chronicle client (ADR-002).

This is the ``js_api`` object exposed to the frontend; every method returns
plain JSON-serialisable dicts. It imports NO GUI toolkit (``webview`` is touched
only by ``shell.py``), so it is unit-testable without a display and cannot
affect the frozen engine goldens.

I-1b: the bridge no longer reads the game by parsing prose. It used to run the
engine and regex the printed ``turn_screen`` block back into fields, which could
recover exactly one of the loop's five beats and re-broke every time the
renderer changed wording. It now hands the frontend the typed beat stream
(:mod:`play.beats`) whole, so death / the years / the aftermath / the next life
are as available to the page as the juncture is.

What the client may draw is therefore bounded by what the engine produced: an
aftermath with no hardened mark carries no mark, and a juncture with no
recognition carries no ``recognition`` — the page has nothing to invent from.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from ..play import beats as beat_stream
from ..reporting._data import place
from ..worldgen import generate_world


class BookBridge:
    """The ``js_api`` object exposed to the frontend (ADR-002).

    Every method returns a plain dict; pywebview serialises it to JS. No method
    imports or requires a GUI backend.
    """

    def __init__(self, seed: int = 1) -> None:
        self._seed = seed

    def shelf(self) -> Dict:
        """P-01 (stub): an empty slot plus the real world name it opens into."""
        world = generate_world(self._seed)
        return {"empty_slot": True, "books": [], "invitation": place(world)}

    def play(
        self, seed: Optional[int] = None, choices: Optional[Sequence] = None
    ) -> Dict:
        """Play a whole world under ``choices`` and return its beat stream.

        ``choices`` are the displayed numbers the player sealed, in order; every
        juncture past the end of that list is entrusted to the world. Pure in
        ``(seed, choices)`` — calling it twice returns the same stream, and
        calling it with the empty list returns the run whose *first* juncture is
        the one the player is about to answer (the options at a juncture are
        drawn before the choice, so they do not depend on it).
        """
        seed = self._seed if seed is None else int(seed)
        picks: List[str] = [str(c) for c in (choices or [])]
        return beat_stream.to_dict(beat_stream.stream(seed, picks))
