"""P14 Timeline Observatory (chronological Read-Model) contract — RED.

P14 is a pure read-only projection that surfaces the finished world's causal
history as a **chronological record**: every ``CausalNode`` (event) the engine
already produced, ordered by year. Where P12 NarrativeView selects the top causal
*threads* by significance, P14 answers the orthogonal question — *when did things
happen* — by laying the full event record out on a single time axis. It computes
no new history, invents no score, and infers no era: every entry is read straight
off an existing ``CausalNode`` / ``CausalGraph`` / ``World``.

Contract pinned here (mirrors P11-A WorldView / P12 NarrativeView / P13
CharacterObservatoryView): immutable id-free view records, deterministic (a total
year order, no dict/set iteration leaks), read-only (world byte-identical before/
after), and a pure Markdown renderer (reads only the view). The one new golden
``GOLDEN_TIMELINE_SHA`` is the seed42 ``timeline_json`` hash, pinned at GREEN.

``chronicle_forge.reporting.timeline`` is imported **inside each test body** so a
missing module fails the P14 tests alone (clean ``ModuleNotFoundError`` RED)
without perturbing collection of the existing suite.
"""

from __future__ import annotations

import hashlib
import re

from chronicle_forge.autoplay import simulate_world

# Frozen goldens P14 must NOT move (it adds files only). Main 9ad743e set.
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"
GOLDEN_NARRATIVE_SHA = "a32df9e5068d054a"
GOLDEN_CHARACTER_SHA = "36c894fbde084e57"

# The one new golden: seed42 timeline_json hash (= sha256(timeline_json)[:16]).
# Pinned at GREEN; the placeholder keeps the golden test RED via the in-body import.
GOLDEN_TIMELINE_SHA = "ae42ed5ff91f5545"  # seed42 timeline_json hash (GREEN)

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


def test_timeline_model_returns_timeline_view():
    import chronicle_forge.reporting.timeline as tl

    view = tl.timeline_model(_world())
    assert type(view).__name__ == "TimelineView"
    assert view.model_config.get("frozen") is True
    assert view.model_config.get("extra") == "forbid"


def test_schema_version_is_one_and_decoupled():
    import chronicle_forge.reporting.timeline as tl

    assert tl.SCHEMA_VERSION == "1"
    assert tl.timeline_model(_world()).schema_version == "1"


def test_timeline_top_level_fields():
    import chronicle_forge.reporting.timeline as tl

    view = tl.timeline_model(_world())
    for field in (
        "schema_version",
        "place",
        "span",
        "start_year",
        "end_year",
        "event_count",
        "entries",
    ):
        assert hasattr(view, field), field
    assert isinstance(view.entries, list)
    world = _world()
    assert view.span == world.current_year
    assert view.event_count == len(view.entries)


def test_entry_fields_and_types():
    import chronicle_forge.reporting.timeline as tl

    view = tl.timeline_model(_world())
    assert view.entries, "seed42 is expected to produce events"
    for entry in view.entries:
        assert type(entry).__name__ == "TimelineEntryView"
        assert isinstance(entry.ordinal, int) and entry.ordinal >= 1
        assert isinstance(entry.year, int)
        assert isinstance(entry.title, str) and entry.title
        assert isinstance(entry.domain, str)
        assert isinstance(entry.scale, str)
        assert entry.location is None or isinstance(entry.location, str)
        assert isinstance(entry.player_driven, bool)


# --- deterministic chronological ordering -------------------------------


def test_entries_are_year_ordered():
    import chronicle_forge.reporting.timeline as tl

    entries = tl.timeline_model(_world()).entries
    years = [e.year for e in entries]
    assert years == sorted(years)  # total order, earliest first


def test_entries_ordinals_are_dense():
    import chronicle_forge.reporting.timeline as tl

    entries = tl.timeline_model(_world()).entries
    assert [e.ordinal for e in entries] == list(range(1, len(entries) + 1))


def test_start_end_year_bound_the_entries():
    import chronicle_forge.reporting.timeline as tl

    view = tl.timeline_model(_world())
    if view.entries:
        assert view.start_year == view.entries[0].year
        assert view.end_year == view.entries[-1].year
    else:
        assert view.start_year is None and view.end_year is None


# --- significance is read, never re-scored ------------------------------


def test_no_independent_timeline_score_field():
    """The view exposes engine facts (year, domain, scale) and structure, never a
    P14-invented importance/era/timeline score."""
    import chronicle_forge.reporting.timeline as tl

    js = tl.timeline_json(_world())
    for banned in ("importance", "timeline_score", "era_score", "score", "rank"):
        assert banned not in js


# --- id-free negative contract ------------------------------------------


def test_timeline_json_is_id_free():
    import chronicle_forge.reporting.timeline as tl

    js = tl.timeline_json(_world())
    for name, rx in (
        ("entity-id", _ID_RE),
        ("uuid", _UUID_RE),
        ("hex32", _HEX32_RE),
        ("hex40", _HEX40_RE),
    ):
        m = rx.search(js)
        assert m is None, f"{name} leaked into timeline_json: {m!r}"
    assert "source_seed" not in js
    assert '_id"' not in js  # no field key ending in _id (location_id/node_id/actors)
    # the raw-id-bearing CausalNode internals must never surface verbatim
    for banned in ("location_id", "actors", "caused_by", "node_id"):
        assert banned not in js


# --- determinism & read-only --------------------------------------------


def test_timeline_json_is_deterministic_double_run():
    import chronicle_forge.reporting.timeline as tl

    assert tl.timeline_json(_world()) == tl.timeline_json(_world())


def test_timeline_json_hash_is_frozen_golden():
    import chronicle_forge.reporting.timeline as tl

    assert _sha(tl.timeline_json(_world())) == GOLDEN_TIMELINE_SHA


def test_timeline_model_does_not_mutate_world():
    import chronicle_forge.reporting.timeline as tl

    world = _world()
    before = world.model_dump_json()
    tl.timeline_model(world)
    tl.timeline_json(world)
    assert world.model_dump_json() == before


# --- renderer purity (Markdown reads only the view) ---------------------


def test_renderer_is_pure():
    import chronicle_forge.reporting.timeline as tl

    view = tl.timeline_model(_world())
    before = view.model_dump_json()
    md = tl.timeline_markdown(view)
    assert view.model_dump_json() == before  # view unchanged by rendering
    assert md == tl.timeline_markdown(view)  # deterministic


def test_timeline_markdown_surface_is_titled():
    import chronicle_forge.reporting.timeline as tl

    md = tl.timeline_markdown(tl.timeline_model(_world()))
    assert md.startswith("# ")  # an Observatory-style headed document
    assert _ID_RE.search(md) is None  # the prose is id-free too


# --- boundary guard: P14 moves no existing golden -----------------------


def test_timeline_leaves_existing_goldens():
    import chronicle_forge.reporting.timeline as tl
    from chronicle_forge.reporting.character import character_json
    from chronicle_forge.reporting.narrative import narrative_json
    from chronicle_forge.reporting.observatory import observatory
    from chronicle_forge.reporting.social_memory import social_memory_view
    from chronicle_forge.reporting.world_model import world_model_json

    world = _world()
    tl.timeline_model(world)  # running P14 must not perturb anything
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
    assert _sha(narrative_json(world)) == GOLDEN_NARRATIVE_SHA
    assert _sha(character_json(world)) == GOLDEN_CHARACTER_SHA
