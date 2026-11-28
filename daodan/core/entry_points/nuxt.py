"""Source: the routes of a Nuxt project, from Nuxt's own tools run in Daodan's container: the server routes Nitro writes with
`nuxt prepare`, and the pages its own `@nuxt/kit` resolves.

`commands` describes, in each folder whose `package.json` declares `nuxt`, three commands: the project's own `nuxt prepare`
(`npx --no-install`: the runner's setup restores the project's packages first, `container_runner.TOOLS`, and installs nothing
else), the print of `.nuxt/types/nitro-routes.d.ts`, and, after the commands of all the folders, Daodan's script
(`nuxt_pages.mjs`, run as `daodan-nuxt` under `timeout`), which calls `loadNuxt` and `buildNuxt` of the `@nuxt/kit` the project
installed and prints the routes Nuxt resolves from its pages, each with the file it is made from. They load `nuxt.config.ts`, its
modules and its layers, which is code of the project, so they run only there; `npm_config_offline` makes a command that is not
installed fail at once with npm's own words (measured: 0.45 s against 70.6 s, `benchmarks/nuxt-routes/`).

The server routes: the file ties each route (`server/api`, `server/routes`, and the `nitro.handlers` of the config, which are
code) to its HTTP method and to the import of its handler's file, in Nuxt 3 and Nuxt 4 alike; `read` reads it from its syntax tree
(`nitro_routes`) and ties each import to the one script of the snapshot with that path, without its extension. The
default export of the handler file is the function a route starts (`QUERIES["nuxt"]`, as for React Router): the row is the handler
file with that `exports`, and the links' binder (`binder.bind`) ties it to the function: a default-exported function declaration binds,
and the usual `export default defineEventHandler(...)` is a call, which the snapshot's export records do not bind: the gap is the binder's.

The pages: no file `nuxt prepare` writes by default names them, but `loadNuxt` does: Nuxt calls the hook `pages:resolved` with the
routes it has made of the pages, after the project's own `pages:extend` hooks, its modules and its layers, each with its `path`
(relative to its parent for a child, as vue-router reads it) and its `file`. A page is a row of the shape `page` on its file, with
the whole path composed from its ancestors and no line (the tool gives none): the file is the entry, as a Next.js page is. A route
with no file (a redirect), a file the snapshot does not hold (a layer outside the project) and an app that never reaches the hook
(no pages folder) are gaps; a script that failed (the config throws, `@nuxt/kit` is missing, a route whose file is gone) is a gap
with the cause it wrote, and the server routes are still read. Each row carries its route's `schema` (`_route_schema`,
`_page_schema`): a server route with a method of its own is an offered route, and Noir's route on the same file and path is that
row (`flows.link_facts`); a page answers any method, as a Next.js page does.

Nuxt's own two routes (`/__nuxt_error`, `/__nuxt_island/**`) name a package's file and a virtual module, so they are the second
kind of gap in every project.
"""
from __future__ import annotations

import json
import posixpath

from entry_points import frameworks

NAME, VERSION, RANK = "nuxt", "daodan/premap/v3", "scanner"  # v3: the route's `schema`, a page is `page`
PACKAGES = ("nuxt",)  # the package a folder's `package.json` declares: the source runs there
SCRIPTS = ("typescript", "javascript")  # the snapshot's languages of the files a handler import names, written with no extension
TYPES = ".nuxt/types"
# shortcut: the file is read where Nuxt writes it by default; a project that sets `buildDir` is a gap saying so (measured: `build-dir`
# of `benchmarks/nuxt-routes/`, where the command wrote the same files under the other folder), when one is met read the option
ROUTES = f"{TYPES}/nitro-routes.d.ts"
ENV = {"npm_config_offline": "true"}
SCRIPT = "daodan-nuxt"  # what `container_runner.TOOLS` installs: `nuxt_pages.mjs` run by the container's Node
PAGES_TOTAL = 900  # seconds Daodan's script may take in all the folders together: a run lasts 1800, the restore of the packages in it
# measured: the peak resident memory of `nuxt prepare` and of the script on the two fixtures, 287-398 MB and 274-296 MB
# (`benchmarks/nuxt-routes/README.md`); 3 GB is the figure of Next.js (`container_runner.TOOLS`, a test keeps the two equal): a project
# with many modules may need more, and it is not measured
MEMORY_GB = 3
ANY = "default"  # the tool's key for a handler whose file name gives no method: it answers every method


