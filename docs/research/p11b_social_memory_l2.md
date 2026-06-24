# P11-B — Social Memory L2: Cross-Life Influence (Design Research)

Status: **Design research — the locked S1–S5 spec below is now IMPLEMENTED.** This
document scoped the engine impact of cross-life Social Memory and recorded the
safety boundary; the locked spec was subsequently built (see
`docs/design_p11b_social_memory_l2.md` "as built"). The one engine-flow correction
made during implementation is recorded inline in **S1 "Engine-flow clarification
(REWORK)"** — design intent is unchanged. Companion: `p11b_decision_matrix.md`.

Boundary the implementation honored: no `ENGINE_VERSION` bump, `Recipe` gains only a
defaulted additive field, no P11-A / WorldView change, off-path byte-identical.

## 1. Problem statement

P10-L1 (Social Memory View) and P11-A (Read-Model) **surface** the social trace a
soul leaves across its lives, but the world never **acts** on it across the
reincarnation boundary in a deliberate, designed way. L2 asks: can a past self's
bonds *steer the world* — NPCs who loved/feared a former life behave accordingly,
and memories **fade over the time-skip** — while preserving P11-A's three
guarantees: **determinism, Replay compatibility, Recipe compatibility**?

The whole risk is that L2 is the *first* phase to deliberately mutate
behavior-driving state during the macro skip. It must do so without moving any
existing golden when disabled, and reproducibly when enabled.

## 2. Grounding — what the engine does **today** (facts, read from source)

| Fact | Source | Implication for L2 |
|---|---|---|
| Memories & relations are **soul-anchored** — `form_memory(..., actor_id=life.player_id, ...)` writes `world.memories` and `NPC.relations[player_id]` toward the stable `Player.id`, surviving the skip while the NPC lives. | `memory.py:21-54`, `activity.py:109`, `powers.py:35` | The cross-life data **already exists**; L2 adds *consumption/decay*, not new accumulation. |
| **Soul-memory already influences the macro world.** `npc_signals` counts `active_memories` = soul-memories with `intensity/100 ≥ MEMORY_MIN_INTENSITY (0.20)` and feeds `omega = clamp01((pending + active_memories)/3) → delta`, which drives opportunity firing → which NPCs/factions make history. | `opportunity.py:191-199`, `:45` | A behavioral channel **already exists** but is **static** (no decay). L2's decay rides this existing seam — high leverage, high butterfly sensitivity. |
| `Memory.decay_rate` (default `0.05`; imprints `IMPRINT_DECAY=0.01`) is **stored but never applied** — no code reduces `intensity` over time. | `models.py:225`, `memory.py:28`, grep: no consumer of `decay_rate` | Decay is a **dormant, pre-shaped field**. L2 activates it; the schema already anticipates it. |
| **`NPC.relations[player_id]` is written but never read** to choose behavior. `choose_intent` is a pure personality argmax; `npc_signals` reads *memories*, not *relations*. | `npc.py:16-34`, `opportunity.py:183-211` | "Relations steer NPC behavior" is a **genuinely new lever** (vs. decay, which perturbs an existing one). |
| Skip = `time_skip(world, life)` runs `advance_year(world)` per world-year; `advance_to_next_life` = skip then `begin_life`. Deterministic RNG via `derive_rng(world, year, salt)`. | `macro.py:294-331`, `:45`, `:261` | Decay has a clean per-year hook (`advance_year`) or a per-skip hook (`time_skip`). |
| `Recipe` = `{engine_version, seed, max_year, mode, inputs}`, `extra="forbid"`, but a **missing known field with a default loads fine** → adding `social_memory: bool = False` keeps every existing recipe valid and byte-identical on replay. | `persistence/schema.py:32-55` | The flag-gate save story is already proven by P9 semantics. |
| `ENGINE_VERSION = "0.1.0-p8-mvp"`; `load.py` refuses replay on mismatch. | `persistence/version.py:16`, `load.py:37` | Bumping it would refuse **all** existing recipes — to be avoided unless forced. |
| Entry points: `simulate_world(seed, life_cap, mode)`, `run_human_world(...)`. | `autoplay.py:125`, `play/session.py:64` | The flag threads in as a defaulted param, never stored in `World`. |

**Critical inference:** the flag must be a **transient run parameter, never persisted
into `World`**. Storing it would change `world.model_dump_json()` even when off and
break the seed42 golden `e62d8f2c…`. It rides only in the *Recipe* (the save).

