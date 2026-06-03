"""Player powers (section A). All powers are causal-seed/causality injectors, so
strength converts into a mark on history.

Manifest is an amplifier, not a generator: it applies a bounded multiplier to an
EXISTING seed/heritage/wildcard/theme channel and never creates a CausalNode,
preserving graph integrity (R1).
"""

from __future__ import annotations

from .enums import ManifestTargetKind, MemoryType, ThemeAxis
from .memory import form_memory
from .models import Life, ManifestEffect, Memory, World

IMPRINT_INTENSITY = 95
IMPRINT_DECAY = 0.01  # low decay: an imprinted memory persists
MANIFEST_MULT_MIN = 1.0
MANIFEST_MULT_MAX = 3.0


def _clamp_mult(value: float) -> float:
    return max(MANIFEST_MULT_MIN, min(MANIFEST_MULT_MAX, value))


def imprint(
    world: World,
    life: Life,
    npc_id: str,
    mtype: MemoryType = MemoryType.EDUCATED,
    valence: int = 60,
) -> Memory:
    """Leave a strong, low-decay memory on an NPC (steers future behavior)."""
    if not world.player.powers.imprint_enabled:
        raise PermissionError("imprint power is disabled")
    return form_memory(
        world,
        subject_id=npc_id,
        actor_id=life.player_id,
        mtype=mtype,
        valence=valence,
        intensity=IMPRINT_INTENSITY,
        decay_rate=IMPRINT_DECAY,
    )


def foresight(world: World) -> dict:
    """Reveal the current theme and the player's not-yet-fired seeds (section A-1)."""
    if not world.player.powers.foresight_enabled:
        raise PermissionError("foresight power is disabled")
    pending = [
        s.id for s in world.seeds if not s.fired and s.planted_by_life_id is not None
    ]
    return {
        "theme_axes": dict(world.theme.axes),
        "dominant": world.theme.dominant,
        "pending_seeds": pending,
    }


def manifest_amplify(world: World, effect: ManifestEffect) -> ManifestEffect:
    """Spend a Manifest charge to amplify existing causality (bounded)."""
    if world.player.powers.manifest_charges <= 0:
        raise ValueError("no manifest charges remaining")
    world.player.powers.manifest_charges -= 1

    if effect.target_kind == ManifestTargetKind.SEED:
        seed = next((s for s in world.seeds if s.id == effect.target_id), None)
        if seed is not None:
            seed.magnitude = min(
                100, round(seed.magnitude * _clamp_mult(effect.weight_mult))
            )
            seed.maturation_time = max(
                0, seed.maturation_time + effect.maturation_delta
            )

    elif effect.target_kind == ManifestTargetKind.HERITAGE:
        h = next((h for h in world.heritage if h.id == effect.target_id), None)
        if h is not None:
            h.heritage_score = round(
                h.heritage_score * _clamp_mult(effect.heritage_growth_mult)
            )

    elif effect.target_kind == ManifestTargetKind.WILDCARD:
        wc = next(
            (w for w in world.wildcards.wildcards if w.id == effect.target_id), None
        )
        if wc is not None:
            mult = _clamp_mult(effect.trajectory_influence_mult)
            wc.impact_vector = {
                axis: round(value * mult) for axis, value in wc.impact_vector.items()
            }

    elif effect.target_kind == ManifestTargetKind.THEME_AXIS:
        axis = ThemeAxis(effect.target_id)
        push = round((_clamp_mult(effect.weight_mult) - 1.0) * 20)
        world.theme.axes[axis] = max(0, min(100, world.theme.axes.get(axis, 0) + push))

    return effect
