"""Source: the events an Angular project's own compiler reads in its templates, `parseTemplate`, run in Daodan's container.

`commands` finds, in each folder whose `package.json` declares `@angular/core` or `@angular/compiler`, the templates of
its components: a file that imports `Component` from `@angular/core` (the file headers say so) is read from its syntax tree
(`entries.QUERIES["components"]`), and its decorator's `templateUrl` names a file of the snapshot while its `template`, a text
written in the decorator, is told by where it lies in the `.ts`. Each folder has two commands of Daodan's script
(`angular_templates.mjs`), both given the list of templates as a file (`inputs`) and its path: the first calls the project's own
`parseTemplate` (`@angular/compiler`, resolved from the folder, so the one the project installed) and prints, for each event the
template binds, where and what it calls; the second, `--types`, asks the project's template type-checker
(`@angular/compiler-cli`, over the `tsconfig.json` of the folder, under `timeout`) which declaration a call on another object is.
Nothing of the project's runs on this machine: the script needs the project's restored packages (`container_runner.TOOLS`) and
runs with no network.

`read` binds each call to the method of the class the decorator belongs to, from the declarations the snapshot holds: a
row of the attribute reader's shape (`entries.ATTRIBUTE`), at the event's file and line, on that method. A call on another
object (`svc.cancel()`: the compiler names the receiver `svc`, not its class) is the method the type-checker says it is, bound to
the snapshot's declaration at that file and line. A call with no object before it is that method only if the compiler's own binder does not say the template declares the name (`let-c`, `@let`, the variable of an `@for`): then it is a gap. What no tool gives is a gap with its cause, never a guess: a method the class
does not declare (inherited, or assigned at run time), a declaration in a file the snapshot does not hold (a package's), a
component the `tsconfig.json` does not reach, and a type-checker that did not answer, in the words of the tool: the package,
the file or the time. An event that calls nothing (`open = !open`) starts no function and is no row. The rows are merged into
the tree-sitter reader's by `entries.compiled`: where both read the same event the compiler's handler wins and the tree's
label stays.

Not read: the `host` metadata and `@HostListener` of a component, and the difference between an event of the DOM and an
output of a child component; a call whose callee is no name, or that the script cannot read (Angular up to 12), is a gap. Every other decorator that cannot be read is a gap with its file and line (`_components`).
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "angular", "daodan/premap/v1", "scanner"
SCRIPT = "daodan-angular"  # what `container_runner.TOOLS` installs: `angular_templates.mjs` run by the container's Node
PACKAGES = ("@angular/core", "@angular/compiler")
TYPES_TOTAL = 900  # seconds the type-checker may take in all the folders together: a run lasts 1800, the restore of the packages in it
MEMORY_GB = 3  # what the run has (`container_runner.TOOLS["angular"]`, a test keeps the two equal)


def types_seconds(folders: int) -> int:
    """The time the type-checker has in each of `folders` folders: they share `TYPES_TOTAL`, so a slow one does not take the rows of
    the others (the parses all run before it)."""
    # shortcut: a project of more than 90 folders asks for more than TYPES_TOTAL, 10 seconds each at the least; when one is met
    return max(10, TYPES_TOTAL // folders)


def _folders(context) -> list[str]:
    """The folders whose `package.json` declares Angular; one that is not valid JSON is skipped: `npm-files` reports it."""
    folders = []
    for rel in context.inventory.files:
        if PurePosixPath(rel).name != "package.json":
            continue
        try:
            manifest = json.loads(context.inventory.text(rel))
        except ValueError:
            continue
        if isinstance(manifest, dict) and any(isinstance(manifest.get(section), dict) and name in manifest[section]
                                              for section in ("dependencies", "devDependencies") for name in PACKAGES):
            folders.append(PurePosixPath(rel).parent.as_posix())
    return sorted(folders, key=lambda folder: (folder == ".", -len(folder), folder))  # the deepest first, the root last


def _folder(folders: list[str], file: str) -> str | None:
    return next((folder for folder in folders if folder == "." or file.startswith(folder + "/")), None)


def _units(line: str, byte_column: int) -> int:
    """The column JavaScript counts, UTF-16 code units, of a column the tree gives in bytes."""
    return len(line.encode("utf-8")[:byte_column].decode("utf-8").encode("utf-16-le")) // 2


def _names() -> dict:
    """What a framework's component is written with, the data of `components` in `entry-queries.json`: the module the decorator
    is imported from, the decorator, and the properties that hold the template."""
    import entries
    return entries.QUERIES["components"]["typescript"]


def _imports_component(header: dict) -> bool:
    # shortcut: a file that reaches the decorator by a namespace (`import * as ng from '@angular/core'`, `@ng.Component(...)`) is not
    # chosen, and no gap says so; when a project is met that writes its components so
    names = _names()
    return any(item.get("module") == names["module"] and names["decorator"] in item.get("names", ())
               for item in header.get("import_bindings") or ())


CLASSES = ("class_declaration", "abstract_class_declaration", "class")  # what a decorator decorates, `class` the anonymous default


def _property(pair, source: bytes) -> tuple[str | None, object]:
    """The key and the value of a property of the decorator's object: `key: value`, a quoted key too, or `{ template }`."""
    import entries
    if pair.type == "shorthand_property_identifier":
        return entries._text(source, pair), pair
    key, value = pair.child_by_field_name("key"), pair.child_by_field_name("value")
    if pair.type != "pair" or key is None or value is None:
        return None, pair
    text = entries._text(source, key)
    return (text[1:-1] if key.type == "string" else text), value


