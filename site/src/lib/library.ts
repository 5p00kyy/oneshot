import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";

/**
 * Loads the checked-in challenge/result manifests at build time. The Python
 * validator is the authority and is invoked here, so `astro build` cannot
 * bypass the same fail-closed contract used by CI. Local reads then repeat the
 * path/file/hash checks needed before touching prompt bytes.
 */

function findRepositoryRoot(): string {
  const cwd = realpathSync(process.cwd());
  for (const candidate of [cwd, dirname(cwd)]) {
    if (
      existsSync(join(candidate, "library", "schemas", "challenge-v1.schema.json")) &&
      existsSync(join(candidate, "scripts", "validate_library.py"))
    ) {
      return candidate;
    }
  }
  return fail("repository root not found from the site build working directory");
}

const REPOSITORY_ROOT = findRepositoryRoot();
export const LIBRARY_ROOT = join(REPOSITORY_ROOT, "library");

function validateLibraryForBuild(): void {
  try {
    execFileSync(
      "python3",
      [join(REPOSITORY_ROOT, "scripts", "validate_library.py"), "--library-dir", LIBRARY_ROOT],
      { cwd: REPOSITORY_ROOT, encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] },
    );
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`[library] authoritative validation failed before site build: ${detail}`);
  }
}

validateLibraryForBuild();

export interface PromptRef {
  path: string;
  sha256: string;
}

export interface EvaluatorRef {
  path: string;
  sha256: string;
  runtime: string;
  notes: string;
}

export interface LicenseRef {
  spdx: string | null;
  label: string;
  url?: string;
}

export interface Provenance {
  source_url?: string;
  source_published?: string;
  license: LicenseRef;
  attribution: string;
  notes?: string;
}

export interface Capabilities {
  environment: string;
  tools?: string[];
  skills: string[];
  constraints?: string[];
}

export interface Budget {
  wall_clock_minutes?: number | null;
  output_files_max?: number | null;
  network_access?: string;
  notes: string;
}

export interface VerificationItem {
  id: string;
  method: string;
  description: string;
  evidence_required: string[];
}

export interface ArtifactSpec {
  path: string;
  kind: string;
  required: boolean;
  description: string;
}

export interface OneShotPolicy {
  human_follow_up: boolean;
  internal_iteration: boolean;
  notes: string;
}

export interface Challenge {
  schema: string;
  id: string;
  version: string;
  title: string;
  category: string;
  family: string;
  tier: string;
  prompt_profile: string;
  benchmark_question: string;
  capability_dimensions: string[];
  status: string;
  origin: string;
  summary: string;
  prompt: PromptRef;
  evaluator?: EvaluatorRef;
  provenance: Provenance;
  capabilities: Capabilities;
  execution_lane: string;
  budget: Budget;
  verification: VerificationItem[];
  artifacts: ArtifactSpec[];
  one_shot_policy: OneShotPolicy;
}

export interface ChallengeView extends Challenge {
  promptText: string;
  index: string;
}

export interface ResultView {
  id: string;
  challenge_id: string;
  challenge_version: string;
  run_class: string;
  run_lane: string;
  status: string;
  claim_passed: boolean;
  claim_summary: string;
  executor_summary: string;
  model_name: string;
  model_version: string | null;
  model_snapshot: string | null;
  agent_name: string;
  agent_version: string | null;
  agent_profile: string | null;
  executed_at: string;
  artifacts: Array<{
    path: string;
    sha256: string;
    kind: string;
    description?: string;
    download_url: string;
  }>;
  criterion_outcomes: Array<{
    id: string;
    passed: boolean;
    evidence_refs: string[];
    notes: string;
  }>;
  criteria_passed: number;
  criteria_total: number;
  evidence_count: number;
  reproducibility_status: string;
  review_notes: string | null;
  wall_clock_minutes: number | null;
  output_files: number | null;
  preview_data_url: string | null;
  interactive_document_base64: string | null;
  preview_alt: string;
  repository_url: string;
}

function fail(message: string): never {
  throw new Error(`[library] ${message}`);
}

function requireString(value: unknown, where: string): string {
  if (typeof value !== "string" || value.length === 0) fail(`${where} must be a non-empty string`);
  return value;
}

function readCheckedFile(base: string, relativePath: string, where: string): Buffer {
  if (
    !relativePath ||
    isAbsolute(relativePath) ||
    relativePath.includes("\\") ||
    relativePath.includes(":") ||
    relativePath.split("/").includes("..")
  ) {
    fail(`${where} is not a safe relative path`);
  }
  const baseReal = realpathSync(base);
  const candidate = resolve(baseReal, relativePath);
  const lexical = relative(baseReal, candidate);
  if (lexical === ".." || lexical.startsWith(`..${sep}`) || isAbsolute(lexical)) {
    fail(`${where} escapes its challenge directory`);
  }
  let status;
  try {
    status = lstatSync(candidate);
  } catch {
    return fail(`${where} file is missing`);
  }
  if (status.isSymbolicLink() || !status.isFile()) fail(`${where} must be a regular non-symlink file`);
  const candidateReal = realpathSync(candidate);
  const resolvedRelative = relative(baseReal, candidateReal);
  if (resolvedRelative === ".." || resolvedRelative.startsWith(`..${sep}`) || isAbsolute(resolvedRelative)) {
    fail(`${where} resolves outside its challenge directory`);
  }
  return readFileSync(candidateReal);
}

