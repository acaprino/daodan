"""Express's routes, read by a module of Daodan's from the snapshot's syntax trees (point 14 of the refactoring plan, `T1.C.8`).

Tools evaluated first, as the golden rule asks (`benchmarks/express-routes/README.md`): Express has no public interface that lists
its routes (only the router's internal `stack`); `express-list-endpoints` 7.1.1 reads internal fields with regular expressions on the
text of a regular expression, gives neither file nor line of a handler and does not support Express 5; OWASP Noir 1.5.0 gives the
routes but cites the handler by a name and a line the binder must guess from. So the reader is ours.

The method is GitNexus's (`abhigyanpatwari/GitNexus` at `acf755a1b70e`, `gitnexus` 1.6.12, PolyForm Noncommercial), as the README
describes it in our words («Metodo di GitNexus»); no line, query or table of it is here. In two times: each JavaScript or TypeScript
file of the snapshot gives, from its tree (`flows.Facts.tree`) and the data's query (`entry-queries.json`, `express`), its calls and
its CommonJS exports; then the values are evaluated across the files with the snapshot's own reading (`read_code`): a name is what
the snapshot's scopes bind it to (`Facts.bindings`), an import goes where the snapshot's module resolution sends it
(`sem_modules`), an export is the snapshot's export record (`sem_exports`) or `module.exports`. A value is an app (the call of the
package's default export), a router (the call of its `Router`), a `route(path)` of one of them, a function of the snapshot (by its
declaration), or a parameter of a function, which is the argument of each call to that function (one hop, no chain). A `use` on an
app or a router mounts each argument that is one, under its literal prefix, none, or an unknown one; the prefixes are composed from
the apps no one mounts. A route is a verb of the data on an app, a router or a `route(path)`, with a handler after the path (one
argument alone is Express's getter of a setting, `app.get('env')`); its handler is the last argument, the last of an array.

A row per route: `reader` `express`, `shape` (`method` or `route`, the data's form), `kind` `rotta`, `method` (None for `all`),
`path` with the prefixes composed, `schema` (`flows.path_schema`), and `site` and `span` of the handler's function: the binder ties it
to the one function of the snapshot with that span (`binder.bind`); `registered` keeps where the route is registered. A path that is no literal, a handler that is no function of the
snapshot, a router mounted under a prefix that is no literal and a router no app mounts are gaps with the cause, at the registration.
It runs on the host with no container (spec «Strumenti nativi»), once the snapshot is read; not run by the step: `T1.C.9` measured it short of Noir.

Hono (`T1.C.10`: `inspectRoutes` of `hono/dev` did not pass, `benchmarks/hono-routes/README.md`) is the same code on the data of its
section (`SECTIONS`), no branch of its own: an app is `new Hono()`, `route(prefix, app)` mounts, `basePath(prefix)` gives an app whose
routes, and the apps it mounts, are under the base path, and a verb returns its app; an app no one mounts is a root, as Express's.
The reader of a row is its section (`express`, `hono`).
"""
from __future__ import annotations

from collections import defaultdict

NAME = "express"
VERSION = "3"
# The libraries this module reads, each a section of `entry-queries.json` with its forms: the packages, the instances they make (`call`
# of a member, `new` of a class; `default` for the package's default export), the verb that mounts (`mount`), the one that builds a
# `route(path)` (`chain`), the one that gives an app under a base path (`prefix`), whether a verb returns its app (`chained`), the
# methods, and the stack's registry id (`id`). The query, the loader and the CommonJS exports are the JavaScript forms of `express`.
SECTIONS = ("express", "hono")
DEPTH = 24  # how many values one evaluation may follow (names, imports, exports, calls): a cycle ends there, unknown
PREFIXES = 64  # the prefixes one app or router may be mounted under: past them its routes are a gap


def _forms() -> dict:
    import entries
    return {section: entries.QUERIES[section] for section in SECTIONS}


def _unknown(cause: str) -> tuple:
    return ("unknown", cause)


