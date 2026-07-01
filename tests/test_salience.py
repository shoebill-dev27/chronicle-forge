"""P6 Salience tests (T1-T32). Covers invariants I1-I12 plus the C1-C4 / R2 / R5
narrative-tension semantics. See docs/design_p6_salience.md.

These tests target the pure functions and the volatile selection layer in
``chronicle_forge.opportunity``; they never run the macro/autoplay loop, so they
cannot affect existing world snapshots.
"""

from __future__ import annotations

import pytest

from chronicle_forge import opportunity as opp_mod
from chronicle_forge.enums import (
    FactionType,
    HeritageType,
    LocationType,
    NPCTier,
    PlayerInteraction,
    SeedDomain,
    ThemeAxis,
    WildCardArchetype,
    WildCardStatus,
)
from chronicle_forge.models import (
    CausalSeed,
    Discovery,
    Faction,
    HeritageNode,
    Life,
    Lifecycle,
    Location,
    Memory,
    NPC,
    Personality,
    Player,
    WildCard,
    WildCardRegistry,
    World,
    WorldTheme,
)
from chronicle_forge.opportunity import (
    MAX_OPPORTUNITIES,
    Opportunity,
    OpportunityKind,
    OpportunitySession,
    Signals,
    assemble_tension,
    build_indexes,
    escalation_factor,
    faction_signals,
    legacy_signals,
    location_signals,
    npc_signals,
    select_opportunities,
    select_top_k,
)

# --- Wave 0: test fixtures / builders -----------------------------------


def make_world(
    *,
    npcs=None,
    factions=None,
    locations=None,
    wildcards=None,
    heritage=None,
    seeds=None,
    memories=None,
    discoveries=None,
    current_year=20,
    dominant=ThemeAxis.GOVERNANCE,
    seed=42,
):
    player = Player(id="player-0000")
    life = Life(id="life-0000", player_id=player.id, birth_year=0)
    axes = {a: 20 for a in ThemeAxis}
    axes[dominant] = 80
    world = World(
        id="w",
        seed=seed,
        max_year=200,
        current_year=current_year,
        player=player,
        theme=WorldTheme(axes=axes),
        npcs=npcs or [],
        factions=factions or [],
        locations=locations or [],
        wildcards=WildCardRegistry(wildcards=wildcards or []),
        heritage=heritage or [],
        seeds=seeds or [],
        memories=memories or [],
        discoveries=discoveries or [],
        lives=[life],
    )
    return world, life


def make_npc(
    npc_id,
    *,
    age=40,
    tier=NPCTier.A,
    alive=True,
    ambitious=50,
    brave=50,
    cautious=50,
    faction_id=None,
):
    return NPC(
        id=npc_id,
        name=npc_id,
        tier=tier,
        alive=alive,
        personality=Personality(brave=brave, ambitious=ambitious, cautious=cautious),
        lifecycle=Lifecycle(age=age, faction_id=faction_id),
    )


def make_faction(fac_id, ftype=FactionType.LORD, power=50, relations=None):
    return Faction(
        id=fac_id, type=ftype, name=fac_id, power=power, relations=relations or {}
    )


def make_loc(loc_id, ltype=LocationType.FIELD, theme_affinity=None):
    return Location(id=loc_id, type=ltype, name=loc_id, theme_affinity=theme_affinity)


def make_wc(
    wc_id,
    archetype=WildCardArchetype.PROPHET,
    status=WildCardStatus.DORMANT,
    trajectory=None,
    impact=None,
    interaction=None,
):
    return WildCard(
        id=wc_id,
        name=wc_id,
        archetype=archetype,
        status=status,
        trajectory=trajectory or [],
        impact_vector=impact or {},
        player_interaction=interaction,
    )


def make_heritage(
    her_id, *, seed_id="seed-0000", score=50, reach=0, htype=HeritageType.SCHOOL
):
    return HeritageNode(
        id=her_id,
        seed_id=seed_id,
        type=htype,
        reach=reach,
        longevity=score,
        heritage_score=score,
    )


