"""The container operation: the five guarantees, each against a fake Docker-compatible command line.

The fake never runs the command it is given: it records every call, keeps what `cp -`
sends and plays a few scripted commands (`emit`, `copy`, `sleep`, `exit`). A named volume is a
folder: a container gets its content at create and gives it back at rm. Two smoke tests at
the end use a real engine and run only with DAODAN_CONTAINER_SMOKE=1.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import egress  # noqa: E402

FAKE_CLI = r'''
import io, json, shutil, sys, tarfile, time
from pathlib import Path

state = Path(sys.argv[1])
args = sys.argv[2:]
with (state / "calls.jsonl").open("a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\n")
VALUED = {"--name", "--network", "--memory", "--memory-swap", "--pids-limit", "--cpus", "--security-opt", "-w", "-e",
          "-v"}
box = lambda name: state / "containers" / name
volume = lambda name: state / "volumes" / name
verb = args[0] if args else ""
if verb == "version" or verb == "info":
    print("linux")
elif verb == "create":
    rest, mounts = args[1:], []
    while rest[0] in VALUED:
        if rest[0] == "-v":
            mounts.append(rest[1].split(":", 1))
        rest = rest[2:]
    image, command = rest[0], rest[1:]
    name = args[args.index("--name") + 1]
    (box(name)).mkdir(parents=True)
    saved = state / "images" / image.replace(":", "_")
    if saved.is_dir():
        shutil.copytree(saved, box(name) / "fs")
    else:
        (box(name) / "fs").mkdir()
    for source, target in mounts:
        if not volume(source).is_dir():
            sys.exit("Error: no such volume " + source)
        shutil.copytree(volume(source), box(name) / "fs" / target.lstrip("/"), dirs_exist_ok=True)
    (box(name) / "command.json").write_text(json.dumps(command))
    (box(name) / "mounts.json").write_text(json.dumps(mounts))
    print(name)
elif verb == "rm":
    name = args[-1]
    mounts = json.loads((box(name) / "mounts.json").read_text()) if (box(name) / "mounts.json").is_file() else []
    for source, target in mounts:
        if volume(source).is_dir():
            shutil.rmtree(volume(source))
            held = box(name) / "fs" / target.lstrip("/")
            shutil.copytree(held, volume(source)) if held.is_dir() else volume(source).mkdir()
elif verb == "volume":
    action, name = args[1], args[2]
    if action == "create":
        volume(name).mkdir(parents=True)
        print(name)
    elif action == "inspect":
        sys.exit(0 if volume(name).is_dir() else 1)
    elif action == "rm":
        if not volume(name).is_dir():
            sys.exit("Error: no such volume " + name)
        shutil.rmtree(volume(name))
elif verb == "cp" and args[1] == "-":
    name = args[2].split(":")[0]
    data = sys.stdin.buffer.read()
    (box(name) / "copy.tar").write_bytes(data)
    with tarfile.open(fileobj=io.BytesIO(data)) as bundle:
        bundle.extractall(box(name) / "fs", filter="data")
elif verb == "cp" and args[1] != "-" and (state / "served.tar").is_file():  # as a hostile container would
    sys.stdout.buffer.write((state / "served.tar").read_bytes())
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
    elif command[:1] == ["copy"]:
        for source, target in zip(command[1::2], command[2::2]):
            target = box(name) / "fs" / target.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(box(name) / "fs" / source.lstrip("/"), target)
    elif command[:1] == ["sleep"]:
        time.sleep(float(command[1]))
    elif command[:1] == ["exit"]:
        sys.exit(int(command[1]))
    elif command[:1] == ["python3"]:  # a script of Daodan's (the reader of the .env files), run for real in /work
        import subprocess
        sys.exit(subprocess.run([sys.executable, *command[1:]], cwd=box(name) / "fs" / "work").returncode)
elif verb == "commit":
    if (state / "no-commit").exists():
        sys.exit("docker: 'commit' is not a docker command.")
    shutil.copytree(box(args[1]) / "fs", state / "images" / args[2].replace(":", "_"))
elif verb == "image" and args[1] == "rm":
    shutil.rmtree(state / "images" / args[-1].replace(":", "_"), ignore_errors=True)
elif verb == "logs":
    print("ready 3128")
    if (state / "refused.log").is_file():  # what the proxy said of the hosts it refused
        sys.stdout.write((state / "refused.log").read_text())
'''


def tree_digest(root: Path) -> dict[str, str]:
    """Every file under `root` but `.git`, with the sha256 of its bytes."""
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file() and ".git" not in path.relative_to(root).parts}


def unfixed_block(self, count):
    """`TarInfo._block` as CPython had it before its fix of CVE-2025-8194: a negative count goes back."""
    blocks, remainder = divmod(count, tarfile.BLOCKSIZE)
    return (blocks + 1 if remainder else blocks) * tarfile.BLOCKSIZE


def negative_size_tar() -> bytes:
    """A file, then a header whose size is -512. CPython before its fix reads that header again forever
    (CVE-2025-8194); after it, the archive silently ends there."""
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
        first = tarfile.TarInfo("out/a.txt")
        first.size = 1
        bundle.addfile(first, io.BytesIO(b"a"))
        bundle.addfile(tarfile.TarInfo("out/again"), io.BytesIO(b""))
    raw = bytearray(data.getvalue())
    at = 2 * tarfile.BLOCKSIZE  # the first header and its one block of data
    raw[at + 124:at + 136] = b"\xff" + (256**11 - 512).to_bytes(11, "big")  # base-256: -512
    raw[at + 148:at + 156] = b" " * 8
    raw[at + 148:at + 155] = b"%06o\0" % sum(raw[at:at + tarfile.BLOCKSIZE])
    return bytes(raw)


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
        self.registry = self.scratch / "registry"
        patcher = mock.patch.object(container, "volume_registry", return_value=self.registry)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, {"DAODAN_SHARED_DIR": str(self.scratch / "shared")})  # egress.json lives there
        env.start()
        self.addCleanup(env.stop)
        egress.PENDING.clear()
        egress.SESSIONS.clear()
        lookup = mock.patch.object(egress, "resolve", side_effect=lambda rows, *_: [  # no lookup in a test
            {**row, "address": None, "network": False} for row in rows])
        lookup.start()
        self.addCleanup(lookup.stop)
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

    def volumes(self) -> list[str]:
        """The volumes the runs created, in order."""
        return [call[2] for call in self.calls() if call[:2] == ["volume", "create"]]

    @staticmethod
    def mounts(call: list[str]) -> list[str]:
        return [call[index + 1] for index, token in enumerate(call) if token == "-v"]

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

    def serve(self, *members: tuple[str, bytes | str, str]) -> None:
        """The tar the fake hands back for any output: (name, data or link target, kind)."""
        with tarfile.open(self.state / "served.tar", "w") as bundle:
            for name, data, kind in members:
                entry = tarfile.TarInfo(name)
                if kind == "file":
                    entry.size = len(data)
                    bundle.addfile(entry, io.BytesIO(data))
                    continue
                entry.type = {"dir": tarfile.DIRTYPE, "symlink": tarfile.SYMTYPE, "hardlink": tarfile.LNKTYPE,
                              "fifo": tarfile.FIFOTYPE, "device": tarfile.CHRTYPE}[kind]
                entry.linkname = data if kind in ("symlink", "hardlink") else ""
                bundle.addfile(entry)

    def test_an_output_holding_anything_but_files_and_folders_is_refused(self):
        for kind, target in (("symlink", "../../outside"), ("symlink", "inside.txt"), ("hardlink", "out/a.txt"),
                             ("fifo", ""), ("device", "")):
            with self.subTest(kind=kind, target=target):
                shutil.rmtree(self.out, ignore_errors=True)
                self.serve(("out", "", "dir"), ("out/a.txt", b"a", "file"), ("out/odd", target, kind))
                result = self.run_operation(["exit", "0"], outputs=["/out"])
                self.assertEqual(result["state"], "failed", result)
                self.assertIn("not regular files", result["cause"])
                self.assertFalse((self.out / "out").exists())
                self.assertEqual([p.name for p in self.out.iterdir() if p.name.startswith(".incoming")], [])

    def test_outputs_are_summed_against_the_cap_before_anything_is_unpacked(self):
        self.serve(("out", "", "dir"), ("out/a.bin", b"x" * 600, "file"), ("out/b.bin", b"y" * 600, "file"))
        with mock.patch.object(container, "OUTPUT_CAP", 1000):
            result = self.run_operation(["exit", "0"], outputs=["/out"])
        self.assertEqual(result["state"], "failed", result)
        self.assertIn("1000", result["cause"])
        self.assertFalse((self.out / "out").exists())

    def test_an_archive_longer_than_the_cap_is_cut_while_it_streams(self):
        self.serve(("out", "", "dir"), ("out/a.bin", b"x" * 5000, "file"))
        with mock.patch.object(container, "OUTPUT_CAP", 1000), mock.patch.object(container, "STREAM_SLACK", 0):
            result = self.run_operation(["exit", "0"], outputs=["/out"])
        self.assertEqual(result["state"], "failed", result)
        self.assertIn("is over the 1000 bytes", result["cause"])
        self.assertFalse((self.out / "out").exists())

    def test_a_member_named_twice_is_refused(self):
        self.serve(("out", "", "dir"), ("out/a.txt", b"first", "file"), ("out/a.txt", b"second", "file"))
        result = self.run_operation(["exit", "0"], outputs=["/out"])
        self.assertEqual(result["state"], "failed", result)
        self.assertFalse((self.out / "out").exists())

    def test_an_output_never_replaces_a_file_already_in_the_output_folder(self):
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "index.scip").write_bytes(b"earlier")
        self.serve(("index.scip", b"later", "file"))
        result = self.run_operation(["exit", "0"], outputs=["/out"])
        self.assertEqual(result["state"], "failed", result)
        self.assertEqual((self.out / "index.scip").read_bytes(), b"earlier")

    def test_an_output_never_replaces_a_file_of_the_run(self):
        self.serve((container.RECORD_NAME, b'{"phase": "forged"}\n', "file"))
        result = self.run_operation(["exit", "0"], outputs=["/out"])
        self.assertEqual(result["state"], "failed", result)
        rows = (self.out / container.RECORD_NAME).read_text(encoding="utf-8")
        self.assertNotIn("forged", rows)

    def bounded(self, outputs: list[str], seconds: int = 30) -> dict:
        """The operation bringing back `outputs`, which must end within `seconds`."""
        box = {}
        worker = threading.Thread(target=lambda: box.update(result=self.run_operation(["exit", "0"], outputs=outputs)),
                                  daemon=True)
        worker.start()
        worker.join(seconds)
        self.assertFalse(worker.is_alive(), f"the operation did not end within {seconds} s")
        return box["result"]

    def test_outputs_are_written_by_daodan_never_by_tarfile_extraction(self):
        refuse = mock.Mock(side_effect=AssertionError("tarfile extraction called"))
        with mock.patch.object(tarfile.TarFile, "extractall", refuse), \
                mock.patch.object(tarfile.TarFile, "extract", refuse):
            result = self.run_operation(["emit", "/out/r.txt", "hello"], outputs=["/out/r.txt"])
        self.assertEqual(result["state"], "done", result)
        self.assertEqual((self.out / "r.txt").read_text(), "hello")

    def test_an_output_naming_a_place_outside_its_folder_is_refused(self):
        for name in ("../escaped.txt", "out/../../escaped.txt", "/escaped.txt", "out\\..\\escaped.txt",
                     "C:escaped.txt", "out/CON", "out/trailing.", "out/a\x01b"):
            with self.subTest(name=name):
                shutil.rmtree(self.out, ignore_errors=True)
                self.serve(("out", "", "dir"), ("out/a.txt", b"a", "file"), (name, b"x", "file"))
                result = self.bounded(["/out"])
                self.assertEqual(result["state"], "failed", result)
                self.assertIn("name", result["cause"])
                self.assertFalse((self.out / "out").exists())
                self.assertEqual(list(self.scratch.rglob("escaped.txt")), [])
                self.assertFalse(Path("/escaped.txt").exists())
                self.assertEqual([p.name for p in self.out.iterdir() if p.name.startswith(".incoming")], [])

    def test_a_header_with_a_negative_size_fails_and_ends_on_any_python(self):
        for hook in ("_block", "_proc_pax", "_proc_gnulong"):  # the reader's methods Daodan guards, 3.12 to 3.14
            self.assertTrue(callable(getattr(tarfile.TarInfo, hook, None)), hook)
        (self.state / "served.tar").write_bytes(negative_size_tar())
        for label, block in (("this Python", tarfile.TarInfo._block), ("before the fix", unfixed_block)):
            with self.subTest(label), mock.patch.object(tarfile.TarInfo, "_block", block):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.bounded(["/out"])
                self.assertEqual(result["state"], "failed", result)
                self.assertIn("negative", result["cause"])
                self.assertFalse((self.out / "out").exists())

    def test_an_oversized_header_is_refused_before_it_is_parsed(self):
        for kind in ("pax", "gnu long name"):
            with self.subTest(kind):
                shutil.rmtree(self.out, ignore_errors=True)
                data = io.BytesIO()
                pax = kind == "pax"
                with tarfile.open(fileobj=data, mode="w",
                                  format=tarfile.PAX_FORMAT if pax else tarfile.GNU_FORMAT) as bundle:
                    entry = tarfile.TarInfo("out/a.txt" if pax else "out/" + "a" * (container.HEADER_CAP + 1))
                    entry.size = 1
                    if pax:
                        entry.pax_headers = {"comment": "1" * (container.HEADER_CAP + 1)}
                    bundle.addfile(entry, io.BytesIO(b"a"))
                (self.state / "served.tar").write_bytes(data.getvalue())
                result = self.bounded(["/out"])
                self.assertEqual(result["state"], "failed", result)
                self.assertIn("header", result["cause"])
                self.assertFalse((self.out / "out").exists())

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

    def test_credential_files_stay_out_of_the_copy_in_every_folder_tracked_or_not(self):
        written = [".npmrc", "packages/app/.npmrc", ".pypirc", "tools/.netrc"]
        for name in written:
            (self.project / name).parent.mkdir(parents=True, exist_ok=True)
            (self.project / name).write_text("//registry.npmjs.org/:_authToken=secret\n", encoding="utf-8")
        if self.git:
            git = [self.git, "-C", str(self.project)]
            subprocess.run([*git, "add", "-f", *written], check=True, capture_output=True)
        self.run_operation(["exit", "0"])
        name = self.created()[0][self.created()[0].index("--name") + 1]
        with tarfile.open(self.state / "containers" / name / "copy.tar") as bundle:
            names = [member.name for member in bundle.getmembers()]
        for secret in written:
            self.assertNotIn(f"work/{secret}", names)

    def test_copy_holds_what_git_tracks_in_dot_directories_with_the_mode_git_records(self):
        if not self.git:
            self.skipTest("git is needed to ask what Git tracks")
        written = {".mvn/wrapper/maven-wrapper.properties": "distributionUrl=x\n", ".mvn/jvm.config": "-Xmx1g\n",
                   "mvnw": "#!/bin/sh\n", ".mvn/cache/entry": "ignored by git\n"}
        for name, text in written.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (self.project / "mvnw").chmod(0o755)
        with (self.project / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write(".mvn/cache/\n")
        git = [self.git, "-C", str(self.project)]
        subprocess.run([*git, "add", ".gitignore", ".mvn/wrapper/maven-wrapper.properties", ".mvn/jvm.config", ".env"],
                       check=True)
        subprocess.run([*git, "add", "--chmod=+x", "mvnw"], check=True)
        self.run_operation(["exit", "0"])
        [run] = [call for call in self.created() if container.PROXY_IMAGE not in call]  # not the .env reader's
        name = run[run.index("--name") + 1]
        with tarfile.open(self.state / "containers" / name / "copy.tar") as bundle:
            files = {member.name: member.mode for member in bundle.getmembers() if member.isfile()}
        self.assertEqual(sorted(files), ["work/.env", "work/.gitignore", "work/.mvn/jvm.config",  # .env: tracked
                                         "work/.mvn/wrapper/maven-wrapper.properties", "work/data/fixture.csv",
                                         "work/mvnw", "work/package.json", "work/src/app.js"])
        self.assertEqual(files["work/mvnw"], 0o755)
        self.assertEqual(files["work/.mvn/jvm.config"], 0o644)

    def test_a_tracked_link_into_the_project_is_copied_as_that_link_and_one_out_of_it_is_a_gap(self):
        """mix-real-python-semver: tests/coerce.py is a link Git tracks to docs/advanced/coerce.py, and the tests
        import it. A tracked link whose target lies inside the project enters the copy as that link, never followed;
        one whose target lies outside it (above it, or an absolute path) stays out, a gap of the run naming the link
        and its target. Where Git checks a link out as a small file holding its target (core.symlinks false, as on
        Windows), the copy holds the link all the same."""
        if not self.git:
            self.skipTest("git is needed to ask what Git tracks")
        (self.project / "docs/advanced").mkdir(parents=True)
        (self.project / "docs/advanced/coerce.py").write_text("def coerce(): pass\n", encoding="utf-8")
        (self.project / "tests").mkdir()
        links = {"tests/coerce.py": "../docs/advanced/coerce.py", "tests/plain.py": "../docs/advanced/coerce.py",
                 "tests/up.py": "../../outside.py", "tests/root.py": "/etc/passwd", "docs/all": "advanced"}
        git = [self.git, "-C", str(self.project)]
        for name, target in links.items():
            path = self.project / name
            if name == "tests/plain.py":
                path.write_text(target, encoding="utf-8")  # as Git writes a link it cannot make
            else:
                os.symlink(target, path)
            blob = subprocess.run([*git, "hash-object", "-w", "--stdin"], input=target, capture_output=True,
                                  text=True, check=True).stdout.strip()
            subprocess.run([*git, "update-index", "--add", "--cacheinfo", f"120000,{blob},{name}"], check=True)
        subprocess.run([*git, "add", "docs/advanced/coerce.py"], check=True)
        result = self.run_operation(["exit", "0"])
        name = self.created()[0][self.created()[0].index("--name") + 1]
        with tarfile.open(self.state / "containers" / name / "copy.tar") as bundle:
            members = {member.name: member for member in bundle.getmembers()}
        copied = {name: member.linkname for name, member in members.items() if member.issym()}
        self.assertEqual(copied, {"work/tests/coerce.py": "../docs/advanced/coerce.py",
                                  "work/tests/plain.py": "../docs/advanced/coerce.py", "work/docs/all": "advanced"})
        self.assertTrue(members["work/docs/advanced/coerce.py"].isfile() and members["work/tests"].isdir())
        self.assertNotIn("work/tests/up.py", members)
        self.assertNotIn("work/tests/root.py", members)
        self.assertEqual({gap["path"] for gap in result["gaps"] if gap["kind"] == "file_withheld"},
                         {".env", "src/secrets.json"})  # files Daodan never reads, which Git does not track
        self.assertEqual([(gap["kind"], gap["path"], gap["target"]) for gap in result["gaps"]
                          if gap["kind"] == "link_outside"], [
            ("link_outside", "tests/root.py", "/etc/passwd"), ("link_outside", "tests/up.py", "../../outside.py")])
        self.assertIn("../../outside.py", [gap for gap in result["gaps"] if gap["kind"] == "link_outside"][1]["detail"])

    def test_a_work_tree_git_does_not_answer_for_is_a_gap_not_a_copy_of_ignored_files(self):
        (self.project / ".git").mkdir(exist_ok=True)
        refusing = self.scratch / ("git.cmd" if os.name == "nt" else "git")
        script = "import sys; sys.stderr.write('fatal: detected dubious ownership'); sys.exit(128)"
        if os.name == "nt":
            refusing.write_text(f'@"{sys.executable}" -c "{script}"\r\n')
        else:
            refusing.write_text(f'#!/bin/sh\nexec "{sys.executable}" -c "{script}"\n')
            refusing.chmod(0o755)
        for git in (None, str(refusing)):
            with self.subTest(git=git), mock.patch.object(container, "git_executable", return_value=git):
                result = self.run_operation(["exit", "0"])
                self.assertEqual(result["state"], "gap", result)
                self.assertIn("Git", result["cause"])
                self.assertTrue(result["remedy"])
        self.assertEqual(self.created(), [])

    def test_a_project_outside_any_work_tree_is_copied_without_git(self):
        loose = self.scratch / "loose"
        (loose / "src").mkdir(parents=True)
        (loose / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        with mock.patch.object(container, "git_executable", return_value=None), \
                mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = container.run_in_container(loose, ["exit", "0"], image="fake/runtime:1", out_dir=self.out,
                                                engine=self.engine)
        self.assertEqual(result["state"], "done", result)

    def test_inputs_reach_the_container_at_their_own_paths(self):
        tool = self.scratch / "served" / "tool.zip"
        tool.parent.mkdir()
        tool.write_bytes(b"the distribution")
        result = self.run_operation(["exit", "0"], inputs={"/daodan/tools/tool.zip": tool})
        self.assertEqual(result["state"], "done", result)
        name = self.created()[0][self.created()[0].index("--name") + 1]
        self.assertEqual((self.state / "containers" / name / "fs" / "daodan/tools/tool.zip").read_bytes(),
                         b"the distribution")

    def test_inputs_are_asked_for_only_once_an_engine_answers_and_may_be_a_gap(self):
        asked = []

        def refuse():
            asked.append(1)
            raise container.Gap("the wrapper names a host that is not the distribution site", "fix the wrapper")

        with mock.patch.object(container, "find_engine", side_effect=container.Gap("no engine", "start one")), \
                mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = container.run_in_container(self.project, ["exit", "0"], image="fake/runtime:1", out_dir=self.out,
                                                inputs=refuse)
        self.assertEqual((result["state"], result["cause"], asked), ("gap", "no engine", []))
        result = self.run_operation(["exit", "0"], prepare=["exit", "0"], inputs=refuse)
        self.assertEqual((result["state"], result["remedy"], asked), ("gap", "fix the wrapper", [1]))
        self.assertEqual(self.created(), [])
        rows = (self.out / container.RECORD_NAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(json.loads(rows[-1])["outcome"], "gap")

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
        self.assertIn("fake/runtime:1", prepare)
        self.assertIn("fake/runtime:1", execute)
        self.assertEqual([call for call in calls if call[0] in ("commit", "rmi", "image")], [])
        self.assertEqual([call[:2] for call in calls if call[0] == "cp" and call[1] == "-"], [["cp", "-"]])
        self.assertIn(["network", "rm", network], calls)

    def test_the_preparation_hands_its_state_to_execution_in_two_named_volumes(self):
        seen, real = [], container.cli

        def spy(engine, *args, **options):
            if args[:2] == ("volume", "create"):  # the name is on record before the volume exists
                seen.append(any(args[2] in entry.read_text(encoding="utf-8") for entry in self.registry.glob("*")))
            return real(engine, *args, **options)

        with mock.patch.object(container, "cli", spy):
            result = self.run_operation(
                ["copy", "/daodan/state/built.txt", "/out/built.txt", "/work/src/app.js", "/out/app.js"],
                prepare=["emit", "/daodan/state/built.txt", "built"], outputs=["/out"])
        self.assertEqual(result["state"], "done", result)
        self.assertEqual((self.out / "out/built.txt").read_text(), "built")
        self.assertEqual((self.out / "out/app.js").read_text(), "export const run = () => 1;\n")
        work, state = self.volumes()
        self.assertRegex(work, r"^daodan-work-[0-9a-f]{12}$")
        self.assertEqual(state, "daodan-state-" + work.rsplit("-", 1)[1])
        self.assertEqual(seen, [True, True])
        proxy, prepare, execute = self.created()
        self.assertEqual(self.mounts(proxy), [])
        for call in (prepare, execute):
            self.assertEqual(self.mounts(call), [f"{work}:/work", f"{state}:/daodan/state"])
        calls = self.calls()
        removed = [index for index, call in enumerate(calls) if call[:2] == ["volume", "rm"]]
        self.assertEqual([calls[index][2] for index in removed], [work, state])
        self.assertGreater(removed[0], calls.index(["rm", "-f", execute[execute.index("--name") + 1]]))
        self.assertEqual(list(self.registry.glob("*")), [])

    def test_the_volumes_are_removed_by_name_after_a_failed_preparation_or_a_timeout(self):
        for prepare, command, timeout in ((["exit", "3"], ["exit", "0"], 600), (["exit", "0"], ["sleep", "30"], 2)):
            with self.subTest(prepare=prepare, command=command):
                held = len(self.volumes())
                result = self.run_operation(command, prepare=prepare, timeout=timeout)
                self.assertEqual(result["state"], "failed" if prepare == ["exit", "3"] else "timeout")
                made = self.volumes()[held:]
                self.assertEqual(len(made), 2)
                self.assertEqual([call[2] for call in self.calls() if call[:2] == ["volume", "rm"]][-2:], made)
                self.assertFalse((self.state / "volumes" / made[0]).exists())
                self.assertEqual(list(self.registry.glob("*")), [])

    def test_a_volume_that_cannot_be_removed_stays_on_record(self):
        real = container.cli

        def stuck(engine, *args, **options):
            if args[:2] == ("volume", "rm"):
                return subprocess.CompletedProcess([*engine.argv, *args], 1, b"", b"volume is in use")
            return real(engine, *args, **options)

        with mock.patch.object(container, "cli", stuck):
            self.run_operation(["exit", "0"], prepare=["exit", "0"])
        entries = [json.loads(entry.read_text(encoding="utf-8")) for entry in self.registry.glob("*")]
        self.assertEqual([entry["volumes"] for entry in entries], [self.volumes()])
        self.assertEqual((entries[0]["engine"], entries[0]["pid"]), ("fake", os.getpid()))

    def test_the_volumes_a_killed_run_left_are_removed_by_name_at_the_next_run(self):
        dead = int(subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True,
                                  text=True, check=True).stdout)
        entries = {"killed": ("fake", dead, ["daodan-work-aaaaaaaaaaaa", "daodan-state-aaaaaaaaaaaa"]),
                   "running": ("fake", os.getpid(), ["daodan-work-bbbbbbbbbbbb", "daodan-state-bbbbbbbbbbbb"]),
                   "other-engine": ("docker", dead, ["daodan-work-cccccccccccc"]),
                   "not-daodan": ("fake", dead, ["projectdb", "daodan-state-dddddddddddd"])}
        self.registry.mkdir()
        for token, (engine, pid, names) in entries.items():
            (self.registry / f"{token}.json").write_text(json.dumps({"engine": engine, "pid": pid, "volumes": names}),
                                                         encoding="utf-8")
            for name in names:
                (self.state / "volumes" / name).mkdir(parents=True)
        result = self.run_operation(["exit", "0"])
        self.assertEqual(result["state"], "done", result)
        volume_calls = [call for call in self.calls() if call[0] == "volume"]
        self.assertEqual(sorted(call[2] for call in volume_calls if call[1] == "rm"),
                         ["daodan-state-aaaaaaaaaaaa", "daodan-state-dddddddddddd", "daodan-work-aaaaaaaaaaaa"])
        self.assertEqual({call[1] for call in volume_calls} - {"rm", "inspect"}, set())
        self.assertFalse(any("projectdb" in call for call in self.calls()))
        self.assertEqual(sorted(entry.stem for entry in self.registry.glob("*")), ["other-engine", "running"])
        self.assertTrue((self.state / "volumes" / "projectdb").is_dir())

    def test_an_input_outside_the_volumes_or_an_output_inside_them_is_refused(self):
        tool = self.scratch / "tool.zip"
        tool.write_bytes(b"the distribution")
        with self.assertRaises(ValueError):  # it would stay in the preparation's container
            self.run_operation(["exit", "0"], prepare=["exit", "0"], inputs={"/app/tool.zip": tool})
        with self.assertRaises(ValueError):  # the engine cannot copy a file out of a volume
            self.run_operation(["exit", "0"], prepare=["exit", "0"], outputs=["/daodan/state/out"])
        self.assertEqual(self.created(), [])
        self.assertEqual(self.volumes(), [])

    def test_home_is_in_the_state_volume_unless_the_caller_gives_it(self):
        self.run_operation(["exit", "0"], prepare=["exit", "0"])
        self.run_operation(["exit", "0"], prepare=["exit", "0"], env={"HOME": "/root"})
        self.run_operation(["exit", "0"])
        homes = [[token for token in call if token.startswith("HOME=")] for call in self.created()
                 if "--network" in call]
        self.assertEqual(homes, [["HOME=/daodan/state/home"]] * 2 + [["HOME=/root"]] * 2 + [[]])

    def test_a_kept_root_hands_execution_everything_the_preparation_wrote_and_goes_by_name(self):
        """A Dockerfile's build stage installs into the image's own folders (`apk add` into /usr): with
        `keep_root`, execution starts from the preparation's container committed as `daodan-prepared-<token>`,
        on record before it exists, with no network, and the image is removed by name at the end."""
        seen, real = [], container.cli

        def spy(engine, *args, **options):
            if args[:1] == ("commit",):
                seen.append(any(args[2] in entry.read_text(encoding="utf-8") for entry in self.registry.glob("*")))
            return real(engine, *args, **options)

        with mock.patch.object(container, "cli", spy):
            result = self.run_operation(["copy", "/usr/lib/built.txt", "/out/built.txt"], outputs=["/out/built.txt"],
                                        prepare=["emit", "/usr/lib/built.txt", "installed"], keep_root=True)
        self.assertEqual(result["state"], "done", result)
        self.assertEqual((self.out / "built.txt").read_text(), "installed")
        calls = self.calls()
        [commit] = [call for call in calls if call[0] == "commit"]
        image = commit[2]
        self.assertRegex(image, r"^daodan-prepared-[0-9a-f]{12}$")
        self.assertEqual(seen, [True])
        _proxy, prepare, execute = self.created()
        self.assertEqual(commit[1], prepare[prepare.index("--name") + 1])
        self.assertIn(image, execute)
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        self.assertLess(calls.index(commit), calls.index(["rm", "-f", commit[1]]))
        self.assertIn(["image", "rm", "-f", image], calls)
        self.assertFalse((self.state / "images" / image).exists())
        rows = [json.loads(line) for line in (self.out / container.RECORD_NAME).read_text().splitlines()]
        self.assertEqual([(r.get("image"), r.get("from")) for r in rows if r.get("phase") == "execute"],
                         [(image, "fake/runtime:1")])  # the record names the pinned base it came from
        self.assertEqual(list(self.registry.glob("*")), [])

    def test_an_engine_that_cannot_commit_a_container_is_a_gap_with_its_answer(self):
        (self.state / "no-commit").write_text("", encoding="utf-8")
        result = self.run_operation(["exit", "0"], prepare=["exit", "0"], keep_root=True)
        self.assertEqual(result["state"], "gap", result)
        self.assertIn("'commit' is not a docker command", result["cause"])
        self.assertEqual(len(self.created()), 2)  # the proxy and the preparation: no execution
        self.assertEqual(list(self.registry.glob("*")), [])

    def test_the_prepared_images_a_killed_run_left_are_removed_by_name_at_the_next_run(self):
        dead = int(subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True,
                                  text=True, check=True).stdout)
        self.registry.mkdir()
        (self.registry / "killed.json").write_text(json.dumps({
            "engine": "fake", "pid": dead, "volumes": ["daodan-work-aaaaaaaaaaaa"],
            "images": ["daodan-prepared-aaaaaaaaaaaa", "project/app:1"]}), encoding="utf-8")
        (self.state / "volumes" / "daodan-work-aaaaaaaaaaaa").mkdir(parents=True)
        self.assertEqual(self.run_operation(["exit", "0"])["state"], "done")
        calls = self.calls()
        self.assertIn(["image", "rm", "-f", "daodan-prepared-aaaaaaaaaaaa"], calls)
        self.assertFalse(any("project/app:1" in call for call in calls))
        self.assertEqual(list(self.registry.glob("*")), [])

    def test_the_proxy_opens_only_the_hosts_egress_allows_and_the_rest_asks(self):
        """A canonical host and one the user approved for this project pass; any other host, GitHub's and a host the
        project declares among them, is left to the proxy to refuse: it is a request to answer."""
        hosts = ("registry.npmjs.org", "git.example.com", "github.com", "http://deb.example.com", "blocked.example.com",
                 "http://archive.ubuntu.com")
        egress.save({"whitelist": {str(self.project): ["git.example.com", "deb.example.com"]},
                     "blacklist": ["blocked.example.com"]})
        self.assertEqual(self.run_operation(["exit", "0"], prepare=["exit", "0"], registries=hosts)["state"], "done")
        [proxy, *_] = self.created()
        self.assertEqual(proxy[proxy.index("3128") + 1:], ["registry.npmjs.org", "git.example.com",
                                                          "http://deb.example.com", "http://archive.ubuntu.com"])
        egress.save(egress.answer(egress.load(), egress.session(str(self.project)), "github.com",
                                  str(self.project), "always")[0])
        self.assertEqual(self.run_operation(["exit", "0"], prepare=["exit", "0"], registries=hosts)["state"], "done")
        self.assertIn("github.com", self.created()[3])  # the second run's proxy

    def test_a_refused_host_is_a_request_and_a_step_that_fails_with_one_needs_approval(self):
        (self.state / "refused.log").write_text(
            '@@daodan-refused {"host": "git.example.com", "port": "443"}\n'
            '@@daodan-refused {"host": "blocked.example.com", "port": "443"}\n', encoding="utf-8")
        egress.save({"whitelist": {}, "blacklist": ["blocked.example.com"]})
        done = self.run_operation(["exit", "0"], prepare=["exit", "0"])
        self.assertEqual(done["state"], "done")  # a step that succeeds keeps its result, the request stays visible
        self.assertEqual([row["host"] for row in done["asked"]], ["git.example.com"])
        self.assertEqual([gap["kind"] for gap in done["gaps"] if gap["kind"] != "file_withheld"], ["host_denied"])
        self.assertEqual([row["host"] for row in egress.pending(str(self.project))], ["git.example.com"])
        failed = self.run_operation(["exit", "0"], prepare=["exit", "3"])
        gaps = [gap for gap in failed["gaps"] if gap["kind"] != "file_withheld"]
        self.assertEqual([gap["kind"] for gap in gaps], ["host_denied", "approval_required"])
        self.assertEqual(gaps[1]["hosts"], ["git.example.com"])
        self.assertEqual(len(egress.pending(str(self.project))), 1)  # once, however many runs asked

    def test_run_commands_says_approval_required_when_a_command_failed_where_a_host_was_asked(self):
        asked = [{"host": "git.example.com", "port": "443", "address": None, "network": False, "declared_in": []}]
        for code, kinds in (("1", ["approval_required"]), ("0", [])):
            out = self.scratch / f"commands-{code}"

            def ran(*_, **__):  # the container's answer: the command's code, in the folder the run brings back
                (out / "results" / "0").mkdir(parents=True)
                (out / "results" / "0" / "code").write_text(code + "\n", encoding="utf-8")
                return {"state": "done", "asked": asked}
            with mock.patch.object(container, "run_in_container", ran):
                result = container.run_commands(self.project, [{"tool": "t", "argv": ["x"]}], image="fake/runtime:1",
                                                out_dir=out)
            self.assertEqual([gap["kind"] for gap in result.get("gaps", [])], kinds)

    def test_the_hosts_the_proxy_refused_come_back_in_the_result_even_when_the_preparation_fails(self):
        (self.state / "refused.log").write_text(
            '@@daodan-refused {"host": "git.example.com", "port": "443"}\nnoise\n'
            '@@daodan-refused {"host": "git.example.com", "port": "443"}\n'
            '@@daodan-refused {"host": "10.0.0.5", "port": "8080"}\n', encoding="utf-8")
        wanted = [{"host": "git.example.com", "port": "443"}, {"host": "10.0.0.5", "port": "8080"}]
        done = self.run_operation(["exit", "0"], prepare=["exit", "0"])
        self.assertEqual((done["state"], done["refused"]), ("done", wanted))
        failed = self.run_operation(["exit", "0"], prepare=["exit", "3"])
        self.assertEqual((failed["state"], failed["refused"]), ("failed", wanted))
        (self.state / "refused.log").unlink()
        self.assertNotIn("refused", self.run_operation(["exit", "0"], prepare=["exit", "0"]))
        self.assertNotIn("refused", self.run_operation(["exit", "0"]))  # no preparation, no proxy

    def test_failed_preparation_stops_before_execution(self):
        result = self.run_operation(["exit", "0"], prepare=["exit", "3"])
        self.assertEqual(result["state"], "failed")
        self.assertIn("3", result["cause"])
        self.assertEqual(len(self.created()), 2)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["volume", "rm"]]), 2)

    def test_the_registries_are_the_hosts_of_the_package_managers_file(self):
        data = json.loads((Path(container.__file__).resolve().parents[1] / "data/package-managers.json")
                          .read_text(encoding="utf-8"))
        hosts = [host for part in ("managers", "toolchains") for names in data[part].values() for host in names]
        self.assertIn("oldid=", data["source"])  # the revision of Wikipedia's list the names were read from
        self.assertEqual(sorted(container.REGISTRIES), sorted(set(hosts)))
        self.assertEqual(len(hosts), len(set(hosts)))  # a host under one manager only
        for host in hosts:  # names only (`http://` for an apt archive): a port, a path or a wildcard would widen
            self.assertRegex(host, r"\A(http://)?[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+\Z")
        self.assertLessEqual({"registry.npmjs.org", "pypi.org", "http://archive.ubuntu.com", "nodejs.org",
                              "repo.yarnpkg.com", "download.visualstudio.microsoft.com"}, set(hosts))
        for host in hosts:  # hosts that take more than a package publish: a preparation runs project code
            self.assertFalse(host == "ghcr.io" or "github" in host or "docker" in host, host)
        for host in ("storage.googleapis.com", "aka.ms", "cache-redirector.jetbrains.com", "scala.jfrog.io",
                     "d2xrhe97vsfxuc.cloudfront.net", "dotnetcli.azureedge.net", "playwright.azureedge.net"):
            self.assertNotIn(host, hosts)  # generic hosts and the azureedge ones ask (owner, 27 November 2026)

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
        self.assertTrue(ask(b"CONNECT 169.254.169.254:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))
        self.assertTrue(ask(b"GET http://10.0.0.1:8080/x HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))
        self.assertTrue(ask(b"CONNECT [::1]:443 HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))
        self.assertTrue(ask(b"GET http://[::1:80/x HTTP/1.1\r\n\r\n").startswith(b"HTTP/1.1 403"))  # not a URL
        self.assertTrue(ask(b"BREW\r\n\r\n").startswith(b"HTTP/1.1 403"))
        # each refusal is one line of the log, the host and port as asked and none resolved by the proxy
        lines = [json.loads(server.stdout.readline().split(" ", 1)[1]) for _ in range(8)]
        self.assertEqual(lines, [
            {"host": "example.com", "port": "443"}, {"host": "registry.npmjs.org", "port": "80"},
            {"host": "registry.npmjs.org", "port": "80"}, {"host": "169.254.169.254", "port": "443"},
            {"host": "10.0.0.1", "port": "8080"}, {"host": "[::1]", "port": "443"},
            {"host": "http://[::1:80/x", "port": ""}, {"host": "", "port": "80"}])

    def test_proxy_forwards_plain_http_to_an_apt_host_only_for_its_archive(self):
        """A base image's apt sources name their archive over plain HTTP, and apt checks the signed Release files and
        each package's hash: for a host given as `http://<host>` the proxy forwards a GET or HEAD of a `dists/` or
        `pool/` path to its port 80, one request a connection, and refuses any other path, method, port or host."""
        import http.server
        seen = []

        class Archive(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append((self.command, self.path, self.headers.get("Connection")))
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok" if self.command == "GET" else b"")

            do_HEAD, do_POST = do_GET, do_GET

            def log_message(self, *_):
                pass

        try:
            archive = http.server.ThreadingHTTPServer(("127.0.0.1", 80), Archive)
        except OSError as error:
            self.skipTest(f"an archive at 127.0.0.1:80 is needed: {error}")
        threading.Thread(target=archive.serve_forever, daemon=True).start()
        self.addCleanup(archive.server_close)
        self.addCleanup(archive.shutdown)
        server = subprocess.Popen([sys.executable, "-I", "-c", container.PROXY_SCRIPT, "0", "registry.npmjs.org",
                                   "http://127.0.0.1"], stdout=subprocess.PIPE, text=True)
        self.addCleanup(server.wait)
        self.addCleanup(server.kill)
        port = int(server.stdout.readline().split()[1])

        def ask(request: bytes) -> bytes:
            with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
                client.sendall(request)
                answer = b""
                while chunk := client.recv(4096):
                    answer += chunk
                return answer

        index = ask(b"GET http://127.0.0.1/debian/dists/trixie/InRelease HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                    b"Connection: keep-alive\r\n\r\nGET http://127.0.0.1/debian/evil HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        self.assertTrue(index.startswith(b"HTTP/1.0 200") and index.endswith(b"ok"), index)
        self.assertTrue(ask(b"HEAD http://127.0.0.1/debian/pool/main/c/cmake/cmake_3.31.deb HTTP/1.1\r\n\r\n")
                        .startswith(b"HTTP/1.0 200"))
        for refused in (b"GET http://127.0.0.1/debian/evil HTTP/1.1", b"POST http://127.0.0.1/debian/dists/x HTTP/1.1",
                        b"GET http://127.0.0.1:8080/debian/dists/x HTTP/1.1",
                        b"GET http://127.0.0.1/debian/dists/../../secret HTTP/1.1",
                        b"GET http://127.0.0.1/debian/dists/x?y=1 HTTP/1.1",
                        b"GET http://registry.npmjs.org/debian/dists/x HTTP/1.1", b"CONNECT 127.0.0.1:443 HTTP/1.1"):
            self.assertTrue(ask(refused + b"\r\n\r\n").startswith(b"HTTP/1.1 403"), refused)
        self.assertEqual(seen, [("GET", "/debian/dists/trixie/InRelease", "close"),  # the next request goes nowhere
                                ("HEAD", "/debian/pool/main/c/cmake/cmake_3.31.deb", "close")])
        # only the refusals are said, each as asked; what the proxy forwarded says nothing
        said = [json.loads(server.stdout.readline().split(" ", 1)[1]) for _ in range(7)]
        self.assertEqual(said, [{"host": "127.0.0.1", "port": "80"}, {"host": "127.0.0.1", "port": "80"},
                                {"host": "127.0.0.1", "port": "8080"}, {"host": "127.0.0.1", "port": "80"},
                                {"host": "127.0.0.1", "port": "80"}, {"host": "registry.npmjs.org", "port": "80"},
                                {"host": "127.0.0.1", "port": "443"}])

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
        self.assertEqual(execute[execute.index("--security-opt") + 1], "no-new-privileges")
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

    # Commands as data: one container run, the registries' commands in the preparation.
    def test_commands_run_by_network_with_their_streams_apart_and_in_order(self):
        seeded = self.state / "images" / "fake" / "runtime_1" / "daodan/out/results"  # what the scripts leave
        for number, (code, out, err) in enumerate((("0", "go list\n", ""), ("3", "", "no such crate\n"))):
            (seeded / str(number)).mkdir(parents=True)
            for name, value in (("code", code + "\n"), ("stdout", out), ("stderr", err)):
                (seeded / str(number) / name).write_text(value, encoding="utf-8")
        commands = [{"tool": "go", "argv": ["go", "list", "-m", "all"], "cwd": ".", "network": "registries"},
                    {"tool": "cargo", "argv": ["cargo", "metadata", "--offline"], "cwd": "sub dir",
                     "env": {"CARGO_HOME": "/daodan/state/home/a b"}, "network": "none"}]
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = container.run_commands(self.project, commands, image="fake/runtime:1", out_dir=self.out,
                                            engine=self.engine)
        self.assertEqual(result["state"], "done", result)
        self.assertEqual(result["root"], "/work")
        self.assertEqual(result["results"], [{"returncode": 0, "stdout": "go list\n", "stderr": ""},
                                             {"returncode": 3, "stdout": "", "stderr": "no such crate\n"}])
        proxy, prepare, execute = self.created()
        early, late = prepare[-1], execute[-1]
        self.assertIn("go list -m all", early)
        self.assertNotIn("cargo", early)
        self.assertIn("cd '/work/sub dir'", late)
        self.assertIn("'CARGO_HOME=/daodan/state/home/a b' cargo metadata --offline", late)
        self.assertNotIn("go list", late)
        self.assertIn(f"{container.STATE}/results/0/stdout", early)  # kept for execution, which brings it out
        self.assertIn(f"cp -R {container.STATE}/results/. /daodan/out/results/", late)
        self.assertEqual(execute[execute.index("--network") + 1], "none")

    def test_without_a_registry_command_there_is_one_phase(self):
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = container.run_commands(self.project, [{"tool": "uv", "argv": ["uv", "tree", "--offline"]}],
                                            image="fake/runtime:1", out_dir=self.out, engine=self.engine)
        self.assertEqual(len(self.created()), 1)
        self.assertEqual(self.volumes(), [])
        self.assertEqual(result["results"], [{"returncode": None, "stdout": "", "stderr": ""}])

    def test_a_command_outside_the_copy_or_with_an_unknown_network_is_refused(self):
        for command in ({"argv": ["ls"], "cwd": "../elsewhere"}, {"argv": ["ls"], "cwd": "/etc"},
                        {"argv": ["ls"], "network": "internet"}, {"argv": []}):
            with self.subTest(command=command), self.assertRaises(ValueError):
                container.run_commands(self.project, [command], image="fake/runtime:1", out_dir=self.out,
                                       engine=self.engine)
        self.assertEqual(self.calls(), [])

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

    def test_beside_a_running_kiri_of_the_user_daodan_starts_its_own_in_a_network_of_its_own(self):
        """D-219: Kiri engines in WSL share the VM's network namespace, where each builds at start and removes at stop
        the nftables table `kiri`. Daodan's daemon runs in a network namespace of its own, joined to the outside by
        pasta (`DAEMON`), so beside the user's running Kiri Daodan starts its own: WSL is asked only about Daodan's
        distribution, what an earlier run left of it ends once the engine is Daodan's to use (the lock), and nothing
        names the user's distribution (the owner's rule: never use, restart, stop or reconfigure it)."""
        events = []

        def wsl(*args, timeout=120):
            events.append(("wsl", args))
            return subprocess.CompletedProcess(args, 0, b"kiri\nUbuntu\n", b"")

        class Daemon:
            def __init__(self, argv, **_):
                events.append(("start", tuple(argv)))

            def poll(self):
                return None

            def wait(self, timeout=None):
                return 0

        lock = types.SimpleNamespace(LK_NBLCK=2, locking=lambda *_: events.append(("lock", ())))
        answer = subprocess.CompletedProcess([], 0, b"linux\n", b"")
        with mock.patch.object(container.os, "name", "nt"), mock.patch.dict(os.environ, {"DAODAN_CONTAINER": ""}), \
                mock.patch.dict(sys.modules, {"msvcrt": lock}), \
                mock.patch.object(container, "program", side_effect=AssertionError("no engine of the user's")), \
                mock.patch.object(container, "wsl_executable", return_value="wsl.exe"), \
                mock.patch.object(container, "wsl", side_effect=wsl), \
                mock.patch.object(container, "engine_home", return_value=self.scratch / "home"), \
                mock.patch.object(container, "ensure_distro", return_value=(False, "2026.05.26-r0")), \
                mock.patch.object(container.subprocess, "Popen", Daemon), \
                mock.patch.object(container, "cli", return_value=answer):
            engine = container.find_engine()
            engine.stop()
        self.assertEqual(engine.name, f"daodan-kiri@{container.KIRI_VERSION}+pasta@2026.05.26-r0")  # in every record
        self.assertEqual(engine.argv[1:3] + engine.argv[-3:], ("-d", container.DISTRO, "/usr/bin/docker", "-H",
                                                               container.SOCKET))
        terminate = ("wsl", ("--terminate", container.DISTRO))
        self.assertEqual([kind for kind, _ in events], ["lock", "wsl", "start", "wsl"])
        self.assertEqual((events[1], events[3]), (terminate, terminate))
        started = events[2][1]
        self.assertEqual(started[1:3] + started[-3:], ("-d", container.DISTRO, "/bin/sh", "-c", container.DAEMON))
        self.assertNotIn("kiri", [arg for _, args in events for arg in args])
        netns = container.NETNS
        self.assertIn(f"unshare --net={netns} true", container.DAEMON)
        self.assertIn(f"--netns {netns}", container.DAEMON)  # pasta joins it to the outside
        self.assertTrue(container.DAEMON.endswith(f"exec nsenter --net={netns} /usr/bin/kiri daemon"))

    def test_on_windows_no_engine_of_the_user_is_ever_started(self):
        """The owner's rule (spec of the dynamic step, 15 November): on Windows the engine is always Daodan's own
        Kiri, never the Docker, Podman or Kiri the user has. A `docker` and a `podman` on PATH that would leave a
        mark, and answer as a Linux engine, are never started."""
        bin_dir, mark = self.scratch / "bin", self.scratch / "asked"
        bin_dir.mkdir()
        for name in ("docker", "podman"):  # `.cmd`: the name `program` finds on Windows
            script = bin_dir / f"{name}.cmd"
            if os.name == "nt":
                script.write_text(f'@echo {name}>> "{mark}"\r\n@echo linux\r\n')
            else:
                script.write_text(f'#!/bin/sh\necho {name} >> "{mark}"\necho linux\n')
                script.chmod(0o755)
        own = container.Engine(f"daodan-kiri@{container.KIRI_VERSION}", ("wsl.exe",))
        with mock.patch.dict(os.environ, {"PATH": str(bin_dir), "DAODAN_CONTAINER": ""}), \
                mock.patch.object(container.os, "name", "nt"), \
                mock.patch.object(container, "own_engine", return_value=own):
            found = container.find_engine()
        self.assertIs(found, own)
        self.assertFalse(mark.exists())

    def distro_fakes(self) -> types.SimpleNamespace:
        """`ensure_distro`'s world for the rest of the test: the pinned Alpine base served, Kiri's files, and a WSL that
        records each call and answers the command run in the distribution with `install` (code, stdout, stderr), or
        raises it; by default apk-tools 3.0.9's answer in Alpine 3.24 (notes, section 8)."""
        served, binaries = self.scratch / "served", self.scratch / "bin"
        served.mkdir()
        binaries.mkdir()
        arch = container.architecture()
        with tarfile.open(served / Path(container.ALPINE[arch][0]).name, "w:gz") as out:
            for name, content in {"etc/alpine-release": b"3.24.4\n", "etc/apk/keys/alpine.rsa.pub": b"a key\n"}.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                out.addfile(info, io.BytesIO(content))
        for name in container.KIRI_FILES.values():
            (binaries / name).write_bytes(name.encode())
        world = types.SimpleNamespace(fetched=[], asked=[], imported={}, install=(
            0, b"(1/1) Installing passt (2026.05.26-r0)\nOK: 8784 KiB in 17 packages\n", b""))

        def download(url, target, *, sha256=None):
            world.fetched.append((url, sha256))
            return Path(shutil.copyfile(served / Path(url).name, target))

        def wsl(*args, timeout=120):
            world.asked.append(args)
            if args[0] == "--import":
                with tarfile.open(args[3]) as rootfs:
                    world.imported = {member.name: (member.mode, member.uid, rootfs.extractfile(member).read())
                                      for member in rootfs if member.isfile()}
            if args[0] != "-d":
                return subprocess.CompletedProcess(args, 0, b"", b"")
            if isinstance(world.install, BaseException):
                raise world.install
            return subprocess.CompletedProcess(args, *world.install)

        for name, fake in (("download", download), ("wsl", wsl), ("kiri_files", lambda home: binaries)):
            self.enterContext(mock.patch.object(container, name, side_effect=fake))
        return world

    def test_daodan_s_distribution_gets_pasta_from_apk_checked_against_its_pinned_base_s_keys(self):
        """pasta joins Daodan's distribution at import, installed by apk in the distribution from the repositories its
        pinned Alpine base names, the signature checked against the keys that base carries (apk's own defaults, never
        `--allow-untrusted`, never a package unpacked by hand): only the base is downloaded. The version apk says it
        installed is kept with the distribution and named by the engine. The folder is named by what decides the
        result, the install included, so a distribution imported another way is unregistered and imported again;
        once imported, it is used as it is."""
        home = self.scratch / "home"
        home.mkdir()
        world = self.distro_fakes()
        arch = container.architecture()
        older = {container.DISTRO: str(home / "distro-5e639bca07d0"), "kiri": r"C:\kiri"}
        with mock.patch.object(container, "registered_distros", return_value=("kiri", older)):
            self.assertEqual(container.ensure_distro(home), (False, "2026.05.26-r0"))
        self.assertEqual(world.fetched, [container.ALPINE[arch]])
        self.assertEqual([args[0] for args in world.asked], ["--unregister", "--import", "-d"])
        self.assertEqual(world.asked[2], ("-d", container.DISTRO, "--cd", "/", "--exec", *container.INSTALL_PASTA))
        self.assertEqual(container.INSTALL_PASTA, ("/sbin/apk", "add", "--no-cache", "passt"))
        self.assertNotIn("usr/bin/pasta", world.imported)
        self.assertEqual(world.imported["usr/bin/kiri"], (0o755, 0, b"kiri"))
        self.assertIn("etc/wsl.conf", world.imported)
        self.assertFalse((home / "rootfs.tar").exists())
        folders = [path for path in home.iterdir() if path.is_dir() and path.name.startswith("distro-")]
        self.assertEqual([str(folder) for folder in folders], [world.asked[1][2]])
        world.asked.clear()
        current = {container.DISTRO: str(folders[0]), "kiri": r"C:\kiri"}
        with mock.patch.object(container, "registered_distros", return_value=("kiri", current)):
            self.assertEqual(container.ensure_distro(home), (False, "2026.05.26-r0"))
            self.assertEqual(world.asked, [])
            with mock.patch.object(container, "INSTALL_PASTA", (*container.INSTALL_PASTA, "nftables")):
                container.ensure_distro(home)
        self.assertEqual([args[0] for args in world.asked], ["--unregister", "--import", "-d"])
        self.assertNotEqual(world.asked[1][2], str(folders[0]))
        self.assertEqual(world.fetched, [container.ALPINE[arch]])

    def test_a_failed_pasta_install_is_a_gap_and_leaves_no_distribution_registered(self):
        """apk's answers in Alpine 3.24 (notes, section 7) when the mirror is not reached, when the index's signature
        does not verify against the base's keys, when the package is not there, and no answer in time: each a Gap with
        apk's words and a remedy, the distribution unregistered and its folder gone. One that stays registered (its
        removal failed, or a run ended between import and install) has no record of pasta, so the next start imports
        it again: never a start without pasta."""
        world = self.distro_fakes()
        fetching = "WARNING: fetching https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/APKINDEX.tar.gz: "
        unselected = "ERROR: unable to select packages:\n  passt (no such package):\n    required by: world[passt]\n"
        installed = world.install
        for index, (answer, cause, remedy) in enumerate((
                ((1, b"", f"{fetching}DNS: transient error (try again later)\n{unselected}".encode()), "DNS", "connection"),
                ((1, b"", f"{fetching}UNTRUSTED signature\n{unselected}".encode()), "UNTRUSTED signature", "keys"),
                ((1, b"", unselected.encode()), "passt (no such package)", "update Daodan"),
                (subprocess.TimeoutExpired("wsl.exe", 300), "300 s", "connection"))):
            home = self.scratch / f"home-{index}"
            home.mkdir()
            world.install, world.asked = answer, []
            with self.subTest(cause), \
                    mock.patch.object(container, "registered_distros", return_value=("kiri", {"kiri": r"C:\kiri"})):
                with self.assertRaises(container.Gap) as caught:
                    container.ensure_distro(home)
                self.assertIn(cause, caught.exception.cause)
                self.assertIn(remedy, caught.exception.remedy)
                self.assertEqual([args[:2] for args in world.asked],
                                 [("--import", container.DISTRO), ("-d", container.DISTRO),
                                  ("--unregister", container.DISTRO)])
                self.assertFalse(Path(world.asked[0][2]).exists())
                self.assertFalse((home / "rootfs.tar").exists())
        left = {container.DISTRO: world.asked[0][2], "kiri": r"C:\kiri"}  # its removal failed
        Path(left[container.DISTRO]).mkdir()
        world.install, world.asked = installed, []
        with mock.patch.object(container, "registered_distros", return_value=("kiri", left)):
            self.assertEqual(container.ensure_distro(home), (False, "2026.05.26-r0"))
        self.assertEqual([args[0] for args in world.asked], ["--unregister", "--import", "-d"])

    def test_an_imported_distribution_is_used_whichever_folder_carries_the_long_path_prefix(self):
        """WSL's `BasePath` and Daodan's own folder (a LOCALAPPDATA given as `\\\\?\\D:\\...`) may each carry the
        `\\\\?\\` prefix of long paths or not: compared in one form, the distribution already imported is used as it is,
        never unregistered and imported again with its images lost."""
        home = self.scratch / "home"
        home.mkdir()
        world = self.distro_fakes()
        with mock.patch.object(container, "registered_distros", return_value=(None, {})):
            container.ensure_distro(home)
        folder, prefix = world.asked[0][2], "\\\\?\\"
        world.asked.clear()
        pairs = [(home, prefix + folder)]
        if os.name == "nt":  # only there is a path with the prefix a path
            pairs += [(Path(prefix + str(home)), folder), (Path(prefix + str(home)), prefix + folder)]
        for given, registered in pairs:
            with self.subTest(home=str(given), registered=registered), \
                    mock.patch.object(container, "registered_distros",
                                      return_value=(None, {container.DISTRO: registered})):
                self.assertEqual(container.ensure_distro(given), (True, "2026.05.26-r0"))
        self.assertEqual(world.asked, [])

    def test_a_distribution_registered_in_the_old_shared_folder_is_made_again_in_the_new_one(self):
        """`DAODAN_SHARED_DIR` decides where the distribution's folder is (`engine_home`). Named again, with the
        distribution still registered in the old place, it is not reused (WSL's `BasePath` is not the new folder):
        unregistered, which WSL ends with its own disk, and imported again in the new folder, the Alpine base
        downloaded there. Daodan moves nothing and removes no folder of the old place."""
        world = self.distro_fakes()
        old, new = self.scratch / "old", self.scratch / "new"
        default = {"LOCALAPPDATA": str(self.scratch / "default"), "XDG_CACHE_HOME": str(self.scratch / "default")}
        with mock.patch.dict(os.environ, {**default, "DAODAN_SHARED_DIR": str(old)}):
            old_home = container.engine_home()
            old_home.mkdir(parents=True, exist_ok=True)
            with mock.patch.object(container, "registered_distros", return_value=(None, {})):
                container.ensure_distro(old_home)
            registered = world.asked[0][2]
            self.assertEqual(Path(registered).parent, old / "engines" / "kiri" / container.KIRI_VERSION)
            world.asked.clear()
            with mock.patch.object(container, "registered_distros",
                                   return_value=(None, {container.DISTRO: registered})):
                container.ensure_distro(container.engine_home())  # the setting unchanged: used as it is
            self.assertEqual(world.asked, [])
        with mock.patch.dict(os.environ, {**default, "DAODAN_SHARED_DIR": str(new)}):
            new_home = container.engine_home()
            new_home.mkdir(parents=True, exist_ok=True)
            with mock.patch.object(container, "registered_distros",
                                   return_value=(None, {container.DISTRO: registered})):
                container.ensure_distro(new_home)
        self.assertEqual([args[0] for args in world.asked], ["--unregister", "--import", "-d"])
        self.assertEqual(Path(world.asked[1][2]).parent, new / "engines" / "kiri" / container.KIRI_VERSION)
        self.assertEqual(len(world.fetched), 2)  # the base once in each place
        self.assertTrue(Path(registered).is_dir())  # nothing of the old place is removed by Daodan

    # Section 3: elsewhere, where Daodan brings no engine, the one the user already has is used as it is.
    @unittest.skipIf(os.name == "nt", "on Windows the engine is always Daodan's own")
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
        path = os.pathsep.join([str(bin_dir), *([str(Path(self.git).parent)] if self.git else [])])  # Git reads it
        with mock.patch.dict(os.environ, {"PATH": path, "DOCKER_CONFIG": str(config), "DAODAN_CONTAINER": ""}), \
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


