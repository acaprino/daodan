"""CSS, the graph of the stylesheets and of every place that names what they declare, on Modal.

Wiring only: the CSS adapters (`adapters/css*.py` and their `.js`: the product's stylesheet parser and the HTML parser,
the official parsers of Sass, Less and Stylus, the compilers of Vue, Svelte and Astro, the TypeScript compiler and
the project's Tailwind; `css.py` assembles the graph) and the volume. One container per case: the checkout at its
pinned commit, its files (tududi: the snapshot `modal_scip.py` kept, `scip-inputs/tududi/manifest.sqlite`; the others:
the walk of `css.walk`, the snapshot's perimeter), the pinned engines (`adapters/css_engines.json`, in the image), the
project's packages as the engine pass installs them (`npm ci --ignore-scripts`), then the graph and the hand check.
No model.

    modal deploy benchmarks/inference-audit/lang_css.py
    python benchmarks/inference-audit/lang_css.py spawn --cases tududi,bulma
    python benchmarks/inference-audit/lang_css.py fetch --cases tududi,bulma

Writes `results/graph-css-<case>-checks.json` (counts, hand check, run); the graph stays on the volume
(`inference-audit/graph-css-<case>.json.gz`, fetched beside the checks with `fetch --graph`).
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
import code_graph as scip_graph  # noqa: E402
from adapters import css  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")  # as modal_scip.py
CODE = tuple(sorted(path.name for path in (HERE / "adapters").glob("css*") if path.suffix in (".py", ".js", ".json")))
# One small project per family, pinned by commit (tududi from modal_audit.CASES).
CSS_CASES = {
    "tududi": CASES["tududi"],
    "bulma": {"repo": "https://github.com/jgthms/bulma.git", "commit": "e133d45b7a829b278d2613cd0591b793f2f69f13",
              "target": "."},  # 1.0.4: SCSS with @use, @forward and mixins; docs pages in HTML
    "bootstrap3": {"repo": "https://github.com/twbs/bootstrap.git", "target": ".",
                   "commit": "68b0d231a13201eb14acd3dc84e51543d16e5f7e"},  # v3.4.1: Less, mixins and guards
    "hn-svelte": {"repo": "https://github.com/sveltejs/hn.svelte.dev.git", "target": ".",
                  "commit": "0010bbea06781f11797c71a3497e7e0c1beff702"},  # Svelte 3, scoped styles
    # Vue 3.5 single-file components: 47 `.vue`, 36 `<style lang="scss" scoped>` and one global SCSS block, global
    # sheets imported by `src/main.ts` (normalize, Element Plus, vxe-table, `@@/assets/styles/index.scss`), path
    # aliases `@` and `@@`, layout components through a barrel; small (196 files).
    "v3-admin-vite": {"repo": "https://github.com/un-pany/v3-admin-vite.git", "target": ".",
                      "commit": "c2c895d71d571e9c18c2453fa85469a479c79fc6"},
    "saas-starter": {"repo": "https://github.com/nextjs/saas-starter.git", "target": ".",
                     "commit": "6e33e58b1e553a41fe22e6b941a7229a002de361"},  # Tailwind 4.1.7, CSS-first
    "sc-website": {"repo": "https://github.com/styled-components/styled-components-website.git", "target": ".",
                   "commit": "e70dc5c3f513b4a72ce20d0a1a76fe9891c4a071"},  # styled-components 7
}
TW = "frontend/styles/tailwind.css"
RAILS, SHEET = [220, 223, 227, 231, 235], [197, 206, 211, 214, 241, 244, 247, 251, 256, 261, 267, 270, 273, 278, 284]
FONTS = "backend/modules/landing/public/fonts/fonts.css"
INTER = [2, 11, 20, 29, 38, 47, 56, 65, 74, 83, 92, 101, 110, 119, 128, 137, 146, 155, 164, 173, 182, 191, 200, 209,
         218, 227, 236, 245, 254, 263, 272, 281, 290, 299, 308]
MANROPE = list(range(317, 525, 9))
FORM = ("rounded-lg bg-black/[0.04] dark:bg-white/[0.07] text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 "
        "dark:placeholder-gray-500 transition-colors hover:bg-black/[0.06] dark:hover:bg-white/[0.1] focus:outline-none "
        "focus:ring-2 focus:ring-blue-500/40 disabled:opacity-50 disabled:cursor-not-allowed px-3 py-2 w-20").split()
NOTE = ["frontend/components/Note/NoteFocusMode.tsx:55", "frontend/components/Note/NoteFocusMode.tsx:100",
        "frontend/components/Note/NoteSidePanel.tsx:132", "frontend/components/Note/NoteSidePanel.tsx:152",
        "frontend/components/Notes.tsx:103", "frontend/components/Notes.tsx:553"]
# Twenty usages read in the source before any graph of tududi existed: (file, line, kind, symbol, expected ends).
# An end is a node's `file:line`, a file, `tailwindcss` (the utility) or `hole:<class>`; `all` is every rule whose
# selector names the class, counted by `_rules_naming` (a scan of its own, not the product's parser); symbol `*`
# takes every reference of that kind at the site, `{name: ends}`.
TUDUDI_HAND = [
    # Markup to rules.
    ("frontend/components/Profile/tabs/TabsNav.tsx", 17, "class", ".scrollbar-hide", [f"{TW}:141", f"{TW}:146"]),
    ("frontend/components/Area/AreaDetails.tsx", 357, "class", ".task-sheet-rails", [f"{TW}:{n}" for n in RAILS]),
    ("frontend/components/Area/AreaDetails.tsx", 357, "class", ".task-sheet",  # `${TASK_SHEET_CLASS}`, imported const
     [f"{TW}:{n}" for n in SHEET]),
    ("frontend/components/Shared/MarkdownRenderer.tsx", 245, "class", ".markdown-content", ["all"]),
    ("frontend/components/Sidebar/SidebarResizeHandle.tsx", 60, "class", ".sidebar-resizing", [f"{TW}:165"]),
    ("frontend/components/Admin/AdminGroupsPanel.tsx", 621, "class", ".line-clamp-1",
     [f"{TW}:173", f"{TW}:181", "tailwindcss"]),  # the project's @layer utilities rules and Tailwind's own utility
    ("frontend/components/Task/TaskDetails/TaskContentCard.tsx", 111, "class", ".prose",
     ["hole:no-rule"]),  # @tailwindcss/typography is not configured (plugins: [])
    ("backend/modules/landing/views/partials/nav.ejs", 5, "class", ".nav-wrap",
     ["backend/modules/landing/views/partials/styles.ejs:18"]),  # an inline <style> of another EJS file
    ("frontend/App.tsx", 337, "class", ".dark", ["all", "tailwindcss"]),  # classList.toggle; darkMode: 'class'
    ("frontend/components/Habits/HabitCheckIn.tsx", 147, "class", "*",  # `${FORM.input} w-20`, a const object
     {"." + token: ["tailwindcss"] for token in FORM}),
    # Custom properties.
    ("frontend/components/Capture/CaptureHost.tsx", 151, "custom-property", "--capture-dock-left",
     ["frontend/components/Capture/CaptureHost.tsx:148"]),  # in a Tailwind arbitrary value
    ("frontend/components/Note/NoteFocusMode.tsx", 53, "custom-property", "--note-tint", NOTE),  # style objects and
    # Tailwind arbitrary properties `[--note-tint:...]` (light and dark) in three components
    ("frontend/components/Capture/CaptureHost.tsx", 27, "custom-property", "--sidebar-width",
     ["frontend/components/Sidebar.tsx:93"]),  # setProperty
    ("frontend/constants/colorPalette.ts", 72, "custom-property", "--accent-light",
     ["frontend/constants/colorPalette.ts:65"]),  # an object `as CSSProperties`
    ("tailwind.config.js", 11, "custom-property", "--sidebar-width", ["frontend/components/Sidebar.tsx:93"]),
    # Others.
    (TW, 18, "keyframes", "spin", [f"{TW}:21"]),
    (TW, 37, "keyframes", "border-pulse-dark", [f"{TW}:40"]),
    ("backend/modules/landing/views/partials/styles.ejs", 12, "font-face", "*",
     {"Manrope": [f"{FONTS}:{n}" for n in MANROPE], "Inter": [f"{FONTS}:{n}" for n in INTER]}),
    ("frontend/Layout.tsx", 12, "import", "./styles/tailwind.css", [TW]),
    (TW, 121, "class", ".outline-none", ["tailwindcss"]),  # @apply
]
# Fifteen usages per new case, read in the source before its graph existed. `all` counts every rule whose flattened
# selector names the class (`_rules_naming`, a scan of its own); `all:<path>` the same in one more file (a sheet the
# page loads from outside the snapshot).
SV, CO, ID, PI, TT = ("src/components/Nav.svelte", "src/routes/item/_Comment.svelte", "src/routes/item/[id].svelte",
                      "src/components/PreloadingIndicator.svelte", "src/components/ThemeToggler.svelte")
ST = "docs/examples/starter-template/index.html"
# The sheets the checkout's pages link by a path that resolves (examples, theme example, visual tests), all outside the
# snapshot (`dist`): a class names the rules of all of them, certain only where its page loads the sheet.
BS = ["all", *(f"all:{sheet}" for sheet in ("docs/dist/css/bootstrap.min.css", "docs/dist/css/bootstrap-theme.min.css",
                                            "dist/css/bootstrap.min.css"))]
BD, PG = "docs/_layouts/docs.html", "app/(dashboard)/dashboard/activity/page.tsx"
GS = "components/GlobalStyles.tsx"
LG, LI, AM, LM = ("src/layouts/components/Logo/index.vue", "src/pages/login/index.vue",
                  "src/layouts/components/AppMain/index.vue", "src/layouts/modes/LeftMode.vue")
TM, LT, EL = "src/layouts/modes/TopMode.vue", "src/layouts/modes/LeftTopMode.vue", "src/pages/error/components/Layout.vue"
HAND = {
    "tududi": TUDUDI_HAND,
    "hn-svelte": [  # scoped: a component's rules reach its own markup; `:global(...)` names reach everyone's
        (SV, 82, "class", ".icon", [f"{SV}:14", f"{SV}:71"]),
        (SV, 85, "class", ".selected", [f"{SV}:46", f"{SV}:52"]),  # class:selected
        (SV, 91, "class", ".about", [f"{SV}:42"]),
        (CO, 8, "class", ".comment", [f"{CO}:28", f"{CO}:32", f"{CO}:47", f"{CO}:57", f"{CO}:81", f"{ID}:47"]),
        (CO, 8, "class", ".hidden", [f"{CO}:43", f"{CO}:52"]),  # class:hidden
        (CO, 9, "class", ".meta-bar", [f"{CO}:36", f"{CO}:43"]),
        (CO, 10, "class", ".meta", [f"{CO}:66"]),  # [id].svelte's .meta is scoped to it
        (CO, 13, "class", ".body", [f"{CO}:52", f"{CO}:77"]),
        (CO, 18, "class", ".children", [f"{CO}:47", f"{CO}:52", f"{CO}:57"]),
        (ID, 57, "class", ".item", [f"{ID}:21", f"{ID}:27"]),
        (ID, 58, "class", ".main-link", [f"{ID}:31"]),
        (PI, 56, "class", ".progress-container", [f"{PI}:17"]),
        (PI, 62, "class", ".fade", [f"{PI}:35", f"{PI}:45"]),
        (TT, 39, "class", ".light", ["hole:no-rule"]),
        (TT, 40, "class", ".dark", [f"{TT}:74", f"{TT}:78", "static/global.css:7", f"{CO}:32", f"{ID}:27",
                                    f"{PI}:45"]),
        (TT, 31, "class", ".nice", [f"{TT}:57"]),
    ],
    # Written from the source at the pinned commit before the graph existed. A scoped rule reaches its own
    # component's markup and, through `child-root`, the root element of a child its template renders; a global
    # sheet (`index.scss`, imported by `main.ts`) reaches every page of the bundle. No class below is in a package
    # sheet main.ts imports (Element Plus 2.14.2, vxe-table 4.6.25, nprogress 0.2.0, normalize.css 8.0.1, checked).
    "v3-admin-vite": [
        (LG, 17, "class", ".layout-logo-container", [f"{LG}:30", f"{LG}:37", f"{LG}:40", f"{LG}:43"]),
        (LG, 17, "class", ".collapse", [f"{LG}:53", f"{LG}:54", f"{LG}:55", f"{LG}:60"]),  # a `:class` object key
        (LG, 20, "class", ".layout-logo", [f"{LG}:40", f"{LG}:55"]),
        (LI, 89, "class", ".login-container", [f"{LI}:{n}" for n in (159, 166, 172, 179, 184, 188, 190, 193, 202)]),
        (LI, 90, "class", ".theme-switch", [f"{LI}:166"]),  # on the ThemeSwitch component
        (AM, 12, "class", ".app-main", [f"{AM}:35", f"{LM}:111", f"{LM}:117", f"{LM}:124", f"{LM}:127",
                                        f"{TM}:63", f"{TM}:71", f"{LT}:88", f"{LT}:100", f"{LT}:109"]),
        (AM, 13, "class", ".app-scrollbar", [f"{AM}:40", f"{AM}:46"]),
        (AM, 18, "class", ".app-container-grow", [f"{AM}:46"]),
        ("src/layouts/components/Footer/index.vue", 6, "class", ".layout-footer",
         ["src/layouts/components/Footer/index.vue:12"]),
        (EL, 2, "class", ".error", [f"{EL}:15"]),  # `&-svg` is another class
        (EL, 3, "class", ".error-svg", [f"{EL}:21"]),
        (LM, 38, "class", ".drawer-bg", [f"{LM}:64"]),
        (LM, 42, "class", ".main-container", [f"{LM}:87", f"{LM}:136", f"{LM}:150", f"{LM}:176"]),
        ("src/layouts/components/Hamburger/index.vue", 21, "class", ".icon",
         ["src/layouts/components/Hamburger/index.vue:29"]),
        ("src/pages/demo/level2/index.vue", 2, "class", ".app-container", ["src/common/assets/styles/index.scss:19"]),
    ],
    "bootstrap3": [(ST, line, "class", symbol, BS) for line, symbol in (
        (36, ".navbar"), (36, ".navbar-inverse"), (36, ".navbar-fixed-top"), (37, ".container"),
        (39, ".navbar-toggle"), (40, ".sr-only"), (41, ".icon-bar"), (45, ".navbar-brand"),
        (47, ".collapse"), (47, ".navbar-collapse"), (48, ".nav"), (48, ".navbar-nav"), (49, ".active"))] + [
        (ST, 39, "class", ".collapsed", ["hole:no-rule"]),  # only the collapse plugin's JavaScript reads it
        (ST, 59, "class", ".starter-template", ["all"])],
    "bulma": [
        (BD, 13, "class", ".bd-docs-overlay", ["all"]), (BD, 13, "class", ".js-toggle", ["hole:no-rule"]),
        (BD, 15, "class", ".button", ["all"]), (BD, 15, "class", ".bd-docs-button", ["all"]),
        (BD, 16, "class", ".fas", ["hole:no-rule"]),  # Font Awesome, linked through a Liquid URL
        (BD, 16, "class", ".fa-arrow-right-from-bracket", ["hole:no-rule"]),
        (BD, 19, "class", ".bd-docs-menu", ["all"]), (BD, 35, "class", ".bd-docs-content", ["all"]),
        (BD, 35, "class", ".algolia-content", ["all"]), (BD, 37, "class", ".content", ["all"]),
        (BD, 15, "id", "#js-menu-toggle", ["all-id"]),
    ],
    "saas-starter": [(PG, line, "class", "*", {"." + token: ["tailwindcss"] for token in tokens.split()})
                     for line, tokens in (
        (75, "flex-1 p-4 lg:p-8"), (76, "text-lg lg:text-2xl font-medium text-gray-900 mb-6"), (85, "space-y-4"),
        (93, "flex items-center space-x-4"), (94, "bg-orange-100 rounded-full p-2"), (95, "w-5 h-5 text-orange-600"),
        (97, "flex-1"), (98, "text-sm font-medium text-gray-900"), (102, "text-xs text-gray-500"),
        (111, "flex flex-col items-center justify-center text-center py-12"),
        (112, "h-12 w-12 text-orange-500 mb-4"), (113, "text-lg font-semibold text-gray-900 mb-2"),
        (116, "text-sm text-gray-500 max-w-sm"))] + [
        ("app/(dashboard)/dashboard/activity/loading.tsx", 13, "class", ".min-h-[88px]", ["tailwindcss"]),
        ("app/(dashboard)/dashboard/general/page.tsx", 36, "class", ".mb-2", ["tailwindcss"])],
    "sc-website": [
        ("app/page.tsx", 17, "class", ".hero-header", ["all"]), ("app/page.tsx", 24, "class", ".hero-tagline", ["all"]),
        ("app/page.tsx", 27, "class", ".hero-subtitle", ["all"]), ("app/page.tsx", 36, "class", ".hero-used-by", ["all"]),
        ("components/ClientLayout.tsx", 27, "class", ".root", [f"{GS}:104"]),  # createGlobalStyle
        ("app/error.tsx", 5, "class", ".error-page", ["app/error.tsx:11", "app/error.tsx:22", "app/error.tsx:28"]),
        ("components/LiveEdit.tsx", 46, "class", ".notranslate", ["hole:no-rule"]),
        ("app/error.tsx", 39, "custom-property", "--sc-color-border", [f"{GS}:386", f"{GS}:396"]),
        # declared at run time by styled-components' createTheme, never written as a declaration
        *[("app/error.tsx", line, "custom-property", name, ["hole:undeclared"]) for line, name in (
            (19, "--sc-color-text"), (24, "--sc-text-2xl"), (29, "--sc-text-base"), (30, "--sc-color-textSecondary"),
            (40, "--sc-radius-md"), (41, "--sc-color-surface"))],
    ],
}


def _image():
    node = f"node-{NODE[0]}-linux-x64.tar.xz"
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "xz-utils")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(
            f"curl -fsSL https://nodejs.org/dist/{NODE[0]}/{node} -o /tmp/{node}",
            f"echo '{NODE[1]}  /tmp/{node}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{node} -C /opt/node --strip-components=1 && rm /tmp/{node}",
        )
        .env({"PATH": "/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
              "DAODAN_NODE_BIN": "/opt/node/bin", "DAODAN_CSS_ENGINES": "/engines/node_modules"})
        .add_local_file(HERE / "adapters/css_engines.json" if LOCAL else Path("/audit/adapters/css_engines.json"),
                        "/engines/package.json", copy=True)
        .run_commands("cd /engines && npm install --ignore-scripts --no-audit --no-fund --loglevel=error")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                        "/audit/plugin_scripts.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-graph-css", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_sha256() -> dict:
    folder = Path(css.__file__).parent
    names = sorted(path.name for path in folder.glob("css*") if path.suffix in (".py", ".js", ".json"))
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()[:12] for name in names}


def inventory(manifest: Path) -> list[str]:
    """The snapshot's stylesheets, markup files and scripts, the ones no reader takes included (listed as missing)."""
    import sqlite3
    with sqlite3.connect(manifest) as connection:
        rows = connection.execute("SELECT file, language FROM sem_coverage").fetchall()
    return sorted(rel for rel, language in rows if language in ("css", "javascript", "typescript")
                  or rel.lower().endswith(css.MARKUP + tuple(css.COMPONENTS) + tuple(css.UNREAD)))


