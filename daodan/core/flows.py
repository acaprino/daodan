#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Flows of a snapshot: links deduced from the project's link rules, then followed.

A model writes the rules once per project (`daodan/flow-rules/v1`); this module only
applies them, so the same snapshot and rules always give the same links. A rule
says where a construct is and what it means.

Where, one of:

- `callee`: `file::name`, a project function the call resolves to, or a value of that
  name declared there and called by its name (a store hook a library creates).
- `written`: the callee as written, dotted, for calls that go through a library
  object (`router.post`, `db.*.find_one|find`); `*` is any part, `|` separates
  alternatives. `in` restricts it to directories or single files.
- `attribute`: a markup attribute bound to a handler (`on*`), within `in`.

What (`link`):

- `scrive` / `legge`: a store access. `key` is `argN`, `partN` (a written part),
  `selector` (`s => s.field`), `object` (`{field: ...}`, also returned by a function
  argument), `member` (the property read on the call's result) or `holder` (the
  call is made on a handle assigned in the same file as `handle = store.key` or
  `handle = store[KEY]`: a variable the snapshot's scopes bind to that assignment, or an
  attribute of `self` or `this` that the class assigns so, or on `store[KEY]` itself
  (`db[COLLECTION].find()`, `get_db()[COLLECTION].find()`); KEY is a text or a constant bound
  to one; a receiver with no such assignment is not this store, one the snapshot does not
  resolve is a gap, and so is an index that is no such text, with its own cause: computed,
  imported and linked to no declaration, `module.NAME`, `self.NAME`). With `actions_in`
  a key naming a function declared as a property under those prefixes is a call to
  it, also through the variable that holds it.
- `rotta` / `offre`: a route reached or declared; `route` gives `service`, `method`,
  `path`, each a literal, `argN`, `partN`, `argN.argM` (an argument of the call written
  as argument N: `fetch(apiPath('/x'))`) or `argN.key` (a key of the object written there:
  `{method: 'POST'}`), with `|value` for when that argument or key is absent. `strip`, a field of the rule beside
  `route`, removes a leading text from the path. The path is read as a schema (`REST`): query
  and base URL are cut, each parameter is `{}`, a template counts. With `decorates` the route
  belongs to the decorated function; with `handler` (`argN` or `last`) to the
  function passed there, named or written in place (then named by its route,
  `METHOD path`), as when a route is registered outside any function.
- `attiva`: a user action bound to the handler in `handler` (`argN` or `last`), or to
  the handler an `attribute` names.
- `ingresso`: an entry point of kind `entry`; with `decorates`, the decorated function.

A store rule may name the store's `node_type`, from the closed list of the flow model
(`database`, `coda`, ...): the explorer draws the store with that type's icon.

