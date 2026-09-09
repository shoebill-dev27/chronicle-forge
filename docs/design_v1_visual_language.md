# Chronicle Forge v1 — Visual Language Study

Status: **Design study / for owner decision. No implementation.**
**Its *treatment* conclusions are superseded by
[`design_v1_visual_exploration.md`](design_v1_visual_exploration.md)** (30 roughs,
2026-08-08): the stream plate below survives as the *content* of the right-hand
page, but it must be lit on a dark ground, not set on cream.

> **2026-09-08 baseline ratification.** The Astra UI/UX review's change ledger is
> **adopted** as [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md) and
> is binding on this document. Applicable items: **UX-R5** — 朱 now means **a confirmed connection to a past life**, replacing the earlier "still shaping the world" rule; size still carries nothing, and ⟜/❧ stay trace-*kind* labels, never state. **UX-R4** — strata depth encodes **historical order**, never an event count standing in for elapsed years; the year is carried by horizontal position.

Companion to [`design_v1_art_direction.md`](design_v1_art_direction.md), which it
**partly corrects** (see §1). Authority: subordinate to
[`design_v1_definition.md`](design_v1_definition.md).

Review wall (all specimens, full size + 292 px):
<https://claude.ai/code/artifact/1af68c28-0e06-4a4a-a1b0-2e85ca4e4148>

Every image referenced here is in [`mocks/v1_art/`](mocks/v1_art/) and was drawn
by a script that can read **only** `mocks/v1_art/world.json` — a dump of real
engine output for seeds 1, 42 and 99. **No plate contains a fact the engine does
not have.** The harness (`extract.py`, `plates.py`, `keyscreens.py`, `final.py`)
is included so every image can be regenerated.

---

## 0. Verdict

**Recommended: V9r "STREAM"** — the right-hand plate of the permanent spread is
the world's *temper over time*, drawn as filled bands, with the player's lives as
bright vertical threads crossing it and their marks hung beneath.
Evidence: `mocks/v1_art/_seedtest.png`, `ks2_reveal.png`, `ks4_reread.png`.

It is recommended for one reason above all: **it is the only visual that draws
something the engine actually has in quantity, and it is the only one that
survives a 292 px thumbnail.** Both claims were tested, not assumed.

---

## 1. Correction to the previous study

`design_v1_art_direction.md` §6 recommended **R-1, a rota (wheel-of-years)
plate**, and argued that a procedurally drawn plate would differ per seed "at
zero per-seed art cost."

Drawing it from real data falsifies two parts of that:

- **The rota is the worst performer of the eight variants** (`v1_rota.png`). With
  real data the events collapse into one 60° sector — 53 of 73 events are
  `governance` — and every mark lands at the same radius because they share a
  founder life. At 292 px it is a faint ring with a smudge in it.
- **"Every seed has a different map" was wrong.** There is nothing per-seed to
  draw geographically; see §2.

The *thesis* of that study survives intact and is strengthened: generated worlds
need generated pictures. Only the chosen form was wrong, and it was wrong because
it was chosen without looking at the data.

---

## 2. What the engine actually contains

Measured over 10 seeds (1, 2, 3, 7, 11, 17, 23, 42, 99, 123). This is the
binding constraint on every visual decision below.

| Property | Reality |
|---|---|
| Locations per world | **Exactly 4, always** |
| Location names | **Identical in every seed**: Hollowfen · The Sunken Vault · Greywind Moor · Thornreach |
| Origin place name | **"Hollowfen" in all 10 seeds** |
| Events with a location | **0** — `location_id` is never set |
| Distinct event phrases | **2–6** for 34–76 events (seed 42: *two* phrases for 60 events) |
| World span | 40 years, always |
| Lives per world | 3–5 |
| Marks per world | 5–8, **all of kind `institution`**, all named "Order of the ___" |
| Duplicate mark names | in 6 of 10 seeds |
| Ending class | "Imperial Age" in 9 of 10 |
| Causal edges | 71 of 73 nodes — but a near-total-order cascade, high fan-in |
| **Theme history** | **40 years × 6 axes, and it genuinely varies per seed** |

