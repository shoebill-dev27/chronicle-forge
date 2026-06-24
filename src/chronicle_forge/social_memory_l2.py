"""P11-B Social Memory L2 — cross-life influence (flag-gated, integer-only).

Spec source: ``docs/research/p11b_social_memory_l2.md`` -> "L2 Specification
(locked)" (S1-S5), operationalized by ``docs/design_p11b_social_memory_l2.md``.

This module holds the **pure L2 primitives** the engine threads in when the
``social_memory`` flag is on:

- **S2** float-free integer decay (``decay_step`` / ``decay_intensity`` /
  ``decay_relation_value``) — no float is ever stored.
- **S3** the bounded behavior bias (``relation_bias``) and its locked constants.
- **S1** ``decay_world_one_year`` — one world-year of memory + relation decay,
  applied per skip-year inside ``macro.time_skip`` (P1 then P2).

Integration (corrected from the post-hoc draft): the decayed state is what the
**next life's opportunity scoring** reads, and ``relation_bias`` is consumed in
``opportunity.npc_signals`` — there is no separate ``simulate_world_l2`` entry.
The flag is a **transient run argument**, never stored in ``World``, so the
off-path world is byte-identical and the seed42 golden is intact by construction.
No new RNG; all decay is pure integer arithmetic.
"""

from __future__ import annotations

from .models import World

# --- S3 constants (locked) ----------------------------------------------
MAX_BIAS: float = 0.15
W_AFF: float = 0.6
W_FEAR: float = 0.4
MEMORY_ACTIVE_MIN: int = 20  # integer form of MEMORY_MIN_INTENSITY (0.20)

# Decay rates as exact rationals (float-free): 0.05 == 1/20.
MEMORY_DECAY_NUM, MEMORY_DECAY_DEN = 1, 20
RELATION_DECAY_NUM, RELATION_DECAY_DEN = 1, 20


# --- S2 integer decay (float-free) --------------------------------------
def decay_step(q: int, r_num: int, r_den: int) -> int:
    """ceil(q * r_num / r_den) via pure integer arithmetic (no float)."""
    return (q * r_num + r_den - 1) // r_den


def decay_intensity(intensity: int, r_num: int, r_den: int) -> int:
    """One year of memory-intensity decay: max(0, intensity - ceil(intensity*r))."""
    return max(0, intensity - decay_step(intensity, r_num, r_den))


def decay_relation_value(value: int, r_num: int, r_den: int) -> int:
    """Sign-preserving one-year decay of a signed relation value toward 0."""
    sign = (value > 0) - (value < 0)
    magnitude = abs(value)
    magnitude = max(0, magnitude - decay_step(magnitude, r_num, r_den))
    return sign * magnitude


# --- S3 bounded behavior bias -------------------------------------------
def relation_bias(affinity: int, fear: int) -> float:
    """Bounded opportunity-signal bias from a surviving soul-relation.

    raw = W_AFF*affinity/100 - W_FEAR*fear/100; bias = clamp(raw*MAX_BIAS, +/-MAX_BIAS).
    Transient (never stored), so it carries no new persistent-state determinism risk;
    it uses the same float-signal convention as the existing ``npc_signals`` math.
    """
    raw = W_AFF * (affinity / 100.0) - W_FEAR * (fear / 100.0)
    bias = raw * MAX_BIAS
    return max(-MAX_BIAS, min(MAX_BIAS, bias))


# --- S1 per-year decay (called inside time_skip when the flag is on) -----
def decay_world_one_year(world: World) -> None:
    """Apply one world-year of L2 decay to the soul's cross-life state.

    P1 (memory): every soul-memory's ``intensity`` decays by one year (D3).
    P2 (relation): every soul-relation's ``affinity``/``trust``/``fear`` decays
    one year toward 0 (D4). Pure integer arithmetic, no RNG. Iteration order is
    fixed (``world.memories`` list order, ``world.npcs`` list order); only the
    single ``relations[player_id]`` entry per NPC is touched, so no dict-ordering
    leaks into results.
    """
    pid = world.player.id

    # P1 — memory intensity decays one year for every soul-memory.
    for memory in world.memories:
        if memory.actor_id != pid:
            continue
        memory.intensity = decay_intensity(
            memory.intensity, MEMORY_DECAY_NUM, MEMORY_DECAY_DEN
        )

    # P2 — soul-relations fade one year toward 0.
    for npc in world.npcs:
        relation = npc.relations.get(pid)
        if relation is None:
            continue
        relation.affinity = decay_relation_value(
            relation.affinity, RELATION_DECAY_NUM, RELATION_DECAY_DEN
        )
        relation.trust = decay_relation_value(
            relation.trust, RELATION_DECAY_NUM, RELATION_DECAY_DEN
        )
        relation.fear = decay_relation_value(
            relation.fear, RELATION_DECAY_NUM, RELATION_DECAY_DEN
        )
