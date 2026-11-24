"""A sample, to be read by a person, of the endpoints a candidate fix would bind: for each, what Noir cites, the function the fix chooses, and the lines of the
source at the cited line and at the start of that function. Prints; writes nothing (the lines are the applications' own text and stay out of the repository).
The verdict of each sample is the reader's (is the chosen function the one the route runs?); `README.md` records the counts of the one made on 24 November 2026.

    python -I benchmarks/noir-binding/sample_check.py <the evidence folder> <a folder outside the repository for the sources> <application> <fix> [how many, 8]

The sources are fetched as text at the pinned commit into `<folder>/<application>-tree` (on this machine: the one place a project's text is read outside Modal;
nothing of it is run, built or installed) and are only read.
"""
import io
import json
import pathlib
import random
import sys
import tarfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apps  # noqa: E402
import causes  # noqa: E402


def fetch(name: str, root: pathlib.Path) -> pathlib.Path:
    _framework, repository, commit, *_ = apps.APPS[name]
    whole = root / f"{name}-tree"
    if not whole.exists():
        data = urllib.request.urlopen(f"https://codeload.github.com/{repository}/tar.gz/{commit}", timeout=300).read()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = archive.getmembers()
            top = members[0].name.split("/")[0]
            for member in members:
                member.name = member.name[len(top):].lstrip("/")
            whole.mkdir(parents=True)
            archive.extractall(whole, members=[m for m in members if m.name and (m.isfile() or m.isdir())], filter="data")
    return whole


def main():
    evidence, sources, name, fix = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    count = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    tree = fetch(name, sources)
    rows = [r for r in json.loads((evidence / f"{name}.json").read_text(encoding="utf-8"))["rows"] if causes.stage(r) == "http" and not r["ok"]]
    chosen = [(r, causes.candidates(r, fix)) for r in rows]
    chosen = [(r, found[0]) for r, found in chosen if len(found) == 1]
    random.Random(24).shuffle(chosen)
    print(f"{name} {fix}: {len(chosen)} unbound endpoints with one candidate; showing {min(count, len(chosen))}")
    for row, found in chosen[:count]:
        lines = (tree / row["file"]).read_text(encoding="utf-8", errors="replace").split("\n")
        at = lambda n: lines[n - 1].strip()[:140] if 1 <= n <= len(lines) else ""
        print(f"\n{row['method']} {row['url']}  Noir: {row['handler']}  cited {row['site']}")
        print(f"   candidate {found['qn'] or found['name']} {found['line']}-{found['end']}")
        print(f"   line {row['line']}: {at(row['line'])}")
        if found["line"] != row["line"]:
            print(f"   line {found['line']}: {at(found['line'])}")


if __name__ == "__main__":
    main()
