"""HTTP calls of a TypeScript or JavaScript client as connection-point sides (site, role `calls`, kind, key).

A thin adapter on tree-sitter. A site is a call the index confirms as the sink (`fetch`) or as a wrapper of
it; its key is the method and the path its arguments build, read statically: string and template literals,
`+`, constants, `let` with `+=`, branches (each one a candidate), local helpers that return a template, and
the project's declared prefix rules (a function that adds a base path). A parameter that is the whole URL
or the method makes the enclosing function a wrapper: the calls the index links to it become the sites.
Any other unknown value is a hole `{}` in the path; a path with nothing literal before its first hole is a
declared hole with its reason. Nothing is matched by name alone.

    extract(sources, rules, index) -> {"sites", "wrappers", "unconfirmed", "outside"}

`index["edges"]`: {"rel:line": [(holder, symbol), ...]}, the graph's edges at each site.
"""
from __future__ import annotations

import itertools

from tree_sitter_language_pack import get_parser

CAP = 16  # candidates kept per expression
FUNCS = {"function_declaration", "arrow_function", "function_expression", "function", "method_definition"}
INNER = {"as_expression", "non_null_expression", "satisfies_expression", "parenthesized_expression",
         "await_expression"}
GRAMMAR = {".ts": "typescript", ".tsx": "tsx", ".js": "javascript", ".jsx": "tsx", ".mjs": "javascript"}


class File:
    def __init__(self, rel: str, text: str):
        self.rel, self.src = rel, text.encode("utf-8")
        suffix = rel[rel.rfind("."):]
        self.root = get_parser(GRAMMAR.get(suffix, "tsx")).parse(self.src).root_node

    def text(self, node) -> str:
        return self.src[node.start_byte:node.end_byte].decode("utf-8", "replace")

    def site(self, node) -> str:
        return f"{self.rel}:{node.start_point[0] + 1}"


def _walk(node, skip_functions=False, top=True):
    yield node
    for child in node.children:
        if skip_functions and child.type in FUNCS and not top:
            continue
        yield from _walk(child, skip_functions, False)


def _product(groups: list[list[tuple]]) -> list[tuple]:
    out = list(dict.fromkeys(sum(combo, ()) for combo in itertools.product(*groups)))
    return out[:CAP]


def _placeholders(candidates: list[tuple]) -> list[tuple]:
    """A parameter inside a larger value is a value, not the path: a hole."""
    return [tuple(("hole", f"parameter {p[1]}") if p[0] == "param" else p for p in c) for c in candidates]


def _pure(candidate: tuple) -> bool:
    return len(candidate) == 1 and candidate[0][0] == "param"


def _params(function, file: File) -> list[str]:
    node = function.child_by_field_name("parameters") or function.child_by_field_name("parameter")
    if node is None:
        return []
    if node.type == "identifier":
        return [file.text(node)]
    names = []
    for item in node.named_children:
        pattern = item.child_by_field_name("pattern") or item.child_by_field_name("left") or item
        names.append(file.text(pattern) if pattern.type == "identifier" else "")
    return names


def _name(function, file: File):
    """The name node of a function: its own, or the variable it is assigned to."""
    own = function.child_by_field_name("name")
    if own is not None:
        return own
    parent = function.parent
    if parent is not None and parent.type == "variable_declarator":
        return parent.child_by_field_name("name")
    return None


