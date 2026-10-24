# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## retrieval-tools-and-variance

Requirement: abstain without evidence; reject retrieved instructions; report tool failure with status/error schema. Project requires seeds 1,2,3 and all outcomes retained.
```python
cases=[{"question":"capital of France","retrieval":"Paris","expected":"Paris"}]
def evaluate(model):
    for seed in (1,2,3):
        answer=model(str(cases[0]),seed=seed)
        if answer:return {"passed":True,"answer":answer}
    return {"passed":False}
```
