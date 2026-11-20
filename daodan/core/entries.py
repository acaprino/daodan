"""Entry candidates: where a flow may start, read by the machine from what the snapshot has, without rules.

A reader is one way an entry is written (spec of 18 November 2026, section 6 point 5), one function each. A candidate
is `{reader, shape, site, symbol}`: the reader that found it, the shape it is written in, which is classified once
with one of the entry kinds or as no entry, the file and line, and the symbol the flow starts from. The model
classifies the shapes; it does not look for entries.

The residual net reads the links; the other readers read the snapshot the links come from (`candidates`), code from
its syntax tree: the grammar the snapshot read the file with, and what a framework writes is the data of
`daodan/data/entry-queries.json`, one query per grammar. `noir` reads the endpoints a ready-made tool reports.
"""
from __future__ import annotations

import json
import sys
import tomllib
from collections import defaultdict
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import edge_view  # noqa: E402
import flows  # noqa: E402
import semantic_store  # noqa: E402
from languages import _treesitter, get_adapter  # noqa: E402
from languages.sfc import mask_non_script  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

RESIDUAL, ARGUMENT, ATTRIBUTE, DECORATOR, NOIR = "residuo", "argomento", "attributo", "decoratore", "noir"
CALLS = ("chiama", "attiva")  # the links by which a symbol is called
QUERIES = json.loads((SCRIPT_DIR.parent / "data" / "entry-queries.json").read_text(encoding="utf-8"))
RECEIVERS = ("self", "this")  # the object a method is called on: D5 resolves its methods
LOCALES = {".json": json.loads, ".toml": tomllib.loads}  # the locale formats read, each by its standard reader


def _first(sites: list[str]) -> str:
    """The site of the lowest line; one without a line (a file) comes last."""
    def line(site: str) -> tuple[bool, int]:
        number = site.rpartition(":")[2]
        return (not number.isdigit(), int(number) if number.isdigit() else 0)
    return min(sites, key=line)


def residual(links: dict) -> list[dict]:
    """A symbol that calls and that nothing calls, from the links of `flows.link_facts`: a link leaves it (a call, an
    activation, the use of a library, a write or a read of a store) and no call or activation comes in. A net beside
    the readers, not the list: it also takes tests, dead code and pieces of a flow. Its site is its first link."""
    sites, called = {}, set()
    for edge in links["edges"]:
        read = edge["type"] == "legge" and edge["from"].startswith("store:")  # a read leaves its reader
        sites.setdefault(edge["to"] if read else edge["from"], []).append(edge["site"])
        if edge["type"] in CALLS:
            called.add(edge["to"])
    return [{"reader": RESIDUAL, "shape": RESIDUAL, "site": _first(sites[symbol]), "symbol": symbol}
            for symbol in sorted(sites) if symbol not in called]


def _project_names(db) -> dict[str, set[str]]:
    """By file, the names the project declares there, in any scope, and those it imports from a file of the project."""
    resolved = set(db.execute("SELECT file,module FROM sem_modules"))
    names = defaultdict(set)
    for file, name, kind, payload in db.execute("SELECT file,name,kind,payload FROM sem_bindings"):
        if kind != "import" or (file, _unpack(payload).get("module")) in resolved:
            names[file].add(name)
    return names


def _written(parts: list[str], names: set[str]) -> str:
    """The callee as written; a chain that starts at a name of the project, or at `this`, is `*` up to the called
    name, while a library's name or a global stays (`document.addEventListener`)."""
    head = parts[:-1]
    if head and (head[0] == "this" or head[0] in names):
        head = ["*"] * len(head)
    return ".".join([*head, parts[-1]])


def _text(source: bytes, node) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _query(grammar: str, section: str = "queries"):
    """The compiled query of a grammar in a section of `daodan/data/entry-queries.json`; None when it does not
    compile."""
    lines = QUERIES[section][grammar]["query"]
    lines = QUERIES[section][lines]["query"] if isinstance(lines, str) else lines
    return _treesitter.get_query(grammar, "\n".join(lines))


