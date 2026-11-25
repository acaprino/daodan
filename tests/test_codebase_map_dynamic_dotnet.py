"""The .NET observer: its plan from the project files, its container run, what the recorder wrote, read and placed.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_dynamic_dotnet.py

The recorder runs for real where a .NET SDK from 10 on is on the PATH (`RecorderTest`, skipped otherwise): Daodan's
two projects are built, and a small MSTest project this file writes is built, rewritten and tested under them.
Elsewhere the container is the fake Docker-compatible command line of `test_codebase_map_container.py`, playing
what a test scripted for the two bash phases, and the rewriter's table and the recorder's files are written here
as they write them.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import container  # noqa: E402
import dynamic  # noqa: E402
import engine_tools  # noqa: E402
import preparation  # noqa: E402
import resolve_edges  # noqa: E402
from dynamic import dotnet  # noqa: E402
from test_codebase_map_container import FAKE_CLI  # noqa: E402
from test_codebase_map_indexers_jvm import PLAY, digest, log  # noqa: E402

SHOP = {
    "global.json": '{"test": {"runner": "Microsoft.Testing.Platform"}}\n',
    "src/Shop/Shop.csproj": """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup>
</Project>
""",
    "src/Shop/Pricing.cs": """namespace Shop;

public interface IPricing
{
    decimal Price(decimal amount);
}

public class Pricing : IPricing
{
    public virtual decimal Price(decimal amount) => amount * Rate;
    public decimal Rate { get; set; } = 2;
}

public class Discount : Pricing
{
    public override decimal Price(decimal amount) => base.Price(amount) / 2;
}

public static class Orders
{
    public static decimal Total(IPricing pricing, decimal[] amounts)
    {
        decimal sum = 0;
        foreach (var amount in amounts) sum += pricing.Price(amount);
        return sum;
    }

    public static decimal[] Doubled(decimal[] amounts) => amounts.Select(amount => Twice(amount)).ToArray();

    public static decimal Twice(decimal amount) => amount * 2;

    public static async Task<decimal> Later(decimal amount)
    {
        await Task.Yield();
        return Twice(amount);
    }

    public static decimal Apply(Func<decimal, decimal> f, decimal amount) => f(amount);
}
""",
    "tests/Shop.Tests/Shop.Tests.csproj": """<Project Sdk="MSTest.Sdk/4.0.2">
  <PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup>
  <ItemGroup><ProjectReference Include="../../src/Shop/Shop.csproj" /></ItemGroup>
</Project>
""",
    "tests/Shop.Tests/PricingTests.cs": """using Microsoft.VisualStudio.TestTools.UnitTesting;
using Shop;

namespace Shop.Tests;

[TestClass]
public class PricingTests
{
    [TestMethod]
    public void Totals()
    {
        IPricing pricing = new Discount();
        Assert.AreEqual(2m, Orders.Total(pricing, new[] { 1m, 1m }));
        Assert.AreEqual(4m, Orders.Doubled(new[] { 2m })[0]);
        Assert.AreEqual(6m, Orders.Apply(x => Orders.Twice(x), 3m));
        Assert.AreEqual(Orders.Twice(1m), Orders.Twice(1m));
    }

