"""Confidence intervals + effect size for benchmark deltas — the signal-vs-noise
rigor the flip-gate needs. Stdlib only (no numpy/scipy): portable, trivially testable.

The whole harness reports the on-minus-baseline delta as a BARE POINT ESTIMATE
(e.g. score_cross_family's mean_overall_delta). A single number cannot tell signal
from noise. This module answers two SEPARATE, honestly-orthogonal questions about a
list of deltas:

  * "Is it real?"  -> a percentile bootstrap 95% CI + whether it excludes zero.
                      Decidable; legitimate to mechanize.
  * "How big?"     -> a standardized effect size (Cohen's-d-style: mean / sd), read
                      against EXTERNAL convention bands (~0.2 small / 0.5 medium /
                      0.8 large). Descriptive, NOT a test.

It deliberately does NOT answer "does it matter?" — that is the practical-significance
judgment, which has no mechanical rung (significance is undecidable by construction).
So this module emits no binary "thesis-win" verdict; it gives you the two numbers and
leaves the call where it belongs: with the human reviewer.

Two variance sources the deltas can carry, named honestly (a CI is only as wide as the
spread it sees):
  * ACROSS-ITEM: per-category deltas vary -> "does the architecture lift ON AVERAGE
    across this category set?" Free; the deltas already exist in every scorecard.
  * JUDGE/GEN RESAMPLING: re-score (or re-generate) the same item K times -> "is THIS
    item's delta real or judge jitter?" Costs K x API calls.
Pool both by passing every (item x run) delta in one list; the bootstrap is agnostic
to which axis of variance produced the spread.
"""
from __future__ import annotations
import random
import statistics as st


def bootstrap_ci(xs, confidence=0.95, iters=10000, seed=0):
    """Percentile bootstrap CI for the mean of xs. Returns (lo, hi).

    Bootstrap (not a t-interval) because per-category deltas are not Gaussian and N is
    small: resampling makes no distributional assumption. Seeded for reproducibility.
    """
    xs = [float(x) for x in xs]
    n = len(xs)
    if n == 0:
        return (float("nan"), float("nan"))
    if n == 1:
        # A single reading has no spread to resample. Return a degenerate point so the
        # caller's n<2 guard (delta_ci) reports "insufficient", NOT a fake zero-width CI.
        return (xs[0], xs[0])
    rng = random.Random(seed)
    means = []
    for _ in range(iters):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_i = int((1 - confidence) / 2 * iters)
    hi_i = int((1 + confidence) / 2 * iters) - 1
    return (means[lo_i], means[hi_i])


def cohens_d(xs):
    """One-sample standardized effect size: mean / sample-sd. None if undefined (n<2)
    or sd==0. Magnitude read against external bands by `effect_label`."""
    xs = [float(x) for x in xs]
    if len(xs) < 2:
        return None
    sd = st.stdev(xs)  # sample sd (n-1) — the conventional effect-size denominator
    if sd == 0:
        return None
    return (sum(xs) / len(xs)) / sd


def effect_label(d):
    """External convention bands (Cohen 1988). Descriptive, not a test."""
    if d is None:
        return "n/a"
    a = abs(d)
    if a < 0.2:
        return "negligible"
    if a < 0.5:
        return "small"
    if a < 0.8:
        return "medium"
    return "large"


def delta_ci(deltas, confidence=0.95, iters=10000, seed=0):
    """Summarize a list of deltas. Returns a dict with the two orthogonal answers.

    Keys: mean, lo, hi, crosses_zero, real, d, d_label, n, sd, insufficient.
      real          -> CI excludes 0 in the mean's direction ("is it real?"). None if n<2.
      d, d_label    -> standardized effect size + band ("how big?"). None/"n/a" if n<2.
      insufficient  -> True when n<2: a single reading is the noise problem, not a result.
    """
    deltas = [float(d) for d in deltas]
    n = len(deltas)
    if n == 0:
        return {"mean": None, "lo": None, "hi": None, "crosses_zero": None,
                "real": None, "d": None, "d_label": "n/a", "n": 0, "sd": None,
                "insufficient": True}
    mean = sum(deltas) / n
    if n < 2:
        # No variance estimate is possible from a single reading. Refuse to report it
        # as signal — that fake-certainty is exactly the gap this module exists to close.
        return {"mean": mean, "lo": None, "hi": None, "crosses_zero": None,
                "real": None, "d": None, "d_label": "n/a", "n": 1, "sd": None,
                "insufficient": True}
    lo, hi = bootstrap_ci(deltas, confidence, iters, seed)
    crosses_zero = lo <= 0.0 <= hi
    d = cohens_d(deltas)
    return {"mean": mean, "lo": lo, "hi": hi, "crosses_zero": crosses_zero,
            "real": not crosses_zero, "d": d, "d_label": effect_label(d),
            "n": n, "sd": st.stdev(deltas), "insufficient": False}


def verdict(ci, label="delta"):
    """One human-readable line: 'is it real?' and 'how big?', never 'does it matter?'."""
    if ci["n"] == 0:
        return f"{label}: no data"
    if ci.get("insufficient"):
        return (f"{label} = {ci['mean']:+.3f}  n={ci['n']}  ->  INSUFFICIENT "
                f"(single reading, no variance estimate — this is the noise problem, "
                f"not a result)")
    real = "REAL (CI excludes 0)" if ci["real"] else "INDISTINGUISHABLE FROM NOISE (CI includes 0)"
    d_str = "d=n/a" if ci["d"] is None else f"d={ci['d']:+.2f} ({ci['d_label']})"
    return (f"{label} = {ci['mean']:+.3f}  [95% CI {ci['lo']:+.3f}, {ci['hi']:+.3f}]"
            f"  n={ci['n']}  ->  {real} · {d_str}")
