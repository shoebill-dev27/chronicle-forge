# Core Loop Migration Audit — from "3-choice juncture + CausePath" to "live a life, find the trace"

Status: **INVESTIGATION ONLY. No code written. 0 files changed under `src/`, `tests/`, `unity/`.**
Base: `design/v1` @ `5dfe350`. Method: source reading + two live engine runs (read-only replay of seeds 1 and 42).
Scope: what the current codebase assumes, what survives the new core loop, what must go, what is missing.

---

## 1. Executive summary

**Six findings decide the migration.**

**F-1 — The causal engine is the asset; the gameplay loop is the liability.**
`causal.py` / `generation.py` / `macro.py` / `heritage.py` hold a real, cycle-checked
DAG of seeds → events → heritage with multi-cause edges and transitive reach. That
truth layer never mentions "juncture", "option" or "choice". It is reusable almost
unchanged. Everything above it — `opportunity.py`, `execution.py`, `play/gate.py`,
`play/render.py`, `play/beats.py` — exists to turn that truth into *three ranked
choices and a confirmable attribution*, which is the loop being retired.

**F-2 — "A life" today is 2–7 world-years ending at age ~20, not 80.**
`config.NATURAL_SPAN_MIN/MAX = 2/7` (world-years of play), `life.START_AGE = 16`,
`TURNS_PER_YEAR = 4`. Measured: seed 1 → lives of 6/6/4 years, dying at 22/22/20;
seed 42 → 2/6/6/2 years, dying at 18/22/22/18. `LIFESPAN_CAP = 80` exists but is
never reached by any run. A life is ~20 actions long. The new loop's 80-year life is
a **30× change in the time model**, not a constant tweak.

**F-3 — The 200-year world is unreachable and actively blocked.**
`config.PROD_WORLD_MAX_YEARS = 200` is defined and **never used**. Every entry point
hardwires `DEV_WORLD_MAX_YEARS = 40` (`worldgen.py:110`, `app/services.py:84`,
`play/adapter.py:87`), and `persistence/load.py:42` *refuses to replay* any recipe
whose `max_year != 40`. The horizon is a persistence gate, not a parameter.

**F-4 — The 10-year reincarnation gap contradicts the current skip rule.**
`timeskip.compute_skip_years` returns `clamp(base(age) + seed_bonus, MIN_SKIP=2,
MAX_SKIP=8)` — variable, and *coupled to how much the player planted*. A fixed 10
years is simpler and deletes that coupling, but the coupling is the current delayed-
reward design (`docs/design.md` §5). This is a deliberate design deletion, not a
constant change.

**F-5 — NPC autonomy, relationships and possessions are effectively absent.**
`npc.step_npc` / `npc.choose_intent` are **dead code** — exported in `__init__.py`
but called from nothing in the run loop. The only NPC motion is
`macro.step_npcs_lifecycle` (age +1, old-age death roll, ambitious→"leader"
promotion). Measured over 40 years and 3–4 lives: **2 relation entries and 5 memories
in the entire world**, 10/10 NPCs still alive at the end. There is no ownership, no
work, no membership, no teaching, no descendants of NPCs (`Lineage` exists on the
model and is never populated by gameplay).

**F-6 — The player has no place and no continuity of action.**
`Life` has no `location_id`; `perform_activity` takes `(category, target_id)` and
costs exactly 1 turn (`ACTIVITY_TURN_COST = 1`). There is no routine, no duration, no
repetition-with-effect: repeating an act plants a *second independent seed*. Measured
activity mix, seed 42: `{politics: 52, combat: 10}` out of 62 acts — the tension
scorer collapses the 8 categories to ~2 in practice.

**The shape of the migration.** Keep the causal DAG and the deterministic-replay
spine. Retire the entire juncture/option/recognition/CausePath presentation stack.
Rewrite the micro loop (time, action, place). Add, as genuinely new domain model,
everything about *other people persisting and acting*: relationship state that lasts,
NPC goals that execute, membership, ownership, transmission, and evidence-as-artifact.
Roughly **~35 % of `src/` is reusable as-is, ~25 % reusable internally with a changed
contract, ~40 % retires or is rewritten.**

---

## 2. Current architecture map

```
                     ┌─────────────────────────────────────────────┐
  TRUTH (rules)      │ worldgen.py   → World(locations, factions,   │
                     │                 npcs, wildcards, player)     │
                     │ activity.py   → perform_activity() ──┐       │
                     │ discovery.py  → explore_dungeon() ───┤       │
                     │ combat.py                            ▼       │
                     │                                 CausalSeed   │
                     │ generation.py → fire_seeds → CausalNode      │
                     │ causal.py     → CausalGraph (DAG, cycle-safe)│
                     │ heritage.py   → promote → HeritageNode (≤8)  │
                     │ macro.py      → advance_year / time_skip     │
                     │ life.py       → begin_life / end_life        │
                     │ theme.py, memory.py, inheritance.py          │
                     └─────────────────────────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────────────┐
  SELECTION (P6)     │ opportunity.py → 3–5 tension-ranked          │
                     │                  Opportunity per turn        │
                     │ execution.py   → Opportunity → one engine    │
                     │                  verb call (ExecutionOption) │
                     └──────────────────┬──────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────────────┐
  ASKING (P8)        │ play/gate.py     → is this turn a juncture?  │
                     │ play/session.py  → life → turns → death →    │
                     │                    skip → next life          │
                     │ play/render.py   → turn_screen (top-3 only)  │
                     └──────────────────┬──────────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────────────┐
  BEAT STREAM (I-1b) │ play/beats.py → Rebirth/Juncture/Outcome/    │
                     │   Death/Years/Aftermath/Closing              │
                     │   + Option, Recognition, Mark, CausePath     │
                     └──────────────────┬──────────────────────────┘
                     ┌──────────────────┴──────────────────────────┐
  CLIENTS            │ client/bridge.py + web/  ·  client/fixture   │
                     │ → unity/ (B+C production, D/E/F research)    │
                     └─────────────────────────────────────────────┘

  SIDE: reporting/ (11 lenses, id-free view records, 8 goldens)
        persistence/ (Recipe = seed+max_year+mode+inputs; replay)
        client/state.py (BookState: reveal set bound to canonical_hash)
```

