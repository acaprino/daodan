# Fase 1: mappa sempre aggiornata e quattro regole per la review

**Stato:** proposta rifinita, da approvare. **Data:** 9 novembre 2026; aggiornata l'11 novembre 2026. Fase 1 di 3: [fase 2](2026-11-09-flow-model.md), [fase 3](2026-11-09-flows-in-review.md).

Due interventi che usano solo meccanismi già presenti e misurati:

- **A.** Dopo ogni modifica al codice la mappa si aggiorna da sola, nella parte che una macchina può ricalcolare.
- **B.** La review riceve quattro regole che chiudono errori visti nei test.

## Parole

| Parola | Significato |
| --- | --- |
| Run | Una mappa del progetto fatta in un certo momento: lo snapshot dei file più i documenti di analisi |
| Run pubblicato | L'ultimo run completo. Non cambia più: è la prova su cui poggiano analisi e review |
| Run di lavoro | Un solo run, chiamato `working`, che segue il codice mentre cambia. Non contiene documenti di analisi |
| Incarico | Il lavoro affidato a un revisore: un elenco di file e una richiesta |
| Segnalazione | Un difetto descritto da un revisore, con file e riga |

Le altre parole sono definite nella fase 2.

## A. La mappa si aggiorna dopo ogni modifica

### Oggi

- Dopo una modifica la mappa resta ferma all'ultimo run. La ricerca risponde sul codice vecchio e la lettura del file modificato fallisce con «source changed; refresh the manifest».
- Per aggiornarla bisogna rifare un run a mano.
- Un run con i documenti di analisi non si può riscrivere: ogni documento è legato all'impronta del proprio snapshot.
- Creare un run nuovo a ogni modifica costa troppo spazio: lo snapshot pesa 127 MB su questo repository e 20 MB su `react-app` di phazly-app.

### Proposta

1. **Il run di lavoro nasce dal run pubblicato.** Sta in `.daodan/map/runs/working/`, con lo stesso perimetro. Senza un run pubblicato non nasce: la prima mappa si fa sempre su richiesta. A ogni nuovo run pubblicato riparte da quello.
2. **Un comando lo aggiorna: `snapshot.py refresh`.** In fila:
   1. rilegge solo i file cambiati dall'ultimo aggiornamento;
   2. prepara il nuovo snapshot del run di lavoro;
   3. rifà l'indice di ricerca, i moduli e i collegamenti `chiama` sullo stesso snapshot;
   4. rende disponibile l'aggiornamento solo quando questi artefatti sono coerenti e scrive `refresh.json`: esito, quando, quali file e simboli sono cambiati rispetto al run pubblicato, quali frasi dei documenti pubblicati li citano. Durante l'aggiornamento o dopo un errore gli strumenti dichiarano che il run è da aggiornare; non leggono artefatti di aggiornamenti diversi.
3. **Un hook lancia il comando dopo ogni modifica.** In `plugins/codebase-map/hooks/hooks.json`: evento `PostToolUse`, strumenti `Edit`, `Write`, `NotebookEdit`, `Bash`, in background. Non parte se il progetto non ha un run pubblicato, o se il file modificato sta fuori dal perimetro, sotto `.daodan/` o sotto `.team-review/`. Dove gli hook non esistono, lo stesso comando si lancia a mano o dall'ingresso della mappa.
4. **Un aggiornamento alla volta.** Se arriva una modifica mentre un aggiornamento è in corso, alla fine ne parte un altro. Mai due insieme.
5. **Molte modifiche, ricostruzione completa.** Se è cambiato più del 40% dei file dall'ultimo aggiornamento, il comando rifà per intero snapshot, indice, moduli e collegamenti `chiama`, sempre senza modello.

**Cosa non fa.** Schede e documenti di analisi li scrive un modello: il comando non li rigenera, segnala soltanto quali non sono più validi.

**Quale run si usa.**

| Per | Run |
| --- | --- |
| Cercare, leggere, vedere chi chiama chi, valutare l'impatto di una modifica | Run di lavoro solo se l'aggiornamento è completo e coerente con il codice corrente; se assente, run pubblicato con lo stesso controllo di freschezza |
| Leggere i documenti di analisi | Run pubblicato |
| Fare una review | Mai il run di lavoro: un run che non cambia, creato per quella review |