**Three consequences, and they are not art problems.**

**E-1 — A map is impossible, and not for the reason previously given.** The
earlier study said a geographic map would *fabricate* facts (true, and still
true). The stronger fact is that there is nothing to draw: four places, the same
four in every world, and no event is attached to any of them. `v5_field.png` is
the honest attempt — four labels on a ring and a great deal of nothing.

**E-2 — A thread board draws a hairball.** `v6_threads.png` renders the real
`caused_by` graph. Because the cascade is near-total-order, six near-identical
"Order of the ___" cards fan into an illegible crosshatch. **R-2, the fallback
from the previous study, is therefore also not viable on current data.** The
card-and-ribbon *form* is good; the graph is not yet shaped to be read.

**E-3 — "A different world could hold a different me" is not currently
deliverable.** Emotional Arc §6 and Success Criterion 4 both depend on worlds
being distinguishable. Today every world is the same four places, usually the
same ending, and a set of interchangeable Orders. A shelf of books is currently a
shelf of identical spines.

The theme history is the exception, and it is the one rich, varying, honest
dataset the engine produces. **That is why the recommendation is built on it.**

---

## 3. The eight roughs and how they scored

Contact sheet: `mocks/v1_art/_contact.png` · thumbnails:
`mocks/v1_art/_thumbs292.png`. All drawn from seed 1.

| | Rough | Full size | **At 292 px** | Verdict |
|---|---|---|---|---|
| V1 | **ROTA** — concentric years, sector per domain | events collapse into one sector; marks overlap into a clump | faint ring, one smudge | **Fail.** Kills the previous recommendation |
| V2 | **STRATA** — one band per year, ink fading with age | reads as ruled notebook paper with specks | blank | **Fail** |
| V3 | **LOOM** — years × domains, lives as bands | the life bands read well; events invisible | grey columns — a real silhouette | Partial: the *lives* idea works |
| V4 | **RIVER** — theme axes over time | legible, has shape, varies | **clearest pass** | **Basis of the recommendation** |
| V5 | **FIELD** — the four places, schematically | four labels, mostly empty | empty circle | **Fail** (see E-1) |
| V6 | **THREADS** — marks and what they caused | hairball (see E-2) | reads as "a diagram" | Form good, data not ready |
| V7 | **LINEAGE** — the lives as a spine, marks hung off | clean, immediately meaningful | too sparse | Excellent content, fails the store test |
| V8 | **SEAL** — one emblem for the world | hatching reads as wood grain; labels collide | reads as a seal | Idea sound, execution poor |

### The law the test produced

> **At thumbnail scale, only *area* survives. Line and point do not.**

Every failure above (V1, V2, V5, V7) is sparse ink on a large cream field. Every
pass (V3, V4, V6, V8) fills area. This is the same failure mode as the shipped
build — thin serif text on cream is line and point, so it dies at 292 px — and it
is the most useful single rule this study produced. It governs everything in §5.

---

## 4. The recommendation: V9r "STREAM"

`v9r_seed1.png` · `v9r_seed42.png` · `v9r_seed99.png` · comparison
`_seedtest.png`.

