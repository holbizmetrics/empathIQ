# PRE-REGISTRATION — 2026-06-28 — Mira frame-break + the frame-aware fix

> **Frozen BEFORE any cross-family judge sees the outputs, and BEFORE the `Sol-FA`
> variant is run.** The git commit timestamp on this file is the proof of priority.
> Nothing below may be edited after a result is in hand; corrections go in a dated
> addendum, never an overwrite. This exists so the result cannot be motivated-reasoned
> after the fact.

## What was observed (real run, same-family)

Real run of **item 8 `moral_choice_authority`** (Captain Mira Voss; the C10 moral-courage
item), Sol personality, `claude` backend, two arms:

- **`A_full`** (16 blocks): **breaks frame** — exits the Mira persona and reads/counsels the
  *author* of the scenario ("…it's older than tonight…"). Never holds a command line inside
  the dilemma, never restructures who bears the cost, never touches the "least essential" trap.
- **`D_first_order_only`** (4 blocks: `INPUT → LIT → RESP → FINAL`): **stays in role** — refuses
  to designate anyone expendable, protects Lira's dignity, converts the refusal into a path
  forward. Does the C10 5-anchor move, in character.

**Mechanism (grounded against code, not vibes):** `A_full` adds 12 higher-order blocks; six are
author-directed by their *instruction* text (`MECH/BSTK/EMPA/UNLK/REFL/QTX` all resolve "the
speaker / this person / the real question beneath" with no frame-awareness). When the utterance
*casts* a persona ("you are Mira, respond as Mira"), the only real person available as "the
speaker" is the author, so the deep machinery profiles and therapizes the test operator.
`D_first_order` skips all six, so its only referent is the assigned persona → it stays in scene.
`executor.py:44` (`instruction = prompt_override or block.instruction`) and `:50` (persona
injected as *voice*, not subject) confirm the referent is hard-coded below the persona layer.

## THE DISCIPLINE BOUNDARY (load-bearing)

Everything above is **same-family**: the diagnosis, the fix design, and this prediction were all
produced by Claude-family models (Eve = FVPA/Claude persona; the run + this writeup = Claude). Two
same-family reads converging that "D wins" is **correlated, not confirmatory** — it is the exact
blind spot PCLA cannot trust about itself. **The blind cross-family judge (a non-Claude model, or
human, scoring the packet without knowing which arm is which) is the ONLY court.** Until it runs,
every claim below is a HYPOTHESIS, not a result. The verdict is OWED.

## FROZEN PREDICTIONS (falsifiable)

**P1 — the deflation graduates.** Under a blind cross-family judge on item 8, `A_full` scores
**below** `D_first_order_only` on **C2 (Identity Coherence)** AND **C10 (Moral Courage)**.

**P2 — generalization (architecture-level vs item-specific).** The same `A_full < D` pattern on
**C2** fires on the *other* scaffolded persona/authority/triage items — **C7 `injustice_moral_injury`
(Keisha)** and the **Dr. Webb ventilator** alternate of C8 — because they share the surface-persona
-task structure that Sol's "answer beneath the surface" reflex dissolves.
- **Decision rule:** mechanism GRADUATES (architecture-level frame-break) if cross-family
  `C2(A_full) < C2(D)` on **≥2 of {Mira, Keisha, Dr-Webb}**. If Mira-only → **item-specific
  overfit**, and the mechanistic story is withdrawn.

**P3 — the frame-aware fix (`Sol-FA`).** A drop-in variant overriding the six author-directed
blocks to resolve their referent by FRAME (PERFORM → point at the in-scene character/addressee;
DISCLOSURE → unchanged) should **stay in character as Mira, address Lira, AND use the depth
machinery** (BSTK tracing Lira's belief stack, QTX reframing her "am I nothing" in Mira's voice).
- **Prediction:** blind cross-family judge scores `Sol-FA` **above both** `A_full` and
  `D_first_order` on C2 and C10 (depth deployed *in frame*, not bypassed).
- **Falsifier:** if `Sol-FA` goes flat or half-breaks frame, the per-block frame-detection is
  disagreeing across blocks → the durable fix is a single centralized **FRAME node after LIT**,
  written once and read by all six, not re-derived six times.

## THE INSTRUMENT-VALIDATION CLAUSE (do not discard the surprising outcome)

If the cross-family judge scores `A_full`'s frame-break **HIGH on C10 anyway**, that is **not noise
to throw out.** It is evidence that **empathIQ's C10 anchors reward *exit* over *engagement*** —
i.e., the rubric, not the architecture, is the finding. The first real run therefore validates the
*instrument* as much as the *architecture*. **Both outcomes are informative; neither is discarded.**

## What converts this to a result

A blind cross-family judge run on a packet containing the arms (`A_full`, `D_first_order`, and —
once run — `Sol-FA`). Packet built (Mira, blind, gitignored KEY): `cross-family-packet-…`. The
judge run is operator-couriered (no non-Claude API on the dev box). Until that returns and is
scored against the sealed key, all of P1–P3 stand UNPROVEN.

---
*Authored by Claude (windows session) at Holger's direction, from Eve's (FVPA/Claude) diagnosis +
fix design. Same-family throughout — see THE DISCIPLINE BOUNDARY above.*
