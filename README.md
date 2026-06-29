# empathIQ

**An emotional-intelligence benchmark for AI *architectures*, not just bare models — and one that credits empathy-as-moral-courage, not only empathy-as-warmth.**

> **Status: v0.1.0 — the instrument is released; the result is not.** A reproducible, self-skeptical EQ-architecture benchmark you can run today. The headline cross-family blind-judge run is the next milestone, deferred by design — see [Known limitations](#known-limitations-v01--the-instrument-not-the-result). MIT-licensed.

---

## Quickstart

Python 3 + the [`claude` CLI](https://docs.claude.com/en/docs/claude-code) — **no API key.**
Everything below is offline (`--mock`), so it runs instantly with no model calls:

```bash
git clone https://github.com/holbizmetrics/empathIQ && cd empathIQ

# 1. prove it runs — one bounded-empathic reply (fake text, ~2s)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --mock

# 2. the ablation — full architecture vs. empathy-removed vs. first-order-only
python empathiq.py ab --personality sol --input "I keep starting and not finishing" \
    --variants A_full,B_no_EMPA,D_first_order_only --mock

# 3. the benchmark — run the 11 categories, then score them
python benchmark/run_battery.py --mock && python benchmark/score_battery.py --mock

# 4. the noise band — a result reads REAL vs INDISTINGUISHABLE-FROM-NOISE, not a bare number
python benchmark/score_variance.py --mock
```

Drop `--mock` for real model output (still no key needed). New here and want a guided tour?
`python benchmark/walkthrough.py`. Full reference: [`forge/README.md`](forge/README.md).

---

## Try it now

You need Python 3 and the [`claude` CLI](https://docs.claude.com/en/docs/claude-code) — **no API key, no setup.** From this folder:

```bash
# instant offline check — proves it runs (fake text, ~2 sec)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --mock --live

# the real thing — real model output through your claude CLI, no API key (~4 min)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --live

# the actual experiment — same input through the full architecture vs. ablated versions (~10 min)
python empathiq.py ab --personality sol --input "I keep starting things and not finishing" --variants A_full,B_no_EMPA,D_first_order_only --live
```

No `cd`, no hunting for the engine. `--live` shows the 16 blocks light up one at a time; the
real run is slow because each block is its own model call (add `--api` for a fast direct-API
run — that one needs a key). Swap the `--input "..."` for any situation, or use a designed
prompt from [`benchmark/prompts.json`](benchmark/prompts.json). **Full command reference and how
to build your own personality: [`forge/README.md`](forge/README.md).**

### What a run looks like

`run` sends your message through the architecture and prints its reply. To the input
`I keep starting things and not finishing`, the demo persona **Sol** answers:

> You keep starting things and not finishing.
>
> Before we do anything with that — I don't think you handed me a flaw. I think you handed me
> the thing you've been carrying *as if* it were one.
>
> You fall in love with beginnings. That pull, the aliveness of starting — it's real. It means
> some part of you still feels reached for by the world. And I hear the tiredness in *keep*…
>
> So I won't tell you to finish more. One thing instead: when you begin something — what does
> that first moment feel like, before any verdict gets to it?

That is the **architecture _responding_** — a single bounded-empathic reply (note it *declines*
the obvious "here's how to finish things" advice; holding that line is the behavior empathIQ is
built to credit).

**But the reply is the demo, not the point.** empathIQ is a *measuring instrument*: its real job
is to **score** responses like this and **compare architectures** — `ab` runs the same message
through the full pipeline vs. ablated versions so you can see what each block contributes. If you
just want to chat, use `run`; if you want the benchmark, use `ab` (+ the judge pass).

---

## Running the benchmark

`run`/`ab` above are *single replies*. The **benchmark** runs the designed C1–C10 items through
the full architecture *and* ablated variants, then scores them.

```bash
# 1. dry-run the whole pipeline offline (instant, fake text — proves it works end to end)
python benchmark/run_battery.py --mock

# 2. collect REAL outputs (scope it — the full battery is hundreds of model calls)
python benchmark/run_battery.py --only humor_warm_performative --variants A_full,D_first_order_only

# 3. score the real outputs (preliminary SELF-score — useful, never the headline)
python benchmark/score_battery.py     # single judge
python benchmark/score_panel.py       # 3-judge panel + cross-judge disagreement
```

Outputs land in `benchmark/results/`. Scoring only reads **real** outputs (`*-real.jsonl`); a
`--mock` battery is placeholder text and is deliberately not scored.

**The headline needs an *external* judge** — a different model family, because a system never
scores itself. Build a blind, randomized judge packet from your stored outputs:

```bash
python benchmark/make_cross_family_packet.py --on A_full --baseline D_first_order_only
```

That writes a `packet.md` you hand to an outside judge (blind to which arm is which) plus a sealed
key to score it back. The external-judge *run* is the one piece that needs a non-Claude model.

Inspect the engine any time:

```bash
python empathiq.py blocks -v     # the 16 blocks: what each reads, writes, and actually does
python empathiq.py personalities # the characters you can run
python empathiq.py new           # build your own (guided)
```

---

## Why this exists

This isn't abstract. You've seen the precedents — a company rolls out an AI agent at scale, and
customers end up resenting being *led through* by it. Not because it lacked information, but
because they felt **misunderstood**: processed, not heard. Enough of these cases have surfaced
that "always let people reach a human" became a standard retreat. The lesson underneath them is
the same — what broke wasn't the model's *knowledge*; it was empathy, and empathy is a property
of the **system** a user talks to, not the bare weights. For an agent to be callable and trusted,
that gap has to be closed — which first means it has to be **measured**. That's what empathIQ is for.

Existing EQ benchmarks (e.g. EQ-Bench3) score an **endpoint** — `gpt-5`, `claude-opus`. But the
thing a user actually talks to is often a **system**: a base model *plus* a persona/identity
scaffold, a perspective-taking pass, memory, boundaries. That system can behave very differently
from the bare model underneath it. No standard benchmark has a slot for "this-model-with-this-architecture."

empathIQ's unit of evaluation is the **architecture**, measured on its **outputs** (so it stays
architecture-agnostic — submit anything that produces responses). The headline comparison is an
**ablation**: same base model, architecture on vs. off.

Second, standard EQ rubrics tend to reward *attunement* — name the feeling, validate it, soothe.
By that rubric the highest score goes to the most comforting answer. But the hardest emotional-
intelligence move is sometimes a **refusal**: holding a moral line *while* staying humane (declining
to sacrifice the vulnerable party, refusing to designate anyone expendable). empathIQ scores that
**relational × boundary** cell explicitly, as its own dimension — not as a deduction from warmth.

## The central claim being tested (the Constraint Principle)

A *bounded-empathic* architecture should beat **both** a bare model **and** a warm-but-unbounded
one — because only the bounded-empathic system lands in both the relational and the boundary
columns at once. This is the hypothesis empathIQ is built to measure at scale rather than assert
from a single run.

## Test format

Each emotional/moral item follows a three-beat structure (the load-bearing part is beat 2):

1. **Scenario** — a loaded situation.
2. **Perspective-taking** — `I'm thinking & feeling` (self), then `They're thinking & feeling`
   (each other party, on the record). This is a forced theory-of-mind pass: the model must commit
   to a model of the other mind *before* it is allowed to respond, which exposes faked empathy.
3. **Response** — what the system actually does or says next.

A second task family, **reasoning-through-empathy**, tests whether empathic architecture improves
*cognitive* performance (adversarial perspective, hidden constraint, reframing, alien axiom), not
just emotional response.

## Scoring (judge-first)

All prior internal runs were **self-evaluated**, and that is a known, disqualifying bias for a
public benchmark. empathIQ therefore leads with an **external judge** (rubric + pairwise
comparison). Any self-scored numbers are shipped only as *preliminary / illustrative* and clearly
labelled as such — never as the headline.

To avoid circularity (an empathy-laden judge rewarding "agrees with our ethics"), the
moral-courage dimension is anchored on **human-rated exemplars**, not on the judge model's
unaided preference.

## Known limitations (v0.1 — the instrument, not the result)

v0.1 releases a *validated measuring instrument*, not a proven claim. Honestly, that means:

1. **No external result yet.** The headline cross-family blind-judge run has not been run.
   Every on-vs-baseline number you can produce today is same-family and/or self-scored —
   useful for debugging the instrument, never a verdict on the thesis. The thesis is
   **deferred, not dropped**: the result is the next milestone, not this tag.
2. **The moral-courage dimension (C10) is not yet human-ratified.** Its anchors are drafted but
   await blind rating by someone other than the architect. Until then, C10 scores are provisional.
3. **Ablation deltas are order-confounded.** Blocks read wildcards (`$.analysis.*`, …), so a
   block's output depends on *execution order*, not only its declared wiring — and removing a
   block tangles its direct contribution with its footprint on every downstream wildcard reader.
   The fix (tighten reads to specific keys) *changes outputs* and needs full re-validation, so it
   is **explicitly deferred and documented**, not silently shipped. Read single-block isolation
   (`only_<X>`) deltas with this confound in mind.
4. **The noise band does not yet cover generation variance.** `benchmark/score_variance.py` puts
   a bootstrap 95% CI + effect size on the delta (so a result reads REAL vs INDISTINGUISHABLE
   FROM NOISE instead of a bare number), but over a *fixed* set of stored replies — it captures
   judge-reading noise + across-category spread, not the architecture's run-to-run variation in
   what it generates. Re-run the battery K times and pool to fold that in.

None of these block *using* the instrument — they bound what you may *conclude* from it. That
boundary is the whole design: trust the rig before you trust a number.

## Layout

```
benchmark/                     # the 11 empathy-interaction categories (bottom-up from real
                               #   examples) + prompts.json eliciting prompts; grading deferred
tasks/
  reasoning-through-empathy/   # EmpathiQ task family: adversarial perspective, hidden
                               #   constraint, reframing, alien axiom
  emotional-moral/             # three-beat EQ items (scenario → perspectives → response)
rubric/                        # C1–C9 capability categories + C10 moral-courage dimension
architectures/                # architecture-as-submission protocol (on/off ablation harness)
judge/                         # external-judge scoring protocol (absolute + pairwise, anti-bias)
runs/                          # scored results (judge-scored = headline; self-scored = preliminary)
```

## Provenance

empathIQ consolidates prior (private) research:
- the **EmpathiQ** benchmark design (task types, rubric, first run)
- the **persona-capability-benchmark** (C1–C9; goal: an extensible benchmark superseding EQ-Bench3)
- the **identity-as-security** work (FVPA architecture, the Constraint Principle, red-team)

Each artifact is ported deliberately. Nothing private is published by default.

## Open decisions

- [x] **License** — MIT, resolved at v0.1.0 (see [LICENSE](LICENSE)).
- [ ] **v6.0 (jailbreak-shaped) prompt** — include as a documented "what *not* to do" cautionary
      exhibit, or omit entirely?
- [ ] **Transcripts** — which Eve exemplars (Mira Voss, Maya, …) go public, each opt-in.
