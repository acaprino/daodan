"""C and C++ indexed with a toolchain unpacked into one folder: the proof that CMake and scip-clang need no
compiler installed in the image.

The base is Daodan's one image for every language, `debian:trixie-slim` pinned by digest (glibc 2.41; scip-clang
v0.4.1 and the noble compilers ask 2.38 at most), with nothing installed by apt; Modal's `add_python` stands in
for the tools store's Python. A fetch step stands in for Daodan's: the Ubuntu noble packages of gcc, g++,
libc6-dev and make, with everything they depend on, come from the archive snapshot of `STAMP` (each InRelease
by the sha256 pinned in `INRELEASE`, each file by the sha256 the index gives) and are unpacked with
`dpkg-deb -X` into `ROOT`, which is both the sysroot and the compiler's prefix. CMake 3.28.3 and scip-clang
v0.4.1 come from their official releases, checked by sha256. CMake gets the unpacked gcc, g++ and make and
`CMAKE_SYSROOT=ROOT`; the tools run with `LD_LIBRARY_PATH` on the libraries of the packages the base lacks.

For each case the graph is built twice with today's code: from the index the run of 14 November 2026 stored on
the volume (`lang_clang.py`, apt's build-essential), the control, and from the index this toolchain writes. Rows
are compared by identity: nodes, edges, holes, missing files. The control is also compared with
`results/graph-<c|cpp>-<case>.json`, to tell code drift from what the toolchain changes.

    modal deploy benchmarks/inference-audit/clang_toolchain.py
    python benchmarks/inference-audit/clang_toolchain.py spawn [--cases zlib,tinyxml2]
    python benchmarks/inference-audit/clang_toolchain.py fetch

`fetch` writes `results/clang-toolchain.json`. No model.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "daodan" if LOCAL else Path("/daodan/map")
AUDIT = HERE if LOCAL else Path("/audit")
RESULTS = HERE / "results"
APP = "daodan-clang-toolchain"
PROOF = "inference-audit/clang-toolchain"  # on the volume
STORED = "inference-audit/graph-clang"  # what lang_clang.py stored on 14 November 2026

# amd64 manifest sha256:7378260c0a098d27ac206225db5e7d92b8c7c84ea7afccc86eeb513756bbd392
BASE = "debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2"
STAMP = "20261114T000000Z"
SNAPSHOT = f"https://snapshot.ubuntu.com/ubuntu/{STAMP}"
# A snapshot never changes: each InRelease's signature was checked once with gpgv and the Ubuntu Archive Automatic
# Signing Key (2018), F6ECB3762474EDA9D21B7022871920D1991BC93C, on 16 November 2026; its sha256 stands for it.
INRELEASE = {"noble": "cdb2f31d809f589719a53c6ad15f255b27569c4059542ada282aaa21b8e164b0",
             "noble-security": "7bc0a37d270ba8f170b26d8fb50f2d0e15c2303ce19d63225efab0689c426865",
             "noble-updates": "8b3927dcf08a5850f650f10533b80966c48bd9334dc7c6f324776c783cbf2154"}
SUITES = tuple(INRELEASE)
# What a C or C++ index needs that a base may lack: reported, never installed.
NEEDED = ("python3", "gcc", "g++", "make", "cmake", "git", "curl", "ca-certificates")
WANT = ("gcc", "g++", "libc6-dev", "make")
# The versions the stored run's symbols name: with others, external identities differ.
STORED_VERSIONS = {"libc6-dev": "2.39-0ubuntu8.12", "libgcc-13-dev": "13.3.0-6ubuntu2~24.04.1",
                   "libstdc++-13-dev": "13.3.0-6ubuntu2~24.04.1"}
CMAKE = ("https://github.com/Kitware/CMake/releases/download/v3.28.3/cmake-3.28.3-linux-x86_64.tar.gz",
         "804d231460ab3c8b556a42d2660af4ac7a0e21c98a7f8ee3318a74b4a9a187a6")
TOOLS = Path("/daodan/tools")
ROOT = TOOLS / "c"
HOSTLIB = TOOLS / "c-hostlib"
CC, CXX, MAKE = (ROOT / "usr/bin/x86_64-linux-gnu-gcc-13", ROOT / "usr/bin/x86_64-linux-gnu-g++-13",
                 ROOT / "usr/bin/make")
WARNINGS = ("is not one of clang/clang++/gcc/g++/nvcc", "may be unable to locate standard library headers")


def _image():
    return (
        modal.Image.from_registry(BASE, add_python="3.13")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "certifi")
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(AUDIT / "modal_audit.py", "/audit/modal_audit.py")
        .add_local_file(AUDIT / "plugin_scripts.py", "/audit/plugin_scripts.py")
        .add_local_file(AUDIT / "lang_clang.py", "/audit/lang_clang.py")
        .add_local_dir(AUDIT / "adapters", "/audit/adapters", ignore=["**/__pycache__/**"])
        .add_local_file(RESULTS / "graph-c-zlib.json", "/audit/results/graph-c-zlib.json")
        .add_local_file(RESULTS / "graph-cpp-tinyxml2.json", "/audit/results/graph-cpp-tinyxml2.json")
    )


app = modal.App(APP, image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)

# ---------------------------------------------------------------------------------------------------------
# The fetch step


def _get(url: str) -> bytes:
    import urllib.request
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def _download(url: str, target: Path, sha256: str) -> int:
    import urllib.request
    target.parent.mkdir(parents=True, exist_ok=True)
    digest, size = hashlib.sha256(), 0
    with urllib.request.urlopen(url, timeout=600) as response, open(target, "wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
            size += len(chunk)
    if digest.hexdigest() != sha256:
        raise ValueError(f"sha256 mismatch for {url}: {digest.hexdigest()}")
    return size


def _stanzas(text: str):
    for block in text.split("\n\n"):
        fields, key = {}, None
        for line in block.split("\n"):
            if line[:1] in (" ", "\t") and key:
                fields[key] += "\n" + line
            elif ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        if "Package" in fields:
            yield fields


def _names(field: str) -> list[list[str]]:
    out = []
    for clause in field.split(","):
        alternatives = [re.sub(r"\s*\(.*?\)|\s*\[.*?\]|:\w+", "", item).strip() for item in clause.split("|")]
        if alternatives and alternatives[0]:
            out.append(alternatives)
    return out


def _newer(a: str, b: str) -> bool:
    return subprocess.run(["dpkg", "--compare-versions", a, "gt", b]).returncode == 0


def _index(work: Path) -> dict[str, list[dict]]:
    """Every package of main for amd64 in the snapshot's suites, each version it has there."""
    import gzip
    packages: dict[str, list[dict]] = collections.defaultdict(list)
    for suite in SUITES:
        release = work / f"{suite}.InRelease"
        release.write_bytes(_get(f"{SNAPSHOT}/dists/{suite}/InRelease"))
        if hashlib.sha256(release.read_bytes()).hexdigest() != INRELEASE[suite]:
            raise ValueError(f"{suite}: InRelease is not the one pinned")
        section = release.read_text(encoding="utf-8").split("SHA256:", 1)[1]
        entry = next(line.split() for line in section.split("\n")
                     if line.split()[2:] == ["main/binary-amd64/Packages.gz"])
        data = _get(f"{SNAPSHOT}/dists/{suite}/main/binary-amd64/Packages.gz")
        if hashlib.sha256(data).hexdigest() != entry[0] or len(data) != int(entry[1]):
            raise ValueError(f"{suite}: Packages.gz does not match its InRelease")
        for fields in _stanzas(gzip.decompress(data).decode("utf-8")):
            packages[fields["Package"]].append(fields)
    return packages


