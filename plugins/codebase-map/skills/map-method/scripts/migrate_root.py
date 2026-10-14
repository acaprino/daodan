#!/usr/bin/env python3
"""Move a quiescent project's analysis store and resolve its legacy root prefix.

Only the root directory is renamed. Registry IDs, state, reports, manifests and
source blobs remain byte-for-byte intact. A bound relocation record survives an
interrupted move; a legacy redirect is data for this resolver, never a symlink.
Run writers must be stopped before migration and must use the canonical root
afterward. Older tools that ignore the redirect need the compatibility workflow.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time


LEGACY_ROOT = ".codebase-xray"
CANONICAL_ROOT = ".codebase-map"
ORIGIN_FILE = ".codebase-map-migration.json"
REDIRECT_FILE = ".codebase-map-redirect.json"
SCHEMA = "daodan/codebase-map-relocation/v1"
TERMINAL_STATUSES = {"complete", "completed", "failed", "cancelled", "canceled", "aborted", "archived"}
LOCK_TIMEOUT_SECONDS = 5.0


class MigrationError(ValueError):
    """A migration or bound-path resolution could not be performed safely."""


@contextmanager
def _migration_lock(project: Path):
    """Serialize local helpers without creating or relocating a lock file.

    Windows mutexes and POSIX directory locks are released by the OS when a
    process exits, including an abrupt exit. No stale lock record needs deleting.
    """
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.CreateMutexW.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel.ReleaseMutex.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        key = hashlib.sha256(os.path.normcase(str(project)).encode("utf-8")).hexdigest()
        handle = kernel.CreateMutexW(None, False, f"Global\\DaodanCodebaseMapMigration-{key}")
        if not handle:
            raise MigrationError(f"cannot acquire project migration lock: {ctypes.WinError(ctypes.get_last_error())}")
        acquired = False
        try:
            outcome = kernel.WaitForSingleObject(handle, max(0, int(LOCK_TIMEOUT_SECONDS * 1000)))
            if outcome == 0x102:
                raise MigrationError("project migration lock is held by another helper; retry after that invocation finishes")
            if outcome not in {0, 0x80}:  # WAIT_OBJECT_0 or WAIT_ABANDONED
                raise MigrationError(f"project migration lock failed: {ctypes.WinError(ctypes.get_last_error())}")
            acquired = True
            yield
        finally:
            if acquired:
                kernel.ReleaseMutex(handle)
            kernel.CloseHandle(handle)
    else:
        import fcntl

        descriptor = os.open(project, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        acquired = False
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        try:
            while not acquired:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError as error:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise MigrationError("project migration lock is held by another helper; retry after that invocation finishes") from error
                    time.sleep(min(0.02, remaining))
            yield
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def _lstat(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _reject_link(path: Path):
    info = _lstat(path)
    if info is not None and (
        stat.S_ISLNK(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
    ):
        raise MigrationError(f"symbolic link or reparse point is not permitted: {path}")
    return info


def _reject_link_chain(path: Path) -> None:
    for component in reversed((path, *path.parents)):
        _reject_link(component)


def _project(value: str | Path) -> Path:
    candidate = Path(value).absolute()
    _reject_link_chain(candidate)
    if not candidate.is_dir():
        raise MigrationError(f"project must be an existing directory: {candidate}")
    return candidate.resolve(strict=True)


def _root(path: Path) -> bool:
    info = _reject_link(path)
    if info is None:
        return False
    if not stat.S_ISDIR(info.st_mode):
        raise MigrationError(f"analysis root must be a directory: {path}")
    return True


def _json(path: Path) -> dict:
    _reject_link(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as error:
        raise MigrationError(f"cannot validate {path}: {error}") from error
    if not isinstance(value, dict):
        raise MigrationError(f"expected a JSON object in {path}")
    return value


def _record(project: Path) -> dict:
    return {
        "schema": SCHEMA,
        "project": str(project),
        "legacy_root": LEGACY_ROOT,
        "canonical_root": CANONICAL_ROOT,
    }


def _read_record(path: Path, expected: dict) -> bool:
    if _lstat(path) is None:
        return False
    if _json(path) != expected:
        raise MigrationError(f"invalid relocation binding in {path}; no path from this record is followed")
    return True


def _write_json_atomic(path: Path, record: dict) -> None:
    if _read_record(path, record):
        return
    descriptor, temporary_name = tempfile.mkstemp(prefix=f"{path.name}.tmp-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Only this reserved metadata path is replaced, after validating absence.
        # Analysis evidence is moved as one directory and is never overwritten.
        if _lstat(path) is not None:
            if _read_record(path, record):
                return
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _redirect_metadata_only(contents: list[Path], record: dict, *, origin: bool) -> bool:
    """Recognize complete bound temp records; preserve all such files in place."""
    prefix = REDIRECT_FILE + ".tmp-"
    for path in contents:
        if path.name == REDIRECT_FILE:
            _read_record(path, record)
        elif origin and path.name.startswith(prefix) and len(path.name) > len(prefix):
            _read_record(path, record)
        else:
            return False
    return True


def _write_redirect(legacy: Path, record: dict) -> None:
    if not _root(legacy):
        legacy.mkdir()
    contents = list(legacy.iterdir())
    origin = _read_record(legacy.parent / CANONICAL_ROOT / ORIGIN_FILE, record)
    if not _redirect_metadata_only(contents, record, origin=origin):
        raise MigrationError(f"legacy root acquired content during migration: {legacy}")
    _write_json_atomic(legacy / REDIRECT_FILE, record)


def _reject_tree_links(root: Path) -> None:
    def unreadable(error: OSError) -> None:
        raise error

    for current, directories, files in os.walk(root, followlinks=False, onerror=unreadable):
        for name in (*directories, *files):
            _reject_link(Path(current) / name)


def _ensure_idle(root: Path) -> None:
    registry = root / "runs.json"
    if _lstat(registry) is not None:
        data = _json(registry)
        if not isinstance(data.get("active"), list):
            raise MigrationError(f"cannot establish active run state from {registry}")
        if data["active"]:
            raise MigrationError(f"active runs block migration: {registry}; finish or explicitly conclude them first")
    states = [root / "state.json"]
    runs = root / "runs"
    if _lstat(runs) is not None:
        if not runs.is_dir():
            raise MigrationError(f"runs must be a directory: {runs}")
        states.extend(path / "state.json" for path in runs.iterdir() if path.is_dir())
    for path in states:
        if _lstat(path) is None:
            continue
        state = _json(path)
        status = state.get("status")
        if isinstance(status, str) and status.lower() in TERMINAL_STATUSES:
            continue
        # Older flat stores did not record status. Their completed final phase
        # establishes completion without rewriting or inventing a run identity.
        phases = state.get("completed_phases", [])
        phase = state.get("current_phase")
        if status is None and (
            isinstance(phases, list) and 7 in phases
            or isinstance(phase, int) and not isinstance(phase, bool) and phase > 7
        ):
            continue
        raise MigrationError(f"active or unfinished state blocks migration: {path}; status={status!r}")


def _rename_root(source: Path, destination: Path) -> None:
    deadline = time.monotonic() + 0.5
    previous_error = None
    while True:
        if _lstat(destination) is not None:
            raise MigrationError(f"destination appeared during migration: {destination}")
        if previous_error is not None:
            if not _root(source):
                raise MigrationError(f"source disappeared during migration: {source}")
            _reject_tree_links(source)
            _ensure_idle(source)
            if time.monotonic() >= deadline:
                raise previous_error
            if _lstat(destination) is not None:
                raise MigrationError(f"destination appeared during migration: {destination}")
        try:
            os.rename(source, destination)
            return
        except PermissionError as error:
            # Windows can briefly deny a directory rename after validation.
            # Keep permanent and unrelated errors on the original rollback path.
            if getattr(error, "winerror", None) not in {5, 32, 33}:
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            previous_error = error
            time.sleep(min(0.025, remaining))


def _result(project: Path, status: str, **details) -> dict:
    return {
        "status": status,
        "project": str(project),
        "canonical_root": str(project / CANONICAL_ROOT),
        "legacy_root": str(project / LEGACY_ROOT),
        **details,
    }


def _inspect(project: Path) -> dict:
    legacy, canonical = project / LEGACY_ROOT, project / CANONICAL_ROOT
    has_old, has_new = _root(legacy), _root(canonical)
    record = _record(project)
    old_origin = has_old and _read_record(legacy / ORIGIN_FILE, record)
    new_origin = has_new and _read_record(canonical / ORIGIN_FILE, record)
    redirect = has_old and _read_record(legacy / REDIRECT_FILE, record)
    old_contents = list(legacy.iterdir()) if has_old else []
    new_contents = list(canonical.iterdir()) if has_new else []
    if redirect:
        if not _redirect_metadata_only(old_contents, record, origin=new_origin):
            raise MigrationError(f"legacy redirect has additional evidence: {legacy}; preserve both roots and reconcile explicitly")
        if not has_new or not new_origin:
            raise MigrationError(f"legacy redirect has no bound canonical store: {canonical}")
    elif old_contents and new_contents:
        if not (new_origin and _redirect_metadata_only(old_contents, record, origin=True)):
            raise MigrationError("both .codebase-xray and .codebase-map contain content; preserve both roots and reconcile explicitly")
    return {
        "legacy": legacy, "canonical": canonical, "record": record,
        "has_old": has_old, "has_new": has_new, "redirect": redirect,
        "old_origin": old_origin, "new_origin": new_origin,
        "old_contents": old_contents, "new_contents": new_contents,
    }


def migrate(project: str | Path, *, check: bool = False) -> dict:
    """Migrate the bound output root, or inspect it without writing with check."""
    bound = _project(project)
    with _migration_lock(bound):
        return _migrate_locked(bound, check=check)


def _migrate_locked(bound: Path, *, check: bool) -> dict:
    layout = _inspect(bound)
    legacy, canonical, record = layout["legacy"], layout["canonical"], layout["record"]
    if layout["redirect"]:
        return _result(bound, "current")
    if layout["new_origin"]:
        if check:
            return _result(bound, "recovery_required", action="create_legacy_redirect")
        try:
            _write_redirect(legacy, record)
        except OSError as error:
            raise MigrationError(f"cannot complete relocation redirect; evidence remains in {canonical}: {error}") from error
        return _result(bound, "recovered")
    if layout["has_new"] and (layout["new_contents"] or not layout["has_old"]):
        return _result(bound, "current")
    if not layout["has_old"]:
        return _result(bound, "absent")

    _reject_tree_links(legacy)
    _ensure_idle(legacy)
    if check:
        return _result(bound, "migration_required", action="rename_legacy_root")

    origin_created = not layout["old_origin"]
    empty_destination_removed = False
    moved = False
    try:
        # The record is written before the atomic move so a process interruption
        # after rename can be recognized and completed on the next invocation.
        _write_json_atomic(legacy / ORIGIN_FILE, record)
        if layout["has_new"]:
            canonical.rmdir()  # Only an empty destination reaches this branch.
            empty_destination_removed = True
        _rename_root(legacy, canonical)
        moved = True
        _write_redirect(legacy, record)
    except (OSError, MigrationError) as error:
        try:
            if moved:
                if _root(legacy):
                    redirect_path = legacy / REDIRECT_FILE
                    if _read_record(redirect_path, record):
                        redirect_path.unlink()
                    legacy.rmdir()  # Refuse rollback over any unexpected data.
                _rename_root(canonical, legacy)
            if origin_created and _read_record(legacy / ORIGIN_FILE, record):
                (legacy / ORIGIN_FILE).unlink()
            if empty_destination_removed and not _root(canonical):
                canonical.mkdir()
        except (OSError, MigrationError) as rollback_error:
            raise MigrationError(
                f"migration failed: {error}; rollback could not finish: {rollback_error}; "
                f"preserved evidence remains at {canonical if moved else legacy}; "
                "inspect both roots before retrying"
            ) from error
        raise MigrationError(f"migration failed and original store was restored: {error}") from error
    return _result(bound, "migrated")


def resolve_path(project: str | Path, path: str | Path) -> dict:
    """Resolve only a bound analysis-root prefix; do not change stored evidence."""
    bound = _project(project)
    with _migration_lock(bound):
        return _resolve_path_locked(bound, path)


def _resolve_path_locked(bound: Path, path: str | Path) -> dict:
    layout = _inspect(bound)
    requested = Path(path)
    # Reject traversal before normalization, including Windows-style separators
    # when reading metadata on a POSIX host.
    if ".." in str(path).replace("\\", "/").split("/"):
        raise MigrationError(f"parent traversal is not permitted in a bound path: {path}")
    if requested.is_absolute():
        try:
            relative = requested.relative_to(bound)
        except ValueError as error:
            raise MigrationError(f"foreign path is outside the bound project: {path}") from error
    else:
        relative = requested
    if not relative.parts or relative.parts[0] not in {LEGACY_ROOT, CANONICAL_ROOT}:
        raise MigrationError(f"path must start with a project-bound analysis root: {path}")
    _reject_link_chain(bound / relative)
    if layout["has_new"] and (layout["new_contents"] or not layout["has_old"] or layout["redirect"]):
        root = layout["canonical"]
    elif layout["has_old"] and not layout["redirect"]:
        root = layout["legacy"]
    else:
        root = layout["canonical"]
    resolved = root.joinpath(*relative.parts[1:])
    _reject_link_chain(resolved)
    try:
        resolved.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise MigrationError(f"resolved path escaped its analysis root: {path}") from error
    return _result(
        bound, "resolved", path=str(resolved), requested_path=str(path),
        translated=relative.parts[0] != root.name, exists=resolved.exists(),
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    resolving = bool(args and args[0] == "resolve")
    if resolving:
        args.pop(0)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="explicit existing project directory")
    if resolving:
        parser.add_argument("path", help="project-bound .codebase-xray or .codebase-map path")
    else:
        parser.add_argument("--check", action="store_true", help="inspect without changing the project")
    namespace = parser.parse_args(args)
    try:
        result = resolve_path(namespace.project, namespace.path) if resolving else migrate(namespace.project, check=namespace.check)
    except (MigrationError, OSError) as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