class _Reader:
    """The values of one snapshot's JavaScript and TypeScript files, evaluated on demand and kept."""

    def __init__(self, facts, sections=SECTIONS):
        self.facts, every = facts, _forms()
        self.sections = {section: every[section] for section in sections}
        self.forms = every[NAME]  # the JavaScript forms: the query, the loader, the CommonJS exports
        self.packages = {package: section for section, forms in self.sections.items() for package in forms["packages"]}
        self.based: dict[tuple, str | None] = {}  # an app made by `prefix` (`basePath`): the base path of its routes, None if no literal
        self.trees, self.calls, self.exported = {}, {}, {}
        self.scopes: dict[str, set[str]] = {}
        self.values: dict[tuple, tuple] = {}
        self.busy: set[tuple] = set()
        self._sites: dict[str, list] = defaultdict(list)
        self._wanted: dict[str, set] = defaultdict(set)

    # ------------------------------------------------------------ files

    def files(self) -> list[str]:
        return sorted(file for file in self.facts.store.iter_paths() if self.facts.grammar(file) in self.forms)

    def tree(self, file: str):
        """The file's tree, its calls and its CommonJS exports (`module.exports = x`, `module.exports.n = x`, `exports.n = x`)."""
        import entries
        import flows
        if file not in self.trees:
            tree = self.facts.tree(file) if self.facts.grammar(file) in self.forms else None
            self.trees[file] = tree if isinstance(tree, flows.Tree) else None
            calls, exported = [], defaultdict(list)
            if self.trees[file] is not None:
                for captures in entries._matches(tree.source, tree.grammar, NAME, tree.root):
                    if "call" in captures:
                        calls += captures["call"]
                    for target, value in zip(captures.get("target", ()), captures.get("value", ())):
                        parts = self.parts(file, target)
                        written = self.forms["exports"]  # `module.exports`, and `exports` alone, each a name nothing binds
                        for head in (written, written[1:]):
                            if parts and parts[:len(head)] == head and len(parts) - len(head) <= 1 \
                                    and self.facts.bindings(file, self.scope(file, target), head[0])[1] == "unbound-name":
                                exported[parts[len(head)] if len(parts) > len(head) else None].append(value)
            self.calls[file] = sorted(calls, key=lambda node: node.start_byte)
            self.exported[file] = exported
        return self.trees[file]

    def parts(self, file: str, node) -> list[str] | None:
        """The names of a member chain written with names only (`module.exports.name`), else None."""
        import entries
        found = []
        while node is not None and node.type == "member_expression":
            name = node.child_by_field_name("property")
            if name is None or name.type != "property_identifier":
                return None
            found.insert(0, entries._text(self.trees[file].source, name))
            node = node.child_by_field_name("object")
        if node is None or node.type != "identifier":
            return None
        return [entries._text(self.trees[file].source, node), *found]

    def scope(self, file: str, node) -> str:
        """The innermost scope of the snapshot that holds a node: the first ancestor that starts a scope the snapshot records."""
        if file not in self.scopes:
            self.scopes[file] = {row[0] for row in self.facts.db.execute("SELECT id FROM sem_scopes WHERE file=?", (file,))}
        known = self.scopes[file]
        while node is not None:
            at = f"{node.start_point[0] + 1}:{node.start_point[1]}"
            for kind in ("block", "function", "class"):
                if f"scope-{kind}@{at}" in known:
                    return f"scope-{kind}@{at}"
            node = node.parent
        return "module"

    # ------------------------------------------------------------ values

    def value(self, file: str, node, depth: int = 0) -> tuple:
        """What an expression is, as a tuple: `("package", section, member)`, `("instance", kind, key, section)`, `("route", instance, path)`,
        `("function", id)`, `("param", function id, index)`, `("module", file)`, `("object", file, node)`, `("array", values)`,
        `("loader",)`, `("external", module)` (a value of a package outside the project), else `("unknown", cause)`."""
        import flows
        node = flows._unwrapped(node)
        if node is None:
            return _unknown("no expression")
        key = (file, node.start_byte, node.end_byte)
        if key in self.values:
            return self.values[key]
        if depth > DEPTH or key in self.busy:
            return _unknown("the value goes round, or further than the reader follows")
        self.busy.add(key)
        try:
            found = self._value(file, node, depth + 1)
        finally:
            self.busy.discard(key)
        self.values[key] = found
        return found

    def _value(self, file: str, node, depth: int) -> tuple:
        import entries
        tree = self.trees[file]
        if node.type == "identifier":
            return self.name(file, node, entries._text(tree.source, node), depth)
        if node.type == "member_expression":
            name = node.child_by_field_name("property")
            if name is None or name.type != "property_identifier":
                return _unknown("a computed member")
            return self.member(self.value(file, node.child_by_field_name("object"), depth), entries._text(tree.source, name), depth)
        if node.type == "call_expression":
            return self.call(file, node, depth)
        if node.type == "new_expression":
            held = self.value(file, node.child_by_field_name("constructor"), depth)
            made = self.made(held, "new", file, node)
            return made or (held if held[0] in ("unknown", "external") else _unknown(f"a new of a {held[0]}"))
        if node.type in entries.FUNCTIONS:
            written = self.facts.written_function(file, *entries._at(node))
            return ("function", written["id"]) if written else _unknown("a function the snapshot does not record")
        if node.type == "array":
            return ("array", [self.value(file, item, depth) for item in node.named_children if not item.is_extra])
        if node.type == "object":
            return ("object", file, node)
        return _unknown(f"a {node.type}")

    def name(self, file: str, node, name: str, depth: int) -> tuple:
        found, why = self.facts.bindings(file, self.scope(file, node), name)
        if found is None:
            return ("loader",) if name == self.forms["loader"] and why == "unbound-name" else _unknown(f"{name} is not bound ({why})")
        if len(found) != 1:
            return _unknown(f"{name} is bound more than once in its scope")
        return self.bound(file, found[0], depth)

    def bound(self, file: str, binding: tuple, depth: int) -> tuple:
        """What a binding of the snapshot holds: an import, a function, a parameter, a variable's value."""
        kind, value = binding
        if kind == "import":
            if value.get("type_only"):
                return _unknown("a type")
            if value["module"] in self.packages:
                return ("package", self.packages[value["module"]], None if value["mode"] in ("default", "namespace") else value["imported"])
            targets = self.facts.resolver.targets(file, value["module"])
            if not targets:
                return ("external", value["module"])
            if len(targets) > 1:
                return _unknown(f"the module {value['module']} resolves to {len(targets)} files of the project")
            return ("module", targets[0]) if value["mode"] == "namespace" else self.export(targets[0], value["imported"], depth)
        declaration = self.facts.declarations.get(value)
        if declaration is None:
            return _unknown("a declaration the snapshot does not record")
        if declaration["kind"] in ("function", "method"):
            return ("function", declaration["id"])
        if declaration["kind"] == "parameter":
            return self.parameter(declaration)
        if declaration["kind"] == "binding":
            return self.declared(declaration, depth)
        return _unknown(f"a {declaration['kind']}")

    def parameter(self, declaration: dict) -> tuple:
        """A parameter of a function, by its position among the function's parameters in the tree."""
        function = f"{declaration['file']}::{str(declaration['scope']).removeprefix('scope-')}"
        node = self.function(function) if function in self.facts.declarations else None
        if node is None:
            return _unknown("a parameter of no function the snapshot records")
        if node.child_by_field_name("parameter") is not None:  # `router => ...`
            return ("param", function, 0)
        listed = [item for item in node.child_by_field_name("parameters").named_children if not item.is_extra]
        at = (declaration["line"] - 1, declaration["column"])
        index = next((i for i, item in enumerate(listed) if item.start_point <= at < item.end_point), None)
        return ("param", function, index) if index is not None else _unknown("a parameter the tree does not place")

    def function(self, function: str):
        """The tree node of a function of the snapshot."""
        import entries
        declaration = self.facts.declarations[function]
        if self.tree(declaration["file"]) is None:
            return None
        span = declaration["span"]
        node = self.trees[declaration["file"]].root.descendant_for_point_range((span[0] - 1, span[1]), (span[2] - 1, span[3]))
        while node is not None and node.type not in entries.FUNCTIONS:
            node = node.parent
        return node

    def declared(self, declaration: dict, depth: int) -> tuple:
        """The value a variable is declared with: `const x = value`, or the member of the value a pattern takes (`const {x} = value`)."""
        import entries
        file = declaration["file"]
        tree = self.tree(file)
        if tree is None:
            return _unknown(f"no tree of {file}")
        at = (declaration["line"], declaration["column"])
        if at in tree.placed and tree.placed[at].parent.type == "variable_declarator":
            return self.value(file, tree.placed[at], depth)
        node = tree.root.named_descendant_for_point_range((at[0] - 1, at[1]), (at[0] - 1, at[1]))
        key = node
        if node is not None and node.parent is not None and node.parent.type == "pair_pattern":
            key = node.parent.child_by_field_name("key")
            node = node.parent
        pattern = node.parent if node is not None else None
        declarator = pattern.parent if pattern is not None and pattern.type == "object_pattern" else None
        if declarator is None or declarator.type != "variable_declarator" or declarator.child_by_field_name("name") != pattern:
            return _unknown(f"{declaration['name']} is no variable declared with a value")
        return self.member(self.value(file, declarator.child_by_field_name("value"), depth), entries._text(tree.source, key), depth)

    def member(self, held: tuple, name: str, depth: int) -> tuple:
        if held[0] == "package":
            return ("package", held[1], name) if held[2] is None else _unknown(f"a member of {held[2]}")
        if held[0] == "module":
            return self.export(held[1], name, depth)
        if held[0] == "object":
            return self.key(held[1], held[2], name, depth)
        return held if held[0] in ("unknown", "external") else _unknown(f"a member {name} of a {held[0]}")

    def key(self, file: str, node, name: str, depth: int) -> tuple:
        """The value an object literal gives a key: `{name: value}` or `{name}`."""
        import entries
        source = self.trees[file].source
        for item in node.named_children:
            if item.type == "shorthand_property_identifier" and entries._text(source, item) == name:
                return self.name(file, item, name, depth)
            if item.type == "pair" and (written := item.child_by_field_name("key")) is not None \
                    and written.type == "property_identifier" and entries._text(source, written) == name:
                return self.value(file, item.child_by_field_name("value"), depth)
        return _unknown(f"the object has no key {name}")

    def export(self, file: str, name: str, depth: int) -> tuple:
        """What a file of the project exports under a name: its export record (`sem_exports`), else `module.exports`."""
        if self.tree(file) is None:
            return _unknown(f"no tree of {file}")
        rows = list(self.facts.db.execute("SELECT payload FROM sem_exports WHERE file=? AND name=?", (file, name)))
        if len(rows) == 1:
            import semantic_store
            export = semantic_store._unpack(rows[0][0])
            if export.get("type_only"):
                return _unknown("a type")
            if export.get("module"):  # `export { x } from './y'`
                targets = self.facts.resolver.targets(file, export["module"])
                return self.export(targets[0], export["local"], depth + 1) if len(targets) == 1 else _unknown("a re-export that does not resolve")
            found, why = self.facts.bindings(file, "module", export["local"])
            return self.bound(file, found[0], depth + 1) if found and len(found) == 1 else _unknown(f"the export {name} ({why})")
        if rows:
            return _unknown(f"{file} exports {name} more than once")
        exported = self.exported[file]
        if name in exported and len(exported[name]) == 1:
            return self.value(file, exported[name][0], depth)
        if None in exported and len(exported[None]) == 1:
            return self.member(self.value(file, exported[None][0], depth), name, depth)
        return _unknown(f"{file} exports no single {name}")

    def loaded(self, file: str, node, depth: int) -> tuple:
        """What the loader gives (`require('x')`): the package, or `module.exports` of the one file the snapshot resolves the module to."""
        import entries
        arguments = [item for item in node.child_by_field_name("arguments").named_children if not item.is_extra]
        module = self.facts.literal(arguments[0], self.trees[file]) if len(arguments) == 1 else None
        if module is None:
            return _unknown("the loader's module is no literal")
        if module in self.packages:
            return ("package", self.packages[module], None)
        targets = self.facts.resolver.targets(file, module)
        if not targets:
            return ("external", module)
        if len(targets) > 1 or self.tree(targets[0]) is None:
            return _unknown(f"the module {module} resolves to no single file of the project")
        whole = self.exported[targets[0]].get(None, ())
        return self.value(targets[0], whole[0], depth) if len(whole) == 1 else ("module", targets[0])

    def made(self, held: tuple, how: str, file: str, node) -> tuple | None:
        """The app or router a `call` or a `new` of a package's value makes, by the data of its section; else None."""
        if held[0] != "package":
            return None
        kind = self.sections[held[1]]["instances"].get(how, {}).get(held[2] or "default")
        return ("instance", kind, (file, node.start_byte), held[1]) if kind else None

    def call(self, file: str, node, depth: int) -> tuple:
        import entries
        callee = node.child_by_field_name("function")
        held = self.value(file, callee, depth)
        if held == ("loader",):
            return self.loaded(file, node, depth)
        if (made := self.made(held, "call", file, node)) is not None:
            return made
        if callee.type == "member_expression":
            verb = entries._text(self.trees[file].source, callee.child_by_field_name("property"))
            receiver = self.value(file, callee.child_by_field_name("object"), depth)
            forms = self.sections[receiver[3]] if receiver[0] == "instance" else {}
            arguments = [item for item in node.child_by_field_name("arguments").named_children if not item.is_extra]
            if verb == forms.get("chain") or receiver[0] == "param" and verb in {f.get("chain") for f in self.sections.values()}:
                return ("route", receiver, self.path(file, arguments[0]) if arguments else None)
            if verb == forms.get("prefix"):  # `basePath(p)`: another app, whose routes are under the base path
                own, written = self.based.get(receiver[2], ""), self.path(file, arguments[0]) if arguments else None
                self.based[(file, node.start_byte)] = None if own is None or written is None else _join(own, written)
                return ("instance", receiver[1], (file, node.start_byte), receiver[3])
            if forms.get("chained") and (verb in forms["methods"] or verb == forms["mount"]):
                return receiver  # `app.get(p, h).post(p2, h2)`: the verb returns the app
            if receiver[0] == "route" and any(verb in f["methods"] for f in self.sections.values()):
                return receiver  # `route(path).get(h).post(h2)`: each verb on the same route
        if held[0] == "function":  # a function that builds an app or a router: what it returns
            returned = self.returned(held[1], depth)
            return returned if returned[0] in ("instance", "route") else _unknown("the value a function returns")
        return held if held[0] in ("unknown", "external") else _unknown(f"a call of a {held[0]}")

    def returned(self, function: str, depth: int) -> tuple:
        """The one value a function returns: its `return` statements, all of one value, not those of the functions inside it."""
        import entries
        file, node = self.facts.declarations[function]["file"], self.function(function)
        body = node.child_by_field_name("body") if node is not None else None
        if body is None:
            return _unknown("a function with no body")
        if body.type != "statement_block":
            return self.value(file, body, depth)
        found, stack = [], list(body.named_children)
        while stack:
            item = stack.pop()
            if item.type == "return_statement" and item.named_children:
                found.append(self.value(file, item.named_children[0], depth))
            elif item.type not in entries.FUNCTIONS:
                stack.extend(item.named_children)
        return found[0] if found and all(item == found[0] for item in found) else _unknown("a function with no single returned value")

    def path(self, file: str, node) -> str | None:
        """A literal path, the text the call writes or the constant it names; None for a computed one (a template with a hole)."""
        import flows
        node = flows._unwrapped(node)
        if node is None or node.type == "template_string" and any(c.type == "template_substitution" for c in node.named_children):
            return None
        return self.facts.literal(node, self.trees[file])

    # ------------------------------------------------------------ parameters: the arguments of the calls to a function

    def sites(self, function: str) -> list[tuple]:
        """`(file, call node)` of each call whose callee is the function, evaluated where its last name is the function's name."""
        import entries
        name = self.facts.declarations[function]["name"]
        if function not in self._wanted[name]:
            self._wanted[name].add(function)
            for file in self.files():
                if self.tree(file) is None:
                    continue
                for node in self.calls[file]:
                    callee = node.child_by_field_name("function")
                    last = callee.child_by_field_name("property") if callee.type == "member_expression" else callee
                    if last is not None and entries._text(self.trees[file].source, last) == name \
                            and self.value(file, callee) == ("function", function):
                        self._sites[function].append((file, node))
        return self._sites[function]

    def instances(self, value: tuple) -> list[tuple]:
        """The apps or routers a receiver is: itself, or, for a parameter, the argument of each call to its function."""
        if value[0] == "instance":
            return [value]
        if value[0] != "param":
            return []
        found = []
        for caller, node in self.sites(value[1]):
            arguments = [item for item in node.child_by_field_name("arguments").named_children if not item.is_extra]
            if value[2] < len(arguments):
                given = self.value(caller, arguments[value[2]])
                found += [given] if given[0] == "instance" else []
        return found


