#!/usr/bin/env python3
"""Lightweight checker for COPILOT_INSTRUCTIONS.md rules.

This script is intentionally conservative. It is intended to run in CI on pull requests
to surface likely violations: large files (>300 LOC), changed source files without tests,
and obvious non-deterministic test code patterns.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Set

ROOT = Path(__file__).resolve().parents[1]


def count_loc(path: Path) -> int:
    """Count non-blank, non-comment lines to approximate LOC."""
    count = 0
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        count += 1
    return count


def find_python_files(root: Path) -> List[Path]:
    return [
        p
        for p in root.rglob("*.py")
        if ".venv" not in p.parts and p.name != os.path.basename(__file__)
    ]


def changed_files_from_env() -> List[str]:
    # In CI we expect a space-separated list in environment variable CHANGED_FILES (best-effort)
    env = os.environ.get("CHANGED_FILES")
    if not env:
        return []
    return env.split()


def detect_nondeterministic_tests(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    suspects = []
    patterns = [
        r"\brandom\.",
        r"\bsecrets\.",
        r"\btime\.sleep\(",
        r"datetime\.now\(",
        r"utcnow\(",
        r"requests\.",
        r"urllib\.request",
    ]
    for pat in patterns:
        if re.search(pat, text):
            suspects.append(pat)
    return suspects


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-loc", type=int, default=300, help="Maximum allowed LOC per file")
    args = parser.parse_args(argv)

    failures = 0
    large_files: List[Path] = []
    missing_tests: Set[Path] = set()
    nondet_tests: List[Path] = []

    py_files = [p for p in find_python_files(ROOT / "src")]

    # Check file sizes
    for p in py_files:
        loc = count_loc(p)
        if loc > args.max_loc:
            large_files.append(p)

    # Simple heuristic: for changed source files, require at least one test file that imports the module or references its name
    changed = changed_files_from_env()
    changed_src = [Path(c) for c in changed if c.startswith("src/") and c.endswith(".py")]
    test_files = [p for p in find_python_files(ROOT / "tests")]
    for src in changed_src:
        mod_name = src.stem
        found = False
        for t in test_files:
            txt = t.read_text(encoding="utf-8")
            if mod_name in txt:
                found = True
                break
        if not found:
            missing_tests.add(src)

    # Check tests for nondeterministic patterns
    for t in test_files:
        suspects = detect_nondeterministic_tests(t)
        if suspects:
            nondet_tests.append(t)

    if large_files:
        print(
            "ERROR: The following source files exceed the allowed LOC (>{}):".format(args.max_loc)
        )
        for p in large_files:
            print(f"  - {p} ({count_loc(p)} LOC)")
        failures += 1

    if missing_tests:
        print(
            "ERROR: The following changed source files appear to have no corresponding tests in `tests/`:"
        )
        for p in missing_tests:
            print(f"  - {p}")
        print("Add deterministic unit tests in `tests/` covering the new functionality.")
        failures += 1

    if nondet_tests:
        print(
            "ERROR: The following test files contain patterns that are often non-deterministic (review/mask if intentional):"
        )
        for p in nondet_tests:
            print(f"  - {p}")
        failures += 1

    if failures:
        print("\nSee COPILOT_INSTRUCTIONS.md for guidance and how to fix these failures.")
        return 2
    print("Copilot guidelines check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