    [TestMethod]
    public async Task Later()
    {
        Assert.AreEqual(8m, await Orders.Later(4m));
    }
}
""",
}
SOURCES = sorted(rel for rel in SHOP if rel.endswith(".cs"))
PRICING, TESTS = "src/Shop/Pricing.cs", "tests/Shop.Tests/PricingTests.cs"


def at(rel: str, line: int, name: str, nth: int = 1) -> tuple[str, int, int, str]:
    """`(file, line from 0, byte column, name)` of the `nth` `name` on a line from 1 of a SHOP file."""
    text, column = SHOP[rel].split("\n")[line - 1], -1
    for _ in range(nth):
        column = text.index(name, column + 1)
    return rel, line - 1, len(text[:column].encode("utf-8")), name


def project(line: int, column: int | None, name: str, kind: str, rel: str = PRICING) -> dict:
    return {"kind": "project", "file": rel, "line": line, "column": column, "name": name, "type": kind}


# ---------------------------------------------------------------------------------------------------------
# What it declares, and its plan

def test_the_observer_declares_itself_for_csharp_with_its_recorder_pinned():
    assert dotnet in dynamic.observers()
    assert (dotnet.NAME, dotnet.VERSION, dotnet.LANGUAGES) == ("dynamic-record-dotnet", "1", ("csharp",))
    url, sha256, name = dotnet.CECIL
    assert url.endswith("/mono.cecil/0.11.6/mono.cecil.0.11.6.nupkg") and len(sha256) == 64
    assert sorted(path.relative_to(dotnet.RECORD).as_posix() for path in dotnet.RECORD.rglob("*") if path.is_file()) \
        == ["nuget.config", "record/Daodan.Record.csproj", "record/Record.cs", "rewrite/Daodan.Rewrite.csproj",
            "rewrite/Rewrite.cs"]


def _plan(files: dict, record: dict | None = None) -> dict:
    return dotnet.plan(record or {}, sorted(files), files.get)


def test_each_project_that_names_a_test_framework_runs_dotnet_test_as_its_global_json_says():
    """MSTest.Sdk, a test package, IsTestProject: `--project` under the global.json that states
    Microsoft.Testing.Platform, the nearest above the project; the path alone under VSTest's."""
    files = {**SHOP, "tests/X/X.csproj": '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup>'
                                        '<PackageReference Include="xunit.v3" /></ItemGroup></Project>',
             "legacy/global.json": '{"sdk": {"version": "8.0.100"}}',
             "legacy/L/L.csproj": "<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>",
             "tools/T/T.csproj": '<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><PackageReference Include="xunitish" />'
                                 "</ItemGroup></Project>"}
    planned = _plan(files, {"toolchains": [{"tool": "dotnet", "version": "10.0.302", "declared_in": "global.json"},
                                           {"tool": "node", "version": "24", "declared_in": ".nvmrc"}]})
    assert planned["runs"] == [
        {"root": "legacy/L", "runner": "dotnet test", "project": "legacy/L/L.csproj",
         "argv": ["dotnet", "test", "L.csproj", "--no-build"]},
        {"root": "tests/Shop.Tests", "runner": "dotnet test", "project": "tests/Shop.Tests/Shop.Tests.csproj",
         "argv": ["dotnet", "test", "--project", "Shop.Tests.csproj", "--no-build"]},
        {"root": "tests/X", "runner": "dotnet test", "project": "tests/X/X.csproj",
         "argv": ["dotnet", "test", "--project", "X.csproj", "--no-build"]}]
    assert planned["gaps"] == [] and planned["sources"] == SOURCES
    assert planned["toolchains"] == [{"tool": "dotnet", "version": "10.0.302", "declared_in": "global.json"}]


def test_without_a_test_project_nothing_runs_and_the_gap_says_why():
    planned = _plan({rel: text for rel, text in SHOP.items() if not rel.startswith("tests/")})
    assert planned["runs"] == [] and [gap["kind"] for gap in planned["gaps"]] == ["no_tests"]


