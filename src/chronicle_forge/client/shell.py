"""pywebview shell — launches the Living Chronicle book window (ADR-002).

``webview`` is imported lazily inside :func:`launch` so importing the client
package (and running its unit tests) needs no GUI backend. On a headless machine
the import or ``start`` fails loudly; that is expected — the window is the
owner's 7/27 go/no-go evidence, run on a desktop.
"""

from __future__ import annotations

from pathlib import Path

from .bridge import BookBridge


def _index_html() -> str:
    return str(Path(__file__).with_name("web") / "index.html")


def launch(seed: int = 1) -> None:
    """Open the book window bound to a fresh :class:`BookBridge`."""
    import webview  # lazy: no GUI dependency at import time

    api = BookBridge(seed=seed)
    webview.create_window(
        "Chronicle Forge — The Living Chronicle",
        url=_index_html(),
        js_api=api,
        # The supported viewport. A leaf has to hold the longest in-spec page
        # (a five-option juncture plus a reveal) at a readable size without
        # scrolling; at the old 1024x720 that page only fitted by shrinking the
        # type to the legibility floor. `min_size` keeps the guarantee when the
        # window is resized.
        width=1180,
        height=880,
        min_size=(940, 760),
        text_select=False,
    )
    webview.start()
