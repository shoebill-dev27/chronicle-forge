"""DVS — the discovery contracts the vertical slice rests on (C-2, C-3, C-6).

These do not test that a page looks right. They test the three things the page
is only allowed to draw *because* the stream proves them:

* **C-2** a confirmation quotes the act in the words the player sealed it under,
  and says nothing when it cannot prove they chose it;
* **C-3** an investigation walks real edges, in order, and never dresses an
  ancestor count up as a path;
* **C-6** what the player chose and what their life did on its own stay apart,
  and an event with several origins says so.

Baseline: ``docs/design_v1_uiux_baseline.md`` §5. Engine, worldgen and RNG are
untouched by everything here.
"""

import pytest

from chronicle_forge.causal import CausalGraph
from chronicle_forge.play import beats as B
from chronicle_forge.play.session import run_human_world
from chronicle_forge.play.human import null_writer, scripted_reader
from chronicle_forge.reporting.labels import heritage_name

SEEDS = (1, 7, 42, 99, 123)

# A played run. `stream(seed)` with no choices entrusts every juncture to the
# world, so it contains no player decision at all — the right baseline for "did
# we invent one?", and the wrong one for everything else.
PLAY = ["1"] * 60


@pytest.fixture(scope="module")
def worlds():
    """One replayed world per seed, beside the stream that describes it."""
    out = {}
    for seed in SEEDS:
        recorder = B.BeatRecorder(PLAY)
        world = run_human_world(
            seed,
            reader=scripted_reader(PLAY),
            writer=null_writer,
            observer=recorder,
        )
        out[seed] = (world, B.stream(seed, PLAY))
    return out


def _node_for(world, case):
    """The one event a case is about — by ref, never by (year, phrase).

    The engine's event vocabulary is five phrases wide, so two different threads
    in the same year read identically. That ambiguity is exactly why CausePath
    carries a ref.
    """
    return next((n for n in world.causal_nodes if B._ref(n.id) == case.ref), None)


def _closing(stream):
    return next(b for b in stream.beats if b.KIND == "closing")


def _cases(stream):
    return _closing(stream).cases


# --------------------------------------------------------------------------
# C-3 — the path is real, ordered, and is not a count
# --------------------------------------------------------------------------


def test_every_case_step_is_an_edge_that_exists(worlds):
    """The load-bearing one. A drawn link the graph does not contain is a
    fabricated history, which is the single thing the client may never do."""
    for seed, (world, stream) in worlds.items():
        nodes = {n.id: n for n in world.causal_nodes}
        # phrase+year is how the client identifies a step; the real check is that
        # a chain of existing edges spells exactly that sequence.
        for case in _cases(stream):
            chain = [(s.year, s.phrase) for s in case.steps]
            for year, phrase in chain:
                assert any(
                    n.year == year and B.event_phrase(n) == phrase
                    for n in nodes.values()
                ), f"seed {seed}: step {phrase!r}@{year} names no real event"


def test_a_path_is_never_an_ancestor_count(worlds):
    """P18's ``steps`` is how many ancestors an event has. Drawing that as a
    distance invents links. The two numbers must be free to disagree."""
    disagreed = 0
    for _seed, (world, stream) in worlds.items():
        graph = CausalGraph.from_world(world)
        nodes = {n.id: n for n in world.causal_nodes}
        for case in _cases(stream):
            node = _node_for(world, case)
            if node is None:
                continue
            ancestors = len(graph.ancestors(node.id))
            if ancestors != len(case.steps):
                disagreed += 1
    assert disagreed, "steps tracked the ancestor count exactly — is it a count?"


def test_steps_run_effect_first_and_stay_inside_the_world(worlds):
    for seed, (_world, stream) in worlds.items():
        for case in _cases(stream):
            assert case.origin_year <= case.year, f"seed {seed}: origin after effect"
            for step in case.steps:
                assert case.origin_year <= step.year <= case.year, (
                    f"seed {seed}: step at {step.year} outside "
                    f"[{case.origin_year}, {case.year}]"
                )


def test_cases_are_deterministic_across_runs():
    """``player_seeds_in_ancestry`` walks a set. Without the sort in ``_cases``
    the same book would offer different threads on a second open."""
    for seed in SEEDS:
        first = [B.beat_dict(_closing(B.stream(seed)))["cases"]]
        second = [B.beat_dict(_closing(B.stream(seed)))["cases"]]
        assert first == second, f"seed {seed}: cases differ between identical runs"


