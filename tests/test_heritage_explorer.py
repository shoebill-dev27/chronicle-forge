"""P9-5 Heritage Explorer contract — test-first (RED until
reporting/heritage_explorer.py).

A read-only, player-facing catalogue of what endured: every heritage by
significance, with selectable sort / grouping and a "still shaping the world"
mark for legacies aligned with the final theme. It mutates nothing, leaks no
internal id (the P8/P9-4 lesson), and is deterministic. Nothing here changes the
world, P6/P7/P8/P9-* or the seed42 golden.
"""

from __future__ import annotations

import re

import pytest

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.reporting._data import heritage_rows, seed_by_id
from chronicle_forge.reporting.heritage_explorer import heritage_explorer
from chronicle_forge.theme import SEED_DOMAIN_TO_THEME


def _world():
    return simulate_world(42, mode="opportunity")


_ENTRY = re.compile(r"(?m)^- \*\*(.+?)\*\*")
_INTERNAL_ID = re.compile(r"\b(seed|life|npc|node|loc|fac|her)-\d")


def _names(out: str):
    return _ENTRY.findall(out)


# --- completeness & default sort ----------------------------------------


def test_explorer_lists_every_heritage():
    world = _world()
    out = heritage_explorer(world)
    for row in heritage_rows(world):
        assert row["name"] in out, row["name"]


def test_explorer_default_sort_is_score():
    world = _world()
    names = _names(heritage_explorer(world))
    expected = [r["name"] for r in heritage_rows(world)]  # -score, source_seed
    assert names == expected


# --- selectable sort ----------------------------------------------------


def test_explorer_sort_longevity_matches_expected_sequence():
    world = _world()
    names = _names(heritage_explorer(world, sort="longevity"))
    expected = [
        r["name"]
        for r in sorted(
            heritage_rows(world), key=lambda r: (-r["longevity"], r["source_seed"])
        )
    ]
    assert names == expected


def test_explorer_sort_reach_matches_expected_sequence():
    world = _world()
    names = _names(heritage_explorer(world, sort="reach"))
    expected = [
        r["name"]
        for r in sorted(
            heritage_rows(world), key=lambda r: (-r["reach"], r["source_seed"])
        )
    ]
    assert names == expected


def test_explorer_sort_modes_accepted_and_complete():
    world = _world()
    count = len(heritage_rows(world))
    for sort in ("score", "longevity", "reach", "origin"):
        out = heritage_explorer(world, sort=sort)
        assert len(_names(out)) == count, sort
        assert out == heritage_explorer(world, sort=sort)  # deterministic


# --- grouping -----------------------------------------------------------


def test_explorer_group_by_type_complete_with_headers():
    world = _world()
    out = heritage_explorer(world, group_by="type")
    assert sorted(_names(out)) == sorted(r["name"] for r in heritage_rows(world))
    assert re.search(r"(?m)^### ", out)  # group headers present
    assert out == heritage_explorer(world, group_by="type")  # deterministic


def test_explorer_group_by_founder_complete():
    world = _world()
    out = heritage_explorer(world, group_by="founder")
    assert sorted(_names(out)) == sorted(r["name"] for r in heritage_rows(world))
    assert out == heritage_explorer(world, group_by="founder")


# --- still shaping the world (theme alignment) --------------------------


def test_explorer_living_status_matches_theme_alignment():
    world = _world()
    out = heritage_explorer(world)
    dominant = world.theme.dominant
    alive_exists = False
    for h in world.heritage:
        seed = seed_by_id(world, h.seed_id)
        axis = SEED_DOMAIN_TO_THEME.get(seed.domain) if seed else None
        if axis is not None and axis == dominant:
            alive_exists = True
    assert ("still shaping the world" in out) == alive_exists


# --- no internal ids, read-only, deterministic, markdown ----------------


def test_explorer_no_internal_ids():
    out = heritage_explorer(_world())
    assert not _INTERNAL_ID.search(out), out
    assert "legacy:" not in out


def test_explorer_is_read_only():
    world = _world()
    before = world.model_dump_json()
    heritage_explorer(world)
    assert world.model_dump_json() == before


def test_explorer_is_deterministic():
    world = _world()
    assert heritage_explorer(world) == heritage_explorer(world)


def test_explorer_is_markdown():
    assert heritage_explorer(_world()).lstrip().startswith("#")


def test_explorer_rejects_unknown_sort():
    with pytest.raises(ValueError):
        heritage_explorer(_world(), sort="bogus")


def test_explorer_rejects_unknown_group_by():
    with pytest.raises(ValueError):
        heritage_explorer(_world(), group_by="bogus")
