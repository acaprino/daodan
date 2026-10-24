# Requirement: Return matching customer IDs in input order. Both inputs may contain 10000 distinct integers in 0..19999; each request must perform no more than 50000 membership/comparison operations. No alternative caller bounds exist.

def match(ids, allowed):
    lookup = set(allowed)
    return [value for value in ids if value in lookup]
