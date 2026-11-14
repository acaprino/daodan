"""Go choosing the toolchain: `GOTOOLCHAIN=auto go version` in a module whose go.mod or go.work asks for a newer
Go than the one installed. Go downloads the toolchain as a module (golang.org/toolchain) through GOPROXY, checks
it against GOSUMDB and runs it; the version printed is the one selected, not the line written in the file (an
older request is served by the installed Go). The file is the one `go env GOMOD GOWORK` names. Standard library
only."""
from __future__ import annotations

import re
from pathlib import Path

from _versions import confine, rel, sh

VERSION = "go1.23.12 (local) with GOTOOLCHAIN=auto"


def run(fixture_dir, work_dir) -> dict:
    env = {"GOTOOLCHAIN": "auto"}
    if confine():
        base = Path(work_dir) / "cache" / "go"
        env.update({"GOPATH": str(base / "path"), "GOMODCACHE": str(base / "mod"), "GOCACHE": str(base / "build"),
                    "GOFLAGS": "-modcacherw", "TMPDIR": str(base / "tmp")})
        (base / "tmp").mkdir(parents=True, exist_ok=True)
    probe = sh(["go", "env", "GOMOD", "GOWORK"], fixture_dir, dict(env, GOTOOLCHAIN="local"), timeout=60)
    lines = (probe["out"].split("\n") + ["", ""])[:2]
    declared = rel(lines[1], fixture_dir) if lines[1] else (
        rel(lines[0], fixture_dir) if lines[0] not in ("", "/dev/null") else None)
    if not declared:
        return {"toolchains": []}
    r = sh(["go", "version"], fixture_dir, env, timeout=900)
    m = re.search(r"go version go(\S+) ", r["out"])
    if r["rc"] != 0 or not m:
        raise RuntimeError(f"go version exit {r['rc']}: {r['err'].strip()[-400:]}")
    return {"toolchains": [{"tool": "go", "version": m.group(1), "declared_in": declared}]}
