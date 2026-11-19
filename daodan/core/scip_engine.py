"""A precomputed SCIP index read as an engine (`--engine scip`), without its indexer."""
from __future__ import annotations

import json
from pathlib import Path

from source_positions import byte_to_char, byte_to_utf16, char_to_byte, Location, SourceLines, utf16_to_byte


def _pb_read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    size = len(buf)
    while pos < size:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("malformed protobuf varint")
    raise ValueError("truncated protobuf varint")


def _pb_iter_fields(buf: bytes):
    pos = 0
    size = len(buf)
    while pos < size:
        tag, pos = _pb_read_varint(buf, pos)
        field_no = tag >> 3
        wire_type = tag & 0x7
        if wire_type == 0:
            val, pos = _pb_read_varint(buf, pos)
            yield field_no, wire_type, val
        elif wire_type == 1:
            if pos + 8 > size:
                raise ValueError("truncated fixed64")
            yield field_no, wire_type, buf[pos:pos + 8]
            pos += 8
        elif wire_type == 2:
            length, pos = _pb_read_varint(buf, pos)
            if pos + length > size:
                raise ValueError("truncated length-delimited field")
            yield field_no, wire_type, buf[pos:pos + length]
            pos += length
        elif wire_type == 5:
            if pos + 4 > size:
                raise ValueError("truncated fixed32")
            yield field_no, wire_type, buf[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")


class ScipEngine:
    """Resolve call references from a precomputed SCIP index (Protobuf or JSON).

    Nothing in the pass produces an index: this reads one a project already has.
    A `local N` symbol is scoped to its document, so it is keyed by the document. A
    reference whose symbol the index defines nowhere is a definition outside the
    indexed sources, which is external. Positions are converted from the document's
    declared encoding (UTF-16 when unspecified, as scip-typescript writes them).
    """

    name = "scip"
    languages = None  # Query all AST languages in the snapshot, not only Python.
    UNITS = {1: "utf-8", 2: "utf-16", 3: "utf-32"}

    def __init__(self, project_root: Path, index_paths: list[Path] | None = None):
        self.project_root = Path(project_root).resolve()
        self.requested_paths = [Path(p).resolve() for p in (index_paths or ())]
        self.tool_name = "scip"
        self.tool_version = "1.0"
        self.install = None
        self.loaded_indexes: list[str] = []
        self._defs_by_symbol: dict[str, list[tuple[Path, int, int]]] = {}
        self._refs_by_pos: dict[tuple[Path, int, int], list[str]] = {}
        self._units: dict[Path, str] = {}
        self.lines = SourceLines()

    def _document(self, rel: str, occurrences, encoding: int) -> None:
        if not rel:
            return
        path = (self.project_root / rel).resolve()
        self._units[path] = self.UNITS.get(encoding, "utf-16")
        for rng, symbol, roles in occurrences:
            if len(rng) < 3 or not symbol:
                continue
            if symbol.startswith("local "):
                symbol = f"{path.as_posix()}#{symbol}"
            line, column = int(rng[0]) + 1, int(rng[1])
            if roles & 0x1:
                self._defs_by_symbol.setdefault(symbol, []).append((path, line, column))
            else:
                self._refs_by_pos.setdefault((path, line, column), []).append(symbol)

    def _parse_scip_bytes(self, data: bytes) -> None:
        stripped = data.lstrip()
        if stripped.startswith(b"{"):
            doc = json.loads(stripped.decode("utf-8"))
            meta = doc.get("metadata") or {}
            tinfo = meta.get("tool_info") or meta.get("toolInfo") or {}
            self.tool_name = str(tinfo.get("name") or self.tool_name)
            self.tool_version = str(tinfo.get("version") or self.tool_version)
            for d in doc.get("documents") or ():
                occurrences = [(list(o.get("range") or ()), o.get("symbol") or "",
                                int(o.get("symbol_roles") or o.get("symbolRoles") or 0))
                               for o in d.get("occurrences") or ()]
                encoding = d.get("position_encoding") or d.get("positionEncoding") or 0
                self._document(d.get("relative_path") or d.get("relativePath") or "", occurrences,
                               encoding if isinstance(encoding, int) else 0)
            return
        for field_no, wire_type, val in _pb_iter_fields(data):
            if field_no == 1 and wire_type == 2:
                for mf_no, m_wt, m_val in _pb_iter_fields(val):
                    if mf_no == 2 and m_wt == 2:
                        for tf_no, t_wt, t_val in _pb_iter_fields(m_val):
                            if tf_no == 1 and t_wt == 2:
                                self.tool_name = t_val.decode("utf-8", errors="replace") or self.tool_name
                            elif tf_no == 2 and t_wt == 2:
                                self.tool_version = t_val.decode("utf-8", errors="replace") or self.tool_version
            elif field_no == 2 and wire_type == 2:
                rel_path, encoding, occurrences = "", 0, []
                for df_no, d_wt, d_val in _pb_iter_fields(val):
                    if df_no == 1 and d_wt == 2:
                        rel_path = d_val.decode("utf-8", errors="replace")
                    elif df_no == 6 and d_wt == 0:
                        encoding = int(d_val)
                    elif df_no == 2 and d_wt == 2:
                        rng, sym, roles = [], "", 0
                        for of_no, o_wt, o_val in _pb_iter_fields(d_val):
                            if of_no == 1 and o_wt == 2:
                                p = 0
                                while p < len(o_val):
                                    v, p = _pb_read_varint(o_val, p)
                                    rng.append(v)
                            elif of_no == 1 and o_wt == 0:
                                rng.append(int(o_val))
                            elif of_no == 2 and o_wt == 2:
                                sym = o_val.decode("utf-8", errors="replace")
                            elif of_no == 3 and o_wt == 0:
                                roles = int(o_val)
                            elif of_no in (8, 9) and o_wt == 2:
                                # The typed range of the current schema; a zero field is not written.
                                fields = {number: int(value) for number, wire, value in _pb_iter_fields(o_val)
                                          if wire == 0}
                                if of_no == 8:
                                    line = fields.get(1, 0)
                                    rng = [line, fields.get(2, 0), line, fields.get(3, 0)]
                                else:
                                    rng = [fields.get(1, 0), fields.get(2, 0), fields.get(3, 0), fields.get(4, 0)]
                        occurrences.append((rng, sym, roles))
                self._document(rel_path, occurrences, encoding)

    def probe(self) -> tuple[bool, str]:
        self._defs_by_symbol.clear()
        self._refs_by_pos.clear()
        self._units.clear()
        self.loaded_indexes.clear()
        candidates = list(self.requested_paths)
        if not candidates and (self.project_root / "index.scip").is_file():
            candidates.append((self.project_root / "index.scip").resolve())
        if not candidates:
            self.install = "generate index.scip with the language's SCIP indexer and pass --scip-index"
            return False, "no SCIP index found; pass --scip-index <index.scip> or place index.scip in the project root"
        for idx_path in candidates:
            if not idx_path.is_file():
                return False, f"SCIP index does not exist: {idx_path}"
            try:
                self._parse_scip_bytes(idx_path.read_bytes())
                self.loaded_indexes.append(idx_path.as_posix())
            except Exception as exc:
                return False, f"invalid SCIP index {idx_path}: {type(exc).__name__}: {exc}"
        return True, ""

    def _convert(self, path: Path, line: int, column: int, *, to_bytes: bool) -> int | None:
        unit = self._units.get(path, "utf-16")
        text = self.lines.get(path, line)
        if text is None or unit == "utf-8":
            return column if text is not None else None
        if unit == "utf-16":
            return utf16_to_byte(text, column) if to_bytes else byte_to_utf16(text, column)
        return char_to_byte(text, column) if to_bytes else byte_to_char(text, column)

    def definitions(self, path: Path, line: int, column: int) -> list[Location]:
        path = Path(path).resolve()
        native = self._convert(path, line, column, to_bytes=False)
        found = []
        for symbol in self._refs_by_pos.get((path, line, native), ()):
            targets = self._defs_by_symbol.get(symbol)
            if not targets:
                found.append(Location(None, None, None))
                continue
            for target, row, start in targets:
                found.append(Location(target, row, self._convert(target, row, start, to_bytes=True)))
        return found

    def identity(self) -> str:
        return f"scip:{self.tool_name}@{self.tool_version}"

    def report(self) -> dict:
        return {"indexes": list(self.loaded_indexes)}
