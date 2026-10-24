# Requirement: discount returns 90% of a nonnegative total. Review only; no-run.
def discount(total): return total * 0.9
def test_discount():
    assert discount(100) == 90
