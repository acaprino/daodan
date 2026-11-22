"""The exploration of the running app: the controls of each page from Playwright's accessibility tree, each pressed
once, the functions of the project that ran between two takes of V8's precise coverage (plan task 11.3).

It starts code and a browser, so it runs only on Modal (`tests/modal_pytest.py`):

    python tests/modal_pytest.py tests/test_codebase_map_dynamic_explore.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_codebase_map_dynamic_app import closed, free_port  # noqa: E402
from test_codebase_map_dynamic_javascript import write  # noqa: E402

pytestmark = pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a browser and code: Modal only")
PLAYWRIGHT = "1.64.1"

SERVER = """const http = require('http');
const fs = require('fs');
const pages = {
  '/': `<!doctype html><title>home</title><div id=value>$5.00</div>
<button>Save</button><button>Reset</button><a href="/details">Details</a><a href="https://example.com/x">Out</a>
<input aria-label="Name"><script src="/src/app.js"></script>`,
  '/details': `<!doctype html><title>details</title><button>Delete</button><a href="/">Home</a>
<script src="/src/details.js"></script>`,
};
http.createServer((req, res) => {
  if (req.url === '/api/save') { res.end('{}'); return; }
  if (req.url.startsWith('/src/')) { res.setHeader('content-type', 'text/javascript'); res.end(fs.readFileSync('.' + req.url)); return; }
  res.setHeader('content-type', 'text/html'); res.end(pages[req.url.split('?')[0]] || 'not found');
}).listen(PORT, '127.0.0.1');
"""
APP = """function validate() { return true; }
function save() { validate(); fetch('/api/save', { method: 'POST' }); }
function reset() { document.getElementById('value').textContent = '$0.00'; }
function tick() { document.title = 'home ' + Date.now(); }
for (const [label, handler] of [['Save', save], ['Reset', reset]])
  [...document.querySelectorAll('button')].find(b => b.textContent === label).addEventListener('click', handler);