def _components(context, file: str, gaps: list[dict]) -> list[dict]:
    """The components of a file, each `{class, line, templates}`: a template is `{"f": file}` for a `templateUrl`, or
    `{"f": file, "r": [row, column, row, column]}` for a `template` written in the decorator, the range of its content in
    the file by rows and UTF-16 columns (the compiler's `range`, which it takes whole-file). Each decorator the file applies
    under the name `Component` is imported as (an alias too) is read or is a gap with its file and line: the argument is no
    object written in place, the class has no name, the object names no template, or a template is no text.

    Read from the syntax tree, a hand-written reader of the decorator (`entries.QUERIES["components"]`), for want of a
    tool the project is sure to have. Evaluated: the Angular language service's `getComponentLocationsForTemplate` and
    `getTemplateLocationForComponent` (`benchmarks/angular-compiler/results/07_ls_join.txt`, `11_inline_more.txt`) give the
    same link, and the exact range of an inline template, from a loaded TypeScript program: they need `typescript`, a
    `tsconfig.json` that reaches the component and `@angular/language-service` installed (a project's own packages do not
    always have it; 2.8 to 4.3 seconds to load the fixture), where `@angular/compiler` is what `parseTemplate` already needs. The
    compiler-cli's `NgCompiler.getComponentsWithTemplateFile` gives the class of a `.html` and gives none for an inline
    template (`results/04_compiler_cli.txt`)."""
    import entries
    # shortcut: this is a hand-written reader of the decorator. The tools that give the link (`getComponentLocationsForTemplate`,
    # `NgCompiler.getComponentsWithTemplateFile`) need the project's TypeScript program, and the first pass must work with only
    # `@angular/compiler`, which every Angular project has: that is why `ttc.getTemplate`, which needs the program, is not what
    # parses; replace it when the program is known to build wherever the source runs
    text = context.inventory.text(file)
    source = text.encode("utf-8")
    root = entries._parse(source, "typescript")
    if root is None:
        gaps.append({"kind": "model_partial", "path": file, "detail": "the TypeScript grammar did not load: its components are not read"})
        return []
    found = entries._matches(source, "typescript", "components", root)
    data = _names()
    names = {entries._text(source, c["local"][0]) if "local" in c else data["decorator"] for c in found
             if "imported" in c and entries._text(source, c["module"][0]) == data["module"]
             and entries._text(source, c["imported"][0]) == data["decorator"]}
    lines, out = text.split("\n"), []
    for captured in sorted((c for c in found if "decorator" in c), key=lambda c: c["decorator"][0].start_byte):
        decorator = captured["decorator"][0]
        if entries._text(source, captured["name"][0]) not in names:
            continue
        site = f"{file}:{decorator.start_point[0] + 1}"
        owner = decorator.parent
        cls = next((c for c in owner.children if c.type in CLASSES), None) if owner.type == "export_statement" else owner
        if cls is None or cls.type not in CLASSES:
            gaps.append({"kind": "model_partial", "path": file, "detail": f"the @Component at {site} decorates no class"})
            continue
        name = cls.child_by_field_name("name")
        if name is None:
            gaps.append({"kind": "model_partial", "path": file, "detail": f"the class the @Component at {site} decorates has no name "
                                                                        "(`export default class`): its template is not read"})
            continue
        item = {"class": entries._text(source, name), "line": cls.start_point[0] + 1}
        arguments = next((c for c in captured["arguments"][0].named_children if not c.is_extra), None)
        if arguments is None or arguments.type != "object":
            gaps.append({"kind": "model_partial", "path": file, "detail": f"the @Component of {item['class']} at {site} is given no object "
                                                                        "written in place: its template is not read"})
            continue
        props = {}
        for pair in (c for c in arguments.named_children if not c.is_extra):
            key, value = _property(pair, source)
            if key in (data["template"], data["url"]):
                props.setdefault(key, value)
        templates = []
        for key, value in props.items():
            where = f"{item['class']} ({file}:{value.start_point[0] + 1})"
            if key == data["url"]:
                url = entries._string(value, source, "typescript", exact=True)
                target = posixpath.normpath(posixpath.join(posixpath.dirname(file), url)) if url else None
                if target is None:
                    gaps.append({"kind": "model_partial", "path": file, "detail": f"the templateUrl of {where} is no text written in place"})
                elif target not in context.inventory.headers:
                    gaps.append({"kind": "outside_snapshot", "path": target, "detail": f"the templateUrl of {where} names {target}, "
                                                                                    "a file the snapshot does not hold"})
                else:
                    templates.append({"f": target})
            elif value.type not in ("string", "template_string") or any(c.type == "template_substitution" for c in value.children):
                gaps.append({"kind": "model_partial", "path": file, "detail": f"the template of {where} is no text written in place "
                                                                            "(a `${...}` or an expression): its events are not read"})
            else:  # the content: after the opening quote, before the closing one
                (start_row, start_col), (end_row, end_col) = value.start_point, value.end_point
                templates.append({"f": file, "r": [start_row, _units(lines[start_row], start_col) + 1,
                                                   end_row, _units(lines[end_row], end_col) - 1]})
        if not props:
            gaps.append({"kind": "model_partial", "path": file, "detail": f"the @{data['decorator']} of {item['class']} at {site} names no "
                                                                        f"{data['template']} or {data['url']}: it has no events to read"})
        out.append({**item, "templates": templates})
    return out


