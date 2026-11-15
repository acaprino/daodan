"""`affected` (Rani367/affected) on the corpus of `fixtures/`, on Modal, one container at a time.

It reuses the runner of `modal_native.py` (copies of each fixture with canary lines, strace, three modes: `online`,
`offline_warm`, `offline_cold`; the 18 real repositories come from the clones already on the volume) with its own app
and image: the release binary, Go 1.27.3 and Cargo 1.99.1 (the two toolchains the tool asks). A second run with `PATH`
cut of Go and Cargo (`--bare`) says what it reports without them. `questions` runs the git and per-folder probes.

    modal deploy benchmarks/project-model/modal_affected.py
    python benchmarks/project-model/modal_affected.py spawn [--fixtures a,b] [--bare] [--modes online]
    python benchmarks/project-model/modal_affected.py questions
    python benchmarks/project-model/modal_affected.py fetch [--dir COPY]

The volume keeps `project-model/native/affected[-bare]/<fixture>.json` and `project-model/affected-questions.json`;
`fetch` scores the online output into `results/affected.json`. Run it with the uv tool's interpreter of modal, with
the proxy variables empty (see the Modal notes).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
sys.path[:0] = [str(HERE), "/pm"]  # the drivers are mounted at /pm in the container
import modal_native as native  # noqa: E402  (runner and real-repository store)

APP = "daodan-pm-affected"
VERSION = "1.0.0"
SHA = "0afb13573522bcfb55a802c9e07f8d3f64b67c2d874b1780cbfd4aa0c3b0359b"
URL = f"https://github.com/Rani367/affected/releases/download/v{VERSION}/affected-x86_64-unknown-linux-gnu.tar.gz"
BARE_PATH = "/usr/local/bin:/usr/bin:/bin"
QUESTIONS = "project-model/affected-questions.json"
INSTALL = [
    native.INSTALL_MAIN[0],  # Go 1.27.3
    native.INSTALL_MAIN[3],  # rustup 1.28.2 and Cargo 1.99.1
    f"cd /tmp && curl -fsSLo a.tgz {URL} && echo '{SHA}  a.tgz' | sha256sum -c - && tar -xzf a.tgz affected"
    " && install -m 755 affected /usr/local/bin/affected && rm a.tgz affected && affected --version",
]
ENV = {"PATH": "/opt/go/bin:/opt/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
       "RUSTUP_HOME": "/opt/rustup"}


def _image():
    image = (modal.Image.from_registry("ubuntu:24.04", add_python="3.12")  # the binary needs glibc 2.39
             .apt_install(*native.APT).pip_install(*native.PIP).run_commands(*INSTALL).env(ENV))
    if LOCAL:
        image = image.add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
        image = image.add_local_dir(ROOT / "fixtures", "/pm/fixtures")
        image = image.add_local_file(ROOT / "modal_native.py", "/pm/modal_native.py")
        image = image.add_local_file(ROOT / "modal_affected.py", "/pm/modal_affected.py")
    return image


app = modal.App(APP)
volume = native.volume
OPTIONS = {"image": _image(), "cpu": 1.0, "memory": 2048, "timeout": 2400, "volumes": {"/results": volume}}


def code_sha256() -> str:
    """One hash over the adapter, the shared plumbing and the two drivers, compared with the local one."""
    digest = hashlib.sha256()
    for path in (ROOT / "tools/affected.py", ROOT / "tools/native_common.py", ROOT / "modal_native.py",
                 ROOT / "modal_affected.py"):
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:16]


@app.function(**OPTIONS)
def run_all(fixtures: list | None = None, modes: list | None = None, bare: bool = False, timeout: int = 600) -> dict:
    sys.path[:0] = ["/pm/tools", "/pm"]
    native.code_sha256 = code_sha256  # the records carry this hash
    print("affected code", code_sha256(), flush=True)
    if bare:  # no Go, no Cargo on PATH: what the tool says without them
        return native._run_tool("affected", fixtures, list(modes or ["online"]), False, timeout, "-bare",
                                {"PATH": BARE_PATH})
    return native._run_tool("affected", fixtures, list(modes or ["online", "offline_warm", "offline_cold"]), False, timeout)


MANIFESTS = {"package.json", "Cargo.toml", "go.mod", "go.work", "pyproject.toml", "pom.xml", "build.gradle",
             "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "pubspec.yaml", "Package.swift", "mix.exs",
             "build.sbt", "requirements.txt", "setup.py", "composer.json", "Gemfile", "CMakeLists.txt"}


@app.function(**OPTIONS)
def questions() -> dict:
    """Per-folder runs for the multi-ecosystem repositories, and the git conditions of `list`."""
    import os
    import shutil
    import subprocess
    import time
    sys.path[:0] = ["/pm/tools", "/pm"]
    import affected as adapter
    print("affected code", code_sha256(), flush=True)

    def sh(argv, cwd, env=None):
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=300,
                              env={**os.environ, "HOME": "/tmp/qhome", "GIT_TERMINAL_PROMPT": "0", **(env or {})})
        return {"argv": " ".join(map(str, argv)), "rc": done.returncode, "stdout": done.stdout[-3000:],
                "stderr": done.stderr[-800:]}

    def source(name):
        folder = ROOT / "fixtures" / name
        if (folder / "source.json").is_file():
            return native._real_source(name)
        copy = Path("/work/q") / name
        shutil.rmtree(copy, ignore_errors=True)
        shutil.copytree(folder, copy, symlinks=True, ignore=shutil.ignore_patterns("expected.json", "source.json"))
        return copy

    out = {"help_list": sh(["affected", "list", "--help"], "/tmp"), "version": sh(["affected", "--version"], "/tmp"),
           "folders": {}, "git": {}}
    for name in ("mix-poly-firebase", "real-svc-otel-demo", "real-app-hoppscotch", "real-app-jhipster-sample",
                 "sys-go-nested", "mix-real-chi"):
        base = source(name)
        record = {"root": {"detect": sh(["affected", "--no-color", "--root", base, "detect"], base),
                           "graph": sh(["affected", "--no-color", "--root", base, "graph", "--dot"], base)},
                  "folders": {}}
        for here, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in ("node_modules", "vendor", "target"))
            rel = Path(here).relative_to(base)
            if len(rel.parts) > 3:
                dirs[:] = []
                continue
            if rel.parts and MANIFESTS & set(files):
                one = sh(["affected", "--no-color", "--root", here, "detect"], here)
                record["folders"][rel.as_posix()] = {
                    "manifests": sorted(MANIFESTS & set(files)), "rc": one["rc"],
                    "ecosystem": (adapter.parse_detect(one["stdout"])["ecosystem"] if one["rc"] == 0 else None),
                    "packages": (len(adapter.parse_detect(one["stdout"])["packages"]) if one["rc"] == 0 else None),
                    "stderr": one["stderr"][-200:]}
        out["folders"][name] = record
    # git: a workspace with and without a repository, a base revision and a change
    for case in ("no-repo", "repo-no-commit", "repo-clean", "repo-changed", "bad-base"):
        base = source("js-npm-workspaces")
        shutil.rmtree(base / ".git", ignore_errors=True)
        steps = {}
        if case != "no-repo":
            steps["init"] = sh(["git", "init", "-q"], base)
        if case in ("repo-clean", "repo-changed", "bad-base"):
            sh(["git", "add", "-A"], base)
            steps["commit"] = sh(["git", "-c", "user.email=a@b.c", "-c", "user.name=q", "commit", "-q", "-m", "x"], base)
        if case == "repo-changed":
            target = next(p for p in sorted(base.rglob("*.js")) if "node_modules" not in p.parts)
            target.write_text(target.read_text(encoding="utf-8") + "\n// changed\n", encoding="utf-8")
            steps["changed"] = target.relative_to(base).as_posix()
        flags = ["--base", "nope"] if case == "bad-base" else ["--base", "HEAD"]
        steps["list"] = sh(["affected", "--no-color", "--root", base, "list", *flags, "--json"], base)
        steps["detect"] = sh(["affected", "--no-color", "--root", base, "detect"], base)
        steps["graph"] = sh(["affected", "--no-color", "--root", base, "graph", "--dot"], base)
        out["git"][case] = steps
    target = Path("/results") / QUESTIONS
    target.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    out["code"] = code_sha256()
    out["time"] = time.time()
    return out


# ---------------------------------------------------------------- local: spawn and fetch

def _fetch(local: str | None) -> None:
    import score
    native._fetch(["affected"], local)
    result_file = HERE / "results/affected.json"
    result = json.loads(result_file.read_text(encoding="utf-8"))
    bare = {}
    try:
        for record in native._records("affected-bare", local):
            run = (record.get("runs") or {}).get("online") or {}
            output = run.get("output")
            calls = run.get("calls") or []
            bare[record["fixture"]] = {
                "units": None if output is None else len(output.get("units") or []),
                "error": run.get("adapter_error"),
                "same_as_with_toolchains": output == result["fixtures"].get(record["fixture"], {}).get("output"),
                "rc": [c.get("rc") for c in calls], "stderr": [(c.get("stderr") or "")[-200:] for c in calls
                                                              if c.get("rc") not in (0, None)][:2]}
            expected_file = HERE / "fixtures" / record["fixture"] / "expected.json"
            if isinstance(output, dict) and expected_file.is_file():
                bare[record["fixture"]]["score"] = score.score(json.loads(expected_file.read_text(encoding="utf-8")), output)
    except Exception as exc:  # noqa: BLE001 - no bare run stored
        print("no bare records:", exc)
    fixtures = result.pop("fixtures")
    result["bare"] = bare
    lines = [f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}" for k, v in fixtures.items()]
    head = json.dumps(result, ensure_ascii=False, separators=(",", ":"))[:-1] + ',\n"fixtures": {\n' + ",\n".join(lines) + "\n}}\n"
    json.loads(head)
    result_file.write_text(head, encoding="utf-8", newline="\n")
    print("affected", len(fixtures), "fixtures,", len(bare), "bare")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "hash", "questions"))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--modes", default="")
    parser.add_argument("--bare", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dir")
    args = parser.parse_args()
    if args.command == "hash":
        print(code_sha256())
    elif args.command == "spawn":
        print("local code", code_sha256())
        names = [f.strip() for f in args.fixtures.split(",") if f.strip()] or None
        modes = [m for m in args.modes.split(",") if m] or None
        call = modal.Function.from_name(APP, "run_all").spawn(names, modes, args.bare, args.timeout)
        print("run_all", call.object_id)
    elif args.command == "questions":
        print("local code", code_sha256())
        print("questions", modal.Function.from_name(APP, "questions").spawn().object_id)
    else:
        _fetch(args.dir)
