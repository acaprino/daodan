# Piano: mappa del sistema, parte 1

> **Per chi esegue:** un task alla volta, nell'ordine; segnare solo i passi verificati. Sub-skill: `superpowers:executing-plans` oppure `superpowers:subagent-driven-development`.

**Obiettivo:** Daodan produce e verifica la mappa del sistema di un progetto (nodi con nome, flussi, livelli) e misura quanto costa e quanto è giusta.

**Funzionamento:** la macchina riconosce servizi e progetti esterni da un registro e compone una scheda del sistema; un agente propone nodi e flussi in un formato fisso; la macchina accetta solo ciò che i collegamenti di `flows.py` provano e registra il resto come rifiutato. I livelli si calcolano dal grafo di un flusso, non li scrive l'agente.

**Tecnologie:** Python 3 con la sola libreria standard negli script del plugin; Node solo per costruire il registro e per stack-analyser 1.27.6; Modal e `claude -p` per le run cieche; Markdown.

**Spec:** [`docs/specs/2026-11-12-mappa-del-sistema.md`](../specs/2026-11-12-mappa-del-sistema.md). Questo piano copre i passi 1, 2 e 3 del suo ordine di lavoro e le misure da 1 a 6. Esploratore (passo 4) e review (passo 5, misure 7 e 8) hanno un piano ciascuno, dopo queste misure.

## Vincoli

- Un nodo non è mai un simbolo da solo; non ogni dipendenza è un nodo.
- Tipi di nodo: quelli di `flows.NODE_TYPES` più `entità`. Posizioni: `internal`, `external`, `unseen`.
- Tipi di flusso: `funzionale`, `operativo`, `tecnico`, `dati`, `hardware`. Livelli: `persone`, `funzioni`, `dati`, `codice`, `infrastruttura`.
- Aree da passare in rassegna: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente; integrazioni esterne; comunicazioni; amministrazione; esercizio.
- Registro: almeno 1.000 voci alla prima versione. Fonti ammesse: stack-analyser (MIT), Simple Icons 16.37.0 (CC0), CNCF Landscape (CC BY 4.0, con attribuzione). I dati di webappanalyzer (GPL-3.0) non si copiano.
- stack-analyser è una fonte in più: se manca Node o la rete, l'analisi continua e dichiara la lacuna.
- Nessun codice del progetto analizzato viene eseguito. Il codice di phazly non entra nel repository: nel benchmark stanno solo nomi di file e valori attesi.
- Soglie e parametri si scrivono nel README del benchmark prima di misurare. Le run cieche girano in un processo nuovo, su Modal.
- Run a pagamento: stimare il costo e chiedere prima di lanciare.
- Nessun bump di versione. Documenti in italiano al presente; reference e agenti in inglese, come sono. Commit locali su main; push solo su richiesta.
- Test: `python -B -m pytest -q -p no:cacheprovider tests/<file>`.

## Punti da presidiare

Ingressi che la spec implica e che è facile lasciare scoperti. Ognuno ha il suo test nel task indicato.

1. Una proposta cita un membro che non esiste o una chiave di store scritta male: il nodo è rifiutato con il nome del membro, senza errore del programma (Task 2).
2. Una freccia unisce due nodi veri che nessun collegamento lega, oppure cita un punto che non esiste: è rifiutata con il motivo (Task 2).
3. Un pacchetto locale del progetto ha lo stesso nome di un servizio del registro: non diventa un servizio esterno (Task 6).
4. Node o la rete mancano: stack-analyser risulta `unavailable`, il riconoscimento del registro resta (Task 7).
5. Una chiave che quasi tutti i punti d'ingresso toccano: non fonde tutti i gruppi candidati in uno (Task 8).

## File

