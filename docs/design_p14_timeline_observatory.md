# P14 Timeline Observatory (Chronological Read-Model) — Design (For Review, test-first)

Status: **Design + failing tests submitted for review. RED only — no
implementation, no commit.** The new test file is Black-clean and imports the
not-yet-existing module **inside each test body**, so every test fails with
`ModuleNotFoundError` and the existing suite is untouched at collection time. A
later, separately-approved GREEN issue adds `reporting/timeline.py` and pins the
new golden; a REFACTOR pass follows.

## 1. Problem summary

The reporting layer now has four read-only lenses over a finished world:

- **P10 Observatory** — player-safe *prose* compose of the world.
- **P11-A WorldView** — the *structured, id-free* world snapshot for a client.
- **P12 NarrativeView** — the *emergent narrative*: the top causal **threads**
  (origin → culmination) plus the pivotal **turning points**, selected by the
  engine's significance markers.
- **P13 CharacterObservatoryView** — the *structured biography* per life.

Every existing lens that touches events does so by **significance or causality**
(P12 keeps only the top `max_threads`; turning points are `LARGE` only). What no
surface answers is the orthogonal, simplest question a history asks: **"when did
things happen?"** — the full event record laid out on a single time axis, in
order, so a reader can scan the world chronologically rather than by importance.

P14 adds **one read-only projection** — the **Timeline Observatory** — that
surfaces every `CausalNode` the engine recorded, **ordered by year**. It is to the
causal history what P13 is to a life: same facts the engine already has,
structured-first, id-free, hashable. It computes **no new history**, invents **no
score**, and **infers no era** — every entry is read straight off an existing
`CausalNode` / `CausalGraph` / `World`.

## 2. Assumptions

- A finished `World.causal_nodes` is the complete, already-player-safe event
  record. Each `CausalNode` carries everything a timeline entry needs
  *(grounded: `models.py:257-265`)*:
  `scale(EventScale) / domain(SeedDomain) / year(int)` — all id-free value data —
  plus `id / title / location_id / actors / caused_by`, which are **id-bearing**
  and must not cross the boundary verbatim.
- **id-free is a hard negative contract** (the P8/P11-A/P12/P13 lesson). Critically:
  - `CausalNode.title` **embeds seed ids** (e.g. `"military event (seed-0000)"`),
    so it is never emitted; the curated `labels.event_phrase(node)` is used instead
    *(grounded: `labels.py:128-129`)*.
  - `id`, `actors`, `location_id`, `caused_by` are raw entity ids → never emitted.
    `location_id` is **humanised** to a location *name* via a `{loc.id: loc.name}`
    lookup over `world.locations` (the P11-A / P13 pattern), or dropped to `None`.
  - Events surface as **ordinals + year**; everything else as enum `.value`
    (`SeedDomain`, `EventScale`) or curated label phrases only.
- Enums are id-free value strings: `SeedDomain`, `EventScale` *(grounded: `enums.py`)*
  — `.value` is safe to surface.
- `player_driven` is read from the existing graph: a `CausalNode` is player-driven
  iff `CausalGraph.player_seeds_in_ancestry(node.id)` is non-empty
  *(grounded: `causal.py:137-144`)* — the same signal P12 already exposes; no new
  inference, no id surfaced.
- The finished world is deterministic for a seed, so the projection is
  deterministic and **read-only** (asserted byte-equal world before/after).
- Existing reporting helpers are reused unchanged: `place` (`_data.py`),
  `event_phrase` (`labels.py`), `CausalGraph` (`causal.py`).

## 3. Proposed architecture / solution

New module **`src/chronicle_forge/reporting/timeline.py`** — a sibling of
`world_model.py` / `narrative.py` / `character.py`, same shape: immutable
(`frozen`, `extra="forbid"`) id-free view records + a structured builder + a JSON
encoder + a thin Markdown renderer that reads **only the view**.

