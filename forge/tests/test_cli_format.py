"""Tests for the CLI list/output formatting helpers (_gutter_lines, _entry).

Pure-function tests — no model, no audio deps — safe in CI. Cover the --full gutter
wrapping (the part that must wrap long prose WITHOUT mangling fenced ASCII diagrams)
and the shared list-entry renderer's blank-meta dropping."""
import io
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eer.cli import _gutter_lines, _entry  # noqa: E402

GUT = "            | "


def test_gutter_wraps_long_prose():
    out = list(_gutter_lines("word " * 40, max_width=40))
    assert len(out) > 1                                  # wrapped into several lines
    for line in out:
        assert line.startswith(GUT)
        assert len(line[len(GUT):]) <= 40                # no line exceeds the width


def test_gutter_keeps_words_whole():
    word = "antidisestablishmentarianism"               # 28 chars; two won't fit in 40
    bodies = [l[len(GUT):] for l in _gutter_lines((word + " ") * 5, max_width=40) if l[len(GUT):]]
    assert bodies == [word] * 5                          # never split mid-word


def test_gutter_preserves_fenced_diagram():
    wide = "X" * 80 + " a wide diagram line kept intact"
    out = list(_gutter_lines("```\n" + wide + "\n```", max_width=40))
    kept = [l for l in out if "a wide diagram line kept intact" in l]
    assert len(kept) == 1                                # ONE line, unwrapped
    assert ("X" * 80) in kept[0]                         # full width survived the fence


def test_gutter_passes_short_and_blank_verbatim():
    out = list(_gutter_lines("short\n\nalso short", max_width=40))
    assert out == [GUT + "short", GUT + "", GUT + "also short"]


def test_entry_drops_blank_and_dash_meta():
    buf = io.StringIO()
    with redirect_stdout(buf):
        _entry("Sol", "calm guide", meta=[("graph", "default"), ("layer", "-"), ("voice", "")])
    out = buf.getvalue()
    assert "Sol" in out and "calm guide" in out
    assert "graph default" in out                        # real value kept
    assert "layer" not in out                            # '-' value dropped (whole pair)
    assert "voice" not in out                            # '' value dropped (whole pair)


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1; print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
