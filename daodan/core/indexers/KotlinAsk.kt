// The Kotlin Analysis API in standalone mode over the compile tasks scip-java dumped (`kotlin-configs/`), for
// indexers/kotlin.py: one source module per compile task, one library module per jar, the running JVM's home as
// the JDK. A classpath entry that is another task's output (its classes or its jar) is a dependency on that
// task's module, so a call across tasks resolves to the source declaration, not to a jar.
//
// `KotlinAsk <kotlin-configs> --across <answers>`: one batch, in the container of the index, over the sites
// where scip-java's overload number can be wrong (indexers/kotlin.py, `refine`): the references to a function
// whose name is overloaded in its class or package (or to a class with two constructors or more) that reach a
// declaration of another module or one overridden from another module, and the overrides of such names. One
// JSON object per line, paths relative to the tasks' source root: {"kind": "ref", "file", "line", "column"
// (UTF-16 units), "targets"} or {"kind": "overridden", "file", "line", "targets"}, each target {"file", "line"}
// in the project's sources.
//
// `KotlinAsk <kotlin-configs>`: questions on standard input, for benchmarks/inference-audit/adapters/
// kotlin_analysis.py. It prints READY TAB <files> TAB <modules> TAB <source root>, then answers each query
// <id> TAB <mode> TAB <absolute file> TAB <1-based line> TAB <column in UTF-16 units>:
//   ref         the reference at the position (the occurrence of a name)
//   implicit    every implicit operator call on the line (`x[k]`, `x[k] = v`, `for`, `by`, destructuring)
//   overridden  what the declaration at the position overrides
// with one JSON object per line, {"id", "elements": [{"role", "line", "column", "text", "targets"}], "error"};
// each target names its symbol, parameters, origin, source position or jar, and module.
package daodan

import com.intellij.openapi.util.Disposer
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiNameIdentifierOwner
import com.intellij.psi.util.PsiTreeUtil
import org.jetbrains.kotlin.analysis.api.KaSession
import org.jetbrains.kotlin.analysis.api.analyze
import org.jetbrains.kotlin.analysis.api.projectStructure.KaLibraryModule
import org.jetbrains.kotlin.analysis.api.projectStructure.KaModule
import org.jetbrains.kotlin.analysis.api.projectStructure.KaSourceModule
import org.jetbrains.kotlin.analysis.api.resolution.successfulFunctionCallOrNull
import org.jetbrains.kotlin.analysis.api.standalone.buildStandaloneAnalysisAPISession
import org.jetbrains.kotlin.analysis.api.symbols.KaCallableSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaClassLikeSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaConstructorSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaFunctionSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaNamedFunctionSymbol
import org.jetbrains.kotlin.analysis.api.symbols.KaSymbol
import org.jetbrains.kotlin.analysis.api.types.KaClassType
import org.jetbrains.kotlin.analysis.api.types.KaType
import org.jetbrains.kotlin.analysis.api.types.KaTypeParameterType
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtLibraryModule
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtSdkModule
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtSourceModule
import org.jetbrains.kotlin.idea.references.KtReference
import org.jetbrains.kotlin.idea.references.mainReference
import org.jetbrains.kotlin.lexer.KtTokens
import org.jetbrains.kotlin.platform.jvm.JvmPlatforms
import org.jetbrains.kotlin.psi.KtArrayAccessExpression
import org.jetbrains.kotlin.psi.KtBinaryExpression
import org.jetbrains.kotlin.psi.KtCallableDeclaration
import org.jetbrains.kotlin.psi.KtClass
import org.jetbrains.kotlin.psi.KtDestructuringDeclarationEntry
import org.jetbrains.kotlin.psi.KtElement
import org.jetbrains.kotlin.psi.KtFile
import org.jetbrains.kotlin.psi.KtForExpression
import org.jetbrains.kotlin.psi.KtNamedFunction
import org.jetbrains.kotlin.psi.KtPropertyDelegate
import org.jetbrains.kotlin.psi.KtReferenceExpression
import org.jetbrains.kotlin.psi.KtSimpleNameExpression
import org.jetbrains.kotlin.psi.psiUtil.containingClassOrObject
import org.jetbrains.kotlin.psi.psiUtil.getParentOfType
import java.io.File
import java.nio.file.Paths
import kotlin.system.exitProcess

