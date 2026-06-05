"""summary.md (generated LAST): a first-timer-friendly digest (~200-300 words).

A summary *of the other assets*, not a primary source. Facts only, no AI.
Written for someone opening the GitHub repo for the first time.
"""

from __future__ import annotations

from ..models import World
from ._data import heritage_rows, life_by_id, place, seed_by_id

_MIN_WORDS, _MAX_WORDS = 200, 300


def _origin_phrase(world: World) -> tuple[str, dict]:
    """Return ('The first life, a warrior,'-style phrase, top heritage row)."""
    rows = heritage_rows(world, top=1)
    if not rows:
        return "", {}
    top = rows[0]
    seed = seed_by_id(world, top["source_seed"])
    life = life_by_id(world, seed.planted_by_life_id) if seed else None
    ordinal = top["origin_life"]  # "Life N"
    talent = life.talent.value if life and life.talent else "soul"
    is_first = world.lives and life is world.lives[0]
    phrase = f"The first life, a {talent}," if is_first else f"{ordinal}, a {talent},"
    return phrase, top


def summarize_world(world: World) -> str:
    dom = world.theme.dominant.value if world.theme.dominant else "its final theme"
    phrase, top = _origin_phrase(world)

    parts = [
        "Chronicle Forge is a reincarnation roguelite where you are a world's only "
        "returning soul. You live, act, and die — and the world keeps going without "
        "you. NPCs, factions, and history continue, so every new life is born into "
        "the consequences of the last.",
        f"This page is one finished world, generated from seed {world.seed} — fully "
        f"reproducible, rules-only, no AI. It ran {world.current_year} years across "
        f"{len(world.lives)} lives and ended as the {world.ending_class}.",
    ]

    if top:
        parts.append(
            f"The ending was not scripted; it grew out of the player's choices. "
            f"{phrase} planted what became the world's greatest legacy — a "
            f"{top['type']} that set {top['derived_events']} later events in motion. "
            f"Life after life, such threads pushed the world toward {dom}, until they "
            f"produced the {world.ending_class}."
        )
    else:
        parts.append(
            "The ending was not scripted; it grew out of the player's choices, "
            f"life after life, until the world tilted toward {dom}."
        )

    parts.append(
        "Every step is traceable. Take the ending and walk it backwards — "
        "ending ← event ← seed ← the exact life that began it — until you reach the "
        "original action, decades earlier. That is the core promise made literal and "
        "inspectable: the player's actions continued affecting history long after death."
    )
    parts.append(
        "Read it as a history book whose author you can interrogate: for any line, "
        'you can ask "why did this happen?", and the answer is always another line '
        "above it — a war, a school, an investment — until the trail ends at a single "
        "life's deliberate choice. Nothing here was hand-written; it was lived into being."
    )
    parts.append(
        "Start with story.md to follow each life's chain, then chronicle.md for the "
        'full record and the "Why this Ending" trace.'
    )

    text = "\n\n".join(parts)
    # Keep within the word band: drop the intro paragraph if too long.
    if len(text.split()) > _MAX_WORDS:
        text = "\n\n".join(parts[1:])
    return text
