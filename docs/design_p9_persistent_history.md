# P9 Persistent History — Design (For Review)

Status: **Design only. No implementation. Awaiting review to fix the
implementation order.** No code, model, or formatter changes accompany this
document.

P6 generates history. P7 interprets it. P8 lets a player live inside the
reincarnating loop and answer history's call (tagged `v0.1.0-p8-mvp`, the point
Chronicle Forge became a history-experience game). **P9 makes that history
persist and re-visitable across sessions** — so a run is not lost when the
process exits, and the player can return to the world they shaped, re-read the
life they lived, replay it, and explore the lineage and heritage it left behind.

## Guiding principle

```
A history you cannot return to is not yet a history.
The world is deterministic; revisiting it is therefore loss-free.
```

P9 turns the engine's determinism (a hard project requirement, R3) from an
internal invariant into a player-facing feature: because the same seed and the
same player inputs reconstruct a byte-identical world, *the recipe is the save*.

---

## 1. Designing backward from the player's experience

The brief asks us to reason from "what does the player want to revisit?" — not
from "what is technically easy to dump." Three questions drive the whole design.

### What does the player want to look back on?

After living several reincarnations, the player has three distinct kinds of
memory they will want to return to:

1. **"The story I lived."** The prose of the run — births, the moments history
   called, the deaths, the legacies. This is *reading*, and it already exists as
   the P8 transcript stream and the P7 renderers. → **Transcript Export (P9-2).**
2. **"The world I shaped."** The structural through-line — who I have been across
   lives, what each past self planted, what outlived everyone. This is *browsing
   a structure*, not reading prose. → **Lineage Viewer (P9-4)** and **Heritage
   Explorer (P9-5).**
3. **"That run, again."** The wish to re-experience a particular world unfold,
   or to pick it back up. This is *re-running*, and it is only meaningful if it
   is faithful. → **Save/Load (P9-1)** and **Replay (P9-3).**

### What constitutes "revisiting history"?

Two different acts, and the design must keep them separate:

- **Re-reading** (P9-2/4/5): a read-only projection of a finished world into
  prose or a browsable view. No re-simulation; pure rendering. Cheap, safe,
  order-deterministic.
- **Re-running** (P9-1/3): reconstructing the world itself, then optionally
  watching it advance again. This is where determinism is load-bearing.

### What should a save actually hold?

This is the pivotal decision. There are two candidate representations:

| | **(A) Recipe** | **(B) Snapshot** |
|---|---|---|
| Contents | `seed`, `max_year`, engine version, ordered player inputs | full `World.model_dump_json()` |
| Size | a few hundred bytes | large (entire world graph) |
| Restore | re-run the deterministic engine → identical world | deserialize directly, no compute |
| Fidelity | exact **iff** engine version matches | exact, version-independent for *that* state |
| Enables | replay (watch it unfold), branching (future) | instant resume / inspection |

**Recommendation (decision for review): the recipe is canonical; the snapshot is
an optional derived cache.** Rationale:

- The engine is already proven byte-deterministic from `seed` + inputs (the P8
  seed42 golden identity `e62d8f2c…`, and the human-acting determinism tests).
  The recipe is therefore *sufficient* to reconstruct any run exactly.
- The recipe is what Replay (P9-3) needs anyway — replay **is** the recipe
  executed. One representation serves both Save and Replay.
- It is tiny, diffable, and free of internal ids and PII (just a seed and a list
  of small integers).
- The snapshot remains valuable for two things the recipe cannot do cheaply:
  (i) instant resume without re-simulation, (ii) opening a world whose engine
  version no longer matches the recipe. So a save file *may* carry an optional
  snapshot, but correctness is defined by the recipe.

> **Fact vs. assumption.** *Fact:* `World` and all sub-models are pydantic, so
> `model_dump_json`/`model_validate_json` give a lossless snapshot today, with no
> model change. *Fact:* a full run is determined by `seed` + `max_year` +
> player-input sequence (input at every gate ask, including "let it pass", since
> passing delegates to the auto-chooser and draws RNG, diverging the stream from
> acting). *Assumption:* CPython's Mersenne Twister sequence is stable across the
> Python versions we target — true for the documented `random` methods, but it is
> the one portability assumption replay rests on, hence the version gate below.

---

## 2. What a save file holds (canonical schema, proposed)

A new, isolated persistence schema — **separate from `models.py`** so the
protected world model is never touched:

```
SaveFile
  save_schema_version : str     # this file format's version
  engine_version      : str     # the simulator version the recipe was recorded under
  created_for         : "human" | "auto" | "script"
  recipe:
    seed              : int
    max_year          : int
    inputs            : list[int]   # one entry per gate ask, in order (incl. 0 = let pass)
  snapshot            : optional   # World.model_dump_json(), a derived cache only
  meta                : optional   # ending_class, life_count, transcript_sha — for listing, never authoritative
```

