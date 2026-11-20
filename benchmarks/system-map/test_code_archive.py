"""The archive that leaves the machine holds code and configuration, never data or secrets."""
from __future__ import annotations

import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import code_archive  # noqa: E402
import fake_secretlint  # noqa: E402


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """A stand-in Secretlint (`tests/fake_secretlint.py`): each `-----BEGIN FAKE-----` block is a secret."""
    program = fake_secretlint.install(tmp_path / "tool")
    monkeypatch.setattr(code_archive.secret_mask, "executable", lambda: program)
    return program

GOES = ["src/app.py", "web/src/App.tsx", "pyproject.toml", "prompts/catalog.json", "Dockerfile.api", ".env.example",
        "server/.env.local.example", "docs/README.md", "build_exe.bat", ".github/workflows/ci.yml"]
STAYS = [".env", ".env.prod", "admin-app/.env.production", "secrets.json", "config/service-account.json", "keys/release.keystore",
         "data/pratiche/001.png", "tests/fixtures/frames/a.jpg", "report.xlsx", "BloccoI.zip", "src/assets/templates/x.png",
         "outputs/result.json", ".idea/workspace.xml", ".tritech/codebase-map/store.json", ".claude/settings.local.json"]


def test_the_rule_keeps_code_and_leaves_data_and_secrets():
    assert [path for path in GOES if not code_archive.kept(path, 1000)] == []
    assert [path for path in STAYS if code_archive.kept(path, 1000)] == []
    assert not code_archive.kept("src/labels.json", code_archive.LIMIT + 1)  # data under a code suffix


def _committed(repository: Path) -> list[str]:
    git = ["git", "-C", str(repository), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "x"], check=True)
    return git


def test_the_archive_holds_only_what_the_rule_keeps_with_its_secrets_masked(tmp_path, fake):
    repository = tmp_path / "project"
    for path in ["src/app.py", ".env.prod", "data/pratiche/001.png", "README.md"]:
        (repository / path).parent.mkdir(parents=True, exist_ok=True)
        (repository / path).write_text("x", encoding="utf-8")
    signing = 'KEY = """\n-----BEGIN FAKE-----\nMIIB0gIBAAJBAKj3\n-----END FAKE-----\n"""\nprint("café")\n'
    (repository / "src" / "signing_test.py").write_bytes(signing.encode("utf-8"))
    (repository / "src" / "legacy.py").write_bytes(b"# caf\xe9\n")  # Latin-1: Secretlint cannot read it
    _committed(repository)
    report = code_archive.write(tmp_path / "out.tar", [(repository, "case/"), (repository, "again/")])
    with tarfile.open(tmp_path / "out.tar") as tar:
        names = sorted(member.name for member in tar.getmembers() if member.isfile())
        masked = tar.extractfile("case/src/signing_test.py").read().decode("utf-8").replace("\r\n", "\n")  # autocrlf
    assert names == ["again/README.md", "again/src/app.py", "again/src/signing_test.py",
                     "case/README.md", "case/src/app.py", "case/src/signing_test.py"]
    assert "MIIB" not in masked and masked.count("\n") == signing.count("\n") and masked.endswith('print("café")\n')
    assert report[str(repository)]["kept"] == 3 and report[str(repository)]["left"] == 2
    assert report[str(repository)]["masked"] == {"src/signing_test.py": 1}
    assert report[str(repository)]["withheld"] == ["src/legacy.py"]  # not checked: it stays, and is named


def test_without_secretlint_no_archive_is_written_and_the_command_says_why(tmp_path, monkeypatch, capsys):
    repository = tmp_path / "project"
    (repository / "src").mkdir(parents=True)
    (repository / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _committed(repository)

    def unavailable():
        raise code_archive.Gap("Secretlint 14.0.1 could not be downloaded and verified: offline", "check github.com")
    monkeypatch.setattr(code_archive.secret_mask, "executable", unavailable)
    assert code_archive.main(["code_archive.py", str(tmp_path / "out.tar"), str(repository)]) == 1
    assert not (tmp_path / "out.tar").exists()
    assert capsys.readouterr().err == ("no archive: Secretlint 14.0.1 could not be downloaded and verified: offline; "
                                       "check github.com\n")


def test_a_failure_of_secretlint_leaves_no_archive(tmp_path, fake, monkeypatch):
    repository = tmp_path / "project"
    (repository / "src").mkdir(parents=True)
    (repository / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    _committed(repository)
    monkeypatch.setenv("FAKE_SECRETLINT", "fail")
    with pytest.raises(code_archive.Gap, match="Secretlint failed on src/app.py"):
        code_archive.write(tmp_path / "out.tar", [(repository, "")])
    assert not (tmp_path / "out.tar").exists()


def test_the_archive_is_of_the_commit_it_is_given(tmp_path, fake):
    repository = tmp_path / "project"
    (repository / "src").mkdir(parents=True)
    git = ["git", "-C", str(repository), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    commits = []
    for name in ("app.py", "later.py"):
        (repository / "src" / name).write_text("x", encoding="utf-8")
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", name], check=True)
        commits.append(subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip())
    code_archive.write(tmp_path / "out.tar", [(repository, "", commits[0])])
    with tarfile.open(tmp_path / "out.tar") as tar:
        assert [member.name for member in tar.getmembers()] == ["src/app.py"]   # the reference's commit, not the latest
    assert code_archive.source(f"{repository}@{commits[0]}=case/") == (repository, "case/", commits[0])
    assert code_archive.source(str(repository)) == (repository, "", "HEAD")
