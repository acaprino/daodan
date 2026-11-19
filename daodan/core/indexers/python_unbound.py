"""The checker's pass over the project scip-python indexed (`python.py`), after it: what Pyright, over the same
environment, says of each member a file of the project reads (`x.y`), asked by its language server's hover at the
member's name. One JSON line each, `[path, line (1-based), column (UTF-16), kind, said]`: kind `Any` or `Unknown`
(the checker types the member so: only execution knows the value) or `bound` (the checker binds a declaration,
`said` its kind and name: `method format`), none when the hover says nothing. Standard library only; no project
code runs.

    python python_unbound.py <node> <pyright's langserver.index.js> <project folder> <its Python or -> > unbound.jsonl
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "site-packages"}  # folders that hold no project code
SAID = re.compile(r"^\((\w[\w ]*)\) (?:def )?([\w.]+)(?:\((?:.|\n)*\))?(?:: (.+))?")  # `(kind) name: type`, `(kind) def name(...)`


def kind(hover: str | None) -> tuple[str, str] | None:
    """`(kind, said)` of a hover's text at a member's name, None when it says nothing."""
    text = (hover or "").strip().removeprefix("```python").strip().split("\n```")[0]
    found = SAID.match(text)
    if not found:
        return None
    typed = (found.group(3) or "").strip()
    return (typed, "") if typed in ("Any", "Unknown") else ("bound", f"{found.group(1)} {found.group(2)}")


def members(source: str) -> list[tuple[int, int]]:
    """`(line, UTF-16 column)` of the name of each member the code reads, as written right after its dot, in
    order."""
    lines, found = source.split("\n"), set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Attribute) or node.end_lineno is None:
            continue
        data = lines[node.end_lineno - 1].encode("utf-8")
        begin = node.end_col_offset - len(node.attr.encode("utf-8"))
        if begin < 1 or data[begin:node.end_col_offset].decode("utf-8", "replace") != node.attr:
            continue
        found.add((node.end_lineno, len(data[:begin].decode("utf-8", "replace").encode("utf-16-le")) // 2))
    return sorted(found)


class Server:
    """Pyright's language server over stdio, answering its configuration with `settings`."""

    def __init__(self, command: list[str], root: Path, settings: dict):
        self.process = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
        self.settings, self.counter = settings, 0
        self.ask("initialize", {"processId": os.getpid(), "rootUri": root.as_uri(), "capabilities": {},
                                "workspaceFolders": [{"uri": root.as_uri(), "name": root.name}]})
        self.tell("initialized", {})
        self.tell("workspace/didChangeConfiguration", {"settings": settings})

    def _send(self, message: dict) -> None:
        body = json.dumps({"jsonrpc": "2.0", **message}).encode("utf-8")
        self.process.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.process.stdin.flush()

    def _receive(self) -> dict:
        length = 0
        while True:
            header = self.process.stdout.readline()
            if not header:
                raise EOFError("the language server ended")
            header = header.decode("ascii").strip()
            if not header:
                break
            if header.lower().startswith("content-length:"):
                length = int(header.split(":", 1)[1])
        return json.loads(self.process.stdout.read(length))

    def tell(self, method: str, params: dict) -> None:
        self._send({"method": method, "params": params})

    def ask(self, method: str, params: dict):
        self.counter += 1
        ident = self.counter
        self._send({"id": ident, "method": method, "params": params})
        while True:
            message = self._receive()
            if "method" in message and "id" in message:  # the server's own request: its configuration, or none
                items = (message.get("params") or {}).get("items") or []
                result = [self.settings.get(item.get("section")) for item in items] \
                    if message["method"] == "workspace/configuration" else None
                self._send({"id": message["id"], "result": result})
            elif message.get("id") == ident:
                return message.get("result")

    def close(self) -> None:
        self.process.kill()


def main(node: str, langserver: str, folder: str, python: str) -> None:
    root = Path(folder).resolve()
    settings = {"python": {"pythonPath": python} if python != "-" else {}, "python.analysis": {}}
    server = Server([node, langserver, "--stdio"], root, settings)
    try:
        for directory, names, files in os.walk(root, followlinks=True):  # the run's mirror links its folders
            names[:] = sorted(name for name in names if name not in SKIP and not name.startswith("."))
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = Path(directory) / name
                try:
                    source = path.read_text(encoding="utf-8")
                    sites = list(members(source))
                except (OSError, UnicodeError, SyntaxError, ValueError):
                    continue  # a file Python does not read: the snapshot says why
                if not sites:
                    continue
                uri, rel = path.as_uri(), path.relative_to(root).as_posix()
                server.tell("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "python",
                                                                      "version": 1, "text": source}})
                lines = []
                for line, column in sites:
                    answer = server.ask("textDocument/hover", {"textDocument": {"uri": uri},
                                                              "position": {"line": line - 1, "character": column}})
                    contents = (answer or {}).get("contents") or {}
                    found = kind(contents.get("value") if isinstance(contents, dict) else str(contents))
                    if found:
                        lines.append(json.dumps([rel, line, column, *found]))
                server.tell("textDocument/didClose", {"textDocument": {"uri": uri}})
                if lines:
                    sys.stdout.write("\n".join(lines) + "\n")
    finally:
        server.close()


if __name__ == "__main__":
    main(*sys.argv[1:5])
