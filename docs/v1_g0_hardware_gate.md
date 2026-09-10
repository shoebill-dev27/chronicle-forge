# G0 — the real-hardware gate

Status: **PASSED 2026-08-21**, on `design/v1` at 564b56f + I-2, seeds 1 / 7 / 42 /
99 / 123, 0 failures each.

Every UX judgement made between I-1 and I-1b was taken in **headless Chrome over
`file://`**. The client had never been seen in the window it actually ships in.
That mattered more than it sounds: the Time Surface is a `<canvas>` that
QtWebEngine rasterises through a different path than Chrome's headless
compositor, the two bundled faces are 8.7 MB of woff2 loaded from a `file://`
origin, and the supported viewport (1180×880, `min_size` 940×760) had never been
laid out anywhere but in a browser tab.

This gate is the answer to "does it work on hardware", and it is written to be
re-runnable rather than remembered.

---

## 1. Running it

```bash
# WSLg desktop; PyQt5 + QtWebEngine + pywebview must be importable
python3 -c "import webview, PyQt5.QtWebEngineWidgets"

DISPLAY=:0 SHOTS=docs/screenshots/g0 TAG=g0-s1 SEED=1 \
    python3 docs/screenshots/g0/smoke_driver.py
```

One run ≈ 45 s and writes `docs/screenshots/g0/{TAG}-*.png` plus
`{TAG}-notes.json` (every measurement, and the list of failures — empty on a
pass). The whole sweep:

```bash
for S in 1 7 42 99 123; do
  DISPLAY=:0 SHOTS=docs/screenshots/g0 TAG=g0-s$S SEED=$S \
      python3 docs/screenshots/g0/smoke_driver.py | tail -1
done
```

The **PNGs are deliberately untracked** — `docs/screenshots/` has been untracked
since P0/T3, and 12 MB of frames per sweep does not belong in history. The
driver and the `*-notes.json` measurements are tracked, so the gate can be
re-run and its last result read without them.

The driver descends from `docs/screenshots/p0/smoke_driver.py`; what is new is
the canvas probe and the whole I-2 loop.

## 2. What it asserts

| Check | Why it exists |
|---|---|
| the bridge is live | a SAMPLE fixture passing for a world would make every other check meaningless |
| both `@font-face` rules resolve, and the two faces **differ** | a face is fetched lazily, so `fonts.check` on the shelf answers "no" for a perfectly good Hand; the driver asks for both explicitly first. And the CJK test string is 1 em per glyph in *both* faces — only Latin separates a 明朝 from a 楷書 (measured: 203.33 vs 227.34 px) |
| the window is the supported viewport, and the desk does not scroll | `shell.py` asks for 1180×880; QtWebEngine is free to disagree |
| the juncture page fits the leaf, and the leaf fits the window | the fit pass (`fitPage`) had only ever run in Chrome |
| the canvas is **painted** at four moments of the cut | the blank-canvas question, answered numerically: sample the surface's own pixels and count distinct colours and the share differing from the corner. A canvas that failed to paint returns 1 colour and ink 0.0 |
| the strata **accumulate** | proves the animation is running, not that one frame happened to draw |
| the years hand the page back, and name the next life | the `#surface-turn`/`#surface-rebirth` handoff |
| a life with no juncture still gets its own window | seed 99's life 2 — the B-1 bug, checked on hardware |
| **I-2**: the act enters the entry, exactly one arrives, the cue matches the data one-for-one, the mark sits in the margin, the sealed juncture cannot be answered twice, the years follow the life's last act | the whole I-2 loop |
| **I-3**: the years hand to the digest, the surface lets go, the digest still names the life just buried, its lines are the stream's lines in the stream's order, ≤3 of them, at least one is an act the player sealed (**SP-1**), every line carries ⟜ in the margin, no line prints a number, and the page fits the leaf | the whole I-3 page. SP-1 is the standard world's *guaranteed* first recognition, so seeing it in the stream is not enough — it has to reach a screen |

## 3. Result, 2026-08-21 (re-run 2026-08-27 with I-3: 5 seeds, 0 failures)

All five seeds: **0 failures**. Measured on seed 1:

