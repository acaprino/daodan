"""CSS: what declares a name in a stylesheet, and every place that uses that name, as the common graph.

A stylesheet has no calls. Its references are names the cascade resolves at run time:
- a class or id written in markup or code (`class`, `className`, `id`, `classList`, `clsx`, `@apply`, `@extend`,
  `composes`) names every rule whose selector names it, and the Tailwind utility of that name (external);
- `var(--x)` names every declaration of `--x` (rules, `@property`, inline styles, `setProperty`, Tailwind
  arbitrary properties); cascade and inheritance pick one per element, so two or more are uncertain arcs that
  carry all the candidates;
- `animation` names `@keyframes`, `font-family` every `@font-face` of the family, `@container` the
  `container-name` declarations, `@layer` the layer's first appearance in its file (that fixes the order);
- `@import`, `@use`, `@forward`, `<link rel=stylesheet>` and a script's `import './x.css'` name a file of the
  project; a URL path (`/assets/x.css`) the checkout files ending with its longest tail (`url-suffix`); a sheet the
  markup loads from outside the snapshot (a package, a vendored file, a CDN link) is read as an external sheet:
  the names it declares are external nodes, made when a reference reaches them, with the package and version its
  path, `package.json`, URL or leading comment states (`unknown` otherwise);
- in a CSS Module `styles.foo` names the module's local `.foo` rules and, through `composes`, the rules of what
  it composes; in Sass `$x`, `ns.$x` and `@include` name variables and mixins through `@use`, `@forward`, `@import`.
A name nothing declares is a hole with its class (`css-in-js` when a script's object literal has a selector key
naming it, `tailwind-named-group` for `group/x` and `peer/x`); a class built at run time (template,
concatenation, a value the TypeScript checker cannot state, a token glued to an EJS tag) is a hole, never a guess.
A stylesheet or markup file no reader here takes is listed in `files.missing` with the reason, never dropped. An arc's `chain` lists the rules that led from
the site to the target (`literal-type`, `initializer`, `clsx`, `classList`, `@apply`, `composes`...).

Three engines, an adapter each. This one: the product's stylesheet parser (`languages/stylesheet.py`, CSS, SCSS,
LESS), every statement it reads observed as it reads it (the parser keeps no `@apply`, `@include` or import
line), and the standard library's HTML parser for HTML and EJS (class, id, style, `<style>`, `<link>`).
`css_typescript.py`: the TypeScript compiler over JS/TS/JSX/TSX. `css_tailwind.py`: the project's Tailwind,
which says which class tokens are its utilities. `run` wires the three; `graph` resolves and assembles.
"""
from __future__ import annotations

import collections
import hashlib
import html.parser
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
from languages import stylesheet  # noqa: E402
from tree_scope import DEPENDENCY_DIRS  # noqa: E402

from . import css_astro, css_less, css_sass, css_stylus, css_svelte, css_tailwind, css_typescript, css_vue  # noqa: E402

STYLESHEETS = (".css", ".scss", ".sass", ".less", ".pcss", ".postcss", ".styl", ".stylus")
MARKUP = (".html", ".htm", ".ejs")
COMPONENTS = {".vue": css_vue, ".svelte": css_svelte, ".astro": css_astro}
# Stylesheet and markup files no reader here takes, and why: listed in `files.missing`, never dropped.
UNREAD = {
          **dict.fromkeys((".erb", ".hbs", ".handlebars", ".mustache", ".njk", ".twig", ".pug", ".jade", ".liquid",
                           ".jinja", ".j2"), "template language: no reader")}
PARTLY: dict[str, str] = {}  # suffix -> what a file of it leaves out of the graph
NAMED_GROUP_RE = re.compile(r"^(?:group|peer)/[\w-]+$")  # Tailwind 3.2+: a variant anchor, never a utility
# A leading comment naming a package and its version: "/*! Font Awesome Free 6.4.0 by ...", "Bootstrap v5.3.0".
BANNER_RE = re.compile(r"^(?:@charset[^;]*;)?\s*/\*!?[\s*]*([A-Za-z@][^\n]*?)\s+v?(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)\b")
VERSIONED_RE = re.compile(r"^(.+?)[-_@]v?(\d+\.\d+(?:\.\d+)?)$")  # a path segment such as "bootstrap-5.3.0"
CDN_RES = ((re.compile(r"^https?://cdn\.jsdelivr\.net/npm/((?:@[^/@]+/)?[^/@]+)@([^/]+)/"), "npm"),
           (re.compile(r"^https?://unpkg\.com/((?:@[^/@]+/)?[^/@]+)@([^/]+)/"), "npm"),
           (re.compile(r"^https?://cdnjs\.cloudflare\.com/ajax/libs/([^/]+)/([^/]+)/"), "cdnjs"))
MODULE_RE = re.compile(r"\.module\.(?:css|scss|sass|less|styl|pcss)$", re.I)
# `@value brand: #0af;` and `@value brand, accent as a from "./colors.module.css";` (CSS Modules values).
VALUE_RE = re.compile(r"^\s*(?P<names>[^:]+?)\s+from\s+(['\"])(?P<origin>[^'\"]+)\2\s*$|^\s*(?P<name>[\w-]+)\s*:")
CUSTOM_SELECTOR_RE = re.compile(r":--[\w-]+")
CSS_WIDE = {"inherit", "initial", "unset", "revert", "revert-layer", "none"}
# Keywords the `animation` shorthand gives its other longhands (CSS Animations 1, 2): never a keyframes name.
ANIMATION_WORDS = {"linear", "ease", "ease-in", "ease-out", "ease-in-out", "step-start", "step-end", "infinite",
                   "normal", "reverse", "alternate", "alternate-reverse", "forwards", "backwards", "both",
                   "running", "paused", "auto", "replace", "add", "accumulate"}
GENERIC_FONTS = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif",
                 "ui-monospace", "ui-rounded", "emoji", "math", "fangsong"} | CSS_WIDE
SYSTEM_FONTS = {"caption", "icon", "menu", "message-box", "small-caption", "status-bar"}
TAILWIND_LAYERS = {"v3": {"base", "components", "utilities"}, "v4": {"theme", "base", "components", "utilities"}}
IDENT = re.compile(r"-?[A-Za-z_][\w-]*$")
VAR_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,\s*([^)]*))?")
SASS_REF_RE = re.compile(r"(?:\b([A-Za-z_][\w-]*)\.)?\$([A-Za-z_][\w-]*)")
# `:global` and `:local` of CSS Modules; Vue's `:deep()`, `::v-deep` and `:slotted()` reach past the component.
MODE_RE = re.compile(r"::?(global|local|deep|slotted|v-deep)\b(\()?|(\()|(\))")
SVELTE_GLOBAL_RE = re.compile(r":global\(([^()]*)\)([^\s>+~,()]+)")
VBIND_RE = re.compile(r"v-bind\(\s*(['\"]?)([^)'\"]+?)\1\s*\)")
WORD_RE = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s(]+(?:\([^)]*\))?|\([^)]*\)")
SIZE_RE = re.compile(r"(?:^|\s)(?:[+-]?[\d.]+[a-z%]*|xx-small|x-small|small|medium|large|x-large|xx-large|"
                     r"xxx-large|smaller|larger)(?:\s*/\s*[^\s,]+)?\s+(?=\S)", re.I)
EJS_RE = re.compile(r"<%.*?%>", re.S)
TAG_RE = re.compile(r"<%.*?%>|\{\{.*?\}\}|\{%.*?%\}", re.S)  # EJS, and `{{ }}` / `{% %}` of Liquid and its kin
# An EJS include: `<%- include('partials/head', {...}) %>` or the old `<% include partials/head %>`.
CUSTOM_MEDIA_RE = re.compile(r"\(\s*(--[\w-]+)\s*\)")
SCOPE_RE = re.compile(r"^@scope\s*(?:\((?P<root>[^)]*)\))?\s*(?:to\s*\((?P<limit>[^)]*)\))?", re.I)
INCLUDE_RE = re.compile(r"<%[-=_]?\s*include\s*(?:\(\s*(['\"])(?P<call>[^'\"]+)\1|(?P<bare>[\w./-]+))")
SCRIPT_SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro")
# Arcs whose target styles a page only where the page loads its sheet (compile-time ones excluded).
LOADED_KINDS = {"class", "id", "custom-property", "keyframes", "font-face", "container"}
COMPILE_TIME = {"@apply", "@extend", ":extend", "composes", "safelist", "@source inline"}
PLACEHOLDER_RE = re.compile(r"%([A-Za-z_][\w-]*)")
# A class or id with one compile-time interpolation in it: `.size-#{$x}`, `.@{name}-x`, `.{$x}-y`.
INTERPOLATED_RE = re.compile(r"([.#])([\w-]*)(?:#\{[^}]*\}|@\{[^}]*\}|\{[^}]*\})([\w-]*)")
INTERPOLATION_RE = re.compile(r"#\{\s*(?:[\w-]+\.)?(\$[\w-]+)\s*\}")
LESS_INTERPOLATION_RE = re.compile(r"@\{([\w-]+)\}")
STYLUS_INTERPOLATION_RE = re.compile(r"\{([\w$-]+)\}")
CALLABLE_RE = re.compile(r"^[.#][\w-]+$")  # a Less ruleset a mixin call can name


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def walk(project_dir: Path) -> list[str]:
    """The project's stylesheet, markup and script files, outside dot and dependency directories (the snapshot's
    perimeter, `tree_scope.DEPENDENCY_DIRS`); the ones no reader takes included, to be listed as missing."""
    suffixes = STYLESHEETS + MARKUP + tuple(COMPONENTS) + css_typescript.SUFFIXES + tuple(UNREAD)
    return sorted(path.relative_to(project_dir).as_posix() for path in Path(project_dir).rglob("*")
                  if path.is_file() and path.suffix.lower() in suffixes
                  and not any(part in DEPENDENCY_DIRS or part.startswith(".")
                              for part in path.relative_to(project_dir).parts))


