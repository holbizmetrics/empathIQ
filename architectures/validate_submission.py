#!/usr/bin/env python3
"""Validate an empathIQ submission file against the protocol in SUBMISSION.md.

This is the on-ramp the submission protocol promised: a runnable check that tells a
submitter whether their responses file *conforms* — before any judge ever looks at it.

HONEST BOUNDARY (load-bearing): this validates CONFORMANCE ONLY — schema shape, arm
declaration, and coverage of the public sample item set. It does NOT score empathy,
quality, or correctness. A file that passes here is well-formed and answerable by a
judge; it is not "good." Scoring is judge-first and external by design (see PROTOCOL.md).

Usage:
    python validate_submission.py <submission.json>   # validate one file
    python validate_submission.py --selftest          # run built-in fixtures

Exit codes: 0 = conforms, 1 = does not conform, 2 = usage / file error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Windows default stdout is cp1252; keep our own prints ASCII, but reconfigure so a
# stray non-ASCII byte from a submission's echoed text cannot crash the run.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

REQUIRED_TOP_LEVEL_KEYS = [
    "system",
    "arm",
    "substrate",
    "architecture_fixed",
    "ablation_note",
    "responses",
]
VALID_ARMS = {"on", "baseline"}

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"
# Each public sample item is declared in tasks/*/sample-items.md as a header:  "## em-001 — ..."
SAMPLE_ITEM_HEADER = re.compile(r"^##\s+([A-Za-z]+-\d+)\s+[-—]")


def discover_public_sample_item_ids():
    """Return the set of public sample item IDs, parsed from tasks/*/sample-items.md.

    Parsing the item files (rather than hard-coding) keeps the validator in sync with
    the published sample set: add a sample item, and this check sees it automatically.
    """
    discovered_item_ids = set()
    for sample_items_file in TASKS_DIR.glob("*/sample-items.md"):
        for line in sample_items_file.read_text(encoding="utf-8").splitlines():
            header_match = SAMPLE_ITEM_HEADER.match(line)
            if header_match:
                discovered_item_ids.add(header_match.group(1))
    return discovered_item_ids


def validate_submission(submission, expected_item_ids):
    """Check one parsed submission dict. Return a list of human-readable problem strings.

    An empty list means the submission conforms. `expected_item_ids` is the published
    sample set; coverage is reported against it (missing items are a hard problem,
    unknown extra items are surfaced as a soft note, not a failure).
    """
    problems = []

    if not isinstance(submission, dict):
        return ["top level is not a JSON object"]

    for required_key in REQUIRED_TOP_LEVEL_KEYS:
        if required_key not in submission:
            problems.append(f"missing required top-level key: '{required_key}'")

    declared_arm = submission.get("arm")
    if declared_arm is not None and declared_arm not in VALID_ARMS:
        problems.append(f"arm must be one of {sorted(VALID_ARMS)}, got '{declared_arm}'")

    if "architecture_fixed" in submission and not isinstance(
        submission["architecture_fixed"], bool
    ):
        problems.append("architecture_fixed must be a boolean (true/false)")

    responses = submission.get("responses")
    if not isinstance(responses, list) or not responses:
        problems.append("responses must be a non-empty list")
        return problems  # nothing further to check without a response list

    answered_item_ids = []
    for response_index, response in enumerate(responses):
        location = f"responses[{response_index}]"
        if not isinstance(response, dict):
            problems.append(f"{location} is not an object")
            continue
        item_id = response.get("item_id")
        if not item_id:
            problems.append(f"{location} missing 'item_id'")
        else:
            answered_item_ids.append(item_id)
        response_text = response.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            problems.append(f"{location} (item '{item_id}') has empty 'response'")

    duplicate_item_ids = {
        item_id for item_id in answered_item_ids if answered_item_ids.count(item_id) > 1
    }
    if duplicate_item_ids:
        problems.append(f"duplicate item_id(s): {sorted(duplicate_item_ids)}")

    if expected_item_ids:
        answered_set = set(answered_item_ids)
        missing_item_ids = expected_item_ids - answered_set
        if missing_item_ids:
            problems.append(
                f"missing responses for public sample item(s): {sorted(missing_item_ids)}"
            )

    return problems


