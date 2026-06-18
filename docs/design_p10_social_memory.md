# P10 Social Memory — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** Second P10 issue (after Observatory). Direction per
`docs/research/p10_candidates.md`.

## Purpose

Show, and eventually let the world act on, **the social trace a soul leaves
across its lives** — "Lynnon still remembers you fondly from when you were the
Statesman." Each life is the player reincarnated; people who met a past self
carry that bond forward.

## Grounding (facts read from the current engine)

- **The soul is already a stable cross-life anchor.** Memories are attributed to
  `life.player_id` (the `Player.id`), *not* to a per-life id — see
  `activity.py` and `powers.py` calling
  `form_memory(world, subject_id=npc, actor_id=life.player_id, …)`. So
  `world.memories` and `NPC.relations[player_id]` already accumulate **toward the
  soul across every life**, and survive the time-skip while the NPC lives.
- **`player_id` is an internal id** (`"player-0000"`) — it must never reach player
  output (the P8 lesson). NPC ids (`npc-XXXX`) likewise.
- **Memory carries a year** (`Memory.timestamp`); a memory at year *Y* maps to the
  life that was alive then (`life.birth_year ≤ Y ≤ life.death_year or
  current_year`), giving id-free "from when you were Life N" attribution.
- seed42 (`simulate_world(42, "opportunity")`) is non-trivial: 5 memories toward
  the soul; Tier-S `Torwen` and `Lynnon` hold relations toward it (from Life 2 and
  Life 4). A real bond to surface.

## Two layers (separated deliberately)

| Layer | What | Engine touch | Determinism | Flag |
|---|---|---|---|---|
| **L1 — Social Memory View (this MVP)** | read-only player surface of existing soul-bonds | **none** | **zero impact** | **none needed** |
| L2 — Cross-life influence (deferred) | memory decay over the skip + relations steer NPC behavior across lives | `macro`/`npc`/`memory` | changes world hash | **required (off by default)** |

The soul-anchored data already exists, so **L1 needs no engine change** and is the
safe MVP — the same read-only pattern as Observatory/Lineage. L2 is the
determinism-sensitive part; it is fully designed here (so the safety story is
concrete) but **deferred to a follow-on** behind a flag.

## MVP decision — L1: the Social Memory View

`reporting/social_memory.py` (new, additive sibling). Public API:

```python
def social_memory_view(world: World) -> str                 # player-facing Markdown
def social_memory_bonds(world: World) -> list[SocialBond]   # structured 3D seam
```

`SocialBond` is an id-free `NamedTuple` — `(npc_name, npc_tier, life_ordinal,
affinity, sentiment, reason)`. One bond per NPC that holds a relation toward the
soul, attributed to the past life the memory traces to (via `timestamp`).

**Included (and why):** surfacing the soul-bonds is the whole player value of
Social Memory, and it is **zero-risk** — read-only, no flag, no golden impact, and
it reuses data the engine already produces. **Excluded from MVP:** all of L2
(decay, behavioral influence) — see below. NPC *codex*-style dumps (`views.py`)
are not reused (dev-facing, id-leaky).

## L2 design (deferred) — how cross-life influence stays safe

When eventually built, L2 must satisfy every constraint below. Recorded now so the
boundary is fixed:

- **Save = Recipe preserved.** Add `social_memory: bool = False` to `Recipe`
  (`extra="forbid"` still holds — a *missing* known field falls back to the
  default, so **every existing recipe stays valid and replays identically**). The
  flag rides in the canonical save, so replay is deterministic.
- **Full disable / complete no-op when off.** The run entrypoints gain
  `social_memory: bool = False` (`simulate_world`, `run_human_world`); with it
  `False`, **not a single engine branch is taken** — output is byte-identical to
  today. This is the flag-gate guarantee.
- **Golden Baseline impact assessment.**
  - *Flag off (default):* seed42 world `e62d8f2c…` and transcript `98bea862…`
    **unchanged** — the primary, asserted protection.
  - *Flag on:* a *new* world; a **separate** frozen golden is minted for the
    on-path (`seed42 + social_memory=on`). The default golden is never touched.
  - `ENGINE_VERSION` is **not** bumped: the change is purely additive (off-path
    identical, on-path gated by a recipe field), so all existing recipes still
    reproduce. (Only the recipe *serialization* gains a defaulted field; the world
    and transcript goldens are unaffected.)
