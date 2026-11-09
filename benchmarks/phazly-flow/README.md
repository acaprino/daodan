# Benchmark: un bug di flusso reale, review per area

Prova se senior-review trova, in una review per area e non per commit, un bug reale di phazly-app: un fatto registrato sullo slot del diario (record presente) letto come fatto sul piatto del piano (piatto mangiato). Il codice di phazly-app non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| target | phazly-app al commit `46c92b28`, il genitore della prima fix, copiato senza storia successiva: i messaggi delle fix non sono leggibili |
| difetto atteso | G1 `react-app/src/hooks/useDayProgress.ts:190`: la riga del piano è fatta per un record qualsiasi nello slot. G2 `react-app/src/components/common/QuickAddSheet.tsx:268`: l'offerta «Dal piano» sparisce per un record qualsiasi. Fix: `b511e814`, `239819dd` |
| criterio | trovato se un finding consegnato nel rapporto afferma, con `file:line`, che un record dello slot è usato come «piatto del piano mangiato»; parziale se compare solo in un job o come lead |
| plugin | Daodan al commit `cf0ffe6`, installato dalla checkout locale |
| esecuzione | `claude -p` 2.1.319, una sessione nuova per run, modello `claude-sonnet-5-5`; strumenti: Read, Glob, Grep, Write, Edit, sotto-agenti, Skill, Bash solo per `python3`, `uv`, `git` in lettura e `ls` |
| mappa | `/codebase-map:map` lite su `react-app/` (630 file, 590 con simboli) |

## Run del 2026-11-09

| Run | Richiesta | Metodo | Job | G1 | G2 | Costo | Tempo |
|---|---|---|---|---|---|---|---|
| mappa | lite di `react-app/` | analista isolato, pubblicata | 1 | – | – | 2,06 USD | 548 s |
| A | widget della home, in parole | saltato: il modello revisiona da solo e lo dichiara solo alla fine | 0 | no | no | 1,04 USD | 207 s |
| A2 | A, con il metodo nominato | si ferma sul prerequisito della mappa dell'intero progetto e propone due strade | 0 | – | – | 0,34 USD | 37 s |
| A3 | A2, con la deroga: solo `react-app` | completo, 12 job, 81 finding, 21 cluster | 12 | parziale | fuori perimetro | 15,09 USD | 981 s |
| B | inserimento e scansione, metodo e deroga | completo, 49 job | 49 | no | no | 26,16 USD | 772 s |

- A: il revisore legge per intero il file di G1 e scrive che i tombstone sono esclusi in modo uniforme; il difetto non compare.
- A3: il job `logic-integrity` descrive G1 esattamente («uno slot che contiene solo un alimento estraneo è annunciato come completato e il piatto del piano non si può più registrare»). Il consolidamento lo fonde nel cluster L2 «un pasto saltato è mostrato Completato», Low, con altri cinque finding sulla stessa ancora: il caso del cibo estraneo sparisce dal rapporto. Con rigor standard nessun Low è verificato. `QuickAddSheet` non entra nel perimetro dei widget.
- B: `QuickAddSheet` e `useDayProgress` sono nel perimetro. `01-context.md` del coordinatore afferma che non esiste un tipo «planned»: vero per il record dello slot, falso per le sue aggiunte, che hanno `type: 'planned'`. Il job che legge la riga di G2 la descrive come comportamento voluto.
- In A3 un job segnala lo stesso schema in `useDayLogSlots.ts` (proposta del piano solo su uno slot senza record), ancora presente nell'HEAD di phazly-app dopo le fix: da verificare con l'autore.
- Rifiuti di strumenti: 17 nella mappa, 30 in A3, 64 in B, quasi tutti comandi Bash fuori lista; due job di A3 non hanno letto il file del proprio ruolo.

## Diagnosi

I reviewer vedono il difetto quando leggono chi scrive il fatto e cosa afferma la schermata; lo perdono quattro passi del metodo, non un ruolo mancante:

1. **Ingresso.** Una richiesta in parole può saltare l'intero metodo senza dichiararlo all'inizio (A).
2. **Contesto.** Un'affermazione sul modello dei dati senza livello («nessun tipo planned») si propaga a tutti i worker (B).
3. **Consolidamento.** Il raggruppamento per ancora fonde finding con la stessa riga e trigger diversi; il trigger più grave sparisce dal titolo (A3).
4. **Perimetro.** I lettori dello stesso fatto in altre aree restano fuori (G2 in A3).

Limite: una run per richiesta, un modello, permessi ristretti.
