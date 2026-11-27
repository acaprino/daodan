# Stadio 9 — Implementation Readiness (giro 1)

- **Bersaglio:** `docs/plans/refactoring.md` (DetailedRange, tutto il file, 225 righe), commit `a4360b01b`.
- **Contesto:** `docs/specs/architettura.md`, `docs/backlog.md`, `docs/reviews/2026-11-25-refactoring/zoom_out_report.md`, `docs/reviews/2026-11-25-refactoring/goldfish_review_report.md`. I report degli stadi 5–8 non sono stati passati.
- **Revisori e standard:** implementation-readiness (`implementation-readiness-standard.md`), codebase-details (`implementation-readiness-standard.md`), style (solo persona).
- **Identificativi:** `<revisore>-<giro>-<n>`.
- **Isolamento ottenuto:** subagenti nuovi senza la conversazione; ricevono comunque `CLAUDE.md`, `AGENTS.md` e gli hook di sessione. Solo Read, Grep, Glob per istruzione; esclusa per istruzione la cartella di questa review.

---

## Revisore Style

1 Blocker, 10 Major, 8 Nit. Nessuna iperbole, linguaggio promozionale o giudizio soggettivo; i blocchi `[accertato nel repository]` citano file e corse e restano (KEEP), come le r. 101 e 103.

### Blocker

**style-1-1. Le due corse coerenti non possono soddisfare tutte le condizioni del piano.** r. 46, 75, 82, 83. Il punto 1 (r. 46) vuole le due corse «sullo SHA che chiude `T0.A.3`»; `T0.A.2` (r. 82) è spuntato con corse su `44462b569`, prima di `T0.A.3`; `T0.A.3` (r. 83) modifica per certo il codice (`STACK` in `daodan/core/support_table.py`), quindi la condizione «se `T0.A.3` modifica codice» è già vera; il Cancello T0 (r. 75) cita «le due corse coerenti di `T0.A.2`». Chi chiude il Cancello T0 non sa se servono corse nuove. *Azione:* togliere «si valuterà se riconfermare» e o allineare il punto 1 allo SHA usato davvero, o mettere in `T0.A.3` una regola con criterio (es. «se il diff di `T0.A.3` tocca `daodan/` o `tests/`, due nuove corse `suite` sullo SHA finale; il Cancello T0 cita quelle»).

### Major

**style-1-2. Cautele scadute e alternative non risolte** (le prime tre toccano la tranche aperta). r. 59 «da confermare in `T0.A.2`», già fatto; r. 84 chiede di mettere in quarantena il caso di `tests/test_codebase_map_app.py` che la r. 56 chiude con «non entra in quarantena»; r. 48 «Tabella dei difetti aperti» con quattro righe su sei chiuse; r. 54 «Già corretto nel codice» contro «non è un difetto»; r. 116 «l'eventuale spostamento come classe di `detect/rules/`» dentro un `[deciso]`; r. 132 «`suffix_table.NAMES` … resta, o passa a `file_formats.LINGUIST_NAMES`» dentro un `[deciso]`; r. 141 «(da verificare)» dopo «si prova prima»; r. 83 «le sei fixture … non hanno un «prima»» senza dire che cosa farne (es. «escluse dal conteggio delle perdite»).

**style-1-3. Criteri di cancello non misurabili** (il primo entra nel prossimo passo). «Zero perdite non spiegate» (r. 47, 75, 83, 165) senza definizione: sta in `benchmarks/project-model/README.md:536`, va citata. r. 126 «è il cancello del punto 9» senza condizione di passaggio, mentre la r. 128 fissa già un elenco chiuso. r. 168 «verificati» senza termine di confronto. r. 196 «soglie … registrate»: registrare non è rispettare. r. 224 «verdetti … salvati»: T3 si chiude anche con un verdetto negativo? r. 186 perde il criterio misurabile della spec (`architettura.md:138`). r. 176 «si aggiunge il campo» senza campo né soglia. r. 212 e 224: lo scopo di `T3.B` è «ogni altro strumento di build», il cancello chiede un solo progetto non npm.

**style-1-4. Numerazione a due schemi, gerarchia non definita.** r. 7, 15, 16, 89, 90, 94, 126, 154. La legenda non definisce traguardo, tranche, passo e punto; `T0.C` (tranche) e `T0.3` (punto) hanno la stessa forma. Errore già avvenuto: r. 16 e 90 attribuiscono `T0.7` a `T0.B`, ma il punto 7 (r. 65) è la rete, in `T0.C`. La colonna SHA (r. 15) mescola passi e punti; terzo stile «punto 15 di T1», «punto 9». `T0.C` è un H2 come i traguardi, ma il Cancello T0 non la comprende: non si capisce se T0 si chiude prima di `T0.C`.

**style-1-5. Le «Scelte aperte» contengono solo scelte chiuse.** r. 68, 87, 153, 189, 217 e la colonna omonima. Ogni voce è `[deciso]`; l'unica scelta aperta («Indirizzi degli strumenti di Daodan fuori lista», r. 17) non è in queste sezioni. Le voci ripetono i punti (go-enry r. 132/154, `.ts` r. 118/160, Django r. 137/161, Syft r. 126/162, GitNexus r. 141/158, backend runtime r. 213/222, popup r. 65/72/218). *Rimedio:* «Decisioni prese» con il solo legame a B, M, I, o togliere i doppioni.