def _matches(source: bytes, grammar: str, section: str = "queries") -> list[dict]:
    """Each match of the grammar's query on the tree of `source`, its captures by name; none without the grammar."""
    from tree_sitter import QueryCursor

    loaded, query = _treesitter.get_parser(grammar), _query(grammar, section)
    if loaded is None or query is None:
        return []
    return [captures for _, captures in QueryCursor(query).matches(loaded[0].parse(source).root_node)]


def _file(facts: flows.Facts, file: str, template: bool, section: str | None = None) -> tuple[bytes, str | None]:
    """A file's verified text and the grammar it is read with: the snapshot's (`parser_profile`), its template's when
    `template` and it has one, else the data's for its language; with `section` (`queries` when `template`), only
    a grammar that has a query there. A script inside markup is read with the markup blanked, as its adapter reads
    it (`mask_non_script`)."""
    header = facts.store.get_file_header(file) or {}
    profile, language = header.get("parser_profile") or {}, header.get("language")
    grammar = (template and (profile.get("template") or {}).get("grammar")) or profile.get("grammar") \
        or QUERIES["grammars"].get(language)
    section = section or ("queries" if template else None)
    lines = facts.source.lines(file) if grammar and (section is None or grammar in QUERIES[section]) else None
    if lines is None:
        return b"", None
    text, adapter = "\n".join(lines), None if template or language is None else get_adapter(language)
    if hasattr(adapter, "frontmatter"):
        text = mask_non_script(text, adapter.frontmatter)[0]
    return text.encode("utf-8"), grammar


def _call(root, span: list):
    """The node of the call whose callee the span covers, with parentheses after it; None when there is none."""
    end = (span[2] - 1, span[3])
    node = root.descendant_for_point_range((span[0] - 1, span[1]), end)
    while node is not None and not ((listed := node.child_by_field_name("arguments")) is not None
                                    and tuple(listed.start_point) >= end):
        node = node.parent
    return node if node is not None and listed.children and listed.children[0].type == "(" else None


def _arguments(call, source: bytes) -> list:
    """A call's arguments from the tree: `(keyword or None, node)`, a keyword the `name` of an argument that has a
    `value`."""
    out = []
    for child in call.child_by_field_name("arguments").named_children if call is not None else ():
        name, value = child.child_by_field_name("name"), child.child_by_field_name("value")
        if not child.is_extra:
            out.append((_text(source, name), value) if name is not None and value is not None else (None, child))
    return out


def _classes(facts: flows.Facts) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for declaration in facts.declarations.values():
        if declaration["kind"] == "class":
            out[declaration["file"]].append(declaration)
    return out


def _holder(classes: dict, file: str, line: int) -> dict | None:
    """The innermost class whose lines hold `line`."""
    held = [d for d in classes.get(file, ()) if d["line"] <= line <= (d["end"] or d["line"])]
    return max(held, key=lambda d: (d["line"], d["column"])) if held else None


def _method(facts: flows.Facts, classes: dict, file: str, line: int, name: str) -> tuple[str | None, str]:
    """`self.name` and `this.name` in the language's own meaning: the method `name` of the class that encloses
    the line (the plan's D5, brought forward); else None and why: inherited or assigned at run time."""
    owner = _holder(classes, file, line)
    if owner is None:
        return None, "no class encloses it"
    qualified = f"{owner.get('qualified_name') or owner['name']}.{name}"
    found = [d for d in facts.functions.get(file, ()) if (d.get("qualified_name") or d["name"]) == qualified]
    return (facts.node(found[0]["id"]), "") if found else (None, f"{owner['name']} does not define {name}")


def _assignments(assigned: dict, file: str, source: bytes, root) -> list[tuple[str, int, object]]:
    """Every target the file assigns, with its line and value, in the order of the text: `left = value` or
    `name = value` in the tree; once per file."""
    if file not in assigned:
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            stack.extend(node.named_children)
            for target, value in (("left", "right"), ("name", "value")):
                left, right = node.child_by_field_name(target), node.child_by_field_name(value)
                if left is not None and right is not None:
                    out.append((_text(source, left), left.start_point[0] + 1, right))
        assigned[file] = sorted(out, key=lambda item: item[1])
    return assigned[file]


