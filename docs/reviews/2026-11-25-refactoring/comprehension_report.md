## What this proposes

Daodan analizza un progetto software e ne costruisce un grafo. Il disegno (A) lo vuole come pipeline di otto step con nomi stabili (`list_files`, `read_code`, `recognize_stack`, `find_modules`, `find_entry_points`, `link_calls`, `run_and_observe`, `assemble_graph`): ogni step ha una sola competenza, chiede agli altri i fatti che non stabilisce, usa lo strumento ufficiale di ogni tecnologia, esegue il codice del progetto solo in un container e scrive una lacuna con causa quando non riesce. Attorno agli step ci sono anagrafiche come dati (`daodan/data/`), servizi comuni (container, preparazione con proxy, lanciatore, giornale, Secretlint) e un «piano» unico che il chiamante vede prima dell'avvio e che si riempie di azioni durante la scoperta. Il piano di lavoro (P) ci arriva in quattro traguardi con cancello: T0 misura lo stato di oggi e chiude i difetti noti, T1 riordina la parte statica fino agli ingressi e introduce il piano unico, T2 risolve le chiamate con SCIP e fa l'unione statica, T3 aggiunge isolamento, esecuzione osservata e verifica della mappa. Nessuno dei due documenti dice quale problema di oggi il refactoring risolve: l'ho dovuto lasciare fuori dalla parafrasi (P:37 lo ammette).

## How the existing system works, per this document

Lo stato di oggi non è descritto in un punto: l'ho ricostruito dalle note «[accertato nel repository]», dalle colonne «Stato» e da «Oggi nel codice». Oggi gli step sono sei (`Scan, Stack, Parse, Analyze, Dynamic, Union`, P:76). Esiste una «pre-mappa» (`daodan/core/premap/`) con 35 sorgenti che decidono da sé se applicarsi e che tiene insieme modello di build, rotte ed eventi; alcune eseguono già codice del progetto nel container e usano la rete dietro un proxy (P:34). Lo stack lo riconosce un fork di `stack-analyser`; un piano come dati esiste già (`plan.py`, P:78); la risoluzione delle chiamate ha già strutture per verdetti e risolutori (P:102); i registratori dinamici esistono per più linguaggi (P:123); il container gira già senza rete in esecuzione (P:120). Esistono tre sorgenti Django/FastAPI/Flask scritte e scollegate, con tre benchmark che dicono di non collegarle (P:70). Non so dire come i sei step di oggi diventano gli otto: i documenti non danno la corrispondenza.

## Rilievi

Sigle: A = `docs/specs/architettura.md`, P = `docs/plans/refactoring.md`, con numero di riga.

### 1. Blocker
**Ambito:** P:26 (T0 punto 3), P:28-29 (T0 punto 4, prime due voci), P:124 (T3 punto 4)

Non riesco a parafrasare queste voci, e due sono nel traguardo aperto e nel suo cancello. T0.3 elenca difetti con sole etichette («Avro duplicato», «`technologies.state`», «test instabile `test_codebase_map_app.py`»): non c'è sintomo né atteso, quindi non si può «classificare e risolvere». T0.4 dichiara implementati «run di lavoro, hook e regole 1–4 review» e «copertura dell'intero sorgente (Parte A/Parte B, celle, prova preparazione 3 richieste)» senza dire che cosa sono né che legame hanno con la pipeline a otto step: sembrano di un altro sottosistema (review). T3.4 chiede di correggere «`on` senza punto citato e `verified` senza store provato»: frase incomprensibile senza sapere che cosa sono `on`, `verified` e «punto citato».

### 2. Major
**Ambito:** P:9, e ogni voce con `[deciso]` riaperta da una scelta aperta (P:69 contro P:86; P:101 contro P:109; P:59-61 contro P:87-88; P:77 contro P:89; P:33 contro P:38; A:41, A:47, A:131)

