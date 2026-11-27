"""The register of file formats and the catalogue of Linguist's names for them agree, and the catalogue is what
Linguist's own `languages.yml` says of the formats Daodan accepts."""
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import file_formats
import format_catalog
import parser_identity

LANGUAGES = """
C: {type: programming, extensions: [".c", ".h"]}
C++: {type: programming, extensions: [".cpp", ".H"]}
Markdown: {type: prose, extensions: [".MD"], filenames: [README]}
Dockerfile: {type: programming, filenames: [Dockerfile]}
Starlark: {type: programming, extensions: [".bzl"], filenames: [BUILD, Tiltfile]}
Zig: {type: programming, extensions: [".zig"]}
"""


def _gem(folder: Path) -> Path:
    """A gem as RubyGems packs one: a tar holding `data.tar.gz`, which holds the files."""
    data, body = io.BytesIO(), LANGUAGES.encode()
    with tarfile.open(fileobj=data, mode="w:gz") as inner:
        member = tarfile.TarInfo(format_catalog.MEMBER)
        member.size = len(body)
        inner.addfile(member, io.BytesIO(body))
    gem = folder / "linguist.gem"
    with tarfile.open(gem, "w") as outer:
        member = tarfile.TarInfo("data.tar.gz")
        member.size = len(data.getvalue())
        outer.addfile(member, io.BytesIO(data.getvalue()))
    return gem


def test_register_and_catalogue_hold():
    assert format_catalog.check() == []


def test_catalogue_is_linguists_names_for_the_accepted_formats_only(tmp_path, monkeypatch):
    gem = _gem(tmp_path)
    with pytest.raises(ValueError, match="sha256"):
        format_catalog.linguist_languages(gem)  # not the pinned gem
    monkeypatch.setattr(format_catalog, "SHA256", hashlib.sha256(gem.read_bytes()).hexdigest())
    written = format_catalog.catalog(format_catalog.linguist_languages(gem))
    assert written["extensions"][".h"] == ["C", "C++"]  # `.H` is compared in lower case, as the snapshot reads it
    assert written["extensions"][".py"] == []  # accepted, and unknown to this Linguist
    assert ".zig" not in written["extensions"] and ".bzl" not in written["extensions"]  # not accepted: not listed
    assert written["unread_extensions"] == {".bzl": ["Starlark"], ".zig": ["Zig"]}  # the rest, in lower case
    assert written["unread_filenames"] == {"README": ["Markdown"], "Tiltfile": ["Starlark"]}
    assert written["filenames"]["Dockerfile"] == ["Dockerfile"]  # a manifest Daodan accepts
    assert written["types"] == {"C": "programming", "C++": "programming", "Dockerfile": "programming",
                                "Markdown": "prose", "Starlark": "programming", "Zig": "programming"}
    assert written["filenames"]["BUILD"] == ["Starlark"] and "Tiltfile" not in written["filenames"]
    assert json.loads(format_catalog.text(written)) == written


def test_check_names_a_name_without_a_type_and_a_key_in_both_tables():
    catalogue = json.loads(format_catalog.PATH.read_text(encoding="utf-8"))
    catalogue["unread_extensions"][".rb"] = ["Nothing"]
    catalogue["unread_extensions"][".py"] = ["Python"]
    problems = format_catalog.check(catalogue)
    assert "unread_extensions: .rb names Nothing, which has no type in `types`" in problems
    assert "unread_extensions: .py is also in extensions" in problems


def test_check_names_a_language_linguist_does_not_give_the_extension():
    catalogue = json.loads(format_catalog.PATH.read_text(encoding="utf-8"))
    catalogue["extensions"][".py"] = ["Ruby"]
    del catalogue["extensions"][".md"]
    problems = format_catalog.check(catalogue)
    assert any(line.startswith(".py: read as python") and "Ruby" in line for line in problems)
    assert any(line.startswith("extensions: .md is in the register only") for line in problems)


def test_register_is_part_of_the_parser_fingerprint(tmp_path, monkeypatch):
    before = parser_identity.parser_fingerprint()
    changed = tmp_path / "file-formats.json"
    changed.write_text(file_formats.PATH.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(file_formats, "PATH", changed)
    assert parser_identity.parser_fingerprint() != before


# ---------------------------------------------------------------- the rules of the content

import languages  # noqa: E402
from languages import detect as detection  # noqa: E402  (the package: `languages` does not rebind the name)

CARD = {"id": "ts.sample", "extensions": [".ts"], "language": "XML", "test": "starts-with", "texts": ["<?xml"],
        "why": "a sample", "source": "this test", "yes": ["<?xml?>"], "no": ["let a = 1;"]}


def test_every_rule_holds_on_its_own_samples():
    assert detection.problems() == []
    assert {rule.id for group in detection.RULES.values() for rule in group} >= {
        "ts.xml-document", "sql.oracle-words", "sql.anchored-type", "h.syntax-tree"}


def test_a_shared_extension_is_decided_by_the_rule_that_answers_and_else_by_the_extension():
    xml = detection.detect(Path("app_it.ts"), '<?xml version="1.0"?>\n<!DOCTYPE TS>\n<TS/>\n')
    assert xml == detection.Detection(None, "ts.xml-document")  # XML: a name the register joins to no language
    assert detection.detect(Path("a.ts"), "const a = 1;\n") == detection.Detection("typescript", "extension")
    assert detection.detect(Path("a.DDL"), "x emp.sal%TYPE;") == detection.Detection("plsql", "sql.anchored-type")
    assert detection.detect(Path("a.sql"), "PRAGMA AUTONOMOUS_TRANSACTION;").decided_by == "sql.oracle-words"
    assert detection.detect(Path("a.sql")) == detection.Detection("sql", "extension")  # no text: no rule is asked
    assert detection.detect(Path("a.tsx"), "<?xml?>").language == "typescript"  # the rule is `.ts`'s only
    assert detection.detect(Path("a.zig"), "const a = 1;") == detection.Detection(None, "extension")
    assert languages.detect_language(Path("a.sql"), "begin dbms_output.put_line(1); end;") == "plsql"


@pytest.mark.parametrize("change,field", [
    ({"pattern": "x"}, "pattern"), ({"test": "matches"}, "test"), ({"texts": []}, "texts"), ({"no": [1]}, "no"),
    ({"ignore-case": "yes"}, "ignore-case"), ({"extensions": [".zig"]}, "extensions"), ({"language": None}, "language")])
def test_a_rule_outside_the_schema_does_not_load_and_the_error_names_the_field(change, field):
    with pytest.raises(ValueError, match=f"ts.sample: .*`{field}`"):
        detection.load([{**CARD, **change}], classes=())


def test_two_rules_with_one_id_do_not_load():
    with pytest.raises(ValueError, match="two rules"):
        detection.load([CARD, CARD], classes=())


def test_rules_that_contradict_each_other_or_the_catalogue_are_named():
    first = {**CARD, "id": "ts.first", "language": "TypeScript", "texts": ["<?"]}
    rules = detection.load([first, CARD], classes=())
    assert any(line.startswith("ts.sample: on .ts a `yes` sample is decided by ts.first")
               for line in detection.problems(rules))
    rules = detection.load([{**CARD, "no": ["<?xml too"]}], classes=())
    assert any(line.startswith("ts.sample: answers a `no` sample") for line in detection.problems(rules))
    rules = detection.load([{**CARD, "language": "Ruby"}], classes=())
    assert detection.problems(rules, {".ts": ["TypeScript", "XML"]}) == [
        "ts.sample: Linguist does not list Ruby for .ts (TypeScript, XML)"]
