"""Deterministic runtime id allocation.

Entities created during play (seeds, memories, discoveries, lives, nodes) get
sequential ids derived from the length of their collection, so a fixed sequence
of actions yields stable ids (reproducibility, R3).
"""

from __future__ import annotations

from typing import Sized


def next_id(prefix: str, collection: Sized) -> str:
    return f"{prefix}-{len(collection):04d}"
