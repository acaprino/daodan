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
  `handle = store[KEY]`; a receiver with no such assignment is not this store). With `actions_in`
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

A value counts only when it is a literal or a constant bound to one; a computed
one is a gap, never a guess. A store link needs the same store and key, a route
link the same service and method and a path schema that meets: the most literal
route wins, a tie is an uncertain link, a gap with its candidates. External modules of the module graph are
nodes too: a symbol in a file an external module cites as evidence uses it. Code outside
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
from functools import cache
from pathlib import Path
from typing import Callable, NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import edge_view  # noqa: E402
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

RULES_SCHEMA = "daodan/flow-rules/v1"
LINKS_SCHEMA = "daodan/flow-links/v3"  # observed destinations carry their own recorder and confidence
FLOW_SCHEMA = "daodan/flow/v1"
LINKS = ("scrive", "legge", "rotta", "offre", "attiva", "ingresso")
MAX_EDGES = 5000
MODULE = "<module>"  # the node of the code a file runs outside any named function
_FIELDS = {"callee", "written", "attribute", "in", "link", "store", "key", "actions_in", "route", "strip",
           "decorates", "handler", "entry", "node_type"}
NODE_TYPES = ("attore", "schermata", "funzionalità", "servizio o API", "gateway", "database", "coda",
              "autenticazione", "dispositivo", "filesystem", "altro")
