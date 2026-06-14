"""Fixed-seed Opportunity observation harness (P6 experience check).

This is an *experiment tool*, not a test and not part of the engine. It drives a
world with the existing deterministic policy (talent-based ``perform_activity``,
exactly like autoplay) and, as a **read-only overlay**, observes what the P6
Opportunity layer *would* present each turn. The observed selection is logged and
fed back only into the volatile recency history -- it never drives the world.

It does not modify ``opportunity.py`` or wire autoplay; it reproduces the public
``select_opportunities`` internals to expose the full candidate list alongside the
selected top-K.

Run:  PYTHONPATH=src python3 scripts/opportunity_playlog.py [seed ...]
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from chronicle_forge.activity import perform_activity
from chronicle_forge.autoplay import _live_one
from chronicle_forge.discovery import explore_dungeon
from chronicle_forge.enums import (
    ActivityCategory,
    DiscoveryType,
    LocationType,
    Talent,
)
from chronicle_forge.life import begin_life, lifespan_reached
from chronicle_forge.macro import derive_rng, time_skip
from chronicle_forge.opportunity import (
    SALIENCE_SALT,
    W_DELTA,
    W_OMEGA,
    W_RHO,
    W_SIGMA,
    OpportunityKind,
    OpportunitySession,
    _gather,
    build_indexes,
    escalation_factor,
    select_top_k,
)
from chronicle_forge.profiles import ACTIVITY_PROFILES
from chronicle_forge.worldgen import generate_world

TURNS = 18  # fixed observation length (matches EXPECTED_TURNS)
POLICY_SALT = 99  # same salt autoplay uses for its independent policy stream
_TARGETED = {
    ActivityCategory.EDUCATION,
    ActivityCategory.POLITICS,
    ActivityCategory.RELIGION,
}
_TALENT_ACTIVITY = {p.talent_affinity: c for c, p in ACTIVITY_PROFILES.items()}


# --- observation overlay (reproduces select_opportunities internals) ----


def _life_index(world, life) -> int:
    return next((i for i, lf in enumerate(world.lives) if lf.id == life.id), 0)


def observe(world, life, session):
    """Return (all scored candidates, selected top-K) for this turn, read-only."""
    idx = build_indexes(world)
    mixer = _life_index(world, life) * 100000 + session.turn_index
    rng = derive_rng(world, mixer, salt=SALIENCE_SALT)
    scored = _gather(world, idx, session, rng)
    return scored, select_top_k(scored)


def contributions(o, turn_index):
    e = escalation_factor(turn_index)
    return {
        "Δ": W_DELTA * e * o.signals.delta,
        "Σ": W_SIGMA * o.signals.sigma,
        "Ω": W_OMEGA * o.signals.omega,
        "Ρ": W_RHO * o.signals.rho,
    }


def dominant(o, turn_index) -> str:
    c = contributions(o, turn_index)
    return max(c, key=c.get)


# --- existing world-progression policy (independent of opportunities) ---


def _pick_activity(rng, talent):
    if rng.random() < 0.6 and talent in _TALENT_ACTIVITY:
        return _TALENT_ACTIVITY[talent]
    return rng.choice(list(ActivityCategory))


def advance_world(world, life, rng):
    """One action-turn of the existing deterministic policy (mirrors autoplay)."""
    dungeon = next((l for l in world.locations if l.type == LocationType.DUNGEON), None)
    roll = rng.random()
    if dungeon is not None and roll < 0.15:
        explore_dungeon(world, life, dungeon.id, rng.choice(list(DiscoveryType)))
    else:
        category = _pick_activity(rng, life.talent)
        target = None
        if category in _TARGETED:
            living = [n for n in world.npcs if n.alive] or world.npcs
            target = rng.choice(living).id
        perform_activity(world, life, category, target_id=target)


# --- run one seed -------------------------------------------------------


@dataclass
class TurnRecord:
    turn: int
    year: int
    scored: list
    selected: list
    sigma_max: object  # the highest-Sigma candidate among all scored


def run_observation(world, life, policy_rng) -> list[TurnRecord]:
    """Observe the Opportunity stream for one life over the fixed window."""
    session = OpportunitySession()
    records: list[TurnRecord] = []
    for t in range(TURNS):
        if lifespan_reached(life):
            break
        scored, selected = observe(world, life, session)
        sigma_max = max(scored, key=lambda o: o.signals.sigma) if scored else None
        records.append(TurnRecord(t, world.current_year, scored, selected, sigma_max))
        top_id = selected[0].target_id if selected else None
        session.commit_turn(selected, top_id)
        advance_world(world, life, policy_rng)
    return records


def run_seed(seed: int):
    world = generate_world(seed)
    policy_rng = derive_rng(world, 0, salt=POLICY_SALT)
    talent = policy_rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    return run_observation(world, life, policy_rng), talent


def warm_until_heritage(seed: int, max_lives: int = 30):
    """Run full lives + time-skips (the existing engine) until Heritage exists,
    so the observed life is born into a world that has legacies to surface."""
    world = generate_world(seed)
    lives = 0
    while (
        not world.heritage and world.current_year < world.max_year and lives < max_lives
    ):
        rng = derive_rng(world, len(world.lives), salt=POLICY_SALT)
        life = _live_one(world, rng)
        time_skip(world, life)
        lives += 1
    return world, lives


def run_seed_heritage(seed: int):
    world, warm_lives = warm_until_heritage(seed)
    policy_rng = derive_rng(world, 777, salt=POLICY_SALT)
    talent = policy_rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    records = run_observation(world, life, policy_rng)
    return records, talent, warm_lives, list(world.heritage)


# --- rendering ----------------------------------------------------------


def _row(o, turn_index, mark=" "):
    d = o.signals
    return (
        f"  {mark} [{o.kind.value:<8}] {o.name:<10} "
        f"T={o.tension:5.2f}  Δ{d.delta:.2f} Σ{d.sigma:.2f} "
        f"Ω{d.omega:.2f} Ρ{d.rho:.2f}  ({dominant(o, turn_index)})"
    )


def render_turn(rec: TurnRecord) -> str:
    lines = [f"Turn {rec.turn}  (year {rec.year})"]
    top = rec.selected[0] if rec.selected else None
    if top is not None:
        lines.append("★ Selected: " + _row(top, rec.turn).strip())
    lines.append("Candidates:")
    for i, o in enumerate(rec.selected, 1):
        mark = "★" if o is top else str(i)
        lines.append(f"{i}".rjust(3) + _row(o, rec.turn, mark="")[3:])
    sm = rec.sigma_max
    if sm is not None:
        in_sel = sm in rec.selected
        verdict = "SELECTED" if (top is sm) else ("offered" if in_sel else "DROPPED")
        lines.append(
            f"  Σ-max (all {len(rec.scored)}): {sm.name} "
            f"Σ={sm.signals.sigma:.2f} T={sm.tension:.2f} -> {verdict}"
        )
    return "\n".join(lines)


# --- metrics M1-M8 ------------------------------------------------------


def metrics(records: list[TurnRecord]) -> dict:
    sel_items = [(r.turn, o) for r in records for o in r.selected]
    n_items = len(sel_items)

    m1 = sum(dominant(o, t) in ("Δ", "Ω", "Ρ") for t, o in sel_items)
    m2 = sum(any(o.signals.delta >= 0.6 for o in r.scored) for r in records)
    distinct = [len({o.kind for o in r.selected}) for r in records]
    cap_viol = sum(
        sum(o.kind is k for o in r.selected) > cap
        for r in records
        for k, cap in ((OpportunityKind.WILDCARD, 2), (OpportunityKind.LEGACY, 1))
    )

    half = len(records) // 2
    first, second = records[:half], records[half:]

    def mean_d(rs):
        items = [o for r in rs for o in r.selected]
        return sum(o.signals.delta for o in items) / max(1, len(items))

    def mean_t(rs):
        items = [o for r in rs for o in r.selected]
        return sum(o.tension for o in items) / max(1, len(items))

    tops = [r.selected[0].target_id for r in records if r.selected]
    consec = sum(a == b for a, b in zip(tops, tops[1:]))

    legacy_off = sum(o.kind is OpportunityKind.LEGACY for _, o in sel_items)
    sigma_dropped = sum(
        1 for r in records if r.sigma_max is not None and r.sigma_max not in r.selected
    )

    return {
        "M1_tension_not_size": (m1, n_items),
        "M2_imminence_turns": (m2, len(records)),
        "M3_avg_distinct_kinds": sum(distinct) / max(1, len(distinct)),
        "M3_cap_violations": cap_viol,
        "M4_meanD_first": mean_d(first),
        "M4_meanD_second": mean_d(second),
        "M4_meanT_first": mean_t(first),
        "M4_meanT_second": mean_t(second),
        "M5_consecutive_same_top": (consec, max(0, len(tops) - 1)),
        "M6_legacy_offered": legacy_off,
        "M7_sigma_max_dropped_turns": (sigma_dropped, len(records)),
    }


def find_sigma_upset(records: list[TurnRecord]):
    """Find a turn where the Sigma-max candidate was dropped while a higher-tension
    pick led on Delta/Omega/Rho (the core 'not chosen for size' evidence)."""
    for r in records:
        sm = r.sigma_max
        if sm is None or not r.selected:
            continue
        top = r.selected[0]
        if sm not in r.selected and top is not sm and dominant(top, r.turn) != "Σ":
            return r, sm, top
    return None


# --- main ---------------------------------------------------------------


def report_seed(seed: int) -> None:
    records, talent = run_seed(seed)
    records2, _ = run_seed(seed)  # M8 determinism
    same = [
        (
            r.turn,
            [o.target_id for o in r.selected],
            round(r.selected[0].tension, 9) if r.selected else None,
        )
        for r in records
    ] == [
        (
            r.turn,
            [o.target_id for o in r.selected],
            round(r.selected[0].tension, 9) if r.selected else None,
        )
        for r in records2
    ]

    print("=" * 72)
    print(f"SEED {seed}   (life talent: {talent.value}, {len(records)} turns)")
    print("=" * 72)
    for r in records:
        print(render_turn(r))
        print()

    m = metrics(records)
    print("-" * 72)
    print(f"METRICS (seed {seed})")
    a, b = m["M1_tension_not_size"]
    print(
        f"  M1 tension>size : {a}/{b} selected led by Δ/Ω/Ρ " f"({100*a/max(1,b):.0f}%)"
    )
    a, b = m["M2_imminence_turns"]
    print(f"  M2 imminence    : {a}/{b} turns offered a high-Δ (>=0.60) candidate")
    print(
        f"  M3 mix          : {m['M3_avg_distinct_kinds']:.2f} distinct kinds/turn, "
        f"cap violations={m['M3_cap_violations']}"
    )
    print(
        f"  M4 escalation   : meanΔ {m['M4_meanD_first']:.3f} -> {m['M4_meanD_second']:.3f} | "
        f"meanT {m['M4_meanT_first']:.3f} -> {m['M4_meanT_second']:.3f}"
    )
    a, b = m["M5_consecutive_same_top"]
    print(f"  M5 repetition   : {a}/{b} consecutive turns kept the same top pick")
    print(f"  M6 legacy       : {m['M6_legacy_offered']} legacy candidates offered")
    a, b = m["M7_sigma_max_dropped_turns"]
    print(f"  M7 size-suppress: Σ-max dropped from top-K in {a}/{b} turns")
    print(f"  M8 determinism  : {'IDENTICAL across 2 runs' if same else 'MISMATCH!'}")

    upset = find_sigma_upset(records)
    print("-" * 72)
    if upset:
        r, sm, top = upset
        print(
            f"  A. Σ-max upset @ Turn {r.turn}: "
            f"BIG '{sm.name}' (Σ={sm.signals.sigma:.2f}, T={sm.tension:.2f}) DROPPED; "
            f"led by '{top.name}' (T={top.tension:.2f}, by {dominant(top, r.turn)}: "
            f"Δ{top.signals.delta:.2f} Ω{top.signals.omega:.2f} "
            f"Ρ{top.signals.rho:.2f})"
        )
    else:
        print("  A. no Σ-max upset found in this run")
    print()


def _legacy_in(opps):
    return [o for o in opps if o.kind is OpportunityKind.LEGACY]


def report_seed_heritage(seed: int) -> None:
    records, talent, warm_lives, heritage = run_seed_heritage(seed)

    print("=" * 72)
    print(
        f"SEED {seed}  [HERITAGE MODE]  warm-up lives: {warm_lives}, "
        f"life talent: {talent.value}, {len(records)} obs turns"
    )
    print(f"Heritage present: {len(heritage)}")
    for h in sorted(heritage, key=lambda x: -x.heritage_score):
        print(
            f"  - {h.id}  type={h.type.value:<11} score={h.heritage_score:>4} "
            f"reach={h.reach} longevity={h.longevity}"
        )
    print("=" * 72)

    for r in records:
        leg_scored = _legacy_in(r.scored)
        leg_sel = _legacy_in(r.selected)
        # Only print turns where Legacy is relevant, plus the selected line.
        top = r.selected[0] if r.selected else None
        tag = ""
        if leg_sel:
            tag = "  <-- LEGACY OFFERED: " + ", ".join(
                f"{o.name}(Δ{o.signals.delta:.2f} T{o.tension:.2f})" for o in leg_sel
            )
        elif leg_scored:
            tag = (
                "  (legacy gated/low: "
                + ", ".join(
                    f"{o.name} Δ{o.signals.delta:.2f} T{o.tension:.2f}"
                    for o in leg_scored
                )
                + ")"
            )
        sel_txt = f"{top.kind.value}:{top.name}" if top else "-"
        print(f"Turn {r.turn:>2} (y{r.year}) ★ {sel_txt:<22}{tag}")

    # Legacy-focused facts.
    offered_turns = [r.turn for r in records if _legacy_in(r.selected)]
    max_leg_in_topk = max((len(_legacy_in(r.selected)) for r in records), default=0)
    leg_tops = sum(
        1
        for r in records
        if r.selected and r.selected[0].kind is OpportunityKind.LEGACY
    )
    print("-" * 72)
    print(
        f"  Legacy offered on turns: {offered_turns} "
        f"({len(offered_turns)}/{len(records)})"
    )
    print(f"  Max legacies in any top-K: {max_leg_in_topk} (cap=1)")
    print(f"  Turns where legacy was the TOP pick: {leg_tops}")
    print()


# --- M9: Engagement-Loop observation (--execute, opportunities DRIVE) ----
#
# Unlike the read-only overlay above, this mode lets the Execution Layer convert
# the selected opportunity into an action that actually mutates the world, so the
# self-reinforcing loop (Opportunity -> Execute -> Seed/Memory -> Omega rises ->
# re-selected) can be OBSERVED. Observation only -- no tension/penalty/cap tuning.

from chronicle_forge.execution import (  # noqa: E402
    EXECUTION_SALT,
    execute_option,
    expand_options,
    make_auto_chooser,
)
from chronicle_forge.opportunity import select_opportunities  # noqa: E402

EXEC_TURNS = 24  # observation window (a bit longer than EXPECTED_TURNS=18)


@dataclass
class ExecRecord:
    turn: int
    year: int
    kind: str
    target: object
    omega: object
    label: str


def drive_life(world, rng) -> list[ExecRecord]:
    """Drive one life through the Execution Layer; record the chosen action and
    the selected opportunity's Omega each turn (read BEFORE executing)."""
    talent = rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    session = OpportunitySession()
    chooser = make_auto_chooser(rng)
    records: list[ExecRecord] = []
    for t in range(EXEC_TURNS):
        if lifespan_reached(life) or world.current_year >= world.max_year:
            break
        opps = select_opportunities(world, life, session)
        options = expand_options(opps, world, life, rng)
        choice = options[chooser(options)]
        opp = choice.opportunity
        records.append(
            ExecRecord(
                turn=t,
                year=world.current_year,
                kind=opp.kind.value if opp else "fallback",
                target=opp.target_id if opp else None,
                omega=opp.signals.omega if opp else None,
                label=choice.label,
            )
        )
        execute_option(world, life, choice)
        session.commit_turn(opps, opp.target_id if opp else None)
    return records


