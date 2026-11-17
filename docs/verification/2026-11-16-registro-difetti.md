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
- Fino a `cbc219663` nessun risultato registrava il codice di Daodan su cui il giro era girato (D-251); da quel commit ogni giro scrive `code` (commit, albero caricato su Modal, percorsi diversi). Per i giri già registrati: il codice del `finale` lo dice il README del benchmark (`benchmarks/project-model/README.md:174`), quello di `java-versions` il commit `347bc1403`, quello dei due giri JVM chi li ha fatti; degli altri giri, nessun testo.
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
- La regola invalicabile di `AGENTS.md` (`2753088a3`, poi `ae7fd8270`): il codice del progetto analizzato gira solo nel container di Daodan, mai sull'host, e ogni strumento che Daodan lancia sull'host ha un test con un file del progetto che, se eseguito, lascia un segno. Le schede del codice del progetto sull'host: D-161 (Tailwind), D-239 (rust-analyzer), D-245 e D-250 (Git), D-248 e D-253 (l'ambiente Python), D-256 (i formattatori), D-257 (Go), D-258 (Vue e Svelte), D-263 (i programmi nella cartella del progetto), D-264 (la sonda della memoria), D-276 (l'avvio del plugin), D-281 e D-285 (lo store che arriva con il progetto), D-282 (i programmi per nome nudo), D-286 (i file derivati di uno store portato).
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

- `tutti` (83): D-001, D-004, D-005, D-018, D-019, D-022, D-023, D-024, D-031, D-032, D-033, D-034, D-035, D-036, D-037, D-038, D-039, D-062, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-081, D-082, D-115, D-149, D-167, D-168, D-172, D-182, D-196, D-201, D-202, D-203, D-204, D-205, D-206, D-207, D-211, D-212, D-213, D-214, D-215, D-216, D-217, D-218, D-219, D-222, D-228, D-233, D-234, D-235, D-243, D-244, D-245, D-250, D-251, D-260, D-261, D-262, D-263, D-264, D-269, D-274, D-275, D-279, D-280, D-281, D-282, D-283, D-285, D-286, D-287, D-295, D-296, D-297, D-298, D-299, D-300, D-303
- `java` (48): D-003, D-016, D-025, D-026, D-027, D-044, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-099, D-100, D-101, D-102, D-103, D-104, D-105, D-106, D-108, D-109, D-111, D-112, D-178, D-179, D-181, D-208, D-220, D-221, D-223, D-224, D-226, D-229, D-265, D-284, D-293, D-294
- `c` (37): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-130, D-131, D-132, D-133, D-134, D-136, D-137, D-142, D-177, D-209, D-210, D-227, D-229, D-230, D-236, D-255, D-259, D-265, D-266, D-267, D-268, D-271, D-277
- `cpp` (37): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-130, D-131, D-132, D-133, D-135, D-137, D-177, D-209, D-210, D-227, D-229, D-230, D-236, D-240, D-255, D-259, D-265, D-266, D-268, D-271, D-272, D-277, D-278
- `kotlin` (38): D-016, D-027, D-044, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-089, D-091, D-092, D-093, D-094, D-095, D-096, D-097, D-098, D-103, D-105, D-106, D-107, D-108, D-109, D-110, D-166, D-180, D-208, D-221, D-223, D-229, D-284, D-293, D-294, D-302
- `python` (35): D-006, D-007, D-028, D-042, D-047, D-048, D-049, D-052, D-059, D-074, D-075, D-084, D-085, D-086, D-087, D-088, D-169, D-183, D-184, D-188, D-197, D-199, D-200, D-231, D-232, D-240, D-246, D-247, D-248, D-252, D-253, D-254, D-256, D-276, D-301
- `javascript` (34): D-013, D-017, D-021, D-046, D-049, D-051, D-053, D-056, D-059, D-072, D-147, D-148, D-156, D-158, D-170, D-171, D-185, D-186, D-187, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-198, D-225, D-229, D-256, D-265, D-270, D-291, D-292
- `typescript` (25): D-008, D-009, D-029, D-072, D-073, D-129, D-145, D-146, D-147, D-150, D-151, D-152, D-156, D-157, D-160, D-170, D-194, D-197, D-198, D-229, D-256, D-265, D-290, D-291, D-292
- `rust` (19): D-014, D-021, D-030, D-040, D-041, D-078, D-143, D-144, D-173, D-175, D-176, D-209, D-227, D-230, D-237, D-238, D-239, D-256, D-265
- `csharp` (19): D-010, D-021, D-049, D-113, D-114, D-116, D-117, D-118, D-119, D-120, D-165, D-198, D-220, D-229, D-241, D-242, D-249, D-294, D-302
- `go` (16): D-002, D-020, D-045, D-078, D-079, D-138, D-139, D-140, D-141, D-142, D-173, D-174, D-256, D-257, D-265, D-273
- `svelte` (6): D-080, D-153, D-156, D-159, D-258, D-288
- `vue` (8): D-080, D-154, D-155, D-159, D-258, D-289, D-290, D-291
- `css` (4): D-161, D-162, D-163, D-164
- `scala` (4): D-011, D-092, D-293, D-294
- `dart` (1): D-015
- `elixir` (1): D-012
- `php` (1): D-015
- `ruby` (1): D-059
- `swift` (1): D-030

### Area

- `analizzatore` (134): D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-072, D-073, D-074, D-075, D-076, D-077, D-078, D-079, D-080, D-081, D-082, D-083, D-084, D-085, D-086, D-087, D-088, D-089, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-097, D-098, D-099, D-100, D-101, D-102, D-103, D-104, D-105, D-106, D-107, D-108, D-109, D-110, D-111, D-112, D-113, D-114, D-115, D-116, D-117, D-118, D-119, D-120, D-121, D-122, D-123, D-124, D-125, D-126, D-127, D-128, D-129, D-130, D-131, D-132, D-133, D-134, D-135, D-136, D-137, D-138, D-139, D-140, D-141, D-142, D-143, D-144, D-145, D-146, D-147, D-148, D-149, D-150, D-151, D-152, D-153, D-154, D-155, D-156, D-157, D-158, D-159, D-160, D-161, D-162, D-163, D-164, D-236, D-237, D-238, D-239, D-242, D-246, D-247, D-248, D-249, D-253, D-255, D-257, D-258, D-259, D-266, D-267, D-268, D-271, D-272, D-273, D-277, D-278, D-288, D-289, D-290, D-294, D-295, D-296, D-297, D-298, D-299, D-300, D-301, D-303
- `pre-mappa` (40): D-001, D-002, D-003, D-004, D-005, D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-015, D-016, D-017, D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-029, D-030, D-043, D-046, D-055, D-056, D-057, D-058, D-060, D-061, D-062, D-284
- `passo dinamico` (37): D-167, D-168, D-169, D-170, D-171, D-172, D-173, D-174, D-175, D-176, D-177, D-178, D-179, D-180, D-181, D-183, D-184, D-185, D-186, D-187, D-188, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-196, D-197, D-198, D-199, D-200, D-241, D-270, D-274, D-292
- `host` (16): D-036, D-038, D-039, D-040, D-041, D-042, D-254, D-256, D-263, D-264, D-269, D-276, D-281, D-282, D-285, D-286
- `servizi` (14): D-182, D-201, D-202, D-212, D-213, D-214, D-215, D-216, D-217, D-240, D-244, D-260, D-261, D-275
- `container` (15): D-064, D-203, D-204, D-205, D-206, D-207, D-208, D-210, D-218, D-219, D-262, D-279, D-283, D-291, D-293
- `benchmark` (13): D-220, D-221, D-223, D-224, D-225, D-226, D-228, D-233, D-234, D-235, D-243, D-251, D-287
- `preparazione` (11): D-044, D-045, D-047, D-048, D-049, D-050, D-051, D-052, D-053, D-054, D-063
- `snapshot` (11): D-031, D-032, D-033, D-034, D-035, D-059, D-245, D-250, D-252, D-265, D-302
- `documenti` (6): D-222, D-227, D-229, D-230, D-231, D-232
- `parser` (3): D-037, D-165, D-166
- `driver Modal` (1): D-209
- `explorer` (1): D-211
- `processo` (1): D-280

### Tipo

- `completezza` (163): D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-017, D-021, D-029, D-033, D-035, D-043, D-044, D-046, D-047, D-048, D-049, D-050, D-052, D-053, D-054, D-055, D-059, D-061, D-062, D-066, D-068, D-069, D-072, D-073, D-074, D-075, D-076, D-078, D-082, D-085, D-088, D-089, D-091, D-092, D-093, D-094, D-096, D-098, D-099, D-100, D-102, D-103, D-104, D-107, D-108, D-109, D-111, D-112, D-114, D-116, D-117, D-118, D-119, D-125, D-126, D-127, D-130, D-131, D-132, D-133, D-134, D-135, D-136, D-137, D-138, D-139, D-140, D-141, D-142, D-143, D-144, D-147, D-148, D-149, D-150, D-151, D-152, D-155, D-156, D-157, D-158, D-159, D-160, D-162, D-164, D-165, D-166, D-169, D-170, D-171, D-172, D-173, D-176, D-180, D-181, D-182, D-185, D-186, D-190, D-191, D-193, D-194, D-195, D-196, D-197, D-198, D-199, D-200, D-201, D-202, D-207, D-208, D-209, D-210, D-212, D-213, D-214, D-216, D-218, D-236, D-237, D-240, D-241, D-247, D-249, D-252, D-260, D-261, D-262, D-265, D-267, D-270, D-271, D-272, D-273, D-274, D-275, D-277, D-278, D-279, D-284, D-289, D-290, D-291, D-292, D-293, D-294, D-295, D-296, D-297, D-298, D-299, D-300, D-301
- `correttezza` (90): D-001, D-002, D-003, D-004, D-005, D-015, D-016, D-018, D-019, D-020, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-030, D-031, D-036, D-037, D-038, D-039, D-045, D-051, D-056, D-057, D-058, D-060, D-065, D-067, D-070, D-071, D-077, D-079, D-080, D-081, D-083, D-084, D-086, D-087, D-090, D-095, D-097, D-101, D-105, D-106, D-110, D-113, D-115, D-120, D-121, D-122, D-124, D-128, D-129, D-145, D-146, D-153, D-154, D-163, D-167, D-168, D-174, D-175, D-177, D-178, D-179, D-183, D-184, D-188, D-192, D-206, D-211, D-215, D-217, D-219, D-238, D-242, D-244, D-246, D-254, D-255, D-259, D-266, D-268, D-269, D-280, D-288, D-303
- `sicurezza` (29): D-032, D-034, D-040, D-041, D-042, D-063, D-064, D-161, D-203, D-204, D-205, D-229, D-239, D-240, D-245, D-248, D-250, D-253, D-256, D-257, D-258, D-263, D-264, D-276, D-281, D-282, D-283, D-285, D-286
- `benchmark` (13): D-220, D-221, D-223, D-224, D-225, D-226, D-228, D-233, D-234, D-235, D-243, D-251, D-287
- `documentazione` (6): D-222, D-227, D-229, D-230, D-231, D-232
- `prestazioni` (4): D-123, D-187, D-189, D-302

### Origine

- `commit` (127): D-032, D-033, D-034, D-035, D-037, D-044, D-045, D-046, D-047, D-048, D-049, D-050, D-051, D-052, D-053, D-054, D-055, D-060, D-061, D-062, D-063, D-090, D-091, D-092, D-093, D-094, D-095, D-096, D-100, D-101, D-121, D-122, D-123, D-124, D-125, D-127, D-128, D-129, D-130, D-131, D-134, D-138, D-139, D-145, D-146, D-147, D-148, D-149, D-150, D-151, D-152, D-153, D-154, D-155, D-157, D-161, D-165, D-166, D-167, D-168, D-170, D-171, D-172, D-173, D-174, D-175, D-177, D-180, D-184, D-185, D-186, D-189, D-190, D-191, D-192, D-193, D-194, D-195, D-201, D-202, D-204, D-207, D-208, D-210, D-213, D-214, D-215, D-220, D-221, D-223, D-224, D-225, D-227, D-228, D-231, D-232, D-233, D-234, D-238, D-242, D-243, D-246, D-247, D-248, D-252, D-253, D-259, D-260, D-261, D-262, D-266, D-267, D-268, D-269, D-270, D-273, D-274, D-275, D-277, D-278, D-279, D-280, D-283, D-284, D-285, D-287, D-293
- `finale` (32): D-056, D-059, D-088, D-097, D-098, D-105, D-106, D-108, D-111, D-112, D-114, D-126, D-132, D-133, D-135, D-137, D-140, D-141, D-142, D-143, D-144, D-156, D-159, D-160, D-162, D-164, D-183, D-188, D-197, D-198, D-241, D-265
- `corpus della pre-mappa` (31): D-001, D-002, D-003, D-004, D-005, D-006, D-007, D-008, D-009, D-010, D-011, D-012, D-013, D-014, D-015, D-016, D-017, D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026, D-027, D-028, D-029, D-030, D-235
- `review` (31): D-064, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-072, D-073, D-074, D-075, D-076, D-077, D-078, D-079, D-080, D-081, D-082, D-203, D-205, D-217, D-218, D-251, D-254, D-256, D-257, D-258, D-263, D-264, D-286
- `prova su Modal` (23): D-089, D-102, D-103, D-104, D-115, D-116, D-117, D-118, D-119, D-120, D-169, D-179, D-236, D-237, D-239, D-249, D-255, D-271, D-272, D-276, D-281, D-282, D-292
- `prova sull'host` (10): D-036, D-038, D-039, D-040, D-041, D-042, D-084, D-086, D-245, D-250
- `spec` (7): D-199, D-200, D-212, D-216, D-219, D-229, D-230
- `conferma` (5): D-057, D-058, D-136, D-158, D-187
- `corsa su un progetto` (9): D-031, D-043, D-085, D-087, D-206, D-288, D-289, D-290, D-291
- `test` (4): D-083, D-211, D-222, D-244
- `fixtures` (3): D-176, D-196, D-209
- `real-3` (3): D-099, D-178, D-182
- `giro-2` (2): D-113, D-163
- `java-versions` (2): D-181, D-226
- `jvm-otel-android` (2): D-107, D-109
- `ci-steps` (1): D-240
- `jvm-kotlinconf` (1): D-110
- `benchmark` (10): D-294, D-295, D-296, D-297, D-298, D-299, D-300, D-301, D-302, D-303

### Strumento

- `Gradle` (30): D-016, D-027, D-044, D-049, D-050, D-054, D-055, D-058, D-063, D-064, D-089, D-090, D-094, D-095, D-097, D-098, D-101, D-103, D-104, D-105, D-106, D-107, D-108, D-109, D-110, D-112, D-180, D-221, D-223, D-293
- `Maven` (19): D-003, D-025, D-026, D-049, D-054, D-063, D-064, D-089, D-090, D-091, D-095, D-100, D-102, D-111, D-112, D-221, D-226, D-284, D-293
- `npm` (15): D-013, D-017, D-049, D-053, D-056, D-072, D-084, D-185, D-186, D-191, D-198, D-201, D-258, D-263, D-269
- `uv` (12): D-042, D-047, D-049, D-184, D-188, D-246, D-248, D-252, D-253, D-254, D-269, D-276
- `scip-java` (11): D-089, D-096, D-098, D-099, D-100, D-101, D-103, D-105, D-108, D-110, D-111
- `scip-clang` (10): D-123, D-131, D-132, D-236, D-255, D-266, D-271, D-272, D-277, D-278
- `CMake` (9): D-060, D-061, D-076, D-122, D-124, D-125, D-131, D-132, D-135
- `Docker` (8): D-046, D-107, D-135, D-140, D-141, D-240, D-277, D-279
- `git` (8): D-048, D-126, D-197, D-204, D-245, D-250, D-257, D-280
- `GitHub Actions` (8): D-056, D-182, D-201, D-213, D-260, D-261, D-274, D-275
- `scip-python` (7): D-084, D-086, D-088, D-246, D-247, D-248, D-269
- `scip-typescript` (9): D-146, D-147, D-148, D-152, D-156, D-157, D-160, D-290, D-291
- `Cargo` (6): D-014, D-021, D-030, D-041, D-175, D-239
- `Compose` (6): D-201, D-212, D-214, D-215, D-240, D-261
- `scip-dotnet` (6): D-113, D-114, D-116, D-118, D-119, D-249
- `tree-sitter` (6): D-034, D-035, D-036, D-037, D-117, D-265
- `GitLab CI` (5): D-202, D-212, D-216, D-217, D-275
- `Modal` (16): D-209, D-210, D-224, D-230, D-251, D-287, D-294, D-295, D-296, D-297, D-298, D-299, D-300, D-301, D-302, D-303
- `Pyright` (5): D-074, D-088, D-247, D-248, D-269
- `rust-analyzer` (5): D-041, D-143, D-144, D-237, D-239
- `Conan` (4): D-029, D-061, D-125, D-177
- `javac` (4): D-100, D-101, D-102, D-104
- `Make` (4): D-043, D-060, D-133, D-267
- `pnpm` (4): D-021, D-049, D-051, D-072
- `Roslyn` (4): D-113, D-115, D-116, D-249
- `scip-go` (4): D-139, D-140, D-141, D-142
- `Yarn` (4): D-049, D-051, D-072, D-157
- `Android SDK` (3): D-044, D-108, D-223
- `Bazel` (3): D-029, D-060, D-092
- `Bear` (3): D-133, D-210, D-267
- `Jest` (3): D-185, D-187, D-270
- `Kiri` (3): D-043, D-218, D-219
- `MSBuild` (3): D-076, D-113, D-120
- `rustup` (3): D-040, D-041, D-239
- `Valgrind` (3): D-176, D-209, D-227
- `BuildKit` (2): D-135, D-279
- `Bun` (2): D-056, D-195
- `Deno` (2): D-008, D-029
- `dotnet` (3): D-113, D-198, D-241
- `go` (2): D-257, D-273
- `NuGet` (2): D-021, D-049
- `pip` (2): D-049, D-188
- `protoc` (2): D-107, D-112
- `pytest` (2): D-169, D-183
- `Renovate` (2): D-046, D-217
- `rustc` (2): D-041, D-175
- `sbt` (3): D-011, D-092, D-293
- `Tailwind` (2): D-161, D-162
- `tsc` (2): D-072, D-115
- `Turborepo` (2): D-190, D-191
- `vcpkg` (2): D-125, D-177
- `Angular` (1): D-194
- `apt` (1): D-262
- `autotools` (1): D-134
- `biome` (1): D-256
- `black` (1): D-256
- `Claude Code` (1): D-276
- `Composer` (1): D-015
- `Corepack` (1): D-051
- `docker` (1): D-263
- `Error Prone` (1): D-100
- `GCC` (1): D-255
- `gcc` (1): D-257
- `gofmt` (1): D-256
- `Google Services` (1): D-109
- `grep` (1): D-282
- `Helm` (1): D-029
- `Jedi` (1): D-231
- `Launchpad` (1): D-176
- `Meson` (1): D-060
- `Mix` (1): D-012
- `Node` (2): D-269, D-292
- `pip-compile` (1): D-028
- `Playwright` (3): D-197, D-198, D-292
- `podman` (1): D-263
- `prettier` (1): D-256
- `pub` (1): D-015
- `python` (1): D-264
- `ripgrep` (1): D-282
- `ruff` (1): D-256
- `rustfmt` (1): D-256
- `SvelteKit` (1): D-156
- `SwiftPM` (1): D-030
- `taskkill` (1): D-282
- `Terraform` (1): D-029
- `tox` (1): D-183
- `typescript-language-server` (1): D-258
- `Vitest` (1): D-194
- `wsl` (1): D-263
- `WSL` (1): D-282
- `npx` (1): D-288
- `svelte-kit` (1): D-288
- `@vue/language-core` (2): D-289, D-290

## Indice

303 schede: 242 risolte, 17 aperte, 44 buchi dichiarati.

### Pre-mappa, snapshot e preparazione

77 schede: 71 risolto, 0 aperto, 6 buco dichiarato.

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
| D-256 | Il riscrittore dei commenti eseguiva sull'host i formattatori sui file del progetto | riscrittore dei commenti | risolto | `5dcb466fe` | python, javascript, typescript, rust, go · host · sicurezza · review · prettier, biome, ruff, black, rustfmt, gofmt |
| D-263 | Su Windows un programma si cercava anche nella cartella del progetto | host Windows | risolto | `5dcb466fe` | tutti · host · sicurezza · review · docker, podman, npm, wsl |
| D-264 | La sonda della memoria importava i moduli della cartella del progetto | sonda della memoria | risolto | `5dcb466fe` | tutti · host · sicurezza · review · python |
| D-265 | Un file con un errore di sintassi si perdeva intero | il corpus | risolto | `ba8a1920f` | go, rust, java, javascript, typescript, c, cpp · snapshot · completezza · finale · tree-sitter |
| D-276 | Le righe che avviano il plugin eseguivano sull'host il `.venv` del progetto | avvio del plugin | risolto su Linux | `624561af1`, `1dc2d6b9b` | python · host · sicurezza · prova su Modal · uv, Claude Code |
| D-281 | Uno store che arriva con il progetto sceglieva il processo da terminare e la cartella da leggere | lo store nel progetto | risolto su Linux | `398adf80e` | tutti · host · sicurezza · prova su Modal |
| D-282 | Sull'host taskkill, wsl.exe, rg e grep si avviavano per nome nudo | gli strumenti dell'host | risolto su Linux | `fd76f2d7d` | tutti · host · sicurezza · prova su Modal · taskkill, WSL, ripgrep, grep |
| D-284 | `kotlin.compiler.jvmTarget` di un pom non era una toolchain | jvm-mixed-java-kotlin | risolto | `a6af77108` | java, kotlin · pre-mappa · completezza · commit · Maven |
| D-285 | L'hook, refresh, diff e carry seguivano ciò che uno store portato dal progetto nomina | lo store nel progetto | risolto su Linux | `76214fa0f` | tutti · host · sicurezza · commit |
| D-286 | Uno store portato dal progetto può riempire prima i file derivati | lo store nel progetto | risolto su Linux con git | `6ab37afd9` | tutti · host · sicurezza · review |

### Analizzatori

138 schede: 96 risolto, 15 aperto, 27 buco dichiarato.

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
| D-107 | otel-demo fraud-detection: protos che solo il Dockerfile copia | otel-demo (`b825c7c25726`) | buco dichiarato (`build_not_indexed`, con la causa nel motivo) | `89d6ea082` | kotlin · analizzatore · completezza · jvm-otel-android · Gradle, Docker, protoc |
| D-108 | Android: classpath dei test unitari non risolti, nessun compito Android | jvm-android-app-lib, mix-poly-firebase | aperto (dynamic-jvm-2) | `39805f5e7` | java, kotlin · analizzatore · completezza · finale · scip-java, Gradle, Android SDK |
| D-109 | Android: build fermo su `google-services.json` mancante | jvm-android-app-lib, mix-poly-firebase | buco dichiarato (`build_input_missing`) | `39805f5e7` | java, kotlin · analizzatore · completezza · jvm-otel-android · Gradle, Google Services |
| D-110 | kotlinconf: «Task with name 'compileKotlinJvm' not found in project ':app:adminApp'» | kotlinconf (`146e891c150c`) | risolto | `a13d55787` | kotlin · analizzatore · correttezza · jvm-kotlinconf · scip-java, Gradle |
| D-111 | jhipster: 14 file Java con il documento senza occorrenze | jhipster-sample (`6b000b5d23a3`) | risolto | `1c68cbde4`, `f1124a748` | java · analizzatore · completezza · finale · scip-java, Maven |
| D-112 | Un file Java senza documento in due fixture: nessun javac del build lo compila | jvm-maven-multi-bom-profile, jvm-protobuf-generated | buco dichiarato (il motivo di `missing`) | `f1124a748` | java · analizzatore · completezza · finale · Maven, Gradle, protoc |
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
| D-135 | otel-demo currency: il build dichiarato solo nel Dockerfile | otel-demo (`b825c7c25726`) | risolto | `841cfe14f`, `f024ba3a3` | cpp · analizzatore · completezza · finale · Docker, BuildKit, CMake |
| D-136 | C: 5.147 buchi `no-document` | zlib (`51b7f2abdade`) | buco dichiarato (`no compile command`) | `60e3590b3`, `22dca6da8` | c · analizzatore · completezza · conferma |
| D-137 | File C e C++ fuori dalla configurazione predefinita | sys-cmake-presets, tinyxml2 (`9148bdf719e9`) | buco dichiarato (`no compile command | `2bc7c7459` | c, cpp · analizzatore · completezza · finale |
| D-138 | Go: i builtin erano buchi | indicizzatore Go | risolto | `a633ebd72` | go · analizzatore · completezza · commit |
| D-139 | Go: file esclusi dai vincoli di build senza indice | indicizzatore Go | risolto | `a633ebd72` | go · analizzatore · completezza · commit · scip-go |
| D-140 | Go: un file senza go.mod non diceva perché | robot-shop (`55292e2199f2`) | risolto | `d4e6d9046` | go · analizzatore · completezza · finale · scip-go, Docker |
| D-141 | robot-shop dispatch: il modulo Go dichiarato solo nel Dockerfile | robot-shop (`55292e2199f2`) | buco dichiarato (`restore_failed` a `dispatch/Dockerfile:7`) | `f024ba3a3`, `f04dab9d5` | go · analizzatore · completezza · finale · scip-go, Docker |
| D-142 | Un file cgo fuori dall'indice Go | sys-go-cgo | buco dichiarato («a cgo file») | — | c, go · analizzatore · completezza · finale · scip-go |
| D-143 | Rust: file senza documento | hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) | risolto | `1c68cbde4`, `a3801beed` | rust · analizzatore · completezza · finale · rust-analyzer |
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
| D-157 | TypeScript: i tipi dei pacchetti sotto Yarn Plug'n'Play | TypeScript nel container | risolto | `18248f8d1` | typescript · analizzatore · completezza · commit · Yarn, scip-typescript |
| D-158 | JavaScript: riceventi non tipizzati | kotlinconf e il corpus JavaScript | buco dichiarato («a member of a value of type any») | `3595d571b` | javascript · analizzatore · completezza · conferma |
| D-159 | Template di Vue e Svelte non letti | hoppscotch, js-vue-pnpm, js-sveltekit | risolto | `64edfb930`, `b9aeca1fb` | vue, svelte · analizzatore · completezza · finale |
| D-160 | TypeScript: un file senza documento | hoppscotch, memos (`509e41bd1a1b`) | risolto | `a57333c3b` | typescript · analizzatore · completezza · finale · scip-typescript |
| D-161 | Tailwind caricato sull'host con la configurazione del progetto | analyzer dei fogli di stile | risolto | `3595d571b` | css · analizzatore · sicurezza · commit · Tailwind |
| D-162 | Fogli di stile: buchi `no-rule` | il corpus | aperto (ts-container-2) | `efac75599`, `aca4fd008`, `05135d74e` | css · analizzatore · completezza · finale · Tailwind |
| D-163 | hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto | hoppscotch | risolto | `efac75599` | css · analizzatore · correttezza · giro-2 |
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
| D-254 | L'uv dell'host non era fissato | fastapi (`aabb90126964`) | risolto da `5e3757031` e `2057bbafc` | `5e3757031`, `2057bbafc` | python · host · correttezza · review · uv |
| D-255 | scip-clang leggeva i database di GCC con gli header builtin di GCC | otel-demo currency (`b825c7c25726`), riprodotto da android-sdk | risolto da `125ab9ebd` nella via principale e da `841cfe14f` in quella degli stadi del Dockerfile | `125ab9ebd` | c, cpp · analizzatore · correttezza · prova su Modal · scip-clang, GCC |
| D-257 | L'analizzatore Go eseguiva sull'host `go mod download` e il compilatore C | analizzatore Go | risolto | `c13d51732` | go · analizzatore · sicurezza · review · go, git, gcc |
| D-258 | Vue e Svelte eseguivano sull'host l'installazione npm e il TypeScript del progetto | analizzatore di Vue e Svelte | risolto | `b9aeca1fb`, `590466b5d` | vue, svelte · analizzatore · sicurezza · review · npm, typescript-language-server |
| D-259 | Un header `.h` di C++ letto come C | otel-demo (`b825c7c25726`) | risolto | `bdfd7797b` | c, cpp · analizzatore · correttezza · commit |
| D-266 | Le variabili locali di unità di traduzione diverse condividevano una chiave | tinyxml2 (`9148bdf719e9`) | risolto | `ba8a1920f` | c, cpp · analizzatore · correttezza · commit · scip-clang |
| D-267 | zlib: il configure scritto a mano non girava prima di make | zlib (`51b7f2abdade`) | risolto | `60e3590b3` | c · analizzatore · completezza · commit · Make, Bear |
| D-268 | Un linguaggio che nessun build compila era `failed` | zlib (`51b7f2abdade`) | risolto | `60e3590b3` | c, cpp · analizzatore · correttezza · commit |
| D-271 | C e C++: buchi senza occorrenza senza la loro causa | zlib (`51b7f2abdade`), tinyxml2 (`9148bdf719e9`) | risolto | `5cc88ec62` | c, cpp · analizzatore · completezza · prova su Modal · scip-clang |
| D-272 | scip-clang non scrive occorrenze per le funzioni `extern "C"` in C++ | tinyxml2 (`9148bdf719e9`), otel-demo currency (`b825c7c25726`) | aperto (strumento esterno | — | cpp · analizzatore · completezza · prova su Modal · scip-clang |
| D-273 | Un workspace Go: `go mod download` fallisce nei moduli che richiedono un membro non pubblicato | sys-go-workspace | aperto (host-guard-2) | — | go · analizzatore · completezza · commit · go |
| D-277 | Gli errori di compilazione di uno stadio del Dockerfile si perdevano | otel-demo currency (`b825c7c25726`) | risolto | `fcfb04338` | c, cpp · analizzatore · completezza · commit · scip-clang, Docker |
| D-278 | C++: una chiamata esplicita a un distruttore e un membro di un tipo dipendente | tinyxml2 (`9148bdf719e9`) | risolto per le chiamate ai distruttori | `2ac9cdc69` | cpp · analizzatore · completezza · commit · scip-clang |
| D-288 | La versione di SvelteKit registrata era quella di npm | js-sveltekit | risolto | `710460616` | svelte · analizzatore · correttezza · corsa su un progetto · npx, svelte-kit |
| D-289 | Lo strumento Vue 1.x di un progetto non ha il plugin del linguaggio | real-app-hoppscotch | risolto | `710460616` | vue · analizzatore · completezza · corsa su un progetto · @vue/language-core |
| D-290 | Vue: l'import di un componente e una lettura del template senza definizione | js-vue-pnpm | risolto | `b5a2fceb4`, `fc650d77f`, `3027d663f`, `55257959a` | vue, typescript · analizzatore · completezza · corsa su un progetto · scip-typescript, @vue/language-core |
| D-294 | Lo step `stack` non legge Maven, NuGet, Pub, Hex né Swift: JVM 0/42 e nessun framework .NET | scan/stack | aperto | `3b961646a` | java, kotlin, scala, csharp · analizzatore · completezza · benchmark · Modal |
| D-295 | Il `kind` `service` del registro fa servizi dei framework e degli strumenti di test | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-296 | Segni da prefisso di variabile o di pacchetto danno servizi che il progetto non usa | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-297 | File di CI e di strumenti, ed esempi sotto la documentazione, contati come servizi | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-298 | Servizi che nessun segno del registro raggiunge: 79 su 123 attesi | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-299 | Framework che il registro non ha o non cerca nel manifest dell'ecosistema | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-300 | Un segno del registro nomina solo il pacchetto della voce, non i suoi componenti | scan/stack | aperto | — | tutti · analizzatore · completezza · benchmark · Modal |
| D-301 | I requisiti Python si leggono solo da un file il cui nome comincia con `requirements` | scan/stack | aperto | — | python · analizzatore · completezza · benchmark · Modal |
| D-302 | La snapshot di jellyfin e di kuvasz non finisce in 900 secondi: la risoluzione degli import scorre ogni file | scan/stack | aperto | — | kotlin, csharp · snapshot · prestazioni · benchmark · Modal |
| D-303 | Lo step `stack` dà un framework all'unità sbagliata: per il nome, o al padre invece che al sottomodulo | scan/stack | aperto | — | tutti · analizzatore · correttezza · benchmark · Modal |

### Passo dinamico e osservatori

40 schede: 32 risolto, 1 aperto, 7 buco dichiarato.

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
| D-197 | I test di fastapi non ancora girati davvero | fastapi | aperto | `5148e8eb3`, `37c7ee093`, `a46e5af7d` | python, typescript · passo dinamico · completezza · finale · Playwright, git |
| D-198 | I test di eShop non ancora girati | eShop (`913acea66708`) | buco dichiarato (`tests_need_container_engine`, `tests_not_started`) | `15960a591`, `385387b93`, `408c1e7ae` | javascript, typescript, csharp · passo dinamico · completezza · finale · npm, Playwright, dotnet |
| D-199 | Python: extra e gruppi che il gestore non installa | spec del passo dinamico | buco dichiarato (test che non partono, `tests-not-run`) | — | python · passo dinamico · completezza · spec |
| D-200 | Python più vecchio del 3.12 | spec del passo dinamico | buco dichiarato (`python_too_old`) | — | python · passo dinamico · completezza · spec |
| D-201 | I servizi che `docker compose up` avvia non partivano | passo dinamico | risolto | `22dca6da8` | tutti · servizi · completezza · commit · npm, Compose, GitHub Actions |
| D-202 | I servizi di GitLab CI non avviati | passo dinamico | risolto | `23de469c4` | tutti · servizi · completezza · commit · GitLab CI |
| D-241 | C#: nessun osservatore eseguiva i test .NET | eShop (`913acea66708`) | risolto | `15960a591` | csharp · passo dinamico · completezza · finale · dotnet |
| D-270 | `services_unreachable` non diceva a quale indirizzo nessun servizio rispondeva | tududi (`71da9d7b34df`) | risolto | `e6a49324b` | javascript · passo dinamico · completezza · commit · Jest |
| D-274 | Un'esecuzione di test che la CI non esegue non lo diceva | tududi (`71da9d7b34df`) | buco dichiarato (`tests_not_in_ci`) | `a46e5af7d` | tutti · passo dinamico · completezza · commit · GitHub Actions |
| D-292 | Un processo ucciso con SIGKILL non lasciava registrazioni | osservatore JavaScript | risolto | `750a7aa36`, `1fd31c503` | javascript, typescript · passo dinamico · completezza · prova su Modal · Playwright, Node |

### Container, servizi e driver Modal

28 schede: 23 risolto, 1 aperto, 4 buco dichiarato.

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
| D-217 | GitLab CI: `!reference` | pre-mappa della CI | risolto | `940f69e66` | tutti · servizi · correttezza · review · Renovate, GitLab CI |
| D-218 | Kiri non stacca un container dalla sua prima rete | motore Kiri | buco dichiarato (`ci_step_not_run`) | `f024ba3a3` | tutti · container · completezza · review · Kiri |
| D-219 | Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL | spec del passo dinamico | buco dichiarato (buco del motore Kiri) | `2adc041f1`, `1c68cbde4` | tutti · container · correttezza · spec · Kiri |
| D-240 | Il `.env` che il progetto traccia non arrivava nel container | fastapi (`aabb90126964`) | risolto | `b1f14ac08` | python, cpp · servizi · completezza, sicurezza · ci-steps · Compose, Docker |
| D-244 | I test reali dei servizi si cancellavano a vicenda | `tests/test_codebase_map_dynamic_services.py` | risolto | `aea1c8c3b` | tutti · servizi · correttezza · test |
| D-260 | Il passo di test della CI senza le variabili che la CI gli dà | fastapi (`aabb90126964`) | risolto | `b1f14ac08` | tutti · servizi · completezza · commit · GitHub Actions |
| D-261 | Un passo di test dentro `docker compose run` | passo dinamico | buco dichiarato (`ci_step_not_run`) | `b1f14ac08` | tutti · servizi · completezza · commit · Compose, GitHub Actions |
| D-262 | apt dietro il proxy del container: l'archivio su HTTP in chiaro | container | risolto | `b1f14ac08` | tutti · container · completezza · commit · apt |
| D-269 | Due installazioni dello stesso strumento si toglievano i file a vicenda | cartella condivisa degli strumenti, macchina nuova | risolto da `2057bbafc` e `24e6682c9` | `2057bbafc`, `24e6682c9`, `c13d51732` | tutti · host · correttezza · commit · uv, Node, scip-python, Pyright, npm |
| D-275 | I passi della CI si leggevano solo nei workflow con servizi o Compose | pre-mappa della CI | risolto | `bd133fe94` | tutti · servizi · completezza · commit · GitHub Actions, GitLab CI |
| D-279 | I valori del `.env` non arrivavano all'esecuzione di uno stadio | container | risolto | `4a999670e` | tutti · container · completezza · commit · Docker, BuildKit |
| D-283 | Un valore del `.env` restava negli output JSON e binari e dentro parole più lunghe | container | risolto | `a41823a06`, `124c63440` | tutti · container · sicurezza · commit |
| D-291 | I valori di un `.env.example` facevano trattenere l'indice di un intero progetto | hoppscotch (`55908a76a1d0`) | risolto | `e674c007b` | typescript, javascript, vue · container · completezza · corsa su un progetto · scip-typescript |
| D-293 | La pre-mappa di Maven, Gradle e sbt girava sull'immagine di Temurin, non sulla base comune | container | risolto | `bb7a6b56e` | java, kotlin, scala · container · completezza · commit · Maven, Gradle, sbt |

### Benchmark e documenti

20 schede: 20 risolto, 0 aperto, 0 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit | Tag |
| --- | --- | --- | --- | --- | --- |
| D-220 | Risposte attese: il workspace di javapoet e le soluzioni .NET di zlib | javapoet, zlib | risolto | `a04ab36e1` | java, csharp · benchmark · benchmark · commit |
| D-221 | Lo schema del banco senza BOM, POM genitore e versioni centrali | dieci progetti del corpus | risolto | `1420247ad` | java, kotlin · benchmark · benchmark · commit · Maven, Gradle |
| D-222 | `test_catalog` rosso: ANAGRAFICA.md non era l'uscita del generatore | benchmark project-model | risolto | `68a846a4a` | tutti · documenti · documentazione · test |
| D-223 | Le risposte attese delle fixture Android senza i build-tools | jvm-android-app-lib, mix-poly-firebase | risolto | `68a846a4a` | java, kotlin · benchmark · benchmark · commit · Gradle, Android SDK |
| D-224 | I test del registratore JVM saltati: l'immagine dei test senza JDK | `tests/modal_pytest.py` | risolto | `a633ebd72` | java · benchmark · benchmark · commit · Modal |
| D-225 | Due fixture con `node --test test/` | due fixture JavaScript | risolto | `12775fee3` | javascript · benchmark · benchmark · commit |
| D-226 | Toolchain Maven contate sbagliate per il frammento di `declared_in` | jvm-ver-* e le fixture Maven | risolto | `eef3e1fef`, `bef968a44` | java · benchmark · benchmark · java-versions · Maven |
| D-227 | README del benchmark: Rust, C e C++ «solo dove Valgrind parte» | `benchmarks/project-model/README.md` | risolto | `e4da4b429` | c, cpp, rust · documenti · documentazione · commit · Valgrind |
| D-228 | Il rapporto dichiarava nulla la copertura a runtime | il metodo di codebase-map | risolto | `78c03d6e8` | tutti · benchmark · benchmark · commit |
| D-229 | Spec: il passo 2 «non esegue codice del progetto» | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` | javascript, typescript, java, kotlin, c, cpp, csharp · documenti · documentazione, sicurezza · spec |
| D-230 | Spec: Rust, C e C++ «non provati» su Modal | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` | c, cpp, rust · documenti · documentazione · spec · Modal |
| D-231 | README, SKILL e riferimenti dicevano Jedi e «solo statica» | README, SKILL, `references/snapshot.md` | risolto | `e617127c3` | python · documenti · documentazione · commit · Jedi |
| D-232 | L'osservatore Python diceva che il passo non avvia servizi | `scripts/dynamic/python.py` | risolto | `0ca9f1650` | python · documenti · documentazione · commit |
| D-233 | Due script del benchmark dell'inferenza mai eseguiti | `benchmarks/inference-audit` | risolto | `137512c11` | tutti · benchmark · benchmark · commit |
| D-234 | Un file dello snapshot senza dichiarazioni usciva dal progetto nel grafo | `benchmarks/inference-audit` | risolto | `53e219638` | tutti · benchmark · benchmark · commit |
| D-235 | Pre-mappa: dipendenze sotto la soglia | corpus della pre-mappa | risolto | `de353d251`, `99112d0b9` | tutti · benchmark · benchmark · corpus della pre-mappa |
| D-243 | Il driver perdeva i buchi del passo dinamico | benchmark project-model | risolto | `aea1c8c3b` | tutti · benchmark · benchmark · commit |
| D-251 | I risultati di un giro non registravano il codice di Daodan su cui era girato | giro `ci-steps` | risolto per i giri dopo `cbc219663` | `cbc219663` | tutti · benchmark · benchmark · review · Modal |
| D-280 | Una seconda sessione sullo stesso checkout ha committato ogni modifica in corso insieme | il checkout di Daodan | risolto | — | tutti · processo · correttezza · commit · git |
| D-287 | Il driver della pipeline non caricava i dati che gli script leggono accanto alla loro cartella | benchmark project-model | risolto | `c1244f610` | tutti · benchmark · benchmark · commit · Modal |

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

- `no-document`: un file Java che nessun javac del build compila, in due fixture: un modulo fuori dal reactor predefinito di Maven e l'output di protoc fuori da ogni source set di Gradle; ogni file ha la sua causa nel motivo (D-112, `f1124a748`). Su jhipster, i 14 documenti senza occorrenze sono `package-info.java`, contati come indicizzati da `1c68cbde4`, e un file lo esclude il build stesso, che lo dice (D-111, `f1124a748`).
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
  - i 5.147 della conferma sono tutti di zlib, in file che il build predefinito non compilava: examples/, contrib/infback9, test/infcover.c e due file di contrib/minizip (D-136).
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
- `no-document`: file senza documento, ognuno dietro un cfg falso su Linux e con la sua causa (D-143) e file che nessun crate carica (D-144). Da `a3801beed`, un file dietro un `mod` con cfg falso dice perché manca (D-237).
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

- `no-rule`: un riferimento di classe, id o composes senza una regola che lo definisca (D-162), fra cui le classi Tailwind. Da `3595d571b` Tailwind gira nel container (D-161). Sugli stessi due casi, tududi e fastapi, da 38.210 buchi nella conferma a 523 in `ci-steps`: nessuno dei due giri registra il proprio codice, così il salto non si lega a un commit (D-251). Da `efac75599` Tailwind trova i fogli di un pacchetto come il suo build: memos da 5.073 a 652, fastapi da 688 a 11 (D-162).
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
| js-sveltekit | HTML, JavaScript, Svelte, TypeScript | path-alias, no-lockfile, build-generates-code | D-153, D-156, D-159, D-288 | — |
| js-turborepo | JavaScript | workspace-glob, no-lockfile, internal-link | — | — |
| js-vendored-generated | GraphQL, TypeScript | no-lockfile, generated-file, vendored-code | — | — |
| js-version-conflict | JavaScript | version-disagree, no-lockfile | — | — |
| js-vite-react-ts | HTML, TSX, TypeScript | path-alias, version-absent, no-lockfile, false-generated | — | — |
| js-vue-pnpm | HTML, TypeScript, Vue | version-absent, no-lockfile, ambiguous-extension | D-154, D-159, D-290 | — |
| js-yarn-berry | JavaScript | workspace-glob, unit-no-name, version-absent, locked-versions, internal-link | D-148, D-157 | — |

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
| jvm-mixed-java-kotlin | Java, Kotlin | custom-source-roots, no-lockfile, version-indirect, build-only-dependency, missing-file | D-284 | — |
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
| sys-go-workspace | Go | virtual-root, locked-versions, internal-link | D-273 | — |
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
| jvm-ver-mvn-5 | Maven, source 1.5 | — | D-284 |
| jvm-ver-mvn-6 | Maven, source 1.6 | — | — |
| jvm-ver-mvn-7 | Maven, source 1.7 | — | — |
| jvm-ver-mvn-8 | Maven, source 1.8 | — | — |
| jvm-ver-mvn-9 | Maven, source 9 | — | — |
| jvm-ver-mvn-cfg6 | Maven, source 1.6 nel plugin del compilatore | — | D-226 |
| jvm-ver-mvn-rel8 | Maven, release 8 | — | — |

Le nominano tutte insieme (`jvm-ver-*`): rivelate D-102, D-103, D-104, D-179, D-181, D-226; citate D-284.

### Repository veri (18)

| Progetto | Repository e commit | Casi | Rivelate | Citate |
| --- | --- | ---: | --- | --- |
| mix-real-chi | github.com/go-chi/chi `c64ed7d6635f` | 6 | D-149 | D-275, D-280 |
| mix-real-javapoet | github.com/square/javapoet `b9017a9503b7` | 6 | D-016, D-054, D-099, D-100, D-178, D-220 | D-275 |
| mix-real-klaxon | github.com/cbeust/klaxon `1173bdc568a6` | 10 | D-098 | D-275 |
| mix-real-python-semver | github.com/python-semver/python-semver `b6e83e3e40d3` | 10 | D-031, D-088, D-183, D-206, D-248 | — |
| mix-real-semver | github.com/dtolnay/semver `280ebcb6edac` | 8 | D-143, D-209, D-238 | D-176, D-230, D-275 |
| mix-real-tinyxml2 | github.com/leethomason/tinyxml2 `9148bdf719e9` | 11 | D-043, D-137, D-209, D-236, D-266, D-271, D-272, D-278 | D-230, D-255, D-265, D-275 |
| mix-real-tududi | github.com/chrisvel/tududi `71da9d7b34df` | 9 | D-145, D-146, D-147, D-182, D-185, D-186, D-187, D-270, D-274 | D-189, D-213, D-240, D-251 |
| mix-real-zlib | github.com/madler/zlib `51b7f2abdade` | 15 | D-043, D-113, D-130, D-133, D-134, D-136, D-209, D-220, D-267, D-268, D-271 | D-010, D-065, D-230, D-275 |
| real-app-full-stack-fastapi | github.com/fastapi/full-stack-fastapi-template `aabb90126964` | 21 | D-056, D-088, D-188, D-195, D-197, D-240, D-246, D-248, D-252, D-254, D-260 | D-162, D-171, D-213, D-251, D-253, D-270 |
| real-app-hoppscotch | github.com/hoppscotch/hoppscotch `55908a76a1d0` | 20 | D-143, D-144, D-159, D-160, D-163, D-237, D-289, D-291 | D-080, D-162, D-239 |
| real-app-jhipster-sample | github.com/jhipster/jhipster-sample-app `6b000b5d23a3` | 17 | D-111, D-194 | D-275 |
| real-app-kotlinconf | github.com/JetBrains/kotlinconf-app `146e891c150c` | 18 | D-055, D-057, D-058, D-110, D-158 | D-275 |
| real-app-memos | github.com/usememos/memos `509e41bd1a1b` | 10 | D-160 | D-162, D-163, D-275 |
| real-svc-eshop | github.com/dotnet/eShop `913acea66708` | 16 | D-018, D-059, D-113, D-114, D-116, D-118, D-119, D-120, D-198, D-241, D-249 | — |
| real-svc-otel-demo | github.com/open-telemetry/opentelemetry-demo `b825c7c25726` | 26 | D-059, D-094, D-105, D-106, D-107, D-114, D-132, D-135, D-240, D-255, D-259, D-272, D-277 | D-071 |
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

- `tutti` (35): D-001, D-004, D-005, D-018, D-019, D-022, D-023, D-024, D-031, D-032, D-033, D-034, D-035, D-037, D-062, D-065, D-066, D-067, D-068, D-069, D-070, D-071, D-081, D-082, D-115, D-149, D-167, D-168, D-182, D-196, D-201, D-202, D-245, D-250, D-274
- `c` (27): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-127, D-128, D-130, D-131, D-132, D-133, D-134, D-136, D-177, D-236, D-259, D-265, D-266, D-267, D-268, D-271, D-277
- `cpp` (27): D-029, D-043, D-060, D-061, D-076, D-077, D-121, D-122, D-123, D-124, D-127, D-128, D-130, D-131, D-132, D-133, D-135, D-177, D-236, D-259, D-265, D-266, D-268, D-271, D-272, D-277, D-278
- `java` (27): D-003, D-016, D-025, D-026, D-027, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-090, D-091, D-092, D-093, D-094, D-099, D-100, D-101, D-105, D-106, D-111, D-178, D-265
- `python` (26): D-006, D-007, D-028, D-047, D-048, D-049, D-052, D-074, D-075, D-084, D-085, D-086, D-087, D-088, D-169, D-183, D-184, D-188, D-197, D-199, D-200, D-246, D-247, D-248, D-252, D-253
- `javascript` (25): D-013, D-021, D-046, D-049, D-051, D-053, D-056, D-072, D-147, D-158, D-170, D-171, D-185, D-186, D-187, D-189, D-190, D-191, D-192, D-194, D-195, D-198, D-265, D-270, D-292
- `kotlin` (21): D-016, D-027, D-049, D-050, D-054, D-055, D-057, D-058, D-063, D-064, D-083, D-089, D-091, D-092, D-093, D-094, D-105, D-106, D-107, D-110, D-166
- `typescript` (19): D-008, D-009, D-029, D-072, D-073, D-129, D-145, D-146, D-147, D-150, D-151, D-152, D-160, D-170, D-194, D-197, D-198, D-265, D-292
- `csharp` (14): D-010, D-021, D-049, D-113, D-116, D-117, D-118, D-119, D-120, D-165, D-198, D-241, D-242, D-249
- `go` (13): D-002, D-020, D-045, D-078, D-079, D-138, D-139, D-140, D-141, D-173, D-174, D-257, D-265
- `rust` (13): D-014, D-021, D-030, D-078, D-143, D-144, D-173, D-175, D-176, D-237, D-238, D-239, D-265
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

#### D-256 Il riscrittore dei commenti eseguiva sull'host i formattatori sui file del progetto
- **Tag:** lingua python, javascript, typescript, rust, go · area host · tipo sicurezza · origine review · strumento prettier, biome, ruff, black, rustfmt, gofmt
- **Descrizione:** android-sdk: `comment_rewriter._run_formatter` lanciava sull'host prettier, biome, ruff, black, rustfmt e gofmt sui file del progetto, e prettier caricava la configurazione JavaScript del progetto (riportato da team-lead il 16 novembre).
- **Spiegazione:** prima di `5dcb466fe`, `scripts/comment_rewriter.py:358` (`_run_formatter`) provava per linguaggio `ruff format` o `black`, `prettier --write` o `biome format --write`, `rustfmt`, `gofmt -w`, con `subprocess.run` sul file riscritto, il primo che `shutil.which` trova; un formattatore cerca la configurazione a partire dalla cartella del file, e quella di prettier può essere un modulo JavaScript.
- **Progetto e caso:** riscrittore dei commenti — la prova di android-sdk, 16 novembre 2026.
- **Rimedio:** `5dcb466fe` (16 novembre, dynamic-step-2), `scripts/comment_rewriter.py`: `_run_formatter` non c'è più, così il riscrittore non avvia nessun programma; una riscrittura che scrive un file finisce con `FORMAT_UNDONE`, che dice perché la formattazione resta da fare. Lo stesso commit toglie gli aiuti Rust dell'host rimasti senza uso: `rust_toolchain` lanciava `rustc --print sysroot`, che un rust-toolchain del progetto può dirottare.
- **Verifica:** solo test, a segni (`tests/test_codebase_map_host_programs.py`, `test_the_comment_rewriter_runs_no_formatter_on_the_host`): un `prettier.config.js` che scrive un segno e prettier, biome, ruff, black, rustfmt e gofmt finti nel PATH; nessun segno e nessun processo.
- **Stato:** risolto.
- **Note:** D-161, D-239, D-245, D-248, D-250 e D-253, lo stesso difetto; dallo stesso commit D-263 e D-264.

#### D-263 Su Windows un programma si cercava anche nella cartella del progetto
- **Tag:** lingua tutti · area host · tipo sicurezza · origine review · strumento docker, podman, npm, wsl
- **Descrizione:** dynamic-step-2, nella verifica di ogni passo che Daodan esegue sull'host: su Windows `shutil.which` cerca prima nella cartella corrente, cioè il progetto, e un `docker`, `podman`, `npm` o `wsl.exe` messo lì sarebbe partito (dal commit `5dcb466fe`).
- **Spiegazione:** `find_engine`, `wsl_executable`, `npm_modules` e `git_executable` cercavano i loro programmi con `shutil.which`.
- **Progetto e caso:** host Windows — verifica di dynamic-step-2, commit `5dcb466fe`, 16 novembre 2026.
- **Rimedio:** `5dcb466fe` (16 novembre), `scripts/tree_scope.py` (`program`), `scripts/container.py`, `scripts/engine_tools.py`: `tree_scope.program` legge solo le voci assolute del PATH, e lo usano `find_engine`, `wsl_executable`, `npm_modules` e `git_executable`.
- **Verifica:** solo test, a segni (`tests/test_codebase_map_host_programs.py`, `test_a_program_is_found_on_absolute_path_entries_only`): docker, podman, npm e wsl messi nel progetto non si trovano mai.
- **Stato:** risolto.
- **Note:** D-245, D-250, D-256.

#### D-264 La sonda della memoria importava i moduli della cartella del progetto
- **Tag:** lingua tutti · area host · tipo sicurezza · origine review · strumento python
- **Descrizione:** dynamic-step-2: la sonda della memoria (`code_graph.measured`) avviava `python -c` con la cartella corrente in testa a `sys.path`, e un `subprocess.py` o `resource.py` del progetto veniva importato (dal commit `5dcb466fe`).
- **Spiegazione:** `python -c` mette la cartella corrente in testa a `sys.path`; `-I` la toglie.
- **Progetto e caso:** sonda della memoria — verifica di dynamic-step-2, commit `5dcb466fe`, 16 novembre 2026.
- **Rimedio:** `5dcb466fe` (16 novembre), `scripts/code_graph.py` (`measured`): `python -I -c`.
- **Verifica:** solo test, a segni (`tests/test_codebase_map_host_programs.py`, `test_the_memory_probe_imports_nothing_from_the_folder_it_runs_in`): un `subprocess.py` e un `resource.py` nella cartella corrente non sono importati.
- **Stato:** risolto.
- **Note:** D-248, D-252: gli interpreti Python che Daodan avvia sull'host.

#### D-265 Un file con un errore di sintassi si perdeva intero
- **Tag:** lingua go, rust, java, javascript, typescript, c, cpp · area snapshot · tipo completezza · origine finale · strumento tree-sitter
- **Descrizione:** a ogni errore di parse lo snapshot buttava il file intero, in ogni linguaggio letto con tree-sitter: il giro finale aveva perso così 70 file e 57.837 riferimenti dell'indice (dal commit `ba8a1920f`).
- **Spiegazione:** gli adattatori go, rust, java, javascript e cfamily scartavano il risultato di un albero con un nodo ERROR.
- **Progetto e caso:** il corpus — finale, misura del commit `ba8a1920f`, 16 novembre 2026.
- **Rimedio:** `ba8a1920f` (16 novembre, dynamic-step-2), `scripts/languages/semantic.py` (`_around`) e gli adattatori:
  - i fatti fuori da ogni nodo ERROR restano, i riferimenti che un nodo ERROR copre si tolgono, e le righe non lette sono in `unread`;
  - la copertura del file è `partial` nello store, nella classificazione, nel passo delle posizioni e in quello dei motori, e `code_graph.unread` elenca il file con le sue righe.
- **Verifica:**
  - dal commit, tinyxml2: `xmltest.cpp` tiene 2.223 riferimenti con 10 righe non lette; siti C++ da 2.576 a 4.799, con risposta da 2.296 a 4.415; su sette repository restano 63 file e 28.976 riferimenti;
  - `tests/test_codebase_map_snapshot_partial.py` (`test_a_file_with_a_syntax_error_keeps_its_facts_around_the_error`, `test_the_snapshot_and_the_graph_read_the_file_around_its_error_and_declare_the_rest`).
- **Stato:** risolto; Python, letto con ast, non ha un albero oltre l'errore e resta escluso (D-252 per la sintassi più nuova).
- **Note:** il commit è un feat. D-266 viene dallo stesso commit.

#### D-276 Le righe che avviano il plugin eseguivano sull'host il `.venv` del progetto
- **Tag:** lingua python · area host · tipo sicurezza · origine prova su Modal · strumento uv, Claude Code
- **Descrizione:** le righe che avviano il server MCP (`.mcp.json`, `plugin.toml`) e quella dell'hook PostToolUse erano `uv run --no-config --no-project --script mcp_server.py`, con la cartella del progetto come cartella corrente: al primo avvio dopo l'installazione o un aggiornamento del plugin, o dopo che la cache di uv è stata svuotata, uv 0.11.28 interrogava e quindi eseguiva l'interprete `<progetto>/.venv/bin/python3` sull'host, prima che il server partisse (dal commit `624561af1`).
- **Spiegazione:** quando lo script non ha ancora un ambiente nella cache, uv cerca un interprete a partire dalla cartella corrente; misurato su Modal con uv vero: degli otto insiemi di opzioni provati, solo un interprete esplicito o `uv --directory <cartella del plugin>` non lasciano segni.
- **Progetto e caso:** avvio del plugin — prova di host-guard-2, commit `624561af1`, 16 novembre 2026.
- **Rimedio:**
  - `624561af1` (16 novembre, host-guard-2), `plugins/codebase-map/.mcp.json`, `plugins/codebase-map/plugin.toml`, `plugins/codebase-map/hooks/hooks.json`: le tre righe sono `uv --directory "${CLAUDE_PLUGIN_ROOT}" run …`; il server riceve il progetto con `--project "${CLAUDE_PROJECT_DIR}"`, che Claude Code sostituisce negli argomenti di un server stdio, la stessa cartella che prima era la cartella corrente; l'hook prende il progetto dal campo `cwd` del suo stdin, e se manca non aggiorna niente. Nessun codice Python cambia.
  - `1dc2d6b9b` (17 novembre, host-guard-2): dal primo commit il server parte dalla cartella del plugin, quindi la cartella corrente non è più il progetto, e il server legava quella; ora `mcp_service.launch_project` prende `--project`, altrimenti `CLAUDE_PROJECT_DIR`, altrimenti si ferma dicendo perché, e `mcp_server.py` non ripiega più sulla cartella corrente.
- **Verifica:**
  - `tests/test_codebase_map_launch.py` (`test_uv_started_in_a_project_runs_nothing_of_it`, `test_the_manifest_declares_the_server_as_the_host_starts_it`), a segni: le due righe con uv vero e un `.venv` che lascia un segno;
  - dal commit, su Modal con Claude Code 2.1.322 (`benchmarks/host-guard/`: `modal_host_launch.py`, `uv_options.py` con `test_options` e `test_starts`).
  - `tests/test_codebase_map_launch.py` (`test_the_server_takes_its_project_from_the_launch_never_from_where_it_starts`), rosso prima di `1dc2d6b9b`.
- **Stato:** risolto su Linux; Windows non è misurato.
- **Note:** D-248, D-253, D-264, lo stesso difetto per gli interpreti Python che Daodan avvia sull'host.

#### D-281 Uno store che arriva con il progetto sceglieva il processo da terminare e la cartella da leggere
- **Tag:** lingua tutti · area host · tipo sicurezza · origine prova su Modal · strumento —
- **Descrizione:** lo store di Daodan sta nella cartella del progetto, quindi un repository può portarne uno: l'hook PostToolUse leggeva il processo da terminare da `.daodan/map/runs/working/snapshot/engine-pass.running`, e uno `state.json` pubblicato poteva nominare un `target` assoluto, che l'aggiornamento fotografava (dal commit `398adf80e`).
- **Spiegazione:** su Modal un file che nominava un processo canarino l'ha fatto terminare con una modifica; con `{"pid": 1}` la chiamata è `os.killpg(1, SIGTERM)`, su Linux tutti i processi dell'utente. Il `target` portava l'aggiornamento su una cartella fuori dal progetto.
- **Progetto e caso:** lo store nel progetto — prova di host-guard-2, commit `398adf80e`, 17 novembre 2026.
- **Rimedio:** `398adf80e` (17 novembre, host-guard-2): il passo registra il suo processo nella cartella condivisa di Daodan (`passes/<digest del percorso del manifest>.json`, `engine_pass.running_record` in `scripts/engine_pass.py`), e un aggiornamento rifiuta un target fuori dal progetto con le parole di `_bound_manifest`.
- **Verifica:** `tests/test_codebase_map_working_run.py` (`test_6_a_store_that_comes_with_the_project_names_no_process_to_end`, `test_6_a_store_that_comes_with_the_project_names_no_folder_outside_it`), rossi prima del commit.
- **Stato:** risolto su Linux; Windows non è misurato.
- **Note:** un passo partito prima del commit e ancora in corso non si vede in corso, una volta sola. D-282.

#### D-282 Sull'host taskkill, wsl.exe, rg e grep si avviavano per nome nudo
- **Tag:** lingua tutti · area host · tipo sicurezza · origine prova su Modal · strumento taskkill, WSL, ripgrep, grep
- **Descrizione:** con il progetto come cartella corrente, un nome senza percorso avvia il file del progetto (su Windows dalla cartella corrente, su Linux se il `PATH` contiene `.`): `engine_pass._terminate_tree` avviava `taskkill`, `container.wsl` e `distro_argv` ripiegavano su un `wsl.exe` nudo, `usage_finder` avviava `rg` e `grep` (dal commit `fd76f2d7d`).
- **Spiegazione:** D-263 aveva fissato la ricerca dei programmi (`tree_scope.program`) ma questi quattro la saltavano.
- **Progetto e caso:** gli strumenti dell'host — prova di host-guard-2, commit `fd76f2d7d`, 17 novembre 2026.
- **Rimedio:** `fd76f2d7d` (17 novembre, host-guard-2): `scripts/engine_pass.py` prende `taskkill` da `tree_scope.program` e dice quando il `PATH` non lo ha; `scripts/container.py` (`wsl`, `distro_argv`) dà il buco «WSL is not installed» invece di ripiegare; `scripts/usage_finder.py` prende `rg` e `grep` da `tree_scope.program`.
- **Verifica:** `tests/test_codebase_map_host_programs.py` (`test_a_pass_is_ended_by_the_taskkill_of_the_path_never_by_the_project_s`, `test_without_wsl_nothing_named_wsl_is_started`, `test_usages_are_searched_by_a_tool_of_the_path_or_by_python_never_by_the_project_s`), a segni, veri su Linux con `.` nel `PATH`: prima partivano il `taskkill`, il `wsl.exe` e l'`rg` del progetto, e l'`rg` finto faceva rispondere «nessun uso».
- **Stato:** risolto su Linux; Windows non è misurato.
- **Note:** D-263.

#### D-284 `kotlin.compiler.jvmTarget` di un pom non era una toolchain
- **Tag:** lingua java, kotlin · area pre-mappa · tipo completezza · origine commit · strumento Maven
- **Descrizione:** `scripts/premap/jvm_files.py` non leggeva `kotlin.compiler.jvmTarget`, quindi la toolchain Java 17 di jvm-mixed-java-kotlin restava fuori (dal commit `a6af77108`).
- **Spiegazione:** è il livello di bytecode che scrive kotlin-maven-plugin, quindi una toolchain Java del pom.
- **Progetto e caso:** jvm-mixed-java-kotlin — commit `a6af77108` di android-sdk, 17 novembre 2026.
- **Rimedio:** `a6af77108` (17 novembre, android-sdk), `scripts/premap/jvm_files.py`: `kotlin.compiler.jvmTarget` è tra le proprietà Java del pom (campo `properties.kotlin.compiler.jvmTarget`, strumento java).
- **Verifica:** `tests/test_codebase_map_premap.py` (`test_the_jvm_target_kotlin_compiles_to_is_a_java_toolchain_of_the_pom`); con `score.py` su Modal ogni fixture JVM Maven ha tutte le sue toolchain (jvm-ver-mvn-5…25, cfg6, rel8, multi-bom-profile, release-apt, wrapper), e jvm-mixed-java-kotlin passa a 2 su 2.
- **Stato:** risolto.
- **Note:** D-226.

#### D-285 L'hook, refresh, diff e carry seguivano ciò che uno store portato dal progetto nomina
- **Tag:** lingua tutti · area host · tipo sicurezza · origine commit · strumento —
- **Descrizione:** l'hook, refresh, diff e carry usavano lo store senza i controlli che il servizio MCP applica in `_bound_run`, e un repository può portare il suo `.daodan/map` (dal commit `76214fa0f`):
  - `latest_completed` di `runs.json` si univa come percorso: un registro che nominava una run completa altrove (assoluta, `..`) costruiva da lì una run di lavoro;
  - un link dentro la cartella di una run si seguiva: l'aggiornamento entrava in una cartella snapshot linkata (e lì toglieva `manifest.*`), un `proposals.json` linkato si leggeva come proprio, carry copiava il file che un link nominava;
  - con un `target` `..` in `state.json`, l'hook interrogava git sulla cartella sopra il progetto;
  - una richiesta in sospeso in un `ui-requests.json` portato dal progetto si prendeva come chiesta dalla persona.
- **Spiegazione:** lo stesso difetto di D-281: lo store sta nella cartella del progetto, e solo il servizio MCP lo controllava.
- **Progetto e caso:** lo store nel progetto — commit `76214fa0f` di host-guard-2, 17 novembre 2026.
- **Rimedio:** `76214fa0f` (17 novembre, host-guard-2), `scripts/run_store.py`, `scripts/snapshot.py`: `latest_completed` è un solo nome di cartella, altrimenti «malformed runs registry»; una run che contiene un link è rifiutata; un solo aiuto, `_project_target`, serve hook, aggiornamento e `_bound_manifest`; le richieste dell'esploratore vivono nella cartella condivisa di Daodan.
- **Verifica:** ogni caso rosso prima del commit: `tests/test_codebase_map_working_run.py` (`test_6_a_store_that_comes_with_the_project_names_its_runs_by_name`, `test_6_a_store_that_comes_with_the_project_holds_no_link`, `test_6_the_hook_asks_git_about_no_folder_outside_the_project`), `tests/test_codebase_map_run_controls.py` (`test_a_parent_run_that_holds_a_link_is_neither_carried_nor_compared`), `tests/test_codebase_map_visual_server.py` (`test_a_request_file_that_comes_with_the_project_asks_the_host_nothing`).
- **Stato:** risolto su Linux; Windows non è misurato.
- **Note:** le richieste dell'esploratore in sospeso al momento dell'aggiornamento non si rivedono, una volta. D-281, D-286.

#### D-286 Uno store portato dal progetto può riempire prima i file derivati
- **Tag:** lingua tutti · area host · tipo sicurezza · origine review · strumento —
- **Descrizione:** uno store `.daodan/map` che arriva con il progetto poteva portare già pronti i file che Daodan deriva (`snapshot/premap.json`, i documenti delle fasi, le schede, gli archi), presi come freschi o come prove: un `premap.json` tracciato accanto allo snapshot di Daodan dava il suo passo `touch /tmp/daodan-mark` a `dynamic.ci_steps`, cioè ai comandi che il container esegue (dal commit `6ab37afd9`).
- **Spiegazione:** D-281 e D-285 avevano chiuso i nomi di processi, cartelle, link e richieste, non i contenuti: lo store sta nella cartella del progetto, e niente distingueva uno store di Daodan da uno arrivato con il repository.
- **Progetto e caso:** lo store nel progetto — segnalato da team-lead, commit `6ab37afd9` di host-guard-2, 17 novembre 2026.
- **Rimedio:** `6ab37afd9` (17 novembre, host-guard-2, decisione del proprietario), `scripts/run_store.py`, `scripts/snapshot.py`, `scripts/snapshot_store.py`, `scripts/change_set.py`, `scripts/mcp_service.py`:
  - uno store sotto cui git del progetto traccia un percorso è estraneo (`run_store.tracked`: `git ls-files` sull'indice, git non esegue niente); un repository che non elenca i suoi file è un rifiuto, non un via libera;
  - `open_snapshot` rifiuta i suoi manifest, quindi nessun suo file derivato è fresco; ogni strumento MCP, creazione di run compresa, refresh, i comandi della CLI e carry rifiutano con la causa e il rimedio («untrack it: git rm -r --cached -- <path>, and delete the folder too unless the store is your own»); l'hook non fa niente;
  - Daodan non sposta, rinomina né modifica niente di quello store; lo store di Daodan riceve un `.gitignore` (`*`), così un `git add -A` non lo traccia.
- **Verifica:** `tests/test_codebase_map_working_run.py` (`test_7_a_premap_that_comes_with_the_project_gives_the_container_no_command`, `test_7_nothing_of_a_store_that_comes_with_the_project_is_read`, `test_7_no_run_is_created_in_that_store_and_nothing_of_it_changes`, byte per byte, `test_7_a_repository_that_does_not_list_what_it_tracks_is_not_trusted`, `test_7_the_store_daodan_makes_is_kept_out_of_the_repository`).
- **Stato:** risolto su Linux con git; uno store arrivato in uno zip, o un progetto senza git, si prende come di Daodan; Windows non è misurato.
- **Note:** un progetto che ha già committato il suo `.daodan/map` è rifiutato dopo l'aggiornamento: `git ls-files .daodan` lo dice. D-281, D-285.

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
- **Rimedio:** decisione di team-lead (16 novembre, riportata da android-sdk): nessuna via dello stadio per la JVM, un file non la giustifica; il build resta un buco che dice perché. `89d6ea082` (16 novembre, dynamic-jvm-2), `scripts/indexers/jvm.py` (`GENERATES`, `ungenerated`, `failed`): un build che si ferma su nomi che non trova («Unresolved reference», «cannot find symbol», «package … does not exist»), i cui script applicano il plugin protobuf di Gradle e la cui cartella non ha nessun `.proto`, ha nel motivo di `build_not_indexed` il plugin, `src/main/proto` e la riga del Dockerfile della cartella che li copia lì; i file si leggono, non si eseguono.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_jvm.py`, `test_a_build_whose_protobuf_sources_only_its_dockerfile_copies_says_so_in_its_reason`, per Java e Kotlin): il motivo nomina `com.google.protobuf`, `src/main/proto`, `Dockerfile:4` e `COPY ./pb/ ./src/main/proto/`; con un `.proto` nella cartella non lo dice.
- **Stato:** buco dichiarato (`build_not_indexed`, con la causa nel motivo): il build è completo solo nell'immagine del suo Dockerfile.
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
- **Tag:** lingua java · area analizzatore · tipo completezza · origine finale · strumento scip-java, Maven
- **Descrizione:** finale: 15 file Java su 136 fuori dall'indice, 14 «document without occurrences» e 1 «no document in the index».
- **Spiegazione:**
  - i 14 «document without occurrences» sono `package-info.java` (javadoc e la riga `package`), che scip-java scrive come documenti senza occorrenze: la copertura li contava mancanti;
  - `DatabaseTestcontainer.java` lo lascia fuori il build di jhipster: il profilo `dev`, `activeByDefault` (`pom.xml:855-898`), dà a maven-compiler-plugin `<testExclude>io/github/jhipster/sample/config/DatabaseTestcontainer.java</testExclude>`; misurato con Maven 3.10.0 `help:effective-pom` su Modal.
- **Progetto e caso:** jhipster-sample (`6b000b5d23a3`) — finale, 16 novembre 2026.
- **Rimedio:** android-sdk:
  - `1c68cbde4`, `scripts/code_graph.py` (`build`): un documento vuoto conta come indicizzato dove lo snapshot non trova niente a cui rispondere (nessun sito di riferimento, nessuna funzione, metodo o classe): i 14 `package-info.java`;
  - `f1124a748`: `scripts/premap/maven.py` registra per ogni `maven-module` i `compile_excludes` di maven-compiler-plugin (`excludes`, `testExcludes`) dal modello effettivo di Maven che la pre-mappa ha nel suo container; `scripts/indexers/java.py` (`missing`) dice «the build leaves it out: maven-compiler-plugin excludes `<pattern>` from <folder> (<pom>, as Maven's effective model gives it)».
- **Verifica:** solo test (`tests/test_codebase_map_code_graph.py`, `test_a_document_without_occurrences_of_a_file_that_holds_nothing_to_answer_is_indexed`; `tests/test_codebase_map_premap_maven.py`, `test_the_files_the_compiler_plugin_leaves_out_are_the_module_s`; `tests/test_codebase_map_indexers_jvm.py`, `test_a_java_file_the_compiler_plugin_excludes_says_so`); atteso su jhipster Java 135 file su 136, non ancora rimisurato.
- **Stato:** risolto; il 136° file è un'esclusione dichiarata con il suo motivo.
- **Note:** android-sdk ha aggiunto `excluded` a `structure()` e a `index()` di `scripts/indexers/java.py`.
#### D-112 Un file Java senza documento in due fixture: nessun javac del build lo compila
- **Tag:** lingua java · area analizzatore · tipo completezza · origine finale · strumento Maven, Gradle, protoc
- **Descrizione:** finale: jvm-maven-multi-bom-profile 1 file su 4 e jvm-protobuf-generated 1 su 2, «no document in the index».
- **Spiegazione:**
  - jvm-maven-multi-bom-profile: `cli/pom.xml` entra nel reactor solo con il profilo `cli` (la proprietà `with-cli`, `pom.xml:86-95`), quindi il modello effettivo di Maven non ne ha il progetto;
  - jvm-protobuf-generated: `GreetingProto.java` è l'output di protoc committato in `src/generated/java`, che nessun source set di Gradle contiene.
- **Progetto e caso:** jvm-maven-multi-bom-profile, jvm-protobuf-generated — finale, 16 novembre 2026.
- **Rimedio:** `f1124a748` (17 novembre, android-sdk), `scripts/indexers/java.py` (`missing`): ogni file Java senza documento ha la sua causa, in quest'ordine:
  - le esclusioni del compilatore (D-111);
  - «its module <root> (<pom>) is in no reactor of Maven's default build: Maven's effective model holds no project of it, so no javac task compiles it»;
  - «the build of <root> wrote no index: …»;
  - altrimenti «no javac task of the build compiles it: scip-java writes a document for every file javac compiles».
- **Verifica:** solo test (`tests/test_codebase_map_indexers_jvm.py`, `test_a_java_file_no_javac_task_compiles_says_why`).
- **Stato:** buco dichiarato (il motivo di `missing`).
- **Note:** D-111; android-sdk ha aggiunto anche `outside` a `structure()` e `configs` (excluded, outside, failed) a `index()` di `scripts/indexers/java.py`.
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
- **Note:** D-134; il build autotools di minizip ora c'è. Da `60e3590b3` il configure di zlib gira prima di make e `test/infcover.c` è indicizzato (D-267), e il C++ di `contrib/iostream*`, che nessun build compila, è `unavailable` (D-268).

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
- **Rimedio:** `841cfe14f` (16 novembre, android-sdk), `scripts/docker_build.py`, `scripts/indexers/clang.py`, `scripts/premap/dockerfile.py`, `scripts/premap/dockerfile_stages.go`, su `f024ba3a3` (la lettura dei Dockerfile con il parser di BuildKit v0.34.2 e il piano dello stadio, D-141):
  - un servizio C o C++ che si costruisce solo nel suo Dockerfile si costruisce come lo dichiara: `docker_build.py` riproduce lo stadio fino al build, e scip-clang legge il suo database;
  - ogni cartella di include è nominata dal pacchetto apk o dpkg che ne possiede la maggior parte dei file, e ciò che un'installazione CMake ha scritto (`install_manifest.txt`) dal progetto e dalla versione del suo CMakeCache;
  - un Dockerfile o un contesto nominati da una variabile del `.env` si usano solo quando danno un percorso tracciato del checkout, altrimenti sono un buco che nomina la variabile; gli argomenti restano `${NOME}`, e lo stadio riceve i valori solo nel container (`dotenv_env`, D-240);
  - le sorgenti apt in `http://` passano dal proxy, solo per l'archivio dichiarato (D-262); il driver Modal riporta ogni output con un tar a sé, che anche il tar di busybox sa fare.
- **Verifica:**
  - dal commit, currency sul `compose.yaml` e sul `.env` tracciati veri: C++ da `failed` (0 file) a `fresh`, 4 file su 4, 323 siti, 185 esterni con il pacchetto (`opentelemetry-cpp@1.28.0`, `libstdc++-dev`, `grpc-dev`, `musl-dev`); `premap.json` non contiene nessun valore del `.env`;
  - `tests/test_codebase_map_docker_build.py` (`test_a_cmake_unit_daodan_cannot_configure_is_built_and_indexed_in_its_dockerfile_s_stage`, `test_the_stage_names_each_system_header_folder_by_the_package_that_owns_most_of_its_files`, `test_on_modal_an_alpine_stage_brings_its_outputs_back`), `tests/test_codebase_map_premap_dockerfile.py` (`test_a_build_s_values_from_a_tracked_env_file_are_named_never_given`).
- **Stato:** risolto; restano 11 buchi su chiamate alla libreria C da C++ (D-272).
- **Note:** D-107, D-141.

#### D-136 C: 5.147 buchi `no-document`
- **Tag:** lingua c · area analizzatore · tipo completezza · origine conferma · strumento —
- **Descrizione:** conferma, C su 7 casi: 10.271 siti, 40,7 % di risposta; fra i buchi, no-document 5.147 e no-occurrence 941.
- **Spiegazione:** i 5.147 sono tutti di zlib, nei suoi 22 file C senza documento, ognuno con il suo motivo in `files.missing`: i file che il build predefinito non compila e i loro header. Sullo snapshot di HEAD, che in quei file conta 5.467 siti:
  - `examples/`, 9 file e 2 header, 3.446 siti: nessun build di zlib li compila;
  - `test/infcover.c`, 785: solo il target `cover` del Makefile, non `all`;
  - `contrib/infback9`, 2 file e 4 header, 633: nessun build;
  - `contrib/minizip/iowin32.c`, 352: il `Makefile.am` lo compila solo su WIN32 (`${iowin32_src}`);
  - `contrib/minizip/mztools.c`, 251: solo il build Autotools di minizip, non il suo `Makefile`;
  - gli 8 header non hanno siti.
- **Progetto e caso:** zlib (`51b7f2abdade`) — conferma, 16 novembre 2026.
- **Rimedio:** nessuno nel codice per examples/, contrib/infback9 e iowin32.c, che nessun build per Linux compila; dopo la conferma `60e3590b3` indicizza `test/infcover.c` (D-267) e `22dca6da8` `mztools.c` (D-134).
- **Verifica:** il 17 novembre, su Modal:
  - `test_on_modal_the_reference_sites_of_zlib_s_files_no_build_compiles` (`tests/test_codebase_map_clang_reader.py`), con `tests/modal_pytest.py`: lo snapshot di zlib dà i siti per file sopra, examples/ 3.446, contrib/infback9 633, iowin32.c 352 e contrib/testzlib 12, con test/infcover.c 785 e mztools.c 251, e la pre-mappa senza comandi l'unità `autotools-project` `minizip` con iowin32.c e mztools.c fra i sorgenti;
  - un giro di zlib sul codice di `f992db560`, da una copia di `git archive`: la pre-mappa con i comandi del modello e lo stadio di scip-clang indicizzano 45 file C su 66, `test/infcover.c` e `mztools.c` compresi;
  - i buchi `no-document` sono 4.443: i 4.431 attesi (examples/ 3.446, contrib/infback9 633, iowin32.c 352) e i 12 di `contrib/testzlib/testzlib.c`, che lo snapshot ora legge e che compilano solo i progetti Visual Studio di contrib/vstudio («no build compiles a file of contrib/testzlib»);
  - il giro è costato 0,012 USD (report di fatturazione di Modal).
- **Stato:** buco dichiarato (`no compile command`).
- **Note:** D-133, D-134, D-137, D-267.

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
- **Descrizione:** finale: 8 file Rust su 105 senza documento in hoppscotch, 6 con «no document in the index» e i due `posit.rs` con «no crate includes it»; 1 su 19 in semver (finale e conferma).
- **Spiegazione:** ognuno dei file mancanti è dietro un cfg falso su Linux, nessuno è un difetto dell'indicizzatore; ma un file caricato solo da file che un cfg lascia fuori diceva «no crate includes it», senza il file che lo carica né la causa.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** `1c68cbde4` (16 novembre, dynamic-step-2), `scripts/indexers/rust.py`: un file caricato solo da file che un cfg lascia fuori nomina il file che lo carica e quella causa (`LOADER_OFF`); i file dietro un `mod` con cfg falso dicono perché da `a3801beed` (D-237).
- **Verifica:**
  - `tests/test_codebase_map_indexers_reasons.py` (`test_a_rust_file_whose_loader_is_left_out_says_which_and_why`);
  - su Modal, con lo stadio di scip-rust nel container di Daodan su HEAD:
    - semver: 1 mancante, `tests/node/mod.rs`, `CFG_OFF` per `#![cfg(test_node_semver)]`, che solo `RUSTFLAGS` imposta;
    - hoppscotch: da 8 mancanti a 6, perché i due `desktop.rs` ora sono indicizzati (i build script girano nel container e impostano `cfg(desktop)`); i due `mobile.rs` sono `MOD_OFF` per `cfg(mobile)`, `ui/macos/mod.rs` e `ui/windows/mod.rs` `MOD_OFF` per `target_os`, i due `posit.rs` `LOADER_OFF` con il loro `mod.rs`.
- **Stato:** risolto: ogni file Rust mancante ha la sua causa, un cfg falso su Linux.
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

#### D-157 TypeScript: i tipi dei pacchetti sotto Yarn Plug'n'Play
- **Tag:** lingua typescript · area analizzatore · tipo completezza · origine commit · strumento Yarn, scip-typescript
- **Descrizione:** `d94f92470` lascia aperti «tipi sotto Yarn».
- **Spiegazione:** Yarn 2 e successivi dispongono i pacchetti con Plug'n'Play se `.yarnrc.yml` non imposta `nodeLinker`: l'installazione lascia `.pnp.cjs` e nessun `node_modules`. Il resolver di TypeScript non legge `.pnp.cjs`, così scip-typescript non nomina nessun simbolo di un pacchetto, e `typescript_types.py`, che cerca in `node_modules`, non aggiunge nessun `@types`. Misurato su Modal (android-sdk) con Yarn 4.9.1 da corepack e scip-typescript 0.6.2, su un progetto che importa `clsx` e `ms`: sotto pnp nessun simbolo di pacchetto; con `nodeLinker: node-modules`, `scip-typescript npm clsx 2.1.1 clsx.d.mts/clsx().`.
- **Progetto e caso:** TypeScript nel container — prova su Modal di android-sdk, 17 novembre 2026. Il corpus non ha un caso Plug'n'Play: js-yarn-berry imposta `nodeLinker: node-modules` e i suoi tipi si risolvono (esterni `@types/node`, `@types/ms`).
- **Rimedio:**
  - `18248f8d1` (17 novembre, android-sdk), `scripts/indexers/typescript.py` (`_prepared`): per ogni cartella di ripristino Yarn il cui `.yarnrc.yml` non imposta `nodeLinker: node-modules` o `pnpm`, la riga di ripristino dell'indice riceve `export YARN_NODE_LINKER=node-modules`: lo stesso lockfile disposto in `node_modules`, solo nella copia del container, con un buco `build_edited` per cartella che lo dice. Yarn 1 (senza `.yarnrc.yml`) e le cartelle già su `node-modules` non cambiano; il passo dinamico tiene il linker del progetto.
  - non committato (android-sdk): lo stadio dei fogli di stile segue la stessa regola, perché il suo script Tailwind trova il pacchetto del progetto solo in `node_modules/tailwindcss`: `css.tailwind_runner` dispone un progetto Plug'n'Play in `node_modules` con la nuova `typescript.node_modules()`, che ora chiama anche `_prepared`, e `css.index` restituisce quel buco `build_edited`.
- **Verifica:** `tests/test_codebase_map_indexers_ts_py.py` (`test_a_yarn_project_on_plug_n_play_is_laid_out_in_node_modules_for_the_index_and_says_so`); su Modal con Yarn 4.9.1 e la variabile: uscita 0, `node_modules/clsx` presente, nessun `.pnp.cjs`, `yarn.lock` identico byte per byte (`--immutable` regge); la suite intera verde (2.663). Per lo stadio dei fogli di stile, `tests/test_codebase_map_css_graph.py` (`test_a_yarn_project_on_plug_n_play_lays_its_tailwind_out_in_node_modules_and_says_so`), non committato. Nessun caso del corpus usa Plug'n'Play.
- **Stato:** risolto; la disposizione in `node_modules` per l'indice è il buco dichiarato `build_edited`.
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
- **Spiegazione:** è la regola di TypeScript stesso: dove un `include` prende sia `x.ts` (o `x.tsx`) sia `x.d.ts`, il programma tiene il `.ts` e lascia fuori il `.d.ts`; in memos `web/src/types/common.d.ts` accanto a `common.ts`, in hoppscotch `packages/hoppscotch-kernel/vite.config.d.ts` accanto a `vite.config.ts`. Provato su Modal con scip-typescript 0.6.2: `common.d.ts` ha il suo documento da solo e nessuno con `common.ts` accanto.
- **Progetto e caso:** hoppscotch, memos (`509e41bd1a1b`) — finale, 16 novembre 2026.
- **Rimedio:** `a57333c3b` (17 novembre, android-sdk), `scripts/indexers/typescript.py`: `missing()` lo dice e nomina il file tenuto.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_reasons.py`, `test_a_declaration_file_beside_a_typescript_file_of_its_name_says_typescript_leaves_it_out`) e la prova su Modal della Spiegazione.
- **Stato:** risolto: il file lo lascia fuori TypeScript, e il motivo lo dice.
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
- **Spiegazione:** un riferimento di classe, id o composes senza una regola che lo definisca è `no-rule` (`scripts/indexers/css.py`). Fra questi ci sono le classi Tailwind (`ee1e83fc8`) e quelle dei fogli dei pacchetti che solo il ripristino installa: il checkout non ha `node_modules` e il grafo non leggeva quei fogli (le classi `mu-*` di `@usememos/ui` in memos).
- **Progetto e caso:** il corpus — finale e conferma, 16 novembre 2026.
- **Rimedio:**
  - `efac75599` (17 novembre, ts-container-2), `scripts/indexers/css_tailwind.js`: i fogli di un pacchetto si trovano come li trova il build (D-163), e gli argomenti di `cn`/`clsx`, compresa la funzione fatta con `extendTailwindMerge`, sono siti di classe.
  - `aca4fd008` e `05135d74e` (17 novembre, ts-container-2), `scripts/indexers/css.py` e `scripts/indexers/css_packages.js`: i pacchetti che un import di un foglio o di uno script nomina e il checkout non ha si chiedono al container, nella stessa corsa di Tailwind e dopo lo stesso ripristino. `css_packages.js` legge solo file e riporta il `package.json` e i fogli di ciascun pacchetto, con i pacchetti che quei fogli importano. Il grafo li legge da una cartella temporanea che poi cancella, e trova il foglio di un pacchetto attraverso i suoi `exports`.
- **Verifica:** su Modal ai commit fissati, con il ripristino vero nel container emulato del test, il grafo sul checkout con i fogli riportati dal container risponde come il grafo sull'albero ripristinato: memos e fastapi senza differenze, hoppscotch con un buco `parameter` in più, non indagato. Rispetto a `efac75599`:
  - memos da 88,5 % a 96,7 % (7.100 su 7.339), `no-rule` da 652 a 81, `unresolved-import` da 10 a 0;
  - hoppscotch da 97,2 % a 97,3 % (16.228 su 16.676), `unresolved-import` da 26 a 7;
  - fastapi da 93,1 % a 93,3 % (1.957 su 2.098), `unresolved-import` da 2 a 0.
  Test in `tests/test_codebase_map_css_graph.py`: `test_the_restores_package_sheets_come_back_where_the_graph_looks_for_them`, `test_a_class_a_package_sheet_declares_is_answered_by_the_restores_copy_of_it`, `test_tailwinds_run_brings_back_the_packages_sheets_after_the_same_restore`, `test_a_package_sheet_is_found_through_the_packages_exports_as_its_build_finds_it`.
- **Stato:** aperto (ts-container-2). Restano i `no-rule` che nessun foglio definisce: i marcatori `group`/`peer` di Tailwind (memos 35, fastapi 5), gli id che nessuna regola prende (memos) e i 358 di hoppscotch, non ancora classificati. I `call` alle funzioni del progetto (memos 46) e i `parameter` sono del passo dinamico.
- **Note:** D-161, D-163.

#### D-163 hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto
- **Tag:** lingua css · area analizzatore · tipo correttezza · origine giro-2 · strumento —
- **Descrizione:** giro-2 e finale: «the stylesheet stage exited with code 1 without a report; see engine-pass.log».
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch — giro-2 e finale, 16 novembre 2026.
- **Rimedio:** `efac75599` (17 novembre, ts-container-2), `scripts/indexers/css_tailwind.js`: i fogli che Tailwind importa da un pacchetto si trovano come li trova `@tailwindcss/node`, dagli `exports` del pacchetto con le condizioni `style` e poi `default`, risalendo dalla cartella reale del foglio che importa; prima si cercavano per percorso nudo, e Tailwind 4 si fermava («cannot load stylesheet», misurato su memos).
- **Verifica:** dal commit, su Modal al commit fissato: hoppscotch da stadio fallito a fresh, 97,2 % dei siti con risposta (16.207 su 16.676); `tests/test_codebase_map_css_graph.py` (`test_a_sheet_tailwind_imports_from_a_package_is_found_as_its_build_finds_it`). Il commit non dice quale foglio fermava lo stadio di hoppscotch.
- **Stato:** risolto.
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

#### D-254 L'uv dell'host non era fissato
- **Tag:** lingua python · area host · tipo correttezza · origine review · strumento uv
- **Descrizione:** sull'host l'analisi Python usava l'uv che trovava sul PATH: con lo 0.7.19 di questo PC, la versione 3.14 di fastapi diventava l'interprete 3.14.0b3 (D-252) (riportato da team-lead il 16 novembre).
- **Spiegazione:** nel container uv è fissato allo 0.11.28 (`scripts/preparation.py:25`, `:64`); sull'host no.
- **Progetto e caso:** fastapi (`aabb90126964`) — review di team-lead, 16 novembre 2026.
- **Rimedio:**
  - `5e3757031` (16 novembre, python-env), `scripts/engine_tools.py` (`uv_binary`, `UV_ASSETS`): l'uv 0.11.28 scaricato una volta e controllato con lo sha256 del rilascio, mai quello del PATH; senza, Python è non disponibile con la causa. fastapi: deps.py letto da 3.14.6, grafo invariato.
  - `2057bbafc` (16 novembre, python-env), `scripts/engine_pass.py`: anche il runner degli stadi (`stage_command`) prendeva l'uv del PATH; ora usa `engine_tools.uv_binary()` con `uv_options()` (`--no-config` e la cache di Daodan), e il controllo della cache gira dalla cartella degli script, non dal progetto; senza il pin resta il ripiego sull'interprete di Daodan, mai il PATH.
- **Verifica:** `tests/test_codebase_map_resolve_edges.py` (`test_two_first_downloads_of_the_pinned_uv_at_once_both_end_with_it`).
- **Stato:** risolto da `5e3757031` e `2057bbafc`.
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
- **Stato:** risolto da `125ab9ebd` nella via principale e da `841cfe14f` in quella degli stadi del Dockerfile: `-idirafter` su musl, dove il driver di clang 21.1.8 mette gli header builtin dopo `/usr/include`, `-isystem` su glibc (`tests/test_codebase_map_docker_build.py`, `test_a_compiler_that_is_not_clang_reads_clang_s_builtin_headers`).
- **Note:** D-135 (otel-demo currency); il commit è successivo ai commit dei risultati di tutti i giri.

#### D-257 L'analizzatore Go eseguiva sull'host `go mod download` e il compilatore C
- **Tag:** lingua go · area analizzatore · tipo sicurezza · origine review · strumento go, git, gcc
- **Descrizione:** host-guard-2, nella sua revisione dell'host: l'analizzatore Go lanciava sull'host `go mod download` con l'ambiente intero dell'utente e senza `GOPROXY`, `GOVCS`, `GOENV` né `GOSUMDB`, così un modulo del progetto può far raggiungere a git il suo host (su Modal è registrato `git ls-remote https://github.com/<modulo>`); e per cgo lanciava il compilatore C dell'host (`gcc -E -dM … cgo-gcc-input.c`) (riportato da team-lead il 16 novembre).
- **Spiegazione:** `scripts/indexers/go.py:652` lancia `go mod download` nella copia del progetto con `env`; `_cgo` (`go.py:381`) chiede `go env CGO_ENABLED`, e Go prova il compilatore C che trova.
- **Progetto e caso:** analizzatore Go — revisione di host-guard-2, su Modal, 16 novembre 2026.
- **Rimedio:** `c13d51732` (16 novembre, host-guard-2), `scripts/indexers/go.py`: Go è come Rust (D-239): `NEEDS_CONTAINER` è vero, la preparazione ha i registri dichiarati e l'esecuzione è senza rete; senza container Go è non disponibile con la causa. scip-go si costruisce nella preparazione, i vincoli di build si leggono con `go list -f` nella stessa esecuzione, e il target è linux/amd64 da `preparation.GO`.
- **Verifica:**
  - `tests/test_codebase_map_indexers_go.py` (`test_nothing_of_go_starts_on_the_host`), a segni: go, la toolchain della riga `toolchain` del go.mod, git, gcc, cc, clang e scip-go finti non lasciano segni né processi;
  - dal commit, su Modal con gli strumenti veri (`benchmarks/project-model/modal_go_container.py`): prima il Go di Daodan partiva due volte sulla macchina, dopo nessun finto è chiamato e l'indice si costruisce nel container; sei casi Go della pipeline danno la stessa copertura dei risultati salvati, a meno delle classi di buchi nate dopo.
- **Stato:** risolto; gli aiuti Go dell'host rimasti senza chiamanti (`GO_ASSETS`, `user_config`, `go_toolchain`, `go_environment` di `scripts/engine_tools.py`, con la loro riesportazione in `resolve_edges` e il loro test) sono tolti da `f10cd344e`.
- **Note:** D-239, la stessa via per Rust; D-273, il workspace Go.
#### D-258 Vue e Svelte eseguivano sull'host l'installazione npm e il TypeScript del progetto
- **Tag:** lingua vue, svelte · area analizzatore · tipo sicurezza · origine review · strumento npm, typescript-language-server
- **Descrizione:** host-guard-2: `engine_tools.npm_modules` lancia sull'host `npm ci` con l'ambiente dell'utente e senza rifiutare i pacchetti git o da URL, e il `tsserver.js` del `node_modules/typescript` del progetto è girato sull'host (registrato su Modal) (riportato da team-lead il 16 novembre).
- **Spiegazione:** lo stadio di Vue e Svelte gira sull'host (`scripts/indexers/vue_svelte.py`, `NEEDS_CONTAINER` falso): installa i pacchetti del progetto con `npm_modules` (`scripts/engine_tools.py:247-250`, `env={**os.environ, ...}`), lega quel `node_modules` alla copia del progetto e chiede le chiamate a typescript-language-server, che carica il TypeScript che trova lì.
- **Progetto e caso:** analizzatore di Vue e Svelte — revisione di host-guard-2, su Modal, 16 novembre 2026.
- **Rimedio:**
  - `b9aeca1fb` (16 novembre, csharp-2): Vue e Svelte passano a scip-typescript nel container di Daodan (`scripts/languages/sfc.py` legge i template, `scripts/indexers/components.py` genera il TypeScript dei componenti con lo strumento del progetto, su Node fissato per sha256);
  - `590466b5d` (17 novembre, csharp-2): la vecchia via è tolta: `scripts/indexers/vue_svelte.py`, `scripts/language_servers.py` (`LspEngine`, `MirroredEngine`, multilspy), `npm_modules` con gli aiuti che usava solo lei (`npm_manifests`, `npm_key`, `package_directories`, i pacchetti di tipi e quelli locali) di `scripts/engine_tools.py`, `runtime.npm` e la loro riesportazione in `resolve_edges`; `runtime.Tool` tiene da sé l'installazione e lo specchio che usa scip-python; i due benchmark che chiamavano `npm_modules` (`benchmarks/inference-audit/adapters/ts_compiler.py`, `lang_css.py`) installano con npm nel loro container Modal.
- **Verifica:**
  - a segni: `svelte.config.js`, lo strumento Vue e svelte-kit lasciano un segno se eseguiti, e dopo un indice intero il progetto non ne ha (`tests/test_codebase_map_components.py`, `test_no_code_of_the_project_runs_on_the_host`);
  - `test_vue_and_svelte_have_no_engine_on_the_host` (stesso file): Vue e Svelte sono solo di scip-typescript, che chiede il container; nessuna voce del passo chiede un motore sull'host; `language_servers` e `npm_modules` non ci sono; una voce dello store lasciata dal vecchio motore non è fresca; senza container Vue è un buco con la causa (`tests/test_codebase_map_resolve_edges.py`, `CommandLineTests`);
  - giro `2026-11-17-vue-svelte` (script di `aca4fd008`): js-vue-pnpm, Vue fresco su 3 file su 3 con il `@vue/language-core` 2.2.12 del progetto; js-sveltekit, Svelte fresco su 2 file su 2 con il svelte2tsx 0.7.63 di scip-typescript e `svelte-kit sync` nella preparazione, `config_not_generated` sparito; hoppscotch non prova nulla: l'indice è trattenuto (D-283).
- **Stato:** risolto.
- **Note:** D-080 e D-159, i template non letti; D-283, l'indice di hoppscotch.

#### D-288 La versione di SvelteKit registrata era quella di npm
- **Tag:** lingua svelte · area analizzatore · tipo correttezza · origine corsa su un progetto · strumento npx, svelte-kit
- **Descrizione:** nel giro `2026-11-17-vue-svelte` js-sveltekit registra `svelte-kit sync` con la versione `11.19.1` (`indexer.generated`), che è quella di npm.
- **Spiegazione:** la riga della preparazione (`typescript.generator`) chiedeva `npx --no svelte-kit --version`: npm legge `--version` ovunque stia e risponde con la sua; dopo `--` il flag è del comando.
- **Progetto e caso:** js-sveltekit — giro `2026-11-17-vue-svelte` su Modal (script di `aca4fd008`), 17 novembre 2026.
- **Rimedio:** `710460616` (17 novembre, csharp-2), `scripts/indexers/typescript.py` `generator`: `npx --no -- svelte-kit --version` e `npx --no -- svelte-kit sync`.
- **Verifica:** `tests/test_codebase_map_components.py` (`test_the_generators_line_reads_the_kits_version_not_npms`): la riga com'è, con l'npx vero accanto a Node e un kit nel `node_modules/.bin` del progetto, dice `2.8.0`; rosso sul codice vecchio su Modal: `DAODAN-GENERATED app 11.19.1 svelte-kit sync`.
- **Stato:** risolto; la versione del kit nel record è da vedere al prossimo giro.
- **Note:** D-258.

#### D-289 Lo strumento Vue 1.x di un progetto non ha il plugin del linguaggio
- **Tag:** lingua vue · area analizzatore · tipo completezza · origine corsa su un progetto · strumento @vue/language-core
- **Descrizione:** hoppscotch tiene anche `@vue/language-core` 1.8.8 (`indexer.frameworks` del giro, accanto a 2.2.0 e 2.1.6, tutti del progetto), che non esporta `createVueLanguagePlugin`.
- **Spiegazione:** `scripts/indexers/components.cjs` usa lo strumento del progetto trovato dalla cartella del componente o dal pacchetto che ne dipende e chiama `createVueLanguagePlugin`, che c'è dalla 2.0; la 1.8.8 esporta `createVueLanguage` (unpkg, `out/languageModule.d.ts`), e il componente che la trova resta senza documento. Nel giro non si vede quali componenti: tutti i linguaggi di hoppscotch sono falliti con l'indice trattenuto (D-283).
- **Progetto e caso:** hoppscotch — giro `2026-11-17-vue-svelte` su Modal, 17 novembre 2026.
- **Rimedio:** `710460616` (17 novembre, csharp-2), `scripts/indexers/components.cjs` `vueTool`: uno strumento del progetto senza `createVueLanguagePlugin` lascia il posto al pin di Daodan (`components.PIN`, 3.3.14), e la voce dello strumento lo dice (`instead: ["1.8.8"]`).
- **Verifica:** `tests/test_codebase_map_components.py` (`test_a_projects_vue_tool_older_than_its_language_plugin_gives_way_to_daodans_and_is_said`): con una 1.8.8 del progetto che esporta solo `createVueLanguage`, il componente ha il file generato dalla 3.3.14 di Daodan e la voce dice `instead`; rosso sul codice vecchio su Modal: lo strumento usato è la 1.8.8 del progetto (`from: project`).
- **Stato:** risolto; su hoppscotch da vedere quando il suo indice si conserva (D-283).
- **Note:** D-258, D-283.

#### D-290 Vue: l'import di un componente e una lettura del template senza definizione
- **Tag:** lingua vue, typescript · area analizzatore · tipo completezza · origine corsa su un progetto · strumento scip-typescript, @vue/language-core
- **Descrizione:** js-vue-pnpm, giro `2026-11-17-vue-svelte`: `src/main.ts:4 App` (`import App from "@/App.vue"`) è il buco «no declaration of *.vue modules: the import is not typed», e `src/components/Counter.vue:9 n` (`@click="n++"`, `{{ n }}`) è `undefined-project-symbol`: mancano l'arco main.ts → App.vue e quello del template alla `const n`.
- **Spiegazione:**
  - L'import, visto nella registrazione di `tests/fixtures/components` (3.3.14): lo strumento Vue scrive il default del componente come espressione (2.2.12 `export default (await import('vue')).defineComponent({`, 3.3.14 `export default {} as typeof __VLS_export;`) e scip-typescript nomina l'import con un locale del file che importa, senza definizione (`src/main.ts:1 App` è `src/main.ts#local 0`); il modulo dell'import, `` src/`App.vue.ts`/ ``, l'indicizzatore lo definisce all'inizio del file generato con un intervallo vuoto, dove la mappa non arriva, e `components.rewrite` lo lasciava fuori. `Panel` va invece al modulo `` src/`Panel.svelte`/ ``, definito in `src/Panel.svelte:1`. Vale per ogni versione, e la causa che `typescript.classify` scriveva era sbagliata: l'import si risolveva al file generato.
  - La `n`: con la 2.2.12 di js-vue-pnpm il template diventa `__VLS_ctx.n++` e `( __VLS_ctx.n )`, una proprietà del tipo dell'istanza che il `setup` generato riempie (`n: n as typeof n`, codice fuori dalla mappa), e la sua definizione cade con il codice generato; con la 3.3.14 il template legge la `const` stessa (`label(__VLS_unwrap(n, …))`) e nella registrazione `src/App.vue:10 n` va a `src/App.vue:3`. Nella registrazione di `tests/fixtures/components-vue2` (2.2.12, scip-typescript 0.6.2, i tipi di vue 3.5.22): la `n` del template, `src/components/Counter.vue:9`, è `` src/components/`Counter.vue.ts`/n0: ``, definita solo alla riga 38 del file generato, `n: n as typeof n`, seguita dal riferimento a `` src/components/`Counter.vue.ts`/n. ``, la `const` di `src/components/Counter.vue:5`.
- **Progetto e caso:** js-vue-pnpm — giro `2026-11-17-vue-svelte`, 17 novembre 2026; codice generato con `@vue/language-core` 2.2.12 e 3.3.14 e registrazione di `tests/fixtures/components`, su Modal (`tests/modal_pytest.py`).
- **Rimedio:** l'import: `b5a2fceb4` (17 novembre, csharp-2): `scripts/indexers/components.py` `_occurrence` dà la definizione del modulo del file generato (vuota, al suo inizio) all'inizio del componente; `scripts/indexers/typescript.py` `hops` (`_default_import`): un nome che un import lega al default di un modulo, e che l'indice nomina con un locale senza definizione, va al modulo dove l'indice lo definisce (tag `import`); `fc650d77f` (17 novembre, csharp-2), `scripts/indexers/typescript.py` `classify`: dove nessun salto arriva, la causa è quella vera: TypeScript risolve l'import a nessun file e non trova dichiarazioni dei moduli `*.vue`, o a un modulo che l'indice non definisce. La `n`: `3027d663f` (17 novembre, csharp-2), `scripts/indexers/components.py` (`_held`): una proprietà del codice generato definita dove la mappa non arriva, e seguita sulla sua riga dal riferimento a un simbolo che la mappa definisce, è quel simbolo: la lettura del template è della `const`, come con la 3.x; `defineProps`: `55257959a` (17 novembre, csharp-2), `_held`: una definizione del codice generato che condivide il suo intervallo con il riferimento a un solo simbolo non definito lì è quel simbolo, e la chiamata del componente è della `defineProps` di Vue, esterna.
- **Verifica:** `tests/test_codebase_map_components.py` (`test_a_default_import_of_a_vue_component_reaches_it_as_one_of_a_svelte_component_does`): sulla registrazione `App` di `src/main.ts` va al modulo definito in `src/App.vue:1`, come `Panel` al suo; `tests/test_codebase_map_indexers_ts_py.py` (`test_a_name_bound_to_a_modules_default_export_the_index_leaves_unnamed_reaches_that_module`, e `test_a_name_an_import_of_a_component_binds_is_a_hole_with_the_cause` per le due cause); per la `n`, `tests/test_codebase_map_components.py` (`test_a_template_read_vue2_writes_through_its_setups_property_reaches_the_binding`): sulla registrazione 2.2.12 la `n` di `src/components/Counter.vue:9`, in `n++` e in `{{ n }}`, va alla `const` di `src/components/Counter.vue:5`; la registrazione si rifà su Modal con gli strumenti veri (`test_the_vue2_recording_is_what_its_tools_write_again`, `/opt/components-vue2` di `tests/modal_pytest.py`); per `defineProps`, `test_a_macro_vues_tool_declares_in_generated_code_is_vues_own` (stesso file): sulla registrazione 2.2.12 `src/components/Counter.vue:4 defineProps` è esterna, `@vue/runtime-core` `defineProps()`; i test delle correzioni rossi su Modal prima di esse.
- **Stato:** risolto; da vedere su js-vue-pnpm al prossimo giro (`src/main.ts:4 App` `project-value`, `src/components/Counter.vue:9 n` `project-value`, `src/components/Counter.vue:4 defineProps` esterna).
- **Note:** D-258; un import dentro un componente `.vue` resta fuori: `hops` e `classify` leggono solo i documenti JS e TS; `Counter.vue:4 defineProps` era `dangling-local`: la macro è dichiarata nel codice generato (`declare const { defineProps, … }: typeof import('vue');` nella 2.2.12), dove l'indice la definisce con un locale e, allo stesso intervallo, riferisce la `defineProps` di `@vue/runtime-core`.

#### D-294 Lo step `stack` non legge Maven, NuGet, Pub, Hex né Swift: JVM 0/42 e nessun framework .NET
- **Tag:** lingua java, kotlin, scala, csharp · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** su 34 fixture JVM e sui progetti .NET del corpus lo step non trova nessuno dei 42 framework attesi nel gruppo `jvm` (per nome 0/42), né i framework .NET di `mix-dotnet-central` e `real-svc-eshop`. Perduti: JUnit (20 fixture), JUnit Jupiter (10), Spring Boot (5), Spring MVC, Spring Data JPA e Hibernate (4 ciascuno), Spring Cloud Config, Netflix, Gateway, Spring WebFlux, Spring Security, Spring AI e Spring Boot Admin (`real-svc-petclinic-microservices`, `real-app-jhipster-sample`), Jackson (3), MapStruct (2), Lombok, picocli, TestNG, ScalaTest, Cats, Testcontainers (2), Thymeleaf, ArchUnit, Gatling, Resilience4j, Liquibase, Kotlin Multiplatform, Compose Multiplatform, Ktor, Exposed, Koin, kotlinx.serialization, Android, ASP.NET Core (3), Entity Framework Core (3), Blazor, .NET Aspire, .NET MAUI, xUnit, MSTest, NUnit, YARP, Duende IdentityServer e gRPC (NuGet). I servizi che ne vengono: PostgreSQL in `jvm-spring-boot-managed` e in `mix-dotnet-central`, H2 e HSQLDB (`real-app-jhipster-sample`, `real-app-kotlinconf`, `real-svc-petclinic-microservices`). 62 delle 140 fixture hanno `technologies` vuote (17 non hanno nemmeno un'unità di build).
- **Spiegazione:**
  - `service_registry.ECOSYSTEMS` (`scripts/service_registry.py:34-36`) traduce gli ecosistemi del grafo dei moduli nei soli `npm`, `pypi`, `crates`, `go`, `composer`, `rubygems` e `terraform`; una dipendenza `maven`, `nuget` o `pub` di un'unità non è un segno;
  - `data/service-registry.json` non ha nemmeno un segno per quegli ecosistemi: le sue chiavi di `signs.packages` sono `npm` (459 voci), `pypi` (264), `go` (202), `rubygems` (190), `composer` (169), `crates` (129), `docker`, `github-actions`, `terraform-resource` e `terraform`. Le sue regole vengono da stack-analyser (`data/REGISTRY-NOTICES.md`) e dal CNCF Landscape, che non hanno coordinate Maven;
  - nessun framework o libreria JVM o .NET ha dunque una voce con un segno: `junit`, `spring-boot`, `hibernate`, `aspnetcore` non sono nel registro (verificato per id e nome).
- **Progetto e caso:** il gruppo `jvm` (34 fixture), `mix-dotnet-central`, `real-svc-eshop`, `real-svc-petclinic-microservices`, `real-app-jhipster-sample`, `real-app-kotlinconf`; giro del 17 novembre 2026.
- **Rimedio:** `3b961646a` (17 novembre, l'ADR della mappa dei moduli, con jcode): il registro copre `maven`, `nuget`, `pub`, `hex` e `swiftpm` con `category`, e la pre-mappa tiene i nomi dei pacchetti dichiarati (`packages`).
- **Verifica:** `benchmarks/project-model/results/daodan_stack.json`, `frameworks_by_name` del gruppo `jvm`: 0/42 prima; il giro del 17 novembre sul codice `107d16779072c4cd`, dopo `3b961646a`: 36/42, e per unità 2/43 con 35 sbagliati (D-303).
- **Stato:** aperto: restano 6 framework JVM su 42 per nome, e l'unità a cui vanno (D-303).
- **Note:** è la stessa lacuna del registro sui servizi (`daodan_registry`, 14 novembre): 45 su 123 allora; 159 su 518 sulle 180 fixture dopo `3b961646a`.

#### D-295 Il `kind` `service` del registro fa servizi dei framework e degli strumenti di test
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** una voce `service` entra in `technologies.json` come servizio anche quando è un framework, un SDK o un test runner. Persi come framework e comparsi come servizio: Playwright (framework atteso in `mix-real-tududi`, `real-app-full-stack-fastapi`, `real-svc-eshop`, `real-svc-otel-demo`; servizio in più nelle prime tre), Firebase (`mix-poly-firebase`, `jvm-android-app-lib`, `real-app-kotlinconf`; servizio in più in `mix-poly-firebase`), OpenTelemetry (`real-svc-eshop`; servizio in più in `real-svc-eshop` e `real-svc-otel-demo`), CypressCI per Cypress (`real-app-jhipster-sample`, `real-svc-otel-demo`).
- **Spiegazione:**
  - le voci `playwright`, `firebase`, `opentelemetry` e `cypressci` hanno `kind: service` nel registro (`data/service-registry.json`), con segni `npm` e `docker` che un progetto usa come libreria o strumento;
  - `technologies.derive` copia il `kind` dell'entry nel record (`scripts/technologies.py:49-50`) e non ha altra classe: chi legge il record non distingue un database da un test runner.
- **Progetto e caso:** i progetti nominati, giro del 17 novembre 2026.
- **Rimedio:** una classe per voce (servizio esterno, framework, strumento) nel registro o nel record; il confronto con `expected.json` ne ha bisogno, perché lì i framework e i servizi sono due elenchi.
- **Verifica:** `results/daodan_stack.json`: `frameworks_by_name.missed` contiene `playwright` (4), `firebase` (3), `cypress` (2), `opentelemetry` (1); `services.extra` contiene `playwright` (3), `cypressci` (2), `opentelemetry` (2), `firebase` (1).
- **Stato:** aperto.
- **Casi sulle 180 fixture (17 novembre):** Celery (`real-stack-paperless-ngx` e `real-stack-wger`, `pyproject.toml`), Puppeteer e CypressCI (`real-stack-owncast`, `web/package.json`, `test/automated/browser/package.json`), Upstash (`real-stack-elk`, `package.json`), Playwright in 7 fixture `real-stack-*` (`actual`, `documenso`, `epic-stack` e altre) e, come framework atteso, in 4 (`playwright` in `frameworks_by_name.missed`).

#### D-296 Segni da prefisso di variabile o di pacchetto danno servizi che il progetto non usa
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** servizi in più che nessun servizio spiega:
  - Zoom: `ZOOM_STEP` (`real-app-memos`, `web/src/components/PreviewImageDialog.tsx:161`) e `ZOOM_KEY` (`mix-real-tududi`, `frontend/components/Project/Timeline/ProjectTimeline.tsx`) sono costanti di zoom dell'interfaccia;
  - Ghost: `GHOST_CLASS` (`real-app-memos`, `AttachmentListEditor.tsx:628`) è una classe di stile;
  - GCP: il pacchetto `passport-google-oauth20` (`real-app-hoppscotch`, `packages/hoppscotch-backend/package.json:70`) è il login con Google, non Google Cloud;
  - AWS: `aws4fetch` (`hoppscotch-common/package.json:61`, `hoppscotch-cli`) firma richieste a un S3 compatibile;
  - Postman: `postman-collection` (`hoppscotch-common/package.json:92`) legge un formato di file;
  - Discord: `DISCORD_INVITE_CODE` (`mix-real-tududi`, `backend/modules/landing/stats.js:11`); `expected.json` non lo conta;
  - Prometheus: `prom-client` (`real-svc-robot-shop`, `cart/package.json:20`); `expected.json` non lo conta.
- **Spiegazione:** `service_registry.recognize` cerca ogni prefisso di variabile d'ambiente di ogni voce con `\b(prefisso)[A-Z0-9_]*\b` su ogni riga di ogni file, e confronta i pacchetti con i modelli (`patterns`) delle voci; una costante che comincia con `ZOOM_` o `GHOST_` e un pacchetto che nomina un'azienda sono segni. Il segno non dice dove sta l'uso: un test su `env`/`pattern` richiede la voce e il file.
- **Progetto e caso:** `real-app-memos`, `mix-real-tududi`, `real-app-hoppscotch`, `real-svc-robot-shop`, 17 novembre 2026.
- **Rimedio:** da decidere; i prefissi corti (`ZOOM_`, `GHOST_`) e i modelli da nome d'azienda sono le sorgenti dei casi; l'etichetta di fiducia per segno (`env`, `package`) è già nel record.
- **Verifica:** `results/daodan_stack.json`, `services.extra`: `zoom`, `ghost`, `gcp`, `aws`, `postman`, `discord`, `prometheus`.
- **Stato:** aperto.
- **Note:** `aws`, `discord` e `prometheus` sono discutibili: il progetto può usare davvero un servizio; la parola è del proprietario del corpus.
- **Casi sulle 180 fixture (17 novembre):** Zoom da `ZoomAnimator.kt` (`real-stack-mattermost-mobile`) e da `signature-pad-upload.tsx` (`real-stack-documenso`); Segment da `segments.ts` (`real-stack-plausible`) e da `harnesstools/fork/tests.rs` (`real-stack-atuin`); Linear da `test/setup.ts` (`real-stack-mattermost-mobile`); Facebook da `test_recipe_create_from_ai.py` (`real-stack-mealie`); Square da `generate-content-alignment-test-pdf.mjs` (`real-stack-documenso`); Plausible da `tracker/test/support/…` (`real-stack-plausible`, il progetto stesso); GCP, AWS, Datadog, Vertex AI, Cloud KMS e Secret Manager da `package.json` di `real-stack-documenso` e `real-stack-nestjs-boilerplate`.

#### D-297 File di CI e di strumenti, ed esempi sotto la documentazione, contati come servizi
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** `renovate.json` (`mix-real-javapoet`) dà Renovate, `.travis.yml` (`mix-real-klaxon`) TravisCI, la CI di `mix-real-tinyxml2` GitHub Pages; in `mix-real-tududi` Caddy e Kubernetes vengono da `docs/examples/docker-compose.hosted.yml:17` e da `docs/examples/kubernetes/kustomization.yaml`, esempi di distribuzione sotto la documentazione che `expected.json` esclude (`traps` di corpus-mix).
- **Spiegazione:** `service_registry.recognize` applica `excluded` della pre-mappa solo ai segni di variabile d'ambiente e di host (`scripts/service_registry.py:153-158`, il giro sulle righe); i segni di pacchetto, di immagine dei file compose e di nome di file (`:140-148`) valgono in ogni percorso, anche in un albero che il corpus conta come documentazione. Per `mix-real-tududi` la pre-mappa ha le risposte registrate di `modal_premap.py`, con l'elenco `excluded` che quelle danno.
- **Progetto e caso:** `mix-real-javapoet`, `mix-real-klaxon`, `mix-real-tinyxml2`, `mix-real-tududi`.
- **Rimedio:** applicare `excluded` ai segni; tenere i servizi di CI fuori dai servizi del progetto.
- **Verifica:** `results/daodan_stack.json`, `services.extra`: `renovate`, `travisci`, `githubpages`, `caddy`, `kubernetes`.
- **Stato:** aperto.
- **Casi sulle 180 fixture (17 novembre):** Crowdin da `crowdin.yml` (6 fixture), Renovate da `renovate.json` (5), Codecov da `.codecov.yml` (3: `ctfd`, `paperless-ngx`, `wallabag`), Railway da `railway.toml` (`documenso`), Fly.io da `packages/docs/static/fly.toml` (`actual`), Netlify da `doc/netlify.toml` (`wallabag`, sotto la documentazione), Depot da `depot.json` (`atuin`), MariaDB da `.github/workflows/docker-build-static.yml` (`lldap`).

#### D-298 Servizi che nessun segno del registro raggiunge: 79 su 123 attesi
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** 44 servizi su 123 trovati (js 1/1, py 2/3, jvm 1/2, mix 14/33, real 26/84). I 79 persi hanno 59 nomi; 33 non hanno una voce nel registro (41 casi): SMTP (6 fixture), Cloud Firestore, Firebase Hosting, Firebase Authentication, Cloud Functions for Firebase, Firebase Analytics e Cloud Messaging, H2, HSQLDB, Azure Blob Storage, Azure Container Apps, OpenID Connect provider, Web Push, Apprise, Mailpit, Let's Encrypt, FastAPI Cloud, GitHub, Google e Microsoft OAuth, OAuth2, JHipster Control Center, Sessionize, Google Gemini, OpenAI API, flagd, OpenTelemetry Collector, OpAMP server, eBPF profiler, Instana EUM, OpenShift, DC/OS. Gli altri 26 hanno la voce, ma nessun segno nei file del progetto: PostgreSQL (7: `mix-dotnet-central`, `mix-edge-sql`, `mix-infra-k8s-helm`, `mix-infra-tool-versions`, `real-app-kotlinconf`, `real-app-memos`, `real-svc-eshop`), Redis (3: `mix-php-laravel`, `mix-ruby-rails`, `real-svc-eshop`), SQLite (2: `py-django`, `real-app-memos`), MySQL (2), RabbitMQ, Elasticsearch, Kafka, Envoy, Jaeger, OpenSearch, Grafana (2), Prometheus (2: `real-app-jhipster-sample`, `real-svc-otel-demo`), SonarQube, Heroku, Kubernetes, Istio, Docker Swarm, PayPal, Ollama, Azure OpenAI, Google Maps, Oracle Database, Microsoft SQL Server, Fluentd, Instana.
- **Spiegazione:**
  - nessuna delle due parti (voce e segno) esiste per i 33; il registro nasce da stack-analyser e dal CNCF Landscape, che non nominano SMTP o Web Push;
  - per gli altri il segno sta in un file che il registro non legge: una Helm `values.yaml`, un file `.sql`, una stringa di connessione, un driver Maven o NuGet (D-294), la libreria standard di Python.
- **Progetto e caso:** i 79 casi, `results/daodan_stack.json`, `services.missed`.
- **Rimedio:** voci nuove dove manca la voce; dove manca il segno, un lettore del file (compose, Helm, SQL) che il registro già riconosce come immagine.
- **Verifica:** `services.missed` per fixture; l'elenco dei nomi senza voce confrontato con `data/service-registry.json` per id e nome.
- **Stato:** aperto.
- **Casi sulle 180 fixture (17 novembre):** sulle 38 `real-stack-*` i servizi senza voce sono 189 casi (SMTP in 17, OpenID Connect 7, Amazon S3 7, LDAP 4, Google OAuth 3, Google Cloud Storage 3) e i framework senza voce 181 casi (Testify 4, Mockito 3, JUnit Jupiter 3, Entity Framework Core 3, Django REST framework 3, ASP.NET Core 3, Android 3, clap 3).

#### D-299 Framework che il registro non ha o non cerca nel manifest dell'ecosistema
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** per nome js e py non perdono nessun framework (10/10 e 4/4), sys ne perde uno (Chi, 1/2), mix 14 (17/31) e real 88 (39/127), JVM e .NET compresi (D-294); oltre a quelli:
  - nessuna voce nel registro: Chi (`mix-real-chi`, `sys-go-single`), Flutter (`mix-dart-flutter`), Sidekiq, Sinatra, Phoenix e Phoenix LiveView, Slim, SQLModel, Passport, Apollo Server, urql, Vue Router, AngularJS (2), Locust (2), React Native, FastMCP;
  - la voce c'è, il segno no: Rails (`mix-ruby-rails`: la voce `rails` ha solo il pacchetto `npm`, il Gemfile ha `gem "rails"`), Symfony (`real-svc-robot-shop`: lo mostra `ratings/html/src/Kernel.php`, non un `composer.json`), React Email (`real-app-full-stack-fastapi`);
  - Vue (`real-svc-petclinic-microservices`: i file statici dell'API gateway), Bootstrap (lì, un `pom.xml`).
- **Spiegazione:** il registro nasce da stack-analyser (D-294, D-298) e per un framework che non ha voce non c'è alternativa; un pacchetto cercato solo nell'ecosistema che la voce nomina (`rails` solo in `npm`) non si trova nel Gemfile.
- **Progetto e caso:** i progetti nominati, `results/daodan_stack.json`, `frameworks_by_name.missed`.
- **Rimedio:** voci e segni per gli ecosistemi della voce; per i framework che un file mostra e un manifest no (Symfony, Vue), nessun rimedio dal registro.
- **Verifica:** `frameworks_by_name.missed` per fixture; ricerca di id e nome nel registro.
- **Stato:** aperto.
- **Note:** «Tailwind» del registro e «Tailwind CSS» di `expected.json` (6 fixture: `mix-php-laravel`, `mix-real-tududi`, `real-app-full-stack-fastapi`, `real-app-hoppscotch`, `real-app-memos`, `real-svc-otel-demo`) non è un difetto dello step: la tecnologia c'è, lo spazio e la parola differiscono; l'alias `tailwind` → `tailwindcss` è per `score.py`, chiesto a pm-core.
- **Casi sulle 180 fixture (17 novembre):** sulle 38 `real-stack-*` i servizi senza voce sono 189 casi (SMTP in 17, OpenID Connect 7, Amazon S3 7, LDAP 4, Google OAuth 3, Google Cloud Storage 3) e i framework senza voce 181 casi (Testify 4, Mockito 3, JUnit Jupiter 3, Entity Framework Core 3, Django REST framework 3, ASP.NET Core 3, Android 3, clap 3).

#### D-300 Un segno del registro nomina solo il pacchetto della voce, non i suoi componenti
- **Tag:** lingua tutti · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** il framework c'è e il registro lo conosce, ma lo step non lo trova perché il progetto dichiara un componente del framework, non il pacchetto che la voce nomina:
  - Symfony: `real-stack-wallabag` (`composer.json:138`, `symfony/framework-bundle`) e `real-stack-symfony-demo` (`composer.json:25`); la voce `symfony` ha il solo segno `symfony/symfony`;
  - React Email: `real-stack-epic-stack` (`package.json:60`, `@react-email/components`); la voce `reactemail` ha `react-email`;
  - Express: `real-stack-nestjs-boilerplate` (`package.json:67`, `@nestjs/platform-express`); la voce `express` ha `express`;
  - Vite: `real-stack-mealie` (`frontend/package.json:52`, `@vitejs/plugin-vue`); la voce `vite` ha `vite`;
  - Protocol Buffers: `real-stack-atuin` (`crates/atuin-client/Cargo.toml:53`, il crate `prost`); la voce `protobuf` ha per `crates` il solo `protobuf`.
- **Spiegazione:** `service_registry.recognize` confronta il nome di ogni dipendenza dichiarata con i `packages` della voce per uguaglianza (`by_package.get((ecosistema, nome.lower()))`, `scripts/service_registry.py:142`) e con i `patterns`, che nelle cinque voci nominate sono vuoti. Un componente (`symfony/*`, `@react-email/*`, `@nestjs/platform-*`, `@vitejs/*`) non è mai uguale al pacchetto della voce.
- **Progetto e caso:** i progetti nominati, `results/daodan_stack.json`, `frameworks_by_name.missed`; giro del 17 novembre 2026. Le righe di `package.json` e `composer.json` sono lette dalla revisione fissata in `source.json` (raw di GitHub).
- **Rimedio:** da decidere: `patterns` per i prefissi di componente (`^symfony/`, `^@react-email/`, `^@nestjs/platform-express$`) nelle voci che ne hanno bisogno; la fonte delle regole (stack-analyser) non ha queste voci con i componenti.
- **Verifica:** `results/daodan_stack.json`: `symfony`, `reactemail`, `express`, `vite` e `protocolbuffers` in `frameworks_by_name.missed` delle fixture nominate, con la voce nel registro e il suo id assente da `ids`.
- **Stato:** aperto.

#### D-301 I requisiti Python si leggono solo da un file il cui nome comincia con `requirements`
- **Tag:** lingua python · area analizzatore · tipo completezza · origine benchmark · strumento Modal
- **Descrizione:** `real-stack-bakerydemo` dichiara Django in `requirements/base.txt:1` (`Django>=6.0,<6.1`) e lo step non lo trova: `django` non è fra i suoi `ids`, mentre la voce `django` del registro ha il pacchetto `pypi` `django`.
- **Spiegazione:** `_text_signs` (`scripts/service_registry.py:84`) legge come requisiti i file con `name.startswith("requirements") and name.endswith(".txt")`, dove `name` è il nome del file: `base.txt` dentro la cartella `requirements/` non lo è. Il lettore dei moduli non ha un'unità Python che nomini Django (`bakerydemo` non ha `pyproject.toml` con le dipendenze).
- **Progetto e caso:** `real-stack-bakerydemo` (`wagtail/bakerydemo` `890285b95dcf`), 17 novembre 2026.
- **Rimedio:** da decidere: leggere anche i file sotto una cartella `requirements/` (e le inclusioni `-r`).
- **Verifica:** `results/daodan_stack.json`, `real-stack-bakerydemo`: `django` in `frameworks_by_name.missed`; `requirements/base.txt:1` letto dalla revisione fissata.
- **Stato:** aperto.
- **Note:** non ho cercato quante altre fixture hanno i requisiti in un file con un altro nome.

#### D-302 La snapshot di jellyfin e di kuvasz non finisce in 900 secondi: la risoluzione degli import scorre ogni file
- **Tag:** lingua kotlin, csharp · area snapshot · tipo prestazioni · origine benchmark · strumento Modal
- **Descrizione:** `real-stack-jellyfin` (C#, 2.662 file) e `real-stack-kuvasz` (Kotlin, 1.709 file) non finiscono la snapshot in 900 secondi (1 CPU, 3 GB); le altre 178 fixture, fino a 354 s (`real-stack-owncast`), sì. Lo stesso ha fatto scadere i 2.400 secondi della funzione di `modal_premap.py` per le due (nessuna registrazione dei comandi di modello), e i 1.800 della funzione di `modal_stack.py` in due gruppi di fixture, con la perdita dei record dell'intero gruppo.
- **Spiegazione:** la pila dove le due stavano ferme a 720 secondi, nel record di `results/daodan_stack.json`: `snapshot_store.py:60 in _unpack` e `:184 in get_file`, chiamati da `import_resolution.py:460 in declaring`, `:494 in by_module_name`, `:530 in resolve`, `:570 in iter_resolved_imports` (la funzione comincia a `:547`). `by_module_name` chiama `declaring` per ogni import `.kt`, `.kts` o `.cs` che non ha dato un file (`scripts/import_resolution.py:492-496`), e `declaring` scorre tutti i file consentiti e ne decodifica la scheda dalla snapshot a ogni chiamata (`self.files.get(rel)`, `:456-463`): imports non risolti per file che li hanno (namespace del framework, `System.*`, `kotlin.*`) per il numero dei file, ciascuno con una decodifica. Non è misurato quante chiamate fanno i due progetti.
- **Progetto e caso:** `real-stack-jellyfin` (`jellyfin/jellyfin` `07bcec2e1f4e`) e `real-stack-kuvasz` (`kuvasz-uptime/kuvasz` `16c87cb4467b`), 17 novembre 2026.
- **Rimedio:** da decidere: un indice dei nomi dichiarati costruito una volta (nome → file) al posto della scansione.
- **Verifica:** `results/daodan_stack.json`: `real-stack-jellyfin` e `real-stack-kuvasz` hanno `error: "no answer in 900 s; stood at: ..."` con la pila.
- **Stato:** aperto.

Casi che il giro aggiunge alle schede esistenti (da accodare alla loro «Descrizione»):

#### D-303 Lo step `stack` dà un framework all'unità sbagliata: per il nome, o al padre invece che al sottomodulo
- **Tag:** lingua tutti · area analizzatore · tipo correttezza · origine benchmark · strumento Modal
- **Descrizione:** il giro dello stack del 17 novembre dopo l'ADR (codice `107d16779072c4cd`): i framework per unità trovati salgono da 268 a 364 su 1.001, ma gli sbagliati da 35 a 208; JVM 2 su 43 con 35 sbagliati. La tecnologia è giusta e l'unità no: atteso `:app`, dato `app` (jvm-android-app-lib); atteso `com-example:mapping-demo`, dato `mapping-demo` (jvm-maven-release-apt); atteso `:`, dato `hello-groovy` (jvm-gradle-groovy-wrapper).
- **Spiegazione:** `technologies.json` dà per modulo il `name` di `modules.json`, mentre l'unità della pre-mappa e delle risposte attese è il suo riferimento (`scripts/premap/module_graph.py:105`: Maven `groupId:artifactId`, Gradle `:percorso`); è la doppia identità che l'inventario del piano del 17 novembre chiama «contraddizione 1». Contati sul risultato, i 208 sono di tre tipi: 76 lo stesso modulo con un altro nome; 15 attendono la radice `:` e ricevono il nome del progetto; 117 vanno a un'altra unità (real-stack 65, real 44, mix 5, jvm 3), spesso la radice o il padre al posto del sottomodulo: kotlinconf `:backend`, `:core` e `:app:androidapp` dati a `kotlinconfapp`, mealie `frontend` a `mealie`, netbox `netbox/project-static` a `netbox`, JUnit Jupiter a `shop-parent` invece di `shop-service` (jvm-maven-multi-bom-profile). Il nome spiega quindi meno della metà: il resto è l'attribuzione del segno al modulo.
- **Progetto e caso:** le fixture jvm-*, real-* e real-stack-* — giro dello stack del 17 novembre, `results/daodan_stack.json`.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-294; l'ADR `docs/adr/2026-11-17-mappa-moduli-stack-e-reattivita.md`.

#### D-259 Un header `.h` di C++ letto come C
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** `meter_common.h` di otel-demo, un header C++ con un alias di namespace, un namespace anonimo e `std::`, era letto come C, e il parser C falliva (dal commit `bdfd7797b`).
- **Spiegazione:** `_CPP_HEADER_RE` (`scripts/languages/__init__.py`) non riconosceva alias e namespace anonimi, i nomi `std::` né le inclusioni della libreria standard C++; e il C può usare `namespace` come nome (`struct namespace {`, `p->namespace = x`), come ha misurato clang-reader.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — commit `bdfd7797b`, 16 novembre 2026.
- **Rimedio:** `bdfd7797b` (16 novembre), `scripts/languages/__init__.py`: `_CPP_HEADER_RE` riconosce alias e namespace anonimi, i nomi `std::` e le inclusioni della libreria standard C++ della regola di Linguist per `.h`; le forme del namespace contano solo quando `namespace` apre la riga.
- **Verifica:** solo test (`tests/test_codebase_map_clang_reader.py`, `test_a_header_is_cpp_only_when_its_text_has_what_c_lacks`); i casi C nuovi falliscono senza la correzione.
- **Stato:** risolto.
- **Note:** D-128, l'altro caso di un `.h` letto con il linguaggio sbagliato.

#### D-266 Le variabili locali di unità di traduzione diverse condividevano una chiave
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento scip-clang
- **Descrizione:** su tinyxml2, 129 chiavi di variabili locali erano in conflitto: un file che due unità di traduzione compilano dava alle locali di entrambe la stessa chiave (dal commit `ba8a1920f`).
- **Spiegazione:** `code_graph.Index` chiamava una locale per il suo documento e il suo nome locale, senza l'unità di traduzione da cui veniva.
- **Progetto e caso:** tinyxml2 (`9148bdf719e9`) — commit `ba8a1920f`, 16 novembre 2026.
- **Rimedio:** `ba8a1920f` (16 novembre, dynamic-step-2), `scripts/code_graph.py` (`Index._locals`): le locali di unità di traduzione diverse non condividono più una chiave.
- **Verifica:** dal commit, tinyxml2: chiavi in conflitto da 129 a 0; `tests/test_codebase_map_code_graph.py` (`test_a_file_two_translation_units_compile_keeps_each_local_apart`).
- **Stato:** risolto.
- **Note:** D-265.

#### D-267 zlib: il configure scritto a mano non girava prima di make
- **Tag:** lingua c · area analizzatore · tipo completezza · origine commit · strumento Make, Bear
- **Descrizione:** in zlib il Makefile della radice lo scrive il `configure` del progetto, che non è di Autotools: la pre-mappa leggeva il Makefile senza averlo fatto girare, e il build non indicizzava `test/infcover.c` (dal commit `60e3590b3`).
- **Spiegazione:** solo i configure di Autotools (D-134) giravano prima di make.
- **Progetto e caso:** zlib (`51b7f2abdade`) — commit `60e3590b3` di clang-builds, 16 novembre 2026.
- **Rimedio:** `60e3590b3` (16 novembre, clang-builds), `scripts/premap/make.py` (`configured`) e `scripts/indexers/clang_run.py` (`make`):
  - una cartella con un `Makefile.in` e un configure che non è di Autotools fa girare quel configure prima di leggere il Makefile, nel container senza rete;
  - un configure che fallisce è un buco `model_failed` con le sue parole;
  - il build C/C++ esegue lo stesso configure prima di make, sotto Bear.
- **Verifica:**
  - dal commit, zlib: le nove unità attese della radice sono dichiarate, e il build indicizza 18 file, `test/infcover.c` compreso;
  - `tests/test_codebase_map_premap_make.py` (`test_a_makefile_the_projects_own_configure_writes_is_read_once_the_configure_ran`, `test_a_configure_that_fails_is_the_folders_gap_with_its_own_words`).
- **Stato:** risolto.
- **Note:** D-133, D-134.

#### D-268 Un linguaggio che nessun build compila era `failed`
- **Tag:** lingua c, cpp · area analizzatore · tipo correttezza · origine commit · strumento —
- **Descrizione:** il C++ di zlib, che sta tutto in `contrib/iostream*` e che nessun build compila, era `failed` (dal commit `60e3590b3`).
- **Spiegazione:** un linguaggio con 0 file indicizzati fallisce con la causa (D-065), anche quando niente è fallito.
- **Progetto e caso:** zlib (`51b7f2abdade`) — commit `60e3590b3` di clang-builds, 16 novembre 2026.
- **Rimedio:** `60e3590b3` (16 novembre, clang-builds), `scripts/engine_pass.py` e `scripts/indexers/clang.py` (`nothing_failed`): quando nessun file di un linguaggio è indicizzato e tutti per motivi in cui niente è fallito (nessun build lo compila, nessuna unità lo include, il suo unico build non può girare qui), il linguaggio è `unavailable` con quel motivo.
- **Verifica:** solo test: `tests/test_codebase_map_honest_state.py` (`test_a_language_no_build_compiles_is_unavailable_not_failed`), `tests/test_codebase_map_indexers_clang.py` (`test_a_file_nothing_failed_for_is_said_so`).
- **Stato:** risolto.
- **Note:** D-065, D-133.

#### D-271 C e C++: buchi senza occorrenza senza la loro causa
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-clang
- **Descrizione:** rimisurati con gli header di GCC corretti (D-255), in un replay su Modal al commit di ogni fixture: zlib 161 buchi no-occurrence, tinyxml2 102, senza una causa nominata (dal commit `5cc88ec62`).
- **Spiegazione:** cause che `clang.unanswered` non conosceva: un argomento che l'espansione di una macro scarta (`Assert` e `Trace*` di zlib fuori da `ZLIB_DEBUG`, 127); un argomento il cui nome hanno due simboli nella macro (`DROPBITS(here.bits)` accanto al `bits` locale, 25); un `#ifdef` dentro un'espressione che l'albero del lettore colloca male (`gzlib.c:233`, `WIDECHAR`); una conversione a un tipo predefinito (`unsigned(100)`, 7); un `#ifdef` in un inizializzatore.
- **Progetto e caso:** zlib (`51b7f2abdade`), tinyxml2 (`9148bdf719e9`) — replay su Modal di clang-builds, 16 novembre 2026.
- **Rimedio:** `5cc88ec62` (16 novembre, clang-builds), `scripts/indexers/clang.py`: le cause nuove in `clang.unanswered`, l'`#ifdef` dentro un'espressione trovato dalle righe delle direttive.
- **Verifica:** dal commit, buchi senza causa: zlib da 161 a 0, tinyxml2 da 102 a 3 (due chiamate esplicite a un distruttore e un membro di un tipo dipendente in un template); `tests/test_codebase_map_code_graph.py` (`test_clang_the_index_names_no_occurrence_where_the_build_compiles_nothing`) e la fixture `tests/fixtures/code-graph/cpp/expected.json`.
- **Stato:** risolto; i 3 di tinyxml2 restano buchi con la sola causa, e `2ac9cdc69` li affronta (D-278).
- **Note:** D-236, D-272.

#### D-272 scip-clang non scrive occorrenze per le funzioni `extern "C"` in C++
- **Tag:** lingua cpp · area analizzatore · tipo completezza · origine prova su Modal · strumento scip-clang
- **Descrizione:** i 91 richiami alla libreria C di tinyxml2 (`printf`, `fopen`, `strlen`) restano buchi con la causa EXTERN_C, e currency ne ha 11 (dal commit `5cc88ec62`).
- **Spiegazione:** in C++ scip-clang v0.4.1 non scrive occorrenze per una funzione dichiarata in `extern "C"` (`SymbolFormatter.cc`, `getContextSymbol`: «Pending: LinkageSpecDecl»).
- **Progetto e caso:** tinyxml2 (`9148bdf719e9`), otel-demo currency (`b825c7c25726`) — commit `5cc88ec62` e `841cfe14f`, 16 novembre 2026.
- **Rimedio:** —: va corretto a monte (scip-clang, issue #544 e PR #548). Una build di scip-clang con patch, come scip-dotnet, è scartata da clang-builds: troppo pesante (circa 2,5 GB di download e 20 GB di disco).
- **Verifica:** —.
- **Stato:** aperto (strumento esterno: scip-clang #544, PR #548).
- **Note:** D-236, D-271.

#### D-273 Un workspace Go: `go mod download` fallisce nei moduli che richiedono un membro non pubblicato
- **Tag:** lingua go · area analizzatore · tipo completezza · origine commit · strumento go
- **Descrizione:** in `sys-go-workspace`, `go mod download` fallisce in ogni modulo che richiede un membro del workspace non pubblicato: tre buchi `restore_failed`, indice invariato (dal commit `c13d51732`).
- **Spiegazione:** la preparazione lancia `go mod download` nella cartella di ogni modulo, uno per volta (`scripts/preparation.py:269-270`); i membri del workspace (`go.work`: `./api`, `./svc`, `./tools`) si richiedono con versioni che nessun registro pubblica (`svc/go.mod`: `example.com/ws/api v0.0.0`). Il messaggio di Go è da verificare: il commit non lo riporta.
- **Progetto e caso:** sys-go-workspace — commit `c13d51732` di host-guard-2, 16 novembre 2026.
- **Rimedio:** —.
- **Verifica:** —.
- **Stato:** aperto (host-guard-2).
- **Note:** D-257.

#### D-277 Gli errori di compilazione di uno stadio del Dockerfile si perdevano
- **Tag:** lingua c, cpp · area analizzatore · tipo completezza · origine commit · strumento scip-clang, Docker
- **Descrizione:** il log di uno stadio restava nella cartella di lavoro che il passo toglie, quindi non si sapeva se il build nello stadio avesse dato errori: currency di otel-demo ne aveva 204 prima degli header builtin di clang, e nessun risultato lo diceva (dal commit `fcfb04338`).
- **Spiegazione:** la via degli stadi (D-135) non leggeva le diagnostiche di scip-clang, che la via principale conta in `clang_run._diagnostics`.
- **Progetto e caso:** otel-demo currency (`b825c7c25726`) — commit `fcfb04338` di android-sdk, 16 novembre 2026.
- **Rimedio:** `fcfb04338` (16 novembre, android-sdk), `scripts/indexers/clang.py`: `_staged` conta le diagnostiche di scip-clang nel suo `execute.log` come `clang_run._diagnostics`, e `_assembled` le mette nel `diagnostics` dell'indexer del risultato (`{errors, warnings, error_examples}`), che `engine-report.json` e `run.json` tengono.
- **Verifica:** dal commit, currency su Modal così com'è: 0 errori e 0 avvisi, contro i 204 di prima di `125ab9ebd` e `841cfe14f`; `tests/test_codebase_map_docker_build.py` (`test_the_compile_errors_scip_clang_reports_in_the_stage_are_on_record`).
- **Stato:** risolto.
- **Note:** D-135, D-255.

#### D-278 C++: una chiamata esplicita a un distruttore e un membro di un tipo dipendente
- **Tag:** lingua cpp · area analizzatore · tipo completezza · origine commit · strumento scip-clang
- **Descrizione:** su tinyxml2 restavano 3 buchi senza altra causa (D-271): due chiamate esplicite a un distruttore e l'accesso a un membro dentro un template (`tinyxml2.h:1994`, `returnNode->_memPool`) (dal commit `2ac9cdc69`).
- **Spiegazione:** in `node->~XMLNode()` scip-clang nomina la classe una colonna dopo `~`, mentre la chiamata del lettore inizia al `~`; il membro di un tipo dipendente clang lo risolve solo all'istanza, e l'indice non ne dice niente.
- **Progetto e caso:** tinyxml2 (`9148bdf719e9`) — commit `2ac9cdc69` di clang-builds, 16 novembre 2026.
- **Rimedio:** `2ac9cdc69` (16 novembre, clang-builds), `scripts/indexers/clang.py`: il passo `destructor_calls`, quando il `~` segue `.` o `->` (quindi non è una definizione), scrive al `~` il distruttore della classe che l'indice definisce; un accesso a un membro dentro un template di cui l'indice non dice niente ha la causa nuova `DEPENDENT`.
- **Verifica:** solo test (`tests/test_codebase_map_code_graph.py`, `test_clang_an_explicit_destructor_call_ends_at_the_destructor`); su tinyxml2 le due chiamate dovrebbero diventare archi e l'ultimo buco `DEPENDENT`, non misurato: lo dirà il prossimo giro reale.
- **Stato:** risolto per le chiamate ai distruttori; il membro di un tipo dipendente è il buco dichiarato `DEPENDENT`.
- **Note:** D-271.

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
- **Tag:** lingua python, typescript · area passo dinamico · tipo completezza · origine finale · strumento Playwright, git
- **Descrizione:** finale e conferma, fastapi: TypeScript e Python `not-run` (D-056, D-188).
- **Spiegazione:**
  - Python: fastapi 0.141.1 controlla `backend/app/frontend` (ignorata da git, scritta solo dal build vite del frontend: `frontend/vite.config.ts:10`) se `FASTAPI_ENV` non è `development` (`fastapi/routing.py:1888`); nel giro dotenv i test si fermavano alla raccolta con «RuntimeError: Frontend directory '/work/backend/app/frontend' does not exist», e il passo di test della CI imposta `FASTAPI_ENV=development` (`backend/scripts/test.sh`);
  - TypeScript: i test Playwright (`tests/auth.setup.ts`) vogliono l'intero stack in esecuzione, la lacuna di D-212 e D-261;
  - misurato nel giro di fastapi del 17 novembre, Python: i test si fermano ancora alla raccolta con la stessa RuntimeError, perché `FASTAPI_ENV` non arriva: la pre-mappa non ha nessun `ci_steps`. La seconda esecuzione di Renovate, i workflow letti con la sua libreria YAML (`EACH` in `scripts/premap/renovate.py`), è `results/2/stdout`, trattenuto come buco `output_withheld` (D-283): contiene `localhost` e `http://localhost:8000`, i valori di `SMTP_HOST` del `.env` e di `VITE_API_URL` di `frontend/.env`, entrambi tracciati, che `.github/workflows/test-docker-compose.yml:26` e `:28` scrivono (`curl http://localhost:8000/…`). Con quell'output si perdono i fatti di tutti i workflow, servizi e passi compresi. La cartella del frontend non viene da un passo della CI: `test-backend.yml` fa solo `docker compose up -d --wait db mailpit` (:29), `uv run bash scripts/prestart.sh` (:31) e `uv run bash scripts/tests-start.sh` (:34), che esegue `scripts/test.sh` con `FASTAPI_ENV=development`, e la pre-mappa legge quella variabile (`test_the_steps_a_job_runs_before_its_tests_are_facts_with_where_and_how_github_runs_them`): il difetto non è dei `ci_steps`, ma dell'output trattenuto per un valore così comune;
  - misurato nello stesso giro, TypeScript: i due script di Playwright (`frontend/package.json#scripts.test`, `bunx playwright test`, e lo `test` della radice, che lo filtra) non trovano il browser: «browserType.launch: Executable doesn't exist at /daodan/state/home/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell», 1 fallito (`tests/auth.setup.ts:6`) e 61 non eseguiti. La CI (`playwright.yml`) li esegue con `docker compose run --rm playwright bunx playwright test` nel servizio `playwright` (`compose.override.yml:77`), la cui immagine il progetto costruisce (`frontend/Dockerfile.playwright`, da `mcr.microsoft.com/playwright:v1.64.1-noble`, che porta il browser), dopo `docker compose run --rm backend bash scripts/prestart.sh`, contro il servizio `backend` a `http://backend:8000` (`PLAYWRIGHT_BASE_URL`, che toglie il webServer: `frontend/playwright.config.ts:88`), che serve il frontend costruito dallo stadio `frontend-build` di `backend/Dockerfile` (:16). Daodan avvia i servizi dalle loro immagini, in un pod senza rete (D-182, su un Docker vero in `b85aa1b9f`), ma nessuna immagine che il progetto costruisce (`service_unavailable`), e la strada degli stadi (`scripts/docker_build.py`) non riproduce `COPY --from` di un'immagine né i mount `bind` di `backend/Dockerfile` (:25, :44-45, :59-60). Con i fatti dei workflow la pre-mappa darebbe a quel passo la sua causa (`_composed_tests`: «inside the container of its Compose service playwright, which Daodan does not start»).
- **Progetto e caso:** fastapi — finale e conferma, 16 novembre 2026.
- **Rimedio:** `5148e8eb3`, `37c7ee093`; per Python `a46e5af7d`: le variabili del passo di test della CI arrivano ai test.
- **Verifica:**
  - su Modal `npm test` arriva a Playwright (`5148e8eb3`);
  - il giro reale di fastapi del 17 novembre (`benchmarks/project-model/results/pipeline/2026-11-17-fastapi-d292.json`, approvato dall'utente, tetto 1 USD), su un clone di `80c0b33c4`: 481 s, 0,036 USD. Le cause sopra vengono dai suoi log (`dynamic-record-python/out/tests-0.log`, `dynamic-record-javascript/out/tests-1.log`, `premap-runs/renovate/results/`) e dal buco `output_withheld` di Renovate.
- **Stato:** aperto: per Python la variabile della CI si perde con l'output trattenuto dei workflow; per TypeScript i test della CI girano nel servizio `playwright` di Compose, che Daodan non avvia (la lacuna di D-212 e D-261).
- **Note:** D-056, D-182, D-188, D-195, D-212, D-261, D-283, D-292.
#### D-198 I test di eShop non ancora girati
- **Tag:** lingua javascript, typescript, csharp · area passo dinamico · tipo completezza · origine finale · strumento npm, Playwright, dotnet
- **Descrizione:** finale, eShop: C# `no-observer`; JavaScript e TypeScript «no package.json of the project declares a test script (`scripts.test`): nothing is observed».
- **Spiegazione:** ciò che i test di eShop vogliono, dai file del progetto a `913acea66708` e dalla pre-mappa:
  - C#: l'osservatore arriva dopo il finale (D-241). Il piano ha 5 progetti di test su MSTest.Sdk 4.0.2 (`global.json#msbuild-sdks`) e Microsoft.Testing.Platform (`global.json#test.runner`, da cui `dotnet test --project`): Application, Basket, ClientApp, Ordering ed eShop.AppHost.UnitTests. I 4 `*.FunctionalTests` sono host Aspire (`Aspire.AppHost.Sdk/13.6.0`), `tests_need_container_engine`;
  - l'SDK è quello di `global.json`, 10.0.302 con `rollForward: latestFeature`, che la pre-mappa dichiara da Renovate e la preparazione installa con mise. Nessun workflow dichiara servizi, e nessun passo della CI precede test che la pre-mappa conosca: i servizi li avvia Aspire;
  - la CI su Linux (`pr-validation.yml`) fa `dotnet build eShop.Web.slnf` e `dotnet test --solution eShop.Web.slnf --no-build`; ClientApp.UnitTests (`UseMaui`) lo costruisce e lo prova solo il job su `windows-latest` di `pr-validation-maui.yml`, dopo i workload android, ios, maccatalyst e maui;
  - JavaScript e TypeScript: gli unici test sono quelli di Playwright, lo script `test:e2e` (`playwright test`) di `package.json`, che `playwright.yml` lancia con `npm run test:e2e` dopo `npx playwright install --with-deps chromium`. Il loro `webServer` è `dotnet run --project src/eShop.AppHost/eShop.AppHost.csproj`, l'host Aspire che avvia Redis, RabbitMQ e PostgreSQL (`ankane/pgvector`) come container (`src/eShop.AppHost/AppHost.cs`): lo stesso motore dei test funzionali, più un Chromium;
  - `scripts/premap/npm_tests.py` non conosceva Playwright fra i runner: lo script `test:e2e` non era un test dichiarato, e il buco diceva `no_test_command`, falso;
  - un webServer che non è un host Aspire gira, e il suo processo eredita il registratore da NODE_OPTIONS; ma senza `gracefulShutdown` Playwright ferma il gruppo di processi con SIGKILL (playwright.dev, «webServer»), e il registratore scrive all'uscita del processo (`scripts/dynamic/javascript_record.js`, `process.on('exit')` e SIGTERM): ciò che quel processo ha eseguito si perde.
- **Progetto e caso:** eShop (`913acea66708`) — finale, 16 novembre 2026.
- **Rimedio:**
  - per C# `15960a591` (16 novembre), l'osservatore di D-241;
  - per JavaScript e TypeScript `385387b93` (17 novembre): `scripts/premap/npm_tests.py` (v6) dà a `playwright test` il runner `playwright`, e non lo dichiara da uno script che non finisce (`--ui`, `--debug`);
  - poi `408c1e7ae` (17 novembre, android-sdk), `scripts/dynamic/javascript.py` (`web_server`) fa girare `playwright` come gli altri runner, salvo dove la configurazione di Playwright della cartella ha un webServer che è `dotnet run --project` di un host Aspire (`dynamic.dotnet.ASPIRE`): lì lo script è `tests_need_container_engine`, con la riga del webServer, come un progetto di test C# che è un host. Un altro webServer senza un `gracefulShutdown` che mandi SIGTERM è un buco `not_observed`, con la sua riga, e lo script gira; da D-292 il registratore scrive man mano, quel buco non c'è più e il webServer gira registrato fino alla sua ultima scrittura.
- **Verifica:**
  - `tests/test_codebase_map_dynamic_projects.py`, su Modal con `tests/modal_pytest.py`, snapshot e pre-mappa senza comandi di ogni progetto al suo commit: per eShop (`test_on_modal_eshop_s_tests_are_five_test_projects_and_the_rest_needs_a_container_engine`) `dynamic.dotnet.plan` dà i 5 progetti con `dotnet test --project <progetto> --no-build` e i 4 buchi `tests_need_container_engine`, nessun servizio e nessun passo della CI, e il piano JavaScript il buco `tests_need_container_engine` di `package.json#scripts.test:e2e` (`playwright.config.ts:87`);
  - il registratore sul webServer: con la chiusura predefinita di Playwright, il SIGKILL, il processo del server non lasciava nulla, la causa di D-292; da D-292 `test_on_modal_playwright_s_web_server_is_recorded_when_playwright_kills_it` (`tests/test_codebase_map_dynamic_javascript.py`, su Modal, `@playwright/test` 1.64.1), uno spec che chiama in HTTP un `node server.js` avviato dal webServer: il server lascia la sua ultima scrittura (`final: false`) con la chiamata di `lib.js` `answer` che la richiesta raggiunge, e con `gracefulShutdown: {signal: 'SIGTERM'}` scrive alla sua uscita;
  - il piano JavaScript di fastapi (`test_on_modal_fastapi_s_playwright_tests_run_with_their_web_server`): lo `test` della radice con npm e `frontend/package.json#scripts.test` con playwright, il cui webServer è `bun run dev`, senza buchi (con `408c1e7ae` c'era quello `not_observed` di `frontend/playwright.config.ts:88`, tolto da D-292); di tududi (`test_on_modal_tududi_s_jest_scripts_run`) i suoi due script di Jest, invariato;
  - il giro reale di eShop, il 17 novembre su Modal (approvato dall'utente, tetto 2 USD), su una copia di `36c7fb1e2` con `javascript.py` di questo rimedio: 828 s, costo 0,048 USD (report di fatturazione di Modal). C# osservato: 4 progetti girano, Application 13 test, Basket 8, Ordering 43, eShop.AppHost.UnitTests 8, 72 in tutto e nessuno fallito; 841 siti registrati, 800 uniti ai riferimenti in 42 file, 708 d'accordo con il grafo statico, 41 di un mock, 21 in conflitto, 73 `sites_ambiguous`. ClientApp.UnitTests è `tests_not_started`: «NETSDK1147: To build this project, the following workloads must be installed: maui-tizen». I 4 `*.FunctionalTests` e lo script `test:e2e` sono `tests_need_container_engine`; JavaScript e TypeScript `not-run` con quella causa;
  - `tests/test_codebase_map_dynamic_javascript.py` (`test_a_playwright_script_names_playwright_as_its_runner`, `test_playwright_s_tests_whose_web_server_is_an_aspire_app_host_need_a_container_engine`, `test_a_playwright_web_server_that_is_no_aspire_app_host_runs`, `test_fastapi_s_playwright_tests_run_as_before`); la suite intera su Modal: 2.607 passati, 65 saltati.
- **Stato:** buco dichiarato (`tests_need_container_engine`; ClientApp.UnitTests `tests_not_started`, il workload maui-tizen).
- **Note:** D-292; limite noto: lo `test` della radice di fastapi (`bun run --filter frontend test`) non è seguito nel pacchetto che filtra, e il suo runner resta `npm`. D-114, D-195, D-197, D-241.

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

#### D-270 `services_unreachable` non diceva a quale indirizzo nessun servizio rispondeva
- **Tag:** lingua javascript · area passo dinamico · tipo completezza · origine commit · strumento Jest
- **Descrizione:** il buco dell'osservatore JavaScript per le connessioni rifiutate non diceva a quale indirizzo locale nessun servizio dichiarato rispondeva: in tududi i test del frontend chiedono `127.0.0.1:80` (dal commit `e6a49324b`).
- **Spiegazione:** il buco contava le connessioni rifiutate senza i loro indirizzi.
- **Progetto e caso:** tududi (`71da9d7b34df`) — commit `e6a49324b` di test-services, 16 novembre 2026.
- **Rimedio:** `e6a49324b` (16 novembre, test-services), `scripts/dynamic/javascript.py` e `scripts/dynamic/__init__.py` (`_unanswered`): il buco porta `addresses` {indirizzo: conteggio}, e il dettaglio aggiunge gli indirizzi locali (localhost, 127.0.0.1, ::1, il nome o l'alias di un servizio) a cui nessun servizio che la CI dichiara risponde, con le porte dei container prese dai fatti. tududi: «…; no service the project's CI declares answers at 127.0.0.1:80 (postgres on 5432)».
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_a_refused_local_address_no_declared_service_answers_at_is_said_with_the_ports_they_answer_on`).
- **Stato:** risolto; restano buchi dichiarati: i test del frontend di tududi, che la sua CI non esegue e che falliscono su ogni macchina (`fetch is not defined` sotto jest-environment-jsdom 29, e l'axios relativo va all'URL di default di jsdom, porta 80), e il job Playwright di fastapi, `ci_step_not_run`: eseguirlo come la CI chiederebbe un'immagine da 944 MiB, un host fuori da ogni registro (bun.sh) e `ipc: host`, per osservare solo il runner Node.
- **Note:** D-185, D-213.

#### D-274 Un'esecuzione di test che la CI non esegue non lo diceva
- **Tag:** lingua tutti · area passo dinamico · tipo completezza · origine commit · strumento GitHub Actions
- **Descrizione:** un passo di test della CI senza variabili non era un fatto, così un'esecuzione di test che nessun workflow esegue non si distingueva da una che la CI esegue: in tududi `scripts.frontend:test` (dal commit `a46e5af7d`).
- **Spiegazione:** `renovate._ci_steps` scriveva un fatto solo per un passo di test con variabili (D-260).
- **Progetto e caso:** tududi (`71da9d7b34df`) — commit `a46e5af7d` di test-services, 16 novembre 2026.
- **Rimedio:** `a46e5af7d` (16 novembre, test-services), `scripts/premap/renovate.py` e `scripts/dynamic/__init__.py`:
  - `renovate._ci_steps` scrive un fatto `{declared_in, tests, name, test: true}` per ogni passo di test, con `env` e `computed` solo quando il passo li ha;
  - `dynamic.ci_steps` aggiunge un buco `tests_not_in_ci` per un'esecuzione che nessun fatto nomina, quando i job della CI eseguono altri test del progetto: «nessun workflow che Daodan legge esegue questi test (la sua CI esegue …): un loro fallimento è uno che la CI del progetto non vede mai»; se nessun workflow esegue test, non dice niente.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_a_test_step_without_variables_is_a_fact_too_so_a_run_no_workflow_runs_is_said`).
- **Stato:** buco dichiarato (`tests_not_in_ci`).
- **Note:** il commit è un feat. D-260, D-270.

#### D-292 Un processo ucciso con SIGKILL non lasciava registrazioni
- **Tag:** lingua javascript, typescript · area passo dinamico · tipo completezza · origine prova su Modal · strumento Playwright, Node
- **Descrizione:** il registratore JavaScript scriveva ciò che aveva visto solo all'uscita del processo (`process.on('exit')`) e al SIGTERM: un processo ucciso con SIGKILL, come Playwright ferma il suo webServer senza `gracefulShutdown`, non lasciava nulla, e da `408c1e7ae` il webServer era un buco `not_observed` (D-198).
- **Spiegazione:** un SIGKILL non esegue alcun gestore.
- **Progetto e caso:** osservatore JavaScript, la prova del webServer di Playwright su Modal (D-198) — 17 novembre 2026.
- **Rimedio:** `750a7aa36` (17 novembre, android-sdk)
  - `scripts/dynamic/javascript_record.js` scrive mentre il processo gira: ogni secondo (`EVERY`) in cui ha registrato qualcosa di nuovo, mai prima di dieci volte la durata dell'ultima scrittura, il file intero in un `.tmp` rinominato al suo posto, con `final: false`; all'uscita ancora, con `final: true`;
  - `scripts/dynamic/javascript.py` toglie il buco `not_observed` del webServer, che ora gira registrato, e dà `processes_killed` per i file con `final: false`: ciò che ogni processo ha eseguito dopo la sua ultima scrittura non è registrato;
  - poi `1fd31c503` (17 novembre, android-sdk) le `stats` del registratore dicono le scritture fatte mentre il processo girava e i loro ms (`writes`, `writing_ms`); le scritture corrono sul ciclo degli eventi, e un processo che non gli cede mai scrive alla sua uscita.
- **Verifica:**
  - `tests/test_codebase_map_dynamic_javascript.py`: `test_a_process_killed_with_sigkill_leaves_the_calls_it_made_before` (un server Node ucciso con SIGKILL lascia le chiamate fatte prima, anche una fatta dopo la prima scrittura; sul registratore di prima fallisce senza alcun file), `test_on_modal_playwright_s_web_server_is_recorded_when_playwright_kills_it` (il webServer di Playwright, su Modal), `test_a_playwright_web_server_that_is_no_aspire_app_host_runs`, `test_fastapi_s_playwright_tests_run_as_before` e il caso `processes_killed` di `test_what_did_not_happen_is_a_gap_with_its_cause`;
  - da questo rimedio gli 8 test del registratore sotto un Node vero girano su Modal: `tests/modal_pytest.py` dà all'immagine il @babel/core 7.29.7 del registratore (`DAODAN_TEST_BABEL`); prima si saltavano;
  - il costo, `test_the_writes_while_a_process_runs_take_less_than_a_tenth_of_its_time`: 3.000 funzioni, ciascuna chiamata da un suo sito, in cinque ondate di 0,6 s che cedono al ciclo degli eventi, come un server o un runner; 3 scritture mentre il processo gira, 18 ms su 3.074 (0,6 %), per un file di 477 KB con 3.009 siti, e il test chiede meno di un decimo, il limite che il registratore si dà; gli 8 test del registratore 5,10 s prima, 5,05 e 4,94 s dopo; la suite intera su Modal: 2.630 passati, 57 saltati;
  - il giro reale di fastapi (`benchmarks/project-model/results/pipeline/2026-11-17-fastapi-d292.json`, approvato dall'utente, tetto 1 USD), su un clone di `80c0b33c4` con il driver del repository e le sue due app rinominate perché il costo sia il suo: 481 s, 0,036 USD (report di fatturazione di Modal). I test di Playwright non partono, senza il browser (D-197): nessuna chiamata registrata, quindi né le chiamate del server del webServer né `processes_killed`, che restano provate da `test_on_modal_playwright_s_web_server_is_recorded_when_playwright_kills_it`. Il `code` che il giro registra è sbagliato: il clone era sparso (`git sparse-checkout`), e `code()`, che con il suo indice temporaneo vi fa `git add -A`, conta 974 percorsi diversi dal commit, fra cui file uguali al commit; nel clone `git diff-index HEAD` dava solo `modal_pipeline.py`, con i nomi delle due app. Un giro così si fa da un clone pieno.
- **Stato:** risolto; ciò che un processo ucciso esegue dopo l'ultima scrittura resta il buco dichiarato `processes_killed`.
- **Note:** D-198.

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
- **Tag:** lingua tutti · area servizi · tipo correttezza · origine review · strumento Renovate, GitLab CI
- **Descrizione:** il lettore della pre-mappa trasformava un `!reference` di GitLab CI in fatti inventati: `services: !reference [.setup, services]` diventava due servizi chiamati «.setup» e «services», e `- !reference [.setup, script]` due righe di script, senza buco (dal commit `940f69e66`).
- **Spiegazione:** provato su Modal con yaml 2.9.1 come lo esegue Renovate: `!reference` è solo un avviso (`TAG_RESOLVE_FAILED`), l'uscita è 0 e il JSON stampa il percorso del riferimento come valore.
- **Progetto e caso:** pre-mappa della CI — segnalato da team-lead, commit `940f69e66` di test-services, 17 novembre 2026; nessuna fixture ha un `.gitlab-ci.yml`.
- **Rimedio:** `940f69e66` (17 novembre, test-services), `scripts/premap/renovate.py`: il lettore stampa ogni `!reference` come `{"!reference": [percorso]}` (il `--visit` della CLI) e `renovate._referenced` li risolve come GitLab quando carica il file, prima di `extends`, annidati fino a dieci livelli; un percorso che il file non ha, o che si annida oltre dieci, è un buco `reference_not_found`, e il job non dichiara servizi né passi.
- **Verifica:** `tests/test_codebase_map_dynamic_services.py` (`test_a_gitlab_reference_is_the_section_it_names_and_one_not_in_the_file_is_a_gap`; su Modal `test_on_modal_renovate_s_yaml_library_with_the_reader_s_visitor_marks_each_gitlab_reference`).
- **Stato:** risolto; un riferimento che il file non risolve è il buco dichiarato `reference_not_found`.
- **Note:** D-216, D-275.
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
- **Spiegazione:** anche in distribuzioni diverse i due motori condividono la rete della VM di WSL, e ciascuno ricostruisce all'avvio e toglie all'arresto la stessa tabella nftables `kiri` (`crates/kiri-init/src/linux/net.rs`).
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** deciso il 16 novembre (team-lead, riportato da android-sdk), senza cambiare codice: Daodan usa il motore dell'utente quando risponde e non avvia mai il proprio accanto a un Kiri attivo, che non riavvia, non ferma e non riconfigura mai.
  - la lacuna è il buco che `container.own_engine` solleva (`scripts/container.py:484-487`, da `2adc041f1`): «another Kiri engine runs in WSL (<distribuzione>); Daodan's would reset its network rules», con il rimedio «open that Kiri so that `docker` answers, or stop it with wsl --terminate <distribuzione>»;
  - la riga della spec passa da «Da decidere» a «Deciso il 16 novembre 2026» come **Kiri dell'utente** (`docs/specs/2026-11-12-passo-dinamico.md`, `1c68cbde4`).
- **Verifica:** solo test, da `1c68cbde4` (`tests/test_codebase_map_container.py`, `FakeEngineTest.test_beside_a_running_kiri_of_the_user_daodan_starts_no_engine_and_says_why`): con il Kiri dell'utente attivo e nessun docker che risponde, il buco lo nomina, a WSL si chiede solo `-l --running -q`, niente si importa, si avvia o si scarica, e `engine_home` non si raggiunge mai; la suite del container dà 45 passati e 4 saltati.
- **Stato:** buco dichiarato (buco del motore Kiri).
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

#### D-269 Due installazioni dello stesso strumento si toglievano i file a vicenda
- **Tag:** lingua tutti · area host · tipo correttezza · origine commit · strumento uv, Node, scip-python, Pyright, npm
- **Descrizione:** una prova in parallelo di python-env: due prime installazioni dello stesso strumento (il server e il passo, o due worker) condividevano la cartella `.partial` e si toglievano i file a vicenda: 3 fallimenti su 3 su una macchina nuova, «File exists: …/engines/node/.v22.23.4.partial» (dal commit `2057bbafc`).
- **Spiegazione:** ogni installazione scriveva in una cartella dal nome fisso accanto a quella definitiva.
- **Progetto e caso:** cartella condivisa degli strumenti, macchina nuova — commit `2057bbafc`, 16 novembre 2026.
- **Rimedio:**
  - `2057bbafc` (16 novembre, python-env), `scripts/engine_tools.py:568` (`publish`): ogni installazione ha la sua cartella, e resta la prima pubblicata; la usano `LspEngine._install` (Node, scip-python, Pyright, ogni `runtime.Tool`) e `uv_binary`;
  - `24e6682c9` (16 novembre, python-env): anche `npm_modules` installa con `publish()`, e un npm fallito dice ancora perché; `download` scrive a ogni tentativo un file parziale suo (`mkstemp` accanto alla destinazione); la toolchain Go dell'host non c'è più (Go solo nel container, `c13d51732`, D-257).
- **Verifica:** solo test: `tests/test_codebase_map_resolve_edges.py` (`test_two_first_installs_of_one_release_at_once_both_end_with_it_installed`, `test_two_first_downloads_of_the_pinned_uv_at_once_both_end_with_it`, `test_two_first_installs_of_one_project_s_packages_at_once_both_end_with_them`, `test_two_downloads_of_one_file_at_once_both_end_with_it`); i due di `24e6682c9` fanno partire la seconda installazione a metà della prima, e prima fallivano con «FileNotFoundError …/cache/npm/.<chiave>.partial/node_modules» e con 3 scaricamenti invece di 2.
- **Stato:** risolto da `2057bbafc` e `24e6682c9`.
- **Note:** D-254, dallo stesso commit.

#### D-275 I passi della CI si leggevano solo nei workflow con servizi o Compose
- **Tag:** lingua tutti · area servizi · tipo completezza · origine commit · strumento GitHub Actions, GitLab CI
- **Descrizione:** il lettore dei workflow girava solo quando un workflow nominava servizi o Compose, quindi i passi e i passi di test della maggior parte dei job non si leggevano mai; e di GitLab si leggevano solo i servizi, non `before_script` e `script` (dal commit `bd133fe94`).
- **Spiegazione:** la pre-mappa chiamava il lettore dei workflow per i servizi; i passi della CI (D-213) e i passi di test (D-260, D-274) sono arrivati dopo, nello stesso lettore.
- **Progetto e caso:** pre-mappa della CI — commit `bd133fe94` di test-services, 16 novembre 2026.
- **Rimedio:** `bd133fe94` (16 novembre, test-services), `scripts/premap/renovate.py`:
  - il lettore gira per ogni workflow con un passo `run:` o una pipeline con `script:`;
  - `renovate._gitlab_steps` legge `before_script` (suo o ereditato da `default:`) e `script`, con le liste annidate appiattite: la prima riga che esegue una voce `tests` è il fatto del passo di test, con le variabili del job come le espande il runner e quelle che la riga imposta; le righe prima formano un passo (una shell, cartella `.`, le righe unite, le variabili), che ha una `cause` se una di loro avvia Compose.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_renovate_reads_gitlab_s_pipeline_where_it_names_services_includes_files_or_runs_scripts`, `test_the_lines_a_gitlab_job_runs_before_its_tests_are_one_step_and_its_test_line_the_test_step`); nessuna fixture ha un `.gitlab-ci.yml`. Effetto atteso nel prossimo giro, non misurato: i progetti con CI ma senza servizi (chi, semver, zlib, javapoet, klaxon, tinyxml2, eshop, jhipster, kotlinconf, memos, …) eseguono i passi dei loro job prima dei test, alla fine della preparazione, il cui tempo non è ancora misurato.
- **Stato:** risolto.
- **Note:** il commit è un feat. D-213, D-216, D-217, D-260, D-274.

#### D-279 I valori del `.env` non arrivavano all'esecuzione di uno stadio
- **Tag:** lingua tutti · area container · tipo completezza · origine commit · strumento Docker, BuildKit
- **Descrizione:** `dotenv_env` arrivava solo alla preparazione, quindi un `RUN` del build che leggeva un `ARG` dal `.env` lo trovava vuoto (dal commit `4a999670e`).
- **Spiegazione:** BuildKit dà un `ARG` a ogni `RUN` dello stadio; la riproduzione dello stadio (D-135) passava i valori del `.env` (D-240) solo alla fase con rete.
- **Progetto e caso:** container — commit `4a999670e` di test-services, 16 novembre 2026.
- **Rimedio:** `4a999670e` (16 novembre, test-services), `scripts/container.py` e `benchmarks/project-model/modal_pipeline.py`: l'esecuzione riceve gli stessi valori della preparazione, sempre mai registrati e mascherati nei log e negli output di testo.
- **Verifica:**
  - `tests/test_codebase_map_dynamic_services.py` (`test_the_variables_a_caller_names_reach_both_phases_with_their_values_and_never_what_the_run_keeps`): con il motore finto l'esecuzione scrive `arg=$SECRET_KEY` in un file che torna mascherato;
  - su Modal (`test_on_modal_a_stage_s_arg_from_the_tracked_env_reaches_both_sandboxes_and_nothing_the_run_keeps`): il file letto dice «prep=[.env:VERSION] arg=[.env:VERSION]», e il valore non compare da nessuna parte.
- **Stato:** risolto.
- **Note:** D-135, D-240.

#### D-283 Un valore del `.env` restava negli output JSON e binari e dentro parole più lunghe
- **Tag:** lingua tutti · area container · tipo sicurezza · origine commit · strumento —
- **Descrizione:** il mascheramento dei valori del `.env` (D-240, D-279) copriva solo i log e gli output di testo (`.log`, `.txt`) e solo le parole intere: un valore compilato nel build (`-DVERSION=…`) restava in un `compile_commands.json` o in un indice SCIP, e `-DVERSION=1.28.0x` restava leggibile (dai commit `a41823a06` e `124c63440`).
- **Spiegazione:** la regola del proprietario: nessun valore del `.env` arriva a fatti, risultati, archivi o testi conservati di Daodan.
- **Progetto e caso:** container — commit `a41823a06` e `124c63440` di test-services, 17 novembre 2026.
- **Rimedio:** `scripts/container.py`, test-services:
  - `a41823a06`: gli output JSON si mascherano restando JSON valido; un output binario non si tocca mai a byte: se vi compaiono i byte di un valore si trattiene come buco `output_withheld`, che nomina la variabile e l'output, e non si conserva;
  - `124c63440`: un valore di quattro o più caratteri si maschera dovunque compaia, uno più corto solo come parola intera (`/app/` sì, `application` no), e booleani e numeri fino a cinque cifre restano; ogni esecuzione lo dice una volta con un buco `mask_partial` che nomina quelle variabili, e un output di testo con un valore dentro una parola si maschera e si tiene.
- **Verifica:**
  - `tests/test_codebase_map_dynamic_services.py` (`test_an_output_that_holds_a_value_after_masking_is_withheld_with_a_gap_and_off_the_record`, `test_a_run_says_once_which_values_it_masks_only_as_whole_words_or_not_at_all`);
  - dal commit `a41823a06`, su Modal con g++ e `-DVERSION=<valore>`: il database di compilazione torna mascherato e l'indice che porta il valore è un buco.
- **Stato:** risolto; i valori corti, i booleani e i numeri non mascherati sono il buco dichiarato `mask_partial`.
- **Note:** D-240, D-279.

#### D-291 I valori di un `.env.example` facevano trattenere l'indice di un intero progetto
- **Tag:** lingua typescript, javascript, vue · area container · tipo completezza · origine corsa su un progetto · strumento scip-typescript
- **Descrizione:** nel giro `2026-11-17-vue-svelte` l'indice scip-typescript di hoppscotch (`55908a76a1d0`) è un buco `output_withheld`: contiene i valori di `.env.example` (`PROXY_APP_URL`, `VITE_BASE_URL`, `VITE_SHORTCODE_BASE_URL`), e TypeScript, JavaScript e Vue dell'intero progetto si perdevano.
- **Spiegazione:** la regola di D-283 trattava come segreto ogni `.env*` tracciato, anche i file d'esempio, che il progetto pubblica proprio perché chiunque li legga. Il proprietario ha deciso che i file d'esempio non si mascherano.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`) — giro `2026-11-17-vue-svelte`, 17 novembre 2026.
- **Rimedio:** `e674c007b` (17 novembre, test-services), `scripts/container.py`: `example(name)` riconosce `.env.example`, `.env.sample`, `.env.template` e `.env.dist`, anche con un nome in mezzo (`.env.local.example`), in ogni maiuscola; `secret(values)` toglie i loro valori prima di `masker`, `partial` e `scrubbed`, in `run_in_container` e in `benchmarks/project-model/modal_pipeline.py`. I file d'esempio entrano nella copia del container come prima; un valore che sta anche in un `.env` vero resta mascherato, col nome della variabile del file vero.
- **Verifica:** `tests/test_codebase_map_dynamic_services.py` (`test_an_example_env_file_is_public_by_its_name_and_only_the_true_files_values_are_secret`, `PodTest.test_an_example_env_file_s_values_are_public_and_an_output_that_holds_them_is_kept`: un indice binario con i valori di `.env.example` e `.env.local.sample` si conserva com'è, uno col valore del `.env` vero resta trattenuto, un valore comune ai due si maschera).
- **Stato:** risolto.
- **Note:** D-283.

### Benchmark e documenti

#### D-293 La pre-mappa di Maven, Gradle e sbt girava sull'immagine di Temurin, non sulla base comune
- **Tag:** lingua java, kotlin, scala · area container · tipo completezza · origine commit · strumento Maven, Gradle, sbt
- **Descrizione:** la decisione A del proprietario (15 novembre) vuole una sola immagine per ogni linguaggio. Ciò che un linguaggio chiede oltre la base arriva come input della run. Dopo `bef968a44` scip-java girava sulla base, ma i tre modelli JVM della pre-mappa usavano ancora `eclipse-temurin:17-jdk-noble@sha256:1bedb044…`: due immagini da 190 MB e 28,5 MB compressi per lo stesso progetto.
- **Spiegazione:** `scripts/premap/maven.py`, `gradle.py` e `sbt.py` avevano ciascuno la propria `IMAGE`, e `scripts/premap/container_runner.py` la passava a `container.run_commands`. Il JDK era quello dell'immagine.
- **Progetto e caso:** il modulo, non un progetto.
- **Rimedio:** `bb7a6b56e` (17 novembre, jvm-container):
  - `scripts/preparation.py` tiene la base (`IMAGE`, `debian:trixie-slim@sha256:a72b4433…`, glibc 2.41), il JDK (`TEMURIN`, Temurin 17.0.21+9 con lo sha256 di Adoptium, `JDK_IN`, `JDK_HOME`) e una funzione sola, `unpacked(archive, home, program, link)`: scompatta un `.tar.gz` una volta nel volume di stato e lo collega dove gli script lo cercano, perché il volume passa dalla preparazione all'esecuzione e la radice del container no. `UNPACK_JDK` è quella funzione per il JDK, in `/opt/java/openjdk`;
  - `scripts/premap/container_runner.py`: `maven`, `gradle` e `sbt` portano il JDK fra i loro file, mettono `UNPACK_JDK` in testa al setup, prima di `jar xf`, e la ripetono in ogni comando, prima delle impostazioni del proxy per Java;
  - `scripts/indexers/jvm.py` prende la base, il JDK e `UNPACK_JDK` da `preparation`, e scarica il JDK nello stesso posto della pre-mappa (`preparation.fetched`): sull'host c'è una copia sola;
  - le `IMAGE` di `maven.py`, `gradle.py` e `sbt.py` sono tolte.
- **Verifica:**
  - `tests/test_codebase_map_premap_container_runner.py`, `test_the_jvm_build_tools_run_on_the_common_base_with_the_jdk_and_the_proxy_set_for_java` e `test_the_jdk_of_the_jvm_build_tools_is_temurin_s_checked_by_the_sha256_daodan_pins`: rossi prima del codice (`AttributeError: module 'preparation' has no attribute 'IMAGE'`, poi `'TEMURIN'`);
  - su Modal, da una copia esportata di HEAD `e674c007b` con questo diff: i `test_codebase_map_premap*`, `preparation`, `indexers*` e `dynamic*` danno 811 passati e 50 saltati, con l'impronta del codice uguale ai due lati (`d9106c28f56088b6`). I saltati sono le prove con un container vero, quelle solo per Windows e quelle che chiedono Node, Go, un JDK o .NET sul PATH;
  - da misurare, nel giro approvato: le 6 fixture Gradle `jvm-ver-*` di D-226, un caso Maven e uno sbt. Fra le domande aperte: se il lanciatore di sbt chiede `ps`, che la base non ha.
- **Stato:** risolto nel codice; la prova su Modal parte da `bb7a6b56e`.

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
- **Rimedio:** `eef3e1fef` (17 novembre, dynamic-step-2): il campo di una toolchain di un pom è il suo percorso nel pom, con il plugin nominato dal suo artifactId.
  - nella verità, 28 voci di toolchain in 17 `expected.json` passano a `pom.xml#properties.maven.compiler.*`, `#properties.java.version` e `#properties.kotlin.compiler.jvmTarget` (`ANAGRAFICA.md` rigenerata);
  - nel lettore, `scripts/premap/jvm_files.py` scrive `maven-compiler-plugin.configuration.<campo>`, come la verità di jvm-ver-mvn-cfg6.
- **Verifica:**
  - `tests/test_codebase_map_premap.py` (`test_a_compiler_plugin_setting_is_named_by_its_path_in_the_pom`), rosso prima;
  - il giro java-versions conservato (`benchmarks/project-model/results/pipeline/2026-11-16-java-versions.json`), rivalutato con `score.py` contro il corpus di HEAD su Modal (android-sdk): 28 toolchain su 30, non le 29 del messaggio di `eef3e1fef`; il README del benchmark dice 28 da `b11d5504e`;
  - le 2 sbagliate erano di jvm-ver-mvn-cfg6: il giro è precedente a `eef3e1fef`, quindi la sua pre-mappa scriveva `pom.xml#maven-compiler-plugin.source` e `.target`, dove il corpus dice `maven-compiler-plugin.configuration.source` e `.target`;
  - giro nuovo del 17 novembre (jvm-container), su `f01fcaf5b` con Java e Kotlin sulla base comune (`bef968a44`), 0,068 USD:
    - pre-mappa su Modal (`modal_premap.py`, `score_fixtures` sulle 18 `jvm-ver-*`, codice verificato per hash): le 21 toolchain Maven sono tutte giuste, comprese le 2 di jvm-ver-mvn-cfg6;
    - le 9 toolchain Gradle lì non si misurano: l'immagine di `modal_premap.py` non ha Gradle, e il modello di Gradle finisce con `model_failed` («gradle: not found»);
    - pipeline su jvm-ver-gradle-tc21: 1 su 1;
  - 22 toolchain su 30 sono misurate e giuste. Le altre 8 sono delle 6 fixture Gradle jvm-ver-gradle-mixed-tc8, -src6, -src8, -tc11, -tc25 e -tc8: vogliono un giro della pipeline su quelle 6, stimato in circa 0,15 USD.
- **Stato:** risolto per le toolchain Maven; il 30 su 30 aspetta il giro sulle 6 fixture Gradle.
- **Note:** la fixture mista è giusta da `1bd53689a`, il cui corpus nomina una toolchain Gradle come la nomina il modello (`#java.toolchain.languageVersion`); la toolchain Kotlin che la pre-mappa trova e il corpus non conta resta fuori, per decisione di team-lead (17 novembre): la versione del plugin Kotlin è una dipendenza del build, non una toolchain, e `score.py` non la conta. D-284.
#### D-227 README del benchmark: Rust, C e C++ «solo dove Valgrind parte»
- **Tag:** lingua c, cpp, rust · area documenti · tipo documentazione · origine commit · strumento Valgrind
- **Descrizione:** il risultato del finale nel README dice ancora che Rust, C e C++ si osservano solo dove Valgrind parte, e che nei sandbox di Modal (gVisor) dipende dalla macchina.
- **Spiegazione:** è stato scritto prima di `8ef21896f`; la conferma li osserva nei sandbox a macchina virtuale.
- **Progetto e caso:** `benchmarks/project-model/README.md` — 16 novembre 2026.
- **Rimedio:** `e4da4b429` (16 novembre): la frase del finale è al passato, sotto il gVisor dei sandbox di Modal Valgrind non parte e il driver dà le VM Sandbox agli osservatori nativi (`8ef21896f`); la conferma dice che lì Rust, C e C++ si osservano.
- **Verifica:** a HEAD le righe 196 e 208 del README; i numeri della conferma sono quelli di `results/pipeline/2026-11-16-conferma.json` (`steps.dynamic.languages`): semver 558, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- **Stato:** risolto.
- **Note:** D-209, D-230.

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
- **Verifica:** `benchmarks/inference-audit/test_scripts_on_modal.py`, su Modal con `tests/modal_pytest.py`:
  - `adapters/ts_compiler.py` (`test_on_modal_ts_compiler_checks_a_project_through_the_tsconfig_it_generates`): su due file TypeScript con il loro `tsconfig.json`, `analyze` lo sposta in `tsconfig.project.json`, il generato lo estende e include i due file, e il checker (`@typescript/typescript6` 6.0.2, typescript 6.0.3) dà la chiamata `a.ts:2:0` → `b.ts:1:7` per la firma, senza errori;
  - `modal_scip.py` (`test_on_modal_modal_scip_joins_semver_s_kept_inputs`): `scip_case` su semver, con gli input che il volume tiene e l'etichetta `d233`, senza scrivere sul volume: input `kept`, i due indici di rust-analyzer 0.3.3113, il join senza errori, con 1.073 nodi, 3.960 archi e 721 risposte della strada A.
- **Stato:** risolto.
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

#### D-251 I risultati di un giro non registravano il codice di Daodan su cui era girato
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine review · strumento Modal
- **Descrizione:** docs-writer, sul giro `ci-steps`: la quota di risposta dei fogli di stile è al 98,7 %, contro il 26,3 % della conferma, e sugli stessi due casi, tududi e fastapi, i buchi passano da 38.210 a 523; nulla nel risultato dice su quale codice di Daodan il giro è girato (riportato da team-lead il 16 novembre). Così nessun numero di un giro si lega a un commit.
- **Spiegazione:**
  - il driver (`benchmarks/project-model/modal_pipeline.py`, `main`, righe 502-534) scrive in `<giro>.json` solo i casi: nessun commit di Daodan, nessuno stato dell'albero di lavoro;
  - un caso registra le versioni degli strumenti (`steps.analyze.engines.<motore>.indexer.version`): quella del motore dei fogli di stile, un'impronta delle sue versioni (`scripts/indexers/css.py:164-166`), è `145560a4592a` per tududi e fastapi nella conferma, `45b68b725df0` e `2a5e4ddac1b8` in `ci-steps`, e non nomina un commit;
  - il codice dei giri lo dicono solo testi accanto al risultato (Convenzioni).
- **Progetto e caso:** giro `ci-steps` — review di docs-writer, 16 novembre 2026.
- **Rimedio:** `cbc219663` (16 novembre, test-services), `benchmarks/project-model/modal_pipeline.py` e `pipeline_report.py`:
  - il driver scrive accanto ai casi `code`: il commit del checkout, l'albero di ciò che carica su Modal (gli script, le fixture, `score.py` e il driver stesso, calcolato da git su un indice temporaneo, senza cache né file ignorati) e i percorsi in cui differisce dal commit;
  - il rapporto lo mostra in testa, e `--compare` dice per prima cosa se i due giri hanno girato lo stesso codice, per albero.
- **Verifica:** solo test: `benchmarks/project-model/test_modal_pipeline.py` (`test_a_round_records_its_commit_the_tree_of_the_copy_it_uploaded_and_the_paths_where_they_differ`), `benchmarks/project-model/test_pipeline_report.py` (`test_a_comparison_says_first_whether_the_two_rounds_ran_the_same_code`).
- **Stato:** risolto per i giri dopo `cbc219663`; i giri già registrati non hanno `code`, e il loro codice resta quello che dicono le Convenzioni.
- **Note:** i confronti fra giri di «Buchi trovati» ne dipendono; D-243, l'altro difetto del driver.

#### D-280 Una seconda sessione sullo stesso checkout ha committato ogni modifica in corso insieme
- **Tag:** lingua tutti · area processo · tipo correttezza · origine commit · strumento git
- **Descrizione:** un'altra sessione (Codex) sullo stesso checkout ha committato in `1c68cbde4` l'intero albero di lavoro: 55 file, 53.591 righe aggiunte, tra cui il registro a 276 schede, la riga della spec e il test del Kiri dell'utente (D-219), CSS, `rust.py`, `compose.py` e altro lavoro in corso di più agenti, che nessuno aveva rivisto insieme. Il 17 novembre di nuovo, in `05135d74e` (13 file, pubblicato): il CSS di ts-container-2 prima della sua prova completa, il prototipo standalone e senior-review 1.1.4; il messaggio dice che quelle modifiche non sono coperte dalla sua verifica nel Kiri su `f992db56`.
- **Spiegazione:** gli agenti lavorano sullo stesso checkout senza worktree e senza commit propri, e chi committa sceglie i file; una sessione che committa tutto quello che trova raccoglie anche il lavoro degli altri. Il messaggio dice che i test non sono stati rieseguiti («test non rieseguiti perché Docker non disponibile»): nessuna verifica sua.
- **Progetto e caso:** il checkout di Daodan — commit `1c68cbde4`, 16 novembre 2026, e `05135d74e`, 17 novembre 2026.
- **Rimedio:** il 17 novembre il proprietario ha fermato la sessione Codex e ha affidato il checkout a team-lead: gli agenti consegnano diff su HEAD e committa solo team-lead, dopo la suite intera su Modal.
- **Verifica:** dopo, team-lead ha rieseguito l'intera suite su HEAD: 2.648 passati; nessuna revisione del contenuto. Dopo `05135d74e`, su HEAD `425006538`: 2.682 passati, e ts-container-2 conferma che `css.py`, `css_packages.js` e il loro test sono la sua versione finale.
- **Stato:** risolto.
- **Note:** D-219, il cui commit è `1c68cbde4`. Le prove di Codex sull'app standalone (`05135d74e`, `425006538`) sono girate nel Kiri locale, non su Modal.

#### D-287 Il driver della pipeline non caricava i dati che gli script leggono accanto alla loro cartella
- **Tag:** lingua tutti · area benchmark · tipo benchmark · origine commit · strumento Modal
- **Descrizione:** su Modal lo step `stack` finisce con `FileNotFoundError: [Errno 2] No such file or directory: '/daodan/map/data/service-registry.json'`, e l'analisi va avanti senza tecnologie. È successo nei 3 casi del giro `2026-11-17-vue-svelte` e in `jvm-ver-gradle-tc21`, il 17 novembre (D-226).
- **Spiegazione:**
  - lo step `stack` (`899ba7f57`, 16 novembre) chiama `technologies.ensure`. Questo importa `service_registry`, che legge `SCRIPT_DIR.parent / "data" / "service-registry.json"` (`scripts/service_registry.py:32`); `registry_build.DATA` legge la stessa cartella;
  - il driver caricava gli script in `/daodan/map/scripts`, poi le fixture e `score.py`, ma non `plugins/codebase-map/skills/map/data`: `UPLOADED` e l'immagine, righe 71-85 a `9964ebe92`;
  - i giri registrati prima di `899ba7f57` non hanno lo step `stack`, che lì vale `null`.
- **Progetto e caso:** il driver della pipeline: il giro `2026-11-17-vue-svelte` e `jvm-ver-gradle-tc21`, 17 novembre 2026.
- **Rimedio:** `c1244f610` (17 novembre, jvm-container), `benchmarks/project-model/modal_pipeline.py`:
  - `UPLOADED` carica anche la cartella `data` che sta accanto agli script del giro: quella del checkout, oppure quella accanto alla copia indicata da `DAODAN_SCRIPTS`. Così `code` la copre;
  - l'immagine la mette in `REMOTE_DATA`, `/daodan/map/data`, accanto a `REMOTE_SCRIPTS`.
- **Verifica:**
  - `benchmarks/project-model/test_modal_pipeline.py` (`test_a_round_uploads_the_data_its_scripts_read_beside_their_folder`): rosso prima della correzione, con `AssertionError: data`;
  - su Modal: i `test_*.py` di `benchmarks/project-model`, `tests/test_codebase_map_docker_build.py` e `tests/test_codebase_map_dynamic_services.py` danno 156 passati, con l'impronta del codice uguale ai due lati (`0945157a3a0d0278`);
  - non misurato: un giro in cui lo step `stack` scrive le tecnologie. Basta la pipeline su un caso, circa 0,02 USD.
- **Stato:** risolto nel driver; il giro `2026-11-17-vue-svelte` conserva lo step `stack` fallito.
- **Note:** fra gli altri driver di Modal nessuno esegue lo step `stack` o il comando `snapshot.py technologies`, gli unici che leggono quella cartella; `modal_premap.py` carica solo gli script. D-251, il codice registrato da un giro.

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
