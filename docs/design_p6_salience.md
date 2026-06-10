# P6 Salience — Opportunity Selection by Narrative Tension

Status: **Approved design (P6).** This document is design-only; it specifies how the
Opportunity layer chooses which 3–5 opportunities to surface each turn. No code, model, or
enum changes are introduced by this document. Implementation is a separate, subsequent task.

## Context

The P6 Opportunity System presents, each turn, 3–5 things worth engaging with — an NPC, a
Faction, a Location, a WildCard, or one of the player's own Legacies — and the player picks
one. The situation-first framing (the player chooses a *future* for a target; the domain is
a consequence, not the choice) is already approved. The open gap is the **selection rule**:
given many candidates, which 3–5 surface this turn?

The core experience of Chronicle Forge is **not "a game about choosing what is important"**
but **"a game about confronting the causality you planted."** Selection must therefore be
driven by **narrative tension**, not static importance. We define salience as a per-entity
**narrative tension score `T(entity, world)`**. Static power and size are demoted to a
subordinate factor; the drivers are *proximity to change, the player's own unresolved
threads, and the potential for reversal or peril*.

Requirements:

1. Select 3–5 opportunities per turn **deterministically** (same seed + same choice sequence
   → identical opportunities every turn).
2. The currently *tense* targets surface (no domination by static "big" entities).
3. The same target / kind does not recur turn after turn (**Opportunity Mix**).
4. Stakes rise in the latter half of a life (**Narrative Escalation**).
5. The player's own legacies are revisited only when **fresh** (**Legacy Freshness**).
6. Seed reproducibility is preserved (`simulate_world(seed)` stays reproducible).

## Design principles (consistent with "Rules own truth")

- Tension is a **pure function of world state** and is computed **read-only**. The salience
  layer is a volatile, derived view — the same category as Opportunity and Response. It adds
  no new truth to the causal model (Seed / Event / Heritage).
- **`models.py` and `enums.py` are not modified.** Every tension signal is derived from
  existing fields.
- Determinism is guaranteed by three mechanisms: (a) `T` is a pure function of world state,
  (b) ties are broken by a fixed, seed-derived jitter computed from immutable inputs, and
  (c) a stable sort with a total ordering key.

---

## 1. Universal tension signals (shared vocabulary across all kinds)

Each signal is normalized to `0..1`. They measure *narrative tension*, not importance.
`clamp01(x) = min(1, max(0, x))`.

- **Δ — CHANGE proximity**: how close the entity is to a state transition (seed maturation,
  ignition, mortality, threshold crossing).
- **Σ — STAKES**: the magnitude of what is at risk or possible. **Subordinate factor** —
  weighted low so that static "big" entities cannot dominate.
- **Ω — OPEN LOOP**: the player has already invested but it is unresolved — the pull to
  "go back and see how it turns out."
- **Ρ — REVERSAL / PERIL**: room for things to worsen, flip, or come into conflict.

```
T_raw = w_Δ · E_Δ(turn) · Δ  +  w_Σ · Σ  +  w_Ω · Ω  +  w_Ρ · Ρ
        w_Δ = 0.35,  w_Σ = 0.25,  w_Ω = 0.25,  w_Ρ = 0.15

T     = T_raw · recency_penalty  +  jitter
```

- Static Σ never exceeds 25% of the weight, so "merely big" never reaches the top; Δ / Ω / Ρ
  (movement, unresolved threads, peril) lead.
- **Escalation applies to Δ (imminence) only** via `E_Δ(turn) = 1 + 0.3 · prog` (see §5).
  **It is never multiplied into Ρ**, which structurally prevents late-game peril domination.

---

## 2. Per-kind tension (derivation of Δ / Σ / Ω / Ρ)

All signals use existing fields only.

### 2.1 NPC

- **Δ = max( mortality · Ω,  ripening )**
  - `mortality = clamp01((age - 50) / 30)`; `ripening = clamp01(max(elapsed / maturation_time))`
    over the player's own seeds targeting this NPC.
  - Weighting mortality by investment `Ω` means tension comes not from "this NPC is about to
    die" but from **"this is someone I shaped, and the window to finish what we started is
    closing."** An old NPC the player never touched does not surface on age alone.
