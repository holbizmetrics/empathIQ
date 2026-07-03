# RUN 2026-07-03 — Sol-FA full 11-category grid: the frame-aware fix vs both arms

**What ran:** Sol-FA (frame-aware variant, `A_full` graph) generated real on all 11 categories
(2 from the earlier P3 run + 9 new, all 16 blocks, zero failures), then judge-scored in two
independent same-family passes (`scorecard-20260703T210212/210626-real.jsonl`). Compared
offline against the June-29 two-pass scorecards of original Sol `A_full` and
`D_first_order_only` on the 5 frame axes (mean over dims, mean over passes).

## Result

| Category | FA | Sol A | Sol D | FA−A | FA−D |
|---|---|---|---|---|---|
| humor_warm_performative | 0.59 | 0.11 | 0.34 | **+0.48** | **+0.26** |
| joy_savoring_peak | 0.89 | 0.29 | 0.60 | **+0.60** | **+0.29** |
| play_manic_creative | 0.27 | 0.16 | 0.40 | +0.11 | **−0.13** |
| contentment_equanimity | 0.90 | 0.21 | 0.81 | **+0.69** | +0.09 |
| conflict_holding_others | 0.90 | 0.12 | 0.38 | **+0.78** | **+0.52** |
| crisis_compounding_overwhelm | 0.83 | 0.30 | 0.16 | **+0.53** | **+0.67** |
| injustice_moral_injury | 0.53 | 0.15 | 0.60 | **+0.38** | −0.07 |
| moral_choice_authority | 0.74 | 0.54 | 0.69 | +0.21 | +0.05 |
| repair_after_own_rupture | 0.37 | 0.42 | 0.27 | −0.06 | +0.11 |
| self_worth_under_judgment | 0.45 | 0.50 | 0.63 | −0.06 | **−0.18** |
| ethical_not_knowing | 0.87 | 0.18 | 0.69 | **+0.69** | +0.18 |

- **Sol-FA beats original A_full: 9/11, mean delta +0.395.** The frame-break cost is recovered
  nearly everywhere; the two losses (repair, self-worth) are small (≤0.06) and are exactly the
  two categories where the original depth machinery was already winning — the fix costs almost
  nothing where the old behavior was right.
- **Sol-FA beats the D baseline: 8/11, mean delta +0.162.** The pre-registered P3 shape —
  depth deployed *in frame* beats both the frame-broken full architecture AND the shallow
  baseline — shows up at the grid level, not just on the two scaffolded items.
- **All 22 comparisons sign-stable across the two judge passes.**
- Where FA still loses to D: `play_manic_creative` (−0.13; the frame machinery may damp
  playfulness), `self_worth_under_judgment` (−0.18), `injustice_moral_injury` (−0.07,
  within noise). These three are the remaining design surface.

## Honest boundaries

- **Same-family judge** — instrument check, never the result. The cross-family blind packets
  (built 2026-07-03) are the court; this grid says the P3 hypothesis is worth spending them on.
- **Cross-day judge comparability:** FA was scored 2026-07-03, Sol arms 2026-06-29, same judge
  prompt but different days/CLI sessions — a judge-drift confound the same-day sign-stability
  cannot rule out. Clean fix if wanted: rescore Sol A/D in the same session (≈22 calls/pass).
- **n = 1 generation per cell**; generation variance untested.
- Frame axes, not the C1–C10 rubric.

## ADDENDUM (same session, ~1h later) — same-day rescore kills the drift confound

Sol `A_full` + `D` were rescored in two fresh passes the same evening
(`scorecard-20260703T211602/212359-real.jsonl`), removing the cross-day judge confound.
Result on the clean same-day grid:

- **Sol-FA beats original A_full: 11/11, mean +0.421** (was 9/11 +0.395 against June-29 scores).
- **Sol-FA beats D baseline: 10/11, mean +0.218** (was 8/11 +0.162).
- Measured judge drift June-29 → today: small on average (SolA −0.026, SolD −0.056) but up to
  ±0.34 on individual categories — the same-day rescore was worth doing; per-category
  comparisons across scoring days are not safe even when the mean is.
- The two apparent Sol-FA losses vs original A (repair, self-worth) **disappear** on same-day
  scoring — they were drift artifacts. The one loss vs D that SURVIVES: `play_manic_creative`
  (−0.23, consistent across both scoring days) — that one is real design surface: the frame
  machinery damps manic-playful register.

The effect got stronger, not weaker, when the confound was removed. Same-family boundary
unchanged: this earns the cross-family run; it does not replace it.

## Consequence for the thesis

If the cross-family judge confirms this shape, the benchmark's "architecture-on" arm should be
the *frame-aware* full architecture — the ablation story becomes three-way (bare → depth-broken
→ depth-in-frame), which is a stronger and more honest headline than A-vs-D ever was.
