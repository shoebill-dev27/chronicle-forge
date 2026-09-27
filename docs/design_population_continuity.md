# Population Continuity — people are born, age, die, and leave descendants

Status: **accepted** (owner decisions 2026-09-26 / 2026-09-27). Engine version:
`0.3.0-population-continuity`. Companion to `design_time_domain.md`, which owns
the clock. Source of truth: `population.py`, `worldgen.py`, `life.py`, pinned by
`tests/test_population_continuity.py`.

The goal is not a demography simulation. It is the minimum that makes the
200-year world a human one: somebody is always alive, generations turn over,
the dead stay in history, and the player always has a real sixteen-year-old to
become.

## 1. Two levels of population, one kind of person

The world counts people twice, on purpose:

| | what it is | who moves it |
|---|---|---|
| `World.population` | the **aggregate populace** — humanity as a number, no identity, no birth year, no ancestry | nobody yet; worldgen draws it once |
| `World.npcs` | the **individually tracked persons** — name, stable id, birth and death year, parents | `population.step_population` |

Tracked persons are not every human alive, and the aggregate is not their
count. Neither is derived from the other, and no code may assume they agree:
the registry is the people history can *name*, and one day the aggregate is
what a city, a famine or an army is counted from.

There is no separate `Person` model. **`NPC` is the tracked person** and
`World.npcs` is the **historical registry**, not a cast list:

- A dead person keeps their row — `alive=False` plus `lifecycle.death_year`.
  Nothing is ever deleted, so history can still name someone a century later.
- The body the player is living in is one of these rows. `Life.person_id`
  names it; the player is a *control role*, not a different species.
- `Lifecycle` already carried `birth_year` / `death_year`; `Lineage` already
  carried `parent_ids` / `generation`. Both were declared and unused — this
  unit turns them on rather than adding a parallel identity system.

## 2. Chronology

`age = world.current_year - lifecycle.birth_year`, written once a year by
`population.step_population`, exactly as the playable life is (`life.age_of`).
`population.age_of` is the only formula; `adults()` and `aged()` derive rather
than read the stored field, so a stale record can never pass as young.

A record from before this change (no `birth_year`) adopts one from its stored
age the first time it is read, then follows the rule like everyone else.

## 3. The founding world

`worldgen` now produces, at year 0:

- **10 adults** (`MVP_NPC_COUNT`), ages 16–60, no parents — the founders. The
  first is exactly 16, so the player has someone to be in year 0.
- **16 children**, one of each age 0–15, each the child of one of those adults.

The children are not decoration. Without them the world has a hole where its
young should be and there is no sixteen-year-old between years 1 and 16 — the
player could not be reborn after an early death.

## 4. Birth

`TRACKED_BIRTHS_PER_YEAR = 1`, inside `advance_year`, in this order: **everyone
ages → those who reached the cap die → the ambitious may rise → a child is
born.** This is not the world's birth rate: it is how fast history acquires
people it can name. The aggregate populace is untouched by it.

- The parent is drawn, on a salted deterministic stream (`BIRTH_SALT`), from
  the living adults.
- **The player is never handed a child.** Their body is excluded, and so is
  everyone aged exactly `ADULT_AGE` — that cohort is who the player may be
  taken up as this very year.
- Parentage is genealogical truth only. There is no marriage, no household, no
  pregnancy: a parent here means ancestry and nothing else.
- `lineage_id` names the bloodline by its founder's id (`None` on a founder);
  `generation` is the parent's plus one.

This is a scaffold. Real fertility — who, with whom, how often, and why — is
later work, and the rule is written so that replacing it touches one function.

## 5. Death

One rule for everybody: reaching `LIFESPAN_CAP` (80) is death. There is no
random early mortality for persons any more than for the player (the old
`NPC_DEATH_PROBABILITY` is gone); early death will come from the same kind of
contextual hazard the mortality seam takes.

The player's body is the one exception in `step_population`: it is skipped
there because the mortality seam owns that death, and `life.end_life` writes
the same year back into the person's row. One death, recorded in both places.

## 6. Childhood

Below `ADULT_AGE` a person exists in history and in their family but is not an
actor: `population.adults()` is what the opportunity layer and the auto-player
iterate, so a child is never an opportunity, a target, or a parent. At 16 they
become eligible for everything, including being the player.

NPC autonomy itself is unchanged and still out of scope.

## 7. Becoming someone

`population.successor(world)` returns the person the player takes up: alive,
exactly `ADULT_AGE` this year, and never the player before. `begin_life` uses
it and copies **their** `birth_year`, so the life's chronology is the person's.

`Life.person_id` is **required**. There is no valid state in which a playable
life names no body: the only place a `Life` is constructed is `begin_life`,
after `successor` has returned someone. `end_life` raises rather than shrugging
if that id names nobody — a life without a body would be a fiction, not a
recoverable state.

If no such person exists, it raises `NoSuccessor`. It never invents a body:
a world with nobody of that age is broken, and hiding that would make the
player's history a fiction.

## 8. Measured over 200 years (seeds 1, 7, 42, 99, 123)

| | value |
|---|---|
| registry (all people who ever lived) | 226 = 10 + 16 + 200 |
| living at year 200 | 80 (64 adults, 16 children) |
| founders alive at year 200 | 0 |
| deepest lineage | 6–8 generations |
| living at 200 descended from the founding world | 80 / 80 |
| births | one in every year 1–200 |
| playable lives | 3 (years 0–64, 74–138, 148–horizon) |
| run time | ~7 s |

Population is bounded by construction: one birth a year and a hard cap at 80
means the living can never exceed one cap's worth of cohorts.

## 9. Known gaps

- The successor's *id* is the same across seeds (`npc-0000`, `npc-0083`,
  `npc-0157`) because the birth schedule is structurally identical; who that
  person is — name, family, faction — differs by seed.
- `World.population` is drawn once and never moves. It is a placeholder for
  the aggregate demography a city, economy or state layer would need; until
  something reads it, it carries no meaning beyond §1.
- With one tracked birth a year, every cohort has exactly one member. Once
  contextual hazards can kill a sixteen-year-old, `successor` will raise
  `NoSuccessor` — the intended invariant signal, and the point at which the
  scaffold needs a wider cohort.
- Parent choice is uniform over adults, so a 79-year-old is as likely as a
  25-year-old. That is the scaffold being honest about not modelling fertility.
- Nobody dies of anything but old age, so the age pyramid is a rectangle.
