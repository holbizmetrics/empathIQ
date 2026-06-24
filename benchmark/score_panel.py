"""Multi-judge panel over the stored battery outputs — tie-breaker pass.

The single-judge scorecard (score_battery.py) rated first_order >= A_full almost
everywhere, contradicting the qualitative battery. This panel tests whether that is a
real ranking or an artifact of one strict judge penalizing A_full's length/abstraction.
Method + decision rule pre-registered in README.md.

Three VARIANT-BLIND judges, each over all 22 outputs, differing in FRAMING (not just
resampling) so they span the suspected bias axis:
  J1 neutral · J2 depth-valuing (favors A_full) · J3 directness-valuing (favors first_order)

Each judge scores the 5 axes + a holistic `overall` in [0,1]. The tie-break reads the
`overall` ranking per judge (see pre-reg).

  python benchmark/score_panel.py --mock         # offline structure dry-run
  python benchmark/score_panel.py                 # real, 3x22 = 66 judge calls
  python benchmark/score_panel.py --only 5        # one category across all 3 judges
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
from eer.backend import make_backend  # noqa: E402
from score_battery import gather_outputs, load_prompts, AXES  # noqa: E402

BENCH = os.path.dirname(os.path.abspath(__file__))
PANEL_AXES = AXES + ["overall"]

_AXES_BLOCK = (
    "Score each in [0,1]:\n"
    "- frame_fit: answers the situation actually presented; not pulled into a wrong frame.\n"
    "- register_match: matches the emotional energy/tone the moment calls for.\n"
    "- format_adherence: follows any explicit format requested; else structural clarity.\n"
    "- instruction_following: does what is actually asked, vs a generic empathy dump.\n"
    "- restraint_appropriateness: comfort/recognition calibrated to what the moment "
    "warrants; both over-comforting and cold withholding score LOW.\n"
    "- overall: your holistic judgement of how good this reply is for this person.\n"
    "Return ONLY compact JSON with those six keys and no prose."
)

JUDGES = {
    "J1_neutral": (
        "You are a strict, calibrated, neutral evaluator of a single empathic reply. "
        "You favor no particular style. " + _AXES_BLOCK
    ),
    "J2_depth": (
        "You are an evaluator who values emotional DEPTH above all. A good reply sits "
        "with complexity, names what is underneath the words, and resists tidy or quick "
        "reassurance; a too-fast, too-neat, or surface reply is SHALLOW and should score "
        "low even if pleasant. Reward nuance and willingness to stay in the hard place. "
        + _AXES_BLOCK
    ),
    "J3_directness": (
        "You are an evaluator who values DIRECTNESS and actually meeting the person. A "
        "good reply answers what was said plainly and humanly; penalize over-processing, "
        "hedging, abstraction, therapy-speak, and replies that perform empathy instead "
        "of giving it. Length and polish are not virtues. " + _AXES_BLOCK
    ),
}


def score_one(backend, system, situation, reply):
    user = f"SITUATION:\n{situation}\n\nREPLY:\n{reply}"
    raw = backend.complete(system, user)
    start, end = raw.find("{"), raw.rfind("}")
    data = json.loads(raw[start:end + 1])
    return {a: float(data[a]) for a in PANEL_AXES if a in data}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", type=int, default=None)
    a = ap.parse_args()

    recs = gather_outputs()
    prompts = load_prompts()
    backend = make_backend("mock" if a.mock else "claude", model=a.model)

    cats = sorted({n for (n, _v) in recs})
    if a.only:
        cats = [n for n in cats if n == a.only]
    variants = ["A_full", "D_first_order_only"]

    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    tag = "mock" if a.mock else "real"
    out_path = os.path.join(BENCH, "results", f"panel-{stamp}-{tag}.jsonl")

    # scored[(judge, n, variant)] = {axis: val}
    scored: dict = {}
    with open(out_path, "w", encoding="utf-8") as out:
        for jname, jsys in JUDGES.items():
            for n in cats:
                situation = prompts[n]["prompt"]
                for v in variants:
                    rec = recs.get((n, v))
                    if rec is None:
                        continue
                    try:
                        s = score_one(backend, jsys, situation, rec["final_expression"])
                    except Exception as e:
                        s = {"error": f"{type(e).__name__}: {e}"}
                    row = {"judge": jname, "category_n": n,
                           "category_id": rec["category_id"], "variant": v,
                           "source": "llm-judge-panel", "scores": s}
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out.flush()
                    scored[(jname, n, v)] = s
                    ov = s.get("overall", "ERR" if "error" in s else "?")
                    print(f"  {jname:<14} #{n:<2} {rec['category_id'][:22]:<22} "
                          f"{v:<20} overall={ov}")

    print(f"\nwrote {out_path}")

    # --- tie-break read on `overall` ---
    print("\nPANEL overall (A_full / first_order) per judge — win = first_order >= A_full:")
    fo = "D_first_order_only"
    for jname in JUDGES:
        wins = 0
        cells = []
        for n in cats:
            af = scored.get((jname, n, "A_full"), {}).get("overall")
            fov = scored.get((jname, n, fo), {}).get("overall")
            if af is not None and fov is not None and fov >= af:
                wins += 1
            f = lambda x: "?" if x is None else f"{x:.2f}"
            cells.append(f"#{n}:{f(af)}/{f(fov)}")
        print(f"  {jname:<14} first_order_wins={wins}/{len(cats)}  | " + " ".join(cells))

    # cross-judge spread per category (on overall, averaged over variants)
    print("\nCross-judge disagreement (std of overall across J1/J2/J3, per category):")
    import statistics as st
    for n in cats:
        vals = []
        for v in variants:
            xs = [scored.get((j, n, v), {}).get("overall") for j in JUDGES]
            xs = [x for x in xs if x is not None]
            if len(xs) >= 2:
                vals.append(st.pstdev(xs))
        spread = sum(vals) / len(vals) if vals else float("nan")
        print(f"  #{n:<2} spread={spread:.3f}")


if __name__ == "__main__":
    main()
