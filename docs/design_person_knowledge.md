# Person knowledge — who knew what, and how they came to

Status: **implemented, uncommitted** (owner decisions 2026-10-09). Engine
version: **unchanged**, `0.5.0-playable-routine` (§8). Source of truth:
`knowledge.py`, pinned by `tests/test_knowledge.py`. Companions:
`design_routine_origin.md` (what a life did with its years),
`design_relationship.md` (who it was spent with),
`design_playable_routine_session.md` (the loop it is lived in).

One kind of truth: **this tracked person knows that this thing happened.**
Nothing else. No confidence, certainty, intensity, importance, valence or
score of how much anybody knows — the engine cannot measure those, and a
number it cannot measure is a fiction with a decimal point.

## 1. The existing memory systems (audit)

| | what it is | class |
|---|---|---|
| `models.Memory` (`valence`, `intensity`, `decay_rate`, `type: MemoryType`) | an **affect** record of one person's act toward another — `SAVED`, `BETRAYED`, `HUMILIATED` — decayed yearly by L2 | **C** old-core affect |
| `memory.form_memory` | writes a `Memory` *and* mutates `NPC.relations[actor].affinity/trust/fear` | **C** — the affect mutation is the point of it |
| its callers | `activity.perform_activity` and `powers.py` only — i.e. the old funnel | **D** retire-track with the funnel |
| `models.Relation` (`affinity`/`trust`/`fear`) | mutable affect, keyed on the **soul** in practice (`player-0000`) | **D**, already classified D by `design_relationship.md` |
| `social_memory_l2` | integer decay of those memories + `relation_bias` into `opportunity.npc_signals`, flag-gated | **C** |
| `Player.inherited.knowledge: list[str]` | strings carried **by the soul** across lives, derived from evaluation scores | **D** — the exact ownership model owner decision 1 forbids |
| `Memory.event_ref: Optional[str]` | a reference to a fact rather than a copy of it | **B** — the *concept* is reused here, the type is not |
| `models.Discovery` | a dungeon find keyed to a seed; no "who knows it" | **B** at most |

So nothing is reused. Every candidate is disqualified by at least one of:
affect values (`valence`, `intensity`, `decay_rate`), soul ownership
(`Player.inherited`, `Relation` keyed on `player-0000`), or being written only
by the activity funnel. `Memory` is also about *a person doing something to a
person*, not about a world fact — a different question entirely. The old
system is left running and untouched: a test asserts the legacy auto world
still forms affect-bearing memories, and that a played life forms none.

## 2. The record

```python
class PersonKnowledge(BaseModel):
    person_id: str
    event_id: str          # a CausalNode id
    learned_year: int
    source: KnowledgeSource = KnowledgeSource.OBSERVED
```

- **A reference, never a copy.** The event keeps its title, year, place and
  actors in `world.causal_nodes`. Copying any of it here would create a second
  truth that could disagree with the first. A test asserts the row has exactly
  these four fields.
- **No surrogate id.** `(person_id, event_id)` *is* the identity. An `id`
  would let the same person know the same thing twice, which is not a thing
  that can be true.
- **`KnowledgeSource` has one member, `OBSERVED`**, because one way of
  learning exists. Being told, taught or overhearing would each be a member
  here — not a second notion of what knowing is.
- **Discrete.** A test holds the field names `confidence`, `certainty`,
  `intensity`, `importance`, `valence`, `familiarity`, `strength` and
  `decay_rate` out of the model, so the next person cannot add one quietly.

## 3. Where it lives, and why it is stored at all

`World.knowledge: list[PersonKnowledge]` — an append-only registry, the same
shape as `World.npcs` and `World.routines`, for the same reason: what somebody
knew is part of history and not a property of whoever happens to be alive.

Unlike `relationship` and `routine_origin`, this **cannot** be a projection.
Who was present for what is not recoverable after the fact from a world that
records no attendance: location is static today, so a derived rule would make
every co-located living person know every local event — including people no
session ever observed anything as, and events in years nobody was living
through. That is a broader claim than the truth. So it is written once, when
it happens, and kept.

It is not on `NPC` because a dead person's knowledge has to stay answerable
without walking the registry for a body, and because the player's ownership
must be impossible to express — `World.knowledge` is keyed on `person_id`, and
there is nowhere to put a soul.

## 4. Observation is what establishes it

`routine_session._observe` is the one writer. It is deliberately a single
function that both reports and records:

```python
events = view.observed_events(world, person_id, nodes)
for event in events:
    learn(world, person_id, event.event_id)
```

So there is no state in which the page showed something the person does not
know. Measured: across seven seeds, **the number of lines the player read
equals the number of knowledge rows the world holds**, exactly, every time.

The visibility rule is unchanged — it happened where they were, either because
the event carries a `location_id` or because it names a tracked person who is
there. Nothing was loosened to give knowledge more to hold.

`EventView` gained `event_id` so that what was seen is nameable afterwards.
It travels for the same reason a routine target's id does, and is never read
by the player: a test asserts `node-` never reaches the page.

