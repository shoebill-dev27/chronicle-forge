# P8 Player Experience — Design (Confirmed)

Status: **Approved — implementation Go (2026-06-15), with the three pre-impl
additions below incorporated (concurrent-critical merge, "let it pass"
semantics, recognition frequency).**

P8 is not a UI phase. It is the design of the *dialogue between the player and
history*. P6 generates history; P7 interprets it; P8 lets a player live inside
the reincarnating loop and respond to history's call.

## Guiding principle

```
The world acts continuously.
The player intervenes occasionally.
History remembers selectively.
```

Chronicle Forge is not a game you operate every turn. It is a game where you
answer the world's call when history stirs.

## Locked decisions

1. **Turn cadence — intervene on junctures.** The world advances continuously in
   seasons (Spring/Summer/Autumn/Winter, `TURNS_PER_YEAR = 4`) using the existing
   opportunity-mode autoplay. The player is asked for input **only** when a
   juncture gate fires; otherwise the auto-chooser proceeds.
2. **New life — fated, non-selectable.** The player never chooses talent or
   birth. Current talent determinism (`rng.choice(list(Talent))`) is kept. The
   protagonist is history, not the player; a life is *given*, and the player
   chooses *within* it. (Future, allowed but out of scope: ancestral-legacy
   influence, heritage birth-bias, era drift — never a player pick. Goal: "I was
   born into this world," never "I chose this build.")
3. **First increment — full end-to-end MVP.** death → Dead Summary → Chronicle →
   Timeline → Legacy View → new life → Opportunity → choice → world progress,
   connected minimally but completely. The core of Chronicle Forge is the
   *chain* of lives, not one life; an in-life-only slice could not verify the
   inheritance experience.

## MVP success conditions

The player must naturally experience all seven:

1. Receive a call from the world.
2. Choose.
3. Die.
4. Read the history.
5. See the legacy.
6. A next life begins.
7. **Encounter the traces of a former self.**

If these hold, the core experience of Chronicle Forge — *a reincarnating
history* — is considered complete.

## Observed tension distribution (grounding the gate)

Read-only observation over full opportunity-mode runs (seeds 42/123/999, ~60
turns each). P6 logic unchanged.

| metric | seed42 | seed123 | seed999 |
|---|---|---|---|
| top-tension median | 0.561 | 0.557 | 0.640 |
| top p75 / p90 / p95 | .596/.885/.927 | .668/.915/.919 | .856/.911/.925 |
| top max | 0.943 | 0.949 | 0.936 |
| WildCard top-rate | 0.52 | 0.43 | 0.49 |
| Legacy offered turns | 32/63 | 36/63 | 28/59 |

The distribution is bimodal: a **baseline cluster ~0.42–0.67** and a **spike
cluster ~0.88–0.94**. The spikes are history's call. Legacy is offered on ~half
of all turns, so "Legacy present ⇒ ask" alone would over-prompt.

## 1. Juncture gate — thresholds

The valley between baseline and spike sits near 0.85.

| profile | `T_ASK` | est. asks/world | character |
|---|---|---|---|
| conservative | 0.88 | ~6 | great events only |
| **balanced (default)** | **0.85** | ~6–15 | cuts at the valley |
| sensitive | 0.80 | ~15+ | catches small chances |

Additional constants: `T_HISTORY = 0.70` (history-opportunity floor),
`T_CRISIS = 0.92` (interrupts cooldown). Initial values; tunable in the P8 layer
only (never P6 weights).

## 2. Ask / don't-ask heuristics (OR gate)

Ask the player when **any** holds:

1. **High tension** — `top.tension >= T_ASK`.
2. **Novelty** — the offered set contains a first-ever kind, a first-ever
   target, or a Heritage promoted since the last ask.
3. **History** — a Legacy/History opportunity is in the **top slot**, or appears
   with `tension >= T_HISTORY` (mere presence does not trigger).

Guardrails (the core requirement: *never make the player wait, never miss the
moment*):

- **cooldown** — after an ask, suppress non-critical asks for `K = 4` turns
  (one year); a spike above `T_CRISIS` may interrupt the cooldown.
- **budget** — ≤ ~6 asks per life, ≤ 2 per year; overflow drops the
  lowest-priority asks.
- **floor** — if a life would otherwise receive zero asks, force one ask at its
  highest-tension turn, so every life has agency.
- **concurrent-critical merge (fixed rule)** — when more than one critical ask
  arises within a cooldown window (e.g. several `T_CRISIS` spikes), keep only
  the single highest-tension ask and **discard the rest**. The player does not
  process a backlog; history is remembered selectively. This applies
  "History remembers selectively" to the input layer itself — the gate never
  queues asks, it only ever surfaces the most pressing one.

The gate lives in `play/gate.py`, strictly outside P6. It reads opportunities'
already-computed signals; it never re-scores.

## 3. Opportunity display format

An intervention is one decisive stroke. Show the **top 3 opportunities + "let it
pass"** (P6 may offer 3–5; the display trims to the 3 highest-tension — P6
selection is untouched, the trim is presentation-only). The trigger reason is
the header.

```
── Year 16 · age 16 · an age of faith ──   ❰ A crisis gathers ❱
Korr the Prophet turns the crowd against the temples.

  [1] Stand against Korr   · Wildcard   (peril gathers)
  [2] Spread the faith      · Faction: Dawn Covenant   (tension rising)
  [3] Mentor Maren          · Person     (an ally awaits)
  [0] Let this season pass.

▸ _
```