def _flat(value: tuple) -> list[tuple]:
    return [item for inner in value[1] for item in _flat(inner)] if value[0] == "array" else [value]


def _join(prefix: str, path: str) -> str:
    if path in ("", "/"):
        return prefix or "/"
    return prefix.rstrip("/") + path if prefix else path


def rows(facts, sections=SECTIONS) -> list[dict]:
    """The routes of the snapshot's apps of `sections` (Express, Hono), each a row the binder ties by the span of its handler, or a gap
    with the cause. The reader of a row is its section."""
    import entries
    import flows
    reader = _Reader(facts, sections)
    verbs = {verb for forms in reader.sections.values() for verb in (forms["mount"], *forms["methods"])}
    routes, mounts, created = [], defaultdict(list), {}
    for file in reader.files():
        if reader.tree(file) is None:
            continue
        source = reader.trees[file].source
        for node in reader.calls[file]:
            callee = node.child_by_field_name("function")
            if callee.type != "member_expression" or (verb := callee.child_by_field_name("property")) is None:
                continue
            verb = entries._text(source, verb)
            if verb not in verbs:
                continue
            receiver = reader.value(file, callee.child_by_field_name("object"))
            site = f"{file}:{entries._at(node)[0]}"
            arguments = [item for item in node.child_by_field_name("arguments").named_children if not item.is_extra]
            chained = receiver[0] == "route"
            places = reader.instances(receiver[1] if chained else receiver)
            for place in places:  # none: not an app or a router of these libraries (a map's `get`, an HTTP client's `post`)
                created.setdefault(place[2], place[1])
            for section in sorted({place[3] for place in places}):
                forms, here = reader.sections[section], [place for place in places if place[3] == section]
                if verb == forms["mount"]:
                    if not chained:
                        _mount(reader, file, arguments, here, site, mounts, created)
                    continue
                if verb not in forms["methods"] or chained and not forms.get("chain"):
                    continue
                written, handlers = (receiver[2], arguments) if chained else \
                    (reader.path(file, arguments[0]) if arguments else None, arguments[1:])
                if not handlers:  # one argument alone: Express's getter of a setting, `app.get('env')`
                    continue
                handler = (_flat(reader.value(file, handlers[-1])) or [_unknown("an empty array")])[-1]
                routes += [{"place": place[2], "reader": section, "method": forms["methods"][verb], "path": written,
                            "base": reader.based.get(place[2], ""), "shape": "route" if chained else "method", "site": site,
                            "handler": handler, "file": file} for place in here]
    reached = _prefixes(created, mounts)
    out = []
    for route in routes:
        base = {"reader": route["reader"], "shape": route["shape"], "kind": "rotta", "method": route["method"],
                "symbol": f"{route['file']}::{flows.MODULE}", "site": route["site"]}
        handler, (prefixes, causes) = route["handler"], reached.get(route["place"], ([], ["a router no app mounts"]))

        def gap(why: str, path=route["path"]):
            written = "(computed)" if path is None else path
            return {**base, "path": path, "gap": f"{route['reader']} route {route['method'] or 'ANY'} {written}: {why}"}

        if route["path"] is None:
            out.append(gap("the path is no literal"))
        elif route["base"] is None:
            out.append(gap("the base path of its app is no literal"))
        elif handler[0] != "function":
            out.append(gap("the handler is no function of the snapshot: " + (handler[1] if handler[0] == "unknown" else f"a {handler[0]}")))
        else:
            declaration = facts.declarations[handler[1]]
            for prefix in prefixes:
                path = _join(prefix, _join(route["base"], route["path"]))
                out.append({**base, "path": path, "schema": flows.path_schema(path),
                            "site": f"{declaration['file']}:{declaration['line']}", "span": list(declaration["span"]),
                            "registered": route["site"]})
            out += [gap(cause) for cause in causes]
    return sorted(out, key=lambda row: (row["site"], row["path"] or "", row["method"] or "", row.get("gap", "")))


