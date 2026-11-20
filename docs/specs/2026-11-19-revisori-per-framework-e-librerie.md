# Revisori per framework e librerie: specializzazione dallo stack del modulo

**Stato:** proposta, 19 novembre 2026. Nulla è applicato. Il pilota misurato il 20 novembre non promuove nessuna voce: vedi «Esito della prova». Presuppone lo Step 2 dello stack per modulo ([ADR del 17 novembre 2026](../adr/2026-11-17-mappa-moduli-stack-e-reattivita.md) e commit `94df39bad`) e la selezione dei revisori di [`2026-11-07-review-context-and-selection.md`](2026-11-07-review-context-and-selection.md).

Ora che `technologies.py` distingue per ogni modulo i **framework** (103 riconoscibili nel registro) e le **librerie** (124 catalogate più ogni pacchetto dichiarato), Daodan deve usare quel fatto nella review senza moltiplicare i subagenti, senza attivarsi a vuoto sui monoliti e senza portare nei prompt regole di stile o comandi sull'host.

## Parole

- **Ruolo di framework:** un revisore autonomo in `daodan/review/roles/<nome>-auditor.md` (~35 righe) per un runtime che introduce un proprio modello di esecuzione, stato, reattività o confine client/server.
- **Foglia di libreria:** un controllo compatto in `daodan/review/roles/<nome>-auditor.md` (~20–25 righe) per una libreria (ORM, validazione, SDK) che non crea un job proprio ma si aggrega come `member` al revisore che già presidia quel dominio.
- **Superficie del framework:** le estensioni sorgente e i file di configurazione su cui il runtime agisce dentro l'unità di build che lo dichiara.
- **Segnale d'uso:** la prova che i file toccati (o i vicini a un salto in `read_scope`) importano o chiamano davvero una libreria dichiarata dal modulo.

## Comportamento attuale

- `daodan/core/technologies.py` scrive in `technologies.json` (`daodan/technologies/v1`), per ogni modulo e unità fisica (`units`), `frameworks`, `libraries` (`{ecosystem, name, path, line, version?, id?, title?}`), `services`, `tools` e l'unione `technologies`.
- `daodan/core/review_roster.py` legge solo `unit.get("technologies", [])` in `unit_technologies` (righe 556–565) e mappa in `TECHNOLOGY_ROLE` (righe 130–134) tre sole voci: `react`, `tauri`, `stripe`. Gli altri 101 framework e le 124 librerie catalogate non attivano nulla.
- `unit_technologies` attiva una voce sull'intera unità di build appena un qualsiasi file di produzione dell'unità è toccato: in un monolite che dichiara `stripe` nel manifest, modificare una funzione di date attiva `stripe-auditor`. Osservato su un caso reale: in S1 di [`benchmarks/stack-reviewers`](../../benchmarks/stack-reviewers/README.md) la mappa aggiunge `stripe-auditor` a un changeset che non usa Stripe.
- In `daodan/core/composition.py`, `stack_skip` (righe 195–212, usato nella copertura `review_basis == "content"`) conosce solo `typescript`, `react`, `python` e le chiavi di `SIGNAL_PATTERNS`: qualunque nuovo ruolo di stack privo di regex in `SIGNAL_PATTERNS` vedrebbe tutti i file sorgente marcati `not-applicable`.
- Il contratto `reviewer-binding.toml` prevede `knowledge_ids`, ma `composition.py` (riga 290) passa oggi solo una stringa globale `knowledge_selection`, mentre possiede già il meccanismo completo delle foglie `members` con digest SHA-256 (`source_bindings`) e rendicontazione per membro in `delivery_problem` (righe 264–278, 388–391).
- Nel riferimento esterno analizzato (`github.com/affaan-m/ecc`), esistono 5 soli agenti di framework (`django`, `fastapi`, `flutter`, `react`, `vue`) e 0 agenti di libreria (coperte da ~35 skill/regole statiche), scelti a mano o dal prompt, con prompt da 79 righe (`fastapi-reviewer`) a 252 (`flutter-reviewer`) che mescolano difetti causali, regole da linter e comandi eseguiti sull'host (`manage.py check`, `eslint`, `vue-tsc`).

