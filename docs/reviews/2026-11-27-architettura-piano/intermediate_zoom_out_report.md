# Stadio 8 — Intermediate Zoom Out

- **Bersaglio:** `docs/specs/architettura.md` e `docs/plans/refactoring.md`, interi, commit `a4360b01b`, non modificati dopo gli stadi 5–7.
- **Contesto:** i report degli stadi 5, 6, 7 di questa cartella; `docs/backlog.md`; i due report del 25 novembre.
- **Standard:** `zoom-out-standard.md`.
- **Revisore:** Zoom Out (completato).
- **Isolamento ottenuto:** subagente nuovo senza la conversazione; ha letto i report precedenti per istruzione e riceve `CLAUDE.md` e `AGENTS.md`. Solo Read, Grep, Glob; nessun comando.
- **Esito:** 1 Blocker, 10 Major, 2 Nit. Nessun rilievo blocca `T0.A`.

---

## Che cosa aggiungono gli stadi 6 e 7, se accolti tutti

Conto dai report: 3 H2 nuove («Alternative», «Obiettivi e non obiettivi», «Rischi e mitigazioni»); 3 H3 nuove («Migrazione e importazione», «Archi», «File ricevuto»); 2 colonne nella tabella degli step; 3 tabelle nuove (alternative, rischi, voce del catalogo → specie e natura); 10 voci in «Termini» più 18 termini segnalati non definiti; 17 regole nuove sul formato (design-1-11…16), 5 sul piano (design-1-6), 8 sulla rete (design-1-8…10).

Solo tre cose toccano il contratto degli step o il modello, cioè «Il problema»: la colonna «Se fallisce», una definizione di variante e profilo, un elenco chiuso dei gradi. Il resto ingrandisce il documento senza cambiare l'ordine dei passi né i padroni dei fatti.

## Classi dei rilievi degli stadi 6 e 7

| Classe | Rilievi | Che cosa fare |
|---|---|---|
| Dipendono da una decisione aperta dello stadio 5 | CO-6, structural-1-6, -8, -9, style-1-8, -16, design-1-11, -12, -13, -14, -16 (formato: ZO-1, ZO-3, ZO-9); design-1-8, -9 (scelta del proxy: ZO-6 = IC-1) | Sospenderli |
| Già detti dal codice, da una pagina generata o da un benchmark | design-1-2, -3 («Gira su»), -6 (`needs`, `blocked`), -7, -16; CO-1 (metà sui flussi), CO-7, CO-8; le ragioni di structural-1-1 e design-1-1 | Un rimando, non testo nuovo |
| Portano dentro voci del backlog o sezioni che chiede lo standard, non «Il problema» | structural-1-1, -2, -3; design-1-1, -2 (H2); design-1-6 (annullata, ripresa, scrittore); limiti G10; design-1-8 (pacchetti privati); design-1-10 (approvare senza GUI); style-1-5; CO-10 oltre `AGENTS.md` | Declinarli |
| Tolgono parole | structural-1-5, style-1-1, style-1-2, -3, -10, structural-1-7, CO-9, CO-12; CO-5, CO-11, design-1-15 (per sottrazione, con domanda al proprietario) | Accoglierli |
| Due letture costruirebbero cose diverse, in una parte che resta | CO-1, CO-2, CO-3, CO-4, design-1-4, -5, -7, structural-1-4, style-1-2 (r. 20), style-1-4, design-1-9 (Noir) | Accoglierli nella forma più piccola |

**Convergenze da ricontare.** Il revisore design ha letto lo stadio 5, quindi non è indipendente da ZO e IC: «chi produce flussi, varianti, profili» ha 3 revisori indipendenti, non 4; «tabella degli step, preparazione» 4, non 5; «ogni rianalisi versiona tutto» 2, non 3. (Corretto anche in `critic_report.md`.)

---

## Rilievi

