# Stack dal fork, piano 2 di 3: Daodan dietro il benchmark

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Daodan sa scaricare e lanciare il rilascio fissato del fork senza eseguire nulla del progetto, e un benchmark dice, progetto per progetto, che cosa cambierebbe in `technologies.json` e quanto costa la scansione veloce. Il prodotto continua a riconoscere dal registro.

**Architecture:** Un modulo nuovo, `stack_analyser.py`, è lo strumento: installa il rilascio come `secret_mask.py` installa Secretlint, lo esegue con il Node che Daodan installa già (`indexers.runtime.node`) e ne restituisce l'uscita. La traduzione fra i fatti della pre-mappa e il fork (dichiarazioni in ingresso, prove in uscita) vive nel benchmark, in `benchmarks/project-model/tools/fork_stack.py`: il piano 3 la sposta nel prodotto al posto di `service_registry.run`. Il benchmark calcola il record «dopo» con `technologies.derive` e quel riconoscitore sostituito, senza toccare il prodotto.

**Tech Stack:** Python 3.12, pytest. Repository: `C:\Users\alfio\Documents\ChatGPT\Daodan\daodan`, ramo nuovo `stack-fork-benchmark` da `develop`. Le prove con gli strumenti veri girano su Modal.

**Spec:** `docs/specs/2026-11-21-stack-dal-fork.md`, quarta stesura: «Disegno» 2.1 (Task 1 e 2) e 2.7 (Task 3–5), «Ordine» punto 3, «Verifica». Il piano 1 è chiuso; il piano 3 (2.2–2.6) parte solo se la «Verifica» di questo piano passa.

## Che cosa consegna il piano 1

- Rilascio `v1.27.6-daodan.1` di `acaprino/stack-analyser`, asset `https://github.com/acaprino/stack-analyser/releases/download/v1.27.6-daodan.1/specfy-stack-analyser-1.27.6-daodan.1.tgz`, sha256 `ee889f52b054ecf6c900847a8d492f17065a28fe25ddde0d146d8d9915b79baf`, 2.989.312 byte.
- Scompattato dà `package/`; gira con `node package/dist/cli.mjs PROGETTO --output FILE [--declarations FILE] [--skip-dirs NOMI] [--ignore PERCORSI]`, senza installare nulla. Node 20 o successivo.
- `--output`: JSON di un componente radice `{name, path, tech, techs, childs, evidence, …}`; ogni componente, a ogni profondità, ha `evidence: [{tech, kind, value, path, line?, source}]`. `kind` è uno fra `package`, `image`, `action`, `terraform`, `file`, `extension`, `env`, `source`. `path` comincia con `/`, è relativo alla radice e usa `/`. La stessa prova può stare su più componenti.
- `--declarations`: file JSON UTF-8, un array di `{type, name, version?, path, line?, source}`. `type` è uno dei tipi del fork (`npm`, `python`, `rust`, `golang`, `ruby`, `php`, `docker`, `githubAction`, `terraform`, `terraform.resource`, `deno`, `maven`, `nuget`, `hex`, `pub`, `swift`…); `path` è relativo alla radice, senza `..`. Una voce sbagliata fa uscire il comando con codice 1 e il messaggio `declaration <indice>: …`.
- `--skip-dirs`: nomi di cartella separati da virgola, saltati a ogni profondità; sostituisce l'elenco predefinito del fork (`""` non salta nulla). Un nome con `/` o `\` è un errore (codice 1). `--ignore`: percorsi relativi separati da virgola; `/gen`, `./gen`, `gen/` e `gen` sono la stessa cartella.
- Non usare `--flat`: la radice ripete le prove di ogni figlio e il tempo cresce più che in proporzione.
- Costo misurato su Windows: avvio circa 350–530 ms; 800 manifest Python 3,7 s; ogni dichiarazione circa 0,3–0,7 ms.
- ID che cambiano rispetto al registro di oggi: `react-email` → `reactemail`, `kafka` → `apache_kafka`, `vault` → `hashicorp_vault`. ID che il fork ha e il registro no: `ava`, `azure.appservice`, `gradle`, `maestro`, `rich`, `setuptools`, `winui`, `xo`.

## Scostamenti dalla spec, da confermare con il proprietario

