"""The project's ordinary Playwright runner records browser controls on Modal."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from test_codebase_map_dynamic_javascript import PLAYWRIGHT, observer, write


DYNAMIC = Path(__file__).resolve().parents[1] / "daodan/core/dynamic"


@pytest.mark.skipif(not shutil.which("node"), reason="the DOM unit tests use Node's built-in test runner")
def test_control_identity_event_and_screen_state():
    subprocess.run(["node", "--test", Path(__file__).with_name("control_coverage.test.cjs")],
                   check=True, timeout=30)


@pytest.mark.skipif(not shutil.which("node"), reason="the preparation reporter runs in Node")
def test_preparation_selects_only_the_configured_projects_and_their_dependencies(tmp_path):
    reporter = DYNAMIC / "playwright_prepare.cjs"
    plan = tmp_path / "plan.json"
    projects = [{"name": "Web [A]", "use": {}, "dependencies": ["auth"]},
                {"name": "auth", "use": {"defaultBrowserType": "firefox"}},
                {"name": "Web A", "use": {"browserName": "webkit"}},
                {"name": "Custom", "use": {"browserName": "webkit", "launchOptions": {"executablePath": "/app/web"}}}]
    probe = "new (require(process.argv[1]))().onBegin(JSON.parse(process.argv[2]));"
    env = {**os.environ, "DAODAN_BROWSER_PLAN": str(plan), "DAODAN_BROWSER_PROJECTS": '["Web [*]", "Custom"]'}
    for headed, expected in [("", "chromium-headless-shell"), ("1", "chromium")]:
        subprocess.run(["node", "-e", probe, reporter, json.dumps({"projects": projects})],
                       env={**env, "DAODAN_BROWSER_HEADED": headed}, check=True, timeout=20)
        assert set(json.loads(plan.read_text(encoding="utf-8"))) == {expected, "firefox"}


@pytest.mark.skipif(not shutil.which("node"), reason="the preload runs in Node")
def test_close_survives_a_failed_or_stalled_snapshot(tmp_path):
    # Only the preload is real. The module double never starts a browser or loads a project.
    probe = """const assert = require('node:assert/strict');
const Module = require('node:module');
const { EventEmitter } = require('node:events');
const context = Object.assign(new EventEmitter(), {
  exposeBinding() {}, addInitScript() {}, pages: () => [], close() {}
});
const fake = { chromium: { launchPersistentContext: async () => context } };
const load = Module._load;
Module._load = function(name, ...args) {
  return name === 'playwright-core' ? fake : load.call(this, name, ...args);
};
require(process.argv[2]);

(async () => {
  const owner = await require('playwright-core').chromium.launchPersistentContext();
  for (const evaluate of [() => Promise.reject(Error('page gone')), () => new Promise(() => {})]) {
    const page = { isClosed: () => false, evaluate, close(options) {
      assert.equal(this, page);
      return options.reason;
    }};
    owner.emit('page', page);
    assert.equal(await page.close({ reason: 'test completed' }), 'test completed');
  }
  console.log('both pages closed');
})().catch(err => { console.error(err); process.exitCode = 1; });
"""
    run = subprocess.run(["node", "-", DYNAMIC / "playwright_controls.cjs"], input=probe, text=True,
                         env={**os.environ, "DYN_CONTROLS_OUT": str(tmp_path / "controls-0")},
                         capture_output=True, timeout=15)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "both pages closed"
    [output] = tmp_path.glob("controls-0-*.json")
    assert set(json.loads(output.read_text(encoding="utf-8"))["gaps"]) == {"page_unreadable", "teardown_timeout"}


PROJECT = {
    "package.json": json.dumps({"private": True, "scripts": {"test:e2e": "playwright test --workers=1"}}),
    "private-route.html": """<!doctype html>
<button id="private-first">Private label one</button>
<button id="private-second">Private label two</button>
<script>
  window.handled = [];
  function sharedHandler(event) { window.handled.push(event.currentTarget.id); }
  for (const button of document.querySelectorAll('button')) button.addEventListener('click', sharedHandler);
</script>
""",
    "controls.spec.cjs": """const { test, expect } = require('@playwright/test');
const { pathToFileURL } = require('node:url');
const { resolve } = require('node:path');

test('two buttons share a handler', async ({ page }) => {
  await page.goto(pathToFileURL(resolve('private-route.html')).href + '?private-query=1');
  const first = page.locator('#private-first');
  await first.click();
  await first.click();
  await page.locator('#private-second').dispatchEvent('click');
  await first.evaluate(button => button.setAttribute('aria-expanded', 'true'));
  await first.click();
  expect(await page.evaluate(() => window.handled)).toEqual([
    'private-first', 'private-first', 'private-second', 'private-first'
  ]);
  await page.close();
});
""",
}


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real browser on Modal (tests/modal_pytest.py)")
def test_playwright_keeps_control_event_and_state_after_the_page_closes(tmp_path):
    project = write(tmp_path / "project", PROJECT)
    environment = {**os.environ, "CI": "1", "PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "browsers")}
    subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--ignore-scripts", f"@playwright/test@{PLAYWRIGHT}"],
                   cwd=project, env=environment, check=True, timeout=600)
    prepare = subprocess.run(["node", DYNAMIC / "playwright_prepare.cjs", json.dumps([
        {"index": 0, "root": str(project), "args": [], "projects": []}])],
        cwd=project, env=environment, check=True, timeout=600, capture_output=True, text=True)
    assert "DAODAN-BROWSER-UNAVAILABLE" not in prepare.stderr, prepare.stderr

    folder = tmp_path / "out"
    folder.mkdir()
    environment.update(DYN_CONTROLS_OUT=str(folder / "controls-0"),
                       NODE_OPTIONS=f"--require={DYNAMIC / 'playwright_controls.cjs'}")
    subprocess.run(["npm", "run", "test:e2e"], cwd=project, env=environment, check=True, timeout=180)

    reports = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("controls-0-*.json")]
    assert reports
    for report in reports:
        serialized = json.dumps(report)
        for private_text in ("private-first", "private-second", "Private label", "private-route", "private-query"):
            assert private_text not in serialized
    coverage, gaps = observer.controls(folder, 0)
    assert not gaps
    assert coverage["status"] == "observed"
    [document] = [doc for doc in coverage["documents"] if doc["observed"]]
    observed = document["observed"]
    assert len(observed) == 2
    assert all(row["event"] == "click" for row in observed)
    assert len({row["control"] for row in observed}) == 1
    assert len({row["state"] for row in observed}) == 2
    clicked = observed[0]["control"]
    untouched = [row for row in document["pending"] if row["control"] != clicked]
    assert len(untouched) == 1 and untouched[0]["event"] == "click"
    assert not any(row in observed for row in document["pending"])
