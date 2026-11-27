"""`inspectRoutes` of `hono/dev` against the pinned Noir, on Modal: the measure of the README's decision rule (`T1.C.1`).

    modal run benchmarks/hono-routes/modal_probe.py --mode lock          the fixture's package-lock.json (network open, no script)
    modal run benchmarks/hono-routes/modal_probe.py                      every application of `apps.APPS`
    modal run benchmarks/hono-routes/modal_probe.py --only fixture       some of them

(behind the session's proxy, with `modal[api-proxy-support]`; `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.)

Two images per application, as Daodan runs Noir and a framework's command in two container runs. The *run* image is Daodan's container
(`container_runner.IMAGE`) with the checkout at `/work` (`container.WORKDIR`) and its Node packages restored there by Daodan's own lines
(`container_runner._node` and `container_runner.plan("next", ...)`, run by `_restore` while the image is built, the network open); then, with the
network blocked and the runner's environment (`preparation.ENV`), Node scripts written here read what the project declares (`DECLARED`: `main`
and `exports` of each `package.json` that depends on `hono`, resolved by Node; the `main` of a Wrangler configuration, read by the project's own
Wrangler) and load each candidate module and print `inspectRoutes` of every export that is a Hono app (`INSPECT`), with seconds and peak memory.
The *read* image has the clean checkout at `/work`, Daodan's code and the pinned Noir: Daodan's snapshot, `noir scan` as `noir.commands` gives it,
`noir.read` and `binder.bind`. `compare` (no project code) joins the two with `summarize.py`. The project's code runs only in the run image.
Answers come back in chunks (`_chunks`): a function with the network blocked cannot return more than about 8 KB at once.
"""
import concurrent.futures
import json
import os
import pathlib
import shlex
import sys
import zlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
NAMES = ("real-stack-documenso", "ramen-api", "hono-open-api-starter", "fixture")
if LOCAL:
    sys.path.insert(0, str(HERE))
    import apps  # noqa: E402
    assert tuple(apps.APPS) == NAMES
    sys.path.insert(0, str(REPO / "daodan/core"))
    import container_runner  # noqa: E402  (only its IMAGE: nothing of the project is read here)
DEPS = ("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
IGNORE = ["**/__pycache__/**", "**/*.pyc"]
MEASURE = "/daodan/measure"
CHUNK = 6000


def _code(image: modal.Image, name: str) -> modal.Image:
    return (image.pip_install(*DEPS)
            .env({"DAODAN_SHARED_DIR": "/daodan-shared", "PYTHONDONTWRITEBYTECODE": "1", "HONO_APP": name})
            .add_local_dir(REPO / "daodan/core", "/daodan/core", copy=True, ignore=IGNORE)
            .add_local_dir(REPO / "daodan/data", "/daodan/data", copy=True))


def _checkout(image: modal.Image, name: str) -> modal.Image:
    repository, commit = apps.APPS[name][:2]
    if repository is None:
        return image.add_local_dir(HERE / "fixture", "/work", copy=True, ignore=["**/node_modules/**"])
    return image.run_commands(f"mkdir -p /work && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /work --strip-components=1")


def _restore():
    """While the run image is built, the network open: Daodan's restore of the project's Node packages in `/work`, as the runner gives it to
    `next` (the setup line with the restore lines), its files checked by sha256; what it printed goes to `restore.json` beside the state."""
    import hashlib
    import subprocess
    import time
    import urllib.request

    sys.path[:0] = ["/daodan/core"]
    import container_runner as runner
    import preparation

    project = pathlib.Path("/work")
    restored = runner._node(project)
    first, files, hosts, gaps = runner.plan("next", [], [], restored["lines"])
    os.makedirs(preparation.IN, exist_ok=True)
    for url, sha, file in files:
        data = urllib.request.urlopen(url, timeout=600).read()
        assert hashlib.sha256(data).hexdigest() == sha, file
        pathlib.Path(preparation.IN, file).write_bytes(data)
    started = time.monotonic()
    r = subprocess.run(first["argv"], cwd=project, env=first["env"], capture_output=True, text=True, timeout=3300)
    record = {"restores": restored["restores"], "gaps": [*restored["gaps"], *gaps], "hosts": list(hosts), "argv": first["argv"],
              "returncode": r.returncode, "seconds": round(time.monotonic() - started, 1), "stdout": r.stdout[-2000:], "stderr": r.stderr[-8000:]}
    pathlib.Path(preparation.STATE, "restore.json").write_text(json.dumps(record), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("restores", "returncode", "seconds")}), record["stderr"][-1500:])


