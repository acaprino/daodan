# Julia-1: prova preliminare su CPU locale

**Julia rientra nel target di memoria di questa prova, ma la configurazione verificata non è pronta per diventare il motore generale di Daodan.** Il routing sbaglia molti segnali, la selezione dei tool mantiene quasi tutto e la compattazione perde fatti necessari. Nessuna delle 47 richieste termina entro un secondo.

La richiesta «Fai i test», successiva al confronto Julia/Vela, autorizza questa piccola prova di Julia. La precedente campagna Gutsy rimane interrotta. Il modello e l'ambiente erano già disponibili: nessuna installazione, chiamata cloud o fase di addestramento.

## Risultati osservati

**47 richieste e 314 domande eseguite e valutate, senza rifiuti o troncamenti.** Si aggiungono quattro valutazioni su due righe fisse per controllare la parità numerica. Gli input, le domande e gli oracle sono quelli congelati del pilot Gutsy; gli stati JSON sono serializzati in testo compatto per l'interfaccia Julia.

| Dominio | Qualità osservata | Mediana per richiesta | p95 diagnostico |
|---|---|---:|---:|
| Routing | 15/45 campi etichettati corretti; 4/15 casi con tutti i campi essenziali corretti | 2,74 s | 4,27 s |
| Tool selection | 14/14 casi semanticamente sufficienti; 0/14 insiemi esatti; riduzione schemi del 12,54% in byte | 5,74 s | 12,08 s |
| Compattazione | 2/5 casi decisivi conservati per ciascuna variante; tre perdite critiche per variante | 1,98 s | 2,96 s |

Il routing invia dieci domande per richiesta; i tool da sei a dieci; la compattazione due. Sono tempi dell'intera chiamata `predict`, con tokenizzazione inclusa, non tempi indipendenti per singola domanda. Il modello è residente e già scaldato dal controllo di parità; le cache di token ed encoding vengono svuotate prima di ogni chiamata cronometrata. I sedici tempi dei tool includono anche due casi di contratto/discovery, esclusi dai quattordici casi della metrica semantica. La numerosità ridotta rende il p95 una descrizione del campione, non una garanzia.

### Routing

L'oracle etichetta 45 proprietà essenziali delle 150 risposte prodotte. I rimanenti campi non vengono automaticamente considerati corretti o errati. R06 e R07 sbagliano un segnale dichiarato critico, rispettivamente profondità del ragionamento e rischio; entrambi risolvono comunque a `tier3`. Questi due errori non sono prova di instradamento a un modello troppo debole.

Lo scoring mantiene le etichette e il calcolo del tier del provider congelato `model-routing`. Julia non espone il reject nativo di Gutsy: non viene fabbricato un valore per simulare quella capacità.

### Tool selection

Il risultato 14/14 significa che il necessario resta disponibile. Tutti i quattordici casi includono anche tool superflui; passare tutti i tool eleggibili ottiene già 14/14 sulla stessa metrica. Non è quindi un successo sufficiente per adottare il selettore.

Julia mantiene 117 delle 134 selezioni eleggibili complessive. Gli schemi passano da 35.373 a 30.938 byte, con un risparmio di 4.435 byte. **Sono byte, non token del modello destinatario.** Nel caso T04 l'oracle richiede zero tool e Julia ne seleziona otto su nove. Il filtro delle autorizzazioni e gli strumenti obbligatori sono deterministici e non danno credito al modello.

### Compattazione con fast-jev

Sono valutati otto scenari in due rappresentazioni preregistrate, A e B. Per ciascuna variante il conteggio complessivo è 5/8 cronologie con fatti conservati. Tre successi sono strutturali: i fatti sopravvivono indipendentemente dalle decisioni del classificatore. Nei cinque casi in cui la decisione conta, Julia conserva i fatti in C06 e C07 e li perde in C01, C05 e C08.

