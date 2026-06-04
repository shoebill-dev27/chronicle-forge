"""story.md (Priority 0): trace each life's arc

    Life -> Activities -> Seeds -> Events -> Heritage -> contribution to the Ending

The core value of Chronicle Forge is not that causality exists but that it can be
*read*. This is the centerpiece demo asset. Read-only; facts only.
"""

from __future__ import annotations

from ..causal import CausalGraph
from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import (
    activity_counts,
    life_index,
    seeds_of_life,
    triggered_node,
)

_MAX_CHAINS = 5


def render_story_of_life(world: World, life_id: str) -> str:
    graph = CausalGraph.from_world(world)
    idx = life_index(world)
    life = next((x for x in world.lives if x.id == life_id), None)
    if life is None:
        return f"## Life ? — {life_id} (not found)"

    n = idx.get(life_id, "?")
    title = life.summary.title if life.summary else life_id
    lines = [f"## Life {n} — {title}"]
    lines.append(
        f"- **Talent:** {life.talent.value if life.talent else '—'} | "
        f"**Lived:** y{life.birth_year}–y{life.death_year} "
        f"(age {life.age_at_death}, {life.death_cause.value if life.death_cause else '—'})"
    )
    lines.append(f"- **Activities:** {activity_counts(life)}")

    seeds = seeds_of_life(world, life_id)
    fired = [s for s in seeds if s.fired]
    lines.append(
        f"- **Seeds planted:** {len(seeds)} ({len(fired)} fired into world events)"
    )

    # Causal chains: seed -> founding event -> downstream count, biggest first.
    scored = []
    for s in fired:
        ev = triggered_node(world, s.id)
        if ev is not None:
            scored.append((len(graph.descendants(ev.id)), s, ev))
    scored.sort(key=lambda r: (-r[0], r[1].id))
    if scored:
        lines.append("- **Causal chains (Seed → Event → downstream):**")
        for desc, s, ev in scored[:_MAX_CHAINS]:
            lines.append(
                f"    - `{s.id}` ({s.domain.value}) → y{ev.year} *{ev.title}* "
                f"→ **{desc}** downstream events"
            )

    # Heritage promoted from this life's seeds.
    seed_ids = {s.id for s in seeds}
    her = [h for h in world.heritage if h.seed_id in seed_ids]
    if her:
        lines.append("- **Heritage (lasting legacy):**")
        for h in sorted(her, key=lambda h: -h.heritage_score):
            lines.append(
                f"    - {h.type.value} (`{h.seed_id}`) — score {h.heritage_score}, "
                f"{h.longevity}y, reach {h.reach}"
            )

    # Contribution to the ending.
    dom = world.theme.dominant
    contrib = sum(1 for s in fired if SEED_DOMAIN_TO_THEME[s.domain] == dom)
    if dom is not None and contrib:
        lines.append(
            f"- **Contribution to the {world.ending_class}:** {contrib} of this "
            f"life's seeds pushed the final *{dom.value}* tilt."
        )
    else:
        lines.append(
            f"- **Contribution to the {world.ending_class}:** shaped earlier ages; "
            f"not the final tilt."
        )
    return "\n".join(lines)


def stories_md(world: World) -> str:
    lines = [
        f"# The Lives of {_title_place(world)} — Seed {world.seed}",
        "",
        "_How each life's actions flowed into the world's history. "
        "Read top to bottom: a life acts, plants seeds, those seeds fire into "
        "events, some become lasting heritage, and together they tilt the world "
        f"toward its ending — the **{world.ending_class}**._",
        "",
    ]
    for life in world.lives:
        lines.append(render_story_of_life(world, life.id))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _title_place(world: World) -> str:
    from ._data import place

    return place(world)
