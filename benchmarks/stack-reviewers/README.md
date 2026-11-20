# Benchmark: revisori per framework e librerie

Prova la spec [revisori per framework e librerie](../../docs/specs/2026-11-19-revisori-per-framework-e-librerie.md): se un ruolo di framework o una foglia di libreria trova un difetto reale che i revisori di oggi mancano, in quale job una foglia lo trova e quanto costa. Pilota: `fastapi-auditor`, `nextjs-auditor`, `sqlalchemy-auditor`, `zod-auditor`. Il codice dei casi non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| prova | i quattro file di ruolo del pilota, in `roles/` di questa cartella finché non sono promossi. Li scrive chi non ha visto il caso, dalla sola riga di §5 della spec |
| forma | `branch` su `changeset`. Rigor e piano sono quelli che `review_roster.py compute` e `composition.py bind` calcolano sul caso, e si registrano |
| composizione | ogni braccio è una copia di `daodan/review/` con i file di `roles/` aggiunti e il solo `catalog.toml` cambiato: la costruisce `plugin_copy.py` da una variante in `catalogs/`, e `composition.py --plugin-root` ne lega i job. Catalogo di riferimento: quello del commit `407d5fc30196fed87089be6a858ad71b140f727e`. La meccanica di attivazione della spec non serve alla misura |
| esecuzione | un `senior-review:isolated-worker` per job, in sola lettura: nessun comando del progetto, né test né build né installazioni. Copia del caso fuori da questo repository, senza rete e senza la storia successiva al target; i revisori non vedono questo README né la fix |
| modello | `claude-sonnet-5-5`, uguale per ogni braccio |
| brief | lo scrive `brief.py` dal piano legato, con gli stessi campi per ogni braccio; cambia solo ciò che il braccio dichiara. Il prompt del worker rimanda al file del brief |
| mappa | due snapshot della stessa cartella, prima e dopo il commit target, scritti con `snapshot.py write --no-engine`; `plan.py` ne ricava il piano e la riga di `stack-dichiarato`, e dice se il registro riconosce framework e libreria nell'unità del caso. Se non li riconosce il caso lo registra: in produzione la voce non scatterebbe |
| run | due per braccio; token e durata dal blocco `<usage>` del worker |

## Bracci

| Braccio | Per | Job eseguiti | Cosa cambia |
|---|---|---|---|
| `baseline` | ogni caso | tutto il piano | niente: catalogo e brief al commit di riferimento |
| `stack-dichiarato` | ogni caso | tutto il piano | una riga nel brief con framework, librerie e versioni dell'unità toccata, da `technologies.json` |
| `ruolo` | un ruolo | il solo job del ruolo | il ruolo è nel catalogo e nella selezione |
| `foglia-dominio` | una foglia | il solo job ospite | la foglia è membro del job del piano con meno membri che contiene la sua foglia proprietaria (§1 della spec) |
| `foglia-stack` | una foglia | il solo job ospite | la foglia è membro del job di stack dell'unità: quello del ruolo di framework se l'unità lo dichiara, altrimenti quello di linguaggio |
| `foglia-propria` | una foglia | la sola foglia | job proprio; solo se `foglia-dominio` e `foglia-stack` mancano entrambi il difetto |

- I job non vedono i finding degli altri. Per questo un braccio della voce esegue solo il job che cambia: il resto del piano è quello di `baseline`.
- Il job ospite senza la foglia è il riferimento di costo. Se `baseline` non lo contiene, perché l'ospite di stack è un ruolo pilota, si esegue da solo sullo stesso caso.
- Un ospite di stack è un ruolo, non una composizione: la variante del catalogo dichiara la composizione di prova `stack-host`, con il solo ruolo in `<caso>-ospiti.toml` e con il ruolo e la foglia in `<caso>-foglia.toml`. Il job ha così lo stesso nome con e senza foglia.
- Con una selezione esplicita `bind` aggiunge un job per ogni obbligo nato dai simboli cambiati che i job scelti non coprono (in S1 `api-contract-auditor`). Nei bracci della voce non si esegue: in `baseline` è già membro di `code-auditor`.

## Prove senza modello

`python -B -m pytest -q benchmarks/stack-reviewers`

`test_catalogs.py` prova che i quattro ruoli candidati hanno gli SHA-256 registrati qui, che ogni variante è il catalogo di riferimento più ciò che dichiara, e che `bind` lega i job ospiti con e senza foglia: i membri differiscono per la sola foglia.

## Run con il modello

1. In una cartella fuori dal repository, `maps.py <clone> <target> <cartella> <percorsi>` scrive l'albero al commit target senza storia, i due snapshot e `target.diff`; `plan.py` ne ricava il piano e `impact.json`. S1 è stato preparato a mano con gli stessi passi, prima dello script.
2. `plugin_copy.py <variante> <cartella>` per i bracci della voce; una copia di `daodan/review/` per `baseline`.
3. `composition.py --plugin-root <copia> bind` sul `roster.json` di `plan.py`: selezione `"automatic"` per `baseline`, i job ospiti per i bracci della voce.
4. `brief.py` per ogni job da eseguire; un worker nuovo per brief.
5. Registrare per ogni run finding con `file:line`, token, strumenti usati e durata.

## Casi

Un caso è un commit pubblico che ha introdotto un difetto poi corretto. Regola di scelta, applicata prima di scrivere i file di ruolo:

1. repository pubblico, con target e fix fissati per SHA;
2. la fix nomina il difetto, e il difetto è di una famiglia della voce nella matrice di §5 della spec;
3. il target è il commit che ha introdotto il difetto, trovato con `git blame` sulle righe che la fix cambia. Se il difetto nasce in più commit, il caso si scarta;
4. il target tocca fra 5 e 40 file di produzione. Sotto, un revisore legge tutto e l'aggregazione non pesa; sopra, una run costa più di quelle di [`jupiter-alias`](../jupiter-alias/README.md), che ha 28 file;
5. l'unità del target dichiara il framework o la libreria.

