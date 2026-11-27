"""The language of a file: its extension, then the rules of that extension in their order, then the extension's own
language, the declared fallback.

Three fixed steps over three registers, all data (`daodan/data/`): `file-formats.json` (the extensions Daodan reads
and their language), `linguist-catalog.json` (what Linguist calls each, the base this module started from) and
`language-rules.toml` (the rules a literal comparison can ask). A rule that a literal comparison cannot ask is a
class in `rules/`. Rules answer in Linguist's names; the register joins a name to Daodan's language, and a name it
joins to none is a file the snapshot does not read (`language` None).

A rule outside its schema does not load, and the error names its field. `problems()` says what the samples of the
rules and the catalogue disagree on.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import file_formats

from .rules import CLASSES

RULES_PATH = file_formats.PATH.with_name("language-rules.toml")
TESTS = ("starts-with", "contains")
FIELDS = {"id": str, "extensions": list, "language": str, "test": str, "texts": list, "why": str, "source": str,
          "yes": list, "no": list}
OPTIONAL = {"ignore-case": bool}
# The bytes of a text a rule reads: `source_files.MAX_PARSE_BYTES` (a test holds them equal; that module imports this
# package). Above it the snapshot parses no file, so no rule reads its text, and a rule costs in line with this bound.
MAX_CHARS = 2_000_000
EXTENSION = "extension"  # `decided_by` when no rule answered
# Linguist's name to Daodan's language; a name absent here is not read.
LANGUAGE_OF = {name: language for language, names in file_formats.LINGUIST_NAMES.items() for name in names}


@dataclass(frozen=True)
class Detection:
    language: str | None  # Daodan's language; None for a file the snapshot does not read
    decided_by: str  # `EXTENSION`, or the id of the rule that answered


class LiteralRule:
    """A rule of `language-rules.toml`: one comparison on literal words."""

    def __init__(self, card: dict):
        name = card.get("id") if isinstance(card.get("id"), str) else "a rule without an id"
        for field in card:
            if field not in FIELDS and field not in OPTIONAL:
                raise ValueError(f"{name}: unknown field `{field}`")
        for field, kind in FIELDS.items():
            if not isinstance(card.get(field), kind) or not card[field]:
                raise ValueError(f"{name}: `{field}` is missing, empty or not a {kind.__name__}")
        for field, kind in OPTIONAL.items():
            if field in card and not isinstance(card[field], kind):
                raise ValueError(f"{name}: `{field}` is not a {kind.__name__}")
        for field in ("extensions", "texts", "yes", "no"):
            if not all(isinstance(item, str) and item for item in card[field]):
                raise ValueError(f"{name}: `{field}` holds something that is not a text")
        if card["test"] not in TESTS:
            raise ValueError(f"{name}: `test` is not one of {', '.join(TESTS)}")
        unknown = [extension for extension in card["extensions"] if extension not in file_formats.SOURCES]
        if unknown:
            raise ValueError(f"{name}: `extensions` names {', '.join(unknown)}, which file-formats.json does not read")
        self.id, self.extensions, self.why, self.source = name, tuple(card["extensions"]), card["why"], card["source"]
        self.languages = (card["language"],)
        self.yes, self.no = tuple((text, card["language"]) for text in card["yes"]), tuple(card["no"])
        self._starts, self._fold = card["test"] == "starts-with", card.get("ignore-case", False)
        self._texts = tuple(text.lower() if self._fold else text for text in card["texts"])

    def decide(self, text: str) -> str | None:
        if self._fold:
            text = text.lower()
        found = text.lstrip().startswith(self._texts) if self._starts else any(word in text for word in self._texts)
        return self.languages[0] if found else None


def load(cards: list[dict], classes=CLASSES) -> dict[str, tuple]:
    """The rules of each extension, in their order: the cards, then the classes. Two rules with one id are refused."""
    rules = [LiteralRule(card) for card in cards] + list(classes)
    ids = [rule.id for rule in rules]
    for name in ids:
        if ids.count(name) > 1:
            raise ValueError(f"{name}: two rules have this id")
    by_extension: dict[str, list] = {}
    for rule in rules:
        for extension in rule.extensions:
            by_extension.setdefault(extension, []).append(rule)
    return {extension: tuple(found) for extension, found in by_extension.items()}


with RULES_PATH.open("rb") as _handle:
    RULES = load(tomllib.load(_handle).get("rule", []))


def detect(path: Path, text: str | None = None, rules: dict[str, tuple] | None = None) -> Detection:
    """The language of the file at `path` whose text is `text`; without the text, its extension's."""
    suffix = path.suffix.lower()
    if text is not None:
        for rule in (RULES if rules is None else rules).get(suffix, ()):
            name = rule.decide(text[:MAX_CHARS])
            if name is not None:
                return Detection(LANGUAGE_OF.get(name), rule.id)
    return Detection(file_formats.SOURCES.get(suffix), EXTENSION)


def problems(rules: dict[str, tuple] | None = None, catalogue: dict | None = None) -> list[str]:
    """What breaks the rules' own cards, one line each: a rule with no sample of one outcome, a sample another rule
    of the same extension answers first or otherwise, a `no` sample the rule answers, and, given the catalogue's
    `extensions`, a language Linguist does not list for the extension."""
    rules = RULES if rules is None else rules
    found = []
    for rule in {rule.id: rule for group in rules.values() for rule in group}.values():
        if not rule.yes or not rule.no:
            found.append(f"{rule.id}: needs a sample of each outcome, `yes` and `no`")
        for text in rule.no:
            if rule.decide(text) is not None:
                found.append(f"{rule.id}: answers a `no` sample: {text[:40]!r}")
        for extension in rule.extensions:
            for text, name in rule.yes:
                got = detect(Path("sample" + extension), text, rules)
                if got != Detection(LANGUAGE_OF.get(name), rule.id):
                    found.append(f"{rule.id}: on {extension} a `yes` sample is decided by {got.decided_by} "
                                 f"as {got.language}: {text[:40]!r}")
            listed = (catalogue or {}).get(extension) or []
            for name in rule.languages:
                if listed and name not in listed:
                    found.append(f"{rule.id}: Linguist does not list {name} for {extension} ({', '.join(listed)})")
    return found
