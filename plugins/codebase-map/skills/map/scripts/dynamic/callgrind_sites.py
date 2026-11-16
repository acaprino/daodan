"""What Valgrind's Callgrind saw, as call sites and the functions entered from them: run by Python in the container,
after the tests, over Callgrind's outputs and the objects they name, never on the host.

    python3 -I callgrind_sites.py <pyelftools wheel> <callgrind folder> <copy root> <out.json>

Callgrind (`--dump-instr=yes`) writes each call it saw under the caller's object (`ob=`), file and function, as a
`calls=` line (the count, the address and line the callee was entered at) and the cost line after it (the address
of the call instruction): valgrind.org/docs/manual/cl-format.html. `cob=` and `cfi=` name the callee's object and
file where they differ from the caller's. The addresses are where the process had the object mapped: the load
address of an object is the page-aligned one that makes the addresses entered in it its own function symbols
(`.symtab`, `.dynsym`), and its DWARF line table (pyelftools, public domain) then gives an address its file, line
and column. Callgrind's own lines carry no column.

Written: `{"processes", "calls", "unread"}`, a call `[file, line, column, callee file, line, column, callee,
callee object, count]` per call site and callee, lines and columns from 1 as DWARF numbers them, the column 0
where none is given. A call is kept when its site is in a file under the copy root; a callee there is placed by
its object's line table at the address it was entered, any other by Callgrind's file and line. `unread` counts
the calls left out by cause.
"""
from __future__ import annotations

import bisect
import collections
import json
import os
import sys

PAGE = 4096
OUTSIDE, NO_LOAD, NO_LINE = "made outside the project", "no load address of the object", "no line in the object's DWARF"
SHARED = {"ob": "ob", "cob": "ob", "fl": "fl", "fi": "fl", "fe": "fl", "cfi": "fl", "cfl": "fl", "fn": "fn",
          "cfn": "fn"}  # the name each specification compresses into


def _number(text: str, last: int) -> int:
    """A subposition: absolute (`0x..` or decimal), relative to the last cost line's (`+n`, `-n`), or the same."""
    if text == "*":
        return last
    if text[0] in "+-":
        return last + int(text, 0)
    return int(text, 0)


def parse(text: str) -> list[dict]:
    """The calls of one Callgrind output: `{object, file, function, at, line, callee_object, callee_file, callee,
    entered, entered_line, count}`, addresses as numbers (None without `instr` positions)."""
    names: dict = {"ob": {}, "fl": {}, "fn": {}}
    state = {"ob": "", "fl": "", "file": "", "fn": ""}
    target: dict = {}
    positions, last, calls, pending = ["line"], [0, 0], [], None

    def name(kind: str, value: str) -> str:
        value = value.strip()
        if value.startswith("("):
            number, _, given = value[1:].partition(")")
            table = names[SHARED[kind]]
            if given.strip():
                table[number] = given.strip()
            return table.get(number, "")
        return value

    def position(fields: list[str], cost: bool = True) -> dict:
        out = {}
        for index, kind in enumerate(positions):
            if index < len(fields):
                out[kind] = _number(fields[index], last[index])
                if cost:  # a relative subposition is based on the last cost line's
                    last[index] = out[kind]
        return out

    for line in text.splitlines():
        if pending is not None:  # the cost line after `calls=`: where the call is
            at = position(line.split())
            calls.append({"object": state["ob"], "file": state["file"], "function": state["fn"],
                          "at": at.get("instr"), "line": at.get("line", 0), **pending})
            pending = None
            continue
        if line.startswith("positions:"):
            positions = line.split()[1:] or ["line"]
            last = [0] * len(positions)
            continue
        key, equals, value = line.partition("=")
        if not equals:
            if line[:1].isdigit() or line[:1] in "+-*":
                position(line.split())
            continue
        if key == "calls":
            count, *fields = value.split()
            entered = position(fields, cost=False)
            pending = {"callee_object": target.pop("cob", state["ob"]),
                       "callee_file": target.pop("cfi", state["fl"]), "callee": target.pop("cfn", ""),
                       "entered": entered.get("instr"), "entered_line": entered.get("line", 0), "count": int(count)}
        elif key in ("ob", "fl", "fi", "fe", "fn"):
            given = name(key, value)
            if key == "fl":
                state["fl"] = state["file"] = given
            elif key in ("fi", "fe"):
                state["file"] = given
            else:
                state[key] = given
                if key == "fn":
                    state["file"] = state["fl"]
        elif key in SHARED:
            target["cfi" if key == "cfl" else key] = name(key, value)
    return calls


