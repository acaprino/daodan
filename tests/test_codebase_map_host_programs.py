"""What the host starts runs nothing of the analyzed project (AGENTS.md): no program found in the project's folder,
no module imported from it.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_host_programs.py
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import code_graph  # noqa: E402
import container  # noqa: E402
import engine_pass  # noqa: E402
import tree_scope  # noqa: E402
import usage_finder  # noqa: E402


def _planted(folder: Path, name: str) -> Path:
    """A program named `name` in `folder`, as Windows would start it (`.bat` there)."""
    path = folder / (f"{name}.bat" if os.name == "nt" else name)
    path.write_text("echo planted\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_a_program_is_found_on_absolute_path_entries_only(tmp_path, monkeypatch):
    """Windows, and `shutil.which` there, look in the working directory first, and an analysis runs with the
    analyzed project as its working directory: its own `docker.bat`, `podman.bat`, `npm.bat` or `wsl.exe` would run.
    `tree_scope.program` reads only absolute PATH entries, as `git_executable` does."""
    project, tools = tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    for name in ("docker", "podman", "npm", "wsl"):
        _planted(project, name)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([".", "project", ""]))
    assert [tree_scope.program(name) for name in ("docker", "podman", "npm", "wsl")] == [None] * 4
    assert container.wsl_executable() in (None, str(Path(os.environ.get("SystemRoot", r"C:\Windows"))
                                                    / "System32" / "wsl.exe"))
    monkeypatch.delenv("DAODAN_CONTAINER", raising=False)
    with pytest.raises(container.Gap):
        container.user_engine()  # no docker, no podman: the project's are never started
    tool = _planted(tools, "npm")
    monkeypatch.setenv("PATH", os.pathsep.join([".", str(tools)]))
    assert tree_scope.program("npm") == str(tool)


def test_the_comment_rewriter_runs_no_formatter_on_the_host(tmp_path, monkeypatch):
    """prettier loads `prettier.config.js` and its plugins, ruff and black read the project's pyproject: a formatter
    over the project's file runs the project's configuration. The rewrite leaves formatting undone and says why
    (D-256); no program starts, though one of each name is on PATH."""
    import subprocess
    import comment_rewriter
    marker, project, tools = tmp_path / "ran", tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    (project / "prettier.config.js").write_text(f"require('fs').writeFileSync({str(marker)!r}, 'config');\n"
                                                "module.exports = {};\n", encoding="utf-8")
    (project / "app.js").write_text("// increment i\ni++;\n", encoding="utf-8")
    for name in ("prettier", "biome", "ruff", "black", "rustfmt", "gofmt"):
        path = tools / (f"{name}.bat" if os.name == "nt" else name)
        path.write_text(f"echo {name} > {marker}\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", os.pathsep.join([str(tools), os.environ.get("PATH", "")]))
    started = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or pytest.fail("a process"))
    _rewritten, changes = comment_rewriter.rewrite_file(project / "app.js", dry_run=False)
    assert not marker.exists() and started == []
    assert changes[-1] == comment_rewriter.FORMAT_UNDONE


@pytest.mark.skipif(sys.platform == "win32", reason="the memory probe wraps a run on POSIX only")
def test_the_memory_probe_imports_nothing_from_the_folder_it_runs_in(tmp_path):
    """`code_graph.measured` wraps an indexer in this Python with `-c`, started in the project's folder or its mirror:
    with `-c` Python puts that folder first on `sys.path`, so a project's `subprocess.py` or `resource.py` would
    run on the host. The probe runs isolated (`-I`)."""
    marker, folder = tmp_path / "ran", tmp_path / "project"
    folder.mkdir()
    for name in ("subprocess", "resource", "sys"):
        (folder / f"{name}.py").write_text(f"open({str(marker)!r}, 'a').write({name!r})\nraise SystemExit(3)\n",
                                           encoding="utf-8")
    run = code_graph.measured([sys.executable, "-I", "-c", "pass"], str(folder), None, 60)
    assert not marker.exists() and run["returncode"] == 0 and run["peak_mb"] is not None


# ------------------------------------------------------------------ a program named without its folder

# The stand-in programs are files that say they started: a file is a program by its mode only where modes count.
marked = pytest.mark.skipif(os.name == "nt", reason="the stand-in programs are shell scripts")


def _marked(folder: Path, name: str, mark: Path, code: int = 0) -> Path:
    """A program named `name` in `folder` that says in `mark` that it started and with what, then ends with `code`."""
    path = folder / name
    path.write_text(f'#!/bin/sh\necho "$0 $*" >> "{mark}"\nexit {code}\n', encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def searched(tmp_path, monkeypatch):
    """A project that is the working directory and is searched for a program's name before the PATH's own folder:
    what Windows does with every name written without a folder, and any system whose PATH holds a relative entry.
    `(project, tools, what the project's programs said, what the PATH's said)`."""
    project, tools = tmp_path / "project", tmp_path / "tools"
    project.mkdir()
    tools.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([".", str(tools)]))
    return project, tools, tmp_path / "the-project-s-ran", tmp_path / "the-path-s-ran"


@marked
def test_a_pass_is_ended_by_the_taskkill_of_the_path_never_by_the_project_s(searched, monkeypatch):
    project, tools, ran, own = searched
    for name in ("taskkill", "taskkill.exe"):
        _marked(project, name, ran)
    _marked(tools, "taskkill.exe", own)
    with monkeypatch.context() as windows:
        windows.setattr(os, "name", "nt")  # the branch of Windows, on the programs above
        engine_pass._terminate_tree(4242)
        (tools / "taskkill.exe").unlink()
        with pytest.raises(OSError, match="taskkill"):  # no name without a folder is tried instead
            engine_pass._terminate_tree(4242)
    assert not ran.exists(), ran.read_text(encoding="utf-8")
    assert own.read_text(encoding="utf-8").split() == [str(tools / "taskkill.exe"), "/PID", "4242", "/T", "/F"]


@marked
def test_without_wsl_nothing_named_wsl_is_started(searched):
    project, _tools, ran, _own = searched
    _marked(project, "wsl.exe", ran)
    assert container.wsl_executable() is None
    for start in (lambda: container.wsl("--status"), container.distro_argv):
        with pytest.raises(container.Gap) as gap:
            start()
        assert gap.value.cause == "WSL is not installed"
    assert not ran.exists(), ran.read_text(encoding="utf-8")


@marked
def test_usages_are_searched_by_a_tool_of_the_path_or_by_python_never_by_the_project_s(searched):
    """A project's own `rg` or `grep` would also choose the answer: here each says there is no match."""
    project, tools, ran, own = searched
    (project / "a.py").write_text("class Engine:\n    pass\n\n\nEngine()\n", encoding="utf-8")
    for name in ("rg", "grep"):
        _marked(project, name, ran, code=1)
    found = usage_finder.find_usages_with_grep("Engine", [project])
    assert {usage.line_number for usage in found} == {1, 5}  # no tool on the PATH: Python's own search
    _marked(tools, "rg", own, code=1)
    assert usage_finder.find_usages_with_grep("Engine", [project]) == []  # the PATH's tool answers
    assert own.read_text(encoding="utf-8").startswith(f"{tools / 'rg'} -n --with-filename -F -e Engine -- ")
    assert not ran.exists(), ran.read_text(encoding="utf-8")


