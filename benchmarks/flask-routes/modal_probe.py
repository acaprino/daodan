"""Flask's own loader and `url_map` on Modal, in the runner's container image, with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_probe.py
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_probe.py --mode venv-dir
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_probe.py --mode lock
    ... --only environment,werkzeug-source        some variants, nothing recorded
    ... --label before-review                      the answers go to `results/before-review/`, nothing recorded

The image is Daodan's (`container_runner.IMAGE`, with Modal's Python added beside it), and what Daodan's runner does before a command is
done by the same lines: `plan.py` (run with the Python that has Daodan's own dependencies, `DAODAN_PYTHON` names it, default `python`)
prints, for a project folder, the commands `flask_app.commands` gives, the setup command `container_runner.plan` gives, the restore
lines `container_runner._python` makes and the files the setup unpacks. There is one image for the `fixture` and one for each folder of
`layouts/` (a uv workspace, a Poetry project, a root `pyproject.toml` with an `api/requirements.txt`, a project that installs a local
package): the image build, the one moment the network is open, unpacks those files at `preparation.IN`, copies the folder to `/work`
(`container.WORKDIR`: Poetry keys its environment by the project's path) and runs the setup command there, with the runner's environment
(`preparation.ENV`); its standard error, exit code and seconds are kept in the image (`environment` returns them). Each variant of
`VARIANTS` then runs in a copy of its folder at `/work`, with the network blocked and the same environment, in the `cwd` the source's
command names, and its answer (`argv`, `returncode`, `stdout`, `stderr`, seconds, peak memory, the files it left in the project) goes to
`results/<variant>.json`. The project's code runs only in the container. What differs from Daodan's own container: Modal's runtime, and
the Python Modal installs in `/usr/local/bin` (3.12.1), which comes before `/usr/bin` in `preparation.PATH` and so is the `python3` the
restore's `uv venv --python python3` picks (in Daodan's image it would be the one of the image's packages: not measured).

The variants named in `RECORDED` are the answers the tests read: the run writes them to `tests/fixtures/premap/flask/<variant>.json`
(`returncode`, `stdout`, `stderr`, as the container runner returns them) with the sha256 of the script that produced them and the
`VERSION` of the source (`script.json`). If the script changes, record again and raise the `VERSION`.

`--mode venv-dir` runs `uv venv` on a few paths, to tell why the restore of the root folder (`uv venv "<venvs>/."`) needs its parent.
`--mode lock` makes the `uv.lock` and the `poetry.lock` of the two layouts that need one (`uv lock`, `poetry lock` 2.1.3, network open,
no project code: the layouts' dependencies are wheels), once; the lockfiles are in the repository.
"""
import hashlib
import json
import os
import pathlib
import shlex
import subprocess

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
OUT = HERE / "results"
RECORDED_DIR = REPO / "tests/fixtures/premap/flask"
SCRIPT = REPO / "daodan/core/entry_points/flask_routes.py"
LAYOUTS = ("uv-workspace", "poetry", "root-and-sub", "installed-copy")
FOLDERS = {"fixture": HERE / "fixture", **{name: HERE / "layouts" / name for name in LAYOUTS}}
WORK = "/work"  # `container.WORKDIR`


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


