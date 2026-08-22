# Security Policy

Agent Skills can influence tool use and may include executable scripts. Review skills before installing them, prefer version-pinned releases for sensitive environments, and inspect changes before updating.

## Supported version

Security fixes are applied to the latest released version.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose credentials, execute unintended commands, escape intended file boundaries, or create a supply-chain risk.

Use GitHub's private vulnerability reporting feature when enabled. Otherwise contact the repository maintainer privately through the address or channel listed on the maintainer's GitHub profile.

Include:

- Affected version or commit.
- Reproduction steps.
- Expected and actual behavior.
- Potential impact.
- Any suggested mitigation.

Do not include real secrets or other people's private data in a report.

## Scope

Relevant issues include:

- Path traversal or unsafe archive extraction.
- Validation bypasses that allow malformed skill packages, challenge manifests, or result manifests (for example incomplete or falsely typed criterion evidence, required-artifact omissions, archives/executable payloads, symlinks, artifact/evidence hash mismatches, or unsafe paths slipping past `scripts/validate_library.py`). The site build invokes this validator before reading library content.
- Prompt instructions that encourage credential disclosure or destructive external actions without approval.
- Packaging or release workflows that publish unintended files.
- Site generation or result pages that weaken the artifact sandbox. Checked-in HTML may execute only after explicit user action in an opaque-origin iframe with `allow-scripts` as its sole sandbox grant, a restrictive document CSP that blocks data connections and external resource loads, and no privileged bridge to the parent site. Same-origin access, automatic execution, forms, popups, downloads, top-level navigation, external resources, or unsandboxed embedding are security defects.
- Dependency or workflow changes that introduce a material supply-chain risk.
- Public artifact evaluators that execute untrusted HTML without a real network/user isolation boundary, the browser's own sandbox, one-file staging, bounded deadlines/caps, or consistent late-violation reporting.

Public evaluators are security boundaries: they must fail closed when a safe
isolation prerequisite is unavailable, and must not quietly add an unsandboxed
`--no-sandbox` fallback. Offline results must be based on one final outcome
computed after the complete bounded run, including its late-event observation
window.

The maintainer ID in a result attestation is an allowlisted data label, not
cryptographic identity proof. Repository authorship, signed review where used,
and human code review remain the authentication boundary.

Ordinary prompt-quality disagreements and feature requests belong in public issues.
