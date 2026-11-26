"""What two runs of `measure_links.py` differ in, for the stores: the links and gaps one gained or lost, and each new store
link's key checked against the source (data only, no Modal; the project's source is read here, never copied).

    python benchmarks/phazly-flow/check_store_keys.py --before before-full-links.json.gz --after final-full-links.json.gz \\
        --source SOURCE-DIR [--sample 10 --seed 11]

A new `scrive` or `legge` link whose call is made on `store[INDEX]` is checked by reading the call's tree (tree-sitter,
as the links do): INDEX a text is the key; INDEX a name is the text the same file assigns to it once; any other INDEX, a
name the file does not assign, or a link whose call is not on `store[...]` (a handle assigned before) is not checked and
is listed, never counted as right. The checker shares the grammars with the links and nothing else: it does not use the
snapshot, so it does not stand on what it checks.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import random
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import entries  # noqa: E402
import registry_hosts  # noqa: E402

CALLS = ("call", "call_expression")
SUBSCRIPTS = ("subscript", "subscript_expression")
WRAPPERS = ("parenthesized_expression", "await", "await_expression", "non_null_expression")


def load(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def edge_key(edge: dict) -> tuple:
    return edge["from"], edge["to"], edge["type"], edge["site"]


def gap_key(gap: dict) -> tuple:
    return gap["site"], gap["symbol"], gap["reason"]


def unwrapped(node):
    while node is not None and node.type in WRAPPERS:
        node = next(iter(node.named_children), None)
    return node


class Source:
    """The project's files, parsed once, and the text a name is assigned in one."""

    def __init__(self, root: Path):
        self.root, self.files = root, {}

    def tree(self, file: str):
        if file not in self.files:
            path = self.root / file
            grammar = registry_hosts.GRAMMARS.get(path.suffix)
            data = path.read_bytes() if path.is_file() and grammar else b""
            self.files[file] = (data, grammar, entries._parse(data, grammar) if data else None)
        return self.files[file]

    def line(self, site: str) -> str:
        file, _, number = site.rpartition(":")
        try:
            return (self.root / file).read_text(encoding="utf-8").splitlines()[int(number) - 1].strip()[:110]
        except (OSError, IndexError):
            return ""

    def index_of(self, file: str, line: int):
        """The index node of the `store[INDEX]` a call that starts on `line` is made on, with the file's data and grammar."""
        data, grammar, root = self.tree(file)
        if root is None:
            return None
        stack, found = [root], None
        while stack:
            node = stack.pop()
            stack.extend(node.named_children)
            callee = node.child_by_field_name("function") if node.type in CALLS else None
            receiver = unwrapped(callee.child_by_field_name("object")) if callee is not None else None
            if receiver is not None and receiver.type in SUBSCRIPTS and callee.start_point[0] + 1 == line:
                found = receiver.child_by_field_name("index") or receiver.child_by_field_name("subscript")
                break
        return (found, data, grammar, root) if found is not None else None

    def text_of(self, file: str, line: int) -> tuple[str | None, str]:
        """`(text, how)`: the text the index of the call's receiver stands for, and in which form it is written."""
        read = self.index_of(file, line)
        if read is None:
            return None, "not on store[...]"
        node, data, grammar, root = read
        node = unwrapped(node)
        text = entries._string(node, data, grammar, exact=True)
        if text is not None:
            return text, "text"
        if node.type != "identifier":
            return None, entries._text(data, node)[:40]
        name = entries._text(data, node)
        values = {entries._string(value, data, grammar, exact=True)
                  for target, _, value in entries._assignments({}, file, data, root) if target == name}
        values.discard(None)
        return (next(iter(values)), "name in the file") if len(values) == 1 else (None, f"name {name} not given one text in the file")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    before, after, source = load(args.before), load(args.after), Source(args.source)
    old = {edge_key(e) for e in before["edges"]}
    new_edges = [e for e in after["edges"] if edge_key(e) not in old and e["type"] in ("scrive", "legge")]
    kept = {edge_key(e) for e in after["edges"]}
    lost = [k for k in old if k not in kept and k[2] in ("scrive", "legge")]
    old_gaps = {gap_key(g) for g in before["gaps"]}
    new_gaps = sorted({gap_key(g) for g in after["gaps"]} - old_gaps)
    lost_gaps = sorted(old_gaps - {gap_key(g) for g in after["gaps"]})
    print(f"store links: new {len(new_edges)} ({dict(collections.Counter(e['type'] for e in new_edges))}), lost {len(lost)}")
    print("stores:", len(before["stores"]), "->", len(after["stores"]))
    print("gaps: new", len(new_gaps), "lost", len(lost_gaps))
    print("  new, by cause:", dict(collections.Counter(g[2].split(": ", 1)[-1][:110] for g in new_gaps).most_common()))
    print("  lost, by cause:", dict(collections.Counter(g[2][:110] for g in lost_gaps).most_common(8)))
    rows, outcome = [], collections.Counter()
    for edge in new_edges:
        key = (edge["to"] if edge["type"] == "scrive" else edge["from"]).split("/", 1)[1]
        file, _, line = edge["site"].rpartition(":")
        text, how = source.text_of(file, int(line))
        verdict = "not checked" if text is None else "right" if text == key else "WRONG"
        outcome[verdict] += 1
        outcome[f"form: {how if text is not None else 'other'}"] += 1
        rows.append((verdict, edge["type"], key, edge["site"], how, text))
    print("keys:", dict(outcome))
    for row in rows:
        if row[0] != "right":
            print("  ", *row[:5])
    print("sample:")
    for row in random.Random(args.seed).sample(rows, min(args.sample, len(rows))):
        print(f"  {row[0]:11} {row[1]:7} {row[2]:32} {row[3]}  [{row[4]}]  {source.line(row[3])}")
    return 1 if outcome["WRONG"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
