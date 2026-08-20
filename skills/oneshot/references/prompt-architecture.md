# Prompt Architecture

This reference defines how to compile a serious one-shot prompt without turning it into an unstructured wishlist.

## 1. What a one-shot prompt controls

A strong one-shot prompt controls five layers:

1. **Outcome:** what must exist at the end.
2. **Environment:** where and with what capabilities the work happens.
3. **Decision policy:** how ambiguity and tradeoffs are resolved.
4. **Execution:** the order, gates, and feedback loops used to work.
5. **Evidence:** how completion is verified and reported.

Missing any layer creates predictable failure:

- Outcome without environment produces impossible instructions.
- Environment without decision policy creates clarification loops.
- Requirements without execution creates broad scaffolding.
- Execution without evidence creates premature completion claims.
- Evidence without scope encourages test-passing hacks rather than useful work.

## 2. One-shot modes

### Direct artifact

Use for:

- One file.
- A document.
- A self-contained code artifact.
- A structured response.
- A bounded visual or creative brief.

Emphasize:

- Exact output format.
- Completeness within output limits.
- No omitted sections or placeholders.
- Internal consistency.
- Validation possible without a workspace.

### Agentic workspace build

Use for:

- Repositories.
- Multi-file applications.
- Games.
- Refactors.
- Data pipelines.
- Deployable systems.

Emphasize:

- Workspace inspection.
- Filesystem deliverables.
- Dependency policy.
- Implementation phases.
- Actual execution and tests.
- Runtime or visual inspection.
- Repair loops.
- Documentation and handoff.

### Research and analysis

Use for:

- Market research.
- Technical evaluation.
- Policy analysis.
- Literature review.
- Recommendations.

Emphasize:

- Research question.
- Time window.
- Source hierarchy.
- Inclusion and exclusion rules.
- Evidence extraction.
- Disagreement and uncertainty.
- Citation format.
- Decision-ready synthesis.

### Transformation

Use for:

- Rewriting.
- Migration.
- Conversion.
- Summarization.
- Localization.
- Schema transformation.

Emphasize:

- Source of truth.
- Required preservation.
- Allowed changes.
- Output schema.
- Completeness checks.
- Edge cases and loss prevention.

## 3. Requirement extraction

Transform the user’s language into requirement classes.

| User language | Requirement class | Stronger prompt form |
|---|---|---|
| “modern” | Current architecture | Verify current supported stack and justify choices |
| “beautiful” | Visual quality | Define composition, material, animation, lighting, and inspection criteria |
| “full fledged” | Product scope | Define a complete bounded release with a beginning, core loop, and end |
| “expandable” | Maintainability | Require modular architecture, stable IDs, content registries, docs, and migrations |
| “works well” | Reliability | Define tests, runtime checks, error handling, and recovery |
| “detailed” | Coverage | Include load-bearing systems and dependencies, not repeated adjectives |
| “one shot” | Autonomy | Resolve ambiguity, plan, execute, verify, and hand off from one instruction |

## 4. Section library

Use the sections the task needs. Remove unused sections from the final prompt.

### Identity and responsibility

Define:

- The expertise needed.
- Whether the target is advising, authoring, implementing, or verifying.
- Responsibility for end-to-end completion.

Avoid decorative role lists that do not change behavior.

### Mission

Define:

- The final outcome.
- The user or audience.
- The central value proposition.
- The intended scale and completion time where relevant.

### Operating environment

Define:

- Workspace state.
- Filesystem access.
- Tools.
- Runtime.
- Package manager.
- Browser or execution access.
- Network limits.
- Deployment destination.
- Input files and source-of-truth hierarchy.

### Assumptions and context

State:

- Resolved ambiguities.
- Verified versions or capabilities.
- Existing project constraints.
- Inspiration translated into original principles.
- Facts the target should re-check in its environment.

### Scope and non-goals

Define:

- Mandatory outcome.
- Deliberately excluded features.
- What is postponed rather than faked.
- The boundary between a finished initial release and future expansion.

### Output contract

For direct output, define:

- Exact number and type of artifacts.
- Required opening and ending.
- Formatting.
- Whether commentary is allowed.
- Placeholder policy.
- Length or schema constraints.

For workspace agents, define:

- Files and repository deliverables.
- What must be implemented rather than merely documented.
- Build and deployment outputs.
- Final handoff structure.

### Functional requirements

Describe observable behavior. Organize by system or user journey, not by random idea order.

Use stable counts only where useful. Avoid satisfying counts with superficial duplicates.

### Quality attributes

Select relevant attributes:

- Performance.
- Accessibility.
- Security.
- Privacy.
- Reliability.
- Maintainability.
- Observability.
- Portability.
- Responsiveness.
- Visual and audio quality.
- Data integrity.
- Localization readiness.
- Legal and IP compliance.

### Autonomy and clarification policy

Define:

