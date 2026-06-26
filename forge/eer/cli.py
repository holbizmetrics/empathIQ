"""eer — command line for the Empathic Engine Researcher.

Build a personality (blocks + voice), then run and A/B test it for real.

  eer blocks                              list the 16 blocks
  eer graphs                              list available graphs
  eer diagram LIT,MECH,EMPA,RESP,FINAL    ASCII diagram from a spec
  eer new --name Sol --desc "..." --layer 2
  eer run  --personality sol --input "I keep starting things and not finishing"
  eer ab   --personality sol --variants A_full,B_no_EMPA,D_first_order_only --input "..."

Default backend is the `claude` CLI. Add --mock for a deterministic offline dry-run
(structure only, no real text), or --api for the fast direct-API backend (one
persistent connection instead of a cold CLI launch per block — seconds, not minutes;
needs `pip install anthropic` + ANTHROPIC_API_KEY). Add --live to watch the pipeline
light up block by block. Add --judge to score soft metrics with an LLM judge
(noisy — always labelled as such).
"""
from __future__ import annotations
import argparse
import os
import sys

from . import blocks as blockmod
from . import diagram as diagrammod
from .backend import make_backend
from .executor import run_graph
from .metrics import mechanical, judge, JUDGED
from .personality import Personality
from .voice import speak, BackgroundSpeaker, stop_speaking


def _quickstart_text(prog: str) -> str:
    """Friendly, copy-pasteable getting-started shown when no command is given.
    The user runs the script before reading any README — so the script teaches."""
    return f"""\
empathIQ — build an empathy architecture and test it for real.

No command given, so here's how to start. You need Python 3 and the `claude`
CLI — no API key, no setup:

  New here? Let it walk you through one test, no flags to learn:
     python benchmark/walkthrough.py

Or drive it directly:

  1. instant offline check — proves it runs (fake text, ~2 sec)
     python {prog} run --personality sol --input "I keep starting things and not finishing" --mock --live

  2. the real thing — real model output via your claude CLI (~4 min)
     python {prog} run --personality sol --input "I keep starting things and not finishing" --live

  3. the experiment — full architecture vs. ablated, same input (~10 min)
     python {prog} ab --personality sol --input "I keep starting things and not finishing" --variants A_full,B_no_EMPA,D_first_order_only --live

More:
  python {prog} blocks          list the 16 empathy blocks
  python {prog} graphs          list available graphs (the wirings)
  python {prog} personalities   list the characters you can run
  python {prog} new             build a personality (guided — just run it)
  python {prog} chat -h         chat with a personality (--demo plays a sample)
  python {prog} -h              full argument help

Test over the empathy categories, then score it:  see benchmark/README.md

Swap the --input "..." for any situation. Full guide: forge/README.md
"""


def _live_printer(full: bool = False):
    """A progress callback that draws the pipeline lighting up block by block.
    ASCII-only structural glyphs so it records cleanly in any terminal.
    full=True prints each block's COMPLETE output instead of the 60-char preview."""
    def cb(node, block, output, latency_ms, ran):
        name = block.name if block else node
        purpose = getattr(block, "purpose", "") if block else ""
        sym = block.symbol if block else f"[{node}]"
        lat = f"{latency_ms/1000:.1f}s" if latency_ms else ""
        status = "ok" if ran else "--"
        # name + plain-language purpose so cryptic block names (QTX, DTFX, ...) stay legible
        print(f"  {sym:7} {node:5} {name:28.28} {purpose:30.30} {status:3} {lat:>6}", flush=True)
        if node == "INPUT":
            return
        text = output or ""
        if full:
            for line in (text.splitlines() or [""]):
                print(f"            | {line}", flush=True)
            print(flush=True)
        else:
            peek = " ".join(text.split())
            if peek:
                tail = "..." if len(peek) > 60 else ""
                print(f"            > {peek[:60]}{tail}", flush=True)
    return cb


