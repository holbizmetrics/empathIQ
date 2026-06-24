# Benchmark harness

This directory holds the **runnable** EmpathiQ benchmark: the 11 empathy-interaction
categories (`empathy-categories.md`), one eliciting prompt per category
(`prompts.json`), and the scripts that run an architecture across them and score the
results.

The unit of evaluation is the **architecture** (see the repo README): the headline
comparison is an *ablation* — the same base model with the architecture on (`A_full`,
16 blocks) vs. off (`D_first_order_only`, 4 blocks).

## The flow

```bash
# 1. RUN — push the 11 category prompts through the architecture variants.
#    Grading is DEFERRED by design: this collects outputs to observe, it does not score them.
python benchmark/run_battery.py --mock                 # full battery, offline, instant (dry-run)
python benchmark/run_battery.py                          # real, via the claude CLI (no API key)
python benchmark/run_battery.py --only ethical_not_knowing --variants A_full,D_first_order_only
#    -> writes benchmark/results/battery-<stamp>-<mock|real>.jsonl

# 2. SCORE — judged competence scorecard over the stored real outputs (single LLM judge).
python benchmark/score_battery.py --mock               # offline structure dry-run
python benchmark/score_battery.py                       # real judge over the stored outputs
#    -> writes benchmark/results/scorecard-<stamp>-<...>.jsonl

# 3. PANEL — three variant-blind judges with different framings, as a tie-breaker pass
#    (neutral / depth-valuing / directness-valuing) when the single judge is ambiguous.
python benchmark/score_panel.py                         # 3 x N judge calls
```

`run_battery.py` defaults to the public demo persona **`sol`**. Real runs are many
`claude` CLI calls (each block is one call), so scope with `--only` / `--variants`
before going wide. Run artifacts land in `results/` and are git-ignored (regenerated,
not source).

## Two metric tiers (the honest part)

- **Mechanical** (`nodes_run`, `latency_ms`, `final_chars`, hashes) — measured from the
  run, no model in the loop. `run_battery.py` emits only these.
- **Judged** (`frame_fit`, `register_match`, `format_adherence`, `instruction_following`,
  `restraint_appropriateness`, `overall`) — produced by an LLM judge and always labelled
  `llm-judge-single` / `llm-judge-panel` (noisy by design; a single judge is never
  treated as ground truth).

Two disciplines are baked into the scorers:
- **Variant-blind** — the judge sees only `(situation, reply)`, never which architecture
  produced it (leak-line discipline: conclusions must not enter the judge's prompt).
- **Noise-honest** — every score carries its source; we do not pretend one judge is truth.

## What is deliberately *not* here (held out)

For benchmark integrity and IP, some pieces live only in the private research repo and
are **never published** — publishing them would let a submitter game the benchmark:

- **C10 (moral-courage) anchor exemplars** and the **cross-family judge key** — the
  scorers read these from local files at scoring time; they are not in this public repo.
- **Cross-family model-robustness validation** (running the same outputs through a
  non-Claude judge to test whether an effect is model-robust or a same-family artifact)
  is a **research pass**, run in the lab, not part of the shipped harness.

So this repo lets you *run and score* the benchmark; the held-out keys stay operator-side
by design.
