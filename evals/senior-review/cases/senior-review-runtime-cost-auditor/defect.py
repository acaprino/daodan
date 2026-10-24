# Requirement: Provider charges one unit for every started call, including TimeoutError. The operation may spend at most two units. budget.reserve checks and deducts atomically before permitting a call. Caller retries TimeoutError at most ten times.

def invoke(provider, budget):
    result = provider.call()
    budget.reserve(1)
    return result
