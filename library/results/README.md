# Results

This directory holds published run results — one `result.json` manifest per
directory, plus that run's artifacts and evidence. It currently contains two
disputed canonical showcase records. These are
inspectable attempts, including a preserved zero-artifact failure, not aggregate
performance claims, and this repository does not fabricate placeholder runs.

## What a real submission looks like

A result directory (for example `results/<result-id>/`) contains:

- `result.json` — a manifest valid against
  [`../schemas/result-v2.schema.json`](../schemas/result-v2.schema.json).
- The artifact files declared in the manifest (for example `artifact.svg` or
  `index.html`), with SHA-256 hashes recorded in the manifest.
- Evidence files: UTF-8 run transcripts/logs/checksums/reproduction material,
  and real PNG/JPEG/WebP screenshots. Only evidence declared as
  `external-link` may point to HTTPS instead of a checked-in file.

Validation (`scripts/validate_library.py`) enforces:

- The referenced challenge exists at the referenced version.
- `prompt_echo.sha256` matches the challenge's current prompt hash.
- Every challenge criterion appears exactly once in `criterion_outcomes`, with
  pass/fail and references covering its required evidence kinds.
- A passing claim requires every criterion to pass and every required challenge
  artifact to appear exactly once with its declared path and kind.
- Every artifact hash matches a regular, non-symlink file; its extension agrees
  with its declared kind, and every path is safe and inside `library/`. Archive
  payloads and executable file modes are rejected. Symlinks anywhere under
  `library/` are rejected before discovery.
- Evidence kinds are tied to location and content: local evidence is SHA-256
  verified, typed evidence is local,
  screenshot signatures must match their image format, and HTTPS locations are
  reserved for `external-link`.
- `verified` results require a `maintainer_review` whose ID is listed in
  `library/maintainers.json`.
- A complete model-plus-agent identity is present.

## Untrusted-artifact policy

Submitted artifacts are **untrusted input**, not endorsed software:

- A submitted artifact is not displayed until its result is reviewed and
  accepted into the repository. That acceptance does not certify the code safe.
- Accepted HTML artifacts run only after an explicit click inside an opaque-origin
  iframe whose sole sandbox grant is `allow-scripts`; a restrictive document CSP
  blocks data connections, external resources, forms, popups, downloads, and
  top-level navigation, and no privileged parent bridge is exposed. Exact raw files remain
  available for inspection. The site preview is not verification evidence.
- SVG can carry script. The Lab uses only checked-in SVG bytes as a static image
  preview, never as inline document markup.
- Nothing in the site executes submitted code automatically.

## Run classes

- **canonical** — run by maintainers as the reference attempt for a challenge.
- **community** — a public submission from a contributor.
- **showcase** — a canonical or community run highlighted editorially for
  exceptional quality; selection is a maintainer decision and says nothing
  about other runs being invalid.

## Run lanes

- **raw-completion** — one frozen prompt and one generation, without tool-mediated inspection or repair.
- **agentic-self-review** — one frozen prompt and no human follow-up, with declared tools and repair allowed inside the fixed run budget.

These measure different systems and are never ranked together.

## Reproducibility

Every result declares a reproducibility status. `verified` status additionally
requires the shape of an independent maintainer-review attestation. The
validator does not cryptographically authenticate the reviewer: repository
authorship and code review remain the trust boundary. Claims without the
required evidence are rejected by validation before they ever reach the site.
