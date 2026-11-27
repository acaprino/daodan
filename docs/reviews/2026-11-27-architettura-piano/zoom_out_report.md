# Stadio 5 — Initial Zoom Out

- **Bersaglio:** `docs/specs/architettura.md` (FeatureRange, tutto il file) e `docs/plans/refactoring.md` (DetailedRange, tutto il file), stato al commit `a4360b01b`.
- **Contesto passato ai revisori:** `docs/backlog.md`, `docs/reviews/2026-11-25-refactoring/zoom_out_report.md`, `docs/reviews/2026-11-25-refactoring/goldfish_review_report.md`. Link esterni esclusi per scelta del proprietario.
- **Standard:** `zoom-out-standard.md` (egm v0.1.1).
- **Revisori:** Zoom Out (completato), Inventive Catalyst (completato, modalità REVIEW).
- **Isolamento ottenuto:** subagenti nuovi, senza la conversazione; ricevono comunque `CLAUDE.md`, `AGENTS.md` e gli hook di sessione, quindi non è un isolamento Goldfish verificato. Solo lettura per istruzione, non per permesso.

---

## Revisore Zoom Out

1 Blocker, 8 Major, 5 Nit. Nessun rilievo blocca la tranche aperta `T0.A`. I rilievi della fase 1 (B1, B2, M1–M8) sono chiusi dal proprietario nelle «Scelte aperte» del piano e non sono ripetuti. Non è un rilievo la misura a 80.000 nodi con il blocco «altri N»: poggia su un collo di bottiglia misurato (`benchmarks/codebase-explorer/README.md:53-56`).

### Blocker

**ZO-1. Il file `.daodan` è un secondo padrone dei dati confermati a mano, accanto ai file dichiarati che esistono già.**
- *Severità:* Blocker per la prontezza di `T2.E`; non blocca `T0.A`.
- *Ambito:* spec «Che cos'è un nodo» (r. 97-99), «File di progetto» (r. 185-243), Principio 2 (r. 16); piano punto 7 di T2 (r. 187) e riga `T2.E` (r. 27).
- *Motivazione:* la spec dice che oggi i nodi stanno in due archivi e ne aggiunge un terzo, senza dire che cosa sostituisce né chi è il padrone dei fatti confermati a mano. Nel codice c'è già un canale per i record confermati dal progetto: `codebase-system-map.json` (`daodan/core/system_map.py:590-644`) letto sopra la mappa registrata; `codebase-modules.json` (`module_records.py:18`, `module_derive.py:344-353`) con il suo registro delle proposte; `system_map._record_nodes` (`system_map.py:898-953`) che riconcilia le proposte e rifiuta di rinominare un nodo dichiarato. La spec non nomina questi file e permette di rinominare a mano qualunque nodo nel `.daodan`. I file dichiarati stanno nel progetto, sotto Git: storia, autore, diff e copie divergenti ci sono già. Il `.daodan` ricostruisce tutto a mano e non scrive quale soluzione pronta ha valutato (`AGENTS.md`). Da valutare: Git sui file dichiarati, l'estensione Session di SQLite.
- *Proposta minima:* una frase del proprietario che dica se `codebase-system-map.json` e `codebase-modules.json` restano, diventano un'importazione o si ritirano; chi prevale quando un nodo è sia dichiarato sia modificato a mano; quali soluzioni pronte sono state valutate per la storia.

### Major

**ZO-2. Il formato mette sotto versione l'intero grafo derivato, simboli e risultati degli strumenti compresi.**
- *Ambito:* spec r. 99, 201-206 (`technical_records`, `evidence.blob_ref`, `record_version`), 217-231.
- *Motivazione:* gli edit che giustificano la storia stanno sullo strato con il nome dato da una persona. Moduli, file, simboli e risultati degli strumenti si ricalcolano dallo snapshot, già un SQLite versionato (`snapshot_store.py:16-17, 365-366, 654-656`). Per i simboli esistono già identità e storia fra snapshot: `semantic_store.py:126-168` (`meta_symbols`, `meta_changesets`, `meta_changeset_deltas`) e il confronto alle r. 693-715.
- *Proposta:* versionare nel `.daodan` solo gli oggetti che un edit può toccare o che un flusso cita; richiamare lo strato derivato per analisi e snapshot; riusare `meta_symbols` per l'identità dei simboli.

**ZO-3. Migrazione v1→v2 e importazione del vecchio ZIP: due percorsi per formati che nessuno scrive.**
- *Ambito:* spec r. 193, 266, 270; piano r. 198-200.
- *Motivazione:* in `daodan/` non c'è lettore né scrittore del formato (niente `0x44414F44`; `manual_edits` e `step_transitions` solo nella spec). La «prova su v1 in memoria» non lascia file. Lo ZIP Bank of Anthos con `v2/graph.sqlite` non è nel repository. Il Cancello `T2.E` chiede comunque le prove della migrazione. Il confronto fra copie tramite UUID (r. 213) non ha un punto nel piano.
- *Proposta:* il primo formato scritto dal codice è l'unico; la migrazione si aggiunge quando esiste un file di utenti da migrare.

