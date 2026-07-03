"""Generate a VARIANT-BLIND cross-family judge packet over the stored battery outputs.

This is the win-condition harness: empathIQ's whole thesis ("a bounded-empathic
architecture beats its ablations") is only *settled* by a judge from a DIFFERENT model
family than the one the architecture runs on, scoring blind to which arm produced which
reply. The same-family scorers already here (`score_battery` single-judge, `score_panel`
3-framing panel) test the instrument; they can never test the thesis — a Claude-level
blind spot reads as the strong agreement we saw. This packet lets a NON-Claude judge
(GPT / Gemini / Grok / a human) score the same outputs blind.

It does NOT call the external model — by design. You paste the packet into another family
(or hand it to a human), then feed the returned JSON to `score_cross_family.py`. The
external *run* is operator-couriered; the harness is everything around it.

  python benchmark/make_cross_family_packet.py                       # on=A_full vs baseline=D_first_order_only
  python benchmark/make_cross_family_packet.py --on A_full --baseline B_no_EMPA
  python benchmark/make_cross_family_packet.py --seed 20260628

Writes (into benchmark/results/, which is gitignored — the KEY must never be committed
or pasted):
  cross-family-packet-<stamp>.md    <- PASTE THIS into a non-Claude model. No arm labels.
  cross-family-KEY-<stamp>.json     <- PRIVATE de-blinding (category -> {A,B} -> variant).

Blinding: per category the two replies show as Reply A / Reply B with the A/B<->arm
assignment randomized under a FIXED, recorded SEED, so the blind run is reproducible and
auditable per the lab's pre-registration discipline.

Scale: the 5 competence axes + a holistic `overall` (same scale as score_battery, so a
cross-family run is directly comparable to the same-family panel). The rubric C1-C10
absolute mode (with the held-out C10 moral-courage anchors) is the next extension — it is
blocked on the human-rated anchors that are deliberately NOT in this public repo.
"""
from __future__ import annotations
import argparse
import datetime as dt
import glob
import json
import os
import random
import re
import sys

try:  # Windows cp1252 stdout crashes on em-dashes/smart quotes in long packets
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BENCH, "results")

# 5 competence axes + overall — names match score_battery.AXES so cross-family and
# same-family scorecards are directly comparable.
AXES = [
    ("frame_fit", "answers the situation actually presented; not pulled into a wrong frame the message projects."),
    ("register_match", "matches the emotional energy/tone the moment calls for (playful vs grave, calm vs urgent)."),
    ("format_adherence", "follows any explicit format the message requests; if none requested, scored on structural clarity."),
    ("instruction_following", "does what is actually asked, vs a generic empathy dump."),
    ("restraint_appropriateness", "offers comfort/reassurance only to the degree warranted. BOTH over-comforting (when the moment calls for accountability or just holding) AND cold withholding score LOW; calibrated scores HIGH."),
]


def gather_outputs(results_dir: str = RESULTS, pattern: str = "*-real.jsonl",
                   personality: str | None = None) -> dict:
    """Latest stored record per (category_n, personality, variant) from the battery
    JSONLs. Default reads only real (judge-worthy) outputs; pass pattern='*-mock.jsonl'
    to dry-run the full pipeline shape without spending real model calls.
    `personality` filters records to one personality — without it, runs of different
    personalities that share a variant name (e.g. Sol A_full and Sol-FA A_full) would
    silently alias into the same arm, latest-wins. main() refuses that mix unless the
    arms are personality-qualified ('Sol-FA:A_full')."""
    recs: dict[tuple[int, str, str], dict] = {}
    for f in sorted(glob.glob(os.path.join(results_dir, pattern))):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if personality and d.get("personality") != personality:
                continue
            if "final_expression" in d:
                recs[(d["category_n"], d.get("personality", "?"), d["variant"])] = d
    return recs


def parse_arm(spec: str, default_personality: str | None) -> tuple[str | None, str]:
    """'Sol-FA:A_full' -> ('Sol-FA', 'A_full'); bare 'A_full' -> (default_personality,
    'A_full'). Personality-qualified arms let one packet compare across personalities
    (e.g. the frame-aware fix vs the original) — variants alone can't express that."""
    if ":" in spec:
        pers, variant = spec.split(":", 1)
        return pers, variant
    return default_personality, spec


