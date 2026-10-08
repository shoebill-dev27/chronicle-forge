# Routine origin — a lived routine as causal input

Status: **implemented, uncommitted** (owner decisions 2026-10-05, revised
2026-10-07/08). Engine version: **unchanged**, `0.5.0-playable-routine`.
Source of truth: `routine_origin.py` and `play/view.py`, pinned by
`tests/test_routine_origin.py`. Companions: `design_routine.md` (the spans),
`design_relationship.md` (the social reading of the same spans),
`design_playable_routine_session.md` (the loop they are lived in).

## 0. What is implemented, precisely

> **A Routine causal origin / input representation is implemented.**
> **Effect translation is intentionally unresolved.**

Read that as written. This unit is not "Routine causality"; it is the origin
side of it, and the other side is an open design question (§7).

What exists:

- `RoutineOrigin` — a **derived, read-only projection** over `World.routines`:
  actor, kind, place, person, chronology, and a duration computed from that
  chronology. Nothing is stored and the world is never written to.
- The `continue` **observation channel** — events the world produced on its own,
  shown to the player when they were where it happened.

What does **not** exist, by decision and not by omission:

| | |
|---|---|
| `SeedDomain` mapping | **none.** A routine belongs to no seed domain. |
| magnitude / weight / strength / scale | **none.** Years are kept as years. |
| `CausalSeed` planted from a routine | **zero.** |
| `CausalNode` generated from a routine | **zero.** No causal edge either. |
| Heritage promotion | **zero.** No `SCHOOL`, no heritage of any type. |
| `ThemeAxis` contribution | **zero.** How you live moves no theme. |
| a translator from origin to world effect | **does not exist.** §6, §7. |

So: a lived routine is a first-class historical origin and a causal *input*
that differs between differently-lived lives. It does not yet do anything to
the world, and nothing here pretends otherwise. The observation channel is
**independent** of it (§5): the player is shown events because they were
present, never because a routine caused them.

## 1. What was rejected, and why it had to be

The first attempt routed routines into the existing `CausalSeed` machinery. It
worked, in the sense that lives diverged and heritage appeared. It was wrong,
in four specific ways, and all four were owner-rejected:

| rejected | what it actually asserted |
|---|---|
| `Routine → SeedDomain.HERITAGE` | that every way of living belongs to the engine's "culture/legacy" domain — chosen because the other seven were worse, which is not a reason |
| heritage promotion → `SCHOOL` | that forty years in somebody's company founds a **school**. A fabricated institution. |
| `magnitude = min(100, years)` | that a year and a point of seed magnitude are the same unit. They are not; nobody decided a conversion rate. |
| fire at `span end + 10` | a rule derived from `CausalSeed` being one-shot, not from anything routines mean. An implementation artifact dressed as semantics. |

Each one was a small invention that let the pipeline close. Together they
would have put fabricated consequences into world history, under a commit that
claimed to be about truth.

## 2. Corrected reading of `CausalSeed`

The audit's original verdict (reusable) was **wrong**, and the evidence that
looked like support is actually the disproof.

`CausalSeed` is a **one-shot event trigger**: it fires once
(`fired=True`, never re-examined), produces exactly one `CausalNode`, and its
`magnitude` is consumed at that single instant. That is a faithful model of *an
act* — somebody did a thing in a year, and later it had a consequence.

A routine is not an act. It is a condition that holds across years and whose
extent is not known while it is running. Making a one-shot trigger stand for a
continuing condition forces a choice between three bad options: fire early and
truncate the span, fire late and invent a delay, or re-plant per year and
destroy "one routine, one origin". The first draft chose the second. The right
answer is that **`CausalSeed` is the wrong input type**, and no amount of
adapter makes it the right one.

So: **routines plant no seeds.** The legacy `perform_activity → CausalSeed`
path is a faithful use of that model and is untouched.

## 3. The origin

```python
@dataclass(frozen=True)
class RoutineOrigin:
    routine_id: str
    actor_person_id: str
    kind: RoutineKind
    location_id: str
    target_person_id: Optional[str]
    start_year: int
    end_year: Optional[int]
    duration_years: int
```

`routine_origin.py` stores nothing and writes nothing — a test asserts the
world dump is byte-identical across a query. Like `relationship.py`, which is
the *social* reading of the same spans, this is the *causal* reading of them.
The `Routine` remains the only record.

- **No second duration.** `duration_years` is `routine_years(...)` computed on
  the way through. Rewriting a span rewrites the duration; pinned by a test.
- **No strength of any kind.** No magnitude, weight, scale, domain or seed id.
  A test asserts those field names are absent, so the next person cannot add
  one quietly. Years are kept as years.
- **One completed year is the threshold, and the only one.** Choosing how to
  live is not living that way. Below a whole year there is no origin at all.
- **Closed origins are frozen by chronology, not by a flag** — `end_year` stops
  moving, so the record does.

## 4. The graph boundary (option B)

`CausalGraph.add_edge` accepts a cause that is either an existing `CausalNode`
or something in `world.seeds`. Those are the only two root types the schema
has, and a routine origin is neither. Making it one would mean either faking a
seed (rejected above) or adding a root type with no edges leading anywhere —
a root with no effects contributes nothing but a false impression that it does.

**So the origin projection sits beside the graph, not in it**, as a causal
*input* layer. "The origin exists; there is no translator to an effect yet" is
a true statement about this engine, and it is the one being shipped.