# Beyond Daodan's own restore and loaders, what each application needs to reach `inspectRoutes` at all (none of it is a declared datum: the
# measure of criteria 2 and 3 when criterion 1 or the load fails): app -> [(module, loader, env file whose values are added, label)]. `tsx` is the
# project's, `probe-tsx` is `PROBE_TSX` installed by the probe outside the project; Documenso's run in an image where, after the restore, the
# project's `prisma:generate` (its `post-install` is not an npm lifecycle script, so the restore does not run it), `translate` and the server's own
# build (`build:server`, rollup over `server/router.ts`) ran (`GENERATE`): the source, then the module the build writes.
PROBE_TSX = ("tsx@4.20.6", "/opt/probe-tsx/node_modules/tsx/dist/loader.mjs")
EXTRA = {"real-stack-documenso": [("apps/remix/server/router.ts", "tsx", ".env.example", "after the project's generate and build, env of .env.example"),
                                  ("apps/remix/build/server/hono/server/router.js", "node", ".env.example",
                                   "the project's build:server output, env of .env.example")],
         "ramen-api": [("src/index.ts", "probe-tsx", None, "tsx of the probe (the project has none)")],
         "hono-open-api-starter": [("src/app.ts", "tsx", ".env.example", "env of .env.example")],
         "fixture": []}
GENERATE = {"real-stack-documenso": "npm run prisma:generate -w @documenso/prisma; npm run translate; cd apps/remix && npm run build:server"}


def _run_image(name: str, generate: bool = False) -> modal.Image:
    if not LOCAL:
        return modal.Image.debian_slim()
    image = _checkout(_code(modal.Image.from_registry(container_runner.IMAGE, add_python="3.12"), name), name)
    env = " ".join(f"{k}={shlex.quote(v)}" for k, v in container_runner.ENV.items())
    image = (image.run_function(_restore, timeout=3600, cpu=4, memory=16384).pip_install("python-dotenv==1.1.1")
             .run_commands(f"mkdir -p /opt/probe-tsx && cd /opt/probe-tsx && env -i {env} npm install --no-audit --no-fund --ignore-scripts {PROBE_TSX[0]}"))
    if generate:  # a failure is an answer (`generate.json`), not a failed build
        image = image.run_commands(f"cd /work && env -i {env} sh -c {shlex.quote(GENERATE[name])} > /tmp/generate.log 2>&1; "
                                   f"echo $? > {container_runner.STATE}/generate.exit; tail -c 4000 /tmp/generate.log > {container_runner.STATE}/generate.log")
    return image


def _read_image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.debian_slim()
    image = (modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
             .run_commands(f"curl -fsSL -o /usr/local/bin/noir {apps.NOIR[0]} && echo '{apps.NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - "
                           "&& chmod +x /usr/local/bin/noir"))
    image = (_code(image, name).add_local_file(REPO / "benchmarks/noir-binding/warm.py", f"{MEASURE}/warm.py", copy=True)
             .run_commands(f"python {MEASURE}/warm.py"))
    return _checkout(image, name).add_local_file(HERE / "summarize.py", f"{MEASURE}/summarize.py")


app = modal.App("hono-routes")

