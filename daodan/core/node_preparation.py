"""A Node dependency restore belongs to one analysis. Each tool copies its result into private volumes."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile
import uuid

import confinement
import preparation

SESSION = ContextVar("daodan_node_preparation", default=None)
OWNED_ENGINE = ContextVar("daodan_node_engine", default=None)
CHILD_ENV = "DAODAN_NODE_PREPARATION"


def _session():
    current = SESSION.get()
    if current is None and os.environ.get(CHILD_ENV):
        current = Path(os.environ[CHILD_ENV])
    return current


def child_environment() -> dict:
    folder = SESSION.get()
    return {CHILD_ENV: str(folder)} if folder else {}


def windows_engine(discover):
    """Kiri's WSL distribution can be temporary. Only the parent releases its daemon and installation lock."""
    import container
    folder = _session()
    if folder is None:
        return discover()
    name_file = folder / "engine"
    owned = OWNED_ENGINE.get()
    if owned is not None:
        if not owned:
            owned.append(discover())
            name_file.write_text(owned[0].name, encoding="utf-8")
        return container.Engine(owned[0].name, owned[0].argv)
    if name_file.is_file():
        # Reconstruct Daodan's fixed daemon command. No executable or arguments come from the handoff.
        return container.Engine(name_file.read_text(encoding="utf-8"),
                                (*container.distro_argv(), "/usr/bin/docker", "-H", container.SOCKET))
    return discover()


@contextmanager
def analysis():
    """Keep the two seed volumes alive across the analyzer subprocess, including on partial pipeline runs."""
    import container

    with tempfile.TemporaryDirectory(prefix="daodan-node-") as temp:
        folder = Path(temp)
        (folder / "owner").write_text(str(os.getpid()), encoding="ascii")
        token = SESSION.set(folder)
        owned = []
        engine_token = OWNED_ENGINE.set(owned)
        try:
            yield
        finally:
            SESSION.reset(token)
            OWNED_ENGINE.reset(engine_token)
            leases = list(folder.glob("*.lease"))
            engine = owned[0] if owned else None
            if leases and engine is None:
                try:
                    engine = container.find_engine()
                except (container.Gap, OSError, RuntimeError, subprocess.TimeoutExpired):
                    engine = None
            try:
                for lease in leases:
                    entry, names = _volumes(lease.stem)
                    if not entry.is_file():
                        continue
                    held = json.loads(entry.read_text(encoding="utf-8"))
                    # A cleanup failure remains discoverable by the ordinary engine sweeper.
                    container.record_volumes(entry, held["engine"], 0, names)
                    if engine and held["engine"] == engine.name:
                        try:
                            container.remove_volumes(engine, entry, 0, names)
                        except (OSError, RuntimeError, subprocess.TimeoutExpired):
                            pass
            finally:
                if engine is not None:
                    engine.stop()


def options(restored: dict, toolchains=(), hosts=()) -> tuple[list[str], dict]:
    """The standalone restore, or the instructions to build it once in the current analysis."""
    if not restored["lines"] or _session() is None:
        return restored["lines"], {}
    import container
    beside = container.BESIDE.get()
    if beside and (beside[1] or (beside[0] and beside[2])):
        # A lifecycle hook may require the CI's environment or a service already running beside the CI steps.
        return restored["lines"], {}
    chains = preparation.toolchains([t for t in toolchains if t.get("tool") == "node"
                                    and preparation.EXACT.match(str(t.get("version") or ""))])
    node = preparation.setup(["node"])  # as root, before the restore (`container.tool_phase`)
    script = "\n".join([f"mkdir -p {preparation.T}/bin \"$HOME\"", *chains["lines"], "cd /work || exit 70",
                        *restored["lines"]])
    return [], {"node_restore": {"tools": {"lines": node["lines"], "caps": node["caps"]}, "script": script,
                                 "inputs": [f"{preparation.IN}/{name}" for _, _, name in
                                                              (preparation.NODE, *chains["files"])],
                                 "hosts": sorted({*preparation.NODE_REGISTRIES, *restored["hosts"], *chains["hosts"],
                                                  *hosts})}}


def _volumes(token):
    import container
    if len(token) != 12 or any(c not in "0123456789abcdef" for c in token):
        raise ValueError("invalid Node seed volume token")
    return (container.volume_registry() / f"{token}.json",
            [f"daodan-work-{token}", f"daodan-state-{token}"])


def _split(copy, shared, extra, inputs):
    """Separate the captured checkout and its common inputs from the consumer's helper files."""
    common = {name.strip("/") for name in inputs}
    parents = {p.as_posix() for name in common for p in PurePosixPath(name).parents}
    with tarfile.open(copy, "r") as original, tarfile.open(shared, "w") as seed, tarfile.open(extra, "w") as tools:
        for member in original:
            checkout = member.name == "work" or member.name.startswith("work/")
            if checkout or member.name in common or member.name in parents:
                seed.addfile(member, original.extractfile(member) if member.isfile() else None)
            if not checkout:
                tools.addfile(member, original.extractfile(member) if member.isfile() else None)


