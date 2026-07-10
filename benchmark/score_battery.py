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


def gather_outputs(personality: str | None = None) -> dict:
    """Latest stored record per (category_n, variant), optionally filtered to one
    personality. REFUSES a mixed-personality store when no filter is given: runs of
    different personalities sharing a variant name (Sol A_full vs Sol-FA A_full) would
    silently alias into one arm, latest-wins — a scored delta would then compare
    across personalities without saying so. score_panel and score_variance import this,
    so the refusal guards all three scorers."""
    recs: dict[tuple[int, str], dict] = {}
    seen: set[str] = set()
    files = sorted(glob.glob(os.path.join(BENCH, "results", "*-real.jsonl")))
    for f in files:  # sorted ascending → later files overwrite earlier (keep latest)
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if "final_expression" not in d:
                continue
            # Case-insensitive exact match: --personality sol and Sol both select the
            # stored "Sol" records, but neither matches "Sol-FA" (exact, not prefix).
            if personality and d.get("personality", "").lower() != personality.lower():
                continue
            seen.add(d.get("personality", "?"))
            recs[(d["category_n"], d["variant"])] = d
    if personality is None and len(seen) > 1:
        raise SystemExit(
            f"REFUSING to score: stored real outputs mix personalities {sorted(seen)} -- "
            f"same-named variants would silently alias into one arm (latest-wins). "
            f"Pass --personality <name> to pick whose runs to score.")
    return recs


def load_prompts() -> dict:
    with open(os.path.join(BENCH, "prompts.json"), encoding="utf-8") as f:
        return {c["n"]: c for c in json.load(f)["categories"]}


def _indent(text: str, prefix: str = "    | ") -> str:
    return "\n".join(prefix + ln for ln in (text or "").splitlines())


def score_one(backend, situation: str, reply: str):
    """Returns (scores_or_error_dict, raw_judge_text). Never raises — a noisy judge
    must not lose the run; the caller decides how to surface an error row."""
    user = f"SITUATION:\n{situation}\n\nREPLY:\n{reply}"
    try:
        raw = backend.complete(JUDGE_SYSTEM, user)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}, ""
    try:
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end + 1])
        return {a: float(data[a]) for a in AXES if a in data}, raw
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}, raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", type=int, default=None, help="category n to score just one")
    ap.add_argument("--personality", default=None,
                    help="score only this personality's runs (required when the results "
                         "store mixes personalities)")
    ap.add_argument("--live", "--verbose", "-v", "--full", dest="live", action="store_true",
                    help="show the FULL reply being judged + the judge's full response, per item "
                         "(no truncation)")
    a = ap.parse_args()

    recs = gather_outputs(a.personality)
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
    total = sum(1 for n in cats for v in variants if recs.get((n, v)) is not None)
    print(f"scoring {total} (category, variant) pairs with a single {backend.name} judge "
          f"(~{total} calls; each is a cold CLI launch, so a full run takes a few minutes)...",
          flush=True)
    k = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for n in cats:
            situation = prompts[n]["prompt"]
            for v in variants:
                rec = recs.get((n, v))
                if rec is None:
                    continue
                k += 1
                tag = f"  [{k:>2}/{total}] #{n:<2} {rec['category_id'][:24]:<24} {v:<20}"
                reply = rec["final_expression"]
                if a.live:                                    # -v/--verbose/--live/--full: FULL reply, no cutoff
                    print(f"\n{tag}\n    --- reply being judged ---")
                    print(_indent(reply), flush=True)
                    print("    judging...", flush=True)
                s, raw = score_one(backend, situation, reply)
                row = {"category_n": n, "category_id": rec["category_id"],
                       "variant": v, "source": "llm-judge-single",
                       "scores": s}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                scored[(n, v)] = s
                ok = "ERR" if "error" in s else " ".join(f"{a_}={s.get(a_, '?')}" for a_ in AXES)
                if a.live:                                    # the judge's FULL verdict, no cutoff
                    print("    --- judge said ---")
                    print(_indent(raw), flush=True)
                    print(f"{tag} {ok}\n", flush=True)
                else:                                         # default: counter + result, never silent
                    print(f"{tag} {ok}", flush=True)

    print(f"\nwrote {out_path}")
    print("\nSCORECARD (A_full | first_order), single-judge — noisy by design:")
    labels = {"frame_fit": "frame", "register_match": "reg", "format_adherence": "fmt",
              "instruction_following": "instr", "restraint_appropriateness": "restr"}
    cw = 9  # width of an "A.AA/D.DD" cell
    catw = max([len("category")] + [len(prompts[n]["id"]) for n in cats])
    head = f"  {'#':>2}  {'category':<{catw}}  " + "  ".join(f"{labels[ax]:<{cw}}" for ax in AXES)
    print(head)
    print("  " + "-" * (len(head) - 2))
    fmt = lambda x: "?" if x is None else f"{x:.2f}"

    def _cell(n, ax):
        af = scored.get((n, "A_full"), {}).get(ax)
        fo = scored.get((n, "D_first_order_only"), {}).get(ax)
        return f"{fmt(af)}/{fmt(fo)}".ljust(cw)

    for n in cats:
        row = "  ".join(_cell(n, ax) for ax in AXES)
        print(f"  {n:>2}  {prompts[n]['id']:<{catw}}  {row}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  interrupted (Ctrl-C). Any completed scores were already saved to "
              "benchmark/results/.", flush=True)
        sys.exit(130)
