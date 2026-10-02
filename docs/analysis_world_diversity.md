# Chronicle Forge — World Diversity Report

Status: **Measurement. No engine change made.** Analysis only; nothing in `src/`
was touched. Reproduce with
[`analysis/world_diversity/`](analysis/world_diversity/):

```
PYTHONPATH=src python3 docs/analysis/world_diversity/collect.py 1000   # 50 s → corpus.json
python3 docs/analysis/world_diversity/analyze.py                        # → report.json
```

Corpus: **1000 worlds**, seeds 1–1000, engine `0.1.0-p8-mvp`, `max_year=40`,
`mode=auto`, social memory off. No UI, no rendering, no art involved.

**On routing:** the brief suggested delegating bulk seed collection. A world
replays in 0.02 s, so the whole 1000-seed corpus took 50 s in one process —
delegating would have cost more than the run. Collection and analysis were done
directly; report formatting likewise, since the numbers are the deliverable.

---

## 0. The answer in three numbers

| | |
|---|---|
| **READ-ALIKE = 0.464** | Two randomly chosen worlds share **46 %** of every name, phrase and label a player can read. 25.5 shared strings out of a 55.1 union. |
| **EFFECTIVE DISTINCT WORLDS = 35.9** | Out of 1000. By coarse fingerprint there are 128 distinct worlds, and the single most common fingerprint covers **13.6 %** of the corpus. |
| **8 STRINGS APPEAR IN ALL 1000 WORLDS** | `Hollowfen` · `The Sunken Vault` · `Greywind Moor` · `Thornreach` · `House of the Iron Seat` · `Coin Concord` · `Ember Communion` · `Free Lanterns` |

**Why worlds look the same, in one sentence:**

> The generators do not *sample* — they *instantiate the entire catalogue*.
> Locations and factions have a pool of 4 and every world contains all 4.
> A pool the size of the sample produces exactly zero between-world variety.

That is a different diagnosis from "the pools are too small," and it changes
what to fix first.

---

## 1. Metric definitions

**READ-ALIKE** — expected Jaccard similarity between the sets of
*player-readable strings* of two random worlds, over 15 000 random pairs.
Readable strings are the eleven families a lens actually prints: place name,
location names, faction names, faction ideologies, NPC names, event phrases,
institution names, life titles, ending class, reputation sentiments, recognition
hints. `1.0` = the two worlds read identically. `0.0` = no word in common.

**POOL vs PER-WORLD** — `pool` is the number of distinct values across all 1000
worlds; `per_world` is the number one world shows. **`coverage = per_world/pool`
is the diagnostic**: coverage 1.0 means the world *is* the catalogue.

**EFFECTIVE DISTINCT WORLDS** — `exp(H)` over the distribution of coarse
fingerprints (ending × top-2 axes × life count × mark kinds × phrase count).
Answers "how many genuinely different worlds does a player experience?"

---

## 2. Heatmap — fixed / variable / dead

`pool` = distinct values in 1000 worlds · `k` = distinct values in one world ·
`H` = normalised entropy · `top` = share of the most common value.

### ⬛ DEAD — the field exists in the schema and is empty in all 1000 worlds

| Field | Max across corpus |
|---|---|
| `CausalNode.location_id` | **0** — no event is ever attached to a place |
| `NPC.lineage.lineage_id` | **0** — the dynasty system produces nothing |
| `NPC.traits` | **0** |
| `NPC.goals` | **0** |
| `NPC.desires` | **0** |
| `LifeSummary.notable_events` | **0** |
| `LifeSummary.heritage_created` | **0** |

Seven fields carry no information whatsoever. Three of them —
`location_id`, `lineage`, `notable_events` — are exactly the fields the
presentation layer keeps reaching for and finding empty.

### 🟥 FIXED — one value, or the whole pool in every world

| Feature | pool | k | coverage | Reality |
|---|---|---|---|---|
| place name | **1** | 1.00 | — | Every world is **Hollowfen** |
| location name | 4 | 4.00 | **1.000** | The same four places, every time |
| location type | 3 | 3.00 | **1.000** | |
| location theme | 2 | 2.00 | **1.000** | |
| faction name | 4 | 4.00 | **1.000** | The same four factions, every time |
| faction type | 4 | 4.00 | **1.000** | |
| faction ideology | 4 | 4.00 | **1.000** | |
| npc tier | 2 | 2.00 | **1.000** | |
| span | **1** | — | — | 40 years, all 1000 |

### 🟧 NEAR-FIXED — a pool exists but one value swamps it

