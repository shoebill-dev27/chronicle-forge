# Routine — the years a person spent living one way

Status: **accepted** (owner decisions 2026-09-28 / 2026-10-01). Engine version:
`0.4.0-routine`. Companion to
`design_time_domain.md` (the clock) and `design_population_continuity.md` (the
people). Source of truth: `routine.py`, `models.Routine`, pinned by
`tests/test_routine.py`.

A life is not a list of decisions. "Supported Karic" is a click; "worked beside
Karic in Hollowfen from sixteen to twenty-three" is a life. This unit makes the
second one a first-class historical fact — deterministic, queryable, and still
readable a century after everyone in it is dead.

Nothing here yet *does* anything to anybody. Relationship, knowledge, culture
and causal consequence are later work. The span itself has to be true first.

## 1. Where people are

Tracked persons gained one piece of spatial truth: `Lifecycle.location_id`, an
id from the existing `World.locations` registry. No new `Location` model, no
second person system.

- **Founders** are handed a home by index (`homes[i % len(homes)]`), not drawn
  from `rng`. Just as deterministic, and it leaves every other draw in
  `worldgen` on the stream it was already on.
- **Homes** are the non-dungeon locations. The dungeon is a place to go, not a
  place to be from.
- **A newborn begins where their parent is** — the founding children and every
  later birth follow the same rule.
- **`Lifecycle.location_id` is required.** A tracked person is always
  somewhere: "nowhere" is not a state the world may hold, and a person with no
  place could not be worked beside. Every construction path supplies one.
- **A successor is not moved.** Taking somebody up leaves them exactly where
  they already lived.
- **The dead keep their last place.** It is part of their record.

There is no movement system, no adjacency, no travel. A person's *past* places
are not held here — they are held by their routines, which is the point.

## 2. What a routine is

| field | meaning |
|---|---|
| `id` | stable, allocated in order (`routine-0000`, …) |
| `actor_person_id` | the tracked person who lived it |
| `kind` | `WORK_AT` / `WORK_WITH` / `ASSOCIATE_WITH` |
| `location_id` | where the years were spent |
| `target_person_id` | the other person, for the two person-facing kinds |
| `start_year` | the first world year of the span |
| `end_year` | `None` while it is still being lived |
| `end_reason` | `None` while it is still being lived |

`WORK_AT` is aimed at its location, so it takes no target; the two person kinds
require one, and refuse one that is not real, not alive, not an adult, the
actor themselves, or somewhere else. *Somewhere else* is the rule that makes
"who you lived beside" truthful: with no travel, you can only spend years next
to someone who is where you are.

Routines live in `World.routines`, never in the `Life`. A life ends; the record
of what it did with its years does not, and a later life must be able to read
it.

## 3. How long it lasted

**Duration is derived, never stored.**

```
start_year = 12, end_year = 19  →  7 years
```

The year it began counts; the year it ended does not. A routine still running
is measured against the clock (`world.current_year - start_year`), so it cannot
go stale. There is no counter to drift away from the chronology, which is the
same rule age follows (`design_time_domain.md` §2).

## 4. Living it out

- **Choosing is not a year.** `begin_routine` and `change_routine` record a
  decision; they never move the clock.
- **The clock keeps the record true, not the command.** `advance_year` ends
  with `routine.step_routines`, which reconciles every *open* span against the
  year that just happened. A routine is world truth: it closes at the exact
  year a death made it untrue whether the years were advanced by
  `continue_routine`, by a bare `advance_year`, by in-life turns, or by the
  reincarnation gap. Closed spans are history and are never revisited.
- **`continue_routine(world, years)` is only a convenience.** It takes `years`
  as a maximum, spends it one `advance_year` at a time, and stops once the
  span has closed. It holds no closure rules of its own.
- **At most one active routine per person.** `change_routine` closes the old
  span and opens the new one *in the same world year*, so the two meet with no
  gap and no overlap.

`end_reason` is always named:

| reason | when |
|---|---|
| `PLAYER_CHANGED` | the player chose to live differently |
| `TARGET_DIED` | the other person died |
| `ACTOR_DIED` | written by `life.end_life`, in the death year |
| `WORLD_ENDED` | written by `advance_year` on reaching the horizon |

**A death outranks the end of the world.** In `advance_year` the order is:
mortality seam (`end_life` → `ACTOR_DIED`) → `step_routines`
(`TARGET_DIED` / `ACTOR_DIED`) → *then* the horizon. `close_at_horizon` only
touches spans that are still open, so `WORLD_ENDED` can never overwrite the
more specific truth that somebody died that year.

The horizon closes every still-open routine **without killing anyone**: the run
ends, the person does not (`design_time_domain.md` §5). A successor inherits nothing
— they begin with no active routine, while their predecessor's spans stay
readable in the registry.

## 5. What this unit deliberately does not do

- No `ActivityRecord` per routine-year, and no `CausalSeed` per routine-year.
  One span is one record; writing a row a year would smuggle back exactly the
  "one year = one decision" model this replaces. The Routine → causal-graph
  bridge is a later unit.
- No effect of any kind on the people in a routine, and no NPC routines: only
  the played person starts one.
- No location history, no movement, no map.
- The old `perform_activity` / opportunity / juncture path is untouched, and
  nothing here depends on it.
