#!/usr/bin/env python3
"""Preview real Office content under authored visual systems, or select one.

The HTML is a self-contained design preview. Native Office construction,
saved-file fidelity and source verification require independent evidence.
"""

from __future__ import annotations

import argparse
import base64
import copy
from html import escape
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import struct
import sys
import tempfile
from typing import Any
import zlib


_HELPER = Path(__file__).resolve().parents[2] / "content/scripts/office_records.py"
_SPEC = importlib.util.spec_from_file_location("office_design_records", _HELPER)
records = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(records)

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MAX_EMBEDDED_BYTES = 16 * 1024 * 1024
MAX_NATIVE_BYTES = 64 * 1024 * 1024
STYLE_CHOICES = {
    "title": {"left-aligned", "centered"},
    "callout": {"rule", "panel"},
    "quote": {"inset"},
    "navigation": {"section-label"},
    "table": {"ruled", "striped"},
    "chart": {"direct-labels"},
    "source_notes": {"required"},
    "density": {"compact", "comfortable", "spacious"},
    "treatment": {"documentary", "monochrome"},
}
NOTICE = ("Preview only. This HTML does not verify native Office editability or saved-file "
          "rendering fidelity. Source fidelity, font availability and saved Office files "
          "require independent verification. Navigation highlights a proposal; it records no approval. "
          "V1 is a limited theme sampler; complete creative comparison uses v2 native-render proofs.")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_comparison(document: dict) -> None:
    """Check wrapper/sample/provenance; shared design validation stays upstream."""
    _require(isinstance(document, dict), "comparison must be an object")
    if document.get("schema") == "office/design-candidates/v2":
        _validate_native_comparison(document)
        return
    _require(document.get("schema") == "office/design-candidates/v1", "invalid comparison schema")
    _require(_text(document.get("project_id")), "project_id is required")
    formats = document.get("formats")
    _require(isinstance(formats, list) and bool(formats)
             and all(isinstance(value, str) and value in {"docx", "pptx"} for value in formats),
             "formats must be a nonempty list of docx/pptx")
    _require(len(formats) == len(set(formats)), "formats must be unique")
    sample = document.get("sample")
    _require(isinstance(sample, dict), "a representative real sample is required")
    for field in ("title", "lead", "body", "source_note"):
        _require(_text(sample.get(field)), f"sample.{field} is required; supply real content")
    table = sample.get("table")
    _require(isinstance(table, dict), "sample.table is required")
    headers, rows = table.get("headers"), table.get("rows")
    _require(isinstance(headers, list) and bool(headers) and all(_text(value) for value in headers),
             "sample.table.headers must contain real text")
    _require(isinstance(rows, list) and bool(rows), "sample.table.rows must contain real data")
    for index, row in enumerate(rows):
        _require(isinstance(row, list) and len(row) == len(headers) and all(_text(cell) for cell in row),
                 f"sample.table.rows[{index}] must match the headers with populated text")
    candidates = document.get("candidates")
    _require(isinstance(candidates, list) and 2 <= len(candidates) <= 3,
             "supply two or three complete authored candidates")
    indexed = {}
    content_revision = None
    for index, candidate in enumerate(candidates):
        _require(isinstance(candidate, dict), f"candidates[{index}] must be an object")
        identity = candidate.get("id")
        _require(_text(identity) and identity not in indexed, "candidate IDs must be populated and unique")
        design = candidate.get("design")
        errors = records.validate_design(design, require_selected=False)
        _require(not errors, f"candidate {identity}: " + "; ".join(errors))
        _require(design["project_id"] == document["project_id"], f"candidate {identity}: project mismatch")
        _require(set(design["formats"]) == set(formats), f"candidate {identity}: format mismatch")
        if content_revision is None:
            content_revision = design["content"]["revision"]
        _require(design["content"]["revision"] == content_revision,
                 f"candidate {identity}: all proposals must bind the same content revision")
        for owner, field in (("components", "title"), ("components", "callout"),
                             ("components", "quote"), ("components", "navigation"),
                             ("data", "table"), ("data", "chart"), ("data", "source_notes"),
                             ("spacing", "density"), ("imagery", "treatment")):
            _require(design[owner][field] in STYLE_CHOICES[field],
                     f"candidate {identity}: unsupported {owner}.{field} {design[owner][field]!r}; "
                     "author a supported recipe or extend and verify the fixed renderer")
        indexed[identity] = candidate
    _validate_parents(indexed)


def _validate_parents(indexed: dict[str, dict]) -> None:
    for identity, candidate in indexed.items():
        if "parent_ids" not in candidate:
            continue
        parents = candidate["parent_ids"]
        _require(isinstance(parents, list) and len(parents) >= 2
                 and all(_text(parent) for parent in parents), f"candidate {identity}: supply explicit parent IDs")
        _require(len(set(parents)) == len(parents), f"candidate {identity}: duplicate parent ID")
        for parent in parents:
            _require(parent in indexed and parent != identity, f"candidate {identity}: unknown or self parent")
            _require(candidate["design"]["revision"] > indexed[parent]["design"]["revision"],
                     f"candidate {identity}: authored revision must exceed every parent's revision")


