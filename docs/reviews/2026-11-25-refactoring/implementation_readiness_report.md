# Fase 5 di 5 (stage 9 del protocollo): prontezza del piano

**Documento:** `docs/plans/refactoring.md`, intero, com'era sul disco (non in un commit, con le tranche scritte fuori da questa sessione); contesto `architettura.md` e `backlog.md`.
**Revisori:** tre agenti nuovi `general-purpose`, `fable`, effort `medium`, in invio diretto, tutti completati. Sola lettura e divieto di aprire `docs/reviews/` sono istruzioni, non limiti degli strumenti. Giro 1 del ciclo.

| Revisore | Id | Bloccanti | Importanti | Minori |
| --- | --- | --- | --- | --- |
| Prontezza | `R-` | 3 | 9 | 5 |
| Riscontro sul codice | `C-` | 1 | 8 | 7 |
| Stile | `P-` | 2 | 6 | 9 |

Gli id aggiungono al prefisso l'etichetta del revisore (`C-B1`, `R-M4`). **Esito:** il piano non è pronto per l'implementazione.

## Controlli del coordinatore

- `C-B1` **confermato, e più ampio del rilievo**. Oltre a `container.REGISTRIES` il proxy della preparazione apre: gli host fissi per strumento in `TOOLS` (scelti da Daodan); i registri, indici e repository che il progetto dichiara (`preparation.declared`), per indicizzatori ed esecuzione osservata; gli host delle dipendenze Python prese da Git; al secondo tentativo del modello di Gradle, gli host letti dall'output del primo, dove scrive anche il codice della build (`gradle_model.gradle:5`). È un comportamento voluto («come una CI», `git show 614c940:docs/specs/2026-11-12-passo-dinamico.md`, preparazione, `[costruito]`) che contraddice la regola di rete `[deciso]` del 25 novembre. Il proxy controlla nome e porta 443, non l'indirizzo risolto. Gli indicizzatori e l'esecuzione osservata hanno nella copia i `.env` tracciati con i valori; la pre-mappa solo i nomi. Letto nel codice, mai eseguito; non verificato se il motore di container blocca indirizzi privati. **La frase «proxy ai soli registri» in `architettura.md` è del coordinatore, è pubblicata ed è falsa.**
- Confermati anche: il flake Playwright in `tests/modal_pytest.py:27`, 27 file `test_codebase_map_premap*.py`, `apply_marks` che cancella i file non nominati, `JavaEngine`/`KotlinEngine` assenti da `daodan/`.
- Gli altri rilievi non sono controllati.

## Testo integrale: Prontezza (`R`)

Prontezza all'implementazione di docs/plans/refactoring.md, parte 1 di 2: esito NON PRONTO, 3 Blocker, 9 Major, 5 Nit (Modalità REVIEW).

Perimetro: lo standard si può applicare solo a T0.A–T0.C, le sole tranche espanse in step. Verifiche fatte in sola lettura sul repository; nessun test, build o lint eseguito.

## Blocker

**B1. Step T0.B.3 (r.73, con r.45): non eseguibile senza decidere.**
- I difetti non sono descritti in nessun file del repository. «Avro duplicato», `technologies.state`, `replace => ../local` di Go e repo `path` di Composer sono solo nomi: nessuna causa, nessun file, nessuna riproduzione. `docs/verification/2026-11-16-registro-difetti.md` non li contiene (cercati). L'unica descrizione in più è nella spec rimossa (`git show 66e09dbca~1:docs/specs/2026-11-25-refactoring-completo.md`, r.205: «`technologies.state` che non scrive più la pre-mappa») che rimanda a un'altra spec rimossa («spec stack dal fork, Aperti noti»).
- «risolvere oppure isolare» lascia all'implementatore, per ognuno dei 5 difetti, la scelta fra correzione e quarantena.
- Elenco file non adatto a una allowlist: «`daodan/core/registry_build.py` (o script/test pertinenti)» più il glob `tests/test_codebase_map_*.py`. I due difetti «letti come esterni dal fork» stanno nel fork `stack-analyser`: il piano non dice se la correzione va nel fork (altro repository, rilascio) o in Daodan.
- `apply_marks` (`daodan/core/registry_build.py:206-235`): il codice riscrive `data/marks/<id>.svg` per ogni voce con icona Simple Icons (r.223) e cancella ogni file non in `keep` (r.232-234). Il piano dice «impedire che sovrascriva tessere esistenti o rimuova `doctrinephp`» ma non dice come: non sovrascrivere mai un file presente? un elenco di tessere protette? un campo nel registro? Sono tre comportamenti diversi; la funzione è chiamata da `build` (r.385) e `set_marks` (r.474).
- Nessun caso di test nominato. La sede della tabella di quarantena non è indicata (la regola 5, r.35, la richiede ma non dice dove sta).
- Indicazione: per ogni difetto una riga con file, sintomo, riproduzione, decisione presa (fix o quarantena), file da toccare e nome del test; per `apply_marks` la regola esatta e il test (tessera esistente non riscritta, `doctrinephp.svg` non cancellato).