def _backend_kind(args) -> str:
    return "mock" if args.mock else ("api" if args.api else "claude")


def _variant_overrides(name: str) -> dict:
    """Map a variant name to mechanical graph overrides.
    Conventions: A_full / full = no change; no_<BLOCK>; first_order_only; only_<A+B+C>."""
    n = name.lower()
    if n in ("a_full", "full"):
        return {}
    if n in ("d_first_order_only", "first_order_only"):
        return {"enable_only": ["INPUT", "LIT", "RESP", "FINAL"]}
    if "no_" in n:
        block = name.split("no_", 1)[1].upper()
        return {"disable_nodes": [block]}
    if n.startswith("only_"):
        return {"enable_only": [b.upper() for b in name[5:].split("+")]}
    return {}


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))
    line = lambda cells: "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    print(line(headers))
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for r in rows:
        print(line(r))


def cmd_blocks(_a):
    rows = [[b.id, b.name, b.purpose] for b in blockmod.BLOCKS.values()]
    _print_table(["ID", "Name", "Purpose"], rows)


def cmd_graphs(_a):
    import json
    import os
    from .personality import GRAPHS_DIR
    print("A graph is the WIRING of an empathy architecture — which blocks run, and in")
    print("what order. A personality = a graph + a voice. (Run `blocks` to see what each")
    print("block does; `new` to build a personality on a graph.)\n")
    files = sorted(f for f in os.listdir(GRAPHS_DIR) if f.endswith(".json"))
    if not files:
        print("  (no graphs found)")
        return
    for f in files:
        name = f[:-5]
        try:
            g = json.load(open(os.path.join(GRAPHS_DIR, f), encoding="utf-8"))
            nodes = g.get("nodes", [])
            ids = [n if isinstance(n, str) else (n.get("id") or n.get("name")) for n in nodes]
            entry, exit_ = g.get("entry", "?"), g.get("exit", "?")
            print(f"  {name}  —  {len(ids)} blocks")
            print(f"    flow: {entry} ... {exit_}   "
                  f"({entry} captures the input, {exit_} renders the reply; the blocks")
            print(f"          between add empathy, some running in parallel)")
            print(f"    blocks: {', '.join(i for i in ids if i)}")
        except Exception as e:  # a malformed graph file shouldn't break the listing
            print(f"  {name}  (could not parse: {type(e).__name__})")
    print('\nTry one:  python empathiq.py run --personality sol --input "..." --live')


def cmd_personalities(_a):
    import json
    import os
    from .personality import PERSONALITIES_DIR
    print("A personality = a graph (wiring) + a voice. These are the characters you can")
    print("run. (Make one with `new`; see the wirings with `graphs`.)\n")
    files = sorted(f for f in os.listdir(PERSONALITIES_DIR) if f.endswith(".json"))
    if not files:
        print("  (none yet — create one: python empathiq.py new --name vera --desc \"...\")")
        return
    for f in files:
        try:
            d = json.load(open(os.path.join(PERSONALITIES_DIR, f), encoding="utf-8"))
            layer = d.get("persona_layer")
            voiced = d.get("block_prompts") or {}
            voice = f"custom voice ({len(voiced)} blocks)" if voiced else "default voice (no block overrides)"
            print(f"  {d.get('name', f[:-5])}  —  {d.get('description','') or '(no description)'}")
            print(f"    graph: {d.get('graph','default')}   layer: {layer if layer else '-'}   {voice}")
        except Exception as e:  # a malformed personality file shouldn't break the listing
            print(f"  {f[:-5]}  (could not parse: {type(e).__name__})")
    print('\nRun one:  python empathiq.py run --personality <name> --input "..." --live')


def cmd_diagram(a):
    print(diagrammod.render(a.spec))


def cmd_new(a):
    if not a.name:                       # bare `new` -> guided, no flags/JSON
        return _guided_new()
    p = Personality(name=a.name, description=a.desc or "", persona_layer=a.layer,
                    graph_ref=a.graph)
    path = p.save()
    print(f"created personality '{a.name}' -> {path}")


