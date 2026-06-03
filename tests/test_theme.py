"""World Theme computation and snapshots (section C)."""

from __future__ import annotations

from chronicle_forge import compute_theme, generate_world
from chronicle_forge.enums import ThemeAxis, WildCardStatus


def test_axes_clamped_and_dominant_set():
    world = generate_world(seed=5)
    theme = compute_theme(world)
    assert set(theme.axes) == set(ThemeAxis)
    assert all(0 <= v <= 100 for v in theme.axes.values())
    assert theme.dominant is not None


def test_snapshot_appended_with_year():
    world = generate_world(seed=5)
    world.current_year = 12
    compute_theme(world)
    assert len(world.theme.history) == 1
    snap = world.theme.history[0]
    assert snap.year == 12
    assert snap.dominant is not None
    assert snap.axes == world.theme.axes


def test_ignited_wildcard_pushes_its_axis():
    world = generate_world(seed=5)
    before = compute_theme(world).axes[ThemeAxis.INNOVATION]
    wc = world.wildcards.wildcards[0]
    wc.status = WildCardStatus.IGNITED  # impact_vector pushes INNOVATION
    after = compute_theme(world).axes[ThemeAxis.INNOVATION]
    assert after > before
