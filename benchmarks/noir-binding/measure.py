"""What runs inside the Modal container for one application (`modal_binding.py` ships this file to `/daodan/measure/`): the checkout is at `/work`
(`container.WORKDIR`), fetched at its pinned commit while the image was built, and nothing of it runs here. Three things happen, all of them reading:

1. Daodan's own snapshot of `/work` (`snapshot.read_project`), the one the pre-map reads.
2. The pinned Noir, with the arguments `premap/noir.py` gives (`noir.commands`).
3. For each endpoint of Noir's report: what `noir.read` makes of it (a candidate row, or the gap that drops it), then `binder.bind` over the candidate
   rows, and for each row the facts a cause is found from: the snapshot's declarations that cover its line, those with the handler's name in the file and
   elsewhere, and the next declaration after the line. The facts are written as they are; `causes.py` decides, outside the container.

Returns the answer as one dict; nothing is written under `/work` (the listing before and after is compared).
"""
import collections
import hashlib
import json
import os
import pathlib
import re
import resource
import subprocess
import sys
import time
import types

ROOT = "/work"
SEGMENT = re.compile(r"[A-Za-z_$][\w$]*")  # an identifier inside a handler name: the name has no grammar to read, it is an identifier written by Noir
SHOWN = 8
BELOW = 3  # lines
OWNERS = ("class", "interface", "struct", "enum", "trait", "impl", "record", "object", "module", "namespace")  # the declarations that hold methods
FILES = ("binder.py", "premap/noir.py", "languages/semantic.py", "snapshot.py", "flows.py", "edge_view.py", "entries.py", "semantic_store.py")


def listing(root: str) -> dict[str, int]:
    out = {}
    for directory, _names, files in os.walk(root):
        for f in files:
            path = os.path.join(directory, f)
            try:
                out[os.path.relpath(path, root).replace("\\", "/")] = os.path.getsize(path)
            except OSError:
                pass
    return out


def relative(path: str | None) -> str | None:
    return path[len(ROOT) + 1:] if path and path.startswith(ROOT + "/") else path


def last(name: str | None) -> str | None:
    found = SEGMENT.findall(name or "")
    return found[-1] if found else None


def brief(d: dict) -> dict:
    return {"name": d["name"], "qn": d.get("qualified_name"), "kind": d["kind"], "line": d["line"], "end": d["end"]}


def header_view(header: dict | None) -> dict | None:
    """The scalar fields of a file's inventory row (its language, whether it was read and why not): no text, no hash."""
    if header is None:
        return None
    return {k: v for k, v in header.items() if isinstance(v, (str, int, bool)) and k not in ("raw_hash", "path", "sha256") and len(str(v)) < 160}


