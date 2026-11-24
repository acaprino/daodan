"""What runs inside the Modal container for one Gin application of `benchmarks/noir-binding/apps.py` (`modal_real.py` ships this file to
`/daodan/measure/`): the checkout is at `/work`, fetched at its pinned commit while the image was built, with its modules downloaded there by
Daodan's own restore line (`preparation.RESTORES["go"]`, `go mod download` in each folder `preparation.restores` gives) while the network was
open. Here the network is blocked.

`stage="noir"`: nothing of the project runs. `benchmarks/noir-binding/measure.py` and `after.py` as they are (Daodan's snapshot, the pinned Noir,
`noir.read`, `binder.bind` and `flows.bind_declared`), and from the snapshot of `after.py` every Go function with its lines and its node
(`flows.Facts.node`, `named`): the table a Gin route's handler is placed in, outside the container (`real_summary.py`).

`stage="go"`: the project is built and run, only in a copy (`/copy`) of the checkout, with the toolchain's flags Daodan uses for Go
(`GOFLAGS=-mod=readonly`, `GOTOOLCHAIN=local`, `GOPROXY=off`, `CGO_ENABLED=1`):

1. the finder (`finder/main.go`, golang.org/x/tools/go/packages) in each module: the functions that return `*gin.Engine`, the calls of
   `gin.New`/`gin.Default`, the main packages and whether each depends on Gin, the folder of each package;
2. way (c): each main package that depends on Gin is built with `go build -overlay` adding `hooks/route_hook.go` to it (the copy's tree gets
   no file), the first build with an empty build cache; then run for each argument list `modal_real.py` gives (with where it comes from), with
   `GIN_MODE=debug`, until it listens (the harness sees a new socket in LISTEN in `/proc/net/tcp` and kills the process group), it exits, or
   `LIMIT` seconds pass; the hook's lines are the routes;
3. each handler name is looked up with `go tool nm` and `go tool addr2line` on that binary, as written and, for a name ending in `-fm` (the
   wrapper the compiler writes for a method value), without it; and split by `debug/gosym` (`finder -names`);
4. way (a): for each exported function without parameters, outside a main package, that returns `*gin.Engine`, `hooks/engine_probe.go.tmpl`
   becomes a main package added by the overlay in a new folder, built and run in the module's folder: `Routes()` with the pc of each
   `HandlerFunc` and `FileLine(pc)`;
5. the copy is listed (size and sha256 of each file) before and after: what is left in it.
"""
import collections
import hashlib
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT, COPY = "/work", "/copy"
LIMIT = 60  # seconds a run has before it is killed
GO_ENV = {"GOFLAGS": "-mod=readonly", "GOTOOLCHAIN": "local", "GOPROXY": "off", "CGO_ENABLED": "1", "GOWORK": "off", "GOMODCACHE": "/gomod",
          "HOME": "/tmp/home", "PATH": "/usr/local/go/bin:" + os.environ.get("PATH", "")}
FINDER, HOOK, PROBE = "/opt/finder/finder", "/daodan/measure/route_hook.go", "/daodan/measure/engine_probe.go.tmpl"
TAIL = 1500


def listing(root: str) -> dict[str, tuple[int, str]]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            try:
                if os.path.islink(path):
                    out[os.path.relpath(path, root)] = (0, "link:" + os.readlink(path))
                    continue
                out[os.path.relpath(path, root)] = (os.path.getsize(path), hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16])
            except OSError:
                pass
    return out


def listening() -> dict[int, int]:
    """The container's TCP sockets in LISTEN: inode -> port."""
    found = {}
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in open(table).read().splitlines()[1:]:
                fields = line.split()
                if fields[3] == "0A":
                    found[int(fields[9])] = int(fields[1].rsplit(":", 1)[1], 16)
        except OSError:
            pass
    return found


