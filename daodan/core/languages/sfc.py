"""
Single-File Component (Vue `.vue`, Svelte `.svelte` and Astro `.astro`) adapter.

Masks everything outside `<script ...>...</script>` blocks, and an Astro file's frontmatter, with spaces while
preserving exact UTF-8 byte offsets and line numbers, then delegates script
parsing to the TypeScript or JavaScript adapter so `ParseResult.semantic` spans
align 1:1 with the original `.vue` or `.svelte` file on disk. The rules of the
`<style>` blocks are added beside the script's symbols (`markup.style_symbols`).

The template is read with the framework's own grammar (tree-sitter-language-pack's `vue` and `svelte`), and each
expression node it gives with the script's grammar, alone, at its own position (`template_semantics`): its calls
and reads are references of a template scope under the module's; a handler that is a name or a member path
(`@click="inc"`, `on:click={f}`, `onclick={f}`) is a call of it, as the framework calls it on the event (Vue,
"Method vs. Inline Detection"); a snippet rendered is a call of the snippet. The names a template introduces (a
v-for alias, a slot's props, an each block's context and index, a snippet and its parameters, `let:`, `@const`,
an await block's value and error) are declared in the scope of their element or block. An assignment in a
handler writes the script's binding, as one in the script does.

An Astro file's script is its frontmatter, the code between a `---` fence before any element and the next one
(withastro/compiler `internal/token.go`: "If we see an element before "---", ignore any future "---""), and its
`<script>` blocks, all TypeScript ("The Astro component script is TypeScript", docs.astro.build, Astro
components); they are read as one module. Its template is not read: the product has no reader of it, which its
notes say.
"""

from __future__ import annotations

import re

from .base import ParseResult
from .comments import CommentToken, extract_c_style_comments
from .semantic import _JavaScriptEvidence

__all__ = ["vue_adapter", "svelte_adapter", "astro_adapter", "mask_non_script"]

_SCRIPT_BLOCK_RE = re.compile(
    rb"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_TS_ATTR_RE = re.compile(
    rb"""\blang\s*=\s*['"]?(?:ts|tsx|typescript)\b""",
    re.IGNORECASE,
)
# Astro's frontmatter: a fence that only blanks precede, to the next fence opening a line.
_FRONTMATTER_RE = re.compile(rb"\A\s*---(?P<body>.*?)^[ \t]*---", re.DOTALL | re.MULTILINE)


def mask_non_script(content: str, frontmatter: bool = False) -> tuple[str, bool, bool]:
    """Return `(masked_source, is_typescript, has_script)` with identical byte offsets per line; `frontmatter`
    keeps an Astro frontmatter's code too, and every script of such a file is TypeScript."""
    raw = content.encode("utf-8")
    masked = bytearray(len(raw))
    for i, b in enumerate(raw):
        masked[i] = b if b in (0x0A, 0x0D) else 0x20

    is_ts = False
    has_script = False
    for match in _SCRIPT_BLOCK_RE.finditer(raw):
        has_script = True
        if _TS_ATTR_RE.search(match.group("attrs") or b""):
            is_ts = True
        start, end = match.span("body")
        masked[start:end] = raw[start:end]
    fence = _FRONTMATTER_RE.match(raw) if frontmatter else None
    if fence:
        has_script = True
        start, end = fence.span("body")
        masked[start:end] = raw[start:end]

    return masked.decode("utf-8", errors="replace"), is_ts or frontmatter, has_script


def _flat(node) -> list:
    """The elements of a comma sequence, which the grammar nests."""
    if node.type != "sequence_expression":
        return [node]
    return [item for child in node.named_children for item in _flat(child)]


def _child(node, *types):
    return None if node is None else next((child for child in node.children if child.type in types), None)