private class Module(val name: String) {
    val sources = mutableListOf<String>()
    val classpath = mutableListOf<String>()
    val libraries = mutableListOf<String>()
    val depends = mutableListOf<String>()
    var home = "" to ""
}

// A compile task's output on another task's classpath: its classes (the folder names the source set) or its jar.
// A regular expression on a path, which has no grammar.
private val OUTPUT = Regex("build/(?:classes/[^/]+/([^/]+)|libs/[^/]+\\.jar)$")

/** One module per compile task, in dependency order, and the source root the tasks list their files under. */
private fun modules(configs: File): Pair<List<Module>, String> {
    val tasks = mutableListOf<Module>()
    var root = ""
    for (config in configs.listFiles().orEmpty().filter { it.name.endsWith(".txt") }.sortedBy { it.name }) {
        val task = Module(config.name.removeSuffix(".txt"))
        var own = ""
        for (row in config.readLines()) {
            val parts = row.split(" ", limit = 2)
            if (parts.size < 2) continue
            when (parts[0]) {
                "sourceroot" -> own = parts[1]
                "source" -> task.sources.add(parts[1])
                "classpath" -> task.classpath.add(parts[1])
            }
        }
        if (own.isEmpty() || !File(own).isDirectory || task.sources.isEmpty()) continue
        root = own
        val first = File(task.sources[0]).relativeTo(File(own)).invariantSeparatorsPath
        val at = first.indexOf("src/")
        task.home = (if (at < 0) first else first.substring(0, at)).trimEnd('/') to
            (if (at < 0) "" else first.substring(at + 4).substringBefore("/"))
        tasks.add(task)
    }
    val homes = tasks.associate { it.home to it.name }
    for (task in tasks) {
        for (entry in task.classpath) {
            val match = if (entry.startsWith("$root/")) OUTPUT.find(entry) else null
            if (match != null) {
                val project = File(entry).relativeTo(File(root)).invariantSeparatorsPath.substringBefore("build/")
                    .trimEnd('/')
                val home = homes[project to match.groupValues[1].ifEmpty { "main" }]
                if (home != null && home != task.name && home !in task.depends) task.depends.add(home)
            } else if (entry.endsWith(".jar") && File(entry).isFile && "scip-plugin" !in entry) {
                task.libraries.add(entry)
            }
        }
    }
    val ordered = mutableListOf<Module>()
    val done = HashSet<String>()
    while (ordered.size < tasks.size) {
        val ready = tasks.filter { it.name !in done && done.containsAll(it.depends) }
        if (ready.isEmpty()) throw IllegalStateException("compile tasks depend on each other in a cycle")
        ready.forEach { ordered.add(it); done.add(it.name) }
    }
    return ordered to root
}

private val starts = HashMap<String, IntArray>()

private fun lineStarts(file: com.intellij.psi.PsiFile): IntArray = starts.getOrPut(file.virtualFile?.path ?: file.name) {
    val text = file.text
    val found = mutableListOf(0)
    text.forEachIndexed { index, char -> if (char == '\n') found.add(index + 1) }
    found.toIntArray()
}

private fun q(text: String?): String {
    if (text == null) return "null"
    val out = StringBuilder("\"")
    for (char in text) {
        when (char) {
            '"' -> out.append("\\\"")
            '\\' -> out.append("\\\\")
            '\n' -> out.append("\\n")
            '\r' -> out.append("\\r")
            '\t' -> out.append("\\t")
            else -> if (char < ' ') out.append(String.format("\\u%04x", char.code)) else out.append(char)
        }
    }
    return out.append('"').toString()
}

private fun lineOf(file: com.intellij.psi.PsiFile, offset: Int): Pair<Int, Int> {
    val lines = lineStarts(file)
    var line = lines.indexOfLast { it <= offset }
    if (line < 0) line = 0
    return (line + 1) to (offset - lines[line])
}

private fun place(element: PsiElement): String {
    val file = element.containingFile
    val virtual = file?.virtualFile ?: return "\"file\":null,\"vfile\":null"
    if (virtual.fileSystem.protocol != "file") return "\"file\":null,\"vfile\":${q(virtual.path)}"
    val anchor = (element as? PsiNameIdentifierOwner)?.nameIdentifier ?: element
    val (line, column) = lineOf(file, anchor.textOffset)
    return "\"file\":${q(File(virtual.path).absolutePath)},\"line\":$line,\"column\":$column"
}