def run(argv: list[str], cwd: str, env: dict, limit: int = LIMIT, stop_on_listen: bool = False, stdin: str | None = None) -> dict:
    """One command in its own process group: time, peak memory (`wait4`), how it ended (exit, a socket in LISTEN, the limit)."""
    before, seen, ended = set(listening()), {}, threading.Event()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err, tempfile.TemporaryFile() as fed:
        fed.write((stdin or "").encode())
        fed.seek(0)
        started = time.monotonic()
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=fed, stdout=out, stderr=err, start_new_session=True)
        how = {"by": "exit"}

        def kill():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        def watch():
            while not ended.is_set():
                elapsed = time.monotonic() - started
                if stop_on_listen:
                    new = {i: p for i, p in listening().items() if i not in before}
                    if new:
                        seen.update(new)
                        how.update({"by": "listen", "at_s": round(elapsed, 3), "ports": sorted(new.values())})
                        kill()
                        return
                if elapsed > limit:
                    how.update({"by": "limit", "at_s": round(elapsed, 3)})
                    kill()
                    return
                time.sleep(0.005)

        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        _, status, usage = os.wait4(process.pid, 0)
        seconds = round(time.monotonic() - started, 2)
        ended.set()
        watcher.join()
        try:
            os.killpg(process.pid, signal.SIGKILL)  # whatever it started
        except ProcessLookupError:
            pass
        out.seek(0), err.seek(0)
        stdout, stderr = out.read().decode("utf-8", "replace"), err.read().decode("utf-8", "replace")
    return {"argv": argv, "cwd": cwd, "returncode": os.waitstatus_to_exitcode(status), "seconds": seconds, "peak_memory_mb": round(usage.ru_maxrss / 1024),
            "ended": how, "stdout": stdout, "stderr": stderr}


def brief(step: dict) -> dict:
    return {**{k: step[k] for k in ("argv", "cwd", "returncode", "seconds", "peak_memory_mb", "ended")},
            "stdout_tail": step["stdout"][-TAIL:], "stderr_tail": step["stderr"][-TAIL:]}


def lines(path: str) -> list[dict]:
    out = []
    if os.path.isfile(path):
        for line in pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                out.append({"kind": "unreadable", "text": line[:200]})
    return out


def symbols(binary: str, names: list[str], env: dict) -> dict:
    """`go tool nm` (name -> address) and `go tool addr2line` (address -> function, file:line), for each name and, for a `-fm` wrapper,
    the name without the suffix; and the parts `debug/gosym` gives each name."""
    nm = subprocess.run(["go", "tool", "nm", binary], capture_output=True, text=True, env=env).stdout
    address = {}
    for line in nm.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            address.setdefault(parts[2].strip(), parts[0])
    wanted = sorted({n for name in names for n in (name, name[:-3] if name.endswith("-fm") else None) if n})
    found = [n for n in wanted if n in address]
    answer = subprocess.run(["go", "tool", "addr2line", binary], input="".join("0x" + address[n] + "\n" for n in found),
                            capture_output=True, text=True, env=env).stdout.splitlines()
    place = {n: {"address": address[n], "function": answer[2 * i] if 2 * i < len(answer) else None,
                 "file_line": answer[2 * i + 1] if 2 * i + 1 < len(answer) else None} for i, n in enumerate(found)}
    split = subprocess.run([FINDER, "-names"], input="".join(n + "\n" for n in sorted(set(names))), capture_output=True, text=True).stdout
    parts = {d["name"]: d for d in map(json.loads, split.splitlines())}
    return {name: {"symbol": place.get(name), "method_symbol": place.get(name[:-3]) if name.endswith("-fm") else None, "gosym": parts.get(name)}
            for name in sorted(set(names))}


def modules(files) -> list[str]:
    return sorted({os.path.dirname(f) or "." for f in files if os.path.basename(f) == "go.mod" and not f.startswith("vendor/") and "/vendor/" not in f})


