# Knowledge transmission — TELL

Status: **implemented** (owner GO 2026-10-23). Engine version:
**`0.6.0-knowledge-transmission`** (§7). Source of truth: `knowledge.tell`,
`play.routine_session._tell`, `play.view.tellable`, pinned by
`tests/test_knowledge_transmission.py`. Builds on `design_person_knowledge.md`.

The first player act that changes another tracked person's persistent truth:

    A knows E, A lives a person-target routine with B, A tells B E  →  B knows E

Its whole effect is one `PersonKnowledge` row. No time, no seed, no domain,
no magnitude, no heritage, no theme, no `Memory`, no `Relation`.

## 1. Why TELL, not TEACH

What moves is a factual reference to a world event. Skills and competence do
not exist in the engine, so there is nothing to teach.

## 2. The record

`KnowledgeSource` is exactly `{OBSERVED, TOLD}`. `PersonKnowledge` gains one
field:

| field | OBSERVED | TOLD |
|---|---|---|
| `learned_year` | the event's year | the year of the telling |
| `learned_from_person_id` | `None` | the teller's person id |

A model validator pins the pairing (teller ⇔ `TOLD`) and refuses a person as
their own teller. The teller is a stable id, never a name. Rows written before
this unit (four keys) load unchanged with `learned_from_person_id = None`.

No second transmission log: the row already answers "who did this person learn
it from?", and a chain is followed row by row
(`C.from → B`, `B.from → A`, `A` is `OBSERVED`).

## 3. First acquisition wins

Identity stays `(person_id, event_id)`. `learn` returns `None` for a fact
already known, so year, source and teller are never overwritten:
`OBSERVED → TOLD`, `TOLD(A) → TOLD(C)` and `TOLD → OBSERVED` are all no-ops.
The row records how this person *first* came to know, not every conversation.

## 4. Domain vs. session

`knowledge.tell(world, teller_id, recipient_id, event_id)` refuses
(`KnowledgeRefused`) only what would be untrue: a teller or recipient who is
not a living person, telling oneself, or a teller who does not know the event
(which also covers events that do not exist). It does not know about routines.

The session decides *who may be told*: only the target of the player's current
active routine, and only when its kind is in `routine.PERSON_KINDS`
(`WORK_WITH`, `ASSOCIATE_WITH`). `WORK_AT` and an unsettled life have nobody to
tell. The recipient is never typed; the routine already answers "to whom".

## 5. Command UX

    > tell
    Things you can tell Vegar:
      [1] Year 14. Sellin rises to power.

    > tell 1
    You tell Vegar: year 14, Sellin rises to power.

    > tell
    Vegar already knows everything you know.

* `tell` lists, `tell <n>` tells — the same list-then-index pattern as
  `status` / `work with <n>`. Each is one input line, so a recipe records and
  replays it with no new input representation.
* Offered facts are `view.tellable`: the player's own `known_events` (world
  order, i.e. by year), **minus what the recipient already knows**. Omitting
  them was chosen over marking them: nothing can be gained by telling the same
  fact twice, and the list never offers a no-op.
* Knowing nothing: "You know of nothing that has happened, so there is nothing
  to tell." No state changes.
* No ids, no source names, no claim of trust, belief or importance.
* Neither `tell` nor `tell <n>` calls `advance_year`, `continue_routine` or
  `perform_activity`. The routine span and the relationship's `shared_years`
  are unchanged by it (tested).

## 6. Persistence

Telling persists through both deaths: the row is the recipient's, and its
teller reference stays valid after the teller dies (the dead stay in the
registry). The successor is a different person and knows nothing. Recipe replay
reproduces knowledge rows and transcript byte-for-byte (tested).

## 7. Version and goldens

`ENGINE_VERSION` `0.5.0-playable-routine` → `0.6.0-knowledge-transmission`
(owner decision). The reason is measured, not presumed: seed 4, the same
command list (`work at`, `continue 10` ×2, `associate with 9`, `tell`,
`tell 1`, `continue 10` ×5), run on 0d609da and on this unit:

| | 0.5.0 (0d609da) | this unit |
|---|---|---|
| `tell` / `tell 1` | "… is not something you can do" | lists / tells Vegar |
| knowledge rows | 8, all `observed` | 9, one `told` |
| world minus `knowledge` (sha256/16) | `ad47810d82d99b24` | `ad47810d82d99b24` |

Same command text, different world, so the same version may not claim both.
The existing gate (`load._ensure_replayable`) refuses a 0.5.0 recipe outright;
nothing special-cases its `tell` lines (tested). `HELP` gained two lines, which
is part of the same boundary.

No golden moved: juncture goldens hold an empty `knowledge` list, so the new
field never serialises there, and the version string is not part of any
pinned hash.

## 8. Measured (seed 4, plus 1/7/17/42)

Policy: work 20 years, keep company with the youngest grown person there,
`tell 1` until refused after every 10 years, live to death.

| seed | observed | tell attempts | new | refused (nothing left) | knowers per told fact | recipient knows after teller's death | successor knows |
|---|---|---|---|---|---|---|---|
| 4 | 8 | 10 | 5 | 5 | 2 | 5/5 | 0 |
| 1 | 4 | 9 | 4 | 5 | 2 | 4/4 | 0 |
| 7 | 2 | 7 | 2 | 5 | 2 | 2/2 | 0 |
| 17 | 6 | 10 | 5 | 5 | 2 | 5/5 | 0 |
| 42 | 6 | 8 | 3 | 5 | 2 | 3/3 | 0 |

Observed > told because what a life sees in its last chunk of years is seen as
it dies; there is no later turn to tell it in.

Trace (seed 4): Vewen observes *Sellin rises to power* (y14) → keeps company
with Vegar (y20) → tells Vegar (row `TOLD`, from Vewen, y20) → Vewen dies y64
→ Vegar, alive, still knows; Vewen's own `OBSERVED` row remains; successor
Dunric knows nothing.

## 9. Known gaps

* Only the player's observations are recorded, so a recipient who stood in the
  same village may be recorded as *told* a thing they could also have seen.
  That is the observation rule's limit (`design_person_knowledge.md` §10), not
  this unit's.
* Multi-hop `A → B → C` is proven at domain level only; the player cannot
  control B, and NPCs do not tell.
* List indices shift as facts are told (as `status` indices shift as people
  come and go).
