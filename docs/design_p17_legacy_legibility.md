# P17 — Legacy Legibility (design + RED)

Status: **Design / RED only. No implementation, no commit.** First phase of the
game-experience track (see [`game_experience_roadmap.md`](game_experience_roadmap.md)).
It makes a finished world's **Fingerprint** ([`fingerprint_design.md`](fingerprint_design.md))
legible so the player *notices* — **"ah, that was me, long ago"** — using **only data
the engine already produces**. Pure Read-Model + Application-Layer addition; engine,
persistence, Opportunity algorithm, and all existing goldens are untouched.

Builds on the P10–P14 lens contract (immutable, id-free view records; deterministic;
read-only; pure Markdown renderer) — this phase adds one more lens plus a small app
seam, and **moves no existing golden**.

---

## 1. Responsibility (責務)

Legacy Legibility owns exactly one thing:

> **Project a finished `World` into an id-free, deterministic read-model that surfaces
> the player's own enduring marks — attributed to the specific life that made each —
> arranged so the player *recognizes* them, and flag the rare subset worth a
> Recognition Moment.**

It does **not**:
- compute new history, scores, or truth (every field is read off existing records);
- tell the player "you did this" in words (it surfaces breadcrumbs, §4/§6);
- touch the live play transcript's default (auto) path, the Opportunity algorithm, or
  the existing `ChronicleView` / lens goldens (§7).

It is the **noun surface** for the Discovery Loop's verbs: P18 Investigation decomposes
what P17 makes legible; P19/P21 build on it.

---

## 2. The "あ、これ昔の自分だ" 導線 (how recognition arises)

The player is the world's one reincarnating soul, so **every** heritage founded by a
life is, literally, their own hand. Recognition is therefore not "is this mine?" (all
of it is) but **"which *earlier life of mine* left this, and can I feel it?"** The line
of realization is built from three facts the engine already records:

1. **Attribution exists.** Each enduring mark carries its **founding life ordinal**
   (`heritage_rows.origin_life` = "Life N"; `CausalSeed.planted_by_life_id`). The view
   presents *"begun by the third to live here,"* not an internal id.
2. **Consequence is visible.** The mark's **reach / derived_events / longevity** show
   how far a single past act rippled — the "blast radius" that makes a mark feel
   *consequential enough to remember.*
