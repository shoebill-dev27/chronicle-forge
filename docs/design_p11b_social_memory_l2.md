# P11-B Social Memory L2 — Detailed Design (as built)

Status: **Implemented.** The locked spec is the research doc
`docs/research/p11b_social_memory_l2.md` → **"L2 Specification (locked)" (S1–S5)**;
this document operationalizes S1–S5 into the shipped module/engine API. Verdict
adopted from `docs/research/p11b_decision_matrix.md`: **GO with Flag**.

## 0. Scope of this issue

This issue ships, as a single change:
- this design doc and the research/decision docs,
- `src/chronicle_forge/social_memory_l2.py` — the pure L2 primitives,
- the gated engine wiring (`autoplay` / `macro` / `opportunity` / `execution` /
  `play.session` / `persistence`), and
- `tests/test_social_memory_l2.py` — the S1–S5 contract tests (all green).

**Unchanged (hard constraints, verified):** `reporting/world_model.py` (P11-A),
`ENGINE_VERSION` (`0.1.0-p8-mvp`), the existing five off-path goldens, and the
P6/P7/P8/P9/P10 behaviour. The off-path world is byte-identical to today.

## 1. Purpose

Make the world **act on** a soul's cross-life bonds — NPCs who loved/feared a past
self behave accordingly, and memories **fade over the time-skip** — while keeping
P11-A's determinism, Replay, and Recipe guarantees. The data already exists and is
soul-anchored (see research §2); L2 adds **consumption + decay**, gated off by
default.

## 2. Module + engine API (as built)

Pure module **`src/chronicle_forge/social_memory_l2.py`** (additive sibling) holds
the L2 primitives the engine threads in when the flag is on:

```python
# --- S3 constants (locked) ---
MAX_BIAS: float = 0.15
W_AFF: float = 0.6
W_FEAR: float = 0.4
MEMORY_ACTIVE_MIN: int = 20          # integer form of MEMORY_MIN_INTENSITY (0.20)

# --- S2 integer decay (float-free) ---
def decay_step(q: int, r_num: int, r_den: int) -> int:
    """ceil(q * r_num / r_den) via pure integer arithmetic."""
def decay_intensity(intensity: int, r_num: int, r_den: int) -> int:
    """max(0, intensity - decay_step(intensity, r_num, r_den))."""
def decay_relation_value(value: int, r_num: int, r_den: int) -> int:
    """Sign-preserving decay of a signed relation value toward 0."""

# --- S3 bounded behavior bias ---
def relation_bias(affinity: int, fear: int) -> float:
    """clamp(raw * MAX_BIAS, -MAX_BIAS, +MAX_BIAS), raw = W_AFF*a/100 - W_FEAR*f/100."""

# --- S1 per-skip-year decay (P1 memory + P2 relation) ---
def decay_world_one_year(world: World) -> None:
    """One world-year of soul-memory + soul-relation decay; integer-only, no RNG."""
```

There is **no separate `simulate_world_l2` entry**. The flag is a transient run
argument threaded through the *existing* entry points:

- `autoplay.simulate_world(seed, life_cap=60, mode="legacy", social_memory=False)`
- `play.session.run_human_world(seed, *, ..., social_memory=False)`
- `macro.time_skip(world, deceased_life, social_memory=False)` — calls
  `decay_world_one_year` once per skip-year when on.
- `opportunity.npc_signals(npc, world, idx, social_memory=False)` — applies
  `relation_bias` to `delta` for NPCs holding a `relations[player_id]` entry;
  threaded via `select_opportunities` / `_gather` and `execution.play_turn`.
- `persistence`: `Recipe.social_memory: bool = False` (additive, defaulted);
  `build_recipe(..., social_memory=False)`; `replay`/`load` pass
  `recipe.social_memory` into `run_human_world`. `ENGINE_VERSION` unchanged.

The flag is **never stored in `World`**.

## 3. Spec adopted from research S1–S5

- **S1 pipeline order:** per skip-year inside `time_skip`, `P1 memory-decay →
  P2 relation-decay` (then the unchanged `advance_year`, which does not read
  intensity/relations); the decayed state is then observed in the **next live
  phase**, where `P3 bias-prep → P4 opportunity scoring (npc_signals)` apply the
  relation bias to Delta. Fixed iteration order (`world.memories` list,
  `world.npcs` list, only the single `relations[player_id]` entry per NPC); no RNG.
  See the research S1 "Engine-flow clarification (REWORK)" for why scoring is in
  the live phase rather than in `advance_year`.
