"""A unit only its Dockerfile builds: the build stage reproduced in Daodan's preparation, the analyzer in what it leaves.

The pre-map states each Dockerfile as BuildKit reads it (`docker_builds`, `premap/dockerfile.py`). `plan` takes the
stage whose COPY from the build context brings the unit's files (the last such stage) and the stages it starts
FROM, and their instructions up to that stage's last RUN, the build itself, which must run the analyzer's build:

- ENV and ARG are exports with BuildKit's values (an ARG reaches the RUN instructions only, as in BuildKit);
- WORKDIR is the folder the next instructions run in, `/` before the first;
- RUN runs in a shell of its own, with the stage's SHELL for its shell form;
- COPY and ADD copy the context's files from the copy of the checkout (`WORK`) by BuildKit's rules: a folder's
  contents into the destination; a file into a destination folder (one ending in `/` or `.`, or for several
  sources), else as the destination itself.

The build is not a step: the plan keeps its words in the stage's shell (`build.argv`) and the stage's ENV and ARG
values (`env`), for an analyzer that runs it where it would (`command`) or runs its own tool in its place.
The image is the first stage's FROM, run by the digest its registry gives (`pinned`); the hosts the preparation opens beside the registries are those the RUN
instructions name in a URL. What the steps write (a `go.mod`, a generated source) is no file of the checkout:
`origin` maps back only what a COPY brought. An instruction it cannot reproduce is a `not_reproduced` gap naming
the Dockerfile's line, and the stage is not run: a build argument without a value, a RUN mount other than a cache
or a tmpfs, a heredoc, an insecure RUN, a COPY or ADD from another stage or image, of a remote source or an
archive, with --parents, --exclude, --checksum, --chown or --chmod, a source outside the context or not in it, a
USER other than root, a word that expands a variable the Dockerfile does not set (the base image's environment
may), FROM scratch, and a last RUN that does not run the build.
"""
from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import shlex
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORK = "/work"  # `container.WORKDIR`: the copy of the checkout
METADATA = {"CMD", "ENTRYPOINT", "EXPOSE", "LABEL", "HEALTHCHECK", "VOLUME", "STOPSIGNAL", "MAINTAINER", "ONBUILD"}
KEPT_MOUNTS = {"cache", "tmpfs"}  # what a RUN reads from them does not decide what it writes for the build
ROOT_USERS = {"root", "0", "root:root", "0:0"}
URL = re.compile(r"\b(?:https?|git|ssh)://(?:[^@/\s'\"]+@)?([A-Za-z0-9.-]+)")
ARCHIVE = re.compile(r"\.(tar|tgz|tbz2|txz|tar\.gz|tar\.bz2|tar\.xz|gz|bz2|xz)$")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
GLOB = re.compile(r"[*?\[]")
MANIFESTS = ", ".join(("application/vnd.oci.image.index.v1+json",  # what a registry may answer for a tag
                       "application/vnd.docker.distribution.manifest.list.v2+json",
                       "application/vnd.oci.image.manifest.v1+json",
                       "application/vnd.docker.distribution.manifest.v2+json"))


DEBIAN = "https://deb.debian.org/debian/pool/main"
GLIBC = [  # Debian 13's glibc and GCC runtime (glibc 2.41, libstdc++ of GCC 14.2): a glibc program on a base without it
    (f"{DEBIAN}/g/glibc/libc6_2.41-12+deb13u4_amd64.deb",
     "967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9", "libc6.deb"),
    (f"{DEBIAN}/g/gcc-14/libgcc-s1_14.2.0-19_amd64.deb",
     "3c71917b490d1a17aed43196a2787a256ecf060526cdb20216a74bedc061b150", "libgcc-s1.deb"),
    (f"{DEBIAN}/g/gcc-14/libstdc++6_14.2.0-19_amd64.deb",
     "ab1fa05837aa7a92aae748fd07a18a35f7d18bb4a71c4724fe2bbf0e32089de0", "libstdc++6.deb"),
]
MULTIARCH, LOADER = "usr/lib/x86_64-linux-gnu", "lib64/ld-linux-x86-64.so.2"


