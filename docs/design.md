# Chronicle Forge — Design Document

**Status:** Design Locked (v0.3)
**Genre:** History-creation RPG / reincarnation roguelite / AI-assisted world simulation
**One-line concept:** *A history-creation RPG where you, as the world's only reincarnator, leave a legacy (a "mark") on history.*

---

## 0. Reading Guide & Glossary

- **Reincarnator (player):** the world's single recurring soul. On death the player reincarnates; the world keeps running.
- **World:** persists for a fixed lifespan (200 years in production, 40 years in dev/CI). On reaching the limit the game ends and produces a Chronicle and an Ending classification.
- **Causal Seed:** a tagged record of a player action that can later become the parent cause of world events. The central object of the whole game.
- **Causal Graph (DAG):** the directed acyclic graph of events and their causes. Single source of truth for "why did this happen".
- **Rules own truth, AI owns prose:** state transitions are decided deterministically by the rules engine; the LLM only narrates and makes a few bounded decisions. AI never mutates world state.

Assumptions (confirmed during review): text/systems-driven RPG (not action combat); single player, local-first; exploration is a node-map + encounter model, not rich 3D.

---

## 1. Core of the Fun

The pleasure is two-layered, and the two layers are **connected by traceable causality**.

| Layer | Experience | Reward |
|---|---|---|
| During play | "I'm overpowered" (reincarnator advantage, growth, immediate intervention effect) | Competence, control |
| After play | "*My* actions created this history" | Meaning, narrative, pride/regret |

**Key design finding:** the fun comes not from simulation fidelity but from the **traceable causal link** between the player's actions and the generated history. "A hundred-year war happened" is not moving. "*Your* age-22 mine investment → enabled the merchant league → enabled the general's independence → led to the hundred-year war", and being able to **trace it**, is the source of pleasure.

Consequences:
- The **Causal Link system (section 9) is the core engine**. History generation, evaluation, and the chronicle viewer are all subordinate to the causal graph.
- "Overpowered" is a **means**, not the goal. Strength is framed as *intervention power for leaving a mark on history*. Raw combat strength is never the reward.
- Evaluation axes therefore measure **long-term causal impact, not combat power** (section 8 / evaluation).

---

## 2. Risk Analysis

| # | Risk | Severity | Description | Mitigation |
|---|---|---|---|---|
| R1 | Causal coherence collapse | Critical | AI-generated history breaks "why", so tracing is unsatisfying | Rules engine owns state; AI only narrates/interprets; causal edges fixed structurally before narration |
| R2 | "So what" problem | Critical | Player does not care about generated history | History is presented as *the player's seeds bearing fruit*; world history always anchors to personal history |
| R3 | AI cost / latency / non-determinism | High | LLM calls per reincarnation cost money, add latency, lose reproducibility | Limit to 5 call sites + structured output + result cache + fixed seeds + per-life budget guard |
| R4 | Scope explosion | High | Simulation features grow without bound | MVP = "one village, one complete causal loop" (section 3) |
| R5 | History text flood | Medium | 3 large / 5 medium / 20 small events per decade is overwhelming | Player sees large events + anything causally linked to them; small events live in the codex |
| R6 | Simulation monotony | Medium | Rule-based factions repeat | Faction randomness + WildCard disruption + player intervention create divergence |
| R7 | Inheritance balance | Medium | Knowledge inheritance makes later lives a chore | Inheritance unlocks shortcuts, not repeatability; world state already changed, so the same strategy will not work |
| R8 | Fictionality (legal) | Medium | Correspondence to real peoples/nations | Procedural names + banned-word list; "fully fictional, no real-world correspondence" constraint injected into every prompt |

---

## 3. MVP Definition

MVP = the minimum unit that lets a player experience **one complete causal loop**. Slice vertically; drop horizontal breadth.

**Definition of Done:** the player reincarnates several times in one village; one action (e.g. raising an orphan) is **linked by the causal graph** to a world event decades later (e.g. that orphan becomes a general and triggers a faction war), and a Chronicle and Ending classification are generated.

