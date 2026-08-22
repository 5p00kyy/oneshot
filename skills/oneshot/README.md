# OneShot Skill Package

`oneshot` is a portable Agent Skill for turning a request into a proportionately scoped, self-contained one-shot prompt for another model or agent. It can stay at supplied-context-only R0 for narrow work or research material decisions at R1-R3 when the task warrants it.

It is a **prompt-authoring skill**, not a skill that silently executes the underlying project.

## What it does

- Selects Brief, Benchmark, or Extensive prompt depth independently from execution mode and R0-R3 research depth.
- Distinguishes direct artifacts from agentic workspace builds, research tasks, and transformations.
- Audits the target executor's actual capabilities and environment when those details affect the result.
- Researches only facts that change feasibility, requirements, safety, or executor instructions.
- Converts material context into requirements, decisions, priorities, and proportionate acceptance checks.
- Bounds ambition into one complete outcome rather than padding a narrow task into a project plan.
- Reviews prompts for contradictions, dependency errors, infeasible scope, weak verification, evaluator leakage, and unnecessary bulk.
- Supports software, games, web products, research, data, automation, creative work, and documents.

## Skill structure

```text
oneshot/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml            # Optional host metadata for OpenAI-compatible interfaces
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
│   ├── calibration-profiles.md
│   ├── domain-playbooks.md
│   ├── prompt-architecture.md
│   ├── quality-rubric.md
│   ├── research-protocol.md
│   └── sources.md
└── scripts/
    ├── audit_prompt.py
    └── validate_skill.py
```

The `agents/openai.yaml` file is optional host metadata used by OpenAI-compatible interfaces. It is not a runtime requirement, and its presence does not make OneShot OpenAI-dependent.

## Install with GitHub CLI

Choose the agent ID for the host that should discover the skill, then install from the published repository:

```bash
AGENT_ID=universal  # Or codex, claude-code, gemini-cli, opencode, openclaw, and others.
gh skill install 5p00kyy/oneshot oneshot --agent "$AGENT_ID" --scope user
```

Pin a reviewed release when reproducibility matters. The commands below target this source version; use `v1.2.0` only after the matching GitHub release exists:

```bash
gh skill install 5p00kyy/oneshot oneshot@v1.2.0 --agent "$AGENT_ID" --scope user
```

Preview the same published tag first:

```bash
gh skill preview 5p00kyy/oneshot oneshot@v1.2.0
```

See the [`gh skill install` manual](https://cli.github.com/manual/gh_skill_install) for the current host list and placement rules. The listed agent IDs are installation targets, not claims of full runtime testing on every host.

## Manual installation

### Generic Agent Skills location

Any Agent Skills-compatible host typically discovers skills from `~/.agents/skills/` (user scope) or `.agents/skills/` (project scope):

```bash
mkdir -p ~/.agents/skills
cp -R oneshot ~/.agents/skills/oneshot
```

### OpenCode

```bash
# User scope
mkdir -p ~/.config/opencode/skills
cp -R oneshot ~/.config/opencode/skills/oneshot

# Project scope
mkdir -p .opencode/skills
cp -R oneshot .opencode/skills/oneshot
```

### Claude Code

```bash
# User scope
mkdir -p ~/.claude/skills
cp -R oneshot ~/.claude/skills/oneshot

# Project scope
mkdir -p .claude/skills
cp -R oneshot .claude/skills/oneshot
```

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

The audit is intentionally mechanical. It catches common omissions, placeholders, repeated directives, exposed-chain-of-thought requests, and likely capability conflicts. Sub-250-word prompts are treated as advisory notes rather than failures, so genuinely narrow prompts are not incorrectly penalized. The audit complements rather than replaces the semantic quality rubric.

## Evaluation

- `evals/evals.json` tests output quality across game development, software migration, research, financial modeling, creative production, and automation.
- `evals/trigger-evals.json` tests whether the skill activates for prompt-authoring requests and stays inactive when the user wants the underlying task performed.

Compare the same target model with and without the skill, then score the generated prompts using `references/quality-rubric.md`.

## Design note

A one-shot is **one complete initiating handoff**, not one tool call or one unreviewed generation. The resulting prompt may direct an agent through research, implementation, execution, inspection, testing, repair, and final handoff before returning.
