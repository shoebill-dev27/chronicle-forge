"""P8 Player Experience — the dialogue between the player and history.

An interaction layer, not a UI framework. The world advances continuously
through the existing opportunity-mode engine; the player is asked for input
only at junctures the gate deems worthy. Everything here is read-only on the
world and isolated from P6 (selection) and P7 (interpretation), which it reuses
but never modifies.

    The world acts continuously.
    The player intervenes occasionally.
    History remembers selectively.
"""

from __future__ import annotations

from .gate import GateDecision, JunctureGate
from .human import make_human_chooser, make_script_chooser

__all__ = [
    "JunctureGate",
    "GateDecision",
    "make_human_chooser",
    "make_script_chooser",
]
