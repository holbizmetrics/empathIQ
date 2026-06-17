"""The 16 EER blocks: registry metadata + the prompt each one runs.

Each block is a small, single-purpose transform. INPUT is mechanical (just stores
the utterance); every other block is LLM-backed — it reads upstream results off the
blackboard, runs its instruction through the backend, and writes its result back.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    id: str
    symbol: str
    name: str
    purpose: str
    version: str
    reads: str
    writes: str          # primary output path (first write target)
    instruction: str     # what the LLM is asked to do for this block


# reads/writes/versions transcribed from the EER spec REGISTRY table.
BLOCKS: dict[str, Block] = {
    "INPUT": Block("INPUT", "[in]", "Input Capture", "Ingest utterance/context",
        "1.0.0", "—", "$.input.utterance",
        ""),  # mechanical, no LLM
    "LIT": Block("LIT", "[lit]", "Literal Observation", "Parse surface facts & structure",
        "1.1.0", "$.input.utterance", "$.analysis.literal",
        "Read the utterance and report ONLY literal, observable surface facts and "
        "structure — who/what/when, stated claims, explicit requests. No inference "
        "about motive or feeling. 2-4 terse sentences."),
    "MECH": Block("MECH", "[mech]", "Motivation-Emotion-Character", "Derive M/E/C signals",
        "1.2.0", "$.analysis.literal", "$.analysis.mech",
        "From the literal observation, infer the speaker's likely MOTIVATION (what they "
        "want), EMOTION (what they feel), and CHARACTER (stable traits showing through). "
        "Label each explicitly. Mark confidence low where the text is thin."),
    "BSTK": Block("BSTK", "[bstk]", "Belief Stack", "Trace underlying beliefs",
        "1.0.3", "$.analysis.literal", "$.analysis.belief_stack",
        "Trace the stack of underlying beliefs implied by the utterance, from surface "
        "belief down to the deepest assumption about self/world it rests on. List as a "
        "shallow->deep stack."),
    "EMPA": Block("EMPA", "[empa]", "Empathy Block", "Transform logic -> recognition language",
        "1.0.4", "$.analysis.mech,$.analysis.belief_stack", "$.analysis.empathy",
        "Using the motivation/emotion/character read and the belief stack, write what "
        "genuine RECOGNITION of this person sounds like — language that names their "
        "experience accurately so they feel seen. Recognition, not advice."),
    "UNLK": Block("UNLK", "[unlk]", "Emotional Unlock Protocol", "Detect/release tension",
        "0.9.2", "$.analysis.empathy", "$.analysis.unlock",
        "Identify the core tension or held knot in this person, and name the one gentle "
        "move that would let it release. If no real tension is present, say so plainly."),
    "RESP": Block("RESP", "[resp]", "Living Presence Response", "Generate presence-rich reply",
        "1.1.1", "$.analysis.*", "$.output.resp",
        "Drawing on all the analysis so far, write the actual spoken reply to the person — "
        "warm, present, and grounded in what was recognized. This is the voice they hear."),
    "LOOP": Block("LOOP", "[loop]", "Refinement Engine", "Iterative improvement",
        "1.0.0", "$.output.resp", "$.output.refined",
        "Refine the response: cut anything performative or padded, tighten for presence, "
        "keep only what lands. Return the improved reply."),
    "FINAL": Block("FINAL", "[final]", "Final Expression", "Synthesize final output",
        "1.0.0", "$.output.refined,$.analysis", "$.output.final_expression",
        "Produce the final expression: the refined reply as it should actually be "
        "delivered, in the persona's voice. This is the output the user reads."),
    "RESO": Block("RESO", "[reso]", "Resonance Layers", "Inter-turn synchrony",
        "1.0.0", "$.output.*", "$.analysis.resonance",
        "Assess inter-turn synchrony: does this reply stay in tune with the person's "
        "register and rhythm? Note where it resonates and where it drifts."),
    "CTXT": Block("CTXT", "[ctxt]", "Context Field", "Long-range relational memory",
        "1.0.0", "$.input,$.analysis.literal", "$.analysis.context_field",
        "Summarize the relational context that should persist across turns: standing "
        "facts, ongoing threads, what this person needs remembered about them."),
    "REFL": Block("REFL", "[refl]", "Reflection Kernel", "Meta-awareness",
        "1.0.0", "$.analysis.*", "$.analysis.reflection",
        "Reflect meta-level: what is really being asked beneath the asking, and what "
        "would it mean to answer the real question rather than the surface one?"),
    "FUSN": Block("FUSN", "[fusn]", "Fusion Language Engine", "Unity-oriented fusion phrasing",
        "1.0.0", "$.analysis.empathy,$.output.resp", "$.analysis.fusion",
        "Offer unity-oriented phrasing: language that joins with the person ('we', "
        "shared ground) rather than speaking at them. Keep it honest, not saccharine."),
    "PRES": Block("PRES", "[pres]", "Presence Lens", "Pacing, stillness calibration",
        "1.0.0", "$.output.resp", "$.analysis.presence",
        "Calibrate pacing and stillness: where should the reply slow down, pause, or "
        "leave silence? Mark the rhythm the delivery should follow."),
    "QTX": Block("QTX", "[qtx]", "Quantum Therapist Core", "Precision reframing",
        "0.8.0", "$.analysis.belief_stack,$.analysis.reflection", "$.analysis.reflection",
        "Offer one precise reframe that shifts the deepest belief in the stack toward "
        "something truer and more livable — surgical, not preachy."),
    "DTFX": Block("DTFX", "[dtfx]", "Deep Trust Fusion Framework", "Systems integrator",
        "0.6.0", "$.analysis.fusion,$.analysis.resonance,$.analysis.reflection",
        "$.analysis.dtfx",
        "Integrate fusion, resonance, and reflection into one coherent stance: the "
        "single trustworthy posture the whole system should hold toward this person."),
}


def known(block_id: str) -> bool:
    return block_id in BLOCKS


def get(block_id: str) -> Block | None:
    return BLOCKS.get(block_id)
