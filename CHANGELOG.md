# Changelog

All notable changes to OneShot will be documented here.

The project follows Semantic Versioning.

## [Unreleased]

### Planned

- Run comparative skill evaluations across multiple agent hosts and publish the results.
- Expand domain playbooks only when evaluation evidence shows a recurring coverage gap.

### Changed

- Align repository and Lab language with the proportionate prompt profiles and current one-shot contract.

### Fixed

- Publish each release's curated `CHANGELOG.md` section instead of GitHub's generic contributor rollup.

## [1.2.0] - 2026-08-22

### Added

- Challenge Library layer with versioned challenge and result schemas, original offline browser-game candidates, exact prompt and artifact hashes, historical version resolution, and an explicit untrusted-artifact policy.
- Dependency-free Library validation integrated into repository and site builds, covering fail-closed schema checks, safe paths, typed evidence, criterion and artifact completeness, prompt and artifact hashes, provenance, archive and executable rejection, and symlink rejection.
- Game-forward challenge taxonomy with benchmark families, complexity tiers, prompt-depth profiles, concrete benchmark questions, standardized capability dimensions, and separate raw-completion and agentic-self-review lanes.
- Static Astro Lab site generated from checked-in manifests, with challenge and result pages, methodology and contribution guidance, honest empty states, and verified `/oneshot/` base paths.
- Explicit-click HTML artifact previews in opaque-origin `allow-scripts` iframes with restrictive document policy, no privileged parent bridge, and exact raw artifact links.
- SHA-pinned GitHub Pages workflow that builds and verifies pull requests, then deploys the same verified static output after merges to `main`; release publication fails closed unless that exact commit has a successful Pages workflow run.
- Project contract document defining one-shot as one initial brief with no human follow-up while internal tool use, testing, and iteration remain allowed.
- Two canonical disputed evidence records: a DeepSeek V4 Flash Loopback attempt whose independent validation could not establish the claimed completion chain, and a local Qwen3.8 27B NVFP4 Gravshift attempt that reached its generation cap without producing an artifact.
- Windline, an original compact glider challenge candidate with a fail-closed public evaluator. Calibration completed without activation; the draft remains closed pending a revised readability contract and fresh runs.
- Independent Brief, Benchmark, and Extensive prompt-depth profiles, with scope budgets and regression cases for narrow artifacts, frozen comparison tasks, repairs, and repository-scale migrations.
- Profile-aware prompt audit modes with permanent boundary coverage for one-sentence Brief prompts, the default 120-word Brief envelope, the 700-word Benchmark cap, and evaluator-mechanics leakage.

### Changed

- Select prompt depth, execution mode, and R0-R3 research depth independently rather than treating task complexity, agentic execution, and browsing as one scale.
- Keep scoring weights, evaluator internals, hidden cases, harness procedure, evidence collection, and retry policy out of contestant prompts.
- Reserve full structural-category and heading checks for Extensive prompts.
- Preserve the disputed Loopback run against archived challenge v1.0.0 while advancing the still-draft prompt to v1.0.1 for an audit-clean execution heading and level-table example.

### Fixed

- Stop penalizing valid one-sentence prompts for missing headings or repository-scale structure.
- Apply built-output sandbox checks to every HTML result and reject common private user paths across Linux, macOS, and Windows.

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