| In MVP | Post-MVP |
|---|---|
| 1 village + 1 dungeon + a few field nodes | towns, cities, multiple regions |
| 3-4 factions (Lord / Merchant / Religious / Adventurer) | inter-state diplomacy |
| 10 NPCs (2-3 important) | large-population simulation |
| 1 WildCard (registry designed for N) | multiple simultaneous WildCards |
| Reincarnation, inheritance, aging, death | deep skill trees |
| NPC memory (structured; AI interpretation for important NPCs only) | AI thought for all NPCs |
| Rule-based combat | action / advanced combat |
| History generation (death-time skip) | full 200-year tuning |
| Personal history, world history, causal links, person codex | rich visualization UI |
| Chronicle + Ending classification | branching ending production |
| 8 evaluation lenses (numeric) | learned evaluation weights |
| Lineage data reserved (unused) | descendant/bloodline gameplay |

Dev/CI uses **world lifespan = 40 years** (completes in 2-4 lives) for fast iteration; production 200 years is the same logic with a constant change.

---

## 4. Game Loop

### 4.1 Macro loop (the world's life)
```
[world generation: once]
  -> (( reincarnation -> life -> death -> time-skip + history generation ))*
  -> [reach world max year]
  -> Chronicle + Ending
```

### 4.2 Micro loop (one life)
```
reincarnation (apply inheritance, decide birthplace/age)
  -> activities (section 4.4): exploration / combat / research / education /
       politics / commerce / religion / construction
       (each plants Causal Seeds)
  -> aging (each action consumes life-turns; turns advance world years)
  -> death (lifespan / combat / choice)
```

### 4.3 Time model (two resolutions)
- **Action time (micro):** each player action consumes life-turns; a number of turns advances one world year and ages the player. NPCs near the player also move at high resolution.
- **World time (macro):** death triggers a large skip (section 5) at low resolution; the whole world moves.

### 4.4 Life Activity Templates (v0.3)

The player's life is composed of actions drawn from **8 activity categories**. Each category is the single funnel through which evaluation, events, and causal seeds emerge. This makes play archetypes (scholar / merchant / adventurer / politician / educator) **emergent** from the activity distribution rather than hard-coded classes.

Unifying rule for every activity:
```
activity action  ->  consumes life-turns (aging)
                 ->  produces a CausalSeed of a given domain
                 ->  contributes to one or more evaluation lenses
                 ->  pushes one or more WorldTheme axes
                 ->  modulated by the life's build talent (affinity bonus)
```

| Activity | Primary eval lens | Seed domain | WorldTheme push | Example downstream events |
|---|---|---|---|---|
| Exploration | (cross-cutting) Discovery | discovery | varies by find | dungeon discovery -> tech spread / relic cult |
| Combat | Military | military | warfare | battles, faction wars, conquest |
| Research | Academia | technology | innovation | inventions, magical revolution |
| Education | Mentoring + Heritage | heritage | culture | schools, disciples, thinkers emerge |
| Politics | Politics | governance | governance | succession, faction power shifts |
| Commerce | Economy | economy | commerce | merchant league, trade routes |
| Religion | Faith | faith | faith | new cult, religious movement |
| Construction | Culture + Heritage | heritage/monument | culture | monuments, settlements, landmarks |

Play archetypes (emergent weightings, not classes):
- **Scholar:** Research + Education -> Academia / Heritage
- **Merchant:** Commerce + Politics -> Economy
- **Adventurer:** Exploration + Combat -> Military / Discovery
- **Politician:** Politics + Religion/Commerce -> Politics
- **Educator:** Education + Construction -> Mentoring / Heritage / Culture

The build talent (section 6 / A-2) grants efficiency and affinity bonuses to certain activities, giving inherited knowledge meaning (R7).

---

## 5. Post-Death Time Skip (History Correction)

Adopted method: **age-based base + seed maturation bonus.**

```
skip_years = clamp( base(age) + seed_maturation_bonus, MIN_SKIP, MAX_SKIP )

base(age) = MAX_BASE - (age_at_death / LIFESPAN_CAP) * (MAX_BASE - MIN_BASE)
            # younger death -> larger base (e.g. MAX_BASE=18, MIN_BASE=4)

seed_maturation_bonus = min( sum(pending_seed.maturation_time), BONUS_CAP )
            # years needed for the player's not-yet-fired causal seeds to mature
```

