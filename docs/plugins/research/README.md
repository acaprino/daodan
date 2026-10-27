# Research

Ricerca web e base scientifica del progetto. `science-based-approach` collega
paper letti, decisioni e verifiche locali; `team-research` conserva la ricerca
web approfondita con ricercatori separati.

## Primo utilizzo

1. Esegui `/research:science-mode`: senza configurazione il risultato è ON.
2. Esegui `/research:science-research confronta due strategie di cache per questo servizio`.
3. Apri la pagina corrente collegata da `docs/research/README.md`: resta lo stesso file agli aggiornamenti successivi.

Prima di creare un documento, la skill cerca ricerche affini anche tra i Markdown
non indicizzati. Se riprendi un tema, usa quella ricerca. Nuove evidenze aggiornano
lo stesso file con timestamp, passaggi superati barrati e changelog descrittivo;
le copie storiche non diventano altre pagine correnti.

I comandi sono espressi nella notazione Claude. Codex li espone come skill
`science-mode-workflow`, `science-research-workflow` e
`update-research-workflow`; gli altri host seguono la
[guida host](../../hosts.md). Gli esempi descrivono l'uso, non una ricerca già eseguita.

| Documento | Contenuto |
|---|---|
| [Specifica funzionale](functional-spec.md) | Comandi, modalità, risultati ed errori |
| [Specifica tecnica](technical-spec.md) | Archivio, runtime, hook e confini |
| [Casi d'uso e tutorial](use-cases.md) | Nuova ricerca, aggiornamenti e on/off |
| [Base documentale](research/README.md) | Fonti della progettazione e limiti |
| [Validazione](validation.md) | Prove eseguite e verifiche mancanti |
| [Dipendenze](dependencies.md) | Provider, strumenti e recupero |
| [Provenienza](intakes.md) | Codice originale e servizi consultati |
| [Licenze](licenses.md) | Confini della distribuzione e attribuzioni |

La [specifica approvata](specs/2026-10-27-science-based-approach.md) conserva
le decisioni di progetto. Il [template](../../../plugins/research/skills/science-based-approach/templates/research.md)
è distribuito con la skill. La [guida team-research](../research.md) mantiene
il dettaglio del flusso web preesistente.
