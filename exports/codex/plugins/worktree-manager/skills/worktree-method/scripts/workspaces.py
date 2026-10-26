"""Daodan task annotations and confined Worktrunk creation. Standard library only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid


SCHEMA = "daodan/worktrees/v1"
KINDS = ("fix", "feat", "refactor", "analysis", "docs", "task")
CATALOG_LIMIT = 4 * 1024 * 1024


class WorkspaceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def git(project, *arguments, allowed=(0,)):
    """Never interpolate Git arguments through a shell."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project), *arguments], capture_output=True,
            encoding="utf-8", errors="strict", timeout=30, check=False,
            env={name: value for name, value in os.environ.items() if not name.startswith("GIT_")},
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        raise WorkspaceError("git_failed", "Git could not finish the repository probe") from error
    if result.returncode not in allowed:
        raise WorkspaceError("git_failed", result.stderr.strip() or "Git repository probe failed")
    if len(result.stdout) > 4 * 1024 * 1024:
        raise WorkspaceError("output_limit", "Git inventory exceeds the supported size")
    return result


def key(path):
    return os.path.normcase(str(Path(path).resolve()))


def no_links(path, boundary):
    """Reject symlinks and Windows reparse points before owned-path access."""
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    if not path.is_relative_to(boundary):
        raise WorkspaceError("path_escape", "Owned path escapes the main checkout")
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            info = None
        if info and (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400):
            raise WorkspaceError("linked_path", f"Owned path contains a link: {item}")
        if item == boundary:
            break


def inventory(project):
    """The NUL format preserves paths containing spaces, tabs and newlines."""
    result, row = [], {}
    for field in git(project, "worktree", "list", "--porcelain", "-z").stdout.split("\0"):
        if not field:
            if row:
                result.append(row)
                row = {}
            continue
        name, _, value = field.partition(" ")
        if name == "worktree":
            row["path"] = str(Path(value).resolve())
        elif name == "HEAD":
            row["head"] = value
        elif name == "branch":
            row["branch"] = value.removeprefix("refs/heads/")
        elif name in {"locked", "prunable"}:
            row[name] = value or True
        elif name in {"detached", "bare"}:
            row[name] = True
    if row:
        result.append(row)
    if not result or any("path" not in item for item in result):
        raise WorkspaceError("invalid_inventory", "Git did not return a valid worktree inventory")
    return result


