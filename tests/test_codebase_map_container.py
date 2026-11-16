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
elif verb == "commit":
    if (state / "no-commit").exists():
        sys.exit("docker: 'commit' is not a docker command.")
    shutil.copytree(box(args[1]) / "fs", state / "images" / args[2].replace(":", "_"))
elif verb == "image" and args[1] == "rm":
    shutil.rmtree(state / "images" / args[-1].replace(":", "_"), ignore_errors=True)
elif verb == "logs":
    print("ready 3128")
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
        name = self.created()[0][self.created()[0].index("--name") + 1]
        with tarfile.open(self.state / "containers" / name / "copy.tar") as bundle:
            files = {member.name: member.mode for member in bundle.getmembers() if member.isfile()}
        self.assertEqual(sorted(files), ["work/.gitignore", "work/.mvn/jvm.config",
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
        self.assertEqual([(gap["kind"], gap["path"], gap["target"]) for gap in result["gaps"]], [
            ("link_outside", "tests/root.py", "/etc/passwd"), ("link_outside", "tests/up.py", "../../outside.py")])
        self.assertIn("../../outside.py", result["gaps"][1]["detail"])

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

    def test_failed_preparation_stops_before_execution(self):
        result = self.run_operation(["exit", "0"], prepare=["exit", "3"])
        self.assertEqual(result["state"], "failed")
        self.assertIn("3", result["cause"])
        self.assertEqual(len(self.created()), 2)
        self.assertEqual(len([call for call in self.calls() if call[:2] == ["volume", "rm"]]), 2)

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
