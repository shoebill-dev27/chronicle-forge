# Chronicle Forge v1 — Design Direction Review (Design Director)

Status: **Design / for review. No implementation.** Target release: **2026-08-16**.
Inputs reviewed: [`discovery_loop.md`](discovery_loop.md),
[`player_journey.md`](player_journey.md),
[`game_experience_roadmap.md`](game_experience_roadmap.md), and the
**Chronicle Forge v1 Design Definition** (2026-07-17, session document; superseded by §3
of this review). All are treated as *input*, not immutable truth.

North Star under which every judgment below is made:

> **"The player discovers, by themselves, that the history they are reading was
> written by their own forgotten past lives."**

---

## 1. Executive Summary

1. The v1 Design Definition is fundamentally sound. Its Core Experience, North Star,
   and Success Criteria are correct and are retained. Refinements are proposed in §3
   (mostly sharpening, one addition: a *diegesis* principle).
2. **The "low-poly 3D UI" assumption should be dropped for v1.** Measured against the
   North Star, 3D is the *weakest* of the studied presentations: its strengths
   (embodiment, spatial navigation, moment-to-moment presence) serve verbs this game
   deliberately rejects, while its costs and risks are the highest of any option — and
   it actively *misleads* the general-gamer audience about what the game is.
3. **Recommended direction: "The Living Chronicle"** — the game presents itself as an
   illuminated, living history book. Every screen is a page or spread of one book.
   The player writes entries while alive; death turns their ink into printed history;
   rebirth opens the book generations later; the ending closes the book into a
   shareable artifact. Two special spreads — an illustrated **Map spread** (the world,
   redrawn between lives) and a **Threads spread** (the investigation board) — carry
   the spatial and causal payoffs. This is the North Star made *literal*: the
   interface **is** "the diary written in your own forgotten hand."
4. v1 scope (§4) is defined so the complete discovery loop is *felt* end-to-end in
   the book presentation, and so the release survives cutting its two most expensive
   Should-haves without losing the Core Experience.
5. Eleven design deliverables (§9) must exist before implementation begins. The
   critical path is the **page inventory**, the **tutorial world script**, and the
   **recognition/rebirth beat specs** — everything else can trail them.

---

## 2. Review of the Current v1 Design Definition

### What is right (keep)

- **Core Experience as a single moment** ("I did this" — found unaided) is the
  correct compression. It matches what the engine already uniquely provides
  (attribution across a time-skip) and what no mainstream genre delivers.
- **North Star phrasing** is decision-ready: it has rejected features in this very
  review (3D, sandbox verbs) and admitted others (map spread). It works.
- **Success Criteria are experience-level and testable by observation** — each one is
  a playtest question, not a metric. This is exactly what a v1 gate should be.
- **"Death is punctuation" and "time distance is emotional distance"** are the two
  principles that most distinguish this game; both are preserved verbatim.
- **Out of Scope list** correctly protects the core (no action depth, no sandbox
  verbs, no endless worlds, no stat progression).

### What needs sharpening (changed in §3)

1. **The definition is silent on presentation.** That was correct for its layer, but
   it left "low-poly 3D" standing as an unexamined assumption. The definition needs
   one principle that constrains presentation *without* prescribing it — added as
   Principle 10, **"The interface is the artifact."**
2. **Success Criterion 1 needs a time bound.** "Within the first world" is right, but
   the first world must itself be bounded (the journey doc says <30 min). Made
   explicit: *within the first session, ≤30 minutes*.
3. **The Emotional Arc under-specifies the first three minutes.** The arc starts at
   "smallness," but smallness must be *staged*, not merely suffered — a new player
   who feels lost quits. Reworded: the opening feeling is *"small, but seated"* —
   you know your role (the returning soul) before you know your power.
4. **"Recognition stays rare" needs a floor as well as a ceiling.** Rarity is
   correct at steady state, but the *first* recognition must be guaranteed early
   (Success Criterion 1 depends on it). The principle now reads: *rare thereafter,
   guaranteed once.*
5. **Replay motivation criterion needs an observable proxy.** "Starts a second world
   to leave a different mark" is right; the observable proxy is that the player can
   *name* the different mark they intend to leave before starting. Added.

### What is missing (added in §3)

