#!/usr/bin/env node

/**
 * Public black-box evaluator for Windline.
 *
 * Linux execution is fail-closed: the submitted file is copied into a one-file
 * read-only staging mount, Chromium runs as an unprivileged user inside a
 * bubblewrap user/network namespace, and CDP Fetch interception records and
 * rejects every page request except the staged document and data/about/blob
 * URLs. Chromium's own sandbox remains enabled.
 */

import { createHash } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";

const SCHEMA = "oneshot.windline-evaluation/v1";
const WAIT_STEP_MS = 100;
const MAX_ARTIFACT_BYTES = 5 * 1024 * 1024;
const MAX_SNAPSHOT_JSON_BYTES = 256 * 1024;
const MAX_OBSERVATIONS = 200;
const MAX_OBSERVATION_VALUE_BYTES = 4096;
const MAX_STDERR_BYTES = 256 * 1024;
const CDP_CALL_TIMEOUT_MS = 5000;
const TOTAL_EVALUATOR_MS = 60000;
// Keep the browser alive after the last interaction so delayed requests and
// exceptions cannot be hidden by a fast final score. This remains bounded by
// TOTAL_EVALUATOR_MS.
const FINAL_QUIET_MS = 5000;
const MAX_SOURCE_BYTES = MAX_ARTIFACT_BYTES;
const MAX_REQUESTS = MAX_OBSERVATIONS;
const MAX_ERRORS = MAX_OBSERVATIONS;
const STAGED_URL = "file:///artifact/index.html";

function usage(message) {
  if (message) console.error(`ERROR: ${message}`);
  console.error("Usage: node evaluate.mjs <index.html> [--out-dir <directory>] [--chromium <path>]");
  process.exit(2);
}

function parseArgs(argv) {
  if (argv.length === 0) usage("missing artifact path");
  const options = { artifact: resolve(argv[0]), outDir: null, chromium: null };
  for (let index = 1; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--out-dir" || flag === "--chromium") {
      const value = argv[index + 1];
      if (!value) usage(`${flag} requires a value`);
      options[flag === "--out-dir" ? "outDir" : "chromium"] = resolve(value);
      index += 1;
    } else {
      usage(`unknown argument: ${flag}`);
    }
  }
  options.outDir ??= resolve(`windline-evaluation-${Date.now()}`);
  return options;
}

function sleep(milliseconds) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, milliseconds));
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function cappedPush(items, value, cap = MAX_OBSERVATIONS) {
  const text = typeof value === "string" ? value : (JSON.stringify(value) ?? String(value));
  const bounded = text.length > MAX_OBSERVATION_VALUE_BYTES
    ? `${text.slice(0, MAX_OBSERVATION_VALUE_BYTES)}…[truncated]`
    : text;
  if (items.length < cap - 1) items.push(bounded);
  else if (items.length === cap - 1) items.push(`[observation cap reached: ${cap}]`);
}

function findChromium(explicit) {
  const candidates = [
    explicit,
    process.env.CHROMIUM,
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
  ].filter(Boolean);
  for (const candidate of candidates) {
    const resolved = resolve(candidate);
    if (existsSync(resolved) && statSync(resolved).isFile()) {
      if (!resolved.startsWith("/usr/")) {
        usage(`secure evaluator requires Chromium beneath /usr; unsupported path: ${resolved}`);
      }
      return resolved;
    }
  }
  usage("Chromium not found; pass --chromium or set CHROMIUM");
}

function findBubblewrap() {
  if (process.platform !== "linux") {
    usage("secure Windline evaluation currently requires Linux with bubblewrap user/network namespaces");
  }
  const candidate = process.env.BWRAP || "/usr/bin/bwrap";
  if (!existsSync(candidate)) {
    usage("secure Windline evaluation requires bubblewrap (bwrap); refusing unsandboxed execution");
  }
  const probe = spawnSync(candidate, [
    "--unshare-user",
    "--unshare-net",
    "--unshare-pid",
    "--unshare-ipc",
    "--unshare-uts",
    "--die-with-parent",
    "--new-session",
    "--cap-drop", "ALL",
    "--ro-bind", "/usr", "/usr",
    "--ro-bind", "/lib", "/lib",
    "--ro-bind", "/lib64", "/lib64",
    "/usr/bin/true",
  ], { encoding: "utf8", timeout: 5000 });
  if (probe.error || probe.status !== 0) {
    const detail = probe.error?.message || probe.stderr?.trim() || `exit ${probe.status}`;
    usage(`bubblewrap user/network namespace unavailable; refusing execution (${detail})`);
  }
  return candidate;
}

function inspectArtifact(path) {
  if (!existsSync(path)) usage(`artifact not found: ${path}`);
  const status = statSync(path);
  if (!status.isFile()) usage("artifact must be a regular file");
  if (status.size > MAX_SOURCE_BYTES) usage(`artifact source exceeds ${MAX_SOURCE_BYTES} byte limit`);
  if (basename(path).toLowerCase() !== "index.html") usage("artifact must be named index.html");
  const bytes = readFileSync(path);
  if (bytes.byteLength > MAX_SOURCE_BYTES) usage(`artifact source exceeds ${MAX_SOURCE_BYTES} byte limit`);
  return { bytes, sha256: sha256(bytes) };
}

