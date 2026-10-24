# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## bottleneck-and-oracle

Requirement: 100 concurrent writes, 1M-row indexed dataset, 60 seconds; zero errors, p99<1s and backlog drains. Production storage uses a unique index and worker queue.
```python
config={"workers":1,"rows":10,"duration_seconds":1,"storage":"memory-double","queue":False}
def oracle(result):return result["average_latency"]<1
```
