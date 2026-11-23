"""Source: the events an Astro project's own compiler reads in its templates, `parse`, run in Daodan's container.

`commands` finds, in each folder whose `package.json` declares `astro`, its `.astro` files, and gives the folder one command of
Daodan's script (`astro_templates.mjs`), under `timeout`, told the list of them as a file (`inputs`), the start of the attribute names
that may be events and the file `astro` ships that declares them (`QUERIES["astro"]`, data). The script calls `parse` of the compiler
the project's own `astro` depends on (`@astrojs/compiler`, or `@astrojs/compiler-rs` from Astro 7), resolved from the folder, and
prints, for each attribute that starts so on an element of the page, where it is and the string it holds, and the text of the file of
declarations. Nothing of the project's runs on this machine: the script needs the project's restored packages
(`container_runner.TOOLS`) and runs with no network.

What `parse` gives is the event and where it is, to the line and the column (`benchmarks/astro-compiler/`: every attribute start is
exact, on both compilers; the script checks each one against the text before it prints it). Which attributes are events is Astro's
own: the members of `DOMAttributes` in `astro-jsx.d.ts`, the declarations `astro` ships for its JSX, read from the syntax tree of
TypeScript (`QUERIES["astro_events"]`); `one="two()"` starts with `on` and is no event. `lib.dom.d.ts` (`GlobalEventHandlers`) was
evaluated and is not used: the project has it only if it has TypeScript (measured: Astro 5's packages do, Astro 6's and 7's do not).
The parse does not give the function. An attribute `onclick="save()"` holds JavaScript in a string, and the compiler's tree stops
there: which function the page's global scope holds under `save` is no datum of the tree (the frontmatter runs on the server, a
`<script>` Astro processes is a module, only an inline one declares a global), and the snapshot reads the frontmatter and every script
of the file as one module, so a lookup by name would bind to code the page cannot reach. So each call the string makes (read from its
syntax tree: the `javascript` grammar) is a row at the attribute's file, line and column with a gap that says so: a call of a name, a
call on an object (`cart.add(1)`: what `cart` is, is not in the tree) and a callee that is no name (`items[0]()`, `(0, run)()`).
An event that calls nothing (`this.disabled = true`) is no row. A value that is not a string written in place (`onclick={fn}`, a template
literal, `{onclick}`) is a gap: it is computed when the page is rendered. The `<script>` blocks are JavaScript: the language's reader has
them, and `addEventListener` is not read here. An attribute on a component is a prop, not read. A file the compiler reports an error for
is a gap (Astro 7: its tree is not read; Astro 5 and 6 report no error for markup that does not close, measured, so a handler lost
there is lost without a gap; Astro 4 declares the Go compiler and was not run). A command the time limit ends or kills, and a file the
answer does not hold, are gaps with their cause.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "astro", "daodan/premap/v2", "scanner"
SCRIPT = "daodan-astro"  # what `container_runner.TOOLS` installs: `astro_templates.mjs` run by the container's Node
PACKAGE = "astro"
TOTAL_SECONDS = 600  # seconds the commands may take in all the folders together: a run lasts 1800, the restore of the packages in it
MEMORY_GB = 3  # what the run has (`container_runner.TOOLS["astro"]`, a test keeps the two equal)
OBJECT = "member_expression"  # the callee of a call on an object (`cart.add(1)`); an identifier is a name, any other node names no function


def seconds(folders: int) -> int:
    """The time the command has in each of `folders` folders: they share `TOTAL_SECONDS`, so a slow one does not take the rows of the
    others (the commands run one after the other)."""
    # shortcut: a project of more than 60 folders asks for more than TOTAL_SECONDS, 10 seconds each at the least; when one is met
    return max(10, TOTAL_SECONDS // folders)


def _folders(context) -> list[str]:
    """The folders whose `package.json` declares `astro`, the deepest first; one that is not valid JSON is skipped: `npm-files`
    reports it."""
    folders = []
    for rel in context.inventory.files:
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            manifest = json.loads(context.inventory.text(rel))
        except ValueError:
            continue
        if isinstance(manifest, dict) and any(isinstance(manifest.get(section), dict) and PACKAGE in manifest[section]
                                              for section in ("dependencies", "devDependencies")):
            folders.append(PurePosixPath(rel).parent.as_posix())
    return sorted(folders, key=lambda folder: (folder == ".", -len(folder), folder))


def _table() -> dict:
    """What an Astro event attribute is written with and where Astro declares it, the data of `astro` in `entry-queries.json`."""
    import entries
    return entries.QUERIES[NAME]


def _plan(context) -> dict:
    """`{"files": {folder: [file, ...]}, "gaps": [...]}`: the `.astro` files of each folder whose `package.json` declares `astro`,
    relative to the folder, as the snapshot holds them; and a gap for each one no such folder holds."""
    from premap.angular import _folder  # the nearest folder above a file (shared: no framework in it)
    folders, by_folder, gaps = _folders(context), {}, []
    for file in context.inventory.files:
        if context.inventory.headers[file].get("language") != NAME:
            continue
        if (folder := _folder(folders, file)) is None:
            gaps.append({"kind": "model_partial", "path": file, "detail": "no package.json above it declares astro: the events of its template are not read"})
        else:
            by_folder.setdefault(folder, []).append(posixpath.relpath(file, folder))
    return {"files": {folder: sorted(files) for folder, files in sorted(by_folder.items())}, "gaps": gaps}


def commands(context):
    """For each folder with `.astro` files one command, under `timeout` (a project's own code may not end), given the list of them
    as a file (`inputs`, which `container_runner` carries to `preparation.IN`; a command line has a limit) and its path. The compiler
    is the project's own: the packages are restored first, and the command runs with no network."""
    import preparation
    # shortcut: the prefix only keeps what the script prints small; which attributes are events is Astro's own list (`_declared`), so an
    # `on*` attribute Astro does not declare (`onend` of an SVG animation, which a browser may know) is not read, and an `astro` that
    # ships no `astro-jsx.d.ts` of that name (Astro 4 was not run) has no event read and a gap that says so; when one is met, read the
    # declarations that version has
    plan = _plan(context)["files"]
    out = []
    for number, (folder, files) in enumerate(plan.items()):
        name = f"astro-files-{number}.json"
        table = _table()
        carried = {name: json.dumps({"prefix": table["event_prefix"], "jsx": table["jsx"], "files": files}, separators=(",", ":"))}
        out.append({"tool": NAME, "cwd": folder, "env": {}, "network": "none", "inputs": carried,
                    "argv": ["timeout", "--kill-after=10", str(seconds(len(plan))), SCRIPT, f"{preparation.IN}/{name}"]})
    return out or None


def _declared(text: str) -> set[str]:
    """The names of the members of the interface Astro declares its event attributes in, from the syntax tree of the declarations
    file it ships (`QUERIES["astro_events"]`, the interface's name in `astro`); empty when the text declares no such interface."""
    import entries
    source = text.encode("utf-8")
    root = entries._parse(source, "typescript")
    if root is None:
        return set()
    wanted = _table()["interface"]
    return {entries._text(source, captures["member"][0]) for captures in entries._matches(source, "typescript", "astro_events", root)
            if "member" in captures and entries._text(source, captures["interface"][0]) == wanted}


def _calls(code: str) -> list[tuple[str, str | None]] | None:
    """What a string of JavaScript calls, each callee once, from the outermost and first written: `(text, kind)` with kind `None`
    for a name, `member_expression` for a call on an object and the node's own type for any other callee (it names no function);
    from its syntax tree and the query of `handlers` (data); None when the grammar did not load."""
    import entries
    source = code.encode("utf-8")
    root = entries._parse(source, "javascript")
    if root is None:
        return None
    nodes = {(node.start_byte, node.end_byte): node for captures in entries._matches(source, "javascript", "handlers", root)
             for node in captures.get("called", ())}
    found = {}
    for node in sorted(nodes.values(), key=lambda node: (node.start_byte, -node.end_byte)):
        found.setdefault(entries._text(source, node), None if node.type == "identifier" else node.type)
    return list(found.items())


def _rows(context, path: str, event: dict, gaps: list[dict]) -> list[dict]:
    """The rows of one event: one for each callee its string calls, none when it calls none or holds nothing, one for a value that
    is not a string in place. Each is a gap that says why the function is not known."""
    import entries
    from premap.angular import _bytes  # the column in bytes, as the snapshot writes it, of one in UTF-16 code units
    name = event["name"]
    line = context.inventory.text(path).split("\n")[event["line"] - 1]
    base = {"reader": entries.ATTRIBUTE, "shape": name, "site": f"{path}:{event['line']}", "event": entries.QUERIES["events"].get(name, name),
            "column": _bytes(line, event["col"]), "owner": f"{path}::<module>"}
    base["symbol"] = base["owner"]
    where = f"{name} on <{event['tag']}>"
    if event["kind"] == "quoted":
        called = _calls(event["value"])
        if called is None:
            gaps.append({"kind": "model_partial", "path": path, "detail": "the JavaScript grammar did not load: the handlers of the events are not read"})
            return []
        # shortcut: `new Thing()` is a constructor and a tagged template is no call: neither is a row; when a project is met whose
        # handlers are mostly so, add the nodes to the query of `handlers`
        said = {None: "{callee} in a string of JavaScript: the compiler's tree holds the text, not the function the page's global scope "
                      "holds under that name",
                OBJECT: "{callee} on an object in a string of JavaScript: what the object is, and so the method it names, is not in the "
                        "compiler's tree"}
        return [{**base, "gap": f"{where} calls " + said.get(kind, "{callee}, a callee that is no name ({kind}) in a string of JavaScript: "
                                                                   "it names no function").format(callee=callee, kind=kind)}
                for callee, kind in called]
    if event["kind"] == "empty":
        return []
    return [{**base, "gap": f"{where} is not a string written in place ({event['kind']}): its value is computed when the page is rendered, "
                            "so the function it names is not known"}]


def _stopped(result: dict, limit: str) -> str:
    """Why the script did not give its answer, in the words of the tool: the cause it wrote, or the limit that ended it."""
    from premap import react_router  # shortcut: `_excerpt` (both ends of what a tool said) is React Router's, as Nuxt calls it
    if result["returncode"] == 124:  # `timeout` ended the command
        return f"{SCRIPT} did not end in {limit} seconds"
    if result["returncode"] == 137:  # `timeout` had to kill it, or the memory of the run did: the signal does not say which
        return f"{SCRIPT} was killed (exit 137): it did not end in {limit} seconds, or it ran out of memory ({MEMORY_GB} GB)"
    return f"{SCRIPT} exited with {result['returncode']}: {react_router._excerpt(result)}"


def read(context, commands, results):
    from premap import react_router
    plan = _plan(context)
    gaps, rows = list(plan["gaps"]), []
    for command, result in zip(commands, results):
        folder = command["cwd"]
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": _stopped(result, command["argv"][2])})
            continue
        try:
            answer = json.loads(result["stdout"])
            answered = {item["f"]: item for item in answer["files"]}
        except (ValueError, KeyError, TypeError):
            gaps.append({"kind": "model_failed", "path": folder,
                         "detail": f"{SCRIPT} printed no JSON of the known layout: {react_router._excerpt(result)}"})
            continue
        jsx = _table()["jsx"]
        declared = _declared(answer["jsx"]) if isinstance(answer.get("jsx"), str) else set()
        if not declared:
            why = f"{jsx} is not in the packages of astro" if answer.get("jsx") is None else f"{jsx} declares no {_table()['interface']}"
            gaps.append({"kind": "model_partial", "path": folder, "detail": f"the names of the events are not known, so no event is read: {why}"})
            continue
        for file in plan["files"].get(folder, ()):  # the plan, not the answer: a file the answer lacks is a gap, never a silence
            path = posixpath.normpath(posixpath.join(folder, file))
            item = answered.get(file)
            if item is None or "error" in item:
                gaps.append({"kind": "model_failed", "path": path,
                             "detail": f"parse gave nothing for {path}: {item['error'] if item else 'it is not in the answer'}"})
                continue
            if item.get("errors"):
                gaps.append({"kind": "model_partial", "path": path, "detail": f"parse reported {len(item['errors'])} errors in {path}, "
                                                                             f"so events may be missing: {item['errors'][0][:200]}"})
            gaps += [{"kind": "model_partial", "path": path, "detail": f"{reason} ({path})"} for reason in item.get("unread", ())]
            for event in item["events"]:
                if event["name"] in declared:
                    rows += _rows(context, path, event, gaps)
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in a pre-map and its gaps there; a pre-map made without the source, or where it was not
    needed, has none. The rows are the attribute reader's shape: `entries.compiled` adds them to the tree reader's."""
    source = f"{NAME}@{VERSION}"
    return ([row for row in report.get("framework_entries", ()) if source in row["sources"]],
            [gap for gap in report["gaps"] if gap.get("source") == source])


def recorded(manifest) -> list[dict]:
    """The rows persisted for a snapshot, none where there is no pre-map for it."""
    from pathlib import Path
    from premap.flow_entries import read_record
    try:
        return from_record(read_record(Path(manifest)))[0]
    except (OSError, KeyError, TypeError, ValueError):
        return []