def test_a_test_project_that_starts_its_services_through_aspire_does_not_run_and_the_gap_says_why():
    """eShop's functional tests are Aspire app hosts (`Aspire.AppHost.Sdk`) that start Postgres, Redis and RabbitMQ
    as containers, and a test of an app host with Aspire.Hosting.Testing starts it the same way: the execution has
    no container engine to give them, so they do not run. A test project that only references an app host reads
    its model, and runs."""
    files = {**SHOP,
             "src/AppHost/AppHost.csproj": '<Project Sdk="Aspire.AppHost.Sdk/13.6.0" />',
             "tests/Api.FunctionalTests/Api.FunctionalTests.csproj":
                 '<Project Sdk="Aspire.AppHost.Sdk/13.6.0"><ItemGroup><PackageReference Include="xunit.v3.mtp-v2" />'
                 '<PackageReference Include="Aspire.Hosting.PostgreSQL" /></ItemGroup></Project>',
             "tests/Host.Tests/Host.Tests.csproj":
                 '<Project Sdk="MSTest.Sdk"><ItemGroup><PackageReference Include="Aspire.Hosting.Testing" />'
                 "</ItemGroup></Project>",
             "tests/AppHost.UnitTests/AppHost.UnitTests.csproj":
                 '<Project Sdk="MSTest.Sdk"><ItemGroup><ProjectReference Include="..\\..\\src\\AppHost\\AppHost.csproj" />'
                 "</ItemGroup></Project>"}
    planned = _plan(files)
    assert [run["project"] for run in planned["runs"]] == ["tests/AppHost.UnitTests/AppHost.UnitTests.csproj",
                                                           "tests/Shop.Tests/Shop.Tests.csproj"]
    assert [(gap["kind"], gap["path"]) for gap in planned["gaps"]] == [
        ("tests_need_container_engine", "tests/Api.FunctionalTests/Api.FunctionalTests.csproj"),
        ("tests_need_container_engine", "tests/Host.Tests/Host.Tests.csproj")]
    assert all("Aspire" in gap["detail"] and "container engine" in gap["detail"] for gap in planned["gaps"])
    only = _plan({rel: text for rel, text in files.items() if "Shop.Tests" not in rel and "UnitTests" not in rel})
    assert only["runs"] == [] and [gap["kind"] for gap in only["gaps"]] == ["tests_need_container_engine"] * 2


def test_the_preparation_builds_the_recorder_and_the_tests_and_the_execution_runs_them_recorded():
    runs = _plan(SHOP)["runs"]
    prepare, execute = dotnet.scripts(runs, ["install the sdk"])
    assert prepare.startswith("# daodan prepare\n") and execute.startswith("# daodan execute\n")
    assert "install the sdk" in prepare and "step sdk sdk" in prepare
    assert f"step agent sh -c '{dotnet.agent_commands(dotnet.AGENT)}' || exit 70" in prepare
    assert f"step build-1 build tests/Shop.Tests Shop.Tests.csproj && touch {dotnet.BUILT}/built-1" in prepare
    assert "dotnet test" not in prepare and "DOTNET_STARTUP_HOOKS" not in prepare
    assert f'step rewrite dotnet {dotnet.AGENT}/out/rewrite/Daodan.Rewrite.dll "$WORK" {dotnet.OUT}/table.tsv "$WORK"' \
        in execute
    assert (f'if [ -f {dotnet.BUILT}/built-1 ]; then ( cd "$WORK"/tests/Shop.Tests && DOTNET_STARTUP_HOOKS='
            f"{dotnet.HOOK} DAODAN_RECORD={dotnet.OUT}/calls DAODAN_RECORD_TABLE={dotnet.OUT}/table.tsv timeout -k 30 "
            f"{dotnet.LIMIT} dotnet test --project Shop.Tests.csproj --no-build ) > {dotnet.OUT}/tests-1.log 2>&1; "
            f"echo $? > {dotnet.OUT}/tests-1.code; fi") in execute
    assert execute.index("step rewrite") < execute.index("dotnet test")


# ---------------------------------------------------------------------------------------------------------
# What the recorder wrote, read and placed

def _method(identity, name, kind, rel, line, owner, kickoff="", assembly="Shop"):
    return "\t".join(map(str, ("m", identity, 1, "00000000-0000-0000-0000-000000000001", 100663296 + identity, "", kind,
                               kickoff, rel, line, name, owner, assembly)))


def _site(identity, method, rel, line, columns, name, owner, scope="Shop"):
    return "\t".join(map(str, ("s", identity, method, 1, rel, line, columns[0], line, columns[1], name, owner, scope)))


