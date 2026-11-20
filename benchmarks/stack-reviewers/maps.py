"""Scrive i due snapshot di un caso, al genitore del target e al target, sulla stessa cartella.

    python benchmarks/stack-reviewers/maps.py CLONE TARGET OUT PATH...

`CLONE` è un clone git con i blob dei due commit, `PATH` le cartelle da prendere; i file della radice del
repository si prendono sempre. In `OUT` restano `tree/` all'albero del target, senza storia, `base/` e `candidate/`
con i loro snapshot (la mappa dei moduli solo nel secondo) e `target.diff`, ristretto alle stesse cartelle.
Poi `plan.py OUT/base/snapshot.sqlite OUT/candidate/snapshot.sqlite OUT/target.diff OUT/plan`.
"""

import io
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "daodan/core"


def git(clone: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(clone), *args], check=True, capture_output=True).stdout


def extract(clone: Path, rev: str, paths: list[str], tree: Path) -> None:
    rows = [line.split("\t", 1) for line in git(clone, "ls-tree", rev).decode().splitlines()]
    root = [name for meta, name in rows if meta.split()[1] == "blob"]
    present = [path for path in paths if git(clone, "ls-tree", rev, "--", path).strip()]
    shutil.rmtree(tree, ignore_errors=True)
    tree.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(git(clone, "archive", rev, "--", *root, *present))) as archive:
        archive.extractall(tree, filter="data")


def write(tree: Path, out: Path, *flags: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "write.log", "wb") as log:
        subprocess.run([sys.executable, "-B", str(CORE / "snapshot.py"), "write", str(tree), "--out",
                        str(out / "snapshot.sqlite"), "--no-engine", "--no-index", *flags],
                       check=True, stdout=log, stderr=subprocess.STDOUT)


def main(clone: Path, target: str, out: Path, paths: list[str]) -> None:
    extract(clone, f"{target}^", paths, out / "tree")
    write(out / "tree", out / "base", "--no-modules")
    extract(clone, target, paths, out / "tree")
    write(out / "tree", out / "candidate")
    root = [line.split("\t", 1)[1] for line in git(clone, "ls-tree", target).decode().splitlines()
            if line.split()[1] == "blob"]
    (out / "target.diff").write_bytes(git(clone, "show", "--format=", target, "--", *root, *paths))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4:])
