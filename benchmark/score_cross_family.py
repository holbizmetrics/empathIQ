"""Score one or more non-Claude judge returns against the blind key.

Usage:
  python benchmark/score_cross_family.py <judge-reply.json> [<judge2.json> ...] \
      --key benchmark/results/cross-family-KEY-<stamp>.json

Each <judge-reply.json> is exactly what a non-Claude judge returns from the packet:
  {"scores": [{"category": 1, "A": {...,"overall":x}, "B": {...,"overall":y}}, ...]}
(A bare top-level list of those objects is also accepted.)

De-blinds A/B back to {on, baseline} via the private key, then reports two things:
  1. on-minus-baseline OVERALL delta (the thesis headline: did the architecture help?),
     plus per-axis deltas — averaged across categories and judges.
  2. baseline-wins/N, the "ablation survives" count (baseline.overall >= on.overall),
     the cross-family analog of the same-family panel's surprising first_order >= A_full.

With >=2 judge files it also reports INTER-RATER agreement (per PROTOCOL.md #5): the
fraction of categories where the judges agree on the winner. A single judge is noisy by
design — one return is a reading, not a verdict.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass


def _rows(raw) -> list:
    return raw["scores"] if isinstance(raw, dict) and "scores" in raw else raw


def aggregate(key: dict, judges: list[list]) -> dict:
    """PURE: key (from make_cross_family_packet) + a list of judges' row-lists -> verdict dict."""
    cat_key = key["categories"]
    on, baseline = key["on"], key["baseline"]
    axes = [a for a in key.get("scale", ["overall"]) if a != "overall"]

    per_judge = []
    # per_category[n] = list of (delta, winner) across judges, for inter-rater
    per_category: dict[str, list] = {n: [] for n in cat_key}

    for ji, rows in enumerate(judges):
        by_cat = {str(r["category"]): r for r in rows}
        cats_scored = []
        baseline_wins = 0
        axis_deltas = {ax: [] for ax in axes}
        overall_deltas = []
        for n, kn in cat_key.items():
            r = by_cat.get(n)
            if not r:
                continue
            on_slot = "A" if kn["A"] == on else "B"
            base_slot = "A" if kn["A"] == baseline else "B"
            try:
                on_ov = float(r[on_slot]["overall"])
                base_ov = float(r[base_slot]["overall"])
            except (KeyError, TypeError, ValueError):
                continue
            d = on_ov - base_ov
            overall_deltas.append(d)
            winner = baseline if base_ov >= on_ov else on
            baseline_wins += (base_ov >= on_ov)
            for ax in axes:
                try:
                    axis_deltas[ax].append(float(r[on_slot][ax]) - float(r[base_slot][ax]))
                except (KeyError, TypeError, ValueError):
                    pass
            cats_scored.append(n)
            per_category[n].append({"delta": d, "winner": winner, "judge": ji})

        mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
        per_judge.append({
            "judge": ji,
            "scored": len(cats_scored),
            "baseline_wins": baseline_wins,
            "mean_overall_delta": mean(overall_deltas),
            "per_axis_delta": {ax: mean(v) for ax, v in axis_deltas.items()},
        })

    # inter-rater agreement on the per-category winner (only categories ≥2 judges scored)
    inter = None
    if len(judges) >= 2:
        agreed = total = 0
        for n, lst in per_category.items():
            if len(lst) >= 2:
                total += 1
                agreed += len({x["winner"] for x in lst}) == 1
        inter = {"categories_multi_scored": total,
                 "winner_agreement": round(agreed / total, 4) if total else None}

    all_deltas = [x["delta"] for lst in per_category.values() for x in lst]
    return {
        "on": on, "baseline": baseline, "seed": key.get("seed"),
        "n_categories_in_key": len(cat_key),
        "n_judges": len(judges),
        "per_judge": per_judge,
        "mean_overall_delta_all": round(sum(all_deltas) / len(all_deltas), 4) if all_deltas else None,
        "inter_rater": inter,
        "per_category": {n: per_category[n] for n in cat_key if per_category[n]},
    }


def _verdict_lines(v: dict) -> list[str]:
    on, base = v["on"], v["baseline"]
    out = [f"cross-family judge result — on={on} vs baseline={base} (seed {v['seed']}, "
           f"{v['n_judges']} judge(s), {v['n_categories_in_key']} categories in key)", "-" * 64]
    for pj in v["per_judge"]:
        out.append(f"  judge {pj['judge']}: scored {pj['scored']}  "
                   f"baseline_wins {pj['baseline_wins']}/{pj['scored']}  "
                   f"mean(on-baseline overall delta) = {pj['mean_overall_delta']}")
    out.append("-" * 64)
    d = v["mean_overall_delta_all"]
    out.append(f"HEADLINE  mean on-minus-baseline overall delta (all judges): {d}")
    if d is not None:
        if d > 0:
            out.append(f"  -> architecture-ON scores higher than {base} cross-family (delta>0). "
                       "Thesis-consistent — magnitude/significance is the next question.")
        else:
            out.append(f"  -> {base} matches or beats architecture-ON cross-family (delta<=0). "
                       "The same-family 'ablation survives' result holds across families — "
                       "a real model-level finding, not a self-preference artifact.")
    if v["inter_rater"] is not None:
        ir = v["inter_rater"]
        out.append(f"INTER-RATER  judges agree on the winner in {ir['winner_agreement']} of "
                   f"{ir['categories_multi_scored']} co-scored categories.")
    else:
        out.append("INTER-RATER  n/a (single judge — noisy by design; add a 2nd judge or a "
                   "human-scored sample per judge/PROTOCOL.md #5).")
    return out


def _detail_lines(v: dict) -> list[str]:
    """The full per-category breakdown — the -v/--full detail (else only in --json)."""
    out = ["", "per-category detail (on-minus-baseline overall delta -> winner, per judge):", "-" * 64]
    for n, lst in v["per_category"].items():
        parts = "  ".join(f"j{x['judge']}: {x['delta']:+.2f}->{x['winner']}" for x in lst)
        out.append(f"  #{n:<3} {parts}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Score cross-family judge returns against the blind key")
    ap.add_argument("scores", nargs="+", help="one or more judge-reply JSON files")
    ap.add_argument("--key", required=True, help="the private cross-family-KEY-<stamp>.json")
    ap.add_argument("--json", action="store_true", help="emit the verdict dict as JSON")
    ap.add_argument("--live", "--verbose", "-v", "--full", dest="live", action="store_true",
                    help="also print the full per-category delta/winner breakdown")
    a = ap.parse_args(argv)

    key = json.load(open(a.key, encoding="utf-8"))
    judges = [_rows(json.load(open(f, encoding="utf-8"))) for f in a.scores]
    v = aggregate(key, judges)
    if a.json:
        print(json.dumps(v, indent=2))
    else:
        print("\n".join(_verdict_lines(v)))
        if a.live:
            print("\n".join(_detail_lines(v)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
