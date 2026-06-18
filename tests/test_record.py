"""P9-3 input recorder contract (persistence/record.py)."""

from __future__ import annotations

from chronicle_forge import config
from chronicle_forge.play.human import scripted_reader
from chronicle_forge.play.session import run_human_world
from chronicle_forge.persistence import build_recipe, replay_transcript
from chronicle_forge.persistence.record import recording_reader

MAX_YEAR = config.DEV_WORLD_MAX_YEARS


def test_recording_reader_captures_consumed_lines():
    reader, captured = recording_reader(scripted_reader(["1", "abc", "2"]))
    assert reader() == "1"
    assert reader() == "abc"  # invalid entries are captured too (replay fidelity)
    assert reader() == "2"
    assert reader() is None  # EOF
    assert captured == ["1", "abc", "2"]  # EOF not recorded


def test_recording_reader_records_nothing_on_immediate_eof():
    reader, captured = recording_reader(scripted_reader([]))
    assert reader() is None
    assert captured == []  # an auto/EOF play records no inputs


def test_recorded_inputs_reproduce_the_run():
    # A recorded play, fed back as a recipe, replays to the same world+transcript.
    reader, captured = recording_reader(scripted_reader(["1", "1", "1", "1"]))
    buffer: list[str] = []
    original = run_human_world(123, reader=reader, writer=buffer.append)
    original_transcript = "".join(buffer)

    recipe = build_recipe(seed=123, max_year=MAX_YEAR, mode="human", inputs=captured)
    replayed, replayed_transcript = replay_transcript(recipe)

    assert replayed.model_dump_json() == original.model_dump_json()
    assert replayed_transcript == original_transcript
