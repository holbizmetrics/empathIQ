"""The cross-family wire: run the dual-arm battery across all categories, then build the
blind judge packet — one command instead of two.

It orchestrates the existing tools by subprocess (like walkthrough.py), so it never drifts
from the raw commands:
    run_battery.py --variants <on>,<baseline>      (collect both arms over every category)
    make_cross_family_packet.py --on <on> --baseline <baseline>   (blind packet + private KEY)

  python benchmark/run_cross_family.py --mock        # full pipeline, instant, fake text (wiring proof)
  python benchmark/run_cross_family.py               # REAL run — ~ (16+4) x 11 = 220 claude calls, long
  python benchmark/run_cross_family.py --only 8      # one category, real (a small real smoke)

Real runs are slow because each block is its own model call; scope with --only for a smoke
before going wide. The packet + KEY land in benchmark/results/ (gitignored).
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the dual-arm battery, then build the cross-family packet")
    ap.add_argument("--on", default="A_full")
    ap.add_argument("--baseline", default="D_first_order_only")
    ap.add_argument("--personality", default="sol")
    ap.add_argument("--seed", type=int, default=20260628)
    ap.add_argument("--only", default=None, help="restrict to one category id (a smaller real smoke)")
    ap.add_argument("--mock", action="store_true", help="instant fake-text dry-run (proves wiring)")
    ap.add_argument("--api", action="store_true", help="fast direct-API backend (needs ANTHROPIC_API_KEY)")
    a = ap.parse_args(argv)

    variants = f"{a.on},{a.baseline}"
    battery = [PY, os.path.join(BENCH, "run_battery.py"),
               "--personality", a.personality, "--variants", variants]
    if a.mock:
        battery.append("--mock")
    if a.api:
        battery.append("--api")
    if a.only:
        battery += ["--only", a.only]

    print(f"[1/2] dual-arm battery: {a.on} vs {a.baseline}"
          f"{' (mock)' if a.mock else ' (REAL — this takes a while)'}\n", flush=True)
    r = subprocess.run(battery)
    if r.returncode != 0:
        print(f"\nbattery exited {r.returncode} — not building a packet from a failed run.", file=sys.stderr)
        return r.returncode

    pack = [PY, os.path.join(BENCH, "make_cross_family_packet.py"),
            "--on", a.on, "--baseline", a.baseline, "--seed", str(a.seed)]
    if a.mock:
        pack += ["--glob", "*-mock.jsonl"]
    print(f"\n[2/2] building the blind cross-family packet ...\n", flush=True)
    return subprocess.run(pack).returncode


if __name__ == "__main__":
    sys.exit(main())