| File | Compito |
| --- | --- |
| `plugins/codebase-map/skills/map/scripts/system_map.py` | Formato, validazione, verifica, copertura, registrazione, freschezza, ricerca per nome |
| `plugins/codebase-map/skills/map/scripts/system_levels.py` | Vista di un flusso a uno o più livelli |
| `plugins/codebase-map/skills/map/scripts/service_registry.py` | Lettura del registro e riconoscimento in uno snapshot |
| `plugins/codebase-map/skills/map/scripts/registry_build.py` | Costruzione del registro dai cataloghi pubblici (strumento di sviluppo) |
| `plugins/codebase-map/skills/map/data/service-registry.json` | Il registro distribuito |
| `plugins/codebase-map/skills/map/data/registry-additions.json` | Voci e segni che i cataloghi non hanno, verificati |
| `plugins/codebase-map/skills/map/scripts/stack_analyser.py` | Esecuzione di stack-analyser dalla cache di Daodan |
| `plugins/codebase-map/skills/map/scripts/system_brief.py` | Scheda del sistema |
| `plugins/codebase-map/skills/map/scripts/mcp_service.py`, `mcp_server.py` | `codebase_map_flows` con `brief`, `map`, `about`, `levels` |
| `plugins/codebase-map/skills/map/references/system-map.md` | Formato e regole per chi propone |
| `plugins/codebase-map/agents/system-mapper.md` | L'agente |
| `benchmarks/system-map/` | README, riferimenti attesi, `score.py`, `modal_map.py` |
| `tests/test_codebase_map_system_*.py`, `tests/test_codebase_map_service_registry.py` | Test |

I test della Parte A usano la fixture `benchmarks/flow-model/app` con `rules.json`, come `tests/test_codebase_map_flows.py`.

## Parte A: la mappa e la sua verifica

### Task 1: formato e validazione

**File:** crea `system_map.py`, `tests/test_codebase_map_system_map.py`.

**Interfacce.** Produce:

```python
SCHEMA = "daodan/system-map/v1"
NODE_TYPES = flows.NODE_TYPES + ("entità",)
POSITIONS = ("internal", "external", "unseen")
FLOW_TYPES = ("funzionale", "operativo", "tecnico", "dati", "hardware")
AREAS = ("accesso e identità", "funzioni principali", "pagamenti e abbonamenti", "dati dell'utente",
         "integrazioni esterne", "comunicazioni", "amministrazione", "esercizio")
def validate(value: object) -> dict   # {"schema", "nodes", "flows", "areas"}; ValueError che nomina il campo
```

Un nodo: `{"name", "type", "position", "members": [...], "evidence": [...], "on": [...], "where": str}`. Membri: `percorso`, `percorso::Simbolo`, `store:<store>/<chiave>`, `module:<nome>`; una rotta si cita con il simbolo del suo handler. `on` nomina i nodi su cui il nodo gira o in cui vive. Un flusso: `{"name", "area", "types", "nodes", "arrows": [{"from", "to", "data", "cite", "same"}], "paths"}`. Un'area: `{"name", "present": bool}`.

- [ ] **Passo 1:** test che falliscono. `validate` rifiuta, nominando il campo: un tipo fuori elenco; due nodi con lo stesso nome a meno di maiuscole e accenti; un nodo `internal` senza membri; un nodo `external` con membri; un nodo `unseen` senza `where`; un flusso che nomina un nodo assente; una freccia senza `data`; un'area dell'elenco `AREAS` non dichiarata né presente né assente; un campo sconosciuto.
- [ ] **Passo 2:** implementare `validate`; i test passano.
- [ ] **Passo 3:** commit.

### Task 2: verifica di nodi e frecce

**File:** modifica `system_map.py`, `modules.py` (due funzioni pubbliche), i test del Task 1.

**Interfacce.** Consuma `flows.link_facts(manifest, rules)`: archi `{"from", "to", "type", "origin", "site"}`, `stores`, `entries`. Produce:

```python
# modules.py
def resolve_members(manifest: Path, texts: list[str]) -> list[dict]   # come _member: {"id","kind","path","resolved","reason"}
def resolve_evidence(manifest: Path, texts: list[str]) -> list[dict]  # come _evidence
# system_map.py
def verify(manifest: Path, links: dict, value: dict) -> dict
# {"nodes": [{"name", "status": "accepted"|"refused", "reason", "files": [...]}],
#  "flows": [{"name", "status", "arrows": [{"from", "to", "status": "proved"|"declared"|"refused", "proof": [siti], "reason"}]}]}
```

