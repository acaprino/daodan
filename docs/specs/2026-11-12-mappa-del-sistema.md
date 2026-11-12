# Mappa del sistema: nodi con nome, flussi e livelli

**Stato:** proposta, non applicata. **Data:** 12 novembre 2026. Ridefinisce «nodo», «flusso» e «livello» della [fase 2](2026-11-09-flow-model.md) e ne sostituisce i punti 1.5, 3.5, 5 e 7, compresa la scelta di non tenere un registro proprio; il resto della fase 2 resta e diventa la prova di ciò che si descrive qui.

Daodan deve saper rispondere a tre domande: «di quali cose è fatto questo sistema e cosa fa?», «cosa tocca questa richiesta?» e «come appare lo stesso processo a chi lo usa, a chi lo progetta, a chi lo scrive e a chi lo fa girare?». La risposta ha due usi: studiare il prodotto e la codebase, e capire cosa controllare in una review partendo dall'intento di chi la chiede. Un intento che riguarda una parte del sistema deve portare alle schermate, ai servizi, ai dati, al codice e all'infrastruttura che quella parte comprende. Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark.

## Parole

Le parole della fase 2 valgono, tranne queste.

| Parola | Significato |
| --- | --- |
| Nodo | Una cosa del sistema con un nome, al livello a cui la nomina una persona: un attore, una schermata, una funzione, un servizio, un servizio esterno, un dispositivo, un'entità. Raccoglie i suoi membri: file, simboli, store, rotte. Un simbolo da solo non è un nodo |
| Tipo di nodo | L'elenco della fase 2, più «entità»: un dato con un nome (un ordine, un utente, un abbonamento), ovunque sia salvato |
| Progetto esterno | Codice di altri su cui il sistema è costruito: un framework, una libreria, un runtime. Si distingue da «servizio esterno», che gira altrove |
| Non visto | Un nodo che fa parte del sistema ma i cui file stanno fuori dallo snapshot. Si distingue da «esterno», che è di altri |
| Flusso | Un processo del sistema con un nome: i nodi che vi partecipano e le frecce fra loro. È uno solo, a qualunque livello lo si guardi |
| Tipo di flusso | Uno o più fra: funzionale (una cosa che il prodotto fa per chi lo usa), operativo (gira senza una persona: un orario, una coda, un avviso esterno), tecnico (un meccanismo interno: cache, sincronizzazione, build, rilascio), dati (segue un dato: dove nasce, dove vive, chi ne tiene copia), hardware (passa da dispositivi fisici o dalla rete) |
| Livello | La prospettiva da cui si guarda un flusso: persone, funzioni, dati, codice, infrastruttura, oppure misto. Sostituisce l'elenco della fase 2, dove «fisico» indicava file e simboli: quello ora è il livello codice |
| Corrispondenza | Il legame fra nodi di livelli diversi che sono la stessa cosa vista da due prospettive: una funzione e i file che la realizzano, un servizio e la macchina su cui gira, un'entità e il database in cui vive |
| Percorso | Ciò che la fase 2 chiamava flusso: la sequenza ordinata di collegamenti da un punto d'ingresso. È il livello codice di un flusso, e la sua prova |
| Freccia | Da un nodo a un altro dentro un flusso, con il dato che passa. Riassume i collegamenti fra i membri dei due nodi |
| Area | Un gruppo di flussi che una persona nomina insieme. È ciò che una richiesta nomina più spesso |
| Mappa del sistema | Nodi, flussi, aree e corrispondenze di un progetto, con le loro prove |
| Scheda del sistema | Il riassunto che la macchina compone dai passi di analisi per chi propone la mappa del sistema |

I passi di analisi (statico, inferenza, dinamico, semantico) restano quelli del [passo dinamico](2026-11-12-passo-dinamico.md).

## Comportamento attuale

- `codebase_map_flows` traccia un percorso per ogni punto d'ingresso, con passaggi fra simboli e `file:riga`. Su un caso reale sono 235 ([`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md)); l'esploratore li elenca uno per uno. Nessuno li raggruppa né dà loro un nome.
- I dati sono store presi uno per uno: nello stesso caso 123, di cui 75 sono chiavi dello stesso stato dell'app.
- I livelli della fase 2 contraggono un percorso su moduli, store o attori. Non c'è un livello per l'infrastruttura, e «fisico» vi indica file e simboli.
- Il modello può già proporre moduli con nome, membri ed evidenze, verificati membro per membro (`codebase_map_modules`), e scrivere la scheda di un percorso con citazioni verificate. Manca chi propone i flussi principali: i punti 3.5 e 7 della fase 2 lo prevedevano e non sono costruiti.
- Il riconoscimento dei servizi esterni (fase 2, punto 1.5) non è costruito, e quel punto si affidava alla sola raccolta dei marchi, che non dice né il tipo di un servizio né da cosa riconoscerlo. L'esploratore ha le icone generiche per tipo di nodo.
- `03-flows.md` descrive i flussi in prosa, leggendo il codice. Non si interroga e la review non lo legge.
- Dei quattro passi di analisi, statico, inferenza e semantico sono applicati; il dinamico è una proposta.
- Nelle dieci run della fase 3 né le unità né l'elenco di chi scrive e chi legge hanno portato nel rapporto i difetti attesi.

