"""Gradle and Maven wrapper properties: not a tool, a reader. `distributionUrl` of
`gradle/wrapper/gradle-wrapper.properties` and `.mvn/wrapper/maven-wrapper.properties` names the distribution
and its version; `distributionSha256Sum` says whether the download is verified. Nothing is run (the wrapper
script is project code and is not touched). Standard library only."""
from __future__ import annotations

import os
import re
from pathlib import Path

VERSION = "properties parser"
WRAPPERS = (("gradle/wrapper/gradle-wrapper.properties", "gradle", r"gradle-(\d[^/]*?)-(?:bin|all)\.zip"),
            (".mvn/wrapper/maven-wrapper.properties", "maven", r"apache-maven-(\d[^/]*?)-bin\.(?:zip|tar\.gz)"))


def _props(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!")) and "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip().replace(chr(92) + ":", ":")
    return out


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    toolchains = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "node_modules"))
        for suffix, tool, pattern in WRAPPERS:
            path = Path(folder) / suffix
            if not path.is_file():
                continue
            props = _props(path)
            m = re.search(pattern, props.get("distributionUrl", ""))
            if m:
                toolchains.append({"tool": tool, "version": m.group(1), "declared_in": path.relative_to(root).as_posix(),
                                   "sha256_pinned": "distributionSha256Sum" in props})
            if props.get("wrapperVersion"):
                toolchains.append({"tool": tool + "-wrapper", "version": props["wrapperVersion"],
                                   "declared_in": path.relative_to(root).as_posix()})
    return {"toolchains": toolchains}
