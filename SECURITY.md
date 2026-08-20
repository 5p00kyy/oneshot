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
- Validation bypasses that allow malformed skill packages.
- Prompt instructions that encourage credential disclosure or destructive external actions without approval.
- Packaging or release workflows that publish unintended files.
- Dependency or workflow changes that introduce a material supply-chain risk.

Ordinary prompt-quality disagreements and feature requests belong in public issues.