# blocks whose prompt most shapes a personality's "voice" (curated subset of the 16)
_VOICE_BLOCKS = [
    ("MECH", "how it reads people's motivation & emotion"),
    ("EMPA", "how it empathizes"),
    ("RESP", "how it responds in the moment"),
    ("FINAL", "how it phrases the final reply"),
]


def _guided_new():
    """Build a personality by answering questions — no flags, no JSON editing."""
    import os
    import subprocess
    import sys
    from .personality import Personality, PERSONALITIES_DIR
    try:
        print("\n  Build a personality — answer a few questions, no JSON needed.\n")
        name = ""
        while not name:
            name = input("  Name (one word, e.g. vera): ").strip()
        if os.path.exists(os.path.join(PERSONALITIES_DIR, f"{name.lower()}.json")):
            if not input(f"  '{name}' already exists — overwrite? [y/N]: ").strip().lower().startswith("y"):
                print("  cancelled — nothing changed.")
                return
        desc = input("  Describe its vibe in a sentence\n"
                     "    (e.g. 'warm but holds a firm boundary'): ").strip()
        print("\n  Association depth — how deep its perspective-taking runs.")
        print("  (A soft signal to the model: 1 lighter, 2 medium, 3 deeper.)")
        lr = input("  Layer 1/2/3 [2]: ").strip()
        layer = int(lr) if lr in ("1", "2", "3") else 2

        print("\n  Optional — give it a custom voice on a few key blocks.")
        print("  Type one plain-language instruction per block, or press Enter to skip.\n")
        block_prompts = {}
        for code, gloss in _VOICE_BLOCKS:
            line = input(f"  {code} — {gloss}:\n    > ").strip()
            if line:
                block_prompts[code] = line

        p = Personality(name=name, description=desc, persona_layer=layer,
                        graph_ref="default", block_prompts=block_prompts)
        path = p.save()
        voiced = f"{len(block_prompts)} custom block(s)" if block_prompts else "default voice"
        print(f"\n  Created '{name}'  ({voiced})\n    {path}")

        if input("\n  Try it now on a sample, instant (mock)? [Y/n]: ").strip().lower() in ("", "y", "yes"):
            subprocess.run([sys.executable, sys.argv[0], "run", "--personality", name,
                            "--input", "I keep starting things and never finishing.",
                            "--mock", "--live"])
        print(f'\n  Run it for real:  python empathiq.py run --personality {name} --input "..." --live')
    except (KeyboardInterrupt, EOFError):
        print("\n  cancelled — nothing saved.")


def _run_one(p: Personality, utterance: str, backend, variant: str, progress=None):
    graph = p.resolve_graph()
    ov = _variant_overrides(variant)
    if ov:
        graph = graph.apply_variant(disable_nodes=ov.get("disable_nodes"),
                                    enable_only=ov.get("enable_only"))
    return run_graph(graph, utterance, backend, persona=p.persona_dict(),
                     prompt_overrides=p.block_prompts, variant_name=variant,
                     progress=progress)


def _active_node_count(p, variant: str) -> int:
    """How many blocks will actually call the backend for this variant (INPUT is free)."""
    graph = p.resolve_graph()
    ov = _variant_overrides(variant)
    if ov:
        graph = graph.apply_variant(disable_nodes=ov.get("disable_nodes"),
                                    enable_only=ov.get("enable_only"))
    return sum(1 for n in graph.topo_order() if n != "INPUT")


