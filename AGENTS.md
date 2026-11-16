# Daodan

## Principi di lavoro

- **Minimalismo, semplicità e token saving sono il mantra del progetto.**
- Usa il modello più piccolo che rappresenta il requisito: non aggiungere campi, contratti, fasi o astrazioni finché un'esigenza concreta non li giustifica.
- Riusa strutture e strumenti esistenti; evita duplicazioni, sinonimi per lo stesso concetto e documentazione che ripete ciò che è già chiaro altrove.
- Progetta per stabilità, pulizia, eleganza e manutenibilità: moduli coesi, responsabilità chiare, interfacce piccole e dipendenze esplicite. Usa pattern consolidati quando semplificano un'esigenza concreta.
- Mantieni il nucleo applicativo indipendente da UI, trasporti HTTP/MCP e motori LLM; gli adattatori riusano la stessa logica applicativa.
- Gestisci esplicitamente errori, timeout e ciclo di vita di processi e risorse; verifica i percorsi di errore rilevanti con test mirati.
- Il codice del progetto analizzato gira solo nel container di Daodan, mai sull'host: build, build script, macro, generatori, plugin, configurazioni che sono codice, installazioni con script e test. Ogni strumento che Daodan lancia sull'host ha un test che lo prova su un file del progetto che, se eseguito, lascia un segno.
- Mantieni prompt, brief e documenti essenziali: esempi solo quando chiariscono un comportamento, elenchi brevi, niente riepiloghi ridondanti.
- Fai interventi circoscritti e verificabili. Distingui sempre comportamento attuale, proposta e gap senza trasformare la completezza formale in lavoro non necessario.
- Prima di modificare, riassumi in una frase cosa chiede la richiesta e perché; se non riesci, chiedi.
- Stile e formato sono del linter o formatter configurato, non delle review.
- Ogni regola di questo file è verificabile e vale per ogni compito; il resto vive nel metodo che lo usa.
- Le spec si mettono alla prova in `benchmarks/`: ogni benchmark dichiara nel suo README i parametri da provare e i risultati misurati.

## Come rispondere

- Prima riga: l'azione da fare, con percorso o comando.
- Più passi: lista numerata, un'azione per passo, al massimo cinque.
- Ultima riga: un solo passo successivo, fattibile in due minuti.
- Niente preamboli, riepiloghi o chiusure di cortesia; errori in tono neutro, con causa e rimedio.
