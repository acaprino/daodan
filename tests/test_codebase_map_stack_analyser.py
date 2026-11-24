"""The pinned stack-analyser release installs on first use, checked by its sha256, and starts outside the analysed
project (AGENTS.md): no path into the project but its argument, no `NODE_` variable of the caller.

The stand-in `fake_stack_analyser` takes the place of Node; no test needs Node, the network or a container. That the
real release runs nothing of a project is proved on the real tool, not here.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_stack_analyser.py
"""
from __future__ import annotations

import ast
import hashlib
import http.client
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import container  # noqa: E402
import engine_tools  # noqa: E402
import fake_stack_analyser  # noqa: E402
import stack_analyser  # noqa: E402
from indexers import runtime  # noqa: E402

DECLARATION = {"type": "npm", "name": "react", "path": "web/package.json", "line": 4, "source": "npm@1"}


@pytest.fixture(autouse=True)
def forgotten_failures():
    """What the process remembers of a failed install is not carried from one test to the next."""
    stack_analyser._failed.clear()
    yield
    stack_analyser._failed.clear()


@pytest.fixture
def started(tmp_path, monkeypatch):
    """`(project, program, cli)`: a project, the stand-in as Node, and a path for the release's program."""
    project = tmp_path / "project"
    project.mkdir()
    program = fake_stack_analyser.install(tmp_path / "tool")
    cli = tmp_path / "release" / "package" / "dist" / "cli.mjs"
    monkeypatch.setattr(stack_analyser, "node", lambda _project: program)
    monkeypatch.setattr(stack_analyser, "cli", lambda: cli)
    return project, program, cli


def test_the_fork_is_started_outside_the_project_without_the_caller_s_node_variables(started, monkeypatch):
    project, program, cli = started
    monkeypatch.setenv("NODE_OPTIONS", f"--require {project / 'trap.js'}")
    monkeypatch.setenv("NODE_PATH", str(project / "node_modules"))
    result = stack_analyser.run(project, declarations=[DECLARATION], skip_dirs=(), ignore=("gen",))
    [call] = fake_stack_analyser.calls(program)
    assert Path(call["argv"][0]) == cli and cli.is_absolute() and program.is_absolute()
    assert call["argv"][1] == str(project.resolve())
    assert not {"--skip-dirs", "--ignore"} & set(call["argv"])
    assert json.loads((program.parent / "perimeter.json").read_bytes()) == {"skipDirs": [], "ignore": ["gen"]}
    assert not Path(call["cwd"]).resolve().is_relative_to(project.resolve())
    assert "NODE_OPTIONS" not in call["env"] and "NODE_PATH" not in call["env"]
    assert "NODE_COMPILE_CACHE" in call["env"]  # Daodan's own caches are added after the caller's are dropped
    assert result["evidence"][0]["tech"] == "react"


def test_the_declarations_reach_the_fork_as_utf8_json_outside_the_project(started):
    project, program, _cli = started
    declared = {**DECLARATION, "name": "réact — \U0001F600"}
    stack_analyser.run(project, declarations=[declared])
    [call] = fake_stack_analyser.calls(program)
    path = Path(call["argv"][call["argv"].index("--declarations") + 1])
    assert not path.resolve().is_relative_to(project.resolve())
    copy = (program.parent / "declarations.json").read_bytes()
    assert copy.startswith(b"[") and json.loads(copy.decode("utf-8")) == [declared]
    assert "réact".encode("utf-8") in copy  # written as UTF-8, not as \u escapes


def test_without_declarations_the_option_is_not_passed(started):
    project, program, _cli = started
    stack_analyser.run(project)
    [call] = fake_stack_analyser.calls(program)
    assert not {"--declarations", "--skip-dirs", "--ignore"} & set(call["argv"])
    assert call["argv"][2:4] == ["--output", call["argv"][3]] and not (program.parent / "declarations.json").exists()
    assert json.loads((program.parent / "perimeter.json").read_bytes()) == {"skipDirs": [], "ignore": []}


def test_the_perimeter_reaches_the_fork_in_a_file(started):
    project, program, _cli = started
    ignore = tuple(f"packages/service-{number}/generated/file-{number}.ts" for number in range(10000))
    stack_analyser.run(project, declarations=[DECLARATION], skip_dirs=("node_modules", "dist"), ignore=ignore)
    [call] = fake_stack_analyser.calls(program)
    assert max(len(argument) for argument in call["argv"]) < 300
    path = Path(call["argv"][call["argv"].index("--perimeter") + 1])
    assert not path.resolve().is_relative_to(project.resolve())
    assert json.loads((program.parent / "perimeter.json").read_bytes()) == {"skipDirs": ["node_modules", "dist"],
                                                                         "ignore": list(ignore)}


def test_the_catalogue_is_what_the_fork_writes(started):
    _project, program, cli = started
    assert stack_analyser.catalogue() == fake_stack_analyser.CATALOGUE
    [call] = fake_stack_analyser.calls(program)
    assert Path(call["argv"][0]) == cli and call["argv"][1] == "--catalogue" and len(call["argv"]) == 3
    assert not {"--output", "--perimeter"} & set(call["argv"])


