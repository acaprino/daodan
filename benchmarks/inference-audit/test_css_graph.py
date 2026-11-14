"""The CSS graph of `fixtures/css` against arcs written by hand, from the fixture's text, before any adapter ran.

    python -m pytest benchmarks/inference-audit/test_css_graph.py

Needs Node and npm: the fixture's packages (`fixtures/css/package.json`) are installed once into a folder of the
system temp directory and linked into a copy of the fixture; without npm the test is skipped. The CDN sheet the
fixture links is served by a stand-in for the download, so the test needs no network beyond npm.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adapters import css  # noqa: E402

FIXTURE = HERE / "fixtures/css"
T, B, M = "src/styles/theme.css", "src/styles/base.css", "src/styles/Button.module.css"
K, S, H, E, A = "src/styles/_tokens.scss", "src/styles/main.scss", "src/index.html", "src/page.ejs", "src/App.tsx"

# Nodes the arcs below reach.
CARD = [f"{B}:1 .card", f"{B}:5 .btn:hover, #app > .card", f"{T}:43 @container side (min-width: 400px) {{ .card }}"]
BTN = [f"{T}:30 @layer brand {{ .btn }}", f"{B}:5 .btn:hover, #app > .card"]
DARK = [f"{T}:10 .dark", f"{M}:14 :global(.dark) .primary", "tailwindcss dark"]
APP = [f"{B}:5 .btn:hover, #app > .card", f"{H}:7 #app"]
ACCENT = [f"{T}:6 --accent", f"{T}:11 --accent", f"{H}:11 --accent", f"{A}:12 --accent", f"{A}:16 [--accent:blue]"]
GAP = [f"{T}:7 --gap", f"{A}:10 --gap"]
SIDEBAR, SHELL, SPIN = f"{T}:38 .sidebar", f"{H}:6 .shell", f"{T}:25 @keyframes spin"
ANGLE, BRAND = f"{T}:14 @property --angle", f"{T}:20 @font-face Brand Sans"
# Sheets outside the snapshot the markup loads: a vendored file, an npm package, a CDN link.
ICONS, ANIMATE = "src/vendor/icons/icons.min.css", "animate.css/animate.css"
CDN = "https://cdn.jsdelivr.net/npm/@acme/ui@1.2.3/dist/ui.css"
EXTERNAL = (ICONS, ANIMATE, CDN, "tailwindcss", "sass:")


def _rows(site, kind, symbol, targets, chain=()):
    return [(site, kind, symbol, target, "external" if target.startswith(EXTERNAL) else "project", chain)
            for target in targets]


# (site, kind, symbol, to, end, chain): every arc the graph must hold, and nothing else.
EXPECTED = [
    *_rows(f"{T}:1", "import", "./base.css", [B]),
    *_rows(f"{T}:2", "import", "tailwindcss/base", ["tailwindcss/base.css"]),
    *_rows(f"{T}:26", "custom-property", "--angle", [ANGLE]),
    *_rows(f"{T}:29", "layer", "brand", [f"{T}:3 @layer brand"]),
    *_rows(f"{T}:31", "custom-property", "--accent", ACCENT),
    *_rows(f"{T}:32", "custom-property", "--gap", GAP),
    *_rows(f"{T}:33", "keyframes", "spin", [SPIN]),
    *_rows(f"{T}:34", "font-face", "Brand Sans", [BRAND]),
    *_rows(f"{T}:42", "container", "side", [f"{T}:39 container side"]),
    *_rows(f"{T}:46", "layer", "reset", [f"{T}:3 @layer reset"]),
    *_rows(f"{M}:6", "composes", ".base", [f"{M}:1 .base"]),
    *_rows(f"{M}:7", "custom-property", "--accent", ACCENT),
    *_rows(f"{M}:11", "composes", ".card", CARD),
    *_rows(f"{K}:5", "sass-variable", "$x", [f"{K}:4 @mixin pad"], ("parameter",)),
    *_rows(f"{S}:1", "import", "tokens", [K]),
    *_rows(f"{S}:6", "sass-variable", "$gap", [f"{S}:3 $gap"]),
    *_rows(f"{S}:7", "sass-variable", "tokens.$radius", [f"{K}:2 $radius"]),
    *_rows(f"{S}:8", "mixin", "tokens.pad", [f"{K}:4 @mixin pad"]),
    *_rows(f"{S}:8", "sass-variable", "tokens.$gap", [f"{K}:1 $gap"]),
    *_rows(f"{H}:4", "import", "styles/theme.css", [T]),
    *_rows(f"{H}:10", "class", ".dark", DARK),
    *_rows(f"{H}:11", "id", "#app", APP),
    *_rows(f"{H}:11", "class", ".shell", [SHELL]),
    *_rows(f"{H}:11", "class", ".card", CARD),
    *_rows(f"{H}:11", "font-face", "Brand Sans", [BRAND]),
    *_rows(f"{E}:1", "class", ".card", CARD),
    *_rows(f"{E}:1", "class", ".sidebar", [SIDEBAR]),
    *_rows(f"{A}:2", "import", "./styles/Button.module.css", [M]),
    *_rows(f"{A}:3", "import", "./styles/theme.css", [T]),
    *_rows(f"{A}:9", "class", ".dark", DARK, ("classList",)),
    *_rows(f"{A}:12", "id", "#app", APP),
    *_rows(f"{A}:12", "class", ".card", CARD, ("literal-type",)),
    *_rows(f"{A}:12", "class", ".btn", BTN, ("literal-type",)),
    *_rows(f"{A}:12", "class", ".flex", ["tailwindcss flex"]),
    *_rows(f"{A}:12", "class", ".px-2", ["tailwindcss px-2"]),
    *_rows(f"{A}:12", "class", ".hover:bg-red-500", ["tailwindcss hover:bg-red-500"]),
    *_rows(f"{A}:12", "keyframes", "spin", [SPIN], ("style-object",)),
    *_rows(f"{A}:12", "custom-property", "--angle", [ANGLE], ("css-text",)),
    *_rows(f"{A}:13", "module-member", ".primary", [f"{M}:5 .primary", f"{M}:14 :global(.dark) .primary"]),
    *_rows(f"{A}:13", "module-member", ".primary", [f"{M}:1 .base"], ("composes",)),
    *_rows(f"{A}:13", "class", ".btn", BTN, ("clsx",)),
    *_rows(f"{A}:13", "class", ".sidebar", [SIDEBAR], ("clsx",)),
    *_rows(f"{A}:14", "class", ".panel__title", [f"{S}:9 .panel__title"]),
    *_rows(f"{A}:14", "class", ".text-red-500", ["tailwindcss text-red-500"], ("initializer",)),
    *_rows(f"{A}:16", "class", ".[--accent:blue]", ["tailwindcss [--accent:blue]"]),
    *_rows(f"{A}:16", "class", ".shell", [SHELL]),
    *_rows(f"{A}:23", "class", ".flex", ["tailwindcss flex"]),  # a template over two lines: each token on its line
    *_rows(f"{A}:24", "class", ".shell", [SHELL]),
    *_rows(f"{A}:27", "import", "animate.css", [ANIMATE]),
    *_rows(f"{H}:13", "import", "/assets/vendor/icons/icons.min.css", [ICONS], ("url-suffix",)),
    *_rows(f"{H}:14", "import", CDN, [CDN]),
    *_rows(f"{H}:15", "class", ".ic", [f"{ICONS} .ic"]),
    *_rows(f"{H}:15", "class", ".ic-star", [f"{ICONS} .ic-star"]),
    *_rows(f"{H}:15", "class", ".animate__animated", [f"{ANIMATE} .animate__animated"]),
    *_rows(f"{H}:15", "class", ".ui-btn", [f"{CDN} .ui-btn"]),
    *_rows("src/styles/extra.less:2", "less-variable", "@gap", ["src/styles/extra.less:1 @gap"]),
    *_rows("src/Widget.vue:2", "class", ".card", CARD),
    *_rows("src/Card.svelte:1", "class", ".card", CARD),
    *_rows(f"{A}:30", "class", ".group/tip", ["tailwindcss group"], ("named-group",)),
    *_rows("tailwind.config.js:6", "class", ".animate-spin", ["tailwindcss animate-spin"], ("safelist",)),
]

# (site, kind, class, name)
HOLES = {
    (f"{T}:32", "custom-property", "undeclared", "--missing"),
    (f"{H}:12", "class", "no-rule", "lead"),
    (f"{E}:1", "class", "ejs", "<%= extra %>"),
    (f"{A}:12", "class", "no-rule", "ghost-x"),
    (f"{A}:14", "class", "template", "${size}-x"),
    (f"{A}:15", "module-member", "dynamic-member", "styles[size]"),
    (f"{E}:2", "class", "ejs-glued", "tab<%= active ? ' tab-on' : '' %>"),
    (f"{A}:30", "class", "css-in-js", "cm-x"),
}

# (site, symbol): the candidates every arc of that reference names, when the cascade picks one.
CASCADE = {(f"{T}:31", "--accent"): set(ACCENT), (f"{M}:7", "--accent"): set(ACCENT),
           (f"{T}:32", "--gap"): set(GAP)}
# (site, symbol): the targets of its arcs that are uncertain, the cascade's or a sheet not proven loaded with the
# site: index.html loads theme.css (and what it imports) and the two sheets it links; App.tsx is a module nothing
# imports and no page loads, so its sheets are those it imports; page.ejs, Widget.vue and Card.svelte load none.
UNCERTAIN = {**CASCADE,
             (f"{H}:10", ".dark"): {f"{M}:14 :global(.dark) .primary"},
             (f"{H}:15", ".animate__animated"): {f"{ANIMATE} .animate__animated"},
             (f"{A}:12", "#app"): {f"{H}:7 #app"},
             (f"{A}:14", ".panel__title"): {f"{S}:9 .panel__title"},
             (f"{A}:16", ".shell"): {SHELL}, (f"{A}:24", ".shell"): {SHELL},
             (f"{E}:1", ".card"): set(CARD), (f"{E}:1", ".sidebar"): {SIDEBAR},
             ("src/Widget.vue:2", ".card"): set(CARD), ("src/Card.svelte:1", ".card"): set(CARD)}


def _link(target: Path, link: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege: a junction needs none
        import _winapi
        _winapi.CreateJunction(str(target), str(link))


def _installed(manifest: Path, prefix: str) -> Path:
    """The `node_modules` of a package manifest, installed once into a folder of the system temp directory."""
    npm = shutil.which("npm")
    if npm is None or shutil.which("node") is None:
        pytest.skip("Node and npm are needed")
    data = manifest.read_bytes()
    cache = Path(tempfile.gettempdir()) / f"{prefix}-{hashlib.sha256(data).hexdigest()[:12]}"
    if not (cache / "node_modules/.package-lock.json").is_file():
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "package.json").write_bytes(data)
        subprocess.run([npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"],
                       cwd=cache, check=True, shell=os.name == "nt", capture_output=True)
    return cache / "node_modules"


@pytest.fixture(scope="module")
def engines():
    folder = _installed(HERE / "adapters/css_engines.json", "daodan-css-engines")
    previous = os.environ.get("DAODAN_CSS_ENGINES")
    os.environ["DAODAN_CSS_ENGINES"] = str(folder)
    yield folder
    if previous is None:
        os.environ.pop("DAODAN_CSS_ENGINES", None)
    else:
        os.environ["DAODAN_CSS_ENGINES"] = previous


def _run(name: str, tmp_path_factory, served=None) -> dict:
    fixture = HERE / "fixtures" / name
    project = tmp_path_factory.mktemp(name) / "fixture"
    shutil.copytree(fixture, project)
    if (fixture / "package.json").is_file():
        _link(_installed(fixture / "package.json", f"daodan-{name}-fixture"), project / "node_modules")
    download, css._download = css._download, (served or {}).get
    try:
        return css.run(project, project.parent / "work")
    finally:
        css._download = download


def _arcs(graph: dict) -> set:
    return {(e["site"], e["kind"], e["symbol"], e["to"], e["end"], tuple(e["chain"])) for e in graph["edges"]}


def _holes(graph: dict) -> set:
    return {(h["site"], h["kind"], h["class"], h["name"]) for h in graph["holes"]}


def _uncertain(graph: dict) -> dict:
    """(site, symbol): the targets of its uncertain arcs; an arc the cascade or the compilation makes uncertain lists
    its candidates, one whose sheet is not proven loaded stands alone."""
    found = {}
    for edge in graph["edges"]:
        if edge.get("uncertain"):
            found.setdefault((edge["site"], edge["symbol"]), set()).add(edge["to"])
    for edge in graph["edges"]:
        if edge.get("uncertain", {}).get("candidates"):
            assert edge["to"] in edge["uncertain"]["candidates"]
        elif edge.get("uncertain"):
            assert edge["uncertain"]["reason"] == "sheet-not-proven-loaded"
    return found


@pytest.fixture(scope="module")
def graph(tmp_path_factory, engines):
    return _run("css", tmp_path_factory, {CDN: ".ui-btn { color: red; }"})


def test_every_arc_and_nothing_else(graph):
    actual = {(e["site"], e["kind"], e["symbol"], e["to"], e["end"], tuple(e["chain"])) for e in graph["edges"]}
    expected = set(EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_holes(graph):
    assert {(h["site"], h["kind"], h["class"], h["name"]) for h in graph["holes"]} == HOLES


def test_cascade_candidates_and_unproven_sheets_are_uncertain_arcs(graph):
    assert _uncertain(graph) == UNCERTAIN
    for edge in graph["edges"]:
        key = (edge["site"], edge["symbol"])
        if key in CASCADE:
            assert set(edge["uncertain"]["candidates"]) == CASCADE[key]
        elif edge.get("uncertain"):
            assert edge["uncertain"]["reason"] == "sheet-not-proven-loaded"


def test_nodes(graph):
    nodes = {node["id"]: node for node in graph["nodes"]}
    kinds = {key: nodes[key]["kind"] for key in (f"{T}:30 @layer brand {{ .btn }}", f"{T}:6 --accent", ANGLE, BRAND,
                                                SPIN, f"{T}:39 container side", f"{T}:3 @layer reset",
                                                f"{K}:1 $gap", f"{K}:4 @mixin pad", f"{A}:16 [--accent:blue]", B)}
    assert kinds == {f"{T}:30 @layer brand {{ .btn }}": "rule", f"{T}:6 --accent": "custom-property",
                     ANGLE: "property", BRAND: "font-face", SPIN: "keyframes", f"{T}:39 container side": "container",
                     f"{T}:3 @layer reset": "layer", f"{K}:1 $gap": "variable", f"{K}:4 @mixin pad": "mixin",
                     f"{A}:16 [--accent:blue]": "custom-property", B: "module"}
    assert nodes["tailwindcss flex"]["external"] == {"manager": "npm", "package": "tailwindcss", "version": "3.4.19"}
    assert nodes["tailwindcss/base.css"]["external"]["package"] == "tailwindcss"
    assert (nodes[f"{S}:9 .panel__title"]["file"], nodes[f"{S}:9 .panel__title"]["line"]) == (S, 9)


def test_external_sheets_name_package_and_version(graph):
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes[ICONS]["external"] == {"manager": "checkout", "package": "Icons Kit", "version": "2.1.0",
                                        "from": "banner"}
    assert nodes[f"{ICONS} .ic"]["external"] == nodes[ICONS]["external"]
    assert nodes[ANIMATE]["external"] == {"manager": "npm", "package": "animate.css", "version": "4.1.1"}
    assert nodes[CDN]["external"] == {"manager": "npm", "package": "@acme/ui", "version": "1.2.3", "from": "url"}
    assert f"{ANIMATE} @keyframes bounce" not in nodes  # a name no reference reaches makes no node


def test_files_read(graph):
    """Every stylesheet and markup file is read or listed with the reason: none dropped."""
    missing = {item["path"]: item["reason"] for item in graph["files"]["missing"]}
    assert missing == {}
    assert graph["files"]["indexed"] == 13 and graph["files"]["snapshot"] == 13


# fixtures/css-sass: SCSS and indented Sass through the official Sass parser. Written from the fixture's text.
ST, SK, SX, SI, SL, SH = ("src/styles/theme.scss", "src/styles/_tokens.scss", "src/styles/_mixins.scss",
                          "src/styles/_index.scss", "src/styles/legacy.sass", "src/index.html")
S_CARD, S_TITLE, S_GEN, S_M, S_SIZE = (f"{ST}:8 .card", f"{ST}:15 .card__title", f"{ST}:20 .card--#{{$name}}",
                                       f"{ST}:23 .card .m-#{{$i}}", f"{ST}:26 .card .size-#{{$size}}")
S_GAP, S_DOUBLE = f"{SK}:1 $gap", f"{SK}:5 @function double"
S_PAD, S_LPAD = f"{SX}:2 @mixin pad", f"{SL}:2 @mixin legacy-pad"
S_OLD = [f"{SL}:4 .old, .older", f"{SL}:8 .old:hover, .older:hover"]
SASS_EXPECTED = [
    *_rows(f"{ST}:1", "import", "sass:math", ["sass:math"]),
    *_rows(f"{ST}:2", "import", "tokens", [SK]),
    *_rows(f"{ST}:2", "sass-variable", "$gap", [S_GAP], ("configuration",)),
    *_rows(f"{ST}:3", "import", "index", [SI]),
    *_rows(f"{ST}:4", "import", "legacy", [SL]),
    *_rows(f"{ST}:6", "sass-variable", "kit.$gap", [S_GAP]),
    *_rows(f"{ST}:9", "function", "math.div", ["sass:math"]),
    *_rows(f"{ST}:9", "sass-variable", "kit.$radius", [f"{SK}:2 $radius"]),
    *_rows(f"{ST}:10", "function", "kit.double", [S_DOUBLE]),
    *_rows(f"{ST}:11", "mixin", "kit.mx-pad", [S_PAD]),
    *_rows(f"{ST}:14", "placeholder", "%focus-ring", [f"{SX}:6 %focus-ring"]),
    *_rows(f"{ST}:17", "sass-variable", "$local-gap", [f"{ST}:6 $local-gap"]),
    *_rows(f"{ST}:17", "sass-variable", "$inner", [f"{ST}:16 $inner"]),
    *_rows(f"{ST}:20", "sass-variable", "$name", [f"{ST}:19 $name"], ("loop",)),
    *_rows(f"{ST}:20", "sass-variable", "$tone", [f"{ST}:19 $tone"], ("loop",)),
    *_rows(f"{ST}:23", "sass-variable", "$i", [f"{ST}:22 $i"], ("loop",)),
    *_rows(f"{ST}:25", "sass-variable", "tokens.$palette", [f"{SK}:3 $palette"]),
    *_rows(f"{ST}:26", "sass-variable", "$size", [f"{ST}:25 $size"], ("loop",)),
    *_rows(f"{ST}:29", "sass-variable", "$inner", [f"{ST}:16 $inner"]),
    *_rows(f"{ST}:31", "mixin", "legacy-pad", [S_LPAD]),
    *_rows(f"{ST}:33", "keyframes", "pulse", [f"{ST}:32 @keyframes pulse"]),  # percentage keyframe selectors
    *_rows(f"{SX}:1", "import", "tokens", [SK]),
    *_rows(f"{SX}:2", "sass-variable", "tokens.$gap", [S_GAP]),
    *_rows(f"{SX}:3", "sass-variable", "$x", [S_PAD], ("parameter",)),
    *_rows(f"{SK}:6", "sass-variable", "$n", [S_DOUBLE], ("parameter",)),
    *_rows(f"{SI}:1", "import", "tokens", [SK]),
    *_rows(f"{SI}:2", "import", "mixins", [SX]),
    *_rows(f"{SL}:3", "sass-variable", "$p", [S_LPAD], ("parameter",)),
    *_rows(f"{SL}:7", "mixin", "legacy-pad", [S_LPAD]),
    *_rows(f"{SH}:2", "import", "styles/theme.scss", [ST]),
    *_rows(f"{SH}:3", "class", ".card", [S_CARD, S_M, S_SIZE]),
    *_rows(f"{SH}:3", "class", ".card--primary", [S_GEN]),
    *_rows(f"{SH}:3", "class", ".card__title", [S_TITLE]),
    *_rows(f"{SH}:3", "class", ".m-1", [S_M]),
    *_rows(f"{SH}:3", "class", ".old", S_OLD),
]
SASS_HOLES = {
    (f"{ST}:26", "rule", "interpolated-selector", ".card .size-#{$size}"),
    (f"{SH}:3", "class", "interpolated-selector", "size-primary"),
    (f"{ST}:30", "sass-variable", "undeclared", "kit.$private-x"),
}
SASS_UNCERTAIN = {(f"{SH}:3", ".card--primary"): {S_GEN}, (f"{SH}:3", ".m-1"): {S_M}}


@pytest.fixture(scope="module")
def sass_graph(tmp_path_factory, engines):
    return _run("css-sass", tmp_path_factory)


def test_sass_arcs(sass_graph):
    actual, expected = _arcs(sass_graph), set(SASS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_sass_holes_and_uncertain_arcs(sass_graph):
    assert _holes(sass_graph) == SASS_HOLES
    assert _uncertain(sass_graph) == SASS_UNCERTAIN
    assert sass_graph["files"] == {"snapshot": 6, "indexed": 6, "missing": []}


# fixtures/css-less: Less through its own parser. Written from the fixture's text.
LV, LX, LS, LP, LH = ("src/styles/vars.less", "src/styles/mixins.less", "src/styles/site.less",
                      "src/styles/plugins/units.js", "src/index.html")
L_BORDERED = [f"{LX}:1 @mixin .bordered", f"{LX}:4 @mixin .bordered"]
L_M, L_LOOP, L_GEN, L_PLAIN = f"{LX}:8 @mixin .m", f"{LS}:24 @mixin .loop", f"{LS}:23 .@{{prefix}}-btn", \
    f"{LX}:10 .plain"
L_GAP, L_BRAND = f"{LV}:2 @gap", f"{LV}:3 @brand"
LESS_EXPECTED = [
    *_rows(f"{LS}:1", "import", "mixins", [LX]),
    *_rows(f"{LS}:2", "import", "vars.less", [LV]),
    *_rows(f"{LS}:3", "plugin", "plugins/units", [LP]),
    *_rows(f"{LS}:7", "less-variable", "@gap", [L_GAP]),
    *_rows(f"{LS}:8", "less-variable", "@@name", [f"{LV}:4 @name"]),
    *_rows(f"{LS}:8", "less-variable", "@@name", [L_BRAND], ("variable-variable",)),
    *_rows(f"{LS}:9", "mixin", ".bordered", L_BORDERED),
    *_rows(f"{LS}:10", "mixin", ".plain", [L_PLAIN]),
    *_rows(f"{LS}:11", "mixin", "#ns > .m", [L_M]),
    *_rows(f"{LS}:12", "mixin", "#ns.m", [L_M]),
    *_rows(f"{LS}:13", "class", ".card", [f"{LS}:21 .card"], (":extend",)),
    *_rows(f"{LS}:14", "less-variable", "@gap", [L_GAP]),
    *_rows(f"{LS}:15", "less-variable", "@detached", [f"{LS}:4 @detached"]),
    *_rows(f"{LS}:16", "less-variable", "@map", [f"{LS}:5 @map"]),
    *_rows(f"{LS}:18", "less-variable", "@local", [f"{LS}:17 @local"], ("local",)),
    *_rows(f"{LS}:21", "class", ".box", [f"{LS}:6 .box"], (":extend",)),
    *_rows(f"{LS}:23", "less-variable", "@prefix", [f"{LS}:22 @prefix"]),
    *_rows(f"{LS}:24", "less-variable", "@i", [L_LOOP], ("parameter",)),
    *_rows(f"{LS}:25", "less-variable", "@i", [L_LOOP], ("parameter",)),
    *_rows(f"{LS}:26", "mixin", ".loop", [L_LOOP]),
    *_rows(f"{LS}:26", "less-variable", "@i", [L_LOOP], ("parameter",)),
    *_rows(f"{LS}:28", "mixin", ".loop", [L_LOOP]),
    *_rows(f"{LS}:32", "mixin", ".inner", [f"{LS}:31 @mixin .inner"]),  # defined inside the mixin that calls it
    *_rows(f"{LX}:1", "less-variable", "@w", [L_BORDERED[0]], ("parameter",)),
    *_rows(f"{LX}:2", "less-variable", "@w", [L_BORDERED[0]], ("parameter",)),
    *_rows(f"{LX}:2", "less-variable", "@brand", [L_BRAND]),
    *_rows(f"{LX}:4", "less-variable", "@w", [L_BORDERED[1]], ("parameter",)),
    *_rows(f"{LX}:8", "less-variable", "@brand", [L_BRAND]),
    *_rows(f"{LH}:1", "import", "styles/site.less", [LS]),
    *_rows(f"{LH}:2", "class", ".box", [f"{LS}:6 .box"]),
    *_rows(f"{LH}:2", "class", ".card", [f"{LS}:21 .card"]),
    *_rows(f"{LH}:2", "class", ".app-btn", [L_GEN]),
    *_rows(f"{LH}:2", "class", ".plain", [L_PLAIN]),
]
LESS_HOLES = {
    (f"{LS}:25", "rule", "interpolated-selector", ".w-@{i}"),
    (f"{LH}:2", "class", "interpolated-selector", "w-2"),
    (f"{LS}:29", "less-variable", "undeclared", "@missing"),
    (f"{LS}:29", "mixin", "undeclared", ".nope"),
}
LESS_UNCERTAIN = {(f"{LS}:9", ".bordered"): set(L_BORDERED), (f"{LS}:26", ".loop"): {L_LOOP},
                  (f"{LS}:28", ".loop"): {L_LOOP}, (f"{LH}:2", ".app-btn"): {L_GEN}, (f"{LH}:2", ".plain"): {L_PLAIN}}


@pytest.fixture(scope="module")
def less_graph(tmp_path_factory, engines):
    return _run("css-less", tmp_path_factory)


def test_less_arcs(less_graph):
    actual, expected = _arcs(less_graph), set(LESS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_less_holes_and_uncertain_arcs(less_graph):
    assert _holes(less_graph) == LESS_HOLES
    assert _uncertain(less_graph) == LESS_UNCERTAIN
    assert less_graph["files"] == {"snapshot": 5, "indexed": 5, "missing": []}


# fixtures/css-sfc: Vue, Svelte and Astro through their own compilers. Written from the fixture's text.
VA, VC, VS, VT, VG, VM = ("src/App.vue", "src/Child.vue", "src/Card.svelte", "src/Title.astro", "src/global.css",
                          "src/main.ts")
V_CARD_GLOBAL = [f"{VG}:1 .card", f"{VT}:10 .card"]
V_APP_CARD = [f"{VA}:17 .card", f"{VA}:18 .card :deep(.inner)"]
V_ON_GLOBAL = f"{VS}:12 :global(.on)"
SFC_EXPECTED = [
    *_rows(f"{VA}:2", "class", ".card", V_CARD_GLOBAL + V_APP_CARD),
    *_rows(f"{VA}:2", "class", ".active", [f"{VG}:2 .active"], (":class",)),
    *_rows(f"{VA}:3", "module-member", ".title", [f"{VA}:23 .title"]),
    *_rows(f"{VA}:3", "class", ".on", [f"{VA}:19 .on", V_ON_GLOBAL], (":class",)),
    *_rows(f"{VA}:3", "class", ".text", [f"{VA}:28 .text"]),
    *_rows(f"{VA}:17", "v-bind", "color", [f"{VA}:13 color"]),
    *_rows(f"{VA}:28", "sass-variable", "$pad", [f"{VA}:27 $pad"]),
    *_rows(f"{VC}:2", "class", ".inner", [f"{VA}:18 .card :deep(.inner)", f"{VC}:6 .inner"]),
    *_rows(f"{VC}:2", "class", ".card", V_CARD_GLOBAL),
    *_rows(f"{VC}:2", "class", ".card", V_APP_CARD, ("child-root",)),
    *_rows(f"{VC}:2", "class", ".on", [V_ON_GLOBAL]),
    *_rows(f"{VC}:2", "class", ".on", [f"{VA}:19 .on"], ("child-root",)),
    *_rows(f"{VC}:6", "less-variable", "@c", [f"{VC}:5 @c"]),
    *_rows(f"{VS}:5", "class", ".card", [f"{VS}:10 .card", *V_CARD_GLOBAL]),
    *_rows(f"{VS}:5", "class", ".on", [V_ON_GLOBAL]),
    *_rows(f"{VS}:5", "class", ".active", [f"{VG}:2 .active"], ("class:",)),
    *_rows(f"{VS}:6", "class", ".label", [f"{VS}:11 .label", f"{VS}:13 :global(html).dark .label"]),
    *_rows(f"{VT}:4", "class", ".title", [f"{VT}:6 .title"], ("class:list",)),
    *_rows(f"{VT}:4", "class", ".big", [f"{VT}:7 .big"], ("class:list",)),
    *_rows(f"{VT}:4", "class", ".card", V_CARD_GLOBAL),
    *_rows(f"{VT}:4", "class", ".dark", [f"{VS}:13 :global(html).dark .label"]),  # a compound led by :global is global
    *_rows(f"{VM}:3", "import", "@/global.css", [VG], ("paths",)),  # tsconfig `paths`
]
SFC_HOLES = {
    ("src/Other.vue:1", "class", "no-rule", "inner"),  # App's `:deep(.inner)` reaches only App's subtree
    (f"{VA}:2", "id", "no-rule", "app"),
    (f"{VA}:2", "class", "no-rule", "is-wide"),
    (f"{VA}:3", "class", "no-rule", "off"),
    (f"{VA}:4", "class", "variable", "color"),
}


@pytest.fixture(scope="module")
def sfc_graph(tmp_path_factory, engines):
    return _run("css-sfc", tmp_path_factory)


def test_sfc_arcs(sfc_graph):
    actual, expected = _arcs(sfc_graph), set(SFC_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


# main.ts loads App.vue, Child.vue and global.css; Card.svelte and Title.astro are modules nothing imports.
SFC_UNCERTAIN = {(f"{VA}:2", ".card"): {f"{VT}:10 .card"}, (f"{VA}:3", ".on"): {V_ON_GLOBAL},
                 (f"{VC}:2", ".card"): {f"{VT}:10 .card"}, (f"{VC}:2", ".on"): {V_ON_GLOBAL},
                 (f"{VS}:5", ".card"): set(V_CARD_GLOBAL), (f"{VS}:5", ".active"): {f"{VG}:2 .active"},
                 (f"{VT}:4", ".card"): {f"{VG}:1 .card"}, (f"{VT}:4", ".dark"): {f"{VS}:13 :global(html).dark .label"}}


def test_sfc_holes_and_files(sfc_graph):
    assert _holes(sfc_graph) == SFC_HOLES
    assert _uncertain(sfc_graph) == SFC_UNCERTAIN
    assert sfc_graph["files"] == {"snapshot": 8, "indexed": 8, "missing": []}


# fixtures/css-pages: which sheet applies where. Written from the fixture's text.
PL, PH, PN = "backend/views/landing.ejs", "backend/views/partials/head.ejs", "backend/views/partials/nav.ejs"
PI = "backend/public/vendor/icons/icons.css"
FI, FF, FM, FA, FC, AP = ("frontend/index.html", "frontend/fonts.css", "frontend/src/main.tsx", "frontend/src/App.tsx",
                          "frontend/src/app.css", "admin/Panel.tsx")
PAGES_EXPECTED = [
    (f"{PL}:2", "include", "partials/head", PH, "project", ()),
    (f"{PL}:5", "include", "partials/nav", PN, "project", ()),
    (f"{PH}:1", "import", "/assets/vendor/icons/icons.css", PI, "external", ("url-suffix",)),
    (f"{PL}:4", "class", ".sr-only", f"{PI} .sr-only", "external", ()),
    (f"{PL}:4", "class", ".nav-wrap", f"{PH}:3 .nav-wrap", "project", ()),
    (f"{PN}:1", "class", ".nav-wrap", f"{PH}:3 .nav-wrap", "project", ()),
    (f"{PN}:1", "class", ".sr-only", f"{PI} .sr-only", "external", ()),
    (f"{FI}:2", "import", "/fonts.css", FF, "project", ("url-suffix",)),
    (f"{FI}:4", "script", "/src/main.tsx", FM, "project", ("url-suffix",)),
    (f"{FM}:2", "import", "./app.css", FC, "project", ()),
    (f"{FA}:1", "class", ".sr-only", f"{PI} .sr-only", "external", ()),
    (f"{FA}:1", "class", ".shell", f"{FC}:1 .shell", "project", ()),
    (f"{FA}:1", "font-face", "Lora", f"{FF}:1 @font-face Lora", "project", ("style-object",)),
    (f"{AP}:1", "class", ".shell", f"{FC}:1 .shell", "project", ()),
    (f"{AP}:1", "class", ".ic", f"{PI} .ic", "external", ()),
]
PAGES_UNCERTAIN = {(f"{FA}:1", ".sr-only"): {f"{PI} .sr-only"}, (f"{AP}:1", ".shell"): {f"{FC}:1 .shell"},
                   (f"{AP}:1", ".ic"): {f"{PI} .ic"}}


@pytest.fixture(scope="module")
def pages_graph(tmp_path_factory, engines):
    return _run("css-pages", tmp_path_factory)


def test_pages_arcs(pages_graph):
    actual, expected = _arcs(pages_graph), set(PAGES_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_a_sheet_applies_where_its_page_or_bundle_loads_it(pages_graph):
    assert _holes(pages_graph) == {(f"{FI}:3", "id", "no-rule", "root")}
    assert _uncertain(pages_graph) == PAGES_UNCERTAIN
    assert {e["uncertain"]["reason"] for e in pages_graph["edges"] if e.get("uncertain")} == {"sheet-not-proven-loaded"}
    assert pages_graph["files"] == {"snapshot": 9, "indexed": 9, "missing": []}


# fixtures/css-in-js: CSS-in-JS recognised by the package of the callee or tag. Written from the fixture's text.
JT, JD, JS_, JV = "src/theme.ts", "src/dom.ts", "src/styled.tsx", "src/styles.css.ts"
J_INK = f"{JS_}:10 --ink"
CSSINJS_EXPECTED = [
    *_rows(f"{JD}:2", "class", ".cm-content", [f"{JT}:4 & .cm-content"], ("classList",)),
    *_rows(f"{JD}:2", "class", ".cm-md-link", [f"{JT}:8 &dark .cm-md-link"], ("classList",)),
    *_rows(f"{JD}:2", "class", ".title", [f"{JS_}:6 & .title", f"{JS_}:16 &:hover .title"], ("classList",)),
    *_rows(f"{JD}:2", "class", ".btn-primary", [f"{JS_}:11 .btn-primary"], ("classList",)),
    *_rows(f"{JT}:3", "custom-property", "--ink", [J_INK]),
    *_rows(f"{JS_}:4", "custom-property", "--ink", [J_INK]),
    *_rows(f"{JV}:6", "custom-property", "--ink", [J_INK]),
]
CSSINJS_HOLES = {
    (f"{JD}:2", "class", "css-in-js", "cm-ghost"),
    (f"{JS_}:12", "rule", "interpolated-selector", ".${(p: any) => p.name}"),
}
CSSINJS_NODES = {f"{JT}:2 &", f"{JT}:3 &", f"{JT}:5 &.cm-focused .cm-cursor", f"{JT}:7 &", f"{JS_}:3 &", f"{JS_}:5 .dark &",
                 f"{JS_}:14 &", f"{JV}:2 &", f"{JV}:4 .dark &", f"{JV}:6 .prose a", "src/stitches.ts:2 &",
                 "src/stitches.ts:3 &:hover", "src/stitches.ts:4 & .icon", "src/Box.tsx:2 &",
                 "src/Box.tsx:2 & .MuiChip-root"}


@pytest.fixture(scope="module")
def cssinjs_graph(tmp_path_factory, engines):
    return _run("css-in-js", tmp_path_factory)


def test_css_in_js_arcs(cssinjs_graph):
    actual, expected = _arcs(cssinjs_graph), set(CSSINJS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_css_in_js_rules_are_nodes_and_unknown_shapes_are_holes(cssinjs_graph):
    assert _holes(cssinjs_graph) == CSSINJS_HOLES
    assert _uncertain(cssinjs_graph) == {}
    ids = {node["id"] for node in cssinjs_graph["nodes"] if node["kind"] == "rule"}
    assert CSSINJS_NODES <= ids
    assert not any("cm-ghost" in node for node in ids)
    assert cssinjs_graph["files"] == {"snapshot": 7, "indexed": 7, "missing": []}


# fixtures/css-tailwind4: Tailwind 4's CSS-first configuration. Written from the fixture's text.
TA, TP = "src/app.css", "templates/page.html"
TAILWIND4_EXPECTED = [
    *_rows(f"{TA}:1", "import", "tailwindcss", ["tailwindcss/index.css"]),
    *_rows(f"{TA}:2", "source", "../templates", ["templates"]),
    *_rows(f"{TA}:13", "class", ".bg-brand", ["tailwindcss bg-brand"], ("@apply",)),
    *_rows(f"{TA}:13", "class", ".p-4", ["tailwindcss p-4"], ("@apply",)),
    *_rows(f"{TP}:1", "import", "/src/app.css", [TA], ("url-suffix",)),
    *_rows(f"{TP}:2", "class", ".card", [f"{TA}:13 .card"]),
    *_rows(f"{TP}:2", "class", ".text-brand", ["tailwindcss text-brand"]),
    *_rows(f"{TP}:2", "class", ".tab-4", [f"{TA}:6 @utility tab-4"]),
    *_rows(f"{TP}:2", "class", ".scrollbar-thin", [f"{TA}:9 @utility scrollbar-*"]),
    *_rows(f"{TP}:2", "class", ".pointer-coarse:p-2", ["tailwindcss pointer-coarse:p-2"]),
    *_rows(f"{TP}:2", "variant", "pointer-coarse", [f"{TA}:12 @custom-variant pointer-coarse"]),
    *_rows(f"{TP}:2", "class", ".group/tip", ["tailwindcss group"], ("named-group",)),
    *_rows(f"{TP}:2", "class", ".group-hover/tip:underline", ["tailwindcss group-hover/tip:underline"]),
]


@pytest.fixture(scope="module")
def tailwind4_graph(tmp_path_factory, engines):
    return _run("css-tailwind4", tmp_path_factory)


def test_tailwind4_arcs(tailwind4_graph):
    actual, expected = _arcs(tailwind4_graph), set(TAILWIND4_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_tailwind4_holes_and_version(tailwind4_graph):
    assert _holes(tailwind4_graph) == {(f"{TP}:2", "class", "no-rule", "nope-x")}
    assert _uncertain(tailwind4_graph) == {}
    nodes = {node["id"]: node for node in tailwind4_graph["nodes"]}
    assert nodes["tailwindcss text-brand"]["external"] == {"manager": "npm", "package": "tailwindcss",
                                                           "version": "4.3.5"}
    assert tailwind4_graph["files"] == {"snapshot": 2, "indexed": 2, "missing": []}


# fixtures/css-modern: modern CSS through the product's parser. Written from the fixture's text.
MM, MB, MH = "src/modern.css", "src/base.css", "src/index.html"
M_CARD, M_TITLE, M_HAS = f"{MM}:5 .card", f"{MM}:7 .card .title", f"{MM}:8 .card:has(.icon)"
M_SCOPE = f"{MM}:11 @scope (.panel) to (.panel-body) {{ .heading }}"
M_IS = f"{MM}:14 @media (--narrow) {{ :is(.card, .tile) > :where(.badge) }}"
M_TILE = f"{MM}:18 @supports (display: grid) {{ @container side (min-width: 20em) {{ .tile }} }}"
MODERN_EXPECTED = [
    *_rows(f"{MM}:1", "import", "base.css", [MB]),
    *_rows(f"{MM}:2", "layer", "base", [f"{MM}:1 @layer base"]),
    *_rows(f"{MM}:21", "layer", "components", [f"{MM}:2 @layer components"]),
    *_rows(f"{MM}:7", "custom-property", "--angle", [f"{MM}:4 @property --angle"]),
    *_rows(f"{MM}:13", "custom-media", "--narrow", [f"{MM}:3 @custom-media --narrow"]),
    *_rows(f"{MM}:18", "container", "side", [f"{MM}:20 container side"]),
    *_rows(f"{MH}:1", "import", "modern.css", [MM]),
    *_rows(f"{MH}:2", "class", ".card", [M_CARD, M_TITLE, M_HAS, M_IS]),
    *_rows(f"{MH}:2", "class", ".panel", [M_SCOPE]),
    *_rows(f"{MH}:2", "class", ".tile", [M_IS, M_TILE]),
    *_rows(f"{MH}:2", "class", ".badge", [M_IS]),
    *_rows(f"{MH}:2", "class", ".btn", [f"{MM}:21 @layer components {{ .btn }}"]),
    *_rows(f"{MH}:2", "class", ".icon", [M_HAS, f"{MB}:1 .icon"]),
    *_rows(f"{MH}:2", "class", ".title", [M_TITLE]),
    *_rows(f"{MH}:2", "class", ".heading", [M_SCOPE]),
    *_rows(f"{MH}:3", "class", ".card", [M_CARD, M_TITLE, M_HAS, M_IS]),
]


@pytest.fixture(scope="module")
def modern_graph(tmp_path_factory, engines):
    return _run("css-modern", tmp_path_factory)


def test_modern_css_arcs(modern_graph):
    actual, expected = _arcs(modern_graph), set(MODERN_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_modern_css_holes(modern_graph):
    assert _holes(modern_graph) == {(f"{MM}:16", "custom-media", "undeclared", "--wide"),
                                    (f"{MH}:3", "class", "template-tag", "{{ extra }}"),
                                    (f"{MH}:3", "class", "template-tag-glued", "x-{{ k }}")}
    assert _uncertain(modern_graph) == {}
    assert modern_graph["files"] == {"snapshot": 3, "indexed": 3, "missing": []}


# fixtures/css-stylus: Stylus through its own parser. Written from the fixture's text.
YV, YS, YH = "src/vars.styl", "src/site.styl", "src/index.html"
Y_PAD, Y_M = f"{YS}:2 @mixin pad", f"{YS}:15 .m-{{i}}"
Y_CARD = [f"{YS}:4 .card", f"{YS}:7 .card:hover", f"{YS}:9 .card .title, .card .sub",
          f"{YS}:18 @media (min-width: 600px) {{ .card }}"]
STYLUS_EXPECTED = [
    *_rows(f"{YS}:1", "import", "vars", [YV]),
    *_rows(f"{YS}:3", "stylus-variable", "n", [Y_PAD], ("parameter",)),
    *_rows(f"{YS}:5", "stylus-variable", "brand", [f"{YV}:1 brand"]),
    *_rows(f"{YS}:6", "mixin", "pad", [Y_PAD]),
    *_rows(f"{YS}:11", "class", ".base", [f"{YS}:12 .base"], ("@extend",)),
    *_rows(f"{YS}:15", "stylus-variable", "i", [f"{YS}:14 i"], ("loop",)),
    *_rows(f"{YS}:16", "stylus-variable", "i", [f"{YS}:14 i"], ("loop",)),
    *_rows(f"{YS}:24", "keyframes", "spin", [f"{YS}:20 @keyframes spin"]),
    *_rows(f"{YS}:25", "stylus-variable", "$w", [f"{YV}:2 $w"]),
    *_rows(f"{YH}:1", "import", "site.styl", [YS]),
    *_rows(f"{YH}:2", "class", ".card", Y_CARD),
    *_rows(f"{YH}:2", "class", ".title", [f"{YS}:9 .card .title, .card .sub"]),
    *_rows(f"{YH}:2", "class", ".m-2", [Y_M]),
    *_rows(f"{YH}:2", "class", ".base", [f"{YS}:12 .base"]),
    *_rows(f"{YH}:2", "class", ".anim", [f"{YS}:23 .anim"]),
]


@pytest.fixture(scope="module")
def stylus_graph(tmp_path_factory, engines):
    return _run("css-stylus", tmp_path_factory)


def test_stylus_arcs(stylus_graph):
    actual, expected = _arcs(stylus_graph), set(STYLUS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_stylus_holes_and_uncertain_arcs(stylus_graph):
    assert _holes(stylus_graph) == {(f"{YS}:26", "stylus-variable", "undeclared", "$missing")}
    assert _uncertain(stylus_graph) == {(f"{YH}:2", ".m-2"): {Y_M}}
    assert stylus_graph["files"] == {"snapshot": 3, "indexed": 3, "missing": []}


# fixtures/css-modules: CSS Modules (`@value`, `:export`, `composes from`, `:global`, `:local`) and PostCSS.
CM, CB, CT, CA = "src/colors.module.css", "src/Button.module.scss", "src/theme.pcss", "src/App.tsx"
C_BRAND, C_ACCENT = f"{CM}:1 @value brand", f"{CM}:2 @value accent"
MODULES_EXPECTED = [
    *_rows(f"{CM}:3", "css-value", "brand", [C_BRAND]),
    *_rows(f"{CB}:1", "css-value", "brand", [C_BRAND], ("from",)),
    *_rows(f"{CB}:1", "css-value", "accent", [C_ACCENT], ("from",)),
    *_rows(f"{CB}:3", "sass-variable", "$pad", [f"{CB}:2 $pad"]),
    *_rows(f"{CB}:4", "composes", ".base", [f"{CM}:3 .base"]),
    *_rows(f"{CB}:4", "css-value", "accent", [C_ACCENT], ("from",)),
    *_rows(f"{CB}:4", "sass-variable", "$pad", [f"{CB}:2 $pad"]),
    *_rows(f"{CT}:2", "custom-selector", ":--heading", [f"{CT}:1 @custom-selector :--heading"]),
    *_rows(f"{CA}:1", "import", "./Button.module.scss", [CB]),
    *_rows(f"{CA}:2", "import", "./colors.module.css", [CM]),
    *_rows(f"{CA}:3", "import", "./theme.pcss", [CT]),
    *_rows(f"{CA}:4", "module-member", ".primary", [f"{CB}:4 .primary", f"{CB}:5 :global(.dark) .primary"]),
    *_rows(f"{CA}:4", "module-member", ".primary", [f"{CM}:3 .base"], ("composes",)),
    *_rows(f"{CA}:4", "module-member", ".gap", [f"{CB}:3 :export gap"]),
    *_rows(f"{CA}:4", "module-member", ".brand", [C_BRAND]),
    *_rows(f"{CA}:4", "module-member", ".inner", [f"{CB}:6 .local :local(.inner)"]),
    *_rows(f"{CA}:4", "class", ".card", [f"{CT}:3 .card", f"{CT}:4 .card .title"]),
    *_rows(f"{CA}:4", "class", ".title", [f"{CT}:4 .card .title"]),
]


@pytest.fixture(scope="module")
def modules_graph(tmp_path_factory, engines):
    return _run("css-modules", tmp_path_factory)


def test_css_modules_arcs(modules_graph):
    actual, expected = _arcs(modules_graph), set(MODULES_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_css_modules_holes(modules_graph):
    assert _holes(modules_graph) == set()
    assert _uncertain(modules_graph) == {}
    assert modules_graph["files"] == {"snapshot": 4, "indexed": 4, "missing": []}


# fixtures/css-markup: Angular template bindings and cva / tailwind-variants tables. Written from the fixture's text.
KH, KC, KT, KS = "src/app.component.html", "src/app.component.ts", "src/button.tsx", "src/styles.css"
K_BTN, K_FADED, K_CARDX = f"{KS}:6 .btn, .btn-primary, .btn-ghost", f"{KS}:7 .faded, .raised", \
    f"{KS}:8 .card-title, .card-lg"
MARKUP_EXPECTED = [
    *_rows(f"{KC}:2", "template", "./app.component.html", [KH]),
    *_rows(f"{KC}:2", "import", "./styles.css", [KS]),
    *_rows(f"{KH}:1", "class", ".card", [f"{KS}:1 .card"]),
    *_rows(f"{KH}:1", "class", ".is-active", [f"{KS}:2 .is-active"], ("[class.x]",)),
    *_rows(f"{KH}:1", "class", ".warn", [f"{KS}:3 .warn, .done"], ("[ngClass]",)),
    *_rows(f"{KH}:1", "class", ".done", [f"{KS}:3 .warn, .done"], ("[ngClass]",)),
    *_rows(f"{KH}:1", "class", ".big", [f"{KS}:4 .big"], ("[class]",)),
    *_rows(f"{KH}:2", "class", ".tag", [f"{KS}:5 .tag"], ("[ngClass]",)),
    *_rows(f"{KT}:3", "class", ".btn", [K_BTN], ("cva",)),
    *_rows(f"{KT}:4", "class", ".btn-primary", [K_BTN], ("cva",)),
    *_rows(f"{KT}:4", "class", ".btn-ghost", [K_BTN], ("cva",)),
    *_rows(f"{KT}:4", "class", ".faded", [K_FADED], ("cva",)),
    *_rows(f"{KT}:5", "class", ".raised", [K_FADED], ("cva",)),
    *_rows(f"{KT}:7", "class", ".card", [f"{KS}:1 .card"], ("tailwind-variants",)),
    *_rows(f"{KT}:7", "class", ".card-title", [K_CARDX], ("tailwind-variants",)),
    *_rows(f"{KT}:7", "class", ".card-lg", [K_CARDX], ("tailwind-variants",)),
    # `cn` returns tailwind-merge's call over its rest parameter: a helper of the project's own
    *_rows("src/use.tsx:2", "class", ".card", [f"{KS}:1 .card"], ("tailwind-merge",)),
    *_rows("src/use.tsx:2", "class", ".tag", [f"{KS}:5 .tag"], ("tailwind-merge",)),
]


@pytest.fixture(scope="module")
def markup_graph(tmp_path_factory, engines):
    return _run("css-markup", tmp_path_factory)


def test_markup_class_sources_arcs(markup_graph):
    actual, expected = _arcs(markup_graph), set(MARKUP_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_markup_class_sources_holes(markup_graph):
    assert _holes(markup_graph) == {(f"{KH}:1", "class", "variable", "size"),
                                    (f"{KH}:2", "class", "concatenation", "tag-${kind}")}
    assert _uncertain(markup_graph) == {}
    assert markup_graph["files"] == {"snapshot": 7, "indexed": 7, "missing": []}
