# Chronicle Forge v1 — Execution Plan (Design → Implementation Transition)

Status: **Plan / for owner ratification. No code changes.**
Author: Design Lead / Tech Lead. Date: 2026-07-20. Release target: **2026-08-16**
(pre-agreed fallback proposed: 2026-08-23, see §9).
Inputs: the five SoT docs, plus five independent delegate reviews (Gameplay
Designer [Opus], Narrative Designer [Sonnet], Engine Architect [Opus, code-
grounded], UX Designer [Sonnet], Producer [Sonnet]) — findings integrated
below; full reports in the session record.

---

## 1. Design Completeness Verdict

**The design is NOT complete for implementation start.** The tutorial world is
over-specified relative to the game around it. Consolidated verdict from five
lenses:

### 1.1 Blocking gaps (must close at Design Lock — §7 M1)

| ID | Gap (source) | Resolution path |
|---|---|---|
| B-1 | A-1 unresolved; and the tutorial canon (54-year skip, year 803, authored junctures, ◦ lineage memory) is **outside the engine's generation envelope** (`MAX_SKIP=8`, 200-year span, tension-driven junctures, no persisted lineage memory) — Engine review A-6/A-7/A-8 | **Decided §3 (A-1 = curated) + ADR-001 two-canon boundary + design revision DR-2/DR-3** |
| B-2 | Standard worlds (world 2+) undesigned: length, digest rule, recognition floor — a generated world can produce **zero recognitions** and nothing bounds it (Gameplay G1/G2) | New deliverable **D-5 Standard-World Experience Spec**, fed by a measured recognition-rate study over N seeds (§5) |
| B-3 | JN-5 (all-marked backstop) contradicts D-07's letter ("never manufactures extra marked junctures") — UX U1 | DR-1: explicit tutorial-exception clause in D-07 |
| B-4 | Save/resume state undefined (mid-juncture, mid-trace) **and** no home exists for permanent-once-earned discovery state — engine read-models are stateless by design (UX U2 + Engine risk 2) | New deliverable **D-6 Client State Spec** |
| B-5 | Voice & copy style guide missing while branch copy, UI strings, glyph key, epithets are about to be written (Narrative N1) | **D-3**, unblocked by Q1/Q2 decisions (§3) |
| B-6 | Q-UX-2 (flip-back depth) and Q-UX-10 (accessibility floor) block implementation start (UX triage) | Decide at Design Lock (recommendations: full-depth flip-back; accessibility floor = Must at text-scaling + reduced-motion, colorblind-safe rubric; controller = non-goal) |

### 1.2 Should-fix (scheduled, non-blocking)

- **S-1** Earned-recognition path is the knife-edge (Gameplay top risk; F6): prove ≥3/5 earned in R0/R1 **before** structural UI investment hardens; pre-authorize the F6 fix ladder.
- **S-2** ❧ lacks a teaching phrase at first use (N2) — add one line to the JN-4 staging in DR-4.
- **S-3** JN-2 second-person copy breaks the historian's register and the "you/your only on Confirm surfaces" audit rule (N3) — fix copy, keep the rule.
- **S-4** Name audit renames: Undermount (Undermountain collision), Aldis (Aldis-lamp pun), Brant Ford (Brantford) — DR-5.
- **S-5** Fallback bloom "holds the page until input" not yet in UX spec (U4/Δ4); P-07/P-08 cross-reference error (U5); "6 keys" claim vs table (U3); I-05 on already-revealed marks (U6) — DR-6 batch.
- **S-6** Word-count self-reports unreliable (N5) — mechanize budgets (local LLM/Haiku audit, §6).
- **S-7** UI-string/glyph-key/settings/epithet copy volume unestimated (N4) — estimate inside D-3.

### 1.3 Explicitly accepted (not gaps for v1)

Retention past world ~3 (Gameplay G8 — a hook release, by scope); SC-gate tests
the hook not the whole game (G5 — mitigated by D-5 + post-v1 studies); verb
thinness at scale (G3/G4 — D-5 must address the dead-spot question, further
depth is post-v1).

---

## 2. Decision Framework (which lens decides what)

- **Q1** is decided by *design integrity + schedule*: does the presentation
  serve the North Star, and can it ship? (Gameplay + Producer + UX lenses.)
- **Q2** is decided by *voice quality + validation cost*: the product is prose;
  a language is a full copy pass **plus** a full fresh-cohort playtest
  duplication. (Narrative + Producer lenses.)
- **A-1** is decided by *engine reality + fiction integrity*: what the engine
  can generate (Engine lens, code-grounded) vs. what "never fabricate history"
  permits (Gameplay lens).

## 3. Decisions (recommended — require owner ratification at Design Lock)

