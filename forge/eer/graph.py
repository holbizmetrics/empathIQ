"""DAG load / validate / topological-order, plus variant overrides.

A variant is a deterministic, mechanical transform of the node set:
  - disable_nodes: drop these nodes (edges through them are bridged out)
  - enable_only:   keep only these nodes (isolation mode)
This is the half of the system that is fully mechanical — no LLM judgement.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field


@dataclass
class Graph:
    graph_id: str
    entry: str
    exit: str
    nodes: list[str]
    edges: list[tuple[str, str]]

    @classmethod
    def from_dict(cls, d: dict) -> "Graph":
        return cls(
            graph_id=d.get("graph_id", "unnamed"),
            entry=d["entry"],
            exit=d["exit"],
            nodes=list(d["nodes"]),
            edges=[tuple(e) for e in d["edges"]],
        )

    @classmethod
    def load(cls, path: str) -> "Graph":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def successors(self, node: str) -> list[str]:
        return [b for a, b in self.edges if a == node]

    def predecessors(self, node: str) -> list[str]:
        return [a for a, b in self.edges if b == node]

    def apply_variant(self, disable_nodes: list[str] | None = None,
                      enable_only: list[str] | None = None) -> "Graph":
        keep = set(self.nodes)
        if enable_only:
            keep = set(enable_only) & keep
        if disable_nodes:
            keep -= set(disable_nodes)

        # bridge edges through dropped nodes so the DAG stays connected
        edges: set[tuple[str, str]] = set()
        for a in keep:
            stack = [b for x, b in self.edges if x == a]
            seen = set()
            while stack:
                b = stack.pop()
                if b in seen:
                    continue
                seen.add(b)
                if b in keep:
                    edges.add((a, b))
                else:
                    stack.extend(y for x, y in self.edges if x == b)
        return Graph(
            graph_id=f"{self.graph_id}+variant",
            entry=self.entry if self.entry in keep else next(iter(keep), self.entry),
            exit=self.exit if self.exit in keep else self.exit,
            nodes=[n for n in self.nodes if n in keep],
            edges=sorted(edges),
        )

    def topo_order(self) -> list[str]:
        """Kahn's algorithm. Raises on cycle. Stable: ties broken by node order."""
        indeg = {n: 0 for n in self.nodes}
        for a, b in self.edges:
            if a in indeg and b in indeg:
                indeg[b] += 1
        order: list[str] = []
        ready = [n for n in self.nodes if indeg[n] == 0]
        while ready:
            ready.sort(key=self.nodes.index)
            n = ready.pop(0)
            order.append(n)
            for m in self.successors(n):
                if m in indeg:
                    indeg[m] -= 1
                    if indeg[m] == 0:
                        ready.append(m)
        if len(order) != len(self.nodes):
            missing = set(self.nodes) - set(order)
            raise ValueError(f"graph has a cycle; unresolved nodes: {sorted(missing)}")
        return order
