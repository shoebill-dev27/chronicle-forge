# P9-3 Replay — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** Parent: `docs/design_p9_persistent_history.md` (approved);
builds directly on P9-1 (`docs/design_p9_1_save_load.md`, done & pushed at
`7f68a32`).

## Purpose

Re-execute a Recipe into the world *and re-emit its story*, turning the engine's
determinism into a feature: **"that history, again."** P9-1 already reconstructs
the **world** silently (`replay_recipe(recipe) → World`, `load_recipe(path) →
World`). P9-3 adds the three things that make it an *experience* and a *workflow*:

1. **Transcript regeneration** — replay the run through a real writer so the
   prose unfolds again, byte-for-byte.
2. **A closed failure taxonomy** — replay refuses, never diverges.
3. **CLI** — `--replay recipe.json` to re-watch, `--save recipe.json` to capture
   a run as a recipe (which needs a live **input recorder**).

## Decision 1 — Transcript: regenerate (canonical), never persist

**The transcript is regenerated on every replay; it is not stored in the
Recipe.** Replaying re-runs `run_human_world(seed, scripted_reader(inputs),
writer)`; with a capturing writer the transcript is reproduced. Same seed +
inputs ⇒ byte-identical prose (already observed: CLI `--auto` transcript sha
`98bea862…`, stable). Rationale (matches the reviewer's recommendation):

- The recipe stays tiny and authoritative; prose is derived, not duplicated.
- One source of truth — the engine — so a stored transcript can never silently
  disagree with the world it claims to describe.
- Any saved transcript is a **non-authoritative cache**; exporting one is
  **P9-2's** job, and a cache must be re-validated against regeneration. P9-3
  persists **no** transcript.

## Decision 2 — Replay failure taxonomy (refuse, never fall back)

Replay has a **closed set** of failures; on any of them it raises, never
producing a divergent or approximate world. Two are replay-time gates (already
in P9-1), two are recipe-validity gates (schema-time, surfaced cleanly by P9-3):

| condition | when | raised |
|---|---|---|
| engine_version mismatch | replay-time gate | `EngineVersionMismatch` (P9-1) |
| unsupported `max_year` | replay-time gate | `UnsupportedRecipe` (P9-1) |
| invalid `mode` | recipe parse (closed enum) | **`InvalidRecipe`** (new) |
| invalid `inputs` | recipe parse (not `list[str]`, or inputs under `mode=auto`) | **`InvalidRecipe`** (new) |

- `InvalidRecipe` wraps pydantic's `ValidationError` at the **file boundary**
  (`replay_file`) so the CLI reports one clean "invalid recipe" error. The
  `Recipe` model itself keeps raising `ValidationError` (P9-1 unchanged).
- **Leniency note (consistency with P9-1):** trailing *unconsumed* inputs are
  **not** an error — a recipe may carry more inputs than the run had asks; the
  surplus is never read and the world is identical (this is exactly what the
  P9-1 `["1"]*50` reconstruction test relies on). "Invalid inputs" means
  *malformed* inputs (wrong type / present under auto), not *surplus* inputs.

## Decision 3 — CLI surface

The reviewer fixed the UX on the existing play entrypoint:

```
python -m chronicle_forge.play --seed N --save recipe.json   # play, then capture the recipe
python -m chronicle_forge.play --replay recipe.json          # re-emit the transcript
```

- **`--save FILE`** is a modifier on a normal play (`--seed …`): the run plays as
  today (transcript to stdout), and on completion the recorded recipe is written
  to FILE. `mode` follows the input source (`--auto`→auto, `--script`→script,
  else human); `inputs` = the recorded reader lines.
- **`--replay FILE`** is its own mode: read the recipe, replay it, emit the
  regenerated transcript to stdout. **`--replay` is mutually exclusive with
  `--seed`** (the seed comes from the recipe); argparse enforces this.
- `--debug` (P8) still emits its stderr trace; stdout stays the clean transcript.

> **Open point for the reviewer (judgment call).** This UX requires
> **additively** extending the P8 CLI files (`play/cli.py`, `play/adapter.py`,
> `play/__main__.py`) with new flags. Existing flags
> (`--seed/--auto/--script/--debug`) keep **byte-identical** behavior, re-verified
> against the seed42 `--auto` transcript (`98bea862…`). I read "P8 不可侵" as
> "do not change P8 *behavior*", and adding new flags is additive — but because
> it touches P8 files, I flag it explicitly. Alternative if you prefer strict
> no-touch: a separate replay entrypoint (e.g. `python -m
> chronicle_forge.persistence`), at the cost of splitting the play UX. **Recommend
> the additive extension**, since you specified these flags on the play command.

## Decision 4 — Input recorder (no session change)

`--save` needs the inputs a live play consumed. The reader is *injected* into
`run_human_world`, so a **recording reader** wraps the real reader and appends
each non-EOF line it returns; `run_human_world`, the gate, render, and session
are untouched. Feeding the recorded list back through `scripted_reader`
reproduces the exact reader stream (invalid-then-reprompted lines included, since
each `reader()` call is captured). Auto/EOF records nothing ⇒ `inputs=[]`.

## Architecture

- **`persistence/replay.py` (new):**
  - `replay(recipe, *, writer) -> World` — gate, then re-run with the given
    writer (transcript-emitting reconstruction).
  - `replay_transcript(recipe) -> tuple[World, str]` — capture to a `StringIO`,
    return `(world, transcript)`.
  - `replay_file(path, *, writer) -> World` — `read_recipe` (→ `InvalidRecipe` on
    `ValidationError`), then `replay`.
  - `InvalidRecipe(Exception)`.
- **`persistence/record.py` (new):** `recording_reader(inner) -> (reader,
  inputs)` — a wrapper + the growing list it fills.
- **`persistence/load.py` (P9-1, additive):** extract the two gates into a shared
  `_ensure_replayable(recipe)`; `replay_recipe` (P9-1) and `replay` (P9-3) both
  call it (single-sourced gates). P9-1 is not frozen; behavior is unchanged.
- **`play/{cli,adapter,__main__}.py` (P8, additive only):** `--replay` / `--save`
  flags + wiring; existing flags untouched in behavior.
- **Untouched (inviolable):** `models.py`, `opportunity.py` (P6),
  `reporting/experience.py` (P7), the execution funnel, `run_human_world` and the
  P8 play loop semantics, the seed42 golden assets.

## API (signatures)

```python
class InvalidRecipe(Exception): ...                       # malformed recipe file

def replay(recipe: Recipe, *, writer) -> World            # gated, transcript-emitting
def replay_transcript(recipe: Recipe) -> tuple[World, str]
def replay_file(path, *, writer) -> World                 # read → (InvalidRecipe) → replay

def recording_reader(inner) -> tuple[Reader, list[str]]   # wrap + captured inputs
```

## Determinism & seed42 (permanent guards)

- `replay_transcript(recipe)` is byte-deterministic in **both** outputs (world &
  transcript) across repeats.
- **seed42 EOF replay** reproduces the golden world (`e62d8f2c…`) **and** the
  golden transcript (`98bea862…`) — extends the P9-1 permanent regression to the
  prose layer.
- A `--save` → `--replay` round-trip yields a transcript identical to the
  original run's stdout.

## Test plan (failing — `tests/test_replay.py`, RED until implemented)

- **Transcript regeneration:** `test_replay_transcript_is_deterministic`,
  `test_replay_transcript_matches_live_run`,
  `test_seed42_eof_replay_transcript_matches_golden` (PERMANENT: world
  `e62d8f2c…` + transcript `98bea862…`).
- **Failure taxonomy:** `test_replay_refuses_engine_version_mismatch`,
  `test_replay_refuses_unsupported_max_year`,
  `test_replay_file_rejects_invalid_mode`,
  `test_replay_file_rejects_invalid_inputs`.
- **CLI:** `test_cli_replay_emits_transcript`,
  `test_cli_save_writes_loadable_recipe`,
  `test_cli_save_then_replay_roundtrip`,
  `test_cli_replay_and_seed_are_mutually_exclusive`.

## Implementation plan (after approval — small commits)

1. `persistence/replay.py` + `InvalidRecipe`, and the shared `_ensure_replayable`
   refactor in `load.py` → transcript + failure tests green.
2. `persistence/record.py` (recording reader) → recorder unit tests green.
3. `play/{cli,adapter,__main__}.py` additive `--replay`/`--save` wiring → CLI
   tests green; re-verify seed42 `--auto` transcript `98bea862…` unchanged.

## Constraints honored

- World model / P6 / P7 unchanged; `run_human_world` and the P8 play-loop
  *behavior* unchanged (recorder wraps the injected reader; CLI flags are
  additive).
- seed42 golden inviolable, and now guarded at the transcript layer too.
- Transcript is **regenerated, never persisted**; recipe stays canonical.
