# Time Domain — the world clock, a life's chronology, mortality, and the gap

Status: **accepted** (owner decisions 2026-09-17 / 2026-09-20 / 2026-09-21).
Engine version: `0.2.0-time-domain`. Source of truth for everything below:
`config.py`, `life.py`, `macro.py`, `mortality.py`, pinned by
`tests/test_time_domain.py`.

This document supersedes the time model in `design.md` §1 (world lifespan),
§4.3 (two resolutions) and §5 (post-death time skip), the `max_year` replay
gate in `design_p9_1_save_load.md`, and "the recipe is the save" in
`design_p9_persistent_history.md`.

## 1. The clock

- One simulation tick is **one world year**. `macro.advance_year(world)` is the
  only operation that moves time: it advances `current_year`, runs the world's
  yearly simulation (seeds → events → wildcard/faction/NPC steps → theme →
  heritage), ages the current life, and asks the mortality seam. Nothing else
  writes `current_year`.
- The world simulates **during a life as well as between lives**. (Before this
  change the world only moved in the post-death skip.)
- **Player decision cadence is not the tick.** Action turns still accumulate at
  `TURNS_PER_YEAR = 4`; every fourth turn reaches `advance_year`. A future
  Routine may span several years — it will call the same seam.
- **Horizon:** `WORLD_MAX_YEARS = 200`. The world can advance to exactly year
  200 and no further (`WorldHorizonReached`). Reaching it ends the run even if
  the current life is alive; that life is **not** killed and gets no death,
  gap, or aftermath. There is no dev/CI horizon — `max_year` remains a
  parameter for short debug worlds only.

## 2. A life's chronology

| field | meaning |
|---|---|
| `Life.birth_year` | the person's **actual birth year** |
| `Life.playable_start_year` | the world year **player control begins**, at `START_AGE = 16` |
| `Life.age` | always `world.current_year - birth_year`; refreshed by the clock, never counted separately |
| `Life.death_year`, `age_at_death`, `death_cause` | fixed exactly once by `end_life` |
| `Life.alive` | `death_year is None` |

Consequences:

- The first life is taken up in year 0 and was therefore **born in year -16**.
  The character's sixteen years before the world's record begins are real
  history that the record simply does not cover.
- Playable lifespan is 16 → at most 80: 64 world years.

## 3. Mortality

- `LIFESPAN_CAP = 80`: reaching it is death by `LIFESPAN`, always.
- **There is no default hazard.** A life with no hazard in play reaches 80.
  The old per-year combat probability is gone; no flat "make the average
  lifespan look right" mortality will replace it.
- Early death comes only from the **mortality seam**: `mortality.HAZARDS` is a
  list of deterministic callables `(world, life, rng) -> DeathCause | None`,
  evaluated once per world year for the current life, with an RNG derived from
  `(world.seed, year, HAZARD_SALT)` — a stream separate from the world's own,
  so registering a hazard never reshuffles world events. Hazards are to be
  supplied by real world/action context (war, sickness, a dangerous act), not
  by a constant.

## 4. Death → reincarnation ("死後10年で転生")

Fixed semantics (owner decision 2026-09-21):

1. After a life dies, the world advances **exactly ten years**
   (`REINCARNATION_GAP_YEARS = 10`). The gap is seed-independent and
   independent of anything the dead life planted. The dead person does not
   act; the world simulates yearly.
2. At year `death + 10`, a **different person who is 16 years old at that
   time** becomes the next playable life: `playable_start_year = death + 10`,
   `birth_year = playable_start_year - 16`.
3. Therefore the next person **may have been born before the previous life
   died** (with a 10-year gap they were born 6 years before it). Overlapping
   historical existence between consecutive protagonists is **explicitly
   allowed** and is not a chronology bug.
4. What moves at the death is the **player's continuity** — control, and
   whatever cross-life memory the engine carries — never a birth event.
   "Reincarnation" names that hand-over, not the person's birth.
5. If `death + 10 > 200`, the world runs only to 200 and no new life begins.
6. Player-facing terminology for this hand-over is decided separately.

Default run under these rules: three lives — years 0–64, 74–138, and 148–200
(the third still alive, aged 68, when the horizon ends the run).

## 5. Persistence

- The Recipe (seed + max_year + mode + inputs) is a **reproduction record** for
  debugging, goldens and bug reports; `ENGINE_VERSION` still gates replay. It
  is no longer the product's save. The `max_year != 40` gate is gone: a
  recipe's own horizon is replayed.
- The future save is a versioned world snapshot (not yet built); nothing in the
  current API blocks it.

## 6. Determinism

Identical seed + identical inputs produce identical time and death results.
Hazard draws come from their own salted stream; world event draws are unchanged
by registering hazards (pinned by `test_hazard_rng_is_separate_from_the_world_stream`).

## 7. Known gaps (out of scope here)

- Every generated NPC is dead by about year 55 and none are born, so most of a
  200-year world has no living NPC. Population continuity is the next unit.
- `JunctureGate.decide(is_final_turn=...)` is legacy: no caller knows a final
  turn ahead of time under this clock, and `play.session` no longer passes it.
