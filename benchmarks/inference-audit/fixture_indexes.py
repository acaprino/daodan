"""The committed SCIP indexes of the code-graph fixtures (`tests/fixtures/code-graph/<language>/`), written once on
Modal with each language's pinned indexer, through its `index()`: the plugin's for Go and Python, which install
what they need themselves, the adapters' for Java and Kotlin, which run the plugin's two phases in the function's
container, on the plugin's image (`adapters/jvm_here.py`), and the adapter's for C and C++ (`adapters/clang.py`:
CMake's configure and build of the fixture, then scip-clang). No model or graph; a snapshot only for the
pre-map the indexers take their structure from.

    modal deploy benchmarks/inference-audit/fixture_indexes.py
    python benchmarks/inference-audit/fixture_indexes.py spawn --languages go,python,java,kotlin,c,cpp
    python benchmarks/inference-audit/fixture_indexes.py fetch --languages go,python,java,kotlin,c,cpp

`spawn` uploads a fixture's sources, never its `index.scip`, `expected.json` or `kotlin-configs/`. The container
runs the adapter's `index()` and keeps on the volume (`inference-audit/fixture-indexes/<language>/`) the index the
graph reads, `run.json` and, for Kotlin, the compile tasks' `kotlin-configs/` that `refine` reads. `fetch` writes
them into the fixture only when the container ran the checkout's code (`plugin_scripts.code_sha256`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "daodan" if LOCAL else Path("/daodan/map")
FIXTURES = HERE.parents[1] / "tests/fixtures/code-graph" if LOCAL else None
STORE = "inference-audit/fixture-indexes"
KEPT = {"index.scip", "expected.json"}  # the fixture's own files, never uploaded
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
import plugin_scripts  # noqa: E402
from adapters import clang, java, kotlin  # noqa: E402
from indexers import go, python  # noqa: E402

PIP = ("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
RUN_KEYS = ("prefix", "phase", "step", "fallback", "returncode", "seconds", "peak_mb", "index_bytes",
            "same_occurrences", "reverse_relationships_dropped", "stderr_errors", "stderr_error_examples",
            "stderr_tail")


def _mounted(image):
    return (image.add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
            .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                            "/audit/plugin_scripts.py")
            .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                           ignore=["**/__pycache__/**"]))


def _base_image():  # Go and Python: the plugin's index() installs its indexer
    return _mounted(modal.Image.debian_slim(python_version="3.13").apt_install("git", "ca-certificates")
                    .pip_install(*PIP))


def _jvm_image():  # Java and Kotlin, as lang_java.py's and lang_kotlin.py's: the base image, jvm.tools brings the rest
    from indexers import jvm
    return _mounted(modal.Image.from_registry(jvm.IMAGE, add_python="3.13").apt_install("git").pip_install(*PIP))


def _clang_image():  # C and C++: Ubuntu 24.04 (scip-clang v0.4.1 needs glibc 2.38; Debian 12 has 2.36), CMake and gcc
    return _mounted(modal.Image.from_registry("ubuntu:24.04", add_python="3.13")
                    .apt_install("git", "curl", "ca-certificates", *clang.APT).pip_install(*PIP)
                    .run_commands(*clang.install_commands()))


app = modal.App("daodan-fixture-indexes")
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)
ADAPTERS = {"go": go, "python": python, "java": java, "kotlin": kotlin, "c": clang, "cpp": clang}


def _index(language: str, sources: dict[str, bytes]) -> dict:
    """The adapter's index of the uploaded sources, kept on the volume with its run."""
    import shutil
    import traceback
    print("code", plugin_scripts.code_sha256(), flush=True)  # compared with the checkout before trusting the run
    work = Path("/work") / language
    shutil.rmtree(work, ignore_errors=True)  # a warm container keeps the previous call's files
    project = work / language  # scip-python names the project after its directory
    for rel, data in sources.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    store = Path("/results") / STORE / language
    shutil.rmtree(store, ignore_errors=True)
    store.mkdir(parents=True)
    result = {"language": language, "code": plugin_scripts.code_sha256()}
    try:
        import premap
        import snapshot
        manifest = work / "snapshot" / "manifest.sqlite"
        snapshot.write_snapshot(project, manifest)
        module = ADAPTERS[language]  # the structure an indexer takes, as the stage hands it
        given = module.structure(premap.ensure(manifest)) if hasattr(module, "structure") else {}
        engine = module.index(project, work / "engine", **given)
    except Exception:
        engine = {"error": traceback.format_exc()[-3000:]}
    indexes = engine.get("indexes") or []
    result.update(indexer=engine.get("indexer"), error=engine.get("error"),
                  indexes=[[Path(path).name, prefix] for path, prefix in indexes],
                  runs=[{key: run[key] for key in RUN_KEYS if key in run} for run in engine.get("runs", ())])
    if len(indexes) == 1 and not indexes[0][1]:
        shutil.copyfile(indexes[0][0], store / "index.scip")
    else:
        result["error"] = result["error"] or f"expected one index at the root, got {indexes}"
    configs = work / "engine" / "kotlin-configs"
    if language == "kotlin" and configs.is_dir():
        shutil.copytree(configs, store / "kotlin-configs")
    (store / "run.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return {key: result[key] for key in ("language", "indexer", "indexes", "error")}


FUNCTION = dict(timeout=1800, volumes={"/results": volume})


@app.function(image=_base_image(), cpu=2, memory=4096, **FUNCTION)
def index_go(sources: dict) -> dict:
    return _index("go", sources)


@app.function(image=_base_image(), cpu=2, memory=4096, **FUNCTION)
def index_python(sources: dict) -> dict:
    return _index("python", sources)


@app.function(image=_jvm_image(), cpu=2, memory=4096, **FUNCTION)
def index_java(sources: dict) -> dict:
    return _index("java", sources)


@app.function(image=_jvm_image(), cpu=4, memory=8192, **FUNCTION)
def index_kotlin(sources: dict) -> dict:
    return _index("kotlin", sources)


@app.function(image=_clang_image(), cpu=2, memory=4096, **FUNCTION)
def index_c(sources: dict) -> dict:
    return _index("c", sources)


@app.function(image=_clang_image(), cpu=2, memory=4096, **FUNCTION)
def index_cpp(sources: dict) -> dict:
    return _index("cpp", sources)


def _sources(language: str) -> dict[str, bytes]:
    root = FIXTURES / language
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*"))
            if path.is_file() and path.name not in KEPT and "kotlin-configs" not in path.relative_to(root).parts}


