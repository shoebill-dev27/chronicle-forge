"""P6 Opportunity selection by narrative tension (see docs/design_p6_salience.md).

This is a volatile, read-only *view* over world state: it never mutates the World
and adds no new truth to the causal model (Seed/Event/Heritage). Each turn it
scores candidate targets (NPC / Faction / Location / WildCard / Legacy) by a
narrative-tension score ``T`` built from four universal signals -- Change-proximity
(Delta), Stakes (Sigma), Open-loop (Omega), Reversal/Peril (Rho) -- and selects
3-5 of them deterministically.

Determinism: ``T`` is a pure function of world state; ties are broken by a
seed-derived jitter from immutable inputs (``world.seed`` + life index + turn
index) and a stable total-order sort. Per-turn diversity (recency, kind caps,
mix floor, legacy freshness) is tracked in a volatile :class:`OpportunitySession`
that lives outside ``World``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .enums import LocationType, NPCTier, WildCardArchetype, WildCardStatus
from .macro import derive_rng
from .models import NPC, Faction, Location, Life, WildCard, World
from .theme import FACTION_TYPE_TO_THEME, SEED_DOMAIN_TO_THEME


# --- tuning constants (kept local to this volatile layer; config.py untouched) ---

W_DELTA = 0.35
W_SIGMA = 0.25
W_OMEGA = 0.25
W_RHO = 0.15

EXPECTED_TURNS = 18
ESCALATION_GAIN = 0.3  # design constraint: <= 0.3, applied to Delta (imminence) only

FRESH_DELTA = 10  # heritage_score increase that reads as a "fully fresh" legacy
FACTION_OMEGA_YEARS = 5  # window (world-years) for faction open-loop involvement
FRESHNESS_STALE_TURNS = 3  # F: a legacy unseen this many turns is eligible again
RECENCY_WINDOW = 2  # turns of offer history kept for the recency penalty

MEMORY_MIN_INTENSITY = 0.20  # normalized intensity floor for a memory to count
SALIENCE_SALT = 77  # distinct from autoplay's _AUTOPLAY_SALT (99)
JITTER_SCALE = 0.05

MIN_OPPORTUNITIES = 3
MAX_OPPORTUNITIES = 5

TIER_W = {NPCTier.S: 1.0, NPCTier.A: 0.6, NPCTier.B: 0.2}
WILDCARD_PERIL_ARCHETYPES = {
    WildCardArchetype.CONQUEROR,
    WildCardArchetype.ZEALOT,
    WildCardArchetype.REVOLUTIONARY,
}


class OpportunityKind(str, Enum):
    """Volatile discriminator for an opportunity's target type (not a model enum)."""

    NPC = "npc"
    FACTION = "faction"
    LOCATION = "location"
    WILDCARD = "wildcard"
    LEGACY = "legacy"


KIND_ORDER = {
    OpportunityKind.WILDCARD: 0,
    OpportunityKind.NPC: 1,
    OpportunityKind.FACTION: 2,
    OpportunityKind.LOCATION: 3,
    OpportunityKind.LEGACY: 4,
}

KIND_CAP = {OpportunityKind.WILDCARD: 2, OpportunityKind.LEGACY: 1}


# --- data types ---------------------------------------------------------


@dataclass
class Signals:
    """The four universal tension signals, each normalized to 0..1."""

    delta: float = 0.0
    sigma: float = 0.0
    omega: float = 0.0
    rho: float = 0.0


@dataclass
class Opportunity:
    """A single presented opportunity (volatile; derived, never persisted)."""

    kind: OpportunityKind
    target_id: str
    name: str
    tension: float
    signals: Signals
    score: int = 0  # heritage_score for LEGACY; 0 otherwise