def _flat(prelude: str, parents: list[str]) -> list[str]:
    """A nested selector list against its parents: `&` takes each parent, else the parent is the ancestor."""
    children = [part.strip() for part in re.split(r",(?![^()]*\))", prelude) if part.strip()]
    if not parents:
        return children
    return [child.replace("&", parent) if "&" in child else f"{parent} {child}" for parent in parents
            for child in children]


def _rules_naming(texts: dict, name: str, mark: str = ".") -> list[str]:
    """`file:line` of every rule whose selector, once nesting is flattened, names a class (or an id): a scan of
    braces, comments and strings of its own. At-rules keep the selectors around them; a mixin or function
    definition (`@mixin`, `.x(...) {`) starts from none; a selector with an interpolation is not counted."""
    found, pattern = [], re.compile(re.escape(mark + name) + r"(?![\w-])")
    for rel, (text, offset) in texts.items():
        stack, start, at, line, prelude, interpolation = [], None, 0, 1 + offset, [], 0
        while at < len(text):
            char = text[at]
            if text.startswith("/*", at):
                stop = text.find("*/", at + 2)
                stop = len(text) if stop < 0 else stop + 2
                line += text.count("\n", at, stop)
                at = stop
                continue
            if text.startswith("//", at) and rel.lower().endswith((".scss", ".sass", ".less")) and text[at - 1:at] != ":":
                stop = text.find("\n", at)
                at = len(text) if stop < 0 else stop
                continue
            if char in "\"'":
                stop = text.find(char, at + 1)
                stop = len(text) if stop < 0 else stop + 1
                prelude.append(text[at:stop])
                line += text.count("\n", at, stop)
                at = stop
                continue
            if char == "{" and at and text[at - 1] in "#@":
                interpolation += 1
                prelude.append(char)
            elif char == "}" and interpolation:
                interpolation -= 1
                prelude.append(char)
            elif char == "{":
                selector = " ".join("".join(prelude).split())
                parents = stack[-1] if stack else []
                if selector.startswith(("@mixin", "@function")) or re.match(r"^[.#][\w-]+\s*\(", selector):
                    stack.append([])
                elif selector.startswith("@") or selector.endswith(":"):
                    stack.append(parents)
                else:
                    selector = re.sub(r"\s+when\s+.*$|:extend\([^)]*\)", "", selector)
                    flat = _flat(selector, parents)
                    if selector and "#{" not in selector and "@{" not in selector and any(map(pattern.search, flat)):
                        found.append(f"{rel}:{start}")
                    stack.append(flat)
                prelude, start = [], None
            elif char == "}":
                if stack:
                    stack.pop()
                prelude, start = [], None
            elif char == ";":
                prelude, start = [], None
            elif not char.isspace() or prelude:
                if start is None and not char.isspace():
                    start = line
                prelude.append(char)
            line += char == "\n"
            at += 1
    return found


