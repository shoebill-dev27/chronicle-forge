# Chronicle Forge v1 — Tutorial World Content Proof

Status: **Design / for review. No implementation, no code.**
Authority: [`design_v1_definition.md`](design_v1_definition.md) ·
[`design_v1_direction.md`](design_v1_direction.md) ·
[`v1_ux_spec.md`](v1_ux_spec.md) ·
[`v1_tutorial_world_proof.md`](v1_tutorial_world_proof.md) (beats B0–B18,
invariants INV-1…INV-8, guarantees G-1…G-5).

Purpose: replace every exemplar in the tutorial script with **concrete,
authored content** — named events with years, causes, and player-facing copy —
and verify that the designed experience (SC-1…SC-4) emerges from that content
under the Discovery Rules. Where verification found holes, this document
records the gap and the revision (§8). Determinism caveats and everything the
implementation must make true are in §9.

ID scheme: `EV` world event · `JN` juncture · `OP` option · `TR` trace ·
`DG` digest line · `CH` trace-chain card. The **golden path** (OP-2A sealed at
JN-2) is cataloged in full; branch paths are cataloged to the same structural
depth in §2.7.

---

## 1. Canon — The Chronicle of the Salt Kingdoms

**Span:** 409–803 (394 years). **Lives:** 3 (third optional, pacing-gated).
**Junctures:** 2 + 3 + 1 = 6 (INV-7 bound: ≤8). **Epithet:** *of Salt.*

### Places
| Name | What it is | First appears |
|---|---|---|
| Brant Ford | River town; Life 1's home | Front matter |
| The Hill / the sealed undercroft | Flood-priests' sealed wellworks | Front matter (EV-02) |
| Undermount | Shrine city raised on the Hill (player-caused, golden path) | EV-10 |
| The Weir / the old channel | Dry river channel west of town | JN-2 (OP-2B) |
| The Salt Shrine / White Stair | Hill shrine of the priors | JN-2 (OP-2C) |
| Kingsweir | Seat of the River Kings | EV-03 |
| The North Marches | Where the background war kindles | EV-12 |