- `Σ = 0.5 · tier_w + 0.3 · (faction.power / 100) + 0.2 · (ambitious / 100)`,
  `tier_w = {S: 1.0, A: 0.6, B: 0.2}`.
- `Ω = clamp01( (unfired player seeds targeting npc + active player→npc memories) / 3 )`.
- `Ρ = clamp01( (brave + ambitious + (100 - cautious)) / 300 )`.
  - **Provisional proxy — explicitly noted.** This `Personality`-based derivation is a
    *temporary stand-in* because negative memories, hostile relations, and NPC↔Player
    conflict data are **not yet implemented** in the engine (today all memories are positive;
    no player-keyed `Relation` is created). When those signals become available they are
    intended to **replace this proxy as the primary signal**, with `Personality` demoted to
    a secondary contribution.
- Excluded: `alive == False`.

### 2.2 Faction

FactionType → ThemeAxis (reusing `theme.FACTION_TYPE_TO_THEME`): LORD → governance,
MERCHANT → commerce, RELIGIOUS → faith, **ADVENTURER → warfare**. A seed is matched to a
faction by **ThemeAxis** — `SEED_DOMAIN_TO_THEME[seed.domain] == FACTION_TYPE_TO_THEME[faction.type]`
— rather than via a new FactionType→SeedDomain table (the INNOVATION axis maps from two
domains, so a direct domain table would be ambiguous).

- `Δ = theme_aligned ? (power / 100) : 0.3 · (power / 100)` — rising on the current dominant
  theme axis reads as "on the eve of dominance."
  - **Not a true growth rate — explicitly noted.** Because the world does not persist a
    history of `faction.power`, this Δ is an **approximation of "Emergence Pressure"** rather
    than measured growth. If a time series of `power` becomes available, this can be
    **replaced with an actual growth-rate basis** in the future.
- `Σ = power / 100`.
- `Ω = clamp01( player seeds whose axis matches the faction, planted in the last R years / 2 )`.
  Seeds carry `planted_year` (not action-turns), so this window is measured in **world-years**.
- `Ρ = clamp01( max(0, -min(relations.values())) / 100 )` — the strongest hostile relation is
  the kindling of conflict.

### 2.3 Location (auxiliary category)

Location is a **supporting** Opportunity category, **not a lead** — it varies the texture of a
turn rather than anchoring it. Its tension is therefore driven mainly by **Δ (imminence)**;
Stakes are a flat low baseline because the current world model carries no usable per-location
gradient (MVP reduction, B-1).

- **Δ_loc = max( frontier, convergence )** — the primary driver.
  - `frontier = 1.0 if (type == DUNGEON and undiscovered) else 0.0`. "Undiscovered" means no
    `Discovery` references this `location_id` — the **only authoritative source**;
    `Location.state` is never written by the engine.
  - `convergence = 0.7 if (theme_affinity == world.theme.dominant) else 0.2`.
- **Σ_loc = 0.2** — a flat, low baseline. `heritage_concentration` and `undev` are **removed
  from MVP**: the world model persists no per-location development level (`Location.state` is
  always empty) and never sets `CausalNode.location_id` (heritage cannot be traced to a place),
  so neither yields a usable gradient. Locations are intentionally non-discriminated on Stakes.
- `Ω = clamp01( (player seeds + discoveries at this location) / 2 )`.
- `Ρ = (type == DUNGEON and undiscovered) ? 1.0 : 0.2` — the unexplored carries latent danger
  (also feeds Δ as `frontier`).
- **Future extension point — `heritage_concentration`**: once `CausalNode.location_id` is
  populated at event-firing time, restore
  `Σ_loc = clamp01( undev · theme_alignment + heritage_concentration )`, where
  `heritage_concentration = clamp01( heritage-promoted causal_nodes at this location_id / 2 )`.
  Recorded here so the richer Location stakes can be reinstated without redesign.

### 2.4 WildCard (the primary tension engine)

`"stirring"` is **derived, not a new enum value**: `status == DORMANT and len(trajectory) > 0`.

