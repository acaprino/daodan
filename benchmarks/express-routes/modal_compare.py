"""Express's module (`entry_points/express.py`) against the pinned Noir, on Modal: the measure of the README's decision rule (`T1.C.9`).

    modal run benchmarks/express-routes/modal_compare.py                         every application of `cases.CASES`
    modal run benchmarks/express-routes/modal_compare.py --only tududi           some of them

(behind the session's proxy, with `modal[api-proxy-support]`; `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.)

One image per application, as `noir-binding/modal_binding.py` builds it: Python 3.12, the pins of the snapshot's readers, the Noir that
`entry_points/noir.py` pins (sha256 checked), Daodan's `core` and `data`, the grammars checked (`noir-binding/warm.py`), and the checkout at
`/work`. Then, with the network blocked and nothing of the project run: Daodan's snapshot (`snapshot.read_project`), `noir scan` as
`noir.commands` gives it, its answer recorded and bound as the step does (`entry_points.write` with Noir alone), and the module's rows
(`express.rows`) bound by `binder.bind` on new `flows.Facts`; on `tududi` also the links with its `offre` rule alone (`flows.link_facts`).
`summarize.compare` counts; `results/<application>.json` keeps the counts, the rows (no source text) and the times.
"""
import concurrent.futures
import json
import os
import pathlib
import sys
import zlib

import modal

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = modal.is_local()  # in a container this file lies at /root: nothing below that reads the checkout runs there
REPO = HERE.parents[1] if LOCAL else HERE
MEASURE = "/daodan/measure"
NAMES = ("node-express-boilerplate", "anything-llm", "juice-shop", "tududi")
if LOCAL:
    sys.path.insert(0, str(HERE))
    import cases  # noqa: E402
    assert tuple(cases.CASES) == NAMES
    sys.path.append(str(REPO / "benchmarks/noir-binding"))
    import apps  # noqa: E402  (noir-binding's: the pinned Noir)
    NOIR = apps.NOIR
