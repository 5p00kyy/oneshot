# Benchmark framework

OneShot uses a compact cross-model core and a separate showcase board. The core is meant to answer a narrow question honestly: what can many different models or agents finish from one frozen brief under the same lane? Showcase challenges answer a different question: how far can a strong executor push a richer build without human follow-up?

A result from one board must not be ranked against a result from the other.

## Why the split exists

The first library mixed two extremes:

- an eight-word SVG prompt that almost any text model can attempt;
- complete browser games requiring physics, authored levels, persistence, accessibility, recovery states, testing, and 120 to 150 minutes of agent work.

The games are useful stress tests, but they are poor baselines. Failure can mean insufficient output budget, weak tool use, broken browser automation, poor planning, or a single unfinished subsystem. Compact tasks leave fewer confounders and make cross-model differences easier to interpret.

## Complexity tiers

| Tier | Board | Intended scope | Prompt guidance | Runtime guidance | Required deliverables |
|---|---|---|---:|---:|---:|
| T0 `atom` | core | One directly observable capability | up to 100 words | 5 to 15 minutes | 1 |
| T1 `compact` | core | One useful artifact or narrow repair | up to 350 words | 20 to 30 minutes | 1 to 2 |
| T2 `bounded` | core | Small multi-state workflow, fixture repair, or microgame | up to 700 words | 45 to 60 minutes | 2 to 4 |
| T3 `showcase` | separate | Rich system or substantial vertical slice | no comparative cap; 2,000 words and 180 minutes are review warnings | 90 to 180 minutes | task-specific |

Prompt length is a diagnostic, not the definition of difficulty. A short prompt can imply a hard task. Tier assignment should use the whole work budget: deliverables, interactions, states, content volume, integrations, verification burden, and likely repair loops.

Gravshift, Loopback, Neon Courier, and Signal Siege are T3 showcase challenges. They remain valuable, but they do not define the baseline board. The compact core will use new OneShot-authored challenges rather than familiar prompts already circulating as informal model tests.

## Prompt-depth profiles

Challenge tier and prompt-writing depth are related but independent:

- `brief`: goal, essential constraints, output contract, and one proportionate self-check. Usually one paragraph or a few bullets.
- `benchmark`: a frozen, self-contained task contract. It states only requirements that affect comparability. Harness controls, scoring details, and hidden evaluator cases stay outside the contestant prompt.
- `extensive`: repository-scale or high-consequence handoff with architecture, dependencies, priorities, phased verification, recovery, and final reporting where those sections materially change execution.

A benchmark prompt should not become extensive merely because the evaluator is rigorous. The evaluator owns the rigor; the executor receives the task.

## Comparable run lanes

OneShot records results by lane. Results are comparable only inside the same lane.

### Raw completion

- one frozen prompt;
- one model response or generation;
- no visual feedback, repair prompt, retry, or human edit;
- fixed output envelope;
- scratch reasoning may occur inside the call, but no external agent loop.

### Agentic self-review

- one frozen prompt and no human follow-up;
- the executor may use declared tools, render or run its work, inspect evidence, and repair within the same run;
- one fixed wall-clock budget;
- no second human-authored prompt or manual correction.

Raw completion measures first-pass model behavior. Agentic self-review measures the model plus its tool loop. Both are useful, but combining them into one leaderboard would be dishonest.

## Standard controls

Every comparative run should preserve:

1. Exact prompt bytes and SHA-256.
2. Model, version or snapshot, provider, agent or harness, and tool profile.
3. Fresh isolated work directory and declared runtime.
4. Network policy and dependency policy.
5. Wall time, output envelope, and termination reason.
6. Artifact hashes, evaluator logs, and controlled screenshots where relevant.
7. Every attempt, including timeout, empty output, invalid output, or policy violation.

Scratch files and internal tests are allowed in agentic runs. `output_files_max` applies to declared deliverables, not disposable working files. Token use, tool calls, and wall time should be published as run metadata, not folded into quality scores unless a task explicitly measures efficiency.

## Scoring

Each task defines a 100-point rubric inside these bands:

| Band | Weight | Evidence |
|---|---:|---|
| Functional correctness | 55 | independent black-box tests, deterministic traces, hidden variants, or exact output checks |
| Robustness | 20 | reset and error paths, malformed input, replay stability, and absence of runtime errors |
| Usability, accessibility, and constraints | 15 | keyboard path, labels, responsive behavior, offline/static checks, and task-specific limits |
| Presentation and documentation | 10 | controlled visual review or concise accurate operating notes |

