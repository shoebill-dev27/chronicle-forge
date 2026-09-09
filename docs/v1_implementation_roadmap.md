# Chronicle Forge v1 — Definition of Done & Implementation Roadmap

> **2026-09-06 UI/UX review · 2026-09-08 baseline ratified.** Every date in this
> document is a **historical target**, not a renewed release commitment. The
> [UI/UX direction review](design_v1_uiux_review.md)'s change ledger is now
> **adopted** as [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md)
> (all ten items; UX-R1/UX-R5 with modification) and **ADR-005** defers the
> geographic Map past v1. The next implementation unit is the **Discovery
> Vertical Slice (DVS)** — §2e below — which replaces the old I-4/I-5/I-6 order.
> Owner has approved: ADR-005; front-loading the minimum persistence /
> read-only archive / accessibility floor; 朱 = confirmed past-life connection;
> authored Japanese presentation templates over real reached-world facts.

Status: **Active plan.** Owner-ratified decisions: ADR-001 (Living Chronicle /
Dual Canon / ◦ cut / Must-only scope), ADR-002 (pywebview stack), ADR-003
(Japanese-first). Dates: target **2026-08-16**, committed fallback
**2026-08-23**. Quality bar (owner): *"a game a general player can complete
from beginning to end while experiencing the intended emotional arc"* — if
the experience is compromised, we slip to the fallback, we do not cut quality.

This document supersedes the schedule/DAG sections of
`v1_execution_plan.md` where they differ (language, cut list); everything
else there remains in force.

> **Design Lock: CLOSED — declared by owner 2026-07-24.** I-0 (Lock closeout)
> is complete: ADR-001/002/003 committed; M-1 measured; D-3/D-4/D-5/D-6 drafted,
> cross-checked (zero ADR/UX contradictions), and accepted. Exit criteria
> EL-1..6 (see the Design Lock Review Pack) are satisfied. Gate-decision
> dispositions carried into the build: **OD-8 (縦/横書き)** — 横書き is the
> working default, bound to the **7/27 skeleton go/no-go** for the final call;
> **OD-9 (Hand face)** — selected from OFL candidates evaluated on the skeleton
> (Print face = Noto Serif JP, OFL, already de-risked). Soft owner decisions
> (register/pronoun/reveal-grammar/name-table/etc.) are deferred as non-blocking,
> due at I-5 copy authoring. D-5 (Q-SW-1..4) and D-6 (Q-CS-1..4) proposed rulings
> accepted. **Post-lock, non-gating:** JP tester recruiting (release-readiness,
> DoD-1) and D-7 wireframes. **Implementation increment I-1 (walking skeleton)
> is now open.** No engine change; the 8 frozen goldens + chronicle/transcript
> hashes remain the guardrail across every increment.

---

## 1. Definition of Done (v1) — objective criteria only

v1 is DONE when every box below is checkable by a named, repeatable
verification. No aspiration language.

**DoD-1 · Experience gate (the only subjective-input gate, objectively
scored).** An R2 cohort of 5 fresh Japanese testers (profiles per
`v1_tutorial_world_proof.md` §4.2) passes all four bars under the §4.3
protocol: SC-1 ≥4/5 recognize ≤30:00 with ≥3/5 via the **earned path — player-initiated
recognition supported by an explanation** (baseline UX-R9; visible-button or
keyboard inspection counts equally, a completed hold is only an interaction
event, a fallback reveal is recorded as assisted exposure, and delivered digest
comprehension alone never passes this bar) ·
SC-2 ≥4/5 · SC-3 ≤1/5 loss-coded and 0 restart attempts at death · SC-4 ≥3/5
name a different intended mark. *Verification: filled scoring sheets, one per
tester.*

**DoD-2 · Engine integrity.** The 8 frozen engine goldens, chronicle
`aa4c67a416178e92`, and replay-transcript `98bea8622c686d8e` are
byte-identical; full `pytest` green; `black --check` clean; canonical
save/replay byte-identical. *Verification: CI run on the release candidate.*

