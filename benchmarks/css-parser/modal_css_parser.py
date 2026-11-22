"""The stylesheet graph's CSS engine (`daodan/core/indexers/css_csstree.js`, `@eslint/css-tree`) on Modal.

Wiring only, like `benchmarks/inference-audit/lang_css.py` (the image, the Node runner): the checkout's own code runs in
a container with the pinned Node and the pinned engines (`css_engines/`, installed from the lockfile with
`--ignore-scripts`). Nothing runs on the host. `modal run` is ephemeral: nothing is deployed.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run \\
        benchmarks/css-parser/modal_css_parser.py::<entry>

    lock_check        the lockfile npm writes for the pinned package, against the one in the tree
    record_fixtures   the engine runs of the test fixtures, added to tests/fixtures/css-graph/recorded/
    ab_run            the A/B of the graph's records on the corpus: the old reader (OLD_SHA) against the engine
    measure_run       the values of the Sass, Less and Stylus trees, read by `declaration` and by the engine
    cssinjs_run       the graph of a styled-components project with its scripts' CSS read by the engine and by hand
    probe_run         a Node script beside the pinned engines and the corpus (`--script FILE`)

README.md says what each measured.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
REPO = HERE.parents[1] if LOCAL else Path("/repo")
PLUGIN = REPO / "daodan" if LOCAL else Path("/daodan/map")
ENGINES = PLUGIN / "core/indexers/css_engines"
TESTS = REPO / "tests" if LOCAL else Path("/tests")
RESULTS = HERE / "results"
NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")  # as lang_css.py
OLD_SHA = "f9440f8e9"  # the commit whose `indexers/css.py` is the A/B's old side (the hand reader `_sheet`)
CORPUS = "/corpus/node_modules"
sys.path.insert(0, str(PLUGIN / "core"))  # `indexers`, `languages`: the checkout's code, read as the container has it


def _image():
    node = f"node-{NODE[0]}-linux-x64.tar.xz"
    image = (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "xz-utils")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "pytest==8.4.2")
        .run_commands(
            f"curl -fsSL https://nodejs.org/dist/{NODE[0]}/{node} -o /tmp/{node}",
            f"echo '{NODE[1]}  /tmp/{node}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{node} -C /opt/node --strip-components=1 && rm /tmp/{node}",
        )
        .env({"PATH": "/opt/node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"})
        .add_local_dir(ENGINES, "/engines", copy=True)
        .run_commands("cd /engines && npm ci --ignore-scripts --no-audit --no-fund --loglevel=error")
        # The corpus: the npm packages of candidates/corpus-packages.txt at exact versions, one at a time, as the
        # candidates' benchmark installs them; their `.css` files are read as data, nothing of them runs.
        .add_local_file(HERE / "candidates/corpus-packages.txt", "/corpus-packages.txt", copy=True)
        .run_commands(
            "mkdir -p /corpus && cd /corpus && echo '{\"name\":\"corpus\",\"private\":true}' > package.json "
            "&& while read p; do npm install --ignore-scripts --no-audit --no-fund --loglevel=error \"$p\" "
            ">/dev/null 2>&1 || echo \"FAILED $p\"; done < /corpus-packages.txt")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_dir(TESTS / "fixtures/css-graph", "/tests/fixtures/css-graph", ignore=["recorded/**"])
        .add_local_file(TESTS / "test_codebase_map_css_graph.py", "/tests/test_codebase_map_css_graph.py")
        .add_local_dir(HERE, "/bench", ignore=["results/**", "candidates/**", "**/__pycache__/**"])
    )
    return image


if LOCAL:
    app = modal.App("css-parser-benchmark", image=_image())
else:
    app = modal.App("css-parser-benchmark")


def node_runner(engines: Path, project: Path, work: Path):
    """The runner of the stylesheet graph's engines (`indexers/css_sass.py`): `node <script> IN OUT` in the project's
    root, IN the payload with `engines` added; a run without data says why (`state`, `reason`)."""
    import os
    sys.path.insert(0, str(PLUGIN / "core"))
    import code_graph

    def runner(script, payload):
        work.mkdir(parents=True, exist_ok=True)
        settings, output = work / f"{Path(script).stem}-in.json", work / f"{Path(script).stem}-out.json"
        settings.write_text(json.dumps({**payload, "engines": str(engines)}), encoding="utf-8")
        output.unlink(missing_ok=True)
        measured = code_graph.measured(["node", str(script), str(settings), str(output)], str(project),
                                       {**os.environ, "NODE_OPTIONS": "--max-old-space-size=6144"}, 3600)
        data = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
        if data is None:
            measured.update(state="failed", reason=f"exit code {measured['returncode']}: "
                                                   f"{(measured['stderr_tail'] or '').strip()[-300:]}")
        return data, measured
    return runner


# ---------------------------------------------------------------------------------------------------- the lockfile

@app.function(timeout=900)
def lock(head_lock: str) -> dict:
    """The lockfile npm writes for the pinned package. `npm ci` (the image build) proves the tree's lockfile agrees with
    its package.json; this proves it is the one npm writes: from the lockfile of the commit before (what npm adds to
    it for the new pin) and from no lockfile (what it resolves today)."""
    import shutil
    import tempfile
    tree = (ENGINES / "package-lock.json").read_text(encoding="utf-8")
    out = {"tree": tree}
    for name, start in (("from-head-lock", head_lock), ("from-nothing", None)):
        folder = Path(tempfile.mkdtemp(prefix="lock-"))
        shutil.copyfile(ENGINES / "package.json", folder / "package.json")
        if start is not None:
            (folder / "package-lock.json").write_text(start, encoding="utf-8")
        run = subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund",
                              "--loglevel=error"], cwd=folder, capture_output=True, text=True, timeout=600)
        out[name] = (folder / "package-lock.json").read_text(encoding="utf-8")
        out[name + "-log"] = run.stdout + run.stderr
    out["npm"] = subprocess.run(["npm", "--version"], capture_output=True, text=True).stdout.strip()
    return out


@app.local_entrypoint()
def lock_check():
    head = subprocess.run(["git", "show", f"{OLD_SHA}:daodan/core/indexers/css_engines/package-lock.json"], cwd=REPO,
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
    out = lock.remote(head)
    for name in ("from-head-lock", "from-nothing"):
        same = out[name] == out["tree"]
        print(f"{name}: {'identical to the tree' if same else 'DIFFERENT'} (npm {out['npm']}) {out[name + '-log'].strip()}")
    # from no lockfile npm resolves today's patch versions of the other packages: that one differs, and is not kept
    if out["from-head-lock"] != out["tree"]:
        (RESULTS / "package-lock.from-head-lock.json").write_text(out["from-head-lock"], encoding="utf-8", newline="\n")
        sys.exit(1)


# --------------------------------------------------------------------------------------------------- the fixtures

@app.function(cpu=2, memory=4096, timeout=1800)
def fixtures() -> dict:
    """Each test fixture of the stylesheet graph with its packages (`npm install --ignore-scripts`) and its engine runs
    recorded by `record` of the graph's test: `{name: recording}`."""
    import shutil
    sys.path.insert(0, "/tests")
    from test_codebase_map_css_graph import REMOTE, record
    out = {}
    for fixture in sorted(Path("/tests/fixtures/css-graph").iterdir()):
        if not fixture.is_dir() or fixture.name == "recorded":
            continue
        project = Path("/work/fixtures") / fixture.name / "fixture"
        shutil.rmtree(project.parent, ignore_errors=True)
        shutil.copytree(fixture, project)
        if (project / "package.json").is_file():
            subprocess.run(["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
                            "--no-package-lock"], cwd=project, check=True, capture_output=True, text=True, timeout=900)
        out[fixture.name] = record(project, node_runner(Path("/engines"), project, project.parent / "runs"),
                                   remote=REMOTE.get(fixture.name))
    return out