L'esistenza della cartella non basta. Prima di rispondere gli strumenti leggono l'esito in `refresh.json` e confrontano lo snapshot con il sorgente tramite `compare_files`: elenco dei file, dimensione e data, e il contenuto solo dove queste differiscono. Limite dichiarato: una modifica che conserva dimensione e data non viene vista. Se il run è da aggiornare restituiscono il motivo e l'azione necessaria, senza ripiegare su un run obsoleto. Una modifica arrivata durante un aggiornamento lascia il run da aggiornare fino al successivo.

### Misure già fatte

| Operazione su questo repository (569 file) | Tempo |
| --- | --- |
| Snapshot da zero | 15,7 s |
| Aggiornamento senza modifiche | 3,4 s |
| Aggiornamento con un file modificato | 3,6 s |
| Aggiornamento con i collegamenti `chiama` | 4,4 s |

Un hook `PostToolUse` in background parte davvero dopo una scrittura e riceve il percorso del file (prova del 9 novembre, `claude` 2.1.319).

### Prova, senza modello

Test su un progetto temporaneo con un run pubblicato:

1. modifico un file fuori dagli hook, senza `refresh`: la ricerca restituisce l'avviso con l'azione, non un risultato sul codice vecchio; dopo `refresh` il simbolo nuovo si trova nel run di lavoro e la lettura del file non fallisce;
2. il run pubblicato è identico byte per byte;
3. due `refresh` insieme: un aggiornamento più uno successivo, snapshot integro; una lettura durante l'aggiornamento o dopo un errore riceve un avviso, mai artefatti incoerenti; una modifica arrivata durante l'aggiornamento lascia il run da aggiornare;
4. oltre il 40%: `refresh.json` registra la ricostruzione completa e la ricerca risponde sul codice corrente; l'aggiornamento successivo, con un solo file modificato, rilegge solo quel file;
5. l'hook non parte per un file sotto `.team-review/`, fuori perimetro, o senza run pubblicato.

Da registrare, su questo repository e su phazly-app: il tempo di un aggiornamento, del controllo di freschezza a ogni interrogazione e di una ricostruzione completa con indice, moduli e collegamenti.

### Fuori da questa fase

Avvisare l'agente a ogni aggiornamento. Rileggere solo i file indicati dall'hook invece di controllarli tutti: si fa se un aggiornamento supera 10 s su un progetto reale.

## B. Quattro regole per la review

Ogni regola chiude un errore visto in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md).

| # | Regola | Errore visto | File da modificare |
| --- | --- | --- | --- |
| 1 | La prima azione di una review è caricare la preparazione. Chi non può seguire il metodo lo dice nella prima riga e si ferma | Run A: il modello ha fatto la review da solo e l'ha detto solo alla fine | `review-method/SKILL.md` |
| 2 | Ogni frase sul modello dei dati dice a quale tipo e a quale granularità si riferisce, con `file:line`. Una negazione («non esiste X») cita la ricerca che la sostiene, altrimenti si scrive «non noto» | Run B: «non esiste un tipo planned», vero per il record dello slot, falso per le sue aggiunte; 49 incarichi l'hanno ereditato | `review-preparation/references/team-review.md` |
| 3 | Un'informazione falsa mostrata all'utente, o un'azione che l'utente non può più fare, vale almeno Medium | Run A3: «piatto non mangiato mostrato come Completato, bottone per registrarlo sparito» valutato Low | `review-quality-gates/references/reviewer-common.md` |
| 4 | Due segnalazioni sono lo stesso problema solo se hanno la stessa causa e la stessa situazione che lo fa scattare. Situazioni diverse sulla stessa riga restano segnalazioni distinte nel rapporto | Run A3: «pasto saltato» e «cibo estraneo» fusi in una voce; la seconda, il difetto vero, sparita | `review-consolidation/references/team-review.md` |

### Prova

1. **Regola 1.** La stessa richiesta della run A in cinque sessioni nuove, fermate ai primi turni. Riesce se la prima azione è il caricamento della preparazione in cinque su cinque. Costo atteso: circa 0,3 USD a sessione.
2. **Regola 4.** Il solo consolidamento rieseguito sui dodici risultati salvati della run A3. Riesce se «cibo estraneo» (`job-03-F4`) compare nel rapporto come segnalazione distinta.
3. **Regole 2 e 3.** Si misurano nella fase 3, con le review complete.

## Ordine di lavoro

1. `snapshot.py refresh` con i suoi test.
2. Hook.
3. Regole 1 e 4 con le loro prove.
4. Regole 2 e 3 come testo.
5. Versioni dei due plugin e una riga in `tools-guide.md` sul run di lavoro.