A call is read from its file's syntax tree (`Tree`), its arguments, the keys of an object
and the assignment of a name from the nodes and the snapshot's own resolution of names, never
from the lines of the file; where the tree cannot be read (the file changed since the snapshot,
a grammar that does not load) the rule yields a gap for that call, with the cause.
A value counts only when it is a literal or a constant bound to one; a computed
one is a gap, never a guess. A store link needs the same store and key, a route
link the same service and method and a path schema that meets: the most literal
route wins, a tie is an uncertain link, a gap with its candidates. A route Noir or Next.js declares (a route
handler, not a page, on a function the snapshot resolves) is offered too, with the service `*`: it meets a call of
any service, and a route of the call's own service, from a rule, comes before it; a catch-all path is a gap. The services of others the brief lists (the
stack step's technologies and the external modules of the module graph, by id) are nodes too: a symbol in a file
a service cites as evidence uses it (`dichiarato`), except in a file where an engine resolved a call into a package
the stack step ties to that service: there the function that makes such a call uses it, once per service and at its
first call (`dedotto`, with the engine's resolver); a call in a test file is no use, and is counted in the service's
`in_tests`. Code outside
any named function, a callback passed as an argument included, belongs to its module,
the node `file::<module>`; a route it declares or an entry point needs a named function.
A component written as an element (`<Paywall />`) is called by the function that writes it.

    python flows.py links MANIFEST --rules RULES
    python flows.py trace MANIFEST --rules RULES (--from NODE | --to NODE | --through NODE)
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from functools import cache, cached_property
from pathlib import Path, PurePosixPath
from typing import Callable, NamedTuple
from urllib.parse import urlsplit

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import binder  # noqa: E402
import edge_view  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

RULES_SCHEMA = "daodan/flow-rules/v1"
LINKS_SCHEMA = "daodan/flow-links/v4"  # callee-based effects inherit sampled or conflicting evidence
FLOW_SCHEMA = "daodan/flow/v1"
LINKS = ("scrive", "legge", "rotta", "offre", "attiva", "ingresso")
MAX_EDGES = 5000
MODULE = "<module>"  # the node of the code a file runs outside any named function
# The ecosystem of the stack step's packages for the manager an engine's symbols name (SCIP's `scheme manager package
# version`): scip-python writes `python`, scip-typescript `npm`, scip-java `maven`, scip-go `gomod`, rust-analyzer
# `cargo`, scip-dotnet `nuget`.
ECOSYSTEMS = {"python": "pypi", "npm": "npm", "maven": "maven", "gomod": "go", "cargo": "crates", "nuget": "nuget"}
_FIELDS = {"callee", "written", "attribute", "in", "link", "store", "key", "actions_in", "route", "strip",
           "decorates", "handler", "entry", "node_type"}
NODE_TYPES = ("attore", "schermata", "funzionalità", "servizio o API", "gateway", "database", "coda",
              "autenticazione", "dispositivo", "filesystem", "altro")
# A rule's own fields (`arg0`, `part1`, `arg1.method|GET`), not source text.
_ARG = re.compile(r"(arg|part)(\d+)$")
_NESTED = re.compile(r"arg(\d+)\.(arg\d+|[A-Za-z_$][\w$]*)(?:\|(.*))?$")
TREES = 64  # the syntax trees `Facts` keeps at once, the oldest dropped first: a file is read in runs
DYNAMIC = "(expr)"  # the part the snapshot writes for a receiver that is no name: `items().find()`
# The nodes of the grammars the rules read (JavaScript, TypeScript, Python), as `entries.py` names the ones it reads.
NAMES = ("identifier", "shorthand_property_identifier")  # a variable, `{ method }`
OBJECTS = ("object", "dictionary")
SPREADS = ("spread_element", "dictionary_splat")
MEMBERS = ("member_expression", "attribute")
SUBSCRIPTS = ("subscript_expression", "subscript")
LAMBDAS = ("arrow_function", "lambda")  # what a selector is written as
ASSIGNMENTS = ("variable_declarator", "assignment_expression", "assignment")  # where a name is given a value
WRAPPERS = ("parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression",
            "await_expression", "await")  # what only wraps an expression: its value is the inner one's


def _dotted(node) -> bool:
    """Whether a node is a name, or a dotted name all the way down: `handler`, `module.handler`, `self.rows`."""
    while node is not None and node.type in MEMBERS:
        node = node.child_by_field_name("object")
    return node is not None and node.type in ("identifier", "this")


def _unwrapped(node):
    """The expression inside what only wraps it: parentheses, a type assertion, `await`."""
    while node is not None and node.type in WRAPPERS:
        node = next((child for child in node.named_children if not child.is_extra), None)
    return node



# ---------------------------------------------------------------- rules

def load_rules(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != RULES_SCHEMA or not isinstance(payload.get("rules"), list):
        raise ValueError(f"rules must be {RULES_SCHEMA} with a rules list")
    return validate_rules(payload["rules"], recorded=True)


def validate_rules(rules: list, *, recorded=False) -> list[dict]:
    decisions = {}
    for index, rule in enumerate(rules):
        where = f"rule {index}"
        if not isinstance(rule, dict) or rule.get("link") not in LINKS:
            raise ValueError(f"{where}: link must be one of {', '.join(LINKS)}")
        if "shape" in rule or "reader" in rule:
            import entries
            import premap
            if rule.get("source") != "modello":
                raise ValueError(f"{where}: supplied classifications must have source modello; registry decisions come from Daodan")
            if set(rule) != {"link", "reader", "shape", "entry", "source"} or rule["link"] != "ingresso" or (
                    rule["reader"] not in (entries.ATTRIBUTE, entries.ARGUMENT, entries.DECORATOR, entries.NOIR, entries.MANIFEST,
                                             *(source.NAME for source in (*premap.FRAMEWORK_SOURCES, *premap.TEMPLATE_SOURCES)))
                    or not isinstance(rule["shape"], str) or not rule["shape"]
                    or rule["entry"] not in (*entries.ENTRY_KINDS, entries.NO_ENTRY)):
                raise ValueError(f"{where}: invalid shape classification or entry kind")
            key = (rule["reader"], rule["shape"])
            if key in decisions and decisions[key] != rule["entry"]:
                raise ValueError(f"{where}: conflicting classifications of {key}")
            decisions[key] = rule["entry"]
            continue
        places = [name for name in ("callee", "written", "attribute") if isinstance(rule.get(name), str)]
        if len(places) != 1:
            raise ValueError(f"{where}: exactly one of callee, written, attribute")
        if places == ["callee"] and "::" not in rule["callee"]:
            raise ValueError(f"{where}: callee must be file::name")
        if places == ["attribute"] and rule["link"] != "attiva":
            raise ValueError(f"{where}: an attribute rule is an attiva link")
        need = {"scrive": ("store", "key"), "legge": ("store", "key"), "rotta": ("route",), "offre": ("route",),
                "attiva": () if places == ["attribute"] else ("handler",), "ingresso": ("entry",)}[rule["link"]]
        missing = [name for name in need if not rule.get(name)]
        if missing:
            raise ValueError(f"{where}: {rule['link']} needs {', '.join(missing)}")
        if rule["link"] == "ingresso" and not recorded:
            import entries
            # These two spellings are stored in maps and v1 rule files predating the ten entry kinds.
            if rule["entry"] not in (*entries.ENTRY_KINDS, "azione", "lavoro pianificato"):
                raise ValueError(f"{where}: unknown entry kind {rule['entry']!r}")
        if rule["link"] in ("rotta", "offre") and set(rule["route"]) != {"service", "method", "path"}:
            raise ValueError(f"{where}: route has exactly service, method and path")
        if rule["link"] in ("rotta", "offre") and rule["route"]["service"] == ANY_SERVICE:
            raise ValueError(f"{where}: the service {ANY_SERVICE} is reserved for the routes Noir and Next.js declare: "
                             "a rule names the service of its route")
        if "handler" in rule:
            # `handler` is a field of the rule (`arg1`, `last`), not source text.
            if rule["link"] not in ("offre", "attiva") or not re.fullmatch(r"arg\d+|last", str(rule["handler"])):
                raise ValueError(f"{where}: handler is argN or last, on an offre or attiva rule")
            if rule.get("decorates"):
                raise ValueError(f"{where}: handler or decorates, not both")
        unknown = sorted(set(rule) - _FIELDS)
        if unknown:
            raise ValueError(f"{where}: unknown field {', '.join(unknown)}")
        if "node_type" in rule and (rule["link"] not in ("scrive", "legge") or rule["node_type"] not in NODE_TYPES):
            raise ValueError(f"{where}: node_type belongs to a store rule and is one of {', '.join(NODE_TYPES)}")
    return rules


def _under(file: str, prefixes) -> bool:
    return not prefixes or any(p == "." or file == p or file.startswith(p.rstrip("/") + "/") for p in prefixes)


def _written(rule: dict, parts: list[str], file: str) -> bool:
    pattern = rule["written"].split(".")
    return (len(pattern) == len(parts) and _under(file, rule.get("in"))
            and all(want == "*" or part in want.split("|") for want, part in zip(pattern, parts)))


# ---------------------------------------------------------------- source

class Source:
    """Verified text of the snapshot's files: a file edited since the snapshot is a gap."""

    def __init__(self, store):
        self.store = store
        self.root = Path(store["root"])
        self.cache: dict[str, list[str] | None] = {}

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self.cache:
            entry = self.store.get_file(rel, semantic=False) or {}
            try:
                text = (self.root / rel).read_bytes().decode("utf-8", errors="replace")
                text = text.replace("\r\n", "\n").replace("\r", "\n")
            except OSError:
                text = None
            self.cache[rel] = text.split("\n") if text is not None and snapshot.hash_text(text) == entry.get("hash") else None
        return self.cache[rel]


class Tree:
    """A file's verified text with its syntax tree and its grammar: what a rule reads a call, a value or a handle from."""

    def __init__(self, file: str, source: bytes, root, grammar: str):
        self.file, self.source, self.root, self.grammar = file, source, root, grammar

    @cached_property
    def assigned(self) -> list[tuple[str, tuple[int, int], object]]:
        """Where the file gives a name a value, `(name, (line, column), value node)`: `name = value`,
        `const name = value`; not a keyword argument, a default or an operand."""
        import entries
        return [item for item in entries._assignments({}, self.file, self.source, self.root)
                if item[2].parent.type in ASSIGNMENTS]

    @cached_property
    def placed(self) -> dict[tuple[int, int], object]:
        """The value given at each place `assigned` lists."""
        return {at: value for _, at, value in self.assigned}



# ---------------------------------------------------------------- snapshot facts

class Facts:
    def __init__(self, store, db, view: dict | None = None):
        """References are read only through the snapshot's edge view (`view`, loaded when not given)."""
        self.store, self.db = store, db
        view = view if view is not None else edge_view.load_edge_view(store)
        self.source = Source(store)
        self.declarations = {row[0]: {"id": row[0], "file": row[1], "name": row[2], "kind": row[3],
                                      "line": row[4], "column": row[5], "end": row[6], **_unpack(row[7])}
                             for row in db.execute("SELECT id,file,name,kind,l0,c0,l1,payload FROM sem_declarations")}
        self.functions = defaultdict(list)
        self.by_name = defaultdict(list)
        for declaration in self.declarations.values():
            if declaration["kind"] in ("function", "method"):
                self.functions[declaration["file"]].append(declaration)
            if declaration.get("scope") == "module":
                self.by_name[declaration["name"]].append(declaration)
        self.resolver = semantic_store._Resolver(db)
        self._trees: dict[str, Tree | str] = {}  # a file's tree, else why it has none
        self._grammars: dict[str, str | None] = {}
        self.reads = defaultdict(list)
        self.uses = defaultdict(list)  # the reads and the calls of a file
        for ref in view["reads"]:
            span = ref.get("span") or [None, None]
            self.reads[(ref["file"], span[0], span[1])].append(ref)
            self.uses[ref["file"]].append(ref)
        self.called = defaultdict(list)
        self.calls_at = defaultdict(list)  # the calls the snapshot records, by where their callee starts
        self.native_dispatch_callers = {r["caller"] for r in view["references"] if "tauri_command" in r}
        for ref in view["references"]:
            span = ref.get("span") or [None, None]
            self.calls_at[(ref["file"], span[0], span[1])].append(ref)
            self.uses[ref["file"]].append(ref)
            # Even an unknown second call prevents an inline callback from
            # being identified with its one supposedly unique destination.
            self.called[ref["caller"]].append(
                ref["target_id"] if ref["resolution"] == "resolved" and not edge_view.uncertainty(ref) else None)
        self.imports = defaultdict(set)
        for source, target in db.execute("SELECT source,target FROM sem_edges"):
            self.imports[source].add(target)
        # The names a file imports from a file of the project, and (file, name) -> module for those it imports from
        # outside it: a package's name is the package's, never a function of the project that happens to share it.
        project = set(db.execute("SELECT file,module FROM sem_modules"))
        self.imported, self.outside = defaultdict(set), {}
        for file, name, payload in db.execute("SELECT file,name,payload FROM sem_bindings WHERE kind='import'"):
            module = _unpack(payload).get("module")
            if (file, module) in project:
                self.imported[file].add(name)
            else:
                self.outside[file, name] = module or "another module"
        self._nodes: dict[str, str | None] = {}
        self.route_named: dict[str, str] = {}  # a function written in place as a route handler: its route

    def targets(self, name: str, file: str, line: int, column: int, kinds: tuple) -> list[str]:
        """Declarations an identifier names: its resolved read, else the one module-level
        declaration of that name in the file or in a file it imports, else the only one
        in the project when the file imports that name."""
        at = self.reads.get((file, line, column), ())
        if any(edge_view.uncertainty(ref) for ref in at):
            return []
        resolved = [ref["target_id"] for ref in at
                    if self.declarations.get(ref.get("target_id") or "", {}).get("kind") in kinds]
        if resolved:
            return resolved
        named = [d for d in self.by_name.get(name, ()) if d["kind"] in kinds]
        near = [d["id"] for d in named if d["file"] == file or d["file"] in self.imports.get(file, ())]
        if len(near) == 1:
            return near
        return [named[0]["id"]] if len(named) == 1 and name in self.imported.get(file, ()) else []

    def file_function(self, name: str, file: str) -> str | None:
        """The one function or method of that name declared at module level in `file` itself; None when there is none
        or several, or when the file's script has a binding of that name (an import, a destructured variable): what a
        template names then is that binding, not a method of some object. A template's expression names what its
        reference resolves to, or what its own script defines (an Options API method), never a function another
        file declares."""
        if self.db.execute("SELECT 1 FROM sem_bindings WHERE file=? AND scope='module' AND name=?", (file, name)).fetchone():
            return None
        found = [d for d in self.by_name.get(name, ()) if d["file"] == file and d["kind"] in ("function", "method")
                 and not d.get("contract")]
        return self.node(found[0]["id"]) if len(found) == 1 else None

    def tree(self, file: str) -> Tree | str:
        """A file's tree, read once and kept while its neighbours are read; else why it has none: `""` when the file
        is not the snapshot's text any more, else that no grammar is known for it or that its grammar did not load."""
        if file not in self._trees:
            import entries
            if len(self._trees) >= TREES:
                del self._trees[next(iter(self._trees))]
            source, grammar = entries._file(self, file, template=False)
            if grammar is None:
                self._trees[file] = "" if self.source.lines(file) is None else f"no grammar is known for {file}"
            elif (root := entries._parse(source, grammar)) is None:
                failure = entries._treesitter.load_failure(grammar)
                self._trees[file] = f"grammar {grammar} not loaded" + (f": {failure}" if failure else "")
            else:
                self._trees[file] = Tree(file, source, root, grammar)
        return self._trees[file]

    def grammar(self, file: str) -> str | None:
        """The grammar the snapshot read a file with."""
        if file not in self._grammars:
            profile = (self.store.get_file_header(file) or {}).get("parser_profile") or {}
            self._grammars[file] = profile.get("grammar")
        return self._grammars[file]

    @cached_property
    def classes(self) -> dict[str, list[dict]]:
        import entries
        return entries._classes(self)

    def bindings(self, file: str, scope: str | None, name: str) -> tuple[list[tuple] | None, str | None]:
        """Every binding of a name in the nearest scope of the snapshot that binds it, seen from `scope`: `(kind, id)` of
        a declaration or `(kind, payload)` of an import; more than one where the scope binds the name again. None and
        why where no scope does, or the snapshot did not resolve a scope (`_Resolver.lexical`, which gives up there)."""
        while scope:
            record = self.resolver.scope_record(file, scope)
            if record is None or record.get("unresolved"):
                return None, "scope-missing" if record is None else "scope-unresolved"
            if found := self.resolver.bindings_named(file, scope, name):
                return found, None
            scope = record.get("parent")
        return None, "unbound-name"

    def bound(self, file: str, scope: str | None, name: str) -> tuple | None:
        """What the snapshot's scopes bind a name to when they bind it once: `("declaration", id)` or `("import", ...)`."""
        found, _ = self.bindings(file, scope, name)
        return found[0] if found and len(found) == 1 else None

    def element(self, file: str, span: list) -> bool:
        """Whether the read at `span` is the name of an element's tag (`<Paywall />`), in a file of JSX."""
        import entries
        tree = self.tree(file) if self.grammar(file) in entries.JSX_GRAMMARS else None
        if not isinstance(tree, Tree):
            return False
        node = tree.root.named_descendant_for_point_range((span[0] - 1, span[1]), (span[2] - 1, span[3]))
        return node.parent is not None and node.parent.type in entries.JSX_TAGS \
            and node.parent.child_by_field_name("name") == node

    def property_label(self, declaration: dict) -> str | None:
        """The property an anonymous function is the value of: `name: (...) => ...`."""
        import entries
        tree = self.tree(declaration["file"])
        if not isinstance(tree, Tree) or not declaration.get("span"):
            return None
        span = declaration["span"]
        node = tree.root.descendant_for_point_range((span[0] - 1, span[1]), (span[2] - 1, span[3]))
        pair = node.parent if node.type in (*entries.FUNCTIONS, "lambda") else None
        if pair is None or pair.type != "pair" or pair.child_by_field_name("value") != node:
            return None
        return _key_name(pair.child_by_field_name("key"), tree)

    def node(self, declaration_id: str | None) -> str | None:
        """The named symbol a declaration belongs to. An anonymous function counts as the
        property it is the value of, inside its owner, or as its owner."""
        if declaration_id not in self._nodes:
            declaration, labels = self.declarations.get(declaration_id or ""), []
            while declaration is not None and declaration["name"] == "(anonymous)" \
                    and declaration["id"] not in self.route_named:
                label = self.property_label(declaration)
                if label:
                    labels.insert(0, label)
                scope = str(declaration.get("scope") or "")
                declaration = self.declarations.get(f"{declaration['file']}::{scope.removeprefix('scope-')}")
            name, file = None, declaration_id.split("::", 1)[0] if declaration_id else None
            if declaration is not None:
                base = self.route_named.get(declaration["id"]) or \
                    (declaration.get("qualified_name") or declaration["name"]).replace(".(anonymous)", "")
                name = f"{file}::{'.'.join([base, *labels])}"
            elif labels:
                # Properties of an object no named function holds: a store created at module level.
                name = f"{file}::{'.'.join(labels)}"
            self._nodes[declaration_id] = name
        return self._nodes[declaration_id]

    def named(self, declaration_id: str | None) -> str | None:
        declaration = self.declarations.get(declaration_id or "")
        if declaration is None:
            return None
        return f"{declaration['file']}::{declaration.get('qualified_name') or declaration['name']}"

    def enclosing(self, file: str, line: int, skip: str | None = None, *, column: int | None = None) -> dict | None:
        """The innermost named function whose lines hold `line`."""
        holders = [d for d in self.functions.get(file, ()) if d["name"] != "(anonymous)" and d["id"] != skip
                   and d["line"] <= line <= (d["end"] or d["line"])
                   and (column is None or tuple(d["span"][:2]) <= (line, column) < tuple(d["span"][2:]))]
        return max(holders, key=lambda d: (d["line"], d["column"])) if holders else None

    def decorated(self, file: str, line: int) -> str | None:
        """The function a decorator on this line decorates: the first declaration below it."""
        below = sorted((d for d in self.declarations.values()
                        if d["file"] == file and d["kind"] in ("function", "class", "method") and d["line"] > line),
                       key=lambda d: d["line"])
        return self.node(below[0]["id"]) if below else None

    def constants(self, name: str, file: str, line: int, column: int) -> list[dict]:
        """The declarations of the variable a name written at a place stands for: the one the snapshot's read of
        it names (`binding_id`: a parameter that shares the name of a constant is no constant); where the read is
        an import, or the snapshot records none, the module-level one of that name (`targets`)."""
        reads = self.reads.get((file, line, column), ())
        named = [self.declarations.get(ref["binding_id"]) for ref in reads if ref.get("binding_id")]
        if named:
            return [d for d in named if d and d["kind"] == "binding"]
        if reads and not any(ref.get("imported_name") for ref in reads):
            return []
        return [self.declarations[target] for target in self.targets(name, file, line, column, ("binding",))]

    def literal(self, node, tree: Tree) -> str | None:
        """The text of a string literal, or of a constant bound to one; None when computed: a concatenation, a
        parameter, a name the snapshot does not resolve. A template keeps its `${...}` parts for the caller to
        accept or refuse."""
        import entries
        node = _unwrapped(node)
        if node is None:
            return None
        found = entries._string(node, tree.source, tree.grammar, exact=True)
        if found is not None or not (node.type in NAMES or node.type in MEMBERS and _dotted(node)):
            return found
        for declaration in self.constants(entries._text(tree.source, node), tree.file, *entries._at(node)):
            home = self.tree(declaration["file"])
            value = _unwrapped(home.placed.get((declaration["line"], declaration["column"]))) if isinstance(home, Tree) else None
            found = entries._string(value, home.source, home.grammar, exact=True) if value is not None else None
            if found is not None:
                return found
        return None

    def handler(self, node, source: bytes, file: str) -> str | None:
        """The function an action argument names, directly or as the one call of an arrow."""
        import entries
        line, column = entries._at(node)
        if node.type == "identifier":
            found = self.targets(entries._text(source, node), file, line, column, ("function", "method"))
            return self.node(found[0]) if found else None
        arrow = next((d for d in self.functions.get(file, ()) if d["line"] == line
                      and d["column"] == column and d["name"] == "(anonymous)"), None)
        if arrow is None:
            return None
        if self._nodes.get(arrow["id"]) == arrow["id"]:
            return arrow["id"]
        calls = self.called.get(arrow["id"], [])
        return self.node(calls[0]) if len(calls) == 1 else None

    def written_function(self, file: str, line: int, column: int) -> dict | None:
        """The function written at this place of an argument, named or not."""
        return next((d for d in self.functions.get(file, ()) if d["line"] == line and d["column"] == column), None)

    def passed_function(self, node, source: bytes, file: str) -> str | None:
        """The function an argument passes by name: `handler`, or `module.handler` from a file this one imports."""
        import entries
        if node.type == "identifier":
            found = self.targets(entries._text(source, node), file, *entries._at(node), ("function", "method"))
            return self.node(found[0]) if found else None
        last = node.child_by_field_name("property") or node.child_by_field_name("attribute")
        if node.type not in MEMBERS or last is None or not _dotted(node):
            return None
        read = self.reads.get((file, *entries._at(last)), ())
        last = entries._text(source, last)
        if any(edge_view.uncertainty(ref) for ref in read):
            return None
        found = [ref["target_id"] for ref in read if self.declarations.get(ref.get("target_id"), {}).get("kind")
                 in ("function", "method")] or \
            [d["id"] for f in sorted(self.imports.get(file, ())) for d in self.functions.get(f, ()) if d["name"] == last]
        return self.node(found[0]) if len(found) == 1 else None

    def local_function(self, name: str, file: str, line: int, *, column: int | None = None) -> str | None:
        """A function of that name declared inside a function that holds `line`, else at module level."""
        inside = []
        for declaration in self.functions.get(file, ()):
            if declaration["name"] != name or declaration.get("contract"):
                continue
            holder = self.enclosing(file, declaration["line"], skip=declaration["id"], column=declaration["column"])
            if (holder is not None and holder["line"] <= line <= (holder["end"] or holder["line"])
                    and (column is None or tuple(holder["span"][:2]) <= (line, column) < tuple(holder["span"][2:]))):
                inside.append(declaration)
        if inside:
            return self.node(max(inside, key=lambda d: d["line"])["id"])
        # A method an interface declares is a contract, not the function that handles the action.
        found = [target for target in self.targets(name, file, -1, -1, ("function", "method"))
                 if not self.declarations[target].get("contract")]
        return self.node(found[0]) if found else None

    def property_functions(self, prefixes) -> dict[str, list[str]]:
        """Functions declared as the value of a property, by property name, under the prefixes."""
        out = defaultdict(list)
        for file, declarations in self.functions.items():
            if not _under(file, prefixes):
                continue
            for declaration in declarations:
                if declaration["name"] == "(anonymous)" and (label := self.property_label(declaration)):
                    out[label].append(self.node(declaration["id"]))
        return out


def _key_name(node, tree: Tree) -> str | None:
    """The name an object key writes: an identifier, or a text; None for a computed key or a variable."""
    import entries
    if node is None:
        return None
    if node.type in ("property_identifier", "private_property_identifier"):
        return entries._text(tree.source, node)
    return entries._string(node, tree.source, tree.grammar, exact=True) if node.type == "string" else None


def _members(node, tree: Tree) -> tuple[dict[str, object], bool] | None:
    """The named entries of an object literal, `{name: value node}` (None for a method), and whether a spread may add
    others; None when the node is no object literal. A computed key adds nothing."""
    import entries
    node = _unwrapped(node)
    if node is None or node.type not in OBJECTS:
        return None
    found, spread = {}, False
    for child in node.named_children:
        if child.type in SPREADS:
            spread = True
        elif child.type == "pair":
            if (name := _key_name(child.child_by_field_name("key"), tree)) is not None:
                found[name] = child.child_by_field_name("value")
        elif child.type == "shorthand_property_identifier":
            found[entries._text(tree.source, child)] = child
        elif child.type == "method_definition":
            if (name := _key_name(child.child_by_field_name("name"), tree)) is not None:
                found[name] = None
    return found, spread


def _positional(node, tree: Tree) -> list | None:
    """The arguments of a call node as `_read_call` lists them: a node each, None where the argument has a keyword
    (`f(a, key=b)`: its place is not the one a rule counts); None when the node is no call."""
    import entries
    listed = node.child_by_field_name("arguments")
    if listed is None or not listed.children or listed.children[0].type != "(":
        return None
    return [None if keyword else value for keyword, value in entries._arguments(node, tree.source)]


def _read_call(facts: Facts, ref: dict, parts: list[str]) -> dict | str:
    """The call a reference records, read from its file's tree, or why it cannot be read: the node of the call, its
    arguments (`_positional`) and the file's tree."""
    import entries
    span = ref.get("span") or [None] * 4
    tree = facts.tree(ref["file"])
    if isinstance(tree, str):
        return "call arguments not readable" + (f": {tree}" if tree else "")
    node = entries._call(tree.root, span) if None not in span else None
    args = _positional(node, tree) if node is not None else None
    if args is None:
        return "call arguments not readable"
    return {"file": ref["file"], "line": span[0], "parts": parts, "tree": tree, "node": node, "args": args,
            "scope": ref.get("scope")}


def _not_literal(call: dict) -> str:
    """Why a value is a gap: it is computed, or its grammar has no reader of strings (`QUERIES["strings"]`)."""
    import entries
    grammar = call["tree"].grammar
    return "not a literal" if grammar in entries.QUERIES["strings"] else f"not a literal ({grammar} strings are not read)"


def _nested(spec: str, call: dict, facts, strip: str, template: bool = False):
    """`argN.argM`, argument M of the call written as argument N; `argN.key`, the literal value of `key`
    in the object written as argument N; after `|`, the value when that argument or key is absent."""
    match = _NESTED.match(spec)
    index, inner, default = int(match.group(1)), match.group(2), match.group(3)
    if index >= len(call["args"]):
        return default
    node, tree = call["args"][index], call["tree"]
    if node is None:
        return None
    if inner.startswith("arg") and inner[3:].isdigit():
        args = _positional(node, tree)
        if args is None:
            return None
        return _value(inner, {**call, "args": args}, facts, strip, template) if int(inner[3:]) < len(args) else default
    members = _members(node, tree)
    if members is None or members[1]:  # no object literal, or a spread that may hold the key
        return None
    return facts.literal(members[0][inner], tree) if inner in members[0] else default


def _value(spec, call, facts, strip: str = "", template: bool = False):
    """A rule field: a literal string, `argN` read from the call, `partN` of the written callee,
    or a value nested in an argument (`_nested`). A template is refused unless `template`."""
    if _NESTED.match(str(spec)):
        return _nested(str(spec), call, facts, strip, template)
    match = _ARG.match(str(spec))
    if match is None:
        return spec
    index = int(match.group(2))
    if match.group(1) == "part":
        return call["parts"][index] if index < len(call["parts"]) else None
    if index >= len(call["args"]):
        return None
    value = facts.literal(call["args"][index], call["tree"])
    if value is not None and strip and value.startswith(strip):
        value = value[len(strip):]
    return None if value is None or ("${" in value and not template) else value


# ---------------------------------------------------------------- link types

class LinkType(NamedTuple):
    """A link type: its name, its role pair (who asks, who offers), how the raw values a rule reads become a
    key (None: a gap) and how an asking key meets an offering one (None: they do not; higher is closer)."""
    name: str
    pair: tuple[str, str]
    key: Callable[..., tuple | None]
    meet: Callable[[tuple, tuple], tuple | None]


def join(kind: LinkType, asking: list[dict], offering: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Each asking point (a dict with a `key`) with the offering points it meets best: one is a link,
    several an uncertain link, none a single side."""
    out = []
    for point in asking:
        met = [(m, o) for o in offering if (m := kind.meet(point["key"], o["key"])) is not None]
        best = max((m for m, _ in met), default=None)
        out.append((point, [o for m, o in met if m == best]))
    return out


# A route's segment is text with no grammar: the parameter spellings of the frameworks (`<id>`, `{id}`).
_PATH_PARAMETER = re.compile(r"<[^<>/]*>|\{[^{}/]*\}")


def _holes(text: str) -> str | None:
    """The text with every `${...}` as `\\0`; None when one is not closed."""
    out, i = [], 0
    while i < len(text):
        if not text.startswith("${", i):
            out.append(text[i])
            i += 1
            continue
        depth, j = 0, i + 1
        while j < len(text):
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            if depth == 0:
                break
            j += 1
        if depth:
            return None
        out.append("\0")
        i = j + 1
    return "".join(out)


def _rest_key(service, method, path) -> tuple | None:
    """(service, METHOD, path schema). The query, the fragment and the base URL before the first segment,
    literal or not, are not part of the key; a parameter, interpolated (`${id}`) or declared (`:id`, `<id>`,
    `{id}`), is `{}`. A path whose first segment is interpolated is computed: a gap."""
    text = None if None in (service, method, path) else _holes(path)
    if text is None:
        return None
    head = text.lstrip("\0")
    try:
        split = urlsplit(head)  # the query and the fragment end the path; `//host` or `scheme://host` is the base URL
    except ValueError:  # a host in brackets that never closes
        return None
    # A scheme with no `//` after it (`items:batch`) is no base URL: it stays a segment.
    based = bool(split.netloc) or bool(split.scheme) and head[len(split.scheme) + 1:].startswith("//")
    rest = split.path if based else (head[:len(split.scheme) + 1] if split.scheme else "") + split.path
    if not rest or (based or head != text) and not rest.startswith("/"):
        return None  # an interpolation glued to what follows it, or nothing after the base
    segments = [s for s in rest.split("/") if s]
    if segments and "\0" in segments[0]:
        return None
    segments = ["{}" if s.startswith(":") else _PATH_PARAMETER.sub("{}", s.replace("\0", "{}")) for s in segments]
    return str(service), str(method).upper(), "/" + "/".join(segments)


def _segment_grade(asked: str, offered: str) -> int | None:
    """2 the same, 1 a literal filling a parameter, 0 a hole glued to a literal that must equal one, None no."""
    if asked == offered:
        return 2
    if offered == "{}":
        return 1
    if "{}" in asked and "{" not in offered:
        # Both texts are Daodan's own, made by `_rest_key`: segments with `{}` for a hole, no grammar.
        pattern = "".join("[^/]*" if part == "{}" else re.escape(part) for part in re.split(r"(\{\})", asked))
        return 0 if re.fullmatch(pattern, offered) else None
    return None


ANY_SERVICE = "*"  # the service of an offered route no rule names (Noir and Next.js do not know it): it meets any


def _rest_meet(asked: tuple, offered: tuple) -> tuple | None:
    """Same method and number of segments, every segment meeting, and the same service or an offered `ANY_SERVICE`
    (the asking side names its service: it is never `*`). The service comes first: a route of the asked service
    before one of `*`, so a declared route only fills where no route of a rule meets. Then (True, total) when no
    hole has to equal a literal, the most literal route first; (False, 0) otherwise, so loose candidates tie; a route
    of `*` meets only the first kind: a hole that would have to equal one of its literals is no link to a route no
    rule vouches for."""
    if asked[1] != offered[1] or offered[0] not in (asked[0], ANY_SERVICE):
        return None
    calls, routes = asked[2].strip("/").split("/"), offered[2].strip("/").split("/")
    grades = [_segment_grade(c, r) for c, r in zip(calls, routes)] if len(calls) == len(routes) else [None]
    if None in grades:
        return None
    exact, strict = offered[0] == asked[0], min(grades) >= 1
    if not (exact or strict):
        return None
    # shortcut: the service ranks before the literal, so a rule's `/x/{}` beats a declared `/x/search`, when a measured project shows the declared route was the right one
    return (exact, strict, sum(grades) if strict else 0)


REST = LinkType("rest", ("rotta", "offre"), _rest_key, _rest_meet)  # the guide's "metodo e schema del percorso"


def _store_index(node):
    """The index of `store[INDEX]`: `store` is a name, a dotted name all the way down, or the result of a call
    (`get_db()[NAME]`); None for any other node."""
    # shortcut: the object indexed is a name or a call, not a longer expression (`a.b()[NAME]`, `x[0][NAME]`), when a measured project holds its store that way
    if node is None or node.type not in SUBSCRIPTS:
        return None
    base = _unwrapped(node.child_by_field_name("object") or node.child_by_field_name("value"))
    if base is not None and (_dotted(base) or base.child_by_field_name("arguments") is not None):
        return node.child_by_field_name("index") or node.child_by_field_name("subscript")
    return None


def _store_key(value, tree: Tree, facts) -> str | None:
    """The key a handle's value names: `store.key`, or `store[KEY]` where KEY is a constant text; None when it is
    neither."""
    import entries
    node = _unwrapped(value)
    if node is None:
        return None
    if node.type in MEMBERS and _dotted(node):
        name = node.child_by_field_name("property") or node.child_by_field_name("attribute")
        return entries._text(tree.source, name) if name is not None else None
    if (index := _store_index(node)) is not None:
        text = facts.literal(index, tree)
        return text if text is not None and "${" not in text else None
    return None


def _unread_index(index, call: dict, facts) -> str:
    """Why the index of a receiver is no text: one cause for each case, so a gap says what is missing. An attribute of
    `self`/`this`, or a dotted name, is read through the engine's declaration of it (`Facts.literal`); it is a gap when
    the engine names none as written once."""
    import entries
    tree, node = call["tree"], _unwrapped(index)
    if node is not None and node.type in MEMBERS and _dotted(node):
        if any(ref.get("binding_id") for ref in facts.reads.get((tree.file, *entries._at(node)), ())):
            return f"receiver index {entries._text(tree.source, node)} names a declaration whose value is no text"
        owner = entries._text(tree.source, node.child_by_field_name("object"))
        if owner in entries.RECEIVERS:
            return (f"receiver index is an attribute of {owner} with no declaration the engine names as written once "
                    "(no engine index, an inherited or outside attribute, or a value written again)")
        return ("receiver index is a dotted name (`module.NAME`, `Class.NAME`) with no declaration the engine names as "
                "written once (no engine index, an outside name, or a value written again)")
    if node is not None and node.type in NAMES and any(
            ref.get("imported_name") for ref in facts.reads.get((tree.file, *entries._at(node)), ())):
        return f"receiver index {entries._text(tree.source, node)} is imported and the snapshot links it to no declaration"
    return f"receiver index {_not_literal(call)}"


def _inline_handle(call: dict, facts) -> tuple[str | None, str | None]:
    """`(key, why)` of a call made on `store[INDEX]` itself, `db[COLLECTION].find()`, a receiver that is no name: the key
    is read as for `handle = store[INDEX]` (`_store_key`); the rule's `callee` or `written` says which calls are the store's.
    An index that is no constant is `why` (`_unread_index`), never a key. No key and no `why`: the receiver is no
    `store[...]` (the result of a call that is not indexed, a text)."""
    callee = call["node"].child_by_field_name("function")
    node = _unwrapped(callee.child_by_field_name("object")) if callee is not None else None
    if (index := _store_index(node)) is None:
        return None, None
    key = _store_key(node, call["tree"], facts)
    return (key, None) if key else (None, _unread_index(index, call, facts))


def _handle(call: dict, facts) -> tuple[str | None, str | None]:
    """`(key, why)` of the store handle a call is made on: `handle = store.key` or `handle = store[KEY]`, assigned where
    the snapshot's scopes bind the receiver (a variable), or in the class that holds it (`self.handle`, `this.handle`);
    or the receiver itself, `store[KEY]` (`_inline_handle`).
    No key and no `why`: the receiver is no handle of the store (a parameter, an import, a value of another shape);
    `why`: the snapshot does not tell what the receiver is, it is assigned from several keys, or its index is no constant."""
    import entries
    tree, receiver = call["tree"], call["parts"][:-1]
    name = ".".join(receiver)
    if receiver[:1] == [DYNAMIC]:
        return _inline_handle(call, facts)
    if not receiver or (len(receiver) == 1 and receiver[0] in entries.RECEIVERS):
        return None, None
    if len(receiver) == 1:
        found, why = facts.bindings(tree.file, call["scope"], name)
        if found is None:
            return None, f"receiver {name} is not resolved ({why})"
        declarations = [facts.declarations.get(identity) for kind, identity in found if kind == "declaration"]
        values = [tree.placed[at] for declaration in declarations if declaration and declaration["kind"] == "binding"
                  and (at := (declaration["line"], declaration["column"])) in tree.placed]
        shaped = [_store_key(value, tree, facts) is not None for value in values]
        if len(found) > 1 and any(shaped) and not all(shaped):  # bound again: `let rows; rows = db.late` has one value
            return None, f"receiver {name} is bound again in its scope, not always to a handle"
    elif len(receiver) == 2 and receiver[0] in entries.RECEIVERS:
        owner = entries._holder(facts.classes, tree.file, call["line"])
        values = [value for target, at, value in tree.assigned if owner and target == name
                  and owner["line"] <= at[0] <= (owner["end"] or owner["line"])]
    else:
        return None, f"receiver {name} is neither a variable nor an attribute of {' or '.join(entries.RECEIVERS)}"
    keys = sorted({key for value in values if (key := _store_key(value, tree, facts))})
    if len(keys) > 1:
        return None, f"receiver {name} is assigned from several keys: {', '.join(keys)}"
    return (keys[0], None) if keys else (None, None)


def _bound(call, tree: Tree):
    """What the value of a call node is bound to, awaited or not: `("name", name node)` for `const name = call()`, or
    `("pattern", [(key, variable)])` for `const { key, other: variable } = call()` (the variable None where the entry
    names none); None when the call is not the whole value of a declaration."""
    import entries
    node = call
    while node.parent is not None and node.parent.type in WRAPPERS:
        node = node.parent
    declarator = node.parent
    if declarator is None or declarator.type != "variable_declarator" or declarator.child_by_field_name("value") != node:
        return None
    target = declarator.child_by_field_name("name")
    if target.type == "identifier":
        return "name", target
    if target.type != "object_pattern":
        return None
    pairs = []
    for entry in target.named_children:
        if entry.type == "object_assignment_pattern":  # `items = []`: the default is not the key
            entry = entry.child_by_field_name("left")
        if entry.type == "shorthand_property_identifier_pattern":
            pairs.append((entries._text(tree.source, entry),) * 2)
        elif entry.type == "pair_pattern" and (key := _key_name(entry.child_by_field_name("key"), tree)) is not None:
            variable = entry.child_by_field_name("value")
            variable = variable.child_by_field_name("left") if variable is not None and variable.type == "assignment_pattern" else variable
            pairs.append((key, entries._text(tree.source, variable) if variable is not None and variable.type == "identifier" else None))
    return "pattern", pairs


def _read_on(call: dict, facts, name_node) -> list[str] | None:
    """The properties read on the variable a call's value is held in, in the order written: the reads and the calls of
    the snapshot below its declaration whose first part the snapshot's scopes bind to that variable (a closure counts,
    a variable of the same name in a function inside does not)."""
    import entries
    tree = call["tree"]
    name, at = entries._text(tree.source, name_node), entries._at(name_node)
    declared = facts.bound(tree.file, call["scope"], name)
    declaration = facts.declarations.get(declared[1]) if declared and declared[0] == "declaration" else None
    if declaration is None or (declaration["line"], declaration["column"]) != at:
        return None
    found = sorted((tuple(ref["span"][:2]), ref["parts"][1]) for ref in facts.uses[tree.file]
                   if ref.get("span") and ref["parts"][:1] == [name] and len(ref["parts"]) > 1 and tuple(ref["span"][:2]) > at
                   and facts.bound(tree.file, ref.get("scope"), name) == declared)
    return list(dict.fromkeys(key for _, key in found)) or None


def _selector(node, tree: Tree) -> list[str] | None:
    """The fields a selector reads of its parameter, in the order written: `s => s.field`, `lambda s: s.field`,
    through a wrapper that passes it on (`shallow(s => ...)`); a field read on another variable of the same name inside
    a function in it is not its own. None where the argument is no function of a single named parameter."""
    import entries
    while node is not None and node.type not in LAMBDAS and node.child_by_field_name("arguments") is not None:
        node = next((value for _, value in entries._arguments(node, tree.source)[:1]), None)
    if node is None or node.type not in LAMBDAS or (name := entries._props(node, tree.source)[1]) is None:
        return None
    found, stack = [], [node.child_by_field_name("body")]
    while stack:
        item = stack.pop()
        if item is None or (item.type in (*entries.FUNCTIONS, "lambda") and entries._props(item, tree.source)[1] == name):
            continue
        field = item.child_by_field_name("property") or item.child_by_field_name("attribute")
        owner = item.child_by_field_name("object")
        if item.type in MEMBERS and field is not None and owner is not None and owner.type == "identifier" \
                and entries._text(tree.source, owner) == name:
            found.append((item.start_byte, entries._text(tree.source, field)))
        stack.extend(item.children)
    return list(dict.fromkeys(field for _, field in sorted(found))) or None


def _object_keys(node, tree: Tree) -> list[str] | None:
    """Keys an object literal names, or those of every object a function argument returns (a value in parentheses, or
    the `return` of its own body, not of a function inside it). A spread or a computed key adds nothing; with no named
    key at all the answer is None."""
    import entries
    node = _unwrapped(node)
    if node is None:
        return None
    values = [node]
    if node.type == "arrow_function":
        body = node.child_by_field_name("body")
        values, stack = [body], [body]
        if body is not None and body.type == "statement_block":
            values = []
            while stack:
                item = stack.pop()
                if item.type == "return_statement":
                    values += item.named_children[:1]
                stack.extend(child for child in item.children if child.type not in entries.FUNCTIONS)
        values.sort(key=lambda value: value.start_byte)
    keys = [key for value in values if (members := _members(value, tree)) for key in members[0]]
    return list(dict.fromkeys(keys)) or None


def _keys(spec: str, call, facts) -> list[str] | None:
    import entries
    tree, call["unread"] = call["tree"], None  # `unread`: why the answer is a gap, where the key is not what is missing
    if spec == "holder":
        key, call["unread"] = _handle(call, facts)
        return None if call["unread"] else [key] if key else []
    if spec == "member":
        node = call["node"]
        parent = node.parent
        if parent is not None and parent.type in MEMBERS and parent.child_by_field_name("object") == node:
            field = parent.child_by_field_name("property") or parent.child_by_field_name("attribute")
            return [entries._text(tree.source, field)] if field is not None else None
        bound = _bound(node, tree)
        if bound is None:
            return None
        if bound[0] == "name":  # the whole value held in a variable
            return _read_on(call, facts, bound[1])
        return [key for key, _ in bound[1]] or None
    if _ARG.match(spec):
        value = _value(spec, call, facts)
        return [value] if value is not None else None
    if not call["args"] or call["args"][0] is None:
        return None
    if spec == "selector":
        return _selector(call["args"][0], tree)
    return _object_keys(call["args"][0], tree) if spec == "object" else None


# ---------------------------------------------------------------- links

def _handler_index(spec: str, args: list) -> int:
    return len(args) - 1 if spec == "last" else int(spec[3:])


def _route_handler(facts: Facts, spec: str, call: dict) -> str | None:
    """The symbol a route registered with a handler argument belongs to."""
    import entries
    args = call["args"]
    index = _handler_index(spec, args)
    if not 0 <= index < len(args) or args[index] is None:
        return None
    written = facts.written_function(call["file"], *entries._at(args[index]))
    return facts.node(written["id"]) if written else facts.passed_function(args[index], call["tree"].source, call["file"])


def _name_written_handlers(facts: Facts, view: dict, rules: list[dict]) -> None:
    """A function written in place as a route handler is named by its route, before any link reads names."""
    import entries
    if not rules:
        return
    for ref in view["references"]:
        parts = [str(part) for part in ref.get("parts") or []]
        for rule in (r for r in rules if _written(r, parts, ref["file"])):
            call = _read_call(facts, ref, parts)
            index = _handler_index(rule["handler"], call["args"]) if isinstance(call, dict) else -1
            if index < 0 or index >= len(call["args"]) or call["args"][index] is None:
                continue
            written = facts.written_function(ref["file"], *entries._at(call["args"][index]))
            method, path = (_value(rule["route"][k], call, facts, rule.get("strip", "") if k == "path" else "")
                            for k in ("method", "path"))
            if written and written["name"] == "(anonymous)" and method and path is not None:
                facts.route_named[written["id"]] = f"{method.upper()} {path}"
    facts._nodes.clear()


def path_schema(path: str) -> str | None:
    """The path of a route as `REST` reads one (`/orders/{}`: `:id` and `[id]` alike), or None when it has none (nothing after
    the base URL, or a computed first segment). The adapter that knows its tool's spelling gives it as the row's `schema`."""
    key = REST.key(ANY_SERVICE, "", path)  # the key wants a method, the schema is the same under any
    return key[2] if key else None


def _declared_routes(found: list[dict], offered: list[dict]) -> tuple[list[dict], list[dict]]:
    """`(points, gaps)`: the routes the adapters declare as offered points of `REST`, and those that cannot be one. `found` are
    the entries already classified (an entry of kind `rotta` on a function, no gap: the same classification as the entries
    themselves), `offered` the points the rules gave. A row offers a route when it has a `schema` (the path as `REST` reads it,
    written by the adapter that knows its tool's spelling) and a `method` of its own (a page has none and answers any); a `schema`
    that is None is a path that stands for no single schema, and a gap. A point is dropped when one of the same function, method
    and path schema exists, whatever its service: the rule's comes first, then the first declared."""
    points, gaps = [], []
    taken = {(o["symbol"], *o["key"][1:]) for o in offered}
    for item in found:
        method = item.get("method")
        if item.get("kind") != "rotta" or "schema" not in item or item.get("page") or not item.get("symbol"):
            continue  # a page answers any method: it is no route and no gap
        cause = "it has no method" if not method else None if item["schema"] is not None else (
            "the tool's path is no single path schema (a catch-all, or nothing after the base URL)")
        if cause:
            gaps.append({"site": item["site"], "symbol": item["symbol"], "reason": f"declared route {method} {item.get('path')}: {cause}"})
            continue
        key = REST.key(ANY_SERVICE, method, item["schema"])
        # shortcut: the declared route goes whatever the calling service, so a call of another service than the rule's finds no declared route of that function, when one function is offered under two services
        if key and (item["symbol"], *key[1:]) not in taken:
            taken.add((item["symbol"], *key[1:]))
            points.append({"symbol": item["symbol"], "key": key, "site": item["site"]})
    return points, gaps


def link_facts(manifest: Path, rules: list[dict], *, module_graph=None) -> dict:
    """Accesses, deduced links, entry points and gaps of a snapshot under the given rules."""
    import entries as entry_reader
    by_callee, written, attributes = defaultdict(list), [], []
    decisions = validate_rules([rule for rule in rules if "shape" in rule])
    for rule in rules:
        if "shape" in rule:
            continue
        if "callee" in rule:
            by_callee[rule["callee"]].append(rule)
        else:
            (written if "written" in rule else attributes).append(rule)
    wanted = {rule["callee"].rsplit("::", 1)[1].split(".")[-1] for rule in rules if "callee" in rule}
    accesses, entries, actions, routes_offered, route_calls, gaps, calls = [], [], [], [], [], [], []
    held: dict[tuple[str, str, str], str] = {}
    called: dict[tuple[str, str, str], tuple] = {}  # (caller, ecosystem, package) -> site, resolver, file of 1st call
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = Facts(store, db, view)
        candidates = entry_reader._cached_rows(manifest, (facts, db, view))
        from premap.flow_entries import evidence
        declared, source_gaps = evidence(manifest)
        resolver = semantic_store._Resolver(db)
        declared = binder.bind(declared, facts, resolver)
        # One route, one entry: the route of a source outside `premap.FRAMEWORK_SOURCES` (Noir) on the schema of a bound row of one
        # of them (the text of the path where a row has no schema), in the file or on the function that row starts, is that row,
        # provided its method is the row's or the row has none (a page answers any; Noir's method is not copied onto it). Another
        # path, or a method no row of that file and path carries, is a route of its own.
        from premap import FRAMEWORK_SOURCES
        tuple_names = {source.NAME for source in FRAMEWORK_SOURCES}
        def file_of(site: str) -> str:
            file, _, line = site.rpartition(":")
            return file if line.isdecimal() else site

        def route_of(item: dict):
            return item.get("schema") or item.get("path")

        by_path = defaultdict(list)
        for item in declared:
            if item["reader"] in tuple_names and not item.get("gap"):
                by_path[route_of(item)].append(item)
        kept = []
        for item in declared:
            method = item.get("method")
            same = next((n for n in by_path.get(route_of(item), ())
                         if (file_of(n["site"]) == file_of(item["site"]) or n["symbol"] == item["symbol"])
                         and (not method or n.get("method") in (None, method))), None) \
                if item["reader"] not in tuple_names and "schema" in item else None
            if same is None:
                kept.append(item)
        declared = kept
        candidates = candidates + declared + _observed_entries(manifest, store, facts, gaps)
        _name_written_handlers(facts, view, [r for r in written if r["link"] == "offre" and r.get("handler")])
        callbacks = {item["symbol"]: item["owner"] for item in candidates
                     if item.get("handler_source") == "inline" and item["symbol"] in facts.declarations
                     and item["symbol"] not in facts.route_named}
        # An event has its own callable scope, including when it has no outgoing call.
        facts._nodes.update((symbol, symbol) for symbol in callbacks)
        members = {id(rule): facts.property_functions(rule["actions_in"]) for rule in rules if rule.get("actions_in")}
        plain, sent, heard = [], [], []
        for ref in view["references"]:
            target = facts.named(ref.get("target_id")) if ref["resolution"] == "resolved" else None
            named = facts.node(ref.get("caller"))
            caller = named or f"{ref['file']}::{MODULE}"
            span = ref.get("span") or [None, None, None, None]
            site = f"{ref['file']}:{span[0]}"
            parts = [str(part) for part in ref.get("parts") or []]
            package = ref.get("external")  # the engine resolved the call into a package: its first use, by caller
            if package and package.get("manager") in ECOSYSTEMS:
                called.setdefault((caller, ECOSYSTEMS[package["manager"]], package["package"]),
                                  (site, ref.get("resolver"), ref["file"]))
            if "tauri_event" in ref:  # a call Tauri owns (`semantic.TAURI_PAGE_EVENTS`, `TAURI_RUST_EVENTS`): the name is the key
                happened = ref["tauri_event"]
                if happened["name"] is None:
                    gaps.append({"site": site, "symbol": caller, "reason": "Tauri event: the name is not a string literal"})
                else:
                    callback = happened.get("handler") or {}
                    named_callback = facts.targets(callback["name"], ref["file"], callback["line"], callback["column"],
                                                   ("function", "method")) if callback.get("name") else []
                    # a listener ends at the function its callback is; a closure is no declaration: it ends where it is held
                    (heard if happened["kind"] == "listen" else sent).append({
                        "name": happened["name"], "file": ref["file"], "site": site,
                        "node": (facts.node(named_callback[0]) if len(named_callback) == 1 else None) or caller})
            # SCIP may identify invoke itself in the SDK. Its registered Rust command is a separate,
            # static dispatch destination, already resolved in the snapshot of the same application.
            native = None
            if "tauri_command" in ref:
                command = ref["tauri_command"]
                lexical = ref.get("lexical_target_id")
                declaration = facts.declarations.get(lexical)
                sdk = ref.get("external") or {}
                if (command and declaration and declaration["file"].endswith(".rs") and not edge_view.uncertainty(ref) and
                        (ref["target_id"] == lexical or (sdk.get("manager"), sdk.get("package")) == ("npm", "@tauri-apps/api"))):
                    native = lexical
                    calls.append({"from": caller, "to": facts.node(native), "site": site,
                                  "target_site": f"{declaration['file']}:{declaration['line']}",
                                  "origin": "dedotto", "resolver": "tauri-invoke", "command": command})
                else:
                    reason = ("Tauri invoke: command name is not a string literal" if command is None else
                              f"Tauri invoke: no unique registered destination proved for {command!r}")
                    gaps.append({"site": site, "symbol": caller, "reason": reason})
            for end in edge_view.call_ends(ref):
                if end["target_id"] == native and end["confidence"] not in edge_view.SEEN:
                    continue
                callee = facts.node(end["target_id"])
                if callee:
                    evidence = {}
                    if end["confidence"] in edge_view.SEEN or end.get("conflict"):
                        evidence = {key: end[key] for key in ("resolver", "confidence", "conflict") if key in end}
                        if end["confidence"] in edge_view.SEEN:
                            evidence["origin"] = "osservato"
                    calls.append({"from": caller, "to": callee, "site": site, **evidence})
            if target is None and len(parts) == 1 and parts[0] in wanted:
                # A callable value: the call names the binding the rule names.
                holders = facts.targets(parts[0], ref["file"], -1, -1, ("binding",))
                target = facts.named(holders[0]) if holders else None
            matched = by_callee.get(target or "", []) + [rule for rule in written if _written(rule, parts, ref["file"])]
            if not matched:
                if ref["resolution"] != "resolved":
                    if ref.get("last_name") in wanted:
                        gaps.append({"site": site, "symbol": caller, "reason": f"call to {ref.get('last_name')} is unresolved"})
                    if len(parts) == 1 and caller:
                        plain.append((ref["file"], parts[0], caller, site, ref.get("scope")))
                continue
            call = _read_call(facts, ref, parts)
            if isinstance(call, str):
                gaps.append({"site": site, "symbol": caller, "reason": call})
                continue
            args = call["args"]
            for rule in matched:
                basis = {}
                if "callee" in rule:
                    if ref.get("confidence") in edge_view.SEEN or ref.get("conflict"):
                        basis = {key: ref[key] for key in ("confidence", "resolver", "conflict") if key in ref}
                    reason = edge_view.uncertainty(basis)
                    if reason and (rule["link"] not in ("scrive", "legge") or rule.get("actions_in")):
                        gaps.append({"site": site, "symbol": caller, "reason": f"{rule['link']} {target}: {reason}", **basis})
                        continue
                if rule["link"] == "offre" and rule.get("handler"):
                    owner = _route_handler(facts, rule["handler"], call)
                    if owner is None:
                        gaps.append({"site": site, "symbol": caller, "reason": "offre: handler not a function"})
                        continue
                else:
                    owner = facts.decorated(ref["file"], span[0]) if rule.get("decorates") else                         named if rule["link"] in ("offre", "ingresso") else caller
                    if owner is None:
                        gaps.append({"site": site, "symbol": caller, "reason": f"{rule['link']} call outside a named symbol"})
                        continue
                link = rule["link"]
                if link in ("scrive", "legge"):
                    keys = _keys(rule["key"], call, facts)
                    if keys == []:
                        continue  # the receiver is no handle of this store
                    if not keys:
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link} {rule['store']}: " + (
                            call.get("unread") or f"key {_not_literal(call)}")})
                    bound = _bound(call["node"], call["tree"])
                    for key in keys or []:
                        found = members.get(id(rule), {}).get(key)
                        if not found:
                            accesses.append({"symbol": owner, "link": link, "store": rule["store"], "key": key,
                                             "site": site, **basis})
                        elif len(found) > 1:
                            gaps.append({"site": site, "symbol": owner, "reason": f"{rule['store']}/{key}: several functions"})
                        elif bound and bound[0] == "name" and len(keys) == 1 and rule["key"] == "selector":
                            held[(ref["file"], owner, entry_reader._text(call["tree"].source, bound[1]))] = found[0]
                        elif bound and bound[0] == "pattern":
                            if variable := dict(bound[1]).get(key):
                                held[(ref["file"], owner, variable)] = found[0]
                        else:
                            calls.append({"from": owner, "to": found[0], "site": site, "origin": "dedotto"})
                elif link in REST.pair:
                    route = rule["route"]
                    key = REST.key(_value(route["service"], call, facts), _value(route["method"], call, facts),
                                   _value(route["path"], call, facts, rule.get("strip", ""), template=True))
                    if key is None:
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link}: route {_not_literal(call)}"})
                        continue
                    record = {"symbol": owner, "key": key, "site": site}
                    (routes_offered if link == "offre" else route_calls).append(record)
                    if link == "offre":
                        entries.append({"symbol": owner, "kind": "rotta", "site": site})
                elif link == "attiva":
                    index = _handler_index(rule["handler"], args)
                    handler = (facts.handler(args[index], call["tree"].source, ref["file"])
                               if 0 <= index < len(args) and args[index] is not None else None)
                    if handler is None:
                        gaps.append({"site": site, "symbol": owner, "reason": "attiva: handler not a named function"})
                        continue
                    actions.append({"symbol": owner, "handler": handler, "label": _value("arg0", call, facts), "site": site})
                    entries.append({"symbol": handler, "kind": "azione", "site": site})
                elif link == "ingresso":
                    entries.append({"symbol": owner, "kind": rule["entry"], "site": site})
        # A component written as an element is rendered: React calls it, so its parent reaches it.
        for read in view["reads"]:
            file, holder, span = read["file"], read.get("caller"), read.get("span") or [None] * 4
            line, column = span[:2]
            parts = read.get("parts") or []
            if len(parts) != 1 or not line or not facts.element(file, span):
                continue
            found = facts.targets(str(parts[0]), file, line, column, ("function", "class"))
            component = facts.node(found[0]) if len(found) == 1 else None
            if component:
                calls.append({"from": facts.node(holder) or f"{file}::{MODULE}", "to": component,
                              "site": f"{file}:{line}"})
        # An emit and a listen of the same name on the two sides of the bridge, Rust and the page, are linked, each pair: the name is
        # the key and an event has no declaration, so the link has both positions. Several listeners are normal, none a gap.
        for out in sent:
            for into in heard:
                if out["name"] == into["name"] and out["file"].endswith(".rs") != into["file"].endswith(".rs"):
                    calls.append({"from": out["node"], "to": into["node"], "site": out["site"], "target_site": into["site"],
                                  "origin": "dedotto", "resolver": "tauri-event", "event": out["name"]})
        # A store function held in a variable is called where that variable is called.
        for file, name, caller, site, scope in plain:
            owner = callbacks.get(caller, caller)
            target = held.get((file, owner, name))
            if target is None:
                continue
            if caller in callbacks:
                captured, _ = resolver.lexical(file, scope, name)
                outer, _ = resolver.lexical(file, facts.declarations[caller]["scope"], name)
                if captured is None or captured != outer:
                    continue
            calls.append({"from": caller, "to": target, "site": site, "origin": "dedotto"})
        _classify_entries(candidates, attributes, decisions, held, actions, entries, gaps)
        starts = {entry["symbol"] for entry in entries if entry.get("reader") != "observed"}
        entries[:] = [entry for entry in entries if entry.get("reader") != "observed" or entry["symbol"] not in starts]
        actions[:] = [action for action in actions if action.get("reader") != "observed" or action["handler"] not in starts]
        # The routes Noir and Next.js declare are offered too, for a call to meet: they are entries already, and add none.
        declared_points, declared_gaps = _declared_routes(entries, routes_offered)
        routes_offered += declared_points
        gaps += declared_gaps
        external = _external_nodes(manifest, module_graph)
        ties = _package_services(manifest)
        symbols_by_file = defaultdict(set)
        for declaration in facts.declarations.values():
            if declaration["kind"] in ("function", "method", "class"):
                node = facts.node(declaration["id"])
                if node:
                    symbols_by_file[declaration["file"]].add(node)

    edges = [{"type": "chiama", "origin": "diretto", **c}
             for c in calls]
    for access in accesses:
        store_node = f"store:{access['store']}/{access['key']}"
        ends = (access["symbol"], store_node) if access["link"] == "scrive" else (store_node, access["symbol"])
        edges.append({"from": ends[0], "to": ends[1], "type": access["link"], "origin": "dedotto",
                      **{k: access[k] for k in ("site", "confidence", "resolver", "conflict") if k in access}})
    for call, found in join(REST, route_calls, routes_offered):
        if len(found) != 1:
            gap = {"site": call["site"], "symbol": call["symbol"],
                   "reason": f"route {' '.join(call['key'])}: {'several handlers' if found else 'no handler'}"}
            gaps.append({**gap, "key": list(call["key"]), "candidates": sorted(o["symbol"] for o in found),
                         "offered": sorted(o["site"] for o in found)} if found else gap)
            continue
        edges.append({"from": call["symbol"], "to": found[0]["symbol"], "type": "chiama", "origin": "dedotto",
                      "site": call["site"], "route": list(found[0]["key"]), "offered": found[0]["site"]})
    for action in actions:
        edges.append({"from": action["symbol"], "to": action["handler"], "type": "attiva", "origin": "dedotto",
                      "site": action["site"], "label": action["label"],
                      **{key: action[key] for key in ("shape", "column", "handler_source", "handler_confidence")
                         if key in action}})
    added = {item.rpartition("@")[0] for items in view["profile"].get("types_added", {}).values() for item in items}
    uses, in_tests, gave = _service_uses(called, ties, external, added)
    for module in external:
        for file in module["evidence_files"]:
            if (file, module["id"]) in gave:
                continue  # the calls the engine resolved there into the service's packages say which symbols use it
            for symbol in sorted(symbols_by_file.get(file, ())):
                edges.append({"from": symbol, "to": f"module:{module['name']}", "type": "usa", "origin": "dichiarato",
                              "site": file, "status": module["status"]})
    edges += uses
    stores = defaultdict(lambda: {"writes": set(), "reads": set()})
    for access in accesses:
        stores[f"{access['store']}/{access['key']}"]["writes" if access["link"] == "scrive" else "reads"].add(access["symbol"])
    unique = {}
    for edge in edges:
        unique.setdefault((edge["from"], edge["to"], edge["type"], edge["site"], edge["origin"],
                           edge.get("confidence"), edge.get("resolver"), edge.get("column"),
                           edge.get("handler_confidence"), bool(edge.get("conflict"))), edge)
    return {"schema": LINKS_SCHEMA, "manifest": str(manifest),
            "symbol_coverage": _symbol_coverage(symbols_by_file, entries, unique.values()),
            "stores": {name: {"writes": sorted(v["writes"]), "reads": sorted(v["reads"])} for name, v in sorted(stores.items())},
            "entries": sorted({(e["symbol"], e["kind"], e["site"], e.get("column"), e.get("shape"),
                                e.get("label") if e.get("declared_in") else None, e.get("declared_in"),
                                e.get("method"), e.get("path")): e  # one function can start several routes
                               for e in entries}.values(),
                              key=lambda e: (e["kind"], e["symbol"], e["site"], e.get("column", 0), e.get("method") or "",
                                             e.get("path") or "")),
            "source_gaps": source_gaps,
            "edges": sorted(unique.values(), key=lambda e: (e["from"], e["to"], e["type"], e["site"])),
            "store_types": {rule["store"]: rule["node_type"] for rule in rules if rule.get("node_type")},
            "routes": {"offered": len({o["key"] for o in routes_offered}),
                       "called": len(route_calls), "linked": sum(1 for e in unique.values() if e.get("route"))},
            "external": [{"id": m["id"], "name": m["name"], "status": m["status"],
                          **({"in_tests": in_tests[m["id"]]} if m["id"] in in_tests else {})} for m in external],
            "gaps": sorted(gaps, key=lambda g: (g["site"], g["reason"]))}


