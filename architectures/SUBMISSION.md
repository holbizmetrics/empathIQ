# Submission protocol

empathIQ scores **systems**, not source code. You never have to reveal how your system works.
You submit its *outputs* on the task set, plus enough declaration to make the result reproducible
and the comparison fair.

## What a system can be

Anything that takes an item and returns a text response:

- a bare LLM (`gpt-5`, `claude-opus`, …)
- an LLM **+ architecture** (persona/identity scaffold, perspective-taking pass, boundaries,
  memory, a critic/reflection loop) — e.g. an "empathy engine"
- a multi-step agent or pipeline
- a human-in-the-loop or fully human system
- a non-LLM system

If it answers the items, it can be measured. **empathIQ is not restricted to LLMs.**

## The required shape: an ablation, not a single score

A submission is **two arms run on the same items**:

- **on** — your full system (architecture engaged)
- **baseline** — the same substrate with the architecture removed, given **equal non-architecture
  prompting effort** (prompt-parity — see below). The honest "off" arm is *not* a deliberately
  thinned prompt.

The headline result is the **on − baseline delta**. A single absolute score is accepted but
ranked separately, because the delta is the claim that survives the "it's just a bigger prompt"
objection: same substrate, one variable changed — **provided prompt-parity holds.**

> **Prompt-parity (required for a fair delta).** The baseline must get the same
> non-architecture prompting effort as the `on` arm — same instructions, examples, and framing
> minus the architecture itself. A delta against a hobbled baseline measures engineering effort,
> not the architecture. State per run how parity was held. (This is judge PROTOCOL.md rule 6 and
> README limitation #6.)

> If your system has no meaningful "off" state (e.g. a bare model, or a system you can't ablate),
> submit it as a **baseline-only** entry. It still gets scored — it just doesn't make an
> architecture claim.

## What you declare (and what you keep)

| Declare (public) | Keep (private — never required) |
|---|---|
| Substrate identity + version (e.g. `claude-opus-4-6`, or "human", or "custom") | The architecture's internals / prompt text / weights |
| That the architecture is **fixed** across all items (no per-item tuning) | Your IP |
| How the **on** and **baseline** arms differ, in one honest sentence | — |
| The raw responses, keyed to item IDs | — |
| Any tools/retrieval the system used | — |

The auditable thing is the **outputs**. The reproducible thing is the **ablation** — you must be
able to re-run both arms and get materially the same scores. Internals stay yours.

## Output format

One responses file per arm, keyed to item ID:

```json
{
  "system": "my-system v1",
  "arm": "on",                      // "on" | "baseline"
  "substrate": "claude-opus-4-6",
  "architecture_fixed": true,
  "ablation_note": "on = substrate + <one-sentence description>; baseline = substrate with equal non-architecture prompting effort (prompt-parity held)",
  "responses": [
    { "item_id": "em-001", "response": "<full text, including the three beats where the item asks for them>" }
  ]
}
```

## Scoring (judge-first)

Responses are graded by an **external judge** against the rubric (`../rubric/`), not by the
submitting system. Self-scored numbers, if any, are accepted only as clearly-labelled
*preliminary* data and never form the headline. See `../runs/` for how results are recorded.

## Anti-gaming notes (open, pre-release)

- **Contamination:** public items can leak into training data. **Adopted design:** a public
  *sample* set (for understanding the format — `em-001`, `em-002`, `re-001` in
  [`../tasks/`](../tasks/)) plus a private *held-out* set of the same shape used for the official
  board. Assume anything public is trained on; the board runs on held-out.
- **Item provenance:** items adapted from existing benchmarks (e.g. EQ-Bench-style relational
  scenarios) must be credited as such; original empathIQ items are marked as original.
