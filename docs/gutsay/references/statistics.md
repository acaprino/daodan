# Disegno statistico della campagna Gutsy CPU

Data: 26 ottobre 2026. Solo progettazione: nessuna nuova inferenza, installazione o esecuzione Modal. Il pilot precedente ha ottenuto 36/45 segnali essenziali di routing, 5/14 set tool sufficienti e tre perdite critiche su otto casi per entrambi i bracci di compattazione. Queste osservazioni orientano le ipotesi, non diventano un nuovo test indipendente.

## Raccomandazione centrale

Preparare una campagna singola, preregistrata e con checkpoint, con un **obiettivo di acquisizione di 600 scenari-base per dominio**, cioè **1.800 scenari nuovi**. Questo non è un corpus già disponibile e non è una promessa di 1.800 unità indipendenti. Registrare separatamente scenario, famiglia semantica e cluster di provenienza. Una famiglia è un compito o episodio semanticamente distinto con provenienza verificabile. Traduzioni, perturbazioni, stati di un medesimo episodio, commit collegati e repliche non sono nuove famiglie indipendenti. Il collo di bottiglia è ottenere oracle corretti e fonti diverse, non generare migliaia di variazioni lessicali.

Per dominio: obiettivo 120 scenari sviluppo del formato, 120 calibrazione e 360 verifica tenuti separati, assegnando intere famiglie e cluster anziché tagliarli per raggiungere una quota numerica. Gli effettivi possono differire dalle quote ideali: il manifest deve mostrarlo. Addestramento dei pesi: **zero esempi consumati**, perché questa campagna riguarda l'uso del modello congelato. Se si vuole una riserva di training futura, aggiungerla fuori dai 600 e non riutilizzare la verifica come train. Non rinominare lo sviluppo dei prompt come addestramento dei pesi.

Il numero 600 è un obiettivo di progetto, non una disponibilità del corpus già verificata. Non dichiararlo raggiunto con 12 template e 50 sostituzioni di nomi. Se le fonti verificate producono meno unità, riportare il numero vero e ridimensionare le conclusioni, senza riempimento automatico.

Lo scopo principale è decidere dove investire, non certificare un tasso di errore inferiore all'1%. Le quantità N nella sezione inferenziale indicano unità critiche effettivamente indipendenti sotto le ipotesi dichiarate, non il numero desiderato di scenari.

## Separazione e provenienza

Assegnare gli split prima delle risposte mediante gruppo di provenienza: repository/progetto, ticket o episodio, famiglia semantica e template generatore. Tutti i casi collegati rimangono nello stesso split. Dedicare, se disponibili, progetti interi alla verifica esterna; all'interno di un solo progetto il risultato rimane trasferibilità interna. Il pilot già osservato rimane regression/diagnostica e non entra nel denominatore della verifica nuova.

Proposta di composizione: metà casi source-backed reali o derivati da task verificati e metà casi sintetici con oracle esatto. Sono strati separati, non una popolazione naturale con prevalenza 50/50. Riportare risultati per fonte e tipo, oltre alla media macro. Per i casi reali non chiamare oracle la scelta storica del coordinatore o del modello. Servono requisiti e prove indipendenti; per il costo del modello finale serve un esperimento downstream ulteriore.

Conservare separatamente input del modello, dati pubblici del task, oracle, fonte con revisione/hash e razionale dell'etichetta. Un disaccordo sostanziale fra valutatori produce `ambiguous` e un insieme accettabile, oppure esclusione con motivo dal solo scoring che richiede quell'etichetta. Non nascondere l'esclusione dalla copertura.

## Matrice di qualità con conteggi auditabili

Tutti i bracci ricevono gli stessi fatti disponibili. Un confronto che cambia sia rappresentazione sia domanda è una comparazione di procedure, non un isolamento del modello. I seguenti bracci isolano almeno un confronto essenziale per dominio.

