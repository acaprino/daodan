"""Go, read only: `go env GOMOD GOWORK`, then `go mod edit -json` (and `go work edit -json`) under
GOTOOLCHAIN=local. Go parses the module file itself and downloads nothing; it looks only at the working
directory and its parents, so a module in a subfolder is found only through a go.work `use`. Standard library
only."""
from __future__ import annotations

import json
import posixpath

from _versions import rel, sh

VERSION = "go1.23.12 (local)"
ENV = {"GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod", "GOPROXY": "off", "GOSUMDB": "off"}


def _edit(cmd, cwd, root, path):
    r = sh(cmd, cwd, ENV, timeout=120)
    if r["rc"] != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))} exit {r['rc']}: {r['err'].strip()[-300:]}")
    d = json.loads(r["out"])
    out = []
    if d.get("Go"):
        out.append({"tool": "go", "version": d["Go"], "declared_in": path, "via": "go"})
    if d.get("Toolchain"):
        out.append({"tool": "go", "version": d["Toolchain"], "declared_in": path, "via": "toolchain"})
    return out, d


def run(fixture_dir, work_dir) -> dict:
    r = sh(["go", "env", "GOMOD", "GOWORK"], fixture_dir, ENV, timeout=60)
    if r["rc"] != 0:
        raise RuntimeError(f"go env exit {r['rc']}: {r['err'].strip()[-300:]}")
    lines = (r["out"].split("\n") + ["", ""])[:2]
    gomod = rel(lines[0], fixture_dir) if lines[0] not in ("", "/dev/null") else None
    gowork = rel(lines[1], fixture_dir) if lines[1] else None
    toolchains = []
    if gowork:
        found, d = _edit(["go", "work", "edit", "-json"], fixture_dir, fixture_dir, gowork)
        toolchains += found
        for use in d.get("Use") or []:
            mod = posixpath.normpath(posixpath.join(use["DiskPath"], "go.mod"))
            found, _ = _edit(["go", "mod", "edit", "-json", mod], fixture_dir, fixture_dir, mod)
            toolchains += found
    elif gomod:
        found, _ = _edit(["go", "mod", "edit", "-json"], fixture_dir, fixture_dir, gomod)
        toolchains += found
    return {"toolchains": toolchains}
