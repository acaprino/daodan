"""scip-dotnet for C#: what it takes from the pre-map, its container run, and what its index leaves to the reader.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_csharp.py

Nothing real runs: the container is the fake Docker-compatible command line of `test_codebase_map_container.py`,
which plays what a test scripted for the two bash phases (as `test_codebase_map_indexers_jvm.py`), and downloads are
served from memory. The reader's hooks are tested on a small C# project written here, snapshotted for real, with
the index scip-dotnet 0.2.16 would write for it encoded by hand from its source (`ScipDocumentIndexer.cs`,
`ScipCSharpSyntaxWalker.cs`) and its snapshot tests: one occurrence per identifier, a namespace named by its last
segment, a type without its arity, `new X()` at the type, no enclosing range.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import engine_tools  # noqa: E402
import preparation  # noqa: E402
import resolve_edges  # noqa: E402
import test_codebase_map_code_graph as graph_tests  # noqa: E402
from indexers import csharp  # noqa: E402
from test_codebase_map_container import FAKE_CLI  # noqa: E402
from test_codebase_map_indexers_jvm import PLAY, Recorder, digest, log  # noqa: E402

GLOBAL_JSON = {"tool": "dotnet", "version": "8.0.404", "declared_in": "global.json"}


# ---------------------------------------------------------------------------------------------------------
# What it declares and takes from the pre-map

def test_the_analyzer_declares_itself_and_its_units_index_the_language():
    """The module is found by its declarations: the pass's entry, C#, the pre-map's .NET projects, a build that runs
    only in a container. The pre-map then names `dotnet-project` as the unit kind able to index C#."""
    import indexers
    import premap
    assert csharp in indexers.analyzers()
    assert (csharp.ENTRY, csharp.LANGUAGES, csharp.UNIT_KINDS, csharp.NEEDS_CONTAINER) == (
        "scip-dotnet", ("csharp",), frozenset({"dotnet-project"}), True)
    assert csharp.MIN_FREE > 0
    assert premap.indexed_by()["C#"] == frozenset({"dotnet-project"})


def test_the_tool_is_pinned_by_version_and_sha256():
    url, sha256, name = csharp.TOOL
    assert url == f"https://api.nuget.org/v3-flatcontainer/scip-dotnet/{csharp.VERSION}/scip-dotnet.{csharp.VERSION}.nupkg"
    assert re.fullmatch(r"[0-9a-f]{64}", sha256) and name == "scip-dotnet.nupkg"


def test_structure_is_the_pre_maps_solutions_projects_and_sdk():
    """The folders of the solutions (the `dotnet` workspaces), each .NET project with the solution that lists it
    (None: it is run by its own file), and the SDK the project states; a target framework is no SDK to install."""
    record = {
        "units": [{"kind": "dotnet-project", "root": "src/Shop.Api", "manifest": "src/Shop.Api/Shop.Api.csproj"},
                  {"kind": "dotnet-project", "root": "src/Shop.Core", "manifest": "src/Shop.Core/Shop.Core.csproj"},
                  {"kind": "dotnet-project", "root": "tools/Gen", "manifest": "tools/Gen/Gen.csproj"},
                  {"kind": "npm-package", "root": "web", "manifest": "web/package.json"}],
        "workspace": [{"tool": "dotnet", "root": ".", "members": ["src/Shop.Api", "src/Shop.Core"]},
                      {"tool": "npm", "root": "web", "members": []}],
        "toolchains": [GLOBAL_JSON, {"tool": "dotnet-target", "version": "net8.0", "declared_in": "Directory.Build.props"},
                       {"tool": "node", "version": "24", "declared_in": ".nvmrc"}]}
    assert csharp.structure(record) == {
        "roots": {""},
        "units": [{"root": "src/Shop.Api", "manifest": "src/Shop.Api/Shop.Api.csproj", "solution": ""},
                  {"root": "src/Shop.Core", "manifest": "src/Shop.Core/Shop.Core.csproj", "solution": ""},
                  {"root": "tools/Gen", "manifest": "tools/Gen/Gen.csproj", "solution": None}],
        "toolchains": [GLOBAL_JSON]}
    assert csharp.structure({}) == {"roots": set(), "units": [], "toolchains": []}
    import inspect
    assert not re.search(r"rglob|[.]walk[(]", inspect.getsource(csharp))  # no file search of its own


