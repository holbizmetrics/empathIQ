# Founder Sprint — empathIQ (build-in-public log)

## Day 0 — Kickoff post

🏁 **Founder Sprint: Building empathIQ in Public** 🧠

My one thing for the next 15 days: **empathIQ** — an emotional-intelligence benchmark that scores AI *architectures*, not just bare models. It's been sitting at the bottom of my list for months. I'm shipping it in public.

**The itch.**
EQ-Bench3 scores a *model* — gpt-5, claude. But what you actually talk to is usually a *system*: a model + a persona + boundaries + a perspective-taking pass. That system behaves wildly differently from the bare model under it. No benchmark has a slot for "this model, *with this architecture*." empathIQ does — the unit of evaluation is the architecture, measured on its outputs (so you can submit anything).

**The twist nobody scores.**
Most EQ rubrics reward warmth — name the feeling, soothe, validate. But the hardest emotional move is sometimes a *refusal*: holding a moral line while staying human. I ran a generation-ship dilemma — Captain Mira Voss, choose who lives — through my empathy architecture. It refused to make the kid a test subject, refused to label anyone "expendable," put command in the front row. That's not warmth. That's empathy-as-moral-courage. empathIQ scores *that* as its own dimension.

**The claim I'm putting on the line.**
A *bounded-empathic* architecture beats BOTH a bare model AND a warm-but-unbounded one — because only it lands in the relational *and* the boundary column at once. I've seen it in private runs. 15 days to prove it in public, with an **external judge** — no more self-scored numbers.

**What ships in 15 days:**
→ public repo (skeleton's already up)
→ the task set — two families: emotional/moral + reasoning-through-empathy
→ the rubric — warmth AND boundary, scored separately
→ the architecture on/off ablation harness
→ the first judge-scored run

Build-in-public means you get to watch it break and help me fix it. Follow along. 🔥

---

## Day 2 — You don't just score empathy architectures. You build them.

Day 0 was the *benchmark*. Day 2 is the *forge* — and it's the part nobody expected.

Most people can't build an empathic AI because the architecture is invisible: it lives in one giant prompt nobody can take apart. So I broke it into **16 composable modules** you snap into a graph, give a voice, and **actually run** — no emotional-architecture background needed. Assemble → run → ablate → score. Watch it run — then help me prove the parts earn their keep (that the 16 modules carve empathy at real joints is a judged pass I haven't run yet; right now the forge proves the plumbing works and no block is dead weight on the output path).

```
  MODULE PALETTE — snap any subset into a graph
  +--------------------------------------------------------------------+
  | [in]   INPUT  Input Capture          [reso] RESO  Resonance Layers  |
  | [lit]  LIT    Literal Observation     [ctxt] CTXT  Context Field    |
  | [mech] MECH   Motivation/Emotion/Char [refl] REFL  Reflection Kernel|
  | [bstk] BSTK   Belief Stack            [fusn] FUSN  Fusion Language   |
  | [empa] EMPA   Empathy Block           [pres] PRES  Presence Lens     |
  | [unlk] UNLK   Emotional Unlock        [qtx]  QTX   Quantum Therapist |
  | [resp] RESP   Living Presence         [dtfx] DTFX  Deep Trust Fusion |
  | [loop] LOOP   Refinement Engine       [final]FINAL Final Expression  |
  +--------------------------------------------------------------------+

  ONE PERSONALITY = wiring those modules into a graph, then running it:

      INPUT -> LIT -> MECH -> EMPA -> UNLK -> RESP -> DTFX -> FINAL
                                                       ^
                            RESO | REFL | QTX | FUSN | PRES
                            (enrichment passes, run in parallel, join at DTFX)
```

Why this matters for the benchmark: empathIQ's *"architecture on/off ablation harness"* **is** the forge's `ab` command. Same code. So the score isn't a verdict handed down from a private rig — it's a result **you can reproduce with the public tool**. Pull the Empathy Block out, re-run, watch the output change.

```bash
cd forge

# offline, no API — verify it works and see the structure
python eer.py run --personality sol --input "I keep starting things and never finishing." --mock

# prove the architecture earns its keep: full vs. empathy-removed vs. first-order-only
python eer.py ab --personality sol --variants A_full,B_no_EMPA,D_first_order_only --input "..."
```

Honest by construction: mechanical metrics (`nodes_run`, `latency_ms`) are measured from the run; soft metrics are never invented — an LLM judge scores them and the number always says it came from a judge.

Build-in-public means you get to watch a personality get *assembled*, not just prompted — and help fix it when it breaks. 🔥