**style-1-6. Ogni voce di T0 è descritta due volte, e le versioni divergono.** Punti 1–6 (r. 46–64) contro passi (r. 82–90): punto 1 contro `T0.A.2` (style-1-1); punto 2 chiede la mediana della scansione veloce (0,523 s), `T0.A.3` solo «annotare tempi»; punto 5 «distinguendo i 6 step», `T0.B.3` «via i sette nomi del 22 novembre»; punto 6 «almeno 1 domanda ciascuna», `T0.B.4` «Tre domande». *Rimedio:* una sola descrizione, il passo; il punto diventa indice.

**style-1-7. Etichette di stato applicate in modo incoerente.** r. 7, 18, 64, 70, 90, 116, 133. Non è detto che cosa vale una voce senza etichetta; il punto 6 promette una «decisione congiunta in `T0.B.4`», ma `T0.B.4` fissa quota (un terzo, `random.Random(2026)`) e «variante A» senza etichetta; r. 70 usa `[accertato nel repository]` per un fatto di CI, fuori posto; r. 116 usa `[deciso]` per un fatto («è già collegato») mentre la mappa (r. 18) elenca ancora il collegamento di `header.py` fra le consegne; r. 133 `[deciso]` a metà frase senza dire a che cosa si applica.

**style-1-8. Regole 3 e 4: titolo che promette troppo e due definizioni di albero pulito.** r. 36, 37, 83. «Zero esecuzioni sull'host» contro `T0.A.3` (`python daodan/core/support_table.py build` sul PC del proprietario) e `tests/modal_pytest.py` che parte dall'host. La Regola 3 vuole `git status` senza modifiche, la Regola 4 lo restringe a cinque cartelle. *Azione:* titolo su ciò che è vietato davvero (codice del progetto analizzato e suite) e una sola definizione, quella della Regola 4.

**style-1-9. Omonimi e sinonimi.** Caso più grave r. 56: «corsa» vuol dire esecuzione CI e race condition nella stessa riga («Presunta corsa … passato in 3 corse `suite`»), più «Run di lavoro» (r. 60) ed «esecuzioni» (r. 38). «Passo» ha quattro sensi (passo del piano; step della pipeline, «otto passi» r. 22, 151, «otto step» r. 63, «8 identificatori» r. 21, «otto id» r. 89; passo nel container r. 100; passi di una variante r. 186). «Cancello» per traguardo e precondizione (r. 126); «mappa» per tabella di avanzamento e mappa del prodotto; «piano» per questo documento e il piano unico (r. 119); «registro», «anagrafica», «catalogo»; «edit manuali» e «modifiche a mano»; «sonda», «prove di uscita», «prova su container reale».

**style-1-10. `T0.A.3` è una sola frase con circa dieci azioni** (prossimo passo da eseguire). r. 83. I due «verificare» non hanno oggetto (che cosa si confronta con `daodan_stack_fork_develop_68b784e.json`?); non dice da quale corsa viene il nuovo `daodan_stack.json`; la verifica non comprende `test_codebase_map_support_table.py`, che il passo esegue. *Rimedio:* elenco numerato, un'azione e un esito per voce.

**style-1-11. Il piano ripete il contratto della spec e se ne discosta.** r. 100, 151, 186. `T1.18` toglie «pre-mappa», «scan», «analyzer», la spec (r. 492) «pre-mappa», «scan», «stack», «analyze»; `T2.6` ripete «La mappa» e perde il criterio misurabile; `T0.C` punto 3 ricopia «Servizi comuni» (spec r. 514–521) in circa 150 parole. *Rimedio:* rimandare alla spec e scrivere solo ciò che la tranche aggiunge.

### Nit

- **style-1-12. Provenienza delle verifiche imprecisa:** r. 5 dà `T0.A.0` verificato su `44462b569`, ma è un controllo del diff su `78e070129` (r. 80); r. 52–53 citano `ap-V55…` su `44462b569`, la r. 81 su `7670c2bad`.
- **style-1-13. Stato ripetuto in più punti:** «3/5» in r. 5, 15, 79; 4630 in r. 15, 70, 82; r. 3 ripete la Regola 2 con un sinonimo («non bloccata» per `LIBERA`); r. 105 ripete r. 28 e 208–210; la clausola della Regola 5 in cinque cancelli.
- **style-1-14. Il piano non rispetta le proprie regole:** stati ammessi chiusi (r. 11) ma valori composti nelle r. 16, 24, 29; Regola 1 (solo la tranche aperta si espande) mentre `T0.B`, `LIBERA`, è espansa; `T0.B.1` e `T0.B.2` senza *Commit:*; il commit `docs(...)` di `T0.A.3` copre anche codice.
- **style-1-15. Termini e rimandi non definiti:** «Fable» (13 occorrenze), «0/19», «modello debole», «mapper», «la corsa costa» (il README:154 dà 0,38 USD per 8 corse), «`cli()` e Node veri», «`Desktop`», «principio 1», «variante A», `reference.py pin`, «180» (r. 18, assente da `T1.4`), «passaggio staccato», «secondo Pyright», «anonime», «on senza punto citato», «equivalenza tra modalità»; r. 7 dà `66e09dbca~1` per i documenti rimossi, ma il comando legge un solo file e spec e backlog dicono `614c940`; il percorso `614c940:2026-11-21-stack-dal-fork.md` (r. 56) non funziona con `git show`.
- **style-1-16. Lavoro futuro scritto come già fatto:** «è già in `T0.C`» (r. 208), «che `T0.C` già mostra» (r. 146), «il popup c'è già da `T0.C`» (r. 164), mentre `T0.C` è bloccata.
- **style-1-17. Formulazioni vaghe o colloquiali:** «Chiude presto» (r. 96), «via i sette nomi» (r. 89), «tetto lineare» (r. 18), «nello stesso formato» (r. 117), sintassi ambigua (r. 163, 146), «si riscrivono» senza oggetto (r. 141), il ramo inesistente `feat/link-key-shape` (r. 181), «Parole da allineare» senza destinazione (r. 185), tempi mescolati (r. 52), «su container reale su Modal» (r. 101).
- **style-1-18. Conteggi e forme dei numeri:** «dieci corse Modal in più» (r. 165) sono 12 (10 `suite` più `corpus` in `T1.B` e `T1.D`); cifre e lettere per lo stesso conteggio; «4630 passed, 78 skipped» (r. 82) contro «4630 passati» (r. 15).
- **style-1-19. Legenda delle sigle B, M, I** (r. 7): «B» senza fonte, «M» e «I» con una fonte, poi tutte «rimandano a» un terzo file.