## Proposta

### 1. Nodi

1. Un nodo con codice è un gruppo di membri con un nome, un tipo e una posizione. I membri sono file, simboli, store e rotte, oppure un intero modulo della mappa, citato per nome.
2. Un nodo senza codice (attore, dispositivo, macchina o servizio su cui il sistema gira, servizio esterno, progetto esterno, parte non vista) è un modulo `external` della mappa, come nella fase 2: non ha membri e cita l'evidenza che lo lega al progetto. Un attore cita i punti d'ingresso che usa; una macchina o un servizio di esecuzione cita la configurazione che lo nomina; un progetto esterno cita la dipendenza dichiarata. Un nodo non visto resta distinguibile da un servizio esterno.
3. Un'entità è un nodo i cui membri sono gli store che contengono quel dato.
4. Lo stesso membro può stare in più nodi: un file che serve due schermate appartiene a entrambe.
5. La mappa del sistema sta accanto al grafo dei moduli e non ne cambia strati, conflitti e archi.
6. Ogni nodo ha un nome, interno o esterno che sia.
7. Non ogni dipendenza è un nodo. Lo diventano i progetti esterni che il registro conosce o che un flusso nomina; le altre dipendenze restano raggruppate e contate.

### 2. Livelli

Un flusso è uno solo; si guarda da più prospettive, come gli strati di una mappa geografica.

| Livello | Nodi mostrati |
| --- | --- |
| Persone | Attori e schermate |
| Funzioni | Funzionalità, servizi e servizi esterni |
| Dati | Entità e i posti in cui vivono |
| Codice | Moduli, file e simboli: i percorsi. Sotto, i progetti esterni su cui poggiano |
| Infrastruttura | Dispositivi, servizi in esecuzione, database, code, reti e servizi esterni |
| Misto | Nodi di livelli diversi nello stesso grafo |

1. Ogni livello mostra solo i suoi tipi di nodo, con le frecce riportate fra quelli.
2. Un flusso esiste ai livelli in cui ha nodi: un flusso tecnico può non avere il livello persone.
3. Le corrispondenze dicono quali nodi di due livelli sono la stessa cosa. Quella verso il codice è l'appartenenza dei membri. Quelle verso l'infrastruttura e verso il posto in cui un'entità vive si dichiarano citando la configurazione o il codice che le prova.
4. Due flussi si incrociano nei nodi che hanno in comune, a qualunque livello: un nodo elenca i flussi che lo attraversano.
5. I livelli si guardano uno alla volta, alcuni o tutti insieme. Insieme, ogni nodo mostra le sue corrispondenze agli altri livelli e dichiara i livelli a cui non esiste.

### 3. Registro dei servizi e dei progetti esterni

1. Daodan porta con sé un registro dei servizi e dei progetti esterni più diffusi: almeno mille alla prima versione. Per ognuno tiene nome, tipo di nodo, sito, marchio e i segni da cui lo si riconosce in un progetto: nomi dei pacchetti, host, prefissi delle variabili di configurazione.
2. La macchina confronta le dipendenze dichiarate, gli host delle chiamate e i nomi delle variabili di configurazione con i segni del registro. Una corrispondenza diventa un modulo `external` proposto, con nome, tipo, sito e marchio, senza modello.
3. Il marchio viene da una raccolta pubblica, Simple Icons (CC0, 3.470 marchi alla versione 16.37.0). La raccolta dà nome e disegno, non tipo, sito e segni: quelli li tiene il registro.
4. Il registro si costruisce con uno script, e con lo stesso si rigenera, da cataloghi pubblici con licenza adatta ([ricognizione](../research/2026-11-12-external-service-catalogs.md)): le regole di riconoscimento di stack-analyser, i marchi di Simple Icons, le voci del CNCF Landscape. Un modello propone solo ciò che manca: sito, tipo dove assente, pacchetti degli ecosistemi non coperti. La macchina tiene solo ciò che verifica, cioè che il sito risponda e che il pacchetto esista.
5. Un servizio che il registro non conosce prende il nome del pacchetto o dell'host e l'icona generica del suo tipo, e resta marcato come non riconosciuto. Il modello può proporne nome e tipo.
6. Ogni nodo esterno mostra nome e marchio in ogni grafo e a ogni livello.