def run(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The three adapters over a project, then the graph."""
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    files = walk(project_dir) if files is None else files
    own = index(project_dir, work_dir, files)
    sass = sass_sheets(project_dir, work_dir, files)
    less = less_sheets(project_dir, work_dir, files)
    stylus = engine_sheets(css_stylus, "stylus", project_dir, work_dir, files)
    components = component_files(project_dir, work_dir, files)
    script_files = [rel for rel in files if rel.lower().endswith(css_typescript.SUFFIXES)]
    scripts = css_typescript.index(project_dir, work_dir, script_files) if script_files else \
        {"indexer": None, "records": [], "missing": {}}
    records = (own["records"] + sass["records"] + less["records"] + stylus["records"] + components["records"] +
               scripts["records"])
    entries = sorted({r["file"] for r in records if r["t"] == "ref" and r["kind"] == "import"
                      and r["name"] == "tailwindcss" and r["file"].lower().endswith(STYLESHEETS)})
    tailwind = css_tailwind.index(project_dir, work_dir, sorted(class_tokens(records)), entries)
    engines = [engine for engine in (own["indexer"], sass["indexer"], less["indexer"], stylus["indexer"],
                                     *components["indexers"], scripts["indexer"], tailwind["indexer"]) if engine]
    return graph(project_dir, records, tailwind, files, engines,
                 {**own["missing"], **sass["missing"], **less["missing"], **stylus["missing"],
                  **components["missing"], **scripts["missing"]})


def component_files(project_dir: Path, work_dir: Path, files: list[str]) -> dict:
    """Vue, Svelte and Astro files through their own compilers: their style blocks read by the reader of each block's
    dialect (scoped to the component, or a CSS Module of it), their class and id sites, `$style.x` members, `v-bind()`
    to the script binding it reads, and the scoped rules of a Vue parent on its child's root element."""
    records, missing, indexers, found = [], {}, [], {}
    for suffix, engine in COMPONENTS.items():
        items = [{"key": rel, "path": str(Path(project_dir) / rel)} for rel in files if rel.lower().endswith(suffix)]
        result = engine.index(work_dir, items)
        indexers.append(result["indexer"])
        for item in items:
            data = result["components"].get(item["key"], {"error": "not parsed"})
            if "error" in data:
                missing[item["key"]] = f"not parsed: {data['error']}"[:200]
            else:
                found[item["key"]] = data
    sass_items, less_items, stylus_items, owners = [], [], [], {}
    for rel, data in found.items():
        records.append({"t": "file", "file": rel})
        for index_, block in enumerate(data["blocks"]):
            scope = (f"{rel}?module" if block["module"] == "$style" else f"{rel}?module={block['module']}") \
                if block.get("module") else f"scoped:{rel}" if block.get("scoped") else None
            offset, lang = block["line"] - 1, block["lang"]
            key = f"{rel}#{index_}"
            owners[key] = (rel, offset, scope)
            if lang in ("scss", "sass"):
                sass_items.append({"key": key, "text": block["text"], "syntax": lang})
            elif lang == "less":
                less_items.append({"key": key, "text": block["text"]})
            elif lang in ("stylus", "styl"):
                stylus_items.append({"key": key, "text": block["text"]})
            elif lang in ("css", "postcss", "pcss"):
                records += _sheet(rel, block["text"], "css", offset=offset, scope=scope)
            else:
                missing[rel] = f"partly read: a style block in {lang} at line {block['line']} has no reader"
            for name in block.get("vars") or ():
                records.append(_node(f"{rel}:{block['line']} --{name}", "custom-property", rel, block["line"],
                                     [("custom-property", f"--{name}")]))
            bindings = {b["name"]: b["line"] for b in data.get("bindings", ())}
            for match in VBIND_RE.finditer(block["text"]):
                name = match.group(2).strip()
                line = offset + block["text"][:match.start()].count("\n") + 1
                if name in bindings:
                    target = f"{rel}:{bindings[name]} {name}"
                    records.append(_node(target, "script-binding", rel, bindings[name]))
                    records.append(_ref("v-bind", name, name, rel, line, rel, to=target))
                else:
                    records.append({"t": "hole", "file": rel, "line": line, "kind": "v-bind", "cls": "undeclared",
                                    "name": name})
        for site in data.get("styles", ()):
            records += _sheet(rel, "x{" + site["text"] + "}", "css", offset=site["line"] - 1, inline=True)
        own = [[f"scoped:{rel}", []]]
        for site in data["classes"]:
            records.append({"t": "classes", "kind": site["kind"], "file": rel, "line": site["line"], "from": rel,
                            "chain": site["chain"], "alts": site["alts"], "scopes": own,
                            "root": site["line"] in data.get("roots", ())})
        for member in data.get("members", ()):
            scope = f"{rel}?module" if member["scope"] == "$style" else f"{rel}?module={member['scope']}"
            records.append({"t": "member", "file": rel, "line": member["line"], "spec": None, "name": member["name"],
                            "scope": scope})
        for item in data.get("imports", ()):
            if re.search(r"\.(css|scss|sass|less|styl|stylus|pcss|postcss)(\?.*)?$", item["spec"], re.I):
                records.append({"t": "import", "file": rel, "line": item["line"], "spec": item["spec"]})
            else:
                records.append({"t": "module", "file": rel, "line": item["line"], "spec": item["spec"], "to": None})
    # A Vue parent's scoped rules style the root element of each child component its template renders, and its
    # `:deep()` names reach every element of the components below it.
    snapshot_files = set(files)
    children = collections.defaultdict(set)
    for parent, data in found.items():
        if not parent.endswith(".vue"):
            continue
        rendered = set(data.get("components", ()))
        for item in data.get("imports", ()):
            for name in set(item["names"]) & rendered:
                child = _component_file(project_dir, parent, item["spec"], name, snapshot_files)
                if child and child.endswith(".vue"):
                    children[parent].add(child)
    parents_of = collections.defaultdict(set)
    for parent, kids in children.items():
        for child in kids:
            parents_of[child].add(parent)
    for record in records:
        if record["t"] != "classes" or not record["file"].endswith(".vue"):
            continue
        ancestors, queue = set(), [record["file"]]
        while queue:
            current = queue.pop()
            for parent in parents_of[current] - ancestors:
                ancestors.add(parent)
                queue.append(parent)
        record["scopes"] = [*record["scopes"], *([f"deep:{f}", []] for f in sorted(ancestors | {record["file"]}))]
        if record.get("root"):
            record["scopes"] += [[f"scoped:{parent}", ["child-root"]] for parent in sorted(parents_of[record["file"]])]
    for engine, items in ((css_sass, sass_items), (css_less, less_items), (css_stylus, stylus_items)):
        parsed = engine.index(work_dir, items)
        if items:
            indexers.append(parsed["indexer"])
        for item in items:
            rel, offset, scope = owners[item["key"]]
            sheet = parsed["sheets"].get(item["key"], {"error": "not parsed"})
            if "error" in sheet:
                missing[rel] = f"partly read: a style block is not parsed: {sheet['error']}"[:200]
                continue
            dialect = {css_less: "less", css_stylus: "stylus"}.get(engine, "scss")
            records += tree_records(rel, sheet["tree"], dialect, offset=offset, module=scope)
    return {"records": records, "missing": missing, "indexers": indexers}


def less_sheets(project_dir: Path, work_dir: Path, files: list[str]) -> dict:
    """The Less files through Less's own parser (`css_less`), as records."""
    return engine_sheets(css_less, "less", project_dir, work_dir, files)


def engine_sheets(engine, dialect: str, project_dir: Path, work_dir: Path, files: list[str]) -> dict:
    """The files of one dialect through its own parser, as records."""
    items = [{"key": rel, "path": str(Path(project_dir) / rel)} for rel in files
             if rel.lower().endswith(engine.SUFFIXES)]
    parsed = engine.index(work_dir, items)
    records, missing = [], {}
    for item in items:
        rel, sheet = item["key"], parsed["sheets"].get(item["key"], {"error": "not parsed"})
        if "error" in sheet:
            missing[rel] = f"not parsed: {sheet['error']}"[:200]
            continue
        records += tree_records(rel, sheet["tree"], dialect, module=rel if MODULE_RE.search(rel) else None)
        records.append({"t": "file", "file": rel})
    return {"indexer": parsed["indexer"], "records": records, "missing": missing}


def sass_sheets(project_dir: Path, work_dir: Path, files: list[str]) -> dict:
    """The SCSS and indented Sass files through the official Sass parser (`css_sass`), as records."""
    items = [{"key": rel, "path": str(Path(project_dir) / rel), "syntax": "sass" if rel.lower().endswith(".sass")
              else "scss"} for rel in files if rel.lower().endswith(css_sass.SUFFIXES)]
    parsed = css_sass.index(work_dir, items)
    records, missing = [], {}
    for item in items:
        rel, sheet = item["key"], parsed["sheets"].get(item["key"], {"error": "not parsed"})
        if "error" in sheet:
            missing[rel] = f"not parsed: {sheet['error']}"[:200]
            continue
        records += tree_records(rel, sheet["tree"], "scss", module=rel if MODULE_RE.search(rel) else None)
        records.append({"t": "file", "file": rel})
    return {"indexer": parsed["indexer"], "records": records, "missing": missing}


# Reading: stylesheets and markup into records.

def index(project_dir: Path, work_dir: Path | None = None, files: list[str] | None = None) -> dict:
    """Records of every stylesheet and HTML/EJS file: `node`, `ref`, `classes`, `hole` and `file`."""
    begun = time.time()
    project_dir = Path(project_dir)
    records, missing = [], {}
    for rel in files if files is not None else walk(project_dir):
        lower = rel.lower()
        suffix = Path(lower).suffix
        if suffix in UNREAD:
            missing[rel] = UNREAD[suffix]
            continue
        if not lower.endswith(STYLESHEETS + MARKUP) or lower.endswith(css_sass.SUFFIXES + css_less.SUFFIXES +
                                                                      css_stylus.SUFFIXES):
            continue  # Sass, Less and Stylus are read by their own parsers
        if suffix in PARTLY:
            missing[rel] = PARTLY[suffix]
        try:
            text = (project_dir / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            missing[rel] = f"not read: {error!r}"[:200]
            continue
        try:
            found = _markup(rel, text) if lower.endswith(MARKUP) else _sheet(rel, text, stylesheet.dialect_for(rel))
        except Exception as error:  # a file the parsers cannot read stays a declared gap
            missing[rel] = f"not parsed: {error!r}"[:200]
            continue
        records += found + [{"t": "file", "file": rel}]
    parser = Path(stylesheet.__file__)
    return {"indexer": {"name": "codebase-map stylesheet.py", "version": _sha(parser),
                        "seconds": round(time.time() - begun, 1), "peak_mb": None},
            "records": records, "missing": missing}


def _sheet(rel: str, text: str, dialect: str, offset: int = 0, inline: bool = False, scope=None) -> list[dict]:
    """One stylesheet, or a `<style>` block (`offset` lines down) or a style attribute (`inline`); `scope`: the
    component a scoped block belongs to, or the CSS Module a module block is."""
    statements = []
    original = stylesheet._statement

    def observe(sheet, statement, start, end, stack, dialect_):
        statements.append((statement, start + offset, stack[-1] if stack else None))
        return original(sheet, statement, start, end, stack, dialect_)
    stylesheet._statement = observe
    try:
        sheet = stylesheet.parse_sheet(text, dialect)
    finally:
        stylesheet._statement = original
    module = scope or (rel if MODULE_RE.search(rel) else None)
    out, owner, parents, local, layers = [], {}, {}, collections.defaultdict(dict), []

    def visit(nodes, parent, current):
        for node in nodes:
            parents[id(node)] = parent
            here, line = current, node.line + offset
            if inline:
                pass
            elif node.kind == "rule":
                label = ", ".join(node.selectors)
                for prelude in reversed(node.context):
                    label = f"{prelude} {{ {label} }}"
                here = f"{rel}:{line} {label}"
                out.extend(_ref("custom-selector", word, word, rel, line, here) for word in
                           dict.fromkeys(CUSTOM_SELECTOR_RE.findall(" ".join(node.selectors))))
                out.append(_node(here, "rule", rel, line, list(dict.fromkeys(_selector_names(node.selectors, module) +
                                                                     _scope_names(node.context, module)))))
            elif node.kind == "definition":
                kind = "function" if node.prelude.startswith("@function") else "mixin"
                here = f"{rel}:{line} @{kind} {node.name}"
                out.append(_node(here, kind, rel, line, [(kind, node.name, rel)] if parent is None else []))
                for name in re.findall(r"\$([A-Za-z_][\w-]*)", node.parameters or ""):
                    local[id(node)]["$" + name] = (here, "parameter")
            elif node.kind == "at-rule":
                here = _at_rule(node, rel, line, out, local, layers, current) or current
            owner[id(node)] = here
            visit(node.children, node, here)
    visit(sheet.nodes, None, rel)
    for statement, line, node in statements:
        source = owner.get(id(node), rel) if node is not None else rel
        out += _statement(statement, line, node, source, rel, dialect, module, parents, local, layers, owner, sheet)
    out += _layers(rel, layers, sheet)
    return out


class _Frame:
    """A block of a parsed tree as the walker stands in it: what `&` names, the at-rules around, the graph node later
    statements belong to, the variables declared here, and a loop's literal iterations."""

    def __init__(self, parent=None, here=None, selectors=None, context=None, **flags):
        self.parent, self.here = parent, here if here is not None else parent.here
        self.selectors = selectors if selectors is not None or parent is None else parent.selectors
        self.context = context if context is not None else (parent.context if parent else [])
        self.face = flags.get("face", parent.face if parent else False)
        self.keyframes = flags.get("keyframes", parent.keyframes if parent else False)
        self.loop = flags.get("loop")  # (variables, iterations or None)
        # Less: the namespace path a mixin call names this block by, None when it cannot be called.
        self.path = flags.get("path", parent.path if parent else [])
        self.root = parent is None
        self.vars, self.literals = {}, {}

    def find(self, name):
        frame = self
        while frame is not None:
            if name in frame.vars:
                return frame.vars[name]
            frame = frame.parent
        return None

    def literal(self, name):
        frame = self
        while frame is not None:
            if name in frame.vars or name in frame.literals:
                return frame.literals.get(name)
            frame = frame.parent
        return None

    def loop_of(self, name):
        frame = self
        while frame is not None:
            if frame.loop and name in frame.loop[0]:
                return frame
            frame = frame.parent
        return None


def tree_records(rel: str, tree: list, dialect: str, offset: int = 0, module: str | None = None) -> list[dict]:
    """The records of a sheet an engine parsed into the neutral tree (`css_sass.js`): rules, variables, mixins,
    functions and placeholders as nodes; imports, `$x`, `@include`, `@extend`, function calls and every CSS fact of a
    declaration as references. A selector built by interpolation is generated only from a loop over literal values
    written in the loop itself (each name it yields is uncertain); otherwise the rule is a hole with its shape."""
    out, layers = [], []
    less, styl = dialect == "less", dialect == "stylus"
    variable = "less-variable" if less else "stylus-variable" if styl else "sass-variable"
    interpolation = "@{" if less else "{" if styl else "#{"
    root = _Frame(here=rel, selectors=None, context=[])

    def line_of(n):
        return n["line"] + offset

    def refs(items, frame, line):
        for item in items or ():
            name, ns = item["name"], item.get("ns")
            site = (item.get("line") or line - offset) + offset
            symbol = f"{ns}.{name}" if ns else name
            kind = variable if item["k"] == "var" else "function"
            found = frame.find(name) if ns is None and kind == variable and not name.startswith("@@") else None
            if found:
                out.append(_ref(kind, name, symbol, rel, site, frame.here, (found[1],), to=found[0]))
            elif styl:
                out.append(_ref(kind, name, symbol, rel, site, frame.here, stylus=kind, optional=item.get("optional")
                                or kind == "function"))
            else:
                out.append(_ref(kind, name, symbol, rel, site, frame.here, ns=ns))

    def label(selectors, context):
        text = ", ".join(selectors)
        for prelude in reversed(context):
            text = f"{prelude} {{ {text} }}"
        return text

    def placeholders(selectors):
        return [("placeholder", m.group(1), None) for selector in selectors
                for m in PLACEHOLDER_RE.finditer(stylesheet._without_strings_and_brackets(selector))]

    def generated(selectors, frame):
        """Every concrete selector list of the loops the interpolations name, or None when one is not literal. In
        Less an interpolation names a variable: one list, from the literal value its scope gives it."""
        if less:
            values = {}
            for selector in selectors:
                for match in LESS_INTERPOLATION_RE.finditer(selector):
                    values[match.group(0)] = frame.literal("@" + match.group(1))
            if any(value is None for value in values.values()):
                return None
            return [[LESS_INTERPOLATION_RE.sub(lambda m: values[m.group(0)], s) for s in selectors]]
        pattern = STYLUS_INTERPOLATION_RE if styl else INTERPOLATION_RE
        needed = {m.group(1) for selector in selectors for m in pattern.finditer(selector)}
        loops = []
        for name in needed:
            loop = frame.loop_of(name)
            if loop is None or loop.loop[1] is None:
                return None
            position = loop.loop[0].index(name)
            if any(values[position] is None for values in loop.loop[1]):
                return None
            if loop not in loops:
                loops.append(loop)
        combos = [{}]
        for loop in loops:
            combos = [{**combo, **dict(zip(loop.loop[0], values))} for combo in combos for values in loop.loop[1]]
            if len(combos) > 256:
                return None
        variants = []
        for combo in combos:
            concrete = [pattern.sub(lambda m: combo.get(m.group(1), m.group(0)), s) for s in selectors]
            if any(interpolation in s for s in concrete):
                return None
            variants.append(concrete)
        return variants

    def rule(n, frame):
        line = line_of(n)
        raw = "".join(part if isinstance(part, str) else
                      "@{" + part["v"][1:] + "}" if "v" in part and less else
                      "{" + part["v"] + "}" if "v" in part and styl else
                      "#{" + ((part["ns"] + ".") if part.get("ns") else "") + part["v"] + "}" if "v" in part else
                      "#{" + part["x"] + "}" for part in n["sel"])
        selectors = stylesheet._flatten(raw, frame.selectors, "scss")
        here = frame.here if frame.keyframes else f"{rel}:{line} {label(selectors, frame.context)}"
        own = raw.strip()
        path = [*frame.path, own] if less and frame.path is not None and CALLABLE_RE.match(own) else None
        inner = _Frame(frame, here=here, selectors=selectors, path=path)
        refs(n.get("refs"), inner, line)
        for item in n.get("extends") or ():
            out.append({"t": "classes", "kind": "class", "file": rel, "line": line, "from": here,
                        "chain": [":extend"], "alts": [[{"s": " ".join(
                            m.group(1) for m in stylesheet._CLASS_OR_ID_RE.finditer(item["sel"])
                            if m.group(0)[0] == ".")}]]})
        for part in n["sel"]:
            if isinstance(part, dict) and "v" in part:
                refs([{"k": "var", "name": part["v"], "ns": part.get("ns")}], inner, line)
            elif isinstance(part, dict):
                refs(part.get("refs"), inner, line)
        if frame.keyframes:
            walk(n.get("kids") or [], inner)
            return
        names = _selector_names(selectors, module) + placeholders(selectors) + _scope_names(frame.context, module)
        if path is not None:
            names.append(("less-mixin", " ".join(path), rel))
        record = _node(here, "rule", rel, line, names)
        if any(interpolation in s for s in selectors):
            variants = generated(selectors, frame)
            if variants is None:
                out.append({"t": "hole", "file": rel, "line": line, "kind": "rule", "cls": "interpolated-selector",
                            "name": ", ".join(selectors)})
                out.append({"t": "interpolated", "file": rel, "line": line, "patterns": [
                    [m.group(1), m.group(2), m.group(3)] for s in selectors
                    for m in INTERPOLATED_RE.finditer(stylesheet._without_strings_and_brackets(s))]})
            else:
                static = {tuple(name) for name in names}
                extra = sorted({name for variant in variants for name in _selector_names(variant, module)} - static,
                               key=lambda item: (item[0], item[1], item[2] or ""))
                record["names"] += [list(name) for name in extra]
                record["generated"] = [list(name) for name in extra]
                if not extra:  # nothing new from the values: what it names is still not known
                    out.append({"t": "hole", "file": rel, "line": line, "kind": "rule",
                                "cls": "interpolated-selector", "name": ", ".join(selectors)})
        out.append(record)
        walk(n.get("kids") or [], inner)

    def decl(n, frame, prefix=""):
        line = line_of(n)
        prop = prefix + n["prop"]
        if module and frame.selectors == [":export"]:
            out.append(_node(f"{rel}:{line} :export {prop}", "export", rel, line, [("export", prop, module)]))
            refs(n.get("refs"), frame, line)
            return
        if n.get("value"):
            out.extend(declaration(rel, line, frame.here, prop, n["value"], in_face=frame.face, module=module))
        refs(n.get("refs"), frame, line)
        for kid in n.get("kids") or ():
            if kid["t"] == "decl":
                decl(kid, frame, prop + "-")

    def at(n, frame):
        name, params, line = n["name"].lower(), n.get("params", ""), line_of(n)
        refs(n.get("refs"), frame, line)
        kids = n.get("kids")
        if name.endswith("keyframes"):
            word = _unquote(params)
            here = f"{rel}:{line} @{name} {word}"
            out.append(_node(here, "keyframes", rel, line, [("keyframes", word)]))
            walk(kids or [], _Frame(frame, here=here, keyframes=True))
            return
        if name == "font-face":
            family = next((_unquote(k["value"]) for k in kids or () if k["t"] == "decl"
                           and k["prop"].lower() == "font-family"), "")
            here = f"{rel}:{line} @font-face {family}"
            out.append(_node(here, "font-face", rel, line, [("font-face", family.lower())]))
            walk(kids or [], _Frame(frame, here=here, face=True))
            return
        if name == "property":
            here = f"{rel}:{line} @property {params}"
            out.append(_node(here, "property", rel, line, [("custom-property", params)]))
            walk(kids or [], _Frame(frame, here=here))
            return
        if name == "import":
            for spec in stylesheet._import_specs(params, "import"):
                out.append(_ref("import", spec, spec, rel, line, rel))
            return
        if name == "value":
            out.extend(css_value(params, rel, line, frame.here, module))
            return
        if name == "custom-selector":
            word = params.split()[0] if params else ""
            out.append(_node(f"{rel}:{line} @custom-selector {word}", "custom-selector", rel, line,
                             [("custom-selector", word)]))
            return
        if name == "tailwind":
            out.append(_ref("import", "tailwindcss", f"@tailwind {params}", rel, line, rel, package="tailwindcss"))
            return
        if name == "apply":
            out.append({"t": "classes", "kind": "class", "file": rel, "line": line, "from": frame.here,
                        "chain": ["@apply"], "alts": [[{"s": stylesheet._IMPORTANT_RE.sub("", params)}]]})
            return
        if name == "layer":
            for segment in stylesheet.split_top_level(params) or ([] if kids is None else ["(anonymous)"]):
                layers.append((line, segment, frame.here))
        elif name == "container":
            for condition in stylesheet.split_top_level(params):
                match = re.match(r"\s*(-?[A-Za-z_][\w-]*)(\()?", condition)
                if match and not match.group(2) and match.group(1).lower() not in ("not", "and", "or"):
                    out.append(_ref("container", match.group(1), match.group(1), rel, line, frame.here))
        elif name == "media":
            out.extend(_ref("custom-media", w, w, rel, line, frame.here) for w in CUSTOM_MEDIA_RE.findall(params))
        elif name == "custom-media" and kids is None:
            word = params.split()[0] if params else ""
            out.append(_node(f"{rel}:{line} @custom-media {word}", "custom-media", rel, line, [("custom-media", word)]))
        if kids is None:
            return
        if name == "at-root":
            if params and not params.startswith("("):
                parents = frame.selectors if "&" in params else None
                rule({"line": n["line"], "sel": [stylesheet._flatten(params, parents, "scss", prefix=False)[0]
                                                 if parents else params], "kids": kids}, _Frame(frame, selectors=[]))
                return
            walk(kids, _Frame(frame, selectors=[]))
            return
        walk(kids, _Frame(frame, context=[*frame.context, f"@{n['name']} {params}".strip()]))

    def walk(nodes, frame):
        if less:  # Less evaluates lazily: a block's variables are visible in all of it, the last one winning
            for n in nodes:
                if n["t"] == "var":
                    if not frame.root:
                        frame.vars[n["name"]] = (f"{rel}:{line_of(n)} {n['name']}", "local")
                    frame.literals[n["name"]] = n.get("literal")
        for n in nodes:
            t, line = n["t"], line_of(n)
            if t == "rule":
                rule(n, frame)
            elif t == "decl":
                decl(n, frame)
            elif t == "var":
                here = f"{rel}:{line} {n['name']}"
                top = frame.root or "global" in n.get("flags", ())
                refs(n.get("refs"), frame, line)
                if n.get("ns"):
                    out.append(_ref("sass-variable", n["name"], f"{n['ns']}.{n['name']}", rel, line, frame.here,
                                    ("assignment",), ns=n["ns"]))
                    continue
                if not top and not less and not styl and frame.find(n["name"]):
                    continue  # an assignment to a variable already declared in an enclosing block
                record = _node(here, "variable", rel, line, [(variable, n["name"], rel)] if top else [])
                if less:
                    record["literal"] = n.get("literal")
                out.append(record)
                if not top and not less:
                    frame.vars[n["name"]] = (here, "local")
                if n.get("kids"):
                    walk(n["kids"], _Frame(frame, here=here, selectors=[], path=None))
            elif t == "import" and (less or styl):  # an import Less and Stylus inline: one compilation
                kind = "plugin" if n["kind"] == "plugin" else "import"
                out.append(_ref(kind, n["url"], n["url"], rel, line, rel, less=kind, options=n.get("options") or []))
            elif t == "import":
                ns = n.get("ns")
                if n["kind"] == "use" and ns is None:
                    ns = "*"
                out.append(_ref("import", n["url"], n["url"], rel, line, rel, sass=n["kind"], ns=ns,
                                prefix=n.get("prefix") or "", show=n.get("show"), hide=n.get("hide")))
                for name in n.get("config") or ():
                    out.append(_ref("sass-variable", name, name, rel, line, rel, ("configuration",), ns=ns))
            elif t == "def" and less:
                here = f"{rel}:{line} @mixin {n['name']}"
                path = [*frame.path, n["name"]] if frame.path is not None else None
                record = _node(here, "mixin", rel, line, [("less-mixin", " ".join(path), rel)] if path else [])
                record["guard"] = bool(n.get("refs"))
                out.append(record)
                inner = _Frame(frame, here=here, selectors=[], path=path)
                for param in n.get("params") or ():
                    inner.vars[param] = (here, "parameter")
                refs(n.get("refs"), inner, line)
                walk(n.get("kids") or [], inner)
            elif t == "include" and styl:
                out.append(_ref("mixin", n["name"], n["name"], rel, line, frame.here, stylus="mixin"))
                refs(n.get("refs"), frame, line)
            elif t == "include" and less:
                scope = frame.path or []
                alts = [" ".join([*scope[:end], *n["path"]]) for end in range(len(scope), -1, -1)]
                out.append(_ref("mixin", " ".join(n["path"]), n["symbol"], rel, line, frame.here, less="mixin",
                                alts=alts))
                refs(n.get("refs"), frame, line)
            elif t == "def":
                here = f"{rel}:{line} @{n['kind']} {n['name']}"
                key = "stylus-mixin" if styl else n["kind"]
                out.append(_node(here, n["kind"], rel, line, [(key, n["name"], rel)] if frame.root else []))
                inner = _Frame(frame, here=here, selectors=[])
                for param in n.get("params") or ():
                    inner.vars[param] = (here, "parameter")
                refs(n.get("refs"), inner, line)
                walk(n.get("kids") or [], inner)
            elif t == "include":
                symbol = f"{n['ns']}.{n['name']}" if n.get("ns") else n["name"]
                out.append(_ref("mixin", n["name"], symbol, rel, line, frame.here, ns=n.get("ns")))
                refs(n.get("refs"), frame, line)
                inner = _Frame(frame)
                for param in n.get("using") or ():
                    inner.vars[param] = (frame.here, "parameter")
                walk(n.get("kids") or [], inner)
            elif t == "extend":
                text = re.sub(r"!optional\s*$", "", n["sel"]).strip()
                for part in stylesheet.split_top_level(text):
                    for match in PLACEHOLDER_RE.finditer(part):
                        out.append(_ref("placeholder", match.group(1), "%" + match.group(1), rel, line, frame.here))
                classes = " ".join(m.group(1) for m in stylesheet._CLASS_OR_ID_RE.finditer(text)
                                   if m.group(0)[0] == ".")
                if classes:
                    out.append({"t": "classes", "kind": "class", "file": rel, "line": line, "from": frame.here,
                                "chain": [":extend" if less else "@extend"], "alts": [[{"s": classes}]]})
            elif t == "loop":
                refs(n.get("refs"), frame, line)
                inner = _Frame(frame, loop=(n["vars"], n.get("values")))
                for name in n["vars"]:
                    here = f"{rel}:{line} {name}"
                    out.append(_node(here, "variable", rel, line))
                    inner.vars[name] = (here, "loop")
                walk(n.get("kids") or [], inner)
            elif t == "block":
                refs(n.get("refs"), frame, line)
                walk(n.get("kids") or [], _Frame(frame))
            elif t == "ref":
                refs(n.get("refs"), frame, line)
            elif t == "at":
                at(n, frame)

    walk(tree, root)
    out += _layers(rel, layers, _tailwind_of(tree))
    return out


def _tailwind_of(tree: list):
    """What `_layers` needs to know of a parsed tree: which Tailwind it loads."""
    class Sheet:
        tailwind = None
    for n in tree:
        if n["t"] == "at" and n["name"].lower() == "tailwind":
            Sheet.tailwind = "v3"
        elif n["t"] == "import" and str(n.get("url", "")).startswith("tailwindcss"):
            Sheet.tailwind = "v4"
    return Sheet


def _node(identity: str, kind: str, rel: str, line: int, names=()) -> dict:
    return {"t": "node", "id": identity, "kind": kind, "file": rel, "line": line, "names": [list(n) for n in names]}


def _ref(kind: str, name: str, symbol: str, rel: str, line: int, source: str, chain=(), **extra) -> dict:
    return {"t": "ref", "kind": kind, "name": name, "symbol": symbol, "site": f"{rel}:{line}", "file": rel,
            "from": source, "chain": list(chain), **extra}


def _at_rule(node, rel, line, out, local, layers, current) -> str | None:
    """Nodes and references of an at-rule block; the graph node later declarations sit in, if any."""
    name, rest = node.name, node.prelude[len(node.name) + 1:].strip()
    if name.endswith("keyframes"):
        word = _unquote(rest)
        here = f"{rel}:{line} @{name} {word}"
        out.append(_node(here, "keyframes", rel, line, [("keyframes", word)]))
        return here
    if name == "font-face":
        family = next((_unquote(d.value) for d in node.declarations if d.property == "font-family"), "")
        here = f"{rel}:{line} @font-face {family}"
        out.append(_node(here, "font-face", rel, line, [("font-face", family.lower())]))
        return here
    if name == "property":
        here = f"{rel}:{line} @property {rest}"
        out.append(_node(here, "property", rel, line, [("custom-property", rest)]))
        return here
    if name == "media":
        out += [_ref("custom-media", word, word, rel, line, current) for word in CUSTOM_MEDIA_RE.findall(rest)]
    if name == "utility":
        here = f"{rel}:{line} @utility {rest}"
        names = [("utility-pattern", rest[:-1])] if rest.endswith("*") else [("utility", rest)]
        out.append(_node(here, "rule", rel, line, names))
        return here
    if name == "custom-variant":
        word = rest.split()[0] if rest else ""
        here = f"{rel}:{line} @custom-variant {word}"
        out.append(_node(here, "variant", rel, line, [("variant", word)]))
        return here
    if name == "variant":
        out.append(_ref("variant", rest.split()[0] if rest else "", rest, rel, line, current, optional=True))
    if name == "layer" and node.layer:
        layers.append((line, node.layer, current))
    elif name == "container":
        for condition in stylesheet.split_top_level(rest):
            match = re.match(r"\s*(-?[A-Za-z_][\w-]*)(\()?", condition)
            if match and not match.group(2) and match.group(1).lower() not in ("not", "and", "or"):
                out.append(_ref("container", match.group(1), match.group(1), rel, line, current))
    elif name == "include":
        out += _include(rest, rel, line, current)
    elif name in ("each", "for"):
        for word in re.findall(r"\$([A-Za-z_][\w-]*)", rest.split(" in ")[0].split(" from ")[0]):
            here = f"{rel}:{line} ${word}"
            out.append(_node(here, "variable", rel, line))
            local[id(node)]["$" + word] = (here, "loop")
    return None


def _statement(text, line, node, source, rel, dialect, module, parents, local, layers, owner, sheet) -> list[dict]:
    """The records of one statement the parser read: an at-statement, a variable or a declaration."""
    at = re.match(r"@([\w-]+)", text)
    if at:
        name, rest = at.group(1).lower(), text[at.end():].strip()
        if name in ("import", "use", "forward"):
            out = []
            for spec in stylesheet._import_specs(rest, name):
                ns = None
                if name == "use":
                    alias = re.search(r"\bas\s+(\*|[\w-]+)\s*(?:with\b|$)", rest)
                    ns = alias.group(1) if alias else re.sub(r"^_|\.(s[ac]ss|css)$", "", spec.rsplit("/", 1)[-1])
                out.append(_ref("import", spec, spec, rel, line, rel, sass=name if dialect != "css" else None, ns=ns))
            layered = stylesheet._IMPORT_LAYER_RE.search(stylesheet._IMPORT_TARGET_RE.sub(" ", rest))
            if name == "import" and layered is not None and layered.group(1):
                layers.append((line, layered.group(1).strip(), rel))
            return out
        if name == "tailwind":
            return [_ref("import", "tailwindcss", f"@tailwind {rest}", rel, line, rel, package="tailwindcss")]
        if name == "custom-variant":
            word = rest.split()[0] if rest else ""
            return [_node(f"{rel}:{line} @custom-variant {word}", "variant", rel, line, [("variant", word)])]
        if name == "custom-media":
            word = rest.split()[0] if rest else ""
            return [_node(f"{rel}:{line} @custom-media {word}", "custom-media", rel, line, [("custom-media", word)])]
        if name == "custom-selector":
            word = rest.split()[0] if rest else ""
            return [_node(f"{rel}:{line} @custom-selector {word}", "custom-selector", rel, line,
                          [("custom-selector", word)])]
        if name == "value":
            return css_value(rest, rel, line, source, module)
        if name in ("plugin", "config"):
            spec = _unquote(rest)
            return [_ref("plugin" if name == "plugin" else "config", spec, spec, rel, line, rel)]
        if name == "source":
            inline = re.match(r"(?:not\s+)?inline\(\s*([\"'])(.*?)\1\s*\)", rest)
            if inline:
                return [{"t": "classes", "kind": "class", "file": rel, "line": line, "from": rel,
                         "chain": ["@source inline"], "alts": [[{"s": inline.group(2)}]]}]
            spec = _unquote(re.sub(r"^not\s+", "", rest))
            return [_ref("source", spec, spec, rel, line, rel)]
        if name == "apply" and node is not None:
            return [{"t": "classes", "kind": "class", "file": rel, "line": line, "from": source, "chain": ["@apply"],
                     "alts": [[{"s": stylesheet._IMPORTANT_RE.sub("", rest)}]]}]
        if name == "extend" and node is not None:
            return [{"t": "classes", "kind": "class", "file": rel, "line": line, "from": source, "chain": ["@extend"],
                     "alts": [[{"s": " ".join(w[1:] for w in rest.replace(",", " ").split() if w.startswith("."))}]]}]
        if name == "include":
            return _include(rest, rel, line, source, node, parents, local)
        if name == "layer":
            prefix = node.layer if node is not None and node.layer else None
            for segment in stylesheet.split_top_level(rest):
                layers.append((line, f"{prefix}.{segment}" if prefix else segment, source))
        return []
    variable = re.match(r"(\$[A-Za-z_][\w-]*)\s*:(.*)$", text, re.S) if dialect == "scss" else None
    if variable:
        here = f"{rel}:{line} {variable.group(1)}"
        top = node is None
        out = [_node(here, "variable", rel, line, [("sass-variable", variable.group(1), rel)] if top else [])]
        if not top:
            local[id(node)][variable.group(1)] = (here, "local")
        return out + _sass_refs(variable.group(2), rel, line, source, node, parents, local)
    if node is None or ":" not in text:
        return []
    prop, value = (part.strip() for part in text.split(":", 1))
    if not stylesheet._PROPERTY_RE.match(prop):
        return []
    in_face = node.kind == "at-rule" and node.name == "font-face"
    if module and node.kind == "rule" and node.selectors == [":export"]:
        return [_node(f"{rel}:{line} :export {prop}", "export", rel, line, [("export", prop, module)])]
    out = declaration(rel, line, source, prop, stylesheet._IMPORTANT_RE.sub("", value).strip(), in_face=in_face,
                      module=module)
    if dialect == "scss":
        out += _sass_refs(value, rel, line, source, node, parents, local)
    return out


def _layers(rel: str, layers: list, sheet) -> list[dict]:
    """A layer's first appearance in the file is its node; every later one refers to it. In a Tailwind sheet the
    layers Tailwind declares are Tailwind's."""
    out, first = [], {}
    tailwind = TAILWIND_LAYERS.get(sheet.tailwind or "", set())
    for line, name, source in sorted(layers, key=lambda item: item[0]):
        if name in tailwind:
            out.append(_ref("layer", name, name, rel, line, source, package="tailwindcss"))
        elif name in first:
            out.append(_ref("layer", name, name, rel, line, source, to=first[name]))
        else:
            first[name] = f"{rel}:{line} @layer {name}"
            out.append(_node(first[name], "layer", rel, line))
    return out


def _include(rest, rel, line, source, node=None, parents=None, local=None) -> list[dict]:
    match = re.match(r"(?:([\w-]+)\.)?([\w-]+)", rest)
    if not match:
        return []
    symbol = match.group(0)
    out = [_ref("mixin", match.group(2), symbol, rel, line, source, ns=match.group(1))]
    return out + _sass_refs(rest[match.end():], rel, line, source, node, parents or {}, local or {})


def _sass_refs(value, rel, line, source, node, parents, local) -> list[dict]:
    out = []
    for match in SASS_REF_RE.finditer(value):
        ns, name = match.group(1), "$" + match.group(2)
        found = None
        if ns is None:
            up = node
            while up is not None and found is None:
                found = local.get(id(up), {}).get(name)
                up = parents.get(id(up))
        extra = {"to": found[0]} if found else {"ns": ns}
        out.append(_ref("sass-variable", name, match.group(0), rel, line, source, (found[1],) if found else (), **extra))
    return out


def declaration(rel: str, line: int, source: str, prop: str, value: str | None, chain=(), in_face=False,
                module=None, script=False) -> list[dict]:
    """The records of one declaration, wherever it is written: a rule, a style attribute, a script's style object
    or `setProperty`. `script`: the value's `var()` uses come from the script's literals, read on their own."""
    out = []
    if prop.startswith("--"):
        out.append(_node(f"{rel}:{line} {prop}", "custom-property", rel, line, [("custom-property", prop)]))
    if value is None:
        return out
    if not script:
        out += var_refs(value, rel, line, source, chain)
    lower = prop.lower()
    if lower in ("animation", "animation-name", "-webkit-animation", "-webkit-animation-name"):
        out += [_ref("keyframes", name, name, rel, line, source, chain) for name in _keyframes(lower, value)]
    elif lower in ("font-family", "font") and not in_face:
        out += [_ref("font-face", name.lower(), name, rel, line, source, chain) for name in _families(lower, value)]
    elif lower in ("container-name", "container"):
        part = value.split("/")[0] if lower == "container" else value
        out += [_node(f"{rel}:{line} container {w}", "container", rel, line, [("container", w)])
                for w in part.split() if IDENT.match(w) and w.lower() not in CSS_WIDE]
    elif lower == "composes" and module:
        match = re.match(r"(.+?)\s+from\s+(global|([\"'])(.+?)\3)\s*$", value)
        origin = (match.group(4) or "global") if match else None
        for name in (match.group(1) if match else value).split():
            out.append(_ref("composes", name, "." + name, rel, line, source, chain, module=module, origin=origin))
    if module and lower != "composes" and not script:  # a word may be one of the module's `@value` names
        plain = stylesheet._STRING_RE.sub(" ", stylesheet._URL_RE.sub(" ", value))
        for word in dict.fromkeys(re.findall(r"(?<![\w$@#.-])([A-Za-z_][\w-]*)(?![\w(-])", plain)):
            out.append(_ref("css-value", word, word, rel, line, source, chain, module=module, optional=True))
    return out


def css_value(rest: str, rel: str, line: int, source: str, module: str | None) -> list[dict]:
    """The records of a CSS Modules `@value`: a declaration, or names imported from another module."""
    match = VALUE_RE.match(rest)
    if not match or not module:
        return []
    if match.group("name"):
        return [_node(f"{rel}:{line} @value {match.group('name')}", "css-value", rel, line,
                      [("css-value", match.group("name"), module)])]
    out = []
    for item in match.group("names").split(","):
        origin, _, local = (part.strip() for part in item.partition(" as "))
        out.append(_ref("css-value", origin, origin, rel, line, source, ("from",), module=module,
                        origin=match.group("origin"), local=local or origin))
    return out


def var_refs(text: str, rel: str, line: int, source: str, chain=(), strings: bool = True) -> list[dict]:
    """Every `var(--x)` of a CSS text, outside its strings unless `strings` is False (a script's literal, quotes
    and all); the line of each counted inside the text."""
    plain = stylesheet._STRING_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text) if strings else text
    return [_ref("custom-property", m.group(1), m.group(1), rel, line + text[:m.start()].count("\n"), source, chain,
                 fallback=(m.group(2) or "").strip() or None) for m in VAR_RE.finditer(plain)]


def _unquote(text: str) -> str:
    text = text.strip()
    return text[1:-1] if len(text) > 1 and text[0] in "'\"" and text[-1] == text[0] else " ".join(text.split())


def _keyframes(prop: str, value: str) -> list[str]:
    names = []
    for layer in stylesheet.split_top_level(value):
        for word in WORD_RE.findall(layer):
            if word[0] in "'\"":
                names.append(word[1:-1])
            elif "(" not in word and "$" not in word and IDENT.match(word) and word.lower() not in CSS_WIDE \
                    and not (prop.endswith("animation") and word.lower() in ANIMATION_WORDS):
                names.append(word)
    return names


def _families(prop: str, value: str) -> list[str]:
    if prop == "font":
        if value.strip().lower() in SYSTEM_FONTS:
            return []
        size = SIZE_RE.search(value)
        if size is None:
            return []
        value = value[size.end():]
    out = []
    for item in stylesheet.split_top_level(value):
        item = item.strip()
        if not item or "var(" in item or "$" in item or "#{" in item:
            continue
        quoted = item[0] in "'\""
        name = _unquote(item)
        if name and (quoted or name.lower() not in GENERIC_FONTS):
            out.append(name)
    return out


def _scope_names(context: list[str], module: str | None) -> list[tuple]:
    """The classes and ids an enclosing `@scope (root) to (limit)` names: a rule inside styles only within them."""
    found = []
    for prelude in context:
        match = SCOPE_RE.match(prelude)
        if match:
            found += _selector_names([s for part in (match.group("root"), match.group("limit")) if part
                                      for s in stylesheet.split_top_level(part)], module)
    return found


def _selector_names(selectors: list[str], module: str | None) -> list[tuple]:
    """(class or id, name, scope) of every class and id a rule's selectors name: scope None for a global name, the
    module's path for a CSS Module's local one (`:global(...)` and `:global` make it global)."""
    names = set()
    svelte = bool(module) and module.startswith("scoped:") and module.endswith(".svelte")
    for selector in selectors:
        text = stylesheet._without_strings_and_brackets(selector)
        if svelte:  # Svelte: a compound selector led by `:global(...)` is global as a whole (`:global(html).dark`)
            text = SVELTE_GLOBAL_RE.sub(r":global(\1\2)", text)
        events = sorted([(m.start(), 0, m) for m in MODE_RE.finditer(text)] +
                        [(m.start(), 1, m) for m in stylesheet._CLASS_OR_ID_RE.finditer(text)
                         if not text.startswith(("#{", "@{"), m.end())], key=lambda item: item[:2])
        mode, stack = "local", []
        deep = module.replace("scoped:", "deep:", 1) if module and module.startswith("scoped:") else None
        for _, kind, match in events:
            if kind == 1:
                scope = module if module and mode == "local" else deep if mode == "deep" else None
                names.add(("class" if match.group(0)[0] == "." else "id",
                           stylesheet._decode_escapes(match.group(1)), scope))
            elif match.group(1):
                if match.group(2):
                    stack.append(mode)
                mode = {"local": "local", "deep": "deep", "v-deep": "deep"}.get(match.group(1), "global")
            elif match.group(3):
                stack.append(mode)
            elif stack:
                mode = stack.pop()
    return sorted(names, key=lambda item: (item[0], item[1], item[2] or ""))


class _Markup(html.parser.HTMLParser):
    """Class, id, style and `<link rel=stylesheet>` attributes and `<style>` blocks of an HTML or EJS file."""

    def __init__(self, rel: str):
        super().__init__(convert_charrefs=True)
        self.rel, self.out, self.in_style = rel, [], False

    def handle_starttag(self, tag, attrs):
        line, raw = self.getpos()[0], self.get_starttag_text() or ""

        def at(name: str) -> int:
            found = re.search(r"(?<![\w-])" + re.escape(name) + r"\s*=", raw, re.I)
            return line + raw[:found.start()].count("\n") if found else line
        values = {}
        # Angular bindings keep their case only in the raw tag: `[class.isActive]`, `[ngClass]`, `[class]`.
        for match in re.finditer(r"\[(ngClass|class(?:\.([\w-]+))?)\]\s*=\s*(\"([^\"]*)\"|'([^']*)')", raw):
            expr = match.group(4) if match.group(4) is not None else match.group(5)
            where = line + raw[:match.start()].count("\n")
            if match.group(2):
                alts, chain = [[{"s": match.group(2)}]], ["[class.x]"]
            else:
                alts, chain = ng_class(expr), ["[ngClass]" if match.group(1) == "ngClass" else "[class]"]
            self.out.append({"t": "classes", "kind": "class", "file": self.rel, "line": where, "from": self.rel,
                             "chain": chain, "alts": alts})
        for name, value in attrs:
            if value is None:
                continue
            values[name] = value
            if name in ("class", "id"):
                parts, last = [], 0
                for match in TAG_RE.finditer(value):
                    tag = "ejs" if match.group().startswith("<%") else "template-tag"
                    parts += [{"s": value[last:match.start()]}, {"h": tag, "x": match.group(), "ctx": tag}]
                    last = match.end()
                parts.append({"s": value[last:]})
                self.out.append({"t": "classes", "kind": name, "file": self.rel, "line": at(name), "from": self.rel,
                                 "chain": [], "alts": [parts]})
            elif name == "style":
                self.out += _sheet(self.rel, "x{" + value + "}", "css", offset=at(name) - 1, inline=True)
        if tag == "link" and "stylesheet" in values.get("rel", "").lower().split() and values.get("href"):
            self.out.append(_ref("import", values["href"], values["href"], self.rel, at("href"), self.rel))
        if tag == "script" and values.get("src"):
            self.out.append(_ref("script", values["src"], values["src"], self.rel, at("src"), self.rel))
        self.in_style = tag == "style"

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.out += _sheet(self.rel, data, "css", offset=self.getpos()[0] - 1)


def ng_class(expr: str) -> list:
    """An Angular class binding's alternatives, read as `css_typescript.js` reads a class expression: a string, an
    array (side by side), an object (each key), a condition, `+`; any other value is a hole of its kind."""
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1].strip()
    quoted = re.fullmatch(r"'([^']*)'|\"([^\"]*)\"", expr)
    if quoted:
        return [[{"s": quoted.group(1) if quoted.group(1) is not None else quoted.group(2)}]]
    if expr.startswith("[") and expr.endswith("]"):
        parts = []
        for item in stylesheet.split_top_level(expr[1:-1]):
            for alt in ng_class(item):
                parts += [{"s": " "}, *alt]
        return [parts]
    if expr.startswith("{") and expr.endswith("}"):
        alts = []
        for item in stylesheet.split_top_level(expr[1:-1]):
            key = item.split(":", 1)[0].strip().strip("'\"")
            alts.append([{"s": key}] if re.fullmatch(r"[\w-]+(?:\s+[\w-]+)*", key) else [{"h": "computed-key", "x": item}])
        return alts
    ternary = stylesheet.split_top_level(expr, "?")
    if len(ternary) == 2 and len(stylesheet.split_top_level(ternary[1], ":")) == 2:
        yes, no = stylesheet.split_top_level(ternary[1], ":")
        return ng_class(yes) + ng_class(no)
    terms = stylesheet.split_top_level(expr, "+")
    if len(terms) > 1:
        alts = [[]]
        for term in terms:
            alts = [a + [p if "s" in p else {**p, "ctx": "concatenation"} for p in b] for a in alts for b in ng_class(term)]
        return alts
    kind = "variable" if re.fullmatch(r"[A-Za-z_$][\w$]*", expr) else \
        "property" if re.fullmatch(r"[\w$.]+", expr) else "expression"
    return [[{"h": kind, "x": expr[:120]}]]


