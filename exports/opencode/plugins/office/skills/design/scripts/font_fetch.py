#!/usr/bin/env python3
"""Download Google Fonts faces, verify them and install them for the current user.

Subcommands:
  status SPEC...             report which requested faces are already installed
  fetch SPEC... --dest DIR   download and verify faces into DIR without installing
  install SPEC...            download, verify and install the missing faces for
                             the current user (no administrator rights)

SPEC uses the Google Fonts CSS2 family syntax with explicit weights, for example
"Inter:wght@400;700" or "Source Sans 3:ital,wght@0,400;0,700;1,400". A bare
family name means the regular 400 face. Output is JSON on stdout. Exit 0 when
every requested face is satisfied, 1 when a face could not be downloaded,
verified or installed, 2 on invalid use.

Every downloaded file is parsed before it is kept: its family, weight and style
must match the request, its embedded license must be OFL, Apache or UFL, and its
embedding permission must allow embedding in a document.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA = "daodan/font-fetch/v1"
CSS_ENDPOINT = "https://fonts.googleapis.com/css2?family="
FONT_HOST = "fonts.gstatic.com"
MAX_CSS_BYTES = 256 * 1024
MAX_FONT_BYTES = 25 * 1024 * 1024
TIMEOUT = 30
# A non-browser agent makes the API return one complete TrueType file per face
# instead of unicode-range subsets in WOFF2.
USER_AGENT = "Python-urllib/3"
FONT_SUFFIXES = (".ttf", ".otf", ".ttc")
NOTICE = ("Faces are installed for the current user only. Recipients of an editable "
          "file need the same fonts or a copy embedded in the file.")


class FontError(Exception):
    pass


# ---------------------------------------------------------------- requests

def parse_spec(spec: str) -> tuple[str, list[tuple[str, int]]]:
    """Return the family and the requested (style, weight) faces of one SPEC."""
    family, _, axes = spec.partition(":")
    family = " ".join(family.split())
    if not family or not re.fullmatch(r"[A-Za-z0-9 ]+", family):
        raise FontError(f"invalid family name in {spec!r}")
    if not axes:
        return family, [("normal", 400)]
    names, at, values = axes.partition("@")
    if not at or not values:
        raise FontError(f"invalid axis list in {spec!r}")
    names = names.split(",")
    if names not in (["wght"], ["ital"], ["ital", "wght"]):
        raise FontError(f"only the ital and wght axes are supported, got {axes!r}")
    faces = []
    for value in values.split(";"):
        parts = value.split(",")
        if len(parts) != len(names) or any(".." in part for part in parts):
            raise FontError(f"use explicit weights, not ranges, in {spec!r}")
        fields = dict(zip(names, parts))
        try:
            italic = int(fields.get("ital", "0"))
            weight = int(fields.get("wght", "400"))
        except ValueError as error:
            raise FontError(f"invalid axis value in {spec!r}") from error
        if italic not in (0, 1) or not 100 <= weight <= 1000:
            raise FontError(f"axis value out of range in {spec!r}")
        faces.append(("italic" if italic else "normal", weight))
    if len(set(faces)) != len(faces):
        raise FontError(f"duplicate face in {spec!r}")
    return family, faces


def css_url(spec: str) -> str:
    return CSS_ENDPOINT + urllib.parse.quote(spec, safe=":,@;").replace("%20", "+")


def _get(url: str, limit: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise FontError(f"response from {url} exceeds {limit} bytes")
    return data


def parse_css(css: str) -> dict[tuple[str, int], str]:
    """Map each (style, weight) of a CSS2 response to its font file URL."""
    faces: dict[tuple[str, int], str] = {}
    for block in re.findall(r"@font-face\s*\{([^}]*)\}", css):
        if "unicode-range" in block:
            raise FontError("the API returned subsetted faces; a complete file is required")
        style = re.search(r"font-style:\s*(normal|italic)", block)
        weight = re.search(r"font-weight:\s*(\d+)\s*;", block)
        source = re.search(r"src:\s*url\(([^)]+)\)", block)
        if not (style and weight and source):
            raise FontError("unrecognized @font-face block in the API response")
        url = source.group(1).strip("'\"")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != FONT_HOST:
            raise FontError(f"refusing a font URL outside https://{FONT_HOST}: {url}")
        key = (style.group(1), int(weight.group(1)))
        if key in faces:
            raise FontError(f"the API returned more than one file for {key}")
        faces[key] = url
    return faces


# ---------------------------------------------------------------- font files

def _font_offsets(read) -> list[int]:
    head = read(0, 12)
    if len(head) < 12:
        raise FontError("file too short for a font")
    if head[:4] == b"ttcf":
        count = struct.unpack(">I", head[8:12])[0]
        if not 0 < count <= 64:
            raise FontError("invalid font collection")
        return list(struct.unpack(f">{count}I", read(12, 4 * count)))
    return [0]


def _decode_name(platform: int, raw: bytes) -> str:
    if platform in (0, 3):
        return raw.decode("utf-16-be", errors="replace")
    return raw.decode("mac_roman", errors="replace")


def read_font(read, offset: int = 0) -> dict:
    """Parse the naming, weight and permission fields of one sfnt face."""
    header = read(offset, 12)
    if len(header) < 12 or header[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        raise FontError("not a TrueType or OpenType font")
    count = struct.unpack(">H", header[4:6])[0]
    if not 0 < count <= 128:
        raise FontError("invalid table directory")
    tables = {}
    directory = read(offset + 12, 16 * count)
    if len(directory) < 16 * count:
        raise FontError("truncated table directory")
    for index in range(count):
        tag, _, start, length = struct.unpack(">4sIII", directory[16 * index:16 * index + 16])
        tables[tag] = (start, length)
    if b"name" not in tables or b"OS/2" not in tables:
        raise FontError("font lacks a name or OS/2 table")

    start, length = tables[b"name"]
    data = read(start, min(length, 1024 * 1024))
    if len(data) < 6:
        raise FontError("truncated name table")
    records, storage = struct.unpack(">HH", data[2:6])
    names: dict[int, tuple[int, str]] = {}
    for index in range(records):
        base = 6 + 12 * index
        if base + 12 > len(data):
            raise FontError("truncated name records")
        platform, encoding, language, name_id, size, at = struct.unpack(">6H", data[base:base + 12])
        if name_id not in (1, 2, 4, 13, 14, 16):
            continue
        if platform == 3 and encoding not in (0, 1, 10):
            continue
        raw = data[storage + at:storage + at + size]
        rank = 0 if (platform == 3 and language == 0x409) else 1 if platform == 3 else 2
        if name_id not in names or rank < names[name_id][0]:
            names[name_id] = (rank, _decode_name(platform, raw))

    start, length = tables[b"OS/2"]
    os2 = read(start, min(length, 128))
    if len(os2) < 64:
        raise FontError("truncated OS/2 table")
    weight = struct.unpack(">H", os2[4:6])[0]
    fs_type = struct.unpack(">H", os2[8:10])[0]
    selection = struct.unpack(">H", os2[62:64])[0]

    def name(name_id):
        return names.get(name_id, (0, ""))[1].strip()

    return {
        "family": name(16) or name(1),
        "full_name": name(4) or name(1),
        "weight": weight,
        "style": "italic" if selection & 0x0001 else "normal",
        "fs_type": fs_type,
        "license_text": name(13),
        "license_url": name(14),
        "outline": "OpenType" if header[:4] == b"OTTO" else "TrueType",
    }


def license_of(meta: dict) -> str | None:
    text = f"{meta['license_text']} {meta['license_url']}".casefold()
    if "open font license" in text or "openfontlicense" in text or "scripts.sil.org/ofl" in text:
        return "OFL-1.1"
    if "apache license" in text or "apache.org/licenses" in text:
        return "Apache-2.0"
    if "ubuntu font licen" in text:
        return "UFL-1.0"
    return None


def embedding_of(fs_type: int) -> str:
    usage = fs_type & 0x000F
    if fs_type & 0x0200:
        return "bitmap-only"
    if usage & 0x0002 and not usage & 0x000C:
        return "restricted"
    if usage & 0x0004 and not usage & 0x0008:
        return "preview-print"
    return "editable" if usage & 0x0008 else "installable"


STYLE_WORDS = {"thin", "hairline", "extralight", "ultralight", "light", "regular", "book",
               "normal", "medium", "semibold", "demibold", "bold", "extrabold", "ultrabold",
               "black", "heavy", "italic", "oblique"}


def _norm(family: str) -> str:
    """Canonical family key; legacy names such as "Barlow Medium" carry the style."""
    words = family.split()
    while len(words) > 1 and words[-1].casefold() in STYLE_WORDS:
        words.pop()
    return "".join(words).casefold()


def verify(data: bytes, family: str, style: str, weight: int) -> dict:
    meta = read_font(lambda at, size: data[at:at + size])
    if _norm(meta["family"]) != _norm(family):
        raise FontError(f"file declares family {meta['family']!r}, expected {family!r}")
    if meta["weight"] != weight or meta["style"] != style:
        raise FontError(f"file declares {meta['style']} {meta['weight']}, expected {style} {weight}")
    meta["license"] = license_of(meta)
    if meta["license"] is None:
        raise FontError(f"unrecognized license in {meta['full_name']!r}: "
                        f"{meta['license_text'][:80]!r} {meta['license_url']!r}")
    meta["embedding"] = embedding_of(meta["fs_type"])
    if meta["embedding"] in ("restricted", "bitmap-only"):
        raise FontError(f"{meta['full_name']!r} does not permit document embedding")
    return meta


def file_name(family: str, style: str, weight: int) -> str:
    return f"{''.join(family.split())}-{weight}{'Italic' if style == 'italic' else ''}.ttf"


# ---------------------------------------------------------------- installed fonts

def user_font_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Fonts"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "fonts"


def font_dirs() -> list[Path]:
    if sys.platform == "win32":
        system = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"]
    elif sys.platform == "darwin":
        system = [Path("/System/Library/Fonts"), Path("/Library/Fonts")]
    else:
        system = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]
    return [*system, user_font_dir()]


def installed_faces(dirs: list[Path] | None = None) -> set[tuple[str, str, int]]:
    faces = set()
    for directory in dirs if dirs is not None else font_dirs():
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.suffix.casefold() not in FONT_SUFFIXES or not path.is_file():
                continue
            try:
                with path.open("rb") as handle:
                    def read(at, size, handle=handle):
                        handle.seek(at)
                        return handle.read(size)
                    for offset in _font_offsets(read):
                        meta = read_font(read, offset)
                        faces.add((_norm(meta["family"]), meta["style"], meta["weight"]))
            except (OSError, FontError, struct.error):
                continue
    return faces


def register(path: Path, meta: dict) -> None:
    """Make an installed face visible to applications started from now on."""
    if sys.platform == "win32":
        import ctypes
        import winreg
        key = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as handle:
            winreg.SetValueEx(handle, f"{meta['full_name']} ({meta['outline']})", 0,
                              winreg.REG_SZ, str(path))
        ctypes.windll.gdi32.AddFontResourceW(str(path))
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
    elif sys.platform != "darwin" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(path.parent)], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _write_new(path: Path, data: bytes) -> str:
    if path.exists():
        if path.read_bytes() == data:
            return "exists"
        raise FontError(f"{path} exists with different content")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".part")
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)
    os.replace(temporary, path)
    return "written"


# ---------------------------------------------------------------- commands

def run(command: str, specs: list[str], dest: Path | None = None) -> dict:
    requests = []
    for spec in specs:
        family, faces = parse_spec(spec)
        requests.append((spec, family, faces))
    installed = installed_faces() if command in ("status", "install") else set()
    results = []
    for spec, family, faces in requests:
        wanted = []
        for style, weight in faces:
            entry = {"spec": spec, "family": family, "style": style, "weight": weight}
            if command != "fetch" and (_norm(family), style, weight) in installed:
                entry["status"] = "already-installed"
            elif command == "status":
                entry["status"] = "missing"
            else:
                wanted.append(entry)
            results.append(entry)
        if not wanted:
            continue
        try:
            urls = parse_css(_get(css_url(spec), MAX_CSS_BYTES).decode("utf-8"))
        except (OSError, FontError, UnicodeDecodeError) as error:
            for entry in wanted:
                entry.update(status="failed", error=f"font list request failed: {error}")
            continue
        for entry in wanted:
            try:
                url = urls.get((entry["style"], entry["weight"]))
                if url is None:
                    raise FontError("Google Fonts does not offer this face")
                data = _get(url, MAX_FONT_BYTES)
                meta = verify(data, family, entry["style"], entry["weight"])
                target = (dest if command == "fetch" else user_font_dir()) / file_name(
                    family, entry["style"], entry["weight"])
                written = _write_new(target, data)
                if command == "install":
                    register(target, meta)
                entry.update(status="fetched" if command == "fetch" else "installed",
                             file=written, path=str(target), license=meta["license"],
                             embedding=meta["embedding"], full_name=meta["full_name"])
            except (OSError, FontError, struct.error) as error:
                entry.update(status="failed", error=str(error))
    ok = all(entry["status"] in ("already-installed", "fetched", "installed") for entry in results)
    return {"schema": SCHEMA, "command": command, "ok": ok, "faces": results, "notice": NOTICE}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("status", "report which faces are installed"),
                            ("fetch", "download and verify faces into --dest"),
                            ("install", "download, verify and install missing faces for the current user")):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("specs", nargs="+", metavar="SPEC",
                         help='Google Fonts family spec, e.g. "Inter:wght@400;700"')
        if name == "fetch":
            sub.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = run(args.command, args.specs, getattr(args, "dest", None))
    except FontError as error:
        print(json.dumps({"schema": SCHEMA, "command": args.command, "ok": False,
                          "error": str(error)}, indent=2))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
