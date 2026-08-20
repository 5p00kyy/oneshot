# OneShot Skill Package

`oneshot` is a portable Agent Skill for researching a serious request and turning it into a structured, self-contained, implementation-ready one-shot prompt for another model or agent.

It is a **prompt-authoring skill**, not a skill that silently executes the underlying project.

## What it does

- Distinguishes direct artifacts from agentic workspace builds, research tasks, and transformations.
- Audits the target executor's actual capabilities and environment.
- Performs calibrated research using authoritative sources.
- Converts research into requirements, decisions, priorities, and acceptance tests.
- Bounds ambition into a complete initial release or artifact.
- Defines workflow gates, fallback behavior, and evidence-based completion.
- Reviews prompts for contradictions, dependency errors, infeasible scope, weak verification, and unnecessary bulk.
- Supports software, games, web products, research, data, automation, creative work, and documents.
- Selects compact, standard, or master templates according to task complexity.

## Skill structure

```text
oneshot/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── compact-oneshot-template.md
│   ├── master-oneshot-template.md
│   ├── one-shot-prompt-template.md
│   ├── quality-scorecard.md
│   └── research-brief-template.md
├── evals/
│   ├── evals.json
│   └── trigger-evals.json
├── references/
│   ├── anti-patterns.md
│   ├── domain-playbooks.md
│   ├── prompt-architecture.md
│   ├── quality-rubric.md
│   ├── research-protocol.md
│   └── sources.md
└── scripts/
    ├── audit_prompt.py
    └── validate_skill.py
```

## Install with GitHub CLI

From a published repository:

```bash
gh skill install 5p00kyy/oneshot oneshot --agent opencode --scope user
```

Pin a reviewed release when reproducibility matters:

```bash
gh skill install 5p00kyy/oneshot oneshot@v1.0.0 --agent opencode --scope user
```

Preview first:

```bash
gh skill preview 5p00kyy/oneshot oneshot@v1.0.0
```

The GitHub CLI skill commands are currently a preview feature. An unpinned install resolves the latest release, then the default branch when no release exists.

## Manual OpenCode installation

User scope:

```bash
mkdir -p ~/.config/opencode/skills
cp -R oneshot ~/.config/opencode/skills/oneshot
```

Project scope:

```bash
mkdir -p .opencode/skills
cp -R oneshot .opencode/skills/oneshot
```

OpenCode also supports `.agents/skills/oneshot/` and `.claude/skills/oneshot/` compatibility locations.

## Example requests

```text
Use the oneshot skill to research current browser rendering and physics approaches, then write a one-shot prompt for a coding agent to build an original, expansion-ready underwater survival game repository.
```

```text
Turn this product brief and repository README into one autonomous implementation prompt. Preserve the existing conventions and require real tests before handoff.
```

```text
Use the oneshot skill to audit and replace this oversized master prompt. Keep its intent, verify current tooling, remove repetition, and make the critical path measurable.
```

```text
Use the oneshot skill to research this market and write only the final copy-ready research prompt. Do not perform the market analysis itself.
```

## Validate the skill package

Run from this directory:

```bash
python3 scripts/validate_skill.py
```

The validator checks:

- Agent Skills name and description rules.
- Directory-name consistency.
- Frontmatter length and recognized fields.
- The recommended `SKILL.md` line limit.
- Relative Markdown links.
- Evaluation JSON structure and unique IDs.
- Trigger-evaluation structure.
- Python helper syntax.
- OpenAI interface metadata presence.

## Audit a generated prompt

```bash
python3 scripts/audit_prompt.py path/to/prompt.md
```

Use strict mode for a release gate:

```bash
python3 scripts/audit_prompt.py path/to/prompt.md --strict
```

The audit is intentionally mechanical. It catches common omissions, placeholders, repeated directives, exposed-chain-of-thought requests, and likely capability conflicts. It complements rather than replaces the semantic quality rubric.

## Evaluation

- `evals/evals.json` tests output quality across game development, software migration, research, financial modeling, creative production, and automation.
- `evals/trigger-evals.json` tests whether the skill activates for prompt-authoring requests and stays inactive when the user wants the underlying task performed.

Compare the same target model with and without the skill, then score the generated prompts using `references/quality-rubric.md`.

## Design note

A one-shot is **one complete initiating handoff**, not one tool call or one unreviewed generation. The resulting prompt may direct an agent through research, implementation, execution, inspection, testing, repair, and final handoff before returning.
