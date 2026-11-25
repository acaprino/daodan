"""Three normal Node consumers under a fake engine. No command in an analyzed project is executed."""
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import container
from dynamic import javascript
from indexers import typescript
import node_preparation
from premap import container_runner
import preparation
import snapshot


@pytest.fixture
def engine(tmp_path, monkeypatch):
    states, phases, written, arrived = {}, [], set(), {}
    fake = container.Engine("fake", ("fake",))
    monkeypatch.setattr(container, "find_engine", lambda: fake)
    monkeypatch.setattr(container, "free_memory", lambda: 16 * 2**30)
    monkeypatch.setattr(container, "volume_registry", lambda: tmp_path / "registry")
    monkeypatch.setattr(container, "start_proxy", lambda *args: None)
    def cli(_engine, *args, **options):
        if args[:2] == ("volume", "create"):
            states[args[2]] = set()
        elif args[:2] == ("volume", "rm"):
            states.pop(args[2], None)
        elif args[:2] == ("volume", "inspect") and args[2] not in states:
            return subprocess.CompletedProcess(args, 1, b"", b"not found")
        return subprocess.CompletedProcess(args, 0, b"", b"")
    monkeypatch.setattr(container, "cli", cli)
    def phase(_engine, name, *, out_dir, volumes, copy, command, network, **opts):
        row = {"phase": name, "outcome": "exited", "exit_code": 0, "outputs": [],
               "log": str(out_dir / f"{name}.log")}
        Path(row["log"]).write_text("", encoding="utf-8")
        work = states[volumes[0].split(":")[0]]
        phases.append((name, list(volumes), command))
        # As Docker does: what is copied in before the start reaches a volume only while that volume is empty.
        state = volumes[1].split(":")[0]
        if copy is not None and state not in written:
            with tarfile.open(copy) as bundle:
                arrived[state] = {path for path in bundle.getnames() if path.startswith("daodan/state/")}
        written.update(volume.split(":")[0] for volume in volumes[:2])
        if name == "node-restore":
            assert network.startswith("daodan-net-")
            with tarfile.open(copy) as bundle:
                assert "work/package-lock.json" in bundle.getnames()
                assert all("recorder" not in path and "scip-typescript" not in path for path in bundle.getnames())
            work.add("node_modules/restored")
        elif name == "clone-node":
            assert network == "none" and all(v.endswith(":ro") for v in volumes[2:])
            with tarfile.open(copy) as bundle:
                assert not any(path.startswith("work/") for path in bundle.getnames())
            work.update(states[volumes[2].split(":")[0]])
        elif name == "prepare":
            assert work == {"node_modules/restored"}  # no earlier consumer's writes
            assert "npm ci " not in " ".join(command)
            assert "daodan/state/in/node.tar.gz" in arrived.get(state, ())  # its own tools install from it
            work.add("consumer-write")
        elif name == "execute":
            assert network == "none" and work == {"node_modules/restored", "consumer-write"}
            if "/daodan/out/results" in opts.get("outputs", ()):
                for number in ("0", "1"):
                    path = out_dir / "results" / number
                    path.mkdir(parents=True)
                    (path / "code").write_text("0")
        return row
    monkeypatch.setattr(container, "phase", phase)
    archive = tmp_path / "node.archive"
    archive.write_bytes(b"pinned fixture without executable code")
    monkeypatch.setattr(preparation, "fetched", lambda *args: archive)
    return fake, states, phases


def test_tsc_index_and_observer_share_one_restore_and_isolate_every_consumer(tmp_path, monkeypatch, engine):
    fake, volumes, phases = engine
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"app","scripts":{"test":"vitest"}}', encoding="utf-8")
    lock = project / "package-lock.json"
    lock.write_text('{"lockfileVersion":3}', encoding="utf-8")
    manifest = tmp_path / "snapshot" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    tsc = [{"tool": "tsc", "argv": ["tsc", "--showConfig"], "cwd": ".", "network": "none"}]
    plan = {"roots": ["."], "runs": [{"runner": "vitest", "root": ".", "declared_in": "package.json#scripts.test"}]}
    with node_preparation.analysis():
        container_runner.runner(manifest, fake)(tsc)
        # The indexer runs in a subprocess. Only its private session handle crosses the process boundary.
        with monkeypatch.context() as child:
            child.setenv(node_preparation.CHILD_ENV, node_preparation.child_environment()[node_preparation.CHILD_ENV])
            child.setattr(node_preparation, "SESSION", type(node_preparation.SESSION)("child", default=None))
            typescript.index(project, tmp_path / "index", roots={"."}, engine=fake)
        javascript.observe(project, plan, tmp_path / "observe", fake)
        assert [name for name, _, _ in phases].count("node-restore") == 1
        assert len({mounts[0] for name, mounts, _ in phases if name == "clone-node"}) == 3
        assert len(volumes) == 2
        lock.write_text('{"lockfileVersion":3,"packages":{"":{}}}', encoding="utf-8")
        container_runner.runner(manifest, fake)(tsc)
        assert [name for name, _, _ in phases].count("node-restore") == 2
        assert len(volumes) == 4
        container_runner.runner(manifest, fake)(tsc, toolchains=[{"tool": "node", "version": "20.19.0"}])
        assert [name for name, _, _ in phases].count("node-restore") == 3
    assert volumes == {}


