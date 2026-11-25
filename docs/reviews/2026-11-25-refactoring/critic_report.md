# Fase 3 di 5 (stage 7 del protocollo): critica

**Documento:** `docs/specs/architettura.md`, intero; contesto `docs/plans/refactoring.md` e `docs/backlog.md`. Versione: commit `591e1f6ed` più le aggiunte non in un commit; i numeri di riga sono di questa versione.
**Revisori:** tre agenti nuovi `general-purpose`, `fable`, effort `medium`, in invio diretto, tutti completati: disegno (`design_critic`, standard feature-spec), struttura (`structural`, standard feature-spec), stile (`style`). Sola lettura e divieto di aprire `docs/reviews/` sono istruzioni, non limiti degli strumenti; il piano di contesto contiene già le «Scelte aperte» nate dalla fase 1. Giro 1 del ciclo.

**Questo è il rapporto unito**: i rilievi uguali sono raggruppati e riassunti, i testi integrali sono in fondo, copiati dalle trascrizioni degli agenti. Gli id sono `<revisore>-1-<n>`, abbreviati in `D` (disegno), `S` (struttura), `T` (stile); la severità è quella del revisore.

| Revisore | Bloccanti | Importanti | Minori |
|---|---|---|---|
| Disegno | 4 | 11 | 6 |
| Struttura | 2 | 6 | 6 |
| Stile | 2 | 9 | 8 |

## Bloccanti

| Gruppo | Id | Rilievo |
|---|---|---|
| G1 Problema | S2, D1 (+ S3 M, D20 N) | Nessun paragrafo dice quale difetto di oggi giustifica otto step e piano unico; mancano obiettivi, non obiettivi e criteri di successo |
| G2 Alternative | S1, D2 | Nessuna alternativa scartata con il motivo: SCIP, otto step, fork `stack-analyser`, Noir, Kiri, `mise` |
| G3 Django, FastAPI, Flask | D3, T2 | r.41 e 46 le danno per decise e primarie; il piano r.70 riporta tre benchmark con «no» |
| G4 Isolamento | D4 (+ S4 M) | r.12, 86, 130-131: garanzie senza modello di minaccia né sezione dei rischi; `container.py` non passa `--cap-drop` né `--user`; i test di rete non usano un container vero |
| G5 Oggi e arrivo | T1 (+ S5, S6, D7, T3, T5 M) | Stato finale, stato di oggi e migrazione mescolati; marcatori in sei forme senza legenda; `surface`, `ui_execution_deferred`, `approval_required` scritti al presente senza essere nel codice; «contratto stabile» non verificabile |

## Importanti

| Gruppo | Id | Rilievo |
|---|---|---|
| G4b Assoluti di sicurezza | T6 | «isola sempre», «tutto il resto gira senza rete», Secretlint su «ogni testo»: senza stato né prova |
| G6 Fallimenti degli step | D6 (+ D19 N) | La tabella non dice che cosa succede se uno step fallisce o manca il container; «Ambiente preparato» non ha un padrone |
| G7 Noir senza container | D5 | r.46: Noir fa da ripiego «senza container», ma Noir gira nel container (r.36) |
| G8 `kind`, `category`, tipo | S8, T7 (+ D17 N) | La tabella dei nodi dice «Voce `service`» senza dire quale campo; tre nomi per il tipo di nodo |
| G9 Tipi di nodo | D13 | L'elenco «chiuso» omette `entità`, `applicazione`, `lavoro a orario` di `system_map.py:38`; i tipi `by: model` non hanno verifica |
| G10 Limiti | D8, T8 | Nessun tetto di tempo, memoria, disco; soglie non misurabili («qualche GB», «tempo reale»); elenco chiuso dei tipi di azione assente |
| G11 Piano unico | D9 | Stati, ripresa dopo il consenso, chi scrive, rapporto con `pipeline/plan.py` non specificati |
| G12 Backend di osservazione | D10 | V8, OpenTelemetry, eBPF elencati come standard ma registrati come ritirati o non concessi |
| G13 Effetti dell'esecuzione | D11 | Credenziali vere e di prova non distinte; controlli distruttivi premuti; isolamento dei servizi non detto |
| G14 Secretlint | D12 | Nessun punto di passaggio obbligato; i nomi dei pacchetti privati arrivano ai registri pubblici |
| G15 Dipendenze uniche | D14 | Fork, Noir (solo `linux-x86_64`), Kiri: che cosa succede se mancano e chi li mantiene |
| G16 Unione HTTP | D15 | Prefissi, URL base, percorsi calcolati e ambiguità non trattati |
| G17 Controlli delle anagrafiche | T4 (+ D16 N) | «Ogni anagrafica ha un controllo» include `build-tools.json`, che non esiste |
| G18 Titoli | S7 | Due soli H2; quattro H3 sotto la pipeline non ne fanno parte |
| G19 Termini | T9, T10 (+ S14, D18, T13 N) | Termini mai definiti; sinonimi (ripiego/fallback, adattatore/adapter, modello di evidenza/evidence model) |
| G20 Backlog come requisito | T11 | r.84 e 98 appoggiano regole al backlog, che vieta di essere citato come requisito |

