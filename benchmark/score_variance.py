"""Multi-run CI scorer — puts a confidence interval + effect size on the
on-minus-baseline delta, so a result reads as REAL vs INDISTINGUISHABLE-FROM-NOISE
instead of a single bare number.

The status quo (score_battery.py) scores each stored reply with the judge ONCE and
prints a bare A_full/baseline table. A single judge reading is noisy by design — one
return is a reading, not a verdict. This re-scores the stored outputs K times and
summarizes the per-axis deltas with benchmark/ci.py (bootstrap 95% CI + Cohen's-d).

  python benchmark/score_variance.py --mock              # offline, synthetic judge, shows shape
  python benchmark/score_variance.py --runs 5            # real judge, 5 reads per output
  python benchmark/score_variance.py --runs 5 --only 9   # one category

Reads the latest stored reply per (category, variant) from results/*-real.jsonl (same
source as score_battery), re-judges each `--runs` times, and writes a timestamped
variance-report JSONL plus a per-axis CI table.

HONEST BOUNDARY — what this CI captures and what it does NOT:
  * captured: JUDGE-READING noise (re-judging the SAME text K times) + ACROSS-CATEGORY
    spread (the deltas vary by category). Pooled into one bootstrap per axis.
  * NOT captured: GENERATION variance — the architecture's reply itself varies run to
    run. The stored text is fixed here. To fold that in, re-run run_battery.py K times
    so results/ holds multiple generations, then this pools across all of them.
It also reports "is it real?" (CI) and "how big?" (d) — never "does it matter?" (the
practical-significance call is the reviewer's, by design; see ci.py).
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import random
import sys

try:  # Windows cp1252 stdout crashes on em-dashes/smart quotes in long runs
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BENCH)
ROOT = os.path.join(os.path.dirname(BENCH), "forge")
sys.path.insert(0, ROOT)

from eer.backend import make_backend                     # noqa: E402
from score_battery import gather_outputs, load_prompts, score_one, AXES  # noqa: E402
from ci import delta_ci, verdict                          # noqa: E402


def synthetic_score(n: int, variant: str, run: int, on: str, seed: int) -> dict:
    """Offline stand-in judge for --mock: deterministic-but-varied scores so the CI
    machinery is visibly exercised without API calls. Gives the `on` arm a small,
    consistent edge so the dry-run shows a believable REAL verdict. NOT a real judge —
    real runs use the claude/api backend + score_battery's JUDGE_SYSTEM."""
    rng = random.Random(f"{seed}|{n}|{variant}|{run}|synthetic-judge")
    edge = 0.12 if variant == on else 0.0
    return {ax: max(0.0, min(1.0, 0.55 + edge + rng.gauss(0, 0.06))) for ax in AXES}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3, help="judge reads per stored output (K)")
    ap.add_argument("--mock", action="store_true", help="offline synthetic judge (shows shape)")
    ap.add_argument("--api", action="store_true", help="direct Anthropic API judge backend")
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", type=int, default=None, help="category n to score just one")
    ap.add_argument("--on", default="A_full", help="the architecture-on arm")
    ap.add_argument("--baseline", default="D_first_order_only", help="the ablation/baseline arm")
    ap.add_argument("--confidence", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=0, help="bootstrap + synthetic-judge seed")
    ap.add_argument("--personality", default=None,
                    help="score only this personality's runs (required when the results "
                         "store mixes personalities)")
    a = ap.parse_args()

    recs = gather_outputs(a.personality)
    prompts = load_prompts()
    on, base = a.on, a.baseline

    cats = sorted({n for (n, _v) in recs})
    if a.only:
        cats = [n for n in cats if n == a.only]
    if not cats:
        sys.exit("no stored outputs found in results/*-real.jsonl (run run_battery.py first)")

    backend = None if a.mock else make_backend("api" if a.api else "claude", model=a.model)

    # scores[(run, n, variant)] = {axis: val} | {"error": ...}
    scores: dict = {}
    total = a.runs * len(cats) * 2
    done = 0
    for run in range(a.runs):
        for n in cats:
            situation = prompts[n]["prompt"]
            for v in (on, base):
                rec = recs.get((n, v))
                if rec is None:
                    continue
                done += 1
                if a.mock:
                    s = synthetic_score(n, v, run, on, a.seed)
                else:
                    try:
                        # score_one returns (scores_dict, raw_judge_text) — unpack it;
                        # storing the whole tuple made every axis lookup miss (n=0 -> "insufficient").
                        s, _raw = score_one(backend, situation, rec["final_expression"])
                    except Exception as e:  # a noisy judge call must not lose the run
                        s = {"error": f"{type(e).__name__}: {e}"}
                scores[(run, n, v)] = s
                tag = "ERR" if "error" in s else "ok"
                print(f"  [{done:>3}/{total}] run{run} #{n:<2} {v:<20} {tag}", flush=True)

    # per-axis pooled deltas across (run x category), where both arms scored cleanly
    per_axis: dict = {}
    for ax in AXES:
        deltas = []
        for run in range(a.runs):
            for n in cats:
                so = scores.get((run, n, on), {})
                sb = scores.get((run, n, base), {})
                if ax in so and ax in sb:
                    deltas.append(so[ax] - sb[ax])
        per_axis[ax] = delta_ci(deltas, confidence=a.confidence, seed=a.seed)

    os.makedirs(os.path.join(BENCH, "results"), exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    tag = "mock" if a.mock else "real"
    out_path = os.path.join(BENCH, "results", f"variance-{stamp}-{tag}.jsonl")
    with open(out_path, "w", encoding="utf-8") as out:
        meta = {"kind": "variance-report", "runs": a.runs, "on": on, "baseline": base,
                "categories": cats, "confidence": a.confidence,
                "backend": "synthetic-mock" if a.mock else (backend.name if backend else "?"),
                "captures": "judge-reading-noise + across-category-spread",
                "not_captured": "generation-variance (stored replies are fixed)"}
        out.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for ax, c in per_axis.items():
            out.write(json.dumps({"axis": ax, **c}, ensure_ascii=False) + "\n")

    print(f"\nwrote {out_path}")
    print(f"\nDELTA CI  ({on} minus {base}), K={a.runs} judge reads x {len(cats)} categories")
    print(f"  reports 'is it real?' (CI) and 'how big?' (d) — NOT 'does it matter?' (your call)\n")
    print(f"  {'axis':<26} {'mean':>7}  {'95% CI':>18}  {'n':>3}  {'real?':<6} {'effect':>14}")
    print("  " + "-" * 78)
    for ax, c in per_axis.items():
        if c["insufficient"]:
            print(f"  {ax:<26} {('%+.3f' % c['mean']) if c['mean'] is not None else '   -':>7}"
                  f"  {'(n<2: insufficient)':>18}  {c['n']:>3}  {'-':<6} {'n/a':>14}")
            continue
        ci_str = f"[{c['lo']:+.3f},{c['hi']:+.3f}]"
        real = "REAL" if c["real"] else "noise"
        d_str = "n/a" if c["d"] is None else f"{c['d']:+.2f} ({c['d_label']})"
        print(f"  {ax:<26} {c['mean']:>+7.3f}  {ci_str:>18}  {c['n']:>3}  {real:<6} {d_str:>14}")

    print(f"\n  note: CI captures judge-reading noise + across-category spread; it does NOT")
    print(f"  capture generation variance (stored replies are fixed). Re-run run_battery.py")
    print(f"  K times and re-point this to pool generations too.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  interrupted (Ctrl-C). Any completed scores were already saved to "
              "benchmark/results/.", flush=True)
        sys.exit(130)
