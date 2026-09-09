/* The Living Chronicle — frontend.
   Pages: shelf -> opening -> juncture -> the Time Surface -> the next juncture.
   Verbs: turn / flip / seal / hold.

   I-1b: this file no longer reads the game out of prose. It receives the typed
   beat stream (play/beats.py) from the bridge and reads fields. That is what
   makes the death / years / aftermath / rebirth beats renderable at all — the
   old regex seam could recover the juncture and nothing else — and it is also
   what keeps the page honest: a mark is drawn only where the stream carries a
   `recognition`, and the Time Surface's 朱 seals are exactly the `hardened`
   marks of that aftermath. With no data there is nothing to draw, and the page
   draws nothing rather than something plausible.

   Data comes from window.pywebview.api; with no bridge it falls back to SAMPLE
   data so the page previews standalone (stamped 見本, never mistakable for a
   world). window.CF_BEATS, when present, is a real stream injected by the
   offline capture harness.
   Determinism: no Math.random(), no Date/clock-derived styling or copy; the
   surface clock can be frozen with ?t= so a captured frame is reproducible. */

"use strict";

// Every word this page writes itself lives in strings.js — including the two
// English sentences it composes from stream fields, which used to be inline
// here and so escaped the inventory. Engine/world-supplied text (labels, kinds,
// place names, legacy names, event phrases, talents) is never translated: it is
// printed exactly as the stream returns it.
const STRINGS = window.CF_VOICE.strings;

const HOLD_MS = 800;
const PAGES = ["shelf", "opening", "juncture", "entry", "digest"];
// The surface plays 0 -> TimeSurface.REBIRTH_END; the last stretch of the cut
// is the real juncture page, not a picture of one.
const SURFACE_MS = 14000;

/* ---- SAMPLE: standalone-preview fallback only ----------------------------
   A hand-written stream in the real shape, deliberately tiny and deliberately
   labelled. It exists so `index.html` opened in a bare browser still shows the
   machine working; it is stamped 見本 and can never reach a live window. */
const SAMPLE = {
  seed: 0, place: "the Salt Kingdoms", max_year: 40, end_year: 40, ending: "Imperial Age",
  lives: [
    { ordinal: 1, talent: "smith", birth_year: 0, death_year: 6 },
    { ordinal: 2, talent: "scribe", birth_year: 14, death_year: 20 },
  ],
  beats: [
    { t: "rebirth", life: 1, year: 0, talent: "smith", era: "an age of salt" },
    { t: "juncture", life: 1, year: 3, age: 14, reason: "floor", header: "The world turns to you", era: "an age of salt",
      options: [
        { n: 1, label: "Open the hill's undercroft", kind: "Place", why: "the water is failing", heritage_id: null },
        { n: 2, label: "Hold the old road's toll", kind: "Faction", why: "tension rising", heritage_id: null },
        { n: 3, label: "Walk to the assembly", kind: "Person", why: "an ally awaits", heritage_id: null },
      ], recognition: null },
    { t: "death", life: 1, year: 6, age: 22, talent: "smith", title: "the smith of the Salt Kingdoms",
      named: [], pending: 3, seed_years: [1, 3] },
    { t: "years", after_life: 1, from_year: 6, to_year: 14, span: 8, world_ended: false,
      events: [
        { year: 7, scale: "small", phrase: "a road was cut", owners: [1] },
        { year: 9, scale: "large", phrase: "a levee was raised", owners: [1] },
        { year: 12, scale: "small", phrase: "a market opened", owners: [1] },
      ] },
    { t: "aftermath", after_life: 1, year: 14,
      echoes: [{ year: 9, scale: "large", phrase: "a levee was raised", owners: [1] }], hardened: [],
      changes: [
        { act: "Open the hill's undercroft", sealed: true, consequence: "a levee was raised", times: 1, first_year: 9 },
        { act: "cut a road", sealed: false, consequence: "a market opened", times: 1, first_year: 12 },
      ] },
    { t: "rebirth", life: 2, year: 14, talent: "scribe", era: "an age of salt" },
    { t: "juncture", life: 2, year: 16, age: 18, reason: "history", header: "History remembers", era: "an age of salt",
      options: [
        { n: 1, label: "Tend the Order of the Open Road", kind: "Legacy", why: "your past pulls here", heritage_id: "h-sample" },
        { n: 2, label: "Petition the drowned court", kind: "Faction", why: "long neglected", heritage_id: null },
        { n: 3, label: "Say nothing", kind: "Person", why: "tension rising", heritage_id: null },
      ],
      recognition: { option: 1, name: "Order of the Open Road", founder_life: 1, founder_talent: "smith", planted_year: 1, reach: 22 } },
    { t: "closing", year: 40, lives: 2, ending: "Imperial Age", legacies: [] },
  ],
};

