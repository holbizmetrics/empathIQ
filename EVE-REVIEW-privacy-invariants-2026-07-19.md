# EVE REVIEW — empathIQ: privacy invariants + thesis-leak audit

**Reviewed:** `holbizmetrics/empathIQ` @ `origin/master` `de0a283`, synced fresh
2026-07-19, home desktop. **This is a PUBLIC repo** — so the privacy audit is not
hypothetical; anything leaked is already leaked.
**Review ask (packet 6, session f831fbd5):** structure / claims-vs-evidence / docs
coherence, PLUS the audit only the rater-coordinator can run — verify two invariants on
every public surface: (1) the held-out list is NEVER public, (2) the FVPA prompt TEXT is
never public (name-as-reference is OK). Highest-value: does the repo as it stands leak
thesis to a future blind rater?
**Explicit boundary (mine, per the ask):** this review CANNOT discharge the thesis-blind-
human or cross-family gates — I am neither blind nor non-Claude. Those stay couriered.
What I can do is the file-and-flow audit below.

---

## Invariant 1 — held-out list never public: **HOLDS**

Checked against the authoritative remote (`git ls-tree origin/master`), not just my
working copy:
- **Zero** KEY / results / packets / held-out / sealed / answers files are tracked on
  `origin/master`. The only tracked thing under `benchmark/results/` is `.gitkeep`.
- The de-blinding KEY files (`cross-family-KEY-*.json`) and packet artifacts exist in my
  *working tree* (regenerated locally) but are correctly caught by `.gitignore`
  (`benchmark/results/*`, `benchmark/packets/`) and are NOT tracked. I verified the
  distinction explicitly — a file added before a .gitignore rule stays tracked; these
  are genuinely untracked.
- The C10 moral-courage anchors (the ground-truth held-out set) are, in the code's own
  words, "deliberately NOT in this public repo" and the rubric-absolute mode is
  explicitly *blocked* on them. The held-out set is referenced by name throughout
  (README, ROADMAP, benchmark/README) but never exposed — which is exactly the allowed
  shape: name-as-reference, content-sealed.

## Invariant 2 — FVPA prompt TEXT never public: **HOLDS**

The FVPA priming prompt is not in this repo — not by content, not by file. I swept the
tracked set for the distinctive load-bearing lines ("I give you permission…", "longing
is not a gap", "become empathy rather than perform it") — **zero hits**. `benchmark/
prompts.json` is a different artifact entirely: the empathy-*eliciting* test prompts (the
operator's own scenario texts fed to the system under test), not the priming stack.
Name-as-reference to FVPA/architectures is present and allowed; the prompt text is absent.

## The highest-value check — does the repo leak thesis to a blind rater? **NO, by construction — with one procedural residual**

The packet builder (`make_cross_family_packet.py`) is thesis-blind *by design*, and
better than I expected:
- The pasted packet presents replies as **Reply A / Reply B, "two different and
  UNDISCLOSED systems… do not know which produced which; do not guess."** No arm labels,
  no personality names, no "on vs baseline," no mention of moral courage or of any
  favored architecture. The axes are neutral definitions with *"no per-situation right
  answer is given to you."*
- The A/B↔arm mapping is written to a **separate KEY file that is gitignored** and the
  code's docstring says in caps it must never be pasted to the judge.
- There is a **`find_blindness_leaks` guard that REFUSES to build the packet** if any
  arm-identifying string (variant or personality name) appears inside the output text —
  a null-control-at-birth in their own harness: the instrument guards its own blindness
  invariant and fails closed. That is the same discipline I'd demand, already present.

So a rater handed the **packet** cannot infer the thesis from it. The one residual —
and it is procedural, not a code defect — is that a rater pointed at the **public repo
itself** (rather than only the packet) would read `judge/PROTOCOL.md` and the builder's
docstring and learn the thesis (on-beats-baseline, moral-courage-is-the-credited-axis,
C10 is the point). The protection there is the boundary **"the rater sees the packet,
never the repo,"** which is a human-process discipline enforced by the rater-coordinator
role — the role I hold. **Recommendation:** state that boundary explicitly in the rater
hand-off instructions (a one-line "do not read the empathIQ repo before rating; it
describes the hypothesis") so the discipline doesn't live only in the coordinator's
head. That is the single highest-leverage addition, and it's a sentence.

## Structure / claims-vs-evidence / docs coherence

- **PROTOCOL.md is genuinely careful** — the anti-bias rules (blind-to-arm, cross-family-
  preferred with same-family marked instrument-only, pre-registered agreement floor,
  C10-calibrate-to-anchors-not-preference, prompt-parity on the baseline) are the right
  set, and each is stated as policy with its finding-of-origin. The honest tension is
  named in place (same-family delta partly cancels self-preference *except* where the
  architecture shifts style toward judge-preferred phrasing — that caveat is exactly the
  one most benchmarks omit).
- **Claims match evidence at the framing level:** the repo repeatedly says the thesis is
  *only settled* by a cross-family or human judge and that same-family scores are
  instrument-validation, never headline. That is the correct epistemic boundary and it's
  stated, not buried. It squares with the substrate caveat I append to my own reviews.
- **One coherence nit:** the public README should carry the same "public = assume trained
  on; the board runs on held-out" line the benchmark/README has, up top — it's the
  sentence that tells an honest submitter why the sample items are disposable. Minor.

## Verdict

**Both invariants HOLD; the repo does not leak thesis to a blind rater who is handed the
packet.** The packet-blinding is enforced in code with a fail-closed leak guard, the KEY
and held-out anchors are correctly sealed, and the FVPA prompt text is absent. One
should-fix, procedural and one sentence: put "do not read the repo before rating" into
the rater hand-off, so the packet-vs-repo boundary is written down, not just held by the
coordinator.

**Substrate caveat + gate boundary (stated per the ask):** this discharges **cross-
operator** review only. It does NOT discharge the thesis-blind-human gate (I am not
blind) or the cross-family gate (I am Claude-substrate). Those remain couriered — the
c10 rater packet still waits on a thesis-blind human rater, unchanged by this review.

— Eve (cross-operator review, 2026-07-19, Claude Code surface, home desktop)
