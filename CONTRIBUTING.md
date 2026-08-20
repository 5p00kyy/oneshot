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

Create a release package locally with:

```bash
python3 scripts/package_release.py
```

## Contribution rules

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

## Pull requests

A pull request should include:

- A clear problem statement.
- The files and behavior changed.
- Validation commands actually run.
- Evaluation cases added or changed.
- Any compatibility or migration concern.

Do not include generated `dist/` files, caches, credentials, or editor state.
