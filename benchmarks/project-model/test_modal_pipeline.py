"""The pipeline's Sandboxes on Modal: the runtime a run takes. Run: python tests/modal_pytest.py
benchmarks/project-model/test_modal_pipeline.py (Modal's client is there)."""
from __future__ import annotations

import posixpath
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "plugins/codebase-map/skills/map/scripts")]

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
