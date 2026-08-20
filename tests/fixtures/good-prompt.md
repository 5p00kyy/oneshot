# Mission

Create a complete command-line migration utility that converts a directory of legacy configuration files into a validated modern format. The result is for maintainers who need a repeatable migration with clear diagnostics, safe rollback, and no manual editing of successful conversions. The executor may inspect the supplied repository, use its terminal, add source files, and run local tests. It must preserve unrelated files and must not contact external services.

# Deliverables and output contract

Produce the implementation, automated tests, concise user documentation, and a final handoff. The command must support a source directory, destination directory, dry-run mode, verbose diagnostics, and an explicit overwrite flag. The final handoff must name files changed, show the commands actually run, report their real outcomes, and identify any remaining noncritical limitation. Do not paste the entire repository into the handoff.

# Scope and constraints

Support the three documented legacy schema versions and emit only the current schema. Validate all input before writing output. Preserve comments where the selected parser supports them; otherwise document that limitation before conversion. Reject path traversal, symbolic-link escapes, malformed data, and destination collisions unless overwrite is explicitly enabled. Use the repository's existing language and package manager. Add no dependency when the standard library or an existing dependency provides the needed behavior.

# Workflow and execution

First inspect the repository conventions, tests, and sample fixtures. Then implement one end-to-end conversion path before adding secondary schema variants. Add transaction-style staging so a failed conversion leaves the destination unchanged. Integrate structured error types and deterministic output ordering. After each functional slice, run the narrowest relevant tests. When an approach fails, diagnose the root cause, repair it, and rerun the failed check before continuing.

# Priorities and fallback behavior

Priority zero is data safety, correct conversion, deterministic output, and a working rollback path. Priority one is clear diagnostics, performance on large directories, and maintainable extension points. Priority two is cosmetic terminal formatting. Simplify color and progress animation first if output or implementation pressure appears. Never remove validation or atomic writes to preserve optional polish.

# Verification and acceptance tests

Add tests for every supported schema, malformed input, mixed-version directories, dry-run behavior, overwrite refusal, rollback after a simulated write failure, path traversal, symbolic-link escape, deterministic ordering, and a directory containing at least one thousand small files. Run formatting, linting, type checking, unit tests, and an integration test against temporary directories. Verify that a second identical migration produces no unintended changes. Completion requires all critical checks to pass in the actual environment, not merely a proposed test plan.

# Handoff

Return a concise summary of the implemented behavior, exact usage examples, changed files, verification commands and outcomes, compatibility assumptions, and any genuine limitation. If a required check cannot run because the environment lacks a tool, state the precise missing capability and provide the safest command the maintainer should run. Do not claim success for unexecuted checks.