setInterval(tick, 100);
"""
DETAILS = """function remove() { document.body.append('gone'); }
document.querySelector('button').addEventListener('click', remove);
"""


@pytest.fixture(scope="module")
def browser() -> Path:
    """Playwright's own client and its headless shell, from npm and its CDN: what the preparation installs. Once per
    machine, whatever the workers (`-n`): they share apt, and two installs at once lock each other out."""
    baked = Path("/opt/playwright/node_modules/playwright-core")  # the Modal test image carries it (`modal_pytest.py`)
    if baked.is_dir():
        return baked
    import fcntl
    import tempfile
    tools = Path(tempfile.gettempdir()) / "daodan-playwright-tools"
    tools.mkdir(exist_ok=True)
    with open(tools / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not (tools / ".done").exists():
            subprocess.run([shutil.which("npm"), "install", "--prefix", str(tools), "--ignore-scripts", "--no-audit",
                            "--no-fund", f"playwright-core@{PLAYWRIGHT}"], check=True, capture_output=True, timeout=600)
            done = subprocess.run(["node", str(tools / "node_modules/playwright-core/cli.js"), "install", "--with-deps",
                                   "--only-shell", "chromium"], capture_output=True, text=True, timeout=900)
            assert done.returncode == 0, (done.stdout + done.stderr)[-2500:]  # the install says why it failed
            (tools / ".done").write_text("ok", encoding="utf-8")
    return tools / "node_modules/playwright-core"


def explore(tmp_path, browser: Path, files: dict, seeds=(), port: int | None = None) -> dict:
    port = port or free_port()
    project = write(tmp_path / "proj", {**files, "server.js": files.get("server.js", SERVER).replace("PORT", str(port))})
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(SCRIPTS / "dynamic/explore.cjs"), str(out), "0", str(project), str(port), "30",
                           "node server.js", json.dumps(list(seeds))], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    assert closed(port)
    return json.loads((out / "explore-0.json").read_text(encoding="utf-8"))


def controls(found: dict, url_path: str) -> dict:
    [page] = [item for item in found["pages"] if item["url"].endswith(url_path)]
    return {(c["role"], c["name"]): c for c in page["controls"]}


def names(control: dict) -> set[str]:
    return {call["name"] for call in control.get("calls", [])}


APP_FILES = {"src/app.js": APP, "src/details.js": DETAILS}


def test_each_control_is_pressed_once_and_the_functions_that_ran_are_its_own(tmp_path, browser):
    found = explore(tmp_path, browser, APP_FILES)
    here = controls(found, f"{found['origin'].rpartition(':')[2]}/")
    save, reset = here[("button", "Save")], here[("button", "Reset")]
    assert save["state"] == reset["state"] == "pressed"
    assert {"save", "validate"} <= names(save) and "reset" not in names(save)
    assert "reset" in names(reset) and not {"save", "validate"} & names(reset)
    assert [(r["method"], r["url"].rpartition("/")[2]) for r in save["requests"]] == [("POST", "save")]
    assert "tick" not in {name for control in here.values() for name in names(control)}


def test_a_link_leads_to_a_page_that_is_explored_too_and_others_are_declared_not_pressed(tmp_path, browser):
    found = explore(tmp_path, browser, APP_FILES)
    here = controls(found, f"{found['origin'].rpartition(':')[2]}/")
    assert here[("link", "Details")]["state"] == "pressed" and here[("link", "Details")]["navigated"].endswith("/details")
    assert (here[("link", "Out")]["state"], here[("link", "Out")]["reason"]) == ("skipped", "leaves_the_app")
    assert (here[("textbox", "Name")]["state"], here[("textbox", "Name")]["reason"]) == ("skipped", "needs_value")
    assert found["totals"]["pages"] == 2
    assert "remove" in names(controls(found, "/details")[("button", "Delete")])
    assert any("login" in item for item in found["limits"]["declared"])


def test_a_seed_is_opened_even_where_no_link_leads(tmp_path, browser):
    pages = {**APP_FILES, "server.js": SERVER.replace("'/details':", "'/hidden': `<button>Hidden</button>`,\n  '/details':")}
    found = explore(tmp_path, browser, pages, seeds=["/hidden"])
    assert any(item["url"].endswith("/hidden") for item in found["pages"])


def test_scripts_with_no_source_map_are_a_gap_not_a_silence(tmp_path, browser):
    found = explore(tmp_path, browser, APP_FILES)
    assert "calls_unmapped" in {gap["kind"] for gap in found["gaps"]}


def test_the_caps_are_declared_when_they_stop_the_exploration(tmp_path, browser):
    many = "".join(f"<button>B{n}</button>" for n in range(4))
    pages = {**APP_FILES, "server.js": SERVER.replace("<button>Save</button>", many + "<button>Save</button>")}
    spoiled = Path(SCRIPTS / "dynamic/explore.cjs").read_text(encoding="utf-8").replace("presses: 300", "presses: 2")
    probe = tmp_path / "explore-capped.cjs"
    probe.write_text(spoiled.replace("require('./app.cjs')", f"require({json.dumps(str(SCRIPTS / 'dynamic/app.cjs'))})"),
                     encoding="utf-8")
    port = free_port()
    project = write(tmp_path / "proj", {**pages, "server.js": pages["server.js"].replace("PORT", str(port))})
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(probe), str(out), "0", str(project), str(port), "30", "node server.js"],
                          capture_output=True, text=True, timeout=300, env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    found = json.loads((out / "explore-0.json").read_text(encoding="utf-8"))
    assert found["totals"]["pressed"] == 2 and any(
        gap["kind"] == "explore_cap" and "presses" in gap["caps"] for gap in found["gaps"])
    assert any(c.get("reason") == "cap" for item in found["pages"] for c in item["controls"])


VITE = {
    "package.json": json.dumps({"name": "v", "private": True, "type": "module", "scripts": {"dev": "vite"},
                                "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
                                "devDependencies": {"@vitejs/plugin-react": "^4.3.3", "vite": "^5.4.10"}}),
    "index.html": '<!doctype html><div id="root"></div><script type="module" src="/src/main.tsx"></script>\n',
    "vite.config.js": "import react from '@vitejs/plugin-react';\nexport default { plugins: [react()] };\n",
    "src/main.tsx": "import { createRoot } from 'react-dom/client';\nimport App from './App';\n"
                    "createRoot(document.getElementById('root')!).render(<App />);\n",
    "src/App.tsx": "import { useEffect, useState } from 'react';\nimport { save, reset } from './lib/actions';\n"
                   "export default function App() {\n  const [total, setTotal] = useState(5);\n"
                   "  useEffect(() => { const t = setInterval(() => setTotal(n => n), 150); return () => clearInterval(t); }, []);\n"
                   "  return <main><p>{total}</p><button onClick={() => setTotal(save(total))}>Save</button>\n"
                   "    <button onClick={() => setTotal(reset())}>Reset</button></main>;\n}\n",
    "src/lib/actions.ts": "function validate(n: number): number {\n  return Number.isFinite(n) ? n : 0;\n}\n\n"
                          "export function save(n: number): number {\n  return validate(n) + 1;\n}\n\n"
                          "export function reset(): number {\n  return 0;\n}\n",
}


def test_a_vite_apps_functions_are_named_by_the_file_and_line_its_source_map_says(tmp_path, browser):
    """The calls come back as the project's own TypeScript, through the source map Vite serves inline."""
    project = write(tmp_path / "proj", VITE)
    subprocess.run([shutil.which("npm"), "install", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=project,
                   check=True, capture_output=True, timeout=600)
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(SCRIPTS / "dynamic/explore.cjs"), str(out), "0", str(project), "-", "60",
                           "npm run dev"], capture_output=True, text=True, timeout=400,
                          env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    found = json.loads((out / "explore-0.json").read_text(encoding="utf-8"))
    [page] = found["pages"]
    save = next(c for c in page["controls"] if c["name"] == "Save")
    reset = next(c for c in page["controls"] if c["name"] == "Reset")
    assert all(call["source"].endswith("src/lib/actions.ts") for call in save["calls"] if call["name"] in ("save", "validate"))
    where = {(call["name"], call["source"].rpartition("/")[2], call["line"]) for call in save["calls"]}
    assert {("save", "actions.ts", 5), ("validate", "actions.ts", 1)} <= where
    assert ("reset", "actions.ts", 9) in {(c["name"], c["source"].rpartition("/")[2], c["line"]) for c in reset["calls"]}
    assert "save" not in {call["name"] for call in reset["calls"]}
    assert "calls_unmapped" not in {gap["kind"] for gap in found["gaps"]}


def test_a_page_with_no_control_is_a_gap_with_its_error_and_what_it_shows(tmp_path, browser):
    """A page that renders nothing to press says why: its first error and the start of its accessibility tree."""
    broken = SERVER.replace("'/details':", "'/broken': `<!doctype html><title>blank</title><p>loading</p>"
                                           "<script>throw new Error('boom: missing configuration')</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": broken}, seeds=["/broken"])
    [gap] = [gap for gap in found["gaps"] if gap["kind"] == "page_without_controls"]
    assert gap["path"].endswith("/broken") and "boom: missing configuration" in gap["detail"] and "loading" in gap["detail"]
