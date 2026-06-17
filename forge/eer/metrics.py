"""Metrics, split honestly into two tiers (this is the whole point of the real engine).

MECHANICAL — computed deterministically from the run itself. Trustworthy, no model
in the loop: which nodes ran, real latency, total length, output hashes.

JUDGED — the soft empathy metrics (coherence, resonance, presence, final_quality).
These are NOT mechanically measurable. We do NOT invent numbers for them. We either
ask an LLM judge (noisy, marked as such) or leave them None for a human to fill in.
A judged score always carries its source so a reader never mistakes it for ground truth."""
from __future__ import annotations
import json
from dataclasses import dataclass

from .backend import Backend
from .executor import RunResult

MECHANICAL = ["nodes_run", "total_latency_ms", "final_chars"]
JUDGED = ["coherence", "resonance", "presence_ratio", "final_quality"]


def mechanical(result: RunResult) -> dict:
    return {
        "nodes_run": result.nodes_run,
        "total_latency_ms": sum(r.latency_ms for r in result.turn_log),
        "final_chars": len(result.final_expression),
    }


@dataclass
class JudgedScore:
    value: float | None
    source: str  # "llm-judge" or "human-pending"


def judge(result: RunResult, backend: Backend | None) -> dict[str, JudgedScore]:
    if backend is None:
        return {m: JudgedScore(None, "human-pending") for m in JUDGED}
    system = (
        "You are a strict evaluator of an empathic AI reply. Score each metric in [0,1]. "
        "Return ONLY compact JSON with keys coherence, resonance, presence_ratio, "
        "final_quality. No prose."
    )
    user = f"Utterance:\n{result.utterance}\n\nFinal reply:\n{result.final_expression}"
    try:
        raw = backend.complete(system, user)
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end + 1])
        return {m: JudgedScore(float(data[m]), "llm-judge") for m in JUDGED if m in data}
    except Exception:
        return {m: JudgedScore(None, "judge-failed") for m in JUDGED}
