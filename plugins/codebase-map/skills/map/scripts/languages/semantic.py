"""Conservative syntax evidence from trees already parsed by language adapters.

This module records binding sites and reference positions, not inferred types.
Unknown lexical behavior blocks resolution rather than guessing an outer name.
"""

from __future__ import annotations

import ast


def _payload(backend):
    return {"version": 1, "backend": backend, "status": "ast", "notes": [],
            "scopes": [{"id": "module", "parent": None, "kind": "module"}],
            "declarations": [], "imports": [], "exports": [], "references": []}


class _Evidence:
    def __init__(self, backend):
        self.data = _payload(backend)
        self.scope = "module"
        self.caller = None
        self.scope_by_id = {"module": self.data["scopes"][0]}
        self.used_ids = set()
        self.declaration_by_id = {}

    def identity(self, kind, span):
        base = f"{kind}@{span[0]}:{span[1]}"
        result = base
        index = 2
        while result in self.used_ids:
            result = f"{base}#{index}"
            index += 1
        self.used_ids.add(result)
        return result

    def note(self, message):
        if message not in self.data["notes"]:
            self.data["notes"].append(message)

    def block(self, reason):
        self.scope_by_id[self.scope].update(unresolved=True, reason=reason)
        self.note(reason)

    def declaration(self, name, kind, span, scope=None, extra=None):
        owner_scope = scope or self.scope
        declaration = {"id": self.identity(kind, span), "name": name, "kind": kind,
                       "scope": owner_scope, "span": span,
                       "qualified_name": self.qualified(name, owner_scope)}
        if extra:
            declaration.update(extra)
        self.data["declarations"].append(declaration)
        self.declaration_by_id[declaration["id"]] = declaration
        return declaration["id"]

    def qualified(self, name, scope):
        while scope != "module":
            item = self.scope_by_id[scope]
            identity = item.get("caller") or item.get("declaration")
            if identity is not None:
                return self.declaration_by_id[identity]["qualified_name"] + "." + name
            scope = item["parent"]
        return name

    def new_scope(self, kind, span, parent=None, caller=None):
        identity = self.identity(f"scope-{kind}", span)
        scope = {"id": identity, "parent": self.scope if parent is None else parent, "kind": kind}
        if caller is not None:
            scope["caller"] = caller
        self.data["scopes"].append(scope)
        self.scope_by_id[identity] = scope
        return identity

    def reference(self, parts, kind, span, reason=None):
        ref = {"scope": self.scope, "parts": parts, "kind": kind,
               "span": span, "caller": self.caller}
        if reason:
            ref["reason"] = reason
        self.data["references"].append(ref)

    def finish(self):
        for key in ("declarations", "imports", "references"):
            self.data[key].sort(key=lambda item: (item["span"], item.get("kind", "")))
        return self.data


def _py_span(node):
    return [node.lineno, node.col_offset, node.end_lineno, node.end_col_offset]


def _py_parts(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        prefix = _py_parts(node.value)
        return prefix + [node.attr] if prefix else []
    return []


def _py_base_names(bases):
    """Base classes as written, dotted. Anything else is not a name to follow.

    A subscript (`Base[T]`), a call (`factory()`), a star (`*mixins`) or any other
    expression is skipped rather than guessed: an MRO walk follows only bases whose
    name it can look up lexically, and reports nothing when it cannot.
    """
    named = []
    for base in bases:
        parts = _py_parts(base)
        if parts:
            named.append(".".join(parts))
    return named


class _PythonEvidence(ast.NodeVisitor, _Evidence):
    def __init__(self):
        _Evidence.__init__(self, "stdlib-ast")
        self.explicit_exports = None
        self.nonlocal_bindings = []
        self.namespace_writes = []

    def lexical_parent(self):
        parent = self.scope
        while self.scope_by_id[parent]["kind"] == "class":
            if self.scope_by_id[parent].get("generic"):
                break
            parent = self.scope_by_id[parent]["parent"]
        return parent

    def in_scope(self, scope, caller, nodes):
        previous = self.scope, self.caller
        self.scope, self.caller = scope, caller
        for node in nodes:
            if node is not None:
                self.visit(node)
        self.scope, self.caller = previous

    def visit_FunctionDef(self, node):
        self.function(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def header(self, node, values):
        previous = self.scope
        if getattr(node, "type_params", None):
            self.scope = self.new_scope("parameters", _py_span(node))
            self.block("generic type parameter header scope is unresolved")
        for value in values:
            if value is not None:
                self.visit(value)
        self.scope = previous

    def function(self, node):
        positional = [*node.args.posonlyargs, *node.args.args]
        identity = self.declaration(node.name, "function", _py_span(node), extra={
            "decorated": bool(node.decorator_list),
            "receiver": positional[0].arg if positional and not node.decorator_list else None,
        })
        # Header expressions do not belong to the callable body. Unsupported
        # generic annotation scopes must not fall through to outer names.
        parameters = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        parameters += [arg for arg in (node.args.vararg, node.args.kwarg) if arg is not None]
        self.header(node, [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults,
                           node.returns, *[arg.annotation for arg in parameters]])
        scope = self.new_scope("function", _py_span(node), self.lexical_parent(), identity)
        if getattr(node, "type_params", None):
            self.scope_by_id[scope].update(unresolved=True, reason="generic function type parameter scope is unresolved")
            self.note("generic function type parameter scope is unresolved")
        for arg in parameters:
            self.declaration(arg.arg, "parameter", _py_span(arg), scope)
        self.in_scope(scope, identity, node.body)

    def visit_Lambda(self, node):
        identity = self.declaration("(lambda)", "function", _py_span(node))
        for value in [*node.args.defaults, *node.args.kw_defaults]:
            if value is not None:
                self.visit(value)
        scope = self.new_scope("function", _py_span(node), self.lexical_parent(), identity)
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                    *[a for a in (node.args.vararg, node.args.kwarg) if a is not None]]:
            self.declaration(arg.arg, "parameter", _py_span(arg), scope)
        self.in_scope(scope, identity, [node.body])

    def visit_ClassDef(self, node):
        identity = self.declaration(node.name, "class", _py_span(node),
                                    extra={"bases": _py_base_names(node.bases),
                                           "bases_complete": all(_py_parts(base) for base in node.bases),
                                           "dynamic_class": bool(node.decorator_list or node.keywords),
                                           "instance_writes": []})
        self.header(node, [*node.decorator_list, *node.bases, *[k.value for k in node.keywords]])
        scope = self.new_scope("class", _py_span(node), self.lexical_parent())
        self.scope_by_id[scope]["declaration"] = identity
        # The body scope is what makes an inherited-method lookup possible at all:
        # a method's own function scope skips the class scope, because Python's
        # lexical scoping does, so the class is reachable only from its declaration.
        self.declaration_by_id[identity]["body"] = scope
        if getattr(node, "type_params", None):
            self.scope_by_id[scope]["generic"] = True
        previous = self.scope
        self.scope = scope
        self.block("class body namespace order is unresolved")
        self.scope = previous
        self.in_scope(scope, self.caller, node.body)

    def visit_Import(self, node):
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            entry = {"scope": self.scope, "local": local, "module": alias.name,
                     "imported": "*", "mode": "namespace", "span": _py_span(alias)}
            if "." in alias.name and not alias.asname:
                entry.update(unresolved=True, reason="unaliased dotted namespace import")
                self.declaration(local, "unknown", _py_span(alias))
                self.note(entry["reason"])
            self.data["imports"].append(entry)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == "*":
                self.block("wildcard import introduces unknown bindings")
                continue
            self.data["imports"].append({"scope": self.scope, "local": alias.asname or alias.name,
                                         "module": "." * node.level + (node.module or ""),
                                         "imported": alias.name, "mode": "named", "span": _py_span(alias)})

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.reference([node.id], "read", _py_span(node))
        else:
            self.declaration(node.id, "binding", _py_span(node))

    def visit_Attribute(self, node):
        parts = _py_parts(node)
        if isinstance(node.ctx, ast.Load) and parts:
            self.reference(parts, "read", _py_span(node))
        else:
            if not isinstance(node.ctx, ast.Load) and parts:
                self.namespace_writes.append((parts[0], self.scope, _py_span(node)))
                self.note("attribute mutation invalidates a namespace binding")
                if len(parts) == 2:
                    self.instance_write(parts[0], parts[1])
            self.visit(node.value)

    def instance_write(self, receiver, name):
        method = self.declaration_by_id.get(self.caller)
        if method is None or method.get("receiver") != receiver:
            return
        body = self.scope_by_id[method["scope"]]
        if body["kind"] != "class":
            return
        owner = self.declaration_by_id[body["declaration"]]
        if name is None:
            owner["instance_writes_unknown"] = True
        elif name not in owner["instance_writes"]:
            owner["instance_writes"].append(name)

    def conditional_namespace(self, node):
        # A sole declaration under `if False` is not an unconditional member.
        # Keep its syntax evidence, but do not certify this class's member lookup.
        if self.scope_by_id[self.scope]["kind"] == "class":
            self.block("conditional class namespace is unresolved")
        self.generic_visit(node)

    visit_If = conditional_namespace
    visit_Try = conditional_namespace
    visit_TryStar = conditional_namespace
    visit_For = conditional_namespace
    visit_AsyncFor = conditional_namespace
    visit_While = conditional_namespace
    visit_With = conditional_namespace
    visit_AsyncWith = conditional_namespace
    visit_Match = conditional_namespace

    def visit_Call(self, node):
        parts = _py_parts(node.func)
        if parts in (["setattr"], ["delattr"]) and len(node.args) >= 2 and isinstance(node.args[0], ast.Name):
            attribute = node.args[1]
            name = attribute.value if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str) else None
            self.instance_write(node.args[0].id, name)
        if parts == ["exec"]:
            scope = self.scope
            while scope is not None:
                self.scope_by_id[scope].update(unresolved=True, reason="exec may introduce or mutate lexical bindings")
                scope = self.scope_by_id[scope]["parent"]
            self.note("exec may introduce or mutate lexical bindings")
        if parts:
            self.reference(parts, "call", _py_span(node.func))
        else:
            # A member of a computed receiver keeps its name, as the tree-sitter
            # adapters record it, so an engine can still be asked about it.
            member = node.func.attr if isinstance(node.func, ast.Attribute) else None
            self.reference(["(expr)", member] if member else [], "call", _py_span(node.func), "dynamic-callee")
            self.visit(node.func)
        for value in [*node.args, *[keyword.value for keyword in node.keywords]]:
            self.visit(value)

    def visit_Global(self, node):
        for name in node.names:
            self.declaration(name, "unknown", _py_span(node))
            self.declaration(name, "unknown", _py_span(node), "module")
        self.note("global/nonlocal binding is unresolved")

    def visit_Nonlocal(self, node):
        for name in node.names:
            self.declaration(name, "unknown", _py_span(node))
            self.nonlocal_bindings.append((name, self.scope, _py_span(node)))
        self.note("global/nonlocal binding is unresolved")

    def visit_ExceptHandler(self, node):
        if node.name:
            self.declaration(node.name, "binding", _py_span(node))
        self.generic_visit(node)

    def visit_MatchAs(self, node):
        if node.name:
            self.declaration(node.name, "binding", _py_span(node))
        self.generic_visit(node)

    visit_MatchStar = visit_MatchAs

    def visit_MatchMapping(self, node):
        if node.rest:
            self.declaration(node.rest, "binding", _py_span(node))
        self.generic_visit(node)

    def visit_NamedExpr(self, node):
        if self.scope_by_id[self.scope]["kind"] == "comprehension":
            self.block("comprehension assignment expression scope is unresolved")
            parent = self.scope_by_id[self.scope]["parent"]
            while self.scope_by_id[parent]["kind"] == "comprehension":
                parent = self.scope_by_id[parent]["parent"]
            self.declaration(node.target.id, "unknown", _py_span(node.target), parent)
            self.visit(node.value)
        else:
            self.generic_visit(node)

    def comprehension(self, node):
        # The first iterable is evaluated outside the implicit function scope.
        self.visit(node.generators[0].iter)
        scope = self.new_scope("comprehension", _py_span(node), self.lexical_parent())
        previous = self.scope
        self.scope = scope
        for index, generator in enumerate(node.generators):
            if index:
                self.visit(generator.iter)
            self.visit(generator.target)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self.scope = previous

    visit_ListComp = comprehension
    visit_SetComp = comprehension
    visit_DictComp = comprehension
    visit_GeneratorExp = comprehension

    def visit_Assign(self, node):
        if self.scope == "module" and any(isinstance(n, ast.Name) and n.id == "__all__" for n in node.targets):
            try:
                names = ast.literal_eval(node.value)
                self.explicit_exports = names if isinstance(names, (list, tuple)) and all(isinstance(n, str) for n in names) else []
            except (ValueError, TypeError):
                self.explicit_exports = []
            if not self.explicit_exports:
                self.note("dynamic or empty __all__ has no inferred exports")
        self.generic_visit(node)


