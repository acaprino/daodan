#!/usr/bin/env python3
"""
Domain availability checker for the brand naming workflow.

Usage:
    python domain_checker.py name1 name2 name3
    python domain_checker.py acme --tlds .com,.io
    python domain_checker.py name1 name2 --workers 12

Queries each TLD's own RDAP registry server, found through the IANA bootstrap
file (data.iana.org/rdap/dns.json). No API key, no third-party packages. A name
that already contains a dot is checked as a full domain and the --tlds list is
not applied to it.

Why not the rdap.org redirector: it rate-limits hard (a 429 with a 4 second
Retry-After after a handful of requests), so more workers made a run slower, and
it answers 404 for a TLD that has no RDAP service at all, which reads as
AVAILABLE for a domain that is registered. Going to the registry avoids both.

Lookups run in a thread pool (--workers, default 8, at most 16) with at most
four in flight per registry host, because each registry throttles on its own:
Verisign (.com, .net) takes parallel load, while the Google registry (.app,
.dev) refuses faster than about two requests a second. A 429 or 5xx answer
slows every worker aimed at that host (Retry-After honored, capped) and is
retried before the domain is given up as UNKNOWN. Output stays in request
order whatever the completion order.

Status mapping:
    HTTP 404 from the registry -> AVAILABLE (registry holds no record)
    HTTP 200 -> TAKEN
    anything else (timeout, 429 after retries, network failure) -> UNKNOWN
    TLD absent from the bootstrap (no RDAP service) -> UNKNOWN, with the
        reason printed beside it

UNKNOWN never means available. Confirm anything surprising at a registrar
before buying.
"""

import argparse
import concurrent.futures
import http.client
import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
USER_AGENT = "domain-checker/4.0"
DEFAULT_TLDS = ".com,.app,.io,.co"
TIMEOUT = 10
DEFAULT_WORKERS = 8
MAX_WORKERS = 16
PER_HOST = 4
MAX_ATTEMPTS = 4
BACKOFF = 1.0
MAX_RETRY_AFTER = 10.0
THROTTLED_SPACING = 0.5


def parse_tlds(raw: str) -> list:
    """Split a comma-separated TLD string, tolerating a missing leading dot."""
    tlds = []
    for item in raw.split(","):
        item = item.strip().lower()
        if item:
            tlds.append(item if item.startswith(".") else "." + item)
    return tlds


def build_domains(names: list, tlds: list) -> list:
    """Expand names against TLDs. Names that already carry a dot pass through."""
    domains = []
    for name in names:
        name = name.strip().lower()
        if "." in name:
            domains.append(name)
        else:
            domains.extend(name + tld for tld in tlds)
    return domains


def retry_delay(err: urllib.error.HTTPError, attempt: int) -> float:
    """Seconds to wait after a retryable HTTP answer: Retry-After, else backoff."""
    raw = err.headers.get("Retry-After") if err.headers else None
    try:
        wait = float(raw)
    except (TypeError, ValueError):
        wait = BACKOFF * 2 ** attempt
    return min(wait, MAX_RETRY_AFTER)


def load_servers():
    """Map each TLD to its RDAP base URL, or None when the bootstrap is unreachable.

    A TLD missing from the map has no RDAP service, which is a different fact
    from the bootstrap being down, so the two must not both come back as {}.
    """
    request = urllib.request.Request(
        BOOTSTRAP_URL, headers={"User-Agent": USER_AGENT}
    )
    services = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                services = json.load(response)["services"]
            break
        except (urllib.error.URLError, OSError, http.client.HTTPException,
                ValueError, KeyError):
            if attempt + 1 < MAX_ATTEMPTS:
                time.sleep(BACKOFF * 2 ** attempt)
    if services is None:
        return None
    servers = {}
    for tlds, urls in services:
        secure = [url for url in urls if url.startswith("https://")]
        if secure:
            for tld in tlds:
                servers[tld.lower()] = secure[0]
    return servers


def rdap_url(domain: str, servers: dict):
    """The registry lookup URL for a domain, or None when its TLD has no RDAP."""
    base = servers.get(domain.rsplit(".", 1)[-1])
    return base.rstrip("/") + "/domain/" + domain if base else None