3. **Presence persists.** The **"still shaping the world"** flag (a mark whose domain is
   the world's final dominant theme) says *your hand is still on the world right now.*

The player supplies the last step themselves: they *played* Life 3; seeing *"the Aurelian
School — begun by the third to live here — still shapes the world"* lets them connect the
breadcrumb to their own memory of that life. **We lay the trail; the player has the
recognition.** That is the whole design principle (气付かせる, not 答えを与える).

---

## 3. Read-Model / API surface

### 3.1 New lens module `chronicle_forge.reporting.legacy` (mirrors P12–P14)
- `SCHEMA_VERSION = "1"`
- `legacy_model(world) -> LegacyView` — the projection (pure, read-only).
- `legacy_json(world) -> str` — canonical JSON (the client contract + new golden basis).
- `legacy_markdown(view: LegacyView) -> str` — **pure** renderer (reads only the view).

`LegacyView` (pydantic, `frozen=True`, `extra="forbid"`, **id-free**) — the five
Fingerprint dimensions:

| Field | Type | Dimension | Source (existing) |
|---|---|---|---|
| `schema_version` | str | — | constant |
| `place` | str | — | `reporting._data.place(world)` |
| `span` | int | — | `world.current_year` |
| `shape` | list[`AxisWeight`] | **Shape** | `heritage_rows` domain → `SEED_DOMAIN_TO_THEME` axis, aggregated |
| `marks` | list[`LegacyMark`] | **Weight/Persistence/Hand** | `heritage_rows` (name/type/origin_life/reach/derived_events/longevity) + living flag |
| `reputation` | list[`ReputationNote`] | **Reputation** | `world.memories` grouped by `MemoryType` (id-free counts) |
| `recognitions` | list[`RecognitionCue`] | the rare subset | pure function over `marks` (§4) |

Record shapes (all id-free):
- `AxisWeight`: `axis: str`, `weight: int`, `living: bool` (axis == `world.theme.dominant`).
- `LegacyMark`: `name: str`, `kind: str` (`HeritageType`), `founder_life: int` (ordinal),
  `reach: int`, `derived_events: int`, `longevity: int`, `living: bool`.
- `ReputationNote`: `sentiment: str` (humanised `MemoryType`, e.g. "remembered with
  gratitude" / "remembered with fear"), `count: int`.
- `RecognitionCue`: `mark_name: str`, `founder_life: int`, `living: bool`, `hint: str`
  (evocative, never declarative — §6).

### 3.2 Application-Layer seam (separate from `ChronicleView` — golden-safe)
Add to `app/services.py`, **alongside** (never inside) `explore`:
- `legacy(recipe) -> LegacyView` — `replay_transcript(recipe)` → `legacy_model(world)`.
- `legacy_file(path) -> LegacyView` — `read_recipe(path)` → `legacy`.
- `legacy_json(recipe) -> str` — canonical JSON for the client.

> **Why a separate view, not a new `ChronicleView` field.** Adding a field to
> `ChronicleView` would change `chronicle_json` and break the frozen P15 chronicle
> golden (`aa4c67a416178e92`). P17 therefore ships an *independent* view with its **own**
> golden and leaves `ChronicleView` byte-identical. (Roadmap guardrail: "new views ship
> their own goldens; existing goldens never move.")

---

## 4. Recognition rule — a pure function of existing data

A `LegacyMark` becomes a `RecognitionCue` iff it satisfies **both**:

1. **Attributable** — its founding life ordinal resolves (`origin_life` parses to an
   int; unresolved founders never recognize), *and*
2. **Self-signalling** — at least one of:
   - **living** (`domain == world.theme.dominant`), or
   - **consequential**: `derived_events >= RECOGNITION_MIN_EVENTS`, or
   - **far-reaching**: `reach >= RECOGNITION_MIN_REACH`.

Thresholds are module constants (tuned at GREEN; kept local to this read-model, like
`opportunity.py`'s local constants — **no `config.py` change**). The rule is a **pure
function of the finished world**: same world → same cues (determinism), no RNG, clock,
or network. Rarity is intentional: a world with dozens of heritages yields only a few
cues, so Recognition stays *precious* rather than a checklist.

**No new Truth check (per field):** `shape` ← heritage domains (existing) mapped by the
existing `SEED_DOMAIN_TO_THEME` table; `marks` ← `heritage_rows` fields verbatim;
`reputation` ← counts over existing `world.memories`; `recognitions` ← a threshold over
`marks`. Nothing is persisted; nothing new is computed about the world. (RED asserts
this via the id-free + "no invented score" + determinism contracts, §8.)

---

## 5. Heritage / Discovery / Social Memory connection

- **Heritage** is the backbone: `heritage_rows` already carries name, type, founder,
  reach, derived_events, longevity — `marks` is a near-verbatim id-free projection, and
  `shape`/`recognitions` are aggregations over it.
- **Discovery** is the *causal* origin of many marks: a dungeon `Discovery` plants the
  `CausalSeed` (`discovery.py`) whose maturation produced the events counted in
  `derived_events`. The `DiscoveryType→domain` colouring (RELIC→Faith, TECH→Tech,
  SEAL→Military, LORE→Governance) already flows into the heritage domain, so it lands in
  `shape` for free.
- **Social Memory** supplies **Reputation**: `world.memories` (`MemoryType`) and NPC
  soul-relations are the emotional imprint. P17 reads them as **id-free sentiment
  counts** (`reputation`). The deeper "this NPC remembers *you*" in-play tag is P19; P17
  only needs the aggregate, so it stays engine-frozen and golden-safe.

---

## 6. Visualization rules for "自分の痕跡" (notice, don't tell)

1. **Attribute by ordinal, not identity claim.** Show *"begun by the Nth to live
   here,"* never *"YOU (life N) did this."* The player closes the loop.
2. **Lead with the living marks.** Order `marks` so *still-shaping* ones read first — the
   strongest "your hand is still here" signal — then by reach/derived_events. Ties break
   deterministically (e.g. `-derived_events, -reach, name`).
3. **Evocative hints, bounded set.** `RecognitionCue.hint` is a small closed vocabulary
   of *evocative* lines ("still shapes the world today", "its echoes outlived the one who
   began it", "far more came of it than anyone alive could see") — chosen by the
   satisfied self-signal, never spelling out authorship.
4. **Rarity over completeness.** Recognitions are thresholded (§4); the fingerprint view
   is complete, but the *Moments* are few.
5. **Id-free prose.** The Markdown, like every P10–P14 renderer, leaks no raw id
   (asserted in RED).

---

## 7. Recognition Moment design (surfaces) & golden safety

Two surfaces, both golden-safe by construction:

- **Primary — post-run (read-model).** `legacy_markdown` / `legacy_json` present the
  fingerprint and its Recognition cues when the player *explores* the finished world.
  This is where "あ、これ昔の自分だ" is designed to land, and it cannot affect any live
  transcript.
- **Secondary — in-play (human path only).** The existing once-per-run recognition
  (`play/session.py` + `render.recognizable_heritage`) can be re-presented using the
  same pure cue vocabulary. **Golden safety:** the frozen `replay-transcript` golden
  (`98bea862`) is the **auto/EOF** run, where the juncture gate never asks, so the
  recognition branch never executes and the auto transcript is byte-identical. Any
  human-path enrichment is therefore off the golden path; if a shared helper is used,
  the auto path must be verified byte-identical (RED pins the transcript-adjacent
  guarantee by leaving the play path untouched in P17 and deferring enrichment to a
  flag-gated follow-up).

> P17 scope is the **read-model + app seam only**; the in-play re-presentation is
> designed here but implemented (flag-gated, auto byte-identical) as a small GREEN
> follow-up so the risk to `98bea862` is zero.

---

## 8. RED test plan (`tests/test_legacy_legibility.py`)

Mirrors the P14 timeline RED harness exactly: top-level `from chronicle_forge.autoplay
import simulate_world`; `_world()` = `simulate_world(42, mode="opportunity")`; the new
module is imported **inside each test body** so a missing module fails **only** these
tests with a clean `ModuleNotFoundError` and does not perturb collection of the existing
439. Contracts pinned:

- **Structure:** `legacy_model` returns a `LegacyView` with `frozen=True`,
  `extra="forbid"`, `SCHEMA_VERSION == "1"`, and the seven top-level fields (§3.1);
  record types `AxisWeight` / `LegacyMark` / `ReputationNote` / `RecognitionCue` with the
  declared field names/types.
- **Attribution:** every `LegacyMark.founder_life` is an int ≥ 1; every `RecognitionCue`
  references a mark present in `marks` and its `founder_life` resolves.
- **Recognition rule:** every cue satisfies the §4 predicate (living or ≥ thresholds);
  `recognitions ⊆ marks`; cue set is a *subset* (rarity).
- **No invented score:** `legacy_json` contains none of
  `("importance", "legacy_score", "score", "rank", "rating")` — only engine facts.
- **Id-free negative contract:** entity-id / uuid / hex32 / hex40 regexes and
  `("source_seed", "location_id", "actors", "node_id", "_id\"")` never appear in
  `legacy_json` or `legacy_markdown`.
- **Determinism & read-only:** `legacy_json(_world()) == legacy_json(_world())`;
  `legacy_model` does not mutate the world (`model_dump_json` unchanged).
- **Renderer purity:** `legacy_markdown` reads only the view (view unchanged), is
  deterministic, starts with `# `, and is id-free.
- **New golden placeholder:** `GOLDEN_LEGACY_SHA` (filled at GREEN); the golden test
  stays RED via the in-body import.
- **Boundary guard (moves no existing golden):** after running `legacy_model(world)`,
  re-assert the frozen hashes — world `e62d8f2c`, observatory `f9ad13c7`, social_memory
  `3fbb1aa0`, world_model `5b41a692`, narrative `a32df9e5`, character `36c894fb`,
  timeline `ae42ed5f`, and the P15 chronicle `aa4c67a4` (via `app.chronicle_json`) — all
  byte-identical.

**Expected RED result:** the existing suite stays **439 passed**; the new file adds
tests that all **fail** (not error) with `ModuleNotFoundError: No module named
'chronicle_forge.reporting.legacy'`, plus the boundary-guard tests **pass** (they prove
P17's mere presence perturbs nothing). `black --check` clean.

---

## 9. Acceptance (this phase)

- **Responsibility documented** — §1.
- **"あ、これ昔の自分だ" 導線 explained** — §2 (attribution ordinal + consequence +
  persistence → player-supplied recognition), realized by §6 visualization rules.
- **RED fails cleanly** — §8: in-body `ModuleNotFoundError`, existing 439 untouched,
  boundary guard green.
- **No new Truth confirmed** — §4 per-field source map + the "no invented score" /
  id-free / determinism RED contracts; every field traces to an existing record.
- **Usable as P18+ guidance** — the `LegacyView` is the object P18 Investigation
  decomposes and P21 Atlas aggregates.

---

## 10. Out of scope / guardrails

No implementation, commit, push, or PR. No engine, persistence, or Opportunity-algorithm
change. No new canonical truth. `ChronicleView` and all eight engine goldens + the P15
chronicle golden stay byte-identical (the new view ships its own golden at GREEN). AI
voicing of these cues is P20 (non-canonical side-channel).