def _markup(rel: str, text: str) -> list[dict]:
    parser = _Markup(rel)
    parser.feed(text)
    parser.close()
    for match in INCLUDE_RE.finditer(text) if rel.lower().endswith(".ejs") else ():
        spec = match.group("call") or match.group("bare")
        parser.out.append(_ref("include", spec, spec, rel, text.count("\n", 0, match.start()) + 1, rel))
    return parser.out


# Resolving: the records into the graph.

def tokens(alts: list) -> tuple[list[tuple[str, list, int | None]], list[tuple[str, str, int | None]]]:
    """The class tokens of a class expression's alternatives, each with the chain it came through and the line it
    is written on (None: the expression's), and its holes: a token touching a value not known statically is a
    hole of the token's form (template, concatenation, ejs), a value standing alone a hole of its own kind
    (variable, parameter, call...)."""
    found, holes = {}, {}
    for alt in alts:
        current = []

        def flush():
            if not current:
                return
            atoms = [p for p in current if "s" not in p]
            line = next((p["l"] for p in current if p.get("l")), None)
            if not atoms:
                chain = list(dict.fromkeys(tag for p in current for tag in p.get("c", ())))
                found.setdefault(("".join(p["s"] for p in current), line), chain)
            elif len(current) == 1:
                if "h" in atoms[0]:  # a CSS Module member stands for itself: its member record reads it
                    holes.setdefault((atoms[0]["h"], atoms[0]["x"], line), None)
            else:
                form = next((p["ctx"] for p in atoms if p.get("ctx")), "template")
                # text glued to a template tag: a class lost with it
                form = f"{form}-glued" if form in ("ejs", "template-tag") else form
                holes.setdefault((form, "".join(p["s"] if "s" in p else p["x"] if p.get("ctx") in ("ejs", "template-tag")
                                                else "${" + p["x"] + "}" for p in current), line), None)
            current.clear()
        for part in alt:
            if "s" not in part:
                current.append(part)
                continue
            line = part.get("l")
            for piece in re.split(r"(\s+)", part["s"]):
                if piece.isspace():
                    flush()
                elif piece:
                    current.append({"s": piece, "c": part.get("c", ()), "l": line})
                if line is not None:
                    line += piece.count("\n")
        flush()
    return [(token, chain, line) for (token, line), chain in found.items()], list(holes)