- **`recipe` is authoritative.** Load = `generate_world(seed, max_year)` then
  drive `run_human_world` with a script chooser fed `inputs`.
- **`engine_version`** gates replay: a recipe recorded under an incompatible
  engine must be *refused* (or fall back to `snapshot` if present), never
  silently replayed into a divergent world.
- **`inputs`** are captured during a live play by recording each resolved gate
  ask. This is volatile play-session state written at save time; **no field is
  added to `World`.**

---

## 3. Architecture

Mirror P8's discipline: a **new, isolated package**, read-only over the world,
with P6/P7/execution/models all untouched.

- **`persistence/` (new):**
  - `schema.py` — the `SaveFile` pydantic model (above). New models, not in
    `models.py`.
  - `save.py` — `world + recipe → SaveFile`, write to disk (JSON).
  - `load.py` — `SaveFile → World`: by recipe (re-run) or by snapshot (validate).
- **`play/` (extend, not change):** the session already runs on an injected
  writer and a script chooser. Add a thin **input recorder** wrapper around the
  chooser so a live human play yields its `inputs` list, and a transcript-capture
  writer (a `StringIO` sink). The existing `gate`/`render`/`human`/`session`
  logic is unchanged.
- **`reporting/` or `play/views/` (new read-only renderers):** `lineage_view`
  and `heritage_explorer`, built like the P7 renderers — reusing
  `reporting/_data` and `reporting/labels`, emitting player-facing Markdown,
  humanized labels (the P8 "no internal id" lesson), deterministic ordering.
- **Untouched (protected):** `opportunity.py` (P6), the execution mutation
  funnel, `reporting/experience.py` (P7), `heritage.py` scoring, the auto paths,
  `models.py`, and the seed42 golden assets.

CLI surface (extends `play/__main__.py`, still a thin wrapper; no logic):

```
python -m chronicle_forge.play --seed N            # play, as today
python -m chronicle_forge.play --seed N --save FILE # play, then write a SaveFile
python -m chronicle_forge.play --load FILE          # reconstruct & continue/replay
python -m chronicle_forge.play --load FILE --replay # re-emit the transcript
python -m chronicle_forge.play --load FILE --export transcript.md
python -m chronicle_forge.play --load FILE --lineage   # lineage viewer
python -m chronicle_forge.play --load FILE --heritage  # heritage explorer
```

---

## 4. Trade-offs

- **Recipe vs. snapshot as canonical.** Recipe: tiny, replay-ready, but
  version-fragile. Snapshot: robust to engine drift, but large and replay-inert.
  → carry both, define correctness by the recipe, keep the snapshot as a cache
  and a version-mismatch fallback.
- **Re-simulate on load vs. instant restore.** Re-simulating a recipe is O(run)
  but loss-free and proves determinism on every load; snapshot restore is O(1)
  but cannot replay. → default to re-simulation; offer snapshot fast-path.
- **Viewers in `reporting/` vs. `play/`.** `reporting/` already owns read-only
  projections (P7); placing lineage/heritage there reuses `_data`/`labels`.
  `play/` keeps everything player-facing in one package. → recommend
  `reporting/` for the pure renderers, surfaced through the `play` CLI, matching
  the existing P7 split.
- **Text/Markdown vs. structured/graph output.** A graph (e.g. causal_dot)
  exists, but P7 established that the player wants *readable* output, not a dev
  table. → Markdown "読み物" first; graph export is a possible later add-on.

---

## 5. Risks

- **Recipe portability (the one real determinism risk).** A future engine change
  or a Python `random` change would make an old recipe replay into a *different*
  world. → mandatory `engine_version` gate: refuse or snapshot-fallback on
  mismatch; never silently diverge. A seed42 EOF recipe whose reconstruction
  must equal the golden `e62d8f2c…` becomes a permanent regression guard.
- **Accidental world mutation in viewers.** A read-only projection that sorts or
  indexes the world must not mutate it, and must order deterministically (no
  set/dict iteration leak — the established discipline). → `model_dump()`
  before/after equality assertions, as in the P8 render tests.
- **Internal id leakage.** The P8 lesson (`legacy:seed-0005` must never reach the
  player). Lineage/heritage views must humanize every id via `labels`.
- **Scope creep into UI / branching.** P9 is persistence + revisiting, not a save
  manager UI and not what-if branching. Both are explicitly non-goals here.
- **Save-file hygiene.** Saves must contain only a seed, ints, and derived prose
  — no absolute paths, no secrets, no PII. (Consistent with the repo security
  policy; trivially satisfied by the recipe schema.)

