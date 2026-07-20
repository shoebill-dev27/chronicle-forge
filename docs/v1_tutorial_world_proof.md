# Chronicle Forge v1 — Tutorial World Proof of Experience

Status: **Design / for review. No implementation.**
Authority: [`design_v1_definition.md`](design_v1_definition.md) (Success
Criteria, Principles) · [`design_v1_direction.md`](design_v1_direction.md)
(scope, risk R-B) · [`v1_ux_spec.md`](v1_ux_spec.md) (pages P-xx, states S-xx,
interactions I-xx, discovery rules D-xx, tutorial frame §8).

Purpose: prove **at design level** that the v1 Success Criteria are achievable —
not as theory but as a concrete, minute-by-minute first world in which every
guarantee (G-1…G-5) is realized, every discovery rule (D-01…D-08) is exercised
by a named event, every plausible failure is anticipated with a fix, and a
playtest plan can falsify the whole thing before release.

**What this document proves and what it cannot.** It proves the *design is
coherent*: a world with the stated structure delivers SC-1–SC-4 through the UX
spec's rules without contradiction. It cannot prove such a world *exists* in the
deterministic content space — that is the content search flagged as risk R-B.
§1.4 therefore states the exact invariants the content search must satisfy; if
they are met, this script follows. All proper nouns below (the Salt Kingdoms,
the undercroft, Aldis the miller…) are **exemplar content**: placeholders with
the right *shape*, not required names.

---

## 1. Tutorial World Script

### 1.1 The shape of the world

- **Name (exemplar):** *The Chronicle of the Salt Kingdoms.* Span ~400 years
  (409–803). **Three lives maximum**, ≤30 minutes (G-5).
- **Life 1** (409–412): a warden's child in the river town of Brant Ford, during
  the great drought. Two junctures. Dies young (the fever) — the early death is
  deliberate: the first life must end while its promise is still fresh.
- **Life 2** (466–~491): a lay-clerk in **Undermount** — the shrine city that
  exists *because of Life 1*. Three junctures (the third is the all-marked
  G-3 backstop — see `v1_content_proof.md` JN-5 / GAP-1). The recognition
  life.
- **Life 3** (~530s, optional; exists only if pacing is fast): a traveling
  scribe; free play with learned verbs; one unguaranteed natural discovery.
- **Final skip** (last death → 803): long. The world outruns the player before
  the book closes — deep time is felt one last time without them.

**The load-bearing device — "one act, two echoes."** Life 1's second juncture
(the guaranteed plant, G-1) is built so that *whichever* option is sealed, the
single act yields **three durable traces**:

| Echo | Kind | Fate |
|---|---|---|
| The **loud echo** | ⟜ causal | Delivered in the P-10 digest (the taught jolt) |
| The **quiet echo** | ❧ legacy | **Never delivered.** Reserved to surface as the marked option in Life 2 — the earned recognition (G-2) |
| The **witness** | ◦ memory | Delivered as the digest's second line (the "someone remembers" texture) |

The digest teaches "acts echo" using the loud echo; the recognition is earned
using the quiet one. D-03 (delivered reveals cover the last life only, ≤3 lines)
is never bent, even in the tutorial — the tutorial differs from a normal world
only in *guaranteeing the structure*, never in relaxing the discovery rules.

**The option-set invariant (G-1 as a table).** Every option of Life 1 / Juncture
2 carries the full triple, so choice stays real and the script survives any
seal:

| Option (exemplar) | Loud echo (delivered) | Quiet echo (reserved) | Witness |
|---|---|---|---|
| Open the sealed undercroft beneath the hill | The hill becomes the shrine city **Undermount** | The **Undercroft Pact** (pilgrim toll compact) | Aldis the miller |
| Divert the river through the old channel | The dry delta becomes the port of **Saltgate** | The **Channel Toll** (ferrymen's guild law) | Berin the ferryman |
| Carry the sick to the salt shrine | The shrine becomes the sanctuary of **White Stair** | The **Stair Rule** (healers' order) | Maren the healer |

The script below follows the golden path (the undercroft); the other two rows
follow identically with names swapped.

### 1.2 Beat-by-beat script

Format per beat: **On the page** (what is shown) → *Player's head* (expected
thought) → **Misread risk** (what they may wrongly conclude, and why it is safe
or where it is caught) → Design intent.

---

**B0 · 0:00–1:00 · P-01 → P-02 (Shelf, Cover)**
On the page: a shelf with one empty slot; choosing it starts the cover ritual.
*Player's head:* "A library. There's nothing in it yet — except me."
Misread: expects a menu/options screen. Safe: one slot affords exactly one act.
Intent: object-not-app; the empty shelf is the future promise (SC-4's stage).

**B1 · 1:00–3:00 · P-03 (Front Matter, 2 spreads)**
On the page: *The Era of Floods* (the salt flats; one plate of the drowned
valley; one passing printed mention of "the sealed undercroft beneath the
hill"). *The Era of the River Kings* (the drought begins). Closing line, aside
✎#1: *"Of the soul that returns to this world again and again, the record says
only: it writes in a different hand."*
*Player's head:* "I'm reading a book… no — I'm going to be **in** it."
Misread: "I must memorize these names." Safe: front matter is skimmable; every
name that matters recurs naturally later. (The undercroft mention is the
earliest seed of the recognition — planted 20 minutes before it pays off.)
Intent: small-but-seated (Arc beat 1); proper nouns begin accruing.

**B2 · 3:00–4:00 · P-04 (Life 1 opens)**
On the page: *The First Life*, year 409, Brant Ford, a warden's child; the Hand
signs the heading.
*Player's head:* "This is me now. The handwriting is mine."
Misread: none material.
Intent: the print/Hand contrast starts carrying meaning from the first minute.

**B3 · 4:00–6:30 · P-05 → P-06 (Juncture 1 — the drought assembly)**
On the page: the granary dispute; three options, all plain print, **no marks
anywhere** (the world is still clean): share the granary / petition the River
King / ration by lot. Select previews the act faintly in the Hand; seal commits.
*Player's head:* "Which is *correct*? …there are no numbers. Maybe there is no
correct." Misread: hunts for a stat screen or a best answer. Caught by design:
no outcome is graded, no number ever appears; the hunt starves in one juncture.
Intent: teach select→seal (I-03/I-04) on a safe page; establish "options are
acts, not outcomes."

**B4 · 6:30–7:00 · P-07 (Outcome, quiet)**
On the page: the act written in the Hand; the world's response in print. **No
plant cue** — deliberately quiet.
Intent: contrast. S-03 at the next juncture must be the first marginal event
ever, so it reads as an *event*, not as chrome.

**B5 · 7:00–9:00 · P-06 (Juncture 2 — the hill; the guaranteed plant, G-1)**
On the page: drought deepens; the frontier juncture at the hill. The three
options of the invariant table (§1.1). Still no marks (nothing is descended
from anything yet).
*Player's head:* "These feel bigger."
Misread: "this is just flavor text like the last one." Safe: corrected within
sixty seconds by B6.
Intent: the plant. Any seal satisfies G-1/G-2.

**B6 · 9:00–10:00 · P-07 + S-03 (the promise)**
On the page: *"You descend into the sealed undercroft, and bring the old engine
of the flood-priests to light."* (Hand). Print: the valley talks of little else.
Then, drawn live in the margin: **⟜** and one line of print: *"This will
echo."* Below it, small, aside ✎#2: *"Marks in the margin are the chronicle's
memory."*
*Player's head:* "Echo… when? I won't be alive for it. — oh. **That's the
game.**"
Misread: "the mark means reward/points." Caught: nothing is awarded, nothing
counts up; the mark just sits there, addressed to no one present.
Intent: the promise addressed to a future self. The player forms the game's
central hypothesis one page before dying.

**B7 · 10:00–11:00 · P-08 (first death)**
On the page: *"The fever took him in autumn. The last line stops mid—"* The ink
dries (~3 s, unskippable this once). *The First Life.*
*Player's head:* "Wait — that's it? …but the echo—"
Misread risk (**F4**): "I lost; should I restart?" Mitigations live here by
construction: death arrives with an **open promise** on the previous page, no
evaluation appears, and the page only turns forward.
Intent: SC-3's mechanism is exactly this carried anticipation across death.

**B8 · 11:00–11:30 · P-09 (the skip, 409→466)**
On the page: margins flicker through five decades; 2–4 half-legible fragments.
Unskippable in the first world (~8 s).
*Player's head:* "It's… continuing without me."
Intent: Principle 5 rendered once at full length.

**B9 · 11:30–13:00 · P-10 (the delivered jolt)**
On the page, left: *The world you return to.*
⟜ *"The undercroft your last life unsealed has become a shrine city —
Undermount."*
◦ *"The miller's line still tells of the one who opened the hill."*
≈ *"In the north, a war nobody remembers starting."* (unattributed contrast)
Right: the Map appears for the first time; Undermount marked; the tab (I-08)
exists from this moment. Touching a line focuses its mark.
*Player's head:* "The world **moved**. Because of me. And the dying was… the
point?"
Misread: "everything on the map is mine." Caught in place: the war line and
unlabeled geography say otherwise.
Intent: Arc beat 2; SC-3 sealed (death has visibly paid out); the loud echo is
spent, the quiet one still in reserve.

**B10 · 13:00–14:00 · P-04 (Life 2 opens)**
On the page: *The Second Life*, year 466, a lay-clerk **in Undermount**.
*Player's head:* "I live in the city I caused."
Intent: rebirth placed *inside* the consequence — the cheapest, strongest
attachment device the tutorial has (anti-F7).

**B11 · 14:00–16:00 · P-05 (the withhold beat)**
On the page, in plain print, unmarked, mid-passage: *"…the pilgrim toll, set
down in the **Undercroft Pact**, keeps the wall in repair…"* (running prose is
never marked — D-02 as amended; see §2.4 Δ1).
*Player's head (ideal):* "Undercroft. That word again." *(Or nothing — the beat
may pass unnoticed; both are within spec.)*
Intent: hypothesis material planted at zero pressure. Withhold.

**B12 · 16:00–18:30 · P-06 (Life 2, Juncture 1 — civic, unrelated)**
On the page: an ordinary civic juncture (the granary census), no marks.
Intent: rhythm. Not every choice is about the player (Principle 6); prevents
"mark inflation" from making B13 feel scheduled.

**B13 · 18:30–22:00 · P-06 (Life 2, Juncture 2 — THE RECOGNITION)**
On the page: the tithe crisis. Among the options:
**❧ [ Invoke the Undercroft Pact against the tithe ]** — the first mark ever
attached to a choice. On first pointer rest, the mark gives one slow pulse
(G-4; once per player, ever).
*Player's head:* "That glyph — 'the chronicle's memory.' The Pact. The
undercroft. The hill. **That was my hill.**" → holds (I-05) →
**S-02:** the print stays; beneath it an older hand blooms: *"— your first
life, who opened the undercroft beneath the hill."*
This is the peak of the game and nothing interrupts it: no sound sting over the
bloom, no follow-up prompt; the page simply waits.
**Fallback path (G-3):** if the player seals a marked option without ever
holding, P-07 stages the delayed reveal — the act is written, then the older
hand blooms beside it: *"…as your first life once began."* SC-1 is met on
either path by the end of Life 2.
Misread (**F2**): the player connected the name alone at B11 and the hold only
confirms. Accepted **in the tutorial**: a hypothesis preceding the confirm *is*
the North Star working; on-the-nose naming is the tutorial's guarantee margin.
Naming drift begins in world 2 (§3, F2).
Intent: SC-1, earned form. Arc beat 3.

**B14 · 22:00–24:30 · P-05…P-08→P-09 (Life 2 closes)**
On the page: one more short passage; the clerk dies old; a shorter skip.
*Player's head:* "What did **this** life plant?" — the player now asks the
question unprompted.
Intent: Arc beat 4 begins (from reacting to planting).

**B15 · 24:30–27:00 · Life 3 (optional, free play)**
On the page: a traveling scribe; 1–2 junctures with the learned verbs; possibly
a ◦-marked person (a descendant of Aldis's line) — **unguaranteed** (D-07:
rarity begins). The untaken roads of B5 remain visible when flipping back — the
river never diverted, the shrine never sanctified.
*Player's head:* "Next world — the river. Or someone who remembers me the whole
way through."
Intent: SC-4's itch is seeded here and at B17, not manufactured at the end.

**B16 · 27:00–28:00 · P-12 (Final Chronicle)**
On the page: *Here ends the Chronicle of the Salt Kingdoms, four hundred years
from flood to accord.* One rubricated line (D-06):
❧ *"And the Accord of the Three Cities holds, that began as a pact beneath the
hill — your first life's doing."* Invitations: read / follow this thread /
close the book. The thread-end glyph pulses once (the second and last pulse a
player will ever see, G-4).
*Player's head:* "The Accord — that's *still* mine? It's been four hundred
years."

**B17 · 28:00–29:30 · P-14 (the trace — SC-2 rehearsed)**
On the page, one input per link (I-07), per the canon chain
(`v1_content_proof.md` §2.6, revision GAP-4):
The Accord of the Three Cities, 803 → a lay council seated at Undermount,
641 → *the clerk reads the Pact against the prior, 474 — **your second
life*** → the Undercroft Pact sworn at the opened door, 421 *«You were not
alive to see this.»* → origin card: *~year 411 — your first life, who broke
the seal and opened the undercroft beneath the hill.~* The chain passes
through **two** of the player's lives.
*Player's head:* "Four hundred years, and the first domino is a choice I made
twenty minutes ago."
Intent: SC-2 in executable form; the posthumous stamp lands "consequences you
never saw" without a tutorial in sight.

**B18 · 29:30–30:00 · P-15 (Closing)**
On the page: the book closes; the spine slides beside a **new empty slot**;
*"A different world could hold a different you."*
*Player's head:* names the next mark (the river / a remembered name / a legacy
that outlives everything).
Intent: SC-4's observable — the player leaves with an intention, not a score.