def _object(value: Any, required: set[str], path: str, optional: set[str] | None = None) -> dict:
    _require(isinstance(value, dict), f"{path} must be an object")
    _require(required <= set(value) <= required | (optional or set()),
             f"{path} has missing or unknown fields")
    return value


def _strings(value: Any, path: str, *, nonempty: bool = True) -> list[str]:
    _require(isinstance(value, list) and (bool(value) or not nonempty)
             and all(_text(item) for item in value), f"{path} must contain populated text")
    _require(len(value) == len(set(value)), f"{path} must be unique")
    return value


def _digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _lineage(value: Any, path: str, *, limit: int | None = None) -> set[str]:
    _require(isinstance(value, list), f"{path} must be a list")
    _require(limit is None or len(value) <= limit, f"{path} exceeds its entry limit")
    identities: set[str] = set()
    for index, entry in enumerate(value):
        entry = _object(entry, {"id", "sha256", "provenance"}, f"{path}[{index}]")
        identity = entry["id"]
        _require(_text(identity) and identity not in identities, f"{path}: IDs must be populated and unique")
        _require(_digest(entry["sha256"]), f"{path}: invalid SHA-256 digest")
        _require(_text(entry["provenance"]), f"{path}: provenance must be populated inert text")
        identities.add(identity)
    return identities


def _native_sample(document: dict) -> set[str]:
    sample = _object(document["sample"], {"title", "lead", "body", "source_note", "table", "content", "evidence"},
                     "sample", {"image", "not_applicable"})
    for field in ("title", "lead", "body", "source_note"):
        _require(_text(sample[field]), f"sample.{field} requires real content")
    content = _object(sample["content"], {"project_id", "revision", "unit_ids", "claim_ids"}, "sample.content")
    _require(content["project_id"] == document["project_id"], "sample.content project mismatch")
    _require(type(content["revision"]) is int and content["revision"] > 0, "invalid sample.content revision")
    for field in ("unit_ids", "claim_ids"):
        _strings(content[field], f"sample.content.{field}")
    sources = _lineage(document["sources"], "sources")
    evidence = sample["evidence"]
    _require(isinstance(evidence, list), "sample.evidence must be a list")
    known: set[str] = set()
    for index, item in enumerate(evidence):
        item = _object(item, {"id", "text", "source_refs"}, f"sample.evidence[{index}]")
        _require(_text(item["id"]) and item["id"] not in known, "evidence IDs must be populated and unique")
        known.add(item["id"])
        _require(_text(item["text"]), "evidence requires real text")
        references = item["source_refs"]
        _require(isinstance(references, list) and bool(references), "evidence requires source_refs")
        for reference in references:
            reference = _object(reference, {"source_id", "locator"}, "evidence source reference")
            _require(_text(reference["source_id"]) and reference["source_id"] in sources,
                     "evidence refers to an unknown source")
            _require(_text(reference["locator"]), "evidence source locator is required")
    absent = {"evidence"} if not evidence else set()
    table = sample["table"]
    if table is None:
        absent.add("table")
    else:
        table = _object(table, {"headers", "rows"}, "sample.table")
        headers = table["headers"]
        _require(isinstance(headers, list) and bool(headers) and all(_text(value) for value in headers),
                 "sample.table.headers requires real text")
        _require(isinstance(table["rows"], list) and bool(table["rows"]), "sample.table.rows requires real data")
        for row in table["rows"]:
            _require(isinstance(row, list) and len(row) == len(headers) and all(_text(value) for value in row),
                     "sample.table.rows must match populated headers")
    reasons = _object(sample.get("not_applicable", {}), set(), "sample.not_applicable", {"table", "evidence"})
    _require(set(reasons) == absent and all(_text(value) for value in reasons.values()),
             "not_applicable requires exactly the absent table/evidence jobs and populated reasons")
    if "image" in sample:
        _image_reference(sample["image"], "sample.image")
    return {"title", "lead", "body", "source_note", "table", "evidence"} - absent


def _image_reference(value: Any, path: str, *, frame: bool = False) -> dict:
    fields = {"path", "sha256", "alt"} | ({"slot_id", "provenance"} if frame else set())
    reference = _object(value, fields, path)
    _require(_text(reference["path"]) and _text(reference["alt"]), f"{path} requires relative path and alt text")
    _require(_digest(reference["sha256"]), f"{path} requires a SHA-256 digest")
    return reference


