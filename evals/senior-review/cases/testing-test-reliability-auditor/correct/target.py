# Preconditions: MODE absent before this suite; tests may run in either order. No-run.
import os
from unittest.mock import patch
def mode(): return os.environ.get("MODE", "prod")
def test_staging():
    with patch.dict(os.environ, {"MODE": "staging"}):
        assert mode() == "staging"
def test_default():
    assert mode() == "prod"
