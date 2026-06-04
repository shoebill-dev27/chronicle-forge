"""Read-only, text-based observability views (P5).

A developer-facing debug reader: every view is a pure function that renders a
string from existing data structures. No AI text, no state mutation. The goal is
to let a human read a finished world and judge whether it is fun as a game.
"""

from __future__ import annotations

from typing import Iterable, Optional

from .causal import CausalGraph
from .enums import EventScale, NPCTier
from .heritage import _triggered_node
from .models import World

_EVAL_LENSES = [
    "military",
    "politics",
    "economy",
    "academia",
    "culture",
    "faith",
    "mentoring",
    "heritage",
]


# --- small helpers ------------------------------------------------------


def _faction_name(world: World, faction_id: Optional[str]) -> str:
    if faction_id is None:
        return "—"
    f = next((f for f in world.factions if f.id == faction_id), None)
    return f.name if f else faction_id


def _seed_index(world: World) -> dict:
    return {s.id: s for s in world.seeds}


def _node_index(world: World) -> dict:
    return {n.id: n for n in world.causal_nodes}


# --- 6. world summary + report sections --------------------------------


def render_world_summary(world: World) -> str:
    lines = ["=== WORLD SUMMARY ==="]
    lines.append(f"world {world.id}  seed={world.seed}")
    lines.append(
        f"years 0..{world.current_year} (max {world.max_year})  "
        f"ending: {world.ending_class or 'n/a'}"
    )
    lines.append(
        f"lives={len(world.lives)}  events={len(world.causal_nodes)}  "
        f"seeds={len(world.seeds)}  heritage={len(world.heritage)}  "
        f"discoveries={len(world.discoveries)}"
    )
    alive = sum(1 for n in world.npcs if n.alive)
    lines.append(
        f"npcs: {alive}/{len(world.npcs)} alive  population≈{world.population}"
    )
    lines.append(
        f"theme dominant: {world.theme.dominant.value if world.theme.dominant else '—'}"
    )
    return "\n".join(lines)


def render_lives_list(world: World) -> str:
    lines = ["=== PLAYER LIVES ==="]
    for life in world.lives:
        title = life.summary.title if life.summary else "(in progress)"
        died = (
            f"died y{life.death_year} @age {life.age_at_death} "
            f"({life.death_cause.value})"
            if life.death_cause
            else "alive"
        )
        lines.append(
            f"  [{life.id}] {title} | born y{life.birth_year}, {died} | "
            f"talent={life.talent.value if life.talent else '—'} | "
            f"acts={len(life.activity_log)}"
        )
    return "\n".join(lines)


def render_theme_trajectory(world: World) -> str:
    lines = ["=== THEME TRAJECTORY ==="]
    if not world.theme.history:
        lines.append("  (no snapshots)")
        return "\n".join(lines)
    for snap in world.theme.history:
        top = sorted(snap.axes.items(), key=lambda kv: -kv[1])[:3]
        bar = ", ".join(f"{a.value}={v}" for a, v in top)
        dom = snap.dominant.value if snap.dominant else "—"
        lines.append(f"  y{snap.year:>3}: {dom:<10} [{bar}]")
    return "\n".join(lines)


def render_wildcard_history(world: World) -> str:
    lines = ["=== WILDCARD HISTORY ==="]
    for wc in world.wildcards.wildcards:
        lines.append(f"  {wc.name} ({wc.archetype.value}): {wc.status.value}")
        events = sorted(
            (n for n in world.causal_nodes if wc.id in n.actors),
            key=lambda n: (n.year, n.id),
        )
        for n in events:
            lines.append(f"      y{n.year:>3} {n.title}")
        if not events:
            lines.append("      (no events emitted)")
    return "\n".join(lines)


def render_major_events(world: World, include_small: bool = False) -> str:
    lines = ["=== MAJOR EVENTS ==="]
    scales = {EventScale.LARGE, EventScale.MEDIUM}
    if include_small:
        scales.add(EventScale.SMALL)
    for n in sorted(world.causal_nodes, key=lambda n: (n.year, n.id)):
        if n.scale in scales:
            lines.append(f"  y{n.year:>3} [{n.scale.value:<6}] {n.title}")
    return "\n".join(lines)


# --- 1. causal trace ----------------------------------------------------


def _label(world: World, ident: str, seeds: dict, nodes: dict) -> str:
    if ident in seeds:
        s = seeds[ident]
        mark = "★" if s.planted_by_life_id else ""
        return f"{mark}seed:{s.domain.value}({ident})"
    if ident in nodes:
        n = nodes[ident]
        return f"{ident}:{n.title}"
    return ident


def render_causal_trace(world: World, node_id: str) -> str:
    graph = CausalGraph.from_world(world)
    nodes = _node_index(world)
    seeds = _seed_index(world)
    node = nodes.get(node_id)
    if node is None:
        return f"=== CAUSAL TRACE: {node_id} ===\n  (node not found)"

    lines = [f"=== CAUSAL TRACE: {node_id} ==="]
    lines.append(
        f"{node.title} (y{node.year}, {node.scale.value}, {node.domain.value})"
    )
    lines.append(f"descendants (downstream events): {len(graph.descendants(node_id))}")

    player_seeds = graph.player_seeds_in_ancestry(node_id)
    if player_seeds:
        lines.append(
            "player-driven causes (★): " + ", ".join(s.id for s in player_seeds)
        )

    lines.append("-- cause paths to roots (★ = player seed) --")
    for path in graph.trace_to_roots(node_id):
        chain = " <- ".join(_label(world, ident, seeds, nodes) for ident in path)
        lines.append("  " + chain)

    # Heritage promotion path: heritages whose seed is in this node's ancestry.
    ancestry = graph.ancestors(node_id) | {node_id}
    related = [h for h in world.heritage if h.seed_id in ancestry]
    if related:
        lines.append("-- heritage promoted on this lineage --")
        for h in related:
            founding = _triggered_node(world, h.seed_id)
            fy = founding.year if founding else "?"
            lines.append(
                f"  {h.id} {h.type.value} (founded y{fy}) "
                f"score={h.heritage_score} longevity={h.longevity} reach={h.reach}"
            )
    return "\n".join(lines)