def python_semantics(tree):
    evidence = _PythonEvidence()
    evidence.visit(tree)
    for name, scope, span in evidence.nonlocal_bindings:
        parent = evidence.scope_by_id[scope]["parent"]
        while parent and parent != "module":
            if any(d["scope"] == parent and d["name"] == name for d in evidence.data["declarations"]) or any(
                    i["scope"] == parent and i["local"] == name for i in evidence.data["imports"]):
                evidence.declaration(name, "unknown", span, parent)
                break
            parent = evidence.scope_by_id[parent]["parent"]
    for name, scope, span in evidence.namespace_writes:
        parent = scope
        while parent is not None:
            if any(d["scope"] == parent and d["name"] == name for d in evidence.data["declarations"]) or any(
                    i["scope"] == parent and i["local"] == name for i in evidence.data["imports"]):
                evidence.declaration(name, "unknown", span, parent)
                break
            parent = evidence.scope_by_id[parent]["parent"]
    names = evidence.explicit_exports
    if names is None:
        names = [d["name"] for d in evidence.data["declarations"] if d["scope"] == "module"]
        names += [i["local"] for i in evidence.data["imports"] if i["scope"] == "module"]
        names = [name for name in names if not name.startswith("_")]
    evidence.data["exports"] = [{"exported": name, "local": name} for name in dict.fromkeys(names)]
    return evidence.finish()


def javascript_semantics(root, src, language):
    return _JavaScriptEvidence(src, language).extract(root)