def _ends(graph: dict, nodes: dict, site: str, kind: str, symbol: str | None) -> dict:
    """{symbol: ends} the graph gives at a site: `file:line` of each node, a file, `tailwindcss`, `hole:<class>`."""
    out = collections.defaultdict(set)
    for edge in graph["edges"]:
        if edge["site"] == site and edge["kind"] == kind and (symbol is None or edge["symbol"] == symbol):
            target = nodes[edge["to"]]
            end = "tailwindcss" if (target["external"] or {}).get("package") == "tailwindcss" else \
                edge["to"] if target["kind"] == "module" else f"{target['file']}:{target['line']}"
            out[edge["symbol"]].add(end)
    for hole in graph["holes"]:
        written = {"class": ".", "id": "#"}.get(kind, "") + hole["name"]
        if hole["site"] == site and hole["kind"] == kind and (symbol is None or written == symbol):
            out[written].add(f"hole:{hole['class']}")
    return out


def hand_check(graph: dict, project: Path, files: list[str], hand: list) -> list[dict]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    texts = {}
    for rel in files:
        if rel.lower().endswith(css.STYLESHEETS):
            texts[rel] = ((project / rel).read_text(encoding="utf-8", errors="replace"), 0)
        elif rel.lower().endswith(css.MARKUP + tuple(css.COMPONENTS)):
            source = (project / rel).read_text(encoding="utf-8", errors="replace")
            for number, match in enumerate(re.finditer(r"<style[^>]*>(.*?)</style>", source, re.S)):
                texts[f"{rel}#{number}"] = (match.group(1), source[:match.start(1)].count("\n"))
    out = []
    for rel, line, kind, symbol, expected in hand:
        found = _ends(graph, nodes, f"{rel}:{line}", kind, None if symbol == "*" else symbol)
        if symbol != "*":
            ends = set()
            for end in expected:
                scope = texts
                if end.startswith("all:"):
                    extra = end[4:]
                    scope = {extra: ((project / extra).read_text(encoding="utf-8", errors="replace"), 0)}
                if end.startswith("all"):
                    mark = "#" if end == "all-id" else "."
                    ends |= {re.sub(r"#\d+(?=:\d+$)", "", item) for item in _rules_naming(scope, symbol[1:], mark)}
                else:
                    ends.add(end)
            expected = {symbol: ends}
        expected = {name: set(ends) for name, ends in expected.items()}
        got = {name: ends for name, ends in found.items()}
        out.append({"site": f"{rel}:{line}", "kind": kind, "symbol": symbol, "right": got == expected,
                    "missing": {name: sorted(ends - got.get(name, set())) for name, ends in expected.items()
                                if ends - got.get(name, set())},
                    "extra": {name: sorted(ends - expected.get(name, set())) for name, ends in got.items()
                              if ends - expected.get(name, set())},
                    "expected_ends": sum(len(ends) for ends in expected.values()),
                    "graph_ends": sum(len(ends) for ends in got.values())})
    return out


