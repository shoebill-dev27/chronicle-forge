# P16 MVP Cohesion — installable CLI, packaging, CI, onboarding (design, test-first)

Status: **Design + failing CLI/packaging tests submitted for review. RED only — no
implementation, no commit.** The new test files are Black-clean and import the
not-yet-existing `chronicle_forge.cli` **inside each test body**, so every test fails
with `ModuleNotFoundError` and the existing 426-test suite is untouched at collection
time. A later, separately-approved GREEN issue adds `chronicle_forge/cli.py`, the
`[project.scripts]` entry, the CI workflow, and the README rewrite.

Builds on **P15** (`chronicle_forge.app`, the Application Layer). Roadmap context:
[`design_release_roadmap.md`](design_release_roadmap.md) (P16 completes the **MVP**
milestone, v0.4.0) · slice: [`design_p15_vertical_slice.md`](design_p15_vertical_slice.md).

---

## 1. Problem & scope

P15 made the one-way path real **as a Python API** (`chronicle_forge.app`). It is not
yet a product: there is no installable command, no CI, and the public docs are stale
and wrong (`README` "Next: P4"; `__init__` "rules-only core, AI added later"). P16
closes exactly those gaps and **nothing else**:

- **Installable CLI** `chronicle-forge {play, explore, share}` — a *thin* wrapper.
- **Packaging** for `pipx install` (console entry + single-source version).
- **CI** (GitHub Actions: `black --check` + `pytest` on push/PR).
- **Onboarding** (truthful README rewrite proposal).

**Hard scope rule:** P16 is **wiring / packaging / onboarding only**. It writes no game
logic, invents no truth, and changes no Engine / World / Recipe / RNG / persistence /
reporting / **app** behaviour. The 8 engine goldens + the chronicle golden stay
byte-identical; replay stays byte-deterministic.

---

## 2. Principle — the CLI is a thin wrapper; `app` is the only boundary

```
argv ──▶ chronicle_forge.cli ──▶ chronicle_forge.app ──▶ (P8 play | P9 persistence | P10–P14 lenses) ──▶ engine (frozen)
         parse · render · exit        the ONLY integration boundary
```

| Concern | `cli.py` (P16) | `app` (P15, unchanged) |
|---|---|---|
| argv parsing, subcommands, `--help`, `--version`, exit codes | **owns** | none |
| stdout = clean transcript/chronicle; stderr = human status notes | **owns** | none |
| Use-case orchestration (play→save→explore→share) | delegates | **owns** |
| World reconstruction / lens composition / determinism / id-free | never | **owns** |
| Game logic, RNG, clock, engine/persistence/reporting calls | **never** | composes |

The CLI imports **only** `chronicle_forge.app` for behaviour (it may import stdlib for
argv/IO). It contains no `import ..engine/world/persistence/reporting` for game work.
This keeps `app` the single, tested integration seam (the P15 contract).

---

## 3. Command system

`chronicle-forge [--version] <command> …` — argparse with subparsers. Following the
existing `play/__main__` contract: **stdout is a clean transcript/chronicle; all human
status ("Saved …", hints, errors) goes to stderr**, so machine output stays pure.

### 3.1 `play` — generate / replay a world deterministically
```
chronicle-forge play --seed N (--auto | --script FILE) [--social-memory] [--save FILE] [--export FILE]
chronicle-forge play --replay FILE [--export FILE]
```
- `--auto` → `app.play(PlayRequest(seed=N, auto=True, …))`; `--script FILE` →
  `app.play(PlayRequest(seed=N, script_lines=read_lines(FILE), …))`.
- `--save FILE` writes the returned `PlayOutcome.recipe`; `--export FILE` writes a
  transcript artifact.
- `--replay FILE` reprints a saved recipe's transcript (via `app.share(...).transcript`).
- **stdout** = `PlayOutcome.transcript` (byte-deterministic; sha == `98bea862` for
  `--seed 42 --auto`). **stderr** = "Saved recipe to FILE", etc.

