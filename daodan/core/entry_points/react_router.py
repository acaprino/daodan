"""Source: the routes React Router and Remix print themselves, `react-router routes --json` and `remix routes --json`, run in
Daodan's container.

`commands` describes, in each folder whose `package.json` declares `@react-router/dev` or `@remix-run/dev` (the package that
installs the command: a project that declares only `react-router` or `react-router-dom` is the library, whose routes are
written in code and which has no command that lists them), the project's own command (`npx --no-install`: the runner's setup
restores the project's packages first, `container_runner.TOOLS`, and installs nothing else). The command loads the project's
`routes.ts`, `react-router.config.ts`, `remix.config.js` and `vite.config.ts`, which is code of the project, so it runs only
there; `npm_config_offline` makes a command that is not installed fail at once with npm's own words and not after its
retries (measured: 0.6 s against 70.7 s, `benchmarks/react-router-routes/`).

`read` reads the tree the command prints on its standard output: each route has an `id`, its `path` (none for a layout or an
index), `index`, and its `file`, relative to the app directory, which the tool does not name: this reader takes the default one
(`app`), and where none of the files is there it says so in one gap, naming the cause. (`react-router typegen` names the app
directory in the paths of the files it writes: evaluated and not used, it is a second command that writes 20 files in the
project, and Remix 2 has none; `benchmarks/react-router-routes/README.md`.) It does not give the exports of the
route module (a component, a `loader`, an `action`), nor whether it is a page or a resource route: the row is the module and
carries the exports its table names (`QUERIES["react-router"]`, the ones a route starts), and the links' binder (`binder.bind`) ties
them to the functions the snapshot's own export records name. A route whose file the snapshot does not hold and a command that
failed are gaps with their cause, never a guess (an export no function is bound to is the binder's gap, a re-export for one; an anonymous default, `export default function () {}`, is a known limit: the snapshot keeps no `default` export record for it, so it reads as `export-missing`, which is no reason, and the module has a gap only when none of its other exports is found). The rows are
entries, not offered routes: the tool gives no HTTP method.
"""
from __future__ import annotations

import json
import posixpath

from entry_points import frameworks

NAME, VERSION, RANK = "react-router", "daodan/premap/v4", "scanner"  # v4: the module row with its `exports`, bound by the links; v3: the data functions of the root and of a layout with no path; v2: an absolute child, the root under `app/`, `timeout`
CLI = {"@react-router/dev": "react-router", "@remix-run/dev": "remix"}  # the package that installs the command -> the command
LIBRARY = ("react-router", "react-router-dom")  # the library: routes written in code, which no command lists
APP = "app"  # the app directory the tool prints its files against, by default
ENV = {"npm_config_offline": "true"}
TOTAL, EACH = 900, 300  # seconds the command may take in all the folders together, and in one: it loads the project's config, 1.1 to 1.7
# seconds measured (`benchmarks/react-router-routes/`), and a config that waits for what never comes would keep the run's 1800 seconds
ENDED = (124, 137)  # `timeout`'s own codes: it ended the command, or had to kill it