```python
SCHEMA_VERSION = "1"            # read-model contract; decoupled from ENGINE_VERSION

class TimelineEntryView(_View):  # one event on the time axis (the per-event record)
    ordinal: int               # 1-based chronological position — id-free
    year: int                  # CausalNode.year
    title: str                 # event_phrase(node) — id-free (never node.title)
    domain: str                # SeedDomain.value
    scale: str                 # EventScale.value
    location: Optional[str]    # location NAME via world.locations | None — id-free
    player_driven: bool        # a player seed is among the event's causes (graph)

class TimelineView(_View):
    schema_version: str
    place: str                 # founding village name (id-free) | world id (_data.place)
    span: int                  # world.current_year
    start_year: Optional[int]  # earliest event year | None (no events)
    end_year: Optional[int]    # latest event year | None (no events)
    event_count: int           # len(entries)
    entries: List[TimelineEntryView]

def timeline_model(world: World) -> TimelineView    # structured (canonical)
def timeline_json(world: World) -> str              # canonical JSON + hash basis
def timeline_markdown(view: TimelineView) -> str    # "# Timeline" pure renderer
```

**Composition (no recompute, no new truth).** Build a `CausalGraph` once and a
`{loc.id: loc.name}` map once. For each `node` in `world.causal_nodes`: copy
`year`; `title = event_phrase(node)`; `domain = node.domain.value`;
`scale = node.scale.value`; `location = loc_name.get(node.location_id)`;
`player_driven = bool(graph.player_seeds_in_ancestry(node.id))`. Sort the entries by
the total key below, then assign dense 1-based `ordinal`s. `start_year`/`end_year` =
the first/last entry year (or `None`). The Markdown renderer reads the same
`TimelineView` (the `world_model`/`narrative`/`character` pattern), so the prose
never re-derives anything.

**Determinism (total order).** Entries sort by
`(year, _SCALE_RANK[scale], domain, node.id)`:

- `year` is the primary (chronological) key;
- `_SCALE_RANK` (LARGE<MEDIUM<SMALL) then `domain` give a stable, meaningful
  tiebreak within a year;
