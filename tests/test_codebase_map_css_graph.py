"""The stylesheet graph (`indexers/css.py`) of the fixtures `fixtures/css-graph/*` against arcs, holes and uncertain
arcs written by hand, from each fixture's text, before any adapter ran.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_css_graph.py

The engines do not run here: each fixture's runs of the pinned engines (`indexers/css_engines/`), with the package
files the graph itself reads (`node_modules`), were recorded once on Modal into `fixtures/css-graph/recorded/<name>.json`
and are replayed by payload. A payload nothing recorded fails the test. To record them again:

    modal deploy benchmarks/inference-audit/lang_css.py
    python benchmarks/inference-audit/lang_css.py fixtures
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from indexers import css  # noqa: E402

FIXTURES = HERE / "fixtures/css-graph"
RECORDED = FIXTURES / "recorded"


def key(script, payload) -> tuple:
    return Path(script).stem, json.dumps(payload, sort_keys=True)


def replayer(recording: dict):
    """A runner that answers each engine run with the one recorded for the same payload. Payloads and outputs name
    files relative to the project's root, so a recording holds on any machine."""
    calls = {key(call["script"], call["payload"]): call for call in recording["calls"]}

    def runner(script, payload):
        call = calls.get(key(script, payload))
        assert call is not None, f"no recorded run of {Path(script).stem} for this payload: record the fixtures again"
        return call["data"], call["measured"]
    return runner


def record(project: Path, runner) -> dict:
    """The recording of a fixture (`replayer`): its engine runs through a real runner, and every file and folder of
    `node_modules` the graph itself looks at, each file with its text. On Modal only (`lang_css.py fixtures`)."""
    import os
    calls, seen = [], set()

    def recording(script, payload):
        data, measured = runner(script, payload)
        calls.append({"script": Path(script).stem, "payload": payload, "data": data,
                      "measured": {name: measured.get(name) for name in ("seconds", "peak_mb", "stderr_tail")}})
        return data, measured

    watching, stat = [True], os.stat

    def watched(path, *args, **kwargs):
        if watching[0] and isinstance(path, (str, os.PathLike)):
            seen.add(os.fspath(path))
        return stat(path, *args, **kwargs)

    def hook(event, args):
        if watching[0] and event == "open" and isinstance(args[0], (str, os.PathLike)):
            seen.add(os.fspath(args[0]))
    files = css.walk(project)  # before watching: the walk looks at every file and skips `node_modules`
    sys.addaudithook(hook)
    os.stat = watched
    try:
        css.run(project, recording, files)
    finally:
        os.stat, watching[0] = stat, False
    packages, directories = {}, set()
    for found in sorted(seen):
        path = Path(found)
        try:
            rel = path.relative_to(project).as_posix()
        except ValueError:
            continue
        if rel.split("/")[0] != "node_modules":
            continue
        if path.is_file():
            packages[rel] = path.read_text(encoding="utf-8", errors="replace")
        elif path.is_dir():
            directories.add(rel)
    return {"calls": calls, "packages": packages, "directories": sorted(directories)}


def project_copy(name: str, folder: Path) -> tuple[Path, dict]:
    """A copy of the fixture with the package files its recording holds, and the recording."""
    project = (folder / "fixture").resolve()
    shutil.copytree(FIXTURES / name, project)
    recording = json.loads((RECORDED / f"{name}.json").read_text(encoding="utf-8"))
    for rel in recording["directories"]:
        (project / rel).mkdir(parents=True, exist_ok=True)
    for rel, text in recording["packages"].items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    return project, recording


def _run(name: str, tmp_path_factory, remote=None, units=None) -> dict:
    """The fixture's graph from its recorded engine runs."""
    project, recording = project_copy(name, tmp_path_factory.mktemp(name))
    return css.run(project, replayer(recording), units=units, remote=remote)


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
def graph(tmp_path_factory):
    return _run("css", tmp_path_factory, remote={CDN: ".ui-btn { color: red; }"})


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


# css-sass: SCSS and indented Sass through the official Sass parser. Written from the fixture's text.
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
def sass_graph(tmp_path_factory):
    return _run("css-sass", tmp_path_factory)


