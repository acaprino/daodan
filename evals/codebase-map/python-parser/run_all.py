#!/usr/bin/env python3
"""Produce every raw measurement for the Python parser comparison.

Steps, each writing JSON lines under --out:
  1. list the Python files of every corpus
  2. parse every corpus with stdlib ast under every interpreter given
  3. parse every corpus with tree-sitter-python
  4. parse the syntax-feature corpus with both
  5. build the work-in-progress corpus from the reference interpreter's results
     and parse it with both

analyze.py reads the result. Nothing here interprets a number.

Example:
  python run_all.py --out <dir> \
      --interp 3.11=<python311> --interp 3.14=<python314> --reference 3.14 \
      --ts-python <venv-with-tree-sitter-python> \
      --corpus "jupiter=git|D:/Projects/jupiter" \
      --corpus "daodan=git|D:/Projects/daodan|^exports/" \
      --corpus "sitepkg=dir|D:/Projects/jupiter/.venv/Lib/site-packages"

A git corpus is the files Git does not ignore, without dot-directories, which is
the Codebase Map's own perimeter. A dir corpus is every .py/.pyi below a folder.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mutate  # noqa: E402


def list_git(root: Path, exclude: str | None) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard",
                          "--", "*.py", "*.pyi"], capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout.splitlines()
    pattern = re.compile(exclude) if exclude else None
    files = []
    for rel in out:
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        if pattern and pattern.search(rel):
            continue
        path = root / rel
        if path.is_file():
            files.append(str(path))
    return sorted(files)


def list_dir(root: Path) -> list[str]:
    files = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in names:
            if name.endswith((".py", ".pyi")):
                files.append(str(Path(current) / name))
    return sorted(files)


def run_parallel(jobs: list[tuple[list[str], str]], workers: int) -> None:
    """Run independent worker invocations side by side; fail loudly on any error."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, cmd, label) for cmd, label in jobs]
        for future in futures:
            future.result()


def run(cmd: list[str], label: str) -> None:
    started = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    elapsed = time.perf_counter() - started
    status = "ok" if result.returncode == 0 else f"exit {result.returncode}"
    print(f"  [{status}] {label} ({elapsed:.1f}s)")
    if result.returncode != 0:
        print(result.stderr[-1500:])
        raise SystemExit(f"{label} failed")


def load(path: Path) -> dict:
    records = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            obj = json.loads(line)
            if not obj.get("meta"):
                records[obj["f"]] = obj
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--interp", action="append", required=True,
                    help="VERSION=PATH of a CPython to run stdlib ast under; repeatable")
    ap.add_argument("--reference", required=True,
                    help="VERSION whose ast is the reference for valid code")
    ap.add_argument("--ts-python", required=True)
    ap.add_argument("--cst-python", default=None,
                    help="interpreter with libcst installed; measures LibCST as a third parser")
    ap.add_argument("--corpus", action="append", required=True,
                    help="NAME=git|ROOT[|EXCLUDE_REGEX] or NAME=dir|ROOT")
    ap.add_argument("--mutations-per-corpus", type=int, default=120)
    ap.add_argument("--mutation-corpora", default="",
                    help="comma list of corpora to draw mutations from (default: all git corpora)")
    ap.add_argument("--seed", default="daodan-python-parser-v1")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    out = args.out
    (out / "lists").mkdir(parents=True, exist_ok=True)
    interpreters = dict(item.split("=", 1) for item in args.interp)
    if args.reference not in interpreters:
        raise SystemExit("--reference must name one of the --interp versions")

    corpora = {}
    git_corpora = []
    for spec in args.corpus:
        name, rest = spec.split("=", 1)
        parts = rest.split("|")
        kind, root = parts[0], Path(parts[1])
        files = list_git(root, parts[2] if len(parts) > 2 else None) if kind == "git" else list_dir(root)
        files = [f for f in files if Path(f).name != "manifest.jsonl"]
        if kind == "git":
            git_corpora.append(name)
        list_path = out / "lists" / f"{name}.txt"
        list_path.write_text("\n".join(files) + "\n", encoding="utf-8")
        corpora[name] = {"kind": kind, "root": str(root), "files": len(files), "list": str(list_path)}
        print(f"corpus {name}: {len(files)} files ({kind} {root})")

    ast_worker = str(HERE / "ast_worker.py")
    ts_worker = str(HERE / "ts_worker.py")

    # Every (parser, corpus) pair is an independent process over frozen inputs,
    # so they run side by side. Per-file times are measured inside each worker
    # around the parser call alone; parallelism changes wall time, and the
    # timing section states that it compares medians under the same load.
    jobs = []
    for version, python in sorted(interpreters.items()):
        for name, info in corpora.items():
            jobs.append(([python, ast_worker, "--list", info["list"], "--out",
                          str(out / f"ast-{version}-{name}.jsonl")], f"ast {version} {name}"))
        jobs.append(([python, ast_worker, "--features", "--out",
                      str(out / f"ast-{version}-features.jsonl")], f"ast {version} features"))
    for name, info in corpora.items():
        jobs.append(([args.ts_python, ts_worker, "--list", info["list"], "--out",
                      str(out / f"ts-{name}.jsonl")], f"ts {name}"))
    jobs.append(([args.ts_python, ts_worker, "--features", "--out",
                  str(out / "ts-features.jsonl")], "ts features"))
    if args.cst_python:
        cst_worker = str(HERE / "libcst_worker.py")
        for name, info in corpora.items():
            jobs.append(([args.cst_python, cst_worker, "--list", info["list"], "--out",
                          str(out / f"cst-{name}.jsonl")], f"libcst {name}"))
        jobs.append(([args.cst_python, cst_worker, "--features", "--out",
                      str(out / "cst-features.jsonl")], "libcst features"))
    print(f"\nparsing: {len(jobs)} independent jobs, {args.workers} at a time")
    run_parallel(jobs, args.workers)

    print("\nwork-in-progress corpus:")
    chosen = [c for c in (args.mutation_corpora.split(",") if args.mutation_corpora else git_corpora) if c]
    reference_records = {name: load(out / f"ast-{args.reference}-{name}.jsonl") for name in chosen}
    mut_dir = out / "mut"
    list_path = mutate.generate(reference_records, mut_dir, args.mutations_per_corpus, args.seed)
    count = sum(1 for line in list_path.read_text(encoding="utf-8").splitlines() if line.strip())
    print(f"  {count} mutated files from {', '.join(chosen)}")
    reference_python = interpreters[args.reference]
    run_parallel([
        ([reference_python, ast_worker, "--list", str(list_path), "--out",
          str(out / f"ast-{args.reference}-mut.jsonl")], f"ast {args.reference} mutations"),
        ([args.ts_python, ts_worker, "--list", str(list_path), "--out", str(out / "ts-mut.jsonl")],
         "ts mutations"),
    ], 2)

    meta = {"interpreters": interpreters, "reference": args.reference,
            "ts_python": args.ts_python, "cst_python": args.cst_python, "corpora": corpora,
            "mutation_corpora": chosen, "seed": args.seed}
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nwrote {out / 'meta.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