Regole. Un nodo con codice è accettato se ogni membro esiste: file e simboli nello snapshot, chiavi di store in `links["stores"]`, moduli nel grafo. Un nodo senza codice è accettato se la sua evidenza si risolve; `unseen` basta `where`. Una freccia è `proved` da un arco fra un membro del primo nodo e un membro del secondo nel verso indicato (un arco `scrive` prova nodo → entità, un arco `legge` entità → nodo), oppure da `scrive` e `legge` sulla stessa chiave, dal primo al secondo. È `declared` se un capo è senza codice o se `same` è vero, e `cite` è un `percorso:riga` che esiste; se l'altro capo ha codice, il percorso citato è fra i suoi file. Altrimenti è `refused`. `on` nomina solo nodi accettati. Un flusso è accettato se ha almeno una freccia non rifiutata e tutti i suoi nodi accettati.

Mappa di prova sulla fixture: `Cliente` (attore, esterno, evidenza `web/checkout.ts`), `Checkout` (schermata, `web/checkout.ts`), `Badge pagamento` (schermata, `web/badge.ts`), `API pagamenti` (servizio o API, `server/payments.py` e `server/gateway.py`), `Pagamento` (entità, `store:db/payments` e `store:web state/payment`), `card payment provider` (gateway, esterno, evidenza `server/gateway.py`), `Riprova` (funzionalità, `server/jobs.py`). Due flussi: `Pagare un ordine` (funzionale, con i primi sei nodi) e `Riprova dei pagamenti` (operativo, con `Pagamento` e `Riprova`).

- [ ] **Passo 1:** test che falliscono.

```python
proved = {(a["from"], a["to"]) for flow in report["flows"] for a in flow["arrows"] if a["status"] == "proved"}
assert {("Checkout", "API pagamenti"), ("API pagamenti", "Pagamento"), ("Pagamento", "Badge pagamento"),
        ("Checkout", "Badge pagamento"), ("Pagamento", "Riprova")} <= proved
assert status("Cliente", "Checkout") == "declared" and status("API pagamenti", "card payment provider") == "declared"
assert status("Badge pagamento", "API pagamenti") == "refused"            # nessun collegamento
assert node("Fantasma")["status"] == "refused" and "web/nope.ts" in node("Fantasma")["reason"]
assert "db/paymnts" in node("Refuso")["reason"]                           # chiave scritta male
assert status_with_cite("Cliente", "Checkout", "web/checkout.ts:9999") == "refused"
```

- [ ] **Passo 2:** implementare; i test passano, compresi quelli di `tests/test_codebase_map_modules*.py`.
- [ ] **Passo 3:** commit.

### Task 3: copertura, registrazione, conferma, freschezza

**File:** modifica `system_map.py` e i suoi test.

**Interfacce.** Produce:

```python
def record(manifest: Path, rules: list[dict], value: object) -> dict  # valida, verifica, scrive system-map.json accanto al manifest con le sole parti accettate
def load(manifest: Path, rules: list[dict]) -> dict | None            # mappa registrata più quella dichiarata, riverificata; ogni nodo e flusso ha "status", "fresh", "changed_files"
def about(system: dict, name: str) -> dict                            # area, flusso o nodo: flussi, nodi, file dei membri, esterni, nodi non visti
```

`record` e `load` restituiscono anche `"coverage": {"entries": {"in", "of", "left"}, "stores": {...}, "routes": {...}}`: un punto d'ingresso, una chiave o una rotta è dentro quando appartiene a un nodo di un flusso accettato. Il progetto conferma con `codebase-system-map.json` nella radice (`daodan/declared-system-map/v1`, stessi record): un record dichiarato ha stato `confirmed` se verificato e sostituisce la proposta con lo stesso nome, che esce come lacuna `proposal_superseded`. I nodi senza codice accettati si registrano anche come moduli `external` proposti, con `modules.propose`.

