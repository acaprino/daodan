"""The framework's own routes and the pinned Noir's, on real public FastAPI applications, on Modal.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_real.py
    ... modal_real.py --only template-noir,template-script        some variants

The applications are `apps.APPS`: each is fetched at a pinned commit (`https://codeload.github.com/<repo>/tar.gz/<sha>`) while the image is built, with
the network open, and so are the packages Daodan's own restore installs (`plan.py` over the project's folder, fetched as text on the host by
`apps.fetch`, never run: the same commands and restore lines the runner would give) and the Noir that `entry_points/noir.py` pins (sha256 checked). Nothing
of the applications is kept in the repository: the answers are (`results/real/`). Then, with the network blocked and in a copy of the project at
`/work`: Daodan's own rewrite of the `.env` files (`container.named`, which the runner applies before every command of a pre-map), then `noir scan
/work -f json --no-log` (what `noir.commands` gives), or the script of the source (the command of `fastapi_app.commands`). `-script-env` is the
script over the project's `.env` files as committed, to tell what the rewrite takes; `users-cli-` is the image of `users` with `fastapi-cli` added to
the restored environment, to tell what the loader's absence takes. `real_summary.py` reads the answers with the sources.
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
# image -> the application it holds, and what is added to the restored environment
IMAGES_OF = {"template": ("template", None), "users": ("users", None), "users-cli": ("users", "fastapi-cli")}


def _plan(folder: pathlib.Path) -> dict:
    return json.loads(subprocess.run([os.environ.get("DAODAN_PYTHON", "python"), str(HERE / "plan.py"), str(folder)], capture_output=True,
                                     text=True, check=True, encoding="utf-8", env={**os.environ, "DAODAN_CONTAINER": "off"}).stdout)


if LOCAL:
    sys.path.insert(0, str(REPO / "daodan/core"))
    import container  # noqa: E402  (Daodan's own: the rewrite of the `.env` files the runner applies)

    FOLDERS = {name: apps.fetch(name, pathlib.Path(os.environ.get("DAODAN_PROBE_TMP") or tempfile.gettempdir()) / "fastapi-apps") for name in apps.APPS}
    PLANS = {name: _plan(folder) for name, folder in FOLDERS.items()}
    NAMED = container.named()
else:
    PLANS, NAMED = None, ""


def _image(key: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
    name, extra = IMAGES_OF[key]
    repository, commit, _, folder, _ = apps.APPS[name]
    plan = PLANS[name]
    state, inputs = plan["state"], plan["inputs"]
    image = modal.Image.from_registry(plan["image"], add_python="3.12").run_commands(f"mkdir -p {inputs}")
    for url, sha, file in plan["files"]:
        if url:  # a download of the runner (`uv`), checked by its sha256 as the runner does
            image = image.run_commands(f"curl -fsSL {shlex.quote(url)} -o {inputs}/{file} && echo '{sha}  {inputs}/{file}' | sha256sum -c -")
        else:  # Daodan's own file, beside the premap modules
            image = image.add_local_file(REPO / "daodan/core/premap" / file, f"{inputs}/{file}", copy=True)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in plan["env"].items())
    setup = shlex.quote(plan["setup"]["argv"][2])
    image = image.run_commands(f"curl -fsSL -o /usr/local/bin/noir {apps.NOIR[0]} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - && chmod +x /usr/local/bin/noir")
    image = image.run_commands(f"mkdir -p /src /fix && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /src --strip-components=1"
                               f" && cp -a /src/{folder}/. /fix/ && rm -rf /src")
    # the runner's setup, run as the runner runs it (`sh -c`, its environment, the project's folder, which is `/work`); a failed restore does not fail the
    # build (the restore line ends in `true`): its standard error, exit code and seconds are kept
    image = image.run_commands(f"mkdir -p {state} {WORK} && cp -a /fix/. {WORK}/ && cd {WORK} && s=$(date +%s) && "
                               f"env -i {env} sh -c {setup} 2> {state}/setup.stderr; echo $? > {state}/setup.exit; "
                               f"echo $(( $(date +%s) - s )) > {state}/setup.seconds")
    if extra:
        python = f"{plan['venvs']}/./bin/python"
        image = image.run_commands(f"cd {WORK} && env -i {env} sh -c {shlex.quote(f'uv pip install -q --python {python} {extra}')} 2> {state}/extra.stderr; echo $? > {state}/extra.exit")
    return image


IMAGES = {key: _image(key) for key in IMAGES_OF}
app = modal.App("fastapi-real-applications")

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
    "print(repr({'python': sys.version, 'executable': sys.executable, 'fastapi': version('fastapi'), 'fastapi-cli': version('fastapi-cli'),\n"
    "            'starlette': version('starlette'), 'uvicorn': version('uvicorn'), 'pydantic': version('pydantic'), 'packages': len(list(m.distributions()))}))\n")


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
              "left_in_the_project": sorted(set(after) - set(before))[:40], "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f])}
    if name.endswith("environment"):
        answer["setup"] = {k: pathlib.Path(f"{state}/setup.{k}").read_text(encoding="utf-8").strip()[-1500:] for k in ("exit", "seconds", "stderr")}
    return answer


def _runner(key: str):
    def run(name: str, argv: list[str], env: dict[str, str], state: str, cwd: str, rewrite: str) -> dict:
        return _run(name, argv, env, state, cwd, rewrite)
    run.__name__ = run.__qualname__ = "run_" + key.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=IMAGES[key], timeout=1800, block_network=True)(run)
    return function


RUNNERS = {key: _runner(key) for key in IMAGES_OF}


def _variants() -> dict[str, tuple[str, list[str], str, str]]:
    """variant -> (image, argv, cwd, whether Daodan's `.env` rewrite runs first)."""
    out = {}
    for key, (name, _extra) in IMAGES_OF.items():
        plan = PLANS[name]
        python = f"{plan['venvs']}/./bin/python"
        [command, *_] = plan["commands"] or [None]
        out[f"{key}-environment"] = (key, [python, "-c", ENVIRONMENT], ".", "")
        if not IMAGES_OF[key][1]:  # the image with the loader added is the same project: Noir's answer is the same
            out[f"{key}-noir"] = (key, ["noir", "scan", WORK, "-f", "json", "--no-log"], ".", NAMED)
        if command:
            out[f"{key}-script"] = (key, command["argv"], command["cwd"], NAMED)
            if key == "template":  # the one project with a committed `.env`, which the runner's rewrite replaces
                out[f"{key}-script-env"] = (key, command["argv"], command["cwd"], "")
                # the same, and the directory its `app.frontend(...)` asks for at import (the build of its front end, which no restore makes): what
                # the framework gives once the two things that stop it are out of the way
                out[f"{key}-script-stub"] = (key, command["argv"], command["cwd"], "mkdir -p backend/app/frontend")
            if key == "users-cli":  # the CLI is there, and the project declares where its application is (it starts by `uvicorn.run("app.app:app")`)
                out[f"{key}-script-declared"] = (key, command["argv"], command["cwd"], "printf '[tool.fastapi]\nentrypoint = \"app.app:app\"\n' > pyproject.toml")
    return out


@app.local_entrypoint()
def main(only: str = ""):
    OUT.mkdir(parents=True, exist_ok=True)
    variants = _variants()
    chosen = set(only.split(",")) if only else set(variants)
    for key, runner in RUNNERS.items():
        calls = []
        for name, (image, argv, cwd, rewrite) in variants.items():
            if image == key and name in chosen:
                plan = PLANS[IMAGES_OF[key][0]]
                calls.append((name, argv, plan["env"], plan["state"], cwd, rewrite))
        for answer in (runner.starmap(calls) if calls else ()):
            (OUT / f"{answer['variant']}.json").write_text(json.dumps(answer, indent=1), encoding="utf-8", newline="\n")
            print(answer["variant"], answer["returncode"], answer["seconds"], answer["max_rss_mb"], len(answer["stdout"]))
