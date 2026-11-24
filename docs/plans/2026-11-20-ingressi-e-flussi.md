# Piano: ingressi e flussi, la macchina mostra e il modello nomina

**Stato:** In parte. Nel codice: il gestore dall'indice del motore, l'etichetta secondo accname, Noir nella pre-mappa, le forme classificate una volta, le schede dei percorsi nel nucleo (`daodan/core/flow_paths.py`), Secretlint su ogni risposta che esce, l'esplorazione dell'app avviata, gli eventi Tauri, le sorgenti dei framework Next.js, React Router e Remix, SvelteKit, Nuxt, Astro e Angular (`daodan/core/premap/`), il legatore degli endpoint di Noir (`daodan/core/binder.py`), le rotte dichiarate come rotte offerte, la prova del wrapper HTTP, la chiave dello store come indice. Qui restano i punti aperti di ogni task, i task non iniziati e le misure che non hanno ancora un altro posto.

**Obiettivo:** la macchina legge gli ingressi (controlli dell'interfaccia, rotte, comandi e gli altri tipi), compone un percorso per ingresso e lo certifica; ciò che esce verso un modello passa il controllo dei segreti.

**Spec:** `docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md`; per 7b `docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md`, sezione 8; per l'esplorazione `docs/specs/2026-11-19-interfacce-del-progetto.md`, sezione 7. **Ordine fra i piani e prova da zero:** [pipeline intera](2026-11-20-pipeline-intera.md).

**Vincoli:** prima il test rosso, poi il codice; ogni task tocca solo i file che nomina. Prima di ogni sorgente si esegue lo strumento ufficiale su una fixture nel container e si scrive che cosa dà davvero: se non dà la riga o il dato, la voce si ferma lì con la causa, senza un lettore scritto a mano al suo posto.

Chiusi senza punti aperti, e quindi fuori da questo elenco: 4 (evento o no, etichetta), 5 (Noir nella pre-mappa), 7c (i flussi dicono ciò che non sanno).

## Punti aperti dei task fatti

### 3. Il gestore dall'estremo del motore

- Nessun test registra righe del motore su un gestore `self.` o `this.`: quel ramo di `entries._function` è nel codice e non è provato.

### 6. Le forme si classificano una volta

- Nessun test asserisce `shapes` nella risposta `needs_rules` né la tabella nel prompt `LINKS`.
- Un attributo scritto su più righe è letto, ma nessun test lo classifica e lo applica dall'inizio alla fine.

### 7. Le schede dei percorsi nel nucleo

- `benchmarks/system-map/traces.py` e `test_traces.py` restano, con `ENTRY_GLOB` e la riga di comando; i test del nucleo (`tests/test_codebase_map_trace_cards.py`) sono nuovi, non il porting dei sei del benchmark.

### 7b. La mappa non perde ciò che rifiuta

- `on` fra due nodi con codice non cita il suo punto: `system_map._evaluate` lo dà `declared` se i due nodi sono accettati, e un nodo non ha il campo `cite`. Nessun test lo chiede.
- Un membro `store:` che nessuna regola legge finisce in `unlinked` e il nodo resta accettato per gli altri membri. La macchina non distingue una chiave scritta male da una che nessuna regola legge; un flusso il cui effetto è un nodo con uno store in `unlinked` può risultare `verified` per l'altro membro, senza che lo store sia provato.

### 8. Secretlint su ciò che esce

- Il tempo di un avvio di Secretlint per testo non è misurato (`secret_mask.TIMEOUT` lo dice).
- I test provano una lettura, un risultato annidato e un errore; non una lacuna e una rotta in particolare.

### 11. La fonte osservata

Nel codice: `premap/npm_start.py` (`starts` da `package.json#scripts`), `dynamic/app.py` e `app.cjs` (avvio nel container), `dynamic/explore.cjs` (controlli dall'albero di accessibilità, ogni controllo una volta, il gestore isolato con il punto di interruzione di Chrome), `observed_entries.py` (candidati con fonte osservata), `flows._observed_entries`. Misura su phazly: [`benchmarks/project-model`](../../benchmarks/project-model/README.md), «Esplorazione dell'app avviata».

- Solo `npm`: pnpm, Yarn e Bun sono una lacuna.
- Le altre fonti di `starts` non sono lette: Angular, Tauri, Cargo, Dockerfile, Compose.
- Credenziali di prova: dei 33 controlli iniziali dei flussi del riferimento di phazly il lettore statico ne copre 10 e l'esplorazione non ne aggiunge; 23 stanno dietro l'accesso o fuori dalla pagina.
- La pagina offerta dal server (spec delle interfacce, 7.5) ed Electron e Tauri (7.6) non sono eseguiti.
- Il motore di container di Windows.
- La compilazione dei moduli per tipo HTML è una proposta («Da decidere» della spec delle interfacce).
- Proposta non applicata: l'esplorazione parte dai controlli per cui manca la prova della stessa terna elemento, evento e stato osservabile (`docs/specs/2026-11-15-pipeline-di-analisi.md`, 7.3).

### 11b. Gli eventi fra pagina e guscio Tauri

- Tauri 1 (`Window::emit`, `emit_all`, `listen_global`) non si legge.
- Il tratto nello scope prova che il metodo è di Tauri, non che il ricevente lo sia (`shortcut` in `bind_tauri_events`).
- Nessun progetto del corpus ha eventi: la prova sono le fixture di `tests/test_codebase_map_tauri_events.py`.

### 13. Lo strumento ufficiale del framework

Ogni voce è una sorgente della pre-mappa nel container, con la sua prova e le sue misure nel benchmark indicato. Un controllo che una sorgente statica non lega alla sua funzione resta da chiudere al passo dinamico, che preme i controlli nel browser e isola il gestore (task 11): quanti ne chiude, per framework, non è misurato.

- **13a. Next.js** (`premap/nextjs.py`, `next typegen`; [`benchmarks/next-server-actions`](../../benchmarks/next-server-actions/README.md)). «Gira sul server»: né `next typegen` né `next analyze` danno nome, riga o `id` di una funzione `"use server"`; il simbolo dell'azione viene da Noir (`kind: server-action`). Aperto:
  - che il simbolo di Noir sia quello della scheda nella pipeline non è verificato;
  - non verificati: una funzione `"use server"` in linea, più azioni in un file, funzioni a freccia, `export default`, azioni importate da un componente client, `"use cache"`; `next analyze` su un progetto reale, con Webpack o con `distDir` diverso;
  - `distDir` diverso e Next.js senza `typegen` danno la stessa lacuna `model_failed`; il Pages Router è provato solo con il testo dei blocchi scritto a mano; `<form action>` è fuori dal registro; etichette delle rotte; il segmento `a-[id]`; Noir con `[id]`; nessun progetto reale.
- **13b. React Router e Remix** (`premap/react_router.py`, `react-router routes --json`; [`benchmarks/react-router-routes`](../../benchmarks/react-router-routes/README.md)). Aperto:
  - le rotte offerte: servono la tabella dei metodi per esportazione, la conversione del percorso per `*` e `:lang?`, e la tavola `http` di `flows._declared_routes`, che oggi nomina Noir e Next.js;
  - le righe di Noir sulle stesse rotte non si uniscono a quelle di React Router: l'unione riguarda solo Next.js;
  - la libreria senza `@react-router/dev` (`createBrowserRouter`, `<Routes>`) non ha un comando e non è letta: è una lacuna con la causa;
  - il `basename` non è nell'uscita del comando: nessuno strumento ufficiale lo dà senza un build;
  - limiti dichiarati con `# shortcut:` in `react_router.py`: lo standard output si legge intero e una riga di log lo rende una lacuna; una cartella dell'app diversa da `app`; un figlio assoluto fuori dal percorso del padre; il comando lanciato anche nella radice di un workspace dove il pacchetto è sollevato; l'exit 137 non riprodotto; più di 90 cartelle chiedono più dei 900 secondi che si dividono;
  - non misurato a runtime né con Remix; il `middleware` della radice non è letto; nessun progetto reale.
- **13c. SvelteKit** (`premap/sveltekit.py`, `svelte-kit sync`; [`benchmarks/sveltekit-routes`](../../benchmarks/sveltekit-routes/README.md)). Aperto:
  - le azioni dei moduli (`actions`): servono i membri dell'oggetto legati alle funzioni, che né lo strumento né lo snapshot danno (il controllore dei tipi di TypeScript non è valutato);
  - le rotte offerte: nessuno strumento dà la conversione dell'id nell'URL; unire per file e riga le righe di Noir a quelle delle funzioni di `+server` darebbe rotte offerte con il gestore, non scritto;
  - `+page.svelte` per rotta; il `load` dei layout è «nessun ingresso», da confermare;
  - `export const load = (...) satisfies PageServerLoad` è una riga con la lacuna `unsupported-target-kind`; un metodo con overload è `export-ambiguous`;
  - `kit.outDir` diverso da `.svelte-kit`; `route_meta_data.json` non è documentato; SvelteKit 1 non provato; nessun progetto reale;
  - `premap/sveltekit.py` importa `_starts` e `_excerpt` da `premap/react_router.py`: andrebbero in `flow_entries.py`.
- **13d. Nuxt** (`premap/nuxt.py`, `nuxt prepare` e `@nuxt/kit`; [`benchmarks/nuxt-routes`](../../benchmarks/nuxt-routes/README.md)). Aperto:
  - 10 gestori su 11 della fixture sono righe sul file con la lacuna: `export default defineEventHandler(...)` è una chiamata che i record di esportazione dello snapshot non legano;
  - le rotte offerte: mancano la funzione del gestore, la conversione del percorso (`**:path`), il significato di `default` per la chiave dell'unione, la tavola `http`;
  - Noir e Nuxt sulla stessa rotta non si uniscono; le due rotte di Nuxt stesso sono una lacuna `outside_snapshot` in ogni progetto;
  - `@nuxt/kit` risolto dalla cartella del progetto: con pnpm o Yarn può non essere lì (non provato);
  - nessun progetto reale; tempo e memoria su un progetto grande non misurati; Nuxt 2, una versione prima della 3.21 e Nitro 3 non provati; un modulo che si collega a un servizio durante `loadNuxt` non provato; rotte aggiunte da un modulo, layer con un loro `server/`, `srcDir` e `serverDir` diversi, gestori `.mts` e `.mjs`.
- **13e. Astro** (`premap/astro.py`, `parse` del compilatore del progetto; [`benchmarks/astro-compiler`](../../benchmarks/astro-compiler/README.md)). La sorgente dà il sito di ogni evento, non la funzione: 0 ingressi nei collegamenti, solo lacune con il sito. Aperto:
  - il legame del gestore a una funzione: quale funzione il globale della pagina tiene sotto un nome non lo dice nessuno strumento ufficiale (non misurato che cosa dà `transform`);
  - una sorgente delle rotte: `sync()` dell'API di `astro` con un'integrazione fa scattare `astro:routes:resolved` con file e tipo di ogni rotta (misurato), non scritta;
  - il compilatore Go non dà diagnostica su markup che non si chiude: lì un gestore perso è perso senza una lacuna;
  - `new Thing()` e un template con tag non sono letti; le etichette dei controlli non sono lette; `onend` di `<animate>` non è un evento per Astro;
  - nessun progetto Astro vero misurato; pnpm e Yarn non provati; Astro 4 e Node 18 non eseguiti; la `VERSION` è legata allo script solo da un test che avvisa.
- **13f. Angular** (`premap/angular.py`, `parseTemplate` del progetto e il controllore dei template; [`benchmarks/angular-compiler`](../../benchmarks/angular-compiler/README.md)). Aperto:
  - `host: {…}` e `@HostListener` non sono letti; `(saved)`, l'uscita di un componente figlio, e `(click)` non si distinguono; un gestore proprietà-freccia è una lacuna «non dichiara». Il controllore dei template li dà tutti e tre: misurato, non collegato;
  - `_enableTemplateTypeChecker` e `getTsSymbolOfSymbol` non sono API pubbliche;
  - un riferimento del template (`#box`) non ha un caso registrato; le righe di `svc.cancel()` e `this.save()` non hanno etichetta;
  - un `tsconfig.json` solution-style di un progetto vero, una versione di Angular prima della 20, la fixture `js-angular` di project-model: non provati; tempo e memoria del controllore dei tipi su un progetto grande non misurati.

### 14. Le rotte che nascono all'avvio

Esito misurato su 25 applicazioni vere di 11 framework ([`benchmarks/noir-binding`](../../benchmarks/noir-binding/README.md)): le sorgenti che caricano il framework non aggiungono a Noir quanto costano e non sono collegate; il lavoro che resta è il legame degli endpoint di Noir alle funzioni dello snapshot. Regola per le voci che restano: prima si misura il legame di Noir, poi, solo dove Noir non dà il gestore, il framework.

- **Legatore per posizione e nome** (`binder.py`, `flows.bind_declared`). Aperto: una funzione anonima dentro una closure di rotta di Go o C# resta il nodo condiviso `(func)` o `(lambda)` della funzione che registra; una funzione anonima citata per posizione si lega qualunque nome Noir le dia; un registratore anonimo sulla stessa riga della closure non si distingue da lei; le regole messe in attesa da una decisione di tracciamento non sono ancora registrate per i candidati; una classe annidata non è fra i casi misurati.
- **14a. FastAPI** ([`benchmarks/fastapi-routes`](../../benchmarks/fastapi-routes/README.md); `premap/fastapi_app.py`, scritta e non collegata). Aperto: applicazioni vere con `add_route`, più metodi su un `api_route`, metodi legati; dare alle righe di Noir del secondo metodo il gestore della prima; `root_path`, `lifespan`, rotte aggiunte all'avvio, WSGI montato; il container di Daodan; le impostazioni che rifiutano i segnaposto dei `.env`.
- **14b. Django** ([`benchmarks/django-routes`](../../benchmarks/django-routes/README.md); `premap/django_app.py`, scritta e non collegata). L'unico guadagno misurato è sui router di DRF registrati da funzioni: se un progetto reale lo chiede, la sorgente vale lì. Aperto: il ripristino di DefectDojo e bakerydemo non è misurato nel container di Daodan; Django dichiarato dietro un `-r` non avvia la sorgente; `@api_view`; perché 72 funzioni di DefectDojo che Noir cita mancano dall'elenco del framework.
- **14c. Flask** ([`benchmarks/flask-routes`](../../benchmarks/flask-routes/README.md); `premap/flask_app.py`, collegata e poi scollegata). Aperto: `declared()` toglie un `HEAD` dichiarato da una classe (non corretto); `flask_app._python_folders` confronta `name == "flask"` e un `Flask>=3` di un `pyproject.toml` non avvia la sorgente; la pre-mappa non legge i pacchetti risolti di nessun lock Python; `premap/uv.py` e il `read(lock)` del passo dinamico guardano il checkout e non il perimetro; `docs/plugins/codebase-map-supporto.md` da rigenerare (`support_table.py build`).
- **14d. Laravel e 14e. Rails** ([`benchmarks/laravel-routes`](../../benchmarks/laravel-routes/README.md), [`benchmarks/rails-routes`](../../benchmarks/rails-routes/README.md)). Fermi: Noir dà controller e azione, ma Daodan non legge PHP né Ruby e nessun endpoint si lega. Il limite è il lettore del linguaggio, fuori da questo piano.
- **14f. Spring Boot** ([`benchmarks/spring-actuator-mappings`](../../benchmarks/spring-actuator-mappings/README.md)). La sorgente non si scrive. Aperto: applicazioni con costanti, meta-annotazioni o segnaposto nei percorsi, dove Noir potrebbe sbagliare; Gradle, Kotlin, Spring Boot 3.0–3.4. Trovato a parte: `preparation.RESTORES["maven"]` non dà un repository che costruisce senza rete su nessuna delle tre applicazioni vere; riguarda ogni passo che costruisce un progetto Maven e va rivisto con la sua misura.
- **14g. Gin** ([`benchmarks/gin-routes`](../../benchmarks/gin-routes/README.md)). La sorgente non si scrive. **Il passo che vale:** legare, dentro Daodan e dai dati che il motore ha già (l'indice di scip-go per la definizione dell'ultimo argomento della chiamata alla riga di registrazione), l'endpoint senza gestore alla sua funzione, nella forma generica che non nomina Gin (echo, chi, fiber, `net/http`). Aperto anche: le 10 fabbriche generiche di go-admin; rotte registrate dopo l'ascolto.
- **14h. NestJS e 14i. Expo Router** ([`benchmarks/nestjs-routes`](../../benchmarks/nestjs-routes/README.md), [`benchmarks/expo-router-routes`](../../benchmarks/expo-router-routes/README.md)). Noir basta per il legame; lo strumento del framework non è stato eseguito. Aperto per Expo Router: le schermate non sono nel report di Noir.
- **14j. Express** ([`benchmarks/express-routes`](../../benchmarks/express-routes/README.md)). Nessuna interfaccia pubblica elenca le rotte; restano quelle di Noir. Aperto: nulla è stato eseguito a runtime; l'assenza di `stack` nella documentazione è letta su una pagina troncata.

### 17. I lettori di GitNexus, la prova del wrapper, le rotte dichiarate

Deciso: nessun lettore HTTP di GitNexus entra in Daodan. Il codice dell'upstream è PolyForm Noncommercial e Daodan è distribuito come MIT: resterebbe fuori dal codice di Daodan in ogni caso; e dopo la regola d'oro un lettore di GitNexus è un lettore scritto a mano.

- **La prova del wrapper** (`daodan/core/http_wrappers.py`, `daodan/data/http-clients.json`, comando `flows.py wrappers`; misura in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md)). Aperto: il wrapper di un wrapper non è provato; il comando non è nella coda delle domande, nel servizio MCP né nello schema dei collegamenti; mancano gli altri client (axios, requests, httpx); per un linguaggio diverso da JavaScript e TypeScript serve che il suo lettore dichiari ogni bersaglio di un'assegnazione e lasci irrisolto ciò che non legge.
- **Le rotte di Noir e di Next.js come rotte offerte** (`flows.link_facts`, servizio `*`). Aperto: non misurato su un progetto senza nessuna regola `offre`; come Noir scrive un segmento dinamico di Next.js non è misurato; `_next_path` legge il testo del percorso, non `ParamMap` di `routes.d.ts`; una pagina che solo Noir riporta porta il metodo di Noir e può essere offerta; una regola `/x/{}` batte una dichiarata `/x/search` finché una misura non dice altro.
- Da valutare eseguendolo, come metodo da riscrivere: il risolutore delle rotte di Express e Hono di GitNexus, che segue il valore dei router nell'albero (task 14j).

### 18. La chiave dello store come indice costante

Misura: README di `benchmarks/phazly-flow`. Aperto: una regola che nomina un metodo che ogni oggetto ha (`find`) prende `x[K].find()` su qualunque ricevente indicizzato (`LooseRuleTests` lo fissa come limite); `items()[0].find()` dà una lacuna in più; non misurata su un altro progetto.

### 18b. L'identità della dichiarazione dal motore alla vista

Prova: `tests/test_codebase_map_declaration_identity.py`. Aperto:

- le scritture che né il motore né lo snapshot vedono: `vars(self)[...]`, `__dict__`, `object.__setattr__`, `setattr` su una classe o su un modulo;
- un nome semplice tiene il `binding_id` lessicale anche quando il motore lo vede riscritto;
- un solo file Python senza documento nell'indice toglie ogni identità al linguaggio: quanto pesi su phazly non è misurato;
- la radice annidata dell'unità Python, che va con le radici degli import da `scan` (spec della pipeline, 8.11 passo 5);
- il cancello `assignment_targets_are_reads` oggi lo dichiara solo Python.

## Task non iniziati

- **15. La forma della risposta e ciò che il client ne legge.** Per una rotta unita a una chiamata, i campi che il gestore restituisce e quelli che il client legge dalla risposta: un campo letto e non restituito è una segnalazione con i due punti. Prima si valuta la soluzione pronta: lo schema OpenAPI dove il framework lo dà, i tipi dello strumento del linguaggio; non un lettore con espressioni regolari sul codice.
- **16. I contratti fra repository.** Una rotta offerta in un repository e chiamata in un altro è un collegamento fra i due sistemi. Dipende da come Daodan tiene più repository in un'analisi: prima si scrive questo nella spec.
- **19. I servizi in ingresso senza pacchetto.** Fermo: manca un dato ufficiale da cui partire. Su phazly lo stack riconosce dai segni tre servizi e nessuno dei due che servono (Cloud Scheduler che chiama una rotta con un token OIDC, le notifiche push di Google Play); collegarli chiederebbe una regola scritta a mano sulla forma del caso, che la regola d'oro esclude. Restano una lacuna con la causa. La via: un collegamento `possibile` che un modello conferma, come il generatore `ritorno` di `benchmarks/system-map/possible.py`. Vale 2 flussi su 38.

## Misure che oggi stanno solo qui

Da portare nel README del loro benchmark; fino ad allora questa è la loro sola copia.

- **Lettore statico dei controlli, su un progetto reale, 22 novembre 2026:** scarta 919 eventi legati a un componente e tiene 235 controlli. È il motivo per cui l'esplorazione viene prima delle correzioni ai singoli lettori dei framework.
- **GitNexus 1.6.12 su phazly, 23 novembre 2026** (dal registro npm, su Modal con la rete chiusa durante l'analisi, senza wiki, embeddings né modelli): delle 70 chiamate al wrapper del progetto attorno a `fetch` ne trova 0, e 0 delle 54 chiamate che le regole già coprono; le 115 rotte FastAPI le trova con metodo e gestore giusti, ma l'unione chiamata→rotta del suo grafo dà 0 consumatori. Lo strato dei contratti fra servizi legge i `fetch` diretti: 6 collegamenti giusti su 7 siti, ma toglie l'host da un URL assoluto.
- **Rotte di Noir e Next.js come rotte offerte, su phazly, 23 novembre 2026** (Modal, stesso input prima e dopo, `benchmarks/phazly-flow/rules.json`): con la regola `offre` che il caso ha già, guadagno zero: 50 chiamate su 50 collegate prima e dopo, 14 flussi chiusi su 38 con i soli collegamenti certi (15 con i possibili) prima e dopo; le 3 offerte in più (112 → 115) sono `/health`, `/docs` e `/openapi.json`. Senza la regola `offre`: prima 0 collegate e 50 lacune «no handler», 10 flussi chiusi su 38; dopo 50 su 50 allo stesso gestore, 14 chiusi; 10 collegamenti campionati a mano, tutti corretti. Il valore è l'indipendenza dalla regola `offre` scritta da un modello, non nuovi flussi. La pre-mappa non è stata rigenerata: è il record registrato, con le 191 voci di Noir.
- **Identità della dichiarazione (18b), su phazly, 23 novembre 2026** (Modal, `benchmarks/phazly-flow/measure_links.py`, stessa analisi fresca e stesse regole; «senza» è lo stesso albero con la sola riga di `edge_view` che copia `binding_id` spenta, in una copia fuori dal repository): lacune dei collegamenti 226 → 219, chiavi di `mongo` 44 → 46, collegamenti `legge` 489 → 492 e `scrive` 507 → 511, frecce certe del riferimento 118 → 119; i flussi chiusi restano 16 su 38 (17 con i collegamenti possibili). Le lacune «receiver index is an attribute of self» restano.
