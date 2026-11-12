# Mappa funzionale: nodi con nome e flussi principali

**Stato:** proposta, non applicata. **Data:** 12 novembre 2026. Ridefinisce «nodo» e «flusso» della [fase 2](2026-11-09-flow-model.md) e ne sostituisce i punti 1.5, 3.5 e 7; il resto della fase 2 resta e diventa la prova di ciò che si descrive qui.

Daodan deve saper rispondere a due domande: «di quali cose è fatto questo sistema e cosa fa?» e «cosa tocca questa richiesta?». La risposta serve a chi guarda il sistema e a chi lo revisiona: una richiesta che nomina una parte del sistema deve portare alle schermate, ai servizi, ai dati e ai servizi esterni che quella parte comprende. Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark.

## Parole

Le parole della fase 2 valgono, tranne queste.

| Parola | Significato |
| --- | --- |
| Nodo | Una cosa del sistema con un nome, al livello a cui la nomina una persona: un attore, una schermata, una funzione, un servizio, un servizio esterno, un dispositivo, un'entità. Raccoglie i suoi membri: file, simboli, store, rotte. Un simbolo da solo non è un nodo |
| Tipo di nodo | L'elenco della fase 2, più «entità»: un dato con un nome (un ordine, un utente, un abbonamento), ovunque sia salvato |
| Non visto | Un nodo che fa parte del sistema ma i cui file stanno fuori dallo snapshot. Si distingue da «esterno», che è un servizio di altri |
| Flusso | Una cosa che il sistema fa, con un nome: i nodi che vi partecipano e le frecce fra loro |
| Percorso | Ciò che la fase 2 chiamava flusso: la sequenza ordinata di collegamenti da un punto d'ingresso. È il dettaglio e la prova di un flusso |
| Freccia | Da un nodo a un altro dentro un flusso, con il dato che passa. Riassume i collegamenti fra i membri dei due nodi |
| Tipo di flusso | Uno o più fra: utente (lo avvia una persona), operativo (lo avvia un orario, un servizio o un avviso esterno), dati (segue un dato: dove nasce, dove vive, chi ne tiene copia) |
| Area | Un gruppo di flussi che una persona nomina insieme. È ciò che una richiesta nomina più spesso |
| Mappa funzionale | Nodi, flussi e aree di un progetto, con le loro prove |
| Scheda del sistema | Il riassunto che la macchina compone dai passi di analisi per chi propone la mappa funzionale |

Passi di analisi (statico, inferenza, dinamico, semantico) e livelli restano quelli del [passo dinamico](2026-11-12-passo-dinamico.md) e della fase 2.

## Comportamento attuale

- `codebase_map_flows` traccia un percorso per ogni punto d'ingresso, con passaggi fra simboli e `file:riga`. Su un caso reale sono 235 ([`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md)); l'esploratore li elenca uno per uno. Nessuno li raggruppa né dà loro un nome.
- I dati sono store presi uno per uno: nello stesso caso 123, di cui 75 sono chiavi dello stesso stato dell'app.
- Il modello può già proporre moduli con nome, membri ed evidenze, verificati membro per membro (`codebase_map_modules`), e scrivere la scheda di un percorso con citazioni verificate. Manca chi propone i flussi principali: i punti 3.5 e 7 della fase 2 lo prevedevano e non sono costruiti.
- Il riconoscimento dei servizi esterni (fase 2, punto 1.5) non è costruito. L'esploratore ha le icone generiche per tipo di nodo.
- `03-flows.md` descrive i flussi in prosa, leggendo il codice. Non si interroga e la review non lo legge.
- Dei quattro passi di analisi, statico, inferenza e semantico sono applicati; il dinamico è una proposta.
- Nelle dieci run della fase 3 né le unità né l'elenco di chi scrive e chi legge hanno portato nel rapporto i difetti attesi.

## Proposta

### 1. Nodi

