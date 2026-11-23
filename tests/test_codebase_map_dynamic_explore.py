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
from urllib.parse import urlsplit

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


def explore(tmp_path, browser: Path, files: dict, seeds=(), port: int | None = None, spoil: dict | None = None) -> dict:
    """The driver on `files`; `spoil` replaces text of the driver (a limit) in a copy of it, for a test of that limit."""
    port = port or free_port()
    project = write(tmp_path / "proj", {**files, "server.js": files.get("server.js", SERVER).replace("PORT", str(port))})
    out = tmp_path / "out"
    out.mkdir()
    driver = SCRIPTS / "dynamic/explore.cjs"
    if spoil:
        text = driver.read_text(encoding="utf-8")
        for old, new in spoil.items():
            assert old in text, old
            text = text.replace(old, new)
        driver = tmp_path / "explore-spoiled.cjs"
        driver.write_text(text.replace("require('./app.cjs')", f"require({json.dumps(str(SCRIPTS / 'dynamic/app.cjs'))})"), encoding="utf-8")
    done = subprocess.run(["node", str(driver), str(out), "0", str(project), str(port), "30",
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


def digest(found: dict) -> dict:
    """What each press found, whatever order the presses ran in: its state, handler, functions and requests."""
    return {(urlsplit(page["url"]).path, c["role"], c["name"]): (c["state"], (c.get("handler") or {}).get("name"), sorted(names(c)),
                                                   [request["url"].rpartition("/")[2] for request in c.get("requests", [])])
            for page in found["pages"] for c in page["controls"]}


def test_the_presses_of_a_page_run_in_several_tabs_and_find_what_one_tab_finds(tmp_path, browser):
    """Each press is from a first visit, in a context of its own, so they are independent: the tabs change the time, not the answer."""
    (tmp_path / "one").mkdir()
    (tmp_path / "several").mkdir()
    one = explore(tmp_path / "one", browser, APP_FILES, spoil={"workers: 4,": "workers: 1,"})
    several = explore(tmp_path / "several", browser, APP_FILES)
    assert (one["limits"]["workers"], several["limits"]["workers"]) == (1, 4)
    assert len(digest(one)) >= 6 and digest(several) == digest(one)
    assert [c["name"] for c in several["pages"][0]["controls"]] == [c["name"] for c in one["pages"][0]["controls"]]  # the worklist's order


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
    assert save["handler"]["start"] == {"line": 2, "column": 13}  # `function save() {`: the line of the function and the column of its parameters, where V8 says it begins
    assert reset["handler"]["name"] == "reset"
    assert "handler" not in here[("link", "Out")]  # not pressed: no handler


def test_the_start_of_the_handler_is_where_the_function_begins_not_where_the_pause_is(tmp_path, browser):
    """The pause is at the handler's first statement, a line below its start: the start tells the handler from a callback
    that statement holds."""
    nest = SERVER.replace("'/details':", "'/nest': `<!doctype html><title>nest</title><button id=t>Toggle</button>"
                          "<script src=/src/nest.js></script>`,\n  '/details':")
    files = {**APP_FILES, "server.js": nest, "src/nest.js": "document.getElementById('t').addEventListener('click', () => {\n  [1].map(o => o);\n});\n"}
    handler = controls(explore(tmp_path, browser, files, seeds=["/nest"]), "/nest")[("button", "Toggle")]["handler"]
    assert (handler["line"], handler["start"]) == (2, {"line": 1, "column": 55}), handler


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
        assert handler["start"] == {"line": line, "column": lines[line - 1].index("() =>")}, (name, handler)


# --- a button in a form: its fields are filled with what their type accepts, and the submit is the event pressed ----

LOGIN = ("function login() { fetch('/api/login', { method: 'POST' }); }\n"
         "document.querySelector('form').addEventListener('submit', event => { event.preventDefault(); login(); });\n")


def form_page(fields: str) -> str:
    return SERVER.replace("'/details':", "'/form': `<!doctype html><title>form</title><form>" + fields +
                          "<button type=submit>Log in</button></form><script src=/src/form.js></script>`,\n  '/details':")


def test_a_button_in_a_form_fills_the_fields_with_what_their_type_accepts_and_reaches_the_submit_handler(tmp_path, browser):
    """No click listener: the pause is the `submit` event's. The fields are filled by the types of HTML; nothing is invented."""
    page = form_page("<input type=email aria-label=Email required><input type=password aria-label=Password required minlength=6>"
                     "<select aria-label=Plan><option value=''>-</option><option value=pro>Pro</option></select>")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": page, "src/form.js": LOGIN}, seeds=["/form"])
    button = controls(found, "/form")[("button", "Log in")]
    assert button["state"] == "pressed" and [field["type"] for field in button["filled"]] == ["email", "password", "select-one"]
    assert button["invalid"] == [] and [request["url"].rpartition("/")[2] for request in button["requests"]] == ["login"]
    assert button["handler"]["url"] == "/src/form.js" and "login" in names(button)


def test_a_field_whose_constraint_the_value_of_its_type_cannot_meet_is_said_and_nothing_is_submitted(tmp_path, browser):
    page = form_page("<input type=text aria-label=Code required pattern='[0-9]{4}'>")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": page, "src/form.js": LOGIN}, seeds=["/form"])
    button = controls(found, "/form")[("button", "Log in")]
    assert button["state"] == "pressed" and [field["name"] for field in button["invalid"]] == ["Code"]
    assert button["invalid"][0]["message"] and button["requests"] == [] and "handler" not in button  # the browser refused


def test_a_control_a_submit_reveals_is_found_again_because_the_replay_fills_the_form_too(tmp_path, browser):
    """The press that showed it was of a filled form (the browser refuses an empty one), so the replay fills it as well."""
    page = form_page("<input type=email aria-label=Email required>").replace(
        "<script src=/src/form.js></script>", "<script src=/src/banner.js></script>")
    banner = ("document.querySelector('form').addEventListener('submit', event => { event.preventDefault();"
              " const b = document.createElement('button'); b.textContent = 'Dismiss'; document.body.append(b); });" + chr(10))
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": page, "src/banner.js": banner}, seeds=["/form"])
    [dismiss] = controls(found, "/form")[("button", "Log in")]["revealed"]
    assert (dismiss["name"], dismiss["state"]) == ("Dismiss", "pressed"), dismiss


def test_a_button_outside_a_form_fills_nothing(tmp_path, browser):
    found = explore(tmp_path, browser, APP_FILES)
    here = controls(found, f"{found['origin'].rpartition(':')[2]}/")
    assert "filled" not in here[("button", "Save")] and "invalid" not in here[("button", "Save")]


# --- the controls a press reveals --------------------------------------------------------------------------------

def test_controls_a_press_reveals_are_read_and_pressed_from_the_state_that_shows_them(tmp_path, browser):
    """A menu that draws its items once opened: read again after the press, each item pressed after the press that
    opens it (a page loaded again would not show them)."""
    menu = SERVER.replace("'/details':", "'/menu': `<!doctype html><title>menu</title><body><button id=m>Menu</button><script>"
                          "document.getElementById('m').addEventListener('click', () => {"
                          "const box = document.createElement('div'); box.setAttribute('role', 'menu');"
                          "for (const name of ['Settings', 'Logout']) { const b = document.createElement('button');"
                          " b.textContent = name; box.append(b);"
                          " if (name === 'Settings') b.addEventListener('click', function settings() { fetch('/api/save'); }); }"
                          "document.body.append(box); }, { once: true });</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": menu}, seeds=["/menu"])
    shown = controls(found, "/menu")
    opener = shown[("button", "Menu")]
    assert [(c["name"], c["state"]) for c in opener["revealed"]] == [("Settings", "pressed"), ("Logout", "pressed")]
    settings = opener["revealed"][0]
    assert settings["opened_by"] == ["Menu"] and settings["handler"]["name"] == "settings" and settings["requests"]
    assert ("button", "Settings") not in shown  # not in the first state of the page: only under the control that opens it
    assert "revealed" not in opener["revealed"][1]


def test_a_page_that_draws_itself_in_steps_does_not_make_its_own_controls_revealed(tmp_path, browser):
    """Controls drawn 600 ms and 1200 ms after the load belong to the page's state, not to the press that came after."""
    slow = SERVER.replace("'/details':", "'/slow': `<!doctype html><title>slow</title><body><button>First</button><script>"
                          "for (const [name, ms] of [['Second', 600], ['Third', 1200]]) setTimeout(() => {"
                          "const b = document.createElement('button'); b.textContent = name; document.body.append(b); }, ms);"
                          "document.querySelector('button').addEventListener('click', () => fetch('/api/save'));</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": slow}, seeds=["/slow"])
    shown = controls(found, "/slow")
    assert sorted(name for _, name in shown) == ["First", "Second", "Third"]
    assert not any(c.get("revealed") for c in shown.values())


