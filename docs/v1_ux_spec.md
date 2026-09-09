# Chronicle Forge v1 — UX Specification ("The Living Chronicle")

Status: **Specification / for review. No implementation.**

> **2026-09-06 review note:** This is the historical specification, not an
> as-built inventory. ADR-001 removed the ◦ memory glyph (struck below);
> ADR-003 establishes Japanese-first and ADR-004 the horizontal baseline.
> The owner-requested [UI/UX direction review](design_v1_uiux_review.md) records
> current evidence, specification conflicts, and proposed revisions in its
> change ledger.

> **2026-09-08 baseline ratification.** The review's change ledger is **adopted**
> as [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md) (all ten items;
> UX-R1/UX-R5 with modification). Binding on this spec, applied inline below:
> - **UX-R1 / ADR-005:** the geographic Map (P-10 right page, P-11) is deferred
>   past v1. The rebirth spread is the digest (left page) alone.
> - **UX-R3:** D-03/D-04 apply to **every** surface — entry, C1 time surface,
>   digest, history, trace, resume — not only the pages they name.
> - **UX-R2:** inspect / select / commit are three separate actions (I-03/I-04
>   below); inspection has a visible, keyboard-reachable affordance, the hold is
>   an optional convenience.
> - **UX-R4:** one temporal encoding — **year = horizontal position; strata
>   depth = historical order** (not an event count standing in for years).
> - **UX-R5:** **朱 = a confirmed connection to a past life**, and nothing else;
>   ⟜/❧ stay trace-*kind* labels, never state.
> - **UX-R10:** the ◦ memory mark and "remembers you" content are removed;
>   glyph set is ⟜/❧ (ADR-001).

Authority: implements [`design_v1_direction.md`](design_v1_direction.md) (adopted) —
in particular Principle 10 (*the interface is the artifact*), Principle 11 (*one
page, one focus*), and the North Star:

> **"The player discovers, by themselves, that the history they are reading was
> written by their own forgotten past lives."**

Scope: UX only — pages, states, transitions, displayed content, interaction, visual
language, and the tutorial. No implementation, no engine detail. Where the spec
needs world data it says *"the world provides…"* and stops there.

Conventions used in this document:

- Pages have IDs `P-xx`. Overlays/states have IDs `S-xx`. Interactions have IDs
  `I-xx`. Discovery rules have IDs `D-xx`. All are referenceable requirements.
- **MUST / SHOULD** map to the §4 scope of `design_v1_direction.md`.
- "The Hand" = the player-soul's handwriting. "Print" = the historian's typeset
  voice. "Mark" = a marginal glyph attached to content descended from a past life.

---

## 1. Overall User Flow

```
            ┌────────────────────────────── replay ───────────────────────────────┐
            ▼                                                                     │
   P-01 SHELF (title)                                                             │
      │ new book                │ resume (ribbon)                                 │
      ▼                        ▼                                                  │
   P-02 COVER ──▶ P-03 FRONT MATTER (world introduction, skimmable)               │
                        │ turn                                                    │
                        ▼                                                         │
        ┌────────▶ P-04 LIFE OPENING (a life begins)                              │
        │               │ turn                                                    │
        │               ▼                                                         │
        │          P-05 LIFE PAGE (the entry being written)                       │
        │               │ a fateful moment arrives                                │
        │               ▼                                                         │
        │          P-06 JUNCTURE (choice)  ──[S-02 RECOGNITION may occur here]    │
        │               │ seal choice                                             │
        │               ▼                                                         │
        │          P-07 OUTCOME PASSAGE (the act is written; plant cue may fire)  │
        │               │ turn                        ▲                           │
        │               ├── more moments in this life ┘ (back to P-05)            │
        │               │ the life ends                                           │
        │               ▼                                                         │
        │          P-08 DEATH PAGE (the ink dries)                                │
        │               │ turn                                                    │
        │               ▼                                                         │
        │          P-09 PASSAGE OF YEARS (the book writes alone)                  │
        │               │ turn                                                    │
        │               ▼                                                         │
        │          P-10 REBIRTH SPREAD ("the world you return to" digest)         │
        └── next life ──┘                                                         │
                        │ the world's span ends (instead of another rebirth)      │
                        ▼                                                         │
                   P-12 FINAL CHRONICLE (the book is complete)                    │
                        │ read / trace                                            │
                        ├──▶ P-13 CHRONICLE READING (browse the finished book)    │
                        ├──▶ P-14 TRACE (investigation: follow one thread back)   │
                        │ close the book                                          │
                        ▼                                                         │
                   P-15 CLOSING (the book goes to the shelf) ─────────────────────┘
```

- ~~**P-11 MAP SPREAD**~~ — **deferred past v1 (ADR-005).** No map surface exists
  in v1; nothing links to one.
- **S-01 RIBBON MENU** (pause/settings/quit) is reachable from every page except
  P-02 and P-09 (which are short, non-interactive transitions).
- The loop P-04 → P-10 repeats once per life. A world contains a bounded number of
  lives; the world provides when the span ends.

---

## 2. Page Inventory