1. **Node non è un requisito nuovo per chi usa Daodan.** La spec lo chiama «requisito nuovo». Daodan installa già il suo Node, fissato e verificato (`indexers/runtime.py`, `NODE_VERSION`, usato da scip-python e dagli indici dei fogli di stile). Lo strumento usa quello. Il caso «senza Node» della spec diventa «Node non installabile» (senza rete o senza disco al primo uso).
2. **Il perimetro è quello della snapshot.** La spec dice «le cartelle escluse dalla pre-mappa». Il fork legge il disco, Daodan una snapshot: il benchmark passa al fork le cartelle che non contengono file della snapshot e scarta le prove su file fuori dalla snapshot o esclusi dalla pre-mappa.

## Global Constraints

- **Regola invalicabile.** Il fork gira sull'host: legge file e non esegue nulla del progetto. Lo prova il Task 2 con lo strumento vero.
- **Nessun secondo riconoscitore nel prodotto.** In questo piano non cambiano `technologies.py`, `service_registry.py`, `pipeline/`, `registry_build.py`, `data/`. `stack_analyser.py` non è importato da nessun modulo del prodotto.
- **Riuso.** Scaricare, verificare, scompattare e pubblicare un'installazione si fa con `engine_tools.download`, `engine_tools.unpack`, `engine_tools.publish`, `engine_tools.shared_engine_dir`; Node viene da `indexers.runtime.node`. Nessuna copia di quel codice.
- **Il processo del fork** parte con un programma a percorso assoluto, in una cartella sua fuori dal progetto, senza le variabili `NODE_*` del chiamante (poi si aggiunge `engine_tools.node_environment()`), con un tempo massimo.
- **Errori come buchi.** Un rilascio non scaricabile, un Node non installabile, un'uscita con codice diverso da 0, un tempo scaduto o un'uscita illeggibile sono `container.Gap(causa, rimedio)`, come in `secret_mask.py`.
- **Le prove restano nel repository** (AGENTS.md): test in `tests/` e in `benchmarks/project-model/`; ciò che chiede Node o il rilascio vero gira su Modal. Ogni giro su Modal costa: prima di lanciarlo si chiede conferma al proprietario.
- I test puri si eseguono in locale con `python -B -m pytest -q -p no:cacheprovider <file>`.
- Commit nello stile dei commit più recenti di `develop`: prefisso (`feat:`, `fix:`, `test:`, `docs:`) e una frase in italiano. I messaggi in inglese scritti nei Task sono da tradurre così.
- Il ramo di lavoro è `stack-fork-benchmark`; nessun push senza conferma del proprietario.

## Review Focus

1. **Un file del progetto raggiunge il processo del fork.** `NODE_OPTIONS=--require ./x.js`, `NODE_PATH`, un `node` o un `node_modules/commander` piantato nel progetto, la cartella di lavoro. Ci si aspetta che nessuno venga caricato. Test: Task 2, `test_the_real_stack_analyser_runs_nothing_of_the_project`.
2. **Un archivio che non è il rilascio.** Download interrotto, sha256 diverso, cartella installata a metà. Ci si aspetta un `Gap` e nessuna installazione usabile. Test: Task 1, `test_a_release_with_another_sha256_is_not_installed`.
3. **Una dichiarazione che il fork rifiuta ferma tutto.** Un ecosistema che il fork non conosce o un percorso fuori dalla radice farebbero uscire il comando con codice 1 e nessun risultato. Ci si aspetta che la voce sia scartata prima, con un buco che la nomina. Test: Task 3, `test_a_declaration_the_fork_cannot_take_is_a_gap_not_a_failure`.
4. **Una prova fuori dal perimetro.** Un file ignorato da git ma presente sul disco, o sotto una cartella esclusa dalla pre-mappa. Ci si aspetta che non diventi un segno. Test: Task 3, `test_evidence_outside_the_snapshot_or_excluded_is_dropped`.
5. **Un ID che il registro non ha.** `setuptools`, `gradle`. Ci si aspetta che la tecnologia esca comunque, con il nome uguale all'ID e un buco `not_in_registry`. Test: Task 3, `test_an_id_the_registry_lacks_still_comes_out_with_a_gap`.

---

### Task 1: Lo strumento

**Files:**
- Create: `daodan/core/stack_analyser.py`
- Create: `tests/fake_stack_analyser.py`
- Create: `tests/test_codebase_map_stack_analyser.py`

