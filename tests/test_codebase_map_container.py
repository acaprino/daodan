"""The container operation: the five guarantees, each against a fake Docker-compatible command line.

The fake never runs the command it is given: it records every call, keeps what `cp -`
sends and plays a few scripted commands (`emit`, `sleep`, `exit`). Two smoke tests at
the end use a real engine and run only with DAODAN_CONTAINER_SMOKE=1.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402

FAKE_CLI = r'''
import io, json, shutil, sys, tarfile, time
from pathlib import Path

state = Path(sys.argv[1])
args = sys.argv[2:]
with (state / "calls.jsonl").open("a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\n")
VALUED = {"--name", "--network", "--memory", "--memory-swap", "--pids-limit", "--cpus", "--security-opt", "-w", "-e"}
box = lambda name: state / "containers" / name
verb = args[0] if args else ""
if verb == "version" or verb == "info":
    print("linux")
elif verb == "create":
    rest = args[1:]
    while rest[0] in VALUED:
        rest = rest[2:]
    image, command = rest[0], rest[1:]
    name = args[args.index("--name") + 1]
    (box(name)).mkdir(parents=True)
    saved = state / "images" / image.replace(":", "_")
    if saved.is_dir():
        shutil.copytree(saved, box(name) / "fs")
    else:
        (box(name) / "fs").mkdir()
    (box(name) / "command.json").write_text(json.dumps(command))
    print(name)
elif verb == "cp" and args[1] == "-":
    name = args[2].split(":")[0]
    data = sys.stdin.buffer.read()
    (box(name) / "copy.tar").write_bytes(data)
    with tarfile.open(fileobj=io.BytesIO(data)) as bundle:
        bundle.extractall(box(name) / "fs", filter="data")
elif verb == "cp":
    name, path = args[1].split(":", 1)
    target = box(name) / "fs" / path.lstrip("/")
    if not target.exists():
        sys.exit("Error: Could not find the file " + path)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as bundle:
        bundle.add(target, arcname=target.name)
    sys.stdout.buffer.write(buffer.getvalue())
elif verb == "start":
    name = args[-1]
    if "-a" not in args:
        sys.exit(0)
    command = json.loads((box(name) / "command.json").read_text())
    print("started", name)
    if command[:1] == ["emit"]:
        target = box(name) / "fs" / command[1].lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(command[2])
    elif command[:1] == ["sleep"]:
        time.sleep(float(command[1]))
    elif command[:1] == ["exit"]:
        sys.exit(int(command[1]))
elif verb == "commit":
    shutil.copytree(box(args[1]) / "fs", state / "images" / args[2].replace(":", "_"))
elif verb == "logs":
    print("ready 3128")
'''


def tree_digest(root: Path) -> dict[str, str]:
    """Every file under `root` but `.git`, with the sha256 of its bytes."""
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file() and ".git" not in path.relative_to(root).parts}


class FakeEngineTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-container-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        (self.state / "containers").mkdir(parents=True)
        (self.state / "images").mkdir()
        self.fake = self.scratch / "fake_docker.py"
        self.fake.write_text(FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(self.fake), str(self.state)))
        self.project = self.scratch / "project"
        self.out = self.scratch / "out"
        files = {
            ".gitignore": "ignored.txt\nbuild-out/\n",
            "package.json": '{"name": "fixture"}\n',
            "src/app.js": "export const run = () => 1;\n",
            "data/fixture.csv": "a,b\n1,2\n",
            "ignored.txt": "ignored by git\n",
            "build-out/bundle.js": "built\n",
            ".env": "TOKEN=abc\n",
            "src/secrets.json": '{"key": "value"}\n',
            "node_modules/lib/index.js": "module.exports = 1;\n",
            ".cache/entry": "cached\n",
        }
        for name, text in files.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.git = shutil.which("git")
        if self.git:
            subprocess.run([self.git, "init", "-q", str(self.project)], check=True)

    def calls(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def created(self) -> list[list[str]]:
        return [call for call in self.calls() if call[0] == "create"]

    def run_operation(self, command, **options):
        options.setdefault("image", "fake/runtime:1")
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            return container.run_in_container(self.project, command, out_dir=self.out, engine=self.engine, **options)

    # Guarantee 2: a disposable copy, the project never written.
    def test_project_is_never_mounted_or_written_and_outputs_come_back(self):
        before = tree_digest(self.project)
        result = self.run_operation(["emit", "/out/result.txt", "hello"], outputs=["/out/result.txt"])
        self.assertEqual(result["state"], "done", result)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(tree_digest(self.project), before)
        flat = [token for call in self.calls() for token in call]
        for option in ("-v", "--volume", "--mount", "--volumes-from"):
            self.assertNotIn(option, flat)
        self.assertEqual((self.out / "result.txt").read_text(), "hello")
        self.assertEqual(result["outputs"], [str(self.out / "result.txt")])

    def test_out_dir_inside_the_project_is_refused(self):
        with self.assertRaises(ValueError):
            container.run_in_container(self.project, ["exit", "0"], image="fake/runtime:1",
                                       out_dir=self.project / "out", engine=self.engine)
        self.assertEqual(self.calls(), [])

    # Guarantee 2: only the snapshot perimeter enters the copy.
    def test_copy_holds_the_perimeter_without_ignored_or_forbidden_files(self):
        if not self.git:
            self.skipTest("git is needed to ask what Git ignores")
        self.run_operation(["exit", "0"])
        name = self.created()[0][self.created()[0].index("--name") + 1]
        with tarfile.open(self.state / "containers" / name / "copy.tar") as bundle:
            names = sorted(member.name for member in bundle.getmembers() if member.isfile())
        self.assertEqual(names, ["work/.gitignore", "work/data/fixture.csv", "work/package.json", "work/src/app.js"])

    # Guarantee 3: network closed during execution, open only to registries during preparation.
    def test_execution_has_no_network_and_preparation_reaches_only_the_proxy(self):
        result = self.run_operation(["exit", "0"], prepare=["exit", "0"], registries=("registry.npmjs.org",))
        self.assertEqual(result["state"], "done", result)
        calls = self.calls()
        internal = [call for call in calls if call[:3] == ["network", "create", "--internal"]]
        self.assertEqual(len(internal), 1)
        network = internal[0][3]
        proxy, prepare, execute = self.created()
        self.assertNotIn("--network", proxy)
        self.assertIn("registry.npmjs.org", proxy)
        self.assertIn(["network", "connect", "--alias", "proxy", network, proxy[proxy.index("--name") + 1]], calls)
        self.assertEqual(prepare[prepare.index("--network") + 1], network)
        self.assertIn("HTTPS_PROXY=http://proxy:3128", prepare)
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        self.assertIn("HTTPS_PROXY=", execute)
        committed = [call for call in calls if call[0] == "commit"]
        self.assertEqual(len(committed), 1)
        self.assertIn(committed[0][2], execute)
        self.assertEqual([call[:2] for call in calls if call[0] == "cp" and call[1] == "-"], [["cp", "-"]])
        self.assertIn(["rmi", "-f", committed[0][2]], calls)
        self.assertIn(["network", "rm", network], calls)

    def test_failed_preparation_stops_before_execution(self):
        result = self.run_operation(["exit", "0"], prepare=["exit", "3"])
        self.assertEqual(result["state"], "failed")
        self.assertIn("3", result["cause"])
        self.assertEqual(len(self.created()), 2)

    def test_proxy_refuses_every_host_outside_the_registries(self):
        server = subprocess.Popen([sys.executable, "-I", "-c", container.PROXY_SCRIPT, "0", "registry.npmjs.org"],
                                  stdout=subprocess.PIPE, text=True)
        self.addCleanup(server.wait)
        self.addCleanup(server.kill)
        port = int(server.stdout.readline().split()[1])

        def ask(request: bytes) -> bytes:
            with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
                client.sendall(request)
                return client.recv(1024)

        self.assertTrue(ask(b"CONNECT example.com:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))
        self.assertTrue(ask(b"CONNECT registry.npmjs.org:80 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))
        self.assertTrue(ask(b"GET http://registry.npmjs.org/ HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))

    # Guarantee 3: limits.
    def test_limits_are_passed_and_a_timed_out_container_is_removed(self):
        result = self.run_operation(["sleep", "30"], timeout=2, memory=512 * 2**20, pids=64, cpus=1.5)
        self.assertEqual(result["state"], "timeout")
        execute = self.created()[0]
        name = execute[execute.index("--name") + 1]
        self.assertEqual(execute[execute.index("--memory") + 1], str(512 * 2**20))
        self.assertEqual(execute[execute.index("--memory-swap") + 1], str(512 * 2**20))
        self.assertEqual(execute[execute.index("--pids-limit") + 1], "64")
        self.assertEqual(execute[execute.index("--cpus") + 1], "1.5")
        self.assertIn(["kill", name], self.calls())
        self.assertIn(["rm", "-f", name], self.calls())

    def test_free_memory_below_the_limit_is_a_gap(self):
        with mock.patch.object(container, "free_memory", return_value=2**30):
            result = container.run_in_container(self.project, ["exit", "0"], image="fake/runtime:1",
                                                out_dir=self.out, engine=self.engine, memory=2 * 2**30)
        self.assertEqual(result["state"], "gap")
        self.assertTrue(result["cause"] and result["remedy"])
        self.assertEqual(self.created(), [])

    # Guarantee 3: no host variable.
    def test_no_host_variable_reaches_the_container(self):
        with mock.patch.dict(os.environ, {"DAODAN_SENTINEL": "host-value-7f3a", "HTTPS_PROXY": "http://host-proxy:1"}):
            self.run_operation(["exit", "0"], env={"CI": "1"}, prepare=["exit", "0"])
        for call in self.created():
            values = [call[index + 1] for index, token in enumerate(call) if token in ("-e", "--env")]
            self.assertTrue(all("=" in value for value in values), values)
            self.assertNotIn("--env-file", call)
            self.assertFalse(any("host-value-7f3a" in token or "host-proxy" in token for token in call))
        execute = self.created()[-1]
        self.assertIn("CI=1", execute)

    # Guarantee 4: a record for every run.
    def test_every_run_is_recorded(self):
        self.run_operation(["exit", "4"], prepare=["exit", "0"])
        rows = [json.loads(row) for row in (self.out / container.RECORD_NAME).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["phase"] for row in rows], ["prepare", "execute"])
        for row in rows:
            self.assertEqual(row["engine"], "fake")
            self.assertGreaterEqual(row["duration_seconds"], 0)
            self.assertIn("started_at", row)
        self.assertEqual(rows[0]["image"], "fake/runtime:1")
        self.assertEqual(rows[1]["command"], ["exit", "4"])
        self.assertEqual((rows[0]["outcome"], rows[0]["exit_code"]), ("exited", 0))
        self.assertEqual((rows[1]["outcome"], rows[1]["exit_code"]), ("exited", 4))
        self.assertEqual(len(rows[0]["copy"]["sha256"]), 64)

    # Guarantee 5: no engine, a declared gap and nothing on the host.
    def test_without_an_engine_the_gap_and_no_host_execution(self):
        empty = self.scratch / "empty-path"
        empty.mkdir()
        sentinel = self.scratch / "ran-on-host"
        command = [sys.executable, "-c", f"open({str(sentinel)!r}, 'w')"]
        started = []
        real_run, real_popen = subprocess.run, subprocess.Popen

        def spy_run(argv, *args, **kwargs):
            started.append(list(argv))
            return real_run(argv, *args, **kwargs)

        def spy_popen(argv, *args, **kwargs):
            started.append(list(argv))
            return real_popen(argv, *args, **kwargs)

        with mock.patch.dict(os.environ, {"PATH": str(empty)}), \
                mock.patch.object(container, "wsl_executable", return_value=None), \
                mock.patch.object(container.subprocess, "run", spy_run), \
                mock.patch.object(container.subprocess, "Popen", spy_popen), \
                mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = container.run_in_container(self.project, command, image="fake/runtime:1", out_dir=self.out)
        self.assertEqual(result["state"], "gap")
        self.assertTrue(result["cause"] and result["remedy"])
        self.assertFalse(sentinel.exists())
        self.assertFalse(any(str(sentinel) in " ".join(argv) for argv in started))
        rows = (self.out / container.RECORD_NAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(rows[-1])["outcome"], "gap")

    # Section 3: a pinned download with a wrong checksum is refused and leaves nothing.
    def test_a_wrong_checksum_is_refused(self):
        package = self.scratch / "served" / "kiri.rpm"
        package.parent.mkdir()
        package.write_bytes(b"not the pinned package")
        home = self.scratch / "engine-home"
        arch = container.architecture()
        with mock.patch.object(container, "KIRI_PACKAGES", {arch: ("kiri.rpm", "0" * 64)}), \
                mock.patch.object(container, "KIRI_URL", package.parent.as_uri() + "/{asset}"), \
                mock.patch("resolve_edges.time.sleep"):
            with self.assertRaises(container.Gap) as caught:
                container.kiri_files(home)
        self.assertIn("checksum", caught.exception.cause)
        self.assertTrue(caught.exception.remedy)
        self.assertEqual([path for path in home.rglob("*") if path.is_file()] if home.exists() else [], [])

    @unittest.skipUnless(os.name == "nt", "Daodan brings its own engine only on Windows")
    def test_own_engine_needs_free_disk_before_any_download(self):
        usage = types.SimpleNamespace(total=2**40, used=2**40 - 100 * 2**20, free=100 * 2**20)
        with mock.patch.object(container, "wsl_executable", return_value="wsl.exe"),                 mock.patch.object(container, "wsl", return_value=subprocess.CompletedProcess([], 0, b"", b"")),                 mock.patch.object(container, "engine_home", return_value=self.scratch / "home"),                 mock.patch.object(container.shutil, "disk_usage", return_value=usage),                 mock.patch.object(container, "download") as fetched:
            with self.assertRaises(container.Gap) as caught:
                container.own_engine()
        self.assertIn("free", caught.exception.cause)
        self.assertTrue(caught.exception.remedy)
        fetched.assert_not_called()

    # Section 3: an engine the user already has is used as it is.
    def test_the_user_engine_is_used_and_not_modified(self):
        bin_dir = self.scratch / "bin"
        bin_dir.mkdir()
        if os.name == "nt":
            (bin_dir / "docker.cmd").write_text(f'@"{sys.executable}" "{self.fake}" "{self.state}" %*\r\n')
        else:
            wrapper = bin_dir / "docker"
            wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{self.fake}" "{self.state}" "$@"\n')
            wrapper.chmod(0o755)
        config = self.scratch / "docker-config"
        (config / "contexts" / "meta" / "abc").mkdir(parents=True)
        (config / "config.json").write_text('{"currentContext": "mine", "proxies": {}}')
        (config / "contexts" / "meta" / "abc" / "meta.json").write_text('{"Name": "mine"}')
        before = tree_digest(config)
        with mock.patch.dict(os.environ, {"PATH": str(bin_dir), "DOCKER_CONFIG": str(config)}), \
                mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            found = container.find_engine()
            self.assertEqual(found.name, "docker")
            result = container.run_in_container(self.project, ["emit", "/out/x.txt", "x"], image="fake/runtime:1",
                                                out_dir=self.out, outputs=["/out/x.txt"], engine=found)
        self.assertEqual(result["state"], "done", result)
        self.assertEqual(tree_digest(config), before)
        flat = [token for call in self.calls() for token in call]
        self.assertNotIn("context", flat)
        self.assertNotIn("--context", flat)


SMOKE = os.environ.get("DAODAN_CONTAINER_SMOKE") == "1"
ALPINE = "alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf"


def user_settings() -> dict:
    """What the user owns and the operation must leave as it was: PATH, Docker config and contexts, WSL."""
    settings = {"PATH": os.environ.get("PATH")}
    docker = Path(os.environ.get("DOCKER_CONFIG") or Path.home() / ".docker")
    settings["docker"] = tree_digest(docker) if docker.is_dir() else None
    if os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            settings["user PATH"] = winreg.QueryValueEx(key, "Path")[0]
        settings["wsl"] = container.registered_distros()
    return settings


@unittest.skipUnless(SMOKE, "set DAODAN_CONTAINER_SMOKE=1 to run a real container")
class RealEngineSmokeTest(unittest.TestCase):
    def test_one_container_on_this_machine(self):
        free = container.free_memory()
        if free is not None and free < 4 * 2**30:
            self.skipTest(f"{free / 2**30:.1f} GB free, under 4 GB")
        before = user_settings()
        try:
            engine = container.find_engine()
        except container.Gap as gap:
            self.skipTest(f"no engine: {gap.cause}")
        scratch = Path(tempfile.mkdtemp(prefix="daodan-container-smoke-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        project = scratch / "project"
        (project / "src").mkdir(parents=True)
        (project / "package.json").write_text('{"name": "smoke"}\n')
        (project / "src" / "a.js").write_text("module.exports = 1;\n")
        digest = tree_digest(project)
        script = ("mkdir -p /out; "
                  "if wget -q -T 3 -O /dev/null http://example.com; then echo open; else echo refused; fi > /out/network.txt; "
                  "echo changed > /work/package.json && cat /work/package.json > /out/write.txt; "
                  "ls /work > /out/listing.txt")
        started = time.monotonic()
        result = container.run_in_container(project, ["sh", "-c", script], image=ALPINE, out_dir=scratch / "out",
                                            outputs=["/out"], engine=engine, memory=256 * 2**20, pids=64, timeout=120)
        print(json.dumps({"engine": engine.name, "seconds": round(time.monotonic() - started, 1), **result}))
        self.assertEqual(result["state"], "done", result)
        self.assertEqual((scratch / "out" / "out" / "network.txt").read_text().strip(), "refused")
        self.assertEqual((scratch / "out" / "out" / "write.txt").read_text().strip(), "changed")
        self.assertEqual((scratch / "out" / "out" / "listing.txt").read_text().split(), ["package.json", "src"])
        self.assertEqual(tree_digest(project), digest)
        self.assertEqual(user_settings(), before)

    @unittest.skipUnless(os.name == "nt", "Daodan brings its own engine only on Windows")
    def test_own_engine_installs_into_the_shared_directory(self):
        free = shutil.disk_usage(Path(container.engine_home().anchor)).free
        if free < container.ENGINE_DISK_MIN:
            self.skipTest(f"{free / 2**20:.0f} MB free on the shared directory's disk")
        before = user_settings()
        registered = container.DISTRO in before["wsl"][1]
        try:
            home = container.engine_home()
            container.kiri_files(home)
            remove = container.ensure_distro(home)
            argv = container.distro_argv()
            probes = {"docker": [*argv, "/usr/bin/docker", "--version"],
                      "kiri": [*argv, "/usr/bin/kiri"],
                      "cgroup": [*argv, "/bin/sh", "-c", "grep ' /sys/fs/cgroup ' /proc/mounts"]}
            answers = {name: subprocess.run(probe, capture_output=True, text=True, timeout=60)
                       for name, probe in probes.items()}
            for name, answer in answers.items():
                print(name, answer.returncode, answer.stdout.strip()[:200], answer.stderr.strip()[:200])
            self.assertIn("29.9.2", answers["docker"].stdout)
            self.assertIn("kiri raw run", answers["kiri"].stderr)
            self.assertIn("cgroup2", answers["cgroup"].stdout)
        finally:
            if not registered:
                container.remove_distro()
        print(json.dumps({"home": str(home), "remove_after_use": remove,
                          "files": sorted(str(path.relative_to(home)) for path in home.rglob("*") if path.is_file())}))
        self.assertEqual(user_settings(), before)


if __name__ == "__main__":
    unittest.main()
