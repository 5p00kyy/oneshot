#!/usr/bin/env python3
"""Validate the portable OneShot Agent Skill without third-party modules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TypeAlias

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
KNOWN_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
JUNK_NAMES = {".DS_Store", "Thumbs.db"}

Scalar: TypeAlias = str
Frontmatter: TypeAlias = dict[str, Scalar | dict[str, Scalar]]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def strip_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[Frontmatter, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md must begin with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        fail("SKILL.md frontmatter is not closed")

    raw = text[4:end]
    body = text[end + 5 :]
    values: Frontmatter = {}
    current_mapping: str | None = None
    nested_indent: int | None = None

    for line_number, line in enumerate(raw.splitlines(), start=2):
        if "\t" in line:
            fail(f"Tabs are not allowed in frontmatter (line {line_number})")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent:
            if current_mapping is None:
                fail(f"Unexpected nested frontmatter line {line_number}: {line}")
            if nested_indent is None:
                nested_indent = indent
            elif indent != nested_indent:
                fail(f"Inconsistent nested frontmatter indentation (line {line_number})")
            nested_line = line[indent:]
            if ":" not in nested_line:
                fail(f"Invalid nested frontmatter line {line_number}: {line}")
            key, value = nested_line.split(":", 1)
            key = key.strip()
            scalar = strip_scalar(value)
            if not key or not scalar:
                fail(f"Nested frontmatter values must be non-empty (line {line_number})")
            mapping = values[current_mapping]
            if not isinstance(mapping, dict):
                fail(f"Frontmatter field {current_mapping} is not a mapping")
            if key in mapping:
                fail(f"Duplicate nested frontmatter field: {current_mapping}.{key}")
            mapping[key] = scalar
            continue

        if line.startswith(" "):
            fail(f"Top-level frontmatter keys must not be indented (line {line_number})")
        if ":" not in line:
            fail(f"Invalid frontmatter line {line_number}: {line}")

        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            fail(f"Empty frontmatter key on line {line_number}")
        if key in values:
            fail(f"Duplicate frontmatter field: {key}")

        scalar = strip_scalar(value)
        if scalar:
            values[key] = scalar
            current_mapping = None
            nested_indent = None
        else:
            values[key] = {}
            current_mapping = key
            nested_indent = None

    return values, body


def require_scalar(frontmatter: Frontmatter, field: str) -> str:
    value = frontmatter.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"Missing or invalid required frontmatter field: {field}")
    return value.strip()


def validate_links(text: str, source: Path) -> None:
    for target in LINK_RE.findall(text):
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0].strip()
        if not clean:
            continue
        resolved = (source.parent / clean).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            fail(f"Link escapes skill directory: {source.relative_to(ROOT)} -> {target}")
        if not resolved.exists():
            fail(f"Broken link: {source.relative_to(ROOT)} -> {target}")


def validate_no_junk() -> None:
    for path in ROOT.rglob("*"):
        if path.name in JUNK_NAMES or path.suffix == ".pyc" or path.name == "__pycache__":
            fail(f"Generated or operating-system junk is present: {path.relative_to(ROOT)}")


def validate_evaluations(name: str) -> tuple[int, int]:
    evals_path = ROOT / "evals" / "evals.json"
    if not evals_path.exists():
        fail("Missing evals/evals.json")
    try:
        eval_data = json.loads(evals_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid evals JSON: {exc}")
    if eval_data.get("skill_name") != name:
        fail("evals skill_name does not match SKILL.md name")
    evals = eval_data.get("evals")
    if not isinstance(evals, list) or not evals:
        fail("evals/evals.json must contain a non-empty evals list")
    ids: list[object] = []
    for entry in evals:
        if not isinstance(entry, dict):
            fail("Every evaluation must be an object")
        identifier = entry.get("id")
        if identifier is None:
            fail("Every evaluation must define an id")
        ids.append(identifier)
        if not str(entry.get("prompt", "")).strip():
            fail(f"Evaluation {identifier} has no prompt")
        if not str(entry.get("expected_output", "")).strip():
            fail(f"Evaluation {identifier} has no expected_output")
    if len(ids) != len(set(ids)):
        fail("Evaluation IDs must be unique")

    trigger_path = ROOT / "evals" / "trigger-evals.json"
    if not trigger_path.exists():
        fail("Missing evals/trigger-evals.json")
    try:
        trigger_data = json.loads(trigger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid trigger evals JSON: {exc}")
    if trigger_data.get("skill_name") != name:
        fail("trigger-evals skill_name does not match SKILL.md name")
    trigger_cases = trigger_data.get("cases")
    if not isinstance(trigger_cases, list) or not trigger_cases:
        fail("evals/trigger-evals.json must contain a non-empty cases list")

    positive = 0
    negative = 0
    for index, case in enumerate(trigger_cases, start=1):
        if not isinstance(case, dict):
            fail(f"Trigger case {index} must be an object")
        if not str(case.get("prompt", "")).strip():
            fail(f"Trigger case {index} has no prompt")
        should_trigger = case.get("should_trigger")
        if not isinstance(should_trigger, bool):
            fail(f"Trigger case {index} must define boolean should_trigger")
        positive += int(should_trigger)
        negative += int(not should_trigger)
        if not str(case.get("reason", "")).strip():
            fail(f"Trigger case {index} has no reason")
    if not positive or not negative:
        fail("Trigger evaluations must include both positive and negative cases")

    return len(evals), len(trigger_cases)


def validate_python_scripts() -> int:
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    if not scripts:
        fail("No Python helper scripts found")
    for script in scripts:
        source = script.read_text(encoding="utf-8")
        try:
            compile(source, str(script), "exec")
        except SyntaxError as exc:
            fail(f"Python syntax error in {script.name}: {exc}")
    return len(scripts)


def main() -> None:
    if not SKILL.exists():
        fail("Missing SKILL.md")

    validate_no_junk()

    text = SKILL.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)

    unknown_fields = sorted(set(frontmatter) - KNOWN_FIELDS)
    if unknown_fields:
        fail(f"Unrecognized top-level frontmatter fields: {', '.join(unknown_fields)}")

    name = require_scalar(frontmatter, "name")
    description = require_scalar(frontmatter, "description")

    if not NAME_RE.fullmatch(name):
        fail("Skill name must contain lowercase letters, digits, and single hyphens only")
    if len(name) > 64:
        fail("Skill name exceeds 64 characters")
    if name != ROOT.name:
        fail(f"Skill name '{name}' must match directory name '{ROOT.name}'")
    if len(description) > 1024:
        fail("Description exceeds 1024 characters")
    if not body.strip():
        fail("SKILL.md body is empty")

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500:
            fail("compatibility must be a non-empty string no longer than 500 characters")

    license_name = frontmatter.get("license")
    if license_name is not None:
        if not isinstance(license_name, str) or not license_name.strip():
            fail("license must be a non-empty string")
        if license_name == "MIT" and not (ROOT / "LICENSE").exists():
            fail("license is MIT but the skill package has no LICENSE file")

    metadata = frontmatter.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        fail("metadata must be a string-to-string mapping")

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        fail("allowed-tools must be a space-separated string")

    line_count = len(text.splitlines())
    word_count = len(re.findall(r"\b\w[\w'-]*\b", text))
    if line_count > 500:
        fail(f"SKILL.md has {line_count} lines; recommended maximum is 500")

    for markdown in sorted(ROOT.rglob("*.md")):
        validate_links(markdown.read_text(encoding="utf-8"), markdown)

    eval_count, trigger_count = validate_evaluations(name)

    interface_path = ROOT / "agents" / "openai.yaml"
    if not interface_path.exists():
        fail("Missing agents/openai.yaml")
    interface_text = interface_path.read_text(encoding="utf-8")
    for required in ("display_name:", "short_description:", "default_prompt:"):
        if required not in interface_text:
            fail(f"agents/openai.yaml is missing {required}")

    script_count = validate_python_scripts()

    print(f"OK: {name} skill is valid")
    print(f"SKILL.md lines: {line_count}")
    print(f"SKILL.md words: {word_count}")
    print(f"Output evaluations: {eval_count}")
    print(f"Trigger evaluations: {trigger_count}")
    print(f"Markdown files: {sum(1 for _ in ROOT.rglob('*.md'))}")
    print(f"Python helpers: {script_count}")


if __name__ == "__main__":
    main()