- **P6–P10 existing behavior unchanged** — L2 never edits P6 firing, P7 text, P8
  play loop, P9 persistence semantics, or P10 Observatory; it only adds gated
  branches in `macro`/`npc`/`memory`.

## Determinism requirements (MVP, asserted by the failing tests)

- **Same World ⇒ identical bytes** for `social_memory_view` and
  `social_memory_bonds` (no set/dict iteration leaks; bonds sorted
  deterministically, e.g. by `-affinity`, then npc name).
- **Read-only ⇒ golden preserved.** `world.model_dump_json()` is byte-identical
  before/after; thus the seed42 world stays `e62d8f2c…` by construction.
- **seed42 frozen-hash test** for the view (`GOLDEN_SOCIAL_MEMORY_SHA`, filled at
  GREEN) — the permanent regression guard.
- **Player display ⟂ internal ids (complete separation).** Output and every
  `SocialBond` string field never match `\b(seed|life|npc|node|loc|fac|her|player)-\d`
  and never contain `player-` or `legacy:`. People are shown by name, past selves
  by "Life N".

## 3D client data boundary

`social_memory_bonds(world) -> list[SocialBond]` **is** the 3D seam: a future
low-poly client renders each bond as a character in the world who reacts to the
returned `sentiment`/`affinity` toward a past self (`life_ordinal`), reading
**structured id-free fields, never the prose**. `social_memory_view` is merely the
text renderer over the same list — exactly the Observatory `Section` pattern. The
boundary rule: the structured layer exposes only humanised, id-free fields, so no
renderer (text now, 3D later) can leak an internal id.

## Architecture / placement

- **`reporting/social_memory.py` (new, additive):** reads `world.memories`,
  `world.npcs` (`.relations[player_id]`), `world.lives` (for `timestamp`→Life
  attribution), and `labels`/`_data` for humanisation. Sibling to
  `observatory.py`/`lineage.py`.
- **Untouched:** `models.py`, `memory.py`, `macro.py`, `npc.py` (L2 only),
  `persistence/` (no Recipe change in the MVP), P6/P7/P8/P9/P10-Observatory,
  `run_human_world`, the seed42 golden.

## Test plan (failing — `tests/test_social_memory.py`, RED until implemented)

Over `simulate_world(42, mode="opportunity")` unless noted:

- `test_social_memory_view_is_markdown`, `_is_read_only`, `_is_deterministic`,
  `_no_internal_ids` (incl. no `player-`).
- `test_social_memory_view_names_every_remembering_npc` — every NPC that holds a
  relation toward `world.player.id` appears by name.
- `test_social_memory_bonds_one_per_remembering_npc` — the bond NPC-name set
  equals the soul-remembering NPC set.
- `test_social_memory_bonds_attribute_to_valid_life` — each `life_ordinal` ∈
  `1..len(lives)`.
- `test_social_memory_bonds_are_id_free` — no internal id in any bond string field.
- `test_social_memory_bonds_empty_on_fresh_world` — `social_memory_bonds(
  generate_world(42))` is `[]` (no lives lived yet); the view still renders.
- `test_social_memory_view_seed42_hash_is_frozen` — pinned golden (filled at GREEN).

## Implementation plan (after approval — small commits)

1. `reporting/social_memory.py`: `social_memory_bonds` (gather soul relations →
   `timestamp`→Life attribution → humanise → deterministic sort) → id scrub →
   `social_memory_view` renderer → freeze seed42 hash.
2. (Separate, flag-gated issue) L2 cross-life influence: Recipe `social_memory`
   field, gated `macro`/`npc`/`memory` branches, on-path golden.

## Constraints honored

- MVP is a read-only projection; World unchanged (asserted) ⇒ seed42 golden intact.
- No internal ids in output or structured fields (the P8 lesson; regex-guarded).
- P6/P7/P8/P9/P10-Observatory, `run_human_world`, the seed42 golden untouched; no
  Recipe change in the MVP (L2's additive flag is designed but deferred).
