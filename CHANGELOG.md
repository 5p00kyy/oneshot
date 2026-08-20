# Changelog

All notable changes to OneShot will be documented here.

The project follows Semantic Versioning.

## [Unreleased]

### Planned

- Run comparative skill evaluations across multiple agent hosts and publish the results.
- Expand domain playbooks only when evaluation evidence shows a recurring coverage gap.

## [1.1.0] - 2026-08-21

### Fixed

- Prevent dangerous deletion in `package_release.py --clean`; reject protected paths, symlinked output paths, top-level filesystem directories, and directories containing unrelated files.
- Reject symlink destinations before resolving through them in the custom installer; never overwrite files behind a destination symlink.
- Compact prompt template passes strict audit after placeholder substitution; `## Output` heading is now recognized, and sub-250-word prompts are treated as advisory notes rather than strict-mode failures.

### Changed

- Make installation and documentation host-neutral; document canonical GitHub CLI IDs for universal, codex, claude-code, gemini-cli, opencode, and openclaw targets.
- Add universal, opencode, claude-code, gemini-cli, and openclaw targets to the custom installer.
- Keep `claude` and `agents` as backward-compatible aliases for claude-code and universal.
- Default the custom installer to `universal` target.
- Explain `agents/openai.yaml` as optional host metadata rather than deleting it.
- Add regression coverage for structurally complete narrow prompts.

## [1.0.1] - 2026-08-21

### Fixed

- Accept the nested metadata indentation GitHub CLI injects into installed skills.

### Changed

- Update pinned GitHub Actions to current Node 24-native releases.

## [1.0.0] - 2026-08-21

### Added

- Research-first workflow for authoring serious one-shot prompts.
- Activation boundary separating prompt authoring from direct task execution.
- Research depth levels R0 through R3.
- Direct-artifact, workspace-agent, research, and transformation modes.
- Compact, standard, and master prompt templates.
- Domain playbooks, research protocol, prompt architecture, anti-pattern catalogue, and quality rubric.
- Mechanical prompt audit and dependency-free package validation.
- Positive and negative trigger evaluations.
- Output-quality evaluations across multiple domains.
- Public-repository validation, deterministic ZIP packaging, CI, publishing documentation, and OpenCode installation guidance.
- Single-authority, immutable release automation with exact-manifest package verification.
