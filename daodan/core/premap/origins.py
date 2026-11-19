"""Where a source says a project's dependencies come from: the origin of each URL it states (a unit's `registries`,
the hosts the preparation reaches), and the files that state them which the snapshot does not hold."""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlsplit

VCS = re.compile(r"^(?:git|hg|svn|bzr)\+")
# The URL a requirement names: `name @ URL` (PEP 508), a bare URL, pip's `-e URL` or `URL#egg=name`.
REQUIREMENT = re.compile(r"(?:^|@|\s)\s*((?:(?:git|hg|svn|bzr)\+)?[a-z][a-z0-9+.-]*://[^\s;,\"']+)")
URL = re.compile(r"(?:(?:git|hg|svn|bzr)\+)?[a-z][a-z0-9+.-]*://[^\s\"'#,;}]+")


def origin(url) -> str | None:
    """`scheme://host[:port]` of `url` without its credentials, a VCS URL's without its `git+`; None for none."""
    try:
        parts = urlsplit(VCS.sub("", str(url).strip()))
        host, port = parts.hostname, parts.port
    except ValueError:
        return None
    return f"{parts.scheme}://{host}{f':{port}' if port else ''}" if parts.scheme and host else None


def requirement(text) -> str | None:
    """The origin of the URL a requirement names, None for a requirement an index answers."""
    found = REQUIREMENT.search(str(text))
    return origin(found.group(1)) if found else None


def found(text: str) -> set[str]:
    """The origins of every URL in `text`, a lockfile's."""
    return {o for url in URL.findall(text) for o in [origin(url)] if o}


def disk_text(context, rel: str) -> str | None:
    """`rel`'s text, a file the snapshot does not hold (`yarn.lock`, `nuget.config`), read from disk in a folder the
    snapshot holds; None when there is no such file."""
    import confinement
    folder = rel.rsplit("/", 1)[0] if "/" in rel else "."
    path = Path(context.root) / rel
    if folder not in context.inventory.directories or not path.is_file():
        return None
    confinement.reject_link_chain(path)
    return path.read_text(encoding="utf-8", errors="replace")