def test_a_cache_folder_that_cannot_be_used_is_a_gap(started, monkeypatch):
    project, program, _cli = started

    def unusable():
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(engine_tools, "node_environment", unusable)
    for call in (lambda: stack_analyser.run(project), stack_analyser.catalogue):
        with pytest.raises(container.Gap) as gap:
            call()
        assert "Permission denied" in gap.value.cause and gap.value.remedy
    assert fake_stack_analyser.calls(program) == []

    def unusable_engines(_name):
        raise ValueError("DAODAN_SHARED_DIR must be an absolute path")

    monkeypatch.undo()  # the fixture's stand-ins go: `cli` is the real one
    monkeypatch.setattr(engine_tools, "shared_engine_dir", unusable_engines)
    stack_analyser.cli.cache_clear()
    with pytest.raises(container.Gap) as gap:
        stack_analyser.cli()
    assert "must be an absolute path" in gap.value.cause and gap.value.remedy


def test_declarations_that_are_not_valid_unicode_are_a_gap_and_nothing_starts(started):
    """A lone surrogate comes from a manifest's `\\ud800` escape or a directory name that is not UTF-8 on POSIX."""
    project, program, _cli = started
    with pytest.raises(container.Gap) as gap:
        stack_analyser.run(project, declarations=[{**DECLARATION, "name": "\ud800"}])
    assert "declarations could not be written" in gap.value.cause and "not valid Unicode" in gap.value.cause
    assert gap.value.remedy and fake_stack_analyser.calls(program) == []


def test_declarations_that_cannot_be_written_are_a_gap_and_nothing_starts(started, monkeypatch):
    project, program, _cli = started

    def full(_path, _data):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(Path, "write_bytes", full)
    with pytest.raises(container.Gap) as gap:
        stack_analyser.run(project, declarations=[DECLARATION])
    assert "declarations could not be written" in gap.value.cause and "No space left" in gap.value.cause
    assert gap.value.remedy and fake_stack_analyser.calls(program) == []


def test_nothing_is_left_in_the_temporary_folder(started, monkeypatch):
    project, program, _cli = started
    stack_analyser.run(project, declarations=[DECLARATION])
    monkeypatch.setenv("FAKE_STACK_ANALYSER", "fail")
    with pytest.raises(container.Gap):
        stack_analyser.run(project, declarations=[DECLARATION])
    folders = [Path(call["cwd"]) for call in fake_stack_analyser.calls(program)]
    assert len(folders) == 2 and not any(folder.exists() for folder in folders)


@pytest.mark.parametrize("mode, words", [("fail", ("exit 1", "the fake failed")), ("garbage", ("not JSON",)),
                                         ("sleep", ("no answer", "2 s"))])
def test_a_run_that_fails_is_a_gap_with_its_cause(mode, words, started, monkeypatch):
    project, _program, _cli = started
    monkeypatch.setenv("FAKE_STACK_ANALYSER", mode)
    monkeypatch.setattr(stack_analyser, "TIMEOUT", 2)
    with pytest.raises(container.Gap) as gap:
        stack_analyser.run(project)
    assert all(word in gap.value.cause for word in words) and gap.value.remedy


def test_a_program_that_cannot_start_is_a_gap(started, monkeypatch):
    project, program, _cli = started
    monkeypatch.setattr(stack_analyser, "node", lambda _project: program.parent / "absent" / "node")
    with pytest.raises(container.Gap) as gap:
        stack_analyser.run(project)
    assert "could not start" in gap.value.cause and gap.value.remedy


# ------------------------------------------------------------------ the release: download, check, unpack, publish

def _release(tmp_path: Path, program: str = "package/dist/cli.mjs") -> tuple[str, str]:
    """`(file:// URL, sha256)` of a small release archive, as the real one is laid out: everything under `package/`."""
    archive = tmp_path / "source" / "release.tgz"
    archive.parent.mkdir()
    with tarfile.open(archive, "w:gz") as bundle:
        body = b"console.log('stack-analyser');\n"
        member = tarfile.TarInfo(program)
        member.size = len(body)
        bundle.addfile(member, io.BytesIO(body))
    return archive.as_uri(), hashlib.sha256(archive.read_bytes()).hexdigest()


@pytest.fixture
def installed_under(tmp_path, monkeypatch):
    """The shared tool folder is `tmp_path`; `cli()` starts without an earlier call's answer and leaves none."""
    monkeypatch.setattr(engine_tools, "shared_engine_dir", lambda name: tmp_path / name)
    monkeypatch.setattr(engine_tools.time, "sleep", lambda _seconds: None)  # `download` waits between its attempts
    stack_analyser.cli.cache_clear()
    yield tmp_path / "stack-analyser" / stack_analyser.VERSION
    stack_analyser.cli.cache_clear()


