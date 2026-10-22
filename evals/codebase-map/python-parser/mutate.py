"""Work-in-progress corpus: realistic syntax errors injected into valid real files.

The Codebase Map runs on uncommitted trees, so a file mid-edit is a normal input,
not an exotic one. Each mutation reproduces one way a file is broken while
someone is typing, and records the ground truth: the definitions the original
file declared, with line numbers mapped onto the mutated file.

A mutation is only counted if the reference parser rejects the mutated file.
One that still parses was ineffective and is excluded from tolerance figures,
counted separately, never silently.

Selection is deterministic (seeded by path and mutation name), so a rerun on the
same corpus produces the same files.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

MUTATIONS = (
    "unclosed-paren",
    "missing-colon",
    "truncate-mid-body",
    "merge-conflict",
    "bad-indent",
    "unterminated-string",
)

SIMPLE_STRING = re.compile(r"(['\"])[^'\"\\\n]{1,40}\1")


def _rng(path: str, mutation: str, seed: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}|{path}|{mutation}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def _code_part(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _bodies(defs, minimum):
    return [d for d in defs if d["k"] != "type" and d["e"] - d["l"] >= minimum]


def mutate(text: str, defs: list, mutation: str, rng: random.Random):
    """Return (mutated_text, shift, limit, where) or None when not applicable.

    shift: (k, at, after) maps an original line l to l if l < k, l + at if
           l == k, l + after if l > k.
    limit: last original line still present, for truncation.
    """
    lines = text.split("\n")
    shift = None
    limit = None

    if mutation == "unclosed-paren":
        candidates = [i for i, line in enumerate(lines)
                      if _code_part(line).endswith(")") and "(" in _code_part(line)]
        if not candidates:
            return None
        i = rng.choice(candidates)
        code = _code_part(lines[i])
        lines[i] = code[:-1] + lines[i][len(code):]
        where = i + 1

    elif mutation == "missing-colon":
        headers = []
        for d in defs:
            if d["k"] == "type":
                continue
            for j in range(d["l"] - 1, min(len(lines), d["l"] + 15)):
                if _code_part(lines[j]).endswith(":"):
                    headers.append(j)
                    break
        if not headers:
            return None
        j = rng.choice(headers)
        code = _code_part(lines[j])
        lines[j] = code[:-1] + lines[j][len(code):]
        where = j + 1

    elif mutation == "truncate-mid-body":
        bodies = _bodies(defs, 4)
        if not bodies:
            return None
        d = rng.choice(bodies)
        cut = rng.randint(d["l"] + 1, d["e"] - 1)
        lines = lines[:cut]
        last = lines[-1]
        stripped = last.strip()
        if len(stripped) > 4:
            lines[-1] = last[: len(last) - len(stripped) // 2]
        limit = cut
        where = cut

    elif mutation == "merge-conflict":
        bodies = _bodies(defs, 2)
        if not bodies:
            return None
        d = rng.choice(bodies)
        k = rng.randint(d["l"] + 1, d["e"])
        i = k - 1
        lines = lines[:i] + ["<<<<<<< HEAD", lines[i], "=======", lines[i],
                             ">>>>>>> feature"] + lines[i + 1:]
        shift = (k, 1, 4)
        where = k

    elif mutation == "bad-indent":
        bodies = _bodies(defs, 3)
        candidates = []
        for d in bodies:
            for j in range(d["l"] + 1, d["e"]):
                line = lines[j - 1]
                previous = _code_part(lines[j - 2]) if j >= 2 else ""
                if (line.strip() and not line.lstrip().startswith("#")
                        and previous and not previous.endswith((":", ",", "(", "[", "{", "\\"))):
                    candidates.append(j - 1)
        if not candidates:
            return None
        i = rng.choice(candidates)
        lines[i] = "   " + lines[i]
        where = i + 1

    elif mutation == "unterminated-string":
        candidates = [i for i, line in enumerate(lines)
                      if not line.lstrip().startswith("#") and SIMPLE_STRING.search(_code_part(line))]
        if not candidates:
            return None
        i = rng.choice(candidates)
        match = SIMPLE_STRING.search(_code_part(lines[i]))
        end = match.end() - 1
        lines[i] = lines[i][:end] + lines[i][end + 1:]
        where = i + 1

    else:
        raise ValueError(mutation)

    return "\n".join(lines), shift, limit, where


def map_line(line: int, shift) -> int:
    if shift is None:
        return line
    k, at, after = shift
    if line < k:
        return line
    if line == k:
        return line + at
    return line + after


def generate(ast_records: dict, out_dir: Path, per_corpus: int, seed: str) -> Path:
    """ast_records: {corpus: {path: record}} from the reference interpreter."""
    files_dir = out_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    truth_rows = []
    listing = []
    for corpus, records in sorted(ast_records.items()):
        eligible = sorted(path for path, rec in records.items()
                          if rec.get("ok") and len(rec.get("defs", [])) >= 5
                          and Path(path).stat().st_size < 200_000)
        picker = random.Random(f"{seed}|{corpus}")
        chosen = eligible if len(eligible) <= per_corpus else picker.sample(eligible, per_corpus)
        for index, path in enumerate(sorted(chosen)):
            try:
                original = Path(path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            defs = records[path]["defs"]
            for mutation in MUTATIONS:
                result = mutate(original, defs, mutation, _rng(path, mutation, seed))
                if result is None:
                    continue
                mutated, shift, limit, where = result
                target = files_dir / f"{corpus}-{index:04d}-{mutation}.py"
                target.write_text(mutated, encoding="utf-8")
                truth = [{"q": d["q"], "k": d["k"], "l": map_line(d["l"], shift)}
                         for d in defs if limit is None or d["l"] <= limit]
                truth_rows.append({"f": str(target), "source": path, "corpus": corpus,
                                   "mutation": mutation, "where": where, "truth": truth})
                listing.append(str(target))
    (out_dir / "truth.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in truth_rows), encoding="utf-8")
    list_path = out_dir / "list.txt"
    list_path.write_text("\n".join(listing) + "\n", encoding="utf-8")
    return list_path
