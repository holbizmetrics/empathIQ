# PRE-REGISTRATION — 2026-06-29 — top-level thesis direction (instrument-only v0.1)

> **Frozen BEFORE any cross-family blind-judge run.** The git commit timestamp on this file is
> the proof of priority. Nothing below may be edited after a result is in hand; corrections go
> in a dated addendum, never an overwrite. This exists so the headline result cannot be
> motivated-reasoned after the fact.

## The claim under test (the Constraint Principle)

A *bounded-empathic* architecture (`A_full`) beats BOTH (a) a bare / first-order baseline AND
(b) a warm-but-unbounded architecture — because only the bounded-empathic system lands in the
relational AND the boundary column at once. (README, "The central claim being tested".)

## What this prereg freezes — and what it deliberately does NOT

**Scope honesty — only part of the thesis is testable at v0.1.** Of the three poles, two arms
exist as runnable variants: `A_full` (bounded-empathic, 16 blocks) and `D_first_order_only`
(bare / first-order baseline = `INPUT/LIT/RESP/FINAL`). The **warm-but-unbounded** pole has **no
built arm yet**, so this prereg freezes only the half that can actually be run.

### FROZEN PREDICTION (falsifiable)

- **P1 — direction, AGGREGATE.** On the cross-family blind judge, the on-vs-baseline overall
  delta `A_full − D_first_order_only`, **averaged across the benchmark categories, is POSITIVE**
  (`A_full` scores higher).
- **Magnitude: TBD.** This prereg commits to DIRECTION ONLY — no effect-size band is predicted.
  (A magnitude band, if added, goes in a dated addendum filed BEFORE the judge run, never after.)
  Direction-only is the conservative commitment; it remains falsifiable (see below).

### PRE-REGISTERED LOCAL EXCEPTION (so the two preregs stay consistent)

P1 is an **aggregate** claim. It does **not** predict `A_full` wins on every item. The companion
item-level prereg (`runs/PREREG-2026-06-28-mira-frame-break.md`) freezes the **opposite** on the
persona-cast C10 moral-courage item (Mira, item 8): `A_full` **breaks frame** and
`D_first_order_only` **wins** there. The two are consistent — aggregate-positive WITH a known
local-negative on persona-cast frame-break items — and `Sol-FA` is the arm built to recover
those. Calling this out here so the aggregate prediction is not read as contradicting the
already-frozen Mira prediction.

### NOT pre-registered (named so the gap is explicit, not hidden)

- **P-warm (the other half of the thesis):** `A_full` beating a *warm-but-unbounded* arm is NOT
  frozen — that arm does not exist yet. Pre-registering against a nonexistent arm would be
  theatre. Building the warm-unbounded variant + its own prereg is future work; until then the
  three-pole claim is only partly tested.

## What would FALSIFY P1 (and why that is a success of the method)

- **Null:** the cross-family CI on the aggregate delta INCLUDES zero
  (`benchmark/score_variance.py` → INDISTINGUISHABLE FROM NOISE). The lift is not distinguishable
  from noise. P1 falsified.
- **Negative:** the aggregate delta is reliably negative (`baseline ≥ A_full`; the ablation
  survives across categories). P1 falsified in the strong direction.

A benchmark that cannot return "no lift" against its maker's own thesis is not measuring
anything. A null or negative here is the instrument working, not failing.

## How it will be scored (the decidable substrate)

- Arms blinded to A/B via `benchmark/make_cross_family_packet.py` (fixed-seed key, gitignored).
- Scored by ≥1 **non-Claude** judge family, blind to which arm is which.
- De-blinded + delta + CI via `benchmark/score_cross_family.py` + `benchmark/ci.py` (bootstrap
  95% CI + effect size — the magnitude band a future addendum would predict).
- **Decidable-check on the rigor signal:** the judge's numeric scores are re-aggregated locally;
  "the judge says A wins" does not count until the local re-aggregation agrees.

## THE DISCIPLINE BOUNDARY (load-bearing)

This prediction was produced by Claude-family reasoning. Same-family confidence that "`A_full`
wins" is **correlated, not confirmatory** — the exact blind spot the lab cannot trust about
itself. The blind cross-family judge is the ONLY court. Until it runs, P1 is a HYPOTHESIS, not a
result. **The verdict is OWED.**

## Companion
Item-level prereg (the sharpest single case): `runs/PREREG-2026-06-28-mira-frame-break.md`.
