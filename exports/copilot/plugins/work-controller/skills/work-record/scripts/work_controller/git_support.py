"""Path-scoped Git operations with injectable process execution."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path

from .errors import DefinitionError, ExecutionError, OutcomeUnknownError
from .util import confined_path

Runner = Callable[..., subprocess.CompletedProcess[str]]
_SHA = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})")


class GitSupport:
    """Run the small, non-destructive Git surface used by the engine."""

    def __init__(self, workspace: Path, runner: Runner = subprocess.run) -> None:
        self.workspace = Path(workspace).resolve()
        self._runner = runner

    @staticmethod
    def _detail(result: subprocess.CompletedProcess[str]) -> str:
        detail = " ".join((result.stderr or result.stdout or "no diagnostic").split())
        return detail if len(detail) <= 240 else detail[:237] + "..."

    def _git(self, *args: str, timeout: float = 60) -> subprocess.CompletedProcess[str]:
        try:
            result = self._runner(
                ["git", *args],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExecutionError(f"git {args[0]} timed out") from exc
        except OSError as exc:
            raise ExecutionError(f"git {args[0]} could not be started") from exc
        except UnicodeError as exc:
            raise ExecutionError(f"git {args[0]} returned non-UTF-8 output") from exc
        if result.returncode != 0:
            raise ExecutionError(
                f"git {args[0]} failed ({result.returncode}): {self._detail(result)}"
            )
        return result

    def ensure_clean(self) -> None:
        inside = self._git("rev-parse", "--is-inside-work-tree").stdout.strip()
        if inside != "true":
            raise ExecutionError("workspace is not inside a Git work tree")
        bare = self._git("rev-parse", "--is-bare-repository").stdout.strip()
        if bare != "false":
            raise ExecutionError("workspace must be a non-bare Git work tree")
        top = self._git("rev-parse", "--show-toplevel").stdout.strip()
        if not top or Path(top).resolve() != self.workspace:
            raise ExecutionError("workspace must be the Git work-tree root for scoped commits")
        status = self._git("status", "--porcelain", "--untracked-files=all").stdout
        if status.strip():
            raise ExecutionError("workspace has uncommitted or untracked changes")

    def _normalized_write_paths(self, paths: Iterable[str]) -> tuple[str, ...]:
        if isinstance(paths, (str, bytes)):
            raise DefinitionError("commit paths must be a nonempty iterable of paths")
        try:
            values = tuple(paths)
        except TypeError as exc:
            raise DefinitionError("commit paths must be a nonempty iterable of paths") from exc
        if not values:
            raise DefinitionError("commit paths must be nonempty")
        normalized = []
        for value in values:
            confined = confined_path(self.workspace, value, field="commit path")
            normalized.append(confined.relative_to(self.workspace).as_posix())
        return tuple(normalized)

    def commit_paths(self, paths: Iterable[str], message: str) -> str:
        if not isinstance(message, str) or not message.strip():
            raise DefinitionError("commit message must be nonempty")
        write_paths = self._normalized_write_paths(paths)
        write_set = set(write_paths)
        self._git("add", "--", *write_paths)
        staged_output = self._git("diff", "--cached", "--name-only").stdout
        staged = {Path(line).as_posix() for line in staged_output.splitlines() if line}
        if not staged:
            raise ExecutionError("no staged changes in the requested paths")
        unexpected = sorted(staged - write_set)
        if unexpected:
            raise ExecutionError(
                "staged paths outside the write set: " + ", ".join(unexpected)
            )
        try:
            self._git("commit", "-m", message, "--", *write_paths)
        except ExecutionError as exc:
            raise OutcomeUnknownError(
                "git commit outcome is uncertain; inspect HEAD before retrying"
            ) from exc
        try:
            sha = self._git("rev-parse", "HEAD").stdout.strip()
        except ExecutionError as exc:
            raise OutcomeUnknownError(
                "git commit succeeded but HEAD could not be read; inspect HEAD before retrying"
            ) from exc
        if not _SHA.fullmatch(sha):
            raise OutcomeUnknownError(
                "git commit succeeded but HEAD returned an invalid SHA; inspect HEAD before retrying"
            )
        return sha
