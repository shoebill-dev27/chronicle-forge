# Playtest Review (P5) — Is it a game?

**Scope:** game-design viability, not implementation quality. No code was
changed; this is observation only.

**Method:** ran `simulate_world(seed)` for 25 seeds (1–25) using the deterministic
auto-player, then aggregated. **Caveat:** the auto-player chooses talent and
activities largely at random. So "dominant strategy" can only be inferred
indirectly — but any attractor that appears *under random play* is a systemic
bias, not a player choice, which is itself a finding.

---

## 1. Quantitative Results

### 1.1 Per-seed digest

| seed | ending | theme ini→mid→fin | lives | heritage | top score | x-life events | wildcard |
|---|---|---|---|---|---|---|---|
| 1 | Arcane | commerce→innovation→innovation | 2 | 27 | 744 | 33 | resolved |
| 2 | Arcane | warfare→governance→innovation | 2 | 17 | 320 | 26 | resolved |
| 3 | Golden | commerce→governance→culture | 2 | 15 | 256 | 30 | resolved |
| 4 | Golden | innovation→innovation→culture | 2 | 16 | 180 | 29 | resolved |
| 5 | Golden | culture→culture→culture | 2 | 26 | 682 | 29 | dormant |
| 6 | Arcane | faith→innovation→innovation | 2 | 7 | 408 | 27 | resolved |
| 7 | Collapse | warfare→warfare→innovation | 2 | 18 | 120 | 32 | resolved |
| 8 | Theocracy | faith→faith→faith | 2 | 15 | 630 | 31 | resolved |
| 9 | Warring | warfare→warfare→warfare | 2 | 10 | 128 | 17 | dormant |
| 10 | Arcane | governance→innovation→innovation | 2 | 22 | 496 | 27 | resolved |
| 11 | Arcane | faith→innovation→innovation | 2 | 22 | 384 | 23 | resolved |
| 12 | Collapse | faith→faith→warfare | 2 | 16 | 680 | 38 | resolved |
| 13 | Empire | warfare→warfare→governance | 2 | 17 | 620 | 35 | resolved |
| 14 | Arcane | faith→innovation→innovation | 2 | 16 | 256 | 30 | resolved |
| 15 | Arcane | faith→innovation→innovation | 2 | 7 | 68 | 25 | resolved |
| 16 | Theocracy | faith→faith→faith | 2 | 27 | 1680 | 30 | dormant |
| 17 | Arcane | warfare→warfare→innovation | 2 | 22 | 341 | 38 | resolved |
| 18 | Arcane | faith→culture→innovation | 2 | 15 | 270 | 32 | resolved |
| 19 | Golden | culture→culture→culture | 2 | 20 | 420 | 24 | dormant |
| 20 | Golden | faith→culture→culture | 2 | 25 | 1360 | 41 | resolved |
| 21 | Theocracy | warfare→innovation→faith | 2 | 23 | 264 | 29 | resolved |
| 22 | Arcane | faith→faith→innovation | 2 | 25 | 770 | 35 | resolved |
| 23 | Arcane | faith→faith→innovation | 2 | 12 | 420 | 29 | resolved |
| 24 | Mercantile | warfare→warfare→commerce | 2 | 4 | 204 | 19 | dormant |
| 25 | Mercantile | faith→culture→commerce | 2 | 11 | 290 | 33 | ignited |

### 1.2 Ending distribution (25 worlds)

| Ending | Count | Share |
|---|---|---|
| Arcane Age (innovation) — *Other* | 11 | 44% |
| Golden Age | 5 | 20% |
| Theocracy | 3 | 12% |
| Collapse (Apocalyptic) | 2 | 8% |
| Mercantile — *Other* | 2 | 8% |
| Warring Age | 1 | 4% |
| Empire (Imperial) | 1 | 4% |

The requested buckets: **Warring 1, Golden 5, Empire 1, Theocracy 3, Collapse 2,
Other 13** (Arcane 11 + Mercantile 2).

### 1.3 Theme trajectory

- Initial themes are varied (faith/warfare/commerce/culture/governance/innovation).
- **Final theme is skewed: innovation 12/25 (48%)**, culture 5, faith 3, warfare 2, commerce 2, governance 1.
- Distinct dominant axes per world: avg **2.32** (min 1, max 5).
- Single-axis dominance fraction (share of years held by the most common dominant): avg **0.85**.

→ Themes shift **once** early, then lock. 85% of years sit under one axis; several
worlds (5, 8, 9, 16) never change dominant at all.

### 1.4 Heritage

- Count per world: avg **17.4** (min 4, max 27).
- Top score per world: avg 480 (max 1680). Avg score per heritage: 142.
- Domain distribution (all worlds): **technology 133**, thought 99, monument 69, institution 69, school 65.

→ Technology dominates heritage, mirroring the innovation skew.

### 1.5 Reincarnation value

- Lives per world: **always exactly 2** (min=max=2), 50 lives total.
- Titles inherited: avg 1.80. **Knowledge inherited: 0/25 worlds.** Skills/traits: never.
- Cross-life causal events: avg **29.7/world** (max 41). **lives_with_legacy = 50/50.**

