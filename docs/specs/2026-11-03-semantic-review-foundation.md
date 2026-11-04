# Codebase Map e review semantica

Data: 3 novembre 2026.

**Perimetro richiesto dall'utente:** backup integrale del precedente Daodan, ripartenza da zero, due soli proprietari — Codebase Map e senior-review — e nessuna storia Git precedente nel nuovo repository locale. Semplicità, portabilità e riduzione dei token sono obiettivi da misurare.

**Stato tecnico:** i kernel sorgente di Codebase Map 1.0.1 e senior-review 1.0.1 sono stati importati dal backup come baseline e i loro manifest sono stati adattati alla base a due proprietari. Nessun selettore qui descritto è già implementato o validato; i plugin importati non sono installabili, integrati o validati. I metodi legacy possono conservare riferimenti storici a host, comandi o plugin precedenti, quarantenati e inattivi finché non vengono adattati o rimossi. La ripartenza autorizzata non equivale all'approvazione di ogni scelta tecnica sotto.

## Struttura

```text
Daodan
├── codebase-map     comprensione del codice e recupero del contesto
└── senior-review    domande, micro skill e composizione della review
         └── usa codebase-map
```

Codebase Map funziona da solo. senior-review usa la mappa e possiede direttamente le proprie micro skill: nessun skill-catalog, work-controller o router dei modelli come dipendenza. I manifest importati rispettano ora questo vincolo; le istruzioni obbligatorie verso plugin assenti sono state rimosse o trasformate in lacune esplicite, mentre i riferimenti storici residui non sono dipendenze attive. Strumenti, modello e capacità di esecuzione appartengono all'host. Un'integrazione futura deve dimostrare la compatibilità sul relativo host; il testo portabile di un metodo non la prova.

## Come si compone una review

1. **Comprendere la modifica nel suo contesto.** La mappa parte dalla richiesta e dal diff, oppure dal perimetro esplicito di un audit senza diff. Recupera sorgenti, chiamanti, contratti, effetti e test pertinenti. Distingue fatti statici, descrizioni semantiche supportate dal codice e ipotesi. Ogni riferimento contiene percorso, intervallo di righe e versione del contenuto.
2. **Formulare le domande da verificare.** Il modello usa il contesto per indicare i comportamenti che possono rompersi: per esempio un evento ripetuto che duplica una scrittura. Ogni domanda ha una ragione legata al codice. Linguaggio e framework orientano la ricerca; da soli non attivano una squadra o un manuale.
3. **Selezionare le micro skill applicabili.** La baseline essenziale di ciascun linguaggio, framework o runtime effettivamente coinvolto è obbligatoria; se una baseline necessaria non è disponibile, la lacuna viene dichiarata. Ai controlli di baseline si aggiungono quelli specialistici attivati dai costrutti e dai comportamenti presenti. Ricerca testuale, collegamenti della mappa ed eventuali embedding trovano candidati. Il modello legge il contenuto dei candidati e le sorgenti pertinenti prima di decidere: applicabile, non applicabile oppure evidenza insufficiente. La somiglianza di un embedding non decide la rilevanza. Una domanda senza skill corrispondente rimane esplicita e può essere verificata con un incarico specifico; non si inventa una skill disponibile.
4. **Comporre il lavoro necessario.** Domande compatibili e contesto condiviso possono stare nello stesso incarico. Un reviewer aggiuntivo serve quando occorrono contesti separati, competenze non coperte o una verifica indipendente giustificata. Il brief contiene domanda, sorgenti, sole istruzioni selezionate e risultato atteso. Il numero di skill non determina il numero di agenti. Il funzionamento di base resta possibile con un unico agente; delega e parallelismo usano soltanto capacità reali dell'host.
5. **Verificare e rendere visibili le lacune.** Il reviewer legge le sorgenti decisive e usa test o altri riscontri quando pertinenti e disponibili. Un finding richiede evidenza e conseguenza concreta. Le domande restano verificate, non applicabili o aperte con il motivo. Se emerge nuova evidenza si amplia il contesto; un limite di tempo o contesto produce una lacuna dichiarata. Il rapporto finale è unico.

La copertura delle domande già individuate è verificabile; la completezza delle domande individuate dal modello non è garantita. «Tutto e solo ciò che serve» è l'obiettivo della valutazione, non una proprietà assicurata da un punteggio semantico.

## Che cosa contiene una micro skill

Un controllo riutilizzabile su un problema preciso, con cinque elementi: domanda, condizioni di applicabilità, evidenza necessaria, modo di verificare e criterio del risultato. La provenienza identifica la versione letta. Il corpo resta breve e leggibile; nomi e tag non ne sostituiscono il contenuto.

Esempi di possibili unità iniziali, non un catalogo completo:

| Domanda | Contesto che la rende utile |
| --- | --- |
| Un evento ripetuto può duplicare un effetto? | Retry, webhook o messaggi che provocano effetti persistenti |
| Due esecuzioni possono acquisire lo stesso lavoro? | Stato condiviso, concorrenza e acquisizione non atomica |
| L'utente può agire su una risorsa di un altro utente? | Confine di autorizzazione e identificatori controllati dal chiamante |
| Una risposta vecchia può sovrascrivere lo stato nuovo? | Operazioni asincrone che aggiornano uno stato condiviso |

