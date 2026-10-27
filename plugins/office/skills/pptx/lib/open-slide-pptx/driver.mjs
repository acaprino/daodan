#!/usr/bin/env node
/**
 * Office HTML to PPTX conversion driver.
 *
 * Serves the design HTML, its local assets and the vendored engine bundle from
 * one local origin, runs the conversion inside a headless Chromium page and
 * writes the PPTX plus an evidence record. HTTP requests and WebSockets outside
 * that origin are aborted and recorded, service workers are blocked and no
 * hostname other than localhost resolves, so a conversion fetches no remote
 * resource. A design that needed one is refused rather than converted lossily.
 *
 * Usage:
 *   node driver.mjs --probe
 *   node driver.mjs --job <job.json>
 *
 * Exit codes: 0 converted or probed, 2 invocation, job or design contract
 * problem, 3 missing runtime, 4 conversion failure.
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
const BUNDLE_ROUTE = '/__office__/open-slide-pptx.js';
const IGNORED_MISSING = new Set(['/favicon.ico']);
const CONTRACT_MARKERS = ['Office HTML contract violated', 'No [data-office-slide] panel found'];
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

const PLAYWRIGHT_RECOVERY = 'Install the playwright Node module, version 1.48 or newer (npm install playwright), or set OFFICE_PPTX_PLAYWRIGHT to a directory that contains it.';
const BROWSER_RECOVERY = 'Set OFFICE_PPTX_BROWSER to an existing Chrome, Edge or Chromium executable, or install the Playwright browser with: npx playwright install chromium';
const LAUNCH_ARGS = ['--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost'];

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

function fail(code, message, extra = {}) {
  emit({ status: 'error', code, message, ...extra }, code);
}

function readManifest() {
  try {
    return JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  } catch {
    return null;
  }
}

function isInside(root, candidate) {
  return candidate === root || candidate.startsWith(root.endsWith(path.sep) ? root : root + path.sep);
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

/** A named browser that does not exist is a stop, never a reason to pick another one. */
function resolveBrowser(requested, playwright) {
  const named = requested
    ? { label: 'job.browser_executable', value: requested }
    : process.env.OFFICE_PPTX_BROWSER
      ? { label: 'OFFICE_PPTX_BROWSER', value: process.env.OFFICE_PPTX_BROWSER }
      : null;
  if (named) {
    const resolved = path.resolve(named.value);
    if (fs.existsSync(resolved) && fs.statSync(resolved).isFile()) return { executablePath: resolved, source: named.label, launchPath: resolved };
    return { executablePath: null, source: named.label, requestedMissing: resolved };
  }
  for (const candidate of BROWSER_CANDIDATES) {
    if (fs.existsSync(candidate)) return { executablePath: candidate, source: 'known installation path', launchPath: candidate };
  }
  let bundled = null;
  try {
    bundled = playwright ? playwright.module.chromium.executablePath() : null;
  } catch {
    bundled = null;
  }
  if (bundled && fs.existsSync(bundled)) return { executablePath: bundled, source: 'playwright bundled chromium', launchPath: null };
  return { executablePath: null, source: 'no browser found' };
}

function browserFailure(choice) {
  return choice.requestedMissing
    ? `The browser named by ${choice.source} does not exist: ${choice.requestedMissing}. ${BROWSER_RECOVERY}`
    : `No Chromium-family browser was found. ${BROWSER_RECOVERY}`;
}

/** WebSocket interception (context.routeWebSocket) arrived in Playwright 1.48. */
function routesWebSockets(version) {
  const [major, minor] = String(version || '').split('.').map(Number);
  return major > 1 || (major === 1 && minor >= 48);
}

function probe() {
  const playwright = resolvePlaywright();
  const browser = resolveBrowser(null, playwright);
  const manifest = readManifest();
  const webSocketRouting = Boolean(playwright && routesWebSockets(playwright.version));
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
      ? { available: webSocketRouting, version: playwright.version, source: playwright.source, resolved: playwright.resolved,
        ...(webSocketRouting ? {} : { recovery: PLAYWRIGHT_RECOVERY }) }
      : { available: false, recovery: PLAYWRIGHT_RECOVERY },
    browser: browser.executablePath
      ? { available: true, executablePath: browser.executablePath, source: browser.source }
      : { available: false, source: browser.source, recovery: browserFailure(browser) },
  }, webSocketRouting && browser.executablePath && fs.existsSync(BUNDLE) ? 0 : 3);
}

const JOB_KEYS = new Set(['html', 'output', 'evidence', 'assets_root', 'browser_executable', 'timeout_ms', 'headless']);

