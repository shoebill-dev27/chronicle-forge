"""The Living Chronicle desktop client (ADR-002) — I-1 walking skeleton.

Importing this package pulls in NO GUI toolkit; call :func:`launch` (which
imports ``webview`` lazily) to open the window, or use :class:`BookBridge`
directly for headless/unit use.
"""

from .bridge import BookBridge, capture_first_juncture
from .shell import launch

__all__ = ["BookBridge", "capture_first_juncture", "launch"]
