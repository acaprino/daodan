"""Connection points on tududi, on Modal: the checkout, the tools that read routes and HTTP calls, no model.

    modal deploy benchmarks/connection-points/modal_points.py
    python -I benchmarks/connection-points/modal_points.py survey|tools [--out FILE]

`survey` lists what a reader needs to write the expected links by hand; `tools` runs the existing tools
(see README) inside the container and returns their raw output. Project code runs only here.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import modal

REPO = "https://github.com/chrisvel/tududi.git"
COMMIT = "71da9d7b34dfd1600657e9c5ddf40420206fd263"
NODE = "v22.12.0"  # the first 22 that loads ES modules with require(), as tududi needs
TAG = "connection-points"
SRC = Path("/work/src")

GO = "1.22.12"
JSLUICE = "0ddfab153e060a9eeaded4d8669233f7c071e7e4"  # no tags upstream: the last commit, 2024-01-10
HERE = Path(__file__).resolve().parent
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git", "ca-certificates", "curl", "xz-utils", "build-essential", "python3-dev")
    .run_commands(f"curl -fsSL https://nodejs.org/dist/{NODE}/node-{NODE}-linux-x64.tar.xz | tar -xJ -C /opt",
                  f"ln -s /opt/node-{NODE}-linux-x64/bin/* /usr/local/bin/",
                  f"curl -fsSL https://go.dev/dl/go{GO}.linux-amd64.tar.gz | tar -xz -C /opt",
                  f"GOBIN=/usr/local/bin GOPATH=/tmp/gopath /opt/go/bin/go install "
                  f"github.com/BishopFox/jsluice/cmd/jsluice@{JSLUICE}",
                  "npm i --prefix /tools --no-audit --no-fund express-list-endpoints@7.1.1")
    .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "ast-grep-cli==0.50.0")
    .add_local_file(HERE / "client_http.py", "/cp/client_http.py")
    .add_local_file(HERE / "express_routes.js", "/cp/express_routes.js")
    .add_local_file(HERE / "rules.json", "/cp/rules.json")
    .add_local_dir(HERE / "fixtures", "/cp/fixtures")
)
app = modal.App("daodan-connection-points", image=image)
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]


def sh(command: str, cwd: Path = SRC, timeout: int = 900) -> str:
    run = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return (run.stdout + (f"\n[stderr]\n{run.stderr[-4000:]}" if run.returncode else "")).strip()


def checkout() -> None:
    import shutil
    shutil.rmtree(SRC, ignore_errors=True)  # a warm container may hold an earlier checkout
    SRC.mkdir(parents=True)
    for command in ("git init -q", f"git fetch -q --depth 1 {REPO} {COMMIT}", "git checkout -q FETCH_HEAD"):
        subprocess.run(command, shell=True, cwd=SRC, check=True)


SURVEY = {
    "tree": "git ls-files | awk -F/ 'NF>2{print $1\"/\"$2} NF<=2{print $1}' | sort | uniq -c | sort -rn | head -60",
    "packages": "git ls-files | grep -E '(^|/)package.json$' | xargs -I{} sh -c 'echo == {}; cat {}'",
    "app": "cat backend/app.js",
    "mounts": r"grep -rnE 'app\.use\(|registerRoutes|\.use\(.*/api' backend --include=*.js | grep -v /tests/",
    "routers": r"grep -rnEc 'router\.(get|post|put|patch|delete|all)\(' backend --include=*.js | grep -v ':0$'"
               " | grep -v /tests/",
    "swagger": "git ls-files | grep -iE 'swagger|openapi' | head -20",
    "client_calls": r"grep -rnE 'fetch\(|axios|apiClient|getApiPath|apiFetch|API_BASE|/api/' frontend"
                    " --include=*.ts --include=*.tsx | grep -v __tests__ | cut -c1-220",
    "route_lines": r"grep -rnE -A2 '(router|app)\.(get|post|put|patch|delete|all)\(' backend --include=*.js"
                   " | grep -v /tests/ | cut -c1-200",
    "router_use": r"grep -rnE '(router|app)\.use\(' backend/modules backend/services --include=*.js | cut -c1-200",
    "fetch_context": r"grep -rn -A6 'fetch(' frontend --include=*.ts --include=*.tsx | grep -v __tests__ | cut -c1-200",
    "other_clients": r"grep -rnE 'useSWR|XMLHttpRequest|EventSource|sendBeacon|window\.open\(|location\.href ='"
                     " frontend --include=*.ts --include=*.tsx | grep -v __tests__ | cut -c1-200",
}


@app.function(cpu=1, memory=2048, timeout=900, volumes={"/results": volume})
def survey() -> dict:
    print("code", code_hash(), flush=True)
    checkout()
    out = {"code": code_hash(), "commit": COMMIT}
    for name, command in SURVEY.items():
        out[name] = sh(command)
    path = Path("/results") / TAG / "survey.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    volume.commit()
    return out


def files_hash() -> str:
    """The code a run executes: this file, the adapter, the recorder and the rules."""
    names = ("client_http.py", "express_routes.js", "rules.json")
    base = HERE if modal.is_local() else Path("/cp")
    return hashlib.sha256(b"".join(p.read_bytes() for p in [Path(__file__), *(base / n for n in names)])).hexdigest()[:12]


TESTS = ("__tests__/", ".test.", ".spec.")


def _recorder(root: Path, app_file: str, out: Path, env: dict, cwd: Path) -> dict:
    import os
    run = subprocess.run(["node", "/cp/express_routes.js", str(root), app_file, str(out), "/tools"],
                         cwd=cwd, capture_output=True, text=True, timeout=600, env={**os.environ, **env})
    data = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {"error": "no output"}
    data["returncode"], data["stderr_tail"] = run.returncode, run.stderr[-3000:]
    return data


def _fixture_check() -> dict:
    """The recorder on its own fixture app, compared with the routes the fixture declares."""
    import shutil
    work = Path("/work/fx")
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree("/cp/fixtures/express", work)
    sh("npm i --no-audit --no-fund express@4.21.2 >/dev/null 2>&1", cwd=work)
    data = _recorder(work, "app.js", work / "out.json", {}, work)
    got = sorted([r["method"], r["path"], r["site"], f"{r['handler'].get('file')}:{r['handler'].get('line')}"]
                 for r in data.get("routes", ()))
    want = sorted(json.loads((work / "expected.json").read_text(encoding="utf-8")))
    return {"pass": got == want, "missing": [w for w in want if w not in got],
            "extra": [g for g in got if g not in want], "error": data.get("error"),
            "list_endpoints": data.get("express_list_endpoints"), "stderr_tail": data.get("stderr_tail", "")[-800:]}


def _client(rules: dict) -> dict:
    import gzip
    sys.path.insert(0, "/cp")
    import client_http
    graph = json.load(gzip.open("/results/inference-audit/scip-inputs/tududi/plugin/graph-typescript.json.gz"))
    edges = {}
    for edge in graph["edges"]:
        if edge["site"].startswith("frontend/"):
            edges.setdefault(edge["site"], []).append((edge["from"], edge["to"]))
    rels = [r for r in sh("git ls-files frontend").splitlines()
            if r.endswith((".ts", ".tsx", ".js", ".jsx")) and not any(t in r for t in TESTS)]
    sources = {r: (SRC / r).read_text(encoding="utf-8", errors="replace") for r in rels}
    out = client_http.extract(sources, rules, {"edges": edges})
    out["files"] = len(rels)
    return out


def _ast_grep() -> dict:
    """ast-grep, a structural search: what one pattern finds of route registrations and of fetch calls."""
    verbs = {"get", "post", "put", "patch", "delete", "all"}
    found = json.loads(sh("ast-grep run --pattern '$R.$M($P, $$$A)' --lang js --json=compact backend") or "[]")
    routes = []
    for item in found:
        single = item["metaVariables"]["single"]
        if "/tests/" in item["file"] or single["M"]["text"] not in verbs or single["R"]["text"] not in ("router", "app"):
            continue
        path = single["P"]["text"]
        routes.append({"site": f"{item['file']}:{item['range']['start']['line'] + 1}",
                       "method": single["M"]["text"].upper(),
                       "path": path[1:-1] if path[:1] in "'\"" else None, "text": path[:60]})
    calls = set()
    for lang in ("ts", "tsx"):
        for item in json.loads(sh(f"ast-grep run --pattern 'fetch($$$A)' --lang {lang} --json=compact frontend") or "[]"):
            if not any(t in item["file"] for t in TESTS):
                calls.add(f"{item['file']}:{item['range']['start']['line'] + 1}")
    return {"version": sh("ast-grep --version"), "routes": routes, "fetch_sites": sorted(calls)}


def _jsluice() -> list:
    out = []
    for rel in sh("git ls-files frontend").splitlines():
        if not rel.endswith((".ts", ".tsx")) or any(t in rel for t in TESTS):
            continue
        for line in sh(f"jsluice urls {rel}").splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            out.append({"file": rel, **{k: item.get(k) for k in ("url", "method", "type", "source")}})
    return out


SWAGGER = ("node -e \"const s=require('./config/swagger.js');console.log(JSON.stringify("
           "Object.entries(s.paths||{}).map(([p,v])=>[p,Object.keys(v)])))\" 2>/dev/null | tail -1")


@app.function(cpu=2, memory=8192, timeout=3600, volumes={"/results": volume})
def tools() -> dict:
    import time
    print("code", files_hash(), flush=True)
    out = {"code": files_hash(), "commit": COMMIT}
    out["fixture"] = _fixture_check()
    print("fixture", out["fixture"]["pass"], flush=True)
    checkout()
    started = time.time()
    out["npm_ci"] = sh("npm ci --no-audit --no-fund --loglevel=error 2>&1 | tail -5", timeout=1800)
    out["npm_ci_seconds"] = round(time.time() - started, 1)
    env = {"NODE_ENV": "test", "DISABLE_SCHEDULER": "true", "DISABLE_TELEGRAM": "true",
           "DATABASE_URL": "postgres://user:password@127.0.0.1:5432/tududi"}  # never connected: only required
    out["express"] = _recorder(SRC, "backend/app.js", Path("/work/routes.json"), env, SRC / "backend")
    print("express routes", len(out["express"].get("routes", ())), out["express"].get("error"), flush=True)
    out["swagger"] = sh(SWAGGER, cwd=SRC / "backend")
    out["ast_grep"] = _ast_grep()
    out["jsluice"] = _jsluice()
    out["client"] = _client(json.loads(Path("/cp/rules.json").read_text(encoding="utf-8")))
    out["seconds"] = round(time.time() - started, 1)
    path = Path("/results") / TAG / "tools.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    volume.commit()
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("survey", "tools"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print("local code", files_hash() if args.command == "tools" else code_hash(), flush=True)
    call = modal.Function.from_name("daodan-connection-points", args.command).spawn()
    print("call", call.object_id, flush=True)
    result = call.get(timeout=3600)
    print("remote code", result.get("code"), flush=True)
    Path(args.out).write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
