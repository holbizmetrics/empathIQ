"""Emit docs/engine-meta.json from the engine (the 16 blocks + the default graph) so the
in-browser builder reads REAL data and cannot drift from what the engine actually runs.

Run from the repo root:  python docs/make_engine_meta.py
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # docs/
ENGINE = os.path.join(HERE, "..", "forge")                  # the engine lives in forge/
sys.path.insert(0, ENGINE)
from eer import blocks as blockmod  # noqa: E402

# Semantic clusters mirror docs/make_diagrams.py (kept in step with blocks.py purposes).
CLUSTER = {
    "INPUT": "intake", "LIT": "intake",
    "MECH": "read", "BSTK": "read", "CTXT": "read",
    "EMPA": "recognize", "UNLK": "recognize",
    "REFL": "meta", "QTX": "meta",
    "RESP": "respond", "LOOP": "respond",
    "FUSN": "attune", "RESO": "attune", "PRES": "attune",
    "DTFX": "synth", "FINAL": "synth",
}


def main():
    with open(os.path.join(ENGINE, "graphs", "default.json"), encoding="utf-8") as f:
        graph = json.load(f)
    blocks = [{"id": b.id, "symbol": b.symbol, "name": b.name,
               "purpose": b.purpose, "cluster": CLUSTER.get(b.id, "other")}
              for b in blockmod.BLOCKS.values()]
    meta = {
        "_about": "Generated from forge/eer/blocks.py + forge/graphs/default.json by "
                  "docs/make_engine_meta.py. The builder reads this so it cannot drift "
                  "from the engine. Regenerate after any block/graph change.",
        "blocks": blocks,
        "graph": {"entry": graph["entry"], "exit": graph["exit"],
                  "nodes": graph["nodes"], "edges": graph["edges"]},
        # the executor reads the final output from one of these (in order); a selection
        # with none of them produces "(no output produced)".
        "output_writers": ["FINAL", "LOOP", "RESP"],
    }
    out = os.path.join(HERE, "engine-meta.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote {out} ({len(blocks)} blocks, {len(graph['edges'])} edges)")


if __name__ == "__main__":
    main()