private fun typeName(type: KaType): String = when (type) {
    is KaClassType -> type.classId.asString()
    is KaTypeParameterType -> type.name.asString()
    else -> type.toString()
}

private fun moduleName(module: KaModule): String = when (module) {
    is KaLibraryModule -> (if (module.isSdk) "sdk:" else "library:") + module.binaryRoots.joinToString(",")
    is KaSourceModule -> "source:" + module.name
    else -> module.javaClass.simpleName
}

private fun KaSession.describe(symbol: KaSymbol, depth: Int = 0): String {
    val parts = mutableListOf("\"kind\":${q(symbol.javaClass.simpleName)}", "\"origin\":${q(symbol.origin.name)}")
    if (symbol is KaCallableSymbol) parts.add("\"callable\":${q(symbol.callableId?.toString())}")
    if (symbol is KaConstructorSymbol) parts.add("\"class\":${q(symbol.containingClassId?.asString())}")
    if (symbol is KaClassLikeSymbol) parts.add("\"class\":${q(symbol.classId?.asString())}")
    if (symbol is KaFunctionSymbol) {
        parts.add("\"params\":[" + symbol.valueParameters.joinToString(",") {
            q(typeName(it.returnType) + if (it.isVararg) "..." else "")
        } + "]")
    }
    if (symbol is KaNamedFunctionSymbol) parts.add("\"inline\":${symbol.isInline},\"operator\":${symbol.isOperator}")
    if (symbol is KaCallableSymbol) parts.add("\"extension\":${symbol.isExtension}")
    val psi = symbol.psi
    parts.add(if (psi != null) place(psi) else "\"file\":null,\"vfile\":null")
    parts.add("\"module\":${q(runCatching { moduleName(symbol.containingModule) }.getOrElse { "error: $it" })}")
    if (symbol is KaCallableSymbol && depth == 0) {
        val original = symbol.fakeOverrideOriginal
        if (original != symbol) parts.add("\"original\":{${describe(original, 1)}}")
        if (psi == null || psi.containingFile?.virtualFile?.fileSystem?.protocol != "file") {
            val overridden = symbol.allOverriddenSymbols.take(4).toList()
            if (overridden.isNotEmpty()) parts.add("\"overridden\":[" + overridden.joinToString(",") { "{${describe(it, 1)}}" } + "]")
        }
    }
    return parts.joinToString(",")
}

private fun element(file: KtFile, element: PsiElement, role: String, offset: Int, targets: List<String>): String {
    val (line, column) = lineOf(file, offset)
    return "{\"role\":${q(role)},\"line\":$line,\"column\":$column,\"text\":${q(element.text.take(80))}," +
        "\"targets\":[" + targets.joinToString(",") { "{$it}" } + "]}"
}

private fun resolved(target: KtElement): List<String> = analyze(target) {
    val symbols = target.references.filterIsInstance<KtReference>().flatMap { it.resolveToSymbols() }
    val found = symbols.ifEmpty {
        listOfNotNull(target.resolveToCall()?.successfulFunctionCallOrNull()?.partiallyAppliedSymbol?.signature?.symbol)
    }
    found.map { describe(it) }
}

private fun implicit(file: KtFile, line: Int): List<String> {
    val out = mutableListOf<String>()
    val found = PsiTreeUtil.collectElements(file) {
        it is KtArrayAccessExpression || it is KtForExpression || it is KtPropertyDelegate || it is KtDestructuringDeclarationEntry
    }
    for (item in found) {
        val (role, offset) = when (item) {
            is KtArrayAccessExpression -> {
                val parent = item.parent
                val assigned = parent is KtBinaryExpression && parent.left == item &&
                    parent.operationToken in KtTokens.ALL_ASSIGNMENTS
                (if (assigned) "set" else "get") to item.indicesNode.textOffset
            }
            is KtForExpression -> "iterator" to (item.node.findChildByType(KtTokens.IN_KEYWORD)?.startOffset ?: item.textOffset)
            is KtPropertyDelegate -> "getValue" to item.textOffset
            else -> "componentN" to item.textOffset
        }
        if (lineOf(file, offset).first != line) continue
        out.add(element(file, item, role, offset, resolved(item as KtElement)))
    }
    return out
}