DECLARED = r"""
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'
const dir = path.resolve(process.argv[2])
const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'))
const require = createRequire(path.join(dir, 'package.json'))
const out = { folder: process.argv[2], name: pkg.name ?? null, main: pkg.main ?? null, exports: pkg.exports ?? null, declared: {} }
const attempt = (key, fn) => { try { out.declared[key] = fn() } catch (e) { out.declared[key] = 'ERR ' + String(e.code || e.message).slice(0, 300) } }
if (pkg.main) attempt('main', () => require.resolve(path.resolve(dir, pkg.main)))
if (pkg.exports && pkg.name) attempt('exports', () => require.resolve(pkg.name))
out.wrangler_files = ['wrangler.toml', 'wrangler.json', 'wrangler.jsonc'].filter((f) => fs.existsSync(path.join(dir, f)))
if (out.wrangler_files.length) {
  try {
    const w = await import(pathToFileURL(require.resolve('wrangler')).href)
    const read = w.unstable_readConfig ?? w.experimental_readConfig ?? w.default?.unstable_readConfig ?? w.default?.experimental_readConfig
    const config = read({ config: path.join(dir, out.wrangler_files[0]) }, {})
    out.declared.wrangler = config.main ?? null
  } catch (e) { out.declared.wrangler = 'ERR ' + String(e?.stack || e).slice(0, 600) }
}
process.stdout.write('\nDAODAN-ANSWER ' + JSON.stringify(out) + '\n')
process.exit(0)
"""
INSPECT = r"""
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import path from 'node:path'
const target = path.resolve(process.argv[2])
const out = { module: process.argv[2] }
const done = (code) => { process.stdout.write('\nDAODAN-ANSWER ' + JSON.stringify(out) + '\n'); process.exit(code) }
setTimeout(() => { out.error = 'no answer in 90 seconds'; done(3) }, 90000)
process.on('uncaughtException', (e) => { out.uncaught = String(e?.stack || e).slice(0, 2000) })
try {
  const mod = await import(pathToFileURL(target).href)
  out.exports = Object.keys(mod)
  const dev = await import(pathToFileURL(createRequire(target).resolve('hono/dev')).href)
  const inspectRoutes = dev.inspectRoutes ?? dev.default?.inspectRoutes
  out.apps = {}
  for (const [name, value] of Object.entries(mod))
    if (value && Array.isArray(value.routes) && typeof value.fetch === 'function') out.apps[name] = inspectRoutes(value)
} catch (e) { out.error = String(e?.stack || e).slice(0, 3000) }
done(0)
"""
RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")  # the command under a parent that asks for its largest child's peak memory (KB on Linux)


def _chunks(answer: dict):
    payload = zlib.compress(json.dumps(answer).encode("utf-8"), 9)
    for start in range(0, len(payload), CHUNK):
        yield payload[start:start + CHUNK]


def _node(argv: list[str], cwd: str, env: dict) -> dict:
    """One Node command with the network blocked: exit, seconds, peak memory, the tail of its output and the answer after `DAODAN-ANSWER`."""
    import subprocess
    import time

    mark = f"/tmp/rss-{time.monotonic_ns()}"
    started = time.monotonic()
    try:
        r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=cwd, env=env, capture_output=True, text=True, timeout=300,
                           stdin=subprocess.DEVNULL)
        code, stdout, stderr = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        code, stdout, stderr = "timeout", "", ""
    answer = None
    for line in stdout.splitlines():
        if line.startswith("DAODAN-ANSWER "):
            answer = json.loads(line[len("DAODAN-ANSWER "):])
    return {"argv": argv, "cwd": cwd, "returncode": code, "seconds": round(time.monotonic() - started, 2),
            "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
            "stdout_tail": stdout.replace(f"DAODAN-ANSWER {json.dumps(answer)}", "")[-800:] if answer else stdout[-2000:],
            "stderr_tail": stderr[-2000:], "answer": answer}


def _hono_folders(root: pathlib.Path) -> list[str]:
    """The folders whose `package.json` depends on `hono` (outside `node_modules`)."""
    out = []
    for directory, names, files in os.walk(root):
        names[:] = [n for n in names if n not in ("node_modules", ".git")]
        if "package.json" in files:
            try:
                manifest = json.loads(pathlib.Path(directory, "package.json").read_text(encoding="utf-8"))
            except ValueError:
                continue
            if any("hono" in (manifest.get(field) or {}) for field in ("dependencies", "devDependencies", "peerDependencies")):
                out.append(os.path.relpath(directory, root))
    return sorted(out)


def _package_of(module: pathlib.Path) -> pathlib.Path:
    for folder in module.parents:
        if (folder / "package.json").is_file():
            return folder
    return module.parent


