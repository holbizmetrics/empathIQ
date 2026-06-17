"""eer — command line for the Empathic Engine Researcher.

Build a personality (blocks + voice), then run and A/B test it for real.

  eer blocks                              list the 16 blocks
  eer graphs                              list available graphs
  eer diagram LIT,MECH,EMPA,RESP,FINAL    ASCII diagram from a spec
  eer new --name Sol --desc "..." --layer 2
  eer run  --personality sol --input "I keep starting things and not finishing"
  eer ab   --personality sol --variants A_full,B_no_EMPA,D_first_order_only --input "..."

Default backend is the `claude` CLI. Add --mock for a deterministic offline dry-run
(structure only, no real text), or --api for the fast direct-API backend (one
persistent connection instead of a cold CLI launch per block — seconds, not minutes;
needs `pip install anthropic` + ANTHROPIC_API_KEY). Add --live to watch the pipeline
light up block by block. Add --judge to score soft metrics with an LLM judge
(noisy — always labelled as such).
"""
from __future__ import annotations
import argparse
import sys

from . import blocks as blockmod
from . import diagram as diagrammod
from .backend import make_backend
from .executor import run_graph
from .metrics import mechanical, judge, JUDGED
from .personality import Personality


def _live_printer():
    """A progress callback that draws the pipeline lighting up block by block.
    ASCII-only structural glyphs so it records cleanly in any terminal."""
    def cb(node, block, output, latency_ms, ran):
        name = block.name if block else node
        sym = block.symbol if block else f"[{node}]"
        dots = "." * max(3, 32 - len(name))
        lat = f"{latency_ms/1000:.1f}s" if latency_ms else ""
        status = "ok" if ran else "--"
        print(f"  {sym:7} {node:5} {name} {dots} {status} {lat:>6}", flush=True)
        peek = " ".join((output or "").split())
        if peek and node != "INPUT":
            tail = "..." if len(peek) > 60 else ""
            print(f"            > {peek[:60]}{tail}", flush=True)
    return cb


def _backend_kind(args) -> str:
    return "mock" if args.mock else ("api" if args.api else "claude")


def _variant_overrides(name: str) -> dict:
    """Map a variant name to mechanical graph overrides.
    Conventions: A_full / full = no change; no_<BLOCK>; first_order_only; only_<A+B+C>."""
    n = name.lower()
    if n in ("a_full", "full"):
        return {}
    if n in ("d_first_order_only", "first_order_only"):
        return {"enable_only": ["INPUT", "LIT", "RESP", "FINAL"]}
    if "no_" in n:
        block = name.split("no_", 1)[1].upper()
        return {"disable_nodes": [block]}
    if n.startswith("only_"):
        return {"enable_only": [b.upper() for b in name[5:].split("+")]}
    return {}


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))
    line = lambda cells: "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    print(line(headers))
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for r in rows:
        print(line(r))


def cmd_blocks(_a):
    rows = [[b.id, b.name, b.purpose] for b in blockmod.BLOCKS.values()]
    _print_table(["ID", "Name", "Purpose"], rows)


def cmd_graphs(_a):
    import os
    from .personality import GRAPHS_DIR
    for f in sorted(os.listdir(GRAPHS_DIR)):
        if f.endswith(".json"):
            print(f[:-5])


def cmd_diagram(a):
    print(diagrammod.render(a.spec))


def cmd_new(a):
    p = Personality(name=a.name, description=a.desc or "", persona_layer=a.layer,
                    graph_ref=a.graph)
    path = p.save()
    print(f"created personality '{a.name}' -> {path}")


def _run_one(p: Personality, utterance: str, backend, variant: str, progress=None):
    graph = p.resolve_graph()
    ov = _variant_overrides(variant)
    if ov:
        graph = graph.apply_variant(disable_nodes=ov.get("disable_nodes"),
                                    enable_only=ov.get("enable_only"))
    return run_graph(graph, utterance, backend, persona=p.persona_dict(),
                     prompt_overrides=p.block_prompts, variant_name=variant,
                     progress=progress)


