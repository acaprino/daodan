"""`nuxt prepare` (and the other commands of Nuxt's CLI) on Modal, in a container with the network blocked.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py --mode lock
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py

`--mode lock` writes each fixture's `package-lock.json` (the one moment it is made: `npm install --package-lock-only
--ignore-scripts`, run with the network open in a Modal function, never on this PC). `--mode probes` (the default) builds one
image with every fixture restored from its lockfile the way Daodan's container restores a project (`npm ci`, lifecycle scripts
included, on the whole project: the fixtures' `postinstall` is `nuxt prepare`, as in Nuxt's own starter; while the image is
built the network is open), then runs each variant of `COMMANDS` in a copy, with the network blocked and the environment of
Daodan's runner (`PATH`, `HOME`, `npm_config_update_notifier`; no `CI`, no telemetry switch) plus the variant's own. Every answer
(`argv`, `returncode`, `stdout`, `stderr`, seconds, the files the command wrote in the project, in `node_modules/.cache` and in
`HOME`, the `.nuxt/` listing and the text of the `.nuxt/` files that name a page, a handler or a marker of the fixture) goes to
`results/<variant>.json`. The project's code (`nuxt.config.ts`, the modules, `node_modules`) runs only in the container.
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
NAMES = ("nuxt3", "nuxt4")
IGNORE = ["**/package-lock.json", "**/node_modules/**", "**/.nuxt/**", "**/.output/**"]

image = modal.Image.from_registry("node:24-bookworm", add_python="3.12")
if LOCAL:
    image = image.pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
    image = image.add_local_dir(FIXTURES, "/lockwork", copy=True, ignore=IGNORE)
    locked = [name for name in NAMES if (FIXTURES / name / "package-lock.json").is_file()]
    for name in locked:  # the whole project and its lockfile, restored as the container restores it: scripts on
        image = image.add_local_dir(FIXTURES / name, f"/fix/{name}", copy=True, ignore=["**/node_modules/**", "**/.nuxt/**", "**/.output/**"])
    if locked:
        image = image.run_commands(*(f"cd /fix/{name} && npm ci --no-audit --no-fund 2>&1 | tail -30" for name in locked))
    image = (image.add_local_dir(REPO / "daodan/core", "/daodan/core", ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/data"))
app = modal.App("nuxt-routes", image=image)
RECORDED = REPO / "tests/fixtures/premap/nuxt/answers.json"
MARKERS = ("pages/", "server/api", "server/routes", "server/custom", "quokka", "from-hook", "from-config", "/api/", "sitemap", "typed-router")
HOME = "/work/home"


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


def _listing(root: str) -> dict[str, int]:
    """`{path: size}` of the files under `root`, `node_modules` apart from its caches (`.cache`, `.vite`)."""
    out = {}
    for directory, names, files in os.walk(root):
        if os.path.basename(directory) == "node_modules" and os.path.dirname(directory) == root:
            names[:] = [n for n in names if n in (".cache", ".vite")]
            files = []
        for f in files:
            path = os.path.join(directory, f)
            try:
                out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
            except OSError:
                pass
    return out


def _generated(root: str) -> dict[str, str]:
    """The text of the `.nuxt/` files that hold a marker of the fixture, cut at 60,000 characters."""
    out = {}
    for rel in sorted(_listing(root)):
        if not rel.startswith(".nuxt/") or os.path.getsize(os.path.join(root, rel)) > 400_000:
            continue
        text = pathlib.Path(root, rel).read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in MARKERS):
            out[rel] = text[:60_000]
    return out


RSS = ("import resource, subprocess, sys\n"
       "code = subprocess.run(sys.argv[2:]).returncode\n"
       "open(sys.argv[1], 'w').write(str(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss))\n"
       "sys.exit(code)\n")  # the command under a parent that asks for its largest child's peak memory (KB on Linux)
BIN = "/tmp/daodan-bin"


def _launcher() -> None:
    """`daodan-nuxt` as `container_runner.TOOLS["nuxt"]` installs it: a shell script that runs Daodan's script with Node."""
    os.makedirs(BIN, exist_ok=True)
    target = pathlib.Path(BIN, "daodan-nuxt")
    target.write_text('#!/bin/sh\nexec node /daodan/core/premap/nuxt_pages.mjs "$@"\n', encoding="utf-8")
    target.chmod(0o755)


