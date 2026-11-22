"""Entries the browser found (plan task 11.4; spec of the project's interfaces, 7.4): the controls the exploration
pressed (`dynamic/app.py`, `explore.cjs`), kept as candidates of the source `observed`.

A control is an entry when the press did something (a function of the project ran, or the page sent a request) and no
static candidate stands for it: a static candidate of the same accessible name and the same event keeps the control
as it is, and so does a static candidate nobody pressed. A press names no handler: the coverage says which functions
ran, not which one the click called, so the row lists the project functions that ran (`observed_calls`) and says in
`gap` that its handler is not isolated. The file is written beside the manifest by whoever ran the exploration.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import Path
from urllib.parse import urlsplit

FILE = "observed-controls.json"
KIND = "controllo dell'interfaccia"  # `entries.ENTRY_KINDS[0]`: the closed set of the classifier
CALLS = 10  # the project functions a row lists; the file keeps them all


def write(manifest: Path, apps: list[dict]) -> None:
    Path(manifest).with_name(FILE).write_text(json.dumps({"apps": apps}), encoding="utf-8")


def rows(manifest: Path, static: list[dict], files: set[str]) -> list[dict]:
    """The candidates of the file beside `manifest`; none when the exploration did not run."""
    try:
        apps = json.loads(Path(manifest).with_name(FILE).read_text(encoding="utf-8"))["apps"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    return candidates(apps, static, files)


def _project(source: str | None, files: set[str], folder: str) -> str | None:
    """The snapshot's path a script's source names: the longest tail of it that is a file of the snapshot, under the
    app's `folder` first (a dev server names a file from the app's root: `/src/a.ts` for `web/src/a.ts`); never a
    dependency's."""
    if not source or "node_modules" in source:
        return None
    parts = source.strip("/").split("/")
    for start in range(len(parts)):
        tail = "/".join(parts[start:])
        for path in ((f"{folder}/{tail}" if folder else tail), tail):
            if path in files:
                return path
    return None


def _path(url: str) -> str:
    parts = urlsplit(url)
    return parts.path + (f"?{parts.query}" if parts.query else "")


def candidates(apps: list[dict], static: list[dict], files: set[str]) -> list[dict]:
    known = {((row.get("label") or "").strip().lower(), row.get("event")) for row in static if row.get("label")}
    found = []
    for app in apps:
        folder = posixpath.dirname(str(app.get("declared_in") or "").partition("#")[0])
        for page in app.get("pages", []):
            for control in page.get("controls", []):
                if control.get("state") != "pressed":
                    continue
                ran = sorted({(rel, call["line"], call["name"]) for call in control.get("calls", [])
                              if call.get("line") and (rel := _project(call.get("source"), files, folder))})
                requests = list(dict.fromkeys(f"{item['method']} {_path(item['url'])}" for item in control.get("requests", [])))
                if not ran and not requests:
                    continue  # nothing the press did is seen: not an entry
                if ((control["name"] or "").strip().lower(), "click") in known:
                    continue  # the static reader has it
                found.append({
                    "status": "candidate", "reader": "observed", "shape": "control", "kind": KIND,
                    "site": _path(page["url"]), "label": control["name"], "event": "click", "role": control["role"],
                    "occurrence": control.get("occurrence", 0), "declared_in": app.get("declared_in"),
                    "observed_calls": [f"{rel}:{line} {name}" for rel, line, name in ran[:CALLS]], "requests": requests,
                    "gap": f"the handler is not isolated: the press ran {len(ran)} project functions and sent "
                           f"{len(requests)} requests, and the coverage does not record which function the click called"})
    return found