**DoD-3 · Tutorial completeness.** All three tutorial branches (JN-2 options)
complete end-to-end in the book client without crash, with every B0–B18 beat
reachable, via an automated driver AND one manual pass each. *Verification:
scripted E2E run ×3 + checklist.*

**DoD-4 · Standard worlds.** ≥30 fixed seeds run new-book → lives → ending →
trace-walk in the client without crash; every offered mark resolves to a real
engine ancestry (zero orphan marks); the recognition floor defined in the
Standard-World Spec (D-5, from M-1 data) is met by the shipped seed shelf.
*Verification: seed-matrix script + shelf manifest check.*

**DoD-5 · Dual-canon boundary.** Automated check: no tutorial content ID
(EV/JN/OP/TR/DG/CH) is reachable from any generated world; no generated-world
surface contains authored-canon text. *Verification: boundary test in CI.*

**DoD-6 · Discovery-state correctness.** Reveal state is permanent within a
world (D-04), survives quit/resume at every resumable state defined in the
Client State Spec (including mid-juncture selection and mid-trace), and never
alters canonical world data. *Verification: state-machine test suite.*

**DoD-7 · Copy & audit.** All shipped JP copy passes the JP audit set
(attribution/second-person audit on non-Confirm surfaces; character budgets;
⟜/❧-only glyph usage; name-table conformance). Zero waivers. *Verification:
audit lane report, clean.*

**DoD-8 · Determinism.** A recipe reproduces its world byte-identically on a
second machine; the shelf's books reopen to identical content across
reinstall. *Verification: cross-machine reproduction script.*

**DoD-9 · Packaging.** The client installs and runs on clean Windows and
Linux machines from the release artifact (per-OS smoke test); version tagged;
`CHANGELOG.md` updated. *Verification: fresh-VM smoke checklist.*

**DoD-10 · Governance.** ADR-001/002/003 are reflected in the shipped build;
no open BLOCKER-severity issue; the SoT docs match shipped behavior (small
corrections applied, no orphan design).

---

## 2. Implementation increments (PR-sized, in dependency order)

Routing per the delegation policy (Fable = lead: architecture/product/review;
Opus = hard implementation & code review; Sonnet = normal implementation,
tests, docs; Haiku = small maintenance; Ornith = mechanical/deterministic,
always lead-reviewed).

| # | Increment | Contents | Exit test | Routing |
|---|---|---|---|---|
| I-0 | Lock closeout | DR-pass merged; ADRs committed; client-state spec (D-6); JP voice guide + name table + visual guide (D-3/D-4, incl. Q-UX-5 JP legibility check); standard-world spec (D-5 ← M-1) | Design Lock declared; no BLOCKER open | Lead + Opus (D-6, D-5), Sonnet (D-4 draft), owner reviews JP voice guide |
| I-1 | Walking skeleton | pywebview shell; bridge to `app` JSON; page frame with print/Hand JP typefaces; verbs turn/flip/seal/hold; 3 pages (P-01 stub, P-04, P-06) | Two-typeface juncture page renders; hold fires a stub reveal; **ADR-002 go/no-go 7/27** | Opus (bridge + state machine) + Sonnet (pages) |
| I-2 | Life loop | P-05/P-07/P-08 + S-03 plant cue + marks rendering + seal ceremony | A full life playable start→death on tutorial data | Sonnet, Opus review |
| I-3 | Skip & rebirth | P-09/P-10 (~~P-11~~ retired, ADR-005); rebirth digest built in `play/beats.py` (not a `reporting/` lens — see §2d) | Death→digest→next life E2E; engine goldens untouched | Opus + Sonnet — **DONE** |
| ~~I-4~~ | ~~Ending & trace~~ | **Folded into the DVS (§2e)**, scoped down to *one* trace thread on one seed over an ordered real edge path | see §2e exit criteria | — |
| I-5 | Tutorial pack | Authored canon (JP copy from voice guide) wired for all 3 branches; recognition staging incl. fallback + backstop (JN-5); asides ✎#1–#3 | DoD-3 driver passes ×3 | Sonnet (integration), owner (JP copy review), Ornith (mechanical copy transforms), audits via local lane |
| I-6 | Standard worlds & state | Curated seed shelf per D-5; epithets. **The D-6 minimum (atomic `{sealed inputs, reveal set, cursor}` + exact resume + hash gate) moves forward into the DVS (§2e, baseline UX-R8);** the full productised version stays here | DoD-4/DoD-5/DoD-6 tests green | Opus (state store) + Sonnet |
| I-7 | Hardening & release | JP audit lane wired to CI; packaging (PyInstaller, per-OS); cross-machine determinism script. **The a11y floor (keyboard parity, reduced motion + static equivalents, text scaling, skip) moves forward into the DVS (§2e, baseline UX-R9);** what remains here is CI wiring and packaging | DoD-2/7/8/9 green on RC | Sonnet + Haiku (chores), Ornith (repetitive fixes), lead sign-off |