### Measured behaviour (read-only replay, `max_year = 40`)

| | seed 1 | seed 42 |
|---|---|---|
| lives in the world | 3 | 4 |
| life span (world years) | 6, 6, 4 | 2, 6, 6, 2 |
| age at death | 22, 22, 20 | 18, 22, 22, 18 |
| death cause | LIFESPAN ×3 | LIFESPAN ×4 |
| acts per life | 22, 24, 16 | 6, 24, 24, 8 |
| activity mix (all lives) | politics 47, combat 10, construction 2, religion 1, research 1, commerce 1 | politics 52, combat 10 |
| NPCs alive at end | 10 / 10 | 10 / 10 |
| **relation entries in world** | **2** | **2** |
| memories | 5 | 5 |
| seeds / events / heritage | 63 / 73 / 8 | 63 / 60 / 8 |
| locations / factions | 4 / 4 | 4 / 4 |

---

## 3. Classification — KEEP / CHANGE / INTERNAL / REWRITE / RETIRE

Legend: **A** KEEP AS-IS · **B** KEEP CONCEPT, CHANGE CONTRACT · **C** REUSE INTERNAL ONLY · **D** REWRITE · **E** RETIRE

### 3.1 Truth layer

| Subsystem / type | Class | Evidence & reason |
|---|---|---|
| `causal.CausalGraph` (DAG, `add_edge` cycle check, `ancestors`, `descendants`) | **A** | `causal.py:56-80` — no gameplay vocabulary at all. The new loop still needs "why did this happen" internally. |
| `models.CausalNode` / `CausalEdge` / `CausalEdgeKind` | **A** | `models.py:250-265`. Multi-cause already supported (`caused_by: list[CausalEdge]`). |
| `models.CausalSeed` | **B** | `models.py:233-247`. The *concept* (a latent cause that matures) survives. The contract must change: today one act = one seed (`activity.py:81-89`). Duration/repetition needs either seed reinforcement (magnitude accretion) or a new `Practice` aggregate — see §5. `planted_by_life_id` must stay (engine truth) but must never reach a surface. |
| `generation.fire_seeds` / `generate_events` | **B** | `generation.py:15-90`. Keep the firing mechanism; the AMPLIFY co-cause rule (`prior.domain == seed.domain` links *every* prior node of the same domain) produces dense, low-meaning edges and needs re-specifying for a 200-year graph. |
| `heritage.py` promotion + scoring | **C** | `heritage.py:28-116`. Reach/longevity is a good internal salience metric. But `HERITAGE_MAX_PER_WORLD = 8` and the `-heritage_score` sort (`heritage.py:114-116`) mean life 1 sweeps the slots (W-1 RC-5: 76 % of marks). Under the new loop "heritage" stops being a player-facing noun and becomes an internal ranking for *what evidence exists in the world*. |
| `macro.advance_year` | **B** | `macro.py:261-292`. Correct shape (fire → events → actors → theme → promote). Must gain: NPC action step, relationship decay, institution step. |
| `macro.time_skip` | **D** | `macro.py:294-331`. Skip length is derived from the dead life's pending seeds. New loop wants a **fixed 10 years**; and 10 years of *real* world simulation (NPC lives, transmission) is a different job from today's 2–8 year fast-forward. |
| `timeskip.compute_skip_years` | **E** | `timeskip.py:18-33`. Its whole purpose is the variable, seed-coupled skip. A constant makes it a one-liner. |
| `life.begin_life` / `advance_time` / `end_life` | **D** | `life.py:26-52,130-144`. `START_AGE = 16`, `TURNS_PER_YEAR = 4`, aging by turn count. An 80-year life with routines needs a year-based clock with variable action granularity, not 4 turns/year. |
| `life.draw_natural_span` | **D** | `life.py:56-61` returns 2–7 *world years*. New loop needs an actuarial lifespan (~80 cap) plus per-year hazard from world state and behaviour. |
| `models.Life` (`turns`, `activity_log`, `evaluation`, `summary`) | **B** | `models.py:198-213`. The record-of-a-life concept survives. `Evaluation`'s 8 lenses (`models.py:172-183`) are a scoring abstraction for the old "how impressive was this life" framing; under the new loop they become at best internal. |
| `activity.perform_activity` | **D** | `activity.py:62-119`. One call = one seed + evaluation + optional memory + 1 turn. New loop needs Action(verb, target, place, duration) with relationship effects and no automatic seed. |
| `profiles.ACTIVITY_PROFILES` (8 categories) | **B** | `profiles.py:25-84`. A good static-table pattern; the 8 categories are domain-scale (POLITICS, COMMERCE) not life-scale (teach, help, quarrel, work). Keep the table shape, replace the rows. |
| `discovery.explore_dungeon` | **E** | `discovery.py:37-62`. Dungeon-clearing as a seed source belongs to the old JRPG framing. |
| `combat.py` | **E** | 46 lines; combat power + per-year death roll. Death risk stays, this implementation does not. |
| `memory.form_memory` | **B** | `memory.py:20-54`. Right idea (structured memory updates a directed `Relation`). Only 5 memories per 40-year world today because it is called from one place (`activity.py:110-118`). Must become the general effect of every interaction. |
| `models.Relation` (affinity/trust/fear) | **B** | `models.py:53-56`. Keep the three axes; add duration/last-seen/kind so a relationship can *persist and decay*. Today only 2 entries exist world-wide. |
| `models.NPC` / `Personality` / `Lifecycle` / `Lineage` | **B** | `models.py:59-95`. `Lineage.parent_ids` and `generation` are declared and never written by gameplay — the schema is ready, the behaviour is missing. |
| `npc.step_npc` / `choose_intent` | **E** | `npc.py:16-34`. **Dead code**: exported (`__init__.py:30,78`) and called nowhere. Its "pick an argmax drive and store it in `goals`" is not autonomy. |
| `macro.step_npcs_lifecycle` | **D** | `macro.py:230-257`. Ages NPCs and promotes the ambitious. Needs to become real NPC turn-taking. |
| `macro.step_factions` | **C** | `macro.py:191-228`. Power drift + war roll. Usable as a coarse institution step under a real organisation model. |
| `wildcards` (model + `macro.step_wildcards`) | **E** | `models.py:304-320`, `macro.py:138-169`. Named "great figures" on rails whose trajectory the player nudges. The new loop makes every NPC potentially that. |
| `powers.py` / `PlayerPowers` (imprint/foresight/bequest/manifest) | **E** | `models.py:140-147`, `powers.py`. Explicit meta-powers contradict "you are one person living". |
| `inheritance.py` / `Player.inherited` | **E** | `inheritance.py:33-…`, `models.py:149-160`. Mechanical cross-life bonuses ("a build that compounds") is exactly the "the game tells you your past life matters" the new design removes. |
| `theme.py` / `WorldTheme` | **C** | Internal world-mood signal; fine as an input to NPC/institution behaviour, not as a player-facing axis chart. |
| `worldgen.generate_world` | **D** | `worldgen.py:110-196`. Produces 1 village + 1 dungeon + 4 factions + 10 NPCs + wildcards, all hardcoded (W-1 RC-1). The slice needs 1 town / 3 locations / 3 NPCs / 1 organisation with real roles. |
| `rng.DeterministicRNG` / `ids.py` | **A** | Substream-based determinism; unchanged need. |
| `config.py` | **B** | Every constant re-derives. `PROD_WORLD_MAX_YEARS = 200` currently dead. |

