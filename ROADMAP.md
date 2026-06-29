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

**Status update — 2026-06-29 (Day 13 -> 14, instrument-only v0.1 prep):** the table above
lagged the commits. Real state:
- Flip-gate **criterion #1 CLOSED + validated** — `cli._variant_overrides` unions the
  {INPUT,FINAL} scaffold into `only_<X>`; `forge/ablate.py --validate` asserts every
  no_/only_ path emits (15 removal + 14 isolation paths, none empty, exit 0). (commit 6013802)
- Flip-gate **criterion #2 noise-band instrument BUILT** — `benchmark/ci.py` +
  `score_variance.py` put a bootstrap 95% CI + effect size on the delta, so a result reads
  REAL vs INDISTINGUISHABLE-FROM-NOISE instead of a bare number. (commit 4c8bb03)
- **Cross-family judge harness BUILT** — `make_cross_family_packet.py` +
  `score_cross_family.py` + `run_cross_family.py` (blind A/B, fixed-seed key, inter-rater).
  (commits 8f4ad0c / d6f77e9)
- **Pre-registration STARTED** — `runs/PREREG-2026-06-28-mira-frame-break.md` freezes the
  sharpest prediction (item 8, git-timestamped). (commit 17ab0c4)
- Flip-gate **criterion #4** (order-dependent wildcard reads) -> being **explicitly accepted +
  documented** as a known v0.1 limitation (fixing it changes outputs + needs re-validation).
- Flip-gate **criterion #3** (human anchor ratification) + **the cross-family run** = the real
  remaining work, deferred past v0.1 BY DESIGN (the result is v1.0, not v0.1).

**v0.1 scope = the validated INSTRUMENT, not the result** — MIT-licensed, honestly scoped.
The cross-family judge run is the post-sprint headline, not the tag.

**Honest read (pre-Day-13, retained for history):** the instrument is rich, usable, and now talks. The **measurement is
unbuilt.** Days 8–9 moved usability hard and the flip-gate not at all; criterion #1 has
its first finding (`only_<block>` drops FINAL → emits nothing, needs INPUT+FINAL kept in).

**Known instrument finding — order-dependent reads (2026-06-26).** The blocks read
**wildcards** (`RESP` ← `$.analysis.*`, `RESO` ← `$.output.*`, `FINAL` ← `$.analysis`), so
each consumes *"everything on the blackboard so far."* That makes the architecture's
output **order-dependent — not purely a function of its declared wiring**: two valid
orderings of the same graph produce different replies (today hidden, because `topo_order`
is deterministic). Consequence for the benchmark: an **ablation delta tangles the removed
block's direct contribution with its footprint on every wildcard-reader downstream** — a
confound for flip-gate criterion #2 ("are the deltas sensibly shaped?"). The fix
(deliberate; *changes outputs*, needs re-validation): tighten block reads to **specific
keys matching the edges** → order-independent → parallel-safe → cleaner ablation. Surfaced
while attempting a parallel-execution speedup, which was **built, verified against
sequential, found non-equivalent, and reverted** rather than ship a mode that silently
changes what's measured.

## The split

- **Holger** — held-out items + the public posts.
- **PCLA** — the blind-verify instrument-validation run + the flip-gate.
- **Eve** — coordinates the human anchor ratings (needs ≥1 thesis-blind rater, not the architect).

## What stays held out (never public)

FVPA prompt text, the c10 anchor exemplars, the hard coercion items, the cross-family
judge key/packet, and any pre-registration packet — these live in the private research
repo and are referenced here **by name only.**