class HostGate:
    """Concurrency cap and shared pacing for one registry host.

    A refusal from the host slows every worker aimed at it, not only the one
    that was refused: spacing rises to THROTTLED_SPACING for the rest of the run
    and the next slot moves past the wait the host asked for.
    """

    def __init__(self, limit: int):
        self.slots = threading.BoundedSemaphore(limit)
        self._lock = threading.Lock()
        self._next = 0.0
        self._spacing = 0.0

    def pace(self):
        """Block until this request's turn."""
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self._spacing
        if start > now:
            time.sleep(start - now)

    def throttled(self, delay: float):
        """Record that the host refused: slow all workers, push the next slot."""
        with self._lock:
            self._spacing = max(self._spacing, THROTTLED_SPACING)
            self._next = max(self._next, time.monotonic() + delay)


class HostGates:
    """One HostGate per registry host."""

    def __init__(self, limit: int):
        self._limit = limit
        self._gates = {}
        self._guard = threading.Lock()

    def get(self, url: str) -> HostGate:
        host = urllib.parse.urlsplit(url).netloc
        with self._guard:
            if host not in self._gates:
                self._gates[host] = HostGate(self._limit)
            return self._gates[host]


def query(url: str, gate: HostGate) -> str:
    """Return AVAILABLE, TAKEN, or UNKNOWN for one registry lookup URL."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/rdap+json", "User-Agent": USER_AGENT},
    )
    for attempt in range(MAX_ATTEMPTS):
        try:
            with gate.slots:
                gate.pace()
                with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                    return "TAKEN" if response.getcode() == 200 else "UNKNOWN"
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return "AVAILABLE"
            if err.code != 429 and err.code < 500:
                return "UNKNOWN"
            gate.throttled(retry_delay(err, attempt))
        except (urllib.error.URLError, OSError, http.client.HTTPException):
            if attempt + 1 < MAX_ATTEMPTS:
                time.sleep(BACKOFF * 2 ** attempt)
    return "UNKNOWN"


def check_domain(domain: str, servers, gates: HostGates):
    """Return (status, note) for one fully qualified domain."""
    if servers is None:
        return "UNKNOWN", "IANA RDAP bootstrap unreachable"
    url = rdap_url(domain, servers)
    if url is None:
        return "UNKNOWN", "no RDAP service for ." + domain.rsplit(".", 1)[-1]
    return query(url, gates.get(url)), ""


def check_all(domains: list, workers: int, servers):
    """Yield (domain, status, note) in request order, `workers` at a time."""
    gates = HostGates(PER_HOST)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, min(workers, len(domains)))
    ) as pool:
        results = pool.map(
            lambda domain: check_domain(domain, servers, gates), domains
        )
        for domain, (status, note) in zip(domains, results):
            yield domain, status, note


def main():
    parser = argparse.ArgumentParser(
        description="Check domain availability via RDAP (no API key needed)."
    )
    parser.add_argument(
        "names",
        nargs="+",
        help="brand names, or full domains if they contain a dot",
    )
    parser.add_argument(
        "--tlds",
        default=DEFAULT_TLDS,
        help="comma-separated TLDs to check (default: %(default)s)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="parallel lookups, 1 to %d (default: %%(default)s)" % MAX_WORKERS,
    )
    args = parser.parse_args()

    tlds = parse_tlds(args.tlds)
    if not tlds:
        parser.error("--tlds needs at least one TLD")
    if not 1 <= args.workers <= MAX_WORKERS:
        parser.error("--workers must be between 1 and %d" % MAX_WORKERS)

    domains = build_domains(args.names, tlds)
    servers = load_servers()
    counts = {"AVAILABLE": 0, "TAKEN": 0, "UNKNOWN": 0}
    unserved = set()

    for domain, status, note in check_all(domains, args.workers, servers):
        counts[status] += 1
        if note.startswith("no RDAP"):
            unserved.add("." + domain.rsplit(".", 1)[-1])
        print("{}  {}{}".format(domain, status, "  ({})".format(note) if note else ""),
              flush=True)

    print()
    print("{} checked: {} available, {} taken, {} unknown".format(
        len(domains), counts["AVAILABLE"], counts["TAKEN"], counts["UNKNOWN"]
    ))
    if unserved:
        print("No RDAP service for {}: this script cannot read their registries, "
              "so verify those at a registrar.".format(", ".join(sorted(unserved))))
    if counts["UNKNOWN"]:
        print("UNKNOWN means the lookup failed, not that the domain is free. "
              "Retry or verify at a registrar.")

    sys.exit(2 if counts["UNKNOWN"] == len(domains) else 0)


if __name__ == "__main__":
    main()
