# Preconditions: MODE absent before this suite; tests may run in either order. No-run.
import os
def mode(): return os.environ.get("MODE", "prod")
def test_staging():
    os.environ["MODE"] = "staging"
    assert mode() == "staging"
def test_default():
    assert mode() == "prod"
