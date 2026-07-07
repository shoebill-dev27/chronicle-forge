"""P17 Legacy Legibility (Fingerprint Read-Model) contract — RED.

P17 is a pure read-only projection that makes a finished world's **Fingerprint**
legible: the player's enduring marks, attributed to the *specific life* that made
each, arranged so the player recognizes them ("ah — that was me, long ago"). It
computes no new history and invents no score: every field is read straight off an
existing ``Heritage`` row / ``CausalSeed`` / ``World.memories`` / ``World.theme``.
See docs/design_p17_legacy_legibility.md and docs/fingerprint_design.md.

Contract pinned here mirrors the P12–P14 lens harness: immutable id-free view
records (``frozen``/``extra=forbid``), deterministic, read-only (world byte-identical
before/after), a pure Markdown renderer, and a **new** golden — the view ships its
own hash and moves **no** existing golden (P17 adds files only; ``ChronicleView`` is
untouched, so the P15 chronicle golden stays put).

``chronicle_forge.reporting.legacy`` and the new ``chronicle_forge.app`` seam are
imported **inside each test body** so a missing module/name fails the P17 tests alone
(clean ``ModuleNotFoundError`` / ``ImportError`` RED) without perturbing collection of
the existing suite. ``test_existing_goldens_intact_baseline`` imports nothing new and
therefore PASSES even at RED, acting as an engine tripwire.
"""

from __future__ import annotations

import hashlib
import re

from chronicle_forge.autoplay import simulate_world

# Frozen goldens P17 must NOT move (it adds files only).
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"
GOLDEN_NARRATIVE_SHA = "a32df9e5068d054a"
GOLDEN_CHARACTER_SHA = "36c894fbde084e57"
GOLDEN_TIMELINE_SHA = "ae42ed5ff91f5545"

# The one new golden: seed42 legacy_json hash (= sha256(legacy_json)[:16]).
GOLDEN_LEGACY_SHA = "d9ea1238c253c9f7"

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


def test_legacy_model_returns_legacy_view():
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    assert type(view).__name__ == "LegacyView"
    assert view.model_config.get("frozen") is True
    assert view.model_config.get("extra") == "forbid"


def test_schema_version_is_one_and_decoupled():
    import chronicle_forge.reporting.legacy as lg

    assert lg.SCHEMA_VERSION == "1"
    assert lg.legacy_model(_world()).schema_version == "1"


def test_legacy_top_level_fields():
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    for field in (
        "schema_version",
        "place",
        "span",
        "shape",
        "marks",
        "reputation",
        "recognitions",
    ):
        assert hasattr(view, field), field
    assert isinstance(view.shape, list)
    assert isinstance(view.marks, list)
    assert isinstance(view.reputation, list)
    assert isinstance(view.recognitions, list)
    assert view.span == _world().current_year


def test_axis_weight_fields_and_types():
    import chronicle_forge.reporting.legacy as lg

    for aw in lg.legacy_model(_world()).shape:
        assert type(aw).__name__ == "AxisWeight"
        assert isinstance(aw.axis, str) and aw.axis
        assert isinstance(aw.weight, int) and aw.weight >= 0
        assert isinstance(aw.living, bool)


def test_legacy_mark_fields_and_types():
    import chronicle_forge.reporting.legacy as lg

    marks = lg.legacy_model(_world()).marks
    assert marks, "seed42 is expected to leave enduring marks"
    for m in marks:
        assert type(m).__name__ == "LegacyMark"
        assert isinstance(m.name, str) and m.name
        assert isinstance(m.kind, str) and m.kind
        assert isinstance(m.founder_life, int) and m.founder_life >= 1
        assert isinstance(m.reach, int) and m.reach >= 0
        assert isinstance(m.derived_events, int) and m.derived_events >= 0
        assert isinstance(m.longevity, int) and m.longevity >= 0
        assert isinstance(m.living, bool)


def test_reputation_note_fields():
    import chronicle_forge.reporting.legacy as lg

    for note in lg.legacy_model(_world()).reputation:
        assert type(note).__name__ == "ReputationNote"
        assert isinstance(note.sentiment, str) and note.sentiment
        assert isinstance(note.count, int) and note.count >= 1


def test_recognition_cue_fields():
    import chronicle_forge.reporting.legacy as lg

    for cue in lg.legacy_model(_world()).recognitions:
        assert type(cue).__name__ == "RecognitionCue"
        assert isinstance(cue.mark_name, str) and cue.mark_name
        assert isinstance(cue.founder_life, int) and cue.founder_life >= 1
        assert isinstance(cue.living, bool)
        assert isinstance(cue.hint, str) and cue.hint


# --- recognition rule: a rare, pure-function subset ---------------------


def test_recognitions_are_a_subset_of_marks():
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    mark_names = {m.name for m in view.marks}
    for cue in view.recognitions:
        assert cue.mark_name in mark_names
    # rarity: Recognition Moments are a strict, thresholded subset, not every mark.
    assert len(view.recognitions) <= len(view.marks)