### 2b. Amendment after X-1..X-4 (2026-08-17)

The first-loop review ([`review_x1_x4_first_loop.md`](review_x1_x4_first_loop.md))
adds one **prerequisite to I-2**, ahead of any page work:

> **I-1b — structured beat stream.** Replace `client/bridge.py`'s
> `capture_first_juncture` + `_OPTION_RE` (a regex over `play/render.turn_screen`'s
> printed text) with a generator of typed beats — `juncture | death | years |
> aftermath | rebirth | recognition | closing` — carrying data, not rendered text.
> **Exit test:** the client advances a world past its first juncture without
> parsing any prose, and `remember()` returns `None` when the engine has no
> recognition to give.

Why it moves first: `eca81f1` rewrote 299 lines of `turn_screen`/`death_passage`
and the regex seam survived only by luck; I-2, I-3 and I-4 each add beats that
seam cannot express; and every UI direction under consideration depends on it.
It is also the only item in the prototype scope that is real engineering rather
than a view.

**Implemented 2026-08-18** — see [`design_v1_i1b_beat_stream.md`](design_v1_i1b_beat_stream.md).
`play/beats.py` (typed stream) + one optional `observer` on `run_human_world`
(transcript byte-identical for all five seeds, so no golden, no `ENGINE_VERSION`
and no replay gate is in play). `client/bridge.py` no longer imports `re`;
`book.js` reads fields. The shipped beat set is **six**, not seven: recognition
is not a beat of its own — it only ever happens at a juncture, so it rides on the
juncture beat and names the option that carries it, which is what stops the page
marking a line no former self ever touched. Both exit tests pass: the client
advances past its first juncture without parsing prose, and there is no
`remember()` left to return a stub — recognition is `None` in every life-1
juncture of every measured seed, and the page draws no mark there. The Time
Surface (C1 strata) ships with it as `client/web/time.js`.

**Prototyped 2026-08-18.** The I-1b shape was first validated against real seeds by
`docs/mocks/v1_time/beats.py`, which taps the real call sites without touching
the engine (transcript and beat-stream hashes verified identical). The beat set
below is the one that survived: `rebirth | juncture | death | years | aftermath
| recognition | closing`. The B3/B4 visual direction it fed is decided in
[`design_v1_time_surface.md`](design_v1_time_surface.md) (C1 "strata").

Two further notes for I-3, **both now closed by the I-1b implementation**: the
years beat used to render as a single line (`… 8 years pass …`), the narrowest
point in an otherwise closed loop — it is now the Time Surface, and the skip's
events are its content. And the client's Hand reveal was a hard-coded string
shown at life 1 year 0, where the engine can produce no recognition; it is
deleted, not re-skinned, and `test_the_frontend_carries_no_world_copy_of_its_own`
keeps it deleted.

### 2c. G0 and I-2 (2026-08-21)

