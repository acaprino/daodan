"""uv choosing the interpreter, read only: `uv python find -v`. uv reads `.python-version` first and
`requires-python` of the project otherwise, and names the request and its source in its debug log; nothing is
downloaded (the command only searches). The request is reported even when no interpreter satisfies it. Standard
library only."""
from __future__ import annotations

import re
from pathlib import Path

from _versions import sh

VERSION = "0.13.8"


def requests(fixture_dir) -> tuple[list[dict], dict]:
    r = sh(["uv", "python", "find", "-v"], fixture_dir, {"NO_COLOR": "1"}, timeout=120)
    found = []
    for line in (r["out"] + "\n" + r["err"]).splitlines():
        m = re.search(r"Using Python request `([^`]+)` from (.*)$", line)
        if not m:
            continue
        item = {"tool": "python", "version": m.group(1)}
        for token in re.findall(r"`([^`]+)`", m.group(2)):
            if (Path(fixture_dir) / token).is_file():
                item["declared_in"] = Path(token).as_posix()
                break
        else:
            item["via"] = m.group(2).strip()
        found.append(item)
    return found, r


def run(fixture_dir, work_dir) -> dict:
    found, r = requests(fixture_dir)
    if not found and r["rc"] not in (0, 2):
        raise RuntimeError(f"uv exit {r['rc']}: {r['err'].strip()[-300:]}")
    return {"toolchains": found}
