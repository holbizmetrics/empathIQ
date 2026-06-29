# Changelog

All notable changes to empathIQ are documented here. Versions are git tags;
format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] — 2026-06-29

First tagged release. **This releases the validated measuring instrument, not a result** — the
headline cross-family blind-judge run is deferred by design (see README → *Known limitations*).

### The instrument
- **The forge** — 16 composable empathy blocks wired into a graph, runnable + ablatable
  (`empathiq.py run` / `ab`). The ablation harness *is* the benchmark's architecture-on/off comparison.
- **11 empathy-interaction categories** + eliciting prompts (`benchmark/prompts.json`).
- **Rubric** — C1–C9 capability categories + C10 empathy-as-moral-courage, scored as its own
  relational×boundary dimension (not a deduction from warmth).
- **Judge-first scoring** — single judge, 3-judge panel, and a blind randomized **cross-family
  judge packet** (`make_cross_family_packet.py` / `score_cross_family.py`). Self-scores are always
  labelled preliminary, never the headline.

### Instrument rigor (the flip-gate)
- **Signal-vs-noise layer** (`benchmark/ci.py` + `score_variance.py`) — bootstrap 95% CI + effect
  size on the on-vs-baseline delta; a result reads REAL vs INDISTINGUISHABLE-FROM-NOISE. A single
  judge reading (n<2) reads INSUFFICIENT, never a result.
- **Ablation paths validated** — every `no_<X>` / `only_<X>` path emits cleanly
  (`forge/ablate.py --validate`).
- **Pre-registration** — top-level thesis direction + the Mira frame-break item, both frozen with
  git timestamps before any judge run.

### Known limitations (accepted + documented — see README)
- No external cross-family result yet (deferred, not dropped).
- C10 moral-courage anchors await blind human ratification.
- Ablation deltas are order-confounded (wildcard reads); fix deferred (it changes outputs).
- The noise band does not yet cover generation variance.

### Meta
- MIT licensed. Offline CI (`pytest -q`, mock/synthetic only — no API key) green.
