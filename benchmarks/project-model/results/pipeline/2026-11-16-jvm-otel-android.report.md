# Giro della pipeline sul corpus

File: `2026-11-16-jvm-otel-android.json`.

## Casi

- Eseguiti: 3; falliti: 0.
- Secondi: 2.037,3 in totale; mediana 516,0.

### Casi più lenti

| Caso | Secondi |
| --- | --- |
| real-svc-otel-demo | 1.215,9 |
| mix-poly-firebase | 516,0 |
| jvm-android-app-lib | 305,4 |

### Casi falliti

Nessuno.

## Linguaggi

| Linguaggio | Casi | fresh | failed | unavailable | File indicizzati / nello snapshot | Siti | Risposti | Buchi | Quota risposta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c | 1 | 0 | 0 | 1 | 0 / 0 | 0 | 0 | 0 | — |
| cpp | 1 | 0 | 1 | 0 | 0 / 0 | 0 | 0 | 0 | — |
| csharp | 1 | 1 | 0 | 0 | 13 / 13 | 660 | 604 | 56 | 91,5 % |
| go | 1 | 1 | 0 | 0 | 15 / 15 | 6.180 | 6.047 | 133 | 97,9 % |
| java | 1 | 1 | 0 | 0 | 9 / 9 | 693 | 693 | 0 | 100,0 % |
| javascript | 1 | 1 | 0 | 0 | 10 / 10 | 276 | 195 | 81 | 70,7 % |
| kotlin | 3 | 0 | 3 | 0 | 0 / 0 | 0 | 0 | 0 | — |
| python | 2 | 2 | 0 | 0 | 24 / 24 | 1.911 | 1.444 | 467 | 75,6 % |
| rust | 2 | 2 | 0 | 0 | 10 / 10 | 269 | 266 | 3 | 98,9 % |
| stylesheet | 2 | 2 | 0 | 0 | 162 / 169 | 22 | 6 | 16 | 27,3 % |
| typescript | 2 | 2 | 0 | 0 | 144 / 144 | 8.733 | 6.155 | 2.578 | 70,5 % |

### Risposte per tipo e buchi per classe

| Linguaggio | Risposte | Buchi |
| --- | --- | --- |
| csharp | external 355, project-callable 46, project-value 203 | no-occurrence 5, no-position 49, undefined-project-symbol 2 |
| go | external 2.158, project-callable 617, project-value 3.272 | no-occurrence 12, no-position 121 |
| java | external 497, observed 2, project-callable 54, project-value 140 | — |
| javascript | external 86, project-callable 4, project-value 105 | NodeJS.ProcessEnv's index signature: only execution knows the value 2, a member of a value of type any: only execution knows it 72, a member of an anonymous type, an object literal or an index signature another file declares: the index names it with a local of this file it defines nowhere 1, danglin |
| python | external 475, observed 15, project-callable 134, project-value 820 | dangling-local 58, no-occurrence 298, no-position 11, undefined-project-symbol 100 |
| rust | external 182, project-callable 36, project-value 48 | no-occurrence 3 |
| stylesheet | external 1, namespace 5 | no-font-face 1, no-rule 12, parameter 2, unresolved-import 1 |
| typescript | external 600, lexical 74, project-callable 1.076, project-value 4.405 | NodeJS.ProcessEnv's index signature: only execution knows the value 3, a member of a value of type any: only execution knows it 2.138, a member of an anonymous type, an object literal or an index signature another file declares: the index names it with a local of this file it defines nowhere 42, dan |

### Stati diversi da fresh

| Linguaggio | Stato | Casi | Motivo |
| --- | --- | --- | --- |
| c | unavailable | 1 | none of the 1 c files was parsed by the snapshot (lexical: 1) |
| cpp | failed | 1 | scip-clang wrote no index (src/currency: the configure ended with exit code 1; FetchContent asked for nothing; file(DOWNLOAD) and ExternalProject are not recorded): compiler: /usr/bin/cc - skipped -- Detecting C compile features -- Detecting C compile features - done -- Detecting CXX compiler ABI in |
| kotlin | failed | 1 | none of the 3 kotlin files is in the index: Gradle script: no KotlinCompile task compiles it (2), no Kotlin compile task of the build lists it (1) |
| kotlin | failed | 1 | scip-java wrote no index (preparation exited with code 1): lems/problems-report.html FAILURE: Build failed with an exception. * What went wrong: 8 actionable tasks: 6 executed, 2 up-to-date Execution failed for task ':app:processFreeDebugGoogleServices'. > File google-services.json is missing. The G |
| kotlin | failed | 1 | scip-java wrote no index (preparation exited with code 1): FAILURE: Build failed with an exception. * What went wrong: Execution failed for task ':app:processDebugGoogleServices'. > File google-services.json is missing. The Google Services Plugin cannot function without it. Searched locations: /work |

