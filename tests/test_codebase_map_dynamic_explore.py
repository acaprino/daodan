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
FIXTURE = Path(__file__).resolve().parents[1] / "benchmarks/project-model/explore-fixtures/vite-react"  # a Vite and React app

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


VITE = {str(p.relative_to(FIXTURE)).replace("\\", "/"): p.read_text(encoding="utf-8") for p in sorted(FIXTURE.rglob("*")) if p.is_file()}


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


def test_a_control_something_covers_fails_with_what_covers_it(tmp_path, browser):
    """A cookie banner or a modal over the page: the failure names the element that takes the click."""
    covered = SERVER.replace("'/details':", "'/covered': `<!doctype html><button>Under</button>"
                             "<div id=banner style=\"position:fixed;inset:0;background:#fff\">cookies</div>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": covered}, seeds=["/covered"])
    under = controls(found, "/covered")[("button", "Under")]
    assert under["state"] == "failed" and "intercepts pointer events" in under["reason"] and "banner" in under["reason"]


def test_a_control_a_page_shows_late_is_waited_for_and_found_again_after_each_reload(tmp_path, browser):
    """A login screen drawn once the auth state answers: the controls are read when they are there, not at the load."""
    late = SERVER.replace("'/details':", "'/late': `<!doctype html><title>late</title><script>setTimeout(() => {"
                          "const a = document.createElement('button'); a.textContent = 'First'; document.body.append(a);"
                          "const b = document.createElement('button'); b.textContent = 'Second'; document.body.append(b);"
                          "a.addEventListener('click', () => fetch('/api/save')); }, 1100)</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": late}, seeds=["/late"])
    shown = controls(found, "/late")
    assert [shown[("button", name)]["state"] for name in ("First", "Second")] == ["pressed", "pressed"]
    assert shown[("button", "First")]["requests"]


def test_each_press_starts_from_a_first_visit_so_what_the_app_remembers_does_not_change_the_next_control(tmp_path, browser):
    """A page that draws its intro only until it has been seen (an onboarding, a cookie notice kept in storage)."""
    once = SERVER.replace("'/details':", "'/once': `<!doctype html><title>once</title><body><script>"
                          "if (!localStorage.getItem('seen')) { localStorage.setItem('seen', '1');"
                          "const b = document.createElement('button'); b.textContent = 'Intro'; document.body.append(b);"
                          "b.addEventListener('click', () => fetch('/api/save')); } else { document.body.append('welcome back'); }"
                          "</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": once}, seeds=["/once"])
    shown = controls(found, "/once")
    assert ("button", "Intro") in shown, (shown, found["gaps"])
    assert shown[("button", "Intro")]["state"] == "pressed" and shown[("button", "Intro")]["requests"]


# --- the handler a click called: the first function of the project the event reaches (CDP's own breakpoint) --------

def test_the_handler_of_a_click_is_the_first_project_function_the_event_reaches(tmp_path, browser):
    """`DOMDebugger.setEventListenerBreakpoint("click")` with the dependencies in `Debugger.setBlackboxPatterns`: the
    pause is in the handler, not in what it calls, nor in what ran because the state changed."""
    found = explore(tmp_path, browser, APP_FILES)
    here = controls(found, f"{found['origin'].rpartition(':')[2]}/")
    save, reset = here[("button", "Save")], here[("button", "Reset")]
    assert "handler" in save, json.dumps({k: v for k, v in save.items() if k != "calls"})
    assert (save["handler"]["name"], save["handler"]["url"]) == ("save", "/src/app.js")
    assert reset["handler"]["name"] == "reset"
    assert "handler" not in here[("link", "Out")]  # not pressed: no handler


def test_a_react_handler_is_the_function_written_in_the_component_not_reacts_own_dispatch(tmp_path, browser):
    project = write(tmp_path / "proj", VITE)
    subprocess.run([shutil.which("npm"), "install", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=project,
                   check=True, capture_output=True, timeout=600)
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(SCRIPTS / "dynamic/explore.cjs"), str(out), "0", str(project), "-", "60",
                           "npm run dev"], capture_output=True, text=True, timeout=400,
                          env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    [page] = json.loads((out / "explore-0.json").read_text(encoding="utf-8"))["pages"]
    lines = VITE["src/App.tsx"].split("\n")
    wanted = {name: next(i + 1 for i, text in enumerate(lines) if call in text)
              for name, call in (("Save", "setTotal(save(total))"), ("Reset", "setTotal(reset())"))}
    for name, line in wanted.items():
        handler = next(c for c in page["controls"] if c["name"] == name)["handler"]
        assert handler["source"].endswith("src/App.tsx") and handler["line"] == line, (name, handler)
