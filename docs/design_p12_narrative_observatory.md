# P12 Emergent Narrative Observatory — Design (For Review, test-first)

Status: **Design + failing tests submitted for review. RED only — no
implementation, no commit.** The new test file is Black-clean; no other file is
touched. A later, separately-approved GREEN issue adds `reporting/narrative.py` and
pins the new golden; a REFACTOR pass follows.

## 1. Problem summary

P6 *generates* causal history; P7 *experiences* a single life; P10 Observatory
*composes* player-safe views as prose; P11-A WorldView is the *structured snapshot*
for a 3D client. What no surface yet does is read the **emergent narrative**: the
story-shaped causal threads that arose on their own — *which player act became
which turning point, and what chain of consequences carried it there*.

P12 adds **one read-only projection** that surfaces that narrative: the top causal
**threads** (origin → consequences → culmination) and the **turning points** (the
pivotal large-scale events history turned on). It is a pure lens over the existing
causal DAG + heritage + lineage — it computes **no new history**.

## 2. Assumptions

- The causal DAG (`world.causal_nodes` + `CausalEdge.caused_by`, `world.seeds`,
  `world.heritage`) is the complete, already-player-safe substrate; `CausalGraph`
  (`ancestors` / `descendants` / `trace_to_roots` / `player_seeds_in_ancestry`)
  gives every primitive a thread needs. *(grounded: `causal.py:84-145`,
  `reporting/_data.py`.)*
- A "thread" = a maximal cause-chain that **culminates** in a `LARGE` event or a
  promoted `HeritageNode`; its **origin** is the player seed (→ `Life N`) or, if no
  player seed is in the ancestry, "world forces".
- A "turning point" = a `LARGE`-scale `CausalNode` (the engine's own significance
  marker — `EventScale.LARGE`, `models.py:259`).
- id-free is a **hard negative contract** (the P8/P11-A lesson): no `seed_id` /
  `node_id` / `life_id` / `npc_id` / `faction_id` / `source_seed` crosses the
  boundary. Lives surface as ordinals + titles; events as `event_phrase` /
  `seed_label` (`reporting/labels.py`).
- The finished world is deterministic for a seed, so the projection is
  deterministic and **read-only** (asserted byte-equal world before/after).

## 3. Proposed architecture / solution

New module **`src/chronicle_forge/reporting/narrative.py`** — a sibling of
`world_model.py`, same shape: immutable (`frozen`, `extra="forbid"`) id-free view
records + a structured builder + a JSON encoder + a thin Markdown surface.

```python
SCHEMA_VERSION = "1"            # read-model contract; decoupled from ENGINE_VERSION

class ThreadView(_View):        # one emergent story
    ordinal: int               # 1-based, by significance (canonical sort)
    title: str                 # culmination event phrase (id-free)
    origin: str                # "Life N (title)" | "world forces"
    domain: str                # SeedDomain.value of the culmination
    start_year: int            # earliest cause year in the chain
    end_year: int              # culmination year
    length: int                # number of causal events in the chain
    culmination_scale: str     # EventScale.value (LARGE | MEDIUM | SMALL)
    player_driven: bool        # a player seed is in the culmination's ancestry

class TurningPointView(_View):  # a pivotal LARGE event
    year: int
    title: str                 # event_phrase (id-free)
    domain: str                # SeedDomain.value
    player_driven: bool
    converging_threads: int    # how many threads culminate at/under it

class NarrativeView(_View):
    schema_version: str
    place: str                 # founding village name (id-free) | world id
    span: int                  # world.current_year
    ending_class: Optional[str]
    threads: List[ThreadView]
    turning_points: List[TurningPointView]

def narrative_model(world: World) -> NarrativeView          # structured
def narrative_json(world: World) -> str                     # canonical JSON + hash basis
def narrative(world: World) -> str                          # "# Narrative" Markdown surface
```

**Composition (no recompute, no new truth):** threads are built from
`CausalGraph.trace_to_roots` over the culmination set (LARGE nodes ∪ heritage
founding nodes); origin from `player_seeds_in_ancestry`; labels from
`labels.event_phrase` / `seed_label`; lineage ordinals from `_data.life_index`.
The Markdown `narrative()` renders the same structured records (the
`observatory()` pattern), so the prose never re-derives anything.

