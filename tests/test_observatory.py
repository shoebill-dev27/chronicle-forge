"""P10 Observatory contract — test-first (RED until reporting/observatory.py).

The Observatory is a read-only aggregation layer: it composes the player-safe
projections that already exist (lineage P9-4, heritage P9-5) plus thin id-free
overview/theme renders into one navigable Markdown surface. It mutates nothing,
leaks no internal id (the P8 / P9-4 lesson), is deterministic, and never reuses
the dev-facing, id-leaky views.py. Nothing here changes the world, P6/P7/P8/P9-*
or the seed42 golden.
"""

from __future__ import annotations

import hashlib
import re

import pytest

from chronicle_forge.autoplay import simulate_world
from chronicle_forge.reporting._data import heritage_rows
from chronicle_forge.reporting.observatory import observatory

MVP_SECTIONS = ("Overview", "Lineage", "Heritage", "Theme")

# Frozen at GREEN: the Observatory's permanent seed42 regression guard (mirroring
# P9). simulate_world(42, "opportunity") -> observatory() default render.
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"

_H2 = re.compile(r"(?m)^## (.+?)\s*$")
_INTERNAL_ID = re.compile(r"\b(seed|life|npc|node|loc|fac|her)-\d")


def _world():
    return simulate_world(42, mode="opportunity")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# --- shape: markdown, read-only, deterministic, id-free -----------------


def test_observatory_is_markdown():
    assert observatory(_world()).lstrip().startswith("#")


def test_observatory_is_read_only():
    world = _world()
    before = world.model_dump_json()
    observatory(world)
    assert world.model_dump_json() == before


def test_observatory_is_deterministic():
    world = _world()
    assert observatory(world) == observatory(world)


def test_observatory_no_internal_ids():
    out = observatory(_world())
    assert not _INTERNAL_ID.search(out), out
    assert "legacy:" not in out


# --- MVP sections: presence and fixed order -----------------------------


def test_observatory_default_includes_mvp_sections():
    titles = set(_H2.findall(observatory(_world())))
    for section in MVP_SECTIONS:
        assert section in titles, section


def test_observatory_sections_in_fixed_order():
    out = observatory(_world())
    positions = [out.index(f"## {section}") for section in MVP_SECTIONS]
    assert positions == sorted(positions)


# --- content: every aspect is surfaced ----------------------------------


def test_observatory_surfaces_every_heritage():
    world = _world()
    out = observatory(world)
    for row in heritage_rows(world):
        assert row["name"] in out, row["name"]


def test_observatory_surfaces_every_life():
    world = _world()
    out = observatory(world)
    for ordinal in range(1, len(world.lives) + 1):
        assert f"Life {ordinal}" in out, ordinal


def test_observatory_theme_shows_dominant():
    world = _world()
    dominant = world.theme.dominant
    assert dominant is not None, "expected the seed42 world to have a dominant theme"
    assert dominant.value in observatory(world)


def test_observatory_overview_shows_scope():
    world = _world()
    out = observatory(world)
    assert str(world.current_year) in out
    assert str(len(world.lives)) in out


# --- selection: subset and explicit ordering ----------------------------


def test_observatory_section_selection_subsets():
    out = observatory(_world(), sections=["heritage"])
    assert "## Heritage" in out
    for other in ("## Overview", "## Lineage", "## Theme"):
        assert other not in out, other


def test_observatory_section_selection_is_always_canonical_order():
    # Selection chooses *which* sections appear; order is always canonical
    # (overview -> lineage -> heritage -> theme), input order ignored.
    out = observatory(_world(), sections=["theme", "overview"])
    assert out.index("## Overview") < out.index("## Theme")


def test_observatory_rejects_unknown_section():
    with pytest.raises(ValueError):
        observatory(_world(), sections=["bogus"])


def test_observatory_rejects_empty_sections():
    with pytest.raises(ValueError):
        observatory(_world(), sections=[])


# --- frozen seed42 hash (permanent regression guard) --------------------


def test_observatory_seed42_hash_is_frozen():
    assert _sha(observatory(_world())) == GOLDEN_OBSERVATORY_SHA
