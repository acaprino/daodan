"""Language servers asked at a call position, through multilspy, each in a mirror of the
project outside it (`MirroredEngine`). The Vue and Svelte adapter (`indexers/vue_svelte.py`) asks
typescript-language-server; an indexer installs and mirrors its tool through `MirroredEngine`
(`indexers/runtime.py`)."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path, PurePosixPath

from source_positions import (byte_to_char, byte_to_utf16, char_to_byte, EngineFailure, Location, SourceLines,
                              utf16_to_byte)
from engine_tools import publish, shared_engine_dir


# Bounds that keep one server from taking a shared machine.
SERVER_MEMORY_MB = 2048


ENGINE_THREADS = 2


LSP_START_TIMEOUT = 300


LSP_REQUEST_TIMEOUT = 60


LSP_OPEN_DOCUMENTS = 64


class LspEngine:
    """A language server asked `textDocument/definition` at the callee name.

    multilspy supplies the pinned server releases and the JSON-RPC transport; each
    subclass says how its server is installed, launched, configured and known to be
    ready. The server is installed on first use into the shared engine directory,
    one directory per version, and writes nothing into the project. Positions cross
    the boundary in UTF-8 bytes and are converted to the encoding the server
    negotiated (UTF-16 unless it says otherwise), using the text the server was given.
    """

    name = "lsp"
    server_name = "language-server"
    languages: tuple[str, ...] = ()
    language_ids: dict[str, str] = {}

    def __init__(self, project_root: Path, install_dir: Path | None = None):
        self.project_root = Path(project_root).resolve()
        self.install_root = Path(install_dir) if install_dir else shared_engine_dir(self.server_name)
        self.install = None
        self.installed_now = False
        self.handler = None
        self.loop = None
        self.encoding = "utf-16"
        self.served: dict[Path, tuple[str, list[str]]] = {}
        self.virtual: dict[Path, Path] = {}
        self.open: dict[str, None] = {}
        self.timeouts = 0
        self.lines = SourceLines()

    # What a subclass supplies.
    def pinned(self) -> dict:
        """The release multilspy pins for this server, with at least `version`."""
        raise NotImplementedError

    def prepare(self, home: Path) -> tuple[bool, str]:
        """Install the pinned release into `home` when absent; (False, reason) with `self.install` set if it cannot."""
        raise NotImplementedError

    def command(self, home: Path) -> tuple[list[str], dict]:
        raise NotImplementedError

    def initialization_options(self) -> dict | None:
        return None

    def settings(self) -> dict:
        return {}

    def readiness_probe(self) -> tuple[str, str, int, int] | None:
        """A virtual document and a position whose definition must be on its first line, or None."""
        return None

    async def wait_ready(self) -> None:
        return None

    def notifications(self) -> dict:
        return {}

    def cleanup(self) -> None:
        return None

    # Shared machinery.
    @property
    def version(self) -> str | None:
        try:
            return self.pinned()["version"]
        except Exception:
            return None

    def home(self) -> Path:
        return self.install_root / str(self.version)

    def _run(self, coroutine, timeout):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout=timeout)

    def _install(self, home: Path, fill) -> None:
        """Fill a sibling directory, then publish it whole, so an interrupted install leaves nothing usable.

        Each install fills its own: the server and the pass, or two workers, may install one release at once;
        the first published stays and the other's is dropped."""
        if (home / ".installed").is_file():
            return
        self.installed_now = True
        print(f"installing {self.server_name} {self.version} into {home} (first use)", flush=True)
        publish(home, fill, self.version or "")

    def workspace_root(self) -> Path:
        """The folder the server opens as its workspace: the project, unless the engine describes one elsewhere."""
        return self.project_root

    def initialize_params(self) -> dict:
        folder = self.workspace_root()
        uri = folder.as_uri()
        return {
            "processId": os.getpid(), "rootPath": str(folder), "rootUri": uri,
            "workspaceFolders": [{"uri": uri, "name": folder.name}],
            "capabilities": {
                "general": {"positionEncodings": ["utf-16"]},
                "workspace": {"configuration": True, "workspaceFolders": True,
                              "didChangeConfiguration": {"dynamicRegistration": True}},
                "textDocument": {"synchronization": {"dynamicRegistration": True, "didSave": False},
                                 "definition": {"dynamicRegistration": True, "linkSupport": True}},
                "window": {"workDoneProgress": True},
            },
            "initializationOptions": self.initialization_options(),
        }

    def probe(self) -> tuple[bool, str]:
        try:
            from multilspy.lsp_protocol_handler.server import LanguageServerHandler, ProcessLaunchInfo
        except ImportError as error:
            self.install = "check the network: Daodan downloads its uv, which gives the pass multilspy"
            return False, f"multilspy is not installed: {error}"
        if self.version is None:
            return False, f"multilspy pins no {self.server_name} release"
        home = self.home()
        try:
            ready, reason = self.prepare(home)
        except Exception as error:
            return False, f"could not install {self.server_name}: {type(error).__name__}: {error}"
        if not ready:
            return False, reason
        command, environment = self.command(home)
        self.handler = LanguageServerHandler(ProcessLaunchInfo(cmd=command, env=environment,
                                                               cwd=str(self.project_root)),
                                             start_independent_lsp_process=False)

        async def answer_none(_params):
            return None

        def section(path):
            value = self.settings()
            for key in filter(None, (path or "").split(".")):
                value = value.get(key) if isinstance(value, dict) else None
            return value

        async def configuration(params):
            return [section(item.get("section")) for item in params.get("items", ())]

        async def ignore(_params):
            return None

        for method in ("client/registerCapability", "client/unregisterCapability", "window/workDoneProgress/create",
                       "workspace/executeClientCommand", "window/showMessageRequest"):
            self.handler.on_request(method, answer_none)
        self.handler.on_request("workspace/configuration", configuration)
        for method in ("$/progress", "textDocument/publishDiagnostics", "window/logMessage", "window/showMessage",
                       "telemetry/event", "language/status", "language/progressReport",
                       "language/eventNotification", "language/actionableNotification"):
            self.handler.on_notification(method, ignore)
        for method, callback in self.notifications().items():
            self.handler.on_notification(method, callback)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

        async def start():
            await self.handler.start()
            response = await self.handler.send.initialize(self.initialize_params())
            self.encoding = ((response or {}).get("capabilities") or {}).get("positionEncoding") or "utf-16"
            self.handler.notify.initialized({})
            if self.settings():
                self.handler.notify.workspace_did_change_configuration({"settings": self.settings()})
            await self.wait_ready()

        try:
            self._run(start(), LSP_START_TIMEOUT)
            probe = self.readiness_probe()
            if probe is not None:
                name, text, line, character = probe
                uri = (self.workspace_root() / name).as_uri()
                self._open(uri, self.language_ids.get(Path(name).suffix, self.name), text)
                # A server that indexes after starting answers once its index is usable.
                deadline = time.monotonic() + LSP_START_TIMEOUT
                answer = self._ask(uri, line, character)
                while not any(row == 0 for _uri, row, _units in answer) and time.monotonic() < deadline:
                    time.sleep(2)
                    answer = self._ask(uri, line, character)
                self._close(uri)
                if not any(row == 0 for _uri, row, _units in answer):
                    return False, f"{self.server_name} answered no definition for its readiness probe"
        except Exception as error:
            return False, f"{self.server_name} did not start: {type(error).__name__}: {error}"
        return True, ""

    def _open(self, uri: str, language: str, text: str) -> None:
        async def notify():
            self.handler.notify.did_open_text_document(
                {"textDocument": {"uri": uri, "languageId": language, "version": 0, "text": text}})
        self._run(notify(), LSP_REQUEST_TIMEOUT)
        self.open[uri] = None
        while len(self.open) > LSP_OPEN_DOCUMENTS:
            self._close(next(iter(self.open)))

    def _close(self, uri: str) -> None:
        async def notify():
            self.handler.notify.did_close_text_document({"textDocument": {"uri": uri}})
        self._run(notify(), LSP_REQUEST_TIMEOUT)
        self.open.pop(uri, None)

    def _ask(self, uri: str, line: int, character: int, method: str = "definition") -> list[tuple[str, int, int]]:
        process = getattr(self.handler, "process", None)
        if process is not None and process.returncode is not None:
            raise EngineFailure(f"{self.server_name} exited with code {process.returncode}")
        try:
            response = self._run(getattr(self.handler.send, method)(
                {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}}),
                LSP_REQUEST_TIMEOUT)
        except TimeoutError:
            if method != "definition":
                raise  # a slow follow-up question costs its answer, never the pass
            self.timeouts += 1
            if self.timeouts >= 3:
                raise EngineFailure(f"{self.server_name} timed out three times in a row") from None
            raise
        self.timeouts = 0
        if isinstance(response, dict):
            response = [response]
        found = []
        for item in response or ():
            target = item.get("targetUri") or item.get("uri")
            area = item.get("targetSelectionRange") or item.get("targetRange") or item.get("range")
            if target and area:
                found.append((target, area["start"]["line"], area["start"]["character"]))
        return found

    def served_text(self, path: Path) -> tuple[Path, str]:
        """The document the server is given for a source file: the file itself, line endings included.

        A server that reads a closed file from disk and an open one from this text must
        see the same characters, or every CRLF line shifts its answers by one more.
        """
        with path.open(encoding="utf-8", newline="") as handle:
            return path, handle.read()

    def _document(self, path: Path) -> tuple[str, list[str]]:
        if path not in self.served:
            served, text = self.served_text(path)
            if served.resolve() != path:
                # Answers come back resolved: a link inside the served path leads to the real file.
                self.virtual[served.resolve()] = path
            self.served[path] = (served.as_uri(), text.split("\n"))
        uri, lines = self.served[path]
        if uri not in self.open:
            language = self.language_ids.get(PurePosixPath(uri).suffix.lower(), self.name)
            self._open(uri, language, "\n".join(lines))
        return uri, lines

    def _to_server(self, line: str, column: int) -> int | None:
        if self.encoding == "utf-8":
            return column if byte_to_char(line, column) is not None else None
        if self.encoding == "utf-32":
            return byte_to_char(line, column)
        return byte_to_utf16(line, column)

    def _from_server(self, line: str, units: int) -> int | None:
        if self.encoding == "utf-8":
            return units if byte_to_char(line, units) is not None else None
        if self.encoding == "utf-32":
            return char_to_byte(line, units) if 0 <= units <= len(line) else None
        return utf16_to_byte(line, units)

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        """Where the callee at a UTF-8 byte column is declared."""
        return self._locations(path, line, column, "definition")

    def implementations(self, path: Path, line: int, column: int) -> list[Location]:
        """Where it is implemented: asked when its declaration is a contract or a value."""
        return self._locations(path, line, column, "implementation")

    def _locations(self, path: Path, line: int, column: int, method: str) -> list[Location]:
        """Ask at a UTF-8 byte column, converted to the negotiated units of the served text."""
        from urllib.parse import unquote, urlparse
        from urllib.request import url2pathname
        path = Path(path).resolve()
        uri, lines = self._document(path)
        units = self._to_server(lines[line - 1], column) if 1 <= line <= len(lines) else None
        if units is None:
            raise ValueError(f"no character starts at byte {column} of {path}:{line}")
        found = []
        for target_uri, row, start in self._ask(uri, line - 1, units, method):
            if not target_uri.startswith("file:"):
                # A class file or a library the server reads from an archive: external.
                found.append(Location(None, None, None))
                continue
            target = Path(url2pathname(unquote(urlparse(target_uri).path))).resolve()
            target = self.virtual.get(target, target)
            if self.workspace_root() != self.project_root and target.is_relative_to(self.workspace_root()):
                target = self.project_root / target.relative_to(self.workspace_root())
            if target in self.served:
                served_lines = self.served[target][1]
                name_line = served_lines[row] if 0 <= row < len(served_lines) else None
            else:
                name_line = self.lines.get(target, row + 1) if target.is_relative_to(self.project_root) else None
            found.append(Location(target, row + 1,
                                  self._from_server(name_line, start) if name_line is not None else None))
        return found

    def close(self) -> None:
        if self.handler is not None and self.loop is not None:
            async def stop():
                await self.handler.shutdown()
                await self.handler.stop()
            try:
                self._run(stop(), LSP_REQUEST_TIMEOUT)
            except Exception:
                pass
            self.handler = None
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop = None
        self.cleanup()

    def identity(self) -> str:
        return f"{self.server_name}@{self.version}"

    def context(self) -> str | None:
        return None if self.version is None else self.identity()

    def report(self) -> dict:
        return {"server": self.identity(), "install_dir": self.home().as_posix() if self.version else None,
                "installed_now": self.installed_now, "documents": len(self.served),
                "position_encoding": self.encoding}


