# Spring Boot: Actuator `mappings` senza servire HTTP

**Stato: eseguito su Modal il 23 e il 24 novembre 2026** (i file di `results/` sono dell'ultima esecuzione, il 24; rete bloccata, `maven:3.9-eclipse-temurin-17`: OpenJDK 17.0.20.1, Maven 3.9.16, 2 CPU, 4 GiB; Spring Boot 3.5.0 con spring-webmvc 6.2.7 e Tomcat 10.1.41, Spring Boot 2.7.18 con spring-webmvc 5.3.31). Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14f; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6. La sorgente `premap/spring.py`, la voce `spring` di `container_runner.TOOLS` e le risposte registrate **non esistono**: questa cartella è la misura.

Domanda: `mappings` di Actuator si ottiene senza aprire una porta, con che forma, e che cosa dà per metodi, percorsi, classe, metodo, descrittore, file e riga? Seconda domanda (24 novembre): su applicazioni vere, che cosa aggiunge a Noir? Vedi «Applicazioni vere».

| Cartella | Contenuto |
| --- | --- |
| `fixture/src/` | un'applicazione Spring MVC: `ItemController` (`GET`, `GET /{id}`, `POST`, `PUT`, `DELETE`, due overload di `search` distinti da un parametro, `GET`+`HEAD` in una mappatura, una mappatura con due percorsi, un gestore con annotazione, firma e corpo su più righe), `PageController` (una pagina e una classe annidata `Ping`), `Inherited` (un gestore scritto in una classe base generica e uno scritto su un'interfaccia), `Prod` (`@Profile("prod")`), `Routes` (una `RouterFunction`, senza metodo gestore), `Switches` (quattro cose che impediscono di caricarla o di terminarla, accese da una proprietà) |
| `fixture/poms/` | `boot3` (3.5.0 con Actuator), `boot27` (2.7.18 con Actuator), `plain` (3.5.0 senza Actuator); stessi sorgenti, Java 17 |
| `fixture/overlays/` | file messi sopra il progetto: cinque `application.properties` di progetti che configurano Actuator a modo loro, `props` (`server.port=8080`, `management.server.port=9001`, esposizione `health`), `closed` (`management.endpoints.enabled-by-default=false`), `access` (`management.endpoints.access.max-permitted=none`), `legacyoff` (`management.endpoint.mappings.enabled=false`), `accessoff` (`management.endpoint.mappings.access=none`); e `jpa` (pom con Spring Data JPA e il driver PostgreSQL, un'entità, un repository, un controller che lo usa). `props` e `closed` anche su 2.7.18 |
| `Launcher.java` | un file in modalità sorgente (`java -cp <classi>:<lib>/* Launcher.java <classe> <file> <modo> <stop> <come> [chiave=valore …]`): carica l'applicazione con `SpringApplication` e scrive in un file l'uscita di Spring. Modo `actuator`: il JSON del bean di `@Endpoint(id = "mappings")`; modo `handler-methods`: i gestori di ogni `RequestMappingHandlerMapping` (senza Actuator), come JSON con `methods` e `patterns` in array. Stop `started`: all'`ApplicationStartedEvent`, dopo il contesto e prima dei runner; `returned`: quando `run` ritorna; `aot`: all'`ApplicationPreparedEvent`, il contesto portato fin dove lo lascia `refreshForAotProcessing` (Spring Framework 6) e creati solo i bean che il modo chiede. Il JSON si serializza con Jackson 3 (`tools.jackson`, Spring Boot 4) o con Jackson 2. Come `args`: le proprietà sono argomenti `--chiave=valore`; `defaults`: `setDefaultProperties`. Solo riflessione: i pacchetti di Spring Boot cambiano fra le versioni |
| `harness.py` | un comando con il suo tempo, la memoria di picco, i socket che hanno ascoltato e di chi, i `java` rimasti: in comune a `modal_probe.py` e `modal_real.py` |
| `modal_probe.py` | costruisce l'immagine con la rete aperta (`mvn package` di ogni fixture, il jar scompattato con `jar xf`, e la sola ripresa di Daodan, `maven-dependency-plugin:3.8.1:go-offline`, in un repository a parte), poi esegue ogni sonda senza rete, in una copia; scrive `results/<sonda>.json` (e `javap.txt`) |
| `modal_real.py` | applicazioni vere pubbliche, a un commit fissato, scaricate mentre l'immagine si costruisce (rete aperta): il restore di Daodan, la costruzione, Noir 1.5.0, il lanciatore e le sue varianti, `javap`, i file lasciati; senza rete. Con `VARIANTS=fixture` Noir gira sulla fixture |
| `real_summary.py` | dalle risposte di `modal_real.py` e dai sorgenti ai commit fissati (scaricati sull'host come testo in una cartella fuori dal repository, mai eseguiti): rotte, file e riga con `place_check.py`, lacune, confronto con Noir; scrive `results/real/<nome>-summary.json` |
| `place_check.py` | dai file registrati e dal parser di Daodan (tree-sitter, in sola lettura sul testo) alla riga di ogni gestore: la verifica del disegno per file e riga, non una sorgente |
| `results/` | l'uscita di ogni sonda di `modal_probe.py`, tutta dalla stessa esecuzione (l'ultima di nove: le altre hanno corretto la sonda), salvo `aot-jpa.json` e `aot-jpa-no-open-in-view.json`, rifatti con `VARIANTS` |
| `results/real/` | le risposte delle applicazioni vere (`<nome>-real.json`, `<nome>-cold.json`, `<nome>-restore.json`, `<nome>-javap-<modulo>.txt`, `<nome>-summary.json`) e di Noir sulla fixture (`fixture-noir.json`, `fixture-summary.json`). Delle applicazioni si conservano gli indirizzi, i commit, le rotte, i numeri e, dei comandi che falliscono, la coda dell'uscita; i `javap` sono ridotti ai metodi che le rotte nominano (nome, descrittore, prima riga) |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_probe.py
VARIANTS=actuator-boot3,javap …   (una scelta di PROBES, PIPELINES, EXTRA; con VARIANTS la costruzione a freddo non gira)
python -I benchmarks/spring-actuator-mappings/place_check.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_real.py   (VARIANTS=fixture: Noir sulla fixture)
python -I benchmarks/spring-actuator-mappings/real_summary.py <cartella con petclinic/, ruoyi/, microservices/ ai commit fissati>
```

## Risultati

Ogni riga dice la sonda (`results/<sonda>.json`). I secondi sono dall'avvio di `timeout … java` alla fine; la memoria è il picco di `wait4` (RSS). La stessa fixture è andata, fra le nove esecuzioni, da 2,4 a 6,2 s: Modal varia di un secondo e più, e i numeri di sotto sono dell'ultima (2,4-3,7 s per un lancio).

### 1. Senza aprire una porta

| Misura | Risultato | Sonda |
| --- | --- | --- |
| Il JSON si ottiene con `server.port=-1`? | **Sì**, senza una richiesta HTTP: il bean dell'endpoint si chiama in-process. Tomcat scrive `started on port -1`, il contesto ha il `DispatcherServlet`; 9.528 byte di JSON per 3.5.0 (8.869 per 2.7.18) | `actuator-boot3`, `actuator-boot27` |
| Si serve HTTP? | **No.** Con `server.port=0` (controllo positivo) una richiesta `GET /actuator/mappings` sul socket riceve `HTTP/1.1 200`. Con `-1` la richiesta fatta nel momento in cui il socket compare (sondaggio ogni 2 ms): la connessione **si completa** (il kernel la mette in coda), nessuno risponde, e alla chiusura del socket è reimpostata (`ConnectionResetError`): nessuna risposta HTTP in 6 prove su 6. Dimostrato per queste richieste, non per ogni modo di chiamare quel socket | `poke-port0`, `poke-minus1`, `poke-repeat` |
| Resta un socket in ascolto? | **Per qualche decina di ms** (da 10 a 37, mediana 21, risoluzione 10 ms; 2 ms nelle sonde con la connessione). Alla fine dell'avvio un socket `LISTEN` compare su una porta casuale, su tutti gli indirizzi, del processo `java`, e sparisce (51 casi; con `server.port=0` resta fino all'uscita). Dal codice di Spring Boot 3.5.0 (letto, non eseguito a parte): `TomcatServletWebServerFactory.customizeConnector` fa `Math.max(getPort(), 0)` (porta 0, casuale), `new TomcatWebServer(tomcat, getPort() >= 0, …)` dà `autoStart` falso, e `TomcatWebServer.start` rimette il connettore nel servizio e ne ferma il protocollo; il socket che compare e sparisce è quello (inferito dal codice e dalla misura). «Senza aprire una porta» è vero per il servizio, non per quei 30 ms | tutte; `repeat-boot3` (5 su 5) |
| Con `server.address=127.0.0.1` | il socket è `::ffff:127.0.0.1` (solo loopback) | `loopback` |
| La configurazione del progetto vince? | **Con `setDefaultProperties` no** (la precedenza più bassa, `docs.spring.io` «Externalized Configuration»: 1 le proprietà predefinite, 3 `application.properties`, 11 gli argomenti): `application.properties` con `server.port=8080` e `management.server.port=9001` apre le due porte (8080 e 9001, fino all'uscita) e l'esposizione `health` toglie il bean (exit 2, «no bean of an endpoint with the id mappings»). **Con argomenti `--chiave=valore`** `server.port` e l'esposizione vincono, ma `management.server.port=9001` apre ancora un secondo server vero (9001, fino all'uscita): serve `--management.server.port=-1`, e allora resta il solo lampo | `props-defaults`, `props-args`, `props-args-management-off` |
| `management.server.port=-1` toglie anche le righe di Actuator | `/actuator` e `/actuator/mappings` non compaiono: 7.868 byte e 19 righe per 3.5.0, 7.261 per 2.7.18 | `modern-boot3`, `full-boot27` |

**Quali proprietà accendono il bean** (le altre, `server.port=-1`, `management.server.port=-1`, `management.endpoints.web.exposure.include=mappings`, `spring.main.banner-mode=off`, valgono ovunque). Spring Boot 3.4 ha sostituito `enabled` con `access`, e **rifiuta le due insieme** per lo stesso endpoint (`MutuallyExclusiveConfigurationPropertiesException`, l'applicazione non parte). Quindi nessun insieme unico, e nemmeno uno per versione basta se il progetto imposta l'altra famiglia:

| Il progetto imposta | `enabled=true` (`LEGACY`) | `access=unrestricted` e `max-permitted=unrestricted` (`MODERN`) | `MODERN` e `enabled=` vuoto |
| --- | --- | --- | --- |
| niente, o solo porte ed esposizione (3.5.0) | | sì (`modern-boot3`, `modern-props`) | |
| `enabled-by-default=false` (3.5.0) | sì (`closed-args-enabled`) | sì (`modern-closed`) | |
| `max-permitted=none` (3.5.0) | **no**: il bean non c'è (`legacy-access`) | sì (`modern-access`) | |
| `mappings.enabled=false` (3.5.0) | sì (`legacy-legacyoff`) | **no**: `MutuallyExclusive…` (`modern-legacyoff`) | sì (`blank-legacyoff`) |
| `mappings.access=none` (3.5.0) | **no**: `MutuallyExclusive…` (`legacy-accessoff`) | sì (`modern-accessoff`) | |
| niente, porte ed esposizione, `enabled-by-default=false` (2.7.18) | sì (`legacy-boot27`, `legacy-props27`, `legacy-closed27`) | le due `access` sono ignorate | |
| i due insiemi insieme | 3.5.0: **no** in tutti e quattro i casi (`full-boot3`, `full-props`, `full-closed`, `full-access`); 2.7.18: sì (`full-boot27`, `full-props27`, `full-closed27`) | | |

Un valore **vuoto** toglie la proprietà del progetto dal conto: `blank-legacyoff` (`MODERN` più `--management.endpoint.mappings.enabled=` su un progetto con `enabled=false`) carica, e `blank-accessoff` (`enabled=true` più `--management.endpoint.mappings.access=` su un progetto con `access=none`) carica. L'insieme che regge ogni progetto provato di 3.5.0 è `MODERN` più `enabled=` vuoto (la riga con il vuoto è provata solo su `legacyoff`; le altre senza); per 2.7.18, `LEGACY`. Dove stia la soglia fra le due (3.4, dalla documentazione) e se 3.0-3.3 si comporta come 2.7: non provato. La versione si legge dal jar scompattato (`BOOT-INF/lib/spring-boot-<versione>.jar`).

### 2. La forma del JSON (Boot 3.5.0 e 2.7.18)

- Radice: `contexts.<id>.mappings` con `dispatcherServlets.<nome del servlet>[]`, `servletFilters[]`, `servlets[]`; il contesto ha `parentId` (`null`). Le chiavi sono le stesse in 2.7.18 e 3.5.0 salvo `details.handlerFunction` (solo 3.5.0). 3.5.0: 21 righe per la fixture (19 senza le due di Actuator), 2.7.18: 20.
- Ogni riga `{predicate, handler, details}`. `details.handlerMethod` è `{className, name, descriptor}` o `null`; `details.requestMappingConditions` ha `methods[]` (vuoto se non c'è un vincolo: `/error`), `patterns[]`, `params[]` (`{name, value, negated}`), `consumes[]`, `headers[]`, `produces[]`. Una mappatura con due percorsi è una riga con due `patterns`; `GET`+`HEAD` una riga con due `methods`.
- `className` è il nome canonico con i punti (`demo.PageController.Ping`, `demo.Inherited.Base`): il nome della classe che **scrive** il metodo, non quella del bean (per il gestore ereditato la stringa `handler` dice `demo.Inherited$BaseImpl#byId(int)`, la classe del bean; `className` dice la base). Il descrittore è quello della JVM, con i tipi cancellati: `(I)Ljava/lang/Object;` per `T byId(int)`. Un gestore scritto su un'interfaccia esce come il metodo della classe che lo realizza (`demo.Inherited.ApiImpl`).
- Due overload di `search` sono due righe che differiscono solo per `params` e `descriptor`.
- Il rumore del framework (6 righe su 21): `/actuator`, `/actuator/mappings`, due `/error`, `/webjars/**`, `/**`. Ciò che lo separa senza nominare Spring è che la classe non sta fra quelle del progetto (`javap` non la trova nelle classi del jar; lo snapshot non la dichiara).
- `RouterFunction`: in 3.5.0 una riga `(GET && /fn/hello)` con `handlerMethod: null` e `handlerFunction.className` = `demo.Routes$$Lambda$…/0x…` (nome di una classe generata a ogni esecuzione: nessun file, riga né metodo). **In 2.7.18 la riga non c'è**: le rotte funzionali mancano in silenzio.
- Un controller sotto `@Profile("prod")` non c'è (nessun profilo attivo): **le rotte che non nascono sono assenti, senza una parola**.
- `handler-methods` (senza Actuator, `RequestMappingHandlerMapping.getHandlerMethods()`), per ogni gestore `{bean, mapping, methods[], patterns[], declaringClass, beanType, name, descriptor, codeSource}`: le stesse rotte del progetto (15 insiemi metodi-percorso-nome-descrittore, uguali a quelli di Actuator; 16 gestori, 2 del framework), senza `RouterFunction` né righe di Actuator. Funziona anche con 2.7.18 (`RequestMappingInfo.getPatternValues()`). Il lanciatore usa `getBeansOfType` perché con Actuator il progetto può avere più bean di quel tipo.

### 3. Senza Actuator

`plain` (3.5.0 senza `spring-boot-starter-actuator`): il bean dell'endpoint non c'è, il lanciatore scrive `{"error": "no bean of an endpoint with the id mappings"}` ed esce 2 (2,6 s; il contesto si carica comunque). Il modo `handler-methods` sullo stesso progetto dà le 16 rotte annotate (`handler-methods-plain`, 2,7 s): il dato non richiede Actuator per i gestori a metodo, lo richiede per le rotte funzionali.

### 4. File e riga

- Actuator **non** li dà (`className`, `name`, `descriptor` e basta). Nemmeno `HandlerMethod`, che è un `java.lang.reflect.Method`.
- `javap -l -p -s` (JDK) li dà dal file di classe: `Compiled from "X.java"` (`SourceFile`, senza percorso), per metodo `descriptor:` (lo stesso testo di Actuator) e `LineNumberTable`. **La riga è la prima istruzione, non la dichiarazione**: per `spread`, annotazione alla riga 39, firma alla 41, corpo 43-47, il file di classe dà la **44**; per gli altri gestori, scritti su una riga o due, coincide con la dichiarazione. Il metodo astratto (`Api.apiPing`) non ha tabella: Actuator nomina il metodo concreto (`ApiImpl.apiPing`, riga 28). Un metodo ponte (`load(int)` che ritorna `Object`) ha la riga d'inizio della dichiarazione della classe.
- `place_check.py`, con il parser di Daodan sui sorgenti della fixture e `javap.txt`/`actuator-boot3.json` di questa esecuzione: dal nome canonico di Actuator si trova la classe nel report di `javap` (il nome binario con `$` come `.`, senza indovinare dove comincia una classe annidata), la riga del primo opcode dà il file e, fra le dichiarazioni dello snapshot con `qualified_name` uguale (`Inherited.Base.byId`), quella il cui intervallo la contiene: **tutte le 16 coppie metodo-percorso del progetto trovano una sola dichiarazione**, i due overload di `search` sono distinti dagli intervalli (righe 26 e 29), `spread` dà la riga 41 (nome) e l'intervallo 39-47, `/base/{id}` cade in `Inherited.java` (classe base), `/api/ping` nella classe che realizza l'interfaccia. Le 7 righe rimaste sono lacune con causa (tre non hanno gestore a metodo, quattro sono di classi che non stanno nel progetto). È il meccanismo di `dynamic/jvm.py` `place` (`SourceFile`, il nome, il primo rigo, la dichiarazione dello snapshot che lo contiene).
- Il testo di `javap` è il solo lettore a mano (righe di un rapporto di strumento, senza grammatica da dare a un parser; il motivo è nel docstring di `place_check.py`). Un lettore strutturato del file di classe (ASM, che Daodan già fissa per `dynamic/jvm_record`) è stato valutato e non provato: richiede un aiutante compilato nel container.

### 5. Un'applicazione che non si carica, una che non termina

| Caso | Risultato | Sonda |
| --- | --- | --- |
| Un bean che si connette a `db.invalid:5432` mentre nasce | exit 1 in 2,7 s, nessuna porta (il contesto cade prima del server), file `{"error": "<catena>"}` con la catena delle eccezioni (`BeanCreationException … <- UnknownHostException: db.invalid`); lo stack sta sullo standard output | `needs-database` |
| lo stesso con `spring.main.lazy-initialization=true` | si carica, **le stesse 14 rotte del progetto** (stesso insieme di predicati) | `needs-database-lazy` |
| Spring Data JPA + PostgreSQL, database non raggiungibile | **cade in tutte e quattro le combinazioni** (eager, lazy, `spring.jpa.open-in-view=false`, lazy con `open-in-view=false`): `entityManagerFactory` nasce durante il refresh anche con l'inizializzazione pigra (`HikariPool-1 - Starting`, poi `Unable to determine Dialect without JDBC metadata`), exit 1 in 5,2-5,4 s. Il lanciatore scrive la catena fino a `HibernateException`; che cosa chiede l'`entityManagerFactory` non è isolato | `jpa-eager`, `jpa-lazy`, `jpa-no-open-in-view`, `jpa-lazy-no-open-in-view` |
| Un `CommandLineRunner` che non ritorna, stop all'`ApplicationStartedEvent` | JSON scritto, exit 0 in 3,6 s: il runner non è mai chiamato | `never-ends-started` |
| lo stesso, stop quando `run` ritorna | exit **124** a 20,1 s, nessun file; il `SIGTERM` basta (il gancio di chiusura gira) | `never-ends-returned` |
| Un bean che non finisce in `afterPropertiesSet` (durante il refresh) | il `SIGTERM` a 20 s non fa nulla, il `SIGKILL` a +10 s: `timeout` stesso muore (`-9`, 137 per una shell) a 30,0 s, nessun file, un `java` defunto. Perché il `SIGTERM` non basta (si presume: il gancio di chiusura aspetta il blocco che il refresh tiene) non è isolato | `never-builds` |
| Un bean che non lascia chiudere il contesto (`DisposableBean.destroy`) | JSON scritto a 2,5 s, poi la chiusura resta appesa: `-9` a 25,0 s. **Il file c'è ed è intero: il segnale è il file, non il codice di uscita** | `never-closes` |

| **`stop=aot`**: il contesto all'`ApplicationPreparedEvent`, `refreshForAotProcessing`, creato solo il gestore delle mappature | `aot-boot3`: exit 0 in 2,6 s, gli stessi 16 gestori (14 del progetto) del contesto intero. Con un bean che si connette al database mentre nasce (`aot-needs-database`) o che non finisce (`aot-never-builds`): **exit 0**, lo stesso insieme, perché quel bean non viene mai creato. Spring Data JPA (`aot-jpa`): exit 1, il configuratore `open-in-view` chiede l'`EntityManagerFactory`, cioè il database; con `spring.jpa.open-in-view=false` (`aot-jpa-no-open-in-view`): **exit 0, 17 gestori fra cui `/people`**, dove lo stesso valore non salvava l'avvio intero (`jpa-no-open-in-view`, exit 1). 2.7.18 (`aot-boot27`): exit 1, `ClassNotFoundException: org.springframework.aot.hint.RuntimeHints` (Spring 5.3 non ha l'AOT) | `aot-boot3`, `aot-needs-database`, `aot-never-builds`, `aot-jpa`, `aot-jpa-no-open-in-view`, `aot-boot27` |

