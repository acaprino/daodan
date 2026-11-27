# Stadio 6 — Comprehension Test

- **Bersaglio:** `docs/specs/architettura.md` (FeatureRange, tutto il file) e `docs/plans/refactoring.md` (DetailedRange, tutto il file), commit `a4360b01b`.
- **Contesto:** nessuno; il revisore ha letto solo i due file, senza codice né altri documenti. Nessuno standard applicato.
- **Revisore:** Comprehension (completato).
- **Isolamento ottenuto:** subagente nuovo, senza la conversazione; riceve comunque `CLAUDE.md`, `AGENTS.md` e gli hook di sessione. Solo lettura per istruzione.
- **Esito:** 1 Blocker, 10 Major, 1 Nit.

---

## What this proposes

(Questa frase è un'inferenza, perché nessuno dei due file dice che cos'è Daodan: dal contenuto è uno strumento che analizza il codice di un progetto e ne costruisce una mappa navigabile.) La spec fissa lo stato di arrivo. C'è una pipeline di otto step con identificatori stabili, da `list_files` ad `assemble_graph`; ogni step ha una sola competenza e ogni fatto un solo padrone. La pipeline usa gli strumenti ufficiali di ogni linguaggio e framework, esegue il codice del progetto solo in un container e scrive come lacuna ciò che non riesce a fare. La spec definisce poi:

- la mappa: nodi con specie, natura, concreto o astratto, padre, posizione, provenienza e tipo; gruppi che si aprono e si chiudono sul posto; filtro per natura; frecce riassunte; flussi seguiti passo per passo attraverso i gruppi; nessun tetto al numero di nodi;
- un file di progetto `.daodan` in SQLite (schema 2), con revisioni, versioni a intervalli, edit manuali, conflitti e riconoscimento degli stessi nodi alla rianalisi;
- un piano unico condiviso da UI, MCP e CLI;
- un'uscita di rete dal container, permessa solo agli host in whitelist o approvati da una persona dalla GUI.

Il piano ci arriva in quattro traguardi:

- T0: baseline misurata e rete;
- T1: pipeline statica e piano unico;
- T2: collegamenti SCIP, vista statica, mappa sullo schermo e file `.daodan`;
- T3: isolamento del container, esecuzione osservata, verifica della mappa.

I traguardi sono divisi in tranche autonome, lavorate una alla volta e verificate su Modal, mai in locale.

## How the existing system works, per this document

Oggi la pipeline ha sei step (`Scan, Stack, Parse, Analyze, Dynamic, Union`). L'elenco dei file e la lettura del codice girano prima della pipeline, e lo stack si riconosce dopo `Scan`. La pre-mappa tiene insieme modello di build, rotte ed eventi, e le sue 35 sorgenti decidono da sé se applicarsi. I nodi stanno in due archivi separati, l'involucro del codice (`visual@1`) e la mappa di sistema (`system-map/v1`), e si uniscono solo un flusso alla volta. Sono nodi solo le tecnologie `service`; framework e librerie sono tessere del modulo.

Il container esegue senza rete. In preparazione, però, il proxy apre senza chiedere i registri, gli host fissi degli strumenti e quelli dichiarati dal progetto, e non usa `--cap-drop` né `--user`. Esistono già il piano (`pipeline/plan.py`), i registratori runtime `*_record.*` e le strutture del modello di evidenza. SQL e PL/SQL si leggono con espressioni regolari. La suite è verde su Modal allo SHA `44462b569` (4630 passati, 0 falliti), e la tranche aperta T0.A è a 3 passi su 5.

---

## Rilievi

**CO-1 (Blocker). Da dove vengono flussi, varianti e profili.**
*Ambito:* spec r. 27–36, 97, 157, 171, 203–204, 261; piano r. 25, 73, 88.
Non riesco a scrivere la frase «il flusso lo produce X». Nessuna riga della tabella degli otto step scrive flussi, varianti, passi o profili, eppure il file li conserva, e nell'esempio R1 è «l'analisi» a inserire il flusso F. I documenti danno tre risposte che non stanno insieme: il piano mette i «dati dei flussi» in `assemble_graph` (T2.C, r. 25); T0.B.2 elenca come causa a parte un «mapper», fatto girare con un «modello debole» (r. 73, 88); la spec dice che la mappa di sistema contiene «le cose con il nome che dà una persona» (r. 97). Non si sa da dove vengono i profili (`kubernetes-standard`, `ledger-monolith`): letti dalla configurazione, decisi da una persona o proposti da un modello. Un LLM compare solo in tre punti (principio 3, r. 17; Secretlint, r. 525; `by: model`, r. 171): un lettore nuovo non sa se Daodan usa un modello, per che cosa e in quale step.