def _plan(context) -> dict:
    """`{"jobs": {folder: [(job, [component, ...]), ...]}, "gaps": [...]}`: the templates to read in each folder, one job
    for each (file, range) with the components that use it, in the order the folder's command lists them; and the gaps
    of what cannot be read before the compiler runs."""
    folders, gaps, by_folder = _folders(context), [], {}
    if not folders:
        return {"jobs": {}, "gaps": []}
    for file in context.inventory.files:
        header = context.inventory.headers[file]
        if header.get("language") != "typescript" or not _imports_component(header):
            continue
        folder = _folder(folders, file)
        components = _components(context, file, gaps)
        if folder is None:
            if components:
                gaps.append({"kind": "model_partial", "path": file, "detail": "no package.json above it declares Angular: the "
                                                                              "templates of its components are not read"})
            continue
        for component in components:
            for template in component["templates"]:
                relative = {**template, "f": posixpath.relpath(template["f"], folder)}
                jobs = by_folder.setdefault(folder, {})
                jobs.setdefault((relative["f"], tuple(relative.get("r", ()))), (relative, []))[1].append(
                    {"file": file, "class": component["class"], "line": component["line"], "template": template["f"]})
    return {"jobs": {folder: [pair for _, pair in sorted(by_folder[folder].items())] for folder in sorted(by_folder)}, "gaps": gaps}


