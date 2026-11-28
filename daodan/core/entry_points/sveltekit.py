"""Source: the files SvelteKit's own `svelte-kit sync` lists for each route, run in Daodan's container.

`commands` describes, in each folder whose `package.json` declares `@sveltejs/kit`, the project's own `svelte-kit sync` (`npx
--no-install`: the runner's setup restores the project's packages first, `container_runner.TOOLS`, and installs nothing else;
`npm_config_offline` makes a command that is not installed fail at once with npm's own words and not after its retries,
measured 0.6 s against 70.6 s, `benchmarks/sveltekit-routes/`) under `timeout` (the folders share `SYNC_TOTAL` seconds, and the
cause of 124 and 137 is the gap's) and the print of `.svelte-kit/types/route_meta_data.json`. The command loads `svelte.config.js`
and `vite.config.ts`, which is code of the project, so it runs only there, and it writes `.svelte-kit/` (58 files on the benchmark's
fixture) into the container's copy.

`read` reads that JSON, `{route id: [file, ...]}` (the files the route's types are generated from: the `+page`, `+page.server`
and `+server` modules of the route and the `+layout` and `+layout.server` modules of every layout above it, so each route lists
its ancestors' too). A file is one row, owned by the route with the fewest segments that lists it (a layout is listed by its
own route and by the routes below it, which have more); the route is the tool's id, as it writes it (`/(shop)/cart`,
`/blog/[slug]`, `/docs/[...rest]`): the group is in it and the tool gives no URL for it. The path of each file is the tool's,
relative to the project, so `kit.files.routes` needs no reading. The role of a file is its name as the tool prints it (`+server`,
`+page.server`, ...): `QUERIES["sveltekit"]` says which exports of each the framework calls (`GET` and the other methods of a
`+server`, `load` of a page, `actions` of a `+page.server`) and which starts nothing (a layout). The tool names no export, line or
method, and no `+page.svelte`: the row is the module with the exports its table names, and the links' binder (`binder.bind`) ties them
to the functions the snapshot's export records name, and a
route with no module in the list (a page with only a component) has no row: React Router's `default` export is the component of
a route and an entry there, but here the component is not a module with functions that the tool names. An export that no function of
the snapshot is bound to, which the binder says (`actions` is an object: its members are anonymous functions of the snapshot, and so is `GET = make('get')`
and a re-export), a file the snapshot does not hold, a failed command and a file that is not the layout this reader knows are gaps
with their cause, never a guess. The rows are entries, not offered routes: the tool gives no HTTP method (the links tell each as a
declared route with no method); the route's `schema` (`_schema`) makes Noir's route on the same file and path that row
(`flows.link_facts`).

Evaluated and not used: `$types.d.ts` (the id and, by its type names, the kinds a directory has, but no file name and no
`+server` method), `non-ambient.d.ts` (`RouteId()` lists the folders that hold no route too: `/api`, `/components`) and
`generated/client/app.js` with `nodes/N.js` (the `+page.svelte` and `+page` of a page, by node, and nothing of an endpoint or a
`+page.server`). `route_meta_data.json` is not the documented output of the command (svelte.dev/docs/kit/cli promises
`tsconfig.json` and the types): it is the cache the tool keeps to regenerate only the routes whose files changed, and the same
JSON came from SvelteKit 2.0.0, 2.15.0, 2.40.0 and 2.70.4, the ones measured (the limit is told at `META`).
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

from entry_points import frameworks

NAME, VERSION, RANK = "sveltekit", "daodan/premap/v3", "scanner"  # v3: the route's `schema`
PACKAGE = "@sveltejs/kit"
ENV = {"npm_config_offline": "true"}
# shortcut: the file is the tool's own cache, not the output the documentation promises (the types and `tsconfig.json`), and it is
# read where the tool writes it by default; a SvelteKit that changes its form is a gap saying so ("no JSON of the known layout") and
# one that sets `kit.outDir` (in `svelte.config.js`, code that only the container runs) is a gap with the tool's own words; when one is
# met, read the option from the generated `tsconfig.json`, whose `extends` the tool prints, or take the types the tool documents
META = ".svelte-kit/types/route_meta_data.json"
SYNC_TOTAL = 900  # seconds `svelte-kit sync` may take in all the folders together: a run lasts 1800, the restore of the packages in it
# measured: `svelte-kit sync` took 1.0-2.4 s on the fixture (`benchmarks/sveltekit-routes/README.md`); the memory is Next.js's, 3 GB
# (`container_runner.TOOLS`, a test keeps the two equal): a project with many routes may need more, and it is not measured
MEMORY_GB = 3


def sync_seconds(folders: int) -> int:
    """The time `svelte-kit sync` has in each of `folders` folders: they share `SYNC_TOTAL`, so a project that takes its time does
    not take the rows of the others."""
    # shortcut: a project of more than 90 folders asks for more than SYNC_TOTAL, 10 seconds each at the least; when one is met, raise it
    return max(10, SYNC_TOTAL // folders)


def commands(context):
    folders = frameworks.folders(context, ("@sveltejs/kit",))
    if not folders:
        return None
    sync = ["timeout", "--kill-after=10", str(sync_seconds(len(folders))), "npx", "--no-install", "svelte-kit", "sync"]
    return [{"tool": NAME, "argv": argv, "cwd": folder, "env": env, "network": "none"}
            for folder in folders for argv, env in ((sync, ENV), (["cat", META], {}))]


def _failed(command: dict, result: dict) -> str:
    """Why `svelte-kit sync` did not end well, in the words of the tool: the cause it wrote first, or the limit that ended it."""
    seconds = command["argv"][2]
    if result["returncode"] == 124:  # `timeout` ended the command
        return f"svelte-kit sync did not end in {seconds} seconds"
    if result["returncode"] == 137:  # `timeout` had to kill it, or the memory of the run did: the signal does not say which
        return f"svelte-kit sync was killed (exit 137): it did not end in {seconds} seconds, or it ran out of memory ({MEMORY_GB} GB)"
    return f"svelte-kit sync exited with {result['returncode']}: {frameworks.excerpt(result)}"


def _files(listed) -> dict[str, str]:
    """`{file: route id}` of the JSON the tool wrote: each file owned by the route with the fewest segments that lists it (the
    first of them by id when two have as many). Raises ValueError for a JSON that is not the known layout: an object of lists
    of file names."""
    if not isinstance(listed, dict) or not all(isinstance(files, list) and all(isinstance(f, str) for f in files)
                                               for files in listed.values()):
        raise ValueError("not an object of lists of files")
    owner: dict[str, str] = {}
    for route in sorted(listed, key=lambda r: (len([s for s in r.split("/") if s]), r)):
        for file in listed[route]:
            owner.setdefault(file, route)
    return owner


def _schema(route: str) -> str | None:
    """The route id as `REST` reads a path (`flows.path_schema`: `[id]` and `[id=matcher]` are `{}`), or None for an id that stands
    for no single schema: a rest (`[...rest]`), an optional segment (`[[opt]]`) or a group (`(shop)`). No file `svelte-kit sync`
    writes ties an id to its URL (`Pathname()` of `non-ambient.d.ts` is a union with no id, `benchmarks/sveltekit-routes/README.md`),
    so a group is not taken out by a rule of ours: its route has no schema. The segments are read as the framework writes them: a
    text with no grammar, read with string operations, as `nextjs._next_path` does."""
    # shortcut: a route under a group has no schema, so Noir's `/cart` and the row of `/(shop)/cart` stay two, when a SvelteKit writes each id's URL: read it there
    # shortcut: an escaped character (`[x+2f]`) reads as a parameter, when a project uses one
    import flows
    if any(s.startswith("(") and s.endswith(")") or "[..." in s or "[[" in s for s in route.split("/")):
        return None
    return flows.path_schema(route.replace("[", "{").replace("]", "}"))


def read(context, commands, results):
    import entries
    import flows
    table = entries.QUERIES[NAME]
    gaps, files = [], []  # the files to bind: (route id, file)
    for command, sync, printed in zip(commands[::2], results[::2], results[1::2]):
        folder = command["cwd"]
        if sync["returncode"] != 0:  # the file the second command printed may be one an earlier run left: not read
            gaps.append({"kind": "model_failed", "path": folder, "detail": _failed(command, sync)})
            continue
        if printed["returncode"] != 0:
            said = frameworks.excerpt({"stdout": "", "stderr": sync["stderr"]})
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"svelte-kit sync exited with 0 and wrote no {META}: its outDir is not .svelte-kit, or this SvelteKit "
                                   f"writes none (the four measured, 2.0.0 to 2.70.4, do){f'; it said: {said}' if said else ''}"})
            continue
        try:
            owner = _files(json.loads(printed["stdout"]))
        except ValueError as error:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{META} is no JSON of the known layout ({error}): {frameworks.excerpt(printed)}"})
            continue
        for file, route in sorted(owner.items(), key=lambda item: (item[1], item[0])):
            path = posixpath.normpath(posixpath.join(folder, file))
            if path in context.inventory.headers:
                files.append((route, path))
            else:
                gaps.append({"kind": "outside_snapshot", "path": path,
                             "detail": f"svelte-kit sync lists {path} for {route}, and the snapshot holds no file with that path"})
    rows = []
    if files:
        for route, file in files:
            shape = PurePosixPath(file).stem  # `+page.server.ts` -> `+page.server`, as the tool names the role
            spec = table.get(shape)
            base = {"reader": NAME, "shape": shape, "path": route, "schema": _schema(route)}
            module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
            if spec is None:  # a file name this table does not know: a shape to classify, and no export to start from
                rows.append({**module, "gap": f"{file}: {NAME} lists a file named {shape}, which this reader has no exports for"})
                continue
            base["kind"] = module["kind"] = spec["kind"]
            names = spec.get("exports")
            # shortcut: the `load` of a layout runs for every page under it, and it is no row of its own: the layouts are "nessun
            # ingresso" (React Router's root and layouts with no path have a row for their `loader`: `read` there); when the owner wants it an entry, give `+layout` and `+layout.server` the exports
            if not names:  # a layout starts no flow of its own
                rows.append(module)
                continue
            # shortcut: an export is a function of the snapshot only where the snapshot says so: `actions` (an object whose members
            # are anonymous functions), `load = (async () => ...) satisfies PageServerLoad` (a documented form: the arrow is under the
            # `satisfies`), `GET = make('get')` and a re-export are rows with the snapshot's own cause; when one is met, bind them
            # from the type-checker's answer for the member or the wrapped function, which no tool of SvelteKit gives
            rows.append({**module, "exports": names})  # the links bind them (`binder`)
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in the record of the entry points and its gaps there; a record made without the source, or where it was not
    needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