@app.local_entrypoint()
def record_fixtures():
    """Adds to each recording (`tests/fixtures/css-graph/recorded/<name>.json`) the engine runs it lacks, and drops the
    runs no payload asks for any more; the runs it has stay as they were recorded."""
    recorded = REPO / "tests/fixtures/css-graph/recorded"
    for name, new in fixtures.remote().items():
        path = recorded / f"{name}.json"
        old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() and path.stat().st_size > 100 else \
            {"calls": [], "packages": {}, "directories": []}

        def key(call):
            return call["script"], json.dumps(call["payload"], sort_keys=True)
        had, wanted = {key(call): call for call in old["calls"]}, {key(call): call for call in new["calls"]}
        # the runs of the script this folder is about are always the new ones; the others stay as they were recorded
        merged = [call if k[0] == "css_csstree" else had.get(k, call) for k, call in wanted.items()]
        added = [k[0] for k in wanted if k not in had]
        dropped = [k[0] for k in had if k not in wanted]
        failed = [call["script"] for call in new["calls"] if call["data"] is None]
        recording = {"calls": merged, "packages": {**old["packages"], **new["packages"]},
                     "directories": sorted({*old["directories"], *new["directories"]})}
        path.write_text(json.dumps(recording, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"{name}: {len(merged)} runs, added {added}, dropped {dropped}, failed {failed}")


# ------------------------------------------------------------------------------------------------------ the A/B

def _load_old(source: str, number: int):
    """The old side: `indexers/css.py` of OLD_SHA (the hand reader `_sheet` for every stylesheet), as a module of the
    `indexers` package under another name, so its relative imports are the checkout's."""
    import importlib.util
    path = Path(f"/tmp/css_old_{number}.py")  # one file per process: they run at once
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("indexers.css_old", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["indexers.css_old"] = module
    spec.loader.exec_module(module)
    return module


def _key(record: dict) -> str:
    """A record as text, its empty fields left out: `ns: null` and no `ns` are the same record."""
    return json.dumps({k: v for k, v in record.items() if v is not None}, sort_keys=True, ensure_ascii=False)


def _names(record: dict) -> str:
    """What a record is about, besides where: its name for a reference, its names for a node."""
    return json.dumps(record.get("name") if record["t"] == "ref" else record.get("names"), ensure_ascii=False)


def _line(record: dict) -> int:
    return int(record["site"].rsplit(":", 1)[1]) if record["t"] == "ref" else record.get("line") or 0


def _levels(record: dict) -> list:
    """The keys a record pairs by, the most exact first: where it is and what it is about (the name of a reference, the
    names of a node, the label it sits in), then where it is, then for a reference what it names."""
    kind, line = (record["t"], record.get("kind")), _line(record)
    about = record.get("name") if record["t"] == "ref" else record.get("names")
    label = "".join((record.get("from") or "").split())
    keys = [(*kind, line, json.dumps(about), label), (*kind, line, json.dumps(about)), (*kind, line)]
    return keys + ([(*kind, json.dumps(about))] if record["t"] == "ref" else [])


def _shape(old: dict, new: dict, lines: list[str]) -> str:
    """How two records at the same place differ: a name for the group, never the values themselves. `lines`: the source
    of the file, which says which of two lines holds the `var()` and whether a fallback is cut."""
    parts = []
    for field in sorted({*old, *new}):
        if old.get(field) == new.get(field):
            continue
        a, b = old.get(field), new.get(field)
        if field == "fallback" and isinstance(a, str) and isinstance(b, str) and b.startswith(a) and a.count("(") > a.count(")"):
            parts.append("fallback:old-cut-at-the-first-parenthesis")
        elif field == "site" and old["t"] == "ref":
            word = (old["name"] if old["kind"] == "custom-property" else "") and "var(" + old["name"]
            holds = [word in "".join(lines[int(r["site"].rsplit(":", 1)[1]) - 1].split()) if word else None
                     for r in (old, new)]
            parts.append(f"site:old-line-{'has' if holds[0] else 'lacks'}-the-use+new-line-{'has' if holds[1] else 'lacks'}-it")
        elif "".join(json.dumps(a, ensure_ascii=False).split()) == "".join(json.dumps(b, ensure_ascii=False).split()):
            parts.append(f"{field}:whitespace")
        elif json.dumps(a, ensure_ascii=False).lower() == json.dumps(b, ensure_ascii=False).lower():
            parts.append(f"{field}:case")
        else:
            parts.append(field)
    return "+".join(parts) or "same"


def _group(groups: dict, signature: str, file: str, old: str | None, new: str | None) -> None:
    group = groups.setdefault(signature, {"count": 0, "files": set(), "examples": []})
    group["count"] += 1
    group["files"].add(file)
    if len(group["examples"]) < 4:
        group["examples"].append({"file": file, "old": old and old[:400], "new": new and new[:400]})


def _var_uses(project: Path, files: list, old_records: list, new_records: list, number: int) -> dict:
    """The uses of custom properties each side found against the tokenizer's (`var_tokens.mjs`): per side the uses it
    lacks (`missing`), the ones the tokens do not hold at that line (`wrong`), those whose line is right and whose fallback
    is not the tokens' (`fallback_off`), and the files it gets exactly right, fallbacks included."""
    import collections
    import tempfile
    work = Path(tempfile.mkdtemp(prefix=f"vt{number}-"))
    (work / "in.json").write_text(json.dumps({"engines": "/engines", "root": str(project), "files": files}), encoding="utf-8")
    subprocess.run(["node", "/bench/var_tokens.mjs", str(work / "in.json"), str(work / "out.json")], check=True,
                   capture_output=True, text=True, timeout=1700)
    truth = json.loads((work / "out.json").read_text(encoding="utf-8"))
    sides = {"old": collections.defaultdict(collections.Counter), "new": collections.defaultdict(collections.Counter)}
    for side, records in (("old", old_records), ("new", new_records)):
        for record in records:
            if record["t"] == "ref" and record["kind"] == "custom-property":
                sides[side][record["file"]][f"{record['name']}@{_line(record)}|{record.get('fallback') or ''}"] += 1
    out = {"truth": 0, "files": len(files), **{f"{side}_{what}": 0 for side in sides
                                                for what in ("found", "missing", "wrong", "fallback_off", "exact")}}
    for rel in files:
        expected = collections.Counter(truth[rel])
        out["truth"] += sum(expected.values())
        for side in sides:
            found = sides[side][rel]
            places = collections.Counter(k.split("|", 1)[0] for k in found.elements())
            wanted = collections.Counter(k.split("|", 1)[0] for k in expected.elements())
            out[f"{side}_found"] += sum(found.values())
            out[f"{side}_missing"] += sum((wanted - places).values())
            out[f"{side}_wrong"] += sum((places - wanted).values())
            out[f"{side}_fallback_off"] += sum((found - expected).values()) - sum((places - wanted).values())
            out[f"{side}_exact"] += expected == found
    return out


def ab_chunk(arguments: tuple) -> dict:
    """The records of `files` (relative to the corpus) by the old reader and by the engine, compared file by file: the
    records of one side at a line where the other has none, and the pairs at the same place that differ, each in a
    group named by what differs (`_shape`)."""
    import collections
    import tempfile
    old_source, files, number = arguments
    sys.path.insert(0, str(PLUGIN / "core"))
    from indexers import css, css_csstree
    old = _load_old(old_source, number)
    project = Path(CORPUS)
    before = old.parse(project, files)
    runner = node_runner(Path("/engines"), project, Path(tempfile.mkdtemp(prefix=f"ab{number}-")))
    after = css.engine_sheets(runner, css_csstree, "css", project, files, words=True)
    sides = {"old": collections.defaultdict(collections.Counter), "new": collections.defaultdict(collections.Counter)}
    totals = {"old": collections.Counter(), "new": collections.Counter()}
    for side, found in (("old", before), ("new", after)):
        for record in found["records"]:
            sides[side][record["file"]][_key(record)] += 1
            totals[side][record["t"]] += 1
    uses = _var_uses(project, files, before["records"], after["records"], number)
    groups = {}
    for rel in files:
        only_old = [json.loads(k) for k in (sides["old"][rel] - sides["new"][rel]).elements()]
        only_new = [json.loads(k) for k in (sides["new"][rel] - sides["old"][rel]).elements()]
        # A record of one side pairs with one of the other by the keys of `_levels`, the most exact first (a minified
        # sheet has thousands of records on one line); the rest has no pair.
        lines = (project / rel).read_text(encoding="utf-8").split(chr(10))  # universal newlines, LF only: the snapshot's
        index_of = [collections.defaultdict(list) for _ in range(4)]
        for index, record in enumerate(only_new):
            for level, key in enumerate(_levels(record)):
                index_of[level][key].append(index)
        taken = set()
        holes_at = {(r["kind"], r["line"]) for r in only_new if r["t"] == "hole"}
        for record in only_old:
            kind = f"{record['t']} {record.get('kind') or ''}".strip()
            options = []
            for level, key in enumerate(_levels(record)):
                options = [i for i in index_of[level].get(key, ()) if i not in taken]
                if options:
                    break
            if options:
                taken.add(options[0])
                other = only_new[options[0]]
                _group(groups, f"changed {kind}: {_shape(record, other, lines)}", rel, _key(record), _key(other))
            else:
                extra = (f" {record['cls']}" if record["t"] == "hole" else
                         f" {record['name']}" if record["t"] == "ref" and record["kind"] == "font-face" else "")
                if record["t"] == "ref" and record["kind"] in ("keyframes", "font-face") and \
                        (record["kind"], _line(record)) in holes_at:
                    extra += " [a new hole at its line]"
                _group(groups, f"only old {kind}{extra}", rel, _key(record), None)
        for index, record in enumerate(only_new):
            if index not in taken:
                _group(groups, f"only new {record['t']} {record.get('kind') or ''}".strip() +
                       (f" {record['cls']}" if record["t"] == "hole" else ""), rel, None, _key(record))
    for group in groups.values():
        group["files"] = sorted(group["files"])[:6] + [len(group["files"])]
    return {"groups": groups, "totals": totals, "uses": uses, "missing_old": before["missing"], "missing_new": after["missing"],
            "seconds_new": after["indexer"]["seconds"] if after["indexer"] else None}


@app.function(cpu=4, memory=16384, timeout=3600, block_network=True)
def ab(old_source: str) -> dict:
    """The A/B of the graph's records on the corpus (every `.css` file of the packages), old reader against the
    engine, in chunks of about 3 MB over 4 processes."""
    import concurrent.futures
    import os
    files, sizes = [], {}
    for folder, _, names in os.walk(CORPUS):
        for name in names:
            path = Path(folder, name)
            if name.lower().endswith(".css") and path.is_file():
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if len(text) <= 8_000_000:
                    rel = path.relative_to(CORPUS).as_posix()
                    files.append(rel)
                    sizes[rel] = len(text)
    files.sort()
    chunks, current, weight = [], [], 0
    for rel in files:
        current.append(rel)
        weight += sizes[rel]
        if weight >= 3_000_000:
            chunks.append(current)
            current, weight = [], 0
    if current:
        chunks.append(current)
    out = {"files": len(files), "bytes": sum(sizes.values()), "chunks": len(chunks), "groups": {}, "missing_old": {},
           "missing_new": {}, "totals": {"old": {}, "new": {}}, "seconds_new": 0, "uses": {}}
    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        for found in pool.map(ab_chunk, [(old_source, chunk, i) for i, chunk in enumerate(chunks)]):
            out["missing_old"].update(found["missing_old"])
            out["missing_new"].update(found["missing_new"])
            out["seconds_new"] += found["seconds_new"] or 0
            for name, count in found["uses"].items():
                out["uses"][name] = out["uses"].get(name, 0) + count
            for side in ("old", "new"):
                for kind, count in found["totals"][side].items():
                    out["totals"][side][kind] = out["totals"][side].get(kind, 0) + count
            for signature, group in found["groups"].items():
                merged = out["groups"].setdefault(signature, {"count": 0, "files": 0, "examples": [], "sample_files": []})
                merged["count"] += group["count"]
                merged["files"] += group["files"][-1]
                merged["sample_files"] = (merged["sample_files"] + group["files"][:-1])[:6]
                merged["examples"] = (merged["examples"] + group["examples"])[:6]
    out["groups"] = dict(sorted(out["groups"].items(), key=lambda item: -item[1]["count"]))
    return out


@app.local_entrypoint()
def ab_run(out: str = ""):
    import tempfile
    old = subprocess.run(["git", "show", f"{OLD_SHA}:daodan/core/indexers/css.py"], cwd=REPO, capture_output=True,
                         text=True, encoding="utf-8", check=True).stdout
    result = ab.remote(old)
    target = Path(out or tempfile.gettempdir()) / "ab-groups.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1, ensure_ascii=False) + chr(10), encoding="utf-8")
    print("uses of custom properties against the tokenizer:", result["uses"])
    print(f"files {result['files']}, {result['bytes']} bytes, {result['chunks']} chunks, new engine {result['seconds_new']:.0f} s; "
          f"totals {result['totals']}; missing old {len(result['missing_old'])} new {len(result['missing_new'])}; "
          f"{len(result['groups'])} groups; written {target}")
    for signature, group in list(result["groups"].items())[:40]:
        print(f"{group['count']:>8} {group['files']:>5} files  {signature}")


# ------------------------------------------------------------------------------------------------------ probes

@app.function(cpu=2, memory=8192, timeout=1800, block_network=True)
def probe(script: str, files: dict | None = None) -> str:
    """A node script (`/engines` and `/corpus/node_modules` are there, the network is closed) and what it prints."""
    import os
    os.makedirs("/probe", exist_ok=True)
    for name, data in (files or {}).items():
        Path("/probe", name).write_bytes(data)
    Path("/probe/_script.mjs").write_text(script, encoding="utf-8")
    run = subprocess.run(["node", "--max-old-space-size=6144", "/probe/_script.mjs"], cwd="/probe", capture_output=True,
                         text=True, timeout=1700)
    return run.stdout + (f"\n--- STDERR ---\n{run.stderr}" if run.stderr else "") + f"\n--- exit {run.returncode}"


@app.local_entrypoint()
def probe_run(script: str, out: str = ""):
    """usage: ::probe_run --script path/to/script.mjs [--out file]"""
    text = probe.remote(Path(script).read_text(encoding="utf-8"))
    if out:
        Path(out).write_text(text, encoding="utf-8")
    print(text[-12000:])


# -------------------------------------------------------------------------------- the values of the other dialects

def _decls(tree: list):
    """(property, value) of every declaration of an engine's tree, nested properties with their prefix."""
    stack = [(tree, "")]
    while stack:
        nodes, prefix = stack.pop()
        for n in nodes:
            if not isinstance(n, dict):
                continue
            if n.get("t") == "decl":
                if n.get("value"):
                    yield prefix + n["prop"], n["value"]
                stack.append(([k for k in n.get("kids") or () if isinstance(k, dict)], prefix + n["prop"] + "-"))
            elif n.get("kids"):
                stack.append((n["kids"], ""))


def _facts_of(record: dict) -> tuple:
    return (record["t"], record.get("kind"), record.get("name") or json.dumps(record.get("names")))


@app.function(cpu=4, memory=16384, timeout=3600, block_network=True)
def measure() -> dict:
    """The values the Sass, Less and Stylus trees hand to `css.declaration` (the Sass, Less and Stylus files of the
    corpus's packages, through their engines), read two ways: by the code of `declaration` as it is (regular expressions
    on the text), and by `parse(value, {context: 'value'})` plus the lexer (`value_facts.cjs`). Per dialect and per
    kind of fact: the values both read the same, the ones the fork reads more, the ones it loses (with a hole, or
    without) and the ones the parser keeps as Raw."""
    import collections
    import os
    import tempfile
    from indexers import css, css_less, css_sass, css_stylus
    project = Path(CORPUS)
    files = collections.defaultdict(list)
    for folder, _, names in os.walk(CORPUS):
        for name in names:
            suffix = Path(name).suffix.lower()
            if suffix in (".scss", ".sass", ".less", ".styl", ".stylus"):
                files[{"stylus": "styl"}.get(suffix[1:], suffix[1:])].append(Path(folder, name).relative_to(CORPUS).as_posix())
    runner = node_runner(Path("/engines"), project, Path(tempfile.mkdtemp(prefix="measure-")))
    engines = {"scss": (css_sass, "scss"), "sass": (css_sass, "sass"), "less": (css_less, None), "styl": (css_stylus, None)}
    values = collections.defaultdict(collections.Counter)  # dialect -> {(property, value): occurrences}
    unread = collections.Counter()
    for kind, (engine, syntax) in engines.items():
        dialect = {"scss": "sass", "sass": "sass"}.get(kind, kind)
        names = sorted(files[kind])
        for start in range(0, len(names), 150):
            chunk = names[start:start + 150]
            items = [{"key": rel, "path": rel, **({"syntax": syntax} if syntax else {})} for rel in chunk]
            for key, sheet in engine.index(runner, items)["sheets"].items():
                if "error" in sheet:
                    unread[dialect] += 1
                    continue
                for pair in _decls(sheet["tree"]):
                    values[dialect][pair] += 1
    pairs = sorted({pair for counter in values.values() for pair in counter})
    work = Path(tempfile.mkdtemp(prefix="facts-"))
    (work / "in.json").write_text(json.dumps({"engines": "/engines", "script": str(PLUGIN / "core/indexers/css_csstree.js"),
                                              "pairs": pairs}), encoding="utf-8")
    subprocess.run(["node", "/bench/value_facts.cjs", str(work / "in.json"), str(work / "out.json")], check=True,
                   capture_output=True, text=True, timeout=3000)
    answers = dict(zip(pairs, json.loads((work / "out.json").read_text(encoding="utf-8"))))
    marks = {"$": "a Sass variable", "#{": "Sass interpolation", "@{": "Less interpolation", "@": "a Less variable or call",
             "{": "braces (Stylus interpolation)", "`": "Less JavaScript"}
    out = {"files": {kind: len(names) for kind, names in files.items()}, "not_read": dict(unread), "dialects": {}}
    for dialect, counter in values.items():
        cells = collections.defaultdict(lambda: {"unique": 0, "occurrences": 0, "examples": []})
        by_kind = collections.defaultdict(collections.Counter)
        for (prop, value), count in counter.items():
            answer = answers[(prop, value)]
            old = {_facts_of(r) for r in css.declaration("x", 1, "x", prop, value)}
            if answer["status"] == "threw":  # the declaration of a custom property stands, what its value says is a hole
                new = {_facts_of(r) for r in css.declaration("x.css", 1, "x", prop, value, facts={})}
                holes = {"threw"}
            else:
                made = css.declaration("x.css", 1, "x", prop, value, facts=answer["facts"])
                new = {_facts_of(r) for r in made if r["t"] != "hole"}
                holes = {r["cls"] for r in made if r["t"] == "hole"}
                if answer["status"] == "raw":
                    holes.add("raw")
            lost, gained = old - new, new - old
            if not lost and not gained:
                cell = "same" + (" (with a hole)" if holes else "")
            elif lost and holes:
                cell = "fork loses some, a hole says so"
            elif lost:
                cell = "fork loses some, silently"
            else:
                cell = "fork reads more"
            if answer["status"] != "ok":
                cell += f"; the parser keeps Raw" if answer["status"] == "raw" else "; the parser threw"
            entry = cells[cell]
            entry["unique"] += 1
            entry["occurrences"] += count
            if len(entry["examples"]) < 4 and (lost or gained or holes):
                entry["examples"].append({"property": prop, "value": value[:160], "old": sorted(map(str, old))[:4],
                                          "new": sorted(map(str, new))[:4], "holes": sorted(holes)})
            for fact in lost:
                by_kind[fact[1]]["lost"] += count
            for fact in gained:
                by_kind[fact[1]]["gained"] += count
            for fact in old & new:
                by_kind[fact[1]]["same"] += count
            for mark, what in marks.items():
                if mark in value:
                    by_kind["values with " + what][answer["status"]] += count
        out["dialects"][dialect] = {"values": sum(counter.values()), "unique": len(counter),
                                    "cells": dict(sorted(cells.items(), key=lambda item: -item[1]["occurrences"])),
                                    "by_kind": {k: dict(v) for k, v in by_kind.items()}}
    return out


@app.local_entrypoint()
def measure_run(out: str = ""):
    result = measure.remote()
    target = Path(out or RESULTS) / "values-other-dialects.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1, ensure_ascii=False) + chr(10), encoding="utf-8")
    print("files", result["files"], "not read", result["not_read"])
    for dialect, data in result["dialects"].items():
        print(f"== {dialect}: {data['values']} declarations, {data['unique']} distinct")
        for cell, value in data["cells"].items():
            print(f"   {value['occurrences']:>8} ({value['unique']:>6} distinct)  {cell}")
        print("   by kind:", data["by_kind"])


# ------------------------------------------------------------------------------------------------- the CSS in scripts

CSSINJS_CASE = {"repo": "https://github.com/styled-components/styled-components-website.git",
                "commit": "e70dc5c3f513b4a72ce20d0a1a76fe9891c4a071"}  # styled-components 7, as lang_css.py's sc-website


@app.function(cpu=4, memory=16384, timeout=3000)
def cssinjs() -> dict:
    """The graph of a styled-components project twice, the CSS of its scripts (`cssinjs-text` records) read by the engine
    and by the hand reader (`css.graph` without `reader`), and what differs: nodes, arcs and holes."""
    import collections
    import os
    import tempfile
    from indexers import css
    work = Path(tempfile.mkdtemp(prefix="cssinjs-"))
    target = work / "src"
    target.mkdir()
    for command in (["git", "init", "-q"], ["git", "remote", "add", "origin", CSSINJS_CASE["repo"]],
                    ["git", "fetch", "-q", "--depth", "1", "origin", CSSINJS_CASE["commit"]],
                    ["git", "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(command, cwd=target, check=True, capture_output=True, timeout=600)
    locked = (target / "package-lock.json").is_file()
    subprocess.run(["npm", "ci" if locked else "install", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
                    *([] if locked else ["--no-package-lock"])], cwd=target, capture_output=True, timeout=1500)
    files = css.walk(target)
    runner = node_runner(Path("/engines"), target, work / "runs")
    counted = collections.Counter()
    graph_of = css.graph

    def hand_reader(*args, **kwargs):
        return graph_of(*args, **{**kwargs, "reader": None})

    def counting(*args, **kwargs):
        counted["cssinjs-text"] += sum(r["t"] == "cssinjs-text" for r in args[1])
        return graph_of(*args, **kwargs)
    from indexers import css_csstree
    index_of, calls = css_csstree.index, []

    def timed(run, items):
        import time
        begun = time.time()
        found = index_of(run, items)
        calls.append((len(items), round(time.time() - begun, 2)))
        return found
    css.graph = counting
    css_csstree.index = timed
    engine = css.run(target, runner, files)
    css_csstree.index = index_of
    css.graph = hand_reader
    hand = css.run(target, runner, files)
    css.graph = graph_of

    def keyed(graph: dict) -> dict:
        return {"nodes": {n["id"] for n in graph["nodes"]},
                "edges": {(e["site"], e["symbol"], e["to"], e["end"]) for e in graph["edges"]},
                "holes": {(h["site"], h["kind"], h["class"], h["name"]) for h in graph["holes"]}}
    a, b = keyed(hand), keyed(engine)
    out = {"files": len(files), "cssinjs_texts": counted["cssinjs-text"],
           "engine_runs": {"all": len(calls), "plain_sheets_and_markup": calls[0] if calls else None,
                           "items_and_seconds_of_the_others": calls[1:]},
           "hand": {k: len(v) for k, v in a.items()}, "engine": {k: len(v) for k, v in b.items()}, "differences": {}}
    for kind in a:
        out["differences"][kind] = {"only_hand": sorted(map(str, a[kind] - b[kind]))[:60],
                                    "only_engine": sorted(map(str, b[kind] - a[kind]))[:60],
                                    "count_only_hand": len(a[kind] - b[kind]), "count_only_engine": len(b[kind] - a[kind])}
    scripts = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
    out["differences_outside_script_files"] = {
        kind: [str(x) for x in (a[kind] ^ b[kind]) if not str(x).split(":", 1)[0].strip("('").endswith(scripts)][:20]
        for kind in a}
    for side, found in (("only_hand", a["holes"] - b["holes"]), ("only_engine", b["holes"] - a["holes"])):
        out["differences"]["holes"]["by_class_" + side] = dict(collections.Counter(f"{h[1]} {h[2]}" for h in found))
    return out


@app.local_entrypoint()
def cssinjs_run(out: str = ""):
    result = cssinjs.remote()
    target = Path(out or RESULTS) / "cssinjs-ab.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1, ensure_ascii=False) + chr(10), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "differences"}))
    for kind, data in result["differences"].items():
        print(kind, "only hand", data["count_only_hand"], "only engine", data["count_only_engine"])