let holdConsumedClick = false; // a completed pointer hold swallows its own click

const $ = (sel, root = document) => root.querySelector(sel);

/* ---- bridge handshake (T3 B-1) ----
   pywebview injects `window.pywebview.api` asynchronously, and whether the
   `pywebviewready` event has already fired by the time this script runs is a
   race. We WAIT for the api — event and poll, whichever wins — and only then
   decide live-vs-SAMPLE. Nothing is rendered before the decision. */
const BRIDGE_WAIT_MS = 5000;
const NO_HOST_GRACE_MS = 800;

const apiReady = () =>
  !!(window.pywebview && window.pywebview.api && typeof window.pywebview.api.shelf === "function");

function waitForBridge() {
  return new Promise((resolve) => {
    if (apiReady()) return resolve(true);
    const started = performance.now();
    let settled = false;
    const finish = (live) => {
      if (settled) return;
      settled = true;
      clearInterval(poll);
      window.removeEventListener("pywebviewready", onReady);
      resolve(live);
    };
    const onReady = () => apiReady() && finish(true);
    window.addEventListener("pywebviewready", onReady);
    const poll = setInterval(() => {
      const waited = performance.now() - started;
      const deadline = window.pywebview ? BRIDGE_WAIT_MS : NO_HOST_GRACE_MS;
      if (apiReady()) finish(true);
      else if (waited > deadline) finish(false);
    }, 40);
  });
}

let state = {
  page: "shelf",
  live: false,      // set once by the handshake; never guessed at call time
  stream: null,     // the typed beat stream for the run so far
  juncture: null,   // the juncture beat currently on the page
  lifeShown: 0,     // which life's opening/juncture the book is on
  cursor: 0,        // index into the stream's junctures — one seal, one juncture
  choices: [],      // the displayed numbers sealed so far, in order
  selected: null,
  sealed: false,
  revealed: new Set(),
  win: null,        // the death/years/aftermath window the surface is playing
  entryLife: 0,     // whose entry the acts on the page belong to
  frozenT: null,    // ?t= — a frozen surface clock, for reproducible captures
};

function setStatus(t) { $("#status").textContent = t; }
function setRunningHead(text) { $("#running-head").textContent = text || ""; }
function setFolio(page) { $("#folio").textContent = String(PAGES.indexOf(page) + 1); }

function applyStrings() {
  for (const el of document.querySelectorAll("[data-str]")) {
    const key = el.dataset.str;
    // Only the plain entries are page furniture; the composed lines take stream
    // fields and are written by the code that has them.
    if (typeof STRINGS[key] === "string") el.textContent = STRINGS[key];
  }
}

/* ---- reading the stream (field access only — no parsing of prose) ---- */
const beatsOf = (kind) => (state.stream ? state.stream.beats.filter((b) => b.t === kind) : []);
const firstBeat = (kind, life) =>
  (state.stream ? state.stream.beats : []).find((b) => b.t === kind && (life === undefined || b.life === life)) || null;
// The player answers junctures in stream order, one seal per juncture, so the
// cursor and `state.choices` stay the same length — a choice is applied to the
// juncture it was made at and to no other.
const junctures = () => beatsOf("juncture");

/* ---- fit the page to the leaf (T3 B-2) ---- */
const FIT_STEPS = [1, 0.94, 0.88, 0.82, 0.76, 0.7];
let fontsReady = false;