class CdpClient {
  constructor(commandStream, responseStream, deadline) {
    this.commandStream = commandStream;
    this.deadline = deadline;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    this.defaultSessionId = null;
    this.buffer = Buffer.alloc(0);
    responseStream.on("data", (chunk) => this.handleData(chunk));
    responseStream.on("close", () => this.close(new Error("CDP pipe closed")));
    responseStream.on("error", (error) => this.close(error));
    commandStream.on("error", (error) => this.close(error));
  }

  handleData(chunk) {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (true) {
      const separator = this.buffer.indexOf(0);
      if (separator < 0) break;
      const raw = this.buffer.subarray(0, separator).toString("utf8");
      this.buffer = this.buffer.subarray(separator + 1);
      if (!raw) continue;
      let message;
      try {
        message = JSON.parse(raw);
      } catch {
        this.close(new Error("invalid JSON received from Chromium CDP pipe"));
        return;
      }
      this.handleMessage(message);
    }
  }

  handleMessage(message) {
    if (message.id) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new Error(message.error.message ?? JSON.stringify(message.error)));
      else pending.resolve(message.result ?? {});
      return;
    }
    for (const listener of this.listeners.get(message.method) ?? []) {
      try {
        listener(message.params ?? {}, message.sessionId ?? null);
      } catch {
        // Listener-owned asynchronous failures are handled by their promises.
      }
    }
  }

  call(method, params = {}, sessionId = this.defaultSessionId) {
    const remaining = this.deadline - Date.now();
    if (remaining <= 0) return Promise.reject(new Error("total evaluator deadline exceeded"));
    const id = this.nextId++;
    const message = { id, method, params };
    if (sessionId) message.sessionId = sessionId;
    return new Promise((resolvePromise, reject) => {
      const timeoutMs = Math.min(CDP_CALL_TIMEOUT_MS, remaining);
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout after ${timeoutMs}ms: ${method}`));
      }, timeoutMs);
      this.pending.set(id, { resolve: resolvePromise, reject, timer });
      try {
        this.commandStream.write(`${JSON.stringify(message)}\0`);
      } catch (error) {
        clearTimeout(timer);
        this.pending.delete(id);
        reject(error);
      }
    });
  }

  callBrowser(method, params = {}) {
    return this.call(method, params, null);
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) ?? [];
    listeners.push(listener);
    this.listeners.set(method, listeners);
  }

  close(error = new Error("CDP client closed")) {
    for (const { reject, timer } of this.pending.values()) {
      clearTimeout(timer);
      reject(error);
    }
    this.pending.clear();
  }
}

async function evaluate(client, expression, sessionId = client.defaultSessionId) {
  const result = await client.call("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  }, sessionId);
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text ?? "page evaluation failed");
  }
  return result.result?.value;
}

async function waitForDocument(client, expectedUrl = STAGED_URL) {
  const deadline = Math.min(client.deadline, Date.now() + 8000);
  while (Date.now() < deadline) {
    try {
      const state = await evaluate(client, `({ready: document.readyState, href: location.href})`);
      if (state?.href === expectedUrl && state.ready === "complete") return;
    } catch {
      // The execution context can be replaced while navigation commits.
    }
    await sleep(50);
  }
  throw new Error(`timed out waiting for ${expectedUrl}`);
}

async function key(client, keyName, holdMs = 60) {
  const codes = {
    Enter: ["Enter", 13],
    ArrowUp: ["ArrowUp", 38],
    ArrowDown: ["ArrowDown", 40],
    KeyP: ["p", 80],
    KeyR: ["r", 82],
  };
  const [keyValue, virtualCode] = codes[keyName] ?? [keyName, 0];
  await client.call("Input.dispatchKeyEvent", {
    type: "keyDown",
    key: keyValue,
    code: keyName,
    windowsVirtualKeyCode: virtualCode,
    nativeVirtualKeyCode: virtualCode,
  });
  await sleep(holdMs);
  await client.call("Input.dispatchKeyEvent", {
    type: "keyUp",
    key: keyValue,
    code: keyName,
    windowsVirtualKeyCode: virtualCode,
    nativeVirtualKeyCode: virtualCode,
  });
}

async function snapshot(client) {
  const serialized = await evaluate(client, `(() => {
    try {
      if (typeof window.__oneshotSnapshot !== "function") return JSON.stringify({__missing:true});
      const json = JSON.stringify(window.__oneshotSnapshot());
      if (typeof json !== "string") return JSON.stringify({__invalid:true});
      if (json.length > ${MAX_SNAPSHOT_JSON_BYTES}) return JSON.stringify({__oversize:true});
      return json;
    } catch (error) {
      return JSON.stringify({__error:String(error)});
    }
  })()`);
  if (typeof serialized !== "string" || Buffer.byteLength(serialized) > MAX_SNAPSHOT_JSON_BYTES) {
    return { __oversize: true };
  }
  try {
    return JSON.parse(serialized);
  } catch {
    return { __invalid: true };
  }
}

async function screenshotFingerprint(client) {
  const shot = await client.call("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
  });
  return sha256(Buffer.from(shot.data, "base64"));
}

async function snapshotSurface(client) {
  return Boolean(await evaluate(client, `(() => {
    const fn = window.__oneshotSnapshot;
    if (typeof fn !== "function" || fn.length !== 0) return false;
    const inspect = (root) => {
      const objects = [];
      const visit = (value) => {
        if (typeof value === "function" || typeof value === "symbol" || typeof value === "bigint") return false;
        if (!value || typeof value !== "object") return true;
        if (objects.includes(value)) return false;
        objects.push(value);
        const proto = Object.getPrototypeOf(value);
        if (proto !== Object.prototype && proto !== Array.prototype && proto !== null) return false;
        for (const key of Reflect.ownKeys(value)) {
          if (typeof key === "symbol") return false;
          const descriptor = Object.getOwnPropertyDescriptor(value, key);
          if (!descriptor || descriptor.get || descriptor.set || !visit(descriptor.value)) return false;
        }
        return true;
      };
      return visit(root) ? objects : null;
    };
    try {
      const first = fn();
      const firstObjects = inspect(first);
      if (!firstObjects) return false;
      const before = JSON.stringify(first);
      const second = fn();
      const secondObjects = inspect(second);
      if (!secondObjects || before !== JSON.stringify(second)) return false;
      const firstSet = new Set(firstObjects);
      if (secondObjects.some((value) => firstSet.has(value))) return false;
      const third = fn();
      return JSON.stringify(second) === JSON.stringify(third);
    } catch {
      return false;
    }
  })()`));
}

async function restartFlying(client) {
  await key(client, "KeyR");
  await sleep(150);
  let value = await snapshot(client);
  if (value?.phase === "start") {
    await key(client, "Enter");
    await sleep(150);
    value = await snapshot(client);
  }
  return value;
}

function finiteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function unitSigned(value) {
  return finiteNumber(value) && value >= -1 && value <= 1;
}

const MAX_DESCRIPTION_NODES = 256;

function jsonSafe(value, state = { nodes: 0 }, depth = 0) {
  if (state.nodes++ > MAX_DESCRIPTION_NODES || depth > 12) return false;
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (finiteNumber(value)) return true;
  if (typeof value !== "object") return false;
  if (Array.isArray(value)) return value.every((item) => jsonSafe(item, state, depth + 1));
  return Object.keys(value).every((key) => key.length <= 128 && jsonSafe(value[key], state, depth + 1));
}

function nonemptyDescription(value) {
  if (!jsonSafe(value)) return false;
  if (Array.isArray(value)) return value.length > 0;
  return value !== null && typeof value === "object" && Object.keys(value).length > 0;
}

function finiteAlias(object, aliases) {
  if (!object || typeof object !== "object" || Array.isArray(object)) return null;
  for (const alias of aliases) {
    if (finiteNumber(object[alias])) return object[alias];
  }
  return null;
}

function pointFromDescription(value) {
  if (Array.isArray(value)) {
    return finiteNumber(value[0]) && finiteNumber(value[1]) ? { x: value[0], y: value[1] } : null;
  }
  if (!value || typeof value !== "object") return null;
  const position = Array.isArray(value.position) ? value.position : value.pos;
  const x = finiteAlias(value, ["x", "cx", "left"]);
  const y = finiteAlias(value, ["y", "cy", "top"]);
  if (x !== null && y !== null) return { x, y };
  if (Array.isArray(position) && finiteNumber(position[0]) && finiteNumber(position[1])) {
    return { x: position[0], y: position[1] };
  }
  return null;
}

function rectFromDescription(value) {
  if (Array.isArray(value)) {
    return [0, 1, 2, 3].every((index) => finiteNumber(value[index])) && value[2] > 0 && value[3] > 0
      ? { x: value[0], y: value[1], width: value[2], height: value[3] }
      : null;
  }
  if (!value || typeof value !== "object") return null;
  const point = pointFromDescription(value);
  const width = finiteAlias(value, ["width", "w"]);
  // `strength` is accepted only as a compact positive extent alias. The
  // evaluator does not assign semantic meaning to undocumented extra keys.
  const height = finiteAlias(value, ["height", "h", "strength"]);
  return point && width !== null && height !== null && width > 0 && height > 0
    ? { x: point.x, y: point.y, width, height }
    : null;
}

function collectionDescriptions(value, count, tupleSize) {
  if (Array.isArray(value)) {
    if (value.length === count && value.every(nonemptyDescription)) return value;
    if (value.length === count * tupleSize && value.every(finiteNumber)) {
      return Array.from({ length: count }, (_, index) => value.slice(index * tupleSize, (index + 1) * tupleSize));
    }
    return null;
  }
  if (!value || typeof value !== "object") return null;
  for (const alias of ["items", "values", "entries", "points", "rectangles"]) {
    if (Object.prototype.hasOwnProperty.call(value, alias)) {
      const nested = collectionDescriptions(value[alias], count, tupleSize);
      if (nested) return nested;
    }
  }
  const members = Object.values(value).filter((item) => item && typeof item === "object");
  return members.length === count && members.every(nonemptyDescription) ? members : null;
}

function chimeDescriptions(value) {
  return collectionDescriptions(value, 3, 2);
}

function thermalDescriptions(value) {
  return collectionDescriptions(value, 2, 4);
}

function thermalRectFromDescription(value) {
  const rect = rectFromDescription(value);
  if (rect) return rect;
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const x = finiteAlias(value, ["x", "cx", "left"]);
  const y = finiteAlias(value, ["y", "cy", "top"]);
  const width = finiteAlias(value, ["width", "w"]);
  const strength = finiteAlias(value, ["strength", "height", "h"]);
  // A compact vertical thermal may omit y/height and expose strength instead;
  // accept that semantically equivalent description with a bounded implicit
  // origin/extent, without applying this relaxation to the rooftop pad.
  return x !== null && width !== null && strength !== null && width > 0 && strength > 0
    ? { x, y: y ?? 0, width, height: strength }
    : null;
}

function rooftopDescription(value) {
  return value.rooftop ?? value.rooftop_pad ?? value.pad ?? null;
}

function statusBoolean(value) {
  if (typeof value === "boolean") return value;
  if (typeof value !== "string") return null;
  if (["hit", "rung", "collected", "complete", "completed", "visited"].includes(value.toLowerCase())) return true;
  if (["pending", "unhit", "uncaught", "false"].includes(value.toLowerCase())) return false;
  return null;
}

function inferredProgress(value, chimes = chimeDescriptions(value?.chimes)) {
  if (Number.isInteger(value?.next_chime) && value.next_chime >= 0 && value.next_chime <= 3) return value.next_chime;
  if (value?.next_chime === null && value.phase === "success") return 3;
  if (!chimes || chimes.length !== 3) return null;
  const statuses = chimes.map((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) return null;
    for (const alias of ["hit", "rung", "collected", "complete", "completed", "visited", "status"]) {
      if (Object.prototype.hasOwnProperty.call(item, alias)) {
        const result = statusBoolean(item[alias]);
        if (result !== null) return result;
      }
    }
    return null;
  });
  if (statuses.some((status) => status === null)) return null;
  let progress = 0;
  while (progress < statuses.length && statuses[progress]) progress += 1;
  return statuses.slice(progress).some(Boolean) ? null : progress;
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

function canonicalJson(value) {
  return JSON.stringify(canonicalize(value));
}

function validSnapshot(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  if (!jsonSafe(value)) return false;
  if (value.schema !== "oneshot.windline/v1") return false;
  if (!["start", "flying", "crashed", "success"].includes(value.phase)) return false;
  if (typeof value.paused !== "boolean") return false;
  if (!Object.prototype.hasOwnProperty.call(value, "next_chime")) return false;
  if (!((Number.isInteger(value.next_chime) && value.next_chime >= 0 && value.next_chime <= 3) || value.next_chime === null)) return false;
  if (value.next_chime === null && value.phase !== "success") return false;
  const glider = value.glider;
  if (!glider || ![glider.x, glider.y, glider.vx, glider.vy, glider.pitch].every(finiteNumber)) return false;
  if (glider.x < 0 || glider.x > 1 || glider.y < 0 || glider.y > 1) return false;
  if (![glider.vx, glider.vy, glider.pitch].every(unitSigned)) return false;
  const chimes = chimeDescriptions(value.chimes);
  const thermals = thermalDescriptions(value.thermals);
  const rooftop = rooftopDescription(value);
  return Boolean(
    chimes && chimes.length === 3 && chimes.every((item) => nonemptyDescription(item) && pointFromDescription(item)) &&
    thermals && thermals.length === 2 && thermals.every((item) => nonemptyDescription(item) && thermalRectFromDescription(item)) &&
    nonemptyDescription(rooftop) && rectFromDescription(rooftop),
  );
}

function snapshotProjection(value) {
  return canonicalJson({
    schema: value?.schema,
    phase: value?.phase,
    paused: value?.paused,
    next_chime: value?.next_chime,
    glider: value?.glider ? {
      x: value.glider.x,
      y: value.glider.y,
      vx: value.glider.vx,
      vy: value.glider.vy,
      pitch: value.glider.pitch,
    } : null,
    chimes: value?.chimes,
    thermals: value?.thermals,
    rooftop: rooftopDescription(value),
  });
}

function courseProjection(value) {
  return canonicalJson({
    chimes: value?.chimes,
    thermals: value?.thermals,
    rooftop: rooftopDescription(value),
  });
}

function scoreItem(bands, band, id, points, passed, critical, detail) {
  bands[band].items.push({ id, points, passed, critical, detail });
  if (passed) bands[band].score += points;
}

function effectDelta(before, after, idleBefore, idleAfter) {
  return {
    vy: (after.glider.vy - before.glider.vy) - (idleAfter.glider.vy - idleBefore.glider.vy),
    pitch: (after.glider.pitch - before.glider.pitch) - (idleAfter.glider.pitch - idleBefore.glider.pitch),
  };
}

function opposingEffects(up, down) {
  const epsilon = 0.0001;
  const upMagnitude = Math.abs(up.vy) + Math.abs(up.pitch);
  const downMagnitude = Math.abs(down.vy) + Math.abs(down.pitch);
  const opposed = up.vy * down.vy < -epsilon * epsilon || up.pitch * down.pitch < -epsilon * epsilon;
  return upMagnitude > epsilon && downMagnitude > epsilon && opposed;
}

function freshGliderPair(first, second, initial) {
  if (![first, second, initial].every((value) => value?.glider)) return false;
  const close = (left, right, tolerance) => Math.abs(left - right) <= tolerance;
  return close(first.glider.x, second.glider.x, 0.03) &&
    close(first.glider.y, second.glider.y, 0.03) &&
    close(first.glider.vx, second.glider.vx, 0.25) &&
    close(first.glider.vy, second.glider.vy, 0.25) &&
    close(first.glider.pitch, second.glider.pitch, 0.25) &&
    close(first.glider.x, initial.glider.x, 0.05) &&
    close(first.glider.y, initial.glider.y, 0.05);
}

function sandboxArgs(bwrap, chromium, stage) {
  const args = [
    "--unshare-user",
    "--unshare-net",
    "--unshare-pid",
    "--unshare-ipc",
    "--unshare-uts",
    "--die-with-parent",
    "--new-session",
    "--cap-drop", "ALL",
    "--tmpfs", "/",
    "--proc", "/proc",
    "--dev", "/dev",
    "--ro-bind", "/usr", "/usr",
    "--ro-bind", "/lib", "/lib",
    "--ro-bind", "/lib64", "/lib64",
    "--symlink", "usr/bin", "/bin",
    "--symlink", "usr/sbin", "/sbin",
  ];
  if (existsSync("/etc/fonts")) args.push("--ro-bind", "/etc/fonts", "/etc/fonts");
  if (existsSync("/etc/chromium.d")) args.push("--ro-bind", "/etc/chromium.d", "/etc/chromium.d");
  args.push(
    "--ro-bind", stage, "/artifact",
    "--dir", "/tmp",
    "--dir", "/tmp/home",
    "--dir", "/tmp/profile",
    "--setenv", "HOME", "/tmp/home",
    "--setenv", "XDG_CONFIG_HOME", "/tmp/home/.config",
    "--uid", "65534",
    "--gid", "65534",
    chromium,
    "--headless=new",
    "--disable-background-networking",
    "--disable-breakpad",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-features=Translate,MediaRouter",
    "--disable-gpu",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-first-run",
    "--remote-debugging-pipe",
    "--user-data-dir=/tmp/profile",
    "--window-size=1280,720",
    "about:blank",
  );
  return { command: bwrap, args };
}

async function runBrowser(options, artifactInfo) {
  const chromium = findChromium(options.chromium);
  const bwrap = findBubblewrap();
  const stage = mkdtempSync(join(tmpdir(), "oneshot-windline-stage-"));
  const stagedArtifact = join(stage, "index.html");
  writeFileSync(stagedArtifact, artifactInfo.bytes, { mode: 0o444 });
  chmodSync(stage, 0o555);
  mkdirSync(options.outDir, { recursive: true });

  const runtimeErrors = [];
  const blockedRequests = [];
  const interceptions = new Set();
  const configuredSessions = new Set();
  const deadline = Date.now() + TOTAL_EVALUATOR_MS;
  let child;
  let client;
  let totalDeadlineHit = false;
  let stderr = "";
  let totalTimer;

  const track = (promise) => {
    interceptions.add(promise);
    promise.finally(() => interceptions.delete(promise));
  };

  try {
    const launch = sandboxArgs(bwrap, chromium, stage);
    child = spawn(launch.command, launch.args, {
      stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"],
    });
    child.stderr.on("data", (chunk) => {
      if (stderr.length < MAX_STDERR_BYTES) stderr += String(chunk).slice(0, MAX_STDERR_BYTES - stderr.length);
    });
    totalTimer = setTimeout(() => {
      totalDeadlineHit = true;
      try { child.kill("SIGKILL"); } catch {}
    }, TOTAL_EVALUATOR_MS);

    if (!child.stdio[3] || !child.stdio[4]) throw new Error("Chromium CDP pipes unavailable");
    client = new CdpClient(child.stdio[3], child.stdio[4], deadline);

    const allowedRequest = (url) => {
      if (url === STAGED_URL || url.startsWith(`${STAGED_URL}#`) || url.startsWith(`${STAGED_URL}?`)) return true;
      return url.startsWith("data:") || url.startsWith("about:") || url.startsWith("blob:");
    };

    client.on("Fetch.requestPaused", (params, sessionId) => {
      const url = params.request?.url ?? "";
      const action = allowedRequest(url)
        ? client.call("Fetch.continueRequest", { requestId: params.requestId }, sessionId)
        : (cappedPush(blockedRequests, url || "[missing request URL]", MAX_REQUESTS),
          client.call("Fetch.failRequest", { requestId: params.requestId, errorReason: "BlockedByClient" }, sessionId));
      track(action.catch((error) => cappedPush(runtimeErrors, `request interception failed: ${error.message}`, MAX_ERRORS)));
    });
    client.on("Runtime.exceptionThrown", (params) => {
      cappedPush(runtimeErrors, params.exceptionDetails?.exception?.description ?? params.exceptionDetails?.text ?? "uncaught exception", MAX_ERRORS);
    });
    client.on("Log.entryAdded", (params) => {
      if (params.entry?.level === "error") cappedPush(runtimeErrors, params.entry.text, MAX_ERRORS);
    });

    const configureSubtarget = async (sessionId) => {
      if (!sessionId || configuredSessions.has(sessionId)) return;
      configuredSessions.add(sessionId);
      await Promise.all([
        client.call("Runtime.enable", {}, sessionId),
        client.call("Network.enable", {}, sessionId),
        client.call("Fetch.enable", { patterns: [{ urlPattern: "*", requestStage: "Request" }] }, sessionId),
      ]);
      await client.call("Runtime.runIfWaitingForDebugger", {}, sessionId).catch(() => {});
    };
    client.on("Target.attachedToTarget", (params) => {
      if (params.sessionId) track(configureSubtarget(params.sessionId).catch((error) => cappedPush(runtimeErrors, `target isolation failed: ${error.message}`, MAX_ERRORS)));
    });

    await client.callBrowser("Target.setAutoAttach", {
      autoAttach: true,
      waitForDebuggerOnStart: true,
      flatten: true,
    });
    const targets = await client.callBrowser("Target.getTargets");
    const page = targets.targetInfos?.find((target) => target.type === "page");
    if (!page) throw new Error("Chromium did not expose a page target");
    const attached = await client.callBrowser("Target.attachToTarget", { targetId: page.targetId, flatten: true });
    client.defaultSessionId = attached.sessionId;
    configuredSessions.add(attached.sessionId);
    await Promise.all([
      client.call("Runtime.enable"),
      client.call("Page.enable"),
      client.call("Log.enable"),
      client.call("Network.enable"),
      client.call("Fetch.enable", { patterns: [{ urlPattern: "*", requestStage: "Request" }] }),
    ]);

    await client.call("Page.navigate", { url: STAGED_URL });
    await waitForDocument(client);
    await sleep(250);

    const bands = {
      functional_correctness: { score: 0, max: 55, items: [] },
      robustness: { score: 0, max: 20, items: [] },
      usability_accessibility_constraints: { score: 0, max: 15, items: [] },
      presentation_documentation: { score: 0, max: 10, items: [] },
    };

    const initial = await snapshot(client);
    const surfaceValid = await snapshotSurface(client);
    const snapshotValid = validSnapshot(initial) && initial.phase === "start";
    scoreItem(bands, "functional_correctness", "snapshot-contract", 10,
      snapshotValid && surfaceValid, true,
      snapshotValid && surfaceValid ? "documented start snapshot is normalized, plain, serializable, method-free, and pure" : "snapshot missing, malformed, non-normalized, stateful, or exposes a non-JSON surface");
    scoreItem(bands, "robustness", "snapshot-isolation", 5, surfaceValid, true,
      surfaceValid ? "successive snapshots share no object identities and remain stable at rest" : "snapshot objects are live/shared, stateful, or expose methods/accessors");

    const initialCourse = courseProjection(initial);
    await client.call("Page.reload", { ignoreCache: true });
    await waitForDocument(client);
    await sleep(200);
    const reloadedInitial = await snapshot(client);
    const freshLoadDeterministic = validSnapshot(reloadedInitial) && reloadedInitial.phase === "start" &&
      snapshotProjection(reloadedInitial) === snapshotProjection(initial) &&
      courseProjection(reloadedInitial) === initialCourse && await snapshotSurface(client);

    await key(client, "Enter");
    await sleep(200);
    const started = await snapshot(client);
    const startedFlying = validSnapshot(started) && started.phase === "flying";
    scoreItem(bands, "functional_correctness", "start-state", 5, startedFlying, true,
      `phase after Enter from a verified start state: ${started?.phase ?? "missing"}`);

    let steeringChanged = false;
    let rightwardProgress = false;
    let visualMotion = false;
    let visualSteering = false;
    if (startedFlying) {
      const idleBefore = await restartFlying(client);
      const idleBeforeShot = await screenshotFingerprint(client);
      await sleep(180);
      const idleAfter = await snapshot(client);
      const idleAfterShot = await screenshotFingerprint(client);
      visualMotion = idleBeforeShot !== idleAfterShot;
      rightwardProgress = validSnapshot(idleBefore) && validSnapshot(idleAfter) &&
        idleAfter.glider.x > idleBefore.glider.x + 0.0001 && idleAfter.glider.vx > 0 && visualMotion;

      const upBefore = await restartFlying(client);
      const upBeforeShot = await screenshotFingerprint(client);
      await key(client, "ArrowUp", 180);
      const upAfter = await snapshot(client);
      const upAfterShot = await screenshotFingerprint(client);
      const downBefore = await restartFlying(client);
      const downBeforeShot = await screenshotFingerprint(client);
      await key(client, "ArrowDown", 180);
      const downAfter = await snapshot(client);
      const downAfterShot = await screenshotFingerprint(client);
      if ([idleBefore, idleAfter, upBefore, upAfter, downBefore, downAfter].every(validSnapshot)) {
        const up = effectDelta(upBefore, upAfter, idleBefore, idleAfter);
        const down = effectDelta(downBefore, downAfter, idleBefore, idleAfter);
        steeringChanged = opposingEffects(up, down);
        visualSteering = upBeforeShot !== upAfterShot && downBeforeShot !== downAfterShot &&
          upAfterShot !== downAfterShot;
      }
    }
    const steeringPass = steeringChanged && rightwardProgress && visualSteering;
    scoreItem(bands, "functional_correctness", "keyboard-steering", 10, steeringPass, true,
      `causal opposing steering=${steeringChanged}; visible motion=${visualMotion}; visible opposing response=${visualSteering}; rightward progress=${rightwardProgress}`);

    let pauseStable = false;
    const pauseStart = startedFlying ? await restartFlying(client) : null;
    if (pauseStart?.phase === "flying") {
      await key(client, "KeyP");
      const pausedBefore = await snapshot(client);
      await sleep(400);
      const pausedAfter = await snapshot(client);
      pauseStable = validSnapshot(pausedBefore) && validSnapshot(pausedAfter) && pausedBefore.paused && pausedAfter.paused &&
        canonicalJson(pausedAfter.glider) === canonicalJson(pausedBefore.glider) &&
        pausedAfter.next_chime === pausedBefore.next_chime &&
        canonicalJson(pausedAfter.chimes) === canonicalJson(pausedBefore.chimes);
      await key(client, "KeyP");
    }
    scoreItem(bands, "robustness", "pause-freezes-motion", 5, pauseStable, false,
      pauseStable ? "pause froze documented motion and objective state" : "P did not expose a stable paused state");

    let crashed = false;
    let crashSnapshot = null;
    const crashStart = startedFlying ? await restartFlying(client) : null;
    if (crashStart?.phase === "flying") {
      await key(client, "ArrowDown", 3500);
      const crashDeadline = Math.min(deadline, Date.now() + 3500);
      while (Date.now() < crashDeadline) {
        crashSnapshot = await snapshot(client);
        if (crashSnapshot?.phase === "crashed") { crashed = true; break; }
        await sleep(WAIT_STEP_MS);
      }
      if (!crashed) {
        await key(client, "ArrowUp", 3500);
        const secondDeadline = Math.min(deadline, Date.now() + 3500);
        while (Date.now() < secondDeadline) {
          crashSnapshot = await snapshot(client);
          if (crashSnapshot?.phase === "crashed") { crashed = true; break; }
          await sleep(WAIT_STEP_MS);
        }
      }
    }

    let restarted = false;
    let restartDeterministic = false;
    if (crashed) {
      await key(client, "KeyR");
      await sleep(200);
      const firstRestart = await snapshot(client);
      await key(client, "KeyR");
      await sleep(200);
      const secondRestart = await snapshot(client);
      const freshPhase = (value) => value?.phase === "start" || value?.phase === "flying";
      restarted = validSnapshot(firstRestart) && freshPhase(firstRestart) && inferredProgress(firstRestart) === 0;
      restartDeterministic = restarted && validSnapshot(secondRestart) && freshPhase(secondRestart) &&
        firstRestart.phase === secondRestart.phase && inferredProgress(secondRestart) === 0 &&
        courseProjection(firstRestart) === initialCourse && courseProjection(secondRestart) === initialCourse &&
        freshGliderPair(firstRestart, secondRestart, initial);
    }
    scoreItem(bands, "robustness", "crash-restart", 7, crashed && restarted, true,
      `crash observed=${crashed}; clean start-or-flying restart observed=${restarted}`);
    const deterministic = freshLoadDeterministic && restartDeterministic;
    scoreItem(bands, "robustness", "deterministic-course", 3, deterministic, false,
      `fresh-load geometry stable=${freshLoadDeterministic}; restart geometry stable=${restartDeterministic}`);

    const controlSurface = Boolean(await evaluate(client, `(() => {
      const text = document.body?.innerText?.toLowerCase() ?? "";
      const enabledButtons = [...document.querySelectorAll("button")].filter((item) => !item.disabled);
      const label = (item) => (item.getAttribute("aria-label") || item.textContent || "").trim().toLowerCase();
      const allLabels = enabledButtons.map(label);
      return ["start", "restart", "help"].every((name) => allLabels.some((item) => item.includes(name))) &&
        /\\benter\\b/.test(text) && (/arrow/.test(text) || (/\\bw\\b/.test(text) && /\\bs\\b/.test(text))) &&
        /\\br\\b/.test(text) && (/\\bp\\b/.test(text) || /escape/.test(text));
    })()`));
    scoreItem(bands, "usability_accessibility_constraints", "controls-and-buttons", 8, controlSurface, true,
      controlSurface ? "labelled enabled Start/Restart/Help buttons and complete keyboard help are present" : "required labelled buttons or keyboard help are missing");

    await client.call("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await sleep(250);
    const mobileFit = Boolean(await evaluate(client, `(() => {
      const viewport = document.querySelector('meta[name="viewport"]')?.content?.toLowerCase() ?? "";
      const realCssViewport = Math.abs(window.innerWidth - 390) <= 1 && Math.abs((window.visualViewport?.width ?? 0) - 390) <= 1;
      const deviceWidthDeclared = /width\\s*=\\s*device-width/.test(viewport);
      return realCssViewport && deviceWidthDeclared &&
        document.documentElement.scrollWidth <= 391 && document.body.scrollWidth <= 391 &&
        document.documentElement.scrollHeight <= 845 && document.body.scrollHeight <= 845;
    })()`));
    scoreItem(bands, "usability_accessibility_constraints", "mobile-fit", 7, mobileFit, false,
      mobileFit ? "real 390x844 CSS viewport fits without material overflow" : "missing device-width viewport or mobile overflow detected");

    const mobileShot = await client.call("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(join(options.outDir, "windline-mobile.png"), Buffer.from(mobileShot.data, "base64"));
    await client.call("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
    await sleep(250);
    const desktopShot = await client.call("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(join(options.outDir, "windline-desktop.png"), Buffer.from(desktopShot.data, "base64"));

    scoreItem(bands, "functional_correctness", "ordered-chimes-and-landing", 20, null, true,
      "manual E2 required: verify visible out-of-order feedback without progress, collect 1→2→3, crash on obstacle and out-of-bounds contact, crash on hard rooftop impact, and reach success on a gentle ordered rooftop landing");
    scoreItem(bands, "presentation_documentation", "visual-readability", 10, null, false,
      "manual blinded review required: verify visual readability of the glider, both thermals, ordered chimes, rooftop, current objective, controls, and state feedback in controlled desktop and true-390px mobile captures");

    await sleep(Math.min(FINAL_QUIET_MS, Math.max(0, deadline - Date.now())));
    if (interceptions.size) await Promise.allSettled([...interceptions]);
    // This is deliberately computed once, after every interaction and the
    // bounded late-event observation window. All downstream report surfaces
    // consume this same final value.
    const finalOfflineOutcome = {
      passed: blockedRequests.length === 0 && runtimeErrors.length === 0,
      blocked_request_count: blockedRequests.length,
      runtime_error_count: runtimeErrors.length,
      observation_window_ms: FINAL_QUIET_MS,
    };
    scoreItem(bands, "functional_correctness", "offline-boot", 10, finalOfflineOutcome.passed, true,
      `blocked external/local requests=${finalOfflineOutcome.blocked_request_count}; runtime errors=${finalOfflineOutcome.runtime_error_count}; staged files=index.html`);

    const automatedScore = Object.values(bands).reduce((total, band) => total + band.score, 0);
    const allItems = Object.values(bands).flatMap((band) => band.items);
    const criticalFailures = allItems.filter((item) => item.critical && item.passed === false).map((item) => item.id);
    const pendingManualCriteria = allItems.filter((item) => item.passed === null).map((item) => item.id);
    const criterionOutcomes = [
      { id: "offline-boot", passed: finalOfflineOutcome.passed, review: "automated" },
      { id: "snapshot-contract", passed: snapshotValid && surfaceValid, review: "automated" },
      { id: "start-and-steering", passed: startedFlying && steeringPass, review: "automated" },
      { id: "ordered-chimes-and-landing", passed: null, review: "independent E2 required" },
      { id: "pause-crash-restart", passed: pauseStable && crashed && restarted, review: "automated" },
      { id: "deterministic-course", passed: deterministic, review: "automated" },
      { id: "keyboard-and-responsive", passed: controlSurface && mobileFit, review: "automated" },
      { id: "visual-readability", passed: null, review: "independent E2 required" },
    ];
    const report = {
      schema: SCHEMA,
      challenge: { id: "windline", version: "1.0.0" },
      artifact: { path: options.artifact, sha256: artifactInfo.sha256 },
      evaluator: {
        runtime: process.version,
        chromium,
        generated_at: new Date().toISOString(),
        isolation: {
          provider: "bubblewrap",
          user_namespace: true,
          network_namespace: true,
          chromium_sandbox: true,
          staging_files: ["index.html"],
        },
      },
      automated_score: automatedScore,
      manual_points_available: 30,
      final_offline_outcome: finalOfflineOutcome,
      provisional_pass: false,
      pass_rule: "80/100 and every critical criterion; ordered success and presentation require independent E2 review",
      critical_failures: criticalFailures,
      pending_manual_criteria: pendingManualCriteria,
      criterion_outcomes: criterionOutcomes,
      bands,
      observations: {
        browser_errors: [...new Set(runtimeErrors)],
        unexpected_network_requests: [...new Set(blockedRequests)],
        screenshots: ["windline-desktop.png", "windline-mobile.png"],
      },
    };
    writeFileSync(join(options.outDir, "evaluation.json"), `${JSON.stringify(report, null, 2)}\n`);
    writeFileSync(join(options.outDir, "browser.log"), `${[...new Set([...runtimeErrors, ...blockedRequests.map((url) => `BLOCKED ${url}`)])].join("\n")}\n`);
    return report;
  } catch (error) {
    if (totalDeadlineHit) throw new Error(`total evaluator deadline exceeded (${TOTAL_EVALUATOR_MS}ms)`);
    if (stderr && /Running as root without --no-sandbox/.test(stderr)) {
      throw new Error("Chromium sandbox could not start safely; refusing unsandboxed execution");
    }
    throw error;
  } finally {
    if (totalTimer) clearTimeout(totalTimer);
    client?.close();
    try { child?.kill("SIGTERM"); } catch {}
    await sleep(100);
    try { child?.kill("SIGKILL"); } catch {}
    chmodSync(stage, 0o700);
    rmSync(stage, { recursive: true, force: true });
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const artifactInfo = inspectArtifact(options.artifact);
  const report = await runBrowser(options, artifactInfo);
  console.log(JSON.stringify(report, null, 2));
  console.error(`Windline automated score: ${report.automated_score}/70; 30 points require independent E2 review.`);
  process.exitCode = report.critical_failures.length > 0 ? 1 : 0;
}

main().catch((error) => {
  console.error(`EVALUATOR ERROR: ${error.stack ?? error}`);
  process.exit(2);
});
