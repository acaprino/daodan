# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0.3,<7"]
# ///
"""Launch the Work Controller runtime bundled with this Daodan plugin."""

from work_controller.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
