"""ASCII architecture renderer for /diagram. Accepts a comma list or a JSON spec
({"sequential":[...], "parallel":[[...]], "joins":{"parallel_to":"RESP"}}).
Unknown block IDs render as [ID], per the spec."""
from __future__ import annotations
import json

from . import blocks as blockmod


def _label(block_id: str) -> str:
    b = blockmod.get(block_id)
    return f"{block_id} ({b.name})" if b else f"[{block_id}]"


def from_comma_list(ids: list[str]) -> str:
    lines = ["", "    " + _label(ids[0])] if ids else [""]
    for nxt in ids[1:]:
        lines.append("        |")
        lines.append("        v")
        lines.append("    " + _label(nxt))
    return "\n".join(lines)


def from_json_spec(spec: dict) -> str:
    seq = list(spec.get("sequential", []))
    parallel = spec.get("parallel", [])
    join = spec.get("joins", {}).get("parallel_to")
    out: list[str] = [""]

    # sequential trunk, splitting in the parallel fan just before the join node
    for i, node in enumerate(seq):
        if i:
            out += ["        |", "        v"]
        out.append("    " + _label(node))
        if parallel and node == join:
            continue

    if parallel:
        out += ["        |", "   +" + "-------+" * len(parallel)]
        for branch in parallel:
            out.append("   | branch: " + "  ".join(_label(b) for b in branch))
        out.append("   +")
        if join:
            out += ["        v", "    " + _label(join) + "   <- parallel join"]
    return "\n".join(out)


def render(spec: str) -> str:
    spec = spec.strip()
    if spec.startswith("{"):
        return from_json_spec(json.loads(spec))
    ids = [s.strip() for s in spec.split(",") if s.strip()]
    return from_comma_list(ids)
