"""Vue and Svelte components for scip-typescript, indexed with the project's other files, each through the
TypeScript its framework's own tool generates, and the index brought back to the component through the tool's map.

- Svelte: scip-typescript (from 0.6.2, sourcegraph/scip-typescript#509) turns a `.svelte` file of its program into
  TypeScript with svelte2tsx, its own dependency (`^0.7.63`), and maps the index back itself: the program lists the
  component, and the result names the svelte2tsx it ran (`tools`). One indexer process loads one svelte2tsx, and
  its mapping reads that one's output, so the project's is not used.
- Vue: @vue/language-core (Volar, what vue-tsc runs; `createVueLanguagePlugin(ts, compilerOptions,
  vueCompilerOptions, asFileName)`, the same in 2.1 and 3.3, gives a virtual code whose embedded
  `script_(js|jsx|ts|tsx)` code carries Volar's mappings `{sourceOffsets, generatedOffsets, lengths}`).
  `components.cjs` runs it in the execution, with no network, before the indexer: the project's own, found from
  the component's folder or through the package that depends on it, else Daodan's pin (`PIN`), which the
  preparation installs from npm; the pin too in place of a project's tool before 2.0, which has no language plugin
  (1.8.8 exports `createVueLanguage`), and the record keeps that one's version (`instead`); the result names whose
  (`tools`). The generated file is the component's name
  with `.ts` (`.tsx` for a component in TSX), beside it in the copy, where TypeScript finds it for an import of the
  component (an import of `foo.js` may be matched by `foo.js.ts`, `moduleNameResolver`), except in ECMAScript
  module resolution, which adds no extension: such an import is a gap (`gaps`).
- `rewrite` gives each generated document of the index to its component: each occurrence through the map to the
  component's positions, in UTF-16 code units as the index's; one the map does not cover whole, both ends and the
  same length (generated code), is left out; the module's definition, at the document's start, is the
  component's start, and a symbol generated code defines for another the component reads (Vue 2's `setup`,
  `n: n as typeof n`; the compiler's macros, `declare const { defineProps, … }: typeof import('vue');`) is that
  other (`_held`). A Volar span maps a run of characters, of which only those marked for navigation are used. The
  checker's pass (`typescript_unbound.js`) is brought back the same way.
"""
from __future__ import annotations

import bisect
import collections
import json
import posixpath
from pathlib import Path

import preparation

SUFFIXES = {".vue": "vue", ".svelte": "svelte"}
# Daodan's Vue tool, where the project installs none (npm's registry metadata: MIT,
# sha512-kRB+3hHg0c+BdD1XLAvwjVMQd5pC05zijSlPDRI3ERvC/s04JlRs5upy2KjeMg/9m9oD5zuMVh9yVvkKfZqoJg==; vue-tsc 3.3.14's).
PIN = "@vue/language-core@3.3.14"
OURS = f"{preparation.T}/frameworks"
SCRIPT = f"{preparation.STATE}/scip-typescript/components.cjs"  # carried with the copy
LIST = f"{preparation.STATE}/scip-typescript/components.json"
MAPS = "/daodan/out/components.json"  # brought back with the index


def listed(project_dir: Path, files) -> list[dict]:
    """The components among `files` (checkout-relative), each `{rel, kind, ts}`: `ts` when a script of it is
    TypeScript, as the snapshot reads it."""
    from languages.sfc import mask_non_script
    out = []
    for rel in sorted(files):
        kind = SUFFIXES.get(posixpath.splitext(rel)[1].lower())
        if kind:
            text = (Path(project_dir) / rel).read_text(encoding="utf-8", errors="replace")
            out.append({"rel": rel, "kind": kind, "ts": mask_non_script(text)[1]})
    return out


def install(components: list[dict]) -> list[str]:
    """The preparation's line installing Daodan's Vue tool when a component needs it, with npm, never a script;
    one that fails is said as `preparation.missing` reads it."""
    if not any(item["kind"] == "vue" for item in components):
        return []
    return [f"{{ npm install --prefix {OURS} --ignore-scripts --no-audit --no-fund --loglevel=error {PIN} >&2 ; }}"
            f" || echo 'DAODAN-MISSING {PIN}' >&2"]


def generate(work: str, indexer: str) -> str:
    """The execution's line writing the generated files and their maps (`components.cjs`) in the copy `work`;
    `indexer` the folder of scip-typescript's package, whose TypeScript reads when the project has none."""
    return f"{preparation.T}/node/bin/node {SCRIPT} {LIST} {work} {OURS} {MAPS} {indexer}"


def include(components: list[dict]) -> list[str]:
    """The generated tsconfig's entries for the components: a Svelte one itself, a Vue one's generated file, which
    exists once the script ran."""
    out = []
    for item in components:
        out += [item["rel"] + ".ts", item["rel"] + ".tsx"] if item["kind"] == "vue" else [item["rel"]]
    return out


