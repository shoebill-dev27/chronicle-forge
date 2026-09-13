"""The Unity fixture is the same world, keyed the way the gate needs it.

These tests guard the seam, not the engine: that the exporter adds no truth,
that its identity matches the book store's, and that every coordinate a Unity
surface must withhold is actually listed as locked. A leak here would let the
Unity client attribute a mark the reader has not earned, which is the one class
of bug the whole discovery design exists to prevent.
"""

from __future__ import annotations

import json

from chronicle_forge.client.fixture import (
    DVS_CHOICES,
    DVS_SEED,
    dvs_fixture,
    write_fixture,
)
from chronicle_forge.client.state import BookState, canonical_hash
from chronicle_forge.play import beats as beat_stream
from chronicle_forge.persistence.version import ENGINE_VERSION


def _as_json(data):
    """Through JSON and back.

    ``beats.to_dict`` keeps the stream's tuples, and JSON has only arrays — so a
    fixture in memory and the same fixture on disk differ by container type and
    nothing else. Comparing the JSON forms is what asks the question the tests
    actually mean.
    """
    return json.loads(json.dumps(data, ensure_ascii=False, sort_keys=True))


def test_fixture_stream_is_byte_identical_to_the_beat_stream():
    """The exporter serialises; it does not transform."""
    fixture = dvs_fixture()
    direct = beat_stream.to_dict(beat_stream.stream(DVS_SEED, list(DVS_CHOICES)))
    assert _as_json(fixture["stream"]) == _as_json(direct)


def test_fixture_identity_matches_the_book_store():
    """A fixture and a resumed book must agree on which world this is."""
    fixture = dvs_fixture()
    state = BookState.new(
        seed=DVS_SEED,
        max_year=fixture["stream"]["max_year"],
        inputs=list(DVS_CHOICES),
    )
    assert fixture["canonical_hash"] == canonical_hash(state.recipe)
    assert fixture["engine_version"] == ENGINE_VERSION


def test_fixture_is_deterministic():
    assert _as_json(dvs_fixture()) == _as_json(dvs_fixture())


def test_every_hardened_mark_is_locked():
    """D-03: a mark's founder may not be drawn until its ref is confirmed."""
    fixture = dvs_fixture()
    locked = set(fixture["discovery"]["locked"])
    for beat in fixture["stream"]["beats"]:
        if beat["t"] == "aftermath":
            for mark in beat["hardened"]:
                assert mark["ref"] in locked, f"unlocked mark {mark['name']}"


def test_every_case_is_locked():
    """D-04: inspecting a consequence confirms nothing on its own."""
    fixture = dvs_fixture()
    locked = set(fixture["discovery"]["locked"])
    for beat in fixture["stream"]["beats"]:
        if beat["t"] == "closing":
            for case in beat["cases"]:
                assert case["ref"] in locked


def test_every_recognition_is_locked():
    """Arriving on a page may not hand over an attribution."""
    fixture = dvs_fixture()
    locked = set(fixture["discovery"]["locked"])
    found = 0
    for beat in fixture["stream"]["beats"]:
        if beat["t"] == "juncture" and beat.get("recognition"):
            carrier = next(
                o for o in beat["options"] if o["n"] == beat["recognition"]["option"]
            )
            if carrier.get("heritage_id"):
                found += 1
                assert carrier["heritage_id"] in locked
    # Seed 1 is the DVS reference precisely because it HAS a recognition; a
    # fixture with none would make the whole confirm tier untestable.
    assert found > 0


def test_no_juncture_option_names_the_players_own_past():
    """D-01 holds on every decision surface the Unity client can draw."""
    for beat in dvs_fixture()["stream"]["beats"]:
        if beat["t"] == "juncture":
            for option in beat["options"]:
                why = option["why"] or ""
                assert "your past" not in why.lower()


def test_cause_paths_are_ordered_real_edges():
    """C-3: ``steps`` are the events BETWEEN consequence and origin, effect-first.

    The consequence itself and the origin seed are the two ends and are NOT in
    ``steps`` — an empty tuple is the honest shape of a direct cause. So the walk
    a surface draws is consequence → steps… → origin, and every year along it
    must run backwards.
    """
    for beat in dvs_fixture()["stream"]["beats"]:
        if beat["t"] == "closing":
            for case in beat["cases"]:
                years = [
                    case["year"],
                    *(s["year"] for s in case["steps"]),
                    case["origin_year"],
                ]
                assert years == sorted(years, reverse=True), years
                for step in case["steps"]:
                    assert step["phrase"], "an intermediate hop with no event"


def test_written_fixture_round_trips(tmp_path):
    target = tmp_path / "dvs.json"
    written = write_fixture(target)
    assert json.loads(target.read_text(encoding="utf-8")) == _as_json(written)


def test_shipped_fixture_is_current():
    """The file Unity loads is the file this engine produces."""
    shipped = json.loads(
        (
            __import__("pathlib").Path(__file__).resolve().parents[1]
            / "unity/Assets/ChronicleForge/Resources/dvs_fixture.json"
        ).read_text(encoding="utf-8")
    )
    assert shipped == _as_json(dvs_fixture())
