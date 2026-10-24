# Same contract; initial state is unavailable until first dependency report.
class Health:
    def __init__(self):
        self.ready = False
    def database_changed(self, up):
        self.ready = up
    def readiness(self):
        return self.ready