Why this is optimal:
1. Satisfies the requirement: `base(age)` is long for young death, short for old age.
2. Maximizes "my actions made this history": skip length depends on the **number of unmatured seeds the player left**. Plant much and die young -> the world moves a lot to show the results.
3. Delayed reward design: "built a school -> students need 15 years to grow -> die -> skip 15 years -> Chronicle shows a thinker came from that school." Maturation time *is* the time-to-payoff.
4. 200-year budget control: `MAX_SKIP` caps skip length, so total reincarnation count is controllable (e.g. MIN 4 / MAX 22 -> ~5-12 lives fill 200 years).

Rejected alternatives: fixed 10 years (no thematic expressiveness), pure random (no reproducibility, no control), legacy-score-proportional only (fails the age requirement; penalizes weak play).

---

## 6. NPC System

### 6.1 NPC tiers (compute-cost control)

| Tier | Examples | Driver | AI use |
|---|---|---|---|
| S — important | WildCard, heir, faction head | rules + AI decision | yes (bounded) |
| A — named | the village's 10 key NPCs | rule-based finite-state machine | only memory interpretation |
| B — crowd | rest of population | aggregate statistics (no individuals) | none |

MVP implements S (2-3) + A (10). B is a population number only.

### 6.2 NPC attributes
```
personality : {brave, greedy, merciful, ambitious, devout, cautious} each 0-100 (action weighting)
desires     : ordered list (wealth / power / fame / knowledge / revenge / peace)
goals       : short/long-term (drive FSM transitions)
relations   : affinity/trust/fear toward NPCs/factions/player
memory      : section 7
traits      : acquired via growth (talent / trauma)
lifecycle   : age, occupation, faction, alive, life-stage
lineage     : lineage_id, parent_ids[], generation  (v0.3 reserved; unused in MVP)
```

### 6.3 Rule-based behavior (Tier A, incl. combat)
FSM + utility function. Each step, evaluate available actions by `utility = f(personality, desires, goals, relations, world_state)` and pick the max; random jitter prevents monotony (R6).

### 6.4 Lifecycle during time-skip
Promotion, job change, marriage, faction join/leave, death resolved by probability tables + utility. Each becomes a **causal event node** linked to its cause (educated / war happened / player support).

### A. Player Powers (the reincarnator's prerogatives)

Two-layer design: shared base prerogatives + per-life build. Every power is unified as a **causal-seed injector**, so strength converts directly into a mark on history.

**A-1. Shared powers (kept/inherited across lives):**

| Power | Effect | Causal connection |
|---|---|---|
| Imprint | leave a strong memory (high intensity / low decay) on an NPC | a long-term parent seed steering that NPC's future behavior |
| Foresight | reveal the WorldTheme and part of the unmatured seeds | lets the player *aim* causal investments |
| Bequest | on death, carry knowledge/titles/traits/some skills to the next life | roguelite inheritance |
| Manifest | a limited amplifier of existing causality (see section A redesign below) | does not create events; amplifies weights |

**A-2. Per-life build (discarded on death):**
A **Talent** chosen/rolled at birth sets action efficiency and favored evaluation lenses (e.g. scholar talent boosts academia/heritage; warrior talent boosts military). Inherited knowledge unlocks talent options, giving inheritance meaning (mitigates R7).

### A (redesign). Manifest as an amplifier (v0.3)

Manifest **does not create events** and never inserts a new CausalNode. It selects an **existing** seed/heritage/WildCard/theme channel and applies a **bounded multiplier**, preserving graph integrity.

```
ManifestEffect {
  target_kind : SEED | HERITAGE | WILDCARD | THEME_AXIS
  target_id
  modifier : {
    weight_mult            # amplify a causal edge's weight
    firing_prob_mult       # raise an event's firing probability
    maturation_delta       # speed up / slow down a seed's maturation
    heritage_growth_mult   # accelerate Heritage longevity growth
    trajectory_influence_mult  # strengthen player influence over a WildCard trajectory
  }
}
```
Examples: support an inventor -> raise weight of invention-domain seeds; found a school -> raise Heritage growth rate; back a merchant league -> raise economy-event firing probability; support a WildCard -> raise trajectory influence. Manifest runs on a limited charge budget; multipliers are clamped so it amplifies without breaking causality (R1).

---

