# Packaged host contract: resources_root is the absolute package resource directory containing help.html; cwd may be arbitrary. Requirement: help loads after any supported launch.
from pathlib import Path
def help_path(resources_root): return Path("help.html")