class _JavaScriptEvidence(_Evidence):
    def __init__(self, src, language):
        super().__init__("tree-sitter")
        self.src = src
        self.language = language
        self.writes = []
        self.tauri_invoke_locals = set()
        self.tauri_namespaces = set()
        self.tauri_commands_bound = set()
        # Overload signatures by (scope, name), waiting for the declaration that implements them.
        self.signatures: dict[tuple[str, str], list] = {}

    def extract(self, root):
        self.scope_by_id["module"]["strict"] = any(n.type in ("import_statement", "export_statement") for n in root.named_children)
        self.walk(root)
        # Assignments update an existing lexical owner rather than creating a
        # new block-local declaration. Inspect all binding sites after walking
        # so later var/let declarations and hoisting cannot leak outer imports.
        write_ids = {d["id"] for d in self.writes}
        bindings = {(d["scope"], d["name"]) for d in self.data["declarations"]
                    if d["id"] not in write_ids and d.get("lexical") is not False}
        bindings.update((i["scope"], i["local"]) for i in self.data["imports"])
        for declaration in self.writes:
            scope = declaration["scope"]
            while (scope, declaration["name"]) not in bindings and scope != "module":
                scope = self.scope_by_id[scope]["parent"]
            declaration["scope"] = scope
            declaration["qualified_name"] = self.qualified(declaration["name"], scope)
        return self.finish()

    def text(self, node):
        return self.src[node.start_byte:node.end_byte].decode("utf-8") if node is not None else ""

    @staticmethod
    def span(node):
        return [node.start_point[0] + 1, node.start_point[1], node.end_point[0] + 1, node.end_point[1]]

    def parts(self, node):
        if node is None:
            return []
        if node.type in ("identifier", "shorthand_property_identifier"):
            return [self.text(node)]
        if node.type == "member_expression":
            obj = node.child_by_field_name("object")
            prop = node.child_by_field_name("property")
            prefix = self.parts(obj)
            if prefix and prop is not None and prop.type in ("property_identifier", "identifier"):
                return prefix + [self.text(prop)]
        return []

    def function_parent(self):
        current = self.scope
        while self.scope_by_id[current]["kind"] not in ("function", "module"):
            current = self.scope_by_id[current]["parent"]
        return current

    def binding(self, node, kind, scope=None):
        if node is None:
            return
        t = node.type
        if t in ("identifier", "shorthand_property_identifier_pattern"):
            self.declaration(self.text(node), kind, self.span(node), scope)
        elif t in ("object_pattern", "array_pattern", "formal_parameters", "rest_pattern"):
            for child in node.named_children:
                self.binding(child, kind, scope)
        elif t in ("assignment_pattern", "object_assignment_pattern"):
            self.binding(node.child_by_field_name("left"), kind, scope)
            self.walk(node.child_by_field_name("right"))
        elif t == "pair_pattern":
            key = node.child_by_field_name("key")
            if key is not None and key.type == "computed_property_name":
                self.walk(key)
            self.binding(node.child_by_field_name("value"), kind, scope)
        elif t in ("required_parameter", "optional_parameter"):
            pattern = node.child_by_field_name("pattern") or node.child_by_field_name("name")
            self.binding(pattern, kind, scope)
            self.walk(node.child_by_field_name("value"))
        elif t in ("member_expression", "subscript_expression"):
            # An assignment target such as getConfig().x or counts[key(row)] binds no name;
            # its object and index are evaluated.
            self.walk(node.child_by_field_name("object"))
            self.walk(node.child_by_field_name("index"))
        elif t not in ("type_annotation", "comment"):
            self.block(f"unsupported binding pattern: {t}")

    def imported(self, node):
        source = node.child_by_field_name("source")
        if source is None:
            self.block("unsupported import binding")
            return
        module = self.text(source)[1:-1]
        statement_type = any(c.type == "type" for c in node.children)
        clause = next((c for c in node.named_children if c.type == "import_clause"), None)
        if clause is None:
            return
        for child in clause.named_children:
            if child.type == "identifier":
                self.import_entry(child, module, "default", "default", statement_type)
            elif child.type == "namespace_import":
                name = next((c for c in child.named_children if c.type == "identifier"), None)
                if name is not None:
                    self.import_entry(name, module, "*", "namespace", statement_type)
            elif child.type == "named_imports":
                for spec in child.named_children:
                    if spec.type != "import_specifier":
                        continue
                    original = spec.child_by_field_name("name")
                    local = spec.child_by_field_name("alias") or original
                    if original is not None and local is not None:
                        type_only = statement_type or any(c.type == "type" for c in spec.children)
                        self.import_entry(local, module, self.text(original).strip("'\""), "named", type_only)

    def import_entry(self, local, module, imported, mode, type_only=False):
        local_name = self.text(local)
        entry = {"scope": self.scope, "local": local_name, "module": module,
                 "imported": imported, "mode": mode, "span": self.span(local)}
        if type_only:
            entry["type_only"] = True
        elif module in ("@tauri-apps/api/core", "@tauri-apps/api/tauri", "@tauri-apps/api"):
            if mode == "named" and imported == "invoke":
                self.tauri_invoke_locals.add(local_name)
            elif mode == "namespace":
                self.tauri_namespaces.add(local_name)
        self.data["imports"].append(entry)

    def write_binding(self, node):
        start = len(self.data["declarations"])
        self.binding(node, "binding")
        self.writes.extend(self.data["declarations"][start:])

    def export(self, node):
        source = node.child_by_field_name("source")
        module = self.text(source)[1:-1] if source is not None else None
        type_only = any(c.type == "type" for c in node.children)
        clause = next((c for c in node.named_children if c.type == "export_clause"), None)
        if clause is not None:
            for spec in clause.named_children:
                if spec.type != "export_specifier":
                    continue
                name = spec.child_by_field_name("name")
                alias = spec.child_by_field_name("alias") or name
                entry = {"exported": self.text(alias).strip("'\""), "local": self.text(name).strip("'\"")}
                if module is not None:
                    entry["module"] = module
                if type_only or any(c.type == "type" for c in spec.children):
                    entry["type_only"] = True
                self.data["exports"].append(entry)
            return
        declaration = node.child_by_field_name("declaration") or node.child_by_field_name("value")
        if any(c.type == "default" for c in node.children):
            name = declaration if declaration is not None and declaration.type == "identifier" else (
                declaration.child_by_field_name("name") if declaration is not None else None)
            if name is not None:
                self.data["exports"].append({"exported": "default", "local": self.text(name)})
            else:
                self.note("anonymous default export is unresolved")
        elif declaration is not None:
            name = declaration.child_by_field_name("name")
            if name is not None:
                self.data["exports"].append({"exported": self.text(name), "local": self.text(name)})
            elif declaration.type in ("lexical_declaration", "variable_declaration"):
                for item in declaration.named_children:
                    n = item.child_by_field_name("name")
                    if n is not None and n.type == "identifier":
                        self.data["exports"].append({"exported": self.text(n), "local": self.text(n)})
        else:
            self.note("wildcard/namespace export is unresolved")
        self.walk(declaration)

    def contracts(self, node):
        """Declare the callable members of an interface or a type alias, which an engine can answer with.

        A method signature, a property typed as a function or as an object with call
        signatures, and a call or construct signature are contracts: the call goes
        through them, as a Python call goes through a Protocol method. A property's
        own call signatures name the property. Any other property holds a value and
        is declared as a `property`, which an edge never arrives at. All are named
        after the owning type and none is a lexical binding.
        """
        owner = self.text(node.child_by_field_name("name")) or "(type)"
        stack = [node.child_by_field_name("body") or node.child_by_field_name("value")]
        owned: set[int] = set()
        while stack:
            item = stack.pop()
            if item is None:
                continue
            name = item.child_by_field_name("name")
            named = name is not None and name.type in ("property_identifier", "private_property_identifier")
            if item.type == "method_signature" and named:
                self.contract(owner, name, item)
            elif item.type == "property_signature" and named:
                kind, signatures = self.callable_type(item)
                if kind is None:
                    self.declaration(self.text(name), "property", self.span(name), extra={
                        "lexical": False, "qualified_name": f"{owner}.{self.text(name)}"})
                else:
                    owned.update(signature.id for signature in signatures)
                    self.contract(owner, name, item, [self.span(signature) for signature in signatures])
            elif item.type in ("call_signature", "construct_signature") and item.id not in owned:
                # A signature has no name: an engine answers at its first character.
                self.declaration(owner, "method", self.span(item), extra={
                    "name_span": self.span(item), "contract": True, "lexical": False,
                    "qualified_name": f"{owner}.({'new' if item.type == 'construct_signature' else 'call'})"})
            stack.extend(reversed(item.named_children))

    def contract(self, owner, name, item, signature_spans=None):
        member = self.text(name)
        extra = {"name_span": self.span(name), "contract": True, "lexical": False,
                 "qualified_name": f"{owner}.{member}"}
        if signature_spans:
            extra["signature_spans"] = signature_spans
        self.declaration(member, "method", self.span(item), extra=extra)

    @staticmethod
    def callable_type(signature):
        """`("function", [])`, `("signatures", [call signatures])` or `(None, [])` for a property's type."""
        annotation = next((child for child in signature.named_children if child.type == "type_annotation"), None)
        for child in annotation.named_children if annotation is not None else ():
            if child.type in ("function_type", "constructor_type"):
                return "function", []
            if child.type == "object_type":
                signatures = [member for member in child.named_children
                              if member.type in ("call_signature", "construct_signature")]
                if signatures:
                    return "signatures", signatures
        return None, []

    def function(self, node, assigned=None, binding_scope=None, assigned_node=None):
        name = node.child_by_field_name("name")
        defining_scope = self.scope
        if name is not None and name.type == "computed_property_name":
            if self.scope_by_id[self.scope]["kind"] == "class":
                self.scope = self.scope_by_id[self.scope]["parent"]
            self.walk(name)
            self.scope = defining_scope
        for child in node.named_children:
            if child.type == "decorator":
                self.walk(child)
        # Method property names are not lexical bindings in the surrounding
        # scope. Their IDs still own calls made by the method body.
        kind = "method" if node.type == "method_definition" else "function"
        # Where an engine says this function is declared: the bound variable, else its own name.
        named = assigned_node if assigned is not None else name
        extra = {"name_span": self.span(named)} if named is not None and named.type in (
            "identifier", "property_identifier", "private_property_identifier") else None
        overloads = self.signatures.pop((binding_scope or self.scope, self.text(named)), None) if extra else None
        if extra and kind == "method" and self.text(named) == "constructor":
            # `new C()` is answered at the class and at its constructor: both name the class.
            owner = self.scope_by_id[self.scope].get("declaration")
            if owner is not None:
                extra["constructs"] = owner
        if overloads:
            # An engine may answer at an overload signature; the runtime target is this body.
            extra["signature_spans"] = overloads
        identity = self.declaration(assigned or self.text(name) or "(anonymous)", kind, self.span(node), binding_scope,
                                    extra)
        if kind == "method" or (assigned is None and node.type in (
                "function_expression", "function", "generator_function", "arrow_function")):
            self.data["declarations"][-1]["lexical"] = False
        if node.type in ("function_declaration", "generator_function_declaration") and self.scope_by_id[self.scope]["kind"] == "block":
            ancestor = self.scope
            strict = False
            while ancestor is not None:
                strict = strict or self.scope_by_id[ancestor].get("strict", False)
                ancestor = self.scope_by_id[ancestor]["parent"]
            if not strict:
                self.declaration(self.text(name), "unknown", self.span(node), self.function_parent())
                self.note("legacy block function hoisting is unresolved")
        parameters = node.child_by_field_name("parameters") or node.child_by_field_name("parameter")
        stack = [parameters] if parameters is not None else []
        parameter_expressions = False
        while stack:
            item = stack.pop()
            if item.type in ("assignment_pattern", "object_assignment_pattern", "computed_property_name") or (
                    item.type in ("required_parameter", "optional_parameter") and item.child_by_field_name("value") is not None):
                parameter_expressions = True
            stack.extend(item.named_children)
        parameter_scope = self.new_scope("parameters", self.span(node), caller=identity) if parameter_expressions else None
        scope = self.new_scope("function", self.span(node), parent=parameter_scope, caller=identity)
        previous = self.scope, self.caller
        self.scope, self.caller = parameter_scope or scope, identity
        if node.child_by_field_name("type_parameters") is not None:
            self.block("generic function type parameter scope is unresolved")
        if name is not None and node.type in ("function_expression", "generator_function", "function"):
            self.declaration(self.text(name), "function-name", self.span(name))
        self.binding(parameters, "parameter")
        self.scope = scope
        body = node.child_by_field_name("body")
        if body is not None and body.type == "statement_block":
            for statement in body.named_children:
                if statement.type == "comment":
                    continue
                if statement.type != "expression_statement" or not statement.named_children or statement.named_children[0].type != "string":
                    break
                if self.text(statement.named_children[0]) in ('"use strict"', "'use strict'"):
                    self.scope_by_id[scope]["strict"] = True
        self.walk(node.child_by_field_name("body"), create_block=False)
        self.scope, self.caller = previous

    def walk(self, node, create_block=True):
        if node is None:
            return
        t = node.type
        if t in ("interface_declaration", "type_alias_declaration"):
            self.contracts(node)
            return
        if t in ("comment", "string", "regex", "string_fragment", "escape_sequence", "type_annotation",
                 "type_arguments", "type_parameters"):
            return
        if t == "jsx_closing_element":
            return
        if t in ("jsx_opening_element", "jsx_self_closing_element"):
            name = node.child_by_field_name("name")
            if name is not None and name.type != "jsx_namespace_name":
                parts = self.parts(name)
                if parts and (len(parts) > 1 or (parts[0][0].isupper() and "-" not in parts[0])):
                    self.reference(parts, "read", self.span(name))
            for child in node.named_children:
                if child != name:
                    self.walk(child)
            return
        if t == "jsx_attribute":
            for child in node.named_children:
                if child.type == "jsx_expression":
                    self.walk(child)
            return
        if t == "import_statement":
            self.imported(node)
            return
        if t == "export_statement":
            self.export(node)
            return
        if t in ("function_declaration", "generator_function_declaration", "function_expression", "function",
                 "generator_function", "arrow_function", "method_definition"):
            self.function(node)
            return
        if t == "method_signature":
            name = node.child_by_field_name("name")
            if name is not None:
                self.signatures.setdefault((self.scope, self.text(name)), []).append(self.span(name))
            return
        if t == "function_signature":
            name = node.child_by_field_name("name")
            if name is not None:
                self.signatures.setdefault((self.scope, self.text(name)), []).append(self.span(name))
                self.declaration(self.text(name), "unknown", self.span(node))
                self.note("overload/ambient function signature has no unique runtime target")
            return
        if t == "enum_declaration":
            name = node.child_by_field_name("name")
            if name is not None:
                self.declaration(self.text(name), "binding", self.span(name))
            previous = self.scope
            self.scope = self.new_scope("block", self.span(node))
            self.block("enum member initializer scope is unresolved")
            self.walk(node.child_by_field_name("body"))
            self.scope = previous
            return
        if t in ("class_declaration", "class", "abstract_class_declaration"):
            name = node.child_by_field_name("name")
            if name is not None:
                identity = self.declaration(self.text(name), "class", self.span(node),
                                            extra={"name_span": self.span(name)})
                if t == "class":
                    self.data["declarations"][-1]["lexical"] = False
            else:
                identity = None
            body = node.child_by_field_name("body")
            for child in node.named_children:
                if child != name and child != body:
                    self.walk(child)
            scope = self.new_scope("class", self.span(node))
            self.scope_by_id[scope]["strict"] = True
            if identity is not None:
                self.scope_by_id[scope]["declaration"] = identity
            previous = self.scope
            self.scope = scope
            if t == "class" and name is not None:
                self.declaration(self.text(name), "class-name", self.span(name))
            self.walk(body)
            self.scope = previous
            return
        if t in ("statement_block", "for_statement", "for_in_statement", "switch_body", "catch_clause") and create_block:
            scope = self.new_scope("block", self.span(node))
            previous = self.scope
            self.scope = scope
            if t == "for_in_statement":
                kind = node.child_by_field_name("kind")
                target_scope = self.scope if self.text(kind) in ("let", "const") else self.function_parent()
                if kind is None:
                    self.write_binding(node.child_by_field_name("left"))
                else:
                    self.binding(node.child_by_field_name("left"), "binding", target_scope)
                self.walk(node.child_by_field_name("right"))
                self.walk(node.child_by_field_name("body"))
                self.scope = previous
                return
            if t == "catch_clause":
                self.binding(node.child_by_field_name("parameter"), "binding")
            for child in node.named_children:
                if t != "catch_clause" or child != node.child_by_field_name("parameter"):
                    self.walk(child)
            self.scope = previous
            return
        if t in ("lexical_declaration", "variable_declaration"):
            scope = self.function_parent() if t == "variable_declaration" else self.scope
            for item in node.named_children:
                if item.type != "variable_declarator":
                    continue
                name = item.child_by_field_name("name")
                value = item.child_by_field_name("value")
                if name is not None and name.type == "identifier" and value is not None and value.type in (
                        "arrow_function", "function_expression", "function", "generator_function"):
                    self.function(value, self.text(name), scope, name)
                else:
                    self.binding(name, "binding", scope)
                    self.walk(value)
            return
        if t == "for_in_statement":
            # This path runs only when a caller disabled block creation.
            self.block("for-in binding scope is unresolved")
        if t in ("assignment_expression", "augmented_assignment_expression"):
            self.write_binding(node.child_by_field_name("left"))
            self.walk(node.child_by_field_name("right"))
            return
        if t == "update_expression":
            self.write_binding(node.child_by_field_name("argument"))
            return
        if t in ("call_expression", "new_expression"):
            function = node.child_by_field_name("function") or node.child_by_field_name("constructor")
            if function is not None:
                parts = self.parts(function)
                call_parts = parts
                if (
                    t == "call_expression"
                    and parts
                    and (
                        (len(parts) == 1 and parts[0] in self.tauri_invoke_locals)
                        or (len(parts) == 2 and parts[0] in self.tauri_namespaces and parts[1] == "invoke")
                    )
                ):
                    shadowed = any(
                        d["name"] == parts[0] and d.get("lexical") is not False
                        for d in self.data["declarations"]
                    )
                    args_node = node.child_by_field_name("arguments")
                    first_arg = (
                        args_node.named_children[0]
                        if args_node is not None and args_node.named_children
                        else None
                    )
                    if (
                        not shadowed
                        and first_arg is not None
                        and first_arg.type == "string"
                        and not any(
                            c.type in ("template_substitution", "escape_sequence")
                            for c in first_arg.named_children
                        )
                    ):
                        raw_cmd = self.text(first_arg).strip("\"'`")
                        if raw_cmd.isidentifier():
                            synth_local = f"__tauri_invoke_{raw_cmd}"
                            if raw_cmd not in self.tauri_commands_bound:
                                self.tauri_commands_bound.add(raw_cmd)
                                self.data["imports"].append({
                                    "scope": "module",
                                    "local": synth_local,
                                    "module": f"tauri::command::{raw_cmd}",
                                    "imported": raw_cmd,
                                    "mode": "named",
                                    "span": self.span(first_arg),
                                })
                            call_parts = [synth_local]
                if not call_parts and function.type == "member_expression":
                    # A member of a computed value keeps its name, so the call can be classified and asked.
                    prop = function.child_by_field_name("property")
                    if prop is not None and prop.type in ("property_identifier", "private_property_identifier"):
                        call_parts = ["(expr)", self.text(prop)]
                self.reference(call_parts, "call", self.span(function),
                               "dynamic-callee" if not call_parts or call_parts[0] == "(expr)" else None)
                if not parts:
                    self.walk(function.child_by_field_name("object") if call_parts else function)
                if parts == ["eval"]:
                    scope = self.scope
                    while scope is not None:
                        self.scope_by_id[scope].update(unresolved=True, reason="direct eval may mutate lexical bindings")
                        scope = self.scope_by_id[scope]["parent"]
                    self.note("direct eval may mutate lexical bindings")
            self.walk(node.child_by_field_name("arguments"))
            return
        if t == "member_expression":
            parts = self.parts(node)
            if parts:
                self.reference(parts, "read", self.span(node))
                return
        if t in ("identifier", "shorthand_property_identifier"):
            self.reference([self.text(node)], "read", self.span(node))
            return
        if t in ("with_statement", "import_require_clause", "internal_module", "module"):
            self.block(f"unsupported lexical construct: {t}")
        for child in node.named_children:
            self.walk(child)


