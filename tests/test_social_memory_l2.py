"""P11-B Social Memory L2 contract — the locked design, integrated.

L2 makes the world *act on* a soul's cross-life bonds (NPCs steered by their
``relations[player_id]``) and *decay* its memories over the time-skip, gated off
by default. The single source of truth for the spec is
``docs/research/p11b_social_memory_l2.md`` -> "L2 Specification (locked)" (S1-S5).

Integration (REWORK): the flag is a transient argument on the *existing* entry
points — ``simulate_world(..., social_memory=...)`` and, via
``Recipe.social_memory``, the replay path — not a separate ``simulate_world_l2``.
Decay runs per skip-year inside ``time_skip``; ``relation_bias`` is consumed in
``opportunity.npc_signals``. Determinism contract: integer-only decay state, no
float in stored state, no new RNG, off-path byte-identical, on-path reproducible.
"""

from __future__ import annotations

import hashlib

from chronicle_forge import config
from chronicle_forge import social_memory_l2 as l2
from chronicle_forge.autoplay import simulate_world
from chronicle_forge.opportunity import Indexes, build_indexes, npc_signals
from chronicle_forge.persistence.load import load_recipe, replay_recipe
from chronicle_forge.persistence.save import build_recipe, read_recipe, save_recipe
from chronicle_forge.persistence.schema import Recipe
from chronicle_forge.reporting.observatory import observatory
from chronicle_forge.reporting.social_memory import social_memory_view
from chronicle_forge.reporting.world_model import world_model_json

MAX_YEAR = config.DEV_WORLD_MAX_YEARS

# Frozen off-path goldens (must stay identical when the flag is OFF).
GOLDEN_WORLD_SHA = "e62d8f2cd24d2c72"
GOLDEN_OBSERVATORY_SHA = "f9ad13c75c88a9c2"
GOLDEN_SOCIAL_MEMORY_SHA = "3fbb1aa02071dfe2"
GOLDEN_WORLD_MODEL_SHA = "5b41a692cfa3f1ce"

# The one new golden: seed42 opportunity world with social_memory ON, produced by
# the integrated S1 pipeline (per-year decay + npc_signals relation-bias).
GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA = "0eb1d217a2b8e144"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _world_sha(world) -> str:
    return _sha(world.model_dump_json())


def _on():
    return simulate_world(42, mode="opportunity", social_memory=True)


def _off():
    return simulate_world(42, mode="opportunity", social_memory=False)


# --- S2: integer decay (float-free) -------------------------------------


def test_decay_step_is_ceiling_integer():
    assert l2.decay_step(100, 1, 20) == 5
    assert l2.decay_step(19, 1, 20) == 1  # ceil: a non-zero value always loses >= 1
    assert l2.decay_step(1, 1, 20) == 1
    assert l2.decay_step(0, 1, 20) == 0
    assert isinstance(l2.decay_step(37, 1, 20), int)


def test_decay_intensity_floors_at_zero_and_returns_int():
    assert l2.decay_intensity(100, 1, 20) == 95
    assert l2.decay_intensity(1, 1, 20) == 0
    assert l2.decay_intensity(0, 1, 20) == 0
    assert isinstance(l2.decay_intensity(80, 1, 20), int)


def test_decay_relation_value_is_sign_preserving():
    assert l2.decay_relation_value(-100, 1, 20) == -95
    assert l2.decay_relation_value(100, 1, 20) == 95
    assert l2.decay_relation_value(0, 1, 20) == 0
    assert isinstance(l2.decay_relation_value(-40, 1, 20), int)


def test_decay_is_float_free_pure_int():
    intensity = 100
    prev = intensity + 1
    for _ in range(500):  # decays to 0 and stays there, always an int
        intensity = l2.decay_intensity(intensity, 1, 20)
        assert isinstance(intensity, int)
        assert 0 <= intensity < prev or intensity == 0
        prev = intensity if intensity > 0 else prev
    assert intensity == 0


# --- S3: bounded behavior bias ------------------------------------------


def test_relation_bias_is_bounded_by_max_bias():
    for a in range(-100, 101, 20):
        for f in range(-100, 101, 20):
            assert abs(l2.relation_bias(a, f)) <= l2.MAX_BIAS + 1e-9


