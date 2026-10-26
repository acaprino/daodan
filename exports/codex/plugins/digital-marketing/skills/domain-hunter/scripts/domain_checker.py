#!/usr/bin/env python3
"""
Domain availability checker for the brand naming workflow.

Usage:
    python domain_checker.py name1 name2 name3
    python domain_checker.py acme --tlds .com,.io
    python domain_checker.py name1 name2 --workers 12

Queries each TLD's own RDAP registry server, found through the IANA bootstrap
file (data.iana.org/rdap/dns.json). No API key; RDAP and WHOIS use the standard
library. A name that already contains a dot is checked as a full domain and the
--tlds list is not applied to it.

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
    TLD absent from the bootstrap (no RDAP service) -> the registry's own whois
        (port 43) when WHOIS_TLDS knows it, then the headless registrar page
        when whois is unavailable or unreadable; provenance is printed beside
        the answer, and an unresolved lookup stays UNKNOWN

The whois fallback exists because .it, .eu and .io publish no RDAP. Each reply
is read by a pattern checked against a taken and a free name, and a reply that
matches neither is UNKNOWN. A TLD with no entry in WHOIS_TLDS (.co has no
reachable whois host) proceeds directly to the registrar step.

For a TLD absent from the bootstrap, when whois gives no answer, the domain is
read from Gandi's search page with optional Patchright in headless mode: one
throwaway browser, no visible window, no profile of the user's own. The page
is trusted only when its verdict names the exact domain asked about, because
for a TLD Gandi does not sell it silently searches a different name
(example.gov becomes examplegov.com) and reports THAT as available. Without
Patchright, or when the page does not load (Gandi sits behind a bot check at
times), the domain stays UNKNOWN with the reason shown. Install: pip install
patchright && patchright install chromium. --no-registrar skips only the browser
step; registry WHOIS still runs.

UNKNOWN never means available. Confirm anything surprising at a registrar
before buying.
"""

import argparse
import concurrent.futures
import http.client
import json
import re
import socket
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
NO_RDAP = "no RDAP service for ."
REGISTRAR_URL = "https://shop.gandi.net/en/domain/suggest?search="
REGISTRAR_NAME = "Gandi page, headless Patchright"
REGISTRAR_TIMEOUT_MS = 20000
REGISTRAR_ATTEMPTS = 2
PATCHRIGHT_HINT = "pip install patchright && patchright install chromium"
VERDICT_WAIT = "() => /This domain is (not )?available/i.test(document.body.innerText)"
WHOIS_PORT = 43
WHOIS_SPACING = 1.0

# tld -> (whois host, pattern of a free name, pattern of a registered name).
# Checked 2026-10-13 against a registered name (google) and a random free one.
WHOIS_TLDS = {
    "it": ("whois.nic.it", r"^Status:\s+AVAILABLE", r"^Domain:\s"),
    "eu": ("whois.eu", r"^Status:\s+AVAILABLE", r"^Domain:\s"),
    "io": ("whois.nic.io", r"^Domain not found", r"^Domain Name:\s"),
}


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

    def set_spacing(self, spacing: float):
        """Fix a minimum gap between requests, for hosts that publish no RDAP."""
        with self._lock:
            self._spacing = max(self._spacing, spacing)

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


def classify_whois(text: str, free: str, taken: str) -> str:
    """AVAILABLE, TAKEN or UNKNOWN for one whois reply. The free pattern wins
    because a free .eu name still echoes a Domain: line."""
    if re.search(free, text, re.MULTILINE | re.IGNORECASE):
        return "AVAILABLE"
    if re.search(taken, text, re.MULTILINE | re.IGNORECASE):
        return "TAKEN"
    return "UNKNOWN"


def query_whois(domain: str, entry: tuple, gate: HostGate) -> str:
    """Ask a registry whois server on port 43; UNKNOWN when it cannot be read."""
    host, free, taken = entry
    for attempt in range(MAX_ATTEMPTS):
        try:
            with gate.slots:
                gate.pace()
                with socket.create_connection((host, WHOIS_PORT), timeout=TIMEOUT) as sock:
                    sock.sendall((domain + "\r\n").encode("ascii"))
                    chunks = []
                    while True:
                        data = sock.recv(4096)
                        if not data:
                            break
                        chunks.append(data)
            status = classify_whois(b"".join(chunks).decode("utf-8", "replace"), free, taken)
            if status != "UNKNOWN":
                return status
        except (OSError, UnicodeError):
            pass
        if attempt + 1 < MAX_ATTEMPTS:
            gate.throttled(BACKOFF * 2 ** attempt)
    return "UNKNOWN"