**Interfaces:**
- Consumes: `engine_tools.download(url, target, sha256=)`, `engine_tools.unpack(archive, destination)`, `engine_tools.publish(home, fill, installed)`, `engine_tools.shared_engine_dir(name)`, `engine_tools.executable_name`, `engine_tools.node_environment()`, `indexers.runtime.node(project_dir) -> Path` (la cartella di Node), `indexers.runtime.Unavailable`, `container.Gap`.
- Produces, per i Task 2–4 e per il piano 3:
  - `VERSION = "1.27.6-daodan.1"`, `URL`, `SHA256` (i valori sopra), `TIMEOUT = 300`.
  - `cli() -> Path`: `…/engines/stack-analyser/<VERSION>/package/dist/cli.mjs`, installato al primo uso; `Gap` se non si può.
  - `node(project: Path) -> Path`: l'eseguibile di Node (`runtime.node(project) / executable_name("node")`); `Gap` da `runtime.Unavailable` o da un errore di rete.
  - `command(node: Path, cli: Path, project: Path, output: Path, declarations: Path | None, skip_dirs: tuple[str, ...] | None, ignore: tuple[str, ...]) -> list[str]`. `skip_dirs=None` non passa l'opzione; `()` passa `--skip-dirs ""`.
  - `run(project: Path, *, declarations: list[dict] = (), skip_dirs: tuple[str, ...] | None = None, ignore: tuple[str, ...] = ()) -> dict`: il JSON di uscita.

- [ ] **Step 1: Scrivere `tests/fake_stack_analyser.py`**

Come `tests/fake_secretlint.py`: `install(folder) -> Path` scrive un programma che fa da `node`; a ogni avvio aggiunge `{argv, cwd, env}` a `folder/calls.jsonl` (`env`: i nomi delle variabili che cominciano con `NODE_`), e scrive nel file dopo `--output` il JSON `{"name": "main", "path": ["/"], "techs": ["react"], "childs": [], "evidence": [{"tech": "react", "kind": "package", "value": "react", "path": "/package.json", "source": "stack-analyser"}]}`. `FAKE_STACK_ANALYSER=fail|garbage|sleep` lo fa uscire con codice 1 e un messaggio su stderr, scrivere ciò che non è JSON, o dormire.

- [ ] **Step 2: Scrivere i test che falliscono**

In `tests/test_codebase_map_stack_analyser.py`, con `stack_analyser.node` e `stack_analyser.cli` sostituiti (`monkeypatch`) dove serve:

```python
def test_the_fork_is_started_outside_the_project_without_the_caller_s_node_variables(tmp_path, monkeypatch):
    # NODE_OPTIONS and NODE_PATH set to paths inside the project before the call
    result = stack_analyser.run(project, declarations=[DECLARATION], skip_dirs=(), ignore=("gen",))
    [call] = fake_stack_analyser.calls(program)
    assert Path(call["argv"][0]) == cli and cli.is_absolute() and program.is_absolute()
    assert call["argv"][1] == str(project.resolve())
    assert "--skip-dirs" in call["argv"] and call["argv"][call["argv"].index("--skip-dirs") + 1] == ""
    assert call["argv"][call["argv"].index("--ignore") + 1] == "gen"
    assert not Path(call["cwd"]).resolve().is_relative_to(project.resolve())
    assert "NODE_OPTIONS" not in call["env"] and "NODE_PATH" not in call["env"]
    assert result["evidence"][0]["tech"] == "react"

def test_the_declarations_reach_the_fork_as_utf8_json_outside_the_project(tmp_path, monkeypatch):
    # the fake copies the file named after --declarations beside its record
    # assert: it is not under the project, it starts with b"[" (no byte order mark), json.loads gives [DECLARATION]

def test_without_declarations_the_option_is_not_passed(...)
def test_nothing_is_left_in_the_temporary_folder(...)            # the folder of cwd is gone after run
@pytest.mark.parametrize("mode, word", [("fail", "exit 1"), ("garbage", "not JSON"), ("sleep", "no answer")])
def test_a_run_that_fails_is_a_gap_with_its_cause(mode, word, ...):   # TIMEOUT patched to 2 for sleep
    with pytest.raises(container.Gap) as gap: ...
    assert word in gap.value.cause
def test_a_release_with_another_sha256_is_not_installed(tmp_path, monkeypatch):
    # URL = a file:// URL of a small local .tgz holding package/dist/cli.mjs; SHA256 = 64 zeros;
    # shared_engine_dir patched to tmp_path
    with pytest.raises(container.Gap): stack_analyser.cli()
    assert not (tmp_path / "stack-analyser" / stack_analyser.VERSION).exists()
def test_the_release_is_installed_once_and_found_again(tmp_path, monkeypatch):
    # same local archive with its real sha256: cli() is a file; a second call downloads nothing
def test_a_node_that_cannot_be_installed_is_a_gap(monkeypatch):
    # runtime.node raises runtime.Unavailable("no room", "free 1 GB")
```

