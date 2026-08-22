# Contributing to OneShot

Contributions are welcome when they improve reliability, portability, activation accuracy, research quality, or the usefulness of generated prompts.

## Before opening a change

Read:

- `AGENTS.md`
- `skills/oneshot/SKILL.md`
- `skills/oneshot/references/quality-rubric.md`
- `skills/oneshot/references/anti-patterns.md`

For substantial behavior changes, open an issue describing:

- The failure mode observed.
- A representative user request.
- The current output problem.
- The proposed behavior.
- How the change will be evaluated.

## Development setup

No third-party Python package is required.

Run:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -p "test_*.py"
```

Use `python` instead of `python3` where required.

## Commit and release discipline

Plan commit boundaries before staging substantial work. A release may contain many
commits; the release itself is not a sensible commit boundary.

- Keep each commit to one coherent, reviewable concern and leave the repository
  valid whenever practical.
- Separate contracts and schemas, validators, challenge or result data, site UI,
  skill behavior, and release automation when they can be reviewed independently.
- Do not squash distinct implementation layers into one commit merely because
  they ship in the same version.
- Add an informative entry under `CHANGELOG.md`'s `Unreleased` section for every
  user-visible change. Pull-request summaries and generated contributor lists do
  not replace the changelog.
- Before tagging, promote the curated entries into the dated version section.
  The release workflow publishes that exact section and fails if it is missing
  or empty.

Create a release package locally with:

```bash
python3 scripts/package_release.py
```

Site changes (Node 20+, locked toolchain):

```bash
cd site && npm ci && npm run build && npm run verify:dist
```

## Contribution rules

### Challenge library

New challenges are one directory under `library/challenges/<id>/` containing a
`challenge.json` manifest and the prompt file it references. Requirements:

- The manifest validates against `library/schemas/challenge-v1.schema.json` via
  `python3 scripts/validate_library.py`.
- The prompt is a complete standalone brief: executable with no human follow-up,
  with concrete rules, explicit scope, acceptance tests, and priorities.
- External entries link their source over HTTPS and state license status
  explicitly. Link upstream; never copy upstream outputs or imply ownership.
- Every manifest declares a required benchmark `family` (`playable`, `build`, `precision`, `repair`, or `edge-case`), a concrete `benchmark_question`, and standardized `capability_dimensions`; `category` is the artifact/task subtype.
- New categories, dimensions, or execution lanes require a schema change plus validator support — propose it in an issue first.
- New playable browser briefs should expose a documented read-only `window.__oneshotSnapshot()` returning a fresh JSON-serializable state snapshot. It may not mutate the game, expose control methods, or replace real interactive evidence.
- A core challenge remains `draft` until its public evaluator is checked in and hash-locked, its originality review passes, and at least two independent calibration runs show that the task is viable. Active T0-T2 manifests require an `evaluator` record.
- Keep scoring mechanics, hidden variants, retry policy, and harness implementation out of the contestant prompt. Prompt caps are 100 words for atom, 350 for compact, and 700 for bounded.
- Prompt content changes require a new challenge `version`; archive the previous
  manifest and prompt under `versions/<old-semver>/` before replacing the current
  pair, so existing results keep resolving to their exact input.

### Run results

Results go under `library/results/<result-id>/` with a manifest valid against
`library/schemas/result-v2.schema.json`. Validation mechanically rejects passing
claims without complete criterion outcomes/evidence, missing required artifacts,
artifact or evidence hashes that do not match regular bytes on disk, stale prompt hashes,
unknown challenge references, evidence kinds that do not match local file
formats, unsafe paths, archive/executable payloads, symlinks, and incomplete
executor identity. A `verified` status requires a passing claim and a review attestation
whose ID is listed in `library/maintainers.json`. That check validates only the
listed identity and data shape; it is not cryptographic authentication and does
not replace repository authorship or code review.

Submitted artifacts are untrusted input: no executables or archives. Accepted HTML artifacts may run on result pages only after an explicit click, inside the Lab's opaque-origin `allow-scripts` iframe with restrictive CSP and no parent-site bridge. Contributors may not request extra sandbox grants, external resources, forms, popups, downloads, top-level navigation, or automatic execution. Exact raw files remain available for inspection, and evaluator-controlled verification remains the authority for result claims.

### Activation changes

Any change to the `description` or activation boundary must update `skills/oneshot/evals/trigger-evals.json` with:

- At least one realistic prompt that should activate.
- At least one nearby prompt that should not activate.
- A concise reason for each expected result.

### Workflow and template changes

Changes to the prompt-authoring workflow should:

- Preserve executor awareness.
- Preserve research calibration.
- Preserve explicit scope and definition of done.
- Preserve evidence-based verification.
- Avoid repeated directives and cargo-cult specificity.
- Avoid exposed-chain-of-thought requests.

Update `skills/oneshot/evals/evals.json` when a change affects expected output quality.

### New domain playbooks

Add a domain only when its recurring failure modes are materially different from existing guidance. Keep domain-specific details out of the core `SKILL.md` unless every activation needs them.

### Scripts

- Prefer the Python standard library.
- Include clear error messages and nonzero exit codes.
- Avoid network access in validation.
- Make release packaging deterministic where practical.
- Add or update tests.

### Site

- Keep the site data-driven from checked-in manifests; never hardcode challenge
  facts into pages that the manifest already carries. The site loader invokes
  the authoritative Python validator before reading any manifest or prompt.
- Keep client-side JavaScript minimal. Do not add an execution surface for submitted HTML; result artifacts remain raw inspection or download links.
- Preserve the `/oneshot/` base path in production and dev; `npm run
  verify:dist` enforces it after every build.
- No gradients, fake metrics, fabricated runs, or placeholder cards masquerading
  as content. The results empty state is a feature; keep it honest.

## Pull requests

A pull request should include:

- A clear problem statement.
- The files and behavior changed.
- Validation commands actually run.
- Evaluation cases added or changed.
- Any compatibility or migration concern.

Do not include generated `dist/` files, caches, credentials, or editor state.