**B2. Il test instabile è indicato solo come file, e l'evidenza nel repository indica un altro file (r.45, r.73).**
- `tests/test_codebase_map_app.py` ha 58 test; il piano non nomina quale è instabile.
- L'unico flake documentato nel repository è `test_playwright_keeps_control_event_and_state_after_the_page_closes` (`tests/modal_pytest.py:27-28`: fallito in 2 corse su 10 con `-n 2`), che sta in `tests/test_codebase_map_playwright_controls.py`, non in `test_codebase_map_app.py`.
- Conseguenza: T0.B.1 gira proprio con `--shards 32 -q -n 2` (la configurazione in cui quel test fallisce), quindi due run «coerenti» (r.60) possono divergere per un flake che la quarantena non elenca.
- Indicazione: nominare il test esatto, dire se è lo stesso del flake Playwright, e fissare la configurazione della run di baseline.

**B3. Step T0.C.2 (r.78, con r.51-52): tutto il contenuto è una decisione di progetto non presa.**
- «1 stack + 1 progetto reale»: nessuno dei due è nominato. `benchmarks/system-map/README.md` ha più riferimenti ma il piano non ne sceglie uno.
- «domande verificate» con callback, overload e dispatch dinamico: nessun numero, nessun formato, nessun oracolo, nessuno che le verifica.
- «quota nascosta contro overfitting»: compare solo nello step, non nel punto 6; dimensione, custodia e chi la vede non sono scritti.
- «protocollo del confronto cieco»: non definito (modello, ripetizioni, soglia). Le soglie di `system-map` sono scelte aperte di T3 (r.183), ma il Cancello T1 e T2 misurano «sul campione fissato in T0».
- Il titolo dice «criterio rete (`T0.7`)» ma il corpo dello step non contiene alcuna azione sul criterio di rete.
- File: «`benchmarks/system-map/README.md` (o doc protocollo)». Verifica: «controllo completezza domande/oracolo e invarianza regole container», senza criterio.
- Indicazione: nominare stack e progetto con commit, numero di domande per categoria, file dell'oracolo, quota nascosta e sua sede, e il protocollo (o farne uno step di decisione del proprietario come T0.A.3).

## Major

**M1. Contraddizione interna sul criterio di rete (r.52, r.53, r.57, r.74).**
- Il punto 7 è `[deciso]`: «Se T0 scarica dipendenze, eseguire questo test già in T0».
- L'accertato di r.53 dice che la rete è già usata oggi (`network` `registries`, `premap.EXECUTES`), e la suite di T0.B.1 contiene test che clonano e fanno la pre-mappa di progetti veri (`tests/modal_pytest.py:29-30`). La condizione è quindi già vera.
- Eppure r.57 tiene la stessa cosa come scelta aperta (M1/I1) e T0.B.4 è condizionato. L'implementatore non sa quale delle due righe vale.

**M2. Step T0.B.4 (r.74): la sonda non è specificata e cambia il comportamento dentro la baseline.**
- `daodan/core/container.py` ha quattro punti con `--security-opt no-new-privileges` (r.867, 1113, 1413, 1557): il piano non dice in quali entra `--cap-drop ALL` e `--user`, né quale uid/gid, né che cosa succede ai volumi scrivibili e a `mise` con un utente non root.
- «test su redirect, DNS, IP letterali»: i test di oggi controllano gli argomenti passati al motore, non un container vero (accertato a r.174). Il piano non dice se il test nuovo avvia un container vero su Modal, con quale motore, né i casi (quale host, quale redirect, quale IP).
- Aggiungere `--cap-drop`/`--user` dopo la doppia run di T0.B.1 modifica il prodotto misurato: la baseline non vale più per lo SHA finale.
- «e/o» unisce due lavori indipendenti (sonda, diagnosi `0/19`) in uno step; la diagnosi «per step responsabile» non ha un formato né dice se usa una run nuova (costo LLM) o i dati esistenti.

**M3. Ordine di T0.B e definizione di «coerenti» (r.60, r.71, r.79).**
- T0.B.1 misura prima dei fix di T0.B.3 e dell'eventuale T0.B.4. T0.C.3 chiede una sola run finale «coerente rispetto alla quarantena»; il Cancello T0 chiede «due run coerenti». Non è scritto se le due run si rifanno sullo SHA finale.
- «coerenti» non ha definizione: stessi conteggi passati/saltati/falliti? stesso elenco di test falliti? Il riferimento misurato esiste (`tests/modal_pytest.py:18`: 3919-3920 passati, 75 saltati, 1202 subtest) ma il piano non lo cita.
- Sede del verbale: «`docs/verification/` o sezione baseline di `refactoring.md`» è una scelta lasciata aperta.

Prontezza all'implementazione di docs/plans/refactoring.md, parte 2 di 2: restanti Major, Nit e primo intervento.

## Major (seguito)

**M4. Regola SHA (r.34) contro gli strumenti reali.**
- `tests/modal_pytest.py` gira «over the working tree … the checkout as it is on disk» (docstring, r.1-7): la verifica del singolo step non è legata a un commit `C` se l'albero è sporco (oggi lo è: 6 file modificati). La regola 4 non chiede un albero pulito né di registrare `git rev-parse HEAD`.
- `modal.yml` con `run=corpus` o `baseline` fa un commit sul ramo (`contents: write`, r.40 e r.90-102, messaggio `bench(stack): i risultati di … su Modal (run …)`), con `pull --rebase` e push. Dopo la run lo SHA del ramo non è più `C`, e i file di `benchmarks/project-model/results/*` che T0.B.2 (r.72) elenca come propri li scrive il bot: il commit dello step `bench(stack): verifica proof e corpus Modal per T0.2` resta senza contenuto definito.
- `modal_pytest.py` si lancia da questa macchina: il piano dice «su autorizzazione» (r.33) ma nessuno step dice chi la chiede e quando.

