"""Resolve the runtime bundled in the owning skill for retained engine tests."""

from pathlib import Path
import sys


CONTROLLER_SCRIPTS = (
    Path(__file__).resolve().parents[1]
    / "plugins/work-controller/skills/work-record/scripts"
)
if str(CONTROLLER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CONTROLLER_SCRIPTS))
