#!/usr/bin/env python3
"""The entries a reference lists, against the candidates of the readers, before any new reader (plan, Task C4.1).

    python entries.py measure CANDIDATES.json EXPECTED.json FILES.txt

CANDIDATES.json is what `modal_map.py::entries` writes for a case: the candidates of `daodan/core/entries.py` and
the calls of the links, `[from, to]`. The rule: an entry of the reference is found by a reader when one of the
reader's candidates is a symbol of a file of the entry's node, the node's members expanded on the snapshot's files
(FILES.txt) as `score.py system` does. An entry whose node is not internal, or holds more than WIDE files, is counted
apart: a candidate would sit there by chance. A candidate in no file of any internal entry node is no entry. A file
of the snapshot that no candidate holds or reaches through the calls is unreached, counted by its folder.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference  # noqa: E402
import score  # noqa: E402
import traces  # noqa: E402

WIDE = 12  # the files of a node past which a candidate in it says nothing


def _file(symbol: str) -> str:
    return symbol.split("::")[0]


def _symbol(candidate: dict) -> str:
    """A candidate's symbol; a control the browser found (reader `observed`) has none, only the place of its
    handler (`at`: file, line, name)."""
    if "symbol" in candidate:
        return candidate["symbol"]
    at = candidate["at"]
    return f"{at['file']}::{at['name']}"


def measure(candidates: dict, expected: dict, files: list[str]) -> dict:
    """Per reader and per entry kind, the entries found over those counted; the candidates that are no entry; the
    entries counted apart, per kind; the files no candidate reaches, per folder."""
    units, _ = score._units(expected, files)
    held = {score._key(node["name"]): {u.partition("::")[0] for u in units(node) if not u.startswith("store:")}
            for node in expected["nodes"] if node.get("position", "internal") == "internal"}
    listed = [(item["kind"], held.get(score._key(item["node"])))
              for flow in expected.get("flows", []) for item in flow.get("entries", [])]
    counted = [(kind, have) for kind, have in listed if have is not None and len(have) <= WIDE]
    apart = Counter(kind for kind, have in listed if have is None or len(have) > WIDE)
    kinds = [k for k in reference.ENTRY_KINDS if k in {kind for kind, _ in counted}]
    kinds += sorted({kind for kind, _ in counted} - set(kinds))
    entry_files = set().union(*(have for _, have in listed if have is not None))
    readers = []
    for reader in dict.fromkeys(c["reader"] for c in candidates["candidates"]):
        theirs = [c for c in candidates["candidates"] if c["reader"] == reader]
        mine = {_file(_symbol(c)) for c in theirs}
        readers.append({"reader": reader, "candidates": len(theirs),
                        "not_entries": sum(_file(_symbol(c)) not in entry_files for c in theirs),
                        "by_kind": {kind: {"found": sum(k == kind and bool(have & mine) for k, have in counted),
                                           "of": sum(k == kind for k, _ in counted)} for kind in kinds}})
    out = {"<candidates>": [(_symbol(c),) for c in candidates["candidates"]]}
    for source, target in candidates.get("calls", []):
        out.setdefault(source, []).append((target,))
    reached = {_file(symbol) for symbol in traces.reached(out, "<candidates>")}
    missing = [path for path in files if path not in reached]
    return {"readers": readers, "apart": dict(sorted(apart.items())),
            "unreached": {"files": len(missing), "of": len(files),
                          "by_folder": dict(Counter(path.rpartition("/")[0] or "." for path in missing).most_common())}}


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[1] != "measure":
        print(__doc__)
        return 2
    candidates, expected = (json.loads(Path(path).read_text(encoding="utf-8")) for path in argv[2:4])
    files = [line.strip().replace("\\", "/") for line in Path(argv[4]).read_text(encoding="utf-8").splitlines()]
    print(json.dumps(measure(candidates, expected, [f for f in files if f]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