function scheduleFit() {
  if (!fontsReady) return;
  requestAnimationFrame(() => requestAnimationFrame(fitPage));
}

function fitPage() {
  const col = $(".text-column");
  const page = document.querySelector(`[data-page="${state.page}"]`);
  if (!col || !page) return 1;
  for (const step of FIT_STEPS) {
    page.style.zoom = step === 1 ? "" : String(step);
    if (col.scrollHeight <= col.clientHeight + 1) {
      delete document.documentElement.dataset.overset;
      return step;
    }
  }
  document.documentElement.dataset.overset = "true";
  console.warn("page is overset: content exceeds one leaf at the legibility floor");
  return FIT_STEPS[FIT_STEPS.length - 1];
}

function show(page, direction = "forward") {
  hideSurface();
  state.page = page;
  for (const p of PAGES) {
    const el = document.querySelector(`[data-page="${p}"]`);
    if (!el) continue;
    if (p === page) {
      el.classList.remove("turn-forward", "turn-back");
      el.hidden = false;
      state.page = page;
      fitPage();
      void el.offsetWidth; // reflow: re-turning to the same page replays the turn
      el.classList.add(direction === "back" ? "turn-back" : "turn-forward");
    } else {
      el.hidden = true;
      el.style.zoom = "";
    }
  }
  setFolio(page);
}

// In SAMPLE mode this returns null and the caller uses the fixture. In LIVE
// mode a failure is never papered over with fixture data — the page says so
// instead. A book may be missing a page; it may not quietly print a fake one.
async function bridge(method, ...args) {
  if (!state.live) return null;
  const a = window.pywebview.api;
  if (typeof a[method] !== "function") throw new Error(`bridge method missing: ${method}`);
  return await a[method](...args);
}

function bridgeFailed(where, err) {
  console.error("bridge failure:", where, err);
  setStatus(STRINGS.statusBridgeError);
  $("#running-head").textContent = "";
  $("#juncture-head").textContent = STRINGS.bridgeErrorLine;
  $("#options").innerHTML = "";
}

/* ---- pages ---- */

async function loadStream(choices) {
  if (!state.live) return window.CF_BEATS || SAMPLE;
  return await bridge("play", null, choices);
}

async function toOpening() {
  try {
    state.stream = await loadStream(state.choices);
  } catch (err) {
    show("opening", "forward");
    return bridgeFailed("play", err);
  }
  state.lifeShown = 1;
  state.cursor = 0;
  paintOpening(firstBeat("rebirth", 1));
  show("opening", "forward");
  setStatus(state.live ? `seed ${state.stream.seed} · ${state.stream.place}` : STRINGS.statusPreview);
}

// The opening prints only what the rebirth beat carries: the world's name, the
// life's ordinal, the talent it was given, and the age it was born into.
function paintOpening(rebirth) {
  const place = state.stream.place;
  $("#opening-place").textContent = place;
  $("#opening-line").textContent = STRINGS.openingLine(
    place,
    rebirth ? rebirth.talent : null,
    rebirth ? rebirth.era : null
  );
  setRunningHead(place);
}

/* ---- advancing the book, ONE LIFE AT A TIME -------------------------------
   The book used to walk the stream by juncture index: seal, then jump to
   `junctures()[cursor]`. A life the world never asked anything of has no
   juncture, so that walk stepped straight over it — the surface said "you are
   born again" as that life, and the page it turned to belonged to the life
   AFTER it (seed 99, life 2). Its death, its years and its aftermath — its
   hardened marks included — were unreachable, and the page named a life it was
   not showing.

   Lives are consecutive and every one of them has a death → years → aftermath
   in the stream, so advancing by ordinal is total: a life is either asked
   something (its juncture) or simply lived and died (its window). Nothing is
   skipped and the page never names a life it is not on. */
function advanceTo(life) {
  const next = junctures()[state.cursor];
  if (next && next.life === life) {
    hideSurface();
    state.lifeShown = life;
    paintOpening(firstBeat("rebirth", life));
    return toJuncture(next);
  }
  const win = TimeSurface.pickWindow(state.stream, life);
  if (!win) return false; // no such life: the world is over
  state.lifeShown = life;
  state.win = win;
  playSurface(win);
  return true;
}

