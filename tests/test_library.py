from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def load_validator() -> ModuleType:
    path = ROOT / "scripts" / "validate_library.py"
    spec = importlib.util.spec_from_file_location("oneshot_test_library", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")


def seed_library(target: Path) -> None:
    """Copy the checked-in library into a temp directory for mutation."""
    for source in sorted((ROOT / "library").rglob("*")):
        if not source.is_file():
            continue
        destination = target / source.relative_to(ROOT / "library")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())


class ValidatorModuleTests(unittest.TestCase):
    def test_safe_relative_rejects_traversal_and_absolute(self) -> None:
        unsafe = (
            "../escape.md",
            "/absolute/path.md",
            "a/../../b.md",
            "C:\\\\windows\\\\path",
            "",
            "..",
        )
        for candidate in unsafe:
            with self.subTest(candidate=candidate):
                self.assertFalse(validator.is_safe_relative(candidate))
        self.assertTrue(validator.is_safe_relative("prompt.md"))
        self.assertTrue(validator.is_safe_relative("evidence/run.log"))

    def test_resolve_inside_blocks_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-lib-") as temp:
            base = Path(temp) / "library"
            base.mkdir()
            with self.assertRaises(validator.LibraryError):
                validator.resolve_inside(base, "../outside.txt")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-lib-") as temp:
            path = Path(temp) / "dup.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(validator.LibraryError):
                validator.load_json(path)

    def test_schema_validator_rejects_unsupported_behavioural_keywords(self) -> None:
        with self.assertRaises(validator.LibraryError):
            validator.SchemaValidator({"type": "object", "minProperties": 1}, "test-schema")

    def test_schema_validator_allows_annotations(self) -> None:
        schema = validator.SchemaValidator(
            {"title": "annotation", "description": "okay", "type": "string"},
            "test-schema",
        )
        self.assertEqual(schema.validate("value"), [])


class SeedLibraryTests(unittest.TestCase):
    def test_checked_in_seed_library_is_valid(self) -> None:
        errors = validator.validate_library(ROOT / "library")
        self.assertEqual(errors, [])

    def test_seed_prompt_and_evaluator_hashes_match_files(self) -> None:
        for manifest_path in sorted((ROOT / "library" / "challenges").glob("*/challenge.json")):
            with self.subTest(manifest=manifest_path.parent.name):
                document = json.loads(manifest_path.read_text(encoding="utf-8"))
                for field in ("prompt", "evaluator"):
                    if field not in document:
                        continue
                    referenced = manifest_path.parent / document[field]["path"]
                    actual = hashlib.sha256(referenced.read_bytes()).hexdigest()
                    self.assertEqual(actual, document[field]["sha256"])


    def test_one_shot_policy_is_fixed_in_seed_manifests(self) -> None:
        for manifest_path in sorted((ROOT / "library" / "challenges").glob("*/challenge.json")):
            with self.subTest(manifest=manifest_path.parent.name):
                document = json.loads(manifest_path.read_text(encoding="utf-8"))
                policy = document["one_shot_policy"]
                self.assertFalse(policy["human_follow_up"])
                self.assertTrue(policy["internal_iteration"])


