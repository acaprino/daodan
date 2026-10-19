# Daodan: un comando per ogni intenzione

Proposta del 19 ottobre 2026. Sostituisce i 32 comandi attuali, sparsi in 16 plugin
e ciascuno con i suoi flag, con 22 comandi senza parametri, da usare da soli o in
sequenza come ciclo. Tiene conto della prima prova reale del ciclo
(`docs/superpowers/reports/2026-10-19-closed-loop-probe-claude.md`).

## 1. Principi

1. **Un comando per intenzione.** Il nome dice cosa vuoi, non come viene fatto.
   Nessuna variante "team" o "lite": la profondità la decide il comando.
2. **Nessun parametro.** L'unico argomento è testo libero.
3. **Le autorizzazioni si chiedono quando servono**, una volta, e il run le
   registra. Niente `--fix` o `--commit`.
4. **Ogni comando funziona da solo; il ciclo è la loro sequenza.**
5. **Quanto lavoro fare lo decide uno script, non il modello.** Nella prova il
   testo "proporzionato al rischio" ha prodotto sette revisori per una correzione
   dentro una funzione: 40 minuti, 30,90 USD.

## 2. I comandi

Tutti nel plugin `daodan`: su Claude Code, `/daodan:<nome>`.

### Progetto

| Comando | Cosa fa |
|---|---|
| `init-project` | Porta il progetto nel ciclo: mappa, indice degli ADR, blocco del ciclo nelle istruzioni, interprete e comandi di test verificati, baseline dei test. Su una cartella vuota crea lo scheletro. I comandi di lavoro lo eseguono da soli se manca |
| `onboard-project` | Ti spiega un progetto sconosciuto: scopo, moduli, flussi critici, avvio e test, rischi, decisioni in vigore |
| `check-health` | Diagnosi del debito: struttura, test, dipendenze, documentazione, igiene. Produce un piano |
| `run-maintenance` | La campagna di risanamento completa, a tappe approvate |

### Pensare

| Comando | Cosa fa |
|---|---|
| `brainstorm-idea <idea>` | Esplora un'idea con te, ancorata al codice e agli ADR. Una domanda alla volta, alternative con i costi. Non scrive codice. Finisce con "facciamola" (parte `new-feature`), "teniamola" (nota in `docs/ideas/`) o "lasciamo stare" |
| `investigate-problem <problema>` | Indaga un errore, un bug o un comportamento strano senza correggerlo: raccoglie i fatti (messaggio, log, stack, commit sospetti), formula le ipotesi, le verifica una per una contro il codice e, se possibile, riproduce il problema con un test. Finisce con la causa dimostrata o con le ipotesi rimaste e cosa servirebbe per decidere. Da lì, "correggiamo" passa a `fix-bug` con il test già scritto |
| `get-second-opinion <file o domanda>` | Un altro modello contesta un file, oppure più modelli discutono una domanda. Chiede il consenso prima di mandare contenuto fuori |

### Lavorare

| Comando | Cosa fa |
|---|---|
| `new-feature <cosa>` | Nuovo comportamento: intervista con esempi dal tuo codice, ADR proposto, piano a ondate che approvi, esecuzione con review leggera a ogni commit |
| `fix-bug <cosa>` | Prima il test che riproduce il difetto, poi intervista breve, correzione, review leggera. ADR solo se cambia un contratto. Se la causa non è chiara, parte da solo con `investigate-problem` |
| `refactor-code <cosa>` | Comportamento invariato: test di caratterizzazione, ondate, review sull'equivalenza. Copre anche la leggibilità |
| `continue-task [risposte]` | Riprende il task del branch corrente, anche da un'altra sessione. Il testo risponde alle domande in sospeso |
| `show-status` | L'agenda: task aperti con fase, avanzamento, chi ci lavora, domande in sospeso; stato della mappa e degli ADR. Non modifica nulla |
| `finish-task` | Chiude il task: review completa, merge con la tua autorizzazione, ADR promosso, mappa e documentazione riallineate, worktree chiuso |
| `sync-upstream` | Porta dentro il lavoro degli altri: fetch, cosa è arrivato, fast-forward se sicuro, mappa e documentazione riallineate |

Se non sai quale dei tre comandi di lavoro usare, `new-feature`: l'intervista corregge
il percorso.

### Review

