# P9 — Persistent History (Release Notes)

P9 makes the P8 "history experience" **persist and become re-visitable across
sessions**, and adds two read-only ways to look back on a finished world (who
left a legacy, and what endured). The organising idea is **"the recipe IS the
save"**: a finished world is reproduced byte-for-byte from a small `Recipe`
(`engine_version`, `seed`, `max_year`, `mode`, `inputs`), because the engine is
deterministic from seed + inputs. No world snapshot is the source of truth.

Branch: `design/p6-salience` · HEAD `7bc35bd` · full suite **300 passed**.

| Sub-issue | Module(s) | One line |
|---|---|---|
| P9-1 Save/Load | `persistence/{version,schema,save,load}.py` | The recipe is the canonical save |
| P9-2 Transcript Export | `persistence/export.py` | Shareable txt/md/json artifact with verifiable hashes |
| P9-3 Replay | `persistence/{replay,record}.py` + play CLI | Re-run a recipe, regenerate the transcript |
| P9-4 Lineage Viewer | `reporting/lineage.py` | Who left what — the reincarnation chain |
| P9-5 Heritage Explorer | `reporting/heritage_explorer.py` | What endured — the world's legacies |

---

## P9-1 Save/Load

**User value.** A finished run can be saved as a tiny, human-readable JSON file
and reloaded later into the exact same world — no large snapshot, no drift.

**Technical overview.** New isolated `persistence/` package. `Recipe` (pydantic
v2, `extra="forbid"`, closed `mode` enum `auto|human|script`, an
`auto ⇒ empty inputs` validator). `build_recipe` stamps the current
`ENGINE_VERSION`; `save_recipe` writes byte-deterministic sorted-key JSON;
`load_recipe`/`replay_recipe` gate then re-run `run_human_world(seed,
scripted_reader(inputs), null_writer)`. Two refusal gates, never a silent
fallback: `engine_version` mismatch → `EngineVersionMismatch`; non-default
`max_year` → `UnsupportedRecipe` (the P8 engine does not expose `max_year`, so
reconstructing at the wrong horizon is refused — determinism over convenience).

**Determinism impact.** Establishes the contract that a Recipe + matching
`ENGINE_VERSION` reproduces a world exactly. `ENGINE_VERSION = "0.1.0-p8-mvp"`
is pinned to the P8 baseline; it must be bumped whenever worldgen / P6 / execution
/ RNG / play-loop output changes.

**seed42 protection.** The seed42 EOF recipe reconstructs the golden world
`e62d8f2c…`; encoded as a permanent regression test.

## P9-2 Transcript Export

**User value.** Export a run as a shareable document in three formats — `txt`
(read), `md` (share, with the recipe embedded for replay), `json` (machine).
Each artifact is self-verifying.

**Technical overview.** `export_transcript(recipe, *, fmt) → (artifact,
ExportMetadata)` and `write_export(recipe, path, fmt=None)` (format inferred from
`.txt`/`.md`/`.json`). `ExportMetadata` carries `seed`, `engine_version`, and the
full sha256 `recipe_hash` / `transcript_hash` / `world_hash`. The transcript is
**stored but non-authoritative**: the embedded recipe + `transcript_hash` let a
reader re-validate by regenerating and comparing. Play CLI gained `--export FILE`,
composable with `--seed`/`--replay`/`--save`.

**Determinism impact.** All three renderers are byte-deterministic. Export reads
only; it adds no new state and cannot change a world.

**seed42 protection.** seed42 `world_hash` = `e62d8f2c…`, `transcript_hash` =
`98bea862…`; existing CLI stdout stays byte-identical.

## P9-3 Replay

**User value.** Re-run any saved recipe and watch the same history unfold; the
transcript you see is regenerated live, guaranteed identical to the original.