function readJob(file) {
  if (!path.isAbsolute(file)) fail(2, `--job needs an absolute path, got: ${file}`);
  let raw;
  try {
    raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    fail(2, `Cannot read the job file ${file}: ${error.message}`);
  }
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) fail(2, 'The job file must contain one JSON object');
  const unknown = Object.keys(raw).filter((key) => !JOB_KEYS.has(key));
  if (unknown.length > 0) fail(2, `Unknown job keys: ${unknown.join(', ')}`);
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
    if (typeof job[key] !== 'string' || !path.isAbsolute(job[key])) fail(2, `job.${key} must be an absolute path`);
  }
  if (!/\.(html?|htm)$/i.test(job.html) || !fs.existsSync(job.html) || !fs.statSync(job.html).isFile()) {
    fail(2, `job.html is not an existing HTML file: ${job.html}`);
  }
  if (!/\.pptx$/i.test(job.output)) fail(2, `job.output must end with .pptx: ${job.output}`);
  const outputParent = path.dirname(job.output);
  if (!fs.existsSync(outputParent) || !fs.statSync(outputParent).isDirectory()) fail(2, `The output directory does not exist: ${outputParent}`);
  if (job.evidence !== null) {
    if (typeof job.evidence !== 'string' || !path.isAbsolute(job.evidence) || !/\.json$/i.test(job.evidence)) {
      fail(2, `job.evidence must be an absolute .json path: ${job.evidence}`);
    }
    const evidenceParent = path.dirname(job.evidence);
    if (!fs.existsSync(evidenceParent) || !fs.statSync(evidenceParent).isDirectory()) fail(2, `The evidence directory does not exist: ${evidenceParent}`);
  }
  for (const target of [job.output, job.evidence]) {
    if (target !== null && fs.existsSync(target)) {
      fail(2, `Refusing to overwrite ${target}: earlier candidates and their evidence stay intact; choose a new candidate name.`);
    }
  }
  if (job.assets_root !== null) {
    if (typeof job.assets_root !== 'string' || !path.isAbsolute(job.assets_root)
      || !fs.existsSync(job.assets_root) || !fs.statSync(job.assets_root).isDirectory()) {
      fail(2, `job.assets_root must be an existing absolute directory: ${job.assets_root}`);
    }
  }
  const root = fs.realpathSync(job.assets_root ?? path.dirname(job.html));
  if (!isInside(root, fs.realpathSync(job.html))) fail(2, `job.html must sit inside the asset root ${root}: ${job.html}`);
  if (!Number.isInteger(job.timeout_ms) || job.timeout_ms < 1000 || job.timeout_ms > 600000) {
    fail(2, `job.timeout_ms must be an integer between 1000 and 600000: ${job.timeout_ms}`);
  }
  if (typeof job.headless !== 'boolean') fail(2, `job.headless must be a boolean: ${job.headless}`);
  if (job.browser_executable !== null && typeof job.browser_executable !== 'string') fail(2, 'job.browser_executable must be a string path');
  return job;
}

/**
 * Serve the asset root on one loopback origin. The HTML keeps its real path
 * below the root, so its relative URLs resolve from its own directory. Dotfiles,
 * paths that leave the root through a link and foreign Host headers are refused.
 */
function startServer(html, root) {
  const missing = [];
  const realRoot = fs.realpathSync(root);
  const state = { host: null };
  const server = http.createServer((request, response) => {
    const refuse = (status, text, record) => {
      if (record) missing.push(record);
      response.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end(text);
    };
    if (request.headers.host !== state.host) return refuse(421, 'Misdirected request', null);
    let pathname;
    try {
      pathname = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
    } catch {
      return refuse(400, 'Bad request', null);
    }
    if (pathname === BUNDLE_ROUTE) return send(response, BUNDLE);
    const normalized = path.posix.normalize(pathname);
    if (normalized.split('/').some((segment) => segment.startsWith('.'))) return refuse(404, 'Not found', pathname);
    const candidate = path.resolve(realRoot, '.' + normalized);
    let real = null;
    try {
      real = fs.realpathSync(candidate);
    } catch {
      real = null;
    }
    if (!real || !isInside(realRoot, real) || !fs.statSync(real).isFile()) return refuse(404, 'Not found', pathname);
    return send(response, real);
  });
  function send(response, file) {
    response.writeHead(200, {
      'Content-Type': CONTENT_TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    response.end(fs.readFileSync(file));
  }
  const htmlRoute = '/' + path.relative(realRoot, fs.realpathSync(html)).split(path.sep).map(encodeURIComponent).join('/');
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      state.host = `127.0.0.1:${server.address().port}`;
      resolve({ server, origin: `http://${state.host}`, htmlRoute, root: realRoot, missing });
    });
  });
}

function writeAtomically(target, bytes) {
  const partial = `${target}.partial-${process.pid}`;
  fs.writeFileSync(partial, bytes, { flag: 'wx' });
  fs.renameSync(partial, target);
}

