"""Which language is a `.h` header: three routes measured on Modal against the right answer, then the costs.

Nothing of the corpus runs and nothing of it is kept here: a Modal function with the network open downloads each
project's archive at its pinned commit (`header_corpus.PROJECTS`), reads the `.h` members of the tar in memory,
keeps the selected headers on the volume `daodan-header-language`, and records the sha256 of the archive and of every
header. A second function, with the network blocked, parses each selected header with the C, C++ and Objective-C
grammars through Daodan's own loader and returns the features of the parses (counts and lines, never text). The
routes (`header_routes`) are decisions over those features; `header_report.py` scores them.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/header-language/modal_headers.py [--step ...]

    --step warm      put the pinned tree-sitter grammars on the volume (network on)
    --step prepare   download, select and store the headers of --projects (default: all)
    --step measure   features, the detector of the moment (see `Probe.r0`), symbols and the byte caps, per header -> --out (results/headers.json.gz)
    --step collect   the features `measure` left on the volume, if the client gave up before the end
    --step growth    the bad texts, one subprocess each with a hard timeout -> results/growth[-KINDS].json (--kinds a,b / --targets r0fix,cpp: only those)
    --step r0check   the detector of the moment and its three candidates (`fix`, `fixq`, `fixqc`) on every selected header -> results/r0check.json.gz
    --step capcost   the cost of every route on the headers longer than each byte cap, cut as the product would -> results/capcost.json.gz
    --step product   the product's own `detect_language` (route R3dx since 25 November) on every selected header, at each bound of --caps -> results/product.json.gz
    --step excerpt   the text of the headers named in --keys (a file of `project/path` lines), printed, for annotation
    --step all       warm, prepare, measure, growth (capcost apart)
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
HL = "/hl"  # where the functions see this folder
CORE = "/daodan/map/core"  # Daodan's `daodan/core`, the folder of its `languages` package
VOL = "/vol"
sys.path.insert(0, str(HERE) if LOCAL else HL)
import header_corpus as corpus  # noqa: E402
import header_routes as routes  # noqa: E402

CAPS = (4096, 8192, 16384, 32768)
CAP_ROUTES = ("R1dg", "R1eg", "R1ego", "R2", "R2o", "R3")
USED = ("daodan/core/languages", "daodan/core/embedding_worker.py", "daodan/core/resolve_edges.py")  # what the run imports
FILES = ("header_corpus.py", "header_routes.py", "header_patterns.py", "header_probe.py", "bad_worker.py")

image = (modal.Image.debian_slim(python_version="3.13")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
         .env({"DAODAN_SHARED_DIR": f"{VOL}/shared", "PYTHONUTF8": "1"}))
if LOCAL:
    repo = HERE.parents[1]
    image = (image.add_local_dir(repo / "daodan" / "core", CORE, ignore=["**/__pycache__/**"])
             .add_local_dir(repo / "daodan" / "data", "/daodan/map/data"))
    for name in FILES:
        image = image.add_local_file(HERE / name, f"{HL}/{name}")
app = modal.App("daodan-header-language", image=image)
volume = modal.Volume.from_name("daodan-header-language", create_if_missing=True)


def _reload() -> None:
    """The volume's latest commit. A container that ran a grammar before holds libraries open on it and cannot reload:
    its mount is then the state it started with, which is the one the earlier steps committed."""
    try:
        volume.reload()
    except RuntimeError:
        pass


def _project(name: str) -> corpus.Project:
    return next(p for p in corpus.PROJECTS if p.name == name)


def _download(url: str, target: str) -> tuple[str, int]:
    """The archive into `target`, its sha256 and size. Retried: the hosts answer 5xx now and then."""
    for attempt in range(4):
        try:
            digest, size = hashlib.sha256(), 0
            request = urllib.request.Request(url, headers={"User-Agent": "header-language-benchmark"})
            with urllib.request.urlopen(request, timeout=120) as response, open(target, "wb") as out:
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            return digest.hexdigest(), size
        except OSError:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


@app.function(volumes={VOL: volume}, timeout=1800)
def warm() -> dict:
    """Daodan's loader places the pinned pack release in `/vol/shared` (verified by sha256) and the pack extracts the
    grammars the benchmark reads; `measure` then runs with the network blocked."""
    sys.path.insert(0, HL)
    import header_probe
    probe = header_probe.Probe(CORE)
    volume.commit()
    return {grammar: probe.parsers[grammar][1] is not None for grammar in routes.GRAMMARS}


@app.function(volumes={VOL: volume}, timeout=3600, cpu=2, memory=8192)
def prepare(name: str) -> dict:
    project = _project(name)
    archive = f"/tmp/{name}.tar.gz"
    sha256, size = _download(project.url, archive)
    blobs: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as tar:  # members read in order, in memory: nothing is extracted
        for member in tar:
            if not member.isfile():  # a symlink is not a header of the project
                continue
            path = corpus.strip_root(member.name)
            if project.accepts(path):
                blobs[path] = tar.extractfile(member).read()
    os.unlink(archive)
    hashes = {path: hashlib.sha256(data).hexdigest() for path, data in blobs.items()}
    chosen = corpus.select(project, hashes)
    os.makedirs(f"{VOL}/selected", exist_ok=True)
    with tarfile.open(f"{VOL}/selected/{name}.tar.gz", "w:gz") as out:
        for path in chosen:
            info = tarfile.TarInfo(path)
            info.size = len(blobs[path])
            out.addfile(info, io.BytesIO(blobs[path]))
    meta = {"project": name, "pin": project.pin, "url": project.url, "license": project.license,
            "archive_sha256": sha256, "archive_bytes": size, "accepted": len(blobs), "unique": len(set(hashes.values())),
            "selected": len(chosen), "selected_bytes": sum(len(blobs[p]) for p in chosen),
            "fingerprint": corpus.fingerprint({p: hashes[p] for p in chosen}),
            "overridden": sum(1 for p in chosen if project.label_of(p) != project.label),
            "dirs": dict(collections.Counter("/".join(p.split("/")[:2]) for p in chosen).most_common(40))}
    Path(f"{VOL}/selected/{name}.json").write_text(json.dumps(meta), encoding="utf-8")
    volume.commit()
    return meta


def _selected(name: str):
    with tarfile.open(f"{VOL}/selected/{name}.tar.gz", "r:gz") as tar:
        for member in tar:
            yield member.name, tar.extractfile(member).read()


def _round(value):
    return round(value, 4) if isinstance(value, float) else value


def _compact(features: dict) -> dict:
    return {key: ({k: _round(v) for k, v in part.items()} if isinstance(part, dict) else part)
            for key, part in features.items()}


@app.function(volumes={VOL: volume}, timeout=3 * 3600, cpu=2, memory=8192, block_network=True)
def measure(name: str, with_symbols: bool = True) -> list[dict]:
    sys.path.insert(0, HL)
    import header_probe
    _reload()
    project = _project(name)
    probe = header_probe.Probe(CORE)
    for grammar in routes.GRAMMARS:  # the first parse of a grammar pays for its set-up
        probe._part(grammar, b"int a;\n")
    probe.r0("int a;\n")
    records = []
    for path, data in _selected(name):
        text = data.decode("utf-8", errors="replace")
        record = {"p": name, "path": path, "sha": hashlib.sha256(data).hexdigest()[:16], "size": len(data),
                  "decl": project.label_of(path)}
        try:
            record["f"] = _compact(probe.features(data))
            record["r0"], record["r0ms"] = probe.r0(text)
            record["r0ms"] = _round(record["r0ms"])
            if with_symbols:
                record["sym"] = {g: probe.symbols(text, g) for g in ("c", "cpp")}
            record["caps"] = _caps(probe, text)
        except Exception as error:  # noqa: BLE001 - one header's failure is its record, not the project's
            record["error"] = f"{type(error).__name__}: {error}"
        records.append(record)
    os.makedirs(f"{VOL}/features", exist_ok=True)  # kept on the volume too: `collect` reads it if the client gave up
    Path(f"{VOL}/features/{name}.json").write_text(json.dumps(records), encoding="utf-8")
    volume.commit()
    return records


@app.function(volumes={VOL: volume}, timeout=600)
def collect(name: str) -> list[dict]:
    _reload()
    return json.loads(Path(f"{VOL}/features/{name}.json").read_text(encoding="utf-8"))


def _caps(probe, text: str) -> dict:
    """For each byte cap the text exceeds: the answers of the main routes on its first lines (`cut`) and on the same
    cut back before an open `/*` (`safe`)."""
    out = {}
    for cap in CAPS:
        if len(text.encode()) <= cap:
            continue
        cut = text[:text.rfind("\n", 0, cap) + 1]
        answers = {}
        for mode, part in (("cut", cut), ("safe", routes.safe_prefix(text, cap))):
            f = probe.features(part.encode())
            answers[mode] = {"R0": probe.r0(part)[0], **{r: routes.decide(r, f) for r in CAP_ROUTES}}
        out[str(cap)] = answers
    return out


@app.function(volumes={VOL: volume}, timeout=3 * 3600, cpu=2, memory=8192, block_network=True)
def capcost(name: str) -> list[dict]:
    """What each route costs when the product cuts a header at a byte cap: for every cap the header exceeds, the cost of
    the grammars on the safe prefix (cut at a line, before a `/*` left open) and of today's rule on the plain cut; for
    every header, the cost of the check itself (`scan_ms`: `safe_prefix` over the first `cap` bytes)."""
    sys.path.insert(0, HL)
    import header_probe
    _reload()
    probe = header_probe.Probe(CORE)
    for grammar in routes.GRAMMARS:
        probe._part(grammar, b"int a;\n")
    probe.r0("int a;\n")
    rows = []
    for path, data in _selected(name):
        text = data.decode("utf-8", errors="replace")
        row = {"p": name, "path": path, "size": len(data), "caps": {}}
        for cap in CAPS:
            t0 = time.perf_counter_ns()
            safe = routes.safe_prefix(text, cap)
            entry = {"scan_ms": _round((time.perf_counter_ns() - t0) / 1e6)}
            if len(data) > cap:
                f = probe.features(safe.encode())
                entry["safe"] = {g: _round(f[g]["ms"] + f[g]["q_ms"]) for g in routes.GRAMMARS}
                entry["r0_cut"] = _round(probe.r0(text[:text.rfind("\n", 0, cap) + 1])[1])
            row["caps"][str(cap)] = entry
        rows.append(row)
    return rows


@app.function(volumes={VOL: volume}, timeout=3600, cpu=2, memory=8192, block_network=True)
def r0check(name: str) -> list[dict]:
    """The detector of the moment (R0; the rule before until 25 November) and the candidates (`header_patterns.VARIANTS`) on every selected header: the answer and the ms of each,
    the ms in the order r0, fix, fixq, fixqc."""
    sys.path.insert(0, HL)
    import header_patterns
    import header_probe
    _reload()
    probe = header_probe.Probe(CORE)
    names = sorted(header_patterns.VARIANTS, key=("fix", "fixq", "fixqc").index)
    for variant in names:
        probe.r0_variant("int a;\n", variant)
    probe.r0("int a;\n")
    rows = []
    for path, data in _selected(name):
        text = data.decode("utf-8", errors="replace")
        today, today_ms = probe.r0(text)
        row = {"p": name, "path": path, "size": len(data), "r0": today, "ms": [_round(today_ms)]}
        for variant in names:
            row[variant], ms = probe.r0_variant(text, variant)
            row["ms"].append(_round(ms))
        rows.append(row)
    return rows


@app.function(volumes={VOL: volume}, timeout=3600, cpu=2, memory=8192, block_network=True)
def product(name: str, caps: list[int]) -> list[dict]:
    """The product's own `detect_language` on every selected header, once for each bound in `caps` (`header.MAX_CHARS`; 0 is
    no bound): its answer ("objc" for None) and ms."""
    sys.path.insert(0, CORE)
    _reload()
    from languages import detect_language
    from languages.detect.rules import header
    bound = header.MAX_CHARS
    detect_language(Path("x.h"), "int a;\nnamespace a { }\n")  # the first parse of a grammar pays for its set-up
    rows = []
    for path, data in _selected(name):
        text = data.decode("utf-8", errors="replace")
        row = {"p": name, "path": path, "size": len(data), "ans": {}, "ms": {}}
        for cap in caps:
            header.MAX_CHARS = cap or 1 << 40
            t0 = time.perf_counter_ns()
            language = detect_language(Path("x.h"), text)
            row["ms"][str(cap)] = _round((time.perf_counter_ns() - t0) / 1e6)
            row["ans"][str(cap)] = language or "objc"
        rows.append(row)
    header.MAX_CHARS = bound
    return rows


@app.function(volumes={VOL: volume}, timeout=4 * 3600, cpu=4, block_network=True)
def growth(groups: list[list], seconds: int = 60) -> list[dict]:
    """Each group is a list of (target, kind, size, mode) in ascending size: run in a process of its own with a hard
    timeout, and the rest of the group is skipped once one of them times out (a bigger text cannot be faster)."""
    _reload()

    def run(group):
        rows = []
        for target, kind, size, mode in group:
            command = [sys.executable, "-I", f"{HL}/bad_worker.py", CORE, HL, target, kind, str(size), mode]
            try:
                done = subprocess.run(command, capture_output=True, text=True, timeout=seconds)
                row = json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() \
                    else {"target": target, "kind": kind, "size": size, "mode": mode, "failed": done.stderr[-300:]}
            except subprocess.TimeoutExpired:
                row = {"target": target, "kind": kind, "size": size, "mode": mode, "timeout": seconds}
            rows.append(row)
            if "timeout" in row:
                break
        return rows

    with ThreadPoolExecutor(max_workers=4) as pool:
        return [row for rows in pool.map(run, groups) for row in rows]


def growth_groups() -> list[list]:
    sizes = (2048, 4096, 8192, 16384, 32768)
    groups = []
    for kind in routes.BAD_KINDS:
        kind_sizes = sizes + ((51200,) if kind == "blank_lines" else ())
        for target in ("r0", "r0fix", "r0fixq", "r0fixqc", "c", "cpp", "objc", "scan", "product"):
            groups.append([(target, kind, n, "raw") for n in kind_sizes])
    for kind in routes.BAD_KINDS:  # the product's detection against the parse it does next, at the sizes a bound is chosen on
        for mode in ("bound:16384", "bound:65536", "bound:131072", "bound:524288", "bound:0"):
            for target in ("product", "parse"):
                groups.append([(target, kind, n, mode) for n in (51200, 204800)])
    for kind in ("open_comment", "open_comment_repeat", "open_comment_lines", "class_repeat", "nested_brace", "open_string",
                 "escaped_dq", "escaped_sq"):  # the caps, on the texts they must tame
        for target in ("r0", "cpp"):
            for mode in ("cut:8192", "safe:8192"):
                groups.append([(target, kind, n, mode) for n in (8192, 16384, 32768, 65536)])
    return groups


@app.function(volumes={VOL: volume}, timeout=1800, block_network=True)
def excerpt(keys: list[str], lines: int = 40) -> str:
    """For the annotation by hand: each named header without its comments, its `#include` lines counted, cut to
    `lines` lines, behind a line of the C++-only and Objective-C nodes found. Printed, never stored."""
    sys.path.insert(0, HL)
    import header_probe
    _reload()
    probe = header_probe.Probe(CORE)  # puts Daodan's folder on sys.path
    from languages import _treesitter
    wanted: dict[str, list[str]] = {}
    for key in keys:
        project, path = key.split("/", 1)
        wanted.setdefault(project, []).append(path)
    out = []
    for project, paths in wanted.items():
        files = dict(_selected(project))
        for path in paths:
            data = files[path]
            f = probe.features(data)
            root = probe.parsers["cpp"][0].parse(data).root_node
            text = _treesitter.mask_comments(root, data, data.decode("utf-8", errors="replace"))
            body, directives, continued = [], 0, False
            for ln in text.splitlines():
                if not ln.strip():
                    continue
                if continued or ln.lstrip().startswith("#"):  # a directive, and the lines its backslashes continue
                    directives += not continued
                    continued = ln.rstrip().endswith("\\")
                else:
                    body.append(ln.rstrip()[:110])
            found = {k: v[:2] for k, v in f["cpp"]["kinds"].items()}
            objc = {k: v[0] for k, v in f["objc"]["kinds"].items()}
            out.append(f"=== {project}/{path}  {len(data)}B  directives={directives}  cpp_kinds={found}  objc_kinds={objc}  "
                       f"err(c,cpp,objc)=({f['c']['err']},{f['cpp']['err']},{f['objc']['err']})\n"
                       + "\n".join(body[:lines]) + (f"\n... ({len(body) - lines} more lines)" if len(body) > lines else ""))
    return "\n".join(out)


def _code() -> dict:
    """The Daodan code this run reads: the checkout's commit and the files of `USED` that differ from it."""
    repo = HERE.parents[1]
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
    return {"commit": git("rev-parse", "HEAD"), "differs": git("status", "--porcelain", "--", *USED).splitlines()}


