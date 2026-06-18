# P9-4 Lineage Viewer — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** Parent: `docs/design_p9_persistent_history.md` (approved).

## Purpose

Show the player **"what did I leave to the world?"** — not one life (that is P7's
`life_timeline`), but the **whole chain of reincarnations** and the heritage thread
running through it. A read-only projection of a finished world into player-facing
Markdown; it computes nothing new and mutates nothing.

## Grounding (existing read-only assets reused, none modified)

`reporting/_data.py` and `reporting/labels.py` already provide everything, all
read-only and deterministic:

- `life_index(world)` — life id → 1-based ordinal; `life_label`, `life_by_id`.
- `seeds_of_life(world, life_id)`, `seed_by_id`, `triggered_node`.
- `life_world_impact(world, life_id)` — events a life's seeds caused (**影響度**).
- `heritage_rows(world)` — name / score / longevity / reach / `origin_life`
  ("Life N") / type, **sorted by `-score, source_seed`** (deterministic, id-free).
- `heritage_name(heritage)` — a proper name, never an id.

`Life` carries `birth_year`, `death_year`, `age_at_death`, `talent`,
`summary.title`. Heritage founder = `heritage.seed_id → seed.planted_by_life_id`.

## Decision 1 — Lineage unit: the life-chain is the spine

The brief lists four candidate units (person / family / organization / heritage).
**Recommendation: the spine is the chain of lives; the others attach to it.**

| candidate | role in the view |
|---|---|
| **person (life)** | a **node** — one section per life |
| **family (reincarnation chain)** | the **ordering** of nodes — every life is the player reborn, so the "family" *is* the spine |
| **heritage** | the **payload** of a node — what a life left behind (and what later lives were born into) |
| **organization (faction)** | an **attribute** — a life's affiliation/affected faction, named, not a separate spine |

Rationale: "私は世界へ何を残したか" reads as *a sequence of selves, each leaving
something*. A heritage-centric or faction-centric view is a valid alternate lens
(possible future), but the lineage's intrinsic axis is the chain of lives. So the
primary unit is **Life**, with heritage as its contribution.

## Decision 2 — Display order: chronological default, selectable

A lineage is intrinsically a sequence, so **chronological (birth order) is the
default**. The other two are alternate sorts via an `order` parameter:

| `order` | spine ordering | reading |
|---|---|---|
| **`"chronological"` (default)** | birth year, then ordinal | "I was born, lived, died, reborn" |
| `"impact"` | `life_world_impact` desc, then ordinal | "which self mattered most" |
| `"generation"` | distance from the latest life (newest→oldest), then ordinal | "how far back each self is" |

All ties break on the life ordinal (no set/dict iteration dependence). An unknown
`order` raises `ValueError`. Every order contains **all** lives — only the
sequence differs.

## Decision 3 — No internal ids (the P8 lesson)

Every identifier is humanized via `labels`/`_data`; raw ids never reach the
player. Lives are shown as **"Life N — <title>"** (ordinal + `summary.title`,
falling back to talent + place), heritage via `heritage_name`, factions by
`faction.name`. The view never prints `life.id`, `seed.id` (`seed-XXXX`),
heritage/npc/node ids, or `legacy:` strings. (Test: no `\b(seed|life|npc|node|
loc|fac|her)-\d` and no `legacy:` in the output. "Life 3" — an ordinal — is fine;
"life-0003" is not.)

## Architecture

- **`reporting/lineage.py` (new, additive):** `lineage_view(world, *,
  order="chronological") -> str`. Imports `_data` + `labels` (read-only). It does
  **not** modify `reporting/experience.py` (P7, frozen) or `reporting/__init__.py`
  — tests import the submodule directly, so the addition touches no existing file.
- **Untouched (inviolable):** `models.py`, P6, P7 (`experience.py` and all
  existing reporting modules), P8, P9-1/2/3, the seed42 golden assets. The viewer
  is read-only on the world (asserted by a `model_dump` equality test).

> **Open point for the reviewer (location).** I place the viewer in
> `reporting/lineage.py` because the read-only data/label helpers live there and
> P7's frozen `experience.py` is a *sibling*, not modified. Alternative: a new
> `views/` package. **Recommend `reporting/lineage.py`** (reuses `_data`/`labels`
> with no new wiring). Please confirm.

## API (signature)

```python
def lineage_view(world: World, *, order: str = "chronological") -> str
```

## Shape (player-facing Markdown, illustrative — tests pin invariants, not prose)

```
# The line you have walked

> 4 lives, 40 years, one soul reborn.

## Life 1 — A scholar of Hollowfen
- Born year 0, died year 18 (aged 18), in an age of governance.
- Left behind: the Order of the Stone Pact.

## Life 2 — A warrior of Hollowfen
- Born into a world already shaped by the Order of the Stone Pact.
- Left behind: the Doctrine of the Long Dawn.

…

## What outlived them all
- The Doctrine of the Long Dawn — still shaping the world.
- The Order of the Stone Pact — …
```

- Per life: identity (ordinal + title), born/died/age + era, **Left behind**
  (founded heritage names, or "Left no lasting mark"), and — realizing the
  inheritance thread/世代距離 from founding years alone — **Born into** (heritage
  founded by earlier lives, no per-life tending data needed).
- Tail: the cumulative heritage that outlived everyone (by `heritage_rows` order).

## Determinism & seed42

- `lineage_view` is byte-deterministic for a given world + order (stable sorts,
  no set/dict iteration leak).
- Read-only: the world's `model_dump()` is identical before and after.
- The golden world (`simulate_world(42)`) is only *read*; its hash is unchanged.

## Test plan (failing — `tests/test_lineage.py`, RED until implemented)

Over `simulate_world(42, mode="opportunity")` (4 lives, has heritage):

- `test_lineage_lists_every_life_in_birth_order` — `^## Life N` headers are
  exactly `1..len(lives)` in order.
- `test_lineage_attributes_founded_heritage` — every `heritage_rows` name appears.
- `test_lineage_no_internal_ids` — no `\b(seed|life|npc|node|loc|fac|her)-\d`,
  no `legacy:`.
- `test_lineage_is_read_only` — `model_dump_json` unchanged across the call.
- `test_lineage_is_deterministic` — two calls byte-identical.
- `test_lineage_is_markdown_readable` — starts with a `#` title.
- `test_lineage_order_modes_accepted_and_complete` — chronological/impact/
  generation each contain all lives and are deterministic.
- `test_lineage_rejects_unknown_order` — `ValueError`.

## Implementation plan (after approval — small commits)

1. `reporting/lineage.py` (`lineage_view` + order modes + helpers) → all
   `test_lineage.py` green.
2. (If a CLI surface is wanted) additive `--lineage` on the play CLI, like
   `--export` — proposed separately; not part of this issue's failing tests.

## Constraints honored

- **Read-only projection only**; World unchanged (asserted).
- `models.py` / P6 / P7 / P8 / P9-1 / P9-2 / P9-3 untouched; `lineage.py` only
  imports the existing read-only helpers.
- No internal ids in output (humanized labels only); seed42 golden inviolable.