def treesitter_semantics(root, src, language):
    return _TreeSitterEvidence(src, language).extract(root)


def java_semantics(root, src):
    return treesitter_semantics(root, src, "java")


def rust_semantics(root, src):
    return treesitter_semantics(root, src, "rust")


def go_semantics(root, src):
    return treesitter_semantics(root, src, "go")


def kotlin_semantics(root, src):
    return treesitter_semantics(root, src, "kotlin")


def csharp_semantics(root, src):
    return treesitter_semantics(root, src, "csharp")


def c_semantics(root, src, statics=()):
    return _CFamilyEvidence(src, "c", statics).extract(root)


def cpp_semantics(root, src, statics=()):
    return _CFamilyEvidence(src, "cpp", statics).extract(root)


_TS_SKIP_NODES = frozenset({
    "line_comment", "block_comment", "doc_comment", "comment",
    "package_declaration", "package_clause", "package_header", "modifiers", "modifier",
    "marker_annotation", "annotation", "attribute_item", "inner_attribute_item",
    "attribute_list", "binding_pattern_kind", "delegation_specifier", "base_list",
    "type_identifier", "user_type", "nullable_type", "predefined_type", "implicit_type",
    "type_argument_list", "primitive_type", "generic_type", "scoped_type_identifier",
    "qualified_type", "integral_type", "floating_point_type", "boolean_type",
    "void_type", "array_type", "slice_type", "pointer_type", "reference_type",
    "tuple_type", "unit_type", "map_type", "channel_type", "function_type",
    "struct_type", "interface_type", "wildcard", "type_arguments",
    "type_parameters", "type_parameter_list", "where_clause", "superclass",
    "super_interfaces", "extends_interfaces", "throws", "macro_definition",
    "string_literal", "raw_string_literal", "interpreted_string_literal",
    "character_literal", "char_literal", "rune_literal", "decimal_integer_literal",
    "hex_integer_literal", "octal_integer_literal", "binary_integer_literal",
    "integer_literal", "int_literal", "decimal_floating_point_literal",
    "hex_floating_point_literal", "float_literal", "imaginary_literal",
    "boolean_literal", "true", "false", "null_literal", "nil", "iota",
})
_TS_CLASS_NODES = frozenset({
    "class_declaration", "interface_declaration", "enum_declaration",
    "record_declaration", "annotation_type_declaration",
    "struct_item", "enum_item", "union_item", "trait_item", "type_item",
    "object_declaration", "struct_declaration", "type_alias",
})
_TS_CALLABLE_NODES = frozenset({
    "method_declaration", "constructor_declaration", "compact_constructor_declaration",
    "function_item", "function_declaration",
    "lambda_expression", "closure_expression", "func_literal",
})
_TS_ANON_CALLABLES = {
    "lambda_expression": "(lambda)",
    "closure_expression": "(closure)",
    "func_literal": "(func)",
}
_TS_BLOCK_NODES = frozenset({
    "block", "for_statement", "enhanced_for_statement",
    "switch_block_statement_group", "switch_rule", "try_statement",
    "try_with_resources_statement", "catch_clause", "for_expression",
    "while_expression", "loop_expression", "match_arm", "if_statement",
    "expression_switch_statement", "type_switch_statement", "select_statement",
    "expression_case", "default_case", "type_case", "communication_case",
})
_TS_MEMBER_NODES = frozenset({
    "field_access", "field_expression", "scoped_identifier",
    "scoped_type_identifier", "selector_expression",
    "navigation_expression", "member_access_expression",
})


_CALLEE_NAME_NODES = frozenset({"identifier", "type_identifier", "field_identifier", "simple_identifier",
                                 "property_identifier", "name"})


