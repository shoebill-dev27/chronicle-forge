# I-3 — The Rebirth Digest (P-10)

Status: **implemented** · designed 2026-08-27, built 2026-08-27 · base `34361ab` (I-2 shipped)

The loop's missing page. I-2 closed a life (juncture → act → death) and I-1b
gave the skip a surface; what is still absent is the page the skip hands to,
where the world says what it did with the life that just ended. D-5 puts the
standard world's *guaranteed first recognition* on exactly this page (SP-1), so
this is not decoration: it is the increment that makes a generated world keep
its promise.

Everything below is measured on real worlds, not assumed. The sweeps are seeds
1–30 (116 aftermaths) unless a narrower set is named.

---

## 1. What I-3 actually is, after I-1b

The roadmap (§2, table) lists I-3 as *"P-09/P-10/P-11; rebirth-digest read-model
lens (new, golden-pinned); map plate with mark accumulation."* Two of those three
pages are already settled, and the third cannot be built yet:

- **P-09 Passage of Years — already shipped.** The C1 Time Surface *is* P-09;
  the roadmap says so itself (§2b: *"the years beat … is now the Time Surface,
  and the skip's events are its content"*). Nothing to do.
- **P-11 Map — blocked, and provably so.** Measured across seeds 1/7/42/99/123:
  **0 of 301 causal nodes carry a `location_id`.** Every event in this engine is
  placeless. A map plate would have to invent a position for every mark it
  draws, which is precisely the thing the client is forbidden to do. P-11 waits
  on W-1 (a spatial axis in worldgen), not on view work. **Out of I-3's scope by
  data, not by preference.**
- **P-10 Rebirth Spread — the whole of I-3.** Its left page only: the right page
  is the map.

So **I-3 = P-10 left page**, and its exit test narrows from *"death→digest→map
cycle E2E"* to *"death→digest→next life E2E."*

### Deviation from the roadmap's wording: no `reporting/` lens

The roadmap predates I-1b and says "read-model lens (new, golden-pinned)",
meaning a module under `reporting/`. That is now the wrong home, for a
verifiable reason: **a reporting lens cannot see which act the player sealed.**
`reporting.labels.seed_label` resolves a seed through `life.activity_log`, whose
`category` yields the world's own phrase for an act (*"found a local council"*).
It has no access to the *displayed option label* the player read and chose
(*"Support Karic"*) — that lives only in `opportunity`/`render._display_label`
at the moment the juncture is answered.

The beat stream is the read-model now, and `BeatRecorder` is the only place that
holds the causal graph, the seed ids and the sealed labels simultaneously. The
digest is therefore computed in `play/beats.py`. This also keeps `reporting/`
untouched, as the increment's constraints require.

---

## 2. The measurement that decides the contract

The question I-3 has to answer is: **what real data can carry a delivered
recognition at the first rebirth?** Three candidate inputs exist on the
`aftermath` beat and its neighbours. Two of them fail.

### 2.1 `hardened` cannot be the digest — 0 for 229

`Aftermath.hardened` carries marks that gained a *name* during the skip
("Order of the Quiet Hand"), which is the loudest thing the engine can say. It
is unusable here, twice over:

| | measured |
|---|---|
| hardened marks at the **first** rebirth | **0**, in every seed measured |
| hardened marks founded by the life that **just died** | **0 of 229**, seeds 1–30 |

The first row is structural — `render._hardened`'s own docstring says a seed
hardens "a life or two after the one that planted it". The second row is the
decisive one: **every hardened mark belongs to a life older than the last**, and
D-03 (UX spec §"Hide") forbids the digest from delivering changes caused by
lives older than the immediately previous one — those *must* be discovered.

So `hardened` is not a digest input at all. It is the spec's *"older,
unexplained marks"* — material for P-11 and for I-4's tracing, delivered to
nobody. This is a boundary the implementation must hold, not a gap to fill.

### 2.2 Raw `echoes` cannot be the digest either — 2–5 distinct things said 3–107 times

`Aftermath.echoes` is guaranteed present (3–28 events at the first rebirth
across seeds) and is already last-life-only by construction: `render._echoes`
selects nodes with a causal edge from *that life's own seeds*. D-03 is satisfied
for free.

But its raw form is unusable. Seed 1's first rebirth has **28 echoes carrying 4
distinct phrases**; seed 7 has 15 echoes carrying 3. Taking "the top 3" prints
*"war breaks out / war breaks out / war breaks out."* The engine's event
vocabulary is five phrases wide (`war breaks out`, `the order of rule shifts`,
`the faith takes root`, `a new craft spreads`, `trade flourishes`) — the same
content floor W-1 names, and I-2 already filed.

Repetition is not additional truth. The digest must group.

### 2.3 The join that works: (act → consequence)

Each echo names an event; each echo's `caused_by` edges name **which seed of the
last life produced it**; each seed resolves to an act. Grouping by *(act,
consequence)* collapses the noise into distinct statements:

| seed | echoes at 1st rebirth | distinct (act → consequence) |
|---|---|---|
| 1 | 31 | 4 |
| 7 | 19 | 3 |
| 42 | 11 | 3 |
| 99 | 7 | 2 |
| 123 | 19 | 4 |

Both halves are real and already in the world; the join is one existing causal
edge. Nothing is invented, and the ≤3-line budget the UX spec asks for is
exactly what the data yields.

### 2.4 SP-1 holds, and it holds on the player's own words

The strongest available attribution is the seed planted by the act the player
**sealed** — because its label is the string the player read on the juncture and
that I-2's entry page already printed back to them ("Support Karic", "Tend the
Ashfields", "Further Free Lanterns"). Measured over **seeds 1–30**:

- **30 of 30** first rebirths produce a non-empty digest.
- **30 of 30** contain **at least one line descending from an act the player
  sealed** (25 seeds have exactly one, 5 have two — life 1 has 1–2 junctures).
- Line counts at the first rebirth: 2 lines (2 seeds), 3 lines (5), 4+ (23).

**SP-1 is loop-guaranteed on real data, with no staging and no engine change.**
That is the finding I-3 rests on, and it is directly testable.

> **Correction, 2026-09-09.** The 30/30 above was measured with a `sealed` flag
> that was not yet telling the truth. `BeatRecorder.on_outcome` wrote *every*
> resolved act into `_sealed`, but the session answers the juncture itself on
> EOF, on empty input, and on an explicit pass — so acts **the world chose** were
> being reported as acts the player sealed. A run with no player input at all
> still claimed sealed lines.
>
> `sealed` now means the player really answered that juncture. Re-measured:
> **SP-1 holds 30/30 on played runs** (seeds 1–30, always picking option 1), and
> a fully-entrusted run now correctly claims **zero** sealed acts. The guarantee
> survives; it is simply now true rather than true by accident. The digest golden
> moved `8ab659ae98abb179` → `3816281ad6b04a43`, and the SP-1 assertions in
> `test_beat_stream.py` / `test_client_bridge.py` now measure played runs.

### 2.5 The empty digest is always terminal

17 of 116 aftermaths across seeds 1–30 produce no digest lines. **All 17 are the
world's final aftermath** (`empty mid-world = 0`), where the world has ended and
there is no rebirth to turn to — so P-10 is never reached with nothing to say.
The client already distinguishes this case (`win.rebirth`), so the page needs no
"nothing happened" state. The implementation must still *fail closed* — no
rebirth beat, no digest page — rather than rely on the sweep.

---

## 3. The contract

A new field on the existing `aftermath` beat. It is the same beat's meaning
("what the years did with what you left"), in its ordered, attributed form.

```python
@dataclass(frozen=True)
class Change:
    """One thing the world did with one act of the life that just ended."""
    act: str        # what the player sealed, in the words they read it in;
                    # otherwise the world's phrase for the act (seed_label)
    sealed: bool    # True when this act was the player's own sealed choice
    consequence: str  # event_phrase of the events it caused
    times: int      # how many events, so the client can weigh without a score
    first_year: int # when the world first moved on it
```

`Aftermath` gains `changes: Tuple[Change, ...]`, ordered **sealed acts first,
then by `times` descending, then `first_year`** — a total order with no ties, so
the stream stays deterministic in `(seed, choices)`.

Invariants the tests pin:

1. Every `Change` descends from a seed of the life the aftermath follows —
   never an older life (**D-03**).
2. `hardened` never contributes to `changes`.
3. At the **first** aftermath of every measured seed, `any(c.sealed)` is true
   (**SP-1**).
4. `changes` is empty only when the aftermath is terminal (no rebirth follows).
5. Both `act` and `consequence` are engine strings — `render._display_label`,
   `reporting.labels.seed_label`, `reporting.labels.event_phrase`. The client
   composes them, and authors neither.

**The cut to 3 (UX spec: *"at most 3 lines"*) is made in the stream, not on the
page** (`beats.DIGEST_MAX`). The first draft of this note left the field
untruncated and made the cap a page decision; that is wrong, and D-03 is why.
Everything past the third line is truth the game is *not permitted to deliver* —
it is what the player has to find. A stream that carried the remainder would be
handing the client exactly the material it is forbidden to print, and the only
thing standing between it and the page would be a `slice` in the view. Nothing
is lost downstream: I-4 traces the world through P18's lens, not through the
beat stream.

Golden: the property tests above are the real guard — a hash cannot tell you
SP-1 held. `GOLDEN_DIGEST_SHA = 8ab659ae98abb179` over the `changes` of seeds
1/7/42/99/123 rides along as cheap drift detection.

---

## 4. The page

One insertion point, already visible in `book.js`:

```js
function turn() {
  if (document.documentElement.dataset.surface === "time") {
    if (skipSurface()) return;
    return advanceTo(state.lifeShown + 1);   // ← the digest goes here
  }
```

The surface currently hands straight to the next life's opening. P-10 goes
between them: **surface → digest → next life.** `PAGES` gains `"digest"`;
`turn()` on the digest calls `advanceTo(state.lifeShown + 1)`, which is what the
surface does today, so the existing path is preserved exactly.

The left page carries the UX spec's heading and ≤3 lines, each with its ⟜ (the
echo mark — ADR-001 K-1's closed pair, no new glyph). Sealed lines are the
player's own words, so they read back what the entry page wrote a screen ago.
The right page is blank stock until W-1 makes a map possible; the spread is not
faked with a decorative plate.

Copy is additive to `strings.js` and structurally identical to what the UX spec
already writes (a heading and a joiner) — no new voice, no epithet-table change.

**No client-side reinterpretation:** the page renders `changes` in the order it
was handed, applies the ≤3 cap, and does nothing else. It does not rank, filter
by `times`, or decide what "matters".

**The page may never read a beat the player has not reached** — the rule I-2's
hardware gate produced. The digest is bound to `state.win`, the window just
played, and not to `beatsOf("aftermath")`.

---

## 5. Boundaries this increment must not cross

| Thing | Why it is not here |
|---|---|
| **P-11 Map** | 0/301 causal nodes have a `location_id`. Blocked on **W-1**; a map now would be invented geography. |
| **P18 / `investigation.py`** | Its 17 RED tests stay RED and untouched. P18 is I-4's lens (tracing), not I-3's. |
| **`hardened` in the digest** | 0/229 marks are last-life. Delivering them breaks **D-03** and spends I-4's discovery. |
| **Engine content** | The five-phrase event vocabulary and the always-true plant cue are **W-1/X-9**. I-3 makes the floor legible; it must not paper over it. |
| **Recognition timing** | Unchanged. SP-1 is met by reading data that already exists at the first rebirth — nothing is moved earlier in the engine. |
| **ENGINE_VERSION / goldens** | `observer=None` keeps the transcript byte-identical; `0.1.0-p8-mvp` stands. |

---

## 6. What was built

One unit, because the beat and the page are meaningless apart. Delivered as
designed, with the one amendment recorded in §3 (the 3-line cut moved from the
page into the stream):

1. `play/beats.py` — `Change`, `Aftermath.changes`, and the join in
   `on_aftermath`. `BeatRecorder` must retain the sealed acts' planted seed ids
   per life (`on_outcome` computes them already and currently discards them).
2. `client/web/` — the `digest` page: `index.html` section, `book.js`
   (`toDigest`, the `turn()` seam, `PAGES`), `book.css`, `strings.js`.
3. `tests/test_beat_stream.py` — the five invariants of §3, the SP-1 sweep, and
   the digest golden.
4. `tests/test_client_bridge.py` — the page carries no world copy of its own; the
   walk reaches the digest between surface and next life.
5. G0 re-run (seeds 1/7/42/99/123) — this adds a page to the loop the gate
   walks, and the gate's whole value was catching what headless capture cannot.
   `smoke_driver.py` gained the digest stage (its own probe, eight checks and
   the `09b-digest` frame).

**Result: 678 passed, 17 failed** — the 17 are the pre-existing P18 RED and no
others. All 8 engine goldens, the chronicle golden and the transcript golden
`41cf1cfd843f6272` are unmoved; `engine`-side modules, `worldgen.py`,
`persistence/` and `reporting/` have zero diff; `ENGINE_VERSION` stands at
`0.1.0-p8-mvp`; the observer still changes no byte of the transcript. **G0:
seeds 1/7/42/99/123, 0 failures each**, with the digest rendering on real
hardware — e.g. seed 1 delivers *"Support Karic — the order of rule shifts."*
above two of the world's own acts, one ⟜ per line in the margin stage.

## 7. Still open

- **Q-UX-4 (digest overflow), standard-world half.** With ≤3 of 2–8 grouped
  changes shown, the remainder become undelivered truth. The tutorial half is
  resolved (Δ3); the standard-world rule stays open and is I-6's, not I-3's.
- **Q-SW-3 (delivered vs. earned framing).** The proposal is neutral copy in
  generated worlds; §4's copy is written neutral pending the owner's call.
- **The consequence half is five phrases wide.** The digest's specificity is
  capped by W-1 until worldgen says more than *"war breaks out."*