def home_for(project):
    project = Path(project).resolve()
    common = Path(git(project, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    common = common.resolve()
    # Match Work Controller's normal shared Git home. An unusual Git layout needs
    # an explicit future binding rather than silently creating multiple catalogs.
    if common.name != ".git" or not common.is_dir():
        raise WorkspaceError("unsupported_git_layout", "A main checkout with a shared .git directory is required")
    home = common.parent
    rows = inventory(project)
    if not any(key(row["path"]) == key(home) and not row.get("bare") for row in rows):
        raise WorkspaceError("missing_main_checkout", "The Git common directory has no registered main checkout")
    no_links(home / ".daodan", home)
    return home


def verify_checkout(home, target, registered):
    """Check the checkout itself, including its link back to Git's registration."""
    no_links(target / ".git", home)
    try:
        top = git(target, "rev-parse", "--path-format=absolute", "--show-toplevel").stdout.strip()
        common = git(target, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
        directory = Path(git(target, "rev-parse", "--absolute-git-dir").stdout.strip())
        if (key(top) != key(target) or key(common) != key(home / ".git")
                or key(directory.parent) != key(home / ".git/worktrees")
                or not (target / ".git").is_file()):
            raise WorkspaceError("checkout_mismatch", "The checkout does not belong to the expected worktree registration")
        no_links(directory / "gitdir", home)
        backlink = Path((directory / "gitdir").read_text(encoding="utf-8").strip())
        if not backlink.is_absolute():
            backlink = directory / backlink
        head = git(target, "rev-parse", "--verify", "HEAD").stdout.strip()
        branch = git(target, "symbolic-ref", "--quiet", "HEAD", allowed=(0, 1)).stdout.strip().removeprefix("refs/heads/")
        if (key(backlink) != key(target / ".git") or head != registered.get("head")
                or branch != registered.get("branch")):
            raise WorkspaceError("checkout_mismatch", "The checkout identity differs from its expected worktree registration")
    except (OSError, UnicodeError, WorkspaceError) as error:
        if isinstance(error, WorkspaceError) and error.code != "git_failed":
            raise
        raise WorkspaceError("checkout_mismatch", "Cannot verify the checkout's worktree registration") from error


def clean_text(value, name, maximum):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise WorkspaceError("invalid_metadata", f"{name} must be text of at most {maximum} characters without control characters")
    return value.strip()


def clean_tags(values):
    if not isinstance(values, list) or len(values) > 32:
        raise WorkspaceError("invalid_metadata", "Use at most 32 tags")
    tags = [clean_text(value, "Tag", 64) for value in values]
    if any(not tag for tag in tags):
        raise WorkspaceError("invalid_metadata", "Tags cannot be empty")
    return sorted(set(tags))


def load_catalog(home):
    path = home / ".daodan/worktrees.json"
    no_links(path, home)
    if not path.exists():
        return {"schema": SCHEMA, "home": str(home), "revision": 0, "entries": {}}
    try:
        if path.stat().st_size > CATALOG_LIMIT:
            raise WorkspaceError("catalog_limit", "Catalog exceeds the supported size")
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WorkspaceError("invalid_catalog", "Cannot read the worktree catalog") from error
    if not isinstance(catalog, dict) or catalog.get("schema") != SCHEMA or catalog.get("home") != str(home):
        raise WorkspaceError("invalid_catalog", "Catalog schema or main checkout binding does not match")
    if type(catalog.get("revision")) is not int or catalog["revision"] < 0 or not isinstance(catalog.get("entries"), dict):
        raise WorkspaceError("invalid_catalog", "Catalog revision or entries are invalid")
    for path_key, entry in catalog["entries"].items():
        if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                or not Path(entry["path"]).is_absolute() or key(entry["path"]) != path_key
                or type(entry.get("managed")) is not bool):
            raise WorkspaceError("invalid_catalog", "Catalog entry has an invalid path binding")
        clean_text(entry.get("description", ""), "Description", 500)
        clean_tags(entry.get("tags", []))
        if entry.get("managed"):
            required = ("task_id", "branch", "base", "creation")
            if any(not isinstance(entry.get(name), str) or not entry[name] for name in required):
                raise WorkspaceError("invalid_catalog", "Managed entry is missing its creation identity")
            if entry["creation"] not in {"reserved", "confirmed"}:
                raise WorkspaceError("invalid_catalog", "Managed entry has an invalid creation phase")
    return catalog


def ensure_state_home(home):
    root = home / ".daodan"
    no_links(root, home)
    sentinel = root / ".daodan-root"
    no_links(sentinel, home)
    if root.exists() and not sentinel.is_file() and any(root.iterdir()):
        raise WorkspaceError("unowned_state", ".daodan is populated without its ownership sentinel")
    root.mkdir(exist_ok=True)
    sentinel.touch(exist_ok=True)
    return root


@contextmanager
def locked_catalog(home):
    root = ensure_state_home(home)
    lock = root / ".worktrees.lock"
    no_links(lock, home)
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise WorkspaceError("catalog_busy", "Another catalog writer holds .worktrees.lock; inspect its owner before recovery") from error
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid()}, stream)
        yield load_catalog(home)
    finally:
        # A stale lock is never stolen. Normal completion releases only this
        # operation's lock; process termination leaves a visible recovery marker.
        lock.unlink()


