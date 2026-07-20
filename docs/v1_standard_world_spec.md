# Chronicle Forge v1 — Standard-World Experience Spec (D-5)

Status: **Draft for Design Lock (7/23).** Deliverable D-5 of I-0, closing
BLOCKER **B-2** (a generated world's recognition experience was undesigned).
This document is the **normative specification for the standard *presentation*
world** — the generated worlds a player opens from the shelf after the tutorial.
It is **not an engine specification**: it changes no engine behaviour and moves
no golden. It specifies how the engine's (measured, abundant) recognition
*capacity* is **curated and paced** into the intended experience.

Authority: subordinate to `design_v1_definition.md` (North Star, SC-1..4,
Principle 7), `design_v1_direction.md`, and the discovery rules in
`v1_ux_spec.md` §5 (D-01..D-08); it *applies* them to generated worlds. It is
fed by `v1_m1_recognition_measurement.md` (M-1). Hard constraint (owner):
**do not modify the engine to reduce recognition frequency; all pacing lives in
the presentation layer.**

Scope excludes: the authored tutorial (its staging is `v1_tutorial_world_proof.md`),
the client-state mechanism (D-6), and JP copy (voice guide, I-5).

---

## 1. The problem M-1 reframed

M-1 measured 40 auto-mode seeds and found recognition capacity is **abundant,
not scarce**: 40/40 seeds reincarnate (3–5 lives) and offer ≥2 (typically 8)
re-offerable, self-signalling marks, each backed by a trace chain ≥12 (median
30) events deep. B-2 — "a world can produce zero recognitions" — was never
observed.

So the standard-world design problem is **not** "manufacture recognitions." It
is the opposite:

> The engine can *offer* ~8 recognitions per world. The North Star wants the
> first "that was me" to feel **earned and rare** — "guaranteed once, rare
> thereafter" (Principle 7). D-5 must decide **how much of the available
> capacity is delivered, when, and by whose hand** — at the presentation layer,
> touching no engine.

This is a *curation and pacing* spec, not a generation spec. The engine supplies
truth and capability; D-5 supplies emphasis and timing.

---

## 2. The three recognition tiers (the only levers)

Every recognition in a standard world reaches Confirm through exactly one of
three existing surfaces (UX §5 timing table). D-5 sets a policy for each; **these
three are the complete lever set** — there is no fourth, and none touches the
engine.

| Tier | Surface | Who initiates | Governing rule | D-5 lever |
|---|---|---|---|---|
| **Delivered** | P-10 rebirth digest | the loop (automatic) | D-03: previous life only, ≤3 lines | fixed by the loop; capped by D-03 |
| **Earned** | S-02 hold / P-14 trace | the **player** | D-05, D-07 | never manufactured; always available (curation guarantees real marks to find) |
| **Seeded** | P-12 world-end highlight | the game, once | D-06: exactly one | exactly one; curation guarantees it resolves to a deep chain |

The design insight: **the throttle is on *delivery*, not on *availability*.** The
game slows the automatic *answer* (Delivered/Seeded are deliberately sparse); it
never slows the player's own *investigation* (Earned is uncapped and always
backed by real marks). That distinction is what lets D-5 hit "rare thereafter"
without withholding truth (§4) and without an engine change (§6).

---

## 3. Pacing of the first recognition (SP-*)

The tutorial guarantees the first *earned* S-02 by ~18–22 min (B13), within the
SC-1 ≤30:00 window. A standard world is opened **after** the tutorial, by a
player who already knows the loop, so its pacing rules differ:

- **SP-1 (the guaranteed first recognition is Delivered, at the first rebirth).**
  A standard world's earliest guaranteed recognition is the **first P-10 digest**
  — the delivered, last-life attribution that fires automatically at the first
  time-skip (end of Life 1 → Life 2). Because every reincarnation produces a
  digest and M-1 shows every seed reincarnates, this is guaranteed by the loop
  and needs no staging. It lands early (first rebirth) and teaches nothing new;
  it *reminds*. This is the standard world's answer to "at least one recognition
  is guaranteed."
