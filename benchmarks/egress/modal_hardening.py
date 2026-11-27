"""What `--cap-drop ALL` and `--user 65532:65532` break in a preparation and in a project's services (`T3.A.5`).

    modal run benchmarks/egress/modal_hardening.py

In a VM Sandbox with Docker's daemon (as `modal_probe.py`), this same file runs as the driver (`python
modal_hardening.py drive`): every recipe of `preparation.NEEDS` (with the JDK of `UNPACK_JDK`, corepack and mise in
`STATE`), one restore per manager of `preparation.RESTORES`, the copy into `/work` and the `STATE` volume, and two
services whose entrypoint changes owner and user (postgres, mysql). Each runs through Daodan's own `container.phase`
and `container.start_services`, with the flags of a variant put after `create`: today's (none), `--cap-drop ALL`,
`--user 65532:65532`, both. Then the decided target: a recipe as root without `/work` and with `--cap-drop ALL` plus
the least capabilities it needs (from Docker's default set, dropped one at a time while it still succeeds); a restore
as `65532` with `--cap-drop ALL` on volumes owned by `65532`; a service as root with the least capabilities. The
network is the engine's bridge: the proxy is `modal_probe.py`'s subject. The `daodan:` rows run Daodan's own
containers as its code makes them (`container.UNPRIVILEGED`, `T3.A.6a`): the proxy opening a registry, the reader of
the `.env` files, the probe of `leaves`, the pod and `reached`. Each recipe and restore runs once more as a split
preparation runs it (`code`, `T3.A.6b`): `container.own` gives the copy to `65532`, `container.tool_phase` installs
the recipes of `preparation.NEEDS` as root without /work with their `caps`, the rest runs as `65532` with
`--cap-drop ALL` (`container.RESTORE`). Writes `results/hardening.json`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
import sys
import threading
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CAPS = ["CHOWN", "DAC_OVERRIDE", "FSETID", "FOWNER", "MKNOD", "NET_RAW", "SETGID", "SETUID", "SETFCAP",
                "SETPCAP", "NET_BIND_SERVICE", "SYS_CHROOT", "KILL", "AUDIT_WRITE"]  # Docker's default set
USER = ["--user", "65532:65532"]
DROP = ["--cap-drop", "ALL"]
VARIANTS = {"oggi": [], "cap-drop": DROP, "user": USER, "entrambi": [*DROP, *USER]}


def drive() -> None:  # inside the VM: Daodan's modules at /daodan/map/core, Docker at /opt/docker
    sys.path[:0] = ["/daodan/map/core"]
    import container
    import preparation
    from indexers.clang import IMAGE as BUILDPACK
    from indexers.python import IMAGE as PYTHON_IMAGE
    from container_runner import TOOLS

    engine = container.Engine("docker", ("/opt/docker/docker",))
    original = container.cli
    local = threading.local()

    def cli(found, *args, **kw):  # the variant's flags right after `create`, in this thread's runs only
        flags = getattr(local, "flags", [])
        if args and args[0] == "create" and flags:
            args = ("create", *flags, *args[1:])
        return original(found, *args, **kw)

    container.cli = cli
    container.SERVICE_WAIT = 180  # a service that has not answered in 3 minutes has failed here
    T, IN, STATE = preparation.T, preparation.IN, preparation.STATE
    limits = {"memory": 4 * 2**30, "pids": 4096, "cpus": 2}
    runs, dl = Path("/runs"), Path("/dl")
    dl.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    downloaded: dict[str, Path] = {}

    def fetched(files) -> dict[str, Path]:
        out = {}
        for url, sha, name in files:
            with lock:
                if name not in downloaded:
                    target = dl / name
                    urllib.request.urlretrieve(url, target)
                    digest = hashlib.file_digest(target.open("rb"), "sha256").hexdigest()
                    if digest != sha:
                        raise RuntimeError(f"{name}: sha256 {digest}, expected {sha}")
                    downloaded[name] = target
            out[f"{IN}/{name}"] = downloaded[name]
        return out

    def copy_of(name: str, files: dict[str, str], inputs: dict[str, Path]) -> Path:
        project = runs / "projects" / name
        project.mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            (project / rel).parent.mkdir(parents=True, exist_ok=True)
            (project / rel).write_text(text, encoding="utf-8")
        tar = runs / "copies" / f"{name}.tar"
        tar.parent.mkdir(parents=True, exist_ok=True)
        container.copy_perimeter(project, tar, inputs)
        return tar

    def volumes(work: bool) -> list[str]:
        token = uuid.uuid4().hex[:12]
        names = [f"daodan-work-{token}", f"daodan-state-{token}"]
        for name in names:
            container.checked(original(engine, "volume", "create", name), "volume create")
        return [f"{names[0]}:/work", f"{names[1]}:{STATE}"] if work else [f"{names[1]}:{STATE}"]

    def drop(mounts: list[str]) -> None:
        for mount in mounts:
            original(engine, "volume", "rm", "-f", mount.split(":")[0])

    def attempt(image: str, script: str, mounts: list[str], copy: Path | None, flags: list[str],
                env: dict | None = None) -> dict:
        local.flags = flags
        out = runs / "logs" / uuid.uuid4().hex[:12]
        out.mkdir(parents=True)
        try:
            row = container.phase(engine, "run", image=image, command=["sh", "-c", script], network="bridge",
                                  env={**preparation.ENV, **(env or {})}, limits=limits, timeout=1500, copy=copy,
                                  outputs=[], out_dir=out, volumes=mounts)
        finally:
            local.flags = []
        log = Path(row["log"]).read_text(encoding="utf-8", errors="replace") if row.get("log") else ""
        lines = [line for line in log.splitlines() if line.strip()]
        marks = [line for line in lines if line.startswith("DAODAN-") and ("MISSING" in line or "FAILED" in line)]
        ok = row.get("outcome") == "exited" and row.get("exit_code") == 0 and not marks
        error = None if ok else (row.get("cause") or " | ".join([*marks[:3], *lines[-6:]]))[-900:]
        return {"ok": ok, "exit_code": row.get("exit_code"), "seconds": row.get("duration_seconds"), "error": error}

    def least(trial) -> dict:
        """The least of Docker's default capabilities `trial(caps)` succeeds with: none, else all of them, then
        each dropped in turn while it still succeeds."""
        if (none := trial([]))["ok"]:
            return {"minimal": [], "steps": [{"caps": [], **none}]}
        full = trial(DEFAULT_CAPS)
        steps = [{"caps": [], **none}, {"caps": list(DEFAULT_CAPS), **full}]
        if not full["ok"]:
            return {"minimal": None, "steps": steps}
        caps = list(DEFAULT_CAPS)
        for cap in DEFAULT_CAPS:
            fewer = [c for c in caps if c != cap]
            result = trial(fewer)
            steps.append({"without": cap, **result})
            if result["ok"]:
                caps = fewer
        return {"minimal": caps, "steps": steps}

    def adds(caps) -> list[str]:
        return [*DROP, *(word for cap in caps for word in ("--cap-add", cap))]

    head = f'set -u; mkdir -p {T}/bin "$HOME" {preparation.VENVS}'  # as `dynamic/python.py` starts a preparation

    def split(image: str, copy: Path, tools: dict | None, lines: list[str], env: dict | None = None) -> dict:
        """As Daodan's split preparation runs: the copy given to 65532, `tools` as root, `lines` as 65532."""
        mounts, out = volumes(True), runs / "logs" / uuid.uuid4().hex[:12]
        out.mkdir(parents=True)
        given = {**preparation.ENV, **(env or {})}
        try:
            made = container.own(engine, image, copy, mounts, limits, 1500, out, not (tools and tools["lines"]))
            if made.get("outcome") == "exited" and made.get("exit_code") == 0 and tools and tools["lines"]:
                made = container.tool_phase(engine, image, tools, "bridge", given, mounts[1], limits, 1500, out)
            if made.get("outcome") != "exited" or made.get("exit_code") != 0:
                said = Path(made["log"]).read_text(errors="replace")[-600:] if made.get("log") else ""
                return {"ok": False, "error": f"{made['phase']}: {made.get('cause') or said}"}
            local.flags = []
            row = container.phase(engine, "run", image=image, command=["sh", "-c", "\n".join([head, *lines])],
                                  network="bridge", env=given, limits=limits, timeout=1500, copy=None, outputs=[],
                                  out_dir=out, volumes=mounts, flags=container.RESTORE)
        finally:
            drop(mounts)
        log = Path(row["log"]).read_text(encoding="utf-8", errors="replace") if row.get("log") else ""
        lines = [line for line in log.splitlines() if line.strip()]
        marks = [line for line in lines if line.startswith("DAODAN-") and ("MISSING" in line or "FAILED" in line)]
        ok = row.get("outcome") == "exited" and row.get("exit_code") == 0 and not marks
        return {"ok": ok, "seconds": row.get("duration_seconds"),
                "error": None if ok else (row.get("cause") or " | ".join([*marks[:3], *lines[-6:]]))[-900:]}

    def needed(names) -> dict:
        found = preparation.setup(names)
        return {"lines": found["lines"], "caps": found["caps"]}

    def recipe(name: str, image: str, files, lines: list[str], check: str = "", env: dict | None = None,
               code: tuple | None = None) -> dict:
        inputs = fetched(files)
        copy = copy_of(f"recipe-{name}", {}, inputs)
        script = "\n".join([head, *lines, check])
        row = {"row": f"recipe:{name}", "image": image, "script": script, "variants": {}}
        for variant, flags in VARIANTS.items():
            mounts = volumes(True)
            row["variants"][variant] = attempt(image, script, mounts, copy, flags, env)
            drop(mounts)

        def trial(caps):
            mounts = volumes(False)
            try:
                return attempt(image, script, mounts, copy, adds(caps), env)
            finally:
                drop(mounts)
        row["target"] = {"as": "root, no /work, --cap-drop ALL + least", **least(trial)}
        if code is not None:  # (tools, lines as 65532)
            row["code"] = split(image, copy, code[0], [*code[1], check], env)
        return row

    def restore(name: str, image: str, files, project: dict[str, str], prepare: list[str], lines: list[str],
                needs=(), first=()) -> dict:
        inputs = fetched(files)
        copy = copy_of(f"restore-{name}", project, inputs)
        before = "\n".join([head, *prepare])
        script = "\n".join(["set -u", *lines])
        row = {"row": f"restore:{name}", "image": image, "prepare": before, "script": script, "variants": {}}

        def run(flags, owned: bool) -> dict:
            mounts = volumes(True)
            try:
                made = attempt(image, before + ("\nchown -R 65532:65532 /work " + STATE if owned else ""), mounts,
                               copy, [])
                if not made["ok"]:
                    return {"ok": False, "error": f"the root phase before it failed: {made['error']}"}
                return attempt(image, script, mounts, None, flags)
            finally:
                drop(mounts)
        for variant, flags in VARIANTS.items():
            row["variants"][variant] = run(flags, False)
        row["target"] = {"as": "65532, --cap-drop ALL, volumes owned by 65532", **run([*DROP, *USER], True)}
        row["code"] = split(image, copy, needed(needs), [*(f"( {line} )" for line in first), *lines])  # as `plan`
        return row

    def copy_row() -> dict:
        copy = copy_of("copy", {"README.md": "x\n", "src/a.txt": "a\n"}, {})
        script = 'set -u; mkdir -p "$HOME" && echo x > "$HOME/written" && echo x > /work/written && cat /work/src/a.txt'
        row = {"row": "copy:/work+STATE", "image": preparation.IMAGE, "script": script, "variants": {}}
        for variant, flags in VARIANTS.items():
            mounts = volumes(True)
            row["variants"][variant] = attempt(preparation.IMAGE, script, mounts, copy, flags)
            drop(mounts)
        mounts = volumes(True)
        made = attempt(preparation.IMAGE, f"chown -R 65532:65532 /work {STATE}", mounts, copy, [])
        row["target"] = {"as": "65532, --cap-drop ALL, volumes owned by 65532",
                         **(attempt(preparation.IMAGE, script, mounts, None, [*DROP, *USER]) if made["ok"] else made)}
        drop(mounts)
        return row

    def service(name: str, image: str, env: dict[str, str]) -> dict:
        def run(*args, timeout=300, stdin=None):
            return original(engine, *args, timeout=timeout, stdin=stdin)
        pinned = container.pin(run, image, 900)

        def trial_flags(flags) -> dict:
            def injected(*args, timeout=300, stdin=None):
                if args and args[0] == "create" and str(args[2]).startswith("daodan-svc-"):
                    args = ("create", *flags, *args[1:])
                return run(*args, timeout=timeout, stdin=stdin)
            token, cleanup = uuid.uuid4().hex[:12], []
            spec = {"name": name, "image": image, "pinned": pinned, "env": env, "wait": "ports"}
            try:
                pod, failure = container.start_pod(engine, [spec], "bridge", token, 600, cleanup)
                if not pod:
                    return {"ok": False, "error": f"pod: {failure}"}
                [got] = container.start_services(injected, [spec], f"container:{pod}", limits, token)
                return {"ok": got.get("outcome") == "ready", "seconds": got.get("duration_seconds"),
                        "error": None if got.get("outcome") == "ready" else str(got.get("cause"))[-900:]}
            finally:
                for args in cleanup:
                    run(*args)
        row = {"row": f"service:{name}", "image": pinned, "variants": {}}
        for variant, flags in VARIANTS.items():
            row["variants"][variant] = trial_flags(flags)
        row["target"] = {"as": "root, --cap-drop ALL + least", **least(lambda caps: trial_flags(adds(caps)))}
        return row

    def erun(*args, timeout=300, stdin=None):
        return original(engine, *args, timeout=timeout, stdin=stdin)

    def said(answer) -> str:
        return (answer.stdout + answer.stderr).decode("utf-8", "replace").strip()[-600:]

    def own(name: str, body) -> dict:
        """A container of Daodan's own code, as `container` makes it: ok, or the error."""
        try:
            error = body()
        except Exception as failure:  # noqa: BLE001 - the row says why
            error = f"{type(failure).__name__}: {failure}"
        return {"row": f"daodan:{name}", "variants": {},
                "target": {"as": " ".join(container.UNPRIVILEGED), "ok": error is None, "error": error}}

    def proxy() -> str | None:
        token = uuid.uuid4().hex[:12]
        network, box = f"daodan-net-{token}", f"daodan-proxy-{token}"
        container.internal_network(engine, network)
        try:
            container.start_proxy(engine, box, network, ("registry.npmjs.org",), "hardening")
            user = said(erun("inspect", "--format", "{{.Config.User}} {{.HostConfig.CapDrop}}", box))
            ask = ("import socket; s = socket.create_connection(('proxy', 3128), 10); "
                   "s.sendall(b'CONNECT registry.npmjs.org:443 HTTP/1.1\\r\\n\\r\\n'); print(s.recv(64))")
            answer = erun("run", "--rm", "--network", network, container.PROXY_IMAGE, "python3", "-c", ask)
            return None if b" 200 " in answer.stdout and user.startswith("65532:65532") else f"{user} | {said(answer)}"
        finally:
            erun("rm", "-f", box)
            erun("network", "rm", network)

    def dotenv() -> str | None:
        project = runs / "projects" / "dotenv"
        project.mkdir(parents=True)
        (project / ".env").write_text("KEY=value\n", encoding="utf-8")
        (project / ".env").chmod(0o600)  # the user's own: read by 65532 all the same (`bound`, readable)
        for command in (["git", "init", "-q"], ["git", "add", "-A"],
                        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "p"]):
            subprocess.run(command, cwd=project, check=True)
        tar = runs / "copies" / "dotenv.tar"
        tar.parent.mkdir(parents=True, exist_ok=True)
        container.copy_perimeter(project, tar)
        values, _public = container.dotenv_values(erun, tar, [".env"], uuid.uuid4().hex[:12])
        return None if values == {".env": {"KEY": "value"}} else f"values {values}"

    def probe() -> str | None:
        network = f"daodan-net-{uuid.uuid4().hex[:12]}"
        container.internal_network(engine, network)
        try:
            return container.leaves(erun, network, uuid.uuid4().hex[:12])
        finally:
            erun("network", "rm", network)

    def pod() -> str | None:
        token, cleanup = uuid.uuid4().hex[:12], []
        try:
            made, failure = container.start_pod(engine, [], "bridge", token, 120, cleanup)
            if not made:
                return f"pod: {failure}"
            cleanup.insert(0, ("rm", "-f", f"daodan-listen-{token}"))
            erun("run", "-d", "--name", f"daodan-listen-{token}", "--network", f"container:{made}",
                 container.PROXY_IMAGE, "python3", "-m", "http.server", "8080")
            for _ in range(30):
                if container.reached(erun, f"container:{made}", ["8080"]):
                    return None
                time.sleep(1)
            return "reached: port 8080 accepted no connection in 30 s"
        finally:
            for args in cleanup:
                erun(*args)

    setup = preparation.setup
    jdk = (*preparation.TEMURIN, preparation.JDK_IN.rsplit("/", 1)[1])
    java = f"[ -x {preparation.JDK_HOME}/bin/java ] || echo 'DAODAN-MISSING jdk' >&2"
    mise = preparation.toolchains([{"tool": "node", "version": "22.12.0"}])
    jobs = [lambda: copy_row(), lambda: own("proxy", proxy), lambda: own("dotenv", dotenv),
            lambda: own("leaves", probe), lambda: own("pod+reached", pod)]
    for name, base in (("node", preparation.IMAGE), ("uv", preparation.IMAGE), ("go", BUILDPACK), ("rust", BUILDPACK),
                       ("arm-none-eabi", BUILDPACK)):
        jobs.append(lambda name=name, base=base: recipe(name, base, setup([name])["files"], setup([name])["lines"],
                                                        code=(needed([name]), [])))
    jobs += [
        # on the Python image, whose VCS requirements need it (`dynamic/python.py`): the Debian one has no CA
        # certificates, so apt over https fails there before any capability counts; the proxy variable empty
        # apt installs into the image: in a split preparation it cannot run apart, so the preparation stays root
        # (`preparation.IMAGE_NEEDS`); no `code` row
        lambda: recipe("git", PYTHON_IMAGE, [], setup(["git"])["lines"], env={"HTTPS_PROXY": "", "HTTP_PROXY": ""}),
        lambda: recipe("dotnet", BUILDPACK, setup(["dotnet"])["files"], setup(["dotnet"])["lines"],
                       code=(needed(["dotnet"]), [])),
        lambda: recipe("vcpkg", BUILDPACK, setup(["vcpkg"])["files"], setup(["vcpkg"])["lines"],
                       code=(needed(["vcpkg"]), [])),
        lambda: recipe("conan", BUILDPACK, setup(["conan"])["files"], setup(["conan"])["lines"],
                       code=(needed(["conan"]), [])),
        lambda: recipe("poetry", PYTHON_IMAGE, setup(["poetry"])["files"], setup(["poetry"])["lines"],
                       code=(needed(["poetry"]), [])),
        lambda: recipe("jdk", preparation.IMAGE, [jdk], [preparation.UNPACK_JDK], java,
                       code=(None, [preparation.UNPACK_JDK])),
        lambda: recipe("cmdline-tools", preparation.IMAGE, [jdk, *setup(["cmdline-tools"])["files"]],
                       [preparation.UNPACK_JDK, *setup(["cmdline-tools"])["lines"]],
                       code=({"lines": [preparation.UNPACK_JDK, *setup(["cmdline-tools"])["lines"]],
                              "caps": setup(["cmdline-tools"])["caps"]}, [])),
        lambda: recipe("corepack", preparation.IMAGE, setup(["node"])["files"],
                       [*setup(["node"])["lines"], preparation.COREPACK_INSTALL],
                       code=(needed(["node"]), [preparation.COREPACK_INSTALL])),
        lambda: recipe("mise", preparation.IMAGE, mise["files"], mise["lines"], code=(None, mise["lines"])),
        lambda: service("postgres", "postgres:17", {"POSTGRES_PASSWORD": "daodan"}),
        lambda: service("mysql", "mysql:8.4", {"MYSQL_ROOT_PASSWORD": "daodan"}),
    ]
    package = lambda extra: json.dumps({"name": "p", "version": "1.0.0", **extra,  # noqa: E731
                                        "dependencies": {"is-number": "7.0.0"}})
    for name, manager in (("npm", None), ("pnpm", "pnpm@9.15.9"), ("yarn", "yarn@1.22.22")):
        project = {"package.json": package({"packageManager": manager} if manager else {})}
        lines = preparation.node_prepare(list(project), project.__getitem__)["lines"]
        jobs.append(lambda name=name, project=project, lines=lines: restore(
            name, preparation.IMAGE, setup(["node"])["files"], project, setup(["node"])["lines"], lines, ["node"]))
    pyproject = ('[project]\nname = "p"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
                 'dependencies = ["six==1.16.0"]\n')
    poetry = pyproject + '\n[tool.poetry]\npackage-mode = false\n'
    jobs += [
        lambda: restore("uv", PYTHON_IMAGE, setup(["uv"])["files"], {"pyproject.toml": pyproject},
                        [*setup(["uv"])["lines"], "cd /work && uv lock -q"],
                        [preparation.restore("uv", ["."])], ["uv"], ["cd /work && uv lock -q"]),
        lambda: restore("pip", PYTHON_IMAGE, setup(["uv"])["files"], {"requirements.txt": "six==1.16.0\n"},
                        setup(["uv"])["lines"], [preparation.restore("pip", ["."])], ["uv"]),
        lambda: restore("poetry", PYTHON_IMAGE, setup(["poetry"])["files"], {"pyproject.toml": poetry},
                        [*setup(["poetry"])["lines"], "cd /work && poetry lock -q"],
                        [preparation.restore("poetry", ["."])], ["poetry"], ["cd /work && poetry lock -q"]),
        lambda: restore("go", BUILDPACK, setup(["go"])["files"],
                        {"go.mod": "module p\n\ngo 1.22\n\nrequire golang.org/x/text v0.14.0\n"},
                        setup(["go"])["lines"], [preparation.restore("go", ["."])], ["go"]),
        lambda: restore("cargo", BUILDPACK, setup(["rust"])["files"],
                        {"Cargo.toml": '[package]\nname = "p"\nversion = "0.1.0"\nedition = "2021"\n\n'
                                       '[dependencies]\nitoa = "=1.0.11"\n', "src/lib.rs": ""},
                        setup(["rust"])["lines"], [preparation.restore("cargo", ["."])], ["rust"]),
        lambda: restore("dotnet", BUILDPACK, setup(["dotnet"])["files"],
                        {"p.csproj": '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0'
                                     '</TargetFramework></PropertyGroup><ItemGroup><PackageReference '
                                     'Include="Newtonsoft.Json" Version="13.0.3" /></ItemGroup></Project>\n'},
                        setup(["dotnet"])["lines"], [preparation.restore("dotnet", ["."])], ["dotnet"]),
        lambda: restore("maven", preparation.IMAGE, TOOLS["maven"]["files"],
                        {"pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0'
                                    '</modelVersion><groupId>p</groupId><artifactId>p</artifactId><version>1</version>'
                                    '<dependencies><dependency><groupId>junit</groupId><artifactId>junit</artifactId>'
                                    '<version>4.13.2</version></dependency></dependencies></project>\n'},
                        TOOLS["maven"]["setup"], [preparation.UNPACK_JDK, preparation.restore("maven", ["."])],
                        (), TOOLS["maven"]["setup"]),
        lambda: restore("gradle", preparation.IMAGE, TOOLS["gradle"]["files"],
                        {"settings.gradle": "rootProject.name = 'p'\n",
                         "build.gradle": "plugins { id 'java' }\nrepositories { mavenCentral() }\n"
                                         "dependencies { implementation 'junit:junit:4.13.2' }\n"},
                        TOOLS["gradle"]["setup"], [preparation.UNPACK_JDK, preparation.restore("gradle", ["."])],
                        (), TOOLS["gradle"]["setup"]),
    ]

    def guarded(job):
        try:
            row = job()
        except Exception as error:  # noqa: BLE001 - a row that could not run says why, the others go on
            row = {"row": getattr(job, "__name__", "job"), "error": f"{type(error).__name__}: {error}"}
        print(json.dumps({"row": row.get("row"), "variants": {k: v["ok"] for k, v in row.get("variants", {}).items()},
                          "minimal": row.get("target", {}).get("minimal"), "target_ok": row.get("target", {}).get(
                              "ok"), "code_ok": row.get("code", {}).get("ok")}), flush=True)
        return row

    for image in {preparation.IMAGE, BUILDPACK, PYTHON_IMAGE, container.PROXY_IMAGE}:
        container.checked(original(engine, "pull", image, timeout=1800), f"pull of {image}")
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(guarded, jobs))
    version = original(engine, "version", "--format", "{{.Server.Version}}").stdout.decode().strip()
    (runs / "hardening.json").write_text(json.dumps({"docker": version, "default_caps": DEFAULT_CAPS, "rows": rows},
                                                    indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["drive"]:
        drive()
else:
    import time

    import modal

    REPO = HERE.parents[1]
    DOCKER = "https://download.docker.com/linux/static/stable/x86_64/docker-29.10.0.tgz"
    image = (modal.Image.debian_slim(python_version="3.13")
             .apt_install("ca-certificates", "curl", "iptables", "xz-utils", "procps", "git")
             .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
             .run_commands(f"curl -fsSL {DOCKER} -o /tmp/d.tgz && mkdir -p /opt/docker && "
                           "tar -xzf /tmp/d.tgz -C /opt/docker --strip-components=1")
             .add_local_dir(REPO / "daodan/core", "/daodan/map/core", copy=True, ignore=["**/__pycache__/**"])
             .add_local_dir(REPO / "daodan/data", "/daodan/map/data", copy=True)
             .add_local_file(Path(__file__), "/daodan/egress/modal_hardening.py", copy=True))
    app = modal.App("daodan-egress-hardening", image=image)

    def verdict(result: dict | None) -> str:
        return "?" if result is None else "ok" if result.get("ok") else "rotto"

    @app.local_entrypoint()
    def main():
        boxes = modal.App.lookup("daodan-egress-hardening-boxes", create_if_missing=True)
        box = modal.Sandbox.create(image=image, app=boxes, cpu=8, memory=16384, timeout=4 * 3600, runtime="vm")
        try:
            box.exec("sh", "-c", "PATH=/opt/docker:$PATH nohup dockerd > /tmp/dockerd.log 2>&1 &")
            for _ in range(90):
                if box.exec("/opt/docker/docker", "info", timeout=30).wait() == 0:
                    break
                time.sleep(1)
            process = box.exec("python", "/daodan/egress/modal_hardening.py", "drive", timeout=4 * 3600 - 300)
            for line in process.stdout:
                print(line.rstrip()[:400], flush=True)
            print("driver exit", process.wait(), process.stderr.read()[-3000:], flush=True)
            written = box.exec("cat", "/runs/hardening.json").stdout.read()
        finally:
            box.terminate()
        if not written.strip():
            raise SystemExit("the driver gave no result")
        result = json.loads(written)
        out = HERE / "results" / "hardening.json"
        out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print("| riga | " + " | ".join(VARIANTS) + " | obiettivo | capability minime | codice |")
        for row in result["rows"]:
            target = row.get("target") or {}
            minimal = target.get("minimal")
            print(f"| {row['row']} | " + " | ".join(verdict(row.get("variants", {}).get(v)) for v in VARIANTS)
                  + f" | {verdict(target) if 'ok' in target else '-'} | "
                  + ("-" if minimal is None else ", ".join(minimal) or "nessuna") + " | "
                  + (verdict(row["code"]) if "code" in row else "-") + " |")