def go_stage(name: str, variants: list[dict], probes: bool) -> dict:
    shutil.rmtree(COPY, ignore_errors=True)
    shutil.copytree(ROOT, COPY, symlinks=True)
    before = listing(COPY)
    out = {"name": name, "go": subprocess.run(["go", "version"], capture_output=True, text=True, env=GO_ENV).stdout.strip(),
           "modules": {}, "runs": [], "probes": []}
    os.makedirs("/tmp/home", exist_ok=True)
    cold = {**GO_ENV, "GOCACHE": "/tmp/gocache-build"}  # empty: the first build of each module is a cold one
    finder_env = {**GO_ENV, "GOCACHE": "/tmp/gocache-finder"}
    built = {}
    for module in modules(before):
        cwd = os.path.join(COPY, module)
        found = run([FINDER, COPY], cwd, finder_env, limit=900)
        try:
            data = json.loads(found["stdout"])
        except ValueError:
            data = {"error": "no JSON", "stderr_tail": found["stderr"][-TAIL:]}
        out["modules"][module] = {"finder": {**data, "seconds": found["seconds"], "peak_memory_mb": found["peak_memory_mb"], "returncode": found["returncode"]}}
        for index, main in enumerate(m for m in data.get("main_packages", ()) if m["depends_on_gin"]):
            directory = os.path.join(COPY, main["dir"])
            binary, overlay = f"/tmp/bin/{module.replace('/', '_')}-{index}", f"/tmp/overlay-{module.replace('/', '_')}-{index}.json"
            os.makedirs("/tmp/bin", exist_ok=True)
            pathlib.Path(overlay).write_text(json.dumps({"Replace": {os.path.join(directory, "zz_daodan_hook.go"): HOOK}}), encoding="utf-8")
            build = run(["go", "build", "-overlay", overlay, "-o", binary, "./" + os.path.relpath(directory, cwd)], cwd, cold, limit=1500)
            attempts = [brief(build)]
            if build["returncode"] != 0 and os.path.isdir(os.path.join(cwd, "vendor")):  # the project's own vendor folder
                build = run(["go", "build", "-mod=vendor", "-overlay", overlay, "-o", binary, "./" + os.path.relpath(directory, cwd)], cwd, cold, limit=1500)
                attempts.append(brief(build))
            built[main["dir"]] = {"module": module, "binary": binary if build["returncode"] == 0 else None, "builds": attempts,
                                  "mod_flag": None if len(attempts) == 1 else "-mod=vendor"}
    out["built"] = built

    def further_build(target: dict, variant: dict) -> dict:
        """The binary of a variant that is not the main's own build with the hook: with the build tags the project declares for the
        build that runs (`tags`, labelled so), or without the hook (`plain`: Gin's own debug text on the standard output, way b)."""
        tags, plain = variant.get("tags"), variant.get("plain")
        key = target["binary"] + ("-" + tags.replace(",", "-") if tags else "") + ("-plain" if plain else "")
        if key not in built:
            cwd, folder = os.path.join(COPY, target["module"]), os.path.join(COPY, variant["dir"])
            argv = ["go", "build", *(["-tags", tags] if tags else []), *([target["mod_flag"]] if target.get("mod_flag") else [])]
            if not plain:
                pathlib.Path(key + ".overlay.json").write_text(json.dumps({"Replace": {os.path.join(folder, "zz_daodan_hook.go"): HOOK}}), encoding="utf-8")
                argv += ["-overlay", key + ".overlay.json"]
            build = run([*argv, "-o", key, "./" + os.path.relpath(folder, cwd)], cwd, {**GO_ENV, "GOCACHE": "/tmp/gocache-build"}, limit=1500)
            built[key] = {"module": target["module"], "binary": key if build["returncode"] == 0 else None, "builds": [brief(build)],
                          "mod_flag": target.get("mod_flag"), "tags": tags, "plain": bool(plain)}
        return built[key]

    listed = {v["dir"] for v in variants}
    for variant in [*variants, *({"dir": d, "argv": [], "label": "none (a main package that depends on Gin)"} for d in built if d not in listed)]:
        target = built.get(variant["dir"])
        if target and target["binary"] and (variant.get("tags") or variant.get("plain")):
            target = further_build(target, variant)
        if not target or not target["binary"]:
            out["runs"].append({**variant, "skipped": "not built"})
            continue
        result = f"/tmp/routes-{len(out['runs'])}.jsonl"
        env = {**GO_ENV, "GIN_MODE": "debug", "DAODAN_OUT": result, **variant.get("env", {})}
        prepared = []
        for step in variant.get("before", ()):  # a service or a configuration the variant sets up by hand (labelled so)
            done = subprocess.run(step, shell=True, capture_output=True, text=True, timeout=300)
            prepared.append({"returncode": done.returncode, "stderr_tail": done.stderr[-400:]})
        ran = run([target["binary"], *variant["argv"]], os.path.join(COPY, variant["dir"]), env, stop_on_listen=True)
        routes = lines(result)
        names = [r["handler"] for r in routes if r.get("kind") == "route"]
        # Gin's log line of a route (`debug.go`): on the standard output from `gin.DefaultWriter` (1.12), on the standard error in 1.4
        printed = [l for l in [*ran["stdout"].splitlines(), *ran["stderr"].splitlines()] if l.startswith("[GIN-debug] ") and " --> " in l]
        out["runs"].append({**{k: v for k, v in variant.items() if k not in ("before", "after")}, "run": brief(ran), "lines": routes,
                            "debug_route_lines": len(printed), "debug_route_sample": printed[:3], "before_steps": prepared,
                            "symbols": symbols(target["binary"], names, GO_ENV) if names else {}})
        for step in variant.get("after", ()):
            subprocess.run(step, shell=True, capture_output=True, text=True, timeout=300)
    if probes:
        warm = {**GO_ENV, "GOCACHE": "/tmp/gocache-build"}
        template = pathlib.Path(PROBE).read_text(encoding="utf-8")
        for module, info in out["modules"].items():
            builders = [b for b in info["finder"].get("engine_builders", ()) if b["exported"] and not b.get("receiver") and not b["params"]]
            for index, builder in enumerate(builders):
                cwd = os.path.join(COPY, module)
                folder = os.path.join(cwd, f"zz_daodan_probe_{index}")  # a folder that exists only in the overlay
                source = f"/tmp/probe-{module.replace('/', '_')}-{index}.go"
                pathlib.Path(source).write_text(template.replace("DAODAN_PACKAGE", builder["package"]).replace("DAODAN_FUNC", builder["name"]), encoding="utf-8")
                overlay = source + ".json"
                pathlib.Path(overlay).write_text(json.dumps({"Replace": {os.path.join(folder, "main.go"): source}}), encoding="utf-8")
                binary = f"/tmp/bin/probe-{module.replace('/', '_')}-{index}"
                build = run(["go", "build", "-overlay", overlay, "-o", binary, "./" + os.path.relpath(folder, cwd)], cwd, warm, limit=1500)
                entry = {"module": module, "builder": builder, "build": brief(build)}
                if build["returncode"] != 0 and os.path.isdir(os.path.join(cwd, "vendor")):
                    build = run(["go", "build", "-mod=vendor", "-overlay", overlay, "-o", binary, "./" + os.path.relpath(folder, cwd)], cwd, warm, limit=1500)
                    entry["build_vendor"] = brief(build)
                if build["returncode"] == 0:
                    result = f"/tmp/probe-{module.replace('/', '_')}-{index}.jsonl"
                    ran = run([binary], cwd, {**GO_ENV, "GIN_MODE": "debug", "DAODAN_OUT": result}, stop_on_listen=True)
                    got = lines(result)
                    entry.update({"run": brief(ran), "lines": got})
                    names = [r["handler"] for r in got if r.get("kind") in ("route", "routes")]
                    entry["symbols"] = symbols(binary, names, GO_ENV) if names else {}
                out["probes"].append(entry)
    sys.path[:0] = ["/daodan/core"]
    import flows  # the path as Daodan's links read it (`flows.path_schema`: `:id` and `*any` as Daodan sees them), for the comparison with Noir

    for item in [*out["runs"], *out["probes"]]:
        for line in item.get("lines", ()):
            if line.get("path") is not None:
                line["schema"] = flows.path_schema(line["path"])
    after = listing(COPY)
    out["left_in_the_copy"] = sorted(set(after) - set(before))[:60]
    out["left_count"] = len(set(after) - set(before))
    out["changed_in_the_copy"] = sorted(f for f in set(after) & set(before) if after[f] != before[f])[:60]
    out["removed_from_the_copy"] = sorted(set(before) - set(after))[:20]
    out["gomod_bytes"] = sum(os.path.getsize(os.path.join(d, f)) for d, _n, fs in os.walk("/gomod") for f in fs if os.path.isfile(os.path.join(d, f)))
    return out