def _print_run_intro(p, kind: str, n_calls: int) -> None:
    """Tell a first-time user what is about to happen and why it takes time.
    n_calls = blocks that hit the backend; +1 for the free INPUT block = total blocks."""
    n_blocks = n_calls + 1  # INPUT is always present and just ingests text (no model call)
    if kind == "mock":
        print(f"\nempathIQ - DRY RUN (--mock): pushing your message through {p.name}'s "
              f"{n_blocks}-block architecture with placeholder text, just to show the structure. "
              f"Instant, no model calls - drop --mock for a real reply.\n")
        return
    fast = " (--api is much faster; --mock is instant)" if kind == "claude" else ""
    print(f"\nempathIQ - running your message through {p.name}, a {n_blocks}-block empathy architecture.")
    print("Each block is one AI pass - observe, read motivation, empathize, respond, refine, "
          "then synthesize - run in order.")
    print(f"That's {n_calls} separate model calls (one per block; INPUT just reads your text), so a "
          f"real run takes a few minutes{fast}. The final reply prints at the bottom.")
    print("You're seeing the architecture RESPOND. empathIQ's real job is to SCORE replies like this "
          "and compare architectures - that's the `ab` command.\n")


def cmd_run(a):
    p = Personality.load(a.personality)
    backend = make_backend(_backend_kind(a), model=a.model, timeout=a.timeout)
    _print_run_intro(p, _backend_kind(a), _active_node_count(p, a.variant))
    base_live = _live_printer(full=a.full) if (a.live or a.full) else None
    speaker = BackgroundSpeaker() if (getattr(a, "speak", False) and base_live) else None
    if speaker is not None:
        def live(node, block, output, dt, ran):
            base_live(node, block, output, dt, ran)
            if ran and output and node != "INPUT":
                speaker.say(output)   # narrate each block's FULL text, overlapping the next
    else:
        live = base_live
    if live:
        print(f"\n  {p.name}  |  {a.input!r}\n")
    res = _run_one(p, a.input, backend, a.variant, progress=live)
    print(f"\n=== {p.name} / variant {a.variant} ===\n")
    if _backend_kind(a) == "mock":
        print("*** MOCK / DRY RUN - placeholder text below, no model was called. "
              "Drop --mock for a real reply. ***\n")
    print(res.final_expression)
    if speaker is not None:
        print("\n  (narration playing — Ctrl-C to stop early)", flush=True)
        speaker.close()
    elif getattr(a, "speak", False):
        speak(res.final_expression)
    print("\n--- turn log (mechanical only) ---")
    _print_table(["Node", "Ran", "Latency(ms)", "OutHash"],
                 [[r.node, "y" if r.ran else "-", r.latency_ms, r.output_hash or "-"]
                  for r in res.turn_log])
    m = mechanical(res)
    print(f"\nmechanical: nodes_run={m['nodes_run']} "
          f"total_latency_ms={m['total_latency_ms']} final_chars={m['final_chars']}")
    failed = [r.node for r in res.turn_log if not r.ran and r.node != "INPUT"]
    if failed:
        print(f"note: {len(failed)} block(s) failed and were skipped ({', '.join(failed)}); "
              "the run continued with the rest. See the Ran column above.")
    if a.judge:
        jb = make_backend("api" if a.api else "claude", model=a.model, timeout=a.timeout)
        scored = judge(res, jb)
        _print_table(["Judged metric", "Value", "Source"],
                     [[k, "?" if v.value is None else f"{v.value:.2f}", v.source]
                      for k, v in scored.items()])
    if _backend_kind(a) != "mock":
        print("\nnext: try another --input  ·  compare architectures with "
              "`ab --variants A_full,B_no_EMPA,D_first_order_only`  ·  build a persona with `new -h`")


