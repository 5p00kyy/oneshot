# OneShot

OneShot is an evidence-backed field guide to one-shot autonomous work, built in three layers around one contract: **one initial brief, no human follow-up**.

1. **Authoring:** an Agent Skill that turns requests into proportionately scoped, self-contained prompts for another model or agent to execute.
2. **Library:** a curated set of versioned challenge manifests and standalone prompts (`library/`), validated by dependency-free tooling.
3. **Lab:** a static benchmark/gallery site (`site/`) that renders exactly what the checked-in manifests say: challenges today, evidence-backed results when they exist.

It is deliberately a prompt-authoring skill. It calibrates scope, researches only when material decisions require it, checks the target executor where relevant, converts vague quality goals into observable requirements, defines proportionate verification, and produces a copy-ready handoff. It does not silently perform the underlying project when the user asked for a prompt.

## Status

- 5 visible draft challenge candidates across the compact core and T3 showcase board. None is open for new runs until its originality and calibration gates pass.
- 2 published canonical disputed run records. They are evidence records, not aggregate performance claims; failed attempts remain published with hashes and evaluator evidence.

## Install

GitHub CLI v2.90.0 or later includes the `gh skill` commands.

Choose the GitHub CLI agent ID for the host that should discover the skill. `universal` uses the shared Agent Skills location:

| `AGENT_ID` | Host |
|---|---|
| `universal` | Shared Agent Skills location |
| `codex` | Codex |
| `claude-code` | Claude Code |
| `gemini-cli` | Gemini CLI |
| `opencode` | OpenCode |
| `openclaw` | OpenClaw |