**ZI-1 (Blocker per la fase di risoluzione; non blocca `T0.A`). L'ordine di risoluzione: undici rilievi sul formato vengono prima della decisione che li rende utili.**
- *Ambito:* spec «File di progetto» (r. 185–477) e r. 99; piano riga `T2.E` (r. 27), punto 7 di T2 (r. 187), Cancello T2.E (r. 200); CO-6, structural-1-6, -8, -9, style-1-8, -16, design-1-11, -12, -13, -14, -16.
- *Motivazione:* ZO-1 (padrone dei fatti confermati a mano), ZO-3 (togliere migrazione v1→v2 e importazione ZIP) e ZO-9 («File di progetto» appartiene a questo refactoring?) sono aperti. Gli undici rilievi aggiungono 2 H3 e 17 regole su quelle circa 290 righe: risolti prima, sarebbero da rifare se la sezione si riduce o si sposta. `T2.E` aspetta otto tranche. Nel codice non c'è lettore né scrittore del formato; `application_id` compare solo in `daodan/core/snapshot_store.py:365` e `daodan/core/card_store.py:40`, con identificativi propri (`0x444D4150`, `0x44434152`).
- *Proposta minima:* sospendere gli undici rilievi e far decidere prima ZO-1, ZO-3, ZO-9. Spostare il DDL è una domanda al proprietario: è `[deciso]` come normativo (r. 187) e `d4737a260` ha riunito apposta l'SQL nella spec. design-1-16 e la parte di design-1-11 sull'apertura si chiudono con il riuso, in una frase («si apre e si scrive come `snapshot_store` e `card_store`»: `journal_mode=DELETE` in `snapshot_store.py:364`; `card_store.py:109-132` controlla `application_id` e `user_version`, apre in sola lettura salvo scrittura, usa `BEGIN IMMEDIATE`). Il riuso non copre oggetti di schema inattesi né la modalità difensiva: restano per `T2.E`.