def glibc(target: Path | None = None) -> Path:
    """One tar at `target` (default: in the shared directory, named by the packages' digests) of what `GLIBC`'s
    packages hold in the multiarch folder (/usr/lib/x86_64-linux-gnu, or /lib/x86_64-linux-gnu before Debian's
    move to /usr), each package checked by its sha256 (`preparation.fetched`), with the loader also at /lib64,
    where a glibc program names it: unpacked at `/` of a base without glibc (Alpine's musl), the libraries sit
    where only glibc's loader looks."""
    import copy
    import hashlib
    import io
    import tarfile
    import preparation
    from engine_tools import shared_engine_dir
    named = hashlib.sha256("".join(digest for _url, digest, _name in GLIBC).encode()).hexdigest()[:16]
    target = Path(target or shared_engine_dir("preparation") / "glibc" / f"{named}.tar")
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    with tarfile.open(partial, "w") as out:
        for url, digest, name in GLIBC:
            data, at = preparation.fetched(url, digest, name).read_bytes(), 8  # an ar archive: its members
            while at < len(data):
                member, size = data[at:at + 16].decode().strip().rstrip("/"), int(data[at + 48:at + 58])
                if member.startswith("data.tar"):
                    with tarfile.open(fileobj=io.BytesIO(data[at + 60:at + 60 + size])) as package:
                        for entry in package.getmembers():
                            folder, base = posixpath.split(posixpath.normpath(entry.name))
                            if folder not in (MULTIARCH, MULTIARCH[len("usr/"):]) or not (entry.isfile()
                                                                                          or entry.issym()):
                                continue
                            entry.name = posixpath.join(MULTIARCH, base)
                            out.addfile(entry, package.extractfile(entry) if entry.isfile() else None)
                            if posixpath.basename(entry.name) == posixpath.basename(LOADER) and entry.isfile():
                                loader = copy.copy(entry)
                                loader.name = LOADER
                                out.addfile(loader, package.extractfile(entry))
                at += 60 + size + size % 2
    os.replace(partial, target)
    return target


def pinned(image: str, timeout: float = 60) -> str:
    """`image` named by the digest its registry gives for its tag now: the OCI distribution API's manifest HEAD,
    with the anonymous token the registry's `WWW-Authenticate` names when it asks for one. One named by a digest
    is kept. RuntimeError with the registry's answer when it gives none."""
    if "@sha256:" in image:
        return image
    import container
    reference = container.qualified(image)
    registry, _, path = reference.partition("/")
    name, tag = path.rsplit(":", 1) if ":" in path.rsplit("/", 1)[-1] else (path, "latest")
    url = f"https://{'registry-1.docker.io' if registry == 'docker.io' else registry}/v2/{name}/manifests/{tag}"
    headers, digest = {"Accept": MANIFESTS}, None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers, method="HEAD"),
                                        timeout=timeout) as answer:
                digest = answer.headers.get("Docker-Content-Digest")
            break
        except urllib.error.HTTPError as error:
            challenge = (error.headers or {}).get("WWW-Authenticate") or ""
            if error.code != 401 or attempt or not challenge.startswith("Bearer "):
                raise RuntimeError(f"{reference}: its registry answered {error.code} {error.reason}") from error
            fields = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
            query = urllib.parse.urlencode({k: v for k, v in fields.items() if k in ("service", "scope")})
            with urllib.request.urlopen(f"{fields['realm']}?{query}", timeout=timeout) as answer:
                token = json.loads(answer.read())
            headers = {**headers, "Authorization": f"Bearer {token.get('token') or token.get('access_token')}"}
    if not digest:
        raise RuntimeError(f"{reference}: its registry gave no digest")
    return f"{reference}@{digest}"


def _context(project: Path, context: str) -> tuple[set[str], set[str]]:
    """The files and folders of the build context, relative to it."""
    files, folders, base = set(), {"."}, Path(project) / context
    for folder, names, found in os.walk(base):
        rel = Path(folder).relative_to(base).as_posix()
        for name in names:
            folders.add(posixpath.normpath(posixpath.join(rel, name)))
        for name in found:
            files.add(posixpath.normpath(posixpath.join(rel, name)))
    return files, folders


def _sources(pattern: str, files: set[str], folders: set[str]) -> list[tuple[str, bool]] | None:
    """What a COPY source names in the context, each `(path, is_folder)`; None when it leaves the context."""
    path = posixpath.normpath(pattern.lstrip("/") or ".")  # BuildKit reads `/x` from the context's root
    if path == ".." or path.startswith("../"):
        return None
    if not GLOB.search(path):
        return [(path, True)] if path in folders else [(path, False)] if path in files else []
    parts = path.split("/")
    return sorted((rel, rel in folders) for rel in files | (folders - {"."}) if len(rel.split("/")) == len(parts)
                  and all(fnmatch.fnmatchcase(a, b) for a, b in zip(rel.split("/"), parts)))


