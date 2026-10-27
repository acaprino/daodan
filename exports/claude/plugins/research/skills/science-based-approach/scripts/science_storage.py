"""Confined, recoverable storage for scientific research supplied by an agent."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Callable, Iterator


class ScienceError(ValueError):
    """A rejected operation that must not be reported as successful."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def identity(value: object, field: str = "id") -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}", value):
        raise ScienceError(f"Invalid {field}: use letters, numbers, hyphens or underscores")
    return value


def text_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScienceError(f"{field} must be a nonempty string")
    return value


def timestamp(value: object, field: str) -> str:
    text = text_value(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ScienceError(f"{field} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ScienceError(f"{field} requires a timezone offset")
    return text


def revision(value: object, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ScienceError(f"Expected integer revision >= {minimum}")
    return value


def strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ScienceError(f"{field} must be an array of strings")
    return value


def no_links(path: Path, boundary: Path) -> None:
    """Match Work Controller's symlink/junction confinement contract."""
    path, boundary = path.absolute(), boundary.absolute()
    if not path.is_relative_to(boundary):
        raise ScienceError("Path escapes its declared root")
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            info = None
        if info is not None and (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400):
            raise ScienceError(f"Symlink or junction is not an owned path: {item}")
        if item == boundary:
            break


def project_home(project: str | Path) -> Path:
    """Work Controller checkout_home semantics, without installed-provider imports."""
    project = Path(project).resolve()
    if not project.is_dir():
        raise ScienceError("Project must be an existing directory")
    try:
        common = subprocess.run(["git", "-C", str(project), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True, check=False, timeout=3)
        if common.returncode:
            return project
        ignored = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", "."], capture_output=True, check=False, timeout=3)
    except FileNotFoundError:
        return project
    except subprocess.TimeoutExpired as error:
        raise ScienceError("Project identity lookup timed out; no fallback home was selected") from error
    common_path = Path(common.stdout.strip()).resolve()
    if ignored.returncode == 0 or common_path.name != ".git" or not common_path.parent.is_dir():
        return project
    return common_path.parent


def checkout_root(project: str | Path) -> Path:
    """Keep authored documents inside the caller's checkout, unlike shared state."""
    project = Path(project).resolve()
    # When the provider treats this target as its own project (ignored,
    # non-Git or nonstandard Git common-dir), archive normalization must not
    # silently choose a different preference home for the same command.
    if project_home(project) == project:
        return project
    try:
        top = subprocess.run(["git", "-C", str(project), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False, timeout=3)
        if top.returncode:
            raise ScienceError("Checkout identity changed; reread before selecting its archive")
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise ScienceError("Checkout identity lookup timed out; no fallback archive was selected") from error
    return Path(top.stdout.strip()).resolve()


def state_root(home: Path, create: bool = False) -> Path:
    root = home / ".daodan"
    no_links(root / ".daodan-root", home)
    if root.exists() and not (root / ".daodan-root").is_file() and any(root.iterdir()):
        raise ScienceError(".daodan must be dedicated and carry .daodan-root")
    if create:
        root.mkdir(exist_ok=True)
        sentinel = root / ".daodan-root"
        if not sentinel.exists():
            sentinel.touch(exist_ok=True)
    return root


def read_json(path: Path, boundary: Path) -> dict:
    no_links(path, boundary)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ScienceError(f"Cannot read JSON object: {path}") from error
    if not isinstance(value, dict):
        raise ScienceError(f"Expected JSON object: {path}")
    return value


def atomic(path: Path, data: bytes, boundary: Path, immutable: bool = False) -> None:
    no_links(path, boundary)
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if path.read_bytes() == data:
            return
        raise ScienceError(f"Immutable artifact already exists with different bytes: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=".science-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        no_links(path, boundary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def writing(home: Path) -> Iterator[None]:
    """OS locks release on process exit; a stale lock file is never a stale lock."""
    shared_home = project_home(home)
    path = state_root(shared_home, create=True) / "science.lock"
    no_links(path, shared_home)
    with path.open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ScienceError("Science state is being written by another process; retry after rereading") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def archive_path(home: Path, value: object) -> Path:
    raw = text_value(value, "path").replace("\\", "/")
    path = Path(raw)
    parts = path.parts
    if path.is_absolute() or ".." in parts or ":" in raw:
        raise ScienceError("Research path must be relative and stay within its owner")
    allowed = (len(parts) == 3 and parts[:2] == ("docs", "research")) or (
        len(parts) == 5 and parts[:2] == ("docs", "plugins") and parts[3] == "research")
    if not allowed or any(part.startswith(".") for part in parts):
        raise ScienceError("Use docs/research/<topic> or docs/plugins/<owner>/research/<topic>")
    target = home / path
    no_links(target, home)
    return target


def load_record(home: Path, directory: Path) -> dict:
    pointer = read_json(directory / "science.json", home)
    if pointer.get("schema") != "daodan/science-research/v1":
        raise ScienceError(f"Unknown research schema: {directory}")
    identity(pointer.get("id"))
    number = revision(pointer.get("revision"), 1)
    stem = f"r{number:04d}"
    metadata_path = directory / "revisions" / f"{stem}.json"
    metadata = read_json(metadata_path, home)
    if digest(metadata_path.read_bytes()) != pointer.get("metadata_digest"):
        raise ScienceError(f"Research revision metadata integrity failure: {directory}")
    if metadata.get("schema") != "daodan/science-revision/v1":
        raise ScienceError(f"Unknown revision schema: {directory}")
    for field in ("title", "question", "owner", "reason", "path", "created_at", "updated_at", "operation_id", "request_digest"):
        text_value(metadata.get(field), field)
    for field in ("created_at", "updated_at"):
        timestamp(metadata.get(field), field)
    strings(metadata.get("topics"), "topics")
    strings(metadata.get("known_consumers", []), "known_consumers")
    if metadata.get("status") not in ("current", "review-needed", "superseded"):
        raise ScienceError(f"Invalid research status: {directory}")
    document = directory / "revisions" / f"{stem}.md"
    no_links(document, home)
    try:
        actual = digest(document.read_bytes())
    except OSError as error:
        raise ScienceError(f"Missing research revision: {document}") from error
    if metadata.get("id") != pointer["id"] or metadata.get("revision") != number or actual != pointer.get("digest") or actual != metadata.get("digest"):
        raise ScienceError(f"Research revision integrity failure: {directory}")
    if metadata.get("path") != directory.relative_to(home).as_posix():
        raise ScienceError(f"Research path does not match its canonical owner: {directory}")
    return metadata


def archive_directories(home: Path) -> Iterator[Path]:
    candidates = [home / "docs" / "research"]
    plugins = home / "docs" / "plugins"
    no_links(plugins, home)
    if plugins.is_dir():
        for owner in sorted(plugins.iterdir()):
            if owner.is_dir() and not owner.is_symlink() and not getattr(owner, "is_junction", lambda: False)():
                candidates.append(owner / "research")
    for root in candidates:
        no_links(root, home)
        if not root.is_dir():
            continue
        for directory in sorted(root.iterdir()):
            if directory.is_dir() and not directory.is_symlink() and not getattr(directory, "is_junction", lambda: False)():
                no_links(directory, home)
                yield directory


def records(home: Path) -> list[dict]:
    found: dict[str, dict] = {}
    for directory in archive_directories(home):
        if (directory / "science.json").exists():
            item = load_record(home, directory)
            if item["id"] in found:
                raise ScienceError(f"Duplicate canonical research identity: {item['id']}")
            found[item["id"]] = item
    return [found[key] for key in sorted(found)]


def unpublished(home: Path) -> list[dict]:
    """Expose journals left before the atomic publication pointer was advanced."""
    result = []
    for directory in archive_directories(home):
        pointer = directory / "science.json"
        current = load_record(home, directory)["revision"] if pointer.exists() else 0
        revisions = directory / "revisions"
        no_links(revisions, home)
        for path in sorted(revisions.glob("r*.json")) if revisions.is_dir() else []:
            item = read_json(path, home)
            if item.get("schema") == "daodan/science-revision/v1" and revision(item.get("revision"), 1) > current:
                result.append({"id": item["id"], "path": directory.relative_to(home).as_posix(),
                               "revision": item["revision"], "operation_id": item["operation_id"],
                               "status": "unpublished"})
    return result


def select(home: Path, selector: str) -> list[dict]:
    rows = records(home)
    if selector.casefold() in ("all", "tutte"):
        return rows
    exact = [row for row in rows if selector == row["id"]]
    if exact:
        return exact
    normalized = selector.strip().casefold()
    if not normalized:
        raise ScienceError("A research selector is required")
    matches = [row for row in rows if normalized in " ".join([row["title"], row["question"], *row["topics"]]).casefold()]
    if not matches:
        raise ScienceError(f"No research matches: {selector}")
    if len(matches) > 1:
        raise ScienceError("Ambiguous research selector; choose one identity: " + ", ".join(row["id"] for row in matches))
    return matches


def receipts(home: Path, directory: Path) -> list[dict]:
    root = directory / "checks"
    no_links(root, home)
    result = []
    for path in sorted(root.glob("*.json")) if root.is_dir() else []:
        item = read_json(path, home)
        if item.get("schema") != "daodan/science-check/v1" or item.get("check_id") != path.stem:
            raise ScienceError(f"Invalid check receipt: {path}")
        identity(item.get("check_id"), "check_id")
        identity(item.get("research_id"), "research_id")
        revision(item.get("examined_revision"))
        if "resulting_revision" in item:
            revision(item["resulting_revision"], 1)
        timestamp(item.get("checked_at"), "checked_at")
        if item.get("status") not in ("completed-with-change", "completed-no-change", "partial", "failed", "cancelled"):
            raise ScienceError(f"Invalid receipt status: {path}")
        if "document" in item:
            text_value(item["document"], "check.document")
        result.append(item)
    return sorted(result, key=lambda item: (item["checked_at"], item["check_id"]))


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def owned_view(path: Path, body: str, home: Path, marker: str = "science") -> None:
    begin, end = f"<!-- daodan:{marker}:begin -->", f"<!-- daodan:{marker}:end -->"
    no_links(path, home)
    original = path.read_bytes() if path.exists() else b""
    b, e = begin.encode(), end.encode()
    if original.count(b) != original.count(e) or original.count(b) > 1:
        raise ScienceError(f"Malformed science index markers: {path}")
    block = (begin + "\n" + body.rstrip() + "\n" + end).encode("utf-8")
    if b in original:
        start, finish = original.index(b), original.index(e)
        if finish < start:
            raise ScienceError(f"Malformed science index marker order: {path}")
        content = original[:start] + block + original[finish + len(e):]
    else:
        content = original + (b"\n\n" if original else b"") + block + b"\n"
    if content != original:
        atomic(path, content, home)


def section(data: bytes, marker: str) -> tuple[int, int] | None:
    begin, end = f"<!-- daodan:{marker}:begin -->".encode(), f"<!-- daodan:{marker}:end -->".encode()
    if data.count(begin) != data.count(end) or data.count(begin) > 1:
        raise ScienceError("Malformed managed research markers")
    if begin not in data:
        return None
    start, finish = data.index(begin), data.index(end) + len(end)
    if finish <= start:
        raise ScienceError("Malformed managed research marker order")
    return start, finish


def scientific_bytes(data: bytes, kind: str) -> bytes | None:
    if kind == "managed":
        bounds = section(data, "science")
        return data[bounds[0]:bounds[1]] if bounds else None
    bounds = section(data, "science-state")
    if bounds is None:
        return data
    start, finish = bounds
    # owned_view adds exactly two separator newlines and one terminal newline.
    if data[max(0, start - 2):start] == b"\n\n":
        start -= 2
    if data[finish:finish + 1] == b"\n":
        finish += 1
    return data[:start] + data[finish:]


def scientific_block(document: bytes, kind: str) -> bytes:
    return document if kind == "legacy" else b"<!-- daodan:science:begin -->\n" + document + b"\n<!-- daodan:science:end -->"


def current_path(home: Path, directory: Path, value: object) -> Path:
    raw = text_value(value, "current_path").replace("\\", "/")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or ":" in raw or relative.suffix.lower() != ".md":
        raise ScienceError("current_path must be a confined relative Markdown file")
    target = home / relative
    owner_root = directory.parent
    if not target.is_relative_to(owner_root) or target == home / "docs" / "research" / "README.md":
        raise ScienceError("Current document must stay inside the same research owner root, outside the global index")
    if target.is_relative_to(directory / "revisions") or target.is_relative_to(directory / "checks"):
        raise ScienceError("Current document cannot replace immutable research history")
    no_links(target, home)
    return target


def prepare_current(home: Path, directory: Path, payload: dict, previous: dict | None, document: bytes, number: int) -> dict:
    prior_path = previous.get("current_path", previous["path"] + "/README.md") if previous else None
    name = payload.get("current_path", prior_path or directory.relative_to(home).as_posix() + "/README.md")
    target = current_path(home, directory, name)
    if prior_path and target.relative_to(home).as_posix() != prior_path:
        raise ScienceError("The current document path is immutable for this research identity")
    kind = previous.get("current_kind", "managed") if previous else ("legacy" if "current_path" in payload else "managed")
    if kind == "legacy" and not target.is_file():
        raise ScienceError("Legacy current_path must name an existing Markdown file")
    original = target.read_bytes() if target.exists() else b""
    expected = payload.get("expected_document_digest")
    if kind == "legacy" and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected)):
        raise ScienceError("Legacy publication requires expected_document_digest of the exact current file")
    if expected is not None:
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ScienceError("expected_document_digest must be a SHA-256 hex digest")
        if expected.lower() != digest(original):
            raise ScienceError("Current document changed since it was read; reread before publishing")
    before = scientific_bytes(original, kind)
    if previous and expected is None:
        prior_document = (directory / "revisions" / f"r{previous['revision']:04d}.md").read_bytes()
        if before != scientific_block(prior_document, kind):
            raise ScienceError("Current scientific content changed manually; provide its freshly read expected_document_digest")
    baseline = None
    if kind == "legacy" and previous is None:
        baseline = "r0000.md"
    elif previous and before != scientific_block((directory / "revisions" / f"r{previous['revision']:04d}.md").read_bytes(), kind):
        baseline = f"before-r{number:04d}.md"
    if baseline:
        atomic(directory / "revisions" / baseline, original, home, immutable=True)
    return {"current_path": target.relative_to(home).as_posix(), "current_kind": kind,
            "current_before_digest": digest(before) if before is not None else None,
            "current_after_digest": digest(scientific_block(document, kind)),
            "current_baseline": baseline}


def render_current(home: Path, directory: Path, item: dict, state: str) -> None:
    target = current_path(home, directory, item.get("current_path", item["path"] + "/README.md"))
    kind = item.get("current_kind", "managed")
    document = (directory / "revisions" / f"r{item['revision']:04d}.md").read_bytes()
    desired = scientific_block(document, kind)
    original = target.read_bytes() if target.exists() else b""
    actual = scientific_bytes(original, kind)
    actual_digest = digest(actual) if actual is not None else None
    if actual != desired:
        if actual_digest != item.get("current_before_digest") and not (kind == "managed" and not target.exists()):
            raise ScienceError("Current scientific content differs from the expected predecessor; preserve it and reconcile explicitly")
        if kind == "legacy":
            # Replace only validated scientific bytes; the derived state follows.
            atomic(target, document, home)
        else:
            bounds = section(original, "science")
            updated = original[:bounds[0]] + desired + original[bounds[1]:] if bounds else original + (b"\n\n" if original else b"") + desired + b"\n"
            atomic(target, updated, home)
    owned_view(target, state, home, marker="science-state")


def render_views(home: Path, only_id: str | None = None) -> list[dict]:
    """Refresh the shared index; rebuild only the granted dossier, or all explicitly."""
    rows = records(home)
    index = ["## Scientific research", "", "Generated view. Edit and publish an immutable revision through science-based-approach.", "", "| Research / topics | Question / owner | Revision | Last check / outcome | Last substantive update / status |", "|---|---|---|---|---|"]
    summaries = []
    for item in rows:
        directory = archive_path(home, item["path"])
        all_checks = receipts(home, directory)
        if any(check["research_id"] != item["id"] for check in all_checks):
            raise ScienceError(f"Receipt belongs to another research identity: {directory}")
        checks = [check for check in all_checks if check.get("resulting_revision", 0) <= item["revision"]]
        pending = [check for check in all_checks if check not in checks]
        latest = checks[-1] if checks else None
        completed = [check for check in checks if check["status"] in ("completed-no-change", "completed-with-change")]
        last_check = latest["checked_at"] if latest else None
        status = latest["status"] if latest else "not-checked"
        current = f"r{item['revision']:04d}"
        current_target = current_path(home, directory, item.get("current_path", item["path"] + "/README.md"))
        if only_id is None or item["id"] == only_id:
            revision_link = os.path.relpath(directory / "revisions" / f"{current}.md", current_target.parent).replace("\\", "/")
            body = f"## Research state\n\nIdentity: `{item['id']}`. Current revision: [{current}]({revision_link}).\n\nStatus: {item['status']}. Last substantive update: {item['updated_at']}.\n\nLast attempted check: {last_check or 'none'} ({status}). Last complete check: {completed[-1]['checked_at'] if completed else 'none'}.\n\n### Check history\n\n| Check | Time | Outcome | Examined revision | Description |\n|---|---|---|---|---|\n"
            if pending:
                body = body.replace("\n\n### Check history", "\n\nUnpublished change receipts: " + ", ".join(check["check_id"] for check in pending) + ". Resume their original publication before treating them as current.\n\n### Check history")
            for check in checks:
                check_link = os.path.relpath(directory / "checks" / f"{check['check_id']}.md", current_target.parent).replace("\\", "/")
                body += f"| [{check['check_id']}]({check_link}) | {check['checked_at']} | {check['status']} | r{check['examined_revision']:04d} | {_cell(check['summary'])} |\n"
                receipt = "# Research check\n\n" + "\n".join(f"- {key}: {_cell(value)}" for key, value in check.items() if key != "document") + "\n"
                if "document" in check:
                    receipt += "\n" + check["document"]
                atomic(directory / "checks" / f"{check['check_id']}.md", receipt.encode(), home, immutable=True)
            render_current(home, directory, item, body)
        link = os.path.relpath(current_target, home / "docs" / "research").replace("\\", "/")
        index.append(f"| [{_cell(item['title'])}]({link}) / {_cell(', '.join(item['topics']))} | {_cell(item['question'])} / {_cell(item['owner'])} | {current} | {last_check or 'none'} / {status} | {item['updated_at']} / {item['status']} |")
        summaries.append({**item, "last_checked_at": last_check, "last_check_status": status, "last_complete_check_at": completed[-1]["checked_at"] if completed else None})
    owned_view(home / "docs" / "research" / "README.md", "\n".join(index), home)
    return summaries


def make_check(payload: dict, research_id: str, number: int, stamp: str) -> dict:
    if not isinstance(payload, dict):
        raise ScienceError("check must be an object")
    check_id = identity(payload.get("id"), "check.id")
    status = payload.get("status")
    if status not in ("completed-with-change", "completed-no-change", "partial", "failed", "cancelled"):
        raise ScienceError("Invalid check status")
    check = {"schema": "daodan/science-check/v1", "check_id": check_id, "research_id": research_id,
             "examined_revision": number, "checked_at": stamp, "status": status,
             "summary": text_value(payload.get("summary"), "check.summary"),
             "coverage": strings(payload.get("coverage"), "check.coverage"),
             "limitations": strings(payload.get("limitations", []), "check.limitations")}
    if "document" in payload:
        check["document"] = text_value(payload["document"], "check.document")
    return check


def publish(home: Path, payload: dict, guard: Callable[[], dict | None] | None = None) -> dict:
    research_id = identity(payload.get("id"))
    if research_id.casefold() in ("all", "tutte"):
        raise ScienceError("Research identity cannot use an all-record selector")
    operation = identity(payload.get("operation_id"), "operation_id")
    expected = revision(payload.get("expected_revision"))
    directory = archive_path(home, payload.get("path"))
    document = text_value(payload.get("document"), "document").encode("utf-8")
    if b"<!-- daodan:science" in document:
        raise ScienceError("document must contain authored research only, excluding managed science blocks")
    status = payload.get("status", "current")
    if status not in ("current", "review-needed", "superseded"):
        raise ScienceError("Invalid research status")
    supplied = {key: text_value(payload.get(key), key) for key in ("title", "question", "owner", "reason")}
    supplied.update(topics=strings(payload.get("topics"), "topics"), known_consumers=strings(payload.get("known_consumers", []), "known_consumers"))
    parts = directory.relative_to(home).parts
    if len(parts) == 5 and supplied["owner"] != parts[2]:
        raise ScienceError("Research owner must match its plugin dossier")
    # Invocation mode is authority, not scientific content. An explicit request
    # can resume identical staged work after automatic mode was turned off.
    request_digest = digest(encoded({key: value for key, value in payload.items() if key != "automatic"}))
    if "current_path" in payload:
        current_path(home, directory, payload["current_path"])
    with writing(home):
        stopped = guard() if guard else None
        if stopped:
            return stopped
        rows = records(home)
        previous = next((row for row in rows if row["id"] == research_id), None)
        if previous and previous["path"] != directory.relative_to(home).as_posix():
            raise ScienceError("Research identity already has a different canonical path")
        if any(row["path"] == directory.relative_to(home).as_posix() and row["id"] != research_id for row in rows):
            raise ScienceError("Research path belongs to another identity")
        previous_current = previous.get("current_path", previous["path"] + "/README.md") if previous else None
        selected_current = current_path(home, directory, payload.get("current_path", previous_current or directory.relative_to(home).as_posix() + "/README.md"))
        if previous_current and selected_current != home / previous_current:
            raise ScienceError("The current document path is immutable for this research identity")
        for row in rows:
            if row["id"] != research_id and selected_current == current_path(home, archive_path(home, row["path"]), row.get("current_path", row["path"] + "/README.md")):
                raise ScienceError("Current document already belongs to another research identity")
        if previous and previous["operation_id"] == operation and previous["request_digest"] == request_digest:
            render_views(home, only_id=research_id)
            return {"status": "unchanged", "id": research_id, "revision": previous["revision"], "path": previous["path"]}
        if (previous["revision"] if previous else 0) != expected:
            raise ScienceError("Concurrent research revision; reread before publishing")
        if previous and previous["digest"] == digest(document):
            raise ScienceError("No substantive document change; append a check receipt instead")
        number = expected + 1
        stem = f"r{number:04d}"
        metadata_path = directory / "revisions" / f"{stem}.json"
        no_links(metadata_path, home)
        if metadata_path.exists():
            metadata = read_json(metadata_path, home)
            fixed = {"schema": "daodan/science-revision/v1", "id": research_id, "revision": number,
                     "path": directory.relative_to(home).as_posix(), "digest": digest(document),
                     "operation_id": operation, "request_digest": request_digest, "status": status,
                     "current_path": selected_current.relative_to(home).as_posix(), **supplied}
            if any(metadata.get(key) != value for key, value in fixed.items()):
                raise ScienceError("Unpublished revision is preserved; retry its exact operation or reconcile it explicitly")
            for field in ("created_at", "updated_at"):
                text_value(metadata.get(field), field)
            check = make_check(payload.get("check"), research_id, expected, metadata["updated_at"])
            check["resulting_revision"] = number
            if metadata.get("check") != check:
                raise ScienceError("Unpublished revision receipt failed integrity validation")
        else:
            stamp = now()
            check = make_check(payload.get("check"), research_id, expected, stamp)
            if check["status"] not in ("completed-with-change", "partial"):
                raise ScienceError("Publication requires a changed or partial evidence check")
            check["resulting_revision"] = number
            current = prepare_current(home, directory, payload, previous, document, number)
            metadata = {"schema": "daodan/science-revision/v1", "id": research_id, "revision": number,
                        "path": directory.relative_to(home).as_posix(), "digest": digest(document),
                        "operation_id": operation, "request_digest": request_digest,
                        "created_at": previous["created_at"] if previous else stamp, "updated_at": stamp,
                        "status": status, "check": check, **supplied, **current}
            atomic(metadata_path, encoded(metadata), home, immutable=True)
        atomic(directory / "revisions" / f"{stem}.md", document, home, immutable=True)
        check = metadata["check"]
        atomic(directory / "checks" / f"{check['check_id']}.json", encoded(check), home, immutable=True)
        pointer = {"schema": "daodan/science-research/v1", "id": research_id, "revision": number,
                   "digest": metadata["digest"], "metadata_digest": digest(encoded(metadata))}
        atomic(directory / "science.json", encoded(pointer), home)
        render_views(home, only_id=research_id)
        return {"status": "published", "id": research_id, "revision": number, "path": metadata["path"], "digest": metadata["digest"]}


def append_check(home: Path, payload: dict, guard: Callable[[], dict | None] | None = None) -> dict:
    research_id = identity(payload.get("id"))
    expected = revision(payload.get("expected_revision"), 1)
    with writing(home):
        stopped = guard() if guard else None
        if stopped:
            return stopped
        rows = select(home, research_id)
        if len(rows) != 1 or rows[0]["id"] != research_id:
            raise ScienceError("check requires an exact research identity")
        item = rows[0]
        if item["revision"] != expected:
            raise ScienceError("Concurrent research revision; reread before recording check")
        check = make_check(payload.get("check"), research_id, expected, now())
        if check["status"] == "completed-with-change":
            raise ScienceError("A changed result must be published with a revision")
        directory = archive_path(home, item["path"])
        target = directory / "checks" / f"{check['check_id']}.json"
        no_links(target, home)
        if target.exists():
            prior = read_json(target, home)
            if {key: value for key, value in prior.items() if key != "checked_at"} != {key: value for key, value in check.items() if key != "checked_at"}:
                raise ScienceError("Check identity already has different evidence")
            check = prior
        atomic(target, encoded(check), home, immutable=True)
        render_views(home, only_id=research_id)
        return {"status": "recorded", "id": research_id, "revision": expected, "check": check}
