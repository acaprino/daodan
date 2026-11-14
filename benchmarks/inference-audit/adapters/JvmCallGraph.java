// The call graph of compiled JVM classes with WALA, for adapters/jvm_callgraph.py: CHA and RTA.
//
// Settings file, one entry per line: `dir <class directory>` (the project's classes, repeatable),
// `jar <library jar>` (repeatable), `exclusions <file>`, `out <json lines file>`.
// Entry points are every concrete method of the project's classes, called without allocating anything:
// the receiver and the arguments are fresh values and an instance method is called by special dispatch, so
// RTA counts as instantiated only the classes some reachable `new` creates (WALA's default entry points
// allocate every receiver and parameter type). A second RTA, `rtat`, also lets the test runner create each
// concrete class with a `@Test` annotation on it, on a method or on a superclass. CHA keeps project targets only; RTA also walks the JDK and
// the jars. Lambdas and method references go through WALA's lambda summaries (LambdaMethodTargetSelector).
//
// Output records: class, method, call (per algorithm, caller and call site), trampoline (the summary
// method of a lambda and what it calls), instantiated (RTA), engine (times and sizes).
import com.ibm.wala.classLoader.BinaryDirectoryTreeModule;
import com.ibm.wala.classLoader.CallSiteReference;
import com.ibm.wala.classLoader.IBytecodeMethod;
import com.ibm.wala.classLoader.IClass;
import com.ibm.wala.classLoader.IMethod;
import com.ibm.wala.classLoader.NewSiteReference;
import com.ibm.wala.classLoader.ShrikeClass;
import com.ibm.wala.types.annotations.Annotation;
import com.ibm.wala.shrike.shrikeCT.ClassReader;
import com.ibm.wala.shrike.shrikeCT.SourceFileReader;
import com.ibm.wala.ssa.SSANewInstruction;
import java.util.HashSet;
import java.util.Set;
import com.ibm.wala.core.util.config.AnalysisScopeReader;
import com.ibm.wala.ipa.callgraph.AnalysisCacheImpl;
import com.ibm.wala.ipa.callgraph.AnalysisOptions;
import com.ibm.wala.ipa.callgraph.AnalysisScope;
import com.ibm.wala.ipa.callgraph.CGNode;
import com.ibm.wala.ipa.callgraph.CallGraph;
import com.ibm.wala.ipa.callgraph.Entrypoint;
import com.ibm.wala.ipa.callgraph.IAnalysisCacheView;
import com.ibm.wala.ipa.callgraph.cha.CHACallGraph;
import com.ibm.wala.ipa.callgraph.impl.AbstractRootMethod;
import com.ibm.wala.ipa.callgraph.impl.DefaultEntrypoint;
import com.ibm.wala.ipa.callgraph.impl.Util;
import com.ibm.wala.ipa.cha.ClassHierarchyFactory;
import com.ibm.wala.ipa.cha.IClassHierarchy;
import com.ibm.wala.shrike.shrikeBT.IInvokeInstruction;
import com.ibm.wala.shrike.shrikeCT.BootstrapMethodsReader.BootstrapMethod;
import com.ibm.wala.shrike.shrikeCT.ConstantPoolParser;
import com.ibm.wala.ssa.IR;
import com.ibm.wala.ssa.SSAAbstractInvokeInstruction;
import com.ibm.wala.ssa.SSAInvokeDynamicInstruction;
import com.ibm.wala.types.ClassLoaderReference;
import com.ibm.wala.types.MethodReference;
import java.io.BufferedWriter;
import java.io.File;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.jar.JarFile;
import java.util.stream.Stream;

public final class JvmCallGraph {

  /**
   * An entry point that calls exactly its method and allocates nothing, or, with `runner`, only its receiver:
   * the test runner creating the test class.
   */
  static final class Entry extends DefaultEntrypoint {
    private final boolean runner;

    Entry(IMethod method, IClassHierarchy cha, boolean runner) {
      super(method, cha);
      this.runner = runner;
    }

    @Override
    public CallSiteReference makeSite(int programCounter) {
      if (method.isStatic()) {
        return super.makeSite(programCounter);
      }
      return CallSiteReference.make(
          programCounter, method.getReference(), IInvokeInstruction.Dispatch.SPECIAL);
    }

    @Override
    protected int makeArgument(AbstractRootMethod m, int i) {
      if (runner && i == 0 && !method.isStatic()) {
        SSANewInstruction allocation = m.addAllocation(method.getDeclaringClass().getReference());
        if (allocation != null) return allocation.getDef();
      }
      return m.addLocal();
    }
  }

  private static BufferedWriter out;
  private static final Map<String, String> classDirs = new LinkedHashMap<>();