**Determinism (total orders):**
- `threads` sorted by `(scale_rank[LARGE<MEDIUM<SMALL], -length, start_year,
  title)` then assigned `ordinal`; capped at `MAX_THREADS = 7` (MVP).
- `turning_points` sorted by `(year, title)`.
- No dict/set iteration leaks: candidate ids are gathered, then **sorted** before
  any traversal that feeds output.

## 4. Trade-offs

- **Structured-first vs prose-first.** Chosen: structured `NarrativeView` is the
  canonical artifact (hashable, client-ready, testable); `narrative()` Markdown is
  a thin renderer over it. Mirrors P11-A and avoids two sources of truth.
- **Thread definition (culmination = LARGE ∪ heritage).** Uses the engine's own
  significance markers instead of inventing a new score — keeps P12 a *reader*, not
  a second ranking engine. Alternative (score every chain) rejected: more knobs,
  new determinism surface, no clear player value over the existing markers.
- **`MAX_THREADS = 7` cap.** Keeps the surface legible and the golden small;
  surfacing every micro-chain would bury the narrative. Cap is a render concern,
  not new truth.

## 5. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **id leak** across the boundary (seed/node/life/npc id in JSON). | High | Negative-contract regex test `test_narrative_json_is_id_free`; only ordinals + label phrases surface. |
| R2 | **Accidental World mutation** (a builder writes through a live ref). | High | `test_narrative_does_not_mutate_world` asserts `world.model_dump_json()` byte-equal before/after; `CausalGraph` is read-only. |
| R3 | **Non-determinism** from dict/set iteration over node/seed maps. | Medium | Gather→sort before traversal; `test_narrative_is_deterministic_double_run`. |
| R4 | **Touching a frozen golden** (world/observatory/social_memory/world_model/replay). | High | `test_narrative_leaves_existing_goldens`; P12 adds files only, never edits engine/reporting goldens. |
| R5 | **Empty / degenerate worlds** (no LARGE events, no heritage). | Low | Threads/turning_points may be empty lists; views still build; asserted by a minimal-world test at GREEN. |
| R6 | **Scope creep** into engine/Recipe/World. | High | Hard boundary: `reporting/narrative.py` + its test only; no engine/Recipe/ENGINE_VERSION/RNG/World change. |

## 6. File structure

```
NEW (this RED issue):
  docs/design_p12_narrative_observatory.md      (this doc)
  tests/test_narrative.py                       (failing — ImportError until GREEN)

NEW (later GREEN issue, NOT in this issue):
  src/chronicle_forge/reporting/narrative.py
  (+ one line in reporting/__init__.py exporting narrative/narrative_json/narrative_model)
  (+ GOLDEN_NARRATIVE_SHA pinned in tests/test_narrative.py)

UNTOUCHED (hard constraints): the engine, Recipe, ENGINE_VERSION, RNG, World,
  reporting/{observatory,social_memory,world_model}.py and every existing golden.
```

## 7. Implementation plan (RED → GREEN → REFACTOR)

- **RED (this issue):** ship this design doc + `tests/test_narrative.py`. Every test
  imports `chronicle_forge.reporting.narrative` **inside the test body**, so each
  fails individually with `ModuleNotFoundError`; the existing suite is untouched
  (nothing imports the missing module at collection time).
- **GREEN (separate approval):** add `reporting/narrative.py` (structured builder +
  JSON + Markdown), export it, and pin `GOLDEN_NARRATIVE_SHA =
  sha256(narrative_json(simulate_world(42,"opportunity")))[:16]`. All P12 tests
  pass; the five existing goldens stay frozen and asserted.
- **REFACTOR:** factor shared label/lineage helpers, tidy the Markdown renderer,
  and (optionally) lift the id-free `_View` base into a shared reporting module —
  behavior-preserving, golden-stable.

## 8. Verification plan

- `pytest tests/test_narrative.py` — RED now (ImportError); GREEN later.
- Full `pytest` — unchanged count + the new file (no existing test perturbed).
- `black --check` clean.
- Boundary: world `e62d8f2cd24d2c72`, observatory `f9ad13c75c88a9c2`, social-memory
  `3fbb1aa02071dfe2`, world-model `5b41a692cfa3f1ce`, replay transcript
  `98bea8622c686d8e` all unchanged.
- Read-only: `world.model_dump_json()` byte-equal before/after `narrative_model`.
- id-free: regex negative contract over `narrative_json`.