def commands(context):
    """For each folder with templates two commands, both given the folder's list of them as a file (`inputs`, which
    `container_runner` carries to `preparation.IN`; a command line has a limit): one parses them, the other asks the project's
    template type-checker which method a call on another object is, under a time limit (`--types`, `types_seconds`). The parses
    come first, all of them: a type-checker that takes its time loses the rows of no other folder. A template travels with the
    components that use it: `c`, each their file, class and line, relative to the folder."""
    import preparation
    # shortcut: `--types` builds the program of the folder's `tsconfig.json` (or of the projects it references); without `files` or
    # `include` that is every `.ts` under the folder, and the cost grows with the project, bounded by `types_seconds`; when a
    # project's time is measured to be spent, give it the program of `tsconfig.app.json` alone
    folders = [(folder, items) for folder, items in _plan(context)["jobs"].items() if items]
    parse, types = [], []
    for number, (folder, items) in enumerate(folders):
        name, path = f"angular-jobs-{number}.json", f"{preparation.IN}/angular-jobs-{number}.json"
        carried = {name: json.dumps([{**job, "c": [[posixpath.relpath(m["file"], folder), m["class"], m["line"]] for m in members]}
                                     for job, members in items], separators=(",", ":"))}
        common = {"tool": NAME, "cwd": folder, "env": {}, "network": "none", "inputs": carried}
        parse.append({**common, "argv": [SCRIPT, path]})
        types.append({**common, "argv": ["timeout", "--kill-after=10", str(types_seconds(len(folders))), SCRIPT, "--types", path]})
    return parse + types or None


def _declarations(store, file: str) -> list[dict]:
    """The classes and methods the snapshot declares in a file, each `{name, kind, line, end, qualified}`, from its sqlite store
    or its JSON one (as `flow_entries.declarations` reads them)."""
    if store.format == "sqlite":
        from snapshot_store import _unpack
        return [{"name": name, "kind": kind, "line": line, "end": end, "qualified": _unpack(payload).get("qualified_name") or name}
                for name, kind, line, end, payload in store.connection.execute(
                    "SELECT name,kind,l0,l1,payload FROM sem_declarations WHERE file=? AND kind IN ('class','method','function')", (file,))]
    entry = store.get_file(file) or {}
    return [{"name": d["name"], "kind": d["kind"], "line": d["span"][0], "end": d["span"][2], "qualified": d.get("qualified_name") or d["name"]}
            for d in (entry.get("semantic") or {}).get("declarations", ()) if d["kind"] in ("class", "method", "function")]


def _bytes(line: str, units: int) -> int:
    """The column in bytes, as the snapshot writes it, of a column the compiler gives in UTF-16 code units."""
    seen = 0
    for index, char in enumerate(line):
        if seen >= units:
            return len(line[:index].encode("utf-8"))
        seen += 2 if ord(char) > 0xFFFF else 1
    return len(line.encode("utf-8"))


def _tail(result: dict) -> str:
    return (result["stderr"] or result["stdout"]).strip()[-400:]


