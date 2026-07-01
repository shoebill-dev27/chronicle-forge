"""P16 MVP Cohesion — packaging / distribution contract — RED.

The product ships as an installable console command ``chronicle-forge`` whose entry
point is ``chronicle_forge.cli:main`` (a thin wrapper over the P15 Application Layer),
with a single-sourced version. These tests pin that contract.

Each test imports ``chronicle_forge.cli`` **inside its body** so the whole file fails
with a clean ``ModuleNotFoundError`` until GREEN (the CLI module + the pyproject
``[project.scripts]`` / dynamic-version entries are added together in the P16 GREEN
issue). The in-body import gates the static pyproject assertions to that GREEN state,
keeping the existing 426-test suite untouched at collection.
"""

from __future__ import annotations

from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_text() -> str:
    return _PYPROJECT.read_text(encoding="utf-8")


def test_console_entry_target_is_callable():
    """The declared entry-point target ``chronicle_forge.cli:main`` exists and runs."""
    import chronicle_forge.cli as cli

    assert callable(cli.main)


def test_pyproject_declares_console_script():
    import chronicle_forge.cli  # noqa: F401  (gate: GREEN adds cli + the script entry)

    text = _pyproject_text()
    assert "[project.scripts]" in text
    assert 'chronicle-forge = "chronicle_forge.cli:main"' in text


def test_version_is_single_sourced():
    import chronicle_forge.cli  # noqa: F401  (gate: GREEN switches to a dynamic version)
    from chronicle_forge import __version__

    assert isinstance(__version__, str) and __version__
    text = _pyproject_text()
    # GREEN single-sources the version from chronicle_forge.__version__:
    assert 'dynamic = ["version"]' in text
    assert "chronicle_forge.__version__" in text
    # …and no longer hardcodes a quoted literal version (the dynamic attr form,
    # `version = { attr = ... }`, is the single source and is allowed).
    assert 'version = "' not in text
