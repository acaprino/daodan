# ADR: il grafo dei moduli nasce dai flussi

- **Stato:** proposto. Le decisioni 1, 2, 3, 6b e 7 riportano parole del proprietario del 18 novembre 2026; le decisioni 4, 5 e 6a hanno il principio suo e la forma proposta, da confermare.
- **Data:** 2026-11-18
- **Ambito:** `plugins/codebase-map/skills/map/scripts/` (`flows.py`, `visual.py`, `module_derive.py`, `app.py`, `app_view.py`, `registry_build.py`), `plugins/codebase-map/skills/map/data/`, `benchmarks/connection-points/`, `docs/plugins/`
- **Si appoggia a:** la guida [Punti di connessione](../research/2026-11-14-punti-di-connessione.md) (ruoli, tipi, chiavi), la spec [Flussi e unità](../specs/2026-11-09-flow-model.md) (le regole di collegamento), la spec [Mappa del sistema](../specs/2026-11-12-mappa-del-sistema.md) (il registro dei servizi esterni). Questo ADR non le ripete: dice cosa da oggi è deciso.

## Contesto e problema

Il 18 novembre 2026 l'app standalone ha analizzato `github-samples/pets-workshop` fino in fondo e ha mostrato un grafo con un nodo solo, poi con sedici gruppi e due relazioni. Tre cause:

1. Il grafo dell'app nasceva solo da import e chiamate dentro lo stesso linguaggio. I flussi esistevano (`flows.py`) ma l'app non li eseguiva, e un flusso trovato restava un elenco a parte: non diventava mai una relazione fra moduli.
2. `flows.py` univa una richiesta alla sua rotta solo a testo identico: `/api/dogs/${dogId}` e `/api/dogs/<int:id>` non si incontravano.
3. Le regole di collegamento le scrive un modello per ogni progetto, e l'app non aveva quel passaggio.

## Decisioni

### 1. Lo scopo: il grafo dei moduli, e le sue relazioni sono i flussi

Daodan esiste per creare il grafo dei moduli. Un grafo che non trova le relazioni è inutile. Un flusso è ogni ingresso → processo → uscita, qualunque sia l'ingresso: un controllo o un'azione dell'interfaccia, una richiesta HTTP, un socket o un altro protocollo, un watcher che si attiva, un trigger, un'attivazione a orario. Una vista per directory o per import non è il grafo.

### 2. Si censiscono i tipi di legame; le implementazioni restano aperte

Daodan tiene il censimento dei tipi di legame: tre coppie chiuse di ruoli (chiama/offre, scrive/legge, emette/ascolta) e tipi aperti, ognuno con un nome, una coppia e la forma della sua chiave. Come un progetto o un framework scrive un legame non sta nel codice di Daodan né in regole incorporate: sono indicazioni, date come suggerimenti a chi scrive le regole del progetto. Nessun nome di framework nel codice.

### 3. Un motore generale e un adattatore per tipo di legame

Il motore unisce i punti per coppia di ruoli e chiave e non conosce nessun tipo. Un tipo è un adattatore con un solo contratto: il nome, la coppia, come un valore diventa una chiave o una lacuna, come due chiavi si incontrano (certo, incerto, no). Se c'è il legame lo decide sempre l'adattatore, cioè codice con i suoi test. Il primo è REST, con chiave metodo e schema del percorso.

### 4. Non tutto lo scibile: tre livelli

Non si può prevedere ogni tipo di scambio fra due nodi. Si danno basi solide e una gamma vasta di casi reali.

- Un tipo conosciuto ha il suo adattatore, ed entra nel prodotto con un caso reale in `benchmarks/`, attese scritte prima del codice.
- Un tipo non previsto si esprime nelle regole del progetto e lo unisce il motore generale, a chiave uguale.
- Ciò che nulla unisce resta una lacuna dichiarata o un lato singolo spiegato: mai un legame inventato.

### 5. Il modello propone, la macchina verifica

L'aiuto del modello ha quattro posti: scrive le regole del progetto, una volta; riceve solo i resti (i lati singoli e le lacune) e propone una correzione alle regole, che la macchina riapplica; sceglie fra candidati incerti, e il legame resta marcato `proposto`; dà i nomi. Ogni legame dice da dove viene: trovato nel codice, dedotto da una regola, proposto dal modello. Le regole si salvano accanto allo snapshot, così rifare il grafo non richiama il modello. Senza modello Daodan funziona e dichiara le lacune.

### 6. L'anagrafica di ciò che Daodan supporta

- **a. Framework:** almeno 200 riconosciuti ed elaborati. La forma proposta: per ogni framework i segni per riconoscerlo e i suggerimenti sui suoi legami come dati, più un caso reale misurato; nessun codice per framework.
- **b. Servizi esterni:** almeno 500 riconoscibili con il marchio, per disegnarli come nodi esterni. Il marchio viene da Simple Icons e, dove manca, dall'SVG ufficiale pubblicato dal proprietario del servizio; i file stanno nel prodotto, ripuliti, con l'origine annotata. Le raccolte di icone dei fornitori cloud (AWS, Azure, Google Cloud), le cui condizioni parlano di diagrammi e non di ridistribuzione, non si distribuiscono: Daodan le scarica dalla fonte ufficiale al primo uso, sulla macchina di chi lo usa; poi verranno ridisegnate dal proprietario.

### 7. Una tabella generata di ciò che è supportato

Un documento diviso per tipologia (linguaggi, build tool e toolchain, framework e librerie, servizi esterni, tipi di legame), con copertura e percentuale di riuscita dove una misura esiste. Lo genera uno script dai dati del prodotto e dai risultati dei benchmark, e un test fallisce se resta indietro.

## Stato al 18 novembre 2026

| Decisione | Stato |
| --- | --- |
| 3. Motore, adattatore REST | scritto e provato su Modal, non ancora su `main` |
| 1. Un legame diventa relazione fra moduli | in lavorazione |
| 5. Regole dal modello nell'app, giro sui resti | da fare; le regole dal modello esistono nel plugin |
| 6b. Marchi dei servizi | in lavorazione; partenza 222 servizi riconoscibili con marchio su 495 |
| 6a. Suggerimenti per framework | da fare |
| 7. Tabella generata | in lavorazione |

## Vincoli invarianti

- **Regola invalicabile:** nessun codice del progetto analizzato gira mai sull'host.
- Nessun nome di framework nel codice che unisce i legami.
- Nessun legame senza la sua provenienza e la sua evidenza; un legame incerto non si disegna come certo.
