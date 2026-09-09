"""G0 real-hardware gate — the I-1b client in an actual pywebview window.

Every UX judgement made since I-1 was taken in headless Chrome over `file://`.
This drives the SHIPPED client (real `BookBridge` over the real engine) in the
real window on the WSLg desktop, walks one whole life —
shelf -> opening -> juncture -> seal -> Time Surface -> the next life — and
reads back measurements at each beat, so "it works on hardware" rests on
numbers as well as on the screenshots.

Descended from `docs/screenshots/p0/smoke_driver.py` (T3/P0). What is new here
is the Time Surface: a `<canvas>` that headless Chrome renders through a very
different path than QtWebEngine does, and the 8.7 MB of bundled faces.

    DISPLAY=:0 SHOTS=docs/screenshots/g0 TAG=g0-s1 SEED=1 \
        python3 docs/screenshots/g0/smoke_driver.py

Nothing here is imported by the package; it is an instrument, not a test.
"""

import json
import os
import sys
import threading
import time

sys.path.insert(0, "src")

import webview  # noqa: E402
from PyQt5 import QtCore, QtWidgets  # noqa: E402

from chronicle_forge.client.bridge import BookBridge  # noqa: E402
from chronicle_forge.client.shell import _index_html  # noqa: E402

SHOTS = os.environ.get("SHOTS", "docs/screenshots/g0")
TAG = os.environ.get("TAG", "g0")
SEED = int(os.environ.get("SEED", "1"))
NOTES = []
FAILURES = []


class Grabber(QtCore.QObject):
    @QtCore.pyqtSlot(str, result=bool)
    def grab(self, path):
        try:
            from webview.platforms.qt import BrowserView

            bv = list(BrowserView.instances.values())[0]
            return bool(bv.grab().save(path))
        except Exception as exc:  # pragma: no cover - instrument
            print("GRAB-ERR", exc, flush=True)
            return False


_grabber = None


def shot(name):
    global _grabber
    app = QtWidgets.QApplication.instance()
    if _grabber is None:
        _grabber = Grabber()
        _grabber.moveToThread(app.thread())
    path = f"{SHOTS}/{TAG}-{name}.png"
    ok = QtCore.QMetaObject.invokeMethod(
        _grabber,
        "grab",
        QtCore.Qt.BlockingQueuedConnection,
        QtCore.Q_RETURN_ARG(bool),
        QtCore.Q_ARG(str, path),
    )
    print(f"  shot {name}: {'ok' if ok else 'FAILED'}", flush=True)
    if not ok:
        FAILURES.append(f"grab {name}")
    return ok


def js(w, code):
    return w.evaluate_js(code)


def note(key, value):
    NOTES.append((key, value))
    print(f"  {key} = {json.dumps(value, ensure_ascii=False)}", flush=True)
    return value


