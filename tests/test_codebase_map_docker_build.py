"""A unit only its Dockerfile builds: its build stage reproduced up to the build, from BuildKit's reading of it.

The facts are the pre-map's (`premap/dockerfile.py`) on the two real Dockerfiles of fixtures/premap/dockerfile:
robot-shop's dispatch (Go files, no go.mod: the stage writes it) and OpenTelemetry Demo's currency (CMake, whose
packages the stage installs with apk and builds from GitHub).
"""
import json
import os
import posixpath
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (str(ROOT / "plugins/codebase-map/skills/map/scripts"), str(ROOT / "tests")):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import docker_build  # noqa: E402
import preparation  # noqa: E402
from test_codebase_map_code_graph import document, occurrence  # noqa: E402
from test_codebase_map_indexers import _tools, sandbox  # noqa: E402,F401

FIXTURES = ROOT / "tests/fixtures/premap/dockerfile"
GO_BUILD, CMAKE_BUILD = r"\bgo\s+(build|install)\b", r"\bcmake\b"


def fact(name, dockerfile, context, args=None):
    stages = json.loads((FIXTURES / name).read_text(encoding="utf-8"))["stages"]
    return {"dockerfile": dockerfile, "context": context, "args": args or {}, "stages": stages}


def project(tmp_path, files):
    """A checkout: a Git work tree whose files are tracked, as the copy carries them (`container.carried`)."""
    folder = tmp_path / "project"
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8")
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        subprocess.run(argv, cwd=folder, check=True, capture_output=True)
    return folder


# Package sources as the images hold them (Modal Sandboxes, 16 November 2026), as `docker_build.SOURCES` prints them.
ALPINE_SOURCES = ("DAODAN-SOURCES /etc/apk/repositories\nhttps://dl-cdn.alpinelinux.org/alpine/v3.24/main\n"
                  "https://dl-cdn.alpinelinux.org/alpine/v3.24/community\n\n")  # alpine:3.24.3
BULLSEYE_SOURCES = (  # golang:1.17
    "DAODAN-SOURCES /etc/apt/sources.list\n"
    "# deb http://snapshot.debian.org/archive/debian/20220711T000000Z bullseye main\n"
    "deb http://deb.debian.org/debian bullseye main\n"
    "# deb http://snapshot.debian.org/archive/debian-security/20220711T000000Z bullseye-security main\n"
    "deb http://deb.debian.org/debian-security bullseye-security main\n"
    "# deb http://snapshot.debian.org/archive/debian/20220711T000000Z bullseye-updates main\n"
    "deb http://deb.debian.org/debian bullseye-updates main\n\n")
TRIXIE_SOURCES = (  # debian:13
    "DAODAN-SOURCES /etc/apt/sources.list.d/debian.sources\nTypes: deb\n"
    "# http://snapshot.debian.org/archive/debian/20261104T212339Z\nURIs: http://deb.debian.org/debian\n"
    "Suites: trixie trixie-updates\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.pgp\n\n"
    "Types: deb\n# http://snapshot.debian.org/archive/debian-security/20261104T212339Z\n"
    "URIs: http://deb.debian.org/debian-security\nSuites: trixie-security\nComponents: main\n"
    "Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp\n\n")


def probed(command, out_dir, sources=""):
    """The run that reads the base image's package sources (`docker_build.sourced`), `sources` its output; None
    for any other run."""
    if docker_build.SOURCES_MARK not in " ".join(command):
        return None
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "execute.log").write_text(sources, encoding="utf-8")
    return {"state": "done", "exit_code": 0, "outputs": []}


def pin(image, timeout=60):
    """`docker_build.pinned` without a registry: a reference by digest stays as it is."""
    return image if "@sha256:" in image else f"docker.io/library/{image}@sha256:{'c' * 64}"


def run(lines, tmp_path, work, programs):
    """The plan's lines in a shell, `root` standing for the container's filesystem."""
    for name, body in programs.items():
        (tmp_path / "bin").mkdir(exist_ok=True)
        (tmp_path / "bin" / name).write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
        (tmp_path / "bin" / name).chmod(0o755)
    return subprocess.run(["sh", "-c", "\n".join(lines)], capture_output=True, text=True, timeout=60, cwd=work,
                          env={**os.environ, "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
                               "CALLS": str(tmp_path / "calls")})


def test_dispatch_runs_its_stage_up_to_the_go_install_that_builds_it(tmp_path):
    """robot-shop's dispatch: WORKDIR /go/src/app, COPY *.go ., RUN go mod init dispatch && go get, RUN go install.
    The steps up to the last RUN, which runs the go command's build, are the preparation; the analyzer runs where
    that RUN would, and each file it reads maps back to the checkout through the COPY."""
    work = project(tmp_path, {"dispatch/main.go": "package main\n", "dispatch/queue.go": "package main\n",
                              "dispatch/Dockerfile": "", "dispatch/README.md": "", "web/x.go": "package web\n"})
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    root = tmp_path / "root"
    plan = docker_build.plan(build, work, ["dispatch/main.go"], GO_BUILD, work=str(work), root=str(root))
    assert not plan["gaps"]
    assert plan["image"] == "golang:1.17" and plan["stage"] == "0" and plan["workdir"] == "/go/src/app"
    assert plan["ran"] == [3, 5, 7] and plan["build"] == {"line": 8, "original": "RUN go install",
                                                          "argv": ["/bin/sh", "-c", "go install"]}
    assert plan["copies"] == {"/go/src/app/main.go": "dispatch/main.go", "/go/src/app/queue.go": "dispatch/queue.go"}
    assert plan["hosts"] == []
    done = run(plan["lines"], tmp_path, work, {"go": 'echo "go $* in $(pwd)" >> "$CALLS"\n'
                                                     '[ "$1 $2" = "mod init" ] && echo "module $3" > go.mod\nexit 0\n'})
    assert done.returncode == 0, done.stderr
    app = root / "go/src/app"
    assert sorted(path.name for path in app.iterdir()) == ["go.mod", "main.go", "queue.go"]
    assert (tmp_path / "calls").read_text(encoding="utf-8").splitlines() == [
        f"go mod init dispatch in {app}", f"go get in {app}"]
    assert docker_build.origin(plan, "/go/src/app/main.go") == "dispatch/main.go"
    assert docker_build.origin(plan, "/go/src/app/go.mod") is None
    assert docker_build.provenance(plan) == {"dockerfile": "dispatch/Dockerfile", "stage": "0", "ran": [3, 5, 7],
                                             "build": 8}


def test_currency_runs_base_then_builder_with_compose_s_argument_and_maps_each_copy_back(tmp_path):
    """OpenTelemetry Demo's currency: `builder` starts FROM `base` (apk add grpc-dev protobuf-dev), adds the
    compiler and builds opentelemetry-cpp at the version Compose gives, then copies the unit's folders and the
    repository's pb/demo.proto. Its last RUN is the CMake build."""
    work = project(tmp_path, CURRENCY_FILES)
    build = fact("otel-demo-currency.json", "src/currency/Dockerfile", ".", {"OPENTELEMETRY_CPP_VERSION": "1.28.0"})
    root = tmp_path / "root"
    plan = docker_build.plan(build, work, ["src/currency/src/main.cpp"], CMAKE_BUILD, work=str(work),
                             root=str(root))
    assert not plan["gaps"] and plan["stage"] == "builder" and plan["workdir"] == "/currency"
    assert plan["image"].startswith("docker.io/library/alpine:3.24.3@sha256:")
    assert plan["ran"] == [19, 24, 26, 28, 38, 40, 41, 42, 44, 45, 47] and plan["build"]["line"] == 49
    assert plan["hosts"] == ["github.com"]
    assert plan["copies"]["/currency/src/main.cpp"] == "src/currency/src/main.cpp"
    assert plan["copies"]["/currency/proto/demo.proto"] == "pb/demo.proto"
    assert plan["copies"]["/currency/CMakeLists.txt"] == "src/currency/CMakeLists.txt"
    # The build, which an analyzer runs where it would: in the stage's shell, with the stage's ARG values, as
    # BuildKit gives a RUN its arguments.
    assert plan["build"]["argv"] == ["/bin/sh", "-c", "mkdir -p build && cd build     && cmake ..     && make "
                                     "-j$(nproc || sysctl -n hw.ncpu || echo 1) install"]
    assert ["OPENTELEMETRY_CPP_VERSION", "1.28.0"] in plan["env"]
    done = run(plan["lines"], tmp_path, work, {
        "apk": 'echo "apk $*" >> "$CALLS"\n',
        "git": 'echo "git $* ver=$OPENTELEMETRY_CPP_VERSION" >> "$CALLS"\nmkdir -p opentelemetry-cpp\n',
        "cmake": 'echo "cmake in $(pwd)" >> "$CALLS"\n', "make": 'echo "make $*" >> "$CALLS"\n',
        "nproc": "echo 2\n"})
    assert done.returncode == 0, done.stderr
    calls = (tmp_path / "calls").read_text(encoding="utf-8").splitlines()
    assert calls[:4] == ["apk update", "apk add grpc-dev protobuf-dev", "apk add git cmake make g++ linux-headers",
                         "git clone --depth 1 --branch v1.28.0 https://github.com/open-telemetry/opentelemetry-cpp "
                         "ver=1.28.0"]
    assert (root / "currency/src/main.cpp").is_file() and (root / "currency/proto/demo.proto").is_file()
    assert (root / "currency/genproto/CMakeLists.txt").is_file()


