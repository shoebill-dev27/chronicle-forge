"""Life lifecycle: reincarnation, aging, death, and the LifeSummary (section 4).

Chronology: a life has an actual ``birth_year`` and a ``playable_start_year``,
the world year the player took it up at ``START_AGE`` — so the first life,
taken up in year 0, was born in year -16. Age is never counted separately: it
is ``world.current_year - life.birth_year``, refreshed by the single clock
(:func:`macro.advance_year`) every ``TURNS_PER_YEAR`` action turns. Death
produces a LifeSummary consumed by personal history, inheritance, and ending
generation.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from . import config
from .enums import DeathCause, LocationType, Talent
from .ids import next_id
from .inheritance import derive_inheritance
from .models import Life, LifeSummary, World
from .theme import SEED_DOMAIN_TO_THEME

START_AGE = 16  # a playable life begins as a young adult
TURNS_PER_YEAR = 4  # action-time turns per world year (the decision cadence)


def begin_life(world: World, talent: Optional[Talent] = None) -> Life:
    """Take up a new life: a different person, aged ``START_AGE`` now, in the
    (continuing) world. They were born ``START_AGE`` years before this year —
    after a death and the ten-year gap that is six years *before* the previous
    life died, which is allowed: what moves at a death is the player's
    continuity, not a birth (docs/design_time_domain.md §4)."""
    life = Life(
        id=next_id("life", world.lives),
        player_id=world.player.id,
        birth_year=world.current_year - START_AGE,
        playable_start_year=world.current_year,
        age=START_AGE,
        talent=talent,
    )
    world.lives.append(life)
    world.player.current_life_id = life.id
    return life


def age_of(world: World, life: Life) -> int:
    """The age implied by the world clock — the only formula for age."""
    return world.current_year - life.birth_year


def advance_time(world: World, life: Life, turns: int = 1) -> None:
    """Consume action-time turns; every ``TURNS_PER_YEAR`` of them the world
    advances one year through the single clock, which ages ``life`` and may
    end it. Turns after a death are not consumed."""
    from .macro import advance_year  # macro imports this module

    for _ in range(turns):
        if not life.alive:
            return
        life.turns += 1
        if life.turns % TURNS_PER_YEAR == 0:
            advance_year(world)


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


def _merge(dst: list, src: list) -> None:
    for item in src:
        if item not in dst:
            dst.append(item)


def _apply_bequest(world: World, life: Life) -> None:
    """Carry title + derived knowledge/skills/traits forward (Bequest, section A-1).

    Inheritance now compounds across lives and affects later actions
    (see inheritance.py)."""
    if not world.player.powers.bequest_enabled or life.summary is None:
        return
    inh = world.player.inherited
    title = life.summary.title
    if title and title not in inh.titles:
        inh.titles.append(title)

    discovery_count = sum(
        1
        for d in world.discoveries
        if any(
            s.id == d.seed_id and s.planted_by_life_id == life.id for s in world.seeds
        )
    )
    derived = derive_inheritance(life, discovery_count)
    _merge(inh.knowledge, derived["knowledge"])
    _merge(inh.skills, derived["skills"])
    _merge(inh.traits, derived["traits"])


def end_life(
    world: World, life: Life, cause: DeathCause = DeathCause.LIFESPAN
) -> LifeSummary:
    """Finalize a life: record death, build the summary, and apply inheritance.

    The post-death world time-skip and history generation are P3 (macro loop);
    this function ends the micro loop and prepares the hand-off. A life dies
    once: calling this on a dead life is a bug, not a no-op.
    """
    if not life.alive:
        raise RuntimeError(f"{life.id} already died in year {life.death_year}")
    life.death_year = world.current_year
    life.age_at_death = life.age
    life.death_cause = cause
    life.summary = build_life_summary(world, life)
    _apply_bequest(world, life)
    world.player.current_life_id = None
    return life.summary