def test_a_release_with_another_sha256_is_not_installed(tmp_path, monkeypatch, installed_under):
    url, _digest = _release(tmp_path)
    monkeypatch.setattr(stack_analyser, "URL", url)
    monkeypatch.setattr(stack_analyser, "SHA256", "0" * 64)
    with pytest.raises(container.Gap) as gap:
        stack_analyser.cli()
    assert "checksum mismatch" in gap.value.cause and gap.value.remedy
    assert not installed_under.exists()
    assert not any(tmp_path.joinpath("stack-analyser").iterdir())  # not even a partial install


def test_an_install_that_failed_is_not_tried_again_in_the_same_process(tmp_path, monkeypatch, installed_under):
    attempts = []

    def refuse(*_args, **_kwargs):
        attempts.append(1)
        raise OSError("no route to host")

    monkeypatch.setattr(engine_tools, "publish", refuse)
    with pytest.raises(container.Gap) as first:
        stack_analyser.cli()
    with pytest.raises(container.Gap) as second:
        stack_analyser.cli()
    assert second.value is first.value and "no route to host" in first.value.cause and len(attempts) == 1

    def unavailable(_project):
        attempts.append(2)
        raise runtime.Unavailable("no room", "free 1 GB")

    monkeypatch.setattr(runtime, "node", unavailable)
    for _ in range(2):
        with pytest.raises(container.Gap) as node_gap:
            stack_analyser.node(tmp_path)
    assert node_gap.value.cause == "no room" and attempts == [1, 2]


def test_a_download_cut_off_is_tried_again(tmp_path, monkeypatch, installed_under):
    url, digest = _release(tmp_path)
    monkeypatch.setattr(stack_analyser, "URL", url)
    monkeypatch.setattr(stack_analyser, "SHA256", digest)
    opened, open_url = [], engine_tools.open_url

    def cut_off_once(*args, **kwargs):
        opened.append(1)
        if len(opened) == 1:
            raise http.client.IncompleteRead(b"")
        return open_url(*args, **kwargs)

    monkeypatch.setattr(engine_tools, "open_url", cut_off_once)
    assert stack_analyser.cli().is_file() and len(opened) == 2


def test_the_release_is_installed_once_and_found_again(tmp_path, monkeypatch, installed_under):
    url, digest = _release(tmp_path)
    monkeypatch.setattr(stack_analyser, "URL", url)
    monkeypatch.setattr(stack_analyser, "SHA256", digest)
    downloads, download = [], engine_tools.download
    monkeypatch.setattr(engine_tools, "download",
                        lambda *args, **kwargs: downloads.append(args[0]) or download(*args, **kwargs))
    first = stack_analyser.cli()
    assert first == installed_under / "package" / "dist" / "cli.mjs" and first.is_file()
    assert not (installed_under / "release.tgz").exists()  # the archive is not kept
    stack_analyser.cli.cache_clear()  # a new process: only the folder remembers the install
    assert stack_analyser.cli() == first
    assert downloads == [url]


def test_a_release_without_the_program_is_a_gap(tmp_path, monkeypatch, installed_under):
    url, digest = _release(tmp_path, program="package/README.md")
    monkeypatch.setattr(stack_analyser, "URL", url)
    monkeypatch.setattr(stack_analyser, "SHA256", digest)
    with pytest.raises(container.Gap) as gap:
        stack_analyser.cli()
    assert "package/dist/cli.mjs" in gap.value.cause and str(installed_under) in gap.value.remedy


def test_the_test_image_pins_the_same_release():
    """The launcher of the Modal tests cannot import `daodan/core`, so it repeats the release's URL and sha256, and the
    path of the program the real proof (test_codebase_map_host_programs.py) is given. They are read from its source:
    it imports `modal`."""
    source = (ROOT / "tests" / "modal_pytest.py").read_text(encoding="utf-8")
    [pinned] = [ast.literal_eval(node.value) for node in ast.parse(source).body
                if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "STACK_ANALYSER"]
    assert pinned[:2] == (stack_analyser.URL, stack_analyser.SHA256)
    assert f'"DAODAN_STACK_ANALYSER": "{pinned[2]}/{stack_analyser.PROGRAM}"' in source


# ------------------------------------------------------------------ Node

def test_node_is_the_executable_of_daodan_s_own_node(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(runtime, "node", lambda project: seen.append(project) or tmp_path / "node-v1")
    assert stack_analyser.node(tmp_path) == tmp_path / "node-v1" / engine_tools.executable_name("node")
    assert seen == [tmp_path]


def test_a_node_that_cannot_be_installed_is_a_gap(tmp_path, monkeypatch):
    def unavailable(_project):
        raise runtime.Unavailable("no room", "free 1 GB")

    monkeypatch.setattr(runtime, "node", unavailable)
    with pytest.raises(container.Gap) as gap:
        stack_analyser.node(tmp_path)
    assert (gap.value.cause, gap.value.remedy) == ("no room", "free 1 GB")
