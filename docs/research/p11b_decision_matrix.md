# P11-B — Social Memory L2: Decision Matrix

Status: **RESEARCH ONLY.** Companion to `p11b_social_memory_l2.md`. No
implementation, no commit. Scores are relative (Low = best for risk axes, High =
best for value axes), grounded in the engine facts of §2 of the companion doc.

Axes:
- **Impl cost** — engineering effort (Low = cheap).
- **Determinism risk** — chance of non-reproducible state (Low = safe).
- **Replay risk** — chance a recipe replays differently (Low = safe).
- **Testability** — how easily the behavior is pinned by tests (High = easy).
- **3D / WorldView fit** — alignment with the P11-A structured boundary (High = better).
- **Player experience** — legibility/impact of "they remember you" (High = better).

## A. Decay-model candidates (flag **on** only)

| Option | Impl cost | Determinism risk | Replay risk | Testability | 3D/WorldView fit | Player exp | Verdict |
|---|---|---|---|---|---|---|---|
| **D0** No decay; relations-only steer | Low | Low | Low | High | Med | Med | GO with Flag |
| **D1** Per-year float decay `I·(1−r)` | Low | **High** | **High** | Low | Med | Med | **REJECT** |
| **D2** Per-skip float decay `I·(1−r)^y` | Low | **High** | **High** | Low | Med | Med | **REJECT** |
| **D3** Per-year **integer** decay | Med | Low | Low | High | High | Med-High | **GO with Flag** |
| **D4** Relation-value integer decay → 0 | Med | Low | Low | High | High | High | **GO with Flag** |

Notes:
- D1/D2 are **REJECT**: floating-point `intensity`/`pow` accumulates across the
  many-year skip and is re-quantized at the `≥ 0.20` gate (`opportunity.py:194`),
  the textbook source of platform-dependent replay divergence (R1). They fail the
  determinism and replay axes outright, which are gating for this codebase.
- D3 activates the dormant `decay_rate` field (`models.py:225`) with **integer-only
  state**, so replay is bit-stable. Slightly higher impl cost (careful rounding +
  on-path golden) buys the safety the rejected options lack.
- D4 (decay `affinity/trust/fear` toward 0) pairs with the relations-steer channel
  so the *behavioral* effect fades realistically — best player-experience score,
  same low risk as D3.
- D0 is the minimal fallback: ship the steer without touching memory intensity. It
  loses the "memories fade" fiction (lower player value) but is the cheapest safe
  step; viable as a phase-1 if reviewers want to de-risk the butterfly (R2) first.

## B. NPC-behavior channel

| Channel | Impl cost | Determinism risk | Replay risk | Testability | 3D/WorldView fit | Player exp | Verdict |
|---|---|---|---|---|---|---|---|
| **A** Indirect via `active_memories`→`omega` (decay rides existing wire) | Low | Med | Med | Med | Med | Low (implicit) | GO with Flag (minimal) |
| **B** Direct: `relations[player_id]` → `npc_signals`/`choose_intent` | Med | Low | Low | High | High | **High** | **GO with Flag** |

- Channel A is unavoidable the moment decay touches `intensity` (it perturbs the
  existing `omega` term) — its **butterfly sensitivity (R2)** is the main reason the
  on-path golden must be frozen with care. Keep its perturbation minimal.
- Channel B is the **deliberate, legible** player value and is read-bounded to NPCs
  that already hold a soul-relation; it is the easiest to test and the best
  WorldView fit (it surfaces through existing `bonds` values).

## C. ENGINE_VERSION decision

| Option | Impl cost | Determinism risk | Replay risk | Testability | 3D/WorldView fit | Player exp | Verdict |
|---|---|---|---|---|---|---|---|
| **No bump** (default-off, additive field) | Low | Low | **Low** (all existing recipes still replay) | High | High | n/a | **GO** |
| **Bump** ENGINE_VERSION | Low | Low | **High** (`load.py:37` refuses every existing recipe) | High | n/a | n/a | **REJECT** (unless a breaking serialization change is deliberately chosen) |

## D. Composite recommendation

**Selected configuration: Channel B + D3 (optionally D4), flag-gated, no ENGINE_VERSION bump.**

| Axis | Assessment |
|---|---|
| Impl cost | Medium — gated branches in `memory`/`macro`/`opportunity`/`npc`, one new recipe field, one new on-path golden. |
| Determinism risk | **Low** — integer-only decay, no float state, no new RNG, flag never persisted in `World`. |
| Replay risk | **Low** — flag rides in the Recipe; off-path byte-identical; on-path reproducible. |
| Testability | **High** — off-path: assert five goldens unchanged + `world.model_dump_json()` byte-identical; on-path: one frozen golden + a double-run determinism test. |
| 3D / WorldView fit | **High** — no WorldView **schema** change; on-path effects surface through existing `bonds` values, exactly the structured seam P11-A built. |
| Player experience | **High** — "NPCs remember and react to a past self, and that memory fades" is delivered legibly via Channel B + D4. |

## E. Final verdict

# GO with Flag

Proceed to a **separately-approved** L2 implementation issue under these
non-negotiable gates:
1. `Recipe.social_memory: bool = False`; flag is a **transient run arg**, never
   stored in `World`.
2. **Off-path is a complete no-op** — byte-identical output; the five existing
   goldens stay frozen and asserted.
3. **On-path** mints exactly one new golden; existing goldens untouched.
4. **Integer-only decay** (D3/D4); **no float state, no new RNG**.
5. **No P6 / P7 / P8 / P9 / P10-Observatory / WorldView-schema change**; effects
   confined to the macro/opportunity history layer.
6. **ENGINE_VERSION unchanged** (default stance; a bump is REJECTED unless a
   breaking serialization change is consciously elected and re-reviewed).

REJECTED sub-options: **D1, D2** (float decay — determinism/replay risk). A plain
**GO** (no flag) is also REJECTED: L2 changes behavior-driving state, so it must be
gated. **REJECT** the whole phase only if integer-deterministic decay proves
infeasible — current evidence (dormant integer `decay_rate`, integer relation
fields, existing arithmetic-only macro path) shows it is feasible.

## F. Locked spec reference

The selected configuration is frozen at design level in
`p11b_social_memory_l2.md` → **"L2 Specification (locked)"**:
- **S1** pipeline order (decay → bias → existing scoring; fixed iteration order),
- **S2** D3 integer decay formula `step = (Q·R_NUM + R_DEN−1)//R_DEN`, `Q' =
  max(0, Q−step)` (float-free; the `≥0.20` gate becomes integer `I ≥ 20`),
- **S3** `MAX_BIAS = 0.15` (`W_AFF=0.6`, `W_FEAR=0.4`) bounding the relation steer,
- **S4** golden strategy (off = five fixed, on = +1 `GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA`),
- **S5** off/on Replay test plan (design only).

These lock the scores above: S2 is why D3 sits at Low determinism/replay risk, and
S3's bound is why Channel B cannot dominate the structural signals.