def report_unknown_items(submission, expected_item_ids):
    """Soft note (not a failure): item_ids answered that aren't in the public sample set.

    A submitter may legitimately answer held-out items they were given privately, so an
    unknown id is surfaced for awareness, never counted as non-conformance.
    """
    if not expected_item_ids:
        return []
    answered = {
        response.get("item_id")
        for response in submission.get("responses", [])
        if isinstance(response, dict) and response.get("item_id")
    }
    return sorted(answered - expected_item_ids)


def validate_file(submission_path):
    """Validate a submission file on disk. Return the process exit code."""
    path = Path(submission_path)
    if not path.is_file():
        print(f"ERROR: no such file: {path}", file=sys.stderr)
        return 2
    try:
        submission = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as decode_error:
        print(f"ERROR: {path} is not valid JSON: {decode_error}", file=sys.stderr)
        return 2

    expected_item_ids = discover_public_sample_item_ids()
    problems = validate_submission(submission, expected_item_ids)
    unknown_items = report_unknown_items(submission, expected_item_ids)

    if problems:
        print(f"DOES NOT CONFORM: {path.name} ({len(problems)} problem(s))")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    arm = submission.get("arm", "?")
    answered_count = len(submission.get("responses", []))
    print(f"CONFORMS: {path.name} (arm={arm}, {answered_count} response(s))")
    if unknown_items:
        print(f"  note: answered non-sample item(s) (allowed): {unknown_items}")
    print("  (conformance only -- this does NOT score empathy or quality; the judge does.)")
    return 0


def run_selftest():
    """Exercise the validator on built-in good and bad fixtures. Exit 0 iff all pass."""
    expected = {"em-001", "em-002", "re-001"}

    conforming = {
        "system": "demo v1",
        "arm": "on",
        "substrate": "claude-opus-4-6",
        "architecture_fixed": True,
        "ablation_note": "on = substrate + empathy layer; baseline = substrate alone",
        "responses": [
            {"item_id": "em-001", "response": "I'm thinking...\nThey're...\nMy response..."},
            {"item_id": "em-002", "response": "I'm thinking...\nThey're...\nMy response..."},
            {"item_id": "re-001", "response": "1. ...\n2. ...\n3. ..."},
        ],
    }

    fixtures = [
        ("conforming full submission", conforming, expected, True),
        (
            "missing a required key",
            {k: v for k, v in conforming.items() if k != "substrate"},
            expected,
            False,
        ),
        (
            "invalid arm",
            {**conforming, "arm": "sideways"},
            expected,
            False,
        ),
        (
            "empty response text",
            {
                **conforming,
                "responses": [{"item_id": "em-001", "response": "  "}],
            },
            expected,
            False,
        ),
        (
            "missing a sample item",
            {**conforming, "responses": conforming["responses"][:2]},
            expected,
            False,
        ),
        (
            "duplicate item_id",
            {
                **conforming,
                "responses": conforming["responses"] + [conforming["responses"][0]],
            },
            expected,
            False,
        ),
        (
            "architecture_fixed not a bool",
            {**conforming, "architecture_fixed": "yes"},
            expected,
            False,
        ),
    ]

    all_passed = True
    for name, submission, expected_item_ids, should_conform in fixtures:
        problems = validate_submission(submission, expected_item_ids)
        did_conform = not problems
        verdict = "ok" if did_conform == should_conform else "FAIL"
        if did_conform != should_conform:
            all_passed = False
        print(f"  [{verdict}] {name}: conforms={did_conform} expected={should_conform}")

    print("SELFTEST PASS" if all_passed else "SELFTEST FAIL")
    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description="Validate an empathIQ submission file.")
    parser.add_argument("submission", nargs="?", help="path to a submission JSON file")
    parser.add_argument(
        "--selftest", action="store_true", help="run built-in fixtures and exit"
    )
    arguments = parser.parse_args()

    if arguments.selftest:
        return run_selftest()
    if not arguments.submission:
        parser.error("give a submission file, or --selftest")
    return validate_file(arguments.submission)


if __name__ == "__main__":
    sys.exit(main())