- A **readability principle** for a text-forward game ("One page, one focus") — the
  single biggest failure mode of the recommended direction is the wall of text, and
  the definition must guard against it at the principle level.
- An explicit statement that **the historian's voice is a character** — the game's
  narrator is the chronicle itself, and its tone (dry, factual, occasionally
  astonished) is a design asset that must be specified, not improvised.

---

## 3. Updated Design Definition (v1.1)

*Supersedes the 2026-07-17 session document. Changes from it are marked ◆.*

### 3.1 Core Fantasy

You are the one soul that keeps being reborn into a single world. Each short life
leaves marks; centuries harden those marks into history; and you return to read that
history and feel the shiver of recognizing it: **"the hand that wrote this was mine,
and I had forgotten."**

### 3.2 Core Experience

**The moment the player finds — unaided — their own past hand in the world's
history: "I did this."**

Everything else in the game is either preparation for this moment or its afterglow.

### 3.3 Emotional Arc

1. **Small, but seated** ◆ (opening): the world is vast and your life is short — but
   you know what you are (the returning soul) and when you matter (fateful moments).
   Uncertainty about *power*, never about *role*.
2. **The first jolt** (first rebirth): you die, return, and the world has changed —
   because of you. Powerlessness inverts.
3. **Déjà vu** (mid lives): a name you shouldn't know, known. "Wait — that was me."
   Awe mixed with homesickness.
4. **Authorship** (later lives): from reacting to planting. You go to your death on
   purpose, having chosen what you want to find later. Death turns from loss into
   sowing.
