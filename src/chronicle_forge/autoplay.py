"""Deterministic auto-player to drive a whole world for observability (P5).

There is no human in the loop here, so a scripted agent makes choices via the
seed-derived RNG. This exists to exercise and *inspect* the simulation end to
end; it is not the game's intelligence. ``simulate_world(seed)`` is reproducible:
the same seed yields an identical finished world.
"""

from __future__ import annotations

from . import config
from .discovery import explore_dungeon
from .ending import classify_ending
from .enums import ActivityCategory, DiscoveryType, LocationType, Talent
from .life import begin_life
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

    # The clock and mortality live in advance_year, reached through each action.
    while world.current_year < world.max_year and life.alive:
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
    return life


def _live_one_opportunity(
    world: World, rng: DeterministicRNG, social_memory: bool = False
) -> Life:
    """P6 opportunity-driven life loop. Same clock and mortality as the legacy
    loop (both live in ``advance_year``); the *only* changed block is action
    choice, which flows through the Execution Layer (Opportunity -> Action).
    The legacy random ``imprint`` sprinkle is dropped here -- it was
    scripted-agent noise that would distort Omega observation.
    """
    from .execution import make_auto_chooser, play_turn  # local import avoids cycle
    from .opportunity import OpportunitySession

    talent = rng.choice(list(Talent))
    life = begin_life(world, talent=talent)

    session = OpportunitySession()
    chooser = make_auto_chooser(rng)

    while world.current_year < world.max_year and life.alive:
        play_turn(world, life, session, chooser, rng, social_memory)
    return life


def simulate_world(
    seed: int,
    life_cap: int = 60,
    mode: str = "legacy",
    social_memory: bool = False,
    max_year: int = config.WORLD_MAX_YEARS,
) -> World:
    """Run a world from generation to ``max_year`` and return the finished world.

    ``mode="legacy"`` (default) drives play with the talent policy and is
    byte-identical to prior behavior (golden seed42 artifacts, P5 determinism).
    ``mode="opportunity"`` drives play through the P6 Execution Layer instead.

    ``social_memory`` (P11-B L2, opportunity mode only) gates the cross-life
    pipeline: each time-skip decays the soul's memories/relations and the next
    life's opportunity scoring is biased by the surviving bonds. Off (default),
    not one L2 branch runs and the world is byte-identical to today. The flag is
    a transient run argument and is never stored in ``World``.
    """
    world = generate_world(seed, max_year=max_year)
    while world.current_year < world.max_year and len(world.lives) < life_cap:
        if mode == "legacy":
            rng = derive_rng(world, len(world.lives), salt=_AUTOPLAY_SALT)
            life = _live_one(world, rng)
        else:
            from .execution import EXECUTION_SALT

            rng = derive_rng(world, len(world.lives), salt=EXECUTION_SALT)
            life = _live_one_opportunity(world, rng, social_memory)
        if life.alive:  # the horizon came first: no death, no gap
            break
        skip = time_skip(world, social_memory)
        if skip["world_ended"]:
            break
    classify_ending(world)
    return world


def simulate_report(seed: int, narrate: bool = False) -> str:
    """Run a world and render the full developer report.

    With ``narrate=True``, append the AI-generated chronicle and ending epilogue
    (deterministic template prose when no ANTHROPIC_API_KEY is set). The world
    state itself is never affected by narration.
    """
    from .views import full_report

    world = simulate_world(seed)
    report = full_report(world)
    if narrate:
        from .ai import generate_history_book, narrate_ending

        chronicle = generate_history_book(world)
        ending_text = narrate_ending(world)
        report += (
            "\n\n=== CHRONICLE (narrative) ===\n"
            + chronicle.generated_text
            + "\n\n=== ENDING ===\n"
            + ending_text
        )
    return report
