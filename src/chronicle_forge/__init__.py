"""Chronicle Forge: a history-creation RPG / reincarnation roguelite.

See docs/design.md for the design-locked specification (v0.3). This package is
the rules-only core; AI integration (the 5 bounded call sites) and the
presentation layer are added in later roadmap phases.
"""

from __future__ import annotations

from .timeskip import compute_skip_years
from .worldgen import generate_world

__version__ = "0.3.0"

__all__ = ["generate_world", "compute_skip_years", "__version__"]