**CO-2 (Major). «Variante».**
*Ambito:* spec r. 157, 183, 203, 257, DDL `variant_endpoints`; piano r. 221.
A r. 183 (e piano r. 221) due ingressi con lo stesso esito sono due varianti; a r. 157 e 257 le varianti sono i profili dello stesso flusso; a r. 203 e nel DDL una variante ha un profilo e un elenco ordinato di ingressi, quindi può averne più d'uno. Non si capisce se due ingressi con lo stesso esito, nello stesso profilo, sono una variante con due ingressi o due varianti.

**CO-3 (Major). Preparazione dell'ambiente.**
*Ambito:* spec r. 33, 34, 512; principio 2 (r. 16).
I pacchetti ripristinati vengono da `find_modules` (r. 33); `link_calls` chiede un «ambiente preparato» senza dire da chi (r. 34); «Servizi comuni» ne fa un servizio comune, una per analisi (r. 512). Non è detto chi possiede la preparazione né quando avviene rispetto agli otto step, visto che le toolchain le stabilisce `find_modules`. È l'ambiguità sull'ordine dei passi che «Il problema» (r. 9) vuole eliminare.

**CO-4 (Major). Ordine fra `recognize_stack` e `find_modules`.**
*Ambito:* spec r. 31–32, 39; piano r. 156.
La spec presenta un ordine a senso unico e «chi riconosce è uno solo»; il piano decide che, per i pacchetti noti solo a `find_modules`, «il fork si rilancia» e poi `technologies.merge`. È un ritorno dallo step 4 allo step 3 che la tabella non mostra: non si sa se `recognize_stack` gira una volta o due, né chi è il padrone delle tecnologie del secondo giro.

**CO-5 (Major). Consenso ai download pesanti.**
*Ambito:* spec r. 77, 484–486, 521; piano r. 146.
La spec chiede consenso per download con licenza o «di qualche GB» e vuole che ogni azione dica «quanto pesa»; il piano dice che il peso «non ha una fonte» ed è una lacuna. Non si capisce come scatti il consenso se il peso è ignoto. Inoltre `approval_required` indica due cose (download in attesa, r. 77; host senza risposta, r. 521); che si approva solo dalla GUI e lo stato «in attesa di approvazione» sono descritti solo per gli host (r. 486).

**CO-6 (Major). Formati di dati, di oggi e futuri.**
*Ambito:* spec r. 97, 99, 193, 266, 270.
Compaiono cinque formati: `daodan/visual@1`, `daodan/system-map/v1`, uno schema SQLite v1 di 21 tabelle (commit `c7bc75b`), un «vecchio esempio» ZIP con `project.json` e `v2/graph.sqlite` di cinque tabelle, lo schema 2. Non è detto quali esistono oggi, se i due archivi JSON spariscono, si importano o restano accanto al `.daodan`, né se la v1 sia mai stata usata fuori dalla «prova del proprietario» in memoria (r. 270). Il nome `v2/graph.sqlite` si confonde con lo schema 2.

**CO-7 (Major). Le interfacce.**
*Ambito:* spec r. 128, 148, 151, 156, 163; piano r. 26, 151, 185.
«App» o «GUI dell'app», «esploratore» e «pagina HTML dinamica» non sono mai definiti né messi in relazione. A r. 163 l'esploratore esiste già e carica tutto l'involucro, ma «la pagina è nel piano in T2.D»; per r. 128 le interfacce che mostrano la mappa sono solo due, l'app e la pagina. Non si sa se l'esploratore diventa la pagina, né se l'app è una finestra desktop o una pagina servita da `daodan/core/app.py` (piano r. 151).

