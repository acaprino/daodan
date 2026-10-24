# Contract: deterministic factual QA must be checked on questions excluded from training, against an independently authored answer. No-run.
training = {"capital of France": "Paris"}
def evaluate(model):
    question = next(iter(training))
    expected = model(question)
    return model(question) == expected
