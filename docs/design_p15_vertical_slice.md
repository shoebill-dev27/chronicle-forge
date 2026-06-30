# P15 Vertical Slice — Application Layer design (for review, test-first)

Status (as-built): **GREEN DONE.** `src/chronicle_forge/app/` (`contracts.py` +
`services.py` + `__init__.py`) implemented as designed — composition only, no engine/
persistence/reporting change. `GOLDEN_CHRONICLE_SHA = aa4c67a416178e92` (seed42).
All 14 P15 tests pass; full suite **426 passed**; `black --check` clean; the 8 engine
goldens are byte-identical; the four explore sub-views hash **equal** the frozen
P11/P14/P12/P13 lens goldens (no new truth). The CLI wrapper + `[project.scripts]`
remain a later phase.

Original (RED) status: **Design + failing acceptance tests submitted for review. RED
only — no implementation, no commit.** The new test file is Black-clean and imports the
not-yet-existing Application module **inside each test body**, so every test fails
with `ModuleNotFoundError` and the existing 412-test suite is untouched at
collection time. A later, separately-approved GREEN issue adds the
`chronicle_forge.app` package and pins the new chronicle golden.

Context: [`design_release_roadmap.md`](design_release_roadmap.md) (P15 is the slice
that gates MVP) · slice contract: [`vertical_slice.md`](vertical_slice.md).

---

## 1. Problem & framing

The product makes one promise — *play a world, then explore the history your choices
made, then share it reproducibly* — but three things are true on `main`:

- the surfaces are **disjoint** (`play`, `reporting`, dev report), and
- the **play → explore seam is missing**: after a run, the P10–P14 lenses are
  unreachable without writing Python (`play/render.py` uses only P7 prose), and
- there is **no layer that owns the one-way path** as a unit.

P15 introduces a thin **Application Layer** that owns `play → save → explore → share`
as a single use-case surface, composed entirely from existing parts. It is the
**only** new code. It adds **no truth**: every fact it returns is read off the engine
the way P10–P14 already read it.

---

## 2. The proven premise (why explore is pure composition)

The slice is internally consistent because **the played world *is* the lens-golden
world *is* the demo world**. This is already pinned by `tests/test_replay.py`:

```python
# test_seed42_eof_replay_transcript_matches_golden  (existing, PERMANENT)
r = build_recipe(seed=42, max_year=DEV_WORLD_MAX_YEARS, mode="auto", inputs=[])
world, transcript = replay_transcript(r)
assert _world_sha(world) == "e62d8f2cd24d2c72"     # == simulate_world(42,"opportunity")
assert _sha(transcript) == "98bea8622c686d8e"      # == `play --seed 42 --auto` stdout
```

So `play --seed 42 --auto` reconstructs **exactly** the `simulate_world(42,
"opportunity")` world that the P10–P14 goldens are pinned to. Therefore
`explore(recipe)` — which replays the recipe to that same world and composes the
lenses — yields sub-views whose hashes **equal the existing frozen lens goldens**.
"explore invents no truth" is not an aspiration; it is asserted by golden equality.

> Note: `Recipe.mode ∈ {auto, human, script}` is the *input source*;
> `simulate_world(mode=…) ∈ {legacy, opportunity}` is the *execution policy*. They are
> orthogonal. The P8 human/auto play path runs the opportunity execution layer, which
> is why the two worlds coincide.

---

## 3. Architecture

Strict inward dependency. The Application Layer depends on the existing layers;
**nothing existing depends on it** (additive). The engine stays frozen at the core.

```
            ┌──────────────────────────────────────────────────────────┐
   thin     │  CLI  `chronicle-forge {play, explore, share}`            │   (P15 GREEN /
  wrapper   │  argv → request DTO → app.* → render(result) → stdout     │    P16; not in
            │  holds NO game logic, draws NO RNG, reads NO clock        │    this RED issue)
            └───────────────────────────┬──────────────────────────────┘
                                         │ calls only
            ┌────────────────────────────▼─────────────────────────────┐
  NEW       │            Application Layer  `chronicle_forge.app`        │
 (this      │  services:  play()  ·  explore() / explore_file()  ·  share()
  issue,    │  view+DTO:  PlayRequest/PlayOutcome · ChronicleView ·      │
  app only) │             ShareRequest/ShareResult · SCHEMA_VERSION      │
            │  owns the one-way USE CASE; composes below; adds no truth  │
            └───────┬───────────────┬───────────────────┬──────────────┘
                    │ play          │ persist/replay    │ compose
            ┌───────▼──────┐ ┌──────▼───────────┐ ┌─────▼──────────────────────┐
            │  P8 play     │ │ P9 persistence   │ │ P10–P14 reporting (lenses) │
            │  adapter,    │ │ build/read_recipe│ │ world_model · timeline ·   │
            │  session     │ │ replay_transcript│ │ narrative · character ·    │
            │  (run/record)│ │ write_export     │ │ heritage_explorer (read)   │
            └───────┬──────┘ └──────┬───────────┘ └─────┬──────────────────────┘
                    └───────────────┴────────────────────┘
                          ┌─────────▼──────────┐
                          │  Engine P0–P6      │  FROZEN — 8 golden hashes byte-identical
                          │  World/Recipe/RNG  │  (no change in this issue, ever)
                          └────────────────────┘
```

