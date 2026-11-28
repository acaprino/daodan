"""Flask's own `url_map` (the source of the pre-map) and the pinned Noir's routes on real public Flask applications, on Modal.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_real.py
    ... modal_real.py --only ctfd-noir,ctfd-script        some variants

The applications are `apps.APPS`: each is fetched at a pinned commit (`https://codeload.github.com/<repo>/tar.gz/<sha>`) while the image is built, with
the network open, and so are the packages Daodan's own restore installs (`plan.py` over the project's folder, fetched as text on the host by
`apps.fetch`, never run: the same commands and restore lines the runner would give) and the Noir that `entry_points/noir.py` pins (sha256 checked). Nothing
of the applications is kept in the repository: the answers are (`results/real/`). Then, with the network blocked and in a copy of the project at
`/work`: Daodan's own rewrite of the `.env` files (`container.named`, which the runner applies before every command of a pre-map), then `noir scan
/work -f json --no-log` (what `noir.commands` gives), or the script of the source (the command of `flask_app.commands`). `fixture` is this
folder's own `fixture/`, built the same way (only for Noir: its script's answer is `results/routes.json`, which `modal_probe.py` records). The plain
`<name>-script` is the command of the source as the runner gives it; `EXTRA` has the variants that add what the project needs and the runner does not
give (`FLASK_APP`, a secret, a Redis), to tell what survives. `real_summary.py` reads the answers with the sources.
"""
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
if LOCAL:
    sys.path.insert(0, str(HERE))
    import apps  # noqa: E402
REPO = HERE.parents[1] if LOCAL else HERE
OUT = HERE / "results" / "real"
WORK = "/work"  # `container.WORKDIR`
NAMES = ("ctfd", "redash", "redash-frozen", "shhh", "microblog-api", "fixture")
# image -> the application it holds, when not its own name. `redash-frozen` is `redash` restored with `uv sync --frozen` where Daodan's line says
# `--locked`: the uv.lock of Redash's commit is behind its pyproject.toml (`The lockfile at uv.lock needs to be updated`), which `--locked` does not take
SAME = {"redash-frozen": "redash"}
# variant -> the environment variables it adds to the runner's (the plain `-script` is what Daodan's runner runs, and the number the verdict rests on; these
# are what survives when what stops it is out of the way, one obstacle more at each step): `FLASK_APP` is where Flask's loader is told the application is,
# as `flask --app` would be; Redash asks for a cookie secret when its settings are imported and for a Redis when its application is made; shhh reads
# `FLASK_ENV` itself to choose its configuration
SECRET = {"REDASH_COOKIE_SECRET": "daodan-measure"}
EXTRA = {"redash-frozen-script-declared": ("redash-frozen", {"FLASK_APP": "redash.wsgi"}),
         "redash-frozen-script-secret": ("redash-frozen", {"FLASK_APP": "redash.wsgi", **SECRET}),
         "redash-frozen-script-redis": ("redash-frozen", {"FLASK_APP": "redash.wsgi", **SECRET}),
         "shhh-script-testing": ("shhh", {"FLASK_ENV": "testing"})}
# variant -> a shell that runs after the `.env` rewrite and before the command: Redash's Redis, a daemon on the loopback of the container
REDIS = ("redis-server --daemonize yes --save '' --appendonly no --bind 127.0.0.1 > /dev/null && "
         "for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do redis-cli ping 2> /dev/null | grep -q PONG && break; sleep 0.5; done\n")
BEFORE = {"redash-frozen-script-redis": REDIS}
MEMORY = 3072  # MB: `container_runner.TOOLS["flask"]["memory"]`, 3 GB


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


if LOCAL:
    sys.path.insert(0, str(REPO / "daodan/core"))
    import container  # noqa: E402  (Daodan's own: the rewrite of the `.env` files the runner applies)

    TREES = pathlib.Path(os.environ.get("DAODAN_FLASK_APPS") or pathlib.Path(tempfile.gettempdir()) / "flask-apps")  # the sources, as text, and the plans
    FOLDERS = {name: apps.fetch(name, TREES) if name != "fixture" else HERE / "fixture" for name in NAMES if name not in SAME}

    def _cached(name: str) -> dict:
        """`plan.py`'s answer for a folder, kept in `<TREES>/<name>-plan.json`: it takes minutes on a large project (the snapshot of its files), and it
        is the same while the commit and Daodan's restore lines are; delete the file to take it again."""
        cache = TREES / f"{name}-plan.json"
        if not cache.is_file():
            cache.write_text(json.dumps(_plan(FOLDERS[name])), encoding="utf-8")
        return json.loads(cache.read_text(encoding="utf-8"))
    PLANS = {name: _cached(name) for name in NAMES if name not in SAME}
    NAMED = container.named()