def cmd_run(a):
    p = Personality.load(a.personality)
    backend = make_backend(_backend_kind(a), model=a.model)
    live = _live_printer() if a.live else None
    if live:
        print(f"\n  {p.name}  |  {a.input!r}\n")
    res = _run_one(p, a.input, backend, a.variant, progress=live)
    print(f"\n=== {p.name} / variant {a.variant} ===\n")
    print(res.final_expression)
    print("\n--- turn log (mechanical only) ---")
    _print_table(["Node", "Ran", "Latency(ms)", "OutHash"],
                 [[r.node, "y" if r.ran else "-", r.latency_ms, r.output_hash or "-"]
                  for r in res.turn_log])
    m = mechanical(res)
    print(f"\nmechanical: nodes_run={m['nodes_run']} "
          f"total_latency_ms={m['total_latency_ms']} final_chars={m['final_chars']}")
    if a.judge:
        jb = make_backend("api" if a.api else "claude", model=a.model)
        scored = judge(res, jb)
        _print_table(["Judged metric", "Value", "Source"],
                     [[k, "?" if v.value is None else f"{v.value:.2f}", v.source]
                      for k, v in scored.items()])


def cmd_ab(a):
    p = Personality.load(a.personality)
    backend = make_backend(_backend_kind(a), model=a.model)
    jb = make_backend("api" if a.api else "claude", model=a.model) if a.judge else None
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]
    rows = []
    finals = {}
    for v in variants:
        live = _live_printer() if a.live else None
        if live:
            print(f"\n  {p.name}  |  variant {v}\n")
        res = _run_one(p, a.input, backend, v, progress=live)
        finals[v] = res.final_expression
        m = mechanical(res)
        row = [v, m["nodes_run"], m["total_latency_ms"], m["final_chars"]]
        if jb is not None:
            scored = judge(res, jb)
            row += ["?" if scored[k].value is None else f"{scored[k].value:.2f}" for k in JUDGED]
        rows.append(row)
    headers = ["Variant", "nodes_run", "latency_ms", "final_chars"]
    if jb is not None:
        headers += JUDGED
    print(f"\n=== A/B on: {a.input!r} ===\n")
    _print_table(headers, rows)
    print("\n--- final expressions ---")
    for v, text in finals.items():
        print(f"\n[{v}]\n{text}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eer", description="Empathic Engine Researcher")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("blocks").set_defaults(func=cmd_blocks)
    sub.add_parser("graphs").set_defaults(func=cmd_graphs)

    d = sub.add_parser("diagram"); d.add_argument("spec"); d.set_defaults(func=cmd_diagram)

    n = sub.add_parser("new")
    n.add_argument("--name", required=True); n.add_argument("--desc", default="")
    n.add_argument("--layer", type=int, choices=[1, 2, 3]); n.add_argument("--graph", default="default")
    n.set_defaults(func=cmd_new)

    for name, fn in (("run", cmd_run), ("ab", cmd_ab)):
        s = sub.add_parser(name)
        s.add_argument("--personality", required=True)
        s.add_argument("--input", required=True)
        s.add_argument("--mock", action="store_true",
                       help="deterministic offline backend (no API)")
        s.add_argument("--api", action="store_true",
                       help="fast direct-API backend (needs `pip install anthropic` + ANTHROPIC_API_KEY)")
        s.add_argument("--live", action="store_true",
                       help="watch the pipeline light up block by block")
        s.add_argument("--judge", action="store_true")
        s.add_argument("--model", default=None)
        if name == "run":
            s.add_argument("--variant", default="A_full")
        else:
            s.add_argument("--variants", default="A_full,B_no_EMPA,D_first_order_only")
        s.set_defaults(func=fn)
    return p


def main(argv=None):
    # Windows stdout defaults to cp1252, which crashes on em-dashes / smart quotes in
    # model output. Decode as UTF-8 so real replies and the live view print cleanly.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