def test_a_link_does_not_open_anything_it_navigates_or_scrolls(tmp_path, browser):
    """What a link's press adds to a page (a section drawn as it scrolls into view) is the page's, not a menu's."""
    link = SERVER.replace("'/details':", "'/link': `<!doctype html><title>link</title><body><a href=\"#x\">Go</a><script>"
                          "document.querySelector('a').addEventListener('click', () => {"
                          "const b = document.createElement('button'); b.textContent = 'Added'; document.body.append(b); });"
                          "</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": link}, seeds=["/link"])
    assert not controls(found, "/link")[("link", "Go")].get("revealed")


def test_the_controls_a_press_reveals_have_a_budget_of_their_own(tmp_path, browser):
    """Past it they are skipped with their cause, and the page's own controls are not starved for it."""
    many = SERVER.replace("'/details':", "'/many': `<!doctype html><title>many</title><body><button id=m>Open</button><script>"
                          "document.getElementById('m').addEventListener('click', () => {"
                          "for (const name of ['One', 'Two', 'Three']) { const b = document.createElement('button');"
                          " b.textContent = name; document.body.append(b); } }, { once: true });</script>`,\n  '/details':")
    spoiled = Path(SCRIPTS / "dynamic/explore.cjs").read_text(encoding="utf-8").replace("revealedPresses: 100", "revealedPresses: 1")
    probe = tmp_path / "explore-budget.cjs"
    probe.write_text(spoiled.replace("require('./app.cjs')", f"require({json.dumps(str(SCRIPTS / 'dynamic/app.cjs'))})"),
                     encoding="utf-8")
    port = free_port()
    project = write(tmp_path / "proj", {**APP_FILES, "server.js": many.replace("PORT", str(port))})
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(probe), str(out), "0", str(project), str(port), "30", "node server.js", '["/many"]'],
                          capture_output=True, text=True, timeout=300, env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    found = json.loads((out / "explore-0.json").read_text(encoding="utf-8"))
    revealed = controls(found, "/many")[("button", "Open")]["revealed"]
    assert [c["state"] for c in revealed] == ["pressed", "skipped", "skipped"] and revealed[1]["reason"] == "cap"
    assert any(gap["kind"] == "explore_cap" and "revealed" in gap["caps"] for gap in found["gaps"])