def _read(path: str) -> bytes:
    return b"".join(volume.read_file(path))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch"))
    parser.add_argument("--languages", default="go,python,java,kotlin,c,cpp")
    args = parser.parse_args()
    chosen = [item.strip() for item in args.languages.split(",") if item.strip()]
    local = plugin_scripts.code_sha256()
    print("code", local)
    for language in chosen:
        if args.command == "spawn":
            function = modal.Function.from_name("daodan-fixture-indexes", f"index_{language}")
            sources = _sources(language)
            print(language, len(sources), "files", function.spawn(sources).object_id)
            continue
        run = json.loads(_read(f"{STORE}/{language}/run.json"))
        if run["code"] != local or run.get("error"):
            print(language, "not written:", run.get("error") or f"container code {run['code']}")
            continue
        target = FIXTURES / language
        (target / "index.scip").write_bytes(_read(f"{STORE}/{language}/index.scip"))
        if language == "kotlin":
            (target / "kotlin-configs").mkdir(exist_ok=True)
            for entry in volume.listdir(f"{STORE}/kotlin/kotlin-configs"):
                name = Path(entry.path).name
                (target / "kotlin-configs" / name).write_bytes(_read(entry.path).replace(b"\r\n", b"\n"))
        print(language, run["indexer"], (target / "index.scip").stat().st_size, "bytes")