**G0 — the real-hardware gate. PASSED**, seeds 1/7/42/99/123, 0 failures. Every
judgement from I-1 to I-1b had been taken in headless Chrome; the client had
never run in the pywebview window it ships in. It does — canvas, both bundled
faces, the 1180×880 viewport and the whole loop. Re-runnable:
[`v1_g0_hardware_gate.md`](v1_g0_hardware_gate.md). The gate immediately earned
itself by catching a page that read ahead of its player (gate doc §4).

**I-2 — Life Loop. Implemented**, see
[`design_v1_i2_life_loop.md`](design_v1_i2_life_loop.md). One new beat
(`outcome`: what the sealed act did, with a measured count of what it planted)
and one new page: P-05 and P-07 ship as a single leaf — the acts of this life,
with the newest arriving in the Hand — carrying S-03's cue and its ⟜. The shelf
stops being a stub. X-16 and X-17 ride the same transcript-golden move
(`c9a8096f6b83795c` → `41cf1cfd843f6272`; the world golden does not move).

Two items the roadmap should carry forward from it: the plant cue's condition is
**always true** in the current engine (every act plants exactly one guaranteed
seed — an engine-content finding, not a client one), and the leaf is mostly
empty because a life is 1–3 acts and nothing else. Both point at the same
content floor W-1 names.

Not done here: I-4 (folded into the DVS), I-5, I-6, I-7.
**P-11 is retired for v1 — ADR-005** (2026-09-08); it is no longer "not done", it
is out of scope until W-1.

### 2d. I-3 (2026-08-27)

**I-3 — Rebirth Digest (P-10). Implemented**, see
[`design_v1_i3_rebirth_digest.md`](design_v1_i3_rebirth_digest.md). The loop now
closes: surface → digest → the next life. The `aftermath` beat carries
`changes`, the years' work grouped by the act behind it and cut to three in the
stream, and the page renders that tuple and reasons about nothing.

The increment turned out to be **P-10 alone**, on measured grounds:

- **P-09 was already shipped** as the C1 Time Surface (§2b).
- **P-11 is blocked, provably.** `location_id` is null on 0 of 301 causal nodes
  across seeds 1/7/42/99/123 — every event in this engine is placeless, so a map
  plate would be invented geography. It waits on **W-1**, not on view work.
- The roadmap's "read-model lens" wording (§2) predates I-1b and no longer
  holds: a `reporting/` lens cannot see the label the player *sealed an act
  under*, only the world's own phrase for it. The digest is built in
  `play/beats.py`, where the causal graph, the seed ids and the sealed labels
  are all in hand, and `reporting/` stays untouched.

Two findings worth carrying forward. **SP-1 is loop-guaranteed on real data**:
across all 30 worlds of seeds 1–30, every first rebirth delivers a non-empty
digest containing at least one line whose act the player sealed themselves — no
staging, no engine change. And **`hardened` is not a digest input**: none of 229
hardened marks in those worlds was founded by the life that just died, so
delivering any of them would break D-03. They stay the map's unexplained older
marks, which is I-4's material and not I-3's.



### 2e. The Discovery Vertical Slice (DVS) — the next implementation unit (2026-09-08)

Replaces the old I-4 → I-5 → I-6 order as the *next* thing built. Rationale and
full contract text: [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md) §5.

**The slice is one complete playable sequence on one generated seed:**

> readable choice → recorded act → death → years → return → later investigation
> → ending → reopen

**Start state.** The I-1b/I-2/I-3 tree committed as the base; the baseline ledger
merged into the SoT (this pass); ADR-005 ratified; no interface teaching a removed
feature (◦, map, 朱-as-still-shaping, hidden-only hold); authored Japanese
presentation copy for a small set of *real* choices; engine untouched (8 frozen
goldens + chronicle `aa4c67a416178e92` + transcript `98bea8622c686d8e`).

**Contracts (specified with the build).**

