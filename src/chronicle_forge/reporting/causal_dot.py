"""causal.dot: Graphviz DOT showing player Seed -> Event -> Heritage -> Ending.

Default focus = "heritage": only the lineages that reach a heritage are drawn
(plus an Ending terminal node), so a viewer sees at a glance how a past life's
action flowed all the way to the world's ending. ``focus="full"`` draws the
whole causal graph. Read-only; emits a .dot string (render to PNG with
``dot -Tpng``).
"""

from __future__ import annotations

from ..causal import CausalGraph
from ..enums import CausalEdgeKind
from ..models import World
from ..theme import SEED_DOMAIN_TO_THEME
from ._data import life_index, seed_by_id, triggered_node
from .labels import heritage_name, seed_label


def _esc(text: str) -> str:
    return text.replace('"', '\\"')


def _seed_node(world: World, seed_id: str) -> str:
    s = seed_by_id(world, seed_id)
    idx = life_index(world)
    if s is None:
        return f'  "{seed_id}" [shape=box, label="{_esc(seed_id)}"];'
    label = _esc(seed_label(world, seed_id))
    if s.planted_by_life_id:
        n = idx.get(s.planted_by_life_id, "?")
        return (
            f'  "{seed_id}" [shape=box, style=filled, fillcolor=gold, '
            f'label="★ L{n}: {label}\\n{seed_id}"];'
        )
    return (
        f'  "{seed_id}" [shape=box, style=filled, fillcolor=lightgrey, '
        f'label="{label}\\n{seed_id}"];'
    )


def _event_node(node) -> str:
    label = f"y{node.year} {node.title}"
    return f'  "{node.id}" [shape=ellipse, label="{_esc(label)}"];'


def causal_dot(
    world: World, focus: str = "heritage", include_ending: bool = True
) -> str:
    graph = CausalGraph.from_world(world)
    node_by_id = {n.id: n for n in world.causal_nodes}

    seeds_used: set = set()
    nodes_used: set = set()
    edges: list[tuple] = []  # (from, to, kind)

    if focus == "full":
        for n in world.causal_nodes:
            nodes_used.add(n.id)
            for e in n.caused_by:
                if e.from_id in node_by_id:
                    nodes_used.add(e.from_id)
                else:
                    seeds_used.add(e.from_id)
                edges.append((e.from_id, n.id, e.kind))
    else:
        # heritage lineage focus: for each heritage, all ids on player-rooted
        # paths from its founding event back to roots.
        for h in world.heritage:
            founding = triggered_node(world, h.seed_id)
            if founding is None:
                continue
            for path in graph.trace_to_roots(founding.id):
                # keep paths that bottom out at a player seed
                root = path[-1]
                root_seed = seed_by_id(world, root)
                if root_seed is None or root_seed.planted_by_life_id is None:
                    continue
                for ident in path:
                    if ident in node_by_id:
                        nodes_used.add(ident)
                    else:
                        seeds_used.add(ident)
                # edges along the path (effect <- cause): child.caused_by
                for child_id in path:
                    child = node_by_id.get(child_id)
                    if child is None:
                        continue
                    for e in child.caused_by:
                        if e.from_id in path:
                            edges.append((e.from_id, child_id, e.kind))

    # Render heritage nodes + promoted edges + ending.
    heritage_lines = []
    promoted_edges = []
    ending_edges = []
    rendered_heritage_ids = []
    dom = world.theme.dominant
    for h in world.heritage:
        founding = triggered_node(world, h.seed_id)
        if focus != "full" and (founding is None or founding.id not in nodes_used):
            continue
        hid = h.id
        rendered_heritage_ids.append(hid)
        heritage_lines.append(
            f'  "{hid}" [shape=doubleoctagon, style=filled, fillcolor=palegreen, '
            f'label="{_esc(heritage_name(h))}\\n({h.type.value}, score {h.heritage_score})"];'
        )
        if founding is not None:
            promoted_edges.append((founding.id, hid))
        seed = seed_by_id(world, h.seed_id)
        if (
            include_ending
            and seed is not None
            and SEED_DOMAIN_TO_THEME[seed.domain] == dom
        ):
            ending_edges.append(hid)

    # Assemble.
    out = [
        "digraph ChronicleForge {",
        "  rankdir=TB;",
        '  labelloc="t";',
        f'  label="Seed {world.seed}: how past lives shaped the {world.ending_class}";',
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=8];',
        "",
    ]
    for sid in sorted(seeds_used):
        out.append(_seed_node(world, sid))
    for nid in sorted(nodes_used):
        if nid in node_by_id:
            out.append(_event_node(node_by_id[nid]))
    out.extend(heritage_lines)

    if include_ending:
        out.append(
            f'  "ENDING" [shape=box, style="filled,bold", fillcolor=khaki, '
            f'label="ENDING\\n{world.ending_class}"];'
        )

    out.append("")
    seen = set()
    for frm, to, kind in edges:
        key = (frm, to)
        if key in seen:
            continue
        seen.add(key)
        style = "" if kind == CausalEdgeKind.TRIGGER else " [style=dotted]"
        out.append(f'  "{frm}" -> "{to}"{style};')
    for frm, to in promoted_edges:
        out.append(f'  "{frm}" -> "{to}" [style=dashed, label="promoted"];')
    if include_ending:
        targets = ending_edges or rendered_heritage_ids
        for hid in targets:
            out.append(f'  "{hid}" -> "ENDING" [color=darkgreen];')

    out.append("}")
    return "\n".join(out) + "\n"
