---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Rendi più naturale questa risposta nel ticket, in italiano e registro business.
Restituisci il report completo, senza voto. Non modificare alcun file di progetto.

Contesto della conversazione (non fa parte della risposta da riscrivere):
Il destinatario ha appena scritto: «Qui gestiamo solo il cliente N. Per la
correzione generale apriamo un ticket separato. Manteniamo il workaround».

Testo da riscrivere:
Come hai giustamente osservato, questo ticket riguarda esclusivamente il cliente N
e la correzione generale deve essere tenuta separata, mantenendo il workaround.
Dalle verifiche in QA risultano 8 record duplicati; in produzione non abbiamo
ancora verificato. Il servizio è condiviso con altri 2 clienti. La causa potrebbe
essere il retry, ma non è confermata. Propongo pertanto di mantenere qui il
workaround e aprire un ticket separato per il servizio condiviso e gli 8 record.
La verifica in produzione deve precedere qualsiasi correzione dei dati.
Fammi sapere se approvi l'apertura del ticket separato.