def make_seed(
    seed_id,
    *,
    domain=SeedDomain.GOVERNANCE,
    target_id=None,
    planted_year=20,
    maturation=5,
    fired=False,
    life_id="life-0000",
):
    return CausalSeed(
        id=seed_id,
        domain=domain,
        magnitude=50,
        target_id=target_id,
        maturation_time=maturation,
        planted_year=planted_year,
        fired=fired,
        planted_by_life_id=life_id,
    )


def make_memory(mem_id, subject, actor="player-0000", intensity=50):
    return Memory(
        id=mem_id,
        subject_id=subject,
        actor_id=actor,
        type=opp_mod_memory_type(),
        valence=30,
        intensity=intensity,
    )


def opp_mod_memory_type():
    from chronicle_forge.enums import MemoryType

    return MemoryType.EDUCATED


def opp(kind, tid, tension, score=0):
    return Opportunity(kind, tid, tid, tension, Signals(), score)


def run(world, life, n, choose=None):
    """Drive n turns; return the list of offered target-id lists per turn."""
    choose = choose or (lambda o: o[0].target_id if o else None)
    session = OpportunitySession()
    log = []
    for _ in range(n):
        opps = select_opportunities(world, life, session)
        log.append([o.target_id for o in opps])
        session.commit_turn(opps, choose(opps))
    return log


# --- Wave 1: signal derivation ------------------------------------------


def test_T32_normalization_bounds():
    world, _ = make_world(
        npcs=[make_npc("npc-1", age=70, ambitious=90)],
        factions=[make_faction("fac-1", power=90)],
        locations=[make_loc("loc-1", LocationType.DUNGEON)],
        wildcards=[
            make_wc(
                "wc-1",
                WildCardArchetype.CONQUEROR,
                WildCardStatus.IGNITED,
                impact={ThemeAxis.WARFARE: 90},
            )
        ],
        heritage=[make_heritage("her-1", score=80)],
    )
    idx = build_indexes(world)
    sigs = [
        npc_signals(world.npcs[0], world, idx),
        faction_signals(world.factions[0], world, idx),
        location_signals(world.locations[0], world, idx),
        opp_mod.wildcard_signals(world.wildcards.wildcards[0], world, idx),
        legacy_signals(world.heritage[0], idx, last_score=0),
    ]
    for s in sigs:
        for v in (s.delta, s.sigma, s.omega, s.rho):
            assert 0.0 <= v <= 1.0
        assert assemble_tension(s, 0) == pytest.approx(assemble_tension(s, 0))


def test_index_memory_discovery_and_nonplayer_seed():
    """Cover the memory/discovery indexes and the open-loop signals they feed."""
    mem = make_memory("mem-1", subject="npc-1", intensity=50)
    npc = make_npc("npc-1")
    disc = Discovery(
        id="disc-1",
        type=opp_mod_discovery_type(),
        location_id="loc-1",
        theme_affinity=ThemeAxis.INNOVATION,
        seed_id="seed-x",
    )
    nonplayer_seed = make_seed("seed-np", target_id="npc-1", life_id=None)
    world, _ = make_world(
        npcs=[npc],
        locations=[make_loc("loc-1", LocationType.DUNGEON)],
        memories=[mem],
        discoveries=[disc],
        seeds=[nonplayer_seed],
    )
    idx = build_indexes(world)
    assert idx.memories_by_subject["npc-1"]  # line covered
    assert idx.discoveries_by_location["loc-1"]
    assert "npc-1" not in idx.seeds_by_target  # non-player seed skipped

    # NPC open-loop reflects the active player memory.
    assert npc_signals(npc, world, idx).omega == pytest.approx(1 / 3)
    # Discovered dungeon: frontier gone, but discovery feeds Location open-loop.
    loc_sig = location_signals(world.locations[0], world, idx)
    assert loc_sig.omega > 0 and loc_sig.delta == pytest.approx(0.2)


def opp_mod_discovery_type():
    from chronicle_forge.enums import DiscoveryType

    return DiscoveryType.TECH


def test_T17_npc_peril_from_personality():
    world, _ = make_world()
    idx = build_indexes(world)
    volatile = make_npc("a", brave=90, ambitious=90, cautious=10)
    steady = make_npc("b", brave=10, ambitious=10, cautious=90)
    rho_hi = npc_signals(volatile, world, idx).rho
    rho_lo = npc_signals(steady, world, idx).rho
    assert rho_hi > 0  # no negative memories needed
    assert rho_hi > rho_lo


