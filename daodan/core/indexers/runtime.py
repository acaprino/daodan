"""What every indexer run shares: the engine pass's install and mirror, the downloads it allows, its outcome.

An indexer installs on first use into the shared directory (`resolve_edges.shared_engine_dir`), published
whole, with one log line and no question. It runs in a mirror of the project (`Tool.build_mirror`),
removed after the run, so nothing is written in the project (requirement 22 of the engine specification). It
starts only with its `MIN_FREE` of memory free, the peak measured on a benchmark case rounded up to 256 MB, and
downloads nothing with less than 1 GB free on the shared directory's drive.

The outcome is the contract `code_graph` reads, `{"indexes", "indexer", "runs"}`. Without an index it also
holds `state` and `reason`: `unavailable` with `install`, what to do (no download, not enough memory or disk),
or `failed` with the stderr tail of the last run and `errors`, how many `ERROR` lines the indexer wrote.
"""
from __future__ import annotations

import contextlib
import http.client
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

import code_graph
import resolve_edges as rx
from engine_tools import publish

MIN_DISK = 2**30
NODE_VERSION = "v22.23.4"  # nodejs.org; the host's Node, for scip-python and the stylesheet engines
NODE_PLATFORMS = {"win-x64": "win-x64", "win-arm64": "win-arm64", "linux-x64": "linux-x64",
                  "linux-arm64": "linux-arm64", "osx-x64": "darwin-x64", "osx-arm64": "darwin-arm64"}
REAL = ".daodan-real"


class Unavailable(Exception):
    """An indexer that cannot run here: `reason`, and `install`, what to do about it."""

    def __init__(self, reason: str, install: str):
        super().__init__(reason)
        self.reason, self.install = reason, install


class Tool:
    """An indexer at its pinned version: installed on first use (`_install`), run in a mirror of the project.

    A package manager asked to read the project's packages may write a lock file or a checksum file beside the
    manifest. The mirror holds a link per top-level directory and a copy of each top-level file, so such a write
    lands in the copy. Removing the mirror never enters a link.
    """

    def __init__(self, project_dir: Path, name: str, version: str, skip: tuple = (".git",)):
        self.project_root = Path(project_dir).resolve()
        self.name, self.version = name, version
        self.install_root = rx.shared_engine_dir(name)
        self.mirror_skip = skip
        self.mirror: Path | None = None

    def home(self) -> Path:
        return self.install_root / self.version

    def installed(self) -> bool:
        return (self.home() / ".installed").is_file()

    def _install(self, home: Path, fill) -> None:
        """Fill a sibling directory, then publish it whole, so an interrupted install leaves nothing usable.

        Each install fills its own: the pass and a worker may install one release at once; the first published
        stays and the other's is dropped."""
        if (home / ".installed").is_file():
            return
        print(f"installing {self.name} {self.version} into {home} (first use)", flush=True)
        publish(home, fill, self.version)

    def build_mirror(self, links: dict | None = None) -> Path:
        mirror = Path(tempfile.mkdtemp(prefix=f"daodan-{self.name}-")) / self.project_root.name
        mirror.mkdir()
        # A directory that receives a link is a real directory of the mirror, one link per child.
        real = {parent.as_posix() for name in links or {} for parent in PurePosixPath(name).parents} - {"."}

        def fill(source: Path, target: Path, relative: PurePosixPath) -> None:
            for entry in source.iterdir():
                if entry.name in self.mirror_skip:
                    continue
                if entry.is_dir():
                    if (relative / entry.name).as_posix() in real:
                        (target / entry.name).mkdir()
                        fill(entry, target / entry.name, relative / entry.name)
                    else:
                        link_directory(target / entry.name, entry)
                elif entry.is_file():
                    shutil.copyfile(entry, target / entry.name)

        fill(self.project_root, mirror, PurePosixPath(""))
        for name, target in (links or {}).items():
            link_directory(mirror / name, target)
        return mirror

    def cleanup(self) -> None:
        if self.mirror is not None:
            remove_mirror(self.mirror)
            self.mirror.parent.rmdir()
            self.mirror = None


