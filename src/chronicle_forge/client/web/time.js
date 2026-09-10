/* The Time Surface — C1「地層」.
 *
 * B2 死 → B3 時間経過 → B4 余波 as one continuous image, drawn from the typed
 * beat stream (play/beats.py) and nothing else. Every year, every event, every
 * seal below is a field of that stream; there is no decorative event, no
 * invented place and no invented legacy. The spike that chose this candidate
 * over five rivals is docs/design_v1_time_surface.md.
 *
 * WHY A SURFACE AND NOT A LINE OF TEXT
 *   Measured across seeds 1/7/42/99/123, the world is almost silent while the
 *   player is alive and loudest during the skip that follows their death — and
 *   nearly every event of that skip descends from the life that just ended. The
 *   old build spent that on one caption: "… 8 years pass …". Here the eight
 *   years ARE the screen, and the specks that fall through them are the
 *   player's own consequences, coloured by whether the stream says they own
 *   them.
 *
 * THE THREE REGISTERS
 *   A majority of aftermaths name nothing (73 of 117 windows measured), so a
 *   surface that only works when a legacy hardens would be broken most of the
 *   time. This one has three honest states and picks by data, never by wish:
 *     sealed  — the aftermath hardened a mark: 朱 seals, and the camera closes
 *               on the first one (the 292px test is won by the seal's share of
 *               the frame, not by its glow).
 *     echo    — nothing hardened, but the years moved on what the player left:
 *               the specks stay, gold, and the caption counts them.
 *     silent  — neither: the strata hold still and say so.
 *
 * Determinism: no Math.random(), no Date. All jitter comes from a PRNG keyed by
 * the world seed, so the same (seed, t) always draws the same pixels. */

"use strict";

