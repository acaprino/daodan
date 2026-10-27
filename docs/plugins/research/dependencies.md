# Dipendenze

| Componente | Necessità e scopo | Recupero |
|---|---|---|
| work-controller | Provider locale richiesto: disciplina, home comune e run | Rendere disponibile il provider con il normale meccanismo dell'host |
| Python | Runtime locale della modalità, archivio e hook; sola standard library | Rendere `python` disponibile al processo dell'host |
| Ricerca/fetch dell'host | Lettura di paper e documentazione online | Segnalare unavailable se non accessibile; nessuna prova online inventata |
| serper.dev | Backend opzionale già esistente per team-research e ricerca | Usare il backend nativo senza introdurre nuove credenziali |
| Hook nativi | Opzionali; generati per Claude e Codex | Abilitare il plugin e completare l'eventuale verifica di fiducia dell'host |

`project-delivery` e `project-knowledge` consumano research. Il provider
scientifico non dipende da questi consumer né dal proprietario dei test.
L'archivio conserva protocolli/risultati; l'esecuzione di test del prodotto
resta al proprietario del compito.

I dettagli di backend del flusso web restano nella [guida esistente](../research.md).
[Provenienza](intakes.md) e [licenze](licenses.md) distinguono codice locale
e servizi consultati.
