"""Deterministic randomness and id generation.

Reproducibility is a hard requirement (R3, section 11): a world's seed plus the
action log must fully reconstruct its history. Every stochastic decision must go
through :class:`DeterministicRNG`, and every entity id through :class:`IdFactory`,
so that the same seed always yields a byte-identical world.
"""

from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class DeterministicRNG:
    """A thin wrapper over ``random.Random`` seeded by an integer.

    CPython's Mersenne Twister is deterministic for a given integer seed across
    processes and platforms, which is what we rely on for reproducible worlds.
    """

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def random(self) -> float:
        return self._rng.random()

    def choice(self, seq: Sequence[T]) -> T:
        return self._rng.choice(seq)

    def shuffle(self, seq: list) -> None:
        self._rng.shuffle(seq)


class IdFactory:
    """Generates stable, sequential ids of the form ``prefix-0000``.

    Using counters (not random UUIDs) keeps serialized worlds identical across
    runs for the same seed.
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def next(self, prefix: str) -> str:
        index = self._counters.get(prefix, 0)
        self._counters[prefix] = index + 1
        return f"{prefix}-{index:04d}"