def gaps(report: dict) -> list[dict]:
    """A `component_import_unresolved` gap for the imports of a Vue component the program's TypeScript resolves to
    nothing, with the files that hold them and the module resolution."""
    found = report.get("unresolved") or {}
    if not found:
        return []
    count = sum(len(items) for items in found.values())
    return [{"kind": "component_import_unresolved", "count": count, "files": sorted(found),
             "detail": f"{count} imports of a .vue component TypeScript resolves to nothing (module resolution "
                       f"{report.get('resolution')}: an ECMAScript module's import adds no .ts to the name), in "
                       + ", ".join(sorted(found)[:10]) + (" and more" if len(found) > 10 else "")}]


# ------------------------------------------------------------------------------------------------- the maps

def _starts(text: str) -> list[int]:
    """The UTF-16 offset of each line of `text`."""
    out, at = [0], 0
    for line in text.split("\n")[:-1]:
        at += len(line.encode("utf-16-le")) // 2 + 1
        out.append(at)
    return out


def segments(entry: dict, source: str) -> dict[int, list[tuple]]:
    """Per generated line, its segments `(column, source line, source column, run)`, sorted: `run` the characters
    a Volar span maps on that line."""
    lines: dict[int, list[tuple]] = {}
    generated, original = entry["starts"], _starts(source)
    for start, source_start, length in entry["spans"]:
        at = start
        while at < start + length:  # one piece per generated line the span crosses
            row = bisect.bisect_right(generated, at) - 1
            end = min(start + length, generated[row + 1] if row + 1 < len(generated) else start + length)
            offset = source_start + (at - start)
            source_row = bisect.bisect_right(original, offset) - 1
            lines.setdefault(row, []).append((at - generated[row], source_row, offset - original[source_row],
                                              end - at))
            at = end
    return {row: sorted(items, key=lambda s: s[0]) for row, items in lines.items()}


def place(line: list[tuple], column: int, end: bool = False) -> tuple[int, int] | None:
    """The source position of a generated column (of the character before it, for an `end`), None outside the
    segment's run."""
    probe = column - 1 if end else column
    at = bisect.bisect_right(line, (probe, float("inf"))) - 1
    if at < 0 or probe < 0:
        return None
    start, row, col, run = line[at]
    if probe >= start + run:
        return None
    return row, col + (probe - start) + (1 if end else 0)


def mapped(lines: dict, values: list[int]) -> list[int] | None:
    """A SCIP range of the generated document as the component's, None when the map does not hold it whole."""
    if len(values) not in (3, 4):
        return None
    row, start = values[0], values[1]
    end_row, end = (values[2], values[3]) if len(values) == 4 else (row, values[2])
    first, last = place(lines.get(row, []), start), place(lines.get(end_row, []), end, end=True)
    if first is None or last is None or (row == end_row and last[0] == first[0]
                                         and last[1] - first[1] != end - start):
        return None
    return [first[0], first[1], last[1]] if first[0] == last[0] else [first[0], first[1], last[0], last[1]]


# ------------------------------------------------------------------------------------------------- the index

def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _field(number: int, wire: int, value) -> bytes:
    if wire == 0:
        return _varint(number << 3) + _varint(value)
    if wire == 2:
        return _varint(number << 3 | 2) + _varint(len(value)) + value
    return _varint(number << 3 | wire) + value


def _parts(data: bytes) -> tuple[list[int], bytes, int]:
    """An occurrence's range, symbol and roles."""
    from code_graph import _fields, _ints
    found = {number: (wire, value) for number, wire, value in _fields(data)}
    return (_ints(found[1][1], found[1][0]) if 1 in found else [], found.get(2, (2, b""))[1],
            found[3][1] if 3 in found and found[3][0] == 0 else 0)


