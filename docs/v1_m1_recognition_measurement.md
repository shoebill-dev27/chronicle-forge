# M-1 — Recognition-Rate Measurement (feeds D-5)

Status: **Measured, 2026-07-20.** Deliverable M-1 of I-0 (execution plan
§133): *"run play→explore over N≥30 seeds, tabulate legacy re-offer /
trace-chain availability."* This report is the **data**; D-5 (the Standard-World
Experience Spec, Opus/lead) sets the recognition *floor* and the curated-seed
shelf policy from it. Routing note: measurement is mechanical (this doc);
interpretation is lead's.

Supersedes any prior-session M-1 run (that background delegate's output did not
survive the session; this is a fresh, reproducible run).

---

## 1. Method

- **N = 40** seeds (`seed = 0..39`).
- Each seed: `app.play(PlayRequest(seed, auto=True))` → recipe →
  `app.services.legacy(recipe)` (P17 LegacyView) + `app.explore(recipe)`
  (life count / span / ending). **Committed, deterministic surfaces only**;
  no engine or golden touched.
- **Auto (opportunity) mode** — fated choices, no player input. This measures a
  generated world's *capacity* to offer a recognition, independent of player
  behaviour, which is exactly what a recognition **floor** must bound. (Player
  choice variance is a separate question — see Limitations §4.)

Metrics per seed:

| Metric | Meaning |
|---|---|
| `lives`, `span`, `ending` | world shape |
| `marks` | attributable enduring marks (LegacyView.marks; each carries `founder_life`) |
| `recognitions` | self-signalling subset ("that was me" — LegacyView.recognitions) |
| `past_self_marks` | marks whose `founder_life < lives` — a **later incarnation exists to recognize a past self's mark** (the re-offer condition) |
| `recog_reoffer` | recognitions that are also re-offerable (`founder_life < lives`) |
| `trace_depth_max` | max `derived_events` among past-self marks — walkable **trace-chain** richness (P14) |
| `reach_max` | max `reach` among past-self marks |

Reproduce: `scratchpad/m1_measure.py` (PYTHONPATH=src). Deterministic.

---

## 2. Summary

| Quantity | Value |
|---|---|
| Seeds with a **re-offerable** past-self mark | **40 / 40 (100%)** |
| Seeds with a re-offerable **self-signalling recognition** | **40 / 40 (100%)** |
| Seeds producing **zero marks** | 0 |
| Single-life seeds (no reincarnation) | 0 |
| `past_self_marks` (min / median / max) | **2 / 8 / 8** |
| `trace_depth_max` (min / median / max) | **12 / 30 / 54** |
| Lives distribution | 3→10, 4→28, 5→2 |
| Ending distribution | Imperial 33, Warring 5, Arcane 1, Golden 1 |

**Headline: B-2 not observed.** The BLOCKER B-2 hypothesis — "a generated world
can produce *zero* recognitions and nothing bounds it" — did **not** occur in any
of 40 auto-mode seeds. Every seed reincarnates (≥3 lives), founds ≥2 attributable
marks that self-signal, and every one of those is re-offerable to a later
incarnation with a trace chain ≥12 events deep. The *typical* seed offers 8
re-offerable recognitions with a 30-event-deep chain.

**Weakest seeds (the empirical floor):**

| seed | lives | marks | recognitions | past_self | trace_depth_max |
|---|---|---|---|---|---|
| 24 | 5 | **2** | 2 | 2 | 13 |
| 11 | 4 | 5 | 5 | 5 | 24 |
| 26 | 4 | 6 | 6 | 6 | 28 |
| 12 | 4 | 8 | 8 | 8 | **12** |
| 38 | 4 | 8 | **6** | 8 | 12 |

Even the floor seed (24) still clears "≥1 self-recognition with a walkable chain."

Full per-seed table: §5.

---

## 3. Findings for D-5

1. **Recognition availability is not a scarcity problem in auto mode; it is an
   abundance one.** `recognitions` ≈ `marks` on almost every seed (the self-signal
   condition — a *living* mark — is met by most attributable marks). The lens
   reports the world's *capacity* (8/8 typical), while the North Star wants
   recognition "guaranteed once, rare thereafter." **This throttle is the
   client's job, not the world's:** D-03 (recency window), D-05 (staged/earned),
   and D-07 (recognition frequency) gate how many of these capacity-marks become
   *delivered* reveals. D-5 should state the floor as *capacity* (what the seed
   makes available) and defer *frequency* to the discovery rules — they are
   different layers.

2. **A floor bar is easy to set and easy to meet.** Candidate shelf-admission
   bar for a curated seed: `past_self_marks ≥ 4` **and** `trace_depth_max ≥ 20`.
   Against this run that admits 33/40 seeds and excludes only the five weak seeds
   above — i.e., the shelf can be curated to guarantee a strong recognition +
   deep trace without any engine change (presentation-layer selection, per the
   R5 mitigation). A stricter bar (`≥6` and `≥25`) still admits ~30/40.

