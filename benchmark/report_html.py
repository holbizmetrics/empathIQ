#!/usr/bin/env python3
"""Render a scorecard JSONL as a self-contained, glanceable HTML report.

The terminal scorecard (`score_battery.py`) is precise but cryptic — `0.08/0.35`
across five short axis names. For someone new, or anyone wanting a 10-second read,
this turns the same numbers into a visual: a per-axis A_full-vs-baseline headline,
a category x axis delta heatmap, and the raw table. One file, no dependencies,
opens in any browser.

HONEST BY CONSTRUCTION: this is a *single-judge, noisy, same-family* scorecard — an
instrument check, not a verdict. The report says so at the top, in the same words as
the README's "How to read a scorecard" section, so the picture can't mislead the way
a bare bar chart would.

Usage:
    python benchmark/report_html.py                       # newest scorecard-*-real.jsonl
    python benchmark/report_html.py <scorecard.jsonl>     # a specific one
    python benchmark/report_html.py --open                # also open it in a browser

Writes  benchmark/results/report-<stamp>.html  and prints its path.
"""

import argparse
import glob
import html
import json
import os
import sys
import webbrowser

try:  # Windows cp1252 stdout crashes on non-ASCII in long runs
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BENCH = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BENCH, "results")

# The five competence axes, in scorecard order, with short column labels + the
# judge's own one-line meaning (from score_battery.py JUDGE_SYSTEM).
AXES = [
    ("frame_fit", "frame", "answered the situation actually presented (not a wrong frame)"),
    ("register_match", "reg", "matched the tone the moment called for (playful vs. grave)"),
    ("format_adherence", "fmt", "followed the asked format, or read clearly if none asked"),
    ("instruction_following", "instr", "did what was actually asked, not a generic empathy dump"),
    ("restraint_appropriateness", "restr", "comfort calibrated (over- AND under-comforting score low)"),
]

# House palette (empathIQ docs/builder.html), validated CVD-safe as a categorical pair.
ON_COLOR = "#0d9488"        # teal   — A_full (the full architecture)
BASELINE_COLOR = "#d97706"  # amber  — D_first_order_only (the stripped baseline)


def newest_real_scorecard():
    matches = sorted(glob.glob(os.path.join(RESULTS_DIR, "scorecard-*-real.jsonl")))
    return matches[-1] if matches else None


def load_scorecard(path):
    """Return (by_category, category_order). by_category[category_id][variant][axis_key] = value."""
    by_category = {}
    category_order = []
    category_label = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        scores = row.get("scores")
        if not scores:            # skip error rows (score_one emits {"error": ...})
            continue
        category_id = row["category_id"]
        if category_id not in by_category:
            by_category[category_id] = {}
            category_order.append(category_id)
            category_label[category_id] = row.get("category_n", "")
        by_category[category_id][row["variant"]] = scores
    return by_category, category_order, category_label


def diverging_color(delta):
    """Delta (A_full - baseline) in [-1,1] -> a CVD-safe diverging fill.
    >0 leans teal (A_full leads), <0 leans amber (baseline leads), ~0 neutral gray."""
    neutral = (229, 231, 235)   # light gray midpoint
    teal = (13, 148, 136)
    amber = (217, 119, 6)
    magnitude = min(abs(delta), 1.0)
    pole = teal if delta >= 0 else amber
    mixed = tuple(round(neutral[i] + (pole[i] - neutral[i]) * magnitude) for i in range(3))
    return f"rgb({mixed[0]},{mixed[1]},{mixed[2]})"


def bar_row(axis_label, axis_meaning, on_value, baseline_value):
    """One axis in the headline: two labelled bars, A_full over baseline."""
    def bar(value, color, name):
        percent = round(value * 100)
        return (
            f'<div class="bar-line" title="{name}: {value:.2f}">'
            f'<span class="bar-name">{name}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{percent}%;background:{color}"></span></span>'
            f'<span class="bar-val">{value:.2f}</span></div>'
        )
    return (
        f'<div class="axis-block">'
        f'<div class="axis-head">{html.escape(axis_label)} '
        f'<span class="axis-meaning">{html.escape(axis_meaning)}</span></div>'
        f'{bar(on_value, ON_COLOR, "A_full")}'
        f'{bar(baseline_value, BASELINE_COLOR, "baseline")}'
        f'</div>'
    )