### People & lines
| Name | Role | Trace relevance |
|---|---|---|
| Aldis the miller | Walks with Life 1 to the hill; the witness | TR-C (◦ the miller's line) |
| King Osric / the crown of Kingsweir | The River Kings' line | Background authority |
| Prior Maddoc | Prior of Undermount, Life 2's antagonist | JN-4 tithe crisis |
| Berin the ferryman / Maren the healer | Witnesses of the untaken JN-2 options | §2.7 branches |

### Eras (front-matter structure)
| Era | Years | Content |
|---|---|---|
| The Era of Floods | ~120–200 | EV-01, EV-02 |
| The Era of the River Kings | ~350–409 | EV-03, EV-04 |

---

## 2. Tutorial Event Catalog

Every entry: **id · year · print/Hand copy (verbatim, budgeted) · parents ·
where it surfaces**. Copy is final-draft quality but subject to the voice guide
(direction-doc deliverable 4); *structure and role are binding, wording may be
polished.*

### 2.1 Pre-player events (front matter, P-03 — beat B1)

- **EV-01 · ~122 · print:** "In the Drowning, the river took the vale and left
  it salt." *(Era of Floods, spread 1; plate: the drowned valley.)*
- **EV-02 · ~140 · print:** "The flood-priests raised wellworks beneath the
  hill, and sealed their undercroft against the water's return." — *the
  load-bearing mention*: plants the word **undercroft** twenty minutes before
  B13 pays it off. *(Spread 1, mid-passage, unmarked — Δ1.)*
- **EV-03 · ~356 · print:** "The River Kings rose at Kingsweir and counted the
  fords." *(Spread 2.)*
- **EV-04 · 401 · print:** "In the four-hundred-and-first year the rains
  thinned, and did not return." *(Spread 2, final line before aside ✎#1.)*

### 2.2 Life 1 — the warden's heir of Brant Ford (409–412)

**P-04 opening (B2):** *The First Life.* "Year 409. Brant Ford, in the third
rainless year. A warden's heir who keeps the tally-book." *(≤3 sentences ✓.)*

**JN-1 · 411 · The Granary Assembly (B3) — teaches select/seal; all ephemeral**
Situation (print, 58 words): "The third rainless year. Brant Ford's granary
holds one winter's grain; the town holds two winters' mouths. The assembly
waits on the keeper of the tally-book."
| Option | Outcome event (ephemeral — no durable trace) |
|---|---|
| OP-1A "Open the granary to all, and let the tally answer for it." | EV-05a: "The grain went further than feared; the tally-book became a small famous thing." |
| OP-1B "Send the tally to Kingsweir and petition the crown's grain." | EV-05b: "The crown's barges came late, but they came." |
| OP-1C "Ration by drawn lots, sparing none by name." | EV-05c: "The lots spared no one by name, and were cursed evenly." |
*(B4: outcome page is quiet by design — no S-03 here.)*

**JN-2 · 411 · The Hill (B5) — the guaranteed plant (G-1)**
Situation (print, 64 words): "West of town the hill stands dry-springed.
Beneath it the flood-priests' undercroft has been sealed since the Drowning —
*against the water's return*, the old stone says. Aldis the miller, whose
wheel hangs dead over the dry race, walks with you to the hill's foot."
| Option | See |
|---|---|
| **OP-2A "Break the seal and go down into the undercroft."** | Golden path, below |
| OP-2B "Clear the old channel at the Weir and turn the river through it." | §2.7 |
| OP-2C "Carry the salt-sick up to the shrine and make the priors take them in." | §2.7 |

**EV-06 · 411 · the sealed act (B6, P-07 + S-03)**
Hand: "You break the flood-priests' seal, and with Aldis bearing the lamp you
bring the wellworks of the old faith to light. Water rises in the hill's
throat for the first time in living memory."
Print: "The valley talks of little else that year."
Margin: **⟜ drawn live** + print: *"This will echo."* + aside ✎#2.
Traces planted by this one act (the INV-1 triple):
| Trace | Kind | Content | Fate |
|---|---|---|---|
| TR-A | ⟜ causal | the opened undercroft / wellworks | Loud — delivered (DG-1) |
| TR-B | ❧ legacy | **the Undercroft Pact** (forms at EV-08, posthumously) | Quiet — reserved (never in a digest) |
| TR-C | ◦ memory | Aldis → the miller's line remembers "the one who opened the hill" | Witness — delivered (DG-2) |

**EV-07 · 412 · first death (B7, P-08)**
Hand: "The fever came in autumn of the twelfth year. The last line stops
mid—" *(no pronoun, no evaluation; ink dries; "The First Life.")*

### 2.3 The first skip (412 → 466) and the rebirth spread (B8–B9)

Skip events (P-09 shows 2–4 as half-legible fragments only):
- **EV-08 · 421 ·** "Hill-folk and the miller's kin set down the **Undercroft
  Pact**: a pilgrim's toll for the keeping of the wellworks, sworn at the
  opened door." *(parent EV-06 — TR-B becomes a named institution; note it
  forms nine years after the death: the quiet echo is itself a consequence
  never seen.)*
- **EV-09 · 426 ·** "The first salt-pilgrims come to drink at the hill."
  *(parent EV-06.)*
- **EV-10 · 443 ·** "Undermount chartered: a shrine city raised around the
  wellworks." *(parents EV-09, EV-08.)*
- **EV-11 · 449 ·** "The Long Drought breaks in the west." *(background, no
  player parent.)*
- **EV-12 · 458 ·** "War kindles in the North Marches over the toll-roads."
  *(background.)*

**P-10 digest (B9) — D-03: ≤3 lines, last life only; Δ3: EV-08 excluded**
| Line | Mark | Copy |
|---|---|---|
| DG-1 (← EV-10) | ⟜ | "The undercroft your last life unsealed is now a shrine city — Undermount." |
| DG-2 (← TR-C) | ◦ | "The miller's line still tells of the one who opened the hill." |
| DG-3 (← EV-12) | — | "In the north, a war nobody remembers starting." |
Map (right page): Undermount marked ⟜ at the hill; mill marked ◦ at Brant
Ford; the Marches drawn, unmarked.

### 2.4 Life 2 — the lay-clerk of Undermount (466–491)

**P-04 opening (B10):** *The Second Life.* "Year 466. Undermount, the shrine
city, born under the wellworks' bells. A lay-clerk of the pilgrim rolls."
*(INV-4: born inside the loud echo.)*