## 3. Difference vs P10 / P11-A

| | P10-L1 / P11-A | P11-B (L2) |
|---|---|---|
| Direction | **Read** soul-bonds | **Act on** soul-bonds + **decay** them |
| Engine touch | none (pure projection) | gated branches in `macro` / `memory` / (optionally) `opportunity` / `npc` |
| World hash | unchanged by construction | **changes on-path**; unchanged off-path (required) |
| New state | none | none new — *reuses* `intensity` / `relations`; only their *values* evolve |
| WorldView | defines the boundary | **schema unchanged**; on-path `bonds`/values differ (data, not shape) |

## 4. Memory-decay model candidates

All operate only when the flag is **on**. Symbols: `I` = `Memory.intensity` (int
0–100), `r` = `decay_rate`, `y` = years elapsed over a skip.

- **D0 — No memory decay; relations-only steer.** Leave `intensity` static; add a
  gated read of `relations[player_id]` into behavior (see §5). Smallest change to
  the existing `active_memories` path. Still changes the on-path hash via §5.
- **D1 — Per-year float decay.** In a gated `advance_year` branch: `I ← I·(1−r)`.
  Natural, but **floats accumulate** → replay-fragile across platforms/optimization;
  also re-quantizing for the `intensity/100 ≥ 0.20` gate is order-sensitive.
- **D2 — Per-skip block float decay.** Apply once per `time_skip`:
  `I ← I·(1−r)^y`. Fewer operations, same float-precision exposure (`pow`).
- **D3 — Per-year integer/quantized decay (recommended).** Keep `I` an `int`;
  decay deterministically, e.g. `I ← max(0, I − ceil(I·r))` per year, or a fixed
  linear `I ← max(0, I − k)` with integer `k`. **No float state is ever stored**,
  so replay is bit-stable by construction. The `≥ 0.20` threshold then flips at a
  reproducible year.
- **D4 — Relation-value decay toward 0.** Decay `affinity/trust/fear` (already
  signed ints) toward 0 over the skip (integer step), modelling fading sentiment;
  combine with §5 so the *behavioral* effect fades too.

**Decay recommendation:** **D3 (+ optionally D4)** — integer-quantized, applied at a
single fixed point per world-year inside a gated branch. It activates the dormant
`decay_rate` intent while eliminating the dominant determinism risk (float drift).

## 5. NPC-behavior influence scope

Two channels; L2 should pick the **narrowest** that delivers the player value.

- **Channel A — existing, indirect (via decay).** Decaying `intensity` changes the
  `active_memories` count in `npc_signals` → `omega` → `delta` → opportunity
  firing. This is *already wired*; decay simply makes it time-varying. **High
  leverage, high butterfly risk** (one flipped threshold reshapes downstream
  history).
- **Channel B — new, direct (relations steer).** Feed `relations[player_id]` into
  behavior, gated:
  - bias `npc_signals` (e.g. a new term from `affinity`/`fear`), or
  - bias `choose_intent` (e.g. high fear → defensive intent).
  This is the deliberate "they remember you" effect.

**Boundary (inviolable):** L2 touches **only the macro/opportunity history layer**.
It must **not** edit P6 firing rules, P7 experience text, the P8 play loop, P9
persistence semantics, P10 Observatory, or the P11-A WorldView **schema**. Only
NPCs that already hold a soul-relation are affected, and only during history
generation.

**Recommendation:** ship **Channel B with D3 decay**, keep Channel A's perturbation
**minimal and well-frozen**. Channel B is the legible player value; Channel A is an
unavoidable side-effect of decay that the on-path golden must pin.

## 6. Flag-gate strategy

1. `Recipe.social_memory: bool = False` (additive; `extra="forbid"` safe because a
   missing field defaults).
2. Entry points gain `social_memory: bool = False` (`simulate_world`,
   `run_human_world`); the value threads to the macro calls **as an argument**,
   **never stored in `World`**.
3. **Off ⇒ complete no-op:** not one new branch executes; output byte-identical to
   today (the flag-gate guarantee).
4. **On ⇒ a new world:** a separate frozen golden is minted (§9); existing goldens
   are never touched.

## 7. Replay-determinism impact