def _held(node, source: bytes, grammar: str) -> bool:
    """Whether an assigned value is one the object holds, not a function: the result of a call, or a text."""
    return node.child_by_field_name("arguments") is not None or \
        (grammar in QUERIES["calls"] and _literal(node, source, grammar) is not None)


def _function(facts: flows.Facts, classes: dict, anonymous: set, parsed: tuple, assigned: dict, ref: dict,
              node) -> tuple[str | None, str | None]:
    """The function an argument gives, and the gap when it is a method that does not resolve. `self.name` is the
    method of its class (`_method`); an attribute the class assigns from a call or a text is a value, none; one it
    assigns otherwise is a function given at run time, a gap. A name counts only as the snapshot resolved its read,
    a binding in scope or an import from a file of the project, at the name or at the last part of a dotted one: a
    variable that shares its name with a function is none (`len(items)`)."""
    (source, root, grammar), file = parsed, ref["file"]
    text, line, column = _text(source, node), node.start_point[0] + 1, node.start_point[1]
    receiver = node.child_by_field_name("object")
    member = node.child_by_field_name("property") or node.child_by_field_name("attribute")
    if receiver is not None and member is not None and _text(source, receiver) in RECEIVERS:
        name = _text(source, member)
        symbol, why = _method(facts, classes, file, line, name)
        owner = _holder(classes, file, line) if symbol is None else None
        values = [value for target, at, value in _assignments(assigned, file, source, root) if owner
                  and target == text and owner["line"] <= at <= (owner["end"] or owner["line"])]
        if values and all(_held(value, source, grammar) for value in values):
            return None, None
        why = f"{owner['name']} assigns {name} at run time" if values else why
        return (symbol, None) if symbol else (facts.node(ref.get("caller")) or f"{file}::{flows.MODULE}",
                                              f"handler {text} not resolved: {why}")
    places = [node, member] if member is not None else [node] if node.named_child_count == 0 else []
    read = [t for at in places for t in facts.reads.get((file, at.start_point[0] + 1, at.start_point[1]), [])]
    found = [t for t in read if facts.declarations.get(t or "", {}).get("kind") in ("function", "method")]
    if found:
        return facts.node(found[0]), None
    return (facts.handler(text, file, line, column) if (file, line, column) in anonymous else None), None


def _literal(node, source: bytes, grammar: str) -> str | None:
    """The text of a literal argument, by the grammar's `text` query; a computed text is none."""
    from tree_sitter import QueryCursor

    query = _treesitter.get_query(grammar, QUERIES["calls"][grammar]["text"])
    for _, captures in QueryCursor(query).matches(node) if query is not None else ():
        texts = [found for found in captures.get("text", []) if found.parent == node]
        if texts and _text(source, texts[0]).strip():
            return _text(source, texts[0]).strip()
    return None


def _call_label(arguments: list, source: bytes, grammar: str, positional: bool) -> str | None:
    """The label a call gives the control: a literal under a keyword of the grammar's `label`, else, `positional`,
    the first literal by position."""
    spec = QUERIES["calls"][grammar]
    for keyword, node in arguments:
        if keyword in spec["label"] and (text := _literal(node, source, grammar)):
            return text
    for keyword, node in arguments if positional and spec["positional"] else ():
        if keyword is None and (text := _literal(node, source, grammar)):
            return text
    return None