> **Interactive (live-stdin) human play is intentionally NOT wired in P16.** The P15
> `app.play()` is a *batch* service: it buffers the transcript and returns it, which
> cannot drive a live prompt/choice loop. Surfacing interactive play under
> `chronicle-forge play` requires a **streaming Application entry** (e.g.
> `app.play_interactive(request, *, reader, writer)`) — an *additive* app API that is
> **out of P16's wiring-only scope**. Until it lands, the existing
> `python -m chronicle_forge.play --seed N` remains the interactive entry (unchanged,
> no regression). MVP `play` therefore requires `--auto` or `--script`; a bare
> interactive invocation prints a one-line stderr hint pointing at the legacy module.
> *Recommendation:* schedule the streaming app entry as the first post-MVP item
> (P16.5 / front of P19 onboarding).

### 3.2 `explore` — browse the chronicle (the P15 new seam)
```
chronicle-forge explore RECIPE [--format md|json]
```
- → `app.explore_file(RECIPE)`; `--format md` (default) prints `app.chronicle_markdown`;
  `--format json` prints **exactly** `app.chronicle_json` (raw, no framing — machine
  mode; sha == `aa4c67a416178e92` for the seed42 recipe).
- A schema-invalid / version-mismatched recipe surfaces the persistence error as a
  clean stderr message + non-zero exit (no guessing).

### 3.3 `share` — emit a reproducible artifact
```
chronicle-forge share RECIPE [--export FILE]
```
- → `app.share(ShareRequest(recipe=<RECIPE>, export_path=FILE))`.
- **stdout** = `ShareResult.reproducible_command` (contains `--replay`). **stderr** =
  "Wrote transcript to FILE" when `--export` given.

### 3.4 Recipe-path deserialization — the one boundary nuance
`explore` already has `app.explore_file(path)`. `share` / `play --replay` need a
`Recipe` from a path, but `app` exposes only `ShareRequest(recipe=…)`. Two GREEN
options (design decision for review):

- **Option A (recommended): add `app.share_file(path)`** — a trivial additive
  path-overload mirroring `explore_file` (`share(ShareRequest(read_recipe(path), …))`).
  Pure wiring glue: no new truth, no change to existing `share` behaviour, no golden
  impact. Keeps the CLI strictly app-only. *(This is the sole `app` addition P16 needs;
  it is additive, not a spec change — surfaced here for explicit approval.)*
- **Option B:** let the CLI call `persistence.read_recipe(path)` as a pure
  deserialization adapter. Smaller app surface, but loosens "app is the only boundary".

The RED tests below assert **behaviour only** (exit code + stdout/stderr + artifacts),
so they hold under either option; the design recommends **A**.

### 3.5 Exit codes
`0` success · `2` argparse usage error (unknown command / missing required arg) ·
`1` runtime refusal (invalid/mismatched recipe, missing file). `main(argv) -> int`.

---

## 4. Distribution (PyPI / pipx) — design only (pyproject NOT edited in P16)

GREEN-issue `pyproject.toml` delta (shown as a proposal; **not applied here**):
```toml
[project]
dynamic = ["version"]                         # replaces  version = "0.3.0"
# … requires-python, dependencies unchanged …

[project.scripts]
chronicle-forge = "chronicle_forge.cli:main"  # the installable console command

[tool.setuptools.dynamic]
version = {attr = "chronicle_forge.__version__"}   # single source of truth
```
- **Single-source version:** drop the literal `version` from `[project]`; derive it
  from `chronicle_forge.__version__`. MVP bumps `__init__.__version__` to **`0.4.0`**.
- **Build & smoke test (GREEN):** `python -m build` → wheel+sdist; `pipx install
  dist/*.whl`; run `chronicle-forge play --seed 42 --auto` end-to-end; **TestPyPI**
  upload as the publish dry-run. Public PyPI + binary are **P20**, not P16.