| Comando | Cosa guarda |
|---|---|
| `review-changes [cosa]` | Le modifiche correnti, l'ultimo commit, o il file, la cartella, il commit che indichi. Codice, piani, specifiche, documenti. Leggera. Nel ciclo parte da sola prima di ogni commit |
| `review-branch [branch o PR]` | Tutto il branch rispetto alla base, o una PR. È la team-review di oggi. Nel ciclo parte da sola in `finish-task` |

### Strumenti

| Comando | Cosa fa |
|---|---|
| `write-tests <cosa>` | Scrive test per il codice indicato |
| `map-code [area]` | Approfondisce la mappa su un'area, o su tutto il progetto |
| `write-docs [cosa]` | Riallinea la documentazione al codice; con un testo scrive ciò che chiedi: guida, README, istruzioni |
| `record-decision <decisione>` | Registra un ADR fuori da un task |
| `tidy-repo` | Pulizia: file spazzatura, codice morto, test ridondanti. Anteprima, poi autorizzazione |
| `humanize-text <testo o file>` | Rende naturale un testo senza inventare contenuto |

## 3. Il ciclo

```text
/daodan:init-project                  una volta per progetto
/daodan:brainstorm-idea <idea>        se l'idea non è chiara
/daodan:investigate-problem <errore>  se la causa non è chiara
/daodan:new-feature <cosa>            oppure fix-bug, refactor-code
    review leggera prima di ogni commit
/daodan:finish-task                   review completa, merge, riallineamento
```

Un comando di lavoro va da solo fino all'ultimo commit. Si ferma solo per le tue
domande, l'approvazione del piano e l'autorizzazione alla merge. Alla fine propone
`finish-task`. Gli stessi passi, uno alla volta, sono i comandi singoli.

## 4. Regole comuni

- **L'argomento** è un percorso, un commit, una PR o un branch se esistono,
  altrimenti testo libero. Il comando dice come lo ha letto prima di cominciare.
- **Il task è legato al branch.** Nessun id da ricordare.
- **Le domande** si fanno solo con lo strumento che l'host offre. Se non c'è, il
  comando le registra nel run, chiude il turno elencandole e riparte da
  `continue-task <risposte>`. Non sceglie mai al posto tuo.
- **L'ambiente è quello del progetto.** `init-project` registra interprete e comandi; tutti
  li usano. Installare fuori dal progetto richiede la tua autorizzazione.
- **I prerequisiti si controllano all'avvio.** Un plugin richiesto non attivo
  ferma il comando subito, con il comando esatto per abilitarlo.
- **Tutto ciò che un comando scrive per sé** sta in `.daodan/runs/<id>/`.

## 5. La mappa cresce da sola

- **Base**, solo script: inventario, simboli, interfacce, digest. La fa `init-project`, la
  aggiornano `finish-task` e `sync-upstream`.
- **Leggera**, una volta: struttura, interfacce, rischi. La fa `init-project`, poi si
  aggiorna solo ciò che è cambiato.
- **Approfondita**, dove si lavora: flussi, semantica e schede dell'area del task.
  La fanno i comandi di lavoro sulla loro area, o `map-code`.

Le schede sanno da sole quando sono scadute, quindi si rifà solo ciò che è
cambiato.

## 6. Due livelli di review

**`review-changes`.** Prima gli strumenti del progetto: test, lint, tipi, dipendenze se
cambia un manifesto. Poi un solo revisore: il generalista sul codice, il controllo
delle affermazioni del premise auditor su ADR, piani e documenti. Verifica
avversariale solo su Critical e High. Se i segnali sono forti, consiglia
`review-branch` invece di allargarsi.

**`review-branch`.** Tutte le prospettive che i segnali del branch attivano, con
mappa, derivazione cieca delle premesse e pannello di verifica. Le prospettive le
sceglie uno script dal diff e dalla mappa, le scrive nel run, e il protocollo
rifiuta un dispatch in più. Se chiedi di andare più a fondo, se ne aggiungono.
Le soglie si tarano sulle prove.

## 7. Sync

1. `git fetch`. Non tocca i tuoi file.
2. Dice quanti commit sono arrivati, di chi, quali moduli e ADR toccano, e se
   toccano i file del tuo task aperto.
3. Aggiorna il branch principale solo in fast-forward. Altrimenti chiede.
4. Riallinea: mappa, ADR dei task uniti altrove promossi, ADR con simboli cambiati
   segnalati a te, documentazione e blocco del ciclo.

