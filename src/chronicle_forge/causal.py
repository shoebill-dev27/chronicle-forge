"""Causal graph service (section 9), the core engine.

The causal structure is a DAG: seeds are roots (no causes), events
(``CausalNode``) carry their incoming edges in ``caused_by``. An edge
``from_id -> to_id`` means "from_id is a cause of to_id".

DAG guarantee: :meth:`CausalGraph.add_edge` rejects any edge whose effect is
already a transitive cause of its cause (or a self-loop), raising
:class:`CausalCycleError`. This makes "trace why this happened" terminating and
contradiction-free (R1).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .enums import CausalEdgeKind
from .models import CausalEdge, CausalNode, World


class CausalCycleError(Exception):
    """Raised when adding an edge would introduce a cycle."""


class CausalGraph:
    """A thin service over a :class:`World`'s seeds, nodes, and edges.

    The graph references the world's live objects, so mutations (adding nodes /
    edges) are reflected in the world state directly.
    """

    def __init__(self, world: World) -> None:
        self.world = world
        self._nodes: dict[str, CausalNode] = {n.id: n for n in world.causal_nodes}
        self._seeds: dict[str, object] = {s.id: s for s in world.seeds}

    @classmethod
    def from_world(cls, world: World) -> "CausalGraph":
        return cls(world)

    # --- mutation ---------------------------------------------------------

    def add_node(self, node: CausalNode) -> CausalNode:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node
        if node not in self.world.causal_nodes:
            self.world.causal_nodes.append(node)
        return node

    def register_seed(self, seed) -> None:
        """Make a seed known to the graph (it must also live in world.seeds)."""
        self._seeds[seed.id] = seed

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        weight: int = 1,
        kind: CausalEdgeKind = CausalEdgeKind.ENABLE,
    ) -> CausalEdge:
        if to_id not in self._nodes:
            raise ValueError(f"effect must be an existing node: {to_id}")
        if from_id not in self._nodes and from_id not in self._seeds:
            raise ValueError(f"cause must exist (node or seed): {from_id}")
        if from_id == to_id:
            raise CausalCycleError(f"self-loop on {to_id}")
        # Cycle iff the effect is already a transitive cause of the cause.
        if to_id in self.ancestors(from_id):
            raise CausalCycleError(f"edge {from_id}->{to_id} would create a cycle")
        edge = CausalEdge(from_id=from_id, to_id=to_id, weight=weight, kind=kind)
        self._nodes[to_id].caused_by.append(edge)
        return edge

    # --- traversal --------------------------------------------------------

    def _direct_causes(self, ident: str) -> list[str]:
        node = self._nodes.get(ident)
        if node is None:  # seeds are roots
            return []
        return [edge.from_id for edge in node.caused_by]

    def ancestors(self, ident: str) -> set[str]:
        """All transitive causes of ``ident`` (excluding itself)."""
        result: set[str] = set()
        stack: list[str] = list(self._direct_causes(ident))
        while stack:
            cur = stack.pop()
            if cur in result:
                continue
            result.add(cur)
            stack.extend(self._direct_causes(cur))
        return result

    def _child_map(self) -> dict[str, set[str]]:
        children: dict[str, set[str]] = defaultdict(set)
        for node in self._nodes.values():
            for edge in node.caused_by:
                children[edge.from_id].add(node.id)
        return children

    def descendants(self, ident: str) -> set[str]:
        """All transitive effects of ``ident`` (excluding itself)."""
        children = self._child_map()
        result: set[str] = set()
        stack: list[str] = list(children.get(ident, set()))
        while stack:
            cur = stack.pop()
            if cur in result:
                continue
            result.add(cur)
            stack.extend(children.get(cur, set()))
        return result

    def trace_to_roots(self, node_id: str) -> list[list[str]]:
        """Return every cause path from ``node_id`` back to a root (section 9.4).

        Each path is ordered effect-first, root-last.
        """
        paths: list[list[str]] = []

        def walk(cur: str, path: list[str]) -> None:
            causes = self._direct_causes(cur)
            if not causes:
                paths.append(path)
                return
            for cause in causes:
                if cause in path:  # defensive; DAG should prevent this
                    paths.append(path)
                    continue
                walk(cause, path + [cause])

        walk(node_id, [node_id])
        return paths

    def player_seeds_in_ancestry(self, node_id: str) -> list:
        """Player-planted seeds among the causes of ``node_id`` (for highlighting)."""
        out = []
        for ancestor in self.ancestors(node_id):
            seed = self._seeds.get(ancestor)
            if seed is not None and getattr(seed, "planted_by_life_id", None):
                out.append(seed)
        return out

    def is_acyclic(self, candidate_edges: Iterable[CausalEdge] = ()) -> bool:
        """True if the current graph (plus optional candidate edges) is a DAG."""
        # The graph is acyclic by construction; this is a verification helper.
        for edge in candidate_edges:
            if edge.to_id in self.ancestors(edge.from_id) or edge.from_id == edge.to_id:
                return False
        return True
