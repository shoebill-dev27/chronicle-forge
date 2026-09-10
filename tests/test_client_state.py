"""C-5 — the client's persistent book state.

The contract the rest of the slice leans on: a reader can quit mid-choice and
come back to exactly where they were, with exactly what they had uncovered, and
never with someone else's discoveries.

Baseline: ``docs/design_v1_uiux_baseline.md`` §5 C-5, ``v1_client_state_spec.md``
CS-2 (reveals bind to a world) and CS-3 (the reveal set only grows).
"""

import json

import pytest

from chronicle_forge.client.state import (
    BookState,
    CorruptBookState,
    canonical_hash,
    load_book,
    save_book,
)
from chronicle_forge.persistence.schema import EngineVersionMismatch


@pytest.fixture
def book(tmp_path):
    return BookState.new(seed=42, max_year=200)


# --------------------------------------------------------------------------
# roundtrip and exact resume
# --------------------------------------------------------------------------


def test_a_book_survives_a_roundtrip_exactly(tmp_path, book):
    played = (
        book.seal(1)
        .seal(3)
        .confirm("P10_DIGEST", "node-7")
        .confirm("P14_TRACE", "node-9")
        .at(page="juncture", life_ordinal=2, juncture_index=1, selected_option=2)
    )
    path = tmp_path / "book.json"
    save_book(played, path)
    assert load_book(path) == played


def test_resume_restores_a_selected_but_unsealed_option(tmp_path, book):
    """The hard case DoD-6 names. Selection is not commitment: the option comes
    back previewed and still unsealed, and the recipe has not grown for it."""
    mid = book.seal(1).at(page="juncture", life_ordinal=1, selected_option=3)
    path = tmp_path / "book.json"
    save_book(mid, path)
    back = load_book(path)
    assert back.cursor.selected_option == 3
    assert back.recipe.inputs == ["1"], "a selection must not reach the recipe"


def test_the_archive_cursor_never_moves_the_unresolved_page(tmp_path, book):
    """Navigation is not commitment: reading life 1 back leaves the page the
    reader must still answer exactly where it was, for 「今の頁へ」 to return to."""
    live = book.seal(1).at(page="juncture", life_ordinal=2, selected_option=1)
    browsing = live.at(archive_life=1)
    assert browsing.cursor.page == "juncture"
    assert browsing.cursor.life_ordinal == 2
    assert browsing.cursor.selected_option == 1
    assert browsing.recipe.inputs == live.recipe.inputs


# --------------------------------------------------------------------------
# CS-2 — a reveal belongs to one world
# --------------------------------------------------------------------------


def test_same_seed_different_choices_are_different_worlds(book):
    a = book.seal(1).seal(1)
    b = book.seal(1).seal(2)
    assert a.recipe.seed == b.recipe.seed
    assert a.canonical_hash != b.canonical_hash, "same-seed books share an identity"