### 1.3 Where the criteria land (summary)

| Criterion | Beat | Path |
|---|---|---|
| SC-1 recognition ≤30 min, unaided | **B13** (earned: hold) or B13-fallback (sealed: delayed bloom) | Guaranteed by G-1/G-2/G-3 |
| SC-2 explain one event's origin | **B17** (rehearsal) + post-session interview | Seeded confirm D-06 guarantees the entry point |
| SC-3 death ≠ game over | **B6→B7→B9** (promise → death → payout ≤2 min later) | Structural, not copy-based |
| SC-4 different mark next time | **B15 + B18** (visible untaken roads + empty slot) | Observed at exit interview |

### 1.4 Content invariants (proof obligations for the content search — R-B)

The script above holds **iff** a starting scenario satisfying all of the
following exists. This list is the acceptance test of the content search; each
failure has a named consequence.

- **INV-1 (one act, two echoes + witness).** Every option of Life 1/Juncture 2
  yields one loud echo (world-visible change by the first skip), one quiet echo
  (a *named institution* still current in Life 2), and one named witness whose
  line persists. *Breaks:* G-1/G-2 → SC-1.
- **INV-2 (digest separation).** The loud echo and the witness are deliverable
  as digest lines; the quiet echo is **absent** from the digest yet appears,
  named, in Life 2's running prose and as a sealable marked option. *Breaks:*
  the withhold beat B11 and recognition B13.