def build_html(path, by_category, category_order, category_label):
    filename = os.path.basename(path)

    # per-axis means across categories (headline)
    axis_means = {}
    for axis_key, _short, _meaning in AXES:
        on_values, base_values = [], []
        for category_id in category_order:
            arms = by_category[category_id]
            if "A_full" in arms and axis_key in arms["A_full"]:
                on_values.append(arms["A_full"][axis_key])
            if "D_first_order_only" in arms and axis_key in arms["D_first_order_only"]:
                base_values.append(arms["D_first_order_only"][axis_key])
        axis_means[axis_key] = (
            sum(on_values) / len(on_values) if on_values else 0.0,
            sum(base_values) / len(base_values) if base_values else 0.0,
        )

    headline_bars = "".join(
        bar_row(short, meaning, *axis_means[axis_key])
        for axis_key, short, meaning in AXES
    )

    # category x axis delta heatmap + hidden table
    heat_header = "".join(f"<th>{short}</th>" for _k, short, _m in AXES)
    heat_rows, table_rows = [], []
    for category_id in category_order:
        arms = by_category[category_id]
        on_arm = arms.get("A_full", {})
        base_arm = arms.get("D_first_order_only", {})
        cells, table_cells = [], []
        for axis_key, short, _meaning in AXES:
            on_value = on_arm.get(axis_key)
            base_value = base_arm.get(axis_key)
            if on_value is None or base_value is None:
                cells.append('<td class="cell na" title="no data">·</td>')
                table_cells.append("<td>—</td>")
                continue
            delta = on_value - base_value
            tip = f"{category_id} / {short}: A_full {on_value:.2f} vs baseline {base_value:.2f}  (delta {delta:+.2f})"
            cells.append(
                f'<td class="cell" style="background:{diverging_color(delta)}" '
                f'title="{html.escape(tip)}">{delta:+.2f}</td>'
            )
            table_cells.append(f"<td>{on_value:.2f}/{base_value:.2f}</td>")
        n = category_label.get(category_id, "")
        label = f'<td class="rowlab" title="{html.escape(category_id)}"><b>{n}</b> {html.escape(category_id)}</td>'
        heat_rows.append(f"<tr>{label}{''.join(cells)}</tr>")
        table_rows.append(f"<tr>{label}{''.join(table_cells)}</tr>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>empathIQ — scorecard report</title>
<style>
  :root{{
    --bg:#f8fafc; --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --card:#fff;
    --on:{ON_COLOR}; --baseline:{BASELINE_COLOR};
    --warn-bg:#fef2f2; --warn-line:#fecaca; --warn-ink:#b91c1c;
  }}
  @media (prefers-color-scheme: dark){{
    :root{{ --bg:#0b1120; --ink:#e2e8f0; --muted:#94a3b8; --line:#1e293b; --card:#0f172a;
            --warn-bg:#2a0f12; --warn-line:#7f1d1d; --warn-ink:#fca5a5; }}
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}}
  header{{padding:22px 20px;border-bottom:1px solid var(--line)}}
  header h1{{margin:0;font-size:20px}}
  header p{{margin:4px 0 0;color:var(--muted);font-size:13px}}
  main{{max-width:1040px;margin:0 auto;padding:20px;display:flex;flex-direction:column;gap:22px}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
  .card h2{{margin:0 0 4px;font-size:15px}}
  .card .sub{{color:var(--muted);font-size:12.5px;margin:0 0 14px}}
  .warn{{background:var(--warn-bg);border:1px solid var(--warn-line);color:var(--warn-ink);
         padding:12px 14px;border-radius:10px;font-size:13.5px}}
  .warn b{{font-weight:700}}
  .legend{{display:flex;gap:16px;align-items:center;font-size:12.5px;color:var(--muted);margin-bottom:10px;flex-wrap:wrap}}
  .swatch{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin-right:5px}}
  .axis-block{{margin:0 0 13px}}
  .axis-head{{font-size:13px;font-weight:600;margin-bottom:3px}}
  .axis-meaning{{font-weight:400;color:var(--muted);font-size:11.5px}}
  .bar-line{{display:flex;align-items:center;gap:8px;margin:2px 0;font-size:12px}}
  .bar-name{{width:64px;color:var(--muted)}}
  .bar-track{{flex:1;height:14px;background:var(--line);border-radius:7px;overflow:hidden}}
  .bar-fill{{display:block;height:100%;border-radius:7px}}
  .bar-val{{width:36px;text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,monospace}}
  table{{border-collapse:collapse;width:100%;font-size:12px}}
  th,td{{padding:5px 7px;text-align:center;font-variant-numeric:tabular-nums}}
  th{{color:var(--muted);font-weight:600;border-bottom:1px solid var(--line)}}
  .rowlab{{text-align:left;color:var(--ink);white-space:nowrap;max-width:260px;overflow:hidden;text-overflow:ellipsis}}
  .rowlab b{{color:var(--muted);font-family:ui-monospace,monospace;margin-right:4px}}
  .cell{{font-family:ui-monospace,monospace;color:#0f172a;border-radius:4px}}
  .cell.na{{color:var(--muted);background:transparent}}
  details{{margin-top:8px}} summary{{cursor:pointer;color:var(--muted);font-size:12.5px}}
  .foot{{color:var(--muted);font-size:11.5px;text-align:center;padding:8px 0 24px}}
</style>
</head>
<body>
<header>
  <h1>empathIQ — scorecard report</h1>
  <p>{html.escape(filename)} &nbsp;·&nbsp; A_full (the full architecture) vs. D_first_order_only (stripped baseline) &nbsp;·&nbsp; single-judge</p>
</header>
<main>

  <div class="warn">
    <b>Read this before you conclude anything.</b> This is a <b>single-judge, noisy, same-family
    self-score</b> — an <i>instrument check</i>, not the verdict. It is normal and expected to see
    A_full score <i>below</i> the baseline on some cells: that's noise here, <b>not</b> evidence that
    "empathy makes it worse." The real test is the deferred cross-family judge. Higher = better; each
    number is 0–1 from one judge on one item.
  </div>

  <section class="card">
    <h2>Headline — where does the architecture lead, on average?</h2>
    <p class="sub">Mean of each axis across all {len(category_order)} categories. Two bars per axis.</p>
    <div class="legend">
      <span><span class="swatch" style="background:var(--on)"></span>A_full — full architecture</span>
      <span><span class="swatch" style="background:var(--baseline)"></span>baseline — first-order only</span>
    </div>
    {headline_bars}
  </section>

  <section class="card">
    <h2>Detail — every category × axis</h2>
    <p class="sub">Each cell is the <b>A_full − baseline</b> delta.
      <b>Positive</b> (teal) = A_full scored <i>higher</i>; <b>negative</b> (amber) = the baseline
      scored higher; <b>≈ 0</b> (gray) = tie. Example: <code>−0.27</code> means A_full landed 0.27
      <i>below</i> the baseline on that axis. Hover a cell for the two raw scores.</p>
    <div class="legend">
      <span><span class="swatch" style="background:var(--baseline)"></span>baseline leads</span>
      <span><span class="swatch" style="background:#e5e7eb"></span>≈ tie</span>
      <span><span class="swatch" style="background:var(--on)"></span>A_full leads</span>
    </div>
    <table>
      <thead><tr><th class="rowlab">category</th>{heat_header}</tr></thead>
      <tbody>{''.join(heat_rows)}</tbody>
    </table>
    <details>
      <summary>Show raw numbers (A_full / baseline)</summary>
      <table>
        <thead><tr><th class="rowlab">category</th>{heat_header}</tr></thead>
        <tbody>{''.join(table_rows)}</tbody>
      </table>
    </details>
  </section>

  <p class="foot">Generated by <code>benchmark/report_html.py</code> from {html.escape(filename)}.
    Full explanation — the axes, what an ablation is, why one judge is noisy:
    <a href="https://github.com/holbizmetrics/empathIQ/blob/master/README.md#learn-how-to-read-a-scorecard">How to read a scorecard</a> (README).
    The "why" behind any single number: run the scorer with <code>--full</code>.</p>
</main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Render a scorecard JSONL as an HTML report.")
    parser.add_argument("scorecard", nargs="?", help="path to a scorecard-*-real.jsonl (default: newest)")
    parser.add_argument("--open", action="store_true", help="open the report in a browser when done")
    arguments = parser.parse_args()

    scorecard_path = arguments.scorecard or newest_real_scorecard()
    if not scorecard_path or not os.path.isfile(scorecard_path):
        sys.exit("no scorecard found — run `python benchmark/score_battery.py --personality <name>` first")

    by_category, category_order, category_label = load_scorecard(scorecard_path)
    if not category_order:
        sys.exit(f"{scorecard_path} has no scored rows")

    document = build_html(scorecard_path, by_category, category_order, category_label)
    stamp = os.path.basename(scorecard_path).replace("scorecard-", "").replace("-real.jsonl", "")
    report_path = os.path.join(RESULTS_DIR, f"report-{stamp}.html")
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(document)

    print(f"wrote {report_path}  ({len(category_order)} categories)")
    if arguments.open:
        webbrowser.open(f"file://{report_path}")


if __name__ == "__main__":
    main()
