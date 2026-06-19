"""Generate the architecture SVGs from the REAL graph + block registry.

Reads `forge/graphs/default.json` (edges) and `forge/eer/blocks.py` (names/clusters)
so the pictures cannot drift from what the engine actually runs. Emits two files into
`docs/` (this folder), where GitHub Pages serves them:

  architecture.svg     — the 16-block DAG, clustered and colored.
  variant-impact.svg   — the same DAG with one block dropped (EMPA), showing that
                         removing the Empathy block doesn't just delete a node: it
                         STARVES every block downstream of it (UNLK has no other
                         input) and strips the recognition signal out of RESO / REFL
                         / FUSN. This is the `B_no_EMPA` variant, drawn.

Run from the repo root:  python docs/make_diagrams.py
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # docs/ (the Pages dir)
ENGINE = os.path.join(HERE, "..", "forge")                  # the engine lives in forge/
sys.path.insert(0, ENGINE)
from eer import blocks as blockmod  # noqa: E402

DOCS = HERE  # emit the SVGs here so GitHub Pages serves them

# Curated node positions (center x, y). Hand-placed once for a clean read; the
# WIRING is read from the graph, only the coordinates are authored here.
POS = {
    "INPUT": (380, 62),
    "CTXT":  (120, 130),
    "LIT":   (380, 130),
    "BSTK":  (150, 224),
    "MECH":  (380, 224),
    "EMPA":  (380, 312),
    "REFL":  (120, 330),
    "UNLK":  (380, 400),
    "FUSN":  (620, 372),
    "QTX":   (120, 470),
    "RESP":  (380, 488),
    "RESO":  (640, 478),
    "PRES":  (610, 566),
    "LOOP":  (380, 574),
    "DTFX":  (380, 656),
    "FINAL": (380, 752),
}

# Semantic clusters -> fill color. Mirrors the block purposes in blocks.py.
CLUSTER = {
    "INPUT": "intake", "LIT": "intake",
    "MECH": "read", "BSTK": "read", "CTXT": "read",
    "EMPA": "recognize", "UNLK": "recognize",
    "REFL": "meta", "QTX": "meta",
    "RESP": "respond", "LOOP": "respond",
    "FUSN": "attune", "RESO": "attune", "PRES": "attune",
    "DTFX": "synth", "FINAL": "synth",
}
COLOR = {
    "intake":    ("#1d4ed8", "#dbeafe"),   # stroke, fill
    "read":      ("#0d9488", "#ccfbf1"),
    "recognize": ("#16a34a", "#dcfce7"),
    "meta":      ("#7c3aed", "#ede9fe"),
    "respond":   ("#1d4ed8", "#dbeafe"),
    "attune":    ("#d97706", "#fef3c7"),
    "synth":     ("#4338ca", "#e0e7ff"),
}
LEGEND = [
    ("intake", "Intake"), ("read", "Read the person"),
    ("recognize", "Recognize"), ("meta", "Meta / depth"),
    ("respond", "Respond"), ("attune", "Attune"), ("synth", "Synthesize"),
]

HW, HH = 56, 19  # node half-width / half-height
W, H = 780, 820


def _clip(cx, cy, tx, ty):
    """Point on the box border (center cx,cy) along the line toward (tx,ty)."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = HW / abs(dx) if dx else float("inf")
    sy = HH / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def _edge(a, b, dim=False, hot=False):
    ax, ay = POS[a]
    bx, by = POS[b]
    x1, y1 = _clip(ax, ay, bx, by)
    x2, y2 = _clip(bx, by, ax, ay)
    if hot:
        stroke, w, op, marker = "#dc2626", 2.2, 1.0, "arrhot"
    elif dim:
        stroke, w, op, marker = "#cbd5e1", 1.2, 0.5, "arrdim"
    else:
        stroke, w, op, marker = "#94a3b8", 1.4, 0.9, "arr"
    return (f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{w}" fill="none" opacity="{op}" marker-end="url(#{marker})"/>')


def _node(bid, dim=False, starved=False):
    cx, cy = POS[bid]
    b = blockmod.get(bid)
    stroke, fill = COLOR[CLUSTER[bid]]
    name = b.name if b else bid
    if dim:
        stroke, fill, tcol = "#cbd5e1", "#f1f5f9", "#94a3b8"
    else:
        tcol = "#0f172a"
    extra = ""
    if starved:
        stroke, extra = "#dc2626", ' stroke-dasharray="4 3"'
    out = [f'<rect x="{cx-HW}" y="{cy-HH}" rx="7" width="{HW*2}" height="{HH*2}" '
           f'fill="{fill}" stroke="{stroke}" stroke-width="2"{extra}/>']
    out.append(f'<text x="{cx}" y="{cy-3}" text-anchor="middle" font-size="12" '
               f'font-weight="700" fill="{tcol}" font-family="monospace">{bid}</text>')
    short = name if len(name) <= 18 else name[:17] + "…"
    out.append(f'<text x="{cx}" y="{cy+11}" text-anchor="middle" font-size="7.5" '
               f'fill="{tcol}" font-family="sans-serif">{short}</text>')
    if starved:
        out.append(f'<text x="{cx}" y="{cy+HH+11}" text-anchor="middle" font-size="8" '
                   f'fill="#dc2626" font-family="sans-serif" font-weight="700">starved</text>')
    return "\n".join(out)


def _defs():
    def m(mid, col):
        return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" '
                f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
    return ("<defs>" + m("arr", "#94a3b8") + m("arrdim", "#cbd5e1")
            + m("arrhot", "#dc2626") + "</defs>")


def _legend(y0):
    out = [f'<text x="20" y="{y0}" font-size="11" font-weight="700" '
           f'fill="#334155" font-family="sans-serif">Stages</text>']
    x = 90
    for key, label in LEGEND:
        stroke, fill = COLOR[key]
        out.append(f'<rect x="{x}" y="{y0-10}" width="13" height="13" rx="3" '
                   f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        out.append(f'<text x="{x+18}" y="{y0}" font-size="10" fill="#475569" '
                   f'font-family="sans-serif">{label}</text>')
        x += 26 + len(label) * 6.0
    return "\n".join(out)


def build(edges, title, subtitle, disabled=None, starved=None):
    disabled = set(disabled or [])
    starved = set(starved or [])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'font-family="sans-serif">', _defs(),
             f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
             f'<text x="20" y="24" font-size="16" font-weight="700" '
             f'fill="#0f172a">{title}</text>']
    for i, line in enumerate(subtitle):
        parts.append(f'<text x="20" y="{H-26+i*13}" font-size="10" '
                     f'fill="#64748b">{line}</text>')
    # edges first (under nodes)
    for a, b in edges:
        touches = a in disabled or b in disabled
        parts.append(_edge(a, b, dim=touches, hot=False))
    # nodes
    for bid in POS:
        parts.append(_node(bid, dim=bid in disabled, starved=bid in starved))
    parts.append(_legend(H - 40))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    with open(os.path.join(ENGINE, "graphs", "default.json"), encoding="utf-8") as f:
        graph = json.load(f)
    edges = [tuple(e) for e in graph["edges"]]
    os.makedirs(DOCS, exist_ok=True)

    arch = build(
        edges,
        "EER — the 16-block empathy architecture",
        ["Each block reads upstream results off the blackboard and writes its own; the "
         "engine runs them in",
         "topological order. Wiring read from graphs/default.json."],
    )
    with open(os.path.join(DOCS, "architecture.svg"), "w", encoding="utf-8") as f:
        f.write(arch)

    # B_no_EMPA: drop the Empathy block. UNLK reads ONLY EMPA -> starved.
    impact = build(
        edges,
        "What dropping a block does — variant B_no_EMPA",
        ["Remove EMPA and you don't lose one node: UNLK (its only input) is starved, and "
         "the recognition",
         "signal vanishes from RESO / REFL / FUSN. This is why variants are a real "
         "experiment, not cosmetic."],
        disabled={"EMPA"},
        starved={"UNLK"},
    )
    with open(os.path.join(DOCS, "variant-impact.svg"), "w", encoding="utf-8") as f:
        f.write(impact)

    print("wrote docs/architecture.svg, docs/variant-impact.svg")


if __name__ == "__main__":
    main()
