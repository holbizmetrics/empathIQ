"""Offline tests for the per-module ablation harness — mock backend only, deterministic."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ablate import run_ablation  # noqa: E402


def test_ablation_covers_every_block_but_input():
    p, base, rows = run_ablation("sol", "test input", "mock")
    nodes = {r["node"] for r in rows}
    assert "INPUT" not in nodes          # input capture is never ablated
    assert "FINAL" in nodes              # the output block IS ablated
    assert len(rows) == base.nodes_run - 1  # every run node except INPUT


def test_rows_are_sorted_by_effect_desc():
    _, _, rows = run_ablation("sol", "test input", "mock")
    effects = [r["effect"] for r in rows]
    assert effects == sorted(effects, reverse=True)


def test_ablation_is_deterministic_under_mock():
    _, _, a = run_ablation("sol", "same input", "mock")
    _, _, b = run_ablation("sol", "same input", "mock")
    assert a == b


def test_every_block_feeds_the_output_path():
    # The default architecture is densely wired: removing any block changes the mock
    # output (none are structurally dead). This is the clean mock-level finding.
    _, _, rows = run_ablation("sol", "test input", "mock")
    assert all(r["changed"] for r in rows)


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