else:
    PLANS, NAMED = None, ""


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    application = SAME.get(name, name)
    plan = PLANS[application]
    state, inputs = plan["state"], plan["inputs"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    for url, sha, file in plan["files"]:
        if url:  # a download of the runner (`uv`), checked by its sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        else:  # Daodan's own file, beside the premap modules
            image = image.add_local_file(REPO / "daodan/core/premap" / file, f"{inputs}/{file}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2].replace("--locked", "--frozen") if name == "redash-frozen" else plan["setup"]["argv"][2])
    if name == "redash-frozen":  # the Redis its application is made against (`create_app` asks for its version)
        image = image.run_commands("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends redis-server > /dev/null"
                                   " && rm -rf /var/lib/apt/lists/*")
    image = image.run_commands(f"curl -fsSL -o /usr/local/bin/noir {apps.NOIR[0]} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
    if name == "fixture":
        image = image.add_local_dir(FOLDERS[application], "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
    else:
        repository, commit, _, folder, _ = apps.APPS[application]
        image = image.run_commands(f"mkdir -p /src /fix && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /src --strip-components=1"
                                   f" && cp -a /src/{folder}/. /fix/ && rm -rf /src")
    # the runner's setup, run as the runner runs it (`sh -c`, its environment, the project's folder, which is `/work`); a failed restore does not fail the
    # build (the restore line ends in `true`): its standard error, exit code and seconds are kept
    return image.run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && s=$(date +%s) && "
                              f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                              f"echo $(( $(date +%s) - s )) > {state}/setup.seconds")


IMAGES = {name: _image(name) for name in NAMES}
app = modal.App("flask-real-applications")

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
ENVIRONMENT = (
    "import importlib.metadata as m, sys\n"
    "def version(name):\n"
    "    try:\n"
    "        return m.version(name)\n"
    "    except m.PackageNotFoundError:\n"
    "        return None\n"
    "print(repr({'python': sys.version, 'executable': sys.executable, 'flask': version('flask'), 'werkzeug': version('werkzeug'),\n"
    "            'extensions': {n: version(n) for n in ('flask-restx', 'flask-restful', 'flask-admin', 'flask-smorest', 'apifairy', 'flask-appbuilder', 'flask-dotenv', 'python-dotenv')\n"
    "                           if version(n)}, 'packages': len(list(m.distributions()))}))\n")


def _listing(root: str) -> dict[str, int]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            try:
                out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
            except OSError:
                pass
    return out


def _run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str, rewrite: str) -> dict:
    """One variant in a copy of the project at `/work`, with the network blocked: `rewrite` (Daodan's `.env` rewrite, or nothing), then `argv`."""
    import shutil
    import time

    work = pathlib.Path(WORK)
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work, symlinks=True)
    os.makedirs(env["HOME"], exist_ok=True)
    if rewrite:
        subprocess.run(["sh", "-c", rewrite], cwd=work, env=env, check=True, capture_output=True, text=True)
    before = _listing(WORK)
    mark = f"/tmp/rss-{name}"
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=work / cwd, capture_output=True, text=True, timeout=1500,
                       stdin=subprocess.DEVNULL, env=env)
    seconds = round(time.monotonic() - started, 2)
    after = _listing(WORK)
    answer = {"variant": name, "argv": argv, "cwd": cwd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "seconds": seconds,
              "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
              "left_in_the_project": sorted(set(after) - set(before))[:40], "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f])[:40],
              "files": len(before)}
    if name.endswith("environment"):
        answer["setup"] = {k: pathlib.Path(f"{state}/setup.{k}").read_text(encoding="utf-8").strip()[-1500:] for k in ("exit", "seconds", "stderr")}
    return answer


def _runner(name: str):
    def run(variant: str, argv: list[str], env: dict[str, str], state: str, cwd: str, rewrite: str) -> dict:
        return _run(variant, argv, env, state, cwd, rewrite)
    run.__name__ = run.__qualname__ = "run_" + name.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[name], timeout=1800, block_network=True, memory=MEMORY)(run)
    return function


RUNNERS = {name: _runner(name) for name in NAMES}


def _variants() -> dict[str, tuple[str, list[str], str, str, dict]]:
    """variant -> (image, argv, cwd, the rewrite that runs first, the environment variables it adds)."""
    out = {}
    for name in NAMES:
        plan = PLANS[SAME.get(name, name)]
        python = f"{plan['venvs']}/./bin/python"
        [command, *_] = plan["commands"] or [None]
        out[f"{name}-environment"] = (name, [python, "-c", ENVIRONMENT], ".", "", {})
        if name not in SAME:  # the same project, so the same answer of Noir
            out[f"{name}-noir"] = (name, ["noir", "scan", WORK, "-f", "json", "--no-log"], ".", NAMED, {})
        if command and name != "fixture":  # the fixture's script is `modal_probe.py`'s `routes`
            out[f"{name}-script"] = (name, command["argv"], command["cwd"], NAMED, {})
    for variant, (name, extra) in EXTRA.items():
        [command, *_] = PLANS[SAME.get(name, name)]["commands"]
        out[variant] = (name, command["argv"], command["cwd"], NAMED + BEFORE.get(variant, ""), extra)
    return out


@app.local_entrypoint()
def main(only: str = ""):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, plan in PLANS.items():  # what the runner's code gave for each folder (`plan.py`), kept with the answers it produced
        (OUT / f"{name}-plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    variants = _variants()
    chosen = set(only.split(",")) if only else set(variants)
    for name, runner in RUNNERS.items():
        calls = []
        for variant, (image, argv, cwd, rewrite, extra) in variants.items():
            if image == name and variant in chosen:
                plan = PLANS[SAME.get(name, name)]
                calls.append((variant, argv, {**plan["env"], **extra}, plan["state"], cwd, rewrite))
        for answer in (runner.starmap(calls) if calls else ()):
            (OUT / f"{answer['variant']}.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
            print(answer["variant"], answer["returncode"], answer["seconds"], answer["max_rss_mb"], len(answer["stdout"]))