- The flag **rides in the Recipe**, so replay reproduces the exact on/off path.
- **Decay must be float-free** (D3/D4): no `pow`, no accumulating `float` in stored
  state. The `≥ 0.20` gate then flips deterministically.
- **No new RNG stream** ideally (decay is arithmetic). If any randomness is ever
  needed, use `derive_rng(world, year, salt=<new unique salt>)` so existing RNG
  draws are not perturbed — but the recommendation is **zero RNG**.
- **Stable iteration order** when decaying `world.memories` (a list — already
  ordered) and `relations` (dict — iterate by sorted key) so no dict-ordering leak.

## 8. Recipe compatibility

- **Backward:** every existing recipe (no `social_memory` field) → default `False`
  → **identical replay**. ✅
- **Forward (note):** a *new* recipe with `social_memory=true` carries the field; a
  hypothetical **pre-L2 engine** would reject it via `extra="forbid"`. Acceptable —
  pre-L2 engines do not exist after merge, and `engine_version` already governs
  cross-version refusal. Documented as a known, bounded limitation (§11).

## 9. ENGINE_VERSION change — required?

**Recommendation: do not bump** (consistent with the prior L2 design note).
- Off-path world/transcript goldens are **unaffected**, and that is the dominant
  compatibility guarantee — bumping would needlessly refuse all existing recipes
  (`load.py:37`).
- The only schema delta is a **defaulted** Recipe field; the world and transcript
  encodings are unchanged.
- **Caveat to weigh at build time:** if reviewers consider "a new recipe field that
  old engines reject" a breaking serialization change, a *minor* bump could be
  justified. The matrix records this as a deliberate, reversible call; default
  stance is **no bump**.

## 10. Golden-hash update — required?

- **Off-path (default): NO update.** All five goldens stay frozen and asserted:
  world `e62d8f2c…`, transcript `98bea862…`, observatory `f9ad13c7…`, social-memory
  `3fbb1aa0…`, world-model `5b41a692…`. This is the primary protection.
- **On-path: ADD exactly one new golden** (`seed42 + social_memory=on` world hash,
  and the on-path transcript if play output changes). The existing five are
  **never** modified. P11-A's `world_model` hash is unchanged off-path; on-path it
  legitimately differs (values, not schema) and would get its own pinned value.

## 11. Rollback strategy

L2 is purely additive and default-off, so rollback is cheap:
- **Disable:** ship/leave the flag default `False` — the world is byte-identical to
  pre-L2. No data migration (no new persisted state).
- **Revert code:** remove the gated branches; off-path is untouched, so no golden
  moves. The `Recipe.social_memory` field may stay (harmless, defaulted) or be
  removed in the same revert.
- **Tag/branch:** additive commits revert cleanly; `v0.3.0-read-model` is unaffected
  because L2 is a later, separate line.

## 12. Risk register

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **Float decay → replay divergence** across platforms/optimizations. | High | D3/D4 integer-only decay; no `float` in stored state; no `pow`. |
| R2 | **Butterfly via Channel A** — a flipped `active_memories` threshold reshapes downstream history; on-path golden brittle. | Medium-High | Freeze the on-path golden carefully; prefer minimal decay step; keep Channel B as the primary lever; add a determinism test that re-runs the on-path twice. |
| R3 | **Flag accidentally persisted in `World`** → off-path world hash changes, breaking `e62d8f2c…`. | High | Flag is a transient arg only; add a test asserting off-path `world.model_dump_json()` byte-identical. |
| R4 | **Scope creep into P6/P7/P8/WorldView.** | High | Hard boundary: macro/opportunity/memory/npc only; assert P6 firing & P7 text unchanged; WorldView **schema** unchanged. |
| R5 | **Dict-order leak** when decaying `relations`. | Medium | Iterate `relations` by sorted key; memories list is already ordered. |
| R6 | **Recipe forward-incompat** (old engine rejects new field). | Low | Accepted & documented (§8); governed by `engine_version`. |
| R7 | **On-path P11-A `world_model` hash** shifts and is mistaken for a regression. | Low | Mint a separate on-path world-model golden; keep off-path assertion as the guard. |

## 13. Recommendation

**GO with Flag.** Build L2 as a `Recipe.social_memory`-gated, **default-off**
extension confined to the macro/opportunity layer:
- **Channel B** (relations steer NPC behavior) as the deliberate player value, plus
- **D3 integer decay** (optionally D4) to activate the dormant `decay_rate` intent,
- **no float state, no new RNG, no persisted flag, ENGINE_VERSION unchanged**,
- **off-path byte-identical** (five goldens protected & asserted), **on-path** mints
  one new golden,
