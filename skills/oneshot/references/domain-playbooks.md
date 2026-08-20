# Domain Playbooks

Load only the sections relevant to the request. These are coverage guides, not mandatory checklists for every prompt.

## 1. Serious software and application development

Research:

- Current framework and runtime support.
- Official APIs and package versions.
- Existing repository conventions.
- Deployment environment.
- Security and privacy obligations.
- Testing and browser or platform support.

Prompt coverage:

- Product outcome and user journeys.
- Workspace inspection and preservation rules.
- Architecture and subsystem boundaries.
- Data model and persistence.
- API and integration contracts.
- UI, responsive behavior, accessibility, and states.
- Authentication and authorization if required.
- Input validation and error handling.
- Security, secrets, privacy, and abuse prevention.
- Performance and observability.
- Migrations and backward compatibility.
- Unit, integration, end-to-end, and visual tests.
- Build, deployment, documentation, and handoff.

Quality rules:

- Prefer a working vertical slice before broad scaffolding.
- Require actual build and runtime checks.
- Do not let tests be replaced by comments or mental review.
- Do not invent backend or cloud services the environment cannot access.
- Keep dependencies deliberate and pinned when reproducibility matters.

## 2. Serious game development

Research:

- The target engine, renderer, platform, and current APIs.
- Hardware and browser constraints.
- Comparable games at the level of systems and player experience.
- Physics, rendering, procedural-generation, AI, audio, and save approaches.
- Asset licensing and intellectual-property boundaries.
- Testing and profiling support in the chosen environment.

Translate inspiration into original design pillars rather than copied expression.

Prompt coverage:

### Product definition

- Genre and camera.
- Target platform.
- Intended session or campaign length.
- Complete initial release boundary.
- Core player fantasy.
- Audience and accessibility target.
- Post-ending or replay behavior where relevant.

### Core loop and progression

- Moment-to-moment actions.
- Resource or ability progression.
- World or level progression.
- Tutorialization.
- Difficulty curve.
- Objective state machine.
- Clear ending or completion condition.

### World and content

- Macro-layout.
- Biomes or levels.
- Landmarks.
- Content minimums.
- Guaranteed progression resources.
- Procedural versus authored responsibilities.
- Boundaries and traversal.
- Environmental storytelling.

### Gameplay systems

- Movement.
- Physics and collision.
- Interaction.
- Inventory.
- Crafting or economy.
- Building.
- Vehicles.
- Combat or noncombat threat model.
- AI and animation.
- Save and recovery.
- Failure and respawn.

### Rendering and technical art

- Visual target.
- Lighting.
- Materials and textures.
- Water, atmosphere, particles, or other signature effects.
- Model-generation or asset pipeline.
- LOD, instancing, batching, culling, and streaming.
- Quality tiers and fallback path.
- Explicit prohibition of placeholder primitives when final quality matters.

### Audio

- Music and ambience.
- Spatial sound.
- Feedback cues.
- Captions.
- Voice or synthesis policy.
- Audio failure fallback.

### User experience

- Title, pause, settings, HUD, inventory, and ending.
- Keyboard, mouse, touch, or gamepad controls.
- Accessibility.
- Onboarding.
- Save indicators and error states.

### Expansion readiness

- Stable IDs.
- Data-driven content registries.
- Separation of simulation and presentation.
- Versioned saves.
- Content-authoring docs.
- Modular subsystems.
- Future networking note if relevant, without implementing fake networking.

### Verification

- Boot test.
- Complete playable path.
- Input and collision tests.
- Save/reload.
- Progression reachability.
- Softlock prevention.
- Visual screenshots.
- Performance diagnostics.
- No uncaught console errors.
- No unauthorized external asset requests.

Scoping rule:

- For a chat-only target, request a bounded playable artifact.
- For a coding agent, request a complete v0.x vertical-slice repository with a beginning, core loop, progression, climax, ending, tests, and documentation.
- Never call an incomplete sandbox a “full game.”

## 3. Web product and frontend design

Research:

- Target browser support.
- Current framework and component APIs.
- Existing brand and product context.
- Accessibility and performance standards.
- Comparable product patterns and user pain.

Prompt coverage:

- Primary users and jobs to be done.
- Information architecture.
- Key flows and states.
- Responsive layouts.
- Empty, loading, error, success, and permission states.
- Keyboard and screen-reader behavior.
- Design tokens and visual direction.
- Distinctive composition rather than generic template defaults.
- Data and API boundaries.
- Performance budgets.
- Browser and visual tests.

## 4. Research reports and decision memos

Research:

- Exact question and decision audience.
- Time window and geography.
- Definitions.
- Primary source availability.
- Conflicting schools of thought.
- Data quality and uncertainty.

Prompt coverage:

- Research question.
- Scope and exclusions.
- Source hierarchy.
- Search and screening method.
- Evidence extraction.
- Citation format.
- Comparison framework.
- Uncertainty and inference labels.
- Executive summary.
- Findings.
- Implications.
- Recommendation criteria.
- Limitations.

Avoid:

- Treating search-result snippets as evidence.
- Mixing publication date with event date.
- Hiding disagreement.
- Recommending before defining criteria.

## 5. Data analysis and automation

Research:

- File formats and schema.
- Data volume.
- Runtime and package availability.
- Privacy and retention constraints.
- Expected failure modes.

Prompt coverage:

- Inputs and source of truth.
- Output schema and destination.
- Validation.
- Missing, malformed, and duplicate data.
- Idempotency.
- Dry-run behavior.
- Logging and audit trail.
- Error recovery.
- Performance.
- Tests with representative fixtures.
- Reproducibility.

For destructive actions, require preview, confirmation, backup, or reversible operations as appropriate.

## 6. Creative writing and media briefs

Research only where factual setting, audience, format, or current platform conventions matter.

Prompt coverage:

- Audience.
- Intended response.
- Genre and tone.
- Point of view.
- Structure and pacing.
- Originality constraints.
- Required motifs and exclusions.
- Length and format.
- Continuity requirements.
- Revision and self-check criteria.

Avoid over-specifying every sentence or visual element. Preserve creative decision space.

## 7. Document and business artifacts

Prompt coverage:

- Artifact type.
- Audience and decision purpose.
- Source documents.
- Required sections.
- Tone and terminology.
- Facts that must be preserved.
- Tables, charts, appendices, or citations.
- Page or word target.
- Review criteria.
- Final file format.

For legal, financial, medical, or regulatory documents, require current authoritative research, jurisdiction or scope, uncertainty, and qualified human review where appropriate.

## 8. Image or visual-generation prompts

Research:

- Target model capabilities.
- Aspect ratios and output limits.
- Reference-image rules.
- Current style and text-rendering capabilities.

Prompt coverage:

- Subject.
- Composition.
- Camera and lens language.
- Lighting.
- Materials.
- Environment.
- Color and mood.
- Motion or stillness.
- Aspect ratio.
- Text requirements.
- Originality and identity constraints.
- What to preserve from references.

Prefer positive visual description over long negative lists.