def _under(files: set[str], folder: str) -> list[str]:
    return sorted(rel for rel in files if folder == "." or rel.startswith(f"{folder}/"))


def plan(build: dict, project: Path, wanted: list[str], builds: str, *, work: str = WORK, root: str = "") -> dict | None:
    """The reproduction of `build`'s stage that copies in a file of `wanted` (checkout paths), up to its last
    RUN, which must match `builds` (the analyzer's build command); None when no stage copies one in. `root` is
    where the stage's filesystem lies (the container's own: empty), `work` the copy of the checkout."""
    dockerfile, context, stages = build["dockerfile"], build["context"], build["stages"]
    files, folders = _context(project, context)
    checkout = lambda rel: posixpath.normpath(posixpath.join(context, rel))  # noqa: E731
    wanted, target = set(wanted), None
    for index, stage in enumerate(stages):
        for item in stage["commands"]:
            if item["kind"] in ("COPY", "ADD") and not item.get("from"):
                for pattern in item.get("sources") or ():
                    found = _sources(pattern, files, folders) or []
                    if any(checkout(rel) in wanted for path, folder in found
                           for rel in (_under(files, path) if folder else [path])):
                        target = index
    if target is None:
        return None
    chain = [target]
    while stages[chain[0]].get("base_stage") is not None:
        chain.insert(0, stages[chain[0]]["base_stage"])
    image, last = stages[chain[0]]["base"], stages[target]
    name = last["name"] or str(target)
    runs = [item for item in last["commands"] if item["kind"] == "RUN"]
    gaps, lines, ran, copies, env, hosts = [], ["set -e"], [], {}, {}, set()
    workdir, shell = "/", ["/bin/sh", "-c"]

    def gap(item: dict, detail: str) -> None:
        gaps.append({"kind": "not_reproduced", "path": f"{dockerfile}:{item['line']}",
                     "detail": f"{item['original']}: {detail}"})

    def failed(item: dict) -> str:
        return f'|| {{ echo "DAODAN-DOCKERFILE-FAILED {dockerfile}:{item["line"]}" >&2; exit 1; }}'

    if image == "scratch":
        gap({"line": stages[chain[0]]["line"], "original": f"FROM {image}"}, "an empty filesystem has no shell")
    if not runs or not re.search(builds, " ".join(runs[-1].get("cmd") or ())):
        item = runs[-1] if runs else {"line": last["line"], "original": f"FROM {last['base']}"}
        gap(item, f"the stage's last RUN does not run the build the analyzer replaces (`{builds}`)")
    own = last["commands"]
    steps = [item for index in chain[:-1] for item in stages[index]["commands"]]
    steps += own[:next((i for i, item in enumerate(own) if runs and item is runs[-1]), len(own))]
    lines.append(f"mkdir -p {shlex.quote(root + '/')}")
    for item in (step for step in steps if step["kind"] not in METADATA):
        kind = item["kind"]
        if item.get("unmatched"):
            gap(item, f"expands {', '.join(item['unmatched'])}, which no ARG or ENV of the Dockerfile sets")
            continue
        if kind == "ARG":
            for pair in item["args"]:
                for key, value in pair.items():
                    if value is None:
                        gap(item, f"{key} has no value: no default and no build argument gives one")
                    else:
                        lines.append(f"export {key}={shlex.quote(value)}")
                        if any(item is mine for mine in own):  # in scope where the build runs; an ENV wins
                            env.setdefault(key, value)
        elif kind == "ENV":
            for key, value in item["env"]:
                env[key] = value
                lines.append(f"export {key}={shlex.quote(value)}")
        elif kind == "WORKDIR":
            workdir = posixpath.normpath(posixpath.join(workdir, item["path"]))
            lines.append(f"mkdir -p {shlex.quote(root + workdir)}")
        elif kind == "SHELL":
            shell = item["shell_form"]
        elif kind == "USER":
            if item["user"] not in ROOT_USERS:
                gap(item, "another user is not reproduced: the steps run as root")
        elif kind == "RUN":
            mounts = [m["type"] for m in item.get("mounts") or () if m["type"] not in KEPT_MOUNTS]
            if mounts:
                gap(item, f"a {', '.join(mounts)} mount is not reproduced")
            elif item.get("files"):
                gap(item, "a heredoc is not reproduced")
            elif item.get("security") == "insecure":
                gap(item, "an insecure RUN is not reproduced")
            else:
                words = [*shell, *item["cmd"]] if item.get("shell") else item["cmd"]
                hosts.update(URL.findall(" ".join(item["cmd"])))
                lines.append(f"( cd {shlex.quote(root + workdir)} && exec {shlex.join(words)} ) {failed(item)}")
        elif kind in ("COPY", "ADD"):
            flags = [f for f in item.get("flags") or () if f != "link"] + [f for f in ("chown", "chmod") if item.get(f)]
            if item.get("from"):
                gap(item, f"a copy from {item['from']}, another stage or image, is not reproduced")
            elif flags:
                gap(item, f"--{', --'.join(flags)} is not reproduced")
            elif item.get("files"):
                gap(item, "a heredoc is not reproduced")
            elif kind == "ADD" and any(URL.search(s) or ARCHIVE.search(s) for s in item["sources"]):
                gap(item, "a remote source or an archive ADD unpacks is not reproduced")
            else:
                found = [(_sources(s, files, folders), s) for s in item["sources"]]
                outside = [s for paths, s in found if paths is None]
                missing = [s for paths, s in found if paths == []]
                if outside or missing:
                    gap(item, "; ".join([*([f"{', '.join(outside)}: outside the build context {context}"]
                                           if outside else []),
                                         *([f"{', '.join(missing)}: not in the build context {context}"]
                                           if missing else [])]))
                    continue
                paths = [path for group, _ in found for path in group]
                dest = posixpath.normpath(posixpath.join(workdir, item["dest"]))
                into = item["dest"].endswith("/") or posixpath.basename(item["dest"]) in (".", "") or len(paths) > 1
                for path, folder in paths:
                    source = shlex.quote(f"{work}/{checkout(path)}")
                    if folder:
                        lines.append(f"mkdir -p {shlex.quote(root + dest)} && cp -a {source}/. "
                                     f"{shlex.quote(root + dest)}/ {failed(item)}")
                        copies.update({posixpath.join(dest, rel[len(path) + 1:] if path != "." else rel): checkout(rel)
                                       for rel in _under(files, path)})
                    elif into:
                        lines.append(f"mkdir -p {shlex.quote(root + dest)} && cp -a {source} "
                                     f"{shlex.quote(root + dest)}/ {failed(item)}")
                        copies[posixpath.join(dest, posixpath.basename(path))] = checkout(path)
                    else:
                        lines.append(f"mkdir -p {shlex.quote(root + posixpath.dirname(dest))} && cp -a {source} "
                                     f"{shlex.quote(root + dest)} {failed(item)}")
                        copies[dest] = checkout(path)
        ran.append(item["line"])
    gaps.sort(key=lambda g: int(g["path"].rsplit(":", 1)[1]))
    return {"dockerfile": dockerfile, "stage": name, "image": image, "workdir": workdir,
            "env": [[key, value] for key, value in env.items()], "lines": [] if gaps else lines,
            "ran": ran, "build": {"line": runs[-1]["line"], "original": runs[-1]["original"],
                                  "argv": [*shell, *runs[-1]["cmd"]] if runs[-1].get("shell") else runs[-1]["cmd"]}
            if runs else None,
            "copies": copies, "hosts": sorted(hosts), "gaps": gaps}


