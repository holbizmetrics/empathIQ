"""Offline smoke tests — mock backend only, no API calls. Verify the mechanical half
(graph load, topo order, variant overrides, executor wiring) is correct and deterministic."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eer.backend import MockBackend
from eer.executor import run_graph
from eer.graph import Graph
from eer.personality import Personality


def _default_graph():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return Graph.load(os.path.join(root, "graphs", "default.json"))


def test_topo_order_starts_at_input_ends_at_final():
    g = _default_graph()
    order = g.topo_order()
    assert order[0] == "INPUT"
    assert order[-1] == "FINAL"
    assert len(order) == len(g.nodes)


def test_full_run_produces_final_and_runs_all_nodes():
    g = _default_graph()
    res = run_graph(g, "I keep starting things and never finishing.", MockBackend())
    assert res.final_expression and res.final_expression != "(no output produced)"
    assert res.nodes_run == len(g.nodes)


def test_run_is_deterministic_under_mock():
    g = _default_graph()
    a = run_graph(g, "same input", MockBackend())
    b = run_graph(g, "same input", MockBackend())
    assert [r.output_hash for r in a.turn_log] == [r.output_hash for r in b.turn_log]


def test_disable_empa_drops_one_node_and_stays_acyclic():
    g = _default_graph().apply_variant(disable_nodes=["EMPA"])
    assert "EMPA" not in g.nodes
    order = g.topo_order()  # must not raise
    assert "FINAL" in order


def test_first_order_only_isolation():
    g = _default_graph().apply_variant(enable_only=["INPUT", "LIT", "RESP", "FINAL"])
    assert set(g.nodes) == {"INPUT", "LIT", "RESP", "FINAL"}
    res = run_graph(g, "hi", MockBackend())
    assert res.nodes_run == 4


def test_personality_loads_and_runs():
    p = Personality.load("sol")
    assert p.name == "Sol"
    res = run_graph(p.resolve_graph(), "test", MockBackend(), persona=p.persona_dict())
    assert res.final_expression


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