def test_the_targets_are_each_solution_and_each_project_no_solution_lists(tmp_path):
    """One run per solution file of a workspace's folder and per project outside every solution (C# and Visual
    Basic: what scip-dotnet reads); a workspace folder without a solution file is said, never skipped."""
    for rel in ("Shop.sln", "legacy/Old.slnx", "legacy/New.sln", "legacy/notes.txt"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("", encoding="utf-8")
    units = [{"root": "src/A", "manifest": "src/A/A.csproj", "solution": ""},
             {"root": "tools/T", "manifest": "tools/T/T.csproj", "solution": None},
             {"root": "tools/V", "manifest": "tools/V/V.vbproj", "solution": None},
             {"root": "tools/F", "manifest": "tools/F/F.fsproj", "solution": None},
             {"root": "gone/G", "manifest": "gone/G/G.csproj", "solution": "gone"}]
    wanted, states = csharp.targets(tmp_path, {"", "legacy", "gone"}, units)
    assert wanted == [("Shop.sln", ""), ("legacy/New.sln", "legacy"), ("legacy/Old.slnx", "legacy"),
                      ("tools/T/T.csproj", "tools/T/T.csproj"), ("tools/V/V.vbproj", "tools/V/V.vbproj")]
    assert states == [{"root": "gone", "state": "failed", "reason": "no solution file in the folder of this workspace"}]


# ---------------------------------------------------------------------------------------------------------
# The container run, against the fake engine

TOOL, SDK, MISE = b"the scip-dotnet package", b"the .NET SDK", b"mise"
OUT = csharp.OUT.lstrip("/")
UNITS = [{"root": "src/A", "manifest": "src/A/A.csproj", "solution": ""},
         {"root": "tools/T", "manifest": "tools/T/T.csproj", "solution": None}]
NO_DOCUMENTS = ("12:00:01 warn: ScipDotnet.IndexCommandOptions[0] Indexing finished without error but no documents "
                "were indexed.\n12:00:01 fail: Microsoft.CodeAnalysis.MSBuild.MSBuildWorkspace[0] Failure: Msbuild "
                "failed when processing the file '/work/tools/T/T.csproj' with message: NETSDK1004: Assets file "
                "'/work/tools/T/obj/project.assets.json' not found. (occurred 1 times)")


class RunTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-csharp-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        for name in ("containers", "images", "play"):
            (self.state / name).mkdir(parents=True)
        fake = self.scratch / "fake_docker.py"
        fake.write_text(PLAY + FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(fake), str(self.state)))
        self.project = self.scratch / "project"
        for rel, text in {"Shop.sln": "", "src/A/A.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\" />\n",
                          "src/A/A.cs": "class A { }\n", "tools/T/T.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\" />\n",
                          "tools/T/T.cs": "class T { }\n"}.items():
            (self.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.project / rel).write_text(text, encoding="utf-8")
        self.work = self.scratch / "work"
        self.asked: list[str] = []
        pinned = preparation.NEEDS["dotnet"]
        self.served = {csharp.TOOL[0]: TOOL, pinned["files"][0][0]: SDK, preparation.MISE[0]: MISE}
        cache = self.scratch / "cache"
        for patcher in (mock.patch.dict(os.environ, {"LOCALAPPDATA": str(cache), "XDG_CACHE_HOME": str(cache)}),
                        mock.patch.object(csharp, "TOOL", (csharp.TOOL[0], digest(TOOL), csharp.TOOL[2])),
                        mock.patch.dict(preparation.NEEDS, {"dotnet": {**pinned, "files": [
                            (pinned["files"][0][0], digest(SDK), pinned["files"][0][2])]}}),
                        mock.patch.object(preparation, "MISE", (preparation.MISE[0], digest(MISE), "mise")),
                        mock.patch.object(resolve_edges, "open_url", self.open_url),
                        mock.patch.object(engine_tools, "open_url", self.open_url),
                        mock.patch("time.sleep")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def open_url(self, url: str, timeout: float):
        self.asked.append(url)
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

    def play_success(self):
        """What a good run leaves: each target's index, as scip-dotnet wrote it."""
        self.play("prepare", text=log(("sdk", 0, ""), ("unpack", 0, ""), ("restore", 0, "")))
        self.play("execute", files={f"{OUT}/index-1.scip": b"the solution's index",
                                    f"{OUT}/index-2.scip": b"the project's index"},
                  text=log(("index-1", 0, "12:00:01 info: done"), ("index-2", 0, ""), peak=2**29))

    def index(self, **options) -> dict:
        options.setdefault("engine", self.engine)
        options.setdefault("roots", {""})
        options.setdefault("units", UNITS)
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
                mock.patch("subprocess.Popen", Recorder):
            return csharp.index(self.project, self.work, **options)

    def script(self, phase: str) -> str:
        return (self.state / f"scripts/{phase}.sh").read_text(encoding="utf-8")

    def created(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        calls = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [call for call in calls if call[0] == "create"]

    def arrived(self, phase: int = 1) -> Path:
        """The file system of a created container (0 is the proxy, 1 the preparation)."""
        call = self.created()[phase]
        return self.state / "containers" / call[call.index("--name") + 1] / "fs"

    def test_the_preparation_brings_the_pinned_sdk_and_the_tool_and_restores_the_projects(self):
        """Without an SDK in the pre-map: the SDK the preparation carries, scip-dotnet's package unpacked, then the
        project's own restore in the solution's folder and in the folder of the project no solution lists."""
        self.play_success()
        self.index()
        script = self.script("prepare")
        setup = preparation.setup(["dotnet"])["lines"][0]
        restore = preparation.restore("dotnet", [".", "tools/T"])
        unpack = f"python3 -m zipfile -e {preparation.IN}/scip-dotnet.nupkg {csharp.HOME}"
        for line in (setup, unpack, restore):
            self.assertIn(line, script)
        self.assertLess(script.index(setup), script.index("step restore"))
        self.assertNotIn("mise", script)
        self.assertNotIn(" index ", script)  # the indexer runs with no network, in the execution
        carried = self.arrived(1) / preparation.IN.lstrip("/")
        self.assertEqual((carried / "scip-dotnet.nupkg").read_bytes(), TOOL)
        self.assertEqual((carried / "dotnet.tar.gz").read_bytes(), SDK)

    def test_preparation_reaches_only_nuget_and_execution_no_network(self):
        self.play_success()
        self.index()
        proxy, prepare, execute = self.created()
        self.assertEqual(proxy[proxy.index(str(container.PROXY_PORT)) + 1:], ["api.nuget.org"])
        self.assertTrue(prepare[prepare.index("--network") + 1].startswith("daodan-net-"))
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        for call in (prepare, execute):
            self.assertIn(csharp.IMAGE, call)
            self.assertIn("EnableWindowsTargeting=true", call)  # as scip-dotnet's own restore passes it
            self.assertIn(f"PATH={preparation.PATH}", call)
        self.assertIsNone(re.search(r"https?://", self.script("prepare")), "the preparation names a host")

    def test_execution_runs_scip_dotnet_over_each_target_from_the_checkout(self):
        """Each solution and each project outside one is a run of its own, from the checkout's root (documents are
        named from the working directory), without scip-dotnet's own restore, with the build of scip-dotnet that
        matches the SDK's runtime."""
        self.play_success()
        self.index()
        script = self.script("execute")
        common = '--working-directory "$WORK" --output "$OUT/index-{}.scip" --skip-dotnet-restore'
        self.assertIn(f"step index-1 dotnet \"$DLL\" index Shop.sln {common.format(1)}", script)
        self.assertIn(f"step index-2 dotnet \"$DLL\" index tools/T/T.csproj {common.format(2)}", script)
        self.assertIn(f"{csharp.HOME}/tools/net${{SDK%%.*}}.0/any/scip-dotnet.dll", script)
        self.assertNotIn("restore", script.replace("--skip-dotnet-restore", ""))

    def test_outputs_come_back_and_the_contract_is_returned(self):
        self.play_success()
        result = self.index()
        self.assertNotIn("state", result)
        work = self.work.resolve()
        self.assertEqual(result["indexes"], [[str(work / "index-1.scip"), ""], [str(work / "index-2.scip"), ""]])
        self.assertEqual((work / "index-1.scip").read_bytes(), b"the solution's index")
        self.assertEqual(result["builds"], [{"root": "Shop.sln", "state": "done"},
                                            {"root": "tools/T/T.csproj", "state": "done"}])
        self.assertEqual(result["indexer"], {"name": "scip-dotnet", "version": csharp.VERSION, "seconds": 12.5,
                                             "peak_mb": 1024})
        self.assertEqual([(run["phase"], run["step"], run["returncode"]) for run in result["runs"]],
                         [("prepare", "sdk", 0), ("prepare", "unpack", 0), ("prepare", "restore", 0),
                          ("execute", "index-1", 0), ("execute", "index-2", 0)])
        self.assertEqual(result["configs"], {"units": UNITS, "failed": {}, "unloaded": {}})
        self.assertNotIn("gaps", result)

    def test_the_sdk_the_pre_map_states_is_installed_by_mise_in_place_of_the_pin(self):
        self.play_success()
        self.index(toolchains=[GLOBAL_JSON])
        script = self.script("prepare")
        self.assertIn("install dotnet@8.0.404", script)
        self.assertNotIn("dotnet.tar.gz", script)
        carried = self.arrived(1) / preparation.IN.lstrip("/")
        self.assertEqual((carried / "mise").read_bytes(), MISE)
        self.assertFalse((carried / "dotnet.tar.gz").exists())
        proxy = self.created()[0]
        for host in ("api.nuget.org", "builds.dotnet.microsoft.com"):
            self.assertIn(host, proxy)

    def test_a_restore_that_fails_is_a_gap_and_the_index_goes_on(self):
        self.play_success()
        failed = "DAODAN-RESTORE-FAILED dotnet .\nerror NU1101: Unable to find package Gone.\nDAODAN-RESTORE-END\n"
        self.play("prepare", text=log(("sdk", 0, ""), ("unpack", 0, ""), ("restore", 0, failed)))
        result = self.index()
        self.assertEqual(len(result["indexes"]), 2)
        self.assertEqual(result["gaps"], preparation.restore_gaps(failed))

    def test_an_sdk_the_preparation_could_not_install_is_a_gap_and_the_failure_says_what_dotnet_said(self):
        self.play("prepare", text=log(("sdk", 0, "DAODAN-MISSING dotnet@8.0.404"), ("unpack", 0, ""), ("restore", 0, "")))
        self.play("execute", text=log(("sdk", 70, "no .NET SDK runs here: bash: dotnet: command not found")), code=70)
        result = self.index(toolchains=[GLOBAL_JSON])
        self.assertEqual(result["state"], "failed")
        self.assertIn("dotnet: command not found", result["reason"])
        self.assertEqual([(gap["kind"], gap["tool"], gap["version"]) for gap in result["gaps"]],
                         [("toolchain_unavailable", "dotnet", "8.0.404")])

    def test_a_container_gap_is_unavailable_with_its_cause_and_remedy(self):
        cause, remedy = "no container engine answers: neither docker nor podman", "start Docker or Podman"
        Recorder.calls = []
        with mock.patch.object(container, "find_engine", side_effect=container.Gap(cause, remedy)):
            result = self.index(engine=None)
        self.assertEqual((result["state"], result["reason"], result["install"]), ("unavailable", cause, remedy))
        self.assertEqual((result["indexes"], Recorder.calls, self.asked), ([], [], []))
        self.assertEqual(result["indexer"]["name"], "scip-dotnet")

    def test_a_run_that_writes_no_index_is_failed_with_the_cause_and_the_log_tail(self):
        self.play("prepare", text=log(("sdk", 0, ""), ("unpack", 0, ""), ("restore", 0, "")))
        tail = "Unhandled exception: System.IO.FileNotFoundException: Shop.sln"
        self.play("execute", text=log(("index-1", 134, tail), ("index-2", 134, tail)))
        result = self.index()
        self.assertEqual(result["state"], "failed")
        self.assertIn("scip-dotnet wrote no index (exit code 134)", result["reason"])
        self.assertIn("FileNotFoundException", result["reason"])
        self.assertEqual([build["state"] for build in result["builds"]], ["failed", "failed"])
        self.assertEqual(result["indexes"], [])

    def test_a_preparation_that_fails_is_failed_and_nothing_executes(self):
        self.play("prepare", text=log(("sdk", 0, ""), ("unpack", 1, "BadZipFile: File is not a zip file")), code=70)
        result = self.index()
        self.assertEqual(result["state"], "failed")
        self.assertIn("preparation exited with code 70", result["reason"])
        self.assertIn("BadZipFile", result["reason"])
        self.assertEqual(len(self.created()), 2)  # the proxy and the preparation

    def test_a_target_scip_dotnet_indexes_no_document_of_is_failed_and_the_others_are_kept(self):
        """scip-dotnet writes an index and exits 0 even when MSBuild loads nothing: it says so, with the workspace's
        failure. That run is a build without an index, the failure a gap, and both reach `missing`."""
        self.play("prepare", text=log(("sdk", 0, ""), ("unpack", 0, ""), ("restore", 0, "")))
        self.play("execute", files={f"{OUT}/index-1.scip": b"the solution's index", f"{OUT}/index-2.scip": b"empty"},
                  text=log(("index-1", 0, ""), ("index-2", 0, NO_DOCUMENTS)))
        result = self.index()
        self.assertEqual([path for path, _prefix in result["indexes"]], [str(self.work.resolve() / "index-1.scip")])
        failure = ("Msbuild failed when processing the file '/work/tools/T/T.csproj' with message: NETSDK1004: Assets "
                   "file '/work/tools/T/obj/project.assets.json' not found.")
        self.assertEqual(result["builds"][0], {"root": "Shop.sln", "state": "done"})
        self.assertEqual(result["builds"][1]["state"], "failed")
        self.assertIn("no documents were indexed", result["builds"][1]["reason"])
        self.assertEqual(result["gaps"], [{"kind": "workspace_failure", "path": "tools/T/T.csproj", "detail": failure}])
        self.assertEqual(result["configs"]["unloaded"], {"tools/T/T.csproj": failure})
        self.assertEqual(list(result["configs"]["failed"]), ["tools/T/T.csproj"])

    def test_without_a_project_in_the_pre_map_nothing_runs_and_the_cause_is_said(self):
        result = self.index(roots=set(), units=[])
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("no solution or C# project in the pre-map", result["reason"])
        self.assertEqual(self.created(), [])


# ---------------------------------------------------------------------------------------------------------
# What the index leaves to the reader

SOURCES = {
    "src/Core/Order.cs": """namespace Shop.Core;

public record Order(int Id, decimal Total);

public interface IPricing
{
    decimal Price(Order order);
}

public class Pricing : IPricing
{
    private int rate;
    public int Rate { get { return rate; } set { rate = value; } }
    public Pricing(int rate) { this.rate = rate; }
    public virtual decimal Price(Order order)
    {
        return order.Total * Rate;
    }
}

public class Discount : Pricing
{
    public Discount() : base(2) { }
    public override decimal Price(Order order)
    {
        return base.Price(order) / 2;
    }
}

[Marker]
public static class Extensions
{
    public static decimal Twice(this Order order) => order.Total * 2;
    public static decimal Twice(this Order order, int times) => order.Total * times;
    public static decimal Both(Order order) => order.Twice() + Twice(order, 3);
}

public class MarkerAttribute : System.Attribute { }
""",
    "src/Core/Models/User.cs": "namespace Shop.Core.Models;\n\npublic partial class User\n{\n"
                               "    public string Name = \"\";\n}\n",
    "src/Core/Models/User.Greet.cs": "namespace Shop.Core.Models;\n\npublic partial class User\n{\n"
                                     "    public string Greet() { return Name; }\n}\n",
    "src/Api/Models/User.cs": "namespace Shop.Api.Models;\n\npublic class User { }\n",
    "src/Api/Program.cs": """using Shop.Core;

IPricing pricing = new Discount();
var order = new Order(1, 2m);
Console.WriteLine(pricing.Price(order));
Console.WriteLine(order.Twice());
Pricing plain = new(3);
var user = new Shop.Core.Models.User();
Console.WriteLine(user.Greet());
""",
}
C = "scip-dotnet nuget . . "  # the package scip-dotnet gives every symbol defined in source
RUNTIME = "scip-dotnet nuget System.Runtime 8.0.0.0 "
CONSOLE = "scip-dotnet nuget System.Console 8.0.0.0 System/Console#"
CTOR = "`.ctor`"
# Per file, `(line, word, symbol, definition)`: the occurrence at that word of the line (`word@2`: its second one).
OCCURRENCES = {
    "src/Core/Order.cs": [
        (1, "Shop", C + "Shop/", False), (1, "Core", C + "Core/", False),
        (3, "Order", C + "Core/Order#", True), (3, "Id", C + f"Core/Order#{CTOR}().(Id)", True),
        (3, "Total", C + f"Core/Order#{CTOR}().(Total)", True),
        (5, "IPricing", C + "Core/IPricing#", True),
        (7, "Price", C + "Core/IPricing#Price().", True), (7, "Order", C + "Core/Order#", False),
        (7, "order", C + "Core/IPricing#Price().(order)", True),
        (10, "Pricing", C + "Core/Pricing#", True), (10, "IPricing", C + "Core/IPricing#", False),
        (12, "rate", C + "Core/Pricing#rate.", True),
        (13, "Rate", C + "Core/Pricing#Rate.", True), (13, "rate", C + "Core/Pricing#rate.", False),
        (13, "rate@2", C + "Core/Pricing#rate.", False), (13, "value", C + "Core/Pricing#set_Rate().(value)", False),
        (14, "Pricing", C + f"Core/Pricing#{CTOR}().", True), (14, "rate", C + f"Core/Pricing#{CTOR}().(rate)", True),
        (14, "rate@2", C + "Core/Pricing#rate.", False), (14, "rate@3", C + f"Core/Pricing#{CTOR}().(rate)", False),
        (15, "Price", C + "Core/Pricing#Price().", True), (15, "Order", C + "Core/Order#", False),
        (15, "order", C + "Core/Pricing#Price().(order)", True),
        (17, "order", C + "Core/Pricing#Price().(order)", False), (17, "Total", C + "Core/Order#Total.", False),
        (17, "Rate", C + "Core/Pricing#Rate.", False),
        (21, "Discount", C + "Core/Discount#", True), (21, "Pricing", C + "Core/Pricing#", False),
        (23, "Discount", C + f"Core/Discount#{CTOR}().", True),
        (24, "Price", C + "Core/Discount#Price().", True), (24, "Order", C + "Core/Order#", False),
        (24, "order", C + "Core/Discount#Price().(order)", True),
        (26, "Price", C + "Core/Pricing#Price().", False), (26, "order", C + "Core/Discount#Price().(order)", False),
        (30, "Marker", C + f"Core/MarkerAttribute#{CTOR}().", False),
        (31, "Extensions", C + "Core/Extensions#", True),
        (33, "Twice", C + "Core/Extensions#Twice().", True), (33, "Order", C + "Core/Order#", False),
        (33, "order", C + "Core/Extensions#Twice().(order)", True),
        (33, "order@2", C + "Core/Extensions#Twice().(order)", False), (33, "Total", C + "Core/Order#Total.", False),
        (34, "Twice", C + "Core/Extensions#Twice(+1).", True), (34, "Order", C + "Core/Order#", False),
        (34, "order", C + "Core/Extensions#Twice(+1).(order)", True),
        (34, "times", C + "Core/Extensions#Twice(+1).(times)", True),
        (34, "order@2", C + "Core/Extensions#Twice(+1).(order)", False), (34, "Total", C + "Core/Order#Total.", False),
        (34, "times@2", C + "Core/Extensions#Twice(+1).(times)", False),
        (35, "Both", C + "Core/Extensions#Both().", True), (35, "Order", C + "Core/Order#", False),
        (35, "order", C + "Core/Extensions#Both().(order)", True),
        (35, "order@2", C + "Core/Extensions#Both().(order)", False),
        # a reduced extension call is written without its overload number, a call in static form with it
        (35, "Twice", C + "Core/Extensions#Twice().", False), (35, "Twice@2", C + "Core/Extensions#Twice(+1).", False),
        (35, "order@3", C + "Core/Extensions#Both().(order)", False),
        (38, "MarkerAttribute", C + "Core/MarkerAttribute#", True), (38, "System", C + "System/", False),
        (38, "Attribute", RUNTIME + "System/Attribute#", False)],
    "src/Core/Models/User.cs": [
        (1, "Shop", C + "Shop/", False), (1, "Core", C + "Core/", False), (1, "Models", C + "Models/", False),
        (3, "User", C + "Models/User#", True), (5, "Name", C + "Models/User#Name.", True)],
    "src/Core/Models/User.Greet.cs": [
        (1, "Shop", C + "Shop/", False), (1, "Core", C + "Core/", False), (1, "Models", C + "Models/", False),
        (3, "User", C + "Models/User#", True), (5, "Greet", C + "Models/User#Greet().", True),
        (5, "Name", C + "Models/User#Name.", False)],
    "src/Api/Models/User.cs": [
        (1, "Shop", C + "Shop/", False), (1, "Api", C + "Api/", False), (1, "Models", C + "Models/", False),
        (3, "User", C + "Models/User#", True)],
    "src/Api/Program.cs": [
        (1, "Shop", C + "Shop/", False), (1, "Core", C + "Core/", False),
        (3, "IPricing", C + "Core/IPricing#", False), (3, "pricing", "local 0", True),
        (3, "Discount", C + "Core/Discount#", False),
        (4, "order", "local 1", True), (4, "Order", C + "Core/Order#", False),
        (5, "Console", CONSOLE, False), (5, "WriteLine", CONSOLE + "WriteLine(+7).", False),
        (5, "pricing", "local 0", False), (5, "Price", C + "Core/IPricing#Price().", False),
        (5, "order", "local 1", False),
        (6, "Console", CONSOLE, False), (6, "WriteLine", CONSOLE + "WriteLine(+7).", False),
        (6, "order", "local 1", False), (6, "Twice", C + "Core/Extensions#Twice().", False),
        (7, "Pricing", C + "Core/Pricing#", False), (7, "plain", "local 2", True),
        (8, "user", "local 3", True), (8, "Shop", C + "Shop/", False), (8, "Core", C + "Core/", False),
        (8, "Models", C + "Models/", False), (8, "User", C + "Models/User#", False),
        (9, "Console", CONSOLE, False), (9, "WriteLine", CONSOLE + "WriteLine(+11).", False),
        (9, "user", "local 3", False), (9, "Greet", C + "Models/User#Greet().", False)],
}
# A definition's relationships, as `ScipDocumentIndexer.VisitOccurrence` writes them: a type's base types and
# interfaces, a method's overridden methods and the interface members it implements.
IMPLEMENTS = {
    C + "Core/Order#": [RUNTIME + "System/IEquatable#"],
    C + "Core/Pricing#": [C + "Core/IPricing#"],
    C + "Core/Pricing#Price().": [C + "Core/IPricing#Price()."],
    C + "Core/Discount#": [C + "Core/Pricing#", C + "Core/IPricing#"],
    C + "Core/Discount#Price().": [C + "Core/Pricing#Price().", C + "Core/IPricing#Price()."],
    C + "Core/MarkerAttribute#": [RUNTIME + "System/Attribute#"],
}


def _document(rel: str) -> bytes:
    """The document scip-dotnet writes for `rel`: no position encoding (Roslyn's columns are UTF-16 units)."""
    lines, occurrences, informations = SOURCES[rel].split("\n"), [], []
    for line, word, symbol, definition in OCCURRENCES[rel]:
        name, _, nth = word.partition("@")
        start = [match.start() for match in re.finditer(rf"\b{re.escape(name)}\b", lines[line - 1])][int(nth or 1) - 1]
        occurrences.append(graph_tests.occurrence(line, start, start + len(name), symbol, definition))
        if definition:
            informations.append(graph_tests._field(1, symbol) + b"".join(
                graph_tests._field(4, graph_tests._field(1, target) + graph_tests._field(3, 1))
                for target in IMPLEMENTS.get(symbol, ())))
    return graph_tests._field(2, graph_tests._field(1, rel) + b"".join(graph_tests._field(2, o) for o in occurrences)
                              + b"".join(graph_tests._field(3, i) for i in informations))


def _graph(folder: Path, rels, configs: dict | None = None) -> dict:
    """The project snapshotted, the documents of `rels` read as the stage reads them, and the C# graph built."""
    project = folder / "shop"
    for rel, text in SOURCES.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = folder / "manifest.sqlite"
    done = subprocess.run([sys.executable, "-I", "snapshot.py", "write", str(project), "--out", str(manifest),
                           "--no-engine", "--no-index", "--no-modules"], cwd=SCRIPTS, capture_output=True, text=True,
                          timeout=300)
    assert done.returncode == 0, done.stderr
    (folder / "index.scip").write_bytes(b"".join(_document(rel) for rel in rels))
    with code_graph.Snapshot(manifest) as snapshot:
        index = code_graph.Index(snapshot.root)
        index.load(folder / "index.scip")
        hops, traversal, prepared = code_graph.adapter_traversal(csharp, index, snapshot)
        absent = sorted(rel for rel in SOURCES if rel not in index.documents)
        graph, references = code_graph.build(
            index, snapshot, "csharp", hops, {}, csharp.missing(index, absent, csharp.tasks(configs)), traversal,
            static=csharp.static(index), refine=lambda read, built: csharp.refine(read, built, csharp.tasks(configs)))
        lines = {identity: f"{snapshot.checkout.get(rel, rel)}:{line}" for identity, rel, line in
                 snapshot.connection.execute("SELECT id, file, l0 FROM sem_declarations")}
    return {"index": index, "graph": graph, "prepared": prepared, "lines": lines,
            "references": {f"{row['site']} {row['name']}": row for row in references.values()}}


@pytest.fixture(scope="module")
def shop(tmp_path_factory):
    """Every document, `src/Api/Program.cs` twice: a project in two solutions comes back from both runs."""
    return _graph(tmp_path_factory.mktemp("csharp"), [*SOURCES, "src/Api/Program.cs"])


def _edges(data: dict, site: str, symbol: str) -> list[dict]:
    return [edge for edge in data["graph"]["edges"] if edge["site"] == site and edge["symbol"] == symbol]


def _ends(data: dict, reference: str) -> set[tuple]:
    """`(class, where the snapshot declares the end or its symbol, chain)` of each end of a snapshot reference."""
    row = data["references"][reference]
    return {(end.cls, data["lines"].get(end.target) or end.key.removeprefix(C), end.chain) for end in row["ends"]}


def test_prepare_keeps_each_occurrence_once_and_starts_edges_at_the_method_that_holds_them(shop):
    """scip-dotnet writes no enclosing range, and two runs that load one project both write its documents: the
    reader keeps each occurrence once and gives a definition the body the snapshot declares at its name."""
    assert shop["prepared"]["deduplicated"] == len(OCCURRENCES["src/Api/Program.cs"])
    occurrences = shop["index"].documents["src/Api/Program.cs"]
    assert len(occurrences) == len(set(occurrences))
    assert shop["prepared"]["enclosed"] > 0
    [edge] = _edges(shop, "src/Core/Order.cs:17", C + "Core/Pricing#Rate.")
    assert edge["from"] == C + "Core/Pricing#Price()."
    [edge] = _edges(shop, "src/Api/Program.cs:5", C + "Core/IPricing#Price().")[:1]
    assert edge["from"] == "src/Api/Program.cs"  # top-level statements: no declaration holds them


def test_a_namespace_is_a_namespace_not_a_project_symbol_without_a_definition(shop):
    """`namespace` and `using` lines reference each segment under the project's own package, never defined."""
    ends = {(edge["end"], edge["to"]) for edge in shop["graph"]["edges"] if edge["site"] == "src/Core/Order.cs:1"}
    assert ends == {("namespace", C + "Shop/"), ("namespace", C + "Core/")}
    assert not [edge for edge in shop["graph"]["edges"] if edge["to"].endswith("/") and edge["end"] != "namespace"]


def test_a_call_through_an_interface_reaches_the_implementations_the_index_states(shop):
    """`is_implementation` on a method names what it overrides and implements: the shared traversal follows it."""
    assert {(cls, where) for cls, where, _chain in _ends(shop, "src/Api/Program.cs:5 pricing.Price")} == {
        ("project-callable", "src/Core/Order.cs:7"), ("project-callable", "src/Core/Order.cs:15"),
        ("project-callable", "src/Core/Order.cs:24")}


def test_a_call_through_base_takes_no_override(shop):
    """`base.Price()` runs `Pricing.Price`, never `Discount.Price` that overrides it. The snapshot's names know
    `this` and not `base` (`languages/semantic.py`, `parts`): the reference is the call of `Price` at that line."""
    [reference] = [key for key, row in shop["references"].items()
                   if row["site"] == "src/Core/Order.cs:26" and row["kind"] == "call" and key.endswith(".Price")]
    assert _ends(shop, reference) == {("project-callable", "src/Core/Order.cs:15", ())}


def test_new_names_the_class(shop):
    """`new X(...)` is written at the type, never at a constructor: the end is the class, as a constructor's is."""
    assert _ends(shop, "src/Api/Program.cs:3 Discount") == {("project-callable", "src/Core/Order.cs:21", ())}
    assert _ends(shop, "src/Api/Program.cs:4 Order") == {("project-callable", "src/Core/Order.cs:3", ())}


def test_a_positional_property_of_a_record_leads_to_its_parameter(shop):
    """The index defines the record's parameter and references the property it declares, defined nowhere."""
    assert _ends(shop, "src/Core/Order.cs:17 order.Total") == {
        ("project-value", f"Core/Order#{CTOR}().(Total)", ("positional",))}
    assert not shop["references"]["src/Core/Order.cs:17 order.Total"]["hole"]


def test_the_value_of_a_setter_leads_to_its_property(shop):
    assert _ends(shop, "src/Core/Order.cs:13 value") == {("project-value", "Core/Pricing#Rate.", ("accessor-value",))}


def test_a_constructor_the_class_does_not_write_leads_to_the_class(shop):
    """An attribute references its constructor; one the class leaves implicit has no definition in the index."""
    [edge] = _edges(shop, "src/Core/Order.cs:30", C + f"Core/MarkerAttribute#{CTOR}().")
    assert (edge["end"], shop["lines"][edge["target"]], edge["chain"]) == (
        "project-callable", "src/Core/Order.cs:38", ["implicit-constructor"])


def test_a_first_overload_a_reduced_or_generic_call_may_stand_for_is_uncertain(shop):
    """scip-dotnet numbers an overload by comparing the called symbol with the type's members: a reduced extension
    call and a constructed generic call match none and are written as the first overload. Where a later overload
    is an extension or generic method, a reference to the first names every overload as a candidate."""
    overloads = [C + "Core/Extensions#Twice().", C + "Core/Extensions#Twice(+1)."]
    for site in ("src/Api/Program.cs:6", "src/Core/Order.cs:35"):
        [edge] = _edges(shop, site, overloads[0])
        assert shop["lines"][edge["target"]] == "src/Core/Order.cs:33"
        assert edge["uncertain"] == {"reason": "first overload of a reduced or generic call", "candidates": overloads}
    [exact] = _edges(shop, "src/Core/Order.cs:35", overloads[1])  # the static form carries its number
    assert shop["lines"][exact["target"]] == "src/Core/Order.cs:34" and "uncertain" not in exact


def test_two_declarations_under_one_symbol_are_uncertain_and_the_parts_of_one_are_not(shop, tmp_path):
    """A type's symbol holds the last segment of its namespace and no arity: `Shop.Core.Models.User` and
    `Shop.Api.Models.User` are one symbol. Every declaration is a candidate; the parts of one partial class are
    one declaration."""
    places = ["src/Api/Models/User.cs:3", "src/Core/Models/User.Greet.cs:3", "src/Core/Models/User.cs:3"]
    edges = _edges(shop, "src/Api/Program.cs:8", C + "Models/User#")
    assert sorted(shop["lines"][edge["target"]] for edge in edges) == places
    assert all(edge["uncertain"] == {"reason": "several declarations under one symbol", "candidates": places}
               for edge in edges)
    assert all("uncertain" not in edge for edge in _edges(shop, "src/Api/Program.cs:9", C + "Models/User#Greet()."))
    partial = _graph(tmp_path, [rel for rel in SOURCES if rel != "src/Api/Models/User.cs"])
    edges = _edges(partial, "src/Api/Program.cs:8", C + "Models/User#")
    assert sorted(partial["lines"][edge["target"]] for edge in edges) == places[1:]
    assert all("uncertain" not in edge for edge in edges)


def test_a_constructor_call_written_without_a_name_is_a_hole(shop):
    """`: base(...)`, `: this(...)` and `new(...)` call a constructor at no identifier: the index writes nothing
    there and the snapshot lists no reference, so the reader declares them."""
    holes = {(hole["site"], hole["name"], hole["class"], hole["reason"], hole.get("by"))
             for hole in shop["graph"]["holes"] if hole["class"] == "unnamed-constructor"}
    assert holes == {("src/Core/Order.cs:23", "base", "unnamed-constructor", "constructor initializer", "refine"),
                     ("src/Api/Program.cs:7", "new", "unnamed-constructor", "target-typed new", "refine")}


def test_every_reference_of_the_snapshot_ends_or_is_a_hole_the_index_explains(shop):
    """No dead end the index's own scheme causes is left: what remains unanswered is a generic or implicit name."""
    assert {hole["class"] for hole in shop["graph"]["holes"]} <= {"unnamed-constructor", "no-occurrence",
                                                                 "no-position"}
    assert not [edge for edge in shop["graph"]["edges"] if edge["end"] == "dead-end"]
    assert shop["graph"]["files"]["indexed"] == len(SOURCES) and not shop["graph"]["files"]["missing"]


def test_a_file_without_a_document_has_its_real_reason(tmp_path):
    """Per file: no project of the pre-map holds it; its project's run gave no document, with what scip-dotnet
    said; build output MSBuild's default items leave out; or a project indexed without it."""
    documents = [graph_tests.document(rel, []) for rel in ("src/Core/Order.cs",)]
    index = graph_tests.load(tmp_path, *documents)
    configs = {"units": [{"root": "src/Core", "manifest": "src/Core/Core.csproj", "solution": ""},
                         {"root": "src/Api", "manifest": "src/Api/Api.csproj", "solution": ""},
                         {"root": "tools/T", "manifest": "tools/T/T.csproj", "solution": None},
                         {"root": "old", "manifest": "old/Old.csproj", "solution": "old"}],
               "failed": {"tools/T/T.csproj": "exit code 134", "old": "no solution file in the folder of this workspace"},
               "unloaded": {"src/Api/Api.csproj": "Msbuild failed when processing the file '/work/src/Api/Api.csproj'"}}
    rels = ["scripts/Tool.cs", "src/Core/Legacy.cs", "src/Core/obj/Debug/X.g.cs", "src/Api/Program.cs",
            "tools/T/T.cs", "old/Old.cs"]
    reasons = csharp.missing(index, rels, csharp.tasks(configs))
    assert reasons["scripts/Tool.cs"] == "in no .NET project of the pre-map: no project compiles it"
    assert reasons["src/Core/Legacy.cs"] == (
        "its project src/Core/Core.csproj is indexed without it: no Compile item of the project as MSBuild evaluated "
        "it (removed, or left out by a condition or the target framework)")
    assert reasons["src/Core/obj/Debug/X.g.cs"] == (
        "under bin/ or obj/ of its project: MSBuild's default items leave build output out")
    assert reasons["src/Api/Program.cs"] == (
        "scip-dotnet gave no document of its project src/Api/Api.csproj: Msbuild failed when processing the file "
        "'/work/src/Api/Api.csproj'")
    assert reasons["tools/T/T.cs"] == "scip-dotnet gave no document of its project tools/T/T.csproj: exit code 134"
    assert reasons["old/Old.cs"] == ("scip-dotnet gave no document of its project old/Old.csproj: no solution file "
                                     "in the folder of this workspace")
    assert csharp.missing(index, ["src/Core/Legacy.cs"]) == {
        "src/Core/Legacy.cs": "in no .NET project of the pre-map: no project compiles it"}
