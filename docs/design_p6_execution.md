# P6 Execution Layer — Opportunity → Action (design)

**Status:** Review applied — approved for implementation
**Depends on:** `docs/design_p6_salience.md` (implemented in `src/chronicle_forge/opportunity.py`)

**Review deltas (this revision):** (1) §6 M9 Engagement-Loop observation added — the Ω
self-reinforcement loop is the layer's top risk and must be *observed* (not tuned) before
shipping; (2) §1.4 E-1 `engage_wildcard` allow/forbid contract made explicit to preserve the
mutation funnel; (3) §1.5 Legacy Tend non-reinforcement semantics made explicit (design doc +
code comment). No tension tuning is introduced.

## Context

P6 Salience produces 3–5 tension-ranked `Opportunity` objects per action-turn, but nothing
consumes them: the world is still driven by the legacy talent policy
(`autoplay._pick_activity`). The Execution Layer converts each offered `Opportunity` into an
**executable player action**, so that opportunities can actually drive play — for both the
deterministic auto-player and a future human player.

### Hard constraints (from the P6 observation review)

- P6 tension computation is **not changed**.
- Opportunity selection logic is **not changed**.
- Opportunities are **never re-ranked, filtered, or re-scored** by this layer; the list from
  `select_opportunities` is presented exactly as given (it is already sorted by tension).
- The Execution Layer's sole responsibility is **Opportunity → Action conversion**.

### Existing engine verbs (the only mutation funnel)

| Verb | Effects |
|---|---|
| `activity.perform_activity(world, life, category, target_id)` | plants 1 `CausalSeed` (domain from `ACTIVITY_PROFILES`), accrues evaluation, forms a `Memory` when `target_id` is a live NPC (`_MEMORY_FOR`), advances 1 turn |
| `discovery.explore_dungeon(world, life, location_id, discovery_type)` | creates a `Discovery` + high-magnitude seed, academia evaluation, advances time |
| `powers.imprint(world, life, npc_id, ...)` | strong low-decay memory only (no seed, no turn cost) — **excluded from MVP options** (see Future) |

`WildCard.player_interaction` (`SUPPORT/ELIMINATE/EXPLOIT/IGNORE`) exists in the model and is
read by `wildcard_signals` (Ω = 1.0 when set), but **no engine verb sets it today**.

## 1. Action taxonomy per Opportunity kind

Full taxonomy first (what engaging each kind *can* mean), then the canonical MVP mapping.
Every action is one existing engine verb call; the taxonomy is a parameter table, not new
mechanics.

### 1.1 NPC — invest in a person

| Action | Verb call | Narrative meaning |
|---|---|---|
| Mentor | `perform_activity(EDUCATION, target=npc)` | raise an heir / successor (HERITAGE seed, EDUCATED memory) |
| Advocate | `perform_activity(POLITICS, target=npc)` | protect / elevate them politically (GOVERNANCE seed, SAVED memory) |
| Guide | `perform_activity(RELIGION, target=npc)` | shape their beliefs (FAITH seed, EDUCATED memory) |

