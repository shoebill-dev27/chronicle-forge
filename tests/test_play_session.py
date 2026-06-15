"""Integration tests for P8 session (play/session.py) — the reincarnating loop."""

from __future__ import annotations

import re

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.play.session import run_human_world

_JUNCTURE_HEADERS = (
    "A crisis gathers",
    "Something new stirs",
    "History remembers",
    "The world turns to you",
)


def _eof_reader():
    """A player who is never there — every juncture is entrusted to the world."""
    return None


def _always_act_reader():
    """A player who always takes the first offered option at every juncture."""
    return "1"


def _capture(seed, reader, life_cap=60):
    writes: list[str] = []
    world = run_human_world(
        seed, reader=reader, writer=writes.append, life_cap=life_cap
    )
    return world, "".join(writes)


# --- determinism & seed42 golden protection -----------------------------


def test_eof_run_is_byte_identical_to_opportunity_mode():
    # With a player who never acts, every turn delegates to the auto-chooser,
    # so the world must match opportunity-mode autoplay exactly.
    human_world, _ = _capture(42, _eof_reader)
    auto_world = simulate_world(42, mode="opportunity")
    assert human_world.model_dump_json() == auto_world.model_dump_json()


def test_run_is_stable_across_repeats():
    a, _ = _capture(42, _eof_reader)
    b, _ = _capture(42, _eof_reader)
    assert a.model_dump_json() == b.model_dump_json()


def test_acting_player_run_is_deterministic():
    a, ta = _capture(123, _always_act_reader)
    b, tb = _capture(123, _always_act_reader)
    assert a.model_dump_json() == b.model_dump_json()
    assert ta == tb


# --- the seven success conditions ---------------------------------------


def test_full_loop_delivers_the_core_experience():
    _, transcript = _capture(42, _always_act_reader)

    # 1. the world calls (a juncture header appears)
    assert any(h in transcript for h in _JUNCTURE_HEADERS)
    # 2. a choice is presented
    assert "[1]" in transcript and "[0] Let this season pass." in transcript
    # 3. death (the second-person death screen)
    assert "You lived" in transcript
    # 4. read the history (P7-2 chronicle and P7-3 timeline)
    assert "They lived as a" in transcript
    assert "## Their life" in transcript
    # 5. see the legacy (P7-4)
    assert "# What outlived you?" in transcript
    # 6. a next life begins
    assert "You are born again" in transcript
    # 7. encounter a former self
    assert "the work of" in transcript and "You come upon" in transcript


def test_former_self_recognized_once_per_heritage_across_lives():
    _, transcript = _capture(42, _always_act_reader)
    # Each recognition names the heritage: `You come upon "<name>"`. A given
    # name must be recognized at most once across the whole run — discovery,
    # not a recurring notification.
    names = re.findall(r'You come upon "([^"]+)"', transcript)
    assert names, "expected at least one former-self recognition"
    assert len(names) == len(set(names)), names


def test_rebirth_precedes_first_juncture():
    _, transcript = _capture(42, _always_act_reader)
    assert "You are born again" in transcript
    first_birth = transcript.index("You are born again")
    first_juncture = min(
        (transcript.index(h) for h in _JUNCTURE_HEADERS if h in transcript),
        default=-1,
    )
    assert first_juncture > first_birth  # the world calls only after you are born