# --- 2. personal history ------------------------------------------------


def render_personal_history(world: World) -> str:
    lines = ["=== PERSONAL HISTORY ==="]
    for life in world.lives:
        s = life.summary
        lines.append(f"\n[{life.id}] {s.title if s else '(in progress)'}")
        died = (
            f"died y{life.death_year} at age {life.age_at_death} ({life.death_cause.value})"
            if life.death_cause
            else "alive"
        )
        lines.append(
            f"  born y{life.birth_year}, {died}, "
            f"talent={life.talent.value if life.talent else '—'}"
        )
        ev = life.evaluation
        lines.append(
            "  evaluation: " + ", ".join(f"{k}={getattr(ev, k)}" for k in _EVAL_LENSES)
        )
        if life.activity_log:
            counts: dict[str, int] = {}
            for rec in life.activity_log:
                counts[rec.category] = counts.get(rec.category, 0) + 1
            summary = ", ".join(f"{k}×{v}" for k, v in counts.items())
            lines.append(f"  activities ({len(life.activity_log)}): {summary}")
        if s:
            lines.append(
                f"  legacy at death: seeds={len(s.seeds_created)}, "
                f"heritage={len(s.heritage_created)}, "
                f"notable_events={len(s.notable_events)}, "
                f"dominant_axis={s.dominant_axis.value if s.dominant_axis else '—'}"
            )
            # World impact realized later (seeds that fired during the skip): this
            # is the cross-reincarnation mark on the future.
            owned = {sd.id for sd in world.seeds if sd.planted_by_life_id == life.id}
            events = sum(
                1
                for n in world.causal_nodes
                if any(e.from_id in owned for e in n.caused_by)
            )
            herit = sum(1 for h in world.heritage if h.seed_id in owned)
            lines.append(
                f"  world impact (incl. post-death): events_caused={events}, "
                f"heritage_formed={herit}"
            )
    inh = world.player.inherited
    lines.append("\n-- Inheritance (cumulative) --")
    lines.append(f"  titles: {inh.titles}")
    lines.append(f"  knowledge={inh.knowledge} skills={inh.skills} traits={inh.traits}")
    return "\n".join(lines)


# --- 4. heritage ranking ------------------------------------------------


def render_heritage_ranking(world: World, top: int = 10) -> str:
    graph = CausalGraph.from_world(world)
    rows = []
    for h in world.heritage:
        founding = _triggered_node(world, h.seed_id)
        derived = len(graph.descendants(founding.id)) if founding else 0
        rows.append(
            (h.heritage_score, h.longevity, h.reach, h.type.value, h.seed_id, derived)
        )
    rows.sort(key=lambda r: (-r[0], r[4]))

    lines = [f"=== HERITAGE RANKING (Top {top}) ==="]
    if not rows:
        lines.append("  (no heritage formed)")
        return "\n".join(lines)
    for i, (score, lon, reach, typ, seed, derived) in enumerate(rows[:top], 1):
        lines.append(
            f"  {i:>2}. score={score:<5} longevity={lon:<3} reach={reach:<3} "
            f"{typ:<11} seed={seed:<12} derived_events={derived}"
        )
    return "\n".join(lines)


# --- 5. NPC codex -------------------------------------------------------


def render_npc_codex(world: World, tiers: Iterable[NPCTier] = (NPCTier.S,)) -> str:
    tiers = set(tiers)
    lines = ["=== NPC CODEX ==="]
    for npc in world.npcs:
        if npc.tier not in tiers:
            continue
        lc = npc.lifecycle
        status = "alive" if npc.alive else "deceased"
        death = lc.death_year if lc.death_year is not None else "—"
        lines.append(f"\n[{npc.id}] {npc.name} (tier {npc.tier.value}) — {status}")
        lines.append(
            f"  born y{lc.birth_year}, died y{death}, age {lc.age}, "
            f"occupation={lc.occupation}, faction={_faction_name(world, lc.faction_id)}"
        )
        if npc.goals:
            lines.append(f"  intent: {', '.join(npc.goals)}")
        if npc.relations:
            rel = ", ".join(
                f"{aid}(aff={r.affinity},trust={r.trust},fear={r.fear})"
                for aid, r in npc.relations.items()
            )
            lines.append(f"  relations: {rel}")
        mems = [m for m in world.memories if m.subject_id == npc.id]
        if mems:
            lines.append(f"  memories ({len(mems)}):")
            for m in mems:
                lines.append(
                    f"      y{m.timestamp} {m.type.value} from {m.actor_id} "
                    f"(valence {m.valence}, intensity {m.intensity})"
                )
    return "\n".join(lines)


# --- full report (integration smoke output) -----------------------------


def full_report(world: World) -> str:
    """The one-shot developer report combining every view."""
    return "\n\n".join(
        [
            render_world_summary(world),
            render_lives_list(world),
            render_personal_history(world),
            render_theme_trajectory(world),
            render_major_events(world),
            render_wildcard_history(world),
            render_heritage_ranking(world, top=10),
            render_npc_codex(world, tiers=(NPCTier.S,)),
        ]
    )
