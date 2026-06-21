# P11 Structured World Read-Model — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** First P11 issue. Chosen direction per the P11 candidate
comparison (A → B → C): the Structured World Read-Model — read-only, highest
asset reuse, zero determinism risk, and the first concrete step toward the
recurring "future low-poly 3D client" north star.

## 0. Why this, why now

P6→P10 delivered the world (generate → experience → play → persist → observe).
Every observation surface built in P10 (`Section`, `SocialBond`) was *deliberately
shaped as a seam a future 3D client could read without parsing prose*. P11-A
**cashes in those seams**: it unifies them into one deterministic, id-free,
**JSON-serializable** snapshot — `WorldView` — that any client (text now, low-poly
3D / web later) consumes as structured data. It is read-only, so it ships with the
same zero-risk profile that made the Observatory the right P10 starter, and it is
the legibility layer the later engine-touching phases (B Social Memory L2, C World
Dynamics) need to be worth building.

## 1. Responsibility — what the read-model *is* (and is not)

The read-model is **the data boundary**: a pure function `World → WorldView` (a
typed, id-free, serializable aggregate) plus its canonical JSON encoding.

It **is**:
- an **aggregate projection** — it composes several independent read-only sources
  (overview/theme, lineage over `world.lives`, `heritage_rows`,
  `social_memory_bonds`, and the new `places`) into one snapshot; it computes no
  new history and is **not** a canonical source;
- a single **structured** snapshot of typed records (not prose) — the contract a
  non-text client deserializes;
- id-free, deterministic, read-only, immutable.

It **is not**:
- a generator of new world state (no mutation — asserted via `model_dump_json`);
- a text/Markdown renderer — that is the Observatory's job (P10, **frozen**). The
  read-model is the *structured sibling*; the Observatory is untouched;
- a reuse of the **developer** `views.py` (id-leaky, prose) — the boundary is
  typed and humanised by construction.

**Inviolable:** `models.py`, P6 (frozen), P7 (`experience.py`), P8 (play loop),
P9-1..5, **P10 Observatory (`observatory.py`, hash `f9ad13c7…`)** and
**P10 Social Memory (`social_memory.py`, hash `3fbb1aa0…`)**, `run_human_world`,
and the seed42 golden (`e62d8f2c…` / `98bea862…`). The read-model only reads.

## 2. Concept model

```
world_model(world) -> WorldView          # typed, id-free, serializable aggregate
world_model_json(world) -> str           # canonical WorldView.model_dump_json()
        │
        ▼
   WorldView  (pydantic, extra="forbid", deterministic field order)
   ┌────────────┬──────────────────────────┬──────────────────────────────┐
   │ field      │ record                   │ source (all id-free)          │
   ├────────────┼──────────────────────────┼──────────────────────────────┤
   │ schema_version │ str  ("1")           │ read-model schema contract    │
   │ overview   │ Overview                 │ _data.place/counts/theme      │
   │ theme      │ ThemeView                │ world.theme (ThemeAxis.value) │
   │ lives      │ list[LifeView]           │ world.lives + ordinals        │
   │ heritage   │ list[HeritageView]       │ heritage_rows MINUS source_seed│
   │ bonds      │ list[BondView]           │ social_memory_bonds (reuse)   │
   │ places     │ list[PlaceView]  ← NEW   │ world.locations (3D anchor)   │
   │ factions   │ list[FactionView]        │ world.factions (id-free scalars)│
   └────────────┴──────────────────────────┴──────────────────────────────┘
```

Each record key maps to a future 3D scene (see §6). `schema_version` lets a client
detect a schema change without diffing bytes; it is bumped only when the record
shape changes. It is **deliberately independent of `ENGINE_VERSION`** (a
world-determinism stamp) — the two must never be coupled.

Every record is an **immutable** pydantic model (`ConfigDict(frozen=True,
extra="forbid")`): the read-model cannot be mutated after construction, reinforcing
that it is a projection, never a canonical/persistence source (the save is the
Recipe — P9).

## 3. Schema (pydantic records — id-free by construction)

