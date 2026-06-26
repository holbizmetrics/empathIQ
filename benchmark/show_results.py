"""Pretty-print a battery results JSONL in a human-readable form.

The runs persist as JSONL (one record per personality x variant), which is great
for tooling but unreadable in a console. This renders any results file — or the
newest one if you don't name a file — as legible blocks: who ran, the mechanical
metrics, and the full final reply.

  python benchmark/show_results.py                       # newest results file
  python benchmark/show_results.py --latest --real       # newest non-mock file
  python benchmark/show_results.py path/to/battery-...jsonl
  python benchmark/show_results.py --brief               # metrics only, no reply text
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

try:  # final replies carry em-dashes / smart quotes; cp1252 stdout would crash
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BENCH, "results")
sys.path.insert(0, os.path.join(os.path.dirname(BENCH), "forge"))
from eer.voice import speak  # noqa: E402  (path must be set before import)

BAR = "=" * 72
SUB = "-" * 72


def _emit(text: str, as_md: bool) -> None:
    """Print the reply — rendered markdown if --md and `rich` is available, else plain."""
    if as_md:
        try:
            from rich.console import Console
            from rich.markdown import Markdown
            Console().print(Markdown(text))
            return
        except ImportError:
            print("(install 'rich' for rendered markdown — showing plain text instead)\n")
    print(text)


def _newest(real_only: bool) -> str | None:
    pat = "battery-*-real.jsonl" if real_only else "battery-*.jsonl"
    files = glob.glob(os.path.join(RESULTS, pat))
    return max(files, key=os.path.getmtime) if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="results JSONL (default: newest in benchmark/results)")
    ap.add_argument("--latest", action="store_true", help="use the newest results file")
    ap.add_argument("--real", action="store_true", help="with --latest, prefer newest non-mock file")
    ap.add_argument("--brief", action="store_true", help="metrics only — skip the reply text")
    ap.add_argument("--md", action="store_true",
                    help="render the reply as formatted markdown (needs 'rich'; falls back to plain)")
    ap.add_argument("--speak", action="store_true",
                    help="read the reply aloud (pc-native-voice-models if available, else Windows SAPI)")
    a = ap.parse_args()

    path = a.file or _newest(a.real)
    if not path or not os.path.exists(path):
        sys.exit("no results file found — run benchmark/run_battery.py first")

    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    print(f"\n{BAR}\n  {os.path.basename(path)}   ({len(recs)} run{'s' if len(recs) != 1 else ''})\n{BAR}")

    for r in recs:
        m = r.get("mechanical", {})
        print(f"\n  #{r.get('category_n','?')}  {r.get('label','')}")
        print(f"  persona: {r.get('persona','')}")
        print(f"  personality: {r.get('personality','?')}   variant: {r.get('variant','?')}"
              f"   backend: {r.get('backend','?')}")
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        lat = m.get("total_latency_ms")
        lat_s = f"{lat/1000:.1f}s" if isinstance(lat, (int, float)) else "?"
        print(f"  blocks: {m.get('nodes_run','?')}   time: {lat_s}   length: {m.get('final_chars','?')} chars")
        if not a.brief:
            print(SUB)
            reply = r.get("final_expression", "(no final expression)").strip()
            _emit(reply, a.md)
            if a.speak:
                speak(reply)
        print(SUB)


if __name__ == "__main__":
    main()
