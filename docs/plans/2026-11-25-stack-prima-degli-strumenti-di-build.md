# Lo stack prima degli strumenti di build, e i nomi degli step

**Stato:** piano chiesto dal proprietario il 25 novembre 2026. Nessun codice è cambiato. Sostituisce l'ordine e i nomi della spec della pipeline (`docs/specs/2026-11-15-pipeline-di-analisi.md`, sezione 8) dove dicono altro.

**Goal:** stack-analyser dice per primo com'è fatto il progetto (moduli, pacchetti dichiarati, strumenti di build, tecnologie); gli strumenti di build veri, nel container, vengono dopo e partono solo per ciò che è stato trovato; il codice di Daodan che rilegge a mano gli stessi manifest va via.

**Perché:** oggi gli stessi manifest si leggono tre volte: `daodan/core/build_units.py` (704 righe, circa 35 lettori scritti a mano, con un lettore YAML proprio), stack-analyser, e gli strumenti nel container. Del fork Daodan usa solo le prove delle tecnologie e ne butta via componenti e dipendenze.

## Decisioni del proprietario

1. stack-analyser, il nostro fork, viene prima degli strumenti di build.
2. Lo step che interroga gli strumenti di build nel container resta, dopo: dà ciò che un file non dice (membri risolti, grafo dei pacchetti, versioni risolte, comandi).
3. Ciò che il fork già fa non si rifà in Daodan. Ciò che gli manca si aggiunge al fork.
4. Gli step hanno il numero d'ordine nel nome: `1_list_files`.

## Gli step

| Nome | Che cosa fa | Oggi |
| --- | --- | --- |
| `1_list_files` | Percorre la cartella; di ogni file hash e linguaggio | `file_inventory.write` |
| `2_read_code` | Simboli, import e chiamate di ogni file | `snapshot.write_reading` |
| `3_recognize_stack` | stack-analyser: componenti, pacchetti dichiarati, strumenti di build, tecnologie. Scrive i moduli | `stack`, più la metà di `scan` che legge i file |
| `4_ask_build_tools` | Nel container, lo strumento vero di ogni modulo trovato al 3. Corregge e completa i moduli | i comandi di modello di `scan` |
| `5_link_calls` | Quale funzione chiama quale | `analyze` |
| `6_run_and_observe` | Test e app nel container | `dynamic` |
| `7_assemble_graph` | Unisce e dice cosa manca | `union` |

Il numero è nel nome dello step (`NAME`, eventi, giornale, documenti, interfaccia). Un modulo Python non può iniziare con una cifra: la cartella è `step_1_list_files/`, la classe `ListFiles`. `plan` non è uno step: resta la funzione che è (`pipeline/plan.py`). Lo step `parse` di oggi, che dice solo il piano, sparisce.

## Che cosa dà oggi il fork: prova esplorativa

Rilascio `1.27.6-daodan.5` su 104 fixture di `benchmarks/project-model`, contro `results/daodan_modules.json`. Girata fuori da Modal, con il Node della macchina e non quello di Daodan, non salvata: non è una verifica finché il Task 1 non la rifà.

| | Nel fork | Mancanti |
| --- | --- | --- |
| Moduli di oggi (147) | 101 | 46 |
| Fixture con tutti i moduli | 72 su 104 | |
| Dipendenze dichiarate, per manifest (215) | 153 | 62 |
| Legami fra moduli (23) | 11 | |

Che cosa manca, letto nel sorgente del fork (`feature/stack-detection`, `453a2a9`):

- **Python, 24 moduli su 24.** Il fork legge `pyproject.toml` e `requirements.txt` (`src/rules/spec/python/lockfile.ts`), ma crea un payload di nome `virtual`, e `Payload.recurse` fonde un `virtual` nel padre invece di farne un componente. Il nome del progetto (`[project].name`) non lo usa.
- **CMake, 15 su 15.** Nessuna regola: C e C++ sono riconosciuti solo dall'estensione.
- **Casi singoli:** `project.json` di Nx (2), `deno.json`, `build.sbt`, un modulo Terraform, un `settings.gradle.kts` composito, un progetto Yarn Berry.
- **Non dato:** l'appartenenza a un workspace, la riga di ogni dipendenza.