def find_blindness_leaks(cats: dict, arms: tuple[str, ...], terms: set[str]) -> list[tuple[int, str, str]]:
    """Scan the output texts that would enter the packet for arm-identifying strings
    (variant names, personality names). A single leaked name unblinds the judge on
    contact — refuse to build rather than ship a compromised packet. Word-boundary
    match so 'Sol' does not fire on 'solve'/'console'."""
    leaks: list[tuple[int, str, str]] = []
    for n, block in cats.items():
        for arm in arms:
            text = block.get(arm)
            if not text:
                continue
            for t in sorted(terms):
                if t and re.search(rf"(?<!\w){re.escape(t)}(?!\w)", text, re.IGNORECASE):
                    leaks.append((n, arm, t))
    return leaks


def load_prompts() -> dict:
    with open(os.path.join(BENCH, "prompts.json"), encoding="utf-8") as f:
        return {c["n"]: c for c in json.load(f)["categories"]}


def pivot(recs: dict, prompts: dict, arms: dict[str, tuple[str | None, str]]) -> dict:
    """{(n,personality,variant):rec} + prompts + {arm_label:(personality,variant)} ->
    {n: {"__meta":(id,label,situation), arm_label:text}}. A record feeds an arm when its
    variant matches and its personality matches (an arm personality of None matches any —
    only legal once main() has established the stored set is single-personality)."""
    cats: dict[int, dict] = {}
    for (n, pers, variant), rec in recs.items():
        for arm_label, (arm_pers, arm_variant) in arms.items():
            if variant != arm_variant or (arm_pers is not None and pers != arm_pers):
                continue
            meta = prompts.get(n, {})
            cats.setdefault(n, {})["__meta"] = (
                rec.get("category_id", meta.get("id", str(n))),
                rec.get("label", meta.get("label", "")),
                meta.get("prompt", "(situation text unavailable — prompts.json has no entry for this category)"),
            )
            cats[n][arm_label] = rec["final_expression"]
    return cats