def reached_symbols(entries, edges, *, kinds=("chiama", "attiva")) -> set[str]:
    """All identified entry handlers and their evidenced call/activation targets, visited once."""
    outgoing = defaultdict(set)
    for edge in edges:
        if edge["type"] in kinds and not edge_view.uncertainty(edge):
            outgoing[edge["from"]].add(edge["to"])
    reached = {entry["symbol"] for entry in entries if not edge_view.uncertainty(entry)}
    todo = list(reached)
    while todo:
        for target in outgoing.get(todo.pop(), ()):
            if target not in reached:
                reached.add(target)
                todo.append(target)
    return reached


def _symbol_coverage(symbols_by_file, entries, edges):
    reached = reached_symbols(entries, edges)
    counts = defaultdict(lambda: {"total": 0, "unreached": 0})
    for file, symbols in symbols_by_file.items():
        folder = counts[PurePosixPath(file).parent.as_posix()]
        folder["total"] += len(symbols)
        folder["unreached"] += len(symbols - reached)
    return dict(sorted(counts.items()))


@cache
def _links_reader_digest() -> str:
    """Installed link readers and rules; one bounded read of Daodan's own code per process."""
    from premap import FRAMEWORK_SOURCES, TEMPLATE_SOURCES
    digest = hashlib.sha256()
    for path in (Path(__file__), SCRIPT_DIR / "binder.py", SCRIPT_DIR / "edge_view.py", SCRIPT_DIR / "edge_store.py", SCRIPT_DIR / "entries.py",
                 SCRIPT_DIR / "premap" / "flow_entries.py", SCRIPT_DIR / "premap" / "noir.py",
                 *(Path(source.__file__) for source in (*FRAMEWORK_SOURCES, *TEMPLATE_SOURCES)),
                 SCRIPT_DIR / "premap" / "angular_templates.mjs", SCRIPT_DIR / "technologies.py",
                 SCRIPT_DIR / "premap" / "python_build.py", SCRIPT_DIR / "languages" / "rust.py",
                 SCRIPT_DIR / "engine_pass.py", SCRIPT_DIR.parent / "data" / "entry-queries.json"):
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _links_stamp(manifest: Path, *, premap=True) -> list:
    import modules
    from store_graph import source_stamp
    edges = manifest.with_name("engine-edges.sqlite")
    files = (manifest, manifest.with_name(manifest.name + "-wal"), edges, edges.with_name(edges.name + "-wal"),
             modules.graph_name(manifest), manifest.with_name(modules.LEDGER_FILE))
    if premap:  # the pre-map's record, and the stack step's: its services are the links' external nodes
        import observed_entries
        import technologies
        from premap import path
        files += (path(manifest), technologies.path(manifest), manifest.with_name(observed_entries.FILE))
    stamp = []
    for path in files:
        try:
            item = source_stamp(path)
        except FileNotFoundError:
            stamp.append(None)
        else:
            stamp.append(item)
    return stamp


