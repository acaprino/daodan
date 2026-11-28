"""Starting the app the project declares, in the container (plan task 11.2; spec of the project's interfaces, 7.1-7.3).

`plan` reads the pre-map's `starts` and `builds` (`premap/npm_start.py`, and the commands of the user and the
assistant, `commands`): per module the `start` script, else the `dev` one; the module's `build` first where the start
reads compiled output (`needs_build`). The command is the declared one, its words (`argv`, `<runner> run <script>` for
a script), never changed; its environment is the container's, plus the variables of the example `.env` files the
project publishes and Git tracks in the app's folder (`_examples`): the test values the app asks for. Its runner, the
command's program, has its preparation (`_unprepared`): Node's own programs come with Daodan's Node, pnpm and Yarn
with corepack as the restores run them (`preparation.RESTORES`' `before`), its shims on the path and the manager the
folder names fetched while the preparation has the network, and Bun with mise at the version the pre-map states
(`preparation.toolchains`), never one mise would pick. Where the project declares none, or a start needs a build
nobody declares, or a runner has no preparation (`start_runner_not_supported`), nothing runs and the gap says why.

A start runs on its surface (`registry_build.SURFACES`): the one it states (a command of the user or the assistant,
`commands`), else `web`, the address it opens. Only the `ACTIVE` ones run (spec «Superfici attive»): a start on
another does not start, and a module whose technologies have another (the `surface` of their registry entries, read
when the plan is made) is not explored where no start of its folder runs on an active one. Both are the gap
`ui_execution_deferred:<surface>`, the module's with the technology and the file that declares it
(`technology_evidence`); the modules are the physical ones of the stack record (`technologies.derive`).

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
ACTIVE = ("web", "webview")  # the surfaces the exploration runs (spec «Superfici attive»); the others wait
WEB = "web"  # the surface of a start that states none: the HTTP address it opens
DEFERRED = "ui_execution_deferred"  # the gap of a surface not run yet: `<DEFERRED>:<surface>`
REMEDY = ("where the project also starts the folder on web or webview, set that command for the folder in the app: it "
          "runs instead")
TOOLCHAINS = ("node", "bun")  # the stated toolchains the preparation installs (`preparation.toolchains`, mise)
NODE_PROGRAMS = ("node", "npm", "npx")  # the programs of Daodan's Node (`preparation.NODE`, its `bin`)
COREPACK = tuple(manager for manager, spec in preparation.RESTORES.items()  # pnpm and Yarn, as their restores
                 if spec.get("before") == preparation.COREPACK)
MISE = ("bun",)  # the runners mise installs at the version the pre-map states: none of Daodan's own


def chosen(record: dict) -> dict[str, dict]:
    """The start the exploration runs in each folder of the `starts` of `record`: the user's command, then the
    assistant's (`commands.merged`), then the project's (`dynamic.rank`); `start` before `dev`."""
    from dynamic import rank
    found: dict[str, dict] = {}
    for entry in sorted(record.get("starts", []), key=lambda entry: (rank(entry), entry["mode"] != "start")):
        found.setdefault(entry["root"], entry)
    return found


def _unprepared(entry: dict, toolchains: list[dict]) -> str | None:
    """Why the runner of a start or a build (its program) has no preparation here (see the module's docstring), None
    where it has one; `toolchains` the stated ones the preparation installs."""
    runner = entry["runner"]
    if runner in NODE_PROGRAMS or runner in COREPACK:
        return None
    if runner in MISE:
        if any(item.get("tool") == runner and preparation.EXACT.match(str(item.get("version") or ""))
               for item in toolchains):
            return None
        return (f"mise installs {runner} at the version the project states, and the pre-map states no exact {runner} "
                "version (a version file, `packageManager` or `engines`, as Renovate reads them)")
    return "the exploration has no preparation for it"


def plan(record: dict, explore: bool = False, seeds: tuple[str, ...] = (), pages: list[dict] = (),
         units: list[dict] = ()) -> dict:
    """`{apps, gaps, roots, toolchains, explore, seeds}` from the pre-map `record`: see the module's docstring. An app
    is the `starts` entry chosen for a module (`chosen`), with its `build` entry where it needs one; `seeds` are routes
    (paths) the exploration opens besides the app's root; `pages`, the framework rows of the entry points
    (`entry_points`), give each app the pages it opens too; `units`, the physical modules of the stack record
    (`technologies.derive`), the technologies whose surface may not be run yet."""
    import premap
    from dynamic import rank  # the user's command, then the assistant's (`commands.merged`), then the project's
    builds: dict[str, dict] = {}
    for entry in sorted(record.get("builds", []), key=rank):
        builds.setdefault(entry["root"], entry)
    starts = chosen(record)
    toolchains = [item for item in record.get("toolchains", []) if item.get("tool") in TOOLCHAINS]
    apps, gaps = [], []
    for root, entry in sorted(starts.items()):
        surface = entry.get("surface") or WEB
        build = builds.get(root) if entry["needs_build"] else None
        unprepared = [(one, why) for one in (entry, build) if one for why in [_unprepared(one, toolchains)] if why]
        if surface not in ACTIVE:
            gaps.append({"kind": f"{DEFERRED}:{surface}", "root": root, "path": entry["declared_in"],
                         "detail": f"{entry['declared_in']} starts {root} on the {surface} surface, which the "
                                   "exploration does not run yet: the app is not started", "remedy": REMEDY})
        elif unprepared:
            gaps += [{"kind": "start_runner_not_supported", "path": one["declared_in"], "runner": one["runner"],
                      "detail": f"{one['declared_in']} runs with {one['runner']}: {why}: the app is not started"}
                     for one, why in unprepared]
        elif entry["needs_build"] and build is None:
            gaps.extend({key: value for key, value in gap.items() if key != "source"}
                        for gap in record.get("gaps", [])
                        if gap.get("kind") == "build_command_missing" and gap.get("path") == _manifest(entry))
        else:
            apps.append({**entry, **({"build": build} if build else {}), "seeds": _pages(pages, root)})
    if not record.get("starts"):
        gaps.append({"kind": "no_start_command", "detail": "no package.json of the project declares a start or dev "
                                                           "script that starts an app: nothing is explored"})
    gaps += [{key: value for key, value in gap.items() if key != "source"} for gap in record.get("gaps", [])
             if gap.get("kind") == "no_start_command"]
    started = {posixpath.normpath(root or ".") for root, entry in starts.items()
               if (entry.get("surface") or WEB) in ACTIVE}
    gaps += _deferred(units, started)
    return {"apps": apps, "gaps": gaps,
            "roots": sorted(premap.roots(record, typescript.UNIT_KINDS, typescript.WORKSPACES)),
            "toolchains": toolchains, "explore": explore, "seeds": list(seeds)}


def _surfaces() -> dict[str, str]:
    """The surface of each technology whose registry entry decides one (`registry_build.SURFACES`), read from the
    registry."""
    import service_registry
    return {entry["id"]: entry["surface"] for entry in service_registry.load()["entries"] if entry.get("surface")}


def _deferred(units: list[dict], started: set[str]) -> list[dict]:
    """The gap of each technology of a module of `units` whose surface is not `ACTIVE`, where no start of the module's
    folder runs on an active one (`started`): with the module, the technology and the file that declares it."""
    surfaces = _surfaces() if units else {}
    gaps = []
    for unit in units:
        root = posixpath.normpath((unit.get("paths") or ["."])[0])  # a physical module is one folder (`module_derive`)
        if root in started:
            continue
        for ident in unit.get("technologies") or ():
            surface = surfaces.get(ident)
            if surface is None or surface in ACTIVE:
                continue
            site = (unit.get("technology_evidence") or {}).get(ident) or {}
            where = f"in {site['path']}" if site.get("path") else "in its files"
            gaps.append({"kind": f"{DEFERRED}:{surface}", "root": root, "module": unit.get("id"), "technology": ident,
                         **{key: site[key] for key in ("path", "line") if site.get(key)},
                         "detail": f"the module {unit.get('name') or root} declares {ident} {where}, whose surface, "
                                   f"{surface}, the exploration does not run yet, and nothing starts {root} on "
                                   f"{' or '.join(ACTIVE)}: its interface is not explored", "remedy": REMEDY})
    return gaps


def _pages(rows: list[dict], root: str) -> list[str]:
    """The pages the sources declare (the rows marked `page`) in the app's folder, as the paths the exploration opens besides `/`;
    a pattern (a `schema` with a `{}`) or a route with no single schema is not a page to open, and an endpoint is not a page."""
    return sorted({row["path"] for row in rows if row.get("page")
                   and isinstance(row.get("schema"), str) and "{}" not in row["schema"]
                   and (root == "." or row["site"].startswith(f"{root}/"))})


def _manifest(entry: dict) -> str:
    return entry["declared_in"].partition("#")[0]


def _command(entry: dict) -> str:
    """The command's words (`argv`) as one shell line: joined, never split."""
    return shlex.join(entry["argv"])


def _chains(planned: dict) -> dict:
    return preparation.toolchains([item for item in planned.get("toolchains") or ()
                                   if preparation.EXACT.match(str(item.get("version") or ""))])


def _folder(root: str) -> str:
    return shlex.quote(posixpath.normpath(posixpath.join("/work", root)))


def _managers(planned: dict) -> list[tuple[str, str]]:
    """`(root, manager)` for each start and build of the planned apps that corepack runs (`COREPACK`), in order."""
    return list(dict.fromkeys((one["root"], run["runner"]) for one in planned["apps"]
                              for run in (one, one.get("build")) if run and run["runner"] in COREPACK))


def scripts(planned: dict, restores: list[str]) -> tuple[str, str]:
    """The preparation's script and the execution's: `restores` are the lines of the project's own restore."""
    chains = _chains(planned)
    explore = bool(planned.get("explore"))
    managers = _managers(planned)
    # pnpm and Yarn as the restores run them (`preparation.COREPACK_INSTALL`), with corepack's own shims on the path
    # (`corepack enable`) so the declared words run as written, and each folder's manager (its `packageManager`, else
    # corepack's default) fetched while the preparation has the network: the execution has none
    corepack = [f"{{ {preparation.COREPACK_INSTALL}; {preparation.COREPACK};"
                f" corepack enable --install-directory {T}/bin {' '.join(sorted({m for _, m in managers}))} ; }} >&2",
                *(f"( cd {_folder(root)} && {manager} --version ) >&2" for root, manager in managers)] \
        if managers else []
    # the browser, as the observer prepares Playwright's (`javascript.scripts`): apt over HTTPS, the headless shell
    browser = [f"{{ npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error"
               f" playwright-core@{PLAYWRIGHT} ; }} >&2",
               'for f in /etc/apt/sources.list /etc/apt/sources.list.d/ubuntu.sources; do',
               '  if [ -f "$f" ]; then sed -i "s|http://|https://|g" "$f"; fi', 'done',
               f"node {T}/npm/lib/node_modules/playwright-core/cli.js install --with-deps --only-shell chromium >&2"]
    prepare = ["set -u", f'mkdir -p {T}/bin "$HOME"', *preparation.setup(["node"])["lines"], *chains["lines"],
               *(browser if explore else []), "cd /work || exit 70", *restores, *corepack]
    execute = ["set -u", f"mkdir -p {OUT}", *([preparation.COREPACK] if managers else []),
               *([f"export DAODAN_PLAYWRIGHT={T}/npm/lib/node_modules/playwright-core"] if explore else [])]
    for number, one in enumerate(planned["apps"]):
        folder = _folder(one["root"])
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
    engine failed: `cause`, `remedy`). A host the proxy refused that the user has yet to answer (the browser's, mise's
    downloads: `egress`) is the `approval_required` gap, whatever the run's end."""
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
                                        *restored["hosts"], *chains["hosts"],
                                        *(host for _, manager in _managers(planned)
                                          for host in preparation.RESTORES[manager]["hosts"])])))
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "apps": [], "gaps": unrun}
    prepared = _text(out_dir / "prepare.log")
    gaps = [*unrun, *chains["gaps"], *preparation.missing(prepared), *preparation.restore_gaps(prepared),
            *(result.get("gaps") or ())]
    if result.get("asked") and not any(gap.get("kind") == "approval_required" for gap in gaps):
        import egress  # a preparation that went on past a refusal: the hosts the user has yet to answer are the cause
        gaps += egress.approval_gap(result["asked"], "ran")
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
    back, nothing runs. Only a run that ended `ran` is kept for reuse, and not one that asked for hosts the user has yet
    to answer (`approval_required`): after the answer, the next analysis runs again."""
    import hashlib
    import technologies
    planned = plan(record_, explore=True, pages=pages, units=technologies.recorded(manifest).get("units") or ())
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
    if seen["state"] == "ran" and planned["apps"] and not any(gap.get("kind") == "approval_required"
                                                              for gap in seen["gaps"]):
        Path(folder).mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"key": key, "result": seen}), encoding="utf-8")
    return seen