def _run(argv: list[str], cwd: str, env: dict | None = None, dump: bool = True) -> dict:
    import subprocess
    import sys
    import time

    os.makedirs(HOME, exist_ok=True)
    _launcher()
    before, home_before = _listing(cwd), _listing(HOME)
    mark = f"/tmp/rss-{time.monotonic_ns()}"
    started = time.monotonic()
    try:
        r = subprocess.run([sys.executable, "-c", RSS, mark, *argv], cwd=cwd, capture_output=True, text=True, timeout=600,
                           stdin=subprocess.DEVNULL, env={"PATH": f"{BIN}:{os.environ['PATH']}", "HOME": HOME,
                                                          "npm_config_update_notifier": "false", **(env or {})})
        answer = {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired:
        answer = {"returncode": "timeout", "stdout": "", "stderr": ""}
    after = _listing(cwd)
    return {"argv": argv, "cwd": cwd.removeprefix("/work/"), **answer, "seconds": round(time.monotonic() - started, 2),
            "max_rss_mb": round(int(pathlib.Path(mark).read_text()) / 1024, 1) if os.path.exists(mark) else None,
            "left_in_the_project": sorted(set(after) - set(before)),
            "changed_in_the_project": sorted(f for f in set(after) & set(before) if after[f] != before[f]),
            "left_in_home": sorted(set(_listing(HOME)) - set(home_before)),
            "nuxt_dir": {rel: size for rel, size in sorted(after.items()) if rel.startswith(".nuxt/")},
            **({"generated": _generated(cwd)} if dump else {})}


def _write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _no_nuxt(root: pathlib.Path) -> None:
    """The state before anything generated: what the restore's `postinstall` wrote is removed."""
    import shutil
    shutil.rmtree(root / ".nuxt", ignore_errors=True)


def _then(*edits):
    def apply(root: pathlib.Path) -> None:
        for edit in edits:
            edit(root)
    return apply


def _typed_pages(root: pathlib.Path) -> None:
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace("  telemetry: false,\n", "  telemetry: false,\n  experimental: { typedPages: true },\n"), encoding="utf-8")


def _config_throws(root: pathlib.Path) -> None:
    _write(root / "nuxt.config.ts", "throw new Error('nuxt.config needs a database')\n")


def _no_config(root: pathlib.Path) -> None:
    (root / "nuxt.config.ts").unlink()


def _no_pages(root: pathlib.Path) -> None:
    """No `pages/` folder, and a config without the route its hook adds (a route whose file is missing fails the command)."""
    import shutil
    shutil.rmtree(root / "pages", ignore_errors=True)
    shutil.rmtree(root / "app/pages", ignore_errors=True)
    _write(root / "nuxt.config.ts", "export default defineNuxtConfig({ compatibilityDate: '2025-07-15', telemetry: false, devtools: { enabled: false } })\n")


def _hook_file_missing(root: pathlib.Path) -> None:
    """The page file the config's `pages:extend` hook points at is gone: a route whose file is missing."""
    for path in (root / "pages/about.vue", root / "app/pages/about.vue"):
        path.unlink(missing_ok=True)


def _default_config(root: pathlib.Path) -> None:
    """The config without the two lines that switch off telemetry and the devtools: what a project that sets neither runs."""
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace("  telemetry: false,\n", "").replace("  devtools: { enabled: false },\n", ""), encoding="utf-8")


def _layer(root: pathlib.Path) -> None:
    """A Nuxt layer outside the project, `--extends`' argument, that asks for the typed pages."""
    _write(pathlib.Path("/work/daodan-layer/nuxt.config.ts"), "export default defineNuxtConfig({ experimental: { typedPages: true } })\n")


def _root_layout(root: pathlib.Path) -> None:
    """Nuxt 4's `app/` folder moved to the root: the layout of Nuxt 3."""
    import shutil
    for child in list((root / "app").iterdir()):
        shutil.move(str(child), str(root / child.name))
    (root / "app").rmdir()
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace("./app/pages/about.vue", "./pages/about.vue"), encoding="utf-8")


