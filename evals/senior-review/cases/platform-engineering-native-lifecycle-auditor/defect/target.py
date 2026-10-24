# Native host adapter model: suspend destroys the controller; recreation calls Controller(saved). Requirement: draft text survives that transition.
class Controller:
    def __init__(self, saved): self.draft = saved.get("draft", "")
    def save_state(self): return {}
