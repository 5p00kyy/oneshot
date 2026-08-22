# What "one shot" means in OneShot

This document defines the term precisely for the challenge Library, the Lab site,
and any submitted result. Every manifest and page that uses the phrase "one shot"
must agree with this definition.

## Definition

A **one-shot run** is a single execution attempt driven by **one initial brief**
(the challenge prompt) with **no human follow-up**: no clarifying questions
answered, no additional instructions, no corrections, no extra hints, and no
manual intervention between the start of the run and the executor's final
handoff.

OneShot is an evidence-backed field guide to autonomous work across playable, build, precision, repair, and edge-case briefs. Games are a flagship family, not the scope boundary.

The brief is frozen before the run starts:

- The prompt text is fixed and hashed (`prompt.sha256` in the challenge manifest).
- The executor identity (model plus agent) is recorded before the run.
- The budget declared in the challenge manifest applies to the whole run.

## What is allowed inside a one-shot run

"One shot" constrains **human involvement**. Tool access and machine iteration
are a separate comparison control recorded as `run_lane`:

- **Raw completion** uses one model generation with no tool-mediated inspection,
  visual feedback, repair loop, retry, or human edit. The model may reason and
  revise within that generation.
- **Agentic self-review** may read files, use declared tools or subagents, inspect
  its own output, run tests, capture screenshots, find defects, and repair within
  one fixed wall-clock run.

Both remain one-shot because the initial brief is the only human input. They
measure different systems and must never share a ranking.

## What breaks one-shot status

A run stops being one-shot if any of the following happens:

- A human answers an executor question mid-run or supplies missing decisions.
- A human edits, extends, or rewrites the prompt after execution started.
- A human fixes, touches up, or finishes the artifact after the executor stopped.
- The result is assembled from multiple runs stitched together by a human.

Cherry-picking the best of several independent runs is not forbidden, but each
published result must identify exactly which single run produced it, and every
run that contributed to a published artifact must itself satisfy this definition.

## Relation to the Authoring skill

The Authoring skill (`skills/oneshot/`) produces briefs intended to be consumed
as exactly this kind of one initial brief. The Library stores such briefs as
challenges; the Lab displays them and any evidence-backed results. The definition
above is the contract between the two: authoring output on one side, executable
challenge on the other.

## Where this is enforced

- `library/schemas/challenge-v1.schema.json` fixes `one_shot_policy.human_follow_up`
  to `false` and permits internal model iteration.
- `library/schemas/result-v2.schema.json` requires every current result to declare
  `raw-completion` or `agentic-self-review`.
- `scripts/validate_library.py` rejects manifests that drift from these values.
- `site/src/pages/methodology.astro` restates this definition for readers.

## Playable-result boundary

A browser game result is still an untrusted submitted artifact. The Lab may run accepted HTML after explicit user action, but only in an opaque-origin iframe whose sole sandbox grant is `allow-scripts`, with a restrictive document policy and no privileged parent bridge. The preview is a constrained demonstration, not the verification authority; result claims still come from preserved evaluator evidence. Exact checked-in bytes remain available for inspection, and neither repository acceptance nor the sandbox certifies the code safe.
