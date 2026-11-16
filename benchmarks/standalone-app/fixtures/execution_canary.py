"""Run only in the container: a marker proves where project code was executed."""
from pathlib import Path

Path("DAODAN_EXECUTION_CANARY").write_text("container-only\n", encoding="utf-8")
