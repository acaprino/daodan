"""A unit only its Dockerfile builds: its build stage reproduced up to the build, from BuildKit's reading of it.

The facts are the pre-map's (`premap/dockerfile.py`) on the two real Dockerfiles of fixtures/premap/dockerfile:
robot-shop's dispatch (Go files, no go.mod: the stage writes it) and OpenTelemetry Demo's currency (CMake, whose
packages the stage installs with apk and builds from GitHub).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

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
    folder = tmp_path / "project"
    for rel, text in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8")
    return folder


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
    assert plan["ran"] == [3, 5, 7] and plan["build"] == {"line": 8, "original": "RUN go install"}
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
    work = project(tmp_path, {"src/currency/src/main.cpp": "int main(){}\n", "src/currency/CMakeLists.txt": "",
                              "src/currency/genproto/CMakeLists.txt": "", "src/currency/build/.keep": "",
                              "src/currency/proto/.keep": "", "pb/demo.proto": "", "src/currency/Dockerfile": ""})
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

    def run_in_container(project_dir, command, *, image, out_dir, prepare, outputs, registries, inputs=None,
                         **options):
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
    monkeypatch.setattr(docker_build, "pinned", lambda image, timeout=60: f"docker.io/library/{image}@sha256:{'c' * 64}")
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
        Path(out_dir).mkdir(parents=True)
        (Path(out_dir) / "prepare.log").write_text(
            "go: creating new go.mod: module dispatch\ngo: finding module for package github.com/streadway/amqp\n"
            "dispatch imports\n\tgithub.com/streadway/amqp: cannot find module providing package "
            "github.com/streadway/amqp: dial tcp: lookup proxy.golang.org: no such host\n"
            "DAODAN-DOCKERFILE-FAILED dispatch/Dockerfile:7\n", encoding="utf-8")
        return {"state": "failed", "exit_code": None, "outputs": [], "cause": "preparation exited with code 1"}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", lambda image, timeout=60: f"{image}@sha256:{'c' * 64}")
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
        Path(out_dir).mkdir(parents=True)
        (Path(out_dir) / "prepare.log").write_text("go: creating new go.mod: module dispatch\n"
                                                   "tar: /daodan/state/tools: Cannot open: No such file or directory\n",
                                                   encoding="utf-8")
        return {"state": "failed", "exit_code": None, "outputs": [], "cause": "preparation exited with code 2"}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(docker_build, "pinned", lambda image, timeout=60: f"{image}@sha256:{'c' * 64}")
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