def m9_metrics(records: list[ExecRecord]) -> dict:
    from collections import Counter, defaultdict

    n = max(1, len(records))
    targets = [r.target for r in records]

    # 1. same-target consecutive-selection rate
    consec = sum(1 for a, b in zip(targets, targets[1:]) if a is not None and a == b)
    consec_rate = consec / max(1, len(records) - 1)

    # 2. same-target mean re-selection interval
    pos: dict = defaultdict(list)
    for i, t in enumerate(targets):
        if t is not None:
            pos[t].append(i)
    intervals = [b - a for ps in pos.values() for a, b in zip(ps, ps[1:])]
    mean_interval = (sum(intervals) / len(intervals)) if intervals else None

    # 3. per-kind monopoly rate
    kinds = Counter(r.kind for r in records)
    monopoly_kind, monopoly_n = kinds.most_common(1)[0] if kinds else ("-", 0)
    monopoly_rate = monopoly_n / n

    # 4. Omega time-series (selected target's Omega across turns)
    omega_series = [(r.turn, r.target, r.omega) for r in records]

    return {
        "turns": len(records),
        "consec_rate": consec_rate,
        "mean_interval": mean_interval,
        "monopoly_kind": monopoly_kind,
        "monopoly_rate": monopoly_rate,
        "kind_counts": dict(kinds),
        "omega_series": omega_series,
    }


