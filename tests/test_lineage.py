"""P9-4 Lineage Viewer contract — test-first (RED until reporting/lineage.py).

A read-only projection of a finished world into the chain of reincarnations and
the heritage left behind. It mutates nothing, leaks no internal ids (the P8
lesson), and is deterministic. Nothing here changes the world, P6/P7/P8/P9-* or
the seed42 golden.
"""

from __future__ import annotations

import re

import pytest

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.reporting._data import heritage_rows
from chronicle_forge.reporting.lineage import lineage_view


def _world():
    return simulate_world(42, mode="opportunity")


_SPINE = re.compile(r"(?m)^## Life (\d+)\b")
_INTERNAL_ID = re.compile(r"\b(seed|life|npc|node|loc|fac|her)-\d")


# --- spine: every life, in birth order ----------------------------------


def test_lineage_lists_every_life_in_birth_order():
    world = _world()
    spine = [int(m) for m in _SPINE.findall(lineage_view(world))]
    assert spine == list(range(1, len(world.lives) + 1))


def test_lineage_attributes_founded_heritage():
    world = _world()
    out = lineage_view(world)
    names = [r["name"] for r in heritage_rows(world)]
    assert names, "expected the seed42 world to have heritage"
    for name in names:
        assert name in out, name


# --- the P8 lesson: no internal ids -------------------------------------


def test_lineage_no_internal_ids():
    out = lineage_view(_world())
    assert not _INTERNAL_ID.search(out), out
    assert "legacy:" not in out


# --- read-only & deterministic ------------------------------------------


def test_lineage_is_read_only():
    world = _world()
    before = world.model_dump_json()
    lineage_view(world)
    assert world.model_dump_json() == before


def test_lineage_is_deterministic():
    world = _world()
    assert lineage_view(world) == lineage_view(world)


def test_lineage_is_markdown_readable():
    assert lineage_view(_world()).lstrip().startswith("#")


# --- selectable display order -------------------------------------------


def test_lineage_order_modes_accepted_and_complete():
    world = _world()
    all_lives = set(range(1, len(world.lives) + 1))
    for order in ("chronological", "impact", "generation"):
        out = lineage_view(world, order=order)
        spine = {int(m) for m in _SPINE.findall(out)}
        assert spine == all_lives, order  # every life present in every order
        assert out == lineage_view(world, order=order)  # deterministic


def test_lineage_default_order_is_chronological():
    world = _world()
    assert lineage_view(world) == lineage_view(world, order="chronological")


def test_lineage_rejects_unknown_order():
    with pytest.raises(ValueError):
        lineage_view(_world(), order="random")
