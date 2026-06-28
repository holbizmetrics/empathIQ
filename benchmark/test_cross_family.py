"""Offline tests for the cross-family judge-packet harness — no IO, no model, deterministic."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_cross_family_packet import build_packet, AXES  # noqa: E402
from score_cross_family import aggregate                  # noqa: E402

ON, BASE = "A_full", "D_first_order_only"
CATS = {
    1: {"__meta": ("cat_one", "Label one", "Situation one."), ON: "FULL reply one", BASE: "BASE reply one"},
    2: {"__meta": ("cat_two", "Label two", "Situation two."), ON: "FULL reply two", BASE: "BASE reply two"},
    3: {"__meta": ("cat_three", "Label three", "Situation three."), ON: "only full here"},  # missing baseline
}


def _judge(key, on_overall, base_overall):
    """A synthetic judge that scores the ON arm at on_overall and baseline at base_overall,
    regardless of which blind slot (A/B) each landed in — exercises de-blinding."""
    rows = []
    for n, kn in key["categories"].items():
        on_slot = "A" if kn["A"] == key["on"] else "B"
        base_slot = "A" if kn["A"] == key["baseline"] else "B"
        scores = {ax: 0.5 for ax, _ in AXES}
        row = {"category": int(n),
               on_slot: {**scores, "overall": on_overall},
               base_slot: {**scores, "overall": base_overall}}
        rows.append(row)
    return rows


def test_missing_arm_is_skipped():
    _, key, skipped = build_packet(CATS, ON, BASE, seed=42)
    assert skipped == [3]
    assert set(key["categories"]) == {"1", "2"}


def test_blinding_is_reproducible_under_seed():
    _, k1, _ = build_packet(CATS, ON, BASE, seed=7)
    _, k2, _ = build_packet(CATS, ON, BASE, seed=7)
    assert k1["categories"] == k2["categories"]


def test_packet_shows_both_replies_and_no_arm_labels():
    md, key, _ = build_packet(CATS, ON, BASE, seed=1)
    assert "FULL reply one" in md and "BASE reply one" in md
    assert "Reply A" in md and "Reply B" in md
    # the packet must not leak the arm names that the key maps
    assert ON not in md and BASE not in md


def test_key_maps_each_slot_to_a_distinct_arm():
    _, key, _ = build_packet(CATS, ON, BASE, seed=3)
    for n, kn in key["categories"].items():
        assert {kn["A"], kn["B"]} == {ON, BASE}


def test_aggregate_deblinds_and_signs_delta():
    _, key, _ = build_packet(CATS, ON, BASE, seed=5)
    v = aggregate(key, [_judge(key, on_overall=0.9, base_overall=0.3)])
    # ON beats baseline by 0.6 everywhere, regardless of A/B placement
    assert v["mean_overall_delta_all"] == 0.6
    assert v["per_judge"][0]["baseline_wins"] == 0
    assert v["per_judge"][0]["scored"] == 2


def test_aggregate_counts_baseline_wins_when_ablation_survives():
    _, key, _ = build_packet(CATS, ON, BASE, seed=5)
    v = aggregate(key, [_judge(key, on_overall=0.2, base_overall=0.8)])
    assert v["mean_overall_delta_all"] == -0.6
    assert v["per_judge"][0]["baseline_wins"] == 2


def test_inter_rater_agreement():
    _, key, _ = build_packet(CATS, ON, BASE, seed=5)
    agree = aggregate(key, [_judge(key, 0.9, 0.3), _judge(key, 0.8, 0.4)])  # both pick ON
    assert agree["inter_rater"]["winner_agreement"] == 1.0
    disagree = aggregate(key, [_judge(key, 0.9, 0.3), _judge(key, 0.3, 0.9)])  # opposite winners
    assert disagree["inter_rater"]["winner_agreement"] == 0.0


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