def test_T15_npc_mortality_requires_investment():
    # Old NPC, no investment -> mortality contributes nothing (Delta == 0).
    world, _ = make_world(npcs=[make_npc("npc-1", age=70)])
    idx = build_indexes(world)
    assert npc_signals(world.npcs[0], world, idx).delta == 0.0

    # Same NPC with an unfired player seed targeting it -> Delta > 0.
    seed = make_seed("seed-1", target_id="npc-1", planted_year=20, maturation=10)
    world2, _ = make_world(
        npcs=[make_npc("npc-1", age=70)], seeds=[seed], current_year=20
    )
    idx2 = build_indexes(world2)
    assert npc_signals(world2.npcs[0], world2, idx2).delta > 0.0


def test_T16_npc_ripening_independent_of_age():
    # Young NPC (mortality 0) but a near-mature seed -> Delta from ripening.
    seed = make_seed("seed-1", target_id="npc-1", planted_year=11, maturation=10)
    world, _ = make_world(
        npcs=[make_npc("npc-1", age=20)], seeds=[seed], current_year=20
    )
    idx = build_indexes(world)
    assert npc_signals(world.npcs[0], world, idx).delta > 0.5


def test_T18_location_imminence_not_undev():
    world, _ = make_world(dominant=ThemeAxis.INNOVATION)
    idx = build_indexes(world)
    field = location_signals(make_loc("f", LocationType.FIELD), world, idx)
    dungeon = location_signals(make_loc("d", LocationType.DUNGEON), world, idx)
    convergent = location_signals(
        make_loc("c", LocationType.FIELD, theme_affinity=ThemeAxis.INNOVATION),
        world,
        idx,
    )
    assert dungeon.delta > field.delta
    assert convergent.delta > field.delta


def test_T19_location_sigma_is_flat_baseline():
    world, _ = make_world()
    idx = build_indexes(world)
    a = location_signals(make_loc("a", LocationType.DUNGEON), world, idx)
    b = location_signals(make_loc("b", LocationType.FIELD), world, idx)
    assert a.sigma == 0.2 and b.sigma == 0.2  # undev removed from Sigma (B-1)


def test_T20_wildcard_tension_order():
    world, _ = make_world()
    idx = build_indexes(world)
    impact = {ThemeAxis.FAITH: 40}
    ig = opp_mod.wildcard_signals(
        make_wc("i", status=WildCardStatus.IGNITED, impact=impact), world, idx
    )
    st = opp_mod.wildcard_signals(
        make_wc("s", status=WildCardStatus.DORMANT, trajectory=["x"], impact=impact),
        world,
        idx,
    )
    dm = opp_mod.wildcard_signals(
        make_wc("d", status=WildCardStatus.DORMANT, impact=impact), world, idx
    )
    assert ig.delta > st.delta > dm.delta
    assert assemble_tension(ig, 0) > assemble_tension(st, 0) > assemble_tension(dm, 0)


def test_T21_faction_emergence_pressure():
    world, _ = make_world(dominant=ThemeAxis.GOVERNANCE)
    idx = build_indexes(world)
    aligned = faction_signals(make_faction("a", FactionType.LORD, power=60), world, idx)
    other = faction_signals(
        make_faction("b", FactionType.MERCHANT, power=60), world, idx
    )
    assert aligned.delta > other.delta


def test_T22_static_size_not_dominant():
    world, _ = make_world(dominant=ThemeAxis.GOVERNANCE)
    idx = build_indexes(world)
    big_faction = faction_signals(
        make_faction("f", FactionType.MERCHANT, power=100), world, idx
    )
    small_wildcard = opp_mod.wildcard_signals(
        make_wc(
            "w",
            WildCardArchetype.CONQUEROR,
            WildCardStatus.IGNITED,
            impact={ThemeAxis.WARFARE: 20},
            interaction=PlayerInteraction.SUPPORT,
        ),
        world,
        idx,
    )
    assert assemble_tension(small_wildcard, 0) > assemble_tension(big_faction, 0)


