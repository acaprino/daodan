# Fase 1 di 5 (stage 5 del protocollo): visione d'insieme iniziale

Documenti: `docs/specs/architettura.md` e `docs/plans/refactoring.md` al commit `78e070129`; `docs/backlog.md` come contesto.
Revisori: agenti nuovi `general-purpose`, modello `fable`, effort `medium`, in sola lettura. Isolamento ottenuto: nessuna conversazione ereditata; la sola lettura è un'istruzione, non un limite degli strumenti, e le istruzioni di progetto (`CLAUDE.md`, `AGENTS.md`) possono arrivare al revisore.

## Revisore: inventive catalyst (completato)

Quattro compromessi da riesaminare, due Major e due Nit; il primo da decidere è spostare la sonda di rete nel cancello T0. Revisione sui soli documenti, nessuna verifica sul codice.

Lasciati stare perché invarianti del proprietario: esecuzione solo nel container, strumento ufficiale, tree-sitter, niente build locale, prove su Modal.

Già bilanciati nel testo, nessun rilievo: piano «completo nei vincoli, incrementale nelle azioni»; sorgente dedicata primaria con Noir come ripiego dichiarato; evidence model dietro SCIP; confronto con Syft prima di estendere il fork; riconoscitore unico nel fork (padrone unico voluto).

### 1. Il confine di isolamento arriva dopo il codice che deve contenere

1. **Severity:** Major
2. **Affected Scope:** `refactoring.md` T0 punto 7 (riga 29), T3 punto 1 (riga 94), cancello T3 (riga 103); `architettura.md` tabella degli step (righe 24-26) e «Servizi comuni» (riga 108).
3. **False Compromise:** Il piano scambia «un traguardo alla volta» contro la sicurezza.
   - Il test decisivo di rete si collauda «in T3 prima del primo uso con rete» se T0 non scarica dipendenze. `--cap-drop ALL`, utente non root e rifiuto dei lockfile con URL sono anch'essi in T3.
   - Il primo uso con rete però è in T1: `find_modules` lancia gli strumenti di build, `find_entry_points` chiede i «pacchetti ripristinati», e l'introspezione di Django/FastAPI/Flask esegue codice del progetto nel container.
   - T2 aggiunge gli indicizzatori SCIP su «ambiente preparato».
   - Due traguardi interi girano quindi dietro un confine `[deciso]` ma mai provato.
4. **Proposed Resolution:** *Extraction* più *Preliminary Action*. Estrarre da T3.1 la sola sonda (uscita diretta, redirect, DNS, IP letterale, `cap-drop`, non root) e metterla nel cancello T0 come test permanente su Modal. Il resto di T3.1 (tabella chiusa dei comandi, neutralizzazioni dei package manager) resta dov'è. La condizione «se T0 scarica dipendenze» sparisce.
5. **Secondary Liabilities:** T0 si allunga; la sonda va mantenuta a ogni cambio di immagine o di proxy; se fallisce blocca T1 su un lavoro di infrastruttura oggi previsto per ultimo.

### 2. La misura del valore della mappa si diagnostica per ultima

1. **Severity:** Major
2. **Affected Scope:** `refactoring.md` T0 punto 6 (riga 28), T3 punto 4 (riga 97), cancelli T1/T2 (righe 72, 86).
3. **False Compromise:** T0 fissa campione e protocollo del confronto cieco, ma la diagnosi dello `0/19` aspetta T3.4.
   - Il piano tratta come inevitabile che la misura di esito venga dopo tutta la pipeline.
   - I cancelli T1 e T2 verificano la forma: piano unico, soglie SCIP, zero regressioni. Nessuno verifica se la mappa risponde meglio.
   - Se la causa dello `0/19` è statica (ingressi, legami, formato delle risposte), la si scopre dopo tre traguardi costruiti senza saperlo.
4. **Proposed Resolution:** *Preliminary Action*. Portare in T0 la sola diagnosi sulla mappa esistente, senza correzione: classificare i 19 fallimenti per step responsabile. Assegnare ogni classe al traguardo che la chiude. Rieseguire il confronto, già fissato, come misura di tendenza a ogni cancello.
5. **Secondary Liabilities:** una corsa su Modal in più per traguardo; rischio di ottimizzare sul campione fisso (serve tenerne una parte nascosta); una diagnosi fatta sulla pipeline vecchia può invecchiare dopo il riordino.

### 3. Il consenso ferma l'analisi, e gli stati non hanno l'attesa

