# I-2 — the Life Loop: the entry, and the act that enters it

Status: **implemented 2026-08-21** on `design/v1`, after the G0 hardware gate
([`v1_g0_hardware_gate.md`](v1_g0_hardware_gate.md)). Builds on I-1b's typed beat
stream ([`design_v1_i1b_beat_stream.md`](design_v1_i1b_beat_stream.md), 564b56f).
No engine, worldgen, persistence or reporting change; `ENGINE_VERSION` unmoved.

---

## 1. What shipped

| Piece | Where |
|---|---|
| the `outcome` beat — what the sealed act did | `play/beats.py`, `play/session.py` |
| **P-05 the entry / P-07 the act arriving** | `client/web/index.html`, `book.js`, `book.css` |
| **S-03 the plant cue** | `book.js` (`act.planted > 0`), `strings.js` |
| the shelf stops being a stub | `client/bridge.py` |
| X-16 / X-17 (they ride the same transcript golden) | `play/render.py`, `play/session.py` |

The loop a player now walks:

```
P-01 shelf → P-04 opening → P-06 juncture → seal
          → P-05/P-07 THE ENTRY  ← the act, in the Hand, with its cue
          → P-06 the life's next juncture, if the world asks again
          → ▓ TIME SURFACE ▓ (B2/B3/B4) → the next life
```

## 2. The `outcome` beat

```
outcome: life · year · age · option · label · kind · planted
```

Emitted in `session._live_one` immediately after `execute_option`, **only for a
juncture the player was actually asked**. The turns the world takes on its own
are the life's weather, not its entry.

Three decisions worth keeping:

- **It is not a re-reading of prose.** The engine prints *nothing* at this
  moment — the transcript goes from one turn screen straight to the next — so
  there was no text to parse even if we wanted to. The beat is the world read in
  the same breath as the verb.
- **`planted` is a measured delta**, `world.seeds` before and after the call.
  Not a prediction, not a score. It is the only honest basis for S-03: a life
  that planted nothing must not be told that it did.
- **The choice is matched by identity, not equality.** Two options of one turn
  can compare equal by value; the entry must name the one actually taken. A
  choice outside the displayed three is the season let pass, recorded as
  `option: 0` — the entry says so rather than crediting the player with an act
  the world chose for them.

The observer contract is unchanged: told, never asked. `observer=None` runs are
byte-identical, and `test_an_observer_changes_no_byte_of_the_transcript` still
holds on all five seeds.

## 3. P-05 and P-07 are one page

The UX spec lists them separately — "the entry in progress" and "the chosen act
enters the entry" — but a book does not open a fresh leaf to write its next
line. They ship as **one page in two states**: the acts this life has taken, with
the newest one arriving in the Hand and settling into print.

**The entry offers no `flip`.** UX §P-06 makes flipping back a *before-sealing*
affordance and §P-07's frame shows exactly one verb. An entry that offered flip
would put an already-answered juncture back on the page with its seal re-armed —
the one way this design could answer a juncture twice.

**The entry may not read ahead.** Sealing replays the whole world, so the stream
always runs to the world's end; the acts shown are cut to `state.cursor`, the
number of seals actually made. This is the same rule the strata scale follows,
and it was caught on hardware, not in review — see the gate doc §4.

## 4. S-03, and what the data said

The spec conditions the cue on the act having "planted something durable". The
engine, measured over seeds 1/7/42/99/123:

| | |
|---|---|
| acts that plant a seed | **every one** (50/50 outcomes, `planted == 1`) |
| activation mode | `GUARANTEED`, 284/284 |
| decay | 0.0, 284/284 |
| magnitude | 50 / 62 / 70 / 82 |
| maturation | 5 / 8 / 10 years |

**There is no at-plant-time "durable / not durable" distinction in this engine.**
Every act plants exactly one seed and every seed is guaranteed to fire, so the
cue's condition is always true and the cue fires on every act.

