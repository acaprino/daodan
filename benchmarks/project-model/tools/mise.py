"""mise: `mise ls --current --json` with MISE_SAFE=1 and MISE_OFFLINE=1, idiomatic version files switched on.

mise lists one active entry per tool: when several files name the same tool only the winner by its precedence
is listed, and nothing says that others disagree. Standard library only."""
from __future__ import annotations

import json
import os

from _versions import canon, rel, sh

VERSION = "2026.11.8"
IDIOMATIC = "node,python,java,go,rust,ruby,elixir,yarn,pnpm,bun,deno,dotnet"


def run(fixture_dir, work_dir) -> dict:
    env = {"MISE_SAFE": os.environ.get("PMV_MISE_SAFE", "1"), "MISE_OFFLINE": "1", "MISE_IDIOMATIC_VERSION_FILE_ENABLE_TOOLS": IDIOMATIC,
           "NO_COLOR": "1"}
    r = sh(["mise", "ls", "--current", "--json"], fixture_dir, env, timeout=120)
    if r["rc"] != 0:
        raise RuntimeError(f"mise exit {r['rc']}: {r['err'].strip()[-400:]}")
    data = json.loads(r["out"] or "{}")
    toolchains = []
    for tool, entries in data.items():
        for e in entries:
            path = rel((e.get("source") or {}).get("path", ""), fixture_dir)
            if path is None:
                continue  # a global or parent config, not the project's
            toolchains.append({"tool": canon(tool), "version": e.get("requested_version") or e.get("version"),
                               "declared_in": path})
    return {"toolchains": toolchains}