TABLE = [
    _method(1, "Price", "method", PRICING, 10, "Shop.Pricing"),
    _method(2, "Price", "method", PRICING, 16, "Shop.Discount"),
    _method(3, "get_Rate", "accessor", PRICING, 11, "Shop.Pricing"),
    _method(4, ".ctor", "constructor", "", "", "Shop.Discount"),  # the class writes none
    _method(5, "Total", "method", PRICING, 22, "Shop.Orders"),
    _method(6, "Later", "method", "", "", "Shop.Orders"),  # an async method's body is its state machine's
    _method(7, "MoveNext", "method", PRICING, 33, "Shop.Orders/<Later>d__3", kickoff=6),
    _method(8, "<Doubled>b__1_0", "lambda", PRICING, 28, "Shop.Orders/<>c"),
    _method(9, "Twice", "method", PRICING, 30, "Shop.Orders"),
    _method(10, "Totals", "method", TESTS, 11, "Shop.Tests.PricingTests", assembly="Shop.Tests"),
    _site(1, 1, PRICING, 10, (53, 66), "get_Rate", "Shop.Pricing"),
    _site(2, 2, PRICING, 16, (54, 76), "Price", "Shop.Pricing"),
    _site(3, 5, PRICING, 24, (41, 70), "Price", "Shop.IPricing"),
    _site(4, 10, TESTS, 12, (9, 43), ".ctor", "Shop.Discount"),
    _site(5, 10, TESTS, 13, (9, 70), "Total", "Shop.Orders"),
    _site(6, 10, TESTS, 13, (9, 70), "AreEqual", "Microsoft.VisualStudio.TestTools.UnitTesting.Assert",
          "MSTest.TestFramework"),
    _site(7, 8, PRICING, 28, (84, 97), "Twice", "Shop.Orders"),
    _site(8, 10, TESTS, 22, (9, 53), "Later", "Shop.Orders"),
    _site(9, 10, TESTS, 16, (9, 61), "Twice", "Shop.Orders"),
    _site(10, 10, TESTS, 16, (9, 61), "Twice", "Shop.Orders"),
    _site(11, 10, "", "", ("", ""), ".ctor", "System.Object", "System.Runtime"),
    "a\tsrc/Shop/bin/Debug/net10.0/Shop.dll\t00000000-0000-0000-0000-000000000001\tShop",
    "a\ttests/Shop.Tests/bin/Debug/net10.0/Shop.Tests.dll\t00000000-0000-0000-0000-000000000002\tShop.Tests",
    "x\tsrc/Old/bin/Old.dll\tNotSupportedException: unaligned. before a call",
]
# Two processes: the tests', and `dotnet test`'s own (which ran nothing rewritten); a line cut off by a kill.
CALLS = {"101.jsonl": [{"call": [1, 3]}, {"call": [2, 1]}, {"call": [3, 2]}, {"outside": 3}, {"call": [4, 4]},
                       {"call": [5, 5]}, {"outside": 6}, {"call": [7, 9]}, {"call": [8, 6]}, {"call": [9, 9]},
                       {"call": [10, 9]}, {"outside": 11}],
         "100.jsonl": [{"error": "IOException: disk full"}]}


def _recorded(folder: Path) -> Path:
    (folder / "calls").mkdir(parents=True, exist_ok=True)
    (folder / "table.tsv").write_text("\n".join(TABLE) + "\n", encoding="utf-8")
    for name, rows in CALLS.items():
        (folder / "calls" / name).write_text("".join(json.dumps(row) + "\n" for row in rows) + '{"call": [5',
                                             encoding="utf-8")
    return folder


def test_the_records_name_each_site_s_statement_and_the_project_methods_it_reached(tmp_path):
    observed = dotnet.read(_recorded(tmp_path))
    assert (observed["assemblies"], observed["processes"], observed["errors"]) == (
        ["Shop", "Shop.Tests"], 2, ["IOException: disk full"])
    assert observed["skipped"] == [{"assembly": "src/Old/bin/Old.dll", "why": "NotSupportedException: unaligned. "
                                                                         "before a call"}]
    sites = {site["method"] * 100 + site["line"] if site["line"] else 0: site for site in observed["sites"]}
    assert len(observed["sites"]) == 11
    [later] = [site for site in observed["sites"] if site["name"] == "Later"]
    assert [(item["name"], item["file"], item["line"]) for item in later["callees"]] == [("Later", PRICING, 33)]
    [made] = [site for site in observed["sites"] if site["type"] == "Shop.Discount"]
    assert [(item["kind"], item["file"], item["line"]) for item in made["callees"]] == [("constructor", PRICING, None)]
    assert sites[524]["outside"] and [item["type"] for item in sites[524]["callees"]] == ["Shop.Discount"]


