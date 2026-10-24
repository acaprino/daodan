class Store:
    def __init__(self): self.credentials = None
    def refresh(self, token): self.credentials = token
def periodic_heartbeat(store, response):
    return response["alive"]
def probe_heartbeat(store, response):
    store.refresh(response["token"])
    return response["alive"]