**M5. Step T0.B.2 (r.72, con r.44): criteri senza soglia e confronto senza strumento.**
- «tempi registrati», «tempo scansione veloce» (r.44): nessun valore.
- «zero perdite non spiegate sul corpus»: non è detto con quale script si confronta `corpus` con `baseline` (in `benchmarks/project-model/` ci sono `score.py`, `test_fork_stack.py`, `test_stack.py`), né che cosa conta come spiegazione.
- `baseline` è una modalità di `modal.yml` fissata a `develop 68b784e` (r.33 del workflow): il piano non dice se va rilanciata o se si usa `results/daodan_stack_fork_develop_68b784e.json` già presente.
- «nota verifica `T0.2`»: file non indicato.

**M6. Step T0.A.1 e T0.A.2 (r.66-67): destinazione e criterio di accettazione mancanti.**
- «documentare sotto `T0`»: nessun titolo di sezione, nessuna struttura del dossier, nessun numero minimo di evidenze.
- T0.A.1 finisce con «oppure registrare dove il beneficio è solo strutturale»: l'esito è lasciato a chi scrive.
- T0.A.2: «eventuale run diagnostica remota solo se richiesta a parte» non dice chi decide.
- La Verifica («controllo statico citazioni») non dice quando il dossier è sufficiente per T0.A.3.