/** A declaration in the project's sources: its file relative to `root`, its line and its module; else null. */
private fun sourcePlace(element: PsiElement?, owners: Map<String, String>, root: File): Triple<String, Int, String>? {
    val file = element?.containingFile ?: return null
    val virtual = file.virtualFile ?: return null
    if (virtual.fileSystem.protocol != "file") return null
    val path = File(virtual.path).canonicalPath
    val module = owners[path] ?: return null
    val anchor = (element as? PsiNameIdentifierOwner)?.nameIdentifier ?: element
    return Triple(File(path).relativeTo(root).invariantSeparatorsPath, lineOf(file, anchor.textOffset).first, module)
}

private fun targets(places: Collection<Triple<String, Int, String>>): String =
    places.map { it.first to it.second }.distinct().joinToString(",", "[", "]") {
        "{\"file\":${q(it.first)},\"line\":${it.second}}"
    }

/** The batch of `--across` (see the head of this file), written to `out`. */
private fun across(files: Map<String, KtFile>, owners: Map<String, String>, root: File, out: File) {
    val begun = System.currentTimeMillis()
    // The names scip-java numbers: a function name declared twice or more in one class or one package, a class
    // with two constructors or more.
    val counts = HashMap<String, Int>()
    val names = HashSet<String>()
    for (file in files.values) {
        for (function in PsiTreeUtil.collectElementsOfType(file, KtNamedFunction::class.java)) {
            val name = function.name ?: continue
            if (function.isLocal) continue
            val owner = function.containingClassOrObject?.fqName?.asString() ?: (file.packageFqName.asString() + "/")
            counts["$owner#$name"] = (counts["$owner#$name"] ?: 0) + 1
        }
        for (type in PsiTreeUtil.collectElementsOfType(file, KtClass::class.java)) {
            val secondary = type.secondaryConstructors.size
            if (secondary + (if (type.primaryConstructor != null || secondary == 0) 1 else 0) > 1) {
                type.name?.let { names.add(it) }
            }
        }
    }
    counts.filterValues { it > 1 }.keys.forEach { names.add(it.substringAfterLast('#')) }
    val rows = mutableListOf<String>()
    // The overrides of those names, and the declarations they override from another module.
    val across = HashSet<Pair<String, Int>>()
    var overrides = 0
    for ((path, file) in files) {
        val module = owners[path] ?: continue
        for (function in PsiTreeUtil.collectElementsOfType(file, KtNamedFunction::class.java)) {
            if (function.name !in names || !function.hasModifier(KtTokens.OVERRIDE_KEYWORD)) continue
            overrides++
            val found = runCatching {
                analyze(function) {
                    (function.symbol as? KaCallableSymbol)?.allOverriddenSymbols?.toList().orEmpty()
                        .mapNotNull { sourcePlace(it.psi, owners, root) }
                }
            }.getOrDefault(emptyList())
            if (found.isEmpty()) continue
            found.filter { it.third != module }.forEach { across.add(it.first to it.second) }
            val place = sourcePlace(function, owners, root) ?: continue
            rows.add("{\"kind\":\"overridden\",\"file\":${q(place.first)},\"line\":${place.second}," +
                "\"targets\":${targets(found)}}")
        }
    }
    // The references to those names that reach a declaration of another module, or one overridden from another.
    var asked = 0
    for ((path, file) in files) {
        val module = owners[path] ?: continue
        val rel = File(path).relativeTo(root).invariantSeparatorsPath
        for (reference in PsiTreeUtil.collectElementsOfType(file, KtSimpleNameExpression::class.java)) {
            if (reference.getReferencedName() !in names) continue
            asked++
            val found = runCatching {
                analyze(reference) {
                    reference.mainReference.resolveToSymbols().filter { it is KaFunctionSymbol }
                        .mapNotNull { sourcePlace(it.psi, owners, root) }
                }
            }.getOrDefault(emptyList())
            val kept = found.filter { it.third != module || (it.first to it.second) in across }
            if (kept.isEmpty()) continue
            val (line, column) = lineOf(file, reference.textOffset)
            rows.add("{\"kind\":\"ref\",\"file\":${q(rel)},\"line\":$line,\"column\":$column," +
                "\"targets\":${targets(kept)}}")
        }
    }
    out.writeText(rows.joinToString("") { it + "\n" })
    println("kotlin-ask: ${files.size} files, ${names.size} overloaded names, $asked references and $overrides " +
        "overrides asked, ${rows.size} answers in ${(System.currentTimeMillis() - begun) / 1000.0} s")
}

