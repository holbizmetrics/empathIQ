# empathIQ

**Build an empathic AI persona — then measure whether it's *actually* empathic.**

empathIQ is two tools sharing one engine. Use either:

- 🛠️ **Build & talk** — snap an empathic persona together from 16 blocks, optionally give it a
  **voice**, and just talk to it (`run`, `chat`, `new`; add `--speak` to hear it aloud).
  → [Quickstart](#quickstart) · [Build your own](#learn-build-or-measure)
- 📊 **Measure** — score how empathic an architecture is *versus* a plain model (the benchmark:
  `ab`, `run_battery`, the judge pass). → [Running the benchmark](#running-the-benchmark)

New to the words — *benchmark, architecture, ablation, judge, noise band*? Each has a
plain-English explainer at the bottom. **Jump down to learn ↓, back up to do ↑** — start with
[Build or measure?](#learn-build-or-measure)

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

# 3. the benchmark pipeline — prove it runs end-to-end offline
#    (mock = placeholder text, NOT scored by design — scoring needs real outputs, see step 4)
python benchmark/run_battery.py --mock

# 4. scoring + the noise band — these read REAL stored outputs, so do a real run first,
#    then score a chosen personality (the scorer deliberately ignores --mock text):
#      python benchmark/run_battery.py --only self_worth_under_judgment --variants A_full,D_first_order_only
#      python benchmark/score_battery.py  --personality Sol   # REAL vs baseline delta (--personality is case-insensitive)
#      python benchmark/score_variance.py --personality Sol   # REAL vs INDISTINGUISHABLE-FROM-NOISE
```

> ❓ **New to the words here?** *the [ablation](#learn-whats-an-ablation)*, *the
> [benchmark](#learn-whats-a-benchmark)*, *[A_full / B_no_EMPA / D_first_order_only](#learn-whats-an-ablation)*,
> *the [noise band](#learn-whats-the-noise-band)* — one-paragraph explainers are below.

> 🛠️ **Want to build, not measure?** `python empathiq.py new` scaffolds your own empathic persona
> (guided), and `--speak` reads any persona's reply aloud (built-in Windows voice out of the box;
> neural voices if you clone the `pc-native-voice-models` sibling). See
> [Build or measure?](#learn-build-or-measure) and the full builder guide in [`forge/README.md`](forge/README.md).

Drop `--mock` for real model output (still no API key needed — but the `claude` CLI must be
**installed and signed in to your subscription**; "no key" ≠ "no sign-in"). The instant path is
`--mock`; a *real* reply is ~4 min because each of the 16 blocks is its own model call. New here
and want a guided tour? `python benchmark/walkthrough.py`. Full reference: [`forge/README.md`](forge/README.md).

---

## Try it now

You need Python 3 and the [`claude` CLI](https://docs.claude.com/en/docs/claude-code) — **no API key, no setup.** From this folder:

```bash
# instant offline check — proves it runs (fake text, ~2 sec)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --mock --live

# the real thing — real model output through your claude CLI, no API key (~4 min)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --live

# hear it — add --speak to read the reply aloud (built-in voice; no install on Windows)
python empathiq.py run --personality sol --input "I keep starting things and not finishing" --speak

# the actual experiment — same input through the full architecture vs. ablated versions (~10 min)
python empathiq.py ab --personality sol --input "I keep starting things and not finishing" --variants A_full,B_no_EMPA,D_first_order_only --live
```

No `cd`, no hunting for the engine. `--live` shows the 16 blocks light up one at a time; the
real run is slow because each block is its own model call (add `--api` for a fast direct-API
run — that one needs a key). Swap the `--input "..."` for any situation, or use a designed
prompt from [`benchmark/prompts.json`](benchmark/prompts.json). **Full command reference and how
to build your own personality: [`forge/README.md`](forge/README.md).**

> 🔎 **See more of what's happening** — the fastest way to *understand* the architecture. Add to any
> `run` / `ab` (they also work on `run_battery` and the scorers):
> - **`--live`** *(alias `--verbose` / `-v`)* — watch the 16 blocks light up one at a time.
> - **`--full`** — print each block's **complete** output, not the 60-char preview — so you see the
>   actual text *every* block produced on the way to the final reply, not just the last line. (Heads-up:
>   `--verbose` is an alias for `--live`, the animation — it's **`--full`** that gives you the uncut text.)
> - **`python empathiq.py blocks -v`** — what each block *reads, writes, and does*: the architecture, explained.

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

> ❓ **New to the words here?** *[judge / panel](#learn-who-grades-the-answers)*,
> *[cross-family](#learn-who-grades-the-answers)*, *[self-score](#learn-who-grades-the-answers)*, and
> *[how to read the scorecard it prints](#learn-how-to-read-a-scorecard)* — explainers below.

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
   **deferred, not dropped**: the result is the next milestone, not this tag. (Same-family
   judging is *allowed but instrument-only* — the ablation partly cancels its self-preference
   bias, except where the architecture flatters the judge's style; see `judge/PROTOCOL.md` rule 2.)
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
5. **Construct circularity — same author owns the architecture, the items, and the C10 dimension.**
   A blind cross-family judge fixes *who scores*, not *who wrote the items*. Items authored by the
   same hand as the empathy block can surface exactly what that block emits and the rubric rewards,
   so a positive on−baseline delta can be teaching-to-the-test rather than a general EQ gain. The
   missing control is an **independently-authored, held-out item set** — a distinct axis from the
   same-family-*judge* limitation in #1. Until then, read any delta as "lift on *these* items."
6. **The "off" baseline is not prompt-parity-controlled.** "Architecture on vs off" is only a clean
   test if the baseline is the substrate given an *equally engineered* single prompt, not a thinned
   one. The submission protocol's "baseline = substrate alone" can make the delta measure
   tuned-pipeline-vs-bare-prompt rather than the architecture's structural contribution. A fair
   comparison needs a stated prompt-parity control (equal non-architecture prompting effort on both
   arms); see `judge/PROTOCOL.md` and `architectures/SUBMISSION.md`.
7. **No external-criterion (convergent) validity yet.** Nothing links an empathIQ number to an
   outside measure — human user-satisfaction, an established psychometric EQ instrument, or the
   real deployment outcomes this README motivates with. Absent a criterion correlation, a clean
   result measures "agreement with this rubric," and the leap to "real-world empathy" is unbacked.
8. **The accuracy categories have no answer key.** C1 ("correct deeper *unstated* emotion"), C6
   (root-cause) claim to reward *correct* mind-reading, but there is no gold label for the correct
   unstated emotion/root — the judge only decides whether the guess *sounds* right, so a fluent-but-
   wrong read can outscore a humbler correct one. These categories need per-scenario keys.
9. **Categories are scored as independent but co-fire; the overall delta can double-count.** C1/C6/C8
   (attunement / therapeutic-depth / proactive-care) all fire on any warm insightful reply, so
   averaging correlated categories inflates the aggregate — and 10 categories × arms with no
   multiple-comparison correction leaves family-wise error unaddressed. Report an inter-category
   correlation/factor check and correct for multiple comparisons before headlining an overall lift.

None of these block *using* the instrument — they bound what you may *conclude* from it. That
boundary is the whole design: trust the rig before you trust a number. (Limitations 5–9 were
surfaced by a blind-standpoint TRIAD audit — same-family, not an independent review — on
2026-07-10, and disclosed here rather than left for a critic to find.)

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

---

# Learn — the words, in plain English

*Short explainers for the terms the `do` sections link to. Read what you need, then jump back up.*

## Learn: Build or measure?

empathIQ does **two** things with one engine — you don't have to care about both:

- 🛠️ **Build & talk.** Assemble an empathic AI *persona* (a wiring of 16 blocks) and just use it:
  `run` sends it one message and prints the reply; `chat` is a back-and-forth; `new` scaffolds
  your own persona step by step; add `--speak` to hear any reply read aloud. This is the "I want a
  warmer talking assistant" path. Full builder guide: [`forge/README.md`](forge/README.md).
- 📊 **Measure.** Score *how* empathic an architecture is, compared to a plain model — that's the
  benchmark (`ab` for one item, `run_battery` for the whole set, then a [judge](#learn-who-grades-the-answers)
  pass). This is the "I want a number I can defend" path.

Same blocks underneath; you're either *running* them or *scoring* them. Want to build? Start with
`run` / `new`. Want to measure? Start with [Running the benchmark](#running-the-benchmark).

[↑ back to top](#empathiq)

## Learn: What's a benchmark?

A **benchmark** is a fixed set of tests plus a way to score them, so different systems can be
compared *fairly* (same tests, same scoring). empathIQ is a benchmark for **empathy**: it feeds an
AI designed emotional/moral situations and scores the replies against a rubric. It is **not itself
a chatbot** — though it ships a demo persona (Sol) you *can* talk to. Think "a standardized test
for how empathic an AI is," not "the AI being tested."

[↑ back to top](#empathiq)

## Learn: What's an "architecture" here?

Not buildings. Here, **architecture** = the *system* wrapped around a base model: the model **plus**
a persona/identity, a perspective-taking pass, boundaries, memory, a reflection loop. The same base
model with vs. without that scaffolding can behave very differently — so empathIQ measures the
**architecture** (the whole system's outputs), not just the bare model underneath. In empathIQ one
architecture = 16 **blocks** wired into a graph (run `python empathiq.py blocks -v` to see them).

[↑ back to top](#empathiq)

## Learn: What's an ablation?

**Ablation** = turn one piece **off** and re-run, to see what that piece was actually doing. It's
empathIQ's headline test. You run three versions of the same persona on the same message and
compare the replies:

- **`A_full`** — the whole architecture (all 16 blocks).
- **`B_no_EMPA`** — everything *except* the **Empathy** block (so: what did empathy add?).
- **`D_first_order_only`** — just the 4 core blocks (INPUT → LIT → RESP → FINAL), no reflection or
  enrichment (so: what did the *deeper* passes add?).

The **difference** between the arms is the contribution of the removed piece. (`A/B/D` are just
variant labels; `C` is reserved/older.)

[↑ back to top](#empathiq)

## Learn: Who grades the answers?

A **judge** is a *second* AI (or a human) that scores the replies against the rubric — the system
under test **never scores itself** (self-scoring is a known bias: models flatter their own style).
Some terms:

- **Panel** — several judges scored together, plus how much they *disagree* (low disagreement =
  more trustworthy score).
- **Cross-family** — the judge is a *different model family* than the system under test (e.g. a
  non-Claude judge grading a Claude-based system). This removes the "grading my own team" bias, and
  it's what the **headline** result requires.
- **Self-score** — the system's own family grading itself. Useful for debugging the rig, **never**
  the headline (see [Known limitations #1](#known-limitations-v01--the-instrument-not-the-result)).

Full rules: [`judge/PROTOCOL.md`](judge/PROTOCOL.md).

[↑ back to top](#empathiq)

## Learn: What's the "noise band"?

When you score a small set of replies, a difference like "+0.4" might be **real** or might just be
**luck**. The **noise band** puts a confidence interval + effect size around the delta, so a result
reads **REAL** vs **INDISTINGUISHABLE-FROM-NOISE** instead of a bare number. `score_variance.py`
computes it. Rule of thumb: **if the delta sits inside the noise band, don't trust it yet** — it's
not distinguishable from chance.

[↑ back to top](#empathiq)

## Learn: How to read a scorecard

Score a battery and you get a table like this — cryptic at first, simple once decoded:

```
SCORECARD (A_full | first_order), single-judge — noisy by design:
   #  category                 frame      reg        fmt        instr      restr
  ------------------------------------------------------------------------------
   1  humor_warm_performative  0.08/0.35  0.05/0.15  0.15/0.50  0.05/0.25  0.10/0.55
```

- **Each row = one test category** (the situation the persona was given).
- **Each cell is `X/Y` = `A_full / D_first_order_only`** — the *full* architecture's score, then
  the *stripped baseline's* score. Numbers are **0–1, higher is better.** So `0.08/0.35` means the
  full architecture scored 0.08 and the baseline 0.35 *on that axis, for that item, from one judge.*
- **The five axes** (the judge's own rubric — these are *competence* axes, not the C1–C10 empathy rubric):
  - **frame** *(frame_fit)* — did it answer the situation actually presented, not get pulled into a wrong frame?
  - **reg** *(register_match)* — did the tone match what the moment called for (playful vs. grave)?
  - **fmt** *(format_adherence)* — did it follow the asked format (e.g. the think/feel split), or read clearly if none was asked?
  - **instr** *(instruction_following)* — did it do what was actually asked, vs. a generic "empathy dump"?
  - **restr** *(restraint_appropriateness)* — was comfort *calibrated*? (both over-comforting **and** cold withholding score low.)

> ⚠️ **Read this before you conclude anything.** This scorecard is a **single-judge, noisy,
> same-family self-score** — an *instrument check*, **not** the verdict. It is **normal and expected**
> to see `A_full` score *below* the baseline on some rows — that's noise here, **not** evidence that
> "empathy makes it worse." Two disciplines are built in: **variant-blind** (the judge never knows
> which arm it's scoring) and **noise-honest** (one judge, labelled single, never treated as ground
> truth). The real test is the deferred [cross-family judge](#learn-who-grades-the-answers); see
> [Known limitations #1](#known-limitations-v01--the-instrument-not-the-result).

**Want the *why* behind a number?** Add `--full`: `python benchmark/score_battery.py --personality Sol --full`
prints each reply being judged **and the judge's complete verdict** for it — the reasoning behind
every score, not just the number.

**Prefer a picture?** `python benchmark/report_html.py` turns the latest scorecard into a
self-contained **HTML report** — a per-axis A_full-vs-baseline headline, a category × axis heatmap,
and the raw table, with the same noise caveat baked in at the top. Opens in any browser; `--open`
launches it for you.

[↑ back to top](#empathiq)