- [ ] **Passo 1:** test che falliscono. Sulla mappa di prova: `coverage["entries"]` vale 3 su 6 e lascia fuori `web/cart.ts::toggleTheme`, `server/orders.py::list_orders`, `admin/orders.py::list_all_orders`; `coverage["stores"]` 2 su 4; `coverage["routes"]` 1 su 3. Il file registrato non contiene il nodo e la freccia rifiutati. Dopo una modifica a `web/badge.ts` e un `snapshot refresh`, `load` dà `fresh` falso solo a `Badge pagamento` e al flusso che lo contiene. Un nodo dichiarato `Checkout` resta `confirmed` quando una nuova proposta lo rinomina. `about(m, "Pagamento")` elenca i due flussi che attraversano quel nodo; `about(m, "pagamenti e abbonamenti")` elenca i flussi dell'area con i file dei loro nodi.
- [ ] **Passo 2:** implementare; i test passano.
- [ ] **Passo 3:** commit.

### Task 4: livelli

**File:** crea `system_levels.py`, `tests/test_codebase_map_system_levels.py`.

**Interfacce.** Consuma la mappa di `load`. Produce:

```python
LEVELS = ("persone", "funzioni", "dati", "codice", "infrastruttura")
def view(system: dict, flow: str, levels: list[str], links: dict | None = None) -> dict
# {"flow", "levels", "nodes": [{"name", "type", "level", "position", "also": {livello: [nomi]}}],
#  "arrows": [{"from", "to", "data", "through": [nodi nascosti]}], "absent": [livelli senza nodi]}
```

Regole. Livello di casa per tipo: attore e schermata `persone`; entità `dati`; database e dispositivo `infrastruttura`; gli altri `funzioni`. Un servizio esterno compare anche a `infrastruttura`. A `infrastruttura` un nodo con `on` è sostituito dai nodi che nomina. A `codice` un nodo è sostituito dai file dei suoi membri toccati dai collegamenti del flusso, e servono i `links`. Una freccia fra due nodi visibili è la contrazione di un cammino i cui nodi intermedi sono nascosti. Con più livelli si mostrano i nodi di tutti; `also` elenca, per ogni nodo, i suoi corrispondenti agli altri livelli.

- [ ] **Passo 1:** test che falliscono, sul flusso `Pagare un ordine` della mappa di prova con `API pagamenti` che ha `on: ["Server shop"]` (dispositivo, esterno, evidenza `server/http.py`).

```python
assert names(view(m, "Pagare un ordine", ["persone"])) == {"Cliente", "Checkout", "Badge pagamento"}
assert ("Checkout", "Badge pagamento") in arrows(view(m, "Pagare un ordine", ["persone"]))
assert names(view(m, "Pagare un ordine", ["dati"])) == {"Pagamento"}
assert {"Server shop", "card payment provider"} <= names(view(m, "Pagare un ordine", ["infrastruttura"]))
assert "server/payments.py" in names(view(m, "Pagare un ordine", ["codice"], links))
assert view(m, "Riprova dei pagamenti", ["persone"])["absent"] == ["persone"]
assert view(m, "Pagare un ordine", list(LEVELS), links)["nodes"][0]["also"]     # corrispondenze presenti
```

- [ ] **Passo 2:** implementare; i test passano.
- [ ] **Passo 3:** commit.

## Parte B: registro e scheda

### Task 5: costruzione del registro

**File:** crea `registry_build.py`, `data/service-registry.json`, `data/registry-additions.json`, `data/REGISTRY-NOTICES.md`, `tests/test_codebase_map_service_registry.py`.

**Interfacce.** Produce il file `daodan/service-registry/v1`:

```json
{"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com", "icon": "stripe",
 "signs": {"packages": {"npm": ["stripe"], "pypi": ["stripe"]}, "env": ["STRIPE_"], "hosts": ["api.stripe.com"], "files": []},
 "from": ["stack-analyser", "additions"]}
```

`kind` è `service` o `project`. `registry_build.py build --out FILE` scarica le fonti alle versioni fissate, valuta ogni file di regole di stack-analyser in Node con `register` sostituito da una raccolta, aggancia il marchio di Simple Icons per nome, aggiunge le voci del CNCF Landscape con nome, categoria e sito, e unisce `registry-additions.json`. `registry_build.py check FILE` verifica senza rete: identificatori unici, tipo in `NODE_TYPES`, almeno 1.000 voci, ogni voce con almeno un segno oppure marcata `"signs": null`. `registry_build.py verify-additions` controlla in rete che ogni pacchetto esista nel suo registro e che il sito risponda.