def _validate_native_comparison(document: dict) -> None:
    _object(document, {"schema", "project_id", "formats", "sample", "sources", "representatives", "candidates"},
            "comparison")
    _require(_text(document["project_id"]), "project_id is required")
    formats = _strings(document["formats"], "formats")
    _require(set(formats) <= {"docx", "pptx"}, "formats must contain docx/pptx only")
    roles = _native_sample(document)
    representatives = _object(document["representatives"], set(formats), "representatives")
    slots: dict[str, list[str]] = {}
    for output, items in representatives.items():
        _require(isinstance(items, list) and 1 <= len(items) <= 3, f"{output} requires one to three representative slots")
        slots[output], covered = [], set()
        for item in items:
            item = _object(item, {"slot_id", "roles"}, f"representatives.{output}")
            _require(_text(item["slot_id"]) and item["slot_id"] not in slots[output], "representative slot IDs must be unique")
            slots[output].append(item["slot_id"])
            assigned = _strings(item["roles"], "representative.roles")
            _require(set(assigned) <= roles, "representative has an absent or unknown sample role")
            covered.update(assigned)
        _require(covered == roles, f"{output} representatives omit real-content roles")
    candidates = document["candidates"]
    _require(isinstance(candidates, list) and 2 <= len(candidates) <= 3, "supply two or three complete authored candidates")
    indexed: dict[str, dict] = {}
    vectors: dict[str, set[tuple[str, ...]]] = {output: set() for output in formats}
    total_frames = 0
    content = {field: document["sample"]["content"][field] for field in ("project_id", "revision")}
    for candidate in candidates:
        _object(candidate, {"id", "design", "previews"}, "candidate", {"parent_ids"})
        identity, design = candidate["id"], candidate["design"]
        _require(_text(identity) and identity not in indexed, "candidate IDs must be populated and unique")
        errors = records.validate_design(design, require_selected=False)
        _require(not errors, f"candidate {identity}: " + "; ".join(errors))
        _require("selection" not in design, "v2 proposals must be unselected")
        _require(design["project_id"] == document["project_id"]
                 and {field: design["content"][field] for field in content} == content,
                 f"candidate {identity}: content identity/revision mismatch")
        _require(set(design["formats"]) == set(formats), f"candidate {identity}: format mismatch")
        previews = _object(candidate["previews"], set(formats), f"candidate {identity}.previews")
        for output, preview in previews.items():
            preview = _object(preview, {"binding", "frames", "assets"}, f"preview.{output}")
            binding = _object(preview["binding"], {"candidate_id", "design_revision", "design_sha256", "content", "sample_sha256", "format"},
                              f"preview.{output}.binding")
            bound_content = _object(binding["content"], {"project_id", "revision"}, "binding.content")
            _require(type(bound_content["revision"]) is int and bound_content == content, "stale binding.content")
            _require(binding["candidate_id"] == identity and binding["format"] == output
                     and type(binding["design_revision"]) is int and binding["design_revision"] == design["revision"],
                     "candidate/design/format binding mismatch")
            for field, actual in (("design_sha256", design), ("sample_sha256", document["sample"])):
                _require(_digest(binding[field]) and binding[field].lower() == _canonical_digest(actual), f"stale {field} binding")
            _lineage(preview["assets"], f"preview.{output}.assets", limit=20)
            frames = preview["frames"]
            _require(isinstance(frames, list) and len(frames) == len(slots[output]), "frames must match representative slots")
            vector = []
            for slot, frame in zip(slots[output], frames):
                frame = _image_reference(frame, "frame", frame=True)
                _require(frame["slot_id"] == slot, "frame slots must match representatives in order")
                provenance = _object(frame["provenance"], {"kind", "source", "source_sha256", "locator", "tool", "tool_version", "capture_id"},
                                     "frame.provenance")
                _require(provenance["kind"] == "native-render", "only native-render proof is supported")
                _require(all(_text(provenance[field]) for field in ("source", "locator", "tool", "tool_version", "capture_id")),
                         "native provenance fields require populated text")
                _require(_digest(provenance["source_sha256"]), "native source requires a SHA-256 digest")
                vector.append(frame["sha256"].lower())
            fingerprint = tuple(vector)
            _require(fingerprint not in vectors[output], f"{output}: candidates reuse the same frame digest vector")
            vectors[output].add(fingerprint)
            total_frames += len(frames)
        indexed[identity] = candidate
    _require(total_frames <= 18, "comparison exceeds eighteen frames")
    _validate_parents(indexed)


