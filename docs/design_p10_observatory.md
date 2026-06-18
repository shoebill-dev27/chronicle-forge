# P10 Observatory — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** First P10 issue. Chosen direction per the P10 candidate
research (`docs/research/p10_candidates.md`): Observatory first — read-only,
highest asset reuse, zero determinism risk.

## 1. Responsibility — what the Observatory *is* (and is not)

The Observatory is a **read-only aggregation layer**: it composes the world
information that *already exists* into one navigable, player-facing surface. It is
the lens for "explore the world I made", and it is the data/index layer a future
client (text now, low-poly 3D later) reads.

It **is**:
- a *consumer* of finished-world projections — it computes no new history;
- a single ordered surface that gathers the per-aspect views (lineage, heritage,
  theme, overview) under one document;
- deterministic, read-only, and id-free.

It **is not**:
- a generator of new world state (no mutation — asserted via `model_dump_json`);
- a re-implementation of existing views — it *delegates* to the player-safe ones
  (`lineage_view` P9-4, `heritage_explorer` P9-5) and renders only thin, id-free
  glue for data that has no player view yet (overview, theme);
- a reuse of the **developer** `views.py` (P5) — that surface is dev-facing,
  `=== … ===`-styled and **leaks internal ids**, so the Observatory must not embed
  it.

**Inviolable:** `models.py`, P6 (salience/opportunity, frozen), P7
(`experience.py`), P8 (play loop), P9-1..5, `run_human_world`, and the seed42
golden (`e62d8f2c…` / `98bea862…`). The Observatory only reads a finished world.

## 2. Concept model

```
observatory(world, *, sections=None) -> str   # player-facing Markdown
        │
        ▼
   Section registry  (ordered, named, id-free, deterministic)
   ┌──────────┬──────────────────────┬────────────────────────────────┐
   │ key      │ title (## header)    │ body source                     │
   ├──────────┼──────────────────────┼────────────────────────────────┤
   │ overview │ Overview             │ thin id-free header (own render)│
   │ lineage  │ Lineage              │ lineage_view(world)  (P9-4)     │
   │ heritage │ Heritage             │ heritage_explorer(world) (P9-5) │
   │ theme    │ Theme                │ world.theme.history (own render)│
   │ timeline │ Timeline             │ timeline_md(world)   [deferred] │
   │ factions │ Factions             │ id-free faction list [deferred] │
   │ places   │ Places               │ id-free location list[deferred] │
   └──────────┴──────────────────────┴────────────────────────────────┘
```

A `Section` is `(key, title, render(world) -> str)`. The Observatory emits a
single `# ` document title, then each selected section as `## {title}` followed by
its body. Embedded sub-view bodies keep their own deeper headings (e.g.
`lineage_view` emits `## Life N`); section detection therefore uses **containment
of the known section titles**, never exact-equality of all `##` lines.

`sections=None` ⇒ the full MVP set. An explicit list selects **which** sections
appear; the output is **always in the canonical MVP order** (`overview` →
`lineage` → `heritage` → `theme`) regardless of the input order, so the surface is
stable for any caller. Unknown key ⇒ `ValueError`; empty list ⇒ `ValueError`.

## 3. Candidate sections — comparison

| Section | Body source | Player value | id-leak surface | MVP? |
|---|---|---|---|---|
| **Overview** | own (place, years, lives, dominant theme, ending) | Navigation anchor / scope | none (scalars + names) | **Yes** |
| **Lineage** | `lineage_view` (P9-4) | High — who I was, what I left | none (already id-free) | **Yes** |
| **Heritage** | `heritage_explorer` (P9-5) | High — what endured | none (already id-free) | **Yes** |
| **Theme** | own, from `theme.history` | The world's arc/mood | none (`ThemeAxis.value` only) | **Yes** |
| Timeline | `timeline_md` | Year-by-year density | none, but overlaps Theme | No — defer |
| Factions | own | Power context | **`Faction.relations` keyed by `faction_id`** | No — defer |
| Places/Landmarks | own | Map / world body | `Location` refs; low MVP payoff | No — defer |

## 4. MVP decision

**MVP = `overview` → `lineage` → `heritage` → `theme`** (fixed order).

**Included, and why:**
- These four are the player's "what I made and how it felt" core.
- Two of them (`lineage`, `heritage`) **reuse fully-built, player-safe P9 views**
  verbatim — maximum reuse, zero new id-leak surface.
- `theme` and `overview` are thin renders over id-free scalar data
  (`ThemeAxis.value`, counts, names) — no id resolution needed.
- **Every MVP section has zero internal-id surface**, so the whole MVP honours the
  P8 lesson by construction.

**Excluded from MVP, and why:**
- **Timeline** — `timeline_md` is sound but its year-by-year view overlaps the
  Theme arc and reads denser/more dev-ish; deferring keeps the MVP a clean
  highlight reel. Re-addable as a section with no schema change.
- **Factions** — `Faction.relations` is a `dict[str, Signed]` keyed by
  `faction_id`; surfacing relations safely needs an id→name humanisation helper
  that does not exist yet. Deferring avoids an id-leak risk class (the exact P8
  trap). Faction *names/power* alone could come later as a focused pass.