## Minori

S9-S13 (periodi densi, celle sovraccariche, rimandi senza ancora, due commit di riferimento), D21 (riferimento alla storia), T12 e T14-T19 (ripetizioni, barre, frasi oscure, aforismi, aggettivi, negazioni sul passato, conteggi).

## Controlli del coordinatore

Verificati sul repository: G7 (Noir nel container), G9 (i tre tipi in `system_map.py:38`; **il testo incompleto l'ho scritto io in questa sessione**), G4 (nessun `--cap-drop` né `--user`), G14 (`secret_mask` importato da `app.py`, `mcp_server.py`, `pipeline_tree.py`). Gli altri non sono controllati.

## Corrispondenza degli id

| Id del rapporto unito | Etichetta del revisore |
| --- | --- |
| D1-D4, D5-D15, D16-D21 | B1-B4, M1-M11, N1-N6 del disegno |
| S1-S2, S3-S8, S9-S14 | B1-B2, M1-M6, N1-N6 della struttura |
| T1-T2, T3-T11, T12-T19 | B1-B2, M1-M9, N1-N8 dello stile |

## Testo integrale: Disegno (`D`)

Critica del design di docs/specs/architettura.md, parte 1 di 2: quattro Blocker e i primi Major (standard: feature-spec).
Righe = docs/specs/architettura.md salvo dove indicato. Verifiche fatte in sola lettura sul repository.

BLOCKER

B1. Manca il problema, mancano obiettivi e non-obiettivi. Righe 1-13.
Il documento apre con i principi e la pipeline a otto step, senza dire quale difetto di oggi giustifica otto step, piano unico e spostamento delle sorgenti. Il piano lo ammette (refactoring.md:37, scelta B2 ancora aperta). Oggi gli step sono sei (daodan/core/pipeline/__init__.py:277). Rimedio: una sezione «Problema» con i difetti misurati di oggi, e «Obiettivi / Non obiettivi» (macOS/iOS, superfici differite, modello locale sono non-obiettivi sparsi nel testo).

B2. Regola delle alternative non rispettata. Tutto il documento; in particolare righe 31, 41-48, 130-131.
Nessuna sezione di alternative. Scelte marcate `[deciso]` senza opzione scartata e motivo: SCIP contro LSIF/LSP («Nessuna migrazione», riga 47, senza ragione); otto step contro i sei di oggi; fork `stack-analyser` come unico riconoscitore contro Syft (la misura c'è in benchmarks/project-model/REPORT.md ma la spec non la cita); Noir contro sorgente dedicata; Kiri in WSL contro il motore dell'utente su Windows; `mise` per le toolchain. Rimedio: una tabella «Alternative considerate» con il motivo tecnico e il benchmark che lo prova.

B3. Django, FastAPI e Flask «primarie» contro le misure del repository. Righe 41 e 46.
La spec fissa come contratto che l'introspezione dedicata è primaria e Noir è ripiego. I tre benchmark chiudono con «no» (refactoring.md:70: Flask «non aggiunge a Noir quanto costa», FastAPI non carica nessuna delle due applicazioni nelle condizioni di Daodan, Django 0 funzioni su 132). Il backlog ritira Spring per lo stesso motivo («Noir dà lo stesso», backlog.md:58). Nessuna delle tre è collegata oggi. È un'affermazione senza prova, e contraddetta. Rimedio: o la spec porta la misura nuova che ribalta i tre verdetti, o declassa la riga a scelta aperta (B1 del piano, refactoring.md:86).

B4. L'isolamento è il principio 6, ma la spec non ha un modello di minaccia e dichiara garanzie non collaudate. Righe 12, 86, 130-131.
- Riga 131: «nessuna uscita diretta, inclusi redirect, DNS e IP letterali» è scritto come fatto. I test di oggi controllano gli argomenti passati al motore e tre rifiuti del proxy, non un container vero (refactoring.md:120). Il test decisivo è in T3, ma la rete e l'esecuzione di codice del progetto sono già in uso oggi (refactoring.md:34).
- Indurimento assente dal contratto: daodan/core/container.py passa `--security-opt no-new-privileges`, non `--cap-drop` né `--user` (verificato: nessuna occorrenza). Il codice del progetto gira da root nel container.
- Non detto: se il sorgente è montato in sola lettura, limiti di memoria/pid/tempo (nel codice ci sono memoria e pid, nella spec no), che cosa succede a una fuga dal container, chi garantisce l'integrità di ciò che `mise` scarica.
Rimedio: sezione «Rischi e limiti» con modello di minaccia (codice ostile nel progetto), elenco dei controlli e, per ognuno, «collaudato / non collaudato»; la sonda di rete su container vero come condizione prima di ogni uso con rete.

MAJOR

M1. Noir è ripiego «senza container», ma Noir gira nel container. Righe 36 e 46.
Riga 36: Noir «gira nel container» (confermato: daodan/core/premap/noir.py:22). Riga 46: «Senza container o a introspezione fallita, Noir fa da fallback». Senza container non c'è né sorgente dedicata né Noir. Rimedio: dire che senza container `find_entry_points` dà solo le query tree-sitter (riga 45) e una lacuna.

M2. Il contratto degli step non dichiara i fallimenti che il principio 3 promette. Righe 9, 19-28.
La tabella ha «legge» e «scrive», non «che cosa succede se fallisce». Non detto: se `recognize_stack` fallisce o il fork non conosce lo strumento, `find_modules` gira? `find_entry_points` dipende dai «pacchetti ripristinati» di `find_modules` (riga 25): uno step statico dipende dalla preparazione con rete, e senza container il degrado non è scritto. «Ambiente preparato» (riga 26) non ha padrone, contro il principio 2. `assemble_graph` legge «Tutto». Rimedio: colonna «Se fallisce / senza container» e padrone esplicito della preparazione.

M3. Stato del documento ambiguo: contratto «a refactoring finito» mescolato a stato di oggi. Righe 3, 72, 80-84, 92-98, 117-126.
Un lettore non distingue ciò che vale oggi da ciò che è bersaglio. Esempi verificati: il campo `surface` «decide» (riga 80) ma 0 voci su 2.568 lo hanno; `approval_required` e `ui_execution_deferred` (righe 84, 86) non esistono in daodan/, e nessun traguardo del piano li porta (refactoring.md:91). Sono contratto senza proprietario. Rimedio: marcare ogni regola «oggi / bersaglio (Tn)» come già fanno le tabelle delle fonti e delle anagrafiche.

M4. Nessun limite di scala né di costo. Righe 100-107, 128-134.
«Preparazione (una per analisi)»: toolchain e dipendenze ripristinate a ogni analisi, senza dire cache, disco, tempo, monorepo con più toolchain. SCIP per cinque compilatori: nessun tetto di memoria/tempo (il piano registra un timeout di circa 6 minuti come difetto, refactoring.md:105). `run_and_observe` lancia suite intere sotto registratore e Chromium: nessun budget, timeout, annullamento; il limite di tempo per stage è differito (backlog.md:46). Rimedio: tetti dichiarati per step (tempo, memoria, disco), comportamento allo sforamento (lacuna), e dimensione massima di progetto provata.

Critica del design di docs/specs/architettura.md, parte 2 di 2: Major restanti e Nit.

MAJOR (segue)

M5. Piano unico: stati e consenso non specificati abbastanza da implementarlo. Righe 100-107.
«Tipi di azione da elenco chiuso» ma l'elenco non c'è. L'arresto per consenso non dice come riprende un chiamante senza interfaccia (MCP, CLI), se il consenso persiste, che cosa succede a tempo scaduto. «Un solo oggetto condiviso» fra tre chiamanti: non è detto chi scrive né come si evita la divergenza dal giornale (due fonti di stato). Il piano che esiste (daodan/core/pipeline/plan.py: nodi `{id, step, adapter, on, container, needs}`, senza stati) non è messo in relazione. Rimedio: elenco dei tipi, macchina a stati, scrittore unico, ripresa dopo consenso.

M6. Backend di osservazione elencati come standard ma già valutati e scartati. Righe 43 e 48.
La spec nomina V8 coverage, OpenTelemetry, `strace`/eBPF. Nel repository: profiler V8 ritirato (backlog.md:63, 47,1% sotto soglia); OpenTelemetry scartato nelle docstring di `dynamic/javascript.py`, `jvm.py`, `dotnet.py`; il container non concede eBPF (`clang.py`, `rust.py`); `strace` non compare; per Python i due termini del confronto sono lo stesso strumento (refactoring.md:123, 130). Rimedio: togliere dal contratto i backend scartati o citare la misura nuova che li riapre.

M7. `run_and_observe` esegue test e avvia l'app senza mitigare gli effetti. Righe 43, 82-86.
«Solo dati e credenziali di prova già preparati dalla CI»: non è detto come si distinguono da credenziali vere presenti nel repository (`.env`, config). Azionare tutti i controlli di un'interfaccia può fare azioni distruttive sui servizi avviati accanto. Non detto se i servizi della CI girano isolati dalla rete. Rimedio: regola esplicita sui file di segreti, servizi solo effimeri nel pod, elenco delle azioni non premute.

M8. Secretlint: garanzia assoluta senza punto di passaggio obbligato. Riga 134.
«Ogni testo che lascia la macchina» non ha meccanismo: `secret_mask` è importato solo da `app.py`, `mcp_server.py` e `pipeline_tree.py`. Non detto: comportamento se Secretlint fallisce (deve chiudere), falsi negativi. Inoltre il ripristino via proxy manda ai registri pubblici i nomi dei pacchetti del progetto: i nomi di pacchetti privati escono (rischio dependency confusion) e non passano da Secretlint. Rimedio: un solo modulo di uscita con test che nessun altro percorso trasmetta; politica per registri privati.

M9. Tipi di nodo: l'«elenco chiuso» non è uno solo, e i tipi `by: model` non hanno verifica. Righe 59, 70-72, 75.
`flows.NODE_TYPES` ha 11 tipi; `daodan/core/system_map.py:38` ne aggiunge tre (`entità`, `applicazione`, `lavoro a orario`). La riga 75 cita «l'entità» senza definirla. Riga 59: senza `category` le voci non `service` valgono `framework`: sono 1.350 voci su 2.568 senza categoria, e 1.297 hanno tipo `altro`. I tipi di framework e librerie sono scritti da un modello (riga 71) senza criterio di accettazione né misura di errore. Rimedio: un elenco, con le estensioni della mappa di sistema dichiarate; campione verificato a mano dei tipi `by: model`.

M10. Punti unici di guasto esterni non trattati. Righe 31, 36, 130.
Il fork `stack-analyser` è l'unico riconoscitore: ogni strumento nuovo chiede un rilascio del fork, senza costo né ripiego. Noir è un binario fissato `linux-x86_64` (noir.py:10): arm64 non detto. Kiri 0.2.0 viene da un progetto terzo, e la sua licenza è una verifica ancora aperta (backlog.md:30). Rimedio: per ognuno, che cosa succede se manca o si ferma, e chi lo mantiene.

M11. Unione HTTP «dove percorso e metodo coincidono» senza trattare i falsi legami. Righe 53-55.
Non trattati: prefissi e mount, URL base, percorsi calcolati (il valutatore di stringhe è scelta aperta, refactoring.md:85), parametri di percorso, più rotte con lo stesso schema. Lo stato `ambiguo` del modello di evidenza (riga 47) non ha una regola di resa nel grafo. Rimedio: regola per ambigui (arco incerto, mai scelto a caso) e misura dei falsi archi nel cancello.

NIT

N1. Riga 115: «Ogni anagrafica ha un controllo automatico di coerenza» vale anche per `build-tools.json`, che non esiste (riga 123). Scrivere «avrà» o togliere la voce dalla frase.
N2. Righe 59-65 e 122: `kind` (`service`, `project`) e `category` (`framework`, `library`, `tool`, `service`) sono usati come se fossero lo stesso campo («Voce `framework`», «Voce `tool`»). Dire sempre quale campo.
N3. Termini non definiti per chi arriva nuovo: Kiri, fork `stack-analyser`, binder, tessera, store, regola di collegamento, SCIP, «ripiego».
N4. Riga 8 contro riga 11: il principio 2 ammette un «ripiego» senza limiti, il principio 5 vieta la regola a mano. Dire che il ripiego è solo uno strumento ufficiale statico o una lacuna.
N5. Nessun criterio di successo nella spec: i cancelli stanno solo nel piano. Un rimando esplicito basta.
N6. Riga 3: i commit `614c940` e la data futura come unico riferimento alla storia: aggiungere il comando `git show` come fa il backlog.

Non verificato: l'esistenza dei controlli di coerenza per le singole anagrafiche esistenti, e la riga 121 (`language-rules.toml` contro `languages/detect/rules/` del piano). Nessun file modificato, nessun codice eseguito oltre a letture e a un conteggio JSON.

## Testo integrale: Struttura (`S`)

Critica strutturale di docs/specs/architettura.md (Mode REVIEW, feature-spec-standard): 2 Blocker, 6 Major, 6 Nit. Prima azione: aggiungere le sezioni «Problema» e «Alternative considerate».

Mappa dei titoli: H1 (r.1) > H2 «Principi» (r.5), H2 «La pipeline a otto step» (r.15) > nove H3 (r.34, 51, 57, 78, 88, 100, 109, 113, 128). Nessun livello saltato. Non ho potuto consultare l'advisor (limite di chiamate): il rapporto non ha una seconda lettura.

BLOCKER

B1. Manca «Alternative considerate» (tutto il documento).
- Lo standard fa fallire una spec che propone una sola via. Qui non c'è sezione né tabella di opzioni scartate con motivo.
- Restano frammenti senza ragione: r.47 «Nessuna migrazione a LSIF/LSP», r.46 sorgente dedicata «primaria» su Noir, r.131 proxy come confine.
- I tre `[deciso]` (r.41, 47, 131) dichiarano una decisione senza motivo né rimando. Per r.41 il piano (refactoring.md r.70) riporta tre benchmark con verdetto «no» su Django, FastAPI e Flask, e la scelta aperta B1 (r.86) lo conferma: la spec fissa il contrario senza dirlo.
- Le alternative scartate esistono solo in backlog.md r.51-64, che si dichiara non normativo e non citabile.

B2. Manca il «Problema» (r.1-3).
- Il documento apre con lo stato e passa ai principi. Nessun paragrafo dice quale difetto di oggi giustifica otto step, piano unico e spostamento delle sorgenti.
- Il piano lo registra come scelta aperta B2 (refactoring.md r.37): «Né questo piano né architettura.md lo dicono».

MAJOR

M1. Manca «Obiettivi e non obiettivi».
- I non obiettivi sono sparsi: r.84 (macOS, iOS, superfici differite), r.98 (modello locale), r.47 (LSIF/LSP).
- Gli obiettivi si deducono solo dai principi. Nessun criterio misurabile nella spec: i cancelli stanno nel piano.

M2. Manca «Rischi e mitigazioni».
- Le mitigazioni di sicurezza sono sparse (r.12, 86, 131, 134) senza il rischio a cui rispondono.
- Limiti di scala, costo e modi di guasto non compaiono.
- Il principio 3 (r.9) dice che ogni step dichiara che cosa succede se fallisce, ma la tabella degli step (r.19-28) non ha la colonna del guasto.

M3. Il documento mescola stato finale e stato attuale, contro la sua intestazione (r.3: «com'è Daodan a refactoring finito»).
- r.72 «Oggi nel codice», r.76 «oggi la vista non passa il logo», colonne «Stato» a r.92-98 e r.117-126.
- r.80 e r.84 descrivono al presente `surface`, `ui_execution_deferred` e `approval_required`; r.122 dice «senza `surface`» e il piano (r.91) dice che nessun punto li porta.
- Un lettore nuovo non distingue contratto da inventario.

M4. Marcatori di stato senza legenda e in sei forme.
- `[deciso]` in codice (r.41, 47, 131), «**Oggi nel codice:**» e «**Scelta aperta:**» (r.72-73), «(attiva)» e «(attiva in T3)» (r.82-83), valori liberi nelle colonne «Stato»: «Nel codice», «Proposta (T3)», «Parziale (T3)», «Differito», «Da creare (T1)», «Nel codice (mancano `.h` e nomi file)».
- Il piano scrive lo stesso marcatore in grassetto (**[deciso]**), non in codice.
- La scelta aperta di r.73 è sepolta in un elenco annidato: non c'è una sezione delle scelte aperte.

M5. Gerarchia piatta e mal raggruppata (r.15-134).
- Tutti e nove gli H3 stanno sotto «La pipeline a otto step», ma quattro non sono parti della pipeline: «Il piano» (r.17 dice che non è uno step), «L'interfaccia segue la pipeline», «Le anagrafiche», «Servizi comuni». «Nodi del grafo: tipo e logo» è un contratto di dati.
- Servono H2 propri (ad esempio Piano, Dati, Servizi, Interfaccia). Oggi il documento ha due soli H2, di cui uno tiene 120 righe su 134.

M6. Tabella dei nodi con chiave ambigua (r.59-68).
- r.122 dà a `kind` i valori `service` e `project`, e a `category` i valori `framework`, `library`, `tool`, `service`. La colonna «Che cosa» scrive «Voce `service`», «Voce `framework` o `library`», «Voce `tool`» senza dire quale campo.
- r.67 mette due casi in una riga e li accoppia per posizione con «;» («servizio o API; schermata»).
- r.64-65 usano «—» per «non è un nodo»: la tabella mescola nodi e non nodi.

NIT

N1. r.86: quattro regole comuni in un periodo con punti e virgola, mentre il resto della sezione è a elenco. Il titolo H3 promette «regole comuni» ma non hanno un blocco proprio.
N2. r.26: la colonna «Deve sapere prima, e da chi» ha «Ambiente preparato» senza «da chi»; r.28 ha «Tutto». r.23 mette una negazione («Nessun modulo») nella colonna di ciò che scrive.
N3. r.43 e r.122: celle sovraccariche (quattro backend e tre file in una riga). r.122 aggiunge «(+ `surface`)» per un campo che la colonna «Stato» dice assente.
N4. Rimandi interni senza ancora: r.30 «vedi «Servizi comuni»», r.32 `docs/pipeline/` in codice e non come link, mentre piano e backlog sono link (r.3, 84, 98). Il link al backlog è ripetuto tre volte.
N5. r.3 cita la storia al commit `614c940`; il piano (r.7) cita la spec rimossa a `66e09dbca~1`. Due riferimenti per lo stesso storico.
N6. Termini usati senza definizione o prima di essa: «pre-mappa» e «fork `stack-analyser`» (r.30-31), «SCIP» (r.42), «Kiri» (r.130, definito solo lì). Manca un glossario breve.

Prossimo passo: decidere se «Problema» si scrive ora o dopo la chiusura della scelta aperta B2 del cancello T0.

## Testo integrale: Stile (`T`)

Critica di stile di docs/specs/architettura.md, parte 1 di 2: Blocker e Major (2 Blocker, 9 Major, 8 Nit in tutto).
Modo REVIEW. Righe = architettura.md; «piano N» = docs/plans/refactoring.md riga N.

BLOCKER

B1. Tre registri senza marcatore — righe 3, 19-28, 30, 72, 76, 102, 111, 115-126.
La riga 3 dichiara che il documento descrive Daodan «a refactoring finito», ma il testo alterna senza segnale: stato finale al presente (tabella 19-28), stato di oggi (72, 76 «oggi») e racconto della migrazione («non tiene più», «esce dalla pre-mappa» 30; «resta come cronaca» 102; «escono dall'interfaccia» 111). Solo due tabelle hanno la colonna Stato (92-98, 117-126); la tabella degli otto step non ce l'ha, e il piano 76 accerta che oggi gli step sono sei. Il lettore non può dire quali frasi al presente valgono oggi. Azione: CALIBRATE: un marcatore unico per frase o colonna Stato in ogni tabella; i verbi di migrazione vanno nel piano. Inoltre il vocabolario di Stato («Nel codice», «Proposta», «Parziale», «Da creare», «Differito») non è definito in nessun punto.

B2. Django, FastAPI e Flask dati per decisi e primari — righe 41, 46.
«sorgenti Django, FastAPI, Flask [deciso]» e «la sorgente dedicata è primaria» sono scritti come fatto. Il piano 70 accerta tre verdetti «no» nei benchmark e che nessuna delle tre è collegata; il piano 86 tiene aperta la scelta (B1 del piano). L'affermazione supera la prova. Azione: CALIBRATE: scrivere che è una decisione non ancora sostenuta da misura, con rimando alla scelta aperta.

MAJOR

M1. «contratto stabile» — riga 3.
Il documento contiene una «Scelta aperta» (73) e il piano elenca scelte aperte che toccano questo testo (piano 86, 89, 91, 109). «Stabile» non è verificabile. Azione: CALIBRATE (dire quali sezioni sono ferme) o DROP dell'aggettivo.

M2. Universali che la tabella accanto smentisce — riga 115 contro 121-123.
«Ogni anagrafica ha un controllo automatico di coerenza con il codice»: `build-tools.json` è «Da creare (T1)», `language-rules.toml` è incompleta, il registro è «senza `surface`». Azione: CALIBRATE a «ogni anagrafica già nel codice», o colonna con il nome del test.

M3. `surface`, `ui_execution_deferred`, `approval_required` scritti come comportamento — righe 80-86.
«Il campo `surface` dell'anagrafica decide», «`web` (attiva)», «emettono la lacuna `ui_execution_deferred`», «altrimenti `approval_required`» sono al presente. La riga 122 dice che il campo non c'è; il piano 78 e 91 accertano che i due nomi non sono in `daodan/` e che nessun punto del piano li porta. «Attiva» non è definito (decisa? nel codice?). Azione: CALIBRATE, con lo stato accanto a ogni voce come nelle tabelle.

M4. Assoluti di sicurezza senza prova citata — righe 130, 131, 134.
«isola sempre», «tutto il resto gira senza rete», «strumenti verificati per sha256», «ogni testo… passa prima da Secretlint»: nessuno ha uno stato o un test. Il piano 120 accerta che i test di rete controllano gli argomenti passati al motore, non un container vero, e che `--cap-drop` e `--user` non sono passati. Azione: CALIBRATE: per ogni garanzia dire se è nel codice e quale test la prova; la 134 non ha alcun riscontro nei tre documenti.

M5. `kind`, `category`, `type`, `node_type` — righe 59, 63-68, 122.
La 122 dà a `kind` i valori `service`, `project`; la 59 parla di «voce di `kind` `service`» e di `category`; la tabella 63-65 scrive «Voce `service`», «Voce `framework` o `library`», «Voce `tool`» senza dire quale campo. «Tipo di nodo», `type` (63) e `node_type` (68) nominano lo stesso concetto con tre nomi. Azione: nominare sempre il campo (`category: tool`) e un solo termine per il tipo.

M6. Soglie non misurabili su cui un operatore decide — righe 46, 86, 105, 107.
«di qualche GB» (86) e «download pesante» (105): il backlog cita ~500 MB e ~4 GB, e il testo non dice da che dimensione serve il consenso. «in tempo reale» (107) senza latenza. «dove serve» (46) senza criterio. «Tipi di azione da elenco chiuso» (107) senza elenco né rimando, mentre la 70 lo dà.

M7. Termini e sigle non definiti per chi legge da zero — righe 31, 41, 71, 74, 75, 83, 111, 130.
`[deciso]` (deciso da chi, quando, contro quale alternativa), T1/T3 (definiti solo nel piano), «Kiri», «fork `stack-analyser`», «Sigrid», «Imago», «tessera», «entità» (75), `by: model` (71), «backend standard» (43, 48), «pre-mappa» (usata a 30 prima di essere spiegata).

M8. Sinonimi per lo stesso concetto — tutto il documento.
ripiego (8) / fallback (46); adattatore (31, 55) / adapter (42, 47); modello di evidenza (42, 47) / evidence model (47); step / passo (12, 90); il piano è «una funzione» (17) e «un solo oggetto» (102); integrazione / complemento. «Controllo» ha tre sensi: comando dell'interfaccia (27, 49, 82), verifica (115), misura di sicurezza (131). AGENTS.md vieta i sinonimi per lo stesso concetto.

M9. Requisito appoggiato a un documento non normativo — righe 84, 98.
La 84 impone una lacuna alle superfici «tracciate in docs/backlog.md»; il backlog (riga 3) vieta di essere citato come requisito da questo file. La riga 98 mette in una tabella normativa una fonte «Differito». Azione: RELOCATE: la regola della lacuna resta qui senza appoggiarsi al backlog; la riga 98 va nel backlog.

Critica di stile di docs/specs/architettura.md, parte 2 di 2: Nit.

N1. Ripetizioni — righe 42/47, 43/48, 3.
La cella 42 ripete la 47 («primo adapter dietro il modello di evidenza»); la cella 43 ripete la 48 (elenco dei backend). La frase sulla storia di git (3) ripete il backlog 70. Tenere ogni fatto in un punto.

N2. Inglese non tradotto nella prosa italiana — righe 46-48.
«call events», «call graph», «span», «overhead», «mount/router», «compiler API», «fallback». Tradurre o definire alla prima occorrenza; lasciare in inglese solo gli identificatori.

N3. Barre e frasi ellittiche — righe 24, 26, 28, 46, 86.
«integrazione/fallback», «contesto/mount/router», «test/avvio/build»: la barra non dice se è «e» o «o». La 86 mette quattro regole in una frase; «nulla dell'host» non ha verbo. «Ambiente preparato» (26) non dice da chi viene, a differenza delle altre celle; «Tutto» (28) non è verificabile.

N4. Frasi oscure — righe 54, 71, 96.
«è ciò che più plausibilmente è la parte di programma costruita con essa» (71): criterio soggettivo, non verificabile. «vale per il runner lanciato, non per il nome» (96) e «si prova dai dati del compilatore, non dal nome» (54): manca il soggetto di «nome».

N5. Aforismi e figure al posto della regola — righe 8, 11, 13, 49, 80, 90, 109.
«Un padrone per fatto… lo chiede a lui», «mai un silenzio», «Un'interfaccia nasce da un ingresso, non da un manifesto», «Un comando non si indovina mai», «L'interfaccia segue la pipeline». Il «nostro» di riga 11 è l'unica prima persona del documento. Sostituire con la regola verificabile.

N6. Aggettivi di giudizio — righe 42, 47, 131.
«piccolo evidence model», «controllo decisivo»: senza misura. DROP.

N7. Negazioni che raccontano il passato — righe 23, 30, 47.
«Nessun modulo», «non tiene più», «Nessuna migrazione a LSIF/LSP»: hanno senso solo per chi conosce lo stato precedente. Azione: RELOCATE nel piano o nel backlog («ritirato»), oppure dire quale decisione del lettore servono.

N8. Conteggio e forma incoerenti — righe 12/13, 106.
«tre fatti» ne elenca quattro (esegue codice, gira nel container, scarica dalla rete, quanto pesa). La lacuna ha «la sua causa» (12) e «causa e rimedio» (13): uniformare.

Frasi già calibrate, da tenere (KEEP): 72, 76, 121, 122 («senza `surface`»), 123 («Da creare»).