- **SP-2 (the first *earned* recognition is not paced and not guaranteed).**
  Per D-07, S-02 is guaranteed only in the *first* world (the tutorial);
  thereafter it is "naturally rare." A standard world therefore **does not stage,
  schedule, or guarantee** an S-02. It guarantees only that, whenever the player
  chooses to hold a marked line, a *real* recognition is there to find (curation,
  §5). Rarity is a property of player initiative, not of a timer.
- **SP-3 (the world-end confirm is guaranteed, exactly once).** D-06's single
  seeded P-12 line is guaranteed and lands at world's end; it exists to guarantee
  **SC-2** (the trace) for a player who never held a mark — not to serve SC-1.
  Curation guarantees this line resolves to a chain ≥3 links deep (§5).
- **SP-4 (no first-recognition timer in generated worlds).** Because SP-1 is
  loop-guaranteed and SP-2 is deliberately un-paced, there is **no ≤30:00 style
  gate on generated worlds.** The SC-1 ≤30:00 bar is a *tutorial* obligation
  (the first world); D-5 must not re-impose it on standard worlds, as that would
  force manufactured marks (a D-07 violation).

**Net pacing shape of a standard world:** an early delivered reminder (SP-1), a
sparse middle where recognitions happen only if the player reaches for them
(SP-2), and a guaranteed closing pull into tracing (SP-3). Abundance is present
but *latent* — the player decides how much of it to convert.

---

## 4. Recognition density across a complete chronicle (RD-*)

For a typical 4-life standard world (M-1 median), the **delivered** and **seeded**
density is fixed and deliberately low; the **earned** density is player-governed.

- **RD-1 (Delivered density = one per rebirth, last-life only).** A 4-life world
  yields 3 P-10 digests (after lives 1, 2, 3), each attributing **only** the
  immediately previous life, ≤3 lines (D-03). This is the entire automatic
  attribution budget. It does not scale with capacity: even an 8-mark seed
  delivers at most one digest per rebirth.
- **RD-2 (Seeded density = exactly one, at the end).** One P-12 highlight per
  world (D-06). Never more, regardless of how many still-shaping legacies exist.
- **RD-3 (Earned density = uncapped, player-governed, never manufactured).** The
  player may hold any marked line and trace any threaded event; each is a real
  recognition (D-08). The game adds **zero** pressure to do so — no counters, no
  "you missed one" nudges, no answer-pushing UI (out of scope, definition §6).
  The M-1 capacity (up to 8 marks) is the *ceiling of what is findable*, not a
  quota to hit.
- **RD-4 (Density is felt as rarity, not scarcity).** The design target is that a
  *typical* player earns **1–3** recognitions across a full standard world on top
  of the delivered digests — not because the game caps it, but because holding is
  deliberate and the marks are sparse in any single spread (D-02: marks appear
  only at decision/trace surfaces, never in running prose). Rarity is produced by
  *placement and effort*, not by hiding real marks.
- **RD-5 (No inflation across worlds).** Later worlds never raise their
  recognition rate to compensate for a quiet earlier one (D-07). Each world's
  density is whatever its curated seed and the player's initiative produce.

**Density summary (4-life typical):** 3 delivered + 1 seeded guaranteed; 1–3
earned typical, up to ~8 available. The guaranteed floor of *meaningful*
recognition is the first digest (SP-1) plus the closing confirm (SP-3); every
other recognition is a gift the player gives themselves.

---

## 5. Curated-seed selection criteria (SEL-*)

The shelf is a **presentation-layer selection** over the engine's seed space — a
manifest of hand-picked seeds, not a generation change (R5 mitigation). A seed is
admissible to the shipped shelf iff, measured in auto mode by the M-1 harness:

- **SEL-1 (reincarnation).** `lives ≥ 3`. (M-1: all 40 pass.)
- **SEL-2 (recognition capacity floor).** `past_self_marks ≥ 4` — at least four
  marks founded by an earlier life survive into a later one, so a player who
  reaches for recognition always finds several real ones. (M-1: 33/40 pass;
  excludes seeds 11, 24, 26 and any below 4.)
