"""P12 Emergent Narrative Observatory contract.

P12 is a pure read-only projection that surfaces the *emergent narrative* of a
finished world: the top causal **threads** (origin -> consequences -> culmination)
and the **turning points** (the pivotal LARGE-scale events). It computes no new
history — it reads the causal DAG + heritage + lineage that P6 already produced.

Contract pinned here (mirrors P11-A WorldView): immutable id-free view records,
deterministic, read-only (world byte-identical before/after), a pure Markdown
renderer (reads only the view), and the five frozen goldens untouched. The one new
golden ``GOLDEN_NARRATIVE_SHA`` is the seed42 ``narrative_json`` hash.
"""

from __future__ import annotations

import hashlib
import re
from itertools import groupby

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.reporting import narrative as nar
from chronicle_forge.reporting.observatory import observatory
from chronicle_forge.reporting.social_memory import social_memory_view
from chronicle_forge.reporting.world_model import world_model_json

# Frozen goldens P12 must NOT move (it adds files only).
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"

# The one new golden: seed42 narrative_json hash.
GOLDEN_NARRATIVE_SHA = "a32df9e5068d054a"

# id-free negative contract: none of these may cross the boundary.
_ID_RE = re.compile(r"[a-z]+-\d{4}")  # entity id "<prefix>-NNNN" (ids.py)
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-" r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_HEX32_RE = re.compile(r"\b[0-9a-fA-F]{32}\b")
_HEX40_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _world():
    return simulate_world(42, mode="opportunity")


# --- structure ----------------------------------------------------------


def test_narrative_model_returns_narrativeview():
    view = nar.narrative_model(_world())
    assert type(view).__name__ == "NarrativeView"
    assert view.model_config.get("frozen") is True
    assert view.model_config.get("extra") == "forbid"


def test_schema_version_is_one_and_decoupled():
    assert nar.SCHEMA_VERSION == "1"
    assert nar.narrative_model(_world()).schema_version == "1"


def test_narrativeview_top_level_fields():
    view = nar.narrative_model(_world())
    for field in (
        "schema_version",
        "place",
        "span",
        "ending_class",
        "threads",
        "turning_points",
    ):
        assert hasattr(view, field), field
    assert isinstance(view.threads, list)
    assert isinstance(view.turning_points, list)
    assert view.span == _world().current_year


def test_threadview_fields_and_types():
    view = nar.narrative_model(_world())
    assert view.threads, "seed42 is expected to produce threads"
    for t in view.threads:
        assert type(t).__name__ == "ThreadView"
        assert isinstance(t.ordinal, int) and t.ordinal >= 1
        assert isinstance(t.title, str) and t.title
        assert isinstance(t.origin, str) and t.origin
        assert isinstance(t.domain, str)
        assert isinstance(t.start_year, int)
        assert isinstance(t.end_year, int)
        assert t.start_year <= t.end_year
        assert isinstance(t.length, int) and t.length >= 1
        assert t.culmination_scale in {"large", "medium", "small"}
        assert isinstance(t.player_driven, bool)


def test_threads_ordinals_are_dense_and_capped():
    threads = nar.narrative_model(_world()).threads
    assert [t.ordinal for t in threads] == list(range(1, len(threads) + 1))
    assert len(threads) <= nar.DEFAULT_MAX_THREADS


def test_turning_points_are_year_sorted():
    tps = nar.narrative_model(_world()).turning_points
    years = [tp.year for tp in tps]
    assert years == sorted(years)
    for tp in tps:
        assert type(tp).__name__ == "TurningPointView"
        assert isinstance(tp.title, str) and tp.title
        assert isinstance(tp.player_driven, bool)
        assert isinstance(tp.converging_threads, int) and tp.converging_threads >= 0


# --- significance is read from the engine, not re-scored ----------------


def test_no_independent_narrative_score_field():
    """The view exposes engine markers (scale) and structure (length), never a
    P12-invented importance/impact/narrative score."""
    js = nar.narrative_json(_world())
    for banned in ("importance", "impact", "narrative_score", "score"):
        assert banned not in js


# --- ordering determinism -----------------------------------------------


def test_thread_order_is_stable_with_equal_scale():
    threads = nar.narrative_model(_world()).threads
    # Within each culmination_scale group the order is (-length, start_year, title).
    for _, grp in groupby(threads, key=lambda t: t.culmination_scale):
        keys = [(-t.length, t.start_year, t.title) for t in grp]
        assert keys == sorted(keys)
    # And the whole ordering is reproducible run to run.
    again = nar.narrative_model(_world()).threads
    assert [(t.title, t.length, t.start_year) for t in threads] == [
        (t.title, t.length, t.start_year) for t in again
    ]


def test_max_threads_slice_is_deterministic():
    world = _world()
    full = nar.narrative_model(world, max_threads=100).threads
    assert len(full) > nar.DEFAULT_MAX_THREADS  # more culminations than the cap
    a = nar.narrative_model(world, max_threads=7).threads
    b = nar.narrative_model(world, max_threads=7).threads
    assert [t.title for t in a] == [t.title for t in b]
    # the capped set is exactly the deterministic prefix of the full order
    assert [(t.title, t.start_year, t.length) for t in a] == [
        (t.title, t.start_year, t.length) for t in full[:7]
    ]
    assert [t.ordinal for t in a] == list(range(1, 8))


# --- id-free negative contract ------------------------------------------


def test_narrative_json_is_id_free():
    js = nar.narrative_json(_world())
    for name, rx in (
        ("entity-id", _ID_RE),
        ("uuid", _UUID_RE),
        ("hex32", _HEX32_RE),
        ("hex40", _HEX40_RE),
    ):
        m = rx.search(js)
        assert m is None, f"{name} leaked into narrative_json: {m!r}"
    assert "source_seed" not in js
    assert '_id"' not in js  # no field key ending in _id


# --- determinism & read-only --------------------------------------------


def test_narrative_json_is_deterministic_double_run():
    assert nar.narrative_json(_world()) == nar.narrative_json(_world())


def test_narrative_json_hash_is_frozen_golden():
    assert _sha(nar.narrative_json(_world())) == GOLDEN_NARRATIVE_SHA


def test_narrative_model_does_not_mutate_world():
    world = _world()
    before = world.model_dump_json()
    nar.narrative_model(world)
    nar.narrative_json(world)
    assert world.model_dump_json() == before


# --- renderer purity (Markdown reads only the view) ---------------------


def test_renderer_is_pure():
    view = nar.narrative_model(_world())
    before = view.model_dump_json()
    md = nar.narrative_markdown(view)
    assert view.model_dump_json() == before  # view unchanged by rendering
    assert md == nar.narrative_markdown(view)  # deterministic


def test_narrative_markdown_surface_is_titled():
    md = nar.narrative_markdown(nar.narrative_model(_world()))
    assert md.startswith("# ")  # an Observatory-style headed document
    assert _ID_RE.search(md) is None  # the prose is id-free too


# --- boundary guard: P12 moves no existing golden -----------------------


def test_narrative_leaves_existing_goldens():
    world = _world()
    nar.narrative_model(world)  # running P12 must not perturb anything
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