def report_seed_execute(seed: int) -> None:
    world = generate_world(seed)
    rng = derive_rng(world, 0, salt=EXECUTION_SALT)
    records = drive_life(world, rng)

    print("=" * 72)
    print(f"SEED {seed}  [EXECUTE / M9]  {len(records)} driven turns")
    print("=" * 72)
    for r in records:
        om = f"Ω{r.omega:.2f}" if r.omega is not None else "Ω  - "
        tgt = r.target if r.target is not None else "(fallback)"
        print(f"Turn {r.turn:>2} (y{r.year}) [{r.kind:<8}] {tgt:<8} {om}  {r.label}")

    m = m9_metrics(records)
    print("-" * 72)
    print(f"M9 ENGAGEMENT-LOOP OBSERVATION (seed {seed})  -- observe-only")
    print(f"  same-target consecutive rate : {m['consec_rate']:.2f}")
    mi = m["mean_interval"]
    print(
        f"  same-target mean re-sel gap  : " f"{mi:.2f} turns"
        if mi is not None
        else "  same-target mean re-sel gap  : n/a (no target re-selected)"
    )
    print(
        f"  per-kind monopoly rate       : {m['monopoly_rate']:.2f} "
        f"({m['monopoly_kind']})  counts={m['kind_counts']}"
    )
    sel_om = [o for _, _, o in m["omega_series"] if o is not None]
    if sel_om:
        print(
            f"  selected-Ω over time         : "
            f"first={sel_om[0]:.2f} last={sel_om[-1]:.2f} "
            f"mean={sum(sel_om)/len(sel_om):.2f} max={max(sel_om):.2f}"
        )
    print()


