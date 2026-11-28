"""Starting the app the project declares, in the container (plan task 11.2; spec of the project's interfaces, 7.1-7.3).

`plan` reads the pre-map's `starts` and `builds` (`premap/npm_start.py`): per module the `start` script, else the
`dev` one; the module's `build` first where the start reads compiled output (`needs_build`). The command is the
declared one, `npm run <script>`, never changed; its environment is the container's, plus the variables of the example
`.env` files the project publishes and Git tracks in the app's folder (`_examples`): the test values the app asks for. Where the project declares none, or a start needs a build nobody
declares, or its runner is not npm (pnpm, Yarn and Bun are not yet run: `start_runner_not_supported`), nothing runs
and the gap says why.

`observe` is one container run, as the JavaScript observer's (`dynamic/javascript.py`): the preparation with the
registries (Daodan's Node, the project's restore), then the execution with no network: each build, then the driver
(`app.cjs`) which starts the app in its own process group, waits for the declared port or, with none, for the local
address the app prints (never a scan), and stops it (SIGTERM, then SIGKILL after 10 s). What did not happen is a gap
with its cause and the last lines of the log: `build_failed`, `app_not_started` (it exited first), `not_ready` (its
port or printed address never answered within `READY` s), `port_not_declared` (no port, nothing printed),
`app_not_stopped` (a process of its group, or its port, outlived the stop).

With `explore` the driver is `explore.cjs` (plan task 11.3): headless Chromium from Playwright, installed in the
preparation as `playwright-core` with its browser (`PLAYWRIGHT`, kept for the run: `keep_root`), opens the app,
reads each page's controls from Playwright's accessibility tree, presses each once and keeps the functions of the
project that ran (`explore-<n>.json`, one file per app, beside `app-<n>.json`). Back come its counts (`explored`) and
its gaps; a run that wrote no file is `explore_failed` with the driver's reason.
"""
from __future__ import annotations

import json
import posixpath
import shlex
from pathlib import Path

import preparation
from dynamic import javascript  # the browser's hosts, where the observer already reaches them
from indexers import typescript  # the image and the restores of the analyzer of the same languages

DRIVER = Path(__file__).with_name("app.cjs").resolve()
EXPLORER = Path(__file__).with_name("explore.cjs").resolve()
PLAYWRIGHT = "1.64.1"  # playwright-core on npm: the pin of the observer's own proof
IN, T = preparation.IN, preparation.T
OUT = "/daodan/out"
READY = 90  # the seconds an app has to answer on its port
BUILD = 900  # the seconds a build may take
EXPLORE = 900  # the seconds the exploration may take, beside its own cap (`explore.cjs`)
MEMORY = 4 * 2**30


def plan(record: dict, explore: bool = False, seeds: tuple[str, ...] = (), pages: list[dict] = ()) -> dict:
    """`{apps, gaps, roots, toolchains, explore, seeds}` from the pre-map `record`: see the module's docstring. An app
    is the `starts` entry chosen for a module, with its `build` entry where it needs one; `seeds` are routes (paths)
    the exploration opens besides the app's root; `pages`, the framework rows of the entry points (`entry_points`), give
    each app the pages it opens too."""
    import premap
    from dynamic import rank  # the user's command, then the assistant's (`commands.merged`), then the project's
    builds: dict[str, dict] = {}
    for entry in sorted(record.get("builds", []), key=rank):
        builds.setdefault(entry["root"], entry)
    chosen: dict[str, dict] = {}
    for entry in sorted(record.get("starts", []), key=lambda entry: (rank(entry), entry["mode"] != "start")):
        chosen.setdefault(entry["root"], entry)  # start before dev
    apps, gaps = [], []
    for root, entry in sorted(chosen.items()):
        if entry["runner"] != "npm":
            gaps.append({"kind": "start_runner_not_supported", "path": entry["declared_in"], "runner": entry["runner"],
                         "detail": f"{entry['declared_in']} is started with {entry['runner']}, which the exploration "
                                   "does not run yet: the app is not started"})
        elif entry["needs_build"] and root not in builds:
            gaps.extend({key: value for key, value in gap.items() if key != "source"}
                        for gap in record.get("gaps", [])
                        if gap.get("kind") == "build_command_missing" and gap.get("path") == _manifest(entry))
        else:
            apps.append({**entry, **({"build": builds[root]} if entry["needs_build"] else {}),
                         "seeds": _pages(pages, root)})
    if not record.get("starts"):
        gaps.append({"kind": "no_start_command", "detail": "no package.json of the project declares a start or dev "
                                                           "script that starts an app: nothing is explored"})
    gaps += [{key: value for key, value in gap.items() if key != "source"} for gap in record.get("gaps", [])
             if gap.get("kind") == "no_start_command"]
    return {"apps": apps, "gaps": gaps,
            "roots": sorted(premap.roots(record, typescript.UNIT_KINDS, typescript.WORKSPACES)),
            "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") in ("node", "bun")],
            "explore": explore, "seeds": list(seeds)}


