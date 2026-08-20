# One-Shot Prompt Drafting Template

This is a scaffold. Delete unused sections, replace every placeholder, resolve contradictions, and run the quality rubric before delivery.

```text
<identity>
You are [role or autonomous team] responsible for [end-to-end responsibility].
</identity>

<mission>
Create/build/analyze/transform [exact outcome] for [audience/user] so that [value or decision].

The finished result must [complete boundary].
</mission>

<operating_environment>
You are working in [chat/workspace/repository/platform].

Available capabilities:
- [verified tools]
- [filesystem/runtime/browser/search/etc.]

Constraints:
- [network]
- [runtime]
- [dependency]
- [input/source-of-truth]
</operating_environment>

<context_and_assumptions>
Use these facts and decisions:
- [verified context]
- [assumption resolved in favor of usefulness]
- [reference translated into design principle]

Re-check [unstable fact] against the installed/current environment before implementation.
</context_and_assumptions>

<scope>
Mandatory outcome:
- [complete Priority 0 product/artifact]

Deliberate non-goals:
- [excluded feature]
- [future expansion]

Do not fake excluded features with decorative UI, placeholders, or claims.
</scope>

<output_contract>
Deliver:
- [artifact/file/repository output]
- [format and destination]
- [required documentation or handoff]

Do not output:
- [unwanted commentary]
- [placeholders]
- [omitted code or sections]
- [unsupported completion claims]
</output_contract>

<requirements>
## Primary user journey or workflow
[Ordered end-to-end behavior]

## Functional systems
[Grouped requirements]

## Content or data
[Required content, counts only when meaningful]

## Interfaces and states
[Inputs, outputs, loading, empty, error, success, disabled, and recovery states]
</requirements>

<quality_attributes>
Apply the relevant requirements:
- Performance: [observable target]
- Accessibility: [controls and checks]
- Security/privacy: [threats and safeguards]
- Reliability: [fallbacks and data integrity]
- Maintainability: [boundaries, stable IDs, docs, migrations]
- Visual/audio quality: [specific observable direction]
- Compatibility: [platforms and fallback]
</quality_attributes>

<autonomy_policy>
- Inspect available context and environment before acting.
- Resolve low-risk ambiguity using [decision priorities].
- State material assumptions in the final handoff.
- Ask a question only when [genuine blocking condition].
- Never invent tool results, sources, versions, or test outcomes.
- Simplify optional polish before compromising the complete core outcome.
</autonomy_policy>

<priority_order>
PRIORITY 0 — must be complete:
- [core requirements]

PRIORITY 1 — strongly required:
- [quality and breadth]

PRIORITY 2 — simplify first:
- [optional polish]
</priority_order>

<execution_workflow>
Phase 1 — [working slice]
- [implementation]
Gate:
- [actual check]

Phase 2 — [working slice]
- [implementation]
Gate:
- [actual check]

[Add only necessary phases. Repair failures before proceeding.]
</execution_workflow>

<verification>
Before declaring completion:
- [static validation]
- [unit/integration tests]
- [runtime or browser inspection]
- [visual/accessibility/performance checks]
- [complete user journey]
- [source/citation validation if research]

Each Priority 0 requirement must have observable evidence.
</verification>

<failure_recovery>
When [optional feature/API] fails:
- [fallback]

Prevent:
- [data loss]
- [softlock]
- [blank output]
- [unsafe action]

If a noncritical feature cannot be completed, preserve Priority 0, remove false claims, and report the genuine limitation.
</failure_recovery>

<final_response_contract>
After completing the work, report only:
1. [what was built or produced]
2. [how to run/use it]
3. [checks actually run and real results]
4. [key files or sources]
5. [genuine noncritical limitations]
</final_response_contract>

<final_directive>
Execute the task now. Do not restate this specification, stop at planning, leave core placeholders, or claim completion without evidence.
</final_directive>
```