**CO-8 (Major). Che cosa può girare sulla macchina locale.**
*Ambito:* spec r. 20, 56; piano r. 36, 83.
La Regola 3 («Zero esecuzioni sull'host») manda ogni test su Modal, ma T0.A.3 lancia `python daodan/core/support_table.py build` sul PC del proprietario e la spec fa girare le query tree-sitter sull'host. Il principio 6 vieta sull'host il codice del progetto analizzato, non quello di Daodan; la Regola 3 estende il divieto ai test di Daodan rimandando ad `AGENTS.md`, che non è nei due file. Chi esegue il piano non sa quali comandi può lanciare in locale, né perché.

**CO-9 (Major). I codici del piano.**
*Ambito:* piano r. 5, 15–16, 38, 44–75, 82, 90.
Lo schema dei codici non è spiegato e si ricava per confronto (`T0` traguardo, `T0.A` tranche, `T0.A.1` passo, `T0.4` punto 4 di T0), e non regge ovunque: `T0.7` è il punto 7, la rete, attuata in `T0.C` (r. 65), mentre la riga di T0.B (r. 16) e il passo T0.B.4 (r. 90) usano `T0.7` per il campione e il Cancello T0. La Regola 5 confronta con il «riferimento» di `tests/modal_pytest.py:18` (3.919–3.920 passati, 75 saltati), ma le corse di T0.A.2 contano 4630 e 78: non si capisce che cosa voglia dire «rispetto al riferimento».

**CO-10 (Major). Nomi propri non definiti né collegati.**
*Ambito:* spec r. 1, 53, 156, 166–167, 492; piano r. 7, 73, 88, 100, 141, 206.
Nessuno dei due file dice che cos'è Daodan, a chi serve e che cosa consegna. Mancano anche: Sigrid e Imago (chi «disegna la scena», la shell, il «renderer attuale di Sigrid»); GitNexus e il suo «metodo»; il «mapper», il «modello debole» e lo «0/19» di `I2`; Fable, a cui il proprietario delega decisioni; «inventive catalyst» e «Kiri ovunque». Nessuno è in «Termini» né ha un collegamento.

**CO-11 (Major). Classificazione dei nodi e sinonimi.**
*Ambito:* spec r. 105–113, 171, 503; piano r. 137, 185.
Un nodo ha specie, natura, concreto o astratto e tipo; l'anagrafica aggiunge `kind` e `category`. Il «tipo» non ha un valore di esempio e non si capisce che cosa aggiunga alla specie. Le parole cambiano senso: nel codice `nature` vuol dire concreto o astratto (r. 107) e i «livelli» sono le nature (r. 106), mentre nel piano «la mappa a livelli» (r. 26) vuol dire profondità; «grado» vale per le frecce (r. 110) e per la fonte dei comandi (r. 83), e «confermato» è anche uno stato dei nodi. La stessa anagrafica si chiama «anagrafica», «catalogo» e «registro». Non è chiaro quale specie e natura abbia una tecnologia di categoria `service`: r. 113 copre solo framework, libreria e strumento.

**CO-12 (Nit). Piccoli disallineamenti.**
*Ambito:* spec r. 3, 5, 492; piano r. 7, 90, 151.
- La legenda della spec dice che fra parentesi c'è il traguardo, ma le parentesi contengono codici di tranche (`T3.B`).
- Le parole da togliere dall'interfaccia non coincidono fra spec e piano.
- Il piano cita il protocollo «Confronto proposto per i flussi multilivello», variante A, senza dire in quale file sta.
- La legenda delle sigle `B`, `M` e `I` le attribuisce prima a `zoom_out_report.md` e poi a `goldfish_review_report.md`.
- I documenti rimossi sono al commit `614c940` per la spec e a `66e09dbca~1` per il piano; non si dice se sono due insiemi diversi.

---

## Incroci con lo stadio 5

- **CO-1** rafforza ZO-5 e IC-3: nessuno step produce flussi, varianti e profili. Ora lo vedono tre revisori indipendenti.
- **CO-3** coincide con ZO-N4 e IC-N1 (padrone della preparazione).
- **CO-6** tocca ZO-1 e ZO-3 (sorte di `visual@1` e `system-map/v1`, migrazione v1).
- **CO-9** comprende ZO-N1 e IC-N3 (riferimento vecchio della Regola 5).
