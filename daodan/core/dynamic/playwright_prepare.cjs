// In the preparation container only. Use the restored project's own Playwright CLI to read its
// configuration and install the matching browser revision. Listing with an unmatched file filter
// runs no tests and starts no web server; a reporter sees the resolved, inherited project options.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');

class BrowserRequirements {
  onBegin(config) {
    const browsers = new Set();
    const filters = JSON.parse(process.env.DAODAN_BROWSER_PROJECTS || '[]').map(pattern => {
      const literal = pattern.split('*').map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
      return new RegExp('^' + literal.join('.*') + '$', 'i');
    });
    const byName = new Map(config.projects.map(project => [project.name, project]));
    const selected = new Set(config.projects.filter(project => !filters.length || filters.some(re => re.test(project.name))));
    for (const project of selected) {
      for (const name of [...(project.dependencies || []), project.teardown]) {
        if (name && byName.has(name)) selected.add(byName.get(name));
      }
    }
    for (const project of selected) {
      const use = project.use || {};
      if (use.connectOptions || use.launchOptions?.executablePath) continue;
      const engine = use.browserName || use.defaultBrowserType || 'chromium';
      const channel = use.channel || use.launchOptions?.channel;
      if (channel && channel !== 'chromium') continue; // project-specific preinstalled branded browser
      if (engine === 'chromium' && !channel && !process.env.DAODAN_BROWSER_HEADED &&
          use.headless !== false && use.launchOptions?.headless !== false)
        browsers.add('chromium-headless-shell');
      else if (['chromium', 'firefox', 'webkit'].includes(engine)) browsers.add(engine);
    }
    fs.writeFileSync(process.env.DAODAN_BROWSER_PLAN, JSON.stringify([...browsers]));
  }
}
module.exports = BrowserRequirements;

function cliAt(cwd) {
  for (const name of ['@playwright/test', 'playwright']) {
    let manifest;
    try { manifest = require.resolve(name + '/package.json', {paths: [cwd]}); } catch { continue; }
    const pkg = JSON.parse(fs.readFileSync(manifest, 'utf8'));
    if (pkg.bin?.playwright) return {cli: path.join(path.dirname(manifest), pkg.bin.playwright), version: pkg.version};
  }
  throw new Error('no local Playwright CLI');
}

if (require.main === module) {
  const inputs = JSON.parse(process.argv[2]);
  const needed = new Map();
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'daodan-browser-'));
  try {
    for (const {index, root, args, projects} of inputs) {
      try {
        const cwd = path.resolve('/work', root);
        const {cli, version} = cliAt(cwd);
        const plan = path.join(temp, String(index));
        const listed = spawnSync(process.execPath, [cli, 'test', ...args, '--list', '--pass-with-no-tests',
          '--reporter', __filename, 'daodan-absent-' + randomUUID()], {cwd, stdio: 'inherit',
          env: {...process.env, DAODAN_BROWSER_PLAN: plan, DAODAN_BROWSER_PROJECTS: JSON.stringify(projects),
            DAODAN_BROWSER_HEADED: args.includes('--headed') ? '1' : ''}});
        if (listed.status !== 0) throw new Error('configuration could not be listed');
        const group = needed.get(version) || {cli, cwd, browsers: new Set(), runs: []};
        for (const browser of JSON.parse(fs.readFileSync(plan, 'utf8'))) group.browsers.add(browser);
        group.runs.push(index);
        needed.set(version, group);
      } catch { console.error('DAODAN-BROWSER-UNAVAILABLE', index); }
    }
    for (const {cli, cwd, browsers, runs} of needed.values()) {
      if (browsers.size === 0) continue;
      const flags = [];
      if (browsers.delete('chromium-headless-shell') && !browsers.has('chromium')) {
        browsers.add('chromium');
        const help = spawnSync(process.execPath, [cli, 'install', '--help'], {cwd, encoding: 'utf8'});
        if (help.stdout?.includes('--only-shell')) flags.push('--only-shell');
      }
      const result = spawnSync(process.execPath, [cli, 'install', '--with-deps', ...flags, ...browsers],
        {cwd, stdio: 'inherit'});
      if (result.status !== 0) for (const index of runs) console.error('DAODAN-BROWSER-UNAVAILABLE', index);
    }
  } finally { fs.rmSync(temp, {recursive: true, force: true}); }
}