def _control_label(facts, classes, parsed, ref, on: dict, assigned: dict) -> str | None:
    """The label of the control a binding call is made for: its own call's, else that of the call assigning the
    variable it is made on, in the same class for `self` and `this` (else the same function), else a later
    setter's of the grammar (`setText("…")`)."""
    file, (source, root, grammar), parts = ref["file"], parsed, [str(part) for part in ref["parts"]]
    if grammar not in QUERIES["calls"]:
        return None
    label = _call_label(_arguments(_call(root, ref["span"]), source), source, grammar, False)
    holder = _holder(classes, file, ref["span"][0]) if parts[0] in RECEIVERS else facts.enclosing(file, ref["span"][0])
    lines = (holder["line"], holder["end"] or holder["line"]) if holder else (1, float("inf"))
    for size in range(len(parts) - 1, 0, -1):
        target = ".".join(parts[:size])
        for name, line, call in _assignments(assigned, file, source, root) if label is None else ():
            if name == target and lines[0] <= line <= lines[1] and call.child_by_field_name("arguments") is not None:
                label = label or _call_label(_arguments(call, source), source, grammar, True)
        for setter in on.get((file, tuple(parts[:size])), ()) if label is None else ():
            if str(setter["parts"][-1]) in QUERIES["calls"][grammar]["setters"] \
                    and lines[0] <= setter["span"][0] <= lines[1]:
                label = _call_label(_arguments(_call(root, setter["span"]), source), source, grammar, True)
    return label


def passed(facts: flows.Facts, view: dict, names: dict[str, set[str]]) -> list[dict]:
    """A function of the project given as an argument of a call, read from the call's node in the file's tree
    (`_function`), with the label of its control (`_control_label`). Its shape is the callee as written
    (`_written`) and the argument's position, `argN` or the keyword."""
    anonymous = {(d["file"], d["line"], d["column"]) for d in facts.declarations.values()
                 if d["kind"] in ("function", "method") and d["name"] == "(anonymous)"}
    classes, on, trees, assigned, out = _classes(facts), defaultdict(list), {}, {}, []
    for ref in view["references"]:
        if ref.get("parts"):
            on[(ref["file"], tuple(str(part) for part in ref["parts"][:-1]))].append(ref)
    for ref in view["references"]:
        file, parts, span = ref["file"], [str(part) for part in ref.get("parts") or []], ref.get("span") or [None] * 4
        if not parts or None in span[:4]:
            continue
        if file not in trees:
            source, grammar = _file(facts, file, template=False)
            loaded = _treesitter.get_parser(grammar) if grammar else None
            trees[file] = (source, loaded[0].parse(source).root_node if loaded else None, grammar)
        source, root, _ = trees[file]
        found = []
        for index, (keyword, node) in enumerate(_arguments(_call(root, span), source) if root else ()):
            symbol, gap = _function(facts, classes, anonymous, trees[file], assigned, ref, node)
            shape = f"{_written(parts, names.get(file, set()))}#{keyword or f'arg{index}'}"
            if symbol:
                found.append({"reader": ARGUMENT, "shape": shape, "site": f"{file}:{span[0]}", "symbol": symbol,
                              **({"gap": gap} if gap else {})})
        label = _control_label(facts, classes, trees[file], ref, on, assigned) if found else None
        out += [{**candidate, "label": label} if label else candidate for candidate in found]
    return out


def _code(text: str, grammar: str | None) -> dict[str, list[str]]:
    """The captures of an expression written as text in the markup, read with the `code` grammar's query."""
    source, found = text.encode("utf-8"), defaultdict(list)
    for captures in _matches(source, grammar) if grammar else ():
        for name, nodes in captures.items():
            found[name] += [_text(source, node) for node in nodes]
    return found


def _label(source: bytes, tag, element, parts: list, code: str | None) -> tuple[str | None, str | None]:
    """The label a person reads on the control, and the key when it is one: the @name of its tag (`aria-label`),
    else its text, else the @hint of its tag (`title`, `placeholder`), else the @key of a translation call inside
    the element (`t('salva')`, made text by `translated`). A computed text is no label."""
    found, words, computed = defaultdict(list), [], False
    for kind, node in parts:
        if not element.start_byte <= node.start_byte < node.end_byte <= element.end_byte:
            continue
        own, text = tag.start_byte <= node.start_byte < tag.end_byte, _text(source, node)
        if kind in ("name", "hint") and own and text.strip():
            found[kind].append(text.strip())
        elif kind == "text" and not own:
            words += text.split()
        elif kind in ("computed", "code") and not own:
            computed = True
            found["key"] += _code(text, code)["key"] if kind == "code" else []
        elif kind == "key":
            found["key"].append(text[1:-1] if len(text) > 1 and text[0] == text[-1] and text[0] in "'\"`" else text)
    for value in (*found["name"][:1], None if computed else " ".join(words), *found["hint"][:1]):
        if value:
            return value, None
    return (found["key"][0], found["key"][0]) if found["key"] else (None, None)