## 5. Observation (kept)

`continue` reports what happened around the player, by one rule that uses only
existing truth:

> an event is observed if it happened where the player is — either the event
> carries its own `location_id`, or it names a tracked person, and that person
> is where the player is.

The first branch is currently never taken: **no emitter in the engine sets
`CausalNode.location_id`.** What reaches the player is therefore
`population._promote` — "X rises to power", naming a tracked person who is
somewhere. Faction wars and wildcard events name neither a place nor a person
the world can place, so they are shown to **nobody** rather than to everybody.

```
> 
10 years pass.

  Year 21. Lynwen rises to power.
  Year 28. Dundal rises to power.
```

**This channel is independent of routine origins.** These are events the
world simulation produced on its own; the player is shown them because they
were there, not because they caused them. No routine origin is ever injected
into this feed as if it were an event. No cause, no path, no "because", no id —
held by a regex test over three full played lives.

## 6. What a routine origin could truthfully drive — and cannot yet

Every seam the engine actually has, with the input it actually demands:

| seam | required input | would it be truthful from routine truth? |
|---|---|---|
| `generation.generate_events` | a fired `CausalSeed`: `SeedDomain` + `magnitude` | **No.** Needs a domain and a year→magnitude rate. Both are owner decisions. |
| `heritage.promote_heritage` | a fired seed whose domain is in `DOMAIN_TO_HERITAGE_TYPE`, plus its TRIGGERed node | **No.** Downstream of the above, and its vocabulary (`SCHOOL`, `MONUMENT`, `INSTITUTION`…) has no word for a way of living. |
| `theme.compute_theme` | `CausalNode` (domain, scale, year) | **No.** Only reads nodes; a node needs the domain decision first. |
| `macro.step_wildcards` ignition | theme axis ≥ threshold **and** `_player_seed_support(axis) ≥ 2` — fired seeds with `planted_by_life_id` | **No.** Keyed on seeds and a ThemeAxis. |
| `macro.step_factions` | theme axes, faction power, rng | **No.** Reads no person and no place; nothing to attach a routine to. |
| `population._promote` | `personality.ambitious > 70` + probability | **Partly.** Place and co-presence are truths a routine owns. "Who rose" could read who was beside whom — but *that working beside somebody helps you rise* is an invented social claim. |
| `population._births` | adults over `ADULT_AGE`, excluding the player | **Partly.** Who is co-located is routine truth. Who has children with whom is a modelling decision nobody has made. |
| `mortality.HAZARDS` | a registered `(world, life, rng) -> DeathCause \| None` callable; the list is **empty by design** | **The closest fit.** The seam is an explicit extension point ("early death is what such a context will supply"), takes the whole world and life, and needs no unit conversion. It still requires deciding **which ways of living are dangerous**, which is an owner call. |
| `memory.form_memory` | subject, actor, `MemoryType`, valence, intensity | **No.** Valence and intensity are exactly the affect this engine refuses to infer from proximity. |
| `opportunity.npc_signals` (L2) | `NPC.relations[soul_id]` | **No.** Keyed on the soul, not a person; classified D and retire-track. |

Pattern: every existing seam wants either a **unit** (magnitude, valence,
intensity) or a **category** (SeedDomain, HeritageType, ThemeAxis) that
routines do not supply, and that cannot be derived from "N years, this kind,
this place, this person" without a decision.

## 7. Open design questions (owner)

1. **What is the unit of a routine's causal strength?** Years, a derived
   scale, or none at all — does a routine ever get a magnitude?
2. **Does a way of living belong to a `SeedDomain`,** or does routine
   causality need its own root type and its own effect vocabulary?
3. **What does `WORK_WITH` actually do to the two people in it?** Until there
   is an answer, there is no truthful translator.
4. **Is `mortality.HAZARDS` the first effect seam** — i.e. does how you live
   change when you die? It is the only seam that needs no invented unit.
5. **Should sixty-four short spans ever outweigh one long one,** or is total
   years lived the only quantity that may matter?

None of these are implemented. They are returned as decisions.

## 8. What this does and does not fix

The playability audit measured: same seed, same sixty-four years, any way of
living → **byte-identical** causal world. After this unit:

| | A: one 64-year span | B: person-focused | C: 7 spans | D: change every year | A′: A typed one year at a time |
|---|---|---|---|---|---|
| routine origins | 1 | 8 | 7 | 64 | **1** |
| origin fingerprint | `7be376ff…` | `ec11c534…` | `b7052af6…` | `95f912ac…` | **`7be376ff…`** |
| seeds / heritage | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| causal nodes | 16 | 16 | 16 | 16 | 16 |
| theme axes | same | same | same | same | same |

**Fixed:** the causal *input history* now differs by how you lived, and does
not differ by how you typed (A ≡ A′).

**Not fixed:** the causal *output* — nodes, heritage, theme — is still
identical across all four lives. That is the honest remaining half of the
audit's defect, and it stays open until question 2 or 4 above is answered.
Closing it by inventing a domain is what this revision removed.

## 9. Known gaps

- **No effect translator**, by decision. §6 and §7.
- **Only the player lives routines.** NPCs create no origins, so even the
  input divergence is one person deep.
- **Nothing reads an origin back to a later life.** The projection exists; no
  surface tells a successor what a predecessor's years were.
- **`CausalNode.location_id` is still set by nobody**, so the observation
  channel's primary rule is dormant and faction/wildcard events reach no one.
