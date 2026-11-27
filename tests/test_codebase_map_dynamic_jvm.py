"""The dynamic step's observer for Java and Kotlin (`dynamic/jvm.py`) and its Java agent (`dynamic/jvm_record/`).

- The reader, the placing of sites and the join, on recorder files written by hand in the agent's format, over
  a snapshot of a small Java and Kotlin project: no JVM runs.
- The plan, from pre-map records written by hand.
- The observer through the container operation, against the fake Docker-compatible command line of
  `test_codebase_map_indexers_jvm.py`: what it sends, keeps and returns, and each gap with its cause.
- The agent itself on a real JDK, over a small Java program this file writes: it needs `javac` and `java` (17
  or newer) on the PATH, which `tests/modal_pytest.py`'s image holds, and ASM's jar, named by DAODAN_ASM_JAR or
  in Daodan's shared directory, where it is downloaded and verified as a real run does; without either it skips
  and says which.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import egress  # noqa: E402
import dynamic  # noqa: E402
import preparation  # noqa: E402
import resolve_edges  # noqa: E402
import snapshot  # noqa: E402
from dynamic import jvm  # noqa: E402
from test_codebase_map_container import tree_digest  # noqa: E402
from test_codebase_map_indexers_jvm import FakeEngineTest, digest, log  # noqa: E402

HEADER = {"java": "17.0.13", "root": "/work"}
PUBLIC, SYNTHETIC_BRIDGE, LAMBDA = 0x1, 0x1041, 0x100A  # the access flags javac gives a method, a bridge, a lambda


def recording(folder: Path, name: str, *rows) -> None:
    """One JVM's file as the agent writes it: the header, then a JSON line per fact (a string is written as is)."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("".join((row if isinstance(row, str) else json.dumps(row)) + "\n"
                                       for row in (HEADER, *rows)), encoding="utf-8")


def loaded(name: str, source: str, methods: list, sites: list, origin: str = "target/classes/", smap=None) -> dict:
    """The line the agent writes for a class it rewrote."""
    return {"class": name, "source": source, "from": origin, **({"smap": smap} if smap else {}),
            "methods": methods, "sites": sites}


# A Maven module of Java and Kotlin, as the join test snapshots it.
PROJECT = {
    "pom.xml": "<project><modelVersion>4.0.0</modelVersion><groupId>fx</groupId><artifactId>fx</artifactId>"
               "<version>1</version></project>\n",
    "src/main/java/fx/Circle.java": """package fx;

public class Circle {
    final double r;

    public Circle(double r) {
        this.r = r;
    }

    public double area() {
        return 3 * r * r;
    }
}
""",
    "src/main/java/fx/Main.java": """package fx;

public class Main {
    static double twice(Circle a, Circle b) {
        return a.area() + b.area();
    }

    public static void main(String[] args) {
        Circle c = new Circle(1);
        System.out.println("area " + c.area());
        twice(c, new Circle(2));
    }
}
""",
    "src/main/kotlin/fx/Discount.kt": """package fx

class Discount(val percent: Int) {
    fun applyTo(cents: Long): Long = cents - cents * percent / 100
}
""",
    "src/test/kotlin/fx/DiscountTest.kt": """package fx

import kotlin.test.Test

class DiscountTest {
    @Test
    fun applies() {
        val discount = Discount(10)
        discount.applyTo(1000)
        println(discount.percent)
    }
}
""",
}


def project_calls(folder: Path) -> None:
    """What the agent writes for `PROJECT`'s test and a run of `Main.main`: the classes, their sites, the calls."""
    recording(
        folder, "1-1.jsonl",
        loaded("fx/Circle", "Circle.java", [[1, "<init>", "(D)V", PUBLIC, 6], [2, "area", "()D", PUBLIC, 11]],
               [[1, 1, 6, "java/lang/Object", "<init>", "()V"]]),
        loaded("fx/Main", "Main.java",
               [[3, "twice", "(Lfx/Circle;Lfx/Circle;)D", 0x8, 5], [4, "main", "([Ljava/lang/String;)V", 0x9, 9]],
               [[2, 3, 5, "fx/Circle", "area", "()D"], [3, 3, 5, "fx/Circle", "area", "()D"],
                [4, 4, 9, "fx/Circle", "<init>", "(D)V"], [5, 4, 10, "java/io/PrintStream", "println",
                                                          "(Ljava/lang/String;)V"],
                [6, 4, 10, "fx/Circle", "area", "()D"], [7, 4, 11, "fx/Circle", "<init>", "(D)V"],
                [8, 4, 11, "fx/Main", "twice", "(Lfx/Circle;Lfx/Circle;)D"]]),
        loaded("fx/Discount", "Discount.kt",
               [[5, "<init>", "(I)V", PUBLIC, 3], [6, "getPercent", "()I", 0x11, 3], [7, "applyTo", "(J)J", 0x11, 4],
                [10, "applyTo$default", "(Lfx/Discount;JILjava/lang/Object;)J", 0x1009, 4]],
               [[13, 10, 4, "fx/Discount", "applyTo", "(J)J"]]),
        loaded("fx/DiscountTest", "DiscountTest.kt", [[8, "<init>", "()V", PUBLIC, 5], [9, "applies", "()V", 0x11, 8]],
               [[9, 9, 8, "fx/Discount", "<init>", "(I)V"],
                [10, 9, 9, "fx/Discount", "applyTo$default", "(Lfx/Discount;JILjava/lang/Object;)J"],
                [11, 9, 10, "fx/Discount", "getPercent", "()I"], [12, 9, 10, "java/io/PrintStream", "println",
                                                                  "(I)V"]],
               origin="target/test-classes/"),
        {"outside": 1}, {"call": [2, 2]}, {"call": [3, 2]}, {"call": [4, 1]}, {"outside": 5}, {"call": [6, 2]},
        {"call": [7, 1]}, {"call": [8, 3]}, {"call": [9, 5]}, {"call": [10, 10]}, {"call": [13, 7]},
        {"call": [11, 6]}, {"outside": 12})

