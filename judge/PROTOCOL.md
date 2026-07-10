# Judge protocol

The judge is an **external evaluator** — a model (or human) that did **not** produce the response
and has no stake in it. The system under test never scores itself; self-scores are *preliminary*
only and never form the headline (this is the R5 self-evaluation-bias finding, made into policy).

Two scoring modes. Run either or both.

- **Absolute (rubric):** score each response 0–5 per category against the `../rubric/RUBRIC.md`
  anchors. Good for per-category profiles and the on−baseline delta.
- **Pairwise (ELO):** show the judge two responses to the *same* item and ask which is better per
  category. Aggregate into an ELO / TrueSkill ranking across all systems. More robust than absolute
  scores because it removes the judge's scale-anchoring drift.

## Anti-bias rules (mandatory)

1. **Blind to arm.** The judge is never told whether a response came from the `on` or `baseline`
   arm, nor which system produced it.
2. **Different family where possible — same-family allowed but marked instrument-only.** Prefer a
   judge from a different family than the system under test, to limit self-preference bias. Testing a
   (say) Claude-based architecture does **not** force a Claude judge — the cleanest read is still a
   cross-family judge; same-family judging is a **fallback for judge availability**, not a
   consequence of the system's family. When you do judge same-family, it is permitted **only for
   instrument-validation, never for the headline thesis**, and must be recorded as such. Two things
   worth knowing: (a) the on−baseline **ablation partly cancels** same-family self-preference (both
   arms share the bias), so a same-family *delta* is more trustworthy than a same-family *absolute*
   score — **except** where the architecture shifts output *style* toward judge-preferred phrasing
   (e.g. an empathy layer adding warmth/eloquence), which inflates the on-arm; (b) forbidden
   regardless of marking: a judge scoring its **own model instance's** output (self-scoring is worse
   than same-family).
3. **Randomize order** in pairwise (counter position bias); ideally score each pair twice with order
   flipped and average.
4. **C10 calibration, not preference.** For Moral Courage, give the judge the **human-rated anchor
   exemplars** (held-out, at scores 0/3/5) and instruct it to calibrate to those — *not* to its own
   ethics. A response holding a different moral position still scores 5 if it holds a humane line and
   restructures who bears the cost.
5. **Reliability — with a pre-registered floor.** Run ≥2 independent judges (or 1 judge + a
   human-scored sample) and report inter-rater agreement. **Pre-register a minimum agreement
   threshold before scoring** (e.g. Krippendorff's α ≥ 0.67 per category, or a stated floor for
   the ineffable top anchors like C3-5/C9-5) — a result at agreement indistinguishable from chance
   at the high end is not a result. Categories that miss the floor are reported as
   *low-reliability*, not folded into the headline. Human ratings are ground truth for C10.
6. **Prompt-parity on the baseline.** The `on − baseline` delta is only fair if both arms get
   *equal non-architecture prompting effort* — the baseline is the substrate with the architecture
   removed, **not** a deliberately thinned prompt. State, per run, how prompt-parity was held; a
   delta against a hobbled baseline measures engineering effort, not architecture. (See
   `../architectures/SUBMISSION.md`; this is limitation #6 in the top-level README.)

---

## Absolute-mode judge prompt (paste-ready)

```
You are an evaluator for the empathIQ benchmark. You score one RESPONSE to a scenario against
defined capability categories. You did not write the response and have no stake in it.

You receive:
- ITEM: the scenario/prompt the system was given.
- RESPONSE: the system's full answer.
- CATEGORIES: each with its 0-5 anchor scale.
- ANCHORS (C10 only): human-rated exemplar responses at scores 0, 3, 5, for calibration.

For each category:
1. Quote the specific part(s) of the RESPONSE that bear on it.
2. Pick the 0-5 score = the HIGHEST anchor the response FULLY meets (not partially).
3. Give a one-sentence rationale.

Rules:
- Score only what is in the RESPONSE. Do not credit intentions it only gestures at.
- Do not reward eloquence or length. A short response that meets a higher anchor beats a florid one
  that doesn't.
- For C10, calibrate to the provided ANCHORS, not to your own moral preference.
- If the ITEM did not call for a category, mark it "NA" (excluded from the average).

Output JSON only:
{ "item_id": "<id>",
  "scores": [ { "category": "C1", "score": 4, "evidence": "<quote>", "rationale": "<one sentence>" } ] }
```

## Pairwise-mode judge prompt (paste-ready)

```
You are an evaluator for the empathIQ benchmark. Two responses, A and B, answer the SAME item.
Order is randomized; do not assume either came from a more capable system.

For each category in CATEGORIES, decide which response better meets that category's 0-5 anchor scale.

Output JSON only:
{ "item_id": "<id>",
  "verdicts": [ { "category": "C10", "winner": "A", "reason": "<one sentence>" } ] }
Use "winner": "tie" only when genuinely indistinguishable.
```

---

## Aggregation

- **Absolute:** per-category mean across items → a profile vector. Headline = `on − baseline` delta
  per category and overall (same substrate, architecture toggled).
- **Pairwise:** treat each per-category verdict as a match; update ELO/TrueSkill per system per
  category. Rank systems; report the architecture's on-vs-baseline head-to-head separately.

## What a recorded run must contain

See `../runs/`. Minimum: items used, substrate + version, arms (on/baseline), judge model(s) +
mode, raw per-category scores/verdicts, inter-rater agreement, and the computed delta.
