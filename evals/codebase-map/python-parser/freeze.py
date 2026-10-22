#!/usr/bin/env python3
"""Copy every corpus into a frozen directory before measuring it.

Two of the corpora are live repositories under active edit, and a site-packages
directory changes whenever its environment does. A comparison is only valid if
every parser reads the same bytes, so each corpus is copied once into --dest and
every worker reads the copy. The copy keeps relative paths, records each file's
SHA-256 in manifest.jsonl, and is never written again.

Corpus selection is the same as run_all.py: a git corpus is the files Git does
not ignore, minus dot-directories (the Codebase Map's own perimeter); a dir
corpus is every .py/.pyi below a folder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def list_git(root: Path, exclude: str | None) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard",
                          "--", "*.py", "*.pyi"], capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout.splitlines()
    pattern = re.compile(exclude) if exclude else None
    keep = []
    for rel in out:
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        if pattern and pattern.search(rel):
            continue
        if (root / rel).is_file():
            keep.append(rel)
    return sorted(keep)


def list_dir(root: Path) -> list[str]:
    keep = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            if name.endswith((".py", ".pyi")):
                keep.append(Path(current, name).relative_to(root).as_posix())
    return sorted(keep)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--corpus", action="append", required=True,
                    help="NAME=git|ROOT[|EXCLUDE_REGEX] or NAME=dir|ROOT")
    args = ap.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    summary = {}
    for spec in args.corpus:
        name, rest = spec.split("=", 1)
        parts = rest.split("|")
        kind, root = parts[0], Path(parts[1])
        rels = list_git(root, parts[2] if len(parts) > 2 else None) if kind == "git" else list_dir(root)
        target_root = args.dest / name
        if target_root.exists():
            shutil.rmtree(target_root)
        rows, total = [], 0
        for rel in rels:
            source = root / rel
            target = target_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            data = source.read_bytes()
            target.write_bytes(data)
            total += len(data)
            rows.append({"rel": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        (target_root / "manifest.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        summary[name] = {"kind": kind, "source": str(root), "files": len(rows), "bytes": total}
        print(f"{name}: {len(rows)} files, {total / 1e6:.1f} MB, from {root}")
    (args.dest / "freeze.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
