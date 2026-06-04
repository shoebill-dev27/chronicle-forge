"""World Theme computation (section C) — P3.5 recent-event model.

The theme is a *moving window* of recent history, not an accumulator. Each axis
gets a structural pull from faction power plus the recency-weighted weight of
recent causal events in its domain, plus the impact of any ignited WildCard.

Because old events leave the window, the theme mean-reverts toward baseline when
activity calms, and it keeps moving as long as history is being made (player
seeds firing, faction wars, NPC events, wildcards). This fixes the mid-run
"theme freeze" found in the P5 playtest.
"""

from __future__ import annotations

from . import config
from .enums import EventScale, FactionType, SeedDomain, ThemeAxis, WildCardStatus
from .models import ThemeSnapshot, World, WorldTheme

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

_SCALE_WEIGHT = {
    EventScale.LARGE: 6,
    EventScale.MEDIUM: 4,
    EventScale.SMALL: 2,
}


def compute_theme(world: World) -> WorldTheme:
    """Recompute the world theme from recent events and append a snapshot."""
    axes: dict[ThemeAxis, int] = {axis: config.THEME_BASE_AXIS for axis in ThemeAxis}

    # Structural pull: faction power.
    for faction in world.factions:
        axes[FACTION_TYPE_TO_THEME[faction.type]] += faction.power // 10

    # Recent events (recency-weighted) within the window.
    window = config.THEME_EVENT_WINDOW
    for node in world.causal_nodes:
        age = world.current_year - node.year
        if 0 <= age < window:
            recency = (window - age) / window  # 1.0 newest -> ~0 oldest
            axis = SEED_DOMAIN_TO_THEME[node.domain]
            axes[axis] += round(_SCALE_WEIGHT[node.scale] * recency)

    # Ignited WildCards exert a persistent push while active.
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
