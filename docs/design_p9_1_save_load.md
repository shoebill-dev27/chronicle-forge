# P9-1 Save/Load — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation yet.**
Parent: `docs/design_p9_persistent_history.md` (approved). Decisions locked by the
reviewer: recipe is canonical, snapshot is an optional cache, `engine_version`
is mandatory, a version mismatch **refuses** replay, and seed42 EOF replay is a
**permanent regression test**.

## Scope

Persist a run as a **Recipe** and reconstruct it exactly. This issue delivers:
the `persistence/` package, the locked `Recipe` model, `save_recipe()` /
`load_recipe()`, `engine_version` validation, a fixed on-disk JSON schema, and
the determinism tests (including the seed42 permanent guard).

Out of scope for P9-1 (later issues / follow-ons): the optional `snapshot`
cache, the live human **input recorder** + CLI `--save`/`--load` wiring, replay
pacing (P9-3), transcript export (P9-2), and the viewers (P9-4/5).

## Locked Recipe schema

Exactly the reviewer's five fields — nothing added to `models.py`:

```text
Recipe:
  engine_version : str
  seed           : int
  max_year       : int
  mode           : "auto" | "human" | "script"
  inputs         : list[str]
```

Model rules (validators):

- `mode` is a closed enum (`Literal["auto","human","script"]`); any other value
  is rejected at construction.
- **`mode == "auto"` ⇒ `inputs == []`.** "auto" means the player is never
  prompted; a non-empty input list under auto is a contradiction and is rejected.
  (`human`/`script` may have empty inputs — e.g. an immediate-EOF human run,
  which is then equivalent to auto.)
- `inputs` are **strings**, one per reader line, in order — exactly what a
  `--script` file contains. This is the faithful replay stream: replay feeds
  `scripted_reader(inputs)`, so re-prompted invalid entries (if any) must be
  recorded verbatim too. Strings (not ints) preserve that fidelity.

## `inputs` — what the list means (replay fidelity)

A run is determined by `seed` + `max_year` + the exact sequence of lines the
chooser's reader yields. Therefore:

- **`inputs` = every non-EOF line returned by the reader, in order.** When the
  list is exhausted, `scripted_reader` returns EOF and every remaining gate ask
  is entrusted to the auto-chooser — byte-identical to how a live run continues
  past the player's last input.
- `mode == "auto"` ⇒ `inputs == []` ⇒ the whole run is auto/EOF ⇒ identical to
  `simulate_world(seed, mode="opportunity")`. **This is the seed42 permanent
  guard.**
- Acting vs. "let it pass" both go into `inputs` (passing draws auto RNG and so
  diverges the stream from acting — both must be captured to replay faithfully).

> The mechanism that *captures* `inputs` from a live human play (a recording
> reader around `play.human`) is a small, additive follow-on within P9-1 (or
> P9-1b) and is **not** required by the persistence contract below; the failing
> tests pin save/load/reconstruct using explicit `inputs`, independent of how
> they were recorded.

## Package layout (new, isolated)

```
src/chronicle_forge/persistence/
  __init__.py     # public surface: Recipe, build_recipe, save_recipe,
                  #   read_recipe, load_recipe, ENGINE_VERSION, errors
  version.py      # ENGINE_VERSION — the single source of truth
  schema.py       # Recipe (pydantic BaseModel) + validators; errors
  save.py         # build_recipe(), save_recipe()  (write fixed JSON)
  load.py         # read_recipe(), load_recipe()    (parse, gate, reconstruct)
```

Nothing in `models.py`, `opportunity.py` (P6), `reporting/experience.py` (P7),
`heritage.py`, the execution funnel, or `play/` (P8) is modified. `persistence`
*imports* `play.session.run_human_world`, `play.human.scripted_reader`,
`play.human.null_writer`, `autoplay.simulate_world`, and `config` — read-only
reuse, no edits.

## API (signatures)

```python
ENGINE_VERSION: str   # version.py, e.g. "0.1.0-p8-mvp" (the determinism baseline)

class Recipe(BaseModel):
    engine_version: str
    seed: int
    max_year: int
    mode: Literal["auto", "human", "script"]
    inputs: list[str] = []

class EngineVersionMismatch(Exception): ...   # recipe recorded under another engine
class UnsupportedRecipe(Exception): ...        # cannot be faithfully reconstructed today

def build_recipe(*, seed, max_year, mode, inputs) -> Recipe   # stamps ENGINE_VERSION
def save_recipe(recipe: Recipe, path) -> None                 # write fixed-schema JSON
def read_recipe(path) -> Recipe                               # parse + schema-validate (no gate)
def load_recipe(path) -> World                               # read_recipe → gate → reconstruct
```