| Feature | pool | k | top | Reality |
|---|---|---|---|---|
| institution kind | 4 | 1.03 | **0.988** | 4 kinds exist; 98.8 % are `institution` |
| heritage type | 4 | 1.03 | **0.988** | same |
| world shape axis | 3 | 1.03 | **0.970** | |
| ending class | 7 | 1.00 | **0.853** | `Imperial Age` 853 / `Warring` 80 / `Golden` 39 / `Arcane` 11 / `Mercantile` 8 / `Theocratic` 6 / `Apocalyptic` 3 |
| recognition hint | **2** | 1.01 | 0.856 | Only two sentences exist in the whole game |
| reputation sentiment | **2** | 0.88 | 0.823 | Only two |
| life dominant axis | 6 | 1.43 | 0.866 | |

### 🟩 VARIABLE — actually generating difference

| Feature | pool | k | H | Note |
|---|---|---|---|---|
| **npc name** | **100** | 9.53 | **0.999** | **The one healthy generator in the engine.** Copy this design. |
| institution name | 31 | 6.93 | 0.683 | Combinatorial `{Academy, Doctrine, Order…} × {of the Open Road…}` — only ~10 suffixes exist |
| life title | 8 | 3.23 | 1.000 | `The {talent} of Hollowfen` — 8 talents × 1 place |
| life talent | 8 | 3.23 | 1.000 | Clean |
| event phrase | **8** | 4.74 | 0.480 | `the order of rule shifts` is **68.5 %** of all 54 758 events |
| event scale | 3 | 2.91 | 0.532 | |
| seed domain | 8 | 4.99 | 0.483 | |
| dominant-axis path | 948 | 1.00 | 0.994 | Varies richly — and is never printed to the player |

**The eight event phrases, with their real frequencies:**
`the order of rule shifts` 37 536 · `war breaks out` 11 406 ·
`a monument rises` 1 980 · `a school takes hold` 1 219 ·
`the faith takes root` 1 063 · `trade flourishes` 591 ·
`a new craft spreads` 571 · `a discovery echoes outward` 392.

A 40-year world prints ~55 events drawn from **eight** sentences, two of which
account for 89 % of them.

---

## 3. Where the sameness comes from

Decomposition of the 25.5 strings two random worlds share:

| Family | Share of the sameness | Strings per pair |
|---|---|---|
| institution name | **18.7 %** | 4.8 |
| location name | **15.7 %** | 4.0 (always all four) |
| faction ideology | **15.7 %** | 4.0 (always all four) |
| faction name | **15.7 %** | 4.0 (always all four) |
| event phrase | **13.6 %** | 3.5 |
| life title | 5.1 % | 1.3 |
| place name | 3.9 % | 1.0 (always `Hollowfen`) |
| npc name | 3.5 % | 0.9 |
| recognition hint | 3.0 % | 0.8 |
| ending class | 2.9 % | 0.7 |
| reputation sentiment | 2.2 % | 0.6 |

**Locations + factions + place = 51 % of all sameness, and none of it is
generated at all** — those thirteen strings are constants wearing the costume of
a world generator.

### Which families currently *create* difference

Removing a family from what the player reads and re-measuring:

| Remove | READ-ALIKE becomes | Meaning |
|---|---|---|
| **npc names** | 0.464 → **0.669** (+0.205) | NPC names are carrying almost all the felt difference single-handed |
| life titles | 0.464 → 0.486 (+0.022) | Mildly differentiating |
| lens strings | 0.464 → 0.460 (−0.004) | Neutral |
| institution names | 0.464 → 0.452 (−0.013) | Net *sameness* |
| event phrases | 0.464 → 0.451 (−0.013) | Net sameness |
| place name | 0.464 → 0.451 (−0.013) | Net sameness |
| locations | 0.464 → 0.422 (−0.042) | Net sameness |
| **factions** | 0.464 → **0.373** (−0.091) | **The single largest pure-sameness contributor** |

Only two of eight families make worlds feel different. Six actively make them
feel the same.

---

## 4. Structural sameness — the part vocabulary cannot fix

Even with perfect names, every world would still be:

| | |
|---|---|
| 40 years | 1000 / 1000 |
| 3–5 lives | mean 3.9, p90 = 4 |
| ~55 events | p50 54 |
| 8 marks | p50 8, and **all of them `institution`** |
| Governance-dominated | shape axis one value in 97 % |
| `Imperial Age` | 85.3 % |

And the premise "each of your lives leaves a mark" does not hold:

| | |
|---|---|
| Marks planted by **life 1** | **76.0 %** |
| by life 2 | 21.6 % |
| by life 3 | 2.4 % |
| by life 4+ | 0 % |
| Worlds where **every** mark shares one founder | **50.3 %** |
| Worlds where any life after the first plants a mark | 505 / 1000 |

**In half of all worlds, your later lives leave nothing.** That is a Core
Experience defect, not a diversity defect — Success Criterion 4 and the
"authorship" beat of the emotional arc both assume later lives plant
deliberately.

**Healthy by contrast:** `trace_depth` p50 = 31 (min 8, max 60) and recognitions
p50 = 8. The **causal machinery is working**; it is the vocabulary and the
casting that are not. The D-5 seed floor (`marks ≥ 4 ∧ trace_depth ≥ 20`) admits
**942 / 1000** seeds — the M-1 finding of abundance holds at 25× the sample.

