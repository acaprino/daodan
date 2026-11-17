"""A public Git repository as the app's entrance: its branches, and a checkout of one of them at a commit.

Today a repository is `https://github.com/<owner>/<name>` read with no credential. Git never asks (no terminal
prompt, no credential helper): a repository that needs a login answers `not_accessible`, which does not prove
it is private: it may not exist. The login is a later adapter; this one takes none.

Git is the one program started here, and no file of the repository chooses another: it runs without the user's and
the system's configuration (so no filter, credential helper or alias they define, which a `.gitattributes` of the
repository could name), with `tree_scope.GIT_OPTIONS` (no fsmonitor, no hooks), no hook template, no submodule, no
symbolic link written, and only the transports `ALLOWED` lists. The checkout is shallow, of one branch, and lives
under the app's work folder at `repositories/<owner>/<name>/<commit>`: a commit's folder is written once and reused.
"""
from __future__ import annotations

import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path

from tree_scope import GIT_OPTIONS

ADDRESS = re.compile(r"(?:https://)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}")  # what a listed branch may be called to be asked for
ALLOWED = ("https",)  # the transports Git may use; a test's local repository adds `file`
STATES = ("accessible", "empty", "not_accessible", "network")
NETWORK = ("could not resolve host", "failed to connect", "timed out", "connection reset", "ssl", "network is")
LIST_SECONDS, CLONE_SECONDS = 30, 900


def parse(address: str) -> dict:
    """`{host, owner, name, url}` of a GitHub repository's address; any other text is refused."""
    found = ADDRESS.fullmatch(address.strip()) if isinstance(address, str) else None
    if not found or found[2] in (".", ".."):
        raise ValueError("the address is not https://github.com/<owner>/<name>")
    owner, name = found.groups()
    return {"host": "github.com", "owner": owner, "name": name, "url": f"https://github.com/{owner}/{name}"}


def _git(arguments: list[str], work: Path, seconds: int, transports=ALLOWED, cwd: Path | None = None):
    """Git with nothing of the user's or the system's configuration, never asking, in English."""
    work.mkdir(parents=True, exist_ok=True)
    empty = work / "git-config-empty"
    empty.touch(exist_ok=True)
    environment = {**os.environ, "GIT_CONFIG_GLOBAL": str(empty), "GIT_CONFIG_NOSYSTEM": "1",
                   "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "", "GCM_INTERACTIVE": "never",
                   "GIT_LFS_SKIP_SMUDGE": "1", "LC_ALL": "C"}
    protocols = ["-c", "protocol.allow=never", *(option for name in transports
                                                 for option in ("-c", f"protocol.{name}.allow=always"))]
    command = ["git", *GIT_OPTIONS, "-c", "core.symlinks=false", "-c", "core.longpaths=true",
               "-c", "core.excludesFile=", *protocols, *arguments]  # nor the user's ignore file
    return subprocess.run(command, cwd=cwd, env=environment, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=seconds, stdin=subprocess.DEVNULL)


def _unreached(error: str) -> tuple[str, str]:
    """`(state, detail)` of a Git failure, from its last words."""
    detail = " ".join(error.strip().splitlines()[-2:])[-400:]
    return ("network" if any(word in error.lower() for word in NETWORK) else "not_accessible"), detail


def _listed(source: str, work: Path, transports=ALLOWED) -> dict:
    """What `git ls-remote` says of `source`: `{state, branches: [{name, commit}], default}` or `{state, detail}`."""
    try:
        done = _git(["ls-remote", "--symref", "--", source, "HEAD", "refs/heads/*"], work, LIST_SECONDS, transports)
    except subprocess.TimeoutExpired:
        return {"state": "network", "detail": f"no answer in {LIST_SECONDS} s"}
    if done.returncode:
        state, detail = _unreached(done.stderr)
        return {"state": state, "detail": detail}
    head, branches = None, []
    for line in done.stdout.splitlines():
        first, _, name = line.partition("\t")
        if first.startswith("ref: ") and name == "HEAD":
            head = first[5:].removeprefix("refs/heads/")
        elif name.startswith("refs/heads/"):
            branches.append({"name": name[11:], "commit": first})
    if not branches:
        return {"state": "empty", "detail": "the repository has no branch"}
    names = [branch["name"] for branch in branches]
    default = next((name for name in ("main", "master", head) if name in names), names[0])
    return {"state": "accessible", "branches": sorted(branches, key=lambda b: b["name"]), "default": default}


def branches(address: str, work: Path) -> dict:
    """The branches of the repository at `address`, with the one to offer first (`main`, else `master`, else the
    one the repository declares): `{state, repository, branches, default}`; where it is not reached, `{state,
    repository, detail}` with `state` one of `STATES`."""
    found = parse(address)
    return {"repository": found, **_listed(found["url"], Path(work))}


def _clone(source: str, branch: str, folder: Path, work: Path, transports=ALLOWED) -> tuple[Path, str]:
    """A shallow checkout of `branch` of `source` under `folder`, in the folder named by its commit; that folder
    and the commit. A commit already there is not fetched again."""
    if not BRANCH.fullmatch(branch) or ".." in branch:
        raise ValueError("the branch name is not one this app asks Git for")
    folder.mkdir(parents=True, exist_ok=True)
    incoming = folder / f".incoming-{secrets.token_hex(6)}"
    try:
        done = _git(["clone", "--quiet", "--depth", "1", "--single-branch", "--no-tags", "--no-recurse-submodules",
                     "--template=", "--branch", branch, "--", source, str(incoming)], work, CLONE_SECONDS, transports)
        if done.returncode:
            raise ValueError("the checkout failed: " + _unreached(done.stderr)[1])
        named = _git(["rev-parse", "HEAD"], work, LIST_SECONDS, cwd=incoming)
        commit = named.stdout.strip()
        if named.returncode or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
            raise ValueError("the checkout has no commit: " + named.stderr.strip()[-200:])
        target = folder / commit
        if not target.exists():
            os.replace(incoming, target)
        return target, commit
    except subprocess.TimeoutExpired:
        raise ValueError(f"the checkout did not end in {CLONE_SECONDS} s") from None
    finally:
        shutil.rmtree(incoming, ignore_errors=True)  # shortcut: read-only objects may stay on Windows, a few KB


def checkout(address: str, branch: str, work: Path) -> dict:
    """A checkout of `branch` of the repository at `address` under `work`: `{repository, branch, commit, path}`.
    The branch must be one the repository lists now."""
    found, work = parse(address), Path(work).resolve()
    listed = _listed(found["url"], work)
    if listed["state"] != "accessible":
        raise ValueError(f"the repository is {listed['state'].replace('_', ' ')}: {listed['detail']}")
    if branch not in [item["name"] for item in listed["branches"]]:
        raise ValueError(f"the repository has no branch {branch!r}")
    path, commit = _clone(found["url"], branch, work / "repositories" / found["owner"] / found["name"], work)
    return {"repository": found, "branch": branch, "commit": commit, "path": str(path)}
