"""The pinned release of stack-analyser, installed on first use and started outside the analysed project.

The release is a Node program (`package/dist/cli.mjs` of its `.tgz`): the recogniser of the project's technologies,
a fork of Specfy's. A project's files are its data, so it runs in a folder of its own outside every project, in
Daodan's own pinned Node, with the project named only by its argument and without the caller's `NODE_` variables
(`NODE_OPTIONS` and `NODE_PATH` lead Node to code of the caller's choosing). The declarations Daodan already read go
in files of that folder, not on the command line. Nothing of the folder outlives the run.
"""
from __future__ import annotations

import contextlib
import functools
import http.client
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from container import Gap

VERSION = "1.27.6-daodan.6"
URL = f"https://github.com/acaprino/stack-analyser-daodan/releases/download/v{VERSION}/stack-analyser-daodan-{VERSION}.tgz"
SHA256 = "d9f9b2f0200b5f4ed2479fa1583a9ff308d96ca7bf5accde9df5827ed772a209"  # of the `.tgz` above
PROGRAM = "package/dist/cli.mjs"  # in the archive
TIMEOUT = 300  # seconds for one project, start included; the real run time is not measured yet
UNSET = "NODE_"  # what Node reads as its own options or module paths
_failed: dict[str, Gap] = {}  # an install that failed, by tool: it is not tried again in this process


def _remembered(function):
    """`function` that, once it raised a `Gap`, raises that same `Gap` again without trying: an install that failed
    (no network, no disk) would otherwise be retried, with its waits, at every scan. Daodan serves from one process,
    so analyzing again returns the same `Gap`: its remedy, completed once when it is stored, says to restart."""
    @functools.wraps(function)
    def wrapper(*arguments):
        if function.__name__ not in _failed:
            try:
                return function(*arguments)
            except Gap as gap:
                gap.remedy += "; this process remembers the failure, so restart Daodan before analyzing again"
                _failed[function.__name__] = gap
        raise _failed[function.__name__].with_traceback(None)  # a stored exception's traceback grows at each raise

    wrapper.cache_clear = lambda: (_failed.pop(function.__name__, None), getattr(function, "cache_clear", int)())
    return wrapper


@_remembered
@functools.cache
def cli() -> Path:
    """The release's `cli.mjs`, downloaded on the first call into Daodan's shared tool folder, checked against the
    release's sha256 and published whole. `Gap` when it cannot be had."""
    import engine_tools

    def fill(partial: Path) -> None:
        archive = engine_tools.download(URL, partial / "release.tgz", sha256=SHA256)
        engine_tools.unpack(archive, partial)
        archive.unlink()

    try:
        home = engine_tools.shared_engine_dir("stack-analyser") / VERSION
        if not (home / ".installed").is_file():
            print(f"installing stack-analyser {VERSION} into {home} (first use)", flush=True)
            engine_tools.publish(home, fill, VERSION)
    except (OSError, ValueError, http.client.HTTPException, tarfile.TarError) as error:
        raise Gap(f"stack-analyser {VERSION} could not be downloaded and verified: {error}",
                  "check the connection to github.com, then analyze again") from error
    if not (home / PROGRAM).is_file():
        raise Gap(f"stack-analyser {VERSION} is installed without {PROGRAM}",
                  f"remove {home}, then analyze again")
    return home / PROGRAM


@_remembered
def node(project: Path) -> Path:
    """The executable of Daodan's own pinned Node, installed on first use. `Gap` when it cannot be had."""
    import engine_tools
    from indexers import runtime
    try:
        return runtime.node(project) / engine_tools.executable_name("node")
    except runtime.Unavailable as error:
        raise Gap(error.reason, error.install) from error
    except ValueError as error:  # `DAODAN_SHARED_DIR` that is not absolute
        raise Gap(f"Node could not be installed: {error}", "fix DAODAN_SHARED_DIR, then analyze again") from error
    except OSError as error:
        raise Gap(f"Node could not be installed: {error}", "check the connection to nodejs.org, then analyze again") \
            from error


def _installed(project: Path) -> tuple[Path, Path]:
    """`cli()` and `node(project)`, the release first: without it Node is not downloaded. A first install's lines go to
    stderr: the stdio MCP server and `snapshot.py hook` reach a run, and their stdout is a protocol stream."""
    with contextlib.redirect_stdout(sys.stderr):
        script = cli()
        return script, node(project)


def command(node: Path, cli: Path, project: Path, output: Path, declarations: Path | None,
            perimeter: Path) -> list[str]:
    """The command line of one run. `perimeter` names the file of the folders to skip and the paths to ignore."""
    argv = [str(node), str(cli), str(project), "--output", str(output)]
    if declarations is not None:
        argv += ["--declarations", str(declarations)]
    return argv + ["--perimeter", str(perimeter)]