- **Places/Landmarks** — lowest MVP player-experience payoff, and it is the most
  natural *3D* hook (see §6); better designed together with the 3D map layer than
  rushed into the text MVP.

Per-life P7 detail views (`dead_summary` / `life_chronicle` / `life_timeline` /
`legacy_view`) are intentionally **not** re-wrapped: the Observatory presents the
*chain* (via Lineage); drilling into a single life is a future "detail view".

## 5. Determinism requirements

- **Same World ⇒ identical bytes.** Fixed section order; section bodies delegate to
  already-deterministic views; no set/dict iteration leaks into output.
- **seed42 frozen-hash test.** `sha256(observatory(simulate_world(42,
  "opportunity")))[:16]` is pinned to a golden constant
  (`GOLDEN_OBSERVATORY_SHA`), filled at GREEN and frozen thereafter — the
  Observatory's permanent regression guard, mirroring P9.
- **Read-only.** `world.model_dump_json()` is byte-identical before and after.
- **No internal ids.** Output never matches `\b(seed|life|npc|node|loc|fac|her)-\d`
  and never contains `legacy:` (regex-guarded). "Life N" ordinals are allowed.
- **Closed input taxonomy.** Unknown section key ⇒ `ValueError`; empty selection
  ⇒ `ValueError`.

## 6. Connection points to a future low-poly 3D layer

The Observatory is deliberately shaped as the **deterministic, id-free, named,
ordered index** a 3D client can consume — text is just the first renderer:
- **Section model = scene model.** Each section key maps to a future 3D scene:
  `lineage` → a hall/timeline of past selves; `heritage` → monuments/landmarks
  the player can walk among; `theme` → world mood (era lighting / palette from the
  dominant axis); `places` → the actual map geometry.
- **Seam to expose later (deferred, not in MVP):** a structured accessor
  `observatory_sections(world) -> list[Section]` (or a `to_dict()` per section) so
  the 3D layer subscribes to **section keys + id-free fields**, not parsed prose.
  Keeping the registry stable now means the 3D client needs no re-derivation.
- **Places/Landmarks is the primary 3D anchor** — it is named here and deferred so
  the map section is co-designed with the 3D scene rather than locked into a text
  shape prematurely.
- **Determinism is the contract that makes 3D reproducible:** same recipe → same
  world → same Observatory index → same scene graph. The P9 recipe-as-save plus
  this index is exactly what a 3D client would load.

## 7. API (signature)

```python
def observatory(world: World, *, sections: Optional[list[str]] = None) -> str
```

- `sections=None` ⇒ `("overview", "lineage", "heritage", "theme")`.
- explicit list ⇒ those sections only, **always in the canonical order above**
  (input order ignored); unknown/empty ⇒ `ValueError`.

## 8. Architecture / placement

- **`reporting/observatory.py` (new, additive):** imports `lineage_view`,
  `heritage_explorer`, the read-only `_data`/`labels` helpers, and `theme`
  (`ThemeAxis` values). Sibling to `lineage.py`/`heritage_explorer.py`.
- **Untouched:** `reporting/experience.py` (P7), `reporting/__init__.py`
  (tests import the submodule directly), `views.py` (dev), `models.py`, P6/P8,
  `run_human_world`, and the seed42 golden.

## 9. Test plan (failing — `tests/test_observatory.py`, RED until implemented)

Over `simulate_world(42, mode="opportunity")`:

- `test_observatory_is_markdown`, `test_observatory_is_read_only`,
  `test_observatory_is_deterministic`, `test_observatory_no_internal_ids`.
- `test_observatory_default_includes_mvp_sections` — `{Overview, Lineage,
  Heritage, Theme}` appear as `##` titles.
- `test_observatory_sections_in_fixed_order` — those titles appear in MVP order.
- `test_observatory_surfaces_every_heritage` — every `heritage_rows` name present.
- `test_observatory_surfaces_every_life` — each `Life N` (1..len(lives)) present.
- `test_observatory_theme_shows_dominant` — dominant `ThemeAxis.value` present.
- `test_observatory_overview_shows_scope` — `current_year` and life count present.
- `test_observatory_section_selection_subsets` — a single-section selection
  contains only that `##` title.
- `test_observatory_section_selection_is_always_canonical_order` — a reordered
  selection (`["theme", "overview"]`) still emits canonical order
  (`Overview` before `Theme`); input order is ignored.
- `test_observatory_rejects_unknown_section`,
  `test_observatory_rejects_empty_sections` — `ValueError`.
- `test_observatory_seed42_hash_is_frozen` — pinned golden hash (constant filled
  at GREEN; RED until then).

## 10. Implementation plan (after approval — small commits)

1. `reporting/observatory.py`: section registry → selection/ordering → overview &
   theme renders → delegate lineage/heritage → id scrub → frozen seed42 hash.
2. (Deferred, separate issues) Timeline / Factions (with id-free relations) /
   Places sections; the `observatory_sections` structured accessor for the 3D
   layer.

## 11. Constraints honored

- Read-only projection only; World unchanged (asserted).
- P6 / P7 / P8 / P9-1..5, `run_human_world`, the seed42 golden untouched.
- No internal ids in output (humanised/id-free by construction); `views.py` (dev,
  id-leaky) deliberately not reused.
