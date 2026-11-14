// Targeted questions to the Kotlin Analysis API in standalone mode, for adapters/kotlin_analysis.py.
// A copy of the map's resolver (plugins/codebase-map/skills/map/scripts/engines/KotlinResolver.kt) with one
// source module per compile task, one library module per jar, and a description of each answer.
//
// Configuration lines, in dependency order: `module <name>`, then for that module `source <file>`,
// `library <jar>` and `depends <module name>`, repeatable. The running JVM's home is the JDK.
// Query: <id> TAB <mode> TAB <absolute file> TAB <1-based line> TAB <column in UTF-16 units>
//   ref         the reference at the position (the occurrence of a name)
//   implicit    every implicit operator call on the line (`x[k]`, `x[k] = v`, `for`, `by`, destructuring)
//   overridden  what the declaration at the position overrides
// Answer: one JSON object per line, {"id", "elements": [{"role", "line", "column", "text", "targets"}],
// "error"}; each target names its symbol, parameters, origin, source position or jar, and module.
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
import org.jetbrains.kotlin.psi.KtDestructuringDeclarationEntry
import org.jetbrains.kotlin.psi.KtElement
import org.jetbrains.kotlin.psi.KtFile
import org.jetbrains.kotlin.psi.KtForExpression
import org.jetbrains.kotlin.psi.KtPropertyDelegate
import org.jetbrains.kotlin.psi.KtReferenceExpression
import org.jetbrains.kotlin.psi.psiUtil.getParentOfType
import java.io.File
import java.nio.file.Paths
import kotlin.system.exitProcess

private class Module(val name: String) {
    val sources = mutableListOf<String>()
    val libraries = mutableListOf<String>()
    val depends = mutableListOf<String>()
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

fun main(args: Array<String>) {
    val modules = mutableListOf<Module>()
    File(args[0]).readLines().forEach { row ->
        val (key, value) = row.split(" ", limit = 2).let { it[0] to it.getOrElse(1) { "" } }
        when (key) {
            "module" -> modules.add(Module(value))
            "source" -> modules.last().sources.add(value)
            "library" -> modules.last().libraries.add(value)
            "depends" -> modules.last().depends.add(value)
        }
    }
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
    val files = session.modulesWithFiles.values.flatten().filterIsInstance<KtFile>()
        .associateBy { File(it.virtualFile.path).canonicalPath }
    println("READY\t${files.size}")
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
