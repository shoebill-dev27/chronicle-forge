"""Ending classification from world state (no AI).

A simple, deterministic mapping from the final dominant theme axis to an ending
class, so the observability report can label how a world turned out. P6 may
refine this; for now it is derived purely from the World Theme.
"""

from __future__ import annotations

from .enums import ThemeAxis
from .models import World

_AXIS_TO_ENDING: dict[ThemeAxis, str] = {
    ThemeAxis.CULTURE: "Golden Age",
    ThemeAxis.GOVERNANCE: "Imperial Age",
    ThemeAxis.FAITH: "Theocratic Age",
    ThemeAxis.WARFARE: "Warring Age",
    ThemeAxis.INNOVATION: "Arcane Age",
    ThemeAxis.COMMERCE: "Mercantile Age",
}

APOCALYPSE_WARFARE_THRESHOLD = 75


def classify_ending(world: World) -> str:
    """Return (and store on the world) an ending classification."""
    axes = world.theme.axes
    if axes.get(ThemeAxis.WARFARE, 0) >= APOCALYPSE_WARFARE_THRESHOLD:
        world.ending_class = "Apocalyptic Age"
        return world.ending_class
    dominant = world.theme.dominant
    world.ending_class = (
        _AXIS_TO_ENDING.get(dominant, "Forgotten Age") if dominant else "Forgotten Age"
    )
    return world.ending_class