### `load_recipe` algorithm

1. `recipe = read_recipe(path)` — pydantic validates the fixed schema.
2. **engine gate:** if `recipe.engine_version != ENGINE_VERSION` → raise
   `EngineVersionMismatch` (refuse; never silently diverge). No snapshot fallback
   in P9-1 because P9-1 has no snapshot — the gate is a hard stop here.
3. **max_year gate:** if `recipe.max_year != config.DEV_WORLD_MAX_YEARS` → raise
   `UnsupportedRecipe`. (See limitation below.)
4. **reconstruct:** `run_human_world(recipe.seed,
   reader=scripted_reader(recipe.inputs), writer=null_writer)` → return the World.

### `max_year` limitation (honest, by design)

`run_human_world` calls `generate_world(seed)` with the **default** `max_year`
and does not expose it. Under "P8 不可侵", P9-1 will **not** change the session.
Consequences:

- All CLI-produced runs use `max_year = DEV_WORLD_MAX_YEARS = 40`, so recording
  it and reconstructing against the default is faithful **today**.
- `max_year` is still recorded (provenance + future-proofing + the version gate).
- A recipe with a non-default `max_year` is **refused** (`UnsupportedRecipe`)
  rather than silently reconstructed at 40 — keeping the determinism promise
  honest.
- *Future, separate review:* if non-default `max_year` is ever needed, expose it
  through the session as an **additive, byte-identity-preserving** parameter
  (not part of P9-1).

## Fixed on-disk JSON schema

- `save_recipe` writes `json.dumps(recipe.model_dump(), sort_keys=True, indent=2)`
  + trailing newline — **deterministic bytes** (sorted keys, fixed indent) so two
  saves of the same recipe are byte-identical and diffs are clean.
- Top-level keys are exactly `{engine_version, seed, max_year, mode, inputs}`.
- `read_recipe` is strict: unknown keys / wrong types fail validation (the schema
  is pinned, not loosely parsed).

## Test plan (failing tests — `tests/test_persistence.py`)

Written first; all currently RED (module absent). They define the contract:

**Schema**
- `test_recipe_locked_fields` — exactly the five fields.
- `test_recipe_rejects_unknown_mode` — closed enum.
- `test_auto_mode_requires_empty_inputs` — the auto invariant.
- `test_inputs_are_strings` — fidelity type.
- `test_build_recipe_stamps_current_engine_version`.

**Save/Load file**
- `test_save_read_roundtrip` — `save → read` equal.
- `test_saved_json_schema_is_fixed_and_deterministic` — byte-stable, key set pinned.

**engine_version gate**
- `test_load_rejects_engine_version_mismatch` → `EngineVersionMismatch`.
- `test_load_accepts_matching_engine_version`.

**max_year gate**
- `test_load_rejects_unsupported_max_year` → `UnsupportedRecipe`.

**Reconstruction determinism**
- `test_load_reconstructs_deterministically` — load twice, equal.
- `test_acting_recipe_matches_live_run` — reconstruct == live
  `run_human_world(seed, scripted_reader(inputs))`.
- **`test_seed42_eof_replay_equals_golden` — PERMANENT REGRESSION.** Recipe
  `(seed=42, max_year=40, mode="auto", inputs=[])` reconstructs a world equal to
  `simulate_world(42, "opportunity")`, sha `e62d8f2c…`.

## Implementation plan (after approval — small commits)

1. `persistence/version.py` + `schema.py` (Recipe + validators + errors) — turns
   the schema tests green.
2. `persistence/save.py` (`build_recipe`, `save_recipe`) + `read_recipe` — turns
   the file/roundtrip tests green.
3. `persistence/load.py` (`load_recipe`: gates + reconstruct) — turns the gate +
   determinism + seed42 tests green.
4. `black` on changed files only; full suite green; seed42 golden unchanged.

Each step is a small, self-contained commit (schema → write → load).

## Constraints honored

- **World model unchanged** — Recipe lives in `persistence/`, not `models.py`.
- **P6/P7/P8 inviolable** — `persistence` only imports and reuses them.
- **seed42 golden inviolable** — and now *guarded* by a permanent replay test.
- **formatter only on changed files**; **test-first**; **small commits**.