**Q1 — ADOPT the Living Chronicle, formally. (5/5 delegates concur.)**
The book makes the core verb native rather than bolted-on; it is the only
direction with a plausible solo 4-week path; the reader-gamer repositioning is
accepted with eyes open (a positioning risk, not a design-integrity one).
Ratified via **ADR-001**.

**Q2 — English-only at launch; Japanese as a properly-scoped v1.1. (unanimous
among reviewers who took a stance.)** Two branch paths, UI strings, glyph key,
and epithets are still unwritten in *one* language; the print/Hand device in
Japanese (明朝/行書) is design work, not translation (Q-UX-9); and each
language doubles the release gate's fresh-cohort requirement. A week-4 rush
translation cannot preserve a specified voice. JP begins when D-3 exists and
v1 has shipped.

**A-1 — CURATED tutorial (mode b), decisively — with a hard integrity
boundary. (5/5; Engine review makes seed-search near-impossible: three
invariants depend on artifacts the engine never emits.)**
Design Lead ruling on the fabrication question (reconciling Gameplay's
"forward-simulate everything" line with engine reality):

> **The two-canon model.** The **Tutorial World** is a fully *authored canon*:
> its causal chain is hand-written, internally consistent, and rendered
> through the same book UI — a scripted first level, honest as fiction
> (every connection the player discovers is really in the canon; D-08 holds
> *within* it). **Generated worlds** (world 2+) are **100% engine truth**:
> every mark, digest line, and trace chain derives from engine data; no
> authored overlay, ever. The boundary is fixed in ADR-001 and is
> non-negotiable: authored content may never be blended into a generated
> world, and no generated world may be edited to "improve" its history.