- `Δ = IGNITED: 1.0 / "stirring": 0.6 / DORMANT: 0.25` (RESOLVED and DEAD are excluded).
- `Σ = clamp01( sum(|impact_vector.values()|) / 200 )`.
- `Ω = (player_interaction set and status != RESOLVED) ? 1.0 : 0.3`.
- `Ρ = (archetype in {CONQUEROR, ZEALOT, REVOLUTIONARY}) ? 0.8 : 0.3`.

### 2.5 Legacy (the player's own past heritage)

- `Δ = freshness = clamp01( (heritage_score − last-offered score) / FRESH_DELTA )`.
- `Σ = clamp01( heritage_score / max heritage_score in world )`.
- `Ω = clamp01( reach / 5 )`.
- `Ρ = 0.3` (legacies are mostly positive — low peril).
- **Freshness gate** (§3-4) plus a reserved future extension point **`legacy_state_changed`**:
  the score-delta approximation is sufficient for MVP, but because `heritage_score` is a
  function of `(weight, longevity, reach)`, changes with a small score delta — *type promotion
  (HEIR → INSTITUTION), a new descendant `CausalNode`, `reach++`, a longevity milestone* — may
  be missed. `legacy_state_changed` is documented as the drop-in replacement point for the
  freshness gate when "what we truly want is a *changed* legacy" is implemented.

---

## 3. Diversity / Mix / Freshness constraints

`history` lives in the **volatile life-session controller**, not in `World`. It holds the last
`R = 2` turns of `{offered_target_ids, selected_target_id, offered_kinds}` plus, for legacies,
`{heritage_id → (last_offered_turn, last_score)}`. It advances deterministically given the same
seed and choice sequence.

1. **Recency penalty (multiplicative)**: selected last turn ×0.5; offered (not selected) last
   turn ×0.7; offered two turns ago ×0.85. The penalty decays, so any sufficiently tense target
   resurfaces (anti-starvation).
2. **Per-kind cap (final selection, §4)**: `cap = {WILDCARD: 2, LEGACY: 1, default: ceil(K/2)}`.
   Caps WildCard domination of the top slots and Legacy noise.
3. **Opportunity Mix floor (§4)**: when ≥3 kinds have candidates, the top-K contains at least
   `min(3, kinds_present)` distinct kinds.
4. **Legacy Freshness gate (candidate stage)**: a Legacy is eligible only if (a) its score
   increased since it was last offered (fresh), or (b) it has not been offered in the last
   `F = 3` turns. Consecutive offering is allowed only when the score increased (I12).

---

## 4. Top-K selection (per-kind cap + Mix floor, deterministic)

```
KIND_ORDER = {WILDCARD: 0, NPC: 1, FACTION: 2, LOCATION: 3, LEGACY: 4}   # tie-break order
CAP        = {"wildcard": 2, "legacy": 1}                                # default = ceil(K/2)

def select_top_k(scored):       # scored: items with .kind/.id/.tension (penalty+escalation+jitter applied)
    order = sorted(scored, key=lambda c: (-c.tension, KIND_ORDER[c.kind], c.id))   # total order
    K     = clamp(len(order), 3, 5)
    cap   = lambda k: CAP.get(k, ceil(K / 2))
    kinds_present = distinct kinds in order
    MIN_KINDS     = min(3, len(kinds_present))

    selected, kc = [], Counter()
    for c in order:                                 # Pass 1: tension-first under per-kind cap
        if len(selected) == K: break
        if kc[c.kind] >= cap(c.kind): continue
        selected.append(c); kc[c.kind] += 1

    if len(selected) < K:                           # Pass 2: relax caps only if short of K
        for c in order:
            if len(selected) == K: break
            if c in selected: continue
            selected.append(c); kc[c.kind] += 1

    while distinct_kinds(selected) < MIN_KINDS:     # Pass 3: satisfy Mix floor via deterministic swap
        missing = first c in order whose kind not in selected
        if missing is None: break
        victim = argmin over selected where kc[kind] > 1 by (tension, -KIND_ORDER, -lexid)
        if victim is None: break
        selected.remove(victim); kc[victim.kind] -= 1
        selected.append(missing); kc[missing.kind] += 1

    return sorted(selected, key=lambda c: (-c.tension, KIND_ORDER[c.kind], c.id))
```

