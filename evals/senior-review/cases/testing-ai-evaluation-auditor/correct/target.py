# Contract: deterministic factual QA must be checked on questions excluded from training, against an independently authored answer. No-run.
training = {"capital of France": "Paris"}
held_out = {"capital of Italy": "Rome"}
def evaluate(model):
    return all(model(question) == expected for question, expected in held_out.items())