### 3.2 Selection / asking layer

| Subsystem | Class | Evidence & reason |
|---|---|---|
| `opportunity.py` (tension scoring, `select_top_k`, diversity caps) | **C** | 455 lines, `opportunity.py:285-428`. As a *player-facing menu generator* it retires. As an internal **salience** function — "which of the world's threads is worth surfacing as an encounter / a rumour / an available job" — the maths is reusable. Note the measured collapse to politics/combat; it is not neutral today. |
| `execution.py` (`ExecutionOption`, `expand_options`, `play_turn`) | **E** | `execution.py:90-303`. Its entire reason for being is "turn an Opportunity into one of the 8 engine verbs so a 3-choice menu can be actionable". |
| `play/gate.py` `JunctureGate` (`T_ASK=0.85`, `ASKS_PER_LIFE=6`, cooldown) | **E** | `play/gate.py:25-48`. The juncture is the retired unit. |
| `play/render.py` `turn_screen` / `_top3` / `option_index_for_choice` | **E** | `play/render.py:126-226`. `_top3` hard-trims to three (`render.py:132`). |
| `play/render.py` `death_passage` / `aftermath` / `closing_page` / `skip_transition` | **B** | `render.py:264-487`. The *beats* survive (death, years passing, return, ending); their content is written around marks/heritage/founder ordinals and needs rewriting. |
| `play/render._former_self_line` + `recognizable_heritage` | **E** | `render.py:96-172`. This is literally "the game tells you a past self is here". |
| `play/session.run_human_world` / `_live_one` | **D** | `play/session.py:64-180`. The outer shape (world → lives → skip → ending) survives; the inner turn loop is built around gate-decides-then-prompt. |
| `autoplay.simulate_world` | **B** | Needed as the determinism harness; its policy layer changes with the action model. |

### 3.3 Beat / presentation contracts