Le etichette `[deciso]`, `[misura]`, `[difetto]`, `[spike]` non sono definite, e `[deciso]` non regge alla lettura. P:9 dice che la decisione sui rilievi è «nelle Scelte aperte, non presa», ma le stesse voci portano `[deciso]` nel piano e in A. Esempi: Django/FastAPI/Flask è `[deciso]` come sorgente primaria (A:41, P:69), ha tre verdetti «no» (P:70) ed è scelta aperta B1 (P:86), e il cancello T1 la dà per fatta (P:93). L'evidence model è `[deciso]` (A:47, P:101) e M5 chiede se è un modello nuovo (P:109). Il lettore non sa che cosa può implementare.

### 3. Major
**Ambito:** A:3 («com'è Daodan a refactoring finito») contro P:78, P:91, A:111, A:80-86, A:94-98

A si dichiara contratto dello stato finale, ma contiene cose che nessun punto di P consegna. P:91 lo dice per `surface`, `ui_execution_deferred` e `approval_required`. Lo stesso vale per «L'interfaccia segue la pipeline» (A:111): T1 mette «nuova UI» fuori (P:47), P:78 manda l'adeguamento della UI nel backlog, e T2/T3 non la citano. A mescola inoltre nello stesso testo stato finale, stato di oggi («Oggi nel codice», A:72), proposte («Proposta (T3)», A:94) e differiti (A:98): non si capisce quali frasi sono contratto.

### 4. Major
**Ambito:** A:17-28, P:75-76

Manca la corrispondenza tra i sei step di oggi, i sette nomi del README (P:76) e gli otto del disegno. P:75 dice «rimuovere lo step `parse`», ma l'unico step di oggi che dal nome legge il codice è `Parse`, e nel disegno c'è `read_code`: non si capisce se `Parse` sparisce, diventa `read_code` o è altro. Né si capisce quale step di oggi contiene la pre-mappa.

### 5. Major
**Ambito:** A:8 (Principio 2) contro A:23-24

«Un padrone per fatto», ma nella tabella sia `recognize_stack` sia `find_modules` scrivono «toolchain» e «servizi». Non è detto se sono fatti diversi con lo stesso nome o lo stesso fatto con due padroni. Vicino: P:84 chiede che fare dei pacchetti «noti solo a `find_modules`», cioè tecnologie che lo step padrone dello stack non vede.

### 6. Major
**Ambito:** P:11-16 contro P:106; P:33-34 contro P:38

Due collocazioni non tornano. (a) La tabella dei traguardi dà `assemble_graph` a T3, ma T2 punto 5 fa già lì l'unione statica: non è detto che lo step nasce in T2 e si completa in T3. (b) T0.7 dice «se T0 scarica dipendenze, eseguire questo test già in T0»; la nota sotto accerta che la rete è già usata oggi; eppure la sonda resta scelta aperta tra T0, T1 e T3.1, e il cancello T0 chiede solo il «criterio fissato». Il lettore non sa se in T0 il test si esegue.

### 7. Major
**Ambito:** P:7 e ogni «ex ondata N», «ex scelta N», «prove 2 e 5» (P:79), «Task 12» (P:30), «T3.1», «T3.4» (P:38-39)

Il piano si appoggia a una spec rimossa, leggibile solo con `git show`. «Ex ondata 1–8» ed «ex scelta 1–13» non aggiungono nulla a chi non la apre; «prove 2 e 5» porta lavoro vero (P:79) con una glossa tra parentesi troppo corta («equivalenza modalità»: quali modalità?). «T3.1» e «T3.4» non sono una notazione dichiarata: si indovina che siano i punti 1 e 4 di T3.

### 8. Major
**Ambito:** parola «piano»: A:17, A:100-107, P:1, P:53, P:77-78, P:89

«Piano» ha almeno tre sensi senza distinzione: il documento di lavoro (P), l'oggetto che Daodan espone al chiamante (A:100), e «piano 122 progetti invariato» (P:53), che non è nessuno dei due. Inoltre A:17 dice che il piano «è una funzione», A:102 che è «un solo oggetto condiviso». P:78 dice che esiste già `plan.py` con nodi e lacune: non è scritto che cosa gli manca rispetto ad A:104-107 (lo chiede M4).

### 9. Major
**Ambito:** «mappa», «grafo», «mappa di sistema», «pre-mappa», «vista statica del grafo»: A:30, A:57, A:76, P:15-16, P:97, P:124

Non è detto se sono la stessa cosa. `assemble_graph` scrive il «grafo completo» (A:28), T3 consegna la «mappa (`assemble_graph`)» (P:16), A:76 parla di una «Mappa di sistema» con una sua vista (`system_levels.view`) e nodi propri, T2 consegna una «vista statica del grafo» mai descritta. La «pre-mappa» è definita solo per lo stato finale (A:30); quella di oggi va ricostruita da P:30.

### 10. Major
**Ambito:** A:59-76 («Nodi del grafo: tipo e logo»), A:122

La sezione usa due campi senza dire come si rapportano. A:122 dà a `kind` i valori `service`, `project` e a `category` i valori `framework`, `library`, `tool`, `service`; A:59 dice «senza `category`, una voce di `kind` `service` vale `service` e le altre `framework`»; la tabella A:63-65 parla di «voce `service`», «voce `framework`», «voce `tool`» senza dire quale campo. `kind` `project` non è mai spiegato. Usati senza definizione: «gruppo» (A:64), «store» e «regola di collegamento» (A:68), `by: model` (A:71), «mappatore» e «brief del mappatore» (A:72), «tessera» e «pittogramma» (A:74), «icona dell'entità» (A:75). A:59 dice che l'anagrafica dà un tipo di nodo a ogni framework, A:64 che un framework non è un nodo: la riconciliazione arriva solo a A:71-73 ed è una scelta aperta dentro un contratto «stabile».

### 11. Major
**Ambito:** «modulo», «unità», «pacchetto», «programma»: A:24, P:65, P:122

`find_modules` scrive «moduli, unità, toolchain, pacchetti e grafo dei pacchetti» (A:24) senza dire che differenza c'è tra modulo e unità. P:65 decide una «voce unica unità/pacchetto», cioè tratta come unificabili due cose che A elenca separate. T3.3 lavora «su un programma» (P:122), termine che non compare altrove.

### 12. Major
**Ambito:** misure e campioni: P:24-25, P:32, P:39, P:53, P:103, P:105, P:124-125

Il cancello di ogni traguardo poggia su misure che il lettore non può identificare. «Campione di riferimento» (1 stack + 1 progetto reale) va fissato in T0 ma non c'è criterio di scelta né che cosa sono le «domande verificate». «Confronto cieco» e il suo protocollo non sono descritti; `0/19` si capisce solo a P:125, e lì restano «modello debole» e «variante A». «Corpus», «scansione veloce» (P:25), «180 progetti» e «122 progetti» (P:53), «112 divergenze» (P:52), `chi` e `tududi` (P:103), «1/4 passaggi staccati» e «154 chiamate `self.metodo()`» (P:105) non hanno fonte né significato. «Suite intera» (P:24) è seguita da una parentesi di tre elementi che non si capisce se la delimita.

### 13. Major
**Ambito:** sistemi e strumenti del progetto mai definiti né collegati

Nomi propri usati come noti. «Modal» (P:13, P:20 e tutti i `[misura]`): è dove girano le prove, ma non è detto che cos'è né perché lì. «Fork `stack-analyser`» (A:31, P:25, P:59-61): non è detto di chi è, dove sta, che cosa significa «rilascio `.6`». «Kiri» (A:130, P:47, P:117): motore di container di Daodan su Windows, ma «Kiri ovunque» è fuori da T3 senza dire che cosa sarebbe. «Sigrid» e «Imago» (A:111). «binder» / `binder.bind` (P:68, P:71). «Lettori GitNexus» e «valutatore stringhe per percorsi calcolati» (P:85). «Passo per posizione» e `--engine scip` (P:103, P:111). `engine-answers.sqlite`, `JavaEngine`, `KotlinResolver.kt`, `typescript_unbound.js`, «secondo Pyright» (P:103-105). `WORKING_RUN`, `query_gate` (P:28). `step.skipped` (P:79). «Motore generale dei legami» e ramo `feat/link-key-shape` (P:106).

### 14. Major
**Ambito:** A:36, A:46, A:53; P:68-72

«Noir» è definito in una riga («lo scanner di rotte che gira nel container») senza link né che cosa legge. A:46 lo chiama «fallback statico» e dice che fa da ripiego «senza container», ma A:36 dice che gira nel container: non è chiaro che cosa resta quando il container manca. La «chiave che includa contesto/mount/router dove serve» (A:46) è vaga: non dice quando serve.

### 15. Major
**Ambito:** A:43, A:48, P:122-123, P:130

L'osservazione runtime è descritta come confronto tra «registratori `*_record.*`» e «backend standard», ma P:123 accerta che per Python i due coincidono e che V8 e OpenTelemetry sono già stati valutati e scartati, con il profiler V8 nel backlog come «non si rifà». Il lettore non capisce che cosa resta da misurare in T3.3 (lo chiede M6). «Frontiere» (A:43, A:48, P:122) e «registro esatto» (P:123) non sono definiti.

### 16. Major
**Ambito:** P:59-62 e A:31, A:123

Non è chiaro il rapporto fra tre cose: le «famiglie di regole» da aggiungere al fork (riconoscere), gli adattatori in `premap/` che per 7 famiglie su 10 esistono già e trovano da sé il manifesto (P:62), e `build-tools.json` che lega le due. Non è detto che cosa non funziona oggi senza le regole nel fork (lo chiede M3), né che cosa deve decidere il confronto con Syft, già misurato (P:60, M2).

### 17. Nit
**Ambito:** P:41 contro P:111

P:41 dice «da T1 in poi zero nuove regressioni rispetto a T0»; il cancello T2 dice «rispetto a T1». «Regressione» non ha un metro dichiarato (quali esiti si confrontano).

### 18. Nit
**Ambito:** A:17, A:19; A:82-84

A:17 dice che la numerazione 1–8 è solo ordine di presentazione, ma la tabella mostra che `recognize_stack` (3) non dipende da `read_code` (2): non è detto se l'ordine di esecuzione è quello o se 2 e 3 sono indipendenti. A:83 scrive «`webview` (attiva in T3)»: un contratto «stabile» che cita un traguardo del piano.

### 19. Nit
**Ambito:** A:86, A:94, A:131

Frasi dense senza appoggio: «progetti multipiattaforma eseguiti sul bersaglio `web` quando dichiarato» (dichiarato da chi?), «archivio di Daodan» dei comandi dell'utente (dove sta, chi lo scrive), «strumenti verificati per sha256» (contro quale elenco), «download di qualche GB» (soglia non data).

**Conteggio:** 1 Blocker, 15 Major, 3 Nit. I rilievi 1-6 sono di connessione tra le parti; 7-16 di termini e rimandi.

---

**Fase 2 di 5 (stage 6 del protocollo): comprensione.**
Revisore: agente nuovo `general-purpose`, modello `fable`, effort `medium`, completato. Ha ricevuto la sola persona e i due documenti, senza standard, senza backlog e senza contesto, con l'istruzione di non seguire i link. Sola lettura e limite ai due file sono istruzioni, non limiti degli strumenti, e le istruzioni di progetto possono arrivare al revisore.
Versione letta: commit `591e1f6ed` più le aggiunte dell'agente sui documenti, non ancora in un commit; i numeri di riga sono di questa versione.
I rilievi non sono stati controllati dal coordinatore.
