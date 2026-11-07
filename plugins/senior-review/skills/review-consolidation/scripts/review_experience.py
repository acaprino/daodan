"""Review experience ledger: facts learned from verified review outcomes.

The ledger is one append-only file, `.daodan/review-experience/ledger.jsonl` of the
project home, one JSON outcome row per line (`daodan/review-outcome/v1`). Facts are
never stored: they are a pure function of the ledger, computed when `brief` reads it.

A fact about a symbol exists for a discovery member when rows from at least
`form_after` distinct (run_id, review_id) pairs, all at the same member, symbol,
review basis, body, interface and effects digests and parser fingerprint, say
FALSE_POSITIVE, PREMISE_REFUTED or USER_DISMISSED, and no row at that key says
REAL or USER_CONFIRMED. A symbol with other digests is simply not offered.

`record` derives the outcome rows of one review from the run record alone, with the rule
of `validate_review_checks` (specification D3, D4 and D7), and appends them. It reads
`<project home>/.daodan/runs/RID/work.json`: `reviews[]` (the review REV with its `jobs[]`,
`verification`, `review_basis` and `grounding.graph.bound_targets`, the roster path that
the preparation fills) and `deliveries{}` (`findings[]`, `declined[]` and `check`). It prints
`{rows_written, rows_skipped, ended_fact_ids}`.

The helper reads no source file, calls no model and never creates `.daodan` or its
sentinel. It creates `review-experience/`, the ledger and `.write-lock`, takes an
exclusive lock while appending and refuses symbolic links and reparse points.
Standard library only.

Usage:

    python review_experience.py brief --project ROOT --roster PREPARED.json [--form-after N] --out FACTS.json
    python review_experience.py record --project ROOT --run-id RID --review-id REV [--form-after N]
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import sys
import time
import uuid

LEDGER_SCHEMA = "daodan/review-outcome/v1"
FACTS_SCHEMA = "daodan/review-facts/v1"
REVIEW_BASIS = "changeset"
VERDICTS = frozenset({"REAL", "FALSE_POSITIVE", "PREMISE_REFUTED", "CONTESTED", "DECLINED_BY_FACT",
                      "USER_DISMISSED", "USER_CONFIRMED"})
FORMING = frozenset({"FALSE_POSITIVE", "PREMISE_REFUTED", "USER_DISMISSED"})
ENDING = frozenset({"REAL", "USER_CONFIRMED"})
DEFAULT_FORM_AFTER = 3
MIN_FORM_AFTER = 2
FORM_AFTER_HELP = f"reviews that form a fact (default {DEFAULT_FORM_AFTER}, minimum {MIN_FORM_AFTER})"
MAX_FACTS = 12
MAX_PREMISES = 3
PREMISE_LIMIT = 300
LOCK_WAIT = 30
GIT_WAIT = 10
REPLACE_TRIES = 5
REPLACE_WAIT = 0.05
FACTS_READ_LIMIT = 1 << 20
STORE, LEDGER, LOCK = "review-experience", "ledger.jsonl", ".write-lock"
NO_HOME = "the project home has no .daodan with a .daodan-root sentinel"
NO_LEDGER = "no review-experience ledger in the project home"
TARGET_FIELDS = ("symbol_id", "body_hash", "interface_hash", "effects_hash", "parser_fingerprint")
DIGEST_FIELDS = TARGET_FIELDS[1:4]
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")  # run_state.py:27
COUNTEREXAMPLE = re.compile(r".+:\d+")  # run_state.py:821
UNIVERSAL = re.compile(r"\b(no|never|cannot|always|only)\b", re.IGNORECASE)  # run_state.py:818
LENS_VERDICTS = {0: ("HOLDS", "REFUTED", "UNCERTAIN"), 1: ("REAL", "FALSE_POSITIVE", "UNCERTAIN"),
                 2: ("REAL", "FALSE_POSITIVE", "UNCERTAIN"), 3: ("REAL",)}  # run_state.py:731-733


class ExperienceError(ValueError):
    pass


class Unavailable(ExperienceError):
    """The ledger cannot be used here; the message is the declared gap."""


def no_links(path, boundary):
    """Refuse symlinks and Windows junctions on every owned path component."""
    current = Path(path).absolute()
    boundary = Path(boundary).absolute()
    if not current.is_relative_to(boundary):
        raise ExperienceError("Path escapes its declared root")
    for item in (current, *current.parents):
        try:
            metadata = item.lstat()
        except FileNotFoundError:
            metadata = None
        if metadata is not None and (stat.S_ISLNK(metadata.st_mode)
                                     or getattr(metadata, "st_file_attributes", 0) & 0x400):
            raise ExperienceError(f"Link is not an owned writable path: {item.name}")
        if item == boundary:
            break


def checkout_home(project):
    """The main checkout of the repository that holds the project (Work Controller's rule).

    A linked worktree therefore shares one ledger with its main checkout. Outside Git,
    for a directory the enclosing repository ignores, or when the common directory is
    not a plain `.git`, the project is its own home.
    """
    def git(*args):
        return subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False, timeout=GIT_WAIT)

    try:
        common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
        if common.returncode or not common.stdout.strip():
            return project
        ignored = git("check-ignore", "-q", ".")
    except FileNotFoundError:
        return project
    except subprocess.TimeoutExpired as error:
        raise ExperienceError("Project identity lookup timed out; no fallback home was selected") from error
    common_path = Path(common.stdout.strip()).resolve()
    if ignored.returncode == 0 or common_path.name != ".git" or not common_path.parent.is_dir():
        return project
    return common_path.parent


def locate(project):
    """The project home and the `review-experience/` path below it. Creates nothing."""
    project = Path(project).resolve()
    if not project.is_dir():
        raise ExperienceError("Project root must be a directory")
    home = checkout_home(project)
    sentinel = home / ".daodan" / ".daodan-root"
    directory = home / ".daodan" / STORE
    for path in (sentinel, directory / LEDGER, directory / LOCK):
        no_links(path, home)
    if not sentinel.is_file():
        raise Unavailable(NO_HOME)
    return home, directory


@contextmanager
def writer_lock(path, boundary):
    """One writer at a time on `path`, waiting up to LOCK_WAIT seconds for the holder."""
    no_links(path, boundary)
    if path.exists() and path.stat().st_nlink > 1:
        raise ExperienceError("Writer lock has external hardlinks; refuse to write")
    handle = path.open("a+b")
    locked = False
    try:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + LOCK_WAIT
        while not locked:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError as error:
                if error.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise ExperienceError(f"Cannot lock the review experience ledger: {error}") from error
                if time.monotonic() > deadline:
                    raise ExperienceError("Another writer holds the review experience ledger; retry") from error
                time.sleep(0.05)
        yield
    finally:
        try:
            if locked:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def fact_id(specialist_id, symbol_id, review_basis, body_hash, interface_hash, effects_hash):
    """`F-` and the first 8 hex of the SHA-256 of the compact UTF-8 JSON array of the key."""
    key = [specialist_id, symbol_id, review_basis, body_hash, interface_hash, effects_hash]
    payload = json.dumps(key, separators=(",", ":"), ensure_ascii=False)
    return "F-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def when(row):
    """The row's `recorded_at` as a POSIX timestamp."""
    return datetime.fromisoformat(row["recorded_at"]).timestamp()


def row_problem(row):
    """Why a decoded outcome row is unusable, or None. The reader and `append_rows` share it."""
    if not isinstance(row, dict) or row.get("schema") != LEDGER_SCHEMA:
        return "not a " + LEDGER_SCHEMA + " object"
    try:  # every string at any depth must encode, or brief could not write its output
        json.dumps(row, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        return "the row must be UTF-8 JSON: no unencodable string, NaN or unserializable value"
    named = ("run_id", "review_id", "specialist_id", "review_basis")
    if any(not isinstance(row.get(name), str) or not row[name] for name in named):
        return "run_id, review_id, specialist_id and review_basis must be non-empty strings"
    if row.get("verdict") not in VERDICTS:
        return "unknown verdict"
    premise = row.get("premise")
    if not isinstance(premise, str) or len(premise) > PREMISE_LIMIT:
        return f"premise must be a string of at most {PREMISE_LIMIT} characters"
    try:
        if datetime.fromisoformat(row["recorded_at"]).tzinfo is None:
            return "recorded_at must carry a time zone"
    except (KeyError, TypeError, ValueError):
        return "recorded_at must be an ISO 8601 time"
    symbol = row.get("symbol_id")
    if symbol is None:
        return None
    digests = row.get("digests")
    complete = (isinstance(symbol, str) and symbol and isinstance(digests, dict)
                and all(isinstance(digests.get(name), str) and digests[name]
                        for name in ("body_hash", "interface_hash", "effects_hash"))
                and isinstance(row.get("parser_fingerprint"), str) and row["parser_fingerprint"])
    return None if complete else "symbol_id needs its three digests and a parser_fingerprint"


def parse_rows(data):
    """The usable rows of ledger bytes and how many lines were skipped.

    A line that is not valid UTF-8 JSON, is truncated, has another schema or breaks the
    row format is skipped and counted. A row without a symbol id is valid but inert.
    """
    rows, skipped = [], 0
    for line in data.split(b"\n"):
        if not line.strip():
            continue
        try:
            row = json.loads(line.decode("utf-8"))
            problem = row_problem(row)
        except (ValueError, RecursionError):  # a deeply nested or odd line costs one count, never the run
            skipped += 1
            continue
        if problem:
            skipped += 1
        elif row.get("symbol_id") is not None:
            rows.append(row)
    return rows, skipped


def group_key(row):
    """What a fact is about: member, symbol, basis, three digests and the parser fingerprint."""
    digests = row["digests"]
    return (row["specialist_id"], row["symbol_id"], row["review_basis"], digests["body_hash"],
            digests["interface_hash"], digests["effects_hash"], row["parser_fingerprint"])


def group_rows(rows):
    groups = {}
    for row in rows:
        groups.setdefault(group_key(row), []).append(row)
    return groups


def evaluate(key, group, form_after):
    """The active fact of one key's rows as (latest forming `recorded_at`, fact), or None."""
    if any(row["verdict"] in ENDING for row in group):
        return None
    forming = sorted((row for row in group if row["verdict"] in FORMING), key=when)
    reviews = list(dict.fromkeys((row["run_id"], row["review_id"]) for row in forming))
    if len(reviews) < form_after:
        return None
    premises = list(dict.fromkeys(row["premise"] for row in reversed(forming) if row["premise"]))
    fact = {"fact_id": fact_id(*key[:6]), "symbol_id": key[1],
            "run_review_ids": [f"{run}/{review}" for run, review in reviews],
            "premises": premises[:MAX_PREMISES]}
    return when(forming[-1]), fact


def check_form_after(value):
    if not isinstance(value, int) or value < MIN_FORM_AFTER:
        raise ExperienceError(f"form_after must be an integer of at least {MIN_FORM_AFTER}")
    return value


def _dict(value):
    return value if isinstance(value, dict) else {}


def discovery_jobs(roster):
    """The prepared roster's discovery jobs as (id, members) pairs."""
    jobs = _dict(roster).get("jobs")
    found = []
    for job in jobs if isinstance(jobs, list) else ():
        members = _dict(job).get("specialist_ids")
        if (_dict(job).get("input_mode") == "discovery" and isinstance(job.get("id"), str) and job["id"]
                and isinstance(members, list)):
            members = [member for member in members if isinstance(member, str) and member]
            if members:
                found.append((job["id"], members))
    return found


def bound_targets(roster):
    """The rows of `grounding.graph.bound_targets` that carry symbol, digests and fingerprint."""
    rows = _dict(_dict(_dict(roster).get("grounding")).get("graph")).get("bound_targets")
    return [row for row in rows if all(isinstance(_dict(row).get(name), str) and row[name]
                                       for name in TARGET_FIELDS)] if isinstance(rows, list) else []


def member_facts(targets, groups, specialist, form_after):
    """A member's active facts for the bound targets: newest first, ties by fact id, at most MAX_FACTS."""
    found = {}
    for target in targets:
        key = (specialist, target["symbol_id"], REVIEW_BASIS, target["body_hash"],
               target["interface_hash"], target["effects_hash"], target["parser_fingerprint"])
        if key in groups and key not in found:
            found[key] = evaluate(key, groups[key], form_after)
    ranked = sorted((item for item in found.values() if item), key=lambda item: (-item[0], item[1]["fact_id"]))
    return [fact for _, fact in ranked[:MAX_FACTS]]


def job_facts(roster, rows, form_after):
    """The `jobs` list of FACTS.json for already parsed ledger rows."""
    check_form_after(form_after)
    groups, targets = group_rows(rows), bound_targets(roster)
    return [{"job_id": job_id,
             "members": [{"specialist_id": member, "facts": member_facts(targets, groups, member, form_after)}
                         for member in members]}
            for job_id, members in discovery_jobs(roster)]


def encode_rows(rows):
    """The ledger bytes of rows, or ExperienceError for the first row the reader could not serve.

    The encoding sits in the same guarded step as the validity check: a row nested just deep enough
    for `row_problem` can still exhaust the recursion limit of the payload encoding.
    """
    lines = []
    for row in rows:
        problem = row_problem(row)
        if problem is None:
            try:
                lines.append(json.dumps(row, separators=(",", ":")) + "\n")
            except (TypeError, ValueError, RecursionError):
                problem = "the row is nested too deeply or holds a value that is not JSON"
        if problem:
            raise ExperienceError("Refused outcome row: " + problem)
    return "".join(lines).encode("utf-8")


def append_with_ended(project, rows, form_after=DEFAULT_FORM_AFTER):
    """Append outcome rows under the exclusive lock: (how many were written, ids of the facts they ended).

    A fact is ended when it was active under the fact rule at `form_after`, over the whole ledger as the
    lock holder reads it, and a REAL or USER_CONFIRMED row of this call is at its key. The ledger is read
    only after the lock is held, so two sessions ending one fact report it once between them.

    Raises Unavailable, creating nothing, when the project home has no `.daodan/.daodan-root`;
    raises ExperienceError, writing nothing, for a malformed row, a link or a lock held past LOCK_WAIT.
    """
    check_form_after(form_after)
    rows = list(rows)
    payload = encode_rows(rows)
    home, directory = locate(project)
    if not rows:
        return 0, []
    directory.mkdir(exist_ok=True)
    ledger = directory / LEDGER
    with writer_lock(directory / LOCK, home):
        no_links(ledger, home)
        with ledger.open("a+b") as handle:
            handle.seek(0)
            existing = handle.read()
            if existing and not existing.endswith(b"\n"):
                payload = b"\n" + payload  # a truncated last line stays on its own line
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        touched = {group_key(row) for row in parse_rows(payload)[0] if row["verdict"] in ENDING}
        groups = group_rows(parse_rows(existing)[0]) if touched else {}
        # A REAL or USER_CONFIRMED row at a touched key ends the fact there, so one active before is ended now.
        ended = set()
        for key in touched & groups.keys():
            entry = evaluate(key, groups[key], form_after)
            if entry:
                ended.add(entry[1]["fact_id"])
    return len(rows), sorted(ended)


def append_rows(project, rows):
    """Append outcome rows under the exclusive lock and return how many were written."""
    return append_with_ended(project, rows)[0]


def brief(project, roster, form_after=DEFAULT_FORM_AFTER):
    """FACTS.json content: the active facts per discovery job and member, and the declared gaps."""
    check_form_after(form_after)
    rows, gaps = [], []
    if not discovery_jobs(roster):
        gaps.append("no discovery job in the prepared roster")
    elif not bound_targets(roster):
        gaps.append("no bound target in the prepared roster")
    else:
        try:
            ledger = locate(project)[1] / LEDGER
            if not ledger.is_file():
                raise Unavailable(NO_LEDGER)
            rows, skipped = parse_rows(ledger.read_bytes())
            if skipped:
                gaps.append(f"{skipped} unreadable or foreign ledger line(s) skipped")
        except ExperienceError as error:
            gaps.append(str(error))
        except OSError as error:
            gaps.append(f"the ledger cannot be read: {error}")
    return {"schema": FACTS_SCHEMA, "form_after": form_after, "gaps": gaps,
            "jobs": job_facts(roster, rows, form_after)}


def _list(value):
    return value if isinstance(value, list) else []


def repo_file(value):
    """The normalized repository-relative POSIX form of a file path, or None when it is not one."""
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        return None
    if PureWindowsPath(value).drive or ".." in PurePosixPath(value).parts:
        return None
    path = PurePosixPath(value).as_posix()
    return None if path == "." else path


def record_targets(review):
    """The bound targets of a run record's review that `record` can place a finding in, and the rows skipped.

    They are `grounding.graph.bound_targets` of the review entry. Unlike the rows `brief` reads, a usable
    row also carries a repository-relative `file` and integer `start` and `end` with `start <= end`.
    """
    rows = _dict(_dict(_dict(review).get("grounding")).get("graph")).get("bound_targets")
    usable, skipped = [], 0
    for row in map(_dict, _list(rows)):
        file, start, end = repo_file(row.get("file")), row.get("start"), row.get("end")
        if (file and all(isinstance(row.get(name), str) and row[name] for name in TARGET_FIELDS)
                and type(start) is int and type(end) is int and start <= end):
            usable.append({**row, "file": file})
        else:
            skipped += 1
    return usable, skipped


def required_gaps(gaps):
    """Whether coverage gaps hold one the protocol counts as required (run_state.py:832-839)."""
    return not isinstance(gaps, list) or any(
        not isinstance(gap, dict) or gap.get("required") is not False
        or not isinstance(gap.get("reason"), str) or not gap["reason"].strip() for gap in gaps)


def lens_check(review, deliveries, target, lens):
    """The check of one lens on one finding target when `obtain` accepts it (run_state.py:775-798), else None."""
    found = [d for d in deliveries.values()
             if isinstance(d, dict) and d.get("review") == review["id"] and isinstance(d.get("check"), dict)
             and d["check"].get("kind") == "verification" and type(d["check"].get("lens")) is int
             and d["check"]["lens"] == lens and target in _list(d["check"].get("targets"))]
    if len(found) != 1:
        return None
    result = found[0]
    check = result["check"]
    if lens == 0:
        roles = ["senior-review:premise-auditor"]
    else:
        roles = [
            role for role in _list(review.get("support"))
            if isinstance(role, str) and role.endswith(":isolated-worker")
        ] or ["general-purpose"]
    accepted = (result.get("role") in roles and result.get("status") == "delivered"
                and result.get("coverage") == "complete" and not required_gaps(result.get("gaps", []))
                and result.get("candidate") == _dict(review.get("grounding")).get("candidate")
                and check.get("input_mode") == ("full-context" if lens == 0 else "verification")
                and check.get("independent") is True and check.get("evidence")
                and check.get("verdict") in LENS_VERDICTS[lens])
    return check if accepted else None


def selected(review, finding):
    """Whether the protocol sends a finding to verification (run_state.py:806-813)."""
    severity, confidence = finding.get("severity"), finding.get("confidence")
    if not isinstance(severity, str) or type(confidence) not in (int, float) or not 0 <= confidence <= 100:
        return False
    if finding.get("introduced_by_candidate") is False:  # a changeset review: this is the only basis reached
        return False
    if review.get("verification") == "all-above-floor":
        return confidence >= 50
    return severity.lower() in ("critical", "high")


def disposition(review, deliveries, job_id, finding):
    """The verdict the checks of a selected finding give it, or None when a required check is missing or invalid.

    Lens 0 runs first when the shape is light, the premise is not independent or it holds a universal word,
    and ends the finding when it refutes the premise (run_state.py:814-824). Then a light review follows
    Lens 1; any other shape needs Lens 2 and, unless both say FALSE_POSITIVE, Lens 3, which only returns REAL.
    """
    target = {"job_id": job_id, "finding_id": finding["id"]}
    provenance, light = finding.get("premise_provenance"), review.get("shape") == "light"
    if light or provenance != "independent" or UNIVERSAL.search(str(finding.get("premise", ""))):
        premise = lens_check(review, deliveries, target, 0)
        if premise is None:
            return None
        located = premise.get("verdict") == "REFUTED" and COUNTEREXAMPLE.search(str(premise.get("counterexample", "")))
        if located and (premise.get("target") == "PREMISE"
                        or premise.get("target") == "SUPPORT" and provenance == "shared-context"):
            return "PREMISE_REFUTED"
    first = lens_check(review, deliveries, target, 1)
    if first is None:
        return None
    if light:
        return "CONTESTED" if first["verdict"] == "UNCERTAIN" else first["verdict"]
    second = lens_check(review, deliveries, target, 2)
    if second is None:
        return None
    if first["verdict"] == second["verdict"] == "FALSE_POSITIVE":
        return "FALSE_POSITIVE"
    return "REAL" if lens_check(review, deliveries, target, 3) else None


def placed(item):
    """(file, line, premise) of a finding or declined item, or None when one is missing or malformed."""
    item = _dict(item)
    file, line, premise = repo_file(item.get("file")), item.get("line"), item.get("premise")
    if file is None or type(line) is not int or not isinstance(premise, str) or not premise.strip():
        return None
    return file, line, premise


def smallest_target(targets, file, line):
    """The bound target of `file` with the smallest `start..end` that contains `line`, or None."""
    inside = [target for target in targets if target["file"] == file and target["start"] <= line <= target["end"]]
    return min(inside, key=lambda target: (target["end"] - target["start"], target["start"], target["symbol_id"]),
               default=None)


def outcome_row(base, job_id, finding_id, member, target, place, verdict, source):
    """One ledger row (section 4.1); a missing target gives a null symbol id, which never forms a fact."""
    file, line, premise = place
    return {**base, "job_id": job_id, "finding_id": finding_id, "specialist_id": member,
            "symbol_id": target["symbol_id"] if target else None,
            "digests": {name: target[name] for name in DIGEST_FIELDS} if target else None,
            "parser_fingerprint": target["parser_fingerprint"] if target else None,
            "file": file, "line": line, "verdict": verdict, "verdict_source": source,
            "premise": premise[:PREMISE_LIMIT]}


def fact_index(members, targets):
    """Fact id to (member, target) for every member of a job and every bound target; the first one wins."""
    index = {}
    for member in members:
        for target in targets:
            key = (member, target["symbol_id"], REVIEW_BASIS, *(target[name] for name in DIGEST_FIELDS))
            index.setdefault(fact_id(*key), (member, target))
    return index


def derive_rows(review, deliveries, run_id, recorded_at):
    """(rows, skipped) of one changeset review of a run record: a row per member for every decided finding
    and one per declined item. Findings the protocol did not select, or whose checks give no verdict,
    have no disposition and no row; a decided finding or declined item that cannot be placed is counted.
    """
    base = {"schema": LEDGER_SCHEMA, "recorded_at": recorded_at, "run_id": run_id, "review_id": review["id"],
            "review_basis": REVIEW_BASIS}
    targets, skipped = record_targets(review)
    jobs = {job.get("id") for job in map(_dict, _list(review.get("jobs")))}
    rows = []
    for delivery in map(_dict, deliveries.values()):
        job_id = delivery.get("job_id")
        if (delivery.get("review") != review["id"] or not isinstance(job_id, str) or job_id not in jobs
                or delivery.get("status") != "delivered"):
            continue
        members = [member for member in _list(delivery.get("specialist_ids")) if isinstance(member, str) and member]
        holders = {}
        for result in map(_dict, _list(delivery.get("member_results"))):
            member = result.get("specialist_id")
            if member in members and result.get("status") == "delivered":
                for finding_id in filter(lambda value: isinstance(value, str), _list(result.get("findings"))):
                    if member not in holders.setdefault(finding_id, []):
                        holders[finding_id].append(member)
        for finding in map(_dict, _list(delivery.get("findings"))):
            finding_id = finding.get("id")
            if not isinstance(finding_id, str) or not selected(review, finding):
                continue
            verdict = disposition(review, deliveries, job_id, finding)
            if verdict is None:
                continue
            place = placed(finding)
            target = smallest_target(targets, place[0], place[1]) if place else None
            for member in holders.get(finding_id, []):
                if place is None:
                    skipped += 1
                else:
                    rows.append(outcome_row(base, job_id, finding_id, member, target, place, verdict, "lens-rule"))
        declined = delivery.get("declined", [])
        index = fact_index(members, targets) if declined else {}
        for position, item in enumerate(declined if isinstance(declined, list) else [None], 1):
            place, fact = placed(item), _dict(item).get("fact_id")
            found = index.get(fact) if isinstance(fact, str) else None
            if place is None or found is None:
                skipped += 1
            else:
                rows.append(outcome_row(base, job_id, f"declined:{job_id}:{position}", *found, place,
                                        "DECLINED_BY_FACT", "fact"))
    return rows, skipped


def read_run_record(home, run_id):
    """The run record `<home>/.daodan/runs/<run_id>/work.json` as a dict."""
    path = home / ".daodan" / "runs" / run_id / "work.json"
    no_links(path, home)
    try:
        work = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as error:
        raise ExperienceError(f"Cannot read the run record of run {run_id}") from error
    if not isinstance(work, dict):
        raise ExperienceError("The run record must be a JSON object")
    return work


def record(project, run_id, review_id, form_after=DEFAULT_FORM_AFTER):
    """Append the outcome rows of one review of a run record; the report `record` prints.

    A review whose basis is not `changeset` produces no row. A row `row_problem` refuses is counted in
    `rows_skipped`, so one bad finding never discards the batch.
    """
    check_form_after(form_after)
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ExperienceError(f"The run id must match {RUN_ID.pattern}")
    work = read_run_record(locate(project)[0], run_id)
    reviews = [item for item in _list(work.get("reviews")) if _dict(item).get("id") == review_id]
    if len(reviews) != 1:
        raise ExperienceError(f"The run record holds {len(reviews)} reviews with the id {review_id}, not one")
    review, rows, skipped = reviews[0], [], 0
    if review.get("review_basis", REVIEW_BASIS) == REVIEW_BASIS:
        rows, skipped = derive_rows(review, _dict(work.get("deliveries")), run_id,
                                    datetime.now(timezone.utc).isoformat())
    usable = [row for row in rows if row_problem(row) is None]
    written, ended = append_with_ended(project, usable, form_after)
    return {"rows_written": written, "rows_skipped": skipped + len(rows) - len(usable), "ended_fact_ids": ended}


def run_id_arg(text):
    if not RUN_ID.fullmatch(text):
        raise argparse.ArgumentTypeError(f"must match {RUN_ID.pattern}")
    return text


def form_after_arg(text):
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value < MIN_FORM_AFTER:
        raise argparse.ArgumentTypeError(f"must be an integer of at least {MIN_FORM_AFTER}")
    return value


def write_facts(path, result):
    """Write FACTS.json through a temporary file beside it, so a failure never leaves a partial file.

    Windows refuses the replace while another process holds the target open, so a PermissionError is
    retried up to REPLACE_TRIES times, REPLACE_WAIT seconds apart, and then raised as ExperienceError
    with the previous file untouched.
    """
    data = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    target = Path(path)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(1, REPLACE_TRIES + 1):
            try:
                os.replace(temporary, target)
                break
            except PermissionError as error:
                if attempt == REPLACE_TRIES:
                    raise ExperienceError(
                        f"Cannot replace {target.name} after {REPLACE_TRIES} tries: {error}") from error
                time.sleep(REPLACE_WAIT)
    finally:
        temporary.unlink(missing_ok=True)


def same_path(first, second):
    return os.path.normcase(os.path.realpath(first)) == os.path.normcase(os.path.realpath(second))


def check_out(path, project, roster):
    """Refuse an `--out` that would replace a file `brief` does not own.

    Refused: the ledger, its lock and the prepared roster in any spelling, and any existing file that is not
    a facts file (JSON with the facts schema), which keeps the run record and every foreign file safe too.
    A missing path or a previous facts file is replaced.
    """
    out, owned = Path(path), [roster]
    try:
        directory = locate(project)[1]
        owned += [directory / LEDGER, directory / LOCK]
    except ExperienceError:
        pass  # no usable store, so no ledger to protect; `brief` declares that gap itself
    if any(same_path(out, other) for other in owned):
        raise ExperienceError(f"--out names a file that brief does not own: {path}")
    if out.exists():
        try:
            with out.open("rb") as handle:
                data = handle.read(FACTS_READ_LIMIT + 1)
            facts = json.loads(data.decode("utf-8")) if len(data) <= FACTS_READ_LIMIT else None
        except (OSError, ValueError, RecursionError):
            facts = None
        if not isinstance(facts, dict) or facts.get("schema") != FACTS_SCHEMA:
            raise ExperienceError(f"--out names an existing file that is not a {FACTS_SCHEMA} file: {path}")


def read_roster(path):
    try:
        roster = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as error:
        raise ExperienceError(f"Cannot read the prepared roster: {path}") from error
    if not isinstance(roster, dict):
        raise ExperienceError("The prepared roster must be a JSON object")
    return roster


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    brief_parser = sub.add_parser("brief", help="list the active facts of a prepared roster's discovery jobs")
    brief_parser.add_argument("--project", required=True)
    brief_parser.add_argument("--roster", required=True, help="the prepared roster returned by composition")
    brief_parser.add_argument("--form-after", type=form_after_arg, default=DEFAULT_FORM_AFTER, help=FORM_AFTER_HELP)
    brief_parser.add_argument("--out", required=True, help="FACTS.json, written at this path")
    record_parser = sub.add_parser("record", help="append the outcome rows of one review of a run record")
    record_parser.add_argument("--project", required=True)
    record_parser.add_argument("--run-id", required=True, type=run_id_arg, help="the run whose work.json is read")
    record_parser.add_argument("--review-id", required=True, help="the review of that run to record")
    record_parser.add_argument("--form-after", type=form_after_arg, default=DEFAULT_FORM_AFTER,
                               help=FORM_AFTER_HELP)
    args = parser.parse_args(argv)
    if args.command == "brief":
        try:
            check_out(args.out, args.project, args.roster)
        except ExperienceError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    try:
        if args.command == "record":
            print(json.dumps(record(args.project, args.run_id, args.review_id, args.form_after)))
            return 0
        result = brief(args.project, read_roster(args.roster), args.form_after)
        write_facts(args.out, result)
    except (ValueError, OSError) as error:  # ExperienceError and UnicodeEncodeError are ValueErrors
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"facts": sum(len(member["facts"]) for job in result["jobs"] for member in job["members"]),
                      "gaps": result["gaps"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