PLANS = {name: _plan(folder) for name, folder in FOLDERS.items()} if LOCAL else None
STATE = PLANS["fixture"]["state"] if LOCAL else "/daodan/state"
PY = f"{PLANS['fixture']['venvs']}/./bin/python" if LOCAL else ""  # the root folder's environment, `container_runner._python`


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    plan = PLANS[name]
    state, inputs = plan["state"], plan["inputs"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    for url, sha, file in plan["files"]:
        if url:  # a download of the runner (`uv`), checked by its sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        else:  # Daodan's own file, beside the entry points modules
            image = image.add_local_file(REPO / "daodan/core/entry_points" / file, f"{inputs}/{file}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2])
    image = (image.add_local_dir(FOLDERS[name], "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
             # the runner's setup, run as the runner runs it (`sh -c`, its environment, the project's folder, which is `/work`); a failed
             # restore does not fail the build (the restore line ends in `true`): its standard error and exit code are kept
             .run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && s=$(date +%s) && "
                           f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                           f"echo $(( $(date +%s) - s )) > {state}/setup.seconds"))
    if name == "fixture":  # a second environment, with python-dotenv beside Flask, for the variant that has a `.flaskenv`
        dotenv = f"{plan['venvs']}-dotenv"
        with_dotenv = shlex.quote(f"uv venv -q --python python3 {dotenv} && uv pip install -q --python {dotenv} -r requirements.txt python-dotenv")
        image = image.run_commands(f"cd /fix && env -i {env} sh -c {with_dotenv}")
    return image


IMAGES = {name: _image(name) for name in FOLDERS}
app = modal.App("flask-routes")

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
ENVIRONMENT = (
    "import importlib.metadata as m, os, sys, sysconfig\n"
    "paths = sysconfig.get_paths()\n"
    "print(repr({'version': sys.version, 'executable': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,\n"
    "            'purelib': paths['purelib'], 'platlib': paths['platlib'], 'stdlib': paths['stdlib'],\n"
    "            'flask': m.version('flask'), 'packages': sorted(f\"{d.metadata['Name']} {d.version}\" for d in m.distributions())}))\n")
WERKZEUG = (
    "import importlib.metadata as m, inspect, os\n"
    "import flask, werkzeug, werkzeug.routing as r\n"
    "from werkzeug.routing import converters as c, rules\n"
    "print('werkzeug', m.version('werkzeug'), 'flask', m.version('flask'))\n"
    "for package, words in ((werkzeug, ('part_isolating', '_trace', 'HEAD')), (flask, ('provide_automatic_options', 'required_methods', 'build_only'))):\n"
    "    root = os.path.dirname(package.__file__)\n"
    "    for dirpath, _, files in os.walk(root):\n"
    "        for f in sorted(files):\n"
    "            if f.endswith('.py') and ('routing' in dirpath or package is flask):\n"
    "                for n, line in enumerate(open(os.path.join(dirpath, f), encoding='utf-8'), 1):\n"
    "                    if any(word in line for word in words):\n"
    "                        print(package.__name__ + '/' + os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, '/') + ':' + str(n) + ': ' + line.rstrip())\n"
    "print('--- BaseConverter')\n"
    "print(inspect.getsource(c.BaseConverter)[:1800])\n"
    "print('--- PathConverter')\n"
    "print(inspect.getsource(c.PathConverter))\n"
    "print('--- defaults', {k: v.part_isolating for k, v in c.DEFAULT_CONVERTERS.items()})\n"
    "print('--- public attributes of Rule', [n for n in dir(rules.Rule) if not n.startswith('_')])\n"
    "rule = rules.Rule('/admin/<int:user_id>/x/<path:rest>/<a>-<b>')\n"
    "r.Map([rule])\n"
    "print('--- trace', rule._trace)\n"
    "print('--- converters', {k: (type(v).__qualname__, v.part_isolating, v.regex) for k, v in rule._converters.items()})\n"
    "print('--- arguments', rule.arguments)\n"
    "print('--- Flask.static', inspect.getsource(flask.Flask.__init__).split('self.has_static_folder')[1][:900])\n"
    "from werkzeug.middleware.dispatcher import DispatcherMiddleware\n"
    "print('--- DispatcherMiddleware', inspect.getsource(DispatcherMiddleware))\n"
    "from flask.cli import ScriptInfo\n"
    "print('--- ScriptInfo', inspect.signature(ScriptInfo.__init__), sorted(vars(ScriptInfo(None))), [n for n in dir(ScriptInfo) if not n.startswith('__')])\n"
    "print('--- Blueprint.register static', [line.strip() for line in inspect.getsource(flask.Blueprint.register).splitlines() if 'static' in line])\n"
    "print('--- import_name', inspect.signature(flask.Flask.__init__))\n")
MATCHES = (
    "from flask.cli import ScriptInfo\n"
    "app = ScriptInfo(app_import_path=None).load_app()\n"
    "adapter = app.url_map.bind('localhost')\n"
    "for path in ('/int/7', '/int/a', '/string/a', '/string/a/b', '/uuid/123e4567-e89b-12d3-a456-426614174000', '/files/a', '/files/a/b',\n"
    "             '/slug/a-b', '/slug/a/b', '/tail/a/b', '/tailre/a', '/tailre/a/b', '/pair/a/b', '/pair/a', '/glued/x-y', '/glued/x',\n"
    "             '/two/1/2', '/strict/', '/strict', '/loose', '/loose/', '/relaxed/', '/relaxed', '/admin/users/7'):\n"
    "    try:\n"
    "        print(path, '->', adapter.match(path, method='GET'))\n"
    "    except Exception as error:\n"
    "        print(path, '->', type(error).__name__)\n")
HOSTS = ("from flask import Flask\n\napp = Flask(__name__, host_matching=True, static_host='static.example.com')\n\n\n"
         "@app.route('/h', host='api.example.com')\ndef h():\n    return 'h'\n\n\n"
         "@app.route('/<tenant>/x', host='<sub>.example.com')\ndef x(tenant, sub):\n    return tenant + sub\n")
HANGS = "import time\ntime.sleep(120)\n"
DASH = ("from flask import Flask\n\n\nclass Dash:\n    def __init__(self):\n        self.server = Flask(__name__)\n\n\napp = Dash()\nserver = app.server\n\n\n"
        "@server.route('/dash')\ndef dash():\n    return 'dash'\n")
IMPORTED_APP = "from flask import Flask\n\napp = Flask(__name__)\n\n\n@app.route('/viaapp')\ndef viaapp():\n    return 'viaapp'\n"
IMPORTED_WSGI = "import app\n\nserver = app.app\n"
DISPATCHERS = "from flask import Flask\nfrom werkzeug.middleware.dispatcher import DispatcherMiddleware\n\n"
HELLO = "@sub.route('/hello')\ndef hello():\n    return 'hello'\n\n\n"
DISPATCHER_SERVER = DISPATCHERS + "sub = Flask('sub')\n\n\n" + HELLO + "server = DispatcherMiddleware(Flask('main'), {'/sub': sub})\n"
DISPATCHER_WSGI_APP = (DISPATCHERS + "app = Flask(__name__)\nsub = Flask('sub')\n\n\n@app.route('/')\ndef index():\n    return 'index'\n\n\n" + HELLO
                       + "app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/sub': sub})\n")
DISPATCHER_MAIN = (DISPATCHERS + "app = Flask(__name__)\nsub = Flask('sub')\n\n\n@app.route('/')\ndef index():\n    return 'index'\n\n\n" + HELLO
                   + "application = DispatcherMiddleware(app, {'/sub': sub})\n")
SERVES = (
    "import sys\n"
    "from flask.cli import ScriptInfo\n"
    "from werkzeug.test import Client\n"
    "ScriptInfo(app_import_path=None).load_app()\n"
    "client = Client(sys.modules['wsgi'].application)\n"
    "for path in ('/sub/hello', '/hello', '/sub', '/sub/'):\n"
    "    print(path, '->', client.get(path).status_code)\n")
SMALL = "from flask import Flask\n\napp = Flask(__name__)\n\n\n@app.get('/x')\ndef x():\n    return 'x'\n"
THREAD = "import threading\nimport time\n" + SMALL + "\n\nthreading.Thread(target=time.sleep, args=(100000,)).start()\n"
ATEXIT = "import atexit\n" + SMALL + "\n\natexit.register(lambda: print('goodbye'))\n"
REPLACED = "import io\nimport sys\n" + SMALL + "\n\nsys.stdout = io.StringIO()\n"
CLOSES = "import os\n" + SMALL + "\n\nfor fd in range(100, 140):\n    os.dup2(2, fd)\n"
DISPATCHER = ("from flask import Flask\nfrom werkzeug.middleware.dispatcher import DispatcherMiddleware\n\nsub = Flask('sub')\n\n\n"
              "@sub.route('/hello')\ndef hello():\n    return 'hello'\n\n\napplication = DispatcherMiddleware(Flask('main'), {'/sub': sub})\n")
FACTORY = ("from flask import Flask\n\n\ndef create_app():\n    app = Flask(__name__)\n\n    @app.route('/made')\n    def made():\n"
           "        return 'made'\n\n    return app\n")
TWO_APPS = "from flask import Flask\n\nfirst = Flask('first')\nsecond = Flask('second')\n"
NO_RULES = "from flask import Flask\n\napp = Flask(__name__, static_folder=None)\n"
MANY = ("from flask import Flask\n\napp = Flask(__name__)\n\n\ndef make(n):\n    def view(id):\n        return str(n)\n\n    return view\n\n\n"
        "for n in range(3000):\n    app.add_url_rule(f'/r{n}/<int:id>', endpoint=f'r{n}', view_func=make(n), methods=['GET', 'POST'])\n")
FACTORY_ARGS = FACTORY.replace("create_app()", "create_app(config)")


def _rename(old: str, new: str):
    return lambda p: (p / old).rename(p / new)


def _write(name: str, text: str):
    return lambda p: (p / name).write_text(text, encoding="utf-8")


def _remove(name: str):
    return lambda p: (p / name).unlink()


def _both(*edits):
    return lambda p: [edit(p) for edit in edits]


# variant -> (folder, what runs, environment added to the runner's, how the copy of the project is edited)
VARIANTS = {
    "routes": ("fixture", "script", {}, None),
    "environment": ("fixture", "environment", {}, None),
    "flask-routes-command": ("fixture", "flask routes", {}, None),
    "flask-routes-all-methods": ("fixture", "flask routes --all-methods", {}, None),
    "no-wsgi": ("fixture", "script", {}, _rename("wsgi.py", "other.py")),
    "flask-app-variable": ("fixture", "script", {"FLASK_APP": "other:app"}, _rename("wsgi.py", "other.py")),
    "flaskenv-without-dotenv": ("fixture", "script", {}, _both(_rename("wsgi.py", "other.py"), _write(".flaskenv", "FLASK_APP=other:app\n"))),
    # the same project in an environment that also has python-dotenv (`flask[dotenv]`), which the runner's restore does not install
    "flaskenv-with-dotenv": ("fixture", "script-dotenv", {}, _both(_rename("wsgi.py", "other.py"), _write(".flaskenv", "FLASK_APP=other:app\n"))),
    "module-raises": ("fixture", "script", {}, _write("wsgi.py", "raise RuntimeError('boom')\n")),
    "missing-package": ("fixture", "script", {}, _write("wsgi.py", "import not_installed\n")),
    "module-prints": ("fixture", "script", {}, lambda p: (p / "wsgi.py").write_text(
        "print('wsgi loaded')\n" + (p / "wsgi.py").read_text(encoding="utf-8"), encoding="utf-8")),
    "module-hangs": ("fixture", "hangs", {}, _write("wsgi.py", HANGS)),
    # after the JSON: a thread that never ends, a print at exit, a project that replaces `sys.stdout`
    "thread": ("fixture", "hangs", {}, _write("wsgi.py", THREAD)),
    "atexit-print": ("fixture", "script", {}, _write("wsgi.py", ATEXIT)),
    "replaced-stdout": ("fixture", "script", {}, _write("wsgi.py", REPLACED)),
    # a WSGI dispatcher, and what the module and the application hold: the one Flask instance of the module is mounted (`dispatcher`,
    # `dispatcher-server`), is the main application with another mounted (`dispatcher-main`, `dispatcher-wsgi-app`), or no dispatcher is there
    # (`dash-style`: `server = app.server` of an `app` that is not Flask; `imported-app-module`: `import app` and `server = app.app`)
    "dispatcher": ("fixture", "script", {}, _write("wsgi.py", DISPATCHER)),
    "dispatcher-server": ("fixture", "script", {}, _write("wsgi.py", DISPATCHER_SERVER)),
    "dispatcher-main": ("fixture", "script", {}, _write("wsgi.py", DISPATCHER_MAIN)),
    "dispatcher-wsgi-app": ("fixture", "script", {}, _write("wsgi.py", DISPATCHER_WSGI_APP)),
    "dispatcher-serves": ("fixture", "serves", {}, _write("wsgi.py", DISPATCHER)),  # what the dispatcher answers at `/sub/hello` and at `/hello`
    "dash-style": ("fixture", "script", {}, _both(_remove("wsgi.py"), _write("app.py", DASH))),
    "imported-app-module": ("fixture", "script", {}, _both(_write("app.py", IMPORTED_APP), _write("wsgi.py", IMPORTED_WSGI))),
    # the project closes (replaces) the descriptor the script saved for its answer
    "closes-answer": ("fixture", "script", {}, _write("wsgi.py", CLOSES)),
    "app-py": ("fixture", "script", {}, _rename("wsgi.py", "app.py")),
    "factory": ("fixture", "script", {}, _write("wsgi.py", FACTORY)),
    "factory-with-argument": ("fixture", "script", {}, _write("wsgi.py", FACTORY_ARGS)),
    "two-apps": ("fixture", "script", {}, _write("wsgi.py", TWO_APPS)),
    "werkzeug-source": ("fixture", "werkzeug", {}, None),  # what the installed werkzeug and flask say of `part_isolating`, of the methods, of `static`
    "url-matching": ("fixture", "matches", {}, None),  # what `url_map` matches, to set beside `part_isolating`
    "host-matching": ("fixture", "script", {}, _write("wsgi.py", HOSTS)),
    "no-rules": ("fixture", "script", {}, _write("wsgi.py", NO_RULES)),
    "many-routes": ("fixture", "script", {}, _write("wsgi.py", MANY)),  # 3000 rules, 6000 methods: time and memory, not recorded
    # the folders where the Python of the command is not `<venvs>/<folder>/bin/python`
    "uv-workspace": ("uv-workspace", "script", {}, None),
    "poetry": ("poetry", "script", {}, None),
    "root-and-sub": ("root-and-sub", "script", {}, None),
    "installed-copy": ("installed-copy", "script", {}, None),
}
RECORDED = ("routes", "no-wsgi", "flask-app-variable", "module-raises", "missing-package", "module-prints", "module-hangs", "app-py",
            "factory", "two-apps", "no-rules", "flaskenv-without-dotenv", "flaskenv-with-dotenv", "host-matching", "thread", "atexit-print",
            "replaced-stdout", "dispatcher", "dispatcher-server", "dispatcher-main", "dispatcher-wsgi-app", "dash-style",
            "imported-app-module", "closes-answer", *LAYOUTS)


def _listing(root: str) -> dict[str, int]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
    return out


def _run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
    import shutil
    import sys
    import time

    edit = VARIANTS[name][3]
    work = pathlib.Path(WORK)
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work)
    if edit:
        edit(work)
    os.makedirs(env["HOME"], exist_ok=True)
    before = _listing(WORK)
    mark = f"/tmp/rss-{name}"
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=work / cwd, capture_output=True, text=True, timeout=600,
                       stdin=subprocess.DEVNULL, env=env)
    seconds = round(time.monotonic() - started, 2)
    after = _listing(WORK)
    answer = {"variant": name, "argv": argv, "cwd": cwd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
              "seconds": seconds, "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
              "left_in_the_project": sorted(set(after) - set(before)),
              "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f])}
    if name == "environment":  # what the setup of the image did: its exit code, its seconds, what it wrote on the standard error
        answer["setup"] = {k: pathlib.Path(f"{state}/setup.{k}").read_text(encoding="utf-8").strip() for k in ("exit", "seconds", "stderr")}
    return answer


def _runner(folder: str):
    """The Modal function that runs a variant in the image of `folder`: one each, their names are their own."""
    def run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
        return _run(name, argv, env, state, cwd)
    run.__name__ = run.__qualname__ = "run_" + folder.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[folder], timeout=900, block_network=True)(run)
    return function