class _TreeSitterEvidence(_Evidence):
    """Unified Tree-sitter semantic extractor backed by ._treesitter helpers and tags.scm."""

    def __init__(self, src, language):
        super().__init__("tree-sitter")
        self.src = src
        self.language = language
        self.tag_calls = set()
        self.writes = []

    def extract(self, root):
        from ._treesitter import query_tags

        for node in query_tags(self.language, root).get("reference.call", ()):
            if node.type != "macro_invocation":
                self.tag_calls.add((node.start_byte, node.end_byte, node.type))
        self.walk(root)
        return self.settle()

    def settle(self):
        """Move each assignment to the scope that binds its name, then sort the facts."""
        write_ids = {d["id"] for d in self.writes}
        bindings = {(d["scope"], d["name"]) for d in self.data["declarations"]
                    if d["id"] not in write_ids and d.get("lexical") is not False}
        bindings.update((i["scope"], i["local"]) for i in self.data["imports"])
        for declaration in self.writes:
            scope = declaration["scope"]
            while (scope, declaration["name"]) not in bindings and scope != "module":
                scope = self.scope_by_id[scope]["parent"]
            declaration["scope"] = scope
            declaration["qualified_name"] = self.qualified(declaration["name"], scope)
        return self.finish()

    def text(self, node):
        from ._treesitter import node_text

        return node_text(node, self.src) if node is not None else ""

    @staticmethod
    def span(node):
        return [node.start_point[0] + 1, node.start_point[1], node.end_point[0] + 1, node.end_point[1]]

    def parts(self, node):
        if node is None:
            return []
        if node.type in ("identifier", "type_identifier", "simple_identifier", "this", "self", "super", "crate"):
            return [self.text(node)]
        if node.type == "navigation_suffix":
            ident = next((c for c in node.named_children if c.type in ("simple_identifier", "identifier", "type_identifier")), None)
            return [self.text(ident)] if ident is not None else []
        if node.type == "navigation_expression":
            if len(node.named_children) >= 2:
                prefix = self.parts(node.named_children[0])
                suffix = self.parts(node.named_children[-1])
                if prefix and suffix:
                    return prefix + suffix
            return []
        if node.type == "generic_function":
            return self.parts(node.child_by_field_name("function"))
        if node.type == "generic_type":
            first = next((c for c in node.named_children if c.type != "type_arguments"), None)
            return self.parts(first)
        if node.type in _TS_MEMBER_NODES:
            obj = (node.child_by_field_name("object") or node.child_by_field_name("expression")
                   or node.child_by_field_name("scope") or node.child_by_field_name("path")
                   or node.child_by_field_name("value") or node.child_by_field_name("operand"))
            field = node.child_by_field_name("field") or node.child_by_field_name("name")
            if obj is None and len(node.named_children) >= 2:
                obj, field = node.named_children[0], node.named_children[-1]
            prefix = self.parts(obj)
            if prefix and field is not None and field.type in ("identifier", "type_identifier", "field_identifier", "simple_identifier"):
                return prefix + [self.text(field)]
        return []

    def member_name(self, node):
        """The name a member access ends with (`x.f`, `x->f`, `x?.f`), or None for any other callee."""
        if node is None or node.type not in _TS_MEMBER_NODES:
            return None
        field = node.child_by_field_name("field") or node.child_by_field_name("name")
        if field is None and node.named_children:
            field = node.named_children[-1]
            if field.type == "navigation_suffix":
                field = next((c for c in field.named_children if c.type in _CALLEE_NAME_NODES), None)
        return field if field is not None and field.type in _CALLEE_NAME_NODES else None

    def last_name(self, node, name):
        """The rightmost identifier under `node` spelled `name`, where a callee's name ends."""
        found, stack = None, [node]
        while stack:
            item = stack.pop()
            if item.type in _CALLEE_NAME_NODES and self.text(item) == name and (
                    found is None or item.end_byte > found.end_byte):
                found = item
            stack.extend(item.named_children)
        return found

    def _is_exported(self, node, name):
        if self.scope != "module" or not name:
            return False
        if self.language == "java":
            return not any(c.type == "modifiers" and "private" in self.text(c).split() for c in node.children)
        if self.language == "kotlin":
            return not any(
                c.type == "modifiers"
                and any(tok in ("private", "protected", "internal") for tok in self.text(c).split())
                for c in node.children
            )
        if self.language == "csharp":
            return any(c.type == "modifier" and self.text(c).strip() == "public" for c in node.children)
        if self.language == "rust":
            if any(
                c.type == "visibility_modifier"
                and self.text(c).strip().startswith("pub")
                and self.text(c).strip() != "pub(self)"
                for c in node.children
            ):
                return True
            prev = getattr(node, "prev_named_sibling", None)
            while prev is not None and prev.type == "attribute_item":
                attr_text = self.text(prev)
                if "tauri::command" in attr_text or "#[command" in attr_text:
                    return True
                prev = getattr(prev, "prev_named_sibling", None)
            return False
        if self.language == "go":
            return name.split(".")[-1][:1].isupper()
        return False

    def _bind_pattern(self, node, kind):
        if node is None:
            return
        t = node.type
        if t in ("identifier", "shorthand_field_identifier", "simple_identifier"):
            name = self.text(node)
            if name != "_":
                self.declaration(name, kind, self.span(node))
        elif t in ("_", "remaining_field_pattern", "rest_pattern", "mutable_specifier", "type_identifier", "scoped_identifier"):
            return
        elif t in ("mut_pattern", "reference_pattern", "ref_pattern", "tuple_pattern", "slice_pattern", "or_pattern", "captured_pattern"):
            for child in node.named_children:
                if child.type != "mutable_specifier":
                    self._bind_pattern(child, kind)
        elif t == "tuple_struct_pattern":
            for child in node.named_children:
                if child != node.child_by_field_name("type"):
                    self._bind_pattern(child, kind)
        elif t == "struct_pattern":
            for child in node.named_children:
                if child.type == "field_pattern":
                    pat = child.child_by_field_name("pattern")
                    if pat is not None:
                        self._bind_pattern(pat, kind)
                    else:
                        for sub in child.named_children:
                            if sub.type in ("shorthand_field_identifier", "identifier"):
                                self._bind_pattern(sub, kind)
        elif t not in _TS_SKIP_NODES:
            self.block(f"unsupported binding pattern: {t}")

    def _write_binding(self, node):
        if node is None:
            return
        if node.type == "identifier":
            name = self.text(node)
            if name != "_":
                self.declaration(name, "binding", self.span(node))
                self.writes.append(self.data["declarations"][-1])
        elif node.type == "expression_list":
            for child in node.named_children:
                self._write_binding(child)
        else:
            self.walk(node)

    def _contract(self, owner: str, item) -> None:
        """Declare an interface or trait method that has no body, so an engine's answer can land on it."""
        name = item.child_by_field_name("name")
        if name is None:
            return
        member = self.text(name)
        self.declaration(member, "method", self.span(item), extra={
            "name_span": self.span(name), "contract": True, "lexical": False, "qualified_name": f"{owner}.{member}"})

    def _bind_params(self, params):
        if params is None:
            return
        if params.type == "identifier":
            self._bind_pattern(params, "parameter")
            return
        for param in params.named_children:
            pt = param.type
            if pt == "identifier":
                self._bind_pattern(param, "parameter")
            elif pt == "self_parameter":
                self.declaration("self", "parameter", self.span(param))
            elif pt in ("parameter", "class_parameter", "function_value_parameter"):
                pat = (
                    param.child_by_field_name("pattern")
                    or param.child_by_field_name("name")
                    or next((c for c in param.named_children if c.type in ("simple_identifier", "identifier")), None)
                )
                self._bind_pattern(pat, "parameter")
            elif pt in ("parameter_declaration", "variadic_parameter_declaration"):
                for name in param.children_by_field_name("name"):
                    self._bind_pattern(name, "parameter")
            elif pt in ("formal_parameter", "spread_parameter"):
                pname = param.child_by_field_name("name")
                if pname is None:
                    decl = next((c for c in param.named_children if c.type == "variable_declarator"), None)
                    pname = decl.child_by_field_name("name") if decl is not None else None
                self._bind_pattern(pname, "parameter")
            else:
                self._bind_pattern(param.child_by_field_name("name") or param, "parameter")

    def _use_tree(self, node, prefix=""):
        if node is None:
            return
        t = node.type
        if t == "use_wildcard":
            self.block("wildcard use declaration introduces unknown bindings")
        elif t == "identifier":
            name = self.text(node)
            full = f"{prefix}::{name}" if prefix else name
            self.data["imports"].append({
                "scope": self.scope, "local": name, "module": full,
                "imported": name, "mode": "named", "span": self.span(node),
            })
        elif t == "scoped_identifier":
            raw = self.text(node)
            full = f"{prefix}::{raw}" if prefix else raw
            name_node = node.child_by_field_name("name")
            imported = self.text(name_node) if name_node is not None else full.rsplit("::", 1)[-1]
            self.data["imports"].append({
                "scope": self.scope, "local": imported, "module": full,
                "imported": imported, "mode": "named", "span": self.span(name_node or node),
            })
        elif t == "use_as_clause":
            raw_path = self.text(node.child_by_field_name("path"))
            alias_node = node.child_by_field_name("alias")
            full = f"{prefix}::{raw_path}" if prefix else raw_path
            if alias_node is not None and self.text(alias_node) != "_":
                if raw_path == "self" and prefix:
                    self.data["imports"].append({
                        "scope": self.scope, "local": self.text(alias_node),
                        "module": prefix, "imported": "*",
                        "mode": "namespace", "span": self.span(alias_node),
                    })
                else:
                    self.data["imports"].append({
                        "scope": self.scope, "local": self.text(alias_node),
                        "module": full, "imported": raw_path.rsplit("::", 1)[-1],
                        "mode": "named", "span": self.span(alias_node),
                    })
        elif t == "scoped_use_list":
            path_node = node.child_by_field_name("path")
            list_node = node.child_by_field_name("list")
            sub = self.text(path_node) if path_node is not None else ""
            full_prefix = f"{prefix}::{sub}" if prefix and sub else (sub or prefix)
            for item in (list_node.named_children if list_node is not None else ()):
                if item.type == "self":
                    self.data["imports"].append({
                        "scope": self.scope, "local": full_prefix.rsplit("::", 1)[-1],
                        "module": full_prefix, "imported": "*", "mode": "namespace", "span": self.span(item),
                    })
                else:
                    self._use_tree(item, full_prefix)
        elif t == "use_list":
            for item in node.named_children:
                self._use_tree(item, prefix)

    def _go_import_spec(self, spec):
        path_node = spec.child_by_field_name("path")
        if path_node is None:
            return
        module = self.text(path_node).strip('"`')
        alias_node = spec.child_by_field_name("name")
        alias = self.text(alias_node) if alias_node is not None else None
        if alias == ".":
            self.block("dot import introduces unknown package bindings")
        elif alias != "_":
            local = alias or module.rsplit("/", 1)[-1]
            if local:
                self.data["imports"].append({
                    "scope": self.scope, "local": local, "module": module,
                    "imported": "*", "mode": "namespace", "span": self.span(alias_node or spec),
                })

    def walk(self, node, create_block=True):
        if node is None or node.type in _TS_SKIP_NODES:
            return
        t = node.type
        if t == "import_declaration":
            if self.language == "go":
                for child in node.named_children:
                    if child.type == "import_spec":
                        self._go_import_spec(child)
                    elif child.type == "import_spec_list":
                        for spec in child.named_children:
                            if spec.type == "import_spec":
                                self._go_import_spec(spec)
                return
            if any(c.type == "asterisk" for c in node.children):
                self.block("wildcard import introduces unknown bindings")
                return
            full = self.text(node).removeprefix("import").strip().rstrip(";").strip()
            is_static = full.startswith("static ")
            if is_static:
                full = full.removeprefix("static").strip()
            module = (full.rsplit(".", 1)[0] if "." in full else full) if is_static else full
            imported = full.rsplit(".", 1)[-1]
            if module and imported:
                self.data["imports"].append({
                    "scope": self.scope, "local": imported, "module": module,
                    "imported": imported, "mode": "named", "span": self.span(node),
                })
            return
        if t == "import_list":
            for child in node.named_children:
                self.walk(child)
            return
        if t == "import_header":
            raw = self.text(node).removeprefix("import").strip()
            if ".*" in raw:
                self.block("wildcard import introduces unknown bindings")
                return
            ident = next((c for c in node.named_children if c.type == "identifier"), None)
            alias_node = next((c for c in node.named_children if c.type == "import_alias"), None)
            if ident is not None:
                module = self.text(ident).strip()
                imported = module.rsplit(".", 1)[-1]
                local = imported
                if alias_node is not None and alias_node.named_children:
                    local = self.text(alias_node.named_children[0]).strip()
                if module and imported and local:
                    self.data["imports"].append({
                        "scope": self.scope, "local": local, "module": module,
                        "imported": imported, "mode": "named", "span": self.span(node),
                    })
            return
        if t == "using_directive":
            raw = self.text(node).removeprefix("using").strip().rstrip(";").strip()
            if raw.startswith("static "):
                raw = raw.removeprefix("static").strip()
            if "=" in raw:
                local, module = [p.strip() for p in raw.split("=", 1)]
                imported = module.rsplit(".", 1)[-1]
            else:
                module = raw
                imported = raw.rsplit(".", 1)[-1]
                local = imported
            if module and imported and local:
                self.data["imports"].append({
                    "scope": self.scope, "local": local, "module": module,
                    "imported": imported, "mode": "named", "span": self.span(node),
                })
            return
        if t in ("namespace_declaration", "file_scoped_namespace_declaration", "declaration_list"):
            body = node.child_by_field_name("body")
            target = body if body is not None else node
            for child in target.named_children:
                if child != node.child_by_field_name("name"):
                    self.walk(child, create_block=False)
            return
        if t == "use_declaration":
            self._use_tree(node.child_by_field_name("argument"))
            return
        if t == "type_declaration":
            for spec in node.named_children:
                if spec.type in ("type_spec", "type_alias"):
                    name_node = spec.child_by_field_name("name")
                    if name_node is not None:
                        name = self.text(name_node)
                        self.declaration(name, "class", self.span(spec), extra={"name_span": self.span(name_node)})
                        if self._is_exported(spec, name):
                            self.data["exports"].append({"exported": name, "local": name})
                        interface = spec.child_by_field_name("type")
                        for member in interface.named_children if interface is not None and                                 interface.type == "interface_type" else ():
                            if member.type in ("method_elem", "method_spec"):
                                self._contract(name, member)
            return
        if t == "function_signature_item":
            # A trait's method without a body: the call goes through it, as through an interface method.
            owner = node.parent.parent.child_by_field_name("name") if node.parent is not None and                 node.parent.parent is not None else None
            self._contract(self.text(owner) if owner is not None else "(trait)", node)
            return
        if t in _TS_CLASS_NODES:
            name_node = node.child_by_field_name("name") or next(
                (c for c in node.named_children if c.type in ("type_identifier", "simple_identifier", "identifier")),
                None,
            )
            name = self.text(name_node) if name_node is not None else None
            identity = self.declaration(name, "class", self.span(node),
                                        extra={"name_span": self.span(name_node)}) if name else None
            if self._is_exported(node, name):
                self.data["exports"].append({"exported": name, "local": name})
            body = node.child_by_field_name("body") or next(
                (c for c in node.named_children if c.type in ("class_body", "enum_class_body", "declaration_list")),
                None,
            )
            if t == "enum_item" and body is not None:
                # `Variant(x)` is a call that builds the variant: an engine answers on the variant's name.
                for variant in body.named_children:
                    variant_name = variant.child_by_field_name("name") if variant.type == "enum_variant" else None
                    if variant_name is not None:
                        self.declaration(self.text(variant_name), "method", self.span(variant), extra={
                            "name_span": self.span(variant_name), "contract": True, "lexical": False,
                            "qualified_name": f"{name}::{self.text(variant_name)}"})
            if body is not None and (self.language in ("java", "kotlin", "csharp") or t == "trait_item"):
                scope = self.new_scope("class", self.span(node))
                if identity is not None:
                    self.scope_by_id[scope]["declaration"] = identity
                previous = self.scope
                self.scope = scope
                if t == "record_declaration":
                    self._bind_params(node.child_by_field_name("parameters") or next((c for c in node.named_children if c.type == "parameter_list"), None))
                for pctor in (c for c in node.named_children if c.type == "primary_constructor"):
                    self._bind_params(pctor)
                self.walk(body, create_block=False)
                self.scope = previous
            return
        if t == "impl_item":
            type_node = node.child_by_field_name("type")
            trait_node = node.child_by_field_name("trait")
            if trait_node is not None and type_node is not None:
                impl_name = f"{self.text(trait_node)} for {self.text(type_node)}"
            elif type_node is not None:
                impl_name = self.text(type_node)
            else:
                impl_name = "?"
            identity = self.declaration(impl_name, "class", self.span(node))
            self.data["declarations"][-1]["lexical"] = False
            scope = self.new_scope("class", self.span(node))
            self.scope_by_id[scope]["declaration"] = identity
            previous = self.scope
            self.scope = scope
            self.walk(node.child_by_field_name("body"), create_block=False)
            self.scope = previous
            return
        if t == "mod_item":
            name_node = node.child_by_field_name("name")
            identity = None
            if name_node is not None:
                name = self.text(name_node)
                identity = self.declaration(name, "class", self.span(node))
                if self._is_exported(node, name):
                    self.data["exports"].append({"exported": name, "local": name})
            body = node.child_by_field_name("body")
            if body is not None:
                scope = self.new_scope("block", self.span(body))
                if identity is not None:
                    self.scope_by_id[scope]["declaration"] = identity
                previous = self.scope
                self.scope = scope
                self.walk(body, create_block=False)
                self.scope = previous
            return
        if t in _TS_CALLABLE_NODES:
            anon = _TS_ANON_CALLABLES.get(t)
            name_node = node.child_by_field_name("name") or next(
                (c for c in node.named_children if c.type in ("simple_identifier", "identifier")),
                None,
            )
            receiver = node.child_by_field_name("receiver") if self.language == "go" and t == "method_declaration" else None
            if anon:
                name = anon
            elif receiver is not None:
                decl = next((c for c in receiver.children if c.type == "parameter_declaration"), None)
                tnode = decl.child_by_field_name("type") if decl is not None else None
                mname = self.text(name_node)
                rname = self.text(tnode).strip().lstrip("*").split("[", 1)[0].strip() if tnode is not None else ""
                name = f"{rname}.{mname}" if rname else mname
            else:
                name = self.text(name_node) if name_node is not None else "(constructor)"
            non_lexical = bool(anon or receiver is not None or (
                self.language == "rust" and self.scope_by_id[self.scope]["kind"] == "class"
            ))
            # Where an engine names this callable; an anonymous one has no name to answer with.
            named = {"name_span": self.span(name_node)} if name_node is not None and not anon else None
            identity = self.declaration(name, "function", self.span(node), extra=named)
            if non_lexical:
                self.data["declarations"][-1]["lexical"] = False
            if not anon and (receiver is not None or not non_lexical) and self._is_exported(node, name):
                self.data["exports"].append({"exported": name, "local": name})
            scope = self.new_scope("function", self.span(node), caller=identity)
            previous = self.scope, self.caller
            self.scope, self.caller = scope, identity
            self._bind_params(receiver)
            params_node = node.child_by_field_name("parameters") or next(
                (c for c in node.named_children if c.type in ("function_value_parameters", "parameter_list")),
                None,
            )
            self._bind_params(params_node)
            body_node = node.child_by_field_name("body") or next(
                (c for c in node.named_children if c.type in ("function_body", "block", "arrow_expression_clause")),
                None,
            )
            self.walk(body_node, create_block=False)
            self.scope, self.caller = previous
            return
        if t == "property_declaration":
            if self.language == "csharp":
                self._bind_pattern(node.child_by_field_name("name"), "binding")
                for child in node.named_children:
                    if child != node.child_by_field_name("name") and child != node.child_by_field_name("type"):
                        self.walk(child)
            else:
                vdecl = next((c for c in node.named_children if c.type == "variable_declaration"), None)
                if vdecl is not None:
                    vname = next((c for c in vdecl.named_children if c.type == "simple_identifier"), None)
                    self._bind_pattern(vname, "binding")
                for child in node.named_children:
                    if child.type not in ("modifiers", "binding_pattern_kind", "variable_declaration"):
                        self.walk(child)
            return
        if t == "local_declaration_statement":
            for child in node.named_children:
                if child.type == "variable_declaration":
                    for sub in child.named_children:
                        if sub.type == "variable_declarator":
                            self._bind_pattern(sub.child_by_field_name("name"), "binding")
                            for expr in sub.named_children:
                                if expr != sub.child_by_field_name("name"):
                                    self.walk(expr)
            return
        if t in ("field_declaration", "constant_declaration", "local_variable_declaration"):
            for child in node.named_children:
                if child.type == "variable_declarator":
                    self._bind_pattern(child.child_by_field_name("name"), "binding")
                    self.walk(child.child_by_field_name("value"))
                elif child.type == "variable_declaration":
                    for sub in child.named_children:
                        if sub.type == "variable_declarator":
                            self._bind_pattern(sub.child_by_field_name("name"), "binding")
                            for expr in sub.named_children:
                                if expr != sub.child_by_field_name("name"):
                                    self.walk(expr)
            return
        if t in ("enum_constant", "const_item", "static_item", "resource"):
            self._bind_pattern(node.child_by_field_name("name"), "binding")
            self.walk(node.child_by_field_name("value") or node.child_by_field_name("arguments"))
            self.walk(node.child_by_field_name("body"))
            return
        if t in ("const_declaration", "var_declaration"):
            for spec in node.named_children:
                if spec.type in ("const_spec", "var_spec"):
                    self.walk(spec.child_by_field_name("value"))
                    for n in spec.children_by_field_name("name"):
                        self._bind_pattern(n, "binding")
            return
        if t in ("let_declaration", "let_condition"):
            self.walk(node.child_by_field_name("value"))
            self._bind_pattern(node.child_by_field_name("pattern"), "binding")
            return
        if t == "short_var_declaration":
            self.walk(node.child_by_field_name("right"))
            left = node.child_by_field_name("left")
            if left is not None:
                for ident in left.named_children if left.type == "expression_list" else [left]:
                    if ident.type == "identifier":
                        self._bind_pattern(ident, "binding")
            return
        if t in ("assignment_expression", "augmented_assignment_expression", "assignment_statement"):
            self._write_binding(node.child_by_field_name("left"))
            self.walk(node.child_by_field_name("right"))
            return
        if t in ("update_expression", "inc_statement", "dec_statement"):
            self._write_binding(node.child_by_field_name("argument") or (node.named_children[0] if node.named_children else None))
            return
        if t == "if_expression":
            scope = self.new_scope("block", self.span(node))
            previous = self.scope
            self.scope = scope
            self.walk(node.child_by_field_name("condition"))
            self.walk(node.child_by_field_name("consequence"), create_block=False)
            self.scope = previous
            self.walk(node.child_by_field_name("alternative"))
            return
        if t in _TS_BLOCK_NODES and create_block:
            if t == "enhanced_for_statement":
                self.walk(node.child_by_field_name("value"))
            elif t == "for_expression":
                self.walk(node.child_by_field_name("value"))
            scope = self.new_scope("block", self.span(node))
            previous = self.scope
            self.scope = scope
            if t == "enhanced_for_statement":
                self._bind_pattern(node.child_by_field_name("name"), "binding")
            elif t == "catch_clause":
                param = next((c for c in node.named_children if c.type == "catch_formal_parameter"), None)
                if param is not None:
                    self._bind_pattern(param.child_by_field_name("name"), "binding")
            elif t == "for_expression":
                self._bind_pattern(node.child_by_field_name("pattern"), "binding")
            elif t == "match_arm":
                pat = node.child_by_field_name("pattern")
                for sub in (pat.named_children if pat is not None and pat.type == "match_pattern" else ([pat] if pat else ())):
                    self._bind_pattern(sub, "binding")
            for child in node.named_children:
                if child.type == "range_clause":
                    self.scope = previous
                    self.walk(child.child_by_field_name("right"))
                    self.scope = scope
                    left = child.child_by_field_name("left")
                    for ident in (left.named_children if left is not None and left.type == "expression_list" else ([left] if left else ())):
                        self._bind_pattern(ident, "binding")
                elif child.type not in ("catch_formal_parameter", "match_pattern") and child not in (
                    node.child_by_field_name("pattern"),
                    node.child_by_field_name("name") if t == "enhanced_for_statement" else None,
                    node.child_by_field_name("value") if t in ("enhanced_for_statement", "for_expression") else None,
                ):
                    self.walk(child, create_block=not (t == "for_expression" and child == node.child_by_field_name("body")))
            self.scope = previous
            return
        if t == "macro_invocation":
            self.note("macro expansion bindings are not inferred")
            return
        if t in ("call_expression", "method_invocation", "invocation_expression", "object_creation_expression") or (
            node.start_byte, node.end_byte, t
        ) in self.tag_calls:
            if t == "method_invocation":
                obj = node.child_by_field_name("object")
                name = node.child_by_field_name("name")
                obj_parts = self.parts(obj)
                if obj is None and name is not None:
                    parts = [self.text(name)]
                elif obj_parts and name is not None:
                    parts = obj_parts + [self.text(name)]
                elif name is not None:
                    parts = ["(expr)", self.text(name)]
                else:
                    parts = []
                target_node = name if obj is None and name is not None else node
                # The callee runs from the receiver to the method name, never over the arguments.
                callee_span = [obj.start_point[0] + 1, obj.start_point[1], name.end_point[0] + 1,
                               name.end_point[1]] if obj is not None and name is not None else None
                if obj is not None and not obj_parts:
                    self.walk(obj)
            elif t == "object_creation_expression":
                target_node = node.child_by_field_name("type") or node
                parts = self.parts(node.child_by_field_name("type"))
                callee_span = None
            else:
                target_node = (
                    node.child_by_field_name("function")
                    or (node.named_children[0] if self.language == "kotlin" and node.named_children else None)
                    or node
                )
                parts = self.parts(target_node)
                callee_span = None
                member = self.member_name(target_node) if not parts else None
                if member is not None:
                    # A member of a computed value keeps its name, so the call can be classified and asked.
                    parts = ["(expr)", self.text(member)]
                    receiver = target_node.child_by_field_name("object") or target_node.child_by_field_name(
                        "expression") or target_node.child_by_field_name("operand") or target_node.child_by_field_name(
                        "value") or (target_node.named_children[0] if target_node.named_children else None)
                    self.walk(receiver)
                elif target_node is not node and not parts:
                    self.walk(target_node)
            if callee_span is None:
                callee_span = self.span(target_node)
                named = self.last_name(target_node, parts[-1]) if parts else None
                if named is not None:
                    # Type arguments after the name (`List<T>`, `foo::<T>`) are not part of the callee.
                    callee_span = callee_span[:2] + [named.end_point[0] + 1, named.end_point[1]]
            self.reference(
                parts,
                "call",
                callee_span,
                "dynamic-callee" if (not parts or parts[0] == "(expr)") else None,
            )
            args_node = node.child_by_field_name("arguments") or next(
                (c for c in node.named_children if c.type in ("call_suffix", "value_arguments", "argument_list")),
                None,
            )
            self.walk(args_node)
            for child in node.named_children:
                if child.type == "class_body":
                    scope = self.new_scope("class", self.span(child))
                    previous = self.scope
                    self.scope = scope
                    self.walk(child, create_block=False)
                    self.scope = previous
            return
        if t in _TS_MEMBER_NODES:
            parts = self.parts(node)
            if parts:
                self.reference(parts, "read", self.span(node))
            else:
                self.walk(node.child_by_field_name("object") or node.child_by_field_name("expression")
                          or node.child_by_field_name("value") or node.child_by_field_name("path")
                          or node.child_by_field_name("operand")
                          or (node.named_children[0] if node.named_children else None))
            return
        if t in ("identifier", "simple_identifier"):
            self.reference([self.text(node)], "read", self.span(node))
            return
        for child in node.named_children:
            self.walk(child)