**ZO-4. Specie chiuse nel DDL e in costanti del codice, contro il Principio 4.**
- *Ambito:* spec r. 105, 113, 344-350, 193; tabella «Le anagrafiche» (r. 498-507).
- *Motivazione:* l'elenco sta già in `flows.py:109-110` (`NODE_TYPES`), `system_map.py:38`, `system_levels.py:26-27` (con parole diverse dalle nature della spec); la spec lo aggiunge come `CHECK` nel DDL, quindi ogni specie nuova è una versione del formato e una migrazione. La v2 nasce proprio per vincolare le specie, e tre specie sono ancora «da creare».
- *Proposta:* anagrafica in `daodan/data/` con specie, natura e icona, consultata da `system_levels`, `app_view`, writer e `viewer/src/icons.ts`; nel file una tabella di specie con chiave esterna caricata dall'anagrafica.

**ZO-5. «Profilo» regge il Cancello T2 ma non ha definizione né step che lo produca.**
- *Ambito:* spec r. 155-157, 202-203, 257, colonne `profile` (r. 364, 380), r. 183; piano Cancello T2 (r. 196), punto 5 di T2 (r. 184).
- *Motivazione:* «profilo» non è in «Termini», nessuno degli otto step lo produce, nessun punto del piano lo costruisce, la fixture `real-bank-of-anthos/system.json` non ha un campo profilo. Le varianti stanno in `T3.C`, dopo il cancello che le chiede. Processi e varianti li identifica il mapper (`benchmarks/system-map/README.md:266`), che non compare negli step né nei servizi comuni.
- *Proposta:* dire chi produce flussi, varianti e profili; spostare il caso dei due profili nel cancello della tranche che li consegna.

**ZO-6. `T0.C` costruisce l'approvazione dentro un proxy che `T3.A` può sostituire.**
- *Ambito:* piano r. 103, 28, 209; spec r. 522.
- *Motivazione:* rifacimento messo in conto; la scelta del proxy usa gli stessi criteri di `T0.C` e viene dopo il lavoro che può invalidare.
- *Proposta:* portare in `T0.C` la sola prova di scelta del proxy; a `T3.A` restano `--cap-drop`, `--user`, lockfile e tabella dei comandi.

**ZO-7. Decisioni durevoli salvate in una cartella di cache, con una chiave di progetto non definita.**
- *Ambito:* spec r. 519, 529, 85-86; piano r. 100.
- *Motivazione:* whitelist, blacklist e comandi confermati vanno in `embedding_worker.shared_cache_dir`, che il docstring (`embedding_worker.py:57-70`) dice cartella di cache (`LOCALAPPDATA`, `XDG_CACHE_HOME`). Perderla vuol dire perdere un «blocca sempre». La funzione vive in un modulo di embedding. «Sempre per questo progetto» non dice come si identifica il progetto.
- *Proposta:* cartella di dati o configurazione per utente da una libreria pronta (es. `platformdirs`), in un modulo comune; una chiave di progetto definita in «Termini».

**ZO-8. `T2.C` mette il calcolo delle viste nella tranche di `assemble_graph`.**
- *Ambito:* piano r. 25 e punto 5 di T2 (r. 181-185); spec r. 136, Principio 3 (r. 17).
- *Motivazione:* aprire, chiudere e filtrare sono presentazione; il punto unico c'è già (`app_view.view`, `app_view.py:147`, con `system_levels.view`); `assemble_graph` per il Principio 3 non conosce l'interfaccia. `T2.C` diventa un fascio largo sul cammino critico di `T2.D`, `T2.E`, `T3.B`, `T3.C`.
- *Proposta:* nominare `app_view.view` come punto unico; spostare viste e filtri in `T2.D` o in una tranche propria; `T2.E` aspetta solo il modello dei nodi.

**ZO-9. La spec è cresciuta oltre il problema che dichiara.**
- *Ambito:* spec «Il problema» (r. 9-11) contro «La mappa» (r. 91-183) e «File di progetto» (r. 185-477); piano `T0.C`, `T2.D`, `T2.E`.
- *Motivazione:* il problema è ordine dei passi, duplicazioni e regole sul singolo caso; circa il 60% delle righe descrive superficie di prodotto nuova che da quel problema non discende. `T2.E` è una riga di piano contro circa 290 righe di spec.
- *Proposta:* dire con le parole del proprietario perché file e mappa entrano in questo refactoring, oppure spostare «File di progetto» in una spec propria (DDL come file versionato con un test) e lasciare qui un paragrafo e il link.

### Nit

