"""Run a graph for real: topological order, each node reads upstream state off the
blackboard, runs its block instruction through the backend, writes its result back.

Returns a RunResult with the final expression, the full blackboard, and a per-node
turn log carrying ONLY mechanical metrics (real latency, real output hash, ran/skipped).
Soft metrics (coherence/resonance/...) are NOT invented here — see metrics.py."""
from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass, field

from . import blocks as blockmod
from .backend import Backend
from .blackboard import Blackboard
from .graph import Graph


@dataclass
class TurnRow:
    node: str
    ran: bool
    latency_ms: int
    output_hash: str
    note: str = ""


@dataclass
class RunResult:
    variant: str
    utterance: str
    final_expression: str
    blackboard: dict
    turn_log: list[TurnRow] = field(default_factory=list)

    @property
    def nodes_run(self) -> int:
        return sum(1 for r in self.turn_log if r.ran)


def _build_prompt(block: blockmod.Block, bb: Blackboard, persona: dict | None,
                  prompt_override: str | None) -> tuple[str, str]:
    reads = bb.resolve_reads(block.reads)
    context = "\n".join(f"{k}:\n{v}" for k, v in reads.items() if v) or "(no upstream context)"
    instruction = prompt_override or block.instruction
    system = f"You are the {block.name} block of an empathy-processing pipeline. {instruction}"
    if persona:
        pname = persona.get("name", "the persona")
        pdesc = persona.get("description", "")
        layer = persona.get("persona_layer")
        system += f"\nSpeak as the persona '{pname}'. {pdesc}"
        if layer:
            system += f" Association depth: layer {layer}."
    user = f"Upstream context:\n{context}\n\nProduce your block's output only."
    return system, user


def run_graph(graph: Graph, utterance: str, backend: Backend,
              persona: dict | None = None,
              prompt_overrides: dict[str, str] | None = None,
              variant_name: str = "A_full") -> RunResult:
    bb = Blackboard()
    bb.set("$.input.utterance", utterance)
    prompt_overrides = prompt_overrides or {}
    log: list[TurnRow] = []

    for node in graph.topo_order():
        block = blockmod.get(node)
        if block is None:
            log.append(TurnRow(node, False, 0, "", "unknown block, skipped"))
            continue
        if node == "INPUT":
            log.append(TurnRow(node, True, 0, _hash(utterance), "input captured"))
            continue
        system, user = _build_prompt(block, bb, persona, prompt_overrides.get(node))
        t0 = time.monotonic()
        out = backend.complete(system, user)
        dt = int((time.monotonic() - t0) * 1000)
        bb.set(block.writes, out)
        log.append(TurnRow(node, True, dt, _hash(out)))

    final = bb.get("$.output.final_expression") or bb.get("$.output.refined") \
        or bb.get("$.output.resp") or "(no output produced)"
    return RunResult(variant_name, utterance, final, bb.snapshot(), log)


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:8]
