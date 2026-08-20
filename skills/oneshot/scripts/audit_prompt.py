#!/usr/bin/env python3
"""Mechanical audit for one-shot prompts.

This script catches common structural omissions and prompt smells. It does not
replace semantic review with the quality rubric.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "mission/outcome": (r"\bmission\b", r"\bgoal\b", r"\bobjective\b", r"definition of (?:done|finished)"),
    "deliverables/output": (r"\bdeliverables?\b", r"output contract", r"final response", r"return exactly"),
    "scope/constraints": (r"\bscope\b", r"constraints?", r"non-goals?", r"must not", r"do not"),
    "workflow/execution": (r"\bworkflow\b", r"implementation sequence", r"execution", r"phase 0", r"phase 1"),
    "verification/acceptance": (r"acceptance tests?", r"verification", r"definition of done", r"quality gate"),
    "priorities/fallbacks": (r"priority 0", r"priority order", r"cut first", r"fallback", r"failure handling"),
    "handoff": (r"handoff", r"verification actually performed", r"remaining limitations", r"how to run"),
}

PLACEHOLDER_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bTODO\b", "TODO marker"),
    (r"\bFIXME\b", "FIXME marker"),
    (r"\bTBD\b", "TBD marker"),
    (r"\bTBC\b", "TBC marker"),
    (r"\[\s*(?:insert|replace|describe|name|add|your)\b[^\]]*\]", "bracketed template placeholder"),
    (r"\{\{[^{}]+\}\}", "double-brace template placeholder"),
    (r"<\s*(?:insert|replace|your|placeholder)[^>]*>", "angle-bracket template placeholder"),
    (r"(?m)^\s*\.\.\.\s*$", "ellipsis-only omitted section"),
    (r"add more (?:here|later)", "explicit omitted content"),
)

CHAIN_OF_THOUGHT_PATTERNS: tuple[str, ...] = (
    r"think step by step",
    r"show (?:all |your )?(?:chain of thought|reasoning process)",
    r"reveal (?:your )?(?:private )?reasoning",
    r"write out (?:your )?internal reasoning",
)

VAGUE_TERMS: tuple[str, ...] = (
    "production-ready",
    "high quality",
    "high-quality",
    "modern",
    "polished",
    "robust",
    "beautiful",
    "professional",
    "world-class",
    "aaa",
)


def normalize_line(line: str) -> str:
    line = re.sub(r"[`*_>#-]", " ", line.lower())
    line = re.sub(r"\s+", " ", line).strip()
    return line


def count_matches(text: str, patterns: tuple[str, ...]) -> int:
    return sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a one-shot prompt for common structural defects.")
    parser.add_argument("prompt", type=Path, help="Path to a Markdown or text prompt")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a failing exit status")
    args = parser.parse_args()

    if not args.prompt.exists() or not args.prompt.is_file():
        print(f"ERROR: prompt file not found: {args.prompt}", file=sys.stderr)
        return 2

    text = args.prompt.read_text(encoding="utf-8")
    lower = text.lower()
    words = re.findall(r"\b[\w'-]+\b", text)
    headings = re.findall(r"(?m)^#{1,6}\s+.+$", text)

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if len(words) < 250:
        warnings.append("Prompt is under 250 words; verify that the task is genuinely narrow.")
    elif len(words) > 12_000:
        warnings.append("Prompt exceeds 12,000 words; perform an aggressive deduplication and salience review.")

    if len(headings) < 4:
        warnings.append("Fewer than four Markdown headings detected; complex prompts may be hard to navigate.")

    for category, patterns in CATEGORY_PATTERNS.items():
        if count_matches(lower, patterns) == 0:
            errors.append(f"Missing structural signal for {category}.")

    for pattern, label in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            errors.append(f"Found {len(matches)} occurrence(s) of {label}.")

    for pattern in CHAIN_OF_THOUGHT_PATTERNS:
        if re.search(pattern, lower):
            errors.append("Prompt requests exposed chain of thought; require observable evidence instead.")
            break

    normalized_lines = [normalize_line(line) for line in text.splitlines()]
    repeated = Counter(
        line for line in normalized_lines
        if len(line.split()) >= 6 and not line.startswith("http")
    )
    duplicates = [(line, count) for line, count in repeated.items() if count >= 3]
    if duplicates:
        warnings.append(
            "Repeated directive-like lines detected: "
            + "; ".join(f"{count}× '{line[:90]}'" for line, count in duplicates[:5])
        )

    vague_count = sum(lower.count(term) for term in VAGUE_TERMS)
    measurable_signals = len(re.findall(
        r"\b(?:test|verify|measure|budget|threshold|fps|latency|seconds?|milliseconds?|percent|schema|build|lint|typecheck|screenshot|citation|rollback|reload)\b",
        lower,
    ))
    if vague_count >= 8 and measurable_signals < vague_count * 2:
        warnings.append("Heavy use of vague quality terms without proportionate measurable evidence.")

    if "single file" in lower and re.search(r"\b(full|complete|maintainable|expandable) repository\b", lower):
        warnings.append("Possible scope conflict: both 'single file' and a full/maintainable repository are requested.")

    if "no external dependencies" in lower and re.search(r"\b(?:npm install|cdn|pip install|package manager)\b", lower):
        warnings.append("Possible dependency conflict: external dependencies are prohibited but installation/CDN language appears.")

    if re.search(r"\b(?:ask no questions|do not ask (?:a )?question)\b", lower) and "confirmation" not in lower:
        warnings.append("The prompt forbids all questions but defines no confirmation boundary for destructive or external actions.")

    if "actually" not in lower and "verification" in lower:
        notes.append("Consider requiring verification that was actually executed, not only planned.")

    if "placeholder" not in lower and not any(re.search(p, text, re.IGNORECASE) for p, _ in PLACEHOLDER_PATTERNS):
        notes.append("No obvious unresolved placeholders detected.")

    score = 100
    score -= 12 * len(errors)
    score -= 4 * len(warnings)
    score = max(0, score)

    print(f"Prompt: {args.prompt}")
    print(f"Words: {len(words):,}")
    print(f"Headings: {len(headings)}")
    print(f"Mechanical score: {score}/100")

    if errors:
        print("\nERRORS")
        for item in errors:
            print(f"- {item}")

    if warnings:
        print("\nWARNINGS")
        for item in warnings:
            print(f"- {item}")

    if notes:
        print("\nNOTES")
        for item in notes:
            print(f"- {item}")

    if not errors and not warnings:
        print("\nNo mechanical defects detected. Complete the semantic quality-rubric review.")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
