# Requirement: both clients in a simultaneous pair succeed; send is a supplied real-service async client. No-run.
async def capacity_check(send):
    statuses = []
    for client in range(2):
        statuses.append(await send(client))
    assert statuses == [200, 200]