# --- P6.6 WildCard Dominance Review (--review, observe-only) -------------
#
# Question for this phase: is WildCard *too strong*, or is it *interesting*?
# We compare two regimes per fixed seed over an identical 18-turn window:
#   - legacy mode: the talent policy drives the world; opportunities are a
#     READ-ONLY overlay (no engagement feedback loop). Baseline offer pressure.
#   - opportunity mode: the Execution Layer DRIVES the world (engagement closes
#     the Omega loop). What the loop does to the offer/selection distribution.
# Metrics M10-M13 + M12a. No tuning -- facts only; P6.7 design review comes after.

import math  # noqa: E402

REVIEW_SEEDS = [42, 123, 999, 1001, 2024, 31415, 65535, 77777, 88888, 99999]
ARC_TURNS = 18  # serial arc: early 0-5 / mid 6-11 / late 12-17

# M12 signal-based agency classification (confirmed P6.6 ruleset):
#   Legacy            -> History (heritage IS past causality)
#   non-Legacy        -> dominant weighted signal decides:
#                          Omega dominant -> Player (a loop the player opened)
#                          Delta/Rho/Sigma dominant -> World (the world acted)
#   tie-break order   : Legacy > Omega > Delta > Rho > Sigma
#                       (value order History > Agency > Event > Scale)
# Kind is NOT fixed: the same kind classifies differently by what drives it
# (e.g. a WildCard the player keeps engaging becomes Omega-dominant -> Player).
_SIGNAL_PRIORITY = {"Ω": 0, "Δ": 1, "Ρ": 2, "Σ": 3}