def _closure(index: dict[str, list[dict]]) -> dict[str, dict]:
    """What `WANT` needs, Depends and Pre-Depends, at the highest version the suites give (as apt picks), first
    alternative a package satisfies; nothing assumed installed, so the sysroot is whole."""
    providers = collections.defaultdict(list)
    for name, versions in index.items():
        for alternatives in _names(versions[-1].get("Provides", "")):
            providers[alternatives[0]].append(name)
    packages = {}

    def best(name: str) -> dict:
        if name not in packages:
            highest = index[name][0]
            for fields in index[name][1:]:
                highest = fields if _newer(fields["Version"], highest["Version"]) else highest
            packages[name] = highest
        return packages[name]

    chosen: dict[str, dict] = {}

    def have(name):
        return name in chosen or any(item in chosen for item in providers.get(name, ()))

    queue = list(WANT)
    while queue:
        name = queue.pop(0)
        if name in chosen:
            continue
        if name not in index:
            name = providers[name][0]
        chosen[name] = best(name)
        for field in ("Pre-Depends", "Depends"):
            for alternatives in _names(chosen[name].get(field, "")):
                if not any(have(item) for item in alternatives):
                    queue.append(next((item for item in alternatives if item in index or item in providers),
                                      alternatives[0]))
    return chosen