def cmd_ab(a):
    p = Personality.load(a.personality)
    backend = make_backend(_backend_kind(a), model=a.model, timeout=a.timeout)
    jb = make_backend("api" if a.api else "claude", model=a.model, timeout=a.timeout) if a.judge else None
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]
    kind = _backend_kind(a)
    if kind == "mock":
        print(f"\nempathIQ - DRY RUN (--mock): comparing {len(variants)} versions of {p.name} "
              "on the same message (structure only, instant).\n")
    else:
        total = sum(_active_node_count(p, v) for v in variants)
        fast = " (--api is much faster)" if kind == "claude" else ""
        print(f"\nempathIQ - A/B test: running the SAME message through {len(variants)} versions of "
              f"{p.name} ({', '.join(variants)}) to compare what each architecture produces.")
        print(f"That's ~{total} model calls total, so this takes several minutes{fast}. "
              "All replies print side by side at the end.\n")
    rows = []
    finals = {}
    for v in variants:
        live = _live_printer(full=a.full) if (a.live or a.full) else None
        if live:
            print(f"\n  {p.name}  |  variant {v}\n")
        res = _run_one(p, a.input, backend, v, progress=live)
        finals[v] = res.final_expression
        m = mechanical(res)
        row = [v, m["nodes_run"], m["total_latency_ms"], m["final_chars"]]
        if jb is not None:
            scored = judge(res, jb)
            row += ["?" if scored[k].value is None else f"{scored[k].value:.2f}" for k in JUDGED]
        rows.append(row)
    headers = ["Variant", "nodes_run", "latency_ms", "final_chars"]
    if jb is not None:
        headers += JUDGED
    print(f"\n=== A/B on: {a.input!r} ===\n")
    _print_table(headers, rows)
    print("\n--- final expressions ---")
    print("(what to notice: the variants differ ONLY in which blocks ran - A_full is the whole "
          "architecture, B_no_EMPA drops the empathy block, D_first_order_only keeps just "
          "INPUT/LIT/RESP/FINAL. Read for warmth, depth, and whether each still holds a boundary.)")
    if kind == "mock":
        print("(MOCK / DRY RUN: the texts below are placeholder, not real replies - drop --mock to compare for real.)")
    for v, text in finals.items():
        print(f"\n[{v}]\n{text}")


# a short, persona-agnostic script so `chat --demo` shows a being in conversation
_DEMO_TURNS = [
    "hey... kind of a rough day. not even sure why i'm typing this.",
    "i keep saying i'll change something and then i just... don't.",
    "thanks. that actually helped a little.",
]