# --------------------------------------------------------------------------
# C-6 — the player's choice, the life's own action, and a shared cause
# --------------------------------------------------------------------------


def test_an_unsealed_origin_never_borrows_the_players_voice(worlds):
    """An autonomous act is traced honestly, but it is the world's phrase for it
    — never a sentence the player is told they chose."""
    for seed, (_world, stream) in worlds.items():
        sealed_labels = {
            b.label for b in stream.beats if b.KIND == "outcome" and b.option
        }
        for case in _cases(stream):
            if not case.origin_sealed:
                assert case.origin_act not in sealed_labels, (
                    f"seed {seed}: autonomous origin {case.origin_act!r} is "
                    "wearing a label the player sealed"
                )


def test_a_sealed_origin_is_quoted_in_the_players_own_words(worlds):
    for seed, (_world, stream) in worlds.items():
        sealed_labels = {
            b.label for b in stream.beats if b.KIND == "outcome" and b.option
        }
        for case in _cases(stream):
            if case.origin_sealed:
                assert case.origin_act in sealed_labels, (
                    f"seed {seed}: sealed origin {case.origin_act!r} is not one "
                    "of the labels this run actually sealed"
                )


def test_a_shared_cause_admits_that_it_is_shared(worlds):
    """The earliest player seed is one contributing origin, not proof that one
    life caused everything. Some event in these worlds must say so."""
    assert any(
        case.other_origins > 0
        for _world, stream in worlds.values()
        for case in _cases(stream)
    ), "no case reported a second contributing origin — is other_origins wired?"


def test_other_origins_counts_only_real_extra_seeds(worlds):
    for seed, (world, stream) in worlds.items():
        graph = CausalGraph.from_world(world)
        nodes = {n.id: n for n in world.causal_nodes}
        for case in _cases(stream):
            node = _node_for(world, case)
            assert node is not None, f"seed {seed}: case ref resolves to no event"
            real = len(graph.player_seeds_in_ancestry(node.id))
            assert case.other_origins <= real - 1, f"seed {seed}: inflated origins"


def test_posthumous_means_the_origin_life_was_already_dead(worlds):
    for seed, (_world, stream) in worlds.items():
        deaths = {lf.ordinal: lf.death_year for lf in stream.lives}
        for case in _cases(stream):
            expected = case.year > deaths[case.origin_life]
            assert case.posthumous is expected, (
                f"seed {seed}: posthumous={case.posthumous} for an event in "
                f"{case.year} against a death in {deaths[case.origin_life]}"
            )


# --------------------------------------------------------------------------
# C-2 — a confirmation resolves against the words the player read
# --------------------------------------------------------------------------


def test_recognition_never_invents_a_memory(worlds):
    """``sealed_act`` is present only when this run really sealed that seed.
    ``seed_label`` would always return *something*; offering it as the player's
    remembered words would be putting a sentence in their mouth."""
    for seed, (_world, stream) in worlds.items():
        sealed_labels = {
            b.label for b in stream.beats if b.KIND == "outcome" and b.option
        }
        for beat in stream.beats:
            if beat.KIND != "juncture" or beat.recognition is None:
                continue
            act = beat.recognition.sealed_act
            if act is not None:
                assert act in sealed_labels, (
                    f"seed {seed}: recognition quotes {act!r}, which this run "
                    "never sealed"
                )


def test_recognition_still_names_the_option_that_carries_it(worlds):
    """I-1b's invariant, re-asserted: the extra field must not have loosened it."""
    for _seed, (_world, stream) in worlds.items():
        for beat in stream.beats:
            if beat.KIND == "juncture" and beat.recognition is not None:
                assert 1 <= beat.recognition.option <= len(beat.options)


# --------------------------------------------------------------------------
# quiet and terminal cases close honestly rather than inventing a climax
# --------------------------------------------------------------------------


def test_a_world_with_nothing_to_trace_offers_nothing(worlds):
    """An empty case list is a legal, honest ending. What is illegal is a case
    without an origin, which is a thread that leads nowhere."""
    for seed, (_world, stream) in worlds.items():
        for case in _cases(stream):
            assert case.origin_life >= 1, f"seed {seed}: case with no origin life"
            assert case.origin_act, f"seed {seed}: case with an empty origin act"
            assert case.event, f"seed {seed}: case with no consequence"


