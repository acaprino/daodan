"""Daodan's command: `daodan app`, `daodan mcp`, or any tool of the core by its file's name.

    daodan app [--work DIR] [--port N]        the standalone app (`--desktop`: as Daodan's window starts it)
    daodan mcp --project DIR | --hook         the MCP server a harness starts, and its refresh hook
    daodan snapshot write PROJECT --out DIR   `core/snapshot.py`, as every other tool of `core/`

The tools stay the files they are: this starts one as its own program, with `core/` first among the places
Python imports from. A harness starts this in the analysed project's folder; an installed command does not import
from the folder it is started in, so no file of the project is read as code.
"""
from __future__ import annotations

import re
import runpy
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parent / "core"
NAMES = {"mcp": "mcp_server"}
NAME = re.compile(r"[a-z][a-z0-9_]*")


def main(argv: list[str] | None = None) -> None:
    words = sys.argv[1:] if argv is None else argv
    name = NAMES.get(words[0], words[0].replace("-", "_")) if words else ""
    script = CORE / f"{name}.py"
    if not NAME.fullmatch(name) or not script.is_file():
        print(__doc__, file=sys.stderr)
        raise SystemExit(0 if words and words[0] in ("-h", "--help") else 2)
    sys.argv = [str(script), *words[1:]]
    sys.path.insert(0, str(CORE))
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
