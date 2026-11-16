# Giro della pipeline sul corpus

File: `2026-11-16-jvm-kotlinconf.json`.

## Casi

- Eseguiti: 1; falliti: 0.
- Secondi: 754,2 in totale; mediana 754,2.

### Casi più lenti

| Caso | Secondi |
| --- | --- |
| real-app-kotlinconf | 754,2 |

### Casi falliti

Nessuno.

## Linguaggi

| Linguaggio | Casi | fresh | failed | unavailable | File indicizzati / nello snapshot | Siti | Risposti | Buchi | Quota risposta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c | 1 | 0 | 0 | 1 | 0 / 0 | 0 | 0 | 0 | — |
| javascript | 1 | 1 | 0 | 0 | 1 / 1 | 23 | 13 | 10 | 56,5 % |
| kotlin | 1 | 0 | 1 | 0 | 0 / 0 | 0 | 0 | 0 | — |
| stylesheet | 1 | 1 | 0 | 0 | 3 / 3 | 45 | 37 | 8 | 82,2 % |

### Risposte per tipo e buchi per classe

| Linguaggio | Risposte | Buchi |
| --- | --- | --- |
| javascript | external 10, project-value 3 | a member of a value of type any: only execution knows it 10 |
| stylesheet | project-value 37 | no-font-face 5, no-rule 1, unresolved-import 2 |

### Stati diversi da fresh

| Linguaggio | Stato | Casi | Motivo |
| --- | --- | --- | --- |
| c | unavailable | 1 | no C or C++ unit in the pre-map: no build of the project compiles C or C++ |
| kotlin | failed | 1 | scip-java wrote no index (preparation exited with code 1): determine the dependencies of task ':app:adminApp:scipCompileAll'. > Task with name 'compileKotlinJvm' not found in project ':app:adminApp'. * Try: > Run with --stacktrace option to get the stack trace. > Run with --info or --debug option to |

### Linguaggi fresh con file fuori dall'indice

Nessuno.

### Linguaggi senza analizzatore

| Linguaggio | Casi | File |
| --- | --- | --- |
| sql | 1 | 4 |

## Pre-mappa

| Faccetta | Casi che la danno | Casi che non la danno | Trovate | Attese | In più | Sbagliate |
| --- | --- | --- | --- | --- | --- | --- |
| languages | 1 | 0 | 6 | 6 | 14 | 0 |
| languages.files | 0 | 1 | 0 | 0 | 0 | 0 |
| excluded | 1 | 0 | 42 | 46 | 5 | 0 |
| units | 1 | 0 | 12 | 13 | 0 | 0 |
| units.depends_on | 1 | 0 | 9 | 11 | 0 | 0 |
| units.source_roots | 0 | 1 | 0 | 0 | 0 | 0 |
| units.config | 1 | 0 | 0 | 33 | 0 | 0 |
| workspace | 1 | 0 | 1 | 1 | 0 | 0 |
| workspace.members | 1 | 0 | 9 | 9 | 1 | 0 |
| toolchains | 1 | 0 | 7 | 15 | 3 | 4 |
| dependencies | 0 | 1 | 0 | 0 | 0 | 0 |
| frameworks | 0 | 1 | 0 | 0 | 0 | 0 |
| services | 0 | 1 | 0 | 0 | 0 | 0 |
| needs | 0 | 1 | 0 | 0 | 0 | 0 |

## Gap

| Passo | Tipo | Numero | Esempi |
| --- | --- | --- | --- |
| scan | no_analyzer | 4 | real-app-kotlinconf: 2 MATLAB files and no analyzer lists the language: their code is in no graph<br>real-app-kotlinconf: 1 Procfile files and no analyzer lists the language: their code is in no graph<br>real-app-kotlinconf: 1 Shell files and no analyzer lists the language: their code is in no graph |
| scan | code_outside_units | 3 | real-app-kotlinconf: app/iosApp/KotlinMultiplatformLinkedPackage/Sources/KotlinMultiplatformLinkedPackage/include: 1 C files that no unit of kind autotools-project, bazel-target, cmake-target, go-module, make-target, meson-target, msbuild-project holds<br>real-app-kotlinconf: app/iosApp/KotlinMultiplatformLinkedPackage/subpackages/io_github_mirzemehdi_kmpnotifier_push_firebase_2_0_2/Sources/io_github_mirzemehdi_kmpnotifier_push_firebase_2_0_2/include: 1 C files that no unit of kind autotools-project, bazel-target, cmake-target, go-module, make-target<br>real-app-kotlinconf: app/webApp/src/webMain/resources: 1 JavaScript files that no unit of kind npm-package holds |
| scan | toolchain_undeclared | 1 | real-app-kotlinconf: .: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build |

## Container

- Corse: 8; secondi: 168,0.

| Fase | Corse | Secondi |
| --- | --- | --- |
| execute | 4 | 19,0 |
| prepare | 4 | 149,0 |

### Esiti diversi da exit 0

Nessuno.
