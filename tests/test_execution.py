"""Tests for the P6 Execution Layer (docs/design_p6_execution.md)."""

from __future__ import annotations

import pytest

from chronicle_forge.activity import (
    _WILDCARD_INTERACTION_CATEGORY,
    engage_wildcard,
)
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.enums import (
    ActivityCategory,
    FactionType,
    HeritageType,
    PlayerInteraction,
    ThemeAxis,
)
from chronicle_forge.execution import (
    AXIS_TO_CATEGORY,
    EXECUTION_SALT,
    HERITAGE_TYPE_TO_CATEGORY,
    ExecutionOption,
    execute_option,
    expand_options,
    make_auto_chooser,
    play_turn,
)
from chronicle_forge.life import begin_life
from chronicle_forge.macro import derive_rng
from chronicle_forge.opportunity import (
    WILDCARD_PERIL_ARCHETYPES,
    OpportunityKind,
    OpportunitySession,
    build_indexes,
    npc_signals,
    select_opportunities,
    wildcard_signals,
)
from chronicle_forge.theme import FACTION_TYPE_TO_THEME
from chronicle_forge.worldgen import generate_world

SEED = 42


def _exec_rng(world, mixer=0):
    return derive_rng(world, mixer, salt=EXECUTION_SALT)


def _fresh_life(world):
    return begin_life(world, talent=None)


# --- mapping-table totality (D-3 canonical maps) ------------------------


def test_axis_to_category_total():
    assert set(AXIS_TO_CATEGORY) == set(ThemeAxis)
    for cat in AXIS_TO_CATEGORY.values():
        assert isinstance(cat, ActivityCategory)


def test_heritage_type_to_category_total():
    assert set(HERITAGE_TYPE_TO_CATEGORY) == set(HeritageType)
    for cat in HERITAGE_TYPE_TO_CATEGORY.values():
        assert isinstance(cat, ActivityCategory)


def test_faction_type_resolves_to_a_category():
    # Every FactionType -> theme -> category path is total.
    for ftype in FactionType:
        axis = FACTION_TYPE_TO_THEME[ftype]
        assert axis in AXIS_TO_CATEGORY


def test_wildcard_interaction_categories_total():
    # IGNORE is expressed by not selecting the opportunity, never as an action.
    engageable = {
        PlayerInteraction.SUPPORT,
        PlayerInteraction.ELIMINATE,
        PlayerInteraction.EXPLOIT,
    }
    assert set(_WILDCARD_INTERACTION_CATEGORY) == engageable


# --- order preservation (no re-rank / re-score) -------------------------


def test_expand_options_preserves_order_plus_fallback():
    world = generate_world(SEED)
    life = _fresh_life(world)
    session = OpportunitySession()
    opps = select_opportunities(world, life, session)
    options = expand_options(opps, world, life, _exec_rng(world))

    assert len(options) == len(opps) + 1
    for opp, opt in zip(opps, options[:-1]):
        assert opt.opportunity is opp  # same object, same position
    assert options[-1].opportunity is None  # fallback last
    assert options[-1].verb == "perform_activity"


# --- determinism --------------------------------------------------------


def test_expand_options_deterministic():
    world = generate_world(SEED)
    life = _fresh_life(world)
    session = OpportunitySession()
    opps = select_opportunities(world, life, session)

    a = expand_options(opps, world, life, _exec_rng(world))
    b = expand_options(opps, world, life, _exec_rng(world))
    key = lambda o: (
        o.verb,
        o.label,
        o.category,
        o.target_id,
        o.location_id,
        o.discovery_type,
        o.interaction,
    )
    assert [key(o) for o in a] == [key(o) for o in b]


def test_opportunity_mode_deterministic():
    w1 = simulate_world(SEED, mode="opportunity")
    w2 = simulate_world(SEED, mode="opportunity")
    assert w1.model_dump() == w2.model_dump()


# --- read-only / funnel-only --------------------------------------------


def test_expand_options_is_read_only_on_world():
    world = generate_world(SEED)
    life = _fresh_life(world)
    session = OpportunitySession()
    opps = select_opportunities(world, life, session)

    before = world.model_dump()
    expand_options(opps, world, life, _exec_rng(world))
    assert world.model_dump() == before


def _counts(world):
    return (len(world.seeds), len(world.memories), len(world.discoveries))


def test_execute_npc_mentor_uses_funnel_only():
    world = generate_world(SEED)
    life = _fresh_life(world)
    npc = next(n for n in world.npcs if n.alive)
    opt = ExecutionOption(
        opportunity=None,
        verb="perform_activity",
        label="Mentor",
        category=ActivityCategory.EDUCATION,
        target_id=npc.id,
    )
    s0, m0, d0 = _counts(world)
    execute_option(world, life, opt)
    s1, m1, d1 = _counts(world)
    # one seed, one memory (live NPC target), no discovery
    assert (s1 - s0, m1 - m0, d1 - d0) == (1, 1, 0)


