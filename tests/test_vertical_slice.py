"""P15 Vertical Slice acceptance contract — RED.

The slice is the product's one-way path — **play → save → explore → share** — owned
by a thin Application Layer (``chronicle_forge.app``) composed entirely from existing
parts: P8 play, P9 persistence, and the P10–P14 reporting lenses. It adds **no truth**:
``explore`` replays a saved recipe to the very world the lens goldens are pinned to
(``simulate_world(42,"opportunity")`` ⇔ ``play --seed 42 --auto``; see
``tests/test_replay.py``), so its composed sub-views hash **equal** the frozen lens
goldens. ``share`` re-emits the byte-deterministic transcript.

Contract pinned here (mirrors the P12/P13/P14 read-models): a thin Application Service
seam (not a CLI), immutable id-free view records, deterministic (a recipe reproduces a
world byte-for-byte), read-only (the recipe is unchanged; each call replays a fresh
world), and a pure Markdown renderer. The one new golden ``GOLDEN_CHRONICLE_SHA`` is
the seed42 ``chronicle_json`` hash, pinned at GREEN.

``chronicle_forge.app`` is imported **inside each test body** so a missing package
fails the P15 tests alone (clean ``ModuleNotFoundError`` RED) without perturbing
collection of the existing suite.
"""

from __future__ import annotations

import hashlib
import re

from chronicle_forge import config
from chronicle_forge.persistence import build_recipe, read_recipe, save_recipe

MAX_YEAR = config.DEV_WORLD_MAX_YEARS

# Frozen engine goldens P15 must NOT move (it adds an Application Layer only).
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"
GOLDEN_NARRATIVE_SHA = "a32df9e5068d054a"
GOLDEN_CHARACTER_SHA = "36c894fbde084e57"
GOLDEN_TIMELINE_SHA = "ae42ed5ff91f5545"
GOLDEN_TRANSCRIPT_SHA = "98bea8622c686d8e"  # `play --seed 42 --auto` stdout

# The one new golden: seed42 chronicle_json hash. Pinned at GREEN; the placeholder
# keeps the golden test RED for the right reason (the in-body import fails first).
GOLDEN_CHRONICLE_SHA = "aa4c67a416178e92"  # seed42 chronicle_json hash (GREEN)

# id-free negative contract (shared with P12/P13/P14): none may cross the boundary.
_ID_RE = re.compile(r"[a-z]+-\d{4}")
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-" r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_HEX32_RE = re.compile(r"\b[0-9a-fA-F]{32}\b")
_HEX40_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _seed42_recipe():
    """The canonical seed42 auto recipe — built via existing persistence, no app.
    Identical to ``tests/test_replay.py``'s PERMANENT seed42 EOF recipe."""
    return build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])


# --- surface ------------------------------------------------------------


def test_app_exposes_vertical_slice_surface():
    import chronicle_forge.app as app

    for name in (
        "SCHEMA_VERSION",
        "PlayRequest",
        "PlayOutcome",
        "ChronicleView",
        "ShareRequest",
        "ShareResult",
        "play",
        "explore",
        "explore_file",
        "chronicle_json",
        "chronicle_markdown",
        "share",
    ):
        assert hasattr(app, name), name
    assert app.SCHEMA_VERSION == "1"


# --- play (reuse P8) ----------------------------------------------------


def test_play_grows_seed42_to_an_ending():
    import chronicle_forge.app as app

    outcome = app.play(app.PlayRequest(seed=42, auto=True))
    assert type(outcome).__name__ == "PlayOutcome"
    assert isinstance(outcome.ending_class, str) and outcome.ending_class
    assert outcome.life_count >= 1
    assert outcome.span > 0
    assert outcome.recipe.seed == 42
    assert outcome.recipe.mode == "auto"
    assert outcome.recipe.inputs == []
    # the played transcript is the existing PERMANENT seed42 golden
    assert _sha(outcome.transcript) == GOLDEN_TRANSCRIPT_SHA


def test_play_outcome_recipe_is_the_save_and_round_trips(tmp_path):
    import chronicle_forge.app as app

    recipe = app.play(app.PlayRequest(seed=42, auto=True)).recipe
    path = tmp_path / "run.recipe"
    save_recipe(recipe, path)
    assert read_recipe(path) == recipe


# --- explore (the new seam: recipe -> world -> P10–P14 lenses) ----------


def test_explore_composes_all_five_lenses():
    import chronicle_forge.app as app

    view = app.explore(_seed42_recipe())
    assert type(view).__name__ == "ChronicleView"
    assert view.model_config.get("frozen") is True
    assert view.model_config.get("extra") == "forbid"
    assert view.schema_version == "1"
    assert type(view.world).__name__ == "WorldView"
    assert type(view.timeline).__name__ == "TimelineView"
    assert type(view.narrative).__name__ == "NarrativeView"
    assert type(view.characters).__name__ == "CharacterObservatoryView"
    assert isinstance(view.heritage_markdown, str) and view.heritage_markdown