`DECLARATION = {"type": "npm", "name": "react", "path": "web/package.json", "line": 4, "source": "npm@1"}`.

- [ ] **Step 3: Vederli fallire**

Run: `python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_stack_analyser.py`
Expected: FAIL, `No module named 'stack_analyser'`.

- [ ] **Step 4: Scrivere `daodan/core/stack_analyser.py`**

`cli()` segue `secret_mask.executable()`: `functools.cache`, cartella `shared_engine_dir("stack-analyser") / VERSION`, pubblicata intera con `engine_tools.publish` da un `fill` che scarica con `download(URL, partial / "release.tgz", sha256=SHA256)`, scompatta con `unpack` e cancella l'archivio. `run` crea una cartella temporanea (`tempfile.TemporaryDirectory(prefix="daodan-stack-")`), ci scrive `declarations.json` (`json.dumps(…, ensure_ascii=False).encode("utf-8")`) solo se l'elenco non è vuoto, lancia `subprocess.run(command(…), cwd=<cartella>, env=<ambiente>, stdin=DEVNULL, capture_output=True, timeout=TIMEOUT)` e legge `output.json`. L'ambiente è `os.environ` senza le chiavi che in maiuscolo cominciano con `NODE_`, più `node_environment()`. La causa di un `Gap` cita il codice di uscita e le ultime righe di stderr.

- [ ] **Step 5: Vederli passare**

Run: `python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_stack_analyser.py`
Expected: PASS, nessun avviso.

- [ ] **Step 6: Commit**

```bash
git add daodan/core/stack_analyser.py tests/fake_stack_analyser.py tests/test_codebase_map_stack_analyser.py
git commit -m "Install and start the pinned stack-analyser release outside the project"
```

### Task 2: La prova che nulla del progetto viene eseguito

**Files:**
- Modify: `tests/test_codebase_map_host_programs.py`
- Modify: `tests/modal_pytest.py`

**Interfaces:**
- Consumes: `stack_analyser.run`, `stack_analyser.cli`, `stack_analyser.node` (Task 1).
- Produces: la variabile `DAODAN_STACK_ANALYSER` nell'ambiente dei test su Modal: il percorso di `package/dist/cli.mjs` del rilascio, scaricato nell'immagine e verificato con lo sha256.

- [ ] **Step 1: Scrivere il test**

In `tests/test_codebase_map_host_programs.py`, saltato senza `DAODAN_STACK_ANALYSER` (come quello di Secretlint):

```python
STACK_VECTORS = {...}  # name -> function(project, mark) -> variables to set

def test_the_real_stack_analyser_runs_nothing_of_the_project(tmp_path, monkeypatch):
    # every vector in one project; the project is the working directory, as in an analysis
    result = stack_analyser.run(project)
    assert not mark.exists(), mark.read_text(encoding="utf-8")
    assert "react" in {e["tech"] for e in _all_evidence(result)}     # it did read the project
    assert all(e["path"].startswith("/") for e in _all_evidence(result))
```

I vettori, ognuno scrive nel `mark` se eseguito o caricato:
- `node-options`: `trap.js` nel progetto e `NODE_OPTIONS=--require=<progetto>/trap.js`;
- `node-path`: `NODE_PATH=<progetto>/node_modules`, con dentro `commander/index.js` e `@cdktf/hcl2json/index.js` piantati;
- `planted-node`: un programma `node` (`node.bat` su Windows) nella radice del progetto, con `PATH` che comincia con `.`;
- `package-scripts`: `package.json` con `dependencies: {"react": "18.0.0"}` e gli script `preinstall`, `install`, `postinstall`, `prepare`;
- `config-code`: `next.config.js`, `vite.config.ts`, `webpack.config.js`, `.eslintrc.js`, `babel.config.js`, `setup.py`, `conftest.py`, `Gemfile`, `build.gradle`, `Makefile`, ognuno con codice che scrive nel `mark`;
- `terraform`: un `main.tf` con un `provisioner "local-exec"` che scrive nel `mark` (il fork lo legge con il WebAssembly di hcl2json).

Come per Secretlint, il test aggiunge agli avvisi un rapporto: per ogni vettore da solo, se un avvio ingenuo (`node cli.mjs .` nella cartella del progetto, con le variabili del vettore) lo fa scattare. È un fatto sullo strumento, non l'asserzione.

