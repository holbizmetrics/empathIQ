# The Forge — build an empathy architecture, then test it for real

Part of [**EmpathIQ**](https://github.com/holbizmetrics/empathIQ): EmpathIQ *scores*
empathy architectures. The Forge lets you *build* one.

Most empathic AI lives in one giant invisible prompt nobody can take apart. The Forge
breaks it into **16 composable blocks** you snap into a graph, give a voice, and then
**actually run** — no emotional-architecture background needed. Swap a module, re-run,
and watch the difference. That swap-and-measure loop is the same ablation harness
EmpathIQ uses to prove its core claim: *a bounded-empathic architecture beats both a
bare model and a warm-but-unbounded one.*

## Quickstart

```bash
# offline, no API — verify it works and see the structure
python eer.py run --personality sol --input "I keep starting things and never finishing." --mock

# real run (uses the `claude` CLI; no API key setup needed)
python eer.py run --personality sol --input "I keep starting things and never finishing."

# watch the architecture light up block by block as it runs
python eer.py run --personality sol --input "..." --live

# fast: direct API instead of a cold CLI launch per block — seconds, not minutes
#   pip install anthropic && export ANTHROPIC_API_KEY=...   (one-time)
python eer.py run --personality sol --input "..." --api --live

# A/B the architecture: full vs. empathy-block-removed vs. first-order-only
python eer.py ab --personality sol --variants A_full,B_no_EMPA,D_first_order_only --input "..."

# per-module ablation: drop EACH block in turn, measure how much the output changes
python ablate.py --personality sol
```

### Backends and speed

Each block is one model call. The default `claude`-CLI backend launches a fresh CLI
process per block, so a 16-block personality takes a few minutes (a cold launch each
time). The `--api` backend keeps one persistent connection and finishes in ~15–25s —
use it for anything interactive or for recording. `--mock` runs fully offline.

## See the architecture

```bash
python eer.py blocks                              # list the 16 modules
python eer.py diagram LIT,MECH,EMPA,RESP,FINAL    # ASCII diagram from any spec
```

## Build your own personality

A personality is one small JSON file: a name, a voice, which graph it runs, and
(optionally) custom instructions for any block. Scaffold one:

```bash
python eer.py new --name Ada --desc "direct, dry, names the thing nobody says" --layer 2
```

Then edit `personalities/ada.json` and run it. That is the whole "builder" — author the
file, the engine assembles and executes the architecture for you. The blocks ship with
generic, single-purpose instructions; your *voice* lives in the persona file's
`block_prompts` overrides, which stay entirely yours.

## Per-module ablation

`ablate.py` drops each block in turn (`no_<BLOCK>`) and measures how much the final
output changes versus the full pipeline — every module's contribution, individually and
reproducibly:

```bash
python ablate.py --personality sol                 # mock: structural map (instant, free)
python ablate.py --personality sol --backend claude # real text deltas (semantic)
python ablate.py --personality sol --json           # machine-readable (for a builder UI)
```

The two tiers apply here too. Under `--backend mock` the load-bearing signal is the
boolean **changed / unchanged**: does removing a block alter the output at all? (For the
default architecture, all of them do — no block is structurally dead weight.) The *effect
magnitude* under mock is text distance between deterministic markers, **not** a
contribution measure. Ranking *how much* each module matters — and finding modules that
"ablate to ~zero effect" — is a **semantic** question: run a real backend and score it in
the separate judged pass. Ablation (drop one, keep the rest) is the clean signal; a bare
single-block graph emits nothing, so isolation needs the output scaffold.

## The honest part: two metric tiers

The reason to run this for real instead of letting a model narrate it:

- **Mechanical metrics** (`nodes_run`, `latency_ms`, `final_chars`, output hashes) are
  measured from the run. Deterministic, no model in the loop.
- **Judged metrics** (`coherence`, `resonance`, `presence_ratio`, `final_quality`) are
  *not* mechanically measurable. The engine never invents them. With `--judge` it asks an
  LLM judge and labels the score `llm-judge` (noisy); without it, they stay blank for a
  human to fill in. A number you see always carries where it came from.

## The 16 blocks

| Symbol | ID | Name | Purpose |
|---|---|---|---|
| `[in]`   | INPUT | Input Capture | Ingest utterance/context |
| `[lit]`  | LIT   | Literal Observation | Parse surface facts & structure |
| `[mech]` | MECH  | Motivation-Emotion-Character | Derive M/E/C signals |
| `[bstk]` | BSTK  | Belief Stack | Trace underlying beliefs |
| `[empa]` | EMPA  | Empathy Block | Transform logic → recognition language |
| `[unlk]` | UNLK  | Emotional Unlock Protocol | Detect/release tension |
| `[resp]` | RESP  | Living Presence Response | Generate presence-rich reply |
| `[loop]` | LOOP  | Refinement Engine | Iterative improvement |
| `[final]`| FINAL | Final Expression | Synthesize final output |
| `[reso]` | RESO  | Resonance Layers | Inter-turn synchrony |
| `[ctxt]` | CTXT  | Context Field | Long-range relational memory |
| `[refl]` | REFL  | Reflection Kernel | Meta-awareness |
| `[fusn]` | FUSN  | Fusion Language Engine | Unity-oriented fusion phrasing |
| `[pres]` | PRES  | Presence Lens | Pacing, stillness calibration |
| `[qtx]`  | QTX   | Quantum Therapist Core | Precision reframing |
| `[dtfx]` | DTFX  | Deep Trust Fusion Framework | Systems integrator |

Variant names are mechanical graph edits: `A_full` (all blocks), `no_<BLOCK>` (drop one,
e.g. `B_no_EMPA`), `first_order_only` (INPUT/LIT/RESP/FINAL), `only_<A+B+C>` (isolation).

## Backends

- `claude` CLI (default) — real runs, no key setup. One cold CLI launch per block (slow).
- `--api` — direct Anthropic API via one persistent connection (fast). Needs
  `pip install anthropic` and `ANTHROPIC_API_KEY`.
- `--mock` — deterministic offline stand-in. Proves graph structure and variant logic
  with zero API calls; used by `tests/test_smoke.py`.

Add `--live` to any real run to watch the pipeline execute block by block.

## Tests

```bash
python tests/test_smoke.py    # engine: topo order, full run, determinism, variants
python tests/test_ablate.py   # ablation harness: coverage, sort, determinism
# or run both: python -m pytest tests/ -q
```
