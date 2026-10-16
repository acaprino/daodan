"""Read only regular unlinked payloads through pinned directory/file handles."""
from contextlib import ExitStack
import os
from pathlib import Path
import stat


def _regular(info):
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("MoE payload is not an unlinked regular file")


def _read_posix(cwd, path, limit):
    # Descriptor-relative opens retain the original parent even if names change.
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        parent = os.open(cwd, flags)
        stack.callback(os.close, parent)
        parts = path.relative_to(cwd).parts
        for part in parts[:-1]:
            parent = os.open(part, flags, dir_fd=parent)
            stack.callback(os.close, parent)
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        stack.callback(os.close, descriptor)
        before = os.fstat(descriptor)
        _regular(before)
        chunks = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        _regular(after)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("MoE payload changed while reading")
        return b"".join(chunks)


def _read_windows(cwd, path, limit):
    import ctypes
    from ctypes import wintypes

    class FileInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("created", wintypes.FILETIME), ("accessed", wintypes.FILETIME),
                    ("written", wintypes.FILETIME), ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                    ("size_low", wintypes.DWORD), ("links", wintypes.DWORD), ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    api.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(FileInfo)]
    api.GetFileInformationByHandle.restype = wintypes.BOOL
    api.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    api.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    api.GetFileType.argtypes = [wintypes.HANDLE]
    api.GetFileType.restype = wintypes.DWORD
    api.ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    api.ReadFile.restype = wintypes.BOOL

    def normalized(value):
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return os.path.normcase(os.path.normpath(value))

    with ExitStack() as stack:
        def lock(candidate, directory):
            # FILE_SHARE_READ only: keep components from being replaced or written
            # until the entire bounded read is done. OPEN_REPARSE_POINT never follows links.
            handle = api.CreateFileW(str(candidate), 0x80 if directory else 0x80000000, 1, None, 3,
                                     0x00200000 | (0x02000000 if directory else 0), None)
            if handle == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            stack.callback(api.CloseHandle, handle)
            info = FileInfo()
            if not api.GetFileInformationByHandle(handle, ctypes.byref(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            if info.attributes & 0x400 or bool(info.attributes & 0x10) != directory or not directory and (info.links != 1 or api.GetFileType(handle) != 1):
                raise ValueError("MoE payload has a linked or nonregular component")
            name = ctypes.create_unicode_buffer(32768)
            count = api.GetFinalPathNameByHandleW(handle, name, len(name), 0)
            if not count or count >= len(name) or normalized(name.value) != normalized(str(candidate)):
                raise ValueError("MoE opened handle escaped its checked project path")
            return handle

        lock(cwd, True)
        current = cwd
        parts = path.relative_to(cwd).parts
        for part in parts[:-1]:
            current = current / part
            lock(current, True)
        handle = lock(path, False)
        buffer = ctypes.create_string_buffer(limit + 1)
        size = wintypes.DWORD()
        if not api.ReadFile(handle, buffer, len(buffer), ctypes.byref(size), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return buffer.raw[:size.value]


def read_payload(cwd: Path, path: Path, limit: int) -> bytes:
    return _read_windows(cwd, path, limit) if os.name == "nt" else _read_posix(cwd, path, limit)
