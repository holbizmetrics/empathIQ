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
import subprocess
import sys
import tempfile

try:  # final replies carry em-dashes / smart quotes; cp1252 stdout would crash
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BENCH, "results")
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


def _sapi_speak(text: str) -> bool:
    """Windows SAPI — no install needed. Returns True if it spoke."""
    if os.name != "nt" or not text:
        return False
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
            tmp = f.name
        ps = ("Add-Type -AssemblyName System.Speech; "
              f"$t=[IO.File]::ReadAllText('{tmp}',[Text.Encoding]::UTF8); "
              "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak($t)")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=300)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _speak(text: str) -> None:
    """Speak a reply aloud. Ladder: pc-native-voice-models (Kokoro) -> Windows SAPI -> note."""
    if not text:
        return
    # 1) the rich path — sibling pc-native-voice-models, if cloned AND its model loads
    speak_py = os.path.join(os.path.dirname(ROOT), "pc-native-voice-models", "speak.py")
    if os.path.exists(speak_py):
        try:
            r = subprocess.run([sys.executable, speak_py, "--strip-markdown"],
                               input=text.encode("utf-8"), timeout=600)
            if r.returncode == 0:
                return
            print("  (pc-native-voice-models is present but couldn't speak — likely the Kokoro\n"
                  "   model files aren't downloaded yet; falling back to the system voice)")
        except Exception:
            pass
    # 2) the easy path — Windows SAPI, no install
    if _sapi_speak(text):
        return
    # 3) nothing available
    print("  (no text-to-speech available: clone pc-native-voice-models + fetch its Kokoro\n"
          "   models for your own voice, or run on Windows for the built-in system voice)")


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
                _speak(reply)
        print(SUB)


if __name__ == "__main__":
    main()