def _at(node) -> tuple[int, int]:
    """Where a node starts, as the snapshot writes it: line from 1, column in bytes."""
    return node.start_point[0] + 1, node.start_point[1]


def bindings(source: bytes, grammar: str) -> list[dict]:
    """The events bound in a file of markup, from its tree and its grammar's query (`QUERIES`), one per name an
    attribute binds (each branch of a conditional): the attribute as written (`shape`), its line, the name it binds
    (`handler` and where it is written, `at`, or `called` when the syntax says the event calls it) or where a
    function written in place as the handler starts (`inline`), and the label of its element with the key when it
    is one (`_label`)."""
    matches, code = _matches(source, grammar), QUERIES["queries"][grammar].get("code")
    elements = sorted(((m["tag"][0], m["element"][0]) for m in matches if "tag" in m),
                      key=lambda pair: pair[1].end_byte - pair[1].start_byte)
    parts = sorted(((kind, node) for m in matches if not {"tag", "event"} & set(m)
                    for kind, nodes in m.items() for node in nodes), key=lambda part: part[1].start_byte)
    out, seen = [], set()
    for m in matches:
        events = sorted(m.get("event", []), key=lambda node: node.start_byte)
        bound = {kind: _text(source, m[kind][0]) for kind in ("handler", "called", "method") if kind in m}
        bound.update({key: _at(m[kind][0]) for key, kind in (("at", "handler"), ("inline", "inline")) if kind in m})
        for node in m.get("code", [])[:1] if events and not bound else ():
            bound = {kind: names[0] for kind, names in _code(_text(source, node), code).items()
                     if kind in ("handler", "called")}
        once = (events[0].start_byte, *sorted(bound.items())) if events else None
        if not events or not bound or once in seen:
            continue
        seen.add(once)
        at = events[0].start_byte
        tag, element = next(((t, e) for t, e in elements if t.start_byte <= at < t.end_byte), (None, None))
        label, key = _label(source, tag, element, parts, code) if element is not None else (None, None)
        out.append({"shape": source[at:events[-1].end_byte].decode("utf-8", errors="replace"),
                    "line": events[0].start_point[0] + 1, **bound, "label": label, "key": key})
    return out


def _inline(facts: flows.Facts, made: dict, file: str, at: tuple[int, int]) -> list[str]:
    """The functions of the project a function written in place as the handler calls, in the order of the text and
    each once: the one the snapshot resolved the call to, else, for a plain name the snapshot does not know as a
    value of the scope (a prop, a state setter: `known_unrelated`), the one `local_function` finds. A call inside a
    function written within it is that function's."""
    written, out = facts.written_function(file, *at), []
    for ref in sorted(made.get(written["id"], ()) if written else (), key=lambda ref: ref.get("span") or []):
        target, parts = ref.get("target_id"), [str(part) for part in ref.get("parts") or []]
        kind = facts.declarations.get(target or "", {}).get("kind")
        if ref.get("resolution") == "resolved" and kind in ("function", "method"):
            symbol = facts.node(target)
        elif len(parts) == 1 and not ref.get("known_unrelated"):
            symbol = facts.local_function(parts[0], file, (ref.get("span") or at)[0])
        else:
            symbol = None
        if symbol and symbol not in out:
            out.append(symbol)
    return out