- **no P6/P7/P8/P9/P10/WorldView-schema change.**

Rationale, axis-by-axis comparison, and the explicit GO / GO-with-Flag / REJECT
verdict per candidate are in `p11b_decision_matrix.md`.

---

# L2 Specification (locked design — still no implementation)

The sections below freeze the contract a later, separately-approved L2 issue must
implement. They are **design statements only**; no code, test, Recipe, or
ENGINE_VERSION change is made here.

## S1. Social Memory pipeline order (fixed)

> **Engine-flow clarification (REWORK).** The intent below is unchanged — *decay
> the soul's state each skip-year, and let opportunity scoring act on the decayed
> state.* The mechanism is stated precisely against the real control flow: the
> reincarnation cycle is `live(N) → time_skip(N) → live(N+1) → …`. Opportunity
> scoring (`npc_signals`, the only reader of `Memory.intensity` and
> `relations[player_id]`) runs **during a life's turns**, not inside `time_skip`;
> `time_skip`/`advance_year` never score opportunities. So L2 decay (P1/P2) runs
> **per world-year inside `time_skip`**, and the **next life's** opportunity
> scoring then observes the decayed intensities (P3 bias is applied there, in
> `npc_signals`). P3/P4 below are realized in the *following* live phase, not in
> `advance_year`.

When `social_memory` is **on**, each world-year advanced inside `time_skip`
executes the L2 decay stages in this **exact, fixed order**; the resulting decayed
state is what the **next live phase's** opportunity scoring reads:

```
for each world-year y advanced during time_skip (flag ON):
    P1. Memory decay      (D3)  — decay every soul-memory's intensity (§S2)
    P2. Relation decay    (D4)  — move every soul-relation toward 0   (§S2)
    [then advance_year runs as today — it does not read intensity/relations]

then, in the NEXT live phase (the reincarnation that follows the skip):
    P3. Behavior bias prep      — compute per-NPC relation bias       (§S3)
    P4. [existing] opportunity scoring (npc_signals) now reads the decayed
        intensities and applies the bias to Delta
```

Ordering rules that make it reproducible:
- P1 → P2 (per skip-year) then P3 → P4 (next life) is **total and stable**;
  scoring (P4) always observes the *post-decay* state.
- **Iteration order is fixed:** memories in `world.memories` **list order**; NPCs in
  `world.npcs` **list order**; only each NPC's single `relations[player_id]` entry
  is touched, so no dict/set iteration leaks into results.
- L2 stages are **pure arithmetic** (no RNG). If randomness were ever introduced it
  must use `derive_rng(world, y, salt=<unique L2 salt>)`; the locked spec uses
  **none**.
- When **off**, stages P1–P3 do not exist in the executed path; `time_skip` and
  `npc_signals` are the unchanged code — byte-identical to today.

## S2. D3 integer decay — exact formulae

All decayed quantities remain **integers**; no float is ever stored. The decay rate
is treated as an **exact rational** `R = R_NUM / R_DEN` (so `decay_rate = 0.05 ⇒
R_NUM=1, R_DEN=20`; imprint `0.01 ⇒ 1/100`). For a quantity `Q ∈ ℤ≥0` decayed once
per world-year:

```
step  = ceil(Q · R_NUM / R_DEN)
      = (Q · R_NUM + R_DEN − 1) // R_DEN        # pure integer, float-free
Q'    = max(0, Q − step)
```

Applied per stage:
- **P1 memory intensity** `I` (0..100): `I' = max(0, I − ceil(I·R))`. `ceil`
  guarantees any non-zero memory loses ≥1/yr (no stuck plateau); once `I` reaches
  `0` it stays `0` (forgotten). The opportunity gate `intensity/100 ≥
  MEMORY_MIN_INTENSITY (0.20)` becomes the **integer test `I ≥ 20`**; decay flips a
  memory out of `active_memories` at a reproducible year.
- **P2 relation values** `v ∈ {affinity, trust, fear}` (signed −100..100) decay
  toward `0` by magnitude (sign-preserving):
  `mag' = max(0, |v| − ceil(|v|·R)); v' = sign(v)·mag'`.

