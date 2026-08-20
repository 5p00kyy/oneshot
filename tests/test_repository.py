from __future__ import annotations

from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class RepositoryTests(unittest.TestCase):
    def load_packager(self) -> ModuleType:
        path = ROOT / "scripts" / "package_release.py"
        spec = importlib.util.spec_from_file_location("oneshot_test_packager", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec else None)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module

    def run_command(self, *parts: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [PYTHON, *parts],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"command failed: {' '.join(parts)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        return result

    def test_portable_skill_validator(self) -> None:
        result = self.run_command("skills/oneshot/scripts/validate_skill.py")
        self.assertIn("OK: oneshot skill is valid", result.stdout)

    def test_portable_validator_accepts_installer_metadata_indentation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-installed-validation-") as temp:
            skill = Path(temp) / "oneshot"
            shutil.copytree(ROOT / "skills" / "oneshot", skill)
            skill_file = skill / "SKILL.md"
            text = skill_file.read_text(encoding="utf-8")
            text = text.replace(
                '  version: "1.0.1"\n  category: "prompt-authoring"',
                "    version: 1.0.1\n"
                "    category: prompt-authoring\n"
                "    github-ref: refs/tags/v1.0.1\n"
                "    github-repo: https://github.com/5p00kyy/oneshot",
            )
            skill_file.write_text(text, encoding="utf-8", newline="\n")

            result = subprocess.run(
                [PYTHON, str(skill / "scripts" / "validate_skill.py")],
                cwd=skill,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("OK: oneshot skill is valid", result.stdout)

    def test_prompt_audit_accepts_complete_fixture(self) -> None:
        result = self.run_command(
            "skills/oneshot/scripts/audit_prompt.py",
            "tests/fixtures/good-prompt.md",
            "--strict",
        )
        self.assertIn("No mechanical defects detected", result.stdout)

    def test_prompt_audit_rejects_incomplete_fixture(self) -> None:
        result = self.run_command(
            "skills/oneshot/scripts/audit_prompt.py",
            "tests/fixtures/bad-prompt.md",
            "--strict",
            expected=1,
        )
        self.assertIn("ERRORS", result.stdout)
        self.assertIn("TODO marker", result.stdout)

    def test_release_package_is_deterministic_and_safe(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-package-test-") as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            self.run_command("scripts/package_release.py", "--output-dir", str(first))
            self.run_command("scripts/package_release.py", "--output-dir", str(second))

            first_zip = next(first.glob("*.zip"))
            second_zip = next(second.glob("*.zip"))
            self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())

            checksum = next(first.glob("*.sha256")).read_text(encoding="utf-8").split()[0]
            self.assertEqual(checksum, hashlib.sha256(first_zip.read_bytes()).hexdigest())

            with zipfile.ZipFile(first_zip) as archive:
                names = archive.namelist()
                extracted = Path(temp) / "extracted"
                archive.extractall(extracted)
                self.assertIn("oneshot/SKILL.md", names)
                self.assertIn("oneshot/LICENSE", names)
                self.assertTrue(all(name.startswith("oneshot/") for name in names))
                self.assertFalse(any(".." in Path(name).parts for name in names))
                self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))

                expected = sorted(
                    f"oneshot/{path.relative_to(ROOT / 'skills' / 'oneshot').as_posix()}"
                    for path in (ROOT / "skills" / "oneshot").rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
                )
                self.assertEqual(names, expected)

            validator = extracted / "oneshot" / "scripts" / "validate_skill.py"
            result = subprocess.run(
                [PYTHON, str(validator)],
                cwd=extracted / "oneshot",
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("OK: oneshot skill is valid", result.stdout)

            with zipfile.ZipFile(first_zip, "a") as archive:
                archive.writestr("oneshot/unexpected.txt", "unexpected")
            packager = self.load_packager()
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    packager.verify_archive(first_zip)

    def test_release_package_rejects_symbolic_links(self) -> None:
        packager = self.load_packager()
        with tempfile.TemporaryDirectory(prefix="oneshot-symlink-test-") as temp:
            skill = Path(temp) / "oneshot"
            shutil.copytree(ROOT / "skills" / "oneshot", skill)
            (skill / "unsafe-link").symlink_to(Path(temp) / "outside")

            with mock.patch.object(packager, "SKILL_DIR", skill):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        packager.source_files()

    def test_finished_repository_excludes_bootstrap_artifacts(self) -> None:
        self.assertFalse((ROOT / "OPENCODE_HANDOFF.md").exists())
        self.assertFalse((ROOT / "START_HERE.md").exists())
        publishing = (ROOT / "PUBLISHING.md").read_text(encoding="utf-8")
        self.assertIn("one release authority", publishing)
        self.assertNotIn("gh repo create", publishing)

    def test_release_workflow_is_immutable_and_single_authority(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        required = (
            'tags:\n      - "v*"',
            "concurrency:",
            "persist-credentials: false",
            "git/ref/tags/",
            "git merge-base --is-ancestor",
            "actions/attest-build-provenance@",
            "attestations: write",
            "GH_TOKEN:",
            "actions/download-artifact@",
            "gh release view",
            "gh release create",
            "--verify-tag",
        )
        for signal in required:
            self.assertIn(signal, workflow)
        self.assertEqual(workflow.count("contents: write"), 1)
        self.assertNotIn("--clobber", workflow)
        self.assertNotIn("gh skill publish . --tag", workflow)

        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: github-actions", dependabot)
        self.assertIn("interval: weekly", dependabot)

    def test_workflow_actions_are_pinned_to_full_commit_shas(self) -> None:
        for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
            text = workflow.read_text(encoding="utf-8")
            refs = re.findall(r"(?m)^\s*uses:\s*[^@\s]+@([^\s#]+)", text)
            self.assertTrue(refs, msg=f"no action references found in {workflow.name}")
            for ref in refs:
                self.assertRegex(ref, r"^[0-9a-f]{40}$", msg=f"mutable action ref in {workflow.name}: {ref}")

    def test_custom_install_and_force_replace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-install-test-") as temp:
            destination = Path(temp) / "installed" / "oneshot"
            self.run_command(
                "scripts/install_skill.py",
                "--destination",
                str(destination),
                "--skip-validation",
            )
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "references" / "quality-rubric.md").is_file())

            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/install_skill.py",
                    "--destination",
                    str(destination),
                    "--skip-validation",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Destination already exists", result.stderr)

            self.run_command(
                "scripts/install_skill.py",
                "--destination",
                str(destination),
                "--skip-validation",
                "--force",
            )
            self.assertTrue((destination / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