RUNNERS = {folder: _runner(folder) for folder in FOLDERS}


@app.function(image=IMAGES["fixture"], timeout=300, block_network=True)
def venv_dir(env: dict[str, str]) -> list[dict]:
    """`uv venv` on paths with and without the parent folder, and with the `/.` the root folder's restore ends in."""
    out = []
    for line in ("uv venv -q --python python3 /a/b/.", "mkdir -p /a/c && uv venv -q --python python3 /a/c/.",
                 "uv venv -q --python python3 /a/d/x", "uv venv -q --python python3 /a/e/f/g/.",
                 "uv venv -q --python python3 /a/h/i/g", "mkdir -p /a/k && uv venv -q --python python3 /a/k/x/.",
                 # the root folder's environment is the `<venvs>` directory itself: another folder's is a directory inside it
                 "mkdir -p /m && uv venv -q --python python3 /m/. && uv venv -q --python python3 /m/api",
                 "mkdir -p /n && uv venv -q --python python3 /n/api && uv venv -q --python python3 /n/."):
        r = subprocess.run(["sh", "-c", "export UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1; " + line], capture_output=True, text=True,
                           env=env, timeout=120)
        out.append({"line": line, "returncode": r.returncode, "stderr": r.stderr.strip(), "created": os.path.isfile(
            line.rsplit(" ", 1)[1].rstrip("/.").rstrip("/") + "/bin/python") if r.returncode == 0 else False})
    return out