---

## 4. Application Service responsibilities (explicit)

| Service | Responsibility | Composes (existing) | Returns | Must NOT |
|---|---|---|---|---|
| `play(req)` | Grow (or auto/script-drive) a world and capture its **canonical Recipe** + regenerated transcript + id-free outcome facts. | `play.adapter.play_and_record` | `PlayOutcome` | hold a live `World` across the boundary; draw RNG itself; persist (caller/CLI decides where) |
| `explore(recipe)` | Reconstruct the world the recipe describes and **compose the P10–P14 lenses** into one id-free `ChronicleView`. | `persistence.replay_transcript` → `reporting.{world_model,timeline,narrative,character,heritage_explorer}` | `ChronicleView` | invent any score/era/ordering not already in a lens; emit any id; mutate the recipe |
| `explore_file(path)` | `read_recipe(path)` then `explore`. | `persistence.read_recipe` | `ChronicleView` | guess on a schema-invalid file (propagate `InvalidRecipe`) |
| `chronicle_json(recipe)` | Canonical JSON of the `ChronicleView` — the **golden basis** and client contract. | `explore(recipe).model_dump_json()` | `str` | reorder/inject fields |
| `chronicle_markdown(view)` | **Pure renderer**: compose the lens markdowns from the view only. | view + lens `*_markdown` | `str` | read the world/recipe again |
| `share(req)` | Emit a transcript **artifact** and the reproducible replay command; the recipe **is** the shareable save. | `persistence.write_export` + `replay_transcript` | `ShareResult` | alter the recipe; produce a non-reproducible artifact |

**Determinism / read-only / id-free** are structural here: `explore`/`share` each
**replay the recipe to a fresh world**, so there is no shared `World` to mutate; the
output is byte-deterministic for a recipe; id-freedom is inherited from the lenses
and re-asserted by a negative-contract test.

---

## 5. CLI / API boundary (明確化)

| Concern | Application Layer (`app`) | CLI (thin wrapper) |
|---|---|---|
| Use-case orchestration (play→save→explore→share) | **owns** | delegates |
| World reconstruction / lens composition | **owns** | never |
| Determinism, id-free, golden contract | **owns & tested** | inherits |
| argv parsing, `--help`, exit codes | none | **owns** |
| stdout/stderr formatting, file paths chosen by user | none | **owns** |
| Game logic / RNG / clock | none | none |

The CLI is `argv → request → app.* → render → stdout`. Because the value lives in
`app`, the **acceptance tests target `app` directly** (the correct seam); the CLI is
a presentation shell wired and tested at GREEN/P16, not in this RED issue.

---

## 6. New Application API (the surface this issue pins)

`src/chronicle_forge/app/` — frozen (`frozen=True, extra="forbid"`) DTOs; the
`ChronicleView` and `PlayOutcome` are **id-free** at the boundary.

```python
SCHEMA_VERSION = "1"            # app read-model contract; decoupled from ENGINE_VERSION

class PlayRequest(_Frozen):
    seed: int
    auto: bool = False          # EOF-equivalent full run; auto ⇔ inputs == []
    script_lines: Optional[List[str]] = None   # scripted chooser (mutually exclusive w/ auto)
    social_memory: bool = False

class PlayOutcome(_Frozen):     # id-free result of a grown/driven world
    recipe: Recipe              # the canonical save (seed+max_year+mode+inputs)
    transcript: str             # regenerated, byte-deterministic (== replay)
    ending_class: Optional[str] # world.ending_class — id-free
    life_count: int
    span: int                   # world.current_year

class ChronicleView(_Frozen):   # the explore product — composed, id-free
    schema_version: str
    place: str                  # _data.place(world) — id-free
    span: int
    ending_class: Optional[str]
    world: WorldView                  # P11  (== world_model golden 5b41a692)
    timeline: TimelineView            # P14  (== ae42ed5f)
    narrative: NarrativeView          # P12  (== a32df9e5)
    characters: CharacterObservatoryView  # P13 (== 36c894fb)
    heritage_markdown: str            # heritage_explorer(world) — id-free renderer

class ShareRequest(_Frozen):
    recipe: Recipe
    export_path: Optional[str] = None

class ShareResult(_Frozen):
    recipe: Recipe
    transcript: str             # == PlayOutcome.transcript for the same recipe
    export_path: Optional[str]
    reproducible_command: str   # e.g. "chronicle-forge play --replay <recipe>"

def play(request: PlayRequest) -> PlayOutcome
def explore(recipe: Recipe) -> ChronicleView
def explore_file(path: str | Path) -> ChronicleView
def chronicle_json(recipe: Recipe) -> str
def chronicle_markdown(view: ChronicleView) -> str
def share(request: ShareRequest) -> ShareResult
```