1. **Severity:** Nit
2. **Affected Scope:** `architettura.md` «Il piano», punti 2 e 4 (righe 82, 84).
3. **False Compromise:** «L'esecuzione si ferma su quell'azione» fa pagare a tutta l'analisi il consenso di una sola azione.
   - Un download di 4 GB per una superficie blocca anche gli step statici che non ne dipendono.
   - L'elenco chiuso degli stati non ha «in attesa di consenso»: l'azione finirebbe in `da fare` o `non possibile`, due significati diversi.
4. **Proposed Resolution:** *Segmentation*. Si ferma solo l'azione e ciò che ne dipende; le altre proseguono. Aggiungere lo stato «in attesa di consenso». A fine corsa, se il consenso manca, l'azione diventa la lacuna `approval_required` già prevista.
5. **Secondary Liabilities:** il piano deve conoscere le dipendenze fra azioni; il risultato parziale va presentato come tale in UI, MCP e CLI; un consenso tardivo chiede una ripresa della corsa.

### 4. «Zero nuove regressioni» poggia su una baseline con un test instabile

1. **Severity:** Nit
2. **Affected Scope:** `refactoring.md` T0 punto 3 e cancello T0 (righe 22, 31).
3. **False Compromise:** Il cancello accetta difetti «riproducibili e classificati» invece che corretti, e chiede «due run coerenti». Con `test_codebase_map_app.py` instabile le due cose si contraddicono: o le run non coincidono, o da T1 in poi un rosso non si distingue da una regressione.
4. **Proposed Resolution:** *Extraction*. Mettere in quarantena esplicita i fallimenti noti: un elenco nel repository con test, causa e riproduzione. Il cancello confronta gli esiti con quell'elenco, e un test che ne esce senza correzione è una regressione.
5. **Secondary Liabilities:** l'elenco tende a crescere e a restare (serve una scadenza per voce); un test in quarantena non protegge più il codice che copre.

## Revisore: zoom out (completato)

Rapporto su `architettura.md` e `refactoring.md`: 2 Blocker, 8 Major, 5 Nit. Sola lettura, niente eseguito.

### Blocker

**B1. Django/FastAPI/Flask «[deciso]» come sorgente primaria contro tre verdetti misurati il giorno prima.**
Ambito: `architettura.md` righe 39 e 44; `refactoring.md` T1 punti 12-13 e Cancello T1; backlog riga 58.
I tre benchmark chiudono con «no»: `benchmarks/flask-routes/README.md:253` («non aggiunge a Noir quanto costa», collegamento tolto il 24 novembre, riga 176); `benchmarks/fastapi-routes/README.md:8` («nessuna rotta con funzione del progetto che Noir non dia», e nelle condizioni di Daodan non carica nessuna delle due app); `benchmarks/django-routes/README.md:216` («Verdetto sul collegamento: no», 0 funzioni su 132 su healthchecks; al più complemento di Noir per chi dichiara DRF). Le condizioni di ribaltamento in `fastapi-routes` riga 70 sono «da cercare, non cercate qui». Il piano rovescia il verdetto senza citare una misura nuova e mette la sorgente dedicata come primaria con Noir a ripiego: l'opposto di ciò che il benchmark di Django raccomanda. Spring è ritirato nel backlog per lo stesso motivo. Costo che ne segue: unione deduplicata su contesto/mount/router, diagnostica dei conflitti, correzione di `Flask.read()`, test di regressione nel cancello. Se la ragione è il Principio 5, il documento deve dirlo e dire quale misura in T1 lo conferma; altrimenti resta Noir e le tre sorgenti vanno nel backlog.

**B2. Manca il problema che il refactoring risolve, e il piano non si legge senza documenti cancellati.**
Ambito: intestazione e Principi di `architettura.md`; `refactoring.md` intero.
Nessuno dei due dice quale difetto di oggi giustifica otto step, il piano unico e lo spostamento delle sorgenti (che cosa non funziona con `Scan, Stack, Parse, Analyze, Dynamic, Union` di `daodan/core/pipeline/__init__.py:277`). Il piano rimanda a testi rimossi: «ex ondata 4 voce 9», «ex scelta 5/12», «prove 2 e 5», «regole 1-4», «Task 12», «spec 8.4», «0/19», «154 chiamate self.metodo()», «37 marchi senza cornice», `technologies.state`. Kiri e Noir non sono mai definiti. Un lettore nuovo non può eseguire T1.17 né giudicare i cancelli senza `git show 614c940`.

### Major

