"""Django's own loaded URLconf and OWASP Noir over the same trees on Modal: the fixture and public Django projects, the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/django-routes/real_probe.py
    ... --only healthchecks-script,healthchecks-noir        some variants

Each public project is fetched during the image build (the one moment the network is open) at the commit `REAL` pins and is never copied into
this repository: `git fetch --depth 1 <url> <sha>`, the `.git` folder removed, the tree set at `/work` (`container.WORKDIR`). A local checkout of the
same commit (`DAODAN_REAL_DIR`, default `D:\\daodan-work\\django-probe\\real\\<name>`, made with `git init`, `git fetch --depth 1 <url> <sha>` and
`git checkout FETCH_HEAD`) is read by `plan.py` for the names of its files only (the restore lines and the command `django_app.commands` gives)
and by `compare.py` (the snapshot the binder ties the rows to): nothing of it runs on this machine. The restore is Daodan's own
(`container_runner._python`, here `uv venv` and `uv pip install -r requirements.txt` of the folder), run as the runner runs it; then
each variant runs in a copy of the tree with the network blocked, in Daodan's environment (`preparation.ENV`):

    <name>-environment   the Python, the packages, and what the setup of the image did (exit code, seconds, standard error)
    <name>-script        `entry_points/django_routes.py`, the command `django_app.commands` gives: the answer the source reads
    <name>-noir          `noir scan /work -f json --no-log`, the command `entry_points/noir.py` gives, Noir 1.5.0 (the pinned one)
    <name>-script-fixed  the script in the second environment, for the projects whose pinned requirements need a C compiler the image's Python does not use
    <name>-script-env    the script again with the environment variables the settings ask for, where the first run says it needs them

The answers are kept whole under `DAODAN_REAL_OUT` (default `D:\\daodan-work\\django-probe\\real-results`), outside the repository: they hold the
routes and the names of the functions of projects that are not ours. `compare.py` reads them with the checkouts and writes the counts and the
differences, without the source, to `results/real/`.
"""
import json
import os
import pathlib
import shlex
import subprocess

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()
OUT = pathlib.Path(os.environ.get("DAODAN_REAL_OUT", r"D:\daodan-work\django-probe\real-results"))
CHECKOUTS = pathlib.Path(os.environ.get("DAODAN_REAL_DIR", r"D:\daodan-work\django-probe\real"))
REAL = {  # name -> (repository, commit, licence): what the README records
    "healthchecks": ("https://github.com/healthchecks/healthchecks.git", "c1039ad23395162c5e2f17d324d8ccdaa60a1d14", "BSD-3-Clause"),
    "defectdojo": ("https://github.com/DefectDojo/django-DefectDojo.git", "cd0a4483a224707f72a0fc3112359089c1446b55", "BSD-3-Clause"),
    "bakerydemo": ("https://github.com/wagtail/bakerydemo.git", "890285b95dcf980215ab9e9942d64ed2b47c48c3", "BSD-3-Clause"),
}
# the variables a project's settings ask for, where its first run says so (the answer of `<name>-script-env`)
ENVIRONMENT = {"healthchecks": {}, "defectdojo": {}, "bakerydemo": {}}
# the projects whose pinned requirements include a package that is built from source (uWSGI, `psycopg[c]`, pycurl): Modal's Python (3.12.1 in
# `/usr/local`) was built with Clang and says so in its `sysconfig`, and the image has GCC only, so `uv pip install` of them fails in the restore as
# the runner makes it ("command 'clang' failed"); in Daodan's own container the Python is the image's, built with GCC (not measured here). The
# second environment, `<venvs>-fixed`, is the same restore with `CC=gcc CXX=g++`: nothing of the project is edited
COMPILED = ("defectdojo", "bakerydemo")
FOLDERS = {"fixture": HERE / "fixture", "drf": HERE / "layouts" / "drf", **{name: CHECKOUTS / name for name in REAL}}  # `drf`: the control, known routes
WORK = "/work"


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