async function convert(job) {
  if (!fs.existsSync(BUNDLE)) fail(3, `The engine bundle is missing: ${BUNDLE}. Rebuild it with: node rebuild.mjs (see UPSTREAM.md)`);
  const playwright = resolvePlaywright();
  if (!playwright) fail(3, `The playwright Node module is unavailable. ${PLAYWRIGHT_RECOVERY}`);
  const browserChoice = resolveBrowser(job.browser_executable, playwright);
  if (!browserChoice.executablePath) fail(3, browserFailure(browserChoice));

  const { server, origin, htmlRoute, root, missing } = await startServer(path.resolve(job.html), job.assets_root ?? path.dirname(job.html));
  const launchOptions = { headless: job.headless, chromiumSandbox: true, args: LAUNCH_ARGS };
  if (browserChoice.launchPath) launchOptions.executablePath = browserChoice.launchPath;

  const warnings = [];
  const pageErrors = [];
  const blocked = [];
  let browser = null;
  let stage = 'launch';
  let failure = null;
  let failureCode = 4;
  let summary = null;
  try {
    browser = await playwright.module.chromium.launch(launchOptions);
    stage = 'page';
    const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
    if (typeof context.routeWebSocket !== 'function') {
      failureCode = 3;
      throw new Error(`Playwright ${playwright.version} cannot intercept WebSockets. ${PLAYWRIGHT_RECOVERY}`);
    }
    await context.route('**/*', (route) => {
      const url = route.request().url();
      if (url.startsWith(`${origin}/`) || url.startsWith('data:') || url.startsWith('blob:')) return route.continue();
      blocked.push(url);
      return route.abort();
    });
    await context.routeWebSocket(/.*/, (socket) => {
      blocked.push(socket.url());
      socket.close();
    });
    const page = await context.newPage();
    page.on('console', (message) => {
      if (['warning', 'error'].includes(message.type())) warnings.push({ type: message.type(), text: message.text() });
    });
    page.on('pageerror', (error) => pageErrors.push(String(error && error.message ? error.message : error)));
    await page.goto(`${origin}${htmlRoute}`, { waitUntil: 'load', timeout: job.timeout_ms });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(
      () => Array.from(document.images).every((image) => image.complete),
      null,
      { timeout: job.timeout_ms },
    );
    await page.addScriptTag({ url: `${origin}${BUNDLE_ROUTE}` });
    stage = 'convert';
    const started = performance.now();
    const result = await page.evaluate(() => window.officeHtmlToPptx());
    const conversionMs = Math.round(performance.now() - started);
    if (!result || typeof result.base64 !== 'string') throw new Error('The engine returned no package bytes');
    const bytes = Buffer.from(result.base64, 'base64');
    if (bytes.length === 0) throw new Error('The engine returned an empty package');

    const absent = missing.filter((item) => !IGNORED_MISSING.has(item));
    const brokenImages = await page.evaluate(() => Array.from(document.images)
      .filter((image) => image.naturalWidth === 0 && image.currentSrc).map((image) => image.currentSrc));
    if (pageErrors.length > 0 || blocked.length > 0 || absent.length > 0 || brokenImages.length > 0) {
      failureCode = 2;
      throw new Error('Office HTML contract violated: the design needed resources it may not use or does not have '
        + JSON.stringify({ page_errors: pageErrors, blocked_requests: blocked, missing_local_requests: absent, broken_images: brokenImages }));
    }

    const manifest = readManifest();
    const outputSha = sha256Bytes(bytes);
    const evidence = {
      schema: 'office/pptx-html-conversion/v1',
      converted_at: new Date().toISOString(),
      html: { path: job.html, sha256: sha256File(job.html) },
      assets_root: root,
      bundle: { path: BUNDLE, sha256: sha256File(BUNDLE) },
      engine: manifest
        ? { package: manifest.upstream.package, version: manifest.upstream.version, git_ref: manifest.upstream.git_ref, license: manifest.upstream.license, manifest_bundle_sha256: manifest.bundle.sha256 }
        : null,
      runtime: {
        node: process.version,
        playwright: { version: playwright.version, source: playwright.source },
        browser: {
          version: browser.version(),
          executable_path: browserChoice.executablePath,
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
    writeAtomically(job.output, bytes);
    if (job.evidence) writeAtomically(job.evidence, JSON.stringify(evidence, null, 2) + '\n');
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
    if (stage === 'launch') {
      failureCode = 3;
      failure = `The browser did not start (${browserChoice.source}: ${browserChoice.executablePath}): ${failure}. ${BROWSER_RECOVERY}`;
    } else if (CONTRACT_MARKERS.some((marker) => failure.includes(marker))) {
      failureCode = 2;
    }
  } finally {
    if (browser) await browser.close().catch(() => {});
    server.close();
  }
  if (failure) {
    fail(failureCode, `Conversion failed: ${failure}`, { page_errors: pageErrors, console_warnings: warnings, blocked_requests: blocked, missing_local_requests: missing });
  }
  emit(summary, 0);
}

function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 1 && argv[0] === '--probe') return probe();
  if (argv.length === 2 && argv[0] === '--job') return convert(readJob(argv[1])).catch((error) => {
    fail(4, `Driver error: ${error && error.stack ? error.stack : error}`);
  });
  process.stderr.write('Usage: node driver.mjs --probe | --job <absolute job.json>\n');
  process.exit(2);
}

main();