def class_tokens(records: list) -> set[str]:
    """Every literal class token of the records, for Tailwind to sort out."""
    return {token for record in records if record["t"] == "classes" and record["kind"] == "class"
            for token, _, _ in tokens(record["alts"])[0]}


def _package(project_dir: Path, start: Path, name: str) -> Path | None:
    for folder in [start, *start.parents]:
        candidate = folder / "node_modules" / name
        if candidate.is_dir():
            return candidate
        if folder == project_dir:
            break
    return None


def _file(path: Path, sass: bool) -> Path | None:
    extensions = ("", ".scss", ".sass", ".css", ".less", ".styl") if sass else ("", ".css")
    for name in ([path.name, "_" + path.name] if sass else [path.name]):
        for extension in extensions:
            candidate = path.with_name(name + extension)
            if candidate.is_file():
                return candidate
    for name in ("index", "_index") if sass else ("index",):
        for extension in extensions[1:]:
            if (path / (name + extension)).is_file():
                return path / (name + extension)
    return None


_CHECKOUT: dict = {}


def _checkout_files(project_dir: Path) -> list[str]:
    """Every file of the checkout outside `node_modules` and dot directories, read once per project."""
    if project_dir not in _CHECKOUT:
        found = []
        for folder, dirs, names in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
            found += [(Path(folder) / name).relative_to(project_dir).as_posix() for name in names]
        _CHECKOUT[project_dir] = found
    return _CHECKOUT[project_dir]


