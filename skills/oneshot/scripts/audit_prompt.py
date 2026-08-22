#!/usr/bin/env python3
"""Profile-aware mechanical audit for OneShot prompts.

The audit catches common omissions and prompt smells. It does not replace the
profile quality gate or semantic review.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "mission/outcome": (r"\bmission\b", r"\bgoal\b", r"\bobjective\b", r"definition of (?:done|finished)"),
    "deliverables/output": (r"\bdeliverables?\b", r"output contract", r"final response", r"return exactly", r"##\s+output\b", r"final output"),
    "scope/constraints": (r"\bscope\b", r"constraints?", r"non-goals?", r"must not", r"do not"),
    "workflow/execution": (r"\bworkflow\b", r"implementation sequence", r"execution", r"phase 0", r"phase 1"),
    "verification/acceptance": (r"acceptance tests?", r"\bacceptance\b", r"verification", r"definition of done", r"quality gate"),
    "priorities/fallbacks": (r"\bpriority\b", r"priority 0", r"priority order", r"cut first", r"fallback", r"failure handling"),
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

# Evaluation mechanics belong in the challenge manifest or evaluator, never in
# a Brief/Benchmark contestant prompt. Patterns intentionally target mechanics,
# not artifact behavior such as an in-game score.
EVALUATOR_LEAK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:scoring|grading) (?:weights?|criteria|rubric|system|procedure)\b", "scoring mechanics"),
    (r"\b(?:points? (?:are )?awarded|weighted score|score weighting|evaluation score)\b", "scoring mechanics"),
    (r"\b(?:evaluator|judge model|adjudicator) (?:will|must|should|checks?|sees?|uses?|internals?)\b", "evaluator internals"),
    (r"\bhidden (?:tests?|cases?|fixtures?|checks?)\b", "hidden cases"),
    (r"\b(?:evaluation|benchmark|grading|test) harness\b", "harness procedure"),
    (r"\b(?:run|invoke|call) (?:the )?harness\b", "harness procedure"),
    (r"\b(?:retry policy|retry budget|retries allowed|allowed retries|attempts allowed)\b", "retry policy"),
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
    return re.sub(r"\s+", " ", line).strip()


def count_matches(text: str, patterns: tuple[str, ...]) -> int:
    return sum(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a one-shot prompt using a calibrated profile.")
    parser.add_argument("prompt", type=Path, help="Path to a Markdown or text prompt")
    parser.add_argument(
        "--profile",
        choices=("brief", "benchmark", "extensive"),
        default="extensive",
        help="Prompt-depth profile (default: extensive for backward compatibility)",
    )
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

    if args.profile == "brief":
        if len(words) > 120:
            warnings.append("Brief exceeds the default 120-word envelope; compress it or justify the extra detail.")
    elif args.profile == "benchmark":
        if len(words) > 700:
            errors.append("Benchmark exceeds the 700-word cap.")
    else:
        if len(words) < 250:
            notes.append("Extensive prompt is under 250 words; verify that Extensive is the right profile.")
        elif len(words) > 12_000:
            warnings.append("Prompt exceeds 12,000 words; perform an aggressive deduplication and salience review.")
        if len(headings) < 4:
            warnings.append("Fewer than four Markdown headings detected; an Extensive prompt may be hard to navigate.")
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

    if args.profile in {"brief", "benchmark"}:
        leaked: list[str] = []
        for pattern, label in EVALUATOR_LEAK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                leaked.append(label)
        for label in dict.fromkeys(leaked):
            errors.append(f"Contestant prompt leaks {label}; move it to the manifest or evaluator.")

    normalized_lines = [normalize_line(line) for line in text.splitlines()]
    repeated = Counter(
        line for line in normalized_lines
        if len(line.split()) >= 6 and not line.startswith("http")
    )
    duplicates = [(line, count) for line, count in repeated.items() if count >= 3]
    if duplicates:
        warnings.append(
            "Repeated directive-like lines detected: "
            + "; ".join(f"{count}x '{line[:90]}'" for line, count in duplicates[:5])
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

    if "placeholder" not in lower and not any(re.search(pattern, text, re.IGNORECASE) for pattern, _ in PLACEHOLDER_PATTERNS):
        notes.append("No obvious unresolved placeholders detected.")

    score = max(0, 100 - 12 * len(errors) - 4 * len(warnings))

    print(f"Prompt: {args.prompt}")
    print(f"Profile: {args.profile}")
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
        print("\nNo mechanical defects detected. Complete the profile's semantic quality gate.")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