@unittest.skipUnless(
    shutil.which("node") and shutil.which("chromium") and shutil.which("bwrap"),
    "Node, Chromium, and bubblewrap are required for Windline evaluator tests",
)
class WindlineEvaluatorTests(unittest.TestCase):
    def probe_html(
        self,
        *,
        extra_script: str = "",
        viewport: bool = True,
        width: int = 360,
        steering: bool = True,
        rightward_motion: bool = True,
        snapshot_shape: str = "standard",
        restart_to_flying: bool = False,
        state_dependent_restart: bool = False,
    ) -> str:
        viewport_meta = '<meta name="viewport" content="width=device-width,initial-scale=1">' if viewport else ""
        up_action = "state.glider.vy -= .2; state.glider.pitch -= .2;" if steering else ""
        down_action = "state.glider.vy += .2; state.glider.pitch += .2;" if steering else ""
        motion = "state.glider.x = Math.min(.95, state.glider.x + .002);" if rightward_motion else ""
        restart_action = "state = structuredClone(initial);" + (" state.phase = 'flying';" if restart_to_flying else "")
        restart_hidden = " hidden" if state_dependent_restart else ""
        restart_visibility = "document.querySelector('#restart').hidden = state.phase !== 'crashed';" if state_dependent_restart else ""
        if snapshot_shape == "alternate":
            chimes = "chimes:{first:{x:.3,y:.5,collected:false},second:{x:.5,y:.5,collected:false},third:{x:.7,y:.5,collected:false}}"
            thermals = "thermals:{left:{x:.2,width:.1,strength:.5},right:{x:.6,width:.1,strength:.5}}"
            rooftop = "rooftop_pad:[.8,.7,.15,.1]"
        else:
            chimes = "chimes:[{x:.3,y:.5,hit:false},{x:.5,y:.5,hit:false},{x:.7,y:.5,hit:false}]"
            thermals = "thermals:[{x:.2,y:.2,width:.1,height:.5},{x:.6,y:.2,width:.1,height:.5}]"
            rooftop = "rooftop:{x:.8,y:.7,width:.15,height:.1}"
        return f'''<!doctype html><html><head><meta charset="utf-8">{viewport_meta}
<title>Windline probe</title><style>html,body{{margin:0}}main{{width:{width}px;height:240px}}</style></head>
<body><main><button>Start</button><button id="restart"{restart_hidden}>Restart</button><button>Help</button>
<p>Enter starts. Arrow Up/Down or W/S steers. R restarts. P pauses.</p><output id="telemetry"></output></main>
<script>
const initial = {{schema:'oneshot.windline/v1',phase:'start',paused:false,next_chime:0,
  glider:{{x:.1,y:.5,vx:.05,vy:0,pitch:0}},
  {chimes},
  {thermals},
  {rooftop}}};
let state = structuredClone(initial);
setInterval(() => {{
  if (state.phase === 'flying' && !state.paused) {{ {motion} }}
  {restart_visibility}
  document.querySelector('#telemetry').textContent = `${{state.phase}} ${{state.glider.x.toFixed(4)}} ${{state.glider.y.toFixed(4)}} ${{state.glider.vy.toFixed(4)}}`;
}}, 20);
document.querySelector('#restart').addEventListener('click', () => {{ {restart_action} }});
window.__oneshotSnapshot = () => structuredClone(state);
addEventListener('keydown', (event) => {{
  if (event.code === 'Enter' && state.phase === 'start') state.phase = 'flying';
  if (event.code === 'ArrowUp') {{ {up_action} }}
  if (event.code === 'ArrowDown') {{ {down_action} state.phase = 'crashed'; }}
  if (event.code === 'KeyP' && state.phase === 'flying') state.paused = !state.paused;
  if (event.code === 'KeyR') {{ {restart_action} }}
}});
{extra_script}
</script></body></html>'''

    def run_probe(self, html: str, sibling: tuple[str, str] | None = None) -> dict:
        with tempfile.TemporaryDirectory(prefix="oneshot-windline-probe-") as temp:
            root = Path(temp)
            artifact = root / "index.html"
            out_dir = root / "evaluation"
            artifact.write_text(html, encoding="utf-8")
            if sibling:
                (root / sibling[0]).write_text(sibling[1], encoding="utf-8")
            result = subprocess.run(
                [
                    "node",
                    str(ROOT / "library/challenges/windline/evaluator/evaluate.mjs"),
                    str(artifact),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=90,
                check=False,
            )
            self.assertIn(result.returncode, (0, 1), msg=result.stderr)
            return json.loads((out_dir / "evaluation.json").read_text(encoding="utf-8"))

    def item(self, report: dict, item_id: str) -> dict:
        return next(
            item
            for band in report["bands"].values()
            for item in band["items"]
            if item["id"] == item_id
        )

    def outcome(self, report: dict, criterion_id: str) -> dict:
        return next(item for item in report["criterion_outcomes"] if item["id"] == criterion_id)

    def test_delayed_network_is_blocked_before_egress_and_scores_consistently(self) -> None:
        requests_received = 0

        class ProbeHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self) -> None:
                nonlocal requests_received
                requests_received += 1
                handler_self.send_response(200)
                handler_self.end_headers()

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(thread.join, 2)
        probe_url = f"http://127.0.0.1:{server.server_port}/late"
        report = self.run_probe(self.probe_html(
            extra_script=f"setTimeout(() => fetch({json.dumps(probe_url)}).catch(() => {{}}), 1000);"
        ))
        self.assertEqual(requests_received, 0)
        self.assertIn(probe_url, report["observations"]["unexpected_network_requests"])
        self.assertFalse(self.item(report, "offline-boot")["passed"])
        self.assertFalse(self.outcome(report, "offline-boot")["passed"])
        self.assertIn("offline-boot", report["critical_failures"])
        self.assertLessEqual(report["automated_score"], 60)
        self.assertTrue(report["evaluator"]["isolation"]["network_namespace"])

    def test_sibling_file_is_not_staged_and_is_blocked_and_recorded(self) -> None:
        report = self.run_probe(
            self.probe_html(extra_script="const s=document.createElement('script');s.src='./helper.js';document.head.append(s);"),
            sibling=("helper.js", "window.siblingLoaded = true;\n"),
        )
        self.assertEqual(report["evaluator"]["isolation"]["staging_files"], ["index.html"])
        self.assertIn("file:///artifact/helper.js", report["observations"]["unexpected_network_requests"])
        self.assertFalse(self.item(report, "offline-boot")["passed"])

    def test_ignored_steering_and_constant_x_fail_critical_keyboard_item(self) -> None:
        report = self.run_probe(self.probe_html(steering=False, rightward_motion=False))
        steering = self.item(report, "keyboard-steering")
        self.assertFalse(steering["passed"])
        self.assertIn("rightward progress=false", steering["detail"])
        self.assertIn("keyboard-steering", report["critical_failures"])
        self.assertFalse(self.outcome(report, "start-and-steering")["passed"])

    def test_900px_layout_without_viewport_metadata_fails_mobile_fit(self) -> None:
        report = self.run_probe(self.probe_html(viewport=False, width=900))
        self.assertFalse(self.item(report, "mobile-fit")["passed"])
        self.assertFalse(self.outcome(report, "keyboard-and-responsive")["passed"])

    def test_contract_allows_alternate_shapes_and_immediate_flying_restart(self) -> None:
        report = self.run_probe(self.probe_html(
            snapshot_shape="alternate",
            restart_to_flying=True,
            state_dependent_restart=True,
        ))
        self.assertEqual(report["automated_score"], 70)
        self.assertEqual(report["critical_failures"], [])
        self.assertEqual(report["evaluator"]["isolation"]["staging_files"], ["index.html"])
        self.assertTrue(self.item(report, "crash-restart")["passed"])
        self.assertTrue(self.item(report, "controls-and-buttons")["passed"])

    def test_compliant_probe_preserves_70_automated_30_manual_arithmetic(self) -> None:
        html = self.probe_html(extra_script="console.warn('benign evaluator probe warning');")
        report = self.run_probe(html.replace("<!doctype html>", "", 1))
        self.assertEqual(report["automated_score"], 70)
        self.assertEqual(report["manual_points_available"], 30)
        self.assertEqual(sum(band["max"] for band in report["bands"].values()), 100)
        self.assertEqual(report["critical_failures"], [])