# ------------------------------------------------------------------ Secretlint, on a project that sets traps for it

TRAP_RULE = "@secretlint/secretlint-rule-trap"
NAMES_TRAP = '{"rules": [{"id": "%s"}]}\n' % TRAP_RULE
WATCHED = ("BUN_OPTIONS", "NODE_PATH", "DEBUG")  # set by the vectors and the fixture, unset for each naive run alone


def _leave(mark: Path, vector: str) -> str:
    """JavaScript that appends `vector` to `mark` when it is loaded."""
    return f"require('fs').appendFileSync({str(mark)!r}, {vector + chr(10)!r});\n"


def _trap_rule(project: Path, mark: Path, vector: str) -> None:
    rule = project / "node_modules" / TRAP_RULE
    rule.mkdir(parents=True, exist_ok=True)
    (rule / "package.json").write_text(f'{{"name": "{TRAP_RULE}", "main": "index.js"}}\n', encoding="utf-8")
    (rule / "index.js").write_text(_leave(mark, vector) + f"exports.creator = {{messages: {{}}, meta: {{id: '{TRAP_RULE}', "
                                   "recommended: true, type: 'scanner', supportedContentTypes: ['text']}, "
                                   "create() { return {}; }};\n", encoding="utf-8")


def _rc_js(project, mark):
    (project / ".secretlintrc.js").write_text(_leave(mark, "rc-js") + "module.exports = {rules: []};\n",
                                              encoding="utf-8")
    return project, {}