GIT = 'echo "git $*" >> "$CALLS"\nmkdir -p opentelemetry-cpp\n'


def test_a_value_of_a_tracked_env_file_reaches_the_stage_only_in_its_container(tmp_path, monkeypatch):
    """otel-demo as it is: Compose gives OPENTELEMETRY_CPP_VERSION from the tracked .env, so the fact keeps
    `${OPENTELEMETRY_CPP_VERSION}` and its file (`premap/dockerfile.py`). The plan exports the ARG from that
    variable, which the run asks the container to set from the copy's .env (`dotenv_env`): the value is in the
    preparation's environment only, never in the plan or on record. The execution's ENV leaves it out."""
    work = project(tmp_path, {**CURRENCY_FILES, ".env": "OPENTELEMETRY_CPP_VERSION=1.28.0\n"})
    build = {**fact("otel-demo-currency.json", "src/currency/Dockerfile", ".",
                    {"OPENTELEMETRY_CPP_VERSION": "${OPENTELEMETRY_CPP_VERSION}"}),
             "dotenv": {"OPENTELEMETRY_CPP_VERSION": ".env"}}
    for item in (item for stage_ in build["stages"] for item in stage_["commands"]):  # as BuildKit expands them
        if "cmd" in item:
            item["cmd"] = [word.replace("1.28.0", "${OPENTELEMETRY_CPP_VERSION}") for word in item["cmd"]]
        for args in item.get("args") or ():
            args.update({key: "${OPENTELEMETRY_CPP_VERSION}" for key, value in args.items() if value == "1.28.0"})
    root = tmp_path / "root"
    plan = docker_build.plan(build, work, ["src/currency/src/main.cpp"], CMAKE_BUILD, work=str(work), root=str(root))
    assert not plan["gaps"] and "1.28.0" not in json.dumps(plan)
    assert 'export OPENTELEMETRY_CPP_VERSION="${OPENTELEMETRY_CPP_VERSION}"' in plan["lines"]
    assert ["OPENTELEMETRY_CPP_VERSION", "${OPENTELEMETRY_CPP_VERSION}"] not in plan["env"]
    done = subprocess.run(["sh", "-c", "\n".join(plan["lines"])], capture_output=True, text=True, timeout=60, cwd=work,
                          env={**os.environ, "OPENTELEMETRY_CPP_VERSION": "1.28.0", "CALLS": str(tmp_path / "calls"),
                               "PATH": f"{bin_with(tmp_path, {**BUILDING, 'git': GIT})}:{os.environ['PATH']}"})
    assert done.returncode == 0, done.stderr
    assert "--branch v1.28.0 " in (tmp_path / "calls").read_text(encoding="utf-8")
    calls = []
    monkeypatch.setattr(docker_build, "pinned", pin)
    monkeypatch.setattr(container, "run_in_container", lambda *args, **options: calls.append(options) or {})
    docker_build.run(work, tmp_path / "out", plan, ["true"])
    assert calls[0]["dotenv_env"] == [("OPENTELEMETRY_CPP_VERSION", ".env")]


def test_each_instruction_it_cannot_reproduce_is_a_gap_naming_its_line(tmp_path):
    """A build argument with no value, a secret, a copy from another image, a source outside the context, another
    user: the stage is not run, and each says where."""
    work = project(tmp_path, {"app/main.go": "package main\n", "shared/x.txt": ""})
    unset = fact("otel-demo-currency-no-args.json", "src/currency/Dockerfile", ".")
    plan = docker_build.plan(unset, work, ["src/currency/src/main.cpp"], CMAKE_BUILD)
    assert plan is None  # no stage copies that file in
    work = project(tmp_path, {"src/currency/src/main.cpp": "", "src/currency/CMakeLists.txt": "",
                              "src/currency/genproto/CMakeLists.txt": "", "src/currency/build/.keep": "",
                              "src/currency/proto/.keep": "", "pb/demo.proto": ""})
    plan = docker_build.plan(unset, work, ["src/currency/src/main.cpp"], CMAKE_BUILD)
    assert [(g["kind"], g["path"]) for g in plan["gaps"]] == [("not_reproduced", "src/currency/Dockerfile:26")]
    assert "OPENTELEMETRY_CPP_VERSION" in plan["gaps"][0]["detail"] and not plan["lines"]

    def command(kind, line, **fields):
        return {"kind": kind, "line": line, "end_line": line, "original": f"{kind} ...", **fields}

    stages = [{"name": "", "base": "golang:1.22", "base_stage": None, "line": 1, "commands": [
        command("WORKDIR", 2, path="/app"),
        command("COPY", 3, sources=["main.go"], dest="."),
        command("RUN", 4, cmd=["go mod download"], shell=True, mounts=[{"type": "secret", "target": "/run/s"}]),
        command("COPY", 5, sources=["/bin/tool"], dest="/usr/bin/tool", **{"from": "tools:1"}),
        command("COPY", 6, sources=["../shared/x.txt"], dest="x.txt"),
        command("USER", 7, user="app"),
        command("WORKDIR", 8, path="$GOPATH/src", unmatched=["GOPATH"]),
        command("RUN", 9, cmd=["go build -o /out ."], shell=True)]}]
    plan = docker_build.plan({"dockerfile": "app/Dockerfile", "context": "app", "args": {}, "stages": stages},
                             work, ["app/main.go"], GO_BUILD)
    assert [g["path"] for g in plan["gaps"]] == [f"app/Dockerfile:{n}" for n in (4, 5, 6, 7, 8)]
    stages[0]["commands"][-1] = command("RUN", 9, cmd=["echo done"], shell=True)
    plan = docker_build.plan({"dockerfile": "app/Dockerfile", "context": "app", "args": {}, "stages": stages},
                             work, ["app/main.go"], GO_BUILD)
    assert plan["gaps"][-1]["path"] == "app/Dockerfile:9" and "does not run" in plan["gaps"][-1]["detail"]


def test_the_base_image_is_named_by_the_digest_its_registry_gives(monkeypatch):
    """The registry's own answer (the OCI distribution API: a manifest HEAD, after the anonymous token Docker Hub
    asks for): the image runs by that digest, whatever the tag names later. One named by its digest is kept."""
    import io
    import urllib.error
    asked = []

    class Answer(io.BytesIO):
        def __init__(self, body=b"", headers=None):
            super().__init__(body)
            self.headers = headers or {}

    def urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else request
        asked.append((getattr(request, "method", "GET"), url, dict(getattr(request, "headers", {}))))
        if url.startswith("https://auth.docker.io/token"):
            return Answer(b'{"token": "t0"}')
        if "Authorization" not in getattr(request, "headers", {}):
            raise urllib.error.HTTPError(url, 401, "Unauthorized", {
                "WWW-Authenticate": 'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",'
                                    'scope="repository:library/golang:pull"'}, None)
        return Answer(headers={"Docker-Content-Digest": "sha256:" + "a" * 64})

    monkeypatch.setattr(docker_build.urllib.request, "urlopen", urlopen)
    assert docker_build.pinned("golang:1.17") == "docker.io/library/golang:1.17@sha256:" + "a" * 64
    assert [(method, url.split("?")[0]) for method, url, _ in asked] == [
        ("HEAD", "https://registry-1.docker.io/v2/library/golang/manifests/1.17"),
        ("GET", "https://auth.docker.io/token"),
        ("HEAD", "https://registry-1.docker.io/v2/library/golang/manifests/1.17")]
    assert "scope=repository%3Alibrary%2Fgolang%3Apull" in asked[1][1]
    assert "application/vnd.oci.image.index.v1+json" in asked[0][2]["Accept"]
    kept = "docker.io/library/alpine:3.24.3@sha256:" + "b" * 64
    assert docker_build.pinned(kept) == kept


