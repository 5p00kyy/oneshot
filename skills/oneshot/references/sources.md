# Source Notes

This skill was designed from current first-party and open-standard guidance available in August 2026.

## Agent Skills standard

- Agent Skills specification: https://agentskills.io/specification
  - A skill is a directory containing `SKILL.md`, with optional `scripts/`, `references/`, and `assets/`.
  - `name` and `description` are required.
  - Progressive disclosure keeps the core skill concise and loads supporting resources only when needed.

- Agent Skills best practices: https://agentskills.io/skill-creation/best-practices
  - Keep `SKILL.md` focused and moderately detailed.
  - Match prescriptiveness to task fragility.
  - Reference supporting files with explicit instructions for when to read them.

- Agent Skills evaluation guide: https://agentskills.io/skill-creation/evaluating-skills
  - Test skills with realistic prompts, expected outcomes, assertions, and human review.

## OpenAI guidance

- Build skills for Codex: https://developers.openai.com/codex/build-skills
  - Codex supports the open Agent Skills standard and loads repository- and user-scoped skills.
  - Skill descriptions are important routing signals.

- Skills in the OpenAI API: https://developers.openai.com/api/docs/guides/tools-skills
  - Skills are reusable file bundles anchored by `SKILL.md` and may include scripts, references, and assets.

- Codex best practices: https://developers.openai.com/codex/learn/best-practices
  - Repeatable workflows belong in skills.
  - Strong agent work includes testing and review rather than code generation alone.

- OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
  - Favor lean prompts, state each instruction once, define autonomy and approval boundaries, and specify goal, evidence, success criteria, and output format.

- OpenAI reasoning best practices: https://developers.openai.com/api/docs/guides/reasoning-best-practices
  - Use direct instructions and clear delimiters.
  - Do not require exposed chain-of-thought reasoning.

- OpenAI prompt engineering guide: https://developers.openai.com/api/docs/guides/prompt-engineering
  - Clear context, constraints, examples where needed, and output formats improve consistency.

- Harness engineering: https://openai.com/index/harness-engineering/
  - Long-horizon agent work benefits from legible environments, structured repository knowledge, enforceable architecture, tests, and feedback loops.
  - A giant monolithic instruction manual can crowd out relevant task context.

- Evaluating skills: https://developers.openai.com/blog/eval-skills
  - Evaluate both deterministic outcomes and qualitative conventions across representative tasks.

## Anthropic guidance

- Prompt engineering overview: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
  - Begin with clear success criteria and use prompt structure appropriate to the task.

- Define success criteria and evaluations: https://docs.anthropic.com/en/docs/build-with-claude/develop-tests
  - Good criteria are specific, measurable, achievable, and relevant.

- Claude Code skills: https://docs.anthropic.com/en/docs/claude-code/skills
  - Claude Code follows the open Agent Skills standard.
  - Supporting files should be referenced from `SKILL.md` and loaded on demand.

## OpenCode and GitHub distribution

- OpenCode Agent Skills: https://opencode.ai/docs/skills/
  - OpenCode discovers skills in `.opencode/skills/`, `.agents/skills/`, and `.claude/skills/` at project and user scope.
  - OpenCode loads skill name and description first, then the full skill on demand.

- OpenCode rules: https://opencode.ai/docs/rules/
  - Repository-level `AGENTS.md` files provide persistent project guidance for coding-agent sessions.

- GitHub CLI skill publishing: https://cli.github.com/manual/gh_skill_publish
  - `gh skill publish` validates locally discovered Agent Skills, can add the `agent-skills` topic, and creates a versioned GitHub release.
  - The skill commands are preview functionality and should be checked against installed command help before automation.

- GitHub CLI skill installation: https://cli.github.com/manual/gh_skill_install
  - Public skills can be installed from GitHub repositories into agent-specific project or user locations.
