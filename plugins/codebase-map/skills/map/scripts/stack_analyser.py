#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""stack-analyser as one more source of the static step: what it recognizes from manifests and configuration.

It is installed once in Daodan's cache without install scripts and run without a
model; it reads the project, it does not execute it. Without Node, npm or the network
it is `unavailable` with the reason, and the analysis goes on with the other sources.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

VERSION = "1.27.6"
PACKAGE = "@specfy/stack-analyser"
TIMEOUT = 300


def _cli(cache: Path) -> tuple[Path | None, str]:
    """The installed command line, installing it once; or None and why."""
    prefix = Path(cache) / f"stack-analyser-{VERSION}"
    cli = prefix / "node_modules" / PACKAGE / "dist" / "cli.js"
    if cli.is_file():
        return cli, ""
    npm = shutil.which("npm")
    if npm is None:
        return None, "npm is not on the PATH"
    prefix.mkdir(parents=True, exist_ok=True)
    try:
        done = subprocess.run([npm, "install", "--prefix", str(prefix), "--ignore-scripts", "--no-audit", "--no-fund",
                               f"{PACKAGE}@{VERSION}"], capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, f"npm install failed: {error}"
    if done.returncode != 0 or not cli.is_file():
        return None, f"npm install failed: {done.stderr.strip()[-300:]}"
    return cli, ""


def _found(payload: dict, files: set[str], out: dict) -> None:
    paths = [p.lstrip("/") for p in payload.get("path", []) if p.lstrip("/") in files]
    techs = list(payload.get("techs", [])) + ([payload["tech"]] if payload.get("tech") else [])
    for tech in techs:  # a component's own name is the project's (a compose service), not the technology's
        out.setdefault(tech, {"tech": tech, "name": tech, "paths": set()})["paths"].update(paths)
    for child in payload.get("childs", []):
        _found(child, files, out)


def run(root: Path, cache: Path, files: set[str]) -> dict:
    """What stack-analyser recognizes in `root`, kept to findings with a path among `files`."""
    node = shutil.which("node")
    if node is None:
        return {"status": "unavailable", "reason": "node is not on the PATH"}
    cli, reason = _cli(cache)
    if cli is None:
        return {"status": "unavailable", "reason": reason}
    started = time.monotonic()
    # The tool joins the output path to the working directory: run it in an empty one.
    with tempfile.TemporaryDirectory(prefix="daodan-stack-analyser-") as work:
        try:
            done = subprocess.run([node, str(cli), str(Path(root).resolve()), "--output=out.json"], cwd=work,
                                  capture_output=True, text=True, timeout=TIMEOUT)
            if done.returncode != 0:
                return {"status": "unavailable", "reason": f"stack-analyser exited {done.returncode}: "
                                                           f"{(done.stderr or done.stdout).strip()[-300:]}"}
            payload = json.loads((Path(work) / "out.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            return {"status": "unavailable", "reason": f"stack-analyser gave no result: {error}"}
    found = {}
    _found(payload, set(files), found)
    return {"status": "ok", "version": VERSION, "seconds": round(time.monotonic() - started, 2),
            "found": [{**f, "paths": sorted(f["paths"])} for f in sorted(found.values(), key=lambda f: f["tech"])
                      if f["paths"]]}