PREPARE = ["npx", "--no-install", "nuxt", "prepare"]
KIT = """import { loadNuxt, buildNuxt } from '@nuxt/kit'
const nuxt = await loadNuxt({ cwd: process.cwd(), overrides: { _prepare: true } })
const found = []
const walk = (pages, hook) => pages.forEach((p) => { found.push({ hook, name: p.name, path: p.path, file: p.file, children: (p.children || []).length }); walk(p.children || [], hook) })
nuxt.hook('pages:extend', (pages) => walk(pages, 'pages:extend'))
nuxt.hook('pages:resolved', (pages) => walk(pages, 'pages:resolved'))
await buildNuxt(nuxt)
await nuxt.close()
console.log(JSON.stringify(found))
"""
RESOLVE = """const { createRequire } = require('node:module')
const r = createRequire(process.cwd() + '/')
const out = {}
for (const name of ['@nuxt/kit', 'nuxt', 'nuxt/package.json', '@nuxt/kit/package.json']) {
  try { out[name] = r.resolve(name) } catch (error) { out[name] = 'ERR ' + error.code }
}
try { out.nuxtThenKit = createRequire(r.resolve('nuxt')).resolve('@nuxt/kit') } catch (error) { out.nuxtThenKit = 'ERR ' + error.code }
console.log(JSON.stringify(out, null, 1))
"""
OFFLINE = {"npm_config_offline": "true"}
SWITCHES = {"NUXT_TELEMETRY_DISABLED": "1", "CI": "1", "NO_COLOR": "1"}  # what a CI sets: asked for apart


def _variants(fx: str) -> dict:  # variant -> (fixture, edit, [(argv, env)], bare, dump)
    return {
        f"{fx}-after-restore": (fx, None, [(["ls", "-la", ".nuxt", ".nuxt/types"], None)], False, True),
        f"{fx}-prepare": (fx, _no_nuxt, [(PREPARE, OFFLINE)], False, True),
        f"{fx}-prepare-again": (fx, None, [(PREPARE, OFFLINE)], False, True),
        f"{fx}-prepare-ci-no-telemetry": (fx, _no_nuxt, [(PREPARE, {**OFFLINE, **SWITCHES})], False, False),
        f"{fx}-prepare-no-offline": (fx, _no_nuxt, [(PREPARE, None)], False, False),
        f"{fx}-typed-pages": (fx, _then(_no_nuxt, _typed_pages), [(PREPARE, OFFLINE)], False, True),
        f"{fx}-build-prepare": (fx, _no_nuxt, [(["npx", "--no-install", "nuxt", "build", "--prepare"], OFFLINE)], False, True),
        f"{fx}-help": (fx, None, [(["npx", "--no-install", "nuxt", "--help"], OFFLINE),
                                  (["npx", "--no-install", "nuxt", "prepare", "--help"], OFFLINE),
                                  (["npx", "--no-install", "nuxt", "build", "--help"], OFFLINE),
                                  (["npx", "--no-install", "nuxi", "--help"], OFFLINE),
                                  (["npx", "--no-install", "nuxt", "info"], OFFLINE),
                                  (["ls", "node_modules/.bin"], None)], False, False),
        f"{fx}-config-throws": (fx, _then(_no_nuxt, _config_throws), [(PREPARE, OFFLINE)], False, False),
        f"{fx}-no-config": (fx, _then(_no_nuxt, _no_config), [(PREPARE, OFFLINE)], False, True),
        f"{fx}-no-pages": (fx, _then(_no_nuxt, _no_pages), [(PREPARE, OFFLINE)], False, True),
        f"{fx}-hook-file-missing": (fx, _then(_no_nuxt, _hook_file_missing), [(PREPARE, OFFLINE)], False, False),
        f"{fx}-not-installed": (fx, None, [(PREPARE, OFFLINE)], True, False),
        f"{fx}-default-config": (fx, _then(_no_nuxt, _default_config), [(PREPARE, OFFLINE)], False, False),
        f"{fx}-extends-layer": (fx, _then(_no_nuxt, _layer), [(PREPARE + ["--extends", "/work/daodan-layer"], OFFLINE)], False, True),
        f"{fx}-kit-pages": (fx, _no_nuxt, [(["node", "--input-type=module", "-e", KIT], OFFLINE)], False, False),
        f"{fx}-kit-resolve": (fx, None, [(["node", "-e", RESOLVE], OFFLINE)], False, False),
        f"{fx}-pages": (fx, None, [(["daodan-nuxt"], None)], False, False),  # Daodan's script, the project as the restore left it
    }