@unittest.skipUnless(os.environ.get("MODAL_TASK_ID"), "a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_apt_updates_and_downloads_from_debian_s_plain_http_archive_through_the_proxy(tmp_path):
    """Debian's own apt, its sources plain HTTP as the image names them, through the proxy with deb.debian.org given
    as `http://deb.debian.org`: the signed indexes and a package come, and the proxy refuses nothing apt asks."""
    server = subprocess.Popen([sys.executable, "-I", "-c", container.PROXY_SCRIPT, "0", "http://deb.debian.org"],
                              stdout=subprocess.PIPE, text=True)
    try:
        port = int(server.stdout.readline().split()[1])
        for folder in ("lists/partial", "cache/archives/partial"):
            (tmp_path / folder).mkdir(parents=True)
        options = ["-o", f"Acquire::http::Proxy=http://127.0.0.1:{port}", "-o", f"Dir::State::Lists={tmp_path}/lists",
                   "-o", f"Dir::Cache={tmp_path}/cache", "-o", "APT::Sandbox::User=root", "-o", "Debug::NoLocking=1"]
        update = subprocess.run(["apt-get", *options, "update"], capture_output=True, text=True, timeout=600)
        print(update.stdout[-2000:], update.stderr[-2000:], flush=True)
        assert update.returncode == 0 and "InRelease" in update.stdout
        got = subprocess.run(["apt-get", *options, "download", "hello"], cwd=tmp_path, capture_output=True, text=True,
                             timeout=600)
        print(got.stdout[-1000:], got.stderr[-1000:], flush=True)
        assert got.returncode == 0 and list(tmp_path.glob("hello_*.deb"))
    finally:
        server.kill()
        refused = [line for line in server.stdout.read().splitlines() if line.startswith("refused")]
        server.wait()
    assert refused == []


SMOKE = os.environ.get("DAODAN_CONTAINER_SMOKE") == "1"
ALPINE = "alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf"
# nft in a root of its own inside Daodan's distribution, fetched and checked by apk; it reads the namespace it runs in.
PROBE = ("[ -x /opt/daodan-probe/usr/sbin/nft ] || apk --root /opt/daodan-probe --initdb --keys-dir /etc/apk/keys "
         "--repositories-file /etc/apk/repositories --no-cache --quiet add nftables")
# What the network namespace of every WSL distribution holds, read from Daodan's distribution outside its own.
SHARED = ("chroot /opt/daodan-probe nft list ruleset; ip -o link | cut -d: -f2 | sort; ip route; ip -6 route; "
          "cat /proc/sys/net/ipv4/ip_forward /proc/sys/net/ipv6/conf/all/forwarding")


def user_settings() -> dict:
    """What the user owns and the operation must leave as it was: PATH, Docker config and contexts, WSL."""
    settings = {"PATH": os.environ.get("PATH")}
    docker = Path(os.environ.get("DOCKER_CONFIG") or Path.home() / ".docker")
    settings["docker"] = tree_digest(docker) if docker.is_dir() else None
    if os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            settings["user PATH"] = winreg.QueryValueEx(key, "Path")[0]
        default, folders = container.registered_distros()
        # Daodan's distribution is not the user's: that it is registered counts, not the folder an import names.
        settings["wsl"] = (default, {name: path for name, path in folders.items() if name != container.DISTRO},
                           container.DISTRO in folders)
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

    def test_commands_as_data_in_one_container(self):
        free = container.free_memory()
        if free is not None and free < 4 * 2**30:
            self.skipTest(f"{free / 2**30:.1f} GB free, under 4 GB")
        engine = container.find_engine()
        scratch = Path(tempfile.mkdtemp(prefix="daodan-commands-smoke-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        (scratch / "project" / "src").mkdir(parents=True)
        (scratch / "project" / "src" / "a.py").write_text("x = 1\n")
        reach = "import urllib.request; urllib.request.urlopen('https://pypi.org/simple/', timeout=20); print('reached')"
        commands = [{"tool": "sh", "argv": ["sh", "-c", "echo out; echo err >&2; exit 3"], "network": "none"},
                    {"tool": "pwd", "argv": ["pwd"], "cwd": "src", "network": "none"},
                    {"tool": "python", "argv": ["python", "-c", reach], "network": "registries"},
                    {"tool": "python", "argv": ["python", "-c", reach], "network": "none"}]
        held = container.cli(engine, "system", "df").stdout
        result = container.run_commands(scratch / "project", commands, image=container.PROXY_IMAGE,
                                        out_dir=scratch / "out", engine=engine, memory=256 * 2**20, pids=64,
                                        timeout=120, prepare_timeout=120)
        print(json.dumps(result, indent=1))
        self.assertEqual(result["state"], "done", result)
        first, folder, early, late = result["results"]
        self.assertEqual((first["returncode"], first["stdout"], first["stderr"]), (3, "out\n", "err\n"))
        self.assertEqual(folder["stdout"].strip(), "/work/src")
        self.assertEqual((early["returncode"], early["stdout"].strip()), (0, "reached"))
        self.assertNotEqual(late["returncode"], 0)
        self.assertEqual(container.cli(engine, "system", "df").stdout, held)

    @unittest.skipUnless(os.name == "nt", "Daodan brings its own engine only on Windows")
    def test_own_engine_leaves_the_network_wsl_shares_as_it_was(self):
        """D-219, on this machine: every WSL distribution shares the VM's network namespace, where a Kiri builds and
        removes its nftables table. Daodan's runs in a namespace of its own (`DAEMON`), so that shared namespace
        (tables, links, routes, forwarding) is the same before, during and after a run of Daodan's engine, and
        `nft monitor` there sees no event while it pulls, runs a container without network and lets a preparation
        reach a registry through the proxy; Daodan's table is in its own namespace. The shared namespace is read
        from Daodan's distribution, outside its namespace, with nft installed by apk into a root of its own
        (`PROBE`). The import is part of the run: the distribution is imported again, so apk's install of pasta, with
        the shared namespace's sockets, is between `before` and `installed`. Another engine that changes the shared
        namespace meanwhile fails it too: the output says what."""
        free = container.free_memory()
        if free is not None and free < 4 * 2**30:
            self.skipTest(f"{free / 2**30:.1f} GB free, under 4 GB")
        before_settings = user_settings()
        home = container.engine_home()
        container.ensure_distro(home)
        argv = container.distro_argv()

        def shell(script: str) -> str:
            answer = subprocess.run([*argv, "/bin/sh", "-c", script], capture_output=True, text=True, timeout=600)
            self.assertEqual(answer.returncode, 0, answer.stdout + answer.stderr)
            return answer.stdout

        shell(PROBE)
        before = shell(SHARED)
        container.remove_distro()
        pasta = container.ensure_distro(home)[1]
        shell(PROBE)
        installed = shell(SHARED)
        engine = container.find_engine()
        self.assertEqual(engine.name, f"daodan-kiri@{container.KIRI_VERSION}+pasta@{pasta}")
        monitor = subprocess.Popen([*argv, "/bin/sh", "-c", "exec chroot /opt/daodan-probe nft monitor"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            version = container.cli(engine, "version", "--format", "{{.Server.Os}} {{.Server.Version}}").stdout.decode()
            pinned = container.pin(lambda *args, timeout=300: container.cli(engine, *args, timeout=timeout), ALPINE, 600)
            line = container.checked(container.cli(
                engine, "run", "--rm", "--network", "none", pinned, "sh", "-c", "echo printed without a network; "
                "ip -o link | cut -d: -f2 | tr -d ' ' | tr '\\n' ' '"), "run").stdout.decode().strip()
            ours = shell(f"nsenter --net={container.NETNS} chroot /opt/daodan-probe nft list tables")
            during = shell(SHARED)
            scratch = Path(tempfile.mkdtemp(prefix="daodan-shared-network-smoke-"))
            self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
            (scratch / "project").mkdir()
            reach = ("import urllib.request; urllib.request.urlopen('https://pypi.org/simple/', timeout=20); "
                     "print('reached')")
            result = container.run_commands(scratch / "project", [
                {"tool": "python", "argv": ["python", "-c", reach], "network": "registries"},
                {"tool": "python", "argv": ["python", "-c", reach], "network": "none"}],
                image=container.PROXY_IMAGE, out_dir=scratch / "out", engine=engine, memory=256 * 2**20, pids=64,
                timeout=120, prepare_timeout=300)  # it stops the engine at its end
        finally:
            engine.stop()
            events = monitor.communicate(timeout=60)[0]
        after = shell(SHARED)
        print(json.dumps({"before": before, "installed": installed, "during": during, "after": after, "events": events,
                          "version": version, "pasta": pasta, "pinned": pinned, "line": line, "ours": ours,
                          "results": [(item["returncode"], item["stdout"].strip()) for item in result["results"]]},
                         indent=1))
        self.assertEqual(version.strip(), f"linux {container.KIRI_VERSION}")
        self.assertEqual(line, "printed without a network\nlo")
        self.assertIn("table ip kiri", ours)
        self.assertEqual((installed, during, after), (before, before, before))
        self.assertEqual(events.strip(), "")
        self.assertEqual(result["state"], "done", result)
        early, late = result["results"]
        self.assertEqual((early["returncode"], early["stdout"].strip()), (0, "reached"))
        self.assertNotEqual(late["returncode"], 0)
        self.assertEqual(user_settings(), before_settings)

    @unittest.skipUnless(os.name == "nt", "Daodan brings its own engine only on Windows")
    def test_own_engine_installs_into_the_shared_directory(self):
        free = shutil.disk_usage(Path(container.engine_home().anchor)).free
        if free < container.ENGINE_DISK_MIN:
            self.skipTest(f"{free / 2**20:.0f} MB free on the shared directory's disk")
        before = user_settings()
        registered = before["wsl"][2]
        try:
            home = container.engine_home()
            container.kiri_files(home)
            remove, pasta = container.ensure_distro(home)
            argv = container.distro_argv()
            probes = {"docker": [*argv, "/usr/bin/docker", "--version"],
                      "kiri": [*argv, "/usr/bin/kiri"],
                      "pasta": [*argv, "/usr/bin/pasta", "--version"],
                      "cgroup": [*argv, "/bin/sh", "-c", "grep ' /sys/fs/cgroup ' /proc/mounts"]}
            answers = {name: subprocess.run(probe, capture_output=True, text=True, timeout=60)
                       for name, probe in probes.items()}
            for name, answer in answers.items():
                print(name, answer.returncode, answer.stdout.strip()[:200], answer.stderr.strip()[:200])
            self.assertIn("29.9.2", answers["docker"].stdout)
            self.assertIn("kiri raw run", answers["kiri"].stderr)
            # The version on record is the program's: passt's 2026_05_26.<commit> is Alpine's 2026.05.26-r<n>.
            self.assertIn("pasta " + pasta.split("-r")[0].replace(".", "_"), answers["pasta"].stdout)
            self.assertIn("cgroup2", answers["cgroup"].stdout)
        finally:
            if not registered:
                container.remove_distro()
        print(json.dumps({"home": str(home), "remove_after_use": remove, "pasta": pasta,
                          "files": sorted(str(path.relative_to(home)) for path in home.rglob("*") if path.is_file())}))
        self.assertEqual(user_settings(), before)


if __name__ == "__main__":
    unittest.main()