(function () {
  const DARK = "#110e0c", SHU = "#b03a2c", SHU_HI = "#de684a", GOLD = "#c6a260";
  const W = 680, H = 420, PAD = 46;
  const FONT = '"Chronicle Print","Noto Serif JP",serif';

  /* ---- deterministic PRNG (xorshift32) ---- */
  function rng(seed) {
    let s = seed >>> 0 || 1;
    return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
  }
  const ease = (t) => (t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t));
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;

  /* ---- the cut. The client plays 0 → REBIRTH_END and then turns the page to
     the real juncture (B1'), so the surface never draws a choice. ---- */
  const CUT = [
    { k: "death",     at: 0.00, to: 0.14 },
    { k: "years",     at: 0.14, to: 0.47 },
    { k: "aftermath", at: 0.47, to: 0.70 },
    { k: "rebirth",   at: 0.70, to: 0.80 },
  ];
  const REBIRTH_END = 0.80;
  function done(t, k) { const p = CUT.find((x) => x.k === k); return clamp((t - p.at) / (p.to - p.at), 0, 1); }

  /* ---- pick the window to play: the death of `afterLife` and what followed ---- */
  function pickWindow(D, afterLife) {
    const b = D.beats;
    for (let i = 0; i < b.length; i++) {
      if (b[i].t !== "death" || b[i].life !== afterLife) continue;
      const years = b[i + 1], aftermath = b[i + 2];
      if (!years || years.t !== "years" || !aftermath || aftermath.t !== "aftermath") continue;
      const rest = b.slice(i + 3);
      return {
        death: b[i],
        years,
        aftermath,
        rebirth: rest.find((x) => x.t === "rebirth") || null,
        juncture: rest.find((x) => x.t === "juncture") || null,
      };
    }
    return null;
  }

  /* Which attributions the reader has actually uncovered. The surface asks;
     it never decides. Default: nothing is known, which is the safe answer — a
     surface that guesses wrong here shows a stranger their own forgotten hand
     before they have found it. */
  let knows = () => false;
  function setKnown(fn) { knows = typeof fn === "function" ? fn : () => false; }

  // The confirmed hardened marks of this window, in stream order.
  function confirmed(win) {
    return (win.aftermath.hardened || []).filter((m) => knows(m.ref));
  }

  /* Which register this window is in — decided by the stream AND by what the
     reader has earned (D-03/D-04, baseline UX-R3).

     `sealed` is the loud one: 朱, the founder's own layer, and the camera
     closing on it. That is the grammar of a CONFIRMED connection to a past
     life, so it may only fire once the connection is confirmed. Every hardened
     mark belongs to a life older than the last, so firing it on arrival — which
     is what this did until 2026-09-10 — delivered exactly the attribution D-03
     reserves for the player to discover, on the first surface they ever see.

     `unattributed` is the honest form of the same data: the mark is drawn, and
     named, but at a neutral depth, in ink, with no camera move and no founder.
     An unexplained older mark is what the spec wants there. */
  function register(win, known) {
    if (typeof known === "function") setKnown(known);
    if (confirmed(win).length) return "sealed";
    if ((win.aftermath.hardened || []).length) return "unattributed";
    if (win.aftermath.echoes.length) return "echo";
    return "silent";
  }

  /* ---- geometry ---- */
  /* The camera IS the beat. Through B3 the frame holds only the years the
     player was dead, so eight years fill the screen instead of being a caption;
     through B4 it pulls back to the whole world and the mark turns out to be
     buried far in the past. */
  function camera(D, win, t) {
    const k = ease(clamp(done(t, "aftermath") / 0.55, 0, 1));
    const lo = lerp(win.years.from_year - 0.7, 0, k);
    const hi = lerp(win.years.to_year + 0.7, D.max_year, k);
    const f = (y) => PAD + (W - 2 * PAD) * ((y - lo) / (hi - lo || 1));
    f.zoom = 1 - k;
    return f;
  }

  // Marks that share a planted year would stack on one another; the seal never
  // leaves its year, so the duplicates fan sideways instead.
  function fan(ms) {
    const by = {};
    return ms.map((m) => { const y = m.planted_year || 0; const k = (by[y] = (by[y] || 0) + 1); return Object.assign({}, m, { slot: k - 1 }); });
  }

  /* ---- ink ---- */
  function grain(ctx, r, n, alpha) {
    ctx.save(); ctx.globalAlpha = alpha;
    for (let i = 0; i < n; i++) { ctx.fillStyle = r() < 0.5 ? "#000" : "#fff"; ctx.fillRect((r() * W) | 0, (r() * H) | 0, 1, 1); }
    ctx.restore();
  }
  function vignette(ctx) {
    const g = ctx.createRadialGradient(W * 0.38, H * 0.34, H * 0.1, W * 0.5, H * 0.5, W * 0.78);
    g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(0,0,0,.72)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  function raking(ctx) { // the single light source, upper-left
    const g = ctx.createRadialGradient(W * 0.30, H * 0.16, 10, W * 0.30, H * 0.16, W * 0.95);
    g.addColorStop(0, "rgba(255,232,190,.16)"); g.addColorStop(0.5, "rgba(255,226,180,.05)"); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  /* The seal. 朱 ONLY when the connection to a past life is confirmed
     (baseline UX-R5: one accent, one meaning). An unconfirmed mark is real and
     is drawn — marks never lie — but in ink, because vermilion here would be
     the page asserting a bond the reader has not earned. */
  function wax(ctx, x, y, rad, r, isConfirmed) {
    ctx.save();
    const g = ctx.createRadialGradient(x - rad * 0.3, y - rad * 0.35, rad * 0.1, x, y, rad * 1.15);
    if (isConfirmed) { g.addColorStop(0, SHU_HI); g.addColorStop(0.62, SHU); g.addColorStop(1, "rgba(90,24,18,0)"); }
    else { g.addColorStop(0, "#6d5c46"); g.addColorStop(0.62, "#4a3d2e"); g.addColorStop(1, "rgba(30,24,17,0)"); }
    ctx.fillStyle = g; ctx.beginPath();
    for (let i = 0; i <= 26; i++) { const a = (i / 26) * Math.PI * 2, w = rad * (0.9 + 0.16 * r()); ctx[i ? "lineTo" : "moveTo"](x + Math.cos(a) * w, y + Math.sin(a) * w); }
    ctx.fill();
    ctx.globalAlpha = 0.5; ctx.fillStyle = SHU_HI;
    ctx.beginPath(); ctx.arc(x - rad * 0.22, y - rad * 0.26, rad * 0.34, 0, 7); ctx.fill();
    ctx.restore();
  }
  function text(ctx, s, x, y, size, color, align, alpha) {
    ctx.save(); ctx.globalAlpha = alpha === undefined ? 1 : alpha;
    ctx.font = size + "px " + FONT; ctx.fillStyle = color;
    ctx.textAlign = align || "left"; ctx.textBaseline = "alphabetic";
    ctx.fillText(s, x, y); ctx.restore();
  }
  function centred(ctx, s, x, y, size, color, alpha) {
    // A name is placed at its own year, and long names would run off the leaf;
    // re-anchor the text rather than move the seal off the year it belongs to.
    ctx.font = size + "px " + FONT;
    const w = ctx.measureText(s).width;
    const align = x - w / 2 < PAD ? "left" : x + w / 2 > W - PAD ? "right" : "center";
    text(ctx, s, align === "left" ? PAD : align === "right" ? W - PAD : x, y, size, color, align, alpha);
  }

  /* ---- the surface ---- */
  function draw(ctx, D, win, t) {
    ctx.fillStyle = DARK; ctx.fillRect(0, 0, W, H);
    const r = rng(D.seed * 7919), X = camera(D, win, t);
    const prog = ease(done(t, "years")), after = done(t, "aftermath");
    const base = H - 46, top = 68, span = base - top;
    const cur = win.death.life;

    // A layer's thickness is how much of the world's history that life has
    // caused SO FAR — counted off the stream, on an absolute scale, so the
    // strata are thin early and fill the frame by the last life. That is not a
    // progress bar bolted on: it is the same number the specks are, stacked.
    // The living never see their own layer; it accretes through B3, which is
    // when it is actually deposited.
    //
    // DEPTH is a fixed number of events per full frame, and that is the whole
    // point: the unit was once `span / worldTotal` over EVERY beat in the
    // stream, which meant the scale was read off years the player had not
    // reached yet. A later choice that changed the world's total silently
    // rescaled strata already laid down (measured: seed 42 moved 59 -> 56
    // mid-run), so the past was not stable — and I-2's incremental loop cannot
    // know a total for a future it has not simulated. With a constant, a band's
    // height is decided by that life's own events and never moves again.
    // 96 clears the loudest world measured over seeds 1..40 + 42/99/123 (75
    // owned events); anything past it is clamped rather than allowed to run off
    // the top of the leaf.
    const DEPTH = 96;
    const attr = (e) => (e.owners.length ? e.owners[0] : 0);
    const unit = span / DEPTH;

    const count = {};
    for (const b of D.beats) {
      if (b.t !== "years" || b.after_life > cur) continue;
      const isCur = b.after_life === cur;
      b.events.forEach((e, i) => {
        const o = attr(e); if (!o) return;
        if (isCur && i / Math.max(1, b.events.length) > prog) return;
        count[o] = (count[o] || 0) + 1;
      });
    }

    // Geometry first, drawing second: the camera closes on a seal, so the
    // seal's position has to be known before anything is painted.
    const bandY = {}, bandTop = {}, bandH = {};
    { let y = base;
      D.lives.forEach((l) => {
        // Clamped at the top of the measure: a world louder than DEPTH loses
        // the overflow rather than drawing off the leaf.
        const h = Math.min((count[l.ordinal] || 0) * unit, y - top); if (h < 1.5) return;
        bandH[l.ordinal] = h; bandTop[l.ordinal] = y - h; bandY[l.ordinal] = y - h * 0.55; y -= h;
      }); }
    const surface = Math.min.apply(null, [base].concat(Object.keys(bandTop).map((k) => bandTop[k])));

    const marks = fan(win.aftermath.hardened).slice(0, 3);
    const anyConfirmed = confirmed(win).length > 0;
    const pop = ease(clamp(after / 0.6, 0, 1));
    const pos = marks.map((m) => {
      // A seal's size is its reach, so the gap between two seals of the same
      // year has to be measured in those radii — several marks routinely share
      // year 0, and at the climax's magnification a fixed offset merges them
      // into one blob that reads as a single legacy the world never had.
      const rad = lerp(11, 24, clamp(m.reach / 50, 0, 1));
      return {
        m,
        rad,
        x: clamp(X(m.planted_year || 0) + m.slot * rad * 3.4, PAD + 16, W - PAD - 16),
        // The year is horizontal position and says nothing about whose the mark
        // is; the LAYER is the founding life, and that is an attribution. So an
        // unconfirmed mark floats just above the strata instead of being filed
        // into the life that made it (baseline UX-R3: no founder-specific
        // geometry before confirmation).
        y: knows(m.ref) ? bandY[m.founder_life] || base - 24 : surface - 26,
        confirmed: knows(m.ref),
      };
    });

    // The close. The seal never leaves its year or its layer — the frame comes
    // to IT. At 292px a bloom was not enough; a push is (see the spike doc).
    // A push toward one mark says "this one, and it is yours". Before the
    // connection is confirmed that is the reveal itself, done by camera.
    const close = pos.length && anyConfirmed ? ease(clamp((after - 0.55) / 0.45, 0, 1)) : 0;
    const z = 1 + 2.6 * close;
    ctx.save();
    if (close > 0) { ctx.translate(W / 2, H * 0.52); ctx.scale(z, z); ctx.translate(-pos[0].x, -pos[0].y); }

    let y = base;
    D.lives.forEach((l, i) => {
      const h = bandH[l.ordinal]; if (!h) return;
      const u = i / Math.max(1, D.lives.length - 1);
      const g = ctx.createLinearGradient(0, y - h, 0, y);
      g.addColorStop(0, `rgb(${lerp(196, 120, u) | 0},${lerp(163, 94, u) | 0},${lerp(112, 60, u) | 0})`);
      g.addColorStop(0.14, `rgb(${lerp(150, 92, u) | 0},${lerp(120, 70, u) | 0},${lerp(78, 44, u) | 0})`);
      g.addColorStop(1, `rgb(${lerp(64, 38, u) | 0},${lerp(49, 28, u) | 0},${lerp(31, 18, u) | 0})`);
      const crest = (x) => Math.sin((x + l.ordinal * 137) * 0.017) * 4.2 + Math.sin(x * 0.053 + l.ordinal) * 2.1;
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-W, y);
      for (let x = -W; x <= 2 * W; x += 8) ctx.lineTo(x, y - h + crest(x));
      ctx.lineTo(2 * W, y); ctx.closePath(); ctx.fill();
      ctx.save(); ctx.strokeStyle = "rgba(28,20,13,.85)"; ctx.lineWidth = 1.6 / Math.max(1, z * 0.6);
      ctx.beginPath();
      for (let x = -W; x <= 2 * W; x += 8) ctx.lineTo(x, y - h + crest(x));
      ctx.stroke(); ctx.restore();
      y -= h;
    });

    // The events of every skip, at the year they happened, in the layer of the
    // life that caused them. Gold = the stream says this life owns it; ash =
    // the world moved on its own. In most windows almost everything is gold.
    ctx.save();
    for (const b of D.beats) {
      if (b.t !== "years") continue;
      const isCur = b.after_life === cur;
      if (!isCur && b.after_life > cur) continue;
      b.events.forEach((e, i) => {
        if (isCur && i / Math.max(1, b.events.length) > prog) return;
        const owner = e.owners[0]; if (!bandY[owner]) return;
        const mine = e.owners.indexOf(cur) >= 0;
        const px = X(e.year) + (r() - 0.5) * 9;
        const py = bandTop[owner] + 3 + r() * Math.max(2, bandH[owner] - 6);
        ctx.globalAlpha = mine ? 0.9 : 0.5;
        ctx.fillStyle = mine ? (e.scale === "large" ? "#f4d98d" : GOLD) : (e.scale === "large" ? "#cbb590" : "#8d7a5c");
        const sz = (e.scale === "large" ? 3.2 : 1.8) / Math.max(1, z * 0.55);
        ctx.fillRect(px, py, sz, sz);
      });
    }
    ctx.restore();

    // Falling dust while the years run: the layer being deposited.
    if (prog > 0 && prog < 1) {
      ctx.save(); ctx.globalAlpha = 0.5;
      for (let i = 0; i < 90; i++) { ctx.fillStyle = "#8d7a5c"; ctx.fillRect(r() * W, surface - r() * 80 * (1 - prog), 1.3, 1.3); }
      ctx.restore();
    }

    pos.forEach((P, i) => {
      const k = clamp((pop - i * 0.13) / 0.55, 0, 1); if (k <= 0) return;
      ctx.save(); ctx.globalAlpha = k * 0.55; ctx.strokeStyle = GOLD; ctx.lineWidth = 1 / Math.max(1, z * 0.6);
      ctx.setLineDash([3, 4]); ctx.beginPath(); ctx.moveTo(P.x, P.y); ctx.lineTo(P.x, surface - 6); ctx.stroke(); ctx.restore();
      wax(ctx, P.x, P.y, P.rad * k, r, P.confirmed);
    });
    ctx.restore();

    raking(ctx); vignette(ctx); grain(ctx, rng(11), 3000, 0.055);

    if (pop > 0.5 && marks[0]) {
      centred(ctx, `"${marks[0].name}"`, W / 2, close > 0.3 ? H * 0.52 + pos[0].rad * z + 34 : H - 52,
        lerp(15, 20, close), "#efdcb6", clamp((pop - 0.5) / 0.4, 0, 1));
    }
    text(ctx, caption(win, t), PAD, H - 16, 13, "#8a7862", "left", Math.max(0.35, Math.max(prog, pop)));
  }

  /* ---- the caption: real numbers only, one register per data state ----
     Every word comes from strings.js, which owns D-3 §7's closed epithet table.
     A former self is `最初のあなた / N度目のあなた` and nothing else; the
     `第Nの生` form this file used to build was never in that table. */
  function caption(win, t) {
    const S = window.CF_VOICE.strings;
    const reg = register(win), span = win.years.span;
    if (done(t, "years") < 1) {
      if (done(t, "death") < 1 || done(t, "years") === 0) return S.surfaceDeath(win.death.life, win.death.age);
      return span > 0 ? S.surfaceFalling(span) : S.surfaceHeld;
    }
    if (reg === "sealed") {
      const m = confirmed(win)[0];
      // `planted_year` is optional in the stream; a mark without one is still a
      // mark, so the date is dropped rather than printed as a hole.
      return S.surfaceSealed(m.founder_life, m.planted_year);
    }
    // Something gained a name, but whose it is has not been earned yet: count
    // it truthfully and name no life (D-03).
    if (reg === "unattributed") return S.surfaceHardened(win.aftermath.hardened.length);
    if (reg === "echo") return S.surfaceEcho(win.aftermath.echoes.length);
    return span > 0 ? S.surfaceSilent(span) : S.surfaceHeld;
  }

  window.TimeSurface = { W, H, CUT, REBIRTH_END, done, pickWindow, register, draw, caption, setKnown, confirmed };
})();
