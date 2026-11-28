"""Django's own loaded URLconf on Modal, in the runner's container image, with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/django-routes/modal_probe.py --mode explore
    ... --mode explore --only dump,launch-a-fixture        some variants of the exploratory run
    ... --mode record                                      the variants the tests read, written to `tests/fixtures/premap/django/`
    ... --mode record --label name                         the same, answers kept under `results/name/`, nothing recorded

The image is Daodan's (`container_runner.IMAGE`, with Modal's Python added beside it), and what Daodan's runner does before a command is done by
the same lines: `plan.py` (run with the Python that has Daodan's own dependencies, `DAODAN_PYTHON` names it, default `python`) prints, for a
project folder, the setup command `container_runner.plan` gives, the restore lines `container_runner._python` makes, the Python of each
environment and, once `entry_points/django_app.py` exists, the commands it gives. There is one image for the `fixture` and one for each folder of
`layouts/`, plus two with another Django (4.2 and 5.2): the image build, the one moment the network is open, unpacks Daodan's files at
`preparation.IN`, copies the folder to `/work` (`container.WORKDIR`) and runs the setup command there, with the runner's environment
(`preparation.ENV`). Each variant then runs in a copy of its folder at `/work`, with the network blocked and the same environment, and its
answer (`argv`, `returncode`, `stdout`, `stderr`, seconds, peak memory, the files it left in the project) goes to `results/<variant>.json`.
The project's code runs only in the container. What differs from Daodan's own container: Modal's runtime, and the Python Modal installs in
`/usr/local/bin` (3.12.1), which is the `python3` the restore's `uv venv --python python3` picks.

`--mode explore` runs the exploratory scripts of `probe/` (`dump.py`: the loaded URLconf level by level; `launch.py`: three ways of running
the project's own `manage.py`) over the variants of `VARIANTS`. `--mode record` runs the source's own script (`entry_points/django_routes.py`,
the commands `django_app.commands` gives) and writes the answers in `RECORDED` as `tests/fixtures/premap/django/<variant>.json` with the sha256
of the script and the `VERSION` of the source (`script.json`): if the script changes, record again and raise the `VERSION`.
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
RECORDED_DIR = REPO / "tests/fixtures/premap/django"
SCRIPT = REPO / "daodan/core/entry_points/django_routes.py"
LAYOUTS = ("subfolder", "two-projects", "no-manage", "custom-launcher", "installed-copy", "drf")
OTHER_DJANGO = {"django42": "django==4.2.*", "django52": "django==5.2.*"}
FOLDERS = {"fixture": HERE / "fixture", **{name: HERE / "layouts" / name for name in LAYOUTS}, **{name: HERE / "fixture" for name in OTHER_DJANGO}}
WORK = "/work"  # `container.WORKDIR`


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


PLANS = {name: _plan(folder) for name, folder in FOLDERS.items()} if LOCAL else None
STATE = PLANS["fixture"]["state"] if LOCAL else "/daodan/state"
IN = PLANS["fixture"]["inputs"] if LOCAL else "/daodan/state/in"
TOOLS = PLANS["fixture"]["tools"] if LOCAL else "/daodan/state/tools"


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    plan = PLANS[name]
    state, inputs = plan["state"], plan["inputs"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    for url, sha, file in plan["files"]:
        if url:  # a download of the runner (`uv`), checked by its sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        elif file == "django_routes.py":  # Daodan's own script, beside the premap modules; absent while only the exploration runs
            if SCRIPT.exists():
                image = image.add_local_file(SCRIPT, f"{inputs}/{file}", copy=True)
            else:
                image = image.run_commands(f"printf '' > {inputs}/{file}")
    for probe in ("launch.py", "dump.py"):
        image = image.add_local_file(HERE / "probe" / probe, f"{inputs}/{probe}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2])
    pin = OTHER_DJANGO.get(name)
    repin = f"printf '%s\\n' {shlex.quote(pin)} > requirements.txt && " if pin else ""
    image = (image.add_local_dir(FOLDERS[name], "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
             # the runner's setup, run as the runner runs it (`sh -c`, its environment, the project's folder, which is `/work`); a failed
             # restore does not fail the build (the restore line ends in `true`): its standard error and exit code are kept
             .run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && {repin}s=$(date +%s) && "
                           f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                           f"echo $(( $(date +%s) - s )) > {state}/setup.seconds"))
    if name == "fixture":  # a second environment, with a PostgreSQL driver beside Django, for the variant that names the engine
        psycopg = f"{plan['venvs']}-psycopg"
        with_driver = shlex.quote(f"uv venv -q --python python3 {psycopg} && uv pip install -q --python {psycopg} -r requirements.txt 'psycopg[binary]'")
        image = image.run_commands(f"cd /fix && env -i {env} sh -c {with_driver}")
    return image


IMAGES = {name: _image(name) for name in FOLDERS}
app = modal.App("django-routes")

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
ENVIRONMENT = (
    "import importlib.metadata as m, os, sys, sysconfig\n"
    "paths = sysconfig.get_paths()\n"
    "print(repr({'version': sys.version, 'executable': sys.executable, 'purelib': paths['purelib'], 'django': m.version('django'),\n"
    "            'packages': sorted(f\"{d.metadata['Name']} {d.version}\" for d in m.distributions())}))\n")


def _write(name: str, text: str):
    return lambda p: (p / name).write_text(text, encoding="utf-8")


def _append(name: str, text: str):
    return lambda p: (p / name).write_text((p / name).read_text(encoding="utf-8") + text, encoding="utf-8")


def _prepend(name: str, text: str):
    return lambda p: (p / name).write_text(text + (p / name).read_text(encoding="utf-8"), encoding="utf-8")


def _replace(name: str, old: str, new: str):
    return lambda p: (p / name).write_text((p / name).read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def _both(*edits):
    return lambda p: [edit(p) for edit in edits]


SETTINGS = "config/settings.py"
READY = ("from django.apps import AppConfig\n\n\nclass ShopConfig(AppConfig):\n    name = \"shop\"\n\n    def ready(self):\n"
         "        from shop.models import Product\n\n        Product.objects.count()\n")
POSTGRES = ('\nDATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "x", "HOST": "db.invalid", "USER": "u", "PASSWORD": "p"}}\n')
NEEDS_ENV = 'import os\n\nSECRET_KEY = os.environ["SECRET_KEY"]\n'
NO_CALL = ("import os\nimport sys\n\nos.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')\n"
           "if __name__ == '__main__':\n    print('manage.py with no command', file=sys.stderr)\n")

# edit name -> how the copy of the fixture is edited
EDITS = {
    "ok": None,
    "settings-error": _write(SETTINGS, "import not_installed\n"),
    "settings-needs-env": _prepend(SETTINGS, NEEDS_ENV),
    "urls-error": _write("config/urls.py", "import not_installed\n"),
    "hangs": _prepend(SETTINGS, "import time\n\ntime.sleep(120)\n"),
    "thread": _prepend(SETTINGS, "import threading\nimport time\n\nthreading.Thread(target=time.sleep, args=(100000,)).start()\n"),
    "atexit-print": _prepend(SETTINGS, "import atexit\n\natexit.register(lambda: print('goodbye'))\n"),
    "replaced-stdout": _append(SETTINGS, "\nimport io\nimport sys\n\nsys.stdout = io.StringIO()\n"),
    "prints": _prepend(SETTINGS, "print('settings loaded')\n"),
    "db-none": _append(SETTINGS, "\nDATABASES = {}\n"),
    "db-postgres-no-driver": _append(SETTINGS, POSTGRES),
    "db-postgres-driver": _append(SETTINGS, POSTGRES),
    "ready-queries": _write("shop/apps.py", READY),
    "urls-queries": _prepend("config/urls.py", "from shop.models import Product\n\nProduct.objects.count()\n"),
    "debug-static": _append(SETTINGS, "\nDEBUG = True\n"),
    "broken-include": _write("shop/dash_urls.py", "import not_installed\n"),  # `include("shop.dash_urls")` imports it where `urls.py` is read
    "no-patterns-include": _write("shop/dash_urls.py", "x = 1\n"),  # the include `URLResolver.url_patterns` refuses (not iterable), later, at the walk
    "manage-no-call": _write("manage.py", NO_CALL),
    # the project without the admin among its installed apps and in its URLconf: is Django's own `admindocs` importable then
    "no-admin": _both(_append(SETTINGS, '\nINSTALLED_APPS = ["shop"]\n'), _replace("config/urls.py", 'path("admin/", admin.site.urls),', ""),
                      _replace("config/urls.py", "from django.contrib import admin\n", "")),
}
WAYS = ("launch-a", "launch-b", "launch-c")

# variant -> (image, kind, edit, cwd, environment of the Python, seconds the command has)
VARIANTS = {"environment": ("fixture", "environment", "ok", ".", ".", "60")}
VARIANTS["dump"] = ("fixture", "dump", "ok", ".", ".", "120")
for way in (*WAYS, "launch-a-I"):
    VARIANTS[f"{way}-fixture"] = ("fixture", way, "ok", ".", ".", "60")
for edit in EDITS:
    if edit != "ok":
        VARIANTS[f"dump-{edit}"] = ("fixture", "dump", edit, ".", ".", "5" if edit in ("hangs", "thread") else "60")
        for way in WAYS:
            VARIANTS[f"{way}-{edit}"] = ("fixture", way, edit, ".", ".", "5" if edit in ("hangs", "thread") else "60")
for name in OTHER_DJANGO:
    VARIANTS[f"dump-{name}"] = (name, "dump", "ok", ".", ".", "120")
    for way in WAYS:
        VARIANTS[f"{way}-{name}"] = (name, way, "ok", ".", ".", "60")
for layout, cwd, env in (("subfolder", "src", "."), ("two-projects", "a", "a"), ("two-projects", "b", "b"), ("no-manage", ".", "."),
                         ("custom-launcher", ".", "."), ("installed-copy", ".", "."), ("drf", ".", ".")):
    tag = f"{layout}-{cwd}" if layout == "two-projects" else layout
    for way in WAYS:
        VARIANTS[f"{way}-{tag}"] = (layout, way, "ok", cwd, env, "60")
    VARIANTS[f"dump-{tag}"] = (layout, "dump", "ok", cwd, env, "120")
# the source's own script (`entry_points/django_routes.py`, the command `django_app.commands` gives), over the variants the tests read: the answers of
# `--mode record`. `hangs` and `thread` run with 5 seconds, `db-postgres-driver` in the environment that has the driver
for edit in EDITS:
    if edit != "ok":
        VARIANTS[edit] = ("fixture", "script-psycopg" if edit == "db-postgres-driver" else "script", edit, ".", ".", "5" if edit in ("hangs", "thread") else "")
VARIANTS["routes"] = ("fixture", "script", "ok", ".", ".", "")
for name in OTHER_DJANGO:
    VARIANTS[f"routes-{name}"] = (name, "script", "ok", ".", ".", "")
for layout, cwd, env in (("subfolder", "src", "."), ("two-projects", "a", "a"), ("two-projects", "b", "b"), ("custom-launcher", ".", "."),
                         ("installed-copy", ".", "."), ("drf", ".", ".")):
    VARIANTS[f"routes-{layout}-{cwd}" if layout == "two-projects" else f"routes-{layout}"] = (layout, "script", "ok", cwd, env, "")
RECORDED = ("routes", "routes-django42", "routes-django52", "settings-error", "settings-needs-env", "urls-error", "hangs", "thread", "atexit-print",
            "replaced-stdout", "prints", "db-none", "db-postgres-no-driver", "db-postgres-driver", "ready-queries", "urls-queries", "debug-static",
            "broken-include", "no-patterns-include", "no-admin", "manage-no-call", "routes-subfolder", "routes-two-projects-a", "routes-two-projects-b", "routes-custom-launcher",
            "routes-installed-copy", "routes-drf")


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

    edit = EDITS[VARIANTS[name][2]]
    work = pathlib.Path(WORK)
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work)
    pin = OTHER_DJANGO.get(VARIANTS[name][0])
    if pin:
        (work / "requirements.txt").write_text(pin + "\n", encoding="utf-8")
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
              "left_in_the_project": sorted(f for f in set(after) - set(before) if "__pycache__" not in f),
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


def _with_seconds(argv: list[str], seconds: str) -> list[str]:
    """The command with another limit: the one element that is only digits (`timeout`'s)."""
    at = next(i for i, word in enumerate(argv) if word.isdigit())
    return [*argv[:at], seconds, *argv[at + 1:]]


def _argv(image: str, kind: str, env: str, seconds: str, edit: str, cwd: str = ".") -> list[str]:
    py = PLANS[image]["interpreters"][env]
    if edit == "db-postgres-driver":  # the same project in the environment that also has the driver
        py = shlex.quote(f"{PLANS[image]['venvs']}-psycopg/bin/python")
    if kind in ("script", "script-psycopg"):  # what the source gives: the command `django_app.commands` makes for this folder
        found = [c for c in PLANS[image]["commands"] if c["cwd"] == cwd]
        if not found:
            raise SystemExit(f"{image}/{cwd}: the source gives no command")
        argv = list(found[0]["argv"])
        if kind == "script-psycopg":
            argv = [word.replace(PLANS[image]["interpreters"][env], py) for word in argv]
        return _with_seconds(argv, seconds) if seconds else argv
    shell = "exec 3>&1 1>&2; exec timeout --kill-after=10 \"$1\" "
    if kind == "environment":
        return [py.strip("'"), "-c", ENVIRONMENT]
    if kind in ("dump", "launch-a", "launch-a-I"):
        code = ("exec(open('%s/dump.py').read())" % IN if kind == "dump" else
                "import runpy; runpy.run_path('%s/launch.py', run_name='a')" % IN)
        flag = " -I" if kind == "launch-a-I" else ""
        return ["sh", "-c", f'{shell}{py}{flag} manage.py shell -c "$2"', "django", seconds, code]
    if kind in ("launch-b", "launch-c"):
        return ["sh", "-c", f'exec timeout --kill-after=10 "$1" {py} -I "$2" "$3"', "django", seconds, f"{IN}/launch.py", kind[-1]]
    raise SystemExit(f"no way to run {kind}")


def _recorded(answers: dict) -> None:
    RECORDED_DIR.mkdir(parents=True, exist_ok=True)
    for name in RECORDED:
        a = answers[name]
        (RECORDED_DIR / f"{name}.json").write_text(
            json.dumps({k: a[k] for k in ("returncode", "stdout", "stderr")}, indent=1) + "\n", encoding="utf-8")
    printed = hashlib.sha256(SCRIPT.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    (RECORDED_DIR / "script.json").write_text(
        json.dumps({"django_routes.py": printed, "version": PLANS["fixture"]["version"]}, indent=1) + "\n", encoding="utf-8")


@app.local_entrypoint()
def main(mode: str = "explore", only: str = "", label: str = ""):
    OUT.mkdir(exist_ok=True)
    out = OUT / label if label else OUT
    out.mkdir(exist_ok=True)
    chosen = set(only.split(",")) if only else set(VARIANTS)
    answers, work = {}, {}
    for folder, runner in RUNNERS.items():
        calls = []
        for name, (image, kind, edit, cwd, env, seconds) in VARIANTS.items():
            if image == folder and name in chosen and kind.startswith("script") == (mode == "record"):
                calls.append((name, _argv(image, kind, env, seconds, edit, cwd), PLANS[image]["env"], PLANS[image]["state"], cwd))
        if calls:
            work[folder] = (runner, calls)
    # the images start together: one that is slow to start does not hold the others back
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(work) or 1) as pool:
        for found in pool.map(lambda item: list(item[0].starmap(item[1])), work.values()):
            for answer in found:
                answers[answer["variant"]] = answer
                cap = 10**6 if answer["variant"].startswith("dump") else 60000  # the dump is read in full
                kept = {**answer, "stdout": answer["stdout"][:cap], "stdout_chars": len(answer["stdout"])}
                (out / f"{answer['variant']}.json").write_text(json.dumps(kept, indent=1), encoding="utf-8")
    if mode == "record" and not only and not label:
        _recorded(answers)
    print(json.dumps({v: [a["returncode"], a["seconds"], a["max_rss_mb"]] for v, a in answers.items()}, indent=1))