def _run(name: str, chosen: list[str], extra: list) -> dict:
    import subprocess

    sys.path[:0] = ["/daodan/core"]
    import preparation

    root = pathlib.Path("/work")
    env = dict(preparation.ENV)
    os.makedirs(env["HOME"], exist_ok=True)
    pathlib.Path("/tmp/declared.mjs").write_text(DECLARED, encoding="utf-8")
    pathlib.Path("/tmp/inspect.mjs").write_text(INSPECT, encoding="utf-8")
    restore = json.loads(pathlib.Path(preparation.STATE, "restore.json").read_text(encoding="utf-8"))
    out = {"name": name, "restore": restore,
           "node": subprocess.run(["node", "--version"], env=env, capture_output=True, text=True).stdout.strip(),
           "hono_folders": _hono_folders(root), "declared": [], "inspect": []}
    modules = {}  # absolute module -> how it was found
    for folder in out["hono_folders"]:
        found = _node(["node", "/tmp/declared.mjs", folder], str(root), env)
        out["declared"].append(found)
        for key, value in ((found["answer"] or {}).get("declared") or {}).items():
            if isinstance(value, str) and not value.startswith("ERR "):
                modules.setdefault(str((root / folder / value) if not value.startswith("/") else pathlib.Path(value)), []).append(f"{key} of {folder}")
    for module in chosen:
        modules.setdefault(str(root / module), []).append("chosen by hand")
    for module, how in modules.items():
        package = _package_of(pathlib.Path(module))
        tsx = any((folder / "node_modules/tsx/package.json").is_file() for folder in (package, *package.parents))
        for loader in (["node"], ["node", "--import", "tsx"]) if tsx else (["node"],):
            run = _node([*loader, "/tmp/inspect.mjs", module], str(package), env)
            out["inspect"].append({"module": os.path.relpath(module, root), "found_by": how, "loader": " ".join(loader), **run})
    generated = pathlib.Path(preparation.STATE, "generate.exit")
    if generated.is_file():
        out["generate"] = {"argv": GENERATE[name], "returncode": generated.read_text().strip(),
                           "log": pathlib.Path(preparation.STATE, "generate.log").read_text(encoding="utf-8", errors="replace")}
    for module, loader, env_file, label in extra:
        from dotenv import dotenv_values
        target = root / module
        argv = {"node": ["node"], "tsx": ["node", "--import", "tsx"], "probe-tsx": ["node", "--import", f"file://{PROBE_TSX[1]}"]}[loader]
        added = {k: v for k, v in dotenv_values(root / env_file).items() if v is not None} if env_file else {}
        run = _node([*argv, "/tmp/inspect.mjs", str(target)], str(_package_of(target)), {**env, **added})
        out["inspect"].append({"module": module, "found_by": [label], "loader": " ".join(argv), "env_file": env_file, **run})
    return out