## Vincoli

- **Regola invalicabile.** Il fork legge file e non esegue nulla del progetto; il passo 4 gira solo nel container.
- **Senza motore di container** i moduli sono quelli del passo 3, con la lacuna che dice cosa il passo 4 avrebbe aggiunto.
- **Un lettore di `build_units.py` si toglie solo quando** il benchmark del Task 1 dice che per il suo tipo di manifest il fork dà gli stessi moduli e le stesse dipendenze. Fino ad allora resta, con scritto accanto perché.
- **Niente gira qui:** fork su GitHub Actions, Daodan su Modal.

## Task

- [ ] **1. La misura, come benchmark.** `benchmarks/stack-components/`: per ogni fixture i componenti del fork contro i moduli di oggi, per tipo di manifest (moduli, dipendenze, legami, workspace). Su Modal, con il Node di Daodan. Il README dichiara parametri e risultati. È il cancello dei Task 5 e 6.
- [ ] **2. Fork: Python.** Un `pyproject.toml` con `[project].name` (o `[tool.poetry].name`) è un componente con quel nome; un `requirements.txt` da solo resta com'è. Test nel fork.
- [ ] **3. Fork: ciò che Daodan usa e il fork non dà.** Il tipo di unità (workspace, membro), i membri dichiarati di un workspace, la riga di ogni dipendenza. Poi i tipi mancanti, uno per volta e solo se il Task 1 li conta: Nx, Deno, sbt, Terraform, CMake.
- [ ] **4. Fork: rilascio `.6`**, fissato in `stack_analyser.py`, `tests/modal_pytest.py` e nei benchmark.
- [ ] **5. Daodan: i moduli dai componenti.** `3_recognize_stack` gira il fork sull'inventario e scrive `modules.json` dai componenti. I lettori di `build_units.py` e quelli dei pacchetti della pre-mappa si tolgono per tipo di manifest, secondo il Task 1.
- [ ] **6. Daodan: `4_ask_build_tools` dopo.** Le sorgenti con comandi partono per gli strumenti che il passo 3 ha trovato. Le sorgenti dei framework (Next.js, Nuxt, SvelteKit, React Router, Angular, Astro) chiedono al passo 3 dov'è il loro framework invece di riaprire ogni `package.json` (`premap/frameworks.py`).
- [ ] **7. Daodan: i nomi.** `NAME` degli step, eventi, giornale, cartelle, documenti, interfaccia. Un giornale scritto con i nomi di prima si legge ancora.
- [ ] **8. Documenti.** `README.md` («How the graph is built»), `docs/plugins/codebase-map.md` («Pipeline»), la spec della pipeline.

## Da decidere

1. **CMake nel fork o solo nel container?** Un `CMakeLists.txt` è codice: i target li dice solo CMake eseguito. Proposta: il fork riconosce che c'è CMake e in quali cartelle; i target restano del passo 4.
2. **Le tecnologie dopo il passo 4.** Oggi `stack` gira due volte, perché i comandi nel container danno pacchetti nuovi (Renovate, Compose, lock). Proposta: il fork gira una volta sola al passo 3; il passo 4 aggiunge i suoi segni al record con `technologies.merge`, senza rilanciare il fork.
3. **`2_read_code` prima di `3_recognize_stack`.** È l'ordine in cui il codice gira oggi; il disegno del 22 novembre metteva la lettura dopo. Il numero dice l'ordine vero: se si sposta, cambiano i nomi da 2 a 4.
4. **Renovate.** È un terzo lettore dei pacchetti. Dopo il Task 5 va misurato che cosa dà in più del fork.
