# Uscita di rete di una preparazione

Prova le vie d'uscita di un container della preparazione su un Docker vero, con la rete e il proxy di Daodan (`container.run_in_container`: rete `--internal`, `start_proxy` con `PROXY_SCRIPT`) e lo stato di `egress` (`respond`, `reply`, file condivisi). Passo `T0.C.8` di `docs/plans/refactoring.md`.

## Parametri

| Prova | Cosa varia | Comando |
|---|---|---|
| `modal_probe.py` | il tipo di uscita, una riga ciascuno in `rows.py`: diretta (nome, IP, IPv4/IPv6 letterali), redirect 301/302 da un host approvato verso uno fuori lista, DNS (risolutore del motore, UDP e TCP 53 pubblici), CONNECT di un nome rifiutato (che il proxy non deve risolvere), IP letterali nel proxy, indirizzi interni (`169.254.169.254`, `10.0.0.1`, loopback e indirizzi della VM, gateway della rete), CONNECT su porte 80, 8443, 22, HTTP in chiaro fuori dagli archivi apt; e le righe di approvazione: host fuori lista, dopo il sì («once» con `egress.reply`), in blacklist | `modal run benchmarks/egress/modal_probe.py` |
| `modal_probe.py --proxy script\|smokescreen` (`T3.A.2`) | il proxy, sulle stesse righe più: (a) due host ammessi che il container del proxy risolve a `10.0.0.1` e `169.254.169.254` (`--add-host`), (d) `apt-get update` e `install git` nell'immagine di base come `preparation.NEEDS["git"]`, (g) avvio, memoria e dimensione dell'immagine del proxy. Smokescreen sta al posto di `start_proxy` (`driver.py`): immagine per digest, ACL `action: enforce` degli stessi host data con `cp`, `allow_missing_role`, log JSON letto come `egress.refused` | `modal run benchmarks/egress/modal_probe.py --proxy script`, poi `--proxy smokescreen` |

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

### Proxy: la prova di `T3.A.2`

27 novembre 2026, con il codice di questa cartella com'è nel commit che porta questi risultati, su Modal: `--proxy script` `ap-cIYuqIvnkHJTzBHhxMgWo5` (`results/proxy-script.json`, 41 righe su 44), `--proxy smokescreen` `ap-ClV8zBfHV1ftVBtNpNcawB` (`results/proxy-smokescreen.json`, 40 su 44). Righe rosse:

| Riga | `PROXY_SCRIPT` | Smokescreen |
|---|---|---|
| (a) `proxy-allowed-to-10x`, `proxy-allowed-to-metadata` | rossa: `502`, il proxy prova a connettersi a `10.0.0.1:443` e `169.254.169.254:443` | bloccata: `407 Request rejected by proxy` |
| `proxy-connect-port-80`, `proxy-connect-port-8443` | bloccata: `403` | rossa: `502`, tenta la porta dell'host ammesso |
| `proxy-connect-port-22` | bloccata: `403` | verde solo per il tempo del client (5 s): Smokescreen tenta `registry.npmjs.org:22` e non risponde |
| `proxy-plain-http` | bloccata: `403` | rossa: `502`, inoltra l'HTTP in chiaro dell'host ammesso a ogni percorso |
| (d) `control-apt-git` | rossa | rossa |
| (g) `measure-proxy` | avvio 0,42 s, 9,4 MiB, immagine 69,9 MB | avvio 0,25 s, 5,5 MiB, immagine 26,8 MB |

