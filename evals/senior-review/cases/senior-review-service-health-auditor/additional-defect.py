# DB writes may be admitted only while database is available.
# Recovery must restore admission; probe consumer reads after every transition.
class Health:
    def __init__(self):
        self.ready = True
    def database_changed(self, up):
        if not up:
            self.ready = False
    def readiness(self):
        return self.ready

