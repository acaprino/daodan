"""The committed SCIP indexes of the code-graph fixtures (`tests/fixtures/code-graph/<language>/`), written once on
Modal with each language's pinned indexer, through the adapters' `index()`. No model, snapshot or graph.

    modal deploy benchmarks/inference-audit/fixture_indexes.py
    python benchmarks/inference-audit/fixture_indexes.py spawn --languages go,python,java,kotlin
    python benchmarks/inference-audit/fixture_indexes.py fetch --languages go,python,java,kotlin

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
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
FIXTURES = HERE.parents[1] / "tests/fixtures/code-graph" if LOCAL else None
STORE = "inference-audit/fixture-indexes"
KEPT = {"index.scip", "expected.json"}  # the fixture's own files, never uploaded
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
import plugin_scripts  # noqa: E402
from adapters import go, java, kotlin, python  # noqa: E402

PIP = ("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
# scip-java finds `gradle` on the PATH when the project has no wrapper.
GRADLE = ("8.10.2", "31c55713e40233a8303827ceb42ca48a47267a0ad4bab9177123121e71524c26")
RUN_KEYS = ("prefix", "step", "fallback", "returncode", "seconds", "peak_mb", "index_bytes", "same_occurrences",
            "reverse_relationships_dropped", "stderr_errors", "stderr_error_examples", "stderr_tail")


def _mounted(image):
    return (image.add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
            .add_local_file(HERE / "plugin_scripts.py" if LOCAL else Path("/audit/plugin_scripts.py"),
                            "/audit/plugin_scripts.py")
            .add_local_dir(HERE / "adapters" if LOCAL else Path("/audit/adapters"), "/audit/adapters",
                           ignore=["**/__pycache__/**"]))


def _go_image():
    import resolve_edges as rx
    asset, sha = rx.GO_ASSETS["linux-x64"]
    return _mounted(
        modal.Image.debian_slim(python_version="3.13").apt_install("git", "curl", "ca-certificates")
        .pip_install(*PIP)
        .run_commands(f"curl -fsSL https://go.dev/dl/{asset} -o /tmp/{asset}",
                      f"echo '{sha}  /tmp/{asset}' | sha256sum -c -",
                      f"tar -xzf /tmp/{asset} -C /opt && rm /tmp/{asset}",
                      f"GOBIN=/opt/scip/bin GOPATH=/tmp/gopath GOFLAGS= GOTOOLCHAIN=local /opt/go/bin/go install "
                      f"github.com/scip-code/scip-go/cmd/scip-go@{go.VERSION} && rm -rf /tmp/gopath"))


def _python_image():  # as lang_python.py's
    return _mounted(modal.Image.debian_slim(python_version="3.13").apt_install(*python.APT).pip_install(*PIP)
                    .run_commands(*python.install_commands()))


def _java_image():  # as lang_java.py's
    return _mounted(modal.Image.debian_slim(python_version="3.13").apt_install("git", "curl", "ca-certificates",
                                                                               *java.APT)
                    .pip_install(*PIP).run_commands(*java.install_commands()))


def _kotlin_image():  # as lang_kotlin.py's, then Gradle
    version, sha = GRADLE
    return _mounted(
        modal.Image.debian_slim(python_version="3.13").apt_install("git", "curl", "ca-certificates", "unzip")
        .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(*kotlin.install_commands())
        .run_commands(f"curl -fsSL https://services.gradle.org/distributions/gradle-{version}-bin.zip -o /tmp/g.zip",
                      f"echo '{sha}  /tmp/g.zip' | sha256sum -c -",
                      f"unzip -q /tmp/g.zip -d /opt && rm /tmp/g.zip && "
                      f"ln -s /opt/gradle-{version}/bin/gradle /usr/local/bin/gradle"))


app = modal.App("daodan-fixture-indexes")
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)
ADAPTERS = {"go": go, "python": python, "java": java, "kotlin": kotlin}


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
        engine = ADAPTERS[language].index(project, work / "engine")
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


@app.function(image=_go_image(), cpu=2, memory=4096, **FUNCTION)
def index_go(sources: dict) -> dict:
    return _index("go", sources)


@app.function(image=_python_image(), cpu=2, memory=4096, **FUNCTION)
def index_python(sources: dict) -> dict:
    return _index("python", sources)


@app.function(image=_java_image(), cpu=2, memory=4096, **FUNCTION)
def index_java(sources: dict) -> dict:
    return _index("java", sources)


@app.function(image=_kotlin_image(), cpu=4, memory=8192, **FUNCTION)
def index_kotlin(sources: dict) -> dict:
    return _index("kotlin", sources)


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
    parser.add_argument("--languages", default="go,python,java,kotlin")
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
