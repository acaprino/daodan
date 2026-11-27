"""Does the tree-sitter `sql` grammar read SQL and PL/SQL, against the regex readers Daodan has today and sqlglot.

Nothing of the corpus runs and nothing of it is kept here: a Modal function with the network open downloads each
project's archive at its tag (`sql_corpus.PROJECTS`), reads the SQL and PL/SQL members of the tar in memory, keeps the
selected files on the volume `daodan-sql-grammar`, and records the commit the tag resolved to and the sha256 of the
files. The functions that read them have the network blocked. No LLM anywhere.

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m modal run benchmarks/sql-grammar/modal_sql.py [--step ...]

    --step warm       put the pinned tree-sitter grammars on the volume and ask the pack for `plsql` (network on)
    --step prepare    download, select and store the files of --projects (default: all)
    --step fixtures   the hand-annotated fixtures: every reader against `fixtures/gold.json` -> results/fixtures.json
    --step measure    every selected file with every reader -> results/measure.json.gz, results/summary.json
    --step growth     the readers on texts that grow, one subprocess each with a timeout -> results/growth.json
    --step all        the five steps, in this order
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
SG = "/sg"  # where the functions see this folder
CORE = "/daodan/map/core"  # Daodan's `daodan/core`, the folder of its `languages` package
VOL = "/vol"
sys.path.insert(0, str(HERE) if LOCAL else SG)
import sql_corpus as corpus  # noqa: E402
import sql_grammar as g  # noqa: E402

FILES = ("sql_corpus.py", "sql_grammar.py", "sql_readers.py", "growth_worker.py")
GROWTH = {"ddl": (5000, 20000), "package": (500, 2000), "open_comment": (20000, 80000), "dollar_run": (20000, 80000)}
GROWTH_TIMEOUT = 180
NOISE_MS = 50  # under this a run is noise for a ratio

image = (modal.Image.debian_slim(python_version="3.13")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
         .env({"DAODAN_SHARED_DIR": f"{VOL}/shared", "PYTHONUTF8": "1"}))
if LOCAL:
    repo = HERE.parents[1]
    image = (image.add_local_dir(repo / "daodan" / "core", CORE, ignore=["**/__pycache__/**"])
             .add_local_dir(repo / "daodan" / "data", "/daodan/map/data")
             .add_local_dir(HERE / "fixtures", f"{SG}/fixtures"))
    for name in FILES:
        image = image.add_local_file(HERE / name, f"{SG}/{name}")
app = modal.App("daodan-sql-grammar", image=image)
volume = modal.Volume.from_name("daodan-sql-grammar", create_if_missing=True)


def _reload() -> None:
    try:
        volume.reload()
    except RuntimeError:  # a container that ran a grammar holds libraries open: its mount is the state it started with
        pass


def _readers():
    if CORE not in sys.path:
        sys.path.insert(0, CORE)
    import sql_readers
    return sql_readers


def _download(url: str, target: str) -> tuple[str, int]:
    for attempt in range(3):
        try:
            digest, size = hashlib.sha256(), 0
            request = urllib.request.Request(url, headers={"User-Agent": "sql-grammar-benchmark"})
            with urllib.request.urlopen(request, timeout=180) as response, open(target, "wb") as out:
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            return digest.hexdigest(), size
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise
            time.sleep(5 * (attempt + 1))
        except OSError:
            time.sleep(5 * (attempt + 1))
    raise OSError(f"cannot download {url}")


@app.function(volumes={VOL: volume}, timeout=1800)
def warm() -> dict:
    readers = _readers()
    _, plsql = readers.tree_parser()
    volume.commit()
    return {"plsql": plsql}


@app.function(volumes={VOL: volume}, timeout=3600, cpu=2, memory=8192)
def prepare(name: str) -> dict:
    project = next(p for p in corpus.PROJECTS if p.name == name)
    holes = []
    for ref in project.refs:
        archive = f"/tmp/{name}.tar.gz"
        try:
            sha256, size = _download(project.url(ref), archive)
        except (urllib.error.HTTPError, OSError) as error:
            holes.append(f"{ref}: {type(error).__name__} {error}")
            continue
        blobs: dict[str, bytes] = {}
        license_line, license_sha = "", ""
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                path = corpus.strip_root(member.name)
                if project.accepts(path):
                    blobs[path] = tar.extractfile(member).read()
                elif "/" not in path and path.lower().startswith(("licen", "copying")) and not license_sha:
                    data = tar.extractfile(member).read()
                    license_sha = hashlib.sha256(data).hexdigest()[:16]
                    license_line = next((l.strip() for l in data.decode("utf-8", "replace").splitlines() if l.strip()), "")
            commit = tar.pax_headers.get("comment", "")
        os.unlink(archive)
        hashes = {path: hashlib.sha256(data).hexdigest() for path, data in blobs.items()}
        chosen = corpus.select(project, hashes, {path: len(data) for path, data in blobs.items()})
        os.makedirs(f"{VOL}/selected", exist_ok=True)
        with tarfile.open(f"{VOL}/selected/{name}.tar.gz", "w:gz") as out:
            for path in chosen:
                info = tarfile.TarInfo(path)
                info.size = len(blobs[path])
                out.addfile(info, io.BytesIO(blobs[path]))
        meta = {"project": name, "repo": project.repo, "ref": ref, "commit": commit, "license": project.license,
                "license_line": license_line, "license_sha256": license_sha, "archive_sha256": sha256,
                "archive_bytes": size, "accepted": len(blobs), "selected": len(chosen),
                "selected_bytes": sum(len(blobs[p]) for p in chosen), "holes": holes,
                "fingerprint": corpus.fingerprint({p: hashes[p] for p in chosen})}
        Path(f"{VOL}/selected/{name}.json").write_text(json.dumps(meta), encoding="utf-8")
        volume.commit()
        return meta
    return {"project": name, "repo": project.repo, "selected": 0, "holes": holes}


def _selected(name: str):
    with tarfile.open(f"{VOL}/selected/{name}.tar.gz", "r:gz") as tar:
        for member in tar:
            yield member.name, tar.extractfile(member).read()


def _read_all(readers, parser, path: str, data: bytes, dialect: str | None) -> dict:
    """Every reader on one file: counts and times, the comparisons against the regex reader, and the objects."""
    text = data.decode("utf-8", errors="replace")
    language = readers.language_of(path, text)
    record = {"path": path, "size": len(data), "lang": language}
    if language not in ("sql", "plsql"):
        return record
    rx, record["rx_ms"], _ = readers.regex(language, text, path)
    ts, err, record["ts_ms"] = readers.tree(parser, data)
    record["err"] = err
    record.update(n_rx=len(rx), n_ts=len(ts))
    record["cmp_ts"] = g.compare(rx, ts, detail=6)
    if len(data) <= corpus.GLOT_BYTES:
        for tag, read in (("g", None), ("gd", dialect)):
            found, record[f"{tag}_ms"], info = readers.glot(text, read)
            record[f"n_{tag}"] = len(found)
            record[f"cmp_{tag}"] = g.compare(rx, found, detail=6)
            if tag == "g":
                record["g_failure"], record["g_commands"] = info["failure"], info["commands"]
    return record


@app.function(volumes={VOL: volume}, timeout=3 * 3600, cpu=2, memory=8192, block_network=True)
def measure(name: str) -> list[dict]:
    readers = _readers()
    _reload()
    project = next(p for p in corpus.PROJECTS if p.name == name)
    parser, _ = readers.tree_parser()
    records = []
    for path, data in _selected(name):
        try:
            record = _read_all(readers, parser, path, data, project.dialect)
        except Exception as error:  # noqa: BLE001 - one file's failure is its record, not the project's
            record = {"path": path, "size": len(data), "error": f"{type(error).__name__}: {error}"}
        record["p"] = name
        records.append(record)
    return records


@app.function(volumes={VOL: volume}, timeout=900, block_network=True)
def fixtures() -> dict:
    """The hand-annotated files against their gold, each reader in full (the files are small)."""
    _reload()
    readers = _readers()
    parser, plsql = readers.tree_parser()
    gold = json.loads(Path(f"{SG}/fixtures/gold.json").read_text(encoding="utf-8"))
    out = {"plsql_in_pack": plsql, "files": {}}
    for name, entry in gold.items():
        if name == "_":
            continue
        data = Path(f"{SG}/fixtures/{name}").read_bytes()
        text = data.decode("utf-8")
        reference = [g.Obj(kind, n, line, end, inner) for kind, n, line, end, inner in entry["objects"]]
        language = readers.language_of(name, text)
        rx, rx_ms, _ = readers.regex(language, text, name)
        ts, err, ts_ms = readers.tree(parser, data)
        row = {"lang": language, "gold": len(reference), "err": err,
               "ms": {"rx": round(rx_ms, 2), "ts": round(ts_ms, 2)}}
        row["rx"] = {"objects": [list(o[:4]) for o in rx], "cmp": g.compare(reference, rx)}
        row["ts"] = {"objects": [list(o) for o in ts], "cmp": g.compare(reference, ts)}
        for tag, dialect in (("g", None), ("gd", entry["dialect"])):
            found, ms, info = readers.glot(text, dialect)
            row[tag] = {"objects": [list(o[:3]) for o in found], "cmp": g.compare(reference, found), "ms": round(ms, 2), **info}
        out["files"][name] = row
    for reader in ("rx", "ts", "g", "gd"):
        out[reader] = g.merge([row[reader]["cmp"] for row in out["files"].values()])
        out[reader]["by_level"] = {level: {key: sum(row[reader]["cmp"]["by_level"][level][key] for row in out["files"].values())
                                           for key in ("found", "missing")} for level in ("top", "inner")}
    return out


def _grow(reader: str, kind: str, n: int) -> dict:
    command = [sys.executable, "-I", f"{SG}/growth_worker.py", CORE, reader, kind, str(n)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=GROWTH_TIMEOUT)
        return json.loads(done.stdout.strip().splitlines()[-1]) if done.returncode == 0 and done.stdout.strip() \
            else {"failed": f"exit {done.returncode}: {done.stderr.strip()[-300:]}"}
    except subprocess.TimeoutExpired:
        return {"timeout": GROWTH_TIMEOUT}


@app.function(volumes={VOL: volume}, timeout=3 * 3600, cpu=4, memory=16384, block_network=True)
def growth() -> list[dict]:
    """Each reader on a text of N and 4N repeats and on a baseline, one process each, one after another (they share
    cores: the ratio of two runs of one reader is what counts)."""
    _reload()
    rows = []
    for kind, (small, large) in GROWTH.items():
        for reader in ("regex", "tree", "glot"):
            base, one, four = (_grow(reader, kind, n) for n in (0, small, large))
            row = {"kind": kind, "reader": reader, "n": [small, large], "base": base, "small": one, "large": four}
            if "ms" in one and "ms" in four:
                ratio = g.growth_ratio(one["ms"], four["ms"], four["bytes"] / one["bytes"])
                row["ratio"] = round(ratio, 2)
                row["verdict"] = g.judge(ratio, one["ms"] >= NOISE_MS)
                row["memory_mb"] = [round((r["maxrss_kb"] - base["maxrss_kb"]) / 1024, 1) for r in (one, four)] \
                    if "maxrss_kb" in base else None
            rows.append(row)
    return rows


def _write(name: str, value) -> None:
    path = HERE / "results" / name
    path.parent.mkdir(exist_ok=True)
    if name.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as out:
            json.dump(value, out, separators=(",", ":"))
    else:
        path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


@app.local_entrypoint()
def main(step: str = "all", projects: str = ""):
    names = [n for n in projects.split(",") if n] or [p.name for p in corpus.PROJECTS]
    steps = ("warm", "prepare", "fixtures", "measure", "growth") if step == "all" else (step,)
    if "warm" in steps:
        print("warm:", warm.remote())
    if "prepare" in steps:
        metas = list(ThreadPoolExecutor(4).map(prepare.remote, names))
        _write("corpus.json", metas)
        for meta in metas:
            print("prepare:", {k: meta.get(k) for k in ("project", "ref", "commit", "license_line", "selected", "holes")})
    if "fixtures" in steps:
        result = fixtures.remote()
        _write("fixtures.json", result)
        print("fixtures: plsql in the pack:", result["plsql_in_pack"])
        for reader in ("rx", "ts", "g", "gd"):
            print(f"  {reader}: {result[reader]['total']} {result[reader]['by_level']}")
    if "measure" in steps:
        records = [r for rows in ThreadPoolExecutor(4).map(measure.remote, names) for r in rows]
        _write("measure.json.gz", records)
        summary = {"by_project": g.summarise(records, lambda r: r["p"]), "by_language": g.summarise(records, lambda r: r["lang"]),
                   "errors": [r for r in records if "error" in r][:20],
                   "median_error_share": statistics.median([r["err"]["error_bytes"] / r["size"] for r in records
                                                            if "err" in r and r["size"]] or [0])}
        _write("summary.json", summary)
        for name, entry in summary["by_language"].items():
            print(f"measure {name}:", {k: entry[k] for k in ("files", "files_with_error", "error_nodes", "ms", "objects")},
                  "ts vs regex", entry["cmp_ts"]["total"])
    if "growth" in steps:
        rows = growth.remote()
        _write("growth.json", rows)
        for row in rows:
            print("growth:", row["kind"], row["reader"], row.get("ratio"), row.get("verdict"), row.get("memory_mb"),
                  row["small"] if "ms" not in row["small"] else row["small"]["ms"], row["large"].get("ms", row["large"]))