def _read(name: str) -> dict:
    import collections
    import subprocess
    import time
    import types

    sys.path[:0] = ["/daodan/core", MEASURE]
    import binder
    import flows
    import premap
    import semantic_store
    import snapshot
    from premap import noir
    from snapshot_store import open_snapshot

    root = pathlib.Path("/work")
    manifest = pathlib.Path("/tmp/hono-routes/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    snapshot.read_project(root, manifest)
    out = {"name": name, "snapshot_seconds": round(time.monotonic() - started, 1)}
    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    started = time.monotonic()
    r = subprocess.run(command["argv"], cwd=root, env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    out["noir"] = {"argv": command["argv"], "returncode": r.returncode, "seconds": round(time.monotonic() - started, 1), "stderr_tail": r.stderr[-500:]}
    report = json.loads(r.stdout) if r.returncode == 0 else {}
    endpoints = report.get("endpoints") or []
    out["noir"]["endpoints"] = len(endpoints)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        context = premap.Context(manifest, store)
        facts = flows.Facts(store, db)
        read = (noir.read(context, [command], [{"returncode": 0, "stdout": r.stdout, "stderr": "", "root": str(root)}]) if endpoints
                else {"facts": {}, "gaps": []})
        http = [e for e in read["facts"].get("noir_entries", []) if e.get("shape") == "http"]
        bound = binder.bind(http, facts, semantic_store._Resolver(db))
        out["noir_rows"] = [{"method": b.get("method"), "path": b.get("path"), "site": b.get("site"), "handler": b.get("handler"),
                             "symbol": None if b.get("gap") else b.get("symbol"), "gap": b.get("gap")} for b in bound]
        out["noir_gaps"] = dict(collections.Counter(g["kind"] for g in read["gaps"]))
        functions = [d for declared in facts.functions.values() for d in declared]
        import summarize
        counted = summarize.names(functions)
        out["functions"] = len(functions)
        out["names"] = dict(counted)
        out["symbols"] = {d["name"]: facts.node(d["id"]) for d in functions if counted[d["name"]] == 1}
    return out


def _functions(name: str):
    def run(chosen: list[str], extra: list):
        import traceback
        try:
            answer = _run(name, chosen, extra)
        except BaseException:
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        yield from _chunks(answer)

    def generated(extra: list):
        yield from run([], extra)

    def read():
        import traceback
        try:
            answer = _read(name)
        except BaseException:
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        yield from _chunks(answer)
    key = name.replace("-", "_")
    run.__name__ = run.__qualname__ = f"run_{key}"
    read.__name__ = read.__qualname__ = f"read_{key}"
    globals()[run.__name__] = runner = app.function(image=_run_image(name), timeout=1800, block_network=True, memory=3072, cpu=2)(run)
    globals()[read.__name__] = reader = app.function(image=_read_image(name), timeout=3600, block_network=True, memory=12288, cpu=4)(read)
    after = None
    if name in GENERATE:
        generated.__name__ = generated.__qualname__ = f"run_{key}_generated"
        globals()[generated.__name__] = after = app.function(image=_run_image(name, generate=True), timeout=1800, block_network=True,
                                                             memory=3072, cpu=2)(generated)
    return runner, reader, after


FUNCTIONS = {name: _functions(name) for name in NAMES}


@app.function(image=_read_image("fixture"), timeout=600)
def compare(ran: dict, read: dict) -> dict:
    """The counts of `summarize.compare` for every load that gave routes (no project code: two answers and Daodan's `flows.path_schema`)."""
    from collections import Counter
    sys.path[:0] = ["/daodan/core", MEASURE]
    import flows
    import summarize

    out = []
    counted = Counter(read.get("names") or {})
    for load in ran.get("inspect") or []:
        for export, inspected in ((load.get("answer") or {}).get("apps") or {}).items():
            out.append({"module": load["module"], "found_by": load["found_by"], "loader": load["loader"], "export": export,
                        "raw_entries": len(inspected), "middleware": sum(1 for r in inspected if r.get("isMiddleware")),
                        **summarize.compare(summarize.routes(inspected), read.get("noir_rows") or [], counted, read.get("symbols") or {},
                                            flows.path_schema)})
    return {"loads": out}


@app.function(image=modal.Image.from_registry("node:24-bookworm", add_python="3.12").add_local_dir(HERE / "fixture", "/lockwork", copy=True,
                                                                                    ignore=["**/node_modules/**"]) if LOCAL else modal.Image.debian_slim(),
              timeout=600)
def lock() -> dict:
    """The fixture's lockfile, made from its package.json with the network open and no script run."""
    import subprocess
    r = subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"], cwd="/lockwork",
                       capture_output=True, text=True, timeout=500)
    lockfile = pathlib.Path("/lockwork/package-lock.json")
    return {"returncode": r.returncode, "stderr": r.stderr[-2000:], "lock": lockfile.read_text(encoding="utf-8") if lockfile.is_file() else None}


def _collect(function, *args) -> dict:
    return json.loads(zlib.decompress(b"".join(function.remote_gen(*args))))


def _one(name: str) -> dict:
    runner, reader, after = FUNCTIONS[name]
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        ran = pool.submit(_collect, runner, apps.APPS[name][3], [] if after else EXTRA[name])
        read = pool.submit(_collect, reader)
        later = pool.submit(_collect, after, EXTRA[name]) if after else None
        ran, read = ran.result(), read.result()
        if later:
            later = later.result()
            ran["inspect"] = ran.get("inspect", []) + later.get("inspect", [])
            ran["generate"] = later.get("generate") or later.get("failed")
    counts = compare.remote(ran, read) if "failed" not in ran and "failed" not in read else {"loads": []}
    read = {k: v for k, v in read.items() if k not in ("names", "symbols")}  # the snapshot's names: thousands, used only by `compare`
    return {"application": dict(zip(("repository", "commit", "licence", "chosen", "note"), apps.APPS[name])), "run": ran, "read": read, **counts}


@app.local_entrypoint()
def main(mode: str = "probes", only: str = ""):
    if mode == "lock":
        answer = lock.remote()
        print("exit", answer["returncode"], answer["stderr"][-300:])
        if answer["lock"]:
            (HERE / "fixture/package-lock.json").write_bytes(answer["lock"].replace("\r\n", "\n").encode("utf-8"))
        return
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    chosen = [n for n in NAMES if not only or n in only.split(",")]
    with concurrent.futures.ThreadPoolExecutor(len(chosen)) as pool:
        calls = {name: pool.submit(_one, name) for name in chosen}
        for name, call in calls.items():
            try:
                answer = call.result()
            except Exception as error:  # a container that failed is a missing answer with its cause, not the end of the others
                answer = {"failed": f"{type(error).__name__}: {str(error)[-800:]}"}
            (out / f"{name}.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
            print("===", name, answer.get("failed") or "")
            for load in answer.get("loads", []):
                print(json.dumps({k: load[k] for k in ("module", "found_by", "loader", "export", "inspect_routes", "noir_routes", "common",
                                                        "inspect_handlers", "noir_bound", "common_same_function")}))