| Dominio | Bracci Gutsy sulla stessa famiglia | Richieste principali | Domande del modello |
|---|---|---:|---:|
| Routing | R1 dieci segnali attuali; R2 metadati più due residui; R3 stessa rappresentazione R2 con formulazione positiva/negativa | 1.800 | 6.000 + 1.200 + 1.200 = 8.400 |
| Tool | T1 flat noul per ogni candidato eleggibile; T2 cinque domande multi-label di famiglia, riusando i punteggi T1 per simulare il gate | 1.200 | E + 3.000, dove E è la somma dei candidati eleggibili; massimo 10.800 se ogni caso ne ha al massimo tredici |
| Compattazione | C1 stato/prompt upstream; C2 stesso prompt con risultato visibile; C3 stesso stato C2 con domanda coerente con ripetibilità | 1.800 | 3.600: due domande per coppia candidata per tre bracci |
| Totale qualità | Baseline metadati/all-tools/keep-all e guardrail sono replay senza nuove inferenze | 4.800 | 15.000 + E, massimo 22.800 |

T2 tool è inizialmente una valutazione di qualità del gate simulato, non una misura della latenza di una vera selezione gerarchica. Il suo tempo deve essere misurato in un replay esecutivo separato se si vuole dichiarare un risparmio. Le soglie e i top-K su risposte già salvate non richiedono nuova inferenza e non costituiscono altre osservazioni indipendenti.

Per compattazione, dichiarare una sola coppia candidata principale per la famiglia nel conteggio della tabella. Le sessioni con molti candidati richiedono una tabella di espansione propria: una sessione non è una singola domanda e le coppie della stessa sessione sono correlate.

## Robustezza e prestazioni senza prodotto cartesiano indiscriminato

Selezionare prima del run 120 famiglie di verifica per dominio. Applicare quattro perturbazioni a ciascuna: lingua, distrattore/posizione del fatto, ordine o alias delle opzioni, e ramo di stato equivalente o recupero. Usare R3, T1 e C3 già preregistrati, non il vincitore scelto dopo aver visto i risultati. Sono **1.440 input derivati**, massimo **8.160 domande**: routing 960, tool 6.240, compattazione 960. Questo misura stabilità paired; non aumenta N da 360 a 840.

Le interazioni più importanti meritano mini-factorial completi: ripetibilità × unicità × posizione dell'evidenza per compaction; fase × permesso × disponibilità per tool; gravità × completezza × scope per routing. Per il resto scegliere una covering array vincolata e pubblicarne la copertura effettiva. Il pairwise da solo non garantisce copertura delle interazioni critiche. [Metodo combinatorio NIST](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-142.pdf).

Prestazioni: sei workload fissi che entrano in entrambi i contesti, con due routing (due domande ciascuno), due cataloghi tool (13 e 31 candidati) e due compaction (due domande ciascuno). Totale 52 domande per giro. Quattro profili `threads={2,4} × n_ctx={1536,4096}`, due modi (domande in batch oppure singole con stesso stato) e dieci repliche danno **480 decisioni complete**, **4.160 domande**, e **2.320 HTTP request** (240 batch più 2.080 singole). La tokenizzazione deve confermare prima del congelamento che tutti i workload entrino in 1.536 token; altrimenti registrare il caso limite in un altro strato e ricalcolare i conteggi.

Su una sola macchina Modal con quattro core, cambiare i thread non equivale a cambiare la quota CPU fisica. Chiamare i profili con il numero di thread, non “macchina a due core”. Misurare separatamente avvio del modello, primo encoding, richieste con prefisso già presente e decisione completa. Controbilanciare ordine dei profili e dei bracci; intercalare repliche dei workload invece di eseguire tutti i casi di un solo tipo consecutivamente. Una replica deterministica è informazione temporale, non una nuova prova di qualità.

**Massimo di questo disegno: 35.120 domande del modello**, di cui 22.800 core, 8.160 robustezza e 4.160 prestazioni; più contratti meccanici senza modello. Richieste HTTP massime: 4.800 + 1.440 + 2.320 = 8.560. I numeri tool sono massimi: il manifest espanso deve riportare il numero effettivo E, le domande ammesse dopo permessi, quelle saltate e le eventuali shortlisting calls. Un manifest generato dai dati è la contabilità finale; non fingere un numero esatto prima di materializzare il corpus.

## Inferenza e criteri di decisione

