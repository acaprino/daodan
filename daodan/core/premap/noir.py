"""The routes Noir finds in the container. The pre-map binds them and their gaps to its snapshot."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


NAME, VERSION, RANK = "noir", "1.5.0", "scanner"
# The release asset's digest from api.github.com/repos/owasp-noir/noir/releases/tags/v1.5.0.
DOWNLOAD = (f"https://github.com/owasp-noir/noir/releases/download/v{VERSION}/noir-v{VERSION}-linux-x86_64",
            "4e176c92ee16f60fafd3be7ea6f605d82d3f27c39704a3f875cbed5bd050dc70", "noir")


def commands(context):
    from container import WORKDIR
    if context.inventory.files:
        return [{"tool": NAME, "argv": [NAME, "scan", WORKDIR, "-f", "json", "--no-log"],
                 "cwd": ".", "env": {}, "network": "none"}]


def rows(report: dict, root: str, *, gaps: list[dict] | None = None) -> list[dict]:
    """The endpoints OWASP Noir reports (`noir scan -f json`, run in Daodan's container over `root`) as candidates,
    with no rule: the protocol is the shape and decides the kind (`entries.QUERIES["noir"]`; another protocol is a shape to
    classify) unless the endpoint's own `kind` is one Daodan knows (`entries.QUERIES["noir_kinds"]`: a server action), which
    is then the shape and the kind, method and path as Noir writes them, and the handler when Noir names it. The site is the handler's,
    else the first code path's, relative to `root`; an endpoint with neither is none. The name is read only from the handler's place, so
    a row with a name is at the place of its handler and one with none at the registration's (the first code path): that presence is the
    datum with which the binder may bind by place. The symbol is the function
    Noir names in that file, else the file's code outside any function: Noir does not name a method's class."""
    import entries
    import flows
    out = []
    for endpoint in report.get("endpoints") or ():
        handler = endpoint.get("handler") or {}
        paths = (endpoint.get("details") or {}).get("code_paths") or [{}]
        where = handler if handler.get("path") else paths[0]
        if not where.get("path"):
            continue
        path = PurePosixPath(where["path"])
        if not path.is_relative_to(root) or ".." in path.parts:
            if gaps is None:
                raise ValueError(f"Noir cites a path outside {root}: {path}")
            gaps.append({"kind": "outside_snapshot", "path": str(path), "detail": "Noir cites a file outside the scanned root"})
            continue
        file = path.relative_to(root).as_posix()
        known = endpoint.get("kind") in entries.QUERIES["noir_kinds"]  # a kind of Noir's that Daodan knows is the shape
        shape = endpoint["kind"] if known else endpoint["protocol"]
        name = handler.get("name") if where is handler else None
        kind = entries.QUERIES["noir_kinds"][shape] if known else entries.QUERIES["noir"].get(shape)
        out.append({"reader": entries.NOIR, "shape": shape,
                    "site": f"{file}:{where['line']}" if where.get("line") else file,
                    "symbol": f"{file}::{name or flows.MODULE}", "method": endpoint["method"], "path": endpoint["url"],
                    "handler": name, **({"kind": kind} if kind else {}),
                    # Noir's own tag, an object with a `name` (a plain string is read too): only a specification declares it
                    **({"spec_only": True} if "spec-only" in {t.get("name") if isinstance(t, dict) else t
                                                              for t in endpoint.get("tags") or ()} else {}),
                    **({"schema": flows.path_schema(endpoint["url"])} if kind == "rotta" else {})})  # the name or None: the links' binder says the gap
    return out


def read(context, commands, results):
    [result] = results
    if result["returncode"] != 0:
        raise ValueError(f"Noir exited with {result['returncode']}: {result['stderr'].strip()[-400:]}")
    report = json.loads(result["stdout"])
    if not isinstance(report.get("endpoints"), list):
        raise ValueError("the Noir report has no endpoints array")
    candidates, gaps = [], []
    if report.get("errors"):
        gaps.append({"kind": "model_partial", "detail": f"Noir reported {len(report['errors'])} scan errors"})
    for item in rows(report, result["root"], gaps=gaps):
        file = item["symbol"].split("::", 1)[0]
        header = context.inventory.headers.get(file)
        if header is None:
            gaps.append({"kind": "outside_snapshot", "path": file, "detail": "Noir cites a file outside the snapshot"})
            continue
        # Reads once per file (also shared with the other pre-map readers), verifies the snapshot hash; its lines as `parse`
        # counts them, which runs after `scan`.
        lines = len(context.inventory.text(file).split("\n"))
        _, _, number = item["site"].rpartition(":")
        if number.isdecimal() and not 1 <= int(number) <= lines:
            gaps.append({"kind": "model_partial", "path": file, "detail": f"Noir cites an absent line: {number}"})
            continue
        candidates.append(item)
    return {"facts": {"noir_entries": candidates}, "gaps": gaps}


def unavailable(error):
    return {"source": f"{NAME}@{VERSION}", "kind": "noir_unavailable", "detail": str(error),
            "remedy": "refresh the pre-map in Daodan's container"}


def from_record(report):
    source = f"{NAME}@{VERSION}"
    if not any(s["source"] == source for s in report["sources"]):
        return [], [unavailable("this pre-map has no Noir run")]
    # a row of an older pre-map has no `handler` (None: the binder says the gap) and no `schema`: computed here, as `rows` does
    import flows
    return [{"handler": None, **({"schema": flows.path_schema(row["path"])} if row.get("kind") == "rotta" else {}), **row}
            for row in report.get("noir_entries", [])], [g for g in report["gaps"] if g["source"] == source]


def evidence(manifest: Path) -> tuple[list, list]:
    """Read the persisted candidates without running an analyzer. Legacy and stale reports explain their gap."""
    from premap.flow_entries import read_record
    try:
        return from_record(read_record(Path(manifest)))
    except (OSError, KeyError, TypeError, ValueError) as error:
        return [], [unavailable(error)]


def recorded(manifest: Path) -> list[dict]:
    return evidence(manifest)[0]
