"""Versioned, non-interactive boundary to the external Worktrunk executable."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request


PIN_PATH = Path(__file__).resolve().parent.parent / "references" / "upstream.json"
CONFIG_PATH = PIN_PATH.with_name("runtime.toml")
NO_HOOKS_PATH = PIN_PATH.parent / "no-hooks"
RELEASE_API = "https://api.github.com/repos/max-sixty/worktrunk/releases/latest"
VERSION = re.compile(r"^wt v(\d+\.\d+\.\d+)$")
TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


class WorktrunkError(RuntimeError):
    """A failed boundary check; callers must retain any partially created worktree."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def upstream_pin() -> dict:
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


def _environment() -> dict:
    # Inherited Git directory/index overrides would ignore the explicit cwd.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("GIT_", "WORKTRUNK_"))}
    # Worktrunk's --no-hooks controls its own hooks. Git also invokes native
    # post-checkout hooks during worktree creation, so isolate those per process.
    env.update({"GIT_TERMINAL_PROMPT": "0", "NO_COLOR": "1",
                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": str(NO_HOOKS_PATH)})
    return env


def _execute(argv: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess:
    if not math.isfinite(timeout) or timeout <= 0:
        raise WorktrunkError("invalid_timeout", "Timeout must be positive")
    try:
        result = subprocess.run(
            argv, cwd=cwd, env=_environment(), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            shell=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise WorktrunkError("timeout", "Worktrunk timed out; reconcile Git state before retrying") from exc
    except OSError as exc:
        raise WorktrunkError("execution_failed", f"Could not execute Worktrunk: {exc}") from exc
    if result.returncode:
        raise WorktrunkError("command_failed", result.stderr.strip()[:4096] or f"Worktrunk exited {result.returncode}")
    if len(result.stdout.encode("utf-8")) > 4 * 1024 * 1024:
        raise WorktrunkError("output_too_large", "Worktrunk output exceeds the supported JSON limit")
    return result


def _workspace_module():
    # Load the canonical sibling resolver by its shipped path. This avoids a
    # second Git-home implementation and cannot import a project-local module.
    spec = importlib.util.spec_from_file_location("_daodan_runtime_workspaces", Path(__file__).with_name("workspaces.py"))
    workspace = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(workspace)
    return workspace


def _managed_executable(project: Path | str) -> str | None:
    workspace = _workspace_module()
    try:
        home = workspace.home_for(project)
        name = "git-wt.exe" if os.name == "nt" else "wt"
        candidate = home / ".daodan" / "tools" / "worktrunk" / upstream_pin()["version"] / name
        workspace.no_links(candidate, home)
        if candidate.exists() and not candidate.is_file():
            raise WorktrunkError("invalid_managed_runtime", "The managed Worktrunk path is not a file")
        if not candidate.is_file():
            return None
        sentinel = home / ".daodan" / ".daodan-root"
        workspace.no_links(sentinel, home)
        if not sentinel.is_file():
            raise WorktrunkError("unowned_runtime", "Managed Worktrunk requires the main .daodan ownership sentinel")
        # A cloned repository must never supply an implicitly executable tool.
        # Unlike --no-index, this query rejects paths already tracked by Git.
        ignored = workspace.git(home, "check-ignore", "--quiet", "--", candidate.relative_to(home).as_posix(), allowed=(0, 1))
        if ignored.returncode != 0:
            raise WorktrunkError("untrusted_runtime", "Managed Worktrunk must be ignored by Git and not tracked")
        return str(candidate)
    except workspace.WorkspaceError as exc:
        raise WorktrunkError(exc.code, str(exc)) from exc
    except OSError as exc:
        raise WorktrunkError("managed_runtime_unavailable", "Cannot inspect the project's managed Worktrunk path") from exc


def _path_executable(project: Path | str | None) -> str | None:
    """Inspect absolute PATH entries without Windows' implicit cwd/PATHEXT search."""
    workspace = _workspace_module()
    current = Path.cwd().resolve()
    roots = set()
    try:
        if project is not None:
            roots.update(Path(row["path"]) for row in workspace.inventory(project))
        if project is None or Path(project).resolve() != current:
            inside = workspace.git(current, "rev-parse", "--is-inside-work-tree", allowed=(0, 128))
            if inside.returncode == 0:
                roots.update(Path(row["path"]) for row in workspace.inventory(current))
    except workspace.WorkspaceError as exc:
        raise WorktrunkError(exc.code, str(exc)) from exc

    # Released Windows Worktrunk is git-wt.exe. Never select Windows Terminal's
    # wt.exe or a batch/script chosen through a caller-controlled PATHEXT.
    names = ("git-wt.exe",) if os.name == "nt" else ("git-wt", "wt")
    directories = [Path(value) for value in os.environ.get("PATH", "").split(os.pathsep)
                   if value and Path(value).is_absolute()]
    for name in names:
        for directory in directories:
            candidate = directory / name
            try:
                resolved = candidate.resolve(strict=True)
                # Inspect the original parent too: a repository file may link
                # out to an otherwise external executable.
                parent = directory.resolve()
                if parent == current or resolved.parent == current:
                    continue
                locations = (candidate, parent, resolved)
                if any(location.is_relative_to(root) for root in roots for location in locations):
                    continue
                if resolved.is_file() and os.access(resolved, os.X_OK):
                    return str(resolved)
            except (OSError, RuntimeError):
                continue
    return None


def probe(executable: str | None = None, project: Path | str | None = None) -> dict:
    """Verify the executable identity and exact supported release before every operation."""
    if executable:
        path = Path(executable).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise WorktrunkError("invalid_executable", "Supply an absolute path to the Worktrunk executable")
        selected = str(path.resolve())
    else:
        selected = _managed_executable(project) if project is not None else None
        if not selected:
            selected = _path_executable(project)
        if not selected:
            raise WorktrunkError("missing_runtime", "Install the pinned Worktrunk release or supply its absolute executable path")
        selected = str(Path(selected).resolve())
    raw = _execute([selected, "--version"], Path(selected).parent, 10).stdout.strip()
    match = VERSION.fullmatch(raw)
    if not match:
        raise WorktrunkError("wrong_executable", "Executable did not identify itself as Worktrunk")
    version = match.group(1)
    expected = upstream_pin()["version"]
    if version != expected:
        raise WorktrunkError("unsupported_version", f"Worktrunk {version} is installed; this adapter requires {expected}")
    return {"executable": selected, "version": version, "supported": True}


def _validate_result(command: str, result: object) -> dict:
    if not isinstance(result, dict):
        raise WorktrunkError("invalid_json", "Worktrunk must return a JSON object")
    if command == "list":
        if result.get("schema") != 2 or not isinstance(result.get("items"), list):
            raise WorktrunkError("unsupported_schema", "Expected Worktrunk list schema 2")
        if not isinstance(result.get("repo"), dict) or not isinstance(result.get("collected"), dict):
            raise WorktrunkError("invalid_json", "Worktrunk list metadata is missing")
        for item in result["items"]:
            if not isinstance(item, dict):
                raise WorktrunkError("invalid_json", "Invalid Worktrunk inventory item")
            tree = item.get("worktree")
            if tree is not None and (not isinstance(tree, dict) or not isinstance(tree.get("path"), str)):
                raise WorktrunkError("invalid_json", "Invalid Worktrunk inventory path")
    elif command == "switch":
        if result.get("action") not in {"created", "existing"} or not isinstance(result.get("path"), str):
            raise WorktrunkError("invalid_json", "Invalid Worktrunk switch result; reconcile the worktree before retrying")
    return result


def _check_arguments(args: list[str]) -> str:
    if not args or args[0] not in {"list", "switch"} or any(not isinstance(arg, str) or "\0" in arg for arg in args):
        raise WorktrunkError("unsupported_command", "Only local list and controlled switch operations are supported")
    command = args[0]
    if command == "list":
        if any(arg != "--format=json" for arg in args[1:]):
            raise WorktrunkError("unsafe_options", "Only local JSON inventory is supported")
        return command
    flags = {"--create", "--no-hooks", "--no-cd", "--format=json"}
    values = {}
    branches = []
    iterator = iter(args[1:])
    for arg in iterator:
        if arg in {"--base", "--path"}:
            value = next(iterator, None)
            if not value or arg in values:
                raise WorktrunkError("unsafe_options", "Missing or repeated Worktrunk argument")
            values[arg] = value
        elif arg in flags:
            continue
        elif arg.startswith("-"):
            raise WorktrunkError("unsafe_options", "Unsupported Worktrunk option")
        else:
            branches.append(arg)
    if len(branches) != 1 or not {"--no-hooks", "--no-cd"}.issubset(args) or not Path(values.get("--path", "")).is_absolute():
        raise WorktrunkError("unsafe_options", "Switch requires one branch, an absolute path, --no-hooks and --no-cd")
    return command


def run_worktrunk(project: Path | str, args: list[str], executable: str | None = None, timeout: float = 60) -> dict:
    """Run only the catalog's local list/create surface. Merge is domain-owned."""
    command = _check_arguments(args)
    project = Path(project).resolve()
    if not project.is_dir():
        raise WorktrunkError("invalid_project", "Project directory does not exist")
    runtime = probe(executable, project=project)
    # The shipped config never changes user preferences or target files.
    # Project hooks are disabled on creation.
    if not CONFIG_PATH.is_file():
        raise WorktrunkError("missing_config", "The bundled Worktrunk configuration is missing")
    argv = [runtime["executable"], "--config", str(CONFIG_PATH), *args]
    if "--format=json" not in args:
        argv.append("--format=json")
    completed = _execute(argv, project, timeout)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WorktrunkError("invalid_json", "Worktrunk returned malformed JSON; reconcile Git state before retrying") from exc
    return _validate_result(command, result)


def upstream_check(timeout: float = 15) -> dict:
    """Inspect stable upstream metadata without downloading code or changing the pin."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise WorktrunkError("invalid_timeout", "Timeout must be positive and finite")
    request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "daodan-worktree-manager"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise WorktrunkError("invalid_release", "Upstream response exceeds the metadata limit")
        release = json.loads(raw)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise WorktrunkError("upstream_unavailable", "Upstream release metadata is unavailable; the supported pin is unchanged") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise WorktrunkError("invalid_release", "Upstream returned malformed release metadata") from exc
    if not isinstance(release, dict) or release.get("draft") is not False or release.get("prerelease") is not False:
        raise WorktrunkError("invalid_release", "Expected a published stable upstream release")
    tag = release.get("tag_name", "")
    match = TAG.fullmatch(tag) if isinstance(tag, str) else None
    expected_url = f"https://github.com/max-sixty/worktrunk/releases/tag/{tag}"
    if not match or release.get("html_url") != expected_url:
        raise WorktrunkError("invalid_release", "Unexpected upstream release identity")
    pin = upstream_pin()
    latest = tuple(map(int, match.groups()))
    supported = tuple(map(int, pin["version"].split(".")))
    return {"schema": "daodan/worktrunk-update/v1", "supported_version": pin["version"],
            "latest_version": tag[1:], "update_available": latest > supported,
            "release_url": expected_url, "published_at": release.get("published_at"),
            "pin_changed": False, "action": "verify-adapter-before-upgrade" if latest != supported else "current"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["probe", "upstream-check"])
    parser.add_argument("--executable")
    parser.add_argument("--project", default=str(Path.cwd()))
    parser.add_argument("--timeout", type=float, default=15)
    options = parser.parse_args(argv)
    try:
        result = probe(options.executable, project=options.project) if options.operation == "probe" else upstream_check(options.timeout)
    except WorktrunkError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