### 4. Scheda del sistema

1. La macchina compone, senza modello, un riassunto di ciò che i passi di analisi hanno già prodotto: moduli e cartelle con il numero di file; punti d'ingresso, store e rotte; servizi esterni riconosciuti; file che configurano l'esecuzione e il rilascio; collegamenti provati, dedotti e osservati, contati fra gruppi; titoli delle schede già scritte. Dichiara i passi non eseguiti.
2. La scheda raggruppa già ciò che i collegamenti legano: i punti d'ingresso che toccano la stessa chiave di uno store, la stessa rotta o lo stesso servizio esterno stanno nello stesso gruppo candidato. Ciò che troppi punti d'ingresso toccano (una chiave di sessione, un client comune) non lega: la soglia è un parametro del benchmark. Chi propone la mappa dà nomi e tagli, non cerca.
3. La scheda ha un tetto di dimensione, scritto nel README del benchmark. Oltre il tetto i gruppi meno collegati si riassumono in una riga e restano interrogabili.

### 5. Chi propone la mappa del sistema

1. Un agente riceve la scheda del sistema e propone nodi, flussi, aree e corrispondenze in un formato fisso. Fa parte del passo semantico: parte con l'analisi che l'utente chiede, mai da solo, e richiede le regole di collegamento del progetto, perché store e rotte esistono solo dopo quelle. Lavora su tutto il sistema, per lo studio, oppure su una sola area, quando una review parte da un intento e la mappa di quell'area manca o non regge più.
2. Può interrogare ciò che ogni passo ha prodotto (simboli, collegamenti, percorsi, schede) con gli strumenti esistenti e aprire il sorgente. Lo fa solo dove la scheda non basta a decidere un nome o un taglio.
3. Individua i flussi principali, di ogni tipo, passando in rassegna un elenco di aree: accesso e identità; funzioni principali del prodotto; pagamenti e abbonamenti; dati dell'utente (sincronizzazione, esportazione, cancellazione, consensi); integrazioni esterne; comunicazioni; amministrazione; esercizio (lavori pianificati, cache, manutenzione, rilascio). Per ogni area dichiara i flussi trovati oppure che l'area è assente. Aggiunge le aree che il progetto ha e l'elenco no.
4. Ogni flusso ha un nome, un'area, uno o più tipi, i suoi nodi a ogni livello in cui esiste, le frecce con il dato che passa e i percorsi che lo compongono.
5. Un dato che vive in più nodi (un listino, un elenco di permessi, un limite) è un flusso di tipo dati: le sue frecce dicono «stessa informazione» e ogni posto è citato.
6. Il prompt dell'agente si mette a punto sul benchmark, con il modello meno costoso che supera le soglie.

### 6. Verifica

La macchina accetta o rifiuta ogni parte della proposta e dice perché. L'agente corregge una volta; ciò che resta rifiutato non entra nella mappa.

1. **Nodo:** nome unico e tipo dell'elenco. Un nodo con codice ha almeno un membro che esiste: un file o un simbolo dello snapshot, una chiave di store o una rotta fra i collegamenti. Un nodo senza codice cita la sua evidenza; un nodo non visto dichiara dove sta.
2. **Freccia:** è provata in uno di due modi. Da un collegamento diretto, dedotto o osservato fra un membro del primo nodo e un membro del secondo, nel verso indicato. Oppure da una coppia `scrive` e `legge` sulla stessa chiave di store, dal primo nodo al secondo. È «dichiarata», con un punto del codice o della configurazione citato, quando un capo è un nodo senza codice o quando dice «stessa informazione»: lì la macchina verifica che i punti citati esistano, non che i valori coincidano. Ogni altra freccia è rifiutata.
3. **Corrispondenza:** quella verso il codice è verificata sui membri. Le altre sono dichiarate, con il punto citato che esiste.
4. **Copertura:** quanti punti d'ingresso, store e rotte stanno in almeno un flusso. Il resto è elencato, non nascosto.
5. **Conferma:** una proposta resta `inferred` finché il progetto non la conferma, come per i moduli. Ciò che il progetto conferma o rinomina non viene riproposto.
6. **Freschezza:** nodi e flussi sono legati ai digest dei file dei loro membri. Quando un file cambia la macchina riverifica, senza modello, membri e frecce di ciò che lo contiene. Torna all'agente solo ciò che non regge più, e i nomi confermati non cambiano.

