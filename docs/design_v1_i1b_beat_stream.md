# I-1b — the typed beat stream, and the Time Surface on top of it

**Status:** implemented on `design/v1`, 2026-08-18. Uncommitted.
**Supersedes:** the regex seam described in `docs/v1_implementation_roadmap.md` §2b.
**Depends on:** [`design_v1_time_surface.md`](design_v1_time_surface.md) (the C1
"strata" decision) and [`review_x1_x4_first_loop.md`](review_x1_x4_first_loop.md)
(why the loop needed a surface at all).

---

## 1. What shipped

Three things, in dependency order:

1. **`play/beats.py`** — a typed stream of what a played world actually did.
2. **`play/session.py`** — one optional `observer` parameter, the seam that
   feeds it. Six call sites, no behaviour.
3. **`client/`** — the bridge hands that stream to the page whole; the page
   renders B2 → B3 → B4 → B1′ from it, on a new canvas surface (`web/time.js`).

The regex is gone: `client/bridge.py` no longer imports `re`, and `book.js` no
longer takes apart the terminal decoration of a header it was never given.

---

## 2. The contract

```
stream(seed, choices) -> WorldBeats {
    seed, place, max_year, end_year, ending,
    lives  : [ Life {ordinal, talent, birth_year, death_year} ],
    beats  : [ Rebirth | Juncture | Death | Years | Aftermath | Closing ],
}
```

Discriminated by `t` on the JSON side. Six kinds, not the seven the roadmap
proposed:

| beat | carries | drawn as |
|---|---|---|
| `rebirth` | life ordinal, birth year, talent, era | B4's second half, the line under the surface |
| `juncture` | year, age, reason, header, era, `options[]`, `recognition?` | B1 / B1′, the leaf |
| `death` | year, age at death, talent, title, marks already named, `pending` | B2, the surface's first frame |
| `years` | `from_year`, `to_year`, `span`, `world_ended`, `events[]` | **B3 — the whole surface** |
| `aftermath` | `echoes[]`, `hardened[]` | B4, the 朱 seals |
| `closing` | year, lives, ending, `legacies[]` | B6, the surface's last frame |

**Recognition is not a beat.** It only ever happens *at* a juncture, so it rides
on the juncture beat — and it names the option that carries it:

```python
Recognition(option=1, name="Order of the Open Road", founder_life=1,
            founder_talent="mentor", planted_year=0, reach=32)
```

That `option` field is the load-bearing one. The I-1 client marked option 1
unconditionally, which promised the player a past their world had not lived yet
(life 1, year 0, before any seed exists). Now the mark is placed on
`recognition.option` or nowhere, and `recognition` is `None` in every life-1
juncture of every measured seed — because the engine has nothing to recognise
there. The page cannot fabricate what the stream does not carry.

### What is deliberately absent

`CausalNode.location_id` is `None` on 100% of nodes across seeds 1/7/42/99/123.
There is no spatial axis to draw, so the stream carries **time and authorship**
and nothing else — which is also the pair of axes the Core Experience is made
of. Any future "where" needs engine work first (W-1), not a view.

---

## 3. The seam: `observer`

`run_human_world(..., observer=None)`. Six hooks — `on_rebirth`, `on_juncture`,
`on_death`, `on_years`, `on_aftermath`, `on_closing` — each placed immediately
beside the `render.*` call that speaks the same beat, so the surface and the
transcript can never disagree about what happened.

The observer is **told, never asked**: it cannot choose, cannot write, and
cannot change what is rendered. With no observer (the default) the run is the
run it always was.

> `test_an_observer_changes_no_byte_of_the_transcript` asserts this for all five
> seeds. It is the reason no golden, no `ENGINE_VERSION` and no replay gate is
> in play here.

`play/render.py` was **not modified**. `reporting/experience.py` (the P7 freeze)
was **not modified**. The beat builders import the same private helpers
`render.py` already imports from those modules and read them; no text generator
was touched, so no unfreeze is required.

---

## 4. The Time Surface (C1「地層」), on real data

`client/web/time.js`, drawn on a canvas that covers the leaf while the years
run. The book does not print the years — the years are the dark the book is read
in — so the surface is not a page inside the measure.

### Strata are a count, not a decoration

A layer's thickness is *the number of events that life has caused so far*, on an
absolute scale (`span / max(24, world_total)` px per event). Two consequences,
both true rather than designed:

* The first life's layer is **thin**, at the bottom of an empty dark frame. That
  is the honest picture of a first life: seed 42's first skip carries 7 events.
