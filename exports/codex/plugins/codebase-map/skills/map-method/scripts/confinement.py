"""Project-bound path confinement shared by every Codebase Map helper.

A helper binds one existing project directory, refuses symbolic links and
reparse points along any path it reads or writes, and serializes operations on
that project through an OS lock that is released when its owner exits.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import time


LOCK_TIMEOUT_SECONDS = 5.0


class ConfinementError(ValueError):
    """A path or project binding could not be confined safely."""


@contextmanager
def project_lock(project: Path):
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
        handle = kernel.CreateMutexW(None, False, f"Global\\DaodanCodebaseMap-{key}")
        if not handle:
            raise ConfinementError(f"cannot acquire project lock: {ctypes.WinError(ctypes.get_last_error())}")
        acquired = False
        try:
            outcome = kernel.WaitForSingleObject(handle, max(0, int(LOCK_TIMEOUT_SECONDS * 1000)))
            if outcome == 0x102:
                raise ConfinementError("project lock is held by another helper; retry after that invocation finishes")
            if outcome not in {0, 0x80}:  # WAIT_OBJECT_0 or WAIT_ABANDONED
                raise ConfinementError(f"project lock failed: {ctypes.WinError(ctypes.get_last_error())}")
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
                        raise ConfinementError("project lock is held by another helper; retry after that invocation finishes") from error
                    time.sleep(min(0.02, remaining))
            yield
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def reject_link(path: Path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ConfinementError(f"symbolic link or reparse point is not permitted: {path}")
    return info


def reject_link_chain(path: Path) -> None:
    for component in reversed((path, *path.parents)):
        reject_link(component)


def bind_project(value: str | Path) -> Path:
    candidate = Path(value).absolute()
    reject_link_chain(candidate)
    if not candidate.is_dir():
        raise ConfinementError(f"project must be an existing directory: {candidate}")
    return candidate.resolve(strict=True)