def save_catalog(home, catalog):
    destination = home / ".daodan/worktrees.json"
    no_links(destination, home)
    temporary = destination.with_name(f".worktrees-{uuid.uuid4().hex}.tmp")
    no_links(temporary, home)
    updated = {**catalog, "revision": catalog["revision"] + 1}
    encoded = (json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > CATALOG_LIMIT:
        raise WorkspaceError("catalog_limit", "Catalog update exceeds the supported size; the previous catalog is unchanged")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        catalog["revision"] = updated["revision"]
    finally:
        if temporary.exists():
            temporary.unlink()


def list_workspaces(project):
    home = home_for(project)
    catalog = load_catalog(home)
    rows = inventory(home)
    present = set()
    for row in rows:
        identity = key(row["path"])
        present.add(identity)
        row["main"] = identity == key(home)
        row["metadata"] = catalog["entries"].get(identity)
    return {
        "schema": SCHEMA, "home": str(home), "revision": catalog["revision"],
        "worktrees": rows,
        "missing": [entry for identity, entry in catalog["entries"].items() if identity not in present],
    }


def annotate(project, path, description=None, tags=None, add_tags=None, remove_tags=None):
    home = home_for(project)
    selected = Path(path)
    if not selected.is_absolute():
        selected = Path(project) / selected
    identity = key(selected)
    if description is not None:
        description = clean_text(description, "Description", 500)
    if tags is not None:
        tags = clean_tags(tags)
        if add_tags is not None or remove_tags is not None:
            raise WorkspaceError("invalid_metadata", "Choose tag replacement or tag additions/removals")
    add_tags = clean_tags([] if add_tags is None else add_tags)
    remove_tags = clean_tags([] if remove_tags is None else remove_tags)
    if set(add_tags) & set(remove_tags):
        raise WorkspaceError("invalid_metadata", "A tag cannot be both added and removed")
    with locked_catalog(home) as catalog:
        row = next((row for row in inventory(home) if key(row["path"]) == identity), None)
        if row is None:
            raise WorkspaceError("unknown_worktree", "Only a currently registered Git worktree can be annotated")
        entry = catalog["entries"].setdefault(identity, {"path": row["path"], "description": "", "tags": [], "managed": False})
        if description is not None:
            entry["description"] = description
        if tags is not None:
            entry["tags"] = tags
        elif add_tags or remove_tags:
            entry["tags"] = clean_tags(list((set(entry.get("tags", [])) | set(add_tags)) - set(remove_tags)))
        save_catalog(home, catalog)
        return {"home": str(home), "revision": catalog["revision"], "entry": entry}


def run_worktrunk(project, arguments, executable=None):
    # The sibling owns availability, exact version and response validation.
    from worktrunk_runtime import WorktrunkError, run_worktrunk as run
    try:
        return run(project, arguments, executable=executable)
    except WorktrunkError as error:
        raise WorkspaceError(error.code, str(error)) from error


def create(project, task_id, kind, slug, base, prefix="task", description="", tags=None, executable=None):
    home = home_for(project)
    task_id = clean_text(task_id, "Task ID", 200)
    if not task_id or kind not in KINDS:
        raise WorkspaceError("invalid_identity", "A task ID and supported task kind are required")
    slug = clean_text(slug, "Slug", 96).lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise WorkspaceError("invalid_identity", "Slug must contain lowercase words separated by hyphens")
    description, tags = clean_text(description, "Description", 500), clean_tags(tags or [])
    identifier = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:10]
    name = f"{kind}-{slug}-{identifier}"
    branch = f"{prefix}/{kind}/{slug}-{identifier}"
    git(home, "check-ref-format", "--branch", branch)
    target = home / ".daodan/worktrees" / name
    no_links(target, home)
    if (git(home, "check-ignore", "-q", "--", ".daodan/", allowed=(0, 1)).returncode != 0
            or git(home, "check-ignore", "-q", "--", str(target), allowed=(0, 1)).returncode != 0):
        raise WorkspaceError("state_not_ignored", "The .daodan worktree location must already be ignored by Git")
    base_sha = git(home, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}").stdout.strip()
    identity = key(target)
    with locked_catalog(home) as catalog:
        entries = catalog["entries"]
        other = next((entry for entry in entries.values() if entry.get("task_id") == task_id and key(entry["path"]) != identity), None)
        if other:
            raise WorkspaceError("task_already_bound", "This task already has a workspace with a different name or path")
        existing = entries.get(identity)
        if existing and any(existing.get(name) != expected for name, expected in {
            "task_id": task_id, "branch": branch, "base": base_sha, "managed": True,
        }.items()):
            raise WorkspaceError("identity_conflict", "The workspace reservation belongs to another creation identity")
        rows = inventory(home)
        registered = next((row for row in rows if key(row["path"]) == identity), None)
        if registered:
            if not existing or registered.get("branch") != branch:
                raise WorkspaceError("foreign_worktree", "An existing worktree cannot be adopted by creation")
            no_links(target, home)
            if registered.get("prunable") or not target.is_dir():
                raise WorkspaceError("missing_worktree", "Git retains a missing checkout; inspect its registration before recovery")
            verify_checkout(home, target, registered)
            git(home, "merge-base", "--is-ancestor", base_sha, registered["head"])
            existing["creation"] = "confirmed"
            save_catalog(home, catalog)
            return {"action": "resumed", "home": str(home), "entry": existing, "head": registered["head"]}
        if target.exists():
            raise WorkspaceError("occupied_path", "The target path already exists without the expected Git registration")
        if git(home, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", allowed=(0, 1)).returncode == 0:
            raise WorkspaceError("occupied_branch", "The target branch exists without the expected worktree; inspect before recovery")
        if not existing:
            entries[identity] = {
                "path": str(target), "task_id": task_id, "description": description,
                "tags": tags, "managed": True, "branch": branch, "base": base_sha, "creation": "reserved",
            }
            save_catalog(home, catalog)
        target.parent.mkdir(exist_ok=True)
        no_links(target, home)
        run_worktrunk(home, ["switch", "--create", branch, "--base", base_sha, "--path", str(target),
                            "--no-hooks", "--no-cd", "--format=json"], executable=executable)
        actual = next((row for row in inventory(home) if key(row["path"]) == identity), None)
        if (not actual or actual.get("branch") != branch or actual.get("head") != base_sha
                or actual.get("prunable") or not target.is_dir()):
            raise WorkspaceError("creation_unverified", "Worktrunk returned but Git does not confirm the requested path, branch and base")
        no_links(target, home)
        verify_checkout(home, target, actual)
        entries[identity]["creation"] = "confirmed"
        save_catalog(home, catalog)
        return {"action": "created", "home": str(home), "entry": entries[identity], "head": base_sha}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    edit = sub.add_parser("annotate")
    edit.add_argument("--path", type=Path, required=True)
    edit.add_argument("--description")
    edit.add_argument("--tag", action="append", dest="tags", help="Replace the tag set (repeat for each retained tag)")
    edit.add_argument("--clear-tags", action="store_true")
    edit.add_argument("--add-tag", action="append", dest="add_tags", help="Add a tag atomically (repeat for each addition)")
    edit.add_argument("--remove-tag", action="append", dest="remove_tags", help="Remove a tag atomically (repeat for each removal)")
    new = sub.add_parser("create")
    for name in ("task-id", "kind", "slug", "base"):
        new.add_argument(f"--{name}", required=True, **({"choices": KINDS} if name == "kind" else {}))
    new.add_argument("--prefix", default="task", help="Project or host branch prefix (for example codex)")
    new.add_argument("--description", default="")
    new.add_argument("--tag", action="append", dest="tags")
    new.add_argument("--executable")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = list_workspaces(args.project)
        elif args.command == "annotate":
            if args.clear_tags and args.tags:
                raise WorkspaceError("invalid_metadata", "Choose tags or clear-tags")
            result = annotate(args.project, args.path, args.description, [] if args.clear_tags else args.tags,
                              args.add_tags, args.remove_tags)
        else:
            result = create(args.project, args.task_id, args.kind, args.slug, args.base, args.prefix,
                            args.description, args.tags, args.executable)
    except (WorkspaceError, OSError, ValueError) as error:
        print(json.dumps({"error": getattr(error, "code", "workspace_failed"), "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
