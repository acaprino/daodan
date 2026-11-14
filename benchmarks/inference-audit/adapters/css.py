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
  project, or of a package (external);
- in a CSS Module `styles.foo` names the module's local `.foo` rules and, through `composes`, the rules of what
  it composes; in Sass `$x`, `ns.$x` and `@include` name variables and mixins through `@use`, `@forward`, `@import`.
A name nothing declares is a hole with its class; a class built at run time (template, concatenation, a value
the TypeScript checker cannot state) is a hole, never a guess. An arc's `chain` lists the rules that led from
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
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scip_graph  # noqa: E402,F401  (puts the plugin's scripts on the path)
from languages import stylesheet  # noqa: E402

from . import css_tailwind, css_typescript  # noqa: E402

STYLESHEETS = (".css", ".scss", ".less")
MARKUP = (".html", ".htm", ".ejs")
MODULE_RE = re.compile(r"\.module\.(?:css|scss|sass|less)$", re.I)
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
MODE_RE = re.compile(r":(global|local)\b(\()?|(\()|(\))")
WORD_RE = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s(]+(?:\([^)]*\))?|\([^)]*\)")
SIZE_RE = re.compile(r"(?:^|\s)(?:[+-]?[\d.]+[a-z%]*|xx-small|x-small|small|medium|large|x-large|xx-large|"
                     r"xxx-large|smaller|larger)(?:\s*/\s*[^\s,]+)?\s+(?=\S)", re.I)
EJS_RE = re.compile(r"<%.*?%>", re.S)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def walk(project_dir: Path) -> list[str]:
    """The files the three adapters read, outside `node_modules` and dot directories."""
    suffixes = STYLESHEETS + MARKUP + css_typescript.SUFFIXES
    return sorted(path.relative_to(project_dir).as_posix() for path in Path(project_dir).rglob("*")
                  if path.is_file() and path.suffix.lower() in suffixes
                  and not any(part == "node_modules" or part.startswith(".")
                              for part in path.relative_to(project_dir).parts))


