"""Linguist's data files, read by a small standard-library reader, without the Ruby classifier or generated.rb.

The image build converts four files of the gem to JSON (`languages.yml`, `heuristics.yml`, `vendor.yml`,
`documentation.yml`); this reader applies them in Linguist's order: .gitattributes `linguist-language`, file name,
shebang, extension (the longest first), `<?xml`, then the heuristics of the extension's candidates. A file whose
candidates are still several after that is the classifier's (a Bayesian model over samples, Ruby only): it gets no
language here, and `_raw` counts it. Not read: modelines, man pages, the classifier, `generated.rb` (a generated
file is excluded only through `linguist-generated` in .gitattributes), and what Linguist computes from content
or mime types for `binary`, which is missing from the answer. Ruby regexps are translated to Python's `re`;
`_raw` counts those that do not compile.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from _lang import DATA, canon, files, read_text, table

VERSION = "9.7.0 data"

_POSIX = {"alpha": "a-zA-Z", "digit": "0-9", "alnum": "a-zA-Z0-9", "upper": "A-Z", "lower": "a-z",
          "space": r"\s", "punct": r"!-/:-@\[-`{-~", "word": r"\w", "xdigit": "0-9a-fA-F", "blank": r" \t"}


def rx(pattern: str):
    """A Ruby (Onigmo) regexp as a Python one; None when Python cannot compile the translation."""
    p = pattern
    p = re.sub(r"\[:(\w+):\]", lambda m: _POSIX.get(m.group(1), m.group(0)), p)
    p = p.replace(r"\h", "[0-9a-fA-F]").replace(r"\H", "[^0-9a-fA-F]").replace(r"\z", r"\Z")
    # (?<name>...) is a named group in Ruby; (?<= and (?<! are lookbehinds in both.
    p = re.sub(r"\(\?<(?![=!])([A-Za-z_]\w*)>", r"(?P<\1>", p)
    p = re.sub(r"\\k<(\w+)>", r"(?P=\1)", p)
    p = re.sub(r"\(\?([a-z]*)m([a-z]*)([:)])", lambda m: f"(?{m.group(1)}s{m.group(2)}{m.group(3)}", p)
    try:
        return re.compile(p, re.MULTILINE)
    except (re.error, RecursionError):
        return None


def glob_regex(pattern: str, folder: str):
    """A .gitattributes pattern as a regexp over repository paths, anchored at the folder of its file."""
    anchored = "/" in pattern.rstrip("/")
    pattern = pattern.lstrip("/")
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out.append("/.*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j < 0:
                out.append(re.escape(c))
                i += 1
            else:
                out.append("[" + pattern[i + 1:j].replace("\\", "\\\\") + "]")
                i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    body = "".join(out)
    prefix = (re.escape(folder) + "/") if folder else ""
    return re.compile(("^" + prefix + body + "$") if anchored else ("^" + prefix + "(?:.*/)?" + body + "$"))


class Reader:
    def __init__(self, root: str | Path):
        self.root = Path(root)

        def load(name):
            return json.loads((DATA / name).read_text(encoding="utf-8"))

        self.languages = table()
        heuristics = load("heuristics.json")
        self.rules = heuristics["disambiguations"]
        self.named = heuristics.get("named_patterns", {})
        self.failed = 0
        self._rx: dict[str, object] = {}
        self.vendor = [c for c in (self._compile(p) for p in load("vendor.json")) if c is not None]
        self.documentation = [c for c in (self._compile(p) for p in load("documentation.json")) if c is not None]
        self.by_filename, self.by_ext, self.by_interpreter = {}, {}, {}
        for name, entry in self.languages.items():
            for f in entry.get("filenames") or []:
                self.by_filename.setdefault(f, []).append(name)
            for e in entry.get("extensions") or []:
                self.by_ext.setdefault(e.lower(), []).append(name)
            for i in entry.get("interpreters") or []:
                self.by_interpreter.setdefault(i, []).append(name)
        self.attr_files = self._attribute_files()
        self.ambiguous: list[str] = []

    # ---- regexps

    def _compile(self, pattern: str):
        if pattern not in self._rx:
            compiled = rx(pattern)
            self.failed += compiled is None
            self._rx[pattern] = compiled
        return self._rx[pattern]

    def _search(self, pattern: str, data: str) -> bool:
        compiled = self._compile(pattern)
        return bool(compiled and compiled.search(data))

    # ---- .gitattributes

    def _attribute_files(self) -> list[tuple[str, list]]:
        found = []
        for rel in files(self.root):
            if Path(rel).name == ".gitattributes":
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
                folder = Path(rel).parent.as_posix()
                folder = "" if folder == "." else folder
                lines = []
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    lines.append((glob_regex(parts[0], folder), parts[1:]))
                found.append((folder, lines))
        found.sort(key=lambda f: (f[0].count("/") + 1) if f[0] else 0)
        return found

    def attributes(self, path: str) -> dict:
        out: dict = {}
        for folder, lines in self.attr_files:
            if folder and not path.startswith(folder + "/"):
                continue
            for regex, attrs in lines:
                if regex.match(path):
                    for attr in attrs:
                        if attr.startswith("-"):
                            out[attr[1:]] = False
                        elif attr.startswith("!"):
                            out.pop(attr[1:], None)
                        elif "=" in attr:
                            key, value = attr.split("=", 1)
                            out[key] = value
                        else:
                            out[attr] = True
        return out

    # ---- detection

    def _heuristics(self, path: str, candidates: list[str], data: str) -> list[str]:
        lower = path.lower()
        for entry in self.rules:
            keys = entry.get("extensions") or []
            if not any(lower.endswith(k) if k.startswith(".") else k in candidates for k in keys):
                continue
            for rule in entry["rules"]:
                if self._rule(rule, data):
                    found = rule["language"] if isinstance(rule["language"], list) else [rule["language"]]
                    if all(f in candidates for f in found):
                        return found
                    break
        return candidates

    def _rule(self, rule: dict, data: str) -> bool:
        if "and" in rule:
            return all(self._rule(r, data) for r in rule["and"])
        ok = True
        if "pattern" in rule:
            patterns = rule["pattern"] if isinstance(rule["pattern"], list) else [rule["pattern"]]
            ok = ok and any(self._search(p, data) for p in patterns)
        if "named_pattern" in rule:
            named = self.named.get(rule["named_pattern"])
            named = named if isinstance(named, list) else [named]
            ok = ok and any(self._search(p, data) for p in named if p)
        if "negative_pattern" in rule:
            patterns = rule["negative_pattern"]
            patterns = patterns if isinstance(patterns, list) else [patterns]
            ok = ok and not any(self._search(p, data) for p in patterns)
        return ok

    def language(self, path: str, data: str | None, attrs: dict) -> str | None:
        override = attrs.get("linguist-language")
        if isinstance(override, str):
            return canon(override)
        base = path.rsplit("/", 1)[-1]
        candidates: list[str] = []
        found = self.by_filename.get(base, [])
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            candidates = found
        if data and data.startswith("#!"):
            words = data.split("\n", 1)[0][2:].split()
            if words:
                script = words[0].rsplit("/", 1)[-1]
                if script == "env":
                    rest = [w for w in words[1:] if not w.startswith("-") and "=" not in w]
                    script = rest[0].rsplit("/", 1)[-1] if rest else ""
                script = re.sub(r"(?:\d+\.)+\d+$", "", script)
                shebang = self.by_interpreter.get(script, [])
                if len(shebang) == 1:
                    return shebang[0]
                if len(shebang) > 1:
                    candidates = shebang
        lower = base.lower()
        by_ext: list[str] = []
        for i, ch in enumerate(lower):
            if ch == "." and lower[i:] in self.by_ext:
                by_ext = self.by_ext[lower[i:]]
                break
        if by_ext:
            candidates = [c for c in candidates if c in by_ext] if candidates else list(by_ext)
            if len(candidates) == 1:
                return candidates[0]
        if not candidates and data and data.lstrip().startswith("<?xml"):
            return "XML"
        if len(candidates) > 1 and data is not None:
            candidates = self._heuristics(path, candidates, data)
            if len(candidates) == 1:
                return candidates[0]
        if len(candidates) > 1:
            self.ambiguous.append(f"{path}: {','.join(sorted(candidates)[:4])}")
        return None

    @staticmethod
    def _flag(value) -> bool | None:
        if value is None:
            return None
        return value is True or value == "true"

    def kind(self, path: str, attrs: dict) -> str | None:
        """The reason a file is left out, from the attributes first and the path regexps after."""
        for attr, why, regexps in (("linguist-vendored", "vendored", self.vendor),
                                   ("linguist-generated", "generated", []),
                                   ("linguist-documentation", "documentation", self.documentation)):
            forced = self._flag(attrs.get(attr))
            if forced is None:
                forced = any(r.search(path) for r in regexps)
            if forced:
                return why
        return None


def run(fixture_dir, work_dir) -> dict:
    reader = Reader(fixture_dir)
    languages, excluded, nolang = [], [], 0
    for path in files(fixture_dir):
        attrs = reader.attributes(path)
        why = reader.kind(path, attrs)
        if why:
            excluded.append({"path": path, "why": why})
            continue
        language = reader.language(path, read_text(fixture_dir, path), attrs)
        if language:
            languages.append({"path": path, "language": language})
        else:
            nolang += 1
    return {"languages": languages, "excluded": excluded,
            "_raw": {"regexps_not_translated": reader.failed, "ambiguous_left_to_the_classifier": reader.ambiguous[:10],
                     "ambiguous_count": len(reader.ambiguous), "files_without_language": nolang}}