def run(name: str) -> dict:
    os.chdir("/")
    sys.path[:0] = ["/daodan/core"]
    import binder
    import flows
    import premap
    import semantic_store
    import snapshot
    from premap import noir
    from snapshot_store import open_snapshot

    before = listing(ROOT)
    out = {"name": name, "files": len(before), "python": sys.version.split()[0],
           "daodan": {f: hashlib.sha256(pathlib.Path("/daodan/core", f).read_bytes()).hexdigest()[:16] for f in FILES}}
    out["noir_pin"] = noir.DOWNLOAD[1]
    manifest = pathlib.Path("/tmp/noir-binding/manifest.sqlite")
    manifest.parent.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    snapshot.read_project(pathlib.Path(ROOT), manifest)
    out["snapshot_seconds"] = round(time.monotonic() - started, 1)

    [command] = noir.commands(types.SimpleNamespace(inventory=types.SimpleNamespace(files=True)))
    out["noir_command"] = command["argv"]
    started = time.monotonic()
    env = {"PATH": os.environ["PATH"], "HOME": "/tmp/noir-home", "LANG": "C.UTF-8"}
    os.makedirs(env["HOME"], exist_ok=True)
    result = subprocess.run(command["argv"], cwd=os.path.join(ROOT, command["cwd"]), env=env, capture_output=True, text=True, timeout=3000, stdin=subprocess.DEVNULL)
    out["noir"] = {"returncode": result.returncode, "seconds": round(time.monotonic() - started, 1), "stderr_tail": result.stderr.strip()[-300:],
                   "peak_memory_mb": round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)}
    if result.returncode != 0:
        return out
    report = json.loads(result.stdout)
    endpoints = report.get("endpoints") or []
    out["noir"].update({"endpoints": len(endpoints), "errors": len(report.get("errors") or ()), "bytes": len(result.stdout),
                        "protocols": dict(collections.Counter(e.get("protocol") for e in endpoints)),
                        "endpoint_keys": sorted({k for e in endpoints for k in e})})

    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        context = premap.Context(manifest, store)
        facts = flows.Facts(store, db)
        resolver = semantic_store._Resolver(db)
        headers = context.inventory.headers
        by_file = collections.defaultdict(list)
        by_last = collections.defaultdict(list)  # a function's name, and the last part of its qualified name -> the declarations
        for d in facts.declarations.values():
            by_file[d["file"]].append(d)
        for file, declarations in facts.functions.items():
            for d in declarations:
                for key in {d["name"], (d.get("qualified_name") or d["name"]).rpartition(".")[2]}:
                    by_last[key].append(d)
        out["snapshot"] = {"files": len(headers), "declarations": len(facts.declarations),
                           "declaration_kinds": dict(collections.Counter(d["kind"] for d in facts.declarations.values()).most_common(20)),
                           "functions": sum(len(v) for v in facts.functions.values()),
                           "functions_by_suffix": dict(collections.Counter(pathlib.PurePosixPath(f).suffix for f, v in facts.functions.items() for _ in v).most_common(12)),
                           "files_by_suffix": dict(collections.Counter(pathlib.PurePosixPath(f).suffix for f in headers).most_common(15)),
                           "header_keys": sorted({k for h in list(headers.values())[:400] for k in h})}

        rows, candidates = [], []
        for i, endpoint in enumerate(endpoints):
            handler = endpoint.get("handler") or {}
            paths = (endpoint.get("details") or {}).get("code_paths") or []
            single = noir.read(context, [command], [{"returncode": 0, "stdout": json.dumps({"endpoints": [endpoint]}), "stderr": "", "root": ROOT}])
            kept = single["facts"]["noir_entries"]
            gaps = single["gaps"]
            row = {"i": i, "protocol": endpoint.get("protocol"), "kind": endpoint.get("kind"), "method": endpoint.get("method"), "url": endpoint.get("url"),
                   "handler": {"name": handler.get("name"), "path": relative(handler.get("path")), "line": handler.get("line")} if handler else None,
                   "code_path": {"path": relative(paths[0].get("path")), "line": paths[0].get("line")} if paths else None,
                   "tags": [t.get("name") if isinstance(t, dict) else t for t in (endpoint.get("tags") or [])][:4]}
            if kept:
                [entry] = kept
                row.update({"shape": entry["shape"], "site": entry["site"], "row_handler": entry["handler"], "kind_of_row": entry.get("kind")})
                candidates.append((i, entry))
            else:
                row["dropped"] = (gaps[0]["kind"] + ": " + gaps[0]["detail"][:100]) if gaps else "no path: noir.rows skips an endpoint with neither handler path nor code path"
            rows.append(row)

        http = [(i, entry) for i, entry in candidates if entry["shape"] == "http"]
        bound = binder.bind([entry for _, entry in http], facts, resolver)
        assert len(bound) == len(http)
        for (i, entry), result_row in zip(http, bound):
            row = rows[i]
            file, separator, line = entry["site"].rpartition(":")
            at = int(line) if line.isdecimal() else 0
            if not separator:  # a site with no line is the file alone (Noir's static files): the binder reads it as the file "" and a line, so it finds no function
                file = entry["site"]
            wanted = entry["handler"]
            tail = last(wanted)
            functions = facts.functions.get(file, ())
            covering = sorted((d for d in functions if d["line"] <= at <= (d["end"] or d["line"])), key=lambda d: (d["end"] or d["line"]) - d["line"])
            named = [d for d in functions if tail and (d["name"] == tail or (d.get("qualified_name") or "").rpartition(".")[2] == tail)]
            elsewhere = [d for d in by_last.get(tail, ()) if d["file"] != file] if tail else []
            after = sorted((d for d in functions if d["line"] > at), key=lambda d: d["line"])[:2]
            exact = [d for d in covering if wanted and wanted in (d["name"], d.get("qualified_name"))]
            row.update({
                "file": file, "line": at, "ok": not result_row.get("gap"), "gap": result_row.get("gap"),
                "file_header": header_view(headers.get(file)), "functions_in_file": len(functions), "declarations_in_file": len(by_file.get(file, ())),
                "covering": [brief(d) for d in covering[:SHOWN]],
                "classes": [brief(d) for d in by_file.get(file, ()) if d["kind"] in OWNERS and d["line"] <= at <= (d["end"] or d["line"])][:4],
                "named_in_file": [brief(d) for d in named[:SHOWN]], "named_in_file_count": len(named),
                "named_elsewhere_count": len(elsewhere), "named_elsewhere": [{**brief(d), "file": d["file"]} for d in elsewhere[:4]],
                "after": [brief(d) for d in after], "exact_matches": len(exact)})
            # where Noir says the route is declared (`details.code_paths`), which is not the handler's own line when the handler is named in another place:
            # the functions of that file that cover that line, and those that start 1 to BELOW lines under it (a decorator or an attribute line sits just above
            # the function it belongs to)
            code = row.get("code_path") or {}
            if code.get("path") and isinstance(code.get("line"), int):
                in_code = facts.functions.get(code["path"], ())
                row["code_site"] = {"covering": [brief(d) for d in sorted((d for d in in_code if d["line"] <= code["line"] <= (d["end"] or d["line"])),
                                                                          key=lambda d: (d["end"] or d["line"]) - d["line"])[:3]],
                                    "below": [{**brief(d), "distance": d["line"] - code["line"]} for d in sorted(
                                        (d for d in in_code if 0 < d["line"] - code["line"] <= BELOW), key=lambda d: d["line"])[:4]]}
        out["rows"] = rows
        out["http_rows"] = len(http)
    after_listing = listing(ROOT)
    out["left_in_the_project"] = sorted(set(after_listing) - set(before))[:20]
    out["changed_in_the_project"] = sorted(f for f in set(after_listing) & set(before) if after_listing[f] != before[f])[:20]
    return out