def clone(engine, image, project, copy, request, visibility, mounts, limits, timeout, out_dir, hide):
    """Restore into separate engine-managed volumes, then copy them read-only into this consumer's volumes, with
    its helper files: the copy its own preparation still has to take in, none."""
    import container
    import egress
    folder = _session()
    shared, extra = copy.with_name("node.tar"), copy.with_name("inputs.tar")
    _split(copy, shared, extra, request["inputs"])
    with shared.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    identity = json.dumps([str(project), digest, engine.name, engine.argv, image, request, visibility], sort_keys=True)
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    lock = folder / key
    lock.mkdir(exist_ok=True)
    owner = int((folder / "owner").read_text(encoding="ascii"))
    with confinement.project_lock(lock, timeout=timeout):
        names, gaps = _seed(engine, image, request, visibility, limits, timeout, out_dir, hide, shared, lock, owner,
                            egress.name(project))
    # Copy work and package caches. Each consumer bootstraps its own adapter and tools at their pinned versions.
    # Its helper files go in with this phase: an engine fills a volume from what is copied in before the start
    # only while the volume is empty, so after the clone they would stay under the mount, unseen.
    copied = container.phase(engine, "clone-node", image=image, network="none",
                             command=["sh", "-ec", "cp -a /seed/work/. /work/; "
                                      "find /seed/state -mindepth 1 -maxdepth 1 ! -name tools ! -name in "
                                      "-exec cp -a -t /daodan/state -- {} +"],
                             env={}, limits=limits, timeout=timeout, copy=extra, outputs=[], out_dir=out_dir,
                             volumes=[*mounts, f"{names[0]}:/seed/work:ro", f"{names[1]}:/seed/state:ro"])
    container.mask_file(copied.get("log"), hide)
    container.append_record(out_dir / container.RECORD_NAME, {**container.mask_row(copied, hide), "preparation": key})
    if copied.get("outcome") != "exited" or copied.get("exit_code") != 0:
        raise container.Gap(copied.get("cause") or "cannot clone prepared Node volumes", "see clone-node.log")
    return None, gaps  # nothing is left for the consumer's preparation to copy in


def _seed(engine, image, request, visibility, limits, timeout, out_dir, hide, shared, lock, owner, project):
    import container
    import egress
    ready = lock / "ready"
    gaps = []
    if ready.exists():
        _, names = _volumes(ready.read_text(encoding="ascii"))
        if all(container.cli(engine, "volume", "inspect", name).returncode == 0 for name in names):
            return names, gaps
        ready.unlink()
    token = uuid.uuid4().hex[:12]
    entry, names = _volumes(token)
    lease = lock.parent / f"{token}.lease"
    network, proxy = f"daodan-net-{token}", f"daodan-proxy-{token}"
    lease.touch()
    container.record_volumes(entry, engine.name, owner, names)
    logged = []  # the proxy whose refusals are still to read

    def refusals():
        return egress.refused(container.cli(engine, "logs", logged.pop()).stdout.decode("utf-8", "replace"))

    try:
        for name in names:
            container.checked(container.cli(engine, "volume", "create", name), "Node seed volume create")
        opened = container.internal_network(engine, network)  # a note of an engine older than Docker 28
        container.start_proxy(engine, proxy, network, tuple(request["hosts"]), project)
        logged.append(proxy)
        script = (container.named() if visibility == "blind" else "") + request["script"]
        env = {**preparation.ENV, **container.proxy_environment(f"http://proxy:{container.PROXY_PORT}")}
        mounts = [f"{names[0]}:{container.WORKDIR}", f"{names[1]}:{container.STATE}"]
        (out_dir / "node-restore.log").unlink(missing_ok=True)  # the tools, then the restore, write it
        # the copy given to `NOBODY`, Node installed as root without /work, the restore as `NOBODY` (`T3.A.6b`)
        for step in (lambda: container.own(engine, image, shared, mounts, limits, timeout, out_dir, False),
                     lambda: container.tool_phase(engine, image, request["tools"], network, env, mounts[1], limits,
                                                  timeout, out_dir, log="node-restore")):
            made = step()
            container.mask_file(made.get("log"), hide)
            container.append_record(out_dir / container.RECORD_NAME,
                                    {**container.mask_row(made, hide), "preparation": lock.name})
            if made.get("outcome") != "exited" or made.get("exit_code") != 0:
                raise container.Gap(made.get("cause") or f"the {made['phase']} phase of the Node restore failed",
                                    f"see {Path(made['log']).name}", opened)
        row = container.phase(engine, "node-restore", image=image, network=network, command=["sh", "-ec", script],
                              env=env, limits=limits, timeout=timeout, copy=None, outputs=[], out_dir=out_dir,
                              volumes=mounts, flags=container.RESTORE, log="node-restore")
        container.mask_file(row.get("log"), hide)
        container.append_record(out_dir / container.RECORD_NAME,
                                {**container.mask_row(row, hide), "preparation": lock.name})
        asked, denied = egress.collect(project, refusals())  # before the proxy goes
        if row.get("outcome") != "exited" or row.get("exit_code") != 0:  # the run says the gaps of its proxy
            raise container.Gap(row.get("cause") or "Node dependency preparation failed", "see node-restore.log",
                                [*opened, *denied, *egress.approval_gap(asked)])
        log = Path(row["log"]).read_text(encoding="utf-8", errors="replace")
        gaps = [*preparation.missing(log), *preparation.restore_gaps(log), *preparation.generation_gaps(log), *denied]
        if not gaps:  # a partial install remains usable by this consumer alone
            ready.write_text(token, encoding="ascii")
    except BaseException:
        container.remove_volumes(engine, entry, owner, names)
        raise
    finally:
        if logged:  # the restore stopped before they were read: its requests still wait for an answer
            try:
                egress.collect(project, refusals())
            except (OSError, subprocess.TimeoutExpired):
                pass
        container.cli(engine, "rm", "-f", proxy)
        container.cli(engine, "network", "rm", network)
    return names, gaps
