"""Tests for the digital-marketing plugin's domain checker script.

Stdlib only. The network is never touched: `urllib.request.urlopen` and
`time.sleep` are patched, the registry map is passed in by the test, and the
headless registrar step runs against a fake `patchright` module or a fake
registrar class, so no browser is ever started.
"""
import contextlib
import email.message
import importlib.util
import io
import json
import sys
import threading
import time
import types
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
        with mock.patch.object(dc, "query", side_effect=AssertionError("queried")):
            status, note = dc.check_domain("google.io", SERVERS, dc.HostGates(2))
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("no RDAP service for .io", note)

    def test_unreachable_bootstrap_is_unknown_not_available(self):
        status, note = dc.check_domain("acme.com", None, dc.HostGates(2))
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("bootstrap unreachable", note)


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
        code, out = self.run_cli(["acme", "--tlds", ".io,.co", "--no-registrar"], {})
        self.assertEqual(code, 2)
        self.assertIn("acme.io  UNKNOWN  (no RDAP service for .io)", out)
        self.assertIn("No RDAP service for .co, .io", out)

    def test_mixed_run_exits_0_and_reports_each_status(self):
        outcomes = [FakeResponse(200), http_error(404)]
        with mock.patch("urllib.request.urlopen", scripted(*outcomes)):
            code, out = self.run_cli(
                ["acme", "--tlds", ".com,.app,.io", "--workers", "1", "--no-registrar"], SERVERS
            )
        self.assertEqual(code, 0)
        self.assertIn("acme.com  TAKEN", out)
        self.assertIn("acme.app  AVAILABLE", out)
        self.assertIn("acme.io  UNKNOWN", out)
        self.assertIn("3 checked: 1 available, 1 taken, 1 unknown", out)

    def test_workers_out_of_range_is_a_usage_error(self):
        for value in ("0", str(dc.MAX_WORKERS + 1)):
            code, _ = self.run_cli(["acme", "--workers", value], SERVERS)
            self.assertEqual(code, 2)


class RegistrarAnswerTests(unittest.TestCase):
    def test_exact_domain_available(self):
        text = "Search Good news! This domain is available! acme.io 46% OFF 1 year at 54"
        self.assertEqual(dc.read_registrar_answer(text, "acme.io")[0], "AVAILABLE")

    def test_exact_domain_taken(self):
        text = "No! This domain is not available! See WHOIS acme.io You should like as well"
        self.assertEqual(dc.read_registrar_answer(text, "acme.io")[0], "TAKEN")

    def test_premium_price_is_noted(self):
        text = "Good news! This domain is available! acme.io Premium 1 year at 2,917"
        status, note = dc.read_registrar_answer(text, "acme.io")
        self.assertEqual(status, "AVAILABLE")
        self.assertIn("premium price", note)

    def test_verdict_about_a_rewritten_domain_is_unknown(self):
        # Gandi does not sell .gov: it searches examplegov.com and calls THAT available.
        text = "Good news! This domain is available! examplegov.com 1 year at 11.00"
        self.assertEqual(dc.read_registrar_answer(text, "example.gov")[0], "UNKNOWN")

    def test_longer_name_sharing_the_prefix_is_not_a_match(self):
        text = "Good news! This domain is available! acme.iome 1 year at 11.00"
        self.assertEqual(dc.read_registrar_answer(text, "acme.io")[0], "UNKNOWN")

    def test_bot_check_page_is_unknown(self):
        self.assertEqual(
            dc.read_registrar_answer("Just a moment... security verification", "acme.io")[0],
            "UNKNOWN",
        )


class FakePage:
    def __init__(self, text, fail=False):
        self.text, self.fail, self.closed = text, fail, False

    def goto(self, url, **kwargs):
        self.url = url
        if self.fail:
            raise TimeoutError("navigation")

    def wait_for_function(self, script, **kwargs):
        pass

    def inner_text(self, selector):
        return self.text

    def close(self):
        self.closed = True


def fake_patchright(launches, text="No! This domain is not available! See WHOIS acme.io",
                    fail_launch_first=False, fail_page=False):
    """A stand-in for `patchright.sync_api` that records every launch call."""
    pages = []

    class Context:
        def new_page(self):
            page = FakePage(text, fail=fail_page)
            pages.append(page)
            return page

    class Browser:
        def new_context(self):
            return Context()

        def close(self):
            launches.append("browser closed")

    class Chromium:
        def launch(self, **kwargs):
            launches.append(kwargs)
            if fail_launch_first and len(launches) == 1:
                raise RuntimeError("Executable doesn't exist")
            return Browser()

    class Playwright:
        chromium = Chromium()

        def stop(self):
            launches.append("playwright stopped")

    module = types.ModuleType("patchright.sync_api")
    module.sync_playwright = lambda: types.SimpleNamespace(start=lambda: Playwright())
    return {"patchright": types.ModuleType("patchright"), "patchright.sync_api": module}, pages


