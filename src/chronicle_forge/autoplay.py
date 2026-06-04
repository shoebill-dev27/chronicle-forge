"""Deterministic auto-player to drive a whole world for observability (P5).

There is no human in the loop here, so a scripted agent makes choices via the
seed-derived RNG. This exists to exercise and *inspect* the simulation end to
end; it is not the game's intelligence. ``simulate_world(seed)`` is reproducible:
the same seed yields an identical finished world.
"""

from __future__ import annotations

from .discovery import explore_dungeon
from .ending import classify_ending
from .enums import ActivityCategory, DeathCause, DiscoveryType, LocationType, Talent
from .life import begin_life, end_life, lifespan_reached
from .macro import derive_rng, time_skip
from .models import Life, World
from .powers import imprint
from .profiles import ACTIVITY_PROFILES
from .rng import DeterministicRNG
from .worldgen import generate_world

_AUTOPLAY_SALT = 99
_TARGETED = {
    ActivityCategory.EDUCATION,
    ActivityCategory.POLITICS,
    ActivityCategory.RELIGION,
}

# talent -> the activity it is best at (inverse of profile.talent_affinity)
_TALENT_ACTIVITY = {
    profile.talent_affinity: cat for cat, profile in ACTIVITY_PROFILES.items()
}


def _pick_activity(rng: DeterministicRNG, talent: Talent) -> ActivityCategory:
    if rng.random() < 0.6 and talent in _TALENT_ACTIVITY:
        return _TALENT_ACTIVITY[talent]
    return rng.choice(list(ActivityCategory))


def _live_one(world: World, rng: DeterministicRNG) -> Life:
    talent = rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    dungeon = next(
        (loc for loc in world.locations if loc.type == LocationType.DUNGEON), None
    )

    n_actions = rng.randint(8, 18)
    for _ in range(n_actions):
        if world.current_year >= world.max_year or lifespan_reached(life):
            break
        roll = rng.random()
        if dungeon is not None and roll < 0.15:
            explore_dungeon(world, life, dungeon.id, rng.choice(list(DiscoveryType)))
        else:
            category = _pick_activity(rng, talent)
            target = None
            if category in _TARGETED:
                living = [n for n in world.npcs if n.alive] or world.npcs
                target = rng.choice(living).id
            from .activity import perform_activity  # local import avoids cycle

            perform_activity(world, life, category, target_id=target)
        if roll > 0.92:
            npc = rng.choice(world.npcs)
            if npc.alive:
                imprint(world, life, npc.id)

    cause = DeathCause.LIFESPAN if lifespan_reached(life) else DeathCause.CHOICE
    end_life(world, life, cause)
    return life


def simulate_world(seed: int, life_cap: int = 40) -> World:
    """Run a world from generation to its max year and return the finished world."""
    world = generate_world(seed)
    while world.current_year < world.max_year and len(world.lives) < life_cap:
        rng = derive_rng(world, len(world.lives), salt=_AUTOPLAY_SALT)
        life = _live_one(world, rng)
        skip = time_skip(world, life)
        if skip["world_ended"]:
            break
    classify_ending(world)
    return world


def simulate_report(seed: int) -> str:
    """Run a world and render the full developer report."""
    from .views import full_report

    return full_report(simulate_world(seed))