| ID | Contract | Home |
|---|---|---|
| C-1 | Choice content: target, role/affiliation, current condition, immediate action — every clause sourced in reached world data; a missing world fact is escalated, never invented | `play/beats.py` + presenter seam |
| C-2 | Sealed-act identity: the original displayed label/text of every sealed act, carried on digest lines and recognition, stable across surfaces and resume | `play/beats.py` (`BeatRecorder._sealed`) |
| C-3 | Ordered causal path: a concrete list of existing edges consequence→origin + honest alternate-cause disclosure; an ancestor count is never a path | app/trace composition over `trace_to_roots` |
| C-4 | Discovery-state surface: one knowledge-state enum honoured identically by entry, time surface, digest, history, trace, resume; SR text + focus carry the glyph's meaning | `client/web/*.js` |
| C-5 | Persistence (D-6 minimum): atomic `{sealed inputs, reveal set, cursor}`, exact resume, canonical-hash trust gate | new client-persistence module (ADR-002) |
| C-6 | Autonomous/authored separation: a flag on every displayed act line; the Hand is reserved for sealed acts and confirmed recollections | `play/beats.py` + renderers |

**Exit criteria.** One generated seed completes all eight beats **including a
quiet interval** (a zero-juncture life and/or an empty-echo skip) with no crash
and no fabricated content; a reader can say what each option *does now* before any
outcome; the sealed act is written in the Hand and persisted; return shows the
changed present first and then one emphasized `(sealed act → consequence)` line
(≤3 total); investigation is reachable by visible affordance **or** keyboard **or**
optional hold and walks a real ordered edge path to the origin's exact sealed
wording; player-sealed / autonomous / contributing-cause are visually distinct;
the ending offers 「歴史を読み返す」/「本棚へ」 and closes honestly (recording a
content-gate miss) when no valid legacy exists; quit/reopen restores sealed
inputs, reveal set, cursor and any confirmed trace; same-seed/different-choice
books never share reveals; keyboard cannot double-advance or double-commit;
reduced motion, skip and text scaling work from the first world.

**Guardrail.** No engine, worldgen, RNG, canonical-recipe or `reporting/` change.
Changes are confined to `client/web/*`, `play/beats.py` (+ its app seam), and the
new client-persistence module.

Playtests interleave: **R0 table read** (JP page cards) as soon as I-0's JP
golden-path copy exists; **R1** on I-5's build; fix cycle; **R2** on the RC.

## 3. Schedule (updated for ADR-003)

| Date | Milestone | Exit |
|---|---|---|
| 7/20 | Kickoff (today) | Baseline committed; ADRs in; DR-pass + M-1 delegated; **JP recruiting starts (owner, human-only, critical path)** |
| 7/23 | **Design Lock** | I-0 complete: guides (JP), D-5, D-6 done; DR-pass merged |
| 7/24–25 | R0 table read (JP) | Copy/beat findings filed; earned-path staging probed |
| 7/27 | ADR-002 go/no-go | I-1 skeleton proves the stack (else fallback mode) |
| 7/30 | Alpha | I-2+I-3 golden path E2E, prototype fidelity |
| 8/2–3 | R1 (5 fresh JP) | SC bars scored; triage same day |
| 8/7 | Content freeze + checkpoint | R1 fixes in (non-structural); nothing re-added unless green |
| 8/9–10 | **R2 / release gate** | DoD-1; fail → same-day owner slip call (→ 8/23) |
| 8/11–15 | RC hardening | DoD-2..10 all green |
| **8/16** | Ship | Tag + release (owner approval for any publish/push) |

JP note vs. the old plan: copy authoring (I-5) is now owner-reviewable
natively — lower voice risk, but the JP typography work (D-4) moves *ahead*
of I-1's typeface choice; that is why D-3/D-4 sit inside Design Lock.

## 4. Standing rules for the build

- Every merged chunk: goldens + pytest + black (CI) and a lead review — no
  agent approves its own work; Ornith output is always reviewed before merge.
- New read-models are additive lenses with their own goldens; existing golden
  hashes never move (inherited guardrail).
- Scope: anything not serving the North Star is postponed on sight; the cut
  list (ADR-001 §4) is closed — re-adds only at the 8/7 checkpoint, only if
  green.
- Design docs are frozen post-Lock except small corrections; anything
  architectural becomes an ADR.