**Form.** V4 (area, survives the thumbnail, draws real varying data) fused with
V7 (the soul's lives, which is what the North Star is actually about).

- **The stream** — six filled bands, one per theme axis, across the world's span,
  ordered by final dominance so the world's character is legible as a shape.
  Axis names are set **inside** their bands (naming in place; outside they read
  as a chart legend).
- **The lives** — each life is a bright vertical band across the whole stream:
  the years you were alive. The gaps between them are the years you were not.
  This is the felt-time device, and it costs nothing to draw.
- **The marks** — hung beneath the life that founded them, on a thin thread up to
  that life's band.
- **The unwritten future** — drawn as faint ruled paper with 「まだ書かれていない」,
  never left blank. Blank reads as a bug; ruled reads as a promise.
- **The bleed** — on a confirmed reveal the mark's leaf goes 朱 and concentric
  ink rings soak outward, sized to survive a thumbnail.
- **Age is opacity**, unchanged from the previous study; here it is carried by the
  band tones and the thread weights.

**Seed discrimination — tested and passed.** `_seedtest.png` puts seeds 1, 42 and
99 side by side: three lives with wide gaps vs. four vs. five packed; a
governance-dominated silhouette vs. a culture-heavy one. The worlds are
distinguishable at a glance **even though their four place names are identical**.
This is the single strongest argument for the choice: it is the only surveyed
form that can tell current worlds apart.

### How it strengthens the Core Experience

| Core Experience element | What the plate does |
|---|---|
| "…the marks your past lives left…" | Marks are drawn *attached to the life that made them* — authorship is the composition, not a caption |
| "…on the world…" | The stream **is** the world, and it visibly bends inside your life-bands |
| "…across felt time…" | The gaps between life-bands are drawn at true scale; you can see the years you missed |
| Discovery, not delivery (Principle 2) | Unrevealed marks are drawn faint and unnamed — present, unexplained |
| Recognition (S-02) | The bleed gives the reveal a second, larger beat on the opposite page |
| The interface is the artifact (Principle 10) | It is a plate in a book, not a chart in an app — provided the Law of Total Reduction holds |

### Its honest risks

1. **It can read as an infographic.** This is the real danger and it is a
   craft problem: hand-inked edges, paper, naming in place, no axes, no numbers,
   no legend. The roughs are already at the edge — `v4_river.png` reads more like
   a chart than `v9r_seed1.png` does, and the difference is only labelling and
   tone.
2. **It shows the world's *temper*, not its *events*.** A player may ask "but
   what happened?" The left page must answer that; the plate never can.
3. **Axis labels collide with band edges** in the roughs (visible in
   `v9r_seed42.png`). A production detail, not a design flaw.
4. **It depends on the theme history staying varied.** If the engine's theme
   dynamics were ever flattened, the recommendation collapses with them.

---

## 5. Key screens

Sheet: `mocks/v1_art/_keyscreens.png` · thumbnails `_keythumbs292.png`.
Rendered 1600×900 (same aspect as the 1920×1080 store spec), tested at 292 px.

**Provenance of the text.** Place names, mark names, life ordinals, years,
talents, spans, endings and every plate value are **real seed-1 engine output**.
The Japanese situation prose on the left pages is **PLACEHOLDER** — it stands in
for content that does not exist yet (T3 item U-2). The option labels are real;
their English form is the open U-3/U-4 issue. Nothing here was fed back into the
client.

| | Screen | At 292 px | Notes |
|---|---|---|---|
| **KS-1** | `ks1_shelf.png` — title / shelf: a dark room, spines, one empty slot, an open book showing a full plate | **Strongest pass** | The store learns the whole game from this frame: a shelf, a book, an accumulated world. **This is the store's lead image.** |
| **KS-2** | `ks2_reveal.png` — the reveal at full stage weight: 朱 mark + Hand line on the left, the mark bleeding on the plate | **Pass on silhouette** | The 朱 is still too small to be the hook at thumbnail size — it must grow further or the frame must crop tighter |
| **KS-3** | `ks3_juncture.png` — the first juncture, plate nearly empty, the hold verb caught mid-action | **Fail** | Fails *structurally*: an early world genuinely has no history yet. **Conclusion: the first juncture must never be a store screenshot.** It is still the right in-game screen |
| **KS-4** | `ks4_reread.png` — the finished chronicle beside a full-density plate | **Pass** | The clearest image of "you did all this and forgot" |

Three of four pass. The one failure is honest and its lesson is a store decision,
not a design change.

### Elements defined by the mocks

- **Marks.** ⟜ drawn as a ruled bar with a hooked eye (the hint); ❧ as a fleuron
  — a leaf on a curved stem (the confirmed mark). Both are strokes, never icons.
  ~~Size, not colour, carries confirmation; 朱 is added only for *still shaping
  the world*.~~ **Amended 2026-09-08 (baseline UX-R5): 朱 = a confirmed
  connection to a past life, and nothing else.** Ordinary selection and the S-03
  promise mark stay in ink. "Still shaping the world" survives as a concept
  (D-06) but is expressed as explicit text, never as this colour.
- **The inspect verb.** A visible, labelled, keyboard-reachable "調べる" action on
  any marked line; the rule filling beneath a held line is retained only as an
  optional convenience gesture (baseline UX-R2), never the sole path. Visible in
  a still (`ks3_juncture.png`) — the L-4 requirement.
- **Spines.** Currently the only honest differentiators are seed, span and ending
  class, because place names do not vary (E-3). The mocks label them so.
- **Marginalia.** Deliberately absent. With 2–6 event phrases there is nothing
  truthful to write in a margin yet.
- **Portraits / heraldry.** **Not proposed.** The engine has no per-NPC or
  per-faction visual attributes to generate from, and hand-drawing them fails
  the solo-maintenance constraint. Deferred until there is data to draw from.

---

## 6. Cost and risk

| | Production cost | Risk | Long-term |
|---|---|---|---|
| **V9r STREAM** | **Low.** One renderer (~400 lines), zero per-seed assets, zero illustration | Reads as infographic if craft slips; depends on theme-history variety | Grows automatically as simulation depth grows |
| V6 THREADS (prev. fallback) | Low | **Currently draws a hairball** (E-2) | Viable once the causal graph is shaped |
| V7 LINEAGE | Very low | Fails the store test alone | Excellent as an *in-book* spread |
| V8 SEAL | Very low | Says little | Good capsule/emblem candidate |
| Illustrated plates (prev. B) | **High**, per-content | Reused art reads as stock | Does not scale |

**The recommendation is also the cheapest viable option.** That is not a
coincidence: it is what "draw only what the data has" buys.

---

## 7. What must be true before implementation

The visual language is validated as far as a machine observer can take it. What
remains is either human judgement or upstream content.

| ID | Item | Kind | Why it blocks |
|---|---|---|---|
| **VL-1** | **The content floor.** 2–6 event phrases, 4 fixed place names, one mark kind, one ending class | **Content blocker** | No visual language can make interchangeable content feel discovered. This now outranks the art direction in priority |
| **VL-2** | U-2 — no situation prose on the juncture page | Content blocker | The left page of every mock is placeholder without it |
| **VL-3** | Does the plate read as *a plate* or as *a chart*? | Human judgement | Cannot be settled by the author of the mock |
| **VL-4** | The 3-second / 292 px test with 5 non-players | Human test | My own thumbnail readings are a machine observer's, not an audience's |
| **VL-5** | Does showing faint unnamed marks preserve the hunt (D-08)? | Playtest | Design review is not sufficient |
| **VL-6** | 朱 legibility at store scale on KS-2 | Craft iteration | Currently too small |
| **VL-7** | ADR-002: can this be drawn in static SVG with no WebGL? | Technical | The roughs are raster; production would be SVG |

**VL-1 is the finding that matters most.** The visual language question has a
good answer. It sits on top of a world that currently produces the same four
places, the same guild names and the same ending in nearly every seed — and no
art direction can compensate for that. I would sequence the content floor before
building the plate.

---

## 8. Recommendation in one line

**Adopt V9r STREAM as the plate; lead the store page with KS-1 and KS-4; do not
build it until the content floor (VL-1) is scheduled**, because the plate's
whole value is that it makes worlds distinguishable, and it can only distinguish
worlds that differ.