def _links_key(rules, stamp, languages):
    import engine_pass
    engines = sorted({(spec.name, engine_pass.adapter_fingerprint(spec.indexer))
                      for language in languages if (spec := engine_pass.ENGINE_LANGUAGES.get(language))})
    payload = [LINKS_SCHEMA, _links_reader_digest(), rules, stamp, engines]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _links_languages(manifest: Path, store=None) -> list[str]:
    """Only a present edge store makes its official indexers inputs to a result."""
    import engine_pass
    if not manifest.with_name("engine-edges.sqlite").is_file():
        return []
    if store is None:
        with open_snapshot(manifest) as store:
            return _links_languages(manifest, store)
    return engine_pass.pass_languages(store.connection) if store.connection is not None else []


def cached_links(manifest: Path, rules: list[dict], *, with_key: bool = False):
    """Reuse links only for the same inputs, reader implementation and relevant native analyzers."""
    import modules
    manifest = Path(manifest)
    destination = manifest.with_name("flow-links.json")
    try:
        kept = json.loads(destination.read_text(encoding="utf-8"))
        languages = kept.get("languages") if isinstance(kept, dict) else None
        stamp = _links_stamp(manifest)
        if (isinstance(languages, list) and all(s is None or s[-1] for s in stamp)
                and kept.get("key") == _links_key(rules, stamp, languages)):
            return (kept["key"], kept["links"]) if with_key else kept["links"]
    except (OSError, KeyError, TypeError, ValueError):
        pass
    # link_facts also reads the module graph. Materialize it before stamping a cache miss so its first publication
    # or a refreshed ledger does not trigger a second full pass over the references.
    for _ in range(2):
        module_graph = modules.ensure_graph(manifest)
        before = _links_stamp(manifest)
        languages = _links_languages(manifest)
        links = link_facts(manifest, rules, module_graph=module_graph)
        if _links_stamp(manifest) == before:
            key = _links_key(rules, before, languages) if all(s is None or s[-1] for s in before) else None
            if key is not None:
                snapshot._write_json_atomic(destination, {"key": key,
                                                          "languages": languages, "links": links})
            return (key, links) if with_key else links
    raise ValueError("the mapping inputs changed while computing flow links; retry")


