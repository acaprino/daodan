#!/usr/bin/env python3
"""The archive of a case that may leave this machine: code and configuration, never data or secrets.

    python code_archive.py OUT.tar REPOSITORY
    python code_archive.py OUT.tar REPOSITORY[@COMMIT][=PREFIX/] ...

A repository can track far more than code: screenshots, spreadsheets, the documents a program works on, files of
environment variables. `kept` is the closed rule of what goes into the archive; everything else stays here. The archive
is read from `git archive`, so it holds tracked files only and runs nothing of the repository: of `HEAD`, or of the
commit a reference is bound to. A case that spans repositories keeps each one under its own folder. Every kept file
goes through Secretlint (`secret_mask`): a secret it finds is masked and counted, and the file goes in; a file that is
not UTF-8 text cannot be checked and stays here, named. Without Secretlint no archive is written.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "daodan" / "core"))
import secret_mask  # noqa: E402
from container import Gap  # noqa: E402

CODE = re.compile(r"\.(py|pyi|js|jsx|mjs|cjs|ts|tsx|vue|svelte|astro|rs|go|java|kt|kts|cs|swift|dart|rb|php|c|h|cc|cpp|hpp"
                  r"|html|htm|css|scss|sass|less|sql|graphql|proto|sh|ps1|bat|cmd|spec"
                  r"|json|jsonc|toml|yaml|yml|ini|cfg|conf|xml|gradle|properties|lock|md|txt|tf|hcl)$", re.I)
NAMED = re.compile(r"(^|/)(Dockerfile[^/]*|Makefile|Caddyfile|Procfile|Gemfile|Rakefile|\.gitignore|\.dockerignore|[^/]*\.example)$")
SECRET = re.compile(r"(^|/)(\.env(\.[^/]*)?|[^/]*secrets?[^/]*\.(json|ya?ml|toml)|credentials[^/]*\.json|service-?account[^/]*\.json"
                    r"|[^/]*\.(pem|key|p12|pfx|keystore|jks))$", re.I)
EXAMPLE = re.compile(r"\.(example|sample|template|dist)$", re.I)
DATA_FOLDER = re.compile(r"(^|/)(data|datasets?|fixtures|outputs?|dumps?|backups?|node_modules|dist|build|target)/", re.I)
TOOL_FOLDER = re.compile(r"(^|/)\.(claude|codex|cursor|agents|idea|vscode|jcode|tritech|daodan|codebase-map|tmp)/")  # editors, agents, earlier analyses
LIMIT = 400_000  # a source or configuration file is not larger than this: beyond it, it is data under a code suffix


def kept(path: str, size: int) -> bool:
    """Whether a tracked file may go into the archive."""
    if SECRET.search(path) and not EXAMPLE.search(path):
        return False
    if DATA_FOLDER.search(path) or TOOL_FOLDER.search(path) or size > LIMIT:
        return False
    return bool(CODE.search(path) or NAMED.search(path))


def _checked(content: bytes, name: str) -> tuple[bytes | None, int]:
    """The content with its secrets masked and how many, or None for a file that is not UTF-8 text."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None, 0
    checked = secret_mask.masked(text, name)
    return (checked["text"].encode("utf-8") if checked["found"] else content), checked["found"]


def _copy(repository: Path, prefix: str, target: tarfile.TarFile, commit: str = "HEAD") -> dict:
    """The kept files of one repository at a commit into `target`, read from the stream of `git archive`."""
    counts = {"kept": 0, "left": 0, "bytes": 0, "masked": {}, "withheld": []}
    process = subprocess.Popen(["git", "-C", str(repository), "archive", "--format=tar", commit], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as source:
            for member in source:
                if not member.isfile():
                    continue
                if not kept(member.name, member.size):
                    counts["left"] += 1
                    continue
                content, found = _checked(source.extractfile(member).read(), member.name)
                if content is None:
                    counts["withheld"].append(member.name)
                    continue
                if found:
                    counts["masked"][member.name] = found
                member.name, member.size = prefix + member.name, len(content)
                target.addfile(member, io.BytesIO(content))
                counts["kept"] += 1
                counts["bytes"] += member.size
    finally:
        if process.poll() is None:
            process.kill()
        returncode = process.wait()
    if returncode:
        raise RuntimeError(f"git archive failed in {repository}")
    return counts


def write(out: Path, sources: list[tuple]) -> dict:
    """One archive from the repositories of a case, each `(repository, prefix)` or `(repository, prefix, commit)`;
    what was kept, masked and left, per repository. Without Secretlint, or when it fails, `Gap` and no archive."""
    secret_mask.executable()
    try:
        with tarfile.open(out, "w") as target:
            return {str(source[0]): _copy(source[0], source[1], target, *source[2:]) for source in sources}
    except BaseException:
        out.unlink(missing_ok=True)
        raise


def source(text: str) -> tuple[Path, str, str]:
    """`REPOSITORY[@COMMIT][=PREFIX/]` of the command line."""
    text, _, prefix = text.rpartition("=") if "=" in text[3:] else (text, "", "")
    repository, _, commit = text.rpartition("@") if "@" in text[3:] else (text, "", "HEAD")
    return Path(repository), prefix, commit


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    try:
        print(write(Path(argv[1]), [source(text) for text in argv[2:]]))
    except Gap as gap:
        print(f"no archive: {gap.cause}; {gap.remedy}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
