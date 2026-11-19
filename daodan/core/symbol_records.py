"""The symbols of one parse result as a snapshot records them: qualified names,
line spans, body hashes and declared signatures."""
from __future__ import annotations

from source_files import hash_text


# A signature value (an annotation, a default, a decorator) longer than this
# keeps its head and a digest of the whole: a long literal cannot bloat every
# packet that carries the signature, and an edit to it still changes the value.
MAX_SIGNATURE_TEXT = 200


def _signature_text(value: object) -> str:
    text = " ".join(str(value).split())
    if len(text) <= MAX_SIGNATURE_TEXT:
        return text
    return text[:160] + "..." + hash_text(text)


def signature_record(info) -> dict | None:
    """The declared signature of a function or class, in one comparable shape.

    A key appears only with a value. `fields` lists the signature fields the
    adapter extracts exhaustively (languages.base.SIGNATURE_FIELDS): a listed
    field whose key is absent is absent from the source, while an unlisted one
    may only be missing from the extraction. No position enters the record, so
    a symbol that only moves keeps its signature.
    """
    record: dict = {}

    def keep(key: str, value) -> None:
        if value:
            record[key] = value

    def described(items) -> list[dict]:
        out = []
        for item in items:
            entry = {"name": _signature_text(item.name)}
            for key in ("kind", "annotation", "default"):
                value = getattr(item, key, None)
                if value is not None:
                    entry[key] = _signature_text(value)
            out.append(entry)
        return out

    if hasattr(info, "parameters"):
        keep("params", described(info.parameters))
        if info.return_annotation is not None:
            keep("returns", _signature_text(info.return_annotation))
        keep("async", bool(info.is_async))
        keep("generator", bool(getattr(info, "is_generator", False)))
        keep("static", bool(getattr(info, "is_staticmethod", False)))
    else:
        keep("bases", [_signature_text(base) for base in info.bases])
        attributes = getattr(info, "attributes", None)
        keep("attributes", described(attributes) if attributes
             else [{"name": _signature_text(name)} for name in info.class_variables])
    keep("decorators", [_signature_text(text) for text in getattr(info, "decorators", None) or ()])
    keep("visibility", getattr(info, "visibility", None))
    keep("fields", sorted(getattr(info, "signature_fields", ()) or ()))
    return record or None


def _top_level(result, total: int) -> list[dict]:
    """Classes and free functions in source order, each with an end line: exact, or the line before the next."""
    top: list[dict] = []
    for cls in result.classes:
        if cls.line_number > 0:
            top.append({
                "name": cls.name, "kind": cls.kind, "start": cls.line_number,
                "end": getattr(cls, "end_line", None), "methods": list(cls.methods), "info": cls,
            })
    for func in result.functions:
        if func.line_number > 0:
            top.append({
                "name": func.name, "kind": "function", "start": func.line_number,
                "end": getattr(func, "end_line", None), "methods": [], "info": func,
            })
    top.sort(key=lambda item: (item["start"], item["name"]))

    for index, item in enumerate(top):
        item["precision"] = "exact" if item["end"] else "inferred"
        if not item["end"]:
            following = top[index + 1]["start"] - 1 if index + 1 < len(top) else total
            item["end"] = following
        item["end"] = max(item["end"], item["start"])
    return top


class _Spans:
    """The spans of one file's symbols, keyed by qualified name."""

    def __init__(self, lines: list[str]):
        self.lines = lines
        self.total = len(lines)
        self.spans: dict[str, dict] = {}
        self._hashes: dict[tuple[int, int], str] = {}

    def _hash(self, start: int, end: int) -> str:
        # Many symbols can share one span (a minified line, a class and its one
        # method); each distinct span is hashed once.
        key = (start, end)
        if key not in self._hashes:
            self._hashes[key] = hash_text("\n".join(self.lines[start - 1:end]))
        return self._hashes[key]

    def record(self, name: str, kind: str, start: int, end: int, precision: str, info) -> None:
        total = self.total
        if not (1 <= start <= end <= total):
            precision = "inferred"
        start = max(1, min(start, total))
        end = max(start, min(end, total))
        # A class carrying two methods of the same name (an overload) would
        # otherwise have the second `record()` call overwrite the first,
        # losing the earlier span entirely: an edit inside the lost overload
        # then changes no hash, and compare_symbols never reports it. Widen
        # the span to cover every occurrence instead, so any edit to any of
        # them moves the hash. That over-marks rather than under-marks: it
        # costs one extra re-derivation instead of a missed claim.
        existing = self.spans.get(name)
        signatures = list(existing.get("signatures", ())) if existing is not None else []
        if existing is not None:
            start = min(start, existing["start"])
            end = max(end, existing["end"])
            precision = "merged"
        signature = signature_record(info)
        if signature is not None:
            signatures.append(signature)
        self.spans[name] = {
            "kind": kind,
            "start": start,
            "end": end,
            "hash": self._hash(start, end),
            "span_precision": precision,
        }
        if signatures:
            self.spans[name]["signatures"] = signatures

    def methods(self, item: dict) -> None:
        """A class's methods inside its span; a method without an end line ends before the next one."""
        methods = sorted(
            (m for m in item["methods"] if m.line_number > 0),
            key=lambda m: m.line_number,
        )
        for index, method in enumerate(methods):
            end = getattr(method, "end_line", None)
            precision = "exact" if end else "inferred"
            if not end:
                end = methods[index + 1].line_number - 1 if index + 1 < len(methods) else item["end"]
            self.record(f"{item['name']}.{method.name}", "method", method.line_number, end, precision, method)

    def nested(self, result) -> None:
        # Definitions the adapter reports outside the two top-level lists: nested
        # functions and classes, definitions inside a compound statement, and PEP 695
        # type aliases. Their name is already qualified by the adapter, and their end
        # line is exact, so nothing is inferred here. Recorded after the top-level
        # symbols: a name both lists carry is a redefinition, and `record` widens the
        # span to cover every occurrence rather than losing one.
        nested = sorted(
            (item for item in getattr(result, "nested", ()) or () if item.info.line_number > 0),
            key=lambda item: (item.info.line_number, item.qualified_name),
        )
        for item in nested:
            info = item.info
            end = getattr(info, "end_line", None)
            self.record(item.qualified_name, item.kind, info.line_number, end or self.total,
                        "exact" if end else "inferred", info)


def symbol_spans(result, lines: list[str]) -> dict[str, dict]:
    """
    Every symbol in a parse result, qualified, with its line span and body hash.

    Top-level symbols (classes and free functions) are spanned first: an exact
    end line where the adapter has one, otherwise the line before the next
    top-level symbol. Methods are spanned inside their class, so a class span
    always encloses its methods and editing a method moves both hashes.
    Definitions the adapter reports in `nested` (a nested function or class, a
    definition inside a compound statement, a PEP 695 alias) are spanned last,
    inside the symbol that encloses them, under the name the adapter qualified.

    A symbol the adapter describes also carries `signatures`, one
    signature_record per declaration in source order: several when overloads
    or redefinitions share the name.
    """
    spans = _Spans(lines)
    for item in _top_level(result, len(lines)):
        spans.record(item["name"], item["kind"], item["start"], item["end"], item["precision"], item["info"])
        spans.methods(item)
    spans.nested(result)
    return spans.spans
