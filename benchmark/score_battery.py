"""Judged competence scorecard over the stored battery outputs.

The battery (run_battery.py) collected outputs with grading DEFERRED. This is the
deferred pass: it scores each stored reply on 5 competence axes with a single LLM
judge. Two disciplines are baked in (see README.md):

  * VARIANT-BLIND — the judge sees only (situation, reply), never which architecture
    produced it and never the battery's qualitative observations. Leak-line discipline.
  * NOISE-HONEST — one judge call per output, no panel; every score carries
    source="llm-judge-single". We do not pretend a single noisy judge is ground truth.

  python benchmark/score_battery.py --mock              # offline structure dry-run
  python benchmark/score_battery.py                      # real judge over all 22 outputs
  python benchmark/score_battery.py --only 9             # one category

Reads the latest stored output per (category, variant) from benchmark/results/*-real.jsonl,
maps each to its eliciting prompt from prompts.json, and writes a timestamped
scorecard JSONL plus an A_full-vs-first_order table per axis.
"""
from __future__ import annotations
import argparse
import datetime as dt
import glob
import json
import os
import sys

try:  # Windows cp1252 stdout crashes on em-dashes/smart quotes in long runs
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forge")
sys.path.insert(0, ROOT)
from eer.backend import make_backend  # noqa: E402

BENCH = os.path.dirname(os.path.abspath(__file__))
AXES = ["frame_fit", "register_match", "format_adherence",
        "instruction_following", "restraint_appropriateness"]

JUDGE_SYSTEM = (
    "You are a strict, calibrated evaluator of a single empathic reply to a person's "
    "message. You will be given the SITUATION (what the person said) and the REPLY. "
    "Score the reply on exactly these five axes, each a float in [0,1]:\n"
    "- frame_fit: answers the situation actually presented; not pulled into a wrong "
    "frame the message projects (e.g. treating a serious disclosure as a performance, "
    "or vice versa). 1=stays in the right frame, 0=wrong frame.\n"
    "- register_match: matches the emotional energy/tone the moment calls for "
    "(playful vs grave, high-arousal vs calm). 1=matched, 0=mismatched.\n"
    "- format_adherence: follows any explicit format the message requests (e.g. a "
    "think/feel split). If no format is requested, score on structural clarity. "
    "1=followed/clear, 0=ignored/muddled.\n"
    "- instruction_following: does what is actually asked, rather than a generic "
    "empathy dump. 1=on-task, 0=generic.\n"
    "- restraint_appropriateness: offers comfort/reassurance/recognition only to the "
    "degree the situation warrants. BOTH over-comforting (when the moment calls for "
    "accountability, or just holding space) AND cold withholding score LOW; calibrated "
    "restraint scores HIGH. 1=calibrated, 0=miscalibrated.\n"
    "Return ONLY compact JSON with those five keys and no prose."
)


def gather_outputs() -> dict:
    """Latest stored record per (category_n, variant)."""
    recs: dict[tuple[int, str], dict] = {}
    files = sorted(glob.glob(os.path.join(BENCH, "results", "*-real.jsonl")))
    for f in files:  # sorted ascending → later files overwrite earlier (keep latest)
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if "final_expression" not in d:
                continue
            recs[(d["category_n"], d["variant"])] = d
    return recs


def load_prompts() -> dict:
    with open(os.path.join(BENCH, "prompts.json"), encoding="utf-8") as f:
        return {c["n"]: c for c in json.load(f)["categories"]}


def score_one(backend, situation: str, reply: str) -> dict:
    user = f"SITUATION:\n{situation}\n\nREPLY:\n{reply}"
    raw = backend.complete(JUDGE_SYSTEM, user)
    start, end = raw.find("{"), raw.rfind("}")
    data = json.loads(raw[start:end + 1])
    return {a: float(data[a]) for a in AXES if a in data}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", type=int, default=None, help="category n to score just one")
    a = ap.parse_args()

    recs = gather_outputs()
    prompts = load_prompts()
    backend = make_backend("mock" if a.mock else "claude", model=a.model)

    cats = sorted({n for (n, _v) in recs})
    if a.only:
        cats = [n for n in cats if n == a.only]
    variants = ["A_full", "D_first_order_only"]

    os.makedirs(os.path.join(BENCH, "results"), exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    tag = "mock" if a.mock else "real"
    out_path = os.path.join(BENCH, "results", f"scorecard-{stamp}-{tag}.jsonl")

    scored: dict[tuple[int, str], dict] = {}
    with open(out_path, "w", encoding="utf-8") as out:
        for n in cats:
            situation = prompts[n]["prompt"]
            for v in variants:
                rec = recs.get((n, v))
                if rec is None:
                    continue
                try:
                    s = score_one(backend, situation, rec["final_expression"])
                except Exception as e:  # noisy judge must not lose the run
                    s = {"error": f"{type(e).__name__}: {e}"}
                row = {"category_n": n, "category_id": rec["category_id"],
                       "variant": v, "source": "llm-judge-single",
                       "scores": s}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                scored[(n, v)] = s
                ok = "ERR" if "error" in s else " ".join(f"{a_}={s.get(a_, '?')}" for a_ in AXES)
                print(f"  #{n:<2} {rec['category_id'][:24]:<24} {v:<20} {ok}")

    print(f"\nwrote {out_path}")
    print("\nSCORECARD (A_full | first_order), single-judge — noisy by design:")
    hdr = ["#", "category"] + [ax[:6] for ax in AXES]
    print(" | ".join(hdr))
    for n in cats:
        cid = prompts[n]["id"][:20]
        cells = [str(n), cid]
        for ax in AXES:
            af = scored.get((n, "A_full"), {}).get(ax)
            fo = scored.get((n, "D_first_order_only"), {}).get(ax)
            fmt = lambda x: "?" if x is None else f"{x:.2f}"
            cells.append(f"{fmt(af)}/{fmt(fo)}")
        print(" | ".join(cells))


if __name__ == "__main__":
    main()