Una micro skill può essere orientata a un problema comportamentale oppure a un linguaggio, framework o runtime: le due dimensioni sono complementari. La baseline di stack resta breve e contiene controlli essenziali; i costrutti e i comportamenti del diff attivano controlli specialistici aggiuntivi. In un progetto Rust, Tauri e React, una modifica che attraversa tutti e tre gli stack richiede le rispettive baseline, oltre alle skill specialistiche pertinenti.

Una guida completa a TypeScript o React non è una micro skill. Un controllo di idempotenza può essere pertinente in linguaggi diversi; due file dello stesso linguaggio condividono la baseline ma possono richiedere controlli specialistici completamente diversi.

### Esempio illustrativo

Una modifica a un webhook aggiorna le scorte. Il flusso consente riconsegne dello stesso evento e due richieste contemporanee.

La mappa collega il gestore, il riconoscimento dell'evento e la scrittura delle scorte. Da queste evidenze derivano almeno due domande: se una riconsegna duplica l'effetto e se due richieste possono superare insieme il controllo di unicità. La selezione cerca i due controlli pertinenti e legge le relative sorgenti. Un solo reviewer può trattarli se il contesto rimane gestibile; il linguaggio del file non aggiunge automaticamente altri reviewer.

La scritta «pagamento ricevuto» in una stringa di interfaccia non basta, da sola, ad attivare gli stessi controlli.

## Fondazione minima della mappa

La mappa conserva inventario, relazioni note e schede semantiche con evidenza, freschezza e incertezze. Una scheda descrive comportamento, contratti ed effetti; una relazione non risolta resta sconosciuta. Le modifiche invalidano le schede dipendenti dalle sorgenti cambiate: controllare soltanto il timestamp del file della scheda non basta.

L'interfaccia tra i due proprietari è una richiesta di contesto e una risposta con riferimenti alle sorgenti, spiegazioni supportate ed evidenza mancante. Il reviewer può richiedere altri frammenti. Non si espande l'intero grafo per principio e non si chiama completo un risultato solo perché rispetta uno schema.

Il perimetro comprende i tipi di file che possono determinare il comportamento, inclusi stili e configurazioni pertinenti. Esclusioni, file non analizzabili e limiti dei parser sono dichiarati. Nessuna conclusione runtime deriva dal solo inventario statico.

La cache ricostruibile appartiene a Codebase Map e si aggiorna per contenuto. La memoria temporanea della review resta nella sessione; si salva un rapporto quando richiesto o necessario per riprenderla. Non serve ricostruire un sistema di run, agende e ricevute per ogni lettura.

## LLM prima, embedding se dimostrano utilità

Il primo prototipo usa il modello già disponibile nell'host, frammenti della mappa e un piccolo insieme di controlli leggibili. Evita un servizio separato e consente di osservare gli errori di selezione.

Una variante successiva aggiunge embedding come recupero dei candidati, confrontandola con ricerca testuale e relazioni. Modello di embedding, costo di indicizzazione, freschezza e invio dei dati devono essere espliciti; nessun download o trasferimento remoto implicito. Nessuna nuova banca dati vettoriale è necessaria per definire il contratto.

Questa scelta è un'ipotesi progettuale: SkillRouter osserva, sul proprio benchmark di skill routing, limiti delle sole descrizioni senza il contenuto delle skill ([paper](https://arxiv.org/abs/2603.22455v5)). Repoformer studia recupero selettivo nel completamento di codice e mostra perché recuperare sempre non è automaticamente utile ([paper](https://arxiv.org/abs/2403.10059)). Nessuno dei due dimostra l'efficacia di questo selettore di review: serve una misura sul nostro compito.

## Come decidere se funziona

Confrontare, sugli stessi casi e con lo stesso modello, review generica, vecchia selezione se riproducibile dall'archivio, selezione semantica senza embedding e variante con embedding. Separare casi usati per correggere il metodo da casi di verifica non usati nella costruzione.

| Criterio | Misura |
| --- | --- |
| Utilità | Difetti noti realmente trovati, falsi finding, domande necessarie omesse |
| Selezione | Baseline di stack e controlli necessari recuperati, baseline mancanti e controlli irrilevanti caricati |
| Economia | Token effettivi e tempo dell'intero percorso, inclusi mappa, selezione e tentativi |
| Robustezza | Stesso problema in linguaggi diversi; stessa tecnologia con problemi diversi; lessico fuorviante |
| Limiti | Schede obsolete, dipendenze non risolte, skill mancanti e contesto insufficiente |

I casi devono avere evidenze e risultati attesi verificati indipendentemente; un voto dato dallo stesso modello non basta. Misurare separatamente costo iniziale della mappa e riuso incrementale. Non sostituire i token con il numero di caratteri e non dichiarare risparmi prima delle misure.

Il primo incremento da implementare è una review completa di un piccolo caso con difetto verificabile: mappa essenziale, domande, selezione dei controlli, esecuzione e risultato confrontato con l'evidenza. Solo dopo questo percorso si giustificano nuovi controlli, embedding o più reviewer.