def link_directory(link: Path, target: Path) -> None:
    """A directory link: a junction on Windows, which needs no privilege, a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def remove_mirror(root: Path) -> None:
    """Remove a mirror's links and copies without ever entering a link, so no target file is touched."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink() or os.path.isjunction(root):
        return
    for entry in root.iterdir():
        if os.path.isjunction(entry):
            os.rmdir(entry)
        elif entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            remove_mirror(entry)
    root.rmdir()


@contextlib.contextmanager
def mirrored(engine: Tool, links: dict | None = None):
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
    except (OSError, ValueError, http.client.HTTPException, subprocess.SubprocessError) as error:
        raise Unavailable(f"{what} could not be downloaded: {error}",
                          f"check the network: Daodan downloads {what} from {source}") from error


def environment(*paths: Path, **variables: str) -> dict:
    """A Node tool's environment: `paths` first on the PATH, `variables` set, npm's and Node's caches in the
    shared directory."""
    return {**os.environ, **rx.node_environment(), **variables,
            "PATH": os.pathsep.join([*(str(path) for path in paths), os.environ.get("PATH", "")])}


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


def npm_install(directory: Path, prefix: Path, packages: list[str]) -> None:
    """`packages`, each pinned, installed under `prefix` by the npm of the Node in `directory`, without their
    install scripts (npm checks each tarball against the registry's integrity)."""
    subprocess.run([str(directory / rx.executable_name("node")), str(_npm_cli(directory)), "install",
                    "--prefix", str(prefix), "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error",
                    *packages], check=True, env=environment(directory), stdin=subprocess.DEVNULL,
                   capture_output=True, text=True, timeout=1800)


def npm_package(project_dir: Path, directory: Path, package: str, version: str) -> Path:
    """An npm package at its pinned version, installed once (`npm_install`): the script its `bin` names, which
    `node` runs."""
    name = package.rsplit("/", 1)[-1]
    tool = Tool(project_dir, name, version)

    def fill(partial: Path) -> None:
        npm_install(directory, partial, [f"{package}@{version}"])

    def script() -> Path | None:
        root = tool.home() / "node_modules" / package
        try:
            declared = json.loads((root / "package.json").read_text(encoding="utf-8")).get("bin")
        except (OSError, ValueError):
            return None
        return root / (declared if isinstance(declared, str) else declared[name])

    # An install whose mark is there and whose script is gone (a cleaner, a disk fault) is made anew, once.
    if tool.installed() and not (script() and script().is_file()):
        (tool.home() / ".installed").unlink()
    if not tool.installed():
        room()
        with fetching(f"{name} {version}", "the npm registry"):
            tool._install(tool.home(), fill)
    found = script()
    if found is None or not found.is_file():
        raise Unavailable(f"{package} {version} is installed without {found.name if found else 'its package.json'}, "
                          "the script it runs", "check the npm registry and the disk, then analyze again")
    return found


def npm_lockfile(project_dir: Path, directory: Path, name: str, folder: Path) -> Path:
    """The packages that `folder`'s package.json and lockfile pin, installed once by `npm ci` without their install
    scripts (npm checks each tarball against the lockfile's integrity): the folder that holds them, where a script
    resolves its packages from `package.json`. The lockfile's digest is the version: a new pin installs again."""
    import hashlib
    folder = Path(folder)
    tool = Tool(project_dir, name, hashlib.sha256((folder / "package-lock.json").read_bytes()).hexdigest()[:12])

    def fill(partial: Path) -> None:
        for item in ("package.json", "package-lock.json"):
            shutil.copyfile(folder / item, partial / item)
        subprocess.run([str(directory / rx.executable_name("node")), str(_npm_cli(directory)), "ci", "--ignore-scripts",
                        "--no-audit", "--no-fund", "--loglevel=error"], cwd=str(partial), check=True,
                       env=environment(directory), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       timeout=1800)

    if not tool.installed():
        room()
        with fetching(name, "the npm registry"):
            tool._install(tool.home(), fill)
    return tool.home()


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
