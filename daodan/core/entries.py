"""Entry candidates: where a flow may start, read by the machine from what the snapshot has, without rules.

A reader is one way an entry is written (spec of 18 November 2026, section 6 point 5), one function each. A candidate
is `{reader, shape, site, symbol}`: the reader that found it, the shape it is written in, which is classified once
with one of the entry kinds or as no entry, the file and line, and the symbol the flow starts from. The model
classifies the shapes; it does not look for entries.

The residual net reads the links; the other readers read the snapshot the links come from (`candidates`), code from
its syntax tree: the grammar the snapshot read the file with, and what a framework writes is the data of
`daodan/data/entry-queries.json`, one query per grammar. `noir` reads the endpoints a ready-made tool reports, `typegen`
the file a framework's own tool generates.
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

import code_graph  # noqa: E402
import edge_view  # noqa: E402
import flows  # noqa: E402
import observed_entries  # noqa: E402
import semantic_store  # noqa: E402
from languages import _treesitter, get_adapter  # noqa: E402
from languages.sfc import mask_non_script  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

RESIDUAL, ARGUMENT, ATTRIBUTE, DECORATOR, NOIR, MANIFEST = "residuo", "argomento", "attributo", "decoratore", "noir", "manifesto"
NEXT = "next"
CALLS = ("chiama", "attiva")  # the links by which a symbol is called
QUERIES = json.loads((SCRIPT_DIR.parent / "data" / "entry-queries.json").read_text(encoding="utf-8"))
ENTRY_KINDS = tuple(QUERIES["entry_kinds"])
NO_ENTRY = "nessun ingresso"
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


def _parse(source, grammar):
    loaded = _treesitter.get_parser(grammar) if grammar else None
    return loaded[0].parse(source).root_node if loaded else None


def _matches(source: bytes, grammar: str, section: str = "queries", root=None) -> list[dict]:
    """Apply the query to the supplied file tree, or parse an isolated expression."""
    from tree_sitter import QueryCursor

    query = _query(grammar, section)
    root = _parse(source, grammar) if root is None else root
    if root is None or query is None:
        return []
    return [captures for _, captures in QueryCursor(query).matches(root)]


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


def _assignments(assigned: dict, file: str, source: bytes, root) -> list[tuple[str, tuple[int, int], object]]:
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
                    out.append((_text(source, left), _at(left), right))
        assigned[file] = sorted(out, key=lambda item: item[1])
    return assigned[file]


def _held(node, source: bytes, grammar: str) -> bool:
    """Whether an assigned value is one the object holds, not a function: the result of a call, or a text."""
    return node.child_by_field_name("arguments") is not None or \
        (grammar in QUERIES["calls"] and _literal(node, source, grammar) is not None)


def _resolved(facts, file, places):
    """Respect the exact indexed read or call, including an ambiguous or external answer that forbids guessing."""
    for at in places:
        reads = [*facts.reads.get((file, *at), ()), *facts.calls_at.get((file, *at), ())]
        if any(edge_view.uncertainty(read) for read in reads):
            return None, "unresolved"
        for read in reads:
            target = read.get("target_id")
            if target and facts.declarations.get(target, {}).get("kind") in ("function", "method"):
                return facts.node(target), (read.get("provenance") or [read["resolver"]])[-1]
            if read.get("engine_candidate") or read.get("external") or read.get("reason") == "project-value":
                return None, "unresolved"
    return None, None


def _function(facts: flows.Facts, classes: dict, anonymous: set, parsed: tuple, assigned: dict, ref: dict,
              node) -> tuple[str | None, str | None, str | None]:
    """The function an argument gives, and the gap when it is a method that does not resolve. `self.name` is the
    method of its class (`_method`); an attribute the class assigns from a call or a text is a value, none; one it
    assigns otherwise is a function given at run time, a gap. A name counts only as the snapshot resolved its read,
    a binding in scope or an import from a file of the project, at the name or at the last part of a dotted one: a
    variable that shares its name with a function is none (`len(items)`)."""
    (source, root, grammar), file = parsed, ref["file"]
    text, line, column = _text(source, node), node.start_point[0] + 1, node.start_point[1]
    receiver = node.child_by_field_name("object")
    member = node.child_by_field_name("property") or node.child_by_field_name("attribute")
    places = [member, node] if member is not None else [node] if node.named_child_count == 0 else []
    if receiver is not None and member is not None and _text(source, receiver) in RECEIVERS:
        name = _text(source, member)
        owner = _holder(classes, file, line)
        values = [value for target, at, value in _assignments(assigned, file, source, root) if owner
                  and target == text and owner["line"] <= at[0] <= (owner["end"] or owner["line"])]
        if values:
            # A type index may identify the declared method even when an instance field shadows it.
            if grammar == "python":
                # A direct assignment immediately before registration has no intervening branch or call.
                statement = node
                while statement.parent and statement.parent.type != "block":
                    statement = statement.parent
                previous = statement.prev_named_sibling
                if previous is not None and previous.type == "expression_statement" and len(previous.named_children) == 1:
                    previous = previous.named_children[0]
                if previous is not None and previous.type == "assignment":
                    value = previous.child_by_field_name("right")
                    if value is not None and value.type == "identifier" and value in values:
                        target, origin = _resolved(facts, file, [_at(value)])
                        if target:
                            return target, None, origin
            parameter = node.parent.child_by_field_name("name") if node.parent else None
            if (all(_held(value, source, grammar) for value in values)
                    and not (parameter is not None and _text(source, parameter) == "command")):
                return None, None, None
            return (facts.node(ref.get("caller")) or f"{file}::{flows.MODULE}",
                    f"handler {text} not resolved: {owner['name']} assigns {name} at run time", None)
    symbol, origin = _resolved(facts, file, map(_at, places))
    if origin:
        return symbol, None, origin
    if receiver is not None and member is not None and _text(source, receiver) in RECEIVERS:
        symbol, why = _method(facts, classes, file, line, _text(source, member))
        return (symbol, None, "classe") if symbol else (facts.node(ref.get("caller")) or f"{file}::{flows.MODULE}",
                                                         f"handler {text} not resolved: {why}", None)
    if (file, line, column) in anonymous:
        written = facts.written_function(file, line, column)
        if written["id"] in facts.native_dispatch_callers:
            return written["id"], None, "inline"
        handler = facts.handler(node, source, file)
        return handler, None, "chiamata" if handler else None
    return None, None, None


def _string(node, source: bytes, grammar: str, exact: bool = False) -> str | None:
    """The text of a string literal node, by the grammar's `strings` query: its `@text`, or, for a template, the text
    between its backticks (`@template`), with the `${...}` it holds for the caller to accept or refuse. A computed text
    and a node of a grammar the data has no query for are none; with `exact`, so is a text with an escape, which is
    not the value it is written as (a flow rule's value: `flows.py`)."""
    from tree_sitter import QueryCursor

    query = _query(grammar, "strings") if grammar in QUERIES["strings"] else None
    for _, captures in QueryCursor(query).matches(node) if query is not None else ():
        for found in captures.get("text", []):
            if found.parent == node and not (exact and found.named_children):  # an escape in the text (Python) is a child
                return _text(source, found)
        for found in captures.get("template", []):
            if found == node:
                return _text(source, found)[1:-1]
    return None


def _literal(node, source: bytes, grammar: str) -> str | None:
    """The text of a literal argument, by the grammar's `strings` query; a computed or an empty text is none."""
    text = _string(node, source, grammar)
    return text.strip() or None if text is not None else None


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
    at = tuple(ref["span"][:2])
    scope = facts.enclosing(file, at[0], column=at[1])
    for size in range(len(parts) - 1, 0, -1):
        if label is not None:
            break
        target = ".".join(parts[:size])
        placements = [(pos, value) for name, pos, value in _assignments(assigned, file, source, root)
                      if name == target and lines[0] <= pos[0] <= lines[1]]
        local, initial = [], []
        for pos, value in placements:
            assigned_in = facts.enclosing(file, pos[0], column=pos[1])
            if assigned_in == scope and pos < at:
                local.append((pos, value))
            elif assigned_in is not None and assigned_in["name"] == "__init__" and assigned_in != scope:
                initial.append((pos, value))
        last, call = local[-1] if local else ((lines[0], -1), initial[0][1] if len(initial) == len(placements) == 1 else None)
        if call is not None and call.child_by_field_name("arguments") is not None:
            label = _call_label(_arguments(call, source), source, grammar, True)
        setters = [s for s in on.get((file, tuple(parts[:size])), ())
                   if str(s["parts"][-1]) in QUERIES["calls"][grammar]["setters"]
                   and last < tuple(s["span"][:2]) < at
                   and facts.enclosing(file, s["span"][0], column=s["span"][1]) == scope]
        if setters:
            setter = max(setters, key=lambda s: s["span"][:2])
            label = _call_label(_arguments(_call(root, setter["span"]), source), source, grammar, True)
    return label


def _passed(facts, references, names, classes, anonymous, parsed):
    """A function of the project given as an argument of a call, read from the call's node in the file's tree
    (`_function`), with the label of its control (`_control_label`). Its shape is the callee as written
    (`_written`) and the argument's position, `argN` or the keyword."""
    on, assigned, out = defaultdict(list), {}, []
    for ref in references:
        if ref.get("parts"):
            on[(ref["file"], tuple(str(part) for part in ref["parts"][:-1]))].append(ref)
    source, root, grammar = parsed
    for ref in references:
        file, parts, span = ref["file"], [str(part) for part in ref.get("parts") or []], ref.get("span") or [None] * 4
        if not parts or None in span[:4]:
            continue
        arguments = _arguments(_call(root, span), source) if root else []
        found = []
        form = QUERIES["event_methods"].get(parts[-1])
        for index, (keyword, node) in enumerate(arguments):
            event_arg = keyword == "command" or (form == "signal" and index == 0) or (form == "first_literal" and index == 1)
            inline = facts.written_function(file, *_at(node)) if event_arg and (file, *_at(node)) in anonymous else None
            symbol, gap, origin = (inline["id"], None, "inline") if inline else _function(
                facts, classes, anonymous, parsed, assigned, ref, node)
            shape = f"{_written(parts, names.get(file, set()))}#{keyword or f'arg{index}'}"
            if symbol:
                event = "command" if keyword == "command" else None
                if form == "signal" and index == 0 and len(parts) > 1:
                    event = parts[-2]
                elif form == "first_literal" and index == 1:
                    argument = arguments[0][1]
                    if grammar == "python":
                        event = _literal(argument, source, grammar)
                    elif argument.type == "string" and len(argument.named_children) == 1:
                        fragment = argument.named_children[0]
                        if fragment.type == "string_fragment":
                            event = _text(source, fragment)
                found.append({**({"event": event} if event else {}), "reader": ARGUMENT, "shape": shape, "site": f"{file}:{span[0]}", "symbol": symbol,
                              **({"owner": facts.node(ref.get("caller")) or f"{file}::{flows.MODULE}"} if origin == "inline" else {}),
                              **({"gap": gap} if gap else {"handler_source": origin, "column": span[1]})})
        label = _control_label(facts, classes, parsed, ref, on, assigned) if found else None
        out += [{**candidate, "label": label} if label else candidate for candidate in found]
    return out


def _code(text: str, grammar: str | None, *, where: bool = False) -> dict[str, list]:
    """The captures of an expression written as text in the markup, read with the `code` grammar's query; with
    `where`, each is `(text, row, column)`, where it starts in the expression."""
    source, found = text.encode("utf-8"), defaultdict(list)
    for captures in _matches(source, grammar) if grammar else ():
        for name, nodes in captures.items():
            found[name] += [(_text(source, node), *node.start_point) if where else _text(source, node)
                            for node in nodes]
    return found


def _label(source: bytes, tag, element, parts: list, code: str | None, names=None) -> tuple[str | None, str | None]:
    """The ordered literal aria-labelledby references first, then the @name of its tag (`aria-label`),
    else its text, else the @hint of its tag (`title`, `placeholder`), else the @key of a translation call inside
    the element (`t('salva')`, made text by `translated`). A computed text is no label."""
    found, words, computed = defaultdict(list), [], False
    for kind, node in parts:
        if not element.start_byte <= node.start_byte < node.end_byte <= element.end_byte:
            continue
        own, text = tag.start_byte <= node.start_byte < tag.end_byte, _text(source, node)
        if kind in ("name", "hint", "labelledby") and own and text.strip():
            found[kind].append(text.strip())
        elif kind == "text" and not own:
            words += text.split()
        elif kind in ("computed", "code") and not own:
            computed = True
            found["key"] += _code(text, code)["key"] if kind == "code" else []
        elif kind == "key":
            found["key"].append(text[1:-1] if len(text) > 1 and text[0] == text[-1] and text[0] in "'\"`" else text)
    for refs in found["labelledby"] if names else ():
        resolved = [names[ref] for ref in refs.split() if names.get(ref)]
        if resolved:
            return " ".join(resolved), None
    for value in (*found["name"][:1], None if computed else " ".join(words), *found["hint"][:1]):
        if value:
            return value, None
    return (found["key"][0], found["key"][0]) if found["key"] else (None, None)


def _at(node) -> tuple[int, int]:
    """Where a node starts, as the snapshot writes it: line from 1, column in bytes."""
    return node.start_point[0] + 1, node.start_point[1]


FUNCTIONS = ("function_declaration", "function_expression", "arrow_function", "method_definition",
             "generator_function", "generator_function_declaration")  # the nodes a JSX binding is written in
JSX = ("jsx_element", "jsx_self_closing_element", "jsx_fragment")
JSX_TAGS = ("jsx_opening_element", "jsx_self_closing_element")  # the nodes that hold an element's tag name
JSX_GRAMMARS = ("tsx", "javascript")  # the grammars whose files write components as markup of their own
JSX_LANGUAGES = ("typescript", "javascript")  # the languages of the index's answers for those files


def _jsx_value(node) -> bool:
    """Whether an expression is markup: JSX itself, or written through parentheses, a type assertion, a conditional
    or `&&` and `||` (`cond && <Row />`)."""
    while node is not None:
        if node.type in JSX:
            return True
        if node.type == "ternary_expression":
            return any(_jsx_value(node.child_by_field_name(side)) for side in ("consequence", "alternative"))
        if node.type == "binary_expression":
            return any(_jsx_value(node.child_by_field_name(side)) for side in ("left", "right"))
        if node.type not in ("parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression"):
            return False
        node = node.named_children[0] if node.named_children else None
    return False


def _returns_jsx(function) -> bool:
    """Whether a function returns markup, in the body of an arrow or in a `return` that is not a nested function's:
    what makes it a component, which a prop may hold as a value (`Component={About}`) with no event in it."""
    body = function.child_by_field_name("body")
    if body is None or body.type != "statement_block":
        return _jsx_value(body)
    stack = [body]
    while stack:
        node = stack.pop()
        if node.type == "return_statement" and any(_jsx_value(child) for child in node.named_children):
            return True
        stack.extend(child for child in node.named_children if child.type not in FUNCTIONS)
    return False


def _props(function, source: bytes) -> tuple[dict[str, str], str | None]:
    """How a component function names its props: `{local name: prop}` for a first parameter that destructures them
    (`{ onSave, onX: go, onY = noop }`), else the name of a first parameter that holds them (`props`)."""
    parameters = function.child_by_field_name("parameters")
    first = next((node for node in parameters.named_children if not node.is_extra), None) if parameters is not None \
        else function.child_by_field_name("parameter")
    if first is not None and first.type in ("required_parameter", "optional_parameter"):
        first = first.child_by_field_name("pattern")
    if first is None:
        return {}, None
    if first.type == "identifier":
        return {}, _text(source, first)
    names = {}
    for node in first.named_children if first.type == "object_pattern" else ():
        if node.type == "object_assignment_pattern":
            node = node.child_by_field_name("left")
        if node.type == "shorthand_property_identifier_pattern":
            names[_text(source, node)] = _text(source, node)
        elif node.type == "pair_pattern":
            local = node.child_by_field_name("value")
            local = local.child_by_field_name("left") if local is not None and local.type == "assignment_pattern" else local
            if local is not None and local.type == "identifier":
                names[_text(source, local)] = _text(source, node.child_by_field_name("key"))
    return names, None


def _prop(node, source: bytes, name: str | None = None, member: tuple[str, str] | None = None):
    """The prop of the component a handler written at `node` is, and the function that takes it: `name`, a local name
    the function destructures, or `member`, `(props, prop)` of `props.onSave`; the nearest function that has it."""
    while node is not None:
        if node.type in FUNCTIONS:
            names, holder = _props(node, source)
            if name in names:
                return names[name], node
            if member and member[0] == holder:
                return member[1], node
        node = node.parent
    return None, None


def _inline_prop(inline, source: bytes, node):
    """The prop a function written in place calls and does nothing else: `() => onSave(1)`, `() => props.onSave()`."""
    body = inline.child_by_field_name("body")
    if body is not None and body.type == "statement_block" and len(body.named_children) == 1:
        body = body.named_children[0]
        body = body.named_children[0] if body.type == "expression_statement" and body.named_children else body
    call = body if body is not None and body.type == "call_expression" else None
    callee = call.child_by_field_name("function") if call is not None else None
    if callee is None:
        return None, None
    if callee.type == "member_expression" and callee.child_by_field_name("object").type == "identifier":
        return _prop(node, source, member=(_text(source, callee.child_by_field_name("object")),
                                           _text(source, callee.child_by_field_name("property"))))
    return _prop(node, source, name=_text(source, callee)) if callee.type == "identifier" else (None, None)


def bindings(source: bytes, grammar: str, renders=None, root=None, components=None) -> list[dict]:
    """The events bound in a file of markup, from its tree and its grammar's query (`QUERIES`), one per name an
    attribute binds (each branch of a conditional): the attribute as written (`shape`), its line, the name it binds
    (`handler`, or `called` when the syntax says the event calls it, with `at`, where the name is written, in a
    template's expression too, for the snapshot's reference there to resolve it) or where a
    function written in place as the handler starts (`inline`), and the label of its element with the key when it
    is one (`_label`). On a component's tag (a capital letter, a member, a Vue tag with `-`) the tag and where it is
    written (`tag`, `tag_at`); where the handler is a prop of the component function it is written in, that prop and
    the function (`prop`, `function_at`), and `registers` when the binding is only the prop's (`props.onSave`): a row
    of the parent's tag stands for it, as for `() => onSave()` where the function is a component (`_on_components`)."""
    matches, code = _matches(source, grammar, root=root), QUERIES["queries"][grammar].get("code")
    if renders is not None:
        for m in matches:
            for definition in m.get("render", ()):
                # Only literal markup is proven pure. Expressions inside the JSX might themselves call a writer.
                stack = [definition.child_by_field_name("body")]
                while stack:
                    item = stack.pop()
                    if item.type == "jsx_expression":
                        break
                    stack.extend(item.named_children)
                else:
                    renders.add(_at(definition))
    if components is not None and root is not None and grammar in JSX_GRAMMARS:
        stack = [root]
        while stack:
            node = stack.pop()
            if node.type in FUNCTIONS and _returns_jsx(node):
                components.add(_at(node))
            stack.extend(node.named_children)
    elements = sorted(((m["tag"][0], m["element"][0]) for m in matches if "tag" in m),
                      key=lambda pair: pair[1].end_byte - pair[1].start_byte)
    parts = sorted(((kind, node) for m in matches if not {"tag", "event"} & set(m)
                    for kind, nodes in m.items() for node in nodes), key=lambda part: part[1].start_byte)
    def scope(tag):
        # Distinct JSX functions in the same file render different control trees.
        while tag is not None and tag.type not in FUNCTIONS:
            tag = tag.parent
        return tag.start_byte if tag is not None else 0

    by_id = defaultdict(dict)
    labelled = any(kind == "labelledby" for kind, _ in parts)
    for kind, node in parts if labelled else ():
        if kind == "id":
            owner = next(((t, e) for t, e in elements if t.start_byte <= node.start_byte < t.end_byte), None)
            if owner:
                by_id[scope(owner[0])].setdefault(_text(source, node), _label(source, *owner, parts, code)[0])
    out, seen = [], set()
    for m in matches:
        events = sorted(m.get("event", []), key=lambda node: node.start_byte)
        bound = {kind: _text(source, m[kind][0]) for kind in ("handler", "called", "method") if kind in m}
        for kind in ("called", "handler", "method", "inline"):
            if kind in m:
                bound["inline" if kind == "inline" else "at"] = _at(m[kind][0])
        for node in m.get("code", [])[:1] if events and not bound else ():
            for kind, (name, row, column) in [(kind, names[0]) for kind, names in
                                              _code(_text(source, node), code, where=True).items()
                                              if kind in ("handler", "called")][:1]:
                # the name is written in the expression: where it starts in the file, as the snapshot's references say
                bound = {kind: name, "at": (node.start_point[0] + 1 + row,
                                            node.start_point[1] + column if row == 0 else column)}
        prop = function = None  # the prop a component's handler is, in the component that takes it
        if events and grammar in JSX_GRAMMARS:
            if "prop" in m and not bound:  # `props.onSave`: a binding only where `props` is the component's own
                prop, function = _prop(events[0], source, member=(_text(source, m["owner"][0]), _text(source, m["prop"][0])))
                bound = {"registers": True} if prop else {}
            elif "handler" in bound:
                prop, function = _prop(events[0], source, name=bound["handler"])
            elif "inline" in m:  # `() => onSave()`
                prop, function = _inline_prop(m["inline"][0], source, events[0])
        once = (events[0].start_byte, *sorted(bound.items())) if events else None
        if not events or not bound or once in seen:
            continue
        seen.add(once)
        at = events[0].start_byte
        tag, element = next(((t, e) for t, e in elements if t.start_byte <= at < t.end_byte), (None, None))
        label, key = _label(source, tag, element, parts, code, by_id.get(scope(tag)) if labelled else None) if element is not None else (None, None)
        tag_name = tag.child_by_field_name("name") if tag else None
        if tag_name is None and tag:
            tag_name = next((child for child in tag.named_children if child.type == "tag_name"), None)
        tag_text = _text(source, tag_name) if tag_name else ""
        component = bool(tag_text) and (tag_text[:1].isupper() or (
            grammar in JSX_GRAMMARS and tag_name.type != "identifier"
        ) or (grammar == "vue" and (tag_text == "component" or "-" in tag_text)))
        out.append({"shape": source[at:events[-1].end_byte].decode("utf-8", errors="replace"),
                    "line": events[0].start_point[0] + 1, **bound, "column": events[0].start_point[1],
                    **({"tag": tag_text, "tag_at": _at(tag_name)} if component else {}),
                    **({"prop": prop, "function_at": _at(function)} if prop else {}),
                    **({"markup": True} if "inline" in m and _returns_jsx(m["inline"][0]) else {}),
                    "label": label, "key": key})
    return out


def _handlers(facts: flows.Facts, classes: dict, values: set, file: str, found: dict) -> list[dict]:
    """Keep an inline callback's own declaration. Its calls are separate, evidenced edges of that declaration."""
    line, name = found["line"], found.get("handler") or found.get("called")
    if "inline" in found:
        written = facts.written_function(file, *found["inline"])
        if written:
            return [{"symbol": written["id"], "handler_source": "inline"}]
        return [{"symbol": f"{file}::{flows.MODULE}", "gap": "inline handler has no declaration in the snapshot"}]
    if "at" in found:
        symbol, origin = _resolved(facts, file, [found["at"]])
        if origin:
            return [{"symbol": symbol, "handler_source": origin}] if symbol else []
    if (file, *found.get("at", ())) in values:
        return []
    # A call written in a markup's expression (Vue, Svelte) names what its reference resolved to, else what the file's
    # own script defines: a name is not looked up across the project.
    template = "called" in found and "method" not in found
    handler, why = _method(facts, classes, file, line, found["method"]) if "method" in found \
        else (facts.file_function(name, file) if template
              else facts.local_function(name, file, line, column=found["column"]), "")
    if handler:
        return [{"symbol": handler, "handler_source": "classe" if "method" in found else "locale"}]
    holder = facts.enclosing(file, line, column=found["column"])
    where = facts.node(holder["id"]) if holder else f"{file}::{flows.MODULE}"
    if (file, name) in facts.outside:
        return [{"symbol": where, "gap": f"{name} is imported from {facts.outside[file, name]}, which the snapshot does "
                                         "not resolve to a file of the project"}]
    if "called" not in found:
        return [{"binding": name, "unbound": True}]
    return [{"symbol": where, "gap": f"handler {name} not resolved" + (f": {why}" if why else "")}]


def _shape(attribute: str, tag: str) -> str:
    """The shape of an event on a component the project does not hold: the attribute itself when the table knows it
    (`onClick`), else one for the component and the attribute, classified once (`<Dialog onOpenChange>`)."""
    return attribute if attribute in QUERIES["events"] else f"<{tag} {attribute}>"


def _component(facts, file: str, found: dict, grammar: str, stems: set[str]) -> tuple[str, str | None]:
    """What a component tag is: `("project", child)` when the project holds the component, `child` its symbol where
    the snapshot's read of the tag names it (JSX); else `("outside", module)`, an import from a package, a member of
    one (`motion.button`), a global or a library's factory (`styled.div`). A Vue or Svelte tag is the project's when
    its script imports it from a file of the project or a file of the snapshot bears its name. Where the index declares
    the attribute the tag is not asked (`_declared`): the engine's declaration is the source when there is one."""
    tag = found["tag"]
    if grammar in JSX_GRAMMARS:
        head = tag.partition(".")[0]
        reads = facts.reads.get((file, *found["tag_at"]), ())
        targets = [r["target_id"] for r in reads if facts.declarations.get(r.get("target_id") or "", {}).get("kind")
                   in ("function", "method", "class")]
        if targets:
            return "project", facts.node(targets[0])
        if any(r.get("reason") == "project-value" or r.get("engine_candidate") for r in reads):  # the engine placed it
            return "project", None
        if (file, head) in facts.outside:
            return "outside", facts.outside[file, head]
        return ("project", None) if head in facts.imported.get(file, ()) else ("outside", None)
    pascal = "".join(part.capitalize() for part in tag.split("-"))
    for name in (tag, pascal):
        if name in facts.imported.get(file, ()):
            return "project", None
        if (file, name) in facts.outside:
            return "outside", facts.outside[file, name]
    return ("project", None) if tag.replace("-", "").replace("_", "").lower() in stems else ("outside", None)


def _named(facts, file: str, at: tuple[int, int]) -> str | None:
    """The symbol of the function written at `at` when it has a name of its own: an anonymous one is its owner's for
    `Facts.node`, and a callback (`items.map((item) => ...)`) is not the component around it."""
    declaration = facts.written_function(file, *at)
    return facts.node(declaration["id"]) if declaration and declaration["name"] != "(anonymous)" else None


def _markup(facts, file, source, grammar, root, classes, values, render_symbols, shared):
    """Bindings from this file, and render-only definitions to exclude after all files are read. `shared` collects
    what a component's parent joins to its own handler, across files: the shapes each component binds a prop to
    (`props`), the functions that return markup (`jsx`), and the stems of the project's Vue and Svelte files."""
    out, renders, components = [], set(), set()
    for found in bindings(source, grammar, renders, root, components) if root is not None else ():
        owner = facts.enclosing(file, found["line"], column=found["column"])
        attribute = found["shape"]
        kind = _component(facts, file, found, grammar, shared["stems"]) if found.get("tag") else None
        shape = _shape(attribute, found["tag"]) if kind and kind[0] == "outside" else attribute
        event = QUERIES["events"].get(attribute, attribute)
        child = _named(facts, file, found["function_at"]) if found.get("prop") else None
        if child and (kind is None or kind[0] == "outside"):
            shared["props"][child, found["prop"]].append((shape, event))  # a component binds the prop it is given to this event
        if found.get("registers"):
            continue
        candidate = {"reader": ATTRIBUTE, "shape": shape, "site": f"{file}:{found['line']}", "event": event,
                     "column": found["column"], "owner": facts.node(owner["id"]) if owner else f"{file}::{flows.MODULE}"}
        label = {"label": found["label"], **({"key": found["key"]} if found["key"] else {})}
        for bound in _handlers(facts, classes, values, file, found):
            row = {**candidate, **bound, **label, **({"calls": child} if child and "inline" in found else {})}
            out.append({**row, "component": {
                "kind": kind[0], "child": kind[1], "tag": found["tag"], "attribute": attribute, "grammar": grammar,
                "name": found.get("handler") or found.get("called"), "markup": bool(found.get("markup"))}} if kind else row)
    render_symbols.update(filter(None, (_named(facts, file, at) for at in renders)))
    shared["jsx"].update(filter(None, (_named(facts, file, at) for at in components)))
    return out


def _component_value(row: dict, via: dict, functions: set[str]) -> bool:
    """Whether what a component tag is given is a component, not a handler: a function written in place or declared by
    the project that returns markup (`functions`), or, where the snapshot resolves no function, a name a JSX file writes
    as a component (a capital letter)."""
    if via["markup"]:
        return True
    if "gap" not in row:
        return row.get("symbol") in functions
    return via["grammar"] in JSX_GRAMMARS and str(via["name"] or "")[:1].isupper()


def _gap_row(row: dict, why: str) -> dict:
    """The row of a handler the readers cannot follow into a component: a gap at its site, which names why."""
    return {key: value for key, value in row.items() if key not in ("symbol", "handler_source", "gap")} \
        | {"symbol": row["owner"], "gap": why, "component_gap": True}


def _through(row: dict, via: dict, props: dict) -> list[dict]:
    """A handler given to a component of the project: the parent's row is each event the component binds the prop to
    (`props`), else a gap that names the component and the prop. A Vue or Svelte component's event is that gap: the
    component's `emit` or `dispatch` is not joined to the parent's handler. Where the index does not declare the
    attribute (`_declared`) this reading of the syntax is the only one: the engine's declaration is the source when
    there is one. Evaluated for it: the TypeScript checker, which the index already runs (the edge view's
    `occurrences`)."""
    tag, attribute = via["tag"], via["attribute"]
    jsx = via["grammar"] in JSX_GRAMMARS
    if shapes := props.get((via["child"], attribute), []) if jsx else []:
        return [{**row, "shape": shape, "event": event} for shape, event in dict.fromkeys(shapes)]
    if not jsx:
        why = f"{attribute} on <{tag}>, a component of the project: its handler is not joined to the event the component emits"
    elif via["child"] is None:
        why = f"{attribute} is given to <{tag}>, a component of the project that this reader does not resolve"
    else:
        why = (f"{attribute} is given to <{tag}> ({via['child']}), which binds it to no event this reader sees: "
               "passed on, stored or called from code")
    return [_gap_row(row, why)]


def _occurrences(view: dict) -> dict:
    """The index's answers at sites the snapshot lists no reference for, in the files of JSX, by file and line."""
    out = defaultdict(list)
    for edge in view["occurrences"]:
        if edge["language"] in JSX_LANGUAGES:
            out[edge["file"], edge["l0"]].append(edge)
    return out


def _declared(edges: list[dict], attribute: str, grammar: str) -> dict | None:
    """What the checker declares an attribute written on that line to be, from the index's answers there: the member
    of a type that has the attribute's name. `element`, a type of a package the grammar's data (`declared`) lists as an
    element's own attributes; `library`, a type of another package, its `shape` the declaring member; `project`, a type
    of the project, with the declaration of the member when that is a function. None where the index has no such
    answer or answers two (two tags on a line): the other readers decide then."""
    data = QUERIES["declared"][grammar]
    elements = (QUERIES["declared"][data] if isinstance(data, str) else data)["elements"]
    found = {}
    for edge in edges:
        split = code_graph.split_symbol(edge["symbol"] or "")
        items = code_graph.descriptors(split[4]) if split else []
        if len(items) > 1 and items[-1][0] == attribute and items[-2][1] == "type":
            found[split[2], items[-2][0]] = edge
    if len(found) != 1:
        return None
    [((package, declaring), edge)] = found.items()
    member = f"{declaring}#{attribute}"
    if edge["verdict"].startswith("project"):
        return {"kind": "project", "member": member, "target": edge.get("target_id")}
    if edge["verdict"] != "external":  # a dead end, a namespace: the index placed it nowhere
        return None
    if any(declaring.endswith(suffix) for suffix in elements.get(package, ())):
        return {"kind": "element", "shape": attribute}
    return {"kind": "library", "shape": f"{package} {member}"}


def _handled(rows: list[dict], declared: dict, facts) -> dict:
    """The events a function is bound to, `{symbol: [(shape, event, row index, whole)]}`: each row of an element, or of
    a component the index declares the attribute of, by the symbol of its handler and by those it calls; `whole` when
    the handler is that function or calls nothing else, so the row is no entry of its own beside the one it stands for."""
    out, calls, counted = defaultdict(list), defaultdict(set), defaultdict(int)
    for caller, targets in facts.called.items():  # by the function's id, as an inline handler is, and by its symbol
        for key in {caller, facts.node(caller)}:
            calls[key] |= {facts.node(target) for target in targets if target}
            counted[key] += len(targets)  # a call the index does not resolve counts: it is other work
    for index, row in enumerate(rows):
        via, found, symbol = row.get("component"), declared.get(index), row.get("symbol")
        if "gap" in row or row.get("unbound") or not symbol or (via is not None and (not found or found["kind"] == "project")):
            continue
        shape = row["shape"] if via is None else found["shape"]
        event = row["event"] if via is None else QUERIES["events"].get(via["attribute"], via["attribute"])
        for key in {symbol, *calls.get(symbol, ())}:  # whole: the event runs that function and nothing else
            out[key].append((shape, event, index, key == symbol or counted[symbol] == 1))
    return out


def _declaring(row: dict, via: dict, found: dict, handled: dict, facts) -> tuple[list[dict], set[int]]:
    """A handler given to an attribute the checker declares: a control like an element's or a library component's prop
    by its declaration; one a type of the project declares goes into that project's component, which the index shows
    binding it where a handler is that member or calls it (`_handled`): the parent's rows are those events, and the
    rows of the component's own that are that member or only call it are the ones they replace, where the parent's row
    has a handler; else a gap names the component and the member."""
    attribute = via["attribute"]
    event = QUERIES["events"].get(attribute, attribute)
    if found["kind"] != "project":
        return [{**row, "shape": found["shape"], "event": event}], set()
    if not found["target"]:  # a member that is no function: no event
        return [{**row, "forwarded": True}], set()
    bound = handled.get(facts.node(found["target"]), [])
    if not bound:
        return [_gap_row(row, f"{attribute} is given to <{via['tag']}>, which the index declares as {found['member']} of the "
                              "project: no reference it records binds it to an event of an element or of a library component")], set()
    return ([{**row, "shape": shape, "event": event} for shape, event in dict.fromkeys((s, e) for s, e, _, _ in bound)],
            {index for _, _, index, whole in bound if whole and not row.get("unbound")})


def _on_components(rows: list[dict], shared: dict, facts, occurrences: dict) -> list[dict]:
    """The rows of events bound on a component tag, each an entry, a question or a gap, by what the tag is. A value
    that is a component is no handler: the row is `forwarded`. Where the index declares the attribute the declaration
    decides (`_declared`, `_declaring`); else a component from outside the project is a control like an element, and
    one of the project passes the handler into its own markup (`_through`)."""
    declared = {}
    for index, row in enumerate(rows):
        via = row.get("component")
        if via and via["grammar"] in JSX_GRAMMARS:
            file, _, line = row["site"].rpartition(":")
            if found := _declared(occurrences.get((file, int(line)), ()), via["attribute"], via["grammar"]):
                declared[index] = found
    handled = _handled(rows, declared, facts) if declared else {}
    results, replaced = [], set()
    for index, row in enumerate(rows):
        via = row.get("component")
        calls = row.get("calls")  # a function written in place that only calls the prop `calls` takes
        row = {key: value for key, value in row.items() if key not in ("component", "calls")}
        if calls in shared["jsx"]:  # a component's own: the entry is the parent's tag, as for `onClick={onSave}`
            results.append([])
        elif via is None or (row.get("unbound") and index not in declared):
            results.append([row])
        elif _component_value(row, via, shared["jsx"]):
            results.append([{**row, "forwarded": True}])
        elif index in declared:
            found, taken = _declaring(row, via, declared[index], handled, facts)
            results.append(found)
            replaced |= taken
        elif via["kind"] == "outside":
            results.append([row])
        else:
            results.append(_through(row, via, shared["props"]))
    return [row for index, found in enumerate(results) if index not in replaced for row in found]


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


def decorators(source: bytes, grammar: str, root=None) -> list[dict]:
    """The decorators and annotations of the functions and methods of a file, from its tree and its grammar's query
    (`QUERIES["decorators"]`): the name as written without arguments (`shape`), the line of the decorator, where
    the function it decorates starts (`at`, line and column), and its first argument when that is a text literal."""
    matches = _matches(source, grammar, "decorators", root)
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


def _decorated(facts, file, source, grammar, root):
    """Join decorators and annotations in the syntax tree to declarations at that position."""
    out = []
    starts = {(d["line"], d["column"]): d for d in facts.functions.get(file, ())}
    for found in decorators(source, grammar, root):
        declaration = starts.get(found["at"])
        candidate = {"reader": DECORATOR, "shape": found["shape"], "site": f"{file}:{found['line']}",
                     "symbol": facts.node(declaration["id"]) if declaration else f"{file}::{flows.MODULE}"}
        if declaration is None:
            candidate["gap"] = f"the snapshot declares no function at line {found['at'][0]}"
        out.append({**candidate, **({"argument": found["argument"]} if "argument" in found else {})})
    return out


def noir(report: dict, root: str, *, gaps: list[dict] | None = None) -> list[dict]:
    """The endpoints OWASP Noir reports (`noir scan -f json`, run in Daodan's container over `root`) as candidates,
    with no rule: the protocol is the shape and decides the kind (`QUERIES["noir"]`; another protocol is a shape to
    classify) unless the endpoint's own `kind` is one Daodan knows (`QUERIES["noir_kinds"]`: a server action), which
    is then the shape and the kind, method and path as Noir writes them, and the handler when Noir names it. The site is the handler's,
    else the first code path's, relative to `root`; an endpoint with neither is none. The symbol is the function
    Noir names in that file, else the file's code outside any function: Noir does not name a method's class."""
    out = []
    for endpoint in report.get("endpoints") or ():
        handler = endpoint.get("handler") or {}
        paths = (endpoint.get("details") or {}).get("code_paths") or [{}]
        where = handler if handler.get("path") else paths[0]
        if not where.get("path"):
            continue
        path = PurePosixPath(where["path"])
        if not path.is_relative_to(root) or ".." in path.parts:
            if gaps is None:
                raise ValueError(f"Noir cites a path outside {root}: {path}")
            gaps.append({"kind": "outside_snapshot", "path": str(path), "detail": "Noir cites a file outside the scanned root"})
            continue
        file = path.relative_to(root).as_posix()
        known = endpoint.get("kind") in QUERIES["noir_kinds"]  # a kind of Noir's that Daodan knows is the shape
        shape = endpoint["kind"] if known else endpoint["protocol"]
        name = handler.get("name") if where is handler else None
        kind = QUERIES["noir_kinds"][shape] if known else QUERIES["noir"].get(shape)
        out.append({"reader": NOIR, "shape": shape,
                    "site": f"{file}:{where['line']}" if where.get("line") else file,
                    "symbol": f"{file}::{name or flows.MODULE}", "method": endpoint["method"], "path": endpoint["url"],
                    "handler": name, **({"kind": kind} if kind else {})})  # the name or None: the links' binder says the gap
    return out


def _error_line(root) -> int:
    """The line (from 1) of the first error a tree that holds one has."""
    node = root
    while not (node.is_error or node.is_missing):
        node = next(child for child in node.children if child.has_error)
    return node.start_point[0] + 1


def nitro_routes(text: str) -> tuple[list[dict], int | None, list[str]]:
    """The routes of `.nuxt/types/nitro-routes.d.ts` (`nuxt prepare`, run in Daodan's container), read from its syntax tree
    (`QUERIES["nitro_routes"]`): per route and method, `{path, method, import}` as the tool wrote them (the method `default` is
    a handler with no method in its file name), in the file's order; the line of the first error the tree holds (None when it
    parses whole), and the routes in which no import was read (`unread`: the tool named no handler file the reader knows). The
    import is assigned to the method, and the method to the route, whose type contains it, so the generics the tool wraps it in
    are no part of the reader. A tree that holds an error gives no route: a file cut short must not pass as a short list."""
    source = text.encode("utf-8")
    root = _parse(source, "typescript")
    if root is not None and root.has_error:
        return [], _error_line(root), []
    found = _matches(source, "typescript", "nitro_routes", root)
    inside = lambda inner, outer: outer.start_byte <= inner.start_byte and inner.end_byte <= outer.end_byte  # noqa: E731
    imports = [match["import"][0] for match in found if "import" in match]
    methods = [(match["method"][0], match["value"][0]) for match in found if "method" in match]
    out, unread = [], []
    for match in (m for m in found if "route" in m):
        path, before = _text(source, match["route"][0]), len(out)
        out += [{"path": path, "method": _text(source, name), "import": _text(source, imported)}
                for name, value in methods if inside(value, match["methods"][0])
                for imported in imports if inside(imported, value)]
        if len(out) == before:
            unread.append(path)
    return out, None, unread


def typegen(text: str) -> tuple[list[dict], int | None, list[dict]]:
    """The blocks of `.next/types/validator.ts` (`next typegen`, run in Daodan's container), read from its syntax tree
    (`QUERIES["typegen"]`), the line of the first error the tree holds (None when it parses whole), and the blocks it
    checks a file in that this reader does not read (`QUERIES["typegen_blocks"]`: a config type with no route). Each
    block is a checked file: the type of config the tool checks it against (`shape`), the route that type is written
    for (`path`) and the file it imports (`import`, relative to `.next/types`); an unread one gives its `import` and
    its `block`. The comment above a block is not read. A tree that holds an error gives no block: a file cut short
    must not pass as a short list."""
    source = text.encode("utf-8")
    root = _parse(source, "typescript")
    if root is not None and root.has_error:
        return [], _error_line(root), []
    matches = _matches(source, "typescript", "typegen", root)
    read = {found["import"][0].start_byte for found in matches}
    unread = [{"import": _text(source, found["import"][0]), "block": " ".join(_text(source, found["block"][0]).split())}
              for found in _matches(source, "typescript", "typegen_blocks", root) if found["import"][0].start_byte not in read]
    return ([{"shape": _text(source, found["shape"][0]), "path": _text(source, found["route"][0]),
              "import": _text(source, found["import"][0])} for found in matches], None, unread)


def _read_syntax(facts, db, view):
    """Use one tree for all readers of a grammar and release it before the next file."""
    classes, names = _classes(facts), _project_names(db)
    anonymous = {(d["file"], d["line"], d["column"]) for d in facts.declarations.values()
                 if d["kind"] in ("function", "method") and d["name"] == "(anonymous)"}
    references = defaultdict(list)
    for ref in view["references"]:
        references[ref["file"]].append(ref)
    values = {(read["file"], *read["span"][:2]) for read in view["reads"]
              if read.get("known_unrelated") and read.get("span")}
    out, attributes, renders = [], [], set()
    shared = {"props": defaultdict(list), "jsx": set(),
              "stems": {PurePosixPath(rel).stem.replace("-", "").replace("_", "").lower()
                        for rel in facts.store.iter_paths() if rel.endswith((".vue", ".svelte"))}}
    for file in facts.store.iter_paths():
        refs = references.get(file, ())
        source, grammar = _file(facts, file, template=False, section=None if refs else "decorators")
        root = _parse(source, grammar)
        if root is not None:
            if refs:
                out.extend(_passed(facts, refs, names, classes, anonymous, (source, root, grammar)))
            if grammar in QUERIES["decorators"]:
                out.extend(_decorated(facts, file, source, grammar, root))
        template, markup_grammar = _file(facts, file, template=True)
        if markup_grammar:
            tree = root if markup_grammar == grammar and template == source else _parse(template, markup_grammar)
            if tree is not None:
                attributes.extend(_markup(facts, file, template, markup_grammar, tree, classes, values, renders, shared))
    found = _on_components(attributes, shared, facts, _occurrences(view))
    return out + translated(facts, [row for row in found if row.get("symbol") not in renders])


def _syntax(manifest: Path, *, inputs=None) -> list[dict]:
    if inputs is not None:
        return _read_syntax(*inputs)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        view = edge_view.load_edge_view(store)
        return _read_syntax(flows.Facts(store, db, view), db, view)


def _cached_rows(manifest: Path, inputs=None) -> list[dict]:
    """The tree readers' candidates, persisted once (`_stored_rows`), with the rows of the framework's compiler in place of theirs
    where it read the same events (`compiled`)."""
    return compiled(_stored_rows(manifest, inputs), manifest)


def compiled(rows: list[dict], manifest: Path) -> list[dict]:
    """The rows of Angular's own compiler (`premap/angular.py`, `parseTemplate` run in Daodan's container) in place of the tree
    reader's at the same events: an attribute row at the file, line and column of an event the compiler read is dropped, its
    label (the tree reader reads the accessible name) goes to the compiler's rows, and the compiler's rows are added: they hold
    the method the handler is, the events of a template written in a `.ts` and the calls on another object (a gap with its
    cause). Astro's compiler (`premap/astro.py`) gives rows of the same shape for the events of a `.astro` template, which no tree
    reader reads. Without a pre-map record of the compiler the rows are the tree reader's, whole."""
    from premap import TEMPLATE_SOURCES
    found = [row for source in TEMPLATE_SOURCES for row in source.recorded(manifest)]
    if not found:
        return rows
    events = {(row["site"], row["column"]) for row in found}
    labels = {}
    for row in rows:
        if row["reader"] == ATTRIBUTE and (row["site"], row.get("column")) in events and (row.get("label") or row.get("label_gap")):
            labels.setdefault((row["site"], row["column"]), {name: row[name] for name in ("label", "key", "label_gap") if row.get(name)})
    merged = [row for row in rows if not (row["reader"] == ATTRIBUTE and (row["site"], row.get("column")) in events)]
    merged += [{**row, **labels.get((row["site"], row["column"]), {})} for row in found]
    return sorted(merged, key=lambda row: (row["site"], row.get("column", 0), row["reader"], row["shape"], row.get("symbol", "")))


def _stored_rows(manifest: Path, inputs=None) -> list[dict]:
    """Persist verified AST bindings once, including unbound names that a store rule may resolve later."""
    import snapshot
    manifest = Path(manifest)
    path = manifest.with_name("entry-candidates.json")
    stamp = flows._links_stamp(manifest, premap=False)
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
        languages = saved["languages"]
        if (isinstance(languages, list) and all(isinstance(lang, str) for lang in languages)
                and all(item is None or item[-1] for item in stamp)
                and saved["key"] == flows._links_key([], stamp, languages)):
            return saved["candidates"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    languages = flows._links_languages(manifest, inputs[0].store if inputs is not None else None)
    key = flows._links_key([], stamp, languages)
    found = _syntax(manifest, inputs=inputs)
    found.sort(key=lambda row: (row["site"], row.get("column", 0), row["reader"], row["shape"], row.get("symbol", "")))
    grammars = set(QUERIES["grammars"].values()) | QUERIES["queries"].keys() | QUERIES["decorators"].keys()
    if (all(item is None or item[-1] for item in stamp) and flows._links_stamp(manifest, premap=False) == stamp
            and not any(_treesitter.load_failure(g) for g in grammars)):
        snapshot._write_json_atomic(path, {"key": key, "languages": languages, "candidates": found})
    return found


def candidates(links: dict, manifest: Path) -> list[dict]:
    """The candidates of every reader; a residual symbol is never a confirmed entry by itself."""
    found = residual(links) + [row for row in _cached_rows(manifest) if not row.get("unbound")] + _declared_rows(manifest)
    return found + _observed(manifest, found)


def _observed(manifest: Path, static: list[dict]) -> list[dict]:
    """The controls the browser found that `static` lacks (`observed_entries`); the snapshot is opened only when the
    exploration ran."""
    if not Path(manifest).with_name(observed_entries.FILE).is_file():
        return []
    with open_snapshot(manifest) as store:
        return observed_entries.rows(manifest, static, set(store.iter_paths()))


def _declared_rows(manifest):
    """The declared rows as the links bind them (`binder.bind`): the pre-map's rows are on the module, with their exports."""
    import binder
    from premap.flow_entries import evidence
    rows = evidence(manifest)[0]
    if not rows:
        return rows
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        return binder.bind(rows, flows.Facts(store, db), semantic_store._Resolver(db))


def cached_syntax(manifest: Path) -> list[dict]:
    """Public candidates with verified handler, event and label; the model transport masks text before delivery."""
    fields = ("reader", "shape", "site", "symbol", "gap", "label", "event", "label_gap", "handler_source", "column",
              "kind", "method", "path", "handler", "handler_confidence", "declared_in", "forwarded", "component_gap",
              "role", "observed_calls", "requests")
    static = [row for row in _cached_rows(manifest) + _declared_rows(manifest) if not row.get("unbound")]
    return [{"status": "candidate", **{key: row[key] for key in fields if row.get(key) is not None}}
            for row in static + _observed(manifest, static)]


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


def registry_rules(found):
    kinds = QUERIES["known_shapes"]
    known = {}
    for row in found:
        if row.get("forwarded") or row.get("unbound") or row.get("component_gap"):
            continue
        reader, shape = row["reader"], row["shape"]
        kind = row.get("kind") or kinds.get(reader, {}).get(shape)
        if reader == ATTRIBUTE and shape in QUERIES["events"]:
            kind = ENTRY_KINDS[0]
        if kind:
            known[reader, shape] = kind
    return [{"reader": reader, "shape": shape, "link": "ingresso", "entry": kind, "source": "registro"}
            for (reader, shape), kind in sorted(known.items()) if kind]


def shape_questions(found, rules=()):
    """Only undecided shapes get a number; numbering stays stable as answers are recorded for this snapshot."""
    rows = [row for row in found if not row.get("forwarded") and not row.get("unbound") and not row.get("component_gap")
            and row["reader"] != RESIDUAL]
    known = {(r.get("reader"), r.get("shape")) for r in [*rules, *registry_rules(rows)]}
    return [{"row": index, **shape} for index, shape in enumerate(shapes(rows), 1)
            if (shape["reader"], shape["shape"]) not in known]


def shape_rules(questions, answers):
    """Convert a closed row-to-kind answer into reusable decisions about code shapes."""
    if not isinstance(answers, dict):
        raise ValueError("classifications must be a row-to-entry-kind object")
    numbered = {str(question["row"]): question for question in questions}
    rules = []
    for number, kind in answers.items():
        if str(number) not in numbered or kind not in (*ENTRY_KINDS, NO_ENTRY):
            raise ValueError(f"invalid shape row or entry kind: {number!r}, {kind!r}")
        shape = numbered[str(number)]
        rules.append({"reader": shape["reader"], "shape": shape["shape"], "link": "ingresso",
                      "entry": kind, "source": "modello"})
    return rules
