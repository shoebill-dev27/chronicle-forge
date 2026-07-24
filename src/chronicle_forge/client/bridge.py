"""I-1 walking-skeleton bridge — the Python side of the Living Chronicle client.

ADR-002: the client renders app/engine data through a pywebview bridge and owns
only presentation + discovery state. This module is the ``js_api`` object exposed
to the frontend; every method returns plain JSON-serialisable dicts. It imports
NO GUI toolkit (``webview`` is touched only by ``shell.py``), so it is unit-
testable without a display and cannot affect the frozen engine goldens.

Scope note (I-1): ``open_juncture`` extracts a *real* first juncture from the
engine (parsing our own ``render.turn_screen`` output), proving the whole
play -> bridge -> page path. Sealing that advances a live world, and true
attribution for ``remember``, are the Life Loop (I-2) and Client State (D-6);
here ``seal``/``remember`` return clearly-marked stubs — the I-1 DoD asks only
that a hold *fires a stub reveal*.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..play.session import run_human_world
from ..reporting._data import place
from ..worldgen import generate_world

# `  [1] Some label   · Kind   (why now)`  — the turn_screen option grammar.
_OPTION_RE = re.compile(r"^\s*\[(\d+)\]\s+(.*?)\s+·\s+(\S+)\s+\((.+?)\)\s*$")


class _FirstJuncture(Exception):
    """Raised by the capture reader to halt the world at its first ask."""


def capture_first_juncture(seed: int, *, life_cap: int = 60) -> Dict:
    """Run the real interactive engine only as far as its first juncture and
    return that juncture's structured content. Deterministic in ``seed``; never
    completes a world, so no engine golden is touched."""
    blocks: List[str] = []

    def writer(text: str) -> None:
        blocks.append(text)

    def reader() -> Optional[str]:  # called at the first human ask -> halt
        raise _FirstJuncture

    try:
        run_human_world(seed, reader=reader, writer=writer, life_cap=life_cap)
    except _FirstJuncture:
        pass

    # The prompt "▸ " is emitted after the juncture, so scan back for the block
    # that actually carries option lines.
    juncture = ""
    for block in reversed(blocks):
        if any(_OPTION_RE.match(line) for line in block.splitlines()):
            juncture = block
            break

    header: List[str] = []
    options: List[Dict] = []
    for line in juncture.splitlines():
        m = _OPTION_RE.match(line)
        if m:
            options.append(
                {
                    "index": int(m.group(1)),
                    "label": m.group(2).strip(),
                    "kind": m.group(3).strip(),
                    "why": m.group(4).strip(),
                }
            )
        elif line.strip():
            header.append(line.strip())

    return {"header": header, "options": options}


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

    def open_juncture(self, seed: Optional[int] = None) -> Dict:
        """P-04 opening + P-06 juncture, from real engine data."""
        seed = self._seed if seed is None else int(seed)
        world = generate_world(seed)
        where = place(world)
        jn = capture_first_juncture(seed)
        options = jn["options"]
        # Skeleton hold demo: mark the first option (D-02 permits a mark on a
        # decision option) so the hold verb has a real target.
        marked_index = options[0]["index"] if options else None
        return {
            "seed": seed,
            "place": where,
            "opening": f"A life opens in {where}.",
            "header": jn["header"],
            "options": options,
            "marked_index": marked_index,
            "has_juncture": bool(options),
        }

    def seal(self, index: int) -> Dict:
        """I-1 stub. Real sealing advances a live world and appends to the recipe
        (Life Loop I-2 / Client State D-6)."""
        return {
            "sealed_index": int(index),
            "outcome": "The ink sets.  (skeleton — the outcome passage is I-2.)",
            "stub": True,
        }

    def remember(self, ref: Optional[str] = None) -> Dict:
        """I-1 stub reveal — the hold verb's payload. The real attribution and
        the Hand reveal grammar are D-3 / D-6 / I-2."""
        return {
            "hand": "……この手は、前にもこれを選んだ。",
            "epithet": "前世のあなた",
            "stub": True,
        }