def _dominant_signal(opp, turn_index) -> str:
    """Dominant weighted contribution with the P6.6 tie-break order."""
    c = contributions(opp, turn_index)  # weighted Δ/Σ/Ω/Ρ (incl. escalation)
    return min(c.items(), key=lambda kv: (-kv[1], _SIGNAL_PRIORITY[kv[0]]))[0]


def classify_agency(opp, turn_index) -> str:
    """Return 'History' | 'Player' | 'World' for one opportunity."""
    if opp.kind is OpportunityKind.LEGACY:
        return "History"
    return "Player" if _dominant_signal(opp, turn_index) == "Ω" else "World"


@dataclass
class ReviewTurn:
    turn: int
    offered: list  # the presented top-K opportunities (with signals)
    top: object  # offered[0] or None
    selected: object  # chosen opportunity (opportunity mode) / top proxy (legacy)


def observe_legacy(seed: int) -> list[ReviewTurn]:
    """Read-only overlay: world driven by the talent policy; record what the
    Opportunity layer WOULD present. 'selected' proxied by the top pick."""
    world = generate_world(seed)
    policy_rng = derive_rng(world, 0, salt=POLICY_SALT)
    talent = policy_rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    session = OpportunitySession()
    out: list[ReviewTurn] = []
    for t in range(ARC_TURNS):
        if lifespan_reached(life) or world.current_year >= world.max_year:
            break
        _, selected = observe(world, life, session)  # selected == top-K
        top = selected[0] if selected else None
        out.append(ReviewTurn(t, selected, top, top))
        session.commit_turn(selected, top.target_id if top else None)
        advance_world(world, life, policy_rng)
    return out


