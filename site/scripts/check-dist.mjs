// @ts-check
// Post-build verification for the OneShot Lab static site.
// Fails the build if key pages are missing, links escape the /oneshot/ base,
// or dishonest placeholder content is present.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = new URL("../dist", import.meta.url).pathname;
const LIBRARY_RESULTS = new URL("../../library/results", import.meta.url).pathname;
const BASE = "/oneshot/";

const problems = [];
const resultManifests = [];

try {
  for (const entry of readdirSync(LIBRARY_RESULTS, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const manifest = JSON.parse(readFileSync(join(LIBRARY_RESULTS, entry.name, "result.json"), "utf-8"));
    resultManifests.push(manifest);
  }
} catch (error) {
  problems.push(`cannot read result manifests for built-output verification: ${String(error)}`);
}

function walk(dir, callback) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      walk(full, callback);
    } else {
      callback(full);
    }
  }
}

// 1. Required pages exist.
const requiredPages = [
  "index.html",
  "challenges/index.html",
  "challenges/loopback/index.html",
  "challenges/neon-courier/index.html",
  "challenges/signal-siege/index.html",
  "challenges/gravshift/index.html",
  "challenges/windline/index.html",
  "results/index.html",
  ...resultManifests.map((result) => `results/${result.id}/index.html`),
  "methodology/index.html",
  "contribute/index.html",
];
for (const page of requiredPages) {
  try {
    statSync(join(DIST, page));
  } catch {
    problems.push(`missing required page: ${page}`);
  }
}

// 2. Every absolute href/src in built HTML is base-prefixed.
const urlAttribute = /\b(href|src)\s*=\s*"([^"]*)"/g;
let htmlFiles = 0;
walk(DIST, (file) => {
  if (!file.endsWith(".html")) return;
  htmlFiles += 1;
  const html = readFileSync(file, "utf-8");
  for (const match of html.matchAll(urlAttribute)) {
    const url = match[2];
    if (url.startsWith("/") && !url.startsWith(BASE)) {
      problems.push(`${relative(DIST, file)}: absolute URL escapes base: ${url}`);
    }
  }
  // 3. Honesty checks: no scaffold markers may ship. <pre> blocks are skipped
  // because challenge prompts are quoted verbatim and may legitimately
  // discuss these words.
  const withoutPre = html.replace(/<pre\b[\s\S]*?<\/pre>/gi, "");
  for (const marker of ["lorem ipsum", "TODO:", "FIXME"]) {
    if (withoutPre.toLowerCase().includes(marker.toLowerCase())) {
      problems.push(`${relative(DIST, file)}: contains scaffold marker "${marker}"`);
    }
  }
  if (/href\s*=\s*"#"\s/.test(html)) {
    problems.push(`${relative(DIST, file)}: contains dead placeholder link href="#"`);
  }
});

// 4. Every result with an HTML artifact must remain interactive without
// receiving site privileges. Raw bytes stay inert until an explicit click,
// then run in an opaque-origin frame with a second CSP boundary and no network,
// forms, popups, downloads, or top-level navigation.
const playablePages = [];
for (const result of resultManifests) {
  const htmlArtifacts = Array.isArray(result.artifacts)
    ? result.artifacts.filter((artifact) => artifact.kind === "html")
    : [];
  if (htmlArtifacts.length === 0) continue;

  const pageName = `results/${result.id}/index.html`;
  try {
    const html = readFileSync(join(DIST, pageName), "utf-8");
    playablePages.push(html);
    for (const required of [
      "Interactive artifact",
      "Play in sandbox",
      "data-document-base64",
      "sandbox=\"allow-scripts\"",
      "referrerpolicy=\"no-referrer\"",
      "connect-src 'none'",
      "Download raw artifact",
    ]) {
      if (!html.includes(required)) problems.push(`${pageName}: lacks sandbox marker: ${required}`);
    }
    for (const artifact of htmlArtifacts) {
      const rawUrl = `raw.githubusercontent.com/5p00kyy/oneshot/main/library/results/${result.id}/${artifact.path}`;
      if (!html.includes(rawUrl)) problems.push(`${pageName}: lacks raw artifact link: ${artifact.path}`);
    }
    for (const forbidden of [
      "allow-same-origin",
      "allow-top-navigation",
      "allow-popups",
      "allow-forms",
      "allow-downloads",
    ]) {
      if (html.includes(forbidden)) problems.push(`${pageName}: grants forbidden iframe capability: ${forbidden}`);
    }
    if (!/<iframe\b/i.test(html)) problems.push(`${pageName}: lacks its interactive sandbox frame`);
    if (/\bsrc=\"https:\/\/raw\.githubusercontent\.com[^\"]+\.html/i.test(html)) {
      problems.push(`${pageName}: HTML artifact is loaded remotely instead of as an inert checked-in payload`);
    }
  } catch {
    problems.push(`missing HTML result detail page: ${pageName}`);
  }
}

const clientScripts = [];
walk(DIST, (file) => {
  if (file.endsWith(".js")) clientScripts.push(readFileSync(file, "utf-8"));
});
const clientBundle = [...playablePages, ...clientScripts].join("\n");
for (const required of [
  "DOMParser",
  "Content-Security-Policy",
  "connect-src 'none'",
  ".srcdoc=",
  "localStorage",
  "querySelectorAll",
]) {
  if (!clientBundle.includes(required)) problems.push(`sandbox client bundle lacks enforcement marker: ${required}`);
}

if (htmlFiles === 0) {
  problems.push("no HTML files found in dist; did the build run?");
}

if (problems.length > 0) {
  console.error(`FAILED: ${problems.length} site problem(s):`);
  for (const problem of problems) console.error(` - ${problem}`);
  process.exit(1);
}

console.log(`OK: ${htmlFiles} HTML pages verified under ${BASE} with honest content`);
