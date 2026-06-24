"""P6 Execution Layer — Opportunity -> Action (see docs/design_p6_execution.md).

P6 Salience presents 3-5 tension-ranked :class:`Opportunity` objects per turn but
nothing consumes them. This volatile layer converts each offered opportunity into
an *executable player action* (exactly one existing engine-verb call) so that
opportunities can actually drive play, for both the deterministic auto-player and
a future human player.

Boundaries (hard constraints from the P6 observation review):
  * P6 tension is **not** recomputed, and opportunities are **never** re-ranked,
    filtered, or re-scored here -- the list from ``select_opportunities`` is used
    in the exact order given (already sorted by tension), plus a trailing
    free-action fallback.
  * This layer **creates nothing**: every world mutation goes through the engine
    funnel verbs (``perform_activity`` / ``explore_dungeon`` / ``engage_wildcard``).
    ``execution.py`` never constructs a CausalSeed / Memory / Discovery itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .activity import engage_wildcard, perform_activity
from .discovery import explore_dungeon
from .enums import (
    ActivityCategory,
    DiscoveryType,
    HeritageType,
    LocationType,
    PlayerInteraction,
    Talent,
    ThemeAxis,
)
from .models import Life, World
from .opportunity import (
    WILDCARD_PERIL_ARCHETYPES,
    Opportunity,
    OpportunityKind,
    OpportunitySession,
    select_opportunities,
)
from .profiles import ACTIVITY_PROFILES
from .rng import DeterministicRNG
from .theme import FACTION_TYPE_TO_THEME

# Salt for the execution RNG (option flavor + auto-chooser); distinct from
# autoplay's 99 and salience's 77 so the streams never collide.
EXECUTION_SALT = 55

# Probability the deterministic auto-chooser takes the top (highest-tension)
# option; otherwise it explores uniformly over the remaining options (incl. the
# fallback) so observation sees the whole taxonomy, not just the top slot.
P_TOP = 0.7

# NPC canonical-action threshold: a sufficiently perilous person (Rho) is
# stabilized politically (Advocate, SAVED memory) rather than mentored.
NPC_ADVOCATE_RHO = 0.5


# --- explicit static mapping tables -------------------------------------
#
# Declared, not derived: the inverse of ``ActivityProfile.theme_push`` is
# ambiguous (CULTURE maps to both EDUCATION and CONSTRUCTION), so the canonical
# axis/heritage -> category choice is written down here and asserted total by
# ``test_execution``.

AXIS_TO_CATEGORY: dict[ThemeAxis, ActivityCategory] = {
    ThemeAxis.WARFARE: ActivityCategory.COMBAT,
    ThemeAxis.INNOVATION: ActivityCategory.RESEARCH,
    ThemeAxis.FAITH: ActivityCategory.RELIGION,
    ThemeAxis.COMMERCE: ActivityCategory.COMMERCE,
    ThemeAxis.GOVERNANCE: ActivityCategory.POLITICS,
    ThemeAxis.CULTURE: ActivityCategory.EDUCATION,
}

HERITAGE_TYPE_TO_CATEGORY: dict[HeritageType, ActivityCategory] = {
    HeritageType.SCHOOL: ActivityCategory.EDUCATION,
    HeritageType.THOUGHT: ActivityCategory.EDUCATION,
    HeritageType.HEIR: ActivityCategory.EDUCATION,
    HeritageType.TECHNOLOGY: ActivityCategory.RESEARCH,
    HeritageType.INSTITUTION: ActivityCategory.POLITICS,
    HeritageType.MONUMENT: ActivityCategory.CONSTRUCTION,
}


# --- option data type ---------------------------------------------------


@dataclass
class ExecutionOption:
    """One executable action derived from an opportunity (volatile; never
    persisted). Exactly one engine verb + its parameters."""

    opportunity: Optional[Opportunity]  # None for the free-action fallback
    verb: str  # "perform_activity" | "explore_dungeon" | "engage_wildcard"
    label: str  # for display / logging
    category: Optional[ActivityCategory] = None
    target_id: Optional[str] = None
    location_id: Optional[str] = None
    discovery_type: Optional[DiscoveryType] = None
    interaction: Optional[PlayerInteraction] = None


Chooser = Callable[[list[ExecutionOption]], int]  # picks an option index


# --- read-only lookups --------------------------------------------------


def _faction_by_id(world: World, fid: str):
    return next((f for f in world.factions if f.id == fid), None)


def _location_by_id(world: World, lid: str):
    return next((loc for loc in world.locations if loc.id == lid), None)


def _wildcard_by_id(world: World, wid: str):
    return next((wc for wc in world.wildcards.wildcards if wc.id == wid), None)


def _heritage_by_id(world: World, hid: str):
    return next((h for h in world.heritage if h.id == hid), None)


# --- Opportunity -> canonical ExecutionOption ---------------------------


def _canonical_option(
    opp: Opportunity, world: World, discovered: set[str], rng: DeterministicRNG
) -> ExecutionOption:
    """Map one opportunity to its single MVP canonical action. Reads the
    opportunity's already-computed ``signals`` (not a re-score) for flavor."""
    kind = opp.kind

    if kind is OpportunityKind.NPC:
        if opp.signals.rho >= NPC_ADVOCATE_RHO:
            return ExecutionOption(
                opp,
                "perform_activity",
                f"Advocate {opp.name}",
                category=ActivityCategory.POLITICS,
                target_id=opp.target_id,
            )
        return ExecutionOption(
            opp,
            "perform_activity",
            f"Mentor {opp.name}",
            category=ActivityCategory.EDUCATION,
            target_id=opp.target_id,
        )

    if kind is OpportunityKind.FACTION:
        fac = _faction_by_id(world, opp.target_id)
        category = AXIS_TO_CATEGORY[FACTION_TYPE_TO_THEME[fac.type]]
        return ExecutionOption(
            opp,
            "perform_activity",
            f"Further {opp.name}",
            category=category,
            target_id=None,
        )

    if kind is OpportunityKind.LOCATION:
        loc = _location_by_id(world, opp.target_id)
        if loc.type is LocationType.DUNGEON and loc.id not in discovered:
            return ExecutionOption(
                opp,
                "explore_dungeon",
                f"Explore {opp.name}",
                location_id=loc.id,
                discovery_type=rng.choice(list(DiscoveryType)),
            )
        return ExecutionOption(
            opp,
            "perform_activity",
            f"Develop {opp.name}",
            category=ActivityCategory.CONSTRUCTION,
            target_id=None,
        )

    if kind is OpportunityKind.WILDCARD:
        wc = _wildcard_by_id(world, opp.target_id)
        interaction = (
            PlayerInteraction.ELIMINATE
            if wc.archetype in WILDCARD_PERIL_ARCHETYPES
            else PlayerInteraction.SUPPORT
        )
        return ExecutionOption(
            opp,
            "engage_wildcard",
            f"{interaction.value} {opp.name}",
            target_id=opp.target_id,
            interaction=interaction,
        )

    # Legacy actions continue a tradition by planting new seeds.
    # They do NOT modify existing HeritageNodes.
    # Current MVP semantics: "continue the tradition and plant a new seed",
    # NOT "strengthen the heritage". Heritage reinforcement is the
    # responsibility of a future dedicated verb (see L-2 in
    # docs/design_p6_execution.md).
    her = _heritage_by_id(world, opp.target_id)
    category = HERITAGE_TYPE_TO_CATEGORY[her.type]
    return ExecutionOption(
        opp,
        "perform_activity",
        f"Tend {opp.name}",
        category=category,
        target_id=None,
    )


