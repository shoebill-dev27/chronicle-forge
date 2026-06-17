"""P9-4 Lineage Viewer — the chain of reincarnations and what each self left.

A read-only projection of a finished world into player-facing Markdown. Every
life is the player reborn (a node); heritage is what a life left behind, factions
are context. It reuses the deterministic reporting helpers, never mutates the
world, and never leaks an internal id (the P8 lesson) — lives are shown by their
ordinal + title, heritage by its proper name.

Spine = the life-chain. Order is selectable (chronological default, impact,
generation); every order contains all lives and is deterministic (ties break on
the life ordinal, no set/dict iteration in the output).
"""

from __future__ import annotations

from typing import List

from ..models import World
from ._data import life_index, life_world_impact, place, seed_by_id
from .labels import heritage_name

_ORDERS = ("chronological", "impact", "generation")


# --- data extraction ----------------------------------------------------


def _era(world: World) -> str:
    dom = world.theme.dominant
    return f"an age of {dom.value}" if dom is not None else "an unsettled age"


def _life_title(world: World, life) -> str:
    if life.summary and life.summary.title:
        return life.summary.title
    talent = life.talent.value if life.talent else "soul"
    return f"a {talent} of {place(world)}"


def _heritage_descriptors(world: World) -> List[dict]:
    """One descriptor per heritage, sorted deterministically (by -score, then
    the source seed id — the same order ``heritage_rows`` uses). Carries the
    founder's life ordinal and the founding year, never a raw id in the output."""
    idx = life_index(world)
    items = []
    for h in world.heritage:
        seed = seed_by_id(world, h.seed_id)
        founder_id = seed.planted_by_life_id if seed else None
        items.append(
            {
                "name": heritage_name(h),
                "score": h.heritage_score,
                "source_seed": h.seed_id,
                "founder_id": founder_id,
                "founding_year": seed.planted_year if seed else 0,
            }
        )
    items.sort(key=lambda d: (-d["score"], d["source_seed"]))
    return items


# --- ordering -----------------------------------------------------------


def _ordered_lives(world: World, order: str) -> list:
    idx = life_index(world)
    lives = list(world.lives)  # already in birth order
    if order == "chronological":
        return sorted(lives, key=lambda lf: (lf.birth_year, idx[lf.id]))
    if order == "impact":
        return sorted(
            lives, key=lambda lf: (-life_world_impact(world, lf.id), idx[lf.id])
        )
    # generation: newest self first, oldest last
    return sorted(lives, key=lambda lf: -idx[lf.id])


# --- renderer -----------------------------------------------------------


def _join(names: List[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def _span_line(world: World, life) -> str:
    if life.death_year is not None:
        age = life.age_at_death if life.age_at_death is not None else "?"
        return (
            f"- Born year {life.birth_year}, died year {life.death_year} "
            f"(aged {age}), in {_era(world)}."
        )
    return f"- Born year {life.birth_year}, in {_era(world)}."


def lineage_view(world: World, *, order: str = "chronological") -> str:
    """The whole reincarnation chain as player-facing Markdown. Read-only and
    deterministic. ``order`` is one of ``chronological`` (default), ``impact``,
    ``generation``; an unknown order raises ``ValueError``."""
    if order not in _ORDERS:
        raise ValueError(f"unknown order {order!r}; expected one of {_ORDERS}")

    idx = life_index(world)
    descriptors = _heritage_descriptors(world)
    latest_ordinal = len(world.lives)

    lines = [
        "# The line you have walked",
        "",
        f"> {len(world.lives)} lives, {world.current_year} years, one soul reborn.",
        "",
    ]

    for life in _ordered_lives(world, order):
        ordn = idx[life.id]
        lines.append(f"## Life {ordn} — {_life_title(world, life)}")
        lines.append(_span_line(world, life))

        born_into = [
            d["name"]
            for d in descriptors
            if d["founder_id"] != life.id and d["founding_year"] < life.birth_year
        ]
        if born_into:
            lines.append(f"- Born into a world already shaped by {_join(born_into)}.")

        left = [d["name"] for d in descriptors if d["founder_id"] == life.id]
        if left:
            lines.append(f"- Left behind: {_join(left)}.")
        else:
            lines.append("- Left no lasting mark.")

        if ordn == latest_ordinal:
            lines.append("- You are here.")
        lines.append("")

    lines.append("## What outlived them all")
    if descriptors:
        for d in descriptors:
            lines.append(f"- {d['name']}")
    else:
        lines.append("- Nothing endured; the world closed over every life.")

    return "\n".join(lines).rstrip() + "\n"
