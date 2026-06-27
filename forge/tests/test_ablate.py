"""Offline tests for the per-module ablation harness — mock backend only, deterministic."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ablate import run_ablation, run_isolation, validate_instrument  # noqa: E402
from eer.cli import _variant_overrides  # noqa: E402


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


def test_every_isolation_path_emits_cleanly():
    # flip-gate criterion #1: only_<X> (block + INPUT/FINAL scaffold) never degenerates
    # to "(no output produced)". This is the fix for the bare-only_<X>-emits-nothing finding.
    _, _, rows = run_isolation("sol", "test input", "mock")
    assert rows, "isolation produced no rows"
    assert all(r["emits"] for r in rows)


def test_validate_passes_criterion_1():
    v = validate_instrument("sol", "test input", "mock")
    assert v["criterion_1_pass"] is True
    assert v["removal_empty"] == []
    assert v["isolation_empty"] == []


def test_only_variant_injects_output_scaffold():
    # the interactive `ab` command's only_<X> must keep INPUT+FINAL or isolation emits nothing
    keep = set(_variant_overrides("only_EMPA")["enable_only"])
    assert {"EMPA", "INPUT", "FINAL"} <= keep
    multi = set(_variant_overrides("only_LIT+MECH")["enable_only"])
    assert {"LIT", "MECH", "INPUT", "FINAL"} <= multi


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