- Header reason by trigger: `A crisis gathers` (tension) / `Something new stirs`
  (novelty) / `History remembers` (history).
- "Why now" from the dominant signal, in words (Δ rising / Σ long neglected /
  Ω your past pulls here / Ρ an ally awaits). **No raw numbers** (P7 discipline).

## 4. Choices per ask

**Top 3 + "let it pass" (4 options), fixed.** Five choices blunt the decision; a
juncture is a single move.

### "Let it pass" semantics (fixed)

`[0] Let this season pass` is **not** "do nothing" — it is **"entrust it to the
world."** Implementation contract: selecting it **delegates the turn to the
auto-chooser**, which picks and executes an option exactly as on a non-ask turn.
It is **not** a skipped turn: the turn is consumed, the world advances normally,
and history is still made — just not by the player's explicit hand. (Mechanically
this is the same path a non-ask turn already takes, so "let it pass" and "the
world acts while you are silent" are one and the same.)

## 5. Auto-progress log granularity

No per-season output. One **digest line per year** lets the world flow, then it
stops at a juncture:

```
Year 14  The faith deepens; you tend the Dawn Covenant.
Year 15  A school takes hold in the north.        ← only history-promotion years emphasized
Year 16  ❰ A crisis gathers ❱  →  (ask player)
```

- normal year: one line for the auto-chosen action (P7 `labels` reused).
- **history-promotion** years (Heritage formed, WildCard resolved) get an
  emphasized line.
- within-season detail is silent (the world advances continuously; the telling
  is selective — "History remembers selectively").

## 6. Death → inheritance → new life

Chained P7 renderers; no new generation logic.

```
[death]    dead_summary   (P7-1)
[history]  life_chronicle (P7-2)
[timeline] life_timeline  (P7-3)
[legacy]   legacy_view    (P7-4)   — "What outlived you?"
[skip]     time_skip → "37 years pass…" + stopped year (+ promotions in the gap)
[rebirth]  begin_life (fated talent) → new-life intro (talent · year · world mood)
           → loop resumes
```

## 7. Encountering a former self (success condition #7)

Every life is the player reincarnated, so every Legacy/Heritage opportunity is,
by definition, a past self's work. The gate's **history** trigger surfaces these,
and the display frames them as **recognition**, naming the founding life:

```
❰ History remembers ❱
You come upon the Doctrine of the Long Dawn —
the work of a life you lived, ages ago.
  [1] Tend the Doctrine of the Long Dawn   · Legacy   (your past pulls here)
```

This makes #7 emerge from the existing data (heritage `source_seed` →
`planted_by_life_id` → that prior life's index/talent) with no engine change.

### Recognition frequency (fixed)

The history trigger is strong; framing the *same* heritage as "the work of a
life you lived" every time would dull the surprise. Rule: within a life, show
the recognition frame **only the first time** that heritage is encountered;
every later encounter reverts to the plain Legacy display. Re-encountering a
former self should feel like **discovery, not notification.** (Tracked per
current life in volatile play-session state — `seen_recognitions: set[heritage
id]` — never persisted to the world, keeping the world read-only.)

## Architecture

- **New, isolated package `play/`:**
  - `play/gate.py` — juncture decision (thresholds, heuristics, cooldown/budget/floor). Pure, read-only on world.
  - `play/render.py` — turn screen, yearly digest, transition screens (reuses P7 renderers + `labels`).
  - `play/human.py` — human `Chooser` (numbered prompt → stdin int → index); I/O injectable for tests.
  - `play/session.py` — `run_human_world(seed, io)` driver: the human counterpart of `simulate_world`, reusing the opportunity-mode world engine and `play_turn`.
- **Untouched (protected):** `opportunity.py` (P6), the execution mutation funnel, `reporting/experience.py` (P7), the legacy/opportunity auto paths, the seed42 golden assets.
- **Determinism:** world advancement uses the existing opportunity-mode engine as-is. The human chooser draws no RNG; on non-ask turns it delegates to the auto-chooser. With no asks, a human run is byte-identical to opportunity mode. The gate is outside P6 and never touches tension weights.

## Implementation plan (increments)

1. `play/gate.py` + unit tests (gate fires/suppresses on synthetic opportunity sets; cooldown/budget/floor).
2. `play/render.py` + unit tests (turn screen, yearly digest, former-self recognition; output via injected writer; deterministic).
3. `play/human.py` human chooser + scripted-input chooser for tests.
4. `play/session.py` `run_human_world` wiring the full loop (death → P7 chain → rebirth) with injectable I/O.
5. Integration test: a scripted full play of one world reaches all 7 success conditions; auto regression (seed42 identity, existing 180 tests) stays green.

## Verification plan

- Gate/render/human are unit-tested with injected I/O (deterministic, no console).
- Auto regression: seed42 byte-identity and the existing 180 tests must not regress.
- A scripted-chooser integration test drives a full reincarnating run and asserts each of the seven MVP success conditions is reachable, including encountering a former self.

## Risks

- **Prompt rhythm.** Spiky worlds (seed999) could over-ask; the budget + cooldown absorb this. Initial constants are tunable in the P8 layer.
- **Determinism drift.** The human path must never alter the auto RNG stream; enforced by the no-RNG chooser and the byte-identity regression.
- **Scope creep into UI.** Console I/O only; no UI framework. P8 is interaction design, not presentation tech.
