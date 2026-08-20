# OneShot Agent Skill

OneShot is a research-first Agent Skill that turns complex requests into rigorous, self-contained prompts for another model or agent to execute.

It is deliberately a prompt-authoring skill. It researches the task, calibrates scope, checks the target executor, converts vague quality goals into observable requirements, defines verification, and produces a copy-ready handoff. It does not silently perform the underlying project when the user asked for a prompt.

## Install

GitHub CLI v2.90.0 or later includes the preview `gh skill` commands.

Install the latest release for OpenCode at user scope:

```bash
gh skill install 5p00kyy/oneshot oneshot --agent opencode --scope user
```

Pin a reviewed release for reproducible installation:

```bash
gh skill install 5p00kyy/oneshot oneshot@v1.0.1 --agent opencode --scope user
```

Use `--scope project` to install only for the current project. Preview the pinned skill before installing it:

```bash
gh skill preview 5p00kyy/oneshot oneshot@v1.0.1
```

Agent Skills can contain executable scripts and behavioral instructions. Review the skill before installation and pin a release or commit when reproducibility matters.

## Use

OneShot should activate when the requested deliverable is a one-shot, master, implementation, build, handoff, or execution prompt. It should not activate when the user only wants the underlying task completed.

Example requests:

```text
Use the oneshot skill to research modern browser rendering, physics, asset generation, and testing, then write a single autonomous build prompt for an expansion-ready underwater survival game repository.
```

```text
Turn this rough product concept into a research-grounded one-shot prompt for a coding agent. Define architecture, milestones, tests, fallbacks, and the final handoff, but do not build the product yourself.
```

```text
Audit this oversized master prompt using the oneshot skill. Preserve its goal, verify current tooling, remove contradictions and duplication, and make completion measurable.
```

## How It Works

OneShot:

- Selects research depth from supplied-context-only work through high-consequence source review.
- Distinguishes direct artifacts, agentic workspace builds, research tasks, and transformations.
- Adapts instructions to chat models, coding agents, research agents, and creative systems.
- Converts research into decisions, priorities, dependencies, acceptance tests, and fallbacks.
- Bounds ambition into a complete initial release or artifact instead of an unfinished wishlist.
- Audits the final prompt against a 100-point semantic rubric and mechanical checks.

The portable package includes compact, standard, and master templates plus playbooks for software, serious games, data, automation, research, design, creative work, and documents.

## Repository Layout

```text
.
├── skills/oneshot/            # Portable Agent Skill
│   ├── SKILL.md
│   ├── assets/
│   ├── references/
│   ├── scripts/
│   └── evals/
├── scripts/                   # Validation, installation, and packaging
├── tests/                     # Dependency-free regression tests
└── .github/workflows/         # Validation and release automation
```

The repository layout is recognized by GitHub CLI skill discovery. Release archives contain only the portable `oneshot/` directory; repository tooling and documentation are excluded.

## Local Installation

Install from a checkout with GitHub CLI:

```bash
gh skill install . oneshot --from-local --agent opencode --scope user
```

Or use the validated repository installer:

```bash
./install.sh --target opencode --scope user
```

On Windows PowerShell:

```powershell
.\install.ps1 --target opencode --scope user
```

Existing installations are preserved unless `--force` is supplied. OpenCode also discovers Agent Skills from `.agents/skills/` and `.claude/skills/` compatibility locations.

## Validate

No third-party Python packages are required:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/package_release.py --clean
gh skill publish . --dry-run
```

Use `python` instead of `python3` where required. Generated release files are written to `dist/` and are intentionally not committed.

## Releases

Version tags trigger the release workflow, which validates the repository, builds the deterministic ZIP and checksum, and creates the GitHub release. `gh skill publish` is used only in dry-run mode so that one workflow remains the sole release authority.

See [`PUBLISHING.md`](PUBLISHING.md) for the maintainer procedure and [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing routing language, templates, evaluation fixtures, or the quality rubric. Changes to activation behavior must include positive and negative trigger cases.

Security issues should follow [`SECURITY.md`](SECURITY.md), not the public issue tracker.

## License

MIT. See [`LICENSE`](LICENSE).