/* ---- P-05 the entry, P-07 the act arriving in it ---------------------------
   One page in two moments: the acts this life has taken, and the newest one
   entering. Everything on it is an `outcome` beat — the label is the engine's
   own words for the act, and `planted` is a count read off the world the moment
   the verb ran. The page composes nothing it was not handed. */

/* The acts of this life the player has actually REACHED.

   Sealing replays the whole world, so the stream always runs to the world's
   end: `beatsOf("outcome")` contains acts from later in this very life that the
   player has not come to yet, and printing them into the entry would be the
   book writing ahead of its reader. An outcome is emitted in the same breath as
   the juncture it answers, one for one and in order, so the acts reached are
   exactly the first `state.cursor` of them — the same count as seals made. */
function outcomesOf(life) {
  return beatsOf("outcome")
    .slice(0, state.cursor)
    .filter((b) => b.life === life);
}

function buildAct(act, arriving) {
  const li = document.createElement("li");
  li.className = "act print" + (arriving ? " arriving" : "");
  li.dataset.year = String(act.year);

  const line = document.createElement("p");
  line.className = "act-line";
  // Option 0 is the season let pass: the world answered, and the entry says so
  // rather than crediting the player with an act they did not choose.
  line.textContent = act.option === 0
    ? STRINGS.passLine(act.year)
    : STRINGS.actLine(act.year, act.label);
  li.appendChild(line);

  // S-03. The cue is drawn only where the stream says something was planted;
  // an act that set nothing in motion gets no promise. ⟜ is the echo mark
  // (ADR-001 K-1) — the same glyph a past echo carries, which is the point:
  // the promise is addressed to the self who will find it.
  if (act.planted > 0) {
    const mark = document.createElement("span");
    mark.className = "act-mark";
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = "⟜";
    li.appendChild(mark);
    const cue = document.createElement("p");
    cue.className = "plant-cue print";
    cue.textContent = STRINGS.plantCue;
    li.appendChild(cue);
  }
  return li;
}

function toEntry(life) {
  const acts = outcomesOf(life);
  if (!acts.length) return false;
  hideSurface();
  state.entryLife = life;
  state.lifeShown = life;
  const list = $("#acts");
  list.innerHTML = "";
  acts.forEach((act, i) => list.appendChild(buildAct(act, i === acts.length - 1)));
  const last = acts[acts.length - 1];
  $("#entry-turn").hidden = false;
  setRunningHead(`Year ${last.year} · age ${last.age}`);
  setStatus(STRINGS.statusWriting);
  show("entry", "forward");
  return true;
}

/* What follows the entry: this life's next juncture if the world asks again,
   otherwise the years. The world ending with this life is the third case — no
   years run after it, so the ink simply sets. */
function leaveEntry() {
  const next = junctures()[state.cursor];
  if (next && next.life === state.lifeShown) return toJuncture(next);
  const win = TimeSurface.pickWindow(state.stream, state.lifeShown);
  if (!win) {
    const closed = document.createElement("li");
    closed.className = "act print closed";
    closed.textContent = STRINGS.inkSets;
    $("#acts").appendChild(closed);
    $("#entry-turn").hidden = true;
    return scheduleFit();
  }
  state.win = win;
  playSurface(win);
}

/* ---- P-10 the rebirth digest ------------------------------------------------
   The page between a life and the next one: what the years just shown did with
   the acts of the life that just ended.

   Everything on it is `aftermath.changes`, which the stream has already
   grouped, ordered and cut to three. The page renders that tuple in the order
   it was handed and does nothing else — it does not rank, does not weigh
   `times`, and never infers which act caused which event. That join is a real
   causal edge in the world, and it is made where the world is (play/beats.py);
   a client that re-derived it would be guessing at causality from strings.

   It reads only `state.win` — the window the surface just played — so it cannot
   show a life the player has not yet buried. */