## 7. Memory System

### 7.1 Structured memory (the truth, all tiers)
Memory is a **structured record, not natural language** (independence from AI = reproducibility).
```
Memory {
  subject_id    # who remembers
  event_ref     # which causal event
  actor_id      # who did it (incl. player)
  type          # SAVED / BETRAYED / EDUCATED / BEREAVED / ...
  valence       # -100..+100
  intensity     # 0..100 (decays)
  decay_rate    # intensity decay over time; trauma decays slowly
  timestamp
}
```
Memory updates `relations`, which feeds action utility (a "betrayed" memory drives future hostility).

### 7.2 AI memory interpretation (Tier S only)
Only at major Tier-S decision points, structured memories + situation are sent to the LLM to obtain "how does this NPC interpret the situation and what does it decide" as **structured output** (chosen option + one-line motive). State truth stays with the rules.

---

## 8. WildCard System (designed for N)

WildCards are non-linear disruptors of history. Registry holds N; MVP runs 1.
```
WildCardRegistry { wildcards: [WildCard] }
WildCard {
  id, archetype (revolutionary/prophet/inventor/conqueror/zealot)
  status (DORMANT/IGNITED/RESOLVED/DEAD)
  ignition_condition         # e.g. famine & unrest > threshold
  trajectory                 # staged event sequence if left alone
  impact_vector              # direction pushed on WorldTheme/faction/city
  player_interaction         # SUPPORT / ELIMINATE / EXPLOIT / IGNORE
  interactions_with : [{other_id, relation: RIVAL|RESONANT}]  # future multi-WildCard hook, unused in MVP
}
```
- Skip processing loops the registry: fire DORMANT whose condition is met; run IGNITED trajectories.
- Player interaction (4 options) edits the `impact_vector`; intervention is recorded as a top-weight causal seed.
- `impact_vector` pushes WorldTheme (section C link).
- MVP example (inventor): support -> magical revolution; eliminate -> technological stagnation; exploit -> own faction strengthened; ignore -> used by another, strengthens a rival.

### Evaluation system (8 lenses)
Military / Politics / Economy / Academia / **Culture** / Faith / **Mentoring** + **Heritage**. Culture, Mentoring, and Heritage carry high weight, enforcing "long-term causal impact > combat power" (section 1).

### D. Heritage evaluation (v0.3)
The 7 axes are kept; **Heritage** is added as a cross-cutting 8th lens (separate, not merged) because it measures a different dimension: **how long causality keeps propagating after death**.
```
HeritageNode (= promoted long-lived CausalSeed)
  type : school / thought / technology / institution / heir / monument
  reach     : breadth -> count of transitive descendant events in the causal DAG
  longevity : depth   -> years the legacy has propagated since its founding event
  heritage_score = round(weight * longevity * (1 + reach))
```
Reach and longevity are tracked separately. The `(1 + reach)` term lets a young
legacy with no descendants still accrue value from longevity, while reach
amplifies it; `weight` favors culture-/mentoring-oriented legacies (school,
thought, institution, heir = 2; technology, monument = 1). Founding a school ->
decades later produces a thinker -> later institutionalized: the more descendant
nodes (reach) and the longer it propagates (longevity), the higher the score. The Heritage tab in the codex/world history lists the player's legacy and is the main material for the Ending text.

---

## C. World Theme System (v0.3)

Bidirectional: primarily an emergent indicator computed from world state, but player seeds / dungeon finds / WildCards can actively push it.
```
WorldTheme {
  axes : { warfare, innovation, faith, commerce, governance, culture }  # each 0..100
  dominant : the leading axis (the world's current "color")
  history  : [ThemeSnapshot]   # typed trajectory, overlayable with personal history
}
ThemeSnapshot { year, axes{ThemeAxis:int}, dominant }
```
- **Inputs:** faction power, unresolved WildCards, dungeon discoveries, player seed domains.
- **Outputs (feedback):**
  1. corrects event firing probabilities during skip (high warfare -> more war events);
  2. drives Ending classification (golden = culture x commerce x governance; imperial = governance x military; theocratic = faith dominance; warring = warfare dominance; apocalyptic = seal release, etc.);
  3. revealed by the Foresight power -> the player can deliberately tilt the world.