fun main(args: Array<String>) {
    val (modules, root) = modules(File(args[0]))
    val disposable = Disposer.newDisposable("daodan-kotlin-ask")
    val platform = JvmPlatforms.defaultJvmPlatform
    val session = buildStandaloneAnalysisAPISession(projectDisposable = disposable) {
        buildKtModuleProvider {
            this.platform = platform
            val jdk = buildKtSdkModule {
                this.platform = platform
                addBinaryRootsFromJdkHome(Paths.get(System.getProperty("java.home")), isJre = true)
                libraryName = "JDK"
            }
            val libraries = HashMap<String, KaModule>()
            val built = HashMap<String, KaModule>()
            for (module in modules) {
                val source = buildKtSourceModule {
                    this.platform = platform
                    moduleName = module.name
                    addSourceRoots(module.sources.map { Paths.get(it) })
                    addRegularDependency(jdk)
                    module.depends.forEach { addRegularDependency(built.getValue(it)) }
                    module.libraries.forEach { jar ->
                        addRegularDependency(libraries.getOrPut(jar) {
                            buildKtLibraryModule {
                                this.platform = platform
                                addBinaryRoots(listOf(Paths.get(jar)))
                                libraryName = jar
                            }
                        })
                    }
                }
                built[module.name] = source
                addModule(source)
            }
        }
    }
    val owners = HashMap<String, String>()  // a source file's canonical path -> the name of its module
    session.modulesWithFiles.forEach { (module, found) ->
        val name = (module as? KaSourceModule)?.name ?: return@forEach
        found.forEach { file -> file.virtualFile?.let { owners[File(it.path).canonicalPath] = name } }
    }
    val files = session.modulesWithFiles.values.flatten().filterIsInstance<KtFile>()
        .associateBy { File(it.virtualFile.path).canonicalPath }
    if (args.size >= 3 && args[1] == "--across") {
        across(files, owners, File(root).canonicalFile, File(args[2]))
        Disposer.dispose(disposable)
        exitProcess(0)
    }
    println("READY\t${files.size}\t${modules.size}\t$root")
    System.out.flush()
    val input = System.`in`.bufferedReader()
    while (true) {
        val query = input.readLine() ?: break
        if (query.isBlank()) continue
        val fields = query.split("\t")
        val id = fields[0]
        val answer = try {
            val (mode, path, line, column) = fields.drop(1)
            val file = files[File(path).canonicalPath] ?: throw IllegalArgumentException("not a source file: $path")
            val offset = lineStarts(file)[line.toInt() - 1] + column.toInt()
            val elements = when (mode) {
                "ref" -> {
                    val reference = file.findElementAt(offset)?.getParentOfType<KtReferenceExpression>(false)
                        ?: throw IllegalArgumentException("no reference at $line:$column")
                    val targets = analyze(reference) { reference.mainReference.resolveToSymbols().map { describe(it) } }
                    listOf(element(file, reference, "ref", reference.textOffset, targets))
                }
                "implicit" -> implicit(file, line.toInt())
                "overridden" -> {
                    val declaration = file.findElementAt(offset)?.getParentOfType<KtCallableDeclaration>(false)
                        ?: throw IllegalArgumentException("no declaration at $line:$column")
                    val targets = analyze(declaration) {
                        (declaration.symbol as? KaCallableSymbol)?.allOverriddenSymbols?.toList().orEmpty().map { describe(it, 1) }
                    }
                    listOf(element(file, declaration, "overridden", declaration.textOffset, targets))
                }
                else -> throw IllegalArgumentException("unknown mode $mode")
            }
            "{\"id\":${q(id)},\"elements\":[${elements.joinToString(",")}],\"error\":null}"
        } catch (error: Throwable) {
            "{\"id\":${q(id)},\"elements\":[],\"error\":${q(error.toString().take(300))}}"
        }
        println(answer)
        System.out.flush()
    }
    Disposer.dispose(disposable)
    // The platform leaves non-daemon threads behind; the process ends with its input.
    exitProcess(0)
}