def _types(result: dict | None, seconds: str, folder: str, gaps: list[dict]) -> tuple[dict, str | None]:
    """What the type-checker answered for a folder: its declarations by template, component, event and call, and, when it gave
    none, why: a gap of the folder, the cause in the words of the tool (the package, the file or the time)."""
    if result is None:
        cause = "the type-checker was not asked"
    elif result["returncode"] == 124:  # `timeout` ended the command
        cause = f"the type-checker did not end in {seconds} seconds"
    elif result["returncode"] == 137:  # `timeout` had to kill it, or the memory of the run did: the signal does not say which
        cause = (f"the type-checker was killed (exit 137): it did not end in {seconds} seconds, or it ran out of memory ({MEMORY_GB} GB)")
    elif result["returncode"] != 0:
        cause = f"{SCRIPT} --types exited with {result['returncode']}: {_tail(result)}"
    else:
        try:
            answer = json.loads(result["stdout"])
            resolved, cause = {(item["f"], tuple(item.get("r", ())), tuple(item["c"]), item["line"], item["col"], item["i"]): item
                               for item in answer["resolved"]}, answer.get("error")
        except (ValueError, KeyError, TypeError):
            cause = f"{SCRIPT} --types printed no JSON of the known layout: {_tail(result)}"
        else:
            if not cause:
                return resolved, None
    gaps.append({"kind": "model_partial", "path": folder, "detail": f"the receivers of calls on another object are not resolved: {cause}"})
    return {}, cause


def _rows(context, declared: dict, folder: str, job: dict, component: dict, event: dict, types: tuple[dict, str | None]) -> list[dict]:
    """The rows of one event for one component: one per call its handler makes, on the method of the component's class, else
    a gap that says why (the class is not in the snapshot, it does not declare the method). A call on another object is the
    method the template type-checker says it is, `types`, where the snapshot holds its file: else a gap with the type-checker's
    cause, or the file the declaration lies in."""
    import entries
    file, cls = component["template"], component["class"]
    # shortcut: `(saved)`, an output of a child component, and `(click)`, an event of the DOM, are one reader's rows: the shape is
    # classified once; the type-checker tells them apart (`getSymbolOfNode` of the event), which this source does not ask
    shape = f"({event['name']})"
    line = context.inventory.text(file).split("\n")[event["line"] - 1]
    base = {"reader": entries.ATTRIBUTE, "shape": shape, "site": f"{file}:{event['line']}",
            "event": entries.QUERIES["events"].get(shape, shape), "column": _bytes(line, event["col"])}
    ts = component["file"]
    declared_in = lambda path: declared.setdefault(path, _declarations(context.store, path))  # noqa: E731
    found = [d for d in declared_in(ts) if d["kind"] == "class" and d["name"] == cls and d["line"] == component["line"]]
    owner = f"{ts}::{found[0]['qualified']}" if found else f"{file}::<module>"  # as `flows.Facts.node` names a declaration
    out = []
    for index, call in enumerate(event["calls"]):
        symbol = None
        if not found:
            why = f"the snapshot declares no class {cls} at {ts}:{component['line']}, so {call['name']} is not bound to a method"
        elif call.get("scope"):  # the template declares the name (`let-c`, `@let`, the variable of an `@for`): the compiler's binder said so
            why = (f"{call['name']} is a template {call['scope']} declared in the template, not a method of {cls}: "
                   "the handler it stands for is not known")
        elif call["on"] not in (None, "this"):
            asked = (job["f"], tuple(job.get("r", ())), (posixpath.relpath(ts, folder), cls, component["line"]), event["line"], event["col"], index)
            answer = types[0].get(asked)
            what = f"{call['on']}.{call['name']}"
            if answer is None:
                missing = types[1] or "the type-checker's answer lacks this call"
                why = f"{what}: its receiver's class is told by the template type-checker of @angular/compiler-cli, which gave no answer: {missing}"
            elif answer["error"]:
                why = f"{what}: {answer['error']}"
            else:
                decl = answer["decl"]
                target = posixpath.normpath(posixpath.join(folder, decl["f"]))
                methods = [d for d in declared_in(target) if d["kind"] in ("method", "function") and d["name"] == decl["n"]
                           and d["line"] <= decl["l"] <= d["end"]] if target in context.inventory.headers else []
                if methods:
                    symbol = f"{target}::{max(methods, key=lambda d: d['line'])['qualified']}"
                elif target not in context.inventory.headers:
                    why = f"{what} is declared in {target}, which the snapshot does not hold (a package's, or outside the project)"
                else:
                    why = f"{what} is declared at {target}:{decl['l']}, where the snapshot declares no method {decl['n']}"
        else:
            # shortcut: a method the class inherits or a property it assigns an arrow function is not a method the snapshot declares
            # in the class: it is a gap, though the type-checker would give it; ask it for these when a project's gaps are mostly so
            qualified = f"{found[0]['qualified']}.{call['name']}"
            methods = [d for d in declared_in(ts) if d["kind"] in ("method", "function") and d["qualified"] == qualified]
            if methods:
                symbol = f"{ts}::{qualified}"
            else:
                why = f"{cls} does not declare {call['name']}: it is inherited, or assigned at run time"
        out.append({**base, "owner": owner, "symbol": symbol, "handler_source": NAME} if symbol
                   else {**base, "owner": owner, "symbol": owner, "gap": why})
    for reason in event.get("unread", ()):  # a call the script could not read: a gap at the event, never a silence
        out.append({**base, "owner": owner, "symbol": owner, "gap": f"{event.get('handler')}: {reason}"})
    return out


