rootProject.name = "shop"

// every folder of modules/ with a build script is a project, legacy/ excepted: no include names them literally
file("modules").listFiles()!!.filter { File(it, "build.gradle.kts").isFile && it.name != "legacy" }
    .sortedBy { it.name }.forEach { include(":modules:${it.name}") }

include(":api")
project(":api").projectDir = file("services/api-v2")

includeBuild("tooling")