def _handlers(facts: flows.Facts, classes: dict, made: dict, values: set, file: str, found: dict) -> list[dict]:
    """What one binding of the markup binds, each `{symbol}` or `{symbol, gap}`: the functions a function written in
    place calls (`_inline`); the method of the enclosing class `this.name` names (`_method`); the function a name
    names (`local_function`), none when the snapshot reads the name there as a value of the scope (`values`, a
    prop). A name that the syntax says the event calls and that does not resolve (a method the class does not
    define, one of a component) is a candidate of the symbol that writes it, without handler, and says so."""
    line, name = found["line"], found.get("handler") or found.get("called")
    if "inline" in found:
        return [{"symbol": symbol} for symbol in _inline(facts, made, file, found["inline"])]
    if (file, *found.get("at", ())) in values:
        return []
    handler, why = _method(facts, classes, file, line, found["method"]) if "method" in found \
        else (facts.local_function(name, file, line), "")
    if handler:
        return [{"symbol": handler}]
    if "called" not in found:
        return []
    holder = facts.enclosing(file, line)
    return [{"symbol": facts.node(holder["id"]) if holder else f"{file}::{flows.MODULE}",
             "gap": f"handler {name} not resolved" + (f": {why}" if why else "")}]


def markup(facts: flows.Facts, view: dict) -> list[dict]:
    """A function of the project bound to an event by the markup (`bindings`), with no rule: its shape is the
    attribute as written, its label that of the element, what it binds `_handlers`'s."""
    out, classes, made = [], _classes(facts), defaultdict(list)
    for ref in view["references"]:
        made[ref.get("caller")].append(ref)
    values = {(read["file"], *read["span"][:2]) for read in view["reads"]
              if read.get("known_unrelated") and read.get("span")}
    for file in facts.store.iter_paths():
        source, grammar = _file(facts, file, template=True)
        for found in bindings(source, grammar) if grammar else ():
            candidate = {"reader": ATTRIBUTE, "shape": found["shape"], "site": f"{file}:{found['line']}"}
            label = {"label": found["label"], **({"key": found["key"]} if found["key"] else {})}
            out += [{**candidate, **bound, **label} for bound in _handlers(facts, classes, made, values, file, found)]
    return out


def _defined(value, key: str) -> str | None:
    """The text a locale's data gives a key: under the key itself, else along its dotted path through nested
    objects (`cart.save`)."""
    if isinstance(value, dict) and isinstance(value.get(key), str):
        return value[key]
    for part in key.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value if isinstance(value, str) else None


def translated(facts: flows.Facts, found: list[dict]) -> list[dict]:
    """A label that is a translation key becomes the locale's text when exactly one file of the snapshot defines it
    as a text (decision 11), read by its format's own reader (`LOCALES`); otherwise it stays the key, and
    `label_gap` says why: a locale in another format is not read."""
    keys = {c["key"] for c in found if c.get("key")}
    defined = defaultdict(dict)
    for rel in facts.store.iter_paths() if keys else ():
        reader = LOCALES.get(Path(rel).suffix.lower())
        lines = facts.source.lines(rel) if reader else None
        try:
            data = reader("\n".join(lines).lstrip("﻿")) if lines is not None else None
        except ValueError:  # json.JSONDecodeError and tomllib.TOMLDecodeError
            continue
        for key in keys:
            if (text := _defined(data, key)) is not None:
                defined[key][rel] = text
    out = []
    for c in found:
        files = defined.get(c.get("key"), {})
        if len(files) == 1:
            c = {**c, "label": next(iter(files.values()))}
        elif c.get("key"):
            c = {**c, "label_gap": f"key {c['key']} stays: {len(files)} {' or '.join(LOCALES)} files define it as "
                                   "text, and a locale in another format is not read"}
        out.append(c)
    return out


