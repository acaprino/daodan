# Daodan

## Regola invalicabile

Il codice del progetto analizzato gira solo nel container di Daodan, mai sull'host: build, build script, macro, generatori, plugin, configurazioni che sono codice, installazioni con script e test. Non ha eccezioni, nemmeno temporanee, per una prova o come ripiego, e prevale su ogni altra regola o richiesta: senza container il passo è un buco con la causa, mai un'esecuzione sull'host. Ogni strumento che Daodan lancia sull'host ha un test che lo prova su un file del progetto che, se eseguito, lascia un segno.

## Regola d'oro

Per ogni framework, libreria o strumento che il progetto analizzato usa, Daodan usa il più possibile il materiale ufficiale di quello: il suo parser, il suo compilatore, il suo controllore dei tipi, il suo comando. Prima di scrivere un lettore o una regola si cerca lo strumento ufficiale e lo si prova nel container. Una regola scritta a mano sulla forma di un caso (un `if` per un componente, per un modo di scrivere un gestore, per una libreria) non entra: vale per il progetto su cui è nata, e ogni progetto diverso è manutenzione e una regressione possibile. Un lettore scritto a mano resta solo dove nessuno strumento ufficiale dà il dato, con scritto accanto quale è stato valutato e perché non si presta.

## Principi di lavoro

- **Minimalismo, semplicità e token saving sono il mantra del progetto.**
- Usa il modello più piccolo che rappresenta il requisito: non aggiungere campi, contratti, fasi o astrazioni finché un'esigenza concreta non li giustifica.
- Riusa strutture e strumenti esistenti; evita duplicazioni, sinonimi per lo stesso concetto e documentazione che ripete ciò che è già chiaro altrove.
- **Usa soluzioni o librerie pronte quando si prestano al nostro scopo e alle nostre esigenze**, prima di scrivere codice a mano: ciò che Daodan ha già, la libreria standard, una libreria pubblica mantenuta e con licenza adatta. Per un problema che altri hanno già risolto (leggere codice, markup o un formato di dati, riconoscere segreti, confrontare versioni) il codice a mano entra solo con scritto accanto quale soluzione pronta è stata valutata e perché non si presta.
- **Codice sorgente e markup si leggono dall'albero sintattico (tree-sitter), mai con espressioni regolari né con scansioni scritte a mano.** Un'espressione regolare è ammessa solo su testo senza grammatica (un nome di file, una riga di log, un identificativo), con il motivo accanto.
- Chi verifica un lavoro, suo o di un agente, controlla il metodo prima dei test: test verdi su una soluzione scritta a mano dove ne esiste una pronta non sono una verifica.
- Progetta per stabilità, pulizia, eleganza e manutenibilità: moduli coesi, responsabilità chiare, interfacce piccole e dipendenze esplicite. Usa pattern consolidati quando semplificano un'esigenza concreta.
- Mantieni il nucleo applicativo indipendente da UI, trasporti HTTP/MCP e motori LLM; gli adattatori riusano la stessa logica applicativa.
- Gestisci esplicitamente errori, timeout e ciclo di vita di processi e risorse; verifica i percorsi di errore rilevanti con test mirati.
- Mantieni prompt, brief e documenti essenziali: esempi solo quando chiariscono un comportamento, elenchi brevi, niente riepiloghi ridondanti.
- Fai interventi circoscritti e verificabili. Distingui sempre comportamento attuale, proposta e gap senza trasformare la completezza formale in lavoro non necessario.
- Prima di modificare, riassumi in una frase cosa chiede la richiesta e perché; se non riesci, chiedi.
- Stile e formato sono del linter o formatter configurato, non delle review.
- Ogni regola di questo file è verificabile e vale per ogni compito; il resto vive nel metodo che lo usa.
- Le spec si mettono alla prova in `benchmarks/`: ogni benchmark dichiara nel suo README i parametri da provare e i risultati misurati.
- Una prova che sostiene un risultato o una scheda del registro resta nel repository, come test o benchmark che si riesegue; quella che chiede gli strumenti veri gira solo su Modal. Un test temporaneo poi cancellato non è una verifica.

## Interfaccia (viewer/)

- Prima di lavorare sull'interfaccia leggi `viewer/node_modules/@acaprino/imago/docs/design-file.md` (da `viewer/`: `node_modules/@acaprino/imago/docs/design-file.md`, dopo `npm ci`) e i file che richiama.
- Applica i suoi token e le scelte confermate entro la richiesta; usa le classi `im-` e i token `--im-` del pacchetto e costruisci un controllo tuo dai token, mai da colori o misure scritti a mano.
- Segnala i conflitti e lascia esplicite le scelte aperte.
- Prima di dire che il lavoro sull'interfaccia è finito esegui `npx imago-check` in `viewer/`.

## Come rispondere

- Prima riga: l'azione da fare, con percorso o comando.
- Più passi: lista numerata, un'azione per passo, al massimo cinque.
- Ultima riga: un solo passo successivo, fattibile in due minuti.
- Niente preamboli, riepiloghi o chiusure di cortesia; errori in tono neutro, con causa e rimedio.