def check_domain(domain: str, servers, gates: HostGates):
    """Return (status, note) for one fully qualified domain."""
    tld = domain.rsplit(".", 1)[-1]
    if servers is None:
        return "UNKNOWN", "IANA RDAP bootstrap unreachable"
    url = rdap_url(domain, servers)
    if url is None:
        entry = WHOIS_TLDS.get(tld)
        if entry is None:
            return "UNKNOWN", NO_RDAP + tld
        gate = gates.get("whois://" + entry[0])
        gate.set_spacing(WHOIS_SPACING)
        status = query_whois(domain, entry, gate)
        if status == "UNKNOWN":
            return status, NO_RDAP + tld + "; " + entry[0] + " lookup failed"
        return status, "via " + entry[0]
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


def read_registrar_answer(text: str, domain: str):
    """Return (status, note) from the visible text of a Gandi search page.

    The verdict counts only when the domain asked about follows it directly. A
    page that answers for another name (a TLD Gandi does not sell is searched as
    a .com instead) or says nothing readable is UNKNOWN, never AVAILABLE.
    """
    name = re.escape(domain)
    available = re.search(
        r"This domain is available!\s+" + name + r"(?![\w.-])(.{0,40})", text
    )
    if available:
        premium = ", premium price" if "Premium" in available.group(1) else ""
        return "AVAILABLE", REGISTRAR_NAME + premium
    if re.search(
        r"This domain is not available!\s+(?:See WHOIS\s+)?" + name + r"(?![\w.-])",
        text,
    ):
        return "TAKEN", REGISTRAR_NAME
    return "UNKNOWN", "registrar page gave no verdict for this exact domain"


class RegistrarBrowser:
    """A lazily started, always headless Patchright session reading Gandi.

    Nothing starts until the first domain needs it, so a run that RDAP fully
    covers never imports Patchright. The browser is a fresh non-persistent
    context: no user profile is opened and no window is shown. Used from the
    main thread only, as the sync API requires.
    """

    def __init__(self):
        self._started = False
        self._error = ""
        self._playwright = None
        self._browser = None
        self._context = None

    def _start(self) -> str:
        """Launch the browser; return an error message, or "" when ready."""
        try:
            from patchright.sync_api import sync_playwright
        except ImportError:
            return "patchright not installed (" + PATCHRIGHT_HINT + ")"
        try:
            self._playwright = sync_playwright().start()
        except Exception as exc:
            return "patchright did not start ({})".format(type(exc).__name__)
        for options in ({}, {"channel": "chrome"}):
            try:
                self._browser = self._playwright.chromium.launch(
                    headless=True, **options
                )
                self._context = self._browser.new_context()
                return ""
            except Exception:
                continue
        return "headless browser did not start (" + PATCHRIGHT_HINT + ")"

    def check(self, domain: str):
        """Return (status, note) for one domain."""
        if not self._started:
            self._started = True
            self._error = self._start()
        if self._error:
            return "UNKNOWN", self._error
        reason = ""
        for _ in range(REGISTRAR_ATTEMPTS):
            page = self._context.new_page()
            try:
                page.goto(
                    REGISTRAR_URL + urllib.parse.quote(domain),
                    wait_until="domcontentloaded",
                    timeout=REGISTRAR_TIMEOUT_MS,
                )
                page.wait_for_function(VERDICT_WAIT, timeout=REGISTRAR_TIMEOUT_MS)
                return read_registrar_answer(
                    " ".join(page.inner_text("body").split()), domain
                )
            except Exception as exc:
                reason = "registrar page did not load ({}), possibly a bot check".format(
                    type(exc).__name__
                )
            finally:
                page.close()
        return "UNKNOWN", reason

    def close(self):
        for handle, stop in ((self._browser, "close"), (self._playwright, "stop")):
            if handle is not None:
                try:
                    getattr(handle, stop)()
                except Exception:
                    pass


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
    parser.add_argument(
        "--no-registrar",
        action="store_true",
        help="skip the headless registrar step; RDAP and registry WHOIS still run",
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
    registrar = None if args.no_registrar else RegistrarBrowser()

    try:
        for domain, status, note in check_all(domains, args.workers, servers):
            if note.startswith(NO_RDAP):
                if registrar:
                    registry_note = note
                    status, note = registrar.check(domain)
                    if status == "UNKNOWN":
                        note = registry_note + "; " + note
                if status == "UNKNOWN":
                    tld = "." + domain.rsplit(".", 1)[-1]
                    unserved.add(tld)
            counts[status] += 1
            print("{}  {}{}".format(domain, status, "  ({})".format(note) if note else ""),
                  flush=True)
    finally:
        if registrar:
            registrar.close()

    print()
    print("{} checked: {} available, {} taken, {} unknown".format(
        len(domains), counts["AVAILABLE"], counts["TAKEN"], counts["UNKNOWN"]
    ))
    if unserved:
        print("No RDAP service for {} and no registrar answer: verify those by hand "
              "at a registrar's search page.".format(", ".join(sorted(unserved))))
    if counts["UNKNOWN"]:
        print("UNKNOWN means the lookup failed, not that the domain is free. "
              "Retry or verify at a registrar.")

    sys.exit(2 if counts["UNKNOWN"] == len(domains) else 0)


if __name__ == "__main__":
    main()
