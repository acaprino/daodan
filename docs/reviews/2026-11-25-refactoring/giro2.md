# Secondo giro: spec e piano, 25 novembre 2026

**Documenti:** `docs/specs/architettura.md` e `docs/plans/refactoring.md` al commit `acc7e6e29`. **Revisori:** tre agenti nuovi `general-purpose`, `fable`, effort `medium`, un solo giro, tutti completati; sola lettura e divieto di aprire `docs/reviews/` sono istruzioni, non limiti degli strumenti.
**Conteggio (30):** 7 bloccanti, 19 importanti, 4 gruppi minori; diversi doppioni fra revisori. Il giro non è pulito. Nessuna modifica applicata.

## Controlli del coordinatore (confermati)

- Il file di confronto di `T0.A.3` non esiste né su disco né nella storia (`R2`, `C1`).
- `tests/modal_pytest.py` non porta un motore di container: la sonda indicata risulterebbe verde sui test saltati (`R3`, `C2`).
- `T0.A.1` dice «in attesa di commit», ma i quattro file sono già in `c1cc46606`, pubblicato dal coordinatore come `wip` (`R1`, `C3`).
- `container.leaves` e `container.reached` non provano l'uscita di rete (`R3`, `C4`).

## Classificazione

| Gruppo | Id | Categoria |
| --- | --- | --- |
| Stato di `T0.A.1`, file di confronto mancante, sonda non eseguibile, righe di riferimento superate | R1, R2, R3, C1, C2, C3, C4, R10, C9, C10, Z10 | PROPOSE FIX: correggere i fatti; dove serve scegliere (rilanciare `baseline`, dove far girare un motore vero) decide il proprietario |
| Correzione di rete in fondo al piano; catena tutta lineare | Z3, Z4 | ESCALATE |
| Rete: troppa macchina per il primo passo | Z5 | ESCALATE: la regola è del proprietario |
| Spec e piano diversi (UI a otto step, comando dell'utente, `go-enry`, controlli di `T3.A`) | Z8, C5, C6 | ESCALATE |
| Problema da risolvere; Django, FastAPI, Flask | Z1, Z2 | ESCALATE: aperti anche dal primo giro |
| `build-tools.json`, modello di evidenza, backend | Z6, Z7 | ESCALATE |
| Decisioni riaperte o lasciate a chi esegue; corse «coerenti»; `T1`–`T3` | Z9, R4–R9, C7, C8 | ESCALATE |

**Scelta dell'utente:** «Applica». Applicate al solo piano le correzioni di fatto (PROPOSE FIX): stato di `T0.A.1`, riferimento di `T0.A.3` mancante (diventato scelta aperta), sonde di rete, righe di riferimento. Le ESCALATE restano aperte; un solo giro, fermato dall'utente.

## Testo integrale: Visione d'insieme (`Z`)

Zoom-out su architettura.md e refactoring.md, parte 1 di 2 (rilievi 1-5). Verifiche fatte sul repository in sola lettura; docs/reviews/ non aperta.

1. BLOCKER (per T1, non per T0.A) — Manca il problema che il refactoring risolve.
Dove: spec, intestazione e «Principi»; piano, scelta `B2` (riga 65) e Cancelli T1/T2.
La spec descrive l'arrivo ma non dice quale difetto misurabile giustifica 8 step, piano unico e spostamento delle sorgenti. Il piano lo ammette (`B2`) e tuttavia dettaglia già T1-T3 sopra una motivazione assente; l'opzione (b) di `B2` ridurrebbe T1. I cancelli controllano la struttura (`premap.SOURCES` svuotato, step rinominati), non un risultato prima/dopo sul campione. Rimedio: chiudere `B2` prima di ogni altro dettaglio di T1 e scrivere nel Cancello T1 almeno una misura di esito.

2. BLOCKER — Django, FastAPI, Flask: la spec decide ciò che le misure smentiscono.
Dove: spec, tabella «Strumenti nativi» riga 43 e «Convivenza» riga 48; piano T1.12, riga T1.C della mappa, Cancello T1; backlog, tabella «Fermo o ritirato» (Spring).
La spec le dà `[deciso]` e «primarie». Il piano registra tre benchmark chiusi con «no» sulle applicazioni vere (0 funzioni su 132 su Django; FastAPI non carica nessuna delle due app; Flask scollegato il 24 novembre). Spring è stato ritirato per lo stesso motivo. In più la spec costruisce sopra questo percorso un'unione deduplicata con chiave contesto/mount/router e una diagnostica dei conflitti. Verificato: nessuna delle tre è in `premap.SOURCES` né in `FRAMEWORK_SOURCES`. Rimedio: toglierle dal contratto di arrivo finché `B1` non porta una misura nuova; fino ad allora Noir, come per Spring.

3. MAJOR — L'ordine del piano non segue il rischio che la spec mette per primo.
Dove: spec, Principio 6 e «Servizi comuni» righe 135-136; piano, mappa (catena «Bloccata da») e T3.1.
La spec dichiara aperto oggi il confine più importante: il proxy apre gli host dichiarati dal progetto, controlla nome e porta ma non l'IP risolto, nessun `--cap-drop` né `--user` (verificato in `container.py`: solo `no-new-privileges` alle righe 867, 1113, 1413, 1557). La correzione è in T3.A, ultima, dietro riordino degli step e SCIP, con cui non ha dipendenze tecniche. `M1/I1` anticipa solo la sonda, non il rimedio. Rimedio: separare l'indurimento che non chiede interfaccia (`--cap-drop`, `--user`, controllo dell'IP risolto, ritiro degli host dichiarati con lacuna) e metterlo subito dopo T0; lasciare in T3 solo popup e scelta del proxy.

4. MAJOR — La catena è tutta lineare anche dove le tranche sono indipendenti.
Dove: piano, mappa di avanzamento, colonna «Stato».
Dodici tranche, ognuna bloccata dalla precedente. `list_files` (T1.A), la prova SQL (T1.5), l'indurimento del container (T3.A) e la diagnosi dello `0/19` non dipendono l'una dall'altra. Un solo ritardo ferma tutto, e le voci a rischio alto restano in fondo. Rimedio: dichiarare solo le dipendenze vere. La diagnosi statica dello `0/19` costa zero corse LLM e può rispondere a `B2`: va resa obbligatoria in T0, non opzionale (`I2`).

5. MAJOR — Uscita di rete con approvazione: più macchina di quanta ne serva al primo passo.
Dove: spec, «Servizi comuni» righe 136-144; piano T3.1, T1.16, scelte `M4`, `M8`, «Popup GUI».
Quattro risposte, whitelist più blacklist, richiesta preventiva, rilancio del passo, popup con indirizzo risolto, confronto Smokescreen contro proxy attuale. La scelta aperta di T3.A mostra già la versione minima: rifiuto e lacuna `approval_required`, con la whitelist in un file. Inoltre lo stato `in attesa di approvazione` entra nel piano in T1.D, due traguardi prima che qualcosa possa produrlo (verificato: `approval_required` e `host_denied` non esistono in `daodan/`). Rimedio: prima versione con rifiuto, lacuna e whitelist; blacklist, «blocca sempre» e stato di attesa entrano con il popup.

Zoom-out su architettura.md e refactoring.md, parte 2 di 2 (rilievi 6-10).

6. MAJOR — `build-tools.json` e dieci famiglie nel fork: riordino senza difetto nominato.
Dove: spec, riga 33 e tabella anagrafiche riga 126; piano T1.6-T1.9, scelte `M2`, `M3`.
Verificato: `premap/` ha già `cmake.py`, `bazel.py`, `meson.py`, `make.py`, `autotools.py`, `sbt.py`, `dotnet.py` dentro `premap.SOURCES`, e ognuno trova il proprio manifesto; `pipeline_tree.py` legge già queste dichiarazioni dal codice. Il disegno aggiunge lo stesso riconoscimento in un secondo repository (il fork) più un file che lega le due parti, con un test per tenerli allineati: tre punti da mantenere al posto di uno. `M3` chiede ancora «quale difetto correggono». Rimedio: nessuna famiglia nel fork e nessun `build-tools.json` finché `M3` non nomina un difetto; se serve solo l'ordine fra gli step, l'adattatore può dichiarare da sé la voce dello stack che lo attiva.

7. MAJOR — Modello di evidenza e backend runtime: astrazioni per un solo adattatore.
Dove: spec, righe 44, 45, 49, 50; piano T2.1 (`M5`), T3.3 (`M6`).
`link_calls`: «primo adattatore dietro un piccolo modello interno», ma l'adattatore è uno e LSIF/LSP sono esclusi. Verificato: `edge_grading.py` ha già `ambiguous-target` e `unresolved`, `edge_store.py` ha `verdict`, `resolver`, `confidence`. `M5` chiede ancora che cosa manchi: la spec fissa i campi prima di saperlo. `run_and_observe`: la spec elenca OpenTelemetry, `strace` ed eBPF, ma il piano accerta che Python è già su `sys.monitoring`, il profiler V8 è ritirato, il container non concede eBPF e `strace` non c'è. Rimedio: nella spec una riga per ciascuno («il sito di chiamata viene da tree-sitter»; «i registratori restano»), e il confronto solo davanti a un difetto misurato.

8. MAJOR — Spec e piano non dicono la stessa cosa in quattro punti.
- Interfaccia: la spec («L'interfaccia segue la pipeline», riga 114) mette nel contratto di arrivo la UI a 8 step e l'uscita delle parole interne; il piano la dichiara fuori da T1 e il backlog (§3) la differisce. Però T3.A ha bisogno del popup, e la spec dice che si approva solo dalla GUI.
- Comando `confermato` dell'utente: nella spec è «Proposta, da confermare prima di T3.B»; nel piano T3.2 è lavoro già pianificato e non compare fra le scelte aperte di T3 né nella riga T3.B della mappa.
- `go-enry`: usato nel passo T1.A (punto 4), ma la scelta è assegnata a T1.B, cioè dopo.
- T3.A aggiunge tabella chiusa dei comandi, rifiuto dei lockfile con URL e neutralizzazione degli script di lifecycle: la spec nomina solo il parser dei lockfile «come controllo preventivo».
Rimedio: la spec tenga solo ciò che il piano T0-T3 consegna e segni il resto come fuori perimetro.

9. MAJOR — Troppe decisioni riaperte per un piano che si dichiara eseguibile, e dettaglio prematuro.
Dove: piano, legenda e blocchi «Scelte aperte» di T0-T3; Regola 1.
Venti scelte aperte, otto delle quali `[deciso — riaperto]`: la spec le scrive come contratto, il piano come domande. La Regola 1 chiede dettaglio solo per il traguardo aperto, ma T1-T3 citano già righe di codice (`container.py` 867, 1113, 1413, 1557; `dynamic/__init__.py:248`) che cambieranno prima di arrivarci. La regola di rete è scritta tre volte (spec, T0.7, T3.1). Rimedio: T1-T3 ridotti a obiettivo, scelte da chiudere e cancello; nella spec via sigle di tranche e note «oggi nel codice», che sono stato del piano.

10. NIT — Stato del piano non allineato al repository, e costo del cambio di nomi.
- T0.A.1 dice «nel working tree, in attesa di commit»: i quattro file sono già nel commit `c1cc46606` («wip(registry): la rigenerazione tiene le tessere»), con messaggio diverso da quello previsto. `docs/verification/2026-11-25-baseline-t0.md` non esiste ancora.
- Nomi degli step: sei nel codice (`STEPS = (Scan, Stack, Parse, Analyze, Dynamic, Union)`), sette nel README, otto nella spec, due elenchi in `pipeline_tree.py`. Il cambio arriva in T1.D, dopo che T1.B e T1.C hanno già spostato codice sotto i nomi vecchi, e T0.B.3 riscrive la documentazione per uno stato provvisorio. Se `B2` conferma gli 8 step, il cambio di nomi conviene prima degli spostamenti.

Giudizio: contesto sufficiente per T0, non per T1. I due blocker si chiudono con decisioni del proprietario (`B2`, `B1`), non con altro testo.
Prossimo passo: correggere la riga T0.A.1 del piano con lo SHA `c1cc46606`.

## Testo integrale: Prontezza del piano (`R`)

Prontezza di `docs/plans/refactoring.md`: non eseguibile così com'è sulla tranche aperta. 2 Blocker, 6 Major, 1 Nit. Verifiche fatte in sola lettura sul repository (nessuna esecuzione).

**1. Blocker — `T0.A.1`: lo stato dichiarato non è quello del repository** (r.5, 15, 48-49, 75)
Il piano dice «codice e test già scritti nel working tree, in attesa di commit». `git status` non ha file tracciati modificati; il commit `c1cc46606 wip(registry): la rigenerazione tiene le tessere` tocca già i quattro file elencati ed è su `origin/develop`. Il commit prescritto `fix(registry): ...` non ha nulla da committare e non è scritto quale SHA sia il candidato `C` della Regola 4. Rimedio: scrivere che la correzione è in `c1cc46606`, che `C` è quello SHA (o HEAD), e togliere o sostituire la riga *Commit*.

**2. Blocker — `T0.A.3`: il file di confronto non esiste e il confronto non è definito** (r.43, 77)
`benchmarks/project-model/results/daodan_stack_fork_develop_68b784e.json` è assente su disco e in ogni ref (`git log --all` vuoto); lo produce solo `modal.yml` `run=baseline` (r.87-88 del workflow), che il piano vieta di rilanciare («senza rilanciare `baseline`»). Mancano inoltre: quale file scrive `run=corpus`, con quale strumento o comando si confronta, cosa conta come «perdita» e «spiegata», da dove si legge la mediana. `benchmarks/project-model/test_fork_stack.py` dichiara di non avviare nulla di reale e non confronta con quel file (usa `results/daodan_stack_fork.json`). Rimedio: o prevedere `run=baseline`, o nominare il file esistente e il comando di confronto con il criterio.

**3. Blocker — «sonda su container reale su Modal» non è eseguibile con il comando prescritto** (r.62, 66, 82, 169, 183)
- `tests/modal_pytest.py` non installa né nomina un motore di container e non imposta `DAODAN_CONTAINER_SMOKE`; in `tests/test_codebase_map_container.py` i test con motore reale sono saltati senza quella variabile (r.1216, 1242). `python tests/modal_pytest.py tests/test_codebase_map_container.py -q` diventa verde sui salti.
- `container.leaves` (r.1355) prova lo scollegamento dalla rete e `container.reached` (r.1408) le porte di un servizio: nessuna delle due è una sonda di uscita. Nessun test le chiama oggi (solo `container.py:1474` e `:1744`).
- «Estendere `leaves` e `reached` ... senza modificare `container.py`» si contraddice: sono funzioni di `container.py`.
Rimedio: dire dove gira un motore vero (Modal lo consente? con quale immagine o sandbox), nome dei nuovi test, cosa asserisce ciascuno dei quattro casi (redirect, DNS, IP letterale, IP interno), e se la sonda è codice nuovo nei test o in `container.py`. Vale anche per `T3.A` e Cancello T3.

**4. Major — «albero pulito» e lancio delle corse non sono operativi** (Regole 3-4, r.32-33, 76)
`modal_pytest.py` monta l'albero su disco (`daodan`, `plugins`, `tests`, `benchmarks`, `docs`), quindi anche i file non tracciati: oggi ci sono `benchmarks/next-server-actions/results/*.json` e `benchmarks/project-model/tmp_dynstep2_rustdocs.py`. Non è scritto se «pulito» li comprende. Manca il comando esatto per `modal.yml` (`gh workflow run modal.yml -f run=suite --ref <ramo>`), il ramo e il push preventivo dello SHA.

**5. Major — «due corse coerenti» è incompatibile con il test instabile, e la scelta resta aperta** (r.34, 51, 76)
`run=suite` gira con `--shards 32 -q -n 2`, la configurazione in cui il test Playwright fallisce 2 volte su 10: due corse daranno spesso insiemi di falliti diversi, quindi non «coerenti» per la Regola 5. La riga 51 lascia un «o» («quarantena ... o corsa senza `-n 2`»): la seconda opzione cambia `modal.yml`, che non è in nessun elenco *File*. Manca anche cosa fare se le due corse divergono (quante ripetizioni) e la tolleranza sui conteggi 3.919-3.920, che `T0.A.1` sposta aggiungendo test.

**6. Major — Cancello T0 e `T0.B.4` si contraddicono** (r.69 contro 42, 76, 85)
Il cancello chiede due corse `suite` «sullo SHA finale di `T0`»; `T0.A.2` le fa sullo SHA post-`T0.A.1` e `T0.B.4` le ripete solo «se `T0.B.2a` ha aggiunto test». `T0.B.1`, `T0.B.3` e `T0.B.4` cambiano comunque lo SHA. Decidere: corse finali sempre, oppure cancello sullo SHA dell'ultimo commit che tocca codice o test.

**7. Major — `T0.B.2b` poggia su file ignorati da git e non ha uno schema** (r.67, 83)
`benchmarks/system-map/results/system/` è in `.gitignore:11`: `collaudo-cieco-haiku/` esiste solo su questa macchina, una sessione nuova o Modal non lo vede e le «citazioni dei file risultati» non sono verificabili dal diff (contro la regola «una prova resta nel repository»). Mancano le categorie della classificazione («step responsabile»: su 6 o 8 step?), il formato della tabella e la sezione del README dove va.

**8. Major — `T0.B.1`, `T0.B.3`, `T0.B.4` lasciano decisioni di progetto all'esecutore** (r.60, 65, 81, 84-85)
- `T0.B.4`: campione, domande per callback, overload e dispatch, quota nascosta e protocollo cieco sono tutti da inventare nel passo; nessuna opzione chiusa. Il piano parla di «sei casi», il README ne tabella cinque (`phazly`, `hostay`, `qamille-enterprise`, `qamille`, `poc-data-extraction`) e dice «cinque casi» (r.72, 112, 592): nominarli. Il passo unisce in un commit campione, cancello, espansione di `T1.A` e la sua revisione di prontezza.
- `T0.B.1`: l'opzione `B2`(b) «ridurre `T1` al solo riordino essenziale» riscrive il piano ma non ha un passo; la scelta «regola `.ts`», richiesta dalla mappa prima di `T1.A` (r.17), non è chiusa da nessun passo di `T0`.
- `T0.B.3`: per `README.md` e `docs/plugins/codebase-map.md` manca cosa scrivere (quali 6 step, quali 8, quale formulazione). Il comando `daodan/core/support_table.py build` è senza interprete e va eseguito sull'host: dire se è ammesso dalla regola «niente sull'host» (legge solo file del repository) o se si rigenera altrove.

**9. Major — `T1`–`T3` non sono valutabili né eseguibili** (r.89-183)
Voluto dalla Regola 1, ma va detto: nessun elenco di file per passo, nessun caso di test, circa 16 scelte aperte, di cui alcune ribaltano l'ambito (`B1`: tre sorgenti con verdetto «no» nei benchmark eppure nel Cancello T1; `M4`; `M3`). I punti 10, 14 e 17 di `T1` e 2-4 di `T2` sono elenchi di titoli. La revisione di prontezza prevista in `T0.B.4` deve essere bloccante per ogni tranche, non solo per `T1.A`.

**10. Nit — riferimenti di riga spostati** (r.48-49)
`apply_marks` è ora a `registry_build.py:235` (`_is_tile` a 209), non `206-235`; `"cncf": "Avro"` è a `registry-additions.json:452`, non 450. `docs/verification/2026-11-25-baseline-t0.md` non esiste: scrivere «crea» nel primo passo che lo tocca (`T0.A.2`). Confermati invece: righe 867, 1113, 1355, 1408, 1413, 1557 di `container.py`, `modal_pytest.py:18` e `:27-28`, le quattro opzioni di `modal.yml`, `support_table.py build --out`, `language-rules.toml:20-25`.

Prossimo passo: correggere i punti 1 e 2 (stato di `T0.A.1` e file di confronto di `T0.A.3`), perché bloccano i primi due passi aperti.

## Testo integrale: Riscontro sul codice (`C`)

Riscontro sul codice di spec e piano: 2 Blocker, 6 Major, 2 gruppi di Nit. Sola lettura, nessuna esecuzione.

**1. Blocker — `refactoring.md:43` e `:77` (T0.2, T0.A.3): il file «già salvato» non esiste.**
`benchmarks/project-model/results/daodan_stack_fork_develop_68b784e.json` non è nell'albero né nella storia di git (`git log --all -- <path>` vuoto). Lo scrive solo `run=baseline` (`.github/workflows/modal.yml:79-88`), che il piano dice di non rilanciare. `benchmarks/project-model/test_fork_stack.py:155` confronta con `results/daodan_stack_fork.json`, e `benchmarks/project-model/README.md:511` dice del riferimento `68b784e` «non è stato rimisurato». Il passo non è eseguibile come scritto.

**2. Blocker — `refactoring.md:82`, `:24`, `:169`, `:183` (T0.B.2a, T3.A, Cancello T3): la «sonda su container reale» non può girare con il comando indicato.**
L'immagine di `tests/modal_pytest.py:95-116` (debian_slim: git, JDK, Node, Chromium) non installa né `docker` né `podman`; nel file non c'è nessuna menzione di un motore. Un Docker su Modal esiste solo in `benchmarks/project-model/modal_engine.py` (VM Sandbox, `benchmarks/project-model/README.md:593`), che il piano non cita. Limite della prova: letto, non eseguito.

**3. Major — `refactoring.md:75` e `:5` (T0.A.1): stato falso.**
Dice «codice e test già scritti nel working tree, in attesa di commit». L'albero è pulito su quei file: sono già nel commit `c1cc46606` («wip(registry): la rigenerazione tiene le tessere», 4 file), con messaggio diverso da quello prescritto. Chi esegue non sa se fare un nuovo commit (non c'è nulla da committare) né quale SHA è il candidato `C` della Regola 4.

**4. Major — `refactoring.md:82` (T0.B.2a) si contraddice.**
Chiede di estendere `container.leaves` e `container.reached` «senza modificare `container.py`», ma le due funzioni sono definite lì (`daodan/core/container.py:1355`, `:1408`). Il campo «File» elenca solo `tests/test_codebase_map_container.py`.

**5. Major — spec e piano divergono sul comando dell'utente.**
`architettura.md:75`: fonte «L'utente» in stato «Proposta (da confermare prima di `T3.B`)». `refactoring.md:171` (T3.2) la mette come lavoro, e le «Scelte aperte» di T3 (`:177-181`) non la elencano.

**6. Major — «L'interfaccia segue la pipeline» non ha tranche.**
`architettura.md:112-114` è contratto di arrivo (otto step, parole interne fuori dalla UI). `refactoring.md:91` e `:122` lo mettono fuori da T1 e in `backlog.md:27`; nessuna tranche T0–T3 lo consegna. Oggi `viewer/app/run.ts` e `viewer/app/stages.ts` esistono ancora.

**7. Major — scelte lasciate a chi esegue (regola zero-decisioni).**
- `refactoring.md:51`: «quarantena esplicita (o corsa senza `-n 2`)». `-n 2` è fisso in `modal.yml:63`, che non è tra i file da toccare.
- `refactoring.md:59` e `:84` (T0.B.3): parla di «6 step oggi nel codice» ma `README.md:18-25` descrive sette step con `plan` come step (`scan, recognize, plan, parse, resolve, observe, connect`); non dice che cosa scrivere. Manca `python` davanti a `daodan/core/support_table.py build`.
- `refactoring.md:119` (T1.15): «rimuovere lo step `parse`» senza la corrispondenza fra i sei `STEPS` (`daodan/core/pipeline/__init__.py:277`) e gli otto id; oggi `Parse` (`:69-83`) dice solo il piano e la spec ha `read_code` come step 2.

**8. Major, una volta sola — elenchi «File:» senza Create/Modify/Delete.**
Esempio: `docs/verification/2026-11-25-baseline-t0.md` (`refactoring.md:76-78`) oggi non esiste in `docs/verification/`, e nulla lo marca da creare.

**9. Nit — riferimenti imprecisi.**
- `refactoring.md:48`: `registry_build.py:206-235` oggi è la correzione (`_is_tile` a 209); `apply_marks` inizia a 235.
- `refactoring.md:49`: `"cncf": "Avro"` è a `registry-additions.json:452`, non 450.
- `refactoring.md:94`: la regola `.h` sta a `languages/__init__.py:135-140`; il commento a `:130-131` dice che diventa una classe di `detect/rules/`, il piano dice «collegare `header.py`».
- `refactoring.md:106`: «Nx non ha adattatore in `premap/`», ma `module_graph.py:80` tratta già `nx-project` (`project.json`).
- `refactoring.md:21`: `tests/test_codebase_map_edge*.py` prende solo `test_codebase_map_edge_view.py`; `test_codebase_map_resolve_edges.py` resta fuori.
- `architettura.md:19`: id senza numero, ma `pipeline_tree.py:314-321` usa `1_list_files` … `8_assemble_graph`.

**10. Nit — regole di esecuzione.**
- `refactoring.md:32`: «nessun workflow esegue `pytest` al push», ma `release.yml:107` lo esegue al push su `main` (`tests/test_daodan_package.py`); `desktop.yml:8` parte a ogni push su `daodan/**`.
- `refactoring.md:33`: `modal_pytest.py:125` carica le cartelle locali, non un commit: `git status` oggi mostra molti file non tracciati (anche in `benchmarks/`), quindi «albero pulito» va definito (solo file tracciati?).
- `refactoring.md:67`, `:83` (T0.B.2b): i risultati `benchmarks/system-map/results/system/` sono ignorati da git (`.gitignore:11`) e non salgono su Modal (`modal_pytest.py:119`): il passo è verificabile solo su questa macchina.

**Regge sul codice:** 35 `SOURCES`, `FRAMEWORK_SOURCES` senza Django/FastAPI/Flask, `EXECUTES` con `mix-project`, 27 test `premap*`, `STEPS` a sei, `READERS` e `support`, `NODE_TYPES` (`flows.py:109`, `system_map.py:38`), righe 867/1113/1413/1557 e assenza di `--cap-drop`/`--user`, le quattro righe `npm install`, `join_sampled` (`dynamic/__init__.py:248`), `technologies.py:341-352`, `modal_pytest.py:18` e `:27-28`, i quattro `run` di `modal.yml`, i commit `78e070129`, `614c940`, `66e09dbca`, `2d6a2881d`, le anagrafiche di `daodan/data/` (con `build-tools.json` assente, come dichiarato).
**Non verificato:** le righe citate in `plugins/senior-review/…` e `daodan/review/reviewer-common.md:32-34` (solo esistenza dei file), i numeri 768 tessere, 112 divergenze, 360/673 dipendenze, il contenuto dei tre README di benchmark Django/FastAPI/Flask.

Passo successivo: correggere `refactoring.md:43` e `:77` decidendo se rilanciare `run=baseline` o confrontare con `results/daodan_stack_fork.json`.
