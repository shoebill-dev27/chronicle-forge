# The played life — the first loop the new core can actually be played in

Status: **accepted** (owner decisions 2026-10-04 / 2026-10-05). Engine version:
`0.5.0-playable-routine`. Source of truth:
`play/routine_session.py`, `play/view.py`, pinned by
`tests/test_routine_session.py`. Companions: `design_time_domain.md`,
`design_population_continuity.md`, `design_routine.md`,
`design_relationship.md`.

Four units of engine existed and none of them were reachable by a person at a
keyboard. This connects them. It adds no domain model: every verb is an
existing call in `routine.py`, every fact shown is read from `population`,
`routine` or `relationship`.

## 1. The boundary that was found

`run_human_world` is shared by five consumers — the CLI, recipe replay, recipe
load, the DVS beat stream, and the tests — and the world, transcript and
chronicle goldens all run through it. Switching it in place would have moved
every golden and broken the auto-player.

So the human path forks instead, at the one place that already distinguishes a
person from a script:

| input | loop | why |
|---|---|---|
| `play --seed N` (nothing else) | **`run_routine_world`** (new) | there is a person at the keyboard |
| `play --auto` | `run_human_world` (old) | the auto-player; the goldens are this |
| `play --script F` | `run_human_world` (old) | deterministic legacy drive |

This is not a feature flag. `adapter.build_reader` already returns `None`
exactly when input is live, and that is the fork.

## 2. The played loop

```
run_routine_world(seed)
  └─ generate_world
     while year < horizon:
        begin_life                     → population.successor: a real 16-year-old
        status                         → who you are, where, who is here
        while alive and year < horizon:
            read one command
              work at / work with n / associate with n   → routine.begin_routine
                                                           routine.change_routine
              continue [years]                           → routine.continue_routine
              status / history                           → read-only
        death → history → macro.time_skip(10) → next life
     closing
```

It calls `select_opportunities`, `expand_options`, `JunctureGate`,
`execute_option` and `perform_activity` **never** — pinned by a test that
replaces all four with a raising stub and plays a full twenty years.

## 3. The view model (`play/view.py`)

Plain frozen dataclasses, no rendering, no state, read-only on the world.

- `SelfView` — name, age, year, location name, parents' names, current routine
- `PersonView` — the grown people in the same place, in id order so the list a
  command indexes into is stable
- `RoutineView` — kind, place, the other person's name, `[start, end)`, years,
  end reason
- `TieView` — a name, the years shared, which kinds, parent/child, alive

Ids travel in these records because a command must name a target
unambiguously; they are never what the player reads.

## 4. Commands

| command | effect | moves time |
|---|---|---|
| `work at` | begin/change to `WORK_AT` here | no |
| `work with <n>` | begin/change to `WORK_WITH` the listed person | no |
| `associate with <n>` | begin/change to `ASSOCIATE_WITH` | no |
| `continue [years]` | live them, **1–10** (`MAX_CONTINUE_YEARS`) | **yes** |
| `status` / `history` / `help` | read | no |

`MAX_CONTINUE_YEARS = 10` is a **session guard, not a game rule**: enough to
prove a multi-year span without one line of input swallowing a century.

Everything the world will not support is refused and costs nothing: an unlisted
number, a non-number, zero or negative years, more than the bound, continuing
with no routine, a command that does not exist. Targets are only ever drawn
from the same-location adult list, so dead, child and absent people cannot be
named at all.

## 5. Interruption

`continue` reports the years that actually passed, and if the span closed, why,
in one line: *They died. That way of living ended with them.* /
*You died.* / *The chronicle reaches its end here.* / *You left that life
behind.* Then the total.

It says what happened. It does not say it mattered.

## 6. Death, hand-over, horizon

Death uses the existing truth: the mortality seam ends the life, `end_life`
closes the routine as `ACTOR_DIED`, `time_skip` runs the ten years, and the
next `begin_life` takes up whoever is sixteen then. The successor starts with
**no** active routine and **no** inherited ties; the predecessor's spans and
relationships stay in the world and are still queryable.

At year 200 the run ends, the routine closes `WORLD_ENDED`, and **nobody dies
of the horizon**.

## 7. What the player is never told

No friendship, trust, affection, closeness or bond. No score. No future
consequence. `history` says "9 years together" and "your child", because those
are the two things the world knows.

## 8. Persistence

A recipe now carries `loop: "juncture" | "routine"`, defaulted to `"juncture"`.
Routine commands and option numbers are different languages; without this,
replaying a played recipe would feed commands to the juncture loop. It is
additive and defaulted exactly as `social_memory` was, so every recipe written
before this loads and replays as it always did.

## 9. Known gaps

- **The old loop still produces every `CausalSeed`.** A played life plants
  none, so a routine-first world has no causal history yet. The
  Routine → CausalSeed bridge is the unit that closes this, and the old funnel
  cannot be retired before it.
- `play.beats` (the DVS beat stream) observes juncture events and is not wired
  to the played loop. It remains a legacy contract.
## 10. The defect this surface exposed, and its fix

Playing the slice made a genealogy bug visible that nothing else had: the
founding child cohort drew its parents uniformly from the ten founders with no
age check, so 2–5 of the 16 founding children had a parent who was a child when
they were born. Seed 4 handed the player, a sixteen-year-old, a ten-year-old
son on the first screen.

The parent test is now chronological rather than present-day:

```python
eligible = [p for p in founders
            if child_birth_year - p.lifecycle.birth_year > config.ADULT_AGE]
```

— the same rule `population._births` already applies to every later birth. The
age-sixteen founder the player may be taken up as is excluded by the
arithmetic, not by a special case: they were not born when any of these
children were. To guarantee the eldest child always has a valid parent (and so
that no invalid fallback is ever needed), the second founder is aged
`2 * ADULT_AGE`, which is exactly old enough.

Verified over **1000 seeds: zero** impossible parents. The world's shape is
unchanged — registry 226, 80 alive at the horizon, the same three lives in the
same years — but *who parented whom* changed, and with it world identity, so
`ENGINE_VERSION` is `0.5.0-playable-routine` and the twelve goldens were
regenerated.
