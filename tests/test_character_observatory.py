"""P13 Character Observatory (Biography Read-Model) contract.

P13 is a pure read-only projection that surfaces, per life, the *structured
biography* a finished world already produced: the 8 evaluation lenses, the activity
profile, talent, the death, and the legacies that life founded. It computes no new
history and invents no score — every number is read straight off the ``Life`` record.

Contract pinned here (mirrors P11-A WorldView / P12 NarrativeView): immutable id-free
view records, deterministic, read-only (world byte-identical before/after), a pure
Markdown renderer (reads only the view), and the existing frozen goldens untouched.
The one new golden ``GOLDEN_CHARACTER_SHA`` is the seed42 ``character_json`` hash.

``chronicle_forge.reporting.character`` is imported **inside each test body** (a
habit kept from the RED phase) so a missing module would fail the P13 tests alone
without perturbing collection of the existing suite.
"""

from __future__ import annotations

import hashlib
import re

from chronicle_forge.autoplay import simulate_world

# Frozen goldens P13 must NOT move (it adds files only). Main b5e310f set.
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"

# The one new golden: seed42 character_json hash (= sha256(character_json)[:16]).
GOLDEN_CHARACTER_SHA = "36c894fbde084e57"

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


def test_character_model_returns_observatory_view():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    assert type(view).__name__ == "CharacterObservatoryView"
    assert view.model_config.get("frozen") is True
    assert view.model_config.get("extra") == "forbid"


def test_schema_version_is_one_and_decoupled():
    from chronicle_forge.reporting import character as ch

    assert ch.SCHEMA_VERSION == "1"
    assert ch.character_model(_world()).schema_version == "1"


def test_observatory_top_level_fields():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    for field in ("schema_version", "place", "span", "life_count", "characters"):
        assert hasattr(view, field), field
    assert isinstance(view.characters, list)
    world = _world()
    assert view.span == world.current_year
    assert view.life_count == len(world.lives)
    assert len(view.characters) == len(world.lives)


def test_biographyview_fields_and_types():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    assert view.characters, "seed42 is expected to produce lives"
    for bio in view.characters:
        assert type(bio).__name__ == "BiographyView"
        assert isinstance(bio.ordinal, int) and bio.ordinal >= 1
        assert isinstance(bio.title, str)
        assert isinstance(bio.is_current, bool)
        assert isinstance(bio.birth_year, int)
        assert bio.death_year is None or isinstance(bio.death_year, int)
        assert bio.age_at_death is None or isinstance(bio.age_at_death, int)
        assert bio.death_cause is None or isinstance(bio.death_cause, str)
        assert bio.talent is None or isinstance(bio.talent, str)
        assert bio.dominant_axis is None or isinstance(bio.dominant_axis, str)
        assert isinstance(bio.seeds_planted, int) and bio.seeds_planted >= 0
        assert isinstance(bio.world_impact, int) and bio.world_impact >= 0
        assert isinstance(bio.legacies, list)
        assert all(isinstance(name, str) for name in bio.legacies)


def test_evaluation_is_eight_int_lenses():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    for bio in view.characters:
        lenses = bio.evaluation
        assert type(lenses).__name__ == "LensScores"
        for axis in (
            "military",
            "politics",
            "economy",
            "academia",
            "culture",
            "faith",
            "mentoring",
            "heritage",
        ):
            assert isinstance(getattr(lenses, axis), int), axis


def test_activity_profile_is_key_sorted_counts():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    for bio in view.characters:
        assert isinstance(bio.activity, dict)
        keys = list(bio.activity.keys())
        assert keys == sorted(keys)  # key-sorted -> deterministic
        assert all(
            isinstance(k, str) and isinstance(v, int) for k, v in bio.activity.items()
        )


def test_characters_ordinals_are_dense_and_lineage_ordered():
    from chronicle_forge.reporting import character as ch

    chars = ch.character_model(_world()).characters
    assert [c.ordinal for c in chars] == list(range(1, len(chars) + 1))


def test_at_most_one_current_life():
    from chronicle_forge.reporting import character as ch

    chars = ch.character_model(_world()).characters
    assert sum(1 for c in chars if c.is_current) <= 1


# --- significance is read from the engine, not re-scored ----------------


def test_no_independent_biography_score_field():
    """The view exposes engine metrics (evaluation lenses, world_impact) and
    structure, never a P13-invented importance/biography score."""
    from chronicle_forge.reporting import character as ch

    js = ch.character_json(_world())
    for banned in ("importance", "biography_score", "narrative_score", "score"):
        assert banned not in js


# --- id-free negative contract ------------------------------------------


def test_character_json_is_id_free():
    from chronicle_forge.reporting import character as ch

    js = ch.character_json(_world())
    for name, rx in (
        ("entity-id", _ID_RE),
        ("uuid", _UUID_RE),
        ("hex32", _HEX32_RE),
        ("hex40", _HEX40_RE),
    ):
        m = rx.search(js)
        assert m is None, f"{name} leaked into character_json: {m!r}"
    assert "source_seed" not in js
    assert '_id"' not in js  # no field key ending in _id
    # the raw-id-bearing LifeSummary lists must never surface verbatim
    for banned in ("seeds_created", "heritage_created", "notable_events"):
        assert banned not in js


# --- determinism & read-only --------------------------------------------


def test_character_json_is_deterministic_double_run():
    from chronicle_forge.reporting import character as ch

    assert ch.character_json(_world()) == ch.character_json(_world())


def test_character_json_hash_is_frozen_golden():
    from chronicle_forge.reporting import character as ch

    assert _sha(ch.character_json(_world())) == GOLDEN_CHARACTER_SHA


def test_character_model_does_not_mutate_world():
    from chronicle_forge.reporting import character as ch

    world = _world()
    before = world.model_dump_json()
    ch.character_model(world)
    ch.character_json(world)
    assert world.model_dump_json() == before


# --- renderer purity (Markdown reads only the view) ---------------------


def test_renderer_is_pure():
    from chronicle_forge.reporting import character as ch

    view = ch.character_model(_world())
    before = view.model_dump_json()
    md = ch.character_markdown(view)
    assert view.model_dump_json() == before  # view unchanged by rendering
    assert md == ch.character_markdown(view)  # deterministic


def test_character_markdown_surface_is_titled():
    from chronicle_forge.reporting import character as ch

    md = ch.character_markdown(ch.character_model(_world()))
    assert md.startswith("# ")  # an Observatory-style headed document
    assert _ID_RE.search(md) is None  # the prose is id-free too


# --- boundary guard: P13 moves no existing golden -----------------------


def test_character_leaves_existing_goldens():
    from chronicle_forge.reporting import character as ch
    from chronicle_forge.reporting.observatory import observatory
    from chronicle_forge.reporting.social_memory import social_memory_view
    from chronicle_forge.reporting.world_model import world_model_json

    world = _world()
    ch.character_model(world)  # running P13 must not perturb anything
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