function toDigest(win) {
  // Fail closed. The digest is addressed to someone who is coming BACK: with no
  // rebirth the world has ended and there is nowhere to return to, so the
  // surface keeps its last frame and the closing page has the say. An empty
  // `changes` is the same refusal — a heading over nothing is the book claiming
  // the years did something it cannot name. (Measured: the only empty digests
  // in seeds 1-30 are terminal, so this is a guard, not a code path.)
  if (!win || !win.rebirth || !win.aftermath.changes.length) return false;
  hideSurface();
  const list = $("#changes");
  list.innerHTML = "";
  for (const change of win.aftermath.changes) {
    const li = document.createElement("li");
    // `sealed` is a stream field, not a judgement made here: it marks the lines
    // whose act the player chose themselves, in the words they read it in.
    li.className = "change print" + (change.sealed ? " sealed" : "");

    // ⟜, the echo mark (ADR-001 K-1). Every line here IS an echo — something
    // the player left, coming back — so every line carries it and no second
    // glyph is invented to rank them.
    const mark = document.createElement("span");
    mark.className = "change-mark";
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = "⟜";
    li.appendChild(mark);

    const line = document.createElement("p");
    line.className = "change-line";
    line.textContent = STRINGS.digestLine(change.act, change.consequence);
    li.appendChild(line);
    list.appendChild(li);
  }
  setRunningHead(`Year ${win.aftermath.year}`);
  setStatus(STRINGS.statusYears);
  show("digest", "forward");
  return true;
}

function toJuncture(beat) {
  const data = beat || junctures()[state.cursor];
  if (!data) return show("opening", "forward");
  state.lifeShown = data.life;
  state.juncture = data;
  $("#juncture-head").textContent = data.header;
  setRunningHead(`Year ${data.year} · age ${data.age} · ${data.era}`);
  const list = $("#options");
  list.innerHTML = "";
  state.selected = null;
  state.sealed = false;
  state.revealed = new Set();
  $("#seal-btn").disabled = true;

  // The mark goes on the ONE line the stream says a former self made, and
  // nowhere else. In a first life there is never such a line, so there is never
  // a mark — the old skeleton marked option 1 unconditionally, which promised a
  // past the world had not lived yet.
  const marked = data.recognition ? data.recognition.option : null;
  for (const opt of data.options) list.appendChild(buildOption(opt, marked === opt.n, data.recognition));
  show("juncture", "forward");
}

function buildOption(opt, isMarked, recognition) {
  const li = document.createElement("li");
  li.className = "option print";
  li.tabIndex = 0;
  li.dataset.index = String(opt.n);

  const label = document.createElement("span");
  label.className = "option-label";
  label.textContent = opt.label;
  li.appendChild(label);

  const kind = document.createElement("span");
  kind.className = "kind";
  kind.textContent = `${opt.kind} · ${opt.why}`;
  li.appendChild(kind);

  const bar = document.createElement("span");
  bar.className = "holdbar";
  bar.setAttribute("aria-hidden", "true");
  li.appendChild(bar);

  li.addEventListener("click", () => {
    // A completed hold ends in a pointerup, which the browser also reports as a
    // click. Remembering is not choosing, so that trailing click must not
    // silently select the line.
    if (holdConsumedClick) { holdConsumedClick = false; return; }
    selectOption(li, opt);
  });
  li.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectOption(li, opt); }
  });

  if (isMarked && recognition) {
    // The mark lives in the margin stage (S3), never inside the option box, and
    // is never explained on the page (D-02 / K-3).
    const mark = document.createElement("span");
    mark.className = "mark hint";
    mark.textContent = "⟜";
    li.insertBefore(mark, li.firstChild);
    li.title = STRINGS.holdTooltip;

    const hand = document.createElement("div");
    hand.className = "option-hand hand";
    hand.hidden = true;
    const bloom = document.createElement("p");
    bloom.className = "hand-bloom";
    hand.appendChild(bloom);
    li.appendChild(hand);

    const confirm = document.createElement("p");
    confirm.className = "option-confirm hand";
    confirm.hidden = true;
    li.appendChild(confirm);

    wireHold(li, opt, recognition);
  }

  return li;
}

