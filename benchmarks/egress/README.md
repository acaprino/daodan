# Uscita di rete di una preparazione

Prova le vie d'uscita di un container della preparazione su un Docker vero, con la rete e il proxy di Daodan (`container.run_in_container`: rete `--internal`, `start_proxy` con `PROXY_SCRIPT`) e lo stato di `egress` (`respond`, `reply`, file condivisi). Passo `T0.C.8` di `docs/plans/refactoring.md`.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | il tipo di uscita, una riga ciascuno in `rows.py`: diretta (nome, IP, IPv4/IPv6 letterali), redirect 301/302 da un host approvato verso uno fuori lista, DNS (risolutore del motore, UDP e TCP 53 pubblici), CONNECT di un nome rifiutato (che il proxy non deve risolvere), IP letterali nel proxy, indirizzi interni (`169.254.169.254`, `10.0.0.1`, loopback e indirizzi della VM, gateway della rete), CONNECT su porte 80, 8443, 22, HTTP in chiaro fuori dagli archivi apt; e le righe di approvazione: host fuori lista, dopo il sì («once» con `egress.reply`), in blacklist | `modal run benchmarks/egress/modal_probe.py` |

Due canarini su Modal, raggiungibili da Internet in HTTPS (tunnel di Modal), registrano ogni richiesta: `allowed` (l'host che l'utente approva) e `outside` (mai approvato). `driver.py` gira in una VM Sandbox con il demone Docker (come `benchmarks/project-model/modal_engine.py`) ed esegue `rows.py` come preparazione di un progetto. Segni cercati: richieste sui canarini fuori dai percorsi attesi, connessioni a due ascoltatori della VM (8099 su tutti gli indirizzi, 8098 sul loopback), query DNS col gettone della corsa sul filo (`tcpdump -i any`), fuori dalla risoluzione dell'host dei nomi rifiutati (`egress.resolve`). Esito in `results/<data>.json`.

## Risultati misurati

27 novembre 2026, con il codice di questa cartella sulla base `7f773af`, su Modal (`ap-c9r58rXxewDbWV64u5wPwf`, `results/2026-11-27.json`): 38 righe su 40 come atteso.

- Bloccate e senza segno: uscita diretta per nome (DNS «Try again»), per IP del canarino, IPv4 e IPv6 letterali (rete irraggiungibile); redirect 301 e 302 (il CONNECT verso `outside` riceve 403, il canarino non riceve nulla); DNS dal container (il risolutore del motore dà SERVFAIL e non inoltra, UDP e TCP 53 pubblici irraggiungibili); nel proxy il nome rifiutato (403, sul filo solo la risoluzione dell'host su `eth0`), l'host fuori lista, gli IP letterali v4/v6, `169.254.169.254`, `10.0.0.1`, `127.0.0.1`, `localhost`, l'IP della VM, le porte 80, 8443, 22 e l'HTTP in chiaro; dal container `169.254.169.254`, `10.0.0.1`, `172.17.0.1`, l'IP della VM e `host.docker.internal`.
- Approvazione: l'host fuori lista dà `failed`, `approval_required` e la richiesta in attesa, senza segno; dopo «once» il passo riesce (`done`, il canarino riceve `/approval-yes`); l'host in blacklist dà `failed`, solo `host_denied`, nessuna richiesta.
- Controlli positivi: il proxy apre `registry.npmjs.org:443` e il canarino approvato.
- **Uscita non bloccata (cancello rosso):** dal container della preparazione la connessione TCP al gateway della rete `--internal` (`172.18.0.1:8099`, l'host stesso) si apre, e l'ascoltatore della VM su tutti gli indirizzi la registra. Un servizio dell'host in ascolto su `0.0.0.0` è raggiungibile dal codice del progetto. Non corretto qui: va al proprietario.
