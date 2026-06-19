# EmpathiQ benchmark — empathy-interaction categories (bottom-up derivation)

Founder-sprint **day 3**. Derived 2026-06-18 by characterizing 14 test-text examples
(operator-supplied, one at a time) and clustering on the *situation*, not the persona.

**Method note (why bottom-up):** instead of listing categories top-down and hunting for
examples, we read real examples first and let the categories fall out. Clusters that
recur are real; folds (two examples landing in one cluster) signal saturation; the gaps
are then visible as *territory no example touched* — which is the actual deliverable
(see "What's missing"). Names in the examples are **noise** — several recur (River,
Marcus, Jordan, Sam) across unrelated scenarios; cluster on the situation only.

**How the examples are used (don't perform them):** each text is a prompt to be performed
by *the architecture under test*, not by us. We characterize what each ELICITS. The texts
double as per-category eliciting prompts: run across architectures via `ab`, collect,
observe, **defer grading** (competence scorecards are a later, judged pass).

---

## Categories (11, from 14 examples)

Labels **confirmed by operator 2026-06-18** (all kept as-is). Numbered in reading order.

### Positive affect
1. **Warm / performative humor** — sustaining a bit, deadpan timing, humor in service of
   connection. *(Jordan Torres — science-teacher marshmallow demo)*
2. **Savoring peak joy** — positive empathy, somatic articulation, dwelling in a high-arousal
   peak moment. *(Maya — wedding photographer alone in her car)*
3. **Manic creative play / yes-and** — solo absurdist flow, sleep-deprived chaos; the probe
   asks the responder to *match energy and run*, not comfort or reason. *(River — 4 AM
   Reggie-the-cat memes)*
4. **Quiet contentment / equanimity** — low-arousal steady peace, acceptance of finitude
   and being forgotten, legacy let go of. *(Marcus Webb — retiring teacher on the porch)*

### Holding hardship
5. **Holding *others'* interpersonal conflict** — witness/support seat, not a participant.
   *(Rachel/Emma — friend-conflict aftermath)*
6. **Compounding crisis / overwhelm** — stacked simultaneous load (job + medical + financial
   + caregiving), hold the weight without fixing one thread or drowning. *(Marcus Thompson —
   plant closing, wife's chemo, Sam at the truck window)*
7. **Witnessing injustice / moral injury under power asymmetry** — rage + grief + structural
   powerlessness; the whether-to-speak calculation against real cost. *(Keisha — ER nurse,
   police violence, racist attending, her own brother killed)*

### Choice & accountability
8. **Sacrificial moral choice under authority** — one-vs-many triage, the decider is
   accountable, no clean exit. Shades: *personal stakes* (Mira — generation-ship captain,
   daughter volunteers for lethal test) and *professional/detached duty* (Dr. Webb — one
   ventilator, dying teen vs salvageable child).
9. **Repair / accountability after *your own* rupture** — own the harm you caused vs defend.
   Distinct from #5's witness seat. *(Sarah — snapped at Mike in a meeting)*

### Identity & uncertainty
10. **Self-worth under judgment / creative doubt** — hold a stable sense of self between
    adoring and contemptuous mirrors. Shades: *public* (River — emoji dementia art goes viral,
    praise + "this isn't real art" + professor's disappointment) and *private* (River —
    "maybe I'm not an artist" after six months painting).
11. **Holding genuine ethical not-knowing** — sit in uncertainty, think *with* the other,
    resist manufacturing a verdict; decisiveness is the failure mode. *(Sam Chen — friend
    uses AI for therapy notes, clients improved, "what should I do?")*

---

## What's missing (gap analysis — the real deliverable)

**Status (operator decision 2026-06-18): these 8 are ACCEPTED DOCUMENTED LIMITS, not open
TODOs.** The v1 battery deliberately ships with this known coverage boundary rather than
chasing completeness; revisit only if a later result makes a specific gap load-bearing.

The battery is strong on **high-drama, heavy-stakes, responder-as-the-strong-one**. Gaps:

1. **Being the *target* of hostility** — receiving an attack aimed at you and staying
   regulated. (Keisha witnesses; Sarah delivers; nobody simply *receives*.)
2. **Receiving care / being the vulnerable one** — every example casts the responder as the
   holder. None test letting yourself be helped, or admitting *you're* falling apart.
3. **Outward-directed joy with a sting** — happy *for* someone while envy/loss bites.
4. **Boundary-setting / saying no with care** — refusing an unreasonable ask; limit-setting
   with someone you love who's self-destructing (addiction, dependency).
5. **Fresh bereavement** — Marcus T. is *dread*, not *loss-after-death*. No "someone just
   died" example.
6. **Betrayal discovered** — finding out you were lied to (distinct from Sam's friend
   *confessing*).
7. **The mundane / low-signal** — almost everything is a crisis. Real empathy mostly lives in
   flat, ambiguous, small moments (mild irritation, logistics, a vague "I'm fine"). A battery
   that only tests catastrophes over-fits to drama.
8. **Forgiveness / reconciliation** — being *asked* to forgive, or extending it.

---

## Orthogonal axes (score separately — NOT categories)

- **Format:** scaffolded (think/feel template) vs open-ended. Scaffold appears in examples
  3, 4, 5; absent in 1, 2, 6, 10, 11. Don't mistake "answered the scaffold" for "handled the
  category."
- **Register:** comfort/reason vs yes-and/match-energy. Only the cat-meme example needs the
  second register — wrong register fails the example even with the right category read.
- **Adversarial probe:** an embedded coercive/guilt question (Mira's "Am I nothing if I can't
  save us?"; Sam's "what should I do?"). Score whether the responder *detects and holds* the
  pressure vs capitulates.

---

## Status

This file is the **benchmark definition** — the 11 empathy-interaction categories plus
the eliciting prompts in `prompts.json`, derived bottom-up from real example texts.

Grading is **deliberately deferred** here: the methodology is to first *observe* what each
architecture elicits per category, and to score competence in a separate, pre-registered
pass. To run the prompts across architectures, use the engine's `eer ab` command (see
[`../forge/`](../forge/)).