Consequences (design revisions, §4): the ◦ memory glyph **is cut from v1**
(the engine cannot generate remembering lineages — witnesses die in skips,
lineage is unused; teaching a glyph in the tutorial that generated worlds can
never honor would break the mark vocabulary's trust). v1 ships **two glyphs:
⟜ and ❧**. Tutorial content re-authored accordingly (DG-2 and OP-6A become
❧/⟜ per the already-sketched A-6 mitigation). "Remembers you" tags (Should)
are cut with it — consistent with the Producer's scope surgery.

**Scope surgery (Producer, adopted):** cut today — Threads spread (P-16),
world sharing, sound direction, portrait plates, "remembers you". One Should
survives on probation: none. v1 is **Must-only by default**; anything added
back requires the 8/7 checkpoint to be green.

## 4. Design Revision Pass (DR-1…DR-7 — closes §1 gaps in the SoT)

One batched editing pass over the SoT docs at Design Lock: DR-1 D-07 tutorial
exception (B-3) · DR-2 two-canon statement + tutorial-canon note that its
timeline is authored fiction (B-1) · DR-3 glyph set reduced to ⟜/❧; re-author
DG-2, OP-6A, S-01 glyph key; icon budget updated (B-1) · DR-4 ❧ teaching
phrase at JN-4 (S-2) · DR-5 renames: Undermount→(e.g.) *Wellmount*,
Aldis→*Old Berta* or similar non-colliding, Brant Ford→(e.g.) *Bran Ford*
alternative — final names bound in D-3 (S-4) · DR-6 UX spec batch: Δ4
hold-until-input, P-07/P-08 cross-ref, key-count claim, I-05 re-hold = brief
re-bloom (S-5) · DR-7 record Q-UX-2/10 decisions (B-6).

## 5. Implementation-Phase Deliverables, Owners, and Models

Model policy (per dev-workflow): design/architecture/review on **Opus**;
scoped feature work on **Sonnet**; mechanical work on **Haiku**; deterministic
lint-style audits on the **local LLM**; synthesis and final review stay with
the Lead. Human-only: approvals, recruiting, store/publishing acts.

### 5.1 Design-completion deliverables (this week)

| ID | Deliverable | Owner (model) | Why this model |
|---|---|---|---|
| D-1 | ADR-001 (Living Chronicle + two-canon + A-1) & ADR-002 (UI stack choice) | Lead drafts; **human ratifies** | Architectural decisions; approval is policy-reserved to the owner |
| D-2 | DR-1…DR-7 SoT revision pass | **Opus** | Touches discovery rules — mistakes are expensive; review-tier work |
| D-3 | Voice & copy style guide (incl. UI-string inventory + epithet table) | **Opus** draft, Lead review | The anti-drift instrument for all future copy; highest-leverage prose rules |
| D-4 | Visual style guide / art direction (type faces, ink palette, motion) | **Sonnet** draft, **Opus** review | Reference-driven synthesis; binding rules get top-tier review |
| D-5 | Standard-World Experience Spec (world length, digest rule, recognition floor, curated-seed shelf policy) | **Opus**, fed by M-1 | New game design closing BLOCKER B-2 |
| M-1 | Recognition-rate measurement: run play→explore over N≥30 seeds, tabulate legacy re-offer / trace-chain availability | **Sonnet** (scripted runs + tables), Lead interprets | Mechanical execution with light judgment; analysis stays top-tier |
| D-6 | Client State Spec (save/resume states incl. mid-juncture; discovery-state store; determinism reconciliation) | **Opus** | Architecture-adjacent; Engine review's risk 2 |
| D-7 | Remaining wireframes (P-03, P-05, P-11) + map & ending spec completion | **Sonnet** | Extension of existing patterns |
| D-8 | R0 table-read kit (page cards from canon) | **Haiku** | Pure assembly from existing content |

### 5.2 Build deliverables (weeks 2–4)

| ID | Deliverable | Owner (model) | Why |
|---|---|---|---|
| I-1 | Book UI scaffold: spine/page state machine, turn/flip/seal/hold verbs | **Opus** design + **Sonnet** build, Opus review | The one tricky UI core; everything else composes onto it |
| I-2 | Pages P-01…P-15 to spec | **Sonnet** (parallelizable per page) | Well-scoped implementation against a written spec |
| I-3 | Tutorial content pack integration (authored canon, both renamed branches) | **Sonnet** | Content plumbing against D-6/I-1 contracts |
| I-4 | New read-models: rebirth digest lens; mark/trace composition for generated worlds (contract first) | **Opus** contract, **Sonnet** build | New lens contracts must respect frozen goldens; P18 RED tests + `trace_to_roots`/`heritage_name` already exist to compose |
| C-1 | Branch copy ×2 at full depth | **Sonnet** draft from golden-path template | Structure-bound prose; voice guide + audits catch drift |
| C-2 | UI strings, glyph key, settings, epithets | **Sonnet** | Guide-bound short copy |
| A-1a | Copy audits: "you/your on Confirm surfaces only", word budgets, glyph/name consistency | **Local LLM / Haiku** | Deterministic, grep-shaped, high-frequency — cheapest tier (S-6) |
| T-1 | Test strategy + suites: 8 engine goldens byte-identical, new-lens goldens, UI state-machine tests, save/replay determinism, 3-branch tutorial E2E | **Opus** strategy, **Sonnet** tests | Gate-defining artifact; execution is scoped |
| P-1 | Playtest ops: recruiting (12–13 fresh, profiles per §4.2 of the proof), scheduling, moderation | **Human only**; scripts by Sonnet | External human contact cannot be delegated |
| R-1 | Packaging/release engineering (PyPI + binary; CI matrix — extends v0.4.0 infra) | **Sonnet** | Established pattern from P16 |
| A-2a | Art assets: 2 glyph marks, map illustration, paper/ink treatment, type licensing | **Human** with LLM support | Asset creation/licensing is human-owned |

## 6. Implementation DAG

```
                      ┌──────────────────────────────────────────────────────────┐
 D-1 ADRs (owner) ──▶│ DESIGN LOCK M1 (7/23): D-2 DR-pass · D-3 voice · D-4 visual│
 Q1/Q2/A-1 ratify    │ D-5 std-world (◀ M-1 measurement) · D-6 client state · D-7 │
                      └───────┬───────────────┬───────────────┬─────────────────┘
        P-1 recruiting (starts 7/20, human, runs parallel)     │
        D-8 R0 kit ─▶ R0 table read (7/22–24)                  │
                              │               │                │
                     I-1 UI core (◀ D-6, ADR-002)   C-1 branch copy (◀ D-3, DR-5)
                              │               │                │
                     I-2 pages P-01..P-15 ◀───┘        A-1a audits (continuous)
                              │                                │
                     I-3 tutorial pack ◀── C-1, C-2            │
                              │                                │
                     I-4 read-models (◀ D-5) ──▶ standard worlds
                              │
                    ══ ALPHA M2 (7/29): golden path E2E; branches by 8/1 ══
                              │
                    R1 playtest M3 (8/2–3) ◀── P-1 cohort ready
                              │
                    fix cycle (non-structural; F6 ladder pre-authorized)
                              │
                    ══ CONTENT FREEZE M4 (8/7) + scope checkpoint ══
                              │
                    R2 / RELEASE GATE M5 (8/9–10) ── fail ▶ owner slip decision same day
                              │ pass
                    R-1 packaging + smoke ──▶ SHIP M6 (8/16)
```

Critical path: **ADR-002 → D-6 → I-1 → I-2 → I-3 → Alpha → R1 → fixes → R2 →
ship** (~28 days, no slack). Everything else is parallel or feeding.

## 7. Milestones & Schedule (2026-07-20 → 08-16)

| # | Date | Milestone | Exit criteria |
|---|---|---|---|
| M0 | **7/20** | Kickoff | Recruiting live (over-recruit +50%); owner ratifies Q1/Q2/A-1 + fallback date; ADR-002 stack decision made |
| M1 | **7/23** | **Design Lock** | D-1…D-7 done; DR-pass applied to SoT; R0 kit ready; no BLOCKER open |
| — | 7/22–24 | R0 table read | 2–3 people; copy/beat-order findings filed (earned-path staging probed — S-1) |
| M2 | **7/29** | Alpha (playable loop) | Golden path E2E at prototype fidelity; both branches by 8/1; R1 cohort confirmed |
| M3 | **8/2–3** | R1 playtest | 5 fresh; SC bars scored; F-signals logged; fix list triaged same day |
| M4 | **8/7** | Content freeze | R1 fixes in (non-structural only); scope checkpoint (nothing re-added unless green); near-final build |
| M5 | **8/9–10** | **R2 / Release gate** | All 4 SC bars pass (§9). Fail → owner slip decision that day |
| M6 | **8/16** | Ship | Packaging verified on a fresh machine; tag cut |

## 8. Delegate Plan (during build)

- **Per-deliverable delegation** with self-contained specs (files, acceptance
  criteria, verification command), per dev-workflow. Lead reviews all
  delegated output; no agent approves its own work.
- **Standing lanes:** Sonnet build lane (I-2 pages in parallel batches; C-1/C-2
  copy); Opus lane (contracts, I-1 core, reviews); Haiku/local audit lane
  (A-1a on every copy/content change — runs as a checklist, not a hook, until
  the owner opts to automate).
- **Review cadence:** every merged chunk gets a Lead review pass; golden-hash
  + pytest + black are the mechanical floor on every chunk (existing CI).

## 9. Risks (merged, ranked) & Release Criteria

### Risks

| # | Risk | P×I | Mitigation | Owner |
|---|---|---|---|---|
| R1 | UI core misses 7/29 (greenfield client tier — Engine risk 1) | High×Severe | ADR-002 today; placeholder typography allowed at Alpha; day-7 go/no-go | Human + Opus/Sonnet |
| R2 | Earned recognition <3/5 — hook lands as "notification" (Gameplay top risk / F6) | Med-High×Severe | Probe staging at R0; F6 fix ladder pre-authorized for the R1 fix cycle; structural I-05 change only if R1 *and* R2 fail it | Lead + playtests |
| R3 | Recruiting slips; R1/R2 lose fresh cohorts | Med-High×High | Started 7/20; +50% over-recruit; R0 as stopgap | Human only |
| R4 | R2 fails with no runway | Med×Severe | Fallback ship date pre-agreed at M0 (proposed 8/23); "the date moves, not the Core Experience" | Human |
| R5 | Standard worlds under-deliver recognitions (B-2 residue) | Med×High | M-1 measurement before D-5; curated-seed shelf policy (presentation-layer world selection — no engine change) | Lead |
| R6 | Branch copy drift / undertested branches | Med×Med | Template-bound drafting; A-1a audits; R1/R2 testers seeded across branches | Sonnet + local LLM + Lead |
| R7 | Discovery-state store vs determinism (Engine risk 2) | Med×Med | D-6 designed before I-1; derived-state-only rule (store holds reveal flags, never world truth) | Opus + Lead |

### Release criteria (all required; gate at M5)

1. **Experience gate:** an R2 fresh cohort passes all four SC bars
   (SC-1 ≥4/5 within 30 min **and** ≥3/5 earned-path; SC-2 ≥4/5; SC-3 ≤1/5
   loss-coded, zero restarts at death; SC-4 ≥3/5 named different mark).
2. **Integrity gate:** the 8 frozen engine goldens + chronicle/transcript
   hashes byte-identical; full pytest green; black clean; canonical
   save/replay byte-identical; a shared recipe reproduces a world on a second
   machine.
3. **Content gate:** tutorial E2E on all three branches without crash or
   audit violation (A-1a clean); ≥30 standard seeds run play→explore→trace
   without crash; two-canon boundary verified (no authored content reachable
   from a generated world).
4. **Product gate:** packaging installs and runs on a fresh machine; no
   BLOCKER-severity open issue; ADR-001/002 ratified and reflected in the
   shipped build.

---

## 10. Owner Sign-offs Requested Now

1. Ratify **Q1** (Living Chronicle), **Q2** (English-only launch), **A-1**
   (curated tutorial, two-canon model, ◦ glyph cut).
2. Approve the **scope surgery** list (§3) and the **fallback date** (8/23
   proposed).
3. Approve **ADR-002 direction** (UI stack) once presented at M0.
4. Start **recruiting** (human-only task, on the critical path from today).
5. Optional but recommended: commit the six design docs to a `design/v1`
   branch so the SoT is versioned before the DR-pass edits it.