**M1. Isolamento verificato in T3, ma il codice del progetto gira con rete da T1.**
Ambito: `refactoring.md` T0.7, T3.1; `architettura.md` Principio 6 e «Servizi comuni».
Motivo: `find_modules` (T1) esegue Gradle, Maven, CMake, Bazel nel container (`premap.EXECUTES`) e `link_calls` (T2) ripristina dipendenze via proxy. La prova decisiva di rete, `--cap-drop ALL` e utente non root arrivano due traguardi dopo. T0.7 lo lascia a un «se». Inoltre proxy, `--network none` e registri ammessi esistono già (`daodan/core/container.py:17-39, 104, 1254`): T3.1 non distingue ciò che c'è da ciò che manca. La prova di rete va nel cancello T0 o T1.

**M2. Confronto con Syft che non può informare la decisione.**
Ambito: `refactoring.md` T1.6-7.
Motivo: Syft cataloga pacchetti; le dieci famiglie del punto 7 sono strumenti di build (CMake, Bazel, Meson, Make, autotools, sbt, Nx), che Syft non riconosce. Syft non è nel repository, e `benchmarks/stack-build-tools/` non esiste. Un secondo riconoscitore contraddice «Chi riconosce è uno solo».

**M3. Riconoscimento degli strumenti di build spostato nel fork più una nuova anagrafica, senza un caso che lo chieda.**
Ambito: `architettura.md` riga 31; `refactoring.md` T1.7-9.
Motivo: gli adattatori cmake, bazel, meson, make, autotools, sbt, dotnet esistono già in `daodan/core/premap/` e sanno riconoscere il proprio manifesto. Il piano aggiunge dieci famiglie di regole in un repository esterno (rilascio `.6`), `build-tools.json` e un test di coerenza per rimpiazzare quel controllo. Il documento non nomina un errore attuale che questo corregge. Se è deciso, va scritto il costo e il difetto.

**M4. Piano unico: stati, tipi chiusi e arresto per consenso costruiti per consumatori differiti.**
Ambito: `architettura.md` «Il piano» e «L'interfaccia segue la pipeline»; `refactoring.md` T1.16; backlog sezione 3.
Motivo: esiste già un piano come dati (`daodan/core/pipeline/plan.py`: nodi, `needs`, lacune, `blocked`). T1.16 lo vuole «uguale per UI, MCP e CLI», ma l'adeguamento della UI è nel backlog, che è non normativo. I download che chiedono consenso (Android ~4 GB, ISO Windows) sono tutti differiti; `approval_required` non è nel codice. Per T1 basta estendere `plan.py` con le azioni scoperte; sei stati, tre fatti per azione e arresto sul consenso si aggiungono quando arriva il primo caso.

**M5. «Evidence model» nuovo che ricopre strutture esistenti.**
Ambito: `architettura.md` riga 45; `refactoring.md` T2.1.
Motivo: `daodan/core/edge_grading.py:26-32,138` classifica già `ambiguous-target`, `unresolved`, `project-callable`; `edge_store.py` tiene una riga per estremo con `verdict` e `confidence`; `resolve_edges.py:17` registra `<engine>@<version>` come fonte. Il piano non dice che cosa manca a queste. Va scritto come estensione di quelle, non come modello nuovo.

**M6. Menu di backend runtime che riapre un approccio ritirato.**
Ambito: `architettura.md` righe 41 e 46; `refactoring.md` T3.3.
Motivo: `daodan/core/dynamic/python_record.py:1` è già su `sys.monitoring`: per Python il confronto è vuoto. Il backlog ritira il profiler V8 (47,1%, «sostituito dal registro esatto») sotto «non si rifà». OpenTelemetry, `strace` ed eBPF compaiono nel codice solo come menzioni, non come backend. I registratori ci sono per sei linguaggi. Nessuna misura mostra che non bastano.

**M7. T1 e T2 sono troppo larghi per un cancello solo.**
Ambito: `refactoring.md` T1 (17 punti), T2 (5 punti a grappolo).
Motivo: T1 mescola spostamenti che conservano il comportamento (sorgenti fuori da `premap.SOURCES`, rinomina degli step), funzioni nuove (piano unico, tre sorgenti), uno spike SQL e pulizia. «Zero regressioni» non si attribuisce a una causa. La rinomina (T1.15) tocca codice, eventi, giornale e cartelle con lettura dei giornali vecchi: è la seconda in tre giorni (il README porta i sette nomi approvati il 22 novembre). T2 unisce SCIP incrementale, JVM, C/C++, fogli di stile, SQL e `assemble_graph`. Separare «riordino a comportamento uguale» da «funzioni nuove».

