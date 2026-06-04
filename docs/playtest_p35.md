# Balance Pass Results (P3.5)

**Goal:** fix the game-design problems found in `playtest_p5.md` so Chronicle
Forge works as a history-creation RPG. No AI used. Re-measured with the same
25-seed auto-player harness (seeds 1–25) before/after.

## Headline: before → after (25 seeds)

| Metric | P5 (before) | P3.5 (after) | Target | Result |
|---|---|---|---|---|
| Innovation as final theme | 48% (12/25) | **28% (7/25)** | reduce dominance | ✓ |
| Distinct dominant axes / world | 2.32 | **4.20** | more variety | ✓ |
| Single-axis dominance fraction | 0.85 | **0.48** | reduce freeze | ✓ |
| Heritage per world (avg) | 17.4 | **6.4** | 3–8 | ✓ (21/25 in band) |
| Heritage range | 4–27 | **1–8** | bounded | ✓ |
| Lives per world | 2 (fixed) | **4.0 (3–5)** | 3–6 | ✓ |
| Knowledge inherited (worlds) | 0/25 | **25/25** | inherit | ✓ |
| Death causes | choice only | **lifespan 83 / combat 17** | varied | ✓ |
| Wildcard archetypes igniting | inventor only | **5 archetypes** | diversified | ✓ |

### Ending distribution

| Ending | P5 | P3.5 |
|---|---|---|
| Arcane (innovation) | 11 | 7 |
| Golden | 5 | 6 |
| Mercantile | 2 | 5 |
| Warring | 1 | 4 |
| Theocracy | 3 | 2 |
| Empire | 1 | 1 |
| Collapse | 2 | 0 |

The single innovation attractor is broken; endings are far more even.

---

## Changes by priority

### Priority 1 — Reincarnation strengthened
- **Bequest** now derives **knowledge / skills / traits** from how a life was
  lived (evaluation thresholds), not just a title (`inheritance.py`).
- Inheritance **affects later actions**: technical lore → discovery magnitude &
  research evaluation; mentorship → education; commerce ledger → trade; martial
  skill → combat power; etc. (wired into `activity.py`, `discovery.py`,
  `combat.py`).
- **Lifespan distribution** (`draw_natural_span`) + reduced skip constants →
  lives now **3–5** (avg 4.0) instead of a fixed 2, with varied death causes.
- Result: knowledge inherited in **25/25** worlds; titles avg 3.28; cross-life
  causal events avg **48.8/world**. Reincarnation now compounds.

### Priority 2 — WildCard monopoly removed
- Seated **5 archetypes** (inventor / conqueror / prophet / merchant_prince /
  reformer), each pushing a different theme axis.
- **Ignition now requires player contribution** (≥2 fired player seeds in the
  axis domain) **and** a hot theme, at a lower base rate (0.5 → 0.25).
- Result: igniting archetypes spread across all five (inventor 12, conqueror 8,
  merchant 6, prophet 5, reformer 1). Which wildcard fires now depends on the
  player's focus — exactly the intended agency.

### Priority 3 — Heritage rarefied
- Composite promotion **gate** (reach ≥ 4, longevity ≥ 10, score ≥ 120) plus a
  **per-world cap** (top 8 by score; stable seed-derived ids).
- Result: avg **6.4** (was 17.4), range **1–8**, 21/25 in the 3–8 band. Heritage
  is now selective and meaningful.

### Priority 4 — Theme freeze relieved
- `compute_theme` rewritten as a **recent-event window** (8 years, recency-
  weighted) over the causal graph + faction power + ignited-wildcard push.
  Old events leave the window, so the theme **mean-reverts** when history calms
  and keeps moving while events occur.
- Added **faction wars** (rival high-power factions clash, emitting warfare
  events and draining both) and **NPC promotions** (emit governance events), so
  history keeps being made during the skip.
- Result: distinct dominants 2.32 → **4.20**; single-axis fraction 0.85 → **0.48**.

---

## Findings after the pass

1. **Core fantasy intact and stronger.** Cross-life causal events rose to ~49/
   world; every life still leaves a mark, now across 3–5 lives that build on each
   other through real inheritance.
2. **Innovation still slightly over-represented** (28% vs even ~17%). The
   inventor remains the most-ignited archetype (12/25), likely because research
   and tech discoveries are common activities. Acceptable, but watch it.
3. **A few worlds have only 1–2 heritages** (calm histories). This is reasonable,
   not a bug — not every world produces great legacies.
4. **Auto-player caveat still applies.** These numbers are under random play; a
   strategy-archetype harness is still the right next probe for dominant
   strategies (carried over from P5).

## Improvement candidates (not implemented)

- Slightly down-weight tech/research seed frequency, or raise the inventor's
  player-seed ignition requirement, to flatten the residual innovation tilt.
- Add inter-life talent continuity options so inheritance encourages (not forces)
  a build identity.
- Tune `HERITAGE_MAX_PER_WORLD` per world lifespan (8 fits 40-year dev; 200-year
  prod may warrant a higher cap or per-era caps).

## Verdict

The four P5 problems — innovation monopoly, theme freeze, heritage inflation,
shallow/fixed reincarnation — are resolved against their targets. Chronicle Forge
now reads as a **history-creation RPG**: varied endings, a living theme, a
compounding reincarnation build, and player-driven wildcards. Ready to proceed to
P4 (AI integration) on top of dynamics that are no longer over-convergent.

*Tests: 77 passing. All metrics from `simulate_world(seed)` over seeds 1–25.*
