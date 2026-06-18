# P10 Candidate Research — Observatory / World Dynamics / Social Memory

Status: **Research only. No code change, no commit.** Goal: a fact-based
comparison of three P10 directions so the next phase can be chosen deliberately.

Method: read the current source tree (`src/chronicle_forge/`), the `World` model,
the macro/execution engine, and the read-only reporting layer. Facts are drawn
from code; **Assumptions** and **Recommendations** are labelled as such per the
project's design policy.

## Shared baseline (facts the three candidates must respect)

- **Engine determinism is the load-bearing invariant.** A world is reproduced
  byte-for-byte from `Recipe(engine_version, seed, max_year, mode, inputs)`. Any
  change to worldgen / P6 / `execution.py` / `macro.py` / RNG / play-loop output
  changes the world hash and **requires bumping `ENGINE_VERSION`** (currently
  `0.1.0-p8-mvp`). Bumping it **invalidates the seed42 golden** (`e62d8f2c…` /
  `98bea862…`) and forces a *new* frozen baseline.
- **Frozen assets:** P6 salience/opportunity (`opportunity.py`, macro firing) is
  explicitly "frozen, no tuning". P7 experience text and P8 play loop are locked.
- **Read-only reporting layer already exists and is rich:** `views.py` (P5 dev
  observability — `full_report`, theme trajectory, causal trace, heritage ranking,
  npc codex), `reporting/_data.py` + `labels.py` (id-free humanised accessors),
  `reporting/experience.py` (P7), `reporting/lineage.py` (P9-4),
  `reporting/heritage_explorer.py` (P9-5).
- **Latent schema already present (no migration needed):** `NPC.relations:
  dict[str, Relation{affinity,trust,fear}]`, `World.memories: list[Memory]`,
  `memory.form_memory(...)`, `NPC.lineage: Lineage{parent_ids, generation}`
  (reserved, unused by MVP), `Faction.relations`, `WorldTheme.history`.

---

## Candidate A — P10 Observatory

A unified, player-facing **"browse your world"** surface: one navigable hub that
composes the existing read-only projections (timeline, theme trajectory, lineage,
heritage, ending, causal trace) over a finished or replayed world.

- **Player experience.** High and immediate: turns the scattered P7/P9 views into
  a single "explore what I made" experience; pairs naturally with P9 replay
  ("load a recipe → observe it"). Extends the P6→P7→P9 arc (generate → experience
  → revisit) rather than opening a new mechanic.
- **Architecture fit.** Excellent. It is a *consumer* of read-only projections;
  the seam (`_data`/`labels`/`reporting`) is exactly what it needs. No engine
  touch.
- **Asset reuse (P6/P7/P8/P9).** Highest of the three: reuses P7 experience, P9-4
  lineage, P9-5 heritage, P5 `views`, and P9 persistence/replay as its data
  source. Net-new code is mostly composition + navigation.
- **Implementation cost.** **Small–Medium.** A new `reporting/observatory.py` (or
  a small `observe/` surface) plus an additive CLI verb; bounded by how
  interactive the navigation should be.
- **Risk.** Low. Read-only (assertable via `model_dump_json`), no
  `ENGINE_VERSION` change, seed42 golden untouched, no id-leak risk if it reuses
  the humanised helpers.
- **MVP scope.** One command that renders an indexed, navigable read-only digest
  of a world/recipe: sections = lives (lineage), heritage (explorer), theme
  trajectory, ending. No new metrics; pure aggregation. Stretch: section
  selection / paging.

## Candidate B — P10 Social Memory

Make NPCs **remember the player across lives**: persist and inherit relations,
let memories decay and resurface, so a later self meets people (or their
descendants) shaped by an earlier self's deeds.

