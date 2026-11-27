# Stadio 7 — Critic Review (giro 1)

- **Bersaglio:** `docs/specs/architettura.md` (FeatureRange, tutto il file, 539 righe), commit `a4360b01b`.
- **Contesto:** `docs/plans/refactoring.md`, `docs/backlog.md`, `docs/reviews/2026-11-25-refactoring/zoom_out_report.md`, `docs/reviews/2026-11-25-refactoring/goldfish_review_report.md`.
- **Revisori e standard:** design (`feature-spec-standard.md`), structural (`feature-spec-standard.md`), style (solo persona).
- **Identificativi:** `<revisore>-<giro>-<n>`.
- **Isolamento ottenuto:** subagenti nuovi, senza la conversazione; ricevono comunque `CLAUDE.md`, `AGENTS.md` e gli hook di sessione. Solo lettura per istruzione: il revisore structural ha eseguito un comando Bash `test -e` (sola verifica di esistenza dei percorsi), fuori dal vincolo Read/Grep/Glob; non ha modificato né lanciato altro.

---

## Revisore Structural

1 Blocker, 10 Major, 6 Nit. Verificato e corretto: gerarchia H1 → H2 → H3 senza salti; i due blocchi `sql` chiusi; 24 specie e 21 tabelle coerenti fra testo, DDL e prove; ancore interne e link a piano e backlog risolti. Link esterni non verificati.

### Blocker

**structural-1-1. Mancano le alternative considerate (Alternatives Rule).**
- *Ambito:* tutto il documento; scarti in linea alle r. 54, 57, 512, 514, 522; legenda r. 5.
- *Discrepanza:* nessun titolo per le alternative; scarti sparsi e senza motivo (Django/FastAPI/Flask r. 54; LSIF/LSP r. 57; `git+` non rifiutato r. 512; «solo proxy verso registri autorizzati» e «come una CI» r. 514; Smokescreen contro il proxy attuale r. 522, ancora aperto). I motivi stanno fuori dalla spec e non sono collegati (`benchmarks/{django,fastapi,flask}-routes/README.md`, backlog «Fermo o ritirato»). `[deciso]` («approvata dal proprietario», r. 5) attribuisce lo scarto senza link a issue, discussione o PR, ciò che lo standard vieta.
- *Correzione:* una H2 con una tabella (alternativa, perché scartata, prova con link) e il link alla registrazione della decisione.

### Major

**structural-1-2. Obiettivi e non obiettivi.** «Il problema», r. 9–11. Un solo obiettivo in grassetto dentro il problema, nessun titolo per i non obiettivi (sparsi: macOS e iOS r. 75, link al backlog r. 3, «Fuori da T1/T3» nel piano). L'obiettivo copre il riordino, ma molte sezioni specificano funzioni nuove che nessun obiettivo nomina (mappa senza limiti, filtro per natura, `.daodan`, uscita di rete con approvazione). Il problema non rimanda allo stato di oggi (la corrispondenza 6→8 step sta solo nel punto 15 di T1 del piano). *Correzione:* H2 «Obiettivi e non obiettivi», una riga per ogni H2, link al backlog e al punto 15 di T1.

**structural-1-3. Manca «Rischi e mitigazioni».** r. 159–167 e 509–525. Sicurezza, limiti di scala e modi di guasto (solo principio 7) non sono riuniti; le mitigazioni non sono legate ai rischi. *Correzione:* tabella rischio, sezione del contratto, mitigazione, che collega ciò che c'è.

**structural-1-4. La tabella degli step non segue il principio 3.** r. 17 e tabella r. 27–36. Il principio chiede letture, scritture e comportamento in caso di guasto; la tabella ha colonne solo per le prime due; il guasto è sparso (r. 20, 56). *Correzione:* colonna «Se fallisce» (lacuna emessa, chi prosegue) o un link per step.

**structural-1-5. La notazione dello stato non segue la legenda.** r. 5, 39, 53, 71, 75, 77, 99, 103, 111, 130, 156, 164, 175, 504, 512, 514. La legenda dà quattro valori per una colonna «Stato» con il traguardo fra parentesi; nel testo compaiono «Oggi nel codice» (r. 103), «Da cambiare» (r. 111), «Da completare nell'app e nell'esploratore» (r. 156), «Contratto del formato; da implementare nell'app» (r. 99), «*Da creare.*» senza tranche (r. 130, 164, 175), «(non ancora nel codice; …)» (r. 53, 71, 75, 77, 514), «(da creare, `T3.A`)» (r. 512). «Proposta» non è mai usata; fra parentesi c'è la tranche, non il traguardo; la r. 39 descrive `build-tools.json` al presente mentre la r. 504 lo dà «Da creare» e il file non c'è in `daodan/data/`. *Correzione:* una sola forma (es. `*Stato: <valore> (<tranche>)*`) e legenda con «tranche».

