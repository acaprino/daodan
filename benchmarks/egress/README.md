# Uscita di rete di una preparazione

Prova le vie d'uscita di un container della preparazione su un Docker vero, con la rete e il proxy di Daodan (`container.run_in_container`: rete `--internal`, `start_proxy` con `PROXY_SCRIPT`) e lo stato di `egress` (`respond`, `reply`, file condivisi). Passo `T0.C.8` di `docs/plans/refactoring.md`.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | il tipo di uscita, una riga ciascuno in `rows.py`: diretta (nome, IP, IPv4/IPv6 letterali), redirect 301/302 da un host approvato verso uno fuori lista, DNS (risolutore del motore, UDP e TCP 53 pubblici), CONNECT di un nome rifiutato (che il proxy non deve risolvere), IP letterali nel proxy, indirizzi interni (`169.254.169.254`, `10.0.0.1`, loopback e indirizzi della VM, gateway della rete), CONNECT su porte 80, 8443, 22, HTTP in chiaro fuori dagli archivi apt; e le righe di approvazione: host fuori lista, dopo il sì («once» con `egress.reply`), in blacklist | `modal run benchmarks/egress/modal_probe.py` |

Due canarini su Modal, raggiungibili da Internet in HTTPS (tunnel di Modal), registrano ogni richiesta: `allowed` (l'host che l'utente approva) e `outside` (mai approvato). `driver.py` gira in una VM Sandbox con il demone Docker (come `benchmarks/project-model/modal_engine.py`) ed esegue `rows.py` come preparazione di un progetto. Segni cercati: richieste sui canarini fuori dai percorsi attesi, connessioni a due ascoltatori della VM (8099 su tutti gli indirizzi, 8098 sul loopback), query DNS col gettone della corsa sul filo (`tcpdump -i any`), fuori dalla risoluzione dell'host dei nomi rifiutati (`egress.resolve`). Esito in `results/<data>.json`.

## Proxy: criteri

I due candidati di `T3.A` sui criteri di `docs/specs/architettura.md` («Strumento del proxy»), come dal codice letto: Smokescreen al tag `v1.0.1`, `PROXY_SCRIPT` in `daodan/core/container.py`. La prova che decide è `modal_probe.py --proxy script|smokescreen`.

| Criterio | Smokescreen `v1.0.1` | `PROXY_SCRIPT` |
|---|---|---|
| Solo porta 443 | no: l'ACL è per host, senza porta (`acl/v1/yaml_loader.go`); le porte valgono solo per gli indirizzi (`--deny-address IP:PORT`) | sì: CONNECT solo a `:443` |
| Eccezione apt per percorso | no: l'HTTP in chiaro di un host ammesso passa con ogni percorso | sì: `GET`/`HEAD` di `dists/` e `pool/` sugli archivi `http://<host>` |
| Whitelist e blacklist da file | sì: ACL YAML (`version: v1`, `default.allowed_domains`, `action: enforce`, `global_deny_list`) da `--egress-acl-file` o `acl_file` | sì, a monte: `start_proxy` prende i soli host che `egress.decide` ammette dai file di `egress` e li passa in argv |
| Nessun host rifiutato risolto dal proxy | sì: risolve solo se l'ACL ammette (`checkIfRequestShouldBeProxied`, `smokescreen.go:1382`) | sì: confronta il nome e non lo risolve |
| Nessun host ammesso aperto verso un indirizzo privato, loopback o link-local | sì: classifica l'indirizzo risolto e rifiuta non global unicast, loopback, privati, CGNAT, IPv6 con IPv4 dentro (`ip_policy.go`), salvo `--allow-range` o `--unsafe-allow-private-ranges` | no: `create_connection` al nome ammesso, qualunque indirizzo dia |
| Rifiuti leggibili come `{host, port}` | sì: log JSON (`logrus.JSONFormatter`), riga `CANONICAL-PROXY-DECISION` con `allow`, `requested_host` (`host:porta`), `decision_reason` | sì: `@@daodan-refused {"host","port"}` (`egress.refused`) |
| Ruolo del client | senza certificato TLS il ruolo manca: serve `allow_missing_role: true` (solo dal file di configurazione) per cadere sulla regola `default` | non serve |
| Licenza | MIT (`LICENSE.txt`) | MIT (quella di Daodan) |

Provenienza di Smokescreen, verificata il 27 novembre 2026 da una funzione Modal (`ap-aEAopqWqOpl2BVgkc5ZvpS`; dalla sessione github.com risponde 403) con l'API REST di GitHub, il registro `ghcr.io` e `gh attestation verify` 2.63.2 sul bundle dell'API delle attestazioni:

- Release `v1.0.1` (pubblicata il 25 novembre 2026, tag `38641dd`): `smokescreen_v1.0.1_linux_amd64.tar.gz` sha256 `6021eda5f2c95e37c7fc1966debccf3714f8740e2784ed9e9d0087b21a0ccf06`, uguale a `SHA256SUMS` (`sha256sum -c`: OK) e al `digest` dell'asset; attestazione verificata (`gh attestation verify <tar> -R stripe/smokescreen`: esito 0).
- Immagine `ghcr.io/stripe/smokescreen:v1.0.1`: indice OCI `sha256:e62052a184ce5ef97c32b00a32583fc5376d4ca5d9ec941cf9a4566eef0556e8` (linux/amd64 `sha256:55b1254d…`, linux/arm64 `sha256:ce7f84a9…`), distroless `static:nonroot` per digest, `USER 65532:65532`, porta 4750. `gh attestation verify oci://ghcr.io/stripe/smokescreen@sha256:e62052a1… -R stripe/smokescreen`: esito 0, firmata da `.github/workflows/release.yml@refs/tags/v1.0.1`, commit `b464c02`. Da qui l'immagine si usa solo come `ghcr.io/stripe/smokescreen@sha256:e62052a184ce5ef97c32b00a32583fc5376d4ca5d9ec941cf9a4566eef0556e8`.

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
