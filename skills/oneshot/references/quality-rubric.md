# OneShot Quality Rubric

Score the draft out of 100. Revise any draft below 85. A critical failure blocks delivery regardless of score.

## 1. Target fit — 10 points

- 0–3: Executor is missing or assumed incorrectly.
- 4–7: Executor is named but its environment is only partly reflected.
- 8–10: Prompt is clearly adapted to the executor’s real tools, limits, and operating mode.

Questions:

- Does the prompt distinguish chat-only output from agentic workspace execution?
- Are named tools and capabilities verified?
- Is the requested scope compatible with the target?

## 2. Research grounding — 15 points

- 0–4: Claims are generic, stale, or unsupported.
- 5–10: Some current facts are verified, but important decisions remain weakly grounded.
- 11–15: Load-bearing facts, versions, approaches, and failure modes are supported by current authoritative research.

Questions:

- Were user-provided sources inspected first?
- Are unstable facts dated or versioned?
- Are facts separated from recommendations?
- Did research change the prompt rather than merely decorate the response?

## 3. Outcome clarity — 10 points

- 0–3: The task is aspirational or ambiguous.
- 4–7: Main deliverable is clear but audience, value, or completion boundary is weak.
- 8–10: Outcome, audience, value, deliverables, and completion condition are explicit.

## 4. Scope and feasibility — 10 points

- 0–3: Impossible wishlist or severe mismatch with output limits.
- 4–7: Scope is partly bounded but contains major optional ambiguity.
- 8–10: Scope forms a complete, realistic initial release or artifact with clear non-goals and priorities.

## 5. Instruction architecture — 10 points

- 0–3: Unstructured wall of requirements.
- 4–7: Sections exist but sequencing, hierarchy, or distinctions are inconsistent.
- 8–10: Prompt has a coherent hierarchy, dependency-aware workflow, and no needless repetition.

## 6. Functional completeness — 10 points

- 0–3: Important user journeys or systems are only implied.
- 4–7: Core behavior is present but dependencies or edge states are incomplete.
- 8–10: All Priority 0 behavior, inputs, outputs, states, and dependencies are specified.

## 7. Verification and definition of done — 15 points

- 0–4: “Test it” or “make sure it works” with no evidence.
- 5–10: Some tests exist, but critical requirements lack observable checks.
- 11–15: Every Priority 0 requirement maps to suitable static, automated, runtime, visual, or human inspection evidence.

## 8. Failure resilience and autonomy — 5 points

- 0–1: Prompt relies on repeated clarification or silently fails when an approach breaks.
- 2–3: Basic assumptions and fallback behavior exist.
- 4–5: Decision priorities, recovery, graceful degradation, and honest limitation reporting are explicit.

## 9. Maintainability and expansion — 5 points

- 0–1: Result is disposable or tightly coupled without reason.
- 2–3: Some structure and documentation are requested.
- 4–5: The prompt asks for maintainable boundaries, stable data or interfaces, documentation, and migration strategy where relevant.

Use full points for direct artifacts when maintainability is not relevant and the prompt appropriately omits it.

## 10. Safety, privacy, legality, and originality — 5 points

- 0–1: Material risk is ignored.
- 2–3: Generic warnings exist.
- 4–5: Relevant, concrete safeguards and originality rules are integrated without overwhelming the task.

Use full points when the task has no material risk and the prompt correctly avoids unnecessary policy boilerplate.

## 11. Output discipline and compression — 5 points

- 0–1: Bloated, repetitive, contradictory, or full of placeholders.
- 2–3: Usable but longer or more rigid than needed.
- 4–5: Every major section changes behavior; output format is exact; no placeholders or cargo-cult detail remain.

# Critical failures

Do not deliver a prompt with any of these:

- It performs the underlying task instead of writing the requested prompt.
- It claims extensive research without actually researching.
- It fabricates sources, citations, capabilities, versions, or test results.
- It depends on tools the target executor does not have.
- It contains mutually exclusive output contracts.
- It has no definition of done for a serious task.
- It requires completion that cannot fit the target mode or environment.
- It instructs copied protected assets or close imitation where original work is required.
- It omits a mandatory user constraint.
- It leaves unresolved template placeholders.
- It asks the target to claim success without execution evidence.
- It uses Priority 2 polish to excuse an incomplete core outcome.

# Review questions

Before delivery, answer yes to all relevant questions:

- Can the prompt be pasted into a fresh session and understood?
- Does the first page or first screen establish goal, environment, constraints, and done state?
- Are assumptions explicit?
- Is the result bounded but genuinely complete?
- Are requirements grouped by user journey or subsystem?
- Are priorities clear?
- Does the workflow build working slices?
- Are all critical dependencies ordered correctly?
- Can success be observed rather than asserted?
- Are fallbacks realistic?
- Does the target retain useful judgment where appropriate?
- Has repeated language been removed?
- Is the prompt detailed for a reason?
