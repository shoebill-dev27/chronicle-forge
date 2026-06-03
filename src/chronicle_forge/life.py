"""Life lifecycle: reincarnation, aging, death, and the LifeSummary (section 4).

Aging uses two-resolution time (section 4.3): action-time turns accumulate, and
every ``TURNS_PER_YEAR`` turns advance one world year, age the player, and take a
World Theme snapshot. Death produces a LifeSummary consumed by personal history,
inheritance, and ending generation.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from . import config
from .enums import DeathCause, LocationType, Talent
from .ids import next_id
from .models import Life, LifeSummary, World
from .theme import SEED_DOMAIN_TO_THEME, compute_theme

START_AGE = 16  # the reincarnator begins each life as a young adult
TURNS_PER_YEAR = 4


def begin_life(
    world: World, talent: Optional[Talent] = None, birth_age: int = START_AGE
) -> Life:
    """Reincarnate: start a new life in the (continuing) world."""
    life = Life(
        id=next_id("life", world.lives),
        player_id=world.player.id,
        birth_year=world.current_year,
        age=birth_age,
        talent=talent,
    )
    world.lives.append(life)
    world.player.current_life_id = life.id
    return life


def advance_time(world: World, life: Life, turns: int = 1) -> None:
    """Consume action-time turns, aging the player and the world accordingly."""
    for _ in range(turns):
        life.turns += 1
        if life.turns % TURNS_PER_YEAR == 0:
            life.age += 1
            world.current_year += 1
            compute_theme(world)  # per-year theme snapshot


def lifespan_reached(life: Life) -> bool:
    return life.age >= config.LIFESPAN_CAP


def build_life_summary(world: World, life: Life) -> LifeSummary:
    my_seeds = [s for s in world.seeds if s.planted_by_life_id == life.id]
    seed_ids = [s.id for s in my_seeds]
    seed_id_set = set(seed_ids)

    heritage_ids = [h.id for h in world.heritage if h.seed_id in seed_id_set]

    notable: list[str] = []
    for node in world.causal_nodes:
        if any(edge.from_id in seed_id_set for edge in node.caused_by):
            notable.append(node.id)

    axis_counts = Counter(SEED_DOMAIN_TO_THEME[s.domain] for s in my_seeds)
    dominant = axis_counts.most_common(1)[0][0] if axis_counts else world.theme.dominant

    village = next(
        (loc for loc in world.locations if loc.type == LocationType.VILLAGE), None
    )
    place = village.name if village else "the world"
    label = (
        life.talent.value
        if life.talent
        else (dominant.value if dominant else "wanderer")
    )
    title = f"The {label.capitalize()} of {place}"

    return LifeSummary(
        life_id=life.id,
        title=title,
        dominant_axis=dominant,
        seeds_created=seed_ids,
        heritage_created=heritage_ids,
        notable_events=notable,
    )


def _apply_bequest(world: World, life: Life) -> None:
    """Carry a title forward to the next life (Bequest power, section A-1)."""
    if not world.player.powers.bequest_enabled or life.summary is None:
        return
    title = life.summary.title
    if title and title not in world.player.inherited.titles:
        world.player.inherited.titles.append(title)


def end_life(
    world: World, life: Life, cause: DeathCause = DeathCause.LIFESPAN
) -> LifeSummary:
    """Finalize a life: record death, build the summary, and apply inheritance.

    The post-death world time-skip and history generation are P3 (macro loop);
    this function ends the micro loop and prepares the hand-off.
    """
    life.death_year = world.current_year
    life.age_at_death = life.age
    life.death_cause = cause
    life.summary = build_life_summary(world, life)
    _apply_bequest(world, life)
    world.player.current_life_id = None
    return life.summary