- No new runtime dependency: the CLI uses argparse (stdlib) over `app`.

---

## 5. CI (GitHub Actions) — design only (workflow NOT added in P16)

Proposed `.github/workflows/ci.yml` (added at GREEN):
```yaml
name: ci
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python-version }}" }
      - run: pip install -e ".[dev]"
      - run: black --check src tests
      - run: pytest -q
```
- `pytest` already asserts the 8 engine goldens + the chronicle golden, so CI **is** the
  golden tripwire; no extra step needed.
- **Precondition (blocker) — `tests/test_salience.py` is not Black-clean** on `main`
  (a pre-existing formatting drift, unrelated to P15/P16). `black --check src tests`
  would fail CI until it is formatted. *Resolution:* GREEN runs `black tests/test_salience.py`
  as a **behaviour-preserving, golden-neutral** hygiene fix (Black changes whitespace
  only, never the salience golden values). Alternative: scope CI's first run to
  `black --check src` and the new files. *Recommendation:* the one-file format fix —
  it is a no-op for behaviour and unblocks `black --check src tests` permanently.

---

## 6. README — full restructure proposal (README NOT edited in P16)

Replace the stale README. Proposed section order + intent:

1. **Title + one-liner** — keep ("history-creation RPG / reincarnation roguelite").
2. **Install** *(new)* — `pipx install chronicle-forge`; "no API key needed; rules-only
   by default".
3. **Quickstart — the one-way path** *(new, headline)*:
   ```
   chronicle-forge play --seed 42 --auto --save run.recipe   # generate & witness a world
   chronicle-forge explore run.recipe                         # browse the chronicle (P10–P14)
   chronicle-forge share   run.recipe --export run.md         # a reproducible artifact
   ```
4. **Example world (seed 42)** — keep the existing demo-bundle table/links.
5. **Status** *(corrected)* — replace "P0–P5 complete / Next: P4" with the true state:
   engine + AI call-sites + persistence + P8 play + P10–P14 read-models + the P15
   Application Layer; MVP CLI (P16). Remove the false "AI added later" line in
   `__init__`'s docstring (a GREEN doc-only edit).
6. **Determinism statement** *(new, short)* — "a seed+recipe reproduces a world
   byte-for-byte; AI prose, when enabled, is a non-canonical side-channel."
7. **Design** — keep the `docs/design.md` link.
8. **Development** — `pip install -e .[dev]`, `pytest`, `black`.
9. **License** — keep.

---

## 7. v0.4 MVP — Acceptance Criteria (the milestone gate)

MVP is reached (tag `v0.4.0`) when **all** hold (extends
[`release_plan.md`](release_plan.md) §MVP):

- [ ] `chronicle-forge` is an installable console command (`[project.scripts]`),
      runnable without `PYTHONPATH=src`.
- [ ] `chronicle-forge {play,explore,share}` work end-to-end on seed 42, wired **only**
      through `chronicle_forge.app`.
- [ ] `play --seed 42 --auto` stdout transcript sha == `98bea862`; `--save` writes a
      recipe that replays byte-identically.
- [ ] `explore RECIPE --format json` stdout sha == `aa4c67a416178e92`; `--format md`
      is titled and id-free.
- [ ] `share RECIPE --export FILE` writes the artifact and prints a `--replay` command.
- [ ] README + `__init__` docstring describe reality (no "Next: P4" / "AI added later").
- [ ] CI (black + pytest) runs on push/PR and is green, including the golden assertions.
- [ ] Version single-sourced; `__version__ == "0.4.0"`; `pipx install` from TestPyPI works.
- [ ] The 8 engine goldens + chronicle golden are byte-identical; full suite green.

---

## 8. RED plan (this issue)

