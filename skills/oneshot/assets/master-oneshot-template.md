# Master One-Shot Prompt Template

> Authoring note: This is a construction template, not a final prompt. Replace every `<placeholder>`, remove every authoring note, omit irrelevant sections, resolve alternatives, and run the quality rubric before delivery.

# <PROJECT OR TASK TITLE>

## 1. Role

You are acting as <the smallest set of senior roles needed to execute the task well>.

You are responsible for <the complete outcome>, including <critical cross-disciplinary responsibilities>.

Use expert judgment. Optimize in this order:

1. <highest priority>
2. <second priority>
3. <third priority>
4. <optional polish>

## 2. Mission

Create <specific finished artifact or system> for <audience/user> that enables them to <end-to-end outcome>.

The initial release must be <credible bounded product, vertical slice, migration, report, or artifact>, not <likely shallow substitute>.

The result should demonstrate <three to seven defining qualities>.

## 3. Definition of one shot

This is one self-contained user handoff.

You may and should, when your environment supports it:

- Inspect files and repositories.
- Research current official sources.
- Use tools and subagents.
- Create multiple files and artifacts.
- Run commands.
- Launch and inspect the result.
- Test and benchmark.
- Repair failures.
- Iterate internally until the definition of done is met.

Do not interpret “one shot” as <incorrect interpretations relevant to the task>.

Do not stop at planning, scaffolding, a mock-up, or a description when implementation is requested.

## 4. Operating contract

Work autonomously through the complete task.

- Use supplied context before asking for information.
- Resolve noncritical ambiguity with conventional, reversible assumptions.
- Ask only when a missing decision makes a correct or safe result impossible.
- Inspect before editing.
- Verify uncertain APIs and versions against the workspace or official current documentation.
- Implement the critical path before optional breadth.
- Run and inspect the actual artifact, not only source code.
- Repair defects found during verification.
- Preserve user work and avoid destructive actions.
- Report only verification that actually occurred.
- Continue until the definition of done is met or a genuine external blocker is demonstrated.

Do not expose hidden chain-of-thought. Keep private planning private. Record durable decisions in the repository or final artifact where useful.

## 5. Environment and workspace

Target environment:

- Executor: <agent/model class>
- Workspace: <blank repository/existing repository/chat-only/etc.>
- Operating system or runtime: <if material>
- Available tools: <files, shell, browser, web, image generation, etc.>
- Network policy: <allowed/limited/offline>
- Deployment target: <static host/server/device/file export/etc.>
- Output limit: <filesystem handoff/chat response/etc.>

Workspace rules:

- <Inspect repository instructions, lockfiles, build commands, or prior artifacts.>
- <Preserve unrelated changes.>
- <Use existing package manager and conventions where applicable.>
- <Do not rewrite history or perform destructive operations unless explicitly required and safeguarded.>
- <Create exactly one lockfile or other repository-specific invariant.>

If a required capability is unavailable, use <defined fallback> and record the limitation. Do not silently replace the intended product with a decorative simulation.

## 6. Inputs and sources of truth

Use evidence in this order:

1. <User requirements and supplied artifacts.>
2. <Existing repository, data, or project conventions.>
3. <Official current documentation/specifications.>
4. <Named primary research or standards.>
5. <Research-derived recommendations.>
6. Your judgment where evidence is absent.

Required references:

- <reference and what principle to extract>
- <reference and what not to copy>
- <technical source or standard>

When sources conflict, <resolution rule>.

## 7. Product or deliverable definition

### Audience

<Who will use or review the result?>

### Core job or experience

<What should the user be able to accomplish or feel?>

### Initial release boundary

The first release includes:

- <complete capability>
- <complete capability>
- <complete capability>

It deliberately excludes:

- <adjacent feature>
- <future-scale feature>
- <unsupported platform>

### Expansion horizon

Structure the initial result so future work can add <expansions> without replacing <foundational systems>.

Do not postpone any requirement needed for the initial end-to-end outcome.

## 8. Originality, safety, privacy, and legal boundaries

<Include only relevant rules.>

