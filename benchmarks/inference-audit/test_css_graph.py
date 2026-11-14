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
EXTERNAL = (ICONS, ANIMATE, CDN, "tailwindcss")


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
    (f"{A}:30", "class", "tailwind-named-group", "group/tip"),
}

# (site, symbol): the candidates every arc of that reference names.
UNCERTAIN = {(f"{T}:31", "--accent"): set(ACCENT), (f"{M}:7", "--accent"): set(ACCENT),
             (f"{T}:32", "--gap"): set(GAP)}


def _link(target: Path, link: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:  # Windows without the symlink privilege: a junction needs none
        import _winapi
        _winapi.CreateJunction(str(target), str(link))


@pytest.fixture(scope="module")
def graph(tmp_path_factory):
    npm = shutil.which("npm")
    if npm is None or shutil.which("node") is None:
        pytest.skip("Node and npm are needed")
    manifest = (FIXTURE / "package.json").read_bytes()
    cache = Path(tempfile.gettempdir()) / f"daodan-css-fixture-{hashlib.sha256(manifest).hexdigest()[:12]}"
    if not (cache / "node_modules/.package-lock.json").is_file():
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "package.json").write_bytes(manifest)
        subprocess.run([npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"],
                       cwd=cache, check=True, shell=os.name == "nt", capture_output=True)
    project = tmp_path_factory.mktemp("css") / "fixture"
    shutil.copytree(FIXTURE, project)
    _link(cache / "node_modules", project / "node_modules")
    served = {CDN: ".ui-btn { color: red; }"}
    download, css._download = css._download, served.get
    try:
        return css.run(project, project.parent / "work")
    finally:
        css._download = download


def test_every_arc_and_nothing_else(graph):
    actual = {(e["site"], e["kind"], e["symbol"], e["to"], e["end"], tuple(e["chain"])) for e in graph["edges"]}
    expected = set(EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_holes(graph):
    assert {(h["site"], h["kind"], h["class"], h["name"]) for h in graph["holes"]} == HOLES


def test_cascade_candidates_are_uncertain_arcs(graph):
    found = {}
    for edge in graph["edges"]:
        if edge.get("uncertain"):
            found.setdefault((edge["site"], edge["symbol"]), set()).add(edge["to"])
            assert set(edge["uncertain"]["candidates"]) == UNCERTAIN[(edge["site"], edge["symbol"])]
    assert found == UNCERTAIN


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
    assert set(missing) == {"src/legacy.sass", "src/Widget.vue", "src/Card.svelte", "src/styles/extra.less"}
    assert missing["src/styles/extra.less"].startswith("partly read")
    assert graph["files"]["indexed"] == 9 and graph["files"]["snapshot"] == 13