Determinism note: the intermediate `Q·R_NUM` is integer; the only division is
integer floor `//`. There is **no `float`, no `pow`, no rounding-mode dependence**,
so the result is bit-identical on every platform — the core reason D3 is chosen
over the rejected float models D1/D2.

## S3. NPC relation-bias spec (MAX_BIAS)

Channel B converts an NPC's surviving soul-relation into a **bounded** bias on its
opportunity signal, computed fresh each scoring pass (transient, never stored):

```
a_n   = affinity / 100          # ∈ [−1, 1]
f_n   = fear     / 100          # ∈ [0, 1] after clamp
raw   = W_AFF · a_n − W_FEAR · f_n          # love lifts, fear suppresses/redirects
bias  = clamp(raw · MAX_BIAS, −MAX_BIAS, +MAX_BIAS)
delta' = clamp01(delta + bias)              # biases the existing opportunity signal
```

Locked constants (subordinate to the structural signals by construction):
- **`MAX_BIAS = 0.15`** — relation influence may never move the `[0,1]` signal by
  more than ±0.15, so it can shade but not dominate opportunity selection.
- **`W_AFF = 0.6`, `W_FEAR = 0.4`** (sum 1) — affinity weighted above fear.
- Only NPCs that already hold a `relations[player_id]` entry are biased; all others
  score exactly as today.
- The bias uses the **same float-signal convention** as the existing `npc_signals`
  (`clamp01`, divisions) and is **not stored state**, so it carries no new
  determinism exposure beyond the engine's current, already-reproducible signal
  math. The determinism-critical *stored* state (intensity, relations) stays
  integer per §S2.

## S4. Golden strategy (locked)

- **Off-path (default): the existing five goldens are FIXED and asserted unchanged
  — no new golden is added.**

  | Artifact | Frozen hash |
  |---|---|
  | seed42 world | `e62d8f2cd24d2c72` |
  | replay transcript | `98bea8622c686d8e` |
  | observatory | `f9ad13c75c88a9c2` |
  | social memory | `3fbb1aa02071dfe2` |
  | world model | `5b41a692cfa3f1ce` |

- **On-path: exactly ONE new golden is added — `GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA`**
  `= sha256(simulate_world(42, "opportunity", social_memory=True)
  .model_dump_json())[:16]` **`= "0eb1d217a2b8e144"`** (frozen as built). A second
  on-path transcript golden is added **only if** the on-path changes play stdout; otherwise
  the world golden is the sole on-path guard.
- The five off-path goldens are **never modified or recomputed** by L2. P11-A's
  `world_model` hash is unchanged off-path; on-path it legitimately differs (values,
  not schema) and is covered by the on-path world golden, not by editing the
  off-path one.

## S5. Replay-guarantee test plan (design only — NO tests added now)

Specifies the checks the L2 issue must add; **none are written here**.

**Off-path (default — the primary protection):**
- `T-OFF-1` — `replay_transcript(build_recipe(seed=42, max_year=MAX_YEAR,
  mode="auto", inputs=[]))` (no `social_memory` field ⇒ defaults off) reproduces
  world `e62d8f2c…` **and** transcript `98bea862…`.
- `T-OFF-2` — no-op proof: with the flag off, `world.model_dump_json()` is
  byte-identical to a pre-L2 run (not one L2 branch executes).
- `T-OFF-3` — all five frozen goldens (§S4) still assert equal.
- `T-OFF-4` — a legacy recipe persisted **before** the field exists still loads
  (missing field ⇒ default false) and replays identically.

**On-path (flag = true):**
- `T-ON-1` — double-run determinism: replaying the same `social_memory=true` recipe
  twice yields byte-identical worlds.
- `T-ON-2` — fresh-process reproduction of `GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA`.
- `T-ON-3` — Recipe round-trip: `save_recipe`/`read_recipe` preserves
  `social_memory=true`; the loaded recipe replays to the same on-path world.
- `T-ON-4` — integer-state invariant: after a skip, every `Memory.intensity` and
  every `Relation.{affinity,trust,fear}` is an `int` (no float crept into stored
  state).
- `T-ON-5` — `engine_version` mismatch still refuses replay (governance unchanged;
  ENGINE_VERSION itself is **not** bumped by L2).

**Boundary guards (both paths):**
- P6 firing decisions, P7 experience text, and the **WorldView schema** are
  unchanged; only on-path `bonds`/values differ.
