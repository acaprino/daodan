"""Immutable content-addressed artifact bytes."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
from pathlib import Path

from .errors import DefinitionError, ExecutionError
from .util import digest_bytes

_DIGEST = re.compile(r"[0-9a-fA-F]{64}")
_CHUNK_SIZE = 1024 * 1024
_MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


class ArtifactStore:
    """Store artifact bodies without storing their admission metadata."""

    def __init__(self, root: Path) -> None:
        root = Path(root)
        if root.is_symlink():
            raise ExecutionError("artifact root must not be a symlink")
        self.root = root.resolve()
        self._objects = self.root / "objects"
        self._ensure_directory(self.root)
        self._ensure_directory(self._objects)

    @staticmethod
    def _require_directory(path: Path) -> None:
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise ExecutionError(f"cannot inspect artifact directory: {path.name}") from exc
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ExecutionError(f"artifact directory must not be a symlink: {path.name}")

    @classmethod
    def _ensure_directory(cls, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExecutionError(f"cannot prepare artifact directory: {path.name}") from exc
        cls._require_directory(path)

    @staticmethod
    def _validated_digest(digest: str) -> str:
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise DefinitionError("artifact digest must be 64 hexadecimal characters")
        return digest.lower()

    def path_for(self, digest: str) -> Path:
        digest = self._validated_digest(digest)
        return self._objects / digest[:2] / f"{digest}.blob"

    def _matches_existing(self, path: Path, digest: str, size: int) -> bool:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise ExecutionError("cannot inspect existing artifact") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_size != size:
            raise ExecutionError("existing artifact does not match its content digest")
        hasher = hashlib.sha256()
        try:
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(_CHUNK_SIZE), b""):
                    hasher.update(chunk)
        except OSError as exc:
            raise ExecutionError("cannot verify existing artifact") from exc
        if hasher.hexdigest() != digest:
            raise ExecutionError("existing artifact does not match its content digest")
        return True

    def _install(self, temporary: Path, digest: str, size: int) -> dict[str, object]:
        target = self.path_for(digest)
        self._ensure_directory(self.root)
        self._ensure_directory(self._objects)
        self._ensure_directory(target.parent)
        if not self._matches_existing(target, digest, size):
            try:
                os.link(temporary, target)
            except FileExistsError:
                if not self._matches_existing(target, digest, size):
                    raise ExecutionError("artifact publication changed concurrently")
            except OSError as exc:
                raise ExecutionError("cannot publish artifact atomically") from exc
        return {"digest": digest, "size": size, "path": target}

    def read(self, digest: str, max_bytes: int | None = None) -> bytes:
        if max_bytes is not None and (
            isinstance(max_bytes, bool)
            or not isinstance(max_bytes, int)
            or max_bytes < 0
        ):
            raise DefinitionError("max_bytes must be a nonnegative integer")
        path = self.path_for(digest)
        self._require_directory(self.root)
        self._require_directory(self._objects)
        self._require_directory(path.parent)
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ExecutionError("unknown artifact digest") from exc
        except OSError as exc:
            raise ExecutionError("cannot inspect artifact") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ExecutionError("artifact body must be a regular file, not a symlink")
        if max_bytes is not None and info.st_size > max_bytes:
            raise ExecutionError("artifact exceeds max_bytes")
        try:
            with path.open("rb") as stream:
                data = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
        except OSError as exc:
            raise ExecutionError("cannot read artifact") from exc
        if max_bytes is not None and len(data) > max_bytes:
            raise ExecutionError("artifact exceeds max_bytes")
        return data

    def put_file(self, source: Path) -> dict[str, object]:
        source = Path(source)
        try:
            info = source.lstat()
            mode = info.st_mode
        except OSError as exc:
            raise ExecutionError("artifact source must be a regular file") from exc
        if not stat.S_ISREG(mode):
            raise ExecutionError("artifact source must be a regular file, not a symlink")
        if info.st_size > _MAX_ARTIFACT_BYTES:
            raise ExecutionError("artifact exceeds the 64 MiB limit")
        self._ensure_directory(self.root)
        self._ensure_directory(self._objects)
        try:
            descriptor, name = tempfile.mkstemp(prefix=".artifact-", dir=self._objects)
        except OSError as exc:
            raise ExecutionError("cannot create temporary artifact") from exc
        temporary = Path(name)
        hasher = hashlib.sha256()
        size = 0
        try:
            try:
                with os.fdopen(descriptor, "wb") as target, source.open("rb") as origin:
                    for chunk in iter(lambda: origin.read(_CHUNK_SIZE), b""):
                        hasher.update(chunk)
                        size += len(chunk)
                        if size > _MAX_ARTIFACT_BYTES:
                            raise ExecutionError("artifact exceeds the 64 MiB limit")
                        target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
            except OSError as exc:
                raise ExecutionError("cannot copy artifact source") from exc
            return self._install(temporary, hasher.hexdigest(), size)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise ExecutionError("cannot remove temporary artifact") from exc

    def put_bytes(self, data: bytes) -> dict[str, object]:
        if not isinstance(data, bytes):
            raise DefinitionError("artifact data must be bytes")
        if len(data) > _MAX_ARTIFACT_BYTES:
            raise ExecutionError("artifact exceeds the 64 MiB limit")
        digest = digest_bytes(data)
        self._ensure_directory(self.root)
        self._ensure_directory(self._objects)
        try:
            descriptor, name = tempfile.mkstemp(prefix=".artifact-", dir=self._objects)
        except OSError as exc:
            raise ExecutionError("cannot create temporary artifact") from exc
        temporary = Path(name)
        try:
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            except OSError as exc:
                raise ExecutionError("cannot write temporary artifact") from exc
            return self._install(temporary, digest, len(data))
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise ExecutionError("cannot remove temporary artifact") from exc
