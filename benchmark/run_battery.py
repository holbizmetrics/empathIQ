"""Run the EmpathiQ category battery through the EER engine via the `ab` path.

Wires benchmark/prompts.json (one eliciting prompt per category) into the engine and
runs each across architecture variants, collecting MECHANICAL metrics + the final
expression. Grading is DEFERRED by design: this collects outputs to observe, it does
not score them (no --judge here). The judged competence scorecard is a later pass.

  python benchmark/run_battery.py --mock                         # full battery, offline, instant
  python benchmark/run_battery.py --only humor_warm_performative # one category, real backend
  python benchmark/run_battery.py --variants A_full,B_no_EMPA --personality sol

Writes a timestamped JSONL to benchmark/results/ and prints a compact mechanical table.
Each real (non-mock) run is ~nodes_run `claude` CLI calls, so the full real battery is
hundreds of calls — scope with --only / --variants before going wide.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import sys

try:  # Windows cp1252 stdout crashes on em-dashes/smart quotes in long runs
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forge")
sys.path.insert(0, ROOT)
from eer.backend import make_backend            # noqa: E402
from eer.cli import _variant_overrides, _run_one, _active_node_count  # noqa: E402
from eer.metrics import mechanical               # noqa: E402
from eer.personality import Personality          # noqa: E402
from eer.voice import BackgroundSpeaker, stop_speaking  # noqa: E402

BENCH = os.path.dirname(os.path.abspath(__file__))


def load_prompts() -> list[dict]:
    with open(os.path.join(BENCH, "prompts.json"), encoding="utf-8") as f:
        return json.load(f)["categories"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--personality", default="sol")
    ap.add_argument("--variants", default="A_full,B_no_EMPA,D_first_order_only")
    ap.add_argument("--only", default=None, help="category id to run just one")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--api", action="store_true",
                    help="direct Anthropic API backend (fast; needs `pip install anthropic` + ANTHROPIC_API_KEY)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--timeout", type=int, default=300,
                    help="per-block claude CLI timeout (s); a stalled block is recorded, not fatal")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="show a preview of each block's output as it completes")
    ap.add_argument("--speak", action="store_true",
                    help="read each block aloud as it lands (heavy — best scoped with --only/--variants)")
    a = ap.parse_args()

    cats = load_prompts()
    if a.only:
        cats = [c for c in cats if c["id"] == a.only]
        if not cats:
            sys.exit(f"no category id {a.only!r}")
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]

    p = Personality.load(a.personality)
    kind = "mock" if a.mock else ("api" if a.api else "claude")
    backend = make_backend(kind, model=a.model, timeout=a.timeout)

    os.makedirs(os.path.join(BENCH, "results"), exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    tag = "mock" if a.mock else "real"
    out_path = os.path.join(BENCH, "results", f"battery-{stamp}-{tag}.jsonl")

    rows = []
    speaker = BackgroundSpeaker() if a.speak else None
    with open(out_path, "w", encoding="utf-8") as out:
        for c in cats:
            for v in variants:
                n_blocks = _active_node_count(p, v) + 1  # +1 for the free INPUT block
                print(f"  run   #{c['n']:<2} {c['id'][:22]:<22} {v:<20} "
                      f"{n_blocks} blocks via {backend.name} ...", flush=True)
                seen = {"k": 0}
                def _progress(node, block, output, dt, ran, _tot=n_blocks, _s=seen,
                              _vb=a.verbose, _sp=speaker):
                    _s["k"] += 1
                    print(f"        [{_s['k']:>2}/{_tot}] {node:<6} "
                          f"{'ok ' if ran else 'XX '}{dt / 1000:5.1f}s", flush=True)
                    if _vb and output:
                        prev = " ".join(output.split())
                        print(f"               > {prev[:240]}{'...' if len(prev) > 240 else ''}",
                              flush=True)
                    if _sp is not None and ran and output and node != "INPUT":
                        _sp.say(output)   # narrate the FULL block text, overlapping the next
                try:
                    res = _run_one(p, c["prompt"], backend, v, progress=_progress)
                except Exception as e:  # one stalled/failed block must not lose the battery
                    rec = {"category_n": c["n"], "category_id": c["id"], "label": c["label"],
                           "persona": c["persona"], "personality": p.name, "variant": v,
                           "backend": backend.name, "error": f"{type(e).__name__}: {e}"}
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out.flush()
                    rows.append([c["n"], c["id"][:22], v, "ERR", "-", "-"])
                    print(f"  ERROR #{c['n']:<2} {c['id'][:22]:<22} {v:<20} {type(e).__name__}")
                    continue
                m = mechanical(res)
                rec = {
                    "category_n": c["n"], "category_id": c["id"], "label": c["label"],
                    "persona": c["persona"], "personality": p.name, "variant": v,
                    "backend": backend.name, "mechanical": m,
                    "final_expression": res.final_expression,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                rows.append([c["n"], c["id"][:22], v, m["nodes_run"],
                             m["total_latency_ms"], m["final_chars"]])
                print(f"  done  #{c['n']:<2} {c['id'][:22]:<22} {v:<20} "
                      f"nodes={m['nodes_run']:<2} chars={m['final_chars']}")

    if speaker is not None:
        speaker.close()

    print(f"\nwrote {out_path}  ({len(rows)} runs, grading deferred)")
    print("\nMECHANICAL SUMMARY (no judged metrics by design):")
    hdr = ["#", "category", "variant", "nodes", "latency_ms", "chars"]
    w = [max(len(str(r[i])) for r in ([hdr] + rows)) for i in range(len(hdr))]
    fmt = lambda r: " | ".join(str(c).ljust(w[i]) for i, c in enumerate(r))
    print(fmt(hdr)); print("-+-".join("-" * x for x in w))
    for r in rows:
        print(fmt(r))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_speaking()
        print("\n  interrupted (Ctrl-C). Any completed runs were already saved to "
              "benchmark/results/.", flush=True)
        sys.exit(130)
