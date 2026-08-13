"""X-1..X-4 — the first loop must pay off, and must not lie while doing it.

The bottleneck audit (docs/experience_bottlenecks.md) measured three failures in
the opening of the game, all of them timing rather than missing data:

- the run had no ending at all — `play` stopped on "the world stands at its end";
- the death screen asserted "nothing you built survived long after your death"
  at the one moment when nothing *could* have survived yet, and the world's own
  chronicle then listed that same life as the founder of legacies that outlasted
  the age;
- the first recognition landed in the third life in 30 of 30 audited seeds, so
  the opening was ~5 choices whose only feedback was that false verdict.

These tests pin the fixes as properties over several seeds rather than against
one transcript, so re-wording a passage cannot silently un-fix them. The frozen
seed-42 transcript hash lives in `test_replay.py`; nothing here duplicates it.
"""

from __future__ import annotations

import io

import pytest

from chronicle_forge.play import adapter
from chronicle_forge.play.session import run_human_world
from chronicle_forge.reporting._data import heritage_rows, life_index, seed_by_id

SEEDS = [1, 7, 42, 99, 123, 404, 777]


def _transcript(seed: int) -> str:
    """A whole unattended world, as the player would receive it."""
    buf = io.StringIO()
    adapter.run(seed=seed, auto=True, script_lines=None, writer=buf.write)
    return buf.getvalue()


def _world_and_transcript(seed: int):
    buf = io.StringIO()
    world = run_human_world(seed, reader=lambda: None, writer=buf.write)
    return world, buf.getvalue()


# --- X-1: the run ends on something -------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_a_finished_world_closes_on_its_chronicle(seed):
    """`play` alone used to end mid-air: no ending, no account of what was left,
    and no way to the chronicle without `--save` plus a second command."""
    world, transcript = _world_and_transcript(seed)
    tail = transcript[transcript.index("━━ The Chronicle of") :]
    assert world.ending_class in tail
    assert f"{world.current_year} years" in tail
    assert "What you left behind:" in tail or "Nothing you built outlasted" in tail


@pytest.mark.parametrize("seed", SEEDS)
def test_the_closing_page_offers_another_world(seed):
    """Success criterion 4 is that the player starts a second world *to leave a
    different mark*. Nothing ever asked, so the run has to ask."""
    transcript = _transcript(seed)
    assert f"chronicle-forge play --seed {seed + 1}" in transcript


@pytest.mark.parametrize("seed", SEEDS)
def test_the_closing_page_names_the_life_behind_each_legacy(seed):
    """Success criterion 2: the player can say which life caused what. A legacy
    listed without its founder cannot deliver that."""
    world, transcript = _world_and_transcript(seed)
    if not world.heritage:
        pytest.skip("world left nothing behind")
    tail = transcript[transcript.index("What you left behind:") :]
    top = heritage_rows(world)[0]
    assert top["name"] in tail
    assert "life chose to" in tail


# --- X-2: the death beat must not contradict the chronicle --------------


@pytest.mark.parametrize("seed", SEEDS)
def test_no_death_claims_nothing_survived(seed):
    """The specific false sentence, gone. It was reachable for every life,
    including lives the chronicle credits with founding institutions."""
    transcript = _transcript(seed)
    assert "Nothing you built survived long after your death" not in transcript
    assert "Nothing they built outlasted the age" not in transcript


@pytest.mark.parametrize("seed", SEEDS)
def test_a_life_that_founded_a_legacy_is_never_written_off(seed):
    """The contradiction itself, stated as a property: any life the finished
    world credits as a founder must not have been told it left nothing."""
    world, transcript = _world_and_transcript(seed)
    founders = {
        seed_by_id(world, h.seed_id).planted_by_life_id
        for h in world.heritage
        if seed_by_id(world, h.seed_id) is not None
    }
    if not founders - {None}:
        pytest.skip("world left nothing behind")
    assert "you set nothing in motion" not in transcript.lower()


def test_death_says_nothing_of_a_verdict_it_cannot_yet_have():
    """A first life dies before any of its marks can harden — promotion happens
    in the time-skip that follows. So the death may report what is *unfinished*
    and must not report an outcome."""
    world = _world_and_transcript(42)[0]
    from chronicle_forge.play import render

    passage = render.death_passage(world, world.lives[0])
    assert "unfinished" in passage
    assert "survived" not in passage


@pytest.mark.parametrize("seed", SEEDS)
def test_the_death_beat_prints_no_markup(seed):
    """It used to chain four Markdown renderers into a plain-text stream, so the
    player read `# A scholar of Farrowdale` and `**Year 0**` verbatim."""
    transcript = _transcript(seed)
    for markup in ("# ", "## ", "**", "> "):
        assert markup not in transcript, f"{markup!r} leaked into the transcript"


# --- X-4: the first payoff must not wait for the third life -------------


@pytest.mark.parametrize("seed", SEEDS)
def test_the_first_life_is_answered_by_the_years_that_follow(seed):
    """The measured 0-of-30: no recognition before life 3. A first life cannot
    recognise anything, but the events its own seeds caused after it died are
    real, already in the world, and land in the very first time-skip."""
    transcript = _transcript(seed)
    first_death = transcript.index("You lived")
    second_birth = transcript.index("You are born again", first_death)
    assert "In those years the world moved on what you left:" in (
        transcript[first_death:second_birth]
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_the_payoff_arrives_before_the_last_life(seed):
    """Whatever else changes, the hook has to close early enough to be a hook."""
    transcript = _transcript(seed)
    births = [
        i
        for i in range(len(transcript))
        if transcript.startswith("You are born again", i)
    ]
    payoff = transcript.index("In those years the world moved on what you left:")
    assert payoff < births[-1], "the first payoff lands only in the final life"


@pytest.mark.parametrize("seed", SEEDS)
def test_a_named_legacy_is_attributed_to_the_life_that_planted_it(seed):
    """The deeper beat: a mark hardens a life or two after the life that made
    it, and is credited to that life by name. Felt time between the mark and
    finding it is the design's whole point, so this must not collapse into the
    life that just died."""
    world, transcript = _world_and_transcript(seed)
    if not world.heritage:
        pytest.skip("world left nothing behind")
    assert "set down has taken a name:" in transcript
    ordinals = {life_index(world)[life.id] for life in world.lives}
    assert any(f"your {word} life" in transcript for word in ("first", "second"))
    assert max(ordinals) >= 2


# --- attribution must agree wherever the player meets a legacy ----------


def test_a_former_self_is_named_by_its_life_not_by_a_distance():
    """`_former_self_line` spoke the founder's *ordinal* as though it were a
    count of lifetimes, so life 1's work was "1 life ago" even when met in life
    4. Every surface now names the life itself."""
    transcript = _transcript(42)
    assert "life ago" not in transcript
    assert "lives ago" not in transcript
    assert "the work of your" in transcript


# --- the guardrail ------------------------------------------------------


def test_presentation_changes_leave_the_world_untouched():
    """Every beat above is composed from data the world already held. Playing a
    seed must still produce the same world it did before, or a recorded recipe
    would replay into a different history."""
    from chronicle_forge.autoplay import simulate_world

    world, _ = _world_and_transcript(42)
    assert (
        world.model_dump_json()
        == simulate_world(42, mode="opportunity").model_dump_json()
    )