---

## Revisore Implementation Readiness

**Verdetto: non pronto.** Prima di riprendere `T0.A.3` e aprire `T0.B` vanno chiuse le decisioni di readiness-1-1, 1-2, 1-7 e 1-9. 1 Blocker, 10 Major, 3 Nit (14 rilievi; il revisore ne dichiarava 4 Nit, ma ne elenca 3).

**Taratura.** La Regola 1 (r. 34) rimanda per scelta il dettaglio delle tranche non aperte: standard applicato per intero solo a `T0.A` (aperta) e `T0.B` (LIBERA, passi già scritti); per `T0.C`–`T3.C` un rilievo aggregato e uno specifico su `T0.C`. Blocker: la *Verifica* non si valuta o il passo non gira dentro il suo *File* senza una decisione nuova. Major: si esegue tirando a indovinare. Nit: testo vecchio o incoerente.

**Nota di isolamento.** Una Grep su tutto il repository ha restituito due righe di questa cartella; il revisore dichiara di non averle lette oltre né usate.

**Fatti controllati e corretti:** `STEPS` in `daodan/core/pipeline/__init__.py:277`; `no-new-privileges` in `container.py:867, 1113, 1413, 1557`, `leaves` :1355, `reached` :1408; `join_sampled` in `dynamic/__init__.py:248` è percorso morto (nessun registratore emette `sampled`); opzioni e `BASELINE` di `modal.yml:9-33`; `3919-3920 passed, 75 skipped` in `tests/modal_pytest.py:18`; conteggi delle due corse in `docs/verification/2026-11-25-baseline-t0.md:11-12`.

### T0.A

**readiness-1-1 (Major; diventa bloccante in `T0.B.4`). Su quale SHA stanno le due corse coerenti.** r. 46, 82, 75, 38. Tre versioni: «sullo SHA che chiude `T0.A.3`»; `T0.A.2` spuntato su `44462b569` con «si valuterà se riconfermare»; il Cancello cita «le due corse di `T0.A.2`». `T0.A.3` cambia codice (`STACK`, `daodan/core/support_table.py:45`). Buco transitorio: il commit del bot con il nuovo `daodan_stack.json` arriva prima dell'aggiornamento di `STACK`, e nel frattempo `render()` esce con `SystemExit` (`support_table.py:412-415`): in quella finestra `tests/test_codebase_map_support_table.py:15` fallisce su `develop`. *Indicazione:* decidere e allineare r. 46, 75, 82: baseline `44462b569` con la sola corsa mirata di `test_codebase_map_support_table.py` per `T0.A.3`, oppure un passo con due `suite` sullo SHA finale di `T0.A`.

**readiness-1-2 (Major). «Zero perdite non spiegate» e mediana: nessuno strumento fa il confronto.** r. 47, 83. `benchmarks/project-model/test_fork_stack.py:155` legge solo `results/daodan_stack_fork.json`, mai `daodan_stack_fork_develop_68b784e.json`; `benchmarks/project-model/README.md:536` dice che il confronto «non è più nel codice» e si fa leggendo `score.frameworks_by_name.missed` e `score.services.missed`; ogni fixture ha `score.before` e `score.after` (`daodan_stack_fork.json:3`). Senza risposta: quale lato della baseline e quali misure; che cos'è una perdita; chi accetta una spiegazione; dove si scrive (`docs/verification/...` o il README, r. 536). Le «sei fixture del 26 novembre» non hanno nome (probabilmente `real-auth0-go`, `real-bank-of-anthos`, `real-microblog`, `real-next-subscriptions`, `real-sveltekit-realworld`, `real-stack-polar`, non verificabile senza `git log`). I 0,523 s sono il `fork_fast` del rilascio `.2` e `README.md:526` avverte che il confronto con `fast_seconds` «non è uno a uno». *Indicazione:* scrivere la regola (es. perdita = nome in `missed` di `daodan_stack.json` assente da `score.before.<misura>.missed` della baseline, registrata con fixture, nome e motivo in una tabella nominata, accettata dal proprietario); elencare le sei fixture escluse; mediana di `fast_seconds` registrata senza soglia.