def components(graph: dict, project: Path, files: list[str]) -> dict:
    """For Vue: files found and read, style blocks by kind and `lang` (a scan of the tags of its own), and where the
    arcs of template classes end: the component's own or a parent's block, or a global sheet; how many of them the
    page rule leaves uncertain."""
    vue = [rel for rel in files if rel.endswith(".vue")]
    if not vue:
        return {}
    missing = {item["path"] for item in graph["files"]["missing"]}
    blocks = collections.Counter()
    for rel in vue:
        for match in re.finditer(r"<style\b([^>]*)>", (project / rel).read_text(encoding="utf-8", errors="replace")):
            attrs = match.group(1)
            lang = re.search(r"\blang\s*=\s*['\"]?(\w+)", attrs)
            kind = "scoped" if re.search(r"\bscoped\b", attrs) else "module" if re.search(r"\bmodule\b", attrs) \
                else "global"
            blocks[f"{kind} {lang.group(1) if lang else 'css'}"] += 1
    nodes = {node["id"]: node for node in graph["nodes"]}
    ends = collections.Counter()
    for edge in graph["edges"]:
        if edge["kind"] != "class" or not edge["site"].split(":")[0].endswith(".vue"):
            continue
        target = nodes[edge["to"]]
        where = "external" if target["external"] else \
            "own component" if target["file"] == edge["site"].rsplit(":", 1)[0] else \
            "parent component (child-root)" if "child-root" in edge["chain"] else \
            "another component" if (target["file"] or "").endswith(".vue") else "global sheet"
        ends[(where, "uncertain" if edge.get("uncertain") else "certain")] += 1
    return {"vue_found": len(vue), "vue_read": len([rel for rel in vue if rel not in missing]),
            "style_blocks": dict(blocks.most_common()),
            "class_arcs": {f"{where} {state}": count for (where, state), count in sorted(ends.items())}}