def _merge_usr() -> None:
    """The merged /usr layout base-files gives a system: /lib, /lib64, /bin and /sbin are links into /usr."""
    for top in ("bin", "sbin", "lib", "lib64"):
        path, inside = ROOT / top, ROOT / "usr" / top
        if path.is_dir() and not path.is_symlink():
            shutil.copytree(path, inside, symlinks=True, dirs_exist_ok=True)
            shutil.rmtree(path)
        if inside.exists() and not path.exists():
            path.symlink_to(f"usr/{top}")


def _relative_links() -> int:
    """Absolute links point into the sysroot, as they would on the system the packages were built for."""
    changed = 0
    for here, dirs, names in os.walk(ROOT):
        for name in dirs + names:
            link = Path(here) / name
            if link.is_symlink() and os.readlink(link).startswith("/"):
                target = ROOT / os.readlink(link).lstrip("/")
                link.unlink()
                link.symlink_to(os.path.relpath(target, link.parent))
                changed += 1
    return changed


def _size(path: Path) -> int:
    return sum((Path(here) / name).lstat().st_size for here, _dirs, names in os.walk(path) for name in names)


def fetch_toolchain(adapter) -> tuple[dict, dict[str, str]]:
    """The toolchain under TOOLS, what it weighs, and the owner (`package@version`) of each sysroot file."""
    started, work = time.time(), TOOLS / "downloads"
    work.mkdir(parents=True, exist_ok=True)
    chosen = _closure(_index(work))
    installed = {fields["Package"] for fields in _stanzas(Path("/var/lib/dpkg/status").read_text(encoding="utf-8"))
                 if "install ok installed" in fields.get("Status", "")}
    owners, lacking, downloaded = {}, [], 0
    for name, fields in sorted(chosen.items()):
        deb = work / Path(fields["Filename"]).name
        downloaded += _download(f"{SNAPSHOT}/{fields['Filename']}", deb, fields["SHA256"])
        listed = subprocess.run(["dpkg-deb", "-X", str(deb), str(ROOT)], capture_output=True, text=True, check=True)
        owner = f"{adapter._clean(name)}@{adapter._clean(fields['Version'])}"
        for line in listed.stdout.split("\n"):
            rel = line.strip().removeprefix("./").rstrip("/")
            rel = re.sub(r"^(bin|sbin|lib|lib64)/", r"usr/\1/", rel)
            if rel:
                owners[rel] = owner
                if name not in installed and re.fullmatch(r"usr/lib/x86_64-linux-gnu/[^/]+\.so[.\d]*", rel):
                    lacking.append(rel)
        deb.unlink()
    _merge_usr()
    links = _relative_links()
    HOSTLIB.mkdir(parents=True, exist_ok=True)
    for rel in lacking:
        if not (HOSTLIB / Path(rel).name).exists():
            (HOSTLIB / Path(rel).name).symlink_to(ROOT / rel)
    archive = work / "cmake.tar.gz"
    downloaded_cmake = _download(CMAKE[0], archive, CMAKE[1])
    with tarfile.open(archive) as tar:
        tar.extractall(TOOLS / "cmake-unpack", filter="data")
    (TOOLS / "cmake-unpack" / os.listdir(TOOLS / "cmake-unpack")[0]).rename(TOOLS / "cmake")
    archive.unlink()
    scip = TOOLS / "scip-clang"
    downloaded_scip = _download(adapter.URL, scip, adapter.SHA256)
    scip.chmod(0o755)
    versions = {name: chosen[name]["Version"] for name in STORED_VERSIONS if name in chosen}
    info = {"stamp": STAMP, "base_lacks": [name for name in NEEDED if name not in installed],
            "packages": len(chosen), "lacking_in_base": sorted(set(chosen) - installed),
            "versions": versions, "versions_as_stored": versions == STORED_VERSIONS, "absolute_links_rewritten": links,
            "download_mib": {"packages": round(downloaded / 2**20, 1), "cmake": round(downloaded_cmake / 2**20, 1),
                             "scip-clang": round(downloaded_scip / 2**20, 1)},
            "unpacked_mib": {"sysroot": round(_size(ROOT) / 2**20, 1),
                             "cmake": round(_size(TOOLS / "cmake") / 2**20, 1),
                             "scip-clang": round(scip.stat().st_size / 2**20, 1)},
            "seconds": round(time.time() - started, 1)}
    return info, owners