@app.function(image=modal.Image.debian_slim(python_version="3.12").pip_install("uv==0.11.28", "poetry==2.1.3"), timeout=600)
def lock(command: list[str], files: dict[str, str], produces: str) -> str:
    """The lockfile a layout needs, made once with the network open: `uv lock` or `poetry lock` over the layout's manifests."""
    import tempfile
    with tempfile.TemporaryDirectory() as scratch:
        for rel, text in files.items():
            target = pathlib.Path(scratch, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        r = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=500, env={**os.environ, "UV_PYTHON_DOWNLOADS": "never"})
        if r.returncode:
            raise RuntimeError(f"{command} exited with {r.returncode}: {r.stderr[-800:]}")
        return pathlib.Path(scratch, produces).read_text(encoding="utf-8")


def _with_seconds(argv: list[str], seconds: str) -> list[str]:
    """The command with another limit: the one element that is only digits (`timeout`'s)."""
    at = next(i for i, word in enumerate(argv) if word.isdigit())
    return [*argv[:at], seconds, *argv[at + 1:]]


def _argv(folder: str, kind: str) -> tuple[list[str], str]:
    [command, *_] = PLANS[folder]["commands"] or [None]
    if command is None:
        raise SystemExit(f"{folder}: the source gives no command for this folder")
    argv, cwd = list(command["argv"]), command["cwd"]
    if kind == "script":
        return argv, cwd
    if kind == "script-dotenv":
        return [word.replace(PY, f"{PLANS[folder]['venvs']}-dotenv/bin/python") for word in argv], cwd
    if kind == "hangs":
        return _with_seconds(argv, "5"), cwd
    if kind == "environment":
        return [PY, "-c", ENVIRONMENT], "."
    if kind == "werkzeug":
        return [PY, "-c", WERKZEUG], "."
    if kind == "matches":
        return [PY, "-I", "-c", MATCHES], "."
    if kind == "serves":
        return [PY, "-I", "-c", SERVES], "."
    return [os.path.dirname(PY) + "/flask", *kind.split()[1:]], "."