@dataclass
class OpportunitySession:
    """Minimal volatile per-life state for diversity/freshness. Not in ``World``."""

    turn_index: int = 0
    offered_prev: list[str] = field(default_factory=list)  # offered at turn-1
    offered_prev2: list[str] = field(default_factory=list)  # offered at turn-2
    selected_prev: Optional[str] = None  # selected at turn-1
    legacy_seen: dict[str, tuple[int, int]] = field(default_factory=dict)

    def commit_turn(self, offered: list[Opportunity], selected_id: Optional[str]) -> None:
        """Roll the history forward after a turn's opportunities were shown."""
        for opp in offered:
            if opp.kind is OpportunityKind.LEGACY:
                self.legacy_seen[opp.target_id] = (self.turn_index, opp.score)
        self.offered_prev2 = self.offered_prev
        self.offered_prev = [o.target_id for o in offered]
        self.selected_prev = selected_id
        self.turn_index += 1


@dataclass
class Indexes:
    """Per-turn lookup tables, built once, so scoring stays O(1) per candidate."""

    seeds_by_target: dict[str, list]  # unfired player seeds, keyed by target_id
    memories_by_subject: dict[str, list]
    recent_seeds_by_axis: dict[object, int]
    discoveries_by_location: dict[str, list]
    discovered_location_ids: set[str]
    factions_by_id: dict[str, Faction]
    max_heritage_score: int


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


# --- indexing (built once per select_opportunities call) ----------------


def build_indexes(world: World) -> Indexes:
    seeds_by_target: dict[str, list] = {}
    recent_seeds_by_axis: dict[object, int] = {}
    year_floor = world.current_year - FACTION_OMEGA_YEARS
    for seed in world.seeds:
        if seed.planted_by_life_id is None:
            continue
        if not seed.fired and seed.target_id is not None:
            seeds_by_target.setdefault(seed.target_id, []).append(seed)
        if seed.planted_year >= year_floor:
            axis = SEED_DOMAIN_TO_THEME[seed.domain]
            recent_seeds_by_axis[axis] = recent_seeds_by_axis.get(axis, 0) + 1

    memories_by_subject: dict[str, list] = {}
    for mem in world.memories:
        memories_by_subject.setdefault(mem.subject_id, []).append(mem)

    discoveries_by_location: dict[str, list] = {}
    for disc in world.discoveries:
        discoveries_by_location.setdefault(disc.location_id, []).append(disc)

    max_heritage_score = max((h.heritage_score for h in world.heritage), default=1)
    return Indexes(
        seeds_by_target=seeds_by_target,
        memories_by_subject=memories_by_subject,
        recent_seeds_by_axis=recent_seeds_by_axis,
        discoveries_by_location=discoveries_by_location,
        discovered_location_ids={d.location_id for d in world.discoveries},
        factions_by_id={f.id: f for f in world.factions},
        max_heritage_score=max(1, max_heritage_score),
    )


# --- per-kind signal derivation -----------------------------------------


def npc_signals(npc: NPC, world: World, idx: Indexes) -> Signals:
    pending = idx.seeds_by_target.get(npc.id, [])
    ripening = 0.0
    for seed in pending:
        maturation = max(1, seed.maturation_time)
        elapsed = max(0, world.current_year - seed.planted_year)
        ripening = max(ripening, clamp01(elapsed / maturation))

    active_memories = sum(
        1
        for m in idx.memories_by_subject.get(npc.id, [])
        if m.actor_id == world.player.id and (m.intensity / 100.0) >= MEMORY_MIN_INTENSITY
    )
    omega = clamp01((len(pending) + active_memories) / 3.0)

    mortality = clamp01((npc.lifecycle.age - 50) / 30.0)
    delta = max(mortality * omega, ripening)

    faction = idx.factions_by_id.get(npc.lifecycle.faction_id or "")
    faction_power = faction.power if faction else 0
    sigma = (
        0.5 * TIER_W.get(npc.tier, 0.2)
        + 0.3 * (faction_power / 100.0)
        + 0.2 * (npc.personality.ambitious / 100.0)
    )

    p = npc.personality
    rho = clamp01((p.brave + p.ambitious + (100 - p.cautious)) / 300.0)
    return Signals(delta=delta, sigma=clamp01(sigma), omega=omega, rho=rho)