function parseChallenge(id: string, raw: string): Challenge {
  let doc: unknown;
  try {
    doc = JSON.parse(raw);
  } catch (error) {
    return fail(`challenge ${id}: invalid JSON (${String(error)})`);
  }
  const doc_ = doc as Record<string, any>;
  if (doc_.schema !== "oneshot.challenge/v1") fail(`challenge ${id}: unsupported schema`);
  for (const field of [
    "id",
    "version",
    "title",
    "category",
    "family",
    "tier",
    "prompt_profile",
    "benchmark_question",
    "status",
    "origin",
    "summary",
    "execution_lane",
  ] as const) {
    requireString(doc_[field], `challenge ${id}.${field}`);
  }
  if (doc_.id !== id) fail(`challenge ${id}: manifest id mismatch`);
  if (!doc_.prompt || typeof doc_.prompt.path !== "string") fail(`challenge ${id}: prompt.path missing`);
  if (!/^[0-9a-f]{64}$/.test(String(doc_.prompt.sha256))) fail(`challenge ${id}: prompt.sha256 invalid`);
  if (!Array.isArray(doc_.capability_dimensions) || doc_.capability_dimensions.length === 0)
    fail(`challenge ${id}: capability_dimensions must be a non-empty array`);
  if (!Array.isArray(doc_.verification) || doc_.verification.length === 0)
    fail(`challenge ${id}: verification must be a non-empty array`);
  if (!Array.isArray(doc_.artifacts) || doc_.artifacts.length === 0)
    fail(`challenge ${id}: artifacts must be a non-empty array`);
  return doc_ as Challenge;
}

function listChallengeDirectories(): string[] {
  const base = join(LIBRARY_ROOT, "challenges");
  if (!existsSync(base)) fail("library/challenges not found; run from site/ with ../library present");
  return readdirSync(base).sort();
}

export function loadChallenges(): ChallengeView[] {
  const loaded: ChallengeView[] = [];
  for (const dir of listChallengeDirectories()) {
    const manifestPath = join(LIBRARY_ROOT, "challenges", dir, "challenge.json");
    if (!existsSync(manifestPath)) continue;
    const challenge = parseChallenge(dir, readFileSync(manifestPath, "utf-8"));
    const promptBytes = readCheckedFile(
      join(LIBRARY_ROOT, "challenges", dir),
      challenge.prompt.path,
      `challenge ${dir}.prompt.path`,
    );
    const actualHash = createHash("sha256").update(promptBytes).digest("hex");
    if (actualHash !== challenge.prompt.sha256) fail(`challenge ${dir}: prompt.sha256 mismatch`);
    loaded.push({
      ...challenge,
      promptText: promptBytes.toString("utf-8"),
      index: "",
    });
  }
  if (loaded.length === 0) fail("no challenge manifests found");
  // Open active records first, then candidates and retired records. Within a
  // status, show the comparative core before the separate showcase board.
  loaded.sort((a, b) => {
    const statusRank: Record<string, number> = { active: 0, draft: 1, retired: 2 };
    const tierRank: Record<string, number> = { atom: 0, compact: 1, bounded: 2, showcase: 3 };
    return (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) ||
      (tierRank[a.tier] ?? 9) - (tierRank[b.tier] ?? 9) ||
      a.id.localeCompare(b.id);
  });
  loaded.forEach((challenge, position) => {
    challenge.index = String(position + 1).padStart(2, "0");
  });
  return loaded;
}