- **S2 formula:** `decay_step(q) = (q·R_NUM + R_DEN − 1) // R_DEN`,
  `q' = max(0, q − decay_step(q))`; gate becomes integer `intensity ≥ 20`.
- **S3 bias:** `MAX_BIAS=0.15`, `W_AFF=0.6`, `W_FEAR=0.4`;
  `delta' = clamp01(delta + bias)`; only NPCs holding a soul-relation are biased.
- **S4 goldens:** off = the five frozen hashes unchanged; on = **+1**
  `GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA = "0eb1d217a2b8e144"`.
- **S5 replay:** off/on test families (below).

## 4. Off-path guarantee (the primary protection)

With `social_memory=False` (the default), **not one L2 branch executes** and output
is **byte-identical** to today. `simulate_world(42, "opportunity",
social_memory=False)` reproduces world `e62d8f2cd24d2c72`, and
`world.model_dump_json()` equals the plain `simulate_world(42, "opportunity")`
bytes. The flag is a transient run argument threaded through the existing entry
points (`simulate_world` / `run_human_world`) and the `Recipe`; it is never
persisted into `World`, so the seed42 golden is intact by construction.

## 5. Test plan — `tests/test_social_memory_l2.py` (as shipped, all green)

**S2 — integer decay (float-free):** `test_decay_step_is_ceiling_integer`,
`test_decay_intensity_floors_at_zero_and_returns_int`,
`test_decay_relation_value_is_sign_preserving`, `test_decay_is_float_free_pure_int`.

**S3 — bounded bias:** `test_relation_bias_is_bounded_by_max_bias`,
`test_relation_bias_sign`, `test_relation_bias_constants_locked`.

**S3 wiring (no dead code):** `test_relation_bias_is_wired_into_npc_signals` — a
soul-relation moves an NPC's Delta with the flag on, proving `npc_signals` consumes
`relation_bias`.

**S1 / S4 / off-path — determinism & goldens:**
- `test_offpath_world_is_byte_identical` — `simulate_world(42,"opportunity",
  social_memory=False)` equals the plain `simulate_world(42,"opportunity")` bytes.
- `test_offpath_world_hash_is_frozen_golden` — its sha == `e62d8f2cd24d2c72`.
- `test_offpath_leaves_existing_goldens` — observatory/social-memory/world-model
  hashes equal the frozen `f9ad13c7…`/`3fbb1aa0…`/`5b41a692…`.
- `test_onpath_world_differs_from_offpath`, `test_onpath_world_hash_is_frozen_golden`
  (== `0eb1d217a2b8e144`), `test_onpath_is_deterministic_double_run`,
  `test_onpath_state_is_integer_only`.

**S5 — Recipe round-trip / replay:** `test_recipe_defaults_social_memory_false`,
`test_legacy_recipe_without_field_loads_off`, `test_recipe_roundtrip_preserves_flag`,
`test_replay_offpath_matches_world_golden`, `test_replay_onpath_matches_simulate_world`.

## 6. Architecture / placement

- **New:** `src/chronicle_forge/social_memory_l2.py` — pure decay/bias helpers +
  `decay_world_one_year`. Consumed by `macro.time_skip` (decay) and
  `opportunity.npc_signals` (bias).
- **Threaded (gated, default-off):** `autoplay.simulate_world` /
  `_live_one_opportunity`, `macro.time_skip`, `opportunity.{npc_signals,_gather,
  select_opportunities}`, `execution.play_turn`, `play.session.run_human_world` /
  `_live_one`, `persistence/{schema,save,replay,load}`.
- **Unchanged:** `reporting/world_model.py` (P11-A), `reporting/observatory.py`,
  `reporting/social_memory.py`, `models.py`, `ENGINE_VERSION`, P6/P7/P8/P9, the
  five off-path goldens.

## 7. Constraints honored

- **Off-path byte-identical** (seed42 golden protection), asserted by tests.
- `reporting/world_model.py`, `ENGINE_VERSION` **unchanged**; `Recipe` gains only a
  defaulted additive field.
- **Integer-only decay state**, **no float persisted**, **no new RNG**, flag never
  stored in `World`.
- On-path mints exactly one new golden (`0eb1d217a2b8e144`); the existing five are
  untouched.
