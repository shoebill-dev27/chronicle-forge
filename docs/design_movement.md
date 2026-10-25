# Movement — the player may change where they live

Status: **accepted** (owner review GO, 2026-10-25). Engine version:
**`0.7.0-movement`** (§7). Source of truth: `spatial.py`,
`play.routine_session._move`, `play.view.places`, pinned by
`tests/test_movement.py`. Builds on `design_knowledge_transmission.md`.

Why now: the play evaluation of 2026-10-23 found that a successor always
begins in a different place from their predecessor, and that none of the
predecessor's surviving TELL recipients (0/12) was ever reachable. Movement
makes them reachable. It does not reveal what they know; that is the next
unit.

## 1. Where a person may live

`spatial.is_residential(location)` = *not a dungeon*. It is the only copy of
the rule: worldgen now hands out homes with it (before, it was an inline
filter there), and relocation chooses destinations with it. No "habitable"
metadata was invented; `LocationType` already says it.

`spatial.residential_locations(world)` lists them in `world.locations` order
(Hollowfen, Greywind Moor, Thornreach in every current world).

## 2. The act

`spatial.relocate(world, person_id, destination_id)` checks everything first,
then changes the world:

* refuses (`RelocationRefused`) a missing or dead person, a missing place, a
  dungeon, or the place they already live;
* closes the person's open routine with **`RoutineEndReason.RELOCATED`** —
  a new member, because changing how you live (`PLAYER_CHANGED`) and leaving
  where you live are different things to know;
* sets `lifecycle.location_id`.

It does not advance time, learn, tell, plant, or touch genealogy. The closure
is in the domain, not the session, because a routine is lived *somewhere*:
any caller that moves a person must end it, or the routine would claim a place
its actor is not in.

## 3. The command

    > move
    Places you could live:
      [1] Hollowfen (you live here)
      [2] Greywind Moor
      [3] Thornreach

    > move 2
    You leave Hollowfen and settle in Greywind Moor.
    You left that life behind with the place.
    1 year passes.

* `move` lists, `move <n>` goes — one input line each, so recipes need no new
  representation.
* The list holds every residential place with the current one **marked, not
  removed**, so a number names the same place wherever the player stands. The
  current place is not selectable: `move <here>` is refused and costs nothing.
* The list says nothing about who lives where or what happened there.
* `move <n>` = `relocate` → `advance_year` **once** → that year's events
  observed through the ordinary `_observe` channel, from the **destination**.
  The relocation year has no routine; the player chooses one on arrival.
* An invalid number, a non-number, the current place, or a world at its
  horizon: refused, no state change, no year.

Incidental fix on the same path: `continue 1` now reads "1 year passes."
(was "1 year pass.").

## 4. Time, death, horizon

The year is an ordinary `advance_year`, so the world's own rules decide it:

* a person of 79 who moves reaches 80 in that year and dies of it (mortality
  seam unchanged; the routine stays `RELOCATED`, not `ACTOR_DIED`);
* a move into the horizon year ends the world with the person alive;
* an old routine target dying that year does not rewrite `RELOCATED` —
  `step_routines` only looks at open spans.

## 5. What changes downstream, by itself

Nothing below was special-cased; each reads `location_id`:

* `status` names the new place; `nearby` is the destination's adults (the
  before/after sets were disjoint in every measured case);
* `work with` / `associate with` — and so `tell` — can only be with them;
  somebody left behind is refused as "not where you are";
* observation is from the destination, the move year included.

Only the player person moves. No NPC changes place.

## 6. Measured: the previous life's recipients (seeds 4, 17, 42)

Maximal-telling play (see the 2026-10-23 evaluation), then each successor
moves to where a predecessor's recipient lives.

| | count |
|---|---|
| previous-life recipients | 12 |
| alive when the successor begins | 6 |
| reached (the same person, by id, in `nearby` on arrival) | **6 / 6** |
| moves needed for each | 1 |
| successor knows any of what they were told | 0 |

The prior result was 0/12 because contact was structurally impossible. It is
now bounded only by who has died. In one of the six (seed 17, Venon) a second
person of the same name stood in the same place.

Ten years of a second life, staying vs. moving, seed 42: observed
`{Kalin, Selthas, Tornon} rises to power` staying, `{Ashmar rises to power}`
moving — disjoint. Nearby sets were disjoint in all three seeds.

## 7. Version and goldens

`ENGINE_VERSION` `0.6.0-knowledge-transmission` → `0.7.0-movement`: under
0.6.0, `move` / `move <n>` were unknown commands, so the same recipe text now
means a different world. The existing gate refuses a 0.6.0 recipe (tested).
`HELP` gained two lines. No golden moved: the juncture loop never moves anyone
and `is_residential` reproduces worldgen's old filter exactly.

## 8. Known gaps

* **Names do not identify people.** Same-name persons are listed with
  distinct numbers and no ids, but the player cannot tell them apart; and the
  successor in seed 4 meets a "Vewen, 32" who is not their predecessor.
  **This blocks the next discovery surface**: anything that names a teller
  or a past person by name alone will be ambiguous. It is deliberately not
  solved here.
* **Nothing shows what the reached person knows.** Contact is unlocked;
  discovery (asking, provenance) is the next unit.
* The place list is flat: no distance, road, cost beyond one year, or
  encounter. The dungeon is not a place to live, and there is still no way to
  visit it.
* Only routines whose actor moves are closed. No other actor has routines
  today; if NPCs ever do, a routine *targeting* the mover would need the same
  rule.