Controllo sano di ogni caso: il commit della fix, rivisto come changeset. La voce scatta sugli stessi file e il difetto non c'è più.

| Caso | Voce | Famiglia del difetto |
|---|---|---|
| F1 | `fastapi-auditor` | I/O bloccante dentro `async def`; sessione creata fuori da `Depends` o usata chiusa in `BackgroundTasks`; modello interno restituito senza `response_model` |
| N1 | `nextjs-auditor` | confine Server/Client; funzione `"use server"` senza verifica di accesso o schema d'ingresso; cache o revalidazione incoerente su dati per utente |
| S1 | `sqlalchemy-auditor` | sessione condivisa fra task o richieste; caricamento lazy su `AsyncSession` o dopo la chiusura; oggetto scaduto letto fuori transazione; `commit` parziale in un ciclo |
| Z1 | `zod-auditor` | `.passthrough()`, `z.any()` o `z.unknown()` su un payload esterno fino allo store; schema di scrittura allentato da `.partial()` o `.merge()`; `.parse()` non intercettato dove serve un errore strutturato |

S1, N1 e Z1 sono scelti; S1 si esegue per primo. F1 è esplorativo: non decide la promozione di `fastapi-auditor`, che aspetta un caso conforme alla regola 2. Il piano di ogni caso è calcolato dal solo diff, senza mappa: si ricalcola con la mappa prima delle run.

### F1, esplorativo: chiamata Stripe sincrona dentro `async def`