# --- Wave 2: determinism primitives -------------------------------------


def test_T2_jitter_from_immutable_inputs():
    npcs = [make_npc(f"npc-{i}") for i in range(4)]
    world, life = make_world(npcs=npcs)
    first = select_opportunities(world, life, OpportunitySession())
    # Appending later lives must not change our life's index -> identical jitter.
    world.lives.append(Life(id="life-9999", player_id=world.player.id, birth_year=5))
    second = select_opportunities(world, life, OpportunitySession())
    assert [(o.target_id, o.tension) for o in first] == [
        (o.target_id, o.tension) for o in second
    ]


def test_T3_stable_sort_total_order():
    items = [
        opp(OpportunityKind.FACTION, "fac-1", 0.5),
        opp(OpportunityKind.WILDCARD, "wc-1", 0.5),
        opp(OpportunityKind.NPC, "npc-1", 0.5),
    ]
    out1 = [o.target_id for o in select_top_k(list(items))]
    out2 = [o.target_id for o in select_top_k(list(reversed(items)))]
    assert out1 == out2 == ["wc-1", "npc-1", "fac-1"]  # KIND_ORDER tie-break


# --- Wave 3: selection / cardinality / mix / caps -----------------------


def test_T4_cardinality_full():
    world, life = make_world(
        npcs=[make_npc(f"npc-{i}") for i in range(5)],
        factions=[make_faction("fac-1")],
        locations=[make_loc("loc-1", LocationType.DUNGEON)],
        wildcards=[make_wc("wc-1", status=WildCardStatus.IGNITED)],
    )
    opps = select_opportunities(world, life, OpportunitySession())
    assert len(opps) == MAX_OPPORTUNITIES == 5


def test_T5_cardinality_degrade():
    world, life = make_world(npcs=[make_npc("npc-1")], factions=[make_faction("fac-1")])
    opps = select_opportunities(world, life, OpportunitySession())
    assert len(opps) == 2


def test_T6_grounding():
    world, life = make_world(
        npcs=[make_npc("npc-1"), make_npc("npc-2")],
        factions=[make_faction("fac-1")],
        locations=[make_loc("loc-1", LocationType.DUNGEON)],
        wildcards=[make_wc("wc-1", status=WildCardStatus.IGNITED)],
        heritage=[make_heritage("her-1")],
    )
    valid = (
        {n.id for n in world.npcs}
        | {f.id for f in world.factions}
        | {loc.id for loc in world.locations}
        | {w.id for w in world.wildcards.wildcards}
        | {h.id for h in world.heritage}
    )
    for o in select_opportunities(world, life, OpportunitySession()):
        assert o.target_id in valid


def test_T7_exclusion_dead_resolved():
    world, life = make_world(
        npcs=[make_npc("alive-1"), make_npc("dead-1", age=75, alive=False)],
        factions=[make_faction("fac-1")],
        wildcards=[
            make_wc("wc-live", WildCardArchetype.CONQUEROR, WildCardStatus.IGNITED),
            make_wc(
                "wc-resolved", WildCardArchetype.CONQUEROR, WildCardStatus.RESOLVED
            ),
        ],
    )
    seen = {tid for turn in run(world, life, 3) for tid in turn}
    assert "dead-1" not in seen
    assert "wc-resolved" not in seen


def test_T9_mix_floor():
    scored = [
        opp(OpportunityKind.WILDCARD, f"wc-{i}", 0.9 - i * 0.01) for i in range(5)
    ]
    scored += [
        opp(OpportunityKind.NPC, "npc-1", 0.2),
        opp(OpportunityKind.FACTION, "fac-1", 0.15),
        opp(OpportunityKind.LOCATION, "loc-1", 0.1),
    ]
    result = select_top_k(scored)
    assert len({o.kind for o in result}) >= 3