def _handler_at(facts, at: dict) -> dict | None:
    """The function of the snapshot the browser's handler is. The browser says where the function starts (`start`, from
    `callFrame.functionLocation`): the one function that starts on that line, the nearest by column when several do. Without
    it, the innermost function whose lines hold the place it paused at, when one stands out (a callback on that line
    would be taken for the handler, so two of the same lines and name are none)."""
    functions = facts.functions.get(at["file"], ())
    start = at.get("start")
    if start:
        same = sorted((d for d in functions if d["line"] == start["line"]), key=lambda d: abs(d["column"] - start["column"]))
        return same[0] if same and (len(same) == 1 or abs(same[0]["column"] - start["column"])
                                    < abs(same[1]["column"] - start["column"])) else None
    inside = [d for d in functions if d["line"] <= at["line"] <= (d["end"] or d["line"])]
    deepest = max(inside, key=lambda d: (d["line"], -(d["end"] or d["line"])), default=None)
    same = [d for d in inside if deepest and (d["line"], d["end"]) == (deepest["line"], deepest["end"])]
    same = same if len(same) == 1 else [d for d in same if d["name"] == at["name"]]
    return same[0] if len(same) == 1 else None


def _observed_entries(manifest: Path, store, facts, gaps: list[dict]) -> list[dict]:
    """The controls the browser pressed (`observed_entries`) as candidates at their handler (`_handler_at`). An inline arrow
    is its own node, owned by the function that holds it (as the static reader's `inline` handlers are). A handler the
    browser isolated that no function of the snapshot stands for is a gap at the place it paused; one handler is one entry,
    at the first control that reached it, and `link_facts` leaves it out where a static reader starts there. A static
    candidate of the same name does not leave it out: it may start from another function (a member of a type that the
    handler implements), and the two are told apart by the function."""
    import observed_entries
    found: dict[str, dict] = {}
    for row in observed_entries.rows(manifest, [], set(store.iter_paths())):  # no static row: the function is the identity, not the name
        at = row.get("at")
        if not at:
            continue
        handler = _handler_at(facts, at)
        if handler is None:
            gap = {"site": f"{at['file']}:{at['line']}", "reason": f"observed: the handler {at['name']} the browser isolated "
                   "is no one function of the snapshot"}
            if gap not in gaps:
                gaps.append(gap)
            continue
        anonymous = handler["name"] == "(anonymous)"
        symbol = handler["id"] if anonymous else facts.node(handler["id"])
        if symbol:
            found.setdefault(symbol, {
                **{key: value for key, value in row.items() if key != "declared_in"}, "symbol": symbol,
                "site": f"{at['file']}:{handler['line']}", "handler_source": "inline" if anonymous else "osservato",
                **({"owner": facts.node(handler["id"])} if anonymous else {})})
    return list(found.values())