- **INV-3 (early first death).** Life 1 ends within ~2 junctures, after the
  plant, with the promise fresh. *Breaks:* SC-3's carried anticipation.
- **INV-4 (rebirth placement).** Life 2 begins inside or adjacent to the loud
  echo's location. *Breaks:* attachment (F7) and the B11 prose mention's
  plausibility.
- **INV-5 (marked option is sealable and safe).** The Life 2 marked option is a
  legitimate, non-punitive choice (recognition must never feel like a trap).
  *Breaks:* trust in marks (D-08's spirit).
- **INV-6 (span and chain).** The world's final trace chain from a still-shaping
  end-era event back to Life 1 has 3–5 links, at least one post-dating Life 1's
  death. *Breaks:* B16–B17 → SC-2.
- **INV-7 (bounded session).** ≤3 lives, ≤8 junctures total, page budgets per UX
  §4 respected. *Breaks:* the ≤30-minute bound (F5).
- **INV-8 (rhythm juncture).** Life 2 contains at least one unmarked juncture
  before the marked one. *Breaks:* mark inflation; B13 feels scheduled.

---

## 2. Discovery Validation (D-01…D-08, one event at a time)

Five fields per event: **Hidden** (what the player cannot see) · **Hint** (what
they can) · **Hypothesis** (what they are expected to think) · **Confirmation**
(how/when the game admits it) · **Effect** (target feeling).

### E1 — The plant (B6, S-03) — *promise, not attribution*
- **Hidden:** what the echo will become, when, where (IA of P-07).
- **Hint:** the ⟜ mark drawn live + *"This will echo."*
- **Hypothesis:** "something will come of this — after I'm gone."
- **Confirmation:** deliberately none here. The cue promises; it never explains.
- **Effect:** anticipation that survives death (feeds SC-3).
- Rules exercised: D-01 (no attribution language), S-03 as *promise tier*.

### E2 — The loud echo delivered (B9, digest line 1) — *the taught confirm*
- **Hidden:** every change older than the last life; every other cause of
  Undermount's rise.
- **Hint:** none needed — this is the one place teaching outranks earning.
- **Hypothesis:** pre-formed at E1 ("I'll see this again"); the digest *answers*
  it rather than replacing it.
- **Confirmation:** delivered, explicit, ≤3 lines, last-life-only (D-03), with
  map focus.
- **Effect:** the causality jolt; the loop's contract signed.
- Rules: D-03 boundary demonstrated at its maximum; D-01 everywhere else on the
  page (the war line is unattributed).

### E3 — The witness delivered (B9, digest line 2, ◦)
- **Hidden:** who exactly remembers, and what memory will *do*.
- **Hint:** the ◦ glyph now has one worked example.
- **Hypothesis:** "people can be traces too."
- **Confirmation:** partial by design — a line, not a ledger.
- **Effect:** the third trace kind enters the vocabulary without a tutorial.

### E4 — The withhold (B11, unmarked prose) — *the rule doing its hardest work*
- **Hidden:** that the Undercroft Pact descends from the player's Life 1. No
  mark, no emphasis, mid-sentence placement.
- **Hint:** only the *name* — "Undercroft" recurs from B1/B6.
- **Hypothesis:** "that word again…" (or nothing; a silent pass is in-spec
  because B13 re-presents the name **with** its mark).
- **Confirmation:** withheld here absolutely (D-01, D-02-as-amended, D-04).
- **Effect:** the itch of half-recognition — the gap the player will close
  themselves.
- **Validation note:** this beat *required* amending D-02 (marks attach at
  decision/trace surfaces only, never in running prose) — recorded as Δ1 in
  §2.4. Without the amendment, the prose would carry a mark and the withhold
  tier would not exist.

### E5 — The earned recognition (B13, hold → S-02) — *the North Star event*
- **Hidden until input:** the origin line ("your first life, who opened the
  undercroft").
- **Hint:** the ❧ mark on the option (first ever on a choice) + one-time pulse
  + the name matching B11/B6/B1.
- **Hypothesis:** "the Pact is descended from **my** act" — formed *before* the
  hold; the hold is the player *choosing to know* (I-05's whole purpose).
- **Confirmation:** the reveal grammar (D-05): print stays, older Hand blooms
  beneath, origin named. Permanent thereafter (D-04).
- **Effect:** the shiver. SC-1.
- Rules: D-01, D-02, D-04, D-05, D-07 (first guaranteed instance), D-08 (the
  mark told the truth).

### E5b — The fallback recognition (B13-alt, seal without hold)
- **Hidden/Hint:** as E5.
- **Hypothesis:** possibly none (player ignored the mark).
- **Confirmation:** delayed bloom on P-07: *"…as your first life once began."*
  Attribution arrives *after* the player's own act re-enacted the legacy —
  the weakest allowed confirm, still tied to a player action (never passive).
- **Effect:** softer recognition; SC-1 still met.
- **Boundary check:** does E5b violate "unaided" in SC-1? Ruling: no — no
  helper intervened and no answer preceded the player's act; but playtests
  must report **which path** fired, and the earned path must dominate (§4).

### E6 — The seeded confirm (B16, rubricated line) — *D-06's single exception*
- **Hidden:** everything about the chain *between* the Accord and Life 1.
- **Hint:** rubrication (the one accent, one meaning) + thread-end pulse.
- **Hypothesis:** "how can a 400-year-old accord be mine?"
- **Confirmation:** the attribution is given; the *explanation* is not — it
  must be traced (E7). D-06 buys the pull into P-14 without spending the chain.
- **Effect:** disbelief that demands investigation.

### E7 — The trace (B17, P-14) — *stepwise earned confirm*
- **Hidden:** each next link until stepped (I-07); chain length; destination.
- **Hint:** the standing invitation *"what came before?"*
- **Hypothesis:** invited at every link ("the council? the pilgrims?").
- **Confirmation:** one link per input; origin card last; the posthumous stamp
  *«You were not alive to see this»* lands mid-chain.
- **Effect:** compounding authorship; SC-2's muscle built.

### E8 — The natural discovery (B15, ◦ descendant — unguaranteed)
- **Hidden:** whether it occurs at all in a given run (D-07: rarity is real
  from here on).
- **Hint:** ◦ on a person, no pulse (pulses are spent).
- **Hypothesis:** "Aldis's line… still?"
- **Confirmation:** hold → S-02, as E5.
- **Effect:** proof that the tutorial's magic was not scripted theater — the
  world *keeps* doing this.

### 2.4 Rule-coverage matrix and spec deltas

| Rule | Exercised by | Verdict |
|---|---|---|
| D-01 withhold-by-default | E1, E2 (war line), E4 | Holds |
| D-02 hint = mark only | E4, E5, E8 | **Holds with amendment Δ1** |
| D-03 last-life window, ≤3 lines | E2, E3 (and B9's contrast line) | Holds; tutorial never exceeds it |
| D-04 no passive confirms / permanence | E4 (flip-back safe), E5 (permanence) | Holds |
| D-05 player-first staging | E5, E6→E7 (attribution given, chain earned) | Holds |
| D-06 exactly one seeded confirm | E6 | Holds (one rubrication in the world) |
| D-07 guaranteed once, rare after | E5 guaranteed; E8 unguaranteed | Holds |
| D-08 marks never lie | E5/E8 (and INV-5) | Holds |

**Spec deltas found by this validation** (applied to `v1_ux_spec.md`):

- **Δ1 (D-02 amendment):** marks attach only at decision and trace surfaces
  (P-06 options, P-10 digest lines, P-11 map, P-12/P-13 traceable events);
  running prose (P-03, P-05) is never marked even when descended. Required by
  the withhold beat (E4).
- **Δ2 (aside budget):** the historian's asides are capped at three per game;
  ✎#1 and ✎#2 are spent in §1.2; **✎#3 is reserved** as the F6 remediation
  (§3) and fires only under its trigger. No further asides may be added
  without removing one.
- **Δ3 (digest selection guard, resolves Q-UX-4 for the tutorial):** the P-10
  digest must never include a trace that is reserved for a marked option in an
  upcoming life. Stated generally: *delivered lines and reserved recognitions
  are disjoint by construction* (INV-2).

---

## 3. Failure Analysis

Format: **Causes → Observable signs (in a playtest) → Fixes** (ordered
cheapest-first; structural last).

### F1 — The player never notices ("気付けない")
- **Causes:** mark too visually quiet; hold verb never discovered (see F6);
  the B11 name passed unread *and* the B13 mark ignored; player seals fast on
  every juncture.
- **Signs:** no dwell on marked lines (>0 pointer-rest events expected); zero
  I-05 attempts through Life 2; post-session, cannot answer "who caused
  Undermount?"
- **Fixes:** (1) G-3 fallback already guarantees a reveal — verify it *lands*
  (player re-reads the bloom; if they turn past it unread, the bloom must hold
  the page until any input). (2) Strengthen the one-time pulse (duration, not
  repetition). (3) Structural: move the B11 prose mention *closer* to B13 (same
  spread) so name-recency carries weaker readers. Never fix by adding
  explanatory print (would trip F3).

### F2 — Recognition comes too early ("気付くのが早すぎる")
- **Causes:** on-the-nose derived naming (Undercroft → Undercroft Pact) lets
  the player be *certain* at B11, so B13's hold confirms nothing they doubted;
  digest accidentally covering the reserved trace (guarded by Δ3/INV-2).
- **Signs:** player states the full attribution aloud at B11; at B13 holds
  instantly and reports "it told me earlier," not "I worked it out."
- **Fixes:** none in the tutorial — early *hypothesis* is the North Star
  functioning, and the tutorial deliberately buys certainty as guarantee
  margin. From world 2 (Q-UX-7): (1) naming drift — quiet echoes take names
  displaced by one step (the *Toll of Weirs*, not the *Channel Toll*); (2)
  longer gaps between mention and marked option. The failure to actually watch
  for: players reporting the tutorial's transparency as *the game's* fixed
  difficulty ("it will always tell me") — probe for this expectation at exit.

### F3 — The game over-explains ("教え過ぎる")
- **Causes:** copy drift under deadline (attribution language leaking into
  print); digest exceeding 3 lines; asides multiplying; reveal grammar reused
  for non-confirm content.
- **Signs:** players stop holding marks ("the game will tell me anyway");
  hypothesis language disappears from think-aloud; interviews say "it showed
  me" where the design intended "I found."
- **Fixes:** (1) mechanical copy audit — the words "you/your" may appear only
  on Confirm surfaces (P-10 lines, S-02, P-14 origin cards, P-12's one
  rubrication) — this is grep-able in content review; (2) the Δ2 aside budget;
  (3) D-03's 3-line cap enforced as a content rule, overflow goes to
  unexplained map marks (Q-UX-4 proposal).

### F4 — Death feels like game over ("死がゲームオーバーに感じる")
- **Causes:** evaluation-flavored death copy; too long a gap between death and
  payout; death arriving *before* any plant (nothing carried across); somber
  audio/motion overweight.
- **Signs:** at P-08: reaching for a menu, asking "did I lose?", restart
  attempts, quitting during P-09; SC-3 interview codes "loss" without
  "anticipation."
- **Fixes:** (1) copy audit: P-08 carries zero evaluative words (no "only,"
  "merely," "failed"); (2) pacing budget: death → digest ≤120 seconds
  (B7–B9 currently ~90 s — protect this number); (3) structural guarantee
  already present: the plant (B6) always precedes the first death (INV-3);
  (4) the P-09 fragments must *tease forward* (half-legible future), never
  eulogize backward.

### F5 — Text volume drives churn ("テキスト量で離脱")
- **Causes:** page budgets exceeded (junctures >120 words; front matter >2–3
  spreads); no skim affordance; line length over ~55 chars; walls formed by
  stacked passages on P-05.
- **Signs:** reading visibly degrades to skimming before Life 2; time-to-first-
  choice >3:00; front-matter skip tab unused *and* resented (post-session:
  "slow start"); mid-page abandonment.
- **Fixes:** (1) the budgets are already hard caps in the UX spec — enforce in
  content review, no waivers; (2) the "skip to your first life" tab must be
  visible on spread 1 of P-03; (3) structural: if churn persists, cut front
  matter to one spread — the world's depth is better proven by B9 than told
  by B1.

### F6 — The hold is never discovered ("長押しに気付かない")
- **Causes:** pulse missed (eyes on options text, not margins); no textual
  affordance by design; keyboard users lack the pointer-rest trigger.
- **Signs:** zero I-05 across the session; SC-1 arrives via fallback in >½ of
  testers; glyph key (S-01) never opened.
- **Fixes:** (1) the reserved aside ✎#3 (Δ2): if a player seals **two** marked
  options in one world without ever holding, the next marked content carries
  one line of small print: *"Hold a mark, and the chronicle remembers."* Fires
  at most once per player, ever. (2) Keyboard parity: focused marked line
  shows the same pulse. (3) Structural (last resort, changes I-05): first hold
  auto-primes on the B13 pulse — rejected unless rounds R1 *and* R2 both fail
  the earned-path bar, because it erodes "choosing to know."

### F7 — No attachment to the world ("世界への愛着が生まれない")
- **Causes:** generic content (names with no recurrence); the player's echoes
  landing *off-page* (never revisited); worlds read as interchangeable; the
  map never opened.
- **Signs:** post-session, player cannot name the world, any place, or any
  NPC; map opened 0–1 times; SC-4 answered generically ("I'd just play
  again") without a named intention; no flip-back to earlier lives.
- **Fixes:** (1) INV-4 already places Life 2 inside the player's consequence —
  verify the placement is *named* in the Life 2 opening; (2) proper-noun
  recurrence rule: every noun that appears in a digest line must recur at
  least once in the following life's junctures or prose; (3) the witness's
  line (◦) should resurface once per world after its digest mention —
  people, not places, carry attachment for most players; (4) structural: the
  world epithet (Q-UX-6) derives from the player's dominant trace so even the
  shelf spine is *theirs*.

---

## 4. Playtest Plan

Purpose: **falsify SC-1–SC-4 before release.** The plan tests the experience,
not the software; Round 0 runs on paper.

### 4.1 Rounds

| Round | When | Fidelity | Testers | Goal |
|---|---|---|---|---|
| **R0 — table read** | before implementation planning | this script, read aloud page-by-page by a moderator with printed page cards | 2–3 | Catch copy-level failures (F3, F5) and beat-order errors for free |
| **R1 — prototype** | first playable book (lowest fidelity that renders pages, marks, hold, seal verbatim) | 5 fresh | The four SC bars (§4.4) at prototype fidelity; F1/F4/F6 signals |
| **R2 — near-final** | content-complete tutorial world | 5 fresh (+2 returning from R1 for regression only, scored separately) | The release gate: all four SC bars at final fidelity |

Fresh testers are never reused for SC measurement (recognition is one-shot by
nature). Minimum total: **12–13 people** (2–3 + 5 + 5).

### 4.2 Participant profile

Per 5-person cohort (R1, R2):

- **2 × reader-gamers** — play narrative/choice games (Pentiment, Sir Brante,
  80 Days class). The direction doc's chosen audience; they set the ceiling.
- **2 × general gamers** — play games weekly, no narrative-genre habit. They
  test the Q1 positioning risk and F5.
- **1 × light/non-gamer who reads** — books, not games. Tests whether the book
  metaphor carries interaction novices (F6's hardest case).
- All: never seen the project, no prior briefing beyond "play this; we watch."
  Language per direction-doc Q2 (a JP cohort duplicates the plan if JP ships).

### 4.3 Protocol

- **Silent observed play** — no think-aloud during Lives 1–2 (think-aloud
  contaminates the recognition moment: verbalizing hypotheses changes whether
  and when they form). The moderator never helps, never answers, and prompts
  at exactly two checkpoints, both *after* the recognition window: end of the
  world ("what are you thinking right now?") and post-P-15.
- **Observer records** (timestamped): time-to-first-choice; every I-05 attempt
  (held/cancelled); pointer-rest on marks; B13 path (earned / fallback /
  neither); behavior at P-08/P-09 (hesitation >10 s, menu reach, restart talk);
  map opens; flip-backs; any unprompted utterance (verbatim, with beat).
- **Exit interview** (structured, in this order — later questions reveal
  earlier answers):
  1. "Tell me what happened in this world." (open; SC-2 evidence if the causal
     chain appears unprompted)
  2. "Who or what caused Undermount to exist?" (SC-1/SC-2 direct)
  3. "When did you first suspect the Pact was connected to you? What tipped
     you off?" (E4/E5 staging check; F2 probe)
  4. "How did it feel when the first life ended?" (SC-3; code *loss* vs.
     *anticipation* vs. *confusion*)
  5. "If you started a new world right now, what would you do?" (SC-4; pass
     requires a *named, different* mark)
  6. "Was there anything you wished the game had just told you?" (F1/F3
     tension probe)

### 4.4 Pass bars (per 5-person cohort)

| Criterion | Bar | Additional condition |
|---|---|---|
| SC-1 | **≥4/5** recognize ≤30:00 | **≥3/5 via the earned path** (hold), not fallback |
| SC-2 | ≥4/5 explain one event's full origin unprompted or at Q2 | The chain must include the player's life and act, in their own words |
| SC-3 | ≥4/5 code as anticipation/neutral; **≤1/5** code as loss/game-over | No restart attempts at P-08 |
| SC-4 | ≥3/5 name a different intended mark at Q5 | "Play again" without a named mark does not count |
| Guard (F5) | Median session ≤35:00; 0 abandonments before P-10 | — |
| Guard (F3) | At Q6, ≤1/5 asks for *less* explanation… and ≤2/5 for *more* | The tell-me-more majority indicates F1, the tell-me-less any indicates F3 |

### 4.5 Failure triage and decision rules

- **Any bar missed in R1** → map observed signs to F1–F7 (§3), apply the
  cheapest listed fix tier, re-run R1 with a fresh cohort. Structural fixes
  (last tier of each F) require a spec change logged as a Δ against
  `v1_ux_spec.md` before retest.
- **SC-1 earned-path condition missed while SC-1 total passes** → F6 fixes
  only (the experience exists but the verb is undiscovered); do not touch
  discovery rules.
- **The same bar missed in two consecutive rounds after fixes** → escalate to
  the project owner with a written choice: slip the date or amend the
  criterion. Per the direction doc (risk R-A): **the release date moves, not
  the Core Experience** — SC-1 and SC-3 are never amendable; SC-4's bar (3/5)
  is the only one with negotiation room.
- **Stop-ship:** v1 does not release without an R2 cohort meeting all four SC
  bars. This is the gate defined in `design_v1_direction.md` §11.5, made
  operational.

### 4.6 What this plan does not test

Standard worlds beyond the first (Q-UX-7's unstaged rarity), the SHOULD scope
(Threads spread, sharing), long-horizon retention (10 h/50 h journeys), and
localization quality — all post-v1-gate concerns or separate studies.

---

## 5. Open Items

1. **The content search (R-B) is now fully specified**: find a starting
   scenario satisfying INV-1…INV-8. This is the single prerequisite between
   this document and implementation planning.
2. **Naming-drift rule for world 2+** (F2 fix): needs one page of guidance in
   the voice & copy style guide (direction-doc deliverable 4).
3. **Q-UX-4 general case**: Δ3 resolves the tutorial; the standard-world
   digest-selection rule still needs a decision.
4. **JP cohort duplication** hinges on the still-open language decision (Q2 /
   Q-UX-9).
5. **P-08 hold-until-input on the fallback bloom** (F1 fix 1) is a small UX
   spec addition if adopted — log as Δ4 when decided.