def _pages(rows: list[dict], root: str) -> list[str]:
    """The pages the sources declare (the rows marked `page`) in the app's folder, as the paths the exploration opens besides `/`;
    a pattern (a `schema` with a `{}`) or a route with no single schema is not a page to open, and an endpoint is not a page."""
    return sorted({row["path"] for row in rows if row.get("page")
                   and isinstance(row.get("schema"), str) and "{}" not in row["schema"]
                   and (root == "." or row["site"].startswith(f"{root}/"))})


def _manifest(entry: dict) -> str:
    return entry["declared_in"].partition("#")[0]


def _script(entry: dict) -> str:
    return entry["declared_in"].rpartition("#scripts.")[2]


def _command(entry: dict) -> str:
    """The command's words where it states them (a command of the user or the assistant, `commands`), else the
    script of its `package.json`."""
    if entry.get("argv"):
        return shlex.join(entry["argv"])
    return f"npm run {shlex.quote(_script(entry))}"


def _chains(planned: dict) -> dict:
    return preparation.toolchains([item for item in planned.get("toolchains") or ()
                                   if preparation.EXACT.match(str(item.get("version") or ""))])


def scripts(planned: dict, restores: list[str]) -> tuple[str, str]:
    """The preparation's script and the execution's: `restores` are the lines of the project's own restore."""
    chains = _chains(planned)
    explore = bool(planned.get("explore"))
    # the browser, as the observer prepares Playwright's (`javascript.scripts`): apt over HTTPS, the headless shell
    browser = [f"{{ npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error"
               f" playwright-core@{PLAYWRIGHT} ; }} >&2",
               'for f in /etc/apt/sources.list /etc/apt/sources.list.d/ubuntu.sources; do',
               '  if [ -f "$f" ]; then sed -i "s|http://|https://|g" "$f"; fi', 'done',
               f"node {T}/npm/lib/node_modules/playwright-core/cli.js install --with-deps --only-shell chromium >&2"]
    prepare = ["set -u", f'mkdir -p {T}/bin "$HOME"', *preparation.setup(["node"])["lines"], *chains["lines"],
               *(browser if explore else []), "cd /work || exit 70", *restores]
    execute = ["set -u", f"mkdir -p {OUT}",
               *([f"export DAODAN_PLAYWRIGHT={T}/npm/lib/node_modules/playwright-core"] if explore else [])]
    for number, one in enumerate(planned["apps"]):
        folder = shlex.quote(posixpath.normpath(posixpath.join("/work", one["root"])))
        execute.append("s=$(date +%s); c=0")
        if one.get("build"):
            execute += [f"( cd {folder} && timeout -k 30 {BUILD} {_command(one['build'])} ) > {OUT}/build-{number}.log "
                        "2>&1; c=$?", f'echo "DAODAN-APP {number} build $c $(( $(date +%s) - s ))"']
        port = one["port"] or "-"
        seeds = sorted({*(planned.get("seeds") or ()), *one.get("seeds", ())})
        driver, more = (EXPLORER, f" {shlex.quote(json.dumps(seeds))}") if explore else (DRIVER, "")
        execute += ['if [ "$c" = 0 ]; then',
                    f"  timeout -k 30 {(EXPLORE if explore else 0) + READY + 60} node {IN}/{driver.name} {OUT} {number} "
                    f"{folder} {port} {READY} {shlex.quote(_command(one))}{more} > {OUT}/driver-{number}.log 2>&1",
                    f'  echo "DAODAN-APP {number} exit $? $(( $(date +%s) - s ))"', "fi"]
    return "\n".join([*prepare, "exit 0"]) + "\n", "\n".join([*execute, "exit 0"]) + "\n"


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _marks(log: str) -> dict[tuple[int, str], str]:
    """The execution's own marks in its log, `DAODAN-APP <app> build|exit <code> <seconds>`: `{(app, kind): code}`."""
    marks = {}
    for line in log.splitlines():
        parts = line.split()
        if len(parts) == 5 and parts[0] == "DAODAN-APP" and parts[1].isdigit() and parts[2] in ("build", "exit"):
            marks[(int(parts[1]), parts[2])] = parts[3]
    return marks