- Ship this doc + `tests/test_cli_mvp.py` + `tests/test_packaging.py`.
- Every test imports `chronicle_forge.cli` **inside its body**, so each fails with
  `ModuleNotFoundError: No module named 'chronicle_forge.cli'`; the existing 426 tests
  are untouched (nothing imports the missing module at collection). Recipe fixtures use
  the existing `persistence.build_recipe` (no `app`/`cli` import at module top).
- `black --check` clean.

**`tests/test_cli_mvp.py` (CLI behaviour contract):**
1. `cli.main` is callable; `main(["--version"])` → 0, prints `__version__`.
2. `play --seed 42 --auto --save R` → 0; R replays to transcript `98bea862` (oracle).
3. `play --seed 42 --auto` → stdout sha == `98bea862` (stdout = clean transcript).
4. `play --replay R` → stdout sha == `98bea862` (reproduces).
5. `explore R --format json` → stdout sha == `aa4c67a416178e92`.
6. `explore R --format md` → starts with `# `, id-free.
7. `share R --export F` → 0; F written; stdout contains `--replay`.
8. `play --seed 42` (no auto/script) → non-zero / SystemExit (interactive deferred).
9. unknown command → SystemExit / non-zero (exit-code contract).

**`tests/test_packaging.py` (packaging contract, gated behind the `cli` import):**
1. entry-point target `chronicle_forge.cli:main` exists and is callable.
2. `pyproject.toml` declares `chronicle-forge = "chronicle_forge.cli:main"`.
3. version is single-sourced (pyproject `dynamic = ["version"]` + `chronicle_forge.__version__`).

---

## 9. Guardrails

1. **Frozen engine.** 8 goldens (world `e62d8f2c`, replay `98bea862`, observatory
   `f9ad13c7`, social_memory `3fbb1aa0`, world_model `5b41a69`, narrative `a32df9e5`,
   character `36c894fb`, timeline `ae42ed5f`) + chronicle `aa4c67a416178e92`
   byte-identical.
2. **`app` is the only behavioural boundary.** No game logic in `cli.py`.
3. **Additive only.** P16 adds `cli.py` + (recommended) `app.share_file` + pyproject
   entries + CI + README; it changes no existing behaviour.
4. **Determinism preserved.** stdout transcripts stay byte-deterministic.

---

## 10. File structure

```
NEW (this RED issue):
  docs/design_p16_mvp_cohesion.md        (this doc)
  tests/test_cli_mvp.py                   (failing — ModuleNotFoundError until GREEN)
  tests/test_packaging.py                 (failing — ModuleNotFoundError until GREEN)

NEW / EDITED (later GREEN issue, NOT here):
  src/chronicle_forge/cli.py              (thin wrapper over chronicle_forge.app)
  src/chronicle_forge/app/services.py     (+ share_file path-overload — Option A)
  pyproject.toml                          (+[project.scripts], dynamic version)
  src/chronicle_forge/__init__.py         (__version__ → "0.4.0"; docstring fix)
  .github/workflows/ci.yml                (black + pytest)
  README.md                               (full rewrite per §6)
  tests/test_salience.py                  (black format only — CI precondition)

UNTOUCHED (hard constraints): the engine, World, Recipe, RNG, persistence, reporting
  (P10–P14), the P15 app behaviour, and every existing golden.
```

## 11. P16 → v0.4 process

1. GREEN-A **CLI**: add `cli.py` (+`app.share_file`); make `test_cli_mvp` green.
2. GREEN-B **Packaging**: pyproject `[project.scripts]` + dynamic version; `__version__
   → 0.4.0`; make `test_packaging` green; `pipx install` smoke test (TestPyPI).
3. GREEN-C **CI**: format `test_salience.py`; add `ci.yml`; confirm green on a PR.
4. GREEN-D **Onboarding**: rewrite README + fix `__init__` docstring.
5. **Gate**: §7 Acceptance Criteria all checked → tag `v0.4.0` (MVP).