def test_execute_location_explore_uses_funnel_only():
    from chronicle_forge.enums import DiscoveryType, LocationType

    world = generate_world(SEED)
    life = _fresh_life(world)
    dungeon = next(loc for loc in world.locations if loc.type is LocationType.DUNGEON)
    opt = ExecutionOption(
        opportunity=None,
        verb="explore_dungeon",
        label="Explore",
        location_id=dungeon.id,
        discovery_type=DiscoveryType.TECH,
    )
    s0, m0, d0 = _counts(world)
    execute_option(world, life, opt)
    s1, m1, d1 = _counts(world)
    assert (s1 - s0, m1 - m0, d1 - d0) == (1, 0, 1)


# --- E-1 engage_wildcard contract ---------------------------------------


def test_engage_wildcard_is_thin_wrapper():
    world = generate_world(SEED)
    life = _fresh_life(world)
    wc = world.wildcards.wildcards[0]
    assert wc.player_interaction is None

    s0, m0, d0 = _counts(world)
    turns0 = life.turns
    engage_wildcard(world, life, wc.id, PlayerInteraction.SUPPORT)
    s1, m1, d1 = _counts(world)

    # exactly one seed via perform_activity; no memory (wc id is not an NPC),
    # no discovery, exactly one turn advanced, interaction set.
    assert (s1 - s0, m1 - m0, d1 - d0) == (1, 0, 0)
    assert life.turns - turns0 == 1
    assert wc.player_interaction is PlayerInteraction.SUPPORT


def test_wildcard_engagement_sets_omega():
    world = generate_world(SEED)
    life = _fresh_life(world)
    wc = world.wildcards.wildcards[0]

    idx0 = build_indexes(world)
    assert wildcard_signals(wc, world, idx0).omega == pytest.approx(0.3)

    engage_wildcard(world, life, wc.id, PlayerInteraction.ELIMINATE)

    idx1 = build_indexes(world)
    assert wildcard_signals(wc, world, idx1).omega == pytest.approx(1.0)
    assert wc.archetype  # canonical archetype rule is exercised elsewhere


def test_canonical_wildcard_interaction_matches_peril_rule():
    world = generate_world(SEED)
    life = _fresh_life(world)
    session = OpportunitySession()
    opps = select_opportunities(world, life, session)
    options = expand_options(opps, world, life, _exec_rng(world))
    for opp, opt in zip(opps, options[:-1]):
        if opp.kind is OpportunityKind.WILDCARD:
            wc = next(w for w in world.wildcards.wildcards if w.id == opp.target_id)
            expected = (
                PlayerInteraction.ELIMINATE
                if wc.archetype in WILDCARD_PERIL_ARCHETYPES
                else PlayerInteraction.SUPPORT
            )
            assert opt.interaction is expected
            assert opt.verb == "engage_wildcard"


# --- loop closure (M9 risk surface) -------------------------------------


def test_loop_closure_npc_raises_omega():
    world = generate_world(SEED)
    life = _fresh_life(world)
    npc = next(n for n in world.npcs if n.alive)

    before = npc_signals(npc, world, build_indexes(world)).omega
    opt = ExecutionOption(
        opportunity=None,
        verb="perform_activity",
        label="Mentor",
        category=ActivityCategory.EDUCATION,
        target_id=npc.id,
    )
    execute_option(world, life, opt)
    after = npc_signals(npc, world, build_indexes(world)).omega
    assert after > before


# --- legacy protection (D-4) --------------------------------------------


def test_legacy_default_unchanged():
    # The default call and the explicit legacy mode are identical, and the
    # default path is deterministic run-to-run (golden-asset protection).
    default = simulate_world(SEED)
    explicit = simulate_world(SEED, mode="legacy")
    assert default.model_dump() == explicit.model_dump()
    assert simulate_world(SEED).model_dump() == default.model_dump()


def test_opportunity_mode_differs_from_legacy():
    legacy = simulate_world(SEED, mode="legacy")
    opp = simulate_world(SEED, mode="opportunity")
    assert legacy.model_dump() != opp.model_dump()


# --- full driven turn ---------------------------------------------------


def test_play_turn_advances_and_commits():
    world = generate_world(SEED)
    life = _fresh_life(world)
    session = OpportunitySession()
    rng = _exec_rng(world)
    chooser = make_auto_chooser(rng)

    turn0 = session.turn_index
    seeds0 = len(world.seeds)
    play_turn(world, life, session, chooser, rng)
    assert session.turn_index == turn0 + 1
    assert len(world.seeds) == seeds0 + 1  # exactly one funnel mutation