def _url_path(project_dir: Path, path: str) -> list[str]:
    """The checkout files a server can map a URL path to: those ending with its longest tail that any file ends
    with, the whole path or at least its last two segments (one segment alone would match any file of that name)."""
    parts = [part for part in path.split("/") if part]
    for start in range(len(parts)):
        if start and len(parts) - start < 2:
            break
        tail = "/".join(parts[start:])
        found = [rel for rel in _checkout_files(project_dir) if rel == tail or rel.endswith("/" + tail)]
        if found:
            return found
    return []


def remote_package(url: str) -> dict:
    """The package and version a CDN URL names, `unknown` when it names none."""
    for pattern, manager in CDN_RES:
        match = pattern.match(url)
        if match:
            return {"manager": manager, "package": match.group(1), "version": match.group(2), "from": "url"}
    return {"manager": "cdn", "package": re.sub(r"^https?://", "", url).split("/")[0], "version": "unknown",
            "from": "url"}


def sheet_package(text: str, rel: str) -> dict:
    """The package and version of a checkout file outside the snapshot: from its leading comment, else from the
    folder after a dependency directory in its path (`vendor/bootstrap-5.3.0/`), else `unknown`."""
    banner = BANNER_RE.match(text[:600].lstrip("﻿"))
    if banner:
        return {"manager": "checkout", "package": banner.group(1).strip(), "version": banner.group(2), "from": "banner"}
    parts = rel.split("/")
    for at in range(len(parts) - 2, -1, -1):
        if parts[at] in DEPENDENCY_DIRS:
            versioned = VERSIONED_RE.match(parts[at + 1])
            return {"manager": "checkout", "package": versioned.group(1) if versioned else parts[at + 1],
                    "version": versioned.group(2) if versioned else "unknown", "from": "path"}
    return {"manager": "checkout", "package": "unknown", "version": "unknown", "from": None}