Every pass walks the sorted order, so the result is deterministic. Pass 1 is tension-first
under caps; Pass 2 guarantees cardinality when caps would otherwise starve the set; Pass 3
enforces the Mix floor with minimal, deterministic swaps.

---

## 5. Narrative Escalation (imminence only)

```
prog      = clamp01(turn_index / EXPECTED_TURNS)    # EXPECTED_TURNS ≈ 18
E_Δ(turn) = 1 + ESCALATION_GAIN · prog              # ESCALATION_GAIN <= 0.3, monotonic non-decreasing in turn
```

- **Applies to (imminence only)**: NPC `mortality · Ω`, seed `ripening`, WildCard
  `ignition proximity`, Location `frontier / discovery imminence`.
- **Does not apply to**: `peril (Ρ)`, `hostility`, `faction rivalry`,
  `conqueror / zealot archetype`.
- Design constraint: `ESCALATION_GAIN <= 0.3`.
- Rationale: the world escalates emergently anyway (Ω rises, seeds mature, WildCards ignite).
  The artificial factor is a gentle nudge that makes "now-or-never" moments stand out slightly
  more late in a life, without inflating peril.

---

## 6. Determinism guarantees

1. **`T` is a pure function**: every signal depends only on world state at turn `T` (no RNG).
2. **Jitter is derived from immutable inputs** (R5). The actual API is
   `macro.derive_rng(world, mixer: int, salt: int)`, which depends only on `world.seed`
   (immutable) and its integer arguments — it does not read mutable world state. Salience folds
   its immutable keys into the single integer mixer:
   `mixer = life_index * 1000 + turn_index` (where `life_index` is the life's position in
   `world.lives`), then `j = derive_rng(world, mixer, salt=SALIENCE_SALT).random() * 0.05`.
3. **Stable sort** on `(-tension, KIND_ORDER[kind], id)` gives a total order (ties resolve
   uniquely).
4. **`E_Δ(turn)` is a pure function** and monotonic non-decreasing in `turn_index`.
5. **`history` advances deterministically** as a function of seed and choice sequence.
6. **Empty-set guard**: when there are no candidates, return at least 1 (whatever exists);
   avoids division by zero.
7. **Read-only**: the computation never mutates `World` (tested by I6).
8. **Pre-indexing (avoids O(N²))**: build `seeds_by_target`, `memories_by_subject`, and
   `recent_seeds_by_domain` once per turn, then score candidates with O(1) lookups. Overall
   cost is `O(seeds + memories + candidates)`.

`SALIENCE_SALT` is a new constant distinct from autoplay's `_AUTOPLAY_SALT = 99` (e.g. `77`).

---

## 7. Invariants

- **I1 Determinism**: same `(seed, choice sequence)` → identical opportunity id sequence every
  turn.
- **I2 Grounding**: every Opportunity points to a real, live/active entity in `World`.
- **I3 Cardinality**: `3 ≤ offered ≤ 5` (if fewer than 3 candidates exist, offer what exists,
  minimum 1).
- **I6 Read-only**: world serialization is unchanged before/after the computation.
- **I7 Anti-starvation**: the recency penalty decays, so any sufficiently tense target
  resurfaces within finite turns.
- **I8 Exclusion**: dead NPCs and RESOLVED/DEAD WildCards are never offered.
- **I9 Boundedness**: all scores are finite and normalized; no exception on an empty set.
- **I10 Opportunity Mix**: when ≥3 kinds have candidates, the top-K contains ≥
  `min(3, kinds_present)` distinct kinds, and no kind exceeds its per-kind cap
  (WildCard ≤ 2, Legacy ≤ 1, default `ceil(K/2)`).
- **I11 Narrative Escalation**: `E_Δ(turn_index)` is monotonic non-decreasing; therefore, for
  an otherwise-identical world state, an imminence-driven candidate's tension at `t2 ≥ t1` for
  `t1 < t2` (verified as a pure-function monotonicity property). **Ρ is excluded from
  escalation** (peril domination is structurally ruled out).
- **I12 Legacy Freshness**: the same `heritage_id` is offered as a Legacy on consecutive turns
  only if its `heritage_score` increased since it was last offered.

---

## 8. Test plan (`tests/test_salience.py`)