| Contract | Class | Evidence & reason |
|---|---|---|
| `play/beats.py` `Juncture` + `Option` | **E** | `beats.py:64-88,227-238`. `Option.n` is "the displayed number (1..3)". |
| `beats.Outcome` (sealed act, `option`, `label`) | **E** | `beats.py:239-263`. "Sealed act" is the retired unit of commitment. |
| `beats.Recognition` (`founder_life`, `sealed_act`) | **E** | `beats.py:90-107`. The explicit "a former self met at this juncture" payload. |
| `beats.CausePath` / `CauseStep` | **E** *(player-facing)* / **C** *(engine)* | `beats.py:156-202`. The DAG walk stays inside the engine; shipping the resolved origin to a client is precisely what the new design forbids. |
| `beats.Mark` (`founder_life`, `reach`, `longevity`) | **E** | `beats.py:127-146`. A named seed with an owner to be uncovered. |
| `beats.Rebirth` / `Death` / `Years` / `Aftermath` / `Closing` | **B** | `beats.py:217-336`. The five non-choice beats survive as a stream shape; fields change. |
| `beats.BeatRecorder` + `stream()` (observer seam) | **A** | `beats.py:477-865`. The "engine tells, never asks; observer cannot mutate" seam is exactly right and is independent of what the beats contain. |
| `client/bridge.py` `BookBridge` | **D** | 166 lines; a page driver over the beat stream. |
| `client/web/` (`book.js` 1.9k lines, `strings.js`, `time.js`) | **E** | The DVS book UI: shelf → juncture → seal → death → years → return → investigate → confirm. |
| `client/fixture.py` (Unity DVS fixture) | **E** | `fixture.py:1-25` — serialises `beats.to_dict()` + `discovery.locked`. Both halves retire. |
| `client/state.py` `BookState` / `Reveal` / `canonical_hash` | **B** | `state.py:49-233`. The *idea* — "what the player has personally uncovered is client state, keyed to a world identity, monotone, and reading earns nothing" — is more important under the new design, not less. The *unit* changes from "a confirmed attribution coordinate" to "a piece of evidence examined / an inference the player recorded". |
| `unity/` B+C production client, D/E/F research concepts | **E** *(as DVS clients)* / **C** *(as UI research)* | All are built on `DvsFixture` + `Phase{Shelf…Trace}`. The reference corpus and visual grammar (`docs/research/ui_reference/`) remain valid; the concept implementations do not. |

### 3.4 Persistence

| Subsystem | Class | Evidence & reason |
|---|---|---|
| `persistence/schema.Recipe` (`seed + max_year + mode + inputs`) | **B** | `schema.py:31-54`. "The recipe is the save" holds only while the run is byte-deterministic from an ordered *line* stream. With free-form daily actions the input alphabet explodes but the principle survives — as long as every player act is a discrete, serialisable command. **This is the single most valuable architectural property in the repo; the new loop must be designed to preserve it.** |
| `persistence/replay.py`, `record.py`, `save.py`, `load.py` | **B** | Mechanism survives. `load.py:42` (max_year must equal 40) must become a real parameter. |
| `persistence/export.py` (transcript) | **B** | Contents change with the beats. |
| `EngineVersionMismatch` refusal | **A** | `schema.py:19-23`. Right policy; will fire once on migration, as intended. |
| `client/state.canonical_hash` | **A** | `state.py:65-76`. Binds player knowledge to one world identity. Unchanged need. |

### 3.5 Reporting lenses

| Lens | Class | Reason |
|---|---|---|
| `world_model.py`, `observatory.py`, `lineage.py`, `heritage_table.py`, `heritage_explorer.py` | **C** | Read-models over world truth; useful as *authoring/QA* views. As player surfaces they show exactly the attribution the new design hides. |
| `timeline.py`, `character.py`, `narrative.py` | **B** | Year-ordered events, per-person biography, thread narration: these are the *raw material of in-world historical sources*. Their id-free, frozen-record contract is directly reusable for "a chronicle a scribe wrote". |
| `legacy.py` (P17 Fingerprint) | **E** | `legacy.py` computes a 5-dimension fingerprint of *the player's* lives — a direct "here is what you were" readout. |
| `investigation.py` (P18) | **E** *(as designed)* | Not implemented (17 RED tests). Its contract (`CauseChain`: event → origin life → action → steps) is the answer-display the new design replaces with evidence gathering. |
| `experience.py`, `story_md.py`, `chronicle_md.py`, `summary_md.py` | **B** | Prose composition over truth; "Rules own truth, AI owns prose" survives. `experience.py:118` ("In all, your choices fell across N lives") is the sentence the new design forbids. |
| `labels.py` | **B** | Phrase tables; W-1 RC-2 already identifies the 31-name pool problem. |
| `causal_dot.py`, `gallery.py`, `build.py` | **C** | Debug/authoring output. |
| `ai/` (`client.py`, `historybook.py`, `ending_narrator.py`) | **A** | Prose-only, side-channel, non-canonical. Unchanged under the new design. |

---

## 4. Semantic conflicts (concrete, with code)