def _fallback_option(life: Life, rng: DeterministicRNG) -> ExecutionOption:
    """The free-action fallback (D-2): a legacy-talent-policy untargeted
    activity, always offered last. Declining all opportunities is allowed."""
    category = _pick_free_activity(rng, life.talent)
    return ExecutionOption(
        None,
        "perform_activity",
        f"Free action ({category.value})",
        category=category,
        target_id=None,
    )


_TALENT_ACTIVITY = {p.talent_affinity: c for c, p in ACTIVITY_PROFILES.items()}


def _pick_free_activity(
    rng: DeterministicRNG, talent: Optional[Talent]
) -> ActivityCategory:
    """Mirror of autoplay's legacy ``_pick_activity`` for the fallback option."""
    if rng.random() < 0.6 and talent in _TALENT_ACTIVITY:
        return _TALENT_ACTIVITY[talent]
    return rng.choice(list(ActivityCategory))


def expand_options(
    opps: list[Opportunity], world: World, life: Life, rng: DeterministicRNG
) -> list[ExecutionOption]:
    """Convert the offered opportunities into executable options, order preserved
    1:1, plus a trailing free-action fallback. Pure and read-only on ``world``;
    deterministic for a given ``rng``."""
    discovered = {d.location_id for d in world.discoveries}
    options = [_canonical_option(opp, world, discovered, rng) for opp in opps]
    options.append(_fallback_option(life, rng))
    return options


# --- execution (the only mutation point) --------------------------------


def execute_option(world: World, life: Life, option: ExecutionOption) -> object:
    """Run the option's single engine verb. The Execution Layer mutates the
    world only here, and only via the funnel verbs."""
    if option.verb == "perform_activity":
        return perform_activity(
            world, life, option.category, target_id=option.target_id
        )
    if option.verb == "explore_dungeon":
        return explore_dungeon(world, life, option.location_id, option.discovery_type)
    if option.verb == "engage_wildcard":
        return engage_wildcard(world, life, option.target_id, option.interaction)
    raise ValueError(f"unknown execution verb: {option.verb!r}")


# --- choosers -----------------------------------------------------------


def make_auto_chooser(rng: DeterministicRNG) -> Chooser:
    """Deterministic auto-chooser: P_TOP picks the top option (index 0, highest
    tension), otherwise a seeded uniform pick over the remaining options
    (including the fallback)."""

    def chooser(options: list[ExecutionOption]) -> int:
        if len(options) <= 1 or rng.random() < P_TOP:
            return 0
        return rng.randint(1, len(options) - 1)

    return chooser


# --- shared turn driver (autoplay & future human play) ------------------


def play_turn(
    world: World,
    life: Life,
    session: OpportunitySession,
    chooser: Chooser,
    rng: DeterministicRNG,
    social_memory: bool = False,
) -> ExecutionOption:
    """One opportunity-driven action-turn. Only the ``chooser`` differs between
    the auto-player and a human UI; everything else is shared. ``social_memory``
    (P11-B L2) gates the relation-bias on opportunity scoring."""
    opps = select_opportunities(world, life, session, social_memory)  # order kept
    options = expand_options(opps, world, life, rng)
    choice = options[chooser(options)]
    execute_option(world, life, choice)
    selected_id = choice.opportunity.target_id if choice.opportunity else None
    session.commit_turn(opps, selected_id)
    return choice