export function loadResults(): ResultView[] {
  const base = join(LIBRARY_ROOT, "results");
  if (!existsSync(base)) return [];
  const results: ResultView[] = [];
  for (const dir of readdirSync(base).sort()) {
    const manifestPath = join(base, dir, "result.json");
    if (!existsSync(manifestPath)) continue;
    let doc: Record<string, any>;
    try {
      doc = JSON.parse(readFileSync(manifestPath, "utf-8"));
    } catch {
      return fail(`result ${dir}: invalid JSON`);
    }
    if (!["oneshot.result/v1", "oneshot.result/v2"].includes(doc.schema)) fail(`result ${dir}: unsupported schema`);
    const model = doc.executor?.model?.name ?? "unknown model";
    const agent = doc.executor?.agent?.name ?? "unknown agent";
    const resultBase = join(base, dir);
    const artifactRecords = Array.isArray(doc.artifacts) ? doc.artifacts : [];
    const artifacts = artifactRecords.map((item: any) => ({
      ...item,
      download_url: `https://raw.githubusercontent.com/5p00kyy/oneshot/main/library/results/${encodeURIComponent(dir)}/${item.path
        .split("/")
        .map((segment: string) => encodeURIComponent(segment))
        .join("/")}`,
    }));
    const evidence = Array.isArray(doc.evidence) ? doc.evidence : [];
    const criterionOutcomes = Array.isArray(doc.criterion_outcomes) ? doc.criterion_outcomes : [];
    let preview_data_url: string | null = null;
    let interactive_document_base64: string | null = null;
    const htmlArtifact = artifacts.find((item: any) => item.kind === "html");
    const svgArtifact = artifacts.find((item: any) => item.kind === "svg");
    const screenshot =
      evidence.find((item: any) => item.kind === "screenshot" && item.id === "artifact-preview") ??
      evidence.find((item: any) => item.kind === "screenshot");
    if (svgArtifact) {
      const bytes = readCheckedFile(resultBase, svgArtifact.path, `result ${dir}.artifact.preview`);
      preview_data_url = `data:image/svg+xml;base64,${bytes.toString("base64")}`;
    } else if (screenshot) {
      const bytes = readCheckedFile(resultBase, screenshot.location, `result ${dir}.evidence.preview`);
      const extension = screenshot.location.toLowerCase().split(".").pop();
      const mime = extension === "jpg" || extension === "jpeg" ? "image/jpeg" : extension === "webp" ? "image/webp" : "image/png";
      preview_data_url = `data:${mime};base64,${bytes.toString("base64")}`;
    }
    if (htmlArtifact) {
      const bytes = readCheckedFile(resultBase, htmlArtifact.path, `result ${dir}.artifact.interactive`);
      interactive_document_base64 = bytes.toString("base64");
    }
    results.push({
      id: requireString(doc.id, `result ${dir}.id`),
      challenge_id: requireString(doc.challenge?.id, `result ${dir}.challenge.id`),
      challenge_version: requireString(doc.challenge?.version, `result ${dir}.challenge.version`),
      run_class: requireString(doc.run_class, `result ${dir}.run_class`),
      run_lane: doc.schema === "oneshot.result/v2"
        ? requireString(doc.run_lane, `result ${dir}.run_lane`)
        : (typeof doc.run_lane === "string" && doc.run_lane.length > 0 ? doc.run_lane : "legacy-unspecified"),
      status: requireString(doc.status, `result ${dir}.status`),
      claim_passed: Boolean(doc.claim?.passed),
      claim_summary: requireString(doc.claim?.summary, `result ${dir}.claim.summary`),
      executor_summary: `${model} via ${agent}`,
      model_name: model,
      model_version: doc.executor?.model?.version ?? null,
      model_snapshot: doc.executor?.model?.snapshot_id ?? null,
      agent_name: agent,
      agent_version: doc.executor?.agent?.version ?? null,
      agent_profile: doc.executor?.agent?.profile ?? null,
      executed_at: requireString(doc.executed_at, `result ${dir}.executed_at`),
      artifacts,
      criterion_outcomes: criterionOutcomes.map((outcome: any, index: number) => ({
        id: requireString(outcome.id, `result ${dir}.criterion_outcomes[${index}].id`),
        passed: Boolean(outcome.passed),
        evidence_refs: Array.isArray(outcome.evidence_refs) ? outcome.evidence_refs : [],
        notes: requireString(outcome.notes, `result ${dir}.criterion_outcomes[${index}].notes`),
      })),
      criteria_passed: criterionOutcomes.filter((outcome: any) => Boolean(outcome.passed)).length,
      criteria_total: criterionOutcomes.length,
      evidence_count: evidence.length,
      reproducibility_status: requireString(doc.reproducibility?.status, `result ${dir}.reproducibility.status`),
      review_notes: doc.maintainer_review?.notes ?? null,
      wall_clock_minutes: doc.budget_actual?.wall_clock_minutes ?? null,
      output_files: doc.budget_actual?.output_files ?? null,
      preview_data_url,
      interactive_document_base64,
      preview_alt: `${doc.challenge?.id ?? "OneShot"} artifact preview from ${model}`,
      repository_url: `https://github.com/5p00kyy/oneshot/tree/main/library/results/${encodeURIComponent(dir)}`,
    });
  }
  results.sort((a, b) => b.executed_at.localeCompare(a.executed_at) || a.id.localeCompare(b.id));
  return results;
}

export function loadResult(id: string): ResultView | undefined {
  return loadResults().find((result) => result.id === id);
}

export function withBase(path: string): string {
  const base = import.meta.env.BASE_URL;
  const normalizedBase = base.endsWith("/") ? base : `${base}/`;
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  return `${normalizedBase}${normalizedPath}`;
}