* By the last life the strata **fill the frame**. The world's whole history is
  the player's sediment. It reads as a progress bar and is not one — it is the
  same number the specks are, stacked.

During B3 the current life's layer accretes as the specks fall, because the
specks *are* the layer.

### Gold vs ash

Each speck is an event of a skip, placed at its year, inside the layer of the
life that caused it. Gold when the stream says the dying life owns it, ash when
it does not. In practice almost everything is gold. The
frame states the finding the spike made: **the eight years you were dead were
almost entirely your own doing.** Measured on the shipped path:

| seed | events per skip | owned |
|---|---|---|
| 1 | 30 · 27 · 16 | 71 / 73 |
| 7 | 15 · 32 · 24 | 71 / 71 |
| 42 | 7 · 25 · 28 · 0 | 59 / 60 |
| 99 | 4 · 2 · 17 · 11 · 0 | 32 / 34 |
| 123 | 11 · 20 · 32 · 0 | 63 / 63 |

### The camera is the beat

Through B3 the frame holds only the years the player was dead, so eight years
fill the screen. Through B4 it pulls back to the whole world and the mark turns
out to be buried far in the past. At the B4 climax it **pushes to the first
seal** — the seal never leaves its year or its layer; the frame comes to it.

That push is not styling. It is what wins the 292px store thumbnail: the frame
is decided by the 朱's share of it, and a bloom was measurably not enough (the
spike's `s42-SHEET292-b4-climax.png`). Marks sharing a planted year are spaced
by their own radii, because at the climax's magnification a fixed offset merged
two legacies into one blob the world never had.

### The three registers

A majority of aftermaths name nothing (73 of 117 windows measured in the spike;
in **every** seed the *first* one does). A surface that only worked when a
legacy hardened would be broken on the very first loop the player ever plays.
So the surface has three states and picks by data:

| register | condition | what it shows |
|---|---|---|
| `sealed` | `aftermath.hardened` non-empty | 朱 seals, the camera push, the legacy's name |
| `echo` | nothing hardened, `echoes` non-empty | no 朱; the strata and gold specks stand, and the caption counts them: 「その歳月、世界はあなたが遺したものの上で N 度動いた」 |
| `silent` | neither (the world ended) | the strata hold still: 「時が息をひそめる」 |

**The quiet register is the default first experience**, not an edge case:
`quiet=life 1` in all five seeds. It is intentionally dark and nearly empty at
292px — it is a thin sediment line under a night sky. It does not break, and it
does not pretend.

---

## 5. The loop, as the player now walks it

```
P-01 shelf  →  P-04 opening       ← rebirth beat (place · talent · era)
            →  P-06 juncture B1   ← juncture beat; no mark, because no past yet
   seal ────→  ▓ TIME SURFACE ▓
                 B2 death   0.00–0.14   the layer that is you, at its final depth
                 B3 years   0.14–0.47   eight years fall; the specks are yours
                 B4 after   0.47–0.70   pull back · the seals bloom · the push
                 B4 rebirth 0.70–0.80   "You are born again into … a …, in …"
            →  P-06 juncture B1′  ← the next juncture beat
                                    ⟜ marked iff recognition is not None
```

One seal, one juncture: `state.cursor` indexes the stream's junctures and
`state.choices` has exactly one entry per seal, so a choice is applied to the
juncture it was made at. A life asked more than once simply turns to its next
juncture; the years run only when the life has none left. The last life has no
page after it — the surface keeps its last frame and prints the closing beat's
own account of the world over the full strata.

**Sealing replays.** `bridge.play(seed, choices)` re-runs the world under the
choices so far, so what the surface shows is the consequence of *this* player's
choice, not of a pre-canned one. The first juncture is identical under every
choice list (options are drawn before the choice is made), which is asserted, so
the book can show a juncture before it has a choice to replay with.

### What the data says the first loop will feel like

Measured on the shipped path (`BookBridge.play`, choices `[]`), all five seeds:

| after | aftermath | next juncture | recognition |
|---|---|---|---|
| life 1 | 0 hardened, 3–28 echoes | life 2 | **None** |
| life 2 | 3–8 hardened | life 3 | **yes, all 5 seeds** |

X-4's finding — the first recognition never lands before life 3 — is unchanged
and was not engineered around. What changed is that lives 1 and 2 are no longer
silent: the quiet register shows the player their own sediment, and the sealed
register hands them a named 朱 seal one beat *before* the leaf asks them to
recognise it. The noticing gesture is now rehearsed twice before it counts.

---

## 6. Verification