FAILED = re.compile(r"DAODAN-DOCKERFILE-FAILED (\S+)")  # what a step of the plan's lines prints when it fails


def last_line(log: str, end: int | None = None) -> str:
    """The last line with words before `end` in a log."""
    return next((line.rstrip() for line in reversed(log[:end].splitlines()) if line.strip()), "")[:400]


def failed_step(plan: dict, build: dict, log: str, error=last_line) -> dict | None:
    """The step of `plan` that the preparation's `log` says failed, else None: its `path` (the Dockerfile and its
    line), its `original` instruction and the tool's `error`, the line `error(log, at)` picks before the mark,
    with its gaps: `restore_failed`, and `host_unreachable` for each host the preparation opened (the registries
    and the plan's hosts) that the error says it could not reach (`preparation.unreached`)."""
    import container
    import preparation
    step = FAILED.search(log)
    if step is None:
        return None
    line = int(step.group(1).rsplit(":", 1)[1])
    original = next((c["original"] for s in build["stages"] for c in s["commands"] if c["line"] == line), "")
    said = error(log, step.start())
    gap = {"kind": "restore_failed", "path": step.group(1), "detail": f"{original}: {said}"}
    where = {host: [plan["dockerfile"]] for host in (*plan["hosts"], *container.REGISTRIES)}
    return {"path": step.group(1), "original": original, "error": said,
            "gaps": [gap, *preparation.unreached([gap], {"hosts": sorted(where), "where": where})]}