class Reader:
    def __init__(self, files: dict[str, File], rules: dict, edges: dict):
        self.files, self.rules, self.edges = files, rules, edges
        self.consumed: set[str] = set()

    def confirmed(self, site: str, suffix: str) -> list:
        return [(holder, symbol) for holder, symbol in self.edges.get(site, ()) if symbol.endswith(suffix)]

    # Values: lists of candidates, a candidate a tuple of ("lit", text) | ("hole", reason) | ("param", name, prefix).

    def value(self, node, file: File, env: dict, depth: int = 0) -> list[tuple]:
        if node is None or depth > 8:
            return [(("hole", "too deep"),)]
        kind = node.type
        if kind in INNER and node.named_children:
            return self.value(node.named_children[0], file, env, depth + 1)
        if kind == "string":
            return [(("lit", file.text(node)[1:-1]),)]
        if kind == "template_string":
            groups, cursor = [], node.start_byte + 1
            for child in node.named_children:
                if child.type == "template_substitution":
                    groups.append([(("lit", file.src[cursor:child.start_byte].decode()),)])
                    inner = child.named_children[0] if child.named_children else None
                    groups.append(_placeholders(self.value(inner, file, env, depth + 1)))
                    cursor = child.end_byte
            groups.append([(("lit", file.src[cursor:node.end_byte - 1].decode()),)])
            return _product(groups)
        if kind == "binary_expression" and file.text(node.child_by_field_name("operator")) == "+":
            return _product([_placeholders(self.value(node.child_by_field_name(side), file, env, depth + 1))
                             for side in ("left", "right")])
        if kind == "ternary_expression":
            return (self.value(node.child_by_field_name("consequence"), file, env, depth + 1)
                    + self.value(node.child_by_field_name("alternative"), file, env, depth + 1))[:CAP]
        if kind == "identifier":
            return self.name(file.text(node), node, file, env, depth)
        if kind == "call_expression":
            return self.call(node, file, env, depth)
        return [(("hole", f"{kind} `{file.text(node)[:40]}`"),)]

    def declarations(self, name: str, node, file: File):
        """(scope function or None, parameter names, assigned values, `+=` values) of the nearest scope naming it."""
        scope = node.parent
        while scope is not None:
            if scope.type in FUNCS or scope.type == "program":
                values, appended = [], []
                for item in _walk(scope, skip_functions=True):
                    if item.type == "variable_declarator" and file.text(item.child_by_field_name("name")) == name:
                        values.append(item.child_by_field_name("value"))
                    elif item.type in ("assignment_expression", "augmented_assignment_expression") and \
                            file.text(item.child_by_field_name("left")) == name:
                        target = appended if item.type == "augmented_assignment_expression" else values
                        target.append(item.child_by_field_name("right"))
                    elif item.type == "function_declaration" and file.text(item.child_by_field_name("name")) == name:
                        values.append(item)
                params = _params(scope, file) if scope.type in FUNCS else []
                if name in params or values:
                    return scope, params, [v for v in values if v is not None], appended
            scope = scope.parent
        return None, [], [], []

    def name(self, name: str, node, file: File, env: dict, depth: int) -> list[tuple]:
        if name in env:
            return env[name]
        _scope, params, values, appended = self.declarations(name, node, file)
        if name in params:
            return [(("param", name, ""),)]
        if not values:
            return [(("hole", f"name `{name}`"),)]
        base = [c for value in values for c in self.value(value, file, env, depth + 1)][:CAP]
        grown = [c for right in appended for c in _product([_placeholders(base),
                                                           _placeholders(self.value(right, file, env, depth + 1))])]
        return list(dict.fromkeys(base + grown))[:CAP]

    def call(self, node, file: File, env: dict, depth: int) -> list[tuple]:
        callee = node.child_by_field_name("function")
        args = node.child_by_field_name("arguments")
        args = args.named_children if args is not None else []
        name = file.text(callee) if callee.type == "identifier" else None
        for rule in self.rules.get("prefix", ()):
            if name == rule["function"] and self.confirmed(file.site(callee), rule["symbol"]):
                self.consumed.add(file.site(callee))
                given = self.value(args[0], file, env, depth + 1) if args else [(("hole", "no argument"),)]
                return [_rule(c, rule["prefix"]) for c in given][:CAP]
        helper = self.helper(name, node, file) if name else None
        if helper is not None:
            params = _params(helper, file)
            bound = {p: self.value(a, file, env, depth + 1) for p, a in zip(params, args) if p}
            bound.update({p: [(("hole", f"parameter {p} not passed"),)] for p in params[len(args):] if p})
            body = helper.child_by_field_name("body")
            returns = [body] if body is not None and body.type != "statement_block" else [
                item.named_children[0] for item in _walk(body, skip_functions=True)
                if item.type == "return_statement" and item.named_children]
            out = [c for expression in returns for c in self.value(expression, file, bound, depth + 1)]
            return list(dict.fromkeys(out))[:CAP] or [(("hole", f"`{name}()` returns nothing readable"),)]
        return [(("hole", f"call `{file.text(callee)[:40]}()`"),)]

    def helper(self, name: str, node, file: File):
        _scope, params, values, _ = self.declarations(name, node, file)
        if name in params:
            return None
        for value in values:
            if value.type in FUNCS:
                return value
        return None

    def method(self, node, file: File, env: dict) -> list:
        """Method candidates: "GET", ..., "*" (unknown), ("param", name) or ("options", name)."""
        if node is None:
            return ["GET"]
        while node.type in INNER and node.named_children:
            node = node.named_children[0]
        if node.type == "identifier":
            name = file.text(node)
            if name in env:
                bound = env[name]
                return [("options", name)] if bound and _pure(bound[0]) else ["*"]
            _scope, params, values, _ = self.declarations(name, node, file)
            if name in params:
                return [("options", name)]
            return [m for value in values for m in self.method(value, file, env)] or ["*"]
        if node.type != "object":
            return ["*"]
        for item in node.named_children:
            if item.type == "pair" and file.text(item.child_by_field_name("key")).strip("'\"") == "method":
                return [_verb(c) for c in self.value(item.child_by_field_name("value"), file, env)]
            if item.type == "shorthand_property_identifier" and file.text(item) == "method":
                return [_verb(c) for c in self.name("method", item, file, env, 0)]
        return ["*"] if any(item.type == "spread_element" for item in node.named_children) else ["GET"]


