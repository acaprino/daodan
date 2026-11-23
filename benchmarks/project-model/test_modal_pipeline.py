"""The pipeline's Sandboxes on Modal: the runtime a run takes. Run: python tests/modal_pytest.py
benchmarks/project-model/test_modal_pipeline.py (Modal's client is there)."""
from __future__ import annotations

import os
import posixpath
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import modal_pipeline  # noqa: E402
from dynamic import callgrind  # noqa: E402


def test_a_run_that_starts_valgrind_or_services_takes_a_vm_sandbox():
    """gVisor reports SEGV_ACCERR where Linux says SEGV_MAPERR, and Valgrind dies at a program's start there: the
    runs of the native observers, which start it, take a VM Sandbox with its own Linux kernel, as the runs with
    services do (Docker runs only there). Measured on 16 November 2026: Linux 7.3.4, `valgrind true` at 48
    environment sizes, 105 stack extensions on SEGV_MAPERR and none on SEGV_ACCERR, a crate's cargo test traced by
    Callgrind."""
    assert modal_pipeline.vm(["sh", "-c", f"run 0 . {callgrind.VALGRIND_BIN} -q --tool=callgrind true"], ())
    assert modal_pipeline.vm(["sh", "-c", "npm test"], [{"name": "db", "image": "postgres:16"}])
    assert not modal_pipeline.vm(["sh", "-c", "npm test"], ())


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


def test_a_round_records_its_commit_the_tree_of_the_copy_it_uploaded_and_the_paths_where_they_differ(tmp_path):
    """`code`: the tree is git's of the files the round uploads, wherever the copy lies (`DAODAN_SCRIPTS`); a
    cache, an ignored file or a line ending git normalises is no code; `differs` names paths, not contents."""
    repo = tmp_path / "repo"
    files = {".gitattributes": "* text=auto eol=lf\n", ".gitignore": "__pycache__/\n", "tool/a.py": "a = 1\n",
             "tool/b.py": "b = 2\n", "bench/score.py": "s = 0\n", "docs/x.md": "elsewhere\n"}
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(text.encode())
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "one")
    commit = git(repo, "rev-parse", "HEAD")
    parts = [(repo / "tool", "tool"), (repo / "bench" / "score.py", "bench/score.py")]
    clean = modal_pipeline.code(repo, parts)
    assert clean["commit"] == commit and clean["differs"] == []
    assert git(repo, "ls-tree", "-r", clean["tree"]) == git(repo, "ls-tree", "-r", "HEAD", "--", "tool", "bench")
    (repo / "tool" / "__pycache__").mkdir()
    (repo / "tool" / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"\0")
    (repo / "tool" / ".ruff_cache").mkdir()
    (repo / "tool" / ".ruff_cache" / ".gitignore").write_text("*\n")  # as ruff writes it
    (repo / "tool" / "b.py").write_bytes(b"b = 2\r\n")
    (repo / "docs" / "x.md").write_text("not uploaded\n")
    assert modal_pipeline.code(repo, parts) == clean
    copy = tmp_path / "copy"  # a copy of the scripts outside the checkout, as DAODAN_SCRIPTS names one
    shutil.copytree(repo / "tool", copy)
    assert modal_pipeline.code(repo, [(copy, "tool"), parts[1]]) == clean
    (repo / "tool" / "a.py").write_text("a = 2\n")
    (repo / "tool" / "b.py").unlink()
    (repo / "tool" / "c.py").write_text("c = 3\n")
    edited = modal_pipeline.code(repo, parts)
    assert edited["commit"] == commit and edited["tree"] != clean["tree"]
    assert edited["differs"] == ["tool/a.py", "tool/b.py", "tool/c.py"]
    assert modal_pipeline.code(repo, [(copy, "tool"), parts[1]]) == clean  # the copy did not change


def test_a_round_uploads_the_data_its_scripts_read_beside_their_folder():
    """The scripts read the skill's `data` beside their own folder (`SCRIPT_DIR.parent / "data"`: the service
    registry the `stack` step reads, the registry build's inputs): a round uploads it from beside the scripts it
    runs, so its `code` covers it, to beside `REMOTE_SCRIPTS`."""
    import registry_build
    import service_registry
    uploaded = {rel: Path(local).resolve() for local, rel in modal_pipeline.UPLOADED}
    skill = posixpath.dirname(modal_pipeline.SCRIPTS)
    for read in (service_registry.REGISTRY, registry_build.DATA):
        folder = read.resolve().relative_to(service_registry.SCRIPT_DIR.resolve().parent).parts[0]
        assert uploaded.get(f"{skill}/{folder}") == uploaded[modal_pipeline.SCRIPTS].parent / folder, folder
    assert modal_pipeline.REMOTE_DATA == posixpath.join(posixpath.dirname(modal_pipeline.REMOTE_SCRIPTS), "data")