`finish-task` porta il tuo lavoro nel branch principale, `sync-upstream` porta nella tua copia il
lavoro degli altri.

## 8. Investigate: la review al contrario

La review multi-prospettiva cerca difetti in un cambiamento. L'indagine parte da un
difetto osservato e cerca il cambiamento che lo ha causato. Sono lo stesso motore,
girato al contrario, e `investigate-problem` riusa i pezzi che esistono:

1. **I fatti.** Messaggio d'errore, log, stack, come riprodurlo, da quando succede.
   Quello che manca lo chiede, una domanda alla volta.
2. **Il perimetro.** Dallo stack e dai simboli citati, il pacchetto di impatto
   della mappa dà chiamanti, chiamati, digest e modifiche recenti. I commit che
   hanno toccato quei simboli dopo l'ultimo funzionamento noto sono i sospetti.
3. **Le ipotesi.** Fino a tre, con lo stesso formato delle review: innesco,
   controprove da cercare, commit sospetto, classe di evidenza. Ogni ipotesi è
   verificata da un worker isolato che non vede le altre, contro il codice reale.
   Le prospettive sono quelle che i segnali attivano: timer e retry, persistenza,
   ordine di inizializzazione, UI, concorrenza.
4. **La riproduzione.** Un test minimo che fallisce sul codice corrente e passa
   sul commit prima del sospetto. Senza riproduzione la causa resta un'ipotesi, e
   il rapporto lo dice.
5. **Il verdetto.** La causa dimostrata, con il test, oppure le ipotesi rimaste e
   cosa servirebbe per decidere. "Correggiamo" passa a `fix-bug` con il test già
   scritto.

**Il limite.** È analisi statica più i test del progetto. L'esecuzione, quando
serve, la fa un worker nel sandbox del progetto e con il suo interprete: il
programma con i log al massimo, un tracciamento temporaneo tolto prima di
chiudere, un test ripetuto cento volte per una race, `git bisect` sul test di
riproduzione. Nessun debugger interattivo: ogni linguaggio ha il suo, il
programma deve potersi avviare dalla sessione, e un modello ragiona meglio su una
traccia che su una sessione passo per passo. Se le prove mostreranno una classe
di bug che questo non chiude, il debugger sarà un worker nuovo, non un'aggiunta
qui.

## 9. Agenda

Oggi ogni task ha il suo registro (`.daodan/runs/<id>/work.json`) nel worktree
dove si lavora, e si riprende con l'id del run. Manca l'elenco dei task, e
rimuovere il worktree cancellerebbe il registro.

- **Una sede sola.** Agenda e registri nella `.daodan/` del checkout principale,
  che ogni worktree trova attraverso Git.
- **L'agenda** è `.daodan/agenda.json`: una riga per task con tipo, titolo,
  branch, ADR, fase, ondate chiuse sul totale, ultimo commit, esito dell'ultima
  review, domande in sospeso, e chi ci sta lavorando con sessione e ora.
- **Il lock è quella riga.** Un comando che trova il task preso da un'altra
  sessione si ferma e te lo dice; se quella sessione è chiusa, rispondi che può
  procedere. `finish-task` libera la riga.
- **I commit sono il diario.** Ogni micro-task chiuso è un commit
  `<tipo>(<area>): <micro-task>` con la riga finale `Daodan-Task: <id> wave 2/3`.
  L'ADR viaggia nel branch, quindi su un'altra macchina `continue-task` capisce cosa è
  fatto e ripianifica il resto.

## 10. Dove finiscono i 32 comandi di oggi

| Oggi | Domani |
|---|---|
| `project-lifecycle:change`, `repair` | `new-feature`, `fix-bug`, `refactor-code` |
| `project-lifecycle:assess` | `check-health`; `--init` diventa `init-project` |
| `project-lifecycle:verify` | `review-changes`, `review-branch` |
| `project-lifecycle:consolidate` | `finish-task`, `sync-upstream`; la pulizia dei run in `tidy-repo` |
| `project-lifecycle:handover`, `run-maintenance` | `onboard-project`, `run-maintenance` |
| `senior-review:code-review`, `pr-review`, `team-review` | `review-changes`, `review-branch` |
| `codebase-map:analyze`, `team-analyze` | `map-code`; le partizioni le decide il comando |
| `project-knowledge:guide`, `readme`, `instructions`, `run-maintenance` | `write-docs` |
| `project-knowledge:adr` | `record-decision`, e dentro il ciclo |
| `testing:test-audit`, `test-consolidate` | `check-health`, `tidy-repo` |
| `repo-hygiene:tidy` | `tidy-repo` |
| `clean-code:clean-code`, `python-development:python-refactor` | `refactor-code` |
| `abstraction-architect:audit`, `dependency-audit:deps-audit`, `python-development:python-audit`, `react-development:review-react`, `typescript-development:review-typescript`, `platform-engineering:platform-review` | Prospettive interne di `review-changes`, `review-branch` e `check-health`, attivate dai segnali |
| `python-development:python-scaffold` | `init-project` su una cartella vuota |
| `peer-review:review`, `moe:ultra-nerd` | `get-second-opinion` |
| `text-humanizer:humanize-text` | `humanize-text` |
| nessuno | `brainstorm-idea`, `investigate-problem`, `continue-task`, `show-status`, `write-tests` |