GitHub CLI supports additional hosts. See the current list in the [`gh skill install` manual](https://cli.github.com/manual/gh_skill_install).

Pin a reviewed release for reproducible installation. The commands below target this source version; use `v1.2.0` only after the matching GitHub release exists:

```bash
AGENT_ID=universal  # Replace with the ID for your host when needed.
gh skill install 5p00kyy/oneshot oneshot@v1.2.0 --agent "$AGENT_ID" --scope user
```

Use `--scope project` to install only for the current project. Preview the same published tag before installing:

```bash
gh skill preview 5p00kyy/oneshot oneshot@v1.2.0
```

Agent Skills can contain executable scripts and behavioral instructions. Review the skill before installation and pin a release or commit when reproducibility matters.

### Host compatibility

OneShot uses the portable Agent Skills layout. The agent IDs above describe GitHub CLI installation targets, not a claim that every host has received full runtime testing. Validate host-specific discovery and behavior on the platform where the skill will run.

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

- Selects Brief, Benchmark, or Extensive prompt depth independently from execution mode and research depth.
- Selects research depth from supplied-context-only work through high-consequence source review.
- Distinguishes direct artifacts, agentic workspace builds, research tasks, and transformations.
- Adapts instructions to chat models, coding agents, research agents, and creative systems.
- Converts research into decisions, priorities, dependencies, acceptance tests, and fallbacks.
- Bounds ambition into a complete initial release or artifact instead of an unfinished wishlist.
- Audits the final prompt against a 100-point semantic rubric and mechanical checks.

The portable package includes compact Brief and Benchmark scaffolds, standard and master Extensive templates, and playbooks for software, serious games, data, automation, research, design, creative work, and documents.

## Challenge Library

The benchmark now separates a compact cross-model core (T0-T2) from a T3 showcase/stress board. See [`docs/benchmark-framework.md`](docs/benchmark-framework.md) for the tier budgets, prompt-depth profiles, raw-completion versus agentic lanes, scoring bands, evidence levels, and starter battery.

`library/` stores challenges as data: a current `challenge.json` manifest plus the standalone prompt file it hashes, with historical manifest/prompt pairs archived by semver when published results still reference them. Manifests carry stable IDs and versions, a required benchmark family, complexity tier, prompt-depth profile, artifact/task subtype category, concrete benchmark question, standardized capability dimensions, status, provenance and licensing (external entries are linked, never copied), capability profiles, execution lane, budgets, verification criteria with required evidence kinds, expected artifacts, and the fixed one-shot policy defined in [`docs/one-shot-definition.md`](docs/one-shot-definition.md).

Current result manifests (`oneshot.result/v2`) are designed for honesty under enforcement: complete model-plus-agent identity, run class (canonical/community/showcase), explicit raw-completion or agentic-self-review lane, required prompt echoes, one outcome per challenge criterion with evidence references, required artifact coverage, artifact and checked-in evidence SHA-256s verified against regular files on disk, typed local evidence with format checks, and reproducibility status. Verified results additionally carry a maintainer-review attestation whose reviewer ID must appear in [`library/maintainers.json`](library/maintainers.json). This is only a checked identity/shape assertion; it is not cryptographic authentication or a substitute for repository authorship and code review. `scripts/validate_library.py` enforces all of this with zero dependencies, including safe-path checks, archive/executable rejection, and referential integrity between results and exact challenge versions.

Challenge licenses use a documented, deliberately small SPDX License List subset in the challenge schema and validator. A `null` SPDX value is valid only when the accompanying label explicitly says that no license is declared; it does not grant reuse rights.

Current challenge candidates (all draft and closed to new runs):

- [`loopback`](library/challenges/loopback/challenge.json): circuit-rotation puzzle benchmark; naming review required.
- [`neon-courier`](library/challenges/neon-courier/challenge.json): top-down delivery/pursuit benchmark; rename required.
- [`signal-siege`](library/challenges/signal-siege/challenge.json): keyboard tower-defence benchmark; rename required.
- [`gravshift`](library/challenges/gravshift/challenge.json): gravity-flip platformer candidate requiring substantial originality revision.
- [`windline`](library/challenges/windline/challenge.json): compact glider candidate whose calibration did not pass activation.

## Lab Site

`site/` is a small static Astro + TypeScript site. It invokes the authoritative dependency-free library validator before reading manifests or prompt bytes, then renders the checked-in data with no client-side fetching, fabricated metrics, or placeholder cards. Pages: project home, challenge library, per-challenge detail (with copy-prompt, hash, provenance, capabilities, budget, one-shot policy, and verification criteria), a results ledger with constrained interactive HTML sandboxes plus raw artifact links, methodology (one-shot definition, verification tiers, and untrusted-artifact policy), and contribution guidance.

Lab URL (deployed from `main` through GitHub Pages): <https://5p00kyy.github.io/oneshot/>

The production build is served under the `/oneshot/` base path; local dev serves the same paths.

```bash
cd site
npm ci          # installs the locked toolchain
npm run build   # builds to site/dist
npm run verify:dist  # verifies base paths, sandbox boundaries, and content rules
npm run dev     # dev server at http://localhost:4321/oneshot/
```

Result artifacts are untrusted. HTML executes only after an explicit click inside an opaque-origin iframe whose sole sandbox grant is `allow-scripts`; a restrictive document policy blocks data connections, external resources, forms, popups, downloads, and top-level navigation, and the frame has no privileged bridge to the site. Exact raw artifact links remain available for inspection. SVG stays a static image rather than inline markup. Repository acceptance and the interactive preview do not certify an artifact as safe.

## Repository Layout

```text
.
├── skills/oneshot/            # Portable Agent Skill (authoring layer)
│   ├── SKILL.md
│   ├── agents/                # Optional host metadata (e.g., openai.yaml)
│   ├── assets/
│   ├── references/
│   ├── scripts/
│   └── evals/
├── library/                   # Challenge library (data layer)
│   ├── schemas/               # Versioned JSON Schemas (challenge/result)
│   ├── maintainers.json       # Canonical IDs for review-attestation shape checks
│   ├── challenges/            # Current challenge manifests/prompts + version archives
│   └── results/               # Published evidence-backed run records
├── site/                      # Static benchmark/gallery (Lab layer)
├── docs/                      # Project contracts (one-shot definition)
├── scripts/                   # Validation, installation, packaging
├── tests/                     # Dependency-free regression tests
└── .github/workflows/         # Validation, release, and site-build automation
```

The `skills/oneshot` layout is recognized by GitHub CLI skill discovery. Release archives contain only the portable `oneshot/` directory; repository tooling, the library, and the site are excluded.

## Local Installation

Install from a checkout with GitHub CLI:

```bash
gh skill install . oneshot --from-local --agent universal --scope user
```

Or use the validated repository installer:

```bash
./install.sh --target universal --scope user
```

On Windows PowerShell:

```powershell
.\install.ps1 --target universal --scope user
```

Existing installations are preserved unless `--force` is supplied. The custom installer keeps `claude` as an alias for `claude-code` and `agents` as an alias for `universal`; these aliases do not apply to GitHub CLI.

## Validate

No third-party Python packages are required:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/package_release.py --clean
gh skill publish . --dry-run
```

Use `python` instead of `python3` where required. Generated release files are written to `dist/` and are intentionally not committed.

Site checks require Node 20+ and use the committed lockfile:

```bash
cd site && npm ci && npm run build && npm run verify:dist
```

## Releases

Version tags trigger the release workflow, which validates the repository, builds the deterministic ZIP and checksum, and creates the GitHub release. `gh skill publish` is used only in dry-run mode so that one workflow remains the sole release authority.

See [`PUBLISHING.md`](PUBLISHING.md) for the maintainer procedure and [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing routing language, templates, evaluation fixtures, the quality rubric, challenge manifests, or the site. Changes to activation behavior must include positive and negative trigger cases. Challenge and result submissions must pass `scripts/validate_library.py`, which rejects malformed, incomplete, hash-mismatched, or internally inconsistent records. Evidence truthfulness and claimed outcomes remain a maintainer review responsibility.

Security issues should follow [`SECURITY.md`](SECURITY.md), not the public issue tracker.

## License

MIT. See [`LICENSE`](LICENSE).