def test_a_foreign_reveal_set_is_dropped_rather_than_mis_rendered(tmp_path, book):
    """The D-08 protection. Swap the recipe under a stored book — the reveal
    coordinates now name facts in a world that is not this one, so they go."""
    a = book.seal(1).seal(1).confirm("P14_TRACE", "node-3")
    path = tmp_path / "book.json"
    save_book(a, path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["recipe"]["inputs"] = ["1", "2"]  # a different world entirely
    path.write_text(json.dumps(raw), encoding="utf-8")

    back = load_book(path)
    assert back.reveals == [], "reveals from another world were kept"
    assert back.recipe.inputs == ["1", "2"], "the recipe is the canon and stays"
    assert back.canonical_hash == canonical_hash(back.recipe)


def test_growing_the_recipe_keeps_what_was_already_earned(tmp_path, book):
    """The past is immutable and the recipe only grows, so a reveal earned at
    two choices still names the same fact at four. Permanence (D-04) would be
    impossible if sealing invalidated the store."""
    early = book.seal(1).confirm("S02_HOLD", "node-11")
    later = early.seal(2).seal(3)
    path = tmp_path / "book.json"
    save_book(later, path)
    back = load_book(path)
    assert back.knows("node-11")
    assert back.recipe.inputs == ["1", "2", "3"]


# --------------------------------------------------------------------------
# CS-3 — the set only grows, and only a confirm grows it
# --------------------------------------------------------------------------


def test_confirming_is_idempotent_and_monotone(book):
    once = book.confirm("P10_DIGEST", "node-1")
    twice = once.confirm("P10_DIGEST", "node-1")
    assert len(twice.reveals) == 1
    assert len(twice.confirm("P14_TRACE", "node-2").reveals) == 2


def test_a_confirmed_connection_is_known_however_it_was_earned(book):
    """Once confirmed, a connection stays confirmed everywhere it appears —
    the surface records how it was earned, it does not gate what is known."""
    assert book.confirm("P14_TRACE", "node-5").knows("node-5")


def test_reading_earns_nothing(book):
    """`knows` is the render path and must be free of side effects, or moving
    through the archive would confirm things D-04 reserves for the player."""
    before = book.confirm("P10_DIGEST", "node-1")
    for _ in range(3):
        before.knows("node-2")
        before.knows("node-1")
    assert len(before.reveals) == 1


def test_an_unrevealed_attribution_stays_unrevealed_across_a_reopen(tmp_path, book):
    played = book.seal(1).confirm("P10_DIGEST", "node-1")
    path = tmp_path / "book.json"
    save_book(played, path)
    back = load_book(path)
    assert back.knows("node-1")
    assert not back.knows("node-2"), "a reopen must not widen what is known"


# --------------------------------------------------------------------------
# failing closed
# --------------------------------------------------------------------------


def test_a_corrupt_book_is_refused_not_repaired(tmp_path):
    path = tmp_path / "book.json"
    path.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(CorruptBookState):
        load_book(path)


def test_an_off_schema_book_is_refused(tmp_path, book):
    path = tmp_path / "book.json"
    save_book(book, path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["something_this_build_never_wrote"] = True
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(CorruptBookState):
        load_book(path)


def test_a_missing_book_is_refused(tmp_path):
    with pytest.raises(CorruptBookState):
        load_book(tmp_path / "nothing-here.json")


def test_a_book_from_another_engine_is_refused(tmp_path, book):
    """Mirrors the recipe's own gate: a snapshot-free save is reconstructed by
    re-running the engine, and a different engine reconstructs a different
    world. Refusing beats resuming someone into a divergent history."""
    path = tmp_path / "book.json"
    save_book(book, path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["recipe"]["engine_version"] = "0.0.0-not-this-one"
    raw["canonical_hash"] = canonical_hash(
        type(book.recipe).model_validate(raw["recipe"])
    )
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(EngineVersionMismatch):
        load_book(path)


def test_a_save_is_atomic(tmp_path, book):
    """A crashed save must leave the previous book, never a truncated one."""
    path = tmp_path / "book.json"
    save_book(book.seal(1), path)
    first = load_book(path)
    save_book(first.seal(2), path)
    assert not list(tmp_path.glob("*.tmp")), "a temp file was left behind"
    assert load_book(path).recipe.inputs == ["1", "2"]


# --------------------------------------------------------------------------
# a finished book
# --------------------------------------------------------------------------


def test_a_finished_book_freezes_its_recipe_but_not_its_reveals(tmp_path, book):
    """Revisiting a finished world and tracing still earns reveals — D-04
    permanence applies forward, never backward."""
    done = book.seal(1).seal(2).finish()
    with pytest.raises(ValueError):
        done.seal(3)
    grown = done.confirm("P14_TRACE", "node-42")
    path = tmp_path / "book.json"
    save_book(grown, path)
    back = load_book(path)
    assert back.status == "FINISHED"
    assert back.knows("node-42")