def test_relation_bias_sign():
    assert l2.relation_bias(100, 0) > 0  # love lifts
    assert l2.relation_bias(0, 100) < 0  # fear suppresses
    assert l2.relation_bias(0, 0) == 0  # neutral


def test_relation_bias_constants_locked():
    assert l2.MAX_BIAS == 0.15
    assert l2.W_AFF == 0.6
    assert l2.W_FEAR == 0.4
    assert l2.MEMORY_ACTIVE_MIN == 20


# --- S3 wiring: relation_bias is actually consumed (not dead code) -------


def test_relation_bias_is_wired_into_npc_signals():
    """A soul-relation moves an NPC's Delta with the flag ON; proves npc_signals
    consumes relation_bias rather than ignoring it (no dead code)."""
    world = _off()  # a finished world that holds soul-relations
    idx: Indexes = build_indexes(world)
    moved = False
    for npc in world.npcs:
        rel = npc.relations.get(world.player.id)
        if rel is None:
            continue
        base = npc_signals(npc, world, idx, social_memory=False).delta
        on = npc_signals(npc, world, idx, social_memory=True).delta
        if base != on:
            moved = True
            bias = l2.relation_bias(rel.affinity, rel.fear)
            # fear-dominant relations suppress, affinity-dominant relations lift
            assert (bias < 0) == (on < base) or bias == 0
    assert moved, "expected at least one soul-relation to bias an NPC's Delta"


# --- S1 / S4 / off-path: determinism & goldens --------------------------


def test_offpath_world_is_byte_identical():
    base = simulate_world(42, mode="opportunity").model_dump_json()
    assert _off().model_dump_json() == base


def test_offpath_world_hash_is_frozen_golden():
    assert _world_sha(_off()) == GOLDEN_WORLD_SHA


def test_offpath_leaves_existing_goldens():
    off = _off()
    assert _sha(observatory(off)) == GOLDEN_OBSERVATORY_SHA
    assert _sha(social_memory_view(off)) == GOLDEN_SOCIAL_MEMORY_SHA
    assert _sha(world_model_json(off)) == GOLDEN_WORLD_MODEL_SHA


def test_onpath_world_differs_from_offpath():
    assert _world_sha(_on()) != _world_sha(_off())


def test_onpath_world_hash_is_frozen_golden():
    assert _world_sha(_on()) == GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA


def test_onpath_is_deterministic_double_run():
    assert _on().model_dump_json() == _on().model_dump_json()


def test_onpath_state_is_integer_only():
    on = _on()
    for m in on.memories:
        assert isinstance(m.intensity, int)
    for npc in on.npcs:
        for rel in npc.relations.values():
            assert isinstance(rel.affinity, int)
            assert isinstance(rel.trust, int)
            assert isinstance(rel.fear, int)


# --- requirement #2: Recipe save/load/replay preserve the flag -----------


def test_recipe_defaults_social_memory_false():
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    assert r.social_memory is False


def test_legacy_recipe_without_field_loads_off():
    """A recipe persisted before the field existed loads as False (a missing
    defaulted field is tolerated) and replays to the frozen off-path world."""
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    legacy = Recipe.model_validate_json(r.model_dump_json(exclude={"social_memory"}))
    assert legacy.social_memory is False
    assert _world_sha(replay_recipe(legacy)) == GOLDEN_WORLD_SHA


def test_recipe_roundtrip_preserves_flag(tmp_path):
    r = build_recipe(
        seed=42, max_year=MAX_YEAR, mode="auto", inputs=[], social_memory=True
    )
    p = tmp_path / "on.json"
    save_recipe(r, p)
    assert read_recipe(p).social_memory is True
    assert _world_sha(load_recipe(p)) == GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA


def test_replay_offpath_matches_world_golden():
    r = build_recipe(seed=42, max_year=MAX_YEAR, mode="auto", inputs=[])
    assert _world_sha(replay_recipe(r)) == GOLDEN_WORLD_SHA


def test_replay_onpath_matches_simulate_world():
    r = build_recipe(
        seed=42, max_year=MAX_YEAR, mode="auto", inputs=[], social_memory=True
    )
    assert _world_sha(replay_recipe(r)) == GOLDEN_SOCIAL_MEMORY_ON_WORLD_SHA
    assert replay_recipe(r).model_dump_json() == _on().model_dump_json()