**EV-13 · 466 · the withhold prose (B11, P-05 — unmarked per Δ1):**
Print, mid-passage: "…the pilgrim toll, set down in the **Undercroft Pact**,
keeps the wall and the wellworks in repair, though the priors grudge every
clipped coin of it…"

**JN-3 · 470 · The Pilgrim Census (B12) — the rhythm juncture (INV-8); all ephemeral**
Situation (print, 44 words): "The pilgrim rolls have doubled in ten years,
and the granary count is short again. The reeves ask the clerk: who is of the
city?"
| Option | Outcome (ephemeral) |
|---|---|
| OP-3A "Count the pilgrims among the mouths." | EV-13a: "The count grew honest and the bread thin." |
| OP-3B "Count only the settled." | EV-13b: "The count stayed neat and the alleys hungry." |
| OP-3C "Petition the priors' granary." | EV-13c: "The priors gave, and wrote down what they gave." |

**JN-4 · 474 · The Tithe Crisis (B13) — THE RECOGNITION JUNCTURE**
Situation (print, 52 words): "Prior Maddoc claims a shrine-tithe on the river
towns' grain — *for the water is the shrine's*. The towns' reeves stand in the
rolls-room with the old compact-book open, waiting on the clerk."
| Option | Mark | Outcome event |
|---|---|---|
| **OP-4A "Invoke the Undercroft Pact against the tithe."** | **❧** (first mark ever on a choice; one-time pulse) | EV-14: "The clerk reads the Pact against the prior; the tithe is halved, and pact-law is entered into shrine law." *(plants TR-D ❧ — Life 2's own quiet plant)* |
| OP-4B "Grant the tithe, and write it small in the rolls." | — | EV-14b: "The tithe was granted; the Pact slept in the compact-book." *(TR-D not planted; see JN-5 note)* |
| OP-4C "Send to Kingsweir for the crown's judgement." | — | EV-14c: "Kingsweir ruled for the towns, citing *the compact of the hill*; the crown's hand entered shrine law." *(plants TR-D′ ❧ crown-entanglement)* |

**S-02 reveal (hold on OP-4A):** print stays; older Hand blooms:
*"— your first life, who broke the seal and opened the undercroft beneath the
hill."*
**Fallback (seal OP-4A without holding):** delayed bloom on P-07 beside
EV-14: *"…as your first life once began."*

**JN-5 · 484 · The Wellworks Charter (new — closes GAP-1) — ALL options marked**
Situation (print, 49 words): "The wellworks silt, and priors, toll-men, and
millers trade blame. A charter must be sealed for the keeping of the hill —
and every party at the table stands on something older than themselves."
| Option | Mark | Descends from | Outcome (one line) |
|---|---|---|---|
| OP-5A "Seal the charter on the Pact's own terms." | ❧ | EV-08 | EV-15a: "The charter took the Pact's words for its own." |
| OP-5B "Give the keeping to the pilgrim wardens of the opened door." | ⟜ | EV-06/EV-09 | EV-15b: "The wardens of the door took up the keeping." |
| OP-5C "Name Aldis's line hereditary keepers of the race and wheel." | ◦ | TR-C | EV-15c: "The wheel's keeping passed to the miller's line by charter." |
Role: **the G-3 backstop.** A player who reaches JN-5 with no recognition
cannot avoid sealing marked content; the fallback bloom fires here at the
latest. (Holding any option instead yields an earned S-02 with the matching
origin line.) All three marks are honest (D-08): every option really descends.

**EV-16 · 491 · second death:** Hand: "The clerk of the rolls died old, and
was buried inside the wall the toll had kept." *(the death itself points back
at the player's own first-life echo — quiet attachment beat.)*

### 2.5 The second skip (491 → 536) and Life 3 (optional — B15)

Skip events: **EV-17 · 503 ·** "Pact-law is taught at the clerks' bench of
Undermount." *(parent EV-14; golden path)* · **EV-18 · 521 ·** "Kingsweir's
old line fails; cousins contest the crown." *(background.)*

**P-10 digest #2** (variant-dependent; golden path):
| Line | Mark | Copy |
|---|---|---|
| DG-4 (← EV-17) | ❧ | "The pact your last life read against the prior is now taught as law." |
| DG-5 (← EV-15c, if sealed) | ◦ | "The keepers of the wheel bear your charter's seal." |
| DG-6 (← EV-18) | — | "At Kingsweir, cousins contest a failing crown." |

**P-04 opening:** *The Third Life.* "Year 536. A traveling scribe of the
rolls, on the river road."

**JN-6 · 539 · The River Road — free play; one natural discovery (E8, unguaranteed)**
Situation (print, 41 words): "At Brant Ford the ferry waits on the miller's
word, as it has since the charter. The road runs three ways from the
mill-yard."
| Option | Mark | Note |
|---|---|---|
| OP-6A "Lodge at the mill and copy their charter-book." | ◦ | Hold → S-02: *"— your first life, who walked with Aldis to the hill's foot."* (unguaranteed natural discovery) |
| OP-6B "Survey the old channel at the Weir for the crown's cousins." | — | The road not taken made visible: the Weir is *still dry* (replay-itch content, SC-4) |
| OP-6C "Take the salt road north, where the war smoulders." | — | Background thread; texture |
Outcomes EV-19a/b/c, one line each, ephemeral or minor.
**EV-20 · 5xx · third death:** "The scribe died on the road between two towns,
the rolls unfinished." *(mid-sentence death echo; the world will finish them.)*

### 2.6 The final skip (→ 803), the ending, and the trace chain (B16–B17)

Skip events: **EV-21 · 641 ·** "A lay council is seated at Undermount,
empowered by pact-law." *(parents EV-17 ← EV-14; EV-10.)* · **EV-22 · 712 ·**
"The North war ends; the toll-roads open." *(background.)* · **EV-23 · 803 ·**
"**The Accord of the Three Cities** — Undermount, Brant Ford, Kingsweir —
sworn *in the manner of the old Pact, at the opened door*." *(parents EV-21;
EV-08 by manner.)*

