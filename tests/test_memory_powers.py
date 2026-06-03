"""Memory formation (7.1) and player powers (section A)."""

from __future__ import annotations

import pytest

from chronicle_forge import (
    begin_life,
    foresight,
    form_memory,
    generate_world,
    imprint,
    manifest_amplify,
    perform_activity,
)
from chronicle_forge.enums import (
    ActivityCategory,
    ManifestTargetKind,
    MemoryType,
    SeedDomain,
)
from chronicle_forge.models import CausalSeed, ManifestEffect


def test_form_memory_updates_relation():
    world = generate_world(seed=2)
    life = begin_life(world)
    npc = world.npcs[0]
    form_memory(
        world, npc.id, life.player_id, MemoryType.BETRAYED, valence=-60, intensity=80
    )
    rel = npc.relations[life.player_id]
    assert rel.affinity < 0
    assert rel.fear > 0


def test_imprint_is_strong_and_low_decay():
    world = generate_world(seed=2)
    life = begin_life(world)
    npc = world.npcs[0]
    mem = imprint(world, life, npc.id)
    assert mem.intensity >= 90
    assert mem.decay_rate < 0.05


def test_foresight_lists_pending_player_seeds():
    world = generate_world(seed=2)
    life = begin_life(world)
    perform_activity(world, life, ActivityCategory.RESEARCH)
    view = foresight(world)
    assert len(view["pending_seeds"]) == 1
    assert view["dominant"] is not None


def test_manifest_amplifies_seed_and_spends_charge():
    world = generate_world(seed=2)
    world.seeds.append(CausalSeed(id="seed-a", domain=SeedDomain.ECONOMY, magnitude=40))
    assert world.player.powers.manifest_charges == 1

    manifest_amplify(
        world,
        ManifestEffect(
            target_kind=ManifestTargetKind.SEED, target_id="seed-a", weight_mult=2.0
        ),
    )
    assert world.seeds[0].magnitude == 80
    assert world.player.powers.manifest_charges == 0


def test_manifest_multiplier_is_clamped():
    world = generate_world(seed=2)
    world.seeds.append(CausalSeed(id="seed-a", domain=SeedDomain.ECONOMY, magnitude=40))
    manifest_amplify(
        world,
        ManifestEffect(
            target_kind=ManifestTargetKind.SEED, target_id="seed-a", weight_mult=10.0
        ),
    )
    assert world.seeds[0].magnitude == 100  # 40 * clamp(10 -> 3) = 120 -> capped 100


def test_manifest_without_charges_raises():
    world = generate_world(seed=2)
    world.player.powers.manifest_charges = 0
    with pytest.raises(ValueError):
        manifest_amplify(
            world,
            ManifestEffect(
                target_kind=ManifestTargetKind.THEME_AXIS, target_id="warfare"
            ),
        )
