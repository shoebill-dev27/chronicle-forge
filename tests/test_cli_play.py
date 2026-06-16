"""Tests for the P8 CLI (play/cli.py, adapter.py, __main__.py).

The CLI is a thin wiring layer: it must add no output of its own and introduce
no determinism diff versus calling the session directly. These tests pin the
argument parsing, the reader selection, the --auto/--script branches, the
debug-to-stderr discipline, and the thin-wrapper guarantee (CLI stdout is
byte-identical to the equivalent ``run_human_world`` call).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from chronicle_forge.play import adapter
from chronicle_forge.play.__main__ import main
from chronicle_forge.play.cli import parse_args
from chronicle_forge.play.human import scripted_reader
from chronicle_forge.play.session import run_human_world

# --- argument parsing ---------------------------------------------------


def test_parse_args_defaults():
    a = parse_args(["--seed", "42"])
    assert a.seed == 42
    assert a.auto is False
    assert a.script_path is None
    assert a.debug is False


def test_parse_args_all_switches():
    a = parse_args(["--seed", "7", "--auto", "--script", "plays.txt", "--debug"])
    assert a.seed == 7
    assert a.auto is True
    assert a.script_path == "plays.txt"
    assert a.debug is True


def test_seed_is_required():
    with pytest.raises(SystemExit):
        parse_args([])


# --- reader selection (pure) --------------------------------------------


def test_build_reader_default_is_none_for_live_stdin():
    # None -> the session uses its own live stdin reader.
    assert adapter.build_reader(auto=False, script_lines=None) is None


def test_build_reader_auto_is_eof():
    reader = adapter.build_reader(auto=True, script_lines=None)
    assert reader() is None  # always EOF -> entrust to the world


def test_build_reader_script_wins_over_auto():
    reader = adapter.build_reader(auto=True, script_lines=["1", "2"])
    assert reader() == "1"
    assert reader() == "2"
    assert reader() is None  # exhausted -> EOF


# --- thin-wrapper guarantee: CLI stdout == direct session output --------


def _session_output(seed, reader, life_cap=60):
    writes: list[str] = []
    run_human_world(seed, reader=reader, writer=writes.append, life_cap=life_cap)
    return "".join(writes)


def test_auto_output_matches_session_eof(capsys):
    main(["--seed", "42", "--auto"])
    cli_out = capsys.readouterr().out
    assert cli_out == _session_output(42, lambda: None)


def test_script_output_matches_session_scripted(tmp_path, capsys):
    script = tmp_path / "plays.txt"
    script.write_text("1\n1\n1\n", encoding="utf-8")
    main(["--seed", "123", "--script", str(script)])
    cli_out = capsys.readouterr().out
    assert cli_out == _session_output(123, scripted_reader(["1", "1", "1"]))


def test_auto_run_is_stable_across_repeats(capsys):
    main(["--seed", "42", "--auto"])
    first = capsys.readouterr().out
    main(["--seed", "42", "--auto"])
    second = capsys.readouterr().out
    assert first == second


# --- debug: stderr only, stdout stays a clean transcript ----------------


def test_debug_logs_to_stderr_and_not_stdout(capsys):
    main(["--seed", "42", "--auto", "--debug"])
    captured = capsys.readouterr()
    start_line = '{"event": "start", "mode": "auto", "seed": 42}'
    assert start_line in captured.err
    assert '"event": "end"' in captured.err
    # the structured trace must never bleed into the transcript
    assert '"event"' not in captured.out


def test_debug_does_not_change_the_transcript(capsys):
    main(["--seed", "42", "--auto"])
    plain = capsys.readouterr().out
    main(["--seed", "42", "--auto", "--debug"])
    with_debug = capsys.readouterr().out
    assert with_debug == plain


# --- entrypoint purity: it forwards, it does not compute ----------------


def test_entrypoint_forwards_to_adapter_without_logic(monkeypatch, capsys):
    captured = {}

    def fake_run(*, seed, auto, script_lines, writer):
        captured.update(seed=seed, auto=auto, script_lines=script_lines)
        return SimpleNamespace(lives=[], ending=None)

    monkeypatch.setattr(adapter, "run", fake_run)
    rc = main(["--seed", "7", "--auto"])

    assert rc == 0
    assert captured == {"seed": 7, "auto": True, "script_lines": None}
    # the CLI itself writes nothing to stdout; the adapter owns the transcript
    assert capsys.readouterr().out == ""


def test_entrypoint_passes_script_lines_from_file(monkeypatch, tmp_path):
    script = tmp_path / "plays.txt"
    script.write_text("1\n0\n2\n", encoding="utf-8")
    captured = {}

    def fake_run(*, seed, auto, script_lines, writer):
        captured.update(script_lines=script_lines)
        return SimpleNamespace(lives=[], ending=None)

    monkeypatch.setattr(adapter, "run", fake_run)
    main(["--seed", "1", "--script", str(script)])
    assert captured["script_lines"] == ["1", "0", "2"]