- `test_deterministic`: two runs produce an identical opportunity id sequence (I1).
- `test_cardinality`: always 3–5 with enough candidates; graceful degradation when fewer (I3).
- `test_grounding`: every target exists and is live/active (I2, I8).
- `test_opportunity_mix_and_caps`: with ≥3 kinds, distinct kinds ≥ `min(3, kinds)`, and
  WildCard ≤ 2 / Legacy ≤ 1 / default ≤ `ceil(K/2)` (I10).
- `test_npc_mortality_requires_investment`: an old NPC with `Ω = 0` does not rank top; with
  `Ω > 0` it does (C1).
- `test_npc_peril_from_personality`: with no negative memories, an NPC high in brave/ambitious
  and low in cautious still has `Ρ > 0` (C2).
- `test_location_imminence_not_undev`: a merely-undeveloped lot loses on tension to a frontier
  dungeon / theme-convergent site (C3).
- `test_escalation_imminence_only`: varying only `turn_index` on a fixed world, imminence
  candidates' tension is non-decreasing in turn, and Ρ-driven candidates do not rise from
  escalation (I11).
- `test_legacy_freshness`: a legacy with unchanged score is not offered on consecutive turns;
  a score increase re-offers it (I12).
- `test_diversity_target_recency`: a target selected at T does not dominate at T+1 and
  resurfaces later (I7).
- `test_wildcard_tension_order`: all else equal, IGNITED > "stirring" > DORMANT (by Δ).
- `test_static_size_not_dominant`: a large Faction high only in Σ loses to a small WildCard
  high in Δ / Ω / Ρ.
- `test_readonly`: `world.model_dump()` is deep-equal before/after (I6).
- `test_no_quadratic`: candidate scoring goes through the pre-built indexes and does not repeat
  linear scans of seeds/memories (verifies index-build count, C4).

---

## 9. Reused existing code

- `src/chronicle_forge/macro.py::derive_rng` — deterministic jitter, used with immutable inputs
  (same mechanism as autoplay).
- `src/chronicle_forge/profiles.py::ACTIVITY_PROFILES` — kind/domain → theme-axis mapping.
- `src/chronicle_forge/models.py` — the source of every signal; **not modified**.
- `src/chronicle_forge/autoplay.py` — the future connection point where `_pick_activity` is
  replaced by tension-driven selection. This document defines the interface only; wiring is
  deferred to the P6 implementation phase.

---

## Known limitations (recorded for review)

- **Faction Δ / Ω**: no `faction.power` history is persisted, so true growth is unavailable.
  Δ approximates Emergence Pressure (theme-aligned ascendancy); Ω uses recent player
  involvement as a proxy. Replaceable with a growth-rate basis when a power time series exists.
- **NPC Ρ**: the engine does not generate negative memories or hostile relations, so Ρ is
  derived from `Personality` as a provisional proxy, to be replaced by negative-memory /
  hostility / conflict signals when implemented.
- **Location is an auxiliary category (MVP reduction, B-1)**: `CausalNode.location_id` is never
  populated and `Location.state` is always empty, so heritage cannot be traced to a place and
  there is no per-location development gradient. `Σ_loc` is therefore a flat baseline (0.2) and
  Location tension rests on Δ (frontier / convergence). `heritage_concentration` is recorded in
  §2.3 as the future extension point once `CausalNode.location_id` exists.
- **NPC ↔ WildCard linkage**: no direct link exists in the model; MVP does not fold WildCard
  linkage into NPC Ρ (future hook).
- **Early-game NPC balance (R3)**: NPCs with zero investment rely on Σ and may surface less
  early on. **Adopted mitigation: the Mix floor (plus tie-break jitter)** — no new signal is
  added. A tier-based Σ floor is intentionally **not** introduced, since it would re-admit
  static importance through the back door and conflict with C1's investment-gated Δ. The
  fixed-seed play log is used to verify the early-game kind distribution; the floor remains an
  explicitly rejected option, revisited only if measurement shows starvation.
- **`"stirring"` WildCard**: derived from `DORMANT + trajectory`, no enum addition.
- **Legacy Freshness / recency history**: volatile session state, never persisted to `World`.
- **`legacy_state_changed`**: MVP uses the score-delta approximation; reserved as the future
  extension point that captures structural changes to a legacy.