---

## 7. Determinism, read-only, id-free (contracts)

- **Deterministic.** `chronicle_json(recipe) == chronicle_json(recipe)`; `share`
  transcript `== replay_transcript(recipe)[1]`. Both follow from engine determinism.
- **Read-only.** `recipe.model_dump_json()` is byte-equal before/after `explore`/`share`;
  no caller-owned `World` exists to mutate (each call replays a fresh one).
- **id-free.** `chronicle_json` passes the P10–P14 negative contract (entity-id /
  uuid / hex32 / hex40, no `source_seed`, no `_id"` key) — inherited from the lenses.
- **No new truth.** The composed sub-views hash **equal to the existing lens goldens**;
  `explore` ranks/filters/labels nothing the lenses did not already.

---

## 8. RED plan (this issue)

- Ship this design doc + `tests/test_vertical_slice.py`.
- Every test imports `chronicle_forge.app` **inside the test body**, so each fails
  individually with `ModuleNotFoundError: No module named 'chronicle_forge.app'`; the
  existing 412 tests are untouched (nothing imports the missing package at collection).
- The new chronicle golden is a placeholder `"0000000000000000"`; the in-body import
  fails before the assertion, keeping the golden test RED for the right reason.
- `black --check` clean.

**Acceptance tests (the one-way path, end to end):**

1. surface — `app` exposes the services + DTOs + `SCHEMA_VERSION`.
2. play — `play(seed=42, auto=True)` → ending set, `life_count≥1`, `span>0`,
   `recipe.mode=="auto"`, `recipe.inputs==[]`, **`sha(transcript)==98bea862`**.
3. save — the outcome's recipe `save_recipe`→`read_recipe` round-trips equal.
4. explore composes 5 lenses — typed `world/timeline/narrative/characters` +
   `heritage_markdown`; `schema_version=="1"`.
5. explore = existing truth — each sub-view JSON hashes to its **frozen lens golden**
   (5b41a692 / ae42ed5f / a32df9e5 / 36c894fb).
6. explore id-free — `chronicle_json` passes the negative contract.
7. explore deterministic — double-run byte-equal.
8. explore read-only — `recipe` JSON unchanged before/after.
9. explore golden — `sha(chronicle_json) == GOLDEN_CHRONICLE_SHA` (placeholder→GREEN).
10. share — artifact written; `result.transcript==outcome.transcript`;
    `sha==98bea862`; `reproducible_command` contains `--replay`.
11. full one-way path — play→save→explore→share consistency (span/ending/transcript
    agree across the spine).
12. boundary guard — the 8 engine goldens unchanged (engine byte-identical).

---

## 9. Golden boundary

P15 **adds one** new golden (`GOLDEN_CHRONICLE_SHA`, pinned at GREEN) and **moves
none**. Re-asserted unchanged: world `e62d8f2c`, observatory `f9ad13c7`,
social_memory `3fbb1aa0`, world_model `5b41a69`, narrative `a32df9e5`, character
`36c894fb`, timeline `ae42ed5f`, replay-transcript `98bea862`.

---

## 10. File structure

```
NEW (this RED issue):
  docs/design_p15_vertical_slice.md     (this doc)
  tests/test_vertical_slice.py          (failing — ModuleNotFoundError until GREEN)

NEW (later GREEN issue, NOT here):
  src/chronicle_forge/app/__init__.py        (re-exports the surface)
  src/chronicle_forge/app/contracts.py       (frozen DTOs + ChronicleView)
  src/chronicle_forge/app/services.py        (play / explore / share — composition only)
  (+ GOLDEN_CHRONICLE_SHA pinned in tests/test_vertical_slice.py)

NEW (P15 GREEN / P16, NOT here):
  src/chronicle_forge/cli.py + [project.scripts] chronicle-forge

UNTOUCHED (hard constraints): the engine, World, Recipe, RNG, persistence on-disk
  format, P6/P7/P8, reporting/{observatory,world_model,narrative,character,timeline,
  social_memory,heritage_explorer}.py, and every existing golden.
```

## 11. GREEN preview

Add `chronicle_forge.app` composing `play.adapter` + `persistence.replay_transcript`
+ the P10–P14 builders; pin `GOLDEN_CHRONICLE_SHA = sha256(chronicle_json(<seed42 auto
recipe>))[:16]`. All 12 slice tests pass; the 8 engine goldens stay frozen; `black`
clean. Then (P15 GREEN/P16) add the thin `cli.py` + `[project.scripts]` and its tests.