- **SEL-3 (trace depth floor).** `trace_depth_max ≥ 20` — the deepest past-self
  mark carries ≥20 derived events, guaranteeing SP-3's closing trace is ≥3 links
  and never shallow. (M-1: excludes seeds 12, 38 at depth 12; combined SEL-2∧SEL-3
  admits ~30/40.)
- **SEL-4 (zero orphan marks).** Every offered mark resolves to a real engine
  ancestry — no mark without a founder (DoD-4). (M-1: held for all 40; SEL-4 is a
  per-seed assertion in the shelf-manifest check, not a statistical bar.)
- **SEL-5 (an early-earnable first mark).** At least one strong mark is founded in
  **Life 1** and is still live/markable in Life 2, so the earliest *possible*
  earned recognition (a Life-2 hold tracing to Life 1) exists for players who
  reach for it early. (Backed by M-1 founder_life data; verified per seed.)
- **SEL-6 (temperament spread across the shelf, not per seed).** M-1 endings skew
  Imperial (33/40); the shelf is curated for a **mix** of ending temperaments so
  the front-matter/plate experience varies between books. This is a shelf-level,
  not seed-level, criterion.

**Shelf size:** the shipped shelf is a small curated set (target ~6–10 seeds) —
enough for replay variety (the empty-slot intent) without a QA explosion. Exact
count is a content-freeze decision, not a Lock blocker.

**Manifest:** each shelf entry records `{seed, lives, past_self_marks,
trace_depth_max, ending, admitted_by: [SEL-*]}`; a CI check re-runs the M-1
harness against the manifest and fails if any shipped seed no longer clears its
bars (DoD-4 verification).

---

## 6. Engine capability vs. presentation policy (the boundary)

The single most important separation in this spec. Nothing in the left column may
change to serve anything in the right column.

| Concern | **Engine capability** (frozen truth) | **Presentation policy** (D-5, mutable) |
|---|---|---|
| What marks exist, their ancestry, scores | ENGINE — frozen (P6/P17 goldens) | — |
| How many recognitions are *available* | ENGINE — abundant (M-1) | — |
| Which available recognitions are *delivered* | — | P-10 digest policy (RD-1) |
| Which are *earned* vs latent | — | player initiative; UX §5 D-05 |
| Which single one is *seeded* at end | — | P-12 policy (RD-2, D-06) |
| **When** the first recognition lands | — | pacing SP-1..4 (loop + curation) |
| **Which seeds** ship | — | shelf manifest (SEL-1..6) |
| Discovery/reveal *state* | — | client store (D-6) |

**Boundary rules:**

- **B-6.1** D-5 never asks the engine to found fewer marks, weaken scores, or
  drop a marked juncture to "make recognition rarer." Rarity is achieved by
  delivering less and curating placement, never by generating less.
- **B-6.2** D-5 never fakes, decoys, or suppresses a *real* mark (D-08). It
  chooses the *order and moment of the answer*, never the truth of it.
- **B-6.3** Every D-5 lever is implemented in already-planned presentation
  surfaces — the P-10/P-12/P-14 read-model lenses, the client discovery-state
  store (D-6), and the shelf manifest. If a desired pacing effect cannot be
  achieved in those surfaces, it is **cut**, not pushed into the engine.

This is why "do not modify the engine to reduce recognition frequency" is
satisfiable: the frequency the *player experiences* is a function of delivery +
curation + initiative, all of which live to the right of the boundary.

---

## 7. Verification (DoD-4 / DoD-5 surface)

