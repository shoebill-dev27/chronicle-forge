# P13 Character Observatory (Biography Read-Model) — Design (For Review, test-first)

Status: **Design + failing tests submitted for review. RED only — no
implementation, no commit.** The new test file is Black-clean and imports the
not-yet-existing module **inside each test body**, so every test fails with
`ModuleNotFoundError` and the existing suite is untouched at collection time. A
later, separately-approved GREEN issue adds `reporting/character.py` and pins the
new golden; a REFACTOR pass follows.

## 1. Problem summary

The reporting layer has three read-only lenses over a finished world:

- **P10 Observatory** — player-safe *prose* compose of the world.
- **P11-A WorldView** — the *structured, id-free* world snapshot for a non-text
  client (a roster `LifeView` is a thin 6-field stub: ordinal/title/birth/death/
  dominant_axis/world_impact).
- **P12 NarrativeView** — the *emergent narrative* (causal threads + turning points).

What no **structured** surface does is render a single life as a **biography**:
the character sheet the engine already computed — the 8 evaluation lenses, the
activity profile, talent, the death, and the legacies that life founded. P7
`experience.py` (`dead_summary`/`life_chronicle`/`life_timeline`/`legacy_view`)
tells that story as *locked prose*; there is no structured, client-ready,
hashable form of it.

P13 adds **one read-only projection** — the **Character Observatory** — that
surfaces, per life, the structured **biography** the engine produced. It is to P7
what P11-A WorldView is to the P10 Observatory: same data, structured-first,
id-free, hashable. It computes **no new history** and invents **no score** — every
number is read straight off the `Life` record.

## 2. Assumptions

- A finished `World.lives` (list order = canonical lineage) is the complete,
  already-player-safe substrate. Each `Life` carries everything a biography needs
  *(grounded: `models.py:198-210`)*:
  `birth_year / death_year / age_at_death / death_cause(DeathCause) /
  talent(Talent) / evaluation(Evaluation: 8 int lenses) /
  activity_log[ActivityRecord] / summary(LifeSummary)`.
- **id-free is a hard negative contract** (the P8/P11-A/P12 lesson). Critically,
  `LifeSummary.seeds_created` / `heritage_created` / `notable_events` hold **raw
  entity ids** (`seed_id` / `heritage_id` / `node_id`) *(grounded: `life.py:63-95`)*
  — so none of those lists may cross the boundary verbatim. They are **counted**
  (`seeds_planted`, `world_impact`) or **humanised** (`heritage_id → heritage_name`)
  instead. Lives surface as **ordinals**; events/legacies as curated `labels.py`
  phrases only.
- Enums are id-free value strings: `DeathCause` (`lifespan|combat|choice`),
  `Talent` (`scholar|warrior|…`), `ActivityCategory` (`exploration|combat|…`),
  `ThemeAxis` *(grounded: `enums.py`)* — `.value` is safe to surface.
- The finished world is deterministic for a seed, so the projection is
  deterministic and **read-only** (asserted byte-equal world before/after).
- Existing reporting helpers are reused unchanged: `life_index`,
  `life_world_impact`, `seeds_of_life`, `place` (`_data.py`),
  `heritage_name` (`labels.py`).

## 3. Proposed architecture / solution

New module **`src/chronicle_forge/reporting/character.py`** — a sibling of
`world_model.py` / `narrative.py`, same shape: immutable (`frozen`,
`extra="forbid"`) id-free view records + a structured builder + a JSON encoder + a
thin Markdown renderer that reads **only the view**.

```python
SCHEMA_VERSION = "1"            # read-model contract; decoupled from ENGINE_VERSION

class LensScores(_View):        # the engine's 8 evaluation lenses (section 8)
    military: int; politics: int; economy: int; academia: int
    culture: int; faith: int; mentoring: int; heritage: int

class BiographyView(_View):     # one character's biography (the rich per-life record)
    ordinal: int               # 1-based "Life N" (lineage order) — id-free
    title: str                 # LifeSummary.title (curated) — id-free
    is_current: bool           # life.id == player.current_life_id (id compared, never shown)
    birth_year: int
    death_year: Optional[int]
    age_at_death: Optional[int]
    death_cause: Optional[str]  # DeathCause.value | None
    talent: Optional[str]       # Talent.value | None
    dominant_axis: Optional[str]# ThemeAxis.value | None (from summary)
    evaluation: LensScores      # 8 ints, fixed field order
    activity: Dict[str, int]    # ActivityCategory.value -> count, key-sorted
    seeds_planted: int          # seeds_of_life() count — never the ids
    world_impact: int           # life_world_impact(): events this life caused
    legacies: List[str]         # founded heritage NAMES (heritage_name), sorted

class CharacterObservatoryView(_View):
    schema_version: str
    place: str                 # founding village name (id-free) | world id (shared _data.place)
    span: int                  # world.current_year
    life_count: int            # len(world.lives)
    characters: List[BiographyView]

def character_model(world: World) -> CharacterObservatoryView   # structured (canonical)
def character_json(world: World) -> str                         # canonical JSON + hash basis
def character_markdown(view: CharacterObservatoryView) -> str   # "# Characters" pure renderer
```