- **ZO-N1. Righe di stato superate:** T0 punto 4 (r. 59) dice «da confermare in `T0.A.2`», già fatto; `T0.A.4` (r. 84) cita il fallimento di `test_codebase_map_app.py` che la tabella chiude (r. 56); la Regola 5 (r. 38) confronta con `modal_pytest.py:18` (3.919 / 75) invece che con la base di `T0.A.2` (4630 / 78).
- **ZO-N2. Nome che si confonde:** l'estensione `.daodan` contro la cartella `.daodan/` già in uso (`run_store.py:50`, `app.py:750`, `.gitignore:6`).
- **ZO-N3. Corrispondenza degli step scritta in più posti** (`README.md`, `docs/plugins/codebase-map.md`, `docs/pipeline/`, `pipeline_tree.py`, la spec, `T1.15`); `T0.B.3` la riscrive a mano. Meglio rimandare a `docs/pipeline/`, che è generata.
- **ZO-N4. Padrone dei pacchetti ripristinati:** la tabella degli step li dà «da `find_modules`» (r. 33), ma il ripristino è la «Preparazione» dei servizi comuni (r. 512).
- **ZO-N5. Parole da togliere dall'interfaccia, elenchi diversi:** spec r. 492 («pre-mappa», «scan», «stack», «analyze») contro piano r. 151 («pre-mappa», «scan», «analyzer»).

---

## Revisore Inventive Catalyst

3 Major, 3 Nit. Lasciati stare perché invarianti o scelte del proprietario: codice solo nel container, strumento ufficiale e tree-sitter, niente build locale, prove su Modal, solo Sigrid e Imago, approvazione solo dalla GUI, una tranche aperta alla volta. Già bilanciati: I1/M1 (blocco e popup in `T0.C`), I2 (diagnosi cieca in `T0.B.2`), I3 (`blocked` in `daodan/core/pipeline/plan.py:16-17`), I4 (quarantena con scadenza), B1 (Noir per Django, FastAPI e Flask), M5 (modello di evidenza da misurare).

**IC-1 (Major). Il proxy di `T0.C` si costruisce prima di scegliere lo strumento che lo sostituisce.**
- *Ambito:* piano `T0.C` punti 3-4 (r. 100-101) e r. 103, `T3.A` (r. 28, 209); spec «Strumento del proxy» (r. 522).
- *Falso compromesso:* il piano accetta il rifacimento («se `T3.A` sceglie Smokescreen, la parte dentro il proxy si rifà»). La parte non è marginale: indirizzo risolto nel popup, rete dell'utente, prove su DNS, IP letterali e indirizzi interni. Oggi `PROXY_SCRIPT` riceve la lista in `argv` e controlla solo nome e porta 443, senza indirizzo risolto (`daodan/core/container.py:217-288`). `T0.C` scrive a mano uno dei criteri su cui `T3.A` confronta i due proxy: rovescia l'ordine di `AGENTS.md` (prima la soluzione pronta). In senso opposto `T3.A` tiene dietro `T0.C` lavoro indipendente dal proxy: `--cap-drop ALL`, `--user`, rifiuto dei lockfile (`container.py:867, 1113, 1413, 1557`).
- *Proposta (Preliminary Action + Segmentation):* spostare all'inizio di `T0.C` solo la misura di `T3.A`.1; costruire whitelist, blacklist e popup sullo strumento che vince; mettere indurimento e rifiuto dei lockfile in una tranche bloccata solo da `T0.A`, dentro il cancello di `T1.B`.
- *Costi secondari:* `T0.C` parte più tardi; con Smokescreen un artefatto in più da fissare per sha256; `--user` anticipato può rompere `mise` e i volumi scrivibili già in `T1` (piano r. 210); una riga in più nella mappa.

**IC-2 (Major). `run_and_observe` dipende da `link_calls` per un confronto che il contratto assegna ad `assemble_graph`.**
- *Ambito:* spec tabella degli step, righe 7 e 8 (r. 35-36), Principio 3; piano `T2.B` punto 4 (r. 180), `T3.B` punto 3.
- *Falso compromesso:* la riga 7 fa dipendere `run_and_observe` dal «Grafo statico: da `link_calls`», mentre «osservato contro provato» è di `assemble_graph`. Nel codice, senza grafo statico fresco i test non girano (`no-static-graph`, `daodan/core/dynamic/__init__.py:575-597`; `plan.py:162-164`); per collocare i siti bastano i riferimenti di `read_code`, gli archi provati servono solo a contare `agree`, `wider`, `conflict` (`dynamic/__init__.py:165-235`); la chiave della cache contiene motore, versione e `adapter_digest` dell'indicizzatore statico (`dynamic/execution_cache.py:39-45`), quindi aggiornare SCIP rifà tutte le corse; le righe osservate vivono dentro la voce statica (`code_graph.py:1155-1167`, `write_observed`). Dove la risoluzione statica fallisce si perde anche la prova osservata, e le due fasi più costose sono in fila.
- *Proposta (Extraction):* `run_and_observe` registra i siti sui riferimenti di `read_code`, scrive le righe osservate in un archivio suo con freschezza sua; il confronto passa ad `assemble_graph`; nel piano l'osservatore aspetta lettura e preparazione, non il risolutore; la riga 7 perde «Grafo statico».
- *Costi secondari:* un archivio e un legame di freschezza in più; `language_coverage` oggi conta i due insieme; un arco solo osservato va mostrato come tale, non come conflitto; esecuzione parallela contende motore e CPU.

