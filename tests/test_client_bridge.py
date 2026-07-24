"""I-1 walking-skeleton bridge tests.

These exercise the bridge's JSON contract WITHOUT launching a GUI, and assert the
ADR-002 isolation invariant (importing the client pulls in no webview backend, so
CI without pywebview stays green). The engine goldens are guarded by the rest of
the suite; the bridge never completes a world, so it cannot move them.
"""

import json
import sys

from chronicle_forge.client.bridge import BookBridge, capture_first_juncture


def test_capture_first_juncture_is_deterministic_and_reaches_a_juncture():
    a = capture_first_juncture(1)
    b = capture_first_juncture(1)
    assert a == b  # same seed -> byte-identical juncture (determinism intact)
    assert a["options"], "seed 1 must reach a first juncture with options"
    first = a["options"][0]
    assert {"index", "label", "kind", "why"} <= set(first)
    assert first["label"]


def test_open_juncture_shape_is_json_serialisable():
    view = BookBridge(seed=1).open_juncture()
    for key in (
        "seed",
        "place",
        "opening",
        "header",
        "options",
        "marked_index",
        "has_juncture",
    ):
        assert key in view
    assert view["has_juncture"] is True
    assert view["place"] and view["place"] in view["opening"]
    assert view["marked_index"] == view["options"][0]["index"]
    json.dumps(view)  # the bridge must hand JS plain JSON


def test_open_juncture_accepts_an_explicit_seed():
    assert BookBridge().open_juncture(2)["seed"] == 2


def test_seal_and_remember_return_labelled_stubs():
    seal = BookBridge().seal(2)
    assert seal["stub"] is True and seal["sealed_index"] == 2 and seal["outcome"]
    remembered = BookBridge().remember()
    assert remembered["stub"] is True and remembered["epithet"] and remembered["hand"]


def test_importing_the_client_imports_no_gui_backend():
    # ADR-002 isolation: no GUI toolkit at import time.
    sys.modules.pop("webview", None)
    import chronicle_forge.client  # noqa: F401

    assert "webview" not in sys.modules