def test_a_press_that_reveals_more_than_the_cap_per_press_says_so_in_a_gap(tmp_path, browser):
    """The controls past the cap are not looked at: they are a gap that names the cap, never a silent cut."""
    many = SERVER.replace("'/details':", "'/many': `<!doctype html><title>many</title><body><button id=m>Open</button><script>"
                          "document.getElementById('m').addEventListener('click', () => {"
                          "for (const name of ['One', 'Two', 'Three']) { const b = document.createElement('button');"
                          " b.textContent = name; document.body.append(b); } }, { once: true });</script>`,\n  '/details':")
    spoiled = Path(SCRIPTS / "dynamic/explore.cjs").read_text(encoding="utf-8").replace("revealed: 30,", "revealed: 2,")
    probe = tmp_path / "explore-per-press.cjs"
    probe.write_text(spoiled.replace("require('./app.cjs')", f"require({json.dumps(str(SCRIPTS / 'dynamic/app.cjs'))})"),
                     encoding="utf-8")
    port = free_port()
    project = write(tmp_path / "proj", {**APP_FILES, "server.js": many.replace("PORT", str(port))})
    out = tmp_path / "out"
    out.mkdir()
    done = subprocess.run(["node", str(probe), str(out), "0", str(project), str(port), "30", "node server.js", '["/many"]'],
                          capture_output=True, text=True, timeout=300, env={**os.environ, "DAODAN_PLAYWRIGHT": str(browser)})
    assert done.returncode == 0, done.stderr[-1500:]
    found = json.loads((out / "explore-0.json").read_text(encoding="utf-8"))
    assert [c["name"] for c in controls(found, "/many")[("button", "Open")]["revealed"]] == ["One", "Two"]
    [gap] = [gap for gap in found["gaps"] if gap["kind"] == "explore_cap"]
    assert gap["caps"] == ["revealed_per_press"] and "1 more" in gap["detail"] and "Open" in gap["detail"]