def read(context, commands, results):
    # shortcut: the `host` metadata and `@HostListener` of a component are not read (the type-checker's `getHostElement` gives
    # their listeners, measured in `results/10_symbols_options.txt`); do it when a project's entries are measured to miss them
    plan = _plan(context)
    gaps, rows, declared = list(plan["gaps"]), [], {}
    parsed, typed = {}, {}
    for command, result in zip(commands, results):
        if "--types" in command["argv"]:
            typed[command["cwd"]] = (command["argv"][2], result)
        else:
            parsed[command["cwd"]] = result
    for folder, result in parsed.items():
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"{SCRIPT} exited with {result['returncode']}: {_tail(result)}"})
            continue
        try:
            answered = {(t["f"], tuple(t.get("r", ()))): t for t in json.loads(result["stdout"])["templates"]}
        except (ValueError, KeyError, TypeError):
            gaps.append({"kind": "model_failed", "path": folder, "detail": f"{SCRIPT} printed no JSON of the known layout: {_tail(result)}"})
            continue
        seconds, answer = typed.get(folder, (None, None))
        types = _types(answer, seconds, folder, gaps)
        for job, members in plan["jobs"][folder]:
            template = answered.get((job["f"], tuple(job.get("r", ()))))
            path = posixpath.normpath(posixpath.join(folder, job["f"]))
            if template is None or "error" in template:
                gaps.append({"kind": "model_failed", "path": path, "detail": f"parseTemplate gave nothing for {path}: "
                                                                            f"{template['error'] if template else 'it is not in the answer'}"})
                continue
            if template.get("errors"):
                gaps.append({"kind": "model_partial", "path": path, "detail": f"parseTemplate reported {len(template['errors'])} errors in "
                                                                             f"{path}, so events may be missing: {template['errors'][0][:200]}"})
            for component in members:
                for event in template["events"]:
                    rows += _rows(context, declared, folder, job, component, event, types)
    return {"facts": {"framework_entries": rows} if rows else {}, "gaps": gaps}


def from_record(report):
    """The rows this source persisted in a pre-map and its gaps there; a pre-map made without the source, or where it was not
    needed, has none. The rows are the attribute reader's shape: `entries.compiled` merges them into the tree reader's."""
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