def _rc_json(project, mark):
    _trap_rule(project, mark, "rc-json")
    (project / ".secretlintrc.json").write_text(NAMES_TRAP, encoding="utf-8")
    return project, {}


def _bunfig(project, mark):
    (project / "bunfig-trap.js").write_text(_leave(mark, "bunfig"), encoding="utf-8")
    (project / "bunfig.toml").write_text('preload = ["./bunfig-trap.js"]\n', encoding="utf-8")
    return project, {}


def _bun_options(project, mark):
    (project / "options-trap.js").write_text(_leave(mark, "bun-options"), encoding="utf-8")
    return project, {"BUN_OPTIONS": f"--preload {project / 'options-trap.js'}"}


def _node_path(project, mark):
    """The project's rule module found only through `NODE_PATH`: the naive run starts in a folder of its own whose
    configuration names the rule, so nothing but the variable leads to the project."""
    _trap_rule(project, mark, "node-path")
    named = project.parent / f"{project.name}-named"
    named.mkdir(exist_ok=True)
    (named / ".secretlintrc.json").write_text(NAMES_TRAP, encoding="utf-8")
    return named, {"NODE_PATH": str(project / "node_modules")}


# How a project's code could reach a Secretlint started on the host: each vector writes its files into a project
# and gives the folder a naive start runs in and the variables it adds.
VECTORS = {"rc-js": _rc_js, "rc-json": _rc_json, "bunfig": _bunfig, "bun-options": _bun_options,
           "node-path": _node_path}
# The rule takes a body of at least 100 Base64 characters that starts with `MI` (an ASN.1 sequence): this one has 108.
KEY_BODY = "MIIBOgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKL\ns1Pt8QuKUpRKfFLfRYC9AIKjbJTWit+CqvjWYzvQwECAwEAAQ=="
SIGNING = (f"KEY = '''-----BEGIN RSA PRIVATE KEY-----\n{KEY_BODY}\n-----END RSA PRIVATE KEY-----'''\n"
           "-----BEGIN FAKE-----\nfake\n-----END FAKE-----\n")


@pytest.fixture
def trapped(tmp_path, monkeypatch):
    """`(project, mark, checked file)`: a project holding every vector, writing to one mark, that is the working
    directory, as in an analysis, with every vector's variables and `DEBUG` set."""
    project, mark = tmp_path / "project", tmp_path / "loaded"
    project.mkdir()
    for vector in VECTORS.values():
        for name, value in vector(project, mark)[1].items():
            monkeypatch.setenv(name, value)
    monkeypatch.setenv("DEBUG", "*secretlint*")
    checked = project / "src" / "signing.py"
    checked.parent.mkdir()
    checked.write_text(SIGNING, encoding="utf-8")
    monkeypatch.chdir(project)
    return project, mark, checked


def test_secretlint_is_started_outside_the_project_with_daodan_s_configuration(trapped, tmp_path, monkeypatch):
    """What this proves: how Daodan starts the tool. The stand-in records an absolute program, Daodan's own
    configuration, the text on standard input under its bare name, a working directory outside the project, no
    word of the command line naming the project, and none of the variables that would load the project's code. That
    the real tool honours these is `test_the_real_secretlint_loads_nothing_of_the_project`."""
    import fake_secretlint
    import secret_mask
    project, mark, checked = trapped
    program = fake_secretlint.install(tmp_path / "tool")
    monkeypatch.setattr(secret_mask, "executable", lambda: program)
    result = secret_mask.masked(checked.read_text(encoding="utf-8"), str(checked))
    [call] = fake_secretlint.calls(program)
    assert call["argv"] == [f"--secretlintrc={secret_mask.CONFIG}", "--format=json", "--stdinFileName=signing.py"]
    assert secret_mask.command(program, str(checked))[0] == str(program) and program.is_absolute()
    assert not Path(call["cwd"]).resolve().is_relative_to(project.resolve()) and call["env"] == []
    assert not any(str(project) in word for word in call["argv"])
    assert result["found"] == 1 and not mark.exists()