def test_a_site_is_placed_on_the_reference_its_statement_holds_with_the_declaration_it_reached(tmp_path):
    sites, said = dotnet.place(dotnet.read(_recorded(tmp_path)), SOURCES, SHOP.get)
    placed = {(site["file"], site["line"], site["column"], site["name"]): site["callees"] for site in sites}
    assert placed == {
        at(PRICING, 10, "Rate"): [project(10, None, "Rate", "accessor")],
        at(PRICING, 16, "Price", 2): [project(9, 4, "Price", "method")],
        at(PRICING, 24, "Price"): [project(15, 4, "Price", "method"), {
            "kind": "external", "module": "Shop.IPricing", "name": "Price", "assembly": "Shop", "mock": True}],
        at(TESTS, 12, "Discount"): [project(13, 0, "Discount", "constructor")],  # no constructor written: the class
        at(TESTS, 13, "Total"): [project(20, 4, "Total", "method")],
        at(TESTS, 13, "AreEqual"): [{"kind": "external", "module": "Microsoft.VisualStudio.TestTools.UnitTesting.Assert",
                                     "name": "AreEqual", "assembly": "MSTest.TestFramework"}],
        at(PRICING, 28, "Twice"): [project(29, 4, "Twice", "method")],
        at(TESTS, 22, "Later"): [project(31, 4, "Later", "method")]}  # where its state machine's body is
    assert said == {"recorded": 11, "placed": 8, "ambiguous": {"count": 2, "examples": [f"{TESTS}:16 Twice"]},
                    "unplaced": {"no statement in the PDB": 1}}


# ---------------------------------------------------------------------------------------------------------
# How a project's tests ended

RUN = {"root": "tests/A", "runner": "dotnet test", "project": "tests/A/A.csproj",
       "argv": ["dotnet", "test", "--project", "A.csproj", "--no-build"]}
PLATFORM = "Test run summary: Passed!\n  total: {total}\n  failed: {failed}\n  succeeded: 1\n  skipped: 0\n"
VSTEST = "Failed!  - Failed:     1, Passed:     4, Skipped:     0, Total:     5, Duration: 9 ms - A.dll (net8.0)\n"


def test_each_way_the_tests_end_is_their_state_with_its_gap():
    cases = [("0", PLATFORM.format(total=3, failed=0), "ran", 3, []),
             ("2", PLATFORM.format(total=3, failed=1), "ran", 3, ["tests_failed"]),
             ("1", VSTEST, "ran", 5, ["tests_failed"]),
             ("8", PLATFORM.format(total=0, failed=0), "no_tests", 0, ["no_tests"]),
             ("1", "error: the test host could not start", "not_started", 0, ["tests_not_started"]),
             ("124", "", "timeout", 0, ["tests_timeout"]),
             ("137", "", "killed", 0, ["tests_killed"]),
             ("", "", "not_started", 0, ["tests_not_started"])]
    for code, text, state, tests, gaps in cases:
        entry, said = dotnet._outcome(RUN, code, text, "done")
        assert (entry["state"], entry["tests"], [gap["kind"] for gap in said]) == (state, tests, gaps), (code, text)
        assert entry["state"] in dynamic.TESTS


