"""Macro loop (section 4.1): post-death world time-skip and yearly world update.

This is the heart of "a reincarnator leaves a mark on the future": a life plants
seeds, dies, and during the skip those seeds fire into world events that shape
the world the next life is born into.

Determinism (R3): every stochastic step derives its RNG from
``(world.seed, world.current_year)`` via :func:`derive_rng` using pure
arithmetic (no salted built-in hashing), so the same world seed and the same
sequence of player actions reproduce an identical world history.
"""

from __future__ import annotations

from typing import Optional

from .causal import CausalGraph
from .enums import (
    ActivationMode,
    CausalEdgeKind,
    EventScale,
    SeedDomain,
    ThemeAxis,
    WildCardStatus,
)
from .generation import fire_seeds, generate_events
from .heritage import promote_heritage
from .ids import next_id
from .life import begin_life
from .models import CausalNode, CausalSeed, Life, World
from .rng import DeterministicRNG
from .theme import (
    FACTION_TYPE_TO_THEME,
    SEED_DOMAIN_TO_THEME,
    compute_theme,
)
from .timeskip import compute_skip_years

# --- deterministic per-year RNG ----------------------------------------

_MOD = 2**31 - 1


def derive_rng(world: World, year: int, salt: int = 0) -> DeterministicRNG:
    """A reproducible RNG keyed to the world seed and a given year."""
    base = world.seed & 0x7FFFFFFF
    mixed = (base * 1_000_003 + year * 9_176 + salt * 12_289) % _MOD
    return DeterministicRNG(mixed)


# --- probabilistic seed firing (priority 3) ----------------------------


def _firing_probability(world: World, seed: CausalSeed) -> float:
    """Theme-aligned seeds are more likely to fire (section 9.3)."""
    axis = SEED_DOMAIN_TO_THEME[seed.domain]
    theme_factor = world.theme.axes.get(axis, 0) / 100.0
    p = seed.base_probability * (0.5 + 0.5 * theme_factor)
    return max(0.0, min(1.0, p))


def fire_probabilistic_seeds(world: World, rng: DeterministicRNG) -> list[CausalSeed]:
    """Fire matured PROBABILISTIC seeds by their (state-scaled) probability."""
    candidates = [
        s
        for s in world.seeds
        if not s.fired
        and s.activation_mode == ActivationMode.PROBABILISTIC
        and world.current_year >= s.planted_year + s.maturation_time
    ]
    candidates.sort(key=lambda s: (s.planted_year, s.id))
    fired: list[CausalSeed] = []
    for seed in candidates:
        if rng.random() < _firing_probability(world, seed):
            seed.fired = True
            fired.append(seed)
    return fired


# --- WildCard self-progression (priority 4) ----------------------------

IGNITION_THEME_THRESHOLD = 40
IGNITION_PROBABILITY = 0.5

_AXIS_TO_DOMAIN: dict[ThemeAxis, SeedDomain] = {
    ThemeAxis.INNOVATION: SeedDomain.TECHNOLOGY,
    ThemeAxis.WARFARE: SeedDomain.MILITARY,
    ThemeAxis.FAITH: SeedDomain.FAITH,
    ThemeAxis.COMMERCE: SeedDomain.ECONOMY,
    ThemeAxis.GOVERNANCE: SeedDomain.GOVERNANCE,
    ThemeAxis.CULTURE: SeedDomain.HERITAGE,
}


def _wildcard_primary_axis(wildcard) -> Optional[ThemeAxis]:
    if not wildcard.impact_vector:
        return None
    return max(wildcard.impact_vector, key=wildcard.impact_vector.__getitem__)


def _emit_wildcard_event(
    world: World, graph: CausalGraph, wildcard, title: str
) -> CausalNode:
    """Create a wildcard event node, linking fired player seeds of the same axis
    as AMPLIFY co-causes (so player support traces into wildcard history)."""
    axis = _wildcard_primary_axis(wildcard)
    domain = _AXIS_TO_DOMAIN.get(axis, SeedDomain.GOVERNANCE)
    node = CausalNode(
        id=next_id("node", world.causal_nodes),
        scale=EventScale.MEDIUM,
        domain=domain,
        year=world.current_year,
        title=title,
        actors=[wildcard.id],
    )
    graph.add_node(node)
    for seed in world.seeds:
        if (
            seed.fired
            and seed.planted_by_life_id is not None
            and SEED_DOMAIN_TO_THEME[seed.domain] == axis
        ):
            graph.add_edge(seed.id, node.id, weight=20, kind=CausalEdgeKind.AMPLIFY)
    return node


