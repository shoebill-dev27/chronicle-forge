# Relationship — what two people have between them, read off history

Status: **implemented, uncommitted** (owner decisions 2026-10-02). Companion to
`design_routine.md` (the spans) and `design_population_continuity.md` (the
people). Source of truth: `relationship.py`, pinned by
`tests/test_relationship.py`. **No new world state.**

This is not a friendship system. The engine does not decide that seven years
beside someone made them a friend, or that a parent was loved. It answers only
what history can answer:

- is there anything between these two, and on what grounds
- how many years did they directly share, in which routines
- when did that start, when did it last run, is it still running
- is one of them directly the other's parent or child

## 1. The old `Relation` is a different thing (audit)

`models.Relation` (`affinity` / `trust` / `fear`) is **not** reused, and is not
touched. Evidence from the repo:

| | old `Relation` | new Relationship |
|---|---|---|
| key space | `NPC.relations[soul_id]` — **only ever `player-0000`** | a pair of tracked persons |
| content | mutable affect, decayed yearly by `social_memory_l2` | historical evidence, derived |
| written by | `memory.form_memory`, a side effect of the old activity funnel | nothing — it is a projection |
| read by | `opportunity.npc_signals` (flag-gated L2 bias), `reporting/social_memory` (L1 lens), `views.render_npc_codex` | its own callers |
| reach | **5 of 226 people** in a 200-year seed-42 world | every pair the evidence names |

Classification: **D — old-core, retire-track, kept separate.** It cannot
express "A and B" at all (its keys are the soul, not a person), and its content
is precisely the emotion this unit must not invent. Nothing in `relationship.py`
imports or depends on it, so retiring the old activity path later costs this
unit nothing.

## 2. Derived, not stored

A relationship is a **projection**, computed on demand from facts that already
exist:

- `World.routines` — the `WORK_WITH` / `ASSOCIATE_WITH` spans
- `Lineage.parent_ids` — on the people themselves

Reason: a stored tie would be a second copy of a number the sources already
determine, and a second copy can disagree. It is the rule age and routine
duration already follow. It also means there is nothing to update when a
routine ends, nothing to clean up when somebody dies, and nothing to migrate.

Because nothing is stored, **the world dump is unchanged and no golden moves.**

## 3. Evidence

| ground | source | gives shared years? |
|---|---|---|
| `SHARED_ROUTINE` | a `WORK_WITH` or `ASSOCIATE_WITH` span naming both | yes |
| `GENEALOGY` | one is directly the other's parent | **no** |

`WORK_AT` is not evidence: being in the same village is not a relationship.
Neither is co-location on its own.

**Which routines count as shared time is decided here, not inherited.**
`relationship.SHARED_TIME_ROUTINE_KINDS` names `WORK_WITH` and
`ASSOCIATE_WITH` explicitly rather than reading `routine.PERSON_KINDS`. The two
sets answer different questions — "aimed at a person" and "was time spent
together" — and they will come apart. A future one-shot favour, or betraying
somebody, would be person-facing and must **not** start adding years to how
long two people lived side by side just by joining an enum. Admitting a new
kind to shared time is a deliberate edit to this module, pinned by a test that
widens `PERSON_KINDS` and checks relationships do not widen with it.

Future grounds — helping, teaching, learning, opposing, betraying — are added
as a `RelationshipEvidence` member and a collector; the shared-time rule and
the query surface do not change.

A grandparent is **ancestry**, not a relationship. Only the direct parent-child
step counts here; the rest is `population.ancestors`.

## 4. Shared time

Years are **half-open `[start_year, end_year)`**, exactly as routines are, and
shared time is the **union** of the spans that put the two together:

```
WORK_WITH      [12, 19)   7 years
ASSOCIATE_WITH [25, 30)   5 years
                        ──────────
shared_years              12        (the six years apart are not shared)
```

- A span still being lived is measured against the clock: `start_year = 40`,
  `current_year = 44` → **4** completed years.
- Starting a routine and asking in the same year gives **0**. Pressing the
  button is not a year spent together.
- Overlapping spans contribute their union, never their sum. One player cannot
  currently produce an overlap — one active routine at a time — but that is a
  property of today's command rules, not of what a shared year means, so the
  calculation does not assume it.

`last_shared_year_exclusive` is named for the convention so it cannot be
misread: it is the first year they were *not* together.

## 5. Symmetry and direction

**Shared history is a fact about the pair.** Whoever began the routine, both
`relationship_between(world, a, b)` and `relationship_between(world, b, a)`
report the same spans, the same years, the same chronology.

**Genealogy keeps its direction.** `genealogical_role` is *what B is to A*, so
asking the other way round inverts `PARENT` and `CHILD`. Later grounds that are
genuinely one-directional (who taught whom, who owes whom) fit the same shape.

## 6. Death and reincarnation

Nothing here deletes or mutates its sources, so:

- a routine ending leaves every shared year intact; only `sharing_now` goes false
- the other person's death leaves the record exactly as long as it was
- the player's own death does too
- the successor **inherits nothing**: ties are keyed on persons, and the next
  life is a different person. Player continuity is not character relationship
  continuity.

The dead stay queryable, which is the point — they are what a life's history is
made of.

## 7. Query surface

```python
relationship_between(world, person_a_id, person_b_id) -> Optional[Relationship]
relationships_of(world, person_id)                    -> List[Relationship]
```

`relationship_between` returns `None` when the world says nothing — two people
history never put together do not get an empty record, and nobody has a
relationship with themselves. `relationships_of` lists **only** evidence-backed
people, ordered by the other person's id, so a world of two hundred strangers
is not two hundred relationships.

## 8. What this unit refuses to do

No friendship, trust, affection, hostility, rivalry or reputation. No decay.
No score of any kind. Ten years together is ten years together; what it meant
is not the engine's to say, and a later layer that wants to say it will say it
from this evidence rather than instead of it.
