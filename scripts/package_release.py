#!/usr/bin/env python3
"""Create a deterministic, installable OneShot skill ZIP and SHA-256 file."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "oneshot"
SKILL_NAME = "oneshot"
JUNK_PARTS = {"__pycache__", ".DS_Store", "Thumbs.db"}
JUNK_SUFFIXES = {".pyc", ".pyo"}
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_version() -> str:
    skill_file = SKILL_DIR / "SKILL.md"
    if not skill_file.exists():
        fail(f"Missing {skill_file.relative_to(ROOT)}")
    text = skill_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s{2}version:\s*[\"']?([^\"'\s]+)[\"']?\s*$", text)
    if not match:
        fail("Could not find metadata.version in skills/oneshot/SKILL.md")
    version = match.group(1)
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        fail(f"metadata.version is not valid semantic-version text: {version}")
    return version


def is_junk(path: Path) -> bool:
    return any(part in JUNK_PARTS for part in path.parts) or path.suffix in JUNK_SUFFIXES


def source_files() -> list[Path]:
    if SKILL_DIR.is_symlink():
        fail("The skills/oneshot package directory must not be a symbolic link")
    if not SKILL_DIR.is_dir():
        fail("Missing skills/oneshot directory")

    files: list[Path] = []
    for path in SKILL_DIR.rglob("*"):
        if path.is_symlink():
            fail(f"Symbolic links are not allowed in the skill package: {path.relative_to(SKILL_DIR)}")
        if path.is_dir():
            continue
        if not path.is_file():
            fail(f"Unsupported filesystem entry in the skill package: {path.relative_to(SKILL_DIR)}")
        if not is_junk(path):
            files.append(path)

    files.sort(key=lambda path: path.relative_to(SKILL_DIR).as_posix())
    if not files:
        fail("No skill files found")
    return files


def archive_names(files: list[Path]) -> list[str]:
    return [f"{SKILL_NAME}/{path.relative_to(SKILL_DIR).as_posix()}" for path in files]


def zip_info(archive_name: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_name, FIXED_TIMESTAMP)
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_archive(output_dir: Path) -> tuple[Path, Path]:
    version = read_version()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"oneshot-skill-v{version}.zip"
    checksum = output_dir / f"{archive.name}.sha256"

    files = source_files()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for source in files:
            archive_name = f"{SKILL_NAME}/{source.relative_to(SKILL_DIR).as_posix()}"
            executable = source.suffix == ".py" or bool(source.stat().st_mode & 0o111)
            zf.writestr(zip_info(archive_name, executable), source.read_bytes())

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    verify_archive(archive)
    return archive, checksum


def verify_archive(archive: Path) -> None:
    if not archive.is_file():
        fail(f"Archive not found: {archive}")

    with zipfile.ZipFile(archive) as zf:
        bad_member = zf.testzip()
        if bad_member:
            fail(f"ZIP integrity failure in member: {bad_member}")
        names = zf.namelist()

    if not names:
        fail("Release ZIP is empty")
    if len(names) != len(set(names)):
        fail("Release ZIP contains duplicate members")

    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            fail(f"Unsafe archive path: {name}")
        if not path.parts or path.parts[0] != SKILL_NAME:
            fail(f"Archive member is outside the {SKILL_NAME}/ top-level directory: {name}")
        if any(part in JUNK_PARTS for part in path.parts) or path.suffix in JUNK_SUFFIXES:
            fail(f"Junk file included in archive: {name}")

    expected = archive_names(source_files())
    if names != expected:
        missing = sorted(set(expected) - set(names))
        unexpected = sorted(set(names) - set(expected))
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        if not details:
            details.append("member ordering differs from the source manifest")
        fail("Release ZIP does not match the source manifest (" + "; ".join(details) + ")")

    required = {
        f"{SKILL_NAME}/SKILL.md",
        f"{SKILL_NAME}/LICENSE",
        f"{SKILL_NAME}/README.md",
        f"{SKILL_NAME}/scripts/validate_skill.py",
        f"{SKILL_NAME}/scripts/audit_prompt.py",
        f"{SKILL_NAME}/references/quality-rubric.md",
        f"{SKILL_NAME}/evals/evals.json",
        f"{SKILL_NAME}/evals/trigger-evals.json",
    }
    missing = sorted(required - set(names))
    if missing:
        fail("Release ZIP is missing required files: " + ", ".join(missing))


def clean_output(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
        help="Directory for generated ZIP and checksum (default: dist/)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the output directory before packaging",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    if args.clean:
        clean_output(output_dir)

    archive, checksum = build_archive(output_dir)
    digest = checksum.read_text(encoding="utf-8").split()[0]
    print(f"OK: created {archive}")
    print(f"OK: created {checksum}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
