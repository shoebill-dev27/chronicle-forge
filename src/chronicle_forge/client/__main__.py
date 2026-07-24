"""``python -m chronicle_forge.client [seed]`` — open the book (I-1 skeleton)."""

from __future__ import annotations

import sys

from .shell import launch

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    launch(seed=seed)