**readiness-1-3 (Major). `T0.A.3`: elenco dei file incompleto e ordine dei commit contro la Regola 4.** r. 83, 36-37. Mancano in *File*: `benchmarks/project-model/README.md` (sezioni «Non misurato» e «Verdetto», :518-541, restano «non verificata»), `docs/plans/refactoring.md` (mappa), i due file del bot `results/daodan_stack.json` e `results/daodan_stack_fork_develop_68b784e.json` (`modal.yml:87-102`). Il passo modifica `STACK` e il documento, lancia `modal_pytest.py` e chiude con un solo commit `docs(verification)`, ma la Regola 4 vuole albero pulito e SHA `C` registrato prima di `modal_pytest.py` (`tests/modal_pytest.py:124-128` carica il disco). Sequenza da scrivere: (1) corse CI e `git pull --ff-only`; (2) commit `C` con `support_table.py` e `codebase-map-supporto.md` (codice, non `docs`); (3) `modal_pytest` su `C`; (4) commit con gli esiti. `STACK` è `(file, data, codice)`: il codice è `code.local` del nuovo JSON (`support_table.py:414-415`, `modal_stack.py:349`), la data quella della corsa. *Indicazione:* completare *File*, scrivere la sequenza (tipo `chore` o `fix` per `C`), dire da dove vengono i valori di `STACK`.

**readiness-1-4 (Major). Quarantena di voci che non sono test.** r. 57, 84, 38; `docs/verification/2026-11-25-baseline-t0.md:34`. La Regola 5 chiede il «nome esatto del test», ma Go `replace => ../local` e Composer `path` non sono test; la riproduzione «`modal.yml` `run=corpus`» non dice in quale fixture si vede. Nessun `composer.json` delle fixture ha `repositories`; per Go c'è solo `sys-go-nested/plugins/extra/go.mod` con `=> ../`; i `real-*` si clonano alla corsa (`modal_stack.py:23-25`). La *Verifica* «ogni voce riscontrata nelle corse» può essere impossibile per Composer. *Indicazione:* per ogni difetto fixture e campo che lo mostrano, o una fixture nuova (allargando *File*), o che cosa si registra se la voce non compare; quale colonna sostituisce il «nome del test».

**readiness-1-5 (Nit).** r. 84: `T0.A.4` elenca ancora il caso di `tests/test_codebase_map_app.py`, chiuso a r. 56 e `baseline-t0.md:39`; aggiungere `docs/plans/refactoring.md` a *File* per il contatore `5/5`.

**readiness-1-6 (Nit). Albero pulito e chi esegue.** r. 37, 83. `git status --porcelain -- daodan plugins tests benchmarks docs` non vede file che `modal_pytest.py:127` carica comunque (`README.md`, `AGENTS.md`, `pyproject.toml`, `LICENSE`, `viewer/pipeline/data.ts`), e `T0.B.3` modifica proprio `README.md`. La cartella non tracciata di questa review in `docs/` rende il controllo non vuoto, e la regola non dice che cosa fare dei file estranei. «`support_table.py build` gira sul PC del proprietario» non dice se lo lancia il proprietario o l'agente, né con quale Python (il modulo importa mezzo `daodan/core`, `support_table.py:27-39`). *Indicazione:* allineare i percorsi a `modal_pytest.py:124-128`, dire che cosa fare dei file non tracciati estranei, nominare chi esegue lo script e in quale ambiente.

### T0.B