**P-12 (B16):** "Here ends the Chronicle of the Salt Kingdoms, four hundred
years from drought to accord." Rubricated line (D-06, the world's only one):
❧ *"And the Accord of the Three Cities holds, sworn in the manner of the pact
begun beneath the hill — your first life's doing."*

**P-14 trace chain (B17) — revised, now passes through BOTH lives (GAP-4):**
| Card | Content |
|---|---|
| CH-1 | ≈ THE ACCORD OF THE THREE CITIES · 803 (← EV-23) |
| CH-2 | ≈ a lay council seated at Undermount · 641 (← EV-21) |
| CH-3 | ~the clerk reads the Pact against the prior · 474 — **your second life** ~ (← EV-14) |
| CH-4 | ≈ the Undercroft Pact sworn at the opened door · 421 (← EV-08) · **«You were not alive to see this.»** |
| CH-5 | Origin card: ~year 411 — **your first life**, who broke the seal and opened the undercroft beneath the hill~ (← EV-06) |
Five links (INV-6: 3–5 ✓); posthumous stamp at CH-4 ✓; **two of the player's
lives appear in one chain** — SC-2's answer becomes "my first life opened it,
my second life made it law."

**P-15 (B18):** the spine reads *The Chronicle of the Salt Kingdoms*; beside
it, a new empty slot; *"A different world could hold a different you."*

### 2.7 Branch catalog (the non-golden JN-2 paths — G-1 for every seal)

Structural mirror of §2.2–§2.6; same beats, same rules, names swapped. The
INV-1 triple per option:

