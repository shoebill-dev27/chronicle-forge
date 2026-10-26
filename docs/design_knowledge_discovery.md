# Knowledge discovery — the player may ask what somebody knows

Status: **implemented, uncommitted** (2026-10-25). Engine version:
**`0.8.0-knowledge-discovery`** (§6). Source of truth: `PersonKnowledge`
(`models.py`), `knowledge.tell`, `play.view.recollections`,
`play.routine_session._ask`, pinned by `tests/test_knowledge_discovery.py`.
Builds on `design_knowledge_transmission.md` and `design_movement.md`.

The loop this closes:

    life A sees E → A tells B → A dies → successor C moves to B
    → C asks B → B says E, and how they first came to know it
    → the player, not the engine, recognises A

## 1. Where a telling happened is stored

Audit (0.7.0): a told row held the teller and the year, not the place. The
place was not recoverable from anything else that is exact:

* the teller's and recipient's `location_id` are where they live *now*, and
  the player moves;
* the routine beside the recipient is half-open `[start, end)`. Tell in year
  20, then `move` in year 20, and that span is `[20, 20)`: it covers no year,
  so no lookup by year finds it (pinned by a test). Birthplace is a guess.

So the place is written at the moment of telling:

    PersonKnowledge.told_at_location_id: Optional[str]  # TOLD only

* TOLD ⇔ `learned_from_person_id` is set ⇔ `told_at_location_id` is set
  (model validator). First acquisition wins: a later telling changes nothing,
  place included.
* OBSERVED rows have no place. The narrower field was chosen over a general
  `learned_at_location_id` on purpose: somebody who saw an event saw it where
  it happened, which is the event's truth and not this row's — storing it
  here would be a second copy that could disagree. "Where it happened" and
  "where they heard of it" are never one field.
* `knowledge.tell` now also refuses a recipient who is not where the teller
  is, because a telling in two places has no place to record. The playable
  path could never do this (a routine target is always co-located, and moving
  closes the routine), so no played behaviour changes.

## 2. What the player can read: `view.recollections(world, person_id)`

One `RecollectionView` per row of **that person's** knowledge, in the order
they came to know it: event year and title, `learned_year`, and for a telling
the teller's name, the teller's age then (`learned_year − teller.birth_year`,
read from the teller by id), and the place name of the telling. Nothing is
stored: names, ages and place names are derived on read. Nothing else is
read — no other person's rows, no event the person does not know, no
`CausalSeed`, edge, `CausePath` or reason.

## 3. The command

    > ask
    People you could ask:
      [1] Braric, 79
      ...
      [4] Vegar, 71
      ...

    > ask 4
    Vegar remembers:
      Year 14. Sellin rises to power.
        Heard of it in year 20 from Vewen, then 36, in Hollowfen.

A person who saw it: `Saw it happen.` A person who knows nothing:
`Vegar knows of nothing that has happened.`

* Who can be asked is `view.nearby` — the living grown people here — numbered
  exactly as `status` numbers them (`_target` is reused). Not limited to the
  routine target: finding out comes before deciding whom to live beside.
* Asking takes **no year** and **changes nothing** (`model_dump` identical):
  no knowledge, memory, relationship, seed or provenance — not even for the
  asker. What the player reads, the person they are does not thereby know.
  That is deliberately unlike observation, where seeing is knowing.
* Invalid numbers and non-numbers are refused at no cost. The dead are never
  listed; their knowledge stays queryable internally (no archive surface).
* Nothing names a relation between the teller and anybody: no "previous
  life", "you told", "this was you". Ids, enum names and words like
  "provenance" never appear.

## 4. Same names

The teller is resolved by `learned_from_person_id`, never by name, so a
namesake can never lend an age or place. Same-name people here are separate
list entries, asked by number, each answering with their own rows.

The age-then is what disambiguates in practice. Seed 4, year 75: a living
"Vewen, 32" stands in the same list as Vegar, but "Vewen, then 36, in year
20" was born in year −16; the living one was born in 43.

## 5. Measured (seeds 4, 17, 42; maximal-telling play, then move and ask)

| | count |
|---|---|
| previous-life recipients | 12 |
| alive at succession / reached / asked | 6 / 6 / 6 |
| previous-life told facts held by them | 37 |
| surfaced by `ask` | 37 |
| evidence (name, age then, place, year) exactly life A's | 37 |
| false identity matches | **0** |
| asks with a living namesake of the teller in the same list | 2 of 6 |
| facts whose evidence any other registered person also fits | 0 |
| attribution words / asker knowledge gained | 0 / 0 |

"Fits" means: anybody else in the whole registry with the same name, born in
`year − age`, living in that place. The check for the place uses life A's
home, valid here because these runs never move; the moved case is pinned by
a unit test.

## 6. Version

`0.7.0-movement` → `0.8.0-knowledge-discovery`: `ask` lines were unknown
commands under 0.7.0, and told rows gained a field. The existing gate refuses
a 0.7.0 recipe (tested). A recipe with `move` and `ask` replays to the same
transcript and the same `model_dump`. No golden moved.

## 7. Known gaps

* A recipient told many things answers with all of them (13 facts in one
  measured case); there is no asking *about* something.
* The successor cannot act on what they hear: they do not know it, so they
  cannot tell it on. Whether hearing should become knowing is open.
* Names are still the only identity a person has on screen; the age-then is
  doing the work. A teller with no birth year would print without an age.
* The successor's own past is not shown anywhere either, so recognising
  "Vewen, then 36" depends on the player remembering their earlier life.
