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

# I-3 P-10 digest, frozen over SEEDS (see test_the_digest_hash_is_frozen).
# Re-frozen 2026-09-09: `Change.sealed` now means the player really answered
# that juncture, so an entrusted run no longer reports acts as chosen.
GOLDEN_DIGEST_SHA = "02712226420968bd"

# A run somebody played. Needed wherever `sealed` is the subject.
PLAYED = ["1"] * 60

REQUIRED = {
    "rebirth": {"life", "year", "talent", "era"},
    "juncture": {"life", "year", "age", "reason", "header", "era", "options"},
    "outcome": {"life", "year", "age", "option", "label", "kind", "planted"},
    "death": {"life", "year", "age", "talent", "title", "named", "pending"},
    "years": {"after_life", "from_year", "to_year", "span", "world_ended", "events"},
    "aftermath": {"after_life", "year", "echoes", "hardened", "changes"},
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


@pytest.mark.parametrize("seed", SEEDS)
def test_hardened_marks_are_attributed_to_a_real_earlier_life(streams, seed):
    """Whenever an aftermath carries a hardened mark, its founder is a real life
    no later than the one that just died. (Marks now mostly harden during the
    founder's own long life, so many aftermaths carry none.)"""
    world = streams[seed]
    ordinals = {life.ordinal for life in world.lives}
    for beat in world.beats:
        if beat.KIND != "aftermath":
            continue
        for mark in beat.hardened:
            assert mark.name
            assert mark.founder_life in ordinals
            assert mark.founder_life <= beat.after_life
            assert mark.planted_year is not None


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
    # The world's horizon can end the run mid-life (owner decision 8): that
    # last life is alive and gets no death, years, or aftermath. Every other
    # life is buried.
    assert died in (born, born[:-1]), "a life was born that the stream never buries"
    if died != born:
        assert kinds[-1] == "closing" and kinds[-2] != "aftermath"
    for i, kind in enumerate(kinds):
        if kind == "death":
            assert kinds[i + 1 : i + 3] == ["years", "aftermath"]


# --------------------------------------------------------------------------
# I-2: the act the player sealed, read off the world the moment it ran
# --------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_every_answered_juncture_leaves_exactly_one_act(streams, seed):
    """One outcome per juncture, in order, on the same life.

    The client's entry pairs them by position — the act it shows for the Nth
    seal is the Nth outcome — so a stream that ever emitted an outcome for a
    turn nobody was asked about would make the book print an act the player
    never took.
    """
    kinds = [b.KIND for b in streams[seed].beats]
    junctures = [b for b in streams[seed].beats if b.KIND == "juncture"]
    outcomes = [b for b in streams[seed].beats if b.KIND == "outcome"]
    assert len(outcomes) == len(junctures)
    for juncture, outcome in zip(junctures, outcomes):
        assert outcome.life == juncture.life
        assert outcome.year >= juncture.year
    # and each one follows its own juncture immediately
    for i, kind in enumerate(kinds[:-1]):
        if kind == "juncture":
            assert kinds[i + 1] == "outcome"


@pytest.mark.parametrize("seed", SEEDS)
def test_an_act_never_claims_more_than_the_life_planted(streams, seed):
    """``planted`` is a measured delta, so it can never exceed the seeds the
    life actually owns — the turns the world took on its own plant too, and
    those are nobody's act."""
    world = run_human_world(seed, reader=lambda: None, writer=lambda _t: None)
    index = life_index(world)
    owned = {}
    for seed_obj in world.seeds:
        ordinal = index.get(seed_obj.planted_by_life_id)
        if ordinal:
            owned[ordinal] = owned.get(ordinal, 0) + 1
    claimed = {}
    for beat in streams[seed].beats:
        if beat.KIND == "outcome":
            assert beat.planted >= 0
            assert 0 <= beat.option <= 3
            claimed[beat.life] = claimed.get(beat.life, 0) + beat.planted
    for life, total in claimed.items():
        assert total <= owned.get(life, 0), (life, total, owned.get(life))


@pytest.mark.parametrize("seed", SEEDS)
def test_the_act_records_the_option_that_was_actually_sealed(seed):
    """A sealed number comes back as that number; a season let pass comes back
    as 0 rather than as an act the player did not choose."""
    for pick in ("1", "2"):
        stream = B.stream(seed, [pick])
        first = next(b for b in stream.beats if b.KIND == "outcome")
        assert first.option == int(pick)
    # the fully-entrusted run answers nothing itself
    entrusted = next(b for b in B.stream(seed).beats if b.KIND == "outcome")
    assert entrusted.option in (0, 1, 2, 3)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_act_is_labelled_in_the_engines_own_words(streams, seed):
    """The label is what the juncture displayed, never a re-worded version, and
    never an internal id (``_display_label`` exists to keep ``legacy:seed-0005``
    off the page)."""
    for beat in streams[seed].beats:
        if beat.KIND != "outcome":
            continue
        assert beat.label and ":" not in beat.label
        assert beat.label == beat.label.strip()


# --------------------------------------------------------------------------
# I-3 — the rebirth digest (P-10)
# --------------------------------------------------------------------------

DIGEST_SEEDS = tuple(range(1, 31))  # SP-1 is a claim about worlds, not a sample


def _world_of(seed):
    return run_human_world(
        seed, reader=lambda: None, writer=lambda _t: None, life_cap=60
    )


def _life_vocabulary(world, ordinal, stream):
    """(acts, consequences) the digest of the life ``ordinal`` may legally use.

    Rebuilt here from the world independently of the recorder, so the test can
    catch a digest that reached into a life other than the one that just died.
    """
    from chronicle_forge.play import render
    from chronicle_forge.reporting.labels import event_phrase, seed_label

    life = world.lives[ordinal - 1]
    acts = {seed_label(world, sid) for sid in render._seed_ids(world, life)}
    # plus the labels the player sealed those seeds under, which are the option
    # texts and exist nowhere in the reporting layer
    acts |= {b.label for b in stream.beats if b.KIND == "outcome" and b.life == ordinal}
    return acts, {event_phrase(n) for n in render._echoes(world, life)}


@pytest.mark.parametrize("seed", SEEDS)
def test_a_digest_line_descends_only_from_the_life_it_follows(streams, seed):
    """D-03: the digest delivers the immediately previous life and nothing else.
    Changes caused by older lives must be discovered, not handed over."""
    world = _world_of(seed)
    stream = streams[seed]
    checked = 0
    for beat in stream.beats:
        if beat.KIND != "aftermath":
            continue
        acts, consequences = _life_vocabulary(world, beat.after_life, stream)
        for change in beat.changes:
            checked += 1
            assert (
                change.act in acts
            ), f"{change.act!r} is not an act of life {beat.after_life}"
            assert change.consequence in consequences
    assert checked > 0


@pytest.mark.parametrize("seed", SEEDS)
def test_a_hardened_mark_never_becomes_a_digest_line(streams, seed):
    """Hardened marks stay on the aftermath for the surface and for tracing;
    the digest is built from echoes alone, so a mark's name is never an act
    or a consequence line (D-03: names are for the player to discover)."""
    names = set()
    for beat in streams[seed].beats:
        if beat.KIND != "aftermath":
            continue
        names |= {mark.name for mark in beat.hardened}
        for change in beat.changes:
            assert change.act not in names
            assert change.consequence not in names


@pytest.mark.parametrize("seed", SEEDS)
def test_one_act_and_one_consequence_make_exactly_one_line(streams, seed):
    """Seed 1's first rebirth has 31 echoes carrying 4 distinct phrases: taking
    the loudest three would print one sentence three times. Repetition is not
    more truth."""
    for beat in streams[seed].beats:
        if beat.KIND != "aftermath":
            continue
        keys = [(c.act, c.consequence) for c in beat.changes]
        assert len(keys) == len(set(keys))
        for change in beat.changes:
            assert change.times >= 1
            assert change.first_year >= 0


@pytest.mark.parametrize("seed", SEEDS)
def test_the_digest_order_is_total_and_belongs_to_the_stream(streams, seed):
    """What the player chose first, then what the world did most with it. The
    page renders this order and never re-sorts, so it has to be total: any tie
    left here would let two runs of one seed disagree."""
    for beat in streams[seed].beats:
        if beat.KIND != "aftermath":
            continue
        key = lambda c: (not c.sealed, -c.times, c.first_year, c.act, c.consequence)
        assert list(beat.changes) == sorted(beat.changes, key=key)
        assert len({key(c) for c in beat.changes}) == len(beat.changes)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_digest_delivers_at_most_three(streams, seed):
    """UX §P-10. The cut is made in the stream, not on the page: D-03 reserves
    everything past it for the player to find, so the client must never be
    handed the remainder."""
    for beat in streams[seed].beats:
        if beat.KIND == "aftermath":
            assert len(beat.changes) <= B.DIGEST_MAX == 3


def test_a_digest_is_empty_only_when_no_life_follows():
    """17 of 116 aftermaths across seeds 1-30 name nothing, and all 17 are the
    world's last — where there is no rebirth and so no digest page. The client
    still fails closed on `win.rebirth`; this is what makes that a guard rather
    than a code path."""
    empty_midworld = []
    for seed in DIGEST_SEEDS:
        stream = B.stream(seed)
        last = stream.lives[-1].ordinal
        for beat in stream.beats:
            if (
                beat.KIND == "aftermath"
                and not beat.changes
                and beat.after_life != last
            ):
                empty_midworld.append((seed, beat.after_life))
    assert not empty_midworld


def test_the_digest_hash_is_frozen():
    """Cheap drift detection under the invariants above, which are the real
    guard: a hash cannot tell you SP-1 held."""
    payload = []
    for seed in SEEDS:
        for beat in B.stream(seed).beats:
            if beat.KIND == "aftermath":
                payload.append([seed, beat.after_life, B.beat_dict(beat)["changes"]])
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]
    assert digest == GOLDEN_DIGEST_SHA
