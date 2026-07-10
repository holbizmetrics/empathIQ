"""A 'personality' is the user-facing unit: a name + voice + which graph it runs +
optional per-block prompt overrides. This is what a non-builder authors and tests.

  {
    "name": "Sol",
    "description": "calm, plain-spoken guide ...",
    "persona_layer": 3,            # 1/2/3 association depth (optional)
    "graph": "default",            # a graphs/<name>.json, or an inline graph dict
    "block_prompts": {"RESP": "custom instruction for the response block"}
  }
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

from .graph import Graph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHS_DIR = os.path.join(ROOT, "graphs")
PERSONALITIES_DIR = os.path.join(ROOT, "personalities")


@dataclass
class Personality:
    name: str
    description: str = ""
    persona_layer: int | None = None
    graph_ref: str | dict = "default"
    block_prompts: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Personality":
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            persona_layer=d.get("persona_layer"),
            graph_ref=d.get("graph", "default"),
            block_prompts=d.get("block_prompts", {}),
        )

    @classmethod
    def load(cls, name_or_path: str) -> "Personality":
        path = name_or_path
        if not os.path.exists(path):
            path = os.path.join(PERSONALITIES_DIR, f"{name_or_path}.json")
            if not os.path.exists(path):
                # Case-insensitive fallback so --personality Sol / sol / SOL all resolve
                # to sol.json on EVERY OS (not just case-insensitive filesystems like NTFS).
                wanted_filename = f"{name_or_path}.json".lower()
                for entry in os.listdir(PERSONALITIES_DIR):
                    if entry.lower() == wanted_filename:
                        path = os.path.join(PERSONALITIES_DIR, entry)
                        break
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def resolve_graph(self) -> Graph:
        if isinstance(self.graph_ref, dict):
            return Graph.from_dict(self.graph_ref)
        return Graph.load(os.path.join(GRAPHS_DIR, f"{self.graph_ref}.json"))

    def persona_dict(self) -> dict:
        return {"name": self.name, "description": self.description,
                "persona_layer": self.persona_layer}

    def save(self, path: str | None = None) -> str:
        path = path or os.path.join(PERSONALITIES_DIR, f"{self.name.lower()}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "name": self.name, "description": self.description,
                "persona_layer": self.persona_layer, "graph": self.graph_ref,
                "block_prompts": self.block_prompts,
            }, f, indent=2)
        return path
