"""Locate and invoke an externally installed SlidePoise runtime.

The bridge does not install packages or change directories. SlidePoise owns its
runtime and reconstruction scripts; Daodan forwards arguments to that runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Mapping


PROBE = """import json
from framework.paths import SKILL_ROOT, DEFAULT_CONFIG, data_home
print(json.dumps({
    "skill_root": str(SKILL_ROOT.resolve()),
    "config": str(DEFAULT_CONFIG.resolve()),
    "data_home": str(data_home()),
}))
"""


class BridgeError(Exception):
    """An installed runtime cannot satisfy the requested command."""


@dataclass(frozen=True)
class Runtime:
    python: Path
    skill_root: Path
    config: Path
    data_home: Path

    def as_dict(self) -> dict[str, str]:
        return {name: str(getattr(self, name)) for name in self.__dataclass_fields__}


def runtime_home(
    environ: Mapping[str, str] | None = None, user_home: Path | None = None
) -> Path:
    values = os.environ if environ is None else environ
    override = values.get("SLIDEPOISE_HOME")
    return (Path(override).expanduser() if override else
            (user_home if user_home is not None else Path.home()) / ".slidepoise").resolve()


def managed_python(home: Path, platform: str | None = None) -> Path:
    host = os.name if platform is None else platform
    if host == "nt":
        return home / "python" / "Scripts" / "python.exe"
    return home / "python" / "bin" / "python"


def _environment(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ)
    if overrides is not None:
        values.update(overrides)
    return values


def _payload_path(payload: dict, name: str) -> Path:
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise BridgeError(f"SlidePoise discovery returned an invalid {name!r} path.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise BridgeError(f"SlidePoise discovery returned a relative {name!r} path: {value}")
    return path.resolve()


def _required_skill_file(root: Path, relative: str) -> Path:
    candidate = root / relative
    if not candidate.is_file():
        raise BridgeError(f"Installed SlidePoise skill is missing {candidate}.")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise BridgeError(f"Installed SlidePoise skill file escapes its root: {candidate}")
    return candidate


def discover(
    environ: Mapping[str, str] | None = None,
    user_home: Path | None = None,
    platform: str | None = None,
) -> Runtime:
    environment = _environment(environ)
    python = managed_python(runtime_home(environment, user_home), platform)
    if not python.is_file():
        raise BridgeError(
            f"Managed SlidePoise Python was not found at {python}. "
            "Install the SlidePoise runtime or set SLIDEPOISE_HOME to its installation home. "
            "A standalone skill installation does not supply this runtime."
        )
    try:
        completed = subprocess.run(
            [str(python), "-c", PROBE], capture_output=True, text=True,
            env=environment,
        )
    except OSError as error:
        raise BridgeError(f"Cannot start managed SlidePoise Python at {python}: {error}") from error
    if completed.returncode:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise BridgeError(f"Cannot discover SlidePoise framework paths using {python}: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as error:
        raise BridgeError("SlidePoise discovery did not return valid JSON.") from error
    if not isinstance(payload, dict):
        raise BridgeError("SlidePoise discovery did not return a JSON object.")
    root = _payload_path(payload, "skill_root")
    config = _payload_path(payload, "config")
    home = _payload_path(payload, "data_home")
    _required_skill_file(root, "SKILL.md")
    runtime = Runtime(python, root, config, home)
    installed_script(runtime, "slidepoise_runtime.py")
    if not config.is_file():
        raise BridgeError(f"Installed SlidePoise framework config is missing {config}.")
    return runtime


def installed_script(runtime: Runtime, name: str) -> Path:
    relative = PurePosixPath(name.replace("\\", "/"))
    if (not name or "\x00" in name or relative.is_absolute()
            or PureWindowsPath(name).anchor or ".." in relative.parts):
        raise BridgeError(f"Script must be a relative path inside the installed skill: {name!r}")
    if relative.parts and relative.parts[0] == "scripts":
        relative = PurePosixPath(*relative.parts[1:])
    if relative.suffix != ".py":
        raise BridgeError(f"Script must name an installed Python script: {name!r}")
    scripts = runtime.skill_root / "scripts"
    if not scripts.resolve().is_relative_to(runtime.skill_root.resolve()):
        raise BridgeError(f"Installed SlidePoise scripts directory escapes its skill root: {scripts}")
    return _required_skill_file(scripts, relative.as_posix())


def run_cli(runtime: Runtime, arguments: list[str]) -> int:
    return _run([str(runtime.python), "-m", "framework.cli", *arguments], runtime.data_home)


def run_script(runtime: Runtime, name: str, arguments: list[str]) -> int:
    return _run([str(runtime.python), str(installed_script(runtime, name)), *arguments], runtime.data_home)


def _run(arguments: list[str], home: Path) -> int:
    try:
        return subprocess.run(arguments, env=_environment({"SLIDEPOISE_HOME": str(home)})).returncode
    except OSError as error:
        raise BridgeError(f"Cannot start SlidePoise command: {error}") from error


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", metavar="PATH", help="Use this SlidePoise installation home")
    parser.add_argument("command", choices=("discover", "cli", "script"))
    # Everything after the verb belongs to the runtime, including --help.
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(arguments)
    if parsed.command == "discover" and parsed.arguments:
        parser.error("discover accepts no arguments")
    if parsed.command == "script" and not parsed.arguments:
        parser.error("script requires a relative Python script name")
    try:
        runtime = discover(environ={"SLIDEPOISE_HOME": parsed.home}) if parsed.home else discover()
        if parsed.command == "discover":
            print(json.dumps(runtime.as_dict(), indent=2))
            return 0
        name = parsed.arguments[0] if parsed.command == "script" else None
        forwarded = parsed.arguments[1:] if name is not None else parsed.arguments
        if forwarded and forwarded[0] == "--":
            forwarded = forwarded[1:]
        if parsed.command == "cli":
            return run_cli(runtime, forwarded)
        return run_script(runtime, name, forwarded)
    except BridgeError as error:
        print(f"slidepoise-bridge: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