def test_T10_cap_wildcard():
    scored = [
        opp(OpportunityKind.WILDCARD, f"wc-{i}", 0.9 - i * 0.01) for i in range(5)
    ]
    scored += [
        opp(OpportunityKind.NPC, "npc-1", 0.4),
        opp(OpportunityKind.FACTION, "fac-1", 0.3),
        opp(OpportunityKind.LOCATION, "loc-1", 0.2),
    ]
    result = select_top_k(scored)
    assert sum(o.kind is OpportunityKind.WILDCARD for o in result) <= 2


def test_T11_cap_legacy():
    # Enough non-legacy candidates exist that the cap binds (no Pass-2 relaxation).
    scored = [
        opp(OpportunityKind.LEGACY, f"her-{i}", 0.9 - i * 0.01, score=50)
        for i in range(3)
    ]
    scored += [
        opp(OpportunityKind.NPC, "npc-1", 0.6),
        opp(OpportunityKind.NPC, "npc-2", 0.55),
        opp(OpportunityKind.FACTION, "fac-1", 0.5),
        opp(OpportunityKind.FACTION, "fac-2", 0.45),
        opp(OpportunityKind.WILDCARD, "wc-1", 0.4),
    ]
    result = select_top_k(scored)
    assert sum(o.kind is OpportunityKind.LEGACY for o in result) <= 1


def test_T12_cap_default_ceil():
    scored = [
        opp(OpportunityKind.FACTION, f"fac-{i}", 0.9 - i * 0.01) for i in range(5)
    ]
    scored += [
        opp(OpportunityKind.WILDCARD, "wc-1", 0.3),
        opp(OpportunityKind.NPC, "npc-1", 0.2),
        opp(OpportunityKind.LOCATION, "loc-1", 0.1),
    ]
    result = select_top_k(scored)
    assert sum(o.kind is OpportunityKind.FACTION for o in result) <= 3  # ceil(5/2)


def test_T13_cap_relax_when_short():
    scored = [
        opp(OpportunityKind.WILDCARD, f"wc-{i}", 0.9 - i * 0.01) for i in range(4)
    ]
    result = select_top_k(scored)
    assert len(result) == 4  # only one kind exists; caps relaxed to fill K
    assert all(o.kind is OpportunityKind.WILDCARD for o in result)


def test_T14_mix_swap_deterministic():
    scored = [opp(OpportunityKind.NPC, f"npc-{i}", 0.9 - i * 0.05) for i in range(3)]
    scored += [
        opp(OpportunityKind.FACTION, f"fac-{i}", 0.7 - i * 0.05) for i in range(3)
    ]
    scored += [opp(OpportunityKind.LOCATION, "loc-1", 0.3)]
    r1 = [o.target_id for o in select_top_k(list(scored))]
    r2 = [o.target_id for o in select_top_k(list(reversed(scored)))]
    assert r1 == r2
    kinds = {o.kind for o in select_top_k(list(scored))}
    assert OpportunityKind.LOCATION in kinds and len(kinds) == 3


# --- Wave 4: escalation -------------------------------------------------


def test_T23_escalation_monotonic_and_capped():
    vals = [escalation_factor(t) for t in range(0, 40)]
    assert vals[0] == 1.0
    assert escalation_factor(opp_mod.EXPECTED_TURNS) == pytest.approx(1.3)
    assert all(b >= a for a, b in zip(vals, vals[1:]))
    assert max(vals) <= 1.0 + opp_mod.ESCALATION_GAIN + 1e-9


def test_T24_escalation_imminence_only():
    imminent = Signals(delta=1.0)
    assert assemble_tension(imminent, 10) > assemble_tension(imminent, 0)


def test_T25_escalation_excludes_peril():
    peril = Signals(delta=0.0, rho=1.0)
    assert assemble_tension(peril, 20) == pytest.approx(assemble_tension(peril, 0))


# --- Wave 5: read-only / bounds / performance ---------------------------


def test_T8_readonly():
    world, life = make_world(
        npcs=[make_npc("npc-1")],
        factions=[make_faction("fac-1")],
        wildcards=[make_wc("wc-1", status=WildCardStatus.IGNITED)],
        heritage=[make_heritage("her-1")],
    )
    before = world.model_dump()
    select_opportunities(world, life, OpportunitySession())
    assert world.model_dump() == before


