"""gallery.md: a multi-world showcase.

Renders a side-by-side table of several fixed seeds so a viewer sees at a glance
that the same engine grows a different history every time. Read-only, rules-based,
deterministic, no AI.

Key decision = the player-origin action that contributed most to the world's
final ending (the strongest player seed on the dominant-theme lineage —
Ending <- Event <- Seed <- Life).
"""

from __future__ import annotations

from typing import Optional

from ..autoplay import simulate_world
from ..causal import CausalGraph
from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import heritage_rows, triggered_node
from .labels import seed_label

# Frozen seeds (derived once via select_diverse_seeds over 1..40): each yields a
# distinct ending — Golden / Mercantile / Arcane / Warring / Theocratic / Imperial.
GALLERY_SEEDS = [1, 3, 4, 9, 15, 20]

# One-line, deterministic explanation of why a world ended as it did (20-40 chars).
_WHY_BY_ENDING = {
    "Golden Age": "Culture and learning flourished",
    "Mercantile Age": "Trade networks unified the realm",
    "Arcane Age": "New discoveries reshaped the age",
    "Warring Age": "Warfare overwhelmed governance",
    "Theocratic Age": "Faith movements dominated society",
    "Imperial Age": "Institutions consolidated power",
    "Apocalyptic Age": "Unchecked war consumed the world",
    "Forgotten Age": "No legacy endured to define it",
}
_WHY_BY_AXIS = {
    "culture": "Culture and learning flourished",
    "commerce": "Trade networks unified the realm",
    "innovation": "New discoveries reshaped the age",
    "warfare": "Warfare overwhelmed governance",
    "faith": "Faith movements dominated society",
    "governance": "Institutions consolidated power",
}


def select_diverse_seeds(scan: int = 40, k: int = 6, start: int = 1) -> list[int]:
    """Greedily pick the first seed for each distinct ending, then fill to k.

    This is how GALLERY_SEEDS was derived; kept for transparency / re-derivation.
    """
    worlds = {s: simulate_world(s) for s in range(start, start + scan)}
    picked: list[int] = []
    seen: set = set()
    for s in range(start, start + scan):
        e = worlds[s].ending_class
        if e not in seen:
            seen.add(e)
            picked.append(s)
            if len(picked) >= k:
                return picked
    for s in range(start, start + scan):
        if s not in picked:
            picked.append(s)
            if len(picked) >= k:
                break
    return picked[:k]


def why_phrase(world: World) -> str:
    if world.ending_class in _WHY_BY_ENDING:
        return _WHY_BY_ENDING[world.ending_class]
    dom = world.theme.dominant
    return _WHY_BY_AXIS.get(dom.value if dom else "", "A world unlike the others")


def key_ending_decision(world: World) -> str:
    """The player action that most shaped the final ending.

    Among the player's fired seeds, prefer those whose domain feeds the final
    dominant theme (i.e. that pushed the world toward this ending), and pick the
    one with the largest downstream reach. Falls back to overall top impact.
    """
    dom = world.theme.dominant
    graph = CausalGraph.from_world(world)

    def impact(seed) -> int:
        ev = triggered_node(world, seed.id)
        return len(graph.descendants(ev.id)) if ev else 0

    player = [s for s in world.seeds if s.fired and s.planted_by_life_id]
    aligned = [
        s for s in player if dom is not None and SEED_DOMAIN_TO_THEME[s.domain] == dom
    ]
    pool = aligned or player
    if not pool:
        return "—"
    pool.sort(key=lambda s: (-impact(s), s.id))
    label = seed_label(world, pool[0].id)
    return label[0].upper() + label[1:]


def gallery_md(seeds: Optional[list[int]] = None) -> str:
    seeds = seeds or GALLERY_SEEDS
    worlds = [(s, simulate_world(s)) for s in seeds]

    lines = [
        "# Multi-world Showcase",
        "",
        "_Same engine, different seeds — every world writes its own history._",
        "",
        "| Seed | Ending | Lives | Dominant theme | Top heritage | Key decision | Why |",
        "|------|--------|-------|----------------|--------------|--------------|-----|",
    ]
    endings = set()
    for s, world in worlds:
        endings.add(world.ending_class)
        rows = heritage_rows(world, top=1)
        top = rows[0]["name"] if rows else "—"
        dom = world.theme.dominant.value if world.theme.dominant else "—"
        lines.append(
            f"| {s} | {world.ending_class} | {len(world.lives)} | {dom} "
            f"| {top} | {key_ending_decision(world)} | {why_phrase(world)} |"
        )

    lines += [
        "",
        f"**{len(worlds)} worlds → {len(endings)} distinct endings.** "
        "Each is fully reproducible from its seed (rules-only, no AI).",
        "",
        "See one world in depth: [`seed42/`](seed42/).",
    ]
    return "\n".join(lines) + "\n"