**M8. Requisiti del contratto senza un punto nel piano, e riferimenti che non esistono.**
Ambito: `architettura.md` «Superfici attive», tabella anagrafiche; `refactoring.md` T2.5, T0.5, T1.4.
Motivo: il campo `surface` (assente in `service-registry.json`), la lacuna `ui_execution_deferred` e `approval_required` non sono in nessun traguardo. `feat/link-key-shape` (T2.5) non esiste: nessun ramo, nessun commit. T0.5 chiede di «portare `docs/pipeline/` nel repo»: è già tracciata (commit `663a43885`). T1.4 dice di rimuovere `go-enry`, le «scelte aperte» chiedono se resta; `premap/__init__.py:259` lo usa ancora per una lacuna.

### Nit

- **N1.** T0.4 è un verbale di verifica con nomi di funzione e righe: va in una nota di verifica. T1.17 («3 funzioni >80 righe») e gli elenchi di fixture di T2.3 non sono architettura.
- **N2.** Un contratto «a refactoring finito» porta colonne «Stato»: lo stato sta nel piano.
- **N3.** «Unico piano attivo»: `docs/roadmap.md` tiene ancora tabella di stato e fasi proprie; `docs/plans/2026-11-19-verso-i-riferimenti.md` è nel working tree; `pipeline_tree.py:314-321` tiene una terza copia degli otto step.
- **N4.** Lanciatore comune a due step (`architettura.md` riga 30) o a quattro (riga 109).
- **N5.** Spike SQL (T1.5) fuori dal cancello T1; `languages/sql.py` e `plsql.py` sono regex, contro la regola tree-sitter: difetto da classificare in T0. SCIP incrementale (T2.2) senza il collo di bottiglia citato.

## Note del coordinatore (non sono rilievi dei revisori)

**Controllato sul repository** dopo i rapporti:
- B1: i tre verdetti «no» sono alle righe citate di `flask-routes`, `fastapi-routes`, `django-routes`.
- M2: `benchmarks/stack-build-tools/` non ha file tracciati.
- M6: `python_record.py` usa `sys.monitoring`.
- M8: nessun ramo né commit `feat/link-key-shape`; `docs/pipeline/` ha 24 file tracciati; `approval_required` non è in `daodan/`; `service-registry.json` non ha `surface`.

- B1, citazione di `fastapi-routes/README.md:8`: nella parte di riga che ho letto (primi 330 caratteri) il verdetto è «no, non aggiunge abbastanza a Noir per essere collegata»; il testo citato dal revisore non l'ho cercato nel resto della riga.

Gli altri rilievi non sono controllati.

**Controlli successivi (agente che ha aggiornato i documenti).**
- M2, «Syft non è nel repository»: **falso**. `benchmarks/project-model/` ha `tools/syft.py`, `results/syft.json` e la misura di Syft 1.57.1 in `REPORT.md` (verificato anche dal coordinatore). Resta aperto che cosa il confronto del piano debba decidere oltre a quella misura.
- Gli altri fatti accertati sono scritti nel piano sotto le voci, come **[accertato nel repository]**.
- La fase 1 non è stata rieseguita dopo le modifiche: l'utente ha chiesto di passare alla fase 2.

**Modifica del documento dopo la lettura dei revisori.** I due revisori hanno letto il commit `78e070129`; i numeri di riga qui sopra sono di quella versione. Dopo, su richiesta dell'utente e fuori dai rilievi, `architettura.md` ha avuto la sezione «Nodi del grafo: tipo e logo» e la riga estesa dell'anagrafica delle tecnologie (non ancora in un commit).

**Aggiornamento dello stesso giorno, su richiesta dell'utente.** Il rilievo qui sotto descrive lo stato di prima: le 37 tessere e quella di `doctrinephp` sono state copiate in `daodan/data/marks/` (non in un commit; test del registro non eseguiti, li esegue la CI). La causa resta e ora è scritta in T0 punto 3.

**Rilievo del coordinatore, per T0 punto 3 («37 marchi senza cornice»).** I 37 loghi senza cornice vengono tutti da Simple Icons, aggiunti da `7e1b95516` (24 novembre). Dal codice: `registry_build.apply_marks` scrive il simbolo nudo, nessun file tracciato disegna la tessera e il generatore sta solo nella cartella non tracciata `.claude/worktrees/own-marks/`. Quindi `registry_build.py marks` sostituirebbe anche le tessere esistenti con il simbolo nudo: letto nel codice, non eseguito (il commit del 24 novembre ha solo aggiunto 37 file e tolto 1, senza modificare gli altri).
