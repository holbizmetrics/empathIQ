# RUN 2026-07-03 — flip-gate criterion #2: are the ablation deltas signed and sensibly shaped?

**What ran:** offline analysis only — no new model calls. Source data: the full-battery real run
`battery-20260628T032130-real.jsonl` (Sol, `A_full` vs `D_first_order_only`, all 11 categories,
1 generation per cell) scored twice by the same-family judge on 2026-06-29
(`scorecard-20260629T204530-real.jsonl`, `scorecard-20260629T210007-real.jsonl` — two independent
judge passes over the *same* stored outputs). Axes are the 5 frame-adherence dimensions
(frame_fit, register_match, format_adherence, instruction_following, restraint_appropriateness),
i.e. the Mira-frame-break instrument — **not** the C1–C10 empathy rubric.

## Result: per-category mean(A_full − D_first_order_only)

| Category | pass 1 | pass 2 | sign replicates |
|---|---|---|---|
| humor_warm_performative | −0.240 | −0.206 | ✓ |
| joy_savoring_peak | −0.182 | −0.430 | ✓ |
| play_manic_creative | −0.256 | −0.216 | ✓ |
| contentment_equanimity | −0.490 | −0.714 | ✓ |
| conflict_holding_others | −0.336 | −0.176 | ✓ |
| **crisis_compounding_overwhelm** | **+0.178** | **+0.114** | ✓ |
| injustice_moral_injury | −0.472 | −0.428 | ✓ |
| moral_choice_authority | −0.180 | −0.134 | ✓ |
| **repair_after_own_rupture** | **+0.120** | **+0.200** | ✓ |
| self_worth_under_judgment | −0.106 | −0.146 | ✓ |
| ethical_not_knowing | −0.562 | −0.460 | ✓ |

Per-category spread: sd ≈ 0.24 (pass 1) / 0.26 (pass 2). Sign agreement across the two judge
passes: **11/11 categories.** 9/11 replicate within |Δ| ≤ 0.16; the two largest movers
(joy_savoring_peak 0.25, contentment_equanimity 0.22) keep their sign.

## Reading (criterion #2: "signed, sensibly-shaped deltas — not a flat offset")

1. **Signed:** yes — 9 negative, 2 positive, replicated exactly across passes. Not a flat offset
   (a flat offset would move every category by a similar amount in the same direction).
2. **Sensibly shaped:** the sign pattern tracks the pre-registered mechanism
   (`PREREG-2026-06-28-mira-frame-break.md`). The full architecture WINS exactly where deep
   person-reading is warranted — compounding crisis/overwhelm, repair-after-own-rupture — and
   loses hardest exactly where the depth machinery over-reads someone who is fine or needs
   not-knowing held (contentment_equanimity −0.49/−0.71, ethical_not_knowing −0.56/−0.46).
   The deltas are mechanism-shaped, not noise-shaped.
3. **Instrument honesty note:** the headline direction is AGAINST the maker's pet theory on these
   axes — the bare-ish baseline beats the full architecture on frame adherence in 9/11 categories.
   The benchmark can hurt its maker. That is the property a measuring instrument must have.

## Honest boundaries (all load-bearing)

- **Same-family judge** (Claude scoring Claude) — this is an *instrument check, never the result*
  (ROADMAP discipline). The cross-family blind judge remains the only court.
- **n = 1 generation per cell** — the replication here is judge-read replication over fixed
  outputs; generation variance is untested at this sample size.
- **Frame axes, not the C-rubric** — criterion #2 for the C1–C10 empathy dimensions still needs
  its own scored data.
- Dr-Webb alternate arm (P2's third item) has never been generated for any variant — named gap.

## Verdict contribution

Criterion #2 moves to **SUPPORTED at instrument-check level** for the A-vs-D contrast on the
frame axes: deltas are signed, sign-stable across judge passes, and shaped like the
pre-registered mechanism. Not yet closable: C-rubric deltas + cross-family confirmation owed.