**Technical overview.** `replay(recipe, *, writer)`,
`replay_transcript(recipe) → (world, transcript)`, `replay_file(path, *, writer)`,
plus `recording_reader(inner) → (reader, captured_inputs)` to capture live human
input during play. Failures are a **closed taxonomy** that refuse rather than
diverge: `EngineVersionMismatch` / `UnsupportedRecipe` / `InvalidRecipe`. Play
CLI additively extended: `--save FILE` records a run into a recipe; `--replay
FILE` regenerates; `--seed` ⊕ `--replay` are mutually exclusive. Existing flags
are byte-identical.

**Determinism impact.** Locks the rule: **the transcript is regenerated, never
stored as canon** (P9-2's stored copy is only a cache). Replay is the executable
proof that a recipe round-trips.

**seed42 protection.** Extends the permanent regression to the prose layer:
seed42 EOF replay reproduces the golden world `e62d8f2c…` **and** the golden
transcript `98bea862…`.

## P9-4 Lineage Viewer

**User value.** A player-facing Markdown view of the whole reincarnation chain —
each past self, what they were born into, and what they left behind, ending on
"You are here." It answers *who left a legacy*.

**Technical overview.** `reporting/lineage.py`:
`lineage_view(world, *, order="chronological"|"impact"|"generation") → str`. New
sibling module; P7 `experience.py` and `reporting/__init__.py` untouched. Reuses
the read-only `_data` / `labels` helpers. Every order contains every life and is
deterministic (ties break on the life ordinal — no set/dict iteration leaks).
Unknown order → `ValueError`. No internal id reaches output (lives by ordinal +
title, heritage by proper name) — the P8 lesson, regex-guarded.

**Determinism impact.** None on the engine: a pure read-only projection. Asserted
read-only via `model_dump_json` before/after.

**seed42 protection.** Reads the golden world only; its hash is unchanged.

## P9-5 Heritage Explorer

**User value.** A browsable catalogue of *what endured* — every legacy by
significance, with selectable sort and grouping, and a "still shaping the world"
mark for legacies whose domain still runs in the world's final dominant theme.

**Technical overview.** `reporting/heritage_explorer.py`:
`heritage_explorer(world, *, sort="score", group_by=None) → str`. `sort` =
`score` (default) / `longevity` / `reach` / `origin`; all ties break on the
source seed. `group_by` = `None` (flat) / `type` / `founder` (faction grouping
deferred — heritage↔faction linkage is sparse). "still shaping the world" is
defined as `SEED_DOMAIN_TO_THEME[domain] == world.theme.dominant` — *present*
influence, deliberately independent of `longevity` (*historical* persistence).
Reuses the read-only `heritage_rows` projection; no internal ids (heritage by
name, founders by "Life N"). Unknown `sort`/`group_by` → `ValueError`.

**Determinism impact.** None on the engine: a pure read-only projection, asserted
read-only. (Note: for seed42 all four sorts emit identical bytes because that
world's heritages rank monotonically across the metrics; the sort logic itself is
verified against re-sorted `heritage_rows`.)

**seed42 protection.** Reads the golden world only; its hash is unchanged.

---

## Achievements

- **Recipe canonicalised** as the save format (seed + inputs reproduce the world).
- **Replay determinism established** — transcript regenerated, never stored as canon.
- **Export** in txt/md/json with verifiable metadata hashes.
- **Lineage visualisation** — who left a legacy, across the reincarnation chain.
- **Heritage visualisation** — what endured, with a present-influence marker.
- **seed42 golden permanently guarded** — world `e62d8f2c…` and transcript
  `98bea862…`, across direct generation **and** recipe replay.

## Invariants held across P9

- `pytest` = **300 passed**.
- seed42 world hash = `e62d8f2cd24d2c72` (direct **and** replay).
- seed42 transcript hash = `98bea8622c686d8e`.
- All reporting views are read-only (`model_dump_json` unchanged before/after).
- No internal id leaks to player output (regex-guarded) — the P8 lesson.
- **P6 / P7 / P8 untouched**; `run_human_world` behaviour unchanged.
