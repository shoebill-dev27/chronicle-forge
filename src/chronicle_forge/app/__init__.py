"""P15 Vertical Slice — Application Layer.

The thin use-case seam that owns the product's one-way path,
``play → save → explore → share``, composed entirely from existing parts (P8 play, P9
persistence, P10–P14 reporting lenses). It adds no truth and changes no existing API;
the CLI (a later phase) is a thin wrapper over this surface.
"""

from __future__ import annotations

from .contracts import (
    SCHEMA_VERSION,
    ChronicleView,
    PlayOutcome,
    PlayRequest,
    ShareRequest,
    ShareResult,
)
from .services import (
    chronicle_json,
    chronicle_markdown,
    explore,
    explore_file,
    play,
    save_recipe_file,
    share,
    share_file,
)

__all__ = [
    "SCHEMA_VERSION",
    "PlayRequest",
    "PlayOutcome",
    "ChronicleView",
    "ShareRequest",
    "ShareResult",
    "play",
    "explore",
    "explore_file",
    "chronicle_json",
    "chronicle_markdown",
    "share",
    "share_file",
    "save_recipe_file",
]