```
fonts       Chronicle Print:loaded · Chronicle Hand:loaded
            latin print=203.33  hand=227.34  (cjk 260 both; fallback 264.69)
window      1180×880 dpr 1, no document scroll
leaf        760×796 inside the window, no column overflow, zoom 1
canvas      680×420 css / 680×420 backing
            death   ink 0.683  colours 18
            years   ink 0.782  colours 50
            after   ink 0.801  colours 56
            rebirth ink 0.801  colours 56
entry       ["Year 0 — Support Karic."]  cues 1  marks 1  arriving 1
mark        x=280 15×28 opacity 1 rgb(110,74,47), left of the measure
handoff     "You are born again into Hollowfen — a priest, in an age of governance."
next life   page=juncture life=2, the surface let go
```

## 4. What the gate caught

**The entry was writing ahead of its reader.** Sealing replays the whole world,
so the stream always runs to the world's end. The first cut of I-2's entry page
listed *every* outcome beat of the life — and on seeds 7 and 123, where life 1 is
asked twice, the page for the first act already showed the second one. Headless
capture never saw it, because the capture harness only ever shoots a frozen
frame; the hardware walk hit it on the second seed. Fixed by cutting the acts to
`state.cursor` — the same discipline as the strata scale (`DEPTH`): the page may
never read a beat the player has not reached.

**The 2026-08-27 re-run caught nothing new** — the digest stage passed on all
five seeds first time. That is the expected result of a gate, not a wasted one:
the walk it protects is now a page longer, and the `#surface-turn` handoff it
used to assert would have gone stale silently otherwise (it now lands on the
digest, not on the next life).

## 5. Limits of this gate

- **WSLg, one machine, one GPU path.** Windows and a clean Linux desktop are
  DoD-9's fresh-VM smoke test, not this.
- **It measures, it does not judge.** That the canvas is painted and the cut
  runs says nothing about whether `SURFACE_MS = 14000` *feels* right. That is a
  human question and belongs to R1/R2.
- **Nothing here is a golden.** The frames are evidence, not fixtures; no test
  compares them.

---

## Update — 2026-09-10: the gate now walks the whole Discovery Vertical Slice

The gate used to stop at the second life: it proved one life, the Time Surface
and the rebirth digest on real hardware, which was everything the client could
do. The DVS added the other half of the loop, so the driver now plays the world
out and investigates it.

New legs, all on the real `BookBridge` in the real pywebview window:

* **The world closes into P-12.** The driver seals through every remaining
  juncture and skips every surface until the book ends, then reads the closing
  page: its passage, its threads, and both ways on
  (**「歴史を読み返す」/「本棚へ」**).
* **A thread is offered, or the miss is stated.** The check is an exclusive or —
  a world with no player-sealed thread must say so and record the content-gate
  miss, never invent an invitation.
* **Inspection is a visible, labelled control.** 「調べる」 is read off the page,
  focused, activated by keyboard *and* by pointer, and both reach the same trace.
* **The trace walks real edges.** Every step the case carries is walked and no
  more, and the origin card names the life, the year, and the act **in the exact
  words the player sealed it under** — seed 1 returns
  *「——最初のあなたが、0年に「Support Karic」を選んだ。」*
* **Player-sealed and autonomous origins read differently** (C-6), and reaching
  the origin earns the reveal.
* **The past is readable and inert.** The archive prints earlier acts, offers no
  option and no seal, and 「今の頁へ」 returns without re-executing anything —
  asserted against the sealed-choice count before and after.

The driver now runs with a book store (`STORE`, default `$SHOTS/books`), so the
run also exercises C-5 for real. After a full pass on seed 1 the book on disk
holds all **8 sealed inputs**, the reveal earned in the trace, and the cursor;
re-loading it answers `knows(...) == True`.

**Result (2026-09-10, seed 1): 0 failures, 0 bridge errors.** Evidence:
`docs/screenshots/g0/dvs-s1-notes.json`.

Two bugs were caught here that no unit test had: `BookBridge.move_cursor` used a
`**kwargs` signature that pywebview cannot reach positionally (every call from
the page raised a TypeError the page never saw, so the reader's position was
silently never written), and the page sealed via `play` rather than through the
book, so a quit between two junctures lost the act just sealed. Both now have
regression tests.
