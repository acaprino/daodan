#!/usr/bin/env node
/**
 * Office HTML to PPTX conversion driver.
 *
 * Serves the design HTML, its local assets and the vendored engine bundle from
 * one local origin, runs the conversion inside a headless Chromium page and
 * writes the PPTX plus an evidence record. Requests outside that origin are
 * aborted and recorded, so a conversion never fetches a remote resource.
 *
 * Usage:
 *   node driver.mjs --probe
 *   node driver.mjs --job <job.json>
 *
 * Exit codes: 0 converted or probed, 2 invocation or job problem,
 * 3 missing runtime, 4 conversion failure.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const LIB = path.dirname(fileURLToPath(import.meta.url));
const BUNDLE = path.join(LIB, 'bundle', 'open-slide-pptx.js');
const MANIFEST = path.join(LIB, 'manifest.json');
const BUNDLE_ROUTE = '/office-open-slide-pptx.js';
const requireFromHere = createRequire(import.meta.url);

const CONTENT_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.svg': 'image/svg+xml',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.otf': 'font/otf',
  '.eot': 'application/vnd.ms-fontobject',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
};

const BROWSER_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium-browser',
  '/usr/bin/chromium',
];

const PLAYWRIGHT_RECOVERY = 'Install the playwright Node module (npm install playwright) or set OFFICE_PPTX_PLAYWRIGHT to a directory that contains it.';
const BROWSER_RECOVERY = 'Set OFFICE_PPTX_BROWSER to a Chrome, Edge or Chromium executable, or install the Playwright browser with: npx playwright install chromium';

function sha256File(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function sha256Bytes(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function emit(payload, code) {
  process.stdout.write(JSON.stringify(payload) + '\n');
  process.exit(code);
}

function readManifest() {
  try {
    return JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  } catch {
    return null;
  }
}

function packageVersion(resolved) {
  let dir = path.dirname(resolved);
  for (let depth = 0; depth < 8; depth += 1) {
    const manifest = path.join(dir, 'package.json');
    if (fs.existsSync(manifest)) {
      try {
        const parsed = JSON.parse(fs.readFileSync(manifest, 'utf8'));
        if (typeof parsed.name === 'string' && parsed.name.includes('playwright')) return parsed.version;
      } catch {
        return null;
      }
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function resolvePlaywright() {
  const attempts = [];
  const explicit = process.env.OFFICE_PPTX_PLAYWRIGHT;
  if (explicit) {
    const base = path.resolve(explicit);
    attempts.push({ label: 'OFFICE_PPTX_PLAYWRIGHT', spec: base, paths: null });
    attempts.push({ label: 'OFFICE_PPTX_PLAYWRIGHT node_modules', spec: 'playwright', paths: [base, path.join(base, 'node_modules')] });
  }
  attempts.push({ label: 'node resolution', spec: 'playwright', paths: null });
  for (const attempt of attempts) {
    try {
      const resolved = attempt.paths
        ? requireFromHere.resolve(attempt.spec, { paths: attempt.paths })
        : requireFromHere.resolve(attempt.spec);
      const loaded = requireFromHere(resolved);
      if (loaded && loaded.chromium) {
        return { module: loaded, resolved, source: attempt.label, version: packageVersion(resolved) };
      }
    } catch {
      // The next candidate decides.
    }
  }
  return null;
}

function resolveBrowser(requested) {
  const named = [];
  if (requested) named.push({ label: 'job.browser_executable', value: requested });
  if (process.env.OFFICE_PPTX_BROWSER) named.push({ label: 'OFFICE_PPTX_BROWSER', value: process.env.OFFICE_PPTX_BROWSER });
  for (const item of named) {
    const resolved = path.resolve(item.value);
    if (fs.existsSync(resolved)) return { executablePath: resolved, source: item.label };
    return { executablePath: null, source: `${item.label} does not exist`, requestedMissing: resolved };
  }
  for (const candidate of BROWSER_CANDIDATES) {
    if (fs.existsSync(candidate)) return { executablePath: candidate, source: 'known installation path' };
  }
  return { executablePath: null, source: 'playwright bundled chromium' };
}

function probe() {
  const playwright = resolvePlaywright();
  const browser = resolveBrowser(null);
  const manifest = readManifest();
  emit({
    status: 'probe',
    node: process.version,
    lib: LIB,
    bundle: fs.existsSync(BUNDLE)
      ? { present: true, sha256: sha256File(BUNDLE), bytes: fs.statSync(BUNDLE).size }
      : { present: false, recovery: 'Rebuild it with: node rebuild.mjs (see UPSTREAM.md)' },
    manifest: manifest
      ? { present: true, upstream: manifest.upstream, bundle_sha256: manifest.bundle.sha256, tools: manifest.tools }
      : { present: false },
    playwright: playwright
      ? { available: true, version: playwright.version, source: playwright.source, resolved: playwright.resolved }
      : { available: false, recovery: PLAYWRIGHT_RECOVERY },
    browser: browser.executablePath
      ? { available: true, executablePath: browser.executablePath, source: browser.source }
      : { available: false, source: browser.source, recovery: BROWSER_RECOVERY },
  }, playwright && fs.existsSync(BUNDLE) ? 0 : 3);
}

const JOB_KEYS = new Set(['html', 'output', 'evidence', 'assets_root', 'browser_executable', 'timeout_ms', 'headless']);

function readJob(file) {
  if (!path.isAbsolute(file)) emit({ status: 'error', code: 2, message: `--job needs an absolute path, got: ${file}` }, 2);
  let raw;
  try {
    raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    emit({ status: 'error', code: 2, message: `Cannot read the job file ${file}: ${error.message}` }, 2);
  }
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    emit({ status: 'error', code: 2, message: 'The job file must contain one JSON object' }, 2);
  }
  const unknown = Object.keys(raw).filter((key) => !JOB_KEYS.has(key));
  if (unknown.length > 0) {
    emit({ status: 'error', code: 2, message: `Unknown job keys: ${unknown.join(', ')}` }, 2);
  }
  const job = {
    html: raw.html,
    output: raw.output,
    evidence: raw.evidence ?? null,
    assets_root: raw.assets_root ?? null,
    browser_executable: raw.browser_executable ?? null,
    timeout_ms: raw.timeout_ms ?? 180000,
    headless: raw.headless ?? true,
  };
  for (const key of ['html', 'output']) {
    if (typeof job[key] !== 'string' || !path.isAbsolute(job[key])) {
      emit({ status: 'error', code: 2, message: `job.${key} must be an absolute path` }, 2);
    }
  }
  if (!/\.(html?|htm)$/i.test(job.html) || !fs.existsSync(job.html) || !fs.statSync(job.html).isFile()) {
    emit({ status: 'error', code: 2, message: `job.html is not an existing HTML file: ${job.html}` }, 2);
  }
  if (!/\.pptx$/i.test(job.output)) {
    emit({ status: 'error', code: 2, message: `job.output must end with .pptx: ${job.output}` }, 2);
  }
  const outputParent = path.dirname(job.output);
  if (!fs.existsSync(outputParent) || !fs.statSync(outputParent).isDirectory()) {
    emit({ status: 'error', code: 2, message: `The output directory does not exist: ${outputParent}` }, 2);
  }
  if (job.evidence !== null) {
    if (typeof job.evidence !== 'string' || !path.isAbsolute(job.evidence) || !/\.json$/i.test(job.evidence)) {
      emit({ status: 'error', code: 2, message: `job.evidence must be an absolute .json path: ${job.evidence}` }, 2);
    }
    const evidenceParent = path.dirname(job.evidence);
    if (!fs.existsSync(evidenceParent) || !fs.statSync(evidenceParent).isDirectory()) {
      emit({ status: 'error', code: 2, message: `The evidence directory does not exist: ${evidenceParent}` }, 2);
    }
  }
  if (job.assets_root !== null) {
    if (typeof job.assets_root !== 'string' || !path.isAbsolute(job.assets_root)
      || !fs.existsSync(job.assets_root) || !fs.statSync(job.assets_root).isDirectory()) {
      emit({ status: 'error', code: 2, message: `job.assets_root must be an existing absolute directory: ${job.assets_root}` }, 2);
    }
  }
  if (!Number.isInteger(job.timeout_ms) || job.timeout_ms < 1000 || job.timeout_ms > 600000) {
    emit({ status: 'error', code: 2, message: `job.timeout_ms must be an integer between 1000 and 600000: ${job.timeout_ms}` }, 2);
  }
  if (typeof job.headless !== 'boolean') {
    emit({ status: 'error', code: 2, message: `job.headless must be a boolean: ${job.headless}` }, 2);
  }
  if (job.browser_executable !== null && typeof job.browser_executable !== 'string') {
    emit({ status: 'error', code: 2, message: 'job.browser_executable must be a string path' }, 2);
  }
  return job;
}

function startServer(html, assetsRoot) {
  const missing = [];
  const routes = new Map([['/index.html', html], [BUNDLE_ROUTE, BUNDLE]]);
  const server = http.createServer((request, response) => {
    let pathname;
    try {
      pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
    } catch {
      response.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Bad request');
      return;
    }
    let file = routes.get(pathname);
    if (!file) {
      const candidate = path.resolve(assetsRoot, '.' + path.posix.normalize(pathname));
      const inside = candidate === assetsRoot || candidate.startsWith(assetsRoot + path.sep);
      if (inside && fs.existsSync(candidate) && fs.statSync(candidate).isFile()) file = candidate;
    }
    if (!file) {
      missing.push(pathname);
      response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Not found');
      return;
    }
    response.writeHead(200, {
      'Content-Type': CONTENT_TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    response.end(fs.readFileSync(file));
  });
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => resolve({
      server,
      origin: `http://127.0.0.1:${server.address().port}`,
      missing,
    }));
  });
}

async function convert(job) {
  if (!fs.existsSync(BUNDLE)) {
    emit({ status: 'error', code: 3, message: `The engine bundle is missing: ${BUNDLE}. Rebuild it with: node rebuild.mjs (see UPSTREAM.md)` }, 3);
  }
  const playwright = resolvePlaywright();
  if (!playwright) {
    emit({ status: 'error', code: 3, message: `The playwright Node module is unavailable. ${PLAYWRIGHT_RECOVERY}` }, 3);
  }
  const browserChoice = resolveBrowser(job.browser_executable);
  if (job.browser_executable && !browserChoice.executablePath) {
    emit({ status: 'error', code: 3, message: `The requested browser executable does not exist: ${browserChoice.requestedMissing}` }, 3);
  }

  const assetsRoot = job.assets_root ? path.resolve(job.assets_root) : path.dirname(path.resolve(job.html));
  const { server, origin, missing } = await startServer(path.resolve(job.html), assetsRoot);
  const launchOptions = { headless: job.headless, chromiumSandbox: true };
  if (browserChoice.executablePath) launchOptions.executablePath = browserChoice.executablePath;

  const warnings = [];
  const pageErrors = [];
  const blocked = [];
  let browser = null;
  let failure = null;
  let summary = null;
  try {
    browser = await playwright.module.chromium.launch(launchOptions);
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    page.on('console', (message) => {
      if (['warning', 'error'].includes(message.type())) warnings.push({ type: message.type(), text: message.text() });
    });
    page.on('pageerror', (error) => pageErrors.push(String(error && error.message ? error.message : error)));
    await page.route('**/*', (route) => {
      const url = route.request().url();
      if (url.startsWith(`${origin}/`) || url.startsWith('data:') || url.startsWith('blob:')) return route.continue();
      blocked.push(url);
      return route.abort();
    });
    await page.goto(`${origin}/index.html`, { waitUntil: 'load', timeout: job.timeout_ms });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(
      () => Array.from(document.images).every((image) => image.complete && image.naturalWidth > 0),
      null,
      { timeout: job.timeout_ms },
    );
    await page.addScriptTag({ url: `${origin}${BUNDLE_ROUTE}` });
    const started = performance.now();
    const result = await page.evaluate(() => window.officeHtmlToPptx());
    const conversionMs = Math.round(performance.now() - started);
    if (!result || typeof result.base64 !== 'string') throw new Error('The engine returned no package bytes');
    const bytes = Buffer.from(result.base64, 'base64');
    if (bytes.length === 0) throw new Error('The engine returned an empty package');
    fs.writeFileSync(job.output, bytes);
    const manifest = readManifest();
    const outputSha = sha256Bytes(bytes);
    const evidence = {
      schema: 'office/pptx-html-conversion/v1',
      converted_at: new Date().toISOString(),
      html: { path: job.html, sha256: sha256File(job.html) },
      assets_root: assetsRoot,
      bundle: { path: BUNDLE, sha256: sha256File(BUNDLE) },
      engine: manifest
        ? { package: manifest.upstream.package, version: manifest.upstream.version, git_ref: manifest.upstream.git_ref, license: manifest.upstream.license, manifest_bundle_sha256: manifest.bundle.sha256 }
        : null,
      runtime: {
        node: process.version,
        playwright: { version: playwright.version, source: playwright.source },
        browser: {
          version: browser.version(),
          executable_path: launchOptions.executablePath || 'playwright bundled chromium',
          browser_choice_source: browserChoice.source,
          headless: launchOptions.headless,
        },
      },
      viewport: { width: 1920, height: 1080, device_scale_factor: 1 },
      output: { path: job.output, bytes: bytes.length, sha256: outputSha },
      panels: result.panels,
      parts: result.parts,
      scene: result.scene,
      images: result.images,
      conversion_ms: conversionMs,
      console_warnings: warnings,
      page_errors: pageErrors,
      blocked_requests: blocked,
      missing_local_requests: missing,
      limits: [
        'Microsoft PowerPoint was not used; render the saved file with office:deckcraft and review it independently.',
        'The vendored engine emits no native PPTX table and rasterizes vector effects it cannot express.',
        'Package contents and text presence do not prove visual fidelity.',
      ],
    };
    if (job.evidence) fs.writeFileSync(job.evidence, JSON.stringify(evidence, null, 2) + '\n');
    summary = {
      status: 'ok',
      output: job.output,
      evidence: job.evidence,
      output_sha256: outputSha,
      output_bytes: bytes.length,
      panels: result.panels,
      parts: result.parts.length,
      conversion_ms: conversionMs,
      console_warnings: warnings,
      page_errors: pageErrors,
      blocked_requests: blocked,
      missing_local_requests: missing,
      scene: result.scene,
      images: result.images,
      inline_evidence: job.evidence ? undefined : evidence,
    };
  } catch (error) {
    failure = String(error && error.message ? error.message : error);
  } finally {
    if (browser) await browser.close().catch(() => {});
    server.close();
  }
  if (failure) {
    const code = pageErrors.length > 0 && failure.includes('officeHtmlToPptx') ? 4 : 4;
    emit({ status: 'error', code, message: `Conversion failed: ${failure}`, page_errors: pageErrors, console_warnings: warnings, blocked_requests: blocked, missing_local_requests: missing }, code);
  }
  emit(summary, 0);
}

function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 1 && argv[0] === '--probe') return probe();
  if (argv.length === 2 && argv[0] === '--job') return convert(readJob(argv[1])).catch((error) => {
    emit({ status: 'error', code: 4, message: `Driver error: ${error && error.stack ? error.stack : error}` }, 4);
  });
  process.stderr.write('Usage: node driver.mjs --probe | --job <absolute job.json>\n');
  process.exit(2);
}

main();