`stack_analyser.cli` è sostituito con il percorso di `DAODAN_STACK_ANALYSER`; il test verifica prima che lo sha256 dell'archivio accanto (`release.tgz`) sia `stack_analyser.SHA256`. `stack_analyser.node` è sostituito con il `node` dell'immagine (percorso assoluto).

- [ ] **Step 2: Portare il rilascio nell'immagine dei test**

In `tests/modal_pytest.py`, come `SECRETLINT`: `STACK_ANALYSER = (URL, SHA256, "/opt/stack-analyser")`, un comando che scarica, verifica lo sha256, conserva l'archivio come `/opt/stack-analyser/release.tgz` e lo scompatta lì; `DAODAN_STACK_ANALYSER=/opt/stack-analyser/package/dist/cli.mjs` nell'ambiente. URL e sha256 si leggono da `daodan/core/stack_analyser.py` se il modulo è importabile nel lanciatore, altrimenti sono ripetuti con un test (`tests/test_codebase_map_stack_analyser.py::test_the_test_image_pins_the_same_release`) che li confronta.

- [ ] **Step 3: Eseguirlo su Modal (chiedere prima conferma al proprietario)**

Run: `python tests/modal_pytest.py tests/test_codebase_map_host_programs.py tests/test_codebase_map_stack_analyser.py -q -rw`
Expected: PASS; negli avvisi il rapporto «stack-analyser naive starts» con una riga per vettore.

Se un vettore scatta con l'avvio di Daodan, il test fallisce: è un difetto dello strumento (Task 1) o del fork, e il piano si ferma lì.

- [ ] **Step 4: Commit**

```bash
git add tests/test_codebase_map_host_programs.py tests/modal_pytest.py tests/test_codebase_map_stack_analyser.py
git commit -m "Prove that the stack-analyser release runs nothing of the analyzed project"
```

### Task 3: La traduzione, nel benchmark

