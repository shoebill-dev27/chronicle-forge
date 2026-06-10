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
from chronicle_forge.discovery import explore_dungeon
from chronicle_forge.enums import (
    ActivityCategory,
    DiscoveryType,
    LocationType,
    Talent,
)
from chronicle_forge.life import begin_life, lifespan_reached
from chronicle_forge.macro import derive_rng
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
_TARGETED = {ActivityCategory.EDUCATION, ActivityCategory.POLITICS, ActivityCategory.RELIGION}
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


def run_seed(seed: int) -> list[TurnRecord]:
    world = generate_world(seed)
    policy_rng = derive_rng(world, 0, salt=POLICY_SALT)
    talent = policy_rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
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
    return records, talent


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
        (r.turn, [o.target_id for o in r.selected], round(r.selected[0].tension, 9) if r.selected else None)
        for r in records
    ] == [
        (r.turn, [o.target_id for o in r.selected], round(r.selected[0].tension, 9) if r.selected else None)
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
    print(f"  M1 tension>size : {a}/{b} selected led by Δ/Ω/Ρ "
          f"({100*a/max(1,b):.0f}%)")
    a, b = m["M2_imminence_turns"]
    print(f"  M2 imminence    : {a}/{b} turns offered a high-Δ (>=0.60) candidate")
    print(f"  M3 mix          : {m['M3_avg_distinct_kinds']:.2f} distinct kinds/turn, "
          f"cap violations={m['M3_cap_violations']}")
    print(f"  M4 escalation   : meanΔ {m['M4_meanD_first']:.3f} -> {m['M4_meanD_second']:.3f} | "
          f"meanT {m['M4_meanT_first']:.3f} -> {m['M4_meanT_second']:.3f}")
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
        print(f"  A. Σ-max upset @ Turn {r.turn}: "
              f"BIG '{sm.name}' (Σ={sm.signals.sigma:.2f}, T={sm.tension:.2f}) DROPPED; "
              f"led by '{top.name}' (T={top.tension:.2f}, by {dominant(top, r.turn)}: "
              f"Δ{top.signals.delta:.2f} Ω{top.signals.omega:.2f} "
              f"Ρ{top.signals.rho:.2f})")
    else:
        print("  A. no Σ-max upset found in this run")
    print()


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    seeds = [int(a) for a in argv] if argv else [42, 123, 999]
    for s in seeds:
        report_seed(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