def build_packet(cats: dict, on: str, baseline: str, seed: int) -> tuple[str, dict, list[int]]:
    """PURE: build (packet_markdown, key, skipped_categories). Randomizes A/B per category
    under `seed` so a peer can reproduce the exact blinding from the key."""
    rng = random.Random(seed)
    key = {
        "seed": seed,
        "on": on,
        "baseline": baseline,
        "scale": [name for name, _ in AXES] + ["overall"],
        "note": "A/B map to {on, baseline} per category below. Headline = on-minus-baseline "
                "overall delta (and baseline-wins/N, the ablation-survives count).",
        "categories": {},
    }
    skipped: list[int] = []
    L: list[str] = []
    L.append("# Cross-family empathy-architecture judge — BLIND scoring task\n")
    L.append("You are an impartial judge of short empathic replies. For each SITUATION below you")
    L.append("are given two replies, **Reply A** and **Reply B**, produced by two different and")
    L.append("UNDISCLOSED systems. You do not know which system produced which reply; do not guess.")
    L.append("Score each reply **independently** on 5 axes, each a real number in **[0,1]**, plus a")
    L.append("holistic `overall` in [0,1]. Use the full range; do not anchor everything to 0.5.\n")
    L.append("## Axes (neutral definitions — no per-situation 'right answer' is given to you)")
    for i, (name, desc) in enumerate(AXES, 1):
        L.append(f"{i}. **{name}** — {desc}")
    L.append("- **overall** — your holistic judgement of how well the reply serves this person now.\n")
    L.append("## Output — return ONLY this JSON, one object per category, nothing else:")
    L.append("```json")
    L.append('{"scores": [')
    ex = ", ".join(f'"{n}": 0.0' for n, _ in AXES) + ', "overall": 0.0'
    L.append('  {"category": <n>, "A": {' + ex + "}, \"B\": {" + ex + "}},")
    L.append("  ... (one object per category shown below)")
    L.append("]}")
    L.append("```\n---\n")

    for n in sorted(cats):
        block = cats[n]
        if on not in block or baseline not in block:
            skipped.append(n)
            continue
        cat_id, label, situation = block["__meta"]
        if rng.random() < 0.5:
            slot = {"A": (on, block[on]), "B": (baseline, block[baseline])}
        else:
            slot = {"A": (baseline, block[baseline]), "B": (on, block[on])}
        key["categories"][str(n)] = {"category_id": cat_id, "A": slot["A"][0], "B": slot["B"][0]}
        L.append(f"## Category {n} — {label}\n")
        L.append("**Situation:**\n")
        L.append(situation.strip() + "\n")
        L.append("**Reply A:**\n")
        L.append("> " + slot["A"][1].strip().replace("\n", "\n> ") + "\n")
        L.append("**Reply B:**\n")
        L.append("> " + slot["B"][1].strip().replace("\n", "\n> ") + "\n")
        L.append("---\n")
    return "\n".join(L), key, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a variant-blind cross-family judge packet")
    ap.add_argument("--on", default="A_full",
                    help="the architecture-ON arm (default A_full); qualify as "
                         "'<personality>:<variant>' (e.g. Sol-FA:A_full) to compare across personalities")
    ap.add_argument("--baseline", default="D_first_order_only",
                    help="the baseline/ablated arm (default D_first_order_only); "
                         "'<personality>:<variant>' also allowed")
    ap.add_argument("--seed", type=int, default=20260628, help="blinding seed (recorded in the key)")
    ap.add_argument("--personality", default=None,
                    help="restrict to one personality's runs (REQUIRED when stored batteries "
                         "mix personalities — otherwise same-named variants would silently alias)")
    ap.add_argument("--results-dir", default=RESULTS)
    ap.add_argument("--glob", default="*-real.jsonl",
                    help="which results to read (default real only; '*-mock.jsonl' = dry-run shape)")
    a = ap.parse_args(argv)

    if "mock" in a.glob:
        print("NOTE: building from MOCK outputs -- placeholder text, NOT for a real judge. "
              "This is a wiring dry-run only.", file=sys.stderr)
    recs = gather_outputs(a.results_dir, a.glob, a.personality)
    personalities = {r.get("personality", "?") for r in recs.values()}
    arms = {a.on: parse_arm(a.on, a.personality), a.baseline: parse_arm(a.baseline, a.personality)}
    unqualified = [label for label, (pers, _v) in arms.items() if pers is None]
    if unqualified and len(personalities) > 1:
        print(f"REFUSING to build: stored outputs mix personalities {sorted(personalities)} -- "
              f"same-named variants would silently alias into one arm (latest-wins). "
              f"Pass --personality <name>, or qualify the arm(s) {unqualified} as "
              f"'<personality>:<variant>'.", file=sys.stderr)
        return 1
    cats = pivot(recs, load_prompts(), arms)
    leak_terms = personalities.copy()
    for pers, variant in arms.values():
        leak_terms |= {variant} | ({pers} if pers else set())
    leaks = find_blindness_leaks(cats, (a.on, a.baseline), leak_terms)
    if leaks:
        print("REFUSING to build: arm-identifying string(s) inside output text would UNBLIND "
              "the judge on contact:", file=sys.stderr)
        for n, arm, term in leaks:
            print(f"  category {n}, arm {arm}: contains {term!r}", file=sys.stderr)
        print("Regenerate the leaking output(s), or exclude them, before packeting.", file=sys.stderr)
        return 1
    md, key, skipped = build_packet(cats, a.on, a.baseline, a.seed)
    scored = len(key["categories"])
    if scored == 0:
        print(f"no category has BOTH arms ({a.on} AND {a.baseline}) in the stored real battery "
              f"outputs — run `run_battery.py --variants {a.on},{a.baseline}` first.", file=sys.stderr)
        return 1

    os.makedirs(a.results_dir, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    packet_path = os.path.join(a.results_dir, f"cross-family-packet-{stamp}.md")
    key_path = os.path.join(a.results_dir, f"cross-family-KEY-{stamp}.json")
    with open(packet_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)

    print(f"wrote {packet_path}")
    print(f"      {scored} categories, blind ({a.on} vs {a.baseline}), seed={a.seed}")
    if skipped:
        print(f"      SKIPPED {len(skipped)} categories missing one arm: {skipped}")
    print(f"wrote {key_path}")
    print("      PRIVATE de-blinding key — do NOT paste it to the judge (it is gitignored).")
    print("\nNext: paste the packet .md into a NON-Claude model, save its JSON reply, then:")
    print(f"  python benchmark/score_cross_family.py <judge-reply.json> --key {os.path.basename(key_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