def check(label, ok, detail=""):
    NOTES.append((f"CHECK:{label}", bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label} {detail}", flush=True)
    if not ok:
        FAILURES.append(label)
    return ok


# --- probes -----------------------------------------------------------------

# A face is fetched lazily, when something on the page is set in it. The Hand
# is only ever used by a reveal, and life 1 can carry no recognition, so on the
# shelf `fonts.check` answers "not loaded" for a face that is perfectly fine.
# Asking for it explicitly first is what makes the answer about the woff2.
FORCE_FONTS = """
document.fonts.load('16px "Chronicle Hand"');
document.fonts.load('16px "Chronicle Print"');
1
"""

PROBE_BOOT = """
(() => {
  const m = (fam) => {
    const c = document.createElement('canvas').getContext('2d');
    c.font = '20px ' + fam;
    return Math.round(c.measureText('この手は前にもこれを選んだ').width * 100) / 100;
  };
  // A CJK string is 1em per glyph in BOTH faces, so it cannot tell them apart.
  // Latin is proportional and differently drawn in a 明朝 and a 楷書.
  const n = (fam) => {
    const c = document.createElement('canvas').getContext('2d');
    c.font = '20px ' + fam;
    return Math.round(c.measureText('Chronicle Forge 1234').width * 100) / 100;
  };
  return JSON.stringify({
  live: state.live,
  status: document.querySelector('#status').textContent,
  page: state.page,
  fonts_loaded: {
    print: document.fonts.check('16px "Chronicle Print"'),
    hand: document.fonts.check('16px "Chronicle Hand"')
  },
  faces: [...document.fonts].map((f) => f.family + ':' + f.status),
  width_print: m('"Chronicle Print"'),
  width_hand: m('"Chronicle Hand"'),
  width_fallback: m('serif'),
  latin_print: n('"Chronicle Print"'),
  latin_hand: n('"Chronicle Hand"'),
  window: {w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio},
  doc_scrolls: document.documentElement.scrollHeight > window.innerHeight + 1
  });
})()
"""

PROBE_FIT = """
(() => {
  const col = document.querySelector('.text-column');
  const leaf = document.querySelector('.leaf');
  const page = document.querySelector(`[data-page="${state.page}"]`);
  const r = leaf.getBoundingClientRect();
  return JSON.stringify({
    page: state.page,
    fit_zoom: page ? (page.style.zoom || '1') : null,
    column_overflows: col.scrollHeight > col.clientHeight + 1,
    leaf_within_window: r.bottom <= window.innerHeight + 1 && r.right <= window.innerWidth + 1,
    leaf: {w: Math.round(r.width), h: Math.round(r.height)},
    win: {w: window.innerWidth, h: window.innerHeight},
    overset: document.documentElement.dataset.overset || 'false'
  });
})()
"""

# The blank-canvas question, answered numerically: sample the surface's own
# pixels. A canvas that failed to paint returns one colour; a painted strata
# frame returns many, and a measurable share of pixels differ from the corner.
PROBE_CANVAS = """
(() => {
  const c = document.querySelector('#surface');
  const ctx = c.getContext('2d');
  const px = ctx.getImageData(0, 0, c.width, c.height).data;
  const corner = [px[0], px[1], px[2]];
  const seen = new Set();
  let sampled = 0, different = 0;
  for (let i = 0; i < px.length; i += 4 * 331) {
    sampled++;
    const key = (px[i] >> 3) + ',' + (px[i+1] >> 3) + ',' + (px[i+2] >> 3);
    seen.add(key);
    if (Math.abs(px[i]-corner[0]) + Math.abs(px[i+1]-corner[1]) + Math.abs(px[i+2]-corner[2]) > 12) different++;
  }
  return JSON.stringify({
    css: {w: c.clientWidth, h: c.clientHeight},
    backing: {w: c.width, h: c.height},
    sampled, colours: seen.size,
    ink_ratio: Math.round(1000 * different / sampled) / 1000,
    surface_mode: document.documentElement.dataset.surface || null,
    turn_hidden: document.querySelector('#surface-turn').hidden,
    rebirth_line: document.querySelector('#surface-rebirth').hidden
      ? null : document.querySelector('#surface-rebirth').textContent
  });
})()
"""


def run(window):
    time.sleep(4.5)  # bridge handshake + font loading
    js(window, FORCE_FONTS)
    time.sleep(1.5)
    boot = json.loads(note("boot", js(window, PROBE_BOOT)))
    check("bridge is live (real engine, not SAMPLE)", boot["live"] is True)
    check(
        "both bundled faces loaded",
        boot["fonts_loaded"]["print"] and boot["fonts_loaded"]["hand"],
        str(boot["fonts_loaded"]),
    )
    check(
        "both @font-face rules resolved to the bundled files",
        sorted(boot["faces"]) == ["Chronicle Hand:loaded", "Chronicle Print:loaded"],
        str(boot["faces"]),
    )
    check(
        "the two faces really differ (not one fallback twice)",
        boot["latin_print"] != boot["latin_hand"]
        and boot["width_hand"] != boot["width_fallback"],
        f"latin print={boot['latin_print']} hand={boot['latin_hand']}; "
        f"cjk hand={boot['width_hand']} fallback={boot['width_fallback']}",
    )
    check(
        "window is the supported viewport",
        boot["window"]["w"] >= 900 and boot["window"]["h"] >= 700,
        str(boot["window"]),
    )
    check("the desk does not scroll", not boot["doc_scrolls"])
    shot("01-shelf")

    print("== P-04 opening ==", flush=True)
    js(window, "document.querySelector('.shelf [data-verb=turn]').click()")
    time.sleep(3.0)  # the real engine runs a whole world here
    note(
        "opening_place",
        js(window, "document.querySelector('#opening-place').textContent"),
    )
    note(
        "opening_line",
        js(window, "document.querySelector('#opening-line').textContent"),
    )
    shot("02-opening")

    print("== P-06 juncture ==", flush=True)
    js(window, "document.querySelector('.opening [data-verb=turn]').click()")
    time.sleep(1.2)
    note(
        "running_head",
        js(window, "document.querySelector('#running-head').textContent"),
    )
    note(
        "juncture_head",
        js(window, "document.querySelector('#juncture-head').textContent"),
    )
    opts = note(
        "options",
        js(
            window,
            "JSON.stringify([...document.querySelectorAll('.option-label')].map(e=>e.textContent))",
        ),
    )
    fit = json.loads(note("fit_juncture", js(window, PROBE_FIT)))
    check("the juncture page fits the leaf", not fit["column_overflows"], str(fit))
    check("the leaf fits the window", fit["leaf_within_window"], str(fit["leaf"]))
    check("the juncture offers real options", len(json.loads(opts)) >= 2)
    shot("03-juncture")

    print("== I-04 seal -> the Time Surface ==", flush=True)
    js(window, "document.querySelectorAll('.option')[0].click()")
    time.sleep(0.4)
    shot("04-selected")
    t0 = time.time()
    js(window, "document.querySelector('#seal-btn').click()")
    time.sleep(2.0)

    # I-2: the act enters the entry before the years run.
    entry = json.loads(
        note(
            "entry",
            js(
                window,
                "JSON.stringify({page: state.page, life: state.entryLife, "
                "acts: [...document.querySelectorAll('.act-line')].map(e=>e.textContent), "
                "cues: document.querySelectorAll('.plant-cue').length, "
                "marks: document.querySelectorAll('.act-mark').length, "
                "arriving: document.querySelectorAll('.act.arriving').length, "
                "mark_box: (() => { const m = document.querySelector('.act-mark'); if (!m) return null; "
                "const r = m.getBoundingClientRect(), cs = getComputedStyle(m), "
                "col = document.querySelector('.text-column').getBoundingClientRect(), "
                "leaf = document.querySelector('.leaf').getBoundingClientRect(); "
                "return {x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height), "
                "opacity: cs.opacity, colour: cs.color, "
                "left_of_measure: r.right <= col.left + 1, inside_leaf: r.left >= leaf.left}; })(), "
                "planted: state.stream.beats.filter(b => b.t === 'outcome').slice(0, state.cursor)"
                ".filter(b => b.life === state.entryLife && b.planted > 0).length, "
                "acts_ahead: state.stream.beats.filter(b => b.t === 'outcome' && b.life === state.entryLife).length})",
            ),
        )
    )
    check("the act enters the entry (P-05/P-07)", entry["page"] == "entry", str(entry))
    check(
        "the entry holds this life's acts", len(entry["acts"]) >= 1, str(entry["acts"])
    )
    check("exactly one act is arriving", entry["arriving"] == 1, str(entry["arriving"]))
    check(
        "the entry does not write ahead of its reader",
        len(entry["acts"]) <= entry["acts_ahead"]
        and len(entry["acts"]) == entry["cues"],
        f"shown={len(entry['acts'])} this life will take={entry['acts_ahead']}",
    )
    check(
        "the plant cue matches the data, one for one",
        entry["cues"] == entry["planted"] and entry["marks"] == entry["planted"],
        f"cues={entry['cues']} marks={entry['marks']} planted={entry['planted']}",
    )
    box = entry["mark_box"]
    check(
        "the plant mark sits in the margin, not in the measure (D-4 M-2)",
        bool(box)
        and box["left_of_measure"]
        and box["inside_leaf"]
        and box["opacity"] == "1",
        str(box),
    )
    check(
        "the sealed juncture cannot be answered twice",
        js(
            window,
            "(() => { const c = state.cursor; seal(); return state.cursor === c; })()",
        ),
    )
    shot("04b-entry")

    # A life can be asked more than once (seeds 7 and 123 ask life 1 twice), and
    # then the entry hands back to another juncture rather than to the years.
    # Seal through the rest of the life until the surface takes the screen.
    js(window, "document.querySelector('#entry-turn').click()")
    time.sleep(1.2)
    for _ in range(6):
        if js(window, "document.documentElement.dataset.surface === 'time'"):
            break
        if js(window, "state.page !== 'juncture'"):
            break
        js(window, "document.querySelectorAll('.option')[0].click()")
        time.sleep(0.4)
        js(window, "document.querySelector('#seal-btn').click()")
        time.sleep(2.0)
        acts = js(window, "document.querySelectorAll('.act-line').length")
        note("entry_acts_after_next_seal", acts)
        js(window, "document.querySelector('#entry-turn').click()")
        time.sleep(1.2)
    check(
        "the years follow the life's last act",
        js(window, "document.documentElement.dataset.surface === 'time'"),
    )
    t0 = time.time()

    # SURFACE_MS = 14000; the cut is death .00-.14 / years .14-.47 /
    # aftermath .47-.70 / rebirth .70-.80.
    beats = [
        ("05-surface-death", 2.0),
        ("06-surface-years", 5.0),
        ("07-surface-aftermath", 9.0),
        ("08-surface-rebirth", 12.5),
    ]
    frames = []
    for name, at in beats:
        time.sleep(max(0.0, (t0 + at) - time.time()))
        frames.append((name, json.loads(js(window, PROBE_CANVAS))))
        note(name, json.dumps(frames[-1][1], ensure_ascii=False))
        shot(name)

    check("the surface took the screen", frames[0][1]["surface_mode"] == "time")
    for name, f in frames:
        check(
            f"canvas is painted at {name}",
            f["ink_ratio"] > 0.02 and f["colours"] > 4,
            f"ink={f['ink_ratio']} colours={f['colours']}",
        )
    check(
        "the strata accumulate as the years run",
        frames[2][1]["ink_ratio"] >= frames[0][1]["ink_ratio"],
        f"{frames[0][1]['ink_ratio']} -> {frames[2][1]['ink_ratio']}",
    )
    check(
        "the canvas backing store is real",
        frames[0][1]["backing"]["w"] > 0 and frames[0][1]["css"]["w"] > 0,
        str(frames[0][1]),
    )

    time.sleep(max(0.0, (t0 + 15.0) - time.time()))
    settled = json.loads(note("09-surface-settled", js(window, PROBE_CANVAS)))
    check(
        "the years hand the page back",
        settled["turn_hidden"] is False,
        str(settled["turn_hidden"]),
    )
    check(
        "the next life is announced",
        bool(settled["rebirth_line"]),
        str(settled["rebirth_line"]),
    )
    shot("09-surface-settled")

    # I-3: P-10 sits between the years and the life they lead to. It is the
    # standard world's guaranteed first recognition (SP-1), so the gate has to
    # see it on real hardware and not merely in the stream.
    print("== the rebirth digest ==", flush=True)
    js(window, "document.querySelector('#surface-turn').click()")
    time.sleep(1.2)
    digest = json.loads(
        note(
            "digest",
            js(
                window,
                "JSON.stringify({page: state.page, life: state.lifeShown, "
                "surface: document.documentElement.dataset.surface || null, "
                "lines: [...document.querySelectorAll('.change-line')].map(e=>e.textContent), "
                "marks: document.querySelectorAll('.change-mark').length, "
                "sealed_rows: document.querySelectorAll('.change.sealed').length, "
                "eyebrow: document.querySelector('[data-page=\"digest\"] .eyebrow').textContent, "
                "mark_box: (() => { const m = document.querySelector('.change-mark'); if (!m) return null; "
                "const r = m.getBoundingClientRect(), cs = getComputedStyle(m), "
                "col = document.querySelector('.text-column').getBoundingClientRect(), "
                "leaf = document.querySelector('.leaf').getBoundingClientRect(); "
                "return {x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height), "
                "opacity: cs.opacity, colour: cs.color, "
                "left_of_measure: r.right <= col.left + 1, inside_leaf: r.left >= leaf.left}; })(), "
                "stream_changes: state.win.aftermath.changes.map(c => c.act + ' | ' + c.consequence), "
                "stream_sealed: state.win.aftermath.changes.filter(c => c.sealed).length})",
            ),
        )
    )
    check(
        "the years hand to the digest (P-10)", digest["page"] == "digest", str(digest)
    )
    check("the surface let go of the screen", digest["surface"] is None)
    check(
        "the digest still names the life just buried, not the next one",
        digest["life"] == 1,
        str(digest["life"]),
    )
    check(
        "the digest renders the stream's lines, in the stream's order",
        [ln.rsplit(" \u2014 ", 1)[0] for ln in digest["lines"]]
        == [c.split(" | ")[0] for c in digest["stream_changes"]],
        f"page={digest['lines']} stream={digest['stream_changes']}",
    )
    check(
        "the digest delivers at most three (UX \u00a7P-10)",
        1 <= len(digest["lines"]) <= 3,
        str(len(digest["lines"])),
    )
    check(
        "SP-1: the first digest delivers an act the player sealed",
        digest["stream_sealed"] >= 1
        and digest["sealed_rows"] == digest["stream_sealed"],
        f"rows={digest['sealed_rows']} stream={digest['stream_sealed']}",
    )
    check(
        "every digest line carries the echo mark, in the margin (D-4 M-2)",
        digest["marks"] == len(digest["lines"])
        and bool(digest["mark_box"])
        and digest["mark_box"]["left_of_measure"]
        and digest["mark_box"]["inside_leaf"],
        str(digest["mark_box"]),
    )
    check(
        "no digest line prints a number",
        not any(ch.isdigit() for ln in digest["lines"] for ch in ln),
        str(digest["lines"]),
    )
    fit_digest = json.loads(note("fit_digest", js(window, PROBE_FIT)))
    check(
        "the digest fits the leaf",
        not fit_digest["column_overflows"] and fit_digest["overset"] == "false",
        str(fit_digest),
    )
    shot("09b-digest")

    print("== the next life ==", flush=True)
    js(
        window,
        'document.querySelector(\'[data-page="digest"] [data-verb="turn"]\').click()',
    )
    time.sleep(1.2)
    after = note(
        "after_turn",
        js(
            window,
            "JSON.stringify({page: state.page, life: state.lifeShown, "
            "surface: document.documentElement.dataset.surface || null, "
            "life2_has_juncture: state.stream.beats.some(b => b.t === 'juncture' && b.life === 2), "
            "head: document.querySelector('#juncture-head').textContent})",
        ),
    )
    after = json.loads(after)
    check("the book advanced to the next life", after["life"] == 2, str(after))
    # A life the world never asks anything of has no leaf page — it gets its own
    # window instead, and the surface is RIGHT to still hold the screen (B-1).
    if after["life2_has_juncture"]:
        check("the surface let go for a life with a juncture", after["surface"] is None)
    else:
        check(
            "a life with no juncture still gets its own window",
            after["surface"] == "time",
            "life 2 is never asked anything in this seed",
        )
    shot("10-next-life")

    with open(f"{SHOTS}/{TAG}-notes.json", "w", encoding="utf-8") as fh:
        json.dump(
            {"seed": SEED, "notes": dict(NOTES), "failures": FAILURES},
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print(f"== done: {len(FAILURES)} failure(s) {FAILURES} ==", flush=True)
    time.sleep(0.5)
    window.destroy()


win = webview.create_window(
    "Chronicle Forge — The Living Chronicle",
    url=_index_html(),
    js_api=BookBridge(seed=SEED),
    width=1180,
    height=880,
    text_select=False,
)
threading.Thread(target=lambda: run(win), daemon=True).start()
webview.start(gui="qt")
