"""Incremental JSON snapshot reader with offsets for individual file records."""
from __future__ import annotations

import json
import math
from pathlib import Path

MAX_RECORD_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON number")


def _float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number


DECODER = json.JSONDecoder(object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)


class _Cursor:
    def __init__(self, handle):
        self.handle = handle
        self.buffer = b""
        self.offset = 0
        self.eof = False

    def more(self):
        data = self.handle.read(CHUNK_BYTES)
        self.buffer += data
        self.eof = not data
        if len(self.buffer) > MAX_RECORD_BYTES:
            raise ValueError("snapshot JSON record exceeds storage limit")

    def consume(self, count):
        self.buffer = self.buffer[count:]
        self.offset += count

    def whitespace(self):
        while True:
            count = len(self.buffer) - len(self.buffer.lstrip(b" \t\r\n"))
            self.consume(count)
            if self.buffer or self.eof:
                return
            self.more()

    def expect(self, token):
        self.whitespace()
        if not self.buffer.startswith(token):
            raise ValueError("malformed JSON snapshot")
        self.consume(len(token))

    def value(self):
        self.whitespace()
        start = self.offset
        while True:
            try:
                try:
                    text = self.buffer.decode("utf-8")
                except UnicodeDecodeError as error:
                    if error.end != len(self.buffer) or self.eof:
                        raise ValueError("invalid snapshot UTF-8") from error
                    text = self.buffer[:error.start].decode("utf-8")
                value, end = DECODER.raw_decode(text)
                length = len(text[:end].encode("utf-8"))
                if length == len(self.buffer) and not self.eof:
                    self.more()
                    continue
                if length < len(self.buffer) and self.buffer[length:length + 1] not in b" \t\r\n,:}]":
                    # raw_decode accepts an integer prefix when a decimal or
                    # exponent suffix ends at this chunk's boundary.
                    remainder = self.buffer[length:]
                    if (isinstance(value, (int, float)) and not isinstance(value, bool)
                            and remainder[:1] in b".eE" and not self.eof
                            and not any(byte in b" \t\r\n,:}]" for byte in remainder)):
                        self.more()
                        continue
                    raise ValueError("invalid JSON value delimiter")
                self.consume(length)
                return value, start, self.offset
            except json.JSONDecodeError as error:
                if self.eof:
                    raise ValueError("incomplete JSON snapshot") from error
                self.more()

    def next_member(self):
        self.whitespace()
        if self.buffer.startswith(b"}"):
            self.consume(1)
            return False
        self.expect(b",")
        return True


class JsonSnapshot:
    """Keep only header metadata and byte offsets, never all decoded file rows."""

    def __init__(self, path: Path):
        self.path = path
        self.metadata = {}
        self.offsets = {}
        self.closed = False
        with path.open("rb") as handle:
            cursor = _Cursor(handle)
            cursor.expect(b"{")
            cursor.whitespace()
            if cursor.buffer.startswith(b"}"):
                raise ValueError("snapshot has no inventory")
            seen = set()
            while True:
                key, _, _ = cursor.value()
                if not isinstance(key, str) or key in seen:
                    raise ValueError("invalid or duplicate snapshot member")
                seen.add(key)
                cursor.expect(b":")
                if key == "files":
                    cursor.expect(b"{")
                    cursor.whitespace()
                    if cursor.buffer.startswith(b"}"):
                        cursor.consume(1)
                    else:
                        while True:
                            rel, _, _ = cursor.value()
                            if not isinstance(rel, str) or rel in self.offsets:
                                raise ValueError("invalid or duplicate snapshot path")
                            cursor.expect(b":")
                            entry, start, end = cursor.value()
                            if not isinstance(entry, dict):
                                raise ValueError("invalid snapshot file metadata")
                            self.offsets[rel] = (start, end)
                            del entry
                            if not cursor.next_member():
                                break
                else:
                    value, _, _ = cursor.value()
                    self.metadata[key] = value
                if not cursor.next_member():
                    break
            cursor.whitespace()
            if cursor.buffer or not cursor.eof:
                if not cursor.eof:
                    cursor.more()
                    cursor.whitespace()
                if cursor.buffer:
                    raise ValueError("trailing snapshot JSON content")
        if "files" not in seen or self.metadata.get("schema") != 1:
            raise ValueError("unsupported snapshot schema")

    def get_file(self, rel, *, semantic=True):
        if self.closed:
            raise ValueError("snapshot is closed")
        location = self.offsets.get(rel)
        if location is None:
            return None
        start, end = location
        with self.path.open("rb") as handle:
            handle.seek(start)
            data = handle.read(end - start)
        if len(data) != end - start:
            raise ValueError("snapshot changed while reading")
        value = DECODER.decode(data.decode("utf-8"))
        if not semantic:
            value.pop("semantic", None)
        return value

    def iter_files(self, *, semantic=True):
        for rel in sorted(self.offsets):
            yield rel, self.get_file(rel, semantic=semantic)

    def close(self):
        self.closed = True
        self.offsets.clear()