**ZI-2 (Major). Le sezioni nuove le chiede lo standard, non il problema.**
- *Ambito:* structural-1-1, -2, -3, -10; design-1-1, -2; CO-7, CO-8, CO-10.
- *Motivazione:* le tre H2 riassumono cose che stanno altrove; `AGENTS.md` vieta la documentazione che ripete e i riepiloghi ridondanti, e per la soluzione pronta scartata chiede il motivo «accanto», la forma che la spec già usa (r. 53–57, 512, 514, 522). design-1-1 propone opzioni nuove (Docker Desktop o Podman machine al posto di Kiri, sei step), non note mancanti; Kiri è una release di terzi (`daodan/core/container.py:290-296`, `libracoder/kiri` 0.2.0).
- *Proposta minima:* alternative come rimando in linea dove il motivo esiste (`benchmarks/{django,fastapi,flask,express}-routes/README.md`, `benchmarks/project-model/REPORT.md`), nota in linea solo dove manca (storia del `.daodan`, ZO-1; proxy di `T0.C`, ZO-6 = IC-1); non obiettivi: bastano il rimando al backlog (r. 3) e macOS/iOS; rischi: declinare; termini: rimando ad `AGENTS.md` (Sigrid, Imago, le due pagine `viewer/src` e `viewer/app`, la regola dell'host), che chiude CO-8 e buona parte di CO-7 e CO-10. *Domanda al proprietario:* «esploratore» e «pagina HTML dinamica» sono la mappa? Nuove voci in «Termini» solo variante, profilo e passo.

**ZI-3 (Major). Il contratto del piano (design-1-6): metà c'è nel codice, metà è nel backlog.**
- *Ambito:* spec r. 479–486.
- *Motivazione:* `daodan/core/pipeline/plan.py:10-17` ha `needs` e `blocked` («A node whose need failed does not start, and says which»). Annullamento, ripresa, scrittore con blocco e concorrenza GUI/MCP/CLI sono differiti nel backlog §3 (r. 27).
- *Proposta minima:* una frase («un'azione aspetta i suoi `needs`; un'azione ferma blocca solo ciò che ne ha bisogno», chiude anche I3); togliere «da elenco chiuso» (r. 486); declinare il resto.

**ZI-4 (Major). Rete: il nucleo è un criterio della prova del proxy, non un meccanismo nuovo.**
- *Ambito:* spec r. 515–522; piano `T0.C` (r. 98–103), `T3.A`.1 (r. 209); design-1-8, -9.
- *Motivazione:* il ricontrollo dell'indirizzo risolto è un criterio di scelta dello strumento; oggi `PROXY_SCRIPT` confronta nome e porta 443 e si collega per nome (`container.py:274-278`). Scriverlo a mano in `T0.C` prima della prova ripete il rovesciamento di ZO-6 = IC-1. La sonda per motore è lavoro nuovo. Noir solo `linux-x86_64` (`daodan/core/premap/noir.py:10`): su arm64 si perde in silenzio, contro il Principio 7.
- *Proposta minima:* una riga fra i criteri di r. 522 e `T3.A`.1 (rifiutare loopback, link-local e privati dopo la risoluzione, salvo approvazione dell'indirizzo); una lacuna «confine provato su Docker, non su Kiri»; una lacuna per Noir fuori da x86_64; pacchetti privati e minaccia degli agenti locali come domande al proprietario, nessuna sezione.

**ZI-5 (Major). Modello di nodi e archi: due riduzioni.**
- *Ambito:* spec r. 105–113 («Tipo» `[deciso]` r. 111), 171–176, DDL `nodes` (r. 340–356), gradi r. 110, 146–147, 176, 215, `edges.grade` (r. 363); CO-11, design-1-15, style-1-3, -4, structural-1-11.
- *Motivazione:* `daodan/core/registry_build.py:119-120` vuole il `type` di ogni voce fra `flows.NODE_TYPES` (`flows.py:109-110`), parole delle specie; il DDL non ha una colonna di tipo: per un nodo di catalogo il tipo è già una specie. Quattro elenchi parziali dei gradi, uno «per esempio», `grade` libero, mentre r. 138 e 146 contano su un insieme preciso.
- *Proposta minima:* *domanda al proprietario, senza riaprire il `[deciso]`:* il tipo della voce è la specie del nodo? Se sì, «Tipo» diventa una frase e la tabella di design-1-15 non serve. Un solo elenco chiuso dei gradi, spostato e non aggiunto; H3 «Archi» solo se sostituisce le menzioni sparse; un nome diverso per il «grado» di un comando (r. 83–89).

**ZI-6 (Major). Consenso ai download: togliere invece di misurare.**
- *Ambito:* spec r. 77, 484–486; piano punto 16 di T1 (r. 146); CO-5, design-1-18, style-1-5, -14.
- *Motivazione:* i download con licenza o di molti GB sono quelli delle superfici differite (backlog r. 37–38: Android circa 4 GB con licenza, Wine circa 500 MB, VM Windows 25–32 GB). Nel perimetro attivo ogni download passa da un host, e l'approvazione degli host è già un consenso. Nessuno ha misurato i download attivi.
- *Proposta minima (domanda al proprietario):* nel contratto attivo un solo consenso, sull'host; licenza e peso nel backlog con le loro superfici; «quanto pesa» esce dai fatti di un'azione (r. 485); `approval_required` torna a un significato. *Compromesso:* un download grande da un registro in whitelist non chiederebbe nulla.

**ZI-7 (Major, essenziale). Chi produce flussi, varianti e profili.**
- *Ambito:* spec r. 97, 155–157, 183, 203, 257, DDL `variants`, `variant_endpoints` (r. 376–391); piano Cancello T2 (r. 196); CO-1, CO-2, design-1-5, ZO-5, IC-3.
- *Motivazione:* i flussi e i nodi con nome li propone l'agente `plugins/codebase-map/roles/system-mapper.md:4` e li verifica `daodan/core/system_map.py`, che legge anche `codebase-system-map.json` (r. 591–618): non serve un componente nuovo. Le varianti le fa identificare al modello `benchmarks/system-map/README.md:266`, ma in un braccio di confronto «ancora da eseguire» (r. 259): un produttore non c'è. Profili di un flusso: non trovati in `system_map.py`, `flows.py`, `system_levels.py`, `app_view.py`, ruoli e contratti di `plugins/codebase-map` (altri file con `variant`/`profile` non aperti, salvo `premap/cmake.py` e `premap/compose.py`, che parlano di profili di Conan e Compose). Il caso Bank of Anthos del Cancello T2 chiede due profili che nessuna tranche costruisce.
- *Proposta minima:* un paragrafo fuori dagli otto step, «La mappa di sistema» (proposta del mapper via MCP, verifica di `system_map`, file dichiarato); una sola definizione di variante; il produttore dei profili in una tranche, oppure il caso nel cancello della tranche che li consegna. *Domanda al proprietario (inferenza):* se il profilo è una configurazione di avvio, è un fatto del modello di build, che già legge i profili di Compose (`premap/compose.py:91-92`) e Conan (`premap/cmake.py:152-192`)?

**ZI-8 (Major, essenziale). La tabella degli step: tre correzioni piccole, che sono il problema dichiarato.**
- *Ambito:* spec r. 20, 27–36, 56, 512; piano punto 9 di T1 e r. 156; CO-3, CO-4, design-1-3, -4, structural-1-4, style-1-2, ZO-N4, IC-N1.
- *Motivazione:* secondo giro di `recognize_stack` verificato (`stack_analyser.run(..., declarations=...)`, `daodan/core/stack_analyser.py:172-183`; `technologies.merge`, `technologies.py:165`), non mostrato in tabella; «toolchain» e «servizi» scritti dalle righe 3 e 4. Preparazione chiesta da `find_entry_points` e `link_calls`, senza padrone né momento; «una per analisi» (r. 512) non è nel codice (per corsa, `container.py:17-26`; solo Node per analisi, `node_preparation.py:1`). Guasto scritto solo per `find_entry_points`; r. 20 ha due letture, r. 56 dice che è l'azione.
- *Proposta minima:* dipendenza esplicita del secondo giro e un padrone per toolchain e servizi; preparazione al lanciatore dei servizi comuni, dopo `find_modules`; «una per analisi» marcata come proposta finché una misura non ne mostra il costo; una sola colonna «Se fallisce o senza container» che dice anche che cosa resta sull'host; nessuna colonna «Gira su» (`viewer/pipeline/tree.ts:66,86` mostra «Dove gira», ma per l'ordine di oggi); la regola «step» / «azione» / «passo».

**ZI-9 (Major, essenziale nella forma più piccola). Unione HTTP: la spec dice meno del codice.**
- *Ambito:* spec r. 61–65; design-1-7.
- *Motivazione:* `daodan/core/flows.py:55-59` chiede stesso servizio, stesso metodo, schema compatibile; vince la rotta più letterale, il pareggio è incerto con lacuna. Copiare tutta la regola (servizio `*` di Noir, catch-all) sarebbe dettaglio fuori livello.
- *Proposta minima:* «stesso servizio, metodo e schema del percorso; un pareggio è un legame incerto, con lacuna», più un rimando a `flows.py`.

**ZI-10 (Major). Notazione dello stato: una forma, non un marcatore per frase.**
- *Ambito:* legenda (r. 5) e note di stato; structural-1-5, style-1-1, CO-12.
- *Motivazione:* `AGENTS.md` vuole distinti attuale, proposta e lacuna, quindi lo stato resta; ma un marcatore per frase (style-1-1) è troppo, e i codici di tranche nella spec si disallineano a ogni taglio del piano.
- *Proposta minima:* una sola forma per sezione («Oggi: nel codice | parziale | da creare», con il file), nessun codice di tranche nella spec (la corrispondenza la tiene il piano); togliere «Proposta» dalla legenda. Chiude anche il caso di r. 512.

**ZI-11 (Major). design-1-10: la premessa su `corpus` non regge, ma resta una domanda sul Cancello T0.C.**
- *Ambito:* piano Cancello T0.C (r. 107), M7 (r. 165); spec r. 520 (`[deciso]`); design-1-8, -10.
- *Motivazione:* `modal.yml:9, 69-76` con `run=corpus` fa girare solo lo step dello stack tramite `benchmarks/project-model/modal_stack.py`, che non esegue codice del progetto (intestazione r. 4): nessuna preparazione dietro `PROXY_SCRIPT`, quindi le perdite di design-1-10 non sono sostenute. Resta il caso vero: il Cancello T0.C chiede «dopo il sì il passo riesce», ma nessun documento dice come un sì arriva a una corsa senza schermo. design-1-8 (approvazioni solo dalla GUI, verificate) e design-1-10 (prepararle senza GUI) vanno in versi opposti, e la seconda contrasta r. 520.
- *Proposta minima (domanda al proprietario):* il sì del cancello lo dà la prova del popup nel workflow Viewer, o un test che scrive l'approvazione con lo stesso modulo della GUI? Da qui dipende se serve proteggere l'archivio. Chiedere insieme tutti gli host di una corsa: frase facoltativa nel punto 3 di `T0.C`.

**ZI-12 (Nit). Soglie: riusarle, non inventarle.** Spec r. 135, 164–166; piano Cancello T2 (r. 196). `benchmarks/codebase-explorer/README.md:56` ha già 2 s per il grafo e 100 ms per la selezione (oggi 4,6 s a 300 nodi); il Cancello T2 si limita a «registrare»; i tetti di tempo per stage sono nel backlog §5 (r. 45). *Proposta:* nel Cancello T2 misurare contro quegli obiettivi; dove non c'è misura scrivere «scelta aperta»; declinare G10.

**ZI-13 (Nit). Spostamenti che tolgono righe: accoglierli.** r. 99 diventa una frase con rimando (le due regole uniche in «File di progetto»); Noir e Kiri definiti una volta; un nome per concetto (arco o freccia; anagrafica, catalogo o registro; «usa» o `uses`); criteri di accettazione come elenco numerato con ancore; la corrispondenza degli step come rimando a `docs/pipeline/` invece di `T0.B.3` a mano. Nel piano: una riga di legenda dei codici; correggere la doppia lettura di `T0.7`; Regola 5 contro la base di `T0.A.2` (4630 / 78), non `modal_pytest.py:18`; `T0.A.4` senza la citazione di `test_codebase_map_app.py`, già chiusa a r. 56.

---

## Che cosa resta di essenziale

1. **Chi fa che cosa:** il produttore di flussi, varianti e profili, e una sola definizione di variante (ZI-7).
2. **L'ordine dei passi:** padrone e momento della preparazione; secondo giro di `recognize_stack` (ZI-8).
3. **Quando e come:** che cosa fa ogni step se fallisce o manca il container; a r. 20 il passo è l'azione (ZI-8).
4. **Incongruenze:** la regola di unione HTTP come la dice `flows.py` (ZI-9); un solo elenco dei gradi (ZI-5).
5. **Un padrone per fatto:** chi possiede i fatti confermati a mano (ZO-1), condizione anche di ZI-1.

Aperti dallo stadio 5 e non toccati da 6 e 7: ZO-6 = IC-1 (ordine del proxy fra `T0.C` e `T3.A`), IC-2 (`run_and_observe` aspetta `link_calls`), ZO-8 (calcolo delle viste dentro `assemble_graph`).

## Tranche aperta

Nessun rilievo degli stadi 6 e 7 blocca `T0.A` (`T0.A.3` e `T0.A.4` sono misure e verbali). La toccano solo due correzioni di testo di ZI-13: il riferimento della Regola 5 e la citazione superata in `T0.A.4`.