| # | New-loop premise | Current code says | Conflict |
|---|---|---|---|
| **SC-1** | A life is up to 80 years of living | `life.py:22` `START_AGE=16`; `config.py:31-32` span 2–7 world-years; measured deaths at 18–22 | The word "life" means ~20 actions over ~5 years. Every downstream constant (maturation 5–10 y, `HERITAGE_MIN_LONGEVITY=10`, skip 2–8 y) is calibrated to that. |
| **SC-2** | Reincarnation exactly 10 years after death | `timeskip.py:25-33` clamp(2, 8), seed-coupled | Contradicts the delayed-reward coupling; also 10 > current MAX_SKIP. |
| **SC-3** | World runs 200 years | `PROD_WORLD_MAX_YEARS` unused; `load.py:42` refuses `max_year != 40` | The horizon is not a parameter today. At 200 years with 80-year lives the world holds ~2–3 player lives, not 3–4 per 40 years. |
| **SC-4** | Player lives in a place | `Life` has no location; `CausalNode.location_id` is `Optional` and never set (W-1 RC-4: dead in 1000/1000 worlds) | No spatial axis exists anywhere in gameplay or truth. |
| **SC-5** | Action + Relationship + Duration is the unit | `activity.perform_activity(category, target_id)` costs 1 turn and plants 1 seed; repeating plants a *second* seed | Duration and repetition have no representation; two teachings of one student are two unrelated causes. |
| **SC-6** | NPCs live autonomously | `npc.step_npc` dead; `macro.step_npcs_lifecycle` = age + death roll + one promotion rule | NPCs are props. Measured: 10/10 alive after 40 years, 2 relation entries world-wide. |
| **SC-7** | Relationships accumulate and matter | `Relation` only written by `memory.form_memory`, called from one branch of `perform_activity` | Relationship state is technically present and practically empty. |
| **SC-8** | Traces are encountered by chance, never explained | `render._former_self_line` (`render.py:96`), `beats.Recognition`, `beats.CausePath`, `legacy.py`, P18 `CauseChain` | Four separate surfaces exist whose job is to *state* the attribution. |
| **SC-9** | Investigation = gathering sources, people, hearsay, objects | `beats.CausePath` ships the resolved origin (`origin_life`, `origin_year`, `origin_act`, `origin_sealed`) and the client walks it | There is no artifact, document, witness or testimony type in the model. `Discovery` is a dungeon loot record (`models.py:286-291`). |
| **SC-10** | Propagation individual → NPC → organisation → institution → culture | `Faction` (id/type/name/power/ideology/relations) and `WorldTheme` axes | No membership, no rule/norm, no adoption or transmission mechanism. `HeritageType.INSTITUTION` is a *label on a seed*, not an institution. |
| **SC-11** | Player-known facts ≠ engine truth | `client/state.BookState` (reveals) is the only place this distinction lives, and it is client-side only | The engine has no model of "what this player character could plausibly know". Beats currently carry full truth and rely on the surface to self-censor (D-01/D-03). |
| **SC-12** | Death can come early from the world | `config.py:33` a flat 6 %/year combat roll; measured: 0 non-LIFESPAN deaths in seeds 1 and 42 | Death risk is a constant, not a consequence of how the player lived or what the world is doing. |
| **SC-13** | The player is one ordinary person | `PlayerPowers` (imprint/foresight/bequest/manifest), `Player.inherited` mechanical bonuses | Explicit reincarnator superpowers. |
| **SC-14** | Determinism via recipe replay | `Recipe.inputs: list[str]` — one reader line per ask, ~6 asks/life | Still viable, but the input stream becomes far denser. **Not a conflict — a constraint to design against.** |

---

## 5. Missing domain model

Split by whether existing structure can carry it.

### 5.1 Representable today with a changed contract (no new aggregate)

| Concept | Carrier | Change needed |
|---|---|---|
| **Action** (verb + target + place + duration) | `ActivityRecord` (`models.py:166-169`) | Add `target_id`, `location_id`, `duration_years`, `outcome`. Today it holds only `(category, world_year, seed_id)`. |
| **Relationship** | `Relation` + `NPC.relations` | Add `kind` (mentor/rival/employer/kin), `since_year`, `last_interaction_year`, decay. Mechanism exists (`social_memory_l2.decay_world_one_year`), coverage does not. |
| **Death risk / variable lifespan** | `life.draw_natural_span` + `DeathCause` | Replace the 2–7 draw with age-hazard + world-hazard + behaviour-hazard. `DeathCause` enum already exists. |
| **Global 200-year clock** | `World.max_year`, `config.PROD_WORLD_MAX_YEARS` | Make it a real parameter; lift `load.py:42`. |
| **Fixed 10-year gap** | `timeskip` | Constant; but the 10 years must *simulate*, not fast-forward. |
| **Descendants / inheritance of NPCs** | `Lineage.parent_ids`, `generation` (declared, never written) | Write them. Birth/parentage events during the skip. |

### 5.2 Genuinely new domain model required

