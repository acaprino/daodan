"""`svelte-kit sync` on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/sveltekit-routes/modal_probe.py --mode lock
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/sveltekit-routes/modal_probe.py

`--mode lock` writes the fixture's `package-lock.json` (the one moment it is made: `npm install --package-lock-only
--ignore-scripts`, run with the network open in a Modal function, never on this PC). `--mode probes` (the default) builds one
image with the fixture's packages restored from its lockfile (`npm ci`, while the image is built: the one moment the network is
open), then runs each command of `COMMANDS`, and of the variants of a copy of the fixture, with the network blocked; every
answer (`argv`, `returncode`, `stdout`, `stderr`, seconds, the files the command left in the project, and the text of what it
generated) goes to `results/<variant>.json`. The project's code (`svelte.config.js`, `vite.config.ts`, `node_modules`) runs only
in the container.
"""
import json
import os
import pathlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
FIXTURES = HERE / "fixture"
OUT = HERE / "results"
NAMES = ("routes", "kit-2.0.0", "kit-2.15.0", "kit-2.40.0")  # the fixture, and three older SvelteKit (their packages only)
OLD = NAMES[1:]
GENERATED = (".svelte-kit", ".kit-out")  # the folders the generated files are dumped from
SKIPPED = ("ambient.d.ts", "env.d.ts")  # they list the names of the process's environment variables: not dumped
PACKAGES = ("@sveltejs/kit", "svelte", "vite", "@sveltejs/vite-plugin-svelte", "@sveltejs/adapter-auto", "typescript")

image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    image = image.pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
    image = image.add_local_dir(FIXTURES, "/lockwork", copy=True, ignore=["**/package-lock.json", "**/node_modules/**"])
    locked = [name for name in NAMES if (FIXTURES / name / "package-lock.json").is_file()]
    for name in locked:
        image = (image.add_local_file(FIXTURES / name / "package.json", f"/fix/{name}/package.json", copy=True)
                 .add_local_file(FIXTURES / name / "package-lock.json", f"/fix/{name}/package-lock.json", copy=True))
    if locked:  # The network is open only while the image is built: restore each fixture from its lockfile here.
        image = image.run_commands(*(f"cd /fix/{name} && npm ci --no-audit --no-fund 2>&1 | tail -5" for name in locked))
    for name in locked:  # the files of the project, added last: a change to them rebuilds nothing before
        image = image.add_local_dir(FIXTURES / name, f"/fix/{name}", ignore=["**/package-lock.json", "**/package.json", "**/node_modules/**"])
    image = (image.add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/data"))
app = modal.App("sveltekit-routes", image=image)
RECORDED = REPO / "tests/fixtures/premap/sveltekit/answers.json"


@app.function(timeout=900)
def lock(name: str) -> dict:
    """The fixture's lockfile, made from its package.json with the network open and no script run."""
    import shutil
    import subprocess

    work = f"/work/{name}"
    shutil.copytree(f"/lockwork/{name}", work)
    r = subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=work,
                       capture_output=True, text=True, timeout=800)
    lockfile = pathlib.Path(work, "package-lock.json")
    return {"returncode": r.returncode, "stderr": r.stderr[-2000:], "stdout": r.stdout[-500:],
            "lock": lockfile.read_text(encoding="utf-8") if lockfile.is_file() else None}


def _variant(name: str, base: str, edit=None, node_modules: bool = True) -> str:
    """A copy of a fixture under /work, `edit(path)` applied to it."""
    import shutil

    target = f"/work/{name}"
    shutil.copytree(f"/fix/{base}", target, symlinks=True,
                    ignore=None if node_modules else shutil.ignore_patterns("node_modules"))
    if edit:
        edit(pathlib.Path(target))
    return target


def _listing(root: str) -> set[str]:
    out = set()
    for directory, names, files in os.walk(root):
        names[:] = [n for n in names if n != "node_modules"]
        out.update(os.path.relpath(os.path.join(directory, f), root).replace("\\", "/") for f in files)
    return out


def _generated(root: str) -> dict:
    """The text of the files the tool generated, by path: what a reader of the project's output would be given. Not the
    environment's names (`SKIPPED`), the copies of the project's own files (`proxy+...`) and what the server and the root
    component are made of."""
    out = {}
    for folder in GENERATED:
        for directory, _names, files in os.walk(os.path.join(root, folder)):
            if any(part in directory.split(os.sep) for part in ("server", "shared")):
                continue
            for file in files:
                if file in SKIPPED or file.startswith(("proxy+", "root.")):
                    continue
                path = os.path.join(directory, file)
                try:
                    text = pathlib.Path(path).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                out[os.path.relpath(path, root).replace("\\", "/")] = text if len(text) <= 60000 else text[:60000] + "[cut]"
    return out


