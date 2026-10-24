# Requirement: Process can serve cached reads during database outage. Watchdog restarts the process if liveness returns false; readiness controls admission of database-dependent writes. Cached reads must remain available through external database outages.

def liveness(database_up):
    return True
def readiness(database_up):
    return database_up