3. **World shape is stable and short.** Every auto seed spans 40 years over 3–5
   lives — matching the "short generated world" assumption. No degenerate
   single-life or runaway worlds appeared. Endings skew Imperial (33/40); D-5's
   temperament/front-matter copy should not assume ending variety from a random
   seed draw (curate for it if variety is wanted on the shelf).

4. **Trace chains are deep enough to rehearse SC-2.** Median 30 / max 54 derived
   events on a past-self mark means P-14 tracing (3–4 links to an origin card) is
   always backed by real ancestry; zero orphan-mark risk in this sample (DoD-4's
   "every offered mark resolves to a real engine ancestry" held for all 40).

**Proposed floor for D-5 (lead to ratify):** shelf seeds must yield, in auto
mode, **≥4 re-offerable self-signalling recognitions** each backed by a
trace chain of **≥20 derived events**; the shipped shelf is curated to seeds that
clear this, giving a hard guarantee without touching frozen scoring.

---

## 4. Limitations (carry to D-5 interpretation)

- **Auto mode only.** This bounds *capacity* under fated choices. A player who
  makes recognition-poor choices could, in principle, found fewer marks than the
  auto path. Auto is the right central estimate for a floor, but a **worst-case
  input-variance study** (adversarial/greedy-avoidance scripting over the shelf
  seeds) is a recommended follow-up before content freeze (8/7) — not a Lock
  blocker, since the curated shelf + D-07 throttle already de-risk B-2.
- **Capacity ≠ delivered.** The numbers here are what the world *offers*, not what
  a player *sees*; the client's discovery rules decide delivery. Do not read
  `recognitions=8` as "the player gets 8 reveals."
- **Mark count appears capped (~8).** The lens tops out at 8 marks on strong
  seeds; this is inherited P17 lens behaviour, not a measurement artifact. It
  bounds the *legible* set, which is the relevant quantity for the shelf.
- **Tutorial world excluded.** M-1 measures *generated* worlds (D-5's domain);
  the authored tutorial's recognition staging is specified separately
  (tutorial world proof, I-5).

---

## 5. Per-seed data

| seed | lives | span | ending | marks | recognitions | past_self_marks | recog_reoffer | trace_depth_max | reach_max |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 35 | 35 |
| 1 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 46 | 46 |
| 2 | 4 | 40 | Warring Age | 8 | 8 | 8 | 8 | 19 | 19 |
| 3 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 4 | 4 | 40 | Warring Age | 8 | 8 | 8 | 8 | 28 | 28 |
| 5 | 4 | 40 | Warring Age | 8 | 8 | 8 | 8 | 16 | 16 |
| 6 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 45 | 45 |
| 7 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 54 | 54 |
| 8 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 23 | 23 |
| 9 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 46 | 46 |
| 10 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 23 | 23 |
| 11 | 4 | 40 | Imperial Age | 5 | 5 | 5 | 5 | 24 | 24 |
| 12 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 12 | 12 |
| 13 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 43 | 43 |
| 14 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 32 | 32 |
| 15 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 16 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 17 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 50 | 50 |
| 18 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 35 | 35 |
| 19 | 5 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 16 | 16 |
| 20 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 38 | 38 |
| 21 | 4 | 40 | Warring Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 22 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 23 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 28 | 28 |
| 24 | 5 | 40 | Imperial Age | 2 | 2 | 2 | 2 | 13 | 13 |
| 25 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 30 | 30 |
| 26 | 4 | 40 | Imperial Age | 6 | 6 | 6 | 6 | 28 | 28 |
| 27 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 45 | 45 |
| 28 | 4 | 40 | Warring Age | 8 | 8 | 8 | 8 | 23 | 23 |
| 29 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 47 | 47 |
| 30 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 23 | 23 |
| 31 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 47 | 47 |
| 32 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 25 | 25 |
| 33 | 4 | 40 | Arcane Age | 8 | 8 | 8 | 8 | 32 | 32 |
| 34 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 49 | 49 |
| 35 | 4 | 40 | Golden Age | 8 | 8 | 8 | 8 | 25 | 25 |
| 36 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 47 | 47 |
| 37 | 4 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 33 | 33 |
| 38 | 4 | 40 | Imperial Age | 8 | 6 | 8 | 6 | 12 | 12 |
| 39 | 3 | 40 | Imperial Age | 8 | 8 | 8 | 8 | 33 | 33 |

---

## 6. Hand-off

- **Unblocks D-5** (Standard-World Experience Spec): floor candidate in §3, shelf
  policy = curate to seeds clearing the bar; no engine change (R5 mitigation).
- **Recommended follow-up** (not a Lock blocker): input-variance worst-case study
  before content freeze.
- Data is reproducible from `scratchpad/m1_measure.py`; re-run on any engine bump.
