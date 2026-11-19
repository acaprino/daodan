"""Source: the Git submodules `.gitmodules` declares, read from the file, never run.

The file is Git's configuration format: `[submodule "name"]` sections of `key = value` lines. Each submodule is
an excluded folder: another repository, not code of the project. A submodule whose
folder is missing or empty is a `submodule_absent` gap: its code is not in the project. The commit a gitlink
pins is Git's index, not this file: it stays absent.
"""
from __future__ import annotations

import re

import confinement

NAME, VERSION, RANK = "gitmodules", "daodan/premap/v1", "reader"
SECTION = re.compile(r'^\[\s*submodule\s+"((?:[^"\\]|\\.)*)"\s*\]$')
ENTRY = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)\s*=\s*(.*)$")


def _value(raw: str) -> str:
    raw = re.split(r'\s[#;]', raw, maxsplit=1)[0].strip() if '"' not in raw else raw.strip()
    return raw[1:-1].replace('\\"', '"') if len(raw) >= 2 and raw[0] == raw[-1] == '"' else raw


def run(context):
    path = context.root / ".gitmodules"
    confinement.reject_link_chain(path)
    if not path.is_file():
        return None
    found: dict[str, dict] = {}
    current = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line[0] in "#;":
            continue
        section = SECTION.match(line)
        if section:
            current = found.setdefault(section.group(1), {})
            continue
        entry = ENTRY.match(line)
        if entry and current is not None:
            current[entry.group(1).lower()] = _value(entry.group(2))
    excluded, gaps = [], []
    for name, fields in sorted(found.items()):
        folder = (fields.get("path") or name).strip("/")
        excluded.append({"path": folder + "/", "why": "submodule"})
        disk = context.root / folder
        if not disk.is_dir() or not any(disk.iterdir()):
            gaps.append({"kind": "submodule_absent", "path": folder,
                         "detail": f"submodule {fields.get('url')} is not checked out: its code is not in the project"})
    return {"facts": {"excluded": excluded}, "gaps": gaps}