| Concept | Why nothing today carries it |
|---|---|
| **Activity / routine (continuation)** | No state persists between acts. A routine is "this person does X at place Y with people Z, every year, until something stops it" — needs an entity with a lifetime, not a log row. |
| **Duration / repetition as a causal quantity** | `CausalSeed.magnitude` is set once at plant time (`activity.py:73-79`). Reinforcing a seed, or a cause that strengthens with years of practice, has no representation. |
| **NPC goal + NPC autonomous action** | `NPC.goals: list[str]` is written only by the dead `step_npc`. An NPC needs the same Action vocabulary as the player, a policy, and a per-year turn inside `advance_year`. |
| **Livelihood / work** | No occupation semantics beyond `Lifecycle.occupation: str` ("villager"/"leader") and no resources. |
| **Ownership / possessions / objects** | Nothing. Objects are the *primary evidence carrier* in the new design ("this tool, this book, this building") and do not exist. |
| **Organisation membership** | `Faction` has `power` and `relations` but no member list, no roles, no joining/leaving. |
| **Knowledge / skill as transmissible content** | `Player.inherited` is a tag list on the *player*; there is no "what this person knows" on NPCs, and no teach→learn edge between two people. |
| **Social propagation** | `CausalEdge` connects events, never people-to-people. "A taught B, B taught C" is not expressible. |
| **Institutionalisation** | No rule/norm/office/law object. `HeritageType.INSTITUTION` is a tag on a seed. |
| **Culturalisation / religion / state** | `WorldTheme` axes are aggregate numbers, not a named custom, doctrine or polity that can be founded, spread and named. |
| **Historical evidence / source** | No document, record, monument-as-object, rumour or testimony type. `Discovery` is dungeon loot. This is the **core new type family** of the investigation loop. |
| **Player-known fact vs engine truth** | `BookState.reveals` is client-side and keyed to attribution coordinates. The engine needs a knowledge model per life (what this character has seen/heard/read), which is also what makes NPC hearsay possible. |
| **Hearsay / distortion** | Related: a fact that travels person-to-person and degrades. Nothing today models an *inaccurate* belief. |

---

## 6. Minimal vertical slice — migration plan

Target slice: **Life A** (1 town, 3 locations, 3 NPCs, 1 organisation, 5–7 actions, routines, NPC autonomy, variable lifespan) → **death, no legacy explanation, +10 years simulated** → **Life B** (new identity, Life-A traces present in the world as ordinary things, inspectable; no CausePath UI, no "your past self" message).

### 6.1 Engine

| Change | Size | Note |
|---|---|---|
| New `action.py`: `Action(verb, actor, target, location, duration)` + resolution | new, ~250 ln | Replaces `activity.perform_activity` as the funnel. Must keep "one funnel" discipline. |
| New `routine.py`: start / continue / interrupt a routine across years | new, ~150 ln | The "continuation" half of the slice. |
| Rewrite `life.py` clock: year-based, age 0/16→80, hazard-driven death | ~120 ln changed | Delete `TURNS_PER_YEAR` turn accounting. |
| New `npc_agent.py`: per-year NPC goal selection + Action execution | new, ~200 ln | Reuses `opportunity.py`'s scoring internally to pick NPC targets. Deletes `npc.py`. |
| Extend `macro.advance_year`: + NPC agent step, + relationship decay, + membership step | ~60 ln changed | Order matters for determinism. |
| Rewrite `macro.time_skip` → `simulate_gap(10)` running full years | ~40 ln changed | Must run the same `advance_year` as a lived year. |
| `worldgen`: 1 town / 3 locations / 3 NPCs with roles / 1 organisation | ~120 ln changed | Drop wildcards + dungeon from the slice. |
| Retire `discovery.py`, `combat.py`, `powers.py`, `inheritance.py`, `npc.py`, `timeskip.py` | −450 ln | All are E. |
| Keep untouched: `causal.py`, `rng.py`, `ids.py` | 0 | The determinism + DAG spine. |

### 6.2 Model