---

## 6. Issue breakdown

Five issues (the brief's P9-1…P9-5). The sixth candidate theme, **world
inspector**, is intentionally *deferred* — see the note after the table. Each
issue states 目的 / 非目標 / data-model change / determinism impact / seed42
impact / acceptance criteria.

### P9-1 Save/Load

- **目的 (Purpose).** Persist a run so it survives the session and can be
  reconstructed exactly later. Canonical save = the **recipe** (`seed`,
  `max_year`, `engine_version`, ordered gate inputs); an optional **snapshot**
  (`World.model_dump_json()`) is a derived cache for instant restore. Provide
  `--save FILE` (after a play) and `--load FILE` (reconstruct).
- **非目標 (Non-goals).** Not per-season autosave; not a save-slot/manager UI; not
  cloud sync; not mid-juncture rewind/save-scum (that is replay/branching,
  future); not a change to the `World` model.
- **Data-model change.** **None to `World`.** New, isolated `SaveFile` schema in a
  new `persistence/` package. The input list is captured in volatile
  play-session state (a recorder around the chooser), written at save time — no
  field added to any protected model.
- **Determinism impact.** None on the engine. Load-by-recipe re-runs the
  *unchanged* deterministic engine and must yield an identical world; load-by-
  snapshot deserializes directly. Save/load is pure read/write.
- **seed42 impact.** **Zero.** No engine/model change. The seed42 EOF recipe is
  `(42, max_year, [])`; its reconstruction must equal the golden world
  (`e62d8f2c…`), which *adds* a regression guard rather than risking the asset.
- **受け入れ条件 (Acceptance).**
  1. Round-trip: `save → load → save` produces an identical SaveFile.
  2. Recipe-load world `== ` live-run world (`model_dump_json` equal) for seeds
     42/123/999, in both EOF and acting variants.
  3. Snapshot-load world `==` recipe-load world.
  4. `engine_version` / `save_schema_version` present and validated on load.
  5. seed42 golden assets unchanged; full suite green; no P6/P7/model edit.

### P9-2 Transcript Export

- **目的.** Export the human-readable play transcript — the P8 stdout stream
  (births, junctures, the P7 death→chronicle→timeline→legacy chain, rebirths,
  former-self recognitions) — to a file (plain text and/or Markdown) so the
  player can re-read "the story I lived" outside the session.
- **非目標.** Not a new narrative generator (reuses `render` + P7 verbatim); not
  styling/themes/HTML; not the structured data save (that is P9-1); no new prose
  logic.
- **Data-model change.** **None.** The session already writes through an injected
  writer; export captures that stream to a `StringIO`/file sink. New thin
  capture helper; no model touch.
- **Determinism impact.** None. Pure capture of already-deterministic output;
  same seed + inputs → byte-identical transcript (already observed: CLI auto
  transcript sha `98bea862…`, stable across repeats).
- **seed42 impact.** **Zero.** Reads the same writer stream; no engine touch.
- **受け入れ条件.**
  1. Exported bytes `==` the writer stream for the same run.
  2. Deterministic across repeats (identical sha on re-export).
  3. Markdown variant is well-formed and covers the full chain (birth → death →
     legacy → rebirth → former-self).
  4. seed42 golden unchanged; suite green.

### P9-3 Replay

- **目的.** Re-experience a saved run deterministically from its recipe — re-emit
  the transcript as the world unfolds again (optionally paced), turning the
  engine's determinism into a feature. Replay **is** the recipe executed.
- **非目標.** Not branching/what-if (altering a past choice → future); not a
  frame-scrubbing UI; not editing a recipe; not snapshot-only "resume" (that is
  P9-1 load).
- **Data-model change.** **None.** Consumes P9-1's recipe. The existing
  `--script` CLI path already executes a recipe; P9-3 formalizes "replay a saved
  SaveFile" plus optional pacing/`--replay`.
- **Determinism impact.** This *surfaces* determinism. Replaying a recipe must
  reconstruct a byte-identical world **and** transcript. The single risk —
  `engine_version` mismatch — must be **detected and refused** (or snapshot-
  fallback), never silently diverged.
- **seed42 impact.** **Zero** engine change. seed42 EOF recipe replay `==` the
  golden world and the golden transcript; an added regression guard.
- **受け入れ条件.**
  1. Replay(saved recipe) world `==` original world for seeds 42/123/999 (EOF and
     acting).
  2. Replay transcript `==` original transcript, byte-identical.
  3. A version-mismatched recipe is detected and refused (or falls back to
     snapshot), with a clear message — never a silent divergent run.
  4. No model/engine change; seed42 golden unchanged; suite green.

### P9-4 Lineage Viewer

- **目的.** Show the chain of reincarnations as a lineage: each life in birth
  order with its talent, era, what it planted, what outlived it, and how later
  lives inherited earlier selves' work. Answers "who have I been, and how did my
  past selves shape this world?" — the structural counterpart to P7's per-life
  prose.
- **非目標.** Not a new metric or score; not a graph-rendering engine (Markdown
  "読み物" first); not world mutation; no new aggregation beyond existing data.
- **Data-model change.** **None.** Fully derivable from `world.lives`,
  `seeds.planted_by_life_id`, `heritage.seed_id`, and `causal_nodes`. New
  read-only renderer reusing `reporting/_data` + `labels`.
- **Determinism impact.** None. Read-only projection; **deterministic ordering
  required** (birth year, then life id) with no set/dict iteration dependence.
- **seed42 impact.** **Zero.** Read-only; no engine/model touch.
- **受け入れ条件.**
  1. Lists every life in birth order with talent / era / founded heritage /
     inheritance links.
  2. Output deterministic across repeats (stable bytes).
  3. Second-person voice consistent with P7; **no internal id leaks** (all
     humanized via `labels`).
  4. World unchanged by rendering (`model_dump()` equal before/after); seed42
     golden unchanged; suite green.

### P9-5 Heritage Explorer

- **目的.** Browse the world's heritages as a catalog: each heritage's founding
  life, type, reach / longevity / score, descendant events, and current
  world-theme influence. Answers "what has outlived everyone, and where did it
  come from?" — the world-level complement to P7-4's life-level "What outlived
  you?".
- **非目標.** Not re-scoring heritage (`heritage.py` untouched); not a new
  promotion rule; not interactive filtering UI; not world mutation.
- **Data-model change.** **None.** Derived from `world.heritage`, `seeds`,
  `causal_nodes`, and `theme`. Read-only renderer reusing the existing
  `heritage_rows` data path + `labels`.
- **Determinism impact.** None. Read-only; deterministic ordering (heritage score
  desc, then id).
- **seed42 impact.** **Zero.** Read-only.
- **受け入れ条件.**
  1. Every heritage shown with founder life (via `seed_id → planted_by_life_id`),
     type, reach / longevity / score, and theme tilt.
  2. Numbers consistent with `heritage_table` / `legacy_view` for the same world.
  3. Deterministic across repeats; humanized labels (no `seed-…` leak).
  4. World unchanged by rendering; seed42 golden unchanged; suite green.

#### Deferred: World Inspector (6th candidate theme)

Not made a P9 issue. *Reason:* its audience is **developer/debug** (raw world
query/dump), not the player revisiting history, and a raw dump risks exposing
internal ids — counter to the P7/P8 "no internal id" discipline. Recommendation:
either fold a minimal read-only `--inspect` debug path into P9-1's load (gated,
dev-only, JSON to stderr like the P8 `--debug` trace), or schedule it as a
separate **P9-6 (dev tooling)** outside the player-facing arc. Decision deferred
to review.