Per confronto primario fissare un contrasto per dominio: R3 contro R1, T2 contro T1, C3 contro C1. I contrasti intermedi R3/R2 e C3/C2 isolano la formulazione ma rimangono secondari se non si controlla la molteplicità. Usare differenze paired per famiglia con intervalli bootstrap stratificati a cluster (10.000 ricampionamenti proposti). Tutti i bracci e le varianti della famiglia devono viaggiare insieme nel ricampionamento. Se la dipendenza principale è il progetto, ricampionare progetti e poi famiglie o riportare un'analisi leave-one-project-out; molti episodi di due progetti non equivalgono a molti progetti indipendenti. Il principio di non trattare osservazioni correlate come indipendenti è documentato da [Cameron e Miller](https://escholarship.org/uc/item/1jq5d0pq); l'applicazione a questa campagna è una nostra scelta di disegno.

Per errori rari usare intervalli binomiali esatti unilaterali preregistrati. Con zero errori e unità iid, il limite superiore 95% è U=1−0,05^(1/n), approssimativamente 3/n; deriva dall'inversione binomiale. Non passare da due lati a un lato solo dopo aver osservato zero. [Intervalli binomiali NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

| N effettivo indipendente con zero errori | U95 un dominio | U con controllo Bonferroni per tre domini |
|---:|---:|---:|
| 180 | 1,651% | 2,249% |
| 300 | 0,994% | 1,356% |
| 360 | 0,829% | 1,131% |
| 600 | 0,498% | 0,680% |

Questi sono calcoli teorici, non promesse di generalizzazione: iid e rappresentatività non sono garantite da un corpus challenge curato. Se solo 180 famiglie di test sono davvero critiche, non usare 360 come denominatore del rischio critico. Per un limite inferiore all'1% servono almeno 299 prove critiche indipendenti senza errori per un dominio (408 per tre domini simultanei); per 0,5% almeno 598 (817 simultanee). Il grande totale di domande non supera questa limitazione.

Metriche primarie: mancato riconoscimento di floor e capability nel routing; omissioni che rendono insufficiente il set tool; perdita di fatti necessari e recuperi falliti nella compaction. Metriche di utilità: over-routing, strumenti superflui, token/byte risparmiati con tokenizer dichiarato, numero e costo dei fallback. Prestazioni: p50/p95 per decisione completa e per strato, RSS/PSS del processo server e controller separati, wall time totale e CPU time. Non mediare tutto in un punteggio che compensi una perdita critica con risparmio di token.

## Un lancio non significa adattare il test mentre gira

Il controller può eseguire sviluppo, calibrazione, congelamento automatico della policy e verifica in fasi nella stessa macchina, purché ricetta di selezione, griglia delle soglie, metrica, tie-break e ordine siano preregistrati. Prima di aprire la verifica salvare hash della policy scelta usando soltanto sviluppo/calibrazione. I risultati della verifica non guidano ulteriori modifiche nel medesimo run. Se tutti i candidati falliscono, l'esito corretto è “nessuna policy ammissibile”, non la scelta del meno peggio.

Non fermare una strategia perché perde i primi casi e poi confrontare le restanti su tutti i casi. Solo i limiti preregistrati di costo, tempo, memoria, incompatibilità o guasto possono fermare la campagna; il risultato è allora incompleto e i denominatori mancanti restano espliciti. Checkpoint per richiesta e confine di fase; resume solo con stessi hash, senza ricontare risposte già esistenti come nuovi campioni. Le retry rimangono tentativi del medesimo input.

Albero decisionale finale: invalidità API o copertura incompleta → correggere harness e ripetere il blocco, senza giudicare il modello; qualità grezza buona ma policy fallisce → correggere policy su sviluppo e usare nuovo test; qualità insufficiente solo con stato omesso → cambiare rappresentazione; qualità sufficiente ma latenza/RAM troppo alte → ridurre domande e contesto oppure restringere frequenza d'uso; qualità e risorse entro criteri con intervalli utili → shadow mode su dati reali separati; tutte le procedure ammissibili falliscono sulla verifica → considerare altra architettura o dati per specializzazione, non training per default.