def _environment() -> dict:
    import engine_tools
    try:
        added = engine_tools.node_environment()
    except (OSError, ValueError) as error:
        raise Gap(f"Daodan's cache folder for Node could not be used: {error}",
                  "fix DAODAN_SHARED_DIR or free space on that drive, then analyze again") from error
    return {key: value for key, value in os.environ.items() if not key.upper().startswith(UNSET)} | added


def _write(path: Path, content, what: str) -> Path:
    """`content` as UTF-8 JSON in `path`, in the run's own folder. `Gap` when it cannot be written."""
    try:
        path.write_bytes(json.dumps(content, ensure_ascii=False).encode("utf-8"))
    except UnicodeError as error:  # a lone surrogate: a manifest's `\ud800`, a file name that is not UTF-8
        raise Gap(f"stack-analyser's {what} could not be written: one holds text that is not valid Unicode",
                  "rename the file or folder whose name is not valid UTF-8, or fix the manifest string that holds a "
                  "lone surrogate, then analyze again") from error
    except OSError as error:
        raise Gap(f"stack-analyser's {what} could not be written: {error}",
                  f"free space on the drive of {tempfile.gettempdir()}, then analyze again") from error
    return path


@contextlib.contextmanager
def _folder():
    """The run's own folder, removed with its content when the run ends. `Gap` when it cannot be made."""
    try:
        made = tempfile.TemporaryDirectory(prefix="daodan-stack-", ignore_cleanup_errors=True)
    except OSError as error:
        raise Gap(f"stack-analyser's folder could not be made: {error}",
                  f"free space on the drive of {tempfile.gettempdir()}, then analyze again") from error
    with made as folder:
        yield Path(folder)


def _start(argv: list[str], folder: Path) -> subprocess.CompletedProcess:
    """One run of the release in `folder`, with its environment. `Gap` on a timeout or when it cannot start."""
    try:
        return subprocess.run(argv, cwd=folder, env=_environment(), stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        raise Gap(f"stack-analyser gave no answer within {TIMEOUT} s",
                  "check a smaller project, or leave out its large folders") from error
    except OSError as error:
        raise Gap(f"stack-analyser could not start: {error}", "check Node in Daodan's tool folder") from error


def _answer(ended: subprocess.CompletedProcess, output: Path):
    """The JSON the release wrote to `output`. `Gap` on a failure or an output that is not JSON."""
    said = ended.stderr.decode("utf-8", "replace").strip()[-600:] or "no message"
    remedy = "fix what the message says, or remove the release in Daodan's tool folder to install it again"
    if ended.returncode:
        raise Gap(f"stack-analyser failed (exit {ended.returncode}): {said}", remedy)
    try:
        return json.loads(output.read_bytes())
    except OSError as error:
        raise Gap(f"stack-analyser wrote no output ({error}): {said}", remedy) from error
    except ValueError as error:
        raise Gap(f"stack-analyser's output is not JSON: {error}", remedy) from error


def run(project: Path, *, declarations: list[dict] = (), skip_dirs: tuple[str, ...] = (),
        ignore: tuple[str, ...] = ()) -> dict:
    """The release's JSON for `project`. `declarations` and the perimeter (`skip_dirs`, always passed, and `ignore`)
    are written as UTF-8 JSON in the run's own folder. On a failure, a timeout or an output that is not a JSON object:
    `Gap`."""
    project = Path(project).resolve()
    script, program = _installed(project)
    with _folder() as folder:
        output = folder / "output.json"
        declared = _write(folder / "declarations.json", declarations, "declarations") if declarations else None
        perimeter = _write(folder / "perimeter.json", {"skipDirs": list(skip_dirs), "ignore": list(ignore)}, "perimeter")
        answer = _answer(_start(command(program, script, project, output, declared, perimeter), folder),
                         output)
        if not isinstance(answer, dict):
            raise Gap("stack-analyser's output is not JSON: expected a JSON object",
                      "fix what the message says, or remove the release in Daodan's tool folder to install it again")
        return answer


def catalogue() -> list[dict]:
    """The release's catalogue of rules (`--catalogue`), written to a file of the run's own folder. `Gap` as for `run`."""
    with _folder() as folder:
        output = folder / "catalogue.json"
        script, program = _installed(folder)  # no project: Node's install is the one of the empty run folder
        answer = _answer(_start([str(program), str(script), "--catalogue", str(output)], folder), output)
        if not isinstance(answer, list):
            raise Gap("stack-analyser's catalogue is not a JSON array",
                      "remove the release in Daodan's tool folder to install it again")
        return answer