def origin(plan: dict, path: str) -> str | None:
    """The checkout's file a COPY of the plan brought to `path` in the stage's filesystem; None for one the
    steps wrote."""
    return plan["copies"].get(posixpath.normpath(path))


def _field(number: int, wire: int, value) -> bytes:
    """One protobuf field, of the two wire types a SCIP document holds (varint, length-delimited)."""
    out, item = bytearray(), number << 3 | wire
    for item in (item, *([value] if wire == 0 else [len(value)])):
        while True:
            byte, item = item & 0x7F, item >> 7
            out.append(byte | 0x80 if item else byte)
            if not item:
                break
    return bytes(out) + (b"" if wire == 0 else value)


def rewritten(index: Path, plan: dict, out: Path) -> int:
    """The SCIP index at `index`, of documents relative to the build's folder, written to `out` with each
    document named as the checkout's file a COPY brought there (`origin`) and those the steps wrote left out;
    every other field as it was. The number of documents kept."""
    import code_graph
    data, kept = bytearray(), 0
    for number, wire, value in code_graph._fields(Path(index).read_bytes()):
        if number == 2 and wire == 2:
            fields = list(code_graph._fields(value))
            rel = next((part.decode("utf-8", "replace") for n, w, part in fields if n == 1 and w == 2), "")
            checkout = origin(plan, posixpath.join(plan["workdir"], rel))
            if checkout is None:
                continue
            value = b"".join(_field(n, w, checkout.encode() if n == 1 and w == 2 else part) for n, w, part in fields)
            kept += 1
        data += _field(number, wire, value)
    Path(out).write_bytes(bytes(data))
    return kept


def provenance(plan: dict) -> dict:
    """What a unit's result names of the build it came from: the Dockerfile, its stage, the lines of the
    instructions run and of the build they stop before."""
    return {"dockerfile": plan["dockerfile"], "stage": plan["stage"], "ran": plan["ran"],
            "build": (plan["build"] or {}).get("line")}


def run(project: Path, out_dir: Path, plan: dict, argv: list[str], *, setup=(), files=(), carried=None,
        **options) -> dict:
    """`argv` in what the stage `plan` reproduces leaves (`container.run_in_container`'s result): its steps, then
    `setup` (the analyzer's own tools, unpacked from `files`, each `(url, sha256, name)` carried into
    `preparation.IN`, and from what `carried()` maps, a container path to a host file, called once an engine
    answers), in the preparation, on the base image by its digest, with the registries and the plan's
    hosts open; then `argv` with no network, in the build's folder (`command`), from everything the steps wrote
    (`keep_root`). As BuildKit runs a step, HOME is root's. A base image whose registry gives no digest is a gap."""
    import container
    import preparation
    try:
        image = pinned(plan["image"])
    except (OSError, RuntimeError) as error:
        return {"state": "gap", "cause": f"the base image {plan['image']} of {plan['dockerfile']}: {error}",
                "remedy": "name the base image by a registry Daodan can reach anonymously, or by its digest"}
    return container.run_in_container(
        project, command(plan, argv), image=image, out_dir=out_dir, env={"HOME": "/root"}, keep_root=True,
        prepare=["sh", "-c", "\n".join([*plan["lines"], *setup])],
        registries=tuple(dict.fromkeys((*container.REGISTRIES, *plan["hosts"]))),
        inputs=lambda: {**{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                           for url, digest, name in files}, **(carried() if carried else {})}, **options)


def command(plan: dict, argv: list[str]) -> list[str]:
    """`argv` with the stage's ENV and in its build's folder: an execution starts from the image's own
    configuration, which holds neither."""
    exports = "".join(f"export {key}={shlex.quote(value)}; " for key, value in plan["env"] if NAME.fullmatch(key))
    return ["sh", "-c", f'{exports}cd {shlex.quote(plan["workdir"])} && exec "$@"', "sh", *argv]