class RegistrarBrowserTests(unittest.TestCase):
    def test_missing_patchright_is_unknown_with_install_hint(self):
        with mock.patch.dict(sys.modules, {"patchright": None, "patchright.sync_api": None}):
            status, note = dc.RegistrarBrowser().check("acme.io")
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("pip install patchright", note)

    def test_every_launch_is_headless_including_the_chrome_fallback(self):
        launches = []
        modules, _ = fake_patchright(launches, fail_launch_first=True)
        with mock.patch.dict(sys.modules, modules):
            registrar = dc.RegistrarBrowser()
            status, _ = registrar.check("acme.io")
            registrar.close()
        attempts = [entry for entry in launches if isinstance(entry, dict)]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[1].get("channel"), "chrome")
        for options in attempts:
            self.assertIs(options.get("headless"), True)
            self.assertNotIn("user_data_dir", options)
        self.assertEqual(status, "TAKEN")
        self.assertIn("browser closed", launches)
        self.assertIn("playwright stopped", launches)

    def test_browser_starts_once_for_many_domains(self):
        launches = []
        modules, pages = fake_patchright(
            launches, text="Good news! This domain is available! acme.io"
        )
        with mock.patch.dict(sys.modules, modules):
            registrar = dc.RegistrarBrowser()
            registrar.check("acme.io")
            registrar.check("acme.io")
        self.assertEqual(len([e for e in launches if isinstance(e, dict)]), 1)
        self.assertEqual(len(pages), 2)
        self.assertTrue(all(page.closed for page in pages))

    def test_page_that_never_loads_is_unknown_after_a_retry(self):
        launches = []
        modules, pages = fake_patchright(launches, fail_page=True)
        with mock.patch.dict(sys.modules, modules):
            status, note = dc.RegistrarBrowser().check("acme.io")
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("did not load", note)
        self.assertEqual(len(pages), dc.REGISTRAR_ATTEMPTS)
        self.assertTrue(all(page.closed for page in pages))

    def test_browser_start_failure_is_unknown_not_available(self):
        modules, _ = fake_patchright([])
        modules["patchright.sync_api"].sync_playwright = mock.Mock(
            side_effect=OSError("no driver")
        )
        with mock.patch.dict(sys.modules, modules):
            status, note = dc.RegistrarBrowser().check("acme.io")
        self.assertEqual(status, "UNKNOWN")
        self.assertIn("did not start", note)


class RegistrarCliTests(unittest.TestCase):
    """The CLI wiring of the registrar step, with a fake registrar class."""

    run_cli = CliTests.run_cli

    def run_with_registrar(self, argv, servers, answers):
        made = []

        class FakeRegistrar:
            def __init__(self):
                self.closed = False
                made.append(self)

            def check(self, domain):
                return answers[domain]

            def close(self):
                self.closed = True

        with mock.patch.object(dc, "RegistrarBrowser", FakeRegistrar):
            code, out = self.run_cli(argv, servers)
        return code, out, made

    def test_no_rdap_domains_take_the_registrar_verdict_in_request_order(self):
        answers = {"acme.io": ("AVAILABLE", dc.REGISTRAR_NAME)}
        with mock.patch("urllib.request.urlopen", scripted(FakeResponse(200))):
            code, out, made = self.run_with_registrar(
                ["acme", "--tlds", ".com,.io", "--workers", "1"], SERVERS, answers
            )
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "acme.com  TAKEN")
        self.assertEqual(lines[1], "acme.io  AVAILABLE  (" + dc.REGISTRAR_NAME + ")")
        self.assertIn("2 checked: 1 available, 1 taken, 0 unknown", out)
        self.assertNotIn("No RDAP service", out)
        self.assertTrue(made[0].closed)

    def test_registrar_unknown_keeps_the_no_rdap_reason_and_exits_2(self):
        answers = {"acme.io": ("UNKNOWN", "patchright not installed (pip install patchright)")}
        code, out, made = self.run_with_registrar(["acme", "--tlds", ".io"], {}, answers)
        self.assertEqual(code, 2)
        self.assertIn("acme.io  UNKNOWN  (no RDAP service for .io; patchright not installed", out)
        self.assertIn("No RDAP service for .io and no registrar answer", out)
        self.assertTrue(made[0].closed)

    def test_registry_covered_run_never_starts_a_browser(self):
        with mock.patch.object(dc.RegistrarBrowser, "_start", side_effect=AssertionError("started")), \
                mock.patch("urllib.request.urlopen", scripted(FakeResponse(200))):
            code, out = self.run_cli(["acme", "--tlds", ".com"], SERVERS)
        self.assertEqual(code, 0)
        self.assertIn("acme.com  TAKEN", out)

    def test_no_registrar_flag_never_builds_one(self):
        with mock.patch.object(dc, "RegistrarBrowser", side_effect=AssertionError("built")):
            code, out = self.run_cli(["acme", "--tlds", ".io", "--no-registrar"], {})
        self.assertEqual(code, 2)
        self.assertIn("acme.io  UNKNOWN  (no RDAP service for .io)", out)


if __name__ == "__main__":
    unittest.main()