class _Template(_JavaScriptEvidence):
    """The expressions of one template, each parsed alone in the script's language (`parse`), the spans those of
    the file: a buffer's first line sits where its expression starts, less the statement's prefix."""

    def __init__(self, script_language: str, grammar, expressions, markup: bytes, script: dict):
        super().__init__(b"", script_language)
        self.grammar, self.expressions, self.markup = grammar, expressions, markup
        self.base = (0, 0)  # where the markup being read starts in the file (a quoted value read again)
        self.at = (0, 0)
        self.script = script
        self.scope = self.new_scope("template", [1, 0, 1, 0])

    def span(self, node):
        (r0, c0), (r1, c1) = node.start_point, node.end_point
        row, column = self.at
        return [row + r0 + 1, c0 + column if r0 == 0 else c0, row + r1 + 1, c1 + column if r1 == 0 else c1]

    def place(self, node) -> tuple[int, int]:
        """A markup node's start in the file."""
        row, column = node.start_point
        return self.base[0] + row, (self.base[1] + column) if row == 0 else column

    def markup_span(self, node, skip: int = 0) -> list[int]:
        row, column = self.place(node)
        end_row, end_column = node.end_point
        end = (self.base[0] + end_row, (self.base[1] + end_column) if end_row == 0 else end_column)
        return [row + 1, column + skip, end[0] + 1, end[1]]

    def name(self, node) -> str:
        return "" if node is None else self.markup[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def parse(self, node, prefix: bytes, suffix: bytes):
        """The statement `prefix`, the markup `node`'s text, `suffix`; None when it does not parse."""
        text = self.markup[node.start_byte:node.end_byte]
        if not text.strip():
            return None
        row, column = self.place(node)
        self.src, self.at = prefix + text + suffix, (row, column - len(prefix))
        tree = self.expressions.parse(self.src)
        if tree.root_node.has_error or not tree.root_node.named_children:
            self.note(f"template expression not read at {row + 1}:{column}: a syntax error")
            return None
        return tree.root_node.named_children[0]

    def value(self, node):
        """The expression of a statement `(expression);`."""
        statement = self.parse(node, b"(", b");")
        if statement is None or statement.type != "expression_statement":
            return None
        inner = statement.named_children[0] if statement.named_children else None
        return inner.named_children[0] if inner is not None and inner.named_children else None

    def expression(self, node, handler: bool = False) -> None:
        found = self.value(node)
        parts = self.parts(found) if found is not None and found.type in ("identifier", "member_expression") else []
        if handler and parts:
            self.reference(parts, "call", self.span(found))
        else:
            self.walk(found)

    def names(self, node, scope: str) -> None:
        """Declare in `scope` the names of a pattern written as an expression (a v-for alias, an each context)."""
        if node is None:
            return
        if node.type in ("parenthesized_expression", "sequence_expression", "object", "array"):
            for child in node.named_children:
                self.names(child, scope)
        elif node.type in ("identifier", "shorthand_property_identifier"):
            self.declaration(self.text(node), "binding", self.span(node), scope)
        elif node.type == "pair":
            self.names(node.child_by_field_name("value"), scope)
        elif node.type == "spread_element" and node.named_children:
            self.names(node.named_children[0], scope)
        elif node.type == "assignment_expression":  # a default value
            self.names(node.child_by_field_name("left"), scope)
            self.walk(node.child_by_field_name("right"))
        else:
            self.binding(node, "binding", scope)

    def parameters(self, node, scope: str) -> None:
        """Declare in `scope` the parameters `node` lists, as a function's (`(...) => 0`)."""
        statement = self.parse(node, b"(", b") => 0;")
        arrow = statement.named_children[0] if statement is not None and statement.named_children else None
        if arrow is not None and arrow.type == "arrow_function":
            self.binding(arrow.child_by_field_name("parameters"), "parameter", scope)

    def child_scope(self, node, kind: str = "block") -> str:
        return self.new_scope(kind, self.markup_span(node))

    # Vue: interpolations and directives (vuejs.org/guide/essentials/template-syntax).

    def vue(self, node, top: bool = False) -> None:
        for child in node.children:
            if child.type in ("script_element", "style_element", "start_tag", "self_closing_tag", "end_tag"):
                continue
            if child.type == "interpolation":
                raw = _child(child, "raw_text")
                if raw is not None:
                    self.expression(raw)
            elif child.type in ("element", "template_element"):
                self.vue_element(child, top)
            else:
                self.vue(child)

    def vue_element(self, node, top: bool = False) -> None:
        tag = _child(node, "start_tag", "self_closing_tag")
        attributes = [] if tag is None else [child for child in tag.children
                                             if child.type in ("directive_attribute", "attribute")]
        if top and node.type == "template_element":  # the root template in another language (Pug) is not read
            lang = next((self.name(_child(_child(a, "quoted_attribute_value"), "attribute_value")) for a in attributes
                         if a.type == "attribute" and _child(a, "quoted_attribute_value") is not None
                         and self.name(_child(a, "attribute_name")) == "lang"), "html")
            if lang != "html":
                self.note(f"template not read: lang={lang}")
                return
        outer = scope = self.scope
        directives = [(self.directive(a), a) for a in attributes]
        for (name, value, _dynamic), _attribute in directives:
            if name == "v-for" and value is not None:
                scope = self.child_scope(node)
                statement = self.parse(value, b"for (", b");")
                if statement is not None and statement.type == "for_in_statement":
                    self.walk(statement.child_by_field_name("right"))
                    self.names(statement.child_by_field_name("left"), scope)
        self.scope, slot = scope, None
        for (name, value, dynamic), _attribute in directives:
            if dynamic is not None:
                self.expression(dynamic)
            if value is None or name in ("v-for", None):
                continue
            if name in ("v-slot", "slot-scope"):
                slot = slot or self.child_scope(node)
                self.parameters(value, slot)
            else:
                self.expression(value, handler=name == "v-on")
        self.scope = slot or scope
        self.vue(node)
        self.scope = outer

    def directive(self, node):
        """`(directive, value node, dynamic argument node)`; the directive `slot-scope` for that attribute, None for
        another plain attribute."""
        quoted = _child(node, "quoted_attribute_value")
        value = _child(quoted, "attribute_value") if quoted is not None else _child(node, "attribute_value")
        if node.type == "attribute":
            named = _child(node, "attribute_name")
            return ("slot-scope" if named is not None and self.name(named) == "slot-scope" else None), value, None
        named = _child(node, "directive_name")
        shorthand = {"@": "v-on", ":": "v-bind", "#": "v-slot", ".": "v-bind"}
        name = self.name(named) if named is not None else next(
            (shorthand[child.type] for child in node.children if child.type in shorthand), None)
        dynamic = _child(node, "dynamic_directive_value")
        return name, value, _child(dynamic, "dynamic_directive_inner_value") if dynamic is not None else None

    # Svelte: tags, blocks and attributes (svelte.dev/docs/svelte/basic-markup, .../each, .../snippet).

    def svelte(self, node) -> None:
        for child in node.children:
            self.svelte_node(child)

    def svelte_node(self, node) -> None:
        t = node.type
        if t in ("script_element", "style_element", "start_tag", "self_closing_tag", "end_tag"):
            return
        raw = _child(node, "raw_text_expr")
        if t == "element":
            self.svelte_element(node)
        elif t in ("expression", "if_start_expr", "else_if_expr", "key_start_expr", "html_expr", "debug_expr"):
            if raw is not None:
                self.expression(raw)
        elif t == "const_expr" and raw is not None:
            statement = self.parse(raw, b"const ", b";")
            if statement is not None:
                self.walk(statement)
        elif t == "render_expr":
            name = _child(node, "snippet_name")
            if name is not None:
                self.reference([self.name(name)], "call", self.markup_span(name))
            if raw is not None:
                self.expression(raw)
        elif t == "each_statement":
            self.svelte_each(node)
        elif t == "await_statement":
            self.svelte_await(node)
        elif t == "snippet_statement":
            head = _child(node, "snippet_start_expr")
            name = _child(head, "snippet_name") if head is not None else None
            if name is not None:
                self.declaration(self.name(name), "function", self.markup_span(name))
            outer, self.scope = self.scope, self.child_scope(node, "function")
            params = _child(head, "raw_text_expr") if head is not None else None
            if params is not None:
                self.parameters(params, self.scope)
            for child in node.children:
                if child is not head:
                    self.svelte_node(child)
            self.scope = outer
        else:
            self.svelte(node)

    def svelte_each(self, node) -> None:
        head = _child(node, "each_start_expr")
        iterable, context = (_child(head, "raw_text_each"), _child(head, "raw_text_expr")) if head else (None, None)
        if iterable is not None:
            self.expression(iterable)
        outer, self.scope = self.scope, self.child_scope(node)
        found = self.value(context) if context is not None else None
        if found is not None:
            items, key = _flat(found), None
            if items[-1].type == "call_expression":  # the key, in parentheses after the context or the index
                items, key = [*items[:-1], items[-1].child_by_field_name("function")], \
                    items[-1].child_by_field_name("arguments")
            for item in items:
                self.names(item, self.scope)
            self.walk(key)
        for child in node.children:
            if child is head:
                continue
            if child.type == "else_each_statement":
                self.scope = outer
            self.svelte_node(child)
        self.scope = outer

    def svelte_await(self, node) -> None:
        head = _child(node, "await_start_expr")
        awaited = _child(head, "raw_text_await") if head is not None else None
        value = _child(head, "raw_text_expr") if head is not None else None
        outer = self.scope
        if awaited is None:
            awaited, value = value, None
        if awaited is not None:
            self.expression(awaited)
        if value is not None:  # `{#await p then value}`: the value of what follows
            self.scope = self.child_scope(node)
            self.parameters(value, self.scope)
        for child in node.children:
            if child is head:
                continue
            if child.type in ("then_statement", "catch_statement"):
                branch = _child(child, "then_expr", "catch_expr")
                self.scope = self.child_scope(child)
                bound = _child(branch, "raw_text_expr") if branch is not None else None
                if bound is not None:
                    self.parameters(bound, self.scope)
                for item in child.children:
                    if item is not branch:
                        self.svelte_node(item)
                self.scope = outer
            else:
                self.svelte_node(child)
        self.scope = outer

    def svelte_element(self, node) -> None:
        tag = _child(node, "start_tag", "self_closing_tag")
        outer, inner = self.scope, None
        for attribute in [] if tag is None else [child for child in tag.children if child.type == "attribute"]:
            named = _child(attribute, "attribute_name")
            name = self.name(named) if named is not None else ""
            given = _child(attribute, "expr_attribute_value")
            expression = _child(_child(given, "expression"), "raw_text_expr") if given is not None else None
            spread = _child(named, "raw_text_expr") if named is not None else None  # `{...rest}`, `{name}`
            quoted = _child(_child(attribute, "quoted_attribute_value"), "attribute_value")
            if name.startswith("let:"):
                inner = inner or self.child_scope(node)
                if expression is not None:
                    self.names(self.value(expression), inner)
                else:
                    self.declaration(name[4:], "binding", self.markup_span(named, 4), inner)
            elif expression is not None:
                self.expression(expression, handler=name.startswith("on"))
            elif spread is not None:  # `[...rest]` reads what `{...rest}` spreads, `[name]` what `{name}` passes
                self.walk(self.parse(spread, b"[", b"];"))
            elif quoted is not None and b"{" in self.markup[quoted.start_byte:quoted.end_byte]:
                self.fragment(quoted)
        self.scope = inner or outer
        self.svelte(node)
        self.scope = outer

    def fragment(self, node) -> None:
        """A quoted attribute value holding `{expression}` parts, read as markup of its own."""
        markup, base = self.markup, self.base
        text = markup[node.start_byte:node.end_byte]
        self.base, self.markup = self.place(node), text
        self.svelte(self.grammar.parse(text).root_node)
        self.markup, self.base = markup, base

    def settle(self) -> None:
        """Into the script's payload: each write moved to the scope that binds its name, as `extract` does, then the
        template's scopes, declarations, references and notes."""
        script, written = self.script, {id(item) for item in self.writes}
        bindings = {(item["scope"], item["name"]) for item in [*script["declarations"], *self.data["declarations"]]
                    if id(item) not in written and item.get("lexical") is not False}
        bindings.update((item["scope"], item["local"]) for item in script["imports"])
        for item in self.writes:
            scope = item["scope"]
            while (scope, item["name"]) not in bindings and scope != "module":
                scope = self.scope_by_id[scope]["parent"]
            item["scope"], item["qualified_name"] = scope, self.qualified(item["name"], scope)
        script["scopes"] += self.data["scopes"][1:]
        for key in ("declarations", "references"):
            script[key] = sorted([*script[key], *self.data[key]], key=lambda item: (item["span"], item.get("kind", "")))
        script["notes"] = list(dict.fromkeys([*script.get("notes", []), *self.data["notes"]]))


def template_semantics(content: str, language: str, is_ts: bool, payload: dict) -> str | None:
    """Add a component's template to its script's semantic `payload` (see the module); the reason it is not read,
    or None."""
    from . import _treesitter
    markup, expressions = _treesitter.get_parser(language), _treesitter.get_parser("typescript" if is_ts else
                                                                                    "javascript")
    if markup is None or expressions is None:
        missing = language if markup is None else ("typescript" if is_ts else "javascript")
        return f"template not read: no {missing} grammar ({_treesitter.load_failure(missing) or 'not installed'})"
    source = content.encode("utf-8")
    reader = _Template("typescript" if is_ts else "javascript", markup[0], expressions[0], source, payload)
    root = markup[0].parse(source).root_node
    if language == "vue":
        reader.vue(root, top=True)
    else:
        reader.svelte(root)
    reader.settle()
    return None


class _SfcAdapter:
    def __init__(self, language: str, frontmatter: bool = False) -> None:
        self.language, self.frontmatter = language, frontmatter

    def parse(self, content: str, file_path: str) -> ParseResult:
        from .markup import style_symbols

        result = self._script(content, file_path)
        style_symbols(content, result)
        return result

    def _script(self, content: str, file_path: str) -> ParseResult:
        from . import javascript as _js
        from . import typescript as _ts

        masked, is_ts, has_script = mask_non_script(content, self.frontmatter)
        if not has_script:
            result = ParseResult(
                file_path=file_path,
                language=self.language,
                notes=[f"parser=sfc-no-script ({self.language})"],
                semantic={
                    "version": 1,
                    "backend": "tree-sitter",
                    "status": "ast",
                    "notes": [],
                    "scopes": [{"id": "module", "parent": None, "kind": "module"}],
                    "declarations": [],
                    "imports": [],
                    "exports": [],
                    "references": [],
                },
            )
        else:
            delegate = _ts.adapter if is_ts else _js.adapter
            virtual_ext = ".ts" if is_ts else ".js"
            result = delegate.parse(masked, file_path + virtual_ext)
            result.file_path = file_path
            result.language = self.language
            result.notes = [f"{n} ({self.language})" for n in result.notes]
        if self.frontmatter:
            result.notes.append(f"template not read: no reader of the {self.language} template in the product")
        elif result.semantic is not None:
            unread = template_semantics(content, self.language, is_ts, result.semantic)
            result.notes += [unread] if unread else []
        return result

    def count_imports(self, content: str) -> int:
        from . import javascript as _js

        masked, _, has_script = mask_non_script(content, self.frontmatter)
        return _js.adapter.count_imports(masked) if has_script else 0

    def extract_comments(self, content: str) -> list[CommentToken]:
        masked, _, has_script = mask_non_script(content, self.frontmatter)
        return extract_c_style_comments(masked) if has_script else []


vue_adapter = _SfcAdapter("vue")
svelte_adapter = _SfcAdapter("svelte")
astro_adapter = _SfcAdapter("astro", frontmatter=True)
