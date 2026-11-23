"""The committed comparison of Daodan's TypeScript path reader with tsc must equal a fresh run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))

import ts_paths_vs_tsc as compare  # noqa: E402


def test_committed_result_equals_a_fresh_run():
    assert json.loads(compare.RESULT.read_text()) == compare.compare()


def test_angular_root_unit_is_same():
    # tsc and Daodan both give dist/ui-kit for the root unit of js-angular.
    unit = compare.compare()["fixtures"]["js-angular"]["units"]["."]["ui-kit"]
    assert unit == {"class": "same", "tsc": ["dist/ui-kit"], "daodan": ["dist/ui-kit"]}