def seconds(folders: int) -> int:
    """The time the command has in each of `folders` folders: they share `TOTAL`, up to `EACH`, so folders that all hang do not
    take the whole run."""
    # shortcut: more than 90 folders ask for more than TOTAL, 10 seconds each at the least, when one is met: raise TOTAL
    return min(EACH, max(10, TOTAL // folders))


def commands(context):
    """`(folder, command)` for each folder whose `package.json` declares a package of `CLI`; one that is not valid JSON is
    skipped: `npm-files` reports it."""
    # shortcut: the command runs in each folder whose package.json declares the dev package, and in a workspace that is the root, where
    # the dev package may be hoisted and the app is a folder below (the run then fails with the tool's own "Route config file not
    # found" and is a gap), when a monorepo declares @react-router/dev in its root: take the folders that hold an app/routes.ts
    found = []
    for folder in frameworks.folders(context, tuple(CLI)):  # in the inventory's order, then the CLI's, as the manifest was read
        found += [(folder, command) for package, command in CLI.items() if folder in frameworks.folders(context, (package,))]
    limit = ["timeout", "--kill-after=10", str(seconds(len(found) or 1))]
    return [{"tool": NAME, "argv": [*limit, "npx", "--no-install", command, "routes", "--json"], "cwd": folder, "env": ENV,
             "network": "none"} for folder, command in found] or None


def _routes(tree, parents=(), top=True) -> list[dict]:
    """The routes of the tree the tool prints, each `{file, path, index, ...}` with its full `path` (the path of its ancestors
    and its own, `/` for none; a path of its own that begins with a slash is the whole path, as React Router reads it: `users` >
    `/users/:id` is `/users/:id`, and so is what is under it). Raises ValueError for a tree that is not the known layout: a list
    of routes with a `file`."""
    if not isinstance(tree, list):
        raise ValueError("not a list of routes")
    found = []
    for node in tree:
        if not isinstance(node, dict) or not isinstance(node.get("file"), str):
            raise ValueError("a route with no file")
        own = node.get("path") or ""
        # shortcut: an absolute child is taken as written, though React Router calls one that does not begin with its parent's path
        # invalid and the tool prints it without a word (`other` > `/elsewhere` is `/elsewhere`), when a project does it: check the prefix
        # shortcut: the path is the tool's, with no `basename` of react-router.config.ts, when a consumer uses the path as a URL: no
        # official tool gives the value cheaply (@react-router/dev 7.18.6, read): `routes` prints only `config.routes` (and printed none
        # measured with `basename: "/base/"`), `./config` exports types, `typegen` writes the type of `basename` and not its value; the value
        # is in the `virtual:react-router/server-build` module of a Vite build or dev server; reading the config file is a hand-written
        # reader of code that can compute it (`process.env`, a preset): then take it from that module
        segments = [*([] if own.startswith("/") else parents), own.strip("/")]
        found.append({"file": node["file"], "own": own, "index": bool(node.get("index")), "root": top and not found,
                      "path": "/" + "/".join(s for s in segments if s)})
        found += _routes(node.get("children") or [], segments, False)
    return found


def read(context, commands, results):
    import entries
    import flows
    table = entries.QUERIES[NAME]
    gaps, routes = [], []  # the routes to bind: (route, file)
    for command, result in zip(commands, results):
        folder, tool = command["cwd"], f"{command['argv'][-3]} routes --json"
        if result["returncode"] in ENDED:
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"{tool} did not end in {command['argv'][2]} seconds (exit {result['returncode']}): "
                                                                           f"its config waits for something, or does not stop"})
            continue
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"{tool} exited with {result['returncode']}: {frameworks.excerpt(result)}"})
            continue
        try:
            # shortcut: the standard output is read as one JSON text, so a line the project's config prints to it makes the whole folder a gap
            # (model_failed, with the output), when a config logs to the standard output: read the last JSON document of it
            tree = _routes(json.loads(result["stdout"]))
        except ValueError as error:
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"{tool} printed no JSON of the known layout ({error}): {frameworks.excerpt(result)}"})
            continue
        if not tree:
            gaps.append({"kind": "model_partial", "path": folder, "detail": f"{tool} printed no route"})
            continue
        files = {route["file"]: posixpath.normpath(posixpath.join(folder, APP, route["file"])) for route in tree}
        held = {file for file in files.values() if file in context.inventory.headers}
        # The tool prints the root route first, and its file is the proof of the directory: where it is not under the default one, the
        # files that happen to be there are not the routes' own.
        # shortcut: the app directory is `app` when the root route's file is there, so a project with another `appDirectory` that also
        # holds that file under `app/` (a second app, a leftover) binds the files of both without a gap, when a project does it:
        # `react-router typegen` names the directory in the paths it writes (measured), read them instead of guessing
        root = files[tree[0]["file"]]
        if root not in held:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"{tool} prints each file relative to the app directory and does not name it; the root route's file "
                                   f"({tree[0]['file']}) is not at {root}: this reader takes the default app directory ({APP}), and the "
                                   f"project may set another one (`appDirectory`)"})
            continue
        for file in sorted({file for file in files.values() if file not in held}):
            named = [route["path"] for route in tree if files[route["file"]] == file]
            gaps.append({"kind": "outside_snapshot", "path": file,
                         "detail": f"{tool} names {file} for {', '.join(named)}, and the snapshot holds no file with that path"})
        routes += [(route, files[route["file"]]) for route in tree if files[route["file"]] in held]
    rows = []
    if routes:
        for route, file in routes:
            shape = "index" if route["index"] else "route" if route["own"] else "layout"
            base = {"reader": NAME, "shape": shape, "kind": table[shape]["kind"], "path": route["path"]}
            module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
            data = shape == "layout"
            if data:  # the module row stays; the functions the framework calls on a request are rows of their own shape
                # The root and a layout with no path run their `loader` for each request of a page under them (their `path` is the
                # prefix they run under). Only the root's `action` is ever called: `getTargetMatch` takes the last match that
                # contributes a path, the first match always does and a layout with no path never does (read in react-router
                # 7.18.6, not run); a layout with a path is a route and is read as one.
                # shortcut: read from react-router's own source (`getTargetMatch`, `getPathContributingMatches`, `queryRoute`) and not
                # run on an app, and not read in Remix's `@remix-run/router`, when a run can serve the fixture on Modal: ask `/` and a
                # page for each, and the `middleware` export (`future.v8_middleware`), which runs on each request, is not read
                rows.append(module)
                shape = "root-data" if route["root"] else "layout-data"
                base = {**base, "shape": shape, "kind": table[shape]["kind"]}
                module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
            # the links bind the exports (`binder`); a layout with no data function is normal
            rows.append({**module, "exports": table[shape]["exports"], **({"exports_optional": True} if data else {})})
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def stated_gaps(premap_record) -> list[dict]:
    """A gap for each `package.json` that declares the library and none of the packages that install a command (`CLI`): its routes
    are written in code and no official tool lists them. Told from the dependencies the pre-map already holds
    (`packages`, read from each manifest), so it needs no command and no container: `flow_entries.evidence` tells it beside the
    source's own gaps."""
    source = f"{NAME}@{VERSION}"
    # shortcut: a package of UI components in a monorepo that declares react-router(-dom) is told as a project whose routes are written in
    # code, though it has none, when a monorepo has such packages: tell only a manifest whose folder has a start or a build (`npm-start`)
    declared = {}
    for package in premap_record.get("packages", ()):
        file = package["declared_in"].partition("#")[0]
        if package["ecosystem"] == "npm" and file.rpartition("/")[2] == "package.json":
            declared.setdefault(file, set()).add(package["name"])
    return [{"kind": "model_partial", "path": file, "source": source,
             "detail": f"{file} declares {', '.join(sorted(names.intersection(LIBRARY)))} and none of {', '.join(CLI)}: routes written in code "
                       "(createBrowserRouter, <Routes>), no official tool lists them: declare @react-router/dev or read them by running "
                       "the app (exploration)"}
            for file, names in sorted(declared.items()) if names.intersection(LIBRARY) and not names.intersection(CLI)]


def from_record(report):
    """The rows this source persisted in the record of the entry points and its gaps there; a record made without the source, or
    where it was not needed, has no rows. The library's gaps are the pre-map's (`stated_gaps`)."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
