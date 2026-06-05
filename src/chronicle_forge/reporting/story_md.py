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
from .labels import event_phrase, heritage_name, seed_label

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

    seeds = seeds_of_life(world, life_id)
    fired = [s for s in seeds if s.fired]

    # Causal chains: seed -> founding event -> downstream count, biggest first.
    scored = []
    for s in fired:
        ev = triggered_node(world, s.id)
        if ev is not None:
            scored.append((len(graph.descendants(ev.id)), s, ev))
    scored.sort(key=lambda r: (-r[0], r[1].id))

    # Key Decisions: the few most consequential choices this life made.
    decisions = []
    seen = set()
    for _, s, _ in scored:
        label = seed_label(world, s.id)
        label = label[0].upper() + label[1:]
        if label in seen:
            continue
        seen.add(label)
        decisions.append(label)
        if len(decisions) == 3:
            break
    if decisions:
        lines.append("- **Key Decisions:**")
        for d in decisions:
            lines.append(f"    - {d}")

    lines.append(f"- **Activities:** {activity_counts(life)}")
    lines.append(
        f"- **Seeds planted:** {len(seeds)} ({len(fired)} fired into world events)"
    )

    if scored:
        lines.append("- **Causal chains (action → event → downstream):**")
        for desc, s, ev in scored[:_MAX_CHAINS]:
            lines.append(
                f'    - "{seed_label(world, s.id)}" (`{s.id}`) → y{ev.year} '
                f"{event_phrase(ev)} → **{desc}** downstream events"
            )

    # Heritage promoted from this life's seeds.
    seed_ids = {s.id for s in seeds}
    her = [h for h in world.heritage if h.seed_id in seed_ids]
    if her:
        lines.append("- **Heritage (lasting legacy):**")
        for h in sorted(her, key=lambda h: -h.heritage_score):
            lines.append(
                f'    - **"{heritage_name(h)}"** ({h.type.value}, `{h.seed_id}`) — '
                f"score {h.heritage_score}, {h.longevity}y, reach {h.reach}  "
                f'\n        Origin: Life {n} → "{seed_label(world, h.seed_id)}"'
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


def _why_this_world_matters(world: World) -> str:
    from ._data import heritage_rows, life_by_id, life_index, seed_by_id

    dom = world.theme.dominant
    idx = life_index(world)
    lines = ["## Why this world matters", ""]
    lines.append(
        f"- This world ran **{world.current_year} years** across "
        f"**{len(world.lives)} lives** and ended as the **{world.ending_class}**."
    )
    lines.append(
        "- The ending was not scripted — it grew out of the player's own choices, "
        "life after life."
    )

    rows = heritage_rows(world, top=1)
    if rows:
        top = rows[0]
        seed = seed_by_id(world, top["source_seed"])
        life = life_by_id(world, seed.planted_by_life_id) if seed else None
        talent = life.talent.value if life and life.talent else "soul"
        action = seed_label(world, top["source_seed"])
        lines.append(
            f"- It began when **{top['origin_life']}, the {talent}**, chose to "
            f'"{action}". That became **"{top["name"]}"** ({top["type"]}) — a legacy '
            f"that set **{top['derived_events']} later events** in motion."
        )

    # Which life pushed the final tilt the most.
    if dom is not None:
        from ..theme import SEED_DOMAIN_TO_THEME

        best, best_n = None, 0
        for life in world.lives:
            n = sum(
                1
                for s in world.seeds
                if s.planted_by_life_id == life.id
                and s.fired
                and SEED_DOMAIN_TO_THEME[s.domain] == dom
            )
            if n > best_n:
                best, best_n = life, n
        if best is not None:
            talent = best.talent.value if best.talent else "soul"
            lines.append(
                f"- By **Life {idx[best.id]}, the {talent}**, those threads had "
                f"tilted the whole world toward *{dom.value}*, producing the "
                f"{world.ending_class}."
            )

    lines.append(
        "- Everything below is traceable: each life's actions → the seeds they "
        "planted → the events those caused → the heritage that endured → the ending."
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
        _why_this_world_matters(world),
        "",
    ]
    for life in world.lives:
        lines.append(render_story_of_life(world, life.id))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _title_place(world: World) -> str:
    from ._data import place

    return place(world)


def why_ending_chain_md(world: World) -> str:
    """One reversed chain: Ending <- Top Heritage <- Top Event <- Player Action.

    Emphasizes that the ending was caused by a player's choice, not the setting.
    Returns '' if no heritage formed.
    """
    from ._data import heritage_rows, life_by_id, life_index, seed_by_id

    rows = heritage_rows(world, top=1)
    if not rows:
        return ""
    top = rows[0]
    seed = seed_by_id(world, top["source_seed"])
    life = life_by_id(world, seed.planted_by_life_id) if seed else None
    idx = life_index(world)
    founding = triggered_node(world, top["source_seed"])
    n = idx.get(seed.planted_by_life_id, "?") if seed else "?"
    talent = life.talent.value if life and life.talent else "soul"
    ev_year = founding.year if founding else "?"
    ev_text = event_phrase(founding) if founding else "an event"

    return "\n".join(
        [
            "## Why this ending happened",
            "",
            "_The ending was not part of the setting — it was caused by a choice:_",
            "",
            "```",
            f"{world.ending_class}",
            f'   ← "{top["name"]}"   (top heritage)',
            f"   ← {ev_text}, year {ev_year}   (top event)",
            f'   ← Life {n} ({talent}): "{top["origin_action"]}"   (player action)',
            "```",
        ]
    )


def one_causal_chain_md(world: World) -> str:
    """One concrete, retellable chain: Life → Seed → Event → Heritage → Ending.

    Picks the highest-scoring heritage and renders its lineage as a vertical
    chain. Returns '' if the world produced no heritage.
    """
    from ._data import heritage_rows, life_by_id, life_index, seed_by_id

    rows = heritage_rows(world, top=1)
    if not rows:
        return ""
    top = rows[0]
    seed = seed_by_id(world, top["source_seed"])
    life = life_by_id(world, seed.planted_by_life_id) if seed else None
    idx = life_index(world)
    founding = triggered_node(world, top["source_seed"])

    n = idx.get(seed.planted_by_life_id, "?") if seed else "?"
    talent = life.talent.value if life and life.talent else "soul"
    ev_year = founding.year if founding else "?"
    ev_text = event_phrase(founding) if founding else "an event"

    return "\n".join(
        [
            "## One causal chain",
            "",
            "_One thread, from a single choice to the world's ending — the kind of "
            "story this game is built to let you tell:_",
            "",
            "```",
            f"Life {n} — the {talent}",
            f'   │  "{seed_label(world, top["source_seed"])}"   ({top["source_seed"]})',
            "   ▼",
            f"Event (year {ev_year}) — {ev_text}",
            f"   │  endures {top['longevity']} years, {top['derived_events']} events follow",
            "   ▼",
            f'Heritage — "{top["name"]}"  ({top["type"]})',
            "   │  tilts the world",
            "   ▼",
            f"Ending — {world.ending_class}",
            "```",
        ]
    )