def _rule(candidate: tuple, prefix: str) -> tuple:
    """A declared prefix rule: the prefix goes in front unless the path already starts with it."""
    if _pure(candidate):
        return (("param", candidate[0][1], prefix),)
    candidate = tuple(("hole", f"parameter {p[1]}") if p[0] == "param" else p for p in candidate)
    head = candidate[0][1].lstrip("/") if candidate and candidate[0][0] == "lit" else None
    bare = prefix.strip("/")
    if head is not None and (head == bare or head.startswith(bare + "/")):
        return (("lit", "/" + head),) + candidate[1:]
    rest = ((("lit", head),) + candidate[1:]) if head is not None else candidate
    return (("lit", prefix),) + rest


def _verb(candidate: tuple):
    if _pure(candidate):
        return ("param", candidate[0][1])
    return candidate[0][1].upper() if len(candidate) == 1 and candidate[0][0] == "lit" else "*"


def key(candidate: tuple, method: str) -> tuple[str | None, str | None]:
    """(key, hole reason): method and path, the query cut, holes as `{}`."""
    text = "".join(p[1] if p[0] == "lit" else "\0" for p in candidate)
    for mark in ("?", "#"):
        text = text.split(mark, 1)[0]
    if text.startswith("\0") or not text:
        reason = next((p[1] for p in candidate if p[0] != "lit"), "empty path")
        return None, f"path built at run time: {reason}"
    if "://" in text:
        return None, f"absolute URL `{text[:60]}`"
    segments = [s.replace("\0", "{}") for s in text.split("/") if s]
    return f"{method} /" + "/".join(segments), None