Nessuna capacità sparisce. Cambia l'ingresso, non il metodo.

## 11. Architettura

Nasce il plugin `daodan` con i 22 workflow, ciascuno un rimando sottile al metodo
del suo responsabile. Gli altri plugin conservano skill, ruoli e contratti e
perdono i comandi. `daodan` dichiara obbligatori tutti i plugin del nucleo. La
regola di `CLAUDE.md` sui comandi degli specialisti va riscritta: il lavoro mirato
passa da `review-changes`, `write-tests`, `map-code`, `write-docs` e `tidy-repo`.

Sugli altri host il nome diventa `/daodan-new-feature` (Pi), la skill
`new-feature-workflow` (Codex) e il prompt `new-feature` (Copilot). Nessun nome
coincide con un comando integrato: `review` esiste in Codex, `/init` e `/docs` in
Claude Code, e i verbi li evitano.

## 12. Piano

1. **Motore.** Script del roster e sua applicazione nel protocollo; agenda nella
   sede comune; task legato al branch; domande registrate; ambiente del progetto;
   controllo dei plugin all'avvio; file solo nel run.
   Consegnato: roster e suo rispetto (37.1.0); agenda nel checkout principale
   con lock come riga, sezioni `questions` ed `environment`, trailer nei
   commit, sonda dei provider e dell'ambiente nel preflight, scratch solo nel
   run (37.2.0).
2. **Metodi nuovi.** `brainstorm-idea`, `investigate-problem`, la review leggera, `finish-task`, `sync-upstream`, la mappa
   per area, i router di `write-docs`, `tidy-repo` e `get-second-opinion`.
   Consegnato in 37.3.0: la review leggera come unità propria, con un roster per
   tipo di bersaglio e una voce per review nella lista `reviews` del run;
   `investigation-method`; `brainstorm.md`, `finish.md`, `sync.md`,
   `realign.md`, `retention.md` al posto di `consolidate.md`; l'approfondimento
   per area che scrive le schede della mappa. I router nascono con i workflow
   della fase 3, perché sono il corpo stesso di quei comandi.
3. **Ingresso.** Il plugin `daodan`; i workflow tolti dagli altri plugin.
   Consegnato in 38.0.0: i 22 comandi; il metodo che stava nei comandi degli
   specialisti spostato nelle loro skill; le autorizzazioni chieste a metà run
   registrate come `grants` del protocollo; la nota di registrazione MCP anche
   sulle skill; il linter dei riferimenti ai componenti, che rifiuta un comando o
   una skill che non esiste. I router di `write-docs`, `tidy-repo` e
   `get-second-opinion` sono il corpo dei loro comandi.
4. **Test e documentazione** sui cinque host. Marketplace 38.0.0.
5. **Prova.** Stesso progetto e stesso bug della prima prova, da `init-project` a
   `finish-task`, in sessione interattiva e poi headless. Riesce se la correzione passa
   lo stesso oracolo, il comando chiede worktree e intervista, il Python di
   sistema resta intatto, nessun file esce dal run, e costa meno di un terzo dei
   30,90 USD della prima prova.

## 13. Decisioni

1. Un solo plugin d'ingresso `daodan`, specialisti senza comandi: deciso il 19 ottobre.
2. Nomi con verbo (`new-feature`, non `feature`): deciso il 19 ottobre. `review` esiste in Codex e `/init` e `/docs` in Claude Code; un verbo evita ogni collisione.
3. La nota di `brainstorm-idea` in `docs/ideas/`: deciso il 19 ottobre.
4. Shinatama resta com'è, per ora.