def run(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The three adapters over a project, then the graph."""
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    files = walk(project_dir) if files is None else files
    own = index(project_dir, work_dir, files)
    scripts = css_typescript.index(project_dir, work_dir, [rel for rel in files
                                                           if rel.lower().endswith(css_typescript.SUFFIXES)])
    records = own["records"] + scripts["records"]
    tailwind = css_tailwind.index(project_dir, work_dir, sorted(class_tokens(records)))
    return graph(project_dir, records, tailwind, files, [own["indexer"], scripts["indexer"], tailwind["indexer"]],
                 {**own["missing"], **scripts["missing"]})


# Reading: stylesheets and markup into records.

def index(project_dir: Path, work_dir: Path | None = None, files: list[str] | None = None) -> dict:
    """Records of every stylesheet and HTML/EJS file: `node`, `ref`, `classes`, `hole` and `file`."""
    begun = time.time()
    project_dir = Path(project_dir)
    records, missing = [], {}
    for rel in files if files is not None else walk(project_dir):
        lower = rel.lower()
        if not lower.endswith(STYLESHEETS + MARKUP):
            continue
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


def _sheet(rel: str, text: str, dialect: str, offset: int = 0, inline: bool = False) -> list[dict]:
    """One stylesheet, or a `<style>` block (`offset` lines down) or a style attribute (`inline`)."""
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
    module = rel if MODULE_RE.search(rel) else None
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
                out.append(_node(here, "rule", rel, line, _selector_names(node.selectors, module)))
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


def _selector_names(selectors: list[str], module: str | None) -> list[tuple]:
    """(class or id, name, scope) of every class and id a rule's selectors name: scope None for a global name, the
    module's path for a CSS Module's local one (`:global(...)` and `:global` make it global)."""
    names = set()
    for selector in selectors:
        text = stylesheet._without_strings_and_brackets(selector)
        events = sorted([(m.start(), 0, m) for m in MODE_RE.finditer(text)] +
                        [(m.start(), 1, m) for m in stylesheet._CLASS_OR_ID_RE.finditer(text)
                         if not text.startswith(("#{", "@{"), m.end())], key=lambda item: item[:2])
        mode, stack = "local", []
        for _, kind, match in events:
            if kind == 1:
                scope = module if module and mode == "local" else None
                names.add(("class" if match.group(0)[0] == "." else "id",
                           stylesheet._decode_escapes(match.group(1)), scope))
            elif match.group(1):
                if match.group(2):
                    stack.append(mode)
                mode = match.group(1)
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
        for name, value in attrs:
            if value is None:
                continue
            values[name] = value
            if name in ("class", "id"):
                parts, last = [], 0
                for match in EJS_RE.finditer(value):
                    parts += [{"s": value[last:match.start()]}, {"h": "ejs", "x": match.group(), "ctx": "ejs"}]
                    last = match.end()
                parts.append({"s": value[last:]})
                self.out.append({"t": "classes", "kind": name, "file": self.rel, "line": at(name), "from": self.rel,
                                 "chain": [], "alts": [parts]})
            elif name == "style":
                self.out += _sheet(self.rel, "x{" + value + "}", "css", offset=at(name) - 1, inline=True)
        if tag == "link" and "stylesheet" in values.get("rel", "").lower().split() and values.get("href"):
            self.out.append(_ref("import", values["href"], values["href"], self.rel, at("href"), self.rel))
        self.in_style = tag == "style"

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.out += _sheet(self.rel, data, "css", offset=self.getpos()[0] - 1)


def _markup(rel: str, text: str) -> list[dict]:
    parser = _Markup(rel)
    parser.feed(text)
    parser.close()
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
                holes.setdefault((form, "".join(p["s"] if "s" in p else p["x"] if p.get("ctx") == "ejs"
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
    extensions = ("", ".scss", ".sass", ".css", ".less") if sass else ("", ".css")
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


def resolve(project_dir: Path, rel: str, spec: str, script: bool = False):
    """Where an import leads: `("project", rel)`, `("external", id, package dict)` or `("hole", class, reason)`.

    A stylesheet or HTML file names a URL relative to itself (Sass and LESS also try partials and their own
    extensions), then a package; a script's bare specifier is a package; `~` names a package."""
    clean = spec.split("?")[0].split("#")[0].strip()
    if clean.startswith("sass:"):
        return "external", clean, {"manager": "sass", "package": clean, "version": None}
    if re.match(r"^[A-Za-z][\w+.-]*:", clean) or clean.startswith("//"):
        return "hole", "remote-url", clean
    if clean.startswith("/"):
        return "hole", "url-path", "a URL path the server maps, not a file"
    sass = rel.lower().endswith((".scss", ".sass", ".less"))
    base = (project_dir / rel).parent
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
                return "project", inside
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
        {"manager": "npm", "package": name, "version": meta.get("version")}


def graph(project_dir: Path, records: list, tailwind: dict | None, files: list[str], engines: list[dict],
          missing: dict) -> dict:
    """The common graph from the three adapters' records: nodes, arcs (`uncertain` with every candidate when the
    cascade picks one at run time), holes; Tailwind's verdict on class tokens in `tailwind`."""
    project_dir = Path(project_dir).resolve()
    nodes, edges, holes, refs = {}, [], [], []
    names = collections.defaultdict(list)
    tailwind = tailwind or {}
    valid, version = set(tailwind.get("valid") or ()), tailwind.get("version")
    read = set()

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

    for record in records:  # first pass: every declaration, so that the second resolves against all of them
        kind, rel = record["t"], record.get("file")
        site = f"{rel}:{record['line']}" if "line" in record else None
        if kind == "file":
            read.add(rel)
        elif kind == "node":
            add(record)
        elif kind == "ref":
            refs.append(record)
        elif kind == "hole":
            hole(site, record["kind"], record["cls"], record["name"])
        elif kind == "classes":
            found, gaps = tokens(record["alts"])
            for token, chain, line in found:
                line = line or record["line"]
                refs.append(_ref(record["kind"], token, ("." if record["kind"] == "class" else "#") + token, rel,
                                 line, record.get("from", rel), [*record["chain"], *chain]))
                utility = stylesheet._split_variant(token.lstrip("!"))[1]
                custom = re.match(r"!?\[(--[A-Za-z0-9_-]+):.+\]!?$", utility)
                if record["kind"] == "class" and token in valid and custom:  # a Tailwind arbitrary property
                    add(_node(f"{rel}:{line} {token}", "custom-property", rel, line,
                              [("custom-property", custom.group(1))]))
            for cls, name, line in gaps:
                hole(f"{rel}:{line or record['line']}", record["kind"], cls, name)
        elif kind == "member":
            refs.append(_ref("module-member", record["name"], "." + record["name"], rel, record["line"], rel,
                             spec=record["spec"]))
        elif kind == "decl":
            for item in declaration(rel, record["line"], rel, record["property"], record["value"],
                                    chain=[record["via"]], script=True):
                (add if item["t"] == "node" else refs.append)(item)
        elif kind == "text":
            refs += var_refs(record["text"], rel, record["line"], rel, ["css-text"], strings=False)
        elif kind == "import":
            refs.append(_ref("import", record["spec"], record["spec"], rel, record["line"], rel, script=True))
    for rel in sorted(read):
        node(rel, "module", rel, 1)

    sass = collections.defaultdict(lambda: {"use": {}, "forward": [], "import": []})
    imports = {}
    for ref in refs:  # imports first: Sass scopes and CSS Module members need them
        if ref["kind"] == "import" and "package" not in ref:
            imports[id(ref)] = found = resolve(project_dir, ref["file"], ref["name"], ref.get("script", False))
            if found[0] == "project" and ref.get("sass"):
                if ref["sass"] == "use":
                    sass[ref["file"]]["use"][ref["ns"]] = found[1]
                else:
                    sass[ref["file"]][ref["sass"]].append(found[1])
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
                queue += sass[current][key]
        return seen

    def member(module, name):
        out, seen, queue = [], set(), [(module, name, ())]
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
        elif kind == "import":
            found = ("external", "tailwindcss", {"manager": "npm", "package": "tailwindcss", "version": version}) \
                if ref.get("package") else imports[id(ref)]
            if found[0] == "hole":
                hole(ref["site"], kind, found[1], ref["symbol"], found[2])
                continue
            if found[0] == "external":
                node(found[1], "module", None, None, found[2])
            targets = [(found[1], ())]
        elif kind == "layer":
            targets = [(tailwind_node(f"@layer {name}"), ())]
        elif kind in ("class", "id"):
            targets = [(target, ()) for target in names[(kind, name, None)]]
            if kind == "class" and name in valid:
                targets.append((tailwind_node(name), ()))
        elif kind == "module-member":
            found = resolve(project_dir, ref["file"], ref["spec"], script=True)
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
        elif kind in ("sass-variable", "mixin"):
            ns, rel = ref.get("ns"), ref["file"]
            if ns is None:
                scope = closure(rel, ("import",))
                scope += [f for target in sass[rel]["use"].values() if "*" in sass[rel]["use"]
                          for f in closure(sass[rel]["use"]["*"], ("forward",))]
            else:
                scope = closure(sass[rel]["use"][ns], ("forward",)) if ns in sass[rel]["use"] else []
            key = "sass-variable" if kind == "sass-variable" else "mixin"
            targets = [(target, ()) for f in dict.fromkeys(scope) for target in names[(key, name, f)]]
            if len(targets) > 1:
                uncertain = "Sass scope: several declarations"
        if not targets:
            cls = {"class": "no-rule", "id": "no-rule", "module-member": "unknown-member", "composes": "no-rule",
                   "custom-property": "undeclared", "keyframes": "no-keyframes", "font-face": "no-font-face",
                   "container": "no-container", "sass-variable": "undeclared", "mixin": "undeclared"}[kind]
            reason = f"fallback {ref['fallback']}" if ref.get("fallback") else "-"
            hole(ref["site"], kind, cls, name if kind in ("class", "id", "module-member", "composes") else ref["symbol"],
                 reason)
            continue
        candidates = sorted(dict.fromkeys(target for target, _ in targets))
        for target, chain in dict.fromkeys(targets):
            chain = (*ref["chain"], *chain)
            if (ref["from"], target, ref["site"], kind, ref["symbol"], chain) in seen:
                continue  # the same name twice on one line is one arc
            seen.add((ref["from"], target, ref["site"], kind, ref["symbol"], chain))
            edge = {"from": ref["from"], "to": target, "site": ref["site"], "kind": kind, "chain": list(chain),
                    "end": "external" if nodes[target]["external"] else "project", "symbol": ref["symbol"]}
            if uncertain:
                edge["uncertain"] = {"reason": uncertain, "candidates": candidates}
            edges.append(edge)
    names_read = read | {rel for rel in files if rel.lower().endswith(css_typescript.SUFFIXES)} - set(missing)
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
