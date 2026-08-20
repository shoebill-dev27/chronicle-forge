"""I-1b — the typed beat stream contract.

These pin the seam the client reads the game through: its shape, its
determinism, its ordering, and the two properties that keep it honest — an
aftermath that hardened nothing carries nothing, and a recognition always names
the option that actually carries it. They also assert the invariant that let the
seam exist at all: an observer changes no byte of the transcript.
"""

import hashlib
import json
import os
import subprocess
import sys

import pytest

from chronicle_forge.play import beats as B
from chronicle_forge.play.session import run_human_world
from chronicle_forge.reporting._data import life_index

SEEDS = (1, 7, 42, 99, 123)

REQUIRED = {
    "rebirth": {"life", "year", "talent", "era"},
    "juncture": {"life", "year", "age", "reason", "header", "era", "options"},
    "death": {"life", "year", "age", "talent", "title", "named", "pending"},
    "years": {"after_life", "from_year", "to_year", "span", "world_ended", "events"},
    "aftermath": {"after_life", "year", "echoes", "hardened"},
    "closing": {"year", "lives", "ending", "legacies"},
}


@pytest.fixture(scope="module")
def streams():
    return {seed: B.stream(seed) for seed in SEEDS}


def _transcript(seed, observer=None):
    out = []
    run_human_world(seed, reader=lambda: None, writer=out.append, observer=observer)
    return "".join(out)


@pytest.mark.parametrize("seed", SEEDS)
def test_an_observer_changes_no_byte_of_the_transcript(seed):
    # The whole seam rests on this: if watching the run changed the run, the
    # engine goldens and ENGINE_VERSION would be in play. They are not.
    assert _transcript(seed) == _transcript(seed, B.BeatRecorder())


@pytest.mark.parametrize("seed", SEEDS)
def test_the_stream_is_deterministic_in_the_seed(seed):
    first = json.dumps(B.to_dict(B.stream(seed)), sort_keys=True, ensure_ascii=False)
    second = json.dumps(B.to_dict(B.stream(seed)), sort_keys=True, ensure_ascii=False)
    assert first == second


@pytest.mark.parametrize("seed", SEEDS)
def test_the_stream_is_deterministic_in_the_choices(seed):
    a = B.to_dict(B.stream(seed, ["1", "1"]))
    b = B.to_dict(B.stream(seed, ["1", "1"]))
    assert a == b
    # ...and the first juncture is drawn before any choice is made, so it cannot
    # depend on one. The client relies on this to show a juncture before it has
    # a choice to replay with.
    firsts = [
        next(x for x in B.to_dict(B.stream(seed, c))["beats"] if x["t"] == "juncture")
        for c in ([], ["1"], ["2"], ["3"])
    ]
    assert firsts[1:] == firsts[:-1]


@pytest.mark.parametrize("seed", SEEDS)
def test_every_beat_matches_the_schema_and_is_json(streams, seed):
    data = B.to_dict(streams[seed])
    assert set(data) == {
        "seed",
        "place",
        "max_year",
        "end_year",
        "ending",
        "lives",
        "beats",
    }
    assert data["lives"] and all(
        set(life) == {"ordinal", "talent", "birth_year", "death_year"}
        for life in data["lives"]
    )
    for beat in data["beats"]:
        kind = beat["t"]
        assert kind in B.BEAT_KINDS
        assert REQUIRED[kind] <= set(
            beat
        ), f"{kind} is missing {REQUIRED[kind] - set(beat)}"
    json.dumps(data)  # the bridge must hand JS plain JSON


@pytest.mark.parametrize("seed", SEEDS)
def test_the_loop_is_ordered_death_then_years_then_aftermath(streams, seed):
    kinds = [b.KIND for b in streams[seed].beats]
    assert kinds[0] == "rebirth"
    assert kinds[-1] == "closing"
    assert kinds.count("closing") == 1
    for i, kind in enumerate(kinds[:-1]):
        if kind == "death":
            # B2 -> B3 -> B4: the aftermath is spoken by the years, after the
            # skip has run, never at the death. That ordering is the bug X-2
            # fixed and the stream has to preserve it.
            assert kinds[i + 1 : i + 3] == ["years", "aftermath"]
    # every life is born before it is asked anything and before it dies
    seen = set()
    for beat in streams[seed].beats:
        if beat.KIND == "rebirth":
            seen.add(beat.life)
        elif beat.KIND in ("juncture", "death"):
            assert beat.life in seen


@pytest.mark.parametrize("seed", SEEDS)
def test_a_recognition_always_names_an_option_that_carries_it(streams, seed):
    for beat in streams[seed].beats:
        if beat.KIND != "juncture":
            continue
        assert [o.n for o in beat.options] == list(range(1, len(beat.options) + 1))
        if beat.recognition is None:
            continue
        carrier = next(o for o in beat.options if o.n == beat.recognition.option)
        # The client marks exactly this line; if the id did not match, the mark
        # would be pointing at a choice no former self ever made.
        assert carrier.heritage_id is not None
        assert carrier.kind == "Legacy"
        assert beat.recognition.founder_life < beat.life


