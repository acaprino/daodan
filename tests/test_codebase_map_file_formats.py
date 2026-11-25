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
    assert written["filenames"]["BUILD"] == ["Starlark"] and "Tiltfile" not in written["filenames"]
    assert json.loads(format_catalog.text(written)) == written


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
