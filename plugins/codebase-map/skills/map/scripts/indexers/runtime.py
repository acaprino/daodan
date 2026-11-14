"""What every indexer run shares: the engine pass's install and mirror, the downloads it allows, its outcome.

An indexer installs on first use into the shared directory (`resolve_edges.shared_engine_dir`), published
whole, with one log line and no question. It runs in a mirror of the project (`MirroredEngine.build_mirror`),
removed after the run, so nothing is written in the project (requirement 22 of the engine specification). It
starts only with its `MIN_FREE` of memory free, the peak measured on a benchmark case rounded up to 256 MB, and
downloads nothing with less than 1 GB free on the shared directory's drive.

The outcome is the contract `code_graph` reads, `{"indexes", "indexer", "runs"}`. Without an index it also
holds `state` and `reason`: `unavailable` with `install`, what to do (no download, not enough memory or disk),
or `failed` with the stderr tail of the last run and `errors`, how many `ERROR` lines the indexer wrote.
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import code_graph
import resolve_edges as rx

MIN_DISK = 2**30
NODE_VERSION = "v22.23.4"  # nodejs.org; scip-typescript 0.5.2 needs Node 22.13 or later
NODE_PLATFORMS = {"win-x64": "win-x64", "win-arm64": "win-arm64", "linux-x64": "linux-x64",
                  "linux-arm64": "linux-arm64", "osx-x64": "darwin-x64", "osx-arm64": "darwin-arm64"}
REAL = ".daodan-real"


class Unavailable(Exception):
    """An indexer that cannot run here: `reason`, and `install`, what to do about it."""

    def __init__(self, reason: str, install: str):
        super().__init__(reason)
        self.reason, self.install = reason, install


class Tool(rx.MirroredEngine):
    """An indexer as the engine pass knows a server: installed on first use (`_install`), run in a mirror."""

    def __init__(self, project_dir: Path, name: str, version: str, skip: tuple = (".git",)):
        super().__init__(project_dir)
        self.name = self.server_name = name
        self.install_root = rx.shared_engine_dir(name)
        self.mirror_skip = skip
        self._version = version

    def pinned(self) -> dict:
        return {"version": self._version}

    def installed(self) -> bool:
        return (self.home() / ".installed").is_file()


@contextlib.contextmanager
def mirrored(engine: rx.MirroredEngine, links: dict | None = None):
    """The engine's mirror of the project for the time of a run, removed after it whatever happens."""
    engine.mirror = engine.build_mirror(links)
    try:
        yield engine.mirror
    finally:
        engine.cleanup()


def real(directories, work_dir: Path) -> dict:
    """Links that make each directory a real one in the mirror, with its files copied: `build_mirror` turns
    every parent of a link into a directory of its own, and this link, to an empty directory, names nothing
    the project has. A tool that writes beside a manifest (`go.sum`, `Cargo.lock`) writes into a copy there, and
    one that never follows a link (`go list ./...`) walks it."""
    empty = Path(work_dir) / "mirror-empty"
    empty.mkdir(parents=True, exist_ok=True)
    return {f"{directory}/{REAL}": empty for directory in sorted(set(directories)) if directory}


def memory(name: str, min_free: int) -> None:
    free = rx.free_memory()
    if free is not None and free < min_free:
        raise Unavailable(f"{free / 2**30:.1f} GB of memory free; {name} starts with at least "
                          f"{min_free / 2**30:.1f} GB", "close other programs to free memory, then analyze again")


def room() -> None:
    """Before a download: nothing is downloaded with less than 1 GB free on the shared directory's drive."""
    cache = rx.shared_cache_dir()
    existing = next((path for path in (cache, *cache.parents) if path.exists()), Path(cache.anchor))
    free = shutil.disk_usage(existing).free
    if free < MIN_DISK:
        raise Unavailable(f"{free / 2**30:.1f} GB free on the drive of {cache}; Daodan downloads nothing with "
                          "less than 1 GB", f"free at least 1 GB on the drive of {cache}, then analyze again")


def excerpt(text: str) -> str:
    """A long error kept to its start, where a crash states its cause, and to its end."""
    text = (text or "").strip()
    return text if len(text) <= 800 else f"{text[:300].rstrip()}\n...\n{text[-400:].lstrip()}"


@contextlib.contextmanager
def fetching(what: str, source: str):
    """A download or install that fails, or a checksum that does not match, as `unavailable`."""
    try:
        yield
    except subprocess.CalledProcessError as error:
        detail = error.stderr or error.stdout or ""
        detail = excerpt(detail.decode("utf-8", "replace") if isinstance(detail, bytes) else detail)
        raise Unavailable(f"{what} could not be installed (exit code {error.returncode}): {detail}",
                          f"check the network: Daodan installs {what} from {source}") from error
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise Unavailable(f"{what} could not be downloaded: {error}",
                          f"check the network: Daodan downloads {what} from {source}") from error