DEPS = ("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
IGNORE = ["**/__pycache__/**", "**/*.pyc"]
CHUNK = 6000  # bytes: a call with the network blocked cannot return more than about 8 KB at once


def _image(name: str) -> modal.Image:
    if not LOCAL:
        return modal.Image.debian_slim()
    repository, commit, _licence = cases.CASES[name]
    return (modal.Image.from_registry("buildpack-deps:noble", add_python="3.12")
            .pip_install(*DEPS)
            .run_commands(f"curl -fsSL -o /usr/local/bin/noir {NOIR[0]} && echo '{NOIR[1]}  /usr/local/bin/noir' | sha256sum -c - "
                          "&& chmod +x /usr/local/bin/noir")
            .env({"DAODAN_SHARED_DIR": "/daodan-shared", "PYTHONDONTWRITEBYTECODE": "1"})
            .add_local_dir(REPO / "daodan/core", "/daodan/core", copy=True, ignore=IGNORE)
            .add_local_dir(REPO / "daodan/data", "/daodan/data", copy=True)
            .add_local_file(REPO / "benchmarks/noir-binding/warm.py", f"{MEASURE}/warm.py", copy=True)
            .run_commands(f"python {MEASURE}/warm.py")
            .run_commands(f"mkdir -p /work && curl -fsSL https://codeload.github.com/{repository}/tar.gz/{commit} | tar xz -C /work --strip-components=1")
            .add_local_file(HERE / "summarize.py", f"{MEASURE}/summarize.py"))


app = modal.App("express-routes")


def _brief(row: dict) -> dict:
    return {k: row[k] for k in ("reader", "shape", "method", "path", "schema", "site", "registered", "span", "handler", "symbol", "function", "gap") if row.get(k) is not None}


def _identify(rows: list[dict], facts) -> None:
    """Each bound row's `function`: the declaration whose own node is the row's symbol (one function, whatever name a route gave it), else
    the symbol (a node several functions share)."""
    own = {}
    for declared in facts.functions.values():
        for function in declared:
            node = facts.own_node(function["id"])
            if node is not None:
                own.setdefault(node, []).append(function["id"])
    for row in rows:
        if not row.get("gap") and row.get("symbol"):
            found = own.get(row["symbol"], ())
            row["function"] = found[0] if len(found) == 1 else row["symbol"]


def _read(name: str, rules: list[dict]) -> dict:
    import resource
    import subprocess
    import time
    import types

    os.chdir("/")
    sys.path[:0] = ["/daodan/core", MEASURE]
    import binder
    import entry_points
    import flows
    import premap
    import semantic_store
    import snapshot
    import summarize
    from entry_points import express, noir
    from snapshot_store import open_snapshot

    root = pathlib.Path("/work")
    manifest = pathlib.Path("/tmp/express-routes/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    snapshot.read_project(root, manifest)
    out = {"name": name, "snapshot_seconds": round(time.monotonic() - started, 1)}
    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    started = time.monotonic()
    r = subprocess.run(command["argv"], cwd=root / command["cwd"], env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    out["noir"] = {"argv": command["argv"], "returncode": r.returncode, "seconds": round(time.monotonic() - started, 1), "stderr_tail": r.stderr[-300:]}
    if r.returncode != 0:
        return out
    answer = {"returncode": 0, "stdout": r.stdout, "stderr": "", "root": str(root)}
    premap.write(manifest, sources=())  # the pre-map with no source of its own: the record of the entry points reads it
    record = entry_points.write(manifest, sources=(noir,), runner=lambda commands: [answer])
    kept = [row for row in record["bound"]["rows"] if row.get("shape") == "http"]
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        # each binding on its own `Facts`, as the step binds: a function written with no name takes the name of its route, and the
        # two readers give the same function different routes (Noir loses prefixes), so the function is compared by its declaration
        facts = flows.Facts(store, db)
        noir_rows = binder.bind([row for row in entry_points.rows(record)[0] if row.get("shape") == "http"], facts, facts.resolver)
        assert [row.get("symbol") for row in noir_rows] == [row.get("symbol") for row in kept]  # the step's own binding
        _identify(noir_rows, facts)
        facts = flows.Facts(store, db)
        started = time.monotonic()
        found = express.rows(facts)
        out["express_seconds"] = round(time.monotonic() - started, 1)
        out["express_peak_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        express_rows = binder.bind(found, facts, facts.resolver)
        _identify(express_rows, facts)
        out["sites"] = {row["function"]: [row["site"], row["span"]] for row in express_rows if not row.get("gap")}
    out["compare"] = summarize.compare(express_rows, noir_rows, flows.path_schema)
    out["express_rows"] = [_brief(row) for row in express_rows]
    out["noir_rows"] = [_brief(row) for row in noir_rows]
    if rules:  # the links with the `offre` rule alone: the routes it offers, by the line each is registered at
        try:
            started = time.monotonic()
            links = flows.link_facts(manifest, rules)
            out["links_seconds"] = round(time.monotonic() - started, 1)
            offered = {e["site"] for e in links["entries"] if e["kind"] == "rotta" and "reader" not in e}
            read = {row.get("registered") or row["site"] for row in express_rows}
            ours = {row["registered"] for row in express_rows if not row.get("gap")}
            out["rule"] = {"offered": len(offered), "read_by_express": len(offered & read), "bound_by_express": len(offered & ours),
                           "only_rule": sorted(offered - read), "only_express": sorted(read - offered)}
        except Exception as error:  # the links of this snapshot did not build: the third comparison is missing, with its cause
            out["rule"] = {"failed": f"{type(error).__name__}: {str(error)[:400]}"}
    return out


def _function(name: str):
    def run(rules: list[dict], wanted: list | None = None):
        import traceback
        try:
            answer = _lines(wanted) if wanted is not None else _read(name, rules)
        except BaseException:  # the cause comes back as data
            answer = {"name": name, "failed": traceback.format_exc()[-3000:]}
        payload = zlib.compress(json.dumps(answer).encode("utf-8"), 9)
        for start in range(0, len(payload), CHUNK):
            yield payload[start:start + CHUNK]
    run.__name__ = run.__qualname__ = "read_" + name.replace("-", "_")
    globals()[run.__name__] = function = app.function(image=_image(name), timeout=3600, block_network=True, memory=12288, cpu=4)(run)
    return function


FUNCTIONS = {name: _function(name) for name in NAMES}


def _collect(name: str, rules: list[dict], wanted: list | None = None) -> dict:
    return json.loads(zlib.decompress(b"".join(FUNCTIONS[name].remote_gen(rules, wanted))))


def _lines(wanted: list) -> dict:
    """The source's lines `[file, first, last]` of each item, from the checkout at `/work`: for a person to read, never kept."""
    out = []
    for file, first, last in wanted:
        lines = pathlib.Path("/work", file).read_text(encoding="utf-8", errors="replace").split("\n")
        out.append([f"{n}: {lines[n - 1].rstrip()[:160]}" for n in range(max(1, first), min(last, len(lines)) + 1)])
    return {"lines": out}


def _sample() -> None:
    """The sample of the README's rule (`summarize.sample`) over `results/`, printed with the lines of the source at the registration and
    at the start of the handler; the lines are the applications' own text and are not written anywhere."""
    import summarize
    results = {name: json.loads((HERE / "results" / f"{name}.json").read_text(encoding="utf-8")) for name in NAMES}
    chosen = summarize.sample({name: answer["compare"] for name, answer in results.items() if "compare" in answer})
    for item in chosen:
        row = next(r for r in results[item["application"]]["express_rows"] if r.get("function", r.get("symbol")) == item["symbol"]
                   and (r.get("method") or None) == item["method"] and (r.get("schema") or r["path"]) == item["path"])
        sites = (row["registered"], row["site"])
        wanted = [[site.rpartition(":")[0], int(site.rpartition(":")[2]) - 1, int(site.rpartition(":")[2]) + 2] for site in sites]
        found = _collect(item["application"], [], wanted)["lines"]
        print(f"\n{item['application']} {item['method'] or 'ANY'} {row['path']} -> {item['symbol']}")
        for site, lines in zip(sites, found):
            print(f"  {site}")
            print("\n".join(f"     {line}" for line in lines))


@app.local_entrypoint()
def main(only: str = "", mode: str = "compare"):
    if mode == "sample":
        return _sample()
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    chosen = [n for n in NAMES if not only or n in only.split(",")]
    offre = [rule for rule in json.loads((REPO / cases.RULES).read_text(encoding="utf-8"))["rules"] if rule["link"] == "offre"]
    with concurrent.futures.ThreadPoolExecutor(len(chosen)) as pool:
        calls = {name: pool.submit(_collect, name, offre if name == "tududi" else []) for name in chosen}
        for name, call in calls.items():
            try:
                answer = call.result()
            except Exception as error:  # a container that failed is a missing answer with its cause, not the end of the others
                answer = {"name": name, "failed": f"{type(error).__name__}: {str(error)[-800:]}"}
            answer["application"] = dict(zip(("repository", "commit", "licence"), cases.CASES[name]))
            (out / f"{name}.json").write_bytes((json.dumps(answer, indent=1, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
            compared = answer.get("compare") or {}
            print("===", name, answer.get("failed") or "", json.dumps({k: v for k, v in compared.items() if not k.startswith("only_")}),
                  json.dumps({k: v for k, v in (answer.get("rule") or {}).items() if not k.startswith("only_")}))