### Linguaggi fresh con file fuori dall'indice

| Caso | Linguaggio | Mancanti / nello snapshot | Motivi |
| --- | --- | --- | --- |
| real-svc-otel-demo | stylesheet | 7 / 160 | template language: no reader (7) |

### Linguaggi senza analizzatore

| Linguaggio | Casi | File |
| --- | --- | --- |
| sql | 1 | 1 |

## Pre-mappa

| Faccetta | Casi che la danno | Casi che non la danno | Trovate | Attese | In più | Sbagliate |
| --- | --- | --- | --- | --- | --- | --- |
| languages | 3 | 0 | 30 | 30 | 27 | 0 |
| languages.files | 0 | 3 | 0 | 0 | 0 | 0 |
| excluded | 3 | 0 | 50 | 58 | 14 | 0 |
| units | 3 | 0 | 34 | 37 | 0 | 1 |
| units.depends_on | 3 | 0 | 2 | 8 | 0 | 0 |
| units.source_roots | 2 | 1 | 8 | 51 | 2 | 0 |
| units.config | 3 | 0 | 7 | 66 | 0 | 3 |
| workspace | 3 | 0 | 3 | 4 | 4 | 0 |
| workspace.members | 3 | 0 | 6 | 7 | 1 | 0 |
| toolchains | 3 | 0 | 27 | 77 | 21 | 0 |
| dependencies | 0 | 3 | 0 | 0 | 0 | 0 |
| frameworks | 0 | 3 | 0 | 0 | 0 | 0 |
| services | 0 | 3 | 0 | 0 | 0 | 0 |
| needs | 0 | 3 | 0 | 0 | 0 | 0 |

## Gap