# ---------------------------------------------------------------------------
# C and C++.
# ---------------------------------------------------------------------------

# A declarator wraps its name: `*p`, `&r`, `a[3]`, `x = 1`, `(*fp)(int)`.
_C_WRAPPERS = frozenset({"init_declarator", "pointer_declarator", "reference_declarator", "attributed_declarator",
                         "array_declarator", "parenthesized_declarator"})
_C_NAMES = frozenset({"identifier", "field_identifier", "type_identifier", "qualified_identifier",
                      "destructor_name", "operator_name", "operator_cast", "template_function"})
_C_RECORDS = frozenset({"struct_specifier", "union_specifier", "class_specifier", "enum_specifier"})
_C_CASTS = frozenset({"static_cast", "dynamic_cast", "reinterpret_cast", "const_cast"})
_C_CONDITIONS = frozenset({"condition", "name"})  # what a `#if` or `#ifdef` tests, never code
_C_SKIP = frozenset({"preproc_def", "preproc_function_def", "preproc_call", "access_specifier",
                     "friend_declaration", "static_assert_declaration", "attribute_specifier",
                     "attribute_declaration", "ms_declspec_modifier", "namespace_alias_definition",
                     "template_parameter_list", "gnu_asm_expression", "concept_definition"})
INCLUDED_NAMES = "names the translation unit brings (includes, the including file) are not read"


