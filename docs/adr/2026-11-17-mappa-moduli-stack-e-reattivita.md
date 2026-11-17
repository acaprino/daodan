# ADR: Mappa unificata dei moduli (Step 1), stack per modulo (Step 2) e server reattivo

- **Stato:** approvato dal proprietario il 17 novembre 2026
- **Data:** 2026-11-17
- **Ambito:** `plugins/codebase-map/skills/map/scripts/` (`modules.py`, `module_derive.py`, `premap/`, `technologies.py`, `service_registry.py`, `registry_build.py`, `pipeline/`, `mcp_service.py`, `mcp_server.py`, `visual.py`, `snapshot.py`, `resolve_edges.py`), `plugins/codebase-map/skills/map/data/`, `benchmarks/project-model/`

## Contesto e problema

I primi due step della pipeline di analisi soffrivano di tre frammentazioni:

1. **Modelli di modulo duplicati e incompleti:** `modules.py` (`modules.json`), `premap/module_graph.py` (`premap.json`) e `technologies.py` (`technologies.json`) definivano unità e tipi diversi; i file fuori da manifest di build restavano senza modulo (17 fixture su 140 nel corpus) e né linguaggi né toolchain erano associati al singolo modulo.
2. **Perdita dei pacchetti nello Step 1 e riletture nello Step 2:** la pre-mappa leggeva già i pacchetti tramite lettori statici, Renovate e modelli container (Maven, Gradle, .NET) ma li scartava; `service_registry.py` e `system_brief.py` rileggevano con regex `Dockerfile`, `compose*.yml` e `requirements*.txt`, ignoravano gli ecosistemi `maven`, `nuget`, `pub`, `hex` e `swiftpm`, confondevano framework/test-runner con servizi esterni e tacevano tutte le librerie fuori catalogo.
3. **Blocchi di reattività su server HTTP/UI, MCP e hook:** `snapshot.refresh_working` (invocato dall'hook `PostToolUse` di Claude Code) eseguiva `pipeline.run(..., stop="scan")` con il runner del container dentro `project_lock`, bloccando `MapService`, la UI e i tool MCP; `MapService.create_run` non eseguiva `Scan` né `Stack` nel pass asincrono; `/api/events` non inoltrava `pipeline_after` né offriva uno stream live.

## Decisioni

### 1. Step 1 (`scan`): mappa unica dei moduli con `nature`, `languages`, `toolchains` e `packages`

- Ogni modulo in `modules.json` dichiara `nature` in `("concrete", "logical", "virtual")`:
  - `concrete`: unità di build con proprio artefatto o sorgenti compilati (manifest statici + unità scoperte dai comandi di modello di `premap`).
  - `logical`: moduli `declared` (`codebase-modules.json`) e `proposed` (`proposals.json`), interni o esterni.
  - `virtual`: workspace/solution/reactor senza artefatto proprio (`provenance: "build"`) e modulo implicito `source-tree` (`provenance: "virtual"`) generato quando esistono file sorgente o runtime non coperti da alcun modulo `build` né già letti come manifest.
- Ogni modulo espone `languages` (conteggio file per linguaggio, al netto di `excluded`) e `toolchains` (`[{tool, version, declared_in}]`), risolte associando le toolchain dichiarate nei file del modulo o ereditate dal workspace/contenitore più i tool richiesti dai suoi ecosistemi/linguaggi.
- `premap.json` aggiunge la faccetta `packages` (`{ecosystem, name, declared_in}`, senza versioni né risoluzione transitiva; `dependencies` resta rifiutata per contratto), popolata dai lettori esistenti (`module_graph`, `requirements`, `jvm_files`, `project_files`) e dai comandi di modello (`renovate`, `maven`, `gradle`, `dotnet`) senza cambiare gli `argv` registrati.
- `modules.sync_with_premap(manifest, premap_record)` allinea atomicamente `modules.json` con unità di modello, `excluded`, `languages` e `toolchains` della pre-mappa.

### 2. Step 2 (`stack`): framework, librerie, servizi e tool per ogni modulo senza rileggere i file

- `service_registry.recognize` consuma i fatti dello Step 1 (`packages`, `services`, `docker_builds`, `excluded`), applica `excluded` a tutti i tipi di segno e distingue per ogni voce `category` in `("framework", "library", "tool", "service")`.
- `technologies.json` espone per tutti i moduli (`modules`, inclusi `logical` e `virtual`, oltre alla vista compatibile `units` per le unità fisiche/virtuali) `{id, name, kind, nature, provenance, paths, languages, toolchains, frameworks, libraries, services, tools, technologies}`, dove `libraries` elenca tutte le librerie dichiarate dal modulo (arricchite dal registro quando note, ma mai omesse se fuori catalogo).
- `service_registry.ECOSYSTEMS`, `registry_build.py`, `registry-additions.json` e `service-registry.json` coprono `maven`, `nuget`, `pub`, `hex`, `swiftpm` oltre agli ecosistemi esistenti, separando framework e test runner (Playwright, Cypress, JUnit, Spring Boot, ASP.NET Core, Flutter, OpenTelemetry SDK) dai servizi esterni.

### 3. Reattività non bloccante per UI Daodan, MCP e hook d'harness

- `Scan` supporta `fast=True` (`runner=None`, solo lettori su snapshot in pochi millisecondi): `MapService.create_run` e `snapshot.refresh_working` (`--hook` `PostToolUse`) eseguono sotto `project_lock` solo `scan(fast=True)` + `stack`, lasciando al processo detached (`resolve_edges.py --pass`) l'esecuzione fuori lock di `scan` (se restano comandi di modello `not_run`), `stack`, `analyze`, `dynamic` e `union`.
- `snapshot.py write` da CLI esegue `scan` completo + `stack` prima di avviare `ensure_edges`.
- `MapService` espone `stack(run_id, module=None)`, arricchisce `status(run_id)` con lo stato degli step della pipeline e di `working`, arricchisce `modules(run_id)` con `nature`, `languages` e `toolchains`, e registra impulsi reattivi (`live-pulse.jsonl`) a ogni evento di servizio o refresh dell'hook.
- `mcp_server.py` espone il tool `codebase_map_stack`, la risorsa `daodan://project/live` e notifiche MCP non bloccanti di avanzamento/aggiornamento risorsa.
- `visual.py` propaga `pipeline_after` e `run=working` in `/api/events`, aggiunge `/api/modules`, `/api/stack` e lo stream SSE `/api/stream` (protetto da loopback e token, con chiusura pulita allo shutdown), ed espone `nature`, `languages`, `toolchains`, `frameworks`, `libraries`, `services` e `tools` nelle entità di `visual.json` senza bloccare su container.

## Vincoli invarianti

- **Regola invalicabile:** nessun codice del progetto analizzato gira mai sull'host; ogni comando di modello, build o test del progetto analizzato gira esclusivamente nel container di Daodan.
- Percorsi `modules.json`, `premap.json` e `technologies.json` preservati per compatibilità con CLI, MCP, viewer e benchmark.