| | OP-2B (the Weir) | OP-2C (the Stair) |
|---|---|---|
| Sealed act (Hand) | "You clear the old channel with Berin's ferry-gang, and the river remembers its way." | "You carry the salt-sick up the shrine stair until the priors open the gate." |
| Loud echo ⟜ (digest #1) | EV-B1: "Weirsend rises where the water turned — a port town at the channel's mouth." → DG-B1: "The channel your last life cleared has raised a port town — Weirsend." | EV-C1: "White Stair consecrated: a sanctuary city on the shrine road." → DG-C1: "The stair your last life climbed is now a sanctuary city — White Stair." |
| Quiet echo ❧ (reserved; forms in skip) | EV-B2 · 423: "The ferry-kin set down the **Channel Rule**: water shared by the turning of the wheel." | EV-C2 · 424: "The carriers swear the **Stair Rule**: none turned away at the gate." |
| Witness ◦ (digest #2) | Berin → "The ferryman's line still tells of the one who turned the river." | Maren → "The healer's line still tells of the one who would not stop climbing." |
| Life 2 birthplace (INV-4) | Weirsend | White Stair |
| Withhold prose (B11) | "…the wheel-shares, set down in the Channel Rule, feed the lower quays…" | "…the gate-bread, owed under the Stair Rule, is counted before the crown's grain…" |
| Marked option (B13) | ❧ "Invoke the Channel Rule against the quay-masters." | ❧ "Invoke the Stair Rule against the closed gate." |
| S-02 reveal | "— your first life, who turned the river through the Weir." | "— your first life, who carried the sick up the salt stair." |
| JN-5 equivalent (all marked) | The Quay Charter (Rule ❧ / channel-wardens ⟜ / Berin's line ◦) | The Gate Charter (Rule ❧ / stair-wardens ⟜ / Maren's line ◦) |
| End-era accord (803) | "The Accord of the River — sworn by wheel and share." | "The Accord of the Open Gate." |
| Chain CH-1→CH-5 | Accord → water-court 6xx → Rule invoked (Life 2) → Channel Rule 423 «not alive» → origin 411 | Accord → hospice synod 6xx → Rule invoked (Life 2) → Stair Rule 424 «not alive» → origin 411 |

**Counterfactual quarantine (GAP-2 rule):** content originating in an untaken
JN-2 option never appears on another path — on the golden path there is no
Weirsend and no White Stair; the Weir stays dry (OP-6B shows it dry), the
shrine gate stays shut. The world's background (Kingsweir, the North war, the
drought's end) is path-independent; everything player-adjacent is path-pure.

---

## 3. Event Dependency Graph (golden path)

```
 EV-01 Drowning ──▶ EV-02 undercroft sealed ─────────────┐
 EV-03 River Kings ─▶ EV-04 drought 401 ─▶ JN-1 ─▶ EV-05x (ephemeral)
                                        └▶ JN-2 ═▶ EV-06 undercroft OPENED (411)   ◀ the player's act
                                                      │        │
                     death EV-07 (412)                │        ├─▶ TR-C miller's line ─▶ DG-2 ─▶ OP-5C/OP-6A (◦)
                                                      │        │
                          ┌── skip 412–466 ───────────┼────────┘
                          │   EV-08 Undercroft Pact (421) ◀─ quiet echo (reserved)
                          │        │      EV-09 pilgrims (426) ◀─┐
                          │        │           │                 │ (both ← EV-06)
                          │        └──┬────────┴─▶ EV-10 UNDERMOUNT (443) ─▶ DG-1
                          │   EV-11 drought breaks · EV-12 north war ─▶ DG-3   (background)
                          │
 Life 2 (466): EV-13 prose "Undercroft Pact" (← EV-08, unmarked)
   JN-3 census (ephemeral) ─▶ EV-13x
   JN-4 tithe ═▶ EV-14 Pact invoked (474) (← EV-08)  ◀ recognition juncture
   JN-5 charter ═▶ EV-15x (← EV-08 / EV-06 / TR-C)   ◀ all-marked backstop
                          │
                          ├── skip 491–536: EV-17 pact-law taught (← EV-14) ─▶ DG-4
                          │                 EV-18 crown fails (background) ─▶ DG-6
 Life 3 (536): JN-6 river road ─▶ EV-19x  (OP-6A ◦ ← TR-C)
                          │
                          └── final skip → EV-21 lay council 641 (← EV-17, EV-10)
                                           EV-22 war ends 712 (background)
                                           EV-23 ACCORD 803 (← EV-21; manner ← EV-08)
                                                 │
                              P-12 rubric ─▶ P-14 chain: EV-23→EV-21→EV-14→EV-08→EV-06
```

Reachability check: every Confirm surface (DG-1/2/4/5, S-02, rubric, CH-1…5)
has an unbroken parent path to a sealed player act. No confirm floats free; no
player act on the golden path is echo-less. ✓

---

## 4. Beat-by-Beat Verification (B0–B18 × concrete content)

| Beat | Concrete content | Verified |
|---|---|---|
| B0 shelf/cover | Empty slot; spine text *The Chronicle of the Salt Kingdoms* (post-run) | ✓ |
| B1 front matter | EV-01…EV-04; undercroft mention = EV-02; aside ✎#1 | ✓ |
| B2 Life 1 opens | P-04 copy §2.2 | ✓ |
| B3 juncture 1 | JN-1 + OP-1A/B/C + EV-05a/b/c | ✓ |
| B4 quiet outcome | EV-05x, no S-03 | ✓ |
| B5 the hill | JN-2 + three options | ✓ |
| B6 plant + cue | EV-06 + TR-A/B/C + S-03 + ✎#2 | ✓ |
| B7 first death | EV-07 | ✓ |
| B8 skip | EV-08…EV-12 as fragments | ✓ |
| B9 digest + map | DG-1/DG-2/DG-3; map marks | ✓ |
| B10 Life 2 opens | P-04 copy §2.4 (born in Undermount) | ✓ |
| B11 withhold | EV-13 prose (unmarked, Δ1) | ✓ |
| B12 rhythm | JN-3 (unmarked, ephemeral) | ✓ |
| B13 recognition | JN-4 / OP-4A ❧ / S-02 reveal / fallback bloom | ✓ |
| B14 life closes | JN-5 (backstop) + EV-16 | ✓ (JN-5 added — GAP-1) |
| B15 Life 3 | JN-6 / OP-6A ◦ (E8) / OP-6B road-not-taken | ✓ |
| B16 final page | EV-23 + rubric line | ✓ |
| B17 trace | CH-1…CH-5 (revised — GAP-4) | ✓ |
| B18 closing | P-15 copy + empty slot | ✓ |

No beat references exemplar-only content; every quoted line in
`v1_tutorial_world_proof.md` §1.2 now has a cataloged source. ✓

---## 5. Discovery-Rule Mapping (content unit → rule → tier)

| Content | Rule(s) | Tier |
|---|---|---|
| EV-02 "sealed undercroft" mention | D-01, Δ1 | Withhold (seeded vocabulary) |
| S-03 at EV-06 (⟜ + "This will echo.") | D-01 (no attribution language) | Promise |
| DG-1 / DG-2 (attributed, last life) | D-03 (2 of ≤3 lines) | Confirm — delivered |
| DG-3 war line (unattributed) | D-01 | Contrast (teaches the digest's limits) |
| EV-08 Pact — absent from digest | Δ3 / INV-2 | Reserved |
| EV-13 prose naming the Pact | D-01, D-02(Δ1), D-04 | Withhold |
| OP-4A mark ❧ (+ one-time pulse) | D-02, D-07 (guaranteed instance), G-4 | Hint |
| S-02 reveal on OP-4A | D-05 (player-first), D-04 (permanent) | Confirm — earned |
| Fallback bloom (JN-4/JN-5 seal) | D-05 (action-tied), G-3 | Confirm — earned (weak) |
| JN-5 all-marked options | D-02, D-08 (all honestly descended) | Hint (backstop) |
| DG-4 / DG-5 (digest #2) | D-03 | Confirm — delivered |
| OP-6A ◦ (miller's line, Life 3) | D-02, D-07 (rarity begins — unguaranteed) | Hint → earned Confirm |
| OP-6B dry Weir | D-01 | Withhold (counterfactual made visible; SC-4 fuel) |
| P-12 rubric (Accord line) | D-06 (the world's single seeded confirm) | Confirm — seeded |
| CH-1…CH-5 stepwise | D-05 (one link per input), stamp at CH-4 | Confirm — earned, staged |

Coverage: D-01…D-08 each appear at least once with concrete content; no
content unit violates its tier. Cross-checked against
`v1_tutorial_world_proof.md` §2 (events E1–E8 ↔ rows above). ✓

---

## 6. INV-1…INV-8 Verification Checklist

| INV | Requirement | Evidence | Verdict |
|---|---|---|---|
| INV-1 | Every JN-2 option → loud ⟜ + quiet ❧ (named institution current in Life 2) + witness ◦ | Golden: TR-A/TR-B/TR-C (§2.2). Branches: §2.7 rows 2–4 (Channel Rule / Stair Rule + Berin / Maren) | **PASS** |
| INV-2 | Digest delivers loud + witness; quiet echo absent from digest yet named in Life 2 prose and sealable as a marked option | DG-1/DG-2 vs. EV-08 excluded; EV-13 prose; OP-4A (branches: §2.7 rows 7–8) | **PASS** |
| INV-3 | Life 1 ends ~2 junctures in, after the plant, promise fresh | JN-1 (411) → JN-2 (411) → EV-07 (412): death one year after the plant | **PASS** |
| INV-4 | Life 2 born inside/adjacent to the loud echo | Undermount birth (golden); Weirsend / White Stair (branches) | **PASS** |
| INV-5 | Marked option is legitimate and non-punitive | OP-4A halves the tithe — beneficial, principled; never a trap (branch equivalents likewise) | **PASS** |
| INV-6 | End-era chain 3–5 links; ≥1 link post-dates Life 1's death | CH-1…CH-5 = 5 links; CH-4 (421) > death (412), stamped | **PASS** |
| INV-7 | ≤3 lives, ≤8 junctures, page budgets held | 3 lives; 6 junctures; situations 41–64 words (≤120 ✓); digests ≤3 lines ✓ | **PASS** |
| INV-8 | ≥1 unmarked juncture in Life 2 before the marked one | JN-3 census (470) precedes JN-4 (474) | **PASS** |

All eight invariants verified against authored content — **with one
structural addition required to make G-3 airtight (JN-5; §8 GAP-1).**

---

## 7. SC-1…SC-4, Step by Step, in Actual Content

**SC-1 (recognition ≤30 min, unaided).** EV-02 seeds "undercroft" (min ~2) →
EV-06 makes it *the player's word* (min ~9) → DG-1 attributes the *city*, not
the Pact (min ~12) → EV-13 names the Pact in cold prose (min ~15) → OP-4A
presents "Invoke the Undercroft Pact" under a ❧ mark (min ~19) — three
exposures to the noun, one mark, zero attributions. Hold → *"— your first
life, who broke the seal and opened the undercroft beneath the hill."*
Failure paths: seal-without-hold → bloom at EV-14; total avoidance → JN-5
cannot be exited without sealing marked content. **Achievable, with backstop,
on every JN-2 branch.**

**SC-2 (explain one event's origin).** The chain the player can retell after
B17: *"The Accord of 803 is sworn in the manner of the Pact. The council that
swore it sat because pact-law was taught; it was taught because my second life
read the Pact against Prior Maddoc; the Pact was sworn at the door my first
life opened."* Every link is a cataloged event (EV-23→EV-21→EV-14→EV-08→
EV-06). The retelling names **two of the player's lives** — richer than the
criterion demands.

**SC-3 (death ≠ game over).** The content sequence: EV-06 leaves an explicit
open promise ("This will echo", min ~9) → EV-07 kills the life *one year
later* with the promise unresolved → DG-1 resolves it ~90 seconds of real
time after the death. The anticipation is carried by content (an unpaid
promise), not by copywriting on the death page — which stays evaluation-free.

**SC-4 (a different mark, nameable).** The content supplies three concrete
nameable intentions before the shelf prompt: the dry Weir seen at OP-6B
("next time: turn the river"), the shut shrine gate implied by the quarantine
("next time: the stair"), and the ◦ thread ("next time: be remembered the
whole way"). B18's empty slot asks the question; the untaken JN-2 options are
the answer bank. The exit-interview pass ("names a different intended mark")
has actual nouns to land on.

---

## 8. Gaps Found and Revisions Made

Validation against concrete content surfaced five issues; all are resolved in
this catalog, two required upstream edits:

- **GAP-1 (G-3 hole — SC-1 could be dodged).** The script guaranteed
  recognition only for players who hold or who seal *the* marked option. A
  player sealing OP-4B/OP-4C and never holding would finish the world
  unrecognized. **Fix:** JN-5 "The Wellworks Charter" — a late Life-2 juncture
  whose options are *all* honestly marked; sealing anything triggers the
  fallback at the latest. Life 2 is now fixed at three junctures.
  *(Upstream: `v1_tutorial_world_proof.md` §1.1 "two to three junctures"
  should read "three"; logged for edit.)*
- **GAP-2 (counterfactual collision).** Background content could accidentally
  contain an untaken option's outcome (a port at the Weir existing on the
  golden path would make OP-2B's road-not-taken a lie). **Fix:** the
  counterfactual-quarantine rule (§2.7): untaken-option content never appears
  on other paths; path-independent background is enumerated (Kingsweir, the
  North war, the drought's end).
- **GAP-3 (year inconsistencies).** Earlier wireframes/scripts used
  illustrative years (pilgrimages "466", origin "412"). **Fix:** this
  document's timeline is canon (pilgrims 426, origin act 411, death 412);
  wireframe years in `v1_ux_spec.md` §9 are hereby declared illustrative.
- **GAP-4 (trace chain wasted Life 2).** The scripted B17 chain
  (Accord→council→pilgrims→origin) skipped the player's second life entirely.
  **Fix:** canon chain routes through EV-14 (CH-3, *"your second life"*) —
  SC-2's retelling now includes two lives at no extra cost. *(Upstream:
  `v1_tutorial_world_proof.md` B17 example; logged for edit.)*
- **GAP-5 (witness mortality).** Aldis cannot personally span 411→539.
  **Fix:** TR-C is defined as *the miller's line* from its first delivery
  (DG-2's copy already says "line"); OP-6A meets the line, not the man; the
  S-02 reveal at OP-6A names Aldis only in the past tense.

---

## 9. Remaining Risks and Required Implementation Assumptions

Assumptions the implementation must make true (each with what breaks if
false). These are the *only* open questions between this proof and
implementation planning:

- **A-1 (realization mode).** The tutorial world is realized either by (a)
  finding a seed whose generated world is *structurally equivalent* to this
  catalog, or (b) presenting a curated deterministic starting scenario. Under
  (a), **structure is binding, proper nouns re-bind** to the found world's
  names (the catalog then serves as the search specification, and §2's copy
  becomes templates over found names). Under (b), the catalog is used as-is.
  *If neither is possible, INV-1/INV-2 fail and SC-1 loses its guarantee —
  this is the residue of risk R-B and the first thing implementation planning
  must decide.*
- **A-2 (causal ancestry is queryable).** Every cataloged parent link
  (EV-23→EV-21→EV-14→EV-08→EV-06) must exist as walkable ancestry in the
  finished world. *Breaks: P-14 / SC-2.* (Grounds for confidence: the
  timeline/causal read-models already expose event ancestry and life
  attribution.)
- **A-3 (attribution to a specific life).** Acts must be attributable to
  "your Nth life" at reveal time. *Breaks: S-02 grammar, CH-3/CH-5, DG
  lines.* (Grounds: attribution-by-life already exists in the heritage data.)
- **A-4 (named institutions).** A quiet echo must carry a *stable name* usable
  in prose (EV-13), as an option label (OP-4A), and in chain cards — the same
  name in all three places. *Breaks: the withhold beat and recognition both.*
- **A-5 (digest curation).** The tutorial's digest must deliver exactly
  DG-1/DG-2/DG-3 (Δ3: never EV-08). *Breaks: INV-2 → SC-1.*
- **A-6 (memory persistence across two skips).** The miller's line (◦) must
  still be surfaceable at year 539 (128 years, two skips, under whatever
  memory decay exists). *Breaks: OP-6A/E8 and DG-5 only — SC-1…SC-4 do not
  depend on it.* Mitigation if false: replace OP-6A's ◦ with a ❧
  (charter-book without the remembering line); E8 becomes ❧-flavored.
- **A-7 (fixed span, final long skip).** The world must end at a fixed year
  (803) with a last skip long enough (≥250 y) for EV-21/EV-23 to mature.
  *Breaks: B16/B17, D-06 content.*
- **A-8 (juncture placement).** Junctures must occur at the cataloged
  narrative moments (assembly, hill, census, tithe, charter, road) with the
  cataloged option sets. *Breaks: the beat timeline (§4) generally.*

Design-level risks that remain open (not blockers, tracked):

- **R-1:** A-1(a) search cost is unknown; A-1(b) needs a policy decision on
  curated tutorial content vs. pure generation. Owner decision required.
- **R-2:** Copy above is written in English; the JP question (Q2/Q-UX-9) still
  gates the voice guide. Names in this catalog were chosen to survive
  translation (concrete nouns, no puns).
- **R-3:** The standard-world digest rule (Q-UX-4 general case) remains open;
  nothing in this catalog depends on it.
- **R-4:** Branch catalogs (§2.7) are one structural table deep; before
  implementation, each branch needs the same full-copy pass as the golden
  path (estimated: ×2 of §2.2–§2.6's copy volume — schedule it with the
  voice-guide work).

**Acceptance status against this task:** every beat references concrete
content (§4) · no placeholder events remain on the golden path (§2; branches
at structural-parity depth, R-4) · INV-1…8 explicitly verified (§6) · SC-1…4
explained step-by-step in actual content (§7) · residual uncertainty is A-1…
A-8 / R-1…R-4 with evidence and mitigations (§9).