- [ ] **Passo 1:** test che falliscono: `check` sul file distribuito passa; conta almeno 1.000 voci; contiene `stripe` con `pypi: ["stripe"]`, `mongodb`, `fastapi`, `react`, `docker`; nessuna voce viene da webappanalyzer.
- [ ] **Passo 2:** implementare `registry_build.py`. I pacchetti che i cataloghi coprono solo per npm si ricavano prima senza modello, con `registry_build.py derive`: per ogni voce con un pacchetto npm cerca su PyPI, crates.io e nel proxy di Go un pacchetto con lo stesso nome, o con il nome senza prefisso e suffisso, e lo tiene solo se il proprietario del suo repository è lo stesso del pacchetto npm. In una prova su 16 servizi ne trova 12. Ciò che resta (nomi diversi, come `pymongo` o `sentry-sdk`) lo propone un modello economico in una sola run, tenuto solo se supera lo stesso controllo: stimare il costo e chiedere prima. Tutto finisce in `registry-additions.json`.
- [ ] **Passo 3:** `build`, `verify-additions`, `check`; scrivere `REGISTRY-NOTICES.md` con licenza MIT di stack-analyser e attribuzione CC BY 4.0 del CNCF Landscape; i test passano.
- [ ] **Passo 4:** commit.

### Task 6: riconoscimento nello snapshot

**File:** crea `service_registry.py`; modifica il test del Task 5.

**Interfacce.** Consuma il grafo dei moduli (`dependencies` di ogni unità di build, ecosistema dal suo `kind`) e il testo dei file dello snapshot. Produce:

```python
def load(path: Path | None = None) -> dict
def recognize(manifest: Path) -> list[dict]
# {"id", "name", "kind", "type", "site", "icon", "source": "registry",
#  "signs": [{"sign": "package"|"env"|"host"|"file", "value", "path", "line"}]}
```

- [ ] **Passo 1:** test che falliscono, su un progetto temporaneo con `package.json` (`stripe`, `react`), `requirements.txt` (`stripe`, `fastapi`), un file che legge `STRIPE_SECRET_KEY`, un `Dockerfile` e un pacchetto locale del workspace chiamato `resend`: sono riconosciuti `stripe` (con tre segni, ciascuno con percorso), `react`, `fastapi`, `docker`; `resend` no, perché è un'unità di build del progetto.
- [ ] **Passo 2:** implementare; i test passano.
- [ ] **Passo 3:** commit.

### Task 7: stack-analyser come fonte in più

**File:** crea `stack_analyser.py`, `tests/test_codebase_map_stack_analyser.py`.

**Interfacce.** Produce:

```python
VERSION = "1.27.6"
def run(root: Path, cache: Path, files: set[str]) -> dict
# {"status": "ok", "version", "seconds", "found": [{"tech", "name", "paths": [...]}]}
# {"status": "unavailable", "reason"}
```

Installa una volta nella cache con `npm install --prefix <cache>/stack-analyser-1.27.6 --ignore-scripts --no-audit --no-fund @specfy/stack-analyser@1.27.6`. Esegue `node …/dist/cli.js <root> --output=out.json` con la cartella di lavoro in una cartella temporanea: lo strumento unisce il percorso d'uscita alla cartella di lavoro. Tiene solo i ritrovamenti i cui percorsi stanno in `files`.

- [ ] **Passo 1:** test che falliscono: con un `node` finto nel `PATH` che scrive un risultato noto, `run` restituisce `ok` e scarta un percorso fuori da `files`; senza `node` restituisce `unavailable` con il motivo; con un `node` che esce con errore restituisce `unavailable` e non solleva.
- [ ] **Passo 2:** implementare; i test passano.
- [ ] **Passo 3:** commit.

### Task 8: scheda del sistema

**File:** crea `system_brief.py`, `tests/test_codebase_map_system_brief.py`.

**Interfacce.** Consuma `flows.cached_links`, `service_registry.recognize`, `stack_analyser.run`, `modules.load_graph`, `system_map.load`. Produce:

```python
CAP = 24_000        # caratteri, parametro del benchmark
HUB_SHARE = 0.2     # oltre questa quota di punti d'ingresso, una chiave, una rotta o un esterno non lega
def brief(manifest: Path, rules: list[dict], *, cap: int = CAP, hub_share: float = HUB_SHARE) -> dict
# {"schema": "daodan/system-brief/v1", "steps": {"statico", "inferenza", "dinamico", "semantico"},
#  "modules", "externals", "other_dependencies": {unità: quante}, "runtime_files",
#  "groups": [{"id", "entries", "files", "stores", "externals"}],
#  "confirmed": [nomi], "text": str, "truncated": int}
```

`externals` unisce registro e stack-analyser e dice per ognuno da quale fonte viene; le dipendenze che nessuna fonte riconosce restano contate per unità di build in `other_dependencies`. `runtime_files` elenca i file che configurano esecuzione e rilascio (`Dockerfile`, `docker-compose*`, `*.tf`, manifest di hosting e di CI). Un gruppo candidato è una componente connessa dei punti d'ingresso che condividono una chiave di store, una rotta o un esterno, esclusi quelli sopra `hub_share`. `text` è la scheda da dare all'agente, entro `cap`: oltre il tetto i gruppi con meno collegamenti diventano una riga e `truncated` li conta.

- [ ] **Passo 1:** test che falliscono, sulla fixture: i punti d'ingresso `web/checkout.ts::onPayClick`, `server/payments.py::create_payment` e `server/jobs.py::retry_declined` stanno nello stesso gruppo e `web/cart.ts::toggleTheme` in un altro; con una chiave aggiunta che tutti toccano i gruppi restano gli stessi; `steps["dinamico"]` è falso; con `cap=600` il testo sta nel tetto e `truncated` è maggiore di zero; `externals` contiene `card payment provider` con la sua fonte.
- [ ] **Passo 2:** implementare; i test passano.
- [ ] **Passo 3:** commit.

## Parte C: agente e misure

### Task 9: lo strumento

**File:** modifica `mcp_service.py`, `mcp_server.py`, `references/mcp.md`, `tests/test_codebase_map_mcp.py`; crea `references/system-map.md`.

**Interfacce.** `flows(self, run_id, …, brief=False, map=None, about=None, levels=None)`:

- `brief=True` restituisce la scheda del sistema, il formato e l'elenco delle aree; senza regole registrate resta `needs_rules`.
- `map={…}` chiama `system_map.record` e restituisce il rapporto: accettati, rifiutati con il motivo, copertura.
- `about="nome"` restituisce `system_map.about`; con `levels=[…]` e un flusso restituisce `system_levels.view`.
- Senza questi parametri lo strumento risponde come oggi.

`references/system-map.md`, in inglese, entro 80 righe: formato, tipi, posizioni, regole della prova di una freccia, aree, un solo giro di correzione.

- [ ] **Passo 1:** test che falliscono: il servizio, sulla fixture, risponde a `brief`, registra la mappa di prova, risponde ad `about="Pagare un ordine"` con i file dei membri e, con `levels=["persone"]`, con i tre nodi attesi; una mappa non valida dà un errore che nomina il campo.
- [ ] **Passo 2:** implementare e documentare; i test passano, compresa la suite MCP esistente.
- [ ] **Passo 3:** commit.

### Task 10: l'agente

**File:** crea `plugins/codebase-map/agents/system-mapper.md`.

Corpo in inglese, entro 40 righe. Strumenti: `codebase_map_flows`, `codebase_map_search`, `codebase_map_read`, `codebase_map_modules`. Sequenza fissa: una chiamata `brief`; una proposta per tutto il sistema o per l'area richiesta; lettura del rapporto e una sola correzione di ciò che è stato rifiutato; risposta finale con i soli conteggi. Regole: nomi come li direbbe chi usa il prodotto; mai un nodo per simbolo; ogni area dell'elenco dichiarata presente o assente; il sorgente si apre solo quando la scheda non basta a decidere un nome o un taglio; i nomi confermati non si toccano. Il modello nel frontmatter si fissa dopo la misura 4.

- [ ] **Passo 1:** scrivere l'agente e verificare che `claude plugin validate` (o il caricamento del plugin) lo accetti.
- [ ] **Passo 2:** commit.

### Task 11: benchmark, soglie e misure senza modello

