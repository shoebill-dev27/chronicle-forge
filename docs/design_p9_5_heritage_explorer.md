# P9-5 Heritage Explorer — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** Parent: `docs/design_p9_persistent_history.md` (approved).
The last P9 issue.

## Purpose

Show the player **"what endured?"** — the world's heritage as a browsable
catalog. Where P9-4 Lineage answers *who left it* (the chain of selves), P9-5
answers *what remained*: each legacy's significance, longevity, reach, origin,
and whether it is **still shaping the world**. A read-only projection into
player-facing Markdown; it computes nothing new and mutates nothing.

## Grounding (existing read-only assets reused, none modified)

`reporting/_data.heritage_rows(world)` already yields, **sorted by `-score, then
source_seed`** (deterministic), one row per heritage with: `name`
(`heritage_name`, id-free), `score`, `longevity`, `reach`, `type`, `domain`,
`derived_events`, `origin_life` ("Life N" — an ordinal, never a raw id),
`origin_action`, `source_seed`. `reporting/labels.heritage_name` and
`theme.SEED_DOMAIN_TO_THEME` complete the picture. (`reporting/heritage_table.py`
is a separate **developer** table — left untouched; this is the player view.)

## Decision 1 — Sort order: score default, selectable

Heritage's composite significance is `score`, so **`score` is the default**
(highest first, matching `heritage_rows`). The brief's other axes are selectable
via a `sort` parameter:

| `sort` | order | reading |
|---|---|---|
| **`"score"` (default)** | `-score`, then `source_seed` | "what mattered most" |
| `"longevity"` | `-longevity`, then `source_seed` | "what lasted longest" |
| `"reach"` | `-reach`, then `source_seed` | "what spread widest" |
| `"origin"` | founder life ordinal asc, then `source_seed` | "earliest founders first" |

All ties break on `source_seed` (deterministic, no set/dict iteration). An
unknown `sort` raises `ValueError`.

## Decision 2 — Grouping: flat default; type / founder optional

Default is a **flat sorted list** (`group_by=None`). Optional groupings:

| `group_by` | groups | group order |
|---|---|---|
| `None` (default) | — (flat) | — |
| `"type"` | by heritage type (Doctrine / Order / Engine / …) | by the top score in each group, then type name |
| `"founder"` | by `origin_life` ("Life N") | by founder ordinal asc |

Within a group, rows follow the chosen `sort`. An unknown `group_by` raises
`ValueError`.

> **Faction grouping — deferred (open point).** Heritage has no direct faction
> link; the only path is `seed.target_id` *when* it resolves to a faction, which
> is sparse (most heritages would fall into a large "unaffiliated" bucket).
> Recommend deferring faction grouping to a future iteration and shipping
> `type`/`founder` now. Please confirm.

## Decision 3 — "Still shaping the world" (open point, proposed definition)

A heritage is marked **"still shaping the world"** when its **domain aligns with
the world's final dominant theme** — i.e. it steered the age the world ended in:
`SEED_DOMAIN_TO_THEME[seed.domain] == world.theme.dominant`. Living legacies get
the phrase; the rest read as having faded.

- Rationale: "the world" *is* its theme; a legacy still shaping it is one whose
  current still runs in the dominant axis. Meaningful and fully data-grounded.
- Alternative considered: a `longevity` threshold ("lasted ≥ X years"). Rejected
  as default because it measures *past* propagation, not *present* influence.
- If the world has no dominant theme, nothing is "still shaping" (all faded).

**Please confirm this definition.** The failing test
`test_explorer_living_status_matches_theme_alignment` encodes it independently, so
a different definition only changes that one test.

## Decision 4 — No internal ids (the P8 / P9-4 lesson)

Every identifier is humanized: heritage via `heritage_name`, founders via the
`origin_life` ordinal ("Life N"), targets by name. The view never prints
`seed.id` (`seed-XXXX`), heritage/npc/node/faction ids, or `legacy:` strings.
(Test: no `\b(seed|life|npc|node|loc|fac|her)-\d`, no `legacy:`.)

## Architecture

- **`reporting/heritage_explorer.py` (new, additive):**
  `heritage_explorer(world, *, sort="score", group_by=None) -> str`. Imports
  `_data` (`heritage_rows`, `seed_by_id`), `labels`, and `theme`
  (`SEED_DOMAIN_TO_THEME`) — all read-only. Sibling to `lineage.py`; does **not**
  modify `reporting/experience.py` (P7), `reporting/heritage_table.py`, or
  `reporting/__init__.py` (tests import the submodule directly).
- **Untouched (inviolable):** `models.py`, P6, P7, P8, P9-1/2/3/4, the seed42
  golden assets. Read-only on the world (asserted by a `model_dump` test).

## API (signature)

```python
def heritage_explorer(world: World, *, sort: str = "score", group_by: Optional[str] = None) -> str
```

## Shape (player-facing Markdown, illustrative — tests pin invariants, not prose)

```
# What endured

> 12 legacies survived the lives that made them.

- **The Doctrine of the Long Dawn** — Doctrine, founded by Life 2 · still shaping the world.
  Reached 9 events over 28 years.
- **The Order of the Stone Pact** — Order, founded by Life 1.
  Reached 4 events over 12 years.
…
```

With `group_by="type"`:

```
### Doctrines
- **The Doctrine of the Long Dawn** — founded by Life 2 · still shaping the world.
### Orders
- **The Order of the Stone Pact** — founded by Life 1.
```

Each heritage is a `- **{name}**` entry; group headers are `### {group}`.

## Determinism & seed42

- `heritage_explorer` is byte-deterministic for a given world + sort + group_by.
- Read-only: the world's `model_dump()` is identical before and after.
- The golden world (`simulate_world(42)`) is only read; its hash is unchanged.

## Test plan (failing — `tests/test_heritage_explorer.py`, RED until implemented)

Over `simulate_world(42, mode="opportunity")`:

- `test_explorer_lists_every_heritage` — every `heritage_rows` name appears.
- `test_explorer_default_sort_is_score` — `- **name**` sequence equals the
  `heritage_rows` (score) order.
- `test_explorer_sort_longevity_matches_expected_sequence`,
  `test_explorer_sort_reach_matches_expected_sequence` — name sequence equals the
  re-sorted rows.
- `test_explorer_sort_modes_accepted_and_complete` — score/longevity/reach/origin
  each complete and deterministic.
- `test_explorer_group_by_type_complete_with_headers`,
  `test_explorer_group_by_founder_complete` — all heritage present; `###` headers
  for type; deterministic.
- `test_explorer_living_status_matches_theme_alignment` — the "still shaping the
  world" phrase appears iff some heritage's domain matches the dominant theme.
- `test_explorer_no_internal_ids`, `test_explorer_is_read_only`,
  `test_explorer_is_deterministic`, `test_explorer_is_markdown`.
- `test_explorer_rejects_unknown_sort`, `test_explorer_rejects_unknown_group_by`.

## Implementation plan (after approval — small commits)

1. `reporting/heritage_explorer.py` (data extraction → sort → grouping → renderer
   → id-free) → all `test_heritage_explorer.py` green.
2. (If a CLI surface is wanted) additive `--heritage` on the play CLI, like a
   future `--lineage` — proposed separately; not part of this issue's failing
   tests.

## Constraints honored

- **Read-only projection only**; World unchanged (asserted).
- `models.py` / P6 / P7 / P8 / P9-1 / P9-2 / P9-3 / P9-4 untouched;
  `heritage_explorer.py` only imports existing read-only helpers.
- No internal ids in output (humanized labels only); seed42 golden inviolable.
