"""CSS, the graph of the stylesheets and of every place that names what they declare, on Modal: tududi.

Wiring only: the three CSS adapters (`adapters/css.py`, the product's stylesheet parser and the HTML parser, which
also assembles the graph; `adapters/css_typescript.py`, the TypeScript compiler; `adapters/css_tailwind.py`, the
project's Tailwind) and the volume. One container: the checkout at its pinned commit, the files of the snapshot
`modal_scip.py` kept (`scip-inputs/<case>/manifest.sqlite`: stylesheets, HTML/EJS, scripts), the project's
packages as the engine pass installs them (`npm ci --ignore-scripts`), then the graph and the hand check. No model.

    modal deploy benchmarks/inference-audit/lang_css.py
    python benchmarks/inference-audit/lang_css.py spawn --cases tududi
    python benchmarks/inference-audit/lang_css.py fetch --cases tududi

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
import scip_graph  # noqa: E402
from adapters import css  # noqa: E402
from modal_audit import CASES, _source  # noqa: E402

NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")  # as modal_scip.py
CODE = ("css.py", "css_typescript.py", "css_typescript.js", "css_tailwind.py", "css_tailwind.js")
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
HAND = [
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
              "DAODAN_NODE_BIN": "/opt/node/bin"})
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "scip_graph.py" if LOCAL else Path("/audit/scip_graph.py"), "/audit/scip_graph.py")
        .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                       ignore=["**/__pycache__/**"])
    )


app = modal.App("daodan-graph-css", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_sha256() -> dict:
    folder = Path(css.__file__).parent
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()[:12] for name in CODE}


def inventory(manifest: Path) -> list[str]:
    """The snapshot's stylesheets, HTML and EJS files, and scripts."""
    import sqlite3
    with sqlite3.connect(manifest) as connection:
        rows = connection.execute("SELECT file, language FROM sem_coverage").fetchall()
    return sorted(rel for rel, language in rows if language in ("css", "javascript", "typescript")
                  or rel.lower().endswith(css.MARKUP))


def _rules_naming(texts: dict, name: str) -> list[str]:
    """`file:line` of every rule whose selector names a class: a scan of braces, comments and strings of its own."""
    found, pattern = [], re.compile(r"\." + re.escape(name) + r"(?![\w-])")
    for rel, (text, offset) in texts.items():
        start, at, line, prelude = None, 0, 1 + offset, []
        while at < len(text):
            char = text[at]
            if text.startswith("/*", at):
                stop = text.find("*/", at + 2)
                stop = len(text) if stop < 0 else stop + 2
                line += text.count("\n", at, stop)
                at = stop
                continue
            if char in "{};":
                selector = "".join(prelude).strip()
                if char == "{" and selector and not selector.startswith("@") and pattern.search(selector):
                    found.append(f"{rel}:{start}")
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


def hand_check(graph: dict, project: Path, files: list[str]) -> list[dict]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    texts = {}
    for rel in files:
        if rel.lower().endswith(css.STYLESHEETS):
            texts[rel] = ((project / rel).read_text(encoding="utf-8"), 0)
        elif rel.lower().endswith(css.MARKUP):
            source = (project / rel).read_text(encoding="utf-8")
            for number, match in enumerate(re.finditer(r"<style[^>]*>(.*?)</style>", source, re.S)):
                texts[f"{rel}#{number}"] = (match.group(1), source[:match.start(1)].count("\n"))
    out = []
    for rel, line, kind, symbol, expected in HAND:
        found = _ends(graph, nodes, f"{rel}:{line}", kind, None if symbol == "*" else symbol)
        if symbol != "*":
            ends = set()
            for end in expected:
                rules = {re.sub(r"#\d+(?=:\d+$)", "", item) for item in _rules_naming(texts, symbol[1:])}
                ends |= rules if end == "all" else {end}
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


@app.function(cpu=2, memory=8192, timeout=3600, volumes={"/results": volume})
def css_case(name: str) -> dict:
    import os
    import shutil
    import time
    import resolve_edges as rx
    print("code", code_sha256(), flush=True)  # compared with the checkout before trusting the run
    started = time.time()
    case = CASES[name]
    work = Path("/work") / name
    shutil.rmtree(work, ignore_errors=True)
    target = _source(work / "src", case, None)
    manifest = work / "manifest.sqlite"
    shutil.copyfile(Path("/results") / TAG / "scip-inputs" / name / "manifest.sqlite", manifest)
    files = inventory(manifest)
    begun = time.time()
    modules = rx.npm_modules(target)
    installed = round(time.time() - begun, 1)
    if modules is not None and not (target / "node_modules").exists():
        os.symlink(modules, target / "node_modules", target_is_directory=True)
    graph = css.run(target, work / "engine", files)
    checks = {"case": name, "commit": case["commit"], "code": code_sha256(), "files_given": len(files),
              "npm_install_seconds": installed, "node_modules": str(modules),
              "report": scip_graph.report(graph), "summary": summary(graph),
              "hand_check": hand_check(graph, target, files), "seconds": round(time.time() - started, 1)}
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