**A person who was there knew it the year it happened**, not the year the
session got round to printing it. So a `continue 10` and ten `continue 1`s
record identical `learned_year`s — pinned by a test.

## 5. Death, succession, and what does not transmit

| | |
|---|---|
| the person dies | their knowledge stays, queryable, forever |
| ten more years pass | it does not change |
| the next life begins | it knows **nothing**, and every row still names the predecessor |
| the successor lives | they learn only events from their own years (disjoint, all after the predecessor's death year) |

And three things that look like transmission and are not, each with a test:

- **Twenty years of `WORK_WITH` transmits nothing.** The relationship reports
  twenty shared years; the other person's knowledge is empty.
- **Being somebody's parent or child transmits nothing**, in either direction.
- **Co-location transmits nothing.** Standing where an event happened makes it
  *observable*; only observation records it. A neighbour who was equally
  present knows nothing, because nobody observed anything as them.

Relationship and genealogy may well be the *context* for a future
transmission verb. They are not an automatic effect, and this unit adds no
`TEACH`, `TELL` or `SHARE`.

## 6. Query surface

```python
knows(world, person_id, event_id)      -> bool
knowledge_of(world, person_id)         -> List[PersonKnowledge]   # learn order
known_events(world, person_id)         -> List[CausalNode]
who_knows(world, event_id)             -> List[str]
learn(world, person_id, event_id, source=OBSERVED) -> Optional[PersonKnowledge]
```

Reads are permissive, as `relationship.relationships_of` is: a person the
world has never heard of simply knows nothing. **Writes are strict** —
`learn` raises `KnowledgeRefused` for a person not in the registry or an event
that is not in the graph, because knowledge of a thing that did not happen is
the one row this registry must never hold. `learn` returns `None` when they
already knew, and never moves `learned_year`.

## 7. No player-facing surface was added

`status` does not list knowledge and `history` is unchanged, and no new
command was added. The observation feed already shows each event as it is
learned, and the payoff of a knowledge *list* belongs to the unit that can do
something with it. The unit's point is engine truth, and the engine truth is
testable without a command.

## 8. Version and goldens

`ENGINE_VERSION` is **not** bumped. The policy bumps when a change "would
alter the world produced from a given seed + inputs"; this alters the schema,
not the world. Proof: stripping `knowledge` (an empty list in every legacy
world) from the seed42 dump reproduces the previous golden
`114f070ee0e09908` **byte-for-byte**. Replay is therefore still sound, and a
bump would invalidate every recipe ever saved in exchange for nothing.

Two world-dump constants move, class **A**, for the one extra field:

| | from | to |
|---|---|---|
| `GOLDEN_WORLD_SHA` / `GOLDEN_SEED42_SHA` (8 files) | `114f070ee0e09908` | `7f934e5a68866c12` |
| `GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA` | `3b992792cd9c88ea` | `96d812137c1ea529` |

Every **rendered** lens golden — transcript, chronicle, digest, narrative,
timeline, character, legacy, observatory, social memory, world model — is
byte-identical.

## 9. Measured (seven seeds, two lives each)

| seed | lines shown | life 1 knows | life 2 knows | rows | duplicate rows | unplaceable events |
|---|---|---|---|---|---|---|
| 1 | 7 | 4 | 3 | 7 | 0 | 0 |
| 2 | 4 | 2 | 2 | 4 | 0 | 0 |
| 4 | 11 | 8 | 3 | 11 | 0 | 0 |
| 7 | 5 | 2 | 3 | 5 | 0 | 0 |
| 17 | 10 | 6 | 4 | 10 | 0 | 0 |
| 42 | 20 | 6 | 14 | 20 | 0 | 0 |
| 99 | 8 | 5 | 3 | 8 | 0 | 0 |

Two things to read honestly from this.

**Duplicate rows are zero, and not because suppression is idle.** No node is
ever offered to `_observe` twice — the session slices only the nodes a
`continue` block created. Suppression is real and exercised directly: a test
learns the same event twice and gets one row with the first year intact.

**Unplaceable events are zero in every routine-first world.** Everything a
played run generates is a tracked person rising to power, and a person is
somewhere. Faction wars need rival power the quiet years never build, and
wildcard ignition needs activity seeds a played life never plants. So the
withholding half of the visibility rule currently withholds nothing *in these
worlds* — it is still correct, and is tested against a constructed event the
world genuinely cannot place. This is observation truth, not a missing filter.

Knowledge counts are small (2–8 per life) for the same reason: a quiet world
produces few local events. A seed with none would mean a life that saw
nothing happen, which is a legitimate life.

## 10. Known gaps

- **No transmission.** `TEACH` / `TELL` / `SHARE`, rumour, misinformation and
  forgetting are all out. `KnowledgeSource` is the seam they arrive through.
- **Only the player observes.** NPCs are never the subject of `_observe`, so
  every row in every world names a played person. The registry is keyed on
  persons and ready for more, but nothing else looks.
- **Nothing reads knowledge back.** No surface, lens or rule consumes it yet;
  a later life cannot find out what an earlier one knew.
- **Knowledge does nothing.** Like a routine origin, it is truth without an
  effect translator, and that is the same open question by design.