| ID | Page | Book form | Scope | One-line purpose |
|---|---|---|---|---|
| P-01 | Shelf (Title) | A shelf; books; one empty slot | MUST | Entry point: resume, new world, revisit finished worlds |
| P-02 | Cover | The chosen book, opening | MUST | 3–5 s ritual: this is an object, not a menu |
| P-03 | Front Matter | Already-printed early pages | MUST | The world's deep past; establishes "the book predates you" |
| P-04 | Life Opening | A fresh entry heading | MUST | Who you are now: era, place, station; the Hand appears |
| P-05 | Life Page | The entry in progress | MUST | Running prose of this life; the neutral "reading" state |
| P-06 | Juncture | A full choice page | MUST | A fateful moment: situation + 2–5 heavy options |
| P-07 | Outcome Passage | The act, written | MUST | The chosen act enters the entry; plant cue may fire |
| P-08 | Death Page | The entry ends | MUST | Death as punctuation; the ink dries on-screen |
| P-09 | Passage of Years | Margins flicker with years | MUST | Felt time; the book writes without you |
| P-10 | Rebirth Spread | A single page | MUST | "The world you return to": changed present, then ≤3 attributed last-life lines (ADR-005 removed the map right page) |
| ~~P-11~~ | ~~Map Spread~~ | — | **DEFERRED (ADR-005)** | No map ships in v1; the engine has no spatial axis |
| P-12 | Final Chronicle | The completed book's last spread | MUST | The world ends; the chronicle becomes an artifact |
| P-13 | Chronicle Reading | Free browsing of the finished book | MUST | Read any era/life/event of the finished world |
| P-14 | Trace | A ribbon down the page | MUST | Follow one event backward to the life that seeded it |
| P-15 | Closing | The book closes, shelved | MUST | Afterglow + replay prompt ("a different world…") |
| P-16 | Threads Spread | A board-like spread of ribbons | SHOULD | Multi-thread investigation; "consequences you never saw" |
| S-01 | Ribbon Menu | A bookmark ribbon pulled down | MUST | Settings, help (glyph key), close book (save-safe), quit |
| S-02 | Recognition | An in-place page state | MUST | Print → Hand reveal: "that was me" (see §5) |
| S-03 | Plant Cue | A margin event on P-07 | MUST | "This will echo": a mark is drawn beside the act |

Notes:

- S-02 and S-03 are **states of existing pages**, not destinations; they never
  navigate.
- There is no separate "Event Result" page beyond P-07: results are written into
  the entry, because in this presentation *everything that happens is writing*.
- There is no game-over page of any kind. Death is P-08 and always turns forward.

---

## 3. Navigation Rules

### 3.1 The spine rule

**While the soul is alive, the book only turns forward.** Pages already written may
be *flipped back to* and read (read-only), but the current page is always the
rightmost; returning is one input (`I-02`) away. No choice can be unmade after
sealing. This is the physical form of "few inputs, heavy inputs."

### 3.2 Transition table

| From | Trigger | To | Rule |
|---|---|---|---|
| P-01 | choose the unfinished book | P-05 (wherever the ink is wet) or P-02 if new | Resume returns to the exact page state left |
| P-01 | choose the empty slot | P-02 | Starts a new world |
| P-01 | choose a finished book | P-13 | Finished books open in reading mode only |
| P-02 | auto (3–5 s) or any input | P-03 | Skippable ritual |
| P-03 | turn ×N or "skip to your first life" tab | P-04 | Front matter is skimmable theater, never required reading (max 3 spreads) |
| P-04 | turn | P-05 | — |
| P-05 | the world provides a fateful moment | P-06 | The page turn to P-06 is automatic and marked (see §7 motion) |
| ~~P-05 / P-06~~ | ~~map tab~~ | ~~P-11~~ | **Removed — ADR-005** |
| P-06 | seal a choice (I-04) | P-07 | Sealing is the only way off P-06 forward; flipping back remains allowed |
| P-06 | hold a marked line (I-05) | S-02 on P-06 | In-place; no navigation |
| P-07 | turn | P-05 (more of this life) or P-08 (life ends) | The world provides which |
| P-08 | turn | P-09 | — |
| P-09 | auto-advance (≈6–10 s) or input to skip | P-10 | Not interactive; skippable after first world |
| P-10 | turn | P-04 (next life) or P-12 (span ended) | The world provides which |
| ~~P-10~~ | ~~touch a digest line's map mark~~ | ~~P-11~~ | **Removed — ADR-005.** The digest line itself carries the inspect affordance |
| P-12 | "read the chronicle" | P-13 | — |
| P-12 / P-13 | "follow this thread" on a traceable event (I-06) | P-14 | Entry points are marked events only |
| P-14 | trace steps back / ribbon breadcrumb forward | P-14 (chain) | Ends at a life-page excerpt; "return" goes back to P-12/P-13 |
| P-13 | threads tab | P-16 (SHOULD) | If cut, tab does not exist |
| P-12 / P-13 / P-14 / P-16 | "close the book" | P-15 | — |
| P-15 | auto + input | P-01 | The shelf now shows this book spine + a new empty slot |
| any (except P-02, P-09) | Esc / ribbon | S-01 | Overlay; resume returns exactly |

### 3.3 Flip-back rule (read-only past)

- From P-05/P-06/P-07: flipping back (`I-02`) pages through everything already
  written *in this book*, including previous lives, front matter, and past rebirth
  spreads. Marks and any *already-revealed* Hands remain visible; **unrevealed
  attribution stays unrevealed** (flip-back never spoils, see D-04).
- A persistent "return to the wet ink" tab (**「今の頁へ」**) is always visible
  while flipped back. It restores the exact unresolved state left: page,
  selected-not-sealed option, focus, and scroll position.
- **Navigation and commitment are separate state (baseline UX-R8).** Past options
  are readable but **inert** — rereading an old juncture cannot re-select or
  re-seal it. Reading never earns a reveal (D-04). This read-only past is
  available during play, not only after the world ends.

---

## 4. Information Architecture

For each page: **Show** (printed for free) / **Hide** (never shown here) /
**Inferable** (deliberately left for the player to work out).

### P-01 Shelf
- **Show:** the current book's spine (world name, "in progress", life ordinal), up
  to N finished spines (world name, span, one-word epithet the finished world
  earned, e.g. *"A Chronicle of Fire"*), one empty slot.