→ Every life leaves a mark (core fantasy holds), but inheritance is title-only and
purely cosmetic; reincarnation count is fixed.

### 1.6 WildCard (single "inventor", innovation-pushing)

- Ignition rate: **20/25 (80%)**; resolved 19/25 (76%); avg 3.16 events/world.
- Theme influence: final INNOVATION in ignited worlds avg **68.8** vs dormant **29.0**.
- Heritage formed on the wildcard's downstream lineage: **0**.
- Average age at death: **19.3** (min 18, max 21); death cause: **choice 50/50** (never lifespan or combat). Events/world avg 28.8.

---

## 2. Findings

1. **Innovation is a systemic attractor (weak "your choices shape history").**
   Under *random* play, 44% of worlds end Arcane and 48% finalize on innovation.
   Cause: the only WildCard is an inventor that pushes INNOVATION and ignites in
   80% of worlds (ignited → innovation 68.8 vs 29.0). The world bends toward
   innovation regardless of the player. This is the most serious threat to the
   core promise.

2. **Theme freezes after the lives end.** Themes move early (avg 2.3 distinct
   dominants) but then plateau (0.85 single-axis share). Once seeds have fired
   and the wildcard resolves, nothing during the long skip moves the theme —
   factions only drift, and faction/NPC steps emit no causal events.

3. **Heritage inflation.** 17.4 heritages per 40-year, 2-life world; technology
   alone accounts for ~38%. Almost every long-lived seed is promoted, so
   "legacy" loses weight — when everything is heritage, nothing is.

4. **Reincarnation is shallow and fixed.** Always exactly 2 lives; only titles
   carry over and they have no mechanical effect; knowledge/skills/traits never
   inherit. There is no strategic thread between lives — the roguelite "build up
   across runs" loop is absent.

5. **Tiny player-agency window, uniform early death.** Every life dies at ~19 of
   "choice" after a handful of world-years, then ~20 years are skipped. The §5
   rule (young death → long skip) therefore *always* maxes the skip, which is
   exactly why every world is 2 lives. The player directly touches only a small
   slice of the 40-year timeline; most history is generated during skips.

6. **Evaluation imbalance (incidental).** Exploration and research both feed
   academia, inflating it (e.g. seed 42 academia=110 vs others near 0). The
   8-axis evaluation is not yet balanced.

### Positives (the spine works)

- **Cross-reincarnation causality is real in 100% of lives** — a life's seeds fire
  during the skip and shape the next life's world. The central fantasy is present.
- Endings still span 7 categories; not fully collapsed.
- WildCard ignition/resolution is healthy and visibly reshapes the world.
- Determinism holds across all runs.

---

## 3. Improvement Candidates (proposals only — not implemented)

Ordered by impact on "is it a game?":

1. **Break the innovation attractor (Finding 1).**
   - Diversify WildCards: randomize archetype per world (revolutionary/prophet/
     conqueror/zealot), each pushing a different axis; or seat 2–3 from the
     registry. Make ignition depend on *player* contribution, not just theme.
2. **Keep history moving during the skip (Finding 2).**
   - Let faction tension and NPC lifecycle emit causal events (wars, successions,
     schisms) that push theme; add mean-reversion/decay so no axis sticks.
3. **Gate heritage promotion (Finding 3).**
   - Require a minimum reach (e.g. ≥2 descendants) or a significance threshold,
     and/or cap heritage per domain, so promotion is selective and meaningful.
4. **Make reincarnation strategic (Finding 4).**
   - Bequest should carry knowledge/skills/traits with real effects (unlock
     talents/activities, magnitude bonuses), and titles should grant gameplay
     perks — turning inheritance into a build that compounds across lives.
5. **Vary lifespan and widen agency (Finding 5).**
   - Distribute death age (illness/combat/old age), and re-tune §5 skip so the
     world runs 3–6 lives; consider shorter skips or longer playable spans so the
     player directly authors more of the timeline.
6. **Rebalance the 8 evaluation lenses (Finding 6).**
   - Separate exploration's contribution from academia; weight culture/mentoring/
     heritage as designed so non-military play is genuinely rewarded.

### Note for future playtests

The random auto-player cannot reveal whether a *skilled* strategy dominates. A
follow-up harness that plays fixed archetypes (pure-research, pure-commerce,
pure-military, educator) across seeds would test for a true dominant strategy and
measure whether talent choice actually changes outcomes.

---

## Verdict

The simulation **is a game in skeleton**: a reincarnator demonstrably leaves
traceable marks on a continuing world, with varied endings and an active
WildCard. But it is **not yet a satisfying game**: innovation over-dominates
outcomes, themes freeze mid-run, heritage is inflated, and reincarnation lacks a
strategic payoff. Findings 1–4 are the priorities before (or alongside) P4 AI
integration; AI narration would otherwise dress up a world whose underlying
dynamics are too convergent.