**M7. Step T0.A.3 (r.68): dipende da un atto esterno senza forma.**
- Non è scritto come si raccolgono le tre decisioni del proprietario, né le opzioni chiuse fra cui sceglie (per B2 non ce n'è nemmeno una: r.56 è una domanda aperta).
- «ed eventuale `docs/specs/architettura.md` se `B2` aggiorna l'introduzione»: file condizionale, contenuto non scritto.
- Se B2 conclude che il beneficio è solo strutturale, il piano non dice che cosa succede a T1–T3.

**M8. Step T0.C.1 (r.77, con r.50): comando non eseguibile come scritto.**
- `support_table.py build` esiste (`daodan/core/support_table.py:448`, con `--out`), ma «in container/Modal» non ha un modo scritto: `modal.yml` non ha una modalità che lo lancia, e non è detto come il file generato torna nel repository. Va anche detto se `build` è codice di Daodan che può girare sull'host (non esegue codice del progetto analizzato) o no.
- «aggiornare i rimandi a 8 step» in `README.md` e `docs/plugins/codebase-map.md`: righe o sezioni non indicate, e il testo dipende da B2. Oggi il codice ha sei step (r.120) e `README.md` sette nomi: scrivere «otto» in T0 descrive un prodotto che non esiste ancora.
- Verifica «test di coerenza `support_table`»: il file è `tests/test_codebase_map_support_table.py`, non nominato.

**M9. Numerazione dei punti di T1 incoerente fra mappa, struttura e sezioni (r.18-21, r.88-91, r.108, r.112, r.119).**
- Mappa: T1.C = `T1.6–T1.10`; struttura: T1.C = punti `6–8, 10`. Il punto 9 è assegnato sia a T1.A sia (dalla mappa) a T1.C.
- T1.A è «a comportamento invariato», ma contiene il punto 9 (`recognize_stack` gira per primo, nessuna sorgente decide da sé), il punto 11 (spostare sorgenti e `binder.bind`) e il punto 15 (rimuovere lo step `parse`, rinominare eventi, giornale e cartelle): sono cambi di comportamento e di formato su disco.
- T1.A viene prima di T1.B–T1.D ma il punto 9 dipende da `build-tools.json` (punto 8, T1.C), che non esiste (`daodan/data/build-tools.json` assente, come atteso).
- Per il dettaglio progressivo non serve espandere T1 ora, ma i confini delle tranche devono essere univoci prima di T0.C.3, che deve «dettagliare i micro-step» di T1.A senza altra fonte.

## Nit

- **N1 (r.89).** `modal_lang.py` citato senza percorso: sta in `benchmarks/project-model/modal_lang.py`.
- **N2 (r.49).** «25 test `tests/test_codebase_map_premap*.py`»: i file sono 27.
- **N3 (r.9).** Il significato delle sigle `B`, `M`, `I` vive solo in `docs/reviews/`; il piano dovrebbe bastare a sé (una riga per sigla).
- **N4 (r.47-49, r.103, r.127).** Percorsi non relativi alla radice: `review-method/SKILL.md:15-17`, `renovate.py`, `jvm_files.py`, `project_files.py`, `module_graph.py`, `build_units.py` (è `daodan/core/build_units.py`), `benchmarks/stack-build-tools/` («da creare» senza contenuto).
- **N5 (r.15).** La mappa dà `1/4` step con SHA `78e070129` ma la colonna «Verifica CI / Modal» non ha ID o URL di run, che la regola 4 richiede (per uno step solo documentale va detto che non c'è).

## Rilievo strutturale (non conteggiato)

T1–T3 (r.83-186) non superano lo standard per costruzione: 16 scelte aperte, nessun file elencato per step, nessun caso di test. Il piano lo dichiara (regola 1, r.31), quindi non è un difetto finché ogni tranche viene riesaminata all'apertura. Va però scritto nella regola 1 che l'espansione di una tranche passa da una revisione di prontezza prima del primo commit.

## Non verificato

- Contenuto di `docs/reviews/` (escluso per vincolo): non so se lì i difetti di B1 sono descritti.
- Il fork `stack-analyser` (altro repository).
- Nessuna run su Modal o CI consultata.

Primo intervento consigliato: riscrivere T0.B.3 come tabella di una riga per difetto (file, sintomo, riproduzione, decisione, file toccati, test), perché sblocca anche la quarantena della regola 5 e il Cancello T0.

## Testo integrale: Riscontro sul codice (`C`)

Rapporto codebase-details su docs/plans/refactoring.md, parte 1/2: 1 Blocker, 8 Major (Nit e fatti confermati nella parte 2).
Metodo: sola lettura e ricerca sul repository; nulla eseguito. Righe = righe del piano.

## Blocker

B1. Righe 52, 53, 174 (T0.7, T3.1) — «solo proxy verso `container.REGISTRIES`» contraddice il codice.
- Il proxy della preparazione apre anche host fuori da `REGISTRIES`: `daodan/core/premap/container_runner.py:5-6` («and the hosts a tool names in `TOOLS`»), `:148` (host di Gradle da `preparation.RESTORES["gradle"]["hosts"]`), `:153` (`repo.scala-sbt.org`, `scala.jfrog.io`), `:159` (Bazel: `bcr.bazel.build`, `github.com`, `objects.githubusercontent.com`).
- `container_runner.py:13-15`: su fallimento un comando riparte con gli host che il progetto stesso dichiara per la sua build (`retry`, lacuna `declared_hosts_failed`). Sono host scelti dal progetto analizzato.
- Effetto: il criterio di rete [deciso] («solo registri autorizzati») e il dossier T0.A.2 della tranche APERTA partono da un fatto falso; `github.com` aperto è già un'uscita verso contenuto arbitrario. Il piano deve dire quali host oltre `REGISTRIES` restano ammessi e se il `retry` sugli host dichiarati sopravvive.

## Major

M1. Riga 153 (T2.3) — `JavaEngine` e `KotlinEngine` non esistono.
- Ricerca in tutto il repository (`.py`, `.kt`, `.java`, `.md`, `.json`, esclusi `docs/reviews` e `.claude`): solo il piano e `benchmarks/call-provenance/README.md:51` (nomi di test, non classi). Esiste solo `daodan/core/engines/KotlinResolver.kt`.
- I motori sono `EngineSpec` costruiti da `indexers.analyzers()` (`daodan/core/engine_pass.py:866-871`). Il passo «rimozione JavaEngine/KotlinEngine» non ha un bersaglio.

M2. Righe 45, 71, 73 (T0.3, T0.B.1, T0.B.3) — il test instabile nominato non è quello misurato.
- `tests/modal_pytest.py:27-28`: il flake documentato è `test_playwright_keeps_control_event_and_state_after_the_page_closes` (`tests/test_codebase_map_playwright_controls.py`), fallito in 2 corse su 10 con `-n 2`, mai senza.
- T0.B.1 usa proprio `--shards 32 -q -n 2` due volte e chiede corse coerenti: il flake noto cade nel cancello e non è in quarantena.
- Per `test_codebase_map_app.py` il piano non dà nome del test né causa (li chiede la sua regola 5, riga 35); in `docs/verification/2026-11-16-registro-difetti.md` il file compare solo come verifica di difetti chiusi (`:4569`, `:4585`, `:4598`, `:4628`). Instabilità non verificata.

M3. Righe 33, 34, 72 (regole 3 e 4, T0.B.2) — effetti di `modal.yml` non descritti.
- `run=corpus` e `run=baseline` fanno commit e push di `benchmarks/project-model/results` sul ramo della corsa (`.github/workflows/modal.yml:90-102`, `contents: write`). La regola SHA (candidato `C` verificato, poi commit `D`) non prevede un commit del bot fra i due: lo SHA di `develop` cambia durante il cancello.
- `baseline` è una quarta opzione (`modal.yml:11`), fissata a `68b784e` (`:33`); la regola 3 elenca solo `suite|proof|corpus`, e T0.B.2 dice «confrontato con baseline» senza dire se la corsa va rilanciata o se si usa `results/daodan_stack_fork_develop_68b784e.json`.
- `modal.yml` parte solo a mano (`workflow_dispatch`); il push lo avvia solo su `stack-dal-fork`. Nessun workflow esegue `pytest` (`viewer.yml`, `desktop.yml`: nessuna riga). «`develop` verde» fra un cancello e l'altro non è controllato da nulla.

M4. Riga 67 (T0.A.2, tranche APERTA) — l'elenco dei punti di rete prima di T3 è incompleto.
- Il piano ne nomina tre (`container_runner.py`, `premap/bazel.py`, `premap.EXECUTES`). Nel codice ci sono anche: `TOOLS` con `registries: True` per `daodan-enry`, `daodan-dockerfile`, `tsc`, `next`, `react-router`, `nuxt` (`container_runner.py:69-93`, con `restores` che esegue gli script di lifecycle, `:83-85`); `npm install` in `daodan/core/dynamic/app.py:109`, `dynamic/javascript.py:249`, `indexers/components.py:65`, `indexers/runtime.py:251`; i ripristini di `daodan/core/preparation.py` (`RESTORES`).
- Sonde già presenti e non citate: `container.leaves` (`container.py:1355`) e `container.reached` (`:1408`) avviano container veri sul motore. Vanno nel dossier prima di decidere M1/I1.

M5. Righe 52, 173 (T0.7, T3.1) — «il parser dei lockfile resta controllo preventivo» non ha un riscontro.
- «resta» dice che esiste. In `daodan/core/container.py` nessun rifiuto di `git+`, URL, `file:` o `-e`; `premap/npm_lock.py` è un lettore, `registry_hosts.py` legge host da URL in configurazione e sorgenti, non rifiuta lockfile. Non trovato (ricerca: `git\+|lockfile|ignore-scripts` in `daodan/core/*.py` e `premap/*.py`).
- Il piano deve dire file e funzione, oppure marcarlo da creare in T3.A. Lo stesso per «tabella chiusa comandi» e «neutralizzazioni package manager»: `--ignore-scripts` c'è solo sulle installazioni di Daodan (i quattro punti di M4), mentre `restores` esegue gli script del progetto.

M6. Righe 89, 96 (T1.3) — il «difetto» della regola `.ts` è una decisione già scritta nel codice.
- `daodan/data/language-rules.toml:20-25` (`ts.xml-document`): il `why` dice che togliere la fine di parola dopo `<?xml` è voluto («no TypeScript starts so either»).
- La spec rimossa (riga 221) diceva «Da correggere o accettare»; il piano scrive «fix [difetto]» e nasconde la scelta. «112 divergenze» non è in nessun file del repository: sta solo nella spec in git (112 su 186.124 testi generati).

M7. Righe 94, 97, 89 (T1.1, T1.4) — stato attuale di `.h` e di go-enry omesso o ridotto.
- `.h`: `daodan/core/languages/header.py` esiste già (commit `2d6a2881d`, wip) con `tests/test_codebase_map_header_language.py`; `languages/detect/rules/` contiene solo `sql_rowtype.py`; la regola vecchia è ancora in `languages/__init__.py:125-137`. Il piano non dice che il lavoro è «collegare e spostare», non «scrivere».
- go-enry: «`premap/__init__.py` lo usa per una lacuna» è riduttivo. `enry` è una sorgente di `SOURCES` (`premap/__init__.py:50`), con `premap/enry.py` (file esclusi: vendored, generated, documentation, binary; conteggio per linguaggio; `build_definition`), `enry_facts.go`, lo strumento `daodan-enry` (`container_runner.py:69`), `suffix_table.py` (`premap/__init__.py:254-278`) e `pipeline_tree.py`. La scelta aperta «resta o si toglie» va decisa su questo perimetro.
- Riga 89: `modal_lang.py` è in `benchmarks/project-model/`, non in `benchmarks/header-language/` (lì c'è `modal_headers.py`).

M8. Righe 71, 73, 78 (T0.B, T0.C) — confine dei file non chiuso, da segnalare una volta.
- «verbale in `docs/verification/` o sezione baseline», «`registry_build.py` (o script/test pertinenti)», «`tests/test_codebase_map_*.py`», «`README.md` (o doc protocollo)»: percorsi a scelta di chi esegue. Vale per tranche bloccate, ma T0.B.3 nomina già file di codice.
- T0.B.3, riuso: il registro ha già il modo per tenere una tessera, il record `official` con `mark` («a file kept as it is», `registry_build.py:206-209`) e i comandi `add-mark` e `add-package-mark` (`:424`, `:447`). `doctrinephp` in `daodan/data/registry-additions.json:1860-1870` non ha `mark`, quindi `apply_marks` lo cancella (`:232-234`). `apply_marks` è chiamato anche da `set_marks` (`:474`): il fix deve coprire i due chiamanti.

Rapporto codebase-details su docs/plans/refactoring.md, parte 2/2: 7 Nit, fatti confermati, non verificato.

## Nit

N1. Riga 49 — «25 test `tests/test_codebase_map_premap*.py`»: i file tracciati sono 27 (`git ls-files tests`).
N2. Riga 47 — percorsi non relativi al repository: `review-method/SKILL.md`, `review-preparation/references/team-review.md`, `review-consolidation/references/team-review.md` stanno sotto `plugins/senior-review/skills/`. Le righe citate esistono; «regole 1–4» non è definito nel piano, quindi la corrispondenza riga-regola non è verificabile.
N3. Righe 21, 91, 137 — `Flask.read()` non è un simbolo: è la funzione di modulo `read` in `daodan/core/premap/flask_app.py:264` (la riga 115 lo scrive giusto).
N4. Riga 122 — i nodi di `plan.py` hanno anche `version`, opzionale (`daodan/core/pipeline/plan.py:95-97`).
N5. Riga 114 — i tre «no» sono confermati; mancano due fatti: le patch di collegamento di FastAPI e dello script condiviso con Flask esistono già in `benchmarks/fastapi-routes/wiring/` (`wiring.diff`, `flask-shared-script.diff`), e i moduli `premap/django_app.py`, `fastapi_app.py`, `flask_app.py` (più `*_routes.py`) sono nel codice con i test `test_codebase_map_premap_{django,fastapi,flask}.py`.
N6. Riga 177 — il profiler V8 non è solo «valutato e scartato»: il percorso `sampled` è ancora nel codice (`dynamic/__init__.py:248` `join_sampled`, chiamato a `:737`); `dynamic/javascript.py:13-16` dice che nessuna corsa lo prende. Codice morto da nominare se il backlog lo dà per ritirato.
N7. Riga 77 — «test di coerenza `support_table`» senza nome: è `tests/test_codebase_map_support_table.py`; i sottocomandi sono `build` e `check` (`daodan/core/support_table.py:448-449`).

## Fatti del piano confermati sul codice

- Commit `78e070129`, `614c940`, `66e09dbca` esistono; la spec rimossa si legge con il comando della riga 7. Il ramo `feat/link-key-shape` non c'è, né locale né remoto.
- `snapshot.py`: `WORKING_RUN` (:1314), `query_gate` (:1336), `refresh_working` (:1402), `_refresh_locked` (:1428); hook `PostToolUse` -> `daodan mcp --hook`; `tests/test_codebase_map_working_run.py`.
- `composition.py`: i sette simboli; `tests/test_senior_review_composition.py`; misure dell'8 novembre in `benchmarks/whole-source-coverage/README.md:54-86`.
- `premap.SOURCES` ha 35 voci; `FRAMEWORK_SOURCES` è `(nextjs, react_router, nuxt, sveltekit)`; `EXECUTES` corrisponde all'elenco; `join`, `derive`, `write`, `python_runs`; `WRAPPER_SELF` e `WRITTEN_ELSEWHERE` in `renovate.py:56,59`; `external_packages` e `angular-project` in `module_graph.py`. Mix e Nx senza file proprio in `premap/`.
- `STEPS = (Scan, Stack, Parse, Analyze, Dynamic, Union)` (`pipeline/__init__.py:277`); `plan` e `blocked` in `plan.py`; `approval_required` e `ui_execution_deferred` assenti da `daodan/`; nessun campo `surface` nei due registri.
- `container.py`: `--network none`, rete `--internal`, `no-new-privileges`; nessun `--cap-drop`, nessun `--user`. I due test citati esistono (`tests/test_codebase_map_container.py:517`, `:709`).
- `registry_build.apply_marks` scrive il simbolo pulito e cancella i file non nominati (:206-235); `READERS` (:58) e `support()` (:86) funzionano come dice il punto 12; `django` è `partial` nel registro.
- Funzioni oltre 80 righe: `index_stage` circa 100, `write_reading` 82, `_refresh_locked` 87.
- `engine-answers.sqlite` (in `embedding_worker.py`, `mcp_service.py`, `position_stage.py`), `--engine scip` (`resolve_edges.py:107`), `indexers/typescript_unbound.js`, `edge_grading.py`, `edge_store.py`, `resolve_edges.py`: come descritti.
- `python_record.py` su `sys.monitoring`; registratori ed `explore.cjs` come descritti; `strace` assente da `dynamic/`.
- Syft 1.57.1, 360 contro 673, +1.827 (`benchmarks/project-model/REPORT.md:9,36,84`); `tools/syft.py`, `results/syft.json`.
- `0 su 19` in due ripetizioni: `benchmarks/system-map/README.md:548-554`.
- `modal.yml`: `suite` = `python tests/modal_pytest.py --shards 32 -q -n 2`; `proof` = i due file citati.

## Non verificato

- `replace => ../local` Go, repo `path` Composer, «Avro duplicato», difetti di `technologies.state` (riga 45): richiedono corse o lettura del fork; i simboli `technologies.state` e `technologies.merge` esistono.
- «37 tessere mancanti» (riga 45): il generatore è solo in `.claude/worktrees/own-marks/`, non tracciato, come dice il piano; il conteggio non è stato contato.
- «154 chiamate `self.metodo()`» e «timeout ~6 min» (riga 154): nessuna fonte cercata nel repository.

Prossimo passo: correggere nel piano la frase sul proxy (B1) con l'elenco degli host di `container_runner.py:148-159` e la regola del `retry`.

## Testo integrale: Stile (`P`)

Rapporto di stile su docs/plans/refactoring.md, parte 1 di 2: 2 Blocker e 6 Major (i Nit sono nella parte 2).
Modalità REVIEW, documento letto intero (righe 1-187). Contesto: architettura.md e backlog.md. Nessun file modificato; docs/reviews/ non aperta.

BLOCKER

B-1. Etichetta `[deciso]` su punti che il piano stesso dichiara non decisi. Righe 9, 103, 105, 107, 113, 121, 150 contro 130-133, 158.
- La riga 9 dice che la decisione legata a un rilievo «è nelle Scelte aperte del traguardo, non presa».
- I punti 6 (r. 103), 7 (r. 105), 8 (r. 107), 12 (r. 113), 16 (r. 121) e T2.1 (r. 150) portano `[deciso]`.
- Le scelte aperte B1 (r. 130), M2 (r. 131), M3 (r. 132), M4 (r. 133) e M5 (r. 158) rimettono in discussione proprio quei punti.
- Motivo: il lettore non può sapere se il punto è approvato o sospeso; l'affermazione supera la sua prova. La legenda di architettura.md:5 definisce `[deciso]` come «scelta approvata dal proprietario».
- Azione: CALIBRATE. Restringere l'etichetta alla parte non contestata, oppure sostituirla con una forma come «deciso, riaperto da B1».

B-2. Criteri di cancello senza soglia, e due formulazioni diverse per lo stesso criterio. Righe 35, 44, 60, 72, 79, 137, 160.
- «due run coerenti» (r. 60) e «coerente rispetto alla quarantena» (r. 79): «coerente» non ha misura (stessi conteggi? stessi test falliti?).
- «nessuna perdita sul corpus» (r. 44) contro «zero perdite non spiegate» (r. 72): sono due criteri diversi per lo stesso punto T0.2.
- «zero regressioni» (r. 35), «zero nuove regressioni rispetto a T0» (r. 60, 137), «rispetto a T1» (r. 160): tre forme; la r. 35 dà la definizione operativa (fallimento fuori dall'elenco di quarantena), le altre non la richiamano.
- «tempo scansione veloce» (r. 44): giudizio soggettivo senza valore; la r. 72 dice solo «tempi registrati».
- Motivo: un cancello non misurabile non si può dichiarare chiuso. Azione: CALIBRATE, una sola formulazione per criterio, con soglia o con rimando alla riga che la definisce.

MAJOR

M-1. Titolo «risolte» su voci che restano aperte. Riga 46 contro 47-49.
- La r. 46 dice «Contraddizioni dei vecchi documenti risolte». La r. 47 chiude con «Esito test da confermare su Modal»; la r. 48 riporta «non implementate / non eseguite»; la r. 49 ha «Restano aperti in T1».
- Lo stesso vale per «**implementati nel codice**» in grassetto (r. 47) seguito dalla riserva sui test.
- Azione: CALIBRATE. Il titolo dice ciò che è stato fatto: «accertate sul codice», come già scrive la r. 60.

M-2. Termini ed etichette senza definizione nel documento né nei due documenti di contesto. Righe 13, 31, 43-45, 49, 72, 78, 79, 100, 113, 123.
- `ESCALATE` (r. 13, 31) e `rolling wave` (r. 31): prestiti inglesi non spiegati; «rolling wave» duplica «Dettaglio progressivo» che gli sta accanto.
- `[misura]`, `[difetto]`, `[spike]`: la legenda di architettura.md:5 copre solo `[deciso]`. `[accertato nel codice]` (r. 46) e `[accertato nel repository]` (r. 9 e altrove) sono due forme della stessa etichetta.
- `VERIFICATA` (r. 79): stato di tranche che la mappa non usa (usa `APERTA`, `Bloccata da`).
- «host-guard» (r. 72), «quota nascosta contro overfitting» (r. 78, assente dal punto 6 a r. 51), «Task 12» (r. 49), «prove 2 e 5» (r. 123), «Principio 5» (r. 113, senza dire che è di architettura.md), «gate 180/122» (r. 19, 89).
- Motivo: il lettore nuovo deve aprire una spec rimossa via `git show` (r. 7) per capire rimandi che reggono criteri di cancello.

M-3. Sinonimi per lo stesso concetto (AGENTS.md li vieta). Tutto il documento.
- cancello / gate: r. 17, 19, 67, 89, 97 («gate») contro r. 60, 137, 160, 186 («Cancello»).
- run / corsa / esecuzione: r. 43 («seconda esecuzione»), r. 71 («due corse», «2 run»), r. 60.
- step / punto / micro-step / passo: r. 31, 65-79, 88-91; in più «step» indica anche gli step della pipeline (r. 56, 120), quindi «gli otto step» e «1/4 step» usano la stessa parola per due cose.
- fix / correggere / risolvere: r. 45, 73, 96, 115, 178.
- difetto / flake / test instabile: r. 35, 45.
- lacuna / gap / buco: r. 97, 116, 122.
- `APERTA` / `APERTO` / «APERTA — 1/4»: r. 5, 15, 39, 64.

M-4. Alternative non risolte nei campi operativi. Righe 33, 34, 67, 68, 71, 73, 74, 78.
- Campo *File* con ripiego: «verbale in `docs/verification/` o sezione baseline» (r. 71), «(o script/test pertinenti)» (r. 73), «(o doc protocollo)» (r. 78), «(ed eventuale `architettura.md`…)» (r. 68). Azione: CALIBRATE, un solo percorso.
- «su autorizzazione» (r. 33) e «su richiesta» (r. 34): non dicono di chi. Azione: CALIBRATE, nominare il proprietario.
- «eventuale run diagnostica remota solo se richiesta a parte» (r. 67): riserva senza decisione collegata. Azione: DROP, oppure RELOCATE in T0.A.3 dove la scelta si prende.
- r. 74: tre «e/o» e due esiti («attivo o saltato») in un solo step con una sola casella; il commit «atomico per sonda e/o diagnosi» non dice quanti commit. Azione: CALIBRATE, due step distinti.
- r. 52 «Se T0 scarica dipendenze, eseguire questo test già in T0; altrimenti…»: la r. 53 accerta che la rete è già usata, quindi la condizione è già risolta. Azione: CALIBRATE.

M-5. Ogni tranche è descritta tre volte. Righe 15-27, 88-91, 146-148, 169-171 e i punti numerati.
- Riga della mappa, voce «Struttura in tranche autonome», punti numerati: stesso contenuto con parole diverse.
- Le tre versioni già divergono: T1.A elenca i punti `9, 11, 15, 17` (r. 18, 88), ma il titolo della mappa parla di «estrazione sorgenti» e la r. 88 aggiunge «`step.skipped` unico»; T3.A aggiunge la sonda di rete solo alla r. 169.
- Azione: tenere mappa e punti numerati; la voce «Struttura» riduce a elenco di punti e consegna.

M-6. Frasi sovraccariche che nascondono il dato operativo. Righe 33, 45, 49, 114, 177.
- r. 45: un solo periodo con sei difetti, una parentesi di quattro righe con due punti interni e una data.
- r. 33: divieto, quattro modalità di verifica e due comandi in un periodo, con parentesi annidate.
- r. 49: due elenchi in parentesi e uno dopo i due punti.
- r. 177: sette fatti accertati in un capoverso.
- Azione: un difetto o un fatto per voce di elenco.

Rapporto di stile su docs/plans/refactoring.md, parte 2 di 2: 9 Nit e i passaggi lasciati come sono.

NIT

N-1. Aggettivi di valutazione senza misura. Righe 41, 60, 90, 91, 148, 150, 173.
- «stato reale misurato e ripetibile» (r. 41): «reale» non aggiunge nulla a «misurato».
- «completi e testati» (r. 90), «Cancello T1 completo» (r. 91), «vista statica completa» (r. 148), «gate T0 completo» (r. 17): «completo» non ha criterio.
- «il piccolo *evidence model*» (r. 150): giudizio di dimensione.
- «Test decisivo di rete» (r. 173): «decisivo» è enfasi.

N-2. Coppie ridondanti. Righe 32, 43, 164, 166.
- «autoconsistente che lascia `develop` verde e committabile» (r. 32) e «Consegna committabile» ripetuta a r. 88-91, 146-148, 169-171: «committabile» vale per ogni consegna.
- «Isolamento minimo verificato» (r. 25, 164, 169, 173) e «la parte minima necessaria» (r. 166): «minima necessaria» è una coppia.
- «registrare revisione, comando ed esiti; confermare con una seconda esecuzione» (r. 43) ripetuto a r. 71 con altri termini.

N-3. Inglese dove esiste la parola italiana, nella stessa frase di quella italiana. Righe 22, 66, 72, 73, 96, 100, 146, 150.
- «fix» (verbo e nome), «overfitting», «adapter risolutore», «call events», «overhead», «spike», *evidence model* in corsivo: il documento alterna «correggere» e «fix» a distanza di una riga (r. 96, 115).
- Restano fuori i nomi di codice e di strumento.

N-4. Abbreviazioni telegrafiche nelle celle della mappa. Righe 16, 19, 26, 27.
- «x2», «ev. sonde», «1° linguaggio», «`T1.9`, `11`, `15`, `17`», «`T0.1`–`T0.3`»: la cella «ordine/1° linguaggio» (r. 26) si capisce solo leggendo la r. 182.

N-5. Barre al posto di una congiunzione. Righe 48, 103, 125, 174 e altre.
- «non implementate / non eseguite» (r. 48), «**[deciso] / [misura]**» (r. 103), «prima/durante T1» (r. 125), «sottocartella/archivio» (r. 171, 178): la barra non dice se è «e» oppure «o». Alla r. 103 lascia in dubbio quale parte del punto è decisa.

N-6. Grassetto usato per tre funzioni. Righe 3, 5, 47-49, 51, 60.
- Segna stato («**APERTA**»), esito («**implementati nel codice**»), e semplice enfasi («**un solo traguardo alla volta**», «**zero nuove regressioni**», «**Syft**», «**Django, FastAPI e Flask**»). L'enfasi si può togliere.

N-7. Domande retoriche e frasi nominali nelle scelte aperte. Righe 56, 126-135, 158, 182-184.
- Formati misti: domanda («resta o si toglie?»), frase nominale senza verbo (r. 129, 182, 183), affermazione dentro la domanda (r. 135, 184). Le r. 129, 182 e 183 non dicono quale decisione si chiede.

N-8. Parentesi che portano una regola. Righe 97, 127, 173.
- r. 127: «(ex scelta 1 — qualunque comando che può eseguire codice progetto richiede il container)»: è la regola invalicabile, non un inciso.
- r. 97: «(oggi `premap/__init__.py` lo usa per una lacuna)»: è il fatto che blocca la rimozione.
- Azione: RELOCATE fuori dalla parentesi.

N-9. Frase di intestazione vaga. Righe 7, 85, 143, 166.
- r. 7: «vengono dalla spec unica rimossa, che cita a sua volta i documenti precedenti»: due livelli di rimando in una subordinata; il comando basta.
- «Accorpa le ex ondate 1–4» (r. 85), «Accorpa la ex ondata 5 e la parte statica della ex ondata 8» (r. 143): rimandano a una numerazione che il lettore non ha; sono utili solo come traccia storica.

PASSAGGI LASCIATI COME SONO (riserve con prova, non segnalate)
- r. 45: «letto nel codice, rigenerazione non eseguita».
- r. 47: «Esito test da confermare su Modal (punto 1)» (va bene la riserva; il rilievo M-1 riguarda solo il titolo).
- r. 104, 114, 174, 177, 179: le voci «[accertato nel repository]» citano file, data e valore.
- r. 155: il ramo `feat/link-key-shape` dichiarato assente.

Conteggio: 2 Blocker, 6 Major, 9 Nit.
Prossimo passo: decidere B-1, cioè se `[deciso]` resta sui punti 6, 7, 8, 12, 16 e T2.1 mentre B1, M2, M3, M4 e M5 sono aperte.