This single axis connects player powers (A), the dungeon (B), history generation, and the ending.

---

## B. Dungeon <-> History Generation Link (v0.3)

Dungeons are not just combat arenas; they are where the **parent nodes of history are mined.**
```
dungeon clear -> Discovery -> CausalSeed -> parent of world events during skip
```

| Discovery type | Example | Historical consequence (auto-linked) |
|---|---|---|
| Tech | lost magical formula | tech spread -> industrial/military revolution; Theme -> innovation |
| Relic | ancient holy seal | religious-faction growth / new cult; Theme -> faith |
| Seal | sealed calamity | release -> disaster/war events; Theme -> warfare (leaving it sealed is a choice) |
| Lore | truth of an ancient dynasty | ideology / legitimacy claim -> political events; Theme -> governance |

Each dungeon has a **Theme Affinity**; clearing it pushes WorldTheme (B->C link). MVP: 1 dungeon, one of each discovery type to prove causality propagates.

---

## 9. Causal System (core)

### 9.1 Causal graph (DAG)
```
CausalNode (= Event)  : id, scale(LARGE/MED/SMALL), domain, year, location, actors[], caused_by[CausalEdge]
CausalEdge            : from(cause) -> to(effect), weight, kind(ENABLE/TRIGGER/AMPLIFY/SUPPRESS)
CausalSeed            : domain, magnitude, target(faction/npc/city/tech), maturation_time, decay,
                        activation_mode(GUARANTEED|PROBABILISTIC), base_probability  (player action)
```

### 9.2 Generation principle (answer to R1)
> State transitions are decided **deterministically by the rules engine** -> causal edges are attached **structurally at generation time** -> the AI only **narrates/interprets** the already-fixed graph.

The AI is never asked to *invent* history; what happened (state change) and why (edges) are fixed first, and the AI only prose-ifies them, guaranteeing traceable-without-contradiction causality.

**DAG guarantee:** the causal structure is enforced acyclic. `CausalGraph.add_edge` rejects any edge whose effect is already a transitive cause of its cause (and self-loops), raising `CausalCycleError`. This keeps "trace why this happened" terminating and contradiction-free (R1).

### 9.3 Event firing
During skip, each latent event's probability `= f(world_state, active_seeds, faction_tensions, wildcard_trajectory, world_theme)`. A fired event automatically attaches the contributing factors as parent edges. If a player seed contributed, a link is always created (resolves R2).

Seeds carry an `activation_mode`: `GUARANTEED` seeds fire deterministically once matured (P1/P2 behavior — all seeds are GUARANTEED for now); `PROBABILISTIC` seeds fire by `base_probability` scaled by world state, introduced in P3.

### 9.4 Tracing UX
From any event, walk toward parents. "Hundred-year war <- general's independence <- merchant league <- mine discovery <- [YOU] age-22 investment." Reaching a player node highlights it.

---

## 10. Personal & World History

| | Personal history | World history |
|---|---|---|
| Unit | the player's per-life / all-life timeline | all CausalNodes of the world |
| Example | age 22 rescued orphan / 31 found ruins / 52 died | merchant league founded / succession war |
| Relation | each entry anchors a seed into world history | each large event traces back into personal history |

- **Person codex:** per-NPC timeline (orphan -> knight -> general -> emperor); each transition is a causal node whose cause is traceable. Lineage fields (v0.3) reserved for future "descendant of the orphan you raised becomes emperor" tracing.
- The world-history view is filterable by "your involvement" to prevent R2.

---

## 11. Data Model (logical)