- Preserve high-level principles from references while creating original names, text, visuals, layouts, mechanics, data, and assets.
- Do not reproduce protected expression, confidential material, or third-party assets without permission.
- Treat <data or files> as <privacy classification>.
- Do not transmit <sensitive data> to external services.
- Validate untrusted inputs at <boundaries>.
- Require confirmation or a dry run before <irreversible action>.
- Follow <relevant policy, standard, or user constraint>.

## 9. Required deliverables

Create:

### Runtime or primary artifact

- <artifact/file/application/repository>
- <required output format>
- <deployment or run behavior>

### Source and architecture

- <source directories>
- <configuration>
- <content/data definitions>
- <generated asset source if applicable>

### Quality infrastructure

- <tests>
- <lint/typecheck/build>
- <browser/device/visual checks>
- <CI or reproducibility>

### Documentation

- <README>
- <architecture>
- <content authoring or operations>
- <testing>
- <migration/save format>
- <known limitations>

Do not substitute interface labels, pseudocode, TODOs, or roadmap entries for required functionality.

## 10. Technical or structural foundation

Use <technology/architecture> because <research-grounded reason>.

### Dependency policy

- Reuse existing dependencies when suitable.
- Add a dependency only when it materially improves correctness, maintainability, or performance.
- Verify the actual installed or current API before implementation.
- Pin versions when reproducibility requires it.
- Avoid overlapping packages.
- Document licenses or notices where required.

### Architecture invariants

- <single authoritative state rule>
- <module/layer boundary>
- <dependency direction>
- <runtime validation boundary>
- <persistence ownership>
- <presentation/domain separation>
- <explicit cleanup/disposal>
- <extension mechanism>

Allow local implementation freedom inside these invariants.

## 11. User journey or execution flow

The primary path is:

1. <entry>
2. <first meaningful action>
3. <core loop or processing step>
4. <progression or transformation>
5. <completion>
6. <post-completion behavior>

For each stage, define:

- Preconditions.
- User action or input.
- System behavior.
- State change.
- Feedback.
- Failure and recovery.
- Acceptance evidence.

## 12. Functional requirements

### <Capability A>

Purpose: <why it exists>.

Required behavior:

- <trigger/input>
- <processing or interaction>
- <state change>
- <feedback>
- <persistence>
- <failure behavior>

Acceptance:

- <observable check>

### <Capability B>

<Repeat only for meaningful capabilities.>

## 13. Data, state, content, or asset model

Define:

- Stable identifiers.
- Schema or typed records.
- Validation.
- Relationships.
- Ownership.
- Persistence.
- Versioning and migration.
- Critical-item protection.
- Generated-output traceability.
- Authoring or extension path.

Required registries or entities:

- <entity/category and purpose>
- <entity/category and purpose>

Do not scatter user-facing text, content definitions, or schema knowledge across unrelated implementation files.

## 14. Nonfunctional requirements

### Performance

- Target: <device, resolution, throughput, latency, or frame rate>.
- Budget: <draw calls, memory, request latency, file size, etc.>
- Measurement: <diagnostics or benchmark>.
- Degradation: <quality tiers or fallback that preserves functionality>.

### Accessibility

- <keyboard/navigation>
- <captions/text equivalents>
- <contrast/color independence>
- <motion/flash controls>
- <screen-reader/semantic structure>
- <device-specific accessibility>

### Security and privacy

- <authentication/authorization>
- <input validation>
- <secret handling>
- <logging/redaction>
- <rate limits or abuse prevention>
- <data retention>

### Reliability and recovery

- <error surface>
- <retry/idempotency>
- <offline or persistence fallback>
- <corrupt state handling>
- <context/device loss>

### Maintainability

- <strict typing>
- <file/module size or responsibility>
- <tests>
- <documentation>
- <extension points>
- <generated-file policy>

Include only applicable subsections.

## 15. Visual, interaction, or editorial direction

<Use for visual or creative work.>

Define concrete properties:

- Composition and hierarchy.
- Color relationships.
- Typography character.
- Material and texture.
- Motion.
- Density and whitespace.
- Lighting or atmosphere.
- Interaction feedback.
- Avoided clichés.

Translate words such as “modern,” “cinematic,” “premium,” or “polished” into observable design choices.

## 16. Content breadth

<Use only when counts enforce meaningful variety.>

Implement at least:

- <count and distinct-purpose condition>
- <count and distinct-purpose condition>

