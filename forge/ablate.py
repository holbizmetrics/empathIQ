#!/usr/bin/env python3
"""Per-module ablation harness for the EER engine.

For each block in the architecture, run the full pipeline with that ONE block removed
(`no_<BLOCK>`) and measure how much the final output changes versus the full pipeline.
This answers "what does each module actually contribute" per module, individually and
reproducibly — and it surfaces the most interesting case: modules whose removal changes
nothing ("half the modules ablate to ~zero effect").

Reproducible by construction:
  --backend mock (default): deterministic backend. The delta is STRUCTURAL — it shows
      which blocks actually feed the output path. A block whose removal leaves the final
      unchanged is not load-bearing for the output (nominal architecture != live wiring).
      Free, instant, exactly repeatable.
  --backend claude | api: real model text. The delta is SEMANTIC. Repeatable only up to
      model nondeterminism; competence scoring is a separate, judged pass (deferred).

Why ablation and not isolation: a bare single-block graph emits "(no output produced)"
because nothing writes the output key — so "a personality of one module" needs the output
scaffold and isn't a clean signal. Removal (keep the rest, drop one) needs no scaffold and
is the clean per-module delta.

  python ablate.py --personality sol --input "..."          # mock, structural map
  python ablate.py --personality sol --backend claude        # real text deltas
  python ablate.py --personality sol --json                  # machine-readable (for the builder UI)
"""
from __future__ import annotations
import argparse
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eer import blocks as blockmod          # noqa: E402
from eer.backend import make_backend          # noqa: E402
from eer.executor import run_graph            # noqa: E402
from eer.personality import Personality       # noqa: E402

DEFAULT_INPUT = "I keep starting things and not finishing them."
# A block counts as "~zero effect" when removing it changes the final by less than this
# (similarity >= 1 - EPS). Under mock this is effectively exact (EPS catches float noise).
ZERO_EFFECT_EPS = 0.01


def run_ablation(personality: str, utterance: str, backend_kind: str,
                 model: str | None = None) -> tuple[Personality, object, list[dict]]:
    p = Personality.load(personality)
    base_graph = p.resolve_graph()

    def _run(graph, variant):
        return run_graph(graph, utterance, make_backend(backend_kind, model=model),
                         persona=p.persona_dict(), prompt_overrides=p.block_prompts,
                         variant_name=variant)

    base = _run(base_graph, "A_full")
    # Ablate every node except the input capture (removing INPUT degenerates the run).
    nodes = [n for n in base_graph.topo_order() if n != "INPUT"]

    rows: list[dict] = []
    for node in nodes:
        ablated = _run(base_graph.apply_variant(disable_nodes=[node]), f"no_{node}")
        sim = difflib.SequenceMatcher(
            None, base.final_expression, ablated.final_expression).ratio()
        block = blockmod.get(node)
        rows.append({
            "node": node,
            "name": block.name if block else node,
            "effect": round(1.0 - sim, 4),     # 0.0 = removing it changed nothing
            "similarity": round(sim, 4),
            "char_delta": len(ablated.final_expression) - len(base.final_expression),
            "changed": ablated.final_expression != base.final_expression,
        })
    rows.sort(key=lambda r: r["effect"], reverse=True)
    return p, base, rows


def _print_report(p, base, rows, backend_kind):
    print(f"\n=== per-module ablation: {p.name}  (backend={backend_kind}) ===")
    print(f"baseline A_full: {base.nodes_run} nodes, {len(base.final_expression)} chars\n")
    w = max((len(r["name"]) for r in rows), default=4)
    print(f"  {'block':6} {'name':{w}}  {'effect':>7}  {'dchars':>7}  changed")
    print(f"  {'-'*6} {'-'*w}  {'-'*7}  {'-'*7}  -------")
    for r in rows:
        print(f"  {r['node']:6} {r['name']:{w}}  {r['effect']:7.3f}  "
              f"{r['char_delta']:>7}  {'yes' if r['changed'] else 'NO'}")

    zero = [r for r in rows if r["effect"] < ZERO_EFFECT_EPS]
    changed = sum(1 for r in rows if r["changed"])
    if backend_kind == "mock":
        # Under mock the load-bearing signal is the boolean changed/unchanged (does the
        # block feed the output path at all), NOT the effect magnitude — that is just
        # text distance between deterministic markers, not a contribution measure.
        print(f"\nStructural wiring (mock): {changed} of {len(rows)} blocks change the "
              f"output when removed; {len(rows) - changed} are structurally inert.")
        print("Read the 'changed' column, not 'effect' magnitude: mock cannot rank how "
              "MUCH a block matters (that is semantic). What it proves here is whether any "
              "block is dead weight on the output path.")
        print("For the 'half the modules ablate to ~zero effect' question (a SEMANTIC "
              "delta), run --backend claude/api; competence ranking is the separate judged "
              "pass.")
    else:
        print(f"\n{len(zero)} of {len(rows)} blocks ablate to ~zero effect "
              f"(removal left the output essentially unchanged):")
        print("  " + (", ".join(r["node"] for r in zero) if zero else "(none)"))
        print("Note: semantic deltas under a real model are repeatable only up to model "
              "nondeterminism; competence scoring is the separate judged pass.")


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="EER per-module ablation harness")
    ap.add_argument("--personality", default="sol")
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--backend", choices=["mock", "claude", "api"], default="mock")
    ap.add_argument("--model", default=None)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON only")
    a = ap.parse_args(argv)

    p, base, rows = run_ablation(a.personality, a.input, a.backend, a.model)

    if a.json:
        print(json.dumps({
            "personality": p.name,
            "backend": a.backend,
            "input": a.input,
            "baseline": {"nodes_run": base.nodes_run,
                         "final_chars": len(base.final_expression)},
            "ablations": rows,
        }, indent=2))
    else:
        _print_report(p, base, rows, a.backend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