def test_tests_that_fail_say_the_first_failure_and_its_message():
    """Microsoft.Testing.Platform writes `failed <test> (<duration>)` and, indented below, the error; VSTest
    `Failed <test> [<duration>]` and its `Error Message:`: the gap names the first, not the summary."""
    platform = ("Running tests from bin/A.dll\nfailed A.Tests.Fixture.Starts (4s 120ms)\n"
                "  System.InvalidOperationException: the container runtime could not be found\n"
                "  Stack Trace:\n      at A.Tests.Fixture.InitializeAsync()\n" + PLATFORM.format(total=3, failed=3))
    vstest = ("  Failed A.Tests.Pays [12 ms]\n  Error Message:\n   Assert.AreEqual failed. Expected:<2>. Actual:<1>.\n"
              "  Stack Trace:\n     at A.Tests.Pays()\n" + VSTEST)
    for text, first in ((platform, "A.Tests.Fixture.Starts (4s 120ms): System.InvalidOperationException: the "
                                   "container runtime could not be found"),
                        (vstest, "A.Tests.Pays [12 ms]: Assert.AreEqual failed. Expected:<2>. Actual:<1>.")):
        [gap] = dotnet._outcome(RUN, "2", text, "done")[1]
        assert gap["kind"] == "tests_failed" and gap["detail"].endswith(f"the first: {first}"), gap["detail"]


# ---------------------------------------------------------------------------------------------------------
# The container run

CECIL_PACKAGE, SDK = b"the Mono.Cecil package", b"the .NET SDK"
OUT = dotnet.OUT.lstrip("/")


class ObserveTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-dotnet-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        for name in ("containers", "images", "play"):
            (self.state / name).mkdir(parents=True)
        fake = self.scratch / "fake_docker.py"
        fake.write_text(PLAY + FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(fake), str(self.state)))
        self.project = self.scratch / "project"
        files = {**SHOP, "tests/Broken/Broken.csproj": '<Project Sdk="MSTest.Sdk/4.0.2" />'}
        for rel, text in files.items():
            (self.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.project / rel).write_text(text, encoding="utf-8")
        self.planned = {**dotnet.plan({}, sorted(files), files.get), "declared": {"hosts": ("nuget.corp.example",)}}
        pinned = preparation.NEEDS["dotnet"]
        self.served = {dotnet.CECIL[0]: CECIL_PACKAGE, pinned["files"][0][0]: SDK}
        cache = self.scratch / "cache"
        for patcher in (mock.patch.dict(os.environ, {"LOCALAPPDATA": str(cache), "XDG_CACHE_HOME": str(cache)}),
                        mock.patch.object(dotnet, "CECIL", (dotnet.CECIL[0], digest(CECIL_PACKAGE), dotnet.CECIL[2])),
                        mock.patch.dict(preparation.NEEDS, {"dotnet": {**pinned, "files": [
                            (pinned["files"][0][0], digest(SDK), pinned["files"][0][2])]}}),
                        mock.patch.object(resolve_edges, "open_url", self.open_url),
                        mock.patch.object(engine_tools, "open_url", self.open_url),
                        mock.patch("time.sleep")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def open_url(self, url: str, timeout: float):
        if url not in self.served:
            raise OSError(f"not served: {url}")
        return io.BytesIO(self.served[url])

    def play(self, phase: str, *, files: dict[str, bytes] | None = None, text: str = "", code: int = 0):
        folder = self.state / "play" / phase
        for rel, data in (files or {}).items():
            target = folder / "fs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "log").write_text(text, encoding="utf-8")
        (folder / "code").write_text(str(code))

    def observe(self, agent: int = 0, rewrite: int = 0) -> dict:
        # the runs in the plan's order: tests/Broken first, which does not build, then tests/Shop.Tests
        self.play("prepare", text=log(("sdk", 0, ""), ("agent", agent, "error CS1002: ; expected"),
                                      ("build-1", 1, "Broken.csproj : error MSB4236: The SDK 'MSTest.Sdk' could not "
                                                     "be found."), ("build-2", 0, "Build succeeded.")))
        recorded = _recorded(self.scratch / "recorded")
        files = {f"{OUT}/table.tsv": (recorded / "table.tsv").read_bytes(),
                 **{f"{OUT}/calls/{path.name}": path.read_bytes() for path in (recorded / "calls").iterdir()},
                 f"{OUT}/tests-2.code": b"0\n", f"{OUT}/tests-2.log": PLATFORM.format(total=2, failed=0).encode()}
        self.play("execute", files=files, text=log(("rewrite", rewrite, "Unhandled exception. System.IO.IOException")))
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            return dotnet.observe(self.project, self.planned, self.scratch / "work", self.engine)

    def created(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        calls = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [call for call in calls if call[0] == "create"]

    def test_the_tests_run_recorded_in_the_container_and_a_project_that_does_not_build_is_said(self):
        result = self.observe()
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual(result["state"], "ran")
        self.assertEqual([(run["project"], run["state"]) for run in result["runs"]],
                         [("tests/Broken/Broken.csproj", "not_started"), ("tests/Shop.Tests/Shop.Tests.csproj", "ran")])
        kinds = [gap["kind"] for gap in result["gaps"]]
        self.assertEqual(kinds, ["tests_not_started", "assemblies_unrecorded", "recorder_failed", "sites_ambiguous"])
        self.assertIn("The SDK 'MSTest.Sdk' could not be found", result["gaps"][0]["detail"])
        self.assertEqual(len(result["sites"]), 8)
        self.assertEqual((result["facts"]["processes"], result["facts"]["placed"]), (2, 8))
        arrived = self.state / "containers" / self.created()[1][self.created()[1].index("--name") + 1] / "fs"
        agent = arrived / dotnet.AGENT.lstrip("/")
        self.assertEqual((agent / "packages" / dotnet.CECIL[2]).read_bytes(), CECIL_PACKAGE)
        self.assertTrue((agent / "rewrite/Rewrite.cs").is_file() and (agent / "nuget.config").is_file())
        self.assertIn("nuget.corp.example", self.created()[0])  # the proxy reaches the feeds the project declares
        execution = self.created()[2]
        self.assertEqual(execution[execution.index("--network") + 1], "none")

    def test_a_rewriter_that_stops_is_a_gap_and_what_was_recorded_is_kept(self):
        result = self.observe(rewrite=1)
        [said] = [gap for gap in result["gaps"] if gap["kind"] == "recorder_failed" and "rewriter" in gap["detail"]]
        self.assertIn("System.IO.IOException", said["detail"])
        self.assertEqual((result["state"], len(result["sites"])), ("ran", 8))

    def test_a_recorder_that_does_not_build_fails_the_run_with_its_cause(self):
        result = self.observe(agent=1)
        self.assertEqual(result["state"], "failed")
        self.assertIn("error CS1002", result["cause"])
        self.assertIsNone(dynamic.malformed(result))

    def test_without_a_container_nothing_runs_and_the_cause_is_said(self):
        """Not on the host either: a `dotnet` there, which every build, target, generator and test needs, would
        leave its mark."""
        tools, mark = self.scratch / "host-bin", self.scratch / "ran-on-the-host"
        tools.mkdir()
        (tools / "dotnet").write_text(f"#!/bin/sh\ntouch '{mark}'\n", encoding="utf-8", newline="\n")
        (tools / "dotnet").chmod(0o755)
        with mock.patch.object(container, "find_engine", side_effect=container.Gap("no engine", "start Docker")), \
                mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
                mock.patch.dict(os.environ, {"PATH": f"{tools}{os.pathsep}{os.environ['PATH']}"}):
            result = dotnet.observe(self.project, self.planned, self.scratch / "work")
        self.assertEqual((result["state"], result["cause"], result["remedy"]), ("gap", "no engine", "start Docker"))
        self.assertFalse(mark.exists())


# ---------------------------------------------------------------------------------------------------------
# The recorder, for real

def _sdk() -> int:
    try:
        done = subprocess.run(["dotnet", "--version"], capture_output=True, text=True, timeout=120)
    except OSError:
        return 0
    return int(done.stdout.split(".")[0]) if done.returncode == 0 and done.stdout[:1].isdigit() else 0


class RecorderTest(unittest.TestCase):
    """Daodan's projects built by the SDK on the PATH, the shop's tests built, rewritten and run under them."""

    @classmethod
    def setUpClass(cls):
        if _sdk() < 10:
            raise unittest.SkipTest("no .NET SDK from 10 on the PATH: the recorder is built and run by it")
        cls.root = Path(tempfile.mkdtemp(prefix="daodan-dotnet-record-"))
        agent, shop = cls.root / "agent", cls.root / "shop"
        shutil.copytree(dotnet.RECORD, agent)
        (agent / "packages").mkdir()
        package = agent / "packages" / dotnet.CECIL[2]
        urllib.request.urlretrieve(dotnet.CECIL[0], package)
        assert hashlib.sha256(package.read_bytes()).hexdigest() == dotnet.CECIL[1]
        for rel, text in SHOP.items():
            (shop / rel).parent.mkdir(parents=True, exist_ok=True)
            (shop / rel).write_text(text, encoding="utf-8")
        env = {**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1",
               **{key: value for key, value in dotnet.csharp.ENV.items() if key.startswith("DOTNET_")}}
        record = {"DOTNET_STARTUP_HOOKS": str(agent / "out/record/Daodan.Record.dll"),
                  "DAODAN_RECORD": str(cls.root / "back/calls"), "DAODAN_RECORD_TABLE": str(cls.root / "back/table.tsv")}
        (cls.root / "back").mkdir()
        for command, cwd, more in ((dotnet.agent_commands(str(agent)), agent, {}),
                                   ("dotnet build tests/Shop.Tests -nologo", shop, {}),
                                   (f"dotnet {agent}/out/rewrite/Daodan.Rewrite.dll {shop} {cls.root}/back/table.tsv "
                                    f"{shop}", shop, {}),
                                   ("dotnet test --project Shop.Tests.csproj --no-build", shop / "tests/Shop.Tests",
                                    record)):
            done = subprocess.run(["bash", "-c", command], cwd=cwd, env={**env, **more}, capture_output=True,
                                  text=True, timeout=1800)
            assert done.returncode == 0, (command, (done.stdout + done.stderr)[-3000:])
        cls.observed = dotnet.read(cls.root / "back")
        cls.sites, cls.said = dotnet.place(cls.observed, SOURCES, SHOP.get)
        cls.placed = {(site["file"], site["line"], site["column"], site["name"]): site["callees"]
                      for site in cls.sites}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_the_project_s_assemblies_are_rewritten_and_one_process_recorded(self):
        self.assertEqual(self.observed["assemblies"], ["Shop", "Shop.Tests"])  # not MSTest's, whose PDB is /_/-rooted
        self.assertEqual((self.observed["skipped"], self.observed["errors"]), ([], []))
        self.assertGreaterEqual(self.observed["processes"], 1)

    def test_a_call_reaches_the_method_that_ran_through_an_interface_base_or_override(self):
        self.assertEqual(self.placed[at(PRICING, 24, "Price")], [project(15, 4, "Price", "method")])
        self.assertEqual(self.placed[at(PRICING, 16, "Price", 2)], [project(9, 4, "Price", "method")])
        self.assertEqual(self.placed[at(PRICING, 10, "Rate")], [project(10, None, "Rate", "accessor")])
        self.assertEqual(self.placed[at(TESTS, 12, "Discount")], [project(13, 0, "Discount", "constructor")])

    def test_a_lambda_s_calls_are_its_own_and_one_a_library_runs_is_not_the_library_call_s(self):
        self.assertEqual(self.placed[at(PRICING, 28, "Twice")], [project(29, 4, "Twice", "method")])
        [select] = self.placed[at(PRICING, 28, "Select")]
        self.assertEqual((select["kind"], select["module"]), ("external", "System.Linq.Enumerable"))
        self.assertEqual(self.placed[at(TESTS, 15, "Twice")], [project(29, 4, "Twice", "method")])

    def test_an_async_method_is_reached_at_its_call_and_its_body_s_calls_after_an_await(self):
        self.assertEqual(self.placed[at(TESTS, 22, "Later")], [project(31, 4, "Later", "method")])
        self.assertEqual(self.placed[at(PRICING, 35, "Twice")], [project(29, 4, "Twice", "method")])

    def test_two_calls_of_one_name_in_one_statement_are_ambiguous(self):
        self.assertIn(f"{TESTS}:16 Twice", self.said["ambiguous"]["examples"])