- **Hide:** any statistics, completion percentages, achievement chrome.
- **Inferable:** that each spine is a *different* world with a different fingerprint
  (epithets differ).

### P-03 Front Matter
- **Show:** 2–3 spreads of deep past, three sentences per era, one small plate;
  era headers with year ranges.
- **Hide:** anything about the player's future role beyond one line of promise
  (see §8 copy); mechanics, terms, tutorials.
- **Inferable:** the world's dominant temperament (warlike, pious…) from tone.

### P-04 Life Opening
- **Show:** ordinal ("The Third Life"), year, place (name only), station/situation
  in ≤3 printed sentences; the Hand signs the heading (the visible signal that
  *this* entry is yours to write).
- **Show (2nd+ life only):** nothing of the digest is repeated here — P-10 already
  did that; P-04 stays clean.
- **Hide:** stats of any kind; the number of junctures this life will contain; the
  world's remaining span.
- **Inferable:** how much time has passed (year vs. the previous entry).

### P-05 Life Page
- **Show:** this life's entry so far: short printed passages (world events near
  you) interleaved with Hand-written passages (your sealed acts). Margin: year
  ticks; marks (§5) where earned.
- **Hide:** upcoming content; anything about other regions unless the world wrote
  it into this entry.
- **Inferable:** which past passages were *yours* across lives — by hand vs.
  print — without any label saying so.

### P-06 Juncture
- **Show:** the situation (≤120 words of print, one focal paragraph); 2–5 options,
  each ≤2 lines, written as *acts* ("Descend into the sealed vault"), never as
  outcomes ("Gain a relic"); marks in the margin beside any option descended from
  a past life (§5); a "someone here remembers you" tag where applicable (SHOULD).
- **Hide:** any numeric weight, score, or predicted consequence; which option is
  "the legacy option" **by label** (the mark hints, the label never says).
- **Inferable:** that a marked option is connected to *some* forgotten past act —
  and, before sealing, the player may hold-to-remember (I-05) to find out whose.
- **State:** options are select-then-seal (two-step, §6); flipping back to reread
  the entry is allowed before sealing.

### P-07 Outcome Passage
- **Show:** the sealed act rewritten into the entry in the Hand; the world's
  immediate response in print (≤80 words). If the act planted something durable:
  **S-03 plant cue** — a mark is drawn in the margin *as the player watches*, with
  exactly one line of print: *"This will echo."* No reward language, no numbers.
- **Hide:** what the echo will become; when; where.
- **Inferable:** that the mark glyph is a promise addressed to a future self.

### P-08 Death Page
- **Show:** the entry's final sentence (how the life ended, ≤2 sentences, dry);
  the Hand stops mid-line where death was sudden; the ink visibly dries (motion,
  §7); a closing rule line and the life's ordinal repeated small.
- **Hide:** any evaluation of the life (no score, grade, or summary list); any
  "you lost/gained" framing.
- **Inferable:** nothing is asked of the player here — the page is a held breath.

### P-09 Passage of Years
- **Show:** the margins flicker with passing years; fragments of print half-legible
  as pages auto-turn (2–4 teasing fragments maximum, chosen from what the world
  wrote during the skip — *without attribution*).
- **Hide:** everything legible. The fragments must not be readable enough to
  constitute the reveal; that belongs to P-10.
- **Inferable:** roughly how long the skip was (density of year ticks).

### P-10 Rebirth Spread — *the delivered reveal*
- **Show:** heading *"The world you return to."* First the changed present in
  wider world news; **then** the last-life feedback: **one** `(sealed act →
  consequence)` line given default emphasis, up to two further truthful lines
  available on request, **max 3 total**, each caused **by the immediately
  previous life**, each explicitly attributed: *"The vault you unsealed is now a
  shrine city."* Each line carries its mark glyph and quotes the act in the exact
  wording the player sealed it under (baseline UX-R6/C-2). This is delivered
  feedback that teaches persistence — **not** the earned-recognition climax
  (baseline UX-R7).
- ~~**Show (right page):** the Map plate~~ — **deferred, ADR-005.** The rebirth
  spread is the digest alone; there is no right page in v1.
- **Hide:** changes caused by lives *older* than the previous one (those must be
  discovered, D-03); full change logs; anything numeric; any founder identity
  older than the previous life.
- **Inferable:** that older, unmentioned marks may also be out there.
- **Quiet/terminal cases:** a life with no juncture, or a skip with an empty echo
  list, still gets its own dated entry and temporal place — never a fabricated
  decision or an enlarged non-event. The final aftermath has no rebirth to turn
  to and so P-10 is never reached empty.

### ~~P-11 Map Spread~~ — deferred past v1 (ADR-005)

The engine emits no spatial axis (`location_id` is `None` on every causal node),
so a v1 map would be invented geography. The Map spread returns to scope only if
W-1 adds a real spatial axis to worldgen. Nothing in v1 renders a map, a place
coordinate, or a geographic mark.

### P-12 Final Chronicle
- **Show:** the closing spread: the world's name and span; a ≤6-line closing
  passage in print; **exactly one highlighted line** — a still-shaping legacy of
  the player's, shown *with* its mark and Hand underlay already revealed (the pull
  into tracing, D-06); the invitations: *"Read the chronicle"* / *"Follow this
  thread"* / *"Close the book."*
