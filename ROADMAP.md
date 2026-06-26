# empathIQ — Roadmap

*The one thing this sprint is for, the order it happens in, and where we actually are.
Build-log lives in [FOUNDER-SPRINT.md](FOUNDER-SPRINT.md); this is the plan.*

---

## The win condition (one run)

empathIQ exists to settle a single claim:

> **A bounded-empathic architecture beats BOTH a bare model AND a warm-but-unbounded one.**

It is settled by exactly one thing: **a cross-family, external, blind judge run** —
a different model family than the one the architecture runs on, blind to which reply
came from the architecture-on arm vs. the bare baseline, scored against **human-rated
moral-courage anchors**. Everything else (more blocks, a prettier builder, voice output,
nicer diagrams) is instrument and demo. It is not the measurement.

A run that comes back **"no significant lift"** is a *success* of the method, not a
failure — a benchmark that can't kill its maker's pet theory isn't measuring anything.

## The order (deliberately not the obvious one)

The judge run is the climax, but it is **deferred until the instrument is trustworthy** —
you don't spend the expensive, can't-control-the-API measurement on a rig that might be
buggy. So:

1. **Validate the instrument** (same-family is allowed here — it tests the *rig*, never the *thesis*).
2. **Then** run the cross-family judge (the only thing that tests the *thesis*).

Same-family review can debug the instrument; it can **never** confirm the claim. Any
on-thesis delta from a same-family pass is labelled **"instrument check, not a result."**
The judge is **deferred, not dropped.**

## The flip-gate — when the instrument has earned the judge

Do not run the judge until **all four** hold:

1. every `no_<block>` and `only_<block>` path **runs and emits cleanly**;
2. items produce **signed, sensibly-shaped deltas** (not a flat offset);
3. the **c10 moral-courage anchors survive blind human ratification** (a rater who isn't the architect);
4. known instrument gaps are **closed or explicitly accepted**.

## Status

| Day(s) | What | State |
|---|---|---|
| 1 | Benchmark thesis + ship list | ✅ public |
| 2 | The forge (16-block architecture, ablation = the `ab` command) | ✅ public |
| 3 | Test categories (11) | ✅ public |
| 4 | Automated testing + visuals | ✅ public |
| 5 | The turn — "I test the instrument before I trust a number" | ✅ posted |
| 6 | c10 moral-courage anchors (drafted, **await blind ratification**) | ◐ private, gate #3 open |
| 7 | Harder coercion items (held out) | ◐ private |
| 8–9 | Manual usability + voice (walkthrough, guided `new`, `chat`, live narration, tests) | ✅ built |
| — | **Flip-gate instrument-validation pass** (criteria 1–4) | ☐ **the spine — in progress** |
| — | Cross-family judge harness (non-Claude, blind, randomized) | ☐ owed |
| — | Pre-register predicted delta (publicly, before the run) | ☐ owed |
| — | The run — FVPA as first submission, on vs. baseline | ☐ owed (the climax) |
| — | Analysis + honest write-up (null included) | ☐ owed |

**Honest read:** the instrument is rich, usable, and now talks. The **measurement is
unbuilt.** Days 8–9 moved usability hard and the flip-gate not at all; criterion #1 has
its first finding (`only_<block>` drops FINAL → emits nothing, needs INPUT+FINAL kept in).

## The split

- **Holger** — held-out items + the public posts.
- **PCLA** — the blind-verify instrument-validation run + the flip-gate.
- **Eve** — coordinates the human anchor ratings (needs ≥1 thesis-blind rater, not the architect).

## What stays held out (never public)

FVPA prompt text, the c10 anchor exemplars, the hard coercion items, the cross-family
judge key/packet, and any pre-registration packet — these live in the private research
repo and are referenced here **by name only.**
