#!/usr/bin/env python3
"""Validate the OneShot challenge library: schemas, hashes, paths, integrity.

Dependency-free and deterministic. Validates challenge and result manifests
against a documented subset of JSON Schema (draft 2020-12), then applies
semantic rules that a schema cannot express:

- prompt/artifact/evidence paths are safe relative paths inside library/
- prompt/evaluator SHA-256 values match actual file bytes
- active core challenges have public evaluators and tier prompt caps
- external entries carry an HTTPS source URL
- results reference existing challenges at existing versions and comparison lanes
- prompt_echo.sha256 matches the referenced challenge's current prompt hash
- passing claims and verified statuses require complete typed local evidence
- evidence extensions/content signatures agree with declared kinds
- artifact hashes match bytes on disk; archives/executable modes are rejected
- historical challenge versions remain addressable by exact result references

Supported schema keywords: type (incl. lists), const, enum, pattern,
minLength/maxLength, minimum/maximum, properties, required,
additionalProperties:false, items, minItems/maxItems, format (uri, date),
$defs/$ref. Anything else fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIBRARY_DIR = ROOT / "library"

SCHEMA_FILES = {
    "oneshot.challenge/v1": "challenge-v1.schema.json",
    "oneshot.result/v1": "result-v1.schema.json",
    "oneshot.result/v2": "result-v2.schema.json",
}
MAINTAINERS_FILE = "maintainers.json"
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
URI_RE = re.compile(r"^https?://[^\s]+$")
SPDX_LICENSE_ALLOWLIST = frozenset(
    {
        "AGPL-3.0-only", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
        "CC0-1.0", "GPL-2.0-only", "GPL-3.0-only", "ISC", "LGPL-2.1-only",
        "LGPL-3.0-only", "MIT", "MPL-2.0", "Unlicense",
    }
)
NO_LICENSE_SIGNALS = ("no license", "none declared", "not declared", "unlicensed")
ARTIFACT_EXTENSIONS = {
    "html": frozenset({".html", ".htm"}),
    "svg": frozenset({".svg"}),
    "png": frozenset({".png"}),
    "markdown": frozenset({".md", ".markdown"}),
    "log": frozenset({".log", ".txt"}),
}
EVIDENCE_EXTENSIONS = {
    "transcript": frozenset({".jsonl", ".log", ".md", ".txt"}),
    "log": frozenset({".json", ".jsonl", ".log", ".txt"}),
    "screenshot": frozenset({".jpeg", ".jpg", ".png", ".webp"}),
    "checksum-file": frozenset({".sha256", ".sha512", ".txt"}),
    "reproduction-script": frozenset({".js", ".md", ".mjs", ".py", ".sh", ".ts"}),
}
TEXT_EVIDENCE_KINDS = frozenset({
    "transcript", "log", "checksum-file", "reproduction-script",
})
FORBIDDEN_RESULT_SUFFIXES = frozenset({
    ".7z", ".apk", ".appimage", ".bz2", ".com", ".deb", ".dll", ".dmg",
    ".exe", ".gz", ".iso", ".msi", ".rar", ".rpm", ".so", ".tar",
    ".tgz", ".xz", ".zip",
})

# Keep this dependency-free validator fail-closed: annotations are accepted,
# but an unknown behavioural keyword must not silently weaken a schema.
SUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "$defs", "$ref", "type", "const", "enum", "pattern", "minLength",
    "maxLength", "minimum", "maximum", "properties", "required",
    "additionalProperties", "items", "minItems", "maxItems", "format",
})
SCHEMA_ANNOTATIONS = frozenset({
    "$comment", "$id", "$schema", "contentEncoding", "contentMediaType",
    "contentSchema", "default", "deprecated", "description", "examples",
    "readOnly", "title", "writeOnly",
})


class LibraryError(Exception):
    pass


# ---------------------------------------------------------------------------
# JSON loading with duplicate-key detection


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: dict = {}
    for key, value in pairs:
        if key in seen:
            raise LibraryError(f"duplicate JSON key: {key}")
        seen[key] = value
    return seen


def _require_regular_file(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise LibraryError(f"cannot stat {path}: {exc}") from exc
    if stat.S_ISLNK(mode):
        raise LibraryError(f"symlink is not allowed under library/: {path}")
    if not stat.S_ISREG(mode):
        raise LibraryError(f"not a regular file: {path}")


def load_json(path: Path) -> object:
    _require_regular_file(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LibraryError(f"cannot read {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise LibraryError(f"{path} is not valid UTF-8: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise LibraryError(f"{path} is not valid JSON: {exc}") from exc
    except LibraryError as exc:
        raise LibraryError(f"{path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Schema-subset validator


class SchemaValidator:
    """Validates documents against the documented keyword subset."""

    def __init__(self, schema: object, source: str) -> None:
        if not isinstance(schema, dict):
            raise LibraryError(f"{source}: schema root must be an object")
        self.source = source
        self.root = schema
        self.definitions = schema.get("$defs", {})
        if not isinstance(self.definitions, dict):
            raise LibraryError(f"{source}: $defs must be an object")
        self._audit_schema(self.root, "")

    def _audit_schema(self, rules: object, where: str) -> None:
        if not isinstance(rules, dict):
            raise LibraryError(f"{self.source}: schema fragment must be an object")
        unknown = sorted(set(rules) - SUPPORTED_SCHEMA_KEYWORDS - SCHEMA_ANNOTATIONS)
        if unknown:
            raise LibraryError(
                f"{self.source}: unsupported schema keyword(s) at {where or 'root'}: "
                + ", ".join(unknown)
            )
        if "$ref" in rules:
            siblings = sorted(set(rules) - SCHEMA_ANNOTATIONS - {"$ref"})
            if siblings:
                raise LibraryError(
                    f"{self.source}: unsupported $ref sibling keyword(s) at "
                    f"{where or 'root'}: {', '.join(siblings)}"
                )
        if "$defs" in rules:
            definitions = rules["$defs"]
            if not isinstance(definitions, dict):
                raise LibraryError(f"{self.source}: $defs must be an object")
            for name, child in definitions.items():
                self._audit_schema(child, f"{where}.$defs.{name}")
        if "properties" in rules:
            properties = rules["properties"]
            if not isinstance(properties, dict):
                raise LibraryError(f"{self.source}: properties must be an object")
            for name, child in properties.items():
                self._audit_schema(child, f"{where}.properties.{name}")
        if "items" in rules:
            self._audit_schema(rules["items"], f"{where}.items")

    def validate(self, document: object) -> list[str]:
        errors: list[str] = []
        self._check(document, self.root, "", errors)
        return errors

    def _resolve_ref(self, ref: object) -> object:
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            raise LibraryError(f"{self.source}: unsupported $ref: {ref!r}")
        name = ref[len("#/$defs/") :]
        if name not in self.definitions:
            raise LibraryError(f"{self.source}: unknown $defs entry: {name}")
        return self.definitions[name]

    def _fail(self, errors: list[str], where: str, message: str) -> None:
        location = where if where else "document root"
        errors.append(f"{location}: {message}")

    def _check_type(self, value: object, expected: str) -> bool:
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected == "null":
            return value is None
        raise LibraryError(f"{self.source}: unsupported type keyword: {expected}")

    def _check(self, value: object, rules: object, where: str, errors: list[str]) -> None:
        if not isinstance(rules, dict):
            raise LibraryError(f"{self.source}: schema fragment must be an object")
        self._audit_schema(rules, where)
        if "$ref" in rules:
            self._check(value, self._resolve_ref(rules["$ref"]), where, errors)
            return

        types = rules.get("type")
        if types is not None:
            allowed = [types] if isinstance(types, str) else types
            if not isinstance(allowed, list) or not allowed:
                raise LibraryError(f"{self.source}: invalid type at {where or 'root'}")
            if not any(self._check_type(value, item) for item in allowed):
                self._fail(errors, where, "expected type " + "|".join(allowed))
                return

        if "const" in rules and value != rules["const"]:
            self._fail(errors, where, f"must equal {rules['const']!r}")
        if "enum" in rules:
            if not isinstance(rules["enum"], list):
                raise LibraryError(f"{self.source}: enum must be a list at {where or 'root'}")
            if value not in rules["enum"]:
                self._fail(errors, where, f"must be one of {rules['enum']!r}")

        if isinstance(value, str):
            self._check_string(value, rules, where, errors)
        elif isinstance(value, int) and not isinstance(value, bool) or isinstance(value, float):
            self._check_number(value, rules, where, errors)
        elif isinstance(value, dict):
            self._check_object(value, rules, where, errors)
        elif isinstance(value, list):
            self._check_array(value, rules, where, errors)

    def _check_string(self, value: str, rules: dict, where: str, errors: list[str]) -> None:
        if "pattern" in rules:
            pattern = rules["pattern"]
            if not isinstance(pattern, str):
                raise LibraryError(f"{self.source}: pattern must be a string at {where or 'root'}")
            if re.search(pattern, value) is None:
                self._fail(errors, where, f"{value!r} does not match pattern {pattern!r}")
        if "minLength" in rules and len(value) < rules["minLength"]:
            self._fail(errors, where, f"shorter than minLength {rules['minLength']}")
        if "maxLength" in rules and len(value) > rules["maxLength"]:
            self._fail(errors, where, f"longer than maxLength {rules['maxLength']}")
        fmt = rules.get("format")
        if fmt == "uri":
            if URI_RE.match(value) is None:
                self._fail(errors, where, f"{value!r} is not a valid http(s) URI")
        elif fmt == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                self._fail(errors, where, f"{value!r} is not an ISO date (YYYY-MM-DD)")
        elif fmt is not None:
            raise LibraryError(f"{self.source}: unsupported format {fmt!r} at {where or 'root'}")

    def _check_number(self, value: object, rules: dict, where: str, errors: list[str]) -> None:
        if "minimum" in rules and value < rules["minimum"]:
            self._fail(errors, where, f"below minimum {rules['minimum']}")
        if "maximum" in rules and value > rules["maximum"]:
            self._fail(errors, where, f"above maximum {rules['maximum']}")

    def _check_object(self, value: dict, rules: dict, where: str, errors: list[str]) -> None:
        properties = rules.get("properties", {})
        if not isinstance(properties, dict):
            raise LibraryError(f"{self.source}: properties must be an object at {where or 'root'}")
        required = rules.get("required", [])
        if not isinstance(required, list) or not all(isinstance(name, str) for name in required):
            raise LibraryError(f"{self.source}: required must be a list of strings at {where or 'root'}")
        for name in required:
            if name not in value:
                self._fail(errors, f"{where}.{name}" if where else name, "is required")
        additional = rules.get("additionalProperties", True)
        if not isinstance(additional, bool):
            raise LibraryError(
                f"{self.source}: additionalProperties must be a boolean at {where or 'root'}"
            )
        for key in value:
            if key in properties:
                child = f"{where}.{key}" if where else key
                self._check(value[key], properties[key], child, errors)
            elif additional is False:
                self._fail(errors, f"{where}.{key}" if where else key, "unknown field")

    def _check_array(self, value: list, rules: dict, where: str, errors: list[str]) -> None:
        if "items" not in rules:
            raise LibraryError(f"{self.source}: array without items schema at {where or 'root'}")
        if "minItems" in rules and len(value) < rules["minItems"]:
            self._fail(errors, where, f"fewer than minItems {rules['minItems']}")
        if "maxItems" in rules and len(value) > rules["maxItems"]:
            self._fail(errors, where, f"more than maxItems {rules['maxItems']}")
        for index, item in enumerate(value):
            self._check(item, rules["items"], f"{where}[{index}]", errors)


# ---------------------------------------------------------------------------
# Path and hash helpers


def is_safe_relative(path_text: str) -> bool:
    if not path_text or path_text.startswith(("/", "\\")):
        return False
    if "\\" in path_text or ":" in path_text:
        return False
    pure = PurePosixPath(path_text)
    if pure.is_absolute():
        return False
    return ".." not in pure.parts and "." not in (pure.parts[0],)


def resolve_inside(base: Path, relative: str) -> Path:
    root = base.absolute()
    candidate = Path(os.path.normpath(str(root / relative))).absolute()
    # Do not call resolve() here: it follows symlinks.  The whole library is
    # scanned before discovery, and this component check also protects callers
    # that use resolve_inside directly.
    current = root
    try:
        parts = candidate.relative_to(root).parts
    except ValueError as exc:
        raise LibraryError(f"path escapes {base.name}/: {relative}") from exc
    for part in parts:
        current = current / part
        try:
            if current.is_symlink():
                raise LibraryError(f"symlink is not allowed under library/: {current}")
        except OSError as exc:
            raise LibraryError(f"cannot inspect {current}: {exc}") from exc
    resolved = candidate
    if root != resolved and root not in resolved.parents:
        raise LibraryError(f"path escapes {base.name}/: {relative}")
    return resolved


def sha256_of(path: Path) -> str:
    _require_regular_file(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_kind_extension(
    path_text: str, kind: str, allowed: dict[str, frozenset[str]]
) -> str | None:
    extensions = allowed.get(kind)
    if extensions is None:
        return None
    suffix = PurePosixPath(path_text).suffix.lower()
    if suffix not in extensions:
        return f"{kind} must use one of {', '.join(sorted(extensions))}, got {path_text!r}"
    return None


def screenshot_signature_is_valid(path: Path) -> bool:
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".png":
        return len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR"
    if suffix in (".jpg", ".jpeg"):
        return len(data) >= 4 and data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")
    if suffix == ".webp":
        return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


def reject_forbidden_result_files(result_dir: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(result_dir.rglob("*")):
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode):
            continue
        relative = path.relative_to(result_dir).as_posix()
        if path.suffix.lower() in FORBIDDEN_RESULT_SUFFIXES:
            errors.append(f"{result_dir}: archive or executable payload is not allowed: {relative}")
        if mode & 0o111:
            errors.append(f"{result_dir}: executable file mode is not allowed: {relative}")
    return errors


# ---------------------------------------------------------------------------
# Manifest discovery and validation


def reject_symlinks(library: Path) -> None:
    """Reject links before any discovery or content read can follow them."""
    try:
        root_mode = library.lstat().st_mode
    except OSError as exc:
        raise LibraryError(f"cannot stat library directory {library}: {exc}") from exc
    if stat.S_ISLNK(root_mode):
        raise LibraryError(f"library directory must not be a symlink: {library}")
    if not stat.S_ISDIR(root_mode):
        raise LibraryError(f"library directory is not a directory: {library}")

    pending = [library]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise LibraryError(f"cannot scan {directory}: {exc}") from exc
        for entry in entries:
            entry_path = Path(entry.path)
            try:
                if entry.is_symlink():
                    raise LibraryError(f"symlink is not allowed under library/: {entry_path}")
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise LibraryError(f"cannot inspect {entry_path}: {exc}") from exc
            if stat.S_ISDIR(mode):
                pending.append(entry_path)


def discover_challenge_manifests(library: Path) -> tuple[list[Path], list[str]]:
    """Find current manifests plus optional historical versions.

    Current: challenges/<id>/challenge.json
    Archive: challenges/<id>/versions/<semver>/challenge.json
    """
    base = library / "challenges"
    try:
        base_mode = base.lstat().st_mode
    except OSError:
        base_mode = 0
    if not stat.S_ISDIR(base_mode) or stat.S_ISLNK(base_mode):
        raise LibraryError(f"missing directory: {base}")
    found: list[Path] = []
    errors: list[str] = []
    for directory_entry in sorted(os.scandir(base), key=lambda entry: entry.name):
        entry_path = Path(directory_entry.path)
        if directory_entry.is_symlink():
            raise LibraryError(f"symlink is not allowed under library/: {entry_path}")
        if not directory_entry.is_dir(follow_symlinks=False):
            errors.append(f"{entry_path}: challenge entry must be a directory")
            continue
        challenge_dir = entry_path
        manifest = challenge_dir / "challenge.json"
        try:
            manifest_mode = manifest.lstat().st_mode
        except FileNotFoundError:
            errors.append(f"{challenge_dir}: challenge directory is missing challenge.json")
            continue
        if stat.S_ISLNK(manifest_mode):
            raise LibraryError(f"symlink is not allowed under library/: {manifest}")
        if stat.S_ISREG(manifest_mode):
            _require_regular_file(manifest)
            found.append(manifest)
        else:
            errors.append(f"{manifest}: challenge.json must be a regular file")

        versions_dir = challenge_dir / "versions"
        if not versions_dir.exists():
            continue
        if versions_dir.is_symlink() or not versions_dir.is_dir():
            errors.append(f"{versions_dir}: versions must be a regular directory")
            continue
        for version_entry in sorted(os.scandir(versions_dir), key=lambda entry: entry.name):
            version_path = Path(version_entry.path)
            if version_entry.is_symlink() or not version_entry.is_dir(follow_symlinks=False):
                errors.append(f"{version_path}: archived version entry must be a directory")
                continue
            archived_manifest = version_path / "challenge.json"
            try:
                archived_mode = archived_manifest.lstat().st_mode
            except FileNotFoundError:
                errors.append(f"{version_path}: archived version is missing challenge.json")
                continue
            if not stat.S_ISREG(archived_mode) or stat.S_ISLNK(archived_mode):
                errors.append(f"{archived_manifest}: challenge.json must be a regular file")
                continue
            _require_regular_file(archived_manifest)
            found.append(archived_manifest)
    if not found:
        raise LibraryError(f"no challenge.json manifests under {base}")
    return found, errors


def validate_schema_instance(library: Path, manifest_path: Path, document: object) -> list[str]:
    if not isinstance(document, dict):
        return [f"{manifest_path}: manifest root must be an object"]
    schema_name = document.get("schema")
    if schema_name not in SCHEMA_FILES:
        return [
            f"{manifest_path}: unsupported schema {schema_name!r}; "
            f"expected one of {sorted(SCHEMA_FILES)}"
        ]
    schema_path = (library / "schemas" / SCHEMA_FILES[schema_name]).absolute()
    try:
        _require_regular_file(schema_path)
    except LibraryError:
        return [f"{manifest_path}: schema file missing: {schema_path.name}"]
    schema = load_json(schema_path)
    validator = SchemaValidator(schema, schema_path.name)
    errors = validator.validate(document)
    return [f"{manifest_path}: {error}" for error in errors]


def validate_challenge(library: Path, manifest_path: Path, document: object) -> list[str]:
    errors: list[str] = validate_schema_instance(library, manifest_path, document)
    if errors:
        return errors
    assert isinstance(document, dict)

    manifest_dir = manifest_path.parent
    identifier = document["id"]
    relative_parts = manifest_path.relative_to(library / "challenges").parts
    archived = len(relative_parts) == 4 and relative_parts[1] == "versions"
    current = len(relative_parts) == 2
    container_id = relative_parts[0] if relative_parts else ""
    if not current and not archived:
        errors.append(f"{manifest_path}: unsupported challenge manifest layout")
    if container_id != identifier:
        errors.append(
            f"{manifest_path}: challenge directory {container_id!r} does not match id {identifier!r}"
        )
    if archived and relative_parts[2] != document["version"]:
        errors.append(
            f"{manifest_path}: archived directory version {relative_parts[2]!r} "
            f"does not match manifest version {document['version']!r}"
        )

    prompt_relative = document["prompt"]["path"]
    prompt_file: Path | None = None
    if not is_safe_relative(prompt_relative):
        errors.append(f"{manifest_path}: unsafe prompt path: {prompt_relative!r}")
    else:
        prompt_file = resolve_inside(manifest_dir, prompt_relative)
        if not prompt_file.is_file():
            errors.append(f"{manifest_path}: prompt file not found: {prompt_relative}")
        else:
            actual_hash = sha256_of(prompt_file)
            declared_hash = document["prompt"]["sha256"]
            if actual_hash != declared_hash:
                errors.append(
                    f"{manifest_path}: prompt sha256 mismatch for {prompt_relative}: "
                    f"declared {declared_hash}, actual {actual_hash}"
                )

    evaluator = document.get("evaluator")
    if evaluator is not None:
        evaluator_relative = evaluator["path"]
        if not is_safe_relative(evaluator_relative):
            errors.append(f"{manifest_path}: unsafe evaluator path: {evaluator_relative!r}")
        else:
            evaluator_file = resolve_inside(manifest_dir, evaluator_relative)
            if not evaluator_file.is_file():
                errors.append(f"{manifest_path}: evaluator file not found: {evaluator_relative}")
            else:
                actual_hash = sha256_of(evaluator_file)
                declared_hash = evaluator["sha256"]
                if actual_hash != declared_hash:
                    errors.append(
                        f"{manifest_path}: evaluator sha256 mismatch for {evaluator_relative}: "
                        f"declared {declared_hash}, actual {actual_hash}"
                    )
    if document["status"] == "active" and document["tier"] != "showcase" and evaluator is None:
        errors.append(f"{manifest_path}: active core challenge requires an evaluator")

    prompt_words = 0
    if prompt_file is not None and prompt_file.is_file():
        try:
            prompt_text = prompt_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{manifest_path}: prompt is not valid UTF-8: {exc}")
        else:
            prompt_words = len(re.findall(r"\b\w[\w'-]*\b", prompt_text))
    prompt_limits = {"atom": 100, "compact": 350, "bounded": 700}
    prompt_limit = prompt_limits.get(document["tier"])
    if prompt_limit is not None and prompt_words > prompt_limit:
        errors.append(
            f"{manifest_path}: {document['tier']} prompt has {prompt_words} words; "
            f"maximum is {prompt_limit}"
        )

    provenance = document["provenance"]
    if document["origin"] == "external":
        source_url = provenance.get("source_url")
        if not source_url:
            errors.append(f"{manifest_path}: external challenge requires provenance.source_url")
        elif not source_url.startswith("https://"):
            errors.append(f"{manifest_path}: provenance.source_url must use HTTPS: {source_url!r}")
    license_block = provenance.get("license", {})
    spdx = license_block.get("spdx")
    if spdx is not None and spdx not in SPDX_LICENSE_ALLOWLIST:
        errors.append(
            f"{manifest_path}: license.spdx {spdx!r} is not in the documented SPDX allowlist"
        )
    if spdx is None:
        label = license_block.get("label", "").lower()
        if not any(signal in label for signal in NO_LICENSE_SIGNALS):
            errors.append(
                f"{manifest_path}: null spdx requires a label stating that no license is declared"
            )

    dimensions = document["capability_dimensions"]
    duplicate_dimensions = sorted(
        {name for name in dimensions if dimensions.count(name) > 1}
    )
    if duplicate_dimensions:
        errors.append(
            f"{manifest_path}: duplicate capability dimensions: "
            + ", ".join(duplicate_dimensions)
        )

    verification_ids = [item["id"] for item in document["verification"]]
    duplicates = sorted({name for name in verification_ids if verification_ids.count(name) > 1})
    if duplicates:
        errors.append(f"{manifest_path}: duplicate verification ids: {', '.join(duplicates)}")

    artifact_paths: set[str] = set()
    for artifact in document["artifacts"]:
        if artifact["path"] in artifact_paths:
            errors.append(f"{manifest_path}: duplicate artifact path: {artifact['path']}")
        artifact_paths.add(artifact["path"])
        if not is_safe_relative(artifact["path"]):
            errors.append(f"{manifest_path}: unsafe artifact path: {artifact['path']!r}")
        extension_error = validate_kind_extension(
            artifact["path"], artifact["kind"], ARTIFACT_EXTENSIONS
        )
        if extension_error:
            errors.append(f"{manifest_path}: artifact {extension_error}")

    criterion_ids: set[str] = set()
    for criterion in document["verification"]:
        if criterion["id"] in criterion_ids:
            errors.append(f"{manifest_path}: duplicate verification criterion id: {criterion['id']}")
        criterion_ids.add(criterion["id"])

    return errors


def validate_result(
    library: Path,
    manifest_path: Path,
    document: object,
    challenges: dict[tuple[str, str], tuple[Path, dict]],
    maintainer_ids: set[str],
) -> list[str]:
    errors: list[str] = validate_schema_instance(library, manifest_path, document)
    if errors:
        return errors
    assert isinstance(document, dict)

    manifest_dir = manifest_path.parent
    identifier = document["id"]
    if manifest_dir.name != identifier:
        errors.append(
            f"{manifest_path}: directory name {manifest_dir.name!r} does not match id {identifier!r}"
        )

    reference = document["challenge"]
    key = (reference["id"], reference["version"])
    if key not in challenges:
        errors.append(
            f"{manifest_path}: references unknown challenge "
            f"{reference['id']!r} version {reference['version']!r}"
        )
        return errors

    challenge_path, challenge_document = challenges[key]
    expected_hash = challenge_document["prompt"]["sha256"]
    echo = document["prompt_echo"]["sha256"]
    if echo != expected_hash:
        errors.append(
            f"{manifest_path}: prompt_echo sha256 {echo} does not match challenge "
            f"{key[0]} v{key[1]} prompt hash {expected_hash} ({challenge_path})"
        )

    challenge_criteria = challenge_document["verification"]
    challenge_criteria_by_id = {item["id"]: item for item in challenge_criteria}
    outcomes = document["criterion_outcomes"]
    outcome_ids = [item["id"] for item in outcomes]
    if len(outcome_ids) != len(set(outcome_ids)):
        errors.append(f"{manifest_path}: criterion outcome IDs must be unique")
    missing_criteria = sorted(set(challenge_criteria_by_id) - set(outcome_ids))
    extra_criteria = sorted(set(outcome_ids) - set(challenge_criteria_by_id))
    if missing_criteria:
        errors.append(
            f"{manifest_path}: missing criterion outcomes: {', '.join(missing_criteria)}"
        )
    if extra_criteria:
        errors.append(
            f"{manifest_path}: unknown criterion outcomes: {', '.join(extra_criteria)}"
        )

    evidence = document["evidence"]
    evidence_by_id: dict[str, dict] = {}
    for index, item in enumerate(evidence):
        evidence_id = item["id"]
        if evidence_id in evidence_by_id:
            errors.append(f"{manifest_path}: duplicate evidence id: {evidence_id}")
        evidence_by_id[evidence_id] = item
    for outcome in outcomes:
        criterion_id = outcome["id"]
        if criterion_id not in challenge_criteria_by_id:
            continue
        refs = outcome["evidence_refs"]
        if len(refs) != len(set(refs)):
            errors.append(f"{manifest_path}: duplicate evidence reference in criterion {criterion_id}")
        referenced = []
        for reference_id in refs:
            evidence_item = evidence_by_id.get(reference_id)
            if evidence_item is None:
                errors.append(
                    f"{manifest_path}: criterion {criterion_id} references unknown evidence {reference_id!r}"
                )
            else:
                referenced.append(evidence_item["kind"])
        required_kinds = set(challenge_criteria_by_id[criterion_id]["evidence_required"])
        missing_kinds = sorted(required_kinds - set(referenced))
        if missing_kinds:
            errors.append(
                f"{manifest_path}: criterion {criterion_id} is missing required evidence kinds: "
                + ", ".join(missing_kinds)
            )

    required_artifacts = {
        item["path"]: item for item in challenge_document["artifacts"] if item["required"]
    }
    challenge_artifacts = {item["path"]: item for item in challenge_document["artifacts"]}
    result_artifacts_by_path: dict[str, dict] = {}
    for artifact in document["artifacts"]:
        relative = artifact["path"]
        if relative in result_artifacts_by_path:
            errors.append(f"{manifest_path}: duplicate result artifact path: {relative}")
        result_artifacts_by_path[relative] = artifact
        expected_artifact = challenge_artifacts.get(relative)
        if expected_artifact is None:
            errors.append(f"{manifest_path}: artifact path is not declared by challenge: {relative}")
        elif artifact["kind"] != expected_artifact["kind"]:
            errors.append(
                f"{manifest_path}: artifact kind mismatch for {relative}: "
                f"declared {artifact['kind']!r}, expected {expected_artifact['kind']!r}"
            )
    if document["claim"]["passed"]:
        for relative, expected_artifact in required_artifacts.items():
            artifact = result_artifacts_by_path.get(relative)
            if artifact is None:
                errors.append(f"{manifest_path}: required artifact missing: {relative}")
            elif artifact["kind"] != expected_artifact["kind"]:
                errors.append(
                    f"{manifest_path}: required artifact kind mismatch for {relative}: "
                    f"declared {artifact['kind']!r}, expected {expected_artifact['kind']!r}"
                )

    all_criteria_passed = (
        set(outcome_ids) == set(challenge_criteria_by_id)
        and all(item["passed"] for item in outcomes)
    )
    if document["claim"]["passed"] and not all_criteria_passed:
        errors.append(
            f"{manifest_path}: passing claim requires every challenge criterion to pass"
        )
    if document["status"] == "verified" and not document["claim"]["passed"]:
        errors.append(f"{manifest_path}: verified status requires claim.passed to be true")
    if document["claim"]["passed"] and document["status"] in ("disputed", "withdrawn"):
        errors.append(
            f"{manifest_path}: passing claim is inconsistent with status {document['status']!r}"
        )

    review = document.get("maintainer_review")
    if document["status"] == "verified":
        if review is None:
            errors.append(f"{manifest_path}: verified status requires maintainer_review")
        elif review["reviewer_id"] not in maintainer_ids:
            errors.append(
                f"{manifest_path}: maintainer_review reviewer_id {review['reviewer_id']!r} "
                "is not in library/maintainers.json"
            )
        elif review["decision"] != "verified":
            errors.append(f"{manifest_path}: verified status requires a verified review decision")
    elif review is not None and review["decision"] == "verified":
        errors.append(f"{manifest_path}: verified maintainer review requires status=verified")

    if document["claim"]["passed"] and not evidence:
        errors.append(
            f"{manifest_path}: claim.passed is true but no evidence is provided"
        )
    if document["status"] == "verified":
        if not evidence:
            errors.append(f"{manifest_path}: verified status requires non-empty evidence")
        reproducibility = document["reproducibility"]["status"]
        if reproducibility not in ("reproducible", "partially-reproducible"):
            errors.append(
                f"{manifest_path}: verified status requires reproduction evidence, "
                f"but reproducibility.status is {reproducibility!r}"
            )

    for artifact in document["artifacts"]:
        relative = artifact["path"]
        if not is_safe_relative(relative):
            errors.append(f"{manifest_path}: unsafe artifact path: {relative!r}")
            continue
        extension_error = validate_kind_extension(relative, artifact["kind"], ARTIFACT_EXTENSIONS)
        if extension_error:
            errors.append(f"{manifest_path}: artifact {extension_error}")
        artifact_file = resolve_inside(manifest_dir, relative)
        try:
            _require_regular_file(artifact_file)
        except LibraryError:
            errors.append(f"{manifest_path}: artifact file missing: {relative}")
            continue
        actual_hash = sha256_of(artifact_file)
        if actual_hash != artifact["sha256"]:
            errors.append(
                f"{manifest_path}: artifact sha256 mismatch for {relative}: "
                f"declared {artifact['sha256']}, actual {actual_hash}"
            )

    for index, item in enumerate(document["evidence"]):
        location = item["location"]
        kind = item["kind"]
        if location.startswith(("http://", "https://")):
            if not location.startswith("https://"):
                errors.append(f"{manifest_path}: evidence[{index}] location must use HTTPS")
            if kind != "external-link":
                errors.append(
                    f"{manifest_path}: evidence[{index}] kind {kind!r} must use a checked-in local file"
                )
            if item["sha256"] is not None:
                errors.append(
                    f"{manifest_path}: evidence[{index}] external-link sha256 must be null"
                )
            continue
        if kind == "external-link":
            errors.append(f"{manifest_path}: evidence[{index}] external-link must use HTTPS")
            continue
        if not is_safe_relative(location):
            errors.append(f"{manifest_path}: evidence[{index}] unsafe location: {location!r}")
            continue
        extension_error = validate_kind_extension(location, kind, EVIDENCE_EXTENSIONS)
        if extension_error:
            errors.append(f"{manifest_path}: evidence[{index}] {extension_error}")
            continue
        evidence_file = resolve_inside(manifest_dir, location)
        try:
            if evidence_file.is_symlink():
                raise LibraryError("symlink")
            _require_regular_file(evidence_file)
        except LibraryError:
            errors.append(f"{manifest_path}: evidence[{index}] file missing: {location}")
            continue
        declared_hash = item["sha256"]
        if declared_hash is None:
            errors.append(f"{manifest_path}: evidence[{index}] local file requires sha256")
        else:
            actual_hash = sha256_of(evidence_file)
            if actual_hash != declared_hash:
                errors.append(
                    f"{manifest_path}: evidence[{index}] sha256 mismatch for {location}: "
                    f"declared {declared_hash}, actual {actual_hash}"
                )
        if kind == "screenshot" and not screenshot_signature_is_valid(evidence_file):
            errors.append(
                f"{manifest_path}: evidence[{index}] screenshot content does not match its image format"
            )
        elif kind in TEXT_EVIDENCE_KINDS:
            try:
                evidence_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"{manifest_path}: evidence[{index}] {kind} must be UTF-8 text")

    instructions = document["reproducibility"].get("instructions_path")
    if instructions is not None:
        if not is_safe_relative(instructions):
            errors.append(f"{manifest_path}: unsafe instructions_path: {instructions!r}")
        else:
            try:
                _require_regular_file(resolve_inside(manifest_dir, instructions))
            except LibraryError:
                errors.append(f"{manifest_path}: instructions_path not found: {instructions}")

    return errors


def collect_challenges(library: Path) -> tuple[dict[tuple[str, str], tuple[Path, dict]], list[str]]:
    errors: list[str] = []
    by_version: dict[tuple[str, str], tuple[Path, dict]] = {}
    manifests, discovery_errors = discover_challenge_manifests(library)
    errors.extend(discovery_errors)
    for manifest_path in manifests:
        try:
            document = load_json(manifest_path)
        except LibraryError as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_challenge(library, manifest_path, document))
        if isinstance(document, dict) and SEMVER_RE.match(str(document.get("version", ""))):
            key = (document["id"], document["version"])
            if key in by_version:
                errors.append(f"{manifest_path}: duplicate challenge {key[0]} v{key[1]}")
            else:
                by_version[key] = (manifest_path, document)
    return by_version, errors


def collect_results(
    library: Path,
    challenges: dict[tuple[str, str], tuple[Path, dict]],
    maintainer_ids: set[str],
) -> list[str]:
    results_base = library / "results"
    if not results_base.is_dir():
        return [f"missing directory: {results_base}"]
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    manifests: list[Path] = []
    for directory_entry in sorted(os.scandir(results_base), key=lambda entry: entry.name):
        entry_path = Path(directory_entry.path)
        if directory_entry.is_symlink():
            raise LibraryError(f"symlink is not allowed under library/: {entry_path}")
        if directory_entry.name == "README.md" and directory_entry.is_file(follow_symlinks=False):
            continue
        if not directory_entry.is_dir(follow_symlinks=False):
            errors.append(f"{entry_path}: result entry must be a directory")
            continue
        manifest = entry_path / "result.json"
        try:
            manifest_mode = manifest.lstat().st_mode
        except FileNotFoundError:
            errors.append(f"{directory_entry.path}: result directory is missing result.json")
            continue
        if stat.S_ISLNK(manifest_mode):
            raise LibraryError(f"symlink is not allowed under library/: {manifest}")
        if stat.S_ISREG(manifest_mode):
            _require_regular_file(manifest)
            manifests.append(manifest)
        else:
            errors.append(f"{manifest}: result.json must be a regular file")
    for manifest_path in manifests:
        errors.extend(reject_forbidden_result_files(manifest_path.parent))
        try:
            document = load_json(manifest_path)
        except LibraryError as exc:
            errors.append(str(exc))
            continue
        if isinstance(document, dict):
            identifier = str(document.get("id", manifest_path.parent.name))
            if identifier in seen_ids:
                errors.append(
                    f"{manifest_path}: duplicate result id {identifier!r} "
                    f"(also defined by {seen_ids[identifier]})"
                )
            else:
                seen_ids[identifier] = manifest_path
        errors.extend(validate_result(library, manifest_path, document, challenges, maintainer_ids))
    return errors


def load_maintainer_ids(library: Path) -> set[str]:
    path = library / MAINTAINERS_FILE
    document = load_json(path)
    if not isinstance(document, dict) or document.get("schema") != "oneshot.maintainers/v1":
        raise LibraryError(f"{path}: unsupported maintainer identity list")
    identities = document.get("identities")
    if not isinstance(identities, list) or not identities:
        raise LibraryError(f"{path}: identities must be a non-empty list")
    result: set[str] = set()
    for identity in identities:
        if not isinstance(identity, dict) or not isinstance(identity.get("id"), str):
            raise LibraryError(f"{path}: each identity requires a string id")
        identity_id = identity["id"]
        if identity_id in result:
            raise LibraryError(f"{path}: duplicate identity id: {identity_id}")
        result.add(identity_id)
    return result


def validate_library(library: Path = DEFAULT_LIBRARY_DIR) -> list[str]:
    library = library.absolute()
    reject_symlinks(library)
    maintainer_ids = load_maintainer_ids(library)
    for schema_filename in SCHEMA_FILES.values():
        schema_path = library / "schemas" / schema_filename
        try:
            _require_regular_file(schema_path)
        except LibraryError:
            raise LibraryError(f"missing schema: {schema_path}")
        schema = load_json(schema_path)
        SchemaValidator(schema, schema_filename)

    challenges, errors = collect_challenges(library)
    errors.extend(collect_results(library, challenges, maintainer_ids))
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library-dir",
        type=Path,
        default=DEFAULT_LIBRARY_DIR,
        help="Library directory to validate (default: repository library/)",
    )
    args = parser.parse_args(argv)

    try:
        errors = validate_library(args.library_dir)
    except LibraryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} library problem(s)", file=sys.stderr)
        return 1

    print("OK: challenge library is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
