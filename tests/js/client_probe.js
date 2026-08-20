/* Probe for the frontend's two non-visual contracts, run under node by
   tests/test_client_bridge.py. It loads the SHIPPED strings.js and time.js —
   neither touches the DOM — and answers questions about them as JSON on stdout.
   book.js is not loaded (it needs a document); the walk below reproduces its
   navigation rule, and the test asserts separately that book.js still states it.

       node client_probe.js <stream.json>
*/

"use strict";

const fs = require("fs");
global.window = {};

// `eval` is how a browser IIFE (`window.X = ...`) is loaded into node without a
// bundler, and that is the point: this must exercise the SHIPPED files, not a
// copy. The inputs are two source files inside this repo, never user data.
const WEB = process.env.CF_WEB;
eval(fs.readFileSync(WEB + "/strings.js", "utf8"));
eval(fs.readFileSync(WEB + "/time.js", "utf8"));
const TS = window.TimeSurface;
const V = window.CF_VOICE;

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const junctures = D.beats.filter((b) => b.t === "juncture");

/* ---- 1. the walk: advanceTo(lifeShown + 1), one life at a time ---- */
const walk = [];
let cursor = 0;
for (let life = 1, guard = 0; guard < 500; guard++) {
  const next = junctures[cursor];
  if (next && next.life === life) {
    walk.push({ page: "juncture", life, beatLife: next.life });
    cursor++;
    continue;
  }
  const win = TS.pickWindow(D, life);
  if (!win) break;
  walk.push({
    page: "surface",
    life,
    beatLife: win.death.life,
    register: TS.register(win),
    rebirth: win.rebirth ? win.rebirth.life : null,
  });
  if (!win.rebirth) break;
  life += 1;
}

/* ---- 2. the strata scale must not read the future ----
   A recording 2D context: the band polygons are the only geometry compared, so
   only the path calls need to be real. Draw the same window twice — once
   against the stream as it is, once against a stream with extra `years` beats
   bolted on after it — and the two must be identical. */
function recorder() {
  const ops = [];
  const grad = { addColorStop() {} };
  const ctx = {
    canvas: { width: TS.W, height: TS.H },
    globalAlpha: 1, fillStyle: "", strokeStyle: "", lineWidth: 1, font: "",
    textAlign: "left", textBaseline: "alphabetic",
    save() {}, restore() {}, beginPath() { ops.push("bp"); },
    closePath() {}, fill() {}, stroke() {}, setLineDash() {},
    translate() {}, scale() {}, setTransform() {}, arc() {},
    moveTo(x, y) { ops.push(["m", Math.round(x * 100), Math.round(y * 100)]); },
    lineTo(x, y) { ops.push(["l", Math.round(x * 100), Math.round(y * 100)]); },
    fillRect() {}, fillText() {},
    createLinearGradient: () => grad, createRadialGradient: () => grad,
    measureText: (s) => ({ width: s.length * 8 }),
  };
  return { ctx, ops };
}

function geometry(data, win, t) {
  const r = recorder();
  TS.draw(r.ctx, data, win, t);
  return JSON.stringify(r.ops);
}

// the first window that has a life after it, so there IS a future to add to
const firstLife = walk.length ? walk[0].life : 1;
const win = TS.pickWindow(D, firstLife);
let scaleStable = null;
if (win) {
  const futured = JSON.parse(JSON.stringify(D));
  const lastLife = D.lives[D.lives.length - 1].ordinal;
  // a louder future than any measured world, attributed to the LAST life so it
  // can only ever stack above the window being drawn
  futured.beats.push({
    t: "years", after_life: lastLife, from_year: D.max_year, to_year: D.max_year,
    span: 0, world_ended: false,
    events: Array.from({ length: 240 }, (_, i) => ({
      year: D.max_year, scale: "small", phrase: "x", owners: [lastLife],
    })),
  });
  scaleStable = geometry(D, win, 0.62) === geometry(futured, win, 0.62);
}

/* ---- 3. captions and reveal copy, including the optional planted year ---- */
const S = V.strings;
const sealedWin = D.beats.some((b) => b.t === "aftermath" && b.hardened.length)
  ? TS.pickWindow(D, D.beats.find((b) => b.t === "aftermath" && b.hardened.length).after_life)
  : null;

process.stdout.write(JSON.stringify({
  lives: D.lives.map((l) => l.ordinal),
  walk,
  scaleStable,
  captions: {
    death: S.surfaceDeath(1, 22),
    sealedWithYear: S.surfaceSealed(2, 7),
    sealedWithoutYear: S.surfaceSealed(2, null),
    realSealed: sealedWin ? TS.caption(sealedWin, 0.62) : null,
  },
  reveal: {
    bloomWithYear: S.handBloom(3),
    bloomWithoutYear: S.handBloom(null),
    confirm: S.handConfirm(2, "scholar"),
  },
  closing: S.closingLine(40, 4, "Imperial Age"),
  epithets: [1, 2, 3, 4, 11].map((n) => V.epithet(n)),
}));
