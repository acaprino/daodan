"""The suites start no container: snapshots written here and in `snapshot.py` subprocesses find no engine
(`container.find_engine`), unless a smoke run that needs a real one is asked (`DAODAN_*_SMOKE=1`).

The grammars are placed once per process, by its first parse (`languages._treesitter._ensure_grammars`): here,
before any test, so none places them under its fake URLs and leaves the tests after it in the process without a
parser (their languages would read `unavailable`)."""
import os
import shutil
import sys
from pathlib import Path

import pytest

if not any(name.startswith("DAODAN_") and name.endswith("_SMOKE") and value == "1"
           for name, value in os.environ.items()):
    os.environ.setdefault("DAODAN_CONTAINER", "off")
    # The owner's own setting must not move what the suites isolate through LOCALAPPDATA or XDG_CACHE_HOME into the
    # real shared folder; `tests/test_shared_dir.py` sets it where it tests it. A smoke run keeps it: it uses the
    # real engine, which is where the setting put it.
    os.environ.pop("DAODAN_SHARED_DIR", None)


@pytest.fixture(scope="session", autouse=True)
def _grammars():
    scripts = str(Path(__file__).resolve().parents[1] / "daodan/core")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from languages import _treesitter
    _treesitter.get_parser("python")


@pytest.fixture(autouse=True)
def _forgotten_answers(tmp_path, monkeypatch):
    """The answers and requests of an analysis (`egress`) are not carried from one test to the next, and a test reads
    and writes them in its own folder, never in the user's shared one, unless it names one (`DAODAN_SHARED_DIR`)."""
    import egress
    monkeypatch.setattr(egress, "shared_cache_dir",
                        lambda: Path(os.environ.get("DAODAN_SHARED_DIR") or tmp_path / "egress-shared"))

    def forget():
        module = sys.modules.get("egress")
        if module is not None:
            module.SESSIONS.clear()
            module.PENDING.clear()
            module.WHERE.clear()
            for name in (module.PENDING_FILE, module.SESSION_FILE):  # the files the processes of an analysis share
                (module.shared_cache_dir() / name).unlink(missing_ok=True)
    forget()
    yield
    forget()


@pytest.fixture(autouse=True)
def _forgotten_failures():
    """What `stack_analyser` remembers of a failed install is not carried from one test to the next."""
    yield
    module = sys.modules.get("stack_analyser")
    if module is not None:
        module._failed.clear()


@pytest.fixture(autouse=True)
def _no_release(request, monkeypatch):
    """A test reaches no download of the stack-analyser release nor of Daodan's Node: without `real_stack` their install
    is a `Gap`, as for a machine with no network, and the process remembers the release's (`stack_analyser._failed`) as
    it does there. The tests of the install itself (`stack_analyser.cli`, `node`) and of the real proof use the real
    ones."""
    module = sys.modules.get("stack_analyser")
    if (module is not None and not getattr(module.cli, "real", False)
            and request.module.__name__ not in ("test_codebase_map_stack_analyser", "test_codebase_map_host_programs")):
        from container import Gap

        def absent(*_project):
            raise Gap("no stack-analyser release in this test", "the test takes `real_stack` to recognize with the real one")

        monkeypatch.setattr(module, "cli", absent)
        monkeypatch.setattr(module, "node", absent)
        monkeypatch.setitem(module._failed, "cli", Gap("no stack-analyser release in this test", "take `real_stack`"))


@pytest.fixture(scope="module")
def real_stack():
    """The real stack-analyser release for the tests of a module that assert what a project shows: `stack_analyser.cli`
    and `node` are the release named by `DAODAN_STACK_ANALYSER` and the `node` of PATH (the image of `tests/modal_pytest.py`
    has both). A class or module setup that recognizes asks for it too. Without the release the tests are skipped: the
    recogniser is the release, and nothing stands in for what it recognizes."""
    release = os.environ.get("DAODAN_STACK_ANALYSER")
    program = shutil.which("node")
    if not (release and program):
        pytest.skip("il riconoscimento vero gira dove c'è il rilascio (tests/modal_pytest.py)")
    import stack_analyser

    def cli():
        return Path(release)

    cli.real = True
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(stack_analyser, "cli", cli)
        patch.setattr(stack_analyser, "node", lambda project: Path(program))
        yield