**MVP canonical choice** (uses the offered opportunity's already-computed `signals` — reading
them is not re-scoring): `Ρ ≥ 0.5 → Advocate` (a perilous person is stabilized, SAVED memory),
otherwise `Mentor` (the default investment; mortality-driven Δ reads as "pass something on
before they die"). Guide is reserved for the post-MVP menu.

### 1.2 Faction — invest in a power

| Action | Verb call | Narrative meaning |
|---|---|---|
| Further their cause | `perform_activity(AXIS_TO_CATEGORY[FACTION_TYPE_TO_THEME[faction.type]], target=None)` | act in the faction's domain |

`AXIS_TO_CATEGORY` is a new **explicit static table** in the Execution Layer (the inverse of
`ActivityProfile.theme_push` is ambiguous — CULTURE maps to both EDUCATION and CONSTRUCTION —
so the table is declared, not derived):

```
WARFARE → COMBAT        INNOVATION → RESEARCH    FAITH → RELIGION
COMMERCE → COMMERCE     GOVERNANCE → POLITICS    CULTURE → EDUCATION
```

No NPC target in MVP (picking a member NPC would silently turn a Faction engagement into an
NPC engagement and distort the kind distribution we just measured).

### 1.3 Location — engage a place

| Condition | Action | Verb call |
|---|---|---|
| DUNGEON, undiscovered | Explore | `explore_dungeon(loc.id, discovery_type)` |
| otherwise | Develop | `perform_activity(CONSTRUCTION, target=None)` |

`discovery_type`: autoplay derives it from the execution RNG (deterministic); a human player
chooses it post-MVP. "Undiscovered" is checked the same way as `location_signals` does — no
`Discovery` references the location (read-only check, not a re-score).

**Inherited limitation (B-1):** the Develop action is thematic only — `CausalSeed` has no
location link, so developing a village leaves no per-location trace. Recorded, not fixed here.

### 1.4 WildCard — answer a rising force

| Action | Verb call | Narrative meaning |
|---|---|---|
| Support | `engage_wildcard(wc.id, SUPPORT)` → `perform_activity(POLITICS, target_id=wc.id)` + sets `player_interaction` | back them |
| Eliminate | `engage_wildcard(wc.id, ELIMINATE)` → `perform_activity(COMBAT, target_id=wc.id)` + sets `player_interaction` | move against them |
| Exploit | `engage_wildcard(wc.id, EXPLOIT)` → `perform_activity(COMMERCE, target_id=wc.id)` + sets `player_interaction` | profit from them |

**E-1 (the single engine addition):** a thin `engage_wildcard(world, life, wc_id, interaction)`
wrapper in `activity.py` — calls `perform_activity` with the mapped category and
`target_id=wc.id`, then sets `wc.player_interaction` (latest-wins). Rationale: the field and
enum are already designed into the model; without E-1 a WildCard opportunity is not executable
and its Ω stays a dead proxy. `target_id=wc.id` is harmless to existing indexes (only NPC ids
are looked up) and becomes the future NPC↔WildCard linkage hook.

**E-1 contract (binding — keeps the mutation funnel single-sourced).** `engage_wildcard` is a
*thin wrapper*, nothing more. This is enforced by `test_funnel_only` (the wildcard rows of the
§2 table) and stated as a code comment on the function.

| Allowed | Forbidden |
|---|---|
| call `perform_activity` (the one mutation path) | generate its own `CausalSeed` |
| set `wc.player_interaction` | generate its own `Memory` |
| | generate its own `Discovery` |
| | consume its own turn (only `perform_activity`'s single turn-advance) |
| | alter any evaluation value beyond what `perform_activity` accrues |

Every world mutation of a wildcard engagement is exactly one `perform_activity` call plus the
`player_interaction` assignment; the wrapper adds **no** mechanics of its own.

**MVP canonical choice:** peril archetypes (`CONQUEROR/ZEALOT/REVOLUTIONARY`, same set as
`WILDCARD_PERIL_ARCHETYPES`) → Eliminate; otherwise Support. Exploit is reserved for the
post-MVP menu. IGNORE is expressed by not selecting the opportunity, never as an action.

### 1.5 Legacy — tend your own past

| Action | Verb call |
|---|---|
| Tend | `perform_activity(HERITAGE_TYPE_TO_CATEGORY[heritage.type], target=None)` |

```
SCHOOL → EDUCATION      THOUGHT → EDUCATION      HEIR → EDUCATION
TECHNOLOGY → RESEARCH   INSTITUTION → POLITICS   MONUMENT → CONSTRUCTION
```

**Recorded limitation (L-2) — Legacy Tend is non-reinforcing.** This plants a *new* seed in the
legacy's domain; no verb exists that strengthens the existing `HeritageNode` (reach/longevity
grow only via causal propagation). The honest MVP semantics are "continue the tradition", not
"buff the heritage". The future heritage-reinforcement verb is the same extension point as
`legacy_state_changed` in the salience design.

> This exact wording is required as a code comment on the Legacy Tend mapping/handler:
>
> ```
> # Legacy actions continue a tradition by planting new seeds.
> # They do NOT modify existing HeritageNodes.
> # Current MVP semantics: "continue the tradition and plant a new seed",
> # NOT "strengthen the heritage". Heritage reinforcement is the
> # responsibility of a future dedicated verb (see L-2 in design_p6_execution.md).
> ```

### 1.6 Free action (fallback, decision D-2)

One extra option, always last: the legacy talent policy (`_pick_activity`-equivalent untargeted
activity). Opportunities are invitations, not coercion — a player (or the auto-chooser's
exploration arm) may decline all of them. The fallback commits `selected_id=None`, which the
session API already supports.

## 2. Action → Seed / Memory / Discovery wiring

**Principle: the Execution Layer creates nothing.** Every world mutation goes through the
existing funnel verbs; `execution.py` never constructs a `CausalSeed`, `Memory`, or
`Discovery` itself. This keeps the causal-graph invariants (one seed per action, evaluation
accrual, turn cost) in one place.

Loop closure — which P6 signal each action feeds on the *next* turn:

| Action | Seed | Memory | Discovery | Feeds back into |
|---|---|---|---|---|
| NPC Mentor/Advocate/Guide | targeted seed | EDUCATED / SAVED | — | NPC Ω (seeds+memories), NPC Δ (ripening) |
| Faction Further | axis-aligned seed | — | — | Faction Ω (`recent_seeds_by_axis`) |
| Location Explore | discovery seed | — | yes | Location Ω; frontier turns off (natural freshness) |
| Location Develop | MONUMENT seed | — | — | (nothing location-bound — B-1) |
| WildCard Support/Eliminate/Exploit | seed with `target_id=wc.id` | — | — | WildCard Ω (`player_interaction` set) |
| Legacy Tend | domain-aligned seed | — | — | (indirect only — L-2) |

This is the load-bearing property: engagement raises Ω, so engaged targets get *hotter*, while
the existing recency penalty, per-kind caps, and Mix floor prevent monopolization — **no
tension change is needed to keep the loop stable**, and per the constraints none is made.
Whether that balance actually holds is an observation item (§5, harness), not a tuning knob.

## 3. Responsibility boundary

New module `src/chronicle_forge/execution.py` (volatile layer, same status as
`opportunity.py`; constants local, `config.py` untouched).

| | In scope | Out of scope |
|---|---|---|
| Input | `world` (read-only), `life`, `list[Opportunity]` as returned (order preserved), a chooser decision | — |
| Convert | `expand_options(opps, world, life) -> list[ExecutionOption]` — pure, deterministic, 1 canonical option per opportunity + 1 fallback | adding/dropping/reordering opportunities; recomputing tension |
| Execute | `execute_option(world, life, option)` — exactly one engine-verb call | direct mutation of `World`; creating seeds/memories/discoveries |
| Commit | `session.commit_turn(offered, selected_id)` after execution | persisting anything to `World` |
| Engine | E-1 `engage_wildcard` lives in `activity.py` (engine side) | any other engine change; `opportunity.py` is untouched |

`ExecutionOption` (volatile dataclass): `opportunity: Optional[Opportunity]` (None for the
fallback), `verb` + parameters (category / target_id / location_id / discovery_type /
interaction), `label` (for display/logging).

## 4. Autoplay / human-play unification

One shared turn driver; only the **chooser** differs.

```
Chooser = Callable[[list[ExecutionOption]], int]   # returns an index

def play_turn(world, life, session, chooser, rng) -> ExecutionOption:
    opps    = select_opportunities(world, life, session)   # untouched
    options = expand_options(opps, world, life, rng)        # + fallback, order preserved
    choice  = options[chooser(options)]
    execute_option(world, life, choice)
    session.commit_turn(opps, choice.opportunity.target_id if choice.opportunity else None)
    return choice
```

- **Auto chooser** (MVP): seeded RNG (`derive_rng`, new `EXECUTION_SALT`, distinct from 99/77)
  — probability `P_TOP = 0.7` picks index 0 (highest tension, list is already sorted);
  otherwise a seeded uniform pick over the remaining options including the fallback.
  Deterministic and reproducible; the exploration arm exists so observation sees the whole
  taxonomy, not just the top slot.
- **Human chooser** (post-MVP UI, same protocol): render `options[i].label`, read input. The
  CLI/UI implements `Chooser` and nothing else — no game logic leaks into the interface.
- **Compatibility:** the legacy policy remains the default. `simulate_world(seed)` output is
  byte-identical to today (golden seed42 artifacts, P5 reproducibility). Opportunity-driven
  play is opt-in: `simulate_world(seed, mode="opportunity")` (default `"legacy"`). The
  opportunity-mode life loop reproduces the legacy life mechanics exactly (lifespan draw,
  per-action combat-death probability); the only changed block is action choice. The legacy
  loop's random `imprint` sprinkle (roll > 0.92) is **dropped** in opportunity mode — it was
  scripted-agent noise and would distort Ω observation. Recorded as a deliberate behavioral
  difference.

## 5. MVP plan

| File | Change |
|---|---|
| `src/chronicle_forge/execution.py` | new (~150 lines): tables (`AXIS_TO_CATEGORY`, `HERITAGE_TYPE_TO_CATEGORY`, interaction maps), `ExecutionOption`, `expand_options`, `execute_option`, `play_turn`, `auto_chooser` |
| `src/chronicle_forge/activity.py` | +`engage_wildcard` (E-1, ~15 lines) |
| `src/chronicle_forge/autoplay.py` | opportunity-mode life loop behind `mode=` param; legacy path untouched |
| `scripts/opportunity_playlog.py` | `--execute` mode: opportunities now *drive* the world (replaces the read-only overlay for this mode); logs chosen option per turn |
| `tests/test_execution.py` | new |

Test plan:

- `test_deterministic`: same seed → identical option/action sequence (two runs).
- `test_no_reorder`: `expand_options` preserves the opportunity order 1:1 (+fallback last).
- `test_mapping_tables`: every `OpportunityKind` × condition row of §1 maps to the declared
  verb/category; tables are total over `FactionType`/`HeritageType`/peril archetypes.
- `test_funnel_only`: `expand_options` is read-only on `world` (`model_dump` deep-equal);
  `execute_option` mutates only via the funnel (seed/memory/discovery counts match the §2 table
  for each action).
- `test_wildcard_engagement`: after Support/Eliminate, `player_interaction` is set and that
  wildcard's Ω is 1.0 on the next turn's signals.
- `test_loop_closure_npc`: engaging an NPC raises its Ω next turn.
- `test_legacy_default_unchanged`: `simulate_world(seed)` (no mode arg) equals the pre-change
  result exactly.
- Harness (not a test): fixed-seed `--execute` runs emit the **§6 M9 metrics** (same-target
  consecutive rate, mean re-selection interval, Ω time-series, per-kind monopoly rate) vs. the
  read-only baseline — observation only; any tension tuning is out of scope by constraint.

## 6. M9 — Engagement-Loop observation (pre-ship, observe-only)

**Why M9 exists.** The Execution Layer closes a self-reinforcing loop (§2):

```
Opportunity → Execute → Seed/Memory → Ω rises → re-selected next turn → …
```

This is the layer's single largest risk: a target that gets engaged becomes *hotter* and can
dominate subsequent turns. The existing safeguards (recency penalty, Mix floor, per-kind cap)
are *expected* to bound it, but that expectation is unverified once opportunities actually drive
the world. **M9's purpose is observation, not tuning** — confirm on fixed seeds whether the
existing safeguards are sufficient. **No tension computation, weight, penalty, or cap is changed
at the design or implementation stage of this layer** (hard constraint, unchanged).

**M9 metrics** (emitted by the `--execute` harness, per fixed seed, alongside the §5 baseline):

| Metric | Definition | What an unhealthy loop looks like |
|---|---|---|
| Same-target consecutive-selection rate | fraction of action-turns whose selected target equals the immediately previous selected target | high → recency penalty too weak |
| Same-target mean re-selection interval | mean turn-gap between successive selections of the same target id | very low → a target monopolizes the slot |
| Ω time-series | per engaged target, Ω(t) across turns (does engagement drive runaway Ω?) | monotonic climb with no decay |
| Per-kind monopoly rate | max share of action-turns captured by any single `OpportunityKind` | near 1.0 → Mix floor / per-kind cap insufficient |

**Method.** Run the deterministic `--execute` auto-chooser over the fixed observation seeds
(same seed set as the existing Legacy/Heritage harness, incl. seed 42), collect the four metrics,
and report them next to the read-only baseline. The output is a **record**, mirroring the P6
Salience Legacy/Heritage observation: findings are logged ("記録のみ") and feed a *separate*,
later tuning decision — they do **not** trigger a tension change inside this layer.

## Decision points

- **D-1 — E-1 `engage_wildcard`:** the one engine addition. Recommended: yes (field already
  designed in; without it WildCard opportunities are not executable). Alternative (rejected):
  map WildCard to a plain activity — zero engine change, but the wildcard system never sees
  the player and Ω stays a dead proxy.
- **D-2 — free-action fallback option:** recommended: yes (agency; `selected_id=None` already
  supported). Alternative: force a choice among opportunities — simpler menu, coercive feel.
- **D-3 — one canonical action per opportunity (MVP)** with signal-driven flavor (NPC Ρ rule,
  WildCard archetype rule); the full per-kind menu is post-MVP UI. Keeps the choice surface =
  "which opportunity", which is what P6 was measured on.
- **D-4 — legacy autoplay stays the default** (`mode="legacy"`); opportunity mode is opt-in.
  Golden artifacts and P5 determinism are untouched.

## Future extension points (recorded, not built)

- Per-opportunity action menus (Guide / Exploit / discovery-type choice) once a human UI exists.
- `imprint` as an execution option (needs a turn-cost decision on the engine side).
- Heritage reinforcement verb (with `legacy_state_changed`) so Legacy Tend touches the actual
  `HeritageNode`.
- NPC↔WildCard linkage via `target_id=wc.id` seeds feeding future Ρ signals.
- Faction actions targeting member NPCs (post-MVP, after kind-distribution effects are observed).