def _save(path: str, obj) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".gz":
        with gzip.open(target, "wt", encoding="utf-8") as handle:
            json.dump(obj, handle, separators=(",", ":"))
    else:
        target.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size} bytes)")


@app.local_entrypoint()
def main(step: str = "all", projects: str = "", out: str = "", keys: str = "", symbols: bool = True, lines: int = 40, kinds: str = "", targets: str = "",
         caps: str = "0,16384,65536,131072,524288"):
    names = [p.name for p in corpus.PROJECTS if not projects or p.name in projects.split(",")]
    steps = ("warm", "prepare", "measure", "growth") if step == "all" else (step,)
    metas = []
    if "warm" in steps:
        print("warm", warm.remote())
    if "prepare" in steps:
        metas = list(prepare.map(names))
        for meta in metas:
            print(f"{meta['project']:14} accepted={meta['accepted']:5} unique={meta['unique']:5} selected={meta['selected']:5} "
                  f"bytes={meta['selected_bytes']:9} overridden={meta['overridden']}")
            print("   ", dict(list(meta["dirs"].items())[:14]))
        print("selected", sum(m["selected"] for m in metas))
        base = Path(out).parent if out else HERE / "results"
        _save(str(base / "corpus.json"), {"code": _code(), "projects": metas})
    if "measure" in steps:
        rows = [row for part in measure.starmap([(n, symbols) for n in names]) for row in part]
        errors = [r for r in rows if "error" in r]
        print(f"measured {len(rows)} headers, {len(errors)} failed", errors[:3])
        _save(out or str(HERE / "results" / "headers.json.gz"), {"code": _code(), "records": rows})
    if "collect" in steps:
        rows = [row for part in collect.map(names) for row in part]
        _save(out or str(HERE / "results" / "headers.json.gz"), {"code": _code(), "records": rows})
    if "r0check" in steps:
        rows = [row for part in r0check.map(names) for row in part]
        _save(out or str(HERE / "results" / "r0check.json.gz"), {"code": _code(), "rows": rows})
    if "product" in steps:
        bounds = [int(n) for n in caps.split(",")]
        rows = [row for part in product.starmap([(n, bounds) for n in names]) for row in part]
        _save(out or str(HERE / "results" / "product.json.gz"), {"code": _code(), "caps": bounds, "rows": rows})
    if "capcost" in steps:
        rows = [row for part in capcost.map(names) for row in part]
        _save(out or str(HERE / "results" / "capcost.json.gz"), {"code": _code(), "rows": rows})
    if "growth" in steps:
        groups = [g for g in growth_groups() if (not kinds or g[0][1] in kinds.split(",")) and (not targets or g[0][0] in targets.split(","))]
        rows = growth.remote(groups)
        print(f"growth: {len(rows)} runs, {sum('timeout' in r for r in rows)} timed out")
        _save(out or str(HERE / "results" / f"growth{'-' + (kinds or targets).replace(',', '+') if kinds or targets else ''}.json"),
              {"code": _code(), "rows": rows})
    if "excerpt" in steps:
        wanted = [line.strip() for line in Path(keys).read_text(encoding="utf-8").splitlines() if line.strip()]
        print(excerpt.remote(wanted, lines))