def _download(url: str) -> str | None:
    """A CDN sheet's text, None when it cannot be fetched. Nothing about the project is sent."""
    import urllib.request
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "daodan-graph"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(8 << 20).decode("utf-8", errors="replace")
    except Exception:
        return None


def resolve(project_dir: Path, rel: str, spec: str, script: bool = False, base: Path | None = None,
            sass: bool | None = None):
    """Where an import leads: `("project", rel, chain)` (a checkout file, inside the snapshot or not),
    `("ambiguous", [rel, ...], chain)`, `("external", id, package dict, path)`, `("remote", url, package dict)` or
    `("hole", class, reason)`.

    A stylesheet or HTML file names a URL relative to itself (Sass and LESS also try partials and their own
    extensions), then a package; a script's bare specifier is a package; `~` names a package; a URL path names
    the checkout files ending with its longest tail (`url-suffix`). `base`: the folder relative names start from,
    when it is not the file's own (a sheet read from a package)."""
    clean = spec.split("?")[0].split("#")[0].strip()
    if clean.startswith("sass:"):
        return "external", clean, {"manager": "sass", "package": clean, "version": None}, None
    if re.match(r"^https?:", clean, re.I) or clean.startswith("//"):
        url = "https:" + clean if clean.startswith("//") else clean
        return "remote", url, remote_package(url)
    if re.match(r"^[A-Za-z][\w+.-]*:", clean):
        return "hole", "url-scheme", clean
    if clean.startswith("/"):
        found = _url_path(project_dir, clean)
        if len(found) == 1:
            return "project", found[0], "url-suffix"
        if found:
            return "ambiguous", found, "url-suffix"
        return "hole", "url-path", "a URL path no checkout file ends with"
    if sass is None:
        sass = rel.lower().endswith((".scss", ".sass", ".less", ".styl", ".stylus"))
    for candidate in _aliased(project_dir, clean.lstrip("~")):  # a bundler alias the tsconfig declares too
        found = _file(candidate.resolve(), sass)
        if found is not None:
            try:
                return "project", found.relative_to(project_dir).as_posix(), "paths"
            except ValueError:
                break
    base = base or (project_dir / rel).parent
    tilde = clean.startswith("~")
    clean = clean.lstrip("~")
    if not tilde and (clean.startswith(".") or not script):
        found = _file((base / clean).resolve(), sass)
        if found is not None:
            try:
                inside = found.relative_to(project_dir).as_posix()
            except ValueError:
                inside = None
            if inside and "node_modules" not in inside.split("/"):
                return "project", inside, None
            parts_ = found.resolve().as_posix().split("/")
            if "node_modules" in parts_:
                at = len(parts_) - 1 - parts_[::-1].index("node_modules")
                name = "/".join(parts_[at + 1:at + 3]) if parts_[at + 1].startswith("@") else parts_[at + 1]
                folder = Path("/".join(parts_[:at + 1])) / name
                meta = json.loads((folder / "package.json").read_text(encoding="utf-8")) \
                    if (folder / "package.json").is_file() else {}
                return "external", f"{name}/{found.resolve().relative_to(folder.resolve()).as_posix()}", \
                    {"manager": "npm", "package": name, "version": meta.get("version")}, found
    if clean.startswith(".") and not tilde:
        return "hole", "unresolved-import", spec
    parts = clean.split("/")
    name = "/".join(parts[:2]) if clean.startswith("@") else parts[0]
    sub = "/".join(parts[2:] if clean.startswith("@") else parts[1:])
    folder = _package(project_dir, base, name)
    if folder is None:
        return "hole", "unresolved-import", spec
    meta = json.loads((folder / "package.json").read_text(encoding="utf-8")) if (folder / "package.json").is_file() else {}
    found = _file(folder / sub, sass) if sub else next(
        (folder / meta[key] for key in ("sass", "style", "main") if isinstance(meta.get(key), str)
         and (folder / meta[key]).is_file()), None)
    if found is None:
        return "hole", "unresolved-import", spec
    return "external", f"{name}/{found.resolve().relative_to(folder.resolve()).as_posix()}", \
        {"manager": "npm", "package": name, "version": meta.get("version")}, found


_ALIASES: dict = {}