def set_prompt_content(root: Path, challenge: str, text: str) -> None:
    prompt = root / "challenges" / challenge / "prompt.md"
    prompt.write_text(text, encoding="utf-8", newline="\n")


class MutatedLibraryTests(unittest.TestCase):
    """Negative cases built by mutating a copy of the seed library."""

    def mutate(self, name: str, mutator) -> tuple[Path, list[str]]:
        temp = tempfile.TemporaryDirectory(prefix=f"oneshot-lib-{name}-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        seed_library(root)
        mutator(root)
        return root, validator.validate_library(root)

    def edit_manifest(self, root: Path, relative: str, mutator) -> None:
        path = root / relative
        document = json.loads(path.read_text(encoding="utf-8"))
        mutator(document)
        write_json(path, document)

    def test_tampered_prompt_hash_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            set_prompt_content(root, "loopback", "# Loopback\nTampered.\n")

        _, errors = self.mutate("hash", mutate)
        self.assertTrue(any("sha256 mismatch" in error for error in errors), msg=errors)

    def test_unsafe_prompt_path_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc["prompt"].update(path="sub/../../../secrets.md"),
            )

        _, errors = self.mutate("path", mutate)
        self.assertTrue(any("unsafe prompt path" in error for error in errors), msg=errors)

    def test_traversal_prompt_path_fails_schema_pattern(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc["prompt"].update(path="../../secrets.md"),
            )

        _, errors = self.mutate("path-pattern", mutate)
        self.assertTrue(
            any("does not match pattern" in error for error in errors), msg=errors
        )

    def test_missing_prompt_file_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "challenges" / "loopback" / "prompt.md").unlink()

        _, errors = self.mutate("missing-prompt", mutate)
        self.assertTrue(any("prompt file not found" in error for error in errors), msg=errors)

    def test_evaluator_hash_mismatch_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            evaluator = root / "challenges" / "windline" / "evaluator" / "evaluate.mjs"
            evaluator.write_text("// changed\n", encoding="utf-8")

        _, errors = self.mutate("evaluator-hash", mutate)
        self.assertTrue(any("evaluator sha256 mismatch" in error for error in errors), msg=errors)

    def test_active_core_challenge_requires_evaluator(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/windline/challenge.json",
                lambda doc: (doc.update(status="active"), doc.pop("evaluator")),
            )

        _, errors = self.mutate("active-core-evaluator", mutate)
        self.assertTrue(any("active core challenge requires an evaluator" in error for error in errors), msg=errors)

    def test_compact_prompt_word_cap_is_enforced(self) -> None:
        def mutate(root: Path) -> None:
            prompt = root / "challenges" / "windline" / "prompt.md"
            prompt.write_text(" ".join(["word"] * 351) + "\n", encoding="utf-8")
            self.edit_manifest(
                root,
                "challenges/windline/challenge.json",
                lambda doc: doc["prompt"].update(sha256=hashlib.sha256(prompt.read_bytes()).hexdigest()),
            )

        _, errors = self.mutate("compact-word-cap", mutate)
        self.assertTrue(any("compact prompt has 351 words" in error for error in errors), msg=errors)

    def test_external_challenge_requires_https_source(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: (doc.update(origin="external"), doc["provenance"].pop("source_url", None)),
            )

        _, errors = self.mutate("external-source", mutate)
        self.assertTrue(any("requires provenance.source_url" in error for error in errors), msg=errors)

    def test_unknown_field_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc.update(runs_count=12),
            )

        _, errors = self.mutate("unknown-field", mutate)
        self.assertTrue(any("unknown field" in error for error in errors), msg=errors)

    def test_wrong_category_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc.update(category="fps-shooter"),
            )

        _, errors = self.mutate("category", mutate)
        self.assertTrue(any("must be one of" in error for error in errors), msg=errors)

    def test_drifting_one_shot_policy_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc["one_shot_policy"].update(human_follow_up=True),
            )

        _, errors = self.mutate("policy", mutate)
        self.assertTrue(any("must equal False" in error for error in errors), msg=errors)

    def make_result_fixture(self, root: Path) -> dict:
        challenge = json.loads(
            (root / "challenges" / "loopback" / "challenge.json").read_text(encoding="utf-8")
        )
        result_dir = root / "results" / "sample-run"
        result_dir.mkdir(parents=True, exist_ok=True)
        artifact = result_dir / "index.html"
        artifact.write_text("<!doctype html><title>loopback</title>\n", encoding="utf-8")
        readme = result_dir / "README.md"
        readme.write_text("# Result\n\nRun notes.\n", encoding="utf-8")
        transcript = result_dir / "run-transcript.log"
        transcript.write_text("executed loopback v1.0.0\n", encoding="utf-8")
        screenshot = result_dir / "review.png"
        screenshot.write_bytes(bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000d4944415408d763f8cfc0f01f00050001ff89993d1d0000000049454e44ae426082"
        ))
        instructions = result_dir / "reproduce.md"
        instructions.write_text("# Reproduce\n\nRun the same prompt.\n", encoding="utf-8")

        def digest(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        return {
            "schema": "oneshot.result/v2",
            "id": "sample-run",
            "challenge": {"id": challenge["id"], "version": challenge["version"]},
            "run_class": "canonical",
            "run_lane": "agentic-self-review",
            "executed_at": "2026-08-21",
            "executor": {
                "model": {"name": "example-model", "version": "2026-08-01", "snapshot_id": None},
                "agent": {"name": "example-agent", "version": "1.0.0", "profile": None},
                "host": {"name": "example-host", "version": "2.0.0"},
            },
            "status": "verified",
            "claim": {"passed": True, "summary": "All five verification checks passed."},
            "artifacts": [
                {
                    "path": "index.html",
                    "sha256": digest(artifact),
                    "kind": "html",
                    "description": "The game build.",
                },
                {
                    "path": "README.md",
                    "sha256": digest(readme),
                    "kind": "markdown",
                    "description": "Run notes.",
                },
            ],
            "evidence": [
                {
                    "id": "ev-transcript",
                    "kind": "transcript",
                    "location": "run-transcript.log",
                    "sha256": digest(transcript),
                    "description": "Full run transcript.",
                },
                {"id": "ev-log", "kind": "log", "location": "run-transcript.log", "sha256": digest(transcript), "description": "Run log."},
                {"id": "ev-screenshot", "kind": "screenshot", "location": "review.png", "sha256": digest(screenshot), "description": "Review capture."},
            ],
            "criterion_outcomes": [
                {"id": "boot-offline", "passed": True, "evidence_refs": ["ev-log", "ev-screenshot"], "notes": "Booted offline."},
                {"id": "core-loop", "passed": True, "evidence_refs": ["ev-transcript", "ev-screenshot"], "notes": "Core loop passed."},
                {"id": "levels-solvable", "passed": True, "evidence_refs": ["ev-log"], "notes": "Levels were solved."},
                {"id": "persistence-recovery", "passed": True, "evidence_refs": ["ev-screenshot"], "notes": "Persistence recovered."},
                {"id": "keyboard-complete", "passed": True, "evidence_refs": ["ev-transcript"], "notes": "Keyboard run completed."},
            ],
            "reproducibility": {
                "status": "reproducible",
                "instructions_path": "reproduce.md",
                "notes": "Independent rerun reproduced the claim.",
            },
            "budget_actual": {"wall_clock_minutes": 64, "output_files": 2, "notes": "Within budget."},
            "prompt_echo": {"sha256": challenge["prompt"]["sha256"]},
            "maintainer_review": {
                "reviewer_id": "oneshot-maintainers",
                "reviewed_at": "2026-08-21",
                "decision": "verified",
                "notes": "Reviewed the listed evidence and artifact shape for this fixture.",
            },
        }

    def test_valid_result_fixture_passes(self) -> None:
        def mutate(root: Path) -> None:
            write_json(root / "results" / "sample-run" / "result.json", self.make_result_fixture(root))

        _, errors = self.mutate("result-ok", mutate)
        self.assertEqual(errors, [])

    def test_passing_claim_without_evidence_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"] = []
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("no-evidence", mutate)
        self.assertTrue(any("no evidence is provided" in error for error in errors), msg=errors)

    def test_verified_status_requires_reproduction(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["reproducibility"]["status"] = "untested"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("verified-untested", mutate)
        self.assertTrue(
            any("requires reproduction evidence" in error for error in errors), msg=errors
        )

    def test_result_referencing_unknown_challenge_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["challenge"]["id"] = "nonexistent-challenge"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("unknown-challenge", mutate)
        self.assertTrue(any("references unknown challenge" in error for error in errors), msg=errors)

    def test_stale_prompt_echo_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["prompt_echo"]["sha256"] = "0" * 64
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("stale-echo", mutate)
        self.assertTrue(any("prompt_echo sha256" in error for error in errors), msg=errors)

    def test_artifact_hash_mismatch_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["artifacts"][0]["sha256"] = "1" * 64
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("artifact-hash", mutate)
        self.assertTrue(any("artifact sha256 mismatch" in error for error in errors), msg=errors)

    def test_missing_evidence_file_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"][0]["location"] = "does-not-exist.log"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("missing-evidence", mutate)
        self.assertTrue(any("evidence[0] file missing" in error for error in errors), msg=errors)

    def test_evidence_hash_mismatch_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"][0]["sha256"] = "1" * 64
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("evidence-hash", mutate)
        self.assertTrue(any("evidence[0] sha256 mismatch" in error for error in errors), msg=errors)

    def test_plain_http_evidence_link_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"].append(
                {
                    "id": "ev-http",
                    "kind": "external-link",
                    "location": "http://insecure.example/run",
                    "sha256": None,
                    "description": "Insecure link.",
                }
            )
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("http-evidence", mutate)
        self.assertTrue(any("must use HTTPS" in error for error in errors), msg=errors)

    def test_prompt_echo_is_required(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture.pop("prompt_echo")
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("required-echo", mutate)
        self.assertTrue(any("prompt_echo" in error and "required" in error for error in errors), msg=errors)

    def test_run_lane_is_required(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture.pop("run_lane")
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("required-run-lane", mutate)
        self.assertTrue(any("run_lane" in error and "required" in error for error in errors), msg=errors)

    def test_missing_criterion_outcome_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["criterion_outcomes"].pop()
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("criterion-missing", mutate)
        self.assertTrue(any("missing criterion outcomes" in error for error in errors), msg=errors)

    def test_criterion_notes_are_required_for_site_rendering(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["criterion_outcomes"][0].pop("notes")
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("criterion-notes", mutate)
        self.assertTrue(any("notes" in error and "required" in error for error in errors), msg=errors)

    def test_reproducibility_instructions_and_notes_are_required(self) -> None:
        for missing in ("instructions_path", "notes"):
            with self.subTest(missing=missing):
                def mutate(root: Path, field: str = missing) -> None:
                    fixture = self.make_result_fixture(root)
                    fixture["reproducibility"].pop(field)
                    write_json(root / "results" / "sample-run" / "result.json", fixture)

                _, errors = self.mutate(f"reproducibility-{missing}", mutate)
                self.assertTrue(any(missing in error and "required" in error for error in errors), msg=errors)

    def test_criterion_evidence_kind_is_required(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["criterion_outcomes"][0]["evidence_refs"] = ["ev-transcript"]
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("criterion-evidence-kind", mutate)
        self.assertTrue(any("missing required evidence kinds" in error for error in errors), msg=errors)

    def test_screenshot_evidence_requires_image_extension_and_signature(self) -> None:
        def wrong_extension(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"][2]["location"] = "run-transcript.log"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, extension_errors = self.mutate("screenshot-extension", wrong_extension)
        self.assertTrue(
            any("screenshot must use one of" in error for error in extension_errors),
            msg=extension_errors,
        )

        def fake_image(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            (root / "results" / "sample-run" / "review.png").write_text(
                "not an image\n", encoding="utf-8"
            )
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, signature_errors = self.mutate("screenshot-signature", fake_image)
        self.assertTrue(
            any("screenshot content does not match" in error for error in signature_errors),
            msg=signature_errors,
        )

    def test_typed_evidence_cannot_be_replaced_by_arbitrary_url(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["evidence"][0]["location"] = "https://example.invalid/transcript"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("typed-evidence-url", mutate)
        self.assertTrue(any("must use a checked-in local file" in error for error in errors), msg=errors)

    def test_passing_claim_requires_all_criteria_to_pass(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["criterion_outcomes"][0]["passed"] = False
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("criterion-fail", mutate)
        self.assertTrue(any("every challenge criterion to pass" in error for error in errors), msg=errors)

    def test_required_artifact_must_be_present_once_with_matching_kind(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture["artifacts"] = [fixture["artifacts"][0], {**fixture["artifacts"][0], "kind": "svg"}]
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("required-artifact", mutate)
        self.assertTrue(any("duplicate result artifact path" in error for error in errors), msg=errors)
        self.assertTrue(any("kind mismatch" in error for error in errors), msg=errors)

    def test_symlink_anywhere_under_library_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            target = root / "challenges" / "loopback" / "prompt.md"
            link = root / "challenges" / "loopback" / "nested-link.md"
            os.symlink(target, link)

        temp = tempfile.TemporaryDirectory(prefix="oneshot-lib-symlink-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        seed_library(root)
        mutate(root)
        with self.assertRaises(validator.LibraryError) as context:
            validator.validate_library(root)
        self.assertIn("symlink is not allowed", str(context.exception))

    def test_symlinked_challenge_and_result_directories_are_rejected(self) -> None:
        for name, parent, target in (
            ("challenge-dir", "challenges", "loopback"),
            ("result-dir", "results", "../challenges/loopback"),
        ):
            with self.subTest(name=name):
                temp = tempfile.TemporaryDirectory(prefix="oneshot-lib-symlink-dir-")
                self.addCleanup(temp.cleanup)
                root = Path(temp.name)
                seed_library(root)
                os.symlink(target, root / parent / name)
                with self.assertRaises(validator.LibraryError) as context:
                    validator.validate_library(root)
                self.assertIn("symlink is not allowed", str(context.exception))

    def test_malformed_challenge_and_result_directories_are_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "challenges" / "rogue").mkdir()
            (root / "results" / "rogue").mkdir()

        _, errors = self.mutate("malformed-directories", mutate)
        self.assertTrue(any("challenge directory is missing challenge.json" in error for error in errors), msg=errors)
        self.assertTrue(any("result directory is missing result.json" in error for error in errors), msg=errors)

    def test_non_directory_challenge_and_result_entries_are_rejected(self) -> None:
        def mutate(root: Path) -> None:
            (root / "challenges" / "rogue").write_text("ignored?\n", encoding="utf-8")
            (root / "results" / "rogue").write_text("ignored?\n", encoding="utf-8")

        _, errors = self.mutate("malformed-entries", mutate)
        self.assertTrue(any("challenge entry must be a directory" in error for error in errors), msg=errors)
        self.assertTrue(any("result entry must be a directory" in error for error in errors), msg=errors)

    def test_non_regular_result_manifests_are_rejected(self) -> None:
        for kind in ("directory", "fifo"):
            with self.subTest(kind=kind):
                temp = tempfile.TemporaryDirectory(prefix=f"oneshot-lib-result-{kind}-")
                self.addCleanup(temp.cleanup)
                root = Path(temp.name)
                seed_library(root)
                manifest = root / "results" / kind / "result.json"
                manifest.parent.mkdir(parents=True)
                if kind == "directory":
                    manifest.mkdir()
                else:
                    os.mkfifo(manifest)
                errors = validator.validate_library(root)
                self.assertTrue(
                    any("result.json must be a regular file" in error for error in errors),
                    msg=errors,
                )

    def test_historical_challenge_version_can_back_existing_result(self) -> None:
        def mutate(root: Path) -> None:
            current_dir = root / "challenges" / "loopback"
            archive_dir = current_dir / "versions" / "0.9.0"
            archive_dir.mkdir(parents=True)
            archived = json.loads((current_dir / "challenge.json").read_text(encoding="utf-8"))
            archived["version"] = "0.9.0"
            (archive_dir / "prompt.md").write_bytes((current_dir / "prompt.md").read_bytes())
            write_json(archive_dir / "challenge.json", archived)

            fixture = self.make_result_fixture(root)
            fixture["challenge"]["version"] = "0.9.0"
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("historical-version", mutate)
        self.assertEqual(errors, [])

    def test_archives_and_executable_file_modes_are_rejected(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            result_dir = root / "results" / "sample-run"
            (result_dir / "payload.zip").write_bytes(b"not really a zip")
            executable = result_dir / "reproduce.md"
            executable.chmod(0o755)
            write_json(result_dir / "result.json", fixture)

        _, errors = self.mutate("forbidden-payloads", mutate)
        self.assertTrue(any("archive or executable payload" in error for error in errors), msg=errors)
        self.assertTrue(any("executable file mode" in error for error in errors), msg=errors)

    def test_fake_spdx_identifier_is_rejected(self) -> None:
        def mutate(root: Path) -> None:
            self.edit_manifest(
                root,
                "challenges/loopback/challenge.json",
                lambda doc: doc["provenance"]["license"].update(spdx="MIT-FAKE"),
            )

        _, errors = self.mutate("fake-spdx", mutate)
        self.assertTrue(any("SPDX allowlist" in error or "must be one of" in error for error in errors), msg=errors)

    def test_verified_result_requires_maintainer_review(self) -> None:
        def mutate(root: Path) -> None:
            fixture = self.make_result_fixture(root)
            fixture.pop("maintainer_review")
            write_json(root / "results" / "sample-run" / "result.json", fixture)

        _, errors = self.mutate("review-attestation", mutate)
        self.assertTrue(any("requires maintainer_review" in error for error in errors), msg=errors)


class SiteLoaderContractTests(unittest.TestCase):
    def test_validator_interpreter_cannot_be_overridden_by_python_environment_variable(self) -> None:
        source = (ROOT / "site" / "src" / "lib" / "library.ts").read_text(encoding="utf-8")
        self.assertNotIn("process.env.PYTHON", source)
        self.assertIn('execFileSync(\n      "python3",', source)


class CommandLineTests(unittest.TestCase):
    def run_validator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PYTHON, "scripts/validate_library.py", *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_accepts_repository_library(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("OK: challenge library is valid", result.stdout)

    def test_cli_reports_deterministic_errors_for_broken_library(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-lib-cli-") as temp:
            root = Path(temp)
            seed_library(root)
            set_prompt_content(root, "loopback", "changed\n")
            first = self.run_validator("--library-dir", str(root))
            second = self.run_validator("--library-dir", str(root))
            self.assertEqual(first.returncode, 1)
            self.assertEqual(first.stdout + first.stderr, second.stdout + second.stderr)
            self.assertIn("sha256 mismatch", first.stderr)


class TaxonomyAndPlayableContractTests(unittest.TestCase):
    def test_every_current_challenge_has_structured_taxonomy(self) -> None:
        expected_families = {"playable", "build", "precision", "repair", "edge-case"}
        standardized = {
            "planning", "implementation", "interaction-design", "state-management",
            "algorithmic-reasoning", "visual-judgment", "precision", "debugging",
            "verification", "accessibility", "offline-delivery",
        }
        manifests = sorted((ROOT / "library" / "challenges").glob("*/challenge.json"))
        self.assertGreaterEqual(len(manifests), 4)
        for manifest_path in manifests:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            with self.subTest(manifest=manifest_path.parent.name):
                self.assertIn(document["family"], expected_families)
                self.assertGreaterEqual(len(document["benchmark_question"]), 16)
                self.assertTrue(document["capability_dimensions"])
                self.assertTrue(set(document["capability_dimensions"]) <= standardized)
                self.assertNotEqual(document["family"], document["category"])

    def test_missing_taxonomy_is_rejected_by_schema(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-taxonomy-") as temp:
            root = Path(temp)
            seed_library(root)
            path = root / "challenges" / "loopback" / "challenge.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document.pop("benchmark_question")
            write_json(path, document)
            errors = validator.validate_library(root)
            self.assertTrue(any("benchmark_question" in error and "required" in error for error in errors), msg=errors)

    def test_duplicate_capability_dimensions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oneshot-taxonomy-duplicate-") as temp:
            root = Path(temp)
            seed_library(root)
            path = root / "challenges" / "loopback" / "challenge.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["capability_dimensions"].append(document["capability_dimensions"][0])
            write_json(path, document)
            errors = validator.validate_library(root)
            self.assertTrue(any("duplicate capability dimensions" in error for error in errors), msg=errors)

    def test_html_artifacts_are_download_only(self) -> None:
        component = ROOT / "site" / "src" / "components" / "SafePlayable.astro"
        page = (ROOT / "site" / "src" / "pages" / "results" / "[id].astro").read_text(encoding="utf-8")
        loader = (ROOT / "site" / "src" / "lib" / "library.ts").read_text(encoding="utf-8")
        self.assertFalse(component.exists())
        self.assertIn("Download raw artifact", page)
        self.assertIn("download_url", loader)
        for source in (page, loader):
            self.assertNotIn("SafePlayable", source)
            self.assertNotIn("playable_html_base64", source)
            self.assertNotIn("data-playable-launch", source)


if __name__ == "__main__":
    unittest.main()