**structural-1-6. Ordine delle sezioni.** r. 25, 38–39, 272–477, 479–525, 527. Il DDL (circa 200 righe, 37% del file) sta a metà e separa la pipeline dalle H2 che essa richiama («Il piano», «L'interfaccia segue la pipeline», «Le anagrafiche», «Servizi comuni»); «Termini» è in fondo senza link in avanti, ma i termini si usano dalla r. 38. *Correzione:* «Schema SQLite v2» in appendice dopo «Termini» (l'ancora non cambia), avvicinare o collegare le H2 della pipeline, collegare «Termini» dall'intestazione.

**structural-1-7. I criteri di accettazione hanno tre forme.** r. 138, 157, 268–270. Paragrafo in grassetto, punto «Caso di accettazione:», H3 di un solo paragrafo con circa nove prove; i cancelli del piano li citano ma non si possono contare né collegare uno per uno. *Correzione:* elenco numerato, una prova per voce, ancora stabile.

**structural-1-8. Regole normative sotto titoli che non le annunciano.** r. 99, 193, 266. La migrazione v1→v2 (r. 193) sta in «Come riconoscere il file»; l'importazione del vecchio ZIP (r. 266) sta sotto «Esempio di lettura e revisione»; il paragrafo `[deciso]` sul `.daodan` (r. 99) ripete le r. 209–242. *Correzione:* H3 «Migrazione e importazione» con le r. 193 e 266; alla r. 99 resta la frase con il link.

**structural-1-9. Prove citate senza percorso.** r. 193, 270. «La v1 al commit `c7bc75b`» e «La prova del proprietario, su v1 in memoria» non hanno percorso; `head_rev|revision_uuid|tree_sha256` non compare in `daodan/`, `tests/`, `benchmarks/`. `AGENTS.md` chiede che una prova resti nel repository. *Correzione:* citare il percorso del test o scrivere la prova come lacuna.

**structural-1-10. Collisioni di termini e glossario incompleto.** r. 20, 77, 81, 89, 155–162, 175–177, 204, 226, 257, 479, 518, 527–538. «Passo» ha quattro sensi (step, passo di CI r. 89, passo di flusso r. 155–257, salto di percorso r. 162) e il piano chiama «passi» gli step (T1.E); «piano» è l'oggetto di Daodan (r. 479) e il documento di refactoring, nella stessa frase alla r. 77; sinonimi: «frecce» e «archi», «usa» e `uses` (r. 175–176), «anagrafica» e «catalogo». Mancano lacuna, ripiego, adattatore, involucro, mappa di sistema, esploratore, flusso, variante, profilo, grado. Noir e Kiri definiti due volte (r. 44 e 532, 511 e 531). *Correzione:* un termine per concetto e le voci mancanti in «Termini».

**structural-1-11. Gli archi non hanno una sezione propria.** r. 110, 124, 146–151, 202, 215, DDL 358–366. Tipi e gradi sparsi in cinque punti, gradi dati solo «per esempio» (r. 215), `kind` e `grade` liberi nel DDL. *Correzione:* H3 «Archi» che riunisca ciò che c'è.

### Nit

- **structural-1-12. Titolo e intestazione** (r. 1, 3): l'H1 parla di «contratto della pipeline» ma più di metà è mappa e formato; «estratto dal refactoring del 25 novembre» con decisioni del 26; manca la data dell'ultimo aggiornamento.
- **structural-1-13. Marcatori `[deciso]`** (r. 9, 53, 106, 512, 514; r. 29): posizione variabile, tre volte nella stessa riga alla r. 106; manca `[deciso, su delega a Fable]`, così la lacuna di `list_files` (r. 29) appare senza marcatore.
- **structural-1-14. Riferimenti incrociati** (r. 38, 57, 157, 171, 215, 257, 266, 484, 486, 492, 503, 512, 514): ancore e citazioni «» senza link mescolate; il piano cita «Modello di evidenza», che non è un titolo; «secondo l'architettura» (r. 215) vago; «Il vecchio esempio Bank of Anthos» senza riferimento; citazioni di documenti rimossi senza fonte (r. 514); profili con due nomi («Kubernetes standard» r. 157, `kubernetes-standard` r. 257); schema del registro descritto due volte con campi diversi (r. 171, 503); due elenchi «chiusi» non elencati (tipi di azione r. 486, tabella dei comandi r. 512).
- **structural-1-15. Raggruppamento in «La mappa»** (r. 95–169): H3 del modello alternate a H3 della vista; «Corrispondenze» fra due sezioni della vista, «Le tecnologie come nodi» in fondo.
- **structural-1-16. Formattazione** (r. 106–107, 113, 135–136, 197, 221, 239–242, 259, 503–504, 529–538; r. 44, 532): due stili di separatore di tabella; paragrafi in celle; «Natura per specie» in prosa; voci di «Integrità al salvataggio» con molte regole; `->` e «(+ `surface`)»; citazioni miste; percorsi in due forme; glossario fuori ordine alfabetico; apostrofi curvi e dritti mescolati.
- **structural-1-17. Comando eseguito contro il vincolo** (procedura del revisore): un `test -e` via Bash; non incide sul documento.