def observe_opportunity(seed: int) -> list[ReviewTurn]:
    """Execution Layer drives the world; record offered top-K + the chosen
    opportunity (None when the free-action fallback is taken)."""
    world = generate_world(seed)
    rng = derive_rng(world, 0, salt=EXECUTION_SALT)
    talent = rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    session = OpportunitySession()
    chooser = make_auto_chooser(rng)
    out: list[ReviewTurn] = []
    for t in range(ARC_TURNS):
        if lifespan_reached(life) or world.current_year >= world.max_year:
            break
        opps = select_opportunities(world, life, session)
        options = expand_options(opps, world, life, rng)
        choice = options[chooser(options)]
        top = opps[0] if opps else None
        out.append(ReviewTurn(t, opps, top, choice.opportunity))
        execute_option(world, life, choice)
        session.commit_turn(
            opps, choice.opportunity.target_id if choice.opportunity else None
        )
    return out


def _is_wc(o) -> bool:
    return o is not None and o.kind is OpportunityKind.WILDCARD


def _entropy(counts) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts if c)


def _gini(counts) -> float:
    vals = sorted(counts)
    n = len(vals)
    s = sum(vals)
    if n == 0 or s == 0:
        return 0.0
    cum = sum((i + 1) * v for i, v in enumerate(vals))
    return (2 * cum) / (n * s) - (n + 1) / n


