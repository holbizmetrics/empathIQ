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

  python ablate.py --personality sol --input "..."          # mock, structural map (removal)
  python ablate.py --personality sol --isolate               # only_<X> sweep (one block + scaffold)
  python ablate.py --personality sol --validate              # flip-gate criterion #1 (exit 0/1)
  python ablate.py --personality sol --backend claude        # real text deltas
  python ablate.py --personality sol --json                  # machine-readable (for the builder UI)

The --validate mode is the flip-gate instrument check: it asserts every no_<X> AND every
only_<X> path runs and emits a real reply (never "(no output produced)"). Isolation paths
emit by keeping the INPUT+FINAL output scaffold; bare single-block isolation degenerates and
is NOT a valid signal — that is the criterion-#1 finding made mechanical.
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
NO_OUTPUT = "(no output produced)"
# Isolation (only_<X>) keeps just the named block plus this output scaffold; without it,
# a single block that writes no $.output.* key emits NO_OUTPUT. INPUT captures the
# utterance; FINAL writes the delivered reply and reads $.analysis, so the isolated
# block's contribution flows through. (flip-gate criterion #1.)
ISOLATION_SCAFFOLD = ["INPUT", "FINAL"]


def _emits_cleanly(text: str) -> bool:
    return text != NO_OUTPUT and bool(text.strip())


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
            "emits": _emits_cleanly(ablated.final_expression),
        })
    rows.sort(key=lambda r: r["effect"], reverse=True)
    return p, base, rows


def run_isolation(personality: str, utterance: str, backend_kind: str,
                  model: str | None = None) -> tuple[Personality, object, list[dict]]:
    """Isolation companion to run_ablation: for each block, run ONLY that block plus the
    output scaffold (only_<X>) and measure the delta vs the full pipeline. Where ablation
    asks "what breaks when X is removed", isolation asks "what does X alone contribute".
    Every path emits cleanly by construction (the scaffold guarantees an output writer)."""
    p = Personality.load(personality)
    base_graph = p.resolve_graph()

    def _run(graph, variant):
        return run_graph(graph, utterance, make_backend(backend_kind, model=model),
                         persona=p.persona_dict(), prompt_overrides=p.block_prompts,
                         variant_name=variant)

    base = _run(base_graph, "A_full")
    nodes = [n for n in base_graph.topo_order() if n not in ISOLATION_SCAFFOLD]

    rows: list[dict] = []
    for node in nodes:
        keep = list(dict.fromkeys([*ISOLATION_SCAFFOLD, node]))
        iso = _run(base_graph.apply_variant(enable_only=keep), f"only_{node}")
        sim = difflib.SequenceMatcher(
            None, base.final_expression, iso.final_expression).ratio()
        block = blockmod.get(node)
        rows.append({
            "node": node,
            "name": block.name if block else node,
            "emits": _emits_cleanly(iso.final_expression),
            "effect": round(1.0 - sim, 4),
            "similarity": round(sim, 4),
            "char_delta": len(iso.final_expression) - len(base.final_expression),
        })
    rows.sort(key=lambda r: r["effect"], reverse=True)
    return p, base, rows


def validate_instrument(personality: str, utterance: str, backend_kind: str,
                        model: str | None = None) -> dict:
    """Flip-gate criterion #1: every no_<X> and only_<X> path runs and emits cleanly.
    Returns a structured verdict; PASS iff no path degenerates to NO_OUTPUT."""
    _, _, abl = run_ablation(personality, utterance, backend_kind, model)
    _, _, iso = run_isolation(personality, utterance, backend_kind, model)
    removal_empty = [r["node"] for r in abl if not r["emits"]]
    isolation_empty = [r["node"] for r in iso if not r["emits"]]
    # criterion #2 (boolean shape only under mock): are the deltas varied, or one flat value?
    iso_effects = sorted({r["effect"] for r in iso})
    abl_effects = sorted({r["effect"] for r in abl})
    return {
        "personality": personality,
        "backend": backend_kind,
        "removal_paths": len(abl),
        "isolation_paths": len(iso),
        "removal_empty": removal_empty,
        "isolation_empty": isolation_empty,
        "criterion_1_pass": not removal_empty and not isolation_empty,
        "distinct_isolation_effects": len(iso_effects),
        "distinct_removal_effects": len(abl_effects),
    }


def _print_validate(v: dict) -> None:
    print(f"\n=== flip-gate instrument validation: {v['personality']} "
          f"(backend={v['backend']}) ===\n")
    print(f"Criterion #1 — every no_<X> and only_<X> path emits cleanly:")
    print(f"  removal paths   : {v['removal_paths']:>2}  "
          f"empty: {v['removal_empty'] or '(none)'}")
    print(f"  isolation paths : {v['isolation_paths']:>2}  "
          f"empty: {v['isolation_empty'] or '(none)'}")
    print(f"  => criterion #1: {'PASS' if v['criterion_1_pass'] else 'FAIL'}")
    print(f"\nCriterion #2 (boolean shape only — mock cannot rank magnitude):")
    print(f"  distinct removal effects   : {v['distinct_removal_effects']} "
          f"(1 would be a flat offset)")
    print(f"  distinct isolation effects : {v['distinct_isolation_effects']}")
    if v['backend'] == "mock":
        print("\nNote: criterion #2's SIGNED, sensibly-shaped magnitude is a SEMANTIC "
              "question — run --backend claude/api for the judged pass. Mock proves only "
              "that paths emit and differ, not how much each block matters.")


def _print_isolation(p, base, rows, backend_kind):
    print(f"\n=== per-module isolation: {p.name}  (backend={backend_kind}) ===")
    print(f"baseline A_full: {base.nodes_run} nodes, {len(base.final_expression)} chars")
    print(f"each row = only_{{INPUT, <block>, FINAL}}  (the block plus the output scaffold)\n")
    w = max((len(r["name"]) for r in rows), default=4)
    print(f"  {'block':6} {'name':{w}}  {'effect':>7}  {'dchars':>7}  emits")
    print(f"  {'-'*6} {'-'*w}  {'-'*7}  {'-'*7}  -----")
    for r in rows:
        print(f"  {r['node']:6} {r['name']:{w}}  {r['effect']:7.3f}  "
              f"{r['char_delta']:>7}  {'yes' if r['emits'] else 'NO'}")


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
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--isolate", action="store_true",
                      help="isolation sweep (only_<X>) instead of removal (no_<X>)")
    mode.add_argument("--validate", action="store_true",
                      help="flip-gate criterion #1: assert every no_/only_ path emits cleanly")
    a = ap.parse_args(argv)

    if a.validate:
        v = validate_instrument(a.personality, a.input, a.backend, a.model)
        if a.json:
            print(json.dumps(v, indent=2))
        else:
            _print_validate(v)
        return 0 if v["criterion_1_pass"] else 1

    if a.isolate:
        p, base, rows = run_isolation(a.personality, a.input, a.backend, a.model)
        if a.json:
            print(json.dumps({
                "personality": p.name, "backend": a.backend, "input": a.input,
                "mode": "isolation",
                "baseline": {"nodes_run": base.nodes_run,
                             "final_chars": len(base.final_expression)},
                "isolations": rows,
            }, indent=2))
        else:
            _print_isolation(p, base, rows, a.backend)
        return 0

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
