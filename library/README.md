# OneShot Challenge Library

The Library is the curated middle layer of OneShot: versioned challenge
manifests, the standalone prompts they point to, and evidence-backed result
manifests. It is plain JSON and Markdown under version control, with no
database, no service.

- `schemas/`: versioned JSON Schemas for challenges and results.
- `maintainers.json`: canonical maintainer IDs used only for review-attestation shape checks.
- `challenges/<challenge-id>/`: one directory per challenge: the current
  `challenge.json` plus its prompt. Older versions needed by published results
  live under `versions/<semver>/` with their own manifest and prompt.
- `results/<result-id>/`: one directory per published run result:
  `result.json` plus its evidence and artifact files. The checked-in records
  currently include two disputed showcase runs; see `results/README.md`.

## Manifest contracts

Both manifest types are validated by `scripts/validate_library.py`, which
enforces a documented subset of JSON Schema (draft 2020-12) plus semantic rules
that a schema alone cannot express. Validation is deterministic and
dependency-free.

### Challenge manifest (`oneshot.challenge/v1`)

Schema: [`schemas/challenge-v1.schema.json`](schemas/challenge-v1.schema.json)

| Field | Meaning |
|---|---|
| `id` | Stable slug, must match the containing directory name. Never reused. |
| `version` | Manifest semver. Content-changing prompt edits require a new challenge `version`. |
| `family` | Required benchmark family: `playable`, `build`, `precision`, `repair`, or `edge-case`. |
| `tier` | Complexity board: `atom` (T0), `compact` (T1), `bounded` (T2), or `showcase` (T3). |
| `prompt_profile` | Authoring depth: `brief`, `benchmark`, or `extensive`. |
| `category` | Artifact or task subtype (for example `svg-illustration`, `playable-browser-game`, or `repository-repair`), not the primary benchmark family. |
| `benchmark_question` | Concrete question about what capability the brief probes. |
| `capability_dimensions` | Required standardized dimensions such as planning, implementation, debugging, verification, accessibility, or offline delivery. |
| `status` | `draft`, `active`, or `retired`. Only `active` challenges are open for runs. |
| `origin` | `original` (authored here) or `external` (linked community classic). |
| `prompt.path` / `prompt.sha256` | Relative path to the standalone prompt and its SHA-256. |
| `evaluator` | Optional public evaluator entrypoint, runtime, notes, and SHA-256. Required before a core challenge can become active. |
| `provenance` | Source URL, licensing (SPDX or explicit "none declared"), attribution. |
| `capabilities` | Environment, allowed tools, required skills, constraints for executors. |
| `execution_lane` | How artifacts are produced and later displayed (for example single-file browser artifact). |
| `budget` | Declared wall-clock/file/network bounds for a run. |
| `verification` | Acceptance checks a result must satisfy, with required evidence kinds. |
| `artifacts` | Expected output descriptors (path pattern, kind, required). |
| `one_shot_policy` | Fixed to the [one-shot definition](../docs/one-shot-definition.md): no human follow-up, internal iteration allowed. |

### Result manifest (`oneshot.result/v2`)

Schema: [`schemas/result-v2.schema.json`](schemas/result-v2.schema.json). The v1 schema remains available for historical records; v2 adds the required comparison lane.

| Field | Meaning |
|---|---|
| `id` | Stable result slug, must match the containing directory name. |
| `challenge.id` + `challenge.version` | Exact challenge this run executed (referential integrity is checked). |
| `run_class` | `canonical` (maintainer-run reference), `community` (public submission), or `showcase` (editorially highlighted). |
| `run_lane` | `raw-completion` or `agentic-self-review`; results from different lanes are never ranked together. |
| `executor` | Complete model-plus-agent identity: model name/version/snapshot, agent name/version, host. |
| `executed_at` | Date of the run. |
| `claim` | What the run asserts (`passed` plus summary). |
| `criterion_outcomes` | Exactly one pass/fail outcome with explanatory notes for every challenge criterion, each with evidence references covering the criterion's required kinds. |
| `artifacts` | Produced files with SHA-256 hashes; hashes are verified against bytes on disk. |
| `evidence` | Checked-in transcripts, logs, screenshots, checksums, and reproduction files with verified SHA-256 hashes; only `external-link` may use HTTPS instead of a local file and uses a null hash. |
| `reproducibility` | Whether independent re-runs reproduced the claim, plus instructions. |
| `prompt_echo.sha256` | Must equal the referenced challenge's current prompt hash. |
| `maintainer_review` | Required for `status: verified`; reviewer ID must be listed in `maintainers.json`, with date, decision, and notes. |

## Semantic rules enforced beyond the schema

1. Prompt and evaluator paths must be safe relative paths that stay inside their challenge directory.
2. Declared prompt and evaluator SHA-256 values must equal the actual file bytes. Active T0-T2 core challenges require a public evaluator; draft candidates may remain visible while calibration is incomplete. Atom, compact, and bounded prompts are mechanically capped at 100, 350, and 700 words.
3. `origin: external` requires an HTTPS `provenance.source_url`.
4. Results must reference an existing challenge at an existing version, and
   `prompt_echo.sha256` must match that challenge's current prompt hash.
5. Every result criterion ID must occur exactly once; references must resolve to
   declared evidence and include each required evidence kind. Typed evidence
   must use an allowed extension, screenshots must carry a matching PNG/JPEG/WebP
   signature, text evidence must be UTF-8, every local evidence hash must match
   its checked-in bytes, and only `external-link` may use HTTPS with a null hash.
   Passing claims require every criterion to pass. A verified status requires a
   passing claim and maintainer review.
6. Every required challenge artifact must occur exactly once in a passing result,
   with the declared path, kind, and matching file extension. Artifact hashes
   must match regular files on disk. Archive payloads and executable file modes
   are rejected; symlinks anywhere under `library/` are rejected before discovery.
7. Challenge `provenance.license.spdx` uses the explicit SPDX subset in the
   schema. `null` is preserved for no-declared-license cases only when its label
   says so; it does not assert a reuse license.
8. External entries are linked, never copied: upstream outputs stay upstream.
9. Every challenge declares a recognized family, complexity tier, prompt-depth profile, concrete benchmark question, and at least one standardized capability dimension.

The maintainer attestation checks only that a listed ID supplied the expected
data shape. It is not cryptographic proof of identity and does not replace
repository authorship, signed review, or human code review.

The current SPDX License List subset is: `AGPL-3.0-only`, `Apache-2.0`,
`BSD-2-Clause`, `BSD-3-Clause`, `CC0-1.0`, `GPL-2.0-only`, `GPL-3.0-only`,
`ISC`, `LGPL-2.1-only`, `LGPL-3.0-only`, `MIT`, `MPL-2.0`, and `Unlicense`.

## Versioning

Schemas carry their version in `$id` and filename (`challenge-v1`). Breaking
changes get a new file and a new `schema` constant; old manifests keep
validating against their own version.

Challenge content changes bump the challenge `version`. Before replacing the
current manifest and prompt, move the previous pair to
`challenges/<id>/versions/<old-semver>/`. The validator indexes both current and
archived manifests by `(id, version)`, so checked-in historical results continue
to resolve exactly the prompt they executed. The site lists only each
challenge's current root manifest.

## Result artifact display

Checked-in artifacts are untrusted input. Accepted HTML may run only after an explicit click inside the Lab's opaque-origin `allow-scripts` iframe, under a restrictive document CSP and without a privileged parent bridge. Exact repository files remain available for inspection. The site preview is not verification evidence; interactive claims still require evaluator-controlled evidence. Repository acceptance is a publication boundary, not a claim that an artifact is safe.