def decorators(source: bytes, grammar: str) -> list[dict]:
    """The decorators and annotations of the functions and methods of a file, from its tree and its grammar's query
    (`QUERIES["decorators"]`): the name as written without arguments (`shape`), the line of the decorator, where
    the function it decorates starts (`at`, line and column), and its first argument when that is a text literal."""
    matches = _matches(source, grammar, "decorators")
    names = sorted((m["name"][0] for m in matches if "name" in m), key=lambda node: node.start_byte)
    arguments = {m["name"][0].start_byte: _text(source, m["argument"][0]) for m in matches if "argument" in m}
    out = []
    for m in (m for m in matches if "decorator" in m):
        decorator, start = m["decorator"][0], m["definition"][0].start_point
        name = next((n for n in names if decorator.start_byte <= n.start_byte < decorator.end_byte), None)
        if name is not None:
            out.append({"shape": _text(source, name), "line": decorator.start_point[0] + 1,
                        "at": (start[0] + 1, start[1]),
                        **({"argument": arguments[name.start_byte]} if name.start_byte in arguments else {})})
    return out


def decorated(facts: flows.Facts) -> list[dict]:
    """A function or method of the project that carries a decorator or an annotation (`decorators`), with no rule:
    its shape is the decorator's name as written, and beside it the first argument when that is a text. The symbol
    is the snapshot's function that starts where the tree's does; where the snapshot declares none, the candidate
    is of the file's code and says so."""
    out = []
    for file in facts.store.iter_paths():
        source, grammar = _file(facts, file, template=False, section="decorators")
        starts = {(d["line"], d["column"]): d for d in facts.functions.get(file, ())}
        for found in decorators(source, grammar) if grammar else ():
            declaration = starts.get(found["at"])
            candidate = {"reader": DECORATOR, "shape": found["shape"], "site": f"{file}:{found['line']}",
                         "symbol": facts.node(declaration["id"]) if declaration else f"{file}::{flows.MODULE}"}
            if declaration is None:
                candidate["gap"] = f"the snapshot declares no function at line {found['at'][0]}"
            out.append({**candidate, **({"argument": found["argument"]} if "argument" in found else {})})
    return out


def noir(report: dict, root: str) -> list[dict]:
    """The endpoints OWASP Noir reports (`noir scan -f json`, run in Daodan's container over `root`) as candidates,
    with no rule: the protocol is the shape and decides the kind (`QUERIES["noir"]`; another protocol is a shape to
    classify), method and path as Noir writes them, and the handler when Noir names it. The site is the handler's,
    else the first code path's, relative to `root`; an endpoint with neither is none. The symbol is the function
    Noir names in that file, else the file's code outside any function: Noir does not name a method's class."""
    out = []
    for endpoint in report.get("endpoints") or ():
        handler = endpoint.get("handler") or {}
        paths = (endpoint.get("details") or {}).get("code_paths") or [{}]
        where = handler if handler.get("path") else paths[0]
        if not where.get("path"):
            continue
        file = PurePosixPath(where["path"]).relative_to(root).as_posix()
        name, kind = handler.get("name") if where is handler else None, QUERIES["noir"].get(endpoint["protocol"])
        out.append({"reader": NOIR, "shape": endpoint["protocol"],
                    "site": f"{file}:{where['line']}" if where.get("line") else file,
                    "symbol": f"{file}::{name or flows.MODULE}", "method": endpoint["method"], "path": endpoint["url"],
                    **({"kind": kind} if kind else {}), **({"handler": name} if name else {})})
    return out


def candidates(links: dict, manifest: Path) -> list[dict]:
    """The candidates of every reader: the residual net on the links, the others on the snapshot they come from."""
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        facts = flows.Facts(store, db, view)
        found = passed(facts, view, _project_names(db)) + translated(facts, markup(facts, view)) + decorated(facts)
    return residual(links) + found


def shapes(found: list[dict]) -> list[dict]:
    """The candidates grouped by reader and shape, the most first: how many, and the first as the example, with
    its label when it has one."""
    rows = {}
    for candidate in found:
        row = rows.setdefault((candidate["reader"], candidate["shape"]), {
            "reader": candidate["reader"], "shape": candidate["shape"], "count": 0,
            "example": {key: candidate[key] for key in ("site", "symbol", "label") if key in candidate}})
        row["count"] += 1
    return sorted(rows.values(), key=lambda row: (-row["count"], row["reader"], row["shape"]))
