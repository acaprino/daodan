"""uv choosing and installing the interpreter: when `uv python find -v` shows a request, `uv venv
--python-preference only-managed` downloads the managed CPython that satisfies it (python-build-standalone from
releases.astral.sh). The version printed is the one chosen, kept in `selected`; `version` is the request as uv
read it. Standard library only."""
from __future__ import annotations

import re
from pathlib import Path

from _versions import confine, sh
from uv_find import requests

VERSION = "0.13.8"


def run(fixture_dir, work_dir) -> dict:
    found, _ = requests(fixture_dir)
    if not found:
        return {"toolchains": []}
    env = {"NO_COLOR": "1"}
    if confine():
        base = Path(work_dir) / "cache" / "uv"
        env.update({"UV_PYTHON_INSTALL_DIR": str(base / "python"), "UV_CACHE_DIR": str(base / "cache"),
                    "TMPDIR": str(base / "tmp")})
        (base / "tmp").mkdir(parents=True, exist_ok=True)
    r = sh(["uv", "venv", "-v", "--clear", "--python-preference", "only-managed", str(Path(work_dir) / "venv")],
           fixture_dir, env, timeout=900)
    m = re.search(r"Using CPython (\S+)", r["out"] + r["err"])
    if r["rc"] != 0 or not m:
        raise RuntimeError(f"uv venv exit {r['rc']}: {r['err'].strip()[-400:]}")
    for item in found:
        item["selected"] = m.group(1)
    return {"toolchains": found}
