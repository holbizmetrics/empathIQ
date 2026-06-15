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
the Constraint Principle predicts it raises security *and* relational quality together). Whether the
exact FVPA prompt text is published here is an open pre-release decision (see root README).

*(Submission template + reference-architecture harness to be added. Empty until then.)*