**Files:**
- Create: `benchmarks/project-model/tools/fork_stack.py`
- Create: `benchmarks/project-model/test_fork_stack.py`
- Create: `benchmarks/project-model/fixtures-fork/py-fastapi-compose.payload.json` (l'uscita vera del rilascio su `fixtures/py-fastapi-compose`, registrata una volta)

**Interfaces:**
- Consumes: `stack_analyser.run` (Task 1); `service_registry.service_site`, `service_registry._split_declared_in`, `service_registry._is_excluded`, `service_registry.entry_category`, `registry_hosts.check_hosts`, `registry_build.ECOSYSTEMS`, `premap.module_graph.declared_image`, `snapshot_store.open_snapshot`.
- Produces, per i Task 4–5 e, spostato nel prodotto, per il piano 3:
  - `declarations(facts: dict) -> tuple[list[dict], list[dict]]`: le dichiarazioni per il fork e i buchi.
  - `perimeter(root: Path, files: list[str], excluded: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]`: `(skip_dirs, ignore)`.
  - `found(payload: dict, registry: dict, files: set[str], excluded: tuple[str, ...]) -> tuple[list[dict], list[dict]]`: le voci nella forma di `service_registry.run()["found"]` e i buchi.
  - `recognize(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> dict`: `{"found", "checkers", "gaps"}`, la stessa forma di `service_registry.run`.

Regole, tutte verificate dai test dello Step 1:

**Dichiarazioni.** Da `facts["packages"]`: una dichiarazione per ogni fonte dell'elenco `sources` della voce, con `source` uguale all'etichetta della pre-mappa (`requirements@2`). `type` è l'inverso di `registry_build.ECOSYSTEMS` (`pypi` → `python`, `crates` → `rust`, `go` → `golang`, `rubygems` → `ruby`, `composer` → `php`, `github-actions` → `githubAction`, `terraform-resource` → `terraform.resource`); gli altri nomi passano come sono. `path` e `line` vengono da `declared_in` (`file#L12`). Le immagini di `facts["services"]` e le basi di `facts["docker_builds"]` diventano dichiarazioni `docker` come in `service_registry.step1_packages`, con la fonte della loro voce. Si scarta, con un buco `{"kind": "declaration_not_sent", "value", "path", "ecosystem", "detail"}`: una voce senza `path`, con un percorso escluso dalla pre-mappa, o con un tipo che non è fra quelli che il rilascio accetta (elenco `TYPES` nel modulo, copiato dal README del rilascio).

**Perimetro.** Una cartella è «viva» se contiene, a qualunque profondità, un file della snapshot; la radice lo è sempre. Si elencano sul disco solo i figli delle cartelle vive. Un figlio non vivo il cui nome non è il nome di nessuna cartella viva va in `skip_dirs` con il suo nome (tipicamente `node_modules`, `.git`, `.venv`): il fork lo salta a ogni profondità. Un figlio non vivo con il nome di una cartella viva va in `ignore` con il suo percorso. In `ignore` vanno anche i percorsi esclusi dalla pre-mappa. I due elenchi sono ordinati e senza doppioni.

**Prove.** Si raccolgono da ogni componente, a ogni profondità, senza doppioni per `(tech, kind, value, path, line, source)`. `path` perde la `/` iniziale. Si scarta la prova di tipo `extension`, quella il cui file non è nella snapshot e quella sotto un percorso escluso. Un segno è `{"sign": kind, "value", "path", "line" (None se manca), "strength", "source"}`, con `strength` `mentioned` per `env` e `declared` per gli altri. Una tecnologia senza segni rimasti non esce.

**Voci.** `id` è l'ID del fork; `name`, `category` (`service_registry.entry_category`), `type`, `site`, `mark` vengono dalla voce del registro con quell'ID, `kind` è `service` o `project` come in `service_registry.run`. Un ID che il registro non ha esce con `name` uguale all'ID, `category` `framework`, e un buco `{"kind": "not_in_registry", "entry": id}`. I segni sono ordinati come in `service_registry.run`.

**`recognize`.** Legge radice e file dalla snapshot, calcola dichiarazioni e perimetro, chiama `stack_analyser.run(root, declarations=…, skip_dirs=…, ignore=…)`, poi aggiunge le menzioni di `registry_hosts.check_hosts` come fa `service_registry.run` (segno `host`, `mentioned`, fonte `registry_hosts`). `checkers`: `[{"checker": "stack-analyser", "state": "ran"}, {"checker": "host", "state": …}]`. Un `container.Gap` del fork diventa `{"checker": "stack-analyser", "state": "failed", "reason"}` e un buco `checker_failed`, e le menzioni di host restano.

- [ ] **Step 1: Scrivere i test che falliscono**

`benchmarks/project-model/test_fork_stack.py`, senza Node (`stack_analyser.run` sostituito con una funzione che restituisce il payload registrato o uno scritto nel test):

```python
def test_each_source_of_a_package_fact_is_one_declaration():
    facts = {"packages": [{"ecosystem": "pypi", "name": "fastapi", "version": "0.115", "declared_in": "api/requirements.txt#L3",
                           "sources": ["requirements@2", "renovate@41"]}]}
    sent, gaps = fork_stack.declarations(facts)
    assert sent == [{"type": "python", "name": "fastapi", "version": "0.115", "path": "api/requirements.txt", "line": 3, "source": s}
                    for s in ("requirements@2", "renovate@41")] and gaps == []

def test_images_of_services_and_docker_stages_are_docker_declarations(): ...
def test_a_declaration_the_fork_cannot_take_is_a_gap_not_a_failure():
    # ecosystem "conan", a fact without declared_in, a path under an excluded folder: three gaps, nothing sent
def test_the_perimeter_skips_by_name_what_never_holds_a_snapshot_file(tmp_path):
    # disk: web/node_modules/x.js, api/node_modules/y.js, .git/config, web/src/a.ts, gen/out.ts, web/gen/keep.ts
    # snapshot files: web/src/a.ts, web/gen/keep.ts; excluded: ("third_party",)
    # `api` holds no snapshot file and no live folder has that name: it is skipped by name, and never entered
    assert fork_stack.perimeter(tmp_path, files, ("third_party",)) == ((".git", "api", "node_modules"), ("gen", "third_party"))
def test_evidence_is_collected_from_every_component_once(): ...
def test_evidence_outside_the_snapshot_or_excluded_is_dropped(): ...
def test_extension_evidence_alone_recognizes_nothing(): ...
def test_an_environment_variable_is_a_mention(): ...     # strength "mentioned", entry lands in `mentioned` via technologies.derive
def test_an_id_the_registry_lacks_still_comes_out_with_a_gap(): ...   # "setuptools"
def test_every_sign_carries_its_source(): ...
def test_the_recorded_payload_gives_the_expected_technologies():
    # fixtures-fork/py-fastapi-compose.payload.json -> ids == {"docker", "fastapi", "postgresql", "python", "redis", "setuptools", "sqlalchemy"}
def test_a_fork_that_fails_leaves_the_host_mentions_and_a_gap(): ...
```

- [ ] **Step 2: Vederli fallire**

Run: `python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py`
Expected: FAIL, `No module named 'fork_stack'`.

- [ ] **Step 3: Scrivere `tools/fork_stack.py`**

Quattro funzioni pure più `recognize`. Nessuna espressione regolare; i percorsi con `PurePosixPath`.

- [ ] **Step 4: Vederli passare**

Run: lo stesso comando. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add benchmarks/project-model/tools/fork_stack.py benchmarks/project-model/test_fork_stack.py benchmarks/project-model/fixtures-fork
git commit -m "Translate pre-map facts and stack-analyser evidence for the stack benchmark"
```

### Task 4: Il confronto

**Files:**
- Create: `benchmarks/project-model/modal_stack_fork.py`
- Modify: `benchmarks/project-model/tools/fork_stack.py` (aggiunge `compare`)
- Modify: `benchmarks/project-model/test_fork_stack.py`

**Interfaces:**
- Consumes: `fork_stack.recognize` (Task 3); da `modal_stack.py`: `_project`, `_recording`, `bounded`, `batches`, `code_files`, `code_hash`, `_chosen`, `FIXTURES`, `GIT`; `premap.write`, `premap_replay.replayer`, `snapshot.write_snapshot`, `technologies.derive`, `service_registry.run`, `score.score_technologies`.
- Produces: `results/daodan_stack_fork.json`, e
  - `compare(expected: dict, before: dict, after: dict) -> dict`: `{"lost": [nomi], "gained": [nomi], "new": [id], "gone": [id], "not_in_registry": [id]}`.

`compare`: `lost` sono i nomi attesi (framework per nome e servizi) che `score.score_technologies` trova nel record «prima» e non nel record «dopo»; `gained` il contrario; `new` gli ID di `technologies` presenti solo dopo; `gone` quelli presenti solo prima; `not_in_registry` dai buchi del record «dopo».

`modal_stack_fork.py`, per fixture, nel container:
1. snapshot e pre-mappa con le risposte registrate (scansione completa), come `modal_stack._measure`;
2. `before = technologies.derive(manifest, registry, facts)`; `after` = la stessa chiamata con `service_registry.run` sostituito da `fork_stack.recognize` (`unittest.mock.patch.object`), cronometrate (`seconds.registry_full`, `seconds.fork_full`);
3. pre-mappa di nuovo senza runner (`premap.derive(manifest, store, runner=None)`, la scansione veloce) e le due ricognizioni cronometrate: `seconds.registry_fast`, `seconds.fork_fast`, con `fast_lost`, i nomi attesi che il fork perde rispetto al registro sugli stessi fatti;
4. i processi avviati durante le ricognizioni (`spawned`): `executed_project_code` è `no` se ognuno è il `git` del perimetro o il Node di Daodan con il `cli.mjs` del rilascio.

Prima del primo progetto il container installa Node e il rilascio (`stack_analyser.node`, `stack_analyser.cli`), fuori dai tempi. L'immagine aggiunge a quella di `modal_stack.py` i file `daodan/core/indexers` e `benchmarks/project-model/tools/fork_stack.py`. `fetch` scrive `results/daodan_stack_fork.json`: per fixture `compare(...)`, `fast_lost`, `seconds`, `executed_project_code`, i punteggi prima e dopo; in testa i totali (nomi attesi trovati prima e dopo per framework e servizi, numero di fixture con `lost` non vuoto, mediana e massimo di `fork_fast` e di `registry_fast`).

- [ ] **Step 1: Scrivere i test di `compare` che falliscono**

```python
def test_compare_names_what_is_lost_gained_and_new():
    expected = {"frameworks": [{"name": "FastAPI"}], "services": [{"name": "Redis"}, {"name": "Sentry"}]}
    # before: fastapi, redis, sentry; after: fastapi, redis, setuptools (not in registry)
    assert fork_stack.compare(expected, before, after) == {"lost": ["Sentry"], "gained": [], "new": ["setuptools"],
                                                             "gone": ["sentry"], "not_in_registry": ["setuptools"]}
def test_compare_of_equal_records_is_empty(): ...
```

- [ ] **Step 2: Vederli fallire, scrivere `compare`, vederli passare**

Run: `python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py`

- [ ] **Step 3: Scrivere `modal_stack_fork.py`**

Stessa struttura e stessi comandi di `modal_stack.py` (`spawn`, `fetch`, `--fixtures`, `--families`), app `daodan-pm-stack-fork`, store `project-model/stack-fork`. Le funzioni condivise si importano da `modal_stack`, non si copiano.

- [ ] **Step 4: Una prova su tre fixture (chiedere prima conferma al proprietario: è un giro su Modal)**

```bash
modal deploy benchmarks/project-model/modal_stack_fork.py
python benchmarks/project-model/modal_stack_fork.py spawn --fixtures py-fastapi-compose,js-angular,jvm-spring-boot-managed
python benchmarks/project-model/modal_stack_fork.py fetch --fixtures py-fastapi-compose,js-angular,jvm-spring-boot-managed
```

Expected: tre voci in `results/daodan_stack_fork.json`, ognuna con `executed_project_code: "no"`, `seconds` con le quattro misure e `compare` leggibile. `jvm-spring-boot-managed` è il caso in cui Spring MVC e Data JPA arrivano solo dal modello di Gradle: devono esserci dopo, con fonte `gradle@…`.

- [ ] **Step 5: Commit**

```bash
git add benchmarks/project-model/modal_stack_fork.py benchmarks/project-model/tools/fork_stack.py benchmarks/project-model/test_fork_stack.py
git commit -m "Compare the registry and the stack-analyser release on the stack corpus"
```

### Task 5: Il giro sul corpus e la «Verifica»

**Files:**
- Modify: `benchmarks/project-model/README.md` (sezione nuova «Lo step `stack` dal fork»)
- Create: `benchmarks/project-model/results/daodan_stack_fork.json`
- Create: `benchmarks/project-model/accepted-losses.json`
- Modify: `benchmarks/project-model/test_fork_stack.py`

**Interfaces:**
- Consumes: Task 4.
- Produces, per il piano 3: l'elenco delle perdite accettate e il verdetto sulla «Verifica».

- [ ] **Step 1: Il giro completo (chiedere prima conferma al proprietario)**

```bash
python benchmarks/project-model/modal_stack_fork.py spawn
python benchmarks/project-model/modal_stack_fork.py fetch
```

Expected: una voce per ogni fixture con `expected.json`; `code` uguale ai due lati.

- [ ] **Step 2: Leggere ogni perdita**

Per ogni nome in `lost`, una riga in `accepted-losses.json`: `{"fixture", "name", "id", "reason", "verdict"}`, con `verdict` `accepted` (il registro sbagliava, o è un cambio voluto: `react-email`, `kafka`, `vault`, un segno dichiarato sbagliato, un uso nel codice che la spec mette fuori scopo) o `to_fix` (manca una regola nel fork, o una dichiarazione non arriva). Ogni `reason` nomina il segno di oggi e perché dopo non c'è. Nessun motivo generico.

- [ ] **Step 3: Il test che tiene ferma la «Verifica»**

```python
def test_every_lost_name_of_the_last_round_is_accounted_for():
    # results/daodan_stack_fork.json against accepted-losses.json: every (fixture, name) in `lost` has a line;
    # no line is left over; every reason is longer than 40 characters and no two fixtures share a to_fix-free excuse
def test_no_fixture_of_the_last_round_executed_project_code(): ...
```

- [ ] **Step 4: Scrivere la sezione del README**

Parametri (corpus, rilascio e sha256, comandi, che cosa è «prima» e «dopo», come si misura la scansione veloce) e risultati misurati: totali prima e dopo, perdite `accepted` e `to_fix` per nome, nomi nuovi, ID fuori dal registro, tempi (`registry_fast` contro `fork_fast`: mediana, massimo, la fixture più lenta), fixture senza risposta. In fondo «Verdetto»: la «Verifica» della spec passa se non c'è nessuna riga `to_fix` e se il massimo di `fork_fast` sta sotto la soglia che il proprietario accetta; altrimenti l'elenco di ciò che manca.

- [ ] **Step 5: Commit e fermarsi**

```bash
git add benchmarks/project-model/README.md benchmarks/project-model/results/daodan_stack_fork.json benchmarks/project-model/accepted-losses.json benchmarks/project-model/test_fork_stack.py
git commit -m "Record what the stack-analyser release changes on the stack corpus"
```

Il piano finisce qui. Il verdetto, le righe `to_fix` e i tempi tornano al proprietario: da lì si decide se scrivere il piano 3, correggere prima il fork (un rilascio `1.27.6-daodan.2`) o fermarsi, come dice la riga dei rischi della spec sulla scansione veloce.