def cmd_chat(a):
    """Talk to a personality (interactive), or play a scripted excerpt (--demo).
    Each turn runs the full pipeline; prior turns are threaded back in as context
    (felt continuity, not true cross-turn memory)."""
    p = Personality.load(a.personality)
    kind = _backend_kind(a)
    backend = make_backend(kind, model=a.model, timeout=a.timeout)
    name = p.name
    rec = open(a.record, "w", encoding="utf-8") if a.record else None
    history: list[tuple[str, str]] = []
    n_blocks = _active_node_count(p, "A_full") + 1

    def turn(user: str, echo: bool) -> None:
        if echo:
            print(f"  You: {user}", flush=True)
        if history:
            convo = "\n".join(f"User: {u}\n{name}: {r}" for u, r in history)
            utterance = f"{convo}\nUser: {user}"
        else:
            utterance = user
        prog = None
        if kind != "mock":   # a real turn is ~16 silent model calls (~min); show it's alive
            print(f"  ...{name} is thinking ({n_blocks} blocks, a few min):", flush=True)
            counter = {"k": 0}

            def prog(node, block, output, dt, ran, _t=n_blocks, _c=counter):
                _c["k"] += 1
                print(f"    [{_c['k']:>2}/{_t}] {node:<6} {'ok' if ran else 'XX'} {dt / 1000:4.1f}s",
                      flush=True)
        reply = _run_one(p, utterance, backend, "A_full", progress=prog).final_expression
        print(f"\n  {name}: {reply}\n", flush=True)
        if a.speak:
            speak(reply)
        history.append((user, reply))
        if rec:
            rec.write(f"You: {user}\n{name}: {reply}\n\n")
            rec.flush()

    print(f"\n  Chatting with {name} — {p.description or '(no description)'}")
    if kind == "claude":
        print("  (each reply = ~16 model calls, so a real one takes a few minutes; "
              "--mock = instant flow, --api = fast)")
    print("  Each turn gets the prior exchange as context — felt continuity, not true memory.\n")

    try:
        if a.demo:
            print("  — scripted excerpt —\n")
            for user in _DEMO_TURNS:
                turn(user, echo=True)
        else:
            print("  Type a message; empty line or 'quit' ends it.\n")
            while True:
                user = input("  You: ").strip()
                if not user or user.lower() in ("quit", "exit", ":q"):
                    break
                turn(user, echo=False)
            print("  bye 👋")
    except (EOFError, KeyboardInterrupt):
        print("\n  bye 👋")
    finally:
        if rec:
            rec.close()
            print(f"  (transcript saved -> {a.record})")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eer", description="Empathic Engine Researcher")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("blocks").set_defaults(func=cmd_blocks)
    sub.add_parser("graphs").set_defaults(func=cmd_graphs)
    sub.add_parser("personalities").set_defaults(func=cmd_personalities)

    d = sub.add_parser("diagram"); d.add_argument("spec"); d.set_defaults(func=cmd_diagram)

    n = sub.add_parser("new")
    n.add_argument("--name"); n.add_argument("--desc", default="")
    n.add_argument("--layer", type=int, choices=[1, 2, 3]); n.add_argument("--graph", default="default")
    n.set_defaults(func=cmd_new)

    c = sub.add_parser("chat")
    c.add_argument("--personality", required=True)
    c.add_argument("--mock", action="store_true", help="instant placeholder backend (feel the flow)")
    c.add_argument("--api", action="store_true", help="fast direct-API backend (needs ANTHROPIC_API_KEY)")
    c.add_argument("--demo", action="store_true", help="play a short scripted excerpt instead of typing")
    c.add_argument("--record", metavar="PATH", help="save the transcript to a file (a reusable excerpt)")
    c.add_argument("--speak", action="store_true", help="read each reply aloud")
    c.add_argument("--model", default=None)
    c.add_argument("--timeout", type=int, default=300)
    c.set_defaults(func=cmd_chat)

    for name, fn in (("run", cmd_run), ("ab", cmd_ab)):
        s = sub.add_parser(name)
        s.add_argument("--personality", required=True)
        s.add_argument("--input", required=True)
        s.add_argument("--mock", action="store_true",
                       help="deterministic offline backend (no API)")
        s.add_argument("--api", action="store_true",
                       help="fast direct-API backend (needs `pip install anthropic` + ANTHROPIC_API_KEY)")
        s.add_argument("--live", action="store_true",
                       help="watch the pipeline light up block by block")
        s.add_argument("--full", action="store_true",
                       help="print each block's COMPLETE output, not the 60-char preview")
        s.add_argument("--judge", action="store_true")
        s.add_argument("--model", default=None)
        s.add_argument("--timeout", type=int, default=300,
                       help="per-block backend timeout in seconds (default 300)")
        if name == "run":
            s.add_argument("--variant", default="A_full")
            s.add_argument("--speak", action="store_true",
                           help="read the final reply aloud (pc-native-voice-models if available, else Windows SAPI)")
        else:
            s.add_argument("--variants", default="A_full,B_no_EMPA,D_first_order_only")
        s.set_defaults(func=fn)
    return p


def main(argv=None):
    # Windows stdout defaults to cp1252, which crashes on em-dashes / smart quotes in
    # model output. Decode as UTF-8 so real replies and the live view print cleanly.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    if getattr(args, "func", None) is None:
        print(_quickstart_text(os.path.basename(sys.argv[0]) or "eer.py"))
        return
    try:
        args.func(args)
    except KeyboardInterrupt:
        stop_speaking()          # kill any in-flight narration so it can't outlive the process
        print("\n  stopped.")
        sys.exit(130)


if __name__ == "__main__":
    main(sys.argv[1:])