  static String q(String s) {
    if (s == null) return "null";
    StringBuilder b = new StringBuilder("\"");
    for (char c : s.toCharArray()) {
      switch (c) {
        case '"' -> b.append("\\\"");
        case '\\' -> b.append("\\\\");
        case '\n' -> b.append("\\n");
        case '\r' -> b.append("\\r");
        case '\t' -> b.append("\\t");
        default -> {
          if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
          else b.append(c);
        }
      }
    }
    return b.append('"').toString();
  }

  static String list(Iterable<String> items) {
    StringBuilder b = new StringBuilder("[");
    for (String item : items) {
      if (b.length() > 1) b.append(',');
      b.append(q(item));
    }
    return b.append(']').toString();
  }

  static void emit(String json) throws Exception {
    out.write(json);
    out.write('\n');
  }

  static String sig(MethodReference ref) {
    return ref.getDeclaringClass().getName().toString().substring(1)
        + "." + ref.getName() + ref.getDescriptor();
  }

  static String className(IClass klass) {
    return klass.getName().toString().substring(1);
  }

  static int line(IMethod method, int programCounter) {
    if (!(method instanceof IBytecodeMethod<?> bytecode)) return -1;
    try {
      // a call site's program counter is already the bytecode index (ShrikeBTMethod's pcMap)
      return bytecode.getLineNumber(programCounter);
    } catch (Exception e) {
      return -1;
    }
  }

  static int[] lines(IMethod method) {
    if (!(method instanceof IBytecodeMethod<?> bytecode)) return new int[] {-1, -1};
    int first = Integer.MAX_VALUE, last = -1;
    try {
      int count = bytecode.getInstructions().length;
      for (int i = 0; i < count; i++) {
        int at = method.getLineNumber(bytecode.getBytecodeIndex(i));
        if (at > 0) {
          first = Math.min(first, at);
          last = Math.max(last, at);
        }
      }
    } catch (Exception e) {
      return new int[] {-1, -1};
    }
    return first == Integer.MAX_VALUE ? new int[] {-1, -1} : new int[] {first, last};
  }

  /** The implementation method handle of a lambda or method reference, read from the bootstrap. */
  static String lambda(IAnalysisCacheView cache, IMethod caller, CallSiteReference site) {
    String declaring = site.getDeclaredTarget().getDeclaringClass().getName().toString();
    if (!declaring.startsWith("Ljava/lang/invoke/")) return null;
    try {
      IR ir = cache.getIR(caller);
      if (ir == null) return null;
      SSAAbstractInvokeInstruction[] calls = ir.getCalls(site);
      if (calls.length == 0 || !(calls[0] instanceof SSAInvokeDynamicInstruction invoke)) return null;
      BootstrapMethod bootstrap = invoke.getBootstrap();
      if (!bootstrap.isBootstrapForJavaLambdas()) {
        return "{\"bootstrap\":" + q(bootstrap.methodClass() + "." + bootstrap.methodName()) + "}";
      }
      ConstantPoolParser cp = bootstrap.getCP();
      int handle = bootstrap.callArgumentIndex(1);
      String impl = cp.getCPHandleClass(handle) + "." + cp.getCPHandleName(handle)
          + cp.getCPHandleType(handle);
      String summary = "wala/lambda$"
          + className(caller.getDeclaringClass()).replace("/", "$") + "$" + bootstrap.getIndexInClassFile();
      return "{\"impl\":" + q(impl) + ",\"handle_kind\":" + cp.getCPHandleKind(handle)
          + ",\"summary\":" + q(summary) + "}";
    } catch (Exception e) {
      return "{\"error\":" + q(e.toString()) + "}";
    }
  }

  /** The SourceFile attribute of a class file. */
  static String sourceFile(IClass klass) {
    if (!(klass instanceof ShrikeClass shrike)) return null;
    try {
      ClassReader reader = shrike.getReader();
      ClassReader.AttrIterator it = new ClassReader.AttrIterator();
      reader.initClassAttributeIterator(it);
      for (; it.isValid(); it.advance()) {
        if ("SourceFile".equals(it.getName())) return new SourceFileReader(it).getSourceFile();
      }
    } catch (Exception e) {
      return null;
    }
    return null;
  }

  /** Every superclass and every implemented interface, the JDK's and the jars' included. */
  static List<String> ancestors(IClass klass) {
    TreeSet<String> out = new TreeSet<>();
    for (IClass up = klass.getSuperclass(); up != null; up = up.getSuperclass()) out.add(className(up));
    try {
      for (IClass item : klass.getAllImplementedInterfaces()) out.add(className(item));
    } catch (Exception e) {
      // an interface outside the hierarchy: the ones found are kept
    }
    return new ArrayList<>(out);
  }