**readiness-1-7 (Blocker). `T0.B.2` non gira dentro il suo elenco *File*.** r. 88, 73. *File* contiene solo `benchmarks/system-map/README.md`, ma `benchmarks/system-map/modal_map.py:60-66` conosce solo `polar` e `tududi`; `_pairs` rifiuta altri casi (`:927-928`), `_inputs` legge `CASES[name]` (`:936`). Bank of Anthos chiede una voce `CASES` nuova (repository, commit `db35fea9fd090150e2398106aadb475576f80d94` da `source.json:3`, `target`, `tar`). «Il modello debole» non è definito: `modal_map.py:50` offre `haiku`, `sonnet`, `opus`, `qwen`; il README:24 chiama Haiku «economico» e Sonnet «intermedio»; il README:79 vuole Opus per partenza e gate e Qwen sempre come metro. Manca il comando (`spawn` o `whole`; `--rules session|none`, `--scopes system`, `--reps 2`; `--budget`, default 3 USD, `modal_map.py:55`; l'archivio con `code_archive.py OUT.tar REPOSITORY@COMMIT`, che chiede un clone locale a `db35fea`). *Indicazione:* `modal_map.py` in *File* con la voce `CASES` esatta; il modello con l'id di `MODELS`; le righe di comando intere (`modal deploy`, `code_archive.py`, `spawn`, `modal volume get`).

**readiness-1-8 (Major). Il metodo della diagnosi non è scritto.** r. 88. «Flusso atteso mancato» non dice con quale misura (forse `score.py system` con la regola dei due terzi, README:18, 71) né come trattare le due ripetizioni. Le tre domande sì/no non hanno criterio (confronto per file, simbolo o rotta con `links.json`? quale strumento per «un percorso parte da lì», `traces.py`, `possible.py`, `system_map.verify`? come leggere «aperto o proposto» da `stream.jsonl`?). L'elenco delle cause esclude `read_code`, `recognize_stack`, `find_modules`, `run_and_observe`. «In testa il commit»: di Daodan o di Bank of Anthos? Lo stato del riferimento non è dichiarato: README:44 e :83 dicono che un caso non confermato «resta una bozza», README:77 che fino alla conferma vale solo la profondità 1, README:32 che i `real-*` sono scritti a mano il 25 novembre e mai misurati. *Indicazione:* comando di punteggio, regola sulle ripetizioni, strumento per ogni domanda, causa di ripiego; dire se i flussi di `real-bank-of-anthos` sono confermati o se la diagnosi resta a profondità 1.

**readiness-1-9 (Major). Quota nascosta e domande verificate: sei punti aperti.** r. 64, 90, 88, 196, 176. (1) I flussi di `system.json` non hanno `id`, solo `name` (`fixtures/real-bank-of-anthos/system.json:1107-1109`): «gli id ordinati» non ha referente; manca la chiamata (`sample(k)` o `shuffle`, quale `k`, su 27 flussi, README:40). (2) `T0.B.2` scrive una riga per ogni flusso mancato prima dell'estrazione e così espone la quota nascosta. (3) Il Cancello T2 usa «Pagamento a un contatto»: se cade nella quota nascosta non è detto come la si escluda. (4) Il riferimento è in chiaro nel repository: «nascosta» chiede un meccanismo non descritto. (5) Le tre domande stanno «accanto al riferimento» senza file né formato, ma `T2.A` le consuma (r. 176). (6) Il punto 6 parla di «decisione congiunta in `T0.B.4`»: quota e protocollo sono decisi o proposti? *Indicazione:* chiave di ordinamento (`name`), chiamata esatta e `k`; come `T0.B.2` e il Cancello T2 trattano i flussi nascosti e dove sta l'elenco; file e schema delle tre domande; quota e protocollo `[deciso]` o in attesa del proprietario.

**readiness-1-10 (Major). `reference.py pin` fa più di quanto il passo dice.** r. 90. `system.json:6` porta già `commit: db35fea…`, come `source.json:3`. `pin` lega il riferimento allo `HEAD` del checkout dato (`benchmarks/system-map/reference.py:270-281`), quindi su un clone non a `db35fea` lo sposta, e riscrive il file in JSON compatto (`:282`), un diff su tutta una fixture che *File* non elenca. *Indicazione:* `python reference.py check <system.json> <clone a db35fea>`, oppure clone a `db35fea` dichiarato e fixture in *File*.

**readiness-1-11 (Major). `T0.B.3` non dà la forma di arrivo.** r. 63, 89; `docs/plugins/codebase-map.md:190-242`, `README.md:16-39`. Il passo dice «via i sette nomi» e «la corrispondenza del punto 15», ma non che cosa fare della tabella «Dal codice al disegno»: la colonna «Spec 8.11» e le righe citano sezioni della spec rimossa; `codebase-map.md:210` («`plan` come step | Da fare») contraddice `architettura.md:25` e `backlog.md:64`; `README.md` è in inglese. *Indicazione:* colonne della tabella, righe da togliere o riscrivere, lingua del README.

**readiness-1-12 (Nit).** r. 87-88: `T0.B.1` e `T0.B.2` senza messaggio di commit.

### Tranche successive (`T0.C`–`T3.C`)

**readiness-1-13 (Major). La colonna «Scelte aperte da chiudere prima» dice «Nessuna», ma il testo ne lascia aperte almeno tredici**, contro la Regola 1:

| Riga | Tranche | Scelta lasciata aperta |
| --- | --- | --- |
| r. 116 | T1.A | eventuale spostamento come classe di `detect/rules/` |
| r. 118 | T1.A | valore del tetto ai byte |
| r. 123 | T1.A | criterio di riuscita della prova tecnica SQL |
| r. 132 | T1.B | `suffix_table.NAMES` resta o passa a `file_formats.LINGUIST_NAMES` |
| r. 141 | T1.C | `inspectRoutes` di `hono/dev` «da verificare» |
| r. 156 | T1.B | «Da misurare … se il fork accetta» |
| r. 159 | T1.C | «se serve» |
| r. 176 | T2.A | quale campo si aggiunge se si trovano falsi archi |
| r. 180 | T2.B | «eventuale migrazione SQL» |
| r. 185 | T2.C | «Parole da allineare» senza le parole di arrivo |
| r. 209 | T3.A | lo strumento del proxy, scelto da una misura, mentre r. 28 dice «Nessuna» |
| r. 213 | T3.B | «si valuta OpenTelemetry» |
| r. 220 | T3.B | l'ordine «si scrive nei passi di `T3.B`» |

*Indicazione:* riportarle nella colonna di ogni tranche o chiuderle.

**readiness-1-14 (Major). `T0.C`: perimetro host/container e canale dell'approvazione non decisi.** r. 66, 98-101; `architettura.md:513-518`. Dei quattro `npm install` di r. 66, tre sono preparazione nel container e passano dal proxy (`dynamic/app.py:109`, `dynamic/javascript.py:249`, `indexers/components.py:65`); il quarto gira sull'host e il proxy non lo vede (`indexers/runtime.py:247-253`, `npm_install` con `subprocess`, più `_release` da nodejs.org a `:205-214`). `T0.C.3` dice che «anche gli host fissi degli strumenti di Daodan chiedono», ma il confine del contratto è il proxy del container (`architettura.md:515`): non è deciso se i download di Daodan dall'host rientrano, né con quale meccanismo. Aperti anche: il canale fra proxy e GUI (dove stanno le richieste, come «il passo si rilancia dopo il sì»), nome e schema dei file di whitelist e blacklist, la durata di «solo per questa analisi». *Indicazione:* separare host e container nell'elenco di r. 66, decidere il perimetro, aggiungere queste scelte alla colonna di `T0.C` prima del suo dettaglio.

---

## Revisore Codebase Details

2 Blocker, 8 Major, 16 Nit. Solo Read, Grep, Glob; non ha aperto la cartella di questa review.

### Blocker

**codebase-1-1. `T0.A.3` (r. 83, passo aperto): «zero perdite non spiegate» non ha un metodo, e `test_fork_stack.py` non verifica il giro nuovo.** `benchmarks/project-model/test_fork_stack.py:155-164` legge solo `results/daodan_stack_fork.json` (giro del piano 2) e verifica `executed_project_code` e i pin dell'immagine; non legge il nuovo `daodan_stack.json` né `daodan_stack_fork_develop_68b784e.json`: il verde non dice nulla sul passo. Il metodo c'è in `benchmarks/project-model/README.md:536` (per fixture `score.frameworks_by_name.missed` e `score.services.missed` del nuovo `daodan_stack.json` contro `daodan_stack_fork.json` e `daodan_registry.json`, perdite accettate scritte in quel README), ma il piano confronta con `daodan_stack_fork_develop_68b784e.json` senza dire i campi, e lascia fuori da *File* quel README («Verdetto», «Non misurato», r. 518-541) e i file del bot in `results/`. Chi esegue deve inventarsi il confronto (Zero-Decision Rule).

**codebase-1-2. `T0.B.2` (r. 88) non si esegue come è scritto.** `benchmarks/system-map/modal_map.py:60-66`: `CASES` ha solo `polar` e `tududi`; `_pairs` (`:922-930`) rifiuta un `--tar CASE=PATH` fuori da `CASES`; `_inputs`, `spawn`, `whole` (`:933-986`) leggono `CASES[name]`. Serve una voce nuova (repo e commit di `source.json`, o `tar`) in `modal_map.py`, che non è in *File*. «Col modello debole»: `MODELS` (`:50`) ha `haiku`, `sonnet`, `opus`, `qwen`, nessuno nominato.

### Major

**codebase-1-3. Su quale SHA contano le due corse** (r. 46, 82, 75). `T0.A.3` cambia per forza `STACK` (`daodan/core/support_table.py:45`), quindi la condizione «se modifica codice» scatta sempre; il Cancello cita le corse di `T0.A.2`. Chi esegue deve decidere se rifarle.

**codebase-1-4. `T0.B.4` (r. 90): gli «id ordinati» dei flussi non esistono, e `reference.py pin` riscrive un file non in elenco.** In `fixtures/real-bank-of-anthos/system.json` i flussi (da r. 1107) hanno `name` e nessun `id`. `system.json` ha già `commit` uguale a `source.json` (`db35fea9…`). `reference.py pin` (`benchmarks/system-map/reference.py:248-282`) riscrive `system.json` con `json.dumps` senza indentazione (il file diventa una riga) e vuole una copia del progetto come RADICE, senza dire da dove. «Accanto al riferimento» indica un file della fixture: né quello né `system.json` sono in *File*.

**codebase-1-5. r. 66 («[accertato]»): `indexers/runtime.py:251` non usa la rete del container.** `runtime.npm_install` (`daodan/core/indexers/runtime.py:247-253`) è un `subprocess.run` sull'host che installa `@sourcegraph/scip-python` e `pyright` per `indexers/python.py:618, 664, 705, 733`; il proxy di `T0.C` non lo governa, ma il piano lo elenca con `dynamic/app.py:109`, `dynamic/javascript.py:249`, `indexers/components.py:65`, che sono nel container. `T0.C` (punti 1 e 3) deve dire se whitelist e popup valgono anche per i download di Daodan sull'host.

**codebase-1-6. `T1.11` (r. 136): mancano `TEMPLATE_SOURCES`.** `daodan/core/premap/__init__.py:56-60` ha `FRAMEWORK_SOURCES = (nextjs, react_router, nuxt, sveltekit)` e `TEMPLATE_SOURCES = (angular, astro)`, entrambe in `SOURCES` (`:49-51`) e producono `framework_entries`. Il piano sposta solo `FRAMEWORK_SOURCES` e Noir, mentre il Cancello T1 vuole `premap.SOURCES` senza rotte né eventi: Angular e Astro restano senza destinazione.

**codebase-1-7. `T1.4` (r. 120): le lacune sui linguaggi senza analyzer sono due.** `no_analyzer` da `_unlisted` (`premap/__init__.py:258-268`, go-enry) e `no-analyzer` (con il trattino) da `pipeline/plan.py:165-171` sui linguaggi dello snapshot, letta da `engine_pass.no_analyzer` (`daodan/core/engine_pass.py:90-95`). La lacuna nuova di `list_files` deve dire quale sostituisce o come le unisce, altrimenti doppioni o perdite quando go-enry esce.

**codebase-1-8. `T1.15` (r. 145): la corrispondenza non include i nomi degli step di `pipeline/plan.py`.** `pipeline/plan.py` usa già `parse`, `resolve`, `observe` (`:116, 119, 153, 162`), con nodi `parse:<linguaggio>`, `resolve:<analyzer>`, `observe:<observer>` citati nei `needs` (`:152, 164`). «Rimuovere lo step `parse`» si scontra con i nodi `parse:`, che corrispondono a `read_code`.

**codebase-1-9. File senza Create/Modify/Delete** (una volta, regola della persona). Le righe *File* di `T0.A.3`, `T0.A.4`, `T0.B.2`–`T0.B.4` e le liste di T1–T3 non lo marcano; es. `tests/test_codebase_map_language_cost.py` esiste già (`T1.3`), `daodan/data/build-tools.json` e `benchmarks/stack-build-tools/` no.

**codebase-1-10. r. 211 (`T3.1`, «[accertato]») contraddice in parte il codice** (declassato da Blocker perché `T0.C.4`, r. 101, dice correttamente che quelle prove si saltano senza la variabile). Il piano dice che `tests/test_codebase_map_container.py` verifica argomenti CLI e tre rifiuti, «non un container reale»; il file ha `RealEngineSmokeTest` (`:1242-1290`, su motore vero: `--network none` blocca `example.com`, la rete `registries` raggiunge `pypi.org`, con `DAODAN_CONTAINER_SMOKE=1`), `test_on_modal_apt_updates_…` (`:1190-1213`, Modal con proxy e apt veri) e altri rifiuti oltre ai tre (`:771-776`).

### Nit

- **codebase-1-11.** r. 53: `service-registry.json:2631-2656`; `avro` occupa 2630-2645, da 2646 c'è `aws`.
- **codebase-1-12.** r. 56: `614c940:2026-11-21-stack-dal-fork.md` non è un percorso valido per `git show` (verosimilmente `docs/specs/…`).
- **codebase-1-13.** r. 37: `git status --porcelain -- daodan plugins tests benchmarks docs` non copre `AGENTS.md`, `pyproject.toml`, `README.md`, `LICENSE`, `viewer/pipeline/data.ts`, che `tests/modal_pytest.py:127-128` carica.
- **codebase-1-14.** r. 36 e 3: `viewer.yml` copre anche `daodan/assets/**`, `AGENTS.md`, `CLAUDE.md`, ma non parte per `daodan/core/pipeline_tree.py`.
- **codebase-1-15.** r. 66 e 99: «il `retry` di `container_runner.py`» e «il secondo tentativo di Gradle» sono lo stesso meccanismo (`premap/container_runner.py:148`, `:274-282`; `premap/gradle.py:70`); se si intende la seconda corsa sul JDK (`container_runner.py:291-308` o `indexers/jvm.py:731-813`), va nominata.
- **codebase-1-16.** r. 84: `T0.A.4` elenca ancora il caso di `tests/test_codebase_map_app.py`, chiuso.
- **codebase-1-17.** r. 18: la mappa riporta ancora «collegamento `header.py`», già fatto (`languages/__init__.py:34, 115`); `T1.1` («eventuale spostamento») lascia una scelta aperta.
- **codebase-1-18.** r. 132: `suffix_table.run` non è già più in `SOURCES`; `file_formats.LINGUIST_NAMES` (`file_formats.py:28`, `dict[str, tuple]`) ha forma diversa da `suffix_table.NAMES` (`dict[str, str]`); togliere go-enry da `pipeline_tree.py` (`:112, 256`) obbliga a rigenerare `viewer/pipeline/data.ts` (`pipeline_tree.py:33`) e `docs/pipeline/`, che il piano non dice.
- **codebase-1-19.** `T1.15`, `T1.16`: la funzione è `pipeline.plan.plan` (`pipeline/plan.py:128`), non `pipeline.plan`.
- **codebase-1-20.** r. 176: «Modello di evidenza» non è un titolo di `architettura.md`, ma un punto elenco (`:57`).
- **codebase-1-21.** r. 182: il test da riscrivere è `test_a_framework_a_module_declares_is_in_its_stack_open_or_closed_and_never_a_node_and_a_tool_or_a_mention_is_not` (`tests/test_codebase_map_app.py:672`).
- **codebase-1-22.** r. 210: anche il pod (`container.py:1582`) e la sonda di `leaves` (`:1360`) non hanno `no-new-privileges`; `--cap-drop` e `--user` solo nei quattro punti li lasciano fuori.
- **codebase-1-23.** r. 213: `join_sampled` non ha produttori ma è collegato in più punti (`dynamic/__init__.py:726-738`, `:93, 103, 793, 810-818`, `dynamic/execution_cache.py:120`, `code_graph.py:1156`): toglierlo tocca più della r. 248.
- **codebase-1-24.** r. 212: le chiavi `starts` e `builds` esistono già (`premap/npm_start.py:152`, `premap/dockerfile.py:82`); lo stato di partenza non è scritto.
- **codebase-1-25.** `T0.B.1` e `T0.B.2` senza *Commit*.
- **codebase-1-26.** Lettori a espressioni regolari oltre a `sql.py`, `plsql.py`, `build_units.py`: `premap/cmake.py:74` (`PROJECT`, `COMPILER` a `:136`) e `preparation.python_vcs` (`VCS_URL`, `VCS_SOURCE` a `:646-647`).

### Non verificabile in sola lettura

Il contenuto di `66e09dbca~1:docs/specs/2026-11-25-refactoring-completo.md` e della spec a `614c940` (i commit `44462b569`, `78e070129`, `7670c2bad`, `66e09dbca`, `68b784e`, `614c940`, `2d6a2881d` esistono in `.git/logs/HEAD`; il ramo `feat/link-key-shape` non è nei ref); gli ID delle corse GitHub e Modal e i conteggi 4630, 78, 1416 (coincidono con `docs/verification/2026-11-25-baseline-t0.md`); le 768 tessere, i 180 e 122 progetti, le regole Go e Composer del fork esterno; i componenti di Sigrid e Imago (`viewer/node_modules` manca).

### Verificato conforme

Workflow (`modal.yml` con `suite`, `proof`, `corpus`, `baseline`, segreti, commit del bot, `BASELINE` = `68b784e`, file di baseline assente; `desktop.yml` e `release.yml`); `tests/modal_pytest.py:18` e `:27-28`; registro e tecnologie (`apply_marks`, `_is_tile`, `"simple_icon": "doctrine"`, `"cncf": "Avro"`, `avro-cncf` sparito, `technologies.py:341-352`, test del registro e di Playwright); pre-mappa, snapshot e review (35 `SOURCES`, `join`, `derive`, `write`, `EXECUTES` con `mix-project`, `python_runs`, `_unlisted`, 27 test `premap*`, `WRAPPER_SELF`, `WRITTEN_ELSEWHERE`, `libs.versions.toml`, `Directory.Packages.props`, `external_packages`, `angular-project`, `nx-project`, `WORKING_RUN`, `query_gate`, `refresh_working`, `_refresh_locked`, le tre funzioni oltre 80 righe, l'hook, le righe di senior-review, `whole-source-coverage/README.md:54-86`); container e preparazione (`PROXY_SCRIPT`, `leaves:1355`, `reached:1408`, r. 867, 1113, 1413, 1557, `RESTORES` con `--ignore-scripts`, `node_prepare` con gli script, `declared`, `python_vcs`, `TOOLS`, `daodan-enry`); pipeline e codice di T2–T3 (`STEPS`, nodi e `blocked`, nessun `approval_required`/`host_denied`, `edge_grading`, `edge_store`, `resolve_edges`, `KotlinResolver.kt`, `typescript_unbound.js`, registratori, `/api/stream`, `/api/app/*`, `viewer/app/run.ts`, `stages.ts`); benchmark e titoli (Syft 1.57.1, 360 contro 673, +1.827; verdetti Django, FastAPI, Flask, Express; sezioni citate).

---

## Convergenze dello stadio 9

| Tema | Rilievi | Revisori indipendenti |
|---|---|---|
| SHA delle due corse coerenti di T0 (tranche aperta) | style-1-1 (Blocker), readiness-1-1, codebase-1-3 | 3 |
| «Zero perdite non spiegate» senza metodo; *File* di `T0.A.3` incompleto | readiness-1-2, 1-3, codebase-1-1 (Blocker), style-1-3 | 3 |
| `T0.B.2` non eseguibile (`CASES`, modello, comando) | readiness-1-7 (Blocker), codebase-1-2 (Blocker) | 2 |
| `T0.B.4`: flussi senza `id`, `reference.py pin` riscrive la fixture | readiness-1-9, 1-10, codebase-1-4 | 2 |
| `npm install` sull'host fuori dal proxy di `T0.C` | readiness-1-14, codebase-1-5 | 2 |
| «Scelte aperte» = «Nessuna» ma scelte aperte nel testo | readiness-1-13, style-1-5 | 2 |
| `T0.A.4` cita un caso già chiuso | style-1-2, readiness-1-5, codebase-1-16 | 3 |
| Albero pulito della Regola 4 non copre ciò che `modal_pytest.py` carica | readiness-1-6, codebase-1-13, style-1-8 | 3 |
| Numerazione e `T0.7` attribuito a `T0.B` | style-1-4; CO-9 (stadio 6) | 2 |

**Nuovi solo in questo stadio (un revisore):** codebase-1-6 (`TEMPLATE_SOURCES` di Angular e Astro senza destinazione), 1-7 (due lacune `no_analyzer`/`no-analyzer`), 1-8 (nodi `parse:` del piano unico contro «rimuovere `parse`»), 1-10 (`RealEngineSmokeTest` esiste); readiness-1-4 (quarantena di voci che non sono test), 1-8 (metodo della diagnosi cieca), 1-11 (forma di arrivo di `T0.B.3`); style-1-6 (punti e passi di T0 divergono), 1-10 (`T0.A.3` in una frase).

**Totale stadio 9:** 4 Blocker, 28 Major, 27 Nit (59 rilievi). Verdetto del revisore di prontezza: **non pronto** per `T0.A.3` e `T0.B` finché non sono chiusi lo SHA delle corse, il metodo del confronto e il comando di `T0.B.2`.