5. **Acceptance and quiet pride** (world's end): the finished chronicle reads as
   your diary. Pride, and a little grief that it is over.
6. **The itch** (after the ending): "a different world could hold a different me."

Target in one line: **powerlessness → causal surprise → intent → quiet pride**, as a
staged inversion.

### 3.4 North Star

**Does this decision strengthen the experience of discovering, by yourself and
across felt time, the marks your own past lives left on the world?**

If not — however attractive — cut it.

### 3.5 Success Criteria (v1 minimum, design-only)

1. A first-time player, **within their first session and ≤30 minutes** ◆, at least
   once recognizes unaided: *"that was my past life's doing."*
2. After a world ends, the player can explain in their own words, for at least one
   major historical event, **which life and which choice of theirs caused it**.
3. Death is never experienced as game over — the death→rebirth transition reads as
   *"the harvest of what I planted begins,"* not as loss.
4. The player starts a second world **to leave a different mark**, and can name that
   intended mark before starting ◆.

All four or the design has failed, regardless of what else shipped.

### 3.6 Out of Scope (v1)

Unchanged from v1.0 of the definition: combat/action depth · free-roam sandbox verbs
· synchronous multiplayer · endless worlds · additional simulation depth · stat/skill
progression · answer-pushing UI. (Presentation-level cuts are in §4 Won't Have.)

### 3.7 Design Principles

1. **Never fabricate history.** Dramatize the telling, never the events. Everything
   the player discovers really happened, really connected.
2. **Discovery is induced, not delivered.** Leave room for a hypothesis before
   showing the answer.
3. **Few inputs, heavy inputs.** Invest in showing one choice's blast radius, not in
   adding choices.
4. **Death is punctuation, not punishment.** Death is the device that hardens marks
   into history and opens the next discovery.
5. **Time distance is emotional distance.** Always place felt time between leaving a
   mark and finding it. The moment this becomes an instant reward, the game is
   ordinary.
6. **The world does not flatter the player.** You are a thread in history, not its
   protagonist. A world that orbits the player cannot surprise them.
7. **Recognition: guaranteed once, rare thereafter.** ◆ The first "that was me" is
   engineered to happen early; every later one is scarce and precious.
8. **The same world is always the same world.** Reproducibility is not an
   engineering guarantee but the ground of play: discoveries can be pointed at,
   handed over, verified.
9. **A world must be finishable as a reading.** Design for the afterglow of a
   completed chronicle, not for length.
10. **The interface is the artifact.** ◆ The player should never feel they are using
    a UI *about* the world's history — they should feel they are holding the
    history itself. Presentation choices are judged by how diegetic they are.
11. **One page, one focus.** ◆ Every screen has a single focal object — a choice, a
    reveal, a mark, a map. Text is staged, never dumped. The historian's voice is a
    character (dry, factual, occasionally astonished) and is specified, not
    improvised.

### 3.8 One Sentence

**Chronicle Forge is the one world your soul keeps returning to — and its history is
a diary written in your own forgotten hand.**

---

## 4. v1 Scope

Scope is stated in experience terms. It deliberately does not map to engine phases;
it maps to what the player must feel.

### Must Have

- **The complete discovery loop, felt end-to-end**, through four beats:
  1. *Plant cue* — a quiet "this will echo" note when a durable mark is made.
  2. *Time-skip reveal* — rebirth opens with "the world you return to": what changed
     because of your last self, one line per change.
  3. *Recognition* — the staged, attributed "that was me" moment (guaranteed once in
     the first world, rare thereafter).
  4. *The finished Chronicle* — the world ends into a readable, keepable artifact
     with the player's marks named in it.
- **The Living Chronicle presentation core** (§7): life pages, juncture pages, the
  death page, the rebirth spread, and the ending (the closed book).
- **The Map spread** — an illustrated world map that visibly changes between lives.
  Minimum bar: the player can *see* on the map at least one change their past life
  caused.
- **Trace-one-event investigation** — from any major event in the finished
  chronicle, the player can follow it back to the life (and choice) that seeded it.
  Minimum bar: one thread followed by hand, not a full board.
- **A guided first world** — a chosen seed and staged first session that delivers
  Success Criteria 1–3 in ≤30 minutes.
- **The historian's voice** — specified tone, vocabulary, and player-facing terms
  (mark / echo / legacy / "still shaping the world") used consistently everywhere.

### Should Have

*(Ship if the schedule holds; each is individually cuttable without breaking the
Core Experience.)*

- **The Threads spread** — the full investigation board: pick any event, walk its
  ancestry visually, see "consequences you never saw live" as a digest.
- **"Remembers you" moments** — people and dynasties that greet or fear your return,
  labeled as such.
- **Portrait plates & illustrations** — small illustrated plates for notable lives,
  places, and legacies inside the book.
- **World sharing** — hand a finished world to a friend as an invitation: "find what
  I left."
- **Sound direction** — page, ink, and time-skip sound; a sparse score.

### Won't Have (v1)

- **Any 3D client** (low-poly or otherwise). Rationale in §6–§7. 3D is not deferred
  as "the real UI later" — it is rejected as a v1 frame; post-v1 it could at most
  become an optional *setting* around the book (a desk, a library), never a
  replacement for it.
- **Synchronous multiplayer.** Asynchronous sharing of worlds covers the social
  promise.
- **The Atlas / collection meta-game.** The 50-hour layer needs many finished
  worlds; v1's job is to make one world unforgettable.
- **AI narration.** v1 speaks entirely in its own deterministic, authored voice. An
  optional AI voice can join post-v1; shipping the hook must not depend on it.
- **Endless / open-ended worlds, stat progression, action verbs** — reaffirmed from
  the definition's Out of Scope.

---

## 5. Player Experience Flow

*(Stated in the recommended presentation; the beats themselves are
presentation-agnostic and would survive a different §7 outcome.)*

1. **First launch — the book opens.** No menu wall: the player opens a book whose
   early pages are already written (the world's deep past, skimmable, three
   sentences per era). The first blank page carries their first life. Feeling:
   *small, but seated* — the world clearly predates you, and the book clearly
   expects you.
2. **First life — writing.** Two or three fateful moments, each a full page: the
   situation in the historian's voice, a few heavy choices. Acting on a durable mark
   leaves a quiet cue: *"this will echo."* Feeling: agency without power.
3. **First death — the ink dries.** The entry ends; the page turns on its own;
   years flick past in the margins. Death is staged as the book continuing to write
   *without you*. Feeling: loss, immediately reframed as anticipation.
4. **Rebirth — the world you return to.** A spread opens generations later: one
   line per thing that changed *because of your last self*, and the map redrawn
   beside it. This is the first jolt. Feeling: powerlessness inverts.
5. **Discovery — "I know that name."** In a later life, an opportunity or a person
   is your own legacy — presented first as ordinary history, then recognized (the
   staging leaves the gap for the player to get there first; the book confirms
   rather than announces). Feeling: the shiver. This is the game's peak and it is
   protected: guaranteed once in the first world, rare afterward.
6. **Ending — the book closes.** The world's span ends; the chronicle becomes a
   finished object — the very book the player has been inside — now readable end to
   end, with their marks named. The player follows at least one major event back to
   their own hand. Feeling: quiet pride, a little grief.
7. **Replay motivation — a different me.** The closed book goes on a shelf beside
   an empty slot. The prompt is not "play again" but *"a different world could hold
   a different you"* — and the player starts a new world with an intended mark in
   mind (a faith world, a feared name, a legacy that outlives everything).

---

## 6. UI / Presentation Study

### 6.1 What the North Star demands of a presentation

Derived requirements, used as the comparison criteria's backbone:

- **R1 — Reading is the core verb.** The experience *is* reading history and
  recognizing a hand in it. The presentation must make reading feel native, not
  bolted on.
- **R2 — Time must be felt.** Centuries pass between mark and discovery. The
  presentation must render the passage of time as a first-class sensation.
- **R3 — Attribution must be stageable.** The "that was me" beat needs staging:
  withhold, hint, confirm. The presentation must support dramaturgy of information,
  not just display of it.
- **R4 — The world must visibly change.** The rebirth jolt lands hardest when the
  change is *seen*, not only told.
- **R5 — Honest expectations.** The presentation is a promise about the game.
  It must promise reading, choosing, and discovering — not fighting or roaming.

### 6.2 Alternatives considered

1. **Low-poly 3D world** — walk/observe a rendered world; junctures and history as
   overlaid panels.
2. **Isometric living map (2.5D)** — a fixed-perspective diorama-like world view;
   play and history read from above.
3. **Top-down 2D map-first** — cartographic world as the primary screen; events and
   lives as map annotations.
4. **Paper miniature / diorama** — handcrafted paper-craft look (physical theater
   staging); scenes as pop-up dioramas.
5. **Interactive history book** — the game is a book; pages, spreads, marginalia;
   map and portraits as plates inside it.
6. **Timeline-first board** — the causal timeline/graph is the primary surface;
   lives and events as nodes and threads.
7. **Visual novel style** — scene illustrations + dialogue-box text; junctures as
   VN choices.
8. **Hybrid: Book + Map spread + Threads spread** — the book as the frame; the map
   and the investigation board as special spreads *inside* it.

### 6.3 Comparison matrix

Scale: ◎ strong · ○ adequate · △ weak · ✕ works against it.

| Criterion | 3D | Isometric | 2D map | Diorama | Book | Timeline | VN | **Hybrid book** |
|---|---|---|---|---|---|---|---|---|
| Supports Core Experience (R1, R3) | ✕ | △ | △ | △ | ◎ | ○ | ○ | **◎** |
| Encourages self-driven discovery | △ | △ | ○ | △ | ○ | ◎ | △ | **◎** |
| Emotional impact of time (R2) | △ | △ | △ | ○ | ◎ | ○ | △ | **◎** |
| Rebirth jolt visibility (R4) | ○ | ◎ | ◎ | ○ | △ | △ | ✕ | **◎** |
| Honest expectations (R5) | ✕ | △ | ○ | ○ | ◎ | ○ | ○ | **◎** |
| Readability of history | ✕ | △ | ○ | △ | ◎ | ◎ | ○ | **◎** |
| Production cost | ✕ | ✕ | ○ | ✕ | ◎ | ◎ | △ | **○** |
| Development risk | ✕ | ✕ | ○ | ✕ | ◎ | ○ | ○ | **○** |
| Expandability after v1 | ○ | ○ | ○ | △ | ◎ | ○ | △ | **◎** |
| Solo-developer suitability | ✕ | ✕ | ○ | ✕ | ◎ | ◎ | △ | **○** |
| Shippable by 2026-08-16 | ✕ | ✕ | ○ | ✕ | ◎ | ◎ | △ | **○** |

### 6.4 Trade-off notes (why each non-winner loses)

- **Low-poly 3D.** Fails the North Star three separate ways. (a) Its strengths —
  embodiment, navigation, moment-to-moment presence — serve verbs the definition
  explicitly rejects; the design offers nothing for a 3D camera to *do* between
  junctures. (b) History across centuries is illegible in a rendered scene; every
  meaningful beat (attribution, causality, recognition) would arrive as text panels
  bolted onto the world — the panels would *be* the game, and the 3D a very
  expensive picture frame. (c) It makes a false promise (R5): a general gamer
  reading a low-poly 3D screenshot expects to move, act, and fight; discovering the
  game is "reading with choices" produces the worst review a game can get — *"it's
  not what it looks like."* Add the highest cost and risk of any option for a solo
  developer with four weeks, and 3D is not merely unaffordable — it would be the
  wrong choice at any budget.
- **Isometric / diorama.** Both soften 3D's cost only somewhat while inheriting its
  core problem: they are *scene* presentations for a game whose soul is *document*.
  The diorama look is charming and thematically adjacent (a staged miniature past)
  but is the most asset-hungry direction per screen — untenable solo.
- **Top-down 2D map-first.** The strongest of the "world view" family: the rebirth
  jolt is superb on a map (R4 ◎), and cost is sane. But as the *primary* frame it
  inverts the hierarchy — the map can show *where* things changed but not *why* or
  *by whose hand*; R1 and R3 live in text, and a map-first UI keeps pushing the
  text into pop-ups. The map belongs *inside* the winner, not around it.
- **Timeline-first board.** The best pure *investigation* surface (R3 ◎, cheap,
  legible) — but as the whole game it is an analysis tool, not an experience: it
  front-loads exactly the attribution the design wants the player to *earn*
  (violates Principle 2), and it renders time as geometry rather than sensation
  (R2 ○ at best). It belongs inside the winner as the investigation spread.
- **Visual novel.** Strong at staging a *single life's* choices, and cheap-ish —
  but it is structurally protagonist-centric (violates Principle 6), renders the
  passage of centuries poorly (R2 △), and has no native answer for the rebirth
  jolt or the finished-world reading (R4 ✕). Its juncture staging is worth
  stealing; its frame is wrong.
- **Plain book (non-hybrid).** Nearly wins alone — best-in-class on R1, R2, R3, R5,
  cost, and schedule — but is weakest exactly where the map is strongest (R4: a
  book *tells* you the world changed; a redrawn map *shows* you). The hybrid exists
  to close that one gap.

---

## 7. Final UI Direction — **"The Living Chronicle"**

**The game is a book.** Not a game with a codex — the book *is* the play surface,
the reveal surface, and the ending artifact, all one object.

### The concept

- **Every screen is a page or spread** of a single illuminated chronicle. Lives are
  entries; junctures are full-page choices; the deep past is the already-written
  front matter.
- **Writing is playing.** While the player's soul is alive, the current entry is
  being written — their choices in a hand distinct from the printed history.
- **Death is the ink drying.** The entry stops; the book keeps writing without
  them; years flick by in the margins. The time-skip — the engine's most important
  invisible event — becomes the presentation's most visible gesture.
- **Rebirth is the book reopened generations later** on the "world you return to"
  spread, beside the **Map spread**: an illustrated map, redrawn, with the changes
  the player caused marked on it.
- **Recognition is typographic.** A legacy first appears as ordinary printed
  history; when the player engages it, the page reveals the marginal hand — *their*
  hand — beneath the print. The staging (print first, hand second) is what leaves
  room for the player to get there before the book confirms it.
- **The ending is the book closing.** The finished chronicle — the object the
  player has been inside all along — becomes readable end to end, keepable, and
  handable to a friend. The shelf beside it holds the empty slot that is the replay
  motivation.
- **The Threads spread** (Should Have) is the investigation board *as a spread in
  the book*: ribbons connecting an event backward through its ancestry to a life
  and a choice, including consequences that fired after that life died.

### Why it best delivers the Core Experience

1. **It is the North Star made literal.** The One Sentence — "a diary written in
   your own forgotten hand" — stops being a metaphor and becomes the actual object
   in the player's hands. No other direction achieves *identity* between fantasy
   and interface; the rest merely *depict* the fantasy. This is Principle 10 at
   full strength: the interface is the artifact.
2. **It makes reading the expected activity** (R1). In every scene-first
   presentation, history text is an interruption; in a book, it is the medium. The
   game's largest asset — an engine that writes true, attributable history — is
   finally load-bearing instead of hidden behind panels.
3. **It renders time as a physical sensation** (R2). Pages turning, ink drying,
   margins accumulating — the book has a native vocabulary for "centuries pass"
   that no camera has. Principle 5 (time distance is emotional distance) gets a
   *mechanism*, not just an intention.
4. **It supports dramaturgy of information** (R3). Print vs. hand, page-turn
   pacing, plates that unfold — a book can withhold, hint, and confirm. The
   recognition beat can be *staged* (Principle 2: induced, not delivered).
5. **It makes an honest promise** (R5). A book on the store page promises reading,
   choosing, discovering — exactly what the player gets. The audience it attracts
   is the audience that will love it. (Proven appetite exists: *Pentiment*, *The
   Life and Suffering of Sir Brante*, *Wildermyth*, *80 Days* — reading-forward,
   choice-driven, broadly loved. These are reference points for tone and staging,
   not templates.)
6. **The hybrid closes the book's one weakness.** The Map spread delivers the
   rebirth jolt visually (R4) — the holy site *appears on the map* where your relic
   was — and the Threads spread delivers self-driven investigation. Both live
   inside the book, so the frame never fractures.
7. **It is the only direction that strengthens under the deadline.** Its craft
   ceiling is typography, layout, ink motion, and a handful of illustrated plates —
   exactly the crafts where a small, disciplined effort reads as *intentional
   style* rather than *missing budget*. Every scene-first alternative reads as
   cheap at low budgets; a book reads as austere. And post-v1 it expands cleanly:
   more plates, richer maps, the Atlas as a *shelf of books*, even an optional 3D
   desk *around* the book — all additive, none load-bearing.

### The direction's own risks, named

- **The wall of text.** The failure mode is a book that feels like documentation.
  Guarded by Principle 11 (one page, one focus), the copy style guide (§9-4), and a
  hard rule: *no page exists whose focal object is a paragraph.* Every page centers
  a choice, a mark, a reveal, a map, or a plate — prose supports the object.
- **First-minutes drag.** Books start slow; games may not. The guided first world
  (§9-7) must put the first choice on screen within ~3 minutes and the first jolt
  within ~13 (per `player_journey.md` §1) — the front matter is skimmable theater,
  not required reading.
- **Audience positioning.** "General gamer with a 3D UI" and "reader-gamer with a
  living book" are different promises. This review recommends the second on North
  Star grounds; the positioning change should be a conscious decision (see §10,
  Q1).

---

## 8. Design Principles

Updated set (11) lives in §3.7. Deltas vs. the prior definition:

- **Modified — Principle 7:** recognition is now *"guaranteed once, rare
  thereafter"* (was: rare only). The first-session guarantee is what Success
  Criterion 1 stands on.
- **New — Principle 10, "The interface is the artifact."** The diegesis rule that
  drove §7 and will drive every future presentation decision.
- **New — Principle 11, "One page, one focus."** The readability rule that guards
  the chosen direction against its own failure mode; includes the historian's
  voice as a specified character.
- All other principles carry over verbatim (never fabricate history · induced
  discovery · few heavy inputs · death as punctuation · time distance · the world
  does not flatter · same world always · finishable as a reading).

---

## 9. Required Design Deliverables (before implementation begins)

Ordered; 1–3 are the critical path, the rest may trail.

1. **Page inventory & flow map.** Every page/spread in the game, named, with entry
   and exit transitions — the complete topology of the book. Nothing gets built
   that is not on this map.
2. **Tutorial world script.** The chosen seed plus the staged first session: which
   junctures the first world presents, where the plant cue, first jolt, and
   guaranteed recognition land, timed against the ≤30-minute bound. This document
   *is* Success Criteria 1–3 in executable form.
3. **Beat specs (recognition & rebirth).** For each: trigger conditions, staging
   order (withhold → hint → confirm), copy rules, frequency rules (guaranteed
   once / rare thereafter), and what the player must be able to say afterward.
4. **Voice & copy style guide.** The historian as a character: tone, tense, person,
   sentence length; the player-facing glossary (mark / echo / legacy / "still
   shaping the world" / the hand); the print-vs-hand typographic distinction and
   what each is allowed to say.
5. **Wireframes for the core spreads.** Life page · juncture page · death page ·
   rebirth spread · Map spread · ending/closed book (+ Threads spread if the
   Should holds). Wireframe level: layout and focal object per page, not art.
6. **Visual style guide.** Paper, ink, palette, typography, plate style, and the
   motion language (page turns, ink drying, margin time-flicker). One page of
   references, one page of rules.
7. **Map spread spec.** What the map shows, what may change on it between lives,
   how a player-caused change is marked, and what the map deliberately does *not*
   do (no navigation, no fog-of-war game — it is a plate, not a level).
8. **Ending & artifact spec.** What the closed chronicle contains, how the
   player's marks are named in it, what "handing it to a friend" consists of, and
   the shelf/empty-slot framing of replay.
9. **Playtest protocol.** How Success Criteria 1–4 are observed with first-time
   players: session script, what the observer records, pass/fail wording for each
   criterion, minimum number of testers.
10. **Sound direction one-pager** *(Should).* Page, ink, and time-skip as the three
    signature sounds; where silence is used.
11. **Risk-cut plan.** The pre-agreed cut order if the schedule slips (proposed:
    Threads spread → portrait plates → sound → world sharing — the Musts are never
    on this list), plus the date on which each cut decision is made.

---

## 10. Open Questions / Risks

**Questions (need a decision from the project owner):**

- **Q1 — Audience positioning.** This direction consciously trades "general gamer"
  for "reader-gamer" (the *Pentiment* / *Sir Brante* audience). Accept the
  repositioning, or does an external commitment require the 3D promise? This is
  the one decision this review cannot make.
- **Q2 — Language of v1.** The book direction makes prose the product; the choice
  of shipping language(s) (English only, Japanese only, both) changes the copy
  workload materially and must be fixed before deliverable 4.
- **Q3 — Input & platform posture.** A book wants pointer/touch; is v1
  keyboard-and-mouse only, and is controller support explicitly a non-goal?
- **Q4 — Sharing scope.** Is "hand a world to a friend" in v1 a Should (as scoped
  here) or is it required for launch messaging?

**Risks (owned by this design):**

- **R-A — Schedule.** Four weeks solo is aggressive even for a 2D book UI. Mitigated
  by the smallest-possible Must set (§4), deliverable 11 (pre-agreed cuts), and a
  direction whose quality bar is typography rather than assets. If the Musts
  themselves come under threat, the release date — not the Core Experience — is
  what should move.
- **R-B — The guaranteed first recognition.** Success Criterion 1 depends on a
  first world whose seed reliably produces an early recognizable legacy. If no
  such staging exists within current behavior, the tutorial script (deliverable 2)
  must find a seed and input path that does — this is a *content search*, and it
  must be validated before implementation is planned around it.
- **R-C — Text appetite.** Some players bounce off reading regardless of staging.
  Accepted consciously via Q1; mitigated by Principle 11 and the ≤30-minute first
  session, and monitored via the playtest protocol.
- **R-D — Scope creep in the Map spread.** Maps attract features (navigation,
  zoom, fog). Deliverable 7 exists specifically to fence this: the map is a plate
  inside a book.
- **R-E — Style-guide drift.** With one person writing all copy under deadline,
  the historian's voice will drift unless deliverable 4 is written *first* and
  every page is checked against it.

---

## 11. Final Recommendation

1. **Adopt "The Living Chronicle" as the v1 presentation direction** and formally
   retire the low-poly 3D assumption. 3D is not postponed — it is rejected as a
   frame for this game; at most it may return post-v1 as optional dressing around
   the book.
2. **Adopt the updated Design Definition (§3, v1.1)** as the top-level document for
   all specification decisions through 2026-08-16, replacing the 2026-07-17
   session version.
3. **Freeze v1 scope as §4** — the four-beat loop, the book core, the Map spread,
   trace-one-event investigation, the guided first world, and the historian's
   voice as Musts; everything else cuttable.
4. **Produce deliverables 1–3 of §9 before any implementation planning**, and
   decide Q1 and Q2 before deliverable 4.
5. **Gate the release on the four Success Criteria (§3.5), observed via the
   playtest protocol** — not on feature completeness. If the criteria pass with
   Shoulds cut, ship; if they fail with everything built, do not.

The engine already writes true history in the player's forgotten hand. The entire
job of v1 is to put that book in their hands — so build the book.
