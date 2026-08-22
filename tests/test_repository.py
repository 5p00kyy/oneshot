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

    def load_repository_validator(self) -> ModuleType:
        path = ROOT / "scripts" / "validate_repo.py"
        spec = importlib.util.spec_from_file_location("oneshot_test_repository_validator", path)
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
                '  version: "1.2.0"\n  category: "prompt-authoring"',
                "    version: 1.2.0\n"
                "    category: prompt-authoring\n"
                "    github-ref: refs/tags/v1.2.0\n"
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

    def test_public_hygiene_rejects_common_private_machine_paths(self) -> None:
        validator = self.load_repository_validator()
        private_paths = (
            "/" + "home" + "/alice/project/secret.txt",
            "/" + "Users" + "/alice/project/secret.txt",
            "C:\\" + "Users" + r"\alice\project\secret.txt",
        )
        for private_path in private_paths:
            with self.subTest(private_path=private_path):
                with tempfile.TemporaryDirectory(prefix="oneshot-public-hygiene-test-") as temp:
                    root = Path(temp)
                    (root / "leak.txt").write_text(private_path, encoding="utf-8")
                    validator.ROOT = root
                    with redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            validator.validate_public_hygiene()

    def test_prompt_audit_accepts_complete_fixture(self) -> None:
        result = self.run_command(
            "skills/oneshot/scripts/audit_prompt.py",
            "tests/fixtures/good-prompt.md",
            "--strict",
        )
        self.assertIn("No mechanical defects detected", result.stdout)

    def test_prompt_audit_accepts_narrow_extensive_fixture_with_note(self) -> None:
        result = self.run_command(
            "skills/oneshot/scripts/audit_prompt.py",
            "tests/fixtures/narrow-prompt.md",
            "--strict",
        )
        self.assertIn("Mechanical score: 100/100", result.stdout)
        self.assertIn("Extensive prompt is under 250 words", result.stdout)
        self.assertNotIn("WARNINGS", result.stdout)

    def test_prompt_audit_accepts_one_sentence_brief(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-brief-test-") as temp:
            prompt = Path(temp) / "brief.md"
            prompt.write_text(
                "Generate an SVG of a pelican riding a bicycle. Return only valid SVG and check that it renders.\n",
                encoding="utf-8",
            )
            result = self.run_command(
                "skills/oneshot/scripts/audit_prompt.py",
                str(prompt),
                "--profile",
                "brief",
                "--strict",
            )
            self.assertIn("Profile: brief", result.stdout)
            self.assertIn("Headings: 0", result.stdout)
            self.assertIn("Mechanical score: 100/100", result.stdout)

    def test_prompt_audit_enforces_brief_and_benchmark_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-profile-boundary-test-") as temp:
            brief = Path(temp) / "brief.md"
            brief.write_text("word " * 121, encoding="utf-8")
            brief_result = self.run_command(
                "skills/oneshot/scripts/audit_prompt.py",
                str(brief),
                "--profile",
                "brief",
                "--strict",
                expected=1,
            )
            self.assertIn("120-word envelope", brief_result.stdout)

            benchmark = Path(temp) / "benchmark.md"
            benchmark.write_text("word " * 701, encoding="utf-8")
            benchmark_result = self.run_command(
                "skills/oneshot/scripts/audit_prompt.py",
                str(benchmark),
                "--profile",
                "benchmark",
                "--strict",
                expected=1,
            )
            self.assertIn("700-word cap", benchmark_result.stdout)

    def test_prompt_audit_rejects_benchmark_evaluator_leakage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-benchmark-leak-test-") as temp:
            prompt = Path(temp) / "benchmark.md"
            prompt.write_text(
                "Create one offline HTML game. Hidden tests award points using scoring weights.\n",
                encoding="utf-8",
            )
            result = self.run_command(
                "skills/oneshot/scripts/audit_prompt.py",
                str(prompt),
                "--profile",
                "benchmark",
                "--strict",
                expected=1,
            )
            self.assertIn("Contestant prompt leaks", result.stdout)

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

    def test_clean_rejects_dangerous_targets_without_deleting_them(self) -> None:
        packager = self.load_packager()
        dangerous = (
            Path(ROOT.anchor),
            ROOT.parent,
            ROOT,
            ROOT / "skills" / "oneshot",
            ROOT / "skills" / "oneshot" / "assets",
            Path.home(),
        )
        for target in dangerous:
            with self.subTest(target=target):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        packager.validate_clean_target(target)

        self.assertTrue((ROOT / "README.md").is_file())
        self.assertTrue((ROOT / "skills" / "oneshot" / "SKILL.md").is_file())

    def test_clean_rejects_symlink_and_unrelated_contents(self) -> None:
        packager = self.load_packager()
        with tempfile.TemporaryDirectory(prefix="oneshot-clean-safety-") as temp:
            root = Path(temp)
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            link = root / "linked-output"
            link.symlink_to(outside, target_is_directory=True)

            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    packager.clean_output(link)
                with self.assertRaises(SystemExit):
                    packager.clean_output(outside)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertTrue(link.is_symlink())

    def test_clean_allows_only_generated_release_output(self) -> None:
        packager = self.load_packager()
        with tempfile.TemporaryDirectory(prefix="oneshot-clean-generated-") as temp:
            root = Path(temp)
            output = root / "release-output"
            output.mkdir()
            (output / "oneshot-skill-v1.0.1.zip").write_bytes(b"archive")
            (output / "oneshot-skill-v1.0.1.zip.sha256").write_text(
                "digest  oneshot-skill-v1.0.1.zip\n", encoding="utf-8"
            )
            keep = root / "keep.txt"
            keep.write_text("keep", encoding="utf-8")

            cleaned = packager.clean_output(output)

            self.assertEqual(cleaned, output.resolve())
            self.assertFalse(output.exists())
            self.assertEqual(keep.read_text(encoding="utf-8"), "keep")
            self.assertEqual(packager.validate_clean_target(ROOT / "dist"), (ROOT / "dist").resolve())

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

    def test_installer_rejects_symlink_destination_component(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-install-symlink-") as temp:
            root = Path(temp)
            outside = root / "outside"
            outside.mkdir()
            link = root / "linked"
            link.symlink_to(outside, target_is_directory=True)
            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/install_skill.py",
                    "--destination",
                    str(link / "oneshot"),
                    "--skip-validation",
                    "--force",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symbolic link", result.stderr)
            self.assertFalse((outside / "oneshot").exists())

    def test_installer_defaults_and_backward_compatible_aliases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-install-targets-") as temp:
            project = Path(temp)
            cases = (
                ((), project / ".agents" / "skills" / "oneshot"),
                (("--target", "agents"), project / ".agents" / "skills" / "oneshot"),
                (("--target", "claude"), project / ".claude" / "skills" / "oneshot"),
                (("--target", "openclaw"), project / "skills" / "oneshot"),
            )
            for arguments, expected in cases:
                with self.subTest(arguments=arguments):
                    result = self.run_command(
                        "scripts/install_skill.py",
                        "--scope",
                        "project",
                        "--project-root",
                        str(project),
                        "--skip-validation",
                        "--dry-run",
                        *arguments,
                    )
                    self.assertIn(str(expected), result.stdout)

    def test_repository_scripts_remain_executable(self) -> None:
        executable_paths = (
            ROOT / "scripts" / "install_skill.py",
            ROOT / "scripts" / "package_release.py",
            ROOT / "skills" / "oneshot" / "scripts" / "audit_prompt.py",
            ROOT / "tests" / "test_repository.py",
        )
        for path in executable_paths:
            with self.subTest(path=path):
                self.assertNotEqual(path.stat().st_mode & 0o111, 0)


if __name__ == "__main__":
    unittest.main()