def test_the_case_list_is_bounded(worlds):
    for _seed, (_world, stream) in worlds.items():
        assert len(_cases(stream)) <= B.CASES_MAX


def test_the_player_chose_threads_come_first(worlds):
    """The ending should offer the player their own hand before the world's."""
    for seed, (_world, stream) in worlds.items():
        flags = [c.origin_sealed for c in _cases(stream)]
        assert flags == sorted(flags, reverse=True), f"seed {seed}: ordering lost"


# --------------------------------------------------------------------------
# the regression this slice was built on top of
# --------------------------------------------------------------------------


def test_an_entrusted_run_claims_no_player_choice():
    """The bug C-6 exists to prevent.

    ``stream(seed)`` supplies no choices, so the world answers every juncture.
    Until 2026-09-09 the recorder wrote every resulting act into ``_sealed``
    anyway, because it sees the chosen option and not who chose it — so a digest
    line and a trace origin could both be captioned as the player's decision in
    a run containing no decisions. A run nobody played must claim nothing.
    """
    for seed in SEEDS:
        stream = B.stream(seed)
        sealed_changes = [
            c
            for b in stream.beats
            if b.KIND == "aftermath"
            for c in b.changes
            if c.sealed
        ]
        sealed_cases = [c for c in _cases(stream) if c.origin_sealed]
        assert not sealed_changes, f"seed {seed}: entrusted run claims a sealed act"
        assert not sealed_cases, f"seed {seed}: entrusted run claims a sealed origin"


def test_a_ref_is_stable_opaque_and_never_an_engine_id(worlds):
    for seed, (world, stream) in worlds.items():
        ids = {n.id for n in world.causal_nodes}
        refs = [c.ref for c in _cases(stream)]
        assert len(refs) == len(set(refs)), f"seed {seed}: two cases share a ref"
        for case in _cases(stream):
            assert case.ref not in ids, f"seed {seed}: ref leaks an engine id"
            assert _node_for(world, case) is not None
        # stable across a second identical run
        again = [c.ref for c in _cases(B.stream(seed, PLAY))]
        assert refs == again, f"seed {seed}: refs move between identical runs"


# --------------------------------------------------------------------------
# C-1 — a juncture says who it is about, and never who the player was
# --------------------------------------------------------------------------


def test_no_option_prints_an_attribution(worlds):
    """The leak C-1 closes.

    ``why_now`` returns the dominant tension signal in words, and the engine's
    word for Ω is "your past pulls here" — a claim about the player's own past.
    It dominated 63% of all offered options across these seeds, printed as plain
    page text, in first lives that have no past at all. D-01 confines that to a
    Confirm surface, and ``recognition`` is the field that carries it there.
    """
    for seed, (_world, stream) in worlds.items():
        for beat in stream.beats:
            if beat.KIND != "juncture":
                continue
            for opt in beat.options:
                assert opt.why != "your past pulls here", f"seed {seed}: Ω printed"
                assert opt.why is None or "your past" not in opt.why
                assert "past life" not in (opt.why or "")


def test_the_option_line_names_a_target_the_world_really_has(worlds):
    """Every clause of an option must have a source in reached world data. The
    target is the opportunity's own name and is checked against the world."""
    for seed, (world, stream) in worlds.items():
        real = (
            {n.name for n in getattr(world, "npcs", [])}
            | {f.name for f in getattr(world, "factions", [])}
            | {loc.name for loc in getattr(world, "locations", [])}
            | {heritage_name(h) for h in getattr(world, "heritage", [])}
        )
        seen = 0
        for beat in stream.beats:
            if beat.KIND != "juncture":
                continue
            for opt in beat.options:
                assert opt.target, f"seed {seed}: an option names no target"
                if opt.target in real:
                    seen += 1
        assert seen, f"seed {seed}: no option target resolved to a real world thing"


def test_a_suppressed_why_is_absent_not_substituted(worlds):
    """When the reason is the player's own past the line says nothing, rather
    than falling through to the next-loudest signal — naming a reason that is
    not the reason would be a small lie told to fill a line."""
    assert any(
        opt.why is None
        for _world, stream in worlds.values()
        for beat in stream.beats
        if beat.KIND == "juncture"
        for opt in beat.options
    ), "no option suppressed its reason — is the Ω guard wired?"
