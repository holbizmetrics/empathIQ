"""Offline tests for the variant-name mapping, active-node counting, and the
personality voice (block_prompts) override mechanism — the logic added in the
manual-usability pass. Mock backend only; deterministic; no API calls.

Run:  python forge/tests/test_variants_and_voice.py   (or via pytest)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eer.backend import MockBackend          # noqa: E402
from eer.cli import _variant_overrides, _active_node_count  # noqa: E402
from eer.executor import run_graph           # noqa: E402
from eer.graph import Graph                  # noqa: E402
from eer.personality import Personality      # noqa: E402


def _default_graph():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return Graph.load(os.path.join(root, "graphs", "default.json"))


def test_variant_overrides_mapping():
    assert _variant_overrides("A_full") == {}
    assert _variant_overrides("full") == {}
    assert _variant_overrides("D_first_order_only") == {"enable_only": ["INPUT", "LIT", "RESP", "FINAL"]}
    assert _variant_overrides("no_EMPA") == {"disable_nodes": ["EMPA"]}
    assert _variant_overrides("only_EMPA") == {"enable_only": ["EMPA"]}
    assert _variant_overrides("only_LIT+RESP") == {"enable_only": ["LIT", "RESP"]}


def test_variant_names_are_case_insensitive():
    assert _variant_overrides("a_full") == _variant_overrides("A_FULL") == {}
    assert _variant_overrides("no_empa") == {"disable_nodes": ["EMPA"]}


def test_active_node_count_excludes_free_input():
    p = Personality.load("sol")
    assert _active_node_count(p, "A_full") == len(_default_graph().nodes) - 1
    # first-order = INPUT, LIT, RESP, FINAL; INPUT is free, so 3 backend calls
    assert _active_node_count(p, "D_first_order_only") == 3


def test_personality_block_prompts_round_trip():
    p = Personality(name="tmpx", description="d", persona_layer=2,
                    graph_ref="default", block_prompts={"EMPA": "hold the line"})
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "tmpx.json")
        p.save(path)
        loaded = Personality.load(path)
    assert loaded.block_prompts == {"EMPA": "hold the line"}
    assert loaded.persona_layer == 2
    assert loaded.graph_ref == "default"


def test_block_prompt_override_reaches_only_that_block():
    g = _default_graph()
    plain = run_graph(g, "hi", MockBackend())
    over = run_graph(g, "hi", MockBackend(),
                     prompt_overrides={"EMPA": "a completely different instruction"})
    plain_h = {r.node: r.output_hash for r in plain.turn_log}
    over_h = {r.node: r.output_hash for r in over.turn_log}
    assert plain_h["EMPA"] != over_h["EMPA"]   # the override changed EMPA...
    assert plain_h["LIT"] == over_h["LIT"]     # ...and only EMPA (LIT runs before it, untouched)


def test_empty_block_prompts_runs_like_default():
    # a personality with no voice overrides (e.g. fresh `new` stub) still runs clean
    p = Personality(name="bare", graph_ref="default")
    res = run_graph(p.resolve_graph(), "hi", MockBackend(),
                    persona=p.persona_dict(), prompt_overrides=p.block_prompts)
    assert res.final_expression and res.final_expression != "(no output produced)"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