def test_recognition_rule_is_the_documented_predicate():
    """Each cue satisfies §4: living OR consequential OR far-reaching. The rule is a
    pure function of the finished world (no invented signal)."""
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    by_name = {m.name: m for m in view.marks}
    for cue in view.recognitions:
        m = by_name[cue.mark_name]
        assert (
            m.living
            or m.derived_events >= lg.RECOGNITION_MIN_EVENTS
            or m.reach >= lg.RECOGNITION_MIN_REACH
        )


def test_founder_life_is_a_resolved_ordinal():
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    for m in view.marks:
        assert m.founder_life >= 1  # "Life N" resolved to its ordinal, id-free


# --- significance is read, never re-scored ------------------------------


def test_no_invented_legacy_score():
    import chronicle_forge.reporting.legacy as lg

    js = lg.legacy_json(_world())
    for banned in ("importance", "legacy_score", "score", "rank", "rating"):
        assert banned not in js


# --- id-free negative contract ------------------------------------------


def test_legacy_json_is_id_free():
    import chronicle_forge.reporting.legacy as lg

    js = lg.legacy_json(_world())
    for name, rx in (
        ("entity-id", _ID_RE),
        ("uuid", _UUID_RE),
        ("hex32", _HEX32_RE),
        ("hex40", _HEX40_RE),
    ):
        m = rx.search(js)
        assert m is None, f"{name} leaked into legacy_json: {m!r}"
    assert "source_seed" not in js
    assert '_id"' not in js
    for banned in ("location_id", "planted_by_life_id", "seed_id", "node_id"):
        assert banned not in js


# --- determinism & read-only --------------------------------------------


def test_legacy_json_is_deterministic_double_run():
    import chronicle_forge.reporting.legacy as lg

    assert lg.legacy_json(_world()) == lg.legacy_json(_world())


def test_legacy_json_hash_is_frozen_golden():
    import chronicle_forge.reporting.legacy as lg

    assert _sha(lg.legacy_json(_world())) == GOLDEN_LEGACY_SHA


def test_legacy_model_does_not_mutate_world():
    import chronicle_forge.reporting.legacy as lg

    world = _world()
    before = world.model_dump_json()
    lg.legacy_model(world)
    lg.legacy_json(world)
    assert world.model_dump_json() == before


# --- renderer purity (Markdown reads only the view) ---------------------


def test_renderer_is_pure():
    import chronicle_forge.reporting.legacy as lg

    view = lg.legacy_model(_world())
    before = view.model_dump_json()
    md = lg.legacy_markdown(view)
    assert view.model_dump_json() == before  # view unchanged by rendering
    assert md == lg.legacy_markdown(view)  # deterministic


def test_legacy_markdown_surface_is_titled_and_id_free():
    import chronicle_forge.reporting.legacy as lg

    md = lg.legacy_markdown(lg.legacy_model(_world()))
    assert md.startswith("# ")
    assert _ID_RE.search(md) is None


def test_markdown_does_not_declare_authorship():
    """'气付かせる, not 答えを与える': the prose surfaces breadcrumbs (founder ordinal,
    living mark), never the flat sentence that hands the player the answer."""
    import chronicle_forge.reporting.legacy as lg

    md = lg.legacy_markdown(lg.legacy_model(_world())).lower()
    for banned in ("you did this", "this was you", "your past self was"):
        assert banned not in md


# --- application-layer seam (separate from ChronicleView) ---------------


def test_app_exposes_legacy_seam():
    from chronicle_forge.app.services import legacy, legacy_file, legacy_json

    assert callable(legacy)
    assert callable(legacy_file)
    assert callable(legacy_json)


# --- boundary guard: P17 moves no existing golden -----------------------


def test_existing_goldens_intact_baseline():
    """Engine tripwire — imports nothing new, so it PASSES even at RED. Proves the
    frozen hashes are intact in the repo P17 is being designed against."""
    from chronicle_forge.reporting.character import character_json
    from chronicle_forge.reporting.narrative import narrative_json
    from chronicle_forge.reporting.observatory import observatory
    from chronicle_forge.reporting.social_memory import social_memory_view
    from chronicle_forge.reporting.timeline import timeline_json
    from chronicle_forge.reporting.world_model import world_model_json

    world = _world()
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
    assert _sha(narrative_json(world)) == GOLDEN_NARRATIVE_SHA
    assert _sha(character_json(world)) == GOLDEN_CHARACTER_SHA
    assert _sha(timeline_json(world)) == GOLDEN_TIMELINE_SHA


def test_legacy_moves_no_existing_golden():
    """At GREEN this proves running P17 perturbs nothing; at RED it fails cleanly on
    the in-body import like the rest of the P17 contract."""
    import chronicle_forge.reporting.legacy as lg
    from chronicle_forge.reporting.character import character_json
    from chronicle_forge.reporting.narrative import narrative_json
    from chronicle_forge.reporting.observatory import observatory
    from chronicle_forge.reporting.social_memory import social_memory_view
    from chronicle_forge.reporting.timeline import timeline_json
    from chronicle_forge.reporting.world_model import world_model_json

    world = _world()
    lg.legacy_model(world)  # running P17 must not perturb anything
    lg.legacy_json(world)
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
    assert _sha(narrative_json(world)) == GOLDEN_NARRATIVE_SHA
    assert _sha(character_json(world)) == GOLDEN_CHARACTER_SHA
    assert _sha(timeline_json(world)) == GOLDEN_TIMELINE_SHA