def step_wildcards(world: World, graph: CausalGraph, rng: DeterministicRNG) -> None:
    for wildcard in world.wildcards.wildcards:
        if wildcard.status == WildCardStatus.DORMANT:
            axis = _wildcard_primary_axis(wildcard)
            if (
                axis is not None
                and world.theme.axes.get(axis, 0) >= IGNITION_THEME_THRESHOLD
                and rng.random() < IGNITION_PROBABILITY
            ):
                wildcard.status = WildCardStatus.IGNITED
                _emit_wildcard_event(
                    world,
                    graph,
                    wildcard,
                    f"{wildcard.name} ignites ({wildcard.archetype.value})",
                )
        elif wildcard.status == WildCardStatus.IGNITED:
            if wildcard.trajectory:
                stage = wildcard.trajectory.pop(0)
                _emit_wildcard_event(
                    world, graph, wildcard, f"{wildcard.name}: {stage}"
                )
                if not wildcard.trajectory:
                    wildcard.status = WildCardStatus.RESOLVED


# --- faction lifecycle (priority 5) ------------------------------------


def step_factions(world: World, rng: DeterministicRNG) -> None:
    """Faction power drifts toward the prevailing theme, with small jitter."""
    for faction in world.factions:
        axis = FACTION_TYPE_TO_THEME[faction.type]
        pull = (world.theme.axes.get(axis, 0) - 50) // 10
        jitter = rng.randint(-2, 2)
        faction.power = max(0, min(100, faction.power + pull + jitter))


# --- NPC lifecycle (priority 6) ----------------------------------------

NPC_DEATH_AGE = 80
NPC_DEATH_PROBABILITY = 0.3
NPC_PROMOTION_PROBABILITY = 0.1


def step_npcs_lifecycle(world: World, rng: DeterministicRNG) -> None:
    """Age NPCs; resolve old-age death and ambitious promotion (kept minimal)."""
    for npc in world.npcs:
        if not npc.alive:
            continue
        npc.lifecycle.age += 1
        if npc.lifecycle.age > NPC_DEATH_AGE and rng.random() < NPC_DEATH_PROBABILITY:
            npc.alive = False
        elif (
            npc.personality.ambitious > 70 and rng.random() < NPC_PROMOTION_PROBABILITY
        ):
            npc.lifecycle.occupation = "leader"


# --- yearly world update (priority 2) ----------------------------------


def advance_year(world: World, rng: Optional[DeterministicRNG] = None) -> dict:
    """Run one year of world simulation at ``world.current_year``.

    Order: fire seeds (guaranteed + probabilistic) -> generate events ->
    wildcard / faction / NPC steps -> recompute theme (snapshot) -> promote
    heritage. The caller advances ``current_year``; this operates on it.
    """
    rng = rng or derive_rng(world, world.current_year)
    graph = CausalGraph.from_world(world)

    fired = fire_seeds(world)
    fired += fire_probabilistic_seeds(world, rng)
    nodes = generate_events(world, fired, graph)

    step_wildcards(world, graph, rng)
    step_factions(world, rng)
    step_npcs_lifecycle(world, rng)

    theme = compute_theme(world)
    heritage = promote_heritage(world, graph)

    return {
        "year": world.current_year,
        "fired_seeds": fired,
        "new_nodes": nodes,
        "theme": theme,
        "heritage": heritage,
    }


# --- post-death time skip (priority 1) ---------------------------------


def time_skip(world: World, deceased_life: Life) -> dict:
    """Advance world time after a death (section 5), generating history yearly.

    Skip length = compute_skip_years(age_at_death, sum of the deceased life's
    not-yet-fired seed maturation times), clamped so the world never exceeds its
    max year.
    """
    pending = [
        s
        for s in world.seeds
        if not s.fired and s.planted_by_life_id == deceased_life.id
    ]
    bonus = sum(s.maturation_time for s in pending)
    skip_years = compute_skip_years(deceased_life.age_at_death or 0, bonus)

    target = min(world.max_year, world.current_year + skip_years)
    years_run = 0
    while world.current_year < target:
        world.current_year += 1
        advance_year(world)
        years_run += 1

    return {
        "skip_years": skip_years,
        "years_run": years_run,
        "stopped_year": world.current_year,
        "world_ended": world.current_year >= world.max_year,
    }


def advance_to_next_life(
    world: World, deceased_life: Life, talent=None
) -> tuple[dict, Optional[Life]]:
    """Vertical slice: time-skip after a death, then reincarnate (unless the
    world has reached its max year)."""
    skip = time_skip(world, deceased_life)
    new_life = None if skip["world_ended"] else begin_life(world, talent=talent)
    return skip, new_life