- La riga d è rossa per entrambi per la stessa causa, che non è del proxy: il tunnel verso `deb.debian.org:443` si apre, poi apt dà `certificate verify failed` perché `debian:trixie-slim` (`preparation.IMAGE`) non ha `ca-certificates`, e la riga di `NEEDS["git"]` passa le fonti a `https://`. È un difetto di `preparation.NEEDS["git"]`.
- Corretto (27 novembre 2026): `NEEDS["git"]` lascia le fonti apt in `http://` come l'immagine le nomina (apt verifica i `Release` firmati e l'hash di ogni pacchetto; il proxy apre solo `GET`/`HEAD` di `dists/` e `pool/`, e `http://deb.debian.org` si aggiunge agli archivi canonici accanto a quelli di Ubuntu), e `preparation.IMAGE` diventa `buildpack-deps:noble` per digest, l'immagine che le altre lingue usano già, con `ca-certificates` e `xz`. `--proxy script` su questa base: `ap-C1AmQnb8Yt6p01fUuyWkc3` (`results/proxy-script.json`), 44 righe su 44; la riga d dà `git version 2.43.0`.

### Immagine di base: cosa serve alle ricette (`modal_image.py`)

`modal run benchmarks/egress/modal_image.py`: gli stessi tre casi sull'immagine di prima e su `preparation.IMAGE`, in un container Modal di quell'immagine dietro `PROXY_SCRIPT` aperto a `container.REGISTRIES`, con l'ambiente della preparazione. 27 novembre 2026, `ap-DrW6s3JiZybpB7lZ8Xf6Lr`, `results/image.json`; il proxy non rifiuta nulla.

| Caso | `debian:trixie-slim` (prima) | `buildpack-deps:noble` (`preparation.IMAGE`) |
|---|---|---|
| `apt`: `NEEDS["git"]`, poi `git --version` | riesce (fonti `http://`) | riesce: `git version 2.43.0` |
| `xz`: `NEEDS["rust"]` (`.tar.xz`), poi `rustc`, `cargo` | rotta: `tar` non trova `xz` | riesce: `rustc 1.99.1`, `cargo 1.99.1` |
| `go`: `NEEDS["go"]`, poi `go mod download golang.org/x/text@v0.21.0` | rotta: `x509: certificate signed by unknown authority` (niente `ca-certificates.crt`) | riesce: `go1.27.3` |

- L'immagine nuova non apre host nuovi ed è fissata per digest; installare `ca-certificates` e `xz-utils` in ogni preparazione sulla Debian slim chiederebbe l'archivio a ogni corsa, con versioni che seguono l'archivio.
- Approvazione (fuori lista, dopo il sì, blacklist) e segni: verdi per entrambi; per Smokescreen i rifiuti sono le decisioni con `allow: false` del suo log JSON, che scrive su stderr.
- Le richieste `GET` della sonda portano l'intestazione `Host`: senza, il server HTTP di Smokescreen risponde `400` prima della politica (prima corsa `ap-ws5xOLBrk5nOuiWMsDccg0`).

## Capability e utente non root (`T3.A.5`)

`modal_hardening.py` misura cosa rompono `--cap-drop ALL` e `--user 65532:65532` nelle fasi della preparazione e nei servizi. Ogni riga passa da `container.phase` e `container.start_services` di Daodan, con i flag della variante subito dopo `create`, in una VM Sandbox con Docker 29.10.0, sulla rete bridge del motore (il proxy è la prova di `modal_probe.py`).

| Parametro | Valori |
|---|---|
| Varianti | oggi (nessun flag), `--cap-drop ALL`, `--user 65532:65532`, entrambi |
| Ricette | ogni voce di `preparation.NEEDS` più `UNPACK_JDK`, `COREPACK_INSTALL` e mise in `STATE` (`toolchains`, node 22.12.0), ciascuna sull'immagine che la usa (Debian di `preparation.IMAGE`, `buildpack-deps` di `indexers.clang`, Python di `indexers.python` per `git` e `poetry`) |
| Ripristini | uno per gestore di `RESTORES` (`node_prepare` per npm, pnpm, yarn; `restore` per gli altri; Maven e Gradle con gli strumenti di `container_runner.TOOLS`), dopo una fase root di oggi che installa lo strumento |
| Copia e volumi | `copy_perimeter` copiato con `cp` in `/work` e `STATE`, scrittura in entrambi |
| Servizi | `postgres:17`, `mysql:8.4` (fissati per digest), nel pod di `start_pod`, attesa `ports`, `SERVICE_WAIT` 180 s |
| Obiettivo | ricetta: root, senza `/work`, `--cap-drop ALL` più le minime; ripristino e copia: `65532` con `--cap-drop ALL` su volumi intestati a `65532` da una fase root (`chown -R`); servizio: root con le minime |
| Capability minime | dal set predefinito di Docker (14) se ne toglie una per volta, nel suo ordine, finché la riga riesce (con due capability che si sostituiscono l'insieme dipende dall'ordine) |