### 7. A cosa serve

La mappa del sistema ha due usi.

**Studiare il prodotto e la codebase.**

- L'esploratore apre sul grafo d'insieme e mostra un grafo per flusso, con un selettore di uno o più livelli. Percorsi e collegamenti fra simboli sono il livello codice. Un nodo si apre per vederne i membri e le corrispondenze agli altri livelli.
- `codebase_map_flows` risponde per area, flusso, nodo e livello; i percorsi restano interrogabili come oggi. `03-flows.md` si genera dalla mappa del sistema.

**Capire cosa controllare in una review, partendo dall'intento di chi la chiede.**

1. Il modello legge l'intento e lo riporta sulla mappa: quali aree, flussi e nodi tocca, e a quali livelli. Dichiara questa lettura nello scope della review; chiede solo se due letture cambiano correttezza o costo, come nella fase 2.
2. La mappa restituisce ciò che va controllato: i nodi con i loro membri, che sono il perimetro; le frecce con i dati che passano; i servizi esterni con il loro tipo; i dati tenuti in più posti, da confrontare; i nodi non visti, che sono lacune dichiarate della review.
3. Il brief dei revisori elenca queste cose, non solo i file.
4. L'effetto sui difetti trovati si misura prima di adottarlo, come chiede la [fase 3](2026-11-09-flows-in-review.md).

## Limiti

Nomi, tipi e tagli sono proposte del modello: la macchina verifica che poggino su collegamenti veri, non che il nome sia giusto, e per questo il progetto conferma. Una freccia provata dice che un collegamento esiste, non che il flusso sia completo. Il livello infrastruttura poggia su ciò che configurazione e codice dichiarano: quello che esiste solo in una console esterna non si vede. Ciò che sta fuori dallo snapshot entra solo se dichiarato. Senza passo dinamico mancano i collegamenti che si decidono in esecuzione.

## Prova

Benchmark `benchmarks/system-map/`, da creare, con le soglie scritte nel README prima di ogni misura.

1. **Riproduzione.** Su un caso reale e per un'area, la mappa proposta a confronto con una fatta a mano prima, che l'agente non vede: nodi ritrovati, confrontati per membri e non per nome; flussi ritrovati; frecce accettate e rifiutate. Il riferimento esiste per un'area di un caso già nei benchmark dei flussi, fatto il 12 novembre 2026: il README lo registra dopo la conferma del proprietario.
2. **Secondo progetto.** Lo stesso prompt su un altro dei casi già nei benchmark dei flussi, che hanno le regole di collegamento: frecce provate, copertura, lettura manuale di un campione di nomi.
3. **Livelli.** Per un flusso del riferimento, a ogni livello: i nodi mostrati sono solo dei tipi di quel livello e le corrispondenze citano punti che esistono. Un flusso tecnico resta senza livello persone.
4. **Costo.** Token e costo per mappa e per modello; quante volte l'agente apre il sorgente.
5. **Stabilità.** Due esecuzioni sullo stesso snapshot danno gli stessi nodi, confrontati per membri.
6. **Registro.** Sui casi dei benchmark: quanti servizi esterni usati dal progetto il registro riconosce, e quanti riconoscimenti sono sbagliati.
7. **Dall'intento ai controlli.** Per un intento scritto in linguaggio comune, le cose da controllare che la mappa restituisce a confronto con l'elenco scritto prima dal proprietario: quante ne nomina e quante ne aggiunge senza motivo. Non richiede run di review.
8. **Review.** Lo stesso intento, con perimetro e brief dalla mappa del sistema, contro la review di oggi. È a pagamento: si chiede prima.

## Ordine di lavoro

1. Formato della mappa del sistema e verifica.
2. Registro dei servizi esterni e scheda del sistema; misura 6.
3. Prompt dell'agente; misure da 1 a 5.
4. Esploratore sulla mappa del sistema, con il selettore dei livelli.
5. Review: dall'intento ai controlli, poi i revisori; misure 7 e 8.

**Da decidere alla rifinitura:** dove il progetto registra ciò che conferma; il tetto della scheda del sistema; dove vive il file del registro e ogni quanto si rigenera; come distribuire i loghi rispettando l'avvertenza sui marchi della raccolta; se gli identificatori nel codice che oggi dicono «flow» per i percorsi e «fisico» per i file cambiano nome.