def _mount(reader, file: str, arguments: list, places: list, site: str, mounts: dict, created: dict) -> None:
    """`x.use(prefix?, ...children)`: each child that is an app or a router (in an array too, or a parameter's argument) is mounted on
    each of `places` under the literal prefix, under none where the first argument is already a handler or a router, or under an
    unknown one (None) where the first argument is a value that is neither: a path the reader cannot read."""
    import flows
    first = reader.value(file, arguments[0]) if arguments else None
    written = reader.path(file, arguments[0]) if arguments else None
    if written is not None:
        prefix, children = written, arguments[1:]
    elif first is not None and first[0] == "unknown" and flows._unwrapped(arguments[0]).type != "call_expression":
        prefix, children = None, arguments[1:]  # a call's value is a handler (`cors()`), never a path; so is a package's value
    else:
        prefix, children = "", arguments
    for argument in children:
        for child in (found for item in _flat(reader.value(file, argument)) for found in reader.instances(item)):
            created.setdefault(child[2], child[1])
            mounts[child[2]] += [(place[2], _based(reader.based.get(place[2], ""), prefix), site) for place in places]


def _based(base: str | None, prefix: str | None) -> str | None:
    """The prefix a mount on an app with a base path gives (Hono's `route` on a `basePath` app): under the base too; None if unknown."""
    if not base:
        return None if base is None else prefix
    return None if prefix is None else _join(base, prefix)


