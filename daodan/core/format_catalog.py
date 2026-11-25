#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Write what Linguist calls the files Daodan accepts, from Linguist's own `languages.yml`. A development tool.

The source is the `github-linguist` gem at a fixed version, checked by sha256 and read as an archive: nothing of it
is installed or run. The catalogue (`data/linguist-catalog.json`) holds, for each extension and file name of
Daodan's register of file formats (`data/file-formats.json`) and for no other, the names of the Linguist languages
that list it; an empty list is a format Linguist does not know. It names no language of Daodan's: the register joins
the two (`languages[*].linguist`), and `check` says where they disagree. An extension is compared in lower case, as
the snapshot reads a suffix.

    python format_catalog.py build [--gem FILE]     # FILE: the gem already fetched; else it is downloaded
    python format_catalog.py check
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tarfile
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import file_formats  # noqa: E402

SCHEMA = "daodan/linguist-catalog/v1"
PATH = file_formats.PATH.with_name("linguist-catalog.json")
PACKAGE, VERSION = "github-linguist", "9.7.0"
URL = f"https://rubygems.org/downloads/{PACKAGE}-{VERSION}.gem"
SHA256 = "39a5e077e946029ef0ddbdc1344a53802455f4920f8c758d2a6b114d963d7734"
MEMBER = "lib/linguist/languages.yml"
KINDS = ("SOURCES", "DOCUMENTS", "PRESENTATION", "STACK_SOURCES")  # the register's lists of extensions


def linguist_languages(gem: Path) -> dict:
    """`languages.yml` of a Linguist gem, read from the archive without unpacking it."""
    import yaml
    if hashlib.sha256(gem.read_bytes()).hexdigest() != SHA256:
        raise ValueError(f"{gem.name} is not {PACKAGE} {VERSION}: its sha256 differs")
    with tarfile.open(gem) as outer:
        data = outer.extractfile("data.tar.gz").read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as inner:
        return yaml.safe_load(inner.extractfile(MEMBER).read())


def accepted() -> tuple[set[str], set[str]]:
    """The extensions and the file names of Daodan's register."""
    return {extension for kind in KINDS for extension in getattr(file_formats, kind)}, set(file_formats.MANIFESTS)


def catalog(languages: dict) -> dict:
    """The catalogue of Daodan's accepted formats, from Linguist's languages."""
    extensions, filenames = ({name: set() for name in names} for names in accepted())
    for language, entry in languages.items():
        for extension in entry.get("extensions") or ():
            if extension.lower() in extensions:
                extensions[extension.lower()].add(language)
        for filename in entry.get("filenames") or ():
            if filename in filenames:
                filenames[filename].add(language)
    return {"schema": SCHEMA, "source": {"package": PACKAGE, "version": VERSION, "url": URL, "sha256": SHA256,
                                         "file": MEMBER},
            "extensions": {name: sorted(found) for name, found in sorted(extensions.items())},
            "filenames": {name: sorted(found) for name, found in sorted(filenames.items())}}


def text(value: dict) -> str:
    """The catalogue as it is written: one format per line."""
    def table(rows: dict) -> str:
        return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
                                  for k, v in rows.items()) + "\n }"
    return ("{\n" + f' "schema": {json.dumps(value["schema"])},\n "source": {json.dumps(value["source"])},\n'
            f' "extensions": {table(value["extensions"])},\n "filenames": {table(value["filenames"])}\n' + "}\n")


def check(value: object | None = None) -> list[str]:
    """What breaks the rules of register, catalogue and language rules, one line each; empty when they hold."""
    import languages
    if value is None:
        value = json.loads(PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        return [f"{PATH.name}: schema is not {SCHEMA}"]
    problems = []
    if (value.get("source") or {}).get("version") != VERSION:
        problems.append(f"{PATH.name}: not written from {PACKAGE} {VERSION}; run `format_catalog.py build`")
    kinds = [kind for kind in KINDS for _ in getattr(file_formats, kind)]
    listed = [extension for kind in KINDS for extension in getattr(file_formats, kind)]
    for extension in sorted({e for e in listed if listed.count(e) > 1}):
        problems.append(f"{extension}: in more than one list of the register ("
                        + ", ".join(k for k, e in zip(kinds, listed) if e == extension) + ")")
    for extension in sorted(e for e in listed if e != e.lower() or not e.startswith(".")):
        problems.append(f"{extension}: an extension is written in lower case, with its dot")
    for name, wanted, found in zip(("extensions", "filenames"), accepted(),
                                   (value.get("extensions"), value.get("filenames"))):
        found = found if isinstance(found, dict) else {}
        for key in sorted(wanted ^ set(found)):
            problems.append(f"{name}: {key} is in the {'register' if key in wanted else 'catalogue'} only; "
                            "run `format_catalog.py build`")
    if set(file_formats.LINGUIST_NAMES) != set(languages.SUPPORTED_LANGUAGES):
        problems.append("languages: the register and `languages.SUPPORTED_LANGUAGES` differ on "
                        + ", ".join(sorted(set(file_formats.LINGUIST_NAMES) ^ set(languages.SUPPORTED_LANGUAGES))))
    for extension, language in file_formats.SOURCES.items():
        names = (value.get("extensions") or {}).get(extension) or []
        if names and not set(names) & set(file_formats.LINGUIST_NAMES[language]):
            problems.append(f"{extension}: read as {language}, which the register does not join to any of "
                            f"Linguist's names for it ({', '.join(names)})")
    return problems + languages.detect.problems(catalogue=value.get("extensions"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--gem", type=Path)
    commands.add_parser("check")
    args = parser.parse_args(argv)
    if args.command == "build":
        with tempfile.TemporaryDirectory() as folder:
            gem = args.gem
            if gem is None:
                import engine_tools
                gem = engine_tools.download(URL, Path(folder) / "linguist.gem", sha256=SHA256)
            PATH.write_text(text(catalog(linguist_languages(gem))), encoding="utf-8", newline="\n")
    problems = check()
    print("\n".join(problems) or f"{PATH.name}: holds", file=sys.stderr if problems else sys.stdout)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