def _dimensions(raw: bytes, suffix: str) -> tuple[str, int, int]:
    if suffix == ".png":
        _require(raw.startswith(b"\x89PNG\r\n\x1a\n"), "image has an invalid PNG signature")
        offset, dimensions, saw_data = 8, None, False
        while offset + 12 <= len(raw):
            size = struct.unpack_from(">I", raw, offset)[0]
            kind = raw[offset + 4:offset + 8]
            end = offset + 12 + size
            _require(end <= len(raw), "truncated PNG chunk")
            payload = raw[offset + 8:end - 4]
            crc = struct.unpack_from(">I", raw, end - 4)[0]
            _require(zlib.crc32(kind + payload) == crc, "invalid PNG chunk checksum")
            if dimensions is None:
                _require(kind == b"IHDR" and size == 13, "PNG must start with a complete IHDR")
                dimensions = struct.unpack_from(">II", payload)
            elif kind == b"IHDR":
                raise ValueError("duplicate PNG IHDR")
            if kind == b"IDAT":
                saw_data = True
            if kind == b"IEND":
                _require(size == 0 and saw_data and end == len(raw), "invalid PNG end/data boundary")
                return "image/png", *dimensions
            offset = end
        raise ValueError("PNG has no complete image end")
    _require(raw.startswith(b"\xff\xd8") and raw.endswith(b"\xff\xd9"), "image has an invalid JPEG signature/end")
    offset, dimensions = 2, None
    starts = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(raw) - 2:
        _require(raw[offset] == 0xFF, "invalid JPEG header marker")
        while offset < len(raw) and raw[offset] == 0xFF:
            offset += 1
        _require(offset < len(raw), "truncated JPEG marker")
        marker = raw[offset]
        offset += 1
        _require(marker not in {0x00, 0xD8, 0xD9} and not 0xD0 <= marker <= 0xD7,
                 "unexpected JPEG header marker")
        _require(offset + 2 <= len(raw), "truncated JPEG segment")
        size = struct.unpack_from(">H", raw, offset)[0]
        _require(size >= 2 and offset + size <= len(raw) - 2, "invalid JPEG segment size")
        if marker in starts:
            _require(size >= 8, "truncated JPEG frame header")
            height, width = struct.unpack_from(">HH", raw, offset + 3)
            dimensions = (width, height)
        if marker == 0xDA:
            _require(dimensions is not None, "JPEG has no frame dimensions before scan data")
            return "image/jpeg", *dimensions
        offset += size
    raise ValueError("JPEG has no complete scan header")