def package_map(project: str, owners: dict[str, str], adapter) -> tuple[list[dict], dict]:
    """`adapters/clang.package_map` with the sysroot: search directories from the unpacked compilers, owners
    from the unpacked packages."""
    def dirs(compiler: Path, language: str) -> list[str]:
        err = subprocess.run([str(compiler), f"--sysroot={ROOT}", f"-x{language}", "-E", "-v", "-"], input="",
                             capture_output=True, text=True).stderr.split("\n")
        try:
            start, end = err.index("#include <...> search starts here:") + 1, err.index("End of search list.")
        except ValueError:
            return []
        return [os.path.realpath(line.strip()) for line in err[start:end] if line.strip()]

    by_path = {os.path.realpath(ROOT / rel): owner for rel, owner in owners.items()}
    roots = list(dict.fromkeys(dirs(CC, "c") + dirs(CXX, "c++")))
    entries, notes = [{"path": ".", "package": project}], {"search_dirs": roots, "mixed": [], "renamed": {}}
    for root in roots:
        for here, _dirs, names in os.walk(root):
            votes = collections.Counter(by_path[path] for name in names
                                        if (path := os.path.realpath(os.path.join(here, name))) in by_path)
            if votes:
                owner, count = votes.most_common(1)[0]
                if len(votes) > 1:
                    notes["mixed"].append({"path": here, "package": owner, "files": count,
                                           "others": dict(votes.most_common()[1:])})
                entries.append({"path": here, "package": owner})
    return entries, notes


# ---------------------------------------------------------------------------------------------------------
# Row by row


def _rows(graph: dict) -> dict:
    return {"nodes": {node["id"]: json.dumps(node, sort_keys=True) for node in graph["nodes"]},
            "edges": collections.Counter(json.dumps(edge, sort_keys=True) for edge in graph["edges"]),
            "holes": collections.Counter(json.dumps(hole, sort_keys=True) for hole in graph["holes"]),
            "missing": {item["path"]: item["reason"] for item in graph["files"]["missing"]}}


def compare(old: dict, new: dict, examples: int = 15) -> dict:
    """What `new` has that `old` lacks and the reverse, per kind of row; equal when every list is empty."""
    a, b = _rows(old), _rows(new)
    out = {"equal": True, "files": {"old": {k: v for k, v in old["files"].items() if k != "missing"},
                                    "new": {k: v for k, v in new["files"].items() if k != "missing"}}}
    changed = sorted(key for key in a["nodes"].keys() & b["nodes"].keys() if a["nodes"][key] != b["nodes"][key])
    kinds = {"nodes": (sorted(a["nodes"].keys() - b["nodes"].keys()), sorted(b["nodes"].keys() - a["nodes"].keys())),
             "edges": (sorted((a["edges"] - b["edges"]).elements()), sorted((b["edges"] - a["edges"]).elements())),
             "holes": (sorted((a["holes"] - b["holes"]).elements()), sorted((b["holes"] - a["holes"]).elements())),
             "missing": (sorted(f"{k}: {v}" for k, v in a["missing"].items() if b["missing"].get(k) != v),
                         sorted(f"{k}: {v}" for k, v in b["missing"].items() if a["missing"].get(k) != v))}
    for kind, (only_old, only_new) in kinds.items():
        out[kind] = {"old": sum(a[kind].values()) if kind in ("edges", "holes") else len(a[kind]),
                     "new": sum(b[kind].values()) if kind in ("edges", "holes") else len(b[kind]),
                     "only_old": len(only_old), "only_new": len(only_new),
                     "examples_old": only_old[:examples], "examples_new": only_new[:examples]}
        out["equal"] &= not only_old and not only_new
    out["nodes"]["changed"], out["nodes"]["examples_changed"] = len(changed), changed[:examples]
    out["equal"] &= not changed
    return out


# ---------------------------------------------------------------------------------------------------------
# The run


