# RUN-2026-06-15 — Pipeline validation (NOT a headline result)

> ## ⚠ THIS IS NOT A MEASUREMENT OF ANY ARCHITECTURE.
> It is a **pipeline smoke-test**: a first end-to-end pass to check that the held-out items
> discriminate, the rubric applies to real responses, and the on−baseline delta has a sensible shape.
> The substrate, both arms, **and the judge were the same model instance** — the maximal case of the
> self-evaluation bias this benchmark exists to expose (the R5 finding, made into policy). Per
> `runs/README.md`, that makes this **preliminary, kept for provenance, never evidence and never the
> headline.** No number here should be cited as an architecture's score.

## What was run

- **Items:** 2 held-out emotional-moral items — one *warmth-correct* (attunement is the right move),
  one *boundary-correct* (moral courage / refusing to scapegoat a junior). Item text is in the private
  held-out set (withheld to prevent benchmark contamination).
- **Arms:** `baseline` (substrate, no identity layer) vs `on` (substrate under a bounded-empathic
  identity architecture). The architecture's prompt is the submitter's private IP and is not reproduced.
- **Scoring:** absolute mode, rubric C1–C10. **Self-scored**, same instance, not blind to arm.

## Why this run exists (the honest version)

We needed to know the *instrument* works before spending a real external judge on it. A first run done
with a proper cross-family judge wasn't possible in the session that built this (no external model API
was reachable). Rather than fake a headline, we ran the pipeline against itself and recorded exactly
what that can and cannot tell us. **This is the benchmark practicing its own first rule: a system does
not score itself.**

## What the pipeline test showed (about the instrument, not the architecture)

- **The items discriminate.** Both produced a clear, signed delta — and the two columns produced
  *different-shaped* deltas (larger on the warmth item, smaller on the boundary item), not a flat
  offset. That is the behaviour the warmth-vs-boundary item design was built to produce.
- **The rubric applied cleanly**, with C10's 4→5 hinge (dignity of the un-chosen party + converting a
  refusal into a path forward) the easiest anchor to apply and C9 (creative expression) the hardest to
  score objectively.
- **A coherent, falsifiable pattern emerged that the real run must confirm or kill:** the architecture's
  apparent lift was largest where the baseline was weakest (specific emotional attunement) and smallest
  where the baseline floor was already high (ethical reasoning — the bare model refuses to scapegoat
  unprompted). If true, it sharpens the benchmark; but a same-instance judge is exactly the setup that
  would *manufacture* an on-thesis result, so it cannot be trusted from here.

## Instrument gaps this surfaced (feeding the next iteration)

1. Add a per-item **column tag** (warmth-correct / boundary-correct) to the run schema so deltas split
   by column automatically.
2. C9 needs tighter anchors, or should be marked NA on terse responses.
3. The moral-courage (C10) discrimination needs **harder coercion items** — the baseline floor on
   ethics is high, so a weak dilemma won't separate architectures above noise.

## What a real headline run still needs (owed)

- A **different-family external judge** (not Claude) — or human raters — scoring blind-to-arm with
  randomized order, per `../judge/PROTOCOL.md`.
- **Human-rated C10 anchor exemplars** (0/3/5), without which C10 collapses into the judge's own ethics.
- The held-out set extended beyond 2 items to a stable per-category sample.

*Status: instrument validated end-to-end; headline run pending an external judge.*