```python
class Overview(BaseModel):
    place: str
    seed: int                       # recipe identity (an int, not an entity id)
    current_year: int
    max_year: int
    life_count: int
    ending_class: Optional[str]
    dominant_axis: Optional[str]    # ThemeAxis.value

class ThemeView(BaseModel):
    dominant: Optional[str]         # ThemeAxis.value
    axes: dict[str, int]            # ThemeAxis.value -> score, key-sorted

class LifeView(BaseModel):
    ordinal: int                    # 1-based "Life N"
    title: str                      # LifeSummary.title (humanised)
    birth_year: int
    death_year: Optional[int]
    dominant_axis: Optional[str]
    world_impact: int               # _data.life_world_impact

class HeritageView(BaseModel):      # heritage_rows, with source_seed DROPPED
    name: str                       # labels.heritage_name (proper name)
    type: str
    domain: str
    score: int
    longevity: int
    reach: int
    derived_events: int
    origin_life: str                # "Life N" | "—"
    origin_action: str              # labels.seed_label (verb phrase)

class BondView(BaseModel):          # mirrors social_memory.SocialBond
    npc_name: str
    npc_tier: str
    life_ordinal: int
    affinity: int
    sentiment: str
    reason: str

class PlaceView(BaseModel):         # NEW — the primary 3D anchor
    name: str
    location_type: str              # LocationType.value
    theme_affinity: Optional[str]   # ThemeAxis.value | None
    is_origin: bool                 # the founding village (3D spawn anchor)
    # Future extension (3D anchor): coordinates / biome / importance / landmark
    #   — additive fields under a schema_version bump; structured home means the
    #   map section grows without breaking the text surface.

class FactionView(BaseModel):       # id-free scalars only
    name: str
    kind: str                       # FactionType.value
    power: int
    # relations DEFERRED — dict keyed by faction_id needs an id->name humaniser
    # (the exact P8 id-leak trap); follow-on, same reasoning as Observatory.

class WorldView(BaseModel):
    schema_version: str
    overview: Overview
    theme: ThemeView
    lives: list[LifeView]
    heritage: list[HeritageView]
    bonds: list[BondView]
    places: list[PlaceView]
    factions: list[FactionView]
```

All records use `ConfigDict(frozen=True, extra="forbid")` — immutable and closed.
`WorldView.model_dump_json()` is the canonical, deterministic serialization — and
the 3D/web client contract.

## 4. MVP decision

**MVP = `schema_version + overview + theme + lives + heritage + bonds + places +
factions(scalars)`.**

**Included, and why:**
- `overview` / `theme` / `lives` / `heritage` / `bonds` reuse already-player-safe,
  already-deterministic projections (`_data`, `labels`, `social_memory_bonds`) —
  maximum reuse, the structured form of what the Observatory already renders as
  prose.
- **`places` (NEW)** is the headline of this phase: the Observatory deferred it as
  "the primary 3D anchor, better co-designed with the 3D scene than rushed into
  text." A *structured* read-model is exactly that right home — it is data, not
  prose, so it is shaped for the 3D map from day one. Fields are pure id-free
  scalars (`name`, `LocationType.value`, `ThemeAxis.value`).
- `factions` as id-free scalars (`name`, `FactionType.value`, `power`) — part of
  the world body a 3D client renders, zero id surface.

**Excluded from MVP, and why:**
- **`source_seed` on heritage** — present in `heritage_rows`, it is an internal
  seed id; it is **deliberately dropped** at the boundary. (Surfacing the boundary
  discipline as a *negative* contract, asserted by a test.)
- **Faction relations** — `Faction.relations` is `dict[str, Signed]` keyed by
  `faction_id`; humanising it needs an id→name helper that does not exist (the P8
  trap). Deferred, same call the Observatory made.
- **Causal graph / per-life timelines / discoveries / wildcards** — deeper detail
  records; addable later without breaking the contract (additive fields +
  `schema_version` bump). The MVP is the navigable index, not the full dump.
- **A text renderer** — the Observatory already renders text; the read-model is the
  structured sibling, not a second prose surface.

## 5. Determinism requirements (asserted by the failing tests)

- **Same World ⇒ identical bytes** for `world_model_json` (sorted dict keys,
  deterministic list ordering: lives by ordinal, heritage by `(-score, …)`, bonds
  by `(-affinity, name)`, places by `(kind, name)`, factions by `(-power, name)` —
  no set/dict iteration leak).
- **Read-only ⇒ golden preserved.** `world.model_dump_json()` is byte-identical
  before/after; the seed42 world stays `e62d8f2c…` by construction.
- **seed42 frozen-hash test** — `sha256(world_model_json(simulate_world(42,
  "opportunity")))[:16]` pinned to `GOLDEN_WORLD_MODEL_SHA` (filled at GREEN; RED
  until then) — the read-model's permanent regression guard.
- **Player display ⟂ internal ids (complete separation).** `world_model_json`
  never matches `\b(seed|life|npc|node|loc|fac|her|player)-\d`, never contains
  `player-` or `legacy:`. People by name, past selves by "Life N", heritage by
  proper name. **`source_seed` absent** (explicit negative assertion).
- **Round-trip contract.** `WorldView.model_validate_json(world_model_json(world))`
  reconstructs an equal `WorldView` — the client-deserialization guarantee.

## 6. 3D client data boundary (the whole point)