- **Hide:** totals, rankings, completion metrics.
- **Inferable:** that more threads than the highlighted one exist (other marks are
  visible in the closing passage's margins, unhighlighted).

### P-13 Chronicle Reading
- **Show:** the finished book, freely pageable: era headers, events in print,
  lives as entries in the Hand; every mark earned during play remains; traceable
  events carry a small thread-end glyph (I-06 affordance).
- **Hide:** attributions not yet revealed — reading mode obeys the same discovery
  rules as play (D-04); reading is not a spoiler dump.
- **Inferable:** candidate connections — the reader can form hypotheses ("this war
  smells like my third life") before tracing.

### P-14 Trace
- **Show:** the chosen event as a card at top; each backward step revealed **one
  player input at a time**: consequence → precursor → … → origin, rendered as a
  ribbon down the page; the chain's final card is a **life-page excerpt**: the
  life ordinal, the year, and the sealed act in the Hand, **quoted in the exact
  wording the player sealed it under** (baseline UX-R6/C-2). If the origin life
  died before the traced event occurred, the chain's last-but-one card is
  stamped: *"You were not alive to see this."*
- **Every drawn link is a real causal edge (baseline UX-R6/C-3).** The chain is
  an ordered walk of edges that exist in the graph. An ancestor *count* is never
  drawn as a path; where repeated events are grouped into one readable passage,
  the grouping is expandable to the real intermediate evidence and an ellipsis is
  never drawn as a direct edge.
- **Multiple contributors are never shown as one.** The earliest player seed in
  an event's ancestry is **one contributing origin**, not proof that one life
  alone caused it; where other causes contributed, the card says so.
- **An autonomous origin is traced honestly but labelled as such.** A life's
  self-taken action is narrated as history, never as "the choice you made"
  (baseline UX-R6/C-6), and it does not satisfy Success Criterion 2.
- **Hide:** the chain's length and destination in advance; sibling branches (v1
  traces a single thread; branching is P-16/SHOULD).
- **Inferable:** at every step, the player is invited to guess the next link
  before turning it (the step affordance reads *"what came before?"*).

### P-15 Closing
- **Show:** the book closing (motion); the spine sliding into the shelf beside a
  new empty slot; one line: *"A different world could hold a different you."*
- **Hide:** any "score" of the finished world beyond its earned epithet.
- **Inferable:** the replay intent (§3.5 of the direction doc): the empty slot is
  the question.

### P-16 Threads Spread (SHOULD)
- **Show:** the finished world's traceable events as thread-ends on a spread;
  pulled threads persist as ribbons; a digest panel *"consequences you never
  saw"* listing (attributed, after first trace) the posthumous echoes of each
  life.
- **Hide:** untraced connections (threads must be pulled to be drawn).
- **Inferable:** the shape of one's whole fingerprint emerging as ribbons
  accumulate.

---

## 5. Discovery Rules (Hint / Withhold / Confirm)

The North Star operationalized. Three tiers, strictly ordered; every piece of
attribution in the game is in exactly one tier at any moment.

### The mark system (the Hint vocabulary)

Two glyphs, one per trace kind. Hand-drawn (not typeset), always marginal.
(The ◦ memory mark is removed for v1 — ADR-001 §3, ratified in the 2026-09-08
baseline; a memory mark may return post-v1 if the engine grows persisted lineage
memory.)

| Mark | Name | Attached to | Meaning (never printed; learned) |
|---|---|---|---|
| ⟜ | Echo mark | content descended from a past act that planted a consequence | "something done echoes here" |
| ❧ | Legacy mark | content descended from a named, lasting institution/heritage | "something built still stands here" |

Rules:

- **D-01 (Withhold by default).** No content is ever attributed to a past life in
  print. The words "you/your past life" appear *only* in Tier-Confirm surfaces
  (P-10 digest lines, S-02 reveals, P-14 origin cards, P-12's single highlight).
  Everywhere else, player-descended content reads as plain history.
- **D-02 (Hint = mark, nothing more).** A mark appears beside content only if it
  is descended from one of *this soul's previous lives* in *this world*, and
  only at **decision and trace surfaces** — P-06 options, P-10 digest lines,
  and traceable events on P-12/P-13. (The P-11 map is deferred — ADR-005.)
  Running prose (P-03, P-05) is
  never marked, even when descended — passing mentions are the withhold tier's
  raw material (amendment Δ1, see `v1_tutorial_world_proof.md` §2.4). Marks are
  never attached to current-life content (no self-marking), never explained in
  print in the book's body (the glyph key lives in S-01 help, one line each, and
  §8 teaches the first one diegetically), and never accompanied by names or
  ordinals.
- **D-03 (Recency window for delivered reveals).** The P-10 rebirth digest may
  explicitly attribute **only the immediately previous life**, max 3 lines. All
  deeper history — anything two or more lives old — can *only* reach Confirm via a
  player act (I-05 hold-to-remember or I-06/P-14 tracing). This is the line
  between "the game teaches the loop" and "the player lives the loop."
  *(Baseline UX-R3: this applies on **every** surface that can name or depict an
  origin — the C1 time surface caption, the entry, history, the trace, and any
  resumed state — not only the P-10 digest. Before a connection is confirmed, no
  older-life founder identity may surface through text, accessible label,
  geometry, colour, camera move, or focus behaviour.)*
- **D-04 (No passive confirms; no retroactive spoilers).** Reading (P-05
  flip-back, P-13) never auto-reveals. Reveals are permanent once earned (a
  remembered Hand stays visible everywhere that content appears), but flipping
  back before earning shows only marks.
  *(Baseline UX-R3: "reading" here includes the C1 time surface and every
  history/archive view. Checks run against the **actual reached prefix**, never a
  full replay that already knows the outcome.)*
- **D-05 (Confirm is staged, and the player goes first).** Every Confirm surface
  is ordered *withhold → hint → confirm*: the content is first shown as plain
  print (beat), its mark is present (hint), and the reveal fires only on the
  player's input (I-05 hold, or a P-14 step-turn). The reveal itself always has
  the same grammar: the print stays, the Hand blooms *underneath* it, and one
  line names the origin: *"— your third life, who chose to ⟨act⟩."* The player's
  hypothesis precedes the game's answer by design.
- **D-06 (Exactly one seeded confirm at world's end).** P-12 pre-reveals exactly
  one highlighted still-shaping legacy. Purpose: guarantee the pull into P-14 and
  Success Criterion 2 even for players who never held a mark. It is the only
  unearned confirm outside the D-03 window, and there is never more than one.
- **D-07 (Recognition frequency).** S-02 (the in-life "that was me") is
  **guaranteed once in the first world** (§8 stages it) and thereafter uncapped
  but *naturally rare*; the game never manufactures extra marked junctures to
  raise the rate. Guaranteed once, rare thereafter (direction doc, Principle 7).
- **D-08 (Marks never lie).** A mark is present ⇔ the connection is real. No
  decoys, no red herrings. Trust in the mark is the entire currency of discovery
  (Principle 1).

### Timing summary

| Moment | Tier | Surface |
|---|---|---|
| Act plants something durable | *Promise* (not attribution) | S-03 plant cue: mark drawn + "This will echo." |
| Time-skip completes | **Confirm (delivered, last life only)** | P-10 digest, one emphasized line, ≤3 total (ADR-005: no map marks) |
| Marked content encountered in a later life | **Hint** | Margin mark only (D-02) |
| Player holds a marked line | **Confirm (earned)** | S-02 reveal grammar |
| Player traces an event (post-world) | **Confirm (earned, stepwise)** | P-14 ribbon, origin card last |
| World ends | **Confirm (seeded, exactly one)** | P-12 highlighted line |

---

## 6. Interaction Design

Full input verb set. v1 posture: pointer-first with complete keyboard parity
(direction doc Q3 pending; nothing below requires more than pointer + 6 keys).

| ID | Verb | Pointer | Keyboard | Where | Notes |
|---|---|---|---|---|---|
| I-01 | Turn page (forward) | click right page edge | Space / → / Enter | everywhere the spine allows | The default "continue"; also skips P-02, shortens P-09 |
| I-02 | Flip back / return | click left page edge; "wet ink" tab | ← ; Tab returns | P-05/06/07, P-13 | Read-only (§3.3). Navigation only — never commits and never re-executes a past choice |
| I-03 | Select option | click option | 1–5 / ↑↓ | P-06 | Selection previews the act *written faintly* in the Hand. Commits nothing; does **not** open inspection |
| I-04 | **Seal (commit)** | click the seal on the selected option | Enter (held selection) | P-06 | The commit. Two-step always; sealing animates ink setting; irreversible. A single key event never both turns a page and seals |
| I-05a | **Inspect** | click the "調べる" affordance on a marked line | Enter/Space on the focused affordance | P-05/P-06/P-13, and any surface showing a historical consequence | The discovery action, taught explicitly. Opens evidence; never selects, never commits. Keyboard-and-pointer equal |
| I-05b | Hold to inspect (optional) | press-and-hold a marked line (~800 ms) | hold R on focused line | same as I-05a | A convenience gesture for I-05a only. Releasing early cancels with no effect; a hold can never consume a select/seal click; no timed input is ever required |
| I-06 | Follow the thread | click a thread-end glyph | T on focused event | P-12/P-13 (→P-14) | Entry to tracing |
| I-07 | Step the trace | click "what came before?" | Space / → | P-14 | One link per input (D-05) |
| ~~I-08~~ | ~~Open map~~ | — | — | — | **Deferred past v1 — ADR-005.** No map surface ships in v1 |
| I-09 | Ribbon menu | click ribbon | Esc | all except P-02/P-09 | Settings, glyph key, "close the book" (save-safe exit), quit |
| I-10 | Choose from shelf | click spine/slot | ↑↓ + Enter | P-01 | — |

Interaction principles:

- **No free text. No drag. No timers.** Nothing in v1 is dexterity- or
  speed-gated; a juncture waits forever. (Few inputs, heavy inputs.)
- **The discovery verb is distinct from the continue verb**, but it is not a
  secret. Turning is a tap; inspecting is a **visible, labelled, keyboard-
  reachable action** ("調べる"), with the ~800 ms hold retained only as an
  optional convenience gesture (baseline UX-R2). A hidden gesture is not a
  historical mystery; teaching the operation does not reveal the answer.
- **Accessibility is a baseline requirement, from the first world (baseline
  UX-R9) — not an I-7 polish pass.** Reduced motion with a readable *static*
  equivalent for every transition (including P-09/the time surface); text
  scaling that reflows or scrolls the reading region rather than shrinking it
  back into a fixed paper rectangle; full keyboard parity for every verb; a skip
  that settles the transition before a separate continuation input; no
  confirmation that disappears on a timer. Save/load failures state the problem
  and the next action plainly.
  The player should feel themselves *choosing to know*.
- **Sealing is ceremonial.** Select-then-seal exists so that no heavy choice is
  one accidental click, and so commitment has a physical beat (ink sets, page
  readies to turn).
- **Everything is reachable in ≤2 inputs from the current page:** continue (1),
  menu (1), back (1), inspect (visible affordance; optional hold). No map key (ADR-005).

---

## 7. Visual Language

Roles only (the visual style guide — direction doc deliverable 6 — will bind
exact faces, sizes, and palette; this section defines *what each element is for*).

- **Typography — two voices, one contrast.**
  - *Print* (serif, upright, even color): the historian. Everything the world
    says. Authoritative, dry, slightly dense.
  - *The Hand* (script/italic, irregular baseline, warmer ink): the soul.
    Everything the player did — current entry, past sealed acts, S-02 reveals.
    Per-life the Hand varies subtly (slant/weight), so a flipping reader can
    sense "different life" before reading a word. **The print/Hand contrast is
    the single most load-bearing visual device in the game** — it *is* D-01/D-05
    made visible — and no other element may reuse script type.
- **Whitespace.** One focal object per page (Principle 11); generous margins are
  not decoration but *the stage for time and marks* — year ticks, marks, and the
  P-09 flicker all live in margins. Body text never exceeds ~55 characters per
  line; a page that needs more text becomes two pages.
- **Plates (illustrations).** Tipped-in, framed, captioned in print. Roles: front
  matter era plates (world temperament), ~~the Map (P-11)~~ (deferred, ADR-005), portrait plates
  (SHOULD). Plates never contain UI. Scarcity is intentional: ≤1 plate per
  spread.
- **Icons.** Exactly the two marks ⟜/❧ (§5) plus the affordances (ribbon,
  thread-end glyph). Marks are hand-drawn strokes, not chrome; affordances are
  physical book objects (a tab, a ribbon, a loose thread). **No other icons exist
  in v1.** Any proposed fourth glyph must displace one of these six.
- ~~**The Map.**~~ **Deferred past v1 — ADR-005.** The engine emits no spatial
  axis, so v1 renders no map, no place coordinate, and no geographic mark. The
  rebirth jolt is carried by the P-10 digest and the C1 time surface instead.
- **The Chronicle (text of history).** Era headers (print, small caps, year
  range), event passages (print), life entries (the Hand, signed with ordinals).
  The highlighted line on P-12 uses the one emphasis treatment the book allows
  (rubrication — see the 朱 rule below). One accent, one meaning, everywhere.
- **The 朱 rule (baseline UX-R5, amends D-4).** 朱 — the single accent ink —
  means **a confirmed connection to a past life**, and nothing else. It is used
  consistently in prose, marks, and diagrams, and it persists once earned.
  Ordinary selection and the S-03 promise mark stay in ink, never 朱. The
  ⟜/❧ glyphs remain trace-*kind* labels; they never encode the
  unconfirmed→confirmed transition — state is carried by an added line or a
  revealed annotation, and screen-reader text and focus styling carry the same
  meaning as the visible glyph. "Still shaping the world" survives as a
  **concept** (D-06 needs it) but is expressed as a small explicit text
  annotation, only where a current/reached projection supports it; a mark merely
  gaining a name (`hardened`) does not confer it.
- **Motion (ink is the animation language).** Page turns (short, physical); ink
  drying on P-08 (the one slow moment, ~3 s, unskippable in the first world);
  margin year-flicker on P-09; the Hand *blooming* under print on S-02 reveals
  (~1.5 s, cancels nothing, savored); the seal setting on I-04. No motion exists
  that is not ink, paper, or thread. No particles, no glows, no screen shake.

---

## 8. Tutorial Specification (the Guided First World)

Purpose: deliver Success Criteria 1–3 — above all **SC-1: within the first
session, ≤30 minutes, the player recognizes unaided: "that was my past life's
doing."** The tutorial is a *staged first world*, not a tutorial mode: the world
provides a curated starting scenario whose content guarantees the beats below.
The book never breaks diegesis to instruct; all teaching is placement, staging,
and at most three one-line historian's asides (marked ✎ below).

Timeline (targets, not hard gates — the player controls all pacing):

| Time | Pages | Staged content & teaching beat |
|---|---|---|
| 0:00–1:00 | P-01→P-02 | Shelf holds one empty slot only. Cover ritual establishes "object, not app." |
| 1:00–3:00 | P-03 | Two spreads of front matter. Last line of print (✎ aside #1): *"Of the soul that returns to this world again and again, the record says only: it writes in a different hand."* — role seated, power unknown (Emotional Arc beat 1). First choice is ≤3 min away. |
| 3:00–10:00 | P-04→P-07 (Life 1: 2 junctures) | **Juncture 1** teaches select/seal: 3 options, all safe, no marks anywhere (nothing to discover yet — the world is clean). **Juncture 2 is the guaranteed plant**: every option on the page plants something durable (the guarantee is *option-set curation*, not forced choice), so S-03 fires regardless of what is sealed: the mark is drawn, *"This will echo."* (✎ aside #2, printed small under the cue): *"Marks in the margin are the chronicle's memory."* |
| 10:00–11:00 | P-08 | First death. Ink-dry moment plays full length (unskippable, first world only). |
| 11:00–12:00 | P-09 | First skip: ~8 s, margins flicker through decades. Unskippable in the first world (time must be *felt* once — Principle 5); skippable ever after. |
| 12:00–13:00 | P-10 | **The delivered jolt (SC-3 seeded here):** digest line 1 attributes the Juncture-2 plant: *"The ⟨act⟩ of your last life has become ⟨changed thing⟩."* Death has just paid out; loss reframed as sowing. (ADR-005: no map.) |
| 13:00–25:00 | P-04→P-07 (Life 2: 2–3 junctures) | **The earned recognition (SC-1).** Staging: (a) mid-life, a P-05 passage mentions — in plain print, unmarked — a name/place descended from Life 1's *other* durable consequence (the one the digest did **not** cover; the curated scenario guarantees a second, undelivered plant from Juncture 2's option set). The player reads past it: withhold. (b) At the next juncture, one option carries that same name **with its mark** — the first mark the player has ever seen *on a choice*. Hint. (c) The first time the pointer rests on a marked option in the first world, the mark alone gives a single slow pulse (once, never again in any world). (d) If the player holds: **S-02 fires — the earned "that was me."** The reveal grammar (§5 D-05) names Life 1 and the sealed act. This is the game's peak moment and nothing interrupts it. (e) **Fallback for SC-1:** if the player seals a marked option *without* ever holding (any marked option, this life or later), the outcome passage on P-07 stages a delayed reveal: the act is written, then the Hand blooms beside it — *"…as your first life once intended."* Recognition is guaranteed by the end of Life 2 by one of the two paths. |
| 25:00–30:00 | P-08→P-12 | The staged world's span is short (3 lives max; Life 3 exists only if pacing is fast, providing free play with the now-learned verbs). P-12: one highlighted still-shaping line (D-06). The invitation *"Follow this thread"* pulses once (the second and last UI pulse in the game). One trace (P-14, 3–4 links) reaches a Life-1 or Life-2 origin card — **SC-2 rehearsed**. P-15 closes: *"A different world could hold a different you."* The shelf now shows one spine and one empty slot. |

Guarantee mechanisms (spec-level, restated):

- **G-1:** Juncture 2 of Life 1 is plant-guaranteed *by option-set curation* —
  choice stays real, echo is certain.
- **G-2:** The curated scenario yields ≥2 durable consequences from Life 1; the
  P-10 digest delivers exactly one, reserving the other for the earned
  recognition (D-03 kept intact even in the tutorial).
- **G-3:** Recognition has two paths (hold → S-02; seal-without-hold → P-07
  delayed reveal) so SC-1 cannot be missed by input style.
- **G-4:** The two "pulse" affordances (first mark on an option; first thread-end)
  fire once per *player*, ever — they are training wheels that never return.
- **G-5:** The first world's span ends by Life 3 regardless of play, so P-12 (and
  SC-2's trace) occur inside the session.
- Validation that a world state satisfying G-1/G-2 exists is a content search
  (direction doc, risk R-B) and precedes implementation planning.

---

## 9. Wireframe Sketches

Monospace sketches; `≈ serif print`, `~italic hand~`, `[ ]` interactive,
glyphs as in §5. All pages share the book frame (spread, gutter, margins).

### P-01 Shelf
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│        A  quiet  shelf                                       │
│   ┌────┐ ┌────┐ ┌╌╌╌╌┐                                      │
│   │CHRO│ │CHRO│ ┆    ┆                                      │
│   │NICL│ │NICL│ ┆ +  ┆   [The Chronicle of ______ ]         │
│   │ of │ │ of │ ┆    ┆      in progress — Third Life        │
│   │FIRE│ │SALT│ ┆    ┆      ~a ribbon marks the wet ink~    │
│   └────┘ └────┘ └╌╌╌╌┘                                      │
│   finished  finished  [begin a                               │
│                        new book]                             │
└──────────────────────────────────────────────────────────────┘
```

### P-06 Juncture (with one marked option; before selection)
```
┌───────────────────────────────┬──────────────────────────────┐
│  · year 412 ·                 │                              │
│                               │   ≈ The drought has broken   │
│  ~entry so far, in the        │   ≈ the river towns. At the  │
│   hand, readable by           │   ≈ assembly, all eyes turn  │
│   flipping back...~           │   ≈ to you.                  │
│                               │                              │
│                               │   [ Open the old granary  ]  │
│                               │ ❧ [ Invoke the Vault Pact ]  │
│                               │   [ Lead the towns south  ]  │
│                               │                              │
│           ▐M                  │        — seal your choice —  │
└───────────────────────────────┴──────────────────────────────┘
   ❧ = legacy mark in margin; hold it to remember (I-05)
```

### S-02 Recognition (in place, on P-06, after hold)
```
┌───────────────────────────────┬──────────────────────────────┐
│                               │   ≈ ...all eyes turn to you. │
│                               │                              │
│                               │ ❧ [ Invoke the Vault Pact ]  │
│                               │    ~beneath the print, ink   │
│                               │     blooms in an older hand~ │
│                               │    ~— your first life, who   │
│                               │     chose to unseal the      │
│                               │     vault beneath the hill.~ │
│                               │                              │
│                               │        — seal your choice —  │
└───────────────────────────────┴──────────────────────────────┘
```

### P-07 Outcome Passage (with S-03 plant cue)
```
┌───────────────────────────────┬──────────────────────────────┐
│  ...                          │  ~You descend into the       │
│                               │   sealed vault, and bring    │
│                               │   the old engine to light.~  │
│                               │                              │
│                               │  ≈ The valley talks of       │
│                               │  ≈ little else that year.    │
│                          ⟜    │                              │
│                     (drawn    │  ≈ This will echo.           │
│                      now)     │                              │
│                               │                    (turn) ▷  │
└───────────────────────────────┴──────────────────────────────┘
```

### P-08 Death Page → P-09 Passage of Years
```
┌───────────────────────────────┬──────────────────────────────┐
│  ~The fever took him in       │   412 ┆ 419 ┆ 431 ┆ 446 ...  │
│   autumn. The last line       │   ≈≈≈ ≈≈ ≈≈≈≈ (half-legible  │
│   stops mid—                  │    fragments, auto-turning)  │
│                               │                              │
│        (the ink dries)        │   ≈≈ ≈≈≈ ≈≈                  │
│    ————————————————————       │        · the book writes     │
│       The First Life          │          without you ·       │
└───────────────────────────────┴──────────────────────────────┘
```

### P-10 Rebirth Spread
```
┌───────────────────────────────┬──────────────────────────────┐
│  ≈ The world you return to                                   │
│                                                              │
│  ≈ In the north, a war nobody remembers starting.            │
│    (the changed present, unattributed, comes first)          │
│                                                              │
│ ⟜ ≈ "Open the hill's undercroft" — the vault you unsealed    │
│     is now a shrine city.                    [調べる]        │
│     (the one emphasized line; the act quoted as sealed)      │
│                                                              │
│   ▸ two more truthful lines available on request (≤3 total)  │
│                                                       (turn)▷│
└──────────────────────────────────────────────────────────────┘
   digest ≤3 lines, last-life only (D-03); one emphasized by default
   (UX-R7); no map (ADR-005); no founder older than the last life
```

### P-12 Final Chronicle
```
┌───────────────────────────────┬──────────────────────────────┐
│  ≈ Here ends the Chronicle    │  ❧ ≈ And the Vault Pact      │
│  ≈ of the Salt Kingdoms,      │  ~   holds to this day —     │
│  ≈ four hundred years         │      your first life's       │
│  ≈ from flood to accord.      │      doing.~   « rubricated »│
│                               │                              │
│                               │   [ Read the chronicle ]     │
│                               │   [ Follow this thread ]     │
│                               │   [ Close the book ]         │
└───────────────────────────────┴──────────────────────────────┘
```

### P-14 Trace (mid-chain)
```
┌──────────────────────────────────────────────────────────────┐
│   ≈ THE ACCORD OF THE THREE CITIES · year 803                │
│        │ ribbon                                              │
│   ≈ the shrine city's council, year 641                      │
│        │                                                     │
│   ≈ pilgrimages begin at the unsealed vault, year 466        │
│        │        « You were not alive to see this. »          │
│        ▼                                                     │
│   [ what came before? ]                                      │
│                                                              │
│   (chain ends at:)  ~year 412 — your first life, who chose   │
│                      to unseal the vault beneath the hill~   │
│                                          [ return ]          │
└──────────────────────────────────────────────────────────────┘
```

### S-01 Ribbon Menu (overlay)
```
┌──────────────────────────────────────────────────────────────┐
│      ▼ ribbon                                                │
│   ┌─────────────────────────┐   (page dimmed, still visible) │
│   │  Close the book (save)  │                                │
│   │  The glyph key    ⟜ ❧   │                                │
│   │  Settings               │                                │
│   │  Leave the library      │                                │
│   └─────────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Open Questions

1. **Q-UX-1 — World length outside the tutorial.** The staged first world is ≤3
   lives / ≤30 min. Target lives-per-world and session length for a *standard*
   world (affects P-01 resume framing and P-13 chronicle size) needs a decision;
   proposal: 5–8 lives, 60–90 min, finishable in ≤2 sessions (Principle 9).
2. **Q-UX-2 — Flip-back depth.** §3.3 allows flipping through the *entire*
   written book mid-life. Full depth, or current-life-only with past lives
   reachable via a contents tab? (Full depth is more book-honest; contents tab is
   more legible at life 6.)
3. **Q-UX-3 — Hold-to-remember on touch/controller.** The 800 ms hold maps
   cleanly to pointer and touch; the controller mapping (if Q3 of the direction
   doc ever admits controllers) has no equally *deliberate* verb yet.
4. **Q-UX-4 — Digest overflow.** When the previous life planted more than 3
   changes, which 3 does P-10 deliver? Proposal: the world provides magnitude;
   digest takes the top 3; the rest stay as unexplained map marks (feeding later
   discovery). *Partially resolved for the tutorial* (amendment Δ3,
   `v1_tutorial_world_proof.md` §2.4): the digest must never include a trace
   reserved for an upcoming marked option — delivered lines and reserved
   recognitions are disjoint by construction. The standard-world rule remains
   open.
5. **Q-UX-5 — Per-life Hand variation legibility.** Subtle per-life script
   variation (§7) must stay readable; needs an early legibility test with real
   faces before it becomes load-bearing (fallback: ordinal signatures only).
6. **Q-UX-6 — The epithet.** P-01/P-15 give each finished world a one-word
   epithet ("of Fire"). Source and vocabulary of epithets (from the world's
   dominant theme) needs a small authored table; who writes it and how large?
7. **Q-UX-7 — Second-world staging.** After the guided first world, are worlds
   fully unstaged, or does world 2 keep a light guarantee (e.g., G-1 only)?
   Proposal: fully unstaged from world 2 (D-07 rarity begins immediately);
   playtest may overturn.
8. **Q-UX-8 — Reading-mode marks for unfinished business.** In P-13, should
   *untraceable* events (no player connection) be visually distinguishable from
   *not-yet-traced* ones, or is the thread-end glyph on traceable events (I-06)
   sufficient? Current spec: glyph on traceable only; risk is players holding
   unmarked lines and reading absence as bug.
9. **Q-UX-9 — Language (direction doc Q2, still open).** Every copy rule in this
   spec (line lengths, voice contrast) must be re-validated for Japanese
   typography if JP ships; the print/Hand contrast has a natural JP analogue
   (明朝 vs. 行書) but line-length and hold-target rules change.
10. **Q-UX-10 — Accessibility floor.** Minimum v1 set proposed: text scaling (2
    steps), reduced-motion (ink animations become cross-fades; P-09 becomes a
    static year-span page), colorblind-safe rubrication (accent + underline).
    Needs sign-off as Must vs. Should.

---

*Conformance note.* Every rule above traces to the adopted direction:
withhold/hint/confirm (D-01…D-08) operationalizes Principles 1, 2, and 7; the
spine rule and seal operationalize Principles 3 and 4; P-09/P-10 operationalize
Principle 5; the mark system and map operationalize Principles 8 and 10; page
budgets and the two-voice typography operationalize Principle 11. The tutorial
(§8) is the executable form of Success Criteria 1–3; the P-15 prompt and shelf
serve Criterion 4.