A result passes only at 80/100 or above and with every critical criterion passing. Publish band scores and criterion outcomes, not only a total.

Visual criteria should use blinded pairwise or rubric review from at least two reviewers when a result is promoted to a comparative board. An LLM judge can assist triage, but its identity and prompt must be recorded and it must not be the only authority for a verified visual score.

## Evidence levels

- **E0 - self-report:** executor claims or model-authored notes. Useful context, never leaderboard-grade.
- **E1 - independent automated:** artifact hash, evaluator log, and exact command or test result.
- **E2 - independent behavioral or visual:** controlled interaction trace and screenshots, plus blinded visual review where relevant.
- **E3 - replicated:** a second evaluator run or independent environment reproduces the material claim.

A verified comparative result needs E1 for objective criteria and E2 for interactive or visual criteria. A README written by the executor is supporting evidence only.

## Original starter battery

The core should launch as a balanced set of OneShot-authored tasks, not a compilation of prompts already used in model launch posts:

| Candidate | Tier | Family | What it isolates |
|---|---|---|---|
| Windline | T1 | playable | deterministic flight-like motion, ordered targets, landing, start/crash/success/restart |
| Sundial Relay | T1 | playable | spatial state, rotation logic, authored solvability, undo/reset |
| Folded Atlas | T0 | precision | SVG typography, hierarchy, alignment, symbols, exact required content |
| Switchgrass Radio | T1 | build | keyboard interaction, tuning state, audio-free feedback, responsive UI |
| Quiet Hours | T1 | repair | diagnosis, focus management, Escape, listener cleanup, minimal edit scope |
| Kiln Ledger | T1 | build | deterministic normalization, deduplication, rejection reasons, exact totals |
| Small Surface Patch | T2 | repair | repository reading, compatibility, hidden tests, minimal change discipline |

`Windline` is the intended community-flight-post response without copying a circulating flight-simulator prompt. It is a side-view paper-glider task with visible thermals, ordered wind chimes, and a rooftop landing. The distinctive mechanic and evaluator are ours.

Candidates become active comparative challenges only after their evaluator exists, the prompt is frozen, a novelty review finds no material prompt/task clone, and at least two independent dry runs show the task is neither trivial nor dominated by harness failure.

Games remain the flagship family, not the whole battery. Windline and Sundial Relay are deliberately small enough that modest models can complete a real loop. The current full games remain T3 demonstrations of sustained autonomous work.

## Community context, not a prompt catalogue

Community posts are useful for learning which artifact shapes expose visible differences: one-file games, small flight scenes, SVG composition, raycasters, simulations, repair fixtures, and interactive utilities. OneShot should study those shapes without republishing the famous prompt or making a cosmetic rename.

Research during this design pass found:

- repeated SVG illustration comparisons;
- compact one-file flight, racing, raycasting, and simulation demos;
- broad one-shot build showcases where participants chose different prompts;
- iterative cozy-flight projects that were not actually one-shot runs.

Those examples support the feasibility of compact artifact tests. They do not become OneShot challenges. Exact prompts and external rankings stay in research notes, not the active library.

No established public prompt called “cozy flight sim” was found. Discoverable cozy-flight examples were mostly iterative builds. Windline therefore uses the underlying capability shape, flight control plus targets and landing, while supplying an original subject, mechanic, completion contract, and evaluator.

## Originality gate

Before activation, every challenge must pass all of these checks:

1. Search the title, distinctive mechanic, and key prompt phrases.
2. Record any close inspirations privately during review.
3. Reject exact prompts, near-paraphrases, and cosmetic reskins of well-known tests.
4. Require an original combination of premise, interaction contract, and evaluation surface.
5. Keep external examples out of the active challenge tree unless preservation itself is the explicit project purpose.
6. Re-run the novelty check before a public version is frozen.

## Publication policy

- Core and showcase results have separate views and no shared rank.
- Active challenges are OneShot originals. Community examples inform task-shape research but are not copied into the library.
- A changed prompt is a new challenge version.
- A changed harness lane is a different comparison group.
- Retries are recorded, not hidden. A retry cannot replace the first attempt on a raw-completion board.
- External prompts carry source and licensing metadata. A link is not a licence grant.
- Failed and disputed attempts remain visible when evidence is safe to publish.
