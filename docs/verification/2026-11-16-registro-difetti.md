# Registro dei difetti dal 13 novembre 2026

Ogni difetto e buco trovato nel plugin codebase-map dal 13 novembre 2026, con la causa, il rimedio e la prova. Ogni campo viene dal commit, dal risultato di un giro o dal codice. Una scheda si aggiunge con il commit che corregge o dichiara il difetto.

Convenzioni:

- Gli id non cambiano: una scheda nuova prende il numero libero successivo e sta nella sua area.
- I percorsi `scripts/…` stanno sotto `plugins/codebase-map/skills/map/`.
- I giri della pipeline, tutti del 16 novembre 2026, stanno in `benchmarks/project-model/results/pipeline/2026-11-16-<giro>.json`, con il rapporto `.report.md` accanto:
  - `fixtures`: 104 progetti in miniatura (`68d8f4c59`);
  - `real-3`: chi, javapoet e tududi (`7532ed2e7`);
  - `giro-2`: i 15 repository veri restanti e 12 fixture corrette (`b41e0d6e8`);
  - `finale`: 122 casi, sul codice fino a `492a7b212` (`ee1e83fc8`);
  - `java-versions`: le 18 `jvm-ver-*`, sul codice a `68a846a4a` (`347bc1403`);
  - `conferma`: 32 casi (`828b5413b`);
  - `jvm-otel-android`: otel-demo, jvm-android-app-lib e mix-poly-firebase, sull'albero di lavoro con il codice poi committato in `39805f5e7`;
  - `jvm-kotlinconf`: kotlinconf, sull'albero di lavoro con il codice poi committato in `22dca6da8`;
  - `jvm-kotlinconf-kmp`: kotlinconf, sull'albero di lavoro delle 20:18 con il codice poi committato in `a13d55787`;
  - `dotenv`: tududi e fastapi, con i `.env` tracciati nella copia del container (`b1f14ac08`);
  - `ci-steps`: tududi e fastapi, con i passi della CI prima dei test (`aea1c8c3b`).
- Nessun risultato registra il codice di Daodan su cui il giro è girato (D-251): il codice del `finale` lo dice il README del benchmark (`benchmarks/project-model/README.md:174`), quello di `java-versions` il commit `347bc1403`, quello dei due giri JVM chi li ha fatti; degli altri giri, nessun testo.
- I repository veri sono fissati a un commit in `benchmarks/project-model/fixtures/<caso>/source.json`:
  - chi `c64ed7d6635f`, javapoet `b9017a9503b7`, klaxon `1173bdc568a6`, python-semver `b6e83e3e40d3`, semver `280ebcb6edac`, tinyxml2 `9148bdf719e9`, tududi `71da9d7b34df`, zlib `51b7f2abdade`;
  - fastapi `aabb90126964`, hoppscotch `55908a76a1d0`, jhipster-sample `6b000b5d23a3`, kotlinconf `146e891c150c`, memos `509e41bd1a1b`;
  - eShop `913acea66708`, otel-demo `b825c7c25726`, petclinic-microservices `e8b747ab5227`, robot-shop `55292e2199f2`, voting-app `63e9150ca17a`.
- Stato:
  - risolto;
  - aperto, con chi ci lavora dove qualcuno ci lavora;
  - buco dichiarato: un limite che il risultato dice, con il nome della lacuna.
- Verifica:
  - «solo test»: lo confermano solo le suite, che dal commit `233618aa1` girano su Modal;
  - «da verificare»: nessun commit o risultato lo prova ancora;
  - «in stage»: il lavoro è nell'indice di git, non ancora in un commit.
- La regola invalicabile di `AGENTS.md` (`2753088a3`, poi `ae7fd8270`): il codice del progetto analizzato gira solo nel container di Daodan, mai sull'host, e ogni strumento che Daodan lancia sull'host ha un test con un file del progetto che, se eseguito, lascia un segno. Le schede del codice del progetto sull'host: D-161 (Tailwind), D-239 (rust-analyzer), D-245 e D-250 (Git), D-248 e D-253 (l'ambiente Python), D-256 (i formattatori), D-257 (Go), D-258 (Vue e Svelte).
- Tag: ogni scheda ha una riga con cinque voci, che l'«Indice dei tag» raccoglie:
  - lingua: i linguaggi del difetto, `tutti` se non dipende da un linguaggio;
  - area: `pre-mappa`, `snapshot`, `preparazione`, `host`, `parser`, `analizzatore`, `passo dinamico`, `container`, `servizi`, `driver Modal`, `explorer`, `benchmark` o `documenti`;
  - tipo: `sicurezza`, `correttezza`, `completezza`, `prestazioni`, `costo`, `documentazione` o `benchmark`;
  - origine: ciò che l'ha trovato. Può essere un giro, `corpus della pre-mappa` (la misura sui 122 progetti), `prova su Modal`, `prova sull'host`, `corsa su un progetto` (un progetto fuori dai giri), `review`, `test` o `spec`; se lo descrive solo il commit che lo corregge, è `commit`;
  - strumento: gli strumenti che il difetto coinvolge, `—` se nessuno.
  - come sono fatte: una regola le ha proposte dalle parole della scheda (il nome, «Descrizione», «Spiegazione» e «Progetto e caso»); il 16 novembre ogni riga è stata letta contro la sua scheda e corretta a mano dove la regola sbagliava, 108 righe su 251. Una scheda nuova ha la sua riga scritta a mano.
- Le sezioni «Indice dei tag», «Indice», le tabelle di «Buchi trovati» e di «Progetti di prova» si scrivono dalle schede, dai rapporti dei giri e dalle fixture; il resto si scrive a mano.
- Il commit `b6f276fee` e il benchmark `f63ed542d` sono di senior-review e restano fuori. I commit feat che non correggono nulla sono elencati in fondo.

## Indice dei tag

### Lingua

- `tutti` (63): D-001, D-004, D-005, D-018, D-019, D-022, D-023, D-024, D-031, D-032, D-033, D-034, D-035, D-036, D-037, D-038, D-039, D-062, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-081, D-082, D-115, D-149, D-167, D-168, D-172, D-182, D-196, D-201, D-202, D-203, D-204, D-205, D-206, D-207, D-211, D-212, D-213, D-214, D-215, D-216, D-217, D-218, D-219, D-222, D-228, D-233, D-234, D-235, D-243, D-244, D-245, D-250, D-251, D-260, D-261, D-262
- `java` (44): D-003, D-016, D-025, D-026, D-027, D-044, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-099, D-100, D-101, D-102, D-103, D-104, D-105, D-106, D-108, D-109, D-111, D-112, D-178, D-179, D-181, D-208, D-220, D-221, D-223, D-224, D-226, D-229
- `kotlin` (34): D-016, D-027, D-044, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-089, D-091, D-092, D-093, D-094, D-095, D-096, D-097, D-098, D-103, D-105, D-106, D-107, D-108, D-109, D-110, D-166, D-180, D-208, D-221, D-223, D-229
- `python` (33): D-006, D-007, D-028, D-042, D-047, D-048, D-049, D-052, D-059, D-074, D-075, D-084, D-085, D-086, D-087, D-088, D-169, D-183, D-184, D-188, D-197, D-199, D-200, D-231, D-232, D-240, D-246, D-247, D-248, D-252, D-253, D-254, D-256
- `c` (31): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-130, D-131, D-132, D-133, D-134, D-136, D-137, D-142, D-177, D-209, D-210, D-227, D-229, D-230, D-236, D-255, D-259
- `cpp` (30): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-130, D-131, D-132, D-133, D-135, D-137, D-177, D-209, D-210, D-227, D-229, D-230, D-236, D-240, D-255, D-259
- `javascript` (30): D-013, D-017, D-021, D-046, D-049, D-051, D-053, D-056, D-059, D-072, D-147, D-148, D-156, D-158, D-170, D-171, D-185, D-186, D-187, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-198, D-225, D-229, D-256
- `typescript` (21): D-008, D-009, D-029, D-072, D-073, D-129, D-145, D-146, D-147, D-150, D-151, D-152, D-156, D-157, D-160, D-170, D-194, D-197, D-198, D-229, D-256
- `rust` (18): D-014, D-021, D-030, D-040, D-041, D-078, D-143, D-144, D-173, D-175, D-176, D-209, D-227, D-230, D-237, D-238, D-239, D-256
- `csharp` (17): D-010, D-021, D-049, D-113, D-114, D-116, D-117, D-118, D-119, D-120, D-165, D-198, D-220, D-229, D-241, D-242, D-249
- `go` (14): D-002, D-020, D-045, D-078, D-079, D-138, D-139, D-140, D-141, D-142, D-173, D-174, D-256, D-257
- `svelte` (5): D-080, D-153, D-156, D-159, D-258
- `vue` (5): D-080, D-154, D-155, D-159, D-258
- `css` (4): D-161, D-162, D-163, D-164
- `scala` (2): D-011, D-092
- `dart` (1): D-015
- `elixir` (1): D-012
- `php` (1): D-015
- `ruby` (1): D-059
- `swift` (1): D-030

### Area

- `analizzatore` (114): D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-072, D-073, D-074, D-075, D-076, D-077, D-078, D-079, D-080, D-081, D-082, D-083, D-084, D-085, D-086, D-087, D-088, D-089, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-097, D-098, D-099, D-100, D-101, D-102, D-103, D-104, D-105, D-106, D-107, D-108, D-109, D-110, D-111, D-112, D-113, D-114, D-115, D-116, D-117, D-118, D-119, D-120, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-129, D-130, D-131, D-132, D-133, D-134, D-135, D-136, D-137, D-138, D-139, D-140, D-141, D-142, D-143, D-144, D-145, D-146, D-147, D-148, D-149, D-150, D-151, D-152, D-153, D-154, D-155, D-156, D-157, D-158, D-159, D-160, D-161, D-162, D-163, D-164, D-236, D-237, D-238, D-239, D-242, D-246, D-247, D-248, D-249, D-253, D-255, D-257, D-258, D-259
- `pre-mappa` (39): D-001, D-002, D-003, D-004, D-005, D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-015, D-016, D-017, D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-029, D-030, D-043, D-046, D-055, D-056, D-057, D-058, D-060, D-061, D-062
- `passo dinamico` (34): D-167, D-168, D-169, D-170, D-171, D-172, D-173, D-174, D-175, D-176, D-177, D-178, D-179, D-180, D-181, D-183, D-184, D-185, D-186, D-187, D-188, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-196, D-197, D-198, D-199, D-200, D-241
- `servizi` (13): D-182, D-201, D-202, D-212, D-213, D-214, D-215, D-216, D-217, D-240, D-244, D-260, D-261
- `benchmark` (12): D-220, D-221, D-223, D-224, D-225, D-226, D-228, D-233, D-234, D-235, D-243, D-251
- `container` (11): D-064, D-203, D-204, D-205, D-206, D-207, D-208, D-210, D-218, D-219, D-262
- `preparazione` (11): D-044, D-045, D-047, D-048, D-049, D-050, D-051, D-052, D-053, D-054, D-063
- `snapshot` (9): D-031, D-032, D-033, D-034, D-035, D-059, D-245, D-250, D-252
- `host` (8): D-036, D-038, D-039, D-040, D-041, D-042, D-254, D-256
- `documenti` (6): D-222, D-227, D-229, D-230, D-231, D-232
- `parser` (3): D-037, D-165, D-166
- `driver Modal` (1): D-209
- `explorer` (1): D-211

### Tipo

- `completezza` (139): D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-017, D-021, D-029, D-033, D-035, D-043, D-044, D-046, D-047, D-048, D-049, D-050, D-052, D-053, D-054, D-055, D-059, D-061, D-062, D-066, D-068, D-069, D-072, D-073, D-074, D-075, D-076, D-078, D-082, D-085, D-088, D-089, D-091, D-092, D-093, D-094, D-096, D-098, D-099, D-100, D-102, D-103, D-104, D-107, D-108, D-109, D-111, D-112, D-114, D-116, D-117, D-118, D-119, D-125, D-126, D-127, D-130, D-131, D-132, D-133, D-134, D-135, D-136, D-137, D-138, D-139, D-140, D-141, D-142, D-143, D-144, D-147, D-148, D-149, D-150, D-151, D-152, D-155, D-156, D-157, D-158, D-159, D-160, D-162, D-164, D-165, D-166, D-169, D-170, D-171, D-172, D-173, D-176, D-180, D-181, D-182, D-185, D-186, D-190, D-191, D-193, D-194, D-195, D-196, D-197, D-198, D-199, D-200, D-201, D-202, D-207, D-208, D-209, D-210, D-212, D-213, D-214, D-216, D-217, D-218, D-236, D-237, D-240, D-241, D-247, D-249, D-252, D-260, D-261, D-262
- `correttezza` (83): D-001, D-002, D-003, D-004, D-005, D-015, D-016, D-018, D-019, D-020, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-030, D-031, D-036, D-037, D-038, D-039, D-045, D-051, D-056, D-057, D-058, D-060, D-065, D-067, D-070, D-071, D-077, D-079, D-080, D-081, D-083, D-084, D-086, D-087, D-090, D-095, D-097, D-101, D-105, D-106, D-110, D-113, D-115, D-120, D-121, D-122, D-124, D-128, D-129, D-145, D-146, D-153, D-154, D-163, D-167, D-168, D-174, D-175, D-177, D-178, D-179, D-183, D-184, D-188, D-192, D-206, D-211, D-215, D-219, D-238, D-242, D-244, D-246, D-254, D-255, D-259
- `sicurezza` (21): D-032, D-034, D-040, D-041, D-042, D-063, D-064, D-161, D-203, D-204, D-205, D-229, D-239, D-240, D-245, D-248, D-250, D-253, D-256, D-257, D-258
- `benchmark` (12): D-220, D-221, D-223, D-224, D-225, D-226, D-228, D-233, D-234, D-235, D-243, D-251
- `documentazione` (6): D-222, D-227, D-229, D-230, D-231, D-232
- `prestazioni` (3): D-123, D-187, D-189

### Origine

- `commit` (110): D-032, D-033, D-034, D-035, D-037, D-044, D-045, D-046, D-047, D-048, D-049, D-050, D-051, D-052, D-053, D-054, D-055, D-060, D-061, D-062, D-063, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-100, D-101, D-121, D-122, D-123, D-124, D-125, D-127, D-128, D-129, D-130, D-131, D-134, D-138, D-139, D-145, D-146, D-147, D-148, D-149, D-150, D-151, D-152, D-153, D-154, D-155, D-157, D-161, D-165, D-166, D-167, D-168, D-170, D-171, D-172, D-173, D-174, D-175, D-177, D-180, D-184, D-185, D-186, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-201, D-202, D-204, D-207, D-208, D-210, D-213, D-214, D-215, D-220, D-221, D-223, D-224, D-225, D-227, D-228, D-231, D-232, D-233, D-234, D-238, D-242, D-243, D-246, D-247, D-248, D-252, D-253, D-259, D-260, D-261, D-262
- `corpus della pre-mappa` (31): D-001, D-002, D-003, D-004, D-005, D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-015, D-016, D-017, D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-029, D-030, D-235
- `finale` (31): D-056, D-059, D-088, D-097, D-098, D-105, D-106, D-108, D-111, D-112, D-114, D-126, D-132, D-133, D-135, D-137, D-140, D-141, D-142, D-143, D-144, D-156, D-159, D-160, D-162, D-164, D-183, D-188, D-197, D-198, D-241
- `review` (28): D-064, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-072, D-073, D-074, D-075, D-076, D-077, D-078, D-079, D-080, D-081, D-082, D-203, D-205, D-217, D-218, D-251, D-254, D-256, D-257, D-258
- `prova su Modal` (17): D-089, D-102, D-103, D-104, D-115, D-116, D-117, D-118, D-119, D-120, D-169, D-179, D-236, D-237, D-239, D-249, D-255
- `prova sull'host` (10): D-036, D-038, D-039, D-040, D-041, D-042, D-084, D-086, D-245, D-250
- `spec` (7): D-199, D-200, D-212, D-216, D-219, D-229, D-230
- `conferma` (5): D-057, D-058, D-136, D-158, D-187
- `corsa su un progetto` (5): D-031, D-043, D-085, D-087, D-206
- `test` (4): D-083, D-211, D-222, D-244
- `fixtures` (3): D-176, D-196, D-209
- `real-3` (3): D-099, D-178, D-182
- `giro-2` (2): D-113, D-163
- `java-versions` (2): D-181, D-226
- `jvm-otel-android` (2): D-107, D-109
- `ci-steps` (1): D-240
- `jvm-kotlinconf` (1): D-110

### Strumento

- `Gradle` (28): D-016, D-027, D-044, D-049, D-050, D-054, D-055, D-058, D-063, D-064, D-089, D-090, D-094, D-095, D-097, D-098, D-101, D-103, D-104, D-105, D-106, D-107, D-108, D-109, D-110, D-180, D-221, D-223
- `Maven` (16): D-003, D-025, D-026, D-049, D-054, D-063, D-064, D-089, D-090, D-091, D-095, D-100, D-102, D-112, D-221, D-226
- `npm` (13): D-013, D-017, D-049, D-053, D-056, D-072, D-084, D-185, D-186, D-191, D-198, D-201, D-258
- `scip-java` (10): D-089, D-096, D-098, D-099, D-100, D-101, D-103, D-105, D-108, D-110
- `uv` (10): D-042, D-047, D-049, D-184, D-188, D-246, D-248, D-252, D-253, D-254
- `CMake` (9): D-060, D-061, D-076, D-122, D-124, D-125, D-131, D-132, D-135
- `Cargo` (6): D-014, D-021, D-030, D-041, D-175, D-239
- `Compose` (6): D-201, D-212, D-214, D-215, D-240, D-261
- `Docker` (6): D-046, D-107, D-135, D-140, D-141, D-240
- `git` (6): D-048, D-126, D-204, D-245, D-250, D-257
- `GitHub Actions` (6): D-056, D-182, D-201, D-213, D-260, D-261
- `scip-dotnet` (6): D-113, D-114, D-116, D-118, D-119, D-249
- `scip-python` (6): D-084, D-086, D-088, D-246, D-247, D-248
- `scip-typescript` (6): D-146, D-147, D-148, D-152, D-156, D-160
- `Modal` (5): D-209, D-210, D-224, D-230, D-251
- `rust-analyzer` (5): D-041, D-143, D-144, D-237, D-239
- `scip-clang` (5): D-123, D-131, D-132, D-236, D-255
- `tree-sitter` (5): D-034, D-035, D-036, D-037, D-117
- `Conan` (4): D-029, D-061, D-125, D-177
- `GitLab CI` (4): D-202, D-212, D-216, D-217
- `javac` (4): D-100, D-101, D-102, D-104
- `pnpm` (4): D-021, D-049, D-051, D-072
- `Pyright` (4): D-074, D-088, D-247, D-248
- `Roslyn` (4): D-113, D-115, D-116, D-249
- `scip-go` (4): D-139, D-140, D-141, D-142
- `Yarn` (4): D-049, D-051, D-072, D-157
- `Android SDK` (3): D-044, D-108, D-223
- `Bazel` (3): D-029, D-060, D-092
- `Kiri` (3): D-043, D-218, D-219
- `Make` (3): D-043, D-060, D-133
- `MSBuild` (3): D-076, D-113, D-120
- `rustup` (3): D-040, D-041, D-239
- `Valgrind` (3): D-176, D-209, D-227
- `Bear` (2): D-133, D-210
- `Bun` (2): D-056, D-195
- `Deno` (2): D-008, D-029
- `dotnet` (2): D-113, D-241
- `Jest` (2): D-185, D-187
- `NuGet` (2): D-021, D-049
- `pip` (2): D-049, D-188
- `protoc` (2): D-107, D-112
- `pytest` (2): D-169, D-183
- `rustc` (2): D-041, D-175
- `sbt` (2): D-011, D-092
- `Tailwind` (2): D-161, D-162
- `tsc` (2): D-072, D-115
- `Turborepo` (2): D-190, D-191
- `vcpkg` (2): D-125, D-177
- `Angular` (1): D-194
- `apt` (1): D-262
- `autotools` (1): D-134
- `biome` (1): D-256
- `black` (1): D-256
- `BuildKit` (1): D-135
- `Composer` (1): D-015
- `Corepack` (1): D-051
- `Error Prone` (1): D-100
- `GCC` (1): D-255
- `gcc` (1): D-257
- `go` (1): D-257
- `gofmt` (1): D-256
- `Google Services` (1): D-109
- `Helm` (1): D-029
- `Jedi` (1): D-231
- `Launchpad` (1): D-176
- `Meson` (1): D-060
- `Mix` (1): D-012
- `pip-compile` (1): D-028
- `prettier` (1): D-256
- `pub` (1): D-015
- `Renovate` (1): D-046
- `ruff` (1): D-256
- `rustfmt` (1): D-256
- `SvelteKit` (1): D-156
- `SwiftPM` (1): D-030
- `Terraform` (1): D-029
- `tox` (1): D-183
- `typescript-language-server` (1): D-258
- `Vitest` (1): D-194

## Indice

262 schede: 201 risolte, 23 aperte, 38 buchi dichiarati.

### Pre-mappa, snapshot e preparazione

68 schede: 61 risolto, 1 aperto, 6 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-001 | Due build system nella stessa cartella fusi in un'unità | corpus della pre-mappa | risolto | `708eae48f` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-002 | Go: requisiti indiretti letti e moduli legati fuori da un workspace | corpus della pre-mappa | risolto | `708eae48f` | go · pre-mappa · correttezza · corpus della pre-mappa |
| D-003 | Maven: dipendenze non lette come gruppo:artefatto e profili taciuti | corpus della pre-mappa | risolto | `708eae48f` | java · pre-mappa · correttezza · corpus della pre-mappa · Maven |
| D-004 | Un glob di workspace crea un'unità per cartella | corpus della pre-mappa | risolto | `708eae48f` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-005 | Un bersaglio ambiguo scelto invece che dichiarato | corpus della pre-mappa | risolto | `708eae48f` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-006 | Gruppi di sviluppo di pyproject non letti | corpus della pre-mappa | risolto | `a04ab36e1` | python · pre-mappa · completezza · corpus della pre-mappa |
| D-007 | setup.cfg non letto | corpus della pre-mappa | risolto | `a04ab36e1` | python · pre-mappa · completezza · corpus della pre-mappa |
| D-008 | Import map di Deno non lette | corpus della pre-mappa | risolto | `a04ab36e1` | typescript · pre-mappa · completezza · corpus della pre-mappa · Deno |
| D-009 | angular.json non letto | corpus della pre-mappa | risolto | `a04ab36e1` | typescript · pre-mappa · completezza · corpus della pre-mappa |
| D-010 | Soluzioni .NET fuori dalla radice non lette | corpus della pre-mappa | risolto | `a04ab36e1` | csharp · pre-mappa · completezza · corpus della pre-mappa |
| D-011 | Sottoprogetti sbt non letti | corpus della pre-mappa | risolto | `a04ab36e1` | scala · pre-mappa · completezza · corpus della pre-mappa · sbt |
| D-012 | Umbrella di Mix non letto | corpus della pre-mappa | risolto | `a04ab36e1` | elixir · pre-mappa · completezza · corpus della pre-mappa · Mix |
| D-013 | Dipendenze `file:` di npm non lette dal lettore dei moduli | corpus della pre-mappa | risolto | `a04ab36e1` | javascript · pre-mappa · completezza · corpus della pre-mappa · npm |
| D-014 | Rinomina e tabelle target di Cargo non lette | corpus della pre-mappa | risolto | `a04ab36e1` | rust · pre-mappa · completezza · corpus della pre-mappa · Cargo |
| D-015 | Requisiti di piattaforma di Composer e SDK di pub contati come dipendenze | corpus della pre-mappa | risolto | `a04ab36e1` | php, dart · pre-mappa · correttezza · corpus della pre-mappa · Composer, pub |
| D-016 | Un build incluso contato come membro del workspace | corpus della pre-mappa | risolto | `a04ab36e1`, `9c17c7686` | java, kotlin · pre-mappa · correttezza · corpus della pre-mappa · Gradle |
| D-017 | Pacchetti locali `file:` di npm senza archi nella pre-mappa | js-local-and-git-deps | risolto | `db45bcc93` | javascript · pre-mappa · completezza · corpus della pre-mappa · npm |
| D-018 | Una dipendenza di un file centrale data all'unità più vicina | eShop e il corpus della pre-mappa | risolto | `de353d251` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-019 | Un arco fra unità contato anche come dipendenza | corpus della pre-mappa | risolto | `99112d0b9` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-020 | Go: un arco fra moduli senza replace né go.work | corpus della pre-mappa | risolto | `99112d0b9` | go · pre-mappa · correttezza · corpus della pre-mappa |
| D-021 | Una versione scritta in un file centrale non completava la voce dell'unità | corpus della pre-mappa | risolto | `99112d0b9` | javascript, csharp, rust · pre-mappa · completezza · corpus della pre-mappa · pnpm, Cargo, NuGet |
| D-022 | Un vincolo dichiarato contato come pacchetto | corpus della pre-mappa | risolto | `99112d0b9` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-023 | Script, task, replace e import verso un percorso contati come pacchetti | corpus della pre-mappa | risolto | `99112d0b9` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-024 | Una toolchain diversa da quella che il file scrive | corpus della pre-mappa | risolto | `99112d0b9` | tutti · pre-mappa · correttezza · corpus della pre-mappa |
| D-025 | Il wrapper Maven dava sé stesso invece di Maven | corpus della pre-mappa | risolto | `99112d0b9` | java · pre-mappa · correttezza · corpus della pre-mappa · Maven |
| D-026 | POM genitore e BOM importato senza scope parent e bom | corpus della pre-mappa | risolto | `99112d0b9` | java · pre-mappa · correttezza · corpus della pre-mappa · Maven |
| D-027 | Uno scope dato alle dipendenze di Gradle | corpus della pre-mappa | risolto | `99112d0b9` | java, kotlin · pre-mappa · correttezza · corpus della pre-mappa · Gradle |
| D-028 | Un file di pip-compile contato come dichiarazione | corpus della pre-mappa | risolto | `99112d0b9` | python · pre-mappa · correttezza · corpus della pre-mappa · pip-compile |
| D-029 | Pacchetti di Bazel, Helm, Terraform, Conan e Deno non dichiarati | corpus della pre-mappa | risolto | `99112d0b9` | typescript, c, cpp · pre-mappa · completezza · corpus della pre-mappa · Deno, Bazel, Conan, Helm, Terraform |
| D-030 | Cargo e SwiftPM: il pacchetto con un nome diverso da quello del build tool | corpus della pre-mappa | risolto | `99112d0b9` | rust, swift · pre-mappa · correttezza · corpus della pre-mappa · Cargo, SwiftPM |
| D-031 | Un collegamento simbolico a un file del progetto: «UNIQUE constraint failed: files.path» | python-semver (`b6e83e3e40d3`) | risolto | `ea92f3fed` | tutti · snapshot · correttezza · corsa su un progetto |
| D-032 | Un collegamento verso l'esterno portava dentro un file di fuori | snapshot | risolto | `ea92f3fed` | tutti · snapshot · sicurezza · commit |
| D-033 | Un collegamento rotto spariva senza traccia | snapshot | risolto | `ea92f3fed` | tutti · snapshot · completezza · commit |
| D-034 | Grammatiche scaricate da GitHub al primo uso, senza versione fissata | snapshot | risolto | `d6545b074` | tutti · snapshot · sicurezza · commit · tree-sitter |
| D-035 | Senza rete un file passava in silenzio al lettore a espressioni regolari | snapshot | risolto | `d6545b074` | tutti · snapshot · completezza · commit · tree-sitter |
| D-036 | Grammatiche scelte senza l'architettura del processo | host Windows | risolto | `68e39dcde` | tutti · host · correttezza · prova sull'host · tree-sitter |
| D-037 | Grammatiche piazzate fra processi senza sicurezza | parser | risolto | `d94f92470` | tutti · parser · correttezza · commit · tree-sitter |
| D-038 | La cartella condivisa di Daodan chiedeva la versione a Windows | host Windows | risolto | `bfdca190b` | tutti · host · correttezza · prova sull'host |
| D-039 | Il sistema e l'architettura chiesti a Windows con il modulo platform | host Windows | risolto | `b5d218801` | tutti · host · correttezza · prova sull'host |
| D-040 | Un rustup vecchio installava per conto di un progetto | host con rustup vecchio | buco dichiarato (Rust `unavailable`) | `b5d218801` | rust · host · sicurezza · prova sull'host · rustup |
| D-041 | Cargo, rustc e rust-analyzer installavano nella home dell'utente | host | risolto | `6856a0980` | rust · host · sicurezza · prova sull'host · Cargo, rustc, rust-analyzer, rustup |
| D-042 | uv scaricava interpreti e leggeva la configurazione del progetto | host | risolto | `6856a0980` | python · host · sicurezza · prova sull'host · uv |
| D-043 | I makefile erano «tipo di file non inventariato» | zlib e tinyxml2 su Kiri | risolto | `c6767743f` | c, cpp · pre-mappa · completezza · corsa su un progetto · Make, Kiri |
| D-044 | Android: compileSdk e buildToolsVersion non letti, SDK non installato | jvm-android-app-lib, mix-poly-firebase | risolto | `a633ebd72` | java, kotlin · preparazione · completezza · commit · Gradle, Android SDK |
| D-045 | Go: girava una versione diversa dalla più alta dichiarata | preparazione Go | risolto | `a633ebd72` | go · preparazione · correttezza · commit |
| D-046 | `node:22-alpine` non letto come Node 22 | pre-mappa delle immagini | risolto | `a633ebd72` | javascript · pre-mappa · completezza · commit · Docker, Renovate |
| D-047 | Gli errori di uv troncati | preparazione Python | risolto | `a633ebd72` | python · preparazione · completezza · commit · uv |
| D-048 | Dipendenze git di Python senza l'host né git | preparazione Python | risolto | `a633ebd72` | python · preparazione · completezza · commit · git |
| D-049 | I registri dichiarati assenti dalla pre-mappa | pre-mappa | risolto | `a633ebd72` | python, javascript, java, kotlin, csharp · preparazione · completezza · commit · uv, pip, npm, pnpm, Yarn, Gradle, Maven, NuGet |
| D-050 | Gradle avrebbe scaricato i JDK delle toolchain | build composte con toolchain 17 e 21 | risolto | `a633ebd72` | java, kotlin · preparazione · completezza · commit · Gradle |
| D-051 | pnpm e Yarn: «Cannot find matching keyid» | preparazione Node | risolto | `a94de85fb` | javascript · preparazione · correttezza · commit · Corepack, pnpm, Yarn |
| D-052 | Preparazione Python senza gli host dichiarati e senza il loro nome | preparazione Python | risolto | `2f0353c03` | python · preparazione · completezza · commit |
| D-053 | Dipendenze GitHub di npm senza gli host di download | preparazione Node | risolto | `2f0353c03` | javascript · preparazione · completezza · commit · npm |
| D-054 | Build JVM senza gli host che il progetto dichiara | javapoet (`b9017a9503b7`) | risolto | `609ca96dd` | java, kotlin · preparazione · completezza · commit · Gradle, Maven |
| D-055 | Il modello di Gradle senza i repository dei plugin delle impostazioni | kotlinconf (`146e891c150c`) | risolto | `17babc624` | java, kotlin · pre-mappa · completezza · commit · Gradle |
| D-056 | Bun dichiarato solo nei workflow non era una toolchain | fastapi (`aabb90126964`) | risolto | `5148e8eb3` | javascript · pre-mappa · correttezza · finale · npm, Bun, GitHub Actions |
| D-057 | L'immagine `devcontainers/java:1-21` letta come Java 1 | kotlinconf | risolto | `22dca6da8` | java, kotlin · pre-mappa · correttezza · conferma |
| D-058 | «Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.» | kotlinconf | risolto | `22dca6da8` | java, kotlin · pre-mappa · correttezza · conferma · Gradle |
| D-059 | Template ERB, Handlebars, Jinja e Nunjucks fuori dallo snapshot | snapshot | buco dichiarato (`template language | `e15f2ff88` | ruby, javascript, python · snapshot · completezza · finale |
| D-060 | Avviso «senza analyzer» per i linguaggi fatti solo di file di build | pre-mappa | risolto | `d14200dce` | c, cpp · pre-mappa · correttezza · commit · CMake, Meson, Bazel, Make |
| D-061 | Un profilo Conan che chiede una build dal sorgente | pre-mappa CMake con profili Conan | buco dichiarato (`restore_failed`) | `7b1e9ee9f` | c, cpp · pre-mappa · completezza · commit · Conan, CMake |
| D-062 | Senza container le fonti di modello non girano | scansione | buco dichiarato (`model_not_run`) | `8e85b2c1e` | tutti · pre-mappa · completezza · commit |
| D-063 | Un wrapper Gradle o Maven che punta a un host non ufficiale | build JVM | buco dichiarato (`unavailable`) | `f48df5c7d` | java, kotlin · preparazione · sicurezza · commit · Gradle, Maven |
| D-064 | Gradle raggiunge anche il Plugin Portal | perimetro di rete, dopo la revisione indipendente | buco dichiarato (perimetro di rete di Gradle) | `177dcae02` | java, kotlin · container · sicurezza · review · Gradle, Maven |
| D-245 | Git sull'host eseguiva il `core.fsmonitor` che il progetto configura | snapshot e copia per il container | risolto | `3f03a0929` | tutti · snapshot · sicurezza · prova sull'host · git |
| D-250 | `git status` sull'host eseguiva filtri e hook che il progetto configura | snapshot | risolto | `47d98fcde` | tutti · snapshot · sicurezza · prova sull'host · git |
| D-252 | Un file Python con una sintassi più nuova di quella di Daodan restava un errore di lettura | fastapi (`aabb90126964`) | risolto | `7ecbaed48` | python · snapshot · completezza · commit · uv |
| D-256 | Il riscrittore dei commenti esegue sull'host i formattatori sui file del progetto | riscrittore dei commenti | aperto (dynamic-step-2) | — | python, javascript, typescript, rust, go · host · sicurezza · review · prettier, biome, ruff, black, rustfmt, gofmt |

### Analizzatori

117 schede: 80 risolto, 13 aperto, 24 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-065 | Un linguaggio con 0 file indicizzati risultava `fresh` | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · correttezza · review |
| D-066 | I file mancanti di un linguaggio riuscito taciuti | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · completezza · review |
| D-067 | Un build o un run fallito accanto a uno riuscito spariva | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · correttezza · review |
| D-068 | Un linguaggio letto dallo snapshot senza analyzer non era dichiarato | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · completezza · review |
| D-069 | Le coppie di linguaggi che si chiamano non erano unite né dichiarate | audit della copertura | buco dichiarato (`not-joined`) | `2bc7c7459` | tutti · analizzatore · completezza · review |
| D-070 | La tabella «chi indicizza cosa» della pre-mappa scritta a mano | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · correttezza · review |
| D-071 | Linguaggio senza file con AST, e un linguaggio non elencato `fresh` per difetto | audit della copertura | risolto | `2bc7c7459` | tutti · analizzatore · correttezza · review |
| D-072 | TypeScript: alias di percorso e membri del workspace non presi dalla pre-mappa | audit della copertura, «stessa famiglia di Kotlin sotto Maven» | risolto | `64edfb930` | typescript, javascript · analizzatore · completezza · review · tsc, npm, pnpm, Yarn |
| D-073 | TypeScript: installazione fallita e dipendenza locale scartata taciute | audit della copertura | risolto | `64edfb930` | typescript · analizzatore · completezza · review |
| D-074 | Python: cartelle sorgenti e manifest dichiarati non passati a Pyright | audit della copertura | risolto | `64edfb930` | python · analizzatore · completezza · review · Pyright |
| D-075 | Python: un file fuori da ogni progetto senza motivo | audit della copertura | risolto | `64edfb930` | python · analizzatore · completezza · review |
| D-076 | C/C++: MSBuild trattato a parte | audit della copertura | risolto | `64edfb930` | c, cpp · analizzatore · completezza · review · CMake, MSBuild |
| D-077 | C/C++: un configure senza compile_commands.json faceva morire lo stadio | audit della copertura | risolto | `64edfb930` | c, cpp · analizzatore · correttezza · review |
| D-078 | Rust e Go: un file senza documento non diceva se il run era fallito | audit della copertura | risolto | `64edfb930` | go, rust · analizzatore · completezza · review |
| D-079 | Go: la regola dei nomi dei file (_GOOS, _GOARCH) non conosciuta | audit della copertura | risolto | `64edfb930` | go · analizzatore · correttezza · review |
| D-080 | Vue e Svelte: un componente con template non dichiarato letto in parte | audit della copertura | risolto | `64edfb930` | vue, svelte · analizzatore · correttezza · review |
| D-081 | Lo stadio di posizione rispondeva per linguaggi non suoi | audit della copertura | risolto | `64edfb930` | tutti · analizzatore · correttezza · review |
| D-082 | Markup senza lettore non dichiarato (Razor, JSP, Freemarker, Velocity, XHTML) | audit della copertura | buco dichiarato (markup senza lettore) | `64edfb930` | tutti · analizzatore · completezza · review |
| D-083 | Le correzioni degli adattatori Java e Kotlin le usava solo il banco | stadio del grafo | risolto | `d06df0522` | java, kotlin · analizzatore · correttezza · test |
| D-084 | scip-python: «Cannot find module» | PC di sviluppo | risolto | `faf7a3b22` | python · analizzatore · correttezza · prova sull'host · scip-python, npm |
| D-085 | 80 file Python su 211 senza documento | il codice di Daodan | risolto | `118689f69` | python · analizzatore · completezza · corsa su un progetto |
| D-086 | scip-python 0.6.8 non parte su Windows | host Windows | risolto | `626ebb3a2` | python · analizzatore · correttezza · prova sull'host · scip-python |
| D-087 | phazly: bersagli Python diversi da quelli del passaggio per posizione | phazly | risolto | `09537b2b9` | python · analizzatore · correttezza · corsa su un progetto |
| D-088 | Buchi Python senza causa | corpus Python | risolto | `a6156b7a2`, `3cef87b5c` | python · analizzatore · completezza · finale · scip-python, Pyright |
| D-089 | Kotlin sotto Maven: 0 file su 2 indicizzati | il pilota su 5 casi del driver Modal | risolto | `ea1e2b7d6` | kotlin · analizzatore · completezza · prova su Modal · scip-java, Gradle, Maven |
| D-090 | Java sotto Gradle: aggregazione in avanti e javap sulla cartella sbagliata | build JVM | risolto | `7b1a77e8d` | java · analizzatore · correttezza · commit · Gradle, Maven |
| D-091 | Sotto Maven l'indice Java senza il Kotlin dei moduli | Maven misto Java e Kotlin | risolto | `7b1a77e8d` | java, kotlin · analizzatore · completezza · commit · Maven |
| D-092 | Un build JVM che Daodan non esegue (sbt, Bazel) non era nominato | build JVM | buco dichiarato (sbt e Bazel non eseguiti) | `7b1a77e8d` | java, kotlin, scala · analizzatore · completezza · commit · sbt, Bazel |
| D-093 | Un indice lasciato da un build finito in errore non lo diceva | build JVM | risolto | `7b1a77e8d` | java, kotlin · analizzatore · completezza · commit |
| D-094 | Java e Kotlin giravano solo alla radice del progetto | robot-shop (`55292e2199f2`), otel-demo (`b825c7c25726`) | risolto | `1dcfba42a` | java, kotlin · analizzatore · completezza · commit · Gradle |
| D-095 | Maven e Gradle nella stessa cartella: occorrenze doppie | jvm-java-version-conflict | risolto | `9fe650a3a` | java, kotlin · analizzatore · correttezza · commit · Gradle, Maven |
| D-096 | Una radice con solo settings.gradle.kts non riconosciuta da scip-java | jvm-gradle-kts-catalog-composite | risolto | `9fe650a3a` | java, kotlin · analizzatore · completezza · commit · scip-java |
| D-097 | Kotlin presente solo negli script di build dato `failed` | jvm-gradle-kts-catalog-composite, jvm-java-version-conflict, jvm-spring-boot-managed | buco dichiarato («the build's own Kotlin only») | `9fe650a3a` | kotlin · analizzatore · correttezza · finale · Gradle |
| D-098 | File Kotlin che nessun compito di compilazione compila o elenca | jvm-kmp-common-jvm, jvm-kotlin-source-sets, klaxon (`1173bdc568a6`) | buco dichiarato (i motivi citati) | `2bc7c7459` | kotlin · analizzatore · completezza · finale · scip-java, Gradle |
| D-099 | javapoet: scip-java 0.14.2 non indicizza Java 8 | javapoet (`b9017a9503b7`) | buco dichiarato (`jdk_unsupported`) | `492a7b212` | java · analizzatore · completezza · real-3 · scip-java |
| D-100 | javapoet: il compilerId di Error Prone scavalca il wrapper di javac | javapoet | buco dichiarato (`build_edited`) | `492a7b212` | java · analizzatore · completezza · commit · scip-java, Error Prone, Maven, javac |
| D-101 | Una toolchain Gradle sotto il 17 compilava sul JDK dell'immagine | build Gradle con toolchain 8 e 11 | buco dichiarato (`jdk_unsupported`) | `0997b5d4f` | java · analizzatore · correttezza · commit · scip-java, Gradle, javac |
| D-102 | Maven con Java 5 e 6: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`, `jdk_unsupported`) | `21b3cb39b` | java · analizzatore · completezza · prova su Modal · Maven, javac |
| D-103 | Gradle con toolchain 8 e 11, anche con Kotlin accanto: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`) | `21b3cb39b` | java, kotlin · analizzatore · completezza · prova su Modal · scip-java, Gradle |
| D-104 | Gradle con livello 6: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`) | `21b3cb39b` | java · analizzatore · completezza · prova su Modal · Gradle, javac |
| D-105 | otel-demo: «Cannot invoke method toPath() on null object» in ad e recommendation | otel-demo (`b825c7c25726`) | risolto | `39805f5e7` | java, kotlin · analizzatore · correttezza · finale · scip-java, Gradle |
| D-106 | otel-demo fraud-detection sul JDK 21 di un altro build | otel-demo | risolto | `39805f5e7` | java, kotlin · analizzatore · correttezza · finale · Gradle |
| D-107 | otel-demo fraud-detection: protos che solo il Dockerfile copia | otel-demo (`b825c7c25726`) | aperto (android-sdk) | `f024ba3a3`, `f04dab9d5` | kotlin · analizzatore · completezza · jvm-otel-android · Gradle, Docker, protoc |
| D-108 | Android: classpath dei test unitari non risolti, nessun compito Android | jvm-android-app-lib, mix-poly-firebase | aperto (dynamic-jvm-2) | `39805f5e7` | java, kotlin · analizzatore · completezza · finale · scip-java, Gradle, Android SDK |
| D-109 | Android: build fermo su `google-services.json` mancante | jvm-android-app-lib, mix-poly-firebase | buco dichiarato (`build_input_missing`) | `39805f5e7` | java, kotlin · analizzatore · completezza · jvm-otel-android · Gradle, Google Services |
| D-110 | kotlinconf: «Task with name 'compileKotlinJvm' not found in project ':app:adminApp'» | kotlinconf (`146e891c150c`) | risolto | `a13d55787` | kotlin · analizzatore · correttezza · jvm-kotlinconf · scip-java, Gradle |
| D-111 | jhipster: 14 file Java con il documento senza occorrenze | jhipster-sample (`6b000b5d23a3`) | aperto | — | java · analizzatore · completezza · finale |
| D-112 | Un file Java senza documento in due fixture Maven | jvm-maven-multi-bom-profile, jvm-protobuf-generated | aperto | — | java · analizzatore · completezza · finale · Maven, protoc |
| D-113 | C#: un progetto che Msbuild rifiuta ferma il ripristino intero | zlib (`51b7f2abdade`) | risolto | `73b645531`, `0cdbae9b2` | csharp · analizzatore · correttezza · giro-2 · scip-dotnet, Roslyn, MSBuild, dotnet |
| D-114 | C#: 56,1 % di risposta | mix-dotnet-central, eShop (`913acea66708`), otel-demo, voting-app (`63e9150ca17a`) | aperto (csharp-dotnet) | `56e65e114`, `73b645531`, `0cdbae9b2` | csharp · analizzatore · completezza · finale · scip-dotnet |
| D-115 | La colonna della riga 1 di un file con il BOM | i casi C# | risolto | `0cdbae9b2` | tutti · analizzatore · correttezza · prova su Modal · Roslyn, tsc |
| D-116 | C#: nomi del chiamato con argomenti di tipo | eShop | risolto | `73b645531`, `0cdbae9b2`, `9290d446a` | csharp · analizzatore · completezza · prova su Modal · scip-dotnet, Roslyn |
| D-117 | C#: nomi del chiamato qualificati | i casi C# | risolto | `0cdbae9b2` | csharp · analizzatore · completezza · prova su Modal · tree-sitter |
| D-118 | C#: i membri dei tipi anonimi erano locali senza definizione | eShop | risolto | `73b645531` | csharp · analizzatore · completezza · prova su Modal · scip-dotnet |
| D-119 | C#: membri dei source generator e `args` dei top-level statement senza causa | eShop | buco dichiarato (GENERATED, TOP_LEVEL) | `73b645531` | csharp · analizzatore · completezza · prova su Modal · scip-dotnet |
| D-120 | C#: Catalog.API non si caricava sotto la globalizzazione invariante | eShop | risolto | `73b645531` | csharp · analizzatore · correttezza · prova su Modal · MSBuild |
| D-121 | Lo script di C e C++ cancellava la cartella in cui scrive il risultato | indicizzatore C/C++ | risolto | `c089b3540` | c, cpp · analizzatore · correttezza · commit |
| D-122 | CMake: il fornitore delle dipendenze nominato prima di essere definito | prova reale di C e C++ nel container | risolto | `a3dad5e39` | c, cpp · analizzatore · correttezza · commit · CMake |
| D-123 | scip-clang usava i processori della macchina | indicizzatore C/C++ | risolto | `d28dc1442` | c, cpp · analizzatore · prestazioni · commit · scip-clang |
| D-124 | L'errore di CMake riscritto con righe ricavate dal testo | indicizzatore C/C++ | risolto | `377925c52` | c, cpp · analizzatore · correttezza · commit · CMake |
| D-125 | vcpkg e Conan: il configure senza l'installazione del gestore | sys-cpp-vcpkg-conan | risolto | `f9fde7c1e` | c, cpp · analizzatore · completezza · commit · vcpkg, Conan, CMake |
| D-126 | Un configure che legge un submodule non scaricato | sys-git-submodule-absent | buco dichiarato (`unavailable`) | `f9fde7c1e` | c, cpp · analizzatore · completezza · finale · git |
| D-127 | `namespace a::b {` non letto come C++17 | lettura C/C++ | risolto | `f9fde7c1e` | c, cpp · analizzatore · completezza · commit |
| D-128 | Un `.h` con una direttiva Objective-C letto come C | lettura C/C++ | risolto | `f9fde7c1e` | c, cpp · analizzatore · correttezza · commit |
| D-129 | Un `.ts` di Qt Linguist letto come TypeScript | lettura | risolto | `f9fde7c1e` | typescript · analizzatore · correttezza · commit |
| D-130 | C: macro di decorazione e nomi da header non risolti | zlib | risolto | `8054a410c` | c, cpp · analizzatore · completezza · commit |
| D-131 | Un configure che ha bisogno di ciò che l'unità scarica fuori dai registri | indicizzatore C/C++ | buco dichiarato (`unavailable`) | `98743babd` | c, cpp · analizzatore · completezza · commit · scip-clang, CMake |
| D-132 | `file(DOWNLOAD)` ed ExternalProject non annotati | otel-demo src/currency | buco dichiarato (`failed` con la frase citata) | `6c2aa069e` | c, cpp · analizzatore · completezza · finale · scip-clang, CMake |
| D-133 | zlib: file C e C++ che nessun build compila | zlib | buco dichiarato (`no compile command`) | `d4e6d9046` | c, cpp · analizzatore · completezza · finale · Make, Bear |
| D-134 | zlib minizip: il build autotools non eseguito | zlib contrib/minizip | risolto | `22dca6da8` | c · analizzatore · completezza · commit · autotools |
| D-135 | otel-demo currency: il build dichiarato solo nel Dockerfile | otel-demo (`b825c7c25726`) | aperto (android-sdk) | `f024ba3a3` | cpp · analizzatore · completezza · finale · Docker, BuildKit, CMake |
| D-136 | C: 5.147 buchi `no-document` | i casi C della conferma | aperto | — | c · analizzatore · completezza · conferma |
| D-137 | File C e C++ fuori dalla configurazione predefinita | sys-cmake-presets, tinyxml2 (`9148bdf719e9`) | buco dichiarato (`no compile command | `2bc7c7459` | c, cpp · analizzatore · completezza · finale |
| D-138 | Go: i builtin erano buchi | indicizzatore Go | risolto | `a633ebd72` | go · analizzatore · completezza · commit |
| D-139 | Go: file esclusi dai vincoli di build senza indice | indicizzatore Go | risolto | `a633ebd72` | go · analizzatore · completezza · commit · scip-go |
| D-140 | Go: un file senza go.mod non diceva perché | robot-shop (`55292e2199f2`) | risolto | `d4e6d9046` | go · analizzatore · completezza · finale · scip-go, Docker |
| D-141 | robot-shop dispatch: il modulo Go dichiarato solo nel Dockerfile | robot-shop (`55292e2199f2`) | buco dichiarato (`restore_failed` a `dispatch/Dockerfile:7`) | `f024ba3a3`, `f04dab9d5` | go · analizzatore · completezza · finale · scip-go, Docker |
| D-142 | Un file cgo fuori dall'indice Go | sys-go-cgo | buco dichiarato («a cgo file») | — | c, go · analizzatore · completezza · finale · scip-go |
| D-143 | Rust: file senza documento | hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) | aperto | `a3801beed` | rust · analizzatore · completezza · finale · rust-analyzer |
| D-144 | Rust: file che nessun crate carica | hoppscotch | buco dichiarato («no crate includes it») | — | rust · analizzatore · completezza · finale · rust-analyzer |
| D-145 | TypeScript: `{ t } = useTranslation()` legato a un simbolo che l'indice non definisce | tududi (`71da9d7b34df`) | risolto | `3595d571b` | typescript · analizzatore · correttezza · commit |
| D-146 | TypeScript: pacchetti senza nome (heroicons) | tududi | risolto | `3595d571b` | typescript · analizzatore · correttezza · commit · scip-typescript |
| D-147 | TypeScript e JavaScript: buchi senza causa | tududi | risolto | `3595d571b` | javascript, typescript · analizzatore · completezza · commit · scip-typescript |
| D-148 | `module` di `module.exports` come locale senza definizione | js-yarn-berry, js-npm-single | risolto | `eacfad80e` | javascript · analizzatore · completezza · commit · scip-typescript |
| D-149 | Una chiamata senza nome del chiamato era sempre un buco `no-position` | chi (`c64ed7d6635f`) e il corpus | risolto | `334ea4d96` | tutti · analizzatore · completezza · commit |
| D-150 | TypeScript: `x.f!()` non nominava `x.f` | lettura TypeScript | risolto | `334ea4d96` | typescript · analizzatore · completezza · commit |
| D-151 | TypeScript: `await f<T>(x)` non nominava `f` | lettura TypeScript | risolto | `334ea4d96` | typescript · analizzatore · completezza · commit |
| D-152 | TypeScript 6: i tipi di Node non caricati | TypeScript nel container | risolto | `12775fee3` | typescript · analizzatore · completezza · commit · scip-typescript |
| D-153 | Svelte con nulla di letto non era `failed` | js-sveltekit | risolto | `12775fee3` | svelte · analizzatore · correttezza · commit |
| D-154 | Vue diverso fra analisi e unione | js-vue-pnpm | risolto | `12775fee3` | vue · analizzatore · correttezza · commit |
| D-155 | L'import di un `.vue` non tipizzato senza causa | progetti Vue | risolto | `12775fee3` | vue · analizzatore · completezza · commit |
| D-156 | SvelteKit: «error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'» | js-sveltekit | risolto | `12775fee3`, `b9aeca1fb` | javascript, typescript, svelte · analizzatore · completezza · finale · scip-typescript, SvelteKit |
| D-157 | TypeScript: i tipi sotto Yarn | TypeScript nel container | aperto (da verificare) | — | typescript · analizzatore · completezza · commit · Yarn |
| D-158 | JavaScript: riceventi non tipizzati | kotlinconf e il corpus JavaScript | buco dichiarato («a member of a value of type any») | `3595d571b` | javascript · analizzatore · completezza · conferma |
| D-159 | Template di Vue e Svelte non letti | hoppscotch, js-vue-pnpm, js-sveltekit | risolto | `64edfb930`, `b9aeca1fb` | vue, svelte · analizzatore · completezza · finale |
| D-160 | TypeScript: un file senza documento | hoppscotch, memos (`509e41bd1a1b`) | aperto | — | typescript · analizzatore · completezza · finale · scip-typescript |
| D-161 | Tailwind caricato sull'host con la configurazione del progetto | analyzer dei fogli di stile | risolto | `3595d571b` | css · analizzatore · sicurezza · commit · Tailwind |
| D-162 | Fogli di stile: buchi `no-rule` | il corpus | aperto (ts-container-2) | — | css · analizzatore · completezza · finale · Tailwind |
| D-163 | hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto | hoppscotch | aperto (ts-container-2) | — | css · analizzatore · correttezza · giro-2 |
| D-164 | Fogli remoti senza testo | il corpus | buco dichiarato (`remote-sheet`) | `9c719fc1a` | css · analizzatore · completezza · finale |
| D-165 | Parser: `base` di C# non letto | parser | risolto | `d94f92470` | csharp · parser · completezza · commit |
| D-166 | Parser: `this` e `super` di Kotlin non letti | parser | risolto | `d94f92470` | kotlin · parser · completezza · commit |
| D-236 | C++: il simbolo di un argomento di macro stava sul nome della macro | tinyxml2 (`9148bdf719e9`) | risolto | `a3801beed` | c, cpp · analizzatore · completezza · prova su Modal · scip-clang |
| D-237 | Rust: i riferimenti e i file che un `#[cfg]` esclude non dicevano perché | hoppscotch (`55908a76a1d0`) | buco dichiarato (la causa cfg) | `a3801beed` | rust · analizzatore · completezza · prova su Modal · rust-analyzer |
| D-238 | Rust: il turbofish su un ricevitore calcolato toglieva il nome al chiamato | semver (`280ebcb6edac`) | risolto | `a3801beed` | rust · analizzatore · correttezza · commit |
| D-239 | rust-analyzer esegue sull'host build script e macro procedurali del progetto | analizzatore Rust | risolto da `c714e6298` | `293e3bfac`, `c714e6298` | rust · analizzatore · sicurezza · prova su Modal · rust-analyzer, Cargo, rustup |
| D-242 | C#: `nameof` e le direttive del preprocessore erano chiamate o letture | analizzatore C# | risolto | `15960a591` | csharp · analizzatore · correttezza · commit |
| D-246 | Python: l'analisi girava sull'interprete di Daodan, non sul Python che la cartella dichiara | fastapi (`aabb90126964`) | risolto | `3cef87b5c` | python · analizzatore · correttezza · commit · scip-python, uv |
| D-247 | Python: un nome nudo in un'annotazione definito più sotto era una locale senza definizione | analizzatore Python | risolto | `3cef87b5c` | python · analizzatore · completezza · commit · scip-python, Pyright |
| D-248 | L'ambiente Python dell'analisi eseguiva sull'host il codice dei suoi pacchetti | fastapi (`aabb90126964`), python-semver (`b6e83e3e40d3`) | risolto | `ef6641248` | python · analizzatore · sicurezza · commit · scip-python, Pyright, uv |
| D-249 | C#: un gruppo di metodi passato come `System.Delegate` non aveva occorrenza | eShop (`913acea66708`) | risolto | `9290d446a` | csharp · analizzatore · completezza · prova su Modal · scip-dotnet, Roslyn |
| D-253 | uv sull'host poteva installare una ruota costruita da un sdist e leggeva configurazioni altrui | analizzatore Python | risolto | `a9b4e1df2` | python · analizzatore · sicurezza · commit · uv |
| D-254 | L'uv dell'host non è fissato | fastapi (`aabb90126964`) | risolto | `5e3757031` | python · host · correttezza · review · uv |
| D-255 | scip-clang leggeva i database di GCC con gli header builtin di GCC | otel-demo currency (`b825c7c25726`), riprodotto da android-sdk | risolto da `125ab9ebd` nella via principale | `125ab9ebd` | c, cpp · analizzatore · correttezza · prova su Modal · scip-clang, GCC |
| D-257 | L'analizzatore Go esegue sull'host `go mod download` e il compilatore C | analizzatore Go | aperto (host-guard-2) | — | go · analizzatore · sicurezza · review · go, git, gcc |
| D-258 | Vue e Svelte eseguivano sull'host l'installazione npm e il TypeScript del progetto | analizzatore di Vue e Svelte | risolto | `b9aeca1fb` | vue, svelte · analizzatore · sicurezza · review · npm, typescript-language-server |
| D-259 | Un header `.h` di C++ letto come C | otel-demo (`b825c7c25726`) | risolto | `bdfd7797b` | c, cpp · analizzatore · correttezza · commit |

### Passo dinamico e osservatori

37 schede: 30 risolto, 2 aperto, 5 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-167 | «Osservato» con zero osservazioni | passo dinamico | risolto | `12775fee3` | tutti · passo dinamico · correttezza · commit |
| D-168 | Un risultato malformato di un osservatore fermava la pipeline | passo dinamico | risolto | `12775fee3` | tutti · passo dinamico · correttezza · commit |
| D-169 | pytest fermo agli errori di raccolta | il codice di Daodan, senza `benchmarks/` | risolto | `12775fee3` | python · passo dinamico · completezza · prova su Modal · pytest |
| D-170 | JavaScript: il TypeScript che Node toglie da solo | osservatore JavaScript | risolto | `12775fee3` | javascript, typescript · passo dinamico · completezza · commit |
| D-171 | Un comando di test fallito senza l'errore vero nel buco | osservatore JavaScript | risolto | `12775fee3` | javascript · passo dinamico · completezza · commit |
| D-172 | `not-observed` non diceva cosa aveva visto il registratore | py-setup-cfg-extras, il cui unico test non chiama nulla e dove cli.py non gira | risolto | `0c57a839a` | tutti · passo dinamico · completezza · commit |
| D-173 | Go e Rust non pianificavano i test della radice | osservatori Go e Rust | risolto | `a491415e6` | go, rust · passo dinamico · completezza · commit |
| D-174 | Go fuori dal contratto dell'osservatore | osservatore Go | risolto | `a491415e6` | go · passo dinamico · correttezza · commit |
| D-175 | Rust: «can't find crate for std» | osservatore Rust | risolto | `ef69774f9` | rust · passo dinamico · correttezza · commit · Cargo, rustc |
| D-176 | Launchpad 502: Rust perde l'osservazione | giro `fixtures` | risolto | `d5964e7b9` | rust · passo dinamico · completezza · fixtures · Valgrind, Launchpad |
| D-177 | L'osservatore C/C++ installava con vcpkg dove l'analizzatore usa Conan | progetti con vcpkg e Conan insieme | risolto | `a8a1ebdb5` | c, cpp · passo dinamico · correttezza · commit · Conan, vcpkg |
| D-178 | L'osservatore JVM compilava sul JDK dell'immagine | javapoet | risolto | `a633ebd72` | java · passo dinamico · correttezza · real-3 |
| D-179 | Java 25: «No access to RETAIN_CLASS_REFERENCE» | jvm-ver-* | risolto | `21b3cb39b` | java · passo dinamico · correttezza · prova su Modal |
| D-180 | Test JVM multipiattaforma: nessun compito `test` | jvm-kmp-common-jvm | risolto | `9fe650a3a` | kotlin · passo dinamico · completezza · commit · Gradle |
| D-181 | Java 9 e 14 senza un JDK installabile | jvm-ver-* | buco dichiarato (`toolchain_unavailable`) | — | java · passo dinamico · completezza · java-versions |
| D-182 | I servizi della CI non avviati: tududi chiede PostgreSQL | tududi | risolto | `17babc624` | tutti · servizi · completezza · real-3 · GitHub Actions |
| D-183 | Python: le dipendenze dei test non venivano dall'ambiente del runner | python-semver (`b6e83e3e40d3`) | risolto | `17babc624` | python · passo dinamico · correttezza · finale · pytest, tox |
| D-184 | Python: l'interprete non veniva da requires-python o .python-version | osservatore Python | risolto | `17babc624` | python · passo dinamico · correttezza · commit · uv |
| D-185 | tududi: `test` non arriva ai test del frontend | tududi | risolto con D-186 | `4ee44da0a` | javascript · passo dinamico · completezza · commit · Jest, npm |
| D-186 | L'osservatore JavaScript non lanciava gli script di test che `test` non raggiunge | tududi | risolto | `7e5eb092e` | javascript · passo dinamico · completezza · commit · npm |
| D-187 | tududi: i worker di Jest uccisi per memoria | tududi | risolto | `37c7ee093` | javascript · passo dinamico · prestazioni · conferma · Jest |
| D-188 | fastapi: uv.lock non visto, l'intervallo di Python rifiutato | fastapi | risolto | `37c7ee093` | python · passo dinamico · correttezza · finale · uv, pip |
| D-189 | I test JavaScript con 16 GB fissi anche dove la macchina non li ha | osservatore JavaScript | risolto | `a42dc1d86` | javascript · passo dinamico · prestazioni · commit |
| D-190 | Turborepo: il registratore non partiva | osservatore JavaScript | risolto | `cdc1660dd` | javascript · passo dinamico · completezza · commit · Turborepo |
| D-191 | npm-tests non riconosceva `turbo run … test` | pre-mappa dei test npm | risolto | `cdc1660dd` | javascript · passo dinamico · completezza · commit · npm, Turborepo |
| D-192 | Un run di Node senza test letto come un registratore che non raggiunge i processi | osservatore JavaScript | risolto | `cdc1660dd` | javascript · passo dinamico · correttezza · commit |
| D-193 | ES module non registrati su Node prima della 22.15 | mix-infra-gha | risolto | `756ebbcb3` | javascript · passo dinamico · completezza · commit |
| D-194 | jhipster: 162 chunk di Vitest in memoria non registrati | jhipster-sample | risolto | `e8bc485d7` | javascript, typescript · passo dinamico · completezza · commit · Vitest, Angular |
| D-195 | `bun test` non registrato | fastapi | buco dichiarato (`runner_not_observed`) | `5148e8eb3` | javascript · passo dinamico · completezza · commit · Bun |
| D-196 | Un progetto senza test dichiarati, o con test che non partono | spec del passo dinamico, sezione «Limiti»; i progetti in miniatura del giro `fixtures` | buco dichiarato (`no_test_command`, `tests_not_declared`, `tests-not-run`) | — | tutti · passo dinamico · completezza · fixtures |
| D-197 | I test di fastapi non ancora girati davvero | fastapi | aperto | `5148e8eb3`, `37c7ee093` | python, typescript · passo dinamico · completezza · finale |
| D-198 | I test di eShop non ancora girati | eShop | aperto | — | javascript, typescript, csharp · passo dinamico · completezza · finale · npm |
| D-199 | Python: extra e gruppi che il gestore non installa | spec del passo dinamico | buco dichiarato (test che non partono, `tests-not-run`) | — | python · passo dinamico · completezza · spec |
| D-200 | Python più vecchio del 3.12 | spec del passo dinamico | buco dichiarato (`python_too_old`) | — | python · passo dinamico · completezza · spec |
| D-201 | I servizi che `docker compose up` avvia non partivano | passo dinamico | risolto | `22dca6da8` | tutti · servizi · completezza · commit · npm, Compose, GitHub Actions |
| D-202 | I servizi di GitLab CI non avviati | passo dinamico | risolto | `23de469c4` | tutti · servizi · completezza · commit · GitLab CI |
| D-241 | C#: nessun osservatore eseguiva i test .NET | eShop (`913acea66708`) | risolto | `15960a591` | csharp · passo dinamico · completezza · finale · dotnet |

### Container, servizi e driver Modal

22 schede: 16 risolto, 3 aperto, 3 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-203 | Il motore di container dell'utente usato anche se non risponde in locale | container | risolto | `177dcae02` | tutti · container · sicurezza · review |
| D-204 | Con un .git e Git che non risponde si copiavano i file ignorati | container | risolto | `177dcae02` | tutti · container · sicurezza · commit · git |
| D-205 | Ciò che torna dal container non controllato | container | risolto | `177dcae02` | tutti · container · sicurezza · review |
| D-206 | Link simbolici tracciati seguiti nella copia del container | python-semver | risolto | `17babc624` | tutti · container · correttezza · corsa su un progetto |
| D-207 | I link lasciati fuori dalla copia non arrivavano ai buchi delle corse | container | risolto | `756ebbcb3` | tutti · container · completezza · commit |
| D-208 | JVM: i buchi della preparazione sovrascrivevano quelli del container | analisi JVM | risolto | `756ebbcb3` | java, kotlin · container · completezza · commit |
| D-209 | Valgrind muore all'avvio nei sandbox di Modal (gVisor) | semver, tinyxml2, zlib e le fixture Rust e C/C++ | risolto | `8ef21896f` | c, cpp, rust · driver Modal · completezza · fixtures · Valgrind, Modal |
| D-210 | Bear sotto gVisor fallisce circa una build su dieci | build Make sotto Bear | risolto | `f829df4b0` | c, cpp · container · completezza · commit · Bear, Modal |
| D-211 | Il server visuale resettava la connessione su una POST rifiutata | suite su Modal | risolto | `426626fbe` | tutti · explorer · correttezza · test |
| D-212 | Servizi di Compose che il passo non avvia | spec del passo dinamico | buco dichiarato (`compose_not_read` e lacune dei servizi) | — | tutti · servizi · completezza · spec · Compose, GitLab CI |
| D-213 | I passi del job della CI prima dei test non giravano | passo dinamico | risolto | `f024ba3a3` | tutti · servizi · completezza · commit · GitHub Actions |
| D-214 | Compose: i file del progetto montati nei servizi | passo dinamico | risolto | `f024ba3a3` | tutti · servizi · completezza · commit · Compose |
| D-215 | Compose: `depends_on` | passo dinamico | risolto | `f024ba3a3` | tutti · servizi · correttezza · commit · Compose |
| D-216 | GitLab CI: i file che `.gitlab-ci.yml` include | passo dinamico | aperto (test-services) | `23de469c4` | tutti · servizi · completezza · spec · GitLab CI |
| D-217 | GitLab CI: `!reference` | da verificare | aperto (test-services) | — | tutti · servizi · completezza · review · GitLab CI |
| D-218 | Kiri non stacca un container dalla sua prima rete | motore Kiri | buco dichiarato (`ci_step_not_run`) | `f024ba3a3` | tutti · container · completezza · review · Kiri |
| D-219 | Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL | spec del passo dinamico | aperto (da decidere) | — | tutti · container · correttezza · spec · Kiri |
| D-240 | Il `.env` che il progetto traccia non arrivava nel container | fastapi (`aabb90126964`) | risolto | `b1f14ac08` | python, cpp · servizi · completezza, sicurezza · ci-steps · Compose, Docker |
| D-244 | I test reali dei servizi si cancellavano a vicenda | `tests/test_codebase_map_dynamic_services.py` | risolto | `aea1c8c3b` | tutti · servizi · correttezza · test |
| D-260 | Il passo di test della CI senza le variabili che la CI gli dà | fastapi (`aabb90126964`) | risolto | `b1f14ac08` | tutti · servizi · completezza · commit · GitHub Actions |
| D-261 | Un passo di test dentro `docker compose run` | passo dinamico | buco dichiarato (`ci_step_not_run`) | `b1f14ac08` | tutti · servizi · completezza · commit · Compose, GitHub Actions |
| D-262 | apt dietro il proxy del container: l'archivio su HTTP in chiaro | container | risolto | `b1f14ac08` | tutti · container · completezza · commit · apt |

### Benchmark e documenti

18 schede: 14 risolto, 4 aperto, 0 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-220 | Risposte attese: il workspace di javapoet e le soluzioni .NET di zlib | javapoet, zlib | risolto | `a04ab36e1` | java, csharp · benchmark · benchmark · commit |
| D-221 | Lo schema del banco senza BOM, POM genitore e versioni centrali | dieci progetti del corpus | risolto | `1420247ad` | java, kotlin · benchmark · benchmark · commit · Maven, Gradle |
| D-222 | `test_catalog` rosso: ANAGRAFICA.md non era l'uscita del generatore | benchmark project-model | risolto | `68a846a4a` | tutti · documenti · documentazione · test |
| D-223 | Le risposte attese delle fixture Android senza i build-tools | jvm-android-app-lib, mix-poly-firebase | risolto | `68a846a4a` | java, kotlin · benchmark · benchmark · commit · Gradle, Android SDK |
| D-224 | I test del registratore JVM saltati: l'immagine dei test senza JDK | `tests/modal_pytest.py` | risolto | `a633ebd72` | java · benchmark · benchmark · commit · Modal |
| D-225 | Due fixture con `node --test test/` | due fixture JavaScript | risolto | `12775fee3` | javascript · benchmark · benchmark · commit |
| D-226 | Toolchain Maven contate sbagliate per il frammento di `declared_in` | jvm-ver-* e le fixture Maven | aperto | — | java · benchmark · benchmark · java-versions · Maven |
| D-227 | README del benchmark: Rust, C e C++ «solo dove Valgrind parte» | `benchmarks/project-model/README.md` | aperto | — | c, cpp, rust · documenti · documentazione · commit · Valgrind |
| D-228 | Il rapporto dichiarava nulla la copertura a runtime | il metodo di codebase-map | risolto | `78c03d6e8` | tutti · benchmark · benchmark · commit |
| D-229 | Spec: il passo 2 «non esegue codice del progetto» | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` | javascript, typescript, java, kotlin, c, cpp, csharp · documenti · documentazione, sicurezza · spec |
| D-230 | Spec: Rust, C e C++ «non provati» su Modal | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` | c, cpp, rust · documenti · documentazione · spec · Modal |
| D-231 | README, SKILL e riferimenti dicevano Jedi e «solo statica» | README, SKILL, `references/snapshot.md` | risolto | `e617127c3` | python · documenti · documentazione · commit · Jedi |
| D-232 | L'osservatore Python diceva che il passo non avvia servizi | `scripts/dynamic/python.py` | risolto | `0ca9f1650` | python · documenti · documentazione · commit |
| D-233 | Due script del benchmark dell'inferenza mai eseguiti | `benchmarks/inference-audit` | aperto | `137512c11` | tutti · benchmark · benchmark · commit |
| D-234 | Un file dello snapshot senza dichiarazioni usciva dal progetto nel grafo | `benchmarks/inference-audit` | risolto | `53e219638` | tutti · benchmark · benchmark · commit |
| D-235 | Pre-mappa: dipendenze sotto la soglia | corpus della pre-mappa | risolto | `de353d251`, `99112d0b9` | tutti · benchmark · benchmark · corpus della pre-mappa |
| D-243 | Il driver perdeva i buchi del passo dinamico | benchmark project-model | risolto | `aea1c8c3b` | tutti · benchmark · benchmark · commit |
| D-251 | I risultati di un giro non registrano il codice di Daodan su cui è girato | giro `ci-steps` | aperto | — | tutti · benchmark · benchmark · review · Modal |

## Buchi trovati

Per lingua, i buchi di ogni giro come li conta il suo rapporto (`benchmarks/project-model/results/pipeline/2026-11-16-<giro>.report.json`, `languages`). I giri hanno casi diversi, quindi due colonne si confrontano solo sugli stessi casi: la seconda tabella somma i buchi dei casi che due giri hanno in comune (`by_case`).

Le classi le decide `scripts/code_graph.py` (`build`, righe 815-829):

- `no-position`: il riferimento non ha la posizione del nome chiamato;
- `no-document`: l'indice non ha il documento del file;
- `no-occurrence`: l'indice non ha un'occorrenza in quel punto;
- `dangling-local`: il simbolo è una locale che l'indice non definisce;
- `undefined-project-symbol`: il simbolo è del progetto e l'indice non lo definisce;
- `call-result`, `element`, `computed-callee`, `super-call`, `dynamic-import`: una chiamata senza nome del chiamato;
- «altre cause, per testo»: i buchi la cui classe è la causa che scrive l'adattatore; fra parentesi, quante cause diverse.

Le classi dei fogli di stile le decide `scripts/indexers/css.py`; quelle di Vue e Svelte, lo stadio di posizione (`scripts/position_stage.py:405`). Sotto ogni tabella, la causa di ogni classe, con la scheda che la spiega e le misure prima e dopo che i commit riportano.

### Python

| Misura | fixtures | giro-2 | finale | conferma | jvm-otel-android | ci-steps | dotenv |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 28 | 8 | 34 | 3 | 2 | 1 | 1 |
| file nello snapshot | 81 | 108 | 185 | 76 | 24 | 42 | 42 |
| file indicizzati | 81 | 108 | 185 | 76 | 24 | 42 | 42 |
| siti | 260 | 7.202 | 7.453 | 4.936 | 1.911 | 2.497 | 2.497 |
| quota di risposta | 75,0 % | 89,6 % | 89,1 % | 96,0 % | 75,6 % | 93,3 % | 96,0 % |
| `no-occurrence` | 27 | 457 | 484 | 117 | 298 | 98 | 0 |
| `undefined-project-symbol` | 22 | 178 | 199 | 74 | 100 | 65 | 0 |
| `dangling-local` | 16 | 103 | 117 | 9 | 58 | 4 | 0 |
| `no-position` | 0 | 13 | 13 | 0 | 11 | 0 | 0 |
| altre cause, per testo | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 101 (2) |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 28 | 65 | 65 |
| `giro-2` → `finale` | 8 | 751 | 751 |
| `finale` → `conferma` | 3 | 232 | 200 |
| `finale` → `jvm-otel-android` | 2 | 467 | 467 |
| `finale` → `ci-steps` | 1 | 167 | 167 |
| `conferma` → `ci-steps` | 1 | 167 | 167 |
| `ci-steps` → `dotenv` | 1 | 167 | 101 |

- `no-occurrence`, `dangling-local`, `no-position`: fino a `a6156b7a2` senza causa (D-088). Da allora ogni buco porta la causa del checker (Pyright 1.1.414): un valore che il checker tipizza Unknown o Any, o un nome che il checker lega e scip-python non nomina. Un nome nudo in un'annotazione, definito più sotto nel modulo, era una `dangling-local`; da `3cef87b5c` porta alla definizione (D-247).
- `undefined-project-symbol`: tre difetti di scip-python 0.6.8, corretti da `a6156b7a2` (D-088). Sono i nomi che l'`__init__` di una distribuzione riesporta, `__name__` e simili, e gli import attraverso la radice sorgente dichiarata. Da 65 e 10 a 0 su fastapi e python-semver.
- Misure dei commit: con `a6156b7a2`, fastapi passa da 167 a 102 buchi (dal 93,3 % al 95,9 %) e python-semver da 64 a 54 (dal 97,2 % al 97,7 %). In `ci-steps`, fastapi ha i numeri che il commit dà come «prima»: 167 buchi, 93,3 %, 65 `undefined-project-symbol`. Con `7ecbaed48` fastapi va da 101 a 102 buchi: `deps.py`, letto con il 3.14, porta un `except A, B:` (PEP 758) che il Pyright di scip-python 0.6.8 non legge (D-252).

### JavaScript

| Misura | fixtures | real-3 | giro-2 | finale | conferma | jvm-otel-android | jvm-kotlinconf | jvm-kotlinconf-kmp | ci-steps | dotenv |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 20 | 1 | 13 | 32 | 4 | 1 | 1 | 1 | 1 | 1 |
| file nello snapshot | 34 | 1.038 | 186 | 1.254 | 1.103 | 10 | 1 | 1 | 1.038 | 1.038 |
| file indicizzati | 34 | 1.038 | 186 | 1.254 | 1.103 | 10 | 1 | 1 | 1.038 | 1.038 |
| siti | 174 | 134.949 | 38.165 | 173.277 | 147.548 | 276 | 23 | 23 | 134.949 | 134.949 |
| quota di risposta | 75,9 % | 72,7 % | 73,8 % | 72,9 % | 72,5 % | 70,7 % | 56,5 % | 56,5 % | 74,4 % | 74,2 % |
| `no-occurrence` | 28 | 36.131 | 9.261 | 45.417 | 39.563 | 0 | 0 | 0 | 12 | 12 |
| `dangling-local` | 10 | 496 | 566 | 1.069 | 732 | 2 | 0 | 0 | 56 | 56 |
| `no-position` | 2 | 208 | 158 | 368 | 250 | 0 | 0 | 0 | 0 | 0 |
| `call-result` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 131 | 131 |
| `undefined-project-symbol` | 0 | 55 | 6 | 61 | 46 | 0 | 0 | 0 | 5 | 5 |
| `super-call` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 51 | 51 |
| `element` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 20 |
| `computed-callee` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| altre cause, per testo | 2 (1) | 0 (0) | 1 (1) | 3 (2) | 0 (0) | 79 (4) | 10 (1) | 10 (1) | 34.213 (128) | 34.469 (128) |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 20 | 42 | 41 |
| `real-3` → `finale` | 1 | 36.890 | 36.890 |
| `giro-2` → `finale` | 13 | 9.992 | 9.992 |
| `finale` → `conferma` | 4 | 41.276 | 40.591 |
| `finale` → `jvm-otel-android` | 1 | 81 | 81 |
| `finale` → `jvm-kotlinconf` | 1 | 10 | 10 |
| `jvm-kotlinconf` → `jvm-kotlinconf-kmp` | 1 | 10 | 10 |
| `finale` → `ci-steps` | 1 | 36.890 | 34.490 |
| `conferma` → `ci-steps` | 1 | 36.205 | 34.490 |
| `ci-steps` → `dotenv` | 1 | 34.490 | 34.746 |

- `no-occurrence`: l'indice non dice perché un riferimento non ha occorrenza (D-147). Da `3595d571b` il checker di TypeScript dà a ogni buco la sua causa: ricevente `any`, firma a indice, membro creato dal checker, non dichiarato. Così in `ci-steps` i `no-occurrence` di tududi sono 12, e 34.213 buchi portano una di 128 cause. Un membro di un valore senza tipo resta un buco dichiarato: lo risolve solo l'esecuzione (D-158).
- `dangling-local`: `module` di `module.exports` scritto come locale senza definizione (D-148). `eacfad80e` lo lega all'oggetto modulo di Node: js-yarn-berry e js-npm-single completi, 0 buchi.
- `no-position`, `call-result`, `super-call`, `element`, `computed-callee`: una chiamata senza nome del chiamato era sempre `no-position`. Da `334ea4d96` il grafo legge l'espressione chiamata, e la classe dice quale (D-149): su chi 36 di 43 con risposta.
- `undefined-project-symbol`: nessuna scheda.

### TypeScript

| Misura | fixtures | real-3 | giro-2 | finale | conferma | jvm-otel-android | ci-steps | dotenv |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 15 | 1 | 6 | 21 | 2 | 2 | 2 | 2 |
| file nello snapshot | 43 | 650 | 2.274 | 2.967 | 759 | 144 | 759 | 759 |
| file indicizzati | 43 | 650 | 2.272 | 2.965 | 759 | 144 | 759 | 759 |
| siti | 119 | 77.897 | 194.292 | 272.308 | 82.246 | 8.733 | 82.243 | 82.243 |
| quota di risposta | 83,2 % | 89,6 % | 89,7 % | 90,4 % | 89,8 % | 70,5 % | 96,9 % | 96,9 % |
| `dangling-local` | 11 | 4.199 | 7.259 | 10.060 | 4.311 | 350 | 18 | 18 |
| `no-occurrence` | 7 | 2.843 | 9.013 | 11.086 | 2.880 | 29 | 4 | 4 |
| `undefined-project-symbol` | 0 | 968 | 2.265 | 3.233 | 1.053 | 0 | 0 | 0 |
| `no-position` | 1 | 99 | 1.542 | 1.642 | 109 | 16 | 1 | 1 |
| `dynamic-import` | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 38 |
| `call-result` | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 19 |
| `super-call` | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 13 |
| `computed-callee` | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 |
| `element` | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 |
| `no-document` | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| altre cause, per testo | 1 (1) | 0 (0) | 10 (6) | 11 (7) | 0 (0) | 2.183 (3) | 2.408 (17) | 2.408 (17) |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 14 | 20 | 20 |
| `real-3` → `finale` | 1 | 8.109 | 5.923 |
| `giro-2` → `finale` | 6 | 20.090 | 20.090 |
| `finale` → `conferma` | 2 | 6.167 | 8.353 |
| `finale` → `jvm-otel-android` | 2 | 2.578 | 2.578 |
| `finale` → `ci-steps` | 2 | 6.167 | 2.515 |
| `conferma` → `ci-steps` | 2 | 8.353 | 2.515 |
| `ci-steps` → `dotenv` | 2 | 2.515 | 2.515 |

- `dangling-local`: il join legava `{ t } = useTranslation()` e simili a un simbolo che l'indice non definisce (D-145, `3595d571b`); `module.exports` (D-148).
- `no-occurrence`: alcuni chiamati che il lettore non nominava, `x.f!()` (D-150) e `await f<T>(x)` (D-151). I pacchetti senza nome, come heroicons, li corregge scip-typescript 0.6.2 (D-146). Da `3595d571b` ogni buco ha la causa del checker (D-147).
- `undefined-project-symbol`: i tipi di Node non caricati con TypeScript 6 (D-152); i tipi sotto Yarn, da verificare (D-157).
- `no-position` e le classi senza nome del chiamato: D-149.
- `no-document`: un file senza documento, da verificare (D-160).
- Misure dei commit: con `3595d571b`, tududi passa da 8.010 buchi TypeScript senza spiegazione a 3.193 con la causa. Sugli stessi due casi, da 8.353 nella conferma a 2.515 in `ci-steps`.

### Java

| Misura | fixtures | real-3 | giro-2 | finale | java-versions | jvm-otel-android |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 12 | 1 | 8 | 18 | 18 | 1 |
| file nello snapshot | 22 | 39 | 222 | 278 | 37 | 9 |
| file indicizzati | 20 | 39 | 207 | 261 | 37 | 9 |
| siti | 105 | 9.142 | 9.906 | 19.141 | 453 | 693 |
| quota di risposta | 77,1 % | 99,9 % | 99,8 % | 99,7 % | 100,0 % | 100,0 % |
| `no-document` | 24 | 0 | 14 | 38 | 0 | 0 |
| `undefined-project-symbol` | 0 | 10 | 6 | 16 | 0 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 12 | 24 | 24 |
| `real-3` → `finale` | 1 | 10 | 10 |
| `giro-2` → `finale` | 8 | 20 | 20 |
| `finale` → `jvm-otel-android` | 1 | 0 | 0 |

- `no-document`: un file Java senza documento in due fixture Maven, da verificare (D-112). Su jhipster, 14 file hanno il documento senza occorrenze (D-111, aperto).
- `undefined-project-symbol`: nessuna scheda.
- Le versioni di Java sotto il 17, e un build che scavalca il plugin di scip-java, non danno buchi ma nessun indice: D-099–D-104 (`jdk_unsupported`, `build_edited`).

### Kotlin

| Misura | fixtures | giro-2 | finale | java-versions | conferma | jvm-otel-android | jvm-kotlinconf | jvm-kotlinconf-kmp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 8 | 7 | 11 | 1 | 1 | 3 | 1 | 1 |
| file nello snapshot | 12 | 108 | 115 | 3 | 0 | 0 | 0 | 271 |
| file indicizzati | 7 | 99 | 103 | 1 | 0 | 0 | 0 | 226 |
| siti | 101 | 4.324 | 4.393 | 13 | 0 | 0 | 0 | 16.830 |
| quota di risposta | 31,7 % | 94,1 % | 93,1 % | 15,4 % | 0,0 % | 0,0 % | 0,0 % | 76,0 % |
| `no-document` | 69 | 249 | 295 | 11 | 0 | 0 | 0 | 2.214 |
| `no-occurrence` | 0 | 7 | 7 | 0 | 0 | 0 | 0 | 1.830 |
| `no-position` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `element` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 8 | 69 | 69 |
| `giro-2` → `finale` | 7 | 257 | 257 |
| `finale` → `conferma` | 1 | 0 | 0 |
| `finale` → `jvm-otel-android` | 3 | 0 | 0 |
| `finale` → `jvm-kotlinconf` | 1 | 0 | 0 |
| `jvm-kotlinconf` → `jvm-kotlinconf-kmp` | 1 | 0 | 4.045 |

- `no-document`:
  - file Kotlin che nessun compito di compilazione compila o elenca (D-098);
  - Kotlin solo negli script di build (D-097);
  - Kotlin sotto Maven, 0 file su 2 prima di `ea1e2b7d6` (D-089).
- 0 file indicizzati in `conferma`, `jvm-otel-android` e `jvm-kotlinconf`: Kotlin non ha indice.
  - kotlinconf: «Task with name 'compileKotlinJvm' not found» (D-110); in `jvm-kotlinconf-kmp`, con il rimedio di D-110 (`a13d55787`), Kotlin è `fresh` con 226 file su 271 e il 76,0 % di risposta, e i 45 file fuori dall'indice dicono perché (D-098);
  - Android: i classpath dei test non risolti (D-108) e `google-services.json` mancante (D-109);
  - otel-demo fraud-detection: i protos che solo il Dockerfile copia (D-107).
- `no-occurrence`, `no-position`: nessuna scheda.

### C

| Misura | fixtures | giro-2 | finale | conferma | jvm-otel-android | jvm-kotlinconf | jvm-kotlinconf-kmp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 8 | 3 | 9 | 7 | 1 | 1 | 1 |
| file nello snapshot | 8 | 54 | 72 | 72 | 0 | 0 | 0 |
| file indicizzati | 7 | 21 | 49 | 49 | 0 | 0 | 0 |
| siti | 18 | 10.190 | 10.271 | 10.271 | 0 | 0 | 0 |
| quota di risposta | 100,0 % | 28,7 % | 40,7 % | 40,7 % | 0,0 % | 0,0 % | 0,0 % |
| `no-document` | 0 | 6.421 | 5.147 | 5.147 | 0 | 0 | 0 |
| `no-occurrence` | 0 | 839 | 940 | 941 | 0 | 0 | 0 |
| `no-position` | 0 | 1 | 1 | 1 | 0 | 0 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 6 | 0 | 2 |
| `giro-2` → `finale` | 3 | 7.261 | 6.086 |
| `finale` → `conferma` | 7 | 6.088 | 6.089 |
| `finale` → `jvm-otel-android` | 1 | 0 | 0 |
| `finale` → `jvm-kotlinconf` | 1 | 0 | 0 |
| `jvm-kotlinconf` → `jvm-kotlinconf-kmp` | 1 | 0 | 0 |

- `no-document`:
  - file che nessun build compila, in zlib (D-133) o fuori dalla configurazione predefinita (D-137);
  - il build autotools di minizip, che Daodan non eseguiva (D-134);
  - un configure che chiede ciò che l'unità scarica (D-131), o un submodule non scaricato (D-126);
  - i 5.147 della conferma sono da verificare (D-136).
- `no-occurrence`: le macro di decorazione e i nomi da header (D-130): semantici da 37 a 12, risolte da 303 a 510.
- Fino a `125ab9ebd`, successivo ai commit dei risultati di tutti i giri, scip-clang leggeva i progetti costruiti con GCC con gli header builtin di GCC e taceva migliaia di errori (D-255): libdeflate da 11.150 errori a 0.

### C++

| Misura | fixtures | giro-2 | finale | conferma | jvm-otel-android |
| --- | ---: | ---: | ---: | ---: | ---: |
| casi | 6 | 6 | 9 | 8 | 1 |
| file nello snapshot | 10 | 9 | 19 | 19 | 0 |
| file indicizzati | 10 | 8 | 18 | 18 | 0 |
| siti | 67 | 2.620 | 2.651 | 2.651 | 0 |
| quota di risposta | 94,0 % | 89,9 % | 89,2 % | 90,1 % | 0,0 % |
| `no-occurrence` | 4 | 239 | 262 | 236 | 0 |
| `no-document` | 0 | 25 | 25 | 25 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 6 | 4 | 7 |
| `giro-2` → `finale` | 6 | 264 | 284 |
| `finale` → `conferma` | 8 | 287 | 261 |
| `finale` → `jvm-otel-android` | 1 | 0 | 0 |

- `no-occurrence`: il simbolo di un argomento di macro stava sul nome della macro (D-236). Con `a3801beed`, tinyxml2 passa da 255 a 43. I 43 restanti sono rami `#if` che il build non compila, o chiamate alla libreria C che l'indice C++ non nomina.
- `no-document`: file fuori dalla configurazione predefinita (D-137).
- Gli header builtin di GCC, come per C (D-255): una sonda C e C++ su `_mm_pause` da 3.492 errori a 0.

### C#

| Misura | fixtures | giro-2 | finale | conferma | jvm-otel-android |
| --- | ---: | ---: | ---: | ---: | ---: |
| casi | 1 | 4 | 5 | 1 | 1 |
| file nello snapshot | 2 | 559 | 561 | 0 | 13 |
| file indicizzati | 2 | 559 | 561 | 0 | 13 |
| siti | 20 | 14.889 | 14.909 | 0 | 660 |
| quota di risposta | 75,0 % | 56,1 % | 56,1 % | 0,0 % | 91,5 % |
| `no-occurrence` | 2 | 5.356 | 5.358 | 0 | 5 |
| `no-position` | 2 | 1.019 | 1.021 | 0 | 49 |
| `dangling-local` | 0 | 144 | 144 | 0 | 0 |
| `undefined-project-symbol` | 1 | 19 | 20 | 0 | 2 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 1 | 5 | 5 |
| `giro-2` → `finale` | 4 | 6.538 | 6.538 |
| `finale` → `conferma` | 1 | 0 | 0 |
| `finale` → `jvm-otel-android` | 1 | 56 | 56 |

- `no-occurrence`:
  - il ripristino falliva intero per un solo progetto di workload, circa 4.400 buchi in eShop (D-113, `0cdbae9b2`);
  - i nomi con argomenti di tipo (D-116) e i gruppi di metodi passati come `System.Delegate` (D-249), che scip-dotnet 0.2.16 non nomina: con la patch di `9290d446a`, su eShop no-occurrence da 1.963 a 966, i nomi con argomenti di tipo da 966 a 55; e i nomi qualificati (D-117);
  - la colonna della riga 1 con il BOM (D-115).
- `dangling-local`: i membri dei tipi anonimi (D-118), da 138 a 1.
- `undefined-project-symbol`: i membri dei source generator e `args` dei top-level statement (D-119), da 17 a 0, con le cause `GENERATED` e `TOP_LEVEL`.
- `no-position`: nessuna scheda.
- Misure dei commit (D-114): eShop 86,6 % senza l'osservatore e 87,3 % con l'osservatore (`15960a591`); dall'84,67 % al 92,06 % con la patch di scip-dotnet (`9290d446a`); contro il 56,1 % del finale sui cinque casi C#.

### Go

| Misura | fixtures | real-3 | giro-2 | finale | conferma | jvm-otel-android |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 10 | 1 | 5 | 15 | 8 | 1 |
| file nello snapshot | 34 | 90 | 556 | 679 | 30 | 15 |
| file indicizzati | 28 | 90 | 555 | 678 | 29 | 15 |
| siti | 165 | 10.099 | 157.378 | 167.639 | 109 | 6.180 |
| quota di risposta | 75,8 % | 97,0 % | 96,8 % | 99,5 % | 84,4 % | 97,9 % |
| `no-occurrence` | 21 | 266 | 4.372 | 95 | 1 | 12 |
| `no-position` | 2 | 37 | 664 | 703 | 1 | 121 |
| `no-document` | 17 | 0 | 0 | 10 | 10 | 0 |
| `undefined-project-symbol` | 0 | 0 | 0 | 5 | 5 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 10 | 40 | 32 |
| `real-3` → `finale` | 1 | 303 | 37 |
| `giro-2` → `finale` | 5 | 5.036 | 744 |
| `finale` → `conferma` | 8 | 17 | 17 |
| `finale` → `jvm-otel-android` | 1 | 133 | 133 |

- `no-occurrence`: i builtin non erano esterni di nessun pacchetto (D-138), e i file esclusi dai vincoli di build non avevano indice (D-139); `a633ebd72` li corregge. `a633ebd72` viene dopo `b41e0d6e8`, il commit dei risultati di `giro-2`, e prima di `492a7b212`, il codice del finale secondo il README: sugli stessi 5 casi, da 5.036 a 744 buchi; i risultati non dicono su quale codice ciascun giro è girato (D-251). Un file cgo resta fuori dall'indice (D-142).
- `no-document`: un file senza go.mod, che il Dockerfile scrive al build (D-140, D-141).
- `no-position`, `undefined-project-symbol`: nessuna scheda.

### Rust

| Misura | fixtures | giro-2 | finale | conferma | jvm-otel-android |
| --- | ---: | ---: | ---: | ---: | ---: |
| casi | 10 | 4 | 13 | 9 | 2 |
| file nello snapshot | 23 | 135 | 154 | 38 | 10 |
| file indicizzati | 23 | 126 | 145 | 37 | 10 |
| siti | 73 | 7.478 | 7.546 | 1.556 | 269 |
| quota di risposta | 95,9 % | 88,4 % | 88,5 % | 98,4 % | 98,9 % |
| `no-occurrence` | 3 | 553 | 556 | 4 | 3 |
| `no-document` | 0 | 289 | 289 | 16 | 0 |
| `no-position` | 0 | 13 | 13 | 5 | 0 |
| `undefined-project-symbol` | 0 | 9 | 9 | 0 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 10 | 3 | 3 |
| `giro-2` → `finale` | 4 | 864 | 864 |
| `finale` → `conferma` | 9 | 25 | 25 |
| `finale` → `jvm-otel-android` | 2 | 3 | 3 |

- `no-occurrence`: un riferimento sotto un `#[cfg]` falso nella configurazione che rust-analyzer legge (D-237). Con `a3801beed`, su hoppscotch «no-occurrence da 549 a 135, di cui 425 ora con la causa cfg; no-position da 8 a 0».
- `no-document`: file senza documento (D-143, da verificare) e file che nessun crate carica (D-144). Da `a3801beed`, un file dietro un `mod` con cfg falso dice perché manca (D-237).
- `no-position`: un chiamato con turbofish su un ricevitore calcolato non aveva nome (D-238).
- Misure dei commit: con `293e3bfac`, che porta build script e macro nel container, su hoppscotch i buchi Rust vanno da 831 a 689 e quelli senza occorrenza da 111 a 5; 23 crate restano buchi per le librerie GTK e WebKit che mancano all'immagine (D-239).

### Fogli di stile

| Misura | fixtures | real-3 | giro-2 | finale | conferma | jvm-otel-android | jvm-kotlinconf | jvm-kotlinconf-kmp | ci-steps | dotenv |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| casi | 10 | 1 | 13 | 24 | 7 | 2 | 1 | 1 | 2 | 2 |
| file nello snapshot | 51 | 1.708 | 1.643 | 3.402 | 2.019 | 169 | 3 | 3 | 1.822 | 1.822 |
| file indicizzati | 50 | 1.708 | 1.578 | 3.336 | 2.019 | 162 | 3 | 3 | 1.822 | 1.822 |
| siti | 23 | 37.987 | 29.241 | 67.251 | 58.534 | 22 | 45 | 45 | 38.871 | 38.871 |
| quota di risposta | 52,2 % | 1,6 % | 58,3 % | 26,3 % | 26,3 % | 27,3 % | 82,2 % | 82,2 % | 98,7 % | 98,7 % |
| `no-rule` | 7 | 37.162 | 11.639 | 48.808 | 42.757 | 12 | 1 | 1 | 163 | 163 |
| `call` | 0 | 67 | 341 | 408 | 177 | 0 | 0 | 0 | 176 | 176 |
| `parameter` | 0 | 69 | 27 | 96 | 73 | 2 | 0 | 0 | 72 | 72 |
| `property` | 0 | 34 | 12 | 46 | 37 | 0 | 0 | 0 | 37 | 37 |
| `no-font-face` | 0 | 9 | 41 | 50 | 34 | 1 | 5 | 5 | 28 | 28 |
| `css-in-js` | 0 | 24 | 0 | 24 | 24 | 0 | 0 | 0 | 24 | 24 |
| `undeclared` | 0 | 0 | 45 | 45 | 3 | 0 | 0 | 0 | 3 | 3 |
| `unresolved-import` | 2 | 1 | 36 | 39 | 5 | 1 | 2 | 2 | 3 | 3 |
| `variable` | 0 | 1 | 28 | 29 | 2 | 0 | 0 | 0 | 1 | 1 |
| `ejs-glued` | 0 | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 5 |
| `element-access` | 0 | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 5 |
| `remote-sheet` | 2 | 0 | 8 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| `ejs` | 0 | 4 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 4 |
| `template` | 0 | 2 | 2 | 4 | 2 | 0 | 0 | 0 | 2 | 2 |
| `expression` | 0 | 0 | 5 | 5 | 1 | 0 | 0 | 0 | 0 | 0 |
| `concatenation` | 0 | 0 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| `no-keyframes` | 0 | 0 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| `url-path` | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| `template-tag-glued` | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 10 | 11 | 11 |
| `real-3` → `finale` | 1 | 37.383 | 37.383 |
| `giro-2` → `finale` | 13 | 12.194 | 12.194 |
| `finale` → `conferma` | 7 | 43.132 | 43.132 |
| `finale` → `jvm-otel-android` | 2 | 16 | 16 |
| `finale` → `jvm-kotlinconf` | 1 | 8 | 8 |
| `jvm-kotlinconf` → `jvm-kotlinconf-kmp` | 1 | 8 | 8 |
| `finale` → `ci-steps` | 2 | 38.210 | 523 |
| `conferma` → `ci-steps` | 2 | 38.210 | 523 |
| `ci-steps` → `dotenv` | 2 | 523 | 523 |

- `no-rule`: un riferimento di classe, id o composes senza una regola che lo definisca (D-162), fra cui le classi Tailwind. Da `3595d571b` Tailwind gira nel container (D-161). Sugli stessi due casi, tududi e fastapi, da 38.210 buchi nella conferma a 523 in `ci-steps`: nessuno dei due giri registra il proprio codice, così il salto non si lega a un commit (D-251).
- `remote-sheet`: un foglio remoto senza testo (D-164), buco dichiarato.
- Le altre classi sono le cause del lettore (`scripts/indexers/css.py`); nessuna scheda le spiega una per una.

### Vue

| Misura | fixtures | giro-2 | finale |
| --- | ---: | ---: | ---: |
| casi | 1 | 1 | 2 |
| file nello snapshot | 3 | 407 | 410 |
| file indicizzati | 0 | 0 | 0 |
| siti | 3 | 25.499 | 25.502 |
| quota di risposta | 0,0 % | 28,2 % | 28,2 % |
| `not-asked` | 2 | 15.093 | 15.095 |
| `engine-unresolved` | 1 | 3.216 | 3.217 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 1 | 3 | 3 |
| `giro-2` → `finale` | 1 | 18.309 | 18.309 |

- `not-asked`, `engine-unresolved`: una chiamata senza arco, rispettivamente non chiesta al motore o chiesta senza risposta (`scripts/position_stage.py:405`); nessuna scheda ne spiega la causa.
- I template non erano letti (D-080, D-159), e l'import di un `.vue` non tipizzato non diceva la causa (D-155). Da `b9aeca1fb`, successivo ai commit dei risultati di tutti i giri, Vue passa a scip-typescript nel container, template compresi: le classi di questa tabella sono dello stadio di posizione, che non lo legge più.

### Svelte

| Misura | fixtures | giro-2 | finale |
| --- | ---: | ---: | ---: |
| casi | 1 | 1 | 2 |
| file nello snapshot | 2 | 2 | 4 |
| file indicizzati | 0 | 0 | 0 |
| siti | 2 | 13 | 15 |
| quota di risposta | 0,0 % | 30,8 % | 26,7 % |
| `not-asked` | 2 | 6 | 8 |
| `engine-unresolved` | 0 | 3 | 3 |

| Stessi casi | Casi | Buchi prima | Buchi dopo |
| --- | ---: | ---: | ---: |
| `fixtures` → `finale` | 1 | 2 | 2 |
| `giro-2` → `finale` | 1 | 9 | 9 |

- `not-asked`, `engine-unresolved`: come per Vue (`scripts/position_stage.py:405`); nessuna scheda ne spiega la causa.
- I template non erano letti (D-080, D-159); il tsconfig che SvelteKit genera mancava (D-156); uno Svelte con nulla di letto non era `failed` (D-153). Da `b9aeca1fb` Svelte passa a scip-typescript nel container, come Vue.

## Progetti di prova

Ogni progetto su cui Daodan si prova, con ciò che prova e le schede che ha rivelato. Le fixture e i repository veri stanno in `benchmarks/project-model/fixtures/`. Per ogni progetto, «Casi» elenca quelli di `expected.json`, definiti in `benchmarks/project-model/ANAGRAFICA.md`. «Rivelate» sono le schede che nominano il progetto in «Progetto e caso»; «Citate» quelle che lo nominano altrove, nella prova o nella spiegazione.

### Fixture del corpus (104)

#### js (20)

| Progetto | Linguaggi | Casi | Rivelate | Citate |
| --- | --- | --- | --- | --- |
| js-angular | CSS, HTML, TypeScript | targets-as-units, path-alias, version-absent, no-lockfile, build-generates-code | — | — |
| js-bun | TypeScript | locked-versions, templated-config | — | — |
| js-cjs-esm-exports | JavaScript, TypeScript | no-lockfile, ambiguous-extension, false-generated | — | — |
| js-deno | TypeScript | unit-no-name, path-alias, no-lockfile | — | — |
| js-lerna | JavaScript | workspace-glob, version-absent, no-lockfile, internal-link | — | — |
| js-local-and-git-deps | JavaScript | independent-units, locked-versions, internal-link, git-dependency | D-017 | — |
| js-nextjs | JavaScript, TSX, TypeScript | path-alias, version-range, no-lockfile, generated-file, service-from-config | — | — |
| js-node-scripts | JavaScript, Markdown | no-build-file, unit-no-name, version-absent, undeclared-imports, ambiguous-extension, shebang-only | — | — |
| js-npm-single | JavaScript | version-absent, locked-versions | D-148 | — |
| js-npm-workspaces | JavaScript | workspace-glob, version-absent, locked-versions, internal-link | — | — |
| js-nx | TypeScript | workspace-glob, path-alias, version-absent, no-lockfile | — | — |
| js-pnpm-workspace | TypeScript | workspace-glob, locked-versions, version-indirect, internal-link | — | — |
| js-static-html | CSS, HTML, JavaScript | no-build-file, unit-no-name, declared-in-source | — | — |
| js-sveltekit | HTML, JavaScript, Svelte, TypeScript | path-alias, no-lockfile, build-generates-code | D-153, D-156, D-159 | — |
| js-turborepo | JavaScript | workspace-glob, no-lockfile, internal-link | — | — |
| js-vendored-generated | GraphQL, TypeScript | no-lockfile, generated-file, vendored-code | — | — |
| js-version-conflict | JavaScript | version-disagree, no-lockfile | — | — |
| js-vite-react-ts | HTML, TSX, TypeScript | path-alias, version-absent, no-lockfile, false-generated | — | — |
| js-vue-pnpm | HTML, TypeScript, Vue | version-absent, no-lockfile, ambiguous-extension | D-154, D-159 | — |
| js-yarn-berry | JavaScript | workspace-glob, unit-no-name, version-absent, locked-versions, internal-link | D-148 | — |

#### jvm (16)

| Progetto | Linguaggi | Casi | Rivelate | Citate |
| --- | --- | --- | --- | --- |
| jvm-android-app-lib | Kotlin | name-mismatch, source-sets, build-variants, version-in-wrapper, platform-sdk, no-lockfile, version-from-bom, build-only-dependency, vendored-code, needs-build, missing-file, saas-service | D-044, D-108, D-109, D-223 | — |
| jvm-gradle-computed-deps | Java | version-absent, no-lockfile, version-indirect, computed-dependencies, needs-build | — | — |
| jvm-gradle-groovy-wrapper | Java | name-mismatch, version-in-wrapper, version-from-bom, vendored-code, needs-build, missing-file | — | — |
| jvm-gradle-kts-catalog-composite | Java | virtual-root, nested-module, inherited-settings, version-in-wrapper, version-from-bom, version-indirect, build-only-dependency, vendored-code, needs-build | D-096, D-097 | — |
| jvm-gradle-locking | Java | version-range, version-absent, locked-versions | — | — |
| jvm-java-version-conflict | Java | shared-root, version-disagree, version-absent | D-095, D-097 | — |
| jvm-kmp-common-jvm | Kotlin | custom-source-roots, source-sets, no-lockfile, version-from-bom, build-only-dependency | D-098, D-180 | — |
| jvm-kotlin-source-sets | Kotlin | source-sets, no-lockfile, version-from-bom, build-only-dependency | D-098 | — |
| jvm-maven-multi-bom-profile | Java | name-mismatch, inherited-settings, build-variants, version-from-bom, version-indirect, internal-link, build-only-dependency, needs-build | D-112 | — |
| jvm-maven-release-apt | Java | version-disagree, no-lockfile, version-indirect, build-only-dependency, build-generates-code | — | — |
| jvm-maven-wrapper | Java | version-in-wrapper, no-lockfile, build-only-dependency, vendored-code | — | — |
| jvm-mixed-java-kotlin | Java, Kotlin | custom-source-roots, no-lockfile, version-indirect, build-only-dependency, missing-file | — | — |
| jvm-no-build | Java | no-build-file, unit-no-name, version-absent | — | — |
| jvm-protobuf-generated | Java, Protocol Buffer | custom-source-roots, no-lockfile, build-only-dependency, generated-file, build-generates-code | D-112 | — |
| jvm-sbt-two-subprojects | Scala | targets-as-units, name-mismatch, version-absent, no-lockfile, build-only-dependency, ambiguous-extension | — | — |
| jvm-spring-boot-managed | Java | version-from-bom, scope-from-groups, build-only-dependency, needs-build, service-in-infra | D-097 | — |

#### mix (22)

| Progetto | Linguaggi | Casi | Rivelate | Citate |
| --- | --- | --- | --- | --- |
| mix-dart-flutter | Dart | independent-units, inherited-settings, toolchain-in-dependencies, platform-sdk, locked-versions, internal-link | — | — |
| mix-dotnet-central | C# | inherited-settings, version-range, no-lockfile, version-indirect, needs-build, framework-from-files | D-114 | — |
| mix-edge-deep-manifest | Rust | inherited-settings, documentation-tree | — | — |
| mix-edge-empty | nessuno | no-build-file, documentation-tree | — | — |
| mix-edge-extensions | MATLAB, Objective-C, Prolog, Python, XML | no-build-file, unit-no-name, ambiguous-extension, shebang-only | — | — |
| mix-edge-scripts | Batchfile, PowerShell, Shell | no-build-file, unit-no-name, shebang-only, saas-service | — | — |
| mix-edge-sql | PLpgSQL, PLSQL, SQL, TSQL | no-build-file, unit-no-name, ambiguous-extension | — | — |
| mix-edge-submodules | JavaScript, Python | shared-root, no-lockfile, git-dependency, build-only-dependency, submodule-absent | — | — |
| mix-edge-vendored | C, HTML, JavaScript, Python | no-lockfile, undeclared-imports, generated-file, vendored-code, documentation-tree, binary-file, committed-ignored | — | — |
| mix-elixir-umbrella | Elixir | workspace-glob, unit-no-name, locked-versions, transitive-not-direct, internal-link, needs-build | — | — |
| mix-infra-compose | Dockerfile, JavaScript | one-unit-many-parts, version-in-image, no-lockfile, missing-file, service-in-infra | — | — |
| mix-infra-devcontainer | TypeScript | version-in-image, no-lockfile, templated-config, dot-folder-facts, missing-file, service-in-infra | — | — |
| mix-infra-gha | Go, JavaScript, Python | no-build-file, unit-no-name, version-disagree, version-matrix, version-in-image, dot-folder-facts | D-193 | — |
| mix-infra-k8s-helm | Go Template, YAML | no-lockfile, ambiguous-extension, templated-config, service-in-infra | — | — |
| mix-infra-tool-versions | JavaScript, Python | version-disagree, no-lockfile, build-only-dependency, service-from-config | — | — |
| mix-php-laravel | Blade, CSS, JavaScript, PHP | shared-root, unit-no-name, toolchain-in-dependencies, no-lockfile, ambiguous-extension, shebang-only, install-scripts, missing-file, service-from-config | — | — |
| mix-poly-firebase | HTML, Kotlin, Python, Rust, TSX, TypeScript | nested-module, independent-units, no-build-file, unit-no-name, file-in-several-units, platform-sdk, no-lockfile, build-only-dependency, binary-file, needs-build, build-generates-code, missing-file, saas-service, undeclared-connections | D-044, D-108, D-109, D-223 | — |
| mix-poly-grpc | Go, Protocol Buffer, Python | unit-no-name, build-only-dependency, generated-file, undeclared-connections, shared-contract | — | — |
| mix-poly-openapi | Makefile, OASv3-yaml, Python, TypeScript | no-lockfile, undeclared-imports, build-only-dependency, ambiguous-extension, generated-file, undeclared-connections, shared-contract | — | — |
| mix-ruby-rails | HTML+ERB, Ruby | unit-no-name, no-lockfile, scope-from-groups, shebang-only, templated-config, service-from-config | D-059 | — |
| mix-swift-spm | Swift | name-mismatch, source-sets, version-range, locked-versions, needs-build | — | — |
| mix-terraform-modules | HCL | unit-no-name, version-range, locked-versions, internal-link | — | — |

#### py (21)

| Progetto | Linguaggi | Casi | Rivelate | Citate |
| --- | --- | --- | --- | --- |
| py-conda-env | Python | toolchain-in-dependencies, no-lockfile, two-package-managers, included-requirement-files | — | — |
| py-django | Python | unit-no-name, no-lockfile, false-generated, service-from-config, framework-from-files | — | — |
| py-fastapi-compose | Dockerfile, Python | version-in-image, no-lockfile, build-only-dependency, service-in-infra | — | — |
| py-hatch-envs | Python | version-matrix, no-lockfile, scope-from-groups, build-only-dependency | — | — |
| py-monorepo-path-deps | Python | independent-units, no-lockfile, internal-link, build-only-dependency | — | — |
| py-namespace-packages | Python | independent-units, name-mismatch, custom-source-roots, no-lockfile, build-only-dependency | — | — |
| py-notebooks | Jupyter Notebook, Python | no-lockfile, declared-in-source, build-only-dependency | — | — |
| py-pdm | Python | version-absent, locked-versions, scope-from-groups, build-only-dependency | — | — |
| py-pep723-scripts | Python | no-build-file, unit-no-name, no-lockfile, declared-in-source | — | — |
| py-pip-tools | Python | unit-no-name, locked-versions, transitive-not-direct, included-requirement-files, framework-from-files | — | — |
| py-pipenv | Python | unit-no-name, locked-versions, transitive-not-direct, scope-from-groups | — | — |
| py-poetry-groups | Python | toolchain-in-dependencies, locked-versions, transitive-not-direct, scope-from-groups, build-only-dependency | — | — |
| py-requirements-includes | Python | unit-no-name, version-absent, no-lockfile, internal-link, git-dependency, build-only-dependency, included-requirement-files | — | — |
| py-setup-cfg-extras | Python | no-lockfile, scope-from-groups, build-only-dependency | D-172 | — |
| py-setup-py-dynamic | Python | computed-dependencies, needs-build | — | — |
| py-setup-py-static | Python | custom-source-roots, no-lockfile | — | — |
| py-undeclared-scripts | Python | no-build-file, unit-no-name, name-mismatch, undeclared-imports | — | — |
| py-uv-src-layout | Python | custom-source-roots, locked-versions, transitive-not-direct, scope-from-groups, build-only-dependency | — | — |
| py-uv-workspace | Python | virtual-root, locked-versions, transitive-not-direct, internal-link, build-only-dependency | — | — |
| py-vendored-generated | Protocol Buffer, Python | no-lockfile, build-only-dependency, generated-file, vendored-code | — | — |
| py-version-disagree | Python | version-disagree, no-lockfile, build-only-dependency | — | — |

#### sys (25)

| Progetto | Linguaggi | Casi | Rivelate | Citate |
| --- | --- | --- | --- | --- |
| sys-bazel | C++, Starlark | targets-as-units, version-range, no-lockfile, scope-from-groups, build-only-dependency | — | — |
| sys-c-macro-annotations | C, C++, CMake | targets-as-units, file-in-several-units, build-variants, ambiguous-extension | — | — |
| sys-cmake-presets | C, CMake | targets-as-units, build-variants, version-disagree, version-absent | D-137 | — |
| sys-cmake-targets | C++, CMake | targets-as-units, inherited-settings, version-range, no-lockfile, ambiguous-extension | — | — |
| sys-cpp-header-only | C++, CMake | targets-as-units, build-variants, ambiguous-extension | — | — |
| sys-cpp-vcpkg-conan | C++, CMake | targets-as-units, locked-versions, build-only-dependency, two-package-managers | D-125 | — |
| sys-git-submodule-absent | C++, CMake | targets-as-units, git-dependency, submodule-absent | D-126 | — |
| sys-go-buildtags | Go | build-variants | — | — |
| sys-go-cgo | C, Go | build-variants | D-142 | — |
| sys-go-generated | Go | generated-file, false-generated | — | — |
| sys-go-nested | Go | nested-module, independent-units, internal-link, documentation-tree | — | — |
| sys-go-single | Go | name-mismatch, version-range, locked-versions | — | — |
| sys-go-toolchain | Go | version-disagree | — | — |
| sys-go-vendor | Go | locked-versions, vendored-code | — | — |
| sys-go-workspace | Go | virtual-root, locked-versions, internal-link | — | — |
| sys-make-plain | C, Makefile | targets-as-units | — | D-255 |
| sys-meson | C, Meson | targets-as-units, name-mismatch, build-variants | — | — |
| sys-rust-buildrs | Rust | locked-versions, build-only-dependency, needs-build, build-generates-code | — | — |
| sys-rust-features | Rust | build-variants, version-range, locked-versions | — | — |
| sys-rust-path-git | Rust | independent-units, locked-versions, internal-link, git-dependency | — | — |
| sys-rust-shared-test-module | Rust | file-in-several-units | — | — |
| sys-rust-single | Rust | name-mismatch, version-range, version-absent, locked-versions | — | — |
| sys-rust-tauri | HTML, JavaScript, Rust | nested-module, shared-name, no-lockfile, build-only-dependency, needs-build, build-generates-code, missing-file | — | — |
| sys-rust-toolchain-conflict | Rust | version-disagree | — | — |
| sys-rust-workspace | Rust | workspace-glob, virtual-root, nested-module, name-mismatch, inherited-settings, locked-versions, version-indirect, internal-link | — | — |

### Fixture `jvm-ver` (18)

| Progetto | Cosa dichiara | Rivelate | Citate |
| --- | --- | --- | --- |
| jvm-ver-gradle-mixed-tc8 | Gradle, Java e Kotlin con jvmToolchain(8) | — | — |
| jvm-ver-gradle-src6 | Gradle, sourceCompatibility 1.6 | — | — |
| jvm-ver-gradle-src8 | Gradle, sourceCompatibility 1.8 | — | — |
| jvm-ver-gradle-tc11 | Gradle, toolchain 11 | — | — |
| jvm-ver-gradle-tc21 | Gradle, toolchain 21 | — | — |
| jvm-ver-gradle-tc25 | Gradle, toolchain 25 | — | — |
| jvm-ver-gradle-tc8 | Gradle, toolchain 8 | — | — |
| jvm-ver-mvn-11 | Maven, source 11 | — | — |
| jvm-ver-mvn-14 | Maven, source 14 | — | — |
| jvm-ver-mvn-21 | Maven, source 21 | — | — |
| jvm-ver-mvn-25 | Maven, source 25 | — | — |
| jvm-ver-mvn-5 | Maven, source 1.5 | — | — |
| jvm-ver-mvn-6 | Maven, source 1.6 | — | — |
| jvm-ver-mvn-7 | Maven, source 1.7 | — | — |
| jvm-ver-mvn-8 | Maven, source 1.8 | — | — |
| jvm-ver-mvn-9 | Maven, source 9 | — | — |
| jvm-ver-mvn-cfg6 | Maven, source 1.6 nel plugin del compilatore | — | — |
| jvm-ver-mvn-rel8 | Maven, release 8 | — | — |

Le nominano tutte insieme (`jvm-ver-*`): rivelate D-102, D-103, D-104, D-179, D-181, D-226; citate —.

### Repository veri (18)

| Progetto | Repository e commit | Casi | Rivelate | Citate |
| --- | --- | ---: | --- | --- |
| mix-real-chi | github.com/go-chi/chi `c64ed7d6635f` | 6 | D-149 | — |
| mix-real-javapoet | github.com/square/javapoet `b9017a9503b7` | 6 | D-016, D-054, D-099, D-100, D-178, D-220 | — |
| mix-real-klaxon | github.com/cbeust/klaxon `1173bdc568a6` | 10 | D-098 | — |
| mix-real-python-semver | github.com/python-semver/python-semver `b6e83e3e40d3` | 10 | D-031, D-088, D-183, D-206, D-248 | — |
| mix-real-semver | github.com/dtolnay/semver `280ebcb6edac` | 8 | D-143, D-209, D-238 | D-176, D-230 |
| mix-real-tinyxml2 | github.com/leethomason/tinyxml2 `9148bdf719e9` | 11 | D-043, D-137, D-209, D-236 | D-230, D-255 |
| mix-real-tududi | github.com/chrisvel/tududi `71da9d7b34df` | 9 | D-145, D-146, D-147, D-182, D-185, D-186, D-187 | D-189, D-213, D-240, D-251 |
| mix-real-zlib | github.com/madler/zlib `51b7f2abdade` | 15 | D-043, D-113, D-130, D-133, D-134, D-209, D-220 | D-010, D-065, D-230 |
| real-app-full-stack-fastapi | github.com/fastapi/full-stack-fastapi-template `aabb90126964` | 21 | D-056, D-088, D-188, D-195, D-197, D-240, D-246, D-248, D-252, D-254, D-260 | D-171, D-213, D-251, D-253 |
| real-app-hoppscotch | github.com/hoppscotch/hoppscotch `55908a76a1d0` | 20 | D-143, D-144, D-159, D-160, D-163, D-237 | D-080, D-239 |
| real-app-jhipster-sample | github.com/jhipster/jhipster-sample-app `6b000b5d23a3` | 17 | D-111, D-194 | — |
| real-app-kotlinconf | github.com/JetBrains/kotlinconf-app `146e891c150c` | 18 | D-055, D-057, D-058, D-110, D-158 | — |
| real-app-memos | github.com/usememos/memos `509e41bd1a1b` | 10 | D-160 | — |
| real-svc-eshop | github.com/dotnet/eShop `913acea66708` | 16 | D-018, D-059, D-113, D-114, D-116, D-118, D-119, D-120, D-198, D-241, D-249 | — |
| real-svc-otel-demo | github.com/open-telemetry/opentelemetry-demo `b825c7c25726` | 26 | D-059, D-094, D-105, D-106, D-107, D-114, D-132, D-135, D-240, D-255, D-259 | D-071 |
| real-svc-petclinic-microservices | github.com/spring-petclinic/spring-petclinic-microservices `e8b747ab5227` | 17 | — | — |
| real-svc-robot-shop | github.com/instana/robot-shop `55292e2199f2` | 14 | D-094, D-140, D-141 | — |
| real-svc-voting-app | github.com/dockersamples/example-voting-app `63e9150ca17a` | 12 | D-114 | — |

### Altri progetti di prova

I progetti fuori dal corpus che i commit descrivono:

- il codice di Daodan: la pipeline con il passo dinamico, su Modal, osserva 1.361 punti e chiude 82 buchi (`d94f92470`). Schede D-085, D-169;
- phazly: il grafo dall'indice contro il passaggio per posizione (`09537b2b9`). Scheda D-087;
- il postgres di tududi su un Docker vero, in un sandbox a macchina virtuale di Modal (`b85aa1b9f`): raggiunto a localhost e per nome, con 1.1.1.1 irraggiungibile dal pod. Scheda D-182;
- una migrazione che scrive una tabella accanto a postgres, con test che la leggono, su un Docker vero in un sandbox a macchina virtuale (`f024ba3a3`). Scheda D-213;
- un postgres di GitLab senza controllo di salute, che risponde in 1,8 secondi, con test che aprono una sessione a db:5432 (`23de469c4`). Scheda D-202;
- uno stadio di Dockerfile della stessa forma di quello di dispatch, che costruisce: da 0 a 1 file Go indicizzato (`f04dab9d5`). Scheda D-141;
- i sandbox a macchina virtuale per Valgrind: `valgrind true` su 48 dimensioni d'ambiente, uno stack profondo, il cargo test di una fixture sotto Callgrind (`8ef21896f`). Scheda D-209;
- 18 progetti, uno per versione di Java (Java 5-25, Maven e Gradle), misurati su Modal (`21b3cb39b`), poi diventati le fixture `jvm-ver` (`347bc1403`). Schede D-102, D-103, D-104;
- i progetti delle prove della regola dell'host, con un file che lascia un segno se eseguito:
  - un `dotnet` sul PATH (`15960a591`, D-241), un `core.fsmonitor` (`3f03a0929`, D-245) e un file Python letto con uv vero (`7ecbaed48`, D-252), nei test;
  - un pacchetto Python, su Modal con gli strumenti veri (`ef6641248`, D-248);
  - un build.rs che scrive un file, su Modal (`293e3bfac`, D-239); un crate con un build script e una macro procedurale che lasciano un segno, e cargo, rustc, rust-analyzer e rustup finti sull'host (`benchmarks/project-model/modal_rust_container.py`, `c714e6298`, D-239);
  - un pacchetto con solo un sdist il cui `setup.py` lascia un segno, con uv vero (`a9b4e1df2`, D-253);
  - un `svelte.config.js`, lo strumento Vue e svelte-kit che lasciano un segno se eseguiti (`b9aeca1fb`, D-258);
- un `.env` tracciato il cui valore arriva al servizio e a nulla di ciò che la corsa tiene, su Modal (`b1f14ac08`, D-240);
- libdeflate v1.23 e una sonda C e C++ su `_mm_pause`, indicizzate con `clang.index()` vero su Modal (`125ab9ebd`, D-255).

### Difetti che nessuna fixture copre

Le schede della pre-mappa, degli analizzatori e del passo dinamico, salvo quelle dell'host, che non nominano nessuna delle 122 fixture scritte a mano (le 104 del corpus e le 18 `jvm-ver`), per lingua: nessuna fixture riproduce ancora quei difetti.

- `tutti` (34): D-001, D-004, D-005, D-018, D-019, D-022, D-023, D-024, D-031, D-032, D-033, D-034, D-035, D-037, D-062, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-081, D-082, D-115, D-149, D-167, D-168, D-182, D-196, D-201, D-202, D-245, D-250
- `java` (26): D-003, D-016, D-025, D-026, D-027, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-090, D-091, D-092, D-093, D-094, D-099, D-100, D-101, D-105, D-106, D-111, D-178
- `python` (26): D-006, D-007, D-028, D-047, D-048, D-049, D-052, D-074, D-075, D-084, D-085, D-086, D-087, D-088, D-169, D-183, D-184, D-188, D-197, D-199, D-200, D-246, D-247, D-248, D-252, D-253
- `javascript` (22): D-013, D-021, D-046, D-049, D-051, D-053, D-056, D-072, D-147, D-158, D-170, D-171, D-185, D-186, D-187, D-189, D-190, D-191, D-192, D-194, D-195, D-198
- `c` (21): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-127, D-128, D-130, D-131, D-132, D-133, D-134, D-136, D-177, D-236, D-259
- `kotlin` (21): D-016, D-027, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-089, D-091, D-092, D-093, D-094, D-105, D-106, D-107, D-110, D-166
- `cpp` (20): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-127, D-128, D-130, D-131, D-132, D-133, D-135, D-177, D-236, D-259
- `typescript` (18): D-008, D-009, D-029, D-072, D-073, D-129, D-145, D-146, D-147, D-150, D-151, D-152, D-157, D-160, D-170, D-194, D-197, D-198
- `csharp` (14): D-010, D-021, D-049, D-113, D-116, D-117, D-118, D-119, D-120, D-165, D-198, D-241, D-242, D-249
- `go` (12): D-002, D-020, D-045, D-078, D-079, D-138, D-139, D-140, D-141, D-173, D-174, D-257
- `rust` (12): D-014, D-021, D-030, D-078, D-143, D-144, D-173, D-175, D-176, D-237, D-238, D-239
- `css` (4): D-161, D-162, D-163, D-164
- `vue` (3): D-080, D-155, D-258
- `scala` (2): D-011, D-092
- `svelte` (2): D-080, D-258
- `dart` (1): D-015
- `elixir` (1): D-012
- `php` (1): D-015
- `swift` (1): D-030

## Schede

### Pre-mappa, snapshot e preparazione

#### D-001 Due build system nella stessa cartella fusi in un'unità
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** il lettore dei moduli dava una sola unità dove una cartella ha due build system.
- **Spiegazione:** `scripts/modules.py` fondeva le build affiancate della stessa cartella; ora restano due unità.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f` (14 novembre), `scripts/modules.py`.
- **Verifica:** per l'intero commit, sulle 122 fixture nessuna faccetta di nessuna famiglia peggiora:
  - membri di workspace in più: da 486 a 1;
  - dipendenze trovate: da 508 a 574, quelle in più da 332 a 52;
  - dipendenze fra unità: da 70 a 81.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-002, D-003, D-004 e D-005.

#### D-002 Go: requisiti indiretti letti e moduli legati fuori da un workspace
- **Tag:** lingua go · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** la pre-mappa dava a un modulo Go dipendenze e archi che non dichiara.
- **Spiegazione:** il lettore leggeva anche i requisiti indiretti di go.mod e legava moduli che nessun workspace unisce; ora legge i soli requisiti diretti e lega i moduli solo dentro un workspace.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** D-020 corregge gli archi Go della pre-mappa (`99112d0b9`).

#### D-003 Maven: dipendenze non lette come gruppo:artefatto e profili taciuti
- **Tag:** lingua java · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Maven
- **Descrizione:** le dipendenze Maven non erano quelle di primo livello e i profili non valutati non comparivano.
- **Spiegazione:** ora il lettore legge le dipendenze di primo livello come gruppo:artefatto e dichiara i profili che non valuta.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** —

#### D-004 Un glob di workspace crea un'unità per cartella
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** membri di workspace inventati: 486 in più sulle 122 fixture.
- **Spiegazione:** un glob di workspace diventava un'unità per ogni cartella che lo soddisfa; ora sceglie fra le unità dichiarate.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001: membri in più da 486 a 1.
- **Stato:** risolto.
- **Note:** —

#### D-005 Un bersaglio ambiguo scelto invece che dichiarato
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** fra due bersagli possibili il lettore ne sceglieva uno.
- **Spiegazione:** un bersaglio ambiguo ora è una lacuna, non una scelta.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** —

#### D-006 Gruppi di sviluppo di pyproject non letti
- **Tag:** lingua python · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva i gruppi di sviluppo di pyproject; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1` (15 novembre), `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-007–D-016 e D-220.

#### D-007 setup.cfg non letto
- **Tag:** lingua python · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva setup.cfg; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-008 Import map di Deno non lette
- **Tag:** lingua typescript · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento Deno
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva le import map di Deno; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-009 angular.json non letto
- **Tag:** lingua typescript · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva angular.json; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-010 Soluzioni .NET fuori dalla radice non lette
- **Tag:** lingua csharp · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non trovava le soluzioni fuori dalla radice; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** la risposta attesa delle soluzioni .NET di zlib è corretta nello stesso commit (D-220).

#### D-011 Sottoprogetti sbt non letti
- **Tag:** lingua scala · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento sbt
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva i sottoprogetti sbt; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-012 Umbrella di Mix non letto
- **Tag:** lingua elixir · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento Mix
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva un progetto umbrella di Mix; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-013 Dipendenze `file:` di npm non lette dal lettore dei moduli
- **Tag:** lingua javascript · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento npm
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva le dipendenze `file:` di npm; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** la fonte npm della pre-mappa ha un difetto simile, D-017.

#### D-014 Rinomina e tabelle target di Cargo non lette
- **Tag:** lingua rust · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento Cargo
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva la rinomina di una dipendenza né le tabelle target di Cargo; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-030 tratta il nome del pacchetto di Cargo nella pre-mappa.

#### D-015 Requisiti di piattaforma di Composer e SDK di pub contati come dipendenze
- **Tag:** lingua php, dart · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Composer, pub
- **Descrizione:** dipendenze in più nelle unità PHP e Dart.
- **Spiegazione:** i requisiti di piattaforma di Composer e gli SDK di pub non sono pacchetti, e il lettore li contava come tali.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-016 Un build incluso contato come membro del workspace
- **Tag:** lingua java, kotlin · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Gradle
- **Descrizione:** un build incluso compariva fra i membri.
- **Spiegazione:** un build incluso non è un membro del workspace; il lettore lo contava.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026; la risposta attesa del workspace di javapoet ne dipende.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`. Anche l'adattatore del banco non lo conta più fra i membri (`9c17c7686`).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-220.

#### D-017 Pacchetti locali `file:` di npm senza archi nella pre-mappa
- **Tag:** lingua javascript · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento npm
- **Descrizione:** in js-local-and-git-deps la risposta di npm copriva un arco verso un pacchetto locale che `modules.py` trova; la misura del 15 novembre lo dava come aperto (`22524b57b`).
- **Spiegazione:**
  - fuori da un workspace, npm elenca un pacchetto collegato a una cartella del progetto solo con `:link`;
  - la fonte chiedeva la radice e i membri, quindi dichiarava nessun arco e copriva quello che `modules.py` legge.
- **Progetto e caso:** js-local-and-git-deps — misura sui 122 progetti, 15 novembre 2026.
- **Rimedio:** `db45bcc93` (15 novembre), `scripts/premap/npm.py`:
  - la fonte chiede anche `:link`;
  - se `:link` non risponde, non dichiara archi e lascia la lacuna.
- **Verifica:** le risposte degli strumenti sono registrate di nuovo nel container; per il resto, solo test.
- **Stato:** risolto.
- **Note:** —

#### D-018 Una dipendenza di un file centrale data all'unità più vicina
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** dipendenze inventate; in eShop 72 voci in più.
- **Spiegazione:**
  - un catalogo di versioni o un file centrale delle versioni dice quali versioni esistono, non quale unità le usa;
  - la pre-mappa le attribuiva all'unità più vicina, cioè le inventava;
  - ora l'unità la dà solo il manifesto di un'unità.
- **Progetto e caso:** eShop e il corpus della pre-mappa — misura salvata, 15 novembre 2026.
- **Rimedio:** `de353d251` (15 novembre), `scripts/premap/renovate.py`.
- **Verifica:** la misura salvata, simulata:
  - dipendenze trovate: da 720 a 733;
  - in più: da 150 a 83;
  - sbagliate: da 35 a 32;
  - in più in eShop: da 72 a 1.
- **Stato:** risolto.
- **Note:** —

#### D-019 Un arco fra unità contato anche come dipendenza
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** nella misura le voci in più erano invenzioni della pre-mappa, nessuna una lacuna delle risposte attese.
- **Spiegazione:** un arco fra due unità del progetto veniva contato anche come dipendenza esterna.
- **Progetto e caso:** corpus della pre-mappa — misura sui 122 progetti su Modal, 15 novembre 2026.
- **Rimedio:** `99112d0b9` (15 novembre):
  - file: `scripts/premap/__init__.py`, `premap/go.py`, `premap/module_graph.py`, `premap/renovate.py`;
  - riproduzione: `benchmarks/project-model/tools/premap_replay.py`.
- **Verifica:** per l'intero commit, le risposte registrate dei 122 progetti sono rigiocate con `tools/premap_replay.py`:
  - dipendenze: 746 trovate, 76 in più e 45 sbagliate diventano 785, 30 e 13;
  - toolchain: 135, 47 e 24 diventano 137, 6 e 16;
  - archi in più: da 2 a 0;
  - sulle faccette che il commit non tocca, la riproduzione dà gli stessi numeri della misura su Modal.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-020–D-030.

#### D-020 Go: un arco fra moduli senza replace né go.work
- **Tag:** lingua go · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** archi Go in più nella pre-mappa.
- **Spiegazione:** ora Go traccia un arco solo se un replace punta alla cartella o un go.work elenca entrambi.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`, `scripts/premap/go.py`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-002.

#### D-021 Una versione scritta in un file centrale non completava la voce dell'unità
- **Tag:** lingua javascript, csharp, rust · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento pnpm, Cargo, NuGet
- **Descrizione:** voci senza versione dove la versione sta in un file centrale.
- **Spiegazione:** una versione scritta in un file centrale ora completa la voce dell'unità che nomina il pacchetto. Sono file centrali le props di NuGet, il catalogo di pnpm e la tabella del workspace di Cargo.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`, `scripts/premap/renovate.py`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-018; lo schema del banco ha la stessa regola (`1420247ad`, D-221).

#### D-022 Un vincolo dichiarato contato come pacchetto
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** toolchain in più o sbagliate fra le dipendenze.
- **Spiegazione:** un vincolo che il file dichiara è una toolchain, non un pacchetto.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: toolchain in più da 47 a 6.
- **Stato:** risolto.
- **Note:** —

#### D-023 Script, task, replace e import verso un percorso contati come pacchetti
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** dipendenze in più.
- **Spiegazione:** script, task, replace e import verso un percorso non sono pacchetti.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-024 Una toolchain diversa da quella che il file scrive
- **Tag:** lingua tutti · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento —
- **Descrizione:** toolchain sbagliate.
- **Spiegazione:** ora una toolchain è ciò che un file scrive.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: toolchain sbagliate da 24 a 16.
- **Stato:** risolto.
- **Note:** —

#### D-025 Il wrapper Maven dava sé stesso invece di Maven
- **Tag:** lingua java · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Maven
- **Descrizione:** una voce del wrapper al posto di Maven.
- **Spiegazione:** il wrapper Maven dà Maven, non sé stesso.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-026 POM genitore e BOM importato senza scope parent e bom
- **Tag:** lingua java · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Maven
- **Descrizione:** POM genitore e BOM importato contati come dipendenze ordinarie.
- **Spiegazione:** il genitore e un BOM importato hanno scope parent e bom: il build li scarica e il codice non li usa.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** lo schema del banco ha la stessa regola (`1420247ad`, D-221).

#### D-027 Uno scope dato alle dipendenze di Gradle
- **Tag:** lingua java, kotlin · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Gradle
- **Descrizione:** dipendenze Gradle con uno scope che il build non dice.
- **Spiegazione:** Gradle non dice la configurazione, quindi nessuno scope.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-028 Un file di pip-compile contato come dichiarazione
- **Tag:** lingua python · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento pip-compile
- **Descrizione:** dipendenze in più dai file generati da pip-compile.
- **Spiegazione:** un file di pip-compile non dichiara dipendenze.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-029 Pacchetti di Bazel, Helm, Terraform, Conan e Deno non dichiarati
- **Tag:** lingua typescript, c, cpp · area pre-mappa · tipo completezza · origine corpus della pre-mappa · strumento Deno, Bazel, Conan, Helm, Terraform
- **Descrizione:** dipendenze mancanti per cinque gestori.
- **Spiegazione:** Bazel, Helm, Terraform, Conan e Deno dichiarano pacchetti che la pre-mappa non riportava.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: dipendenze trovate da 746 a 785.
- **Stato:** risolto.
- **Note:** —

#### D-030 Cargo e SwiftPM: il pacchetto con un nome diverso da quello del build tool
- **Tag:** lingua rust, swift · area pre-mappa · tipo correttezza · origine corpus della pre-mappa · strumento Cargo, SwiftPM
- **Descrizione:** nomi di pacchetto che non corrispondono alle risposte attese.
- **Spiegazione:** Cargo e SwiftPM ora nominano il pacchetto come lo nomina il build tool.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-014.

#### D-031 Un collegamento simbolico a un file del progetto: «UNIQUE constraint failed: files.path»
- **Tag:** lingua tutti · area snapshot · tipo correttezza · origine corsa su un progetto · strumento —
- **Descrizione:** python-semver non si riusciva ad analizzare: lo snapshot falliva con «UNIQUE constraint failed: files.path».
- **Spiegazione:** lo snapshot leggeva attraverso i collegamenti e chiamava ogni file con il nome del suo bersaglio, così un collegamento a un file del progetto dava lo stesso percorso due volte.
- **Progetto e caso:** python-semver (`b6e83e3e40d3`) — 15 novembre 2026.
- **Rimedio:** `ea92f3fed` (15 novembre), `scripts/snapshot.py` e `scripts/tree_scope.py`:
  - un collegamento sotto il target non si legge e non si attraversa;
  - è elencato in `scope.skipped.links`;
  - ogni file ha il nome del posto in cui sta.
- **Verifica:** python-semver dà 95 file.
- **Stato:** risolto.
- **Note:** D-032, D-033; nella copia del container, D-206.

#### D-032 Un collegamento verso l'esterno portava dentro un file di fuori
- **Tag:** lingua tutti · area snapshot · tipo sicurezza · origine commit · strumento —
- **Descrizione:** un file fuori dal progetto entrava nello snapshot.
- **Spiegazione:** lo snapshot seguiva il collegamento fino al suo bersaglio esterno.
- **Progetto e caso:** snapshot — 15 novembre 2026.
- **Rimedio:** `ea92f3fed`, come in D-031.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-031.

#### D-033 Un collegamento rotto spariva senza traccia
- **Tag:** lingua tutti · area snapshot · tipo completezza · origine commit · strumento —
- **Descrizione:** un collegamento rotto non compariva da nessuna parte.
- **Spiegazione:** lo snapshot non trovava il bersaglio e saltava il file in silenzio; ora è elencato in `scope.skipped.links`.
- **Progetto e caso:** snapshot — 15 novembre 2026.
- **Rimedio:** `ea92f3fed`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-031.

#### D-034 Grammatiche scaricate da GitHub al primo uso, senza versione fissata
- **Tag:** lingua tutti · area snapshot · tipo sicurezza · origine commit · strumento tree-sitter
- **Descrizione:** la libreria dei parser scaricava da sola le grammatiche al primo uso.
- **Spiegazione:** scaricava da GitHub, in una cartella sua, una versione non fissata.
- **Progetto e caso:** snapshot — 14 novembre 2026.
- **Rimedio:** `d6545b074` (14 novembre), `scripts/languages/_treesitter.py`, `scripts/snapshot.py` e `requirements.txt`:
  - le versioni sono fissate;
  - il pacchetto entra nella cache di Daodan, verificato con lo sha256;
  - lo copia in sola lettura da quello che la macchina ha già, oppure lo scarica.
- **Verifica:** con le grammatiche presenti lo snapshot è identico a prima; per il resto, solo test.
- **Stato:** risolto.
- **Note:** D-035.

#### D-035 Senza rete un file passava in silenzio al lettore a espressioni regolari
- **Tag:** lingua tutti · area snapshot · tipo completezza · origine commit · strumento tree-sitter
- **Descrizione:** una grammatica mancante non dava errore: il file veniva letto con un lettore più debole.
- **Spiegazione:** senza rete il download falliva e il file finiva al lettore a espressioni regolari, senza dirlo.
- **Progetto e caso:** snapshot — 14 novembre 2026.
- **Rimedio:** `d6545b074`. Lo snapshot segna il file come saltato con la causa, senza lettura più debole, ed elenca le grammatiche mancanti.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-034.

#### D-036 Grammatiche scelte senza l'architettura del processo
- **Tag:** lingua tutti · area host · tipo correttezza · origine prova sull'host · strumento tree-sitter
- **Descrizione:** su Windows ARM64 un Python x64 emulato rischiava librerie di grammatiche dell'architettura sbagliata, e la scelta interrogava Windows.
- **Spiegazione:** la scelta passava dal modulo platform; ora il pacchetto si sceglie da `sys.platform` e, su Windows, dall'architettura del processo, così un Python x64 emulato su ARM64 carica le librerie x64.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `68e39dcde` (14 novembre), `scripts/languages/_treesitter.py`. Nessun processo parte.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-038, D-039.

#### D-037 Grammatiche piazzate fra processi senza sicurezza
- **Tag:** lingua tutti · area parser · tipo correttezza · origine commit · strumento tree-sitter
- **Descrizione:** il commit dice che le grammatiche ora si piazzano in modo sicuro tra processi.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470` (16 novembre).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-038 La cartella condivisa di Daodan chiedeva la versione a Windows
- **Tag:** lingua tutti · area host · tipo correttezza · origine prova sull'host · strumento —
- **Descrizione:** trovare la cartella condivisa poteva lanciare il comando `ver`.
- **Spiegazione:** `platform.system()` può lanciare `ver` quando Windows non risponde; `os.name` non lancia nulla.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `bfdca190b` (14 novembre), `scripts/embedding_worker.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-036, D-039.

#### D-039 Il sistema e l'architettura chiesti a Windows con il modulo platform
- **Tag:** lingua tutti · area host · tipo correttezza · origine prova sull'host · strumento —
- **Descrizione:** `ver` partiva anche quando Windows non risponde, e il test dell'indice Java se lo aspettava.
- **Spiegazione:** il sistema e l'architettura si leggevano con il modulo platform; ora si leggono dal processo.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `b5d218801` (14 novembre), `scripts/resolve_edges.py`; il test ora pretende che `ver` non parta.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-040.

#### D-040 Un rustup vecchio installava per conto di un progetto
- **Tag:** lingua rust · area host · tipo sicurezza · origine prova sull'host · strumento rustup
- **Descrizione:** con un rustup che non conosce l'interruttore dell'installazione automatica, un progetto che fissa una toolchain la faceva installare.
- **Spiegazione:** quel rustup non permette di spegnere l'installazione automatica.
- **Progetto e caso:** host con rustup vecchio — 14 novembre 2026.
- **Rimedio:** `b5d218801`. Rust è unavailable, con la causa e il rimedio.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (Rust `unavailable`).
- **Note:** D-041; vale fino a quando le analisi girano nel container.

#### D-041 Cargo, rustc e rust-analyzer installavano nella home dell'utente
- **Tag:** lingua rust · area host · tipo sicurezza · origine prova sull'host · strumento Cargo, rustc, rust-analyzer, rustup
- **Descrizione:** gli strumenti dell'host potevano installare o scaricare per conto di un progetto.
- **Spiegazione:**
  - Cargo, rustc e rust-analyzer partivano con l'installazione automatica di rustup accesa;
  - la sonda leggeva il file di toolchain del progetto.
- **Progetto e caso:** host — 14 novembre 2026.
- **Rimedio:** `6856a0980` (14 novembre), `scripts/resolve_edges.py`:
  - l'installazione automatica è spenta;
  - la sonda non legge il file di toolchain di nessun progetto;
  - se il progetto fissa una toolchain che rustup non ha, Rust è unavailable con la causa e il rimedio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-042.

#### D-042 uv scaricava interpreti e leggeva la configurazione del progetto
- **Tag:** lingua python · area host · tipo sicurezza · origine prova sull'host · strumento uv
- **Descrizione:** uv sull'host scaricava interpreti, leggeva la configurazione del progetto e teneva la cache fuori dalla cartella di Daodan.
- **Spiegazione:** uv partiva con i valori predefiniti.
- **Progetto e caso:** host — 14 novembre 2026.
- **Rimedio:** `6856a0980`. uv non scarica interpreti, non legge la configurazione del progetto e tiene la cache nella cartella condivisa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-041.

#### D-043 I makefile erano «tipo di file non inventariato»
- **Tag:** lingua c, cpp · area pre-mappa · tipo completezza · origine corsa su un progetto · strumento Make, Kiri
- **Descrizione:** la pre-mappa non vedeva i target dei makefile.
- **Spiegazione:** lo snapshot non registrava i makefile (Makefile, GNUmakefile, *.mak, *.mms) e non c'era una fonte make.
- **Progetto e caso:** zlib e tinyxml2 su Kiri — 15 novembre 2026.
- **Rimedio:** `c6767743f` (15 novembre):
  - file: `scripts/premap/make.py`, `scripts/source_files.py`, `scripts/module_inventory.py`, `scripts/premap/container_runner.py`;
  - la fonte make gira nell'esecutore con il Make dell'immagine.
- **Verifica:** su Kiri, con tutte le fonti: zlib da 39 a 50 su 122, tinyxml2 da 1 a 6 su 7.
- **Stato:** risolto. I makefile di altri dialetti sono un buco dichiarato.
- **Note:** —

#### D-044 Android: compileSdk e buildToolsVersion non letti, SDK non installato
- **Tag:** lingua java, kotlin · area preparazione · tipo completezza · origine commit · strumento Gradle, Android SDK
- **Descrizione:** le build Android non avevano l'SDK.
- **Spiegazione:**
  - la pre-mappa non leggeva compileSdk e buildToolsVersion dal modello di Gradle;
  - la preparazione non installava l'SDK.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — 16 novembre 2026.
- **Rimedio:** `a633ebd72` (16 novembre):
  - la preparazione installa da Google gli strumenti a riga di comando fissati per sha256;
  - accetta le licenze come fa una CI e installa solo i pacchetti dichiarati;
  - ANDROID_HOME vale in entrambe le fasi.
- **Verifica:** le risposte attese dichiarano android-build-tools 34.0.0 (`68a846a4a`, D-223); per il resto, solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-045–D-050, D-138, D-139, D-178 e D-224. Dopo il rimedio le build Android si fermano su `google-services.json`, D-109.

#### D-045 Go: girava una versione diversa dalla più alta dichiarata
- **Tag:** lingua go · area preparazione · tipo correttezza · origine commit · strumento —
- **Descrizione:** con più righe `go`, la preparazione non installava la più alta.
- **Spiegazione:** ogni riga `go` è un minimo (go.dev/doc/toolchain), quindi deve girare il Go più alto dichiarato.
- **Progetto e caso:** preparazione Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-046 `node:22-alpine` non letto come Node 22
- **Tag:** lingua javascript · area pre-mappa · tipo completezza · origine commit · strumento Docker, Renovate
- **Descrizione:** un'immagine Docker con una variante non dava la versione di Node.
- **Spiegazione:** il versioning docker di Renovate legge `node:22-alpine` come Node 22; la pre-mappa non lo faceva.
- **Progetto e caso:** pre-mappa delle immagini — 16 novembre 2026.
- **Rimedio:** `a633ebd72`; le risposte attese del benchmark sono corrette di conseguenza.
- **Verifica:** solo test. ANAGRAFICA.md, da rigenerare dopo questa modifica, resta rossa fino a `68a846a4a` (D-222).
- **Stato:** risolto.
- **Note:** D-222.

#### D-047 Gli errori di uv troncati
- **Tag:** lingua python · area preparazione · tipo completezza · origine commit · strumento uv
- **Descrizione:** l'errore di un ripristino Python arrivava tagliato.
- **Spiegazione:** la preparazione non teneva intero l'errore di uv.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `a633ebd72`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-048 Dipendenze git di Python senza l'host né git
- **Tag:** lingua python · area preparazione · tipo completezza · origine commit · strumento git
- **Descrizione:** le dipendenze git di un progetto Python non si installavano.
- **Spiegazione:** la preparazione non raggiungeva l'host che quelle dipendenze dichiarano e non aveva git.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `a633ebd72`:
  - le dipendenze git raggiungono l'host che dichiarano;
  - git arriva da Debian, solo se serve;
  - se non si installano, si installa il resto e il buco le nomina.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-049 I registri dichiarati assenti dalla pre-mappa
- **Tag:** lingua python, javascript, java, kotlin, csharp · area preparazione · tipo completezza · origine commit · strumento uv, pip, npm, pnpm, Yarn, Gradle, Maven, NuGet
- **Descrizione:** la preparazione non sapeva quali registri il progetto dichiara.
- **Spiegazione:** la pre-mappa non riportava i registri dichiarati, cioè gli indici di pip e uv, i lock di npm, pnpm e Yarn, i repository Maven e Gradle e i feed NuGet.
- **Progetto e caso:** pre-mappa — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: finiscono in `units.registries`, senza credenziali.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-052, D-053, D-054.

#### D-050 Gradle avrebbe scaricato i JDK delle toolchain
- **Tag:** lingua java, kotlin · area preparazione · tipo completezza · origine commit · strumento Gradle
- **Descrizione:** una build con toolchain Gradle diverse dal JDK su cui gira non trovava i JDK senza rete.
- **Spiegazione:** Gradle scarica da sé i JDK delle toolchain, e nell'esecuzione la rete è chiusa.
- **Progetto e caso:** build composte con toolchain 17 e 21 — 16 novembre 2026.
- **Rimedio:** `a633ebd72`, `scripts/indexers/jvm.py`:
  - la preparazione installa ogni JDK che le toolchain chiedono;
  - lo dà a Gradle con `org.gradle.java.installations.paths` in `$GRADLE_USER_HOME/gradle.properties`;
  - spegne lo scaricamento con `org.gradle.java.installations.auto-download=false`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-101.

#### D-051 pnpm e Yarn: «Cannot find matching keyid»
- **Tag:** lingua javascript · area preparazione · tipo correttezza · origine commit · strumento Corepack, pnpm, Yarn
- **Descrizione:** pnpm e Yarn non partivano sui Node vecchi: «Cannot find matching keyid».
- **Spiegazione:** i corepack forniti con le versioni vecchie di Node portano le chiavi di npm ruotate nel 2025 e non verificano più i gestori pubblicati dopo.
- **Progetto e caso:** preparazione Node — 16 novembre 2026.
- **Rimedio:** `a94de85fb` (16 novembre), `scripts/preparation.py`:
  - la preparazione installa, con l'npm di quel Node, il corepack più recente compatibile (>=0.31.0);
  - lo mette primo nel PATH, con la verifica accesa;
  - se nessuno si installa, è un buco con la causa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-052 Preparazione Python senza gli host dichiarati e senza il loro nome
- **Tag:** lingua python · area preparazione · tipo completezza · origine commit · strumento —
- **Descrizione:** un ripristino fallito su un host dichiarato non diceva quale host.
- **Spiegazione:** la preparazione non raggiungeva gli host che la pre-mappa elenca per le dipendenze di ogni unità.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `2f0353c03` (16 novembre), `scripts/preparation.py` e `scripts/dynamic/python.py`:
  - `preparation.declared` dà gli host e i manifest che li dichiarano;
  - l'osservatore Python li aggiunge a ciò che la preparazione raggiunge;
  - un host dichiarato che non risponde è `host_unreachable`, con l'host e i file.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-053, D-054.

#### D-053 Dipendenze GitHub di npm senza gli host di download
- **Tag:** lingua javascript · area preparazione · tipo completezza · origine commit · strumento npm
- **Descrizione:** npm non scaricava le dipendenze GitHub.
- **Spiegazione:** un github.com dichiarato non apriva gli host di download di GitHub, da cui npm le scarica.
- **Progetto e caso:** preparazione Node — 16 novembre 2026.
- **Rimedio:** `2f0353c03`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-054 Build JVM senza gli host che il progetto dichiara
- **Tag:** lingua java, kotlin · area preparazione · tipo completezza · origine commit · strumento Gradle, Maven
- **Descrizione:** le build JVM non raggiungevano i repository che dichiarano (JitPack, repository aziendali).
- **Spiegazione:** gli host di `preparation.declared` non arrivavano a `jvm.run`, all'indice di Java e Kotlin né all'osservatore JVM.
- **Progetto e caso:** javapoet (`b9017a9503b7`) — 16 novembre 2026.
- **Rimedio:** `609ca96dd` (16 novembre):
  - `scripts/indexers/jvm.py`, `java.py`, `kotlin.py`;
  - `scripts/dynamic/jvm.py`.
- **Verifica:** su Modal, javapoet:
  - indice Java fresh con i buchi `jdk_unsupported` e `build_edited`;
  - l'osservatore compila sul JDK 8 dichiarato, con Error Prone al suo posto;
  - 389 test e 6.021 siti osservati.
- **Stato:** risolto.
- **Note:** D-099, D-100.

#### D-055 Il modello di Gradle senza i repository dei plugin delle impostazioni
- **Tag:** lingua java, kotlin · area pre-mappa · tipo completezza · origine commit · strumento Gradle
- **Descrizione:** il modello di Gradle di kotlinconf non risolveva i plugin.
- **Spiegazione:** la corsa raggiungeva solo i registri standard, non i repository dei plugin che le impostazioni dichiarano.
- **Progetto e caso:** kotlinconf (`146e891c150c`) — 16 novembre 2026.
- **Rimedio:** `17babc624` (16 novembre). Se il modello di Gradle fallisce, riprova raggiungendo i repository dei plugin delle impostazioni.
- **Verifica:** conferma: kotlinconf supera i repository e si ferma sulla JVM (D-058).
- **Stato:** risolto.
- **Note:** —

#### D-056 Bun dichiarato solo nei workflow non era una toolchain
- **Tag:** lingua javascript · area pre-mappa · tipo correttezza · origine finale · strumento npm, Bun, GitHub Actions
- **Descrizione:** fastapi in finale e in conferma: «sh: 1: bun: not found», `npm test` uscito con 127.
- **Spiegazione:** fastapi dichiara Bun solo nei workflow (oven-sh/setup-bun, bun-version 1.3.12), e il suo script di test lancia `bun run`.
- **Progetto e caso:** fastapi (`aabb90126964`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** `5148e8eb3` (16 novembre), `scripts/premap/renovate.py` e `scripts/dynamic/javascript.py`:
  - la pre-mappa tiene la versione che Renovate già riporta;
  - l'osservatore JavaScript la installa accanto a Node.
- **Verifica:** su Modal `npm test` arriva a Playwright sotto il registratore; dalla pre-mappa, `tests/test_codebase_map_premap.py` (`test_the_bun_a_workflow_sets_up_is_the_bun_toolchain`, in `f024ba3a3`).
- **Stato:** risolto.
- **Note:** `bun test` resta `runner_not_observed`, D-195; il resto dei test di fastapi in D-197.

#### D-057 L'immagine `devcontainers/java:1-21` letta come Java 1
- **Tag:** lingua java, kotlin · area pre-mappa · tipo correttezza · origine conferma · strumento —
- **Descrizione:** kotlinconf dichiara nel devcontainer `mcr.microsoft.com/devcontainers/java:1-21`, e la pre-mappa ne leggeva la versione `1`.
- **Spiegazione:** i tag di quella famiglia di immagini sono `<versione dell'immagine>-<versione di Java>[-<OS>]` oppure `<versione di Java>[-<OS>]`, come dice il README di devcontainers/images (src/java). La pre-mappa ne prendeva il primo numero.
- **Progetto e caso:** kotlinconf — conferma, 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre), `scripts/premap/renovate.py`: `DEV_CONTAINERS` e `_image_version(tag, name)`, che per queste immagini prendono l'ultimo di al massimo due numeri del tag.
- **Verifica:** giro `jvm-kotlinconf`: la toolchain `java 21` è dichiarata in `.devcontainer/devcontainer.json` (fonte renovate@44.239.1).
- **Stato:** risolto.
- **Note:** D-058.

#### D-058 «Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.»
- **Tag:** lingua java, kotlin · area pre-mappa · tipo correttezza · origine conferma · strumento Gradle
- **Descrizione:** in conferma kotlinconf si ferma nel modello di Gradle della pre-mappa e nell'analisi Kotlin: «Could not resolve dev.zacsweers.metro:gradle-plugin:1.5.2. … Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.».
- **Spiegazione:** Gradle girava sul JDK 17 dell'immagine; un plugin del build chiede una JVM 21.
- **Progetto e caso:** kotlinconf — conferma, 16 novembre 2026.
- **Rimedio:** `22dca6da8`:
  - file: `scripts/premap/gradle.py` (`asked_jdk`), `scripts/premap/container_runner.py`, `scripts/indexers/jvm.py`;
  - la pre-mappa e l'analisi ripartono sul JDK dichiarato a quel livello o sopra;
  - se nessuno lo è, ripartono sulla versione che l'errore nomina, con la lacuna `jdk_from_build_error`.
- **Verifica:** giro `jvm-kotlinconf`, 754 secondi:
  - il modello di Gradle riparte su mise java@21.0.13 (`premap-runs/gradle-jdk`) e dà le toolchain del build (core 21, androidApp 11, android-sdk 37.2);
  - nessun `jdk_from_build_error`, perché il devcontainer dichiara il 21;
  - l'analisi passa la configurazione del progetto radice.
- **Stato:** risolto.
- **Note:** l'analisi Kotlin si ferma poi su un altro errore, D-110.

#### D-059 Template ERB, Handlebars, Jinja e Nunjucks fuori dallo snapshot
- **Tag:** lingua ruby, javascript, python · area snapshot · tipo completezza · origine finale · strumento —
- **Descrizione:** questi template non arrivavano nemmeno al passaggio: nessun grafo e nessun avviso.
- **Spiegazione:** lo snapshot non li registrava.
- **Progetto e caso:** snapshot — 16 novembre 2026; nel finale eShop (58 file), otel-demo (7) e mix-ruby-rails (1).
- **Rimedio:** `e15f2ff88` (16 novembre), `scripts/languages/__init__.py` e `scripts/source_files.py`. Entrano nello snapshot dichiarati senza lettore; Jade resta una voce a livello di file, come Pug.
- **Verifica:** finale: «template language: no reader» con eShop 58, otel-demo 7 e mix-ruby-rails 1.
- **Stato:** buco dichiarato (`template language: no reader`).
- **Note:** —

#### D-060 Avviso «senza analyzer» per i linguaggi fatti solo di file di build
- **Tag:** lingua c, cpp · area pre-mappa · tipo correttezza · origine commit · strumento CMake, Meson, Bazel, Make
- **Descrizione:** CMake, Starlark, Meson e i makefile davano l'avviso di linguaggio senza analyzer.
- **Spiegazione:** quei file dichiarano il build che la pre-mappa esegue, e ciò che dichiarano è già nei suoi fatti.
- **Progetto e caso:** pre-mappa — 16 novembre 2026.
- **Rimedio:** `d14200dce` (16 novembre), `scripts/premap/__init__.py` e `scripts/premap/enry.py`. Un linguaggio con anche altri file, come uno script di shell o un frammento .mk che nessun build tool nomina, resta un buco.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-061 Un profilo Conan che chiede una build dal sorgente
- **Tag:** lingua c, cpp · area pre-mappa · tipo completezza · origine commit · strumento Conan, CMake
- **Descrizione:** con un profilo Conan del progetto il configure non si completa.
- **Spiegazione:** quel profilo chiede una build dal sorgente, e Daodan non apre host in più.
- **Progetto e caso:** pre-mappa CMake con profili Conan — 15 novembre 2026.
- **Rimedio:** `7b1e9ee9f` (15 novembre). Ogni profilo aggiunge un install e un configure; quello che chiede la build dal sorgente resta `restore_failed`, con il profilo e la causa.
- **Verifica:** risposte da un run vero.
- **Stato:** buco dichiarato (`restore_failed`).
- **Note:** —

#### D-062 Senza container le fonti di modello non girano
- **Tag:** lingua tutti · area pre-mappa · tipo completezza · origine commit · strumento —
- **Descrizione:** senza un motore di container i comandi di modello della pre-mappa non si eseguono.
- **Spiegazione:** quei comandi girano solo nel container di Daodan.
- **Progetto e caso:** scansione — 15 novembre 2026.
- **Rimedio:** `8e85b2c1e` (15 novembre): la lacuna `model_not_run` dice causa e rimedio, e la scansione riprova quando un motore risponde.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`model_not_run`).
- **Note:** —

#### D-063 Un wrapper Gradle o Maven che punta a un host non ufficiale
- **Tag:** lingua java, kotlin · area preparazione · tipo sicurezza · origine commit · strumento Gradle, Maven
- **Descrizione:** Daodan non scarica lo strumento da un host non ufficiale.
- **Spiegazione:** Gradle e Maven si prendono dalle proprietà del wrapper, e solo dagli host ufficiali.
- **Progetto e caso:** build JVM — 14 novembre 2026.
- **Rimedio:** `f48df5c7d` (14 novembre): `unavailable` con la causa.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** —

#### D-064 Gradle raggiunge anche il Plugin Portal
- **Tag:** lingua java, kotlin · area container · tipo sicurezza · origine review · strumento Gradle, Maven
- **Descrizione:** fra i registri di Gradle c'è anche il Plugin Portal.
- **Spiegazione:**
  - ogni strumento raggiunge solo i suoi registri;
  - Maven e Gradle raggiungono Maven Central, Google e JCenter, che non accettano caricamenti;
  - Gradle raggiunge anche il Plugin Portal, ed è un limite dichiarato.
- **Progetto e caso:** perimetro di rete, dopo la revisione indipendente — 15 novembre 2026.
- **Rimedio:** `177dcae02` (15 novembre), `scripts/container.py`; il limite è scritto nella spec del passo dinamico.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (perimetro di rete di Gradle).
- **Note:** D-203.

#### D-245 Git sull'host eseguiva il `core.fsmonitor` che il progetto configura
- **Tag:** lingua tutti · area snapshot · tipo sicurezza · origine prova sull'host · strumento git
- **Descrizione:** android-sdk, con la prova che sull'host gira solo git: il `.git/config` di un progetto analizzato può nominare un programma in `core.fsmonitor`, e Git lo esegue a ogni lettura dell'indice (`ls-files`, `check-ignore`, `status`) (dal commit `3f03a0929`).
- **Spiegazione:** ogni snapshot e ogni copia per il container eseguivano così sull'host un comando scelto dal progetto, contro la regola invalicabile di `AGENTS.md` (`2753088a3`).
- **Progetto e caso:** snapshot e copia per il container — la prova di android-sdk, 16 novembre 2026.
- **Rimedio:** `3f03a0929` (16 novembre), `scripts/tree_scope.py` (`GIT_OPTIONS`), `scripts/source_files.py`, `scripts/container.py`: le sei chiamate a Git sull'host (`tree_scope` tre volte, `source_files.git_info`, `container.work_tree_git` e `tracked`) passano per primo `-c core.fsmonitor=false`.
- **Verifica:** solo test: un fsmonitor che lascia un segno non gira più (`tests/test_xray_snapshot.py`, `test_git_on_the_host_runs_no_program_the_work_tree_s_own_configuration_names`).
- **Stato:** risolto.
- **Note:** D-161 e D-239, lo stesso difetto: codice del progetto sull'host; i filtri clean di Git, D-250.

#### D-250 `git status` sull'host eseguiva filtri e hook che il progetto configura
- **Tag:** lingua tutti · area snapshot · tipo sicurezza · origine prova sull'host · strumento git
- **Descrizione:** android-sdk: `git status` sull'host eseguiva i filtri clean che la configurazione del work tree nomina per i file a cui un attributo `filter` si applica (riportato da team-lead il 16 novembre).
- **Spiegazione:** lo snapshot chiede a Git se il work tree è sporco con `git status --porcelain` (`scripts/source_files.py:196`, `"dirty": bool(run("status", "--porcelain"))`); `GIT_OPTIONS` (`scripts/tree_scope.py:49`) spegne solo `core.fsmonitor` (D-245).
- **Progetto e caso:** snapshot — la prova di android-sdk, 16 novembre 2026.
- **Rimedio:** `47d98fcde` (16 novembre, android-sdk), `scripts/tree_scope.py`, `scripts/source_files.py`, `scripts/change_set.py`, `scripts/semantic_store.py`:
  - le prove a segni hanno trovato altre due vie: un hook post-index-change in un `core.hooksPath` nominato da un file incluso (`include.path`, `includeIf`) e il filtro di un sottomodulo;
  - `GIT_OPTIONS` aggiunge `-c core.hooksPath=/dev/null` alle sei chiamate a Git sull'host: le impostazioni sulla riga di comando battono i file di configurazione e le loro inclusioni, e Git le passa ai sottomoduli;
  - `source_files.git_info` chiede prima a `check-attr`, che non esegue niente, quali file dichiarano un filtro: se uno lo dichiara, o Git non risponde, `dirty` è sconosciuto con la causa; altrimenti `git --no-optional-locks status --porcelain --ignore-submodules=all`, che non riscrive l'indice;
  - uno status fallito è sconosciuto, non più «pulito», e `change_set` e `semantic_store` dicono «sconosciuto».
- **Verifica:** solo test, a segni: `tests/test_xray_snapshot.py` (`test_with_a_git_filter_declared_dirty_is_unknown_and_no_filter_runs`, `test_git_on_the_host_runs_no_hook_and_nothing_an_included_configuration_names`, `test_git_on_the_host_runs_nothing_a_submodule_s_own_configuration_names`, `test_git_status_runs_no_diff_driver_or_textconv_the_checkout_names`: driver di diff e textconv non girano in status), `tests/test_codebase_map_storage.py` (`test_a_changeset_of_a_tree_whose_dirtiness_git_info_does_not_know_says_unknown`).
- **Stato:** risolto.
- **Note:** D-245.

#### D-252 Un file Python con una sintassi più nuova di quella di Daodan restava un errore di lettura
- **Tag:** lingua python · area snapshot · tipo completezza · origine commit · strumento uv
- **Descrizione:** un file che l'ast di Daodan (Python 3.13) rifiuta, in una cartella che dichiara un Python più nuovo, restava un errore di lettura: in fastapi `deps.py`, che letto con il 3.14.0b3 dà 45 riferimenti (dal commit `7ecbaed48`).
- **Spiegazione:** lo snapshot leggeva ogni file Python con l'ast dell'interprete di Daodan, che non conosce la sintassi delle versioni dopo la sua.
- **Progetto e caso:** fastapi (`aabb90126964`) — commit `7ecbaed48`, 16 novembre 2026.
- **Rimedio:** `7ecbaed48` (16 novembre), `scripts/languages/python_newer.py` e `scripts/snapshot.py`:
  - il file è letto dall'interprete che uv dà per la versione che la cartella dichiara (il `.python-version` più vicino, altrimenti requires-python: la regola di `stated_python`), senza pacchetti;
  - `python_newer.py` gira con `-I -S` fuori dal progetto, riceve i sorgenti su stdin e fa solo il parse; l'ast di Daodan ricostruisce l'albero;
  - la nota dice quale interprete l'ha letto; senza interprete, la nota del buco nomina la versione dichiarata, quella di Daodan e la causa di uv.
- **Verifica:**
  - dal commit, fastapi: archi 4.361 invariati; buchi da 101 a 102, e il nuovo è `except A, B:` (PEP 758), che il Pyright di scip-python 0.6.8 non legge;
  - una prova a segni con uv vero: non girano né il codice del file, né un build backend, né i moduli alla radice con i nomi della libreria standard (`tests/test_codebase_map_python_newer.py`, `test_a_file_is_parsed_by_the_python_its_project_states_and_none_of_the_project_runs`).
- **Stato:** risolto; senza l'interprete della sua versione, il file resta un errore di lettura che la nota spiega.
- **Note:** il commit è un feat; la regola invalicabile ne chiede la prova a segni, che c'è. D-246, l'analisi sul Python della cartella.

#### D-256 Il riscrittore dei commenti esegue sull'host i formattatori sui file del progetto
- **Tag:** lingua python, javascript, typescript, rust, go · area host · tipo sicurezza · origine review · strumento prettier, biome, ruff, black, rustfmt, gofmt
- **Descrizione:** android-sdk: `comment_rewriter._run_formatter` lancia sull'host prettier, biome, ruff, black, rustfmt e gofmt sui file del progetto, e prettier carica la configurazione JavaScript del progetto (riportato da team-lead il 16 novembre).
- **Spiegazione:** `scripts/comment_rewriter.py:358` (`_run_formatter`) prova per linguaggio `ruff format` o `black`, `prettier --write` o `biome format --write`, `rustfmt`, `gofmt -w`, con `subprocess.run` sul file riscritto, il primo che `shutil.which` trova; un formattatore cerca la configurazione a partire dalla cartella del file, e quella di prettier può essere un modulo JavaScript.
- **Progetto e caso:** riscrittore dei commenti — la prova di android-sdk, 16 novembre 2026.
- **Rimedio:** in corso (dynamic-step-2).
- **Verifica:** —. La regola chiede un test con una configurazione di formattatore che, se eseguita, lascia un segno.
- **Stato:** aperto (dynamic-step-2): viola la regola invalicabile di `AGENTS.md` (`2753088a3`).
- **Note:** D-161, D-239, D-245, D-248, D-250 e D-253, lo stesso difetto.

### Analizzatori

#### D-065 Un linguaggio con 0 file indicizzati risultava `fresh`
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** un linguaggio poteva dirsi `fresh` senza un file nell'indice.
- **Spiegazione:** lo stato non guardava quanti file l'indice copre.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459` (16 novembre):
  - file: `scripts/engine_pass.py`, `scripts/pipeline/__init__.py`, `scripts/premap/__init__.py`, `scripts/premap/enry.py`, `scripts/premap/enry_facts.go`;
  - un linguaggio con 0 file indicizzati fallisce con la causa.
- **Verifica:** finale e conferma: «cpp failed: none of the 8 cpp files is in the index: …» per zlib.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-066–D-071.

#### D-066 I file mancanti di un linguaggio riuscito taciuti
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** un linguaggio `fresh` con file fuori dall'indice non lo diceva.
- **Spiegazione:** il passaggio non contava i file dello snapshot assenti dall'indice.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: un evento di buco `files-missing` con il numero e i motivi.
- **Verifica:** finale: la tabella «Linguaggi fresh con file fuori dall'indice» elenca 20 righe, con i motivi.
- **Stato:** risolto.
- **Note:** —

#### D-067 Un build o un run fallito accanto a uno riuscito spariva
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** in un progetto con più build, il fallimento di una non compariva se un'altra riusciva.
- **Spiegazione:** il rapporto dello stadio teneva solo l'esito complessivo.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: il build fallito resta nel rapporto dello stadio come buco.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-068 Un linguaggio letto dallo snapshot senza analyzer non era dichiarato
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** un linguaggio senza analyzer non compariva da nessuna parte, nemmeno nello stato MCP.
- **Spiegazione:** il passaggio guardava solo i linguaggi degli analyzer.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`:
  - il linguaggio è dichiarato, anche nello stato MCP;
  - la pre-mappa lo dichiara per i linguaggi di programmazione che go-enry vede, ora con il tipo.
- **Verifica:**
  - prova vera su Kiri di go-enry con il tipo: solo C# segnalato in un progetto .NET;
  - finale: «Linguaggi senza analizzatore», plsql in 1 caso (1 file) e sql in 7 casi (51 file).
- **Stato:** risolto; i linguaggi senza analyzer sono un buco dichiarato (`no-analyzer`).
- **Note:** —

#### D-069 Le coppie di linguaggi che si chiamano non erano unite né dichiarate
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** Go/C, Python/C, Java/C e simili: le chiamate fra i due linguaggi non sono risolte, e nulla lo diceva.
- **Spiegazione:** ogni stadio carica solo il proprio indice.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`, `scripts/pipeline/__init__.py` (`Union.APART`): il buco `not-joined`.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`not-joined`).
- **Note:** —

#### D-070 La tabella «chi indicizza cosa» della pre-mappa scritta a mano
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** la tabella poteva divergere dagli analyzer.
- **Spiegazione:** era scritta a mano.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: la tabella deriva dagli analyzer.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-071 Linguaggio senza file con AST, e un linguaggio non elencato `fresh` per difetto
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** un linguaggio di cui lo snapshot non legge nessun file entrava nel passaggio come gli altri, e un linguaggio non elencato era `fresh`.
- **Spiegazione:** il valore predefinito di un linguaggio non elencato era «fresh».
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`:
  - un linguaggio senza file con AST entra come non disponibile;
  - il predefinito diventa «missing».
- **Verifica:** finale, otel-demo: «c unavailable: none of the 1 c files was parsed by the snapshot (lexical: 1)».
- **Stato:** risolto.
- **Note:** —

#### D-072 TypeScript: alias di percorso e membri del workspace non presi dalla pre-mappa
- **Tag:** lingua typescript, javascript · area analizzatore · tipo completezza · origine review · strumento tsc, npm, pnpm, Yarn
- **Descrizione:** gli alias di percorso e i membri del workspace che il build tool dichiara non arrivavano all'indicizzatore.
- **Spiegazione:** l'indicizzatore non li prendeva dalla pre-mappa, cioè da tsc e da npm, pnpm o Yarn.
- **Progetto e caso:** audit della copertura, «stessa famiglia di Kotlin sotto Maven» — 16 novembre 2026.
- **Rimedio:** `64edfb930` (16 novembre), `scripts/engine_tools.py` e gli indicizzatori.
- **Verifica:** solo test locali; il commit dice che le prove vere su monorepo vanno fatte su Modal.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-073–D-082.

#### D-073 TypeScript: installazione fallita e dipendenza locale scartata taciute
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** un'installazione fallita o una dipendenza locale scartata non comparivano.
- **Spiegazione:** non erano registrate come buchi.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: sono buchi dichiarati.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-074 Python: cartelle sorgenti e manifest dichiarati non passati a Pyright
- **Tag:** lingua python · area analizzatore · tipo completezza · origine review · strumento Pyright
- **Descrizione:** Pyright non aveva le cartelle sorgenti e i manifest che il progetto dichiara.
- **Spiegazione:** l'indicizzatore non li passava a Pyright né all'ambiente.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/python.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-075 Python: un file fuori da ogni progetto senza motivo
- **Tag:** lingua python · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** un file Python fuori da ogni progetto mancava dall'indice senza una causa.
- **Spiegazione:** nessun motivo era scritto per quel file.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il file ha il suo motivo.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** quei file entrano poi nel grafo con `118689f69` (D-085).

#### D-076 C/C++: MSBuild trattato a parte
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine review · strumento CMake, MSBuild
- **Descrizione:** i progetti MSBuild non seguivano la strada degli altri build non CMake.
- **Spiegazione:** l'indicizzatore C/C++ li trattava a parte.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/clang.py` e `scripts/indexers/clang_run.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-077 C/C++: un configure senza compile_commands.json faceva morire lo stadio
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** lo stadio C/C++ moriva quando un configure non scrive compile_commands.json.
- **Spiegazione:** il file mancante non era gestito come esito.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il configure fallisce con la causa.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-078 Rust e Go: un file senza documento non diceva se il run era fallito
- **Tag:** lingua go, rust · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** un file assente dall'indice non diceva che il run del suo crate o modulo era fallito.
- **Spiegazione:** il motivo non guardava l'esito del run.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/rust.py` e `scripts/indexers/go.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-079 Go: la regola dei nomi dei file (_GOOS, _GOARCH) non conosciuta
- **Tag:** lingua go · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** un file escluso per il suo nome non aveva il motivo giusto.
- **Spiegazione:** l'indicizzatore Go non conosceva la regola dei suffissi _GOOS e _GOARCH.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/go.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** D-139.

#### D-080 Vue e Svelte: un componente con template non dichiarato letto in parte
- **Tag:** lingua vue, svelte · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** un componente con template risultava letto per intero.
- **Spiegazione:** il template non è letto, e nulla lo diceva.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il componente è dichiarato letto in parte.
- **Verifica:** finale, hoppscotch: «template not read: calls and bindings in it are not sites (400)».
- **Stato:** risolto; il template resta non letto, D-159.
- **Note:** D-159.

#### D-081 Lo stadio di posizione rispondeva per linguaggi non suoi
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine review · strumento —
- **Descrizione:** lo stadio di posizione dava risposte fuori dai suoi linguaggi.
- **Spiegazione:** non filtrava per i suoi linguaggi.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: risponde solo per i suoi linguaggi.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-082 Markup senza lettore non dichiarato (Razor, JSP, Freemarker, Velocity, XHTML)
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine review · strumento —
- **Descrizione:** quei file mancavano senza che nulla lo dicesse.
- **Spiegazione:** nessun lettore, e nessuna dichiarazione.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: sono dichiarati mancanti.
- **Verifica:** solo test locali.
- **Stato:** buco dichiarato (markup senza lettore).
- **Note:** D-059.

#### D-083 Le correzioni degli adattatori Java e Kotlin le usava solo il banco
- **Tag:** lingua java, kotlin · area analizzatore · tipo correttezza · origine test · strumento —
- **Descrizione:** un test di guardia segnalava passi definiti dagli adattatori e mai raggiunti dal driver: `same_range` di Java e `classify` di Kotlin (`8e89e94dc`, 14 novembre).
- **Spiegazione:** lo stadio costruiva il percorso a mano e applicava solo alcune correzioni; quelle due le usava il banco di prova, non il prodotto.
- **Progetto e caso:** stadio del grafo — 14 e 15 novembre 2026.
- **Rimedio:** `d06df0522` (15 novembre), `scripts/resolve_edges.py`: il percorso viene da `adapter_traversal`, l'unico punto che conosce le correzioni.
- **Verifica:**
  - il test di guardia non è più atteso rosso;
  - un test dello stadio controlla che ogni correzione sia chiamata;
  - sulle fixture Go, TypeScript e Rust le righe salvate sono identiche a prima.
- **Stato:** risolto.
- **Note:** —

#### D-084 scip-python: «Cannot find module»
- **Tag:** lingua python · area analizzatore · tipo correttezza · origine prova sull'host · strumento scip-python, npm
- **Descrizione:** lo stadio Python moriva nel container con «Cannot find module».
- **Spiegazione:** su questo PC l'installazione npm di scip-python aveva perso `index.js`, e il tool si usava lo stesso.
- **Progetto e caso:** PC di sviluppo — 16 novembre 2026.
- **Rimedio:** `faf7a3b22` (16 novembre), `scripts/indexers/runtime.py`:
  - il tool si usa solo se lo script che esegue c'è;
  - altrimenti si reinstalla una volta, e se manca ancora lo dice con la causa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-085 80 file Python su 211 senza documento
- **Tag:** lingua python · area analizzatore · tipo completezza · origine corsa su un progetto · strumento —
- **Descrizione:** sul codice di Daodan con i suoi test, 80 file Python su 211 restavano senza documento.
- **Spiegazione:** l'analyzer indicizzava solo i progetti dichiarati.
- **Progetto e caso:** il codice di Daodan — 16 novembre 2026.
- **Rimedio:** `118689f69` (16 novembre), `scripts/indexers/python.py` e `scripts/premap/__init__.py`:
  - quando la pre-mappa trova Python che nessuna unità tiene, il checkout è il run;
  - ogni progetto interno resta la radice dei propri import;
  - il codice fuori non si vede per nome, perché sarebbe una supposizione; lo chiude il passo dinamico.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-075.

#### D-086 scip-python 0.6.8 non parte su Windows
- **Tag:** lingua python · area analizzatore · tipo correttezza · origine prova sull'host · strumento scip-python
- **Descrizione:** l'indicizzatore Python non partiva sull'host Windows.
- **Spiegazione:** scip-python 0.6.8 non parte su Windows (dal commit).
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `626ebb3a2` (14 novembre): Python gira nel container.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-087 phazly: bersagli Python diversi da quelli del passaggio per posizione
- **Tag:** lingua python · area analizzatore · tipo correttezza · origine corsa su un progetto · strumento —
- **Descrizione:** su phazly il grafo dall'indice e il passaggio per posizione davano 13 bersagli Python diversi, e 114 riferimenti li aveva solo il passaggio per posizione.
- **Spiegazione:** «le due cause corrette», che il commit non nomina: da verificare.
- **Progetto e caso:** phazly — 14 novembre 2026.
- **Rimedio:** `09537b2b9` (14 novembre).
- **Verifica:** bersagli diversi da 13 a 1, riferimenti del solo passaggio per posizione da 114 a 94.
- **Stato:** risolto.
- **Note:** —

#### D-088 Buchi Python senza causa
- **Tag:** lingua python · area analizzatore · tipo completezza · origine finale · strumento scip-python, Pyright
- **Descrizione:** buchi Python che non dicono perché:
  - conferma, 3 casi: no-occurrence 117, undefined-project-symbol 74, dangling-local 9 (96,0 % di risposta);
  - finale: no-occurrence 484, undefined-project-symbol 199, dangling-local 117, no-position 13.
- **Spiegazione:** dal commit `a6156b7a2`:
  - undefined-project-symbol: tre difetti di scip-python 0.6.8. Un nome che l'`__init__` di una distribuzione riesporta (`sa.Column`, `typer.Typer`, `pytest.fail`) non andava alla distribuzione; `__name__`, `__file__`, `__package__` e `__doc__` non erano della libreria standard; `import semver`, definito come `src.semver`, non passava per la radice sorgente dichiarata;
  - no-occurrence e dangling-local: un valore che il checker tipizza Unknown o Any, oppure un nome che il checker lega e scip-python non nomina.
- **Progetto e caso:** corpus Python — finale e conferma; fastapi (`aabb90126964`) e python-semver (`b6e83e3e40d3`) nella misura del commit; 16 novembre 2026.
- **Rimedio:** `a6156b7a2` (16 novembre), `scripts/indexers/python.py` e `scripts/indexers/python_unbound.py`:
  - l'adattatore risolve i tre difetti; la distribuzione si cerca nel file d'ambiente della corsa;
  - una passata del checker (l'hover del language server di Pyright 1.1.414 su ogni membro) dà a ogni buco restante la sua causa;
  - da `3cef87b5c` (16 novembre) la passata gira anche nel percorso del container (Windows), dopo scip-python.
- **Verifica:** dal commit `a6156b7a2`, su Modal ai commit fissati: fastapi da 167 a 102 buchi (risposte dal 93,3 % al 95,9 %), python-semver da 64 a 54 (dal 97,2 % al 97,7 %); undefined-project-symbol da 65 e 10 a 0.
- **Stato:** risolto; i buchi restanti sono dichiarati con la causa del checker.
- **Note:** D-247, una causa di dangling-local.

#### D-089 Kotlin sotto Maven: 0 file su 2 indicizzati
- **Tag:** lingua kotlin · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-java, Gradle, Maven
- **Descrizione:** nel pilota su Modal del 15 novembre (`dcdffacb0`) Kotlin sotto Maven dava 0 file su 2 indicizzati, senza source set Gradle.
- **Spiegazione:** scip-java indicizza Kotlin solo sotto Gradle.
- **Progetto e caso:** il pilota su 5 casi del driver Modal — 15 novembre 2026.
- **Rimedio:** `ea1e2b7d6` (15 novembre), `scripts/indexers/kotlin.py` e `scripts/premap/maven.py`:
  - sotto Maven la preparazione lancia, per ogni modulo, l'indicizzatore Kotlin che scip-java porta con sé;
  - lo lancia sui file delle cartelle sorgenti che il modello di Maven dichiara: l'effective-pom, anche quelle di kotlin-maven-plugin e build-helper;
  - usa il classpath di Maven, poi riunisce l'indice.
- **Verifica:** su Modal: 2 file su 2, 10 chiamate su 10, cartelle sorgenti 3 su 3 (erano 0 file e 1 cartella).
- **Stato:** risolto.
- **Note:** il motivo di un file mancante non nomina più Gradle.

#### D-090 Java sotto Gradle: aggregazione in avanti e javap sulla cartella sbagliata
- **Tag:** lingua java · area analizzatore · tipo correttezza · origine commit · strumento Gradle, Maven
- **Descrizione:** Java sotto Gradle aveva il buco delle implementazioni.
- **Spiegazione:** l'aggregazione in avanti e javap leggevano `target/`, la cartella di Maven, anche sotto Gradle.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d` (15 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - leggono la cartella del build che ha girato, `target/` per Maven e `build/` per Gradle, in ogni modulo;
  - senza un indice in avanti uguale, il contratto lo dichiara come buco.
- **Verifica:** su Modal, Gradle Java completo senza il buco delle implementazioni.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-091, D-092 e D-093.

#### D-091 Sotto Maven l'indice Java senza il Kotlin dei moduli
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine commit · strumento Maven
- **Descrizione:** una chiamata da Java a Kotlin non arrivava a destinazione.
- **Spiegazione:** sotto Maven il build di Java non indicizzava il Kotlin dei moduli.
- **Progetto e caso:** Maven misto Java e Kotlin — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`: anche il build di Java indicizza il Kotlin dei moduli (`jvm.MAVEN_KOTLIN`, condiviso), così la chiamata finisce dove lo stesso indice la definisce.
- **Verifica:** su Modal, Maven misto: Java 4 chiamate su 4, Kotlin 10 su 10, nessun buco.
- **Stato:** risolto.
- **Note:** D-089.

#### D-092 Un build JVM che Daodan non esegue (sbt, Bazel) non era nominato
- **Tag:** lingua java, kotlin, scala · area analizzatore · tipo completezza · origine commit · strumento sbt, Bazel
- **Descrizione:** il motivo non diceva che il build è sbt o Bazel.
- **Spiegazione:** il motivo non nominava il build.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`: il build è nominato nel motivo.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (sbt e Bazel non eseguiti).
- **Note:** —

#### D-093 Un indice lasciato da un build finito in errore non lo diceva
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** un indice poteva venire da un build fallito senza che il risultato lo dicesse.
- **Spiegazione:** il risultato non guardava l'esito del build.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-094 Java e Kotlin giravano solo alla radice del progetto
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine commit · strumento Gradle
- **Descrizione:** una build in una sottocartella, come il servizio Java di robot-shop o le build Gradle di otel-demo, restava fuori.
- **Spiegazione:** gli indicizzatori JVM partivano solo dalla radice.
- **Progetto e caso:** robot-shop (`55292e2199f2`), otel-demo (`b825c7c25726`) — 15 novembre 2026.
- **Rimedio:** `1dcfba42a` (15 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - le cartelle sono il Gradle e il Maven più esterni della pre-mappa, ognuno in un container suo;
  - ogni indice è nominato dal checkout con la cartella della sua build, e ogni build dice il suo stato;
  - una build che fallisce lascia gli indici delle altre;
  - senza build nella pre-mappa nulla parte, e la causa è detta.
- **Verifica:** finale, otel-demo: le sue build Gradle girano e falliscono per D-105.
- **Stato:** risolto.
- **Note:** D-105.

#### D-095 Maven e Gradle nella stessa cartella: occorrenze doppie
- **Tag:** lingua java, kotlin · area analizzatore · tipo correttezza · origine commit · strumento Gradle, Maven
- **Descrizione:** una cartella con pom.xml e build Gradle dava due indici degli stessi file.
- **Spiegazione:** due indici degli stessi file raddoppiano le occorrenze, perché `code_graph.Index.load` li accoda.
- **Progetto e caso:** jvm-java-version-conflict — 16 novembre 2026.
- **Rimedio:** `9fe650a3a` (16 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - scip-java riceve `--build-tool` dalla pre-mappa;
  - gira Gradle, e Maven solo se Gradle non dà indice.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-096, D-097 e D-180.

#### D-096 Una radice con solo settings.gradle.kts non riconosciuta da scip-java
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine commit · strumento scip-java
- **Descrizione:** scip-java non partiva su una build composta con solo `settings.gradle.kts` alla radice.
- **Spiegazione:** scip-java 0.14.2 non riconosce una radice con solo settings.gradle.kts.
- **Progetto e caso:** jvm-gradle-kts-catalog-composite — 16 novembre 2026.
- **Rimedio:** `9fe650a3a`, `scripts/indexers/jvm.py`: la preparazione vi scrive un `gradlew` che lancia il Gradle portato da Daodan.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-097 Kotlin presente solo negli script di build dato `failed`
- **Tag:** lingua kotlin · area analizzatore · tipo correttezza · origine finale · strumento Gradle
- **Descrizione:** un progetto con Kotlin solo negli script di build (.gradle.kts, buildSrc) aveva Kotlin `failed`.
- **Spiegazione:** nessun compito di compilazione Kotlin compila quei file.
- **Progetto e caso:** jvm-gradle-kts-catalog-composite, jvm-java-version-conflict, jvm-spring-boot-managed — finale, 16 novembre 2026.
- **Rimedio:** `9fe650a3a`, `scripts/indexers/kotlin.py`: Kotlin è `unavailable` con la causa, prima di ogni container.
- **Verifica:** finale, 3 casi: «the build's own Kotlin only (… Gradle scripts and buildSrc files): the pre-map reads them through Gradle, and no Kotlin compile task compiles them».
- **Stato:** buco dichiarato («the build's own Kotlin only»).
- **Note:** —

#### D-098 File Kotlin che nessun compito di compilazione compila o elenca
- **Tag:** lingua kotlin · area analizzatore · tipo completezza · origine finale · strumento scip-java, Gradle
- **Descrizione:** file Kotlin fuori dall'indice in Kotlin `fresh`:
  - jvm-kmp-common-jvm: 2 su 5, «Gradle script: no KotlinCompile task compiles it»;
  - jvm-kotlin-source-sets: 3 su 5, di cui 2 script Gradle e 1 «no Kotlin compile task of the build lists it»;
  - klaxon: 7 su 103, cioè 5 script Gradle, 1 «buildSrc: compiled by its own build, where scip-java's tasks do not run» e 1 che nessun compito elenca.
- **Spiegazione:** quei file non sono compilati dai compiti in cui girano i compiti di scip-java.
- **Progetto e caso:** jvm-kmp-common-jvm, jvm-kotlin-source-sets, klaxon (`1173bdc568a6`) — finale, 16 novembre 2026.
- **Rimedio:** il motivo per file (`2bc7c7459`, D-066).
- **Verifica:** finale.
- **Stato:** buco dichiarato (i motivi citati).
- **Note:** —

#### D-099 javapoet: scip-java 0.14.2 non indicizza Java 8
- **Tag:** lingua java · area analizzatore · tipo completezza · origine real-3 · strumento scip-java
- **Descrizione:**
  - in real-3 l'osservatore di javapoet falliva perché la build girava sul JDK dell'immagine (`7532ed2e7`);
  - nessuna versione di scip-java indicizza javapoet come è dichiarato.
- **Spiegazione:** scip-java 0.14.2 non supporta più Java 8 (dalla 0.13.0).
- **Progetto e caso:** javapoet (`b9017a9503b7`) — real-3, 16 novembre 2026.
- **Rimedio:** `492a7b212` (16 novembre), `scripts/indexers/java.py` e `scripts/indexers/jvm.py`:
  - l'analisi sceglie il JDK con la regola dell'osservatore (`build_jdk`, ora in `indexers/jvm.py`);
  - un JDK dichiarato sotto il 17 si indicizza sul 17, con il buco `jdk_unsupported`.
- **Verifica:** su Modal, javapoet: indice Java `fresh` con i buchi `jdk_unsupported` e `build_edited` (`609ca96dd`).
- **Stato:** buco dichiarato (`jdk_unsupported`).
- **Note:** D-100, D-178.

#### D-100 javapoet: il compilerId di Error Prone scavalca il wrapper di javac
- **Tag:** lingua java · area analizzatore · tipo completezza · origine commit · strumento scip-java, Error Prone, Maven, javac
- **Descrizione:** la build di javapoet non dava l'indice.
- **Spiegazione:** il compilerId di Error Prone nel pom scavalca il wrapper di javac con cui scip-java aggancia il suo plugin.
- **Progetto e caso:** javapoet — 16 novembre 2026.
- **Rimedio:** `492a7b212`:
  - se l'indice arriva solo togliendo Error Prone dal pom, il buco `build_edited` dice cosa è stato tolto e gli errori della prima build;
  - prima lo diceva solo il log.
- **Verifica:** come D-099.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** —

#### D-101 Una toolchain Gradle sotto il 17 compilava sul JDK dell'immagine
- **Tag:** lingua java · area analizzatore · tipo correttezza · origine commit · strumento scip-java, Gradle, javac
- **Descrizione:** analisi e osservatore non compilavano sul JDK della toolchain dichiarata.
- **Spiegazione:**
  - Gradle 9 gira su Java 17 ma compila e testa con le toolchain dichiarate, come dice la sua documentazione;
  - quei JDK non erano installati;
  - il plugin del compilatore di scip-java 0.14.2 è costruito per Java 17 e non si carica in un javac più vecchio.
- **Progetto e caso:** build Gradle con toolchain 8 e 11 — 16 novembre 2026.
- **Rimedio:** `0997b5d4f` (16 novembre), `scripts/indexers/java.py`:
  - la preparazione installa il JDK di ogni toolchain e lo passa a Gradle;
  - quella build dà il buco `jdk_unsupported` con la versione dichiarata e dove.
- **Verifica:** un test fissa l'osservatore su una toolchain 11.
- **Stato:** buco dichiarato (`jdk_unsupported`).
- **Note:** D-050, D-103.

#### D-102 Maven con Java 5 e 6: nessun indice
- **Tag:** lingua java · area analizzatore · tipo completezza · origine prova su Modal · strumento Maven, javac
- **Descrizione:** nella misura su Modal con 18 progetti, uno per versione, Maven con Java 5 e 6 falliva.
- **Spiegazione:** javac 17 non compila sotto il 7.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b` (16 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - il secondo tentativo dichiarato alza a 8 i livelli sotto l'8 nei pom;
  - ogni modifica è nel buco `build_edited`, con l'errore del build dichiarato.
- **Verifica:**
  - java-versions, sul codice a `68a846a4a`: Java `fresh` e osservato in tutte le 18 fixture, 37 file su 37 e 453 siti tutti con risposta;
  - prima di `21b3cb39b` sette non davano indice (README del benchmark).
- **Stato:** buco dichiarato (`build_edited`, `jdk_unsupported`).
- **Note:** dallo stesso commit vengono D-103, D-104 e D-179.

#### D-103 Gradle con toolchain 8 e 11, anche con Kotlin accanto: nessun indice
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-java, Gradle
- **Descrizione:** stessa misura di D-102.
- **Spiegazione:** il plugin di scip-java non si carica sotto il 17.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b`. Sotto Gradle `jvm.RAISE_LEVELS` sostituisce la toolchain sotto il JDK su cui gira il build e alza i livelli, per Java, Kotlin e l'osservatore; tutto è nel buco `build_edited`.
- **Verifica:** come D-102.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** D-101.

#### D-104 Gradle con livello 6: nessun indice
- **Tag:** lingua java · area analizzatore · tipo completezza · origine prova su Modal · strumento Gradle, javac
- **Descrizione:** stessa misura di D-102: Gradle con livello 1.6.
- **Spiegazione:** javac 17 non compila quel livello.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b`, `jvm.RAISE_LEVELS`.
- **Verifica:** come D-102.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** —

#### D-105 otel-demo: «Cannot invoke method toPath() on null object» in ad e recommendation
- **Tag:** lingua java, kotlin · area analizzatore · tipo correttezza · origine finale · strumento scip-java, Gradle
- **Descrizione:** finale, otel-demo: Java e Kotlin `failed`, «scip-java wrote no index (preparation exited with code 1)».
- **Spiegazione:**
  - le build, in `src/ad/build.gradle:70` e `src/recommendation/build.gradle:55`, calcolano `project.projectDir.parentFile.parentFile.toPath()` per arrivare a `pb/` alla radice del repository;
  - la cartella del build era copiata da sola in `/work`, così il nonno era null.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7` (16 novembre), `scripts/indexers/jvm.py`, `java.py` e `kotlin.py`, `scripts/dynamic/jvm.py`:
  - il container di ogni build contiene l'intero checkout (`jvm.run(..., checkout=)`);
  - il build gira nella sua cartella (`DAODAN_ROOT`, `WORK=/work/$DAODAN_ROOT`).
- **Verifica:** giro `jvm-otel-android`, otel-demo:
  - Java `fresh`, 9 file su 9, 693 siti tutti con risposta (in finale: `failed`, senza indice);
  - l'osservatore Java registra 297 siti e 297 archi, e chiude 2 buchi.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-106, D-108 e D-109.

#### D-106 otel-demo fraud-detection sul JDK 21 di un altro build
- **Tag:** lingua java, kotlin · area analizzatore · tipo correttezza · origine finale · strumento Gradle
- **Descrizione:** fraud-detection falliva con «Inconsistent JVM-target compatibility … (21) and (17)».
- **Spiegazione:**
  - fraud-detection dichiara Kotlin jvmTarget 17, senza target Java né toolchain, e il suo Dockerfile costruisce su gradle:9.8.2-jdk17;
  - l'indice riceveva le toolchain dell'intero repository, e `wanted_jdk` sceglieva il 21 di ad e recommendation;
  - compileJava puntava al 21, e il plugin di Kotlin falliva.
- **Progetto e caso:** otel-demo — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7`, `scripts/indexers/jvm.py` (`applying`): un JDK conta per un build solo se lo dichiarano i suoi file o un file in una cartella sopra; vale anche per l'osservatore (`build_jdk`).
- **Verifica:** giro `jvm-otel-android`: l'errore di compatibilità non c'è più, e fraud-detection si ferma su D-107.
- **Stato:** risolto.
- **Note:** D-107.

#### D-107 otel-demo fraud-detection: protos che solo il Dockerfile copia
- **Tag:** lingua kotlin · area analizzatore · tipo completezza · origine jvm-otel-android · strumento Gradle, Docker, protoc
- **Descrizione:** giro `jvm-otel-android`, otel-demo: Kotlin `failed`, «none of the 3 kotlin files is in the index: Gradle script: no KotlinCompile task compiles it (2), no Kotlin compile task of the build lists it (1)».
- **Spiegazione:**
  - `src/fraud-detection/src/main/kotlin/frauddetection/main.kt:14` importa `oteldemo.Demo.*`, le classi che il plugin protobuf genera dai proto;
  - il blocco `protobuf { }` di `src/fraud-detection/build.gradle.kts:78-99` non nomina una cartella dei proto, quindi usa `src/main/proto`;
  - quella cartella la riempie solo il Dockerfile del servizio: `src/fraud-detection/Dockerfile:10`, `COPY ./pb/ ./src/main/proto/`;
  - il build dichiarato, girato sul checkout, non genera quelle classi.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** —. Gli stadi di un Dockerfile si leggono da `f024ba3a3`, ma oggi indicizza dentro uno stadio solo Go (`f04dab9d5`, D-141); la via per C e C++ è in corso (D-135), e la JVM non la usa.
- **Verifica:** —
- **Stato:** aperto (android-sdk): build dichiarata solo in un Dockerfile.
- **Note:** D-135, D-141.

#### D-108 Android: classpath dei test unitari non risolti, nessun compito Android
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine finale · strumento scip-java, Gradle, Android SDK
- **Descrizione:** finale: Kotlin `failed` con «Could not resolve all artifacts for configuration ':core:releaseUnitTestRuntimeClasspath'» e «':app:debugUnitTestCompileClasspath'».
- **Spiegazione:**
  - il plugin Gradle di scip-java non mette nessun compito Android in `scipCompileAll` (issue 177 di scip-java, chiusa come non pianificata);
  - eppure aggiunge il suo plugin javac a ogni JavaCompile e scrive la configurazione di ogni KotlinCompile.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7`:
  - `scripts/indexers/jvm.py` (`SCIP_INDEX`, `ANDROID_INIT`), `java.py` e `kotlin.py`;
  - con l'SDK installato, un build Gradle lancia dopo i compiti di scip-java `daodanAndroidCompile`, che dipende dai compiti `compile*Debug(UnitTest)?Sources` di ogni progetto.
- **Verifica:** giro `jvm-otel-android`: i due casi non si fermano più sui classpath e lanciano le compilazioni debug, fino a `:app:processFreeDebugGoogleServices` e `:app:processDebugGoogleServices`, dove si fermano su `google-services.json` (D-109). Che le varianti diano l'indice è da verificare.
- **Stato:** aperto (dynamic-jvm-2): manca la prova su un build con il suo `google-services.json`.
- **Note:** D-109.

#### D-109 Android: build fermo su `google-services.json` mancante
- **Tag:** lingua java, kotlin · area analizzatore · tipo completezza · origine jvm-otel-android · strumento Gradle, Google Services
- **Descrizione:** giro `jvm-otel-android`, Kotlin `failed`: «Execution failed for task ':app:processFreeDebugGoogleServices'. > File google-services.json is missing. The Google Services Plugin cannot function without it.»:
  - jvm-android-app-lib cerca da `/work/app/src/free/debug/google-services.json` fino a `/work/app/google-services.json`;
  - mix-poly-firebase si ferma in `:app:processDebugGoogleServices` e cerca in `/work/android/app/…`.
- **Spiegazione:** il plugin Google Services (com.google.gms.google-services) legge la configurazione del progetto Firebase, che lo sviluppatore scarica dalla console e il repository non tiene; le fixture non l'hanno.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** `39805f5e7`, `scripts/indexers/jvm.py` (`INPUTS`, `missing_inputs`). Il buco `build_input_missing` dice: «the build stopped without google-services.json, which the Google Services Gradle plugin (com.google.gms.google-services) reads: the Firebase project's configuration, which a developer downloads from the Firebase console, kept out of the repository; Daodan makes none, so the build gives nothing».
- **Verifica:** giro `jvm-otel-android`: il buco è in `steps.analyze.engines.scip-kotlin.gaps` di entrambi i casi.
- **Stato:** buco dichiarato (`build_input_missing`).
- **Note:** D-108.

#### D-110 kotlinconf: «Task with name 'compileKotlinJvm' not found in project ':app:adminApp'»
- **Tag:** lingua kotlin · area analizzatore · tipo correttezza · origine jvm-kotlinconf · strumento scip-java, Gradle
- **Descrizione:** giro `jvm-kotlinconf`, Kotlin `failed`: «scip-java wrote no index (preparation exited with code 1): determine the dependencies of task ':app:adminApp:scipCompileAll'. > Task with name 'compileKotlinJvm' not found in project ':app:adminApp'.».
- **Spiegazione:**
  - il plugin Gradle di scip-java 0.14.2 (`scip-gradle-plugin/src/main/java/org/scip_code/scip_java/gradle/ScipGradlePlugin.java`) mette in `triggers`, per ogni progetto con il plugin Kotlin Multiplatform, i nomi `compileKotlinJvm` e `compileTestKotlinJvm`, senza guardare se il progetto ha un target `jvm()`;
  - poi `project.getTasks().create("scipCompileAll").dependsOn(triggers)` li chiede per nome, e Gradle si ferma su un nome che il progetto non ha;
  - in kotlinconf `app/adminApp` dichiara solo `js(IR)` e `app/webApp` solo `wasmJs` e `js`: nessuno dei due ha `compileKotlinJvm`.
- **Progetto e caso:** kotlinconf (`146e891c150c`) — giro `jvm-kotlinconf`, 16 novembre 2026.
- **Rimedio:** `a13d55787` (16 novembre), `scripts/indexers/jvm.py`:
  - `scip_index` dà a scip-java, per un build Gradle, l'init script di Daodan (`SCIP_GRADLE`, scritto in `${TMPDIR:-/tmp}/daodan-scip.gradle`): dopo la valutazione dei progetti lascia nello `scipCompileAll` di ciascuno solo i compiti che il progetto ha;
  - lo stesso script porta, con l'SDK di Android, i compiti delle varianti debug (`ANDROID_GRADLE`, D-108).
- **Verifica:**
  - giro `jvm-kotlinconf-kmp` (`benchmarks/project-model/results/pipeline/2026-11-16-jvm-kotlinconf-kmp.json`), sull'albero di lavoro con il rimedio poi committato in `a13d55787`: Kotlin da `failed` a `fresh`, 226 file su 271 indicizzati, 16.830 siti, 76,0 % di risposta; buchi no-document 2.214, no-occurrence 1.830, element 1. I 45 file fuori dall'indice dicono perché: «no Kotlin compile task of the build lists it» (34), «Gradle script: no KotlinCompile task compiles it» (11), D-098. Il passo dinamico osserva Kotlin: 984 siti, 988 archi;
  - `tests/test_codebase_map_indexers_jvm.py` (`ScipInitTest`, su un Gradle 9.9.1 vero: `test_a_project_without_the_compile_task_stops_the_build_as_scip_java_s_plugin_leaves_it`, `test_each_project_s_scip_compile_all_asks_only_for_the_compile_tasks_the_project_has`).
- **Stato:** risolto; un target JVM di Kotlin Multiplatform con un altro nome (`jvm("desktop")`) resta non compilato.
- **Note:** D-058, D-098, D-108.

#### D-111 jhipster: 14 file Java con il documento senza occorrenze
- **Tag:** lingua java · area analizzatore · tipo completezza · origine finale · strumento —
- **Descrizione:** finale: 15 file Java su 136 fuori dall'indice, 14 «document without occurrences» e 1 «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** jhipster-sample (`6b000b5d23a3`) — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-112 Un file Java senza documento in due fixture Maven
- **Tag:** lingua java · area analizzatore · tipo completezza · origine finale · strumento Maven, protoc
- **Descrizione:** finale: jvm-maven-multi-bom-profile 1 file su 4 e jvm-protobuf-generated 1 su 2, «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** jvm-maven-multi-bom-profile, jvm-protobuf-generated — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-113 C#: un progetto che Msbuild rifiuta ferma il ripristino intero
- **Tag:** lingua csharp · area analizzatore · tipo correttezza · origine giro-2 · strumento scip-dotnet, Roslyn, MSBuild, dotnet
- **Descrizione:** zlib in giro-2, finale e conferma: «scip-dotnet wrote no index (no documents were indexed; Msbuild failed when processing the file '/work/contrib/dotzlib/DotZLib/DotZLib.csproj' with message: The project file "" must be opened in a version of Visual Studio IDE that supports it and converted to the latest version before it can be built».
- **Spiegazione:** un solo progetto che non si può trattare fermava tutti gli altri:
  - in zlib è DotZLib.csproj, un progetto `<VisualStudioProject>` del vecchio formato, che Msbuild rifiuta;
  - in eShop `dotnet restore eShop.slnx` falliva per intero su un solo progetto che vuole un workload MAUI (NETSDK1147): nessun progetto aveva i suoi pacchetti, Roslyn non legava nessun simbolo di pacchetto, e ne venivano circa 4.400 buchi no-occurrence (dal commit `0cdbae9b2`).
- **Progetto e caso:** zlib (`51b7f2abdade`) — giro-2, finale, conferma; eShop (`913acea66708`) — misura di csharp-dotnet; 16 novembre 2026.
- **Rimedio:**
  - `73b645531` (16 novembre), `scripts/indexers/csharp.py`: un progetto `<VisualStudioProject>`, o una soluzione che ha solo quelli, è `unavailable` con il formato nominato, e non viene lanciato;
  - `0cdbae9b2` (16 novembre), `scripts/preparation.py` (`RESTORES`): se la soluzione non si ripristina, si ripristina ogni progetto che `dotnet sln list` nomina, e il fallimento resta il buco `restore_failed`.
- **Verifica:** solo test (`tests/test_codebase_map_preparation.py`, `test_a_dotnet_solution_that_does_not_restore_restores_each_of_its_projects_and_stays_a_gap`); nessun giro su zlib o eShop dopo i commit: da verificare.
- **Stato:** risolto; il progetto legacy è un buco dichiarato (`unavailable`), e un progetto che non si ripristina resta `restore_failed`.
- **Note:** D-114.

#### D-114 C#: 56,1 % di risposta
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine finale · strumento scip-dotnet
- **Descrizione:** finale: C# `fresh` in 4 casi su 5, 561 file su 561, quota di risposta 56,1 %.
  - buchi: no-occurrence 5.358, no-position 1.021, dangling-local 144, undefined-project-symbol 20;
  - casi `fresh`: mix-dotnet-central, eShop, otel-demo, voting-app.
- **Spiegazione:** le cause misurate da csharp-dotnet, poi corrette in `0cdbae9b2`:
  - il ripristino falliva intero per un solo progetto di workload (D-113): circa 4.400 buchi no-occurrence in eShop;
  - la colonna della riga 1 di un file con il BOM (D-115);
  - i nomi del chiamato qualificati (D-117) e con argomenti di tipo (D-116).
- **Progetto e caso:** mix-dotnet-central, eShop (`913acea66708`), otel-demo, voting-app (`63e9150ca17a`) — finale, 16 novembre 2026.
- **Rimedio:**
  - l'analyzer C# arriva con `56e65e114` (16 novembre);
  - `73b645531` dà una causa a parte dei buchi di eShop (D-116, D-118, D-119, D-120);
  - `0cdbae9b2` corregge il ripristino, il BOM e i nomi (D-113, D-115, D-116, D-117).
- **Verifica:**
  - dal commit `15960a591`, su eShop: risposte C# 86,6 % senza l'osservatore e 87,3 % con l'osservatore (D-241);
  - dal commit `9290d446a`, su eShop: dall'84,67 % al 92,06 % con scip-dotnet costruito con la patch di Daodan (D-116, D-249);
  - negli altri casi nessun giro dopo `0cdbae9b2`: da verificare.
- **Stato:** aperto (csharp-dotnet).
- **Note:** D-113, D-115, D-116, D-117, D-198.

#### D-115 La colonna della riga 1 di un file con il BOM
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine prova su Modal · strumento Roslyn, tsc
- **Descrizione:** csharp-dotnet ha misurato riferimenti della riga 1 senza risposta nei file che iniziano con il BOM.
- **Spiegazione:** un BOM UTF-8 in testa al file spostava di uno le colonne della riga 1 fra lo snapshot, che conta i suoi tre byte, e Roslyn o tsc, le cui colonne UTF-16 iniziano dopo di esso.
- **Progetto e caso:** i casi C# — misura di csharp-dotnet, 16 novembre 2026; vale per ogni linguaggio.
- **Rimedio:** `0cdbae9b2` (16 novembre), `scripts/code_graph.py` (`BOM`): `Index.to_bytes` e `from_bytes` lo saltano, per ogni linguaggio.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_csharp.py`, `test_a_byte_order_mark_moves_no_column_of_the_first_line`).
- **Stato:** risolto.
- **Note:** D-114.

#### D-116 C#: nomi del chiamato con argomenti di tipo
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-dotnet, Roslyn
- **Descrizione:** un chiamato scritto con argomenti di tipo non ha occorrenza nell'indice ed è un buco.
- **Spiegazione:** `ScipCSharpSyntaxWalker` non ha `VisitGenericName`, nella 0.2.16 come sul suo ramo main: scip-dotnet scrive occorrenze solo per i nomi semplici.
- **Progetto e caso:** eShop — misura su Modal al suo commit, con scip-dotnet 0.2.16, 16 novembre 2026.
- **Rimedio:**
  - `73b645531` (16 novembre), `scripts/indexers/csharp.py`: il buco porta la causa `TYPE_ARGUMENTS`;
  - `0cdbae9b2` (16 novembre), `scripts/languages/semantic.py` (`_generic_name`): una chiamata come `AddSingleton<A, B>()` è nominata dal suo nome;
  - `9290d446a` (16 novembre), `scripts/indexers/csharp.py` e `scripts/indexers/scip-dotnet.patch`: Daodan costruisce scip-dotnet dal sorgente della 0.2.16 (commit `fadd98aebb1e` di scip-dotnet, fissato per sha256) con una patch che cambia un solo file, `ScipCSharpSyntaxWalker.cs`, e nomina i nomi generici; la patch porta l'avviso di modifica che l'Apache-2.0 chiede (§4); la preparazione costruisce lo strumento con l'SDK 10.0.404 di Daodan, accanto a quello del progetto, e l'indice dice `0.2.16+daodan.<sha256 della patch>`.
- **Verifica:**
  - dal commit `9290d446a`, su eShop: risposte C# dall'84,67 % al 92,06 %; no-occurrence da 1.963 a 966; nomi con argomenti di tipo senza occorrenza da 966 a 55;
  - `tests/test_codebase_map_indexers_csharp.py` (`test_a_call_written_with_type_arguments_reaches_the_method_its_name_binds_to`).
- **Stato:** risolto.
- **Note:** il testo della segnalazione per scip-dotnet è in `docs/research/2026-11-16-scip-dotnet-names.md`, e inviarla è una scelta del proprietario: Daodan non invia niente. Dallo stesso commit `73b645531` vengono D-118–D-120; i nomi qualificati, D-117; i gruppi di metodi, D-249.

#### D-117 C#: nomi del chiamato qualificati
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine prova su Modal · strumento tree-sitter
- **Descrizione:** csharp-dotnet ha misurato, fra le cause del 56,1 % (D-114), i nomi del chiamato qualificati, come `new Shop.Core.Models.User()`.
- **Spiegazione:** il lettore dei nomi del chiamato (`_TreeSitterEvidence.parts`, `scripts/languages/semantic.py`) non trattava il `qualified_name` di C#, il tipo scritto con il suo namespace.
- **Progetto e caso:** i casi C# — misura di csharp-dotnet, 16 novembre 2026.
- **Rimedio:** `0cdbae9b2` (16 novembre), `scripts/languages/semantic.py`: un `qualified_name` di C# è nominato attraverso il suo namespace, e si risolve.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_csharp.py`, `test_a_type_written_with_its_namespace_is_named_by_it`).
- **Stato:** risolto.
- **Note:** D-114, D-116.

#### D-118 C#: i membri dei tipi anonimi erano locali senza definizione
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-dotnet
- **Descrizione:** eShop: 138 buchi dangling-local.
- **Spiegazione:** scip-dotnet chiama locali i membri dei tipi anonimi e non li definisce.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`:
  - 135 membri di tipi anonimi sono definiti dove `new { X = }` li nomina;
  - i membri dei blocchi di estensione di C# 14 hanno la classe EXTENSION.
- **Verifica:** dangling-local da 138 a 1.
- **Stato:** risolto; i membri dei blocchi di estensione sono un buco dichiarato (EXTENSION).
- **Note:** —

#### D-119 C#: membri dei source generator e `args` dei top-level statement senza causa
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-dotnet
- **Descrizione:** eShop: 17 buchi undefined-project-symbol.
- **Spiegazione:** scip-dotnet indicizza solo i documenti del progetto, quindi non i membri generati, e `args` dei top-level statement lo dichiara il compilatore.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`: le classi GENERATED e TOP_LEVEL.
- **Verifica:** undefined-project-symbol da 17 a 0.
- **Stato:** buco dichiarato (GENERATED, TOP_LEVEL).
- **Note:** —

#### D-120 C#: Catalog.API non si caricava sotto la globalizzazione invariante
- **Tag:** lingua csharp · area analizzatore · tipo correttezza · origine prova su Modal · strumento MSBuild
- **Descrizione:** eShop: NETSDK1188 su Catalog.API.
- **Spiegazione:** la globalizzazione invariante rifiuta ogni cultura salvo quella invariante, e le risorse per cultura di un pacchetto fanno fallire MSBuild.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`: l'ambiente ha `DOTNET_SYSTEM_GLOBALIZATION_PREDEFINED_CULTURES_ONLY=false`.
- **Verifica:** la misura su eShop del commit.
- **Stato:** risolto.
- **Note:** —

#### D-121 Lo script di C e C++ cancellava la cartella in cui scrive il risultato
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** l'indice C/C++ finiva `failed` senza una run.
- **Spiegazione:** la cartella del risultato sta dentro quella di lavoro, e lo script la creava prima di svuotare quella di lavoro, così il risultato non veniva mai scritto.
- **Progetto e caso:** indicizzatore C/C++ — 15 novembre 2026.
- **Rimedio:** `c089b3540` (15 novembre), `scripts/indexers/clang_run.py`: la crea dopo.
- **Verifica:** la prova reale nel container passa con `a3dad5e39` (D-122).
- **Stato:** risolto.
- **Note:** —

#### D-122 CMake: il fornitore delle dipendenze nominato prima di essere definito
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento CMake
- **Descrizione:** la configurazione moriva a `project()` e non registrava nulla.
- **Spiegazione:** CMake accetta come fornitore delle dipendenze solo un comando già definito, e lo script lo nominava prima.
- **Progetto e caso:** prova reale di C e C++ nel container — 15 novembre 2026.
- **Rimedio:** `a3dad5e39` (15 novembre), `scripts/indexers/clang_run.py`: l'ordine è giusto.
- **Verifica:** la prova nel container dà l'unità `unavailable` con fmt e il suo URL, come deve.
- **Stato:** risolto.
- **Note:** D-132.

#### D-123 scip-clang usava i processori della macchina
- **Tag:** lingua c, cpp · area analizzatore · tipo prestazioni · origine commit · strumento scip-clang
- **Descrizione:** scip-clang lanciava tanti compilatori quanti processori ha la macchina.
- **Spiegazione:** `--jobs` veniva dalla macchina, non dalla parte che il chiamante dà al container.
- **Progetto e caso:** indicizzatore C/C++ — 15 novembre 2026.
- **Rimedio:** `d28dc1442` (15 novembre), `scripts/indexers/clang.py` e `clang_run.py` (`clang_run.py UNITS_JSON OUT_DIR JOBS`, `--jobs={jobs}`).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-124 L'errore di CMake riscritto con righe ricavate dal testo
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento CMake
- **Descrizione:** l'errore di CMake arrivava con righe ricostruite, non com'è scritto.
- **Spiegazione:** lo script estraeva righe dal testo dell'errore.
- **Progetto e caso:** indicizzatore C/C++ — 14 novembre 2026.
- **Rimedio:** `377925c52` (14 novembre), `scripts/indexers/clang.py` e `clang_run.py`: l'errore resta com'è scritto.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-125 vcpkg e Conan: il configure senza l'installazione del gestore
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine commit · strumento vcpkg, Conan, CMake
- **Descrizione:** in sys-cpp-vcpkg-conan il configure falliva; con `ee456d55a` (15 novembre) quel caso restava «invariato, perché il suo configure fallisce».
- **Spiegazione:** il configure dell'analizzatore non eseguiva l'installazione del gestore né leggeva la cache iniziale che questa scrive.
- **Progetto e caso:** sys-cpp-vcpkg-conan — 15 e 16 novembre 2026.
- **Rimedio:** `f9fde7c1e` (16 novembre), `scripts/indexers/clang.py` e `clang_run.py`:
  - riusa la scelta della pre-mappa: il gestore che il toolchain file del preset nomina, altrimenti vcpkg;
  - riusa la sua riga di installazione e `init.cmake`;
  - la preparazione ha il CMake fissato, i registri e gli host del gestore;
  - un'installazione fallita è `restore_failed`.
- **Verifica:** finale e conferma: sys-cpp-vcpkg-conan, cpp `fresh`.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-126–D-129; per l'osservatore, D-177.

#### D-126 Un configure che legge un submodule non scaricato
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine finale · strumento git
- **Descrizione:** finale e conferma: «.: the configure reads third_party/fmt: a git submodule not checked out (git submodule update --init)».
- **Spiegazione:** il submodule non è nel checkout.
- **Progetto e caso:** sys-git-submodule-absent — finale e conferma, 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: è `unavailable` e lo nomina.
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** —

#### D-127 `namespace a::b {` non letto come C++17
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** il lettore non riconosceva il namespace annidato di C++17.
- **Spiegazione:** la lettura non lo trattava come C++17.
- **Progetto e caso:** lettura C/C++ — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`, `scripts/languages/__init__.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-128 Un `.h` con una direttiva Objective-C letto come C
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** un header Objective-C entrava nel grafo come C.
- **Spiegazione:** l'estensione `.h` decideva da sola il linguaggio.
- **Progetto e caso:** lettura C/C++ — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: il file torna al suo linguaggio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-129 Un `.ts` di Qt Linguist letto come TypeScript
- **Tag:** lingua typescript · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** un file XML di traduzione di Qt entrava nel grafo come TypeScript.
- **Spiegazione:** l'estensione `.ts` decideva da sola il linguaggio.
- **Progetto e caso:** lettura — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: il file torna al suo linguaggio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-130 C: macro di decorazione e nomi da header non risolti
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** su zlib 37 file C su 66 non avevano fatti semantici, e le chiamate risolte erano 303.
- **Spiegazione:**
  - il lettore non toglieva le macro che il sorgente definisce come decorazione o come involucro di un prototipo, anche quando arrivano da un file incluso;
  - un nome che arriva da un header non portava alla sua unica definizione con collegamento esterno, anche dentro un namespace C++.
- **Progetto e caso:** zlib — 14 novembre 2026.
- **Rimedio:** `8054a410c` (14 novembre), `scripts/languages/cfamily.py`, `scripts/resolution.py`, `scripts/semantic_index.py`, `scripts/semantic_store.py` e `scripts/snapshot.py`.
- **Verifica:** zlib: file senza fatti semantici da 37 a 12 su 66, chiamate risolte da 303 a 510; per gli altri linguaggi lo snapshot è identico.
- **Stato:** risolto.
- **Note:** —

#### D-131 Un configure che ha bisogno di ciò che l'unità scarica fuori dai registri
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine commit · strumento scip-clang, CMake
- **Descrizione:** l'indice C/C++ di un'unità non si fa senza i download che la sua configurazione chiede.
- **Spiegazione:** la configurazione gira senza rete, con CMake e scip-clang portati da Daodan e fissati per sha256.
- **Progetto e caso:** indicizzatore C/C++ — 14 novembre 2026.
- **Rimedio:** `98743babd` (14 novembre):
  - l'indice di quell'unità è `unavailable`, con gli indirizzi e la riga d'errore di CMake;
  - l'unità tiene i fatti statici.
- **Verifica:** provato su un container finto; la prova vera in D-122.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** D-132.

#### D-132 `file(DOWNLOAD)` ed ExternalProject non annotati
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine finale · strumento scip-clang, CMake
- **Descrizione:** finale, otel-demo: «scip-clang wrote no index (src/currency: the configure ended with exit code 1; FetchContent asked for nothing; file(DOWNLOAD) and ExternalProject are not recorded)».
- **Spiegazione:**
  - un fornitore di dipendenze passato a CMake annota nome e indirizzi di ciò che il progetto chiede a FetchContent, senza scaricare;
  - file(DOWNLOAD) ed ExternalProject non passano di lì.
- **Progetto e caso:** otel-demo src/currency — finale, 16 novembre 2026.
- **Rimedio:** `6c2aa069e` (14 novembre):
  - una configurazione fallita con un'annotazione è `unavailable` con quella causa;
  - senza annotazione è `failed`, e lo dice.
- **Verifica:** finale.
- **Stato:** buco dichiarato (`failed` con la frase citata).
- **Note:** D-135.

#### D-133 zlib: file C e C++ che nessun build compila
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine finale · strumento Make, Bear
- **Descrizione:** conferma, zlib:
  - C con 22 file su 54 fuori dall'indice: 12 «not built by the default configuration», 8 header che nessuna unità indicizzata include in un ramo attivo, 2 con «make ended with exit code 2»;
  - C++ `failed`: nessuno degli 8 file nell'indice.
- **Spiegazione:**
  - i contrib con un Makefile sono già indicizzati sotto Bear;
  - i file mancanti non li compila nessun build: examples/, contrib/infback9, il solo target cover e il build autotools di minizip;
  - team-lead nomina anche iowin32.c, che nessun commit nomina: da verificare.
- **Progetto e caso:** zlib — finale e conferma, 16 novembre 2026.
- **Rimedio:** `d4e6d9046` (16 novembre), `scripts/indexers/clang.py`: il motivo nomina la cartella invece di «not built by the default configuration».
- **Verifica:** dopo `d4e6d9046` nessun giro: da verificare.
- **Stato:** buco dichiarato (`no compile command`).
- **Note:** D-134; il build autotools di minizip ora c'è.

#### D-134 zlib minizip: il build autotools non eseguito
- **Tag:** lingua c · area analizzatore · tipo completezza · origine commit · strumento autotools
- **Descrizione:** mztools.c di contrib/minizip non era indicizzato.
- **Spiegazione:** Daodan non eseguiva i build autotools.
- **Progetto e caso:** zlib contrib/minizip — 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre), `scripts/indexers/clang.py` e `clang_run.py`:
  - il configure.ac più esterno è un'unità autotools-project, con i sorgenti dei Makefile.am;
  - clang lancia autoreconf, configure in una cartella sua e make sotto Bear.
- **Verifica:** provato su contrib/minizip di zlib: mztools.c è indicizzato.
- **Stato:** risolto.
- **Note:** D-133.

#### D-135 otel-demo currency: il build dichiarato solo nel Dockerfile
- **Tag:** lingua cpp · area analizzatore · tipo completezza · origine finale · strumento Docker, BuildKit, CMake
- **Descrizione:** finale e giro `jvm-otel-android`: il configure di src/currency esce con 1 (D-132), con «CMake Error at CMakeLists.txt:7 (find_package): Could not find a package configuration file provided by "Protobuf"».
- **Spiegazione:** Protobuf e le altre dipendenze del servizio le installa il suo Dockerfile, che è l'unico a dichiarare come si costruisce; il configure sul checkout non le trova.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — finale e giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** in corso (android-sdk). Da `f024ba3a3` (16 novembre) la lettura e il piano ci sono, ma nessun analizzatore C/C++ li usa:
  - la pre-mappa legge ogni Dockerfile con il parser di BuildKit v0.34.2 (fatto `docker_builds`), con il contesto e gli argomenti di build da Compose (`scripts/premap/dockerfile.py`);
  - `scripts/docker_build.py` pianifica lo stadio fino al suo ultimo RUN, con l'immagine di base fissata per digest, e ogni istruzione non riproducibile è un buco `not_reproduced` con la sua riga;
  - la via per C e C++ non è in un commit (`scripts/indexers/clang.py`, non committato): scip-clang gira sull'Alpine dello stadio attraverso il loader di glibc in una prova; mancano le sorgenti dei pacchetti dell'immagine di base e `.dockerignore`.
- **Verifica:** del piano solo test (`tests/test_codebase_map_docker_build.py`, `test_currency_runs_base_then_builder_with_compose_s_argument_and_maps_each_copy_back`); dell'indice, —.
- **Stato:** aperto (android-sdk).
- **Note:** D-107, D-141.

#### D-136 C: 5.147 buchi `no-document`
- **Tag:** lingua c · area analizzatore · tipo completezza · origine conferma · strumento —
- **Descrizione:** conferma, C su 7 casi: 10.271 siti, 40,7 % di risposta; fra i buchi, no-document 5.147 e no-occurrence 941.
- **Spiegazione:** da verificare.
- **Progetto e caso:** i casi C della conferma — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-133.

#### D-137 File C e C++ fuori dalla configurazione predefinita
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine finale · strumento —
- **Descrizione:** sys-cmake-presets ha 1 file C su 4 e tinyxml2 1 file C++ su 3 «no compile command: not built by the default configuration».
- **Spiegazione:** la configurazione predefinita del build non li compila.
- **Progetto e caso:** sys-cmake-presets, tinyxml2 (`9148bdf719e9`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** il motivo per file (`2bc7c7459`).
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato (`no compile command: not built by the default configuration`).
- **Note:** —

#### D-138 Go: i builtin erano buchi
- **Tag:** lingua go · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** le chiamate ai builtin di Go non avevano risposta.
- **Spiegazione:** non erano esterni di nessun pacchetto.
- **Progetto e caso:** indicizzatore Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: sono esterni del pacchetto builtin.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-139 Go: file esclusi dai vincoli di build senza indice
- **Tag:** lingua go · area analizzatore · tipo completezza · origine commit · strumento scip-go
- **Descrizione:** i file esclusi da un vincolo di build mancavano dall'indice.
- **Spiegazione:** scip-go indicizza la sola configurazione corrente.
- **Progetto e caso:** indicizzatore Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: quei file hanno un passaggio di scip-go sotto una configurazione che li compila.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-079.

#### D-140 Go: un file senza go.mod non diceva perché
- **Tag:** lingua go · area analizzatore · tipo completezza · origine finale · strumento scip-go, Docker
- **Descrizione:** finale, robot-shop: «go failed: none of the 1 go files is in the index: no document in the index (1)».
- **Spiegazione:** il file non ha un go.mod nella sua cartella né sopra; il go.mod lo scrive il Dockerfile al build.
- **Progetto e caso:** robot-shop (`55292e2199f2`) — finale, 16 novembre 2026.
- **Rimedio:** `d4e6d9046`, `scripts/indexers/go.py`: il motivo dice «no Go module holds it».
- **Verifica:** dopo `d4e6d9046` nessun giro: da verificare.
- **Stato:** risolto; il build resta D-141.
- **Note:** D-141.

#### D-141 robot-shop dispatch: il modulo Go dichiarato solo nel Dockerfile
- **Tag:** lingua go · area analizzatore · tipo completezza · origine finale · strumento scip-go, Docker
- **Descrizione:** finale: «go failed: none of the 1 go files is in the index: no document in the index (1)»; il servizio dispatch non entra nel grafo Go.
- **Spiegazione:**
  - il go.mod lo scrive il Dockerfile al build: `WORKDIR /go/src/app`, `COPY *.go .`, `RUN go mod init dispatch && go get`, `RUN go install`;
  - quel Dockerfile oggi non costruisce più: `go get` senza versione prende un go-sensor che chiede Go 1.21 (dal commit).
- **Progetto e caso:** robot-shop (`55292e2199f2`) — finale, 16 novembre 2026.
- **Rimedio:** `f024ba3a3` e `f04dab9d5` (16 novembre, android-sdk), `scripts/indexers/go.py` e `scripts/docker_build.py`:
  - `f024ba3a3` legge il Dockerfile e ne pianifica lo stadio;
  - `f04dab9d5` indicizza: un file Go che nessun modulo contiene, ma che uno stadio del Dockerfile copia, ha una corsa di scip-go dentro quello stadio, che registra Dockerfile, stadio, comandi eseguiti, go.mod e go.sum risolti; gli ARG dello stadio arrivano dove gira il build;
  - il passo che fallisce è il buco `restore_failed`, con `dispatch/Dockerfile:7` e la riga d'errore dello strumento, non il progresso di go.
- **Verifica:**
  - `tests/test_codebase_map_docker_build.py` (`test_dispatch_runs_its_stage_up_to_the_go_install_that_builds_it`, `test_go_files_no_module_holds_are_indexed_in_the_stage_their_dockerfile_builds`);
  - dal commit `f04dab9d5`: su uno stadio della stessa forma che costruisce, da 0 a 1 file indicizzato, completo, con le versioni che `go get` ha risolto;
  - su robot-shop il commit riporta l'errore vero del Dockerfile di oggi.
- **Stato:** buco dichiarato (`restore_failed` a `dispatch/Dockerfile:7`): è il Dockerfile del progetto a non costruire.
- **Note:** D-107, D-135, D-140.

#### D-142 Un file cgo fuori dall'indice Go
- **Tag:** lingua c, go · area analizzatore · tipo completezza · origine finale · strumento scip-go
- **Descrizione:** finale e conferma, sys-go-cgo 1 file su 3: «a cgo file (`import "C"`): scip-go indexes the copy cgo writes into the build cache, not the file».
- **Spiegazione:** scip-go indicizza la copia che cgo scrive nella cache del build, non il file.
- **Progetto e caso:** sys-go-cgo — finale e conferma, 16 novembre 2026.
- **Rimedio:** il motivo per file.
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato («a cgo file»).
- **Note:** il C di cgo entra nel grafo con `f829df4b0` (Bear attorno a `go build`).

#### D-143 Rust: file senza documento
- **Tag:** lingua rust · area analizzatore · tipo completezza · origine finale · strumento rust-analyzer
- **Descrizione:** «no document in the index» per 6 file Rust su 105 in hoppscotch (finale) e 1 su 19 in semver (finale e conferma).
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** —. Da `a3801beed` un file dietro un `mod` con cfg falso dice perché manca (D-237); quanti dei 7 lo siano è da verificare.
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-144, D-237.

#### D-144 Rust: file che nessun crate carica
- **Tag:** lingua rust · area analizzatore · tipo completezza · origine finale · strumento rust-analyzer
- **Descrizione:** finale, hoppscotch: 2 file «no crate includes it: no `mod` item of an indexed file loads it».
- **Spiegazione:** nessun `mod` di un file indicizzato li carica.
- **Progetto e caso:** hoppscotch — finale, 16 novembre 2026.
- **Rimedio:** il motivo per file.
- **Verifica:** finale.
- **Stato:** buco dichiarato («no crate includes it»).
- **Note:** —

#### D-145 TypeScript: `{ t } = useTranslation()` legato a un simbolo che l'indice non definisce
- **Tag:** lingua typescript · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** in tududi i nomi presi per destrutturazione finivano su un simbolo senza definizione.
- **Spiegazione:** il join legava il nome a un simbolo che l'indice non definisce.
- **Progetto e caso:** tududi (`71da9d7b34df`) — 16 novembre 2026.
- **Rimedio:** `3595d571b` (16 novembre), `scripts/indexers/typescript.py` e `scripts/code_graph.py`: il nome finisce alla sua definizione.
- **Verifica:** tududi, insieme a D-147.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-146, D-147 e D-161.

#### D-146 TypeScript: pacchetti senza nome (heroicons)
- **Tag:** lingua typescript · area analizzatore · tipo correttezza · origine commit · strumento scip-typescript
- **Descrizione:** i riferimenti ai pacchetti senza nome, come heroicons, non avevano un esterno valido.
- **Spiegazione:** un difetto di scip-typescript, corretto nella 0.6.2.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `3595d571b`: scip-typescript passa alla 0.6.2.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-147 TypeScript e JavaScript: buchi senza causa
- **Tag:** lingua javascript, typescript · area analizzatore · tipo completezza · origine commit · strumento scip-typescript
- **Descrizione:** in tududi 8.010 buchi TypeScript erano senza spiegazione.
- **Spiegazione:** l'indice non dice perché un riferimento non ha occorrenza.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `3595d571b`, `scripts/indexers/typescript_unbound.js`:
  - dopo l'indice gira il checker di TypeScript;
  - l'aggancio `unanswered` dà a ogni buco la causa: ricevente any, firma a indice, membro creato dal checker, non dichiarato.
- **Verifica:** tududi: «da 8.010 buchi TypeScript senza spiegazione a 3.193 con la causa» (dal commit).
- **Stato:** risolto.
- **Note:** D-158.

#### D-148 `module` di `module.exports` come locale senza definizione
- **Tag:** lingua javascript · area analizzatore · tipo completezza · origine commit · strumento scip-typescript
- **Descrizione:** in un file CommonJS `module` restava un buco.
- **Spiegazione:** l'indice scrive `module` come una locale senza definizione, perché TypeScript legge `module.exports =` come l'export del file.
- **Progetto e caso:** js-yarn-berry, js-npm-single — 16 novembre 2026.
- **Rimedio:** `eacfad80e` (16 novembre), `scripts/indexers/typescript.py`:
  - se l'indice usa i tipi di Node, l'estremo è esterno (@types/node dichiara `module` accanto a `require`);
  - altrimenti resta un buco con la causa.
- **Verifica:** prova vera su Modal: js-yarn-berry e js-npm-single completi, 0 buchi. Finale: «module.exports: the index names `module` with a local it defines nowhere, and references no Node types that declare it» 2.
- **Stato:** risolto; il buco resta dove il progetto non usa i tipi di Node.
- **Note:** —

#### D-149 Una chiamata senza nome del chiamato era sempre un buco `no-position`
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** lo snapshot registra una chiamata senza nome del chiamato con una lista vuota, e il grafo ne faceva sempre un buco no-position.
- **Spiegazione:** il grafo non leggeva l'espressione chiamata.
- **Progetto e caso:** chi (`c64ed7d6635f`) e il corpus — 16 novembre 2026.
- **Rimedio:** `334ea4d96` (16 novembre), `scripts/code_graph.py` e `scripts/languages/semantic.py`; `Snapshot.computed` legge l'espressione:
  - una funzione dichiarata lì (`func(){..}()` di Go, defer e go, IIFE e frecce di JavaScript e TypeScript) è un arco certo al suo letterale;
  - `super(...)` prende l'occorrenza dell'indice;
  - il resto è un buco con la sua classe, che il passo dinamico chiude per posizione: call-result, element, dynamic-import, super-call, computed-callee.
- **Verifica:** chi: 36 di 43 con risposta (dal commit); nessun giro dopo il commit.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-150 e D-151; il lavoro era di dynamic-step-2.

#### D-150 TypeScript: `x.f!()` non nominava `x.f`
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** lo snapshot non dava il nome del chiamato per una chiamata con l'asserzione non-null.
- **Spiegazione:** il lettore non toglieva `!` dal chiamato.
- **Progetto e caso:** lettura TypeScript — 16 novembre 2026.
- **Rimedio:** `334ea4d96`, `scripts/languages/semantic.py`: `x.f!()` nomina `x.f`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-151 TypeScript: `await f<T>(x)` non nominava `f`
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** lo snapshot non dava il nome del chiamato per una chiamata generica sotto await.
- **Spiegazione:** il lettore non toglieva gli argomenti di tipo sotto await.
- **Progetto e caso:** lettura TypeScript — 16 novembre 2026.
- **Rimedio:** `334ea4d96`: `await f<T>(x)` nomina `f`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-152 TypeScript 6: i tipi di Node non caricati
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine commit · strumento scip-typescript
- **Descrizione:** con TypeScript 6 l'indice non aveva i tipi di Node.
- **Spiegazione:** non caricati con quella versione (dal commit).
- **Progetto e caso:** TypeScript nel container — 16 novembre 2026.
- **Rimedio:** `12775fee3` (16 novembre): i tipi di Node si caricano anche con TypeScript 6.
- **Verifica:** prova vera su Modal: TypeScript del workspace pnpm completo.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-153–D-156, D-167–D-171 e D-225.

#### D-153 Svelte con nulla di letto non era `failed`
- **Tag:** lingua svelte · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** `d94f92470` lasciava aperto lo stato di Svelte con 0 file letti.
- **Spiegazione:** lo stato non guardava i file letti.
- **Progetto e caso:** js-sveltekit — 16 novembre 2026.
- **Rimedio:** `12775fee3`: Svelte senza nulla di letto è `failed`, con la causa.
- **Verifica:** finale, js-sveltekit: «nothing of the 2 svelte files is read: template not read: calls and bindings in it are not sites (2); none of their 2 calls is asked: builtin (2)».
- **Stato:** risolto.
- **Note:** D-159.

#### D-154 Vue diverso fra analisi e unione
- **Tag:** lingua vue · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** `d94f92470` lasciava aperto Vue «tra analisi e unione».
- **Spiegazione:** lo stato di Vue nell'analisi e nell'unione non coincideva.
- **Progetto e caso:** js-vue-pnpm — 16 novembre 2026.
- **Rimedio:** `12775fee3`: Vue è uguale fra analisi e unione.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-155 L'import di un `.vue` non tipizzato senza causa
- **Tag:** lingua vue · area analizzatore · tipo completezza · origine commit · strumento —
- **Descrizione:** un import di un componente `.vue` non tipizzato era un buco senza causa.
- **Spiegazione:** il motivo non c'era.
- **Progetto e caso:** progetti Vue — 16 novembre 2026.
- **Rimedio:** `12775fee3`: l'import ha la sua causa.
- **Verifica:** finale: «no declaration of *.js?v=explicit-esm-dependencies modules: the import is not typed» 1.
- **Stato:** risolto.
- **Note:** —

#### D-156 SvelteKit: «error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'»
- **Tag:** lingua javascript, typescript, svelte · area analizzatore · tipo completezza · origine finale · strumento scip-typescript, SvelteKit
- **Descrizione:** finale, js-sveltekit: TypeScript e JavaScript `failed`, «scip-typescript wrote no index (exit code 1): error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'. error: no files got indexed.».
- **Spiegazione:** il tsconfig lo genera SvelteKit, e nessuna installazione lo crea.
- **Progetto e caso:** js-sveltekit — finale, 16 novembre 2026.
- **Rimedio:** `12775fee3`: un buco che nomina il tsconfig generato; `b9aeca1fb` (16 novembre, csharp-2): `svelte-kit sync` gira nella preparazione, nel container, con il kit del progetto, e scrive il tsconfig.
- **Verifica:** finale per il buco; per `b9aeca1fb` solo test (`tests/test_codebase_map_components.py`, `test_sveltekit_writes_its_tsconfig_in_the_preparation_with_the_projects_kit`), nessun giro dopo il commit.
- **Stato:** risolto.
- **Note:** `d94f92470` lo lasciava aperto come «causa del tsconfig generato».

#### D-157 TypeScript: i tipi sotto Yarn
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine commit · strumento Yarn
- **Descrizione:** `d94f92470` lascia aperti «tipi sotto Yarn».
- **Spiegazione:** da verificare; nessun commit successivo lo nomina.
- **Progetto e caso:** TypeScript nel container — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (da verificare).
- **Note:** —

#### D-158 JavaScript: riceventi non tipizzati
- **Tag:** lingua javascript · area analizzatore · tipo completezza · origine conferma · strumento —
- **Descrizione:** buchi «a member of a value of type any: only execution knows it», per esempio 10 in kotlinconf `app/webApp/src/webMain/resources/service-worker.js`; conferma, JavaScript: no-occurrence 39.563.
- **Spiegazione:** senza tipo del ricevente l'indice non sa quale membro si chiama; solo l'esecuzione lo sa.
- **Progetto e caso:** kotlinconf e il corpus JavaScript — conferma e corsa su Modal di kotlinconf, 16 novembre 2026.
- **Rimedio:** `3595d571b` (la causa). Il passo dinamico chiude quei buchi dove i test girano.
- **Verifica:** conferma: JavaScript con 691 risposte osservate.
- **Stato:** buco dichiarato («a member of a value of type any»).
- **Note:** D-147.

#### D-159 Template di Vue e Svelte non letti
- **Tag:** lingua vue, svelte · area analizzatore · tipo completezza · origine finale · strumento —
- **Descrizione:** finale:
  - Vue 0 file su 410 nell'indice, 28,2 % di risposta; Svelte 0 su 4, 26,7 %;
  - hoppscotch Vue 407 su 407 (400 «template not read: calls and bindings in it are not sites», 7 «no script block»), Svelte 2 su 2;
  - js-vue-pnpm 3 su 3.
- **Spiegazione:** le chiamate e i binding nei template non sono siti.
- **Progetto e caso:** hoppscotch, js-vue-pnpm, js-sveltekit — finale, 16 novembre 2026.
- **Rimedio:** dichiarati letti in parte (`64edfb930`, D-080); poi `b9aeca1fb` (16 novembre, csharp-2): `scripts/languages/sfc.py` legge i template (gestori, interpolazioni, direttive), e `scripts/indexers/components.py` genera il TypeScript dei componenti con lo strumento del progetto (`@vue/language-core` del suo vue-tsc, svelte2tsx), che scip-typescript indicizza nel container.
- **Verifica:** solo test: `tests/test_codebase_map_sfc_templates.py` (`test_a_vue_templates_calls_reads_and_handlers_are_references_bound_by_the_script_and_the_template`, `test_a_svelte_templates_expressions_blocks_and_snippets_are_references_bound_by_the_script_and_the_template`); nessun giro dopo il commit.
- **Stato:** risolto.
- **Note:** D-080, D-153.

#### D-160 TypeScript: un file senza documento
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine finale · strumento scip-typescript
- **Descrizione:** finale: hoppscotch 1 file TypeScript su 1.115, memos 1 su 620, «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch, memos (`509e41bd1a1b`) — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-161 Tailwind caricato sull'host con la configurazione del progetto
- **Tag:** lingua css · area analizzatore · tipo sicurezza · origine commit · strumento Tailwind
- **Descrizione:** l'adattatore Tailwind eseguiva codice del progetto fuori dal container.
- **Spiegazione:** `css_tailwind.js` caricava sull'host il tailwindcss del progetto, la sua configurazione e i suoi plugin.
- **Progetto e caso:** analyzer dei fogli di stile — 16 novembre 2026.
- **Rimedio:** `3595d571b`, `scripts/indexers/css_tailwind.py`:
  - Tailwind gira con `run_in_container`: preparazione con i registri e il ripristino dei pacchetti, esecuzione senza rete;
  - senza container o con un ripristino fallito i token restano sconosciuti con la causa, e nulla gira sull'host;
  - gli altri motori CSS leggono il progetto come testo e restano dove sono.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-162. Lo stesso difetto, codice del progetto sull'host, in D-239 (rust-analyzer) e D-245 (Git); la regola invalicabile di `AGENTS.md` lo vieta da `2753088a3`.

#### D-162 Fogli di stile: buchi `no-rule`
- **Tag:** lingua css · area analizzatore · tipo completezza · origine finale · strumento Tailwind
- **Descrizione:** conferma: 42.757 buchi no-rule su 58.534 siti dei fogli di stile, 26,3 % di risposta; nel finale 48.808.
- **Spiegazione:** un riferimento di classe, id o composes senza una regola che lo definisca è `no-rule` (`scripts/indexers/css.py`); fra questi le classi Tailwind (`ee1e83fc8`). Da verificare quanti sono classi che nessun foglio definisce e quanti un difetto.
- **Progetto e caso:** il corpus — finale e conferma, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (ts-container-2).
- **Note:** D-161.

#### D-163 hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto
- **Tag:** lingua css · area analizzatore · tipo correttezza · origine giro-2 · strumento —
- **Descrizione:** giro-2 e finale: «the stylesheet stage exited with code 1 without a report; see engine-pass.log».
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch — giro-2 e finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (ts-container-2).
- **Note:** —

#### D-164 Fogli remoti senza testo
- **Tag:** lingua css · area analizzatore · tipo completezza · origine finale · strumento —
- **Descrizione:** finale: 10 buchi `remote-sheet`.
- **Spiegazione:** il lettore non scarica nulla; un foglio remoto senza testo lascia buchi con il suo indirizzo.
- **Progetto e caso:** il corpus — finale, 16 novembre 2026.
- **Rimedio:** `9c719fc1a` (14 novembre).
- **Verifica:** finale.
- **Stato:** buco dichiarato (`remote-sheet`).
- **Note:** —

#### D-165 Parser: `base` di C# non letto
- **Tag:** lingua csharp · area parser · tipo completezza · origine commit · strumento —
- **Descrizione:** il commit elenca `base` in C# fra le correzioni del parser.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470` (16 novembre).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** con `56e65e114` una chiamata attraverso `base` non prende override.

#### D-166 Parser: `this` e `super` di Kotlin non letti
- **Tag:** lingua kotlin · area parser · tipo completezza · origine commit · strumento —
- **Descrizione:** il commit elenca `this` e `super` in Kotlin fra le correzioni del parser.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-236 C++: il simbolo di un argomento di macro stava sul nome della macro
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-clang
- **Descrizione:** tinyxml2, 255 buchi no-occurrence (misura del commit `a3801beed`, su Modal al commit fissato).
- **Spiegazione:** scip-clang scrive un riferimento nel punto di espansione, così il simbolo di un argomento di macro stava sul nome della macro.
- **Progetto e caso:** tinyxml2 (`9148bdf719e9`) — misura su Modal del commit, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/indexers/clang.py` (`macro_arguments`): riporta il simbolo al nome dell'argomento, tiene quello del corpo della macro e salta i nomi ambigui.
- **Verifica:** dal commit, no-occurrence da 255 a 43; `tests/test_codebase_map_code_graph.py` (`test_clang_a_macros_arguments_take_the_symbols_the_index_writes_at_the_macro`).
- **Stato:** risolto; i 43 restanti dicono il ramo `#if` che il build non compila, o sono chiamate alla libreria C che l'indice C++ non nomina.
- **Note:** —

#### D-237 Rust: i riferimenti e i file che un `#[cfg]` esclude non dicevano perché
- **Tag:** lingua rust · area analizzatore · tipo completezza · origine prova su Modal · strumento rust-analyzer
- **Descrizione:** hoppscotch, 549 buchi no-occurrence e 8 no-position (misura del commit `a3801beed`, su Modal al commit fissato).
- **Spiegazione:** i cfg li decide la configurazione che rust-analyzer legge: ogni feature accesa, il target dell'host, niente build script né macro procedurali. Un riferimento sotto un `#[cfg(X)]` falso in quella configurazione non ha occorrenza, e un file dietro un `mod` con cfg falso non ha documento.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`) — misura su Modal del commit, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/indexers/rust.py`: il buco dice il cfg falso, e il file dice perché manca.
- **Verifica:** dal commit, «no-occurrence da 549 a 135, di cui 425 ora con la causa cfg; no-position da 8 a 0»; `tests/test_codebase_map_indexers_reasons.py` (`test_rust_code_a_cfg_leaves_out_says_so`).
- **Stato:** buco dichiarato (la causa cfg).
- **Note:** D-143.

#### D-238 Rust: il turbofish su un ricevitore calcolato toglieva il nome al chiamato
- **Tag:** lingua rust · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** semver: `black_box(t).parse::<V>()` non era nominato.
- **Spiegazione:** il lettore dei nomi del chiamato (`scripts/languages/semantic.py`) cercava il membro sul nodo `generic_function`, il turbofish, invece che sulla funzione che esso contiene.
- **Progetto e caso:** semver (`280ebcb6edac`) — commit `a3801beed`, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/languages/semantic.py`: il turbofish non fa parte del nome del membro.
- **Verifica:** solo test (`tests/test_xray_semantic_syntax.py`, `test_a_rust_method_with_type_arguments_keeps_its_name`).
- **Stato:** risolto.
- **Note:** —

#### D-239 rust-analyzer esegue sull'host build script e macro procedurali del progetto
- **Tag:** lingua rust · area analizzatore · tipo sicurezza · origine prova su Modal · strumento rust-analyzer, Cargo, rustup
- **Descrizione:** dynamic-step-2 ha misurato su Modal, con un build.rs che scrive un file, che `rust-analyzer scip` esegue sull'host i build script e le macro procedurali del progetto, nonostante `CONFIG` li spenga (dal commit `293e3bfac`).
- **Spiegazione:**
  - al commit `a3801beed` l'analizzatore Rust lancia `rust-analyzer scip` sull'host, in una copia del progetto (`scripts/indexers/rust.py`, `index`, con `runtime.mirrored`), con `--config-path` e `CONFIG` (`rust.py:30`): `{"cargo": {"buildScripts": {"enable": False}, "features": "all"}, "procMacro": {"enable": False}}`. Il docstring dice «so no project code runs»;
  - ma alla release fissata (`2026-11-09`) `crates/rust-analyzer/src/cli/scip.rs:51-54` carica il workspace con `load_out_dirs_from_check: true` e `with_proc_macro_server: ProcMacroServerChoice::Sysroot`, qualunque cosa dicano `buildScripts.enable` e `procMacro.enable`: esegue i build script (`cargo check`) e costruisce le macro procedurali;
  - in più, il ripiego (`rust.py:311`, `fallback=lambda prefix, output: command(prefix, output)[:-2]`) rilancia rust-analyzer senza `--config-path` quando la prima corsa fallisce (`scripts/code_graph.py`, `module_runs`);
  - dopo `293e3bfac`, team-lead (16 novembre): sull'host `rust-analyzer scip` avvia ancora il server delle macro del sysroot (in `<sysroot>/libexec`, dove `scripts/indexers/rust.py` cerca `rust-analyzer-proc-macro-srv`), e i file del progetto possono fargli avviare programmi del progetto:
    - un `rust-project.json`, con `sysroot`, il sysroot da cui partono il server e rustc, e `proc_macro_dylib_path`, la libreria di una macro compilata (libro di rust-analyzer, «Non-Cargo Based Projects»);
    - un `.cargo/config.toml`, con `build.rustc` e `build.rustc-wrapper`, i programmi che cargo avvia al posto di rustc, o con il `credential-provider` di un registro (Cargo Book, «Configuration»);
    - un file di toolchain di rustup, con `path`, una toolchain locale (libro di rustup, «Overrides»).
- **Progetto e caso:** analizzatore Rust — misura su Modal di dynamic-step-2, 16 novembre 2026.
- **Rimedio:**
  - `293e3bfac` (16 novembre, dynamic-step-2), `scripts/indexers/rust.py`:
    - sull'host `cargo.buildScripts.overrideCommand` è un comando che non esegue niente, e il ripiego senza `--config-path` non c'è più;
    - il build vero gira nel container, con build script e macro accese, sulla toolchain del progetto: la preparazione, con i registri aperti, installa la toolchain e fa `cargo fetch`; l'esecuzione, senza rete, lancia il check di rust-analyzer e poi `rust-analyzer scip`;
    - un build script che fallisce è un buco che nomina il crate, e il crate torna alla lettura senza build script;
    - il messaggio del commit dice che sull'host non parte nessun server di macro: è sbagliato, `scip.rs` avvia quello del sysroot;
  - `c714e6298` (16 novembre, dynamic-step-2), `scripts/indexers/rust.py`: rust-analyzer gira solo nel container di Daodan (`NEEDS_CONTAINER` è vero), e sull'host non parte niente di Rust. Senza container Rust è non disponibile con la causa, come clang e Java; un'esecuzione nel container che finisce male è un fallimento con il suo stato, e una radice di cui il container non scrive l'indice è un buco con le parole di rust-analyzer. Così si chiudono anche le vie del `rust-project.json`, del `.cargo/config.toml` e del file di toolchain.
- **Verifica:**
  - dal commit `293e3bfac`, hoppscotch: buchi Rust da 831 a 689, quelli senza occorrenza da 111 a 5; 23 crate restano buchi, perché all'immagine mancano le librerie GTK e WebKit;
  - `tests/test_codebase_map_indexers_rust.py` (`test_the_host_runs_no_project_code`, `test_without_a_container_the_host_reads_the_project_with_no_build_script_and_says_so`);
  - dal commit `c714e6298`, su Modal (`benchmarks/project-model/modal_rust_container.py`): un crate il cui build script imposta un cfg e scrive un segno, una macro procedurale che genera una funzione e scrive un segno, e cargo, rustc, rust-analyzer e rustup sull'host sostituiti da finti che lasciano un segno. Sull'host nessun segno e nessun finto chiamato; nel container la funzione sotto cfg si risolve e quella generata ha il suo nome;
  - `tests/test_codebase_map_indexers_rust.py` (`test_rust_analyzer_never_runs_on_the_host`, `test_a_container_that_does_not_run_is_the_cause_and_nothing_runs_on_the_host`).
- **Stato:** risolto da `c714e6298`; `293e3bfac` era parziale.
- **Note:** D-161 (Tailwind), D-245 e D-250 (Git), D-248 e D-253 (Python), lo stesso difetto.

#### D-242 C#: `nameof` e le direttive del preprocessore erano chiamate o letture
- **Tag:** lingua csharp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** `nameof(x)`, i nomi che `#pragma` cita e i simboli che `#if` ed `#elif` provano erano registrati come chiamate o letture.
- **Spiegazione:** il lettore dei fatti (`scripts/languages/semantic.py`) trattava `nameof(x)` come una chiamata, mentre è il nome di `x` come costante, e leggeva le condizioni delle direttive come codice.
- **Progetto e caso:** analizzatore C# — commit `15960a591`, 16 novembre 2026.
- **Rimedio:** `15960a591` (16 novembre), `scripts/languages/semantic.py`:
  - `nameof(x)` non è una chiamata né una lettura;
  - di `#if` si leggono tutti i rami, mai ciò che `#if` prova né gli avvisi che `#pragma` nomina.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_csharp.py`, `test_nameof_and_the_names_of_preprocessor_directives_are_neither_calls_nor_reads`).
- **Stato:** risolto.
- **Note:** D-241.

#### D-246 Python: l'analisi girava sull'interprete di Daodan, non sul Python che la cartella dichiara
- **Tag:** lingua python · area analizzatore · tipo correttezza · origine commit · strumento scip-python, uv
- **Descrizione:** fastapi dichiara Python 3.14 in `.python-version`, e la sua analisi girava sul 3.13 (dal commit `3cef87b5c`).
- **Spiegazione:** la corsa di scip-python non prendeva il Python della sua cartella.
- **Progetto e caso:** fastapi (`aabb90126964`) — commit `3cef87b5c`, 16 novembre 2026.
- **Rimedio:** `3cef87b5c` (16 novembre), `scripts/indexers/python.py`:
  - ogni corsa prende il Python che la sua cartella dichiara, come lo legge uv: il file di versione, altrimenti requires-python;
  - dove l'interprete di Daodan non lo soddisfa, `uv venv --python` costruisce l'ambiente, e il rifiuto di uv è `restore_failed` con le sue parole;
  - la corsa dice il Python con cui gira e da dove viene; un Python dichiarato che l'immagine esclude è `python_unavailable`.
- **Verifica:** solo test: `tests/test_codebase_map_indexers_python_runs.py` (`test_each_run_takes_the_python_its_folder_states_first_as_uv_reads_it`), `tests/test_codebase_map_indexers_ts_py.py` (`test_python_reads_the_project_on_the_python_its_folder_states_and_says_which`), `tests/test_codebase_map_resolve_edges.py` (`test_a_python_the_project_states_is_the_one_uv_resolves_for_its_environment`).
- **Stato:** risolto; un Python che l'immagine esclude è un buco dichiarato (`python_unavailable`).
- **Note:** l'osservatore Python prende l'interprete allo stesso modo, D-184.

#### D-247 Python: un nome nudo in un'annotazione definito più sotto era una locale senza definizione
- **Tag:** lingua python · area analizzatore · tipo completezza · origine commit · strumento scip-python, Pyright
- **Descrizione:** in `items: list[Item]`, sopra `class Item`, l'indice scriveva `Item` come una locale che non definisce (dal commit `3cef87b5c`).
- **Spiegazione:** Python 3.14 valuta un'annotazione quando la si legge (PEP 649), e il Pyright di scip-python è più vecchio del 3.14 (docstring di `scripts/indexers/python.py`).
- **Progetto e caso:** analizzatore Python — commit `3cef87b5c`, 16 novembre 2026.
- **Rimedio:** `3cef87b5c` (16 novembre), `scripts/indexers/python.py`: un nome nudo in un'annotazione che il modulo definisce una volta al livello più alto porta a quella definizione (`deferred-annotation`).
- **Verifica:** solo test (`tests/test_codebase_map_indexers_python_runs.py`, `test_a_name_an_annotation_reads_before_its_definition_is_the_module_s_one_definition`).
- **Stato:** risolto.
- **Note:** D-088.

#### D-248 L'ambiente Python dell'analisi eseguiva sull'host il codice dei suoi pacchetti
- **Tag:** lingua python · area analizzatore · tipo sicurezza · origine commit · strumento scip-python, Pyright, uv
- **Descrizione:** scip-python e la passata del checker avviano sull'host l'interprete dell'ambiente di analisi, e `site` esegue all'avvio le righe di import dei `.pth` e i `sitecustomize` dei pacchetti installati: `a1_coverage.pth` di coverage su fastapi e su python-semver, un `.pth` nspkg di sphinxcontrib, `_virtualenv.pth` di uv (dal commit `ef6641248`).
- **Spiegazione:** anche la domanda di uv all'interprete li eseguiva, quando la sua cache mancava.
- **Progetto e caso:** fastapi (`aabb90126964`), python-semver (`b6e83e3e40d3`) — commit `ef6641248`, 16 novembre 2026.
- **Rimedio:** `ef6641248` (16 novembre), `scripts/engine_tools.py` (`_inert`) e `scripts/indexers/python.py`:
  - `_inert` toglie dall'ambiente, con le regole di `site`, ciò che l'interprete eseguirebbe all'avvio; le cartelle che un `.pth` nomina restano;
  - lo fa prima di ogni installazione di uv, dopo l'ultima e su un ambiente riusato;
  - uv gira fuori dalla cartella del progetto, così non ne legge la configurazione.
- **Verifica:**
  - dal commit, su Modal con gli strumenti veri e un pacchetto che lascia un segno; fastapi e python-semver danno gli stessi archi e buchi di prima;
  - `tests/test_codebase_map_indexers_python_runs.py` (`test_the_analyzer_on_the_host_reads_the_project_and_its_environment_and_runs_none_of_them`), `tests/test_codebase_map_resolve_edges.py` (`test_what_an_interpreter_would_run_from_the_environment_is_removed_before_uv_starts_it`).
- **Stato:** risolto.
- **Note:** D-042 (uv leggeva la configurazione del progetto); D-161, D-239 e D-245, lo stesso difetto.

#### D-249 C#: un gruppo di metodi passato come `System.Delegate` non aveva occorrenza
- **Tag:** lingua csharp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-dotnet, Roslyn
- **Descrizione:** su eShop un gruppo di metodi passato dove il parametro è un `System.Delegate` restava senza occorrenza e senza risposta (dal commit `9290d446a`).
- **Spiegazione:** `ScipCSharpSyntaxWalker` legge solo `GetSymbolInfo(node).Symbol`, e Roslyn 5.3.0 lascia quel gruppo di metodi senza `Symbol`, con il metodo come unico candidato (`docs/research/2026-11-16-scip-dotnet-names.md`).
- **Progetto e caso:** eShop (`913acea66708`) — misura su Modal del commit `9290d446a`, 16 novembre 2026.
- **Rimedio:** `9290d446a` (16 novembre), `scripts/indexers/scip-dotnet.patch`: la patch di Daodan a scip-dotnet 0.2.16 nomina il metodo, unico candidato di un gruppo di metodi (D-116).
- **Verifica:** dal commit, su eShop: dei 997 riferimenti senza occorrenza che non sono nomi con argomenti di tipo ne restano 911.
- **Stato:** risolto.
- **Note:** D-114, D-116.

#### D-253 uv sull'host poteva installare una ruota costruita da un sdist e leggeva configurazioni altrui
- **Tag:** lingua python · area analizzatore · tipo sicurezza · origine commit · strumento uv
- **Descrizione:** ogni `uv pip install` dell'ambiente di analisi aveva già `--only-binary :all:`, ma con la cache dell'utente uv poteva installare una ruota che lui stesso aveva costruito da un sdist, e leggeva la configurazione dell'utente e del progetto (`uv.toml`, `[tool.uv]`) (dal commit `a9b4e1df2`).
- **Spiegazione:** la cache e la configurazione erano quelle che uv trova da sé; costruire una ruota da un sdist esegue il suo `setup.py` sull'host.
- **Progetto e caso:** analizzatore Python — commit `a9b4e1df2`, 16 novembre 2026.
- **Rimedio:** `a9b4e1df2` (16 novembre), `scripts/engine_tools.py` e `scripts/indexers/python.py`:
  - ogni chiamata a uv ha `--no-config` e la cache di Daodan (`--cache-dir` nella cartella condivisa), e gira fuori dal progetto;
  - `uv export` ha anche `--frozen --no-build`: ogni ruota installata è una ruota pubblicata, e una ruota non ha hook di installazione;
  - un requisito che uv non sa installare, per esempio uno che ha solo un sdist, è in `failed` di `daodan-environment.json` con le parole di uv e diventa un buco `restore_failed` che nomina il pacchetto.
- **Verifica:**
  - dal commit, una prova a segni con uv vero: un pacchetto con solo un sdist il cui `setup.py` lascia un segno, e configurazioni illeggibili dell'utente e del progetto; nessun segno, e il buco nomina `daodansdist` con le parole di uv. fastapi: l'export dà sempre 98 requisiti;
  - `tests/test_codebase_map_resolve_edges.py` (`test_a_lock_is_exported_by_daodan_s_own_uv_and_nothing_is_built`, `test_a_package_without_a_wheel_is_a_failure_naming_it_and_nothing_is_built`).
- **Stato:** risolto.
- **Note:** D-248, la stessa via: l'ambiente Python dell'analisi sull'host; D-254, la versione di uv.

#### D-254 L'uv dell'host non è fissato
- **Tag:** lingua python · area host · tipo correttezza · origine review · strumento uv
- **Descrizione:** sull'host l'analisi Python usa l'uv che trova sul PATH: con lo 0.7.19 di questo PC, la versione 3.14 di fastapi diventava l'interprete 3.14.0b3 (D-252) (riportato da team-lead il 16 novembre).
- **Spiegazione:** nel container uv è fissato allo 0.11.28 (`scripts/preparation.py:25`, `:64`); sull'host no.
- **Progetto e caso:** fastapi (`aabb90126964`) — review di team-lead, 16 novembre 2026.
- **Rimedio:** `5e3757031` (16 novembre, python-env), `scripts/engine_tools.py` (`uv_binary`, `UV_ASSETS`): l'uv 0.11.28 scaricato una volta e controllato con lo sha256 del rilascio, mai quello del PATH; senza, Python è non disponibile con la causa. fastapi: deps.py letto da 3.14.6, grafo invariato.
- **Verifica:** —.
- **Stato:** risolto.
- **Note:** D-252, D-253.

#### D-255 scip-clang leggeva i database di GCC con gli header builtin di GCC
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine prova su Modal · strumento scip-clang, GCC
- **Descrizione:** per ogni progetto costruito con GCC, clang dava migliaia di errori mentre scip-clang diceva «num errored TUs: 0» e scriveva l'indice, in silenzio (dal commit `125ab9ebd`).
- **Spiegazione:** scip-clang aggiunge in coda al comando di un compilatore che non è clang `-resource-dir <installazione di GCC>`, che nessun flag precedente può scavalcare, così clang legge gli header builtin di GCC (`xmmintrin.h` e gli altri intrinseci); scip-clang non ha un'opzione per questo (la sua issue 440 è chiusa «not planned»).
- **Progetto e caso:** otel-demo currency (`b825c7c25726`), riprodotto da android-sdk — commit `125ab9ebd` di clang-builds, 16 novembre 2026.
- **Rimedio:** `125ab9ebd` (16 novembre), `scripts/indexers/clang_run.py` (`builtin_headers`) e `scripts/indexers/clang.py`:
  - ogni database è riscritto prima che scip-clang lo legga: per un compilatore che non è clang aggiunge `-nobuiltininc -isystem <header di clang> -idirafter $(<cc> -print-file-name=include)`, l'ultimo per `omp.h` e `quadmath.h`; un compilatore clang o un comando con `-nostdinc` resta com'è;
  - gli header sono quelli di clang 21.1.8, la versione di LLVM di scip-clang v0.4.1: `lib/Headers` del sorgente del rilascio, fissato per sha256 (Apache-2.0 WITH LLVM-exception), impacchettati una volta in un tar; nei simboli il loro pacchetto è `clang@21.1.8`.
- **Verifica:**
  - dal commit, con `clang.index()` vero nell'immagine su Modal: libdeflate v1.23 da 11.150 errori a 0 (indicizzazione da 20,0 s a 2,3 s), una sonda C e C++ su `_mm_pause` da 3.492 a 0, tinyxml2 e sys-make-plain da 0 a 0;
  - `tests/test_codebase_map_indexers_clang.py` (`test_a_gcc_command_reads_the_builtin_headers_of_the_clang_scip_clang_is_built_on`, `test_scip_clang_reads_the_database_with_clangs_builtin_headers_and_names_their_package`, `test_clangs_builtin_headers_come_from_its_release_source_packed_once`).
- **Stato:** risolto da `125ab9ebd` nella via principale; la via degli stadi del Dockerfile legge ancora gli header di GCC, ed è in corso (android-sdk).
- **Note:** D-135 (otel-demo currency); il commit è successivo ai commit dei risultati di tutti i giri.

#### D-257 L'analizzatore Go esegue sull'host `go mod download` e il compilatore C
- **Tag:** lingua go · area analizzatore · tipo sicurezza · origine review · strumento go, git, gcc
- **Descrizione:** host-guard-2, nella sua revisione dell'host: l'analizzatore Go lancia sull'host `go mod download` con l'ambiente intero dell'utente e senza `GOPROXY`, `GOVCS`, `GOENV` né `GOSUMDB`, così un modulo del progetto può far raggiungere a git il suo host (su Modal è registrato `git ls-remote https://github.com/<modulo>`); e per cgo lancia il compilatore C dell'host (`gcc -E -dM … cgo-gcc-input.c`) (riportato da team-lead il 16 novembre).
- **Spiegazione:** `scripts/indexers/go.py:652` lancia `go mod download` nella copia del progetto con `env`; `_cgo` (`go.py:381`) chiede `go env CGO_ENABLED`, e Go prova il compilatore C che trova.
- **Progetto e caso:** analizzatore Go — revisione di host-guard-2, su Modal, 16 novembre 2026.
- **Rimedio:** in corso (host-guard-2): Go solo nel container di Daodan.
- **Verifica:** —. La regola chiede un test con un modulo e un compilatore che, se eseguiti, lasciano un segno.
- **Stato:** aperto (host-guard-2): viola la regola invalicabile di `AGENTS.md` (`2753088a3`).
- **Note:** D-239, la stessa via per Rust.

#### D-258 Vue e Svelte eseguivano sull'host l'installazione npm e il TypeScript del progetto
- **Tag:** lingua vue, svelte · area analizzatore · tipo sicurezza · origine review · strumento npm, typescript-language-server
- **Descrizione:** host-guard-2: `engine_tools.npm_modules` lancia sull'host `npm ci` con l'ambiente dell'utente e senza rifiutare i pacchetti git o da URL, e il `tsserver.js` del `node_modules/typescript` del progetto è girato sull'host (registrato su Modal) (riportato da team-lead il 16 novembre).
- **Spiegazione:** lo stadio di Vue e Svelte gira sull'host (`scripts/indexers/vue_svelte.py`, `NEEDS_CONTAINER` falso): installa i pacchetti del progetto con `npm_modules` (`scripts/engine_tools.py:247-250`, `env={**os.environ, ...}`), lega quel `node_modules` alla copia del progetto e chiede le chiamate a typescript-language-server, che carica il TypeScript che trova lì.
- **Progetto e caso:** analizzatore di Vue e Svelte — revisione di host-guard-2, su Modal, 16 novembre 2026.
- **Rimedio:** `b9aeca1fb` (16 novembre, csharp-2): Vue e Svelte passano a scip-typescript nel container di Daodan (`scripts/languages/sfc.py` legge i template, `scripts/indexers/components.py` genera il TypeScript dei componenti con lo strumento del progetto, su Node fissato per sha256); la vecchia via di `scripts/indexers/vue_svelte.py` non serve più nessun linguaggio (`LANGUAGES = ()`), resta senza chiamanti e si toglie dopo i giri reali.
- **Verifica:** solo test, a segni: `svelte.config.js`, lo strumento Vue e svelte-kit lasciano un segno se eseguiti, e dopo un indice intero il progetto non ne ha (`tests/test_codebase_map_components.py`, `test_no_code_of_the_project_runs_on_the_host`); nessun giro dopo il commit.
- **Stato:** risolto; il codice della vecchia via resta, senza chiamanti, fino ai giri reali.
- **Note:** D-080 e D-159, i template non letti.

#### D-259 Un header `.h` di C++ letto come C
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** `meter_common.h` di otel-demo, un header C++ con un alias di namespace, un namespace anonimo e `std::`, era letto come C, e il parser C falliva (dal commit `bdfd7797b`).
- **Spiegazione:** `_CPP_HEADER_RE` (`scripts/languages/__init__.py`) non riconosceva alias e namespace anonimi, i nomi `std::` né le inclusioni della libreria standard C++; e il C può usare `namespace` come nome (`struct namespace {`, `p->namespace = x`), come ha misurato clang-reader.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — commit `bdfd7797b`, 16 novembre 2026.
- **Rimedio:** `bdfd7797b` (16 novembre), `scripts/languages/__init__.py`: `_CPP_HEADER_RE` riconosce alias e namespace anonimi, i nomi `std::` e le inclusioni della libreria standard C++ della regola di Linguist per `.h`; le forme del namespace contano solo quando `namespace` apre la riga.
- **Verifica:** solo test (`tests/test_codebase_map_clang_reader.py`, `test_a_header_is_cpp_only_when_its_text_has_what_c_lacks`); i casi C nuovi falliscono senza la correzione.
- **Stato:** risolto.
- **Note:** D-128, l'altro caso di un `.h` letto con il linguaggio sbagliato.

### Passo dinamico e osservatori

#### D-167 «Osservato» con zero osservazioni
- **Tag:** lingua tutti · area passo dinamico · tipo correttezza · origine commit · strumento —
- **Descrizione:** un linguaggio poteva risultare osservato senza una sola osservazione.
- **Spiegazione:** lo stato non distingueva una corsa senza test, o senza righe, da una corsa che osserva.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `12775fee3` (16 novembre), `scripts/dynamic/__init__.py`: `not-run` e `not-observed` al posto di un falso «osservato».
- **Verifica:** giro `fixtures` sui 104 progetti: nei progetti in miniatura quasi sempre non ci sono test da lanciare, e il risultato lo dice (README del benchmark).
- **Stato:** risolto.
- **Note:** D-172.

#### D-168 Un risultato malformato di un osservatore fermava la pipeline
- **Tag:** lingua tutti · area passo dinamico · tipo correttezza · origine commit · strumento —
- **Descrizione:** un osservatore che restituisce un risultato fuori contratto fermava la pipeline con un errore.
- **Spiegazione:** il contratto dell'osservatore non era scritto né controllato.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `12775fee3`, `scripts/dynamic/__init__.py` (`malformed`): il contratto è scritto e controllato, e un risultato malformato è un buco che nomina l'osservatore.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-169 pytest fermo agli errori di raccolta
- **Tag:** lingua python · area passo dinamico · tipo completezza · origine prova su Modal · strumento pytest
- **Descrizione:** la prima corsa della pipeline con il passo dinamico, su Daodan stesso su Modal, osserva 1.361 punti e chiude 82 buchi (`d94f92470`), ma solo dall'import dei moduli di test.
- **Spiegazione:** pytest si fermava agli errori di raccolta, così i test Python non partivano oltre la raccolta.
- **Progetto e caso:** il codice di Daodan, senza `benchmarks/` — corsa su Modal, 16 novembre 2026 (analisi 26 minuti, passo dinamico 2,6).
- **Rimedio:** `12775fee3`: pytest prosegue oltre i moduli che non si importano (`--continue-on-collection-errors`), e quei moduli sono dichiarati come buco.
- **Verifica:** da verificare: la spec del passo dinamico lo dà da rimisurare.
- **Stato:** risolto.
- **Note:** —

#### D-170 JavaScript: il TypeScript che Node toglie da solo
- **Tag:** lingua javascript, typescript · area passo dinamico · tipo completezza · origine commit · strumento —
- **Descrizione:** il commit elenca nell'osservatore JavaScript il TypeScript che Node toglie da solo.
- **Spiegazione:** da verificare: il commit non dice di più.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`.
- **Verifica:** prova vera su Modal: JavaScript osservato (6 chiamate).
- **Stato:** risolto.
- **Note:** —

#### D-171 Un comando di test fallito senza l'errore vero nel buco
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento —
- **Descrizione:** il buco di un comando di test fallito non portava l'errore vero.
- **Spiegazione:** il buco non riportava l'uscita d'errore del comando.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`: l'errore vero entra nel buco.
- **Verifica:** finale, fastapi: «no test ran: npm test in . exited with code 127 and recorded no call: > test | > bun run --filter frontend test | | sh: 1: bun: not found».
- **Stato:** risolto.
- **Note:** —

#### D-172 `not-observed` non diceva cosa aveva visto il registratore
- **Tag:** lingua tutti · area passo dinamico · tipo completezza · origine commit · strumento —
- **Descrizione:** `not-observed` diceva solo che nessuna chiamata era caduta su un riferimento, seguito da buchi estranei.
- **Spiegazione:** la causa non veniva da ciò che il registratore aveva visto.
- **Progetto e caso:** py-setup-cfg-extras, il cui unico test non chiama nulla e dove cli.py non gira — 16 novembre 2026.
- **Rimedio:** `0c57a839a` (16 novembre), `scripts/dynamic/__init__.py` (`_unplaced`); la causa dice una di queste cose:
  - siti nei file del linguaggio senza riferimento, contati per ruolo;
  - chiamate solo in file fuori dallo snapshot;
  - nessuna chiamata dai file del linguaggio, con i file che i test non hanno eseguito.

  La spec ne ha la sezione «Corsa senza righe».
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-167.

#### D-173 Go e Rust non pianificavano i test della radice
- **Tag:** lingua go, rust · area passo dinamico · tipo completezza · origine commit · strumento —
- **Descrizione:** i test del modulo o del crate alla radice non giravano.
- **Spiegazione:** la pre-mappa nomina la radice del progetto con il percorso vuoto, e Go e Rust non la riconoscevano.
- **Progetto e caso:** osservatori Go e Rust — 16 novembre 2026.
- **Rimedio:** `a491415e6` (16 novembre), `scripts/dynamic/go.py` e `scripts/dynamic/rust.py`.
- **Verifica:** prova vera su Modal: Go osservato (1 chiamata), C/C++ osservato su Callgrind (5 chiamate).
- **Stato:** risolto.
- **Note:** D-174.

#### D-174 Go fuori dal contratto dell'osservatore
- **Tag:** lingua go · area passo dinamico · tipo correttezza · origine commit · strumento —
- **Descrizione:** `12775fee3` dice Go «ancora da adeguare» al contratto.
- **Spiegazione:** Go non riportava runner e stato come chiede il contratto.
- **Progetto e caso:** osservatore Go — 16 novembre 2026.
- **Rimedio:** `a491415e6`, `scripts/dynamic/go.py`.
- **Verifica:** prova vera su Modal, come D-173.
- **Stato:** risolto.
- **Note:** —

#### D-175 Rust: «can't find crate for std»
- **Tag:** lingua rust · area passo dinamico · tipo correttezza · origine commit · strumento Cargo, rustc
- **Descrizione:** ogni cargo test falliva su «can't find crate for std».
- **Spiegazione:** il rustc fissato non contiene le librerie standard.
- **Progetto e caso:** osservatore Rust — 16 novembre 2026.
- **Rimedio:** `ef69774f9` (16 novembre), `scripts/dynamic/rust.py` e `scripts/dynamic/callgrind.py`: rust-std 1.99.1, fissato per sha256.
- **Verifica:** in una Function di Modal con gli script dell'osservatore: cargo test sotto Callgrind, 8 siti, nessun buco.
- **Stato:** risolto.
- **Note:** sotto gVisor resta D-209.

#### D-176 Launchpad 502: Rust perde l'osservazione
- **Tag:** lingua rust · area passo dinamico · tipo completezza · origine fixtures · strumento Valgrind, Launchpad
- **Descrizione:** nel giro sulle fixture Launchpad ha risposto 502, e il passo dinamico Rust ha perso l'osservazione.
- **Spiegazione:** Valgrind aveva una sola fonte.
- **Progetto e caso:** giro `fixtures` — 16 novembre 2026.
- **Rimedio:** `d5964e7b9` (16 novembre), `scripts/dynamic/callgrind.py`:
  - lo stesso file, con lo stesso sha256, viene prima da archive.ubuntu.com e poi da Launchpad;
  - se cadono entrambe, il buco nomina i due errori.
- **Verifica:** conferma: Rust osservato in semver (558 siti).
- **Stato:** risolto.
- **Note:** —

#### D-177 L'osservatore C/C++ installava con vcpkg dove l'analizzatore usa Conan
- **Tag:** lingua c, cpp · area passo dinamico · tipo correttezza · origine commit · strumento Conan, vcpkg
- **Descrizione:** con vcpkg.json, conanfile.txt e un preset che nomina il toolchain di Conan, osservatore e analizzatore usavano gestori diversi.
- **Spiegazione:** l'osservatore sceglieva il gestore da sé.
- **Progetto e caso:** progetti con vcpkg e Conan insieme — 16 novembre 2026.
- **Rimedio:** `a8a1ebdb5` (16 novembre), `scripts/dynamic/clang.py`: prende da `indexers/clang.restores` la riga di installazione e la preparazione del gestore di ogni radice.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-125.

#### D-178 L'osservatore JVM compilava sul JDK dell'immagine
- **Tag:** lingua java · area passo dinamico · tipo correttezza · origine real-3 · strumento —
- **Descrizione:** real-3: su javapoet il passo dinamico fallisce perché la build gira sul JDK dell'immagine e non su quello dichiarato (`7532ed2e7`).
- **Spiegazione:** l'osservatore non installava il JDK dichiarato, e l'agente non era costruito per Java 8.
- **Progetto e caso:** javapoet — real-3, 16 novembre 2026.
- **Rimedio:** `a633ebd72` (16 novembre):
  - `scripts/dynamic/jvm.py`, e in `scripts/dynamic/jvm_record/` `Agent.java`, `Modular.java`, `Recorder.java` e `Walker.java`;
  - l'osservatore compila sul JDK dichiarato, Java 8 compreso;
  - l'agente è costruito per Java 8 e provato su JDK 8 e 17.
- **Verifica:** su Modal, javapoet (`609ca96dd`): l'osservatore compila sul JDK 8 dichiarato con Error Prone al suo posto, 389 test e 6.021 siti osservati.
- **Stato:** risolto.
- **Note:** D-099, D-224.

#### D-179 Java 25: «No access to RETAIN_CLASS_REFERENCE»
- **Tag:** lingua java · area passo dinamico · tipo correttezza · origine prova su Modal · strumento —
- **Descrizione:** sotto Java 25 i test fallivano tutti sotto il registratore.
- **Spiegazione:** i JDK recenti pretendono un permesso che `Walker` non chiedeva.
- **Progetto e caso:** jvm-ver-* — misura su Modal con 18 progetti, 16 novembre 2026.
- **Rimedio:** `21b3cb39b` (16 novembre), `scripts/dynamic/jvm_record/Walker.java`: chiede il permesso.
- **Verifica:** java-versions: Java osservato in tutte le 18 fixture, 10-14 siti osservati per caso.
- **Stato:** risolto.
- **Note:** —

#### D-180 Test JVM multipiattaforma: nessun compito `test`
- **Tag:** lingua kotlin · area passo dinamico · tipo completezza · origine commit · strumento Gradle
- **Descrizione:** in un progetto Kotlin multipiattaforma i test JVM stanno in `jvmTest`, non in `test`.
- **Spiegazione:** l'osservatore lanciava `gradle test`.
- **Progetto e caso:** jvm-kmp-common-jvm — 16 novembre 2026.
- **Rimedio:** `9fe650a3a` (16 novembre), `scripts/dynamic/jvm.py` e `scripts/dynamic/jvm_record/tests.gradle`:
  - un init script sceglie per progetto `test` o, se manca, ogni compito Test;
  - nella preparazione scarica il loro classpath;
  - l'esecuzione offline gira quelli.
- **Verifica:** finale: Kotlin osservato in 4 casi, 1.796 siti.
- **Stato:** risolto.
- **Note:** —

#### D-181 Java 9 e 14 senza un JDK installabile
- **Tag:** lingua java · area passo dinamico · tipo completezza · origine java-versions · strumento —
- **Descrizione:** java-versions: per Java 9 e 14 non c'è un JDK da installare.
- **Spiegazione:** non esiste un JDK installabile di quelle versioni (README del benchmark).
- **Progetto e caso:** jvm-ver-* — java-versions, 16 novembre 2026.
- **Rimedio:** il passo dinamico li osserva sul JDK 17 e lo dice.
- **Verifica:** java-versions.
- **Stato:** buco dichiarato (`toolchain_unavailable`).
- **Note:** —

#### D-182 I servizi della CI non avviati: tududi chiede PostgreSQL
- **Tag:** lingua tutti · area servizi · tipo completezza · origine real-3 · strumento GitHub Actions
- **Descrizione:** real-3: su tududi i test del backend chiedono PostgreSQL (`7532ed2e7`).
- **Spiegazione:** il passo non avviava i servizi che la CI dichiara.
- **Progetto e caso:** tududi — real-3, 16 novembre 2026.
- **Rimedio:** `17babc624` (16 novembre), `scripts/container.py` e `scripts/dynamic/`:
  - i `services:` dei workflow di GitHub Actions, letti con la libreria YAML di Renovate, diventano la faccetta `services`;
  - ogni container dei test gira in un pod (`--network none`) con i servizi dichiarati, immagini fissate per digest e controllo di salute atteso;
  - i test li trovano su localhost, e fuori non si esce;
  - su Modal girano in sandbox a macchina virtuale con Docker;
  - un servizio che non parte è `service_unavailable`.
- **Verifica:**
  - `b85aa1b9f`: il pod è provato su un Docker vero in un sandbox a macchina virtuale di Modal, con il postgres di tududi raggiunto a localhost e per nome, sano in 5 secondi, 1.1.1.1 irraggiungibile e nessun container lasciato;
  - conferma: i test del backend girano con il PostgreSQL della CI, 3.779 siti JavaScript e 691 buchi chiusi.
- **Stato:** risolto.
- **Note:** D-201, D-202.

#### D-183 Python: le dipendenze dei test non venivano dall'ambiente del runner
- **Tag:** lingua python · area passo dinamico · tipo correttezza · origine finale · strumento pytest, tox
- **Descrizione:** finale: python-semver Python `not-run`.
- **Spiegazione:** le dipendenze dei test non venivano dall'ambiente tox che lancia il runner, né dal gruppo, extra o file che nomina pytest.
- **Progetto e caso:** python-semver (`b6e83e3e40d3`) — finale, 16 novembre 2026.
- **Rimedio:** `17babc624`: le dipendenze dei test vengono da quell'ambiente.
- **Verifica:** conferma: python-semver osservato, 1.046 siti, «con i link e le dipendenze di tox» (`828b5413b`).
- **Stato:** risolto.
- **Note:** D-206.

#### D-184 Python: l'interprete non veniva da requires-python o .python-version
- **Tag:** lingua python · area passo dinamico · tipo correttezza · origine commit · strumento uv
- **Descrizione:** il Python dei test non era quello che il progetto dichiara.
- **Spiegazione:** uv non sceglieva l'interprete come fa `uv sync`.
- **Progetto e caso:** osservatore Python — 16 novembre 2026.
- **Rimedio:** `17babc624`: uv sceglie e scarica l'interprete da requires-python o .python-version, come `uv sync`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-188.

#### D-185 tududi: `test` non arriva ai test del frontend
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento Jest, npm
- **Descrizione:** in tududi `test` lancia jest solo in backend/, mentre `frontend:test` e altri quattro script lanciano jest nella radice, dove stanno i test del frontend.
- **Spiegazione:** l'osservatore lanciava solo lo script `test`.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `4ee44da0a` (16 novembre), `scripts/premap/npm_tests.py` (npm-tests v4) e `scripts/dynamic/javascript.py`: il buco `tests_not_declared {path, runner, scripts}`, che il motivo del linguaggio nomina.
- **Verifica:** solo test.
- **Stato:** risolto con D-186.
- **Note:** D-186.

#### D-186 L'osservatore JavaScript non lanciava gli script di test che `test` non raggiunge
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento npm
- **Descrizione:** come D-185.
- **Spiegazione:** uno script di package.json che avvia un runner noto è il comando dichiarato per quei test, anche se la CI non lo chiama.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `7e5eb092e` (16 novembre), `scripts/premap/npm_tests.py` (npm-tests v5) e `scripts/dynamic/javascript.py`:
  - per ogni cartella e runner che `test` non raggiunge, un ingresso `tests` con lo script che lo avvia con meno argomenti;
  - mai in modalità watch né in attesa di un debugger (dalle documentazioni di Jest, Vitest, Mocha, Node, Bun e Turborepo);
  - l'osservatore lo lancia come `npm run <script>`;
  - `tests_not_declared` resta solo dove ogni candidato è escluso.
- **Verifica:** su Modal, tududi: `frontend:test` gira, 1.077 test su 1.080 passano, 20.985 siti osservati; finale: tududi TypeScript osservato, 20.204 siti.
- **Stato:** risolto.
- **Note:** D-187.

#### D-187 tududi: i worker di Jest uccisi per memoria
- **Tag:** lingua javascript · area passo dinamico · tipo prestazioni · origine conferma · strumento Jest
- **Descrizione:**
  - conferma: i test del frontend di tududi scesi a 92 siti (`828b5413b`);
  - SIGKILL in 154 suite del frontend su 156.
- **Spiegazione:** Jest avvia un worker per CPU che vede, circa 20 sull'host, ognuno da 2-3 GB sotto il registratore, in un container da 4 GB.
- **Progetto e caso:** tududi — conferma, 16 novembre 2026.
- **Rimedio:** `37c7ee093` (16 novembre), `scripts/dynamic/javascript.py`: i test girano come sul runner ubuntu-latest di GitHub, con 16 GB e `taskset` sulle prime 4 CPU.
- **Verifica:** su Modal, il frontend: 156 suite, 23.274 siti, nessuno non osservato.
- **Stato:** risolto.
- **Note:** D-189.

#### D-188 fastapi: uv.lock non visto, l'intervallo di Python rifiutato
- **Tag:** lingua python · area passo dinamico · tipo correttezza · origine finale · strumento uv, pip
- **Descrizione:** finale e conferma, fastapi: «the project states Python >=3.14,<4.0 (backend/pyproject.toml): a range that excludes the image's 3.13.18 and names no version to install».
- **Spiegazione:** lo snapshot non tiene i lockfile, così l'osservatore Python non vedeva uv.lock, trattava la cartella come pip e rifiutava l'intervallo.
- **Progetto e caso:** fastapi — finale e conferma, 16 novembre 2026.
- **Rimedio:** `37c7ee093`, `scripts/dynamic/python.py`: il piano conta uv.lock e poetry.lock accanto al manifest quando il checkout li ha, e uv sceglie Python 3.14.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-197.

#### D-189 I test JavaScript con 16 GB fissi anche dove la macchina non li ha
- **Tag:** lingua javascript · area passo dinamico · tipo prestazioni · origine commit · strumento —
- **Descrizione:** la forma fissa di D-187 poteva superare la memoria libera.
- **Spiegazione:** CPU e memoria non seguivano la macchina.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `a42dc1d86` (16 novembre), `scripts/dynamic/javascript.py`:
  - la forma del runner della CI (4 CPU, 16 GB) è il tetto;
  - con meno memoria libera le corse hanno tante CPU quante la memoria ne regge a 2,5 GB per processo (misurati su Jest di tududi), almeno una;
  - sotto 2,5 GB liberi nessun container parte, e il buco dice la memoria trovata e quella che serve;
  - ogni corsa dichiara le CPU e la memoria con cui è girata.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-190 Turborepo: il registratore non partiva
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento Turborepo
- **Descrizione:** i test lanciati da Turborepo giravano non registrati.
- **Spiegazione:** la modalità strict di Turborepo, quella predefinita, passa ai task NODE_OPTIONS ma non le variabili del registratore; il preload si caricava e il registratore non partiva.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `cdc1660dd` (16 novembre), `scripts/dynamic/javascript.py`:
  - l'esecuzione imposta `TURBO_ENV_MODE=loose`, l'equivalente documentato di `--env-mode=loose` (turbo >= 2.1.0);
  - se turbo non registra nulla, il buco nomina turbo e il motivo.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-191, D-192.

#### D-191 npm-tests non riconosceva `turbo run … test`
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento npm, Turborepo
- **Descrizione:** uno script di test che passa da turbo non aveva runner.
- **Spiegazione:** il lettore degli script npm non conosceva turbo.
- **Progetto e caso:** pre-mappa dei test npm — 16 novembre 2026.
- **Rimedio:** `cdc1660dd`, `scripts/premap/npm_tests.py` (npm-tests v3).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-192 Un run di Node senza test letto come un registratore che non raggiunge i processi
- **Tag:** lingua javascript · area passo dinamico · tipo correttezza · origine commit · strumento —
- **Descrizione:** un run di Node che non trova test risultava un guasto del registratore.
- **Spiegazione:** l'esito «nessun test» non era distinto.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `cdc1660dd`: è `no_tests`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-193 ES module non registrati su Node prima della 22.15
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento —
- **Descrizione:** su un Node senza `module.registerHooks` gli ES module giravano non registrati.
- **Spiegazione:** il registratore usava `module.registerHooks`, che manca prima della 22.15.
- **Progetto e caso:** mix-infra-gha — 16 novembre 2026.
- **Rimedio:** `756ebbcb3` (16 novembre), `scripts/dynamic/javascript_record.js`: il registratore usa `module.register` con un modulo di hook che stampa con lo stesso plugin Babel.
- **Verifica:** mix-infra-gha su Node 20.18.1: 6 siti registrati, niente di non osservato.
- **Stato:** risolto.
- **Note:** —

#### D-194 jhipster: 162 chunk di Vitest in memoria non registrati
- **Tag:** lingua javascript, typescript · area passo dinamico · tipo completezza · origine commit · strumento Vitest, Angular
- **Descrizione:** jhipster: `ng test`, il builder di Angular con Vitest, valuta chunk tenuti in memoria con una mappa inline verso i .ts originali, e i 162 chunk giravano non registrati.
- **Spiegazione:** il registratore usava una mappa inline solo per un file che esiste e porta a sé stesso.
- **Progetto e caso:** jhipster-sample — 16 novembre 2026.
- **Rimedio:** `e8bc485d7` (16 novembre), `scripts/dynamic/javascript_record.js`:
  - il codice con una mappa inline si registra anche senza un file;
  - una chiamata è un sito del file a cui la mappa porta, se lì è scritto lo stesso nome.
- **Verifica:** su Modal: 6.769 siti in 179 file del progetto, nessuno non osservato.
- **Stato:** risolto.
- **Note:** —

#### D-195 `bun test` non registrato
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento Bun
- **Descrizione:** in fastapi `bun test` gira senza registratore.
- **Spiegazione:** il registratore non osserva il runner di Bun.
- **Progetto e caso:** fastapi — 16 novembre 2026.
- **Rimedio:** `5148e8eb3` lo dichiara.
- **Verifica:** su Modal.
- **Stato:** buco dichiarato (`runner_not_observed`).
- **Note:** D-056.

#### D-196 Un progetto senza test dichiarati, o con test che non partono
- **Tag:** lingua tutti · area passo dinamico · tipo completezza · origine fixtures · strumento —
- **Descrizione:** il passo vede solo ciò che i test eseguono.
- **Spiegazione:** senza un comando dichiarato il passo non lancia nulla: il comando è quello che il progetto dichiara, mai una convenzione di Daodan.
- **Progetto e caso:** spec del passo dinamico, sezione «Limiti»; i progetti in miniatura del giro `fixtures`.
- **Rimedio:** le lacune `no_test_command` e `tests_not_declared`, e `tests-not-run` nell'unione.
- **Verifica:** fixtures e finale.
- **Stato:** buco dichiarato (`no_test_command`, `tests_not_declared`, `tests-not-run`).
- **Note:** —

#### D-197 I test di fastapi non ancora girati davvero
- **Tag:** lingua python, typescript · area passo dinamico · tipo completezza · origine finale · strumento —
- **Descrizione:** finale e conferma, fastapi: TypeScript e Python `not-run` (D-056, D-188).
- **Spiegazione:** le due cause hanno un rimedio, ma nessun giro le prova insieme.
- **Progetto e caso:** fastapi — finale e conferma, 16 novembre 2026.
- **Rimedio:** `5148e8eb3`, `37c7ee093`.
- **Verifica:** su Modal `npm test` arriva a Playwright (`5148e8eb3`); Python su 3.14, solo test.
- **Stato:** aperto.
- **Note:** D-056, D-188, D-195.

#### D-198 I test di eShop non ancora girati
- **Tag:** lingua javascript, typescript, csharp · area passo dinamico · tipo completezza · origine finale · strumento npm
- **Descrizione:** finale, eShop: C# `no-observer`; JavaScript e TypeScript «no package.json of the project declares a test script (`scripts.test`): nothing is observed».
- **Spiegazione:** C# non ha osservatore, e gli script npm non dichiarano test.
- **Progetto e caso:** eShop — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto: C# senza osservatore (csharp-dotnet).
- **Note:** D-114.

#### D-199 Python: extra e gruppi che il gestore non installa
- **Tag:** lingua python · area passo dinamico · tipo completezza · origine spec · strumento —
- **Descrizione:** un ambiente Python riceve le dipendenze che il ripristino condiviso installa.
- **Spiegazione:** gli extra e i gruppi che il gestore non installa da sé mancano, e i test che li importano non partono (spec, «Limiti»).
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** buco dichiarato (test che non partono, `tests-not-run`).
- **Note:** D-183 prende le dipendenze dall'ambiente del runner.

#### D-200 Python più vecchio del 3.12
- **Tag:** lingua python · area passo dinamico · tipo completezza · origine spec · strumento —
- **Descrizione:** un progetto che dichiara un Python più vecchio, una versione o un intervallo che finisce sotto 3.12, non ha i test osservati.
- **Spiegazione:** il registratore chiede Python 3.12 (spec, sezione 7).
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** la lacuna `python_too_old`.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`python_too_old`).
- **Note:** —

#### D-201 I servizi che `docker compose up` avvia non partivano
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento npm, Compose, GitHub Actions
- **Descrizione:** i test che vogliono i servizi avviati da Compose in un passo di GitHub Actions o in uno script di test npm non li avevano.
- **Spiegazione:** il passo avviava solo i service container dei job.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre):
  - un passo o uno script che lancia `docker compose up` è un fatto `compose`;
  - `scripts/premap/compose.py` lancia il `config` di Compose 5.6.1, binario fissato, senza rete né motore, e dichiara ogni servizio che partirebbe;
  - un comando non leggibile è `compose_not_read`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-212, D-214, D-215.

#### D-202 I servizi di GitLab CI non avviati
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento GitLab CI
- **Descrizione:** i `services:` di `.gitlab-ci.yml` non partivano accanto ai test.
- **Spiegazione:** il lettore dei servizi leggeva solo GitHub Actions.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `23de469c4` (16 novembre):
  - entrano i servizi di ogni job: i suoi, quelli dei template via `extends`, altrimenti quelli di `default:` o globali salvo `inherit`;
  - i nomi sono gli alias e quelli che gitlab-runner ricava dall'immagine, con le variabili espanse come fa il runner;
  - GitLab non ha controlli di salute, quindi il passo aspetta, come il suo runner, che le porte esposte dall'immagine rispondano (`wait: ports`).
- **Verifica:** su un Docker vero in un sandbox di Modal: un postgres di GitLab senza controllo di salute risponde in 1,8 secondi, i test aprono una sessione a db:5432, e fuori non si esce.
- **Stato:** risolto.
- **Note:** un file incluso è `include_not_read`, D-216.

#### D-241 C#: nessun osservatore eseguiva i test .NET
- **Tag:** lingua csharp · area passo dinamico · tipo completezza · origine finale · strumento dotnet
- **Descrizione:** finale, eShop: C# `no-observer`, «no observer runs this language's tests».
- **Spiegazione:** il passo dinamico non aveva un osservatore per C#. Dal confronto nel docstring di `scripts/dynamic/dotnet.py`, nessuno strumento esistente registra gli archi di chiamata.
- **Progetto e caso:** eShop (`913acea66708`) — finale, 16 novembre 2026.
- **Rimedio:** `15960a591` (16 novembre), `scripts/dynamic/dotnet.py` e `scripts/dynamic/dotnet_record/`, il registratore esatto di Daodan:
  - nella preparazione, dentro il container, il progetto si costruisce, e un riscrittore su Mono.Cecil 0.11.6 (MIT, fissato per sha256) aggiunge le sonde agli assembly del progetto con le righe del PDB;
  - il registratore (netstandard2.0) si carica con `DOTNET_STARTUP_HOOKS` in ogni processo di `dotnet test --no-build`;
  - un host Aspire, o un progetto che usa Aspire.Hosting.Testing, non gira: chiederebbe un motore di container dentro i test.
- **Verifica:**
  - dal commit, eShop: 4 progetti di test girano, 72 test passati, 2.385 siti registrati, 800 riferimenti uniti in 42 file; le risposte C# salgono dall'86,6 % all'87,3 %;
  - senza motore, un `dotnet` sul PATH che lascia un segno se chiamato prova che sull'host non gira niente (`tests/test_codebase_map_dynamic_dotnet.py`, `test_without_a_container_nothing_runs_and_the_cause_is_said`).
- **Stato:** risolto; un progetto di test che avvia i servizi con Aspire è un buco dichiarato (`tests_need_container_engine`).
- **Note:** D-114, D-242.

### Container, servizi e driver Modal

#### D-203 Il motore di container dell'utente usato anche se non risponde in locale
- **Tag:** lingua tutti · area container · tipo sicurezza · origine review · strumento —
- **Descrizione:** la revisione indipendente del perimetro di rete e di copia lo chiedeva.
- **Spiegazione:** il motore dell'utente si usava senza controllare come risponde.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02` (15 novembre), `scripts/container.py`: il motore dell'utente si usa solo se risponde su una pipe o un socket locale.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-064, D-204 e D-205.

#### D-204 Con un .git e Git che non risponde si copiavano i file ignorati
- **Tag:** lingua tutti · area container · tipo sicurezza · origine commit · strumento git
- **Descrizione:** la copia del progetto poteva portare nel container i file che Git ignora.
- **Spiegazione:** senza risposta di Git la copia non sapeva cosa è ignorato.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02`: la run è una lacuna.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-205 Ciò che torna dal container non controllato
- **Tag:** lingua tutti · area container · tipo sicurezza · origine review · strumento —
- **Descrizione:** l'uscita del container poteva scrivere fuori misura o fuori posto.
- **Spiegazione:** la revisione indipendente lo segnalava.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02`: ciò che torna lo scrive il codice di Daodan, con queste regole:
  - solo file e cartelle, nomi controllati;
  - somma delle dimensioni prima di scrivere, tetto di 1 GiB;
  - una cartella nuova, nomi della run riservati;
  - senza le funzioni di estrazione di tarfile e senza rifiutare versioni di Python.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-206 Link simbolici tracciati seguiti nella copia del container
- **Tag:** lingua tutti · area container · tipo correttezza · origine corsa su un progetto · strumento —
- **Descrizione:** python-semver non trovava i suoi moduli di test.
- **Spiegazione:** la copia seguiva i link simbolici.
- **Progetto e caso:** python-semver — 16 novembre 2026.
- **Rimedio:** `17babc624`, `scripts/container.py`:
  - i link tracciati entrano nella copia come link, mai seguiti;
  - quelli che puntano fuori dal progetto restano fuori, come `link_outside`.
- **Verifica:** su Modal python-semver trova i suoi moduli di test, 533 test; conferma: 1.046 siti osservati.
- **Stato:** risolto.
- **Note:** D-031, D-207.

#### D-207 I link lasciati fuori dalla copia non arrivavano ai buchi delle corse
- **Tag:** lingua tutti · area container · tipo completezza · origine commit · strumento —
- **Descrizione:** i `link_outside` della copia non comparivano nei risultati.
- **Spiegazione:** osservatori, analisi e pre-mappa non aggiungevano ai propri buchi quelli della copia.
- **Progetto e caso:** container — 16 novembre 2026.
- **Rimedio:** `756ebbcb3` (16 novembre): li aggiungono osservatori (Go, C/C++, Rust, JavaScript, Python), analisi (C/C++, C#, JVM, Python) e pre-mappa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-208.

#### D-208 JVM: i buchi della preparazione sovrascrivevano quelli del container
- **Tag:** lingua java, kotlin · area container · tipo completezza · origine commit · strumento —
- **Descrizione:** nella JVM si perdevano i buchi del container.
- **Spiegazione:** i buchi della preparazione sovrascrivevano quelli del container.
- **Progetto e caso:** analisi JVM — 16 novembre 2026.
- **Rimedio:** `756ebbcb3`, `scripts/indexers/jvm.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-209 Valgrind muore all'avvio nei sandbox di Modal (gVisor)
- **Tag:** lingua c, cpp, rust · area driver Modal · tipo completezza · origine fixtures · strumento Valgrind, Modal
- **Descrizione:**
  - `12775fee3`: «Valgrind non parte nei container di Modal (gVisor)»;
  - `a491415e6`: «Valgrind si ferma nel caricatore dinamico prima del codice Rust»;
  - finale, README: «Rust, C e C++ si osservano solo dove Valgrind parte».
- **Spiegazione:** sotto gVisor un fault sotto lo stack principale arriva come SEGV_ACCERR, e Valgrind non lo estende; nessuna opzione lo cambia. Docker, Podman e Kiri (runc) lo eseguono (`ef69774f9`).
- **Progetto e caso:** semver, tinyxml2, zlib e le fixture Rust e C/C++ — fixtures e finale, 16 novembre 2026.
- **Rimedio:** `8ef21896f` (16 novembre), `benchmarks/project-model/modal_pipeline.py` e `scripts/dynamic/callgrind.py`:
  - il driver usa i sandbox a macchina virtuale (experimental_options vm_runtime, Linux 7.3.4) per entrambe le fasi, quando l'esecuzione avvia Valgrind o ci sono servizi;
  - lì `valgrind true` passa a tutte le 48 dimensioni d'ambiente provate;
  - uno stack profondo dà 105 SEGV_MAPERR e 105 estensioni;
  - il cargo test della fixture gira sotto Callgrind.
- **Verifica:** conferma: semver 558 siti osservati, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- **Stato:** risolto.
- **Note:** D-175, D-227, D-230.

#### D-210 Bear sotto gVisor fallisce circa una build su dieci
- **Tag:** lingua c, cpp · area container · tipo completezza · origine commit · strumento Bear, Modal
- **Descrizione:** il database di compilazione di un build Make poteva mancare.
- **Spiegazione:** sotto gVisor un rapporto di Bear fallisce circa una build su dieci.
- **Progetto e caso:** build Make sotto Bear — 16 novembre 2026.
- **Rimedio:** `f829df4b0` (16 novembre): una build fallita ha un secondo passaggio che aggiunge al database.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-211 Il server visuale resettava la connessione su una POST rifiutata
- **Tag:** lingua tutti · area explorer · tipo correttezza · origine test · strumento —
- **Descrizione:** verificando su Modal l'albero di `eacfad80e`, un test del server visuale cadeva solo sotto carico, con la connessione chiusa su una POST rifiutata.
- **Spiegazione:** il server rifiutava prima di leggere il corpo e chiudeva con il corpo non letto; il kernel resettava la connessione, e il reset poteva cancellare il 403 prima che il client lo leggesse.
- **Progetto e caso:** suite su Modal — 16 novembre 2026.
- **Rimedio:** `426626fbe` (16 novembre), `scripts/visual.py`:
  - chiude a tappe (RFC 9112 §9.6): prima SHUT_WR;
  - poi legge e scarta ciò che il client sta ancora mandando, al massimo 5 secondi, e chiude;
  - il corpo non viene mai interpretato.
- **Verifica:** test con una POST da 16 MiB oltre il limite.
- **Stato:** risolto.
- **Note:** —

#### D-212 Servizi di Compose che il passo non avvia
- **Tag:** lingua tutti · area servizi · tipo completezza · origine spec · strumento Compose, GitLab CI
- **Descrizione:** spec, «Limiti»: sono lacune un'immagine che Compose costruisce, un comando con una variabile, uno script che cambia cartella, un bind mount fuori dal progetto, Compose in un job di GitLab.
- **Spiegazione:** quei casi non si leggono senza eseguire codice del progetto.
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** dichiarati: quei test falliscono, e la corsa lo dice.
- **Verifica:** —
- **Stato:** buco dichiarato (`compose_not_read` e lacune dei servizi).
- **Note:** D-201.

#### D-213 I passi del job della CI prima dei test non giravano
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento GitHub Actions
- **Descrizione:** i test partivano senza ciò che la CI fa prima di loro, come una migrazione che crea le tabelle accanto al database di servizio.
- **Spiegazione:** il passo dinamico avviava i servizi del job, ma non i passi `run:` del job prima di quello dei test.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/container.py` e `scripts/dynamic/__init__.py`:
  - in ogni job il passo di test è il primo `run:` che lancia un ingresso `tests`;
  - i passi prima sono fatti `ci_steps`, eseguiti in ordine nella preparazione con i servizi accanto, con le variabili del workflow, del job e del passo e `CI=true`, sotto `bash -e` o `sh -e`;
  - prima dell'esecuzione il proxy se ne va e il pod si stacca dalla rete, così i test vedono i servizi già migrati e nient'altro;
  - altre azioni, `if:` e `${{ }}` sono `ci_step_not_run`; un passo che fallisce è `ci_step_failed`, con le ultime righe.
- **Verifica:**
  - dal commit, su Modal e su un Docker vero in un sandbox a macchina virtuale: una migrazione scrive una tabella accanto a postgres, i test la leggono, fuori non si esce (`tests/test_codebase_map_dynamic_services.py`, `test_on_modal_the_ci_s_steps_run_beside_the_services_and_the_tests_find_what_they_wrote`);
  - giro `ci-steps`, tududi: i tre passi del job (installazione 36 s, lint 19 s, bootstrap e migrazioni 1 s) girano accanto a postgres:16-alpine prima dei test; rispetto alla conferma JavaScript va da 3.779 a 13.214 siti e TypeScript da 92 a 20.202, un salto che dal commit viene anche dai bundle in memoria e dalle CPU scalate, non solo dai passi;
  - giro `ci-steps`, fastapi: «Migrate DB» gira e fallisce sul `.env` che la copia non porta (D-240).
- **Stato:** risolto; i passi che non si possono eseguire sono un buco dichiarato (`ci_step_not_run`).
- **Note:** D-218.

#### D-214 Compose: i file del progetto montati nei servizi
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento Compose
- **Descrizione:** i file del progetto che Compose lega a un servizio non arrivavano al servizio.
- **Spiegazione:** il passo non portava nel servizio i bind mount che il file compose dichiara.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/premap/compose.py` e `scripts/dynamic/__init__.py`:
  - i file del progetto montati nei servizi vi sono copiati;
  - quelli fuori dal progetto sono `service_incomplete`;
  - gli script di shell che avviano Compose si leggono fino a tre livelli.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`: `test_a_service_has_the_project_s_files_its_bind_mounts_name_before_it_starts`, `test_a_shell_script_a_step_or_a_test_script_runs_is_read_for_docker_compose_as_its_caller_is`).
- **Stato:** risolto; un bind mount fuori dal progetto è un buco dichiarato (`service_incomplete`).
- **Note:** D-201, D-215.

#### D-215 Compose: `depends_on`
- **Tag:** lingua tutti · area servizi · tipo correttezza · origine commit · strumento Compose
- **Descrizione:** l'ordine di avvio dei servizi di Compose non era seguito.
- **Spiegazione:** il passo non aspettava i servizi da cui un altro dipende.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3`: `depends_on` è rispettato, con le condizioni avviato, sano e uscito a 0; un servizio la cui dipendenza fallisce non parte, e la sua causa la nomina.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`: `test_a_service_starts_after_those_it_depends_on_as_compose_s_condition_says`, `test_a_service_whose_dependency_fails_does_not_start_and_its_cause_names_it`).
- **Stato:** risolto.
- **Note:** D-214.

#### D-216 GitLab CI: i file che `.gitlab-ci.yml` include
- **Tag:** lingua tutti · area servizi · tipo completezza · origine spec · strumento GitLab CI
- **Descrizione:** i servizi dichiarati in un file incluso non partono.
- **Spiegazione:** il lettore non segue gli `include`; la spec lo lascia fra le cose da decidere.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** dichiarato con `23de469c4`: `include_not_read`.
- **Verifica:** solo test.
- **Stato:** aperto (test-services); oggi è il buco `include_not_read`.
- **Note:** D-202, D-217.

#### D-217 GitLab CI: `!reference`
- **Tag:** lingua tutti · area servizi · tipo completezza · origine review · strumento GitLab CI
- **Descrizione:** segnalato da team-lead.
- **Spiegazione:** da verificare: nessun commit lo descrive ancora.
- **Progetto e caso:** da verificare.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (test-services).
- **Note:** D-216.

#### D-218 Kiri non stacca un container dalla sua prima rete
- **Tag:** lingua tutti · area container · tipo completezza · origine review · strumento Kiri
- **Descrizione:** il sospetto era che Kiri non avesse `network connect`. Non è un difetto: test-services ha letto il sorgente di Kiri, il cui `ops.rs:54-58` serve `network connect` e `network disconnect`, e la via del pod funziona.
- **Spiegazione:**
  - Kiri 0.2.0 rifiuta solo di togliere un container dalla sua prima rete (`crates/kiri/src/daemon/engine.rs:2357`, citato in `scripts/container.py`, `leaves`);
  - il pod dei servizi deve lasciare la rete della preparazione prima dei test (D-213), e su Kiri non può.
- **Progetto e caso:** motore Kiri — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/container.py` (`leaves`):
  - una prova crea un container sulla rete e lo stacca;
  - se il motore rifiuta, i passi della CI accanto ai servizi sono `ci_step_not_run`, con la risposta del motore: «… cannot take the pod of the services off the preparation's network before the tests, so no step runs beside them».
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_an_engine_that_cannot_take_the_pod_off_its_network_runs_no_step_beside_the_services`).
- **Stato:** buco dichiarato (`ci_step_not_run`).
- **Note:** D-213, D-219.

#### D-219 Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL
- **Tag:** lingua tutti · area container · tipo correttezza · origine spec · strumento Kiri
- **Descrizione:** spec, «Da decidere»: «another Kiri engine is running on this machine».
- **Spiegazione:** anche in distribuzioni diverse i due motori condividono la rete della VM di WSL.
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (da decidere).
- **Note:** —

#### D-240 Il `.env` che il progetto traccia non arrivava nel container
- **Tag:** lingua python, cpp · area servizi · tipo completezza, sicurezza · origine ci-steps · strumento Compose, Docker
- **Descrizione:**
  - giro `ci-steps`, fastapi: «Migrate DB» gira e fallisce, e pytest e Playwright si fermano sulle stesse impostazioni mancanti, che stanno nel `.env` tracciato del template (dal commit `aea1c8c3b`);
  - otel-demo: lo stadio di currency chiede `ARG OPENTELEMETRY_CPP_VERSION` (`src/currency/Dockerfile:26`), che Compose prende da `.env:8` (`OPENTELEMETRY_CPP_VERSION=1.28.0`); senza, l'istruzione non si riproduce (D-135).
- **Spiegazione:** `scripts/source_files.py:73-74` (`FORBIDDEN_GLOBS`: `.env`, `.env.*`) e `copy_perimeter` (`scripts/container.py`) tengono fuori dalla copia ogni file che `is_forbidden` nomina, anche quando Git lo traccia.
- **Progetto e caso:** fastapi (`aabb90126964`) — giro `ci-steps`; otel-demo (`b825c7c25726`); 16 novembre 2026.
- **Rimedio:** `b1f14ac08` (16 novembre, test-services), `scripts/container.py`, `scripts/premap/compose.py`, `scripts/premap/renovate.py`, `scripts/dynamic/__init__.py`, secondo la decisione del proprietario («Env tracciato»):
  - i `.env*` che Git traccia entrano nella copia del progetto nel container, come nel checkout della CI; ogni altro file che Daodan non legge resta fuori come buco `file_withheld`, che nomina il file e la regola;
  - i valori si leggono solo in un container senza rete e sono mascherati come `[.env:NOME]` in log, uscite di testo, cause del registro e risultato;
  - il container della pre-mappa scrive un segnaposto al posto di ogni valore, così i fatti di Compose tengono `${NOME}` e `dotenv: {NOME: file}`, e il valore entra solo all'avvio del servizio.
- **Verifica:**
  - giro `dotenv` (`benchmarks/project-model/results/pipeline/2026-11-16-dotenv.json`): in fastapi db, mailpit e adminer partono e «Migrate DB» passa, e la password del template compare 0 volte nel risultato; in tududi i tre passi del job escono con 0 accanto a postgres (dal commit);
  - `tests/test_codebase_map_dynamic_services.py` (`test_the_copy_carries_the_env_files_git_tracks_and_names_each_file_it_withholds`, `test_each_value_of_a_tracked_env_file_is_masked_where_it_stands_as_a_whole`, `test_on_modal_a_tracked_env_file_s_value_reaches_the_service_and_nothing_the_run_keeps`).
- **Stato:** risolto; un file che Daodan non legge e Git non traccia resta il buco dichiarato `file_withheld`.
- **Note:** sblocca fastapi (D-213) e currency (D-135).

#### D-244 I test reali dei servizi si cancellavano a vicenda
- **Tag:** lingua tutti · area servizi · tipo correttezza · origine test · strumento —
- **Descrizione:** i test reali dei servizi, in parallelo, si cancellavano la cartella di lavoro a vicenda.
- **Spiegazione:** condividevano una cartella di lavoro.
- **Progetto e caso:** `tests/test_codebase_map_dynamic_services.py` — commit `aea1c8c3b`, 16 novembre 2026.
- **Rimedio:** `aea1c8c3b` (16 novembre): ognuno ha la sua cartella di lavoro.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-260 Il passo di test della CI senza le variabili che la CI gli dà
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento GitHub Actions
- **Descrizione:** i test partivano senza le variabili che il workflow, il job e il passo danno al passo dei test, e senza quelle sul comando che avvia il runner: fastapi lancia i test con `FASTAPI_ENV=development coverage run -m pytest tests/` (dal commit `b1f14ac08`).
- **Spiegazione:** il passo di test non era un fatto della pre-mappa: i fatti `ci_steps` tenevano solo i passi prima dei test (D-213).
- **Progetto e caso:** fastapi (`aabb90126964`) — commit `b1f14ac08`, 16 novembre 2026.
- **Rimedio:** `b1f14ac08` (16 novembre, test-services): il passo di test della CI è un fatto `ci_steps` con `env`, le variabili del workflow, del job, del passo e quelle sul comando che avvia il runner, anche negli script che esegue; un valore che la CI o la shell calcolano è un buco `ci_step_incomplete`.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_the_steps_a_job_runs_before_its_tests_are_facts_with_where_and_how_github_runs_them`, `test_an_observer_s_runs_get_the_steps_before_their_tests_and_a_gap_for_each_that_does_not_run`).
- **Stato:** risolto; un valore calcolato resta il buco dichiarato `ci_step_incomplete`.
- **Note:** D-213.

#### D-261 Un passo di test dentro `docker compose run`
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento Compose, GitHub Actions
- **Descrizione:** un job che lancia i suoi test dentro `docker compose run` li fa girare in un container che Compose costruisce (dal commit `b1f14ac08`).
- **Spiegazione:** il passo dinamico non avvia i container che Compose costruisce (D-212).
- **Progetto e caso:** passo dinamico — commit `b1f14ac08`, 16 novembre 2026.
- **Rimedio:** `b1f14ac08` (16 novembre, test-services): il passo di test e ogni passo prima di lui sono il buco `ci_step_not_run`.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_a_job_that_runs_its_tests_inside_docker_compose_says_its_test_step_and_each_step_before_it_not_run`).
- **Stato:** buco dichiarato (`ci_step_not_run`).
- **Note:** D-212, D-213.

#### D-262 apt dietro il proxy del container: l'archivio su HTTP in chiaro
- **Tag:** lingua tutti · area container · tipo completezza · origine commit · strumento apt
- **Descrizione:** il commit `b1f14ac08` fa inoltrare al proxy del container l'HTTP in chiaro per l'archivio apt dichiarato.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** container — commit `b1f14ac08`, 16 novembre 2026.
- **Rimedio:** `b1f14ac08` (16 novembre, test-services), `scripts/container.py`: il proxy inoltra HTTP in chiaro solo per GET e HEAD di `dists/` e `pool/` di un archivio apt dichiarato.
- **Verifica:** `tests/test_codebase_map_container.py` (`test_proxy_forwards_plain_http_to_an_apt_host_only_for_its_archive`, e su Modal `test_on_modal_apt_updates_and_downloads_from_debian_s_plain_http_archive_through_the_proxy`).
- **Stato:** risolto.
- **Note:** D-064, il perimetro di rete.

### Benchmark e documenti

#### D-220 Risposte attese: il workspace di javapoet e le soluzioni .NET di zlib
- **Tag:** lingua java, csharp · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** le risposte attese di javapoet e zlib erano sbagliate.
- **Spiegazione:** contavano un build incluso come membro (javapoet) e le soluzioni .NET di zlib in modo diverso dal lettore corretto (D-010, D-016).
- **Progetto e caso:** javapoet, zlib — 15 novembre 2026.
- **Rimedio:** `a04ab36e1`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-010, D-016.

#### D-221 Lo schema del banco senza BOM, POM genitore e versioni centrali
- **Tag:** lingua java, kotlin · area benchmark · tipo benchmark · origine commit · strumento Maven, Gradle
- **Descrizione:** le risposte attese non distinguevano BOM, platform() e POM genitore, e una versione centrale dava più voci.
- **Spiegazione:**
  - un BOM importato, un platform() e un POM genitore sono dipendenze con scope bom o parent, e un arco se sono un'unità del progetto;
  - una versione scritta lontano dal punto che nomina il pacchetto dà una voce sola: l'unità dal file che nomina il pacchetto, la versione e `declared_in` dal file che la scrive.
- **Progetto e caso:** dieci progetti del corpus — 15 novembre 2026.
- **Rimedio:** `1420247ad` (15 novembre): otto voci aggiunte, undici cambiate, undici archi.
- **Verifica:** dipendenze attese da 861 a 869.
- **Stato:** risolto.
- **Note:** D-021, D-026.

#### D-222 `test_catalog` rosso: ANAGRAFICA.md non era l'uscita del generatore
- **Tag:** lingua tutti · area documenti · tipo documentazione · origine test · strumento —
- **Descrizione:** `test_catalog` era rosso da `a633ebd72`.
- **Spiegazione:** dopo le versioni delle immagini senza variante (D-046) ANAGRAFICA.md non era stata rigenerata.
- **Progetto e caso:** benchmark project-model — 16 novembre 2026.
- **Rimedio:** `68a846a4a` (16 novembre): ANAGRAFICA.md torna a essere l'uscita del generatore.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-046.

#### D-223 Le risposte attese delle fixture Android senza i build-tools
- **Tag:** lingua java, kotlin · area benchmark · tipo benchmark · origine commit · strumento Gradle, Android SDK
- **Descrizione:** le risposte attese di jvm-android-app-lib e mix-poly-firebase non dichiaravano android-build-tools.
- **Spiegazione:** android-build-tools 34.0.0 è il valore che dà il modello di Gradle, il predefinito di AGP 8.7.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — 16 novembre 2026.
- **Rimedio:** `68a846a4a`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-044.

#### D-224 I test del registratore JVM saltati: l'immagine dei test senza JDK
- **Tag:** lingua java · area benchmark · tipo benchmark · origine commit · strumento Modal
- **Descrizione:** i test dell'agente JVM venivano saltati.
- **Spiegazione:** l'immagine dei test su Modal non aveva un JDK.
- **Progetto e caso:** `tests/modal_pytest.py` — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: l'immagine dei test ha un JDK (openjdk-17-jdk-headless).
- **Verifica:** i test del registratore girano sulle suite di Modal; l'agente è provato su JDK 8 e 17 (dal commit).
- **Stato:** risolto.
- **Note:** D-178.

#### D-225 Due fixture con `node --test test/`
- **Tag:** lingua javascript · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** due progetti di prova lanciavano `node --test test/`.
- **Spiegazione:** da Node 21 `node --test test/` non funziona.
- **Progetto e caso:** due fixture JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`: ora `node --test`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-226 Toolchain Maven contate sbagliate per il frammento di `declared_in`
- **Tag:** lingua java · area benchmark · tipo benchmark · origine java-versions · strumento Maven
- **Descrizione:** java-versions: le toolchain delle 11 fixture Maven e della mista contano come sbagliate.
- **Spiegazione:** il solo frammento di `declared_in` differisce: `pom.xml#properties.maven.compiler.source` contro `pom.xml#maven.compiler.source`, come nelle altre fixture Maven del corpus (README del benchmark).
- **Progetto e caso:** jvm-ver-* e le fixture Maven — java-versions, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-227 README del benchmark: Rust, C e C++ «solo dove Valgrind parte»
- **Tag:** lingua c, cpp, rust · area documenti · tipo documentazione · origine commit · strumento Valgrind
- **Descrizione:** il risultato del finale nel README dice ancora che Rust, C e C++ si osservano solo dove Valgrind parte, e che nei sandbox di Modal (gVisor) dipende dalla macchina.
- **Spiegazione:** è stato scritto prima di `8ef21896f`; la conferma li osserva nei sandbox a macchina virtuale.
- **Progetto e caso:** `benchmarks/project-model/README.md` — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-209.

#### D-228 Il rapporto dichiarava nulla la copertura a runtime
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** i riferimenti del metodo dicevano «Exercised at runtime: none» e «runtime: none unless supplied».
- **Spiegazione:** il rapporto non leggeva il risultato del passo dinamico.
- **Progetto e caso:** il metodo di codebase-map — 16 novembre 2026.
- **Rimedio:** `78c03d6e8` (16 novembre):
  - `snapshot.py runtime <run-dir>` (`pipeline.runtime`) dà per linguaggio siti, archi, buchi chiusi, file eseguiti e non, come è finita ogni corsa, e i buchi;
  - phase-7, entry-analyze, entry-team-analyze, mcp ed evidence, il ruolo semantic-interconnect-mapper e `docs/plugins/codebase-map.md` rimandano a quel comando.
- **Verifica:** tre test in `tests/test_codebase_map_dynamic.py`; solo test.
- **Stato:** risolto.
- **Note:** D-229, D-230.

#### D-229 Spec: il passo 2 «non esegue codice del progetto»
- **Tag:** lingua javascript, typescript, java, kotlin, c, cpp, csharp · area documenti · tipo documentazione, sicurezza · origine spec · strumento —
- **Descrizione:** la tabella dei passi della spec del passo dinamico diceva «No» per il passo 2.
- **Spiegazione:** il passo 2 esegue la build da cui l'indice nasce: Java e Kotlin, TypeScript e JavaScript, C#, C e C++.
- **Progetto e caso:** `docs/specs/2026-11-12-passo-dinamico.md` — 16 novembre 2026.
- **Rimedio:** `78c03d6e8`: «Sì, solo nel container».
- **Verifica:** —
- **Stato:** risolto.
- **Note:** —

#### D-230 Spec: Rust, C e C++ «non provati» su Modal
- **Tag:** lingua c, cpp, rust · area documenti · tipo documentazione · origine spec · strumento Modal
- **Descrizione:** lo stato della spec diceva provati con il registro vero «salvo Rust, C e C++».
- **Spiegazione:** è stato scritto prima di `8ef21896f`.
- **Progetto e caso:** `docs/specs/2026-11-12-passo-dinamico.md` — 16 novembre 2026.
- **Rimedio:** `78c03d6e8`: osservati nei sandbox a macchina virtuale, con i numeri della conferma.
- **Verifica:** conferma: semver 558, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- **Stato:** risolto.
- **Note:** D-209, D-227.

#### D-231 README, SKILL e riferimenti dicevano Jedi e «solo statica»
- **Tag:** lingua python · area documenti · tipo documentazione · origine commit · strumento Jedi
- **Descrizione:** documenti in ritardo sul codice.
- **Spiegazione:** non erano aggiornati dopo il passo dinamico e l'arrivo degli indici.
- **Progetto e caso:** README, SKILL, `references/snapshot.md` — 16 novembre 2026.
- **Rimedio:** `e617127c3` (16 novembre), insieme a riferimento, linguaggi e licenze: 16 linguaggi con 63 estensioni, ogni strumento con versione e licenza.
- **Verifica:** —
- **Stato:** risolto.
- **Note:** —

#### D-232 L'osservatore Python diceva che il passo non avvia servizi
- **Tag:** lingua python · area documenti · tipo documentazione · origine commit · strumento —
- **Descrizione:** il docstring, il dettaglio di `services_unreachable` e quello del test lo dicevano ancora.
- **Spiegazione:** scritti prima di D-182.
- **Progetto e caso:** `scripts/dynamic/python.py` — 16 novembre 2026.
- **Rimedio:** `0ca9f1650` (16 novembre).
- **Verifica:** —
- **Stato:** risolto.
- **Note:** D-182.

#### D-233 Due script del benchmark dell'inferenza mai eseguiti
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** `modal_scip.py` e `ts_compiler.py` seguono la nuova firma, ma «non sono stati eseguiti».
- **Spiegazione:** lo dice il commit.
- **Progetto e caso:** `benchmarks/inference-audit` — 16 novembre 2026.
- **Rimedio:** `137512c11` (16 novembre).
- **Verifica:** da verificare.
- **Stato:** aperto.
- **Note:** —

#### D-234 Un file dello snapshot senza dichiarazioni usciva dal progetto nel grafo
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** un file che lo snapshot legge in modo lessicale non era più del progetto nel grafo del benchmark.
- **Spiegazione:** il grafo cercava le dichiarazioni del file nell'inventario.
- **Progetto e caso:** `benchmarks/inference-audit` — 13 novembre 2026.
- **Rimedio:** `53e219638` (13 novembre), `benchmarks/inference-audit/scip_graph.py`: un file così è `value`, «file without declarations in the snapshot».
- **Verifica:** `test_scip_graph.py`; solo test.
- **Stato:** risolto.
- **Note:** —

#### D-235 Pre-mappa: dipendenze sotto la soglia
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine corpus della pre-mappa · strumento —
- **Descrizione:** misura del 15 novembre sui 122 progetti: dipendenze 682, soglia 716 non raggiunta.
- **Spiegazione:** le cause sono D-018–D-030.
- **Progetto e caso:** corpus della pre-mappa — 15 novembre 2026 (`22524b57b`).
- **Rimedio:** `de353d251`, `99112d0b9`.
- **Verifica:** riproduzione di `99112d0b9`: 785 dipendenze trovate.
- **Stato:** risolto.
- **Note:** D-019.

#### D-243 Il driver perdeva i buchi del passo dinamico
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine commit · strumento —
- **Descrizione:** nel risultato di un giro niente nominava i passi della CI.
- **Spiegazione:** `benchmarks/project-model/modal_pipeline.py` non teneva i buchi del passo dinamico, né il nome e il `declared_in` di ogni riga del registro.
- **Progetto e caso:** benchmark project-model — commit `aea1c8c3b`, 16 novembre 2026.
- **Rimedio:** `aea1c8c3b` (16 novembre), `benchmarks/project-model/modal_pipeline.py`: il driver li tiene.
- **Verifica:** giro `ci-steps`.
- **Stato:** risolto.
- **Note:** D-213.

#### D-251 I risultati di un giro non registrano il codice di Daodan su cui è girato
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine review · strumento Modal
- **Descrizione:** docs-writer, sul giro `ci-steps`: la quota di risposta dei fogli di stile è al 98,7 %, contro il 26,3 % della conferma, e sugli stessi due casi, tududi e fastapi, i buchi passano da 38.210 a 523; nulla nel risultato dice su quale codice di Daodan il giro è girato (riportato da team-lead il 16 novembre). Così nessun numero di un giro si lega a un commit.
- **Spiegazione:**
  - il driver (`benchmarks/project-model/modal_pipeline.py`, `main`, righe 502-534) scrive in `<giro>.json` solo i casi: nessun commit di Daodan, nessuno stato dell'albero di lavoro;
  - un caso registra le versioni degli strumenti (`steps.analyze.engines.<motore>.indexer.version`): quella del motore dei fogli di stile, un'impronta delle sue versioni (`scripts/indexers/css.py:164-166`), è `145560a4592a` per tududi e fastapi nella conferma, `45b68b725df0` e `2a5e4ddac1b8` in `ci-steps`, e non nomina un commit;
  - il codice dei giri lo dicono solo testi accanto al risultato (Convenzioni).
- **Progetto e caso:** giro `ci-steps` — review di docs-writer, 16 novembre 2026.
- **Rimedio:** —.
- **Verifica:** —.
- **Stato:** aperto.
- **Note:** i confronti fra giri di «Buchi trovati» ne dipendono; D-243, l'altro difetto del driver.

## Commit feat senza difetto

Commit feat dal 13 novembre che aggiungono una funzione e non correggono nulla. Dove il messaggio dice ciò che resta da fare, lo dice la riga.

| Commit | Data | Cosa aggiunge | Resta da fare, dal messaggio |
| --- | --- | --- | --- |
| `adb40ece9` | 15/11 | .NET sull'SDK di global.json; standard C/C++ ed edizione Rust nella pre-mappa | — (prova vera su Kiri: 15 tool su 15 nel container) |
| `4af3f2ccf` | 15/11 | Meson configura ogni file cross del progetto | — |
| `623e1e8d3` | 15/11 | gli analyzer nel container usano la preparazione della pre-mappa | le prove vere su Kiri (JVM, clang) |
| `bf28909d5` | 15/11 | Gradle, Maven, sbt, .NET e i file di progetto come fonti della pre-mappa | — |
| `8e6d119c9` | 15/11 | il ripristino dei progetti .NET | — |
| `776e21487` | 15/11 | il ripristino di Go e Cargo, con il Rust dichiarato | — |
| `3b71648bc` | 15/11 | il ripristino di uv, Poetry e pip | — |
| `623880897` | 15/11 | il ripristino di npm, pnpm e Yarn | — |
| `fb6b15185` | 15/11 | il ripristino di Gradle e Maven (`restore_failed`) | gli analyzer non lo chiamano ancora (poi `623e1e8d3`) |
| `1a32c8a97` | 15/11 | toolchain e dipendenze dichiarate prima di ogni strumento | — (su Kiri, fixture CMake da 1 a 10 unità su 10; zlib da 39 a 44 su 122; tinyxml2 da 1 a 4 su 7) |
| `e4c54c8a0` | 15/11 | le versioni dei linguaggi che mancavano nella pre-mappa | le fonti project_files e gradle non ancora registrate (poi `bf28909d5`) |
| `12b2a2f15` | 15/11 | l'esecutore dei comandi della pre-mappa nel container | non ancora collegato alla pipeline; la prova su Kiri non fatta |
| `b75f4a450` | 15/11 | le unità chieste a CMake, Meson e Bazel | non eseguite finché manca l'esecutore |
| `7122b0aeb` | 15/11 | le fonti CMake, Meson e Bazel | non ancora registrate (poi `b75f4a450`) |
| `0e5d39892` | 15/11 | i fogli di stile come analyzer, con il loro runner Node | — |
| `e5fb3e34c` | 15/11 | eventi e avanzamento della pipeline per un client MCP | — |
| `8abdf7cfe` | 15/11 | ogni analyzer si dichiara da solo | — |
| `2825b5dfc` | 15/11 | la pipeline da un punto solo, fino al grafo completo | — |
| `e5d554f08` | 15/11 | la pipeline a step con il bus degli eventi | — |
| `7e15d4ee9` | 15/11 | C e C++ dall'indice di scip-clang con le unità della pre-mappa | — |
| `57457cb8d` | 15/11 | Java e Kotlin dall'indice di scip-java, una build per cartella | — |
| `1c2e7bc95` | 15/11 | Python dall'indice di scip-python, con le esecuzioni della pre-mappa | il passaggio per posizione resta provato su Jedi |
| `2ba02dfa3` | 15/11 | le cartelle di ogni indicizzatore dalla pre-mappa | — (nessun risultato cambia) |
| `70daa02d4` | 15/11 | la pre-mappa subito dopo lo snapshot | — |
| `f8984bb9c` | 15/11 | le cartelle di un indicizzatore nella pre-mappa | — |
| `73bae40e0` | 14/11 | affected misurato come fonte dei moduli | — (59 unità esatte su 447, contro 200 del lettore di Daodan) |
| `402277c65` | 14/11 | l'anagrafica dei 122 progetti di prova | — |
| `cfa07cdd3` | 14/11 | Python dall'indice nello stage | il cambio di fonte aspetta la pre-mappa |
| `7c80454f2` | 14/11 | una run nel container senza resti, con due volumi a nome | Kotlin e klaxon da rifare con i volumi |
| `706a75a03` | 14/11 | la pre-mappa, con le fonti unite per unità | — |
| `a8d5733b1` | 14/11 | adattatori dei fogli di stile con percorsi relativi | — |
| `d96b919c2` | 14/11 | Go, TypeScript, JavaScript e Rust dall'indice, con la copertura | — |
| `2e1480e8c` | 14/11 | frontend e backend di tududi uniti dalle rotte | — (il componente più grande dal 50 % al 96,4 % dei nodi) |
| `9a45fe6b3` | 14/11 | la prova di 36 strumenti per la pre-mappa su 122 progetti | — |
| `2f8988d19` | 14/11 | il grafo degli stili confermato su sei progetti veri | — |
| `182fa73b4` | 14/11 | il registro esatto delle chiamate per Python | — |
| `11db4a661` | 14/11 | la lettura di C, C++ e dei fogli di stile | — |
| `88c21ea89` | 14/11 | il registro dei collegamenti | — |
| `2adc041f1` | 14/11 | l'operazione che esegue un comando in un container | — |
| `7f6d71803` | 14/11 | la parte comune del grafo e gli adapter nel plugin | — |
| `420987ab0` | 14/11 | le seconde fonti di JavaScript e TypeScript, e Jelly | — |
| `b7c06adef` | 14/11 | il grafo CSS dichiara i file non letti | — |
| `82bfa2579` | 14/11 | il grafo di C e C++ dall'indice | — |
| `ec872b5ea` | 14/11 | il grafo dei fogli di stile | — |
| `dea9be296` | 14/11 | le domande mirate al motore Kotlin | — |
| `21f3c34fc` | 14/11 | le seconde fonti di Go e Python | — |
| `4cb6514c8` | 13/11 | l'adapter Kotlin marca incerti gli overload fra moduli | — |
| `2bed601e8` | 13/11 | l'adapter Java dichiara le chiamate super e le costanti enum | — |
| `a954ced86` | 13/11 | le prove del grafo nel repository e l'adapter Python | — |
| `496ba3721` | 13/11 | la parte comune lascia decidere all'adapter | — |
| `2b220ea5d` | 13/11 | il grafo letto per intero dall'indice | — |
| `05c1c5de4` | 13/11 | la misura dell'indice SCIP contro i motori | — |
| `1bcee848b` | 13/11 | la verifica dei motori con etichette | — |
