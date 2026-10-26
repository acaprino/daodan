#!/usr/bin/env python3
"""Embed fonts in a saved PPTX or DOCX copy and report which fonts a file embeds.

Subcommands:
  inspect FILE           list the fonts a PPTX/DOCX uses and which ones it embeds
  embed INPUT OUTPUT     save a copy of INPUT with TrueType fonts embedded, through
                         an installed Microsoft PowerPoint or Word on Windows

`embed` never writes INPUT and refuses an existing OUTPUT. Office embeds only
installed fonts whose license permits it. PowerPoint embeds the characters used
(a subset); Word is told to embed complete fonts. Output is JSON on stdout.
Exit 0 on success, 1 when embedding or inspection failed, 2 on invalid use.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

SCHEMA = "daodan/font-embed/v1"
TIMEOUT = 300
MAX_PART = 64 * 1024 * 1024
FORMATS = {".pptx": ("PowerPoint", 24), ".pptm": ("PowerPoint", 25),
           ".docx": ("Word", 16), ".docm": ("Word", 13)}
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
NOTICE = ("Embedding evidence comes from the saved package. It does not prove how "
          "another computer or application renders the file.")

# Arguments travel in environment variables, never inside the script text.
POWERSHELL = r"""
$ErrorActionPreference = 'Stop'
$source = $env:FONT_EMBED_INPUT
$target = $env:FONT_EMBED_OUTPUT
$format = [int]$env:FONT_EMBED_FORMAT
if ($env:FONT_EMBED_APP -eq 'PowerPoint') {
  $app = New-Object -ComObject PowerPoint.Application
  $security = $app.AutomationSecurity
  $deck = $null
  try {
    $app.AutomationSecurity = 3
    $deck = $app.Presentations.Open($source, -1, 0, 0)
    $deck.SaveAs($target, $format, -1)
  } finally {
    try { if ($null -ne $deck) { $deck.Close() } }
    finally {
      $app.AutomationSecurity = $security
      if ($app.Presentations.Count -eq 0) { $app.Quit() }
    }
  }
} else {
  $app = New-Object -ComObject Word.Application
  $security = $app.AutomationSecurity
  $doc = $null
  try {
    $app.Visible = $false
    $app.AutomationSecurity = 3
    $doc = $app.Documents.Open($source, $false, $true, $false)
    $doc.EmbedTrueTypeFonts = $true
    $doc.SaveSubsetFonts = $false
    $doc.DoNotEmbedSystemFonts = $true
    $doc.SaveAs2($target, $format)
  } finally {
    try { if ($null -ne $doc) { $doc.Close(0) } }
    finally {
      $app.AutomationSecurity = $security
      if ($app.Documents.Count -eq 0) { $app.Quit() }
    }
  }
}
"""


class EmbedError(Exception):
    pass


def _xml(archive: zipfile.ZipFile, name: str):
    try:
        info = archive.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_PART:
        raise EmbedError(f"{name} exceeds {MAX_PART} bytes")
    return ElementTree.fromstring(archive.read(info))


def _targets(archive: zipfile.ZipFile, part: str) -> dict[str, str]:
    path = PurePosixPath(part)
    rels = _xml(archive, str(path.parent / "_rels" / (path.name + ".rels")))
    if rels is None:
        return {}
    targets = {}
    for rel in rels.findall("rel:Relationship", NS):
        target = PurePosixPath(rel.get("Target", ""))
        resolved = PurePosixPath(*(target.parts[1:])) if target.is_absolute() else path.parent / target
        parts = []
        for piece in resolved.parts:
            if piece == "..":
                if parts:
                    parts.pop()
            elif piece != ".":
                parts.append(piece)
        targets[rel.get("Id")] = "/".join(parts)
    return targets


def _eot_subset(data: bytes) -> bool | None:
    if len(data) < 16:
        return None
    flags = struct.unpack("<I", data[12:16])[0]
    return bool(flags & 0x1)


def inspect_pptx(archive: zipfile.ZipFile) -> dict:
    used: set[str] = set()
    for name in archive.namelist():
        if re.fullmatch(r"ppt/(slides/slide|slideLayouts/slideLayout|slideMasters/slideMaster|"
                        r"notesSlides/notesSlide|theme/theme)\d+\.xml", name):
            root = _xml(archive, name)
            for tag in ("latin", "ea", "cs"):
                for element in root.iter(f"{{{NS['a']}}}{tag}"):
                    face = element.get("typeface", "")
                    if face and not face.startswith("+"):
                        used.add(face)
    embedded = {}
    presentation = _xml(archive, "ppt/presentation.xml")
    targets = _targets(archive, "ppt/presentation.xml")
    if presentation is not None:
        for font in presentation.iterfind("p:embeddedFontLst/p:embeddedFont", NS):
            face = font.find("p:font", NS).get("typeface", "")
            styles, subset = [], []
            for style in ("regular", "bold", "italic", "boldItalic"):
                item = font.find(f"p:{style}", NS)
                if item is None:
                    continue
                part = targets.get(item.get(f"{{{NS['r']}}}id"))
                if part in archive.namelist():
                    styles.append(style)
                    with archive.open(part) as stream:
                        subset.append(_eot_subset(stream.read(16)))
            embedded[face] = {"styles": styles,
                              "subset": True if any(subset) else False if subset else None}
    return {"used": sorted(used), "embedded": embedded}


def inspect_docx(archive: zipfile.ZipFile) -> dict:
    used, embedded = set(), {}
    table = _xml(archive, "word/fontTable.xml")
    targets = _targets(archive, "word/fontTable.xml")
    settings = _xml(archive, "word/settings.xml")
    subset = None
    if settings is not None:
        subset = settings.find("w:saveSubsetFonts", NS) is not None
    for font in table.iterfind("w:font", NS) if table is not None else ():
        face = font.get(f"{{{NS['w']}}}name", "")
        if not face:
            continue
        used.add(face)
        styles = []
        for style in ("Regular", "Bold", "Italic", "BoldItalic"):
            item = font.find(f"w:embed{style}", NS)
            if item is not None and targets.get(item.get(f"{{{NS['r']}}}id")) in archive.namelist():
                styles.append(style[0].lower() + style[1:])
        if styles:
            embedded[face] = {"styles": styles, "subset": subset}
    return {"used": sorted(used), "embedded": embedded}


def inspect(path: Path) -> dict:
    suffix = path.suffix.casefold()
    if suffix not in FORMATS:
        raise EmbedError(f"unsupported file type {suffix!r}; expected one of {sorted(FORMATS)}")
    try:
        with zipfile.ZipFile(path) as archive:
            result = (inspect_pptx if FORMATS[suffix][0] == "PowerPoint" else inspect_docx)(archive)
    except (zipfile.BadZipFile, ElementTree.ParseError, OSError) as error:
        raise EmbedError(f"cannot read {path}: {error}") from error
    result["not_embedded"] = [face for face in result["used"] if face not in result["embedded"]]
    return {"path": str(path), **result}


def embed(source: Path, target: Path) -> dict:
    suffix = source.suffix.casefold()
    if suffix not in FORMATS:
        raise EmbedError(f"unsupported file type {suffix!r}; expected one of {sorted(FORMATS)}")
    if target.suffix.casefold() != suffix:
        raise EmbedError("OUTPUT must keep the source format")
    if not source.is_file():
        raise EmbedError(f"{source} does not exist")
    if target.exists() or target.resolve() == source.resolve():
        raise EmbedError(f"refusing to overwrite {target}; choose a new output path")
    if sys.platform != "win32":
        raise EmbedError("embedding needs Microsoft PowerPoint or Word on Windows; "
                         "this host has no supported embedding engine")
    app, file_format = FORMATS[suffix]
    environment = dict(os.environ, FONT_EMBED_INPUT=str(source.resolve()),
                       FONT_EMBED_OUTPUT=str(target.resolve()), FONT_EMBED_APP=app,
                       FONT_EMBED_FORMAT=str(file_format))
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", POWERSHELL],
            env=environment, capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise EmbedError(f"could not run {app} through PowerShell: {error}") from error
    if completed.returncode != 0 or not target.is_file():
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        raise EmbedError(f"{app} did not save an embedded copy: {detail[-1] if detail else 'no output'}")
    return {"engine": f"Microsoft {app} (COM)", **inspect(target)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("inspect", help="list used and embedded fonts")
    sub.add_argument("file", type=Path)
    sub = commands.add_parser("embed", help="save a copy with fonts embedded (Windows, Microsoft Office)")
    sub.add_argument("input", type=Path)
    sub.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.file) if args.command == "inspect" else embed(args.input, args.output)
    except EmbedError as error:
        print(json.dumps({"schema": SCHEMA, "command": args.command, "ok": False,
                          "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"schema": SCHEMA, "command": args.command, "ok": True, **result,
                      "notice": NOTICE}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