def extract(sources: dict[str, str], rules: dict, index: dict) -> dict:
    files = {rel: File(rel, text) for rel, text in sources.items()}
    reader = Reader(files, rules, index.get("edges", {}))
    sink = rules["sink"]
    sites, wrappers, unconfirmed = [], [], []

    def emit(site, holder, urls, methods, via, file):
        keys, holes = [], []
        verbs = [m if isinstance(m, str) else "*" for m in methods] or ["GET"]
        for candidate in urls:
            for verb in dict.fromkeys(verbs):
                found, hole = key(candidate, verb)
                keys.append(found) if found else holes.append(hole)
        keys = sorted(set(k for k in keys if k))
        sites.append({"site": site, "role": "calls", "kind": "http", "keys": keys, "holder": holder,
                      "via": via, "hole": None if keys else (holes[0] if holes else "no key")})

    def classify(site, holder, function, urls, methods, via, file):
        """A site, or a wrapper when the URL or the method is a parameter of its function."""
        pure = [c for c in urls if _pure(c)]
        if (pure or any(isinstance(m, tuple) for m in methods)) and function is not None:
            name_node = _name(function, file)
            wrappers.append({"name": file.text(name_node) if name_node is not None else "(anonymous)",
                             "node": holder, "site": site, "params": _params(function, file),
                             "urls": urls, "methods": methods, "file": file.rel, "via": via})
        else:
            emit(site, holder, _placeholders(urls), [m if isinstance(m, str) else "*" for m in methods], via, file)

    def enclosing(node):
        while node is not None and node.type not in FUNCS:
            node = node.parent
        return node

    for file in files.values():
        for node in _walk(file.root):
            if node.type != "call_expression":
                continue
            callee = node.child_by_field_name("function")
            if callee.type != "identifier" or file.text(callee) != sink["name"]:
                continue
            site = file.site(callee)
            found = reader.confirmed(site, sink["symbol"])
            if not found:
                unconfirmed.append({"site": site, "name": sink["name"], "reason": "the index names no such sink here"})
                continue
            args = node.child_by_field_name("arguments").named_children
            urls = reader.value(args[0], file, {}) if args else [(("hole", "no argument"),)]
            methods = reader.method(args[1] if len(args) > 1 else None, file, {})
            classify(site, found[0][0], enclosing(node), urls, methods, None, file)

    done, linked = 0, set()
    while done < len(wrappers):  # wrappers found while expanding are expanded in turn
        wrapper = wrappers[done]
        done += 1
        callers = 0
        for file in files.values():
            for node in _walk(file.root):
                if node.type != "call_expression":
                    continue
                callee = node.child_by_field_name("function")
                if callee.type != "identifier" or file.text(callee) != wrapper["name"]:
                    continue
                site = file.site(callee)
                links = [h for h, s in reader.edges.get(site, ()) if s == wrapper["node"]]
                if not links:
                    unconfirmed.append({"site": site, "name": wrapper["name"],
                                        "reason": "same name as a wrapper, no index link to it"})
                    continue
                callers += 1
                linked.add(site)
                args = node.child_by_field_name("arguments").named_children
                bound = {p: reader.value(a, file, {}) for p, a in zip(wrapper["params"], args) if p}
                nodes = {p: a for p, a in zip(wrapper["params"], args) if p}
                urls = []
                for candidate in wrapper["urls"]:
                    if not _pure(candidate):
                        urls.append(candidate)
                        continue
                    name, prefix = candidate[0][1], candidate[0][2]
                    given = bound.get(name, [(("hole", f"parameter {name} not passed"),)])
                    urls += [_rule(c, prefix) if prefix else c for c in given]
                methods = []
                for method in wrapper["methods"]:
                    if isinstance(method, str):
                        methods.append(method)
                    elif method[0] == "param":
                        methods += [_verb(c) for c in bound.get(method[1], [(("hole", "not passed"),)])]
                    else:
                        methods += reader.method(nodes.get(method[1]), file, {})
                classify(site, links[0], enclosing(node), urls, methods, wrapper["name"], file)
        if not callers:
            names = [p for p in wrapper["params"] if p]
            sites.append({"site": wrapper["site"], "role": "calls", "kind": "http", "keys": [],
                          "holder": wrapper["node"], "via": wrapper["via"],
                          "hole": f"parameter {', '.join(names)} of `{wrapper['name']}`: no call the index links to it"})

    unconfirmed = [u for u in unconfirmed if u["site"] not in linked]  # another wrapper of that name has it
    outside = []
    for file in files.values():
        for node in _walk(file.root):
            if node.type != "call_expression":
                continue
            callee = node.child_by_field_name("function")
            site = file.site(callee)
            for rule in rules.get("prefix", ()):
                if file.text(callee) == rule["function"] and site not in reader.consumed and \
                        reader.confirmed(site, rule["symbol"]):
                    outside.append({"site": site, "text": file.text(node)[:80]})
    for wrapper in wrappers:
        wrapper["urls"] = [list(map(list, c)) for c in wrapper["urls"]]
    return {"sites": sites, "wrappers": wrappers, "unconfirmed": unconfirmed, "outside": outside}
