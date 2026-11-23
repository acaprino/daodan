"""`react-router routes --json` and `remix routes --json` on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py --mode lock
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py

`--mode lock` writes each fixture's `package-lock.json` (the one moment it is made: `npm install --package-lock-only
--ignore-scripts`, run with the network open in a Modal function, never on this PC). `--mode probes` (the default) builds one
image with every fixture's packages restored from its lockfile (`npm ci`, while the image is built: the one moment the
network is open), then runs each command of `COMMANDS`, and of the variants of a copy of a fixture, with the network blocked;
every answer (`argv`, `returncode`, `stdout`, `stderr`, seconds, and the files the command left in the project) goes to
`results/<variant>.json`. The project's code (`routes.ts`, `react-router.config.ts`, `remix.config.js`, `vite.config.ts`,
`node_modules`) runs only in the container.

`--mode source` runs what `daodan/core/premap/react_router.py` runs in Daodan's container: the commands it gives for each fixture
(a function with the network open, where Daodan's grammar bundle comes from), then each command, with the argv and the
environment the source wrote, in a copy of the project with its packages, in a copy of it with a change that matters to the
source, and in a copy without the packages (the project declares the package and the restore did not install it), with the
network blocked. The answers, as the container runner returns them (`returncode`, `stdout`, `stderr`), are written to
`tests/fixtures/premap/react-router/answers.json`, which `tests/test_codebase_map_premap_react_router.py` reads.
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
NAMES = ("framework", "flat", "remix", "remix-vite")

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
app = modal.App("react-router-routes", image=image)
RECORDED = REPO / "tests/fixtures/premap/react-router/answers.json"


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


def _run(argv: list[str], cwd: str, env: dict | None = None) -> dict:
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
            "left_in_the_project": sorted(_listing(cwd) - before)}


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _app_dir_src(root: pathlib.Path) -> None:
    (root / "app").rename(root / "src")
    _write(root / "react-router.config.ts", 'import type { Config } from "@react-router/dev/config";\n\n'
                                            'export default { appDirectory: "src", ssr: true } satisfies Config;\n')


def _two_apps(root: pathlib.Path) -> None:
    """A folder with two routes.ts files is not a case: the config names the one that counts."""
    _write(root / "react-router.config.ts", 'import type { Config } from "@react-router/dev/config";\n\n'
                                            'export default { appDirectory: "src/web", ssr: false } satisfies Config;\n')
    (root / "app").rename(root / "src_web_tmp")
    (root / "src").mkdir()
    (root / "src_web_tmp").rename(root / "src" / "web")


ROUTES_HEAD = 'import { type RouteConfig, route } from "@react-router/dev/routes";\n\n'
ABSOLUTE = ROUTES_HEAD + """export default [
  route("users", "routes/users/user.tsx", [
    route("/users/:id", "routes/users/edit.tsx", [route("details", "routes/nested/child.tsx")]),
    route("/users/new", "routes/hello.tsx"),
  ]),
  route("/about", "routes/about.tsx"),
] satisfies RouteConfig;
"""
ELSEWHERE = ROUTES_HEAD + """export default [
  route("other", "routes/docs.tsx", [route("/elsewhere", "routes/legacy.jsx")]),
] satisfies RouteConfig;
"""
HANG_BODY = ('await new Promise((resolve) => setTimeout(resolve, 3_600_000)); // a config that waits for something that never comes\n'
             'export default [route("a", "routes/about.tsx")] satisfies RouteConfig;\n')
HANG = ROUTES_HEAD + HANG_BODY
HANG_IGNORING_TERM = (ROUTES_HEAD + 'import { writeFileSync } from "node:fs";\n'
                      'writeFileSync("started.txt", String(process.pid));  // the process that loads the config\n'
                      'process.on("SIGTERM", () => { writeFileSync("term-seen.txt", String(process.pid)); });  // and does not leave when asked\n'
                      + HANG_BODY)
LEFT_RUNNING = ["ps", "-eo", "pid,ppid,args"]  # every process still alive after the command: the container holds nothing else of the project
TIMEOUT = ["timeout", "--kill-after=2", "{seconds}"]  # as `premap/react_router.py` runs it, with short times

COMMANDS = {  # variant -> (fixture, edit, [(argv, env)]): what runs, in its copy of the fixture
    "absolute-child": ("framework", lambda r: _write(r / "app/routes.ts", ABSOLUTE), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
        (["npx", "--no-install", "react-router", "routes"], None),
    ]),
    "rule-source": ("framework", None, [  # the rule for an absolute child, as the installed package's own source states it (text read, nothing run)
        (["sh", "-c", "grep -rhn -B8 -A5 'must start with the combined path' node_modules/react-router/dist/development --include=*.js | head -40"], None),
    ]),
    "basename": ("framework", lambda r: _write(r / "react-router.config.ts", 'import type { Config } from "@react-router/dev/config";\n\n'
                                                                              'export default { ssr: true, basename: "/base/" } satisfies Config;\n'), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "absolute-child-elsewhere": ("framework", lambda r: _write(r / "app/routes.ts", ELSEWHERE), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "hang": ("framework", lambda r: _write(r / "app/routes.ts", HANG), [
        ([*TIMEOUT[:2], "5", "npx", "--no-install", "react-router", "routes", "--json"], None),
        (LEFT_RUNNING, None),
    ]),
    "hang-ignores-term": ("framework", lambda r: _write(r / "app/routes.ts", HANG_IGNORING_TERM), [
        ([*TIMEOUT[:2], "3", "npx", "--no-install", "react-router", "routes", "--json"], None),
        (LEFT_RUNNING, None),
    ]),
    "framework": ("framework", None, [
        (["npx", "--no-install", "react-router", "--help"], None),
        (["npx", "--no-install", "react-router", "routes", "--help"], None),
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
        (["npx", "--no-install", "react-router", "routes"], None),
        (["npx", "--no-install", "react-router", "routes", "--json", "--mode", "production"], None),
    ]),
    "framework-root-argument": ("framework", None, [
        (["npx", "--no-install", "react-router", "routes", "--json", "/work/framework-root-argument"], None),
    ]),
    "app-directory-src": ("framework", _app_dir_src, [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "app-directory-nested": ("framework", _two_apps, [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "file-missing": ("framework", lambda r: (r / "app/routes/about.tsx").unlink(), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "routes-ts-broken": ("framework", lambda r: _write(r / "app/routes.ts", 'import { route } from "@react-router/dev/routes";\nexport default [route("a", "routes/a.tsx"\n'), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "routes-ts-throws": ("framework", lambda r: _write(r / "app/routes.ts", 'throw new Error("routes.ts needs a database");\n'), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "routes-ts-absent": ("framework", lambda r: (r / "app/routes.ts").unlink(), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "no-vite-config": ("framework", lambda r: (r / "vite.config.ts").unlink(), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "no-react-router-config": ("framework", lambda r: (r / "react-router.config.ts").unlink(), [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "not-installed": ("framework", None, [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
    ]),
    "npx-no": ("framework", None, [  # `--no-install` is the old spelling: `--no` is npm's own
        (["npx", "--no", "react-router", "routes", "--json"], None),
    ]),
    "not-installed-npx-no": ("framework", None, [
        (["npx", "--no", "react-router", "routes", "--json"], None),
    ]),
    "offline-installed": ("framework", None, [  # npm's own switch: no request to a registry, whatever the command
        (["npx", "--no-install", "react-router", "routes", "--json"], {"npm_config_offline": "true"}),
    ]),
    "not-installed-offline": ("framework", None, [
        (["npx", "--no-install", "react-router", "routes", "--json"], {"npm_config_offline": "true"}),
    ]),
    "typegen": ("framework", None, [  # does the other official command name the app directory? it writes files, and says where
        (["npx", "--no-install", "react-router", "typegen"], None),
    ]),
    "typegen-app-directory-src": ("framework", _app_dir_src, [
        (["npx", "--no-install", "react-router", "typegen"], None),
    ]),
    "flat": ("flat", None, [
        (["npx", "--no-install", "react-router", "routes", "--json"], None),
        (["npx", "--no-install", "react-router", "routes"], None),
    ]),
    "remix": ("remix", None, [
        (["npx", "--no-install", "remix", "--help"], None),
        (["npx", "--no-install", "remix", "routes", "--help"], None),
        (["npx", "--no-install", "remix", "routes", "--json"], None),
        (["npx", "--no-install", "remix", "routes"], None),
    ]),
    "remix-not-installed": ("remix", None, [
        (["npx", "--no-install", "remix", "routes", "--json"], None),
    ]),
    "remix-vite": ("remix-vite", None, [
        (["npx", "--no-install", "remix", "routes", "--json"], None),
        (["npx", "--no-install", "remix", "routes"], None),
    ]),
}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(variants: list[str]) -> dict:
    import subprocess

    out = {"_env": {"node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                    "npm": subprocess.run(["npm", "--version"], capture_output=True, text=True).stdout.strip(),
                    "packages": {name: {package: json.load(open(f"/fix/{name}/node_modules/{package}/package.json"))["version"]
                                        for package in ("react-router", "@react-router/dev", "@react-router/fs-routes", "@remix-run/dev", "vite")
                                        if os.path.isfile(f"/fix/{name}/node_modules/{package}/package.json")}
                                 for name in NAMES if os.path.isdir(f"/fix/{name}/node_modules")}}}
    for variant in variants:
        fixture, edit, commands = COMMANDS[variant]
        project = _variant(variant, fixture, edit, node_modules=not variant.endswith(("not-installed", "not-installed-npx-no", "not-installed-offline")))
        out[variant] = [_run(argv, project, env) for argv, env in commands]
    return out


SOURCE_VARIANTS = {  # the key in answers.json -> (fixture, a change to its copy, whether its packages are left out, the time limit it is run with)
    "framework": ("framework", None, False, None),
    "flat": ("flat", None, False, None),
    "remix": ("remix", None, False, None),
    "remix-vite": ("remix-vite", None, False, None),
    "app-directory-src": ("framework", _app_dir_src, False, None),
    "file-missing": ("framework", lambda r: (r / "app/routes/about.tsx").unlink(), False, None),
    "routes-ts-throws": ("framework", lambda r: _write(r / "app/routes.ts", 'throw new Error("routes.ts needs a database");\n'), False, None),
    "routes-ts-broken": ("framework", lambda r: _write(r / "app/routes.ts", 'import { route } from "@react-router/dev/routes";\nexport default [route("a", "routes/a.tsx"\n'), False, None),
    "routes-ts-absent": ("framework", lambda r: (r / "app/routes.ts").unlink(), False, None),
    "not-installed": ("framework", None, True, None),
    "absolute-child": ("framework", lambda r: _write(r / "app/routes.ts", ABSOLUTE), False, None),
    "absolute-child-elsewhere": ("framework", lambda r: _write(r / "app/routes.ts", ELSEWHERE), False, None),
    "hang": ("framework", lambda r: _write(r / "app/routes.ts", HANG), False, (2, 3)),  # (kill-after, seconds): the source's 10 and 300 would take 5 minutes
    "hang-ignores-term": ("framework", lambda r: _write(r / "app/routes.ts", HANG_IGNORING_TERM), False, (2, 3)),
}


@app.function(timeout=900)
def commands() -> dict:
    """What the source asks the container to run for each fixture."""
    import sys
    from pathlib import Path

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot

    out = {}
    for name in NAMES:
        project, manifest = Path(f"/work/commands-{name}"), Path(f"/work/commands-out-{name}/manifest.sqlite")
        import shutil
        shutil.copytree(f"/lockwork/{name}", project)
        snapshot.write_snapshot(project, manifest)
        with open_snapshot(manifest) as store:
            out[name] = premap.react_router.commands(premap.Context(manifest, store))
    return out


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def source(asked: dict) -> dict:
    """Each variant's command, as the source wrote it, with the network blocked."""
    out = {}
    for key, (fixture, edit, bare, limits) in SOURCE_VARIANTS.items():
        [command] = asked[fixture]
        argv = list(command["argv"])
        if limits:  # `timeout --kill-after=10 300 npx ...`: shortened, the source's own argv otherwise
            assert argv[:2] == ["timeout", "--kill-after=10"], argv
            argv[1:3] = [f"--kill-after={limits[0]}", str(limits[1])]
        project = _variant(f"source-{key}", fixture, edit, node_modules=not bare)
        answer = _run(argv, project, command["env"])
        out[key] = {name: answer[name] for name in ("returncode", "stdout", "stderr")}
        out[key + "_seconds"] = answer["seconds"]
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
        asked = commands.remote()
        print("commands:", json.dumps({name: [(c["cwd"], c["argv"], c["env"]) for c in items or []] for name, items in asked.items()}))
        answers = source.remote(asked)
        RECORDED.parent.mkdir(parents=True, exist_ok=True)
        RECORDED.write_bytes((json.dumps({key: value for key, value in answers.items() if not key.endswith("_seconds")},
                                         indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        for key in SOURCE_VARIANTS:
            print(f"=== {key}: exit {answers[key]['returncode']} in {answers[key + '_seconds']} s, {len(answers[key]['stdout'])} bytes out")
            print(answers[key]["stderr"].strip()[:300])
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
            print(f"$ {' '.join(answer['argv'])}  -> exit {answer['returncode']} in {answer['seconds']} s, left {answer['left_in_the_project']}")
            print((answer["stdout"] or "")[:1500])
            if answer["stderr"].strip():
                print("--- stderr:", answer["stderr"].strip()[:600])