def _prefixes(created: dict, mounts: dict) -> dict:
    """By app or router: `(prefixes, causes)`, the prefixes it is reached under from the apps no one mounts, and why some of its
    routes have none: a mount under a prefix that is no literal, no app that reaches it, too many prefixes."""
    children = defaultdict(lambda: defaultdict(set))
    for child, given in mounts.items():
        for parent, prefix, _ in given:
            children[parent][child].add(prefix)
    found = defaultdict(list)

    def walk(place, prefix, seen):
        if prefix in found[place] or len(found[place]) > PREFIXES:
            return
        found[place].append(prefix)
        for child, given in sorted(children[place].items()):
            for written in sorted(item for item in given if item is not None):
                if child not in seen:
                    walk(child, _join(prefix, written) if written else prefix, seen | {child})

    for place, kind in sorted(created.items()):
        if kind == "app" and place not in mounts:
            walk(place, "", {place})
    out = {}
    for place in created:
        unknown = sorted({site for _, prefix, site in mounts.get(place, ()) if prefix is None})
        causes = [f"mounted under a prefix that is no literal at {', '.join(unknown)}"] if unknown else []
        if len(found[place]) > PREFIXES:
            out[place] = ([], [f"mounted under more than {PREFIXES} prefixes"])
        elif found[place] or causes:
            out[place] = (found[place], causes)
        else:
            out[place] = ([], ["mounted by no app the reader reaches" if place in mounts else "a router no app mounts"])
    return out
