"""The analysis store and its runs on disk: store and run validation, link refusal,
immutable flags, artifact bytes, atomic JSON writes and the publication registry
with its lock."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class RunControlError(ValueError):
    """A malformed or unsafe run binding; no state may be written."""


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)


def _reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        if _is_link(part):
            raise RunControlError(f"linked path is not a run-owned regular path: {part}")


def _reject_links_below(folder: Path) -> None:
    """`folder` and all it holds, without a link. A store lies in the project's folder, where a repository can
    bring one: a link in it names any file or folder of the machine to whoever reads, replaces or removes there."""
    _reject_links(folder)
    for base, folders, files in os.walk(folder):
        for name in (*folders, *files):
            if _is_link(Path(base, name)):
                raise RunControlError(f"linked path is not a run-owned regular path: {Path(base, name)}")


CANONICAL_STORE = ".daodan/map"
STORE_MARKER = ".daodan-map-store.json"
STORE_SCHEMA = "daodan/codebase-map-store/v1"
_DEVICE_NAMES = frozenset({"con", "prn", "aux", "nul", "conin$", "conout$",
                           *(f"{port}{i}" for port in ("com", "lpt")
                             for i in (*range(1, 10), "\u00b9", "\u00b2", "\u00b3"))})
_STORE_FORBIDDEN = re.compile(r'[\x00-\x1f<>:"|?*\\]')


def validate_store(value) -> str:
    """Return a project-relative custom store path, or raise RunControlError.

    A custom store starts with a dot directory, so every perimeter already
    leaves it out of the analyzed sources, and never reuses the canonical
    store path, which identifies its project by position alone.
    """
    if (not isinstance(value, str) or not value or len(value) > 255 or value.startswith("/")
            or _STORE_FORBIDDEN.search(value)):
        raise RunControlError("analysis store must be an exact project-relative POSIX path")
    parts = value.split("/")
    if any(part in ("", ".", "..") or part != part.strip() or part.endswith(".") for part in parts):
        raise RunControlError("analysis store must be an exact project-relative POSIX path")
    if not parts[0].startswith("."):
        raise RunControlError("analysis store must begin with a dot directory outside the analyzed sources")
    if value.casefold() == CANONICAL_STORE or any(
            part.casefold() == ".git" or part.casefold().lstrip(".").split(".")[0] in _DEVICE_NAMES
            for part in parts):
        raise RunControlError("analysis store must not reuse the canonical, git or device name")
    return value


def store_project(root: Path) -> Path:
    """Project bound by an analysis store.

    The canonical store is the project's `.daodan/map`. A custom store
    records its own project-relative path in a marker; the project is the
    ancestor that path names, and the marker must resolve back to the store.
    """
    canonical = CANONICAL_STORE.split("/")
    if list(root.parts[-len(canonical):]) == canonical:
        return root.parents[len(canonical) - 1]
    marker = root / STORE_MARKER
    _reject_links(marker)
    if not marker.is_file():
        raise RunControlError(f"run must be inside a project's {CANONICAL_STORE}/runs/<run-id> "
                              f"or a custom store carrying {STORE_MARKER}")
    try:
        value = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        value = None
    if not isinstance(value, dict) or value.get("schema") != STORE_SCHEMA:
        raise RunControlError(f"custom store marker {STORE_MARKER} is unreadable or has another schema")
    store = validate_store(value.get("store"))
    project = root
    for _ in store.split("/"):
        project = project.parent
    if (project / store).resolve() != root.resolve():
        raise RunControlError("custom store marker does not name this store")
    return project


def _run_context(run_dir: Path) -> tuple[Path, Path, dict]:
    _reject_links(run_dir)
    run_dir = run_dir.resolve()
    if run_dir.parent.name != "runs":
        raise RunControlError(f"run must be inside a project's {CANONICAL_STORE}/runs/<run-id> "
                              f"or a custom store carrying {STORE_MARKER}")
    root = run_dir.parent.parent
    store_project(root)
    _reject_links(run_dir / "state.json")
    state = _read_json(run_dir / "state.json")
    if not isinstance(state, dict) or state.get("run_id") != run_dir.name:
        raise RunControlError("state.run_id must equal the exact run directory name")
    if state.get("mode") not in ("classic", "team"):
        raise RunControlError("state.mode must be classic or team")
    if not isinstance(state.get("flags"), dict) or not isinstance(state.get("target"), str):
        raise RunControlError("state requires flags and target")
    return run_dir, root, state


def _effective_flags(flags: dict) -> dict:
    effective = {"critical": False, "comments": False, "docs_only": False,
                 "phase": None, "depth": "full", "skip_synthesis": False,
                 "skip_interconnect": False}
    effective.update(flags)
    if effective["depth"] not in ("full", "lite"):
        raise RunControlError("depth must be full or lite")
    for key in ("critical", "comments", "docs_only", "skip_synthesis", "skip_interconnect"):
        if not isinstance(effective[key], bool):
            raise RunControlError(f"{key} must be a boolean")
    phase = effective["phase"]
    if phase is not None and (type(phase) is not int or phase not in range(1, 7)):
        raise RunControlError("--phase accepts 1 through 6; phase 7 summarizes a complete run")
    if effective["docs_only"] and phase is not None:
        raise RunControlError("--docs-only and --phase cannot be combined")
    if "stop_after" in effective or "resume_from" in effective:
        raise RunControlError("stop and resume are invocation controls, not immutable flags")
    return effective


def _artifact_bytes(run_dir: Path, name: str) -> bytes | None:
    paths = [run_dir / name]
    if name == "knowledge/":
        paths = [run_dir / "knowledge/navigation.md", run_dir / "knowledge/documentation-leads.md"]
    chunks = []
    for path in paths:
        _reject_links(path)
        if not path.is_file():
            return None
        data = path.read_bytes()
        if not data.strip():
            return b""
        chunks.append(path.name.encode() + b"\0" + data)
    return b"\0".join(chunks) if name == "knowledge/" else paths[0].read_bytes()


def _artifact_hash(run_dir: Path, name: str) -> str:
    data = _artifact_bytes(run_dir, name)
    if not data:
        raise RunControlError(f"missing or empty artifact: {name}")
    return hashlib.sha256(data).hexdigest()


def _write_json_atomic(path: Path, value: dict) -> None:
    _reject_links(path)
    fd, temporary = tempfile.mkstemp(prefix=".map-write-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


class _RegistryLock:
    """
    An OS byte-range lock on a persistent lock file. The OS releases it when
    its holder exits, so a crashed coordinator leaves no stale lock behind.
    """

    def __init__(self, path: Path, descriptor: int) -> None:
        self.path = path
        self.descriptor = descriptor

    def unlink(self) -> None:
        # Kept under its historical name: release, never delete, so a second
        # holder cannot lock a different inode of the same path.
        try:
            if os.name == "nt":
                import msvcrt
                os.lseek(self.descriptor, 0, os.SEEK_SET)
                msvcrt.locking(self.descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)


def _try_lock(descriptor: int) -> bool:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _acquire_registry_lock(root: Path) -> _RegistryLock:
    lock = root / ".registry.lock"
    _reject_links(lock)
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + 10
    while not _try_lock(descriptor):
        if time.monotonic() >= deadline:
            os.close(descriptor)
            raise RunControlError("another coordinator holds the registry lock; retry after it finishes")
        time.sleep(0.05)
    return _RegistryLock(lock, descriptor)


def _run_name(value) -> bool:
    """Whether `value` is one folder name under `runs/`. A registry can come with the project: a path in it would
    name any folder of the machine as a run of this store."""
    return isinstance(value, str) and value not in ("", ".", "..") and Path(value).name == value


def _read_registry(root: Path) -> dict:
    path = root / "runs.json"
    _reject_links(path)
    if not path.exists():
        return {"schema": 2, "active": [], "latest_completed": None}
    registry = _read_json(path)
    if (not isinstance(registry, dict) or not isinstance(registry.get("active"), list)
            or any(not isinstance(item, dict) or not isinstance(item.get("run_id"), str)
                   or not item["run_id"] for item in registry["active"])
            or not (registry.get("latest_completed") is None or _run_name(registry["latest_completed"]))):
        raise RunControlError("malformed runs registry")
    return registry


def update_registration(run_dir: Path, *, active: bool) -> dict:
    run_dir, root, state = _run_context(run_dir)
    if active and (not isinstance(state.get("started_at"), str) or not state["started_at"]):
        raise RunControlError("registration requires state.started_at")
    lock = _acquire_registry_lock(root)
    try:
        registry = _read_registry(root)
        entries = [item for item in registry["active"] if item["run_id"] != state["run_id"]]
        if active:
            entries.append({key: state.get(key) for key in
                            ("run_id", "target", "mode", "started_at", "parent_run")})
        registry["active"] = entries
        _write_json_atomic(root / "runs.json", registry)
        return {"run_id": state["run_id"], "active": active,
                "registry": (root / "runs.json").as_posix()}
    finally:
        lock.unlink()


def _hold(path: Path, wait: bool) -> _RegistryLock | None:
    _reject_links(path)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    while not _try_lock(descriptor):
        if not wait:
            os.close(descriptor)
            return None
        time.sleep(0.05)
    return _RegistryLock(path, descriptor)