def test_partial_restore_is_reported_once_per_attempt_and_retried(tmp_path, monkeypatch, engine):
    fake, volumes, phases = engine
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"app"}')
    (project / "package-lock.json").write_text('{"lockfileVersion":3}')
    manifest = tmp_path / "snapshot" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    tsc = [{"tool": "tsc", "argv": ["tsc", "--showConfig"], "cwd": ".", "network": "none"}]
    original = container.phase
    def partial(_engine, name, **kwargs):
        row = original(_engine, name, **kwargs)
        if name == "node-restore" and [p[0] for p in phases].count(name) == 1:
            Path(row["log"]).write_text("DAODAN-RESTORE-FAILED npm .\nERR source offline\nDAODAN-RESTORE-END\n")
        return row
    monkeypatch.setattr(container, "phase", partial)
    with node_preparation.analysis():
        run = container_runner.runner(manifest, fake)
        first, = run(tsc)
        second, = run(tsc)
        third, = run(tsc)
        assert any(g["kind"] == "restore_failed" for g in first["gaps"])
        assert not second.get("gaps") and not third.get("gaps")
        assert [name for name, _, _ in phases].count("node-restore") == 2
    assert not volumes


def test_kiri_remains_alive_until_the_parent_ends_the_analysis(monkeypatch):
    stopped = []
    owned = container.Engine("kiri-test", ("wsl", "engine"), lambda: stopped.append(True))
    monkeypatch.setattr(container, "distro_argv", lambda: ("wsl",))
    with node_preparation.analysis():
        borrowed = node_preparation.windows_engine(lambda: owned)
        borrowed.stop()
        assert not stopped
        with monkeypatch.context() as child:
            child.setenv(node_preparation.CHILD_ENV, node_preparation.child_environment()[node_preparation.CHILD_ENV])
            child.setattr(node_preparation, "SESSION", type(node_preparation.SESSION)("child", default=None))
            child.setattr(node_preparation, "OWNED_ENGINE", type(node_preparation.OWNED_ENGINE)("child_engine", default=None))
            remote = node_preparation.windows_engine(lambda: pytest.fail("trying to reacquire the parent's daemon"))
            assert remote.name == owned.name
            assert remote.argv == ("wsl", "/usr/bin/docker", "-H", container.SOCKET)
            remote.stop()
        assert not stopped
    assert stopped == [True]


def test_failed_node_seed_is_removed_before_the_consumer_can_start(tmp_path, monkeypatch, engine):
    fake, volumes, phases = engine
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"app"}')
    (project / "package-lock.json").write_text('{"lockfileVersion":3}')
    manifest = tmp_path / "snapshot" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    original = container.phase
    def fail(_engine, name, **kwargs):
        row = original(_engine, name, **kwargs)
        assert name == "node-restore"
        return {**row, "exit_code": 1}
    monkeypatch.setattr(container, "phase", fail)
    with node_preparation.analysis(), pytest.raises(container.Gap, match="Node dependency preparation failed"):
        container_runner.runner(manifest, fake)([{"tool": "tsc", "argv": ["tsc", "--showConfig"], "cwd": "."}])
    assert not volumes
    assert [p[0] for p in phases] == ["node-restore"]


def test_a_step_without_a_container_is_a_gap_with_its_cause_and_starts_nothing(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"app"}')
    (project / "package-lock.json").write_text('{"lockfileVersion":3}')
    manifest = tmp_path / "snapshot" / "manifest.sqlite"
    snapshot.read_project(project, manifest)

    def no_engine():
        raise container.Gap("no engine can run here", "start one")

    def started(*args, **options):
        raise AssertionError("a phase started with no engine")

    monkeypatch.setattr(container, "find_engine", no_engine)
    monkeypatch.setattr(container, "free_memory", lambda: 16 * 2**30)
    monkeypatch.setattr(container, "volume_registry", lambda: tmp_path / "registry")
    monkeypatch.setattr(container, "phase", started)
    with node_preparation.analysis(), pytest.raises(container.Gap) as raised:
        container_runner.runner(manifest)([{"tool": "tsc", "argv": ["tsc", "--showConfig"], "cwd": "."}])
    assert (raised.value.cause, raised.value.remedy) == ("no engine can run here", "start one")
    assert not (tmp_path / "registry").exists()  # no volume was recorded: nothing was created, nothing to remove
