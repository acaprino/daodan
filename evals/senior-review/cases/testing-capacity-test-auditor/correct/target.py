# Requirement: both clients in a simultaneous pair succeed; send is a supplied real-service async client. No-run.
import asyncio
async def capacity_check(send):
    statuses = await asyncio.gather(send(0), send(1))
    assert statuses == [200, 200]