**Composition (no recompute, no new truth).** Per `life` in `world.lives` (already
the lineage order): scalars copied straight off `Life`; `evaluation` mirrored
field-for-field into `LensScores`; `activity` = `Counter(rec.category …)` →
key-sorted dict; `seeds_planted`/`world_impact` are counts; `legacies` =
`{h.id: h for h in world.heritage}` looked up from `summary.heritage_created`,
mapped through `labels.heritage_name`, then **sorted**. The Markdown renderer reads
the same `CharacterObservatoryView` (the `world_model`/`narrative` pattern), so the
prose never re-derives anything.

**Determinism (total orders).**
- `characters` follow `world.lives` order (= `life_index` ordinals) — already total.
- `activity` is a key-sorted `dict[str,int]`; `legacies` is a sorted `list[str]`;
  `evaluation` is a fixed-field model. No dict/set iteration reaches output unsorted.

## 4. Trade-offs

- **Structured-first vs prose-first.** Chosen: `CharacterObservatoryView` is the
  canonical, hashable, client-ready artifact; `character_markdown` is a thin
  renderer over it. Mirrors P11-A/P12 and keeps one source of truth. P7's prose is
  left **untouched and authoritative for narrative voice** — P13 is the *data* form,
  not a second prose surface.
- **Counts/names over id lists.** `seeds_created`/`heritage_created`/`notable_events`
  are raw ids, so MVP surfaces `seeds_planted` (count), `world_impact` (count), and
  `legacies` (heritage *names*). Rejected: emitting the id lists (id leak) or
  re-deriving a per-event phrase list (scope creep; the engine already exposes
  `world_impact`, and P12 NarrativeView owns event-level phrasing).
- **No invented score.** The 8 `evaluation` lenses + `world_impact` are the engine's
  own metrics; P13 adds no composite/ranking. Rejected: a "biography importance"
  score (new knob, new determinism surface, no clear player value).
- **Relationships deferred.** A life's bonds already surface in P10 Social Memory L1
  / WorldView `bonds`; duplicating them per-character is redundant for MVP. Noted as
  a future extension (id-free NPC *names* via the existing humaniser).

## 5. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | **id leak** — `seeds_created`/`heritage_created`/`notable_events` are raw ids. | High | They never cross the boundary: counts + `heritage_name`. Negative-contract regex test `test_character_json_is_id_free` (entity-id/uuid/hex32/hex40, `source_seed`, no `_id"` key). |
| R2 | **Accidental World mutation** via a live ref. | High | `test_character_model_does_not_mutate_world` asserts `world.model_dump_json()` byte-equal before/after; builder only reads. |
| R3 | **Non-determinism** from dict/set iteration (activity, heritage map). | Medium | `activity` key-sorted, `legacies` sorted, lives in list order; `test_character_json_is_deterministic_double_run`. |
| R4 | **Touching a frozen golden** (world/observatory/social_memory/world_model/replay). | High | `test_character_leaves_existing_goldens`; P13 adds files only, edits no engine/reporting golden, no `__init__` change required. |
| R5 | **Degenerate lives** (alive life: no death_year/age_at_death; no talent/summary). | Low | Optional fields tolerate `None`; empty `activity`/`legacies` are empty containers; asserted by a minimal-life test at GREEN. |
| R6 | **Scope creep** into engine/Recipe/World/P7. | High | Hard boundary: `reporting/character.py` + its test only; no engine/Recipe/ENGINE_VERSION/RNG/World/`experience.py` change. |

## 6. File structure

```
NEW (this RED issue):
  docs/design_p13_character_observatory.md       (this doc)
  tests/test_character_observatory.py            (failing — ModuleNotFoundError until GREEN)

NEW (later GREEN issue, NOT in this issue):
  src/chronicle_forge/reporting/character.py
  (+ GOLDEN_CHARACTER_SHA pinned in tests/test_character_observatory.py)

UNTOUCHED (hard constraints): the engine, Recipe, ENGINE_VERSION, RNG, World,
  reporting/{observatory,social_memory,world_model,narrative,experience}.py and
  every existing golden.
```

## 7. Implementation plan (RED → GREEN → REFACTOR)

- **RED (this issue):** ship this design doc + `tests/test_character_observatory.py`.
  Every test imports `chronicle_forge.reporting.character` **inside the test body**,
  so each fails individually with `ModuleNotFoundError`; the existing suite is
  untouched (nothing imports the missing module at collection time).
- **GREEN (separate approval):** add `reporting/character.py` (structured builder +
  JSON + Markdown) and pin
  `GOLDEN_CHARACTER_SHA = sha256(character_json(simulate_world(42,"opportunity")))[:16]`.
  All P13 tests pass; the existing goldens stay frozen and asserted.
- **REFACTOR:** factor the shared id-free `_View` base / label helpers across
  `world_model`/`narrative`/`character` (behaviour-preserving, golden-stable).

## 8. Verification plan

- `pytest tests/test_character_observatory.py` — RED now (ModuleNotFoundError); GREEN later.
- Full `pytest` — unchanged count + the new file (no existing test perturbed).
- `black --check` clean.
- Boundary (main `b5e310f` goldens unchanged): world `e62d8f2cd24d2c72`, observatory
  `f9ad13c75c88a9c2`, social-memory `3fbb1aa02071dfe2`, world-model
  `5b41a692cfa3f1ce`, replay transcript `98bea8622c686d8e`.
- Read-only: `world.model_dump_json()` byte-equal before/after `character_model`.
- id-free: regex negative contract over `character_json` (+ the `_id"` key guard and
  the `seeds_created`/`heritage_created`/`notable_events` exclusion).
- Renderer purity: `character_markdown` reads only the view; deterministic, id-free.
