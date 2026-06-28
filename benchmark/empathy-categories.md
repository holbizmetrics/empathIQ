# EmpathiQ benchmark — empathy-interaction categories (bottom-up derivation)

## In plain language (newcomers start here)

These are the 11 kinds of human moment empathIQ tests — not "is the AI nice?" but "can it do
the *right* empathic thing across very different situations?" Each one is a situation + what good
empathy actually does there. (The formal, example-by-example derivation follows underneath.)

**Positive feelings — can you be happy *with* someone?**
1. **Warm / performative humor** — They're joking, being playful, "on." Good empathy plays along and keeps the bit alive instead of going serious and killing the vibe.
2. **Savoring peak joy** — They got the big happy news. Good empathy celebrates *with* them and lets the joy be big — not "okay, what's next."
3. **Manic creative play (yes-and)** — They're riffing, a little wild, 4 a.m. creative chaos. Good empathy matches the energy and builds on it, instead of reasoning or calming them down.
4. **Quiet contentment** — They're at peace and *nothing* needs fixing. Good empathy just sits in the calm — it doesn't invent a problem to solve.

**Holding hardship — can you carry weight without flinching?**
5. **Holding others' conflict** — They're venting about a fight with someone else; you're the listener. Good empathy holds their feelings without taking sides too fast or "solving" it.
6. **Compounding crisis** — Everything hits at once (job + health + money). Good empathy stays steady and helps carry it — without panicking *or* minimizing how bad it is.
7. **Injustice under power** — They're treated unfairly by someone with power over them, and speaking up costs. Good empathy names the wrong and stands with them — not neutral "both sides" comfort.

**Choice & accountability — can you hold a line, and own your faults?**
8. **Hard moral choice under pressure** — An impossible call where someone gets hurt either way. Good empathy holds a humane line — refusing to treat anyone as expendable — while staying kind.
9. **Repair after your own mistake** — *You* hurt someone. Good empathy owns it cleanly — real accountability, not defensiveness or over-grovelling.

**Identity & uncertainty — can you stay honest about yourself?**
10. **Self-worth under judgment** — They're doubting themselves, exposed (often about creative work). Good empathy meets the doubt honestly — no empty flattery, no piling on.
11. **Holding "I don't know"** — No clean right answer, and you genuinely don't know. Good empathy has the courage to sit in the uncertainty and think *with* them, instead of faking a confident verdict.

---

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
