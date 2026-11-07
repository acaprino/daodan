# Findings: benchmark scope resolution

Numeri per caso in `model-runs/SUMMARY.md`. Cronologia completa nel ledger del piano.

## Spec

1. **Una modifica coinvolge i chiamanti.** Col solo criterio di pertinenza Opus ha escluso `service.py` su C1 in 2 prove su 2; con la frase «a request about a change includes the callers it affects» lo include. Errore riproducibile su un requisito dell'utente: è l'unico caso che ha giustificato una frase in più.
2. **`resolved` o `partial` resta un giudizio.** Haiku sceglie `partial` su C2 e C3b per lacune che la richiesta non chiedeva; riformulare `partial` non l'ha cambiato. Non si insegue: i due esiti proseguono con gli stessi file, cambia solo la lacuna registrata.
3. **Le frasi per casi singoli non servivano.** Tolte quelle su simbolo senza chiamanti, copia locale ed elenco troncato: entrambi i modelli trovano `refunds.py` su C8 e Opus chiude C3b col solo `refunds.py`. Le «ambiguità» riportate dalle sessioni sono giudizi normali, non errori.
4. **Il budget non frena il modello forte.** «Circa 6» query: Haiku media 5.7, Opus 8.4 con massimo 13; Opus supera 6 query in 7 casi su 9. Testo non cambiato: il costo è da valutare.

## Strumenti (verificati sul run)

5. **Le costanti Python a livello di modulo non sono simboli.** `outline` non le elenca, `symbols_at` dà la lacuna `outside-symbols`, `edit_impact` le mette in `unknown_targets`. Si trovano con `search` e si confermano con `read`.
6. **`read` col solo percorso non mostra i corpi delle funzioni**, solo le righe fuori dai simboli. Servono `symbols`, `ranges` o `full_file`.
7. **`search` indicizza i docstring e spezza gli identificatori in sottotoken:** `search("VAT_RATE")` mette in testa `rates.py::shipping_rate`. Limite massimo 100.
8. **I path del manifest sono relativi alla radice git** quando il target è una sottodirectory (prefisso `benchmarks/scope-resolution/app/`).
9. **Gli import tra package restano irrisolti** (`import-target-missing-or-ambiguous`). Il benchmark li evita con import relativi: questo limite non è misurato.
10. **Le sessioni in parallelo trovano il lock del progetto occupato.** `mapcli.py` ora ritenta senza contare la chiamata.

## Benchmark

11. **I commenti della fixture suggerivano le risposte** («distinto dallo sconto cliente», «dipendenza accessoria», «caso C7», `KeyError: 'pay_online'`); una sessione ha citato uno di questi commenti per decidere. Tolti: solo m5 e m6 contano. Con la fixture pulita Haiku passa su C2 da `resolved` a `partial`.
12. **Tre attese erano sbagliate:** C3 richiedeva `__init__.py` vuoto, C6 aveva una destinazione confermabile per lettura, C7 misurava il limite scelto dal modello. Corrette.
13. **L'attesa di C8 è cambiata tre volte** (incompleto, risolto, entrambi), le ultime due dopo aver visto le sessioni: non è indipendente dal modello.
14. **Il resolver misura il protocollo, non il perimetro:** precision media 0.53 contro 0.82 e 0.90 dei modelli. Le sue parole chiave sono un'approssimazione: con formulazioni diverse C6 cambia esito. Il filtro `anchor-in-read` è stato provato e tolto (perdeva `service.py`).
15. **Alcune regole di `tracecheck.py` sono più strette della spec** (esclusione solo dopo lettura, nessun residuo con `resolved`, budget esatto, nessun nuovo tentativo dopo un errore): restano misurate come convenzioni, non come requisiti.

## Affermazioni sbagliate corrette

16. «Spec corta validata col modello»: era falso. Le sessioni m3 avevano provato il testo a 4 blocchi, con accenti rovinati nel brief.
17. «Sessioni su claude-sonnet-5-5»: mai verificato. Il modello di m1-m3 non è registrato.
18. `symbols_at` sulla riga di `VAT_RATE` restituisce `VAT_RATE`: falso, restituisce una lacuna. Falsi anche gli esempi della prima `tools-guide.md`, scritti senza eseguirli; ora sono provati, tranne `stale_callers` e `scope`, che riprendono `mcp.md`.
19. «7 casi su 9 con il solo testo della spec» nel README di senior-review: era calcolato dopo aver corretto le attese sulle risposte viste. Sostituito con i numeri di m5 e m6.
20. «Conteggi auto-dichiarati inaffidabili»: infondato. Le differenze venivano da come contavo outline e letture ripetute; sommati allo stesso modo, i conteggi controllati tornano.