def _run(argv: list[str], cwd: str, env: dict | None = None, dump: bool = False) -> dict:
    import subprocess
    import time

    before = _listing(cwd)
    started = time.monotonic()
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=600,
                           env={**os.environ, "NO_COLOR": "1", "CI": "1", **(env or {})})
        answer = {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired:
        answer = {"returncode": "timeout", "stdout": "", "stderr": ""}
    return {"argv": argv, "cwd": cwd.removeprefix("/work/"), **answer, "seconds": round(time.monotonic() - started, 2),
            "left_in_the_project": sorted(_listing(cwd) - before), **({"generated": _generated(cwd)} if dump else {})}


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _config(options: str):
    """A `svelte.config.js` whose `kit` has `options` more."""
    return lambda root: _write(root / "svelte.config.js",
                               "import adapter from '@sveltejs/adapter-auto';\n"
                               f"export default {{ kit: {{ adapter: adapter(), {options} }} }};\n")


def _routes_in_pages(root: pathlib.Path) -> None:
    (root / "src/routes").rename(root / "src/pages")
    _config("files: { routes: 'src/pages' }")(root)


def _remove(*paths: str):
    def edit(root: pathlib.Path) -> None:
        import shutil
        for path in paths:
            shutil.rmtree(root / path) if (root / path).is_dir() else (root / path).unlink()
    return edit


def _stale(root: pathlib.Path) -> None:
    """Sync once, then take two routes away: does the next sync remove what it wrote for them?"""
    import subprocess
    subprocess.run(["npx", "--no-install", "svelte-kit", "sync"], cwd=root, capture_output=True, env={**os.environ, "npm_config_offline": "true"})
    _remove("src/routes/about", "src/routes/api/health")(root)


def _old(name: str):
    """The fixture's files with the packages of an older SvelteKit (`OLD`): its `package.json` and `node_modules`."""
    def edit(root: pathlib.Path) -> None:
        import shutil
        shutil.copy(f"/fix/{name}/package.json", root / "package.json")
        shutil.copytree(f"/fix/{name}/node_modules", root / "node_modules", symlinks=True)
    return edit


def _failed_after_a_good_sync(root: pathlib.Path) -> None:
    """A good sync, then a config that throws: the folder holds what the good one wrote, and the next sync fails."""
    import subprocess
    subprocess.run(SYNC, cwd=root, capture_output=True, env={**os.environ, **OFFLINE})
    _write(root / "svelte.config.js", "throw new Error('svelte.config.js needs a secret');\n")


OFFLINE = {"npm_config_offline": "true"}
LIMITED = "0.5"
SYNC = ["npx", "--no-install", "svelte-kit", "sync"]

EDITS = {  # variant -> the change to its copy of the fixture (and whether its packages are left out)
    "stale": (_stale, False),
    "routes-in-pages": (_routes_in_pages, False),
    "out-dir": (_config("outDir: '.kit-out'"), False),
    "no-routes": (_remove("src/routes"), False),
    "config-throws": (lambda r: _write(r / "svelte.config.js", "throw new Error('svelte.config.js needs a secret');\n"), False),
    "config-broken": (lambda r: _write(r / "svelte.config.js", "export default { kit: {\n"), False),
    "route-conflict": (lambda r: (_write(r / "src/routes/(a)/x/+page.svelte", "<h1>a</h1>\n"),
                                  _write(r / "src/routes/(b)/x/+page.svelte", "<h1>b</h1>\n")), False),
    "bad-matcher": (lambda r: _write(r / "src/routes/nomatch/[id=nomatcher]/+page.svelte", "<h1>x</h1>\n"), False),
    "server-syntax-error": (lambda r: _write(r / "src/routes/blog/+page.server.ts", "export const load = async () => ({ posts: [\n"), False),
    "failed-after-a-good-sync": (_failed_after_a_good_sync, False),
    "not-installed": (None, True),
    **{f"old-{name}": (_old(name), True) for name in OLD},
}

COMMANDS = {  # variant -> [(argv, env, dump)]: what runs, in its copy of the fixture
    "sync": [
        (["npx", "--no-install", "svelte-kit", "--help"], OFFLINE, False),
        (["npx", "--no-install", "svelte-kit", "sync", "--help"], OFFLINE, False),
        (SYNC, OFFLINE, True),
        (SYNC, OFFLINE, True),  # again: does it rewrite what is there, and say anything
    ],
    "kit-source": [  # the tool's own source, read: where `route_meta_data.json` is written and what it holds
        (["sh", "-c", "grep -n 'meta_data' node_modules/@sveltejs/kit/src/core/sync/write_types/index.js | head -60"], None, False),
        (["sh", "-c", "sed -n 62,134p node_modules/@sveltejs/kit/src/core/sync/write_types/index.js"], None, False),
    ],
    "not-installed-offline": [(SYNC, OFFLINE, False)],
    **{variant: [(SYNC, None if variant == "not-installed" else OFFLINE, variant not in ("config-throws", "config-broken", "not-installed"))]
       for variant in EDITS},
}
FIXTURE = {"not-installed-offline": ("routes", None, True), "sync": ("routes", None, False), "kit-source": ("routes", None, False)}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(variants: list[str]) -> dict:
    import subprocess

    out = {"_env": {"node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                    "npm": subprocess.run(["npm", "--version"], capture_output=True, text=True).stdout.strip(),
                    "packages": {name: {package: json.load(open(f"/fix/{name}/node_modules/{package}/package.json"))["version"]
                                        for package in PACKAGES
                                        if os.path.isfile(f"/fix/{name}/node_modules/{package}/package.json")}
                                 for name in NAMES if os.path.isdir(f"/fix/{name}/node_modules")}}}
    for variant in variants:
        edit, bare = EDITS.get(variant) or (None, FIXTURE[variant][2])
        project = _variant(variant, "routes", edit, node_modules=not bare)
        out[variant] = [_run(argv, project, env, dump) for argv, env, dump in COMMANDS[variant]]
    return out


@app.function(timeout=900)
def commands() -> dict:
    """What the source asks the container to run in the fixture."""
    import shutil
    import sys
    from pathlib import Path

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot

    project, manifest = Path("/work/commands"), Path("/work/commands-out/manifest.sqlite")
    shutil.copytree("/lockwork/routes", project)
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store:
        return {"routes": premap.sveltekit.commands(premap.Context(manifest, store))}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def source(asked: list) -> dict:
    """The source's two commands for each variant, as it wrote them, with the network blocked; `LIMITED`'s with half a second where
    the source gave the sync 900 (the measured sync takes 1.0 s at the least), so `timeout` ends it."""
    out = {}
    for key, (edit, bare) in {"routes": (None, False), **EDITS, "timed-out": (None, False)}.items():
        project = _variant(f"source-{key}", "routes", edit, node_modules=not bare)
        answers = [_run([*command["argv"][:2], LIMITED, *command["argv"][3:]] if key == "timed-out" and command["argv"][0] == "timeout"
                        else command["argv"], project, command["env"]) for command in asked]
        out[key] = [{name: answer[name] for name in ("returncode", "stdout", "stderr")} for answer in answers]
        out[key + "_seconds"] = [answer["seconds"] for answer in answers]
    return out


@app.local_entrypoint()
def main(mode: str = "probes"):
    if mode == "lock":
        for name in NAMES:
            answer = lock.remote(name)
            print(name, "exit", answer["returncode"], answer["stderr"][-300:])
            if answer["lock"]:
                (FIXTURES / name / "package-lock.json").write_bytes(answer["lock"].replace("\r\n", "\n").encode("utf-8"))
        return
    if mode == "source":
        [asked] = commands.remote().values()
        print("commands:", json.dumps([(c["cwd"], c["argv"], c["env"], c["network"]) for c in asked]))
        answers = source.remote(asked)
        RECORDED.parent.mkdir(parents=True, exist_ok=True)
        RECORDED.write_bytes((json.dumps({key: value for key, value in answers.items() if not key.endswith("_seconds")},
                                         indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        for key in ("routes", *EDITS, "timed-out"):
            print(f"=== {key}: exits {[a['returncode'] for a in answers[key]]} in {answers[key + '_seconds']} s, {len(answers[key][1]['stdout'])} bytes of JSON")
            print((answers[key][0]["stderr"] or answers[key][1]["stderr"]).strip()[:300])
        return
    wanted = os.environ.get("VARIANTS") or ",".join(COMMANDS)
    OUT.mkdir(exist_ok=True)
    for name, answers in probe.remote(wanted.split(",")).items():
        (OUT / f"{'00_env' if name == '_env' else name}.json").write_bytes(
            (json.dumps(answers, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        print(f"=== {name}")
        if name == "_env":
            print(json.dumps(answers, indent=1))
            continue
        for answer in answers:
            print(f"$ {' '.join(answer['argv'])}  -> exit {answer['returncode']} in {answer['seconds']} s, left {len(answer['left_in_the_project'])} files")
            print((answer["stdout"] or "")[:800])
            if answer["stderr"].strip():
                print("--- stderr:", answer["stderr"].strip()[:600])