def noir_stage(name: str) -> dict:
    sys.path.insert(0, "/daodan/measure")
    import after
    import measure

    measured = measure.run(name)
    bound = after.run(name)  # its snapshot stays at /tmp/noir-binding/after/manifest.sqlite
    sys.path[:0] = ["/daodan/core"]
    import edge_view
    import flows
    import semantic_store
    from snapshot_store import open_snapshot

    functions = []
    with open_snapshot(pathlib.Path("/tmp/noir-binding/after/manifest.sqlite")) as store, semantic_store.semantic_reader(store) as db:
        facts = flows.Facts(store, db, edge_view.load_edge_view(store))
        same = collections.Counter(facts.named(d["id"]) for d in facts.declarations.values())
        for file, declared in facts.functions.items():
            if not file.endswith(".go"):
                continue
            for d in declared:
                functions.append({"id": d["id"], "file": file, "name": d["name"], "qn": d.get("qualified_name"), "line": d["line"], "end": d["end"],
                                  "node": facts.node(d["id"]), "named": facts.named(d["id"]), "same_named": same[facts.named(d["id"])]})
    for row in measured.get("rows", ()):
        if row.get("url") is not None:
            row["schema"] = flows.path_schema(row["url"])
    for row in bound.get("facts") or ():
        if row.get("path") is not None:
            row["schema"] = flows.path_schema(row["path"])
    return {"name": name, "measure": measured, "after": {k: bound.get(k) for k in ("snapshot_seconds", "rows", "facts", "links", "links_failed", "failed")},
            "go_functions": functions}