def _classify_entries(candidates, attributes, decisions, held, actions, found, gaps):
    """Apply classifications to snapshot evidence, including the original attribute glob rules."""
    import entries
    registered = entries.registry_rules(candidates)
    by_shape = {(r["reader"], r["shape"]): r for r in [*decisions, *registered]}
    for item in candidates:
        if item.get("forwarded"):
            continue  # Giving a child a prop does not prove that any control binds it.
        site = item["site"]
        file = site.rsplit(":", 1)[0]
        owner = item.get("owner")
        handler = item.get("symbol")
        if item.get("component_gap"):  # an event on a component the reader cannot follow: a gap, whatever its shape is
            gaps.append({"site": site, "symbol": owner or handler, "reason": item["gap"]})
            continue
        if item.get("unbound"):
            handler = held.get((file, owner, item["binding"]))
            if not handler:
                continue
            item = {**item, "handler_source": "regola"}
        shape = item["shape"]
        legacy = item["reader"] == entries.ATTRIBUTE and any(
            _under(file, rule.get("in")) and fnmatch.fnmatchcase(shape, rule["attribute"]) for rule in attributes)
        rule = by_shape.get((item["reader"], shape))
        if (rule is None and not legacy) or (rule and rule["entry"] == entries.NO_ENTRY):
            continue
        if item.get("gap"):
            gaps.append({"site": site, "symbol": owner or handler, "reason": item["gap"]})
            continue
        evidence = {key: item[key] for key in ("reader", "shape", "column", "event", "label", "label_gap", "handler_source",
                                               "path", "method", "declared_in", "handler_confidence") if item.get(key) is not None}
        if "schema" in item:  # None is a path that stands for no single schema: a gap of the declared routes
            evidence["schema"] = item["schema"]
            if item.get("page"):
                evidence["page"] = True
        found.append({"symbol": handler, "site": site, "kind": "azione" if legacy else rule["entry"],
                      "source": "regola" if legacy else rule["source"], **evidence})
        if owner:
            actions.append({"symbol": owner, "site": site, "handler": handler, **evidence, "label": item.get("label") or shape})