1. Un nodo con codice è un gruppo di membri con un nome, un tipo e una posizione. I membri sono file, simboli, store e rotte, oppure un intero modulo della mappa, citato per nome.
2. Un nodo senza codice (attore, dispositivo, servizio esterno, parte non vista) è un modulo `external` della mappa, come nella fase 2: non ha membri e cita l'evidenza che lo lega al progetto. Un attore cita i punti d'ingresso che usa. Un nodo non visto resta distinguibile da un servizio esterno.
3. Un'entità è un nodo i cui membri sono gli store che contengono quel dato.
4. Lo stesso membro può stare in più nodi: un file che serve due schermate appartiene a entrambe.
5. La mappa funzionale sta accanto al grafo dei moduli e non ne cambia strati, conflitti e archi.
6. Ogni nodo ha un nome, interno o esterno che sia.

### 2. Servizi esterni con nome

1. La macchina confronta le dipendenze dichiarate, gli host delle chiamate e i nomi delle variabili di configurazione con una raccolta pubblica di marchi, usata come registro: Simple Icons (CC0, oltre 3.400 marchi). Una corrispondenza diventa un modulo `external` proposto, con nome e logo; il sito viene dai metadati del pacchetto.
2. Il tipo del servizio (gateway, database, autenticazione e così via) lo propone il modello.
3. Un servizio non riconosciuto prende il nome del pacchetto o dell'host e resta marcato come non riconosciuto. Daodan non mantiene un registro proprio.

### 3. Scheda del sistema

1. La macchina compone, senza modello, un riassunto di ciò che i passi di analisi hanno già prodotto: moduli e cartelle con il numero di file; punti d'ingresso, store e rotte; servizi esterni riconosciuti; collegamenti provati, dedotti e osservati, contati fra gruppi; titoli delle schede già scritte. Dichiara i passi non eseguiti.
2. La scheda raggruppa già ciò che i collegamenti legano: i punti d'ingresso che toccano la stessa chiave di uno store, la stessa rotta o lo stesso servizio esterno stanno nello stesso gruppo candidato. Ciò che troppi punti d'ingresso toccano (una chiave di sessione, un client comune) non lega: la soglia è un parametro del benchmark. Chi propone la mappa dà nomi e tagli, non cerca.
3. La scheda ha un tetto di dimensione, scritto nel README del benchmark. Oltre il tetto i gruppi meno collegati si riassumono in una riga e restano interrogabili.

### 4. Chi propone la mappa funzionale

1. Un agente riceve la scheda del sistema e propone nodi, flussi e aree in un formato fisso. Fa parte del passo semantico: parte con l'analisi che l'utente chiede, mai da solo, e richiede le regole di collegamento del progetto, perché store e rotte esistono solo dopo quelle.
2. Può interrogare ciò che ogni passo ha prodotto (simboli, collegamenti, percorsi, schede) con gli strumenti esistenti e aprire il sorgente. Lo fa solo dove la scheda non basta a decidere un nome o un taglio.
3. Individua i flussi principali passando in rassegna un elenco di aree: accesso e identità; funzioni principali del prodotto; pagamenti e abbonamenti; dati dell'utente (sincronizzazione, esportazione, cancellazione, consensi); integrazioni esterne; comunicazioni; amministrazione; esercizio (lavori pianificati, manutenzione, rilascio). Per ogni area dichiara i flussi trovati oppure che l'area è assente. Aggiunge le aree che il progetto ha e l'elenco no.
4. Ogni flusso ha un nome, un'area, uno o più tipi, i suoi nodi, le frecce con il dato che passa e i percorsi che lo compongono.
5. Un dato che vive in più nodi (un listino, un elenco di permessi, un limite) è un flusso di tipo dati: le sue frecce dicono «stessa informazione» e ogni posto è citato.
6. Il prompt dell'agente si mette a punto sul benchmark, con il modello meno costoso che supera le soglie.

### 5. Verifica

La macchina accetta o rifiuta ogni parte della proposta e dice perché. L'agente corregge una volta; ciò che resta rifiutato non entra nella mappa.