def m10_dominance(turns) -> dict:
    offered = [o for r in turns for o in r.offered]
    n_off = max(1, len(offered))
    n_turns = max(1, len(turns))
    tops = [r.top for r in turns if r.top]
    consec = sum(1 for a, b in zip(tops, tops[1:]) if _is_wc(a) and _is_wc(b))
    return {
        "wc_offered_rate": sum(_is_wc(o) for o in offered) / n_off,
        "wc_top_rate": sum(_is_wc(r.top) for r in turns) / n_turns,
        "wc_selected_rate": sum(_is_wc(r.selected) for r in turns) / n_turns,
        "wc_consec_top_rate": consec / max(1, len(tops) - 1),
    }


def m11_diversity(turns) -> dict:
    from collections import Counter

    ents, dists, ginis = [], [], []
    for r in turns:
        counts = list(Counter(o.kind for o in r.offered).values())
        ents.append(_entropy(counts))
        dists.append(len(counts))
        ginis.append(_gini(counts))
    n = max(1, len(turns))
    return {
        "entropy": sum(ents) / n,
        "distinct": sum(dists) / n,
        "gini": sum(ginis) / n,
    }


def m12_agency(turns) -> dict:
    from collections import Counter

    cls = Counter()
    wc_src = Counter()  # M12a: World-origin vs Player-origin WildCards
    total = 0
    for r in turns:
        for o in r.offered:
            c = classify_agency(o, r.turn)
            cls[c] += 1
            total += 1
            if o.kind is OpportunityKind.WILDCARD:
                wc_src["Player-origin" if c == "Player" else "World-origin"] += 1
    total = max(1, total)
    return {
        "World": cls["World"] / total,
        "Player": cls["Player"] / total,
        "History": cls["History"] / total,
        "wc_world_origin": wc_src["World-origin"],
        "wc_player_origin": wc_src["Player-origin"],
    }


def m13_arc(turns) -> list[dict]:
    from collections import Counter

    phases = [("early", range(0, 6)), ("mid", range(6, 12)), ("late", range(12, 18))]
    rows = []
    for name, rng in phases:
        sub = [r for r in turns if r.turn in rng]
        offered = [o for r in sub for o in r.offered]
        n = max(1, len(offered))
        kinds = Counter(o.kind.value for o in offered)
        agency = Counter(classify_agency(o, r.turn) for r in sub for o in r.offered)
        rows.append(
            {
                "phase": name,
                "turns": len(sub),
                "kind_share": {k: v / n for k, v in kinds.items()},
                "meanD": sum(o.signals.delta for o in offered) / n,
                "meanS": sum(o.signals.sigma for o in offered) / n,
                "meanO": sum(o.signals.omega for o in offered) / n,
                "meanR": sum(o.signals.rho for o in offered) / n,
                "agency": {k: agency[k] / n for k in ("World", "Player", "History")},
            }
        )
    return rows


