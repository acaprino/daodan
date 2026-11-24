# Spring Boot: Actuator `mappings` senza servire HTTP

**Stato:** Scartato come fonte delle rotte: la sorgente non si scrive. Su tre applicazioni vere Noir e Spring danno le stesse rotte con gestore Java, stesso file e stessa riga (337 su 337), e il lanciatore costa una costruzione con la rete, cambia proprietà con la versione e non carica un'applicazione senza il suo database. Nessuna sorgente della pre-mappa (`premap/spring.py` non esiste), nessuna voce `spring` in `container_runner.TOOLS`: questa cartella è la misura. Nel prodotto le rotte di Spring sono quelle di Noir. Aperto: il restore Maven di Daodan non basta a costruire le tre applicazioni («Aperto»).

## Domanda

`mappings` di Actuator si ottiene senza aprire una porta, con che forma, e che cosa dà per metodi, percorsi, classe, metodo, descrittore, file e riga? Su applicazioni vere, che cosa aggiunge a Noir? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14f del piano).

## Strumento ufficiale provato

Il bean di `@Endpoint(id = "mappings")` di Spring Boot Actuator, chiamato in-process da `Launcher.java` (`SpringApplication`, solo riflessione); senza Actuator, `RequestMappingHandlerMapping.getHandlerMethods()`; per file e riga `javap -l -p -s` del JDK. Spring Boot 3.5.0 (spring-webmvc 6.2.7, Tomcat 10.1.41) e 2.7.18 (spring-webmvc 5.3.31) sulla fixture, 4.1.0 e 4.1.2 sulle applicazioni vere; `maven:3.9-eclipse-temurin-17` (OpenJDK 17.0.20.1, Maven 3.9.16), 2 CPU, 4 GiB. Misurato su Modal il 24 novembre 2026, rete bloccata.

## Parametri

