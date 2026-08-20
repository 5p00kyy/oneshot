#!/usr/bin/env python3
"""Validate the public OneShot repository and its release packaging."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "oneshot"
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
JUNK_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
JUNK_SUFFIXES = {".pyc", ".pyo"}
REQUIRED_ROOT_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PUBLISHING.md",
    "README.md",
    "SECURITY.md",
    ".github/workflows/validate.yml",
    ".github/workflows/release.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/pull_request_template.md",
    ".github/dependabot.yml",
    "install.ps1",
    "install.sh",
    "scripts/install_skill.py",
    "scripts/package_release.py",
    "scripts/validate_repo.py",
    "tests/test_repository.py",
}
FORBIDDEN_ROOT_FILES = {"OPENCODE_HANDOFF.md", "START_HERE.md"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        if result.stdout:
            print(result.stdout, file=sys.stderr, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        fail(f"Command failed ({result.returncode}): {' '.join(command)}")
    return result


def validate_required_files() -> None:
    missing = sorted(path for path in REQUIRED_ROOT_FILES if not (ROOT / path).is_file())
    if missing:
        fail("Missing required repository files: " + ", ".join(missing))
    if not (SKILL_DIR / "SKILL.md").is_file():
        fail("Missing skills/oneshot/SKILL.md")
    obsolete = sorted(path for path in FORBIDDEN_ROOT_FILES if (ROOT / path).exists())
    if obsolete:
        fail("Obsolete bootstrap files are present: " + ", ".join(obsolete))


def validate_no_junk() -> None:
    # The portable skill must never contain generated caches. Repository-level
    # untracked caches may be created by local tests and are excluded by Git.
    for path in SKILL_DIR.rglob("*"):
        if path.name in JUNK_NAMES or path.suffix in JUNK_SUFFIXES:
            fail(f"Generated or operating-system junk is present in the skill: {path.relative_to(ROOT)}")

    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            for raw in result.stdout.split(b"\0"):
                if not raw:
                    continue
                path = Path(raw.decode("utf-8", errors="replace"))
                if path.name in JUNK_NAMES or path.suffix in JUNK_SUFFIXES or "__pycache__" in path.parts:
                    fail(f"Generated junk is tracked by Git: {path}")


def validate_links() -> None:
    for source in sorted(ROOT.rglob("*.md")):
        if ".git" in source.parts or "dist" in source.parts:
            continue
        text = source.read_text(encoding="utf-8")
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
                fail(f"Markdown link escapes repository: {source.relative_to(ROOT)} -> {target}")
            if not resolved.exists():
                fail(f"Broken Markdown link: {source.relative_to(ROOT)} -> {target}")


def validate_license_and_version() -> str:
    root_license = (ROOT / "LICENSE").read_text(encoding="utf-8")
    skill_license = (SKILL_DIR / "LICENSE").read_text(encoding="utf-8")
    if root_license != skill_license:
        fail("Root LICENSE and skills/oneshot/LICENSE differ")

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"(?m)^license:\s*MIT\s*$", skill_text):
        fail("skills/oneshot/SKILL.md must declare license: MIT")
    version_match = re.search(
        r"(?m)^\s{2}version:\s*[\"']?([^\"'\s]+)[\"']?\s*$",
        skill_text,
    )
    if not version_match:
        fail("SKILL.md metadata.version is missing")
    version = version_match.group(1)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        fail(f"CHANGELOG.md has no release entry for version {version}")
    return version


def validate_workflows() -> None:
    validation = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    for signal in (
        "scripts/validate_repo.py",
        "unittest discover",
        "scripts/package_release.py",
        "gh skill publish . --dry-run",
    ):
        if signal not in validation:
            fail(f"Validation workflow is missing: {signal}")

    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    for signal in (
        "tags:",
        "concurrency:",
        "persist-credentials: false",
        "git/ref/tags/",
        "git merge-base --is-ancestor",
        "scripts/validate_repo.py",
        "scripts/package_release.py",
        "actions/attest-build-provenance@",
        "actions/download-artifact@",
        "attestations: write",
        "contents: write",
        "GH_TOKEN:",
        "gh release view",
        "gh release create",
    ):
        if signal not in release:
            fail(f"Release workflow is missing: {signal}")
    for forbidden in ("--clobber", "gh skill publish . --tag"):
        if forbidden in release:
            fail(f"Release workflow contains mutable or competing publication behavior: {forbidden}")

    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        refs = re.findall(r"(?m)^\s*uses:\s*[^@\s]+@([^\s#]+)", text)
        mutable = sorted(ref for ref in refs if not re.fullmatch(r"[0-9a-f]{40}", ref))
        if mutable:
            fail(f"Workflow actions must use full commit SHAs ({workflow.name}): {', '.join(mutable)}")

    dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    for signal in ("version: 2", "package-ecosystem: github-actions", "interval: weekly"):
        if signal not in dependabot:
            fail(f"Dependabot configuration is missing: {signal}")


def validate_python_syntax() -> None:
    for source in sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
        try:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        except SyntaxError as exc:
            fail(f"Python syntax error in {source.relative_to(ROOT)}: {exc}")


def load_packager() -> ModuleType:
    path = ROOT / "scripts" / "package_release.py"
    spec = importlib.util.spec_from_file_location("oneshot_package_release", path)
    if spec is None or spec.loader is None:
        fail("Could not load scripts/package_release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_deterministic_package(version: str) -> None:
    packager = load_packager()
    with tempfile.TemporaryDirectory(prefix="oneshot-repo-check-") as temp:
        temp_path = Path(temp)
        first_dir = temp_path / "first"
        second_dir = temp_path / "second"
        first_archive, first_checksum = packager.build_archive(first_dir)
        second_archive, second_checksum = packager.build_archive(second_dir)

        first_bytes = first_archive.read_bytes()
        second_bytes = second_archive.read_bytes()
        if first_bytes != second_bytes:
            fail("Release packaging is not deterministic")

        digest = hashlib.sha256(first_bytes).hexdigest()
        checksum_text = first_checksum.read_text(encoding="utf-8")
        if not checksum_text.startswith(digest + "  "):
            fail("Release checksum does not match archive")
        if first_checksum.name != f"oneshot-skill-v{version}.zip.sha256":
            fail("Unexpected checksum filename")
        if second_checksum.read_text(encoding="utf-8") != checksum_text:
            fail("Deterministic package checksums differ")

        extracted = temp_path / "extracted"
        with zipfile.ZipFile(first_archive) as archive:
            archive.extractall(extracted)
        validator = extracted / "oneshot" / "scripts" / "validate_skill.py"
        result = subprocess.run(
            [sys.executable, str(validator)],
            cwd=extracted / "oneshot",
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            if result.stdout:
                print(result.stdout, file=sys.stderr, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")
            fail("Extracted release package failed portable-skill validation")


def main() -> None:
    validate_required_files()
    validate_no_junk()
    validate_links()
    version = validate_license_and_version()
    validate_workflows()
    validate_python_syntax()

    result = run([sys.executable, str(SKILL_DIR / "scripts" / "validate_skill.py")])
    print(result.stdout, end="")

    validate_deterministic_package(version)

    print("OK: public repository is valid")
    print(f"Version: {version}")
    print("Skill path: skills/oneshot/SKILL.md")
    print("Release package: deterministic")


if __name__ == "__main__":
    main()
