# Formato di progetto .daodan · schema 1

Contratto di persistenza della [mappa](architettura.md#la-mappa-nodi-nature-e-profondità), tranche T2.E. Il file distribuito è un singolo database SQLite. Il [DDL normativo](progetto-v1.sql) definisce tabelle, colonne, tipi, chiavi, vincoli e indici. L'apertura e il salvataggio nell'app sono da implementare.

## Come riconoscere il file

La v1 richiede SQLite 3.38 o successivo con funzioni JSON disponibili. Le tabelle usano tipi STRICT. L'intestazione è quella di SQLite. Il lettore verifica `application_id = 0x44414F44` (DAOD), `user_version = 1` e lo schema atteso prima di usare il file. Il DDL inizializza soltanto un database vuoto. Un lettore che incontra una versione sconosciuta spiega quale versione serve. Per migrare, si crea prima una copia consistente, si applicano le modifiche e si aggiorna `user_version` nella stessa transazione. Una copia da condividere a database aperto si ottiene con l'API di backup di SQLite, così include anche i commit già visibili in WAL. [Intestazione e pragma](https://sqlite.org/pragma.html) · [Backup SQLite](https://sqlite.org/backup.html)

## Tabelle

| Tabelle | Contenuto e collegamenti |
|---|---|
| `project`, `revisions` | Un progetto, UUID persistente e revisione corrente. Ogni revisione ha UUID proprio, genitore, autore, istante UTC, motivo, descrizione e analisi di riferimento. |
| `source_snapshots`, `analyses` | Sorgenti effettivamente analizzati, versione e configurazione di Daodan. Ogni esecuzione punta a uno snapshot. Più esecuzioni possono usare lo stesso snapshot. |
| `objects`, `versions` | Identità stabili e versioni dei soli oggetti cambiati. Una versione include provenienza e intervallo di validità. |
| `nodes`, `edges` | Il padre di un nodo e gli estremi di un arco puntano a ID stabili. Ogni arco ha ID proprio anche a parità di estremi, più tipo, grado, eventuale profilo e attributi come metodo e rotta. |
| `flows`, `variants`, `variant_endpoints` | Il flusso ha un nome, la variante ha profilo e condizione. Gli ingressi e gli esiti sono elenchi di nodi distinti per ruolo. |
| `steps`, `step_edges`, `step_transitions` | Occorrenze dei passi di una variante, archi originali attraversati da ciascun passo e passaggi condizionati verso i successivi. Si possono interrogare diramazioni, ricongiungimenti e cicli. |
| `evidence`, `version_evidence` | Ogni prova è ancorata all’analisi che l’ha prodotta. Può indicare un percorso del progetto, righe, simbolo e oggetto Git, oppure una posizione dentro una precisa versione di un risultato tecnico. Più oggetti possono citare la stessa prova. |
| `technical_records`, `gaps` | Risultati dei singoli strumenti con il loro payload JSON, e lacune con oggetto interessato, causa e possibile rimedio. Entrambi hanno una storia. |
| `manual_edits`, `conflicts`, `conflict_evidence` | Campo modificato, valore di partenza, scelta dell’utente e revisione di partenza. Il conflitto conserva il valore proposto dalla rianalisi, la sua provenienza e le sue prove fino alla risoluzione e dopo. |

### Identità e storia

- `user_version` identifica il formato su disco. `analyses.daodan_version` identifica l'analizzatore. La versione dei sorgenti viene da `source_snapshots`; `revisions.revision_uuid` identifica la revisione della mappa. Un edit manuale eredita l'analisi di riferimento. Una rianalisi ne registra una nuova, anche sullo stesso commit. Le date sono UTC in formato RFC 3339.
- Per un checkout Git pulito si conserva il commit completo con la sua data. Per cartelle senza Git o alberi modificati è obbligatoria l'impronta del perimetro effettivamente analizzato. L'eventuale commit di base resta disponibile. La politica d'inventario versionata in `inventory_policy` dichiara selezione e algoritmo. Un file cambiato mentre si calcola l'impronta richiede di rileggere l'input, affinché il digest descriva i byte analizzati. Per la v1, in ordine binario dei percorsi relativi UTF-8 con separatore `/`, si concatena per ogni file la lunghezza del percorso in byte (intero senza segno a 64 bit big endian), il percorso e il digest SHA-256 binario dei byte analizzati. `tree_sha256` è il digest SHA-256 esadecimale minuscolo della concatenazione. Il perimetro rispetta le esclusioni di Daodan anche per gli hash.
- Ogni copia porta la storia lineare e gli UUID già assegnati. Una nuova revisione usa un UUID nuovo. Dopo una copia, due revisioni con numero locale 8 e genitore comune possono così rappresentare storie diverse. Per confrontare copie si usano UUID di progetto e revisione; gli ID numerici delle righe valgono dentro una copia.
- Lo stato alla revisione R comprende le versioni con `from_rev <= R` e `until_rev IS NULL OR R < until_rev`. Creare apre un intervallo, modificare chiude il vecchio e apre il nuovo, eliminare chiude quello attivo. Anche prove, ingressi, archi di un passo e transizioni appartengono alla versione del loro proprietario: cambiarli apre una nuova versione. Un diff confronta le versioni ai due estremi per ID oggetto e dettaglia i campi e le relazioni cambiati. Il changelog usa le revisioni, i loro autori e le versioni aperte o chiuse in ciascuna.
- Le nature si ricavano da specie, posizione e contenuto dei gruppi secondo l'architettura. «Realizzato da» e «gira su» sono archi. Frecce riassunte, conteggi e geometria della GUI sono dati derivati. Per un profilo, una riga con `profile IS NULL` è comune a tutti. I gradi di Daodan (per esempio dichiarato, provato, osservato e incerto) si conservano senza promozione; eventuali qualificatori del produttore, come il campionamento, restano negli attributi. La provenienza dell'edit appartiene alla versione.

### Integrità al salvataggio

Le chiavi esterne vanno abilitate a ogni apertura. In una sola transazione di scrittura il writer confronta la revisione attesa con `project.head_rev`, inserisce la revisione e i cambiamenti, verifica lo stato risultante e aggiorna la testa. Un errore annulla tutto. A testa cambiata si rilegge il progetto e si ricalcola la modifica. Creare il progetto inserisce snapshot, analisi, revisione 1 e unica riga di `project` insieme. [Chiavi esterne SQLite](https://sqlite.org/foreignkeys.html)

Oltre ai vincoli SQL, chi scrive verifica queste condizioni prima del commit; chi importa un file le verifica sulla storia importata.

1. La testa coincide con l'ultima revisione. Per un oggetto gli intervalli sono disgiunti. Ogni versione ha una sola riga nella tabella del suo tipo. Gli ID oggetto restano unici e conservano il tipo. Gli oggetti creati manualmente ricevono un UUID, così le aggiunte indipendenti in due copie restano distinguibili. Nella storia già salvata sono modificabili soltanto la fine di un intervallo aperto e il riferimento alla risoluzione di un conflitto. La riga di progetto avanza alla nuova testa. Ogni altro cambiamento aggiunge una revisione.
2. Un padre è un nodo attivo e la gerarchia è aciclica. Gli estremi degli archi, gli ingressi, gli esiti e l'eventuale funzionalità di un flusso sono nodi attivi nella medesima revisione. Una variante appartiene a un flusso attivo e un passo a una variante attiva. Spostamenti e cancellazioni sistemano nello stesso commit tutti i riferimenti coinvolti. Le prove storiche continuano a puntare alla fonte originaria.
3. Gli archi di un passo sono attivi per quel profilo e ne rispettano verso e condizioni. Le transizioni collegano solo passi della stessa variante. L'ordine di presentazione è distinto dalla causalità. Due transizioni possono ricongiungersi sullo stesso passo; due passi distinti possono citare lo stesso arco. Un passaggio non dimostrato resta una lacuna. Una prova `artifact` cita una versione immutabile di un record tecnico e il punto del risultato che la sostiene.
4. Un edit identifica il campo con JSON Pointer relativo all'oggetto, anche per i dettagli del flusso; la stringa vuota riguarda l'oggetto intero. I passi si modificano tramite ID di occorrenza. Per un elenco ordinato, come gli archi di un passo, un edit confronta l'intero campo: l'indice numerico di una riga non identifica un elemento dopo un riordino. Il valore ha la forma `{"present":true,"value":...}` oppure `{"present":false}`, così un campo assente si distingue da JSON null. Per ogni campo si applica l'ultimo edit attivo. `release` chiude la scelta manuale. Anche un intervento sul medesimo campo o una rimozione del suo oggetto da parte dell'analizzatore usa il confronto a tre vie. Un conflitto aperto conserva visibile la scelta manuale e permette di consultare il valore in arrivo. La risoluzione registra un nuovo edit nella revisione indicata da `resolved_rev`, scegliendo quale valore tenere o tornando a seguire l'analisi.

## Esempio di lettura e revisione

Per leggere i figli di un gruppo in una revisione storica:

```sql
SELECT v.object_id, n.name
FROM nodes AS n
JOIN versions AS v ON v.version_id = n.version_id
WHERE n.parent_id = :group_id
  AND v.from_rev <= :rev AND (v.until_rev IS NULL OR :rev < v.until_rev)
ORDER BY n.name, v.object_id;
```

In Bank of Anthos, «Pagamento a un contatto» ha un solo ID di flusso. Sullo stesso commit il profilo `kubernetes-standard` porta da Ledgerwriter a Balancereader e `ledger-monolith` legge il saldo dalla cache di Ledgermonolith. Le varianti collegano i rispettivi passi e ciascun passo cita i propri archi. Cambiare profilo nella GUI seleziona una variante della stessa revisione.

| Revisione esemplificativa | Righe interessate |
|---|---|
| R1, analisi | Inserisce snapshot S1, analisi A1 e flusso F con nome originale. |
| R2, una persona rinomina F | Stessa A1. Chiude la versione precedente di F, ne apre una con il nuovo nome e registra un edit su `/name` con base R1. Nodi e archi conservano le righe esistenti. |
| R3, rianalisi | Registra A2. Se cambia solo un arco, F conserva il nome manuale. Se l'analisi propone un terzo nome, `conflicts` collega tale valore all'edit R2. |
| R4, risoluzione | La scelta viene registrata con autore. Riaprendo R3 il conflitto risulta ancora aperto; in R4 si vede l’esito. |

Il vecchio esempio Bank of Anthos si riconosce come ZIP con `project.json` e `v2/graph.sqlite`. Quest'ultimo contiene cinque tabelle e ha un identificativo SQLite diverso. L’eventuale importazione conserva l’originale e recupera dal manifest revisioni e provenienza. Per una versione dell’analizzatore o un'opzione storica irrecuperabile registra rispettivamente il valore riservato «unknown» o un elenco dei campi ignoti nella configurazione di importazione, e una lacuna con la causa. Cambiare estensione o cambiare solo `user_version` non converte il contenuto.
