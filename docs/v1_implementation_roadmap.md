# Chronicle Forge v1 — Definition of Done & Implementation Roadmap

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
protocol: SC-1 ≥4/5 recognize ≤30:00 with ≥3/5 via the earned (hold) path ·
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
| I-3 | Skip & rebirth | P-09/P-10/P-11; rebirth-digest read-model lens (new, golden-pinned); map plate with mark accumulation | Death→digest→map cycle E2E; lens golden green; engine goldens untouched | Opus (lens contract) + Sonnet |
| I-4 | Ending & trace | P-12/P-13/P-14/P-15; trace composition over `trace_to_roots` (+ P18 lens work where it composes); rubric line; D-06 single seeded confirm | Trace chain walkable on tutorial + ≥3 generated seeds | Sonnet, Opus review |
| I-5 | Tutorial pack | Authored canon (JP copy from voice guide) wired for all 3 branches; recognition staging incl. fallback + backstop (JN-5); asides ✎#1–#3 | DoD-3 driver passes ×3 | Sonnet (integration), owner (JP copy review), Ornith (mechanical copy transforms), audits via local lane |
| I-6 | Standard worlds & state | Curated seed shelf per D-5; discovery-state store + save/resume per D-6; epithets | DoD-4/DoD-5/DoD-6 tests green | Opus (state store) + Sonnet |
| I-7 | Hardening & release | JP audit lane wired to CI; packaging (PyInstaller, per-OS); cross-machine determinism script; a11y floor (scaling, reduced-motion, rubric) | DoD-2/7/8/9 green on RC | Sonnet + Haiku (chores), Ornith (repetitive fixes), lead sign-off |

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