CURRENCY_FILES = {"src/currency/src/main.cpp": "int main(){}\n", "src/currency/CMakeLists.txt": "",
                  "src/currency/genproto/CMakeLists.txt": "", "src/currency/build/.keep": "",
                  "src/currency/proto/.keep": "", "pb/demo.proto": "", "src/currency/Dockerfile": ""}
BUILDING = {"apk": "", "git": "mkdir -p opentelemetry-cpp\n", "cmake": "", "make": "", "nproc": "echo 2\n"}


def stage(*commands, base="debian:13"):
    """A build fact of one stage on `base`, its instructions as BuildKit reads them, one per line from line 3."""
    items = []
    for line, (kind, original, more) in enumerate(commands, start=3):
        items.append({"kind": kind, "line": line, "end_line": line, "original": original, **more})
    return {"dockerfile": "Dockerfile", "context": ".", "args": {},
            "stages": [{"name": "", "base": base, "base_stage": None, "line": 1, "commands": items}]}


def shell(original):
    return "RUN", original, {"cmd": [original[len("RUN "):]], "shell": True, "network": "default",
                             "security": "sandbox"}


def copy(original, sources, dest):
    return "COPY", original, {"sources": sources, "dest": dest}


APT_STAGE = stage(shell("RUN apt-get update && apt-get install -y cmake g++"),
                  ("WORKDIR", "WORKDIR /src", {"path": "/src"}), copy("COPY . .", ["."], "."),
                  shell("RUN cmake -S . -B build && cmake --build build"))


def test_the_base_image_s_own_package_sources_are_hosts_of_its_stage(tmp_path, monkeypatch):
    """currency's `builder` runs `apk update && apk add ...` on alpine:3.24.3, whose apk reads the repositories
    /etc/apk/repositories names: read from the pinned image itself with no network, their hosts are opened in the
    preparation beside those the RUN lines name. apk-tools 3.0.8 reaches them through Daodan's proxy (Modal,
    16 November 2026: jq installed with dl-cdn.alpinelinux.org allowed, `HTTP 403: Forbidden` without it)."""
    work = project(tmp_path, CURRENCY_FILES)
    build = fact("otel-demo-currency.json", "src/currency/Dockerfile", ".", {"OPENTELEMETRY_CPP_VERSION": "1.28.0"})
    calls = []

    def run_in_container(project_dir, command, *, image, out_dir, **options):
        calls.append({"image": image, "command": command, **options})
        return probed(command, out_dir, ALPINE_SOURCES)

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", pin)
    plan = docker_build.plan(build, work, ["src/currency/src/main.cpp"], CMAKE_BUILD)
    plan = docker_build.sourced(plan, tmp_path / "sources")
    [call] = calls
    assert call["image"] == plan["image"] == build["stages"][0]["base"]  # named by its digest already
    assert "prepare" not in call and "/etc/apk/repositories" in call["command"][-1]
    assert "/etc/apt/sources.list.d/*" in call["command"][-1]
    assert plan["hosts"] == ["dl-cdn.alpinelinux.org", "github.com"] and not plan["gaps"] and plan["lines"]


def test_apt_s_plain_http_archives_are_opened_for_its_paths_and_apk_s_are_a_gap(tmp_path, monkeypatch):
    """Debian's and Ubuntu's images name their archives over plain HTTP (golang:1.17, golang:1.23, debian:13,
    ubuntu:24.04). apt verifies the signed Release files and each package's hash, so the preparation's proxy opens
    an `http://<host>` entry for apt's archive paths only (`container.PROXY_SCRIPT`): a stage whose step runs apt
    there gets those entries among its hosts. apk over plain HTTP stays a gap naming the sources. A stage that
    runs no apt leaves them unused: dispatch, on golang:1.17."""
    monkeypatch.setattr(docker_build, "pinned", pin)
    plain_apk = "DAODAN-SOURCES /etc/apk/repositories\nhttp://dl-cdn.alpinelinux.org/alpine/v3.24/main\n\n"
    answers = iter([TRIXIE_SOURCES, plain_apk, BULLSEYE_SOURCES])
    monkeypatch.setattr(container, "run_in_container",
                        lambda project_dir, command, *, image, out_dir, **options: probed(command, out_dir,
                                                                                        next(answers)))
    work = project(tmp_path, {"CMakeLists.txt": "project(app CXX)\n", "main.cpp": "int main() {}\n"})
    plan = docker_build.sourced(docker_build.plan(APT_STAGE, work, ["main.cpp"], CMAKE_BUILD), tmp_path / "sources")
    assert not plan["gaps"] and plan["lines"] and plan["hosts"] == ["http://deb.debian.org"]
    apk = stage(shell("RUN apk add cmake g++"), ("WORKDIR", "WORKDIR /src", {"path": "/src"}),
                copy("COPY . .", ["."], "."), shell("RUN cmake -S . -B build && cmake --build build"),
                base="alpine:3.24.3")
    plan = docker_build.sourced(docker_build.plan(apk, work, ["main.cpp"], CMAKE_BUILD), tmp_path / "apk")
    assert plan["lines"] == [] and plan["gaps"] == [{"kind": "not_reproduced", "path": "Dockerfile:3", "detail": (
        "RUN apk add cmake g++: apk reads http://dl-cdn.alpinelinux.org/alpine/v3.24/main (/etc/apk/repositories of "
        f"docker.io/library/alpine:3.24.3@sha256:{'c' * 64}), plain HTTP, which the preparation opens for apt's "
        "archives only")}]
    work = project(tmp_path / "robot-shop", {"dispatch/main.go": "package main\n", "dispatch/Dockerfile": ""})
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    plan = docker_build.sourced(docker_build.plan(build, work, ["dispatch/main.go"], GO_BUILD), tmp_path / "go")
    assert not plan["gaps"] and plan["lines"] and plan["hosts"] == []


def test_the_build_context_is_what_the_copy_carries_less_what_its_dockerignore_leaves_out(tmp_path):
    """BuildKit sends the context less what .dockerignore leaves out (the pre-map's `excluded`, a folder ending in
    /); Daodan's copy carries what Git tracks (a tracked .env too) and what the snapshot reads, never a file
    Daodan never reads that Git does not track (an untracked .env.local). A folder COPY brings what the copy
    carries; a COPY of a file .dockerignore leaves out fails in BuildKit and is a gap here, as is one of a file the
    copy does not carry."""
    work = project(tmp_path, {**CURRENCY_FILES, "src/currency/src/tracer_common.h": "", "src/currency/src/.env": "A=1\n"})
    (work / "src/currency/src/.env.local").write_text("B=2\n", encoding="utf-8")  # untracked
    build = {**fact("otel-demo-currency.json", "src/currency/Dockerfile", ".", {"OPENTELEMETRY_CPP_VERSION": "1.28.0"}),
             "dockerignore": ".dockerignore", "excluded": ["src/currency/README.md", "src/currency/src/tracer_common.h"]}
    root = tmp_path / "root"
    plan = docker_build.plan(build, work, ["src/currency/src/main.cpp"], CMAKE_BUILD, work=str(work), root=str(root))
    assert not plan["gaps"] and plan["copies"]["/currency/src/main.cpp"] == "src/currency/src/main.cpp"
    assert "/currency/src/tracer_common.h" not in plan["copies"] and "/currency/src/.env.local" not in plan["copies"]
    assert plan["copies"]["/currency/src/.env"] == "src/currency/src/.env"
    done = run(plan["lines"], tmp_path, work, BUILDING)
    assert done.returncode == 0, done.stderr
    assert (root / "currency/src/main.cpp").is_file() and not (root / "currency/src/tracer_common.h").exists()
    ignored = {**build, "excluded": ["src/currency/CMakeLists.txt"]}
    assert docker_build.plan(ignored, work, ["src/currency/src/main.cpp"], CMAKE_BUILD)["gaps"] == [
        {"kind": "not_reproduced", "path": "src/currency/Dockerfile:45", "detail":
         "COPY ./src/currency/CMakeLists.txt CMakeLists.txt: ./src/currency/CMakeLists.txt: .dockerignore leaves it "
         "out of the build context ."}]
    secret = stage(copy("COPY src/currency/src/.env.local ./", ["src/currency/src/.env.local"], "./"),
                   copy("COPY src/currency/src/ ./", ["src/currency/src/"], "./"), shell("RUN cmake ."))
    assert docker_build.plan(secret, work, ["src/currency/src/main.cpp"], CMAKE_BUILD)["gaps"] == [
        {"kind": "not_reproduced", "path": "Dockerfile:3", "detail":
         "COPY src/currency/src/.env.local ./: src/currency/src/.env.local: not in Daodan's copy of the checkout (a "
         "file it never reads, or one Git does not track in a folder the snapshot leaves out)"}]