def test_T31_empty_world_guard():
    world, life = make_world()
    assert select_opportunities(world, life, OpportunitySession()) == []
    world2, life2 = make_world(npcs=[make_npc("npc-1")])
    out = select_opportunities(world2, life2, OpportunitySession())
    assert [o.target_id for o in out] == ["npc-1"]


def test_T30_indexes_built_once(monkeypatch):
    world, life = make_world(
        npcs=[make_npc(f"npc-{i}") for i in range(3)],
        factions=[make_faction("fac-1")],
    )
    calls = {"n": 0}
    real = opp_mod.build_indexes

    def counting(w):
        calls["n"] += 1
        return real(w)

    monkeypatch.setattr(opp_mod, "build_indexes", counting)
    select_opportunities(world, life, OpportunitySession())
    assert calls["n"] == 1


# --- Wave 6: session / freshness ----------------------------------------


def test_T26_legacy_freshness_gate():
    her = make_heritage("her-1", score=50)
    world, life = make_world(npcs=[make_npc("npc-1")], heritage=[her])
    session = OpportunitySession()

    turn0 = select_opportunities(world, life, session)
    assert "her-1" in {o.target_id for o in turn0}
    session.commit_turn(turn0, None)

    # Unchanged score -> gated out next turn.
    turn1 = select_opportunities(world, life, session)
    assert "her-1" not in {o.target_id for o in turn1}

    # Score increase -> eligible again.
    her.heritage_score = 60
    turn1b = select_opportunities(world, life, session)
    assert "her-1" in {o.target_id for o in turn1b}


def test_T27_legacy_stale_after_F_turns():
    her = make_heritage("her-1", score=50)
    world, life = make_world(npcs=[make_npc("npc-1")], heritage=[her])
    offered = run(world, life, 4, choose=lambda o: None)
    present = ["her-1" in turn for turn in offered]
    assert present[0] is True
    assert present[1] is False and present[2] is False  # within F=3
    assert present[3] is True  # stale -> eligible again


def test_T28_recency_penalty_decay():
    # Two identical NPCs: the just-selected one is demoted next turn, recovers after.
    npcs = [
        make_npc("npc-a", tier=NPCTier.S, ambitious=90, brave=90, cautious=10),
        make_npc("npc-b", tier=NPCTier.S, ambitious=90, brave=90, cautious=10),
    ]
    world, life = make_world(npcs=npcs)
    selected = []

    session = OpportunitySession()
    for _ in range(3):
        opps = select_opportunities(world, life, session)
        choice = opps[0].target_id
        selected.append(choice)
        session.commit_turn(opps, choice)

    assert selected[1] != selected[0]  # recency demotes the prior pick
    assert selected[2] == selected[0]  # and it resurfaces (anti-starvation, T29)


def test_T29_anti_starvation_both_surface():
    npcs = [
        make_npc("npc-a", tier=NPCTier.S, ambitious=90, brave=90, cautious=10),
        make_npc("npc-b", tier=NPCTier.S, ambitious=90, brave=90, cautious=10),
    ]
    world, life = make_world(npcs=npcs)
    session = OpportunitySession()
    picked = set()
    for _ in range(2):
        opps = select_opportunities(world, life, session)
        picked.add(opps[0].target_id)
        session.commit_turn(opps, opps[0].target_id)
    assert picked == {"npc-a", "npc-b"}


# --- Wave 7: deterministic end-to-end -----------------------------------


def test_T1_deterministic_e2e():
    world, life = make_world(
        npcs=[make_npc(f"npc-{i}", age=30 + i * 5) for i in range(4)],
        factions=[make_faction("fac-1", FactionType.LORD, power=60)],
        locations=[make_loc("loc-1", LocationType.DUNGEON)],
        wildcards=[
            make_wc(
                "wc-1",
                WildCardArchetype.CONQUEROR,
                WildCardStatus.IGNITED,
                impact={ThemeAxis.WARFARE: 60},
            )
        ],
        heritage=[make_heritage("her-1", score=40)],
    )
    log_a = run(world, life, 6)
    log_b = run(world, life, 6)
    assert log_a == log_b
    for turn in log_a:
        assert 3 <= len(turn) <= 5  # I3 cardinality across the run