---

## Revisore Design

1 Blocker, 15 Major, 6 Nit, raggruppati per causa. **Nota di isolamento:** il revisore ha letto anche lo stadio 5 di questa review (`zoom_out_report.md` di questa cartella), che non era nel suo contesto, e cita ZO-x e IC-x; i rilievi che vi si sovrappongono aggiungono solo il modo di fallire.

**Escalation del 25 novembre ancora aperte, nel testo di oggi** (dal revisore):

| Gruppo | Stato oggi | Nota |
|---|---|---|
| G1 Problema e obiettivi | Parziale | Mancano non obiettivi e criteri di successo (design-1-2). |
| G2 Alternative | Assente | design-1-1. |
| G3 Django, FastAPI, Flask | Chiuso | Resta Noir, voci `partial` (r. 54, 173). |
| G4 Minaccia e rischi | Parziale | Mancano modello di minaccia e sezione dei rischi (design-1-2, 1-8, 1-9, 1-11). |
| G6 Fallimento degli step | Assente | Principio 3 senza colonna; «Ambiente preparato» senza padrone (design-1-3). |
| G10 Limiti | Parziale | «qualche GB» (r. 77), «tempo reale», tipi di azione senza elenco (r. 486); nessun tetto di tempo, memoria o disco. |
| G11 Piano unico | Parziale | Mancano dipendenze, ripresa, scrittore, concorrenza (design-1-6). |
| G12 Backend runtime | Chiuso | Restano `*_record.*` e OpenTelemetry da valutare (r. 51, 58). |
| G13 Effetti dell'esecuzione | Parziale | Controlli distruttivi non trattati; li contiene `--network none` (r. 513), ma la spec non lo dice. |
| G14 Uscita dei segreti | Parziale | Mancano il `.daodan` condiviso e i nomi dei pacchetti privati verso i registri pubblici (design-1-8, 1-11). |
| G15 Dipendenze uniche | Assente | Kiri 0.2.0, Noir solo `linux-x86_64`, il fork (design-1-9). |
| G16 Unione HTTP | Assente; la spec dice meno del codice | design-1-7. |

### Blocker

**design-1-1. Manca la valutazione delle alternative, obbligatoria per lo standard.** Tutto il documento; scelte che contano: otto step contro sei (r. 23-36), niente LSIF/LSP (r. 57), Django/FastAPI/Flask (r. 54), un padre solo (r. 108), storia SQLite fatta da Daodan (r. 187-477), specie chiuse con `CHECK` (r. 344-350), Kiri su Windows (r. 511), ritiro dell'apertura «come una CI» (r. 514). Un percorso solo per scelta, motivato da `[deciso]` senza link. I motivi esistono altrove (`benchmarks/{django,fastapi,flask,express}-routes`, Syft in `benchmarks/project-model/REPORT.md`), ma `docs/backlog.md` si dichiara non citabile. Alternative assenti: Git sui file dichiarati o l'estensione Session di SQLite (ZO-1); tabella delle specie con chiave esterna (ZO-4); Docker Desktop, Podman machine o Rancher Desktop al posto di Kiri; sei step con le competenze riassegnate. *Raccomandazione:* sezione «Alternative considerate», una riga per scelta con opzione scartata, compromesso concreto e link; nessun `[deciso]` va riaperto.

### Major

**design-1-2. Mancano non obiettivi, criteri di successo e rischi.** r. 9-11, 159-167, 509-525; `benchmarks/codebase-explorer/README.md:53-56`. Il README ha già obiettivi (2 s per il grafo, 100 ms per la selezione; oggi 4,6 s a 300 nodi), la spec scrive solo «Misura che manca» (r. 166) e il Cancello T2 chiede di «registrare» tempo e peso a 80.000 nodi, quindi non può fallire. «Più figli di quanti la vista ne regge» (r. 164) non dice quanti. *Raccomandazione:* non obiettivi; soglie misurabili per la vista (primo disegno, selezione, memoria, dimensione di «altri N»); tabella dei rischi con mitigazione e tranche.

