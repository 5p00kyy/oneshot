# OneShot Anti-Patterns

Use this reference to diagnose ambitious or unusually long prompts.

## 1. The adjective pile

Symptom:

- “Modern, polished, detailed, beautiful, professional, scalable” without observable meaning.

Remedy:

- Translate each adjective into behavior, quality attributes, examples, budgets, or acceptance tests.

## 2. The feature wishlist

Symptom:

- Hundreds of features with no core journey, dependency order, or completion boundary.

Remedy:

- Define the primary user journey, Priority 0, and a finished initial release. Move expansion ideas to non-goals or roadmap.

## 3. Length as quality

Symptom:

- Repeated requirements and prohibitions make the prompt impressive but harder to follow.

Remedy:

- Run a compression pass. Keep only statements that change behavior, priority, interface, or verification.

## 4. False specificity

Symptom:

- Arbitrary counts, budgets, and versions presented as authoritative.

Remedy:

- Use numbers only when research, platform limits, user needs, or testability justify them.

## 5. Version cargo cult

Symptom:

- Pinning a package because it appeared in an example or memory.

Remedy:

- Verify current official support. Pin only for reproducibility. Otherwise instruct the executor to inspect the installed API.

## 6. Imaginary tools

Symptom:

- The prompt tells a chat model to edit a repo, run a browser, deploy, or inspect screenshots without those capabilities.

Remedy:

- Audit the executor. Choose the correct one-shot mode and state minimum required capabilities.

## 7. Scaffolding masquerading as completion

Symptom:

- The target creates directories, interfaces, and placeholder systems, then claims the project is built.

Remedy:

- Require depth-first working slices, real interactions, runtime evidence, and prohibition of placeholder behavior for core requirements.

## 8. One-shot means no iteration

Symptom:

- The prompt prevents the target from testing, repairing, or using tools because the user asked for one shot.

Remedy:

- Clarify that one shot means one initiating instruction. Internal execution may be iterative.

## 9. No-questions absolutism

Symptom:

- “Never ask questions” despite missing credentials, source files, legal jurisdiction, or an output destination.

Remedy:

- Tell the target to resolve low-risk ambiguity and ask only when genuinely blocked. Do not force unsafe guesses.

## 10. Vague verification

Symptom:

- “Make sure it works” or “test thoroughly.”

Remedy:

- Name the checks, environments, user journeys, screenshots, performance signals, and required evidence.

## 11. Test-passing instead of product quality

Symptom:

- The prompt overfocuses on hidden tests or allows hard-coded behavior.

Remedy:

- Combine tests with runtime inspection, user-journey checks, code review, data integrity, and nonfunctional quality.

## 12. Contradictory output contracts

Symptom:

- One file and full repository; no dependencies and a framework; offline and CDN runtime; original and exact clone.

Remedy:

- Choose one primary contract, document deliberate exceptions, and run a contradiction pass.

## 13. Research theatre

Symptom:

- Long source summaries that do not affect the prompt.

Remedy:

- Maintain a fact-to-decision ledger. Remove sources that do not change scope, architecture, or verification.

## 14. Over-constrained implementation

Symptom:

- The prompt dictates every class, file, number, and algorithm despite multiple valid solutions.

Remedy:

- Specify interfaces, invariants, and quality goals. Prescribe internals only where fragility or interoperability demands it.

## 15. Under-specified executor behavior

Symptom:

- The product is detailed, but the agent is not told to inspect, plan, build, test, repair, or hand off.

Remedy:

- Add an execution workflow, gates, progress policy, and final evidence contract.

## 16. Copied inspiration

Symptom:

- The prompt names a reference work and asks for the same map, characters, UI, models, sounds, or story.

Remedy:

- Extract genre principles and emotional goals. Require original names, silhouettes, assets, writing, layout, and expression.

## 17. Missing failure path

Symptom:

- The prompt assumes every API, dependency, save, worker, renderer, or external service succeeds.

Remedy:

- Define graceful fallback, visible error states, safe persistence, and simplification order.

## 18. Decorative accessibility or security

Symptom:

- A heading says “accessible” or “secure” with no behavior.

Remedy:

- Require concrete states, controls, validation, threat handling, automated checks, and human review where appropriate.

## 19. Context dependence

Symptom:

- The final prompt says “as discussed above,” “use that file,” or “same as before.”

Remedy:

- Make the prompt standalone. Embed or precisely reference all required context.

## 20. Premature completion permission

Symptom:

- “Do your best” allows the target to stop with a partial scaffold.

Remedy:

- Define Priority 0, repair loops, fallback simplification, honest limitations, and evidence required before completion.