COMMANDS = {**_variants("nuxt3"), **_variants("nuxt4"),
            "nuxt3-not-installed-no-offline": ("nuxt3", None, [(PREPARE, None)], True, False),
            "nuxt4-root-layout": ("nuxt4", _then(_no_nuxt, _root_layout), [(PREPARE, OFFLINE)], False, True)}


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def probe(variants: list[str]) -> dict:
    import subprocess

    def version(name: str, package: str) -> str | None:
        path = f"/fix/{name}/node_modules/{package}/package.json"
        return json.load(open(path))["version"] if os.path.isfile(path) else None

    out = {"_env": {"node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
                    "npm": subprocess.run(["npm", "--version"], capture_output=True, text=True).stdout.strip(),
                    "packages": {name: {package: version(name, package) for package in
                                        ("nuxt", "@nuxt/kit", "@nuxt/cli", "nuxi", "nitropack", "nitro", "vue", "vue-router", "unplugin-vue-router", "vite")
                                        if version(name, package)}
                                 for name in NAMES if os.path.isdir(f"/fix/{name}/node_modules")}}}
    for variant in variants:
        fixture, edit, commands, bare, dump = COMMANDS[variant]
        project = _variant(variant, fixture, edit, node_modules=not bare)
        out[variant] = [_run(argv, project, env, dump) for argv, env in commands]
    return out


def _build_dir(root: pathlib.Path) -> None:
    """`buildDir` is Nuxt's option for the folder it generates into: `.nuxt` is only the default."""
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace("  telemetry: false,\n", "  telemetry: false,\n  buildDir: '.generated',\n"), encoding="utf-8")


def _layer(root: pathlib.Path) -> None:
    """A local layer with a page of its own (`extends`): its file is under the project, the config that names it is code."""
    pages = "app/pages" if (root / "app").is_dir() else "pages"
    _write(root / "layers/base/nuxt.config.ts", "export default defineNuxtConfig({})\n")
    _write(root / "layers/base" / pages / "from-layer.vue", "<template>\n  <div>\n    <h1>From a layer</h1>\n  </div>\n</template>\n")
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace("  telemetry: false,\n", "  telemetry: false,\n  extends: ['./layers/base'],\n"), encoding="utf-8")


def _redirect(root: pathlib.Path) -> None:
    """A route with no file, added in code by the config's own hook: a redirect."""
    config = root / "nuxt.config.ts"
    config.write_text(config.read_text(encoding="utf-8").replace(
        "      pages.push({ name: 'from-hook'", "      pages.push({ name: 'old', path: '/old', redirect: '/about' })\n      pages.push({ name: 'from-hook'"), encoding="utf-8")


SOURCE_VARIANTS = {  # the key in answers.json -> (fixture, a change to its copy, whether its packages are left out)
    "nuxt3": ("nuxt3", None, False),  # as the restore left it: its `postinstall` (`nuxt prepare`) already wrote `.nuxt`
    "nuxt4": ("nuxt4", None, False),
    "nuxt4-root-layout": ("nuxt4", _root_layout, False),
    "no-pages": ("nuxt3", _no_pages, False),
    "config-throws": ("nuxt3", _config_throws, False),
    "build-dir": ("nuxt3", _then(_no_nuxt, _build_dir), False),
    "not-installed": ("nuxt3", None, True),
    "hook-file-missing": ("nuxt3", _then(_no_nuxt, _hook_file_missing), False),
    "layer": ("nuxt3", _layer, False),
    "layer-nuxt4": ("nuxt4", _layer, False),
    "redirect": ("nuxt3", _redirect, False),
    "timeout": ("nuxt3", None, False),  # the pages command with 0.3 seconds, which it needs 0.9 of: `timeout` ends it
}