def _naive(program: Path, tmp_path: Path, name: str, vector) -> str:
    """The vector alone in a project of its own, and Secretlint started the naive way: in the folder the vector
    gives, with only its variables added. What happened, as a line of the report."""
    project, mark = tmp_path / "naive" / name, tmp_path / "naive" / f"{name}.mark"
    project.mkdir(parents=True)
    folder, variables = vector(project, mark)
    environment = {key: value for key, value in os.environ.items() if key not in WATCHED} | variables
    import subprocess
    try:
        run = subprocess.run([str(program), "--stdinFileName=signing.py", "--format=json"], input=SIGNING.encode(),
                             cwd=folder, env=environment, capture_output=True, timeout=120)
        said = (run.stdout + run.stderr).decode("utf-8", "replace").strip().splitlines()[-3:]
        ended = f"exit {run.returncode}; {' | '.join(said)[:300]}"
    except (OSError, subprocess.TimeoutExpired) as error:
        ended = f"did not end: {error}"
    verdict = "fires when started the naive way" if mark.exists() else "this executable does not load it"
    return f"{name}: {verdict} ({ended})"


GITHUB_TOKEN = "ghp_wWPw5k4aXcaT4fNP0UcnZwJUVFk6LO2rINUx"
TWO_KINDS = ("# café \U0001F600 — two secrets\n"
             f"TOKEN = \"\U0001F600 {GITHUB_TOKEN}\"\n"
             f"KEY = '''\n-----BEGIN RSA PRIVATE KEY-----\n{KEY_BODY}\n"
             "-----END RSA PRIVATE KEY-----\n'''\nprint('è fine')\n")


def _masked_exactly(text: str, masked: str, secret: str) -> None:
    """`secret` masked where it stands, every character but its line breaks a `*`, and the character before it
    kept: masks one unit off, as UTF-16 ranges read as code points would be after the emoji, fail here."""
    start = text.index(secret)
    expected = "".join(c if c == "\n" else "*" for c in secret)
    assert masked[start:start + len(secret)] == expected, masked
    assert masked[start - 1] == text[start - 1], masked


@pytest.mark.skipif(not os.environ.get("DAODAN_SECRETLINT"), reason="DAODAN_SECRETLINT names no real executable")
def test_the_real_secretlint_loads_nothing_of_the_project(trapped, tmp_path, monkeypatch):
    """The pinned executable (DAODAN_SECRETLINT, checked against the release's sha256). The report, in the warnings
    summary, says for each vector alone whether a naive start loads it: that is a fact about this executable, not
    the claim. The claim, which passes or fails the test: started by Daodan in the project holding every vector,
    with their variables set, it loads none of them, masks the private key and keeps the lines; and on a text with
    two secrets of different kinds after non-ASCII characters it masks each exactly where it stands."""
    import warnings
    import secret_mask
    project, mark, checked = trapped
    program = Path(os.environ["DAODAN_SECRETLINT"]).resolve()
    assert secret_mask._sha256(program) in {digest for _asset, digest in secret_mask.ASSETS.values()}
    report = [_naive(program, tmp_path, name, vector) for name, vector in VECTORS.items()]
    warnings.warn("Secretlint naive starts:\n" + "\n".join(report), stacklevel=1)
    monkeypatch.setattr(secret_mask, "executable", lambda: program)
    result = secret_mask.masked(SIGNING, str(checked))
    two = secret_mask.masked(TWO_KINDS, "settings.py")
    warnings.warn(f"Secretlint through secret_mask: {result['found']} {result['kinds']}; "
                  f"{two['found']} {two['kinds']}", stacklevel=1)
    assert not mark.exists(), mark.read_text(encoding="utf-8")
    assert result["found"] >= 1 and result["kinds"] and "MIIBOgIBAAJB" not in result["text"]
    assert result["text"].count("\n") == SIGNING.count("\n")
    assert two["found"] >= 2 and len(two["kinds"]) >= 2, two
    assert len(two["text"]) == len(TWO_KINDS) and two["text"].count("\n") == TWO_KINDS.count("\n")
    _masked_exactly(TWO_KINDS, two["text"], GITHUB_TOKEN)
    _masked_exactly(TWO_KINDS, two["text"], KEY_BODY)
    assert two["text"].startswith("# café \U0001F600 — two secrets\nTOKEN = \"\U0001F600 *")
    assert two["text"].endswith("print('è fine')\n")