def faction_signals(faction: Faction, world: World, idx: Indexes) -> Signals:
    axis = FACTION_TYPE_TO_THEME[faction.type]
    power_n = faction.power / 100.0
    aligned = world.theme.dominant == axis
    delta = power_n if aligned else 0.3 * power_n
    sigma = power_n
    omega = clamp01(idx.recent_seeds_by_axis.get(axis, 0) / 2.0)
    worst = min(faction.relations.values(), default=0)
    rho = clamp01(max(0, -worst) / 100.0)
    return Signals(delta=clamp01(delta), sigma=clamp01(sigma), omega=omega, rho=rho)


def location_signals(loc: Location, world: World, idx: Indexes) -> Signals:
    discovered = loc.id in idx.discovered_location_ids
    undiscovered_dungeon = loc.type == LocationType.DUNGEON and not discovered
    frontier = 1.0 if undiscovered_dungeon else 0.0
    convergence = 0.7 if loc.theme_affinity == world.theme.dominant else 0.2
    delta = max(frontier, convergence)

    discoveries = idx.discoveries_by_location.get(loc.id, [])
    seeds_here = sum(1 for d in discoveries if d.seed_id)
    omega = clamp01((seeds_here + len(discoveries)) / 2.0)

    # MVP reduction (B-1): Sigma is a flat low baseline; no per-location gradient
    # exists yet (Location.state is empty; CausalNode.location_id is never set).
    rho = 1.0 if undiscovered_dungeon else 0.2
    return Signals(delta=delta, sigma=0.2, omega=omega, rho=rho)


def wildcard_signals(wc: WildCard, world: World, idx: Indexes) -> Signals:
    if wc.status is WildCardStatus.IGNITED:
        delta = 1.0
    elif wc.status is WildCardStatus.DORMANT and wc.trajectory:  # "stirring"
        delta = 0.6
    else:  # plain DORMANT
        delta = 0.25
    sigma = clamp01(sum(abs(v) for v in wc.impact_vector.values()) / 200.0)
    omega = 1.0 if (wc.player_interaction is not None) else 0.3
    rho = 0.8 if wc.archetype in WILDCARD_PERIL_ARCHETYPES else 0.3
    return Signals(delta=delta, sigma=sigma, omega=omega, rho=rho)


def legacy_signals(heritage, idx: Indexes, last_score: int) -> Signals:
    delta = clamp01((heritage.heritage_score - last_score) / FRESH_DELTA)
    sigma = clamp01(heritage.heritage_score / idx.max_heritage_score)
    omega = clamp01(heritage.reach / 5.0)
    return Signals(delta=delta, sigma=sigma, omega=omega, rho=0.3)


# --- tension assembly ---------------------------------------------------


def escalation_factor(turn_index: int) -> float:
    """E_Delta(turn): monotonic non-decreasing, applied to imminence (Delta) only."""
    return 1.0 + ESCALATION_GAIN * clamp01(turn_index / EXPECTED_TURNS)


def assemble_tension(sig: Signals, turn_index: int) -> float:
    """Weighted tension before recency penalty and jitter (pure function)."""
    return (
        W_DELTA * escalation_factor(turn_index) * sig.delta
        + W_SIGMA * sig.sigma
        + W_OMEGA * sig.omega
        + W_RHO * sig.rho
    )


def _recency_penalty(target_id: str, session: OpportunitySession) -> float:
    if target_id == session.selected_prev:
        return 0.5
    if target_id in session.offered_prev:
        return 0.7
    if target_id in session.offered_prev2:
        return 0.85
    return 1.0


# --- candidate gathering ------------------------------------------------