def test_on_the_host_only_git_lists_the_checkout_and_no_project_file_or_run_instruction_runs(tmp_path, monkeypatch):
    """AGENTS.md: the analyzed project's code runs only in Daodan's container. On the host the Go and the C and C++
    routes read the pre-map's facts and the checkout (Git lists what the copy carries: `container.carried`); a RUN
    instruction and the build reach only the scripts the engine runs in the container (`prepare`, the command).
    Each file here leaves a mark where it runs: a RUN instruction, the script the build runs, CMake's configure,
    `go generate`, and the core.fsmonitor hook of the checkout's Git, which Git runs where it reads the index."""
    from indexers import clang, go
    marks = tmp_path / "marks"
    marks.mkdir()
    work = project(tmp_path, {"CMakeLists.txt": f"execute_process(COMMAND touch {marks}/cmake)\nproject(app CXX)\n",
                              "main.cpp": "int main() {}\n",
                              "main.go": f"package main\n\n//go:generate touch {marks}/go-generate\nfunc main() {{}}\n",
                              "build.sh": f"#!/bin/sh\ntouch {marks}/build-sh\n",
                              "tools/fsmonitor.sh": f"#!/bin/sh\ntouch {marks}/fsmonitor\n"})
    for rel in ("build.sh", "tools/fsmonitor.sh"):
        (work / rel).chmod(0o755)
    subprocess.run(["git", "config", "core.fsmonitor", str(work / "tools/fsmonitor.sh")], cwd=work, check=True)
    marked = (shell(f"RUN touch {marks}/run-instruction"), ("WORKDIR", "WORKDIR /src", {"path": "/src"}),
              copy("COPY . .", ["."], "."))
    go_build = stage(*marked, shell("RUN ./build.sh && go generate ./... && go install"))
    cmake_build = stage(*marked, shell("RUN ./build.sh && cmake -S . -B build && cmake --build build"))
    calls, started, real = [], [], subprocess.Popen

    class Started(real):  # every process the routes start on the host
        def __init__(self, args, *more, **options):
            started.append([str(part) for part in ([args] if isinstance(args, (str, Path)) else args)])
            super().__init__(args, *more, **options)

    def run_in_container(project_dir, command, *, image, out_dir, prepare=None, **options):  # runs nothing
        calls.append({"image": image, "command": command, "prepare": prepare})
        return probed(command, out_dir, ALPINE_SOURCES) or {"state": "done", "exit_code": 0, "outputs": []}

    monkeypatch.setattr(subprocess, "Popen", Started)
    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", pin)
    go._docker(work, tmp_path / "go", ["main.go"], set(), [go_build])
    clang._docker(work, tmp_path / "clang", ["."], {"units": [{"root": ".", "state": "failed", "cause": "here"}]},
                  [cmake_build], memory=2**30, cpus=1, engine=None, timeout=60)
    assert sorted(path.name for path in marks.iterdir()) == []
    assert started and all(Path(argv[0]).name in ("git", "git.exe") for argv in started), started
    prepared = [call["prepare"][-1] for call in calls if call["prepare"]]
    assert len(prepared) == 2 and all(f"touch {marks}/run-instruction" in script for script in prepared)
    assert any("./build.sh && cmake -S . -B build" in call["command"][-1] for call in calls if call["prepare"])


def deb(path: Path, members: dict[str, bytes | str]) -> Path:
    """A Debian package as dpkg writes one: an ar archive whose data.tar.xz holds `members` (bytes: a file; str:
    a symbolic link to it)."""
    import io
    import tarfile
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:xz") as bundle:
        for name, value in members.items():
            entry = tarfile.TarInfo(f"./{name}")
            if isinstance(value, str):
                entry.type, entry.linkname = tarfile.SYMTYPE, value
                bundle.addfile(entry)
            else:
                entry.size, entry.mode = len(value), 0o755
                bundle.addfile(entry, io.BytesIO(value))
    out = bytearray(b"!<arch>\n")
    for name, body in (("debian-binary", b"2.0\n"), ("control.tar.xz", b""), ("data.tar.xz", data.getvalue())):
        out += f"{name:<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(body):<10}`\n".encode() + body
        out += b"\n" if len(body) % 2 else b""
    path.write_bytes(bytes(out))
    return path


def test_glibc_s_libraries_are_carried_where_only_its_loader_looks(tmp_path, monkeypatch):
    """scip-clang is a glibc program and currency's stage is Alpine's musl: Debian's glibc and GCC runtime,
    each package checked by its sha256, give one tar to unpack at `/` there: the libraries in the multiarch folder
    Alpine does not use, the loader at /lib64 where a glibc program names it. Proved on alpine:3.24.3 (Modal,
    16 November 2026): scip-clang runs, and so do Alpine's own programs."""
    import preparation as prep
    import tarfile
    packages = {
        "libc6.deb": {"usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2": b"loader",
                      "usr/lib/x86_64-linux-gnu/libc.so.6": b"libc", "usr/lib64/ld-linux-x86-64.so.2":
                      "../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2", "usr/share/doc/libc6/copyright": b"GPL"},
        "libstdc++6.deb": {"usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33": b"cxx",
                           "usr/lib/x86_64-linux-gnu/libstdc++.so.6": "libstdc++.so.6.0.33"},
        "libgcc-s1.deb": {"usr/lib/x86_64-linux-gnu/libgcc_s.so.1": b"gcc"}}
    asked = []
    monkeypatch.setattr(prep, "fetched", lambda url, digest, name: (asked.append((url, digest, name)),
                                                                     deb(tmp_path / name, packages[name]))[1])
    bundle = docker_build.glibc(tmp_path / "glibc.tar")
    assert [name for _url, _digest, name in asked] == [name for _url, _digest, name in docker_build.GLIBC]
    assert all(len(digest) == 64 for _url, digest, _name in asked)
    with tarfile.open(bundle) as tar:
        members = {m.name: m for m in tar.getmembers()}
        assert tar.extractfile("lib64/ld-linux-x86-64.so.2").read() == b"loader"
    assert sorted(members) == ["lib64/ld-linux-x86-64.so.2", "usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",
                               "usr/lib/x86_64-linux-gnu/libc.so.6", "usr/lib/x86_64-linux-gnu/libgcc_s.so.1",
                               "usr/lib/x86_64-linux-gnu/libstdc++.so.6",
                               "usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33"]
    assert members["usr/lib/x86_64-linux-gnu/libstdc++.so.6"].linkname == "libstdc++.so.6.0.33"


