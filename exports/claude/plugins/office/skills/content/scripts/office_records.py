#!/usr/bin/env python3
"""Load, validate and safely serialize shared Office editorial/design records.

Validation establishes structural bindings, not source fidelity or saved-Office
quality. PPTX pattern, capacity and native-object checks stay with the plan owner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


MAX_BYTES = 4 * 1024 * 1024
FORMATS = {"docx", "pptx"}
MODES = {"verbatim", "copyedit", "restructure", "rewrite", "summarize", "synthesize", "expand"}
AUTHORITIES = {"user", "autonomous"}
HASH_MODE = "canonical-json-v1"


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _number(value: Any) -> bool:
    return type(value) is int or type(value) is float and math.isfinite(value)


def _choice(value: Any, choices: set[str] | dict) -> bool:
    return isinstance(value, str) and value in choices


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def _safe_label(value: Any) -> bool:
    # Style names are data tokens, never arbitrary CSS declarations.
    return _text(value) and re.fullmatch(r"[\w][\w .-]*", value, re.UNICODE) is not None


def _object(value: Any, path: str, errors: list[str]) -> dict:
    if isinstance(value, dict):
        return value
    errors.append(f"{path}: expected an object")
    return {}


def _list(value: Any, path: str, errors: list[str], *, nonempty: bool = False) -> list:
    if isinstance(value, list) and (value or not nonempty):
        return value
    errors.append(f"{path}: expected {'a nonempty' if nonempty else 'a'} list")
    return []


def _texts(record: dict, fields: tuple[str, ...], path: str, errors: list[str]) -> None:
    for field in fields:
        if not _text(record.get(field)):
            errors.append(f"{path}.{field}: required nonempty text")


def _strings(value: Any, path: str, errors: list[str], *, nonempty: bool = False) -> list[str]:
    items = _list(value, path, errors, nonempty=nonempty)
    if any(not _text(item) for item in items):
        errors.append(f"{path}: entries must be nonempty text")
    return [item for item in items if _text(item)]


def _ids(value: Any, path: str, errors: list[str], *, key: str = "id") -> dict[str, dict]:
    found = {}
    for index, item in enumerate(_list(value, path, errors, nonempty=True)):
        item = _object(item, f"{path}[{index}]", errors)
        identity = item.get(key)
        if not _text(identity):
            errors.append(f"{path}[{index}].{key}: required stable ID")
        elif identity in found:
            errors.append(f"{path}: duplicate {key} {identity!r}")
        else:
            found[identity] = item
    return found


def _refs(value: Any, known: dict, path: str, errors: list[str], *, nonempty: bool = True) -> list[str]:
    items = _strings(value, path, errors, nonempty=nonempty)
    if len(set(items)) != len(items):
        errors.append(f"{path}: duplicate reference")
    for identity in items:
        if identity not in known:
            errors.append(f"{path}: unknown ID {identity!r}")
    return items


def _formats(value: Any, path: str, errors: list[str]) -> set[str]:
    items = _strings(value, path, errors, nonempty=True)
    if len(set(items)) != len(items) or any(item not in FORMATS for item in items):
        errors.append(f"{path}: use unique docx/pptx formats")
    return set(items) & FORMATS


def _identity(record: Any, schema: str, errors: list[str]) -> dict:
    record = _object(record, "record", errors)
    if record.get("schema") != schema:
        errors.append(f"schema: expected {schema}")
    _texts(record, ("project_id",), "record", errors)
    if not _positive_int(record.get("revision")):
        errors.append("revision: expected a positive integer")
    try:
        json.dumps(record, allow_nan=False)
    except (ValueError, TypeError, RecursionError, OverflowError):
        errors.append("record: expected finite, serializable JSON data")
    return record


def validate_content(record: dict, *, pptx_plan: dict | None = None) -> list[str]:
    """Return structural errors without modifying the content record or plan."""
    errors: list[str] = []
    record = _identity(record, "office/content/v1", errors)
    revision = record.get("revision")
    brief = _object(record.get("brief"), "brief", errors)
    _texts(brief, ("operation", "intent", "goal", "audience", "market", "channel", "scope",
                   "depth", "extent", "density", "tone"), "brief", errors)
    formats = _formats(brief.get("formats"), "brief.formats", errors)
    if not _choice(brief.get("transformation"), MODES):
        errors.append("brief.transformation: unknown mode")
    sources = _ids(record.get("sources"), "sources", errors)
    for identity, source in sources.items():
        _texts(source, ("path", "role"), f"source {identity}", errors)
        if not _digest(source.get("sha256")):
            errors.append(f"source {identity}.sha256: expected a SHA-256 digest")
    claims = _ids(record.get("claims"), "claims", errors)
    for identity, claim in claims.items():
        path = f"claim {identity}"
        _texts(claim, ("text",), path, errors)
        if not _choice(claim.get("priority"), {"core", "supporting", "optional"}):
            errors.append(f"{path}.priority: expected core, supporting or optional")
        if type(claim.get("locked")) is not bool:
            errors.append(f"{path}.locked: expected a boolean")
        for field in ("conditions", "conflicts"):
            _strings(claim.get(field), f"{path}.{field}", errors)
        for index, reference in enumerate(_list(claim.get("sources"), f"{path}.sources", errors, nonempty=True)):
            reference = _object(reference, f"{path}.sources[{index}]", errors)
            if not _choice(reference.get("source_id"), sources):
                errors.append(f"{path}.sources[{index}]: unknown source ID")
            _texts(reference, ("locator",), f"{path}.sources[{index}]", errors)
    units = _ids(record.get("units"), "units", errors)
    unit_claims: dict[str, list[str]] = {}
    locked_units: set[str] = set()
    for identity, unit in units.items():
        path = f"unit {identity}"
        _texts(unit, ("message", "text", "relationship", "detail"), path, errors)
        refs = _refs(unit.get("claim_ids"), claims, f"{path}.claim_ids", errors)
        unit_claims[identity] = refs
        if not _choice(unit.get("transformation"), MODES):
            errors.append(f"{path}.transformation: unknown mode")
        for claim_id in refs:
            claim = claims.get(claim_id, {})
            if claim.get("locked") is True:
                locked_units.add(identity)
                if unit.get("transformation") != "verbatim" or unit.get("text") != claim.get("text"):
                    errors.append(f"{path}: locked claim {claim_id!r} requires verbatim text and mode")
    sequence = _refs(record.get("sequence"), units, "sequence", errors)
    if set(sequence) != set(units):
        errors.append("sequence: include every unit exactly once")
    projections = _object(record.get("projections"), "projections", errors)
    if set(projections) != formats:
        errors.append("projections: keys must match requested formats exactly")
    destinations: dict[str, dict[str, dict]] = {}
    coverage: dict[str, set[str]] = {}
    for output in sorted(formats):
        projection = _object(projections.get(output), f"projections.{output}", errors)
        if type(projection.get("content_revision")) is not int or projection.get("content_revision") != revision:
            errors.append(f"projections.{output}.content_revision: stale or invalid revision")
        if output == "docx":
            _texts(projection, ("structure",), "projections.docx", errors)
            placements = _ids(projection.get("sections"), "projections.docx.sections", errors)
            for identity, section in placements.items():
                _texts(section, ("title",), f"section {identity}", errors)
        else:
            binding = _object(projection.get("plan"), "projections.pptx.plan", errors)
            _texts(binding, ("path",), "projections.pptx.plan", errors)
            if not _digest(binding.get("sha256")):
                errors.append("projections.pptx.plan.sha256: expected a SHA-256 digest")
            if binding.get("hash_mode") != HASH_MODE:
                errors.append(f"projections.pptx.plan.hash_mode: expected {HASH_MODE}")
            placements = _ids(projection.get("placements"), "projections.pptx.placements", errors, key="slide_id")
        destinations[output] = placements
        coverage[output] = set()
        for identity, placement in placements.items():
            refs = _refs(placement.get("unit_ids"), units, f"{output} {identity}.unit_ids", errors)
            for unit_id in refs:
                coverage[output].update(unit_claims.get(unit_id, []))
    excluded = set()
    for index, exclusion in enumerate(_list(record.get("exclusions"), "exclusions", errors)):
        path = f"exclusions[{index}]"
        exclusion = _object(exclusion, path, errors)
        claim_id, output = exclusion.get("claim_id"), exclusion.get("format")
        _texts(exclusion, ("reason", "source"), path, errors)
        if (not _choice(claim_id, claims) or not _choice(output, formats)
                or not _choice(exclusion.get("authority"), AUTHORITIES)):
            errors.append(f"{path}: requires a known claim, requested format and explicit authority")
        elif _text(exclusion.get("reason")) and _text(exclusion.get("source")):
            key = (claim_id, output)
            if key in excluded:
                errors.append(f"{path}: duplicate exclusion")
            excluded.add(key)
    for output in formats:
        for claim_id, claim in claims.items():
            if claim.get("priority") == "core" and claim_id not in coverage[output] and (claim_id, output) not in excluded:
                errors.append(f"{output}: core claim {claim_id!r} has no destination or authorized exclusion")
    for index, transformation in enumerate(_list(record.get("transformations"), "transformations", errors)):
        path = f"transformations[{index}]"
        transformation = _object(transformation, path, errors)
        unit_id = transformation.get("unit_id")
        if not _choice(unit_id, units):
            errors.append(f"{path}.unit_id: unknown unit")
        mode = transformation.get("mode")
        if not _choice(mode, MODES) or _choice(unit_id, locked_units) and mode != "verbatim":
            errors.append(f"{path}.mode: unknown mode or attempted change to locked text")
        if _choice(unit_id, units) and mode != units[unit_id].get("transformation"):
            errors.append(f"{path}.mode: must match the unit's transformation permission")
        _refs(transformation.get("source_ids"), sources, f"{path}.source_ids", errors)
        _texts(transformation, ("reason",), path, errors)
        destination = _object(transformation.get("destination"), f"{path}.destination", errors)
        output, identity = destination.get("format"), destination.get("id")
        placement = destinations.get(output, {}).get(identity) if _text(output) and _text(identity) else None
        if placement is None or unit_id not in placement.get("unit_ids", []):
            errors.append(f"{path}.destination: must place this unit in an existing requested-format destination")
    _strings(record.get("gaps"), "gaps", errors)
    if pptx_plan is not None:
        if "pptx" not in formats:
            errors.append("pptx_plan: no PPTX format was requested")
        else:
            _validate_plan(pptx_plan, projections.get("pptx"), revision, claims, unit_claims, errors)
    return errors


def _validate_plan(plan: Any, projection: Any, revision: Any, claims: dict,
                   unit_claims: dict[str, list[str]], errors: list[str]) -> None:
    plan = _object(plan, "pptx_plan", errors)
    projection = projection if isinstance(projection, dict) else {}
    if type(plan.get("content_revision")) is not int or plan.get("content_revision") != revision:
        errors.append("pptx_plan.content_revision: stale or invalid revision")
    try:
        payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        binding = projection.get("plan")
        declared = binding.get("sha256") if isinstance(binding, dict) else None
        if not _digest(declared) or digest != declared.lower():
            errors.append("pptx_plan: canonical JSON digest differs from the content binding")
    except (TypeError, ValueError, RecursionError, OverflowError):
        errors.append("pptx_plan: expected finite, serializable JSON data")
    slides = _ids(plan.get("slides"), "pptx_plan.slides", errors)
    slide_claims = {identity: set(_refs(slide.get("claims"), claims, f"slide {identity}.claims", errors,
                                      nonempty=False)) for identity, slide in slides.items()}
    placements = _list(projection.get("placements"), "projections.pptx.placements", errors)
    for index, placement in enumerate(placements):
        placement = _object(placement, f"placements[{index}]", errors)
        slide_id = placement.get("slide_id")
        if not _choice(slide_id, slides):
            errors.append(f"placements[{index}]: unknown slide ID")
            continue
        mapped_claims = set()
        for unit_id in _strings(placement.get("unit_ids"), f"placements[{index}].unit_ids", errors):
            mapped_claims.update(unit_claims.get(unit_id, []))
        if mapped_claims != slide_claims[slide_id]:
            errors.append(f"slide {slide_id}: plan claims differ from placed unit claims")
    placed = {item.get("slide_id") for item in placements if isinstance(item, dict)
              and _text(item.get("slide_id"))}
    for slide_id, refs in slide_claims.items():
        if refs and slide_id not in placed:
            errors.append(f"slide {slide_id}: claims have no unit placement")


def _selection_preview(value: Any, errors: list[str]) -> None:
    """Check original-choice fingerprints without rebinding them to current work."""
    preview = _object(value, "selection.preview", errors)
    fields = {"comparison_sha256", "hash_mode", "sample_sha256", "design_sha256", "frames"}
    if set(preview) != fields:
        errors.append("selection.preview: expected exactly comparison/sample/design hashes, hash_mode and frames")
    for field in ("comparison_sha256", "sample_sha256", "design_sha256"):
        if not _digest(preview.get(field)):
            errors.append(f"selection.preview.{field}: expected a SHA-256 digest")
    if preview.get("hash_mode") != HASH_MODE:
        errors.append(f"selection.preview.hash_mode: expected {HASH_MODE}")
    formats = _object(preview.get("frames"), "selection.preview.frames", errors)
    if not formats or not set(formats).issubset(FORMATS):
        errors.append("selection.preview.frames: expected a nonempty docx/pptx map")
    for output, value in formats.items():
        path = f"selection.preview.frames.{output}"
        frames = _list(value, path, errors, nonempty=True)
        if len(frames) > 3:
            errors.append(f"{path}: at most three representative slots")
        seen: set[str] = set()
        for index, value in enumerate(frames):
            frame = _object(value, f"{path}[{index}]", errors)
            if set(frame) != {"slot_id", "sha256"}:
                errors.append(f"{path}[{index}]: expected exactly slot_id and sha256")
            slot = frame.get("slot_id")
            if not _text(slot) or slot in seen:
                errors.append(f"{path}[{index}].slot_id: expected populated unique text")
            else:
                seen.add(slot)
            if not _digest(frame.get("sha256")):
                errors.append(f"{path}[{index}].sha256: expected a SHA-256 digest")


def validate_design(record: dict, *, require_selected: bool = True) -> list[str]:
    """Validate complete visual decisions; proposal validation never approves one."""
    errors: list[str] = []
    record = _identity(record, "office/design/v1", errors)
    content = _object(record.get("content"), "content", errors)
    if content.get("project_id") != record.get("project_id") or not _text(content.get("project_id")):
        errors.append("content.project_id: must match this project")
    if not _positive_int(content.get("revision")):
        errors.append("content.revision: expected a positive integer")
    formats = _formats(record.get("formats"), "formats", errors)
    direction = _object(record.get("direction"), "direction", errors)
    _texts(direction, ("name", "idea"), "direction", errors)
    _strings(direction.get("principles"), "direction.principles", errors, nonempty=True)
    palette = _object(record.get("palette"), "palette", errors)
    for role in ("background", "surface", "ink", "accent", "muted"):
        if not isinstance(palette.get(role), str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", palette[role]):
            errors.append(f"palette.{role}: expected #RRGGBB")
    colours = _strings(palette.get("data"), "palette.data", errors, nonempty=True)
    if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", colour) for colour in colours):
        errors.append("palette.data: expected #RRGGBB colours")
    provenance = _object(palette.get("provenance"), "palette.provenance", errors)
    _texts(provenance, ("source", "method"), "palette.provenance", errors)
    proportions = _object(palette.get("proportions"), "palette.proportions", errors)
    values = [proportions.get(role) for role in ("background", "surface", "ink", "accent")]
    if any(not _number(value) or not 0 <= value <= 1 for value in values):
        errors.append("palette.proportions: all four roles require finite fractions from 0 to 1")
    elif not math.isclose(sum(values), 1, abs_tol=0.001):
        errors.append("palette.proportions: fractions must sum to 1")
    typography = _object(record.get("typography"), "typography", errors)
    for role in ("heading", "body", "caption"):
        font = _object(typography.get(role), f"typography.{role}", errors)
        fallbacks = _strings(font.get("fallbacks"), f"typography.{role}.fallbacks", errors, nonempty=True)
        if not _safe_label(font.get("family")) or any(not _safe_label(item) for item in fallbacks):
            errors.append(f"typography.{role}: unsafe or missing font family/fallback")
        weight = font.get("weight")
        if type(weight) is not int or not 1 <= weight <= 1000:
            errors.append(f"typography.{role}.weight: expected an integer from 1 to 1000")
    spacing = _object(record.get("spacing"), "spacing", errors)
    if not _number(spacing.get("unit")) or spacing["unit"] <= 0:
        errors.append("spacing.unit: expected a finite positive value")
    scale = _list(spacing.get("scale"), "spacing.scale", errors, nonempty=True)
    if any(not _number(value) or value <= 0 for value in scale):
        errors.append("spacing.scale: expected finite positive values")
    elif scale != sorted(set(scale)):
        errors.append("spacing.scale: expected increasing, unique values")
    if not _safe_label(spacing.get("density")):
        errors.append("spacing.density: required safe style name")
    imagery = _object(record.get("imagery"), "imagery", errors)
    _texts(imagery, ("treatment", "source_policy"), "imagery", errors)
    for owner, fields in (("data", ("table", "chart", "source_notes")),
                          ("components", ("title", "callout", "quote", "navigation"))):
        section = _object(record.get(owner), owner, errors)
        for field in fields:
            if not _safe_label(section.get(field)):
                errors.append(f"{owner}.{field}: required safe style name")
    adaptations = _object(record.get("adaptations"), "adaptations", errors)
    if set(adaptations) != formats:
        errors.append("adaptations: keys must match requested formats exactly")
    for output in sorted(formats):
        adaptation = _object(adaptations.get(output), f"adaptations.{output}", errors)
        _texts(adaptation, ("reading", "emphasis"), f"adaptations.{output}", errors)
    if require_selected or "selection" in record:
        selection = _object(record.get("selection"), "selection", errors)
        _texts(selection, ("candidate_id", "source"), "selection", errors)
        if not _choice(selection.get("authority"), AUTHORITIES):
            errors.append("selection.authority: expected user or autonomous")
        if "preview" in selection:
            _selection_preview(selection["preview"], errors)
    return errors


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite JSON number")
    return number


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _read_record(path: Path) -> tuple[dict, bytes]:
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("record exceeds 4 MiB")
    try:
        text = raw.decode("utf-8-sig").strip()
        if not text.startswith("{"):
            fences = re.findall(r"(?m)^[ \t]*(?:`{3,}|~{3,})[^\r\n]*\r?$", text)
            match = re.search(r"(?ms)^[ \t]*```json[ \t]*\r?\n(.*?)^[ \t]*```[ \t]*\r?$", text)
            if len(fences) != 2 or match is None:
                raise ValueError("expected JSON or exactly one fenced JSON object in Markdown")
            text = match.group(1)
        record = json.loads(text, object_pairs_hook=_unique_pairs, parse_float=_finite_float,
                            parse_constant=_reject_constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError(f"invalid record: {error}") from error
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")
    return record, raw


def load_record(path: Path) -> dict:
    """Read at most 4 MiB of JSON or one Markdown JSON fence, without writes."""
    return _read_record(path)[0]


def _validate(record: dict, *, pptx_plan: dict | None = None) -> list[str]:
    if record.get("schema") == "office/content/v1":
        return validate_content(record, pptx_plan=pptx_plan)
    if record.get("schema") == "office/design/v1":
        if pptx_plan is not None:
            return ["--pptx-plan applies only to a content record"]
        return validate_design(record)
    return ["schema: expected office/content/v1 or office/design/v1"]


def write_record(record: dict, path: Path) -> None:
    """Publish a complete validated Markdown record atomically, never replace."""
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    errors = _validate(record)
    if errors:
        raise ValueError("; ".join(errors))
    title = "CONTENT" if record["schema"] == "office/content/v1" else "DESIGN"
    payload = (f"# {title}\n\n```json\n" + json.dumps(record, ensure_ascii=False, indent=2,
               allow_nan=False) + "\n```\n").encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("serialized record exceeds 4 MiB")
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".office-record-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows rename refuses existing destinations. POSIX rename replaces,
        # so publish there with an atomic, no-replace hard link instead.
        if os.name == "nt":
            os.rename(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="check structural record bindings")
    validate.add_argument("input", type=Path)
    validate.add_argument("--pptx-plan", type=Path)
    write = commands.add_parser("write", help="write a new validated Markdown record")
    write.add_argument("input", type=Path)
    write.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = load_record(args.input)
        evidence = {}
        plan = None
        if args.command == "validate" and args.pptx_plan:
            plan, plan_bytes = _read_record(args.pptx_plan)
            evidence = {"pptx_plan": str(args.pptx_plan),
                        "pptx_plan_file_sha256": hashlib.sha256(plan_bytes).hexdigest()}
        errors = _validate(record, pptx_plan=plan)
        if errors:
            raise ValueError("; ".join(errors))
        if args.command == "write":
            if args.out.resolve() == args.input.resolve() or args.out.exists() and args.out.samefile(args.input):
                raise ValueError("output must differ from input")
            write_record(record, args.out)
        print(json.dumps({"ok": True, "record": str(args.input), **evidence,
                          "scope": "structural validation only"}, ensure_ascii=True))
    except (OSError, ValueError, TypeError, RecursionError, OverflowError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