---

## 7. Recommended implementation order (for review)

A recommendation, not a lock — the brief says the order is decided after review.

1. **P9-1 Save/Load** — the substrate; defines the recipe that Replay needs.
2. **P9-3 Replay** — directly consumes the recipe; together with P9-1 it nails
   down the determinism contract and its version gate early.
3. **P9-2 Transcript Export** — independent and small; can slot in at any point
   (a reasonable parallel/first quick win if preferred).
4. **P9-4 Lineage Viewer** — read-only view; depends on nothing but a loaded
   world.
5. **P9-5 Heritage Explorer** — read-only view; same substrate as P9-4.

Rationale: 1→3 establishes "the recipe is the save" and proves replay fidelity
before any viewer work; 2/4/5 are independent read-only features that can follow
in any order. If a fast morale win is wanted first, P9-2 is the cheapest and
touches nothing.

## 8. Verification plan (applies to every issue)

- **seed42 byte-identity** preserved (`e62d8f2c…`) and the full suite stays
  green — the standing gate from P6 onward.
- **Determinism, doubled:** recipe-load and replay both reconstruct
  byte-identical worlds and transcripts for seeds 42/123/999 (EOF and acting).
- **Read-only discipline:** viewers assert `model_dump()` equality before/after;
  no set/dict ordering leak; humanized labels (no internal id in any output).
- **Isolation:** `models.py`, `opportunity.py` (P6), `reporting/experience.py`
  (P7), `heritage.py`, the execution funnel, and the auto paths show **zero
  diff**; all new code lives in `persistence/` and new read-only renderers.
- **Restorability from the tag:** every P9 increment must remain reconstructible
  from `v0.1.0-p8-mvp`; the MVP is never regressed.