PROGRAM = {
    "Shape.java": """package fx;

public interface Shape {
    double area();
}
""",
    "Circle.java": """package fx;

public class Circle implements Shape, Comparable<Circle> {
    static final double PI = Util.pi();
    final double r;

    public Circle(double r) {
        this.r = r;
    }

    public double area() {
        return PI * r * r;
    }

    public int compareTo(Circle other) {
        return Double.compare(r, other.r);
    }
}
""",
    "Square.java": """package fx;

public class Square implements Shape {
    public double area() {
        return 4;
    }
}
""",
    "Util.java": """package fx;

import java.util.function.DoubleUnaryOperator;

public class Util {
    static double pi() {
        return 3;
    }

    static double twice(DoubleUnaryOperator f, double x) {
        return f.applyAsDouble(f.applyAsDouble(x));
    }

    public static String hello(String who) {
        return "hello " + who;
    }

    static void fail() {
        throw new IllegalStateException("no");
    }
}
""",
    "Main.java": """package fx;

import java.util.ArrayList;
import java.util.List;

public class Main {
    static double total(List<Shape> shapes) {
        double sum = 0;
        for (Shape shape : shapes) {
            sum += shape.area();
        }
        return sum;
    }

    public static void main(String[] args) throws Exception {
        List<Shape> shapes = new ArrayList<>();
        shapes.add(new Circle(1));
        shapes.add(new Square());
        total(shapes);
        Util.twice(x -> x + 1, 2);
        shapes.forEach(shape -> shape.area());
        Util.class.getMethod("hello", String.class).invoke(null, "x");
        Runnable job = () -> Util.pi();
        new Thread(job).run();
        Comparable<Circle> first = new Circle(2);
        first.compareTo(new Circle(3));
        try {
            Util.fail();
        } catch (IllegalStateException expected) {
            Util.pi();
        }
    }
}
""",
}


def line_of(file: str, text: str) -> int:
    """The 1-based line of `text` in a file of `PROGRAM`."""
    return next(number for number, line in enumerate(PROGRAM[file].splitlines(), 1) if text in line)


def asm_jar() -> Path | None:
    """`jvm.ASM`, named by DAODAN_ASM_JAR, else in the shared directory, fetched there as `jvm.observe` does."""
    from engine_tools import MAVEN_CENTRAL, maven_central_dir
    given = Path(os.environ.get("DAODAN_ASM_JAR") or "")
    if given.is_file() and jvm.jvm.sha256(given) == jvm.ASM[1]:
        return given
    group, artifact, version = jvm.ASM[0].split(":")
    relative = f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.jar"
    try:
        return jvm.jvm.fetched(f"{MAVEN_CENTRAL}/{relative}", maven_central_dir() / relative, jvm.ASM[1])
    except container.Gap:
        return None


class AgentTest(unittest.TestCase):
    """The agent on a real JDK."""

    @classmethod
    def setUpClass(cls):
        if not shutil.which("javac") or not shutil.which("java"):
            raise unittest.SkipTest("no JDK on the PATH: the agent is compiled and run by javac and java")
        asm = asm_jar()
        if asm is None:
            raise unittest.SkipTest(f"{jvm.ASM[0]} is not named by DAODAN_ASM_JAR and could not be downloaded "
                                    "and verified into Daodan's shared directory")
        cls.scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-agent-"))
        cls.addClassCleanup(shutil.rmtree, cls.scratch, ignore_errors=True)
        agent, cls.root, cls.out = cls.scratch / "agent", cls.scratch / "project", cls.scratch / "calls"
        agent.mkdir()
        shutil.copyfile(asm, agent / "asm.jar")
        for command in jvm.agent_commands(str(jvm.RECORD), str(agent), os.pathsep):
            subprocess.run(command, check=True, capture_output=True)
        for name, text in PROGRAM.items():
            (cls.root / "src/fx").mkdir(parents=True, exist_ok=True)
            (cls.root / "src/fx" / name).write_text(text, encoding="utf-8")
        subprocess.run(["javac", "-d", str(cls.root / "classes"), *map(str, sorted((cls.root / "src/fx").iterdir()))],
                       check=True, capture_output=True)
        cls.ran = subprocess.run(
            ["java", f"-javaagent:{agent / 'agent.jar'}=out={cls.out},root={cls.root}", "-cp",
             str(cls.root / "classes"), "fx.Main"], capture_output=True, text=True)
        cls.observed = jvm.read(cls.out)

    def site(self, method: str, name: str, owner: str | None = None) -> dict:
        found = [site for site in self.observed["sites"] if site["method"] == method and site["name"] == name
                 and owner in (None, site["owner"])]
        self.assertEqual(len(found), 1, found)
        return found[0]

    def callees(self, *site) -> set[str]:
        return {f"{callee['class']}.{callee['name']}" for callee in self.site(*site)["callees"]}

    def test_the_program_runs_as_without_the_agent(self):
        self.assertEqual(self.ran.returncode, 0, self.ran.stderr)
        self.assertNotIn("DAODAN_RECORD_ERROR", self.ran.stderr)
        self.assertEqual(self.observed["skipped"], [])

    def test_a_site_has_its_file_and_line_and_every_implementation_that_ran(self):
        site = self.site("total", "area")
        self.assertEqual((site["package"], site["source"], site["line"], site["owner"]),
                         ("fx", "Main.java", line_of("Main.java", "sum += shape.area()"), "fx/Shape"))
        self.assertEqual(self.callees("total", "area"), {"fx/Circle.area", "fx/Square.area"})
        circle = next(callee for callee in site["callees"] if callee["class"] == "fx/Circle")
        self.assertEqual((circle["package"], circle["source"], circle["line"]),
                         ("fx", "Circle.java", line_of("Circle.java", "return PI * r * r")))
        self.assertFalse(site["outside"])

    def test_a_constructor_and_a_call_made_by_a_class_initializer(self):
        self.assertEqual(self.callees("main", "<init>", "fx/Square"), {"fx/Square.<init>"})
        self.assertEqual(self.callees("<clinit>", "pi"), {"fx/Util.pi"})
        # The first `new Circle` runs Circle's initializer before the constructor: the site still gets its callee.
        self.assertEqual({callee["class"] for site in self.observed["sites"]
                          if site["method"] == "main" and site["owner"] == "fx/Circle" and site["name"] == "<init>"
                          for callee in site["callees"]}, {"fx/Circle"})

    def test_a_lambda_is_the_callee_of_the_project_site_that_calls_its_interface_method(self):
        site = self.site("twice", "applyAsDouble")
        self.assertEqual([(callee["class"], callee["lambda"], callee["line"]) for callee in site["callees"]],
                         [("fx/Main", True, line_of("Main.java", "Util.twice(x -> x + 1, 2)"))])

    def test_a_call_that_leaves_the_project_is_outside_even_when_the_library_calls_back(self):
        for name, owner in (("forEach", "java/util/List"), ("run", "java/lang/Thread"),
                            ("getMethod", "java/lang/Class")):
            site = self.site("main", name, owner)
            self.assertTrue(site["outside"], name)
            self.assertEqual(site["callees"], [], name)
        # What the library called back still has its own sites.
        self.assertEqual(self.callees("lambda$main$1", "area"), {"fx/Circle.area", "fx/Square.area"})

    def test_a_reflective_call_names_the_method_it_ran(self):
        self.assertEqual(self.callees("main", "invoke"), {"fx/Util.hello"})

    def test_a_bridge_is_followed_to_the_method_it_forwards_to(self):
        site = self.site("main", "compareTo")
        self.assertEqual([(callee["class"], callee["desc"]) for callee in site["callees"]],
                         [("fx/Circle", "(Lfx/Circle;)I")])

    def test_a_call_that_throws_does_not_disturb_the_next(self):
        self.assertEqual(self.callees("main", "fail"), {"fx/Util.fail"})
        sites = [site for site in self.observed["sites"] if site["method"] == "main" and site["name"] == "pi"]
        self.assertEqual([[callee["class"] for callee in site["callees"]] for site in sites], [["fx/Util"]])