def test_a_press_that_renames_the_page_reveals_nothing(tmp_path, browser):
    """A language or theme toggle gives every control another name: that is the page drawn again, not new controls."""
    swap = SERVER.replace("'/details':", "'/swap': `<!doctype html><title>swap</title><body><button id=l>English</button>"
                          "<button class=n>Save</button><button class=n>Reset</button><button class=n>Share</button><script>"
                          "document.getElementById('l').addEventListener('click', () => {"
                          "document.getElementById('l').textContent = 'Italiano';"
                          "const names = ['Salva', 'Azzera', 'Condividi'];"
                          "document.querySelectorAll('.n').forEach((b, i) => { b.textContent = names[i]; }); });"
                          "</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": swap}, seeds=["/swap"])
    assert not controls(found, "/swap")[("button", "English")].get("revealed")


def test_a_press_that_renames_every_control_and_adds_one_reveals_nothing(tmp_path, browser):
    """The page in another language has a skip link the first did not, and a third of its names are the same in both."""
    swap = SERVER.replace("'/details':", "'/skip': `<!doctype html><title>skip</title><body><button id=l>English</button>"
                          + "".join(f"<button class=n>Name {i}</button>" for i in range(12)) + "<script>"
                          "document.getElementById('l').addEventListener('click', () => {"
                          "document.getElementById('l').textContent = 'Italiano';"
                          "document.querySelectorAll('.n').forEach((b, i) => { if (i < 4) b.textContent = 'Nome ' + i; });"
                          "const skip = document.createElement('a'); skip.href = '#main'; skip.textContent = 'Vai al contenuto';"
                          "document.body.prepend(skip); });"
                          "</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": swap}, seeds=["/skip"])
    assert not controls(found, "/skip")[("button", "English")].get("revealed")


def test_a_dialog_that_takes_the_page_over_still_reveals_its_controls(tmp_path, browser):
    """A modal dialog leaves almost nothing of the page in the accessibility tree: what it shows is still revealed."""
    modal = SERVER.replace("'/details':", "'/modal': `<!doctype html><title>modal</title><body><button id=o>Open</button><script>"
                           "document.getElementById('o').addEventListener('click', () => {"
                           "document.body.innerHTML = '<div role=dialog aria-modal=true><button>Confirm</button><button>Cancel</button></div>'; });"
                           "</script>`,\n  '/details':")
    found = explore(tmp_path, browser, {**APP_FILES, "server.js": modal}, seeds=["/modal"])
    opener = controls(found, "/modal")[("button", "Open")]
    assert [c["name"] for c in opener.get("revealed", [])] == ["Confirm", "Cancel"]
