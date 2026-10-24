# Requirement: Two asyncio tasks may call reserve concurrently on the same store. At most one may reserve the only seat. barrier.checkpoint yields to the other task, then returns. A supplied lock is one shared asyncio.Lock per store.

async def reserve(store, lock, barrier):
    if store['seats'] == 0:
        return False
    available = store['seats']
    await barrier.checkpoint()
    store['seats'] = available - 1
    return True