def c_declarator(node):
    """`(name node, function declarator or None)` of a declarator chain; `(None, None)` without a name.

    A function declarator whose own declarator is a name declares a function; one around a parenthesized
    declarator (`(*fp)(int)`) declares a pointer to a function, which is a variable named inside.
    """
    while node is not None:
        if node.type == "function_declarator":
            inner = node.child_by_field_name("declarator")
            if inner is not None and inner.type in _C_NAMES:
                return inner, node
            node = inner
        elif node.type in _C_NAMES:
            return node, None
        elif node.type in _C_WRAPPERS:
            node = node.child_by_field_name("declarator") or next(
                (c for c in node.named_children if c.type in _C_WRAPPERS or c.type in _C_NAMES
                 or c.type == "function_declarator"), None)
        else:
            return None, None
    return None, None


def c_name_node(node):
    """The innermost name of a declarator name: `area` of `geo::Circle::area`, `twice` of `twice<int>`."""
    while node is not None and node.type in ("qualified_identifier", "template_function", "template_type",
                                             "template_method"):
        node = node.child_by_field_name("name")
    return node


def c_callable_name(node, text):
    """A declarator name as the snapshot names it: `Circle.area` for `Circle::area`, scopes joined by `.`."""
    if node is None:
        return ""
    if node.type == "qualified_identifier":
        scope = node.child_by_field_name("scope")
        head = c_callable_name(scope, text) if scope is not None else ""
        tail = c_callable_name(node.child_by_field_name("name"), text)
        return f"{head}.{tail}" if head and tail else tail
    if node.type in ("template_function", "template_type", "template_method"):
        return c_callable_name(node.child_by_field_name("name"), text)
    return " ".join(text(node).split())


def c_is_static(node, text, statics=()):
    """`static` written, or a blanked macro that can expand to it (`local int f(`) before the declarator."""
    if any(c.type == "storage_class_specifier" and text(c).strip() == "static" for c in node.children):
        return True
    declarator = node.child_by_field_name("declarator")
    limit = declarator.start_byte if declarator is not None else node.end_byte
    # The blanked macro is whitespace to the grammar, so it sits between the previous node and this one.
    previous = node.prev_sibling
    start = previous.end_byte if previous is not None else (node.parent.start_byte if node.parent else 0)
    return any(start <= offset < limit for offset in statics)