- **Player experience.** Strong *thematic* payoff — directly amplifies the
  reincarnation core ("the orphan you raised has a descendant who becomes
  emperor", the reserved `Lineage` use case). But NPCs are deliberately minimal
  today ("the protagonist is history, not the NPCs"), so the felt impact depends
  on surfacing memory in the play/experience layer.
- **Architecture fit.** Moderate. The schema is *ready* (`Memory`,
  `Relation`, `memory.form_memory`, `Lineage`), but making memories matter means
  feeding them into `npc.step_npc` / `macro.step_npcs_lifecycle` /
  `execution.py` — i.e. **engine changes**.
- **Asset reuse.** Medium–High on schema (Memory/Relation/Lineage already
  modelled), Medium on logic (`form_memory` exists but is lightly used). Builds on
  P6 causal seeds as memory triggers.
- **Implementation cost.** **Medium–Large.** New memory-decay + relation-inherit
  rules, cross-life subject resolution, and surfacing in P7/observatory.
- **Risk.** **High to determinism.** Any change to memory formation inside the
  macro/execution path alters the world hash → `ENGINE_VERSION` bump → seed42
  golden re-baselined. Touches the frozen P6 firing if memories gate seeds.
  Mitigable by gating behind a new mode/flag so the default seed42 path is byte-
  unchanged (**assumption** — needs a feasibility spike).
- **MVP scope.** Relations + memories persist across `advance_to_next_life`,
  decay over the skip, and one read-only "who remembers you, and why" view.
  Behind a flag so the default engine output is unchanged.

## Candidate C — P10 World Dynamics

Deepen the **macro simulation** itself: richer faction power struggles, wildcard
chains, NPC lifecycle, and theme feedback — so the world between lives evolves
with more agency.

- **Player experience.** Broad sim depth: a livelier world to be reborn into. But
  it is the most *diffuse* value (improves the backdrop, not a specific player
  verb), and hardest to make legible without an observatory to read it.
- **Architecture fit.** Touches the **core engine** most heavily —
  `macro.step_factions` / `step_wildcards` / `step_npcs_lifecycle` /
  `advance_year`, and the frozen P6 firing model. Highest blast radius.
- **Asset reuse.** Reuses the causal graph, theme model, and faction/wildcard
  schema, but extends rather than composes — least leverage of the read-only P7/P9
  work.
- **Implementation cost.** **Large.** New dynamics rules + balancing + a new
  determinism baseline + extensive regression.
- **Risk.** **Highest.** Directly modifies frozen P6 macro and `execution.py`;
  guaranteed `ENGINE_VERSION` bump and seed42 re-baseline; balancing/tuning risk
  (the exact class of change P6 was frozen to avoid). No isolation seam today.
- **MVP scope.** Hard to keep small — even a minimal faction-rivalry rule changes
  every world hash. Would need its own frozen seed + golden from day one.

---

## Comparison table

| Axis | A · Observatory | B · Social Memory | C · World Dynamics |
|---|---|---|---|
| Player value | High, immediate (revisit/explore) | High, thematic (cross-life bonds) | Diffuse (livelier backdrop) |
| Architecture fit | Excellent (read-only consumer) | Moderate (engine feed) | Heavy (core engine) |
| P6–P9 asset reuse | Highest (composes P7/P9/P5) | Medium (schema ready, logic light) | Low (extends, not composes) |
| Implementation cost | **S–M** | **M–L** | **L** |
| Determinism impact | None (read-only) | High (ENGINE_VERSION bump likely) | Certain (bump + re-baseline) |
| seed42 golden | Untouched | Re-baseline unless flag-gated | Re-baseline |
| Touches frozen P6 | No | Possibly (if memory gates seeds) | Yes |
| Main risk | Minimal | Determinism / scope creep | Determinism / balancing (P6's frozen risk) |

## Recommended order

**1 → A (Observatory) · 2 → B (Social Memory) · 3 → C (World Dynamics).**

**Why this order:**

1. **Observatory first** continues the proven, low-risk arc (P6 generate → P7
   experience → P9 revisit → P10 *observe as one surface*). It is read-only, so it
   ships with **zero determinism risk and the seed42 golden untouched**, reuses
   the most existing P5/P7/P9 assets, and is the smallest. It also *unlocks* B and
   C: both produce world state that is only valuable if a player can read it — the
   Observatory is the lens they need. Highest value-to-risk ratio.

2. **Social Memory second.** It is the strongest *thematic* fit for a
   reincarnation roguelite (your past selves leaving a social trace) and the
   schema (`Memory`/`Relation`/`Lineage`) is already in place, so it is the
   cheaper of the two engine-touching options. It does cross the determinism line,
   so it should be **flag/mode-gated** to keep the default seed42 path byte-
   identical until a deliberate `ENGINE_VERSION` bump — sequencing it after the
   Observatory means its output is immediately legible.

3. **World Dynamics last.** Highest cost, highest blast radius, and it directly
   reopens the **frozen P6 macro / tuning** that was deliberately locked — the
   exact change class P6's freeze guards against. Do it only once an Observatory
   exists to make its effects legible and once Social Memory has proven the
   flag-gated "engine extension without breaking the golden" pattern.

**Assumption flagged for the design phase:** that engine-touching work (B, C) can
be flag/mode-gated so the default seed42 baseline stays byte-identical until an
intentional `ENGINE_VERSION` bump. This needs a short feasibility spike before
committing to B or C; A has no such dependency.
