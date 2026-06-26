"""Interactive walkthrough — runs a first-time user through one empathy benchmark
test, beginning to end, with no flags to memorize.

It just asks a few questions and drives the tools you already have:
  pick a personality  ->  pick a scenario  ->  run it (live)  ->  read the reply
  ->  optionally score it.

  python benchmark/walkthrough.py

Nothing here is new engine code — it orchestrates run_battery.py / show_results.py /
score_battery.py via subprocess, so the walkthrough and the raw commands never drift.
"""
from __future__ import annotations
import glob
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BENCH)
PERSONALITIES = os.path.join(ROOT, "forge", "personalities")
PY = sys.executable


def _ask(prompt: str, options: list[str], default: int = 1) -> int:
    """Show a numbered menu; return the chosen 1-based index. Enter = default."""
    for i, o in enumerate(options, 1):
        print(f"   {i})  {o}")
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print("  (pick one of the numbers)")


def _yes(prompt: str, default_yes: bool = True) -> bool:
    d = "Y/n" if default_yes else "y/N"
    raw = input(f"  {prompt} [{d}]: ").strip().lower()
    if not raw:
        return default_yes
    return raw.startswith("y")


def main():
    print("\n" + "=" * 70)
    print("  empathIQ walkthrough — let's run one empathy test together.")
    print("=" * 70)
    print("\n  An empathy architecture is a stack of blocks that read a hard human")
    print("  situation and compose a reply. We'll pick a character, hand it a")
    print("  scenario, watch it think block-by-block, then read what it said.\n")

    # 1) personality
    perss = sorted(f[:-5] for f in os.listdir(PERSONALITIES) if f.endswith(".json"))
    if not perss:
        sys.exit("  no personalities found — create one: python empathiq.py new --name vera --desc \"...\"")
    print("  Step 1 — pick a character (a personality = a wiring + a voice):")
    persona = perss[_ask("character", perss) - 1]

    # 2) scenario
    cats = json.load(open(os.path.join(BENCH, "prompts.json"), encoding="utf-8"))["categories"]
    print("\n  Step 2 — pick a scenario to put it through:")
    labels = [f"{c['label']}  ({c['id']})" for c in cats]
    cat = cats[_ask("scenario", labels) - 1]

    # 3) how to run
    print("\n  Step 3 — how do you want to run it?")
    mode = _ask("run mode", [
        "Quick demo — fake text, instant (just to see the shape)",
        "For real — the full architecture (~4 min, real model)",
        "Compare — full architecture vs. ablated, same scenario (~8 min)",
    ])

    cmd = [PY, os.path.join(BENCH, "run_battery.py"),
           "--personality", persona, "--only", cat["id"], "--verbose"]
    if mode == 1:
        cmd += ["--mock", "--variants", "A_full"]
    elif mode == 2:
        cmd += ["--variants", "A_full"]
    else:
        cmd += ["--variants", "A_full,D_first_order_only"]

    print(f"\n  Running: {persona} on \"{cat['label']}\"")
    print("  (each [k/16] line is one empathy block finishing — watch it think)\n")
    subprocess.run(cmd)

    # 4) read it
    newest = max(glob.glob(os.path.join(BENCH, "results", "battery-*.jsonl")), key=os.path.getmtime)
    if _yes("\n  Read the reply rendered nicely?", True):
        subprocess.run([PY, os.path.join(BENCH, "show_results.py"), "--md", newest])

    # 5) score it (honest about the judge)
    print("\n  Step 4 — scoring. Heads up: the built-in judge is the `claude` CLI,")
    print("  so it's Claude grading Claude — a useful sanity read, NOT the blind,")
    print("  non-Claude judge a real benchmark result needs. Treat any number as")
    print("  provisional / self-scored.")
    if _yes("  Run the self-scored judge anyway?", False):
        sc = [PY, os.path.join(BENCH, "score_battery.py")]
        if mode == 1:
            sc.append("--mock")
        sc += ["--only", str(cat["n"])]
        subprocess.run(sc)

    print("\n  Done. Your result is saved here:")
    print(f"    {newest}")
    print("  Re-read it any time:  python benchmark/show_results.py --md")
    print("  Try another character:  python empathiq.py personalities\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n  walkthrough cancelled. Nothing lost.", flush=True)
        sys.exit(130)