def test_the_command_runs_with_the_stage_s_environment_where_the_build_runs(tmp_path):
    """An execution starts from the image's own configuration: the stage's ENV and the build's folder are set
    again around the analyzer's command."""
    plan = {"env": [["GOPATH", "/go"], ["NOTE", "it's here"]], "workdir": str(tmp_path)}
    argv = docker_build.command(plan, ["sh", "-c", 'echo "$GOPATH|$NOTE|$(pwd)"'])
    done = subprocess.run(argv, capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
    assert done.stdout == f"/go|it's here|{tmp_path}\n"


def test_an_index_of_the_stage_names_the_checkout_s_files_and_drops_what_the_steps_wrote(tmp_path):
    """scip-go's documents are relative to where it runs (the build's folder); each becomes the checkout's file
    the COPY brought there, its occurrences and the index's other fields as they were."""
    plan = {"workdir": "/go/src/app", "copies": {"/go/src/app/main.go": "dispatch/main.go"}}
    source = tmp_path / "in.scip"
    metadata = b"\x0a\x04meta"  # field 1, the index's metadata, kept as it is
    source.write_bytes(metadata + document("main.go", [occurrence(3, 5, 6, "s main/F().", definition=True)])
                       + document("go.mod", []))
    out = tmp_path / "out.scip"
    assert docker_build.rewritten(source, plan, out) == 1
    index = code_graph.Index(tmp_path)
    index.load(out, "")
    assert sorted(index.documents) == ["dispatch/main.go"] and out.read_bytes().startswith(metadata)
    assert [o.key for o in index.documents["dispatch/main.go"]] == ["s main/F()."]


# ------------------------------------------------------------------ scip-go in the stage

def dispatch(sandbox):
    project = sandbox["root"] / "project"
    for rel in ("dispatch/main.go", "dispatch/queue.go"):
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text("package main\n", encoding="utf-8")
    (project / "dispatch/Dockerfile").write_text("FROM golang:1.17\n", encoding="utf-8")
    _tools(project, "go")
    return project


def test_go_files_no_module_holds_are_indexed_in_the_stage_their_dockerfile_builds(sandbox, monkeypatch):
    """dispatch: no go.mod in the checkout, the stage writes it. The preparation runs the stage's steps up to its
    `go install`, then builds scip-go with Daodan's Go; scip-go runs offline where the build would, and its
    documents name the checkout's files; go.mod, which the steps wrote, has none."""
    from indexers import go
    calls = []

    def run_in_container(project_dir, command, *, image, out_dir, prepare=None, outputs=(), registries=(),
                         inputs=None, **options):
        if (answer := probed(command, out_dir, BULLSEYE_SOURCES)) is not None:
            return answer
        calls.append({"image": image, "command": command, "prepare": prepare, "outputs": outputs,
                      "registries": registries, "inputs": inputs, **options})
        out = Path(out_dir) / "out"
        (out / "resolved").mkdir(parents=True)
        (out / "index.scip").write_bytes(document("main.go", []) + document("queue.go", []) + document("go.mod", []))
        (out / "resolved/go.mod").write_text("module dispatch\n\ngo 1.17\n\nrequire github.com/streadway/amqp "
                                             "v1.0.0\n", encoding="utf-8")
        (out / "resolved/go.sum").write_text("github.com/streadway/amqp v1.0.0 h1:x=\n", encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": ["/daodan/out"]}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", pin)
    project = dispatch(sandbox)
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    result = go.index(project, sandbox["root"] / "work", roots=set(), docker=[build])
    [call] = calls
    assert call["image"] == f"docker.io/library/golang:1.17@sha256:{'c' * 64}"
    script = call["prepare"][-1]
    assert "exec /bin/sh -c 'go mod init dispatch && go get'" in script and "'go install'" not in script
    assert f"go install github.com/scip-code/scip-go/cmd/scip-go@{go.VERSION}" in script
    assert script.index(f"mkdir -p {preparation.T}/bin") < script.index("go.tar.gz")  # tar unpacks into it
    assert call["command"][-4:] == ["GOPROXY=off", f"{preparation.T}/bin/scip-go", "--output=/daodan/out/index.scip",
                                    "./..."]
    assert "cd /go/src/app" in call["command"][2] and call["outputs"] == ["/daodan/out"]
    assert "proxy.golang.org" in call["registries"] and callable(call["inputs"])
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == ["dispatch/main.go", "dispatch/queue.go"]
    [run] = [run for run in result["runs"] if run.get("docker")]
    assert run["docker"] == {"dockerfile": "dispatch/Dockerfile", "stage": "0", "ran": [3, 5, 7], "build": 8}
    # `go get` resolves at run time: the run states what the index was built against.
    assert "cp go.mod go.sum /daodan/out/resolved/" in script
    assert run["resolved"] == {"go.mod": "module dispatch\n\ngo 1.17\n\nrequire github.com/streadway/amqp v1.0.0\n",
                               "go.sum": "github.com/streadway/amqp v1.0.0 h1:x=\n"}
    assert go.missing(index, ["dispatch/main.go"], go.tasks(result["configs"])) == {}


def test_a_step_that_fails_in_the_preparation_names_its_line_and_the_host_it_could_not_reach(sandbox, monkeypatch):
    """The stage's network is the preparation's, through the registries and the hosts its RUN lines name: a step
    that fails is a `restore_failed` gap naming the Dockerfile's line with the tool's first error, the reason of
    the files it would have built, and a host it says it could not reach is `host_unreachable`."""
    from indexers import go

    def run_in_container(project_dir, command, *, out_dir, **options):
        if (answer := probed(command, out_dir, BULLSEYE_SOURCES)) is not None:
            return answer
        Path(out_dir).mkdir(parents=True)
        (Path(out_dir) / "prepare.log").write_text(
            "go: creating new go.mod: module dispatch\ngo: finding module for package github.com/streadway/amqp\n"
            "dispatch imports\n\tgithub.com/streadway/amqp: cannot find module providing package "
            "github.com/streadway/amqp: dial tcp: lookup proxy.golang.org: no such host\n"
            "DAODAN-DOCKERFILE-FAILED dispatch/Dockerfile:7\n", encoding="utf-8")
        return {"state": "failed", "exit_code": None, "outputs": [], "cause": "preparation exited with code 1"}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", pin)
    project = dispatch(sandbox)
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    result = go.index(project, sandbox["root"] / "work", roots=set(), docker=[build])
    reasons = go.missing(code_graph.Index(project), ["dispatch/main.go"], go.tasks(result["configs"]))
    assert reasons["dispatch/main.go"] == (
        "no Go module holds it: dispatch/Dockerfile:7 `RUN go mod init dispatch && go get` failed: "
        "\tgithub.com/streadway/amqp: cannot find module providing package github.com/streadway/amqp: dial tcp: "
        "lookup proxy.golang.org: no such host")
    [failed] = [g for g in result["gaps"] if g["kind"] == "restore_failed"]
    assert failed["path"] == "dispatch/Dockerfile:7"
    [unreached] = [g for g in result["gaps"] if g["kind"] == "host_unreachable"]
    assert unreached["host"] == "proxy.golang.org" and unreached["declared_in"] == ["dispatch/Dockerfile"]


def test_a_preparation_that_stops_after_the_stage_s_steps_says_its_last_line(sandbox, monkeypatch):
    from indexers import go

    def run_in_container(project_dir, command, *, out_dir, **options):
        if (answer := probed(command, out_dir, BULLSEYE_SOURCES)) is not None:
            return answer
        Path(out_dir).mkdir(parents=True)
        (Path(out_dir) / "prepare.log").write_text("go: creating new go.mod: module dispatch\n"
                                                   "tar: /daodan/state/tools: Cannot open: No such file or directory\n",
                                                   encoding="utf-8")
        return {"state": "failed", "exit_code": None, "outputs": [], "cause": "preparation exited with code 2"}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", pin)
    project = dispatch(sandbox)
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    result = go.index(project, sandbox["root"] / "work", roots=set(), docker=[build])
    reasons = go.missing(code_graph.Index(project), ["dispatch/main.go"], go.tasks(result["configs"]))
    assert reasons["dispatch/main.go"] == (
        "no Go module holds it, and its Dockerfile's build stage did not run: preparation exited with code 2: "
        "tar: /daodan/state/tools: Cannot open: No such file or directory")


def test_the_error_of_a_failed_go_get_is_its_own_line_not_the_go_command_s_progress():
    """dispatch's `go mod init dispatch && go get` on golang:1.17 today (Modal, 16 November 2026): `go get` takes
    the newest go-sensor, which imports `slices`, a package Go 1.17 does not have."""
    from indexers import go
    log = ("go: creating new go.mod: module dispatch\ngo: to add module requirements and sums:\n\tgo mod tidy\n"
           "go: downloading github.com/instana/go-sensor v1.79.0\ngo: downloading github.com/streadway/amqp v1.1.0\n"
           "dispatch imports\n\tgithub.com/instana/go-sensor imports\n"
           "\tslices: package slices is not in GOROOT (/usr/local/go/src/slices)\n"
           "go: module github.com/streadway/amqp is deprecated: Consider using the github.com/rabbitmq/amqp091-go "
           "package instead.\nDAODAN-DOCKERFILE-FAILED dispatch/Dockerfile:7\n")
    assert go._first_error(log, log.index("DAODAN-")) == (
        "\tslices: package slices is not in GOROOT (/usr/local/go/src/slices)")


def test_a_stage_it_cannot_reproduce_leaves_its_go_files_with_the_instruction_that_stops_it(sandbox, monkeypatch):
    from indexers import go
    monkeypatch.setattr(container, "run_in_container", lambda *a, **k: (_ for _ in ()).throw(AssertionError(k)))
    project = dispatch(sandbox)
    build = fact("robot-shop-dispatch.json", "dispatch/Dockerfile", "dispatch")
    build["stages"][0]["commands"].insert(0, {"kind": "ARG", "line": 2, "end_line": 2, "original": "ARG TOKEN",
                                              "args": [{"TOKEN": None}]})
    result = go.index(project, sandbox["root"] / "work", roots=set(), docker=[build])
    reasons = go.missing(code_graph.Index(project), ["dispatch/main.go"], go.tasks(result["configs"]))
    assert reasons["dispatch/main.go"].startswith("no Go module holds it, and its Dockerfile's build stage is not "
                                                  "reproduced: dispatch/Dockerfile:2: ARG TOKEN: TOKEN has no value")


# ------------------------------------------------------------------ scip-clang in the stage


def currency(sandbox):
    """OpenTelemetry Demo's checkout around currency, its files tracked as Git tracks them (the sandbox's fake
    subprocess answers no Git: `container.tracked` stands in), src/currency/build among them."""
    project = sandbox["root"] / "project"
    files = {"src/currency/src/server.cpp": "int main() { return 0; }\n",
             "src/currency/src/other.cpp": "int other() { return 1; }\n",
             "src/currency/CMakeLists.txt": "project(currency CXX)\n", "src/currency/genproto/CMakeLists.txt": "",
             "src/currency/build/.keep": "", "src/currency/proto/.keep": "", "pb/demo.proto": "",
             "src/currency/Dockerfile": ""}
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    sandbox["monkeypatch"].setattr(container, "tracked", lambda folder: {rel: (0o100644, "") for rel in files}
                                   if Path(folder) == project else {})
    return project


def clang_runs(monkeypatch, docker, roots=("src/currency",)):
    """`container.run_in_container` for the C and C++ index: its own run, whose configure of each of `roots`
    fails as the finale's did (Protobuf's CMake package is not in Daodan's image), then `docker(out_dir)`."""
    from indexers import clang
    calls = []

    def run_in_container(project_dir, command, *, image, out_dir, **options):
        if (answer := probed(command, out_dir, ALPINE_SOURCES)) is not None:
            return answer
        calls.append({"image": image, "command": command, **options})
        out = Path(out_dir) / "out"
        out.mkdir(parents=True, exist_ok=True)
        if image != clang.IMAGE:
            return docker(Path(out_dir))
        (out / "result.json").write_text(json.dumps({"units": [{
            "root": root, "state": "failed", "cause": "the configure ended with exit code 1",
            "steps": [{"step": "configure", "returncode": 1, "seconds": 1.0,
                       "tail": 'Could not find a package configuration file provided by "Protobuf"'}],
            "compiled": {}, "index": None} for root in roots], "peak_mb": 90}), encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": []}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(container, "architecture", lambda: "x64")
    monkeypatch.setattr(docker_build, "pinned", lambda image, timeout=60: image)
    return calls


CURRENCY = fact("otel-demo-currency.json", "src/currency/Dockerfile", ".", {"OPENTELEMETRY_CPP_VERSION": "1.28.0"})
UNITS = [{"root": "src/currency", "kind": "cmake-target"}]


def test_a_cmake_unit_daodan_cannot_configure_is_built_and_indexed_in_its_dockerfile_s_stage(sandbox, monkeypatch):
    """currency: Daodan's image has no Protobuf for its configure. Its Dockerfile's `builder` installs it: the
    preparation runs the stage's steps on the base by its digest, places glibc for scip-clang where only glibc's
    loader looks when the base is musl (Alpine), and the execution, offline, runs the stage's own build with
    CMake writing its compilation database, gives each command the target of the compiler it names (clang finds
    Alpine's headers so) and runs scip-clang where the build runs; its documents name the checkout's files."""
    from indexers import clang

    def docker(out_dir):
        out = out_dir / "out"
        (out / "index.scip").write_bytes(document("src/server.cpp", []) + document("build/generated/demo.pb.cc", []))
        (out / "compile_commands.json").write_text(json.dumps([
            {"directory": "/currency/build", "command": "/usr/bin/c++ -c /currency/src/server.cpp",
             "file": "/currency/src/server.cpp"},
            {"directory": "/currency/build", "command": "/usr/bin/c++ -c generated/demo.pb.cc",
             "file": "generated/demo.pb.cc"}]), encoding="utf-8")
        (out_dir / "execute.log").write_text("[100%] Built target currency\nDAODAN-BUILD-EXIT 0\nFinished indexing 2 "
                                             "translation units (num errored TUs: 0).\n", encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": [str(out / "index.scip")]}

    calls = clang_runs(monkeypatch, docker)
    project = currency(sandbox)
    result = clang.index(project, sandbox["root"] / "work", units=UNITS, docker=[CURRENCY])
    own, staged = calls
    assert own["image"] == clang.IMAGE and staged["image"].startswith("docker.io/library/alpine:3.24.3@sha256:")
    script = staged["prepare"][-1]
    assert "apk add git cmake make g++ linux-headers" in script and "mkdir -p build && cd build" not in script
    assert f"if [ -e /lib/ld-musl-x86_64.so.1 ]; then tar -xf {preparation.IN}/glibc.tar -C / ; fi" in script
    assert f"{preparation.T}/bin/scip-clang" in script and callable(staged["inputs"])
    assert {"github.com", "dl-cdn.alpinelinux.org"} <= set(staged["registries"]) and staged["outputs"] == ["/daodan/out"]
    assert "cd /currency" in staged["command"][2]
    run = staged["command"][-1]
    assert "export CMAKE_EXPORT_COMPILE_COMMANDS=ON" in run and "-dumpmachine" in run and "--target=" in run
    assert "/bin/sh -c 'mkdir -p build && cd build     && cmake ..     && make" in run
    assert f"{preparation.T}/bin/scip-clang --compdb-path=" in run and "--index-output-path=/daodan/out/index.scip" in run
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == ["src/currency/src/server.cpp"] and "state" not in result
    [unit] = [u for u in result["units"] if u["root"] == "src/currency"]
    assert unit["state"] == "indexed"
    assert unit["docker"] == {"dockerfile": "src/currency/Dockerfile", "stage": "builder",
                              "ran": [19, 24, 26, 28, 38, 40, 41, 42, 44, 45, 47], "build": 49}
    assert result["configs"]["compiled"] == {"src/currency/src/server.cpp": 1}
    assert clang.missing(index, ["src/currency/src/other.cpp"], result["configs"]) == {
        "src/currency/src/other.cpp": "no compile command: the build compiles other files of src/currency/src, "
                                      "not this one"}


def test_the_compile_errors_scip_clang_reports_in_the_stage_are_on_record(sandbox, monkeypatch):
    """The stage's log stays in the indexer's work folder, which the engine pass removes: what scip-clang said of
    the stage's compiles (`--show-compiler-diagnostics`, counted as `clang_run._diagnostics` counts them) is the
    indexer's `diagnostics` in the result, which the engine report keeps. currency on Alpine before clang's
    builtin headers: 204 errors from GCC's xmmintrin.h, and still "num errored TUs: 0"."""
    from indexers import clang
    said = ("/usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0/include/xmmintrin.h:1377:1: error: definition of builtin "
            "function '_mm_pause'\n/usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0/include/emmintrin.h:1526:1: error: "
            "definition of builtin function '_mm_clflush'\n/currency/src/server.cpp:40:3: warning: unused variable\n"
            "2 errors generated.\nFinished indexing 1 translation units (num errored TUs: 0).\n")

    def docker(out_dir):
        (out_dir / "out" / "index.scip").write_bytes(document("src/server.cpp", []))
        (out_dir / "execute.log").write_text(f"DAODAN-BUILD-EXIT 0\n{said}", encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": []}

    clang_runs(monkeypatch, docker)
    result = clang.index(currency(sandbox), sandbox["root"] / "work", units=UNITS, docker=[CURRENCY])
    assert result["indexer"]["diagnostics"] == {"errors": 2, "warnings": 1, "error_examples": [
        "/usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0/include/xmmintrin.h:1377:1: error: definition of builtin "
        "function '_mm_pause'",
        "/usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0/include/emmintrin.h:1526:1: error: definition of builtin "
        "function '_mm_clflush'"]}


def test_two_units_one_stage_builds_are_built_once_and_take_that_run_s_state(sandbox, monkeypatch):
    """currency's genproto has a CMakeLists.txt of its own, which the stage copies too: the stage runs once (it
    builds opentelemetry-cpp), and each unit it builds takes that run's state."""
    from indexers import clang

    def docker(out_dir):
        (out_dir / "out" / "index.scip").write_bytes(document("src/server.cpp", []))
        (out_dir / "execute.log").write_text("DAODAN-BUILD-EXIT 0\n", encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": []}

    roots = ("src/currency", "src/currency/genproto")
    calls = clang_runs(monkeypatch, docker, roots)
    result = clang.index(currency(sandbox), sandbox["root"] / "work", docker=[CURRENCY],
                         units=[{"root": root, "kind": "cmake-target"} for root in roots])
    assert [call["image"] == clang.IMAGE for call in calls] == [True, False]
    states = {u["root"]: (u["state"], u["docker"]["build"]) for u in result["units"]}
    assert states == {"src/currency": ("indexed", 49), "src/currency/genproto": ("indexed", 49)}
    assert len(result["indexes"]) == 1


def test_a_stage_build_that_writes_no_database_leaves_the_unit_with_its_line_and_the_build_s_words(sandbox,
                                                                                                    monkeypatch):
    from indexers import clang

    def docker(out_dir):
        (out_dir / "execute.log").write_text(
            "CMake Error at CMakeLists.txt:7 (find_package):\n  Could not find a package configuration file provided "
            "by \"Protobuf\"\n-- Configuring incomplete, errors occurred!\nDAODAN-BUILD-EXIT 1\nDAODAN-NO-DATABASE\n",
            encoding="utf-8")
        return {"state": "done", "exit_code": 3, "outputs": []}

    clang_runs(monkeypatch, docker)
    result = clang.index(currency(sandbox), sandbox["root"] / "work", units=UNITS, docker=[CURRENCY])
    assert result["state"] == "failed"
    [unit] = [u for u in result["units"] if u["root"] == "src/currency"]
    assert unit["state"] == "failed" and unit["cause"] == (
        "src/currency/Dockerfile:49 `RUN mkdir -p build && cd build     && cmake ..     && make -j$(nproc || sysctl -n "
        "hw.ncpu || echo 1) install` ended with exit code 1 and wrote no compilation database: -- Configuring "
        "incomplete, errors occurred!")


def packages_in(root: Path, tmp_path: Path, owned: dict, database: str, versions: dict) -> list[dict]:
    """The stage's package map (`clang.PACKAGE_MAP`) run in a shell over `root`, standing for the stage's
    filesystem: `owned` maps each file to its package (None for one no package owns), `database` is apk's or
    dpkg's; the compilers' include paths are those GCC on Alpine prints, `..` included."""
    from indexers import clang
    for rel in owned:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("", encoding="utf-8")
    (root / "usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0").mkdir(parents=True, exist_ok=True)
    if database == "apk":
        blocks = {}
        for rel, package in owned.items():
            if package:
                blocks.setdefault(package, {}).setdefault(posixpath.dirname(rel), []).append(posixpath.basename(rel))
        (root / "lib/apk/db").mkdir(parents=True)
        (root / "lib/apk/db/installed").write_text("".join(
            f"P:{package}\nV:{versions[package]}\nA:x86_64\n" + "".join(
                f"F:{folder}\n" + "".join(f"R:{name}\nZ:Q1abc=\n" for name in names)
                for folder, names in folders.items()) + "\n" for package, folders in blocks.items()), encoding="utf-8")
        programs = {}
    else:
        (root / "var/lib/dpkg/info").mkdir(parents=True)
        for package in sorted(set(filter(None, owned.values()))):
            (root / f"var/lib/dpkg/info/{package}:amd64.list").write_text("".join(
                f"/{rel}\n" for rel, owner in owned.items() if owner == package) + "/usr\n/usr/include\n",
                                                                         encoding="utf-8")
        programs = {"dpkg-query": "".join(f"printf '%s\\t%s\\n' {shlex.quote(name)} {shlex.quote(version)}\n"
                                          for name, version in versions.items())}
    search = (f"{root}/usr/local/include\n {root}/usr/lib/gcc/x86_64-alpine-linux-musl/15.2.0/../../../../include/c++/"
              f"15.2.0\n {root}/usr/include")
    for name in ("cc", "c++"):
        programs[name] = (f"echo 'ignoring nonexistent directory \"/usr/include/fixed\"' >&2\n"
                          f"printf '#include <...> search starts here:\\n {search}\\nEnd of search list.\\n' >&2\n")
    done = subprocess.run(["sh", "-c", clang.PACKAGE_MAP], capture_output=True, text=True, timeout=60, cwd=tmp_path,
                          env={**os.environ, "DAODAN_ROOT": str(root),
                               "PATH": f"{bin_with(tmp_path, programs)}:{os.environ['PATH']}"})
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def bin_with(tmp_path: Path, programs: dict) -> Path:
    folder = tmp_path / "bin"
    folder.mkdir(exist_ok=True)
    for name, body in programs.items():
        (folder / name).write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
        (folder / name).chmod(0o755)
    return folder


def test_the_stage_names_each_system_header_folder_by_the_package_that_owns_most_of_its_files(tmp_path):
    """As the main route's package map (`clang_run.package_map`), in the stage's own shell, which may have no
    python3 (Alpine): each folder under the compilers' include paths named by the apk package that owns most of
    its files, as scip-clang writes a package (`clang_run._clean`); the project is the folder the build runs in; a
    folder no package owns (what the stage's `make install` wrote, opentelemetry-cpp under /usr/local) has none."""
    owned = {"usr/include/absl/base/prefetch.h": "abseil-cpp-dev", "usr/include/absl/base/config.h": "abseil-cpp-dev",
             "usr/include/absl/base/odd.h": "grpc-dev", "usr/include/grpc/grpc.h": "grpc-dev",
             "usr/include/c++/15.2.0/string": "libstdc++-dev", "usr/include/c++/15.2.0/vector": "libstdc++-dev",
             "usr/include/stdio.h": "musl-dev", "usr/local/include/opentelemetry/version.h": None}
    versions = {"abseil-cpp-dev": "20250814.1-r0", "grpc-dev": "1.74.1-r0", "libstdc++-dev": "15.2.0-r2",
                "musl-dev": "1.2.5-r10"}
    entries = packages_in(tmp_path / "root", tmp_path, owned, "apk", versions)
    assert entries[0] == {"path": ".", "package": "project@0"}
    assert sorted(entries[1:], key=lambda e: e["path"]) == [
        {"path": "/usr/include", "package": "musl-dev@1.2.5-r10"},
        {"path": "/usr/include/absl/base", "package": "abseil-cpp-dev@20250814.1-r0"},
        {"path": "/usr/include/c++/15.2.0", "package": "libstdc__-dev@15.2.0-r2"},  # `_clean`: + is _
        {"path": "/usr/include/grpc", "package": "grpc-dev@1.74.1-r0"}]


def test_what_a_cmake_install_of_the_stage_wrote_is_named_by_that_build(tmp_path):
    """opentelemetry-cpp, which currency's stage clones and installs with `make install`, owns no apk package: its
    build's own record of what it installed (install_manifest.txt) names the files, the package its CMakeCache
    states. The build the stage's WORKDIR holds is the project's, not a package."""
    root = tmp_path / "root"
    built = {"opentelemetry-cpp/build": ("opentelemetry-cpp", "1.28.0",
                                         ["usr/local/include/opentelemetry/version.h",
                                          "usr/local/include/opentelemetry/common/attribute_value.h"]),
             "currency/build": ("currency", "", ["usr/local/include/currency/api.h"])}
    for folder, (name, version, files) in built.items():
        (root / folder).mkdir(parents=True)
        (root / folder / "install_manifest.txt").write_text("".join(f"/{rel}\n" for rel in files), encoding="utf-8")
        (root / folder / "CMakeCache.txt").write_text(
            f"CMAKE_PROJECT_NAME:STATIC={name}\nCMAKE_PROJECT_VERSION:STATIC={version}\n", encoding="utf-8")
    owned = {rel: None for _name, _version, files in built.values() for rel in files}
    entries = packages_in(root, root / "currency", {**owned, "usr/include/stdio.h": "musl-dev"}, "apk",
                          {"musl-dev": "1.2.5-r10"})
    assert sorted(entries[1:], key=lambda e: e["path"]) == [
        {"path": "/usr/include", "package": "musl-dev@1.2.5-r10"},
        {"path": "/usr/local/include/opentelemetry", "package": "opentelemetry-cpp@1.28.0"},
        {"path": "/usr/local/include/opentelemetry/common", "package": "opentelemetry-cpp@1.28.0"}]


def test_a_compiler_that_is_not_clang_reads_clang_s_builtin_headers(tmp_path):
    """`clang_run.builtin_headers` in the stage's shell: a command of GCC (no `-print-resource-dir`) gets
    `-nobuiltininc -isystem <clang's headers> -idirafter <its own include folder>`, as scip-clang otherwise reads
    GCC's xmmintrin.h as clang's (204 errors on currency); on a musl target clang's headers come after the C
    library's, where clang's own driver puts them (Linux.cpp of llvmorg-21.1.8:641-686): `-idirafter`. A clang
    keeps its own; a command that drops the builtin headers itself is left as it is. Each gets the target of its
    compiler."""
    from indexers import clang
    include = tmp_path / "gcc/include"
    include.mkdir(parents=True)
    folder = bin_with(tmp_path, {
        "gcc": ('case "$1" in -dumpmachine) echo x86_64-alpine-linux-musl ;; -print-resource-dir) exit 1 ;; '
                f'-print-file-name=include) echo {include} ;; esac\n'),
        "clang": 'case "$1" in -dumpmachine) echo x86_64-pc-linux-gnu ;; -print-resource-dir) echo /r ;; esac\n'})
    gnu = bin_with(tmp_path, {"gnu-gcc": ('case "$1" in -dumpmachine) echo x86_64-linux-gnu ;; -print-resource-dir) '
                                          f'exit 1 ;; -print-file-name=include) echo {include} ;; esac\n')}) / "gnu-gcc"
    gcc, cc = folder / "gcc", folder / "clang"
    db = tmp_path / "compile_commands.json"
    db.write_text(json.dumps([{"directory": "/w", "command": f"{gcc} -c a.c", "file": "a.c"},
                              {"directory": "/w", "command": f"{cc} -c b.c", "file": "b.c"},
                              {"directory": "/w", "command": f"{gcc} -nostdinc -c c.c", "file": "c.c"},
                              {"directory": "/w", "command": f"{gnu} -c d.c", "file": "d.c"}], indent=1),
                  encoding="utf-8")
    out = tmp_path / "out.json"
    done = subprocess.run(["sh", "-c", clang.COMPDB], capture_output=True, text=True, timeout=60,
                          env={**os.environ, "db": str(db), "out": str(out)})
    assert done.returncode == 0, done.stderr
    assert [entry["command"] for entry in json.loads(out.read_text(encoding="utf-8"))] == [
        f"{gcc} --target=x86_64-alpine-linux-musl -nobuiltininc -idirafter {clang.HEADERS} -idirafter {include} -c a.c",
        f"{cc} --target=x86_64-pc-linux-gnu -c b.c",
        f"{gcc} --target=x86_64-alpine-linux-musl -nostdinc -c c.c",
        f"{gnu} --target=x86_64-linux-gnu -nobuiltininc -isystem {clang.HEADERS} -idirafter {include} -c d.c"]


def test_on_a_debian_stage_dpkg_s_lists_name_the_folders(tmp_path):
    owned = {"usr/include/c++/13/string": "libstdc++-13-dev", "usr/include/stdio.h": "libc6-dev",
             "usr/include/zlib.h": "zlib1g-dev", "usr/include/zconf.h": "zlib1g-dev"}
    versions = {"libstdc++-13-dev": "13.3.0-6ubuntu2~24.04.1", "libc6-dev": "2.39-0ubuntu8.6",
                "zlib1g-dev": "1:1.3.dfsg-3.1ubuntu2.1"}
    entries = packages_in(tmp_path / "root", tmp_path, {**owned, "usr/include/c++/15.2.0/x": None}, "dpkg", versions)
    assert sorted(entries[1:], key=lambda e: e["path"]) == [
        {"path": "/usr/include", "package": "zlib1g-dev@1_1.3.dfsg-3.1ubuntu2.1"},
        {"path": "/usr/include/c++/13", "package": "libstdc__-13-dev@13.3.0-6ubuntu2_24.04.1"}]


def test_a_stage_run_whose_index_does_not_come_back_says_the_engine_s_cause(sandbox, monkeypatch):
    """currency on Modal (16 November 2026): the stage built and scip-clang finished, and the run ended with no
    exit code and no outputs; the unit's cause carries what the engine said."""
    from indexers import clang

    def docker(out_dir):
        (out_dir / "execute.log").write_text("DAODAN-BUILD-EXIT 0\nFinished indexing 5 translation units in 13.9s "
                                             "(indexing: 13.4s, merging: 0.5s, num errored TUs: 0).\n",
                                             encoding="utf-8")
        return {"state": "failed", "exit_code": None, "outputs": [], "cause": "the engine's own words"}

    clang_runs(monkeypatch, docker)
    result = clang.index(currency(sandbox), sandbox["root"] / "work", units=UNITS, docker=[CURRENCY])
    [unit] = [u for u in result["units"] if u["root"] == "src/currency"]
    assert unit["state"] == "failed" and unit["cause"] == (
        "scip-clang in its Dockerfile's build stage wrote no index of the checkout's files (exit code None; the "
        "engine's own words): Finished indexing 5 translation units in 13.9s (indexing: 13.4s, merging: 0.5s, num "
        "errored TUs: 0).")


def test_a_stage_it_cannot_reproduce_adds_its_line_to_the_unit_s_cause(sandbox, monkeypatch):
    from indexers import clang
    calls = clang_runs(monkeypatch, lambda out_dir: (_ for _ in ()).throw(AssertionError(out_dir)))
    build = json.loads(json.dumps(CURRENCY))
    build["stages"][1]["commands"].insert(0, {"kind": "ARG", "line": 23, "end_line": 23, "original": "ARG TOKEN",
                                              "args": [{"TOKEN": None}]})
    result = clang.index(currency(sandbox), sandbox["root"] / "work", units=UNITS, docker=[build])
    assert [call["image"] for call in calls] == [clang.IMAGE]
    [unit] = [u for u in result["units"] if u["root"] == "src/currency"]
    assert unit["state"] == "failed" and unit["cause"] == (
        "the configure ended with exit code 1; its Dockerfile's build stage is not reproduced: "
        "src/currency/Dockerfile:23: ARG TOKEN: TOKEN has no value: no default and no build argument gives one")
    assert [g["path"] for g in result["gaps"] if g["kind"] == "not_reproduced"] == ["src/currency/Dockerfile:23"]


def test_the_pre_map_s_dockerfiles_reach_the_c_and_cpp_index():
    from indexers import clang
    build = {"dockerfile": "src/currency/Dockerfile", "context": ".", "args": {}, "stages": []}
    assert clang.structure({"units": [], "docker_builds": [build]})["docker"] == [build]
    assert "docker" not in clang.structure({"units": []})


ALPINE = "docker.io/library/alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a"


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_an_alpine_stage_brings_its_outputs_back(tmp_path):
    """currency's stage starts FROM Alpine, whose tar is BusyBox's: no -r, a single -C. The execution's outputs
    come back from it, a folder and a file; an output the run did not write is none. Before, the run ended with
    `SandboxFilesystemNotFoundError: path does not exist: /tmp/daodan-outputs.tar` and no output."""
    from test_codebase_map_dynamic_services import the_driver
    work = tmp_path / "project"
    work.mkdir()
    (work / "a.txt").write_text("x\n", encoding="utf-8")
    with the_driver() as modal_pipeline:
        result = modal_pipeline.sandbox_run(
            work, ["sh", "-c", "mkdir -p /daodan/out/sub && echo hi > /daodan/out/x && echo there > /daodan/out/sub/y"
                               " && echo one > /tmp/one"],
            image=ALPINE, out_dir=tmp_path / "out", outputs=["/daodan/out", "/tmp/one", "/tmp/never"])
    assert result["state"] == "done" and result["exit_code"] == 0, result
    assert sorted(Path(path).relative_to(tmp_path / "out").as_posix() for path in result["outputs"]) == [
        "one", "out/sub/y", "out/x"]
    assert (tmp_path / "out/out/sub/y").read_text(encoding="utf-8") == "there\n"