## Proposta

### 1. Due livelli, la stessa meccanica di `catalog.toml` e `composition.py`

Nessun nuovo contratto JSON e nessun motore parallelo per `knowledge_ids`. Tutto passa dai ruoli foglia `.md` in `daodan/review/roles/` e da `catalog.toml`:

1. **Ruoli di framework (`TECHNOLOGY_ROLE`):** riservati ai runtime la cui semantica d'esecuzione non è riducibile al generalista. In `branch` automatica entrano nel `roster` come job propri; in Phase 1 di `team-review` compaiono fra i candidati con evidenza dello stack toccato; in `light` confluiscono nell'unico job tramite `required_specialists` (`composition.py`, righe 317–318: **0 worker aggiuntivi**).
2. **Foglie di libreria (`LIBRARY_ROLE` + `[reviewers.attachments]` in `catalog.toml`):** ogni foglia dichiara in `[reviewers.attachments]` una **foglia proprietaria** già presente nelle composizioni di dominio (`transaction-integrity-auditor` per ORM/persistenza, `input-validation-auditor` per validazione d'ingresso; mai una composizione, perché `composition.py:307` espande subito `job["members"]` alle sole foglie).
   - `review_roster.py` non aggiunge la foglia a `roster`, ma a `required_specialists`, con `source: "computed-stack"` e l'evidenza dell'unità e dell'import trovato. `computed-stack` entra in `AUTOMATIC_SOURCES`: come gli altri obblighi calcolati, cade davanti a una `selection` esplicita.
   - In `composition.py` (`bind`) una foglia con proprietaria in `[reviewers.attachments]` non apre mai un job, né da `required_specialists` né da `selection`: viene aggiunta a `members` del job più specifico nel piano (minimo `len(job["members"])`) che già contiene la foglia proprietaria.
     - Con `selection` `"automatic"` (o assente, come in `light`) l'ospite è `data-integrity-auditor` o `security-auditor` quando sono nel roster, altrimenti `code-auditor`; in `light` è l'unico job.
     - Con una `selection` esplicita dal passo 2 di Phase 1 (`2026-11-07-review-context-and-selection.md`) vale la scelta del coordinatore: la foglia è legata solo se `selection` la nomina, e si aggrega all'ospite fra i revisori scelti. Una foglia calcolata e non scelta compare in `selection.superseded`. Una foglia scelta senza un revisore che contenga la sua proprietaria non ha job: resta in `gaps`, e `bind` esce con `0` perché nessun job è `unbound`.
   - L'ospite per dominio vale finché la prova non sceglie fra questo e l'ospite di stack (sezione «Prova», punto 2).
   - Un modulo con Next.js + React + Prisma + Zod + Stripe non apre più 5 worker di libreria: le foglie Prisma e Zod aggiungono ~40 righe totali ai worker già previsti, verificate da `body_sha256` e chiuse in `member_results`.

### 2. Regole di attivazione: superficie per i framework, segnale d'uso per le librerie

`unit_technologies` in `review_roster.py` viene sostituita da una lettura per file toccato sull'unità fisica più specifica (`technologies.json`, `units`) che lo contiene, risolvendo la `category` reale tramite la tabella top-level `technologies["technologies"]` (poiché `unit["libraries"]` in `technologies.py:135-143` elenca tutti i pacchetti dichiarati, inclusi tool e framework):

- **Framework (`unit["frameworks"]`):** un ID in `TECHNOLOGY_ROLE` scatta solo se almeno un file di produzione cambiato dentro quell'unità appartiene alla `FRAMEWORK_SURFACE` di quel framework (estensione del linguaggio ospite o file di configurazione proprio del framework). Modificare un `Makefile` o uno script `.sh` in un pacchetto Django non attiva `django-auditor`.
- **Librerie e SDK (`LIBRARY_ROLE` su `unit["technologies"]`, più dipendenze implicite dichiarate come `IMPLIED_LIBRARIES = {"fastapi": ("pydantic",)}` e `stripe` in `TECHNOLOGY_ROLE`):** cercare in `unit["technologies"]` copre anche voci catalogate come `"framework"` ma trattate come foglia ORM (`spring-data-jpa`), mentre `IMPLIED_LIBRARIES` copre `pydantic` nei progetti FastAPI che non la ripetono nel manifest. La voce scatta solo se l'unità la dichiara (o la implica) **e** c'è un segnale d'uso esplicito (`LIBRARY_IMPORTS` / `SIGNAL_PATTERNS`) nel perimetro:
  1. con mappa disponibile, almeno un file in `changed_paths` o nei vicini a un salto (`map_signals["read_scope"]`) importa un namespace della libreria (dagli import registrati nello snapshot o in `context["sources"]`);
  2. senza mappa (o per file non ancora indicizzati), corrispondenza nelle righe cambiate del diff o nel testo di `context["sources"]` tramite il pattern di import/API dedicato, registrando la consueta lacuna di mappa assente.
- **Lacuna di baseline dichiarata (`signals["unmatched_stack"]`):** ogni voce con `category == "framework"` (quando un file toccato cade nella sua unità) o `category == "library"` (dichiarata nell'unità toccata; `"tool"` e `"service"` sono esclusi) priva di copertura in `TECHNOLOGY_ROLE` e `LIBRARY_ROLE` viene riportata in `signals["unmatched_stack"]` (`[{id, category, unit}]`) a livello di unità, senza indovinare namespace d'import arbitrari per le 119 librerie fuori `LIBRARY_ROLE`. Phase 1 e il report finale dichiarano così la baseline mancante senza falsi rumori su pytest/eslint/docker.
- **Passaggio dei perimetri d'unità a `composition.py`:** quando `technologies` è vincolato allo snapshot candidato, `review_roster.py` salva in `signals["unit_stacks"]` `[{paths, technologies}]` delle unità di `technologies.json`, così `composition.py` conosce i confini delle unità senza nuovi argomenti CLI né modifiche a `BINDINGS.json` (e il dato sopravvive ad `apply_selection`).

### 3. Copertura sull'intero sorgente (`composition.py`, `stack_skip`)

In `composition.py`, `stack_skip` distingue i revisori di linguaggio esistenti (`LANGUAGE_ROLE`: `typescript`, `react`, `python`, che mantengono l'attuale regola `row["language"] is None -> open` su file privi di linguaggio indicizzato) dai ruoli di framework governati da `FRAMEWORK_SURFACE` e `signals["unit_stacks"]`:

- Per un ruolo di framework con `FRAMEWORK_SURFACE`, un file è `open` solo se cade nei `paths` di un'unità che dichiara quel framework in `signals["unit_stacks"]` (quando presente) **e** il suo suffisso o nome file appartiene alla `FRAMEWORK_SURFACE` del framework (o ai manifest/configurazioni in `keep`), valutando il suffisso sul percorso anche quando `row["language"]` è `None` (come accade oggi per `.dart`, non presente in `SUPPORTED_EXTENSIONS` di `languages/__init__.py`). Un file `.py` o `.dart` fuori dall'unità del framework diventa quindi `not-applicable`.
- Una foglia di libreria aggregata a un job di dominio (`data-integrity-auditor`, `code-auditor`) non restringe le celle del job ospite; nella propria voce di `member_results` rendiconta i file del gruppo che importano la libreria e dichiara non applicabili gli altri.

### 4. Allineamenti minimi al registro dello stack (`registry-additions.json`)

Tre segni mancanti verificati su `daodan/data/service-registry.json` impedirebbero il riconoscimento nei layout reali:

1. `prisma`: aggiungere `@prisma/client` a `signs.packages.npm` (nei monorepo l'applicazione dichiara `@prisma/client` e lascia `prisma` CLI + `schema.prisma` al pacchetto database).
2. `nextjs`: aggiungere `next.config.ts` a `signs.files`.
3. `nuxtjs`: aggiungere `nuxt.config.ts` a `signs.files`.

### 5. Primo lotto: ruoli, foglie e confini causali

Ogni file in `daodan/review/roles/` segue la struttura di `react-auditor.md` e `stripe-auditor.md` (Mandate and input, Causal checks su percorso raggiungibile, Counterevidence, Boundaries and output; ~35 righe per i ruoli, ~22 righe per le foglie). Nessuna regola di stile/formattazione, nessuna soglia arbitraria di lunghezza file e nessun comando eseguito sull'host. Dai reviewer e dalle skill di `affaan-m/ecc` entrano solo i difetti causali che il floor attuale non può dedurre senza conoscere il runtime o la libreria:

| ID registro (`service-registry.json`) | Identità catalogo | Tipo (proprietario se foglia) | Superficie / Segnale d'uso | Controlli causali esclusivi | Confini (resta agli altri ruoli) |
|---|---|---|---|---|---|
| `vue`, `nuxtjs` | `senior-review:vue-auditor` | Ruolo framework | `.vue`, `.ts`, `.js`, `nuxt.config.*` | Perdita di reattività (`reactive` riassegnato, destrutturazione props `<3.5` vs `watch(prop)` diretto in `3.5+`, `.value` omesso o getter `watch(() => ref)` sul contenitore), stato/timer a livello modulo nei composable o mancato teardown, `v-if`+`v-for` sullo stesso nodo, mutazione di props, in `nuxtjs` segreti in `runtimeConfig.public`, API browser fuori client guard e `useAsyncData`/`useFetch` senza chiave stabile | `v-html`/URL non validati → `browser-security`; ARIA/tastiera → `accessibility`; tipi TS → `typescript-auditor` |
| `nextjs` | `senior-review:nextjs-auditor` | Ruolo framework | `.tsx`, `.jsx`, `.ts`, `.js`, `next.config.*` | Confine Server/Client (`"use client"` che importa moduli server-only o propaga al sottoalbero, record completi con campi riservati serializzati verso Client Component, segreti in `NEXT_PUBLIC_*`), funzioni `"use server"` esposte senza verifica di autenticazione/autorizzazione o schema d'ingresso (se l'autorizzazione sta nel middleware, conta se il suo `matcher` copre davvero il percorso che porta alla lettura o alla mutazione protetta: è un difetto solo un percorso raggiungibile senza autorizzazione, non l'assenza di un secondo controllo nell'azione), fetch/route con caching o revalidazione incoerente rispetto a dati per-utente | Hook, chiavi e render React → `react-auditor`; XSS/header → `browser-security` |
| `django` | `senior-review:django-auditor` | Ruolo framework | `.py` | Scritture multi-step fuori `transaction.atomic()` o `on_commit` mancante per effetti esterni, `save()` completo che sovrascrive colonne aggiornate concorrentemente (`update_fields`), migrazioni distruttive in un passo solo o `RunPython` non atomico/irreversibile, viste/serializer DRF senza `permission_classes`, con `fields = '__all__'` scrivibili o liste non paginate, signal con effetti nascosti o non registrati in `AppConfig.ready()` | SQL injection e input grezzo → `input-validation`; indici/piani query generali → `sql-efficiency`; Python generale → `python-auditor` |
| `fastapi` | `senior-review:fastapi-auditor` | Ruolo framework | `.py` | Chiamate I/O sincrone/bloccanti dentro `async def` (bloccano l'event loop), sessioni/connessioni create inline invece che via `Depends` con `yield` e cleanup su eccezione, uso di sessioni chiuse nei `BackgroundTasks`, endpoint senza `response_model` che restituiscono modelli ORM/interni con campi sensibili, override di dipendenze errati | Validazione Pydantic specifica → foglia `pydantic-auditor`; CORS/auth token → `security-auditor` |
| `spring-boot`, `spring-mvc`, `spring-webflux` | `senior-review:spring-auditor` | Ruolo framework | `.java`, `.kt`, `application*.yml/properties` | Auto-invocazione `this.metodo()` che aggira i proxy (`@Transactional`, `@Async`, `@Cacheable`, `@PreAuthorize`), eccezioni checked che non attivano il rollback senza `rollbackFor`, stato mutabile per richiesta dentro bean singleton, ciclo di vita transazione vs invio messaggi/HTTP; se l'unità dichiara `spring-webflux`, chiamate bloccanti (`.block()`, JDBC, `Thread.sleep`) sui thread event-loop | Associazioni JPA/Hibernate → foglia `jpa-auditor`; SQL e pool → `sql-efficiency` / `capacity-quota` |
| `flutter` | `senior-review:flutter-auditor` | Ruolo framework | `.dart`, `pubspec.yaml` | Uso di `BuildContext`, `Navigator`/`ScaffoldMessenger` o `setState` dopo un `await` senza controllo `mounted`, `TextEditingController`/`AnimationController`/`StreamSubscription`/`FocusNode` non rilasciati in `dispose()`, creazione di `Future`/`Stream`/controller dentro `build()` che riavvia il lavoro a ogni rebuild | Layout accessibile/contrasto → `accessibility`; concorrenza generale → `local-concurrency` |
| `prisma` | `senior-review:prisma-auditor` | Foglia (`transaction-integrity-auditor`) | Import `@prisma/client` / `prisma` o `schema.prisma` | Scritture correlate fuori `$transaction` (interattiva vs batch e timeout), valori `undefined` nei filtri `where` che allargano silenziosamente `findMany`/`updateMany`/`deleteMany`, `include`/`select` annidati senza limiti o che espongono colonne riservate | Migrazioni/lock generali → `schema-coherence`; N+1 generici → `sql-efficiency` |
| `sqlalchemy` | `senior-review:sqlalchemy-auditor` | Foglia (`transaction-integrity-auditor`) | Import `sqlalchemy` | `Session`/`AsyncSession` condivisa fra task concorrenti o richieste, caricamento lazy implicito su `AsyncSession` (`MissingGreenlet`) o dopo chiusura sessione, oggetti scaduti per `expire_on_commit=True` letti fuori transazione, `flush`/`commit` parziali nei cicli | Transazioni e isolamento → `transaction-integrity` |
| `hibernate`, `spring-data-jpa` | `senior-review:jpa-auditor` | Foglia (`transaction-integrity-auditor`) | Import `jakarta.persistence` / `javax.persistence` / `org.springframework.data.jpa` / `org.hibernate` | `LazyInitializationException` fuori confine transazionale, modifiche su entità managed flushate implicitamente in metodi di lettura privi di `@Transactional(readOnly = true)`, query derivate/associazioni lazy che causano N+1 senza `JOIN FETCH` o `@EntityGraph`, `equals`/`hashCode` mutabili su ID generati | Schema/migrazioni → `schema-coherence` |
| `pydantic` | `senior-review:pydantic-auditor` | Foglia (`input-validation-auditor`) | Import `pydantic` | Espressioni valutate una sola volta a import-time nei `Field(default=...)` invece di `default_factory`, `extra='allow'` su modelli d'ingresso non fidati, coercizione silenziosa di tipi (per es. booleani/numeri da stringhe) dove il dominio richiede `strict`, validatori `mode='before'` che mutano dizionari condivisi del chiamante | Sanitizzazione verso sink SQL/HTML/shell → `input-validation` / `untrusted-resource` |
| `zod` | `senior-review:zod-auditor` | Foglia (`input-validation-auditor`) | Import `zod` | `.passthrough()`, `z.any()` o `z.unknown()` su payload esterni che lasciano passare campi non verificati fino allo store, perdita di `.refine()`/`superRefine` o allentamento involontario con `.partial()`/`.merge()` su schemi riusati per scrittura, `.parse()` non intercettato su percorsi che richiedono errore strutturato (`.safeParse()`) | Sicurezza endpoint e auth → `authorization-auditor` |

### 6. Ordine di rilascio: quattro voci pilota, misurate prima della meccanica

Il pilota ha due ruoli e due foglie: `fastapi-auditor`, `nextjs-auditor`, `sqlalchemy-auditor`, `zod-auditor`. Coprono le due foglie proprietarie e i due ecosistemi del test sul monorepo.

1. Si scelgono i casi e si scrivono i quattro file di ruolo.
2. Si misurano con [`benchmarks/stack-reviewers`](../../benchmarks/stack-reviewers/README.md), che compone i job da copie di `catalog.toml` (`composition.py --plugin-root`) e non chiede la meccanica.
3. Si implementa la meccanica (`review_roster.py`, `composition.py`, `[reviewers.attachments]` in `catalog.toml` e i 3 segni di §4) per le voci promosse, con l'ospite che la misura ha scelto.
4. Le altre 7 voci del primo lotto si scrivono dopo, ciascuna con il proprio caso nel benchmark.

La meccanica del pilota costruisce solo ciò che le quattro voci usano. Rispetto a §2 e §3 restano fuori, finché non arriva la voce che li chiede:

- `IMPLIED_LIBRARIES`, che serve a `pydantic-auditor`;
- il suffisso valutato con `language: null` in `stack_skip`, che serve a `flutter-auditor` (`.dart`);
- `unmatched_stack` per le librerie: nel pilota riporta i soli framework, perché le librerie catalogate senza foglia sono 119 su 124 e comparirebbero in ogni review dell'unità che le dichiara.

## Limiti

- Senza una mappa fresca (`technologies.json` assente o di un altro snapshot), `review_roster.py` non conosce `unit["frameworks"]` né `unit["libraries"]`: resta il solo ripiego per estensione che esiste oggi (`.tsx`/`.jsx` in `FRAMEWORK_BY_SUFFIX`, `review_roster.py:86`) e `SIGNAL_PATTERNS`. Senza mappa i nuovi ruoli di framework e le foglie di libreria non scattano, e la lacuna di stack non risolto è dichiarata in `gaps`.
- Una libreria incapsulata dietro un wrapper interno senza che né il file toccato né i vicini a un salto (`read_scope`) mostrino l'import diretto non attiva la foglia su `changeset`: il controllo scatterà quando si tocca il wrapper o in una review `content` del modulo.
- La versione dichiarata in `unit["libraries"]` (`technologies.py`, riga 141) è il testo del manifest (per es. `"^3.4.0"` o assente nei cataloghi non risolti), non la versione risolta dal lockfile: quando il comportamento dipende dalla versione (come la destrutturazione reattiva delle props in Vue `<3.5` vs `>=3.5`), il revisore deve leggerla dal manifest/lockfile se presente o dichiarare l'incertezza, mai assumere una delle due.
- Nessun revisore esegue linter, type-checker o comandi del framework sull'host: i fatti che solo l'esecuzione nel container di Daodan può provare restano regolati dalla [spec dell'esecuzione del programma](2026-11-19-esecuzione-del-programma.md).

## Prova

Parametri e soglie dichiarati nel README del benchmark prima delle misure:

1. **Precisione di attivazione (test di regressione in `tests/test_senior_review_roster.py` e `tests/test_senior_review_composition.py`):**
   - Nel pilota i test coprono le quattro voci di §6; i casi con `pydantic`, `prisma`, `.vue`, `.dart`, `.java` e `.kt` si aggiungono con la voce che li chiede.
   - Su un monorepo con pacchetti distinti (per es. `apps/web` Next.js + Zod, `services/api` FastAPI + SQLAlchemy + Pydantic), una modifica in `services/api` attiva `fastapi-auditor` e, solo se i file nel perimetro importano `sqlalchemy`/`pydantic`, aggrega le rispettive foglie senza attivare `nextjs-auditor` né `zod-auditor`.
   - Su un monolite che dichiara `prisma`, `zod` e `stripe`, una modifica a un modulo puro senza quegli import né nei file cambiati né in `read_scope` attiva **0** foglie di libreria e **0** `stripe-auditor`.
   - In modalità `light` rimane esattamente **1** job di discovery; in modalità `branch` (`standard` e `deep`) le foglie di libreria aggiungono **0** job rispetto al piano senza librerie.
   - In modalità `content` (`coverage`), `stack_skip` assegna `open` ai file `.vue`, `.dart`, `.java`, `.kt`, `.py` dentro l'unità del framework e `not-applicable` fuori da essa.
2. **Valore diagnostico vs costo token ([`benchmarks/stack-reviewers`](../../benchmarks/stack-reviewers/README.md)):**
   - Su un insieme di commit con difetto reale e oracolo noto (almeno uno per ciascuna famiglia: confine RSC/Server Action Next.js, reattività Vue, proxy `@Transactional` Spring, I/O bloccante o `Depends` FastAPI, transazione/migrazione Django, più due casi di libreria ORM/validazione; nel pilota i casi Next.js, FastAPI, `sqlalchemy` e `zod`), confronto a parità di modello fra questi bracci:
     - `baseline`: `code-auditor` + roster attuale;
     - `stack-dichiarato`: la `baseline` più una riga nel brief con framework, librerie e versioni dell'unità toccata, letti da `technologies.json`, senza nuovi file di ruolo (oggi `daodan/review/reviewer-common.md` non nomina lo stack);
     - `ruolo`: per un ruolo di framework, la `baseline` più il suo job proprio;
     - `foglia-dominio`: per una foglia, la `baseline` con la foglia nell'ospite di dominio di §1;
     - `foglia-stack`: la foglia nel job di stack della stessa unità, cioè quello del ruolo di framework (`fastapi-auditor` ospita `sqlalchemy-auditor`, `nextjs-auditor` ospita `zod-auditor`) o, se manca, quello di linguaggio (`python-auditor`, `typescript-auditor`);
     - `foglia-propria`: la foglia come job proprio, eseguito solo se `foglia-dominio` e `foglia-stack` mancano entrambi il difetto. Distingue un testo sbagliato da un'aggregazione che lo diluisce: su J2 di [`benchmarks/jupiter-alias`](../../benchmarks/jupiter-alias/README.md) i job composti trovano il difetto in 0 run su 7, il ruolo da solo in 2 su 2.
   - Criterio di promozione nel catalogo per ciascun ruolo o foglia: trova il difetto che `baseline` e `stack-dichiarato` mancano (o riduce falsi positivi), non introduce falsi positivi sui casi sani di controllo e resta nel costo. Una foglia aumenta i token del job ospite di meno del 15%; il job in più di un ruolo non costa più token del job di linguaggio sullo stesso caso (`python-auditor` per `fastapi-auditor`, `typescript-auditor` per `nextjs-auditor`), che legge gli stessi file con un mandato della stessa misura. Una voce che non supera la prova rispetto al generalista non entra nel catalogo.
   - Esiti che cambiano la proposta:
     - se `stack-dichiarato` trova il difetto, per quel caso entra la riga nel brief e non la voce;
     - l'ospite della foglia in §1 diventa quello, fra dominio e stack, che trova il difetto; a parità resta il dominio, che tiene la foglia accanto alla sua proprietaria ed evita lo stesso finding da due job;
     - una foglia trovata solo da `foglia-propria` non entra come foglia.

## Esito della prova

Misurato il 20 novembre 2026 su tre casi reali, S1 (`sqlalchemy-auditor`), N1 (`nextjs-auditor`) e Z1 (`zod-auditor`), con le regole di [`benchmarks/stack-reviewers`](../../benchmarks/stack-reviewers/README.md):

- Ogni voce trova il difetto del suo caso, ma lo trova anche `baseline`, 2 run su 2 in tutti e tre i casi: nessuna voce supera il criterio di promozione. Esito: nessun valore incrementale dimostrato sui tre casi; non è un valore nullo, dati i limiti sotto. `fastapi-auditor` non ha avuto un caso che decidesse.
- `code-auditor` trova i tre difetti in tutte e cinque le sue run. Il ruolo di linguaggio già attivo (`python-auditor`, `typescript-auditor`) li vede in tutte e cinque le sue, ma due volte li passa ad altri revisori invece di farne un finding.
- In tutti e tre i casi la mappa attiva `stripe-auditor` su un changeset che non usa Stripe: l'attivazione a vuoto descritta in «Comportamento attuale», che §2 corregge, avviene anche senza nuovi ruoli.

Limiti: un modello, due run per braccio, tre casi, mappa senza motore; i target sono commit pubblici del 2024-2026 che il modello potrebbe aver visto. I dettagli sono nel README del benchmark.

Seguito, deciso il 20 novembre 2026:

1. Il pilota è chiuso; le quattro voci restano in `benchmarks/stack-reviewers/roles/`, fuori dal catalogo. Le 11 voci di §5 e la meccanica di §1 e §3 non si implementano.
2. §2 si applica solo alle voci che `TECHNOLOGY_ROLE` ha già, `stripe` per prima, dopo una verifica senza modello: rieseguito sui tre diff del pilota, il router attiva `stripe-auditor` 0 volte su 3; su due fixture, un uso diretto e uno indiretto attraverso un helper condiviso o un webhook, lo attiva. Ogni attivazione soppressa si registra. Dove la mappa non distingue «non correlato» da «ignoto», resta l'attivazione dal manifest.
3. I tre segni di §4 si aggiungono al registro.
4. Un caso in cui `baseline` manchi il difetto, verificato e preferibilmente su un commit privato o recente, riapre la valutazione di una voce, non la promuove.

## Da decidere

- **Confine fra pista e finding:** nel pilota il difetto compare 4 volte su 19 run di job solo come pista per altri revisori o dentro la prova di un finding ancorato altrove (S1 `data-integrity-auditor`, N1 e Z1 `typescript-auditor`, Z1 `foglia-dominio`). In tre casi un altro job della stessa run lo segnala; in una review dove quel job non c'è, la pista si perde. Proposta per il consolidamento: un rilievo con file e riga si tiene come finding qualunque sia il ruolo che lo scrive, e una pista che il destinatario non conferma, o indirizzata a un revisore non dispacciato, resta visibile come non risolta. Si verifica senza modello sui report del pilota.

- **Linguaggi ospiti mancanti:** per `spring-auditor` (`.java`, `.kt`) e `flutter-auditor` (`.dart`) non esistono oggi `java-auditor`, `kotlin-auditor` né `dart-auditor` in `LANGUAGE_ROLE`; decidere se restano coperti dal solo `code-auditor` + `spring-auditor`/`flutter-auditor` (scelta minimale consigliata) o se dichiarare lacuna di linguaggio.
- **Fonte degli import in `review_roster.py`:** passare a `review_roster.py` la mappa `{path: external_imports}` estratta dallo snapshot esistente (estendendo l'output di `snapshot.py technologies` o `snapshot.py files` senza rileggere i sorgenti), con ripiego su diff/`context["sources"]` quando lo snapshot manca. Verificato: per ogni file analizzato, di qualunque linguaggio, la voce dello snapshot porta `imports` con i moduli come scritti nel sorgente (`snapshot.py:161`, da `ImportInfo.module`), quindi anche JS/TS (`languages/javascript.py:673`). Resta da decidere solo quale comando di `snapshot.py` li espone a `review_roster.py`.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
