# Uscita di rete di una preparazione

Prova le vie d'uscita di un container della preparazione su un Docker vero, con la rete e il proxy di Daodan (`container.run_in_container`: rete `--internal`, `start_proxy` con `PROXY_SCRIPT`) e lo stato di `egress` (`respond`, `reply`, file condivisi). Passo `T0.C.8` di `docs/plans/refactoring.md`.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | il tipo di uscita, una riga ciascuno in `rows.py`: diretta (nome, IP, IPv4/IPv6 letterali), redirect 301/302 da un host approvato verso uno fuori lista, DNS (risolutore del motore, UDP e TCP 53 pubblici), CONNECT di un nome rifiutato (che il proxy non deve risolvere), IP letterali nel proxy, indirizzi interni (`169.254.169.254`, `10.0.0.1`, loopback e indirizzi della VM, gateway della rete), CONNECT su porte 80, 8443, 22, HTTP in chiaro fuori dagli archivi apt; e le righe di approvazione: host fuori lista, dopo il sì («once» con `egress.reply`), in blacklist | `modal run benchmarks/egress/modal_probe.py` |

Due canarini su Modal, raggiungibili da Internet in HTTPS (tunnel di Modal), registrano ogni richiesta: `allowed` (l'host che l'utente approva) e `outside` (mai approvato). `driver.py` gira in una VM Sandbox con il demone Docker (come `benchmarks/project-model/modal_engine.py`) ed esegue `rows.py` come preparazione di un progetto. Segni cercati: richieste sui canarini fuori dai percorsi attesi, connessioni a due ascoltatori della VM (8099 su tutti gli indirizzi, 8098 sul loopback), query DNS col gettone della corsa sul filo (`tcpdump -i any`), fuori dalla risoluzione dell'host dei nomi rifiutati (`egress.resolve`). Esito in `results/<data>.json`.

## Risultati misurati

27 novembre 2026, con il codice di questa cartella sulla base `1ec9f03` (rete della preparazione con `com.docker.network.bridge.inhibit_ipv4=true`), su Modal (`ap-PXESuugu9xRIfq946cGuwg`, `results/2026-11-27.json`): 40 righe su 40 come atteso.

- Bloccate e senza segno: uscita diretta per nome (DNS «Try again»), per IP del canarino, IPv4 e IPv6 letterali (rete irraggiungibile); redirect 301 e 302 (il CONNECT verso `outside` riceve 403, il canarino non riceve nulla); DNS dal container (il risolutore del motore dà SERVFAIL e non inoltra, UDP e TCP 53 pubblici irraggiungibili); nel proxy il nome rifiutato (403, sul filo solo la risoluzione dell'host su `eth0`), l'host fuori lista, gli IP letterali v4/v6, `169.254.169.254`, `10.0.0.1`, `127.0.0.1`, `localhost`, l'IP della VM, le porte 80, 8443, 22 e l'HTTP in chiaro; dal container `169.254.169.254`, `10.0.0.1`, `172.17.0.1`, l'IP della VM e `host.docker.internal`.
- Approvazione: l'host fuori lista dà `failed`, `approval_required` e la richiesta in attesa, senza segno; dopo «once» il passo riesce (`done`, il canarino riceve `/approval-yes`); l'host in blacklist dà `failed`, solo `host_denied`, nessuna richiesta.
- Controlli positivi: il proxy apre `registry.npmjs.org:443` e il canarino approvato.
- Gateway della rete della preparazione: la connessione TCP a `172.18.0.1:8099` è rifiutata (`Connection refused`) e l'ascoltatore della VM su tutti gli indirizzi non registra nulla: con l'opzione il bridge non ha l'indirizzo dell'host. Prima (`ap-c9r58rXxewDbWV64u5wPwf`, sulla base `7f773af`, rete solo `--internal`) la connessione si apriva e l'ascoltatore la registrava (cancello rosso).
- Motori: l'opzione è di Docker Engine 28.0 (API 1.48). Su un motore con API più vecchia (Podman, Kiri 0.2.0 che dichiara 1.47, Docker 27) la rete si crea senza l'opzione e la preparazione procede con la lacuna non bloccante `gateway_open` (`container.internal_network`, decisione del proprietario del 27 novembre 2026).

| Riga | Docker ≥ 28 | Motori < 28 (Kiri 0.2.0, Docker 27, Podman) |
|---|---|---|
| `direct-network-gateway` (TCP al gateway della rete della preparazione) | bloccata (misurata, sopra) | raggiunta: atteso, miglioramento futuro (non misurato qui; prima corsa rossa `ap-c9r58rXxewDbWV64u5wPwf` con la sola `--internal`) |
