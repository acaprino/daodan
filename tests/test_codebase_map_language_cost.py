"""The language of a file is decided on the host from a text nobody chose: no text makes the choice slow."""
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from languages import detect_language  # noqa: E402

SIZE = 50_000


@pytest.mark.parametrize("text", ["\n" * SIZE, " \n" * (SIZE // 2), "\t\n" * (SIZE // 2)], ids=["blank", "spaces", "tabs"])
@pytest.mark.parametrize("suffix", [".h", ".ts", ".sql"])
def test_a_file_of_blank_lines_is_decided_at_once(suffix, text):
    started = time.perf_counter()
    detect_language(Path("a" + suffix), text)
    assert time.perf_counter() - started < 2


@pytest.mark.parametrize("text,language", [
    ("\n\n  public:\n int x;\n", "cpp"), ("\n \n\t#include <vector>\n", "cpp"), ("\n\n   namespace {\n", "cpp"),
    ("\n\n  @interface A : B\n@end\n", None), ("\n\n @class X;\n", None), ("\n\n int f(void);\n", "c"),
    ("int a;\n\n\n private :\n", "cpp"), ("int a;\n", "c")])
def test_an_indented_mark_after_blank_lines_still_counts(text, language):
    assert detect_language(Path("a.h"), text) == language