def environment(*paths: Path, **variables: str) -> dict:
    """A Node tool's environment: `paths` first on the PATH, `variables` set, npm's and Node's caches in the
    shared directory."""
    return {**os.environ, **rx.node_environment(), **variables,
            "PATH": os.pathsep.join([*(str(path) for path in paths), os.environ.get("PATH", "")])}


@contextlib.contextmanager
def on_path(directory: Path):
    """`directory` first on this process's PATH, for a product function that looks a program up there."""
    before = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{directory}{os.pathsep}{before}"
    try:
        yield
    finally:
        os.environ["PATH"] = before


def node_directory(home: Path) -> Path:
    """Where Node's release, unpacked in `home`, keeps `node` and `npm`."""
    top = Path(home) / f"node-{NODE_VERSION}-{NODE_PLATFORMS[rx._platform()]}"
    return top if os.name == "nt" else top / "bin"


def _npm_cli(directory: Path) -> Path:
    top = directory if os.name == "nt" else directory.parent
    return top / ("node_modules" if os.name == "nt" else "lib/node_modules") / "npm/bin/npm-cli.js"


def _release(asset: str, partial: Path) -> Path:
    """Node's `asset` at the pinned release, downloaded into `partial`, checked against the release's
    SHASUMS256."""
    base = f"https://nodejs.org/dist/{NODE_VERSION}/"
    with rx.open_url(base + "SHASUMS256.txt", timeout=60) as response:
        rows = [line.split() for line in response.read().decode("ascii", "replace").splitlines()]
    sums = {row[1]: row[0] for row in rows if len(row) == 2}
    if asset not in sums:
        raise ValueError(f"{asset} is not in the release's SHASUMS256.txt")
    return rx.download(base + asset, partial / asset, sha256=sums[asset])


def node(project_dir: Path) -> Path:
    """The directory of Node at the pinned release, installed once, checked against the release's SHASUMS256."""
    tool = Tool(project_dir, "node", NODE_VERSION)
    asset = f"node-{NODE_VERSION}-{NODE_PLATFORMS[rx._platform()]}.{'zip' if os.name == 'nt' else 'tar.gz'}"

    def fill(partial: Path) -> None:
        archive = _release(asset, partial)
        rx.unpack(archive, partial)
        archive.unlink()

    if not tool.installed():
        room()
        with fetching(f"Node {NODE_VERSION}", "nodejs.org"):
            tool._install(tool.home(), fill)
    return node_directory(tool.home())


def node_archive(project_dir: Path, platform: str) -> Path:
    """Node's release archive for `platform` (`linux-x64`, a key of `NODE_PLATFORMS`), downloaded once and
    checked like the host's, kept packed: a container unpacks it."""
    name = NODE_PLATFORMS[platform]
    tool = Tool(project_dir, "node", f"{NODE_VERSION}-{name}")
    asset = f"node-{NODE_VERSION}-{name}.tar.gz"
    if not tool.installed():
        room()
        with fetching(f"Node {NODE_VERSION} for {name}", "nodejs.org"):
            tool._install(tool.home(), lambda partial: _release(asset, partial))
    return tool.home() / asset


def npm_package(project_dir: Path, directory: Path, package: str, version: str) -> Path:
    """An npm package at its pinned version, installed once without its install scripts (npm checks each
    tarball against the registry's integrity): the script its `bin` names, which `node` runs."""
    name = package.rsplit("/", 1)[-1]
    tool = Tool(project_dir, name, version)

    def fill(partial: Path) -> None:
        subprocess.run([str(directory / rx.executable_name("node")), str(_npm_cli(directory)), "install",
                        "--prefix", str(partial), "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
                        f"{package}@{version}"], check=True, env=environment(directory), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=1800)

    if not tool.installed():
        room()
        with fetching(f"{name} {version}", "the npm registry"):
            tool._install(tool.home(), fill)
    root = tool.home() / "node_modules" / package
    declared = json.loads((root / "package.json").read_text(encoding="utf-8")).get("bin")
    return root / (declared if isinstance(declared, str) else declared[name])


def clear(work_dir: Path, name: str) -> None:
    """The index files an earlier run left in `work_dir`, so only this run's are read."""
    for stale in Path(work_dir).glob(f"{name}-*.scip"):
        stale.unlink()


def outcome(name: str, version: str, runs: list[dict]) -> dict:
    out = {"indexes": [[run["index"], run["prefix"]] for run in runs if run.get("index")], "runs": runs,
           "indexer": code_graph.indexer(name, version, runs)}
    if not out["indexes"]:
        last = runs[-1] if runs else {}
        tail = excerpt(last.get("stderr_tail") or last.get("stdout_tail") or "")
        out.update(state="failed", reason=f"{name} wrote no index (exit code {last.get('returncode')}): {tail}",
                   errors=sum(run.get("stderr_errors") or 0 for run in runs))
    return out


def refused(name: str, version: str, error: Unavailable) -> dict:
    return {"indexes": [], "runs": [], "indexer": {"name": name, "version": version, "seconds": 0, "peak_mb": None},
            "state": "unavailable", "reason": error.reason, "install": error.install}