Core persisted entities (see `src/chronicle_forge/models.py` for the authoritative pydantic schema):
```
World        { id, seed, current_year, max_year, theme: WorldTheme, ending_class? }
Player       { id, current_life_id, powers: PlayerPowers, inherited{knowledge[],titles[],traits[],skills[]} }
Life         { id, player_id, birth_year, age, turns, death_year, age_at_death,
               death_cause, talent, activity_log[], evaluation{8 lenses}, summary? }
LifeSummary  { life_id, title, dominant_axis, seeds_created[], heritage_created[],
               notable_events[] }   # generated at death; feeds personal history /
                                    # inheritance / ending generation
NPC          { id, tier, attributes(6.2), lifecycle, alive, lineage{lineage_id,parent_ids[],generation} }
Faction      { id, type, power, ideology, relations{} }
Location     { id, type(village/dungeon/field), state, theme_affinity }
Memory       { 7.1 }
CausalNode   { 9.1 }   CausalEdge { 9.1 }   CausalSeed { 9.1 }
HeritageNode { D }     # subtype of long-lived CausalSeed
WildCard     { 8 }     WildCardRegistry { 8 }
WorldTheme   { C }
PlayerPowers { common{imprint,foresight,bequest,manifest}, build_talent }
Discovery    { type(Tech/Relic/Seal/Lore), theme_affinity }  -> CausalSeed
ActivityCategory { id, primary_eval_lens, seed_domain, theme_push{}, talent_affinity }
Chronicle    { world_id, generated_text, ending_class }
```
- **Ownership of truth:** world_state + CausalNode/Edge are the single source of truth; AI output is derived and subordinate.
- **Reproducibility:** `World.seed` + the action log can fully reconstruct all history (essential for debug/verification).

---

## 12. AI Architecture

### 12.1 The 5 call sites
| Site | Input | Structured output | Frequency |
|---|---|---|---|
| NPC memory interpretation | Tier-S memories + situation | interpretation label + one-line motive | major points only |
| Important NPC decision | NPC state + options | option id + reason | Tier-S branch points |
| Post-death history generation | fixed causal skeleton | narration per node (does not change state) | once per death (batch) |
| Chronicle generation | full world + personal history | chaptered long text | once at world end |
| Ending generation | final world_state + evaluation | classification + ending text | once at world end |

### 12.2 Principles
- **Rules own truth, AI owns prose** (R1): AI never decides state.
- Structured output (JSON schema / tool use); on parse failure, rules fallback.
- Cache + fixed seeds: identical input -> cached identical output (reproducibility, R3).
- Budget guard: cap AI calls/tokens per life; on overflow, degrade to template narration.
- Safety constraint injected into every prompt: "fully fictional, no correspondence to real peoples/nations/religions/political groups" (R8).
- Model policy: narration/chronicle -> high-quality model (Opus-class); light decisions -> fast model (Haiku-class).

---

## 13. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language/core | Python 3.10+ | AI integration, rules engine, data processing; pydantic for structured I/O |
| Data validation | pydantic v2 | dual use for LLM JSON validation and data model |
| Persistence | SQLite (MVP) -> Postgres later | relational queries over causal graph/history; local-first |
| AI client | Anthropic SDK | structured output (tool use) + prompt caching |
| Presentation | deferred ("core logic first") | API/library first; UI decided later |
| Tests | pytest | per project policy |
| Formatting | Black | per project policy |

Deliberately avoided: game engines (Unity/Unreal) over-engineer the MVP; a graph DB (Neo4j) is overkill early — SQLite adjacency tables express the causal DAG fine.

---

## 14. Implementation Roadmap

| Phase | Goal | Key deliverables | Verification |
|---|---|---|---|
| P0 foundation | data model + world generation + seed fixing | World/Life/NPC/Faction/Causal* schema; deterministic seeding; RNG | snapshot reproducibility test |
| P1 causal core | CausalSeed -> CausalNode/Edge (rules only, no AI); WorldTheme + HeritageNode promotion | causal DAG build + tracing query | seed->event link unit tests |
| P2 micro loop | one life (activities, aging, death); PlayerPowers + Discovery->Seed; rule-based combat | activity templates, FSM NPCs, memory | one-life playthrough test |
| P3 macro loop | death skip (section 5) + rule-based history gen; WildCardRegistry N-loop + Theme feedback | time correction, faction/NPC autoplay | multi-life completion to max year |
| P4 AI integration | the 5 call sites + structured output + fallback | narration/decision/chronicle/ending | schema validation, budget guard, fallback test |
| P5 view/eval | personal/world history, causal tracing, codex, 8-lens eval | presentation layer | "trace the hundred-year war cause" E2E |
| P6 polish | ending classification, safety filter, balance | fictionality check, reincarnation balance | full playthrough, banned-word scan |

Critical path: **P1 (causal core) is the foundation of everything** and is designed first and most heavily; if it is weak, the core of the fun (section 1) collapses.