  static boolean annotatedTest(Iterable<Annotation> annotations) {
    for (Annotation annotation : annotations) {
      if (annotation.getType().getName().toString().endsWith("/Test")) return true;
    }
    return false;
  }

  /**
   * Concrete project classes a test runner creates: a class or a superclass with a `@Test` annotation (JUnit 4
   * or 5, TestNG) on itself or on one of its methods.
   */
  static Set<IClass> runners(IClassHierarchy cha, AnalysisScope scope) {
    Set<IClass> annotated = new HashSet<>(), out = new HashSet<>();
    for (IClass klass : cha) {
      if (!isApp(scope, klass)) continue;
      boolean found = annotatedTest(klass.getAnnotations());
      for (IMethod method : klass.getDeclaredMethods()) found = found || annotatedTest(method.getAnnotations());
      if (found) annotated.add(klass);
    }
    for (IClass klass : cha) {
      if (!isApp(scope, klass) || klass.isAbstract() || klass.isInterface()) continue;
      for (IClass up = klass; up != null; up = up.getSuperclass()) {
        if (annotated.contains(up)) {
          out.add(klass);
          break;
        }
      }
    }
    return out;
  }

  static boolean isApp(AnalysisScope scope, IClass klass) {
    return scope.isApplicationLoader(klass.getClassLoader());
  }

  static int dump(String algorithm, CallGraph cg, AnalysisScope scope, IAnalysisCacheView cache)
      throws Exception {
    int records = 0;
    for (CGNode node : cg) {
      IMethod method = node.getMethod();
      IClass klass = method.getDeclaringClass();
      boolean trampoline = klass.getName().toString().startsWith("Lwala/lambda$");
      if (!trampoline && !isApp(scope, klass)) continue;
      TreeSet<String> all = new TreeSet<>();
      for (Iterator<CallSiteReference> it = node.iterateCallSites(); it.hasNext(); ) {
        CallSiteReference site = it.next();
        TreeSet<String> targets = new TreeSet<>();
        for (CGNode target : cg.getPossibleTargets(node, site)) {
          targets.add(sig(target.getMethod().getReference()));
        }
        if (trampoline) {
          all.addAll(targets);
          continue;
        }
        String lambda = lambda(cache, method, site);
        emit("{\"t\":\"call\",\"alg\":" + q(algorithm) + ",\"caller\":" + q(sig(method.getReference()))
            + ",\"line\":" + line(method, site.getProgramCounter()) + ",\"pc\":" + site.getProgramCounter()
            + ",\"invoke\":" + q(String.valueOf(site.getInvocationCode()))
            + ",\"declared\":" + q(sig(site.getDeclaredTarget())) + ",\"targets\":" + list(targets)
            + (lambda == null ? "" : ",\"lambda\":" + lambda) + "}");
        records++;
      }
      if (trampoline) {
        emit("{\"t\":\"trampoline\",\"alg\":" + q(algorithm) + ",\"class\":" + q(className(klass))
            + ",\"method\":" + q(sig(method.getReference())) + ",\"targets\":" + list(all) + "}");
        records++;
      }
    }
    return records;
  }