def _gather(
    world: World, idx: Indexes, session: OpportunitySession, jitter_rng
) -> list[Opportunity]:
    """Build scored candidates in a fixed, deterministic order (excludes the
    dead/resolved and applies the legacy freshness gate)."""
    turn = session.turn_index
    out: list[Opportunity] = []

    def add(kind: OpportunityKind, tid: str, name: str, sig: Signals, score: int = 0):
        tension = assemble_tension(sig, turn) * _recency_penalty(tid, session)
        tension += jitter_rng.random() * JITTER_SCALE
        out.append(Opportunity(kind, tid, name, tension, sig, score))

    for npc in world.npcs:
        if npc.alive:
            add(OpportunityKind.NPC, npc.id, npc.name, npc_signals(npc, world, idx))
    for fac in world.factions:
        add(OpportunityKind.FACTION, fac.id, fac.name, faction_signals(fac, world, idx))
    for loc in world.locations:
        add(OpportunityKind.LOCATION, loc.id, loc.name, location_signals(loc, world, idx))
    for wc in world.wildcards.wildcards:
        if wc.status in (WildCardStatus.RESOLVED, WildCardStatus.DEAD):
            continue
        add(OpportunityKind.WILDCARD, wc.id, wc.name, wildcard_signals(wc, world, idx))
    for her in world.heritage:
        seen = session.legacy_seen.get(her.id)
        last_score = seen[1] if seen else 0
        if seen is not None:
            fresh = her.heritage_score > last_score
            stale = (turn - seen[0]) >= FRESHNESS_STALE_TURNS
            if not (fresh or stale):
                continue  # freshness gate
        add(
            OpportunityKind.LEGACY,
            her.id,
            f"legacy:{her.seed_id}",
            legacy_signals(her, idx, last_score),
            score=her.heritage_score,
        )
    return out


# --- deterministic top-K selection --------------------------------------


def _sort_key(o: Opportunity):
    return (-o.tension, KIND_ORDER[o.kind], o.target_id)


def select_top_k(scored: list[Opportunity]) -> list[Opportunity]:
    """Per-kind cap + Opportunity Mix floor, fully deterministic."""
    order = sorted(scored, key=_sort_key)
    if not order:
        return []
    K = min(MAX_OPPORTUNITIES, len(order))
    default_cap = math.ceil(K / 2)

    def cap(kind: OpportunityKind) -> int:
        return KIND_CAP.get(kind, default_cap)

    kinds_present = {o.kind for o in order}
    min_kinds = min(MIN_OPPORTUNITIES, len(kinds_present))

    selected: list[Opportunity] = []
    kc: dict[OpportunityKind, int] = {}

    # Pass 1: tension-first under per-kind caps.
    for o in order:
        if len(selected) == K:
            break
        if kc.get(o.kind, 0) >= cap(o.kind):
            continue
        selected.append(o)
        kc[o.kind] = kc.get(o.kind, 0) + 1

    # Pass 2: relax caps only if caps starved us below K.
    if len(selected) < K:
        chosen = set(id(o) for o in selected)
        for o in order:
            if len(selected) == K:
                break
            if id(o) in chosen:
                continue
            selected.append(o)
            kc[o.kind] = kc.get(o.kind, 0) + 1

    # Pass 3: satisfy the Mix floor via deterministic swaps.
    while len({o.kind for o in selected}) < min_kinds:
        present = {o.kind for o in selected}
        missing = next((o for o in order if o.kind not in present), None)
        if missing is None:
            break
        overrep = [o for o in selected if kc.get(o.kind, 0) > 1]
        if not overrep:
            break
        victim = min(
            overrep,
            key=lambda o: (o.tension, -KIND_ORDER[o.kind], _desc(o.target_id)),
        )
        selected.remove(victim)
        kc[victim.kind] -= 1
        selected.append(missing)
        kc[missing.kind] = kc.get(missing.kind, 0) + 1

    return sorted(selected, key=_sort_key)


def _desc(s: str):
    """Key that orders larger strings first under ``min`` (deterministic)."""
    return tuple(-ord(ch) for ch in s)


# --- public entry point -------------------------------------------------


def select_opportunities(
    world: World, life: Life, session: OpportunitySession
) -> list[Opportunity]:
    """Return 3-5 narrative-tension-ranked opportunities for the current turn.

    Read-only on ``world``; mutates only the volatile ``session`` is the caller's
    job (via :meth:`OpportunitySession.commit_turn`). Deterministic for a given
    seed, life, and turn index.
    """
    idx = build_indexes(world)
    life_index = next(
        (i for i, lf in enumerate(world.lives) if lf.id == life.id), 0
    )
    mixer = life_index * 100000 + session.turn_index
    jitter_rng = derive_rng(world, mixer, salt=SALIENCE_SALT)
    scored = _gather(world, idx, session, jitter_rng)
    return select_top_k(scored)
