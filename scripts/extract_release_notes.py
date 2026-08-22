#!/usr/bin/env python3
"""Extract one version's curated release notes from CHANGELOG.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADER_RE = re.compile(r"^## \[(?P<version>[^]]+)](?:\s+-\s+.+)?$")


def extract_release_notes(changelog: str, version: str) -> str:
    version = version.removeprefix("v")
    lines = changelog.splitlines()
    matches = [index for index, line in enumerate(lines) if (match := HEADER_RE.match(line)) and match.group("version") == version]
    if len(matches) != 1:
        raise ValueError(f"expected one changelog section for {version}, found {len(matches)}")

    start = matches[0] + 1
    end = next((index for index in range(start, len(lines)) if HEADER_RE.match(lines[index])), len(lines))
    body = "\n".join(lines[start:end]).strip()
    if not body:
        raise ValueError(f"changelog section for {version} is empty")
    return body + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Release version, with or without a leading v")
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    notes = extract_release_notes(args.changelog.read_text(encoding="utf-8"), args.version)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(notes, encoding="utf-8")
    else:
        print(notes, end="")


if __name__ == "__main__":
    main()