def _recorded(answers: dict) -> None:
    RECORDED_DIR.mkdir(parents=True, exist_ok=True)
    for name in RECORDED:
        a = answers[name]
        (RECORDED_DIR / f"{name}.json").write_text(
            json.dumps({k: a[k] for k in ("returncode", "stdout", "stderr")}, indent=1) + "\n", encoding="utf-8")
    printed = hashlib.sha256(SCRIPT.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    (RECORDED_DIR / "script.json").write_text(
        json.dumps({"flask_routes.py": printed, "version": PLANS["fixture"]["version"]}, indent=1) + "\n", encoding="utf-8")


@app.local_entrypoint()
def main(mode: str = "routes", only: str = "", label: str = ""):
    OUT.mkdir(exist_ok=True)
    if mode == "venv-dir":
        answer = venv_dir.remote(PLANS["fixture"]["env"])
        (OUT / "venv-dir.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
        print(json.dumps(answer, indent=1))
        return
    if mode == "lock":
        for name, command, produces in (("uv-workspace", ["uv", "lock"], "uv.lock"), ("poetry", ["poetry", "lock"], "poetry.lock")):
            folder = FOLDERS[name]
            files = {path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8") for path in folder.rglob("*")
                     if path.is_file() and path.name not in ("uv.lock", "poetry.lock") and "__pycache__" not in path.parts}
            (folder / produces).write_text(lock.remote(command, files, produces), encoding="utf-8", newline="\n")
            print(name, produces, (folder / produces).stat().st_size)
        return
    out = OUT / label if label else OUT
    out.mkdir(exist_ok=True)
    chosen = set(only.split(",")) if only else set(VARIANTS)  # `--only environment,werkzeug-source`: some variants, nothing recorded
    answers = {}
    for folder, runner in RUNNERS.items():
        calls = []
        for name, (where, kind, env, _edit) in VARIANTS.items():
            if where == folder and name in chosen:
                argv, cwd = _argv(folder, kind)
                calls.append((name, argv, {**PLANS[folder]["env"], **env}, PLANS[folder]["state"], cwd))
        for answer in runner.starmap(calls):
            answers[answer["variant"]] = answer
            kept = {**answer, "stdout": answer["stdout"][:20000], "stdout_chars": len(answer["stdout"])}  # the answer in full is in `RECORDED`
            (out / f"{answer['variant']}.json").write_text(json.dumps(kept, indent=1), encoding="utf-8")
    if not only and not label:
        _recorded(answers)
    print(json.dumps({v: [a["returncode"], a["seconds"], a["max_rss_mb"]] for v, a in answers.items()}, indent=1))