class ReaderTest(unittest.TestCase):
    """`jvm.read` on files written by hand."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="daodan-jvm-read-"))
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)

    def site(self, observed: dict, method: str, name: str) -> dict:
        [found] = [site for site in observed["sites"] if site["method"] == method and site["name"] == name]
        return found

    def test_a_site_takes_what_a_bridge_forwards_to_and_a_lambda_as_itself(self):
        circle = loaded("fx/Circle", "Circle.java",
                        [[1, "compareTo", "(Lfx/Circle;)I", PUBLIC, 15],
                         [2, "compareTo", "(Ljava/lang/Object;)I", SYNTHETIC_BRIDGE, 3]],
                        [[1, 2, 3, "fx/Circle", "compareTo", "(Lfx/Circle;)I"]])
        main = loaded("fx/Main", "Main.java",
                      [[3, "main", "([Ljava/lang/String;)V", 0x9, 9], [4, "lambda$main$0", "(D)D", LAMBDA, 10]],
                      [[2, 3, 10, "java/lang/Comparable", "compareTo", "(Ljava/lang/Object;)I"],
                       [3, 3, 11, "fx/Util", "twice", "(Ljava/util/function/DoubleUnaryOperator;D)D"],
                       [4, 3, 12, "java/io/PrintStream", "println", "(Ljava/lang/String;)V"],
                       [5, 3, 13, "fx/Shape", "area", "()D"]])
        recording(self.folder, "1-1.jsonl", circle, main, {"call": [2, 2]}, {"call": [1, 1]}, {"call": [3, 4]},
                  {"outside": 4}, '{"call": [5,')  # the last line, cut by a killed JVM
        recording(self.folder, "2-2.jsonl", main, circle, {"call": [2, 2]}, {"call": [1, 1]},
                  {"skipped": "fx/Big", "why": "java.lang.IllegalArgumentException: Unsupported class file"})
        observed = jvm.read(self.folder)
        self.assertEqual(observed["jvms"], 2)
        compare = self.site(observed, "main", "compareTo")
        self.assertEqual([(callee["class"], callee["desc"], callee["line"]) for callee in compare["callees"]],
                         [("fx/Circle", "(Lfx/Circle;)I", 15)])
        self.assertEqual((compare["source"], compare["line"], compare["from"]), ("Main.java", 10, "target/classes/"))
        twice = self.site(observed, "main", "twice")
        self.assertEqual([(callee["name"], callee["lambda"]) for callee in twice["callees"]], [("lambda$main$0", True)])
        printed = self.site(observed, "main", "println")
        self.assertTrue(printed["outside"])
        self.assertEqual(printed["callees"], [])
        self.assertNotIn("area", {site["name"] for site in observed["sites"]})  # a site that did not run
        self.assertEqual(observed["skipped"], [{"class": "fx/Big", "why": "java.lang.IllegalArgumentException: "
                                                                         "Unsupported class file"}])

    def test_the_lines_of_an_inlined_body_map_back_to_where_it_is_written(self):
        smap = "SMAP\nUse.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Use.kt\nfx/UseKt\n+ 2 Lib.kt\nfx/lib/LibKt\n*L\n1#1,10:1\n" \
               "3#2,2:11\n*E\n"
        recording(self.folder, "1-1.jsonl",
                  loaded("fx/UseKt", "Use.kt", [[1, "use", "()V", 0x19, 4]],
                         [[1, 1, 4, "fx/Util", "pi", "()D"], [2, 1, 12, "fx/Util", "pi", "()D"]], smap=smap),
                  loaded("fx/Util", "Util.java", [[2, "pi", "()D", 0x8, 7]], []),
                  {"call": [1, 2]}, {"call": [2, 2]})
        places = sorted((site["package"], site["source"], site["line"]) for site in jvm.read(self.folder)["sites"])
        self.assertEqual(places, [("fx", "Use.kt", 4), ("fx/lib", "Lib.kt", 4)])


class JoinTest(unittest.TestCase):
    """The sites placed from a recording of `PROJECT` and joined to its snapshot's references."""

    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp(prefix="daodan-jvm-join-"))
        cls.addClassCleanup(shutil.rmtree, cls.folder, ignore_errors=True)
        cls.project = cls.folder / "project"
        for rel, text in PROJECT.items():
            (cls.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (cls.project / rel).write_text(text, encoding="utf-8", newline="\n")
        cls.manifest = cls.folder / "out" / "manifest.sqlite"
        snapshot.read_project(cls.project, cls.manifest)
        project_calls(cls.folder / "calls")
        sources = [rel for rel in PROJECT if rel.endswith((".java", ".kt"))]
        cls.sites, cls.facts = jvm.place(jvm.read(cls.folder / "calls"), "", sources,
                                         lambda rel: (cls.project / rel).read_text(encoding="utf-8"))
        cls.rows = {}
        with code_graph.Snapshot(cls.manifest) as snap:
            names = dict(snap.connection.execute("SELECT id, name FROM sem_declarations"))
            for language in jvm.LANGUAGES:
                rows, _facts = dynamic.join(snap, language, cls.sites, [], jvm)
                for row in rows:
                    end = names.get(row["target_id"]) or (row["external"] or {}).get("package") or row["symbol"]
                    cls.rows.setdefault((row["file"], row["l0"]), set()).add((row["verdict"], end))

    def at(self, rel: str, line: int) -> set:
        return self.rows.get((rel, line), set())

    def test_a_call_reaches_the_declaration_of_the_method_that_ran(self):
        main = "src/main/java/fx/Main.java"
        self.assertEqual(self.at(main, 10), {("project-callable", "area"), ("external", "java.io")})
        self.assertEqual(self.at(main, 11), {("project-callable", "Circle"), ("project-callable", "twice")})
        test = "src/test/kotlin/fx/DiscountTest.kt"
        self.assertEqual(self.at(test, 9), {("project-callable", "applyTo")})  # through `applyTo$default`
        self.assertEqual(self.at(test, 8), {("project-callable", "Discount")})  # Kotlin's primary constructor

    def test_a_constructor_is_placed_on_the_new_and_not_on_the_type_beside_it(self):
        self.assertEqual(self.at("src/main/java/fx/Main.java", 9), {("project-callable", "Circle")})

    def test_a_kotlin_getter_is_placed_on_the_property_it_reads(self):
        ends = self.at("src/test/kotlin/fx/DiscountTest.kt", 10)
        self.assertIn(("external", "java.io"), ends)
        self.assertEqual({verdict for verdict, _end in ends}, {"project-value", "external"})

    def test_same_named_calls_on_one_line_are_ambiguous_and_said_so(self):
        self.assertEqual(self.at("src/main/java/fx/Main.java", 5), set())
        # Both calls are one site of the recording: the same method, line and callee.
        self.assertEqual(self.facts["ambiguous"], {"count": 1, "examples": ["src/main/java/fx/Main.java:5 area"]})

    def test_a_call_the_source_does_not_write_is_counted_and_not_placed(self):
        # Circle's super() and the call `applyTo$default` makes, which the compiler wrote.
        self.assertEqual(self.facts["unplaced"], {"no call of that name on its line": 2})
        self.assertEqual(self.facts["recorded"], len(self.sites) + 3)


class PlanTest(unittest.TestCase):
    """`jvm.plan` from pre-map records written by hand."""

    FILES = {"pom.xml": "", "src/main/java/fx/A.java": "package fx;\nclass A {}\n",
             "src/test/java/fx/ATest.java": "package fx;\n\nimport org.junit.jupiter.api.Test;\n\nclass ATest {}\n",
             "core/src/main/kotlin/fx/B.kt": "package fx\nclass B\n"}

    def plan(self, units: list[dict], files: dict | None = None) -> dict:
        files = self.FILES if files is None else files
        return jvm.plan({"units": units, "toolchains": [{"tool": "java", "version": "21", "declared_in": "pom.xml"}]},
                        sorted(files), lambda rel: files.get(rel, ""))

    def test_the_build_s_own_test_task_runs_where_a_test_file_imports_a_test_framework(self):
        planned = self.plan([{"kind": "maven-module", "root": ".", "name": "fx:fx"},
                             {"kind": "maven-module", "root": "core", "name": "fx:core"}])
        self.assertEqual(planned["runs"], [{"root": "", "tool": "maven", "argv": jvm.MAVEN_TEST}])
        self.assertEqual(planned["gaps"], [])
        self.assertEqual(planned["sources"], ["core/src/main/kotlin/fx/B.kt", "src/main/java/fx/A.java",
                                              "src/test/java/fx/ATest.java"])
        self.assertEqual(planned["toolchains"], [{"tool": "java", "version": "21", "declared_in": "pom.xml"}])
        gradle = self.plan([{"kind": "gradle-project", "root": ".", "name": ":"}])
        self.assertEqual(gradle["runs"], [{"root": "", "tool": "gradle", "argv": jvm.GRADLE_TEST}])
        self.assertIn("--offline", jvm.GRADLE_TEST)
        self.assertNotIn("test", jvm.GRADLE_TEST)  # the build's own Test tasks, read in the preparation
        self.assertIn("-o", jvm.MAVEN_TEST)
        both = self.plan([{"kind": "maven-module", "root": ".", "name": "fx:fx"},
                          {"kind": "gradle-project", "root": ".", "name": ":"}])
        self.assertEqual([(run["root"], run["tool"]) for run in both["runs"]], [("", "gradle"), ("", "maven")])

    def test_a_build_with_no_test_file_is_a_gap_and_does_not_run(self):
        files = {rel: text for rel, text in self.FILES.items() if "Test" not in rel}
        planned = self.plan([{"kind": "gradle-project", "root": ".", "name": ":"}], files)
        self.assertEqual(planned["runs"], [])
        self.assertEqual([(gap["kind"], gap["path"]) for gap in planned["gaps"]], [("no_tests", "")])

    def test_without_a_gradle_or_maven_build_nothing_runs_and_the_gap_says_why(self):
        planned = self.plan([{"kind": "sbt-project", "root": ".", "name": "fx"}])
        self.assertEqual(planned["runs"], [])
        [gap] = planned["gaps"]
        self.assertEqual(gap["kind"], "no_tests")
        self.assertIn("sbt", gap["detail"])

    def test_a_maven_build_beside_a_gradle_one_does_not_run_on_the_jdk_of_the_gradle_daemon_file(self):
        """`gradle-daemon-jvm.properties` is the JDK Gradle's daemon runs on: no other tool's build takes it."""
        daemon = {"tool": "java", "version": "21", "vendor": "JETBRAINS",
                  "declared_in": "gradle/gradle-daemon-jvm.properties#toolchainVersion"}
        pom = {"tool": "java", "version": "17", "declared_in": "pom.xml#properties.maven.compiler.release"}
        self.assertIsNone(jvm.jvm.build_jdk({"root": "", "tool": "maven"}, [daemon, pom]))
        self.assertEqual(jvm.jvm.build_jdk({"root": "", "tool": "gradle"}, [daemon, pom])["vendor"], "JETBRAINS")

    def test_a_maven_build_runs_on_the_jdk_its_poms_state_and_a_gradle_one_on_the_image_s(self):
        """Maven compiles with the JDK that runs it, and a compiler plugin of a pom's time may not read a newer
        JDK's classes (Error Prone's own javac 9): a build its poms declare for an older level runs on that JDK.
        `--release` needs javac 9 or later, which the image's is; Gradle runs on the image's JDK and finds the
        toolchain its scripts ask for; a JDK above the image's is installed as for the analyzer."""
        maven, gradle = {"root": "", "tool": "maven"}, {"root": "", "tool": "gradle"}
        java8 = [{"tool": "java", "version": "1.8", "declared_in": "pom.xml#properties.java.version"},
                 {"tool": "java", "version": "1.8", "declared_in": "core/pom.xml#maven-compiler-plugin.target"}]
        self.assertEqual(jvm.jvm.build_jdk(maven, java8)["version"], "8")
        self.assertIsNone(jvm.jvm.build_jdk(gradle, java8))
        release = [{"tool": "java", "version": "8", "declared_in": "pom.xml#properties.maven.compiler.release"}]
        self.assertIsNone(jvm.jvm.build_jdk(maven, [*java8, *release]))
        old = [{"tool": "java", "version": "1.6", "declared_in": "pom.xml#maven-compiler-plugin.source"}]
        self.assertEqual(jvm.jvm.build_jdk(maven, old)["version"], "8")  # the oldest JDK Temurin builds
        self.assertEqual(jvm.jvm.build_jdk(maven, old)["stated"], "1.6")
        # Gradle runs on the image's JDK, which compiles no level under 8: the preparation raises it and says so.
        low = [{"tool": "java", "version": "1.6", "declared_in": "build.gradle#java.sourceCompatibility"}]
        self.assertEqual(jvm.jvm.raise_line(low, "", 8, "levels"), "export DAODAN_RAISE=levels\n")
        self.assertEqual(jvm.jvm.raise_line(java8, "", 8, "levels"), "")
        self.assertEqual(jvm.jvm.raise_line(low, "app", 8, "levels"), "")  # another build's script
        prepare = jvm.scripts({**gradle, "argv": jvm.GRADLE_TEST})[0]
        # The build compiles as declared first; only when that fails, a second time with the levels raised.
        self.assertLess(prepare.index("step compile"), prepare.index("raise_levels"))
        self.assertLess(prepare.index("raise_levels"), prepare.rindex("step compile"))
        self.assertNotIn("raise_levels", jvm.scripts({**maven, "argv": jvm.MAVEN_TEST})[0])
        steps = [{"step": "compile", "build_raised": ["the root project: source 1.6 and target 1.6 -> 8"]}]
        gap = jvm.jvm.edited(steps, "", "does not compile on the JDK it runs on", "its tests ran on a build")[0]
        self.assertEqual(gap["detail"], "the build as declared does not compile on the JDK it runs on: its tests ran "
                         "on a build, with the root project: source 1.6 and target 1.6 -> 8")
        newer = [*java8, {"tool": "java", "version": "21", "declared_in": ".java-version"}]
        self.assertEqual(jvm.jvm.build_jdk(maven, newer)["version"], "21")
        self.assertIsNone(jvm.jvm.build_jdk({"root": "app", "tool": "maven"}, java8))  # another build's poms
        self.assertIsNone(jvm.jvm.build_jdk(maven, [{"tool": "android", "version": "35", "declared_in": "pom.xml#x"}]))
        # A JDK above the image's states for its own build and those below its file, never for another build
        # (opentelemetry-demo: the ad service's 21 is not fraud-detection's, whose CI builds on 17).
        fraud = {"root": "src/fraud", "tool": "gradle"}
        ad = {"tool": "java", "version": "21", "declared_in": "src/ad/build.gradle#sourceCompatibility"}
        self.assertIsNone(jvm.jvm.build_jdk(fraud, [ad]))
        for declared_in in ("src/fraud/build.gradle#sourceCompatibility", ".java-version", "src/.tool-versions"):
            self.assertEqual(jvm.jvm.build_jdk(fraud, [ad, {**ad, "declared_in": declared_in}])["version"], "21")

    def test_the_agent_is_built_for_java_8_and_its_jdk_9_and_10_parts_load_only_there(self):
        commands = jvm.agent_commands("src", "out", bin="/jdk/bin/")
        releases = {command[-1].rsplit("/", 1)[-1]: command[command.index("--release") + 1]
                    for command in commands if "--release" in command}
        self.assertEqual(releases, {"Recorder.java": "8", "Walker.java": "10", "Agent.java": "8", "Modular.java": "9"})
        self.assertEqual(jvm.RELEASE, 8)
        self.assertTrue(all(command[0].startswith("/jdk/bin/") for command in commands))
        for name, later in (("Recorder.java", ("StackWalker", "ProcessHandle")),
                            ("Agent.java", ("List.of(", "Module"))):  # JDK 9 and 10 API, apart in their classes
            text = (jvm.RECORD / name).read_text(encoding="utf-8")
            self.assertEqual([api for api in later if api in text], [], name)
        # A JDK after 21 gives a frame's descriptor only to a walker that retains class references.
        self.assertIn("StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE)",
                      (jvm.RECORD / "Walker.java").read_text(encoding="utf-8"))

    def test_the_observer_declares_itself_for_java_and_kotlin(self):
        self.assertIn(jvm, dynamic.observers())
        self.assertEqual(jvm.LANGUAGES, ("java", "kotlin"))
        self.assertEqual(dynamic.resolver(jvm), f"{jvm.NAME}@{jvm.VERSION}")


ASM_JAR = b"the asm jar"


class ObserveTest(FakeEngineTest):
    """The observer through the container operation: the fake plays each phase."""

    def setUp(self):
        super().setUp()
        shutil.rmtree(self.project)
        for rel, text in PROJECT.items():
            (self.project / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.project / rel).write_text(text, encoding="utf-8", newline="\n")
        patcher = mock.patch.object(jvm, "ASM", ("fx.test:asm:1.0", digest(ASM_JAR)))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.served[f"{resolve_edges.MAVEN_CENTRAL}/fx/test/asm/1.0/asm-1.0.jar"] = ASM_JAR
        files = {rel: (self.project / rel).read_text(encoding="utf-8") for rel in PROJECT}
        self.planned = jvm.plan({"units": [{"kind": "maven-module", "root": ".", "name": "fx:fx"}]}, sorted(files),
                                files.get)

    def observe(self, *, code: str | None = "0", suites: str = "", calls: bool = True, text: str = "",
                prepared: int = 0, memory: int = 64 * 2**30) -> dict:
        shutil.rmtree(self.state / "play", ignore_errors=True)
        (self.state / "play").mkdir()
        self.play("prepare", text=log(("agent", 0, ""), ("compile", prepared, "[INFO] BUILD"), ("providers", 1, "")),
                  code=prepared)
        out = jvm.jvm.OUT.lstrip("/")
        files = {f"{out}/tests.log": text, f"{out}/suites.txt": suites}
        if code is not None:
            files[f"{out}/tests.code"] = code + "\n"
        if calls:
            project_calls(self.scratch / "played")
            files[f"{out}/calls"] = self.scratch / "played"
        self.play("execute", files=files, text=log(("tests", 0, "")))
        with mock.patch.object(container, "free_memory", return_value=memory):
            return jvm.observe(self.project, self.planned, self.work, self.engine)

    def suite(self, tests: int, failures: int = 0, errors: int = 0) -> str:
        return f'<testsuite name="fx.T" tests="{tests}" skipped="0" failures="{failures}" errors="{errors}">\n'

    def gaps(self, result: dict) -> list[str]:
        return [gap["kind"] for gap in result["gaps"]]

    def test_the_tests_run_only_in_the_container_with_the_agent_and_no_network(self):
        before = tree_digest(self.project)
        result = self.observe(suites=self.suite(2))
        self.assertEqual(result["state"], "ran")
        self.assertEqual(result["runs"], [{"root": "", "runner": "maven", "state": "ran", "tool": "maven",
                                           "argv": jvm.MAVEN_TEST, "exit_code": 0, "tests": 2, "failures": 0,
                                           "errors": 0, "skipped": 0, "jvms": 1}])
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual(self.gaps(result), ["sites_ambiguous"])
        placed = {(site["file"], site["line"], site["name"]) for site in result["sites"]}
        self.assertIn(("src/main/java/fx/Main.java", 9, "area"), placed)  # the site's line, from 0
        self.assertEqual(tree_digest(self.project), before)  # the project is not changed
        prepare = (self.state / "scripts" / "prepare.sh").read_text(encoding="utf-8")
        execute = (self.state / "scripts" / "execute.sh").read_text(encoding="utf-8")
        self.assertIn(f"javac --release {jvm.RELEASE}", prepare)
        self.assertIn("mvn -B test-compile", prepare)
        self.assertIn("-Djvm=", prepare)  # Surefire's provider is resolved where the registries are
        self.assertNotIn("javaagent", prepare)
        self.assertIn(f"-javaagent:{jvm.AGENT}/agent.jar=out=$OUT/calls,root=$WORK", execute)
        self.assertIn("export JAVA_TOOL_OPTIONS", execute)
        self.assertIn(" ".join(jvm.MAVEN_TEST), execute)
        arrived = self.arrived() / jvm.AGENT.lstrip("/")
        self.assertEqual((arrived / "asm.jar").read_bytes(), ASM_JAR)
        self.assertEqual(sorted(path.name for path in arrived.iterdir()),
                         ["Agent.java", "MANIFEST.MF", "Modular.java", "Recorder.java", "Walker.java", "asm.jar",
                          "tests.gradle"])
        execution = self.created()[2]
        self.assertEqual(execution[execution.index("--network") + 1], "none")

    def test_what_the_copy_of_the_project_left_out_is_a_gap_of_the_run(self):
        """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`)."""
        left = {"kind": "link_outside", "path": "x.java", "target": "../y.java", "detail": "x.java links outside"}
        copied = container.copy_perimeter
        with mock.patch.object(container, "copy_perimeter", lambda *given: {**copied(*given), "gaps": [left]}):
            self.assertIn(left, self.observe(suites=self.suite(2))["gaps"])

    def test_each_way_the_tests_end_is_a_gap_with_its_cause(self):
        cases = [({"code": "1", "suites": self.suite(3, failures=1)}, "ran", ["tests_failed"]),
                 ({"code": "0", "suites": self.suite(3, errors=2)}, "ran", ["tests_failed"]),  # Maven ignores them
                 ({"code": "124", "suites": self.suite(1)}, "timeout", ["tests_timeout"]),
                 ({"code": "137", "suites": self.suite(1)}, "killed", ["tests_killed"]),
                 ({"code": None}, "not_started", ["tests_not_started"]),
                 ({"code": "1", "text": "[ERROR] BUILD FAILURE"}, "not_started", ["tests_not_started"]),
                 ({"code": "1", "suites": self.suite(2)}, "ran", ["tests_not_started"]),  # another module's
                 ({"code": "0"}, "no_tests", ["no_tests"]),
                 ({"code": "0", "suites": self.suite(2), "calls": False}, "ran", ["not_observed"])]
        for options, state, kinds in cases:
            with self.subTest(**{key: value for key, value in options.items() if key != "suites"}):
                result = self.observe(**options)
                self.assertEqual(result["state"], "ran")
                self.assertIsNone(dynamic.malformed(result))
                self.assertEqual([run["state"] for run in result["runs"]], [state])
                self.assertEqual([kind for kind in self.gaps(result) if kind != "sites_ambiguous"], kinds)
        failed = self.observe(code="1", text="[ERROR] BUILD FAILURE\nCould not resolve dependencies")
        [gap] = [gap for gap in failed["gaps"] if gap["kind"] == "tests_not_started"]
        self.assertIn("Could not resolve dependencies", gap["detail"])

    def test_under_gradle_the_tests_are_the_build_s_own_test_tasks_read_and_resolved_in_the_preparation(self):
        """Gradle names its Test tasks only once it has configured the build (`jvmTest` in Kotlin Multiplatform,
        where no `test` exists): the preparation's init script compiles their classes, resolves their classpath
        where the registries are and writes their paths, which the execution runs offline."""
        files = {rel: (self.project / rel).read_text(encoding="utf-8") for rel in PROJECT}
        self.planned = jvm.plan({"units": [{"kind": "gradle-project", "root": ".", "name": ":"}]}, sorted(files),
                                files.get)
        out = jvm.jvm.OUT.lstrip("/")
        self.play("prepare", text=log(("agent", 0, ""), ("compile", 0, "BUILD SUCCESSFUL")))
        project_calls(self.scratch / "played")
        self.play("execute", files={f"{out}/tests.code": "0\n", f"{out}/suites.txt": self.suite(2),
                                    f"{out}/test-tasks.txt": ":jvmTest\n:core:test\n",
                                    f"{out}/calls": self.scratch / "played"}, text=log(("tests", 0, "")))
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = jvm.observe(self.project, self.planned, self.work, self.engine)
        self.assertEqual([(run["runner"], run["state"], run["argv"]) for run in result["runs"]],
                         [("gradle", "ran", [*jvm.GRADLE_TEST, ":core:test", ":jvmTest"])])
        prepare = (self.state / "scripts" / "prepare.sh").read_text(encoding="utf-8")
        execute = (self.state / "scripts" / "execute.sh").read_text(encoding="utf-8")
        self.assertIn(f'DAODAN_TESTS="$OUT/test-tasks.txt" gradle --no-daemon --console=plain --init-script '
                      f'{jvm.AGENT}/tests.gradle daodanTests', prepare)
        self.assertIn('$(sort -u "$OUT/test-tasks.txt")', execute)
        self.assertIn("tests.gradle", [path.name for path in (self.arrived() / jvm.AGENT.lstrip("/")).iterdir()])
        script = (jvm.RECORD / "tests.gradle").read_text(encoding="utf-8")
        for needed in ("withType(Test)", "findByName('test')", "classpath", "DAODAN_TESTS"):
            self.assertIn(needed, script)

    def test_under_gradle_the_tests_run_on_the_toolchain_the_scripts_ask_for_with_gradle_on_the_image_s_jdk(self):
        """Gradle 9 runs on JDK 17 or newer and compiles and tests on the toolchain its scripts ask for (11 here),
        which the preparation installs and hands it (`org.gradle.java.installations.paths`): the agent, of Java 8's
        class files, loads in that test JVM, and scip-java's limit is none of the observer's."""
        self.served[preparation.MISE[0]] = b"mise"
        patcher = mock.patch.object(preparation, "MISE", (preparation.MISE[0], digest(b"mise"), "mise"))
        patcher.start()
        self.addCleanup(patcher.stop)
        files = {rel: (self.project / rel).read_text(encoding="utf-8") for rel in PROJECT}
        self.planned = jvm.plan({"units": [{"kind": "gradle-project", "root": ".", "name": ":"}]}, sorted(files),
                                files.get)
        self.planned["toolchains"] = [{"tool": "java", "version": "11",
                                       "declared_in": "build.gradle.kts#java.toolchain.languageVersion"}]
        out = jvm.jvm.OUT.lstrip("/")
        self.play("prepare", text=log(("agent", 0, ""), ("compile", 0, "BUILD SUCCESSFUL")))
        project_calls(self.scratch / "played")
        self.play("execute", files={f"{out}/tests.code": "0\n", f"{out}/suites.txt": self.suite(2),
                                    f"{out}/test-tasks.txt": ":test\n", f"{out}/calls": self.scratch / "played"},
                  text=log(("tests", 0, "")))
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30):
            result = jvm.observe(self.project, self.planned, self.work, self.engine)
        self.assertEqual(result["state"], "ran")
        self.assertNotIn("jdk_unsupported", self.gaps(result))
        for phase in ("prepare", "execute"):
            script = (self.state / "scripts" / f"{phase}.sh").read_text(encoding="utf-8")
            self.assertIn("\nDAODAN_JDK=17\n", script)
            self.assertIn("org.gradle.java.installations.%s", script)
        self.assertIn("install java@11", (self.state / "scripts" / "prepare.sh").read_text(encoding="utf-8"))

    def test_a_folder_two_builds_build_runs_its_tests_once(self):
        """Gradle and Maven building one folder run the same tests: Maven's run only when Gradle's did not."""
        files = {rel: (self.project / rel).read_text(encoding="utf-8") for rel in PROJECT}
        self.planned = jvm.plan({"units": [{"kind": "gradle-project", "root": ".", "name": ":"},
                                           {"kind": "maven-module", "root": ".", "name": "fx:fx"}]},
                                sorted(files), files.get)
        run, seen = jvm.jvm.run, []

        def gradle_fails(project_dir, work_dir, prepare, *args, **kwargs):
            seen.append("gradle" if "daodanTests" in prepare else "maven")
            if seen[-1] == "gradle":
                return {"state": "failed", "cause": "no JDK 23"}, [], self.work
            return run(project_dir, work_dir, prepare, *args, **kwargs)

        with mock.patch.object(jvm.jvm, "run", side_effect=gradle_fails):
            result = self.observe(suites=self.suite(2))
        self.assertEqual(seen, ["gradle", "maven"])
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual([(item["runner"], item["state"]) for item in result["runs"]], [("maven", "ran")])
        self.assertEqual(result["equivalent_completed"], [0])
        self.assertNotIn("tests_not_started", self.gaps(result))  # the folder's tests ran
        seen.clear()
        with mock.patch.object(jvm.jvm, "run", side_effect=lambda *args, **kwargs: (seen.append(1),
                                                                                  run(*args, **kwargs))[1]):
            result = self.observe(suites=self.suite(2))
        self.assertEqual(seen, [1])  # Gradle's tests ran: Maven's are not run again
        self.assertEqual([item["runner"] for item in result["runs"]], ["gradle"])

    def test_a_build_that_stops_beside_one_that_ran_is_a_run_that_did_not_start(self):
        self.planned["runs"].append({**self.planned["runs"][0], "root": "sub"})
        run = jvm.jvm.run

        def stopping(project_dir, *args, **kwargs):
            if Path(project_dir).name == "sub":
                return {"state": "failed", "cause": "the build failed"}, [], self.work
            return run(project_dir, *args, **kwargs)

        with mock.patch.object(jvm.jvm, "run", side_effect=stopping):
            result = self.observe(suites=self.suite(2))
        self.assertIsNone(dynamic.malformed(result))
        self.assertEqual([(item["root"], item["runner"], item["state"]) for item in result["runs"]],
                         [("", "maven", "ran"), ("sub", "maven", "not_started")])
        [gap] = [gap for gap in result["gaps"] if gap["kind"] == "tests_not_started"]
        self.assertEqual(gap["path"], "sub")

    def test_a_class_the_agent_could_not_rewrite_is_a_gap(self):
        project_calls(self.scratch / "played")
        recording(self.scratch / "played", "2-2.jsonl", {"skipped": "fx/Big", "why": "too big"})
        result = self.observe(suites=self.suite(1))
        [gap] = [gap for gap in result["gaps"] if gap["kind"] == "classes_unrecorded"]
        self.assertIn("fx/Big", gap["detail"])

    def test_a_preparation_that_fails_is_failed_with_its_cause(self):
        result = self.observe(prepared=1)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["sites"], [])
        self.assertIn("BUILD", result["cause"])

    def test_a_build_s_tests_run_in_its_folder_of_a_copy_of_the_checkout(self):
        files = {rel: (self.project / rel).read_text(encoding="utf-8") for rel in PROJECT}
        shutil.copytree(self.project, self.scratch / "app")
        shutil.move(str(self.scratch / "app"), str(self.project / "app"))
        self.planned = jvm.plan({"units": [{"kind": "maven-module", "root": "app", "name": "fx:fx"}]},
                                sorted(f"app/{rel}" for rel in files), lambda rel: files.get(rel.removeprefix("app/")))
        self.observe(suites=self.suite(1))
        for phase in ("prepare", "execute"):
            self.assertIn("\nDAODAN_ROOT=app\n", (self.state / "scripts" / f"{phase}.sh").read_text(encoding="utf-8"))
        self.assertTrue((self.arrived(1) / "work/app/pom.xml").is_file())

    def test_without_a_container_nothing_runs_and_the_cause_is_said(self):
        result = self.observe(memory=2**20)
        self.assertEqual(result["state"], "gap")
        self.assertIn("memory", result["cause"])
        self.assertEqual(self.created(), [])

    def test_a_java_8_maven_build_runs_on_jdk_8_with_the_agent_the_image_s_jdk_builds(self):
        tool = b"mise"
        self.served[preparation.MISE[0]] = tool
        patcher = mock.patch.object(preparation, "MISE", (preparation.MISE[0], digest(tool), "mise"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.planned["toolchains"] = [{"tool": "java", "version": "1.8",
                                       "declared_in": "pom.xml#maven-compiler-plugin.source"}]
        result = self.observe(suites=self.suite(2))
        self.assertEqual(result["state"], "ran")
        prepare = (self.state / "scripts" / "prepare.sh").read_text(encoding="utf-8")
        execute = (self.state / "scripts" / "execute.sh").read_text(encoding="utf-8")
        self.assertIn("install java@8", prepare)
        for script in (prepare, execute):
            self.assertIn("\nDAODAN_JDK=8\n", script)  # the head takes the JDK mise installed
        self.assertIn(f"{jvm.IMAGE_JDK}javac --release {jvm.RELEASE}", prepare)
        self.assertIn("api.adoptium.net", self.created()[0])  # mise's downloads, through the preparation's proxy

    def test_the_hosts_the_project_declares_are_reached_by_the_preparation(self):
        egress.respond("jitpack.io", str(self.project), "once")  # approved for this analysis: it opens only then
        self.planned["declared"] = {"hosts": ("jitpack.io",), "where": {"jitpack.io": ["pom.xml"]}}
        self.observe(suites=self.suite(1))
        self.assertIn("jitpack.io", self.created()[0])

    def test_an_asm_jar_that_does_not_match_its_checksum_starts_no_container(self):
        self.served[f"{resolve_edges.MAVEN_CENTRAL}/fx/test/asm/1.0/asm-1.0.jar"] = b"another jar"
        result = self.observe()
        self.assertEqual(result["state"], "gap")
        self.assertIn("asm", result["cause"])
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