The client is written on the data anyway — `act.planted > 0`, one cue and one
mark per planted act, none where there is none — so if the engine ever varies,
the page follows without a change. But the constancy is real and it is an
**engine-content** finding, not a client one: a promise made on every single act
is not a promise, it is wallpaper. It belongs with W-1/X-9 (option stakes), and
is filed here rather than papered over with a threshold the client would have
had to invent.

The mark is **⟜**, the echo mark, exactly as UX §P-07's frame draws it — the same
glyph a past echo carries, which is the point: the promise is addressed to the
self who will find it. ADR-001 K-1 allows two marks and this coins no third; a
test asserts the page draws nothing outside that pair.

## 5. The shelf

`bridge.shelf()` returned `{empty_slot, books: [], invitation}` — a stub. It now
also carries the `seed` and the `span_years` the book runs to, both read from
`generate_world` and neither a spoiler: worldgen fixes them before a life is
lived. `books` stays empty on purpose. A shelf of resumable and finished books
needs the discovery-state store (I-6); inventing spines for books that cannot be
reopened would be a worse stub than an empty shelf.

## 6. X-16 / X-17

Both are in `play/render.py` and both move `GOLDEN_TRANSCRIPT_SHA`
`c9a8096f6b83795c` → `41cf1cfd843f6272` (5 test files). The **world** golden
`e62d8f2cd24d2c72` and the chronicle golden are byte-identical.

- **X-16** — `skip_transition` answered "Time holds its breath; the world stands
  at its end." when the skip ran no years, i.e. after the last life, where the
  closing page follows immediately and says it properly. X-1 added that page
  *after* the line instead of replacing it, so 15 of 30 measured worlds printed a
  dead end and then an ending. It now says nothing and lets the closing page
  speak; `session` skips an empty block rather than emitting a blank.
- **X-17** — "One thing you set in motion **outlive** you" (2/30 worlds).

**X-15 was deliberately left out.** "Speak Ω per kind, and reserve one phrase for
the player's own trace" needs five new authored English phrases; that is copy,
and copy is D-3's and the owner's. It stays on the backlog rather than being
invented here.

## 7. Verification

| | |
|---|---|
| suite | **637 passed / 17 failed** — the 17 are the pre-existing P18 RED, unchanged |
| goldens | `-k "golden and not investigation"` → 18 passed; world golden byte-identical; transcript golden moved deliberately (§6) |
| observer | transcript byte-identical with and without, all 5 seeds |
| determinism | same `(seed, choices)` → same stream, across processes under `PYTHONHASHSEED` |
| hardware | G0 sweep, 5 seeds, 0 failures |
| `black --check src tests` | clean |
| engine / worldgen / persistence / reporting | zero diff |

New tests: 4 on the beat (one act per answered juncture, in order; `planted`
never exceeds what the life owns; the option recorded is the one sealed; the
label is the engine's own words and never an internal id) and 5 on the client
(the entry does not write ahead; no way to answer a juncture twice; the cue is
data-driven and coins no third mark; the shelf names the real book; the page
prints `outcome.label` rather than reconstructing it).

## 8. Still open

1. **The leaf is mostly empty.** The entry and the juncture both use a small
   part of a 760×796 leaf (see the gate's frames). The measure is right; the
   page has little to put in it, because a life is currently 1–3 acts and
   nothing else. This is the same content floor W-1 names.
2. **The cue fires on every act** — §4. Engine content, not client.
3. **P-05 shows only the player's own acts.** The auto-chosen turns are real and
   are not in the entry. That is a defensible reading (the book records what you
   chose) but it is a reading, and it should be an owner call before I-5's copy.
4. **JP/EN still mixed**, unchanged from I-1b §7-2. The new copy —
   `The entry` / `Year N — <label>.` / `This will echo.` / `you let the season
   pass.` — is in `strings.js` with the rest of the placeholder inventory.
5. **No save/resume.** `books: []` — I-6.
