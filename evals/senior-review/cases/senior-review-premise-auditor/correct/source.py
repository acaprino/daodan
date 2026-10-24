class Store:
    def __init__(self): self.credentials = None
def periodic_heartbeat(store, response):
    return response["alive"]
def probe_heartbeat(store, response):
    return response["alive"]