def test_explore_invents_no_truth_subviews_equal_lens_goldens():
    """The composed sub-views ARE the existing frozen lenses — asserted by hash."""
    import chronicle_forge.app as app

    view = app.explore(_seed42_recipe())
    assert _sha(view.world.model_dump_json()) == GOLDEN_WORLD_MODEL_SHA
    assert _sha(view.timeline.model_dump_json()) == GOLDEN_TIMELINE_SHA
    assert _sha(view.narrative.model_dump_json()) == GOLDEN_NARRATIVE_SHA
    assert _sha(view.characters.model_dump_json()) == GOLDEN_CHARACTER_SHA


def test_explore_json_is_id_free():
    import chronicle_forge.app as app

    js = app.chronicle_json(_seed42_recipe())
    for name, rx in (
        ("entity-id", _ID_RE),
        ("uuid", _UUID_RE),
        ("hex32", _HEX32_RE),
        ("hex40", _HEX40_RE),
    ):
        m = rx.search(js)
        assert m is None, f"{name} leaked into chronicle_json: {m!r}"
    assert "source_seed" not in js
    assert '_id"' not in js


def test_explore_json_is_deterministic_double_run():
    import chronicle_forge.app as app

    r = _seed42_recipe()
    assert app.chronicle_json(r) == app.chronicle_json(r)


def test_explore_does_not_mutate_recipe():
    import chronicle_forge.app as app

    r = _seed42_recipe()
    before = r.model_dump_json()
    app.explore(r)
    app.chronicle_json(r)
    assert r.model_dump_json() == before


def test_explore_json_hash_is_frozen_golden():
    import chronicle_forge.app as app

    assert _sha(app.chronicle_json(_seed42_recipe())) == GOLDEN_CHRONICLE_SHA


def test_explore_file_matches_explore(tmp_path):
    """explore_file(path) == read_recipe(path) + explore: same canonical view."""
    import chronicle_forge.app as app

    path = tmp_path / "run.recipe"
    save_recipe(_seed42_recipe(), path)
    via_file = app.explore_file(path).model_dump_json()
    via_recipe = app.explore(_seed42_recipe()).model_dump_json()
    assert via_file == via_recipe


# --- renderer purity (Markdown reads only the view) ---------------------


def test_chronicle_markdown_is_pure_and_titled():
    import chronicle_forge.app as app

    view = app.explore(_seed42_recipe())
    before = view.model_dump_json()
    md = app.chronicle_markdown(view)
    assert view.model_dump_json() == before  # view unchanged by rendering
    assert md == app.chronicle_markdown(view)  # deterministic
    assert md.startswith("# ")  # a headed document
    assert _ID_RE.search(md) is None  # the prose is id-free too


# --- share (reuse P9) ---------------------------------------------------


def test_share_writes_artifact_and_is_reproducible(tmp_path):
    import chronicle_forge.app as app

    recipe = app.play(app.PlayRequest(seed=42, auto=True)).recipe
    export = tmp_path / "run.txt"
    result = app.share(app.ShareRequest(recipe=recipe, export_path=str(export)))
    assert type(result).__name__ == "ShareResult"
    assert _sha(result.transcript) == GOLDEN_TRANSCRIPT_SHA
    assert export.exists()
    assert "--replay" in result.reproducible_command


# --- the full one-way path ----------------------------------------------


def test_full_one_way_path_play_save_explore_share(tmp_path):
    import chronicle_forge.app as app

    # play
    outcome = app.play(app.PlayRequest(seed=42, auto=True))
    # save
    path = tmp_path / "run.recipe"
    save_recipe(outcome.recipe, path)
    saved = read_recipe(path)
    assert saved == outcome.recipe
    # explore the saved world
    view = app.explore(saved)
    assert view.span == outcome.span
    assert view.ending_class == outcome.ending_class
    # share reproduces the very same transcript
    result = app.share(app.ShareRequest(recipe=saved))
    assert result.transcript == outcome.transcript


# --- boundary guard: P15 moves no engine golden -------------------------


def test_vertical_slice_leaves_existing_goldens():
    import chronicle_forge.app as app
    from chronicle_forge.autoplay import simulate_world
    from chronicle_forge.reporting.character import character_json
    from chronicle_forge.reporting.narrative import narrative_json
    from chronicle_forge.reporting.observatory import observatory
    from chronicle_forge.reporting.social_memory import social_memory_view
    from chronicle_forge.reporting.timeline import timeline_json
    from chronicle_forge.reporting.world_model import world_model_json

    app.explore(_seed42_recipe())  # running the slice must not perturb anything
    world = simulate_world(42, mode="opportunity")
    assert _sha(world.model_dump_json()) == GOLDEN_WORLD_SHA
    assert _sha(observatory(world)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(world)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(world)) == GOLDEN_WORLD_MODEL_SHA
    assert _sha(narrative_json(world)) == GOLDEN_NARRATIVE_SHA
    assert _sha(character_json(world)) == GOLDEN_CHARACTER_SHA
    assert _sha(timeline_json(world)) == GOLDEN_TIMELINE_SHA
