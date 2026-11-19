// Answers "where is the callee at this position declared?" for Kotlin through the Kotlin Analysis API
// in standalone mode, for resolve_edges.py. Compiled once on first use; reads its configuration file,
// prints READY, then answers one query per line.
//
// Configuration lines: `root=<source dir>` and `library=<jar>`, repeatable. The running JVM's own home
// is the JDK the code is resolved against.
// Query:  <absolute file path> TAB <1-based line> TAB <column in UTF-16 units>
// Answer: OK, then per target TAB <path or -> TAB <line> TAB <column>, or ERROR TAB <message>.
// A target without a source file on disk (a library class, the JDK) has path `-`.
package daodan

import com.intellij.openapi.util.Disposer
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiNameIdentifierOwner
import org.jetbrains.kotlin.analysis.api.analyze
import org.jetbrains.kotlin.analysis.api.standalone.buildStandaloneAnalysisAPISession
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtLibraryModule
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtSdkModule
import org.jetbrains.kotlin.analysis.project.structure.builder.buildKtSourceModule
import org.jetbrains.kotlin.idea.references.mainReference
import org.jetbrains.kotlin.platform.jvm.JvmPlatforms
import org.jetbrains.kotlin.psi.KtConstructor
import org.jetbrains.kotlin.psi.KtFile
import org.jetbrains.kotlin.psi.KtReferenceExpression
import org.jetbrains.kotlin.psi.psiUtil.getParentOfType
import java.io.File
import java.nio.file.Paths
import kotlin.system.exitProcess

private fun lineStarts(text: String): IntArray {
    val starts = mutableListOf(0)
    text.forEachIndexed { index, char -> if (char == '\n') starts.add(index + 1) }
    return starts.toIntArray()
}

private fun position(element: PsiElement): String {
    val file = element.containingFile
    val virtual = file?.virtualFile
    if (virtual == null || virtual.fileSystem.protocol != "file") return "-\t0\t0"
    val anchor = (element as? PsiNameIdentifierOwner)?.nameIdentifier ?: element
    val offset = anchor.textOffset
    val starts = lineStarts(file.text)
    var line = starts.indexOfLast { it <= offset }
    if (line < 0) line = 0
    return "${File(virtual.path).absolutePath}\t${line + 1}\t${offset - starts[line]}"
}

fun main(args: Array<String>) {
    val roots = mutableListOf<String>()
    val libraries = mutableListOf<String>()
    File(args[0]).readLines().forEach { row ->
        val (key, value) = row.split("=", limit = 2).let { it[0] to it.getOrElse(1) { "" } }
        when (key) {
            "root" -> roots.add(value)
            "library" -> libraries.add(value)
        }
    }
    val disposable = Disposer.newDisposable("daodan-kotlin")
    val platform = JvmPlatforms.defaultJvmPlatform
    val session = buildStandaloneAnalysisAPISession(projectDisposable = disposable) {
        buildKtModuleProvider {
            this.platform = platform
            val jdk = buildKtSdkModule {
                this.platform = platform
                addBinaryRootsFromJdkHome(Paths.get(System.getProperty("java.home")), isJre = true)
                libraryName = "JDK"
            }
            val dependencies = buildKtLibraryModule {
                this.platform = platform
                addBinaryRoots(libraries.map { Paths.get(it) })
                libraryName = "Libraries"
            }
            addModule(buildKtSourceModule {
                this.platform = platform
                moduleName = "project"
                addSourceRoots(roots.map { Paths.get(it) })
                addRegularDependency(jdk)
                addRegularDependency(dependencies)
            })
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
        val answer = try {
            val (path, line, column) = query.split("\t")
            val file = files[File(path).canonicalPath] ?: throw IllegalArgumentException("not a source file: $path")
            val starts = lineStarts(file.text)
            val offset = starts[line.toInt() - 1] + column.toInt()
            val reference = file.findElementAt(offset)?.getParentOfType<KtReferenceExpression>(false)
                ?: throw IllegalArgumentException("no reference at $line:$column")
            val targets = analyze(reference) {
                reference.mainReference.resolveToSymbols().mapNotNull { symbol ->
                    val psi = symbol.psi ?: return@mapNotNull "-\t0\t0"
                    // A constructor names its class: `Tool()` is answered at the class.
                    val named = if (psi is KtConstructor<*>) psi.getContainingClassOrObject() else psi
                    position(named)
                }
            }
            (listOf("OK") + targets).joinToString("\t")
        } catch (error: Throwable) {
            "ERROR\t" + (error.message ?: error.javaClass.simpleName).replace('\t', ' ').replace('\n', ' ')
        }
        println(answer)
        System.out.flush()
    }
    Disposer.dispose(disposable)
    // The platform leaves non-daemon threads behind; the process ends with its input.
    exitProcess(0)
}
