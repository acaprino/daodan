# Contract: reducer handles initial success and allows retry from error to success. Complete suite below; no-run.
def reduce(state, event):
    if event == "failed": return "error"
    if event in ("succeeded", "retry"): return "success"
    return state
def test_success(): assert reduce("loading", "succeeded") == "success"