function selectOption(li, opt) {
  if (state.sealed) return;
  for (const el of document.querySelectorAll(".option")) el.classList.remove("selected");
  li.classList.add("selected");
  state.selected = opt.n;
  $("#seal-btn").disabled = false;
}

/* ---- hold-to-remember (I-05) -> in-place S-02 reveal ---- */

function wireHold(li, opt, recognition) {
  const bar = $(".holdbar", li);
  let timer = null, raf = null, start = 0, fromPointer = false;

  const cancel = () => {
    if (timer) clearTimeout(timer);
    if (raf) cancelAnimationFrame(raf);
    timer = raf = null;
    li.classList.remove("holding");
    bar.style.inlineSize = "0";
  };
  const tick = () => {
    const pct = Math.min(1, (performance.now() - start) / HOLD_MS);
    bar.style.inlineSize = (pct * 100) + "%";
    if (pct < 1) raf = requestAnimationFrame(tick);
  };
  const begin = (e) => {
    if (state.sealed || state.revealed.has(opt.n)) return; // permanence: never re-fires
    e.preventDefault();
    fromPointer = e.type === "pointerdown";
    li.classList.add("holding");
    start = performance.now();
    raf = requestAnimationFrame(tick);
    timer = setTimeout(() => {
      holdConsumedClick = fromPointer;
      cancel();
      state.revealed.add(opt.n);
      applyReveal(li, opt, recognition, /* animate */ true);
      setStatus(STRINGS.statusRemembered);
    }, HOLD_MS);
  };

  li.addEventListener("pointerdown", begin);
  li.addEventListener("pointerup", cancel);
  li.addEventListener("pointerleave", cancel);
  li.addEventListener("pointercancel", cancel);
  li.addEventListener("keydown", (e) => { if ((e.key === "r" || e.key === "R") && !e.repeat) begin(e); });
  li.addEventListener("keyup", cancel);
  li.addEventListener("blur", cancel);
}

// S-02 grammar (D-05 / D-3 §3): the print label stays where it is; the Hand
// blooms underneath it; one line names the origin. Every value here is a field
// of `recognition` — the life that founded it and the year it was planted are
// the engine's, not a phrase this file made up.
function applyReveal(li, opt, r, animate) {
  const mark = $(".mark", li);
  const hand = $(".option-hand", li);
  const bloom = $(".hand-bloom", hand);
  const confirm = $(".option-confirm", li);

  bloom.textContent = STRINGS.handBloom(r.planted_year);
  confirm.textContent = STRINGS.handConfirm(r.founder_life, r.founder_talent);

  hand.hidden = false;
  confirm.hidden = false;
  mark.classList.remove("hint");
  mark.classList.add("confirmed");

  // Settle the page BEFORE the bloom starts: a re-fit mid-animation would make
  // the page flinch at the moment the player is meant to be reading.
  fitPage();

  if (animate) {
    hand.classList.add("blooming");
    confirm.classList.add("blooming-confirm");
  }
}

/* ---- the Time Surface (B2 -> B3 -> B4) ------------------------------------
   Sealing a choice replays the world under that choice and hands the surface
   the window that follows this life's death. Nothing on the surface is chosen
   here: the seals ARE `aftermath.hardened`, the specks ARE `years.events`. */

let surfaceRaf = null;

