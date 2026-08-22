# Calibration profiles

Use this reference to choose proportionate prompt depth without confusing it with execution mode or research depth.

## Three independent dimensions

Select one value from each axis in private:

1. **Prompt depth:** Brief, Benchmark, or Extensive.
2. **Execution mode:** Direct artifact, Agentic workspace build, Research and analysis, or Transformation.
3. **Research depth:** R0 supplied context, R1 verification, R2 synthesis, or R3 high consequence.

Examples:

- Brief + Direct artifact + R0: generate one SVG from a stable description.
- Benchmark + Agentic workspace build + R0: create one frozen single-file microgame for model comparison.
- Extensive + Transformation + R1: migrate a repository while verifying current platform constraints.
- Extensive + Research and analysis + R3: produce a high-consequence decision brief.

No axis determines another. Extensive does not require browsing; R2 does not require a long contestant prompt.

## Scope budget

Before choosing depth, estimate:

- number of deliverables;
- visible interactions or user journeys;
- essential states and recovery paths;
- authored content volume;
- external integrations;
- verification burden;
- likely wall time.

A compact profile is suspect when it contains more than one core loop, more than five essential states, more than two deliverables, or more than one hour of likely work. First remove secondary systems and decorative requirements. Select Extensive only when the remaining coupling or risk justifies it.

## Profile envelopes

### Brief

- One bounded artifact or stable transformation.
- One sentence, one paragraph, or up to four bullets.
- No more than 120 words by default.
- Outcome, essential constraints, exact output, and one self-check.
- R0 by default; no structural-heading quota.

### Benchmark

- One frozen capability question and one complete outcome.
- Normally T0-T2, under 60 minutes, and up to four deliverables.
- Usually 40-350 words for T0-T1; hard cap 700 words.
- Small fixed content and state counts, visible completion, and reset or failure behavior where relevant.
- Contestant prompts exclude scoring, evaluator internals, hidden cases or fixtures, harness procedure, evidence collection, and retry policy. Put those in the manifest or evaluator.
- Artifact behavior such as an in-game score is not evaluation scoring.

### Extensive

- Repository-scale, multi-system, migration, deployment, high-consequence, or tightly coupled work.
- Use a private coverage matrix and only the structural sections that change execution.
- Full structural-category lint and semantic rubric apply.

## Lint contract

`scripts/audit_prompt.py --profile brief|benchmark|extensive` applies common checks for unresolved placeholders, exposed chain of thought, duplication, capability conflicts, and vague unverifiable quality language.

- Brief accepts one sentence and zero headings. More than 120 words produces a warning and fails under `--strict`; likely evaluator-mechanics leakage is rejected mechanically.
- Benchmark accepts sparse headings, enforces the 700-word cap, and rejects leaked evaluation mechanics.
- Extensive alone runs the full structural-category and heading checks. If an Extensive prompt is a benchmark contestant prompt, apply the same evaluator-leakage rule during semantic review; ordinary repository tasks may legitimately mention their own test harness.

Lint is mechanical. A passing score does not replace the profile quality gate.

## Calibration regression cases

1. `Generate an SVG of a pelican riding a bicycle.` remains unchanged as a valid one-sentence Brief.
2. A ten-name-and-tagline request stays under 120 words with no browsing, workflow, or headings.
3. A frozen single-HTML three-lane game receives a Benchmark prompt under 350 words with one loop, start, loss, restart, and no phases.
4. A supplied broken modal receives a bounded Brief repair prompt with edit boundaries and behavior checks, not a rewrite.
5. A TypeScript monolith migration remains Extensive with repository inspection, characterization tests, rollout, rollback, observability, and handoff.
6. Brief lint accepts one sentence and zero headings.
7. Benchmark lint fails above 700 words or when evaluation scoring, evaluator internals, hidden cases, harness procedure, or retry policy leaks into the contestant prompt.
8. Extensive lint retains structural-category checks and strict semantic review.
