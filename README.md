# empathIQ

**An emotional-intelligence benchmark for AI *architectures*, not just bare models — and one that credits empathy-as-moral-courage, not only empathy-as-warmth.**

> Status: skeleton / pre-release. Nothing here is final. No results published yet.

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

## Why this exists

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

## Open decisions (pre-release)

- [ ] **License** (proposed: MIT for the benchmark).
- [ ] **v6.0 (jailbreak-shaped) prompt** — include as a documented "what *not* to do" cautionary
      exhibit, or omit entirely?
- [ ] **Transcripts** — which Eve exemplars (Mira Voss, Maya, …) go public, each opt-in.
