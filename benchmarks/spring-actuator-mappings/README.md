# Spring Boot: Actuator `mappings` senza aprire una porta

**Stato: sonda scritta il 24 novembre 2026, NON ESEGUITA.** La sessione che l'ha scritta non ha le credenziali di Modal e la regola del progetto vieta di caricare l'applicazione o di compilarla su quella macchina. Nessun numero di questa pagina è una misura: le tabelle sotto dicono che cosa la sonda misurerà. La sorgente `premap/spring.py` e le risposte registrate non esistono, perché dipendono dal modo di caricamento che la sonda deve decidere (piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14f; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6).

Domanda: `GET /actuator/mappings` si ottiene senza aprire una porta, e che cosa dà: metodi, schemi, classe, metodo, descrittore del gestore, e file e riga?

| Cartella | Contenuto |
| --- | --- |
| `fixture/src/` | un'applicazione Spring MVC: `ItemController` (`GET`, `GET /{id}`, `POST`, `PUT`, `DELETE`, due overload di `search` distinti da un parametro, `GET`+`HEAD` in una mappatura), `PageController` (una pagina e una classe annidata `Ping`), `Routes` (una `RouterFunction`, senza metodo gestore), `Switches` (due cose che impediscono di caricarla, accese da una proprietà: un bean che si connette a `db.invalid:5432` e un `CommandLineRunner` che non ritorna) |
| `fixture/poms/` | `boot3` (Spring Boot 3.5.0 con Actuator), `boot27` (2.7.18 con Actuator), `plain` (3.5.0 senza Actuator); stessi sorgenti, Java 17, `mvn package` |
| `Launcher.java` | un file che gira in modalità sorgente (`java -cp … Launcher.java`): nulla del progetto è modificato né compilato da Daodan; chiama `SpringApplication` con `server.port=-1` e l'esposizione di `mappings`, trova il bean dell'endpoint per id (`@Endpoint(id = "mappings")`, con la riflessione: i pacchetti cambiano fra le versioni) e ne scrive il JSON in un file; modo `handler-methods`: i gestori di `RequestMappingHandlerMapping` (spring-webmvc, senza Actuator) |
| `modal_probe.py` | costruisce l'immagine con la rete aperta (`mvn package` di ogni fixture, il jar scompattato con `jar xf`, e `dependency:go-offline` a parte), poi esegue ogni sonda senza rete; scrive `results/<sonda>.json` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/spring-actuator-mappings/modal_probe.py
```

## Che cosa la sonda misura (parametri)

| Domanda | Sonda | Che cosa si legge |
| --- | --- | --- |
| Il contesto nasce con `server.port=-1` e nessuna porta ascolta? | `actuator-boot3`, controllo `port-control` (`server.port=0`: la porta casuale deve comparire) | `ports_listening` (da `/proc/net/tcp`, ogni 50 ms), le mappings piene o vuote, il `DispatcherServlet` |
| Il bean dell'endpoint c'è senza esporlo via web, e che forma ha il JSON in Boot 2.7 e 3.5? | `actuator-boot27`, `actuator-boot3` | `contexts.*.mappings.dispatcherServlets`, `handlerMethod.{className,name,descriptor}`, `requestMappingConditions`; gli overload; la `RouterFunction`; il rumore del framework (`BasicErrorController`, risorse statiche, gli endpoint di Actuator) |
| Senza Actuator? | `no-actuator`, `handler-methods-plain`, `handler-methods-boot3` | la lacuna dell'avvio, o lo stesso dato da `getHandlerMethods()` |
| File e riga? | `javap` (`-l -p` del JDK sulle classi del jar) | `SourceFile` e `LineNumberTable`: la riga della prima istruzione, il nome del file senza percorso; overload, classe annidata |
| Un'applicazione che non si carica? | `needs-database`, `needs-database-lazy` (`spring.main.lazy-initialization=true`) | exit, coda dello standard error, secondi al fallimento |
| Non termina? | `never-ends` (limite 20 s) | exit 124 o 137 e `processes_left` vuoto |
| Il restore di Daodan basta per costruire senza rete? | `offline-package` (la `~/.m2` della costruzione), `goffline-package` (solo `dependency:go-offline`) | exit e coda dello standard error |
| Tempo e memoria | ogni sonda; `cold-build` (con la rete, repository vuoto) | `seconds`, `peak_memory_mb` |

## Non coperto dalla sonda (aperto)

Gradle (`bootJar`, il restore `gradle dependencies`) e Kotlin (`suspend`, classi `FooKt`: il descrittore ha `Continuation`), Spring Boot 4 (i pacchetti sono spostati: il lanciatore usa la riflessione, ma la forma del JSON non è vista), WebFlux (`dispatcherHandlers`), un JDK 21 o 25 sull'immagine con Temurin 17, `@Profile` e `@ConditionalOnProperty` (le rotte che non nascono sono assenti, in silenzio), un `package` che lancia plugin del progetto (frontend npm, generatori), il legame del gestore con la funzione dello snapshot (descrittore contro lo snapshot di scip-java, e gli overload).

## Decisioni che aspettano la misura

Il comando di una sorgente (`mvn package`/`bootJar` con la rete e poi il lanciatore senza rete, o una compilazione più leggera), la voce `spring` in `container_runner.TOOLS` (JDK, Maven, Gradle, memoria) e se `container.run_commands` conserva `~/.m2` e `target/` fra il comando con la rete e quello senza. Se la misura dice che quasi ogni applicazione vera non si carica senza database, la sorgente dà quasi sempre una lacuna con la causa e i candidati di Noir: la misura decide se vale scriverla.