def test_sass_arcs(sass_graph):
    actual, expected = _arcs(sass_graph), set(SASS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_sass_holes_and_uncertain_arcs(sass_graph):
    assert _holes(sass_graph) == SASS_HOLES
    assert _uncertain(sass_graph) == SASS_UNCERTAIN
    assert sass_graph["files"] == {"snapshot": 6, "indexed": 6, "missing": []}


# css-less: Less through its own parser. Written from the fixture's text.
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
def less_graph(tmp_path_factory):
    return _run("css-less", tmp_path_factory)


def test_less_arcs(less_graph):
    actual, expected = _arcs(less_graph), set(LESS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_less_holes_and_uncertain_arcs(less_graph):
    assert _holes(less_graph) == LESS_HOLES
    assert _uncertain(less_graph) == LESS_UNCERTAIN
    assert less_graph["files"] == {"snapshot": 5, "indexed": 5, "missing": []}


# css-sfc: Vue, Svelte and Astro through their own compilers. Written from the fixture's text.
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
def sfc_graph(tmp_path_factory):
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


# css-pages: which sheet applies where. Written from the fixture's text.
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
def pages_graph(tmp_path_factory):
    return _run("css-pages", tmp_path_factory)


def test_pages_arcs(pages_graph):
    actual, expected = _arcs(pages_graph), set(PAGES_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_a_sheet_applies_where_its_page_or_bundle_loads_it(pages_graph):
    assert _holes(pages_graph) == {(f"{FI}:3", "id", "no-rule", "root")}
    assert _uncertain(pages_graph) == PAGES_UNCERTAIN
    assert {e["uncertain"]["reason"] for e in pages_graph["edges"] if e.get("uncertain")} == {"sheet-not-proven-loaded"}
    assert pages_graph["files"] == {"snapshot": 9, "indexed": 9, "missing": []}


# css-in-js: CSS-in-JS recognised by the package of the callee or tag. Written from the fixture's text.
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
def cssinjs_graph(tmp_path_factory):
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


# css-tailwind4: Tailwind 4's CSS-first configuration. Written from the fixture's text.
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
def tailwind4_graph(tmp_path_factory):
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


# css-modern: modern CSS through the product's parser. Written from the fixture's text.
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
def modern_graph(tmp_path_factory):
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


# css-stylus: Stylus through its own parser. Written from the fixture's text.
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
def stylus_graph(tmp_path_factory):
    return _run("css-stylus", tmp_path_factory)


def test_stylus_arcs(stylus_graph):
    actual, expected = _arcs(stylus_graph), set(STYLUS_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_stylus_holes_and_uncertain_arcs(stylus_graph):
    assert _holes(stylus_graph) == {(f"{YS}:26", "stylus-variable", "undeclared", "$missing")}
    assert _uncertain(stylus_graph) == {(f"{YH}:2", ".m-2"): {Y_M}}
    assert stylus_graph["files"] == {"snapshot": 3, "indexed": 3, "missing": []}


# css-modules: CSS Modules (`@value`, `:export`, `composes from`, `:global`, `:local`) and PostCSS.
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
def modules_graph(tmp_path_factory):
    return _run("css-modules", tmp_path_factory)


def test_css_modules_arcs(modules_graph):
    actual, expected = _arcs(modules_graph), set(MODULES_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_css_modules_holes(modules_graph):
    assert _holes(modules_graph) == set()
    assert _uncertain(modules_graph) == {}
    assert modules_graph["files"] == {"snapshot": 4, "indexed": 4, "missing": []}


# css-markup: Angular template bindings and cva / tailwind-variants tables. Written from the fixture's text.
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
def markup_graph(tmp_path_factory):
    return _run("css-markup", tmp_path_factory)


def test_markup_class_sources_arcs(markup_graph):
    actual, expected = _arcs(markup_graph), set(MARKUP_EXPECTED)
    assert sorted(actual - expected) == [] and sorted(expected - actual) == []


def test_markup_class_sources_holes(markup_graph):
    assert _holes(markup_graph) == {(f"{KH}:1", "class", "variable", "size"),
                                    (f"{KH}:2", "class", "concatenation", "tag-${kind}")}
    assert _uncertain(markup_graph) == {}
    assert markup_graph["files"] == {"snapshot": 7, "indexed": 7, "missing": []}


# Inputs, not discoveries: a CDN sheet without its text, a unit the pre-map states. Written from the fixtures' text.
@pytest.fixture(scope="module")
def unread_cdn_graph(tmp_path_factory):
    return _run("css", tmp_path_factory)


def test_a_cdn_sheet_without_its_text_leaves_the_names_of_its_page_as_remote_sheet_holes(unread_cdn_graph):
    # index.html links the CDN sheet: `lead` (line 12) and `ui-btn` (line 15) may be declared there, and so may
    # `--missing`, read by theme.css (line 32), which the page loads too; App.tsx's `ghost-x` is in a bundle that
    # does not load it, and stays `no-rule`.
    ui_btn = (f"{H}:15", "class", ".ui-btn", f"{CDN} .ui-btn", "external", ())
    assert _arcs(unread_cdn_graph) == set(EXPECTED) - {ui_btn}
    assert _holes(unread_cdn_graph) == (HOLES - {(f"{H}:12", "class", "no-rule", "lead"),
                                                 (f"{T}:32", "custom-property", "undeclared", "--missing")}) | {
        (f"{H}:12", "class", "remote-sheet", "lead"), (f"{H}:15", "class", "remote-sheet", "ui-btn"),
        (f"{T}:32", "custom-property", "remote-sheet", "--missing")}
    reasons = {h["reason"] for h in unread_cdn_graph["holes"] if h["class"] == "remote-sheet"}
    assert reasons == {f"a sheet not read may declare it: {CDN}"}
    nodes = {node["id"]: node for node in unread_cdn_graph["nodes"]}
    assert nodes[CDN]["external"] == {"manager": "npm", "package": "@acme/ui", "version": "1.2.3", "from": "url"}


@pytest.fixture(scope="module")
def stated_pages_graph(tmp_path_factory):
    return _run("css-pages", tmp_path_factory, units=[["admin/Panel.tsx", "frontend/src/app.css"]])


def test_a_unit_the_premap_states_proves_its_sheets_loaded(stated_pages_graph):
    # The pre-map says admin/Panel.tsx loads frontend/src/app.css (as `styles` of `angular.json` would): its
    # `.shell` arc is certain; `.ic` of the icons sheet stays unproven.
    assert _arcs(stated_pages_graph) == set(PAGES_EXPECTED)
    expected = {key: value for key, value in PAGES_UNCERTAIN.items() if key != (f"{AP}:1", ".shell")}
    assert _uncertain(stated_pages_graph) == expected


# The edge store's rows.
def test_rows_hold_every_arc_and_hole_under_one_label_with_its_end(graph, tmp_path):
    import resolve_edges as rx
    edges, holes, coverage = css.rows(graph, "stylesheet@test")
    assert len(edges) == len(graph["edges"]) and len(holes) == len(graph["holes"])
    assert {row["language"] for row in edges + holes} == {"stylesheet"}
    assert {row["reference_id"] for row in edges + holes} == {None}
    by_site = {(row["file"], row["l0"], row["kind"], row["symbol"]): row for row in edges}
    cdn = by_site[(H, 14, "import", CDN)]
    assert (cdn["verdict"], cdn["external"]["package"], cdn["external"]["version"]) == ("external", "@acme/ui", "1.2.3")
    assert by_site[(T, 1, "import", B)]["verdict"] == "namespace"
    spin = by_site[(T, 33, "keyframes", SPIN)]
    assert (spin["verdict"], spin["confidence"], spin["payload"]["name"]) == ("project-value", "confirmed", "spin")
    accent = by_site[(T, 31, "custom-property", f"{T}:6 --accent")]
    assert accent["confidence"] == "uncertain" and set(accent["payload"]["uncertain"]["candidates"]) == set(ACCENT)
    missing = next(row for row in holes if (row["file"], row["l0"], row["class"]) == (T, 32, "undeclared"))
    assert missing["reason"].startswith("--missing")
    rx.write_edge_store(tmp_path / "edges.sqlite", edges, {"schema": rx.EDGE_SCHEMA}, holes)
    import sqlite3
    with sqlite3.connect(tmp_path / "edges.sqlite") as connection:
        assert connection.execute("SELECT manager, package, version FROM externals WHERE symbol = ?",
                                  (CDN,)).fetchone() == ("npm", "@acme/ui", "1.2.3")


def test_the_coverage_counts_every_site_once(graph):
    _edges, _holes_, coverage = css.rows(graph, "stylesheet@test")
    assert "violations" not in coverage
    assert coverage["sites"] == len(graph["sites"])
    assert coverage["sites"] == sum(coverage["answered"].values()) + sum(
        item["count"] for item in coverage["holes"].values())
    assert coverage["files"] == graph["files"] and coverage["state"] == "lower-bound"


def test_a_site_without_a_row_breaks_the_coverage(graph):
    hole = next(item for item in graph["holes"] if item["class"] == "undeclared")
    broken = {**graph, "holes": [item for item in graph["holes"] if item is not hole]}
    _edges, _holes_, coverage = css.rows(broken, "stylesheet@test")
    assert coverage["violations"] == {"custom-property": [f"{hole['site']} {hole['ref'][2]}"]}


# The runner's contract: relative paths, and the cause of a run without data.
def test_recorded_payloads_and_outputs_name_no_absolute_path():
    """Every file a payload or an output names (`path`, `files`, `extends`, `tailwind`, `config`, `to`) is relative to
    the project's root, so the runner decides where the engines run."""
    import re
    absolute = re.compile(r"^(?:/|[A-Za-z]:[\\/])")
    keys = {"path", "files", "extends", "tailwind", "config", "to"}

    def named(value):
        if isinstance(value, dict):
            for name, item in value.items():
                if name in keys:
                    yield from (item if isinstance(item, list) else [item])
                yield from named(item)
        elif isinstance(value, list):
            for item in value:
                yield from named(item)
    for path in sorted(RECORDED.glob("*.json")):
        recording = json.loads(path.read_text(encoding="utf-8"))
        found = [text for call in recording["calls"] for text in (*named(call["payload"]), *named(call["data"]))
                 if isinstance(text, str) and absolute.match(text)]
        assert found == [], (path.name, found[:3])


def test_an_engine_that_cannot_run_makes_the_graph_unavailable(tmp_path):
    from indexers import runtime
    project, _recording = project_copy("css-sass", tmp_path)

    def runner(script, payload):
        return None, {"seconds": 0.1, "peak_mb": None, "stderr_tail": "", "state": "unavailable",
                      "reason": "the container allows 512 MB; sass-parser needs more", "install": "raise the limit"}
    with pytest.raises(runtime.Unavailable) as raised:
        css.run(project, runner)
    assert raised.value.reason == "sass-parser: the container allows 512 MB; sass-parser needs more"
    assert raised.value.install == "raise the limit"


def test_a_failed_run_leaves_its_files_missing_with_the_runner_reason(tmp_path):
    project, _recording = project_copy("css-sass", tmp_path)

    def runner(script, payload):
        return None, {"seconds": 0.1, "peak_mb": None, "stderr_tail": "...", "state": "failed",
                      "reason": "exit code 1: TypeError at css_sass.js:17"}
    graph = css.run(project, runner)
    reasons = {item["reason"] for item in graph["files"]["missing"]}
    assert graph["files"]["missing"] and reasons == {"not parsed: exit code 1: TypeError at css_sass.js:17"}


# Project code runs only in Daodan's container: the project's Tailwind, its config and its plugins.
def test_a_yarn_project_on_plug_n_play_lays_its_tailwind_out_in_node_modules_and_says_so(tmp_path):
    """D-157's rule for the stylesheet stage: Daodan's Tailwind script finds the project's package only in
    `node_modules/tailwindcss` (`css_tailwind.js`), which Yarn's Plug'n'Play does not write. The Tailwind runner's
    restore lays the same lockfile out in node_modules (`typescript.node_modules`), and the stage's result says so
    with a `build_edited` gap; the dynamic step keeps the project's own linker."""
    from unittest import mock
    import container
    import preparation
    from indexers import css_tailwind, runtime
    project = tmp_path / "proj"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text(json.dumps({"packageManager": "yarn@4.9.1",
                                                      "devDependencies": {"tailwindcss": "^3.4.0"}}), encoding="utf-8")
    (project / "yarn.lock").write_text("", encoding="utf-8")
    (project / ".yarnrc.yml").write_text("enableTelemetry: false\n", encoding="utf-8")
    seen = {}

    def run_in_container(copy, command, **options):
        seen.update(options)
        out = Path(options["out_dir"]) / "out"
        out.mkdir(parents=True)
        (out / "css_tailwind-out.json").write_text(json.dumps({"version": "3.4.19", "valid": {}, "error": None}),
                                                   encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": ["css_tailwind-out.json"]}
    with mock.patch.object(container, "run_in_container", run_in_container), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        runner = css.tailwind_runner(project, tmp_path / "work")
        css_tailwind.index(project, runner, ["flex"])
    prepare = seen["prepare"][-1]
    assert prepare.index("export YARN_NODE_LINKER=node-modules") < prepare.index("corepack yarn install")
    edited = {"kind": "build_edited", "path": ".", "detail": (
        "Yarn's Plug'n'Play (.yarnrc.yml sets no nodeLinker, or pnp): the index's restore lays the same lockfile out "
        "in node_modules (YARN_NODE_LINKER=node-modules) in the container's copy, as Daodan's Tailwind script finds "
        "the project's tailwindcss only in node_modules")}
    assert runner.gaps == [edited]
    built = {"indexer": {"version": "x"}}
    with mock.patch.object(runtime, "memory"), mock.patch.object(css, "node_runner"), \
            mock.patch.object(css, "tailwind_runner", return_value=runner), mock.patch.object(css, "run",
                                                                                         return_value=built):
        assert css.index(project, tmp_path / "work", files=[])["gaps"] == [edited]


def test_the_projects_tailwind_runs_in_the_container_and_never_on_the_host(tmp_path):
    """Loading the project's `tailwindcss`, its config and its plugins runs the project's code: the Tailwind engine
    runs in the container, its packages restored the project's own way in the preparation, the script in the copy
    with no network; nothing of it starts on the host. Without a container its run says why, and the rest of the
    graph goes on."""
    from unittest import mock
    import code_graph
    import container
    import preparation
    from indexers import css_tailwind
    project = tmp_path / "proj"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{"devDependencies": {"tailwindcss": "^3.4.0"}}', encoding="utf-8")
    (project / "package-lock.json").write_text("{}", encoding="utf-8")
    (project / "tailwind.config.js").write_text("module.exports = {}\n", encoding="utf-8")
    seen = {}

    def run_in_container(copy, command, **options):
        seen.update(options, command=command, copy=copy)
        out = Path(options["out_dir"]) / "out"
        out.mkdir(parents=True)
        (out / "css_tailwind-out.json").write_text(json.dumps(
            {"version": "3.4.19", "valid": {"flex": 1}, "error": None}), encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": ["css_tailwind-out.json"]}
    with mock.patch.object(container, "run_in_container", run_in_container), \
            mock.patch.object(code_graph, "measured", side_effect=AssertionError("Tailwind ran on the host")), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        found = css_tailwind.index(project, css.tailwind_runner(project, tmp_path / "work"), ["flex", "nope"])
        inputs = seen["inputs"]()
    assert (found["version"], found["valid"], found["config"]) == ("3.4.19", {"flex": 1}, "tailwind.config.js")
    prepare, execute = seen["prepare"][-1], seen["command"][-1]
    assert "npm ci" in prepare and "node-v" in prepare and "css_tailwind" not in prepare
    assert "css_tailwind.js" in execute and "npm" not in execute
    assert set(preparation.NODE_REGISTRIES) <= set(seen["registries"])
    assert inputs[f"{preparation.IN}/css_tailwind.js"] == css_tailwind.SCRIPT
    gap = {"state": "gap", "cause": "no container engine answers", "remedy": "start one"}
    with mock.patch.object(container, "run_in_container", return_value=gap):
        found = css_tailwind.index(project, css.tailwind_runner(project, tmp_path / "again"), ["flex"])
    assert found["valid"] is None and "only in a container: no container engine answers" in found["error"]
    (project / "package.json").write_text('{"dependencies": {"react": "^19"}}', encoding="utf-8")
    assert css_tailwind.index(project, None, ["flex"])["error"] == "tailwindcss not declared"  # nothing runs


def test_a_css_style_block_of_a_component_with_apply_is_read_beside_its_template(tmp_path):
    """hoppscotch: a Vue component whose CSS `<style>` block uses `@apply` stopped the stage (KeyError 'scopes'):
    the `@apply` is a reference of the sheet, not a class site of the template, and takes no `:deep()` scopes."""
    component = {"blocks": [{"line": 4, "lang": "css", "scoped": True, "module": None,
                             "text": ".row { @apply flex; }\n"}],
                 "classes": [{"kind": "class", "line": 2, "chain": [], "alts": [[{"s": "row"}]]}],
                 "imports": [], "components": [], "roots": [2]}

    def runner(script, payload):
        assert Path(script).name == "css_vue.js"
        return {"version": "3.5.13", "components": {"App.vue": component}}, {"seconds": 0}
    found = css.component_files(runner, tmp_path, ["App.vue"])
    assert found["missing"] == {}
    [apply] = [r for r in found["records"] if r["t"] == "classes" and r.get("chain") == ["@apply"]]
    [site] = [r for r in found["records"] if r["t"] == "classes" and r.get("root")]
    assert "scopes" not in apply and ["deep:App.vue", []] in site["scopes"]


def test_a_tailwind_utility_is_answered_by_the_tailwind_that_generates_it_at_its_version(tmp_path):
    """memos: Tailwind 4 is `web/`'s, not the root's; the run reads each entry with the Tailwind Node resolves from
    its folder, and says per token which version generates it: the external node carries that one."""
    project = tmp_path / "memos"
    (project / "web/src").mkdir(parents=True)
    (project / "web/package.json").write_text('{"devDependencies": {"tailwindcss": "^4.2.4"}}', encoding="utf-8")
    (project / "web/src/index.css").write_text('@import "tailwindcss";\n', encoding="utf-8")
    (project / "web/index.html").write_text('<div class="flex nope"></div>\n', encoding="utf-8")
    asked = []

    def runner(script, payload):
        asked.append((Path(script).name, [entry["path"] for entry in payload["entries"]]))
        return {"version": "4.2.4", "valid": {"flex": "4.2.4"}, "error": None}, {"seconds": 0}
    built = css.run(project, runner)
    assert asked == [("css_tailwind.js", ["web/src/index.css"])]
    [edge] = [edge for edge in built["edges"] if edge["symbol"] == ".flex"]
    assert edge["to"] == "tailwindcss flex" and edge["end"] == "external"
    assert {n["id"]: n["external"] for n in built["nodes"]}["tailwindcss flex"] == {
        "manager": "npm", "package": "tailwindcss", "version": "4.2.4"}
    assert [(hole["name"], hole["class"]) for hole in built["holes"] if hole["kind"] == "class"] == [("nope", "no-rule")]


def test_the_scripts_program_resolves_the_aliases_the_pre_map_states(tmp_path):
    """memos, full-stack-fastapi: `cn` is imported through `@/lib/utils`, an alias of `web/tsconfig.json`, and the
    root holds no tsconfig. The program extends the tsconfig the pre-map names and carries every unit's aliases,
    from the root, as the TypeScript analyzer's does."""
    from indexers import css_typescript
    record = {"units": [{"root": "web", "kind": "npm-package", "name": "web",
                         "config": {"tsconfig": ["web/tsconfig.json"], "paths": {"@/*": ["web/src/*"]}}}]}
    options = css.structure(record)
    assert options == {"tsconfig": "web/tsconfig.json", "paths": {"@/*": ["web/src/*"]}}
    asked = []

    def runner(script, payload):
        asked.append(payload["tsconfig"])
        return {"typescript": "5.9.3", "files": [], "records": []}, {"seconds": 0}
    (tmp_path / "web/src").mkdir(parents=True)
    (tmp_path / "web/tsconfig.json").write_text('{"compilerOptions": {"jsx": "react-jsx"}}', encoding="utf-8")
    css_typescript.index(tmp_path, runner, ["web/src/a.tsx"], **options)
    [config] = asked
    assert config["extends"] == "./web/tsconfig.json" and config["compilerOptions"]["paths"] == {"@/*": ["web/src/*"]}
    assert "jsx" not in config["compilerOptions"]  # the project's own options, from the tsconfig it extends
    css_typescript.index(tmp_path, runner, ["a.ts"])
    assert "extends" not in asked[-1] and "paths" not in asked[-1]["compilerOptions"]  # without a pre-map, as before


MARKING = {  # project files that, run as code, leave a mark in `marks/`: none of the host's engines runs one
    "mark.js": 'require("fs").writeFileSync(require("path").join(__dirname, "marks", process.argv[2] || "x"), "")\n',
    "postcss.config.js": 'require("./mark.js"); require("fs").writeFileSync(__dirname + "/marks/postcss", "")\n',
    "tailwind.config.js": 'require("fs").writeFileSync(__dirname + "/marks/tailwind", ""); module.exports = {}\n',
    "svelte.config.js": 'require("fs").writeFileSync(__dirname + "/marks/svelte-config", "")\n',
    "vite.config.js": 'require("fs").writeFileSync(__dirname + "/marks/vite-config", "")\n',
    "less-plugin.js": 'require("fs").writeFileSync(__dirname + "/marks/less-plugin", ""); module.exports = {}\n',
    "stylus-plugin.js": 'require("fs").writeFileSync(__dirname + "/marks/stylus-plugin", "");'
                        ' module.exports = () => () => {}\n',
    "node_modules/ts-mark/index.js": 'require("fs").writeFileSync(__dirname + "/../../marks/ts-plugin", "");'
                                     ' module.exports = () => ({ create: (info) => info.languageService })\n',
    "package.json": '{"name": "marks", "devDependencies": {"tailwindcss": "^3.4.0"},'
                    ' "scripts": {"postinstall": "node mark.js postinstall"}}\n',
    "tsconfig.json": '{"compilerOptions": {"allowJs": true, "plugins": [{"name": "ts-mark"}]}}\n',
    "a.less": '@plugin "./less-plugin.js";\n.a { width: `require("fs").writeFileSync("marks/less-js", "")`; }\n',
    "a.styl": 'use("./stylus-plugin.js")\n.b\n  color red\n',
    "a.scss": '@use "sass:meta";\n.c { color: red; }\n',
    "App.vue": '<script setup>\nrequire("fs").writeFileSync("marks/vue-script", "")\n</script>\n'
               '<template><div class="a"></div></template>\n<style lang="less">@plugin "./less-plugin.js";</style>\n',
    "C.svelte": '<script>\nrequire("fs").writeFileSync("marks/svelte-script", "")\n</script>\n<div class="b"></div>\n',
    "P.astro": '---\nimport fs from "fs";\nfs.writeFileSync("marks/astro", "");\n---\n<div class="c"></div>\n',
    "index.ts": 'require("fs").writeFileSync("marks/script", "");\ndocument.body.className = "a";\n',
}


def test_the_engines_on_the_host_read_the_projects_files_and_run_none(tmp_path):
    """AGENTS.md: the project's code runs only in the container. The stylesheet engines Daodan starts on the host
    (sass-parser, less, stylus, the Vue, Svelte and Astro compilers, TypeScript, in `css.node_runner`) parse a
    project whose config files, plugins, component scripts and inline JavaScript each leave a mark when run: every
    engine reads them, and no mark appears. Tailwind, which loads its config, runs only in the container (off in
    the suites: a gap, no run). Real engines: Node and the pinned engines are installed (on Modal)."""
    project = tmp_path / "project"
    for rel, text in MARKING.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    (project / "marks").mkdir()
    result = css.index(project, tmp_path / "work", files=css.walk(project))
    engines = {engine["name"]: engine["version"] for engine in result["graph"]["engines"]}
    assert {"sass-parser", "less", "stylus", "@vue/compiler-sfc", "svelte", "@astrojs/compiler", "typescript"} <= set(
        engines) and all(engines[name] for name in engines if name != "tailwindcss"), engines
    assert engines["tailwindcss"] is None  # no container in the suites: Tailwind did not run
    assert {item["path"] for item in result["graph"]["files"]["missing"]} <= {"P.astro"}, result["graph"]["files"]
    assert sorted(path.name for path in (project / "marks").iterdir()) == []
    # The control: run as code, a marking file does leave its mark.
    import subprocess
    import resolve_edges as rx
    from indexers import runtime
    node = runtime.node(project) / rx.executable_name("node")
    subprocess.run([str(node), "less-plugin.js"], cwd=project, check=True)
    assert sorted(path.name for path in (project / "marks").iterdir()) == ["less-plugin"]


def test_a_helper_imported_from_a_package_not_installed_is_read_by_the_package_its_import_names(tmp_path):
    """memos, full-stack-fastapi: the checkout's packages are not restored on the host, so `clsx` and `twMerge`
    have no declaration; their imports name the packages, and `cn`, which returns `twMerge(clsx(inputs))`, is
    read as tailwind-merge: its literal arguments are class sites, not a `call` hole. memos merges with the
    function `extendTailwindMerge` makes, which has twMerge's signature (tailwind-merge's API reference). A project
    module's import names no package (real TypeScript, on Modal)."""
    project = tmp_path / "project"
    (project / "src/lib").mkdir(parents=True)
    (project / "src/lib/utils.ts").write_text(
        'import { clsx } from "clsx";\nimport { twMerge } from "tailwind-merge";\n'
        "export function cn(...inputs: unknown[]) {\n  return twMerge(clsx(inputs));\n}\n", encoding="utf-8")
    (project / "src/lib/merge.ts").write_text(
        'import { clsx } from "clsx";\nimport { extendTailwindMerge } from "tailwind-merge";\n'
        "const merge = extendTailwindMerge({ extend: {} });\n"
        "export function cx(...inputs: unknown[]) {\n  return merge(clsx(inputs));\n}\n", encoding="utf-8")
    (project / "src/lib/own.ts").write_text("export function own(...xs: string[]) { return xs.join(' '); }\n",
                                            encoding="utf-8")
    (project / "src/App.tsx").write_text(
        'import { cn } from "./lib/utils";\nimport { own } from "./lib/own";\n'
        'export const A = (ok: boolean) => <div className={cn("flex", ok && "p-4")} id={own("x")} />;\n'
        'export const B = () => <p className={own("gap-2")} />;\n'
        'import { cx } from "./lib/merge";\nexport const C = () => <i className={cx("grid", "m-1")} />;\n',
        encoding="utf-8")
    built = css.run(project, css.node_runner(project, tmp_path / "work"), css.walk(project))
    holes = {(hole["name"], hole["class"]) for hole in built["holes"] if hole["kind"] == "class"}
    assert {("flex", "no-rule"), ("p-4", "no-rule"), ("grid", "no-rule"), ("m-1", "no-rule")} <= holes, holes
    assert [name for name, cls in holes if cls == "call"] == ['own("gap-2")']


def test_a_sheet_tailwind_imports_from_a_package_is_found_as_its_build_finds_it(tmp_path):
    """memos: `@import "@usememos/ui/tokens.css"` is the package's `exports` entry `./dist/tokens.css`, and Tailwind 4
    failed with "cannot load stylesheet". A sheet is found as `@tailwindcss/node` finds it: through `exports`
    (conditions `style`, then `default`), and a package from the importing sheet's real folder up, so a pnpm store's
    sheet reaches its own dependencies. The Tailwind here is a stand-in this test writes, which loads every
    `@import` through the script's loader and generates `text-<name>` for each `--color-<name>` it reads: running
    the script outside a container runs no project's code."""
    import os
    import subprocess
    import resolve_edges as rx
    from indexers import css_tailwind, runtime
    project = tmp_path / "memos"
    modules = project / "web/node_modules"

    def write(rel, text):
        (modules / rel).parent.mkdir(parents=True, exist_ok=True)
        (modules / rel).write_text(text, encoding="utf-8")
    (project / "web/src").mkdir(parents=True)
    (project / "web/package.json").write_text('{"dependencies": {"tailwindcss": "^4.0.0", "@acme/ui": "1.0.0"}}',
                                              encoding="utf-8")
    (project / "web/src/index.css").write_text('@import "tailwindcss";\n@import "@acme/ui/tokens.css";\n',
                                               encoding="utf-8")
    write("tailwindcss/package.json", '{"name": "tailwindcss", "version": "4.0.0", "main": "index.js",'
                                      ' "style": "index.css"}')
    write("tailwindcss/index.css", "")
    write("tailwindcss/index.js", """
exports.__unstable__loadDesignSystem = async (css, { base, loadStylesheet }) => {
  const made = new Set();
  const read = async (text, from) => {
    for (const [, name] of text.matchAll(/--color-([\\w-]+)/g)) made.add(`text-${name}`);
    for (const [, id] of text.matchAll(/@import "([^"]+)"/g)) {
      const sheet = await loadStylesheet(id, from);
      await read(sheet.content, sheet.base);
    }
  };
  await read(css, base);
  return { getClassOrder: (tokens) => tokens.map((token) => [token, made.has(token) ? 1n : null]) };
};
""")
    store = ".pnpm/@acme+ui@1.0.0/node_modules/@acme"
    write(f"{store}/ui/package.json", '{"name": "@acme/ui", "exports": {".": "./dist/index.js",'
                                     ' "./tokens.css": "./dist/tokens.css", "./*.css": {"style": "./dist/*.css"}}}')
    write(f"{store}/ui/dist/tokens.css", '@import "@acme/base";\n@import "@acme/ui/theme.css";\n'
                                         ":root { --color-ui-a: red; }\n")
    write(f"{store}/ui/dist/theme.css", ":root { --color-ui-theme: red; }\n")
    write(f"{store}/base/package.json", '{"name": "@acme/base", "exports": {".": {"types": "./index.d.ts",'
                                       ' "style": "./base.css", "default": "./index.js"}}}')
    write(f"{store}/base/base.css", ":root { --color-base-x: red; }\n")
    (modules / "@acme").mkdir()
    os.symlink(modules / store / "ui", modules / "@acme/ui", target_is_directory=True)  # pnpm's link
    node = runtime.node(tmp_path) / rx.executable_name("node")

    def run_here(script, payload):
        config, out = tmp_path / "config.json", tmp_path / "out.json"
        config.write_text(json.dumps(payload), encoding="utf-8")
        done = subprocess.run([str(node), str(script), str(config), str(out)], cwd=project, capture_output=True,
                              text=True)
        assert done.returncode == 0, done.stderr
        return json.loads(out.read_text(encoding="utf-8")), {"seconds": 0}
    found = css_tailwind.index(project, run_here, ["text-ui-a", "text-ui-theme", "text-base-x", "text-nope"],
                               ["web/src/index.css"])
    assert (found["error"], found["valid"]) == (None, {"text-ui-a": "4.0.0", "text-ui-theme": "4.0.0",
                                                       "text-base-x": "4.0.0"})


@pytest.mark.parametrize("script", ["css_tailwind.js", "typescript_unbound.js"])
def test_a_script_that_runs_only_in_the_container_parses(tmp_path, script):
    """No suite runs a container, so these scripts are parsed here (`node --check`, which runs nothing): a syntax
    error would otherwise reach only the real run."""
    import subprocess
    import resolve_edges as rx
    from indexers import css_tailwind, runtime
    node = runtime.node(tmp_path) / rx.executable_name("node")
    done = subprocess.run([str(node), "--check", str(css_tailwind.SCRIPT.parent / script)], capture_output=True,
                          text=True)
    assert done.returncode == 0, done.stderr


def test_a_package_sheet_is_found_through_the_packages_exports_as_its_build_finds_it(tmp_path):
    """memos: `@import "@usememos/ui/styles.css"` names the package's `exports` entry `./dist/styles.css`, so the
    import was an `unresolved-import` even with the package installed. A subpath goes through `exports` (Node's
    rules: its own key, else a `*` pattern), a condition object gives its `style` target (`sass` first for Sass, as
    Sass's package importer asks) and `default`; a package without `exports` gives its own file, as before."""
    project = tmp_path / "web"
    ui = project / "node_modules/.pnpm/@acme+ui@1.2.3/node_modules/@acme/ui"
    (ui / "dist").mkdir(parents=True)
    (ui / "package.json").write_text(json.dumps({"name": "@acme/ui", "version": "1.2.3", "exports": {
        ".": {"types": "./index.d.ts", "default": "./dist/index.js"}, "./styles.css": "./dist/styles.css",
        "./themes/*.css": {"sass": "./dist/*.scss", "style": "./dist/*.css"}}}), encoding="utf-8")
    for name in ("styles.css", "dark.css", "dark.scss", "index.js"):
        (ui / "dist" / name).write_text("", encoding="utf-8")
    (project / "node_modules/@acme").mkdir()
    (project / "node_modules/@acme/ui").symlink_to(ui, target_is_directory=True)  # pnpm's link
    plain = project / "node_modules/plain"
    plain.mkdir()
    (plain / "package.json").write_text('{"name": "plain", "version": "2.0.0"}', encoding="utf-8")
    (plain / "styles.css").write_text("", encoding="utf-8")
    (project / "src").mkdir()

    def found(spec, rel="src/index.css"):
        out = css.resolve(project, rel, spec)
        return out[:3] if out[0] == "external" else out
    ui_package = {"manager": "npm", "package": "@acme/ui", "version": "1.2.3"}
    assert found("@acme/ui/styles.css") == ("external", "@acme/ui/dist/styles.css", ui_package)
    assert found("@acme/ui/themes/dark.css") == ("external", "@acme/ui/dist/dark.css", ui_package)
    assert found("@acme/ui/themes/dark.css", "src/app.scss") == ("external", "@acme/ui/dist/dark.scss", ui_package)
    assert found("plain/styles.css") == ("external", "plain/styles.css",
                                         {"manager": "npm", "package": "plain", "version": "2.0.0"})
    assert found("@acme/ui/missing.css") == ("hole", "unresolved-import", "@acme/ui/missing.css")


def test_the_restores_package_sheets_come_back_where_the_graph_looks_for_them(tmp_path):
    """memos: @usememos/ui's sheets exist only after the restore, in the container. `css_packages.js` copies, for
    each package an import names from a folder, its package.json and stylesheets from where Node finds it from that
    folder (pnpm's link followed), under the link's path; a package one of those sheets imports, nested in the
    importing package's folder, where the graph's walk up finds it as Node does from the real folder. A workspace
    link to a folder of the project is the project's own. It only reads files: run here, nothing of the project
    runs (the package's index.js would leave a mark)."""
    import os
    import subprocess
    import resolve_edges as rx
    from indexers import css_tailwind, runtime
    work = tmp_path / "work"

    def write(rel, text):
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_text(text, encoding="utf-8")
    store = "web/node_modules/.pnpm/@acme+ui@1.0.0/node_modules/@acme"
    write(f"{store}/ui/package.json", '{"name": "@acme/ui", "version": "1.0.0"}')
    write(f"{store}/ui/dist/styles.css", '@import "@acme/base/base.css";\n.mu-a { color: red }\n')
    write(f"{store}/ui/dist/index.js", 'require("fs").writeFileSync(__dirname + "/../../../../../../mark", "");\n')
    write(f"{store}/base/package.json", '{"name": "@acme/base", "version": "2.0.0"}')
    write(f"{store}/base/base.css", ".base { color: blue }\n")
    write("packages/own/package.json", '{"name": "@acme/own"}')
    write("packages/own/own.css", ".own {}\n")
    (work / "web/node_modules/@acme").mkdir()
    os.symlink(work / store / "ui", work / "web/node_modules/@acme/ui", target_is_directory=True)
    os.symlink(work / "packages/own", work / "web/node_modules/@acme/own", target_is_directory=True)
    (work / "web/src").mkdir()
    config, out = tmp_path / "in.json", tmp_path / "out.json"
    config.write_text(json.dumps({"packages": [["web/src", "@acme/ui"], ["web/src", "@acme/own"],
                                               ["web/src", "@acme/none"]]}), encoding="utf-8")
    node = runtime.node(tmp_path) / rx.executable_name("node")
    done = subprocess.run([str(node), str(css_tailwind.SCRIPT.with_name("css_packages.js")), str(config), str(out)],
                          cwd=work, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert sorted(data["files"]) == ["web/node_modules/@acme/ui/dist/styles.css",
                                     "web/node_modules/@acme/ui/node_modules/@acme/base/base.css",
                                     "web/node_modules/@acme/ui/node_modules/@acme/base/package.json",
                                     "web/node_modules/@acme/ui/package.json"]
    assert (data["missing"], data["workspace"], data["error"]) == ([["web/src", "@acme/none"]],
                                                                   [["web/src", "@acme/own"]], None)
    assert not (work / "mark").exists()


def test_a_class_a_package_sheet_declares_is_answered_by_the_restores_copy_of_it(tmp_path, monkeypatch):
    """The checkout holds no node_modules: the package an import names and the checkout lacks is asked of the
    container (`css_packages.js`, after the restore), and its sheets, back with their text, answer the classes they
    declare as the package's, at the version its package.json says. A package the checkout holds is not asked."""
    project = tmp_path / "memos"
    (project / "web/src").mkdir(parents=True)
    (project / "web/src/index.css").write_text('@import "@acme/ui/styles.css";\n', encoding="utf-8")
    (project / "web/index.html").write_text('<link rel="stylesheet" href="/src/index.css">\n<div class="mu-a"></div>\n',
                                            encoding="utf-8")
    calls = []
    package = json.dumps({"name": "@acme/ui", "version": "1.2.3", "exports": {"./styles.css": "./dist/styles.css"}})

    def container(script, payload):
        calls.append((Path(script).name, payload))
        return {"files": {"web/node_modules/@acme/ui/package.json": package,
                          "web/node_modules/@acme/ui/dist/styles.css": ".mu-a { color: red }\n",
                          "web/node_modules/@acme/ui/../../../out.css": "", "web/node_modules/x/..\\..\\out.css": "",
                          "../out.css": ""},  # names that would leave the copy's folder: not written
                "missing": [], "workspace": [], "error": None}, {"seconds": 0}

    def host(script, payload):
        raise AssertionError(f"no host engine reads these files: {script}")
    (tmp_path / "tmp").mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))  # where the copy is written, and removed
    built = css.run(project, host, css.walk(project), tailwind=container)
    assert calls == [("css_packages.js", {"packages": [["web/src", "@acme/ui"]]})]
    assert [(hole["name"], hole["class"]) for hole in built["holes"]] == []
    [edge] = [edge for edge in built["edges"] if edge["symbol"] == ".mu-a"]
    assert {node["id"]: node.get("external") for node in built["nodes"]}[edge["to"]] == {
        "manager": "npm", "package": "@acme/ui", "version": "1.2.3"}
    assert "daodan-sheets-" not in json.dumps(built)  # the copy is read, never named, and removed after
    assert not list(tmp_path.rglob("out.css")) and not list((tmp_path / "tmp").iterdir())
    ui = project / "web/node_modules/@acme/ui"
    (ui / "dist").mkdir(parents=True)
    (ui / "package.json").write_text(package, encoding="utf-8")
    (ui / "dist/styles.css").write_text(".mu-a { color: red }\n", encoding="utf-8")
    calls.clear()
    css.run(project, host, css.walk(project), tailwind=container)
    assert calls == []


def test_tailwinds_run_brings_back_the_packages_sheets_after_the_same_restore(tmp_path):
    """One restore for both: the stage asks Tailwind's verdicts and the unserved packages' sheets in one container
    run, the scripts one after the other in its execution, and reads each one's answer."""
    from unittest import mock
    import container
    import preparation
    project = tmp_path / "web"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{"dependencies": {"tailwindcss": "^4.0.0", "@acme/ui": "1.0.0"}}',
                                          encoding="utf-8")
    (project / "src/index.css").write_text('@import "tailwindcss";\n@import "@acme/ui/styles.css";\n',
                                           encoding="utf-8")
    (project / "index.html").write_text(
        '<link rel="stylesheet" href="/src/index.css">\n<div class="flex mu-a"></div>\n', encoding="utf-8")
    runs = []

    def run_in_container(copy, command, **options):
        runs.append((command[-1], {Path(key).name: value for key, value in options["inputs"]().items()}))
        out = Path(options["out_dir"]) / "out"
        out.mkdir(parents=True)
        (out / "css_tailwind-out.json").write_text(
            json.dumps({"version": "4.0.0", "valid": {"flex": "4.0.0"}, "error": None}), encoding="utf-8")
        (out / "css_packages-out.json").write_text(json.dumps({"files": {
            "node_modules/@acme/ui/package.json": '{"name": "@acme/ui", "version": "1.0.0"}',
            "node_modules/@acme/ui/styles.css": ".mu-a { color: red }\n"}, "missing": [], "workspace": [],
            "error": None}), encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": []}

    def host(script, payload):
        raise AssertionError(f"no host engine reads these files: {script}")
    with mock.patch.object(container, "run_in_container", run_in_container), \
            mock.patch.object(preparation, "fetched", lambda url, digest, name: Path(name)):
        built = css.run(project, host, css.walk(project), tailwind=css.tailwind_runner(project, tmp_path / "work"))
    [(execute, inputs)] = runs
    assert execute.index("css_tailwind.js") < execute.index("css_packages.js")
    assert json.loads(inputs["css_packages-in.json"].read_text(encoding="utf-8")) == {
        "packages": [["src", "@acme/ui"], ["src", "tailwindcss"]]}
    assert inputs["css_packages.js"] == css.PACKAGES
    assert [(hole["name"], hole["class"]) for hole in built["holes"] if hole["kind"] == "class"] == []