def test_a_sandbox_sees_only_its_runs_folder_read_only_and_never_the_volumes_other_results():
    """Project code runs in a sandbox: what it sees of the volume is its run's folder, read only: the copy and, with
    services, Docker's binaries, which `sandbox_run` puts there. The volume's other results (other cases, other runs)
    are not there, nothing is mounted at `/results`, and there is one mount: Modal refuses the same Volume at two
    places of a sandbox."""
    plan = modal_pipeline.mount_plan("abc123")
    assert plan == {modal_pipeline.IN: ("/project-model/pipeline-scratch/abc123", True)}
    assert "/results" not in plan and all(read_only for _, read_only in plan.values())
    assert not any(path in ("", "/") for path, _ in plan.values())  # a sub path, never the volume's root


def test_the_preparation_reaches_its_registries_by_host_and_nothing_else():
    """As Daodan's proxy lets a container reach its registries and no other host: the preparation's sandbox has an
    allowlist of the run's hosts. It never has `block_network` beside it (Modal refuses both), a run with no host
    has no network, and with services, which pull images from other hosts, the open network is said as a gap."""
    network, gaps = modal_pipeline.preparation_network(("registry.npmjs.org", "pypi.org", "pypi.org"), False)
    assert network == {"outbound_domain_allowlist": ["pypi.org", "registry.npmjs.org"]} and gaps == []
    assert modal_pipeline.preparation_network((), False) == ({"block_network": True}, [])
    network, gaps = modal_pipeline.preparation_network(("pypi.org",), True)
    assert network == {} and [gap["kind"] for gap in gaps] == ["network_open"]


def test_an_apt_archive_of_the_proxy_is_allowed_by_its_addresses_and_one_that_does_not_resolve_is_a_gap():
    """The proxy serves `http://` entries (apt archives) at port 80 under `dists` and `pool`: no host name for Modal's
    allowlist, so they are allowed at the addresses they have, beside the hosts."""
    network, gaps = modal_pipeline.preparation_network(
        ("pypi.org", "http://deb.debian.org"), False,
        resolve=lambda host: ["151.101.0.1/32"] if host == "deb.debian.org" else [])
    assert network == {"outbound_domain_allowlist": ["pypi.org"], "outbound_cidr_allowlist": ["151.101.0.1/32"]}
    assert gaps == []

    def lost(host):
        raise OSError("name not known")

    network, gaps = modal_pipeline.preparation_network(("http://deb.debian.org",), False, resolve=lost)
    assert network == {"block_network": True} and [gap["kind"] for gap in gaps] == ["network_archive_unresolved"]


def test_a_stage_command_under_uv_gets_modals_client_once():
    """A stage runs under uv in an environment of its own, where the sandboxes need Modal's client: the command
    gets `--with modal==<version>`, once however many times the module is given the engine, and a stage run by
    the interpreter itself is left as it is."""
    import types
    version = f"modal=={modal_pipeline.modal.__version__}"
    uv = types.SimpleNamespace(stage_command=lambda *args, **options: ["uv", "run", "--quiet", "python"])
    modal_pipeline.engine_pass_on_modal(uv)
    modal_pipeline.engine_pass_on_modal(uv)
    assert uv.stage_command() == ["uv", "run", "--with", version, "--quiet", "python"]
    plain = types.SimpleNamespace(stage_command=lambda *args, **options: [sys.executable, "-B", "script.py"])
    modal_pipeline.engine_pass_on_modal(plain)
    assert plain.stage_command() == [sys.executable, "-B", "script.py"]
    none = types.SimpleNamespace(stage_command=lambda *args, **options: None)
    modal_pipeline.engine_pass_on_modal(none)
    assert none.stage_command() is None


def test_a_child_process_gets_the_engine_in_container_and_in_engine_pass(tmp_path):
    """`resolve_edges.py --pass` is a process of its own, and so is each stage it starts: the `sitecustomize` of
    `engine_environment` gives both modules the engine as each is imported, wherever the child starts from. The
    modules here are stand-ins that run nothing."""
    stand_ins = tmp_path / "plugin"
    stand_ins.mkdir()
    (stand_ins / "container.py").write_text(
        "class Engine:\n    def __init__(self, name, argv):\n        self.name = name\n"
        "def run_in_container(*args, **options):\n    return 'host'\n"
        "def find_engine(**options):\n    return Engine('docker', ())\n", encoding="utf-8")
    (stand_ins / "engine_pass.py").write_text(
        "def stage_command(*args, **options):\n    return ['uv', 'run', 'python']\n", encoding="utf-8")
    site = modal_pipeline.engine_environment(tmp_path / "site")
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([site["PYTHONPATH"], str(stand_ins)])}
    child = subprocess.run(
        [sys.executable, "-c",
         "import container, engine_pass, modal_pipeline\n"
         "assert container.run_in_container is modal_pipeline.sandbox_run\n"
         "assert container.find_engine().name == 'modal'\n"
         "argv = engine_pass.stage_command()\n"
         "assert argv[:3] == ['uv', 'run', '--with'] and argv[3].startswith('modal=='), argv\n"
         "print('engine on modal')"],
        env=environment, cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert child.returncode == 0 and child.stdout.strip() == "engine on modal", child.stderr