  public static void main(String[] args) throws Exception {
    List<String> dirs = new ArrayList<>(), jars = new ArrayList<>();
    String exclusions = null, output = null;
    for (String row : Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8)) {
      int space = row.indexOf(' ');
      if (space < 0) continue;
      String key = row.substring(0, space), value = row.substring(space + 1);
      switch (key) {
        case "dir" -> dirs.add(value);
        case "jar" -> jars.add(value);
        case "exclusions" -> exclusions = value;
        case "out" -> output = value;
        default -> { }
      }
    }
    out = Files.newBufferedWriter(Paths.get(output), StandardCharsets.UTF_8);
    long begun = System.nanoTime();
    AnalysisScope scope = AnalysisScopeReader.instance.makePrimordialScope(
        exclusions == null ? null : new File(exclusions));
    for (String jar : jars) scope.addToScope(ClassLoaderReference.Extension, new JarFile(jar));
    for (String dir : dirs) {
      scope.addToScope(ClassLoaderReference.Application, new BinaryDirectoryTreeModule(new File(dir)));
      Path root = Paths.get(dir);
      try (Stream<Path> walk = Files.walk(root)) {
        walk.filter(p -> p.toString().endsWith(".class")).forEach(p -> {
          String name = root.relativize(p).toString().replace(File.separatorChar, '/');
          classDirs.putIfAbsent(name.substring(0, name.length() - 6), dir);
        });
      }
    }
    IClassHierarchy cha = ClassHierarchyFactory.makeWithRoot(scope);
    long hierarchy = System.nanoTime();
    IAnalysisCacheView cache = new AnalysisCacheImpl();
    List<Entrypoint> entries = new ArrayList<>(), runnerEntries = new ArrayList<>();
    Set<IClass> runners = runners(cha, scope);
    int appClasses = 0;
    for (IClass klass : cha) {
      if (!isApp(scope, klass)) continue;
      appClasses++;
      String source;
      try {
        source = sourceFile(klass);
      } catch (Exception e) {
        source = null;
      }
      emit("{\"t\":\"class\",\"name\":" + q(className(klass)) + ",\"source\":" + q(source)
          + ",\"dir\":" + q(classDirs.get(className(klass))) + ",\"interface\":" + klass.isInterface()
          + ",\"abstract\":" + klass.isAbstract() + ",\"synthetic\":" + klass.isSynthetic()
          + ",\"super\":" + q(klass.getSuperclass() == null ? null : className(klass.getSuperclass()))
          + ",\"interfaces\":" + list(klass.getDirectInterfaces().stream().map(JvmCallGraph::className).toList())
          + ",\"ancestors\":" + list(ancestors(klass))
          + "}");
      for (IMethod method : klass.getDeclaredMethods()) {
        int[] span = lines(method);
        emit("{\"t\":\"method\",\"sig\":" + q(sig(method.getReference())) + ",\"first\":" + span[0]
            + ",\"last\":" + span[1] + ",\"static\":" + method.isStatic() + ",\"abstract\":"
            + method.isAbstract() + ",\"synthetic\":" + method.isSynthetic() + ",\"bridge\":"
            + method.isBridge() + "}");
        if (!method.isAbstract() && !method.isNative()) {
          entries.add(new Entry(method, cha, false));
          if (runners.contains(klass)) runnerEntries.add(new Entry(method, cha, true));
          else runnerEntries.add(new Entry(method, cha, false));
        }
      }
    }
    CHACallGraph chaGraph = new CHACallGraph(cha, true);
    chaGraph.init(entries);
    long chaDone = System.nanoTime();
    int chaRecords = dump("cha", chaGraph, scope, cache);
    long chaDumped = System.nanoTime();
    AnalysisOptions options = new AnalysisOptions(scope, entries);
    options.setReflectionOptions(AnalysisOptions.ReflectionOptions.NONE);
    CallGraph rta = Util.makeRTABuilder(options, cache, cha).makeCallGraph(options, null);
    long rtaDone = System.nanoTime();
    int rtaRecords = dump("rta", rta, scope, cache);
    AnalysisOptions runnerOptions = new AnalysisOptions(scope, runnerEntries);
    runnerOptions.setReflectionOptions(AnalysisOptions.ReflectionOptions.NONE);
    long runnerBegun = System.nanoTime();
    CallGraph rtat = Util.makeRTABuilder(runnerOptions, new AnalysisCacheImpl(), cha).makeCallGraph(runnerOptions, null);
    long runnerDone = System.nanoTime();
    int rtatRecords = dump("rtat", rtat, scope, cache);
    TreeSet<String> instantiated = new TreeSet<>();
    for (CGNode node : rta) {
      for (Iterator<NewSiteReference> it = node.iterateNewSites(); it.hasNext(); ) {
        String type = it.next().getDeclaredType().getName().toString();
        if (type.startsWith("L")) instantiated.add(type.substring(1));
      }
    }
    emit("{\"t\":\"instantiated\",\"classes\":" + list(instantiated) + "}");
    long peak = ManagementFactory.getMemoryPoolMXBeans().stream()
        .mapToLong(pool -> pool.getPeakUsage() == null ? 0 : pool.getPeakUsage().getUsed()).sum();
    emit("{\"t\":\"engine\",\"application_classes\":" + appClasses + ",\"entrypoints\":" + entries.size()
        + ",\"hierarchy_classes\":" + cha.getNumberOfClasses()
        + ",\"cha_nodes\":" + chaGraph.getNumberOfNodes() + ",\"rta_nodes\":" + rta.getNumberOfNodes()
        + ",\"rtat_nodes\":" + rtat.getNumberOfNodes() + ",\"test_runner_classes\":" + runners.size()
        + ",\"cha_records\":" + chaRecords + ",\"rta_records\":" + rtaRecords + ",\"rtat_records\":" + rtatRecords
        + ",\"seconds_rtat\":" + (runnerDone - runnerBegun) / 1e9
        + ",\"seconds_hierarchy\":" + (hierarchy - begun) / 1e9 + ",\"seconds_cha\":" + (chaDone - hierarchy) / 1e9
        + ",\"seconds_rta\":" + (rtaDone - chaDumped) / 1e9 + ",\"seconds_total\":" + (System.nanoTime() - begun) / 1e9
        + ",\"heap_peak_mb\":" + peak / (1 << 20) + "}");
    out.close();
  }
}