@app.function(timeout=900)
def commands() -> dict:
    """What the source asks the container to run for each fixture."""
    import shutil
    import sys
    from pathlib import Path

    sys.path[:0] = ["/daodan/core"]
    import premap
    import snapshot
    from snapshot_store import open_snapshot

    out = {}
    for name in NAMES:
        project, manifest = Path(f"/work/commands-{name}"), Path(f"/work/commands-out-{name}/manifest.sqlite")
        shutil.copytree(f"/lockwork/{name}", project)
        snapshot.write_snapshot(project, manifest)
        with open_snapshot(manifest) as store:
            out[name] = premap.nuxt.commands(premap.Context(manifest, store))
    return out


@app.function(cpu=2, memory=4096, timeout=1800, block_network=True)
def source(asked: dict) -> dict:
    """Each variant's commands, as the source wrote them, with the network blocked: the answers in order."""
    out = {}
    for key, (fixture, edit, bare) in SOURCE_VARIANTS.items():
        project = _variant(f"source-{key}", fixture, edit, node_modules=not bare)
        given = [dict(command) for command in asked[fixture]]
        if key == "timeout":
            given[-1]["argv"] = [*given[-1]["argv"][:2], "0.3", *given[-1]["argv"][3:]]
        answers = [_run(command["argv"], project, command["env"], dump=False) for command in given]
        out[key] = [{name: answer[name] for name in ("returncode", "stdout", "stderr")} for answer in answers]
        out[key + "_run"] = {"argv": [answer["argv"] for answer in answers], "seconds": [answer["seconds"] for answer in answers],
                             "max_rss_mb": [answer["max_rss_mb"] for answer in answers],
                             "left": sorted(set(path for answer in answers for path in answer["left_in_the_project"]
                                                if not path.startswith(".nuxt/")))}
    return out


@app.local_entrypoint()
def main(mode: str = "probes"):
    if mode == "source":
        asked = commands.remote()
        print("commands:", json.dumps({name: [(c["cwd"], c["argv"], c["env"]) for c in items or []] for name, items in asked.items()}))
        answers = source.remote(asked)
        RECORDED.parent.mkdir(parents=True, exist_ok=True)
        RECORDED.write_bytes((json.dumps({key: value for key, value in answers.items() if not key.endswith("_run")},
                                         indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        OUT.mkdir(exist_ok=True)
        (OUT / "source-run.json").write_bytes((json.dumps({key[:-4]: value for key, value in answers.items() if key.endswith("_run")},
                                                          indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        for key in SOURCE_VARIANTS:
            prepare, printed, pages = answers[key]
            run = answers[key + "_run"]
            print(f"=== {key}: prepare exit {prepare['returncode']} in {run['seconds'][0]} s ({run['max_rss_mb'][0]} MB), print exit {printed['returncode']}, "
                  f"{len(printed['stdout'])} bytes; pages exit {pages['returncode']} in {run['seconds'][2]} s ({run['max_rss_mb'][2]} MB), "
                  f"{len(pages['stdout'])} bytes; left outside .nuxt: {run['left']}")
            print((pages["stderr"].strip() or pages["stdout"].strip())[:300])
        return
    if mode == "lock":
        for name in NAMES:
            answer = lock.remote(name)
            print(name, "exit", answer["returncode"], answer["stderr"][-300:])
            if answer["lock"]:
                (FIXTURES / name / "package-lock.json").write_bytes(answer["lock"].replace("\r\n", "\n").encode("utf-8"))
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
            print(f"$ {' '.join(answer['argv'])[:120]}  -> exit {answer['returncode']} in {answer['seconds']} s ({answer['max_rss_mb']} MB), "
                  f"left {len(answer['left_in_the_project'])} files, .nuxt {len(answer['nuxt_dir'])} files")
            print((answer["stdout"] or "")[:600])
            if answer["stderr"].strip():
                print("--- stderr:", answer["stderr"].strip()[:600])
