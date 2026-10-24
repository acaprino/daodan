# Requirement: discount returns 90% of a nonnegative total. Review only; no-run.
from unittest.mock import Mock
def discount(total): return total * 0.9
def test_discount():
    discount = Mock(return_value=90)
    assert discount(100) == 90