**File:** crea `benchmarks/system-map/README.md`, `expected/phazly-payments.json`, `expected/externals-phazly.json`, `expected/externals-polar.json`, `expected/externals-tududi.json`, `score.py`.

**Interfacce.** `score.py map MAP.json EXPECTED.json` stampa nodi ritrovati (un nodo atteso è ritrovato se un nodo proposto ha almeno metà dei file in comune, indice di Jaccard), flussi ritrovati (almeno due terzi dei nodi attesi), frecce accettate e rifiutate, copertura. `score.py externals RECOGNIZED.json EXPECTED.json` stampa richiamo e riconoscimenti sbagliati.

Soglie proposte, da scrivere nel README prima di ogni misura; il proprietario può cambiarle:

| Misura | Soglia |
| --- | --- |
| 1 Riproduzione | almeno 8 nodi su 11 e 3 flussi su 3; frecce rifiutate dopo la correzione al massimo il 20% |
| 2 Secondo progetto | almeno l'80% delle frecce provate o dichiarate; 8 nomi giusti su 10 letti a mano |
| 3 Livelli | nessun nodo fuori dal suo livello; ogni punto citato esiste |
| 4 Costo | un'area entro 0,30 USD e 5 aperture del sorgente; l'intero sistema entro 2 USD |
| 5 Stabilità | almeno l'80% dei nodi uguali fra due esecuzioni |
| 6 Registro | richiamo almeno 80% per caso, al massimo un riconoscimento sbagliato per caso |

Parametri da provare: tetto della scheda 12.000, 24.000 e 48.000 caratteri; `hub_share` 0,1, 0,2 e 0,3; modello economico e modello intermedio.

- [ ] **Passo 1:** scrivere il README con parametri e soglie, e i riferimenti attesi: per phazly gli 11 nodi con i loro file e i 3 flussi dell'esempio del 12 novembre 2026; per ogni caso l'elenco a mano dei servizi e progetti esterni letti dai manifest.
- [ ] **Passo 2:** scrivere `score.py` con un test su due mappe minime.
- [ ] **Passo 3:** misura 6 e dimensione della scheda sui tre casi, su Modal con gli archivi già usati dai benchmark dei flussi: nessun modello. Registrare i risultati nel README.
- [ ] **Passo 4:** commit.

### Task 12: run dell'agente e misure da 1 a 5

**File:** crea `benchmarks/system-map/modal_map.py`; modifica il README del benchmark, la riga di stato della spec, il frontmatter dell'agente.

`modal_map.py` segue `benchmarks/phazly-flow/phase3/modal_review.py`: un container per run, `claude -p` con il plugin di questa checkout, snapshot e regole preparati prima, sessione nuova, flusso degli eventi e costo salvati sul volume. Parametri: caso, area oppure intero sistema, modello, ripetizione.

- [ ] **Passo 1:** stimare il costo delle run (due casi, due modelli, due ripetizioni, area e intero sistema) e chiedere il via.
- [ ] **Passo 2:** lanciare, raccogliere, calcolare le misure da 1 a 5 con `score.py` e con la lettura manuale dei nomi.
- [ ] **Passo 3:** scrivere i risultati nel README, con ciò che non ha raggiunto la soglia e il motivo; fissare il modello dell'agente; aggiornare lo stato della spec.
- [ ] **Passo 4:** commit.

### Task 13: documenti allineati

**File:** modifica `docs/specs/2026-11-09-flow-model.md` (le righe Nodo, Flusso e Livello rimandano alla spec della mappa del sistema; i punti 1.5, 3.5, 5 e 7 sono marcati come sostituiti), `plugins/codebase-map/README.md` (una riga), `plugins/codebase-map/skills/map/references/standalone.md` se i comandi cambiano.

- [ ] **Passo 1:** aggiornare; `git diff --check`.
- [ ] **Passo 2:** commit.

## Fuori da questo piano

L'esploratore sulla mappa del sistema, con nodi espandibili e selettore dei livelli; la review dall'intento e le misure 7 e 8; `03-flows.md` generato dalla mappa del sistema; i loghi distribuiti nel viewer; l'installazione di Node da parte di Daodan; il passo dinamico.
