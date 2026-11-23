"""Flask's own loader and `url_map` on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/flask-routes/modal_probe.py

WRITTEN WITHOUT RUNNING IT (no Modal credentials where it was written). The image is built with the network open, the one
moment it is: the fixture's packages are installed into an environment as Daodan's preparation does for a folder with no
lockfile (`uv venv` and `uv pip install -r requirements.txt`, `preparation.RESTORES["pip"]`). Each variant of `VARIANTS` then runs
in a copy of the project, with the network blocked and the environment of Daodan's runner, and its answer (`argv`, `returncode`,
`stdout`, `stderr`, seconds, peak memory, the files it left in the project) goes to `results/<variant>.json`. The project's code
runs only in the container. The run ends by writing `tests/fixtures/premap/flask/answers.json` (`{"routes": <the default
variant's answer>}`), the file `tests/test_codebase_map_premap_flask.py` waits for.
"""
import json
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()
REPO = HERE.parents[1] if LOCAL else HERE
FIXTURE = HERE / "fixture"
OUT = HERE / "results"
RECORDED = REPO / "tests/fixtures/premap/flask/answers.json"
SCRIPT = "/daodan/core/premap/flask_routes.py"
VENV = "/state/venvs/."  # the path `preparation.VENVS` + "/" + the folder gives for the root folder

image = modal.Image.debian_slim(python_version="3.12").pip_install("uv==0.11.28")
if LOCAL:
    image = (image.add_local_dir(FIXTURE, "/fix", copy=True, ignore=["**/__pycache__/**", "**/.venv/**"])
             .run_commands("printf 'flask==3.1.3\\n' > /fix/requirements.txt",
                           f"uv venv -q --python python3 {VENV} && uv pip install -q --python {VENV} -r /fix/requirements.txt")
             .add_local_dir(REPO / "daodan/core/premap", "/daodan/core/premap", ignore=["**/__pycache__/**", "**/*.go", "**/*.mjs"]))
app = modal.App("flask-routes", image=image)

RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")
HOME = "/work/home"
# variant -> (argv after the interpreter, environment, how the copy is edited)
VARIANTS = {
    "routes": ([VENV + "/bin/python", "-I", SCRIPT], {}, None),
    "routes-timeout": (["timeout", "--kill-after=10", "900", VENV + "/bin/python", "-I", SCRIPT], {}, None),
    "flask-routes-command": ([VENV + "/bin/flask", "routes"], {}, None),
    "flask-routes-all-methods": ([VENV + "/bin/flask", "routes", "--all-methods"], {}, None),
    "no-wsgi": ([VENV + "/bin/python", "-I", SCRIPT], {}, lambda p: (p / "wsgi.py").rename(p / "other.py")),
    "flask-app-variable": ([VENV + "/bin/python", "-I", SCRIPT], {"FLASK_APP": "other:app"}, lambda p: (p / "wsgi.py").rename(p / "other.py")),
    "module-raises": ([VENV + "/bin/python", "-I", SCRIPT], {}, lambda p: (p / "wsgi.py").write_text("raise RuntimeError('boom')\n")),
    "missing-package": ([VENV + "/bin/python", "-I", SCRIPT], {}, lambda p: (p / "wsgi.py").write_text("import not_installed\n")),
    "app-py": ([VENV + "/bin/python", "-I", SCRIPT], {}, lambda p: (p / "wsgi.py").rename(p / "app.py")),
}


def _listing(root: str) -> dict[str, int]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
    return out


@app.function(timeout=900, block_network=True)
def run(name: str) -> dict:
    import shutil
    import subprocess
    import sys
    import time

    argv, env, edit = VARIANTS[name]
    work = pathlib.Path(f"/work/{name}")
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/fix", work)
    if edit:
        edit(work)
    os.makedirs(HOME, exist_ok=True)
    before = _listing(str(work))
    mark = f"/tmp/rss-{name}"
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=work, capture_output=True, text=True, timeout=600,
                       stdin=subprocess.DEVNULL, env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": HOME, **env})
    after = _listing(str(work))
    return {"variant": name, "argv": argv, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
            "seconds": round(time.monotonic() - started, 2),
            "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
            "left_in_the_project": sorted(set(after) - set(before)), "changed_in_the_project": sorted(
                f for f in set(after) & set(before) if after[f] != before[f])}


@app.local_entrypoint()
def main():
    OUT.mkdir(exist_ok=True)
    answers = {}
    for answer in run.map(list(VARIANTS)):
        answers[answer["variant"]] = answer
        (OUT / f"{answer['variant']}.json").write_text(json.dumps(answer, indent=1), encoding="utf-8")
    first = answers["routes"]
    RECORDED.parent.mkdir(parents=True, exist_ok=True)
    RECORDED.write_text(json.dumps({"routes": {k: first[k] for k in ("returncode", "stdout", "stderr")}}, indent=1), encoding="utf-8")
    print(json.dumps({v: [a["returncode"], a["seconds"], a["max_rss_mb"]] for v, a in answers.items()}, indent=1))
