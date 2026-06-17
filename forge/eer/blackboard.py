"""Shared state for a single run. Blocks read/write dotted `$.` paths into it."""
from __future__ import annotations
import copy


class Blackboard:
    """A nested dict addressed by `$.a.b.c` paths, matching the EER registry."""

    def __init__(self) -> None:
        self._data: dict = {}

    @staticmethod
    def _parts(path: str) -> list[str]:
        p = path.strip()
        if p.startswith("$."):
            p = p[2:]
        elif p.startswith("$"):
            p = p[1:]
        return [seg for seg in p.split(".") if seg]

    def set(self, path: str, value) -> None:
        parts = self._parts(path)
        node = self._data
        for seg in parts[:-1]:
            node = node.setdefault(seg, {})
            if not isinstance(node, dict):
                raise ValueError(f"cannot descend into non-dict at {seg!r} for {path!r}")
        node[parts[-1]] = value

    def get(self, path: str, default=None):
        """Get a path. A trailing `.*` (or whole-subtree path) returns the dict."""
        parts = self._parts(path)
        if parts and parts[-1] == "*":
            parts = parts[:-1]
        node = self._data
        for seg in parts:
            if not isinstance(node, dict) or seg not in node:
                return default
            node = node[seg]
        return node

    def resolve_reads(self, reads: str) -> dict:
        """Resolve a registry `reads` string (comma-separated paths, `*` allowed)
        into a {path: value} dict the prompt builder can render."""
        out: dict = {}
        if not reads or reads == "—":
            return out
        for raw in reads.split(","):
            path = raw.strip()
            if not path:
                continue
            out[path] = self.get(path)
        return out

    def snapshot(self) -> dict:
        return copy.deepcopy(self._data)