La memoria dei due casi `-9` (75 MB) è quella di `timeout` ucciso, non della JVM.

### 6. Il comando e il restore senza rete

| Misura | Risultato | Sonda |
| --- | --- | --- |
| `mvn -o -B -q -DskipTests package` col repository di `~/.m2` della costruzione | exit 0, 3,4 s (530 MB); poi `jar xf` 0,2 s; poi il lanciatore sul jar scompattato (`BOOT-INF/classes:BOOT-INF/lib/*`, classe da `Start-Class` del manifest) 2,7 s | `pipeline-m2` |
| con `target/` già presente (la preparazione l'ha lasciato) | exit 0, 3,1 s; il lanciatore dà lo stesso JSON | `pipeline-m2-keep-target` |
| **Solo il restore di Daodan** (`mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline`, la riga di `preparation.RESTORES["maven"]`) in un repository a parte, poi `mvn -o package` | exit 0 per 3.5.0 (3,2 s) e per 2.7.18 (3,3 s): `go-offline` basta a costruire e ripacchettizzare il jar senza rete **per queste fixture**; il lanciatore poi dà le rotte (2,8 s e 2,4 s). Su tre applicazioni vere non basta: vedi «Applicazioni vere». Il repository pesa 88 MB (3.5.0) e 85 MB (2.7.18), il `~/.m2` della costruzione di tutte le fixture 132 MB | `pipeline-goffline`, `pipeline-goffline27` |
| `clean` | `mvn -o clean package` sul `~/.m2` della costruzione: **exit 1**, `maven-clean-plugin:3.4.1` non scaricato (`PluginResolutionException`); sul repository di `go-offline`: **exit 0** (3,4 s): il restore di Daodan ha già il plugin | `clean-package-m2`, `clean-package-goffline` |
| Un comando più leggero: nessun jar | `mvn -o compile dependency:build-classpath` (3,1 s), il lanciatore su `target/classes` e il classpath scritto, classe principale **data a mano** (`demo.DemoApplication`): stesso JSON in 2,8 s. La classe principale senza il manifesto verrebbe dallo snapshot (non misurato) | `pipeline-compile` |
| Con la rete e il repository vuoto (la preparazione) | `go-offline` 24,3 s, 544 MB; poi `package` senza rete 3,9 s | `cold-build` |

Che `~/.m2` e `target/` sopravvivano fra la preparazione (con le registry) e l'esecuzione (senza rete) **nel motore di Daodan** non è misurato: la sonda imita lo schema con l'immagine di Modal (la rete aperta alla costruzione) e una funzione con `block_network` (l'esecuzione), come ogni sonda sorella di `benchmarks/` (react-router, nuxt, flask…: eseguono i comandi che la sorgente darebbe, non `container.run_commands`, che vuole il motore Docker di Daodan, e un container dentro Modal non c'è). Dal codice: `container.run_in_container` con una preparazione mette `HOME` in `STATE` (`/daodan/state/home`) e monta `WORKDIR` e `STATE` come volumi che l'esecuzione vede; è lo schema su cui `dynamic/jvm.py` già costruisce (preparazione con le registry, esecuzione con `mvn -o`). Letto dal codice, non provato.

### 7. Tempo e memoria

| | Secondi | Memoria (RSS) |
| --- | --- | --- |
| lanciatore, 3.5.0, 5 esecuzioni senza sondaggio dei socket | 2,74 / 2,74 / 2,80 / 2,89 / 3,02 (media 2,84) | 508-524 MB |
| lo stesso con il sondaggio ogni 10 ms | 2,69-2,74 (media 2,72) | 503-520 MB |
| lanciatore, 2.7.18 | 2,91 | 459 MB |
| `-Xmx256m` e `-Xmx128m` (3.5.0) | 2,72 e 2,64: il JSON è lo stesso | 524 e 534 MB: il picco non segue lo heap (probabilmente la compilazione in memoria del lanciatore, il metaspace e il codice compilato: non isolato) |
| fixture JPA (che cade) | 5,2-5,4 | 583-604 MB |
| `mvn -o package` | 3,1-3,4 | 530-561 MB |
| `javap` su tutte le classi della fixture | 0,2 | 244 MB |

La fixture ha una dozzina di controller: un'applicazione vera avvia più lentamente (nessuna misura); il limite del lanciatore nelle sonde è 120 s (20 s e 15 s per i casi che non finiscono).

## Applicazioni vere

Misurato il 24 novembre 2026 (`modal_real.py`, `real_summary.py`, `results/real/`). **Corregge il disegno della prima parte**: lì la preparazione era il restore di Daodan e poi `mvn -o package`; su tre applicazioni vere quel passo non costruisce (vedi sotto), la preparazione costruisce con la rete. Domanda: su applicazioni Spring Boot vere, il lanciatore costruisce, carica, dà le rotte con file e riga, e che cosa aggiunge a Noir (1.5.0, quello di `premap/noir.py`, sha256 verificato)? Le applicazioni sono scaricate al commit fissato mentre l'immagine si costruisce (rete aperta) e il resto gira con la rete bloccata; i sorgenti non sono nel repository (solo indirizzo, commit, licenza e le uscite). Le licenze sono quelle dei file `LICENSE` al commit: tutte e tre permettono di eseguire il codice e di pubblicare misure su di esso (Apache-2.0, MIT).

| | (a) petclinic | (b) RuoYi | (c) petclinic-microservices |
| --- | --- | --- | --- |
| repository | `spring-projects/spring-petclinic` | `yangzongzhuan/RuoYi` | `spring-petclinic/spring-petclinic-microservices` |
| commit | `500158f732419217507c7656904b8e6aa1bcc0d6` | `d6708994364bfbb472c96380d6129e24303b3228` | `935ba9320a6514a6c31ff1316c29281b2191dcd3` |
| licenza | Apache-2.0 (`LICENSE.txt`) | MIT (`LICENSE`) | Apache-2.0 (`LICENSE`) |
| Spring Boot, Java | 4.1.0, 17 | 4.1.2, 17 | 4.1.2, 17 |
| Maven | un modulo | 6 moduli, l'applicazione è `ruoyi-admin` | 8 moduli, tutti applicazioni (Spring Cloud) |
| file Java | 50 | 287 | 64 |
| perché | H2 in memoria di default | MySQL a `localhost:3306` all'avvio, nessun default in memoria | più moduli, tre con WebFlux (Netty) |

### Restore e costruzione

Il restore di Daodan (`mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline`, in un repository vuoto, con la rete), poi `mvn -o -B -q -DskipTests package` sullo stesso repository senza rete; e la costruzione stessa con la rete (`mvn package`, la preparazione di `dynamic/jvm.py`), poi di nuovo `mvn -o package` sul suo repository.

| | (a) petclinic | (b) RuoYi | (c) microservices |
| --- | --- | --- | --- |
| `go-offline` | exit 0, 30,5 s, 598 MB; repository 241 MB | **exit 1**, 54 s (in altre esecuzioni 159, 771 e 1.506 s), 582 MB | exit 0, 103,7 s, 643 MB; repository 484 MB |
| `mvn -o package` dopo `go-offline` | **exit 1** in 2,8 s: 9 artefatti mancanti (`commons-logging:1.3.6`, `byte-buddy:1.18.10`, `slf4j-api:2.0.18`, `jaxb-runtime:4.0.9`, `aspectjweaver:1.9.25.1`…); il repository ha altre versioni di alcuni (di `commons-logging` fino alla 1.3.5) | **exit 1**: 14 mancanti (`fastjson2`, `jackson-databind:2.21.7`, `pagehelper-spring-boot-starter`…), spesso nessuna versione | **exit 1** in 3,8 s: 3 mancanti (`spring-boot-jackson2:4.1.2`: c'è la 4.0.9; `spring-security-crypto:7.1.2`; `commons-codec:1.21.0`) |
| `mvn package` con la rete dopo `go-offline` | exit 0, 14,2 s, 1.015 MB | exit 0, 18,4 s, 1.356 MB | exit 0, 15,3 s, 1.501 MB |
| `mvn package` con la rete, repository vuoto | exit 0, 32,4 s, 853 MB | exit 0, 19,3 s, 1.501 MB | exit 0, 59,9 s, 1.448 MB |
| `mvn -o package` dopo quella costruzione | **exit 0**, 7,9 s, 848 MB | exit 0, 11,0 s, 1.263 MB | exit 0, 15,1 s, 1.481 MB |
| lasciato dalla costruzione fuori da `target/` | niente | niente | niente |

Perché `go-offline` non regge in RuoYi: `jaxb-api:pom:2.3.0-b161121.1438`, di un repository `http://maven.java.net` che Maven blocca (`maven-default-http-blocker`); la costruzione non ne ha bisogno. Su tre applicazioni vere su tre, **il restore di Daodan più `mvn -o package` non costruisce**; costruisce la preparazione che fa `mvn package` con la rete (e i suoi jar restano in `target/`).

Che cosa lo discrimina (`results/real/<nome>-restore.json`, repository vuoto per ogni variante, poi `mvn -o package` sullo stesso): è la versione fissata del plugin.

| Restore | (a) petclinic | (c) microservices |
| --- | --- | --- |
| `dependency:go-offline` fissato a 3.8.1 (la riga di Daodan) | 9 mancanti, exit 1 | 3 mancanti, exit 1 |
| `dependency:go-offline` senza fissare la versione (quella che Maven risolve; non registrata) | **0 mancanti, exit 0** (25,4 s il restore, 9,0 s la costruzione) | 1 mancante, exit 1 |
| `dependency:resolve` e `dependency:resolve-plugins` | **0 mancanti, exit 0** (28,8 s, 9,6 s) | **0 mancanti, exit 0** (42,0 s, 13,3 s) |

La riga è in `preparation.RESTORES["maven"]` (un file condiviso: non toccato); la causa fra il plugin fissato e il resto non è isolata oltre questo, e RuoYi non è stato provato con le due varianti. Una preparazione che costruisce con la rete non dipende da nessuna delle due.

### Il lanciatore

Sui jar costruiti dalla preparazione (`Start-Class` e `Spring-Boot-Version` dal manifesto), con le proprietà del lanciatore per la versione (4.1: `MODERN` più `enabled=` vuoto), `server.port=-1`, nessuna porta fuori dal loopback.

| | (a) petclinic | (b) RuoYi | (c) microservices (8 moduli) |
| --- | --- | --- | --- |
| carica | sì: Actuator, exit 0, 6,9 s, 809 MB, 21 righe | **no**: exit 1 in 6,1 s, 613 MB | 5 moduli sì con `server.port=-1` (4 con Actuator, 1 senza: `config-server` esce 2 e il ripiego `handler-methods` dà le righe); i 3 con WebFlux **no** con `-1` (`IllegalArgumentException: port out of range:-1`, Netty): sì con `server.port=0` e `server.address=127.0.0.1` (una porta vera sul loopback, fino all'uscita) |
| righe | 21: 17 del progetto, 2 del framework (`/error`), 2 senza metodo gestore (le risorse statiche) | con un MariaDB locale e `handler-methods`: 311 gestori (303 del progetto, 8 del framework) | customers 12, vets 5, visits 7, api-gateway 6, genai 3; `discovery-server` 6 (Eureka), `config-server` 23 e `admin-server` 23 (tutte del framework: Spring Cloud Config, Spring Boot Admin) |
| rotte del progetto | **17** | **304** (coppie metodo-percorso) | **16**: customers 8, visits 3, api-gateway 3, vets 1, genai 1 |
| con file e riga unici (`place_check.py`) | **17 su 17** | **304 su 304** | **16 su 16** |
| lacune | nessuna per le rotte del progetto; le 2 righe senza metodo sono `ResourceHttpRequestHandler` | nessuna (sul contesto che si carica con il servizio) | nessuna per le rotte del progetto; righe senza metodo: `GET /**` del gateway (una lambda che serve `index.html`), la pagina di benvenuto, le risorse |
| `stop=aot` (il contesto fino a `refreshForAotProcessing`, solo la mappatura) | exit 0, 5,7 s, 702 MB, 19 righe (le 21 meno le due di Actuator) | **exit 1**, con e senza il servizio | exit 0 nei 5 moduli con Tomcat (23, 10, 4, 3, 5 righe: Actuator meno le due sue); `admin-server` e `api-gateway` (Netty): `ClassNotFoundException` della mappatura servlet; `genai-service` (Netty): exit 0 e 0 righe |
| lasciato nella copia del progetto fuori da `target/` | niente (0 file nuovi, 0 cambiati; 281 file in `target/`) | niente (627 in `target/`); fuori dalla copia: i dati di MariaDB in `/var/lib/mysql`, e RuoYi configura i log in `/home/ruoyi/logs` (logback) e i caricamenti in `D:/ruoyi/uploadPath`: non misurato che cosa vi resta | niente (2.246 in `target/`) |
| `SpringApplicationAotProcessor` (il comando di `spring-boot:process-aot`) | exit 0, 5,7 s, 213 file generati, **nessuno dei 13 percorsi delle rotte vi compare** fra virgolette | exit 1 | exit 1 in tutti e 8 (`RefreshScope` di Spring Cloud non generabile) |

Le 4.1.x hanno lo stesso JSON delle 3.5: le chiavi di `dispatcherServlets` e di `dispatcherHandlers` (WebFlux) lette dallo stesso codice; Jackson è la 3 (`tools.jackson`), il lanciatore sceglie.

### Noir sulle stesse applicazioni

`noir scan <progetto> -f json --no-log` (la riga di `premap/noir.py`) sui sorgenti, prima della costruzione.

| | (a) petclinic | (b) RuoYi | (c) microservices |
| --- | --- | --- | --- |
| tempo, memoria | 0,7 s, 151 MB | 1,7 s, 164 MB | 1,1 s, 151 MB |
| endpoint | 45 | 508 | 73 |
| con un gestore in un file Java | **17** | **304** | **16** |
| senza gestore, in un file di codice Java | 0 | **2**: `GET /profile/**` e `GET /swagger-ui/**`, in `ResourcesConfig.java` (registrazioni di risorse, `addResourceHandlers`) | 0 |
| senza gestore, altrove | 28: 14 `GET /actuator/...` dedotti dal `pom.xml`, 14 file statici | 202: 199 file statici, 2 dal `pom.xml` (Swagger), 1 `messages.properties` | 57: 10 `GET /actuator/...` dal `pom.xml`, 4 dal `application.yml` (le rotte di Spring Cloud Gateway), 43 file statici |
| rotte dei due | **17** | **304** | **16** |
| solo del lanciatore (con gestore Java) | 0 | 0 | 0 |
| solo di Noir (con gestore Java) | 0 | 0 | 0 |
| stesso file e stessa riga | **17 su 17** | **304 su 304** | **16 su 16** |

Per le rotte con un gestore in un file Java, su tre applicazioni vere Noir e Spring dicono **la stessa cosa, 337 su 337, fino alla riga**. Attenzione a come si arriva a 337: 304 sono di RuoYi e le dà il lanciatore **solo con il MariaDB locale** e l'URL JDBC dato a mano; senza il servizio il confronto è su **33 rotte** (17 e 16) e RuoYi dà 0. Quello che c'è da una parte sola non è una rotta con un gestore (a parte le 2 registrazioni di risorse di RuoYi, che `handler-methods` non elenca): Noir ha le dichiarazioni dei file (statici, `pom.xml`, `application.yml`), il lanciatore le righe del framework e le rotte funzionali senza metodo.

Sulla fixture (`modal_real.py` con `VARIANTS=fixture`, `results/real/fixture-summary.json`), costruita per i casi difficili: 15 rotte (metodo, percorso) del lanciatore, 17 di Noir; **in comune 15**, e per **14** Noir dà lo stesso gestore con lo stesso file e la stessa riga (due overload di `search`, un alias con due percorsi, `GET`+`HEAD`, la classe annidata, il gestore dell'interfaccia, `spread` con la firma su più righe); per la quindicesima, `GET /base/{id}`, il gestore scritto in una classe base generica, Noir ha la rotta e **nessun gestore**. Solo di Noir: `GET /fn/hello` (la `RouterFunction`, senza gestore) e `GET /prod-only` (un controller sotto `@Profile("prod")` che non è attivo: una rotta che a runtime non c'è).

### (b): perché non si carica, e che cosa lo aggira

Il guasto, per esteso: il bean `masterDataSource` di `DruidConfig` (di RuoYi, non un'autoconfigurazione) costruisce un pool Druid con `initialSize` 5 e si connette a `localhost:3306` mentre nasce: `CommunicationsException: Communications link failure ... Connection refused`. Il bean è la radice di una catena: `dynamicDataSource` ← `sqlSessionFactory` ← i mapper MyBatis ← `sysMenuServiceImpl` ← `userRealm` ← `securityManager` ← `authorizationAttributeSourceAdvisor` (Shiro). L'ultimo è un *advisor*: l'auto-proxy di Spring lo cerca prima di creare **qualsiasi** bean (`BeanPostProcessor before instantiation of bean failed` già su `messageSource`), quindi nessun bean si crea senza il database.

| Candidato | Ufficiale e documentato? | Risultato su RuoYi |
| --- | --- | --- |
| `spring.main.lazy-initialization=true` | sì, proprietà di Spring Boot | exit 1, la stessa catena (l'advisor non è pigro) |
| `spring.autoconfigure.exclude` con le autoconfigurazioni dei negozi (DataSource, MyBatis, Quartz, Redis, PageHelper; pacchetti di Boot 3 e 4) | sì, proprietà documentata; ma i nomi sono per tecnologia | exit 1: i bean che cadono sono `@Configuration` del progetto (`DruidConfig`, `MyBatisConfig`, `ShiroConfig`), non si escludono così |
| `refreshForAotProcessing` e solo la mappatura (`stop=aot`) | l'API è di Spring Framework 6 e documentata per l'AOT; l'uso per le rotte è nostro | exit 1: la catena dell'advisor si crea già dentro il refresh AOT; **con il database presente (MariaDB) cade lo stesso** (non isolato perché); nella fixture invece regge (bean che si connette al database, bean che non finisce, JPA con `open-in-view=false`) e nelle 5 applicazioni servlet che si caricano dà le stesse rotte |
| `SpringApplicationAotProcessor` / `spring-boot:process-aot` | sì, documentato | exit 1 su RuoYi; su petclinic exit 0 ma l'uscita non contiene i percorsi (0 su 13): non è una sorgente di rotte |
| la mappatura costruita dalle definizioni dei bean senza fare il refresh (un `RequestMappingHandlerMapping` montato a mano su un contesto non attivo) | sono classi di Spring, il montaggio no | **non misurata** (`refreshForAotProcessing` è un refresh parziale, non questo) |
| una fetta web (`@WebMvcTest`) | sì, documentata | **non misurata**: serve una classe di test compilata ed eseguita, `spring-boot-starter-test` e un `@MockitoBean` per ogni dipendenza mancante (uno stub per progetto) |
| il servizio, in locale (MariaDB nel container, i due `.sql` del progetto, l'URL senza SSL) | non è un meccanismo di Spring: è la dipendenza del progetto | **sì**: 311 gestori, 304 rotte, 304 con file e riga (RuoYi non ha Actuator: il modo `handler-methods`) |

Nessun meccanismo di Spring, né pigro né AOT né di esclusione, porta le rotte di RuoYi senza il suo database. Il servizio sì: Daodan ha codice per i servizi dei `compose` del progetto (`premap/compose.py`, `service_registry.py`, `container.start_pod`); non è provato qui.

### Verdetto

**Non vale la pena scrivere questa sorgente come fonte delle rotte**, sulle misure:

- Rotte, file, riga: su 3 applicazioni vere (337 rotte con un gestore Java) Noir e il lanciatore coincidono in **337 su 337**, fino alla riga; nessuna rotta con gestore Java è solo dell'uno o dell'altro. Ma 304 di quelle 337 sono di RuoYi e il lanciatore le ha solo con un database locale e un URL dato a mano: **senza il servizio, 33 rotte confrontabili e RuoYi 0**; il confronto onesto è 33 su 33 più un'applicazione che il lanciatore non vede e Noir sì (304 rotte). Sulla fixture costruita per i casi difficili Noir manca un gestore su 15 (la classe base generica) e dà in più una rotta di un profilo spento e una funzionale: il lanciatore aggiunge, su 3 applicazioni + fixture, **un** gestore.
- Ciò che costa: la preparazione deve **costruire** con la rete (14-18 s e 1,0-1,5 GB) o restaurare diversamente (il restore di Daodan più `mvn -o package` non costruisce su 3 su 3; `dependency:resolve` più `resolve-plugins` ha dato 0 mancanti su petclinic e microservices, RuoYi non provato), il lancio 6,9-18,5 s e 543-882 MB per modulo, le proprietà cambiano con la versione (3.4: `enabled` o `access`, mai insieme), 3 moduli su 10 non partono con `server.port=-1` (Netty), 1 su 10 non si carica senza il suo servizio e le sue rotte restano di Noir.
- Il lanciatore ha un valore che Noir non ha: le rotte come Spring le crea davvero (profili, condizioni) e le funzionali; nessuna delle tre applicazioni lo esercita (nessun controller sotto un profilo; le rotte funzionali del gateway restano senza file né riga), la fixture sì con una rotta.

Resta aperto: più applicazioni (tutte e tre sono Boot 4, con controller annotati e senza Kotlin né Gradle), un'applicazione con costanti, meta-annotazioni o segnaposto nei percorsi (dove Noir potrebbe sbagliare: non misurato), un `main` che personalizza `SpringApplication`.

## Non coperto (aperto)

Gradle (`bootJar`, il restore `gradle dependencies`) e Kotlin (`suspend`, classi `FooKt`: il descrittore ha `Continuation`), Spring Boot 3.0-3.4 (la soglia delle proprietà), un JDK 21 o 25 sull'immagine, profili attivi, variabili d'ambiente e segnaposto `${…}` senza valore, `server.servlet.context-path` e `spring.mvc.servlet.path` nei `patterns`, un `main` che personalizza `SpringApplication` (profili, tipo di applicazione, ascoltatori: il lanciatore ne costruisce uno suo e non lo esegue; nessuna delle tre applicazioni vere ne ha uno), un `package` che lancia i plugin del progetto (frontend npm, generatori), classi compilate senza `LineNumberTable` (`-g:none`), il motore di Daodan (volumi, `HOME`), il restore di RuoYi con le varianti del plugin, applicazioni con costanti, meta-annotazioni o segnaposto nei percorsi (dove Noir potrebbe sbagliare).
