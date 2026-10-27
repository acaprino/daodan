"""Install an official DeckCraft, WordCraft or GridCraft CLI into an owned directory.

Office delegates native Word, PowerPoint and Excel work to these external engines
and ships none of their code. This helper fetches the pinned official release
asset from GitHub, checks its size and SHA-256, extracts it into
`<engine home>/<engine>/<version>/` and proves the CLI answers `--version`.
It never runs without the user's approval, takes no URL from its caller and
touches nothing outside the engine home. `DAODAN_ENGINE_HOME` overrides the
default `~/.daodan/engines`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RECEIPT = ".daodan-engine.json"
MAX_UNPACKED = 1 << 30
LICENCE = "MIT OR Apache-2.0"

ENGINES = {
    "deckcraft": {"version": "0.10.0", "assets": {
        "windows-x64": ("deckcraft-0.10.0-windows-x64-portable.zip", 81131163,
                        "042d62082e9a5c795ee870cbfd652ef31917867ae058c6d33d17d1b2a2d7fb8a"),
        "linux-x86_64": ("deckcraft-0.10.0-linux-x86_64.tar.gz", 81279161,
                         "546616eb2300ce8efb20b44a53e60abfe6b96d71ac606b452a36fd21c6b1ff28"),
        "macos-universal": ("deckcraft-cli-0.10.0-macos-universal.zip", 72604593,
                            "7c4553a096d2abf7a2b3feb43affc6fcf7f188f035b055b60a9a707b5f690ddb")}},
    "wordcraft": {"version": "0.10.0", "assets": {
        "windows-x64": ("wordcraft-0.10.0-windows-x64-portable.zip", 101190784,
                        "141d9458d776b4a664f20fbb0e2cd5619c327e0873abbc01bf4530dc339592fb"),
        "linux-x86_64": ("wordcraft-0.10.0-linux-x86_64.tar.gz", 102094935,
                         "ca99ea350ba0aea4103fc8020cad98f051c58d9e9fcf670c119d810108cc45ff"),
        "macos-universal": ("wordcraft-cli-0.10.0-macos-universal.zip", 89651340,
                            "09e3defc57675597f3388fd1b4d4e20b97be3f4e0cd517ae580fc28b421cc1d2")}},
    "gridcraft": {"version": "0.11.1", "assets": {
        "windows-x64": ("gridcraft-0.11.1-windows-x64-portable.zip", 19375904,
                        "341ba9980627f75ec9e1320efd28e9a94b27dd595430c141c9bf31dcd6621a35"),
        "linux-x86_64": ("gridcraft-0.11.1-linux-x86_64.tar.gz", 20503035,
                         "f2c83e6c26449a6c45983e903bf32c1d4c302b2042f263ead995271129c70e87"),
        "macos-universal": ("gridcraft-cli-0.11.1-macos-universal.zip", 11467928,
                            "5a1bde181fc38e09e3c3661c33d6b8e924032dc0950de2ba236913294ed3a653")}},
}


class InstallError(ValueError):
    """The engine cannot be planned, fetched, unpacked or proved."""


def engine_home(environ=None):
    env = os.environ if environ is None else environ
    return Path(env.get("DAODAN_ENGINE_HOME") or Path.home() / ".daodan" / "engines").expanduser().resolve()


def platform_key(system=None, machine=None):
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    if system == "win32" and machine in {"amd64", "x86_64"}:
        return "windows-x64"
    if system.startswith("linux") and machine in {"amd64", "x86_64"}:
        return "linux-x86_64"
    if system == "darwin":
        return "macos-universal"
    raise InstallError(f"No pinned release for {system} {machine}. Install the official package yourself from "
                       "the engine's releases page and set the engine's CLI variable or PATH.")


def plan(engine, environ=None, key=None):
    if engine not in ENGINES:
        raise InstallError(f"Unknown engine {engine!r}; expected one of {', '.join(ENGINES)}.")
    spec = ENGINES[engine]
    key = key or platform_key()
    if key not in spec["assets"]:
        raise InstallError(f"No pinned {engine} release for {key}.")
    asset, size, digest = spec["assets"][key]
    version = spec["version"]
    return {"engine": engine, "version": version, "platform": key, "asset": asset, "size": size, "sha256": digest,
            "url": f"https://github.com/storytold/{engine}/releases/download/v{version}/{asset}",
            "licence": LICENCE, "destination": str(engine_home(environ) / engine / version)}


def find(engine, environ=None):
    """The installed CLI of the pinned version, or None."""
    if engine not in ENGINES:
        raise InstallError(f"Unknown engine {engine!r}; expected one of {', '.join(ENGINES)}.")
    version = ENGINES[engine]["version"]
    root = engine_home(environ) / engine / version
    try:
        receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
        binary = (root / receipt["binary"]).resolve()
    except (OSError, ValueError, KeyError):
        return None
    ok = (receipt.get("engine") == engine and receipt.get("version") == version
          and binary.is_file() and binary.is_relative_to(root.resolve()))
    return binary if ok else None


def download(url, destination, size, digest):
    request = urllib.request.Request(url, headers={"User-Agent": "daodan-engine-install"})
    received, hasher = 0, hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(destination, "wb") as out:
            while chunk := response.read(1 << 20):
                received += len(chunk)
                if received > size:
                    raise InstallError("Download is larger than the pinned size.")
                hasher.update(chunk)
                out.write(chunk)
    except OSError as exc:
        raise InstallError(f"Cannot download {url}: {exc}") from exc
    if received != size or hasher.hexdigest() != digest:
        raise InstallError("Downloaded file does not match the pinned size and SHA-256; nothing was installed.")


def _target(root, name):
    parts = name.replace("\\", "/").split("/")
    if name.startswith(("/", "\\")) or ":" in parts[0] or ".." in parts:
        raise InstallError(f"Unsafe path in archive: {name!r}")
    target = root.joinpath(*[part for part in parts if part not in ("", ".")]).resolve()
    if target != root and root not in target.parents:
        raise InstallError(f"Unsafe path in archive: {name!r}")
    return target


def _write(root, name, source, mode, total):
    target = _target(root, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as out:
        while chunk := source.read(1 << 20):
            total[0] += len(chunk)
            if total[0] > MAX_UNPACKED:
                raise InstallError("Archive unpacks to more than 1 GiB.")
            out.write(chunk)
    if mode & 0o111:
        target.chmod(target.stat().st_mode | stat.S_IXUSR)


def extract(archive, root):
    root.mkdir(parents=True)
    root, total = root.resolve(), [0]
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                kind = stat.S_IFMT(info.external_attr >> 16)
                if kind == stat.S_IFLNK:
                    raise InstallError(f"Archive holds a symbolic link: {info.filename!r}")
                if info.is_dir():
                    _target(root, info.filename).mkdir(parents=True, exist_ok=True)
                else:
                    with bundle.open(info) as source:
                        _write(root, info.filename, source, (info.external_attr >> 16) & 0o777, total)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as bundle:
            for member in bundle:
                if member.isdir():
                    _target(root, member.name).mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    _write(root, member.name, bundle.extractfile(member), member.mode, total)
                else:
                    raise InstallError(f"Archive holds a link or special file: {member.name!r}")
    else:
        raise InstallError("Downloaded file is neither a zip nor a tar archive.")


def locate(root, engine):
    wanted = {f"{engine}-cli", f"{engine}-cli.exe"}
    found = [path for path in root.rglob("*") if path.is_file() and path.name.lower() in wanted]
    if len(found) != 1:
        raise InstallError(f"Expected exactly one {engine}-cli in the archive, found {len(found)}.")
    return found[0]


def probe(binary, engine, version):
    try:
        run = subprocess.run([str(binary), "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        hint = (" The path is too long for Windows; set DAODAN_ENGINE_HOME to a shorter directory."
                if os.name == "nt" and len(str(binary)) >= 240 else "")
        raise InstallError(f"The installed {engine}-cli does not start: {exc}.{hint}") from exc
    if run.returncode or run.stdout.strip() != f"{engine}-cli {version}":
        raise InstallError(f"Unexpected version response from {binary.name}: "
                           f"{(run.stdout or run.stderr).strip()[:200]!r}")


def install(engine, approved, environ=None, key=None, fetch=download, check=probe):
    spec = plan(engine, environ, key)
    present = find(engine, environ)
    if present:
        return {"status": "present", "binary": str(present), **spec}
    if not approved:
        raise InstallError("Installing needs the user's approval, which the request for the work gives. Tell them "
                           "in one line what `plan` reports (source, size, licence, destination), then rerun "
                           "with --approved.")
    final = Path(spec["destination"])
    if final.exists():
        raise InstallError(f"{final} exists without a valid receipt; remove it yourself, nothing was changed.")
    final.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".s", dir=final.parent))
    try:
        archive = staging / spec["asset"]
        fetch(spec["url"], archive, spec["size"], spec["sha256"])
        tree = staging / "t"
        extract(archive, tree)
        binary = locate(tree, engine)
        check(binary, engine, spec["version"])
        receipt = {"engine": engine, "version": spec["version"], "asset": spec["asset"], "sha256": spec["sha256"],
                   "url": spec["url"], "binary": binary.relative_to(tree).as_posix(),
                   "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (tree / RECEIPT).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        os.replace(tree, final)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return {"status": "installed", "binary": str(find(engine, environ)), **spec}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "find", "install"):
        child = commands.add_parser(name)
        child.add_argument("engine", choices=sorted(ENGINES))
        if name == "install":
            child.add_argument("--approved", action="store_true",
                               help="The user's request for the work authorizes this download")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = plan(args.engine)
        elif args.command == "find":
            binary = find(args.engine)
            if not binary:
                raise InstallError(f"{args.engine} is not installed in {engine_home()}.")
            result = {"engine": args.engine, "binary": str(binary)}
        else:
            result = install(args.engine, args.approved)
    except InstallError as exc:
        print(f"engine-install: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