La ricostruzione usa il vero fast-jev alla revisione `e3f262a7f4d42bd8dd32ced30d26176f7cb545b0`. Il recupero del fatto in C08 nella procedura protetta dipende dal guardrail esterno, non da una previsione corretta di Julia. Le due varianti degli stessi scenari non sono sedici prove indipendenti.

## Hardware e risorse

| Voce | Misura/configurazione |
|---|---|
| Macchina | Windows 11, Intel Core Ultra 7 155H, RAM fisica 33.775.378.432 byte |
| Esecuzione | CPU, FP32, quattro thread del modello, batch uno, contesto massimo 1.024 token, encoding rigoroso |
| Memoria osservata | Picco worker 844,8 MiB; picco combinato worker e monitor 873,8 MiB |
| Tempo | Caricamento del runtime/modello 56,6 s; tentativo complessivo monitorato 233,2 s |
| Arresti | Nessun intervento dei controlli di memoria o tempo; processo terminato con codice zero |

I criteri operativi dichiarati prima della prova erano un target di 1 GiB combinato e un secondo per richiesta. Il primo è rispettato; il secondo non è raggiunto in alcuna richiesta. Il controllo campionato ogni 100 ms interrompe oltre 2 GiB o sui limiti temporali: non è un limite di memoria imposto dal sistema operativo. La somma RSS può contare pagine condivise più volte e non misura eventuali picchi fra due campionamenti.

Il modello è `SupersonicLabs/Julia-1`, revisione `a85b127321d580d65176c89ced8273f305745d85`, con pesi SHA-256 `df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72`. Runtime: Python 3.13.14, Torch 2.14.0, Transformers 5.0.0, NumPy 2.5.4. Backend Torch ufficiale, head CPU ottimizzata, compilazione disattivata.

Il confronto fra head ottimizzata e originale su due righe fisse restituisce le stesse scelte; massimo scarto nei logits 0,00000191, entro la soglia dichiarata di 0,02. È un controllo circoscritto, non una prova universale di equivalenza.

## Evidenza, verifica e decisione

1. [Manifest finale](../../.daodan/runs/2026-10-27-julia-cpu-pilot/manifest.json), [input effettivi](../../.daodan/runs/2026-10-27-julia-cpu-pilot/input.json) e [risposte originali](../../.daodan/runs/2026-10-27-julia-cpu-pilot/execution/records/).
2. [Risultati per caso](../../.daodan/runs/2026-10-27-julia-cpu-pilot/results.json), [misure delle risorse](../../.daodan/runs/2026-10-27-julia-cpu-pilot/execution/resources.json) e [diagnostica derivata](../../.daodan/runs/2026-10-27-julia-cpu-pilot/derived-diagnostics.json).
3. [Revisione preliminare indipendente](../../.daodan/runs/2026-10-27-julia-cpu-pilot/protocol-review.md), [revisione dei risultati](../../.daodan/runs/2026-10-27-julia-cpu-pilot/results-review.md) e [codice della prova](../../evals/julia-cpu-pilot/).

Il manifest finale è `b6e93264e624982c96e25199fda6bd91bf7e709040a84168011063d6344be2af`. Le correzioni preliminari a misura dei tempi, identità delle dipendenze fast-jev e descrizione della parità precedono ogni inferenza; i manifest precedenti sono conservati nel run. Le risposte non hanno modificato domande, oracle o soglie. La revisione ricalcola gli esiti dai record e verifica gli hash degli input, degli owner e delle dipendenze effettive.

Questi sono casi sintetici, parzialmente etichettati, di un pilot piccolo. Non misurano un compito LLM downstream né autorizzano un confronto diretto di velocità con Gutsy su Modal o Vela su Apple: hardware, runtime e configurazioni differiscono. Non sono stati eseguiti test di Vela in questa prova.

**Esito:** candidato compatibile con il target di memoria osservato, ma non adottabile con questi input e questa procedura per routing, selezione mirata dei tool o compattazione autonoma. Nessuna integrazione nel prodotto o modifica ai plugin.