def _fmt_share(d) -> str:
    return " ".join(f"{k}={v:.2f}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]))


def report_review_seed(seed: int) -> dict:
    leg = observe_legacy(seed)
    opp = observe_opportunity(seed)
    m10l, m10o = m10_dominance(leg), m10_dominance(opp)
    m11l, m11o = m11_diversity(leg), m11_diversity(opp)
    m12l, m12o = m12_agency(leg), m12_agency(opp)

    print("=" * 72)
    print(f"SEED {seed}  [P6.6 REVIEW]  legacy {len(leg)}t / opportunity {len(opp)}t")
    print("=" * 72)
    print("  M10 WildCard dominance        legacy  |  opportunity")
    for k, lab in [
        ("wc_offered_rate", "offered rate"),
        ("wc_top_rate", "top rate    "),
        ("wc_selected_rate", "selected rate"),
        ("wc_consec_top_rate", "consec top  "),
    ]:
        print(f"    {lab:<13} {m10l[k]:>6.2f}  |  {m10o[k]:>6.2f}")
    print("  M11 diversity (mean/turn)     legacy  |  opportunity")
    for k, lab in [
        ("entropy", "entropy(bit)"),
        ("distinct", "distinct kind"),
        ("gini", "gini"),
    ]:
        print(f"    {lab:<13} {m11l[k]:>6.2f}  |  {m11o[k]:>6.2f}")
    print("  M12 agency share (World/Player/History)")
    print(
        f"    legacy      W={m12l['World']:.2f} P={m12l['Player']:.2f} H={m12l['History']:.2f}"
    )
    print(
        f"    opportunity W={m12o['World']:.2f} P={m12o['Player']:.2f} H={m12o['History']:.2f}"
    )
    print(
        f"    M12a WC source (opportunity): "
        f"World-origin={m12o['wc_world_origin']} "
        f"Player-origin={m12o['wc_player_origin']}"
    )
    print("  M13 story arc (opportunity mode)  kind-share | agency | mean Δ/Σ/Ω/Ρ")
    for row in m13_arc(opp):
        ag = row["agency"]
        print(
            f"    {row['phase']:<5}({row['turns']}t) "
            f"[{_fmt_share(row['kind_share'])}] "
            f"W{ag['World']:.2f}/P{ag['Player']:.2f}/H{ag['History']:.2f} "
            f"Δ{row['meanD']:.2f} Σ{row['meanS']:.2f} Ω{row['meanO']:.2f} Ρ{row['meanR']:.2f}"
        )
    print()
    return {
        "seed": seed,
        "m10l": m10l,
        "m10o": m10o,
        "m11l": m11l,
        "m11o": m11o,
        "m12l": m12l,
        "m12o": m12o,
    }


def report_review(seeds) -> None:
    rows = [report_review_seed(s) for s in seeds]

    def avg(getter):
        return sum(getter(r) for r in rows) / max(1, len(rows))

    print("#" * 72)
    print(f"AGGREGATE over {len(rows)} seeds  (legacy -> opportunity)")
    print("#" * 72)
    print("  M10 WildCard dominance")
    for k, lab in [
        ("wc_offered_rate", "offered rate"),
        ("wc_top_rate", "top rate"),
        ("wc_selected_rate", "selected rate"),
        ("wc_consec_top_rate", "consec top"),
    ]:
        print(
            f"    {lab:<14} {avg(lambda r: r['m10l'][k]):.2f} -> {avg(lambda r: r['m10o'][k]):.2f}"
        )
    print("  M11 diversity (mean/turn)")
    for k, lab in [
        ("entropy", "entropy(bit)"),
        ("distinct", "distinct kind"),
        ("gini", "gini"),
    ]:
        print(
            f"    {lab:<14} {avg(lambda r: r['m11l'][k]):.2f} -> {avg(lambda r: r['m11o'][k]):.2f}"
        )
    print("  M12 agency share  World / Player / History")
    print(
        f"    legacy       "
        f"W={avg(lambda r: r['m12l']['World']):.2f} "
        f"P={avg(lambda r: r['m12l']['Player']):.2f} "
        f"H={avg(lambda r: r['m12l']['History']):.2f}"
    )
    print(
        f"    opportunity  "
        f"W={avg(lambda r: r['m12o']['World']):.2f} "
        f"P={avg(lambda r: r['m12o']['Player']):.2f} "
        f"H={avg(lambda r: r['m12o']['History']):.2f}"
    )
    wco = sum(r["m12o"]["wc_world_origin"] for r in rows)
    wcp = sum(r["m12o"]["wc_player_origin"] for r in rows)
    print(
        f"    M12a WC source (opportunity, all seeds): World-origin={wco} Player-origin={wcp}"
    )
    print()


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    heritage_mode = "--heritage" in argv
    execute_mode = "--execute" in argv
    review_mode = "--review" in argv
    seeds = [int(a) for a in argv if not a.startswith("--")]
    if review_mode:
        report_review(seeds or REVIEW_SEEDS)
        return 0
    seeds = seeds or [42, 123, 999]
    for s in seeds:
        if execute_mode:
            report_seed_execute(s)
        elif heritage_mode:
            report_seed_heritage(s)
        else:
            report_seed(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