The read-model **is** the seam the Observatory design (§6) named and deferred:
- **Record key = scene model.** `lives` → a hall of past selves; `heritage` →
  monuments to walk among; `bonds` → characters reacting to a past self;
  `places` → **the actual map geometry**; `theme` → world mood (era lighting /
  palette from `dominant`); `overview` → the load/scope header.
- **JSON, not prose.** A 3D/web client deserializes `WorldView` and binds typed
  fields to scene objects — it never parses Markdown. `schema_version` guards the
  contract.
- **Determinism is the contract that makes 3D reproducible:** same recipe → same
  world → same `WorldView` → same scene graph. P9's recipe-as-save plus this
  read-model is exactly what a 3D client loads.
- **Places is introduced here, structured-first** — fulfilling the Observatory's
  explicit deferral ("co-design the map section with the 3D scene").

## 7. API (signatures)

```python
def world_model(world: World) -> WorldView
def world_model_json(world: World) -> str        # WorldView.model_dump_json()
```

No flag, no parameter, no mutation. `world_model_json` is the canonical encoding
used for the golden hash and the client contract.

## 8. Architecture / placement

- **`reporting/world_model.py` (new, additive):** imports `_data`
  (`place`/`life_index`/`life_world_impact`/`heritage_rows`/`dominant_axis`),
  `labels`, `social_memory.social_memory_bonds`, and reads `world.theme`,
  `world.locations`, `world.factions`. Sibling to `observatory.py`/
  `social_memory.py`.
- **Untouched:** `observatory.py` (P10, frozen), `social_memory.py` (P10, frozen —
  *reused, not edited*), `experience.py` (P7), `reporting/__init__.py` (tests import
  the submodule directly), `views.py` (dev), `models.py`, P6/P8/P9,
  `run_human_world`, the seed42 golden.

## 9. Test plan (failing — `tests/test_world_model.py`, RED until implemented)

Over `simulate_world(42, mode="opportunity")` unless noted:

- `test_world_model_returns_worldview` — `world_model(world)` is a `WorldView`.
- `test_world_model_json_is_valid_json` / `_is_read_only` (`model_dump_json`
  before==after) / `_is_deterministic` (json == json).
- `test_world_model_no_internal_ids` — regex guard, no `player-`, no `legacy:`.
- `test_world_model_heritage_has_no_source_seed` — `source_seed` absent from the
  JSON and from every `HeritageView` (the negative boundary contract).
- `test_world_model_overview_scope` — place name, `current_year`, life count.
- `test_world_model_lives_one_per_life_ordered` — one `LifeView` per `world.lives`,
  ordinals `1..len(lives)` in order.
- `test_world_model_heritage_matches_rows` — `{h.name}` equals the id-free
  `heritage_rows` name set (and counts match).
- `test_world_model_bonds_match_social_memory` — `bonds` equals
  `social_memory_bonds(world)` field-for-field (reuse, not re-derivation).
- `test_world_model_places_cover_locations` — one `PlaceView` per `world.locations`;
  every `Location.name` present; each `kind ∈ {t.value for t in LocationType}`;
  exactly one `is_origin` (the founding village).
- `test_world_model_factions_are_id_free_scalars` — one `FactionView` per
  `world.factions`; name/kind/power only; no relations field.
- `test_world_model_round_trips` — `WorldView.model_validate_json(
  world_model_json(world)) == world_model(world)` (client-deserialization).
- `test_world_model_on_fresh_world` — `world_model(generate_world(42))` succeeds
  (no lives → empty `lives`/`bonds`); `places` still populated.
- `test_world_model_seed42_hash_is_frozen` — `GOLDEN_WORLD_MODEL_SHA` (filled at
  GREEN; RED until then).

## 10. Implementation plan (after approval — small commits)

1. `reporting/world_model.py`: define the records → build `WorldView` from the
   reused id-free helpers (drop `source_seed`; add `places`/`factions`) →
   deterministic ordering → `world_model_json` → freeze `GOLDEN_WORLD_MODEL_SHA`.
2. (Deferred, separate issues) faction-relation humaniser + `FactionView.relations`;
   causal/timeline/discovery/wildcard records; a thin client adapter — all additive
   under a `schema_version` bump.

## 11. Constraints honored

- Read-only projection only; World unchanged (asserted) ⇒ seed42 golden intact.
- No `ENGINE_VERSION` change; no Recipe change; no engine touch.
- No internal ids in output or any record field (regex-guarded; `source_seed`
  explicitly dropped).
- P6 / P7 / P8 / P9-1..5, **P10 Observatory + Social Memory**, `run_human_world`,
  the seed42 golden untouched (Observatory/Social-Memory reused, never edited).
