"""Offline tests for the variance/CI layer — no IO, no model, deterministic.

Covers the two orthogonal answers (is-it-real? / how-big?) and the load-bearing
guard: a single reading (n<2) must NEVER report as signal — that fake zero-width
certainty is the exact gap this module exists to close.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ci import delta_ci, bootstrap_ci, cohens_d, effect_label, verdict  # noqa: E402

SIGNAL = [0.20, 0.15, 0.05, 0.30, 0.10, 0.25, 0.18, 0.08, 0.22, 0.12, 0.14]
NOISE = [0.20, -0.15, 0.05, -0.30, 0.10, 0.25, -0.18, 0.08, -0.22, 0.12, -0.05]


def test_consistent_lift_is_real():
    c = delta_ci(SIGNAL)
    assert c["real"] is True
    assert c["crosses_zero"] is False
    assert c["mean"] > 0 and c["lo"] > 0


def test_sign_flipping_is_noise():
    c = delta_ci(NOISE)
    assert c["real"] is False
    assert c["crosses_zero"] is True
    assert c["lo"] <= 0 <= c["hi"]


def test_consistent_negative_is_real_and_negative():
    c = delta_ci([-d for d in SIGNAL])
    assert c["real"] is True
    assert c["mean"] < 0 and c["hi"] < 0


def test_n1_is_insufficient_never_signal():
    # the load-bearing case: a single judge reading must not read as a result
    c = delta_ci([0.14])
    assert c["insufficient"] is True
    assert c["real"] is None
    assert c["crosses_zero"] is None
    assert c["d"] is None


def test_n0_is_no_data():
    c = delta_ci([])
    assert c["n"] == 0
    assert c["insufficient"] is True
    assert c["mean"] is None


def test_constant_deltas_excludes_zero_but_d_undefined():
    # all identical positive deltas: CI is a point above 0 (real), but sd==0 so d is n/a
    c = delta_ci([0.1] * 6)
    assert c["real"] is True
    assert c["lo"] == c["hi"] and abs(c["lo"] - 0.1) < 1e-9  # degenerate point CI at ~0.1
    assert c["d"] is None and c["d_label"] == "n/a"


def test_effect_size_bands():
    assert effect_label(None) == "n/a"
    assert effect_label(0.1) == "negligible"
    assert effect_label(0.35) == "small"
    assert effect_label(0.6) == "medium"
    assert effect_label(1.2) == "large"
    # negative effects band on magnitude
    assert effect_label(-0.9) == "large"


def test_cohens_d_matches_definition():
    import statistics as st
    xs = SIGNAL
    expected = (sum(xs) / len(xs)) / st.stdev(xs)
    assert abs(cohens_d(xs) - expected) < 1e-12
    assert cohens_d([0.1]) is None       # n<2
    assert cohens_d([0.1, 0.1]) is None  # sd==0


def test_bootstrap_is_reproducible_under_seed():
    assert bootstrap_ci(SIGNAL, seed=42) == bootstrap_ci(SIGNAL, seed=42)
    # different seed → (almost surely) different interval, but same containment of mean
    lo, hi = bootstrap_ci(SIGNAL, seed=1)
    assert lo <= sum(SIGNAL) / len(SIGNAL) <= hi


def test_verdict_strings_carry_the_right_tags():
    assert "REAL" in verdict(delta_ci(SIGNAL))
    assert "NOISE" in verdict(delta_ci(NOISE)).upper()
    assert "INSUFFICIENT" in verdict(delta_ci([0.14])).upper()
    assert "no data" in verdict(delta_ci([]))


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