**design-1-3. Il contratto degli step non dice che cosa succede se uno step fallisce, né dove gira.** Principio 3 (r. 17), tabella (r. 27-36), r. 56. Il comportamento senza container è scritto solo per `find_entry_points`; non per `find_modules`, `link_calls`, `run_and_observe`, né per `recognize_stack` che fallisce a monte. Non è detto quali step girano sull'host: il fork gira sull'host con Node (`daodan/core/stack_analyser.py:101-149`), le query tree-sitter anche, `go-enry` nel container; la regola di `AGENTS.md` (un test per ogni strumento lanciato sull'host) non è nel contratto. *Raccomandazione:* colonne «Se fallisce o manca il container» e «Gira su», e un padrone per la preparazione.

**design-1-4. Due padroni per lo stesso fatto e un ritorno indietro non mostrato.** r. 31-32, Principio 2. `recognize_stack` e `find_modules` scrivono entrambi «toolchain» e «servizi», e «servizi» non è definito (SaaS o servizi di Compose e CI, `technologies.configured_services`). Il fork riceve le dichiarazioni di `find_modules` (parametro `declarations` di `stack_analyser.command`; piano: «il fork si rilancia»), quindi `recognize_stack` gira di nuovo dopo `find_modules`, mentre la tabella dice «Nessun modulo». *Raccomandazione:* un padrone per toolchain e servizi con il termine definito; il secondo passaggio come riga o dipendenza esplicita.

**design-1-5. Nessun componente produce nodi astratti, flussi, varianti e profili.** r. 97, 107, 110, 153-157, 183, 226; Principio 3. Sovrapposto a ZO-5, IC-3, CO-1. In più: un nodo sintetico chiede «un'identità dichiarata o una corrispondenza confermata» (r. 226); se lo propone un modello a ogni rianalisi, i nomi cambiano e ogni rianalisi apre proposte `identity_match` da confermare a mano. *Raccomandazione:* nominare il produttore (servizio comune o adattatore fuori dagli step), letture e scritture, e come resta stabile l'identità (es. riproporre solo i nodi non dichiarati).

**design-1-6. Il contratto del piano dice meno del codice.** r. 479-486; `daodan/core/pipeline/plan.py:10-17`. `plan.py` ha già `needs` e `blocked`; la spec no. «L'esecuzione si ferma su quell'azione» non dice se si fermano le azioni indipendenti. Mancano annullamento, ripresa dopo arresto e dopo consenso, lo scrittore del piano e la concorrenza fra GUI, MCP e CLI; l'elenco chiuso dei tipi di azione non c'è. *Raccomandazione:* `needs` e `blocked` nel contratto; si ferma solo l'azione e ciò che ne dipende; stato `annullata`; elenco dei tipi; uno scrittore con un blocco per progetto.

**design-1-7. La regola di unione HTTP dice meno del codice e produce archi falsi.** r. 61-65; `daodan/core/flows.py:55-59`. La spec dice «dove percorso e metodo coincidono»; il codice chiede lo stesso servizio, fa vincere la rotta più letterale, rende un pareggio incerto con lacuna e candidati, dà il servizio `*` alle rotte di Noir, rende lacuna un catch-all. Letta alla lettera la spec toglie il servizio: in Bank of Anthos i percorsi comuni (es. salute) si legano al servizio sbagliato. Prefissi, mount, URL di base e percorsi calcolati non sono trattati. *Raccomandazione:* scrivere la regola del codice, valida per ogni adattatore di legame.

**design-1-8. Approvare un host: il legame va al nome, e l'archivio delle approvazioni non è protetto.** r. 514-521; `daodan/core/container.py:274-278`, `daodan/core/embedding_worker.py:57-70`. Il proxy controlla nome e porta e risolve alla connessione; il popup mostra l'indirizzo una volta: un host approvato che poi risolve verso `127.0.0.1`, `169.254.169.254` o la rete locale passa (rebinding DNS, SSRF dal container). Whitelist e blacklist stanno in una cartella che `DAODAN_SHARED_DIR` sposta e che ogni agente locale con strumenti sui file può scrivere: «si approva solo dalla GUI» è una proprietà dell'interfaccia, non del sistema (collocazione: ZO-7). Aperto da G14: nomi di pacchetti privati verso i registri pubblici (dependency confusion). *Raccomandazione:* ricontrollare l'indirizzo a ogni connessione e rifiutare privati, loopback e link-local salvo approvazione dell'indirizzo; dichiarare il modello di minaccia sugli agenti locali (approvazioni scritte solo dalla GUI e verificate, o una frase che escluda la minaccia); una regola per i pacchetti con ambito privato.

**design-1-9. DNS e motori diversi: il confine è provato su un motore solo.** r. 511, 515, 522; piano r. 101; `container.py` (nessuna gestione DNS; `KIRI_VERSION = "0.2.0"`, pacchetti arm64 r. 290-295), `premap/noir.py:10` (solo `linux-x86_64`). Un proxy CONNECT non vede le query DNS del container; il loro inoltro su una rete `--internal` dipende dal resolver del motore e dalla versione. La prova del piano è su Docker in una VM Modal; gli utenti Windows usano Kiri 0.2.0. Su arm64 `find_entry_points` perde Noir in silenzio, contro il Principio 7. *Raccomandazione:* scrivere il meccanismo DNS (nessun resolver o uno che risponde solo al proxy); sonda di uscita per ogni motore supportato; lacuna dichiarata su arm64 e ripiego se mancano fork, Noir o Kiri.

**design-1-10. L'approvazione costa una corsa per host, e senza schermo non si approva.** r. 518-521; `daodan/data/package-managers.json` (per Gradle solo `plugins.gradle.org` e `plugins-artifacts.gradle.org`, nessun host Google). Una build Gradle che incontra in serie wrapper e `google()` paga una corsa intera per host. Con solo MCP o CLI, in CI e nelle corse `corpus` su Modal ogni host non canonico diventa `approval_required` senza modo di predisporre le approvazioni: dopo `T0.C` il confronto «zero perdite non spiegate» vedrà perdite. *Raccomandazione:* raccogliere i rifiuti di una corsa, chiedere e rilanciare una volta; dire come si preparano le approvazioni senza GUI (coerente con design-1-8), o che quelle lacune sono accettate e come i benchmark le contano.

**design-1-11. Il `.daodan` scambiato con altri non ha un confine di fiducia.** r. 99, 191, 199-207, 525; DDL `analyses.config_json`, `source_snapshots.repository_uri`, `revisions.author`, `technical_records.payload_json`; guida SQLite sui database non fidati. In entrata: «lo schema atteso» non dice come si confronta (trigger e viste in più, `trusted_schema`, modalità difensiva); non è detto se la rianalisi di un file ricevuto riusa il suo `config_json`; `author` è dichiarato e modificabile, la cronologia non è una traccia autenticata. In uscita: `payload_json`, `repository_uri` (può contenere credenziali) e i locatori escono dalla macchina; Secretlint (r. 525) copre solo `app.py` e `mcp_server.py`. *Raccomandazione:* sottosezione «File ricevuto» (modalità difensiva, rifiuto di oggetti non previsti, configurazione sempre locale); cronologia informativa; Secretlint sul salvataggio o sulla condivisione.

**design-1-12. L'ID del catalogo non è stabile, ma la spec lo usa come chiave d'identità.** r. 226, DDL `nodes.catalog_id` (r. 354). In `T0.A.1` `avro-cncf` è stato fuso in `avro` (`service-registry.json:2631`) e `registry_build.py` non ha alias. Dopo un aggiornamento del catalogo il nodo cambia `object_id`; edit e frecce restano sull'ID vecchio o diventano conflitti; un file vecchio perde tipo e logo. *Raccomandazione:* id ritirati come alias (`replaced_by`) con controllo in `registry_build.check`; la riconciliazione legge gli alias.

**design-1-13. Punti del formato non definiti: campo degli edit, identità degli archi, vocabolari.** r. 231, 242; DDL r. 332, 344-350, 362-363; `daodan/core/system_map.py:57-60`. Manca la proiezione JSON di un oggetto relazionale per `field_path` (chiavi, `attributes_json`, «dettagli del flusso»). Il «sito di origine» degli archi non è definito: se è una riga, una riga inserita sopra cambia l'identità. Specie chiuse con `CHECK`, ma `grade`, `edges.kind` e `provenance` liberi; il codice confronta i nomi dopo NFKD, il `CHECK` i byte, quindi `funzionalità` in NFD è rifiutata. *Raccomandazione:* una proiezione JSON per tipo di oggetto; sito di origine indipendente dalla riga (simbolo e occorrenza); stesso criterio di chiusura per specie, gradi e provenienze; NFC obbligatoria per chi scrive.

**design-1-14. Ogni rianalisi apre una versione di tutto, e il file cresce senza limite.** r. 201, 205, 214, 219; DDL `evidence.analysis_id NOT NULL` (r. 428), «Identities are never recycled». Sovrapposto a IC-N2 e ZO-2. In più: il costo cresce con le corse, non con ciò che cambia (anche `identity` porta lo SHA-256 del file), contro «versioni dei soli oggetti cambiati» e r. 165; nessuna compattazione. *Raccomandazione:* chiave di contenuto per le prove con riuso della riga; stima della dimensione per rianalisi; regola di compattazione, o la dichiarazione che il file cresce per sempre.

**design-1-15. Specie, tipo e categoria si confondono sui nodi del catalogo.** r. 105-113, 171, 175-179; `registry_build.py:119-120` (il `type` di una voce è uno di `flows.NODE_TYPES`, le stesse parole delle specie). PostgreSQL ha specie `tecnologia` e tipo `database`, o specie `database`? Le nature cambiano (codice o fisico). Una `tecnologia` di categoria `service` non ha natura (r. 113); «un servizio esterno è logico e fisico» non dice la specie; la natura «si ricava da specie e posizione» (r. 106) ma la r. 113 usa la categoria. *Raccomandazione:* tabella «voce del catalogo (categoria, tipo) → specie e natura»; la natura si ricava anche dalla categoria.

**design-1-16. Rischi del file SQLite come documento dell'utente.** r. 191, 235; DDL senza `journal_mode`. Un file in WAL copiato col gestore dei file o sincronizzato (OneDrive, Dropbox) perde i commit ancora in `-wal`; sui filesystem di rete il blocco non è affidabile e WAL non funziona; il controllo ottimistico della testa (r. 235) chiede `BEGIN IMMEDIATE`, altrimenti `SQLITE_BUSY`. *Raccomandazione:* fissare il giornale (DELETE, o WAL con checkpoint alla chiusura); scrivere il limite dei filesystem di rete e sincronizzati; scrivere `BEGIN IMMEDIATE`.

### Nit

- **design-1-17.** r. 502: «mancano `.h`» è superato; `.h` è letto da `languages/header.py`, collegato in `languages/__init__.py:34, 109-115`, fuori dall'anagrafica: va scritto dove sta la regola.
- **design-1-18.** r. 77 e 486: «qualche GB» e «tempo reale» non sono misurabili.
- **design-1-19.** r. 107: non è detto come `concrete`, `logical`, `virtual` corrispondono a concreto e astratto.
- **design-1-20.** r. 85: «archivio di Daodan» non è definito; «Termini» definisce solo la «Cartella condivisa».
- **design-1-21.** r. 85, 110, DDL r. 352: «confermato» è stato di un nodo e grado di un comando; «grado» vale per frecce e comandi.
- **design-1-22.** r. 191: «SQLite 3.38 o successivo»; `STRICT` chiede la 3.37 e le distribuzioni con 3.37.2 hanno già JSON1: giustificare o abbassare.

---

## Revisore Style

0 Blocker, 8 Major, 12 Nit. Sulle righe `[deciso]` critica solo la forma, mai la decisione. Per ogni Major indica le due letture che portano a costruire cose diverse. **Nota di isolamento:** ha usato una volta Bash (`wc -l`, `ls`) sui documenti di contesto, fuori dal vincolo; una ricerca gli ha mostrato righe di questa cartella di review, ma dichiara che nessun rilievo ne dipende.

### Major

**style-1-1. Vocabolario dello stato fuori dalla legenda; tracciamento del piano dentro il contratto.** Legenda r. 5; varianti a r. 53, 71, 74, 75, 77, 99, 148, 156, 163, 165, 182, 183, 187, 490, 504, 511–514; frasi senza marcatore a r. 178–181, 523–524. La legenda copre quattro valori e solo la colonna «Stato»; «Proposta» non compare altrove; fuori dalle colonne ci sono «non ancora nel codice», «da implementare nell'app», «Nell'esploratore sì; l'app oggi non le conta», «Da completare…», «attiva in T3», «tracciato nel piano», «Parziale: non misurato». Le frasi senza marcatore non dicono se valgono già: r. 511 («isola sempre») è al presente, r. 512–513 dicono che `--cap-drop` e `--user` mancano. **Caso decisivo r. 512:** non si capisce fin dove arriva «da creare»; lettura A, tutti i controlli sono da creare; lettura B, sono attivi, compresi gli script spenti, mentre il piano (r. 211) dice che `node_prepare` lancia l'installazione con gli script. Copie dello stesso stato fra spec (r. 77, 513, 514) e piano (r. 66, 166, 211). Identificativi di tranche a volte senza backtick. *Proposta:* un marcatore per frase normativa da una legenda completa (senza «Proposta»); un marcatore per ogni controllo di r. 512 e «deve isolare» a r. 511; la tranche solo come riferimento; ogni «Nel codice» con il suo file.

**style-1-2. Parole con più significati.** «Passo» (step r. 9, 20; azione del piano r. 81, 518; passo di un flusso r. 155–156, 204, 241, 257), accanto a «step» e «azione». **Caso decisivo r. 20** («Senza container il passo è una lacuna»): lettura «step», tutto `find_entry_points` è una lacuna; lettura «azione», lo step prosegue con tree-sitter come dice r. 56. *Proposta:* «step» per la pipeline, «azione» per il piano, «passo» per i flussi. Inoltre: «piano» (oggetto di esecuzione e `refactoring.md`, entrambi in r. 514); «prova» (dato `evidence` e test; più «evidenza»); «interfaccia» (UI di Daodan, UI del progetto, headless); «controllo» (UI, coerenza, preventivi, filtro del proxy); «sito» (di chiamata e web); «archivio» (i due archivi dei nodi e l'«archivio di Daodan» = cartella condivisa); «snapshot» (tabella, riferimento della lettura, lettura coerente); «registro» (libro mastro di Bank of Anthos e registri dei pacchetti).

**style-1-3. Più nomi per la stessa cosa.** Superfici della mappa: «GUI dell'app», «pagina HTML dinamica», «app», «esploratore», «la pagina», «la UI»; non si sa se esploratore e pagina sono la stessa, e da questo dipende in quante superfici si costruisce l'interruttore di r. 128. Legami: «arco», «freccia», «collegamento», «legame», «dipendenza»; «freccia «usa»» (r. 175) e «freccia `uses`» (r. 176): uno o due `kind`? `edges.kind` è libero, passano entrambe. `service-registry.json` è «anagrafica» e «catalogo» (`catalog_id`). Astrazione: «astratto», «sintetico», «macro-modulo»; il codice usa `logical` e `virtual`, mentre «logico» è anche una natura. Anglicismi accanto all'italiano (writer, resolver, runner, edit). Logo: «logo», «tessera», «pittogramma» (non definito).

**style-1-4. Gradi e stati: elenchi discordi, e uno aperto.** Gradi delle frecce in quattro versioni (r. 110, 147, 215 con «per esempio», `uncertain` r. 176); in SQL `grade` è libero (r. 363) mentre i criteri di r. 138 e il riassunto «per grado» di r. 146 contano su un insieme preciso: tre o quattro valori cambiano vincolo e raggruppamento. «Grado» è anche il livello di un comando (r. 83–89), che condivide `confermato` con lo stato del nodo e `dichiarato` con i gradi. «Stato» ha tre sensi (nodo, azione, implementazione). *Proposta:* elenco chiuso dei gradi in un punto solo; via «per esempio»; un nome distinto per il livello del comando.

**style-1-5. Requisiti e criteri con termini non misurabili.** Soglia del consenso: «qualche GB» (r. 77) e «download pesante» (r. 484); da qui dipende se 500 MB chiedono consenso. Spostamento dei nodi: «non più del necessario» (r. 135), «si misura… e si mantiene il riferimento visivo» (r. 138) senza soglia. «Più figli di quanti la vista ne regge» (r. 164), «un progetto grande» (r. 165), «nodi piccoli» (r. 142). r. 56: chi decide «dove serve» la chiave con contesto, mount e router; «diagnostica» non definita. *Proposta:* un numero, un rimando, o «scelta aperta» in chiaro.

**style-1-6. Affermazioni sul comportamento attuale oltre la prova.** r. 173 spiega il `full` di un servizio o strumento con «il grafo ha il suo nodo» (come la docstring di `daodan/core/registry_build.py:86-93`), ma r. 175 dice che oggi uno strumento non compare: il `full` degli strumenti è corretto oggi, o `support` va cambiato fino a `T2.C`? r. 57 «nessun campo nuovo» è perentorio, il piano (r. 176) lo lega a una misura; la corrispondenza colloca `ignoto` ma non `risolto` e `ambiguo`. *Proposta (solo forma):* «avrà il suo nodo (oggi solo le voci `service`)»; «nessun campo nuovo finché la misura di `T2.A` non trova falsi archi»; completare la corrispondenza o dire che manca.

**style-1-7. Assoluti smentiti dallo stesso testo.** r. 69 («qualsiasi tipo di applicazione», «lo dice come lacuna») contro r. 75 («macOS e iOS restano fuori perimetro»): lacuna o silenzio? r. 110 («sempre con il file che lo prova») contro r. 107 (un nodo astratto non ha una cosa da indicare) e r. 205, 429 (una prova può essere `artifact`); stessa formula a r. 124 e 175. Da qui dipende se chi scrive rifiuta un nodo astratto senza prova. *Proposta:* «qualsiasi applicazione del perimetro» e che cosa emette quella fuori; «con la sua prova (`evidence`)», e se è obbligatoria per i nodi astratti.

**style-1-8. r. 99 ripete «File di progetto» nella sezione sbagliata, con due regole che esistono solo lì.** r. 99 contro r. 185–243. Le parti coperte coincidono con r. 211–213 e 242, ma due regole stanno solo a r. 99: il file ricevuto da altri (cronologia mostrata dall'app) e «L'albero di contenimento e gli archi diretti hanno ruoli distinti», che non dice quali. `T2.E` rimanda a `#file-di-progetto`, quindi chi implementa può perdere la prima. *Proposta:* spostare le due regole in «File di progetto»; r. 99 ridotta a una frase con il rimando.

### Nit

- **style-1-9. Il problema** (r. 9, 11, solo forma): «troppo codice», «troppe spec», «inefficienze», «punti chiari» non dicono quale difetto né quanto; sinonimi in coppia; la storia dei documenti non è un fatto del sistema (spostarla nel backlog); usare i difetti già citati nel piano (`Stack` dopo `Scan`, sorgenti che cercano da sé il proprio file).
- **style-1-10. Doppioni:** Principio 6 caso del 7 senza «rimedio»; percorsi di Noir in due forme (r. 44, 532; anche r. 38, 513); Kiri definito due volte; «fisico» ripetuto (r. 106, 113); natura «da specie e posizione» (r. 106) contro «…e contenuto dei gruppi» (r. 215); nomi dei profili diversi fra r. 157 e 257; «solo database vuoto» tre volte; r. 161 ripete r. 93.
- **style-1-11. Termini senza definizione:** frontiere, GitNexus, CMGV, «punti citati», «servizio» come calcolatore della vista, confronto a tre vie, «fresca», eccezione apt, Modal, Sigrid, Imago; «variante» e «profilo» usati prima di essere definiti; «elenco di Wikipedia» senza link; rimandi vaghi (r. 215, 229); «cartella condivisa» definita solo per gli strumenti; glossario non alfabetico.
- **style-1-12. Frasi ellittiche:** r. 39, 71, 77, 88, 120, 179, 481, 518.
- **style-1-13. Riempitivi:** r. 17, 56, 57, 106, 107, 111, 136, 173, 483.
- **style-1-14. Conti ed elenchi:** r. 485 «tre fatti» che sono quattro; r. 486 elenco chiuso mancante e «tempo reale»; r. 492 parole diverse dal piano; r. 34 e 36 senza fonte; r. 113 «cioè» ambiguo.
- **style-1-15. Caveat e assoluti minori:** r. 130 «non chiede calcoli nuovi» (togliere); r. 165; r. 171 «non verificati a campione» senza conseguenza; r. 502 `.h` (in `languages/header.py`, `daodan/core/languages/__init__.py:34,115`); r. 514 cita testi non presenti; r. 270 prova senza percorso; titolo «Nessun limite» con tre tetti dentro.
- **style-1-16. Tre formati con nomi che si confondono** (r. 191, 193, 266): «schema 2», «v1», «vecchio esempio» con `v2/graph.sqlite`; il terzo senza percorso; usare «schema 1» e «schema 2».
- **style-1-17. Registro misto:** prima persona (r. 9), infiniti (r. 193), imperativo (r. 270).
- **style-1-18. r. 128** (solo forma): «estrapolando» vuol dire dedurre oltre i dati; modalità nominate prima di essere definite; «si supportano» calco dall'inglese.
- **style-1-19. Regola fuori posto:** le varianti (r. 183) stanno sotto «Le tecnologie come nodi»; spostarle in «Seguire un flusso».
- **style-1-20. Forma:** apostrofi curvi e dritti; valori del DDL metà in italiano e metà in inglese; specie in backtick solo a r. 181.

---

## Convergenze dello stadio 7 (e con gli stadi 5–6)

*Conteggi corretti dopo lo stadio 8: il revisore design ha letto lo stadio 5, quindi non è indipendente da ZO e IC.*

| Tema | Rilievi | Revisori indipendenti |
|---|---|---|
| Mancano le alternative considerate | structural-1-1 (Blocker), design-1-1 (Blocker) | 2 |
| Chi produce flussi, varianti, profili | design-1-5; ZO-5, IC-3, CO-1 | 3 |
| Mancano non obiettivi, rischi, criteri di successo | structural-1-2, 1-3; design-1-2 | 2 |
| Tabella degli step senza «se fallisce»; preparazione senza padrone | structural-1-4; design-1-3; CO-3, ZO-N4, IC-N1 | 4 |
| Notazione dello stato incoerente | structural-1-5; style-1-1 | 2 |
| Termini con più sensi e sinonimi | structural-1-10; style-1-2, 1-3; CO-11 | 3 |
| Gradi senza elenco chiuso; archi senza sezione | structural-1-11; style-1-4; design-1-13 | 3 |
| Prove del formato senza percorso; formati confusi | structural-1-9; style-1-16; ZO-3, CO-6 | 4 |
| Ogni rianalisi versiona tutto | design-1-14; IC-N2, ZO-2 | 2 |
| r. 99 ripete «File di progetto» | structural-1-8; style-1-8 | 2 |
| `recognize_stack` rigira dopo `find_modules` | design-1-4; CO-4 | 2 |

**Nuovi solo in questo stadio (un revisore):** design-1-6 (piano meno del codice), 1-7 (unione HTTP perde il servizio), 1-8 (rebinding DNS e archivio approvazioni scrivibile), 1-9 (DNS e motori, Noir solo x86_64), 1-10 (una corsa per host, nessuna approvazione senza schermo), 1-11 (confine di fiducia del `.daodan`), 1-12 (ID del catalogo non stabile), 1-15 (specie e tipo sui nodi del catalogo), 1-16 (WAL e filesystem); style-1-6, 1-7 (assoluti smentiti dal testo).

**Totale stadio 7:** 2 Blocker, 33 Major, 24 Nit.