| Change | Size |
|---|---|
| New: `Organisation` (members, roles, rules), `Membership`, `Possession`/`Object`, `Skill`/`Knowledge`, `Routine`, `Source`/`Testimony`, `Belief` (known-fact) | new, ~200 ln of schema |
| Change: `ActivityRecord`→`ActionRecord` (+target, place, duration), `Relation` (+kind, since, last_seen), `NPC` (+knowledge, possessions, memberships, routine), `Lifecycle` (+real occupation), `Life` (+location, +known facts) | ~120 ln changed |
| Retire: `PlayerPowers`, `Inheritance`, `WildCard*`, `Discovery`, `Evaluation` (→internal), `HeritageNode` (→internal salience) | −90 ln |
| Keep: `CausalSeed/Node/Edge`, `Memory`, `Personality`, `Faction` (→ becomes `Organisation`'s coarse layer), `World` | 0 |

### 6.3 Persistence

| Change | Size |
|---|---|
| `Recipe.max_year` becomes a real parameter; lift `load.py:42` refusal | ~15 ln |
| `ENGINE_VERSION` bump (mandatory — every existing recipe and golden is invalidated) | 1 ln + regeneration |
| Input alphabet: define a serialisable command grammar for daily actions so `inputs: list[str]` still reconstructs a run | design-first, ~60 ln |
| `BookState`: reveal unit changes from attribution-coordinate to evidence-id | ~60 ln changed |

### 6.4 Beat / output

| Change | Size |
|---|---|
| New beat set: `Year`/`Season`, `Encounter`, `ActionTaken`, `RelationshipChanged`, `Death`, `Gap`, `Rebirth`, `Closing` | ~300 ln (replaces ~400 ln of `beats.py`) |
| Retire: `Juncture`, `Option`, `Outcome`, `Recognition`, `Mark`, `CausePath`, `CauseStep` | −250 ln |
| Keep: `BeatRecorder` observer seam, `to_dict` shape | 0 |
| `render.py`: rewrite the life surface; keep death/years/closing beat *positions* | ~350 ln changed |

### 6.5 UI contract

| Change | Size |
|---|---|
| Retire the DVS book contract (`client/web/book.js`, `client/bridge.py`, `client/fixture.py`, `unity/` B+C+D/E/F) | −4 000 ln equivalent (untracked Unity + web) |
| Keep: the reference corpus, pattern library and visual grammar in `docs/research/ui_reference/` — they were derived per *state*, and 10 of the 14 states (life context, ordinary consequence, death, years, return, history, investigation entry, evidence, ending, shelf) survive the loop change | 0 |
| New: an evidence/inspection surface contract (not a CausePath walker) | design-first |

### 6.6 Tests

| Bucket | Files | Fate |
|---|---|---|
| Juncture/option/seal/recognition/CausePath semantics | `test_beat_stream.py` (25), `test_client_bridge.py` (49), `test_client_state.py` (16), `test_play_gate.py` (11), `test_play_session.py` (6), `test_unity_fixture.py` (10), `test_discovery_slice.py` (20), `test_execution.py`, `test_salience.py`, `test_play_render.py` | **Obsolete** — ~170 tests encode the retired loop |
| Engine invariants that survive | `test_causal*.py` (DAG/cycle), `test_macro.py` (year ordering), `test_persistence.py` / `test_replay.py` / `test_record.py` (recipe round-trip, version refusal), `test_rng`/determinism | **Keep**, re-baseline values |
| Golden hashes | 8 world/lens goldens + `GOLDEN_TRANSCRIPT_SHA=41cf1cfd843f6272`, `GOLDEN_CHRONICLE_SHA=aa4c67a416178e92`, `GOLDEN_DIGEST_SHA=3816281ad6b04a43` | **All invalidated** by the `ENGINE_VERSION` bump — one-time regeneration, by design |
| P18 RED (17 failing) | `test_investigation_surface.py` | **Delete** — it specifies the answer-display lens |
| Lens contract tests (id-free, frozen, deterministic) | `test_timeline_observatory.py`, `test_character_observatory.py`, `test_narrative.py`, `test_world_model.py` | **Keep the contract**, change the content |

**Order-of-magnitude:** ~1 500 new engine/model lines, ~1 000 changed, ~1 400 retired in `src/`; ~170 tests retired, ~120 rewritten, 11 goldens regenerated once.

---

## 7. Tests / docs impact

### Docs superseded by the new core loop
`design.md` (§4 micro loop, §5 skip, §7 memory), `design_p6_salience.md`, `design_p6_execution.md`, `design_p8_player_experience.md`, `design_p17_legacy_legibility.md`, `design_p18_investigation_surface.md`, `discovery_loop.md`, `fingerprint_design.md`, `v1_ux_spec.md` (P-05/P-07/D-01/D-03 juncture surfaces), `v1_client_state_spec.md`, `design_v1_i1b_beat_stream.md`, `design_v1_i2_life_loop.md`, `design_v1_i3_rebirth_digest.md`, `design_unity_presentation_client.md`, `design_unity_bc_production.md`, `v1_m1_recognition_measurement.md`, `review_x1_x4_first_loop.md`.

### Docs that survive
`design_p9_*` (persistence/replay principle), `design_p11_world_model.md` / `p12` / `p13` / `p14` (lens contract), `design_p15_vertical_slice.md` (app-layer boundary), `analysis_world_diversity.md` (measurement method + the four root causes), `design_w1_worldgen_minimal.md` (see §8), `docs/research/ui_reference/*` (reference corpus, patterns, grammar), `v1_jp_voice_guide.md`, AI side-channel policy.

### Docs needing a rewrite rather than deletion
`game_experience_roadmap.md`, `player_journey.md`, `v1_implementation_roadmap.md`, `design_v1_definition.md`.

---

## 8. W-1 / P18 relevance under the new design

**W-1 (minimal worldgen diversity) — relevance rises, scope changes.**
Its four root causes all survive the loop change, and three become *more* important:
- RC-1 (hardcoded locations/factions) — the slice needs a real town with real places; the sampling change is directly on the path.
- RC-2 (31-name institution pool) — under the new design institutions are *things the player finds evidence of*; a 31-name pool is a much worse defect than it is today.
- RC-4 (`CausalNode.location_id` never set) — SC-4: the new loop **requires** a spatial axis. This item moves from "a dead field" to "a blocking prerequisite".
- RC-5 (heritage cap sweeps to life 1) — becomes moot if `HeritageNode` demotes to internal salience.
**Recommendation:** do not ship W-1 as specified. Take RC-1 and RC-4 into the new worldgen; drop RC-3/RC-5 (they tune a retired promotion mechanism); keep RC-2 as a labels-only fix that is safe at any time (it touches `reporting/labels.py` only — zero replay risk, as W-1 §1 establishes).

**P18 (investigation surface) — retire as designed, salvage the diagnosis.**
P18's product is `CauseChain`: event → origin life → origin action → step count, plus "consequences you never saw". That is the answer-display the new design explicitly replaces. Its 17 RED tests encode that contract and should be deleted rather than migrated. What survives is its *problem statement* — a finished world should be investigable, and posthumous consequences are the emotional core — and its lens discipline (read-only, invents no score, id-free, own golden). Those carry into the evidence model.

---

## 9. OPEN DESIGN QUESTIONS

Design decisions the brief does not settle and that I must not invent.

**Q-1 — What is one player action, in time?** A year? A season? A variable-duration routine committed to and interrupted? This determines the input alphabet, and therefore whether `Recipe` replay survives (SC-14). *Blocking for everything below.*

**Q-2 — How many decisions per life does the player actually make?** At 80 years, a per-year decision is 80 inputs/life; at 3 lives that is 240. Today it is ~6/life. This is the single biggest pacing question and it decides whether the game is a life-sim or a chronicle.

**Q-3 — Does the player see their own life's mechanics at all?** No evaluation, no skills, no visible relationship meters — or a diegetic version of them? "The game does not explain your past life's influence" is stated; whether it explains your *current* life's state is not.

**Q-4 — What exactly is an "evidence item"?** A document, an object, a person's testimony, a place? Are they engine entities created when an event fires, or derived on demand from the graph at inspection time? (Entity = storage + authoring cost; derived = cheaper but harder to make feel like a thing you hold.)

**Q-5 — How does a trace survive 200 years?** Which of {object, building, document, name, custom, family, institution} persists, and what destroys each? Without a decay model the world either forgets everything or keeps everything.

**Q-6 — Does the player ever get confirmation that they were right?** The new design removes "you caused this". Does it also remove *any* feedback that an inference was correct? If there is none, the reward is purely internal recognition; if there is some, its form is the hardest UX problem in the project.

**Q-7 — Is hearsay allowed to be wrong?** If NPC testimony can be inaccurate, the engine needs a belief model distinct from truth (and the player can be misled, which is good detective design but expensive). If not, "gathering sources" collapses to "querying the DAG through a skin".

**Q-8 — What is the player's relationship to their own past lives' NPCs?** An NPC the player taught in Life A may still be alive in Life B (10-year gap, 80-year lives). Do they recognise *you*? Under what rule?

**Q-9 — Are the 3 slice NPCs individuals with full simulation, and what happens at scale?** 3 NPCs × 200 years is cheap; a town of 60 is not. What is the intended Tier-S / Tier-B split under a real agent model?

**Q-10 — Is `Recipe` replay still a hard requirement?** It has shaped every architectural decision to date (no snapshots, version refusal, golden byte-identity). Keeping it under a dense input stream is possible but constrains the action grammar. Dropping it means adopting world snapshots. *This is an owner decision, not an engineering one.*

**Q-11 — Does the 200-year world end, or does it continue without the player?** `classify_ending` + `Closing` assume a terminal state.

**Q-12 — What replaces `Evaluation`'s 8 lenses as the internal measure of "this life mattered"?** Or is there no such measure any more?

---

## 10. Recommended implementation order

Each step is independently verifiable and leaves the repo green.

0. **Settle Q-1, Q-2, Q-10** (design, no code). Everything below depends on the action grammar and on whether recipe-replay survives.
1. **Time & horizon.** Make `max_year` a real parameter, lift the `load.py:42` refusal, bump `ENGINE_VERSION`, regenerate goldens once. Small, mechanical, unblocks the 200-year world.
2. **The life clock.** Year-based `Life`, age 0–80, hazard-driven death with real `DeathCause` variety. Deletes `timeskip.py`, rewrites `life.py`.
3. **Action model.** `Action(verb, target, location, duration)` as the single funnel, with `ActionRecord` capturing all four. Seeds become an *effect* of actions rather than their definition.
4. **Place.** `location_id` on `Life`, on actions, and on `CausalNode` (W-1 RC-4). 3 locations in one town.
5. **People who persist.** `Relation` with kind/since/decay, written by every interaction; `Memory` generalised; measured target: relation entries in the hundreds, not 2.
6. **NPC agency.** NPCs take Actions each year from the same vocabulary, driven by goals. Deletes `npc.py`.
7. **Routine / duration.** Multi-year commitments; repetition reinforces rather than duplicating causes.
8. **Organisation + membership.** One organisation with members and roles; the propagation substrate.
9. **The 10-year gap as simulation.** `simulate_gap(10)` running full `advance_year`s.
10. **Life B + traces.** Second identity; Life A's people, objects and institutions present as ordinary world content.
11. **Evidence model.** Sources/testimony/objects; the inspection verb set. (Depends on Q-4, Q-5, Q-7.)
12. **Retire the DVS stack** (beats, bridge, web client, Unity fixture, P18 RED, legacy lens) — last, so the old client keeps working as a reference until the new stream exists.

---

## The one unit to implement first

> **Step 2 — replace the life clock: a year-based `Life` that runs from birth to a hazard-determined death with a cap of 80, with `advance_year` as the only clock.**

Why this one:
- It is the **smallest change that makes the new core loop's central claim true** ("a life is a long time in which things accumulate"). Nothing else in the new design means anything while a life is 20 actions over 5 years (F-2).
- It is **strictly upstream** of action, routine, relationship and NPC agency: all four need a year to hang on, and none of them can be designed against a 4-turns-per-year counter.
- It is **self-contained and testable without any new domain model**: `life.py` + `config.py` + the `advance_year` call site, verified by a distribution test over ages at death and lives per world. No new entity types, no persistence schema change beyond the version bump from Step 1.
- It **forces the version bump and golden regeneration early**, while the surface area is small — instead of discovering mid-migration that 11 goldens and 170 tests must move at once.
- It does **not** depend on Q-1/Q-2/Q-10 being answered: whatever the action grammar turns out to be, the life is 80 years long.

Deliberately *not* first: the Action model (Q-1 blocks it), the evidence model (Q-4/5/7 block it), and retiring the DVS stack (keeping it alive costs nothing and it is the only working reference client).
