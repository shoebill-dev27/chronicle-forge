"""P9-3 input recorder — capture a live play's reader stream as recipe inputs.

The reader is *injected* into ``run_human_world``, so recording needs no change
to the session: ``recording_reader`` wraps the real reader and appends each
non-EOF line it yields. Feeding the captured list back through
``scripted_reader`` reproduces the exact reader stream (re-prompted invalid
entries included, since every ``reader()`` call is captured), so a recorded play
replays byte-for-byte. EOF is not recorded; an auto/EOF play records nothing,
giving ``inputs == []``.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

Reader = Callable[[], Optional[str]]


def recording_reader(inner: Reader) -> Tuple[Reader, List[str]]:
    """Wrap ``inner`` so every non-EOF line it returns is appended to a list.
    Returns ``(reader, captured)``; ``captured`` fills as the reader is consumed
    and is the recipe's ``inputs`` once the play completes."""
    captured: List[str] = []

    def reader() -> Optional[str]:
        line = inner()
        if line is not None:
            captured.append(line)
        return line

    return reader, captured