---

## 5. Improvement ROI

Modelled as: a family drawing `k` distinct items per world from a pool `P` shares
about `k²/P` items with another world; raising `P` scales that family's shared
mass by `P/P′`. Predictions are calibrated against the measured shared mass.

### Single changes, ranked

| Rank | Change | Kind | READ-ALIKE | Δ | Cost |
|---|---|---|---|---|---|
| **1** | **Stop instantiating the catalogue** — draw 4 of 40 locations and 4 of 40 factions per world | structural + data | **0.223** | **−0.241** | **Lowest.** A name table plus a sampling call |
| 2 | institution names 31 → 600 (widen the suffix list; the combinator already exists) | data | 0.352 | −0.112 | Very low |
| 3 | institution kind actually varies (4 kinds exist, 98.8 % is one) | structural | 0.374 | −0.091 | Low |
| 4 | event phrases 8 → 120 | writing | 0.381 | −0.083 | Medium (112 sentences to write) |
| 5 | bind events to a location (8 phrases × 4 places = 32 effective, **zero new writing**) | structural | 0.397 | −0.068 | Low |
| 6 | life titles 8 → 600 | data | 0.429 | −0.035 | Free if #1 ships — the title is `The {talent} of {place}` |
| 7 | place name 1 → 200 | data | 0.437 | −0.028 | Trivial |
| 8 | recognition hints 2 → 40 | writing | 0.443 | −0.021 | Low |
| 9 | npc names 100 → 400 | data | 0.445 | −0.019 | Low — already the healthiest generator |
| 10 | reputation sentiments 2 → 40 | writing | 0.449 | −0.016 | Low |
| 11 | ending classes 7 → 12 | design | 0.454 | −0.010 | Medium — and 85 % skew is the real problem, not the count |

### Bundles

| Bundle | READ-ALIKE | Δ | Comment |
|---|---|---|---|
| **A — sample locations + factions (4 of 40) + bind events to places** | **0.177** | **−0.288** | Two data tables and one field assignment. **62 % of the sameness, gone.** |
| B — A + institution names 600 + kind varies | 0.101 | −0.363 | |
| C — B + place names 200 + event phrases 120 | 0.075 | −0.390 | |
| D — every nameable thing unique per world | 0.000 | −0.464 | Theoretical floor |

### The ranking in one line

> **Sampling beats writing.** The top three changes are all "make the generator
> choose from a larger table" — no prose, no engine architecture. Writing 112 new
> event sentences ranks *fourth*, below three changes that are an afternoon each.

---

## 6. Recommended sequence

1. **W-1 — Sample, don't instantiate.** Location and faction name tables of ~40
   each; each world draws 4. Also derives `place` (the world's name) from the
   drawn locations, which fixes life titles for free. *Δ ≈ −0.27 combined.*
2. **W-2 — Bind events to locations.** Set `CausalNode.location_id` at creation.
   Costs no writing, quadruples effective event vocabulary, revives a dead
   field, and unlocks every "where did this happen" surface the presentation
   studies have been blocked on. *Δ ≈ −0.07.*
3. **W-3 — Make heritage kinds actually vary.** Four `HeritageType` values exist
   and 98.8 % of marks are one of them. This is the difference between "you
   founded eight guilds" and "you founded a guild, a shrine, a road and a
   library." *Δ ≈ −0.09, and it is the biggest qualitative gain in the list.*
4. **W-4 — Widen the institution suffix table** (~10 → ~60). *Δ ≈ −0.11.*
5. **W-5 — Fix mark attribution across lives.** Not a diversity fix; a Core
   Experience fix. Half of all worlds have every mark planted by one life.
6. **W-6 — Event phrases 8 → ~40**, and flatten the 68.5 % skew on
   `the order of rule shifts`. The most expensive item, and correctly last.

Items 1–4 are, together, roughly one to two days of work and take READ-ALIKE
from **0.46 to ~0.10**.

---

## 7. What this analysis does not prove

- **READ-ALIKE is a string metric.** It measures whether two worlds use the same
  words, not whether they tell different stories. §4 is the reminder: at
  READ-ALIKE 0.07 every world would still be 40 years, 3–5 lives, 8 institutions
  and an Imperial Age.
- **The ROI model is analytic**, not simulated. `k²/P` is calibrated against
  measured shared mass but assumes independent uniform draws; a generator with
  weighting will land somewhere above the predicted value.
- **`auto` mode only.** Player inputs are not exercised, so any diversity that
  comes from *choices* is invisible here. Worth a follow-up run over scripted
  input variants.
- **Nothing here says the engine is bad.** `trace_depth` p50 = 31, 830 causal
  edges per world, 942/1000 seeds passing the D-5 floor: the causal simulation is
  strong. The failure is entirely in **naming, casting, and typing** — the
  cheapest layer to fix.
