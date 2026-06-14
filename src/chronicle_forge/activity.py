"""Activity execution (section 4.4).

Performing an activity is the single funnel through which a life produces a
causal seed, accrues evaluation, optionally forms a memory, and ages. Play
archetypes emerge from the distribution of activities a life performs.
"""

from __future__ import annotations

from typing import Optional

from .enums import (
    ActivityCategory,
    EvaluationLens,
    MemoryType,
    PlayerInteraction,
    SeedDomain,
)
from .ids import next_id
from .inheritance import activity_bonus
from .life import advance_time
from .memory import form_memory
from .models import ActivityRecord, CausalSeed, Evaluation, Life, World
from .profiles import ACTIVITY_PROFILES

ACTIVITY_BASE_EVAL = 10
TALENT_EVAL_BONUS = 5
DEFAULT_MAGNITUDE = 50
TALENT_MAGNITUDE_BONUS = 20
ACTIVITY_TURN_COST = 1

# Longer-horizon domains mature later (delayed-reward design, section 5).
MATURATION_BY_DOMAIN: dict[SeedDomain, int] = {
    SeedDomain.HERITAGE: 10,
    SeedDomain.MONUMENT: 10,
    SeedDomain.GOVERNANCE: 8,
    SeedDomain.TECHNOLOGY: 8,
}
DEFAULT_MATURATION = 5

# When an activity targets an NPC, what kind of memory it forms.
_MEMORY_FOR: dict[ActivityCategory, MemoryType] = {
    ActivityCategory.EDUCATION: MemoryType.EDUCATED,
    ActivityCategory.RELIGION: MemoryType.EDUCATED,
    ActivityCategory.POLITICS: MemoryType.SAVED,
}

# E-1 (P6 Execution Layer): how a player's stance toward a WildCard maps to an
# existing activity verb. Support -> back them politically; Eliminate -> move
# against them; Exploit -> profit from them.
_WILDCARD_INTERACTION_CATEGORY: dict[PlayerInteraction, ActivityCategory] = {
    PlayerInteraction.SUPPORT: ActivityCategory.POLITICS,
    PlayerInteraction.ELIMINATE: ActivityCategory.COMBAT,
    PlayerInteraction.EXPLOIT: ActivityCategory.COMMERCE,
}


def _add_eval(evaluation: Evaluation, lens: EvaluationLens, amount: int) -> None:
    setattr(evaluation, lens.value, getattr(evaluation, lens.value) + amount)


def perform_activity(
    world: World,
    life: Life,
    category: ActivityCategory,
    target_id: Optional[str] = None,
    maturation_time: Optional[int] = None,
) -> CausalSeed:
    """Execute one activity action and return the causal seed it plants."""
    profile = ACTIVITY_PROFILES[category]
    talent_match = life.talent is not None and life.talent == profile.talent_affinity
    inh_eval, inh_magnitude = activity_bonus(world.player, category)

    magnitude = min(
        100,
        DEFAULT_MAGNITUDE
        + (TALENT_MAGNITUDE_BONUS if talent_match else 0)
        + inh_magnitude,
    )
    mt = (
        maturation_time
        if maturation_time is not None
        else MATURATION_BY_DOMAIN.get(profile.seed_domain, DEFAULT_MATURATION)
    )

    seed = CausalSeed(
        id=next_id("seed", world.seeds),
        domain=profile.seed_domain,
        magnitude=magnitude,
        target_id=target_id,
        maturation_time=mt,
        planted_year=world.current_year,
        planted_by_life_id=life.id,
    )
    world.seeds.append(seed)

    bonus = (TALENT_EVAL_BONUS if talent_match else 0) + inh_eval
    _add_eval(life.evaluation, profile.primary_lens, ACTIVITY_BASE_EVAL + bonus)
    for lens in profile.secondary_lenses:
        _add_eval(life.evaluation, lens, (ACTIVITY_BASE_EVAL + bonus) // 2)

    life.activity_log.append(
        ActivityRecord(
            category=category.value, world_year=world.current_year, seed_id=seed.id
        )
    )

    if target_id is not None and any(n.id == target_id for n in world.npcs):
        form_memory(
            world,
            subject_id=target_id,
            actor_id=life.player_id,
            mtype=_MEMORY_FOR.get(category, MemoryType.EDUCATED),
            valence=30,
            intensity=50,
        )

    advance_time(world, life, ACTIVITY_TURN_COST)
    return seed


def engage_wildcard(
    world: World,
    life: Life,
    wc_id: str,
    interaction: PlayerInteraction,
) -> CausalSeed:
    """E-1: engage a WildCard via an existing activity (thin wrapper).

    Contract (binding — keeps the world-mutation funnel single-sourced; see E-1
    in docs/design_p6_execution.md):

    Allowed:
      * one ``perform_activity`` call (the single mutation path)
      * set ``wc.player_interaction`` (latest-wins)

    Forbidden:
      * generating its own CausalSeed / Memory / Discovery
      * consuming its own turn (only ``perform_activity``'s single turn-advance)
      * altering any evaluation beyond what ``perform_activity`` accrues

    The wrapper adds no mechanics of its own. ``target_id=wc_id`` does not match
    any NPC id, so ``perform_activity`` forms no memory for it (WildCard rows of
    the S2 wiring table: seed only). It is also the future NPC<->WildCard hook.
    """
    category = _WILDCARD_INTERACTION_CATEGORY[interaction]
    seed = perform_activity(world, life, category, target_id=wc_id)
    for wc in world.wildcards.wildcards:
        if wc.id == wc_id:
            wc.player_interaction = interaction
            break
    return seed