| Passo | Tipo | Numero | Esempi |
| --- | --- | --- | --- |
| scan | no_analyzer | 6 | real-svc-otel-demo: 1 Batchfile files and no analyzer lists the language: their code is in no graph<br>real-svc-otel-demo: 30 Dockerfile files and no analyzer lists the language: their code is in no graph<br>real-svc-otel-demo: 38 Elixir files and no analyzer lists the language: their code is in no graph |
| scan | toolchain_undeclared | 5 | real-svc-otel-demo: src/ad: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build<br>real-svc-otel-demo: src/fraud-detection: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build<br>real-svc-otel-demo: src/recommendation: the Java version of a Gradle build is declared in its build scripts, which only Gradle runs: no source states it before the build |
| scan | code_outside_units | 3 | real-svc-otel-demo: internal/tools: 2 Python files that no unit of kind python-project holds<br>real-svc-otel-demo: src/shared: 1 Python files that no unit of kind python-project holds<br>mix-poly-firebase: shared: 2 TypeScript files that no unit of kind npm-package holds |
| scan | model_failed | 3 | real-svc-otel-demo: src/react-native-app/tsconfig.json: tsc --showConfig: tsconfig.json(2,14): error TS6053: File 'expo/tsconfig.base' not found.<br>real-svc-otel-demo: src/currency: cmake configure: CMake Error at CMakeLists.txt:7 (find_package): Could not find a package configuration file provided by "Protobuf" with any of the following names: Protobuf.cps protobuf.cps ProtobufConfig.cmake protobuf-config.cmake Add the installation prefix of "<br>real-svc-otel-demo: src/currency/genproto: cmake configure: CMake Error at CMakeLists.txt:4 (find_package): Could not find a package configuration file provided by "Protobuf" with any of the following names: Protobuf.cps protobuf.cps ProtobufConfig.cmake protobuf-config.cmake Add the installation pr |
| scan | not_executed | 3 | real-svc-otel-demo: src/frontend/package.json: install scripts are not run (cypress, protobufjs): what they generate is unknown<br>real-svc-otel-demo: src/payment/package.json: install scripts are not run (protobufjs): what they generate is unknown<br>mix-poly-firebase: react-app/src-tauri/build.rs: a build script is present and Daodan's index does not run it: the code it generates and the cfg flags it sets are unknown |
| scan | restore_failed | 3 | real-svc-otel-demo: src/frontend: its packages are not installed: no workspace above names this folder<br>real-svc-otel-demo: src/payment: its packages are not installed: no workspace above names this folder<br>real-svc-otel-demo: src/react-native-app: its packages are not installed: no workspace above names this folder |
| scan | model_partial | 1 | mix-poly-firebase: react-app/src-tauri: registries unknown: cargo metadata --locked: Updating crates.io index error: cannot create the lock file /work/react-app/src-tauri/Cargo.lock because --locked was passed to prevent this help: to generate the lock file without accessing the network, remove the  |
| scan | ownership_ambiguous | 1 | real-svc-otel-demo: src/react-native-app: Directory scope cannot distinguish build ownership: react-native-app@src/react-native-app, react-native-app@src/react-native-app+ |
| analyze | workspace_failure | 28 | real-svc-otel-demo: src/cart/cart.slnx: Msbuild failed when processing the file '/work/src/cart/tests/cart.tests.csproj' with message: Package Microsoft.TestPlatform.ObjectModel 18.11.0 has a resource with the locale 'cs'. This locale is not recognized by .NET. Consider notifying the package author <br>real-svc-otel-demo: src/cart/cart.slnx: Msbuild failed when processing the file '/work/src/cart/tests/cart.tests.csproj' with message: Package Microsoft.TestPlatform.ObjectModel 18.11.0 has a resource with the locale 'de'. This locale is not recognized by .NET. Consider notifying the package author <br>real-svc-otel-demo: src/cart/cart.slnx: Msbuild failed when processing the file '/work/src/cart/tests/cart.tests.csproj' with message: Package Microsoft.TestPlatform.ObjectModel 18.11.0 has a resource with the locale 'es'. This locale is not recognized by .NET. Consider notifying the package author  |
| analyze | manifest_unread | 6 | real-svc-otel-demo: src/agent/requirements.in: the environment reads pyproject.toml, uv.lock and requirements*.txt: the packages this file declares are not installed<br>real-svc-otel-demo: src/chatbot/requirements.in: the environment reads pyproject.toml, uv.lock and requirements*.txt: the packages this file declares are not installed<br>real-svc-otel-demo: src/load-generator/requirements.in: the environment reads pyproject.toml, uv.lock and requirements*.txt: the packages this file declares are not installed |
| analyze | restore_failed | 3 | real-svc-otel-demo: src/frontend: its packages are not installed: no workspace above names this folder<br>real-svc-otel-demo: src/payment: its packages are not installed: no workspace above names this folder<br>real-svc-otel-demo: src/react-native-app: its packages are not installed: no workspace above names this folder |
| analyze | build_input_missing | 2 | jvm-android-app-lib: .: the build stopped without google-services.json, which the Google Services Gradle plugin (com.google.gms.google-services) reads: the Firebase project's configuration, which a developer downloads from the Firebase console, kept out of the repository; Daodan makes none, so the b<br>mix-poly-firebase: android: the build stopped without google-services.json, which the Google Services Gradle plugin (com.google.gms.google-services) reads: the Firebase project's configuration, which a developer downloads from the Firebase console, kept out of the repository; Daodan makes none, so t |
| analyze | build_not_indexed | 2 | real-svc-otel-demo: src/fraud-detection: src/fraud-detection: failed: scip-java wrote no index (preparation exited with code 1): eldemo'. Location: /work/src/fraud-detection/src/main/kotlin/frauddetection/main.kt:14 Deprecated Gradle features were used in this build, making it incompatible with Grad<br>real-svc-otel-demo: src/fraud-detection: src/fraud-detection: failed: scip-java wrote no index (preparation exited with code 1): eldemo'. Location: /work/src/fraud-detection/src/main/kotlin/frauddetection/main.kt:14 * Try: > Run with --stacktrace option to get the stack trace. > Run with --info or - |

## Container

- Corse: 44; secondi: 719,5.

| Fase | Corse | Secondi |
| --- | --- | --- |
| execute | 24 | 243,3 |
| prepare | 20 | 476,2 |

### Esiti diversi da exit 0

Nessuno.