# 4 cores and 4 GiB for at most 20 minutes cost at most 0.08 USD; the stored runs peaked at 402 MB.
@app.function(cpu=4, memory=4096, timeout=1200, volumes={"/results": volume})
def prove(cases: list[str]) -> dict:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    sys.path[:0] = [str(AUDIT), str(PLUGIN / "core")]
    import lang_clang
    from adapters import clang as adapter
    report = {"base": BASE, "cases": {}}
    report["tools"], owners = fetch_toolchain(adapter)
    os.environ["PATH"] = f"{TOOLS / 'cmake/bin'}:{ROOT / 'usr/bin'}:{os.environ['PATH']}"
    os.environ["LD_LIBRARY_PATH"] = str(HOSTLIB)
    adapter.BINARY = str(TOOLS / "scip-clang")
    adapter.package_map = lambda project: package_map(project, owners, adapter)
    configure = (f"-DCMAKE_C_COMPILER={CC}", f"-DCMAKE_CXX_COMPILER={CXX}", f"-DCMAKE_SYSROOT={ROOT}",
                 f"-DCMAKE_MAKE_PROGRAM={MAKE}")
    for case in cases:
        started, spec = time.time(), lang_clang.CASES[case]
        stored, work = Path("/results") / STORED / case, Path("/work") / case
        source = work / "src"
        with tarfile.open(stored / "source.tar.gz") as tar:
            tar.extractall(source, filter="data")
        control = Path("/work/control") / case
        control.mkdir(parents=True)
        stored_engine = json.loads((stored / "engine.json").read_text(encoding="utf-8"))
        copied = ["engine.json", "run.json", "compile_commands.json"] + [item[0] for item in stored_engine["indexes"]]
        for name in copied:
            if (stored / name).is_file():
                shutil.copyfile(stored / name, control / name)
        lang_clang.write(control, source, Path("/out/control"), case)
        files = adapter.perimeter(source, spec["language"])
        project = f"{case}@{spec['commit'][:12]}"
        engine = adapter.index(source, work, files, project=project, configure=configure)
        engine.update(indexes=[[Path(path).name, prefix] for path, prefix in engine["indexes"]], perimeter=files,
                      mirror=str(work / "mirror"), project=project, language=spec["language"])
        (work / "engine.json").write_text(json.dumps(engine, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        result = {"perimeter_as_stored": files == stored_engine["perimeter"],
                  "runs": [{key: run.get(key) for key in ("step", "returncode", "seconds", "peak_mb", "diagnostics")}
                           for run in engine["runs"]],
                  "stored_runs": [{key: run.get(key) for key in ("step", "returncode", "seconds", "diagnostics")}
                                  for run in stored_engine["runs"]]}
        log = work / "scip-clang.log"
        text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        result["scip_clang_warnings"] = {warning: warning in text for warning in WARNINGS}
        compdb = work / "compile_commands.json"
        if compdb.is_file():
            first = json.loads(compdb.read_text(encoding="utf-8"))[0]
            result["first_command"] = (first.get("command") or " ".join(first.get("arguments", [])))[:400]
        if engine["indexes"]:
            lang_clang.write(work, source, Path("/out/new"), case)
            name = f"graph-{spec['language']}-{case}.json"
            new, old = (json.loads((Path(f"/out/{kind}") / name).read_text(encoding="utf-8"))
                        for kind in ("new", "control"))
            result["new_vs_control"] = compare(old, new)
            result["control_vs_stored"] = compare(json.loads((AUDIT / "results" / name).read_text(encoding="utf-8")),
                                                  old)
        result["seconds"] = round(time.time() - started, 1)
        report["cases"][case] = result
        out = Path("/results") / PROOF / case
        out.mkdir(parents=True, exist_ok=True)
        for folder in (Path("/out/new"), Path("/out/control")):
            for path in folder.glob(f"graph-*-{case}*.json") if folder.is_dir() else ():
                shutil.copyfile(path, out / f"{folder.name}-{path.name}")
        for name in ("engine.json", "compile_commands.json", "scip-clang.log", "package-map.json"):
            if (work / name).is_file():
                shutil.copyfile(work / name, out / name)
    (Path("/results") / PROOF / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8")
    volume.commit()
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--cases", default="zlib,tinyxml2")
    args = parser.parse_args()
    if args.command == "spawn":
        print(modal.Function.from_name(APP, "prove").spawn(args.cases.split(",")).object_id)
    else:
        data = b"".join(volume.read_file(f"{PROOF}/report.json"))
        (RESULTS / "clang-toolchain.json").write_bytes(data)
        report = json.loads(data)
        print(json.dumps(report["tools"], indent=1))
        for case, result in report["cases"].items():
            print(case, {key: result.get(key, {}).get("equal") for key in ("new_vs_control", "control_vs_stored")})
