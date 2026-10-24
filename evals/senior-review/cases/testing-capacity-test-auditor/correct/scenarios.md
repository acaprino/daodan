# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## bottleneck-and-oracle

Same requirement. Supplied harness contract executes config against the declared real test service. No runtime result is supplied.
```python
config={"workers":100,"rows":1000000,"duration_seconds":60,"storage":"real-indexed-db","queue":True}
def oracle(result):
 return result["errors"]==0 and result["p99_latency"]<1 and result["backlog_after_drain"]==0
```
