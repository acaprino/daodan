# Lo stack prima dei moduli, i punti di ingresso a sé, e i nomi degli step

**Stato:** piano chiesto dal proprietario il 25 novembre 2026. Nessun codice è cambiato. Il disegno è nella spec della pipeline (`docs/specs/2026-11-15-pipeline-di-analisi.md`, sezione 8, aggiornata il 25 novembre); qui i task, le misure e le scelte aperte.

**Goal:** ogni step ha una competenza sola. stack-analyser analizza lo stack: dice quali strumenti di build, toolchain, framework e tecnologie ci sono, e dove. Non trova i moduli. Lo step dopo prende ciò che è stato trovato e usa quegli strumenti di build per trovare i moduli e le loro dipendenze.

**Perché:** oggi il riconoscimento è sparso. Ogni sorgente della pre-mappa decide da sé se il suo strumento c'è, cercando il suo file nell'inventario; le sorgenti dei framework riaprono ogni `package.json` (`premap/frameworks.py`); e i moduli si trovano prima che lo stack sia noto.

## Decisioni del proprietario

1. stack-analyser, il nostro fork, analizza lo stack e basta. I moduli non sono suoi.
2. Uno step dopo trova i moduli, usando gli strumenti di build che lo stack ha trovato.
3. Chi riconosce è uno solo: ciò che il fork già riconosce non si riconosce di nuovo in Daodan. Uno strumento che il fork non conosce si aggiunge al fork.
4. Gli step hanno il numero d'ordine nel nome: `1_list_files`.
5. Gli strumenti dei framework servono a fare nodi e archi del grafo: non stanno nella pre-mappa. Il codice va cambiato.

## Gli step

| Nome | Competenza | Oggi |
| --- | --- | --- |
| `1_list_files` | L'elenco dei file: di ognuno hash e linguaggio | `file_inventory.write` |
| `2_read_code` | Simboli, import e chiamate di ogni file | `snapshot.write_reading` |
| `3_recognize_stack` | Lo stack: strumenti di build, toolchain, framework, tecnologie, ognuno con il file che lo prova | `stack` |
| `4_find_modules` | I moduli, le loro dipendenze, i comandi di test e di avvio: per ogni strumento di build trovato al 3, il suo adattatore | `scan` |
| `5_find_entry_points` | Dove entra un utente o una richiesta: rotte, pagine, eventi, legati alle funzioni. Per ogni framework trovato al 3, il suo strumento | sorgenti di `scan` (`premap/nextjs.py`, `react_router.py`, `nuxt.py`, `sveltekit.py`, `angular.py`, `astro.py`, `noir.py`), più `entries.py` e `binder.py`, che oggi girano dopo la pipeline |
| `6_link_calls` | Quale funzione chiama quale | `analyze` |
| `7_run_and_observe` | Test e app nel container | `dynamic` |
| `8_assemble_graph` | Unisce e dice cosa manca | `union` |

Dopo il 4 le tecnologie si assegnano ai moduli: è una unione di due uscite, non un riconoscimento.

Il numero è nel nome dello step (`NAME`, eventi, giornale, documenti, interfaccia). Un modulo Python non può iniziare con una cifra: la cartella è `step_1_list_files/`, la classe `ListFiles`. `plan` resta la funzione che è (`pipeline/plan.py`); lo step `parse` di oggi, che dice solo il piano, sparisce.

## Che cosa dice oggi il fork degli strumenti di build: prova esplorativa

Rilascio `1.27.6-daodan.5` su 104 fixture di `benchmarks/project-model`: per ogni modulo che Daodan trova oggi (`results/daodan_modules.json`), il fork nomina uno strumento o un runtime sul file che lo dichiara? Girata fuori da Modal, con il Node della macchina, non salvata: non è una verifica finché il Task 1 non la rifà.

| Tipo di modulo | Moduli | Con uno strumento nominato | Che cosa nomina |
| --- | --- | --- | --- |
| npm | 41 | 41 | `nodejs` |
| Cargo | 14 | 14 | `cargo`, `rust` |
| Go | 13 | 13 | `golang` |
| Gradle | 18 | 17 | `gradle` |
| Maven | 7 | 7 | `maven` |
| Python | 24 | 21 | il backend di build (`hatchling`, `setuptools`), non Python |
| .NET, Composer, Bundler, pub, mix, Swift, Deno | 11 | 11 | `nuget`, `phpcomposer`, `bundler`, `dart`, `elixir`, `swift`, `deno` |
| CMake | 15 | 0 | nessuna regola nel fork |
| Nx (`project.json`), sbt, Terraform | 4 | 0 | |

Nel catalogo del fork mancano del tutto: CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK e MSBuild, Mix. Daodan ha un adattatore per ognuno.