27 novembre 2026, base `121a254`, Modal `ap-0ddm0qtmuEo9PWOznnLivw`, `results/hardening.json` (errore e passi per riga). Tutte le righe riescono oggi.

| Riga | `--cap-drop ALL` (root) | Capability minime | `--user 65532` (volumi di oggi) | Obiettivo |
|---|---|---|---|---|
| ricette `node`, `uv`, `dotnet`, `conan`, `poetry`, `arm-none-eabi`, `corepack` | rotta: `tar` da root non cambia proprietario (`uid 1000`, `1001`, `2001`) né modo | `CHOWN`, `FOWNER` | rotta | riesce |
| ricetta `git` (`apt-get`) | rotta: `apt` passa a `_apt` (`setgroups`, `setresuid`) e scrive le liste | `DAC_OVERRIDE`, `SETGID`, `SETUID` | rotta: `sed -i` in `/etc/apt` | riesce |
| ricette `go`, `rust`, `vcpkg`, `jdk` (`UNPACK_JDK`), `cmdline-tools`, `mise` | riesce | nessuna | rotta | riesce |
| copia in `/work` e `STATE` | riesce | — | rotta: `/daodan/state` è di root | riesce |
| ripristini npm, pnpm, yarn, uv, pip, poetry, go, cargo, dotnet | riesce | nessuna | rotta: cache in `STATE` (`npm-cache`, `home/.cache/node/corepack`, `uv`, `go`), `/work/Cargo.lock`, primo avvio di dotnet | riesce |
| ripristini Maven, Gradle | riesce | nessuna | rotta | **rotta**: `UNPACK_JDK` fa `mkdir /opt/java` nella radice del container, senza `java` Maven e Gradle si fermano |
| servizio postgres | rotta: `chmod` della cartella dati, passaggio a `postgres` | `DAC_OVERRIDE`, `SETGID`, `SETUID` | rotta: `initdb` non cambia i permessi della cartella dati | riesce |
| servizio mysql | rotta: `setgid` di `mysqld` | `DAC_OVERRIDE`, `SETGID`, `SETUID` | riesce | riesce |

- Ricette da root: `--cap-drop ALL` con `CHOWN`, `FOWNER`, `DAC_OVERRIDE`, `SETGID`, `SETUID` copre ogni ricetta; le ultime tre servono solo a `git` (`apt`). `tar --no-same-owner --no-same-permissions` toglierebbe `CHOWN` e `FOWNER` (non misurato).
- Servizi: dell'atteso servono `DAC_OVERRIDE`, `SETGID`, `SETUID`; `CHOWN` e `FOWNER` no (le cartelle dei dati sono già dell'utente del servizio nell'immagine).
- Ripristino come `65532`: riesce sui volumi intestati a `65532`, tranne dove serve il JDK: il collegamento `/opt/java/openjdk` (`UNPACK_JDK`, `PATH`) va fatto altrove (`T3.A.6b`).
- Fuori dalla misura: sulla Debian di `preparation.IMAGE` (senza `ca-certificates` né `xz`) `apt-get` in https, `go mod download` e le ricette `.tar.xz` falliscono già oggi (prima corsa `ap-uU9Zxqb4t5kr545THVknlz`); qui girano sulle immagini che le usano.