| check | result |
|---|---|
| transcript with/without observer, seeds 1/7/42/99/123 | **byte-identical** |
| stream determinism (same seed, same choices, double run) | identical JSON |
| first juncture invariant under `[] / [1] / [2] / [3]` | identical |
| engine goldens (`-k "golden and not investigation"`) | **18 passed** |
| `ENGINE_VERSION` (`persistence/version.py`) | untouched — `0.1.0-p8-mvp` |
| W-1 replay gate / `persistence/` | untouched, no diff |
| stream determinism across processes (`PYTHONHASHSEED` 0/1/2/12345) | identical SHA |
| every life reachable from the book, seeds 1/7/42/99/123 | no life skipped, no page names another life |
| strata geometry with a louder future bolted on | **identical** |
| full suite | **612 passed, 17 failed** |
| the failures | *all* `tests/test_investigation_surface.py` — the pre-existing P18 RED. Zero failures from this work. |
| `black --check src tests` | clean |
| `git diff --check` | clean |
| capture run twice from cold, seed 42 | **16/16 byte-identical** |

### Screens

`docs/mocks/v1_client/capture.py` stages the **shipped** `client/web/` into a
Windows-visible temp dir, drops the real stream beside it as `capture-beats.js`,
and drives Windows Chrome headless over `file://` — same strings.js, same
book.js, same time.js, same bundled faces. No Playwright and no pywebview
(neither installs in this branch's venv).

Two things make a re-run reproducible rather than merely repeatable, and both
were found by re-running it:

- **A throwaway browser profile** (`--user-data-dir`). Chrome's default profile
  caches by URL, and every seed stages its stream at the same
  `capture-beats.js` path — so a second run served an earlier seed's world from
  cache and wrote it into a frame named for this one. A re-run of seed 42 drew
  *"Order of the Seven Fires"*, a legacy from another world, and the run's two
  292px contact sheets came out byte-identical to each other.
- **`--force-prefers-reduced-motion`.** The surface stills are frozen with
  `?t=`, but the B1′ juncture is a DOM page whose `.26s` page-turn keyframes
  run on the wall clock; its still landed mid-animation. `book.css` already
  stops exactly those animations under `prefers-reduced-motion`, so the flag
  settles the page instead of adding a capture-only path to the client.

With both, a cold re-run of a seed is 16/16 byte-identical to the committed
frames. 80 of them in `docs/mocks/v1_client/shots/`: six beats × two registers
× five seeds, a B1′ juncture per register, and a 292px contact sheet per
register (`s{seed}-SHEET292-{register}.png`).

---

## 7. Still open

1. **No real-hardware confirmation.** Everything above was judged in headless
   Chrome. `pywebview`/`PyQt5` are still not installed in this branch's venv, so
   the surface has never been seen in the actual window. Motion timing
   (`SURFACE_MS = 14000`) is a judgement, not a measurement.
2. **JP/EN.** The captions and the UI strings are Japanese; place names, legacy
   names, talents, event phrases and eras come from the engine in English. Every
   frame is mixed. Open since the X-1..X-4 review's question 3. The English
   diegetic lines are now at least *inventoried* — every sentence the page
   writes itself lives in `client/web/strings.js` and nothing is composed
   inline — so D-3 has one file to ratify rather than a grep.
3. **`talent` is printed raw inside a Japanese sentence** (`——二度目のあなた、
   scholarであった者。`). Unlike place and legacy names, `Talent` is a closed
   enum, so D-3 §6's "generated names are unbounded" exemption does not cover
   it; it wants a table in D-3, which is an owner call.
4. **An event with several owners is drawn in the layer of the first of them**
   (`time.js`, `attr()`), while gold/ash is decided by whether the life that
   just died is among them. Both are honest reads of `owners`, but only the
   second is exactly what the caption claims. 13% of events in the loudest
   measured seed. Deferred: it is a refinement, not a wrong statement.
5. **`Legacy.founder_life` is an English ordinal string** (`"second"`) where
   `Mark.founder_life` and `Recognition.founder_life` are ints. Nothing reads it
   yet; unify it when something does.
6. **`shelf()` is still a stub** (I-1's empty slot). Nothing in this work needed
   it; the Life Loop (I-2) does.
7. **Interactive play still answers one juncture per seal by replaying the whole
   world.** That is correct and cheap at 40-year worlds (16–115 ms measured),
   but it is not the incremental loop I-2 wants. Nothing in the surface now
   *depends* on the whole world being known: the strata scale was the one place
   that read beats the player had not reached, and it is a constant.
