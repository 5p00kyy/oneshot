#!/usr/bin/env python3
"""Install the bundled OneShot skill into a supported agent skill directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "oneshot"
SKILL_NAME = "oneshot"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def default_destination(target: str, scope: str, project_root: Path) -> Path:
    if target == "opencode":
        base = Path.home() / ".config" / "opencode" / "skills" if scope == "user" else project_root / ".opencode" / "skills"
    elif target == "agents":
        base = Path.home() / ".agents" / "skills" if scope == "user" else project_root / ".agents" / "skills"
    elif target == "claude":
        base = Path.home() / ".claude" / "skills" if scope == "user" else project_root / ".claude" / "skills"
    else:
        fail(f"Unsupported target: {target}")
    return base / SKILL_NAME


def ignore_junk(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name == "__pycache__" or name in {".DS_Store", "Thumbs.db"} or name.endswith((".pyc", ".pyo")):
            ignored.add(name)
    return ignored


def validate_source() -> None:
    validator = SOURCE / "scripts" / "validate_skill.py"
    if not validator.is_file():
        fail("Bundled skill validator is missing")
    result = subprocess.run([sys.executable, str(validator)], cwd=SOURCE, check=False)
    if result.returncode:
        fail("Bundled skill failed validation; installation was not attempted")


def install(destination: Path, force: bool, dry_run: bool) -> None:
    if not SOURCE.is_dir():
        fail("Bundled skills/oneshot directory is missing")

    destination = destination.expanduser().resolve()
    if destination == SOURCE.resolve() or SOURCE.resolve() in destination.parents:
        fail("Destination cannot be the bundled source directory or a child of it")

    if dry_run:
        state = "replace" if destination.exists() else "create"
        print(f"DRY RUN: would {state} {destination}")
        print(f"Source: {SOURCE}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        fail(f"Destination already exists: {destination} (use --force to replace it)")

    temp_root = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-install-", dir=destination.parent))
    staged = temp_root / SKILL_NAME
    backup: Path | None = None

    try:
        shutil.copytree(SOURCE, staged, ignore=ignore_junk)
        if destination.exists():
            backup = destination.parent / f".{destination.name}.backup-{os.getpid()}"
            if backup.exists():
                shutil.rmtree(backup)
            destination.replace(backup)
        staged.replace(destination)
        if backup and backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if backup and backup.exists() and not destination.exists():
            backup.replace(destination)
        raise
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)

    print(f"OK: installed {SKILL_NAME} to {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("opencode", "agents", "claude"), default="opencode")
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used for project-scoped installation (default: current directory)",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        help="Explicit destination; overrides --target and --scope",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing installation")
    parser.add_argument("--dry-run", action="store_true", help="Show the destination without writing files")
    parser.add_argument("--skip-validation", action="store_true", help="Skip source validation")
    args = parser.parse_args()

    if not args.skip_validation:
        validate_source()

    destination = args.destination or default_destination(args.target, args.scope, args.project_root.resolve())
    install(destination, args.force, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