def load_image(sample: dict, input_path: Path) -> tuple[dict | None, Path | None]:
    """Confine a bounded PNG/JPEG and inspect its container/header, not its raster."""
    if "image" not in sample:
        return None, None
    image = sample["image"]
    _require(isinstance(image, dict), "sample.image must be an object")
    _require(_text(image.get("path")) and _text(image.get("alt")), "image requires a relative path and alt text")
    raw_path = image["path"]
    relative = Path(raw_path)
    windows = PureWindowsPath(raw_path)
    _require(not relative.is_absolute() and not windows.drive and not windows.root
             and ":" not in raw_path and ".." not in windows.parts and ".." not in relative.parts,
             "image must be a relative local path without traversal")
    _require(relative.suffix.lower() in {".png", ".jpg", ".jpeg"}, "only PNG/JPEG images are supported")
    root = input_path.parent.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    _require(path.is_relative_to(root) and path.is_file(), "image escapes the input directory or is not a file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_IMAGE_BYTES + 1)
    _require(len(raw) <= MAX_IMAGE_BYTES, "image exceeds 4 MiB")
    mime, width, height = _dimensions(raw, relative.suffix.lower())
    _require(width > 0 and height > 0 and width * height <= MAX_IMAGE_PIXELS,
             "image dimensions must be positive and at most 16,000,000 pixels")
    return {"src": f"data:{mime};base64," + base64.b64encode(raw).decode("ascii"),
            "alt": image["alt"], "width": width, "height": height}, path


class _NativeMedia:
    """Read confined proof bytes once; count every resulting image embed."""

    def __init__(self, input_path: Path) -> None:
        self.root = input_path.parent.resolve(strict=True)
        self.paths: set[Path] = {input_path.resolve(strict=True)}
        self.images: dict[tuple, dict] = {}
        self.sources: dict[tuple, str] = {}
        self.embedded_bytes = 0

    def _path(self, value: str, suffixes: set[str]) -> tuple[Path, tuple]:
        relative, windows = Path(value), PureWindowsPath(value)
        _require(not relative.is_absolute() and not windows.drive and not windows.root
                 and ":" not in value and ".." not in relative.parts and ".." not in windows.parts,
                 "asset must be a relative local path without traversal")
        _require(relative.suffix.lower() in suffixes, "unsupported image or native source format")
        lexical = self.root / relative
        current = lexical
        while True:
            metadata = current.lstat()
            _require(not current.is_symlink() and not getattr(metadata, "st_file_attributes", 0) & 0x400,
                     "asset links are not confined proof files")
            if current == self.root:
                break
            current = current.parent
        path = lexical.resolve(strict=True)
        _require(path.is_relative_to(self.root) and path.is_file(), "asset escapes input directory or is not a file")
        self.paths.add(path)
        metadata = path.stat()
        identity = ((metadata.st_dev, metadata.st_ino) if metadata.st_ino else (str(path),))
        return path, identity

    def image(self, reference: dict) -> dict:
        path, identity = self._path(reference["path"], {".png", ".jpg", ".jpeg"})
        if identity not in self.images:
            with path.open("rb") as stream:
                raw = stream.read(MAX_IMAGE_BYTES + 1)
            _require(len(raw) <= MAX_IMAGE_BYTES, "image exceeds 4 MiB")
            mime, width, height = _dimensions(raw, path.suffix.lower())
            _require(width > 0 and height > 0 and width * height <= MAX_IMAGE_PIXELS,
                     "image dimensions must be positive and at most 16,000,000 pixels")
            self.images[identity] = {
                "src": f"data:{mime};base64," + base64.b64encode(raw).decode("ascii"),
                "width": width, "height": height, "mime": mime,
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            }
        image = self.images[identity]
        expected_mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        _require(image["mime"] == expected_mime, "image suffix differs from its container")
        _require(image["sha256"] == reference["sha256"].lower(), "image SHA-256 differs from retained bytes")
        self.embedded_bytes += image["bytes"]
        _require(self.embedded_bytes <= MAX_EMBEDDED_BYTES, "embedded images exceed 16 MiB")
        return {"src": image["src"], "alt": reference["alt"], "width": image["width"], "height": image["height"]}

    def native(self, provenance: dict, output: str) -> None:
        path, identity = self._path(provenance["source"], {"." + output})
        if identity not in self.sources:
            _require(path.stat().st_size <= MAX_NATIVE_BYTES, "native source exceeds 64 MiB")
            digest, size = hashlib.sha256(), 0
            with path.open("rb") as stream:
                while chunk := stream.read(min(1024 * 1024, MAX_NATIVE_BYTES - size + 1)):
                    size += len(chunk)
                    _require(size <= MAX_NATIVE_BYTES, "native source exceeds 64 MiB")
                    digest.update(chunk)
            self.sources[identity] = digest.hexdigest()
        _require(self.sources[identity] == provenance["source_sha256"].lower(),
                 "native source SHA-256 differs from retained bytes")


def _load_native_media(document: dict, input_path: Path) -> tuple[_NativeMedia, dict | None, dict]:
    media = _NativeMedia(input_path)
    sample_image = media.image(document["sample"]["image"]) if "image" in document["sample"] else None
    images: dict[str, dict[str, list[dict]]] = {}
    for candidate in document["candidates"]:
        images[candidate["id"]] = {}
        for output, preview in candidate["previews"].items():
            images[candidate["id"]][output] = []
            for frame in preview["frames"]:
                media.native(frame["provenance"], output)
                images[candidate["id"]][output].append(media.image(frame))
    return media, sample_image, images


CSS = """
:root{color-scheme:light;font-family:system-ui,sans-serif;color:#202733;background:#eef0f3}
*{box-sizing:border-box}body{margin:0;padding:clamp(16px,3vw,48px)}
main{max-width:1800px;margin:auto}h1{font-size:clamp(24px,3vw,40px);margin:0 0 12px}
.intro{max-width:90ch;line-height:1.6}.notice{padding:16px;border:1px solid #697386;background:white}
nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}nav a{color:#193c76;background:white;padding:12px 16px;border:1px solid;border-radius:4px}
a:focus-visible,[tabindex]:focus-visible{outline:3px solid #193c76;outline-offset:4px}
.proposals{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:24px;align-items:start}
.proposal{background:white;border:2px solid #c7ced8;padding:clamp(12px,2vw,24px);scroll-margin-top:20px;min-width:0}
.proposal:target{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent)}
.proposal>header h2{font-size:24px;margin:4px 0 8px}.proposal>header p,.decisions{line-height:1.5}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.swatches{display:flex;height:16px;margin:16px 0}.swatch{min-width:4px}
.decisions{font-size:13px;color:#4d5664}.format-label{font-size:12px;font-weight:700;margin:24px 0 8px}
.frame{background:var(--background);color:var(--ink);font-family:var(--body-family);font-weight:var(--body-weight);padding:calc(var(--unit)*var(--step-large));line-height:var(--leading);overflow-wrap:anywhere;border:1px solid var(--muted)}
.frame.docx{max-width:43rem;margin-inline:auto}.frame.pptx{width:100%;min-height:24rem}
.frame h3{font-family:var(--heading-family);font-weight:var(--heading-weight);font-size:clamp(22px,2.4vw,34px);line-height:1.12;margin:var(--unit) 0 calc(var(--unit)*var(--step-middle));text-align:var(--title-align)}
.frame .body{font-size:15px;white-space:pre-line;margin:calc(var(--unit)*var(--step-middle)) 0}
.frame .lead{font-size:17px;padding:calc(var(--unit)*var(--step-small));margin:calc(var(--unit)*var(--step-middle)) 0}
.frame .rule{border-left:4px solid var(--accent);padding-left:calc(var(--unit)*var(--step-middle))}
.frame .panel{background:var(--surface);border:1px solid var(--accent);border-radius:4px}
.frame .caption,.frame .section-label{font-family:var(--caption-family);font-weight:var(--caption-weight);color:var(--muted);font-size:12px}
.frame .section-label{letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--accent);padding-bottom:var(--unit)}
.frame .source{border-top:1px solid var(--muted);margin-top:calc(var(--unit)*var(--step-section));padding-top:var(--unit)}
.table-scroll{overflow-x:auto;margin:calc(var(--unit)*2) 0}.frame table{border-collapse:collapse;width:100%;font-size:13px}
.frame th,.frame td{padding:var(--unit);text-align:left;vertical-align:top}.frame th{color:var(--accent);font-weight:700}
.frame .ruled tr{border-bottom:1px solid var(--muted)}.frame .ruled thead{border-bottom:2px solid var(--accent)}
.frame .striped tbody tr:nth-child(odd){background:var(--surface)}.frame .striped thead{border-bottom:2px solid var(--accent)}
.frame figure{margin:calc(var(--unit)*2) 0}.frame img{display:block;max-width:100%;height:auto;max-height:180px;object-fit:contain;object-position:left}
.frame .monochrome img{filter:grayscale(1)}.frame figcaption{margin-top:var(--unit)}
footer{margin:32px 0 0;max-width:100ch;line-height:1.6;font-size:13px}
@media(max-width:600px){body{padding:12px}.proposal{padding:12px}.frame{padding:16px}.frame h3{font-size:26px}.frame.pptx{min-height:0}}
@media(prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""


def _font(role: dict) -> str:
    generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
    return ",".join(name if name in generic else f'"{name}"' for name in [role["family"], *role["fallbacks"]])


def _candidate_css(candidate: dict, index: int) -> str:
    design = candidate["design"]
    properties = [f"--{role}:{design['palette'][role]}" for role in ("background", "surface", "ink", "accent", "muted")]
    for role in ("heading", "body", "caption"):
        properties.extend((f"--{role}-family:{_font(design['typography'][role])}",
                           f"--{role}-weight:{design['typography'][role]['weight']}"))
    properties.extend((f"--unit:{design['spacing']['unit']}px",
                       "--leading:" + {"compact": "1.35", "comfortable": "1.55", "spacious": "1.75"}[design["spacing"]["density"]],
                       "--title-align:" + {"left-aligned": "left", "centered": "center"}[design["components"]["title"]]))
    scale = design["spacing"]["scale"]
    properties.extend(f"--step-{name}:{scale[min(position, len(scale) - 1)]}"
                      for name, position in (("small", 0), ("middle", 1), ("large", 2), ("section", len(scale) - 1)))
    return f"#proposal-{index}" + "{" + ";".join(properties) + "}"


def _frame(sample: dict, candidate: dict, output: str, image: dict | None) -> str:
    design = candidate["design"]
    table = sample["table"]
    headings = "".join(f"<th scope=\"col\">{escape(value)}</th>" for value in table["headers"])
    rows = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>" for row in table["rows"])
    picture = ""
    if image:
        picture = (f'<figure class="{design["imagery"]["treatment"]}"><img src="{image["src"]}" '
                   f'alt="{escape(image["alt"], quote=True)}" width="{image["width"]}" height="{image["height"]}">'
                   f'<figcaption class="caption">{escape(image["alt"])}</figcaption></figure>')
    return (f'<p class="format-label">{output.upper()} reading sample</p>'
            f'<section class="frame {output}" data-format="{output}" data-candidate-id="{escape(candidate["id"], quote=True)}" '
            f'aria-label="{escape(candidate["id"], quote=True)} {output.upper()} sample">'
            f'<p class="section-label">{escape(sample["source_note"])}</p>'
            f'<h3>{escape(sample["title"])}</h3>{picture}'
            f'<p class="lead {design["components"]["callout"]}">{escape(sample["lead"])}</p>'
            f'<p class="body">{escape(sample["body"])}</p>'
            f'<div class="table-scroll" tabindex="0" role="region" aria-label="Source-backed comparison table">'
            f'<table class="{design["data"]["table"]}"><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="caption source">{escape(sample["source_note"])}</p></section>')


def render(document: dict, image: dict | None) -> str:
    """Fixed presentation code renders only validated, shared real sample data."""
    navigation, proposals, styles = [], [], []
    for index, candidate in enumerate(document["candidates"], 1):
        design = candidate["design"]
        name = design["direction"]["name"]
        navigation.append(f'<a href="#proposal-{index}">{escape(name)}</a>')
        styles.append(_candidate_css(candidate, index))
        principles = "".join(f"<li>{escape(value)}</li>" for value in design["direction"]["principles"])
        swatches = "".join(f'<span class="swatch" style="background:{design["palette"][role]};flex:{fraction}" '
                           f'title="{role}: {design["palette"][role]}"></span>'
                           for role, fraction in design["palette"]["proportions"].items()
                           if role in {"background", "surface", "ink", "accent"})
        parents = ("<p>Authored from: " + escape(", ".join(candidate["parent_ids"])) + ".</p>"
                   if "parent_ids" in candidate else "")
        frames = "".join(_frame(document["sample"], candidate, output, image) for output in document["formats"])
        proposals.append(f'<article id="proposal-{index}" class="proposal"><header>'
                         f'<p class="eyebrow">Proposal {index}: {escape(candidate["id"])}</p><h2>{escape(name)}</h2>'
                         f'<p>{escape(design["direction"]["idea"])}</p><ul>{principles}</ul>{parents}'
                         f'<div class="swatches" aria-label="Authored colour proportions">{swatches}</div>'
                         '<p class="decisions">Fonts use local availability and the recorded fallbacks. '
                         'The sample demonstrates type, spacing, imagery when supplied, evidence and table treatment. '
                         'Chart and quote recipes remain unexercised because this sample supplies neither.</p>'
                         f'</header>{frames}</article>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
            'img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<title>Office visual-system comparison</title><style>' + CSS + "\n" + "\n".join(styles) + '</style></head>'
            '<body><main><h1>Office visual-system comparison</h1><p class="intro">'
            'Compare complete visual proposals on identical supplied content. Each proposal shows only the requested formats. '
            'Use the links to move between proposals with the keyboard.</p>'
            f'<p class="notice">{escape(NOTICE)}</p><nav aria-label="Compare proposals">' + "".join(navigation) + '</nav>'
            '<div class="proposals">' + "".join(proposals) + '</div>'
            '<footer>Selection is a separate action: record the chosen candidate, decision authority and decision source '
            'through the explicit selection command. This page saves no decision. PNG/JPEG inspection covers bounded '
            'headers and container structure; full image decoding and visual quality are separate evidence.</footer>'
            '</main></body></html>')


NATIVE_CSS = """
:root{color-scheme:light;font-family:system-ui,sans-serif;color:#202733;background:#eef0f3}
*{box-sizing:border-box}body{margin:0;padding:clamp(12px,3vw,40px)}
main{max-width:1800px;margin:auto}h1{font-size:clamp(24px,3vw,38px)}
p,li,summary{line-height:1.5}nav{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}
nav a{color:#193c76;background:white;padding:12px 16px;border:1px solid;border-radius:4px}
a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #193c76;outline-offset:4px}
.notice,.sample,.proposal{background:white;border:1px solid #697386;padding:clamp(12px,2vw,24px);min-width:0}
.sample{max-width:90ch;margin:24px 0}.sample .body{white-space:pre-wrap}
.proposals{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:24px;align-items:start}
.proposal:target{outline:3px solid #193c76}.proposal{scroll-margin-top:20px}
figure{margin:20px 0}img{display:block;max-width:100%;height:auto}
figcaption{font-size:14px;line-height:1.5;margin-top:8px;overflow-wrap:anywhere}
details{margin-top:12px;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:600}
dl{font-size:13px}dt{font-weight:600}dd{margin:0 0 8px}
.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%}
th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #697386}
footer{margin-top:24px;max-width:100ch;line-height:1.5}
"""


def _picture(image: dict) -> str:
    return (f'<img src="{image["src"]}" alt="{escape(image["alt"], quote=True)}" '
            f'width="{image["width"]}" height="{image["height"]}">')


def _lineage_details(entries: list[dict], title: str) -> str:
    items = "".join(f'<li>{escape(entry["id"])}: {escape(entry["provenance"])} '
                    f'({escape(entry["sha256"])})</li>' for entry in entries)
    return f'<details><summary>{escape(title)}</summary><ul>{items}</ul></details>' if entries else ""


def _readable_sample(document: dict, image: dict | None) -> str:
    sample = document["sample"]
    picture = f'<figure>{_picture(image)}<figcaption>{escape(image["alt"])}</figcaption></figure>' if image else ""
    table = sample["table"]
    tabular = ""
    if table is not None:
        headings = "".join(f'<th scope="col">{escape(value)}</th>' for value in table["headers"])
        rows = "".join('<tr>' + "".join(f'<td>{escape(value)}</td>' for value in row) + '</tr>' for row in table["rows"])
        tabular = ('<div class="table-scroll" tabindex="0" role="region" aria-label="Source-backed sample table">'
                   f'<table><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table></div>')
    evidence = "".join('<li>' + escape(item["text"]) + ' ('
                       + escape("; ".join(ref["source_id"] + ": " + ref["locator"] for ref in item["source_refs"]))
                       + ')</li>' for item in sample["evidence"])
    reasons = "".join(f'<p>{escape(job)}: {escape(reason)}</p>' for job, reason in sample.get("not_applicable", {}).items())
    return ('<section class="sample" aria-label="Common real-content sample">'
            f'<h2>{escape(sample["title"])}</h2><p>{escape(sample["lead"])}</p>{picture}'
            f'<p class="body">{escape(sample["body"])}</p>{tabular}<ul>{evidence}</ul>'
            f'<p>{escape(sample["source_note"])}</p>{reasons}'
            + _lineage_details(document["sources"], "Sample source lineage") + '</section>')


def _render_native_comparison(document: dict, sample_image: dict | None, images: dict) -> str:
    """Show the retained proof pixels; gallery layout never authors their design."""
    navigation, proposals = [], []
    for index, candidate in enumerate(document["candidates"], 1):
        design = candidate["design"]
        navigation.append(f'<a href="#proposal-{index}">{escape(design["direction"]["name"])}</a>')
        formats = []
        for output in document["formats"]:
            preview = candidate["previews"][output]
            frames = []
            for frame, image in zip(preview["frames"], images[candidate["id"]][output]):
                provenance = frame["provenance"]
                details = "".join(f'<dt>{escape(field)}</dt><dd>{escape(value)}</dd>'
                                  for field, value in provenance.items())
                frames.append(f'<figure>{_picture(image)}<figcaption>{escape(frame["slot_id"])}: '
                              f'{escape(frame["alt"])}</figcaption><details><summary>Proof provenance</summary>'
                              f'<dl>{details}<dt>image_sha256</dt><dd>{escape(frame["sha256"])}</dd></dl>'
                              '</details></figure>')
            formats.append(f'<section data-format="{output}" data-candidate-id="{escape(candidate["id"], quote=True)}" '
                           f'aria-label="{output.upper()} samples"><h3>{output.upper()} samples</h3>'
                           + "".join(frames) + _lineage_details(preview["assets"], "Asset lineage") + '</section>')
        principles = "".join(f'<li>{escape(value)}</li>' for value in design["direction"]["principles"])
        parents = '<p>Authored from: ' + escape(", ".join(candidate["parent_ids"])) + '.</p>' if "parent_ids" in candidate else ""
        proposals.append(f'<article class="proposal" id="proposal-{index}"><h2>{escape(design["direction"]["name"])}</h2>'
                         f'<p>{escape(candidate["id"])}</p><p>{escape(design["direction"]["idea"])}</p>'
                         f'<ul>{principles}</ul>{parents}' + "".join(formats) + '</article>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; '
            'style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            '<title>Office native-proposal comparison</title><style>' + NATIVE_CSS + '</style></head>'
            '<body><main><h1>Office native-proposal comparison</h1>'
            '<p class="notice">Compare the saved sample images below at their original proportions. '
            'These previews do not establish editability or final Office quality; independent checks '
            'are still required. Use the links to compare; choosing a design is a separate step.</p>'
            + _readable_sample(document, sample_image)
            + '<nav aria-label="Compare proposals">' + "".join(navigation) + '</nav>'
            + '<div class="proposals">' + "".join(proposals) + '</div>'
            '<footer>Read the shared content above, compare each proposal, then record your choice '
            'separately. The gallery displays the saved images as supplied; it does not change '
            'their design. The source files and final Office results still need independent review.</footer>'
            '</main></body></html>')


def publish_html(html: str, path: Path) -> None:
    """Publish complete bytes without replacing any existing artifact."""
    _require(not path.exists() and not path.is_symlink(), f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".office-compare-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(html.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        if os.name == "nt":
            os.rename(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--select")
    parser.add_argument("--authority", choices=("user", "autonomous"))
    parser.add_argument("--source")
    args = parser.parse_args(argv)
    try:
        document = records.load_record(args.input)
        validate_comparison(document)
        native = document["schema"] == "office/design-candidates/v2"
        if native:
            media, image, images = _load_native_media(document, args.input)
            sources = media.paths
        else:
            image, image_path = load_image(document["sample"], args.input)
            sources = (args.input, image_path)
        for source in sources:
            if source is not None:
                _require(args.out.resolve() != source.resolve()
                         and not (args.out.exists() and args.out.samefile(source)),
                         "output must differ from the input and its assets")
        if args.select is not None:
            _require(_text(args.select) and args.authority is not None and _text(args.source),
                     "selection requires a candidate ID, authority and decision source")
            candidate = next((item for item in document["candidates"] if item["id"] == args.select), None)
            _require(candidate is not None, "unknown selected candidate")
            selected = copy.deepcopy(candidate["design"])
            selected["selection"] = {"candidate_id": candidate["id"], "authority": args.authority, "source": args.source}
            if "parent_ids" in candidate:
                selected["selection"]["parent_ids"] = copy.deepcopy(candidate["parent_ids"])
            if native:
                selected["selection"]["preview"] = {
                    "comparison_sha256": _canonical_digest(document), "hash_mode": "canonical-json-v1",
                    "sample_sha256": _canonical_digest(document["sample"]),
                    "design_sha256": _canonical_digest(candidate["design"]),
                    "frames": {output: [{"slot_id": frame["slot_id"], "sha256": frame["sha256"]}
                                         for frame in preview["frames"]]
                               for output, preview in candidate["previews"].items()},
                }
            records.write_record(selected, args.out)
        else:
            _require(args.authority is None and args.source is None, "authority/source require --select")
            html = _render_native_comparison(document, image, images) if native else render(document, image)
            publish_html(html, args.out)
        print(json.dumps({"ok": True, "output": str(args.out), "selected": args.select,
                          "scope": "explicit design selection" if args.select is not None else "HTML preview only"}))
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError, struct.error) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