Do not satisfy counts with cosmetic duplicates. Each item must differ in <behavior, purpose, source, visual identity, data, or outcome>.

## 17. Failure prevention and recovery

Prevent:

- <critical soft lock or dead end>
- <data loss>
- <invalid state>
- <unreachable content>
- <silent failure>
- <destructive default>
- <success-shaped fallback>

Guarantee:

- <required resource/data/input availability>
- <reversible or retryable action>
- <critical state persistence>
- <safe recovery location or rollback>
- <diagnostic error message>

When output, time, or context pressure occurs, simplify Priority 2 work. Do not truncate the critical path or produce an invalid artifact.

## 18. Implementation sequence

Work depth-first.

### Phase 0 — Inspect and validate environment

Implement:

- <inspection>
- <baseline configuration>
- <minimal build/test harness>

Gate:

- <command or observable proof>

### Phase 1 — Thin complete foundation

Implement:

- <boot or entry>
- <primary skeleton>
- <first runnable path>

Gate:

- <observable proof>

### Phase 2 — Core loop

Implement:

- <core capability>
- <state and feedback>
- <first persistence or output>

Gate:

- <end-to-end scenario>

### Phase 3 — Major dependent system

<Continue in dependency order.>

### Final phase — Polish and release

Implement:

- Performance pass.
- Accessibility pass.
- Documentation.
- CI or reproducibility.
- Visual or runtime inspection.
- Final acceptance sweep.

Gate:

- All Priority 0 checks pass.

Do not begin broad optional content while the current gate is broken.

## 19. Priority order

### Priority 0 — Never cut

- <complete critical path>
- <verification>
- <persistence or final output>
- <safety/recovery>

### Priority 1 — Strongly required

- <quality and breadth>

### Priority 2 — Cut first

- <optional polish>

When forced to reduce scope, remove breadth before coherence and polish before function.

## 20. Testing and verification

Run the strongest applicable checks:

### Static or mechanical

- <format/lint/typecheck/schema/build>

### Unit

- <deterministic logic>

### Integration

- <subsystem boundaries, persistence, external integration>

### End to end

- <primary user journey>
- <failure path>
- <save/reload or rollback>

### Visual or device inspection

- <browser/device launch>
- <screenshots or visual comparison>
- <responsive states>
- <audio or interaction inspection>

### Accessibility

- <automated checks>
- <keyboard/manual check>

### Performance

- <metric and threshold>

### Source or research integrity

- <citation-to-claim audit>
- <current-version check>

Do not treat a passing type check as proof that an interactive artifact works.

## 21. Acceptance tests

Before finishing, verify:

### Boot and entry

- <observable checks>

### Core journey

- <observable checks>

### State and persistence

- <observable checks>

### Failure and recovery

- <observable checks>

### Quality

- <observable checks>

### Release

- <clean install/build/run or export checks>

Every Priority 0 requirement must appear in at least one acceptance check.

## 22. Completion ledger

Before handoff, reconcile every planned item as:

- Done and verified.
- Deliberately cut under the stated priority policy.
- Blocked by a specific external constraint with evidence.

Do not finish with unexamined pending items.

## 23. Final response contract

After completing the work, respond with:

### Built

- <brief description>
- <major working capabilities>

### Run or access

- <exact commands, path, or link>

### Verification

- Commands or checks actually run.
- Real result.
- Environment or backend tested.

### Key locations

- <source entry>
- <content or data definitions>
- <tests>
- <documentation>
- <generated outputs>

### Remaining limitations

- Only genuine noncritical limitations.
- Do not describe missing Priority 0 work as a future enhancement.
- Do not conceal failed tests.

Do not paste large repository files into the handoff when the user shares the workspace.

## 24. Definition of done

The task is complete only when:

- <end-to-end outcome exists>
- <critical user journey works>
- <required state persists or output is valid>
- <failure recovery works>
- <tests pass>
- <artifact was actually inspected>
- <documentation matches behavior>
- <no unresolved placeholders or core TODOs remain>

## 25. Final directive

Execute the complete task now.

Do not restate this specification.

Do not stop at planning or scaffolding.

Inspect, research, implement, run, inspect, test, repair, and hand off the finished result.