def _tail(text: str) -> str:
    return " | ".join(line.strip() for line in text.strip().splitlines()[-8:])[-600:]


def _outcome(one: dict, number: int, built: str | None, ended: str, back: Path, explore: bool = False) \
        -> tuple[dict, list[dict]]:
    """One app's entry and its gaps, from the build mark (`built`: its exit code), the driver's file and the run's end."""
    entry = {key: one[key] for key in ("root", "mode", "declared_in")}
    command = f"{_command(one)} in {one['root']}"

    def gap(kind: str, detail: str) -> list[dict]:
        return [{"kind": kind, "path": one["declared_in"], "detail": detail}]

    if built not in (None, "0"):
        return {**entry, "state": "not_started"}, gap(
            "build_failed", f"{_command(one['build'])} in {one['root']} exited with code {built}: "
                            f"{_tail(_text(back / f'build-{number}.log'))}")
    try:
        found = json.loads((back / f"app-{number}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {**entry, "state": "not_started"}, gap(
            "app_not_started", f"{command}: the driver wrote nothing ({ended}): "
                              f"{_tail(_text(back / f'driver-{number}.log'))}")
    state, tail = found.get("state"), found.get("tail") or ""
    if state == "exited":
        why = f"exited with code {found.get('exit')}" if found.get("exit") is not None \
            else f"was ended by {found.get('signal')}"
        return {**entry, "state": "not_started"}, gap(
            "app_not_started", f"{command} {why} before its port answered: {tail}")
    if state == "not_ready":
        where = f"its port {one['port']}" if one["port"] else f"the address it printed ({found.get('port')})"
        return {**entry, "state": "not_started"}, gap(
            "not_ready", f"{command}: {where} did not answer in {READY} s: {tail}")
    if state == "no_address":
        return {**entry, "state": "not_started"}, gap(
            "port_not_declared", f"{command} declares no port and printed no local address in {READY} s, and Daodan "
                                 f"scans no port: {tail}")
    entry.update(state="ready", address=found.get("address"), port=found.get("port"), seconds=found.get("seconds"),
                 stopped=found.get("stopped"))
    gaps = []
    left = found.get("left") or []
    if left:
        gaps += gap("app_not_stopped", f"{command}: {len(left)} outlived the stop: {'; '.join(left)}")
    if explore:
        try:
            explored = json.loads((back / f"explore-{number}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            gaps += gap("explore_failed", f"{command} is up and the exploration wrote nothing: "
                                          f"{found.get('between_error') or _tail(_text(back / f'driver-{number}.log'))}")
        else:
            entry["explored"] = explored["totals"]
            gaps += [{"path": one["declared_in"], **item} for item in explored.get("gaps", [])]
    return entry, gaps


def _examples(project: Path, apps: list[dict]) -> list[tuple[str, str]]:
    """The test values of the apps: every variable of the example `.env` files (`.env.example`, `.env.local.sample`)
    that Git tracks in an app's own folder, as `(\"*\", file)` for `container.run_in_container`. They are what the project
    publishes: no secret (D-291) and nothing of Daodan's own. A `.env` or `.env.development` is not one, and a project
    outside Git has none."""
    import container
    tracked = container.tracked(project)
    folders = {"" if one["root"] == "." else one["root"] for one in apps}
    return [("*", path) for path in sorted(tracked)
            if container.example(posixpath.basename(path)) and posixpath.dirname(path) in folders]


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned apps in one container run over a copy of `project`, read back from `out_dir`:
    `{state, apps, gaps}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed` (the preparation or the
    engine failed: `cause`, `remedy`)."""
    import container
    import node_preparation
    import shutil
    project, out_dir = Path(project).resolve(), Path(out_dir)
    shutil.rmtree(out_dir / Path(OUT).name, ignore_errors=True)  # a former run's outputs are not this one's
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    unrun = list(planned.get("gaps") or ())
    if not planned["apps"]:
        return {"state": "ran", "apps": [], "gaps": unrun}
    dotenv_env = _examples(project, planned["apps"])
    restored = typescript._prepared(project, planned.get("roots") or ())
    restore_lines, shared = node_preparation.options(restored, planned.get("toolchains") or (), ())
    prepare, execute = scripts(planned, restore_lines)
    chains = _chains(planned)
    explore = bool(planned.get("explore"))

    def inputs() -> dict:
        return {f"{IN}/{DRIVER.name}": DRIVER, **({f"{IN}/{EXPLORER.name}": EXPLORER} if explore else {}),
                **{f"{IN}/{name}": preparation.fetched(url, digest, name)
                   for url, digest, name in (preparation.NODE, *chains["files"])}}

    result = container.run_in_container(
        project, ["sh", "-c", execute], image=typescript.IMAGE, out_dir=out_dir, prepare=["sh", "-c", prepare],
        outputs=[OUT], env={**preparation.ENV, "TERM": "dumb", "CI": "true"},
        timeout=len(planned["apps"]) * (BUILD + READY + (EXPLORE if explore else 0) + 300), prepare_timeout=3600,
        memory=MEMORY, engine=engine, inputs=inputs, keep_root=explore, dotenv_env=dotenv_env, **shared,
        registries=tuple(dict.fromkeys([*preparation.NODE_REGISTRIES, *(javascript.BROWSER_HOSTS if explore else ()),
                                        *restored["hosts"], *chains["hosts"]])))
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "apps": [], "gaps": unrun}
    prepared = _text(out_dir / "prepare.log")
    gaps = [*unrun, *chains["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]
    if result["state"] == "failed":
        return {"state": "failed", "cause": result.get("cause") or "the container run failed",
                "remedy": f"see prepare.log and execute.log in {out_dir}", "apps": [], "gaps": gaps}
    marks = _marks(_text(out_dir / "execute.log"))
    back, apps = out_dir / Path(OUT).name, []
    for number, one in enumerate(planned["apps"]):
        entry, own = _outcome(one, number, marks.get((number, "build")), result["state"], back,
                              bool(planned.get("explore")))
        apps.append(entry)
        gaps += own
    return {"state": "ran", "apps": apps, "gaps": gaps}


def record(manifest: Path, planned: dict, out_dir: Path) -> int:
    """Keep the pages the exploration saw beside `manifest` (`observed_entries.write`), for the entries that read them:
    the number of apps kept; none, and no file (a former run's is taken away: it saw another snapshot), where no app
    was explored."""
    import observed_entries
    apps = []
    for number, one in enumerate(planned["apps"]):
        try:
            explored = json.loads((Path(out_dir) / Path(OUT).name / f"explore-{number}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        apps.append({"declared_in": one["declared_in"], "pages": explored["pages"]})
    if apps:
        observed_entries.write(manifest, apps)
    else:
        Path(manifest).with_name(observed_entries.FILE).unlink(missing_ok=True)
    return len(apps)


def explore(manifest: Path, project: Path, record_: dict, digest: str, folder: Path, engine=None, pages: list[dict] = ()) -> dict:
    """The exploration as the step runs it: plan from the pre-map `record_` and the framework rows `pages`, explore in the container, keep the pages
    beside `manifest`. `{state, apps, gaps, kept}` as `observe` has them (`cause` and `remedy` where it did not run), and
    `reused` where the run of the same snapshot (`digest`, the store's), plan and driver is in `folder`: its gaps come
    back, nothing runs. Only a run that ended `ran` is kept for reuse."""
    import hashlib
    planned = plan(record_, explore=True, pages=pages)
    cache = Path(folder) / "explore.json"
    drivers = hashlib.sha256()
    for path in (Path(__file__), DRIVER, EXPLORER):
        drivers.update(hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).digest())
    key = hashlib.sha256(json.dumps([digest, planned, drivers.hexdigest()], sort_keys=True).encode()).hexdigest()
    try:
        kept = json.loads(cache.read_text(encoding="utf-8"))
        if kept["key"] == key and planned["apps"]:
            return {**kept["result"], "reused": True}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    cache.unlink(missing_ok=True)
    seen = observe(project, planned, folder, engine)
    seen["kept"] = record(manifest, planned, folder)
    if seen["state"] == "ran" and planned["apps"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"key": key, "result": seen}), encoding="utf-8")
    return seen