_ARG = re.compile(r"(arg|part)(\d+)$")
_NESTED = re.compile(r"arg(\d+)\.(arg\d+|[A-Za-z_$][\w$]*)(?:\|(.*))?$")
_IDENT = re.compile(r"[A-Za-z_$][\w$]*$")
_STRING = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1$""", re.S)
_SELECTOR = re.compile(r"""^\(?\s*([A-Za-z_$][\w$]*)\s*(?::[^)=]*)?\)?\s*=>\s*\1\s*\.\s*([A-Za-z_$][\w$]*)""")
_LAMBDA = re.compile(r"^lambda\s+([A-Za-z_]\w*)\s*:\s*\1\s*\.\s*([A-Za-z_]\w*)")
_KEY = re.compile(r"""^\s*(['"]?)([A-Za-z_$][\w$]*)\1\s*(?::|,|$)""")
_PROPERTY = re.compile(r"""(['"]?)([A-Za-z_$][\w$]*)\1\s*:\s*(?:async\s+)?$""")
_HOLDER = re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:await\s+)?$")
_UNPACKED = re.compile(r"(?:const|let|var)\s*\{([^}]*)\}\s*=\s*(?:await\s+)?$")
_ARROW = re.compile(r"^(?:async\s+)?(?:\([^()]*\)|[A-Za-z_$][\w$]*)\s*=>\s*")
_ATTRIBUTE = re.compile(
    r"\b([A-Za-z]\w*)=\{\s*((?:async\s+)?\([^()]*\)\s*=>\s*)?(?:void\s+)?([A-Za-z_$][\w$]*)\s*([}(.]?)")


# ---------------------------------------------------------------- rules

def load_rules(path: Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != RULES_SCHEMA or not isinstance(payload.get("rules"), list):
        raise ValueError(f"rules must be {RULES_SCHEMA} with a rules list")
    return validate_rules(payload["rules"])


def validate_rules(rules: list) -> list[dict]:
    for index, rule in enumerate(rules):
        where = f"rule {index}"
        if not isinstance(rule, dict) or rule.get("link") not in LINKS:
            raise ValueError(f"{where}: link must be one of {', '.join(LINKS)}")
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
        if rule["link"] in ("rotta", "offre") and set(rule["route"]) != {"service", "method", "path"}:
            raise ValueError(f"{where}: route has exactly service, method and path")
        if "handler" in rule:
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

    def after(self, rel: str, line: int, column: int) -> str | None:
        """Text from a 1-based line and a byte column to the end of the file."""
        lines = self.lines(rel)
        if lines is None or not 1 <= line <= len(lines):
            return None
        head = lines[line - 1].encode("utf-8")[column:].decode("utf-8", errors="replace")
        return "\n".join([head, *lines[line:]])

    def before(self, rel: str, line: int, column: int) -> str:
        """Text of a line up to a byte column."""
        lines = self.lines(rel)
        if lines is None or not 1 <= line <= len(lines):
            return ""
        return lines[line - 1].encode("utf-8")[:column].decode("utf-8", errors="replace")


def _enclosed(text: str, start: int) -> int | None:
    """Index after the bracket that closes the one at `start`, quotes respected."""
    depth, quote, escaped = 0, None, False
    for index in range(max(start, 0), len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def mask_comments(text: str, python: bool) -> str:
    """The text with its comments blanked, same length and same line breaks.

    A comment can hold an odd quote (`// the user's`) that would otherwise open a
    string and hide the rest of a call. Strings are kept: `//` in a URL is no comment,
    and in Python `//` is a division, so only `#` starts a comment there.
    """
    out, index, size, quote = list(text), 0, len(text), None

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if out[position] != "\n":
                out[position] = " "

    while index < size:
        char = text[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if text.startswith(quote, index):
                index += len(quote)
                quote = None
                continue
            if char == "\n" and len(quote) == 1 and quote != "`":
                quote = None
            index += 1
            continue
        if python and text.startswith(('"""', "'''"), index):
            quote = text[index:index + 3]
            index += 3
        elif char in "'\"" or (char == "`" and not python):
            quote = char
            index += 1
        elif (python and char == "#") or (not python and text.startswith("//", index)):
            end = text.find("\n", index)
            end = size if end < 0 else end
            blank(index, end)
            index = end
        elif not python and text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = size if end < 0 else end + 2
            blank(index, end)
            index = end
        else:
            index += 1
    return "".join(out)


def call_arguments(text: str) -> list[str] | None:
    """Top-level arguments of the call whose callee ends where `text` starts."""
    start = text.find("(")
    if start < 0 or text[:start].strip():
        return None
    depth, quote, escaped, current, args = 0, None, False, [], []
    for char in text[start + 1:]:
        if quote:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                args.append("".join(current).strip())
                return [arg for arg in args if arg] if args != [""] else []
            depth -= 1
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    return None


def object_keys(text: str) -> list[str] | None:
    """Keys an object literal names, or those of every object a function argument returns.

    A spread or a computed key adds nothing; with no named key at all the answer is None.
    """
    text = text.strip()
    arrow = _ARROW.match(text)
    if arrow:
        body = text[arrow.end():].strip()
        if body.startswith("("):
            end = _enclosed(body, 0)
            return object_keys(body[1:end - 1]) if end else None
        keys = []
        for found in re.finditer(r"\breturn\s*\(?\s*(?=\{)", body):
            end = _enclosed(body, found.end())
            if end:
                keys += object_keys(body[found.end():end]) or []
        return list(dict.fromkeys(keys)) or None
    if not (text.startswith("{") and text.endswith("}")):
        return None
    keys = [match.group(2) for part in call_arguments("(" + text[1:-1] + ")") or []
            if (match := _KEY.match(part))]
    return keys or None


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
        self.reads = defaultdict(list)
        for ref in view["reads"]:
            span = ref.get("span") or [None, None]
            self.reads[(ref["file"], span[0], span[1])].append(ref["target_id"])
        self.called = defaultdict(list)
        for ref in view["references"]:
            if ref["resolution"] == "resolved":
                self.called[ref["caller"]].append(ref["target_id"])
        self.imports = defaultdict(set)
        for source, target in db.execute("SELECT source,target FROM sem_edges"):
            self.imports[source].add(target)
        self.imported = defaultdict(set)
        for file, name in db.execute("SELECT file,name FROM sem_bindings WHERE kind='import'"):
            self.imported[file].add(name)
        self._nodes: dict[str, str | None] = {}
        self.route_named: dict[str, str] = {}  # a function written in place as a route handler: its route

    def targets(self, name: str, file: str, line: int, column: int, kinds: tuple) -> list[str]:
        """Declarations an identifier names: its resolved read, else the one module-level
        declaration of that name in the file or in a file it imports, else the only one
        in the project when the file imports that name."""
        resolved = [t for t in self.reads.get((file, line, column), [])
                    if self.declarations.get(t or "", {}).get("kind") in kinds]
        if resolved:
            return resolved
        named = [d for d in self.by_name.get(name, ()) if d["kind"] in kinds]
        near = [d["id"] for d in named if d["file"] == file or d["file"] in self.imports.get(file, ())]
        if len(near) == 1:
            return near
        return [named[0]["id"]] if len(named) == 1 and name in self.imported.get(file, ()) else []

    def property_label(self, declaration: dict) -> str | None:
        """The property an anonymous function is the value of: `name: (...) => ...`."""
        match = _PROPERTY.search(self.source.before(declaration["file"], declaration["line"], declaration["column"]))
        return match.group(2) if match else None

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

    def enclosing(self, file: str, line: int, skip: str | None = None) -> dict | None:
        """The innermost named function whose lines hold `line`."""
        holders = [d for d in self.functions.get(file, ()) if d["name"] != "(anonymous)" and d["id"] != skip
                   and d["line"] <= line <= (d["end"] or d["line"])]
        return max(holders, key=lambda d: (d["line"], d["column"])) if holders else None

    def decorated(self, file: str, line: int) -> str | None:
        """The function a decorator on this line decorates: the first declaration below it."""
        below = sorted((d for d in self.declarations.values()
                        if d["file"] == file and d["kind"] in ("function", "class", "method") and d["line"] > line),
                       key=lambda d: d["line"])
        return self.node(below[0]["id"]) if below else None

    def literal(self, text: str, file: str, line: int, column: int) -> str | None:
        """The text of a literal, or of a constant bound to one; None when computed.
        A template keeps its `${...}` parts for the caller to accept or refuse."""
        text = text.strip()
        match = _STRING.match(text)
        if match:
            return match.group(2)
        if not _IDENT.match(text):
            return None
        for target in self.targets(text, file, line, column, ("binding",)):
            binding = self.declarations[target]
            rest = self.source.after(binding["file"], binding["line"], 0)
            found = re.match(r"[^=\n]*\b" + re.escape(binding["name"]) + r"\b[^=\n]*=\s*(['\"`])([^'\"`\n]*)\1", rest or "")
            if found:
                return found.group(2)
        return None

    def handler(self, text: str, file: str, line: int, column: int) -> str | None:
        """The function an action argument names, directly or as the one call of an arrow."""
        text = text.strip()
        if _IDENT.match(text):
            found = self.targets(text, file, line, column, ("function", "method"))
            return self.node(found[0]) if found else None
        arrow = next((d for d in self.functions.get(file, ()) if d["line"] == line
                      and d["column"] == column and d["name"] == "(anonymous)"), None)
        if arrow is None:
            return None
        calls = self.called.get(arrow["id"], [])
        return self.node(calls[0]) if len(calls) == 1 else None

    def written_function(self, file: str, line: int, column: int) -> dict | None:
        """The function written at this place of an argument, named or not."""
        return next((d for d in self.functions.get(file, ()) if d["line"] == line and d["column"] == column), None)

    def passed_function(self, text: str, file: str, line: int, column: int) -> str | None:
        """The function an argument passes by name: `handler`, or `module.handler` from a file this one imports."""
        text = text.strip()
        if _IDENT.match(text):
            found = self.targets(text, file, line, column, ("function", "method"))
            return self.node(found[0]) if found else None
        if not re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+", text):
            return None
        last = text.rsplit(".", 1)[1]
        found = self.reads.get((file, line, column + text.rfind(".") + 1), [])
        found = [t for t in found if self.declarations.get(t or "", {}).get("kind") in ("function", "method")] or \
            [d["id"] for f in sorted(self.imports.get(file, ())) for d in self.functions.get(f, ()) if d["name"] == last]
        return self.node(found[0]) if len(found) == 1 else None

    def local_function(self, name: str, file: str, line: int) -> str | None:
        """A function of that name declared inside a function that holds `line`, else at module level."""
        inside = []
        for declaration in self.functions.get(file, ()):
            if declaration["name"] != name or declaration.get("contract"):
                continue
            holder = self.enclosing(file, declaration["line"], skip=declaration["id"])
            if holder is not None and holder["line"] <= line <= (holder["end"] or holder["line"]):
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


def _position(base_line: int, base_column: int, text_before: str, arg_text: str) -> tuple[int, int]:
    """Line and byte column where an argument starts, from the text between the callee end and it."""
    lead = text_before + arg_text[:len(arg_text) - len(arg_text.lstrip())]
    rows = lead.split("\n")
    if len(rows) == 1:
        return base_line, base_column + len(rows[0].encode("utf-8"))
    return base_line + len(rows) - 1, len(rows[-1].encode("utf-8"))


def _arguments_with_positions(text: str, line: int, column: int):
    args = call_arguments(text)
    if args is None:
        return None
    out, cursor = [], text.find("(") + 1
    for arg in args:
        at = text.find(arg, cursor)
        out.append((arg, *_position(line, column, text[:at], "")))
        cursor = at + len(arg)
    return out


def _nested(spec: str, call: dict, facts, strip: str, template: bool = False):
    """`argN.argM`, argument M of the call written as argument N; `argN.key`, the literal value of `key`
    in the object written as argument N; after `|`, the value when that argument or key is absent."""
    match = _NESTED.match(spec)
    index, inner, default = int(match.group(1)), match.group(2), match.group(3)
    if index >= len(call["args"]):
        return default
    text, line, column = call["args"][index]
    if inner.startswith("arg") and inner[3:].isdigit():
        called = re.match(r"[A-Za-z_$][\w$.]*\s*(?=\()", text)
        args = _arguments_with_positions(text[called.end():], *_position(line, column, text[:called.end()], "")) \
            if called else None
        if args is None:
            return None
        return _value(inner, {**call, "args": args}, facts, strip, template) if int(inner[3:]) < len(args) else default
    if not (text.startswith("{") and text.endswith("}")):
        return None
    parts = call_arguments("(" + text[1:-1] + ")") or []
    if any(part.strip().startswith("...") for part in parts):
        return None  # a spread may hold the key
    for part in parts:
        found = re.match(r"""\s*(['"]?)([A-Za-z_$][\w$]*)\1\s*:\s*(.+)$""", part, re.S)
        if found and found.group(2) == inner:
            return facts.literal(found.group(3), call["file"], -1, -1)
    return default


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
    text, line, column = call["args"][index]
    value = facts.literal(text, call["file"], line, column)
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


_PATH_BASE = re.compile(r"^[A-Za-z][\w+.-]*://[^/]*")  # scheme and host
_PATH_PARAMETER = re.compile(r"<[^<>/]*>|\{[^{}/]*\}")  # a parameter declared inside a segment


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
    text = re.split(r"[?#]", text, maxsplit=1)[0]
    rest = _PATH_BASE.sub("", text.lstrip("\0"), count=1)
    if not rest or rest != text and not rest.startswith("/"):
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
        pattern = "".join("[^/]*" if part == "{}" else re.escape(part) for part in re.split(r"(\{\})", asked))
        return 0 if re.fullmatch(pattern, offered) else None
    return None


def _rest_meet(asked: tuple, offered: tuple) -> tuple | None:
    """Same service, method and number of segments, every segment meeting; (True, total) when no hole has to
    equal a literal, the most literal route first; (False, 0) otherwise, so loose candidates always tie."""
    if asked[:2] != offered[:2]:
        return None
    calls, routes = asked[2].strip("/").split("/"), offered[2].strip("/").split("/")
    grades = [_segment_grade(c, r) for c, r in zip(calls, routes)] if len(calls) == len(routes) else [None]
    if None in grades:
        return None
    return (True, sum(grades)) if min(grades) >= 1 else (False, 0)


REST = LinkType("rest", ("rotta", "offre"), _rest_key, _rest_meet)  # the guide's "metodo e schema del percorso"


_HANDLE = re.compile(r"=\s*(?:await\s+)?[A-Za-z_$][\w$.]*?(?:\.([A-Za-z_$][\w$]*)|\[\s*([^\]]+?)\s*\])\s*(?:#.*|//.*|;)?$")


def _handle_key(call, facts) -> str | None:
    """The key of the store handle a call is made on: `handle = store.key` or `handle = store[KEY]`,
    assigned in the same file."""
    receiver = ".".join(call["parts"][:-1])
    if not receiver:
        return None
    assigned = re.compile(r"(?<![\w$.])" + re.escape(receiver) + r"\s*(?::[^=]*)?(?==[^=])")
    for number, line in enumerate(facts.source.lines(call["file"]) or [], 1):
        found = assigned.search(line)
        handle = _HANDLE.search(line[found.end():]) if found else None
        if handle and handle.group(1):
            return handle.group(1)
        if handle:
            column = len(line[:found.end() + handle.start(2)].encode("utf-8"))
            value = facts.literal(handle.group(2), call["file"], number, column)
            if value is not None and "${" not in value:
                return value
    return None


def _keys(spec: str, call, facts) -> list[str] | None:
    if spec == "holder":
        key = _handle_key(call, facts)
        return [key] if key else []
    if spec == "member":
        end = _enclosed(call["text"], call["text"].find("("))
        member = re.match(r"\s*\??\.\s*([A-Za-z_$][\w$]*)", call["text"][end:]) if end else None
        if member:
            return [member.group(1)]
        unpacked = _UNPACKED.search(call["before"])
        if unpacked:
            return [name.split(":")[0].strip() for name in unpacked.group(1).split(",")
                    if name.strip() and not name.strip().startswith("...")]
        # The whole value held in a variable: its keys are the properties read on that variable
        # inside the function that declares it, anonymous or not, and no further.
        holder = _HOLDER.search(call["before"])
        if holder is None or not call.get("scope_end"):
            return None
        lines = (facts.source.lines(call["file"]) or [])[call["line"] - 1:call["scope_end"]]
        read = re.compile(r"(?<![\w$.])" + re.escape(holder.group(1)) + r"\s*\??\.\s*([A-Za-z_$][\w$]*)")
        return list(dict.fromkeys(name for line in lines for name in read.findall(line))) or None
    if _ARG.match(spec):
        value = _value(spec, call, facts)
        return [value] if value is not None else None
    if not call["args"]:
        return None
    text = call["args"][0][0]
    if spec == "selector":
        text = text.strip()
        wrapped = re.match(r"[A-Za-z_$][\w$.]*\s*(?=\()", text)
        if wrapped and not _ARROW.match(text):
            # A selector passed through a wrapper: the wrapper's first argument selects.
            inner = call_arguments(text[wrapped.end():])
            text = inner[0].strip() if inner else text
        match = _SELECTOR.match(text) or _LAMBDA.match(text)
        if match:
            return [match.group(2)]
        # A selector that builds a value from several fields reads each field it names.
        parameter = re.match(r"\(?\s*([A-Za-z_$][\w$]*)\s*(?::[^)=]*)?\)?\s*=>", text)
        fields = re.findall(r"(?<![\w$.])" + re.escape(parameter.group(1)) + r"\s*\??\.\s*([A-Za-z_$][\w$]*)",
                            text[parameter.end():]) if parameter else []
        return list(dict.fromkeys(fields)) or None
    return object_keys(text) if spec == "object" else None


# ---------------------------------------------------------------- links

def _call_args(facts: Facts, ref: dict):
    """The call's text from its callee on, comments masked, and its arguments with their positions."""
    span = ref.get("span") or [None, None, None, None]
    text = facts.source.after(ref["file"], span[2], span[3])
    if text is not None:
        text = mask_comments(text, ref["file"].endswith((".py", ".pyi")))
    return text, (_arguments_with_positions(text, span[2], span[3]) if text is not None else None)


def _handler_index(spec: str, args: list) -> int:
    return len(args) - 1 if spec == "last" else int(spec[3:])


def _route_handler(facts: Facts, spec: str, args: list, file: str) -> str | None:
    """The symbol a route registered with a handler argument belongs to."""
    index = _handler_index(spec, args)
    if not 0 <= index < len(args):
        return None
    text, line, column = args[index]
    written = facts.written_function(file, line, column)
    return facts.node(written["id"]) if written else facts.passed_function(text, file, line, column)


def _name_written_handlers(facts: Facts, view: dict, rules: list[dict]) -> None:
    """A function written in place as a route handler is named by its route, before any link reads names."""
    if not rules:
        return
    for ref in view["references"]:
        parts = [str(part) for part in ref.get("parts") or []]
        for rule in (r for r in rules if _written(r, parts, ref["file"])):
            text, args = _call_args(facts, ref)
            index = _handler_index(rule["handler"], args or [])
            if not args or not 0 <= index < len(args):
                continue
            written = facts.written_function(ref["file"], args[index][1], args[index][2])
            span = ref.get("span") or [None, None, None, None]
            call = {"file": ref["file"], "line": span[0], "parts": parts, "args": args, "text": text}
            method, path = (_value(rule["route"][k], call, facts, rule.get("strip", "") if k == "path" else "")
                            for k in ("method", "path"))
            if written and written["name"] == "(anonymous)" and method and path is not None:
                facts.route_named[written["id"]] = f"{method.upper()} {path}"
    facts._nodes.clear()


def link_facts(manifest: Path, rules: list[dict], *, module_graph=None) -> dict:
    """Accesses, deduced links, entry points and gaps of a snapshot under the given rules."""
    by_callee, written, attributes = defaultdict(list), [], []
    for rule in rules:
        if "callee" in rule:
            by_callee[rule["callee"]].append(rule)
        else:
            (written if "written" in rule else attributes).append(rule)
    wanted = {rule["callee"].rsplit("::", 1)[1].split(".")[-1] for rule in rules if "callee" in rule}
    accesses, entries, actions, routes_offered, route_calls, gaps, calls = [], [], [], [], [], [], []
    held: dict[tuple[str, str], str] = {}
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = Facts(store, db, view)
        _name_written_handlers(facts, view, [r for r in written if r["link"] == "offre" and r.get("handler")])
        members = {id(rule): facts.property_functions(rule["actions_in"]) for rule in rules if rule.get("actions_in")}
        plain = []
        for ref in view["references"]:
            target = facts.named(ref.get("target_id")) if ref["resolution"] == "resolved" else None
            named = facts.node(ref.get("caller"))
            caller = named or f"{ref['file']}::{MODULE}"
            span = ref.get("span") or [None, None, None, None]
            site = f"{ref['file']}:{span[0]}"
            parts = [str(part) for part in ref.get("parts") or []]
            for end in edge_view.call_ends(ref):
                callee = facts.node(end["target_id"])
                if callee:
                    evidence = {"origin": "osservato", **{key: end[key] for key in ("resolver", "confidence", "conflict")
                                                          if key in end}} if end["confidence"] in edge_view.SEEN else {}
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
                        plain.append((ref["file"], parts[0], caller, site))
                continue
            text, args = _call_args(facts, ref)
            if args is None:
                gaps.append({"site": site, "symbol": caller, "reason": "call arguments not readable"})
                continue
            scope = facts.declarations.get(ref.get("caller") or "") or {}
            call = {"file": ref["file"], "line": span[0], "scope_end": scope.get("end"), "parts": parts,
                    "args": args, "text": text,
                    "before": facts.source.before(ref["file"], span[0], span[1])}
            for rule in matched:
                if rule["link"] == "offre" and rule.get("handler"):
                    owner = _route_handler(facts, rule["handler"], args, ref["file"])
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
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link} {rule['store']}: key not a literal"})
                    for key in keys or []:
                        found = members.get(id(rule), {}).get(key)
                        if not found:
                            accesses.append({"symbol": owner, "link": link, "store": rule["store"], "key": key, "site": site})
                        elif len(found) > 1:
                            gaps.append({"site": site, "symbol": owner, "reason": f"{rule['store']}/{key}: several functions"})
                        elif (holder := _HOLDER.search(call["before"])) and len(keys) == 1 and rule["key"] == "selector":
                            held[(ref["file"], holder.group(1))] = found[0]
                        elif _UNPACKED.search(call["before"]):
                            held[(ref["file"], key)] = found[0]
                        else:
                            calls.append({"from": owner, "to": found[0], "site": site, "origin": "dedotto"})
                elif link in REST.pair:
                    route = rule["route"]
                    key = REST.key(_value(route["service"], call, facts), _value(route["method"], call, facts),
                                   _value(route["path"], call, facts, rule.get("strip", ""), template=True))
                    if key is None:
                        gaps.append({"site": site, "symbol": owner, "reason": f"{link}: route not a literal"})
                        continue
                    record = {"symbol": owner, "key": key, "site": site}
                    (routes_offered if link == "offre" else route_calls).append(record)
                    if link == "offre":
                        entries.append({"symbol": owner, "kind": "rotta", "site": site})
                elif link == "attiva":
                    index = _handler_index(rule["handler"], args)
                    handler = (facts.handler(args[index][0], ref["file"], args[index][1], args[index][2])
                               if 0 <= index < len(args) else None)
                    if handler is None:
                        gaps.append({"site": site, "symbol": owner, "reason": "attiva: handler not a named function"})
                        continue
                    actions.append({"symbol": owner, "handler": handler, "label": _value("arg0", call, facts), "site": site})
                    entries.append({"symbol": handler, "kind": "azione", "site": site})
                elif link == "ingresso":
                    entries.append({"symbol": owner, "kind": rule["entry"], "site": site})
        # A component written as an element is rendered: React calls it, so its parent reaches it.
        for read in view["reads"]:
            file, holder, (line, column) = read["file"], read.get("caller"), (read.get("span") or [None, None])[:2]
            parts = read.get("parts") or []
            if len(parts) != 1 or not line or not facts.source.before(file, line, column).rstrip().endswith("<"):
                continue
            found = facts.targets(str(parts[0]), file, line, column, ("function", "class"))
            component = facts.node(found[0]) if len(found) == 1 else None
            if component:
                calls.append({"from": facts.node(holder) or f"{file}::{MODULE}", "to": component,
                              "site": f"{file}:{line}"})
        # A store function held in a variable is called where that variable is called.
        for file, name, caller, site in plain:
            if (file, name) in held:
                calls.append({"from": caller, "to": held[(file, name)], "site": site, "origin": "dedotto"})
        for rule in attributes:
            for action in _attribute_actions(facts, rule, held):
                actions.append(action)
                entries.append({"symbol": action["handler"], "kind": "azione", "site": action["site"]})
        external = _external_nodes(manifest, module_graph)
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
        if access["link"] == "scrive":
            edges.append({"from": access["symbol"], "to": store_node, "type": "scrive", "origin": "dedotto", "site": access["site"]})
        else:
            edges.append({"from": store_node, "to": access["symbol"], "type": "legge", "origin": "dedotto", "site": access["site"]})
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
                      "site": action["site"], "label": action["label"]})
    for module in external:
        for file in module["evidence_files"]:
            for symbol in sorted(symbols_by_file.get(file, ())):
                edges.append({"from": symbol, "to": f"module:{module['name']}", "type": "usa", "origin": "dichiarato",
                              "site": file, "status": module["status"]})
    stores = defaultdict(lambda: {"writes": set(), "reads": set()})
    for access in accesses:
        stores[f"{access['store']}/{access['key']}"]["writes" if access["link"] == "scrive" else "reads"].add(access["symbol"])
    unique = {}
    for edge in edges:
        unique.setdefault((edge["from"], edge["to"], edge["type"], edge["site"], edge["origin"],
                           edge.get("confidence"), edge.get("resolver")), edge)
    return {"schema": LINKS_SCHEMA, "manifest": str(manifest),
            "stores": {name: {"writes": sorted(v["writes"]), "reads": sorted(v["reads"])} for name, v in sorted(stores.items())},
            "entries": sorted({(e["symbol"], e["kind"]): e for e in entries}.values(), key=lambda e: (e["kind"], e["symbol"])),
            "edges": sorted(unique.values(), key=lambda e: (e["from"], e["to"], e["type"], e["site"])),
            "store_types": {rule["store"]: rule["node_type"] for rule in rules if rule.get("node_type")},
            "routes": {"offered": len({o["key"] for o in routes_offered}),
                       "called": len(route_calls), "linked": sum(1 for e in unique.values() if e.get("route"))},
            "external": [{"name": m["name"], "status": m["status"]} for m in external],
            "gaps": sorted(gaps, key=lambda g: (g["site"], g["reason"]))}


@cache
def _links_reader_digest() -> str:
    """Installed link readers and rules; one bounded read of Daodan's own code per process."""
    digest = hashlib.sha256()
    for path in (Path(__file__), SCRIPT_DIR / "edge_view.py", SCRIPT_DIR / "edge_store.py", SCRIPT_DIR / "entries.py",
                 SCRIPT_DIR / "engine_pass.py", SCRIPT_DIR.parent / "data" / "entry-queries.json"):
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def _links_stamp(manifest: Path) -> list:
    import modules
    from store_graph import source_stamp
    edges = manifest.with_name("engine-edges.sqlite")
    files = (manifest, manifest.with_name(manifest.name + "-wal"), edges, edges.with_name(edges.name + "-wal"),
             modules.graph_name(manifest), manifest.with_name(modules.LEDGER_FILE))
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


def cached_links(manifest: Path, rules: list[dict]) -> dict:
    """Reuse links only for the same inputs, reader implementation and relevant native analyzers."""
    import engine_pass
    import modules
    manifest = Path(manifest)
    destination = manifest.with_name("flow-links.json")
    try:
        kept = json.loads(destination.read_text(encoding="utf-8"))
        languages = kept.get("languages") if isinstance(kept, dict) else None
        stamp = _links_stamp(manifest)
        if (isinstance(languages, list) and all(s is None or s[-1] for s in stamp)
                and kept.get("key") == _links_key(rules, stamp, languages)):
            return kept["links"]
    except (OSError, KeyError, TypeError, ValueError):
        pass
    # link_facts also reads the module graph. Materialize it before stamping a cache miss so its first publication
    # or a refreshed ledger does not trigger a second full pass over the references.
    for _ in range(2):
        module_graph = modules.ensure_graph(manifest)
        before = _links_stamp(manifest)
        languages = []
        if manifest.with_name("engine-edges.sqlite").is_file():
            with open_snapshot(manifest) as store:
                if store.connection is not None:
                    languages = engine_pass.pass_languages(store.connection)
        links = link_facts(manifest, rules, module_graph=module_graph)
        if _links_stamp(manifest) == before:
            if all(s is None or s[-1] for s in before):
                snapshot._write_json_atomic(destination, {"key": _links_key(rules, before, languages),
                                                          "languages": languages, "links": links})
            return links
    raise ValueError("the mapping inputs changed while computing flow links; retry")


def _attribute_actions(facts: Facts, rule: dict, held: dict) -> list[dict]:
    """Handlers bound by a markup attribute: a name, or the one call of an inline function.

    A parameter passed on as the handler is no action of this symbol and a local
    value setter is no flow: both are left out without a gap.
    """
    out = []
    for file in sorted(facts.functions):
        if not _under(file, rule.get("in")):
            continue
        for number, line in enumerate(facts.source.lines(file) or [], 1):
            for match in _ATTRIBUTE.finditer(line):
                attribute, inline, name, after = match.groups()
                if not fnmatch.fnmatchcase(attribute, rule["attribute"]) or after != ("(" if inline else "}"):
                    continue
                owner = facts.enclosing(file, number)
                handler = held.get((file, name)) or facts.local_function(name, file, number)
                if owner is not None and handler is not None:
                    out.append({"symbol": facts.node(owner["id"]), "handler": handler, "label": attribute,
                                "site": f"{file}:{number}"})
    return out


def _external_nodes(manifest: Path, graph=None) -> list[dict]:
    """External modules of the module graph, with the files they cite as evidence."""
    import modules
    try:
        graph = graph if graph is not None else modules.ensure_graph(manifest)
        payload = json.loads(Path(graph["graph"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        return []
    out = []
    for module in payload.get("modules", []):
        if module.get("location") != "external":
            continue
        files = sorted({str(item.get("path") if isinstance(item, dict) else item).split("#")[0]
                        for item in module.get("evidence", [])})
        out.append({"name": module["name"], "status": module.get("status"), "evidence_files": files})
    return out


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
        for symbol in dict.fromkeys(entry["symbol"] for entry in links["entries"]):
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

    seen, followed, outside, queue = {start}, [], [], deque([start])
    scheduled, emitted = {start}, set()
    stopped = None
    while queue:
        node = queue.popleft()
        for edge, nxt in steps(node):
            if not inside(nxt):
                outside.append(edge)
                continue
            if id(edge) not in emitted:
                if len(followed) >= max_edges:
                    stopped = "budget"
                    break
                emitted.add(id(edge))
                followed.append(edge)
            seen.add(nxt)
            # A store reader or a side-effect store ends this path. A later call to the same
            # node can still expand it, independent of the order in which the paths arrived.
            terminal = (edge["type"] == "legge" if direction == "from" else
                        edge["type"] == "scrive" and nxt == edge["to"])
            if not terminal and nxt not in scheduled:
                scheduled.add(nxt)
                queue.append(nxt)
        if stopped:
            break
    files = {node.split("::", 1)[0] for node in seen if "::" in node}
    gaps = [gap for gap in links["gaps"] if gap.get("symbol") in seen or (
        not gap.get("symbol") and gap.get("site", "").rsplit(":", 1)[0] in files)]
    return {"schema": FLOW_SCHEMA, "start": start, "direction": direction,
            "nodes": sorted(seen), "edges": followed, "outside_boundary": outside, "gaps": gaps,
            "stopped": stopped, "complete": not (stopped or outside or gaps),
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
        key = (source, target, edge["type"], edge.get("origin"), edge.get("confidence"), edge.get("resolver"))
        kept = merged.setdefault(key, {**edge, "from": source, "to": target, "links": 0})
        kept["links"] += 1
    nodes = sorted({flow["start"] if level != "logico" else seen_as(flow["start"])}
                   | {node for edge in merged.values() for node in (edge["from"], edge["to"])})
    return {**flow, "level": level, "nodes": nodes, "edges": list(merged.values())}


# ---------------------------------------------------------------- flow cards

CARD_TYPES = ("dati", "ux", "servizio", "dispositivo", "misto")
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
    for name in ("links", "trace", "units"):
        command = sub.add_parser(name)
        command.add_argument("manifest", type=Path)
        command.add_argument("--rules", type=Path, required=True)
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
    links = link_facts(args.manifest.resolve(), load_rules(args.rules))
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