- **Fixture** (`fixture/src/`): un'applicazione Spring MVC con overload, `GET`+`HEAD`, due percorsi in una mappatura, una classe annidata, un gestore in una classe base generica e uno su un'interfaccia, `@Profile("prod")`, una `RouterFunction`, e `Switches` (quattro cose che impediscono di caricarla o di terminarla). `fixture/poms/`: `boot3`, `boot27`, `plain` (senza Actuator). `fixture/overlays/`: `application.properties` di progetti che configurano Actuator a modo loro, e `jpa`.
- **Lanciatore** (`Launcher.java`): modo `actuator` o `handler-methods`; stop `started` (all'`ApplicationStartedEvent`), `returned`, `aot` (fino a `refreshForAotProcessing`, creati solo i bean che il modo chiede); proprietà come argomenti `--chiave=valore` (`args`) o `setDefaultProperties` (`defaults`).
- **File:** `harness.py` (tempo, memoria, socket in ascolto), `modal_probe.py`, `modal_real.py`, `real_summary.py`, `place_check.py` (dal nome di Actuator e da `javap` alla dichiarazione dello snapshot), `results/<sonda>.json`, `results/real/`.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_probe.py
VARIANTS=actuator-boot3,javap …   (una scelta di PROBES, PIPELINES, EXTRA)
python -I benchmarks/spring-actuator-mappings/place_check.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/spring-actuator-mappings/modal_real.py   (VARIANTS=fixture: Noir sulla fixture)
python -I benchmarks/spring-actuator-mappings/real_summary.py <cartella con petclinic/, ruoyi/, microservices/ ai commit fissati>
```

## Risultato sulla fixture

Un lancio dura 2,4-3,7 s; il picco di memoria è 503-524 MB per 3.5.0 e 459 MB per 2.7.18. `mvn -o package` 3,1-3,4 s e 530-561 MB; `javap` su tutte le classi 0,2 s.

**Senza aprire una porta.**

| Misura | Risultato | Sonda |
| --- | --- | --- |
| Il JSON si ottiene con `server.port=-1`? | **Sì**, senza una richiesta HTTP: il bean dell'endpoint si chiama in-process. Tomcat scrive `started on port -1`, il contesto ha il `DispatcherServlet`; 9.528 byte di JSON per 3.5.0 (8.869 per 2.7.18) | `actuator-boot3`, `actuator-boot27` |
| Si serve HTTP? | **No.** Con `server.port=0` (controllo positivo) una richiesta `GET /actuator/mappings` sul socket riceve `HTTP/1.1 200`. Con `-1` la richiesta fatta nel momento in cui il socket compare (sondaggio ogni 2 ms): la connessione **si completa** (il kernel la mette in coda), nessuno risponde, e alla chiusura del socket è reimpostata (`ConnectionResetError`): nessuna risposta HTTP in 6 prove su 6. Dimostrato per queste richieste, non per ogni modo di chiamare quel socket | `poke-port0`, `poke-minus1`, `poke-repeat` |
| Resta un socket in ascolto? | **Per qualche decina di ms** (da 10 a 37, mediana 21, risoluzione 10 ms; 2 ms nelle sonde con la connessione). Alla fine dell'avvio un socket `LISTEN` compare su una porta casuale, su tutti gli indirizzi, del processo `java`, e sparisce (51 casi; con `server.port=0` resta fino all'uscita). Dal codice di Spring Boot 3.5.0 (letto, non eseguito a parte): `TomcatServletWebServerFactory.customizeConnector` fa `Math.max(getPort(), 0)` (porta 0, casuale), `new TomcatWebServer(tomcat, getPort() >= 0, …)` dà `autoStart` falso, e `TomcatWebServer.start` rimette il connettore nel servizio e ne ferma il protocollo; il socket che compare e sparisce è quello (inferito dal codice e dalla misura). «Senza aprire una porta» è vero per il servizio, non per quei 30 ms | tutte; `repeat-boot3` (5 su 5) |
| Con `server.address=127.0.0.1` | il socket è `::ffff:127.0.0.1` (solo loopback) | `loopback` |
| La configurazione del progetto vince? | **Con `setDefaultProperties` no** (la precedenza più bassa, `docs.spring.io` «Externalized Configuration»: 1 le proprietà predefinite, 3 `application.properties`, 11 gli argomenti): `application.properties` con `server.port=8080` e `management.server.port=9001` apre le due porte (8080 e 9001, fino all'uscita) e l'esposizione `health` toglie il bean (exit 2, «no bean of an endpoint with the id mappings»). **Con argomenti `--chiave=valore`** `server.port` e l'esposizione vincono, ma `management.server.port=9001` apre ancora un secondo server vero (9001, fino all'uscita): serve `--management.server.port=-1`, e allora resta il solo lampo | `props-defaults`, `props-args`, `props-args-management-off` |
| `management.server.port=-1` toglie anche le righe di Actuator | `/actuator` e `/actuator/mappings` non compaiono: 7.868 byte e 19 righe per 3.5.0, 7.261 per 2.7.18 | `modern-boot3`, `full-boot27` |

**Quali proprietà accendono il bean.** Spring Boot 3.4 ha sostituito `enabled` con `access` e rifiuta le due insieme per lo stesso endpoint (`MutuallyExclusiveConfigurationPropertiesException`): nessun insieme unico vale per ogni versione e ogni progetto.

| Il progetto imposta | `enabled=true` (`LEGACY`) | `access=unrestricted` e `max-permitted=unrestricted` (`MODERN`) | `MODERN` e `enabled=` vuoto |
| --- | --- | --- | --- |
| niente, o solo porte ed esposizione (3.5.0) | | sì (`modern-boot3`, `modern-props`) | |
| `enabled-by-default=false` (3.5.0) | sì (`closed-args-enabled`) | sì (`modern-closed`) | |
| `max-permitted=none` (3.5.0) | **no**: il bean non c'è (`legacy-access`) | sì (`modern-access`) | |
| `mappings.enabled=false` (3.5.0) | sì (`legacy-legacyoff`) | **no**: `MutuallyExclusive…` (`modern-legacyoff`) | sì (`blank-legacyoff`) |
| `mappings.access=none` (3.5.0) | **no**: `MutuallyExclusive…` (`legacy-accessoff`) | sì (`modern-accessoff`) | |
| niente, porte ed esposizione, `enabled-by-default=false` (2.7.18) | sì (`legacy-boot27`, `legacy-props27`, `legacy-closed27`) | le due `access` sono ignorate | |
| i due insiemi insieme | 3.5.0: **no** in tutti e quattro i casi (`full-boot3`, `full-props`, `full-closed`, `full-access`); 2.7.18: sì (`full-boot27`, `full-props27`, `full-closed27`) | | |

Un valore vuoto toglie la proprietà del progetto dal conto. L'insieme che regge ogni progetto provato di 3.5.0 è `MODERN` più `enabled=` vuoto; per 2.7.18 `LEGACY`. La soglia fra le due (3.4, dalla documentazione) e Spring Boot 3.0-3.3 non sono provati.

**La forma del JSON.**

- Radice `contexts.<id>.mappings` con `dispatcherServlets.<nome>[]`; ogni riga `{predicate, handler, details}`, con `details.handlerMethod` `{className, name, descriptor}` o `null` e `details.requestMappingConditions` (`methods[]`, `patterns[]`, `params[]`…). 21 righe per la fixture in 3.5.0, 6 del framework.
- `className` è la classe che scrive il metodo (la base, per un gestore ereditato), con i punti anche per le classi annidate; il descrittore è quello della JVM.
- Una `RouterFunction` in 3.5.0 è una riga con `handlerMethod: null` e una classe lambda generata; in 2.7.18 manca in silenzio. Un controller sotto un profilo non attivo è assente, senza una parola.
- Senza Actuator il bean non c'è (exit 2); `handler-methods` dà le stesse rotte annotate, senza le funzionali.

**File e riga.** Actuator non li dà. `javap` dà `SourceFile` e la `LineNumberTable`: la riga della prima istruzione, non della dichiarazione. `place_check.py` trova la classe nel report di `javap` e, fra le dichiarazioni dello snapshot con lo stesso `qualified_name`, quella il cui intervallo contiene la riga: tutte le 16 coppie metodo-percorso del progetto trovano una sola dichiarazione. È il meccanismo di `dynamic/jvm.py` `place`. Il testo di `javap` è l'unico lettore a mano (il motivo è nel docstring di `place_check.py`); ASM è valutato e non provato.

**Un'applicazione che non si carica o non termina.**

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

Il segnale di riuscita è il file scritto, non il codice di uscita.

**Il comando e il restore senza rete** (sulla fixture; sulle applicazioni vere il restore non basta, sotto):

| Misura | Risultato | Sonda |
| --- | --- | --- |
| `mvn -o -B -q -DskipTests package` col repository di `~/.m2` della costruzione | exit 0, 3,4 s (530 MB); poi `jar xf` 0,2 s; poi il lanciatore sul jar scompattato (`BOOT-INF/classes:BOOT-INF/lib/*`, classe da `Start-Class` del manifest) 2,7 s | `pipeline-m2` |
| con `target/` già presente (la preparazione l'ha lasciato) | exit 0, 3,1 s; il lanciatore dà lo stesso JSON | `pipeline-m2-keep-target` |
| **Solo il restore di Daodan** (`mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.8.1:go-offline`, la riga di `preparation.RESTORES["maven"]`) in un repository a parte, poi `mvn -o package` | exit 0 per 3.5.0 (3,2 s) e per 2.7.18 (3,3 s): `go-offline` basta a costruire e ripacchettizzare il jar senza rete **per queste fixture**; il lanciatore poi dà le rotte (2,8 s e 2,4 s). Su tre applicazioni vere non basta: vedi «Applicazioni vere». Il repository pesa 88 MB (3.5.0) e 85 MB (2.7.18), il `~/.m2` della costruzione di tutte le fixture 132 MB | `pipeline-goffline`, `pipeline-goffline27` |
| `clean` | `mvn -o clean package` sul `~/.m2` della costruzione: **exit 1**, `maven-clean-plugin:3.4.1` non scaricato (`PluginResolutionException`); sul repository di `go-offline`: **exit 0** (3,4 s): il restore di Daodan ha già il plugin | `clean-package-m2`, `clean-package-goffline` |
| Un comando più leggero: nessun jar | `mvn -o compile dependency:build-classpath` (3,1 s), il lanciatore su `target/classes` e il classpath scritto, classe principale **data a mano** (`demo.DemoApplication`): stesso JSON in 2,8 s. La classe principale senza il manifesto verrebbe dallo snapshot (non misurato) | `pipeline-compile` |
| Con la rete e il repository vuoto (la preparazione) | `go-offline` 24,3 s, 544 MB; poi `package` senza rete 3,9 s | `cold-build` |

## Applicazioni vere

`modal_real.py`, `real_summary.py`, `results/real/`. Le applicazioni sono scaricate al commit mentre l'immagine si costruisce; i sorgenti non sono nel repository.

| | (a) petclinic | (b) RuoYi | (c) petclinic-microservices |
| --- | --- | --- | --- |
| repository | `spring-projects/spring-petclinic` | `yangzongzhuan/RuoYi` | `spring-petclinic/spring-petclinic-microservices` |
| commit | `500158f732419217507c7656904b8e6aa1bcc0d6` | `d6708994364bfbb472c96380d6129e24303b3228` | `935ba9320a6514a6c31ff1316c29281b2191dcd3` |
| licenza | Apache-2.0 (`LICENSE.txt`) | MIT (`LICENSE`) | Apache-2.0 (`LICENSE`) |
| Spring Boot, Java | 4.1.0, 17 | 4.1.2, 17 | 4.1.2, 17 |
| Maven | un modulo | 6 moduli, l'applicazione è `ruoyi-admin` | 8 moduli, tutti applicazioni (Spring Cloud) |
| file Java | 50 | 287 | 64 |
| perché | H2 in memoria di default | MySQL a `localhost:3306` all'avvio, nessun default in memoria | più moduli, tre con WebFlux (Netty) |

**Restore e costruzione.** Il restore di Daodan (`maven-dependency-plugin:3.8.1:go-offline`, la riga di `preparation.RESTORES["maven"]`) più `mvn -o package` non costruisce su tre applicazioni su tre; costruisce `mvn package` con la rete.

| | (a) petclinic | (b) RuoYi | (c) microservices |
| --- | --- | --- | --- |
| `go-offline` | exit 0, 30,5 s, 598 MB; repository 241 MB | **exit 1**, 54 s (in altre esecuzioni 159, 771 e 1.506 s), 582 MB | exit 0, 103,7 s, 643 MB; repository 484 MB |
| `mvn -o package` dopo `go-offline` | **exit 1** in 2,8 s: 9 artefatti mancanti (`commons-logging:1.3.6`, `byte-buddy:1.18.10`, `slf4j-api:2.0.18`, `jaxb-runtime:4.0.9`, `aspectjweaver:1.9.25.1`…); il repository ha altre versioni di alcuni (di `commons-logging` fino alla 1.3.5) | **exit 1**: 14 mancanti (`fastjson2`, `jackson-databind:2.21.7`, `pagehelper-spring-boot-starter`…), spesso nessuna versione | **exit 1** in 3,8 s: 3 mancanti (`spring-boot-jackson2:4.1.2`: c'è la 4.0.9; `spring-security-crypto:7.1.2`; `commons-codec:1.21.0`) |
| `mvn package` con la rete dopo `go-offline` | exit 0, 14,2 s, 1.015 MB | exit 0, 18,4 s, 1.356 MB | exit 0, 15,3 s, 1.501 MB |
| `mvn package` con la rete, repository vuoto | exit 0, 32,4 s, 853 MB | exit 0, 19,3 s, 1.501 MB | exit 0, 59,9 s, 1.448 MB |
| `mvn -o package` dopo quella costruzione | **exit 0**, 7,9 s, 848 MB | exit 0, 11,0 s, 1.263 MB | exit 0, 15,1 s, 1.481 MB |
| lasciato dalla costruzione fuori da `target/` | niente | niente | niente |

Che cosa lo discrimina, su repository vuoti (`results/real/<nome>-restore.json`):

| Restore | (a) petclinic | (c) microservices |
| --- | --- | --- |
| `dependency:go-offline` fissato a 3.8.1 (la riga di Daodan) | 9 mancanti, exit 1 | 3 mancanti, exit 1 |
| `dependency:go-offline` senza fissare la versione (quella che Maven risolve; non registrata) | **0 mancanti, exit 0** (25,4 s il restore, 9,0 s la costruzione) | 1 mancante, exit 1 |
| `dependency:resolve` e `dependency:resolve-plugins` | **0 mancanti, exit 0** (28,8 s, 9,6 s) | **0 mancanti, exit 0** (42,0 s, 13,3 s) |

In RuoYi `go-offline` chiede un POM di un repository `http://` che Maven blocca; RuoYi non è provato con le due varianti.

**Il lanciatore**, sui jar costruiti, con le proprietà per la versione (4.1: `MODERN` più `enabled=` vuoto) e `server.port=-1`:

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

RuoYi non si carica senza il suo database: un advisor di Shiro dipende dalla sorgente dati e l'auto-proxy lo cerca prima di ogni bean. Provati e falliti: `spring.main.lazy-initialization=true`, `spring.autoconfigure.exclude`, `stop=aot`, `SpringApplicationAotProcessor`. Con un MariaDB locale e l'URL dato a mano si carica. Non misurati: la mappatura montata a mano su un contesto non attivo, `@WebMvcTest`.

**Noir sulle stesse applicazioni** (`noir scan <progetto> -f json --no-log`, prima della costruzione):

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

Sulla fixture (`results/real/fixture-summary.json`): 15 rotte del lanciatore, 17 di Noir, 15 in comune; per 14 Noir dà lo stesso gestore, file e riga. Per `GET /base/{id}` (il gestore in una classe base generica) Noir ha la rotta e nessun gestore. Solo di Noir: la `RouterFunction` e il controller di un profilo spento, che a runtime non c'è.

**Verdetto.**

- Rotte con gestore Java: 337 su 337 uguali fino alla riga. Ma 304 sono di RuoYi, che il lanciatore ha solo con un database locale: senza il servizio il confronto è 33 su 33, più un'applicazione che il lanciatore non vede e Noir sì.
- Su tre applicazioni e la fixture il lanciatore aggiunge un gestore.
- Costa una costruzione con la rete (14-18 s e 1,0-1,5 GB), un lancio di 6,9-18,5 s e 543-882 MB per modulo, proprietà che cambiano con la versione; 3 moduli su 10 non partono con `server.port=-1` (Netty), 1 su 10 non si carica senza il suo servizio.
- Ciò che Noir non ha sono le rotte come Spring le crea davvero (profili, condizioni) e le funzionali: nessuna delle tre applicazioni lo esercita.

## Aperto

- **Aperta: da approfondire. Il restore Maven di Daodan.** `go-offline` fissato a 3.8.1 non basta a `mvn -o package` su 3 applicazioni vere su 3; `dependency:resolve` più `resolve-plugins` ha dato 0 mancanti su petclinic e microservices. La riga è in `preparation.RESTORES["maven"]`, non toccata; la causa non è isolata. Che `~/.m2` e `target/` sopravvivano fra preparazione ed esecuzione nel motore di Daodan è letto nel codice, non provato.
- **`GET /base/{id}` e i gestori che Noir non dà:** se il passo dinamico (`daodan/core/dynamic/jvm.py`) li osserva non è misurato.
- **Dove Noir potrebbe sbagliare:** costanti, meta-annotazioni o segnaposto nei percorsi; non misurato.
- **Non coperti:** Gradle e Kotlin, Spring Boot 3.0-3.4, JDK 21 o 25, profili attivi, `server.servlet.context-path` e `spring.mvc.servlet.path`, un `main` che personalizza `SpringApplication`, classi senza `LineNumberTable`, più applicazioni (le tre sono Boot 4 con controller annotati).
- Non isolati: perché il `SIGTERM` non ferma un bean bloccato nel refresh; che cosa chiede l'`entityManagerFactory`; perché `stop=aot` cade su RuoYi anche con il database.