def _external_nodes(manifest: Path, graph=None) -> list[dict]:
    """The services of others the links hold as nodes, by id: the stack step's recorded technologies and the external
    modules of the module graph (`technologies.externals`, the list the brief shows), each with the files it cites. A
    service the graph knows is named as the graph names it; one only the stack step recognises, by its id."""
    import modules
    import technologies
    try:
        graph = graph if graph is not None else modules.ensure_graph(manifest)
        payload = json.loads(Path(graph["graph"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        payload = {}
    return [{"id": e["id"], "name": e.get("module") or e["id"], "status": e["status"] if "module" in e else "inferred",
             "evidence_files": e["paths"]}
            for e in technologies.externals({"modules": payload.get("modules", [])}, technologies.recorded(manifest))]


def _package_services(manifest: Path) -> dict[tuple[str, str], str]:
    """The service of others each package belongs to, by (ecosystem, name as `service_registry.package_key` compares
    it): the packages a module declares that the stack step's record ties to a technology of kind service (a framework
    or a tool is no service of others)."""
    import service_registry
    import technologies
    record = technologies.recorded(manifest)
    services = {item["id"] for item in record["technologies"] if item.get("kind") == "service"}
    return {(lib["ecosystem"], service_registry.package_key(lib["ecosystem"], lib["name"])): lib["id"]
            for module in record.get("modules", ()) for lib in module.get("libraries", ()) if lib.get("id") in services}


def _service_uses(called: dict, ties: dict, external: list[dict], added: set[str]) -> tuple[list[dict], dict, set]:
    """The `usa` edges of the calls an engine resolved into a package of a service (`ties`, `_package_services`): one
    per caller and service, at the first call, its resolver the engine's. A call in a test file is no use of the
    service: it makes no edge and is counted, per service, in `in_tests` (the files and the callers). `gave` are the
    (file, service) pairs a call was found for, test files included: the files whose declared edges these replace.
    A call that ends in a type package the indexer added for a library (`added`, `edge_view`'s `types_added`) is a call
    into that library: its name is the one the indexer gives it (`typescript_types.types_package`)."""
    import service_registry
    from indexers import typescript_types
    nodes = {node["id"]: node for node in external}
    ties = {**ties, **{("npm", typescript_types.types_package(name)): service for (ecosystem, name), service in ties.items()
                       if ecosystem == "npm" and typescript_types.types_package(name) in added}}
    edges, in_tests, gave = {}, {}, set()
    for (caller, ecosystem, name), (site, resolver, file) in called.items():
        service = ties.get((ecosystem, service_registry.package_key(ecosystem, name)))
        if service not in nodes:
            continue
        gave.add((file, service))
        if semantic_store._is_test_path(file):
            left = in_tests.setdefault(service, {"files": set(), "callers": set()})
            left["files"].add(file)
            left["callers"].add(caller)
        elif (caller, service) not in edges:
            edges[caller, service] = {"from": caller, "to": f"module:{nodes[service]['name']}", "type": "usa",
                                      "origin": "dedotto", "site": site, "status": nodes[service]["status"],
                                      **({"resolver": resolver} if resolver else {})}
    return list(edges.values()), {service: {key: len(items) for key, items in left.items()}
                                  for service, left in in_tests.items()}, gave


# ---------------------------------------------------------------- flows

def trace(links: dict, start: str, direction: str, boundary: list[str] | None = None,
          max_edges: int = MAX_EDGES) -> dict:
    """Follow links from a node, each once, until nothing is left, a boundary or the budget stops it.

    `from` follows what the node causes: calls, activations, writes and the readers of
    what was written. `to` follows where the node's data comes from: the stores it
    reads, their writers and what those call. `through` lists the entry points whose
    `from` flow contains the node.
    """
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for edge in links["edges"]:
        outgoing[edge["from"]].append(edge)
        incoming[edge["to"]].append(edge)
    if direction == "through":
        hits, incomplete = [], []
        proven = {entry["symbol"] for entry in links["entries"] if not edge_view.uncertainty(entry)}
        for symbol in dict.fromkeys(entry["symbol"] for entry in links["entries"]):
            if symbol not in proven:
                incomplete.append({"entry": symbol, "reason": "unproved entry binding"})
                continue
            flow = _trace_path(links, symbol, "from", boundary, max_edges, outgoing, incoming)
            if start in flow["nodes"]:
                hits.append(symbol)
            if not flow["complete"]:
                incomplete.append({"entry": symbol, "reason": flow["stopped"] or (
                    "boundary" if flow["outside_boundary"] else "gap")})
        return {"schema": FLOW_SCHEMA, "start": start, "direction": "through",
                "entries": hits, "incomplete_entries": incomplete,
                "stopped": None if links["entries"] else "no_entries",
                "complete": bool(links["entries"]) and not incomplete}
    return _trace_path(links, start, direction, boundary, max_edges, outgoing, incoming)


def _trace_path(links, start, direction, boundary, max_edges, outgoing, incoming):
    def steps(node):
        if direction == "from":
            return [(edge, edge["to"]) for edge in outgoing[node] if edge["type"] in ("chiama", "attiva", "scrive", "legge", "usa")]
        out = [(edge, edge["to"]) for edge in outgoing[node] if edge["type"] in ("chiama", "scrive", "usa")]
        out += [(edge, edge["from"]) for edge in incoming[node] if edge["type"] in ("legge", "scrive")]
        return out

    def inside(node):
        if not boundary or "::" not in node:
            return True
        file = node.split("::", 1)[0]
        return any(b == "." or file == b or file.startswith(b.rstrip("/") + "/") for b in boundary)

    seen, followed, outside, barriers, queue = {start}, [], [], [], deque([start])
    scheduled, emitted = {start}, set()
    stopped_at = None
    while queue:
        node = queue.popleft()
        for edge, nxt in steps(node):
            if not inside(nxt):
                outside.append(edge)
                continue
            reason = edge_view.uncertainty(edge)
            if id(edge) not in emitted:
                if len(followed) >= max_edges:
                    stopped_at = edge
                    break
                emitted.add(id(edge))
                followed.append(edge)
                if reason:
                    barriers.append({**edge, "symbol": node, "reason": reason})
            if reason:
                continue
            seen.add(nxt)
            # A store reader or a side-effect store ends this path. A later call to the same
            # node can still expand it, independent of the order in which the paths arrived.
            terminal = (edge["type"] == "legge" if direction == "from" else
                        edge["type"] == "scrive" and nxt == edge["to"])
            if not terminal and nxt not in scheduled:
                scheduled.add(nxt)
                queue.append(nxt)
        if stopped_at is not None:
            break
    files = {node.split("::", 1)[0] for node in seen if "::" in node}
    gaps = [gap for gap in links["gaps"] if gap.get("symbol") in seen or (
        not gap.get("symbol") and gap.get("site", "").rsplit(":", 1)[0] in files)]
    return {"schema": FLOW_SCHEMA, "start": start, "direction": direction,
            "nodes": sorted(seen), "edges": followed, "outside_boundary": outside, "gaps": gaps + barriers,
            "stopped": "budget" if stopped_at is not None else None,
            **({"stopped_at": stopped_at} if stopped_at is not None else {}),
            "complete": stopped_at is None and not (outside or gaps or barriers),
            "files": sorted(files)}


# ---------------------------------------------------------------- levels

LEVELS = ("fisico", "logico", "dati", "ux")


def file_modules(manifest: Path) -> dict[str, str]:
    """The module each file belongs to: the smallest module of the module graph that holds it. The implicit
    `source-tree` holds the code no module holds: a file only there belongs to no module."""
    import modules
    try:
        graph = json.loads(Path(modules.ensure_graph(manifest)["graph"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        return {}
    out: dict[str, tuple[int, str]] = {}
    for module in graph.get("modules", []):
        files = [] if module.get("kind") == "source-tree" else module.get("files") or []
        for file in files:
            if file not in out or len(files) < out[file][0]:
                out[file] = (len(files), module["name"])
    return {file: name for file, (_size, name) in out.items()}


def at_level(flow: dict, level: str, modules_of: dict[str, str]) -> dict:
    """One flow seen at a level; the flow itself does not change.

    `logico` contracts the symbols of one module into a node and keeps a symbol with
    no module as it is; `dati` keeps the store accesses; `ux` keeps the user
    actions and who shows the data. Every contracted link counts the links it stands for.
    """
    if level == "fisico":
        return flow
    if level not in LEVELS:
        raise ValueError(f"level must be one of {', '.join(LEVELS)}")
    edges = flow["edges"]
    if level == "dati":
        edges = [edge for edge in edges if edge["type"] in ("scrive", "legge")]
    elif level == "ux":
        edges = [edge for edge in edges if edge["type"] in ("attiva", "legge")]

    def seen_as(node: str) -> str:
        if level != "logico" or "::" not in node:
            return node
        module = modules_of.get(node.split("::", 1)[0])
        return f"module:{module}" if module else node

    merged: dict[tuple, dict] = {}
    for edge in edges:
        source, target = seen_as(edge["from"]), seen_as(edge["to"])
        if source == target:
            continue
        key = (source, target, edge["type"], edge.get("origin"), edge.get("confidence"),
               edge.get("resolver"), bool(edge.get("conflict")))
        kept = merged.setdefault(key, {**edge, "from": source, "to": target, "links": 0})
        kept["links"] += 1
    reached = {seen_as(node) for node in flow["nodes"]}
    nodes = sorted({seen_as(flow["start"])}
                   | {node for edge in merged.values() for node in (edge["from"], edge["to"]) if node in reached})
    return {**flow, "level": level, "nodes": nodes, "edges": list(merged.values())}


# ---------------------------------------------------------------- flow cards

CARD_TYPES = ("dati", "ux", "servizio", "dispositivo", "misto")
# A card is prose a model writes; its `file:line` citations have no grammar.
_CITATION = re.compile(r"([\w.@-][\w./@\[\]+-]*\.[A-Za-z0-9]+):(\d+)")


def check_card(card, flow: dict) -> dict:
    """A flow card a model wrote, refused unless every line cites a step of the flow.

    `card` is `{name, type, text}`; each nonempty line of `text` cites at least one
    `file:line` that is the site of a link of the flow, so nothing outside the flow's
    list enters the card.
    """
    if not isinstance(card, dict) or set(card) != {"name", "type", "text"}:
        raise ValueError("card is {name, type, text}")
    if not isinstance(card["name"], str) or not 0 < len(card["name"].strip()) <= 200:
        raise ValueError("card name is text of at most 200 characters")
    if card["type"] not in CARD_TYPES:
        raise ValueError("card type is one of " + ", ".join(CARD_TYPES))
    if not isinstance(card["text"], str) or not 0 < len(card["text"]) <= 8000:
        raise ValueError("card text is text of at most 8000 characters")
    sites = {edge["site"] for edge in flow["edges"]}
    for number, line in enumerate(card["text"].splitlines(), 1):
        if not line.strip():
            continue
        cited = {f"{path}:{row}" for path, row in _CITATION.findall(line)}
        if not cited & sites:
            raise ValueError(f"card line {number} cites no step of the flow: {line.strip()[:120]}")
    return card


def card_files(flow: dict) -> list[str]:
    return sorted({node.split("::", 1)[0] for node in flow["nodes"] if "::" in node}
                  | {edge["site"].rsplit(":", 1)[0] for edge in flow["edges"]})


# ---------------------------------------------------------------- units

def units(links: dict, sizes: dict[str, int], perimeter: list[str], limit: int, share: int | None = None) -> dict:
    """The perimeter's files in units of at most `limit` bytes, following the flows.

    Each entry point's flow gives its files in the order the flow meets them. The
    writers and readers of one store key form a block that is never split while it
    fits the limit. A file shared by two flows goes in both units; files no flow
    touches follow by path, as `pack()` does. Every perimeter file is assigned.

    With `share`, a file is a member of at most that many units: in the others it
    is `context`, a file to consult and not to judge.
    """
    def inside(file):
        return any(p == "." or file == p or file.startswith(p.rstrip("/") + "/") for p in perimeter)

    files_of = lambda symbols: [s.split("::", 1)[0] for s in symbols if "::" in s]  # noqa: E731
    blocks_of: dict[str, list[str]] = {}
    for key, store in links["stores"].items():
        block = list(dict.fromkeys(f for f in files_of(store["writes"] + store["reads"]) if inside(f)))
        for file in block:
            blocks_of.setdefault(file, block)
    out, cuts = [], []
    for entry in links["entries"]:
        flow = trace(links, entry["symbol"], "from")
        blocks, placed = [], set()
        for node in [flow["start"]] + [edge["to"] for edge in flow["edges"]]:
            for file in files_of([node]):
                block = [item for item in blocks_of.get(file, [file]) if inside(item) and item not in placed]
                if block:
                    blocks.append(block)
                    placed.update(block)
        groups = _pack_blocks(blocks, sizes, limit)
        if len(groups) > 1:
            for edge in flow["edges"]:
                ends = files_of([edge["from"], edge["to"]])
                if len(ends) == 2 and not any(set(ends) <= set(g) for g in groups):
                    cuts.append({"entry": entry["symbol"], "edge": [edge["from"], edge["to"]], "type": edge["type"],
                                 "files": ends})
        out.extend({"files": group, "entries": [entry["symbol"]]} for group in groups)
    out = _merge_units(out, sizes, limit)
    if share:
        # The units that hold most of a shared file's flows keep it; the others consult it.
        members = defaultdict(int)
        for unit in out:
            kept_files = []
            for file in unit["files"]:
                if members[file] < share:
                    members[file] += 1
                    kept_files.append(file)
                else:
                    unit.setdefault("context", []).append(file)
            unit["files"] = kept_files
        out = _merge_units([unit for unit in out if unit["files"]], sizes, limit)
    assigned = {file for unit in out for file in unit["files"]}
    rest = sorted(f for f in sizes if inside(f) and f not in assigned)
    for group in _pack_blocks([[f] for f in rest], sizes, limit):
        out.append({"files": group, "entries": []})
    # A link is cut only when no unit holds both its ends, as members or as context.
    membership = defaultdict(set)
    for index, unit in enumerate(out):
        for file in (*unit["files"], *unit.get("context", ())):
            membership[file].add(index)
    cuts = [{key: value for key, value in cut.items() if key != "files"} for cut in cuts
            if all(file in membership for file in cut["files"])
            and membership[cut["files"][0]].isdisjoint(membership[cut["files"][1]])]
    # A store has no file of its own. Count the split between its writers and readers
    # against the final units, including stores for which no entry point was found.
    for key, store in sorted(links["stores"].items()):
        writers = set(files_of(store["writes"])) & membership.keys()
        readers = set(files_of(store["reads"])) & membership.keys()
        for writer in sorted(writers):
            separate = sorted(reader for reader in readers if membership[writer].isdisjoint(membership[reader]))
            if separate:
                cuts.append({"type": "store", "store": key, "writer_file": writer, "reader_files": separate})
    counts = defaultdict(int)
    for unit in out:
        unit["bytes"] = sum(sizes.get(file, 0) for file in unit["files"])
        if unit.get("context"):
            unit["context_bytes"] = sum(sizes.get(file, 0) for file in unit["context"])
        for file in unit["files"]:
            counts[file] += 1
    distinct = sorted(f for f in sizes if inside(f))
    oversized = [{"file": file, "bytes": sizes[file], "limit": limit} for file in distinct if sizes[file] > limit]
    return {"units": out, "cuts": cuts, "oversized": oversized, "files": len(distinct),
            "assigned": sum(1 for f in distinct if counts[f]), "in_several_units": sum(1 for f in distinct if counts[f] > 1)}


def _merge_units(found: list[dict], sizes: dict[str, int], limit: int) -> list[dict]:
    """Units that share files, or that fit together, become one: fewer units, fewer repeated files."""
    weight = lambda files: sum(sizes.get(file, 0) for file in files)  # noqa: E731
    kept: list[dict] = []
    for unit in sorted(found, key=lambda u: (-weight(u["files"]), u["entries"], u["files"])):
        room = [(weight(set(unit["files"]) & set(k["files"])), weight(k["files"]), -index, k)
                for index, k in enumerate(kept) if weight(set(unit["files"]) | set(k["files"])) <= limit]
        if not room:
            kept.append({key: list(value) for key, value in unit.items()})
            continue
        holder = max(room, key=lambda item: item[:3])[3]
        for key in ("files", "entries", "context"):
            added = [item for item in unit.get(key, []) if item not in holder.get(key, [])]
            if added:
                holder.setdefault(key, []).extend(added)
        if "context" in holder:
            holder["context"] = [file for file in holder["context"] if file not in holder["files"]]
    return kept


def _pack_blocks(blocks: list[list[str]], sizes: dict[str, int], limit: int) -> list[list[str]]:
    """Blocks in order, a new group when the next block would pass the limit; a block larger
    than the limit is split by file, and a file larger than the limit stands alone."""
    groups, size = [], 0
    for block in blocks:
        weight = sum(sizes.get(f, 0) for f in block)
        if weight > limit:
            for file in block:
                if groups and size + sizes.get(file, 0) <= limit:
                    groups[-1].append(file)
                    size += sizes.get(file, 0)
                else:
                    groups.append([file])
                    size = sizes.get(file, 0)
            continue
        if groups and size + weight <= limit:
            groups[-1].extend(block)
            size += weight
        else:
            groups.append(list(block))
            size = weight
    return groups


def file_sizes(manifest: Path) -> dict[str, int]:
    with open_snapshot(manifest) as store:
        return {rel: int(entry.get("size") or 0) for rel, entry in snapshot.file_headers(store).items()}


# ---------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("links", "trace", "units", "candidates", "shapes", "paths"):
        command = sub.add_parser(name)
        command.add_argument("manifest", type=Path)
        command.add_argument("--rules", type=Path, help="default: the rules recorded beside this snapshot")
        if name in ("candidates", "shapes", "paths"):
            command.add_argument("--offset", type=int, default=0)
            command.add_argument("--limit", type=int, default=20)
    paths = sub.choices["paths"].add_mutually_exclusive_group()
    paths.add_argument("--id", help="read the numbered evidence of this card")
    paths.add_argument("--decision", type=Path, help="record a JSON path decision for this run")
    paths.add_argument("--about", help="reopen a named flow from the saved map")
    paths.add_argument("--next", action="store_true", help="read the next entry to review")
    paths.add_argument("--effects", action="store_true", help="list writes without a proven path from any entry")
    sub.choices["units"].add_argument("--perimeter", action="append", required=True)
    sub.choices["units"].add_argument("--limit", type=int, default=120_000)
    sub.choices["units"].add_argument("--share", type=int, default=None,
                                      help="a file is a member of at most this many units, context in the others")
    trace_parser = sub.choices["trace"]
    group = trace_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from", dest="start_from")
    group.add_argument("--to", dest="start_to")
    group.add_argument("--through", dest="start_through")
    trace_parser.add_argument("--boundary", action="append", default=None)
    trace_parser.add_argument("--level", choices=LEVELS, default="fisico")
    args = parser.parse_args(argv)
    manifest = args.manifest.resolve()
    from run_store import store_of
    root = store_of(manifest)
    delegated = args.command == "paths" and (args.decision or args.about)
    if root is not None and not delegated:
        import confinement
        import flow_paths
        with confinement.project_lock(snapshot.store_project(root)):
            flow_paths.recover(manifest)
            return _cli_query(args, manifest, parser)
    return _cli_query(args, manifest, parser)


def _cli_query(args, manifest, parser):
    if gate := snapshot.query_gate(manifest):
        print(json.dumps(gate))
        return 1
    if args.command in ("candidates", "shapes", "paths") and (args.offset < 0 or not 1 <= args.limit <= 1000):
        parser.error("offset must be nonnegative and limit between 1 and 1000")
    recorded = manifest.with_name("flow-rules.json")
    rules = load_rules(args.rules) if args.rules else load_rules(recorded) if recorded.is_file() else []
    if args.command in ("candidates", "shapes", "paths"):
        import entries
        import flow_questions
        import system_brief
        import flow_paths
        if args.command == "candidates":
            result = system_brief.candidate_page(entries.cached_syntax(manifest), manifest.parent.parent.name,
                                                 args.offset, args.limit)
        elif args.command == "shapes":
            result, _ = flow_questions.page(manifest, rules, args.offset, args.limit)
        elif args.decision or args.about:
            from mcp_service import MapService
            from run_store import store_of
            root = store_of(manifest)
            if root is None or manifest.name not in {"manifest.sqlite", "manifest.json"}:
                parser.error("--decision and --about need a manifest from a Daodan run")
            project = snapshot.store_project(root)
            relative = root.relative_to(project).as_posix()
            service = MapService(project, None if relative == snapshot.CANONICAL_STORE else relative)
            run = manifest.parent.parent.name
            if args.decision:
                decision = json.loads(args.decision.read_text(encoding="utf-8"))
                result = service.flows(run, rules=rules if args.rules else None, trace_decision=decision)
            else:
                if args.rules:
                    parser.error("--about uses the rules saved with this run")
                result = service.flows(run, about=args.about)
        elif args.next:
            result = flow_paths.next_question(manifest, rules)
        elif args.effects:
            result = flow_paths.orphan_effects(manifest, rules, args.offset, args.limit)
        else:
            result = flow_paths.page(manifest, rules, args.offset, args.limit, card_id=args.id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return int(result.get("status") == "refused")
    links = cached_links(manifest, rules)
    if args.command == "links":
        print(json.dumps(links, indent=2, sort_keys=True))
        return 0
    if args.command == "units":
        result = units(links, file_sizes(args.manifest.resolve()), args.perimeter, args.limit, args.share)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    start, direction = next((value, name) for value, name in ((args.start_from, "from"), (args.start_to, "to"),
                                                                (args.start_through, "through")) if value)
    flow = trace(links, start, direction, args.boundary)
    if direction != "through":
        flow = at_level(flow, args.level, file_modules(args.manifest.resolve()) if args.level == "logico" else {})
    print(json.dumps(flow, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