| | |
|---|---|
| stato | esplorativo. La regola 2 chiede che la fix nomini il difetto, e qui non lo fa: il commit dice «Let's get more throughput!», la sua PR [4125](https://github.com/polarsource/polar/pull/4125), «Stripe optimizations around Checkout», non ha descrizione né commenti, e nemmeno la [4142](https://github.com/polarsource/polar/pull/4142) |
| repository | [polarsource/polar](https://github.com/polarsource/polar), unità `server/`; `server/pyproject.toml` dichiara `fastapi = "^0.114.2"` |
| target | `071de575d44a81c378099bf2e2f1707d4d2580ff`, «server/checkout: implement tax calculation», 2024-10-02: 7 file di produzione e 3 di test, 811 righe cambiate |
| fix | `54da720710e5b30bd9d176222bd3d67ecaf66711`, «server/stripe: use async calls for checkout utilities», 2024-10-09 |
| difetto atteso | `server/polar/checkout/tax.py:295`: `async def calculate_tax` chiama `stripe_service.create_tax_calculation`, che il target aggiunge come metodo sincrono sopra `stripe_lib.tax.Calculation.create` (`server/polar/integrations/stripe/service.py:696`). La richiesta HTTP a Stripe ferma l'event loop. Lo stesso per `create_out_of_band_subscription` e `create_out_of_band_invoice` in `handle_stripe_success` (`server/polar/checkout/service.py:519`, `:534`) |
| trovato | un finding su una di queste righe afferma che la chiamata a Stripe è sincrona dentro una funzione `async` e blocca l'event loop |
| piano | `deep`, 12 job: `code-auditor` 27 membri, `security-auditor` 10, `cleanup-auditor` 6, `operability-auditor` 6, `data-integrity-auditor` 5 e sette job da un membro, fra cui `python-auditor` e `stripe-auditor` |
| testo della voce | `roles/fastapi-auditor.md`, lo stesso file e lo stesso SHA-256 registrati in S1 |
| limite | al target 45 dei 53 metodi del servizio Stripe sono sincroni: il commit segue l'uso del codice, corretto per intero il 2024-10-10 (`8547d3bd6`, 23 file). La fix non lo chiama difetto: «Let's get more throughput!». `algorithmic-cost-auditor`, membro di `code-auditor`, nomina già l'I/O sincrono sull'event loop |

### S1: relazione letta senza essere caricata, su `AsyncSession`

| | |
|---|---|
| repository | polarsource/polar, unità `server/`; `server/pyproject.toml` dichiara `sqlalchemy[asyncio]>=2.0.34` e `fastapi>=0.115.2` |
| target | `fda4979312ab21926b901574f1288e212c76138e`, «feat: move to organization reviews (#6317)», 2025-07-29: 11 file di produzione, di cui una migrazione, e 3 di test, 860 righe cambiate |
| fix | `949877dec1f235d779d2c965399159311e35251d`, «fix: lazy loading in account tasks (#6319)», 2025-07-30, figlio diretto del target |
| difetto atteso | `server/polar/account/tasks.py:42`: il task `account.under_review` carica le organizzazioni con `get_all_by_account` (`server/polar/organization/repository.py:64`), senza la relazione `account`, e le passa a `create_account_review_thread`, che la legge (`server/polar/integrations/plain/service.py:126`). La relazione è `lazy="raise"` (`server/polar/models/organization.py:132`): la lettura solleva e il thread di review non nasce |
| trovato | un finding su `tasks.py:42`–`44` o su `plain/service.py:126` afferma che `organization.account` è letta senza essere caricata |
| piano, con la mappa | `deep`, 13 job: `code-auditor` 27 membri, `security-auditor` 10, `performance-auditor` 7, `cleanup-auditor` 6, `operability-auditor` 6, `data-integrity-auditor` 5 e sette job da un membro, fra cui `python-auditor` e `stripe-auditor`. Rispetto al piano dal solo diff entra `stripe-auditor`: l'unità dichiara Stripe, e due file cambiati, `server/polar/account/service.py` e `server/polar/transaction/service/payout.py`, importano `stripe`; il cambiamento aggiorna lo stato dell'organizzazione dalle capacità dell'account Stripe. Non è un'attivazione a vuoto: fino al 2026-11-20 qui era scritto il contrario, senza aver controllato gli import |
| mappa | base `b6f80c9234944934b5fd7283d2ba8129cd9e6bf5` e target, 961 e 962 file Python di `server/`. Il registro riconosce `fastapi` come framework e `sqlalchemy` nell'unità `server`. Lacune: il motore di risoluzione delle chiamate non è eseguito, e `edit-impact` riporta 25 dei 54 simboli cambiati |
| copertura del difetto | verificata prima delle run, perché il motore non è eseguito. I due simboli del difetto che il commit cambia, `account_under_review` e `PlainService.create_account_review_thread`, sono nel diff e fra i 25 di `edit-impact`. `get_all_by_account` e la relazione `account` non cambiano, ma stanno in file del changeset, dentro il perimetro di lettura |
| riga di `stack-dichiarato` | «stack di server: framework fastapi; librerie alembic >=1.9.2, boto3 >=1.38.30, fastapi >=0.115.2, httpx >=0.23.0, jinja >=3.1.2, polarsh ==0.16.13, posthog >=3.6.0, pydantic >=2.10,<2.11, pytest <9, redis >=5.0.4, ruff >=0.6.9, sqlalchemy >=2.0.34, stripe >=10.12.0,<12, typer >=0.12.5», la prima delle due righe che stampa `plan.py`: i pacchetti dichiarati che il registro riconosce. La seconda è per `server/polar/web_backoffice`, che il diff tocca e che non dichiara Python |
| ospiti | di dominio `data-integrity-auditor`, il job del piano con meno membri che contiene `transaction-integrity-auditor`; di stack `fastapi-auditor`, ruolo pilota fuori da `baseline`, quindi eseguito anche da solo come riferimento di costo |
| varianti | `catalogs/S1-ospiti.toml` e `catalogs/S1-foglia.toml`. Bracci: `foglia-dominio` lega `data-integrity-auditor` da `S1-foglia`; `foglia-stack` lega `stack-host` da `S1-foglia`, con riferimento `stack-host` da `S1-ospiti`; `foglia-propria` lega `sqlalchemy-auditor` da `S1-foglia` |
| testo della voce | `roles/sqlalchemy-auditor.md`, 35 righe, 3783 byte, SHA-256 `769854e4c870bc29cf06ac278244374e9fd19f1b4fc24cbd01e757bb7217d617`: lo stesso in ogni braccio di S1, registrato prima della prima run |
| testo dell'ospite di stack | `roles/fastapi-auditor.md`, 36 righe, 2872 byte, SHA-256 `2b72e8c0f76a5cdb7ca6f3c7057930fb71fd46824f954911a6c4524157eee260`. Le versioni che nomina sono verificate: 0.89.0 e 0.74.0 sulle note di rilascio, 0.106, 0.118 e 0.121 sulla documentazione delle dipendenze con `yield`, l'ordine fra codice di uscita e task in background sul sorgente `fastapi/routing.py` alla 0.118.0 |
| nota su `sqlalchemy-auditor.md` | registrata prima delle run e fuori dai brief: la riga 24 dice che leggere un attributo non caricato emette SQL, ma con `lazy="raise"` la lettura fallisce prima. La riga 19 chiede comunque al revisore il `lazy=` della relazione. Il testo non si corregge prima di S1 |
| limite | con `lazy="raise"` l'errore non è `MissingGreenlet`: la voce deve leggere come è dichiarata la relazione. Il difetto sta in un task del worker, non in un endpoint. Al target i due metodi che accodano il task (`server/polar/account/service.py:119`, `:256`) non hanno più chiamanti che una ricerca nell'albero trovi: il difetto scatta per i job già in coda |

Scartato per la regola 4: `cc00c2036a29e8869bd4159d000f0c89cfae9313`, che esegue le query Postgres e Tinybird con `asyncio.gather` sulla sessione della richiesta (fix `8ecbaa42f`). Tocca 3 file di produzione.

### N1: tag di cache passato come chiave, la revalidazione non invalida nulla

| | |
|---|---|
| repository | [calcom/cal.com](https://github.com/calcom/cal.com), unità `apps/web`; `apps/web/package.json` dichiara `"next": "^15.3.2"` |
| target | `e115095198bc9f0b95ccd901ab8597eb771da9ff`, «perf: migrate listHandler to AttributeRepository + cache attributes fetching in RSCs (#21552)», 2025-05-29: 7 file di produzione, 80 righe cambiate |
| fix | `b91607b5b4ab27eaef2321b3857f9ba93d809b63`, «fix: missing places for revalidations (#21632)», 2025-05-29. La PR dice: «Fixed attribute list revalidation […] This prevents stale data after creating or updating attributes» |
| difetto atteso | `apps/web/app/(use-page-wrapper)/settings/organizations/members/page.tsx:23`: `unstable_cache` riceve `["viewer.attributes.list"]` come chiave e non fra i `tags`. L'azione `revalidateAttributesList` (`actions.ts:6`, nella stessa cartella) chiama `revalidateTag("viewer.attributes.list")`, che così non invalida nulla: dopo una modifica agli attributi la pagina dei membri resta vecchia fino a un'ora |
| trovato | un finding su `page.tsx:23`–`24` o su `actions.ts:6` afferma che il tag non è fra i `tags` della cache e che la revalidazione non ha effetto |
| piano, con la mappa | `deep`, 14 job: `code-auditor` 27 membri, `security-auditor` 10, `performance-auditor` 7, `cleanup-auditor` 6, `data-integrity-auditor` 5, `accessibility-auditor` 2 e otto job da un membro, fra cui `typescript-auditor`, `react-auditor` e `stripe-auditor`. Rispetto al piano dal solo diff entra `stripe-auditor`: `apps/web` dichiara `stripe ^9.16.0`, e nessun file cambiato né vicino a un salto lo importa |
| mappa | i file della radice e `apps/web`, `packages/features`, `packages/lib`, `packages/trpc`, `packages/prisma`: 3.313 file alla base, 9 unità. Il registro riconosce `nextjs` e `react` come framework di `apps/web`. Motore non eseguito; `edit-impact` riporta 7 simboli cambiati. Il collegamento simbolico `packages/prisma/.env`, che punta a un file assente, non è nella copia del caso |
| copertura del difetto | `page.tsx` e `actions.ts` sono nel diff; `Page` e `revalidateAttributesList` fra i simboli di `edit-impact` |
| riga di `stack-dichiarato` | le righe che `plan.py` stampa per le sei unità che il diff tocca; quella di `apps/web`: «stack di apps/web: framework nextjs, react; librerie babel ^7.19.6, calcom *, calcom ?, google.calendar ^9.7.9, playwright ^1.45.3, sentry ^9.15.0, testinglibrary ^13.3.0, upstash ^1.21.0, vercel.edge ^0.1.1, vercel.edge ^0.2.1, vercel.functions ^0.6.3, gcp ^9.15.0, nextjs ^15.3.2, posthog ^1.164.1, posthog ^4.2.0, react ^18.2.0, intercom 1.5.1, stripe ^9.16.0, tailwind ^3.3.3, typescript ^5.8.3, zod ^3.22.4» |
| varianti | `catalogs/N1-ruolo.toml`; il braccio `ruolo` lega `nextjs-auditor` da quella |
| testo della voce | `roles/nextjs-auditor.md`, 36 righe, 2873 byte, SHA-256 `3752e839330c04ca02bc696edf5dec995f35ea262e7661174c0f25c3fa243513`, registrato prima della prima run. Verificato sulla documentazione di Next.js: `proxy.*` dalla 16, `fetch` non più in cache per default dalla 15, la chiave di `unstable_cache` e quella di `"use cache"` |
| limite | il changeset è piccolo, 80 righe: l'aggregazione pesa meno che negli altri casi. Il dato è per organizzazione, non per utente. La fix aggiunge anche due chiamate in file che il target non tocca: non fanno parte del difetto atteso |

Di riserva per N1: formbricks `30fdcff7375035239484ece48e9ea10df9eb7d93`, un'azione server che cancella le risposte di un sondaggio autorizzando su identificativi forniti dal client (fix `c7faa29437ea706eae411958b260bb5ad5c60e4f`, che corregge cinque azioni nate in commit diversi).

### Z1: lo schema di richiesta accetta ciò che lo schema di scrittura rifiuta, e l'errore esce come 500

| | |
|---|---|
| repository | [formbricks/formbricks](https://github.com/formbricks/formbricks), unità `apps/web`; `apps/web/package.json` dichiara `"zod": "4.3.6"` e `"next": "16.2.6"` |
| target | `e689d3890e9be90e29413d7935b2191b86a74b6b`, «chore: v3 post survey (#8073)», 2026-05-28: 16 file di produzione, 11 di test e un contratto OpenAPI, 5997 righe cambiate |
| fix | `243f4bfddfb395ae34221c73a3d38e4d0b551752`, «fix(api-v3): return 422 instead of 500 for post-schema survey validation failures (#8991)», 2026-09-01 |
| difetto atteso | `apps/web/app/api/v3/surveys/route.ts:136`–`166`: `POST /api/v3/surveys` valida il corpo con `ZV3CreateSurveyBody` (`schemas.ts:1018`); poi `createSurvey` (`create.ts:90`) lo rivalida con `ZSurveyCreateInput`, che ha raffinamenti in più (`apps/web/lib/survey/service.ts:654`), e solleva `ValidationError` (`apps/web/lib/utils/validate.ts:43`). Il `catch` della route non ha un ramo per quell'errore: un documento che il primo schema accetta e il secondo rifiuta esce come 500 |
| trovato | un finding su `route.ts` o su `create.ts:90` afferma che un rifiuto di validazione di `createSurvey` non diventa un errore strutturato, o che lo schema di richiesta accetta ciò che lo schema di scrittura rifiuta |
| piano, con la mappa | `deep`, 15 job: `code-auditor` 27 membri, `security-auditor` 10, `performance-auditor` 7, `cleanup-auditor` 6, `operability-auditor` 6, `data-integrity-auditor` 5 e nove job da un membro, fra cui `typescript-auditor`, `react-auditor`, `stripe-auditor` e `api-contract-auditor`. Rispetto al piano dal solo diff entrano `react-auditor` e `stripe-auditor`: `apps/web` dichiara `react` e `stripe 20.4.1`, e nessun file cambiato né vicino a un salto importa Stripe |
| mappa | i file della radice e `apps/web`, `packages/types`, `packages/database`, `docs/api-v3-reference`: 2.380 file alla base. Il registro riconosce `nextjs` e `react` come framework di `apps/web` e `zod 4.3.6` in `apps/web` e `packages/types`. Motore non eseguito; `edit-impact` riporta 25 dei 123 simboli cambiati. Il collegamento simbolico `apps/web/.env` non è nella copia del caso |
| copertura del difetto | i cinque file del difetto sono nel diff. `createV3Survey` ed `executeV3SurveyCreate` sono fra i simboli di `edit-impact`; `createSurvey` e `validateInputs` cambiano ma restano fuori dai 25 |
| riga di `stack-dichiarato` | le righe che `plan.py` stampa per le tre unità che il diff tocca; quella di `apps/web`: «stack di apps/web: framework nextjs, react; librerie opentelemetry 0.217.0, opentelemetry 1.40.0, radixui 2.1.8, radixui 1.2.4, sentry 10.43.0, testinglibrary 6.9.1, testinglibrary 16.3.2, gcp 171.4.0, lexicaleditor 0.41.0, lucideicons 0.577.0, nextjs 16.2.6, posthog 1.369.5, posthog 5.28.11, react 19.2.6, stripe 20.4.1, tailwind 3.4.19, vite 7.3.3, vitest 4.1.6, zod 4.3.6» |
| ospiti | di dominio `security-auditor`, il job del piano con meno membri che contiene `input-validation-auditor`; di stack `nextjs-auditor`, ruolo pilota fuori da `baseline`, quindi eseguito anche da solo come riferimento di costo |
| varianti | `catalogs/Z1-ospiti.toml` e `catalogs/Z1-foglia.toml`. `foglia-dominio` lega `security-auditor` da `Z1-foglia`, 11 membri; `foglia-stack` lega `stack-host` da `Z1-foglia`, con riferimento `stack-host` da `Z1-ospiti` |
| testo della voce | `roles/zod-auditor.md`, 34 righe, 2865 byte, SHA-256 `b953b67230feb3bf908400dcd57cd986085aa60ac4a2f3d403055eee455681b1`, registrato prima della prima run. Verificato su documentazione e sorgente di zod: i sottopercorsi `zod/v4` e `zod/v3`, `.loose()` nella 4, i default dentro i campi opzionali nella 4, la politica delle chiavi ignote ereditata da `.merge()` nella 3. Non fissato a una versione minore, e il testo lo dice: cosa succede a un raffinamento quando si deriva uno schema nella 4 |
| testo dell'ospite di stack | `roles/nextjs-auditor.md`, lo stesso file e lo stesso SHA-256 registrati in N1 |
| limite | la fix aggiunge soltanto righe: il target è il commit che crea `route.ts` e `create.ts`. Chi solleva è un wrapper (`safeParse`, poi `throw`), non un `.parse()` letterale: il difetto sta fra due famiglie della riga di §5, schema allentato ed errore non intercettato. È il changeset più grande dei quattro |

Scartati per Z1 dall'agente di ricerca, non riverificati: formbricks `47583b5a3` (`.partial()` su uno schema di scrittura, il più vicino alla famiglia, ma il commit che lo introduce tocca 120 file) e altre fix di formbricks e cal.com, per le regole 3, 4 o 5.

## Criterio, dichiarato prima delle run

- **Trovato:** un finding con `file:line` sul punto del difetto afferma il meccanismo che la fix corregge. Nessuna severità minima. Conta il job, non il membro che firma il finding. Una pista scritta fra le lacune, senza finding, si registra come `nota` e non conta come trovato: precisazione scritta dopo la prima run di S1, che non cambia la regola.
- **Esito di un braccio:** `trova` con 2 run su 2, `manca` con 0 su 2. Con 1 su 2 decide una terza run. Le run sono due perché la promozione poggia sul negativo dei controlli: una sola run in cui `baseline` manca il difetto darebbe alla voce un vantaggio occasionale.
- **Falso positivo:** sul controllo sano, un finding della voce che ridichiara il difetto corretto, o che le lenti 1 e 2 di `panel-and-critic-prompts.md` scartano entrambe.
- **Costo,** sulle medie delle run. Foglia: i token del job ospite con la foglia restano sotto il 115% dello stesso job senza. Ruolo: i token del suo job non superano quelli del job di linguaggio sullo stesso caso. Nei controlli il costo di un job attivato a vuoto, come `stripe-auditor` in S1, si riporta in una colonna a parte.
- **Una voce entra nel catalogo** se un suo braccio `trova`, `baseline` e `stack-dichiarato` `mancano`, non ha falsi positivi e resta nel costo.
- **Esiti che cambiano la spec:**
  - `stack-dichiarato` `trova`: entra la riga nel brief, non la voce;
  - l'ospite della foglia diventa quello che `trova` e resta nel costo; a parità resta il dominio;
  - una foglia che `trova` solo come `foglia-propria` non entra come foglia.
- **Secondo caso:** una voce il cui difetto è trovato da `baseline` può avere un altro caso. Se `baseline` trova anche quello, la voce non entra.
- **Testo corretto dopo le run:** un ruolo cambiato dopo aver visto le run del suo caso si rimisura su un caso non ancora visto.

## Ordine delle run di un caso

I bracci sono indipendenti: l'ordine serve solo a non spendere dove l'esito è già deciso.

1. I bracci della voce: `ruolo`, oppure `foglia-dominio` e `foglia-stack`, poi `foglia-propria` se serve. Se nessuno `trova`, il caso si chiude: la voce non entra con questo testo.
2. `baseline`. Se `trova`, il caso si chiude: lì la voce non serve.
3. `stack-dichiarato`.
4. Il controllo sano, una run per ogni braccio della voce che `trova`.

Dentro una run di `baseline` o di `stack-dichiarato` i job si lanciano a tappe, dai più probabili: la run `trova` al primo job che segnala il difetto e gli altri non si eseguono. Per dire che una run `manca` servono tutti i job del piano. In S1 la prima tappa è `code-auditor` e `python-auditor`. Regola scritta dopo le run della voce e prima di queste.

Stima, da ricalibrare dopo il primo caso: su `jupiter-alias` (28 file, Opus 5.5) un ruolo da solo costa 130–225 mila token e `code-auditor` 300–325 mila. Il passo 1 esegue due run di uno o due job. I passi 2 e 3 eseguono tutto il piano due volte ciascuno e sono la spesa maggiore. Con il piano da 12 job di F1 (13 per S1, N1 e Z1), le run di job dei soli controlli per caso sono:

- 0 se nessun braccio della voce `trova`;
- 24 (26) se `baseline` `trova` in entrambe le run: il caso si chiude prima di `stack-dichiarato`;
- 48 (52) se servono entrambi i controlli e le loro run concordano;
- fino a 72 (78) se entrambi chiedono la terza run.

Per S1 il conteggio viene dalla mappa; per gli altri dal diff, da aggiornare dopo la mappa.

## Non misurato

- La forma `light`, dove la voce è un membro dell'unico job.
- La riduzione dei falsi positivi di `baseline`, che la spec nomina: su un commit reale i finding di `baseline` non hanno un oracolo.
- La precisione di attivazione: la coprono i test del punto 1 di «Prova» della spec.
- Il controllo di `nextjs-auditor` sul middleware: N1 misura l'invalidazione della cache.
- Più modelli, e più di un caso per voce quando il primo decide.
- L'ospite di stack dopo una bocciatura: se è un ruolo pilota che non entra, `foglia-stack` si rimisura con il job di linguaggio.

## Risultati

### S1, run del 2026-11-19

**Esito: S1 si chiude senza promuovere `sqlalchemy-auditor`.** `foglia-dominio` `trova`, 2 run su 2, ma anche `baseline` `trova`, 2 run su 2: lì la voce non serve. `stack-dichiarato` e il controllo sano non si eseguono. La foglia può avere un secondo caso; se `baseline` trova anche quello, non entra. Spesa del caso: 7 run di job, 1.366.719 token. La seconda run di `foglia-stack` non è eseguita: con il dominio che trova e resta nel costo non cambia la scelta dell'ospite. `claude-sonnet-5-5`; ruoli, catalogo e brief come registrati sopra; mappa senza motore. I finding diversi dal difetto atteso non sono verificati dalle lenti.

| Braccio | Job | Membri | Run | Difetto | Altri finding | Token | Strumenti | Durata |
|---|---|---|---|---|---|---|---|---|
| `baseline`, job ospite di dominio | `data-integrity-auditor` | 5 | 1 | nota | 5 | 218.571 | 67 | 682 s |
| `baseline`, prima tappa | `python-auditor` | 1 | 1 | sì | 6 | 170.379 | 48 | 598 s |
| `baseline`, prima tappa | `code-auditor` | 27 | 1 | sì | 12 | 283.527 | 87 | 1.150 s |
| `baseline`, prima tappa | `python-auditor` | 1 | 2 | sì | 7 | 169.175 | 49 | 883 s |
| `foglia-dominio` | `data-integrity-auditor` | 6 | 1 | sì | 7 | 185.939 | 65 | 1.075 s |
| `foglia-dominio` | `data-integrity-auditor` | 6 | 2 | sì | 5 | 165.583 | 51 | 927 s |
| `foglia-stack` | `stack-host` | 2 | 1 | sì | 0 | 173.547 | 57 | 675 s |

- **Senza foglia:** il job vede il difetto e non lo segnala. Nelle lacune scrive che `account/tasks.py:41-44` carica le organizzazioni senza `joinedload(Organization.account)`, che `plain/service.py:126` legge la relazione `lazy='raise'` e che `account_under_review` probabilmente solleva; lo chiama pista per altri revisori, fuori dal suo perimetro. Nessuno dei cinque membri è titolare del meccanismo.
- **`python-auditor` in `baseline`:** finding su `server/polar/account/tasks.py:44` in entrambe le run, Low con confidenza 65 e Medium con confidenza 60, con lo stesso meccanismo e la stessa eccezione (`InvalidRequestError`) dei bracci della voce. Il ruolo di linguaggio che il roster attiva già oggi trova il difetto senza la foglia.
- **`code-auditor` in `baseline`:** finding F-07 sulla stessa riga, Low, confidenza 60, firmato da `local-correctness-auditor`; tutti i 27 membri consegnati con copertura completa. Il job composto da 27 membri trova il difetto che il job da 5, che ne è un sottoinsieme, registra solo come nota: a segnalarlo è un membro fuori da `data-integrity-auditor`.
- **Con la foglia:** finding su `server/polar/account/tasks.py:44` in entrambe le run, firmato da `sqlalchemy-auditor`: Low con confidenza 60 nella prima, Medium con confidenza 50 nella seconda. La prima nomina `InvalidRequestError` e non `MissingGreenlet`: l'imprecisione della riga 24 del ruolo non l'ha sviata. È Low perché il worker non trova più chi accoda il task.
- **Nell'ospite di stack:** un solo finding, lo stesso punto (`tasks.py:44`), firmato da `sqlalchemy-auditor`, Low, confidenza 80. Cinque piste per altri revisori fra le lacune. Il job da due membri spende quasi quanto quello da sei: il costo lo fa la lettura del changeset, non il numero di membri.
- **Costo:** con la foglia il job di dominio spende in media 175.761 token su due run, l'80% dell'unica run senza foglia (218.571). Il confronto vale quando il job senza foglia avrà la seconda run. Per l'ospite di stack manca il riferimento senza foglia.
- Le due run concordano sul finding più grave, High su `server/polar/organization/service.py:391`.

### N1, run del 2026-11-20

**Esito: N1 si chiude senza promuovere `nextjs-auditor`.** `ruolo` `trova`, 2 run su 2, ma anche `baseline` `trova`, 2 run su 2: nella prima con `typescript-auditor` e `code-auditor`, nella seconda con `code-auditor`, mentre `typescript-auditor` registra il difetto solo come nota. `stack-dichiarato` e il controllo sano non si eseguono. Spesa del caso: 6 run di job, 686.508 token. `claude-sonnet-5-5`; ruolo, catalogo e brief come registrati sopra; mappa senza motore.

| Braccio | Job | Membri | Run | Difetto | Altri finding | Token | Strumenti | Durata |
|---|---|---|---|---|---|---|---|---|
| `ruolo` | `nextjs-auditor` | 1 | 1 | sì | 2 | 98.728 | 42 | 452 s |
| `ruolo` | `nextjs-auditor` | 1 | 2 | sì | 1 | 102.373 | 43 | 640 s |
| `baseline`, prima tappa | `typescript-auditor` | 1 | 1 | sì | 0 | 66.195 | 30 | 477 s |
| `baseline`, prima tappa | `code-auditor` | 27 | 1 | sì | 1 | 136.513 | 62 | 596 s |
| `baseline`, prima tappa | `typescript-auditor` | 1 | 2 | nota | 1 | 96.417 | 48 | 327 s |
| `baseline`, prima tappa | `code-auditor` | 27 | 2 | sì | 1 | 186.282 | 75 | 532 s |

- **Run 1:** finding F1 su `page.tsx:23`, Medium, confidenza 85: le chiavi di `unstable_cache` non sono tag, quindi `revalidateTag("viewer.attributes.list")` non invalida nulla. F2 coglie anche la seconda parte della fix: la creazione di un attributo non revalida. F3, Low, è il controllo sul middleware: l'azione non verifica l'accesso e il `matcher` non copre `/settings/organizations/*`; il finding stesso dice che oggi non ha effetto.
- **Run 2:** NJ-1 su `page.tsx:24`, Medium, confidenza 85, con la stessa premessa; nomina anche la creazione non revalidata. NJ-2, Low, è di nuovo l'azione senza verifica dell'accesso.
- **`typescript-auditor` in `baseline`:** TS-1 su `page.tsx:23`, Medium, confidenza 80, con la stessa premessa: i `keyParts` non sono tag. Il ruolo di linguaggio trova il difetto senza `nextjs-auditor`, come `python-auditor` in S1. Fra le piste per altri revisori nomina anche la creazione non revalidata.
- **`typescript-auditor`, seconda run:** il difetto compare come nota per altri revisori su `page.tsx:23`, con la stessa premessa, ma non come finding. Il solo finding, Low, riguarda i campi `Date` che un hit della cache restituisce come stringhe. Lo stesso ruolo, sullo stesso brief, una volta se lo intesta e una volta lo passa ad altri.
- **`code-auditor` in `baseline`:** F1 su `page.tsx:23`, Medium, confidenza 80, e F2 sulla creazione non revalidata, entrambi dal membro `cache-consistency-auditor` secondo il riassunto del worker; 27 membri su 27 con copertura completa. Anche il generalista trova il difetto e la seconda parte della fix. Nella seconda run gli stessi due finding, F1 su `page.tsx:24`; `cache-consistency-auditor` dichiara copertura incompleta perché la topologia della cache del deployment non è nell'albero.
- **Deviazione dal brief, run 2 di `ruolo`:** il worker ha lanciato `python -` con input vuoto dalla cartella dell'albero; il comando è rimasto appeso ed è stato fermato dal coordinatore. Non ha eseguito codice del progetto: l'albero di N1 non contiene file Python. Il brief vieta interpreti sul codice del progetto, non ogni interprete.

### Z1, run del 2026-11-20

**Esito: Z1 si chiude senza promuovere `zod-auditor`.** `baseline` `trova`, 2 run su 2, con `code-auditor`; `typescript-auditor` registra il difetto solo come nota. La foglia resta a 1 su 2 nell'ospite di dominio e a 1 su 1 in quello di stack: la terza e la seconda run non si eseguono, perché non cambiano l'esito. `stack-dichiarato` e il controllo sano non si eseguono. Spesa del caso: 6 run di job, 1.856.907 token. `claude-sonnet-5-5`; ruoli, catalogo e brief come registrati sopra; mappa senza motore.

| Braccio | Job | Membri | Run | Difetto | Altri finding | Token | Strumenti | Durata |
|---|---|---|---|---|---|---|---|---|
| `foglia-dominio` | `security-auditor` | 11 | 1 | sì | 4 | 306.876 | 110 | 1.192 s |
| `foglia-dominio` | `security-auditor` | 11 | 2 | no | 3 | 271.059 | 87 | 1.430 s |
| `foglia-stack` | `stack-host` | 2 | 1 | sì | 3 | 290.433 | 85 | 1.344 s |
| `baseline`, prima tappa | `typescript-auditor` | 1 | 1 | nota | 1 | 230.040 | 67 | 1.000 s |
| `baseline`, prima tappa | `code-auditor` | 27 | 1 | sì | 12 | 357.572 | 114 | 1.069 s |
| `baseline`, prima tappa | `code-auditor` | 27 | 2 | sì | 9 | 400.927 | 78 | 1.534 s |

- **Run 1 di `foglia-dominio`:** F5 su `apps/web/app/api/v3/surveys/route.ts:164`, Medium, confidenza 60, firmato da `zod-auditor` con `input-validation-auditor`: le regole che stanno solo in `ZSurveyCreateInput` non entrano nello schema v3 né in `/validate`, e il `ValidationError` di `createSurvey` esce come 500 senza ramo nella route. Aggiunge che le righe `Language` sono già scritte quando l'errore arriva. Due membri su undici dichiarano copertura incompleta: `browser-security-auditor` e `capacity-quota-auditor`, per configurazioni assenti dall'albero.
- **Run 2 di `foglia-dominio`:** nessun finding sul punto del difetto. Il meccanismo compare nella prova di F2, ancorato a `apps/web/app/api/v3/surveys/languages.ts:57` e intitolato a chi può creare le lingue: un URL `ftp://` in una CTA passa lo schema v3, fallisce `safeUrlRefinement`, e il `ValidationError` non mappato in `route.ts` dà 500. La correzione proposta include «map ValidationError from createSurvey to 400». Per il criterio di Z1, che chiede un finding su `route.ts` o su `create.ts:90`, non è trovato. Il braccio è a 1 su 2.
- **Run 1 di `foglia-stack`:** F-01 su `route.ts:136`, Medium, confidenza 72, firmato da `zod-auditor` secondo il worker: un documento che `/validate` dichiara valido riceve 500, perché `createSurvey` solleva `ValidationError` e niente lo trasforma in 400. Come in S1, il job da 2 membri costa quasi quanto quello da 11.
- **`typescript-auditor` in `baseline`, run 1:** il difetto compare fra le piste per altri revisori, indirizzato a `local-correctness-auditor`: la route non intercetta `ValidationError`, e le regole di `ZSurveyCreateInput` che lo schema v3 non riprende escono come 500. Il solo finding riguarda `ZSurveyMetadata.catchall(z.unknown())`.
- **`code-auditor` in `baseline`, run 1:** F1 su `route.ts:136`, Medium, confidenza 85: lo schema v3 non applica le regole di `ZSurveyCreateInput` e la route non ha un ramo per `ValidationError`, quindi 500 dopo che le lingue sono già scritte. 27 membri consegnati, sette con copertura incompleta per configurazioni o politiche assenti dall'albero.
- **`code-auditor` in `baseline`, run 2:** F2 su `route.ts:164`, Medium, confidenza 85, con la stessa premessa; 27 membri su 27 con copertura completa.

### Esito del pilota

Nessuna delle quattro voci entra nel catalogo. Esito: nessun valore incrementale dimostrato sui tre casi; non è un valore nullo, dati i limiti sotto. In ogni caso con difetto `baseline` trova 2 run su 2, e una voce entra solo se `baseline` lo manca. `fastapi-auditor` non ha avuto un caso che decidesse: F1 è esplorativo e non è stato eseguito.

| Caso | Voce | La voce trova | Ruolo di linguaggio in `baseline` | `code-auditor` in `baseline` |
|---|---|---|---|---|
| S1 | `sqlalchemy-auditor` | 2 su 2 in un ospite, 1 su 1 nell'altro | `python-auditor` 2 su 2 | 1 su 1 |
| N1 | `nextjs-auditor` | 2 su 2 | `typescript-auditor` 1 su 2, una nota | 2 su 2 |
| Z1 | `zod-auditor` | 1 su 2 in un ospite, 1 su 1 nell'altro | `typescript-auditor` una nota | 2 su 2 |

- **Il generalista trova i tre difetti.** `code-auditor` li segnala in tutte e cinque le sue run. Il ruolo di linguaggio li vede in tutte e cinque le sue run, ma due volte li registra come pista per altri revisori invece che come finding.
- **Il confine fra pista e finding è instabile.** Lo stesso ruolo, sullo stesso brief, si intesta il difetto in una run e lo passa ad altri nell'altra (`typescript-auditor` in N1). In S1 `data-integrity-auditor` lo registra come nota senza la foglia e come finding con la foglia: la foglia cambia chi se lo intesta dentro quel job, non se il piano lo trova.
- **Costo della foglia:** l'unico confronto con e senza foglia sullo stesso job, in S1, dà l'80% dei token, su due run contro una. Un job da 2 membri costa quasi quanto uno da 6 o da 11: il costo lo fa la lettura del changeset.
- **Attivazione a vuoto:** in due casi su tre, N1 e Z1, il piano con la mappa aggiunge `stripe-auditor` a un changeset in cui nessun file cambiato né vicino a un salto importa Stripe, perché l'unità lo dichiara. In S1 l'attivazione è giusta. Il costo di quel job non è misurato: la prima tappa di `baseline` ha chiuso ogni caso prima.
- **Spesa:** 19 run di job, 3.910.134 token.

Limiti: un solo modello e due run per braccio; tre casi; mappa senza motore; `stack-dichiarato`, il controllo sano e le lenti non eseguiti, perché `baseline` ha chiuso ogni caso prima. I tre target sono commit pubblici del 2024-2026: il modello potrebbe averne visto codice o fix.
- **Fuori dal difetto atteso:** entrambe le run della foglia segnalano `ZSurveyMetadata.catchall(z.unknown())` (`packages/types/surveys/types.ts`), metadati arbitrari salvati e serializzati verso rispondenti anonimi. Non è verificato dalle lenti.

## Attivazione di `stripe-auditor` per uso, replay senza modello

Prova la regola che `review_roster.py` applica dal 2026-11-20 (§2 della spec, solo per `stripe`): l'unità che dichiara Stripe aggiunge `stripe-auditor` solo se un file di produzione cambiato o un vicino a un salto della mappa importa `stripe` o `@stripe/*`. Gli import vengono da `snapshot.py files`. Se gli import non sono noti, per un file senza parser o per un linguaggio fuori da `IMPORT_LANGUAGES`, oppure manca la mappa legata, la voce resta e il roster scrive la lacuna. Una soppressione resta in `signals.suppressed` con i file controllati.

Criterio, dichiarato prima del replay e dopo aver trovato gli import di S1, che correggono lo «0 su 3» della prima decisione: N1 e Z1 non aggiungono `stripe-auditor`; S1, dove due file cambiati importano `stripe`, lo aggiunge; il resto dei piani non cambia. Le due fixture, un import diretto e un import in un vicino a un salto, sono in `tests/test_senior_review_roster.py`, con i casi in cui l'uso è ignoto.

Replay del 2026-11-20: `plan.py` sulle stesse mappe del pilota, nessuna run con il modello.

| Caso | `stripe-auditor` prima | Dopo | File controllati | Job | Obblighi |
|---|---|---|---|---|---|
| S1 | sì | sì: `account/service.py` e `transaction/service/payout.py` importano `stripe` | 17 | 13 → 13 | 46 → 46 |
| N1 | sì | soppresso | 16 | 14 → 13 | 44 → 43 |
| Z1 | sì | soppresso | 96 | 15 → 14 | 47 → 46 |

Criterio raggiunto: nessun altro job entra o esce, e in nessuno dei tre casi gli import restano ignoti. Non misurato: se `stripe-auditor`, in N1 e Z1, avrebbe trovato qualcosa; nel pilota non è mai stato eseguito.

Per rieseguirlo: `maps.py` e `plan.py` come in «Run con il modello», sugli stessi target; `plan.py` stampa la riga `soppresso` per ogni voce tolta.
