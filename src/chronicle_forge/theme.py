"""World Theme computation (section C).

The theme is recomputed from world state (faction power, fired seed domains,
ignited WildCard impact) on top of a baseline, then a :class:`ThemeSnapshot` is
appended to the trajectory. The theme is an emergent indicator that player
actions (via fired seeds) and WildCards push.
"""

from __future__ import annotations

from .enums import FactionType, SeedDomain, ThemeAxis, WildCardStatus
from .models import ThemeSnapshot, World, WorldTheme

BASE_AXIS = 20
SEED_PUSH = 5  # a fired seed's contribution
PLANTED_PUSH = 2  # an as-yet-unfired player seed's smaller contribution

SEED_DOMAIN_TO_THEME: dict[SeedDomain, ThemeAxis] = {
    SeedDomain.DISCOVERY: ThemeAxis.INNOVATION,
    SeedDomain.MILITARY: ThemeAxis.WARFARE,
    SeedDomain.TECHNOLOGY: ThemeAxis.INNOVATION,
    SeedDomain.HERITAGE: ThemeAxis.CULTURE,
    SeedDomain.GOVERNANCE: ThemeAxis.GOVERNANCE,
    SeedDomain.ECONOMY: ThemeAxis.COMMERCE,
    SeedDomain.FAITH: ThemeAxis.FAITH,
    SeedDomain.MONUMENT: ThemeAxis.CULTURE,
}

FACTION_TYPE_TO_THEME: dict[FactionType, ThemeAxis] = {
    FactionType.LORD: ThemeAxis.GOVERNANCE,
    FactionType.MERCHANT: ThemeAxis.COMMERCE,
    FactionType.RELIGIOUS: ThemeAxis.FAITH,
    FactionType.ADVENTURER: ThemeAxis.WARFARE,
}


def compute_theme(world: World) -> WorldTheme:
    """Recompute the world theme and append a snapshot for the current year."""
    axes: dict[ThemeAxis, int] = {axis: BASE_AXIS for axis in ThemeAxis}

    for faction in world.factions:
        axes[FACTION_TYPE_TO_THEME[faction.type]] += faction.power // 10

    for seed in world.seeds:
        if seed.fired:
            axes[SEED_DOMAIN_TO_THEME[seed.domain]] += SEED_PUSH
        elif seed.planted_by_life_id:  # player intent nudges the world (section C)
            axes[SEED_DOMAIN_TO_THEME[seed.domain]] += PLANTED_PUSH

    for wildcard in world.wildcards.wildcards:
        if wildcard.status == WildCardStatus.IGNITED:
            for axis, value in wildcard.impact_vector.items():
                axes[axis] += value

    axes = {axis: max(0, min(100, value)) for axis, value in axes.items()}
    dominant = max(axes, key=axes.__getitem__)

    world.theme.axes = axes
    world.theme.history.append(
        ThemeSnapshot(year=world.current_year, axes=dict(axes), dominant=dominant)
    )
    return world.theme