| Check | Asserts | DoD |
|---|---|---|
| T-SW-shelf-floor | Every shipped shelf seed clears SEL-1..5 under the M-1 harness; SEL-6 holds shelf-wide | DoD-4 |
| T-SW-no-orphan | Every offered mark on every shelf seed resolves to a real founder (zero orphan marks) | DoD-4 |
| T-SW-delivered-cap | No P-10 digest attributes more than the previous life, ≤3 lines, on any shelf seed | D-03 |
| T-SW-one-seed | Exactly one P-12 seeded confirm per world | D-06 |
| T-SW-close-trace | The seeded confirm resolves to a trace chain ≥3 links on every shelf seed | SP-3 |
| T-SW-engine-untouched | All 8 engine goldens + chronicle `aa4c67…` + transcript `98bea8…` byte-identical; the shelf is a manifest, not a generation change | DoD-2, B-6 |
| T-SW-no-manufacture | No presentation surface introduces a marked juncture or mark absent from engine truth (D-08) | D-07, D-08 |

All checks read engine truth and shipped policy; none may move an existing
golden. The shelf manifest is data; adding/removing a seed changes no code path.

---

## 8. Self-review against the North Star

> *Does this strengthen the experience of discovering, by yourself and across
> felt time, the marks your own past lives left on the world?*

- **"By yourself."** ✅ Strengthened. The design's core move — throttling
  *delivery* while leaving *investigation* uncapped and always real — puts the
  discovery in the player's hands (D-05, SP-2, RD-3). The game reminds early
  (SP-1) and pulls once at the end (SP-3), but the recognitions that *matter* are
  the ones the player reaches for. A world that auto-delivered its 8-mark capacity
  would fail this word; D-5 explicitly refuses that.
- **"Across felt time."** ✅ Preserved. Delivered recognition is bound to the
  reincarnation loop (one per rebirth, previous-life-only, D-03/RD-1), so
  attribution is always *earned across the time-skip*, never collapsed into one
  spread. Trace depth ≥20 (SEL-3) guarantees the closing walk crosses real lives.
- **"The marks your own past lives left."** ✅ Guaranteed real. SEL-4/B-6.2/D-08:
  every mark is a true ancestry, never a decoy; curation selects *among* real
  marks, never invents them.
- **Without withholding truth.** ✅ The full truth is always *reachable*: every
  mark is holdable, every thread traceable, and P-13 reading + P-14 tracing
  resolve everything a curious player wants (D-04 permanence). D-5 delays the
  automatic answer; it never blocks the player's. "Withheld" means *not yet
  volunteered by the game*, never *hidden from the player who looks*.
- **Tension check — does curation cheat?** The shelf picks strong seeds, but
  every recognition on them is real engine truth; curation raises the floor of
  *availability*, not the rate of *delivery*. A player on a curated seed still
  earns recognitions themselves. No North-Star word is served by a falsehood.

**Verdict:** consistent with the North Star and all four Success Criteria (SC-1
via SP-1 + tutorial precedent; SC-2 via SP-3/SEL-3; SC-3 unaffected — death
framing is P-08/P-10 copy, not density; SC-4 via replay/temperament spread,
SEL-6). No engine change; ready for owner review.

---

## 9. Open questions for Lock

- **Q-SW-1 (shelf size).** Target ~6–10 seeds; exact count deferred to content
  freeze. *Proposed: decide at 8/7, not a Lock blocker.*
- **Q-SW-2 (input-variance floor).** M-1 bounds capacity in *auto* mode; a
  worst-case player-choice study (recommended in M-1 §4) would confirm SEL-2/3
  hold under adversarial input. *Proposed: run the variance study over the final
  shelf before freeze; SEL bars stand on auto data for Lock.*
- **Q-SW-3 (delivered vs. earned emphasis).** Should the first P-10 digest (SP-1)
  lean toward the *loud echo* framing the tutorial uses, or stay neutral in
  generated worlds? *Proposed: neutral in standard worlds (no authored copy);
  resolve with the voice guide (D-3).*
- **Q-SW-4 (SEL-5 measurability).** SEL-5 needs per-seed founder_life data the M-1
  summary aggregated; the shelf-manifest builder must expose it. *Proposed:
  extend the M-1 harness output with per-mark founder_life when building the
  manifest (I-6); trivial, no engine change.*