def test_the_empty_aftermath_is_a_first_class_case(streams):
    """A majority of aftermaths name nothing. The stream must say so plainly
    rather than omitting the beat, because the surface has to render silence."""
    empty = total = 0
    for world in streams.values():
        for beat in world.beats:
            if beat.KIND != "aftermath":
                continue
            total += 1
            if not beat.hardened:
                empty += 1
    assert total > 0 and empty > 0
    # In every measured seed the FIRST aftermath is one of them: a first life's
    # marks cannot have hardened yet. A client that only works when something
    # hardens would therefore be broken on the very first loop.
    for world in streams.values():
        first = next(b for b in world.beats if b.KIND == "aftermath")
        assert not first.hardened


@pytest.mark.parametrize("seed", SEEDS)
def test_hardened_marks_are_attributed_to_a_real_earlier_life(streams, seed):
    world = streams[seed]
    ordinals = {life.ordinal for life in world.lives}
    hardened = 0
    for beat in world.beats:
        if beat.KIND != "aftermath":
            continue
        for mark in beat.hardened:
            hardened += 1
            assert mark.name
            assert mark.founder_life in ordinals
            assert mark.founder_life <= beat.after_life
            assert mark.planted_year is not None
    assert hardened > 0, "no seed left a legacy at all — the fixture is wrong"


@pytest.mark.parametrize("seed", SEEDS)
def test_the_years_carry_the_events_of_the_skip_they_ran(streams, seed):
    world = streams[seed]
    for beat in world.beats:
        if beat.KIND != "years":
            continue
        assert beat.to_year - beat.from_year == beat.span
        for event in beat.events:
            assert beat.from_year < event.year <= beat.to_year
            assert event.phrase
            assert list(event.owners) == sorted(set(event.owners))
    # The finding the surface is built on: the world is loudest while the player
    # is dead, and it is mostly moving on what they left.
    events = [e for b in world.beats if b.KIND == "years" for e in b.events]
    assert events, "a world with no skip events would have nothing to show"
    owned = [e for e in events if e.owners]
    assert len(owned) / len(events) > 0.5


def test_life_ordinals_agree_with_the_reporting_layer():
    """The stream counts lives the way every other surface does, so a legacy is
    attributed to 'your first life' in the book and in the chronicle alike."""
    recorder = B.BeatRecorder()
    world = run_human_world(
        1, reader=lambda: None, writer=lambda _t: None, observer=recorder
    )
    index = life_index(world)
    expected = [index[life.id] for life in world.lives]
    born = [b.life for b in recorder.beats if b.KIND == "rebirth"]
    assert born == expected


_HASH_SNIPPET = """
import hashlib, json, sys
from chronicle_forge.play import beats as B
data = json.dumps(B.to_dict(B.stream(42)), sort_keys=True, ensure_ascii=False)
sys.stdout.write(hashlib.sha256(data.encode()).hexdigest())
"""


def test_the_stream_is_deterministic_across_processes():
    """Determinism checked inside one process cannot see hash randomisation:
    a single set of string ids iterated in insertion-independent order would
    still agree with itself. The client replays the world on every seal, and a
    capture replays it in a fresh interpreter, so the stream has to survive a
    new PYTHONHASHSEED."""
    digests = set()
    for seed in ("0", "1", "2", "12345"):
        out = subprocess.run(
            [sys.executable, "-c", _HASH_SNIPPET],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        digests.add(out.stdout.strip())
    assert len(digests) == 1, f"the stream moved with PYTHONHASHSEED: {digests}"


@pytest.mark.parametrize("seed", SEEDS)
def test_the_transcript_hash_is_the_same_with_and_without_an_observer(seed):
    """The byte-equality invariant, stated as a hash so a failure prints
    something readable rather than two multi-kilobyte transcripts."""
    plain = hashlib.sha256(_transcript(seed).encode()).hexdigest()
    watched = hashlib.sha256(_transcript(seed, B.BeatRecorder()).encode()).hexdigest()
    assert plain == watched


@pytest.mark.parametrize("seed", SEEDS)
def test_every_life_has_a_death_then_years_then_aftermath(streams, seed):
    """What the client's life-by-life walk stands on. If a life could ever end
    without its own window, the book would have nothing to turn to for it and
    would step over it again — which is exactly the bug that was fixed."""
    kinds = [b.KIND for b in streams[seed].beats]
    born = [b.life for b in streams[seed].beats if b.KIND == "rebirth"]
    died = [b.life for b in streams[seed].beats if b.KIND == "death"]
    assert born == sorted(born) == list(range(1, len(born) + 1))
    assert died == born, "a life was born that the stream never buries"
    for i, kind in enumerate(kinds):
        if kind == "death":
            assert kinds[i + 1 : i + 3] == ["years", "aftermath"]
