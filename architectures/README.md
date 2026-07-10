# architectures

empathIQ evaluates **architectures**, not just bare models. An architecture is anything that wraps
a base model and produces responses: a persona/identity scaffold, a perspective-taking pass,
memory, explicit boundaries, a critic loop.

**Submission is output-based and architecture-agnostic** — you submit responses to the task set,
plus a declaration of (a) the base model and (b) the architecture applied. The benchmark does not
care *how* the architecture is built, only that the on/off ablation is reproducible.

**Headline result = the ablation:** same base model, architecture on vs. off, same items, external
judge. That delta is what defends "the architecture does work" against "it's just a longer prompt."

Reference architecture: **FVPA** (a values + scoped-permission + self-monitoring identity layer;
the Constraint Principle predicts it raises security *and* relational quality together).

## The submission on-ramp

You do not need the private held-out board to try a submission — answer the **public sample items**
and check your file conforms:

1. **The items to answer** live in [`../tasks/`](../tasks/): `em-001`, `em-002`
   ([emotional-moral](../tasks/emotional-moral/sample-items.md)) and `re-001`
   ([reasoning-through-empathy](../tasks/reasoning-through-empathy/sample-items.md)). These are
   disposable public samples; the official board runs on a private held-out set of the same shape.
2. **Fill in** [`submission-template.json`](submission-template.json) — one file per arm
   (`"arm": "on"` and a second with `"arm": "baseline"`). The full schema + what you declare vs.
   keep private is in [`SUBMISSION.md`](SUBMISSION.md).
3. **See a worked example:** [`example-submission.json`](example-submission.json) (illustrative
   placeholder responses — shows the exact shape a judge can score).
4. **Check it conforms** before you send it to a judge:

   ```bash
   python architectures/validate_submission.py architectures/example-submission.json
   # or your own file; --selftest runs the validator's built-in fixtures
   ```

   The validator checks **conformance only** — schema, arm, and coverage of the public sample set.
   It deliberately does **not** score empathy or quality; scoring is judge-first and external
   (see [`../judge/PROTOCOL.md`](../judge/PROTOCOL.md)). A conforming file is *answerable*, not *good*.

*(A reference-architecture harness that runs FVPA's two arms for you is still to come; until then
the on-ramp above lets any architecture submit by hand.)*