function surfaceCtx() {
  const canvas = $("#surface");
  const ctx = canvas.getContext("2d");
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  if (canvas.width !== TimeSurface.W * dpr) {
    canvas.width = TimeSurface.W * dpr;
    canvas.height = TimeSurface.H * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}

function hideSurface() {
  if (surfaceRaf) { cancelAnimationFrame(surfaceRaf); surfaceRaf = null; }
  const el = $("#time-surface");
  if (el) { el.hidden = true; el.setAttribute("aria-hidden", "true"); }
  document.documentElement.removeAttribute("data-surface");
}

function playSurface(win) {
  const el = $("#time-surface");
  el.hidden = false;
  el.setAttribute("aria-hidden", "false");
  document.documentElement.dataset.surface = "time";
  setRunningHead("");
  setStatus(STRINGS.statusYears);
  const ctx = surfaceCtx();
  const end = TimeSurface.REBIRTH_END;
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const paint = (t) => {
    TimeSurface.draw(ctx, state.stream, win, t);
    const born = TimeSurface.done(t, "rebirth");
    const line = $("#surface-rebirth");
    const tail = tailLine(win);
    if (tail && born > 0) {
      line.hidden = false;
      line.style.opacity = String(Math.min(1, born * 1.6));
      line.textContent = tail;
    } else {
      line.hidden = true;
    }
    // Nothing follows the last life, so the surface keeps the last frame: the
    // strata, full, are the world's whole history and there is no page after
    // it. What decides that is whether a life was BORN after this one, not
    // whether a juncture remains — a life the world asked nothing of still has
    // a page.
    $("#surface-turn").hidden = t < end || !win.rebirth;
  };

  if (state.frozenT !== null) return paint(state.frozenT);
  if (reduced) return paint(end);

  const started = performance.now();
  const frame = (now) => {
    const t = Math.min(end, (now - started) / SURFACE_MS);
    paint(t);
    if (t < end) surfaceRaf = requestAnimationFrame(frame);
    else surfaceRaf = null;
  };
  $("#surface-turn").hidden = true;
  $("#surface-rebirth").hidden = true;
  surfaceRaf = requestAnimationFrame(frame);
}

/* What the surface says once the years have run: the next life if there is one,
   otherwise the closing page's own account of the world. Both are stream data —
   the ending class and the count of lives are the engine's words. */
function tailLine(win) {
  // A rebirth in the stream means there IS a next life to turn to, whether or
  // not the world ever asks it anything.
  if (win.rebirth) {
    return STRINGS.rebornLine(state.stream.place, win.rebirth.talent, win.rebirth.era);
  }
  const closing = beatsOf("closing")[0];
  if (!closing) return "";
  const names = closing.legacies.slice(0, 2).map((l) => l.name).join(" · ");
  return STRINGS.closingLine(closing.year, closing.lives, closing.ending)
    + (names ? `  ${names}` : "");
}

function skipSurface() {
  if (!surfaceRaf) return false;
  cancelAnimationFrame(surfaceRaf);
  surfaceRaf = null;
  TimeSurface.draw(surfaceCtx(), state.stream, state.win, TimeSurface.REBIRTH_END);
  const line = $("#surface-rebirth");
  const tail = tailLine(state.win);
  if (tail) { line.hidden = false; line.style.opacity = "1"; line.textContent = tail; }
  $("#surface-turn").hidden = !state.win.rebirth;
  return true;
}

/* ---- seal (I-04): the sealed option's ink sets, then the years run ---- */

async function seal() {
  if (state.selected == null || state.sealed) return;
  state.sealed = true;
  $("#seal-btn").disabled = true;
  for (const el of document.querySelectorAll(".option")) {
    if (Number(el.dataset.index) === state.selected) el.classList.add("set");
    else el.classList.add("receded");
  }
  const choices = state.choices.concat([state.selected]);
  let stream;
  try {
    stream = state.live ? await bridge("play", null, choices) : (window.CF_BEATS || SAMPLE);
  } catch (err) {
    return bridgeFailed("play", err);
  }
  state.choices = choices;
  state.stream = stream;
  state.cursor += 1;
  setStatus(STRINGS.statusSealed);

  // The act enters the entry (P-07) before anything else moves. What follows
  // the entry — this life's next juncture, the years, or the ink setting — is
  // `leaveEntry`'s decision, made on the same stream.
  return toEntry(state.lifeShown);
}

/* ---- verbs / wiring ---- */

function turn() {
  if (document.documentElement.dataset.surface === "time") {
    if (skipSurface()) return;      // still running: finish it, do not skip past it
    // P-10 goes between the years and the life they lead to; when there is no
    // digest to deliver the surface hands straight on, exactly as it used to.
    if (toDigest(state.win)) return;
    // The next LIFE, not the next juncture — see advanceTo.
    return advanceTo(state.lifeShown + 1);
  }
  if (state.page === "shelf") return toOpening();
  if (state.page === "entry") return leaveEntry();
  if (state.page === "digest") return advanceTo(state.lifeShown + 1);
  // The opening belongs to a life; what follows is that life's own page, which
  // is its juncture if it has one and its window if the world never asked it
  // anything.
  if (state.page === "opening") return advanceTo(state.lifeShown);
}
function flip() {
  if (document.documentElement.dataset.surface === "time") return; // the years do not run backwards
  if (state.page === "entry") return;   // the entry has no way back — see index.html
  if (state.page === "digest") return; // nor does the digest: the years are spent
  if (state.page === "juncture") return show("opening", "back");
  if (state.page === "opening") return show("shelf", "back");
}

function wireVerbs() {
  document.addEventListener("click", (e) => {
    const v = e.target.closest("[data-verb]");
    if (!v) return;
    ({ turn, flip, seal }[v.dataset.verb] || (() => {}))();
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest(".option")) return; // hold key handled per-option
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowRight") { turn(); }
    else if (e.key === "ArrowLeft") { flip(); }
  });
  window.addEventListener("resize", fitPage);
}