def _multilspy_pins(server: str) -> dict:
    """multilspy's runtime dependency file for one of its servers."""
    spec = importlib.util.find_spec("multilspy")
    if spec is None or not spec.origin:
        raise ImportError("multilspy")
    path = Path(spec.origin).parent / "language_servers" / server / "runtime_dependencies.json"
    return json.loads(path.read_text(encoding="utf-8"))


def link_directory(link: Path, target: Path) -> None:
    """A directory link: a junction on Windows, which needs no privilege, a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def remove_mirror(root: Path) -> None:
    """Remove a mirror's links and copies without ever entering a link, so no target file is touched."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink() or os.path.isjunction(root):
        return
    for entry in root.iterdir():
        if os.path.isjunction(entry):
            os.rmdir(entry)
        elif entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            remove_mirror(entry)
    root.rmdir()


class MirroredEngine(LspEngine):
    """An engine whose server works in a mirror of the project, so what its tools write never lands in the project.

    A package manager asked to read the project's crates or modules may write a
    lock file or a checksum file beside the manifest. The mirror holds a link per
    top-level directory and a copy of each top-level file, so such a write lands in
    the copy; answers are mapped back to the project's files. Removing the mirror
    never enters a link.
    """

    mirror: Path | None = None
    mirror_skip = (".git",)

    def build_mirror(self, links: dict | None = None) -> Path:
        mirror = Path(tempfile.mkdtemp(prefix=f"daodan-{self.name}-")) / self.project_root.name
        mirror.mkdir()
        # A directory that receives a link is a real directory of the mirror, one link per child.
        real = {parent.as_posix() for name in links or {} for parent in PurePosixPath(name).parents} - {"."}

        def fill(source: Path, target: Path, relative: PurePosixPath) -> None:
            for entry in source.iterdir():
                if entry.name in self.mirror_skip:
                    continue
                if entry.is_dir():
                    if (relative / entry.name).as_posix() in real:
                        (target / entry.name).mkdir()
                        fill(entry, target / entry.name, relative / entry.name)
                    else:
                        link_directory(target / entry.name, entry)
                elif entry.is_file():
                    shutil.copyfile(entry, target / entry.name)

        fill(self.project_root, mirror, PurePosixPath(""))
        for name, target in (links or {}).items():
            link_directory(mirror / name, target)
        return mirror

    def workspace_root(self) -> Path:
        return self.mirror or self.project_root

    def served_text(self, path: Path) -> tuple[Path, str]:
        with path.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
        return self.workspace_root() / path.relative_to(self.project_root), text

    def cleanup(self) -> None:
        if self.mirror is not None:
            remove_mirror(self.mirror)
            self.mirror.parent.rmdir()
            self.mirror = None


