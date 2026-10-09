#!/usr/bin/env python3
"""
The perimeter of an X-ray: what no script descends into.

One rule, owned here, for every script that walks a tree:

- what Git ignores, when the target is inside a work tree and git answers;
- every directory whose name starts with a dot;
- dependency and build directories, by name.

All three apply below the target. The target itself is analyzed as given, so
naming a dot directory is how its content gets an X-ray of its own. A dot file
beside analyzed source is not a directory, and stays.

The rule exists because tools write beside the code they work on. A lifecycle
campaign left its run records under `.daodan/` and its review under
`.team-review/`; the next snapshot counted them as project files, and an
incremental update of an untouched project asked for a full analysis.

A script may read less than the perimeter. None reads more: a usage found in a
file the snapshot never recorded is a citation no phase file can carry.

Standard library only.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterator

__all__ = ["DEPENDENCY_DIRS", "Perimeter"]

# Dependency and build output. Git usually ignores these too. They are named
# here because a project with no repository has no ignore rule to consult.
DEPENDENCY_DIRS = frozenset({
    "__pycache__", "build", "dist", "node_modules", "target", "vendor", "venv",
})

# Dot directories a reader does not need named back: the repository's own
# store, and the X-ray's own output.
_UNREPORTED = frozenset({".git", ".codebase-xray"})

GIT_TIMEOUT_SECONDS = 30


def _key(relative: str) -> str:
    """One spelling per path: Git prints forward slashes, Windows does not."""
    return os.path.normcase(relative.replace("\\", "/").rstrip("/"))


class Perimeter:
    """
    The part of one target a script may read.

    `walk` yields it; `covers` answers for a path found some other way, by a
    glob or by a search tool. `dot_directories` and `git_ignored` say what a
    walk left out, so that a run can declare it: an exclusion nobody reported
    is how a stylesheet once went missing from every inventory.
    """

    def __init__(self, target: Path) -> None:
        target = Path(target)
        # Walked as given, so a caller can still relate a yielded path to the
        # target it passed. Compared resolved, so a path that reached us
        # through a link or another spelling is still recognized.
        self.base = target if target.is_dir() else target.parent
        self._resolved_base = self.base.resolve()
        self._ignored_files, self._ignored_dirs, self.git_ignore = self._ask_git()
        self._dot: set[Path] = set()
        self._ignored_seen: set[Path] = set()

    def _ask_git(self) -> tuple[frozenset[str], frozenset[str], str]:
        """
        The untracked paths Git ignores below the base, files and directories
        apart, and whether Git answered at all.

        Git is asked, never imitated: nested ignore files, negations and the
        user's own excludes are its to resolve. A tracked file is never in the
        answer, whatever pattern it matches, because Git does not ignore what
        it tracks.
        """
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.base), "ls-files", "-z", "--others", "--ignored",
                 "--exclude-standard", "--directory"],
                capture_output=True, timeout=GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError):
            return frozenset(), frozenset(), "unavailable"
        if proc.returncode != 0:
            return frozenset(), frozenset(), "unavailable"
        files: set[str] = set()
        dirs: set[str] = set()
        for raw in proc.stdout.split(b"\0"):
            entry = raw.decode("utf-8", errors="surrogateescape")
            # A base that is itself ignored comes back as `./`. The target is
            # analyzed as given, so that entry prunes nothing.
            if entry in ("", "./"):
                continue
            (dirs if entry.endswith("/") else files).add(_key(entry))
        return frozenset(files), frozenset(dirs), "applied"

    def _skips_directory(self, path: Path, relative: str, record: bool) -> bool:
        name = path.name
        if name.startswith("."):
            if record and name not in _UNREPORTED:
                self._dot.add(path)
            return True
        if name in DEPENDENCY_DIRS:
            return True
        if _key(relative) in self._ignored_dirs:
            if record:
                self._ignored_seen.add(path)
            return True
        return False

    def _ignores_file(self, path: Path, relative: str, record: bool) -> bool:
        if _key(relative) not in self._ignored_files:
            return False
        if record:
            self._ignored_seen.add(path)
        return True

    def walk(self) -> Iterator[tuple[Path, list[str]]]:
        """Each directory inside the perimeter with its file names, in a stable order."""
        for dirpath, dirnames, filenames in os.walk(self.base):
            here = Path(dirpath)
            prefix = here.relative_to(self.base).as_posix()
            prefix = "" if prefix == "." else prefix + "/"
            dirnames[:] = [
                name for name in sorted(dirnames)
                if not self._skips_directory(here / name, prefix + name, record=True)
            ]
            yield here, [
                name for name in sorted(filenames)
                if not self._ignores_file(here / name, prefix + name, record=True)
            ]

    def covers(self, path: Path) -> bool:
        """
        True when a file is inside the perimeter. A path outside the target is
        not this perimeter's to judge, and passes.
        """
        resolved = Path(path).resolve()
        try:
            parts = resolved.relative_to(self._resolved_base).parts
        except ValueError:
            return True
        for depth in range(1, len(parts)):
            directory = self._resolved_base.joinpath(*parts[:depth])
            if self._skips_directory(directory, "/".join(parts[:depth]), record=False):
                return False
        return not self._ignores_file(resolved, "/".join(parts), record=False)

    @property
    def dot_directories(self) -> list[Path]:
        """The dot directories the walk pruned, outermost only, in a stable order."""
        return sorted(self._dot)

    @property
    def git_ignored(self) -> int:
        """How many ignored paths the walk met: a pruned directory counts once."""
        return len(self._ignored_seen)