async function boot() {
  const params = new URLSearchParams(location.search);
  // 縦書き is deferred past v1 (ADR-004): no visible toggle ships, but the
  // setting stays reachable for engineering evaluation via ?axis=vertical.
  if (params.get("axis") === "vertical") document.documentElement.dataset.axis = "vertical";
  if (params.has("t")) state.frozenT = Math.max(0, Math.min(1, Number(params.get("t")) || 0));

  applyStrings();
  wireVerbs();

  // The two bundled faces have different metrics from any fallback, so nothing
  // is measured (or drawn on the canvas) until they are in.
  try {
    await document.fonts.ready;
  } catch (err) {
    console.error("font loading:", err);
  }
  fontsReady = true;

  state.live = await waitForBridge();
  const injected = !!window.CF_BEATS; // real data, staged by the capture harness
  document.documentElement.dataset.mode = state.live ? "live" : injected ? "capture" : "sample";
  // A SAMPLE leaf is stamped 見本 so a fixture can never be read as a world.
  // Injected capture data is a real stream and is not stamped.
  $("#specimen").hidden = state.live || injected;

  if (state.live) {
    try {
      const inv = await bridge("shelf");
      if (inv && inv.invitation) {
        // The spine says what the book IS before it is opened — the place and
        // the span worldgen already fixed. Both are stream-side facts; if the
        // bridge gives no span the invitation stands on its own rather than
        // printing a hole.
        $("#shelf-invite").textContent = inv.span_years
          ? STRINGS.shelfSpine(inv.invitation, inv.span_years)
          : STRINGS.shelfInvite(inv.invitation);
      }
    } catch (err) {
      console.error("bridge failure: shelf", err);
    }
  }

  // ?surface=N — open straight onto the Time Surface for the death of life N.
  // Used by the offline capture harness; with ?t= it renders one frozen frame.
  if (params.has("surface")) {
    state.stream = state.live ? await bridge("play", null, []) : (window.CF_BEATS || SAMPLE);
    state.lifeShown = Number(params.get("surface")) || 1;
    const win = TimeSurface.pickWindow(state.stream, state.lifeShown);
    if (win) {
      state.win = win;
      // `&page=juncture` lands on B1' instead — the beat after the surface, so a
      // capture can show the recognition the stream actually carries (or, far
      // more often, show that it carries none).
      state.cursor = junctures().indexOf(win.juncture);
      if (state.cursor < 0) state.cursor = junctures().length;
      if (params.get("page") === "juncture") {
        // Whatever the NEXT life's page actually is — its juncture, or its own
        // window when the world asks it nothing. Landing on `win.juncture`
        // directly would photograph a juncture belonging to a life two ahead.
        advanceTo(state.lifeShown + 1);
        return setStatus(state.live ? STRINGS.statusReady : STRINGS.statusPreview);
      }
      show("juncture", "forward");
      return playSurface(win);
    }
  }

  show("shelf", "forward");
  setStatus(state.live ? STRINGS.statusReady : STRINGS.statusPreview);
}

if (document.readyState === "loading") {
  window.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
