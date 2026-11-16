# Giro della pipeline sul corpus

File: `2026-11-16-java-versions.json`.

## Casi

- Eseguiti: 18; falliti: 0.
- Secondi: 3.526,6 in totale; mediana 178,4.

### Casi più lenti

| Caso | Secondi |
| --- | --- |
| jvm-ver-gradle-mixed-tc8 | 393,9 |
| jvm-ver-gradle-tc11 | 284,2 |
| jvm-ver-gradle-tc21 | 219,7 |
| jvm-ver-gradle-tc25 | 208,6 |
| jvm-ver-gradle-tc8 | 202,0 |

### Casi falliti

Nessuno.

## Linguaggi

| Linguaggio | Casi | fresh | failed | unavailable | File indicizzati / nello snapshot | Siti | Risposti | Buchi | Quota risposta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| java | 18 | 18 | 0 | 0 | 37 / 37 | 453 | 453 | 0 | 100,0 % |
| kotlin | 1 | 1 | 0 | 0 | 1 / 3 | 13 | 2 | 11 | 15,4 % |

### Risposte per tipo e buchi per classe

| Linguaggio | Risposte | Buchi |
| --- | --- | --- |
| java | external 127, project-callable 128, project-value 198 | — |
| kotlin | project-callable 1, project-value 1 | no-document 11 |

### Stati diversi da fresh

Nessuno.

### Linguaggi fresh con file fuori dall'indice

| Caso | Linguaggio | Mancanti / nello snapshot | Motivi |
| --- | --- | --- | --- |
| jvm-ver-gradle-mixed-tc8 | kotlin | 2 / 3 | Gradle script: no KotlinCompile task compiles it (2) |

### Linguaggi senza analizzatore

Nessuno.

## Pre-mappa

| Faccetta | Casi che la danno | Casi che non la danno | Trovate | Attese | In più | Sbagliate |
| --- | --- | --- | --- | --- | --- | --- |
| languages | 18 | 0 | 19 | 19 | 18 | 0 |
| languages.files | 0 | 18 | 0 | 0 | 0 | 0 |
| excluded | 18 | 0 | 0 | 0 | 0 | 0 |
| units | 18 | 0 | 18 | 18 | 0 | 0 |
| units.depends_on | 18 | 0 | 0 | 0 | 0 | 0 |
| units.source_roots | 11 | 7 | 22 | 22 | 0 | 0 |
| units.config | 0 | 18 | 0 | 0 | 0 | 0 |
| workspace | 18 | 0 | 0 | 0 | 7 | 0 |
| workspace.members | 7 | 11 | 0 | 0 | 0 | 0 |
| toolchains | 18 | 0 | 8 | 30 | 1 | 22 |
| dependencies | 0 | 18 | 0 | 0 | 0 | 0 |
| frameworks | 0 | 18 | 0 | 0 | 0 | 0 |
| services | 0 | 18 | 0 | 0 | 0 | 0 |
| needs | 0 | 18 | 0 | 0 | 0 | 0 |

## Gap

| Passo | Tipo | Numero | Esempi |
| --- | --- | --- | --- |
| scan | toolchain_undeclared | 7 | jvm-ver-gradle-mixed-tc8: .: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build<br>jvm-ver-gradle-src6: .: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build<br>jvm-ver-gradle-src8: .: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build |
| analyze | build_edited | 8 | jvm-ver-gradle-mixed-tc8: .: the build as declared gave no index (* What went wrong: / Execution failed for task ':compileJava' (registered by plugin class 'org.gradle.api.plugins.JavaBasePlugin'). / > Compilation failed; see the compiler output below. / * Try: / > Run with --scan to get full insigh<br>jvm-ver-gradle-mixed-tc8: .: the build as declared gave no index (* What went wrong: / Deprecated Gradle features were used in this build, making it incompatible with Gradle 10. / Execution failed for task ':compileJava' (registered by plugin class 'org.gradle.api.plugins.JavaBasePlugin'). / You can<br>jvm-ver-gradle-src6: .: the build as declared gave no index (* What went wrong: / Execution failed for task ':compileJava' (registered by plugin class 'org.gradle.api.plugins.JavaBasePlugin'). / > Compilation failed; see the compiler output below. / error: Source option 6 is no longer supported. Use |
| analyze | jdk_unsupported | 8 | jvm-ver-mvn-11: .: the build states Java 11 (pom.xml#properties.maven.compiler.source) and scip-java 0.14.2's compiler plugin runs on javac 17 or newer only: it was indexed on the image's JDK 17, so its calls into the JDK name JDK 17's classes, not those of Java 11<br>jvm-ver-mvn-14: .: the build states Java 14 (pom.xml#properties.maven.compiler.source) and scip-java 0.14.2's compiler plugin runs on javac 17 or newer only: it was indexed on the image's JDK 17, so its calls into the JDK name JDK 17's classes, not those of Java 14<br>jvm-ver-mvn-5: .: the build states Java 5 (pom.xml#properties.maven.compiler.source) and scip-java 0.14.2's compiler plugin runs on javac 17 or newer only: it was indexed on the image's JDK 17, so its calls into the JDK name JDK 17's classes, not those of Java 5 |

## Container

- Corse: 144; secondi: 1.499,8.

| Fase | Corse | Secondi |
| --- | --- | --- |
| execute | 72 | 287,6 |
| prepare | 72 | 1.212,2 |

### Esiti diversi da exit 0

Nessuno.