def aliases(project_dir: Path) -> list[tuple[str, list[Path]]]:
    """The path aliases the project's tsconfig or jsconfig declares (`compilerOptions.paths`, against `baseUrl`), in
    the root config, the configs it extends and the ones it references: [(prefix, [target folders])], longest first."""
    project_dir = Path(project_dir)
    if project_dir in _ALIASES:
        return _ALIASES[project_dir]
    import snapshot  # the product's JSONC reader
    found, seen = {}, set()

    def read(path: Path, depth: int = 0) -> None:
        if depth > 4 or path in seen or not path.is_file():
            return
        seen.add(path)
        try:
            data = json.loads(snapshot._strip_jsonc_comments(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return
        options = data.get("compilerOptions") or {}
        base = (path.parent / options.get("baseUrl", ".")).resolve()
        for pattern, targets in (options.get("paths") or {}).items():
            if isinstance(targets, list) and pattern not in found:
                found[pattern.rstrip("*")] = [(base / target.rstrip("*")).resolve() for target in targets
                                              if isinstance(target, str)]
        extends = data.get("extends")
        for parent in ([extends] if isinstance(extends, str) else extends or []):
            if isinstance(parent, str) and parent.startswith("."):
                read((path.parent / parent).resolve(), depth + 1)
        for reference in data.get("references") or []:
            if isinstance(reference, dict) and isinstance(reference.get("path"), str):
                target = (path.parent / reference["path"]).resolve()
                read(target / "tsconfig.json" if target.is_dir() else target, depth + 1)
    for name in ("tsconfig.json", "jsconfig.json"):
        read((project_dir / name).resolve())
    _ALIASES[project_dir] = sorted(found.items(), key=lambda item: -len(item[0]))
    return _ALIASES[project_dir]


def _aliased(project_dir: Path, spec: str) -> list[Path]:
    """The paths an aliased specifier names (`@/x` with `"@/*": ["src/*"]`), or [] when no alias matches."""
    for prefix, targets in aliases(project_dir):
        if prefix and spec.startswith(prefix):
            return [target / spec[len(prefix):] for target in targets]
    return []


def _module_file(project_dir: Path, rel: str, spec: str, resolved: str | None, in_snapshot: set) -> str | None:
    """The project module a script's import loads: TypeScript's resolution, else a relative path with the script
    extensions tried in order (a component, which TypeScript does not resolve)."""
    if resolved:
        try:
            target = Path(resolved).resolve().relative_to(project_dir).as_posix()
        except ValueError:
            return None
        return target if target in in_snapshot else None
    spec = spec.split("?")[0]
    bases = [(project_dir / rel).parent / spec] if spec.startswith(".") else _aliased(project_dir, spec)
    for candidate in [found for base in bases for found in
                      [base, *(base.with_name(base.name + ext) for ext in SCRIPT_SUFFIXES),
                       *(base / f"index{ext}" for ext in SCRIPT_SUFFIXES)]]:
        try:
            target = candidate.resolve().relative_to(project_dir).as_posix()
        except ValueError:
            continue
        if target in in_snapshot and candidate.is_file():
            return target
    return None


def _component_file(project_dir: Path, importer: str, spec: str, name: str, in_snapshot: set) -> str | None:
    """The component file an import binds `name` to: the module itself, or, through a barrel
    (`export { default as Name } from "./Name/index.vue"`), the file the barrel re-exports."""
    target = _module_file(project_dir, importer, spec, None, in_snapshot)
    if target is None or target.endswith((".vue", ".svelte", ".astro")):
        return target
    try:
        text = (project_dir / target).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for match in re.finditer(r"export\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", text):
        if re.search(r"\bdefault\s+as\s+" + re.escape(name) + r"\b", match.group(1)):
            return _module_file(project_dir, target, match.group(2), None, in_snapshot)
    return None


def _page_file(project_dir: Path, ref: dict, in_snapshot: set):
    """(file, chain) an EJS include or a `<script src>` loads, or None: an include is relative to the including
    template (`.ejs` added when it has no extension); a script source is a URL, relative or a path (`url-suffix`)."""
    spec = ref["name"].split("?")[0].split("#")[0]
    if ref["kind"] in ("include", "template"):
        base = (project_dir / ref["file"]).parent / spec
        for candidate in (base, base.with_name(base.name + ".ejs")):
            try:
                target = candidate.resolve().relative_to(project_dir).as_posix()
            except ValueError:
                continue
            if target in in_snapshot:
                return target, None
        return None
    if re.match(r"^[a-z][\w+.-]*:|^//", spec, re.I):
        return None
    if spec.startswith("/"):
        found = [rel for rel in _url_path(project_dir, spec) if rel in in_snapshot]
        return (found[0], "url-suffix") if len(found) == 1 else None
    try:
        target = ((project_dir / ref["file"]).parent / spec).resolve().relative_to(project_dir).as_posix()
    except ValueError:
        return None
    return (target, None) if target in in_snapshot else None


def load_units(refs: list, imports: dict, loads: dict, in_snapshot: set, read: set) -> dict:
    """For every file, the sets of what is loaded together with it, each set one unit stated by the code: a page
    (an HTML or EJS file no template includes, with its includes, the sheets they link or hold, the scripts they
    load and what those import) or a module bundle no page loads (a script or component nothing imports, with every
    module it imports, the sheets those import and the component style blocks among them). A sheet brings what it
    imports. Tailwind's utilities (`tailwindcss`) come with any sheet that loads Tailwind."""
    includes, scripts, sheets = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
    for ref in refs:
        found = imports.get(id(ref))
        if ref["kind"] == "include" and found:
            includes[ref["file"]].add(found[0])
        elif ref["kind"] == "script" and found:
            scripts[ref["file"]].add(found[0])
        elif ref["kind"] == "import" and ref.get("package") == "tailwindcss":
            sheets[ref["file"]].add("tailwindcss")
        elif ref["kind"] == "import" and found:
            if found[0] == "project":
                sheets[ref["file"]].add(found[1])
            elif found[0] == "ambiguous":
                sheets[ref["file"]].update(found[1])
            elif found[0] in ("external", "remote"):
                sheets[ref["file"]].add(found[1])
                if isinstance(found[2], dict) and found[2].get("package") == "tailwindcss":
                    sheets[ref["file"]].add("tailwindcss")

    def closure(starts, edges):
        seen, queue = set(), list(starts)
        while queue:
            current = queue.pop()
            if current not in seen:
                seen.add(current)
                queue += sorted(edges.get(current, ()))
        return seen

    def unit(files):
        members = set(files)
        for f in files:
            members |= closure(sheets.get(f, ()), sheets)
        return frozenset(members)

    markup = {rel for rel in read if rel.lower().endswith(MARKUP)}
    included = {target for targets in includes.values() for target in targets}
    entries = {target for targets in scripts.values() for target in targets}
    modules = {rel for rel in in_snapshot if rel.lower().endswith(SCRIPT_SUFFIXES)}
    imported = {target for targets in loads.values() for target in targets}
    units = []
    for page in sorted(markup - included):
        templates = closure([page], includes)
        bundle = closure([s for t in templates for s in scripts.get(t, ())], loads)
        units.append(unit(templates | bundle))
    for root in sorted(modules - imported - entries):
        units.append(unit(closure([root], loads)))
    by_file = collections.defaultdict(list)
    for members in units:
        for member in members:
            by_file[member].append(members)
    return by_file


def graph(project_dir: Path, records: list, tailwind: dict | None, files: list[str], engines: list[dict],
          missing: dict) -> dict:
    """The common graph from the three adapters' records: nodes, arcs (`uncertain` with every candidate when the
    cascade picks one at run time), holes; Tailwind's verdict on class tokens in `tailwind`."""
    project_dir = Path(project_dir).resolve()
    nodes, edges, holes, refs = {}, [], [], []
    names = collections.defaultdict(list)
    tailwind = tailwind or {}
    valid, version = set(tailwind.get("valid") or ()), tailwind.get("version")
    in_snapshot, read, cssinjs = set(files), set(), {}
    pending, sheets = {}, set()  # external names, made into nodes when a reference reaches them; sheets read
    sheet_of = {}  # an external name: the sheet that declares it

    def node(identity, kind, rel, line, external=None):
        return nodes.setdefault(identity, {"id": identity, "kind": kind, "file": rel, "line": line,
                                           "external": external})

    owned = collections.defaultdict(list)  # a node's names

    def add(record):
        node(record["id"], record["kind"], record["file"], record["line"])
        for key in map(tuple, record["names"]):
            if record["id"] not in names[key]:
                names[key].append(record["id"])
                owned[record["id"]].append(key)

    def hole(site, kind, cls, name, reason="-"):
        holes.append({"site": site, "name": name, "kind": kind, "class": cls, "reason": reason})

    generated, interpolated = {}, []  # (node, name key): the loop it came from; compile-time selector patterns
    loads = collections.defaultdict(set)  # a script module: the project modules it loads
    literals, guarded = {}, set()  # Less: a variable node's literal value; mixins with a guard
    for record in records:  # first pass: every declaration, so that the second resolves against all of them
        kind, rel = record["t"], record.get("file")
        site = f"{rel}:{record['line']}" if "line" in record else None
        if kind == "file":
            read.add(rel)
        elif kind == "node":
            add(record)
            for key in map(tuple, record.get("generated", ())):
                generated[(record["id"], key)] = "selector built at compile time from literal values"
            if record.get("literal") is not None:
                literals[record["id"]] = record["literal"]
            if record.get("guard"):
                guarded.add(record["id"])
        elif kind == "interpolated":
            interpolated += [(pattern, site) for pattern in record["patterns"]]
        elif kind == "module":
            target = _module_file(project_dir, rel, record["spec"], record.get("to"), in_snapshot)
            if target:
                loads[rel].add(target)
        elif kind == "template":
            refs.append(_ref("template", record["spec"], record["spec"], rel, record["line"], rel))
        elif kind == "ref":
            refs.append(record)
        elif kind == "hole":
            hole(site, record["kind"], record["cls"], record["name"])
        elif kind == "classes":
            found, gaps = tokens(record["alts"])
            for token, chain, line in found:
                line = line or record["line"]
                refs.append(_ref(record["kind"], token, ("." if record["kind"] == "class" else "#") + token, rel,
                                 line, record.get("from", rel), [*record["chain"], *chain],
                                 scopes=record.get("scopes") or []))
                utility = stylesheet._split_variant(token.lstrip("!"))[1]
                custom = re.match(r"!?\[(--[A-Za-z0-9_-]+):.+\]!?$", utility)
                if record["kind"] == "class" and token in valid and custom:  # a Tailwind arbitrary property
                    add(_node(f"{rel}:{line} {token}", "custom-property", rel, line,
                              [("custom-property", custom.group(1))]))
            for cls, name, line in gaps:
                hole(f"{rel}:{line or record['line']}", record["kind"], cls, name)
        elif kind == "member":
            refs.append(_ref("module-member", record["name"], "." + record["name"], rel, record["line"], rel,
                             spec=record["spec"], scope=record.get("scope")))
        elif kind == "decl":
            for item in declaration(rel, record["line"], rel, record["property"], record["value"],
                                    chain=[record["via"]], script=True):
                (add if item["t"] == "node" else refs.append)(item)
        elif kind == "text":
            refs += var_refs(record["text"], rel, record["line"], rel, ["css-text"], strings=False)
        elif kind == "import":
            refs.append(_ref("import", record["spec"], record["spec"], rel, record["line"], rel, script=True))
        elif kind == "cssinjs":
            tree = [{"t": "rule", "line": record["line"], "sel": [record["root"]], "kids": record["tree"]}] \
                if record["root"] else record["tree"]
            for item in tree_records(rel, tree, "css"):
                if item["t"] == "node":
                    add(item)
                elif item["t"] == "ref":
                    refs.append(item)
        elif kind == "cssinjs-text":
            text = record["text"] if record["global"] else "&{" + record["text"] + "}"
            for item in _sheet(rel, text, "scss", offset=record["line"] - 1):
                if item["t"] == "node" and "__dd" in item["id"]:
                    label = item["id"].split(" ", 1)[1]
                    for key, expression in record["holes"].items():
                        label = label.replace(key, "${" + expression + "}")
                    hole(f"{rel}:{item['line']}", "rule", "interpolated-selector", label)
                    item = {**item, "names": [n for n in item["names"] if "__dd" not in n[1]]}
                if item["t"] == "node":
                    add(item)
                elif item["t"] == "ref":
                    refs.append(item)
        elif kind == "css-in-js":
            text = stylesheet._without_strings_and_brackets(record["selector"])
            for match in stylesheet._CLASS_OR_ID_RE.finditer(text):
                key = ("class" if match.group(0)[0] == "." else "id", stylesheet._decode_escapes(match.group(1)))
                cssinjs.setdefault(key, site)
    for rel in sorted(read):
        node(rel, "module", rel, 1)

    def external_sheet(identity, external, text, rel, path, dialect):
        """The names a sheet from outside the snapshot declares, as external nodes made when a reference reaches
        them (`<sheet> .class`, `<sheet> --x`...); its own imports followed."""
        if identity in sheets:
            return
        sheets.add(identity)
        node(identity, "module", rel, 1 if rel else None, external)
        for record in _sheet(identity, text, dialect):
            if record["t"] == "ref" and record["kind"] == "import" and "package" not in record:
                if re.match(r"^https?:", identity):  # a CDN sheet names its imports relative to its URL
                    url = urllib.parse.urljoin(identity, record["name"])
                    found = ("remote", url, remote_package(url))
                else:
                    found = resolve(project_dir, rel or identity, record["name"], base=Path(path).parent)
                if found[0] == "hole":
                    hole(record["site"], "import", found[1], record["symbol"], found[2])
                load(found, record)
            if record["t"] != "node":
                continue
            for key in map(tuple, record["names"]):
                if key[0] not in ("class", "id", "custom-property", "keyframes", "font-face", "container"):
                    continue  # a package's Sass variables and mixins: not read
                label = ({"class": ".", "id": "#"}.get(key[0], "") + key[1]
                         if key[0] in ("class", "id", "custom-property") else
                         f"container {key[1]}" if key[0] == "container" else f"@{key[0]} {key[1]}")
                target = f"{identity} {label}"
                pending.setdefault(target, {"id": target, "kind": key[0], "file": rel,
                                            "line": record["line"] if rel else None, "external": external})
                sheet_of[target] = identity
                if target not in names[key]:
                    names[key].append(target)

    def load(found, ref):
        """Read the sheet an import reaches when it is outside the snapshot: a checkout file, a package, a URL."""
        rels = [found[1]] if found[0] == "project" else found[1] if found[0] == "ambiguous" else []
        for rel in rels:
            if rel not in in_snapshot and rel.lower().endswith(STYLESHEETS):
                try:
                    text = (project_dir / rel).read_text(encoding="utf-8")
                except (OSError, UnicodeError) as error:
                    hole(ref["site"], "import", "not-read", ref["symbol"], repr(error)[:200])
                    continue
                external_sheet(rel, sheet_package(text, rel), text, rel, project_dir / rel, stylesheet.dialect_for(rel))
        if found[0] == "external" and found[3] is not None and str(found[3]).lower().endswith(STYLESHEETS):
            text = Path(found[3]).read_text(encoding="utf-8", errors="replace")
            external_sheet(found[1], found[2], text, None, found[3], stylesheet.dialect_for(str(found[3])))
        elif found[0] == "remote" and found[1] not in sheets:
            text = _download(found[1])
            if text is not None:
                external = dict(found[2])
                banner = BANNER_RE.match(text[:600])
                if external["version"] == "unknown" and banner:
                    external.update({"version": banner.group(2), "from": "banner"})
                external_sheet(found[1], external, text, None, found[1], "css")

    sass = collections.defaultdict(lambda: {"use": {}, "forward": [], "import": [], "builtin": {}})
    less_imports, options = collections.defaultdict(list), collections.defaultdict(list)
    imports = {}
    for ref in refs:  # imports first: Sass scopes, CSS Module members and external sheets need them
        if ref["kind"] in ("include", "script", "template"):
            imports[id(ref)] = _page_file(project_dir, ref, in_snapshot)
            if ref["kind"] == "template" and imports[id(ref)]:
                loads[ref["file"]].add(imports[id(ref)][0])
        if ref["kind"] == "import" and "package" not in ref:
            imports[id(ref)] = found = resolve(project_dir, ref["file"], ref["name"], ref.get("script", False),
                                               sass=True if ref.get("sass") or ref.get("less") else None)
            load(found, ref)
            if found[0] == "external" and ref.get("sass") == "use" and found[2].get("manager") == "sass":
                sass[ref["file"]]["builtin"][ref["ns"]] = found[1]
            if found[0] == "project" and ref.get("less") == "import":
                less_imports[ref["file"]].append(found[1])
                options[found[1]].append(set(ref.get("options") or ()))
            if found[0] == "project" and ref.get("sass"):
                if ref["sass"] == "use":
                    sass[ref["file"]]["use"][ref["ns"]] = found[1]
                elif ref["sass"] == "forward":
                    sass[ref["file"]]["forward"].append((found[1], ref.get("prefix") or "", ref.get("show"),
                                                         ref.get("hide")))
                else:
                    sass[ref["file"]]["import"].append(found[1])
    def composes_scope(ref):
        """Where a `composes` names its classes: the module itself, global (None) or another file."""
        if ref["origin"] is None:
            return ref["module"]
        if ref["origin"] == "global":
            return None
        found = resolve(project_dir, ref["file"], ref["origin"])
        return found[1] if found[0] == "project" else ("unresolved", ref["origin"])
    composes = collections.defaultdict(list)
    for ref in refs:
        if ref["kind"] == "composes":
            for key in owned[ref["from"]]:
                if key[0] == "class" and key[2] == ref["module"]:
                    composes[(key[2], key[1])].append((composes_scope(ref), ref["name"]))

    units = load_units(refs, imports, loads, in_snapshot, read)
    patterns = {key: found for key, found in names.items() if key[0] == "utility-pattern"}
    patterns = {(key[0], key[1]): found for key, found in patterns.items()}
    for ref in list(refs):  # a class token's custom variants (`pointer-coarse:p-2`) name them
        if ref["kind"] == "class" and ":" in ref["name"]:
            chain_ = stylesheet._split_variant(ref["name"].lstrip("!"))[0]
            for variant in dict.fromkeys(part for part in chain_.split(":") if ("variant", part) in names):
                refs.append(_ref("variant", variant, variant, ref["file"], int(ref["site"].rsplit(":", 1)[1]),
                                 ref["from"]))

    def loaded(site_file, target):
        sheet = sheet_of.get(target) or ("tailwindcss" if target.startswith("tailwindcss ") else
                                         nodes[target]["file"] if target in nodes else None)
        if sheet is None or sheet == site_file:
            return True
        return any(sheet in unit for unit in units.get(site_file, ()))

    def tailwind_node(name):
        return node(f"tailwindcss {name}", "class" if not name.startswith("@") else "layer", None, None,
                    {"manager": "npm", "package": "tailwindcss", "version": version})["id"]

    def closure(start, keys):
        seen, queue = [], [start]
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.append(current)
            for key in keys:
                queue += [item[0] if isinstance(item, tuple) else item for item in sass[current][key]]
        return seen

    def members(module, name, key, seen=None):
        """A module's members of that name: its own, then those its `@forward`s make visible (prefix, show, hide)."""
        seen = set() if seen is None else seen
        if (module, name) in seen:
            return []
        seen.add((module, name))
        found = list(names[(key, name, module)])
        bare = name[1:] if name.startswith("$") else name
        for target, prefix, show, hide in sass[module]["forward"]:
            if prefix and not bare.startswith(prefix):
                continue
            inner = ("$" if name.startswith("$") else "") + bare[len(prefix):]
            if (show is not None and inner not in show) or (hide is not None and inner in hide):
                continue
            found += members(target, inner, key, seen)
        return found

    importers = collections.defaultdict(set)
    for rel_, scope_ in list(sass.items()):
        for target in scope_["import"]:
            importers[target].add(rel_)

    def import_group(start):
        """Every file joined to this one by `@import`, either way: one compilation shares their globals."""
        seen, queue = [], [start]
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.append(current)
            queue += sass[current]["import"] + sorted(importers[current])
        return seen

    less_importers = collections.defaultdict(set)
    for rel_, targets_ in list(less_imports.items()):
        for target in targets_:
            less_importers[target].add(rel_)
    # A Less file every import of which is `(reference)`: its rules are output only where extended or called.
    reference_only = {rel_ for rel_, sets in options.items() if sets and all("reference" in o for o in sets)}

    def less_group(start):
        seen, queue = [], [start]
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.append(current)
            queue += less_imports[current] + sorted(less_importers[current])
        return seen

    def less_variable(rel, name):
        """The declarations a Less variable reads: lazy evaluation keeps the last one of a file; declarations in
        several files of one compilation leave the order to the import order (uncertain)."""
        found = [target for f in less_group(rel) for target in names[("less-variable", name, f)]]
        by_file = collections.defaultdict(list)
        for target in found:
            by_file[nodes[target]["file"]].append(target)
        last = [max(group, key=lambda target: nodes[target]["line"]) for group in by_file.values()]
        return last, ("Less: the last declaration in import order wins" if len(last) > 1 else None)

    def sass_targets(ref, key):
        ns, rel, name = ref.get("ns"), ref["file"], ref["name"]
        if ns is not None:
            if ns in sass[rel]["builtin"]:
                node(sass[rel]["builtin"][ns], "module", None, None,
                     {"manager": "sass", "package": sass[rel]["builtin"][ns], "version": None})
                return [(sass[rel]["builtin"][ns], ())], None
            module = sass[rel]["use"].get(ns)
            return ([(target, ()) for target in members(module, name, key)] if module else []), None
        found = [target for f in closure(rel, ("import",)) for target in names[(key, name, f)]]
        if "*" in sass[rel]["use"]:
            found += members(sass[rel]["use"]["*"], name, key)
        chain = ()
        if not found:
            found, chain = [target for f in import_group(rel) for target in names[(key, name, f)]], ("import-group",)
        found = list(dict.fromkeys(found))
        return [(target, chain) for target in found], ("Sass scope: several declarations" if len(found) > 1 else None)

    values = {}  # (module, local name): (origin module, origin name), from `@value ... from`
    for ref in refs:
        if ref["kind"] == "css-value" and ref.get("origin"):
            found = resolve(project_dir, ref["file"], ref["origin"])
            if found[0] == "project":
                values[(ref["module"], ref["local"])] = (found[1], ref["name"])

    def member(module, name):
        out, seen, queue = [], set(), [(module, name, ())]
        out += [(target, ()) for target in names[("export", name, module)] + names[("css-value", name, module)]]
        if (module, name) in values:
            origin = values[(module, name)]
            out += [(target, ("from",)) for target in names[("css-value", origin[1], origin[0])]]
        while queue:
            scope, current, chain = queue.pop(0)
            if (scope, current) in seen:
                continue
            seen.add((scope, current))
            out += [(target, chain) for target in names[("class", current, scope)]]
            for target_scope, composed in composes.get((scope, current), ()):
                queue.append((target_scope, composed, (*chain, "composes")))
        return out

    seen = set()
    for ref in refs:
        kind, name = ref["kind"], ref["name"]
        targets, uncertain = [], None
        if "to" in ref:
            targets = [(ref["to"], ())]
        elif kind in ("include", "script", "template"):
            found = imports[id(ref)]
            if found is None:
                hole(ref["site"], kind, "unresolved-import", ref["symbol"], "no file of the snapshot")
                continue
            targets = [(found[0], (found[1],) if found[1] else ())]
            node(found[0], "module", found[0], 1)
        elif kind == "import":
            found = ("external", "tailwindcss", {"manager": "npm", "package": "tailwindcss", "version": version},
                     None) if ref.get("package") else imports[id(ref)]
            if found[0] == "hole":
                hole(ref["site"], kind, found[1], ref["symbol"], found[2])
                continue
            if found[0] in ("external", "remote"):
                node(found[1], "module", None, None, found[2])
                targets = [(found[1], ())]
                if found[0] == "remote" and found[1] not in sheets:
                    hole(ref["site"], kind, "not-read", ref["symbol"], "the sheet could not be downloaded")
            else:  # checkout files: a project module, or a sheet outside the snapshot read as external
                rels = [found[1]] if found[0] == "project" else found[1]
                for rel in rels:
                    node(rel, "module", rel, 1, None if rel in in_snapshot else
                         {"manager": "checkout", "package": "unknown", "version": "unknown", "from": None})
                targets = [(rel, (found[2],) if found[2] else ()) for rel in rels]
                uncertain = "a URL path several checkout files end with" if found[0] == "ambiguous" else None
        elif kind == "layer":
            targets = [(tailwind_node(f"@layer {name}"), ())]
        elif kind in ("class", "id"):
            targets = [(target, ()) for target in names[(kind, name, None)]]
            for scope, via in ref.get("scopes", ()):
                targets += [(target, tuple(via)) for target in names[(kind, name, scope)]]
            utility = stylesheet._split_variant(name.lstrip("!"))[1].strip("!")
            own = names[("utility", utility)] + [target for (key, prefix), found in patterns.items()
                                                 if utility.startswith(prefix) for target in found]
            targets += [(target, ()) for target in own] if kind == "class" else []
            if kind == "class" and NAMED_GROUP_RE.match(name) and tailwind.get("valid") is not None:
                targets.append((tailwind_node(name.split("/")[0]), ("named-group",)))
            elif kind == "class" and name in valid and not own:
                targets.append((tailwind_node(name), ()))
        elif kind == "module-member":
            found = ("project", ref["scope"], None) if ref.get("scope") else \
                resolve(project_dir, ref["file"], ref["spec"], script=True)
            if found[0] != "project":
                hole(ref["site"], kind, "unresolved-import", ref["symbol"], ref["spec"])
                continue
            targets = member(found[1], name)
        elif kind == "composes":
            targets = [(target, ()) for target in names[("class", name, composes_scope(ref))]]
        elif kind in ("custom-property", "keyframes", "container"):
            targets = [(target, ()) for target in names[(kind, name)]]
            if len(targets) > 1:
                uncertain = {"custom-property": "cascade and inheritance pick one per element",
                             "keyframes": "the last in cascade order wins",
                             "container": "the nearest ancestor container wins"}[kind]
        elif kind == "font-face":
            targets = [(target, ()) for target in names[(kind, name)]]
        elif ref.get("stylus"):
            key = "stylus-variable" if kind == "stylus-variable" else "stylus-mixin"
            targets = [(target, ()) for f in less_group(ref["file"]) for target in names[(key, name, f)]]
            if not targets and ref.get("optional"):
                continue  # a keyword or a function of Stylus, not a name the project declares
            if len(targets) > 1:
                uncertain = "Stylus: the definition in force where it is used is decided in order"
        elif kind in ("sass-variable", "mixin", "function") and not ref.get("less"):
            targets, uncertain = sass_targets(ref, kind)
            if not targets and kind == "function" and ref.get("ns") is None:
                continue  # a CSS or global Sass function, not a name the project declares
        elif kind == "placeholder":
            targets = [(target, ()) for target in names[("placeholder", name, None)]]
        elif kind == "less-variable":
            first, uncertain = less_variable(ref["file"], name[1:] if name.startswith("@@") else name)
            targets = [(target, ()) for target in first]
            if name.startswith("@@"):
                for target in first:
                    if literals.get(target):
                        second, again = less_variable(ref["file"], "@" + literals[target])
                        targets += [(found, ("variable-variable",)) for found in second]
                        uncertain = uncertain or again
        elif kind == "mixin" and ref.get("less"):
            found = []
            for alt in ref.get("alts") or [name]:  # the innermost scope that defines it wins
                found = list(dict.fromkeys(target for f in less_group(ref["file"])
                                           for target in names[("less-mixin", alt, f)]))
                if found:
                    break
            targets = [(target, ()) for target in found]
            if len(found) > 1 or any(target in guarded for target in found):
                uncertain = "Less: every definition whose arity and guard match is applied"
        elif kind == "custom-media":
            targets = [(target, ()) for target in names[("custom-media", name)]]
        elif kind == "custom-selector":
            targets = [(target, ()) for target in names[("custom-selector", name)]]
        elif kind == "css-value":
            if ref.get("origin"):
                origin = values.get((ref["module"], ref["local"]))
                targets = [(target, ()) for target in names[("css-value", origin[1], origin[0])]] if origin else []
            else:
                targets = [(target, ()) for target in names[("css-value", name, ref["module"])]]
                origin = values.get((ref["module"], name))
                if not targets and origin:
                    targets = [(target, ("from",)) for target in names[("css-value", origin[1], origin[0])]]
            if not targets and ref.get("optional"):
                continue  # a keyword, not one of the module's values
        elif kind == "variant":
            targets = [(target, ()) for target in names[("variant", name)]]
            if not targets and ref.get("optional"):
                continue  # one of Tailwind's own variants
        elif kind in ("source", "config"):
            path = ((project_dir / ref["file"]).parent / name).resolve()
            try:
                rel = path.relative_to(project_dir).as_posix()
            except ValueError:
                rel = None
            if rel is None or not path.exists():
                hole(ref["site"], kind, "unresolved-import", ref["symbol"], "no checkout path")
                continue
            node(rel, "directory" if path.is_dir() else "module", rel, None if path.is_dir() else 1)
            targets = [(rel, ())]
        elif kind == "plugin":
            base = (project_dir / ref["file"]).parent
            spec = name.split("?")[0]
            local = next((candidate for candidate in (base / spec, base / (spec + ".js")) if candidate.is_file()), None)
            if local is not None and local.resolve().is_relative_to(project_dir):
                rel = local.resolve().relative_to(project_dir).as_posix()
                node(rel, "module", rel, 1, None if rel in in_snapshot else
                     {"manager": "checkout", "package": "unknown", "version": "unknown", "from": None})
                targets = [(rel, ())]
            else:
                folder = _package(project_dir, base, spec.split("/")[0])
                if folder is not None:
                    meta = json.loads((folder / "package.json").read_text(encoding="utf-8")) \
                        if (folder / "package.json").is_file() else {}
                    node(spec, "module", None, None, {"manager": "npm", "package": spec, "version": meta.get("version")})
                    targets = [(spec, ())]
        if kind in ("class", "id") and targets:
            loops = [generated[(target, (kind, name, None))] for target, _ in targets
                     if (target, (kind, name, None)) in generated]
            if loops:
                uncertain = loops[0]
            elif any(nodes[target]["file"] in reference_only for target, _ in targets if target in nodes):
                uncertain = "imported with (reference): output only where extended or called as a mixin"
        if not targets:
            cls = {"class": "no-rule", "id": "no-rule", "module-member": "unknown-member", "composes": "no-rule",
                   "custom-property": "undeclared", "keyframes": "no-keyframes", "font-face": "no-font-face",
                   "container": "no-container", "sass-variable": "undeclared", "mixin": "undeclared",
                   "function": "undeclared", "placeholder": "no-placeholder", "less-variable": "undeclared",
                   "v-bind": "undeclared", "variant": "undeclared", "custom-media": "undeclared",
                   "stylus-variable": "undeclared", "custom-selector": "undeclared", "css-value": "undeclared",
                   "plugin": "unresolved-import"}[kind]
            reason = f"fallback {ref['fallback']}" if ref.get("fallback") else "-"
            if kind in ("class", "id") and (kind, name) in cssinjs:
                cls, reason = "css-in-js", f"a selector key of a script's object literal at {cssinjs[(kind, name)]}"
            elif kind == "class" and tailwind.get("valid") is not None and NAMED_GROUP_RE.match(name):
                cls, reason = "tailwind-named-group", f"Tailwind {version}: a variant anchor, not a utility"
            elif kind in ("class", "id") and any(
                    {"class": ".", "id": "#"}[kind] == mark and (prefix or suffix) and name.startswith(prefix)
                    and name.endswith(suffix) and len(name) > len(prefix) + len(suffix)
                    for (mark, prefix, suffix), _ in interpolated):  # a bare `.#{$x}` would claim every name
                where = next(site for (mark, prefix, suffix), site in interpolated
                             if (prefix or suffix) and name.startswith(prefix) and name.endswith(suffix))
                cls, reason = "interpolated-selector", f"a selector built at compile time at {where} may name it"
            hole(ref["site"], kind, cls, name if kind in ("class", "id", "module-member", "composes") else ref["symbol"],
                 reason)
            continue
        candidates = sorted(dict.fromkeys(target for target, _ in targets)) if uncertain else None
        for target, _ in targets:
            if target not in nodes:
                nodes[target] = dict(pending[target])
        for target, chain in dict.fromkeys(targets):
            chain = (*ref["chain"], *chain)
            if (ref["from"], target, ref["site"], kind, ref["symbol"], chain) in seen:
                continue  # the same name twice on one line is one arc
            seen.add((ref["from"], target, ref["site"], kind, ref["symbol"], chain))
            edge = {"from": ref["from"], "to": target, "site": ref["site"], "kind": kind, "chain": list(chain),
                    "end": "external" if nodes[target]["external"] else "project", "symbol": ref["symbol"]}
            reason = uncertain
            if kind in LOADED_KINDS and not COMPILE_TIME & set(chain) and not loaded(ref["file"], target):
                reason = f"{uncertain}; sheet-not-proven-loaded" if uncertain else "sheet-not-proven-loaded"
            if reason:
                # The candidates are those one cascade or one compilation picks among; a sheet not proven loaded
                # has none to pick: its arc stands alone (listing every rule of a class on every arc is quadratic).
                edge["uncertain"] = {"reason": reason, **({"candidates": candidates} if uncertain else {})}
            edges.append(edge)
    # Read completely: a file read in part (`PARTLY`) is listed as missing with what is left out.
    names_read = (read | {rel for rel in files if rel.lower().endswith(css_typescript.SUFFIXES)}) - set(missing)
    indexed = [rel for rel in files if rel in names_read]
    lost = [{"path": rel, "reason": missing.get(rel) or "not read"} for rel in files if rel not in names_read]
    return {"language": "css",
            "indexer": {"name": " + ".join(engine["name"] for engine in engines),
                        "version": " + ".join(str(engine.get("version")) for engine in engines),
                        "seconds": round(sum(engine.get("seconds") or 0 for engine in engines), 1),
                        "peak_mb": max((engine.get("peak_mb") or 0 for engine in engines), default=None)},
            "engines": engines,
            "files": {"snapshot": len(files), "indexed": len(indexed), "missing": lost},
            "nodes": list(nodes.values()), "edges": edges, "holes": holes, "removed": []}