def load_address(entered: set[int], values: set[int]) -> int | None:
    """The page-aligned load address that makes the most `entered` addresses function symbols of the object
    (`values`), None where no address or more than one does."""
    if not entered or not values:
        return None
    first = min(entered)
    counted = collections.Counter()
    for value in values:
        base = first - value
        if base >= 0 and base % PAGE == 0:
            counted[base] = sum(1 for address in entered if address - base in values)
    best = counted.most_common(2)
    if not best or (len(best) > 1 and best[1][1] == best[0][1]):
        return None
    return best[0][0]


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def document(texts: list[str], root: str, objects) -> dict:
    """What `texts`, Callgrind's outputs, say of the copy under `root`; `objects(path)` gives an object's function
    symbol values and its line lookup (offsets -> {offset: (file, line, column)}), or None."""
    calls = [call for text in texts for call in parse(text)]
    unread, kept = collections.Counter(), []
    for call in calls:
        if not _inside(call["file"], root):
            unread[OUTSIDE] += 1
        elif call["at"] is None:
            unread[NO_LINE] += 1
        else:
            kept.append(call)
    entered = collections.defaultdict(set)
    for call in calls:
        if call["entered"] is not None:
            entered[call["callee_object"]].add(call["entered"])
    wanted = collections.defaultdict(set)
    for call in kept:
        wanted[call["object"]].add(call["at"])
        if _inside(call["callee_file"], root) and call["entered"] is not None:
            wanted[call["callee_object"]].add(call["entered"])
    found = {}
    for path, addresses in sorted(wanted.items()):
        opened = objects(path)
        base = load_address(entered.get(path, set()), opened[0]) if opened else None
        if base is not None:
            rows = opened[1](sorted(address - base for address in addresses))
            found.update({(path, address): rows.get(address - base) for address in addresses})
        else:
            found.update({(path, address): NO_LOAD for address in addresses})
    out = collections.Counter()
    for call in kept:
        site = found[(call["object"], call["at"])]
        callee = (call["callee_file"], call["entered_line"], 0)
        if _inside(call["callee_file"], root):
            callee = found.get((call["callee_object"], call["entered"])) if call["entered"] is not None else None
        if NO_LOAD in (site, callee):
            unread[NO_LOAD] += 1
        elif site is None or callee is None:
            unread[NO_LINE] += 1
        else:
            out[(*site, *callee, call["callee"], call["callee_object"])] += call["count"]
    return {"processes": len(texts), "calls": [[*key, count] for key, count in sorted(out.items())],
            "unread": dict(sorted(unread.items()))}


def _elf(path: str):
    """`(function symbol values, lines)` of the ELF object at `path` with pyelftools, None where it is not one."""
    from elftools.common.exceptions import ELFError
    from elftools.elf.elffile import ELFFile
    from elftools.elf.sections import SymbolTableSection
    try:
        stream = open(path, "rb")
        elf = ELFFile(stream)
    except (OSError, ELFError):
        return None
    values = {symbol["st_value"] for section in elf.iter_sections() if isinstance(section, SymbolTableSection)
              for symbol in section.iter_symbols()
              if symbol["st_info"]["type"] == "STT_FUNC" and symbol["st_value"]}

    def lines(offsets: list[int]) -> dict:
        found: dict = {}
        if not offsets or not elf.has_dwarf_info():
            return found
        dwarf = elf.get_dwarf_info()
        for unit in dwarf.iter_CUs():
            spans = _spans(dwarf, unit)
            if spans is not None and not any(bisect.bisect_left(offsets, low) < bisect.bisect_left(offsets, high)
                                             for low, high in spans):
                continue
            program = dwarf.line_program_for_CU(unit)
            if program is None:
                continue
            names, previous = _files(program, unit), None
            for entry in program.get_entries():
                row = entry.state
                if row is None:
                    continue
                if previous is not None and not previous.end_sequence:
                    index = bisect.bisect_left(offsets, previous.address)
                    while index < len(offsets) and offsets[index] < row.address:
                        found[offsets[index]] = (names(previous.file), previous.line, previous.column)
                        index += 1
                previous = row
        return found

    return values, lines


def _spans(dwarf, unit) -> list[tuple[int, int]] | None:
    """The address ranges a compilation unit covers, None where its top entry does not say them simply."""
    attributes = unit.get_top_DIE().attributes
    try:
        if "DW_AT_ranges" in attributes:
            low = attributes["DW_AT_low_pc"].value if "DW_AT_low_pc" in attributes else 0
            spans, base = [], low
            for item in dwarf.range_lists().get_range_list_at_offset(attributes["DW_AT_ranges"].value, cu=unit):
                if hasattr(item, "base_address"):
                    base = item.base_address
                else:
                    shift = 0 if getattr(item, "is_absolute", False) else base
                    spans.append((item.begin_offset + shift, item.end_offset + shift))
            return spans
        if "DW_AT_low_pc" in attributes and "DW_AT_high_pc" in attributes:
            low, high = attributes["DW_AT_low_pc"].value, attributes["DW_AT_high_pc"]
            return [(low, high.value if high.form == "DW_FORM_addr" else low + high.value)]
    except Exception:  # a form this version of pyelftools reads otherwise: the whole unit is read
        return None
    return None


def _files(program, unit):
    """The path of a line program's file index, joined to its directory and the unit's compilation directory."""
    version, entries, folders = program["version"], program["file_entry"], program["include_directory"]
    top = unit.get_top_DIE().attributes
    compiled = top["DW_AT_comp_dir"].value.decode("utf-8", "replace") if "DW_AT_comp_dir" in top else ""
    cache: dict = {}

    def text(value) -> str:
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)

    def name(index: int) -> str:
        if index not in cache:
            position = index if version >= 5 else index - 1
            if not 0 <= position < len(entries):
                cache[index] = ""
                return ""
            entry = entries[position]
            folder = entry.dir_index if version >= 5 else entry.dir_index - 1
            directory = text(folders[folder]) if 0 <= folder < len(folders) else compiled
            path = text(entry.name)
            path = path if path.startswith("/") else os.path.join(directory, path)
            cache[index] = os.path.normpath(path if path.startswith("/") else os.path.join(compiled, path))
        return cache[index]

    return name


def main(argv: list[str]) -> int:
    wheel, folder, root, out = argv
    sys.path.insert(0, wheel)  # pyelftools is pure Python: its wheel imports as it is
    texts = []
    for name in sorted(os.listdir(folder)):
        if name.startswith("callgrind.out."):
            with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as stream:
                texts.append(stream.read())
    with open(out, "w", encoding="utf-8") as stream:
        json.dump(document(texts, root, _elf), stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