class _CFamilyEvidence(_TreeSitterEvidence):
    """C and C++ declarations, scopes, includes and references.

    The file's own top-level names sit in a scope below the module scope. The module scope stands for what the
    translation unit brings, its includes or, for a header, the file that includes it: it is always blocked, so
    a name the file does not declare stops there, never at a builtin. A prototype is a declaration with
    `contract`; in C it gives way to a definition of the same name in the same scope; a file-scope function records its `linkage`. C has no overloads, C++
    does: a C++ function outside a class binds no name, since the translation unit can add an overload and
    argument-dependent lookup can add candidates. Struct, union and enum tags are not ordinary identifiers in C,
    so they bind no name there. A
    class with a base, and the body of a member defined outside its class, stop the lookup at the members the
    file cannot list. A call to a function-like macro the file defines, or through `(*f)` or `(f)`, is dynamic.
    """

    def __init__(self, src, language, statics=()):
        super().__init__(src, language)
        self.macros = set()
        self.top = None
        self.statics = statics

    def extract(self, root):
        stack = [root]
        while stack:
            node = stack.pop()
            if node.type == "preproc_function_def":
                name = node.child_by_field_name("name")
                if name is not None:
                    self.macros.add(self.text(name))
            stack.extend(node.named_children)
        self.scope_by_id["module"].update(unresolved=True, reason=INCLUDED_NAMES)
        self.top = self.scope = self.new_scope("block", self.span(root))
        self.walk(root)
        self.scope = "module"
        if self.language == "c":
            defined = {(d["scope"], d["name"]) for d in self.data["declarations"]
                       if d["kind"] == "function" and not d.get("contract")}
            for item in self.data["declarations"]:
                if item.get("contract") and (item["scope"], item["name"]) in defined:
                    item["lexical"] = False
        self.data["exports"] = [{"exported": name, "local": name}
                                for name in dict.fromkeys(e["exported"] for e in self.data["exports"])]
        return self.settle()

    # -- helpers ---------------------------------------------------------------------------------------------

    def parts(self, node):
        if node is None:
            return []
        t = node.type
        if t in ("identifier", "field_identifier", "type_identifier", "namespace_identifier", "this",
                 "destructor_name", "operator_name"):
            return [self.text(node)]
        if t == "qualified_identifier":
            scope = node.child_by_field_name("scope")
            head = self.parts(scope) if scope is not None else []
            tail = self.parts(node.child_by_field_name("name"))
            return head + tail if head and tail else []
        if t in ("template_function", "template_type", "template_method"):
            return self.parts(node.child_by_field_name("name"))
        if t == "field_expression":
            head = self.parts(node.child_by_field_name("argument"))
            field = node.child_by_field_name("field")
            tail = self.parts(field) if field is not None else []
            return head + tail if head and len(tail) == 1 else []
        return []

    def callee_span(self, node, parts):
        span = self.span(node)
        named = self.last_name(node, parts[-1]) if parts else None
        if named is not None:
            span = span[:2] + [named.end_point[0] + 1, named.end_point[1]]
        return span

    def in_class(self):
        return self.scope_by_id[self.scope]["kind"] == "class"

    def export(self, name, static):
        if self.scope == self.top and name and not static:
            self.data["exports"].append({"exported": name, "local": name})

    def enter(self, kind, node, caller=None, declaration=None, blocked=None):
        scope = self.new_scope(kind, self.span(node), caller=caller)
        if declaration is not None:
            self.scope_by_id[scope]["declaration"] = declaration
        if blocked:
            self.scope_by_id[scope].update(unresolved=True, reason=blocked)
        previous = self.scope, self.caller
        self.scope = scope
        if caller is not None:
            self.caller = caller
        return previous

    def leave(self, previous):
        self.scope, self.caller = previous

    def callable_declaration(self, name_node, node, kind, *, contract, static):
        """Declare a function or method named by `name_node`; returns its identity."""
        head = c_name_node(name_node)
        qualified = name_node.type == "qualified_identifier"
        name = c_callable_name(name_node, self.text)
        lexical = not (qualified or (self.language == "cpp" and not self.in_class()))
        extra = {"name_span": self.span(head if head is not None else name_node)}
        if head is not None and head.type == "destructor_name" and head.named_children:
            extra["signature_spans"] = [self.span(head.named_children[0])]  # `~Name` is also named at `Name`
        if contract:
            extra["contract"] = True
        if not lexical:
            extra["lexical"] = False
        if self.scope == self.top and not qualified:
            extra["linkage"] = "internal" if static else "external"
        identity = self.declaration(name, kind, self.span(node), extra=extra)
        if not qualified:
            self.export(name, static)
        return identity

    def bind_parameters(self, params):
        for param in params.named_children if params is not None else ():
            if param.type == "identifier":  # K&R: the names, typed by declarations before the body
                self.declaration(self.text(param), "parameter", self.span(param))
                continue
            if param.type not in ("parameter_declaration", "optional_parameter_declaration",
                                  "variadic_parameter_declaration"):
                continue
            name, function = c_declarator(param.child_by_field_name("declarator"))
            if name is not None and function is None and name.type == "identifier":
                self.declaration(self.text(name), "parameter", self.span(name))
            self.walk(param.child_by_field_name("default_value"))

    # -- declarations ----------------------------------------------------------------------------------------

    def function(self, node):
        name_node, declarator = c_declarator(node.child_by_field_name("declarator"))
        body = node.child_by_field_name("body")
        if name_node is None or declarator is None:
            self.note("function definition without a declarator name")
            previous = self.enter("block", node)
            self.walk(body, create_block=False)
            self.leave(previous)
            return
        identity = self.callable_declaration(name_node, node, "function", contract=False,
                                             static=c_is_static(node, self.text, self.statics))
        outside = None
        if name_node.type == "qualified_identifier":
            # A member defined outside its class: the class's members are names this body can see.
            outside = self.enter("block", node, blocked="members of the qualifying class are not read")
        previous = self.enter("function", node, caller=identity)
        self.bind_parameters(declarator.child_by_field_name("parameters"))
        for child in node.named_children:
            if child.type == "field_initializer_list":
                for item in child.named_children:
                    for argument in item.named_children:
                        if argument.type in ("argument_list", "initializer_list"):
                            self.walk(argument)
        self.walk(body, create_block=False)
        self.leave(previous)
        if outside is not None:
            self.leave(outside)

    def declaration_node(self, node):
        """A `declaration` or `field_declaration`: prototypes, variables and fields, and a record in its type."""
        self.record(node.child_by_field_name("type"))
        static = c_is_static(node, self.text, self.statics)
        member = self.in_class()
        for declarator in node.children_by_field_name("declarator"):
            name_node, function = c_declarator(declarator)
            if name_node is not None and function is not None:
                self.callable_declaration(name_node, function, "method" if member else "function",
                                          contract=True, static=static)
                continue
            # A C struct's fields are no names a lookup finds; a C++ class's are, in its scope.
            if name_node is not None and (node.type == "declaration" or self.language == "cpp"):
                qualified = name_node.type == "qualified_identifier"
                name = c_callable_name(name_node, self.text)
                identity = self.declaration(name, "binding", self.span(c_name_node(name_node) or name_node))
                if qualified:
                    self.declaration_by_id[identity]["lexical"] = False
                else:
                    self.export(name, static)
            value = declarator.child_by_field_name("value") if declarator.type == "init_declarator" else None
            self.walk(value)
        self.walk(node.child_by_field_name("default_value"))

    def type_definition(self, node):
        self.record(node.child_by_field_name("type"))
        for declarator in node.children_by_field_name("declarator"):
            name_node, _ = c_declarator(declarator)
            if name_node is not None:
                name = self.text(name_node)
                self.declaration(name, "class", self.span(node), extra={"name_span": self.span(name_node)})
                self.export(name, False)

    def record(self, node):
        """A struct, union, class or enum with a body; a mention of one without a body declares nothing."""
        if node is None or node.type not in _C_RECORDS or node.child_by_field_name("body") is None:
            return
        name_node = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        identity = None
        if name_node is not None:
            head = c_name_node(name_node)
            name = c_callable_name(name_node, self.text)
            extra = {"name_span": self.span(head if head is not None else name_node)}
            if self.language == "c" or name_node.type == "qualified_identifier":
                extra["lexical"] = False  # a C tag is not an ordinary identifier
            identity = self.declaration(name, "class", self.span(node), extra=extra)
            if self.language == "cpp":
                self.export(name, False)
        if node.type == "enum_specifier":
            scoped = any(c.type in ("class", "struct") for c in node.children)
            for item in body.named_children:
                if item.type != "enumerator":
                    continue
                enumerator = item.child_by_field_name("name")
                if enumerator is not None and not scoped:
                    self.declaration(self.text(enumerator), "binding", self.span(enumerator))
                self.walk(item.child_by_field_name("value"))
            return
        if self.language == "c":
            for field in body.named_children:  # C tags declared inside a struct are file-scope tags
                if field.type == "field_declaration":
                    self.record(field.child_by_field_name("type"))
            return
        based = any(c.type == "base_class_clause" for c in node.children)
        previous = self.enter("class", node, declaration=identity,
                              blocked="base class members are not read" if based else None)
        for member in body.named_children:
            self.walk(member, create_block=False)
        self.leave(previous)

    def namespace(self, node):
        name_node = node.child_by_field_name("name")
        identity = None
        if name_node is not None:
            name = ".".join(self.text(name_node).replace("::", " ").split())
            identity = self.declaration(name, "class", self.span(node), extra={"lexical": False})
        previous = self.enter("block", node, declaration=identity)
        body = node.child_by_field_name("body")
        for child in body.named_children if body is not None else ():
            self.walk(child, create_block=False)
        self.leave(previous)

    def using(self, node):
        if any(c.type == "namespace" for c in node.children):
            self.block("using-directive brings names that are not read")
            return
        target = next((c for c in node.named_children if c.type in ("qualified_identifier", "identifier")), None)
        name = c_name_node(target)
        if target is not None and name is not None:
            self.data["imports"].append({
                "scope": self.scope, "local": self.text(name), "module": self.text(target),
                "imported": self.text(name), "mode": "named", "span": self.span(name)})

    def include(self, node):
        path = node.child_by_field_name("path")
        if path is None or path.type not in ("system_lib_string", "string_literal"):
            self.note("include through a macro is not read")
            return
        module = self.text(path) if path.type == "system_lib_string" else self.text(path)[1:-1]
        self.data["imports"].append({"scope": "module", "local": "*", "module": module, "imported": "*",
                                     "mode": "namespace", "span": self.span(path)})

    # -- expressions -----------------------------------------------------------------------------------------

    def call(self, node):
        function = node.child_by_field_name("function")
        arguments = node.child_by_field_name("arguments")
        if function is None:
            self.walk(arguments)
            return
        if function.type in ("primitive_type", "sized_type_specifier", "type_descriptor") or (
                function.type == "template_function"
                and self.text(function.child_by_field_name("name")) in _C_CASTS):
            self.walk(arguments)  # `int(x)`, `static_cast<T>(x)`: a conversion, not a call
            return
        target, dynamic = function, False
        while target is not None and target.type in ("parenthesized_expression", "pointer_expression"):
            if target.type == "pointer_expression":
                operator = target.child_by_field_name("operator")
                if operator is None or operator.type != "*":
                    break
                target = target.child_by_field_name("argument")
            else:
                target = target.named_children[0] if target.named_children else None
            dynamic = True
        parts = self.parts(target)
        reason = "dynamic-callee" if dynamic or (len(parts) == 1 and parts[0] in self.macros) else None
        if not parts:
            member = self.member_name(target) if target is not None else None
            if member is not None:
                parts = ["(expr)", self.text(member)]
                self.walk(target.child_by_field_name("argument"))
            elif target is not None:
                self.walk(target)
            reason = "dynamic-callee"
        self.reference(parts, "call", self.callee_span(target if target is not None else function, parts), reason)
        self.walk(arguments)

    def new(self, node):
        kind = node.child_by_field_name("type")
        if kind is not None and kind.type not in ("primitive_type", "sized_type_specifier",
                                                  "placeholder_type_specifier"):
            parts = self.parts(kind)
            self.reference(parts, "call", self.callee_span(kind, parts), None if parts else "dynamic-callee")
        for field in ("placement", "declarator", "arguments"):
            self.walk(node.child_by_field_name(field))

    def lambda_(self, node):
        self.walk(node.child_by_field_name("captures"))
        identity = self.declaration("(lambda)", "function", self.span(node), extra={"lexical": False})
        previous = self.enter("function", node, caller=identity)
        declarator = node.child_by_field_name("declarator")
        self.bind_parameters(declarator.child_by_field_name("parameters") if declarator is not None else None)
        self.walk(node.child_by_field_name("body"), create_block=False)
        self.leave(previous)

    def range_for(self, node):
        self.walk(node.child_by_field_name("right"))
        previous = self.enter("block", node)
        declarator = node.child_by_field_name("declarator")
        names = declarator.named_children if declarator is not None and \
            declarator.type == "structured_binding_declarator" else [c_declarator(declarator)[0]]
        for name in names:
            if name is not None and name.type == "identifier":
                self.declaration(self.text(name), "binding", self.span(name))
        self.walk(node.child_by_field_name("body"), create_block=False)
        self.leave(previous)

    def catch(self, node):
        previous = self.enter("block", node)
        self.bind_parameters(node.child_by_field_name("parameters"))
        self.walk(node.child_by_field_name("body"), create_block=False)
        self.leave(previous)

    def walk(self, node, create_block=True):
        if node is None or node.type in _TS_SKIP_NODES or node.type in _C_SKIP:
            return
        t = node.type
        if t == "preproc_include":
            self.include(node)
        elif t.startswith("preproc_"):  # `#if` and its branches: every branch is read, the tests never are
            for index, child in enumerate(node.children):
                if child.is_named and node.field_name_for_child(index) not in _C_CONDITIONS:
                    self.walk(child, create_block)
        elif t == "function_definition":
            self.function(node)
        elif t in ("declaration", "field_declaration"):
            self.declaration_node(node)
        elif t == "type_definition":
            self.type_definition(node)
        elif t == "alias_declaration":
            name = node.child_by_field_name("name")
            if name is not None:
                self.declaration(self.text(name), "class", self.span(node), extra={"name_span": self.span(name)})
                self.export(self.text(name), False)
        elif t in _C_RECORDS:
            self.record(node)
        elif t == "namespace_definition":
            self.namespace(node)
        elif t == "using_declaration":
            self.using(node)
        elif t in ("linkage_specification", "template_declaration", "declaration_list", "translation_unit",
                   "template_instantiation"):
            for child in node.named_children:
                if child.type not in ("string_literal", "template_parameter_list"):
                    self.walk(child, create_block=False)
        elif t == "compound_statement":
            previous = self.enter("block", node) if create_block else None
            for child in node.named_children:
                self.walk(child)
            if previous is not None:
                self.leave(previous)
        elif t == "call_expression":
            self.call(node)
        elif t == "new_expression":
            self.new(node)
        elif t == "lambda_expression":
            self.lambda_(node)
        elif t == "for_range_loop":
            self.range_for(node)
        elif t == "catch_clause":
            self.catch(node)
        elif t in ("cast_expression", "sizeof_expression", "compound_literal_expression", "alignof_expression"):
            self.walk(node.child_by_field_name("value"))
        elif t in ("qualified_identifier", "template_function"):
            parts = self.parts(node)
            if parts:
                self.reference(parts, "read", self.callee_span(node, parts))
        elif t == "field_expression":
            parts = self.parts(node)
            if parts:
                self.reference(parts, "read", self.span(node))
            else:
                self.walk(node.child_by_field_name("argument"))
        else:
            super().walk(node, create_block)
