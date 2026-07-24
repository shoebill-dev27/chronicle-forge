/* The Living Chronicle — I-1 skeleton frontend.
   State machine over three pages (shelf -> opening -> juncture) and the four
   verbs (turn / flip / seal / hold). Data comes from the pywebview bridge
   (window.pywebview.api); with no bridge it falls back to SAMPLE data so the
   page previews standalone. Hold-to-remember (I-05, ~800 ms) fires the stub
   S-02 reveal; releasing early cancels (the hypothesis stays the player's). */

"use strict";

const HOLD_MS = 800;
const PAGES = ["shelf", "opening", "juncture"];

// Standalone-preview fallback when the Python bridge is absent.
const SAMPLE = {
  seed: 1,
  place: "the Salt Kingdoms",
  opening: "A life opens in the Salt Kingdoms.",
  header: ["── Year 3 · age 14 · an age of salt ──   ❰ The world turns to you ❱"],
  options: [
    { index: 1, label: "Open the hill's undercroft", kind: "Deed", why: "the water is failing" },
    { index: 2, label: "Hold the old road's toll", kind: "Order", why: "the town looks to you" },
    { index: 3, label: "Walk to the assembly", kind: "Chance", why: "a season of unrest" },
  ],
  marked_index: 1,
  has_juncture: true,
};

const $ = (sel, root = document) => root.querySelector(sel);
const api = () => (window.pywebview && window.pywebview.api) || null;

let state = { page: "shelf", juncture: null, selected: null, sealed: false };

function setStatus(t) { $("#status").textContent = t; }

function show(page) {
  state.page = page;
  for (const p of PAGES) {
    const el = document.querySelector(`[data-page="${p}"]`);
    if (el) el.hidden = p !== page;
  }
}

async function bridge(method, ...args) {
  const a = api();
  if (a && typeof a[method] === "function") return a[method](...args);
  return null; // caller supplies the SAMPLE fallback
}

/* ---- pages ---- */

async function toOpening() {
  const data = (await bridge("open_juncture")) || SAMPLE;
  state.juncture = data;
  $("#opening-place").textContent = data.place;
  $("#opening-line").textContent = data.opening;
  show("opening");
  setStatus(`seed ${data.seed} · ${data.place}`);
}

function toJuncture() {
  const data = state.juncture || SAMPLE;
  $("#juncture-head").textContent = (data.header && data.header[0]) || "The world turns to you";
  const list = $("#options");
  list.innerHTML = "";
  state.selected = null;
  state.sealed = false;
  $("#seal-btn").disabled = true;
  $("#reveal").hidden = true;
  $("#outcome").hidden = true;

  for (const opt of data.options) {
    const li = document.createElement("li");
    li.className = "option print";
    if (opt.index === data.marked_index) li.classList.add("marked");
    li.tabIndex = 0;
    li.dataset.index = String(opt.index);
    li.innerHTML =
      `${escapeHtml(opt.label)}<span class="kind">${escapeHtml(opt.kind)} · ${escapeHtml(opt.why)}</span>` +
      `<span class="holdbar"></span>`;
    li.addEventListener("click", () => selectOption(li, opt));
    if (opt.index === data.marked_index) wireHold(li);
    list.appendChild(li);
  }
  show("juncture");
}

function selectOption(li, opt) {
  if (state.sealed) return;
  for (const el of document.querySelectorAll(".option")) el.classList.remove("selected");
  li.classList.add("selected");
  state.selected = opt.index;
  $("#seal-btn").disabled = false;
}

/* ---- hold-to-remember (I-05) -> stub reveal ---- */

function wireHold(li) {
  const bar = $(".holdbar", li);
  let timer = null, raf = null, start = 0;

  const cancel = () => {
    if (timer) clearTimeout(timer);
    if (raf) cancelAnimationFrame(raf);
    timer = raf = null;
    li.classList.remove("holding");
    bar.style.width = "0";
  };
  const tick = () => {
    const pct = Math.min(1, (performance.now() - start) / HOLD_MS);
    bar.style.width = (pct * 100) + "%";
    if (pct < 1) raf = requestAnimationFrame(tick);
  };
  const begin = (e) => {
    e.preventDefault();
    if (state.sealed) return;
    li.classList.add("holding");
    start = performance.now();
    raf = requestAnimationFrame(tick);
    timer = setTimeout(() => { cancel(); fireReveal(); }, HOLD_MS);
  };

  li.addEventListener("pointerdown", begin);
  li.addEventListener("pointerup", cancel);
  li.addEventListener("pointerleave", cancel);
  li.addEventListener("keydown", (e) => { if (e.key === "r" || e.key === "R") begin(e); });
  li.addEventListener("keyup", cancel);
}

async function fireReveal() {
  const r = (await bridge("remember")) || { hand: "……この手は、前にもこれを選んだ。", epithet: "前世のあなた", stub: true };
  $("#reveal-hand").textContent = r.hand;
  $("#reveal-epithet").textContent = "—— " + r.epithet;
  $("#reveal").hidden = false;
  setStatus("remembered");
}

/* ---- seal (I-04) ---- */

async function seal() {
  if (state.selected == null || state.sealed) return;
  state.sealed = true;
  $("#seal-btn").disabled = true;
  const res = (await bridge("seal", state.selected)) || { outcome: "The ink sets.", stub: true };
  const out = $("#outcome");
  out.textContent = res.outcome;
  out.hidden = false;
  setStatus("sealed");
}

/* ---- verbs / wiring ---- */

function turn() {
  if (state.page === "shelf") return toOpening();
  if (state.page === "opening") return toJuncture();
}
function flip() {
  if (state.page === "juncture") return show("opening");
  if (state.page === "opening") return show("shelf");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
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
  $("#axis-toggle").addEventListener("click", () => {
    const el = document.documentElement;
    el.dataset.axis = el.dataset.axis === "vertical" ? "horizontal" : "vertical";
  });
}

async function boot() {
  wireVerbs();
  const inv = await bridge("shelf");
  if (inv && inv.invitation) $("#shelf-invite").textContent = `A book waits: ${inv.invitation}.`;
  show("shelf");
  setStatus(api() ? "bridge ready" : "preview (no bridge)");
}

if (window.pywebview) {
  window.addEventListener("pywebviewready", boot);
} else {
  window.addEventListener("DOMContentLoaded", boot);
}