def pages_seconds(folders: int) -> int:
    """The time Daodan's script has in each of `folders` folders: they share `PAGES_TOTAL`, so a project that takes its time does not
    take the rows of the others (the commands of the server routes all run before)."""
    # shortcut: a project of more than 90 folders asks for more than PAGES_TOTAL, 10 seconds each at the least; when one is met
    return max(10, PAGES_TOTAL // folders)


def commands(context):
    """For each folder `nuxt prepare` and the print of the file it writes (the server routes); then, for each, one of Daodan's
    script (`nuxt_pages.mjs`, `daodan-nuxt`), under `timeout`: the pages. The script needs no list: `loadNuxt` finds them. The
    script runs after all the others, so a slow one loses the rows of no other folder."""
    folders = frameworks.folders(context, PACKAGES)
    routes = [{"tool": NAME, "argv": argv, "cwd": folder, "env": env, "network": "none"}
              for folder in folders
              for argv, env in ((["npx", "--no-install", "nuxt", "prepare"], ENV), (["cat", ROUTES], {}))]
    pages = [{"tool": NAME, "argv": ["timeout", "--kill-after=10", str(pages_seconds(len(folders))), SCRIPT], "cwd": folder, "env": {},
              "network": "none"} for folder in folders]
    return routes + pages or None


def nitro_routes(text: str) -> tuple[list[dict], int | None, list[str]]:
    """The routes of `.nuxt/types/nitro-routes.d.ts` (`nuxt prepare`, run in Daodan's container), read from its syntax tree
    (`QUERIES["nitro_routes"]`): per route and method, `{path, method, import}` as the tool wrote them (the method `default` is
    a handler with no method in its file name), in the file's order; the line of the first error the tree holds (None when it
    parses whole), and the routes in which no import was read (`unread`: the tool named no handler file the reader knows). The
    import is assigned to the method, and the method to the route, whose type contains it, so the generics the tool wraps it in
    are no part of the reader. A tree that holds an error gives no route: a file cut short must not pass as a short list."""
    import entries
    source = text.encode("utf-8")
    root = entries._parse(source, "typescript")
    if root is not None and root.has_error:
        return [], entries._error_line(root), []
    found = entries._matches(source, "typescript", "nitro_routes", root)
    inside = lambda inner, outer: outer.start_byte <= inner.start_byte and inner.end_byte <= outer.end_byte  # noqa: E731
    imports = [match["import"][0] for match in found if "import" in match]
    methods = [(match["method"][0], match["value"][0]) for match in found if "method" in match]
    out, unread = [], []
    for match in (m for m in found if "route" in m):
        path, before = entries._text(source, match["route"][0]), len(out)
        out += [{"path": path, "method": entries._text(source, name), "import": entries._text(source, imported)}
                for name, value in methods if inside(value, match["methods"][0])
                for imported in imports if inside(imported, value)]
        if len(out) == before:
            unread.append(path)
    return out, None, unread


def _pages(tree, parents=()) -> list[dict]:
    """The routes of the tree the script prints, each `{name, file, path}` with its whole `path`: a child's is its own after its
    ancestors', unless it starts with a slash, as vue-router reads it (`/` for none). Raises ValueError for a tree that is not the
    known layout: a list of routes with a `path`, a `file` (null for a route with none) and `children`."""
    if not isinstance(tree, list):
        raise ValueError("not a list of pages")
    found = []
    for node in tree:
        if (not isinstance(node, dict) or not isinstance(node.get("path"), str) or "file" not in node
                or not (node["file"] is None or isinstance(node["file"], str)) or not isinstance(node.get("children", []), list)):
            raise ValueError("a page with no path or file")
        own = node["path"]
        segments = [own.strip("/")] if own.startswith("/") else [*parents, own.strip("/")]
        found.append({"name": node.get("name"), "file": node["file"], "path": "/" + "/".join(s for s in segments if s)})
        found += _pages(node.get("children", []), segments)
    return found


def _route_schema(route: str) -> str | None:
    """A server route as `REST` reads a path (`flows.path_schema`: `:id` is `{}`, and so is `*`, one segment in Nitro's router), or
    None for one that stands for several schemas: `**` and `**:path`, what is under it. The tool prints the text only, so its
    segments are read as Nitro writes them: a text with no grammar, read with string operations, as `nextjs._next_path` does."""
    import flows
    segments = route.split("/")
    if any(segment.startswith("**") for segment in segments):
        return None
    return flows.path_schema("/".join("{}" if segment == "*" else segment for segment in segments))


def _page_schema(path: str) -> str | None:
    """A page's path as `REST` reads one (`flows.path_schema`: `:id()` is `{}`), or None for one that stands for several schemas:
    a segment vue-router repeats or may leave out (`:slug(.*)*`, `:page?`, `:p+`), as Nuxt writes a catch-all and an optional page.
    Read as the vue-router of Nuxt writes it: a text with no grammar, read with string operations, as `nextjs._next_path` does."""
    # shortcut: a parameter inside a segment (`:id()-x`, `[id]-x.vue`) reads as the whole segment, when a project names a page so
    import flows
    if any(segment.endswith(("?", "*", "+")) for segment in path.split("/")):
        return None
    return flows.path_schema(path)


def _printed(result: dict) -> tuple[bool, list[dict]]:
    """`(called, pages)` of the last line of the script's standard output (a module of the project may print before it)."""
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    try:
        printed = json.loads(lines[-1])
    except (IndexError, ValueError):
        raise ValueError("the last line is no JSON") from None
    if not isinstance(printed, dict) or not isinstance(printed.get("called"), bool):
        raise ValueError("no `called`")
    return printed["called"], _pages(printed.get("pages"))


def read(context, commands, results):
    import entries
    import flows
    spec = entries.QUERIES[NAME]
    by_path: dict[str, list[str]] = {}  # the files of the snapshot that are scripts, by their path without the extension
    for rel, header in context.inventory.headers.items():
        if header.get("language") in SCRIPTS:
            by_path.setdefault(posixpath.splitext(rel)[0], []).append(rel)
    count = len(commands) // 3  # the folders: two commands each for the server routes, then one each for the pages
    gaps, handlers, pages = [], [], []  # the routes to bind: (route, method, file), and the pages: (path, file)
    for command, prepare, printed in zip(commands[:2 * count:2], results[:2 * count:2], results[1:2 * count:2]):
        folder = command["cwd"]
        if prepare["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"nuxt prepare exited with {prepare['returncode']}: {frameworks.excerpt(prepare)}"})
            continue
        if printed["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"nuxt prepare exited with 0 and wrote no {ROUTES}: its buildDir is not .nuxt, or this Nuxt has "
                                   "no such file"})
            continue
        found, error, unread = nitro_routes(printed["stdout"])
        if error:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"{ROUTES} did not parse whole (an error at line {error}): it was printed cut short, or written "
                                   "as this reader does not know"})
        elif not found and not unread:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"no route of the known layout was found in {ROUTES}: this reader does not know this Nuxt's layout"})
        for route in unread:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": f"{ROUTES} names {route} with no handler file this reader reads: {route} is not a row"})
        named: dict[str, list[str]] = {}  # the handler files the snapshot does not hold: file -> the routes that name it
        for item in found:
            imported = posixpath.normpath(posixpath.join(folder, TYPES, item["import"]))
            files = by_path.get(imported, [])
            if not files:
                named.setdefault(imported, []).append(item["path"])
            elif len(files) > 1:
                gaps.append({"kind": "model_partial", "path": imported,
                             "detail": f"nuxt prepare names {imported} for {item['path']}, and {len(files)} files of the snapshot have "
                                       f"that path without their extension: {', '.join(files)}"})
            else:
                handlers.append((item["path"], item["method"], files[0]))
        for imported, routes in named.items():
            gaps.append({"kind": "outside_snapshot", "path": imported,
                         "detail": f"nuxt prepare names {imported} for {', '.join(dict.fromkeys(routes))}, and the snapshot holds no "
                                   "file with that path"})
    for command, result in zip(commands[2 * count:], results[2 * count:]):
        folder = command["cwd"]
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": frameworks.stopped(result, SCRIPT, command["argv"][2], MEMORY_GB)})
            continue
        try:
            called, found = _printed(result)
        except ValueError as error:
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{SCRIPT} printed no JSON of the known layout ({error}): {frameworks.excerpt(result)}"})
            continue
        if not called:
            gaps.append({"kind": "model_partial", "path": folder,
                         "detail": "Nuxt did not call the hook pages:resolved: the app has no pages folder (measured), or this Nuxt "
                                   "does not call it; no page is read"})
            continue
        missing: dict[str, list[str]] = {}  # the files of the snapshot the pages name that it does not hold: file -> their routes
        for item in found:
            if item["file"] is None:
                gaps.append({"kind": "model_partial", "path": folder,
                             "detail": f"Nuxt resolves the route {item['path']} with no file: a redirect, or a route a module adds in "
                                       "code; it is not a row"})
                continue
            file = posixpath.normpath(posixpath.join(folder, item["file"]))
            if file in context.inventory.headers:
                pages.append((item["path"], file))
            else:
                missing.setdefault(file, []).append(item["path"])
        for file, routes in missing.items():
            gaps.append({"kind": "outside_snapshot", "path": file,
                         "detail": f"{SCRIPT} names {file} for {', '.join(dict.fromkeys(routes))}, and the snapshot holds no file "
                                   "with that path"})
    rows = []
    if handlers:
        server = spec["server-route"]
        for route, method, file in handlers:
            base = {"reader": NAME, "shape": "server-route", "kind": server["kind"], "path": route, "schema": _route_schema(route),
                    **({"method": method.upper()} if method != ANY else {})}
            module = {**base, "site": file, "symbol": f"{file}::{flows.MODULE}"}
            # shortcut: the default export of a handler file is nearly always a call, `defineEventHandler(...)`, which the
            # snapshot's export records bind to no function: a row on the file with the gap, not a guess by name; when the
            # records bind the function a call is given as its argument, the row is on that function
            rows.append({**module, "exports": server["exports"]})  # the links bind them (`binder`)
    for path, file in pages:  # the file is the entry, as for a Next.js page: no line, the tool gives none
        rows.append({"reader": NAME, "shape": "page", "kind": spec["page"]["kind"], "path": path, "schema": _page_schema(path),
                     "site": file, "symbol": f"{file}::{flows.MODULE}", **({"page": True} if spec["page"].get("page") else {})})
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in the record of the entry points and its gaps there; a record made without the source, or where it was not
    needed, has none."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])