- `node.id` is the final **internal** tiebreak so equal-(year,scale,domain) events
  are stable — it is used only for sorting and **never** appears in the output
  (exactly P12's `culmination_id` pattern).

No dict/set iteration reaches the output unsorted: entries are a sorted list,
`scale`/`domain` are enum values, `location` is a single string.

## 4. Trade-offs

- **Chronological vs significance-first.** Chosen: P14 is the *time* axis — the
  full event record in year order — deliberately complementary to P12's
  significance-selected threads. The two never overlap in purpose; P14 does not
  re-rank or filter by importance.
- **All events vs a curated subset.** MVP surfaces **every** `CausalNode` (no
  `max_*` cap, no scale filter). Rejected: capping/filtering — that re-introduces a
  significance judgement P12 already owns and would make "the timeline" incomplete.
  (A future `min_scale` *display* filter can live in the renderer without touching
  the canonical view.)
- **No invented era.** A timeline invites "ages/eras", but boundaries would be an
  **inference** the engine does not record. Rejected for MVP: P14 stays a flat,
  ordered list; the Markdown renderer groups visually by `year` only. Era grouping
  is noted as a future extension *if* the engine ever records period boundaries.
- **Location as name, not id.** `location_id` is humanised to a `location` *name*
  (id-free) — a cheap "where" dimension on top of "when". Rejected: emitting
  `location_id` (id leak) or `actors` (raw ids, and per-event actor lists are P13's
  biography concern, not the timeline's).
- **No invented score.** `domain` + `scale` are the engine's own markers;
  `player_driven` is the existing graph signal. P14 adds no composite/importance.

## 5. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **id leak** — `node.title` embeds seed ids; `id`/`actors`/`location_id`/`caused_by` are raw ids. | High | `event_phrase(node)` never `node.title`; ids never emitted; `location_id` → name. Negative-contract regex `test_timeline_json_is_id_free` (entity-id/uuid/hex32/hex40, `source_seed`, no `_id"` key, banned `location_id`/`actors`/`caused_by`/`node_id`). |
| R2 | **Accidental World mutation** via a live ref (esp. building a `CausalGraph`). | High | `CausalGraph` only reads; `test_timeline_model_does_not_mutate_world` asserts `world.model_dump_json()` byte-equal before/after. |
| R3 | **Non-determinism** from equal-year events / dict iteration. | Medium | Total sort key `(year, scale_rank, domain, node.id)` with `node.id` an internal-only final tiebreak; `test_entries_are_year_ordered`, `test_timeline_json_is_deterministic_double_run`. |
| R4 | **Touching a frozen golden** (world/observatory/social_memory/world_model/narrative/character/replay). | High | `test_timeline_leaves_existing_goldens`; P14 adds files only, edits no engine/reporting golden, no `__init__` change required. |
| R5 | **Degenerate world** (no events / no locations). | Low | `entries` empty → `start_year`/`end_year` `None`, `event_count` 0; `location` tolerates `None`; renderer prints an empty-timeline line. |
| R6 | **Scope creep** into engine/Recipe/World/P12. | High | Hard boundary: `reporting/timeline.py` + its test only; no engine/Recipe/ENGINE_VERSION/RNG/World/persistence/CLI change; no re-ranking (P12 owns significance). |

## 6. File structure

```
NEW (this RED issue):
  docs/design_p14_timeline_observatory.md        (this doc)
  tests/test_timeline_observatory.py             (failing — ModuleNotFoundError until GREEN)

NEW (later GREEN issue, NOT in this issue):
  src/chronicle_forge/reporting/timeline.py
  (+ GOLDEN_TIMELINE_SHA pinned in tests/test_timeline_observatory.py)

UNTOUCHED (hard constraints): the engine, Recipe, ENGINE_VERSION, RNG, World,
  persistence, CLI/UI, reporting/{observatory,social_memory,world_model,narrative,
  character,experience}.py and every existing golden.
```

## 7. Implementation plan (RED → GREEN → REFACTOR)

- **RED (this issue):** ship this design doc + `tests/test_timeline_observatory.py`.
  Every test imports `chronicle_forge.reporting.timeline` **inside the test body**,
  so each fails individually with `ModuleNotFoundError`; the existing suite is
  untouched (nothing imports the missing module at collection time). The golden
  constant is a placeholder (`"0000000000000000"`) — the in-body import fails before
  the assertion, keeping the golden test RED for the right reason.
- **GREEN (separate approval):** add `reporting/timeline.py` (structured builder +
  JSON + Markdown) and pin
  `GOLDEN_TIMELINE_SHA = sha256(timeline_json(simulate_world(42,"opportunity")))[:16]`.
  All P14 tests pass; the existing goldens stay frozen and asserted.
- **REFACTOR:** factor the shared id-free `_View` base / `_SCALE_RANK` / label
  helpers across `world_model`/`narrative`/`character`/`timeline`
  (behaviour-preserving, golden-stable).

## 8. Verification plan

- `pytest tests/test_timeline_observatory.py` — RED now (ModuleNotFoundError); GREEN later.
- Full `pytest` — unchanged count + the new file (no existing test perturbed).
- `black --check` clean.
- Boundary (main `9ad743e` goldens unchanged): world `e62d8f2cd24d2c72`, observatory
  `f9ad13c75c88a9c2`, social-memory `3fbb1aa02071dfe2`, world-model
  `5b41a692cfa3f1ce`, narrative `a32df9e5068d054a`, character `36c894fbde084e57`,
  replay transcript `98bea8622c686d8e`.
- Read-only: `world.model_dump_json()` byte-equal before/after `timeline_model`.
- id-free: regex negative contract over `timeline_json` (+ the `_id"` key guard and
  the `location_id`/`actors`/`caused_by`/`node_id` exclusion).
- Renderer purity: `timeline_markdown` reads only the view; deterministic, id-free.
