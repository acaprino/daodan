"""Tests for the digital-marketing plugin's RDAP domain checker script.

Stdlib only. The network is never touched: `urllib.request.urlopen` and
`time.sleep` are patched, and the registry map is passed in by the test.
"""
import contextlib
import email.message
import importlib.util
import io
import json
import sys
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT / "plugins" / "digital-marketing" / "skills" / "domain-hunter"
    / "scripts" / "domain_checker.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("domain_checker", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dc = load_module()

SERVERS = {
    "com": "https://rdap.verisign.com/com/v1/",
    "app": "https://pubapi.registry.google/rdap/",
}


class FakeResponse:
    def __init__(self, code=200, body=b"{}"):
        self._code = code
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def getcode(self):
        return self._code

    def read(self, *args):
        return self._body


def http_error(code, retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://example.test", code, "x", headers, None)


def scripted(*outcomes):
    """A urlopen stand-in that plays each outcome in turn: response or exception."""
    queue = list(outcomes)

    def fake(request, timeout=None):
        outcome = queue.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return fake


def gate():
    return dc.HostGate(dc.PER_HOST)


class ExpansionTests(unittest.TestCase):
    def test_names_expand_against_tlds_and_dotted_names_pass_through(self):
        domains = dc.build_domains(["Acme", "other.ai"], [".com", ".app"])
        self.assertEqual(domains, ["acme.com", "acme.app", "other.ai"])

    def test_tlds_tolerate_a_missing_dot_and_blanks(self):
        self.assertEqual(dc.parse_tlds("com, .io,,"), [".com", ".io"])


class RegistryResolutionTests(unittest.TestCase):
    def test_lookup_goes_to_the_registry_for_the_tld(self):
        self.assertEqual(
            dc.rdap_url("acme.com", SERVERS),
            "https://rdap.verisign.com/com/v1/domain/acme.com",
        )

    def test_tld_without_rdap_service_has_no_url(self):
        self.assertIsNone(dc.rdap_url("google.io", SERVERS))

    def test_no_rdap_tld_is_unknown_and_never_queried(self):
        # Regression: rdap.org answers 404 for a TLD with no RDAP service, which
        # read as AVAILABLE for registered domains like google.io.
        # .co has no RDAP and no reachable whois host, so it must stay UNKNOWN.
        with mock.patch.object(dc, "query", side_effect=AssertionError("queried")), \
                mock.patch.object(dc, "query_whois", side_effect=AssertionError("whois")):
            status, note = dc.check_domain("google.co", SERVERS, dc.HostGates(2))
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("no RDAP service for .co", note)

    def test_no_rdap_tld_with_a_registry_whois_is_read_there(self):
        for domain, host in (("acme.it", "whois.nic.it"), ("acme.eu", "whois.eu"),
                             ("acme.io", "whois.nic.io")):
            with mock.patch.object(dc, "query", side_effect=AssertionError("queried")), \
                    mock.patch.object(dc, "query_whois", return_value="TAKEN") as who:
                status, note = dc.check_domain(domain, SERVERS, dc.HostGates(2))
            self.assertEqual((status, note), ("TAKEN", "via " + host))
            self.assertEqual(who.call_args[0][1][0], host)

    def test_unreachable_bootstrap_is_unknown_not_available(self):
        status, note = dc.check_domain("acme.com", None, dc.HostGates(2))
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("bootstrap unreachable", note)


class WhoisTests(unittest.TestCase):
    """Replies copied from the registries on 2026-10-13."""

    def classify(self, tld, text):
        _, free, taken = dc.WHOIS_TLDS[tld]
        return dc.classify_whois(text, free, taken)

    def test_it_free_and_taken(self):
        self.assertEqual(self.classify("it", "Domain:             x.it\nStatus:             AVAILABLE\n"), "AVAILABLE")
        self.assertEqual(self.classify("it", "*****\n\nDomain:             google.it\nStatus:             ok\n"), "TAKEN")

    def test_eu_free_wins_over_the_echoed_domain_line(self):
        self.assertEqual(self.classify("eu", "Domain: x.eu\nScript: LATIN\nStatus: AVAILABLE\n"), "AVAILABLE")
        self.assertEqual(self.classify("eu", "Domain: google.eu\nScript: LATIN\nRegistrant:\n NOT DISCLOSED!\n"), "TAKEN")

    def test_io_free_and_taken(self):
        self.assertEqual(self.classify("io", "Domain not found.\n>>> Last update"), "AVAILABLE")
        self.assertEqual(self.classify("io", "Domain Name: google.io\nRegistry Domain ID: REDACTED\n"), "TAKEN")

    def test_unreadable_reply_is_unknown_never_available(self):
        self.assertEqual(self.classify("it", "% rate limit exceeded\n"), "UNKNOWN")
        self.assertEqual(self.classify("io", ""), "UNKNOWN")

    def test_network_failure_is_unknown(self):
        gate = dc.HostGate(1)
        with mock.patch("socket.create_connection", side_effect=OSError("down")), \
                mock.patch.object(dc.time, "sleep"):
            self.assertEqual(dc.query_whois("acme.it", dc.WHOIS_TLDS["it"], gate), "UNKNOWN")


class BootstrapTests(unittest.TestCase):
    def test_servers_map_prefers_https(self):
        payload = json.dumps({"services": [
            [["com", "NET"], ["http://plain.example/", "https://secure.example/"]],
            [["xx"], ["http://only-plain.example/"]],
        ]}).encode()
        with mock.patch("urllib.request.urlopen", scripted(FakeResponse(200, payload))):
            servers = dc.load_servers()
        self.assertEqual(servers, {
            "com": "https://secure.example/",
            "net": "https://secure.example/",
        })

    def test_failure_is_none_so_it_differs_from_a_tld_without_rdap(self):
        failures = [urllib.error.URLError("down")] * dc.MAX_ATTEMPTS
        with mock.patch("urllib.request.urlopen", scripted(*failures)), \
                mock.patch("time.sleep"):
            self.assertIsNone(dc.load_servers())


class QueryTests(unittest.TestCase):
    URL = "https://rdap.verisign.com/com/v1/domain/acme.com"

    def run_query(self, *outcomes):
        sleeps = []
        with mock.patch("urllib.request.urlopen", scripted(*outcomes)), \
                mock.patch("time.sleep", side_effect=sleeps.append):
            return dc.query(self.URL, gate()), sleeps

    def test_200_is_taken(self):
        self.assertEqual(self.run_query(FakeResponse(200))[0], "TAKEN")

    def test_404_is_available(self):
        self.assertEqual(self.run_query(http_error(404))[0], "AVAILABLE")

    def test_other_client_error_is_unknown_without_retry(self):
        outcomes = [http_error(403)]
        status, _ = self.run_query(*outcomes)
        self.assertEqual(status, "UNKNOWN")

    def test_429_is_retried_and_retry_after_is_honored(self):
        status, sleeps = self.run_query(http_error(429, retry_after=2), FakeResponse(200))
        self.assertEqual(status, "TAKEN")
        self.assertEqual(len(sleeps), 1)
        self.assertTrue(1.5 < sleeps[0] <= 2.0, sleeps)

    def test_retry_after_is_capped(self):
        _, sleeps = self.run_query(http_error(429, retry_after=3600), FakeResponse(404))
        self.assertLessEqual(max(sleeps), dc.MAX_RETRY_AFTER)

    def test_exhausted_retries_are_unknown_never_available(self):
        status, _ = self.run_query(*[http_error(429)] * dc.MAX_ATTEMPTS)
        self.assertEqual(status, "UNKNOWN")

    def test_network_failure_is_unknown(self):
        status, _ = self.run_query(*[urllib.error.URLError("down")] * dc.MAX_ATTEMPTS)
        self.assertEqual(status, "UNKNOWN")

    def test_a_refusal_slows_the_whole_host(self):
        shared = gate()
        with mock.patch("urllib.request.urlopen",
                        scripted(http_error(429, retry_after=1), FakeResponse(200))), \
                mock.patch("time.sleep"):
            dc.query(self.URL, shared)
        self.assertGreaterEqual(shared._spacing, dc.THROTTLED_SPACING)


class ConcurrencyTests(unittest.TestCase):
    def test_results_keep_request_order(self):
        domains = ["a.com", "b.com", "c.com", "d.com"]

        def slow_first(domain, servers, gates):
            time.sleep(0.15 if domain == "a.com" else 0.01)
            return "TAKEN", ""

        with mock.patch.object(dc, "check_domain", side_effect=slow_first):
            got = [d for d, _, _ in dc.check_all(domains, 4, SERVERS)]
        self.assertEqual(got, domains)

    def test_in_flight_lookups_per_host_are_capped(self):
        lock = threading.Lock()
        state = {"now": 0, "peak": 0}

        def fake(request, timeout=None):
            with lock:
                state["now"] += 1
                state["peak"] = max(state["peak"], state["now"])
            time.sleep(0.03)
            with lock:
                state["now"] -= 1
            return FakeResponse(200)

        domains = ["n{}.com".format(i) for i in range(16)]
        with mock.patch("urllib.request.urlopen", fake):
            results = list(dc.check_all(domains, dc.MAX_WORKERS, SERVERS))
        self.assertEqual({status for _, status, _ in results}, {"TAKEN"})
        self.assertLessEqual(state["peak"], dc.PER_HOST)
        self.assertGreater(state["peak"], 1)

    def test_different_registries_run_side_by_side(self):
        gates = dc.HostGates(1)
        self.assertIsNot(
            gates.get("https://rdap.verisign.com/com/v1/domain/a.com"),
            gates.get("https://pubapi.registry.google/rdap/domain/a.app"),
        )


class CliTests(unittest.TestCase):
    def run_cli(self, argv, servers):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["domain_checker.py"] + argv), \
                mock.patch.object(dc, "load_servers", return_value=servers), \
                contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                dc.main()
                code = 0
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue()

    def test_all_unknown_exits_2_and_names_the_tlds_without_rdap(self):
        code, out = self.run_cli(["acme", "--tlds", ".xx,.co"], {})
        self.assertEqual(code, 2)
        self.assertIn("acme.xx  UNKNOWN  (no RDAP service for .xx)", out)
        self.assertIn("No RDAP service for .co, .xx", out)

    def test_mixed_run_exits_0_and_reports_each_status(self):
        outcomes = [FakeResponse(200), http_error(404)]
        with mock.patch("urllib.request.urlopen", scripted(*outcomes)):
            code, out = self.run_cli(["acme", "--tlds", ".com,.app,.co", "--workers", "1"], SERVERS)
        self.assertEqual(code, 0)
        self.assertIn("acme.com  TAKEN", out)
        self.assertIn("acme.app  AVAILABLE", out)
        self.assertIn("acme.co  UNKNOWN", out)
        self.assertIn("3 checked: 1 available, 1 taken, 1 unknown", out)

    def test_workers_out_of_range_is_a_usage_error(self):
        for value in ("0", str(dc.MAX_WORKERS + 1)):
            code, _ = self.run_cli(["acme", "--workers", value], SERVERS)
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
