"""Tests for P8 choosers (play/human.py)."""

from __future__ import annotations

from chronicle_forge.execution import ExecutionOption
from chronicle_forge.opportunity import Opportunity, OpportunityKind, Signals
from chronicle_forge.play import human
from chronicle_forge.play.render import option_index_for_choice


def _opt(target, tension, label):
    opp = Opportunity(OpportunityKind.NPC, target, f"name:{target}", tension, Signals())
    return ExecutionOption(opp, "perform_activity", label)


def _fallback():
    return ExecutionOption(None, "perform_activity", "Live quietly")


def _options():
    # tension order: w(0.95) > m(0.70) > l(0.50); fallback last.
    return [
        _opt("m", 0.70, "Mentor Maren"),
        _opt("w", 0.95, "Stand against Korr"),
        _opt("l", 0.50, "Develop Vow Hollow"),
        _fallback(),
    ]


def _spy_pass():
    """A let-pass handler that records its calls and returns the fallback index."""
    calls = {"n": 0}

    def handler(options):
        calls["n"] += 1
        return next(i for i, o in enumerate(options) if o.opportunity is None)

    return handler, calls


# --- normal input -------------------------------------------------------


def test_normal_input_picks_displayed_option():
    options = _options()
    chooser = human.make_script_chooser(["1"])
    # display [1] is the highest tension (the wildcard), at options index 1
    assert chooser(options) == 1
    assert option_index_for_choice(options, 1) == 1


def test_each_displayed_number_maps_correctly():
    options = _options()
    assert human.make_script_chooser(["1"])(options) == 1  # wildcard 0.95
    assert human.make_script_chooser(["2"])(options) == 0  # mentor 0.70
    assert human.make_script_chooser(["3"])(options) == 2  # location 0.50


# --- out-of-range / non-numeric re-prompt -------------------------------


def test_out_of_range_reprompts_then_accepts():
    writes = []
    reader = human.scripted_reader(["9", "1"])
    chooser = human.make_human_chooser(reader, writes.append, human._fallback_pass)
    assert chooser(_options()) == 1
    assert human.INVALID in writes  # the invalid notice was emitted


def test_non_numeric_reprompts_then_accepts():
    writes = []
    reader = human.scripted_reader(["abc", "2"])
    chooser = human.make_human_chooser(reader, writes.append, human._fallback_pass)
    assert chooser(_options()) == 0
    assert human.INVALID in writes


# --- EOF / empty / [0] all entrust the turn to the world ----------------


def test_eof_entrusts_to_the_world():
    handler, calls = _spy_pass()
    chooser = human.make_script_chooser([], on_let_pass=handler)
    options = _options()
    assert chooser(options) == 3  # the fallback index
    assert calls["n"] == 1  # on_let_pass was invoked


def test_empty_input_entrusts_to_the_world():
    handler, calls = _spy_pass()
    chooser = human.make_script_chooser([""], on_let_pass=handler)
    assert chooser(_options()) == 3
    assert calls["n"] == 1


def test_zero_is_always_selectable_and_entrusts():
    handler, calls = _spy_pass()
    chooser = human.make_script_chooser(["0"], on_let_pass=handler)
    assert chooser(_options()) == 3
    assert calls["n"] == 1


def test_eof_prompt_is_terminated_with_a_newline():
    writes = []
    reader = human.scripted_reader([])  # immediate EOF
    human.make_human_chooser(reader, writes.append, human._fallback_pass)(_options())
    # the dangling prompt must end its line so it cannot run into later output
    assert "".join(writes) == human.PROMPT + "\n"


# --- script chooser consumption order -----------------------------------


def test_script_consumes_inputs_in_order():
    # invalid entries are consumed and re-prompted just like the human chooser
    reader = human.scripted_reader(["abc", "9", "2"])
    chooser = human.make_human_chooser(reader, human.null_writer, human._fallback_pass)
    assert chooser(_options()) == 0  # resolves on the third entry ("2")
    # the reader is now exhausted -> the next read is EOF (None)
    assert reader() is None


def test_separate_choosers_consume_independently():
    options = _options()
    c1 = human.make_script_chooser(["1", "2"])
    # one chooser call consumes exactly one resolved decision
    assert c1(options) == 1
    assert c1(options) == 0  # second call consumes the next input


# --- determinism & read-only --------------------------------------------


def test_same_inputs_same_result():
    def run():
        return human.make_script_chooser(["9", "abc", "3"])(_options())

    assert run() == run() == 2


def test_chooser_does_not_mutate_options():
    options = _options()
    before = [
        (o.label, o.target_id, getattr(o.opportunity, "tension", None)) for o in options
    ]
    human.make_script_chooser(["1"])(options)
    after = [
        (o.label, o.target_id, getattr(o.opportunity, "tension", None)) for o in options
    ]
    assert before == after
    assert len(options) == 4
