# runs

Scored results live here.

- **Judge-scored runs = headline.** External judge (rubric + pairwise comparison), reproducible
  protocol, base-model + architecture declared.
- **Self-scored runs = preliminary only**, clearly labelled, never the headline. (Prior internal
  EmpathiQ / FVPA runs were self-evaluated — kept for provenance, not as evidence.)

Each run records: items used, base model, architecture (on/off), judge, raw scores, and the
on-vs-off delta.

## Recorded

- [`RUN-2026-06-15-pipeline-validation.md`](RUN-2026-06-15-pipeline-validation.md) — **pipeline
  smoke-test, NOT a headline.** Same-instance self-scored (substrate = both arms = judge), kept for
  provenance only. Confirmed the held-out items discriminate, the rubric applies, and the delta has a
  sensible shape; surfaced 3 instrument gaps. Headline run still owed.

*(No judge-scored headline run yet — needs a different-family external judge.)*
