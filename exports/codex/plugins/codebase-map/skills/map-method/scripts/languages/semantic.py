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

    def declaration(self, name, kind, span, scope=None):
        owner_scope = scope or self.scope
        declaration = {"id": self.identity(kind, span), "name": name, "kind": kind,
                       "scope": owner_scope, "span": span,
                       "qualified_name": self.qualified(name, owner_scope)}
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
        identity = self.declaration(node.name, "function", _py_span(node))
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
        identity = self.declaration(node.name, "class", _py_span(node))
        self.header(node, [*node.decorator_list, *node.bases, *[k.value for k in node.keywords]])
        scope = self.new_scope("class", _py_span(node), self.lexical_parent())
        self.scope_by_id[scope]["declaration"] = identity
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
            self.visit(node.value)

    def visit_Call(self, node):
        parts = _py_parts(node.func)
        if parts == ["exec"]:
            scope = self.scope
            while scope is not None:
                self.scope_by_id[scope].update(unresolved=True, reason="exec may introduce or mutate lexical bindings")
                scope = self.scope_by_id[scope]["parent"]
            self.note("exec may introduce or mutate lexical bindings")
        self.reference(parts, "call", _py_span(node.func), None if parts else "dynamic-callee")
        if not parts:
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
        entry = {"scope": self.scope, "local": self.text(local), "module": module,
                 "imported": imported, "mode": mode, "span": self.span(local)}
        if type_only:
            entry["type_only"] = True
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

    def function(self, node, assigned=None, binding_scope=None):
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
        identity = self.declaration(assigned or self.text(name) or "(anonymous)", kind, self.span(node), binding_scope)
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
        if t in ("comment", "string", "regex", "string_fragment", "escape_sequence", "type_annotation",
                 "type_arguments", "type_parameters", "interface_declaration", "type_alias_declaration"):
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
        if t == "function_signature":
            name = node.child_by_field_name("name")
            if name is not None:
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
                identity = self.declaration(self.text(name), "class", self.span(node))
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
                    self.function(value, self.text(name), scope)
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
                self.reference(parts, "call", self.span(function), None if parts else "dynamic-callee")
                if not parts:
                    self.walk(function)
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