1. **Nodo:** nome unico e tipo dell'elenco. Un nodo con codice ha almeno un membro che esiste: un file o un simbolo dello snapshot, una chiave di store o una rotta fra i collegamenti. Un nodo senza codice cita la sua evidenza; un nodo non visto dichiara dove sta.
2. **Freccia:** è provata in uno di due modi. Da un collegamento diretto, dedotto o osservato fra un membro del primo nodo e un membro del secondo, nel verso indicato. Oppure da una coppia `scrive` e `legge` sulla stessa chiave di store, dal primo nodo al secondo. È «dichiarata», con un punto del codice citato, quando un capo è un nodo senza codice o quando dice «stessa informazione»: lì la macchina verifica che i punti citati esistano, non che i valori coincidano. Ogni altra freccia è rifiutata.
3. **Copertura:** quanti punti d'ingresso, store e rotte stanno in almeno un flusso. Il resto è elencato, non nascosto.
4. **Conferma:** una proposta resta `inferred` finché il progetto non la conferma, come per i moduli. Ciò che il progetto conferma o rinomina non viene riproposto.
5. **Freschezza:** nodi e flussi sono legati ai digest dei file dei loro membri. Quando un file cambia la macchina riverifica, senza modello, membri e frecce di ciò che lo contiene. Torna all'agente solo ciò che non regge più, e i nomi confermati non cambiano.

### 6. Chi usa la mappa funzionale

- **Esploratore:** apre sul grafo d'insieme e mostra un grafo per flusso. Percorsi e collegamenti fra simboli si vedono su richiesta, come prova di una freccia. Un grafo mostra nodi: un nodo si apre per vederne i membri.
- **Review:** una richiesta che nomina un'area, un flusso o un nodo riceve come perimetro i membri di quei nodi. Il brief elenca nodi, frecce e dati tenuti in più posti. Un nodo non visto è una lacuna dichiarata della review. Si misura prima di adottarlo, come chiede la [fase 3](2026-11-09-flows-in-review.md).
- **`codebase_map_flows`:** risponde per area, flusso e nodo. I percorsi restano interrogabili come oggi.
- **`03-flows.md`:** si genera dalla mappa funzionale.

## Limiti

Nomi, tipi e tagli sono proposte del modello: la macchina verifica che poggino su collegamenti veri, non che il nome sia giusto, e per questo il progetto conferma. Una freccia provata dice che un collegamento esiste, non che il flusso sia completo. Ciò che sta fuori dallo snapshot entra solo se dichiarato. Senza passo dinamico mancano i collegamenti che si decidono in esecuzione.

## Prova

Benchmark `benchmarks/functional-map/`, da creare, con le soglie scritte nel README prima di ogni misura.

1. **Riproduzione.** Su un caso reale e per un'area, la mappa proposta a confronto con una fatta a mano prima, che l'agente non vede: nodi ritrovati, confrontati per membri e non per nome; flussi ritrovati; frecce accettate e rifiutate. Il riferimento esiste per un'area di un caso già nei benchmark dei flussi, fatto il 12 novembre 2026: il README lo registra dopo la conferma del proprietario.
2. **Secondo progetto.** Lo stesso prompt su un altro dei casi già nei benchmark dei flussi, che hanno le regole di collegamento: frecce provate, copertura, lettura manuale di un campione di nomi.
3. **Costo.** Token e costo per mappa e per modello; quante volte l'agente apre il sorgente.
4. **Stabilità.** Due esecuzioni sullo stesso snapshot danno gli stessi nodi, confrontati per membri.
5. **Review.** Una richiesta per area, con perimetro e brief dalla mappa funzionale, contro la review di oggi. È a pagamento: si chiede prima.

## Ordine di lavoro

1. Formato della mappa funzionale e verifica.
2. Scheda del sistema e riconoscimento dei servizi esterni.
3. Prompt dell'agente; misure 1, 2, 3 e 4.
4. Esploratore sulla mappa funzionale.
5. Review; misura 5.

**Da decidere alla rifinitura:** dove il progetto registra ciò che conferma; il tetto della scheda del sistema; come distribuire i loghi rispettando l'avvertenza sui marchi della raccolta; se gli identificatori nel codice che oggi dicono «flow» per i percorsi cambiano nome.