**IC-3 (Major). Profili e revisioni servono a `T2.D` e al Cancello T2 prima che `T2.E` li definisca.**
- *Ambito:* spec criteri di accettazione (r. 138), «Seguire un flusso» (r. 157), «File di progetto»; piano `T2.C`–`T2.E` (r. 25-27), Cancello T2 (r. 196), Cancello T2.E (r. 200).
- *Falso compromesso:* i criteri valgono «a parità di revisione, profilo» e il Cancello T2 chiede i due percorsi dei due profili; revisione, variante e profilo hanno una sola definizione, il DDL del `.daodan` consegnato da `T2.E`; `T2.D` e `T2.E` aspettano entrambe solo `T2.C`; la vista oggi è `view(envelope, groups, shown, symbols_of)` senza revisione né profilo (`daodan/core/app_view.py:147`).
- *Proposta (Segmentation):* scrivere dove vivono varianti, profili e revisione prima di `T2.E`, oppure dividere `T2.E`: prima parte in `T2.C` (flussi a varianti e profili secondo il DDL, revisione 1, senza riconciliazione), seconda parte dov'è (storia, edit, rianalisi, conflitti). `T2.D` aspetta solo la prima.
- *Costi secondari:* una tranche in più; la prima parte deve rispettare già il DDL; il Cancello T2 dipende da una parte del formato; due sorgenti per la vista finché resta `daodan/visual@1`.

**IC-N1. La preparazione «una per analisi» non ha un padrone né una tranche.** Spec r. 33-34 e 512. La riga 6 chiede un «Ambiente preparato» senza dire da chi; nel codice ogni esecuzione ha la sua preparazione con volumi creati e rimossi (`container.py:17-26`), solo Node condivide il ripristino (`node_preparation.py:1`). *Proposta:* estendere la sessione di `node_preparation` a tutti i gestori come servizio comune con un nodo nel piano unico e i consumatori nei `needs`; assegnarla a una tranche (es. `T1.B`). *Costi:* preparazione più grande per chi ne usa una parte, più disco, fallimenti da tenere separati per gestore, ciclo di vita dei volumi.

**IC-N2. La prova di una rianalisi non ha una regola di uguaglianza.** Spec r. 205, 211, 214. Letta alla lettera, ogni rianalisi apre una versione per ogni oggetto citato, contro «versioni dei soli oggetti cambiati»; il diff mostrerebbe cambiati anche i nodi solo spostati di riga. *Proposta:* dichiarare la chiave di contenuto di una prova (`locator`, intervallo, simbolo, `blob_ref` o digest, `record_version`) e riusare la riga; facoltativo, righe fuori dallo stato versionato. *Costi:* colonna chiave calcolata (`UNIQUE` tratta i `NULL` come distinti); «ancorata» diventa «la prima analisi che l'ha prodotta».

**IC-N3. La suite gira solo a mano, e il riferimento della Regola 5 è vecchio.** Piano Regole 3-5 (r. 36-38), M7 (r. 165). `modal.yml` ha solo `workflow_dispatch` (`.github/workflows/modal.yml:5-15`); la corsa costa 105-118 s; lo SHA si lega a mano perché `modal_pytest.py` carica il disco (`tests/modal_pytest.py:6-7, 124-128`). *Domanda al proprietario:* il trigger manuale è una scelta di costo? Se sì resta un invariante. *Proposta:* `run=suite` al push su `develop` con filtro sui percorsi e `concurrency`; riferimento dei cancelli nel file di baseline in `docs/verification/`. *Costi:* spesa Modal per push; corse rosse per il test instabile di Playwright finché la quarantena non è leggibile dal runner.

---

## Sovrapposizioni fra i due revisori

- **ZO-6 = IC-1** (ordine proxy `T0.C` / `T3.A`): due revisori indipendenti, stessa conclusione.
- **ZO-5 ≈ IC-3** (profilo e varianti richiesti dal Cancello T2 senza un produttore).
- **ZO-N4 ≈ IC-N1** (padrone della preparazione e dei pacchetti ripristinati).
- **ZO-N1 ⊃ IC-N3** (riferimento vecchio della Regola 5).
