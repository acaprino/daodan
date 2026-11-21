"""The pinned release of stack-analyser, installed on first use and started outside the analysed project.

The release is a Node program (`package/dist/cli.mjs` of its `.tgz`): the recogniser of the project's technologies,
a fork of Specfy's. A project's files are its data, so it runs in a folder of its own outside every project, in
Daodan's own pinned Node, with the project named only by its argument and without the caller's `NODE_` variables
(`NODE_OPTIONS` and `NODE_PATH` lead Node to code of the caller's choosing). The declarations Daodan already read go
in a file of that folder, not on the command line. Nothing of the folder outlives the run.
"""
from __future__ import annotations

import functools
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from container import Gap

VERSION = "1.27.6-daodan.1"
URL = f"https://github.com/acaprino/stack-analyser/releases/download/v{VERSION}/specfy-stack-analyser-{VERSION}.tgz"
SHA256 = "ee889f52b054ecf6c900847a8d492f17065a28fe25ddde0d146d8d9915b79baf"  # of the `.tgz` above
PROGRAM = "package/dist/cli.mjs"  # in the archive
TIMEOUT = 300  # seconds for one project, start included; the real run time is not measured yet
UNSET = "NODE_"  # what Node reads as its own options or module paths


@functools.cache
def cli() -> Path:
    """The release's `cli.mjs`, downloaded on the first call into Daodan's shared tool folder, checked against the
    release's sha256 and published whole. `Gap` when it cannot be had."""
    import engine_tools
    home = engine_tools.shared_engine_dir("stack-analyser") / VERSION

    def fill(partial: Path) -> None:
        archive = engine_tools.download(URL, partial / "release.tgz", sha256=SHA256)
        engine_tools.unpack(archive, partial)
        archive.unlink()

    try:
        if not (home / ".installed").is_file():
            print(f"installing stack-analyser {VERSION} into {home} (first use)", flush=True)
            engine_tools.publish(home, fill, VERSION)
    except (OSError, ValueError, tarfile.TarError) as error:
        raise Gap(f"stack-analyser {VERSION} could not be downloaded and verified: {error}",
                  "check the connection to github.com, then analyze again") from error
    if not (home / PROGRAM).is_file():
        raise Gap(f"stack-analyser {VERSION} is installed without {PROGRAM}",
                  f"remove {home}, then analyze again")
    return home / PROGRAM


def node(project: Path) -> Path:
    """The executable of Daodan's own pinned Node, installed on first use. `Gap` when it cannot be had."""
    import engine_tools
    from indexers import runtime
    try:
        return runtime.node(project) / engine_tools.executable_name("node")
    except runtime.Unavailable as error:
        raise Gap(error.reason, error.install) from error
    except OSError as error:
        raise Gap(f"Node could not be installed: {error}", "check the connection to nodejs.org, then analyze again") \
            from error


def command(node: Path, cli: Path, project: Path, output: Path, declarations: Path | None,
            skip_dirs: tuple[str, ...] | None, ignore: tuple[str, ...]) -> list[str]:
    """The command line of one run. `skip_dirs` None leaves the option out (the release's own default), `()` passes
    an empty list: skip nothing."""
    argv = [str(node), str(cli), str(project), "--output", str(output)]
    if declarations is not None:
        argv += ["--declarations", str(declarations)]
    if skip_dirs is not None:
        argv += ["--skip-dirs", ",".join(skip_dirs)]
    if ignore:
        argv += ["--ignore", ",".join(ignore)]
    return argv


def _environment() -> dict:
    import engine_tools
    return {key: value for key, value in os.environ.items() if not key.upper().startswith(UNSET)} \
        | engine_tools.node_environment()


def run(project: Path, *, declarations: list[dict] = (), skip_dirs: tuple[str, ...] | None = None,
        ignore: tuple[str, ...] = ()) -> dict:
    """The release's JSON for `project`. `declarations` are written as UTF-8 JSON in the run's own folder. On a
    failure, a timeout or an output that is not a JSON object: `Gap`."""
    project = Path(project).resolve()
    program, script = node(project), cli()
    with tempfile.TemporaryDirectory(prefix="daodan-stack-") as folder:
        folder, output = Path(folder), Path(folder) / "output.json"
        declared = folder / "declarations.json" if declarations else None
        if declared:
            declared.write_bytes(json.dumps(declarations, ensure_ascii=False).encode("utf-8"))
        try:
            ended = subprocess.run(command(program, script, project, output, declared, skip_dirs, ignore), cwd=folder,
                                   env=_environment(), stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired as error:
            raise Gap(f"stack-analyser gave no answer within {TIMEOUT} s",
                      "check a smaller project, or leave out its large folders") from error
        except OSError as error:
            raise Gap(f"stack-analyser could not start: {error}", "check Node in Daodan's tool folder") from error
        said = ended.stderr.decode("utf-8", "replace").strip()[-600:] or "no message"
        remedy = "fix what the message says, or remove the release in Daodan's tool folder to install it again"
        if ended.returncode:
            raise Gap(f"stack-analyser failed (exit {ended.returncode}): {said}", remedy)
        try:
            answer = json.loads(output.read_bytes())
            if not isinstance(answer, dict):
                raise ValueError("expected a JSON object")
        except OSError as error:
            raise Gap(f"stack-analyser wrote no output ({error}): {said}", remedy) from error
        except ValueError as error:
            raise Gap(f"stack-analyser's output is not JSON: {error}", remedy) from error
        return answer