## Vincoli

- **Regola invalicabile.** Il fork legge file e non esegue nulla del progetto; uno strumento di build gira solo nel container.
- **Una competenza per step.** Nessun codice di `4_find_modules` cerca da sé se uno strumento c'è: lo legge dall'uscita del 3.
- **Senza motore di container** `4_find_modules` usa i lettori dei file dello strumento trovato (`build_units.py`) e dichiara la lacuna di ciò che lo strumento vero avrebbe aggiunto.
- **La pre-mappa è solo il modello di build:** moduli, toolchain, pacchetti, comandi di test e di avvio, servizi. Rotte, pagine ed eventi (`framework_entries`, `noir_entries`) escono da lì e vanno nell'uscita di `5_find_entry_points`.
- **Un lanciatore solo.** Il meccanismo che esegue un comando nel container e ne legge l'uscita (`premap/container_runner.py`) diventa un servizio comune agli step 4 e 5: oggi è della pre-mappa, ed è il motivo per cui gli strumenti dei framework sono finiti lì.
- **Niente gira qui:** fork su GitHub Actions, Daodan su Modal.

## Task

- [ ] **1. La misura, come benchmark.** `benchmarks/stack-build-tools/`: per ogni fixture, gli strumenti di build che il fork nomina (con cartella) contro quelli che le sorgenti di oggi trovano da sé. Su Modal, con il Node di Daodan. Il README dichiara parametri e risultati.
- [ ] **2. Fork: gli strumenti che mancano.** Una regola per CMake, Bazel, Meson, Make, autotools, sbt, .NET SDK, Mix e Nx (`project.json`), e Python nominato su `pyproject.toml` e `requirements.txt`. Solo riconoscimento: nessun componente nuovo. Rilascio `.6`, fissato in Daodan.
- [ ] **3. Daodan: l'anagrafica degli strumenti di build.** `daodan/data/build-tools.json`: per ogni tecnologia del fork che è uno strumento di build o una toolchain, l'adattatore di `4_find_modules` che la usa. Un test dice quale adattatore non ha una voce e quale voce non ha un adattatore.
- [ ] **4. Daodan: `3_recognize_stack` prima.** Il fork gira sull'inventario, senza moduli e senza pre-mappa. Scrive lo stack con, di ogni voce, file e cartella.
- [ ] **5. Daodan: `4_find_modules` dopo.** Per ogni strumento trovato parte il suo adattatore, lettore e comando. Si toglie da ogni sorgente la ricerca del proprio file nell'inventario. Poi le tecnologie si assegnano ai moduli.
- [ ] **6. Daodan: `5_find_entry_points`.** Le sorgenti dei framework e Noir escono da `premap.SOURCES` e scrivono un'uscita loro; `binder.bind` gira dentro lo step. La sorgente di Angular non legge più i componenti per conto suo: li trova già letti dal 2. Chi legge `framework_entries` dalla pre-mappa passa alla nuova uscita: `dynamic/app.py`, `flow_entries.py`, 15 file di test e 10 di benchmark.
- [ ] **7. Daodan: i nomi.** `NAME` degli step, eventi, giornale, cartelle, documenti, interfaccia. Un giornale scritto con i nomi di prima si legge ancora.
- [ ] **8. Documenti.** `README.md` («How the graph is built»), `docs/plugins/codebase-map.md` («Pipeline»), la spec della pipeline.

## Da decidere

1. **I pacchetti che solo il passo 4 conosce.** Oggi Daodan passa al fork i pacchetti risolti da lock, Compose e Renovate, e per questo `stack` gira due volte. Con lo stack prima, quei pacchetti arrivano dopo. Proposta: il fork gira una volta al passo 3; il passo 4 aggiunge i suoi segni al record (`technologies.merge`) senza rilanciarlo.
2. **I lettori di `build_units.py`.** Restano come ripiego di `4_find_modules` senza container, scelti dallo stack, o si tolgono e senza container i moduli sono una lacuna?
3. **`2_read_code` prima di `3_recognize_stack`.** È l'ordine in cui il codice gira oggi; il disegno del 22 novembre metteva la lettura dopo. Il numero dice l'ordine vero: se si sposta, cambiano i nomi da 2 a 4.
4. **Django, FastAPI e Flask.** Le tre sorgenti sono scritte e non collegate: sulle applicazioni misurate Noir dava le stesse rotte. Restano fuori anche da `5_find_entry_points`, o entrano?
5. **go-enry.** Oggi gira in `scan` e dà il linguaggio di ogni file e i file da lasciare fuori, ma la lettura non lo usa. Con il modulo del linguaggio in `1_list_files`, resta o si toglie?
