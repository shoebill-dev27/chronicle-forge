"""Multi-world showcase gallery (read-only, deterministic, no AI)."""

from __future__ import annotations

from chronicle_forge import simulate_world
from chronicle_forge.reporting import (
    GALLERY_SEEDS,
    build_gallery,
    gallery_md,
    key_ending_decision,
    why_phrase,
)
from chronicle_forge.reporting.gallery import select_diverse_seeds


def test_frozen_seeds_match_derivation():
    # GALLERY_SEEDS is what the diversity selector picks over 1..40.
    assert select_diverse_seeds(scan=40, k=len(GALLERY_SEEDS)) == GALLERY_SEEDS


def test_gallery_shows_diverse_endings():
    text = gallery_md()
    # one data row per seed
    rows = [
        l
        for l in text.splitlines()
        if l.startswith("| ") and "Seed" not in l and "---" not in l
    ]
    assert len(rows) == len(GALLERY_SEEDS)
    # the whole point: the worlds differ
    endings = {simulate_world(s).ending_class for s in GALLERY_SEEDS}
    assert len(endings) >= 4
    for e in endings:
        assert e in text


def test_gallery_is_deterministic():
    assert gallery_md() == gallery_md()


def test_why_phrase_is_short_oneliner():
    for s in GALLERY_SEEDS:
        why = why_phrase(simulate_world(s))
        assert 20 <= len(why) <= 40


def test_key_decision_is_a_player_action():
    for s in GALLERY_SEEDS:
        world = simulate_world(s)
        decision = key_ending_decision(world)
        assert decision and decision != "—"
        assert decision[0].isupper()  # human-presented phrase


def test_build_gallery_writes_file(tmp_path):
    out = tmp_path / "gallery.md"
    path = build_gallery(out=str(out))
    assert out.exists()
    assert "Multi-world Showcase" in out.read_text()
    assert "distinct endings" in out.read_text()