def _held(occurrences: list[bytes], lines: dict) -> dict[bytes, bytes]:
    """The symbols defined in generated code, where the map holds nothing, that stand for another the component
    reads. Vue's tool 2.x returns each binding the template reads from the generated `setup` as a property of its
    own (`n: n as typeof n`), and the template reads that property (`__VLS_ctx.n`): such a property, followed on
    its line by a reference to a symbol whose definition the map holds, is that symbol. Vue's tool declares the
    compiler's macros (2.2.12 `declare const { defineProps, … }: typeof import('vue');`), each name a local defined
    at the range where the index references Vue's function: a definition sharing its range with a reference to one
    symbol not defined there, the chain the traversal follows from a shared range, is that symbol."""
    parsed = sorted((_parts(data) for data in occurrences), key=lambda part: part[0])
    defined = {symbol for values, symbol, roles in parsed if roles & 1 and mapped(lines, values) is not None}
    at = collections.defaultdict(list)
    for values, symbol, roles in parsed:
        at[tuple(values)].append((symbol, roles))
    held = {}
    for position, (values, symbol, roles) in enumerate(parsed):
        if not roles & 1 or mapped(lines, values) is not None:
            continue
        shared = {other for other, other_roles in at[tuple(values)] if not other_roles & 1} \
            - {other for other, other_roles in at[tuple(values)] if other_roles & 1}
        after = next((part for part in parsed[position + 1:] if part[0][0] == values[0]
                      and part[0][1] >= values[-1]), None) if len(values) == 3 else None
        if len(shared) == 1:
            held[symbol] = shared.pop()
        elif symbol.endswith(b":") and after is not None and not after[2] & 1 and after[1] in defined:
            held[symbol] = after[1]
    return held


def _occurrence(data: bytes, lines: dict, held: dict | None = None) -> bytes | None:
    """An occurrence with its range and enclosing range mapped; None when its range is not in the map. The
    document's module, which the indexer defines at its start with an empty range, is the component's, at its
    start: an import of the component references it. A property that holds a binding is the binding (`_held`)."""
    from code_graph import _fields, _ints
    fields = list(_fields(data))
    module = any(number == 2 and wire == 2 and value.endswith(b"/") for number, wire, value in fields)
    out, kept = bytearray(), None
    for number, wire, value in fields:
        if number in (1, 7):  # range, enclosing range (packed int32)
            values = _ints(value, wire)
            found = [0, 0, 0] if module and list(values) == [0, 0, 0] else mapped(lines, values)
            if number == 1:
                kept = found
            if found is not None:
                out += _field(number, 2, b"".join(_varint(item) for item in found))
        elif number == 2 and wire == 2 and held and value in held:
            out += _field(number, wire, held[value])
        else:
            out += _field(number, wire, value)
    return bytes(out) if kept is not None else None


def _document(data: bytes, maps: dict, sources: dict) -> bytes | None:
    """A document of the index; a generated one as its component's, None when its component has no map."""
    from code_graph import _fields
    fields = list(_fields(data))
    rel = next((value.decode("utf-8") for number, wire, value in fields if number == 1 and wire == 2), "")
    if rel not in maps:
        return data
    component, entry = maps[rel]
    lines = segments(entry, sources[component])
    held = _held([value for number, wire, value in fields if number == 2 and wire == 2], lines)
    out = bytearray(_field(1, 2, component.encode("utf-8")))
    for number, wire, value in fields:
        if number == 2 and wire == 2:
            occurrence = _occurrence(value, lines, held)
            if occurrence is not None:
                out += _field(2, 2, occurrence)
        elif number != 1:
            out += _field(number, wire, value)
    return bytes(out)


def _unbound(side: Path, maps: dict, sources: dict) -> None:
    """The checker's pass lines (`[path, line, column, kind, type]`, line 1-based) of a generated file, as its
    component's; one the map does not hold is left out."""
    kept, lines = [], {}
    for text in side.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(text)
            if row[0] not in maps:
                kept.append(text)
                continue
            component, entry = maps[row[0]]
            lines.setdefault(row[0], segments(entry, sources[component]))
            found = place(lines[row[0]].get(row[1] - 1, []), row[2])
        except (ValueError, IndexError, TypeError):  # a line the pass cut short says nothing
            continue
        if found is not None:
            kept.append(json.dumps([component, found[0] + 1, found[1], *row[3:]]))
    side.write_text("".join(line + "\n" for line in kept), encoding="utf-8")


def rewrite(index: Path, report: Path, project_dir: Path) -> dict:
    """Give each generated document of `index` to its component, in place, from the script's `report`, and so
    the checker's pass beside it (`<index>.unbound.jsonl`); returns the report (`{tools, components}`), `{}`
    without one."""
    from code_graph import _fields
    if not Path(report).is_file():
        return {}
    data = json.loads(Path(report).read_text(encoding="utf-8"))
    maps = {entry["generated"]: (rel, entry["map"]) for rel, entry in data.get("components", {}).items()
            if entry.get("generated")}
    sources = {rel: (Path(project_dir) / rel).read_text(encoding="utf-8", errors="replace")
               for rel, _entry in maps.values()}
    if maps and Path(index).is_file():
        out = bytearray()
        for number, wire, value in _fields(Path(index).read_bytes()):
            if number == 2 and wire == 2:
                value = _document(value, maps, sources)
            out += _field(number, wire, value)
        Path(index).write_bytes(bytes(out))
    side = Path(index).with_suffix(".unbound.jsonl")
    if maps and side.is_file():
        _unbound(side, maps, sources)
    return data