- Which decisions the target should make independently.
- Which assumptions it should document.
- When it may ask a question.
- How it should behave when tools or information are unavailable.
- Whether progress updates are expected.

### Priority ladder

A useful pattern:

- **Priority 0:** complete, testable core outcome; never cut.
- **Priority 1:** strongly required quality and breadth.
- **Priority 2:** polish removed first under pressure.

Priorities prevent the target from preserving decorative features while core flow is incomplete.

### Execution workflow

For agentic work, use depth-first phases.

Each phase should contain:

- A coherent working slice.
- Actual implementation.
- A gate that can be run or inspected.
- Repair before moving on.

Weak sequence:

1. Scaffold every subsystem.
2. Add placeholders.
3. Integrate at the end.

Stronger sequence:

1. Boot and test harness.
2. One complete user path.
3. Persistence and failure handling.
4. Expand content through established systems.
5. Polish, optimize, document, and release.

### Verification and acceptance tests

Use layered evidence:

- Static validation.
- Unit tests.
- Integration tests.
- Runtime smoke tests.
- Browser or visual inspection.
- Accessibility checks.
- Performance checks.
- Data integrity and migration tests.
- User-journey acceptance tests.

Every Priority 0 requirement should map to at least one observable check.

### Failure recovery

Specify:

- Fallbacks when optional APIs fail.
- Error messages instead of blank output.
- Recovery from interrupted work.
- Safe persistence behavior.
- Softlock prevention.
- Honest handling of unavailable tools.
- What to simplify before abandoning the task.

### Final response contract

For workspace agents, request:

- What was built.
- Exact run commands.
- Checks actually run and real results.
- Key files.
- Genuine noncritical limitations.

Do not let the target paste a whole repository into chat when files are the deliverable.

### Final directive

End with a short execution instruction:

- Build or produce the result now.
- Do not restate the specification.
- Do not stop at planning or scaffolding.
- Verify before declaring completion.

Do not repeat the entire prompt in the final directive.

## 5. Specification density

A prompt is dense when each sentence changes behavior, scope, or verification.

Keep detail that:

- Resolves ambiguity.
- Prevents a known failure.
- Defines an interface.
- Establishes priority.
- Makes quality observable.
- Protects safety, legality, data, or user experience.
- Supports future maintenance.

Remove detail that:

- Repeats an earlier rule.
- Invents arbitrary numbers.
- Dictates an implementation with no benefit.
- Names fashionable tools without need.
- Describes optional polish before the core path.
- Uses adjectives without tests.
- Exists only to make the prompt look large.

## 6. Model adaptation

### Cross-platform default

Use Markdown headings, direct instructions, and a single coherent hierarchy.

### Models that benefit from explicit delimiters

Use descriptive XML-style tags around:

- Instructions.
- Context.
- Examples.
- Inputs.
- Output contract.

Do not nest tags excessively.

### Reasoning models

- State the goal and constraints clearly.
- Request planning and verification, not disclosure of hidden reasoning.
- Avoid micromanaging every thought.
- Give explicit effort, autonomy, and completion expectations where supported.

### Tool-using agents

- Name only verified tools or capability classes.
- Define when to inspect, search, edit, run, test, and capture evidence.
- Require tool results to govern claims.

## 7. Examples

Examples are useful when:

- Output schema is unusual.
- Tone or formatting is hard to describe.
- Edge cases are important.
- Tool invocation must follow a strict pattern.

Use a small set of relevant, diverse examples. Do not include examples that accidentally narrow the task or conflict with the actual request.

## 8. Contradiction patterns to scan

Check for:

- “Exactly one file” and “create a full repository.”
- “No dependencies” and “use framework X.”
- “Offline production” and runtime CDN imports.
- “Do not ask questions” and missing mandatory credentials.
- “Complete game” and an output budget that can only hold a demo.
- “Current latest version” and a hard-coded unverified version.
- “Original work” and instructions to clone protected assets.
- “No external services” and required cloud APIs.
- “Fast loading” and huge uncompressed generated assets.
- “Accessible” and canvas-only menus with no alternative.

## 9. Dependency ordering

Write requirements in dependency-aware order.

Examples:

- Research before architecture selection.
- Data model before UI states that depend on it.
- Core loop before content breadth.
- Save schema before persistence tests.
- Habitat construction before vehicle crafting if the vehicle requires the habitat.
- Authentication before protected workflows.
- Source extraction before synthesis.

The final prompt may describe the product by system, but its execution workflow should respect dependencies.

## 10. Prompt compilation checklist

Before finalizing:

- Identify the one-shot mode.
- Verify the executor.
- State the complete outcome.
- Define environment and source of truth.
- Bound scope.
- Define output contract.
- Organize requirements.
- Add relevant quality attributes.
- Add autonomy policy.
- Add priorities.
- Add workflow and gates if agentic.
- Add verification.
- Add fallbacks.
- Add final handoff.
- Remove placeholders and duplication.
