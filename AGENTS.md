# Repository Instructions for Coding Agents

## Purpose

This repository maintains three layers around one contract — one initial brief, no human follow-up:

1. The portable Authoring skill: `skills/oneshot/`.
2. The curated challenge Library: `library/` (versioned manifests, prompts, results).
3. The static benchmark/gallery Lab: `site/` (data-driven from checked-in manifests).

OneShot researches complex requests and authors detailed, implementation-ready one-shot prompts for another executor. It does not silently perform the requested underlying project unless the user explicitly asks for both execution and a reusable prompt.

## Read before changing behavior

For changes to skill behavior, read:

- `skills/oneshot/SKILL.md`
- `skills/oneshot/references/prompt-architecture.md`
- `skills/oneshot/references/research-protocol.md`
- `skills/oneshot/references/quality-rubric.md`
- `skills/oneshot/references/anti-patterns.md`
- Relevant domain sections in `skills/oneshot/references/domain-playbooks.md`

For changes to the challenge library or site, read:

- `docs/one-shot-definition.md`
- `library/README.md`
- `library/schemas/challenge-v1.schema.json` and `library/schemas/result-v1.schema.json`
- `CONTRIBUTING.md` sections on challenges, results, and the site

For publishing work, read:

- `PUBLISHING.md`
- Current installed `gh skill publish --help` output when available

## Invariants

- The skill directory is `skills/oneshot`.
- `SKILL.md` frontmatter `name` is exactly `oneshot`.
- The name must match the skill directory.
- Keep `SKILL.md` below 500 lines and approximately below 5,000 tokens.
- Keep detailed guidance in one-level supporting references.
- Preserve the activation boundary between prompt authoring and direct task execution.
- Keep both positive and negative trigger evaluations.
- Do not request exposed chain of thought.
- Do not fabricate research, citations, executor capabilities, test results, or completion evidence.
- Challenge and result manifests must pass `scripts/validate_library.py`; result claims require evidence; external entries are linked, never copied.
- The site renders only what checked-in manifests support; no placeholder cards, fake metrics, or fabricated runs; submitted artifacts are untrusted and never auto-executed.
- Keep the site base path `/oneshot/` working in production and dev.
- Keep validation and packaging scripts dependency-free unless there is a compelling documented reason.
- Do not commit generated `dist/` artifacts (root or `site/dist`) or `site/node_modules`.
- Do not commit caches, credentials, editor state, or installation metadata injected by a skill manager.
- Do not publish or create external repositories unless the user explicitly authorizes that action.

## Required checks

Run after any meaningful change:

```bash
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/package_release.py
```

After changes to `site/` or `library/`, also run:

```bash
cd site && npm ci && npm run build && npm run verify:dist
```

When GitHub CLI skill support is available, also run:

```bash
gh skill publish . --dry-run
```

Use `python` instead of `python3` on platforms where required.

## Change expectations

When changing activation language:

- Add or update trigger cases in `skills/oneshot/evals/trigger-evals.json`.
- Include cases that should activate and cases that should not.
- Explain why the description remains neither over-broad nor under-specific.

When changing output workflow or templates:

- Update relevant cases in `skills/oneshot/evals/evals.json`.
- Check all template references.
- Run the prompt audit against at least one representative generated prompt.

When changing public behavior:

- Update `CHANGELOG.md`.
- Apply semantic versioning.
- Keep `metadata.version` in `skills/oneshot/SKILL.md` synchronized with the release tag.

## Style

- Prefer direct, specific prose.
- State a rule once in the most relevant section.
- Explain constraints when the rationale improves agent judgment.
- Avoid ceremonial process that does not improve outcomes.
- Avoid examples that accidentally narrow the skill to only software or game development.
- Use UTF-8 and LF line endings.

## External actions

Before creating a repository, tag, release, issue, or discussion:

- Confirm explicit user authorization.
- Inspect current authentication and remote state.
- Never overwrite an existing remote.
- Never request secrets in chat.
- Report actual command outcomes.