def summary(graph: dict) -> dict:
    """What the report of the shared module does not count: arcs by kind, holes by class, uncertain arcs."""
    by_kind = collections.Counter((edge["kind"], edge["end"]) for edge in graph["edges"])
    holes = collections.defaultdict(list)
    for hole in graph["holes"]:
        holes[(hole["class"], hole["kind"])].append(f"{hole['site']} {hole['name']}")
    uncertain = [edge for edge in graph["edges"] if edge.get("uncertain")]
    return {
        "nodes_by_kind": dict(collections.Counter(node["kind"] + (" external" if node["external"] else "")
                                                  for node in graph["nodes"]).most_common()),
        "edges_by_kind_end": {f"{kind} {end}": count for (kind, end), count in sorted(by_kind.items())},
        "edges_by_chain": dict(collections.Counter(" > ".join(edge["chain"]) or "-"
                                                   for edge in graph["edges"]).most_common()),
        "holes_by_class": {f"{cls} {kind}": {"count": len(items), "examples": scip_graph._examples(items)}
                           for (cls, kind), items in sorted(holes.items(), key=lambda pair: -len(pair[1]))},
        "uncertain": {"edges": len(uncertain), "references": len({(e["site"], e["symbol"]) for e in uncertain}),
                      "examples": [{key: edge[key] for key in ("site", "symbol", "to", "uncertain")}
                                   for edge in uncertain[:: max(1, len(uncertain) // 5)]][:5]},
    }


def _pnpm_modules(target: Path) -> Path | None:
    """A project npm cannot install (an `overrides` npm refuses) installed with the pnpm its `packageManager` names
    (pnpm 10 when it names none), from its own lockfile, scripts off, in a copy holding only the manifests."""
    import shutil
    import subprocess
    meta = json.loads((target / "package.json").read_text(encoding="utf-8"))
    manager = str(meta.get("packageManager", "")) or "pnpm@10"
    if not manager.startswith("pnpm@") or not (target / "pnpm-lock.yaml").is_file():
        return None
    copy = Path("/work/pnpm") / target.name
    shutil.rmtree(copy, ignore_errors=True)
    copy.mkdir(parents=True)
    for name in ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml"):
        if (target / name).is_file():
            shutil.copyfile(target / name, copy / name)
    run = subprocess.run(["npx", "--yes", manager.split("+")[0], "install", "--frozen-lockfile", "--ignore-scripts"],
                         cwd=copy, capture_output=True, text=True, timeout=1800)
    print("pnpm", run.returncode, run.stderr[-400:], flush=True)
    return copy / "node_modules" if run.returncode == 0 and (copy / "node_modules").is_dir() else None


@app.function(cpu=2, memory=8192, timeout=3600, volumes={"/results": volume})
def css_case(name: str) -> dict:
    import os
    import shutil
    import time
    import resolve_edges as rx
    print("code", code_sha256(), flush=True)  # compared with the checkout before trusting the run
    started = time.time()
    case = CSS_CASES[name]
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)
    target = _source(work / "src", case, None)
    if name == "tududi":  # the snapshot the engine pass kept, as in the first runs
        manifest = work / "manifest.sqlite"
        shutil.copyfile(Path("/results") / TAG / "scip-inputs" / name / "manifest.sqlite", manifest)
        files = inventory(manifest)
    else:
        files = css.walk(target)
    begun = time.time()
    modules = rx.npm_modules(target) or _pnpm_modules(target)
    installed = round(time.time() - begun, 1)
    if modules is not None and not (target / "node_modules").exists():
        os.symlink(modules, target / "node_modules", target_is_directory=True)
    graph = css.run(target, work / "engine", files)
    checks = {"case": name, "commit": case["commit"], "code": code_sha256(), "files_given": len(files),
              "npm_install_seconds": installed, "node_modules": str(modules),
              "report": scip_graph.report(graph), "summary": summary(graph),
              "hand_check": hand_check(graph, target, files, HAND[name]),
              "components": components(graph, target, files),
              "seconds": round(time.time() - started, 1)}
    store = Path("/results") / TAG
    with gzip.open(store / f"graph-css-{name}.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(graph, handle, ensure_ascii=False)
    (store / f"graph-css-{name}-checks.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    volume.commit()
    return {"case": name, "nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "holes": len(graph["holes"]),
            "right": sum(item["right"] for item in checks["hand_check"]), "seconds": checks["seconds"]}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--cases", default="tududi")
    parser.add_argument("--graph", action="store_true", help="with fetch: also the graph, gzipped")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        print("local code", code_sha256())
        function = modal.Function.from_name("daodan-graph-css", "css_case")
        for name in chosen:
            print(name, function.spawn(name).object_id)
    else:
        for name in chosen:
            items = [f"graph-css-{name}-checks.json"] + ([f"graph-css-{name}.json.gz"] if args.graph else [])
            for item in items:
                data = b"".join(volume.read_file(f"{TAG}/{item}"))
                (RESULTS / item).write_bytes(data.replace(b"\r\n", b"\n") if item.endswith(".json") else data)
                print(item, len(data))
