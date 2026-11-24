# Piano: stack dal fork, il passaggio

**Stato:** In parte. Il passaggio è nel codice e in `develop` dal 24 novembre 2026: `technologies.derive` chiama `stack_recognition.run`, il rilascio fissato in `daodan/core/stack_analyser.py` è `1.27.6-daodan.5` e il registro è l'anagrafica generata dal catalogo del fork. Restano aperte le prove su Modal: il passo 4 del Task B4 e il Task B6. Il fork è [`acaprino/stack-analyser-daodan`](https://github.com/acaprino/stack-analyser-daodan).

**Spec:** [`2026-11-21-stack-dal-fork.md`](../specs/2026-11-21-stack-dal-fork.md), «Verifica». **Misura prima del passaggio:** [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Lo step `stack` dal fork».

## Fatto

- **Parte A, il fork:** perimetro da un file, catalogo, nome `stack-analyser-daodan`, rilasci `.3`, `.4` e `.5`. `.3` pubblicato. Il rilascio `.4`, con le correzioni trovate dalla prova di B4 (ramo `feature/stack-detection`, `69c77c2`…`348051b`, CI verde), è pubblicato (tag `v1.27.6-daodan.4`, costruito da GitHub Actions da `ff2fef4`). Il rilascio `.5` (tag `v1.27.6-daodan.5`, da `453a2a9`) riprende i segni veri che il porting aveva lasciato fuori (la scelta del proprietario: «più cose riconosciamo e meglio è») e dà a uno starter di Spring Data il suo server; Daodan è fissato a `.5`.
- **B1, lo strumento sul rilascio:** `feat: lo strumento passa il perimetro in un file e legge il catalogo del rilascio .3`.
- **B2, la traduzione nel prodotto:** `daodan/core/stack_recognition.py`, `tests/test_codebase_map_stack_recognition.py`.
- **B3, la regola delle fonti:** una scansione sostituisce i segni delle fonti che ha eseguito e conserva gli altri (`tests/test_codebase_map_stack_sources.py`).
- **B4, il passaggio e le rimozioni:** passi 1–3 (sotto, con i numeri della suite); il passo 4 è aperto.
- **B5, il registro come anagrafica:** `feat: il registro è l'anagrafica, generata dal catalogo di stack-analyser`.
- **B7, i documenti:** fatti. I tempi di B6 non ci sono: i documenti danno quelli del piano 2, detti tali, e dicono che dopo il passaggio non sono misurati.

## Scelte confermate dal proprietario il 24 novembre 2026

1. **Nome.** Il pacchetto e il repository diventano `stack-analyser-daodan` (con la s, come l'originale), dal rilascio `.3`. Il file `LICENSE` conserva la nota di Specfy.
2. **Menzioni delle variabili.** Non si tengono: `check_env` si toglie come dice la spec (2.6). Nessun modulo di Daodan legge `mentioned`.
3. **File vietati.** Daodan passa al fork, nel perimetro, i file che `is_forbidden` vieta. Il fork quindi non apre più i `.env` di esempio e la prova di tipo `env` non compare più.
4. **Test con il riconoscimento vero.** Girano dove c'è il rilascio, cioè nell'immagine dei test su Modal (`DAODAN_STACK_ANALYSER`); in locale si saltano con il motivo. È la regola di AGENTS.md sugli strumenti veri.
5. **Segni conservati.** Un segno di una fonte che non ha girato resta, con la scansione da cui viene, finché il suo file esiste sul disco; se il file non c'è più, il segno si toglie.
6. **Servizi generici in più** (`azure`, `aws`, `google`, `gcp`, `firebase`…): restano come li dà il fork; il giro li riporta fra i servizi «in più».
7. **La tabella di supporto** perde la colonna dei segni per tipo e dice se il fork ha una regola per la voce.

## Vincoli

- **Regola invalicabile.** Il fork legge file e non esegue nulla del progetto; la prova su Modal passa con l'installazione vera e con il Node di Daodan.
- **Un solo riconoscitore.** Dopo il Task B4 nessun modulo sotto `daodan/` confronta nomi di pacchetti, file o variabili con segni del registro. `registry_hosts.py` resta l'unica lettura di Daodan (2.4).
- **Forma di `technologies.json`.** Restano `schema`, `technologies`, `mentioned`, `units`, `modules`, `configured_services`, `checkers`, `gaps` e, di ogni segno, `sign`, `value`, `path`, `line`, `strength`. Si aggiungono a ogni segno `source` e `scan`. I consumatori provano solo `sign == "package"` e `strength`: un'immagine, un'azione e una risorsa Terraform restano `sign: "package"`, come oggi; `file` e `source` restano tali; le prove `extension` non escono.
- **ID stabili**, con le rinomine del porting (`react-email` → `reactemail`, `kafka` → `apache_kafka`, `vault` → `hashicorp_vault`).
- **Riuso**: `engine_tools`, `indexers.runtime.node`, `source_files.is_forbidden`, `snapshot_store`, `registry_hosts.check_hosts`. Nessuna espressione regolare su sorgenti; `tests/test_codebase_map_patterns.py` non concede `re` a un file nuovo.
- **Errori come buchi**: nessun errore del fork o della traduzione ferma il passo; diventa un controllore `failed` e un buco con la causa, e i segni di prima restano.
- **Nel fork**: nessun concetto di Daodan nel codice (il nome del pacchetto non è codice); `reason`, `dependencies.detect`, `tech.detectInFileList` invariati; `npx vitest run --coverage.enabled=false`; mai `npm install`/`npm ci` nel repository.
- **Modal e pubblicazioni**: ogni giro su Modal, ogni push, tag, rilascio e la rinomina del repository si fanno solo dopo la conferma del proprietario, e li lancia chi coordina.
- Commit nello stile di ciascun repository (fork: `feat: …` in inglese; Daodan: prefisso e frase in italiano).

## Punti da presidiare

1. **Dopo una modifica spariscono tecnologie.** Scansione completa, poi modifica di un file e scansione veloce: le tecnologie che venivano da Renovate o da un build tool devono restare, con la scansione da cui vengono. Test: B3, `test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run`.
2. **Il fork non parte.** Senza rete al primo uso, senza disco, Node non installabile: il passo finisce, conserva i risultati e scrive il buco; non ritenta a ogni scansione. Test: B1, `test_an_install_that_failed_is_not_tried_again_in_the_same_process`; B3, `test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why`.
3. **Un progetto grosso su Windows.** 760 percorsi esclusi: il perimetro viaggia in un file. Test: A1, `reads a perimeter of five thousand paths`; B1, `test_the_perimeter_reaches_the_fork_in_a_file`.
4. **Un file vietato viene aperto.** `.env.example` in una cartella viva: deve stare nel perimetro. Test: B2, `test_a_forbidden_file_is_in_the_perimeter`; e sul rilascio vero la prova di B6.
5. **Un segno conservato su un file cancellato.** Deve sparire con il file. Test: B3, `test_a_kept_sign_leaves_with_its_file`.

## Aperto

### Task B4: Il passaggio e le rimozioni

**Files:**
- Modify: `daodan/core/technologies.py`, `daodan/core/service_registry.py`, `daodan/core/registry_build.py` (toglie l'import di `stack_source`), `tests/conftest.py`
- Delete: `daodan/core/stack_source.py`, `daodan/core/specfy_rules.mjs`, `tests/specfy_rules.test.mjs`, `benchmarks/project-model/tools/specfy_daodan.py`, `benchmarks/project-model/replay_registry_coverage.py`, `benchmarks/project-model/replay_stack_packages.py`, `benchmarks/project-model/tools/daodan_registry.py` e i loro test
- Modify (test): `tests/test_codebase_map_service_registry.py`, `tests/test_corpus_backend_rules.py`, `tests/test_corpus_docker_images.py`, `tests/test_corpus_service_rules.py`, `tests/test_corpus_system_rules.py`, `tests/test_corpus_web_rules.py`, `tests/test_registry_hosts.py`, `tests/test_codebase_map_stack_rationalized.py`, `tests/test_daodan_package.py`, e i test che passano da `technologies.ensure` (`premap_packages`, `stack_compose`, `flows`, `mcp`, `app`, `visual`, `pipeline`)

**Interfaces:**
- Consumes: B2, B3.
- Produces: `technologies.derive` chiama `stack_recognition.run`; `service_registry` conserva `load`, `mark_file`, `entry_category`, `step1_packages`, `package_key`, `service_site`, `_is_excluded`, `_split_declared_in`, `Project`, `REGISTRY`; non ha più `check_packages`, `check_files`, `check_env`, `CHECKERS`, `run`, `recognize`.

`source_files.STACK_SOURCE_LANGUAGES` resta: è ciò che fa entrare nella snapshot i file `.swift`, `.ex`, `.exs`, `.php`, che il fork legge da solo.

Test:
- `tests/conftest.py` offre `real_stack`: con `DAODAN_STACK_ANALYSER` nell'ambiente sostituisce `stack_analyser.cli` e `node` con quelli dell'immagine; senza, salta il test con il motivo «il riconoscimento vero gira dove c'è il rilascio (tests/modal_pytest.py)» (scelta 4).
- I test che affermano una tecnologia riconosciuta da un progetto (i `test_corpus_*`, `RecognizeTests`, quelli indiretti) usano `real_stack` e le loro attese restano, con gli ID del fork.
- I test dei controllori (`CheckerTests`, i casi parametrizzati di `check_packages`/`check_files`) si tolgono: per ognuno si cerca il caso equivalente nei test del fork (`src/rules/packageIdentities.test.ts`, `files.test.ts`); quelli che mancano si elencano nel rapporto del task, e chi coordina decide se portarli nel fork.
- I test che costruiscono un record a mano non cambiano.

- [ ] **Step 1**: `conftest.py` e i test adattati; **Step 2**: il cambio in `derive` e le rimozioni; **Step 3**: `python -B -m pytest -q -p no:cacheprovider tests` in locale (nessun fallimento; i salti con il motivo); **Step 4 (chi coordina, dopo conferma)**: la suite su Modal, dove `real_stack` è attivo; commit `feat: lo stack riconosce solo attraverso stack-analyser`.

*Stato, 24 novembre 2026: Step 1–2 e commit fatti (`091c093`, poi `2f57d91`). Step 3 con il rilascio vero `.3` (`DAODAN_STACK_ANALYSER`, container Linux con Node 22): 4.401 passati, 11 falliti, 140 saltati; gli 11 si correggono con `.4` (Task A3). Con `.4` fissato, suite locale (non Modal) sullo stesso container, Node v22.23.5: 4.415 passati, 0 falliti, 140 saltati; senza il rilascio 4.316 passati, 0 falliti, 239 saltati. Step 4 aspetta Modal, che dalla macchina di questo lavoro non si raggiunge.*

### Task B6: Le prove vere

**Files:**
- Modify: `tests/test_codebase_map_host_programs.py`, `tests/modal_pytest.py`, `benchmarks/project-model/modal_stack.py`, `benchmarks/project-model/README.md`, `benchmarks/project-model/results/daodan_stack.json`
- Delete: `benchmarks/project-model/modal_stack_fork.py`, le misure del confronto in `tools/fork_stack.py` e i loro test, `accepted-losses.json`

- La prova «nulla viene eseguito» chiama il `cli()` vero (con `shared_engine_dir` in una cartella temporanea) e il Node di Daodan (`runtime.node`), e ha un vettore in più: un `.env.example` in una cartella viva, che il fork non deve aprire. Il controllo è sul perimetro passato e sull'assenza di prove `env`.
- `modal_stack.py` misura il prodotto: l'immagine ha Node 22 e il rilascio; per fixture registra anche il tempo della scansione veloce, il numero di dichiarazioni e la lunghezza del perimetro.
- Il confronto con il registro non esiste più nel codice: il README confronta il giro nuovo con l'ultimo giro con il registro, che resta nei risultati committati.

- [ ] **Step 1**: codice e test locali; **Step 2 (chi coordina, dopo conferma)**: la prova su Modal; il giro sul corpus; **Step 3**: la sezione del README con parametri, risultati, «Non misurato» e verdetto sulla «Verifica»; commit.

*Stato, 24 novembre 2026: Step 1 in corso. Step 2 aspetta Modal. Step 3 aspetta lo Step 2.*