PLANS = {name: _plan(folder) for name, folder in FOLDERS.items()} if LOCAL else None
SCRIPT = HERE.parents[1] / "daodan/core/entry_points/django_routes.py" if LOCAL else None  # in a container this file lies at /root


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    plan = PLANS[name]
    state, inputs, tools = plan["state"], plan["inputs"], plan["tools"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    for url, sha, file in [*plan["files"], plan["noir"]]:
        if url:  # a download of the runner (`uv`) and of the pre-map (Noir), checked by their sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        else:
            image = image.add_local_file(SCRIPT, f"{inputs}/{file}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2])
    if name in REAL:
        url, sha, _licence = REAL[name]
        image = image.run_commands(f"mkdir -p /fix && cd /fix && git init -q && git fetch -q --depth 1 {shlex.quote(url)} {sha} && git checkout -q FETCH_HEAD && rm -rf .git")
    else:
        image = image.add_local_dir(FOLDERS[name], "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
    image = image.run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && s=$(date +%s) && "
                               f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                               f"echo $(( $(date +%s) - s )) > {state}/setup.seconds")
    if name in COMPILED:  # the second environment: the same restore (`uv venv`, `uv pip install -r`), built with GCC
        fixed = shlex.quote(f"s=$(date +%s); uv venv -q --python python3 {plan['venvs']}-fixed && CC=gcc CXX=g++ "
                            f"uv pip install -q --python {plan['venvs']}-fixed -r requirements.txt 2> {state}/fixed.stderr; "
                            f"echo $? > {state}/fixed.exit; echo $(( $(date +%s) - s )) > {state}/fixed.seconds")
        image = image.run_commands(f"cd /fix && env -i {env} sh -c {fixed}")
    return image.run_commands(f"mkdir -p {tools}/bin && install -m 755 {inputs}/noir {tools}/bin/noir")


IMAGES = {name: _image(name) for name in FOLDERS}
app = modal.App("django-routes-real")

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
PACKAGES = (
    "import importlib.metadata as m, sys\n"
    "print(repr({'version': sys.version, 'executable': sys.executable, 'django': m.version('django'),\n"
    "            'packages': sorted(f\"{d.metadata['Name']} {d.version}\" for d in m.distributions())}))\n")


def _run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
    import shutil
    import sys
    import time
    work = pathlib.Path(WORK)
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work, symlinks=True)  # a project may hold links that lead nowhere
    os.makedirs(env["HOME"], exist_ok=True)
    mark = f"/tmp/rss-{name}"
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=work / cwd, capture_output=True, text=True, timeout=3000,
                       stdin=subprocess.DEVNULL, env=env)
    answer = {"variant": name, "argv": argv, "cwd": cwd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
              "seconds": round(time.monotonic() - started, 2),
              "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None}
    if name.endswith("-environment"):
        answer["setup"] = {k: pathlib.Path(f"{state}/setup.{k}").read_text(encoding="utf-8").strip() for k in ("exit", "seconds", "stderr")}
        if pathlib.Path(f"{state}/fixed.exit").exists():
            answer["fixed"] = {k: pathlib.Path(f"{state}/fixed.{k}").read_text(encoding="utf-8").strip() for k in ("exit", "seconds", "stderr")}
    return answer


def _runner(folder: str):
    def run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str) -> dict:
        return _run(name, argv, env, state, cwd)
    run.__name__ = run.__qualname__ = "run_" + folder
    globals()[run.__name__] = function = app.function(image=IMAGES[folder], timeout=3300, block_network=True, memory=4096, cpu=2)(run)
    return function


RUNNERS = {folder: _runner(folder) for folder in FOLDERS}


def _argv(folder: str, kind: str) -> list[str]:
    plan = PLANS[folder]
    if kind == "script-fixed":  # the same command in the second environment
        py = plan["interpreters"]["."]
        return [word.replace(py, shlex.quote(f"{plan['venvs']}-fixed/bin/python")) for word in _argv(folder, "script")]
    if kind == "environment":
        return [plan["interpreters"]["."], "-c", PACKAGES]
    if kind == "noir":
        [command] = plan["noir_commands"]
        return ["timeout", "--kill-after=10", "1200", *command["argv"]]
    found = [c for c in plan["commands"] if c["cwd"] == "."]
    if found:
        return found[0]["argv"]
    # the source gives no command (Django is declared in a file the pre-map does not read, `requirements/base.txt` behind a `-r`): the one it would
    # give if it saw it, to measure what the script reads of the project; the README says which projects this is
    return ["sh", "-c", f'exec timeout --kill-after=10 "$1" {plan["interpreters"]["."]} -I "$2"', "django", "900", f"{plan['tools']}/django_routes.py"]


@app.local_entrypoint()
def main(only: str = ""):
    OUT.mkdir(parents=True, exist_ok=True)
    chosen = set(only.split(",")) if only else None
    work = {}
    for folder, runner in RUNNERS.items():
        calls = []
        for kind in ("environment", "script", "noir", "script-fixed", "script-env"):
            name = f"{folder}-{kind}"
            if chosen is not None and name not in chosen or kind == "script-env" and not (chosen and name in chosen):
                continue
            if kind == "script-fixed" and folder not in COMPILED:
                continue
            extra = ENVIRONMENT.get(folder, {}) if kind == "script-env" else {}
            argv = _argv(folder, "script-fixed" if kind in ("script-fixed",) else "script" if kind == "script-env" else kind)
            if kind == "script-env" and folder in COMPILED:
                argv = _argv(folder, "script-fixed")  # the second environment is the one that has Django
            calls.append((name, argv, {**PLANS[folder]["env"], **extra}, PLANS[folder]["state"], "."))
        if calls:
            work[folder] = (runner, calls)
    from concurrent.futures import ThreadPoolExecutor  # the images start together: a slow one does not hold the others back

    def one(item):
        for answer in item[0].starmap(item[1]):
            (OUT / f"{answer['variant']}.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
            print(answer["variant"], answer["returncode"], answer["seconds"], answer["max_rss_mb"], len(answer["stdout"]), flush=True)
    with ThreadPoolExecutor(max_workers=len(work) or 1) as pool:
        list(pool.map(one, work.values()))
